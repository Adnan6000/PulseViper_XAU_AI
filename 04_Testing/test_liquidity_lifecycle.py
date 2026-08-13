"""
Deterministic offline tests for LiquidityLifecycleMap v1.2.

Contracts covered:
- completed-period static context can act on its first visible candle
- TESTED / SWEPT / BROKEN / ACCEPTED_BEYOND / RECLAIMED remain causal
- confirmed swings cannot act on their confirmation candle
- distinct swing_id values remain distinct even at the same source/price
- overlapping contextual sources remain separate identities
- static context rotation resets the active instance
- candles completely beyond a level do not create fake touches
- prefix invariance prevents future leakage
"""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pandas as pd
import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Core.liquidity_lifecycle"
)

LiquidityLifecycleMap: Any = (
    module.LiquidityLifecycleMap
)


def _engine() -> Any:
    return LiquidityLifecycleMap(
        touch_buffer_atr=0.0,
        sweep_buffer_atr=0.0,
        break_buffer_atr=0.0,
        reclaim_buffer_atr=0.0,
        acceptance_closes=2,
    )


def test_static_context_can_act_on_first_visible_candle() -> None:
    frame = pd.DataFrame(
        {
            "high": [
                105.0,
            ],
            "low": [
                104.0,
            ],
            "close": [
                104.5,
            ],
            "atr": [
                1.0,
            ],
            "ctx_pdh": [
                105.0,
            ],
        }
    )

    result = (
        _engine()
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            0,
            "liq_event_type",
        ]
        ==
        "TESTED"
    )

    assert (
        result.loc[
            0,
            "liq_event_source",
        ]
        ==
        "PDH"
    )

    assert (
        result.loc[
            0,
            "liq_event_side",
        ]
        ==
        "HIGH"
    )

    assert int(
        result.loc[
            0,
            "liq_touch_count_bar",
        ]
    ) == 1


def test_high_liquidity_test_then_sweep() -> None:
    frame = pd.DataFrame(
        {
            "high": [
                104.0,
                105.0,
                106.0,
            ],
            "low": [
                103.0,
                103.0,
                103.0,
            ],
            "close": [
                104.0,
                104.0,
                104.0,
            ],
            "atr": [
                1.0,
                1.0,
                1.0,
            ],
            "ctx_pdh": [
                105.0,
                105.0,
                105.0,
            ],
        }
    )

    result = (
        _engine()
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            0,
            "liq_nearest_above_state",
        ]
        ==
        "UNTOUCHED"
    )

    assert (
        result.loc[
            1,
            "liq_event_type",
        ]
        ==
        "TESTED"
    )

    assert (
        result.loc[
            2,
            "liq_event_type",
        ]
        ==
        "SWEPT"
    )

    assert (
        result.loc[
            2,
            "liq_event_source",
        ]
        ==
        "PDH"
    )

    assert (
        result.loc[
            2,
            "liq_event_side",
        ]
        ==
        "HIGH"
    )


def test_high_liquidity_break_acceptance_and_reclaim() -> None:
    frame = pd.DataFrame(
        {
            "high": [
                104.0,
                106.0,
                106.0,
                106.0,
            ],
            "low": [
                103.0,
                104.0,
                104.0,
                103.0,
            ],
            "close": [
                104.0,
                105.5,
                105.6,
                104.0,
            ],
            "atr": [
                1.0,
                1.0,
                1.0,
                1.0,
            ],
            "ctx_pdh": [
                105.0,
                105.0,
                105.0,
                105.0,
            ],
        }
    )

    result = (
        _engine()
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            1,
            "liq_event_type",
        ]
        ==
        "BROKEN"
    )

    assert (
        result.loc[
            2,
            "liq_event_type",
        ]
        ==
        "ACCEPTED_BEYOND"
    )

    assert (
        result.loc[
            3,
            "liq_event_type",
        ]
        ==
        "RECLAIMED"
    )

    assert int(
        result.loc[
            2,
            "liq_accepted_count",
        ]
    ) == 1

    assert int(
        result.loc[
            3,
            "liq_reclaimed_count",
        ]
    ) == 1


