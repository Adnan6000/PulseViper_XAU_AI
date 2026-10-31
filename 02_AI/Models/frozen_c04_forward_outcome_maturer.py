"""
===============================================================================
Module      : frozen_c04_forward_outcome_maturer.py
Project     : PulseViper XAU AI
Purpose     : Gate 15D-C-B2B — Anchor-Required Forward Outcome Maturer V2
===============================================================================

Pure / offline forward-outcome maturation authority.

V2 removes post-hoc reconstruction of decision reference values.

Frozen semantics:
- Raw M5 `time` is candle OPEN time.
- decision_time = completed M5 candle availability / close time.
- decision_bar_open_time = decision_time - 5 minutes.
- Entry close MUST come from a validated prospective outcome anchor.
- Decision ATR14 MUST come from the same validated prospective anchor.
- Historical / later M5 data MUST NOT reconstruct entry close or ATR14.
- Completed M5 data is used only to identify the decision row and collect the
  NEXT 12 COMPLETED M5 rows after the decision row.
- Weekend/session gaps are allowed because the horizon is row-based.

Required chain:

    genuine acquisition snapshot
        ->
    frozen observation
        ->
    prospective immutable anchor
        ->
    future 12 completed M5 rows
        ->
    matured outcome

It does NOT:
- initialize MT5
- acquire market data
- reconstruct the anchor retrospectively
- access validation/test holdouts
- calculate aggregate model performance
- calculate accuracy / win rate / PnL / return / drawdown
- mutate observation / anchor / outcome ledgers
- authorize live trading
- authorize execution
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib
import json
import math
import re
from typing import Any, Mapping, cast

import numpy as np
import pandas as pd


# =============================================================================
# Imported Frozen Authorities
# =============================================================================

_contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_contract"
)

_eligibility: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_eligibility"
)

_anchor_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_anchor"
)


# =============================================================================
# Frozen V2 Authority
# =============================================================================

MATURATION_VERSION: str = (
    "FROZEN_C04_FORWARD_OUTCOME_MATURER_V2"
)

SUPERSEDES_MATURATION_VERSION: str = (
    "FROZEN_C04_FORWARD_OUTCOME_MATURER_V1_1"
)

EXPECTED_ANCHOR_VERSION: str = (
    "FROZEN_C04_FORWARD_OUTCOME_ANCHOR_V1"
)

EXPECTED_ANCHOR_LEDGER_VERSION: str = (
    "FROZEN_C04_FORWARD_OUTCOME_ANCHOR_LEDGER_V1"
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

EXPECTED_BASE_TIMEFRAME: str = (
    "M5"
)

EXPECTED_BASE_TIMEFRAME_MINUTES: int = (
    5
)

EXPECTED_HORIZON_BARS: int = (
    12
)

EXPECTED_PROFIT_ATR: float = (
    1.25
)

EXPECTED_MAX_ADVERSE_ATR: float = (
    0.75
)

DECISION_BAR_SEMANTICS: str = (
    "M5_BAR_OPEN_EQUALS_DECISION_TIME_MINUS_5_MINUTES"
)

ENTRY_REFERENCE: str = (
    "PROSPECTIVE_ANCHOR_DECISION_M5_CLOSE"
)

ATR_REFERENCE: str = (
    "PROSPECTIVE_ANCHOR_DECISION_M5_ATR14"
)

HORIZON_SEMANTICS: str = (
    "NEXT_12_COMPLETED_M5_ROWS_AFTER_DECISION_BAR"
)

ANCHOR_REQUIREMENT: str = (
    "VALIDATED_PROSPECTIVE_ANCHOR_REQUIRED"
)

REFERENCE_RECONSTRUCTION_POLICY: str = (
    "POST_HOC_ENTRY_AND_ATR_RECONSTRUCTION_FORBIDDEN"
)

OUTCOME_MATURATION_AUTHORIZED: bool = True

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

class ForwardOutcomeMaturationError(
    RuntimeError
):
    pass


class InvalidProspectiveAnchorError(
    ForwardOutcomeMaturationError
):
    pass


class InsufficientFutureBarsError(
    ForwardOutcomeMaturationError
):
    pass


# =============================================================================
# Matured Outcome
# =============================================================================

@dataclass(
    frozen=True
)
class FrozenC04ForwardOutcome:

    logical_observation_id: str

    decision_time_utc: str

    decision_bar_open_time_utc: str

    outcome_class: int

    outcome_label: str

    entry_close: float

    decision_atr14: float

    horizon_bars: int

    horizon_semantics: str

    decision_bar_semantics: str

    first_future_bar_time_utc: str

    last_future_bar_time_utc: str

    max_future_high: float

    min_future_low: float

    up_excursion_atr: float

    down_excursion_atr: float

    source_observation_fingerprint: str

    source_anchor_fingerprint: str

    source_anchor_version: str

    contract_fingerprint_sha256: str = (
        EXPECTED_CONTRACT_FINGERPRINT_SHA256
    )

    maturation_version: str = (
        MATURATION_VERSION
    )

    entry_reference: str = (
        ENTRY_REFERENCE
    )

    atr_reference: str = (
        ATR_REFERENCE
    )

    anchor_requirement: str = (
        ANCHOR_REQUIREMENT
    )

    reference_reconstruction_policy: str = (
        REFERENCE_RECONSTRUCTION_POLICY
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
                self.horizon_semantics
            ),

            "decision_bar_semantics": (
                self.decision_bar_semantics
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

            "source_anchor_version": (
                self.source_anchor_version
            ),

            "contract_fingerprint_sha256": (
                self.contract_fingerprint_sha256
            ),

            "maturation_version": (
                self.maturation_version
            ),

            "entry_reference": (
                self.entry_reference
            ),

            "atr_reference": (
                self.atr_reference
            ),

            "anchor_requirement": (
                self.anchor_requirement
            ),

            "reference_reconstruction_policy": (
                self.reference_reconstruction_policy
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
            "semantic_outcome_fingerprint"
        ] = (
            self.semantic_fingerprint()
        )

        return document


# =============================================================================
# Primitive Validation
# =============================================================================

def _require_string(
    value: Any,
    field_name: str,
) -> str:

    if not isinstance(
        value,
        str,
    ):

        raise ForwardOutcomeMaturationError(
            f"{field_name}_NOT_STRING"
        )

    normalized = (
        value.strip()
    )

    if not normalized:

        raise ForwardOutcomeMaturationError(
            f"{field_name}_EMPTY"
        )

    return normalized


def _require_sha256(
    value: Any,
    field_name: str,
) -> str:

    raw = _require_string(
        value,
        field_name,
    ).lower()

    if not _SHA256_RE.fullmatch(
        raw
    ):

        raise ForwardOutcomeMaturationError(
            f"{field_name}_INVALID_SHA256"
        )

    return raw


def _require_positive_finite(
    value: Any,
    field_name: str,
) -> float:

    try:

        number = float(
            value
        )

    except Exception as exc:

        raise ForwardOutcomeMaturationError(
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

        raise ForwardOutcomeMaturationError(
            f"{field_name}_NOT_POSITIVE_FINITE"
        )

    return number


def _utc_timestamp(
    value: Any,
) -> pd.Timestamp:

    try:

        raw = pd.Timestamp(
            value
        )

    except Exception as exc:

        raise ForwardOutcomeMaturationError(
            "INVALID_TIMESTAMP"
        ) from exc

    if raw is pd.NaT:

        raise ForwardOutcomeMaturationError(
            "INVALID_TIMESTAMP_NAT"
        )

    timestamp = cast(
        pd.Timestamp,
        raw,
    )

    if timestamp.tzinfo is None:

        raise ForwardOutcomeMaturationError(
            "TIMESTAMP_MUST_BE_TIMEZONE_AWARE"
        )

    converted = (
        timestamp.tz_convert(
            "UTC"
        )
    )

    if converted is pd.NaT:

        raise ForwardOutcomeMaturationError(
            "TIMESTAMP_UTC_CONVERSION_FAILED"
        )

    return cast(
        pd.Timestamp,
        converted,
    )


def _utc_iso(
    value: Any,
) -> str:

    timestamp = (
        _utc_timestamp(
            value
        )
    )

    output = (
        timestamp.isoformat()
    )

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


# =============================================================================
# Authority Validation
# =============================================================================

def verify_authorities() -> bool:

    if (
        _contract.compute_contract_fingerprint()
        !=
        EXPECTED_CONTRACT_FINGERPRINT_SHA256
    ):

        raise ForwardOutcomeMaturationError(
            "OUTCOME_CONTRACT_FINGERPRINT_MISMATCH"
        )

    if (
        _contract.BASE_TIMEFRAME
        !=
        EXPECTED_BASE_TIMEFRAME
    ):

        raise ForwardOutcomeMaturationError(
            "BASE_TIMEFRAME_AUTHORITY_MISMATCH"
        )

    if (
        _contract.HORIZON_BARS
        !=
        EXPECTED_HORIZON_BARS
    ):

        raise ForwardOutcomeMaturationError(
            "HORIZON_AUTHORITY_MISMATCH"
        )

    if not math.isclose(
        float(
            _contract.PROFIT_ATR
        ),
        EXPECTED_PROFIT_ATR,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):

        raise ForwardOutcomeMaturationError(
            "PROFIT_ATR_AUTHORITY_MISMATCH"
        )

    if not math.isclose(
        float(
            _contract.MAX_ADVERSE_ATR
        ),
        EXPECTED_MAX_ADVERSE_ATR,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):

        raise ForwardOutcomeMaturationError(
            "MAX_ADVERSE_ATR_AUTHORITY_MISMATCH"
        )

    if (
        _anchor_mod.ANCHOR_VERSION
        !=
        EXPECTED_ANCHOR_VERSION
    ):

        raise ForwardOutcomeMaturationError(
            "ANCHOR_VERSION_AUTHORITY_MISMATCH"
        )

    if (
        _anchor_mod.ANCHOR_LEDGER_VERSION
        !=
        EXPECTED_ANCHOR_LEDGER_VERSION
    ):

        raise ForwardOutcomeMaturationError(
            "ANCHOR_LEDGER_VERSION_AUTHORITY_MISMATCH"
        )

    if (
        _anchor_mod.DECISION_BAR_SEMANTICS
        !=
        DECISION_BAR_SEMANTICS
    ):

        raise ForwardOutcomeMaturationError(
            "ANCHOR_DECISION_BAR_SEMANTICS_MISMATCH"
        )

    if (
        _anchor_mod.FORMAL_MATURATION_REQUIRES_ANCHOR
        is not True
    ):

        raise ForwardOutcomeMaturationError(
            "ANCHOR_REQUIREMENT_AUTHORITY_MISMATCH"
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

        raise ForwardOutcomeMaturationError(
            "MATURATION_AUTHORIZATION_BOUNDARY_VIOLATION"
        )

    return True


# =============================================================================
# M5 Future Frame Validation
# =============================================================================

def _validate_m5_frame(
    frame: pd.DataFrame,
) -> pd.DataFrame:

    if (
        frame is None
        or
        frame.empty
    ):

        raise ForwardOutcomeMaturationError(
            "M5_FRAME_EMPTY"
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

        raise ForwardOutcomeMaturationError(
            (
                "M5_REQUIRED_COLUMNS_MISSING:"
                f"{sorted(missing)}"
            )
        )

    output = (
        frame.copy()
    )

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

        raise ForwardOutcomeMaturationError(
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

        raise ForwardOutcomeMaturationError(
            "M5_DUPLICATE_TIMESTAMPS"
        )

    if not bool(
        output[
            "time"
        ].is_monotonic_increasing
    ):

        raise ForwardOutcomeMaturationError(
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

        raise ForwardOutcomeMaturationError(
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

        raise ForwardOutcomeMaturationError(
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

        raise ForwardOutcomeMaturationError(
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

        raise ForwardOutcomeMaturationError(
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

        raise ForwardOutcomeMaturationError(
            "M5_LOW_GEOMETRY_INVALID"
        )

    return output


# =============================================================================
# Anchor Validation / Linkage
# =============================================================================

def _validated_anchor(
    anchor: Any,
) -> Any:

    if anchor is None:

        raise InvalidProspectiveAnchorError(
            "PROSPECTIVE_ANCHOR_REQUIRED"
        )

    if isinstance(
        anchor,
        Mapping,
    ):

        document = dict(
            anchor
        )

    elif hasattr(
        anchor,
        "to_dict",
    ):

        document = (
            anchor.to_dict()
        )

    else:

        raise InvalidProspectiveAnchorError(
            "UNSUPPORTED_PROSPECTIVE_ANCHOR_TYPE"
        )

    try:

        return (
            _anchor_mod.validate_anchor_document(
                document
            )
        )

    except Exception as exc:

        raise InvalidProspectiveAnchorError(
            (
                "INVALID_PROSPECTIVE_ANCHOR:"
                f"{exc}"
            )
        ) from exc


def _verify_observation_anchor_linkage(
    *,
    observation: Mapping[str, Any],
    anchor: Any,
) -> None:

    logical_observation_id = (
        _require_sha256(
            observation.get(
                "logical_observation_id"
            ),
            "LOGICAL_OBSERVATION_ID",
        )
    )

    semantic_observation_fingerprint = (
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

    decision_time_utc = (
        _utc_iso(
            observation.get(
                "decision_time_utc"
            )
        )
    )

    if (
        logical_observation_id
        !=
        anchor.logical_observation_id
    ):

        raise InvalidProspectiveAnchorError(
            "ANCHOR_LOGICAL_OBSERVATION_ID_MISMATCH"
        )

    if (
        semantic_observation_fingerprint
        !=
        anchor.semantic_observation_fingerprint
    ):

        raise InvalidProspectiveAnchorError(
            "ANCHOR_OBSERVATION_FINGERPRINT_MISMATCH"
        )

    if (
        source_snapshot_id
        !=
        anchor.source_snapshot_id
    ):

        raise InvalidProspectiveAnchorError(
            "ANCHOR_SOURCE_SNAPSHOT_ID_MISMATCH"
        )

    if (
        feature_columns_sha256
        !=
        anchor.feature_columns_sha256
    ):

        raise InvalidProspectiveAnchorError(
            "ANCHOR_FEATURE_COLUMNS_MISMATCH"
        )

    if (
        model_sha256
        !=
        anchor.model_sha256
    ):

        raise InvalidProspectiveAnchorError(
            "ANCHOR_MODEL_MISMATCH"
        )

    if (
        canonical_instrument
        !=
        anchor.canonical_instrument
    ):

        raise InvalidProspectiveAnchorError(
            "ANCHOR_CANONICAL_INSTRUMENT_MISMATCH"
        )

    if (
        decision_time_utc
        !=
        anchor.decision_time_utc
    ):

        raise InvalidProspectiveAnchorError(
            "ANCHOR_DECISION_TIME_MISMATCH"
        )

    if (
        feature_columns_sha256
        !=
        EXPECTED_FEATURE_COLUMNS_SHA256
    ):

        raise InvalidProspectiveAnchorError(
            "FEATURE_COLUMNS_AUTHORITY_MISMATCH"
        )

    if (
        model_sha256
        !=
        EXPECTED_MODEL_SHA256
    ):

        raise InvalidProspectiveAnchorError(
            "MODEL_AUTHORITY_MISMATCH"
        )

    if (
        canonical_instrument
        !=
        EXPECTED_CANONICAL_INSTRUMENT
    ):

        raise InvalidProspectiveAnchorError(
            "CANONICAL_INSTRUMENT_AUTHORITY_MISMATCH"
        )


# =============================================================================
# Outcome Label
# =============================================================================

def _label_outcome(
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

        raise ForwardOutcomeMaturationError(
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


# =============================================================================
# Anchor-Required Maturation
# =============================================================================

def mature_observation(
    *,
    observation: Mapping[str, Any],
    anchor: Any,
    completed_m5_bars: pd.DataFrame,
) -> FrozenC04ForwardOutcome:

    verify_authorities()

    # -------------------------------------------------------------------------
    # Observation must still satisfy the frozen prospective eligibility gate.
    # -------------------------------------------------------------------------

    try:

        eligibility = (
            _eligibility.assess_observation(
                observation
            )
        )

    except Exception as exc:

        raise ForwardOutcomeMaturationError(
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

        raise ForwardOutcomeMaturationError(
            (
                "OBSERVATION_NOT_PROSPECTIVELY_ELIGIBLE:"
                f"{eligibility.eligibility_reason}"
            )
        )

    # -------------------------------------------------------------------------
    # A cryptographically valid prospective anchor is mandatory.
    # -------------------------------------------------------------------------

    validated_anchor = (
        _validated_anchor(
            anchor
        )
    )

    _verify_observation_anchor_linkage(
        observation=observation,
        anchor=validated_anchor,
    )

    logical_observation_id = (
        validated_anchor.logical_observation_id
    )

    source_observation_fingerprint = (
        validated_anchor.semantic_observation_fingerprint
    )

    source_anchor_fingerprint = (
        validated_anchor.semantic_fingerprint()
    )

    decision_time = (
        _utc_timestamp(
            validated_anchor.decision_time_utc
        )
    )

    decision_bar_open_time = (
        _utc_timestamp(
            validated_anchor.decision_bar_open_time_utc
        )
    )

    expected_decision_bar_open = (
        decision_time
        -
        pd.Timedelta(
            minutes=(
                EXPECTED_BASE_TIMEFRAME_MINUTES
            )
        )
    )

    if (
        decision_bar_open_time
        !=
        expected_decision_bar_open
    ):

        raise InvalidProspectiveAnchorError(
            "ANCHOR_DECISION_BAR_TIME_MAPPING_MISMATCH"
        )

    # -------------------------------------------------------------------------
    # CRITICAL V2 RULE:
    #
    # Entry and ATR are read ONLY from the prospective immutable anchor.
    # They are never reconstructed from completed_m5_bars.
    # -------------------------------------------------------------------------

    entry_close = (
        _require_positive_finite(
            validated_anchor.decision_m5_close,
            "ANCHOR_DECISION_M5_CLOSE",
        )
    )

    decision_atr14 = (
        _require_positive_finite(
            validated_anchor.decision_m5_atr14,
            "ANCHOR_DECISION_M5_ATR14",
        )
    )

    # -------------------------------------------------------------------------
    # Future rows
    # -------------------------------------------------------------------------

    raw = (
        _validate_m5_frame(
            completed_m5_bars
        )
    )

    decision_mask = (
        raw[
            "time"
        ]
        ==
        decision_bar_open_time
    ).to_numpy(
        dtype=bool
    )

    decision_positions = (
        np.flatnonzero(
            decision_mask
        )
    )

    if len(
        decision_positions
    ) != 1:

        raise ForwardOutcomeMaturationError(
            (
                "DECISION_M5_BAR_NOT_UNIQUE:"
                f"{len(decision_positions)}:"
                f"expected_open="
                f"{_utc_iso(decision_bar_open_time)}"
            )
        )

    decision_index = int(
        decision_positions[
            0
        ]
    )

    future_start = (
        decision_index
        +
        1
    )

    future_end = (
        future_start
        +
        EXPECTED_HORIZON_BARS
    )

    if (
        future_end
        >
        len(
            raw
        )
    ):

        available = max(
            0,
            (
                len(
                    raw
                )
                -
                future_start
            ),
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
            future_start:
            future_end
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    if (
        len(
            future
        )
        !=
        EXPECTED_HORIZON_BARS
    ):

        raise InsufficientFutureBarsError(
            "EXACT_12_FUTURE_M5_ROWS_REQUIRED"
        )

    future_times = cast(
        pd.Series,
        future[
            "time"
        ],
    )

    if not bool(
        future_times
        .is_monotonic_increasing
    ):

        raise ForwardOutcomeMaturationError(
            "FUTURE_M5_ROWS_NOT_MONOTONIC"
        )

    if bool(
        future_times
        .duplicated()
        .any()
    ):

        raise ForwardOutcomeMaturationError(
            "FUTURE_M5_ROWS_CONTAIN_DUPLICATE_TIMESTAMPS"
        )

    first_future_time_raw = (
        future.iloc[
            0
        ][
            "time"
        ]
    )

    last_future_time_raw = (
        future.iloc[
            -1
        ][
            "time"
        ]
    )

    if (
        first_future_time_raw
        is pd.NaT
        or
        last_future_time_raw
        is pd.NaT
    ):

        raise ForwardOutcomeMaturationError(
            "FUTURE_M5_TIMESTAMP_INVALID"
        )

    first_future_time = cast(
        pd.Timestamp,
        first_future_time_raw,
    )

    last_future_time = cast(
        pd.Timestamp,
        last_future_time_raw,
    )

    if (
        first_future_time
        <=
        decision_bar_open_time
    ):

        raise ForwardOutcomeMaturationError(
            "FIRST_FUTURE_BAR_NOT_AFTER_DECISION_BAR"
        )

    if (
        last_future_time
        <=
        first_future_time
    ):

        raise ForwardOutcomeMaturationError(
            "LAST_FUTURE_BAR_NOT_AFTER_FIRST_FUTURE_BAR"
        )

    # -------------------------------------------------------------------------
    # Outcome calculations use ANCHOR values only.
    # -------------------------------------------------------------------------

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

    if (
        not math.isfinite(
            max_future_high
        )
        or
        not math.isfinite(
            min_future_low
        )
    ):

        raise ForwardOutcomeMaturationError(
            "NON_FINITE_FUTURE_EXTREMES"
        )

    up_excursion_atr = (
        (
            max_future_high
            -
            entry_close
        )
        /
        decision_atr14
    )

    down_excursion_atr = (
        (
            entry_close
            -
            min_future_low
        )
        /
        decision_atr14
    )

    if (
        not math.isfinite(
            up_excursion_atr
        )
        or
        not math.isfinite(
            down_excursion_atr
        )
    ):

        raise ForwardOutcomeMaturationError(
            "NON_FINITE_OUTCOME_EXCURSION"
        )

    outcome_class, outcome_label = (
        _label_outcome(
            up_excursion_atr=(
                up_excursion_atr
            ),
            down_excursion_atr=(
                down_excursion_atr
            ),
        )
    )

    return FrozenC04ForwardOutcome(
        logical_observation_id=(
            logical_observation_id
        ),

        decision_time_utc=(
            _utc_iso(
                decision_time
            )
        ),

        decision_bar_open_time_utc=(
            _utc_iso(
                decision_bar_open_time
            )
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
            decision_atr14
        ),

        horizon_bars=(
            EXPECTED_HORIZON_BARS
        ),

        horizon_semantics=(
            HORIZON_SEMANTICS
        ),

        decision_bar_semantics=(
            DECISION_BAR_SEMANTICS
        ),

        first_future_bar_time_utc=(
            _utc_iso(
                first_future_time
            )
        ),

        last_future_bar_time_utc=(
            _utc_iso(
                last_future_time
            )
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

        source_anchor_fingerprint=(
            source_anchor_fingerprint
        ),

        source_anchor_version=(
            validated_anchor.anchor_version
        ),
    )