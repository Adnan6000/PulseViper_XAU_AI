"""
Deterministic offline tests for CandleSwingIntelligence v1.0.

Critical contracts:
- candle anatomy is measured correctly
- basic pattern flags are deterministic
- liquidity-context composites remain causal
- generate() is prefix invariant
- generate() NEVER emits retrospective cslabel_* columns
- generate_research() may label historical swing origins
- future swing confirmation may change research labels
- future swing confirmation must NOT change causal csi_* features
"""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pandas as pd
import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Core.candle_swing_intelligence"
)

CandleSwingIntelligence: Any = (
    module.CandleSwingIntelligence
)


def _frame(
    rows: list[
        tuple[
            float,
            float,
            float,
            float,
        ]
    ],
) -> pd.DataFrame:

    return pd.DataFrame(
        rows,
        columns=[
            "open",
            "high",
            "low",
            "close",
        ],
    )


def test_candle_anatomy_is_measured_correctly() -> None:

    frame = _frame(
        [
            (
                100.0,
                104.0,
                98.0,
                103.0,
            ),
        ]
    )

    result = (
        CandleSwingIntelligence()
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            0,
            "csi_direction",
        ]
        ==
        "BULLISH"
    )

    assert float(
        result.loc[
            0,
            "csi_range",
        ]
    ) == pytest.approx(
        6.0
    )

    assert float(
        result.loc[
            0,
            "csi_body",
        ]
    ) == pytest.approx(
        3.0
    )

    assert float(
        result.loc[
            0,
            "csi_upper_wick",
        ]
    ) == pytest.approx(
        1.0
    )

    assert float(
        result.loc[
            0,
            "csi_lower_wick",
        ]
    ) == pytest.approx(
        2.0
    )

    assert float(
        result.loc[
            0,
            "csi_body_ratio",
        ]
    ) == pytest.approx(
        0.5
    )

    assert float(
        result.loc[
            0,
            "csi_close_location",
        ]
    ) == pytest.approx(
        5.0
        /
        6.0
    )


def test_engulfing_inside_outside_and_doji_flags() -> None:

    frame = _frame(
        [
            (
                101.0,
                102.0,
                99.0,
                100.0,
            ),

            (
                99.5,
                103.0,
                98.5,
                102.0,
            ),

            (
                101.0,
                102.0,
                100.0,
                101.05,
            ),
        ]
    )

    result = (
        CandleSwingIntelligence()
        .generate(
            frame
        )
    )

    assert int(
        result.loc[
            1,
            "csi_bullish_engulfing_flag",
        ]
    ) == 1

    assert int(
        result.loc[
            1,
            "csi_outside_bar_flag",
        ]
    ) == 1

    assert int(
        result.loc[
            2,
            "csi_inside_bar_flag",
        ]
    ) == 1

    assert int(
        result.loc[
            2,
            "csi_doji_flag",
        ]
    ) == 1


def test_rejection_and_liquidity_context_composite() -> None:

    frame = _frame(
        [
            (
                100.0,
                101.0,
                95.0,
                100.5,
            ),
        ]
    )

    frame[
        "liqintel_event_interpretation"
    ] = [
        "SELL_SIDE_SWEEP_TRAP",
    ]

    frame[
        "liqintel_event_bias"
    ] = [
        "BULLISH",
    ]

    frame[
        "liqintel_trap_flag"
    ] = [
        1,
    ]

    frame[
        "liqintel_failed_breakout_flag"
    ] = [
        0,
    ]

    result = (
        CandleSwingIntelligence()
        .generate(
            frame
        )
    )

    assert int(
        result.loc[
            0,
            "csi_bullish_rejection_flag",
        ]
    ) == 1

    assert int(
        result.loc[
            0,
            "csi_bullish_liquidity_rejection_flag",
        ]
    ) == 1

    assert (
        result.loc[
            0,
            "csi_liquidity_bias",
        ]
        ==
        "BULLISH"
    )


def test_generate_is_prefix_invariant_and_live_safe() -> None:

    periods = 200

    index = np.arange(
        periods,
        dtype=float,
    )

    close = (
        2000.0
        +
        np.sin(
            index
            /
            8.0
        )
        +
        index
        *
        0.01
    )

    frame = pd.DataFrame(
        {
            "open": (
                close
                -
                0.05
            ),

            "high": (
                close
                +
                0.25
            ),

            "low": (
                close
                -
                0.25
            ),

            "close": close,
        }
    )

    engine = (
        CandleSwingIntelligence()
    )

    full = engine.generate(
        frame
    )

    prefix = engine.generate(
        frame.iloc[
            :120
        ].copy()
    )

    feature_columns = [
        column

        for column
        in prefix.columns

        if column.startswith(
            "csi_"
        )
    ]

    for column in feature_columns:

        pd.testing.assert_series_equal(
            full.loc[
                :119,
                column,
            ]
            .reset_index(
                drop=True
            ),

            prefix[
                column
            ]
            .reset_index(
                drop=True
            ),

            check_names=False,
            check_dtype=False,
        )

    assert not any(
        column.startswith(
            "cslabel_"
        )
        for column
        in full.columns
    )

    assert int(
        full[
            "csi_live_safe"
        ].iloc[
            -1
        ]
    ) == 1


def test_research_labels_are_written_to_swing_origin_only() -> None:

    frame = _frame(
        [
            (
                100.0,
                101.0,
                99.0,
                100.0,
            ),

            (
                100.0,
                101.0,
                98.0,
                99.0,
            ),

            (
                99.0,
                100.0,
                98.5,
                99.5,
            ),

            (
                99.5,
                101.0,
                99.0,
                100.5,
            ),
        ]
    )

    frame[
        "swing_id"
    ] = [
        0,
        0,
        0,
        7,
    ]

    frame[
        "swing_type"
    ] = [
        "NONE",
        "NONE",
        "NONE",
        "LOW",
    ]

    frame[
        "swing_price"
    ] = [
        np.nan,
        np.nan,
        np.nan,
        98.0,
    ]

    frame[
        "swing_scale"
    ] = [
        "NONE",
        "NONE",
        "NONE",
        "INTERNAL",
    ]

    frame[
        "swing_origin_index"
    ] = [
        -1,
        -1,
        -1,
        1,
    ]

    frame[
        "swing_confirmation_index"
    ] = [
        -1,
        -1,
        -1,
        3,
    ]

    frame[
        "swing_excursion_atr"
    ] = [
        0.0,
        0.0,
        0.0,
        1.8,
    ]

    frame[
        "swing_reversal_atr"
    ] = [
        0.0,
        0.0,
        0.0,
        0.7,
    ]

    result = (
        CandleSwingIntelligence()
        .generate_research(
            frame
        )
    )

    assert int(
        result.loc[
            1,
            "cslabel_swing_start",
        ]
    ) == 1

    assert (
        result.loc[
            1,
            "cslabel_swing_direction",
        ]
        ==
        "BULLISH"
    )

    assert (
        result.loc[
            1,
            "cslabel_swing_scale",
        ]
        ==
        "INTERNAL"
    )

    assert int(
        result.loc[
            1,
            "cslabel_internal_swing_start",
        ]
    ) == 1

    assert int(
        result.loc[
            1,
            "cslabel_confirmation_index",
        ]
    ) == 3

    assert int(
        result.loc[
            1,
            "cslabel_confirmation_bars",
        ]
    ) == 2

    assert float(
        result.loc[
            1,
            "cslabel_excursion_atr",
        ]
    ) == pytest.approx(
        1.8
    )

    assert int(
        result.loc[
            0,
            "cslabel_swing_start",
        ]
    ) == 0

    assert int(
        result.loc[
            3,
            "cslabel_swing_start",
        ]
    ) == 0


def test_future_confirmation_changes_research_label_but_not_causal_features() -> None:

    base = _frame(
        [
            (
                100.0,
                101.0,
                99.0,
                100.0,
            ),

            (
                100.0,
                101.0,
                98.0,
                99.0,
            ),

            (
                99.0,
                100.0,
                98.5,
                99.5,
            ),
        ]
    )

    for (
        column,
        values,
    ) in {
        "swing_id": [
            0,
            0,
            0,
        ],

        "swing_type": [
            "NONE",
            "NONE",
            "NONE",
        ],

        "swing_price": [
            np.nan,
            np.nan,
            np.nan,
        ],

        "swing_scale": [
            "NONE",
            "NONE",
            "NONE",
        ],

        "swing_origin_index": [
            -1,
            -1,
            -1,
        ],

        "swing_confirmation_index": [
            -1,
            -1,
            -1,
        ],
    }.items():

        base[
            column
        ] = values

    extended = pd.concat(
        [
            base,

            pd.DataFrame(
                [
                    {
                        "open": 99.5,
                        "high": 101.0,
                        "low": 99.0,
                        "close": 100.5,

                        "swing_id": 1,
                        "swing_type": "LOW",
                        "swing_price": 98.0,
                        "swing_scale": "MICRO",

                        "swing_origin_index": 1,
                        "swing_confirmation_index": 3,
                    },
                ]
            ),
        ],
        ignore_index=True,
    )

    engine = (
        CandleSwingIntelligence()
    )

    short_causal = engine.generate(
        base
    )

    long_causal = engine.generate(
        extended
    )

    causal_columns = [
        column

        for column
        in short_causal.columns

        if column.startswith(
            "csi_"
        )
    ]

    for column in causal_columns:

        pd.testing.assert_series_equal(
            short_causal[
                column
            ]
            .reset_index(
                drop=True
            ),

            long_causal.loc[
                :2,
                column,
            ]
            .reset_index(
                drop=True
            ),

            check_names=False,
            check_dtype=False,
        )

    short_research = (
        engine.generate_research(
            base
        )
    )

    long_research = (
        engine.generate_research(
            extended
        )
    )

    assert int(
        short_research.loc[
            1,
            "cslabel_swing_start",
        ]
    ) == 0

    assert int(
        long_research.loc[
            1,
            "cslabel_swing_start",
        ]
    ) == 1