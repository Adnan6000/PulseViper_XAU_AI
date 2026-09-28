"""
===============================================================================
Module      : frozen_c04_forward_outcome_maturer.py
Project     : PulseViper XAU AI
Purpose     : Gate 15D-C-A v1.1 — Frozen Forward Outcome Maturation Authority
===============================================================================

Pure / offline forward-outcome maturation authority.

Frozen timestamp semantics:
- Raw M5 `time` is candle OPEN time.
- Gate 13 decision_time = M5 open time + 5 minutes.
- Therefore the decision candle for decision_time T has open time T - 5 minutes.
- Entry close and ATR14 belong to that completed decision candle.
- Outcome horizon is the NEXT 12 COMPLETED M5 ROWS after that decision candle.

This exactly follows the historical training lineage:
    available_time = time + timeframe_minutes
    entry = close[index]
    current_atr = atr[index]
    future_slice = index + 1 : index + horizon_bars + 1

It does NOT:
- access MT5
- acquire market data
- calculate model performance
- calculate accuracy / win rate / PnL / return / drawdown
- mutate any runtime ledger
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
from typing import Any, Mapping, cast

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

FeatureGenerator: Any = (
    _feature_generator_mod.FeatureGenerator
)


MATURATION_VERSION: str = (
    "FROZEN_C04_FORWARD_OUTCOME_MATURER_V1_1"
)

EXPECTED_CONTRACT_FINGERPRINT_SHA256: str = (
    "01fe52a2f068fcc8fb2fc5b89dd7e19dc974fc2d967cfb791e75c3415804ce87"
)

EXPECTED_HORIZON_BARS: int = 12

EXPECTED_BASE_TIMEFRAME: str = "M5"

EXPECTED_BASE_TIMEFRAME_MINUTES: int = 5

EXPECTED_PROFIT_ATR: float = 1.25

EXPECTED_MAX_ADVERSE_ATR: float = 0.75

DECISION_BAR_SEMANTICS: str = (
    "M5_BAR_OPEN_EQUALS_DECISION_TIME_MINUS_5_MINUTES"
)

ENTRY_REFERENCE: str = (
    "DECISION_M5_COMPLETED_BAR_CLOSE"
)

ATR_REFERENCE: str = (
    "DECISION_M5_COMPLETED_BAR_ATR14"
)

HORIZON_SEMANTICS: str = (
    "NEXT_12_COMPLETED_M5_ROWS_AFTER_DECISION_BAR"
)

OUTCOME_MATURATION_AUTHORIZED: bool = True

PERFORMANCE_EVALUATION_AUTHORIZED: bool = False

PNL_EVALUATION_AUTHORIZED: bool = False

LIVE_AUTHORIZED: bool = False

EXECUTION_AUTHORIZED: bool = False


class ForwardOutcomeMaturationError(
    RuntimeError
):
    pass


class InsufficientFutureBarsError(
    ForwardOutcomeMaturationError
):
    pass


@dataclass(frozen=True)
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

    contract_fingerprint_sha256: str = (
        EXPECTED_CONTRACT_FINGERPRINT_SHA256
    )

    maturation_version: str = (
        MATURATION_VERSION
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

            "contract_fingerprint_sha256": (
                self.contract_fingerprint_sha256
            ),

            "maturation_version": (
                self.maturation_version
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

    converted = timestamp.tz_convert(
        "UTC"
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

    timestamp = _utc_timestamp(
        value
    )

    output = timestamp.isoformat()

    if output.endswith(
        "+00:00"
    ):

        return (
            output[
                :-6
            ]
            +
            "Z"
        )

    return output


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

    numeric = output[
        [
            "open",
            "high",
            "low",
            "close",
        ]
    ].to_numpy(
        dtype=float
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


def mature_observation(
    *,
    observation: Mapping[str, Any],
    completed_m5_bars: pd.DataFrame,
) -> FrozenC04ForwardOutcome:

    verify_authorities()

    eligibility = (
        _eligibility.assess_observation(
            observation
        )
    )

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

    logical_observation_id = (
        observation.get(
            "logical_observation_id"
        )
    )

    source_observation_fingerprint = (
        observation.get(
            "semantic_record_fingerprint"
        )
    )

    decision_time_raw = (
        observation.get(
            "decision_time_utc"
        )
    )

    if not isinstance(
        logical_observation_id,
        str,
    ):

        raise ForwardOutcomeMaturationError(
            "LOGICAL_OBSERVATION_ID_MISSING"
        )

    if not isinstance(
        source_observation_fingerprint,
        str,
    ):

        raise ForwardOutcomeMaturationError(
            "SOURCE_OBSERVATION_FINGERPRINT_MISSING"
        )

    if not isinstance(
        decision_time_raw,
        str,
    ):

        raise ForwardOutcomeMaturationError(
            "DECISION_TIME_MISSING"
        )

    decision_time = (
        _utc_timestamp(
            decision_time_raw
        )
    )

    decision_bar_open_time = (
        decision_time
        -
        pd.Timedelta(
            minutes=(
                EXPECTED_BASE_TIMEFRAME_MINUTES
            )
        )
    )

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

    if decision_index < 13:

        raise ForwardOutcomeMaturationError(
            "INSUFFICIENT_PRE_DECISION_HISTORY_FOR_ATR14"
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

    if future_end > len(
        raw
    ):

        available = max(
            0,
            len(
                raw
            )
            -
            future_start,
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

    if len(
        future
    ) != EXPECTED_HORIZON_BARS:

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

    first_future_time = cast(
        pd.Timestamp,
        future.iloc[
            0
        ][
            "time"
        ],
    )

    if (
        first_future_time
        <=
        decision_bar_open_time
    ):

        raise ForwardOutcomeMaturationError(
            "FIRST_FUTURE_BAR_NOT_AFTER_DECISION_BAR"
        )

    last_future_time = cast(
        pd.Timestamp,
        future.iloc[
            -1
        ][
            "time"
        ],
    )

    if (
        last_future_time
        <=
        first_future_time
    ):

        raise ForwardOutcomeMaturationError(
            "LAST_FUTURE_BAR_NOT_AFTER_FIRST_FUTURE_BAR"
        )

    feature_generator = (
        FeatureGenerator()
    )

    featured = (
        feature_generator.generate(
            raw.iloc[
                :
                decision_index
                +
                1
            ].copy()
        )
    )

    if (
        "atr14"
        not in featured.columns
    ):

        raise ForwardOutcomeMaturationError(
            "ATR14_NOT_GENERATED"
        )

    entry_close = float(
        raw.iloc[
            decision_index
        ][
            "close"
        ]
    )

    decision_atr14 = float(
        featured.iloc[
            -1
        ][
            "atr14"
        ]
    )

    if (
        not math.isfinite(
            entry_close
        )
        or
        entry_close
        <=
        0.0
    ):

        raise ForwardOutcomeMaturationError(
            "DECISION_ENTRY_CLOSE_INVALID"
        )

    if (
        not math.isfinite(
            decision_atr14
        )
        or
        decision_atr14
        <=
        0.0
    ):

        raise ForwardOutcomeMaturationError(
            "DECISION_ATR14_INVALID"
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

    up_excursion_atr = (
        max_future_high
        -
        entry_close
    ) / decision_atr14

    down_excursion_atr = (
        entry_close
        -
        min_future_low
    ) / decision_atr14

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
    )