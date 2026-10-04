from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Generator, Mapping, cast

import numpy as np
import pandas as pd


REPO_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


_runtime: Any = importlib.import_module(
    "02_AI.Models.frozen_r03_prospective_runtime"
)

_contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_contract"
)


MATURATION_VERSION = (
    "FROZEN_R03_PROSPECTIVE_OUTCOME_MATURER_V1"
)

OUTCOME_SCHEMA_VERSION = (
    "R03_PROSPECTIVE_OUTCOME_V1"
)

EXPECTED_CONTRACT_FINGERPRINT_SHA256 = (
    "01fe52a2f068fcc8fb2fc5b89dd7e19dc974fc2d967cfb791e75c3415804ce87"
)

EXPECTED_PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256 = (
    "e70d8e26c8f4734c456022689d47de406fe3f8daf1827d01b7f0f0d7fe752b9e"
)

EXPECTED_ARTIFACT_SHA256 = (
    "b5da550921ef227b847207cfbfe5774e86f083f1d3354069a9624a5029ea2a03"
)

EXPECTED_FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

EXPECTED_CANONICAL_INSTRUMENT = "XAUUSD"

EXPECTED_HORIZON_BARS = 12

EXPECTED_BASE_TIMEFRAME_MINUTES = 5

EXPECTED_PROFIT_ATR = 1.25

EXPECTED_MAX_ADVERSE_ATR = 0.75

HORIZON_SEMANTICS = (
    "NEXT_12_COMPLETED_M5_ROWS_AFTER_DECISION_BAR"
)

ENTRY_REFERENCE = (
    "PROSPECTIVE_ANCHOR_DECISION_M5_CLOSE"
)

ATR_REFERENCE = (
    "PROSPECTIVE_ANCHOR_DECISION_M5_ATR14"
)

FUTURE_DATA_POLICY = (
    "OUTCOME_ONLY_NEVER_FEATURE_OR_INFERENCE_INPUT"
)

OUTCOME_LEDGER_RELATIVE_PATH = (
    "01_Data/Shadow/"
    "xauusd_r03_prospective_forward_outcomes.jsonl"
)

OUTCOME_MATURATION_AUTHORIZED = True
PERFORMANCE_EVALUATION_AUTHORIZED = False
PNL_EVALUATION_AUTHORIZED = False
LIVE_AUTHORIZED = False
EXECUTION_AUTHORIZED = False


class R03OutcomeMaturationError(
    RuntimeError
):
    pass


class InsufficientFutureBarsError(
    R03OutcomeMaturationError
):
    pass


class R03OutcomeLedgerError(
    RuntimeError
):
    pass


