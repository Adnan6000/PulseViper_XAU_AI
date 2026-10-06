from __future__ import annotations

import importlib
from typing import Any, cast

import numpy as np
import pandas as pd
import pytest


_regime: Any = importlib.import_module(
    "02_AI.Intelligence."
    "market_regime_intelligence"
)


def make_frame(
    *,
    count: int = 260,
    start: float = 4000.0,
    drift: float = 0.20,
    wave: float = 0.10,
    range_size: float = 1.50,
) -> pd.DataFrame:

    time = pd.date_range(
        "2026-01-01T00:00:00Z",
        periods=count,
        freq="5min",
    )

    index = np.arange(
        count,
        dtype=np.float64,
    )

    close = (
        start
        +
        index
        *
        drift
        +
        np.sin(
            index
            /
            5.0
        )
        *
        wave
    )

    open_ = np.concatenate(
        (
            [close[0]],
            close[:-1],
        )
    )

    high = (
        np.maximum(
            open_,
            close,
        )
        +
        range_size
        /
        2.0
    )

    low = (
        np.minimum(
            open_,
            close,
        )
        -
        range_size
        /
        2.0
    )

    return pd.DataFrame(
        {
            "time": time,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "tick_volume": 100,
        }
    )


def decision_after_frame(
    frame: pd.DataFrame,
) -> pd.Timestamp:

    value = pd.Timestamp(
        frame["time"].iloc[-1]
    )

    assert value is not pd.NaT

    return cast(
        pd.Timestamp,
        value
        +
        pd.Timedelta(
            minutes=5
        ),
    )

def test_01_version_exact() -> None:

    assert (
        _regime.INTELLIGENCE_VERSION
        ==
        "MARKET_REGIME_INTELLIGENCE_V1"
    )


def test_02_no_trade_authority() -> None:

    assert (
        _regime.TRADE_AUTHORIZED
        is False
    )

    assert (
        _regime.LIVE_AUTHORIZED
        is False
    )

    assert (
        _regime.EXECUTION_AUTHORIZED
        is False
    )


def test_03_uptrend_detected() -> None:

    frame = make_frame(
        drift=0.40,
        wave=0.03,
    )

    result = (
        _regime
        .analyze_market_regime(
            completed_m5=frame,
            decision_time_utc=(
                decision_after_frame(
                    frame
                )
            ),
        )
    )

    assert result.regime in {
        _regime.REGIME_TREND_UP,
        _regime.REGIME_BREAKOUT_UP,
    }

    assert (
        result.trend_direction_score
        >
        0
    )


def test_04_downtrend_detected() -> None:

    frame = make_frame(
        start=4200.0,
        drift=-0.40,
        wave=0.03,
    )

    result = (
        _regime
        .analyze_market_regime(
            completed_m5=frame,
            decision_time_utc=(
                decision_after_frame(
                    frame
                )
            ),
        )
    )

    assert result.regime in {
        _regime.REGIME_TREND_DOWN,
        _regime.REGIME_BREAKOUT_DOWN,
    }

    assert (
        result.trend_direction_score
        <
        0
    )


def test_05_range_or_transition_detected() -> None:

    frame = make_frame(
        drift=0.0,
        wave=0.25,
    )

    result = (
        _regime
        .analyze_market_regime(
            completed_m5=frame,
            decision_time_utc=(
                decision_after_frame(
                    frame
                )
            ),
        )
    )

    assert result.regime in {
        _regime.REGIME_RANGE,
        _regime.REGIME_TRANSITION,
        _regime.REGIME_COMPRESSION,
    }


def test_06_compression_detected() -> None:

    frame = make_frame(
        drift=0.03,
        wave=0.08,
        range_size=2.0,
    )

    last = frame.index[-10:]

    for idx in last:

        middle = float(
            frame.loc[
                idx,
                "close",
            ]
        )

        frame.loc[
            idx,
            "open",
        ] = middle

        frame.loc[
            idx,
            "high",
        ] = (
            middle
            +
            0.20
        )

        frame.loc[
            idx,
            "low",
        ] = (
            middle
            -
            0.20
        )

    result = (
        _regime
        .analyze_market_regime(
            completed_m5=frame,
            decision_time_utc=(
                decision_after_frame(
                    frame
                )
            ),
        )
    )

    assert (
        result.compression_detected
        is True
    )

    assert (
        result.regime
        ==
        _regime.REGIME_COMPRESSION
    )


