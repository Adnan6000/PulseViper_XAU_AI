"""
Deterministic offline tests for LiquidityStructureIntelligence v1.2.
"""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pandas as pd
import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Core.liquidity_structure_intelligence"
)

LiquidityStructureIntelligence: Any = (
    module.LiquidityStructureIntelligence
)


def test_external_levels_form_cluster() -> None:

    frame = pd.DataFrame(
        {
            "close": [
                100.0,
            ],

            "atr": [
                2.0,
            ],

            "ctx_pdh": [
                101.0,
            ],

            "ctx_pwh": [
                101.10,
            ],

            "ctx_nearest_major_high": [
                101.15,
            ],
        }
    )

    result = (
        LiquidityStructureIntelligence(
            cluster_tolerance_atr=0.10
        )
        .generate(
            frame
        )
    )

    assert int(
        result.loc[
            0,
            "liqintel_above_cluster_count",
        ]
    ) == 3

    assert int(
        result.loc[
            0,
            "liqintel_above_external_count",
        ]
    ) == 3

    assert (
        result.loc[
            0,
            "liqintel_above_cluster_type",
        ]
        ==
        "EXTERNAL"
    )


def test_external_and_internal_make_mixed_cluster() -> None:

    frame = pd.DataFrame(
        {
            "close": [
                100.0,
            ],

            "atr": [
                2.0,
            ],

            "ctx_pdh": [
                101.0,
            ],

            "ctx_nearest_micro_high": [
                101.10,
            ],
        }
    )

    result = (
        LiquidityStructureIntelligence(
            cluster_tolerance_atr=0.10
        )
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            0,
            "liqintel_above_cluster_type",
        ]
        ==
        "MIXED"
    )

    assert int(
        result.loc[
            0,
            "liqintel_above_external_count",
        ]
    ) == 1

    assert int(
        result.loc[
            0,
            "liqintel_above_internal_count",
        ]
    ) == 1


def test_buy_side_sweep_is_bearish_trap_context() -> None:

    frame = pd.DataFrame(
        {
            "close": [
                100.0,
            ],

            "atr": [
                1.0,
            ],

            "liq_event_type": [
                "SWEPT",
            ],

            "liq_event_side": [
                "HIGH",
            ],
        }
    )

    result = (
        LiquidityStructureIntelligence()
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            0,
            "liqintel_event_interpretation",
        ]
        ==
        "BUY_SIDE_SWEEP_TRAP"
    )

    assert (
        result.loc[
            0,
            "liqintel_event_bias",
        ]
        ==
        "BEARISH"
    )

    assert int(
        result.loc[
            0,
            "liqintel_trap_flag",
        ]
    ) == 1


def test_sell_side_sweep_is_bullish_trap_context() -> None:

    frame = pd.DataFrame(
        {
            "close": [
                100.0,
            ],

            "atr": [
                1.0,
            ],

            "liq_event_type": [
                "SWEPT",
            ],

            "liq_event_side": [
                "LOW",
            ],
        }
    )

    result = (
        LiquidityStructureIntelligence()
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            0,
            "liqintel_event_interpretation",
        ]
        ==
        "SELL_SIDE_SWEEP_TRAP"
    )

    assert (
        result.loc[
            0,
            "liqintel_event_bias",
        ]
        ==
        "BULLISH"
    )


def test_accepted_breakout_has_directional_bias() -> None:

    frame = pd.DataFrame(
        {
            "close": [
                100.0,
            ],

            "atr": [
                1.0,
            ],

            "liq_event_type": [
                "ACCEPTED_BEYOND",
            ],

            "liq_event_side": [
                "HIGH",
            ],
        }
    )

    result = (
        LiquidityStructureIntelligence()
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            0,
            "liqintel_event_interpretation",
        ]
        ==
        "UPSIDE_BREAKOUT_ACCEPTED"
    )

    assert (
        result.loc[
            0,
            "liqintel_event_bias",
        ]
        ==
        "BULLISH"
    )

    assert int(
        result.loc[
            0,
            "liqintel_breakout_accepted_flag",
        ]
    ) == 1


def test_reclaimed_high_is_failed_upside_breakout() -> None:

    frame = pd.DataFrame(
        {
            "close": [
                100.0,
            ],

            "atr": [
                1.0,
            ],

            "liq_event_type": [
                "RECLAIMED",
            ],

            "liq_event_side": [
                "HIGH",
            ],
        }
    )

    result = (
        LiquidityStructureIntelligence()
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            0,
            "liqintel_event_interpretation",
        ]
        ==
        "FAILED_UPSIDE_BREAKOUT"
    )

    assert (
        result.loc[
            0,
            "liqintel_event_bias",
        ]
        ==
        "BEARISH"
    )

    assert int(
        result.loc[
            0,
            "liqintel_failed_breakout_flag",
        ]
    ) == 1


def test_levels_on_wrong_side_are_excluded() -> None:

    frame = pd.DataFrame(
        {
            "close": [
                100.0,
            ],

            "atr": [
                1.0,
            ],

            # Invalid for ABOVE because below current price.
            "ctx_pdh": [
                99.0,
            ],

            "ctx_prev_london_high": [
                102.0,
            ],

            # Invalid for BELOW because above current price.
            "ctx_pdl": [
                101.0,
            ],

            "ctx_prev_london_low": [
                98.0,
            ],
        }
    )

    result = (
        LiquidityStructureIntelligence()
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            0,
            "liqintel_above_cluster_sources",
        ]
        ==
        "PREV_LONDON_HIGH"
    )

    assert (
        result.loc[
            0,
            "liqintel_below_cluster_sources",
        ]
        ==
        "PREV_LONDON_LOW"
    )


def test_prefix_invariance() -> None:

    rows = 100

    frame = pd.DataFrame(
        {
            "close": np.linspace(
                100.0,
                101.0,
                rows,
            ),

            "atr": np.ones(
                rows,
            ),

            "ctx_pdh": np.full(
                rows,
                102.0,
            ),

            "ctx_pdl": np.full(
                rows,
                98.0,
            ),

            "liq_event_type": np.full(
                rows,
                "NONE",
                dtype=object,
            ),

            "liq_event_side": np.full(
                rows,
                "NONE",
                dtype=object,
            ),
        }
    )

    engine = (
        LiquidityStructureIntelligence()
    )

    prefix_size = 60

    full = engine.generate(
        frame
    )

    prefix = engine.generate(
        frame.iloc[
            :prefix_size
        ].copy()
    )

    columns = [
        column

        for column
        in prefix.columns

        if column.startswith(
            "liqintel_"
        )
    ]

    for column in columns:

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