def test_low_liquidity_mirrors_high_logic() -> None:
    frame = pd.DataFrame(
        {
            "high": [
                101.0,
                101.0,
                101.0,
                102.0,
            ],
            "low": [
                100.0,
                99.0,
                98.0,
                99.0,
            ],
            "close": [
                100.0,
                100.0,
                98.5,
                100.5,
            ],
            "atr": [
                1.0,
                1.0,
                1.0,
                1.0,
            ],
            "ctx_pdl": [
                99.0,
                99.0,
                99.0,
                99.0,
            ],
        }
    )

    result = (
        _engine()
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            1,
            "liq_event_type",
        ]
        ==
        "TESTED"
    )

    assert (
        result.loc[
            2,
            "liq_event_type",
        ]
        ==
        "BROKEN"
    )

    assert (
        result.loc[
            3,
            "liq_event_type",
        ]
        ==
        "RECLAIMED"
    )


def test_confirmed_swing_cannot_act_on_confirmation_candle() -> None:
    frame = pd.DataFrame(
        {
            "high": [
                100.0,
                106.0,
                106.0,
            ],
            "low": [
                99.0,
                99.0,
                99.0,
            ],
            "close": [
                99.5,
                104.0,
                104.0,
            ],
            "atr": [
                1.0,
                1.0,
                1.0,
            ],
            "swing_id": [
                0,
                1,
                0,
            ],
            "swing_type": [
                "NONE",
                "HIGH",
                "NONE",
            ],
            "swing_price": [
                np.nan,
                105.0,
                np.nan,
            ],
            "swing_scale": [
                "NONE",
                "MICRO",
                "NONE",
            ],
        }
    )

    result = (
        _engine()
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            1,
            "liq_event_type",
        ]
        ==
        "NONE"
    )

    assert (
        result.loc[
            2,
            "liq_event_type",
        ]
        ==
        "SWEPT"
    )

    assert (
        result.loc[
            2,
            "liq_event_source",
        ]
        ==
        "MICRO_HIGH"
    )


def test_same_price_same_source_different_swing_ids_remain_distinct() -> None:
    frame = pd.DataFrame(
        {
            "high": [
                104.0,
                104.0,
                104.0,
                106.0,
            ],
            "low": [
                103.0,
                103.0,
                103.0,
                103.0,
            ],
            "close": [
                104.0,
                104.0,
                104.0,
                104.0,
            ],
            "atr": [
                1.0,
                1.0,
                1.0,
                1.0,
            ],
            "swing_id": [
                1,
                0,
                2,
                0,
            ],
            "swing_type": [
                "HIGH",
                "NONE",
                "HIGH",
                "NONE",
            ],
            "swing_price": [
                105.0,
                np.nan,
                105.0,
                np.nan,
            ],
            "swing_scale": [
                "MICRO",
                "NONE",
                "MICRO",
                "NONE",
            ],
        }
    )

    result = (
        _engine()
        .generate(
            frame
        )
    )

    assert int(
        result.loc[
            2,
            "liq_registered_count",
        ]
    ) == 2

    assert int(
        result.loc[
            3,
            "liq_sweep_count_bar",
        ]
    ) == 2


def test_same_price_different_sources_keep_separate_identity() -> None:
    frame = pd.DataFrame(
        {
            "high": [
                104.0,
                106.0,
            ],
            "low": [
                103.0,
                103.0,
            ],
            "close": [
                104.0,
                104.0,
            ],
            "atr": [
                1.0,
                1.0,
            ],
            "ctx_pdh": [
                105.0,
                105.0,
            ],
            "ctx_pwh": [
                105.0,
                105.0,
            ],
        }
    )

    result = (
        _engine()
        .generate(
            frame
        )
    )

    assert int(
        result.loc[
            0,
            "liq_registered_count",
        ]
    ) == 2

    assert int(
        result.loc[
            1,
            "liq_sweep_count_bar",
        ]
    ) == 2


def test_daily_context_rotation_same_price_creates_fresh_active_instance() -> None:
    frame = pd.DataFrame(
        {
            "time": pd.to_datetime(
                [
                    "2026-08-10 23:59:00+00:00",
                    "2026-08-11 00:00:00+00:00",
                ],
                utc=True,
            ),
            "high": [
                104.0,
                104.0,
            ],
            "low": [
                103.0,
                103.0,
            ],
            "close": [
                104.0,
                104.0,
            ],
            "atr": [
                1.0,
                1.0,
            ],
            "ctx_pdh": [
                105.0,
                105.0,
            ],
        }
    )

    result = (
        _engine()
        .generate(
            frame
        )
    )

    assert int(
        result.loc[
            0,
            "liq_registered_count",
        ]
    ) == 1

    assert int(
        result.loc[
            1,
            "liq_registered_count",
        ]
    ) == 1

    assert int(
        result.loc[
            0,
            "liq_nearest_above_age_bars",
        ]
    ) == 0

    assert int(
        result.loc[
            1,
            "liq_nearest_above_age_bars",
        ]
    ) == 0


