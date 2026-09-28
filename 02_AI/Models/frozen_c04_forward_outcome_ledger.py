"""
===============================================================================
Module      : frozen_c04_forward_outcome_ledger.py
Project     : PulseViper XAU AI
Purpose     : Gate 15D-C-B1 v1.1 — Append-Only Frozen Forward Outcome Ledger
===============================================================================

Durable append-only storage authority for matured prospective outcomes.

V1.1 aligns outcome storage with corrected frozen M5 semantics:

- raw M5 `time` is bar OPEN time
- decision_time is completed bar availability / close time
- decision_bar_open_time = decision_time - 5 minutes
- entry = completed decision bar CLOSE
- ATR14 = completed decision bar ATR14
- horizon = next 12 completed M5 rows after decision bar

Guarantees:
- Separate from TRUE_FORWARD observation ledger.
- One JSON record per line.
- Locked append.
- flush + fsync after append.
- Exact duplicate can be idempotently ignored.
- Same observation ID with conflicting outcome fails closed.
- Corrupt / truncated / tampered records fail closed.
- No MT5 access.
- No performance evaluation.
- No PnL evaluation.
- No live/execution authority.
===============================================================================
"""

from __future__ import annotations

import contextlib
import dataclasses
from enum import Enum
import importlib
import json
import math
import os
from pathlib import Path
import re
import sys
from typing import Any, Generator, Mapping, cast

import pandas as pd


_maturer: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_maturer"
)

FrozenC04ForwardOutcome: Any = (
    _maturer.FrozenC04ForwardOutcome
)


OUTCOME_LEDGER_VERSION: str = (
    "FROZEN_C04_FORWARD_OUTCOME_LEDGER_V1_1"
)

EXPECTED_MATURATION_VERSION: str = (
    "FROZEN_C04_FORWARD_OUTCOME_MATURER_V1_1"
)

EXPECTED_CONTRACT_FINGERPRINT_SHA256: str = (
    "01fe52a2f068fcc8fb2fc5b89dd7e19dc974fc2d967cfb791e75c3415804ce87"
)

EXPECTED_HORIZON_BARS: int = 12

EXPECTED_BASE_TIMEFRAME_MINUTES: int = 5

EXPECTED_DECISION_BAR_SEMANTICS: str = (
    "M5_BAR_OPEN_EQUALS_DECISION_TIME_MINUS_5_MINUTES"
)

EXPECTED_ENTRY_REFERENCE: str = (
    "DECISION_M5_COMPLETED_BAR_CLOSE"
)

EXPECTED_ATR_REFERENCE: str = (
    "DECISION_M5_COMPLETED_BAR_ATR14"
)

EXPECTED_HORIZON_SEMANTICS: str = (
    "NEXT_12_COMPLETED_M5_ROWS_AFTER_DECISION_BAR"
)

PERFORMANCE_EVALUATION_AUTHORIZED: bool = False
PNL_EVALUATION_AUTHORIZED: bool = False
LIVE_AUTHORIZED: bool = False
EXECUTION_AUTHORIZED: bool = False


_SHA256_RE = re.compile(
    r"^[a-f0-9]{64}$"
)


class OutcomeDuplicateHandling(
    str,
    Enum,
):
    FAIL_CLOSED = "FAIL_CLOSED"
    IDEMPOTENT_IGNORE = "IDEMPOTENT_IGNORE"


class FrozenC04OutcomeLedgerError(
    RuntimeError
):
    pass


class DuplicateOutcomeError(
    FrozenC04OutcomeLedgerError
):
    pass


class ConflictingOutcomeError(
    FrozenC04OutcomeLedgerError
):
    pass


class CorruptedOutcomeLedgerError(
    FrozenC04OutcomeLedgerError
):
    pass


class InvalidOutcomeRecordError(
    FrozenC04OutcomeLedgerError
):
    pass


@dataclasses.dataclass(
    frozen=True
)
class OutcomeAppendResult:
    record: Any
    is_duplicate: bool
    appended: bool
    message: str


