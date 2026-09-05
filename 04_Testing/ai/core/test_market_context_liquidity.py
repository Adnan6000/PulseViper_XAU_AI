"""
Offline deterministic tests for MarketContextLiquidityMap v1.0.

Tests:
- Previous Day High / Low causality
- Previous Week High / Low causality
- Asia session running / previous levels
- confirmed MICRO / INTERNAL / MAJOR swing visibility
- nearest liquidity selection
- prefix invariance / future-leakage protection
"""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pandas as pd
import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Core.market_context_liquidity"
)

MarketContextLiquidityMap: Any = (
    module.MarketContextLiquidityMap
)


def _frame(
    times: list[str],
    opens: list[float],
    highs: list[float],
    lows: list[float],
    closes: list[float],
) -> pd.DataFrame:

    return pd.DataFrame(
        {
            "time": pd.to_datetime(
                times
            ),

            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
        }
    )


def test_previous_day_levels_are_causal() -> None:

    frame = _frame(
        times=[
            "2026-08-10 23:58",
            "2026-08-10 23:59",
            "2026-08-11 00:00",
            "2026-08-11 00:01",
        ],

        opens=[
            100.0,
            101.0,
            102.0,
            103.0,
        ],

        highs=[
            101.0,
            105.0,
            103.0,
            104.0,
        ],

        lows=[
            99.0,
            98.0,
            101.0,
            102.0,
        ],

        closes=[
            100.5,
            104.0,
            102.5,
            103.5,
        ],
    )

    result = (
        MarketContextLiquidityMap()
        .generate(
            frame
        )
    )

    assert np.isnan(
        float(
            result.loc[
                1,
                "ctx_pdh",
            ]
        )
    )

    assert float(
        result.loc[
            2,
            "ctx_pdh",
        ]
    ) == pytest.approx(
        105.0
    )

    assert float(
        result.loc[
            2,
            "ctx_pdl",
        ]
    ) == pytest.approx(
        98.0
    )

    assert float(
        result.loc[
            3,
            "ctx_pdh",
        ]
    ) == pytest.approx(
        105.0
    )


def test_previous_week_levels_use_only_completed_week() -> None:

    frame = _frame(
        times=[
            "2026-08-09 20:00",
            "2026-08-09 21:00",
            "2026-08-10 00:00",
            "2026-08-10 00:01",
        ],

        opens=[
            100.0,
            101.0,
            102.0,
            103.0,
        ],

        highs=[
            104.0,
            110.0,
            106.0,
            107.0,
        ],

        lows=[
            96.0,
            90.0,
            101.0,
            102.0,
        ],

        closes=[
            102.0,
            105.0,
            104.0,
            105.0,
        ],
    )

    result = (
        MarketContextLiquidityMap()
        .generate(
            frame
        )
    )

    assert np.isnan(
        float(
            result.loc[
                1,
                "ctx_pwh",
            ]
        )
    )

    assert float(
        result.loc[
            2,
            "ctx_pwh",
        ]
    ) == pytest.approx(
        110.0
    )

    assert float(
        result.loc[
            2,
            "ctx_pwl",
        ]
    ) == pytest.approx(
        90.0
    )


def test_asia_session_running_and_previous_levels() -> None:

    frame = _frame(
        times=[
            "2026-08-10 00:00",
            "2026-08-10 01:00",
            "2026-08-10 07:59",
            "2026-08-11 00:00",
            "2026-08-11 01:00",
            "2026-08-11 08:00",
        ],

        opens=[
            100.0,
            101.0,
            102.0,
            103.0,
            104.0,
            105.0,
        ],

        highs=[
            101.0,
            106.0,
            104.0,
            104.0,
            105.0,
            106.0,
        ],

        lows=[
            99.0,
            100.0,
            98.0,
            102.0,
            101.0,
            104.0,
        ],

        closes=[
            100.5,
            105.0,
            103.0,
            103.5,
            104.5,
            105.5,
        ],
    )

    result = (
        MarketContextLiquidityMap()
        .generate(
            frame
        )
    )

    assert int(
        result.loc[
            0,
            "ctx_in_asia_session",
        ]
    ) == 1

    assert int(
        result.loc[
            5,
            "ctx_in_asia_session",
        ]
    ) == 0

    assert float(
        result.loc[
            0,
            "ctx_asia_running_high",
        ]
    ) == pytest.approx(
        101.0
    )

    assert float(
        result.loc[
            1,
            "ctx_asia_running_high",
        ]
    ) == pytest.approx(
        106.0
    )

    assert float(
        result.loc[
            2,
            "ctx_asia_running_low",
        ]
    ) == pytest.approx(
        98.0
    )

    assert float(
        result.loc[
            3,
            "ctx_prev_asia_high",
        ]
    ) == pytest.approx(
        106.0
    )

    assert float(
        result.loc[
            3,
            "ctx_prev_asia_low",
        ]
    ) == pytest.approx(
        98.0
    )


