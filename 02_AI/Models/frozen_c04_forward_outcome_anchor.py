"""
===============================================================================
Module      : frozen_c04_forward_outcome_anchor.py
Project     : PulseViper XAU AI
Purpose     : Gate 15D-C-B2A — Prospective Forward Outcome Anchor Authority
===============================================================================

Prospectively freezes the exact outcome reference values from the SAME genuine
forward-acquisition snapshot used for inference.

Frozen semantics:
- raw M5 time = candle OPEN
- decision_time = completed candle close / availability time
- decision bar open = decision_time - 5 minutes
- decision entry = decision candle CLOSE
- decision volatility = decision candle ATR14
- source snapshot identity must match canonical market-data fingerprint
- snapshot M5 must terminate exactly at the decision candle
- no future M5 outcome row may exist in the anchor source snapshot

Anchor ledger:
- append-only JSONL
- one logical observation -> one immutable semantic anchor
- same anchor retry may be idempotently ignored
- conflicting anchor fails closed
- lock + flush + fsync
- runtime file stays under 01_Data/Shadow and is gitignored

NO:
- MT5 initialization
- future outcome access
- performance evaluation
- PnL
- live authorization
- execution authorization
===============================================================================
"""

from __future__ import annotations

import contextlib
import dataclasses
from enum import Enum
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import sys
from typing import Any, Generator, Mapping, cast

import numpy as np
import pandas as pd


_contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_contract"
)

_eligibility: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_eligibility"
)

_feature_generator_mod: Any = importlib.import_module(
    "02_AI.Features.feature_generator"
)

_acquisition_mod: Any = importlib.import_module(
    "02_AI.Adapters.mt5_read_only_forward_acquisition_adapter"
)

FeatureGenerator: Any = (
    _feature_generator_mod.FeatureGenerator
)


# =============================================================================
# Frozen Authorities
# =============================================================================

ANCHOR_VERSION: str = (
    "FROZEN_C04_FORWARD_OUTCOME_ANCHOR_V1"
)

ANCHOR_LEDGER_VERSION: str = (
    "FROZEN_C04_FORWARD_OUTCOME_ANCHOR_LEDGER_V1"
)

EXPECTED_ACQUISITION_AUTHORITY: str = (
    "MT5ReadOnlyForwardAcquisitionAdapter:2.1.0"
)

EXPECTED_CONTRACT_FINGERPRINT_SHA256: str = (
    "01fe52a2f068fcc8fb2fc5b89dd7e19dc974fc2d967cfb791e75c3415804ce87"
)

EXPECTED_FEATURE_COLUMNS_SHA256: str = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

EXPECTED_MODEL_SHA256: str = (
    "48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769"
)

EXPECTED_CANONICAL_INSTRUMENT: str = (
    "XAUUSD"
)

EXPECTED_SOURCE_PROVENANCE: str = (
    "TRUE_FORWARD_OBSERVATION"
)

EXPECTED_BASE_TIMEFRAME: str = (
    "M5"
)

EXPECTED_BASE_TIMEFRAME_MINUTES: int = (
    5
)

DECISION_BAR_SEMANTICS: str = (
    "M5_BAR_OPEN_EQUALS_DECISION_TIME_MINUS_5_MINUTES"
)

ENTRY_REFERENCE: str = (
    "DECISION_M5_COMPLETED_BAR_CLOSE"
)

ATR_REFERENCE: str = (
    "DECISION_M5_COMPLETED_BAR_ATR14"
)

PROSPECTIVE_CAPTURE_POLICY: str = (
    "SAME_ACQUISITION_SNAPSHOT_NO_FUTURE_M5_ROWS"
)

FORMAL_MATURATION_REQUIRES_ANCHOR: bool = True

PERFORMANCE_EVALUATION_AUTHORIZED: bool = False
PNL_EVALUATION_AUTHORIZED: bool = False
LIVE_AUTHORIZED: bool = False
EXECUTION_AUTHORIZED: bool = False


_SHA256_RE: re.Pattern[str] = re.compile(
    r"^[a-f0-9]{64}$"
)


# =============================================================================
# Errors
# =============================================================================

class FrozenC04ForwardOutcomeAnchorError(
    RuntimeError
):
    pass


class InvalidAnchorError(
    FrozenC04ForwardOutcomeAnchorError
):
    pass


class CorruptedAnchorLedgerError(
    FrozenC04ForwardOutcomeAnchorError
):
    pass