def _require_sha256(
    value: Any,
    field_name: str,
) -> str:

    if not isinstance(
        value,
        str,
    ):
        raise InvalidOutcomeRecordError(
            f"{field_name}_NOT_STRING"
        )

    normalized = (
        value.strip()
        .lower()
    )

    if not _SHA256_RE.fullmatch(
        normalized
    ):
        raise InvalidOutcomeRecordError(
            f"{field_name}_INVALID_SHA256"
        )

    return normalized


def _require_string(
    value: Any,
    field_name: str,
) -> str:

    if not isinstance(
        value,
        str,
    ):
        raise InvalidOutcomeRecordError(
            f"{field_name}_NOT_STRING"
        )

    normalized = value.strip()

    if not normalized:
        raise InvalidOutcomeRecordError(
            f"{field_name}_EMPTY"
        )

    return normalized


def _require_utc_timestamp(
    value: Any,
    field_name: str,
) -> str:

    raw = _require_string(
        value,
        field_name,
    )

    try:

        parsed = pd.Timestamp(
            raw
        )

    except Exception as exc:

        raise InvalidOutcomeRecordError(
            f"{field_name}_INVALID_TIMESTAMP"
        ) from exc

    if parsed is pd.NaT:

        raise InvalidOutcomeRecordError(
            f"{field_name}_INVALID_TIMESTAMP"
        )

    timestamp = cast(
        pd.Timestamp,
        parsed,
    )

    if timestamp.tzinfo is None:

        raise InvalidOutcomeRecordError(
            f"{field_name}_MUST_BE_TIMEZONE_AWARE"
        )

    converted = timestamp.tz_convert(
        "UTC"
    )

    if converted is pd.NaT:

        raise InvalidOutcomeRecordError(
            f"{field_name}_UTC_CONVERSION_FAILED"
        )

    utc = cast(
        pd.Timestamp,
        converted,
    )

    text = utc.isoformat()

    if text.endswith(
        "+00:00"
    ):

        text = (
            text[
                :-6
            ]
            +
            "Z"
        )

    return text


def _require_finite_float(
    value: Any,
    field_name: str,
) -> float:

    try:
        number = float(
            value
        )

    except Exception as exc:
        raise InvalidOutcomeRecordError(
            f"{field_name}_NOT_NUMERIC"
        ) from exc

    if not math.isfinite(
        number
    ):
        raise InvalidOutcomeRecordError(
            f"{field_name}_NON_FINITE"
        )

    return number


def verify_authorities() -> bool:

    if (
        _maturer.MATURATION_VERSION
        !=
        EXPECTED_MATURATION_VERSION
    ):
        raise InvalidOutcomeRecordError(
            "MATURATION_VERSION_AUTHORITY_MISMATCH"
        )

    if (
        _maturer.EXPECTED_CONTRACT_FINGERPRINT_SHA256
        !=
        EXPECTED_CONTRACT_FINGERPRINT_SHA256
    ):
        raise InvalidOutcomeRecordError(
            "CONTRACT_FINGERPRINT_AUTHORITY_MISMATCH"
        )

    if (
        _maturer.EXPECTED_HORIZON_BARS
        !=
        EXPECTED_HORIZON_BARS
    ):
        raise InvalidOutcomeRecordError(
            "HORIZON_BARS_AUTHORITY_MISMATCH"
        )

    if (
        _maturer.EXPECTED_BASE_TIMEFRAME_MINUTES
        !=
        EXPECTED_BASE_TIMEFRAME_MINUTES
    ):
        raise InvalidOutcomeRecordError(
            "BASE_TIMEFRAME_MINUTES_AUTHORITY_MISMATCH"
        )

    if (
        _maturer.DECISION_BAR_SEMANTICS
        !=
        EXPECTED_DECISION_BAR_SEMANTICS
    ):
        raise InvalidOutcomeRecordError(
            "DECISION_BAR_SEMANTICS_AUTHORITY_MISMATCH"
        )

    if (
        _maturer.ENTRY_REFERENCE
        !=
        EXPECTED_ENTRY_REFERENCE
    ):
        raise InvalidOutcomeRecordError(
            "ENTRY_REFERENCE_AUTHORITY_MISMATCH"
        )

    if (
        _maturer.ATR_REFERENCE
        !=
        EXPECTED_ATR_REFERENCE
    ):
        raise InvalidOutcomeRecordError(
            "ATR_REFERENCE_AUTHORITY_MISMATCH"
        )

    if (
        _maturer.HORIZON_SEMANTICS
        !=
        EXPECTED_HORIZON_SEMANTICS
    ):
        raise InvalidOutcomeRecordError(
            "HORIZON_SEMANTICS_AUTHORITY_MISMATCH"
        )

    if (
        PERFORMANCE_EVALUATION_AUTHORIZED
        or
        PNL_EVALUATION_AUTHORIZED
        or
        LIVE_AUTHORIZED
        or
        EXECUTION_AUTHORIZED
    ):
        raise InvalidOutcomeRecordError(
            "OUTCOME_LEDGER_AUTHORIZATION_BOUNDARY_VIOLATION"
        )

    return True


