"""
Deterministic offline tests for MarketDecisionClarity v1.0.

Contracts:
- clear bullish evidence => LONG_WATCH
- clear bearish evidence => SHORT_WATCH
- balanced conflict => WAIT_CONFLICT
- one opposite candle does not immediately flip stable direction
- repeated strong opposite evidence can confirm a flip
- weak MICRO disagreement does not override stronger context
- prefix invariance / no future leakage
"""

from __future__ import annotations

import importlib
from typing import Any

import pandas as pd
import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Core.market_decision_clarity"
)

MarketDecisionClarity: Any = (
    module.MarketDecisionClarity
)


def _base(
    rows: int,
) -> pd.DataFrame:

    return pd.DataFrame(
        {
            "close": [
                2000.0
                +
                i
                for i
                in range(
                    rows
                )
            ],

            "structure_bias": [
                "NEUTRAL"
            ]
            *
            rows,

            "bos_direction": [
                "NONE"
            ]
            *
            rows,

            "major_bos": [
                0
            ]
            *
            rows,

            "internal_bos": [
                0
            ]
            *
            rows,

            "micro_bos": [
                0
            ]
            *
            rows,

            "liqintel_event_bias": [
                "NEUTRAL"
            ]
            *
            rows,

            "liqintel_trap_flag": [
                0
            ]
            *
            rows,

            "liqintel_failed_breakout_flag": [
                0
            ]
            *
            rows,

            "liqintel_breakout_accepted_flag": [
                0
            ]
            *
            rows,

            "liqintel_breakout_attempt_flag": [
                0
            ]
            *
            rows,

            "csi_bullish_liquidity_rejection_flag": [
                0
            ]
            *
            rows,

            "csi_bearish_liquidity_rejection_flag": [
                0
            ]
            *
            rows,

            "csi_bullish_displacement_flag": [
                0
            ]
            *
            rows,

            "csi_bearish_displacement_flag": [
                0
            ]
            *
            rows,

            "csi_bullish_engulfing_flag": [
                0
            ]
            *
            rows,

            "csi_bearish_engulfing_flag": [
                0
            ]
            *
            rows,

            "csi_bullish_rejection_flag": [
                0
            ]
            *
            rows,

            "csi_bearish_rejection_flag": [
                0
            ]
            *
            rows,
        }
    )


def test_clear_bullish_evidence_produces_long_watch() -> None:

    frame = _base(
        1
    )

    frame.loc[
        0,
        "structure_bias",
    ] = "BULLISH"

    frame.loc[
        0,
        "bos_direction",
    ] = "BULLISH"

    frame.loc[
        0,
        "internal_bos",
    ] = 1

    result = (
        MarketDecisionClarity()
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            0,
            "mdc_state",
        ]
        ==
        "LONG_WATCH"
    )

    assert (
        result.loc[
            0,
            "mdc_direction",
        ]
        ==
        "BULLISH"
    )


def test_clear_bearish_evidence_produces_short_watch() -> None:

    frame = _base(
        1
    )

    frame.loc[
        0,
        "structure_bias",
    ] = "BEARISH"

    frame.loc[
        0,
        "liqintel_event_bias",
    ] = "BEARISH"

    frame.loc[
        0,
        "liqintel_failed_breakout_flag",
    ] = 1

    result = (
        MarketDecisionClarity()
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            0,
            "mdc_state",
        ]
        ==
        "SHORT_WATCH"
    )

    assert (
        result.loc[
            0,
            "mdc_direction",
        ]
        ==
        "BEARISH"
    )


def test_balanced_opposing_evidence_waits_for_conflict_resolution() -> None:

    frame = _base(
        1
    )

    frame.loc[
        0,
        "structure_bias",
    ] = "BULLISH"

    frame.loc[
        0,
        "liqintel_event_bias",
    ] = "BEARISH"

    frame.loc[
        0,
        "liqintel_trap_flag",
    ] = 1

    result = (
        MarketDecisionClarity()
        .generate(
            frame
        )
    )

    assert int(
        result.loc[
            0,
            "mdc_conflict_flag",
        ]
    ) == 1

    assert (
        result.loc[
            0,
            "mdc_state",
        ]
        ==
        "WAIT_CONFLICT"
    )