def test_context_price_rotation_deactivates_old_instance_without_time() -> None:
    frame = pd.DataFrame(
        {
            "high": [
                104.0,
                104.5,
            ],
            "low": [
                103.0,
                103.5,
            ],
            "close": [
                104.0,
                104.0,
            ],
            "atr": [
                1.0,
                1.0,
            ],
            "ctx_pdh": [
                105.0,
                106.0,
            ],
        }
    )

    result = (
        _engine()
        .generate(
            frame
        )
    )

    assert int(
        result.loc[
            0,
            "liq_registered_count",
        ]
    ) == 1

    assert int(
        result.loc[
            1,
            "liq_registered_count",
        ]
    ) == 1

    assert float(
        result.loc[
            1,
            "liq_nearest_above_price",
        ]
    ) == pytest.approx(
        106.0
    )

    assert int(
        result.loc[
            1,
            "liq_nearest_above_age_bars",
        ]
    ) == 0


def test_touch_requires_actual_candle_range_overlap() -> None:
    frame = pd.DataFrame(
        {
            "high": [
                106.0,
                106.2,
            ],
            "low": [
                105.5,
                105.4,
            ],
            "close": [
                105.8,
                105.9,
            ],
            "atr": [
                1.0,
                1.0,
            ],
            "ctx_pdh": [
                105.0,
                105.0,
            ],
        }
    )

    result = (
        _engine()
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            0,
            "liq_event_type",
        ]
        ==
        "BROKEN"
    )

    assert (
        result.loc[
            1,
            "liq_event_type",
        ]
        ==
        "ACCEPTED_BEYOND"
    )

    assert int(
        result.loc[
            0,
            "liq_touch_count_bar",
        ]
    ) == 0

    assert int(
        result.loc[
            1,
            "liq_touch_count_bar",
        ]
    ) == 0


def test_version_and_mode_are_explicit() -> None:
    frame = pd.DataFrame(
        {
            "high": [
                100.0,
            ],
            "low": [
                99.0,
            ],
            "close": [
                99.5,
            ],
        }
    )

    result = (
        _engine()
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            0,
            "liq_lifecycle_version",
        ]
        ==
        "1.2"
    )

    assert (
        result.loc[
            0,
            "liq_lifecycle_mode",
        ]
        ==
        "CAUSAL_RESEARCH_METADATA_ONLY"
    )


def test_prefix_invariance_prevents_future_leakage() -> None:
    rows = 200

    sequence = np.arange(
        rows,
        dtype=float,
    )

    base = (
        2000.0
        +
        np.sin(
            sequence
            /
            10.0
        )
    )

    frame = pd.DataFrame(
        {
            "time": pd.date_range(
                "2026-08-10 00:00:00+00:00",
                periods=rows,
                freq="min",
            ),

            "high": (
                base
                +
                0.3
            ),

            "low": (
                base
                -
                0.3
            ),

            "close": base,

            "atr": np.full(
                rows,
                0.6,
            ),

            "ctx_pdh": np.full(
                rows,
                2002.0,
            ),

            "ctx_pdl": np.full(
                rows,
                1998.0,
            ),

            "swing_id": np.zeros(
                rows,
            ),

            "swing_type": np.full(
                rows,
                "NONE",
                dtype=object,
            ),

            "swing_price": np.full(
                rows,
                np.nan,
            ),

            "swing_scale": np.full(
                rows,
                "NONE",
                dtype=object,
            ),
        }
    )

    frame.loc[
        50,
        "swing_id",
    ] = 1

    frame.loc[
        50,
        "swing_type",
    ] = "HIGH"

    frame.loc[
        50,
        "swing_price",
    ] = 2001.5

    frame.loc[
        50,
        "swing_scale",
    ] = "INTERNAL"

    prefix_size = 120

    full = (
        _engine()
        .generate(
            frame
        )
    )

    prefix = (
        _engine()
        .generate(
            frame.iloc[
                :prefix_size
            ].copy()
        )
    )

    lifecycle_columns = [
        column
        for column in prefix.columns
        if column.startswith(
            "liq_"
        )
    ]

    for column in lifecycle_columns:
        full_values = (
            full.loc[
                :prefix_size - 1,
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