def validate_outcome_document(
    document: Mapping[str, Any],
) -> Any:

    verify_authorities()

    logical_observation_id = (
        _require_sha256(
            document.get(
                "logical_observation_id"
            ),
            "LOGICAL_OBSERVATION_ID",
        )
    )

    source_observation_fingerprint = (
        _require_sha256(
            document.get(
                "source_observation_fingerprint"
            ),
            "SOURCE_OBSERVATION_FINGERPRINT",
        )
    )

    semantic_outcome_fingerprint = (
        _require_sha256(
            document.get(
                "semantic_outcome_fingerprint"
            ),
            "SEMANTIC_OUTCOME_FINGERPRINT",
        )
    )

    decision_time_utc = (
        _require_utc_timestamp(
            document.get(
                "decision_time_utc"
            ),
            "DECISION_TIME_UTC",
        )
    )

    decision_bar_open_time_utc = (
        _require_utc_timestamp(
            document.get(
                "decision_bar_open_time_utc"
            ),
            "DECISION_BAR_OPEN_TIME_UTC",
        )
    )

    decision_time_ts = cast(
        pd.Timestamp,
        pd.Timestamp(
            decision_time_utc
        ),
    )

    decision_bar_open_ts = cast(
        pd.Timestamp,
        pd.Timestamp(
            decision_bar_open_time_utc
        ),
    )

    expected_decision_time = (
        decision_bar_open_ts
        +
        pd.Timedelta(
            minutes=(
                EXPECTED_BASE_TIMEFRAME_MINUTES
            )
        )
    )

    if (
        decision_time_ts
        !=
        expected_decision_time
    ):
        raise InvalidOutcomeRecordError(
            "DECISION_BAR_TIME_MAPPING_MISMATCH"
        )

    outcome_class_raw = document.get(
        "outcome_class"
    )

    if not isinstance(
        outcome_class_raw,
        int,
    ):
        raise InvalidOutcomeRecordError(
            "OUTCOME_CLASS_NOT_INTEGER"
        )

    outcome_class = (
        outcome_class_raw
    )

    outcome_label = document.get(
        "outcome_label"
    )

    valid_mapping = {
        -1: "SHORT",
        0: "NO_TRADE",
        1: "LONG",
    }

    if (
        outcome_class
        not in valid_mapping
    ):
        raise InvalidOutcomeRecordError(
            "INVALID_OUTCOME_CLASS"
        )

    if (
        outcome_label
        !=
        valid_mapping[
            outcome_class
        ]
    ):
        raise InvalidOutcomeRecordError(
            "OUTCOME_CLASS_LABEL_MISMATCH"
        )

    entry_close = (
        _require_finite_float(
            document.get(
                "entry_close"
            ),
            "ENTRY_CLOSE",
        )
    )

    decision_atr14 = (
        _require_finite_float(
            document.get(
                "decision_atr14"
            ),
            "DECISION_ATR14",
        )
    )

    if entry_close <= 0.0:
        raise InvalidOutcomeRecordError(
            "ENTRY_CLOSE_NON_POSITIVE"
        )

    if decision_atr14 <= 0.0:
        raise InvalidOutcomeRecordError(
            "DECISION_ATR14_NON_POSITIVE"
        )

    horizon_bars_raw = document.get(
        "horizon_bars"
    )

    if not isinstance(
        horizon_bars_raw,
        int,
    ):
        raise InvalidOutcomeRecordError(
            "HORIZON_BARS_NOT_INTEGER"
        )

    horizon_bars = (
        horizon_bars_raw
    )

    if (
        horizon_bars
        !=
        EXPECTED_HORIZON_BARS
    ):
        raise InvalidOutcomeRecordError(
            "OUTCOME_HORIZON_BARS_MISMATCH"
        )

    horizon_semantics = (
        _require_string(
            document.get(
                "horizon_semantics"
            ),
            "HORIZON_SEMANTICS",
        )
    )

    if (
        horizon_semantics
        !=
        EXPECTED_HORIZON_SEMANTICS
    ):
        raise InvalidOutcomeRecordError(
            "OUTCOME_HORIZON_SEMANTICS_MISMATCH"
        )

    decision_bar_semantics = (
        _require_string(
            document.get(
                "decision_bar_semantics"
            ),
            "DECISION_BAR_SEMANTICS",
        )
    )

    if (
        decision_bar_semantics
        !=
        EXPECTED_DECISION_BAR_SEMANTICS
    ):
        raise InvalidOutcomeRecordError(
            "OUTCOME_DECISION_BAR_SEMANTICS_MISMATCH"
        )

    first_future_bar_time_utc = (
        _require_utc_timestamp(
            document.get(
                "first_future_bar_time_utc"
            ),
            "FIRST_FUTURE_BAR_TIME_UTC",
        )
    )

    last_future_bar_time_utc = (
        _require_utc_timestamp(
            document.get(
                "last_future_bar_time_utc"
            ),
            "LAST_FUTURE_BAR_TIME_UTC",
        )
    )

    first_future_ts = cast(
        pd.Timestamp,
        pd.Timestamp(
            first_future_bar_time_utc
        ),
    )

    last_future_ts = cast(
        pd.Timestamp,
        pd.Timestamp(
            last_future_bar_time_utc
        ),
    )

    if (
        first_future_ts
        <=
        decision_bar_open_ts
    ):
        raise InvalidOutcomeRecordError(
            "FIRST_FUTURE_BAR_NOT_AFTER_DECISION_BAR"
        )

    if (
        last_future_ts
        <=
        first_future_ts
    ):
        raise InvalidOutcomeRecordError(
            "LAST_FUTURE_BAR_NOT_AFTER_FIRST_FUTURE_BAR"
        )

    max_future_high = (
        _require_finite_float(
            document.get(
                "max_future_high"
            ),
            "MAX_FUTURE_HIGH",
        )
    )

    min_future_low = (
        _require_finite_float(
            document.get(
                "min_future_low"
            ),
            "MIN_FUTURE_LOW",
        )
    )

    up_excursion_atr = (
        _require_finite_float(
            document.get(
                "up_excursion_atr"
            ),
            "UP_EXCURSION_ATR",
        )
    )

    down_excursion_atr = (
        _require_finite_float(
            document.get(
                "down_excursion_atr"
            ),
            "DOWN_EXCURSION_ATR",
        )
    )

    contract_fingerprint = (
        _require_sha256(
            document.get(
                "contract_fingerprint_sha256"
            ),
            "CONTRACT_FINGERPRINT",
        )
    )

    if (
        contract_fingerprint
        !=
        EXPECTED_CONTRACT_FINGERPRINT_SHA256
    ):
        raise InvalidOutcomeRecordError(
            "OUTCOME_CONTRACT_FINGERPRINT_MISMATCH"
        )

    maturation_version = (
        _require_string(
            document.get(
                "maturation_version"
            ),
            "MATURATION_VERSION",
        )
    )

    if (
        maturation_version
        !=
        EXPECTED_MATURATION_VERSION
    ):
        raise InvalidOutcomeRecordError(
            "OUTCOME_MATURATION_VERSION_MISMATCH"
        )

    if (
        document.get(
            "performance_evaluation_authorized"
        )
        is not False
    ):
        raise InvalidOutcomeRecordError(
            "PERFORMANCE_AUTHORIZATION_VIOLATION"
        )

    if (
        document.get(
            "live_authorized"
        )
        is not False
    ):
        raise InvalidOutcomeRecordError(
            "LIVE_AUTHORIZATION_VIOLATION"
        )

    if (
        document.get(
            "execution_authorized"
        )
        is not False
    ):
        raise InvalidOutcomeRecordError(
            "EXECUTION_AUTHORIZATION_VIOLATION"
        )

    outcome = FrozenC04ForwardOutcome(
        logical_observation_id=(
            logical_observation_id
        ),

        decision_time_utc=(
            decision_time_utc
        ),

        decision_bar_open_time_utc=(
            decision_bar_open_time_utc
        ),

        outcome_class=(
            outcome_class
        ),

        outcome_label=(
            str(
                outcome_label
            )
        ),

        entry_close=(
            entry_close
        ),

        decision_atr14=(
            decision_atr14
        ),

        horizon_bars=(
            horizon_bars
        ),

        horizon_semantics=(
            horizon_semantics
        ),

        decision_bar_semantics=(
            decision_bar_semantics
        ),

        first_future_bar_time_utc=(
            first_future_bar_time_utc
        ),

        last_future_bar_time_utc=(
            last_future_bar_time_utc
        ),

        max_future_high=(
            max_future_high
        ),

        min_future_low=(
            min_future_low
        ),

        up_excursion_atr=(
            up_excursion_atr
        ),

        down_excursion_atr=(
            down_excursion_atr
        ),

        source_observation_fingerprint=(
            source_observation_fingerprint
        ),
    )

    recomputed = (
        outcome.semantic_fingerprint()
    )

    if (
        recomputed
        !=
        semantic_outcome_fingerprint
    ):
        raise InvalidOutcomeRecordError(
            (
                "SEMANTIC_OUTCOME_FINGERPRINT_MISMATCH:"
                f"{semantic_outcome_fingerprint}!="
                f"{recomputed}"
            )
        )

    return outcome