def test_one_opposite_strong_bar_does_not_immediately_flip() -> None:

    frame = _base(
        2
    )

    frame.loc[
        0,
        "structure_bias",
    ] = "BULLISH"

    frame.loc[
        0,
        "bos_direction",
    ] = "BULLISH"

    frame.loc[
        0,
        "internal_bos",
    ] = 1

    frame.loc[
        1,
        "structure_bias",
    ] = "BEARISH"

    frame.loc[
        1,
        "bos_direction",
    ] = "BEARISH"

    frame.loc[
        1,
        "internal_bos",
    ] = 1

    result = (
        MarketDecisionClarity(
            flip_confirmations=2,
        )
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            0,
            "mdc_direction",
        ]
        ==
        "BULLISH"
    )

    assert (
        result.loc[
            1,
            "mdc_direction",
        ]
        ==
        "BULLISH"
    )

    assert (
        result.loc[
            1,
            "mdc_state",
        ]
        ==
        "HOLD_BULLISH"
    )

    assert int(
        result.loc[
            1,
            "mdc_flip_pending",
        ]
    ) == 1


def test_repeated_strong_opposite_evidence_confirms_flip() -> None:

    frame = _base(
        3
    )

    frame.loc[
        0,
        "structure_bias",
    ] = "BULLISH"

    frame.loc[
        0,
        "bos_direction",
    ] = "BULLISH"

    frame.loc[
        0,
        "internal_bos",
    ] = 1

    for index in (
        1,
        2,
    ):

        frame.loc[
            index,
            "structure_bias",
        ] = "BEARISH"

        frame.loc[
            index,
            "bos_direction",
        ] = "BEARISH"

        frame.loc[
            index,
            "internal_bos",
        ] = 1

    result = (
        MarketDecisionClarity(
            flip_confirmations=2,
        )
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            1,
            "mdc_direction",
        ]
        ==
        "BULLISH"
    )

    assert (
        result.loc[
            2,
            "mdc_direction",
        ]
        ==
        "BEARISH"
    )

    assert (
        result.loc[
            2,
            "mdc_state",
        ]
        ==
        "SHORT_WATCH"
    )


def test_weak_micro_disagreement_does_not_override_internal_structure() -> None:

    frame = _base(
        2
    )

    frame.loc[
        0,
        "structure_bias",
    ] = "BULLISH"

    frame.loc[
        0,
        "bos_direction",
    ] = "BULLISH"

    frame.loc[
        0,
        "internal_bos",
    ] = 1

    frame.loc[
        1,
        "bos_direction",
    ] = "BEARISH"

    frame.loc[
        1,
        "micro_bos",
    ] = 1

    result = (
        MarketDecisionClarity()
        .generate(
            frame
        )
    )

    assert (
        result.loc[
            1,
            "mdc_direction",
        ]
        ==
        "BULLISH"
    )

    assert (
        result.loc[
            1,
            "mdc_state",
        ]
        in {
            "HOLD_BULLISH",
            "WAIT_WEAK",
        }
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
                "structure_bias",
            ] = "BULLISH"

            if i % 3 == 0:

                frame.loc[
                    i,
                    "bos_direction",
                ] = "BULLISH"

                frame.loc[
                    i,
                    "micro_bos",
                ] = 1

        else:

            frame.loc[
                i,
                "structure_bias",
            ] = "BEARISH"

            if i % 3 == 0:

                frame.loc[
                    i,
                    "bos_direction",
                ] = "BEARISH"

                frame.loc[
                    i,
                    "micro_bos",
                ] = 1

    engine = (
        MarketDecisionClarity()
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
            "mdc_"
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