class DuplicateAnchorError(
    FrozenC04ForwardOutcomeAnchorError
):
    pass


class ConflictingAnchorError(
    FrozenC04ForwardOutcomeAnchorError
):
    pass


# =============================================================================
# Duplicate Policy
# =============================================================================

class AnchorDuplicateHandling(
    str,
    Enum,
):
    FAIL_CLOSED = (
        "FAIL_CLOSED"
    )

    IDEMPOTENT_IGNORE = (
        "IDEMPOTENT_IGNORE"
    )


# =============================================================================
# Frozen Anchor Record
# =============================================================================

@dataclasses.dataclass(
    frozen=True
)
class FrozenC04ForwardOutcomeAnchor:

    logical_observation_id: str

    semantic_observation_fingerprint: str

    source_snapshot_id: str

    canonical_instrument: str

    decision_time_utc: str

    decision_bar_open_time_utc: str

    decision_m5_close: float

    decision_m5_atr14: float

    feature_columns_sha256: str

    model_sha256: str

    acquisition_authority: str

    source_provenance: str

    contract_fingerprint_sha256: str = (
        EXPECTED_CONTRACT_FINGERPRINT_SHA256
    )

    anchor_version: str = (
        ANCHOR_VERSION
    )

    decision_bar_semantics: str = (
        DECISION_BAR_SEMANTICS
    )

    entry_reference: str = (
        ENTRY_REFERENCE
    )

    atr_reference: str = (
        ATR_REFERENCE
    )

    prospective_capture_policy: str = (
        PROSPECTIVE_CAPTURE_POLICY
    )

    performance_evaluation_authorized: bool = False

    live_authorized: bool = False

    execution_authorized: bool = False

    def semantic_document(
        self,
    ) -> dict[str, Any]:

        return {
            "logical_observation_id": (
                self.logical_observation_id
            ),

            "semantic_observation_fingerprint": (
                self.semantic_observation_fingerprint
            ),

            "source_snapshot_id": (
                self.source_snapshot_id
            ),

            "canonical_instrument": (
                self.canonical_instrument
            ),

            "decision_time_utc": (
                self.decision_time_utc
            ),

            "decision_bar_open_time_utc": (
                self.decision_bar_open_time_utc
            ),

            "decision_m5_close": (
                self.decision_m5_close
            ),

            "decision_m5_atr14": (
                self.decision_m5_atr14
            ),

            "feature_columns_sha256": (
                self.feature_columns_sha256
            ),

            "model_sha256": (
                self.model_sha256
            ),

            "acquisition_authority": (
                self.acquisition_authority
            ),

            "source_provenance": (
                self.source_provenance
            ),

            "contract_fingerprint_sha256": (
                self.contract_fingerprint_sha256
            ),

            "anchor_version": (
                self.anchor_version
            ),

            "decision_bar_semantics": (
                self.decision_bar_semantics
            ),

            "entry_reference": (
                self.entry_reference
            ),

            "atr_reference": (
                self.atr_reference
            ),

            "prospective_capture_policy": (
                self.prospective_capture_policy
            ),

            "performance_evaluation_authorized": False,

            "live_authorized": False,

            "execution_authorized": False,
        }

    def semantic_fingerprint(
        self,
    ) -> str:

        payload = json.dumps(
            self.semantic_document(),
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
            allow_nan=False,
        ).encode(
            "utf-8"
        )

        return hashlib.sha256(
            payload
        ).hexdigest()

    def to_dict(
        self,
    ) -> dict[str, Any]:

        document = (
            self.semantic_document()
        )

        document[
            "anchor_semantic_fingerprint"
        ] = (
            self.semantic_fingerprint()
        )

        document[
            "anchor_ledger_version"
        ] = (
            ANCHOR_LEDGER_VERSION
        )

        return document


@dataclasses.dataclass(
    frozen=True
)
class AnchorAppendResult:

    record: FrozenC04ForwardOutcomeAnchor

    is_duplicate: bool

    appended: bool

    message: str


# =============================================================================
# Primitive Validation Helpers
# =============================================================================