class R03OutcomeLedgerConflictError(
    R03OutcomeLedgerError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise R03OutcomeMaturationError(
            reason
        )


def validate_sha256(
    value: Any,
    field: str,
) -> str:

    if not isinstance(
        value,
        str,
    ):
        raise R03OutcomeMaturationError(
            f"{field}_NOT_STRING"
        )

    normalized = (
        value.strip()
        .lower()
    )

    if (
        len(
            normalized
        )
        !=
        64
        or
        any(
            char
            not in
            "0123456789abcdef"
            for char
            in normalized
        )
    ):
        raise R03OutcomeMaturationError(
            f"{field}_INVALID_SHA256"
        )

    return normalized


def utc_timestamp(
    value: Any,
) -> pd.Timestamp:

    try:
        parsed = pd.Timestamp(
            value
        )
    except Exception as exc:
        raise R03OutcomeMaturationError(
            "INVALID_TIMESTAMP"
        ) from exc

    if parsed is pd.NaT:
        raise R03OutcomeMaturationError(
            "INVALID_TIMESTAMP"
        )

    timestamp = cast(
        pd.Timestamp,
        parsed,
    )

    if timestamp.tzinfo is None:
        raise R03OutcomeMaturationError(
            "TIMESTAMP_MUST_BE_TIMEZONE_AWARE"
        )

    converted = timestamp.tz_convert(
        "UTC"
    )

    if converted is pd.NaT:
        raise R03OutcomeMaturationError(
            "TIMESTAMP_UTC_CONVERSION_FAILED"
        )

    return cast(
        pd.Timestamp,
        converted,
    )


def utc_iso(
    value: Any,
) -> str:

    output = utc_timestamp(
        value
    ).isoformat()

    if output.endswith(
        "+00:00"
    ):
        output = (
            output[:-6]
            +
            "Z"
        )

    return output


def finite_positive(
    value: Any,
    field: str,
) -> float:

    if value is None:
        raise R03OutcomeMaturationError(
            f"{field}_MISSING"
        )

    try:
        number = float(
            value
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise R03OutcomeMaturationError(
            f"{field}_NOT_NUMERIC"
        ) from exc

    if (
        not math.isfinite(
            number
        )
        or
        number
        <=
        0.0
    ):
        raise R03OutcomeMaturationError(
            f"{field}_NOT_POSITIVE_FINITE"
        )

    return number


def require_int(
    value: Any,
    field: str,
) -> int:

    if value is None:
        raise R03OutcomeMaturationError(
            f"{field}_MISSING"
        )

    try:
        number = int(
            value
        )

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise R03OutcomeMaturationError(
            f"{field}_NOT_INTEGER"
        ) from exc

    return number


def canonical_json_sha256(
    document: Mapping[str, Any],
) -> str:

    payload = json.dumps(
        dict(
            document
        ),
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=False,
        allow_nan=False,
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        payload
    ).hexdigest()


def verify_authorities() -> bool:

    require(
        _contract.compute_contract_fingerprint()
        ==
        EXPECTED_CONTRACT_FINGERPRINT_SHA256,
        "OUTCOME_CONTRACT_FINGERPRINT_MISMATCH",
    )

    require(
        _runtime.PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256
        ==
        EXPECTED_PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256,
        "PROSPECTIVE_CONTRACT_FINGERPRINT_MISMATCH",
    )

    require(
        _runtime.ARTIFACT_SHA256
        ==
        EXPECTED_ARTIFACT_SHA256,
        "R03_ARTIFACT_AUTHORITY_MISMATCH",
    )

    require(
        _runtime.FEATURE_COLUMNS_SHA256
        ==
        EXPECTED_FEATURE_COLUMNS_SHA256,
        "FEATURE_AUTHORITY_MISMATCH",
    )

    require(
        int(
            _contract.HORIZON_BARS
        )
        ==
        EXPECTED_HORIZON_BARS,
        "HORIZON_AUTHORITY_MISMATCH",
    )

    require(
        math.isclose(
            float(
                _contract.PROFIT_ATR
            ),
            EXPECTED_PROFIT_ATR,
        ),
        "PROFIT_ATR_AUTHORITY_MISMATCH",
    )

    require(
        math.isclose(
            float(
                _contract.MAX_ADVERSE_ATR
            ),
            EXPECTED_MAX_ADVERSE_ATR,
        ),
        "MAX_ADVERSE_ATR_AUTHORITY_MISMATCH",
    )

    require(
        not PERFORMANCE_EVALUATION_AUTHORIZED,
        "PERFORMANCE_AUTHORIZED",
    )

    require(
        not PNL_EVALUATION_AUTHORIZED,
        "PNL_AUTHORIZED",
    )

    require(
        not LIVE_AUTHORIZED,
        "LIVE_AUTHORIZED",
    )

    require(
        not EXECUTION_AUTHORIZED,
        "EXECUTION_AUTHORIZED",
    )

    return True


def label_outcome(
    *,
    up_excursion_atr: float,
    down_excursion_atr: float,
) -> tuple[int, str]:

    long_mask = (
        up_excursion_atr
        >=
        EXPECTED_PROFIT_ATR
        and
        down_excursion_atr
        <=
        EXPECTED_MAX_ADVERSE_ATR
    )

    short_mask = (
        down_excursion_atr
        >=
        EXPECTED_PROFIT_ATR
        and
        up_excursion_atr
        <=
        EXPECTED_MAX_ADVERSE_ATR
    )

    if (
        long_mask
        and
        short_mask
    ):
        raise R03OutcomeMaturationError(
            "IMPOSSIBLE_TARGET_OVERLAP"
        )

    if long_mask:
        return (
            1,
            "LONG",
        )

    if short_mask:
        return (
            -1,
            "SHORT",
        )

    return (
        0,
        "NO_TRADE",
    )


@dataclasses.dataclass(
    frozen=True
)
class R03ProspectiveOutcomeRecord:

    logical_observation_id: str

    semantic_outcome_fingerprint: str

    decision_time_utc: str

    decision_bar_open_time_utc: str

    outcome_class: int

    outcome_label: str

    entry_close: float

    decision_atr14: float

    horizon_bars: int

    first_future_bar_time_utc: str

    last_future_bar_time_utc: str

    max_future_high: float

    min_future_low: float

    up_excursion_atr: float

    down_excursion_atr: float

    source_observation_fingerprint: str

    source_anchor_fingerprint: str

    feature_columns_sha256: str

    model_artifact_sha256: str

    outcome_contract_fingerprint_sha256: str

    prospective_contract_fingerprint_sha256: str

    performance_evaluation_authorized: bool = False

    live_authorized: bool = False

    execution_authorized: bool = False

    def semantic_document(
        self,
    ) -> dict[str, Any]:

        return {
            "schema_version": (
                OUTCOME_SCHEMA_VERSION
            ),
            "logical_observation_id": (
                self.logical_observation_id
            ),
            "decision_time_utc": (
                self.decision_time_utc
            ),
            "decision_bar_open_time_utc": (
                self.decision_bar_open_time_utc
            ),
            "outcome_class": (
                self.outcome_class
            ),
            "outcome_label": (
                self.outcome_label
            ),
            "entry_close": (
                self.entry_close
            ),
            "decision_atr14": (
                self.decision_atr14
            ),
            "horizon_bars": (
                self.horizon_bars
            ),
            "horizon_semantics": (
                HORIZON_SEMANTICS
            ),
            "entry_reference": (
                ENTRY_REFERENCE
            ),
            "atr_reference": (
                ATR_REFERENCE
            ),
            "future_data_policy": (
                FUTURE_DATA_POLICY
            ),
            "first_future_bar_time_utc": (
                self.first_future_bar_time_utc
            ),
            "last_future_bar_time_utc": (
                self.last_future_bar_time_utc
            ),
            "max_future_high": (
                self.max_future_high
            ),
            "min_future_low": (
                self.min_future_low
            ),
            "up_excursion_atr": (
                self.up_excursion_atr
            ),
            "down_excursion_atr": (
                self.down_excursion_atr
            ),
            "source_observation_fingerprint": (
                self.source_observation_fingerprint
            ),
            "source_anchor_fingerprint": (
                self.source_anchor_fingerprint
            ),
            "feature_columns_sha256": (
                self.feature_columns_sha256
            ),
            "model_artifact_sha256": (
                self.model_artifact_sha256
            ),
            "outcome_contract_fingerprint_sha256": (
                self.outcome_contract_fingerprint_sha256
            ),
            "prospective_contract_fingerprint_sha256": (
                self.prospective_contract_fingerprint_sha256
            ),
            "maturation_version": (
                MATURATION_VERSION
            ),
            "performance_evaluation_authorized": False,
            "live_authorized": False,
            "execution_authorized": False,
        }

    def to_dict(
        self,
    ) -> dict[str, Any]:

        document = (
            self.semantic_document()
        )

        document[
            "semantic_outcome_fingerprint"
        ] = (
            self.semantic_outcome_fingerprint
        )

        return document


def outcome_fingerprint(
    document: Mapping[str, Any],
) -> str:

    semantic = dict(
        document
    )

    semantic.pop(
        "semantic_outcome_fingerprint",
        None,
    )

    return canonical_json_sha256(
        semantic
    )


def validate_completed_m5(
    frame: pd.DataFrame,
) -> pd.DataFrame:

    required_columns = {
        "time",
        "open",
        "high",
        "low",
        "close",
    }

    missing = (
        required_columns
        -
        set(
            frame.columns
        )
    )

    if missing:
        raise R03OutcomeMaturationError(
            (
                "M5_REQUIRED_COLUMNS_MISSING:"
                f"{sorted(missing)}"
            )
        )

    if frame.empty:
        raise R03OutcomeMaturationError(
            "M5_FRAME_EMPTY"
        )

    output = frame.copy()

    output[
        "time"
    ] = pd.to_datetime(
        output[
            "time"
        ],
        utc=True,
        errors="raise",
    )

    output = (
        output
        .sort_values(
            "time"
        )
        .reset_index(
            drop=True
        )
    )

    if bool(
        output[
            "time"
        ]
        .duplicated()
        .any()
    ):
        raise R03OutcomeMaturationError(
            "M5_DUPLICATE_TIMESTAMPS"
        )

    for column in (
        "open",
        "high",
        "low",
        "close",
    ):

        output[
            column
        ] = pd.to_numeric(
            output[
                column
            ],
            errors="coerce",
        )

    values = output[
        [
            "open",
            "high",
            "low",
            "close",
        ]
    ].to_numpy(
        dtype=np.float64
    )

    if not bool(
        np.isfinite(
            values
        ).all()
    ):
        raise R03OutcomeMaturationError(
            "M5_NON_FINITE_OHLC"
        )

    return output


def mature_observation(
    *,
    observation: Any,
    anchor: Any,
    completed_m5_bars: pd.DataFrame,
) -> R03ProspectiveOutcomeRecord:

    verify_authorities()

    if not isinstance(
        observation,
        _runtime.R03ProspectiveObservationRecord,
    ):
        raise R03OutcomeMaturationError(
            "R03_OBSERVATION_RECORD_REQUIRED"
        )

    if not isinstance(
        anchor,
        _runtime.R03ProspectiveAnchorRecord,
    ):
        raise R03OutcomeMaturationError(
            "R03_ANCHOR_RECORD_REQUIRED"
        )

    if (
        observation.logical_observation_id
        !=
        anchor.logical_observation_id
    ):
        raise R03OutcomeMaturationError(
            "OBSERVATION_ANCHOR_ID_MISMATCH"
        )

    if (
        observation.semantic_record_fingerprint
        !=
        anchor.semantic_observation_fingerprint
    ):
        raise R03OutcomeMaturationError(
            "OBSERVATION_ANCHOR_FINGERPRINT_MISMATCH"
        )

    if (
        observation.source_snapshot_id
        !=
        anchor.source_snapshot_id
    ):
        raise R03OutcomeMaturationError(
            "OBSERVATION_ANCHOR_SNAPSHOT_MISMATCH"
        )

    if (
        anchor.model_artifact_sha256
        !=
        EXPECTED_ARTIFACT_SHA256
    ):
        raise R03OutcomeMaturationError(
            "ANCHOR_ARTIFACT_AUTHORITY_MISMATCH"
        )

    decision_time = utc_timestamp(
        anchor.decision_time_utc
    )

    decision_open = utc_timestamp(
        anchor.decision_bar_open_time_utc
    )

    if (
        decision_open
        +
        pd.Timedelta(
            minutes=(
                EXPECTED_BASE_TIMEFRAME_MINUTES
            )
        )
        !=
        decision_time
    ):
        raise R03OutcomeMaturationError(
            "DECISION_BAR_MAPPING_MISMATCH"
        )

    entry_close = finite_positive(
        anchor.decision_m5_close,
        "ANCHOR_DECISION_CLOSE",
    )

    decision_atr = finite_positive(
        anchor.decision_m5_atr14,
        "ANCHOR_DECISION_ATR14",
    )

    raw = validate_completed_m5(
        completed_m5_bars
    )

    decision_positions = np.flatnonzero(
        (
            raw[
                "time"
            ]
            ==
            decision_open
        ).to_numpy(
            dtype=bool
        )
    )

    if (
        len(
            decision_positions
        )
        !=
        1
    ):
        raise R03OutcomeMaturationError(
            (
                "DECISION_BAR_NOT_UNIQUE:"
                f"{len(decision_positions)}"
            )
        )

    start = (
        int(
            decision_positions[
                0
            ]
        )
        +
        1
    )

    end = (
        start
        +
        EXPECTED_HORIZON_BARS
    )

    if (
        end
        >
        len(
            raw
        )
    ):

        available = max(
            0,
            len(
                raw
            )
            -
            start,
        )

        raise InsufficientFutureBarsError(
            (
                "INSUFFICIENT_COMPLETED_FUTURE_M5_BARS:"
                f"{available}/"
                f"{EXPECTED_HORIZON_BARS}"
            )
        )

    future = (
        raw.iloc[
            start:end
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    require(
        len(
            future
        )
        ==
        EXPECTED_HORIZON_BARS,
        "EXACT_12_FUTURE_M5_ROWS_REQUIRED",
    )

    expected_first = (
        decision_open
        +
        pd.Timedelta(
            minutes=5
        )
    )

    expected_last = (
        decision_open
        +
        pd.Timedelta(
            minutes=(
                5
                *
                EXPECTED_HORIZON_BARS
            )
        )
    )

    first_future = utc_timestamp(
        future[
            "time"
        ]
        .iloc[
            0
        ]
    )

    last_future = utc_timestamp(
        future[
            "time"
        ]
        .iloc[
            -1
        ]
    )

    if (
        first_future
        !=
        expected_first
    ):
        raise R03OutcomeMaturationError(
            "FIRST_FUTURE_M5_BAR_NOT_CONTIGUOUS"
        )

    if (
        last_future
        !=
        expected_last
    ):
        raise R03OutcomeMaturationError(
            "LAST_FUTURE_M5_BAR_NOT_CONTIGUOUS"
        )

    expected_times = pd.date_range(
        start=(
            expected_first
        ),
        periods=(
            EXPECTED_HORIZON_BARS
        ),
        freq="5min",
    )

    actual_times = pd.DatetimeIndex(
        future[
            "time"
        ]
    )

    if not actual_times.equals(
        expected_times
    ):
        raise R03OutcomeMaturationError(
            "FUTURE_M5_HORIZON_HAS_GAP"
        )

    max_future_high = float(
        future[
            "high"
        ].max()
    )

    min_future_low = float(
        future[
            "low"
        ].min()
    )

    require(
        math.isfinite(
            max_future_high
        ),
        "MAX_FUTURE_HIGH_NON_FINITE",
    )

    require(
        math.isfinite(
            min_future_low
        ),
        "MIN_FUTURE_LOW_NON_FINITE",
    )

    up_excursion = (
        (
            max_future_high
            -
            entry_close
        )
        /
        decision_atr
    )

    down_excursion = (
        (
            entry_close
            -
            min_future_low
        )
        /
        decision_atr
    )

    require(
        math.isfinite(
            up_excursion
        ),
        "UP_EXCURSION_NON_FINITE",
    )

    require(
        math.isfinite(
            down_excursion
        ),
        "DOWN_EXCURSION_NON_FINITE",
    )

    outcome_class, outcome_label = (
        label_outcome(
            up_excursion_atr=(
                up_excursion
            ),
            down_excursion_atr=(
                down_excursion
            ),
        )
    )

    base_document: dict[str, Any] = {
        "schema_version": (
            OUTCOME_SCHEMA_VERSION
        ),
        "logical_observation_id": (
            observation.logical_observation_id
        ),
        "decision_time_utc": (
            observation.decision_time_utc
        ),
        "decision_bar_open_time_utc": (
            anchor.decision_bar_open_time_utc
        ),
        "outcome_class": (
            outcome_class
        ),
        "outcome_label": (
            outcome_label
        ),
        "entry_close": (
            entry_close
        ),
        "decision_atr14": (
            decision_atr
        ),
        "horizon_bars": (
            EXPECTED_HORIZON_BARS
        ),
        "horizon_semantics": (
            HORIZON_SEMANTICS
        ),
        "entry_reference": (
            ENTRY_REFERENCE
        ),
        "atr_reference": (
            ATR_REFERENCE
        ),
        "future_data_policy": (
            FUTURE_DATA_POLICY
        ),
        "first_future_bar_time_utc": (
            utc_iso(
                first_future
            )
        ),
        "last_future_bar_time_utc": (
            utc_iso(
                last_future
            )
        ),
        "max_future_high": (
            max_future_high
        ),
        "min_future_low": (
            min_future_low
        ),
        "up_excursion_atr": (
            up_excursion
        ),
        "down_excursion_atr": (
            down_excursion
        ),
        "source_observation_fingerprint": (
            observation.semantic_record_fingerprint
        ),
        "source_anchor_fingerprint": (
            anchor.anchor_semantic_fingerprint
        ),
        "feature_columns_sha256": (
            EXPECTED_FEATURE_COLUMNS_SHA256
        ),
        "model_artifact_sha256": (
            EXPECTED_ARTIFACT_SHA256
        ),
        "outcome_contract_fingerprint_sha256": (
            EXPECTED_CONTRACT_FINGERPRINT_SHA256
        ),
        "prospective_contract_fingerprint_sha256": (
            EXPECTED_PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256
        ),
        "maturation_version": (
            MATURATION_VERSION
        ),
        "performance_evaluation_authorized": False,
        "live_authorized": False,
        "execution_authorized": False,
    }

    fingerprint = outcome_fingerprint(
        base_document
    )

    return R03ProspectiveOutcomeRecord(
        logical_observation_id=(
            observation.logical_observation_id
        ),
        semantic_outcome_fingerprint=(
            fingerprint
        ),
        decision_time_utc=(
            observation.decision_time_utc
        ),
        decision_bar_open_time_utc=(
            anchor.decision_bar_open_time_utc
        ),
        outcome_class=(
            outcome_class
        ),
        outcome_label=(
            outcome_label
        ),
        entry_close=(
            entry_close
        ),
        decision_atr14=(
            decision_atr
        ),
        horizon_bars=(
            EXPECTED_HORIZON_BARS
        ),
        first_future_bar_time_utc=(
            utc_iso(
                first_future
            )
        ),
        last_future_bar_time_utc=(
            utc_iso(
                last_future
            )
        ),
        max_future_high=(
            max_future_high
        ),
        min_future_low=(
            min_future_low
        ),
        up_excursion_atr=(
            up_excursion
        ),
        down_excursion_atr=(
            down_excursion
        ),
        source_observation_fingerprint=(
            observation.semantic_record_fingerprint
        ),
        source_anchor_fingerprint=(
            anchor.anchor_semantic_fingerprint
        ),
        feature_columns_sha256=(
            EXPECTED_FEATURE_COLUMNS_SHA256
        ),
        model_artifact_sha256=(
            EXPECTED_ARTIFACT_SHA256
        ),
        outcome_contract_fingerprint_sha256=(
            EXPECTED_CONTRACT_FINGERPRINT_SHA256
        ),
        prospective_contract_fingerprint_sha256=(
            EXPECTED_PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256
        ),
        performance_evaluation_authorized=False,
        live_authorized=False,
        execution_authorized=False,
    )


def validate_outcome_document(
    document: Mapping[str, Any],
) -> R03ProspectiveOutcomeRecord:

    if (
        document.get(
            "schema_version"
        )
        !=
        OUTCOME_SCHEMA_VERSION
    ):
        raise R03OutcomeMaturationError(
            "OUTCOME_SCHEMA_MISMATCH"
        )

    logical_id = validate_sha256(
        document.get(
            "logical_observation_id"
        ),
        "LOGICAL_OBSERVATION_ID",
    )

    fingerprint = validate_sha256(
        document.get(
            "semantic_outcome_fingerprint"
        ),
        "SEMANTIC_OUTCOME_FINGERPRINT",
    )

    if (
        document.get(
            "model_artifact_sha256"
        )
        !=
        EXPECTED_ARTIFACT_SHA256
    ):
        raise R03OutcomeMaturationError(
            "OUTCOME_ARTIFACT_AUTHORITY_MISMATCH"
        )

    if (
        document.get(
            "feature_columns_sha256"
        )
        !=
        EXPECTED_FEATURE_COLUMNS_SHA256
    ):
        raise R03OutcomeMaturationError(
            "OUTCOME_FEATURE_AUTHORITY_MISMATCH"
        )

    if (
        document.get(
            "outcome_contract_fingerprint_sha256"
        )
        !=
        EXPECTED_CONTRACT_FINGERPRINT_SHA256
    ):
        raise R03OutcomeMaturationError(
            "OUTCOME_CONTRACT_AUTHORITY_MISMATCH"
        )

    if (
        document.get(
            "prospective_contract_fingerprint_sha256"
        )
        !=
        EXPECTED_PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256
    ):
        raise R03OutcomeMaturationError(
            "OUTCOME_PROSPECTIVE_CONTRACT_AUTHORITY_MISMATCH"
        )

    if (
        int(
            document.get(
                "horizon_bars",
                -1,
            )
        )
        !=
        EXPECTED_HORIZON_BARS
    ):
        raise R03OutcomeMaturationError(
            "OUTCOME_HORIZON_MISMATCH"
        )

    if (
        document.get(
            "horizon_semantics"
        )
        !=
        HORIZON_SEMANTICS
    ):
        raise R03OutcomeMaturationError(
            "OUTCOME_HORIZON_SEMANTICS_MISMATCH"
        )

    if (
        document.get(
            "performance_evaluation_authorized"
        )
        is not False
    ):
        raise R03OutcomeMaturationError(
            "OUTCOME_PERFORMANCE_AUTHORIZATION_VIOLATION"
        )

    if (
        document.get(
            "live_authorized"
        )
        is not False
    ):
        raise R03OutcomeMaturationError(
            "OUTCOME_LIVE_AUTHORIZATION_VIOLATION"
        )

    if (
        document.get(
            "execution_authorized"
        )
        is not False
    ):
        raise R03OutcomeMaturationError(
            "OUTCOME_EXECUTION_AUTHORIZATION_VIOLATION"
        )

    supplied = dict(
        document
    )

    expected_fp = outcome_fingerprint(
        supplied
    )

    if (
        fingerprint
        !=
        expected_fp
    ):
        raise R03OutcomeMaturationError(
            "OUTCOME_SEMANTIC_FINGERPRINT_MISMATCH"
        )

    return R03ProspectiveOutcomeRecord(
        logical_observation_id=(
            logical_id
        ),
        semantic_outcome_fingerprint=(
            fingerprint
        ),
        decision_time_utc=utc_iso(
            document.get(
                "decision_time_utc"
            )
        ),
        decision_bar_open_time_utc=utc_iso(
            document.get(
                "decision_bar_open_time_utc"
            )
        ),
        outcome_class=require_int(
            document.get(
                "outcome_class"
            ),
            "OUTCOME_CLASS",
        ),
        outcome_label=str(
            document.get(
                "outcome_label"
            )
        ),
        entry_close=finite_positive(
            document.get(
                "entry_close"
            ),
            "ENTRY_CLOSE",
        ),
        decision_atr14=finite_positive(
            document.get(
                "decision_atr14"
            ),
            "DECISION_ATR14",
        ),
        horizon_bars=(
            EXPECTED_HORIZON_BARS
        ),
        first_future_bar_time_utc=utc_iso(
            document.get(
                "first_future_bar_time_utc"
            )
        ),
        last_future_bar_time_utc=utc_iso(
            document.get(
                "last_future_bar_time_utc"
            )
        ),
        max_future_high=float(
            document[
                "max_future_high"
            ]
        ),
        min_future_low=float(
            document[
                "min_future_low"
            ]
        ),
        up_excursion_atr=float(
            document[
                "up_excursion_atr"
            ]
        ),
        down_excursion_atr=float(
            document[
                "down_excursion_atr"
            ]
        ),
        source_observation_fingerprint=validate_sha256(
            document.get(
                "source_observation_fingerprint"
            ),
            "SOURCE_OBSERVATION_FINGERPRINT",
        ),
        source_anchor_fingerprint=validate_sha256(
            document.get(
                "source_anchor_fingerprint"
            ),
            "SOURCE_ANCHOR_FINGERPRINT",
        ),
        feature_columns_sha256=(
            EXPECTED_FEATURE_COLUMNS_SHA256
        ),
        model_artifact_sha256=(
            EXPECTED_ARTIFACT_SHA256
        ),
        outcome_contract_fingerprint_sha256=(
            EXPECTED_CONTRACT_FINGERPRINT_SHA256
        ),
        prospective_contract_fingerprint_sha256=(
            EXPECTED_PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256
        ),
        performance_evaluation_authorized=False,
        live_authorized=False,
        execution_authorized=False,
    )


@contextlib.contextmanager
def file_lock(
    handle: Any,
) -> Generator[
    None,
    None,
    None,
]:

    if sys.platform == "win32":

        import msvcrt

        handle.seek(
            0,
            os.SEEK_SET,
        )

        msvcrt.locking(
            handle.fileno(),
            msvcrt.LK_LOCK,
            1,
        )

        try:
            yield

        finally:

            handle.seek(
                0,
                os.SEEK_SET,
            )

            msvcrt.locking(
                handle.fileno(),
                msvcrt.LK_UNLCK,
                1,
            )

    else:

        import fcntl

        fcntl.flock(
            handle.fileno(),
            fcntl.LOCK_EX,
        )

        try:
            yield

        finally:

            fcntl.flock(
                handle.fileno(),
                fcntl.LOCK_UN,
            )


@dataclasses.dataclass(
    frozen=True
)
class OutcomeAppendResult:

    appended: bool

    is_duplicate: bool

    logical_observation_id: str


class R03ProspectiveOutcomeLedger:

    def __init__(
        self,
        path: Path,
    ) -> None:

        self._path = path.resolve()

        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    @property
    def path(
        self,
    ) -> Path:

        return self._path

    def _read_index(
        self,
        handle: Any,
    ) -> dict[str, str]:

        handle.seek(
            0,
            os.SEEK_SET,
        )

        index: dict[
            str,
            str,
        ] = {}

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
            except Exception as exc:
                raise R03OutcomeLedgerError(
                    (
                        "OUTCOME_LEDGER_JSON_CORRUPTION:"
                        f"{line_number}"
                    )
                ) from exc

            if not isinstance(
                value,
                dict,
            ):
                raise R03OutcomeLedgerError(
                    (
                        "OUTCOME_LEDGER_RECORD_NOT_OBJECT:"
                        f"{line_number}"
                    )
                )

            record = validate_outcome_document(
                value
            )

            logical_id = (
                record.logical_observation_id
            )

            fingerprint = (
                record.semantic_outcome_fingerprint
            )

            if (
                logical_id in index
                and
                index[
                    logical_id
                ]
                !=
                fingerprint
            ):
                raise R03OutcomeLedgerConflictError(
                    (
                        "EXISTING_OUTCOME_CONFLICT:"
                        f"{logical_id}"
                    )
                )

            index[
                logical_id
            ] = fingerprint

        return index

    def append(
        self,
        outcome: R03ProspectiveOutcomeRecord,
    ) -> OutcomeAppendResult:

        document = outcome.to_dict()

        validated = validate_outcome_document(
            document
        )

        logical_id = (
            validated.logical_observation_id
        )

        fingerprint = (
            validated.semantic_outcome_fingerprint
        )

        with self._path.open(
            "a+",
            encoding="utf-8",
        ) as handle:

            with file_lock(
                handle
            ):

                index = self._read_index(
                    handle
                )

                if logical_id in index:

                    if (
                        index[
                            logical_id
                        ]
                        !=
                        fingerprint
                    ):
                        raise R03OutcomeLedgerConflictError(
                            (
                                "OUTCOME_APPEND_CONFLICT:"
                                f"{logical_id}"
                            )
                        )

                    return OutcomeAppendResult(
                        appended=False,
                        is_duplicate=True,
                        logical_observation_id=(
                            logical_id
                        ),
                    )

                handle.seek(
                    0,
                    os.SEEK_END,
                )

                handle.write(
                    json.dumps(
                        document,
                        sort_keys=True,
                        separators=(
                            ",",
                            ":",
                        ),
                        ensure_ascii=False,
                        allow_nan=False,
                    )
                    +
                    "\n"
                )

                handle.flush()

                os.fsync(
                    handle.fileno()
                )

        return OutcomeAppendResult(
            appended=True,
            is_duplicate=False,
            logical_observation_id=(
                logical_id
            ),
        )

    def validate_integrity(
        self,
    ) -> bool:

        if not self._path.exists():
            return True

        with self._path.open(
            "r",
            encoding="utf-8",
        ) as handle:

            self._read_index(
                handle
            )

        return True

    def count(
        self,
    ) -> int:

        if not self._path.exists():
            return 0

        with self._path.open(
            "r",
            encoding="utf-8",
        ) as handle:

            return len(
                self._read_index(
                    handle
                )
            )