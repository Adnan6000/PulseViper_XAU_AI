"""
Offline deterministic tests for MarketRegimeEngine.

No MetaTrader 5 connection is required.
"""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pandas as pd
import pytest


regime_module: Any = importlib.import_module(
    "02_AI.Core.market_regime"
)

MarketRegimeEngine: Any = (
    regime_module.MarketRegimeEngine
)


def _frame(
    close: np.ndarray,
) -> pd.DataFrame:

    values = np.asarray(
        close,
        dtype=np.float64,
    )

    open_values = np.concatenate(
        (
            values[
                :1
            ],
            values[
                :-1
            ],
        )
    )

    high = (
        np.maximum(
            open_values,
            values,
        )
        + 0.10
    )

    low = (
        np.minimum(
            open_values,
            values,
        )
        - 0.10
    )

    return pd.DataFrame(
        {
            "time": pd.date_range(
                "2026-01-01",
                periods=len(
                    values
                ),
                freq="min",
            ),

            "open": (
                open_values
            ),

            "high": (
                high
            ),

            "low": (
                low
            ),

            "close": (
                values
            ),
        }
    )


def test_market_regime_outputs() -> None:

    x = np.arange(
        600,
        dtype=np.float64,
    )

    data = _frame(
        1900.0
        + x * 0.05
        + 0.03 * np.sin(
            x / 3.0
        )
    )

    engine = MarketRegimeEngine()

    result = engine.generate(
        data
    )

    for column in (
        engine.OUTPUT_COLUMNS
    ):
        assert (
            column
            in result.columns
        )

    assert len(
        result
    ) == len(
        data
    )

    assert (
        result[
            "regime_ready"
        ]
        .isin(
            [
                0,
                1,
            ]
        )
        .all()
    )


def test_market_regime_is_causal_prefix_invariant() -> None:

    x = np.arange(
        700,
        dtype=np.float64,
    )

    data = _frame(
        1900.0
        + x * 0.04
        + 0.10 * np.sin(
            x / 9.0
        )
    )

    engine = MarketRegimeEngine()

    prefix = engine.generate(
        data.iloc[
            :450
        ].copy()
    )

    full = engine.generate(
        data.copy()
    )

    for column in (
        engine.OUTPUT_COLUMNS
    ):

        pd.testing.assert_series_equal(
            prefix[
                column
            ].reset_index(
                drop=True
            ),
            full[
                column
            ].iloc[
                :450
            ].reset_index(
                drop=True
            ),
            check_names=False,
        )


def test_market_regime_detects_bullish_trend() -> None:

    x = np.arange(
        600,
        dtype=np.float64,
    )

    data = _frame(
        1900.0
        + x * 0.08
        + 0.04 * np.sin(
            x / 4.0
        )
    )

    result = (
        MarketRegimeEngine()
        .generate(
            data
        )
    )

    tail = result.loc[
        result[
            "regime_ready"
        ]
        == 1
    ].tail(
        100
    )

    assert not tail.empty

    bullish_rate = float(
        (
            tail[
                "regime_trend"
            ]
            == "BULLISH"
        ).mean()
    )

    assert (
        bullish_rate
        >= 0.90
    )


def test_market_regime_detects_range() -> None:

    x = np.arange(
        600,
        dtype=np.float64,
    )

    data = _frame(
        1900.0
        + 0.15 * np.sin(
            x / 2.0
        )
        + 0.05 * np.sin(
            x / 7.0
        )
    )

    result = (
        MarketRegimeEngine()
        .generate(
            data
        )
    )

    tail = result.loc[
        result[
            "regime_ready"
        ]
        == 1
    ].tail(
        100
    )

    assert not tail.empty

    range_rate = float(
        (
            tail[
                "regime_trend"
            ]
            == "RANGE"
        ).mean()
    )

    assert (
        range_rate
        >= 0.80
    )


def test_market_regime_does_not_mutate_input() -> None:

    x = np.arange(
        300,
        dtype=np.float64,
    )

    data = _frame(
        1900.0
        + x * 0.03
    )

    original = data.copy(
        deep=True
    )

    MarketRegimeEngine().generate(
        data
    )

    pd.testing.assert_frame_equal(
        data,
        original,
    )


def test_market_regime_rejects_missing_ohlc() -> None:

    data = pd.DataFrame(
        {
            "close": [
                1900.0,
                1901.0,
            ]
        }
    )

    with pytest.raises(
        ValueError
    ):

        MarketRegimeEngine().generate(
            data
        )