def _require_sha256(
    value: Any,
    field_name: str,
) -> str:

    if not isinstance(
        value,
        str,
    ):

        raise InvalidAnchorError(
            f"{field_name}_NOT_STRING"
        )

    normalized = (
        value.strip()
        .lower()
    )

    if not _SHA256_RE.fullmatch(
        normalized
    ):

        raise InvalidAnchorError(
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

        raise InvalidAnchorError(
            f"{field_name}_NOT_STRING"
        )

    normalized = (
        value.strip()
    )

    if not normalized:

        raise InvalidAnchorError(
            f"{field_name}_EMPTY"
        )

    return normalized


def _utc_timestamp(
    value: Any,
    field_name: str,
) -> pd.Timestamp:

    raw = _require_string(
        value,
        field_name,
    )

    try:

        parsed = pd.Timestamp(
            raw
        )

    except Exception as exc:

        raise InvalidAnchorError(
            f"{field_name}_INVALID_TIMESTAMP"
        ) from exc

    if parsed is pd.NaT:

        raise InvalidAnchorError(
            f"{field_name}_INVALID_TIMESTAMP"
        )

    timestamp = cast(
        pd.Timestamp,
        parsed,
    )

    if timestamp.tzinfo is None:

        raise InvalidAnchorError(
            f"{field_name}_MUST_BE_TIMEZONE_AWARE"
        )

    converted = (
        timestamp.tz_convert(
            "UTC"
        )
    )

    if converted is pd.NaT:

        raise InvalidAnchorError(
            f"{field_name}_UTC_CONVERSION_FAILED"
        )

    return cast(
        pd.Timestamp,
        converted,
    )


def _utc_iso(
    value: Any,
) -> str:

    try:

        parsed = pd.Timestamp(
            value
        )

    except Exception as exc:

        raise InvalidAnchorError(
            "TIMESTAMP_INVALID"
        ) from exc

    if parsed is pd.NaT:

        raise InvalidAnchorError(
            "TIMESTAMP_INVALID"
        )

    timestamp = cast(
        pd.Timestamp,
        parsed,
    )

    if timestamp.tzinfo is None:

        raise InvalidAnchorError(
            "TIMESTAMP_MUST_BE_TIMEZONE_AWARE"
        )

    converted = (
        timestamp.tz_convert(
            "UTC"
        )
    )

    if converted is pd.NaT:

        raise InvalidAnchorError(
            "TIMESTAMP_UTC_CONVERSION_FAILED"
        )

    utc = cast(
        pd.Timestamp,
        converted,
    )

    output = utc.isoformat()

    if output.endswith(
        "+00:00"
    ):

        output = (
            output[
                :-6
            ]
            +
            "Z"
        )

    return output


def _require_positive_finite(
    value: Any,
    field_name: str,
) -> float:

    try:

        number = float(
            value
        )

    except Exception as exc:

        raise InvalidAnchorError(
            f"{field_name}_NOT_NUMERIC"
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

        raise InvalidAnchorError(
            f"{field_name}_NOT_POSITIVE_FINITE"
        )

    return number


# =============================================================================
# Frozen Authority Validation
# =============================================================================

def verify_authorities() -> bool:

    if (
        _contract.compute_contract_fingerprint()
        !=
        EXPECTED_CONTRACT_FINGERPRINT_SHA256
    ):

        raise InvalidAnchorError(
            "OUTCOME_CONTRACT_FINGERPRINT_MISMATCH"
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

        raise InvalidAnchorError(
            "ANCHOR_AUTHORIZATION_BOUNDARY_VIOLATION"
        )

    return True


# =============================================================================
# Snapshot Validation
# =============================================================================

def _validate_m5_snapshot(
    frame: pd.DataFrame,
) -> pd.DataFrame:

    if (
        frame is None
        or
        frame.empty
    ):

        raise InvalidAnchorError(
            "M5_SNAPSHOT_EMPTY"
        )

    required = {
        "time",
        "open",
        "high",
        "low",
        "close",
    }

    missing = (
        required
        -
        set(
            frame.columns
        )
    )

    if missing:

        raise InvalidAnchorError(
            (
                "M5_REQUIRED_COLUMNS_MISSING:"
                f"{sorted(missing)}"
            )
        )

    output = frame.copy()

    try:

        output[
            "time"
        ] = pd.to_datetime(
            output[
                "time"
            ],
            utc=True,
            errors="raise",
        )

    except Exception as exc:

        raise InvalidAnchorError(
            "M5_TIMESTAMP_NORMALIZATION_FAILED"
        ) from exc

    output = (
        output.sort_values(
            "time"
        )
        .reset_index(
            drop=True
        )
    )

    if bool(
        output[
            "time"
        ].duplicated().any()
    ):

        raise InvalidAnchorError(
            "M5_DUPLICATE_TIMESTAMPS"
        )

    if not bool(
        output[
            "time"
        ].is_monotonic_increasing
    ):

        raise InvalidAnchorError(
            "M5_TIMESTAMPS_NOT_MONOTONIC"
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

    numeric = (
        output[
            [
                "open",
                "high",
                "low",
                "close",
            ]
        ]
        .to_numpy(
            dtype=float
        )
    )

    if not bool(
        np.isfinite(
            numeric
        ).all()
    ):

        raise InvalidAnchorError(
            "M5_NON_FINITE_OHLC"
        )

    if bool(
        (
            output[
                "low"
            ]
            <=
            0.0
        ).any()
    ):

        raise InvalidAnchorError(
            "M5_NON_POSITIVE_LOW"
        )

    if bool(
        (
            output[
                "high"
            ]
            <
            output[
                "low"
            ]
        ).any()
    ):

        raise InvalidAnchorError(
            "M5_HIGH_BELOW_LOW"
        )

    if bool(
        (
            output[
                "high"
            ]
            <
            output[
                "open"
            ]
        ).any()
        or
        (
            output[
                "high"
            ]
            <
            output[
                "close"
            ]
        ).any()
    ):

        raise InvalidAnchorError(
            "M5_HIGH_GEOMETRY_INVALID"
        )

    if bool(
        (
            output[
                "low"
            ]
            >
            output[
                "open"
            ]
        ).any()
        or
        (
            output[
                "low"
            ]
            >
            output[
                "close"
            ]
        ).any()
    ):

        raise InvalidAnchorError(
            "M5_LOW_GEOMETRY_INVALID"
        )

    return output


# =============================================================================
# Prospective Anchor Capture
# =============================================================================

def capture_anchor(
    *,
    observation: Mapping[str, Any],
    market_data: Mapping[
        str,
        pd.DataFrame,
    ],
) -> FrozenC04ForwardOutcomeAnchor:

    verify_authorities()

    # -------------------------------------------------------------------------
    # Validate immutable observation identity first.
    #
    # These checks intentionally occur BEFORE eligibility assessment so that
    # frozen model / feature / acquisition authority violations are reported
    # by this anchor authority itself and fail closed deterministically.
    # -------------------------------------------------------------------------

    logical_observation_id = (
        _require_sha256(
            observation.get(
                "logical_observation_id"
            ),
            "LOGICAL_OBSERVATION_ID",
        )
    )

    observation_fingerprint = (
        _require_sha256(
            observation.get(
                "semantic_record_fingerprint"
            ),
            "SEMANTIC_OBSERVATION_FINGERPRINT",
        )
    )

    source_snapshot_id = (
        _require_sha256(
            observation.get(
                "source_snapshot_id"
            ),
            "SOURCE_SNAPSHOT_ID",
        )
    )

    feature_columns_sha256 = (
        _require_sha256(
            observation.get(
                "feature_columns_sha256"
            ),
            "FEATURE_COLUMNS_SHA256",
        )
    )

    model_sha256 = (
        _require_sha256(
            observation.get(
                "model_sha256"
            ),
            "MODEL_SHA256",
        )
    )

    canonical_instrument = (
        _require_string(
            observation.get(
                "canonical_instrument"
            ),
            "CANONICAL_INSTRUMENT",
        )
    )

    source_provenance = (
        _require_string(
            observation.get(
                "source_provenance"
            ),
            "SOURCE_PROVENANCE",
        )
    )

    acquisition_authority = (
        _require_string(
            observation.get(
                "acquisition_authority"
            ),
            "ACQUISITION_AUTHORITY",
        )
    )

    # -------------------------------------------------------------------------
    # Frozen Authority Checks
    # -------------------------------------------------------------------------

    if (
        feature_columns_sha256
        !=
        EXPECTED_FEATURE_COLUMNS_SHA256
    ):

        raise InvalidAnchorError(
            "FEATURE_COLUMNS_AUTHORITY_MISMATCH"
        )

    if (
        model_sha256
        !=
        EXPECTED_MODEL_SHA256
    ):

        raise InvalidAnchorError(
            "MODEL_AUTHORITY_MISMATCH"
        )

    if (
        canonical_instrument
        !=
        EXPECTED_CANONICAL_INSTRUMENT
    ):

        raise InvalidAnchorError(
            "CANONICAL_INSTRUMENT_MISMATCH"
        )

    if (
        source_provenance
        !=
        EXPECTED_SOURCE_PROVENANCE
    ):

        raise InvalidAnchorError(
            "SOURCE_PROVENANCE_MISMATCH"
        )

    if (
        acquisition_authority
        !=
        EXPECTED_ACQUISITION_AUTHORITY
    ):

        raise InvalidAnchorError(
            "ACQUISITION_AUTHORITY_MISMATCH"
        )

    if (
        observation.get(
            "live_authorized"
        )
        is not False
    ):

        raise InvalidAnchorError(
            "LIVE_AUTHORIZATION_VIOLATION"
        )

    if (
        observation.get(
            "execution_authorized"
        )
        is not False
    ):

        raise InvalidAnchorError(
            "EXECUTION_AUTHORIZATION_VIOLATION"
        )

    # -------------------------------------------------------------------------
    # Prospective Eligibility
    # -------------------------------------------------------------------------

    try:

        eligibility = (
            _eligibility.assess_observation(
                observation
            )
        )

    except Exception as exc:

        raise InvalidAnchorError(
            (
                "OBSERVATION_ELIGIBILITY_VALIDATION_FAILED:"
                f"{exc}"
            )
        ) from exc

    if (
        eligibility
        .eligible_for_formal_maturation
        is not True
    ):

        raise InvalidAnchorError(
            (
                "OBSERVATION_NOT_PROSPECTIVELY_ELIGIBLE:"
                f"{eligibility.eligibility_reason}"
            )
        )

    # -------------------------------------------------------------------------
    # Canonical Snapshot Identity
    # -------------------------------------------------------------------------

    canonical_snapshot_id = (
        _acquisition_mod
        .compute_canonical_snapshot_id(
            market_data
        )
    )

    if (
        canonical_snapshot_id
        !=
        source_snapshot_id
    ):

        raise InvalidAnchorError(
            (
                "SOURCE_SNAPSHOT_ID_MISMATCH:"
                f"{source_snapshot_id}!="
                f"{canonical_snapshot_id}"
            )
        )

    # -------------------------------------------------------------------------
    # M5 Snapshot Boundary
    # -------------------------------------------------------------------------

    if (
        EXPECTED_BASE_TIMEFRAME
        not in market_data
    ):

        raise InvalidAnchorError(
            "M5_SNAPSHOT_MISSING"
        )

    m5 = (
        _validate_m5_snapshot(
            market_data[
                EXPECTED_BASE_TIMEFRAME
            ]
        )
    )

    decision_time = (
        _utc_timestamp(
            observation.get(
                "decision_time_utc"
            ),
            "DECISION_TIME_UTC",
        )
    )

    decision_bar_open = (
        decision_time
        -
        pd.Timedelta(
            minutes=(
                EXPECTED_BASE_TIMEFRAME_MINUTES
            )
        )
    )

    latest_m5_time_raw = (
        m5[
            "time"
        ].iloc[
            -1
        ]
    )

    if latest_m5_time_raw is pd.NaT:

        raise InvalidAnchorError(
            "LATEST_M5_TIME_INVALID"
        )

    latest_m5_time = cast(
        pd.Timestamp,
        latest_m5_time_raw,
    )

    # The same acquisition snapshot must terminate exactly at the decision bar.
    # Therefore no future M5 outcome candle can already be present.

    if (
        latest_m5_time
        !=
        decision_bar_open
    ):

        raise InvalidAnchorError(
            (
                "SNAPSHOT_NOT_TERMINATED_AT_DECISION_BAR:"
                f"latest="
                f"{_utc_iso(latest_m5_time)}:"
                f"expected="
                f"{_utc_iso(decision_bar_open)}"
            )
        )

    future_rows_present = bool(
        (
            m5[
                "time"
            ]
            >
            decision_bar_open
        ).any()
    )

    if future_rows_present:

        raise InvalidAnchorError(
            "FUTURE_M5_ROWS_PRESENT_IN_ANCHOR_SNAPSHOT"
        )

    # -------------------------------------------------------------------------
    # Frozen Decision Close + ATR14
    # -------------------------------------------------------------------------

    feature_generator = (
        FeatureGenerator()
    )

    try:

        featured = (
            feature_generator.generate(
                m5.copy()
            )
        )

    except Exception as exc:

        raise InvalidAnchorError(
            (
                "DECISION_ATR_FEATURE_GENERATION_FAILED:"
                f"{exc}"
            )
        ) from exc

    if (
        "atr14"
        not in featured.columns
    ):

        raise InvalidAnchorError(
            "ATR14_NOT_GENERATED"
        )

    if featured.empty:

        raise InvalidAnchorError(
            "ATR_FEATURE_FRAME_EMPTY"
        )

    decision_close = (
        _require_positive_finite(
            m5.iloc[
                -1
            ][
                "close"
            ],
            "DECISION_M5_CLOSE",
        )
    )

    decision_atr14 = (
        _require_positive_finite(
            featured.iloc[
                -1
            ][
                "atr14"
            ],
            "DECISION_M5_ATR14",
        )
    )

    return FrozenC04ForwardOutcomeAnchor(
        logical_observation_id=(
            logical_observation_id
        ),

        semantic_observation_fingerprint=(
            observation_fingerprint
        ),

        source_snapshot_id=(
            source_snapshot_id
        ),

        canonical_instrument=(
            canonical_instrument
        ),

        decision_time_utc=(
            _utc_iso(
                decision_time
            )
        ),

        decision_bar_open_time_utc=(
            _utc_iso(
                decision_bar_open
            )
        ),

        decision_m5_close=(
            decision_close
        ),

        decision_m5_atr14=(
            decision_atr14
        ),

        feature_columns_sha256=(
            feature_columns_sha256
        ),

        model_sha256=(
            model_sha256
        ),

        acquisition_authority=(
            acquisition_authority
        ),

        source_provenance=(
            source_provenance
        ),
    )


# =============================================================================
# Persisted Anchor Validation
# =============================================================================

def validate_anchor_document(
    document: Mapping[str, Any],
) -> FrozenC04ForwardOutcomeAnchor:

    verify_authorities()

    if (
        document.get(
            "anchor_version"
        )
        !=
        ANCHOR_VERSION
    ):

        raise InvalidAnchorError(
            "ANCHOR_VERSION_MISMATCH"
        )

    if (
        document.get(
            "anchor_ledger_version"
        )
        !=
        ANCHOR_LEDGER_VERSION
    ):

        raise InvalidAnchorError(
            "ANCHOR_LEDGER_VERSION_MISMATCH"
        )

    logical_observation_id = (
        _require_sha256(
            document.get(
                "logical_observation_id"
            ),
            "LOGICAL_OBSERVATION_ID",
        )
    )

    semantic_observation_fingerprint = (
        _require_sha256(
            document.get(
                "semantic_observation_fingerprint"
            ),
            "SEMANTIC_OBSERVATION_FINGERPRINT",
        )
    )

    source_snapshot_id = (
        _require_sha256(
            document.get(
                "source_snapshot_id"
            ),
            "SOURCE_SNAPSHOT_ID",
        )
    )

    canonical_instrument = (
        _require_string(
            document.get(
                "canonical_instrument"
            ),
            "CANONICAL_INSTRUMENT",
        )
    )

    decision_time_utc = (
        _utc_iso(
            document.get(
                "decision_time_utc"
            )
        )
    )

    decision_bar_open_time_utc = (
        _utc_iso(
            document.get(
                "decision_bar_open_time_utc"
            )
        )
    )

    decision_m5_close = (
        _require_positive_finite(
            document.get(
                "decision_m5_close"
            ),
            "DECISION_M5_CLOSE",
        )
    )

    decision_m5_atr14 = (
        _require_positive_finite(
            document.get(
                "decision_m5_atr14"
            ),
            "DECISION_M5_ATR14",
        )
    )

    feature_columns_sha256 = (
        _require_sha256(
            document.get(
                "feature_columns_sha256"
            ),
            "FEATURE_COLUMNS_SHA256",
        )
    )

    model_sha256 = (
        _require_sha256(
            document.get(
                "model_sha256"
            ),
            "MODEL_SHA256",
        )
    )

    acquisition_authority = (
        _require_string(
            document.get(
                "acquisition_authority"
            ),
            "ACQUISITION_AUTHORITY",
        )
    )

    source_provenance = (
        _require_string(
            document.get(
                "source_provenance"
            ),
            "SOURCE_PROVENANCE",
        )
    )

    if (
        canonical_instrument
        !=
        EXPECTED_CANONICAL_INSTRUMENT
    ):

        raise InvalidAnchorError(
            "ANCHOR_CANONICAL_INSTRUMENT_MISMATCH"
        )

    if (
        feature_columns_sha256
        !=
        EXPECTED_FEATURE_COLUMNS_SHA256
    ):

        raise InvalidAnchorError(
            "ANCHOR_FEATURE_COLUMNS_MISMATCH"
        )

    if (
        model_sha256
        !=
        EXPECTED_MODEL_SHA256
    ):

        raise InvalidAnchorError(
            "ANCHOR_MODEL_MISMATCH"
        )

    if (
        acquisition_authority
        !=
        EXPECTED_ACQUISITION_AUTHORITY
    ):

        raise InvalidAnchorError(
            "ANCHOR_ACQUISITION_AUTHORITY_MISMATCH"
        )

    if (
        source_provenance
        !=
        EXPECTED_SOURCE_PROVENANCE
    ):

        raise InvalidAnchorError(
            "ANCHOR_SOURCE_PROVENANCE_MISMATCH"
        )

    decision_time = (
        _utc_timestamp(
            decision_time_utc,
            "DECISION_TIME_UTC",
        )
    )

    decision_open = (
        _utc_timestamp(
            decision_bar_open_time_utc,
            "DECISION_BAR_OPEN_TIME_UTC",
        )
    )

    expected_decision_time = (
        decision_open
        +
        pd.Timedelta(
            minutes=(
                EXPECTED_BASE_TIMEFRAME_MINUTES
            )
        )
    )

    if (
        expected_decision_time
        !=
        decision_time
    ):

        raise InvalidAnchorError(
            "ANCHOR_DECISION_BAR_TIME_MAPPING_MISMATCH"
        )

    if (
        document.get(
            "decision_bar_semantics"
        )
        !=
        DECISION_BAR_SEMANTICS
    ):

        raise InvalidAnchorError(
            "DECISION_BAR_SEMANTICS_MISMATCH"
        )

    if (
        document.get(
            "entry_reference"
        )
        !=
        ENTRY_REFERENCE
    ):

        raise InvalidAnchorError(
            "ENTRY_REFERENCE_MISMATCH"
        )

    if (
        document.get(
            "atr_reference"
        )
        !=
        ATR_REFERENCE
    ):

        raise InvalidAnchorError(
            "ATR_REFERENCE_MISMATCH"
        )

    if (
        document.get(
            "prospective_capture_policy"
        )
        !=
        PROSPECTIVE_CAPTURE_POLICY
    ):

        raise InvalidAnchorError(
            "PROSPECTIVE_CAPTURE_POLICY_MISMATCH"
        )

    contract_fingerprint = (
        _require_sha256(
            document.get(
                "contract_fingerprint_sha256"
            ),
            "CONTRACT_FINGERPRINT_SHA256",
        )
    )

    if (
        contract_fingerprint
        !=
        EXPECTED_CONTRACT_FINGERPRINT_SHA256
    ):

        raise InvalidAnchorError(
            "ANCHOR_CONTRACT_FINGERPRINT_MISMATCH"
        )

    if (
        document.get(
            "performance_evaluation_authorized"
        )
        is not False
    ):

        raise InvalidAnchorError(
            "PERFORMANCE_AUTHORIZATION_VIOLATION"
        )

    if (
        document.get(
            "live_authorized"
        )
        is not False
    ):

        raise InvalidAnchorError(
            "LIVE_AUTHORIZATION_VIOLATION"
        )

    if (
        document.get(
            "execution_authorized"
        )
        is not False
    ):

        raise InvalidAnchorError(
            "EXECUTION_AUTHORIZATION_VIOLATION"
        )

    anchor = FrozenC04ForwardOutcomeAnchor(
        logical_observation_id=(
            logical_observation_id
        ),

        semantic_observation_fingerprint=(
            semantic_observation_fingerprint
        ),

        source_snapshot_id=(
            source_snapshot_id
        ),

        canonical_instrument=(
            canonical_instrument
        ),

        decision_time_utc=(
            decision_time_utc
        ),

        decision_bar_open_time_utc=(
            decision_bar_open_time_utc
        ),

        decision_m5_close=(
            decision_m5_close
        ),

        decision_m5_atr14=(
            decision_m5_atr14
        ),

        feature_columns_sha256=(
            feature_columns_sha256
        ),

        model_sha256=(
            model_sha256
        ),

        acquisition_authority=(
            acquisition_authority
        ),

        source_provenance=(
            source_provenance
        ),
    )

    supplied_fingerprint = (
        _require_sha256(
            document.get(
                "anchor_semantic_fingerprint"
            ),
            "ANCHOR_SEMANTIC_FINGERPRINT",
        )
    )

    expected_fingerprint = (
        anchor.semantic_fingerprint()
    )

    if (
        supplied_fingerprint
        !=
        expected_fingerprint
    ):

        raise InvalidAnchorError(
            (
                "ANCHOR_SEMANTIC_FINGERPRINT_MISMATCH:"
                f"{supplied_fingerprint}!="
                f"{expected_fingerprint}"
            )
        )

    return anchor


# =============================================================================
# Cross-Platform File Lock
# =============================================================================

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


# =============================================================================
# Append-Only Anchor Ledger
# =============================================================================

class FrozenC04ForwardOutcomeAnchorLedger:

    def __init__(
        self,
        ledger_path: Path | str,
        duplicate_handling: (
            AnchorDuplicateHandling
        ) = (
            AnchorDuplicateHandling.FAIL_CLOSED
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

                line = (
                    raw_line.strip()
                )

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

                        raise InvalidAnchorError(
                            "ANCHOR_RECORD_NOT_OBJECT"
                        )

                    anchor = (
                        validate_anchor_document(
                            value
                        )
                    )

                except Exception as exc:

                    raise CorruptedAnchorLedgerError(
                        (
                            "ANCHOR_LEDGER_CORRUPTED:"
                            f"line={line_number}:"
                            f"{exc}"
                        )
                    ) from exc

                logical_id = (
                    anchor.logical_observation_id
                )

                fingerprint = (
                    anchor.semantic_fingerprint()
                )

                if logical_id in self._index:

                    existing = (
                        self._index[
                            logical_id
                        ]
                    )

                    if (
                        existing
                        !=
                        fingerprint
                    ):

                        raise ConflictingAnchorError(
                            (
                                "CONFLICTING_ANCHORS_IN_LEDGER:"
                                f"{logical_id}"
                            )
                        )

                self._index[
                    logical_id
                ] = (
                    fingerprint
                )

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
        anchor: FrozenC04ForwardOutcomeAnchor,
    ) -> AnchorAppendResult:

        validated = (
            validate_anchor_document(
                anchor.to_dict()
            )
        )

        logical_id = (
            validated.logical_observation_id
        )

        fingerprint = (
            validated.semantic_fingerprint()
        )

        if logical_id in self._index:

            existing = (
                self._index[
                    logical_id
                ]
            )

            if (
                existing
                !=
                fingerprint
            ):

                raise ConflictingAnchorError(
                    (
                        "CONFLICTING_ANCHOR:"
                        f"{logical_id}:"
                        f"{existing}!="
                        f"{fingerprint}"
                    )
                )

            if (
                self._duplicate_handling
                ==
                AnchorDuplicateHandling.FAIL_CLOSED
            ):

                raise DuplicateAnchorError(
                    (
                        "DUPLICATE_ANCHOR_REJECTED:"
                        f"{logical_id}"
                    )
                )

            return AnchorAppendResult(
                record=(
                    validated
                ),

                is_duplicate=True,

                appended=False,

                message=(
                    "IDEMPOTENT_ANCHOR_DUPLICATE_IGNORED:"
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

            raise CorruptedAnchorLedgerError(
                (
                    "FAILED_TO_APPEND_ANCHOR:"
                    f"{self._path}:"
                    f"{exc}"
                )
            ) from exc

        self._index[
            logical_id
        ] = (
            fingerprint
        )

        return AnchorAppendResult(
            record=(
                validated
            ),

            is_duplicate=False,

            appended=True,

            message=(
                "ANCHOR_RECORDED:"
                f"{logical_id}"
            ),
        )

    def read_all(
        self,
    ) -> list[
        FrozenC04ForwardOutcomeAnchor
    ]:

        records: list[
            FrozenC04ForwardOutcomeAnchor
        ] = []

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

                line = (
                    raw_line.strip()
                )

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

                        raise InvalidAnchorError(
                            "ANCHOR_RECORD_NOT_OBJECT"
                        )

                    records.append(
                        validate_anchor_document(
                            value
                        )
                    )

                except Exception as exc:

                    raise CorruptedAnchorLedgerError(
                        (
                            "ANCHOR_LEDGER_CORRUPTED:"
                            f"line={line_number}:"
                            f"{exc}"
                        )
                    ) from exc

        return records