@contextlib.contextmanager
def _file_lock(
    fd: Any,
) -> Generator[
    None,
    None,
    None,
]:

    if sys.platform == "win32":

        import msvcrt

        fd.seek(
            0,
            os.SEEK_SET,
        )

        msvcrt.locking(
            fd.fileno(),
            msvcrt.LK_LOCK,
            1,
        )

        try:
            yield

        finally:

            fd.seek(
                0,
                os.SEEK_SET,
            )

            msvcrt.locking(
                fd.fileno(),
                msvcrt.LK_UNLCK,
                1,
            )

    else:

        import fcntl

        fcntl.flock(
            fd.fileno(),
            fcntl.LOCK_EX,
        )

        try:
            yield

        finally:

            fcntl.flock(
                fd.fileno(),
                fcntl.LOCK_UN,
            )


class FrozenC04ForwardOutcomeLedger:

    def __init__(
        self,
        ledger_path: Path | str,
        duplicate_handling: (
            OutcomeDuplicateHandling
        ) = (
            OutcomeDuplicateHandling.FAIL_CLOSED
        ),
    ) -> None:

        self._path = Path(
            ledger_path
        ).resolve()

        self._duplicate_handling = (
            duplicate_handling
        )

        self._index: dict[
            str,
            str,
        ] = {}

        if self._path.exists():

            self._rebuild_index_and_verify()

        else:

            self._path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

    @property
    def path(
        self,
    ) -> Path:

        return self._path

    def _rebuild_index_and_verify(
        self,
    ) -> None:

        self._index.clear()

        if not self._path.is_file():
            return

        with self._path.open(
            "r",
            encoding="utf-8",
        ) as handle:

            for (
                line_number,
                raw_line,
            ) in enumerate(
                handle,
                start=1,
            ):

                line = raw_line.strip()

                if not line:
                    continue

                try:

                    value = json.loads(
                        line
                    )

                    if not isinstance(
                        value,
                        dict,
                    ):
                        raise InvalidOutcomeRecordError(
                            "OUTCOME_RECORD_NOT_OBJECT"
                        )

                    outcome = (
                        validate_outcome_document(
                            value
                        )
                    )

                except Exception as exc:

                    raise CorruptedOutcomeLedgerError(
                        (
                            "OUTCOME_LEDGER_CORRUPTED:"
                            f"line={line_number}:"
                            f"{exc}"
                        )
                    ) from exc

                logical_id = (
                    outcome.logical_observation_id
                )

                semantic_fp = (
                    outcome.semantic_fingerprint()
                )

                if logical_id in self._index:

                    existing_fp = (
                        self._index[
                            logical_id
                        ]
                    )

                    if (
                        existing_fp
                        !=
                        semantic_fp
                    ):

                        raise ConflictingOutcomeError(
                            (
                                "CONFLICTING_OUTCOMES_IN_LEDGER:"
                                f"{logical_id}"
                            )
                        )

                self._index[
                    logical_id
                ] = semantic_fp

    def validate_integrity(
        self,
    ) -> bool:

        self._rebuild_index_and_verify()

        return True

    def count(
        self,
    ) -> int:

        return len(
            self._index
        )

    def append(
        self,
        outcome: Any,
    ) -> OutcomeAppendResult:

        document = (
            outcome.to_dict()
        )

        validated = (
            validate_outcome_document(
                document
            )
        )

        logical_id = (
            validated.logical_observation_id
        )

        semantic_fp = (
            validated.semantic_fingerprint()
        )

        if logical_id in self._index:

            existing_fp = (
                self._index[
                    logical_id
                ]
            )

            if (
                existing_fp
                !=
                semantic_fp
            ):

                raise ConflictingOutcomeError(
                    (
                        "CONFLICTING_OUTCOME:"
                        f"{logical_id}:"
                        f"{existing_fp}!="
                        f"{semantic_fp}"
                    )
                )

            if (
                self._duplicate_handling
                ==
                OutcomeDuplicateHandling.FAIL_CLOSED
            ):

                raise DuplicateOutcomeError(
                    (
                        "DUPLICATE_OUTCOME_REJECTED:"
                        f"{logical_id}"
                    )
                )

            return OutcomeAppendResult(
                record=(
                    validated
                ),

                is_duplicate=True,

                appended=False,

                message=(
                    "IDEMPOTENT_DUPLICATE_IGNORED:"
                    f"{logical_id}"
                ),
            )

        line = (
            json.dumps(
                validated.to_dict(),
                sort_keys=True,
                separators=(
                    ",",
                    ":",
                ),
                allow_nan=False,
            )
            +
            "\n"
        )

        try:

            with self._path.open(
                "a+",
                encoding="utf-8",
            ) as handle:

                with _file_lock(
                    handle
                ):

                    handle.seek(
                        0,
                        os.SEEK_END,
                    )

                    handle.write(
                        line
                    )

                    handle.flush()

                    os.fsync(
                        handle.fileno()
                    )

        except Exception as exc:

            raise CorruptedOutcomeLedgerError(
                (
                    "FAILED_TO_APPEND_OUTCOME:"
                    f"{self._path}:"
                    f"{exc}"
                )
            ) from exc

        self._index[
            logical_id
        ] = semantic_fp

        return OutcomeAppendResult(
            record=(
                validated
            ),

            is_duplicate=False,

            appended=True,

            message=(
                "OUTCOME_RECORDED:"
                f"{logical_id}"
            ),
        )

    def read_all(
        self,
    ) -> list[Any]:

        records: list[Any] = []

        if not self._path.exists():
            return records

        with self._path.open(
            "r",
            encoding="utf-8",
        ) as handle:

            for (
                line_number,
                raw_line,
            ) in enumerate(
                handle,
                start=1,
            ):

                line = raw_line.strip()

                if not line:
                    continue

                try:

                    value = json.loads(
                        line
                    )

                    if not isinstance(
                        value,
                        dict,
                    ):
                        raise InvalidOutcomeRecordError(
                            "OUTCOME_RECORD_NOT_OBJECT"
                        )

                    records.append(
                        validate_outcome_document(
                            value
                        )
                    )

                except Exception as exc:

                    raise CorruptedOutcomeLedgerError(
                        (
                            "OUTCOME_LEDGER_CORRUPTED:"
                            f"line={line_number}:"
                            f"{exc}"
                        )
                    ) from exc

        return records