def test_07_breakout_up_detected() -> None:

    frame = make_frame(
        drift=0.02,
        wave=0.10,
    )

    previous_high = float(
        frame[
            "high"
        ]
        .iloc[-21:-1]
        .max()
    )

    frame.loc[
        frame.index[-1],
        "open",
    ] = previous_high

    frame.loc[
        frame.index[-1],
        "close",
    ] = (
        previous_high
        +
        5.0
    )

    frame.loc[
        frame.index[-1],
        "high",
    ] = (
        previous_high
        +
        5.5
    )

    frame.loc[
        frame.index[-1],
        "low",
    ] = (
        previous_high
        -
        0.3
    )

    result = (
        _regime
        .analyze_market_regime(
            completed_m5=frame,
            decision_time_utc=(
                decision_after_frame(
                    frame
                )
            ),
        )
    )

    assert (
        result.breakout_up_detected
        is True
    )

    assert (
        result.regime
        ==
        _regime.REGIME_BREAKOUT_UP
    )


def test_08_breakout_down_detected() -> None:

    frame = make_frame(
        drift=-0.02,
        wave=0.10,
    )

    previous_low = float(
        frame[
            "low"
        ]
        .iloc[-21:-1]
        .min()
    )

    frame.loc[
        frame.index[-1],
        "open",
    ] = previous_low

    frame.loc[
        frame.index[-1],
        "close",
    ] = (
        previous_low
        -
        5.0
    )

    frame.loc[
        frame.index[-1],
        "high",
    ] = (
        previous_low
        +
        0.3
    )

    frame.loc[
        frame.index[-1],
        "low",
    ] = (
        previous_low
        -
        5.5
    )

    result = (
        _regime
        .analyze_market_regime(
            completed_m5=frame,
            decision_time_utc=(
                decision_after_frame(
                    frame
                )
            ),
        )
    )

    assert (
        result.breakout_down_detected
        is True
    )

    assert (
        result.regime
        ==
        _regime.REGIME_BREAKOUT_DOWN
    )


def test_09_confidence_bounded() -> None:

    frame = make_frame()

    result = (
        _regime
        .analyze_market_regime(
            completed_m5=frame,
            decision_time_utc=(
                decision_after_frame(
                    frame
                )
            ),
        )
    )

    assert (
        0.0
        <=
        result.regime_confidence
        <=
        1.0
    )


def test_10_output_trade_flags_false() -> None:

    frame = make_frame()

    result = (
        _regime
        .analyze_market_regime(
            completed_m5=frame,
            decision_time_utc=(
                decision_after_frame(
                    frame
                )
            ),
        )
    )

    assert (
        result.trade_authorized
        is False
    )

    assert (
        result.live_authorized
        is False
    )

    assert (
        result.execution_authorized
        is False
    )


def test_11_forming_bar_forbidden() -> None:

    frame = make_frame()

    with pytest.raises(
        _regime.MarketRegimeIntelligenceError,
        match=(
            "FORMING_M5_BAR_FORBIDDEN"
        ),
    ):

        _regime.analyze_market_regime(
            completed_m5=frame,
            decision_time_utc=(
                frame[
                    "time"
                ].iloc[-1]
            ),
        )


def test_12_insufficient_history_blocked() -> None:

    frame = make_frame(
        count=100
    )

    with pytest.raises(
        _regime.MarketRegimeIntelligenceError,
        match=(
            "M5_INSUFFICIENT_HISTORY"
        ),
    ):

        _regime.analyze_market_regime(
            completed_m5=frame,
            decision_time_utc=(
                decision_after_frame(
                    frame
                )
            ),
        )


def test_13_duplicate_timestamp_blocked() -> None:

    frame = make_frame()

    frame.loc[
        frame.index[-1],
        "time",
    ] = frame.loc[
        frame.index[-2],
        "time",
    ]

    with pytest.raises(
        _regime.MarketRegimeIntelligenceError,
        match=(
            "M5_DUPLICATE_TIMESTAMPS"
        ),
    ):

        _regime.analyze_market_regime(
            completed_m5=frame,
            decision_time_utc=(
                decision_after_frame(
                    frame
                )
                +
                pd.Timedelta(
                    minutes=5
                )
            ),
        )


def test_14_invalid_instrument_blocked() -> None:

    frame = make_frame()

    with pytest.raises(
        _regime.MarketRegimeIntelligenceError,
        match=(
            "UNSUPPORTED_CANONICAL_INSTRUMENT"
        ),
    ):

        _regime.analyze_market_regime(
            completed_m5=frame,
            decision_time_utc=(
                decision_after_frame(
                    frame
                )
            ),
            canonical_instrument=(
                "EURUSD"
            ),
        )


def test_15_output_serializable() -> None:

    frame = make_frame()

    result = (
        _regime
        .analyze_market_regime(
            completed_m5=frame,
            decision_time_utc=(
                decision_after_frame(
                    frame
                )
            ),
        )
    )

    payload = result.to_dict()

    assert (
        payload[
            "intelligence_version"
        ]
        ==
        "MARKET_REGIME_INTELLIGENCE_V1"
    )

    assert (
        payload[
            "canonical_instrument"
        ]
        ==
        "XAUUSD"
    )