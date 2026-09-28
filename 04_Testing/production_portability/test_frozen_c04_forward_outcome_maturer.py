from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pandas as pd
import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_maturer"
)


DECISION_TIME: str = (
    "2026-09-28T12:00:00Z"
)


def _observation() -> dict[str, Any]:

    return {
        "logical_observation_id": (
            "a"
            *
            64
        ),
        "semantic_record_fingerprint": (
            "b"
            *
            64
        ),
        "decision_time_utc": (
            DECISION_TIME
        ),
        "canonical_instrument": "XAUUSD",
        "source_provenance": (
            "TRUE_FORWARD_OBSERVATION"
        ),
        "is_true_forward_eligible": True,
        "feature_columns_sha256": (
            "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
        ),
        "model_sha256": (
            "48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769"
        ),
        "live_authorized": False,
        "execution_authorized": False,
    }


def _base_frame(
    *,
    future_high_offset: float = 0.5,
    future_low_offset: float = 0.5,
) -> pd.DataFrame:

    decision = pd.Timestamp(
        DECISION_TIME
    )

    start = (
        decision
        -
        pd.Timedelta(
            minutes=(
                30
                *
                5
            )
        )
    )

    times = pd.date_range(
        start=start,
        periods=43,
        freq="5min",
        tz="UTC",
    )

    prices = (
        2000.0
        +
        np.arange(
            len(
                times
            ),
            dtype=float,
        )
        *
        0.1
    )

    frame = pd.DataFrame(
        {
            "time": times,
            "open": prices,
            "high": (
                prices
                +
                1.0
            ),
            "low": (
                prices
                -
                1.0
            ),
            "close": (
                prices
                +
                0.2
            ),
            "tick_volume": 100,
        }
    )

    decision_positions = np.flatnonzero(
        (
            frame[
                "time"
            ]
            ==
            decision
        ).to_numpy(
            dtype=bool
        )
    )

    assert len(
        decision_positions
    ) == 1

    decision_index = int(
        decision_positions[
            0
        ]
    )

    entry = float(
        frame.iloc[
            decision_index
        ][
            "close"
        ]
    )

    # Stable historical TR = 2.0.
    # Therefore decision ATR14 = 2.0.
    frame.loc[
        :,
        "open"
    ] = entry

    frame.loc[
        :,
        "close"
    ] = entry

    frame.loc[
        :,
        "high"
    ] = (
        entry
        +
        1.0
    )

    frame.loc[
        :,
        "low"
    ] = (
        entry
        -
        1.0
    )

    future_indexes = frame.index[
        decision_index
        +
        1:
        decision_index
        +
        13
    ]

    frame.loc[
        future_indexes,
        "high"
    ] = (
        entry
        +
        future_high_offset
    )

    frame.loc[
        future_indexes,
        "low"
    ] = (
        entry
        -
        future_low_offset
    )

    frame.loc[
        future_indexes,
        "open"
    ] = entry

    frame.loc[
        future_indexes,
        "close"
    ] = entry

    return frame


def test_01_authorities_pass() -> None:

    assert (
        module.verify_authorities()
        is True
    )


def test_02_exact_frozen_parameters() -> None:

    assert (
        module.EXPECTED_BASE_TIMEFRAME
        ==
        "M5"
    )

    assert (
        module.EXPECTED_HORIZON_BARS
        ==
        12
    )

    assert (
        module.EXPECTED_PROFIT_ATR
        ==
        pytest.approx(
            1.25
        )
    )

    assert (
        module.EXPECTED_MAX_ADVERSE_ATR
        ==
        pytest.approx(
            0.75
        )
    )

    assert (
        module.HORIZON_SEMANTICS
        ==
        "NEXT_12_COMPLETED_M5_ROWS_AFTER_DECISION_ROW"
    )


def test_03_no_performance_or_execution_authority() -> None:

    assert (
        module.OUTCOME_MATURATION_AUTHORIZED
        is True
    )

    assert (
        module.PERFORMANCE_EVALUATION_AUTHORIZED
        is False
    )

    assert (
        module.PNL_EVALUATION_AUTHORIZED
        is False
    )

    assert (
        module.LIVE_AUTHORIZED
        is False
    )

    assert (
        module.EXECUTION_AUTHORIZED
        is False
    )


def test_04_long_outcome() -> None:

    # ATR14 = 2.0.
    # Up = 3.0 / 2.0 = 1.5 ATR.
    # Down = 1.0 / 2.0 = 0.5 ATR.
    frame = _base_frame(
        future_high_offset=3.0,
        future_low_offset=1.0,
    )

    outcome = (
        module.mature_observation(
            observation=_observation(),
            completed_m5_bars=frame,
        )
    )

    assert (
        outcome.outcome_class
        ==
        1
    )

    assert (
        outcome.outcome_label
        ==
        "LONG"
    )

    assert (
        outcome.up_excursion_atr
        ==
        pytest.approx(
            1.5
        )
    )

    assert (
        outcome.down_excursion_atr
        ==
        pytest.approx(
            0.5
        )
    )


def test_05_short_outcome() -> None:

    frame = _base_frame(
        future_high_offset=1.0,
        future_low_offset=3.0,
    )

    outcome = (
        module.mature_observation(
            observation=_observation(),
            completed_m5_bars=frame,
        )
    )

    assert (
        outcome.outcome_class
        ==
        -1
    )

    assert (
        outcome.outcome_label
        ==
        "SHORT"
    )

    assert (
        outcome.up_excursion_atr
        ==
        pytest.approx(
            0.5
        )
    )

    assert (
        outcome.down_excursion_atr
        ==
        pytest.approx(
            1.5
        )
    )


def test_06_no_trade_when_neither_clean_direction() -> None:

    frame = _base_frame(
        future_high_offset=1.0,
        future_low_offset=1.0,
    )

    outcome = (
        module.mature_observation(
            observation=_observation(),
            completed_m5_bars=frame,
        )
    )

    assert (
        outcome.outcome_class
        ==
        0
    )

    assert (
        outcome.outcome_label
        ==
        "NO_TRADE"
    )


def test_07_no_trade_when_both_sides_large() -> None:

    frame = _base_frame(
        future_high_offset=3.0,
        future_low_offset=3.0,
    )

    outcome = (
        module.mature_observation(
            observation=_observation(),
            completed_m5_bars=frame,
        )
    )

    assert (
        outcome.outcome_class
        ==
        0
    )

    assert (
        outcome.outcome_label
        ==
        "NO_TRADE"
    )


def test_08_exact_12_future_rows_required() -> None:

    frame = (
        _base_frame()
        .iloc[
            :-1
        ]
        .copy()
    )

    with pytest.raises(
        module.InsufficientFutureBarsError,
        match=(
            "INSUFFICIENT_COMPLETED_FUTURE_M5_BARS"
        ),
    ):
        module.mature_observation(
            observation=_observation(),
            completed_m5_bars=frame,
        )


def test_09_missing_decision_bar_rejected() -> None:

    frame = _base_frame()

    frame = frame[
        frame[
            "time"
        ]
        !=
        pd.Timestamp(
            DECISION_TIME
        )
    ].copy()

    with pytest.raises(
        module.ForwardOutcomeMaturationError,
        match="DECISION_M5_BAR_NOT_UNIQUE",
    ):
        module.mature_observation(
            observation=_observation(),
            completed_m5_bars=frame,
        )


def test_10_market_gap_does_not_change_row_horizon() -> None:

    frame = _base_frame(
        future_high_offset=3.0,
        future_low_offset=1.0,
    )

    decision = pd.Timestamp(
        DECISION_TIME
    )

    # Simulate a session/weekend-style gap after the third future bar.
    mask = (
        frame[
            "time"
        ]
        >
        (
            decision
            +
            pd.Timedelta(
                minutes=15
            )
        )
    )

    frame.loc[
        mask,
        "time"
    ] = (
        frame.loc[
            mask,
            "time"
        ]
        +
        pd.Timedelta(
            hours=48
        )
    )

    outcome = (
        module.mature_observation(
            observation=_observation(),
            completed_m5_bars=frame,
        )
    )

    assert (
        outcome.horizon_bars
        ==
        12
    )

    assert (
        outcome.outcome_class
        ==
        1
    )


def test_11_pre_contract_observation_rejected() -> None:

    observation = _observation()

    observation[
        "decision_time_utc"
    ] = (
        "2026-09-28T10:15:00Z"
    )

    with pytest.raises(
        module.ForwardOutcomeMaturationError,
        match="OBSERVATION_NOT_PROSPECTIVELY_ELIGIBLE",
    ):
        module.mature_observation(
            observation=observation,
            completed_m5_bars=(
                _base_frame()
            ),
        )


def test_12_semantic_fingerprint_is_deterministic() -> None:

    frame = _base_frame(
        future_high_offset=3.0,
        future_low_offset=1.0,
    )

    first = (
        module.mature_observation(
            observation=_observation(),
            completed_m5_bars=frame,
        )
    )

    second = (
        module.mature_observation(
            observation=_observation(),
            completed_m5_bars=frame.copy(),
        )
    )

    assert (
        first.semantic_fingerprint()
        ==
        second.semantic_fingerprint()
    )


def test_13_source_observation_fingerprint_preserved() -> None:

    outcome = (
        module.mature_observation(
            observation=_observation(),
            completed_m5_bars=(
                _base_frame()
            ),
        )
    )

    assert (
        outcome.source_observation_fingerprint
        ==
        (
            "b"
            *
            64
        )
    )


def test_14_future_window_boundaries() -> None:

    outcome = (
        module.mature_observation(
            observation=_observation(),
            completed_m5_bars=(
                _base_frame()
            ),
        )
    )

    assert (
        outcome.first_future_bar_time_utc
        ==
        "2026-09-28T12:05:00Z"
    )

    assert (
        outcome.last_future_bar_time_utc
        ==
        "2026-09-28T13:00:00Z"
    )

    assert (
        outcome.horizon_bars
        ==
        12
    )


def test_15_decision_atr_matches_frozen_feature_generator() -> None:

    outcome = (
        module.mature_observation(
            observation=_observation(),
            completed_m5_bars=(
                _base_frame()
            ),
        )
    )

    assert (
        outcome.decision_atr14
        ==
        pytest.approx(
            2.0
        )
    )


def test_16_outcome_semantics_are_row_based() -> None:

    outcome = (
        module.mature_observation(
            observation=_observation(),
            completed_m5_bars=(
                _base_frame()
            ),
        )
    )

    assert (
        outcome.horizon_semantics
        ==
        "NEXT_12_COMPLETED_M5_ROWS_AFTER_DECISION_ROW"
    )