def test_confirmed_swings_become_visible_only_on_confirmation_row() -> None:

    frame = _frame(
        times=[
            "2026-08-11 00:00",
            "2026-08-11 00:01",
            "2026-08-11 00:02",
            "2026-08-11 00:03",
            "2026-08-11 00:04",
        ],

        opens=[
            100.0,
            100.0,
            100.0,
            100.0,
            100.0,
        ],

        highs=[
            101.0,
            101.0,
            101.0,
            101.0,
            101.0,
        ],

        lows=[
            99.0,
            99.0,
            99.0,
            99.0,
            99.0,
        ],

        closes=[
            100.0,
            100.0,
            100.0,
            100.0,
            100.0,
        ],
    )

    frame[
        "swing_id"
    ] = [
        0,
        0,
        1,
        0,
        2,
    ]

    frame[
        "swing_type"
    ] = [
        "NONE",
        "NONE",
        "HIGH",
        "NONE",
        "LOW",
    ]

    frame[
        "swing_price"
    ] = [
        np.nan,
        np.nan,
        105.0,
        np.nan,
        95.0,
    ]

    frame[
        "swing_scale"
    ] = [
        "NONE",
        "NONE",
        "INTERNAL",
        "NONE",
        "MAJOR",
    ]

    result = (
        MarketContextLiquidityMap()
        .generate(
            frame
        )
    )

    # INTERNAL HIGH is not known before confirmation row.

    assert np.isnan(
        float(
            result.loc[
                1,
                "ctx_nearest_internal_high",
            ]
        )
    )

    # Becomes usable on confirmation row.

    assert float(
        result.loc[
            2,
            "ctx_nearest_internal_high",
        ]
    ) == pytest.approx(
        105.0
    )

    # MAJOR LOW not yet confirmed.

    assert np.isnan(
        float(
            result.loc[
                3,
                "ctx_nearest_major_low",
            ]
        )
    )

    # MAJOR LOW becomes known on its confirmation row.

    assert float(
        result.loc[
            4,
            "ctx_nearest_major_low",
        ]
    ) == pytest.approx(
        95.0
    )


def test_nearest_liquidity_selects_closest_valid_level() -> None:

    frame = _frame(
        times=[
            "2026-08-10 23:58",
            "2026-08-10 23:59",
            "2026-08-11 00:00",
        ],

        opens=[
            100.0,
            100.0,
            100.0,
        ],

        highs=[
            110.0,
            108.0,
            101.0,
        ],

        lows=[
            90.0,
            92.0,
            99.0,
        ],

        closes=[
            100.0,
            100.0,
            100.0,
        ],
    )

    frame[
        "swing_id"
    ] = [
        0,
        0,
        1,
    ]

    frame[
        "swing_type"
    ] = [
        "NONE",
        "NONE",
        "HIGH",
    ]

    frame[
        "swing_price"
    ] = [
        np.nan,
        np.nan,
        103.0,
    ]

    frame[
        "swing_scale"
    ] = [
        "NONE",
        "NONE",
        "MICRO",
    ]

    result = (
        MarketContextLiquidityMap()
        .generate(
            frame
        )
    )

    # PDH = 110
    # MICRO HIGH = 103
    # Current close = 100
    #
    # MICRO HIGH is the closer upside liquidity.

    assert float(
        result.loc[
            2,
            "ctx_nearest_liquidity_above",
        ]
    ) == pytest.approx(
        103.0
    )

    assert (
        result.loc[
            2,
            "ctx_nearest_liquidity_above_source",
        ]
        ==
        "MICRO_HIGH"
    )

    # PDL = 90 is the only contextual level below.

    assert float(
        result.loc[
            2,
            "ctx_nearest_liquidity_below",
        ]
    ) == pytest.approx(
        90.0
    )

    assert (
        result.loc[
            2,
            "ctx_nearest_liquidity_below_source",
        ]
        ==
        "PDL"
    )


def test_prefix_invariance_proves_no_future_leakage() -> None:

    periods = 1800

    timestamps = pd.date_range(
        "2026-08-10 00:00",
        periods=periods,
        freq="min",
    )

    index = np.arange(
        periods,
        dtype=float,
    )

    close = (
        2000.0
        +
        index * 0.01
        +
        np.sin(
            index / 20.0
        ) * 0.5
    )

    frame = pd.DataFrame(
        {
            "time": timestamps,

            "open": (
                close
                -
                0.05
            ),

            "high": (
                close
                +
                0.30
            ),

            "low": (
                close
                -
                0.30
            ),

            "close": close,

            "swing_id": 0,

            "swing_type": (
                "NONE"
            ),

            "swing_price": (
                np.nan
            ),

            "swing_scale": (
                "NONE"
            ),
        }
    )

    # Simulate an already-causally-confirmed historical swing.

    frame.loc[
        100,
        [
            "swing_id",
            "swing_type",
            "swing_price",
            "swing_scale",
        ],
    ] = [
        1,
        "HIGH",
        2002.0,
        "MICRO",
    ]

    engine = (
        MarketContextLiquidityMap()
    )

    prefix_length = 1200

    full = engine.generate(
        frame
    )

    prefix = engine.generate(
        frame.iloc[
            :prefix_length
        ].copy()
    )

    context_columns = [
        column

        for column
        in prefix.columns

        if column.startswith(
            "ctx_"
        )
    ]

    # Critical causality contract:
    #
    # Adding future candles must NOT change any previously produced
    # market-context value.

    for column in context_columns:

        full_values = (
            full.loc[
                :prefix_length - 1,
                column,
            ]
            .reset_index(
                drop=True
            )
        )

        prefix_values = (
            prefix[
                column
            ]
            .reset_index(
                drop=True
            )
        )

        pd.testing.assert_series_equal(
            full_values,
            prefix_values,
            check_names=False,
            check_dtype=False,
        )