"""
Deterministic offline tests for LevelEntryIntelligence v1.0.

Contracts:
- LONG_WATCH alone is NOT an entry
- conflict blocks entry
- sweep/reclaim + confirmation can create LONG candidate
- bearish event can create SHORT candidate
- event level has priority over nearest generic liquidity
- far-away level blocks entry
- missing confirmation blocks entry
- prefix invariance / no future leakage
"""

from __future__ import annotations

import importlib
from typing import Any

import pandas as pd
import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Core.level_entry_intelligence"
)

LevelEntryIntelligence: Any = (
    module.LevelEntryIntelligence
)


def _base(
    rows: int,
) -> pd.DataFrame:

    return pd.DataFrame(
        {
            "close": [
                2000.0
                for _
                in range(
                    rows
                )
            ],

            "atr": [
                2.0
                for _
                in range(
                    rows
                )
            ],

            "mdc_state": [
                "NEUTRAL"
                for _
                in range(
                    rows
                )
            ],

            "mdc_direction": [
                "NEUTRAL"
                for _
                in range(
                    rows
                )
            ],

            "liq_event_type": [
                "NONE"
                for _
                in range(
                    rows
                )
            ],

            "liq_event_source": [
                "NONE"
                for _
                in range(
                    rows
                )
            ],

            "liq_event_side": [
                "NONE"
                for _
                in range(
                    rows
                )
            ],

            "liq_event_price": [
                float(
                    "nan"
                )
                for _
                in range(
                    rows
                )
            ],

            "liq_nearest_above_price": [
                2000.5
                for _
                in range(
                    rows
                )
            ],

            "liq_nearest_above_source": [
                "INTERNAL_HIGH"
                for _
                in range(
                    rows
                )
            ],

            "liq_nearest_above_state": [
                "UNTOUCHED"
                for _
                in range(
                    rows
                )
            ],

            "liq_nearest_below_price": [
                1999.5
                for _
                in range(
                    rows
                )
            ],

            "liq_nearest_below_source": [
                "INTERNAL_LOW"
                for _
                in range(
                    rows
                )
            ],

            "liq_nearest_below_state": [
                "UNTOUCHED"
                for _
                in range(
                    rows
                )
            ],

            "liqintel_event_interpretation": [
                "NONE"
                for _
                in range(
                    rows
                )
            ],

            "liqintel_event_bias": [
                "NEUTRAL"
                for _
                in range(
                    rows
                )
            ],

            "liqintel_trap_flag": [
                0
                for _
                in range(
                    rows
                )
            ],

            "liqintel_failed_breakout_flag": [
                0
                for _
                in range(
                    rows
                )
            ],

            "liqintel_breakout_accepted_flag": [
                0
                for _
                in range(
                    rows
                )
            ],

            "csi_bullish_liquidity_rejection_flag": [
                0
                for _
                in range(
                    rows
                )
            ],

            "csi_bearish_liquidity_rejection_flag": [
                0
                for _
                in range(
                    rows
                )
            ],

            "csi_bullish_displacement_flag": [
                0
                for _
                in range(
                    rows
                )
            ],

            "csi_bearish_displacement_flag": [
                0
                for _
                in range(
                    rows
                )
            ],

            "csi_bullish_engulfing_flag": [
                0
                for _
                in range(
                    rows
                )
            ],

            "csi_bearish_engulfing_flag": [
                0
                for _
                in range(
                    rows
                )
            ],

            "bos_direction": [
                "NONE"
                for _
                in range(
                    rows
                )
            ],

            "micro_bos": [
                0
                for _
                in range(
                    rows
                )
            ],

            "internal_bos": [
                0
                for _
                in range(
                    rows
                )
            ],

            "major_bos": [
                0
                for _
                in range(
                    rows
                )
            ],
        }
    )


def test_long_watch_alone_is_not_entry() -> None:

    frame = _base(
        1
    )

    frame.loc[
        0,
        "mdc_state",
    ] = "LONG_WATCH"

    frame.loc[
        0,
        "mdc_direction",
    ] = "BULLISH"

    result = (
        LevelEntryIntelligence()
        .generate(
            frame
        )
    )

    assert int(
        result.loc[
            0,
            "lei_candidate_flag",
        ]
    ) == 0

    assert (
        result.loc[
            0,
            "lei_status",
        ]
        ==
        "WAIT_TRIGGER"
    )


def test_conflict_blocks_entry() -> None:

    frame = _base(
        1
    )

    frame.loc[
        0,
        "mdc_state",
    ] = "WAIT_CONFLICT"

    frame.loc[
        0,
        "mdc_direction",
    ] = "BULLISH"

    frame.loc[
        0,
        "liqintel_trap_flag",
    ] = 1

    result = (
        LevelEntryIntelligence()
        .generate(
            frame
        )
    )

    assert int(
        result.loc[
            0,
            "lei_candidate_flag",
        ]
    ) == 0

    assert (
        result.loc[
            0,
            "lei_status",
        ]
        ==
        "WAIT_CONFLICT"
    )


def test_bullish_sweep_reclaim_can_create_long_candidate() -> None:

    frame = _base(
        1
    )

    frame.loc[
        0,
        "mdc_state",
    ] = "LONG_WATCH"

    frame.loc[
        0,
        "mdc_direction",
    ] = "BULLISH"

    frame.loc[
        0,
        "liq_event_type",
    ] = "SWEPT"

    frame.loc[
        0,
        "liq_event_source",
    ] = "PDL"

    frame.loc[
        0,
        "liq_event_side",
    ] = "LOW"

    frame.loc[
        0,
        "liq_event_price",
    ] = 1999.6

    frame.loc[
        0,
        "liqintel_event_interpretation",
    ] = "SELL_SIDE_SWEEP_TRAP"

    frame.loc[
        0,
        "liqintel_event_bias",
    ] = "BULLISH"

    frame.loc[
        0,
        "liqintel_trap_flag",
    ] = 1

    frame.loc[
        0,
        "bos_direction",
    ] = "BULLISH"

    frame.loc[
        0,
        "internal_bos",
    ] = 1

    result = (
        LevelEntryIntelligence()
        .generate(
            frame
        )
    )

    assert int(
        result.loc[
            0,
            "lei_candidate_flag",
        ]
    ) == 1

    assert (
        result.loc[
            0,
            "lei_status",
        ]
        ==
        "LONG_CANDIDATE"
    )

    assert (
        result.loc[
            0,
            "lei_entry_family",
        ]
        ==
        "SWEEP_RECLAIM"
    )

    assert (
        result.loc[
            0,
            "lei_reference_source",
        ]
        ==
        "PDL"
    )

    assert (
        result.loc[
            0,
            "lei_level_class",
        ]
        ==
        "EXTERNAL"
    )

    assert float(
        result.loc[
            0,
            "lei_invalidation_price",
        ]
    ) < 1999.6


def test_bearish_failed_breakout_can_create_short_candidate() -> None:

    frame = _base(
        1
    )

    frame.loc[
        0,
        "mdc_state",
    ] = "SHORT_WATCH"

    frame.loc[
        0,
        "mdc_direction",
    ] = "BEARISH"

    frame.loc[
        0,
        "liq_event_type",
    ] = "RECLAIMED"

    frame.loc[
        0,
        "liq_event_source",
    ] = "PDH"

    frame.loc[
        0,
        "liq_event_side",
    ] = "HIGH"

    frame.loc[
        0,
        "liq_event_price",
    ] = 2000.4

    frame.loc[
        0,
        "liqintel_event_interpretation",
    ] = "FAILED_UPSIDE_BREAKOUT"

    frame.loc[
        0,
        "liqintel_event_bias",
    ] = "BEARISH"

    frame.loc[
        0,
        "liqintel_failed_breakout_flag",
    ] = 1

    frame.loc[
        0,
        "csi_bearish_displacement_flag",
    ] = 1

    result = (
        LevelEntryIntelligence()
        .generate(
            frame
        )
    )

    assert int(
        result.loc[
            0,
            "lei_candidate_flag",
        ]
    ) == 1

    assert (
        result.loc[
            0,
            "lei_status",
        ]
        ==
        "SHORT_CANDIDATE"
    )

    assert (
        result.loc[
            0,
            "lei_entry_family",
        ]
        ==
        "FAILED_BREAKOUT"
    )

    assert float(
        result.loc[
            0,
            "lei_invalidation_price",
        ]
    ) > 2000.4


def test_event_level_has_priority_over_nearest_generic_level() -> None:

    frame = _base(
        1
    )

    frame.loc[
        0,
        "mdc_state",
    ] = "LONG_WATCH"

    frame.loc[
        0,
        "mdc_direction",
    ] = "BULLISH"

    frame.loc[
        0,
        "liq_nearest_below_price",
    ] = 1999.9

    frame.loc[
        0,
        "liq_nearest_below_source",
    ] = "MICRO_LOW"

    frame.loc[
        0,
        "liq_event_price",
    ] = 1999.5

    frame.loc[
        0,
        "liq_event_source",
    ] = "PDL"

    frame.loc[
        0,
        "liq_event_side",
    ] = "LOW"

    frame.loc[
        0,
        "liq_event_type",
    ] = "SWEPT"

    frame.loc[
        0,
        "liqintel_event_bias",
    ] = "BULLISH"

    frame.loc[
        0,
        "liqintel_trap_flag",
    ] = 1

    frame.loc[
        0,
        "csi_bullish_displacement_flag",
    ] = 1

    result = (
        LevelEntryIntelligence()
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            0,
            "lei_reference_origin",
        ]
        ==
        "EVENT_LEVEL"
    )

    assert (
        result.loc[
            0,
            "lei_reference_source",
        ]
        ==
        "PDL"
    )

    assert float(
        result.loc[
            0,
            "lei_reference_price",
        ]
    ) == pytest.approx(
        1999.5
    )


def test_far_level_blocks_entry() -> None:

    frame = _base(
        1
    )

    frame.loc[
        0,
        "mdc_state",
    ] = "LONG_WATCH"

    frame.loc[
        0,
        "mdc_direction",
    ] = "BULLISH"

    frame.loc[
        0,
        "liq_nearest_below_price",
    ] = 1990.0

    frame.loc[
        0,
        "csi_bullish_displacement_flag",
    ] = 1

    result = (
        LevelEntryIntelligence(
            max_entry_distance_atr=0.35,
        )
        .generate(
            frame
        )
    )

    assert int(
        result.loc[
            0,
            "lei_candidate_flag",
        ]
    ) == 0

    assert (
        result.loc[
            0,
            "lei_status",
        ]
        ==
        "WAIT_LOCATION"
    )


def test_trigger_without_confirmation_waits() -> None:

    frame = _base(
        1
    )

    frame.loc[
        0,
        "mdc_state",
    ] = "LONG_WATCH"

    frame.loc[
        0,
        "mdc_direction",
    ] = "BULLISH"

    frame.loc[
        0,
        "csi_bullish_engulfing_flag",
    ] = 1

    result = (
        LevelEntryIntelligence()
        .generate(
            frame
        )
    )

    assert int(
        result.loc[
            0,
            "lei_candidate_flag",
        ]
    ) == 0

    assert (
        result.loc[
            0,
            "lei_status",
        ]
        ==
        "WAIT_CONFIRMATION"
    )


def test_prefix_invariance_proves_no_future_leakage() -> None:

    frame = _base(
        20
    )

    for i in range(
        20
    ):

        if i < 10:

            frame.loc[
                i,
                "mdc_state",
            ] = "LONG_WATCH"

            frame.loc[
                i,
                "mdc_direction",
            ] = "BULLISH"

            frame.loc[
                i,
                "csi_bullish_displacement_flag",
            ] = 1

        else:

            frame.loc[
                i,
                "mdc_state",
            ] = "SHORT_WATCH"

            frame.loc[
                i,
                "mdc_direction",
            ] = "BEARISH"

            frame.loc[
                i,
                "csi_bearish_displacement_flag",
            ] = 1

    engine = (
        LevelEntryIntelligence()
    )

    full = engine.generate(
        frame
    )

    prefix = engine.generate(
        frame.iloc[
            :12
        ].copy()
    )

    columns = [
        column

        for column
        in prefix.columns

        if column.startswith(
            "lei_"
        )
    ]

    for column in columns:

        pd.testing.assert_series_equal(
            full.loc[
                :11,
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