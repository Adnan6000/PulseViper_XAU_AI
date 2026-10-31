"""
Offline tests for ResearchOpportunityWeightEngine v1.0.
"""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pandas as pd
import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Shadow.research_opportunity_weight_engine"
)

Engine: Any = (
    module.ResearchOpportunityWeightEngine
)


def _frame() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "trade_ready": [
                0,
                1,
                0,
                0,
                0,
            ],

            "pipeline_version": [
                "TEST",
            ] * 5,

            "pipeline_mode": [
                "TEST_MODE",
            ] * 5,

            "confidence_score": [
                75.0,
                60.0,
                80.0,
                40.0,
                70.0,
            ],

            "confidence_direction": [
                "BULLISH",
                "BEARISH",
                "BEARISH",
                "BULLISH",
                "BULLISH",
            ],

            "setup_state": [
                "TEST",
            ] * 5,

            "bos_direction": [
                "NONE",
            ] * 5,

            "lei_candidate_flag": [
                1,
                1,
                1,
                1,
                0,
            ],

            "lei_direction": [
                "LONG",
                "SHORT",
                "SHORT",
                "LONG",
                "NONE",
            ],

            "lei_entry_family": [
                "BREAK_ACCEPTANCE",
                "BREAK_ACCEPTANCE",
                "FAILED_BREAKOUT",
                "BREAK_ACCEPTANCE",
                "NONE",
            ],

            "lei_reference_source": [
                "INTERNAL_HIGH",
                "INTERNAL_LOW",
                "INTERNAL_HIGH",
                "MAJOR_HIGH",
                "NONE",
            ],

            "lei_confirmation_type": [
                "BREAKOUT_ACCEPTANCE",
                "BREAKOUT_ACCEPTANCE",
                "BEARISH_DISPLACEMENT",
                "BREAKOUT_ACCEPTANCE",
                "NONE",
            ],

            "lei_distance_atr": [
                0.08,
                0.20,
                0.08,
                0.35,
                np.nan,
            ],

            "regime_state": [
                "BULLISH_LOW_VOL",
                "BEARISH_LOW_VOL",
                "RANGE_NORMAL_VOL",
                "BULLISH_HIGH_VOL",
                "RANGE_LOW_VOL",
            ],

            "research_live_safe": [
                1,
            ] * 5,

            "research_trade_ready_unchanged": [
                1,
            ] * 5,
        }
    )


def test_non_candidate_is_inactive() -> None:

    result = Engine.generate(
        _frame()
    )

    row = result.iloc[
        4
    ]

    assert int(
        row[
            "rwei_active"
        ]
    ) == 0

    assert (
        row[
            "rwei_tier"
        ]
        ==
        "NONE"
    )

    assert pd.isna(
        row[
            "rwei_score"
        ]
    )


def test_long_bullish_low_vol_scores_positive() -> None:

    result = Engine.generate(
        _frame()
    )

    row = result.iloc[
        0
    ]

    assert float(
        row[
            "rwei_score"
        ]
    ) > 0.0

    assert (
        "LONG_BULLISH_LOW_VOL"
        in
        str(
            row[
                "rwei_components"
            ]
        )
    )


def test_short_bearish_low_vol_scores_positive() -> None:

    result = Engine.generate(
        _frame()
    )

    row = result.iloc[
        1
    ]

    assert float(
        row[
            "rwei_score"
        ]
    ) > 0.0

    assert (
        "SHORT_BEARISH_LOW_VOL"
        in
        str(
            row[
                "rwei_components"
            ]
        )
    )


def test_short_bearish_displacement_gets_support() -> None:

    result = Engine.generate(
        _frame()
    )

    row = result.iloc[
        2
    ]

    assert (
        "SHORT_BEARISH_DISPLACEMENT"
        in
        str(
            row[
                "rwei_components"
            ]
        )
    )

    assert float(
        row[
            "rwei_positive_points"
        ]
    ) > 1.0


def test_long_bullish_high_vol_is_negative() -> None:

    result = Engine.generate(
        _frame()
    )

    row = result.iloc[
        3
    ]

    assert float(
        row[
            "rwei_score"
        ]
    ) < 0.0

    assert (
        row[
            "rwei_tier"
        ]
        ==
        "D"
    )


def test_long_70_84_near_level_interaction() -> None:

    result = Engine.generate(
        _frame()
    )

    row = result.iloc[
        0
    ]

    assert (
        "LONG_70_84_NEAR_LEVEL"
        in
        str(
            row[
                "rwei_components"
            ]
        )
    )


def test_reference_internal_receives_positive_evidence() -> None:

    result = Engine.generate(
        _frame()
    )

    row = result.iloc[
        0
    ]

    assert (
        "REFERENCE_INTERNAL"
        in
        str(
            row[
                "rwei_components"
            ]
        )
    )


def test_trade_ready_is_unchanged() -> None:

    frame = _frame()

    before = frame[
        "trade_ready"
    ].copy()

    result = Engine.generate(
        frame
    )

    pd.testing.assert_series_equal(
        before,
        result[
            "trade_ready"
        ],
    )


def test_protected_families_are_unchanged() -> None:

    frame = _frame()

    result = Engine.generate(
        frame
    )

    for column in (
        "confidence_score",
        "confidence_direction",
        "setup_state",
        "bos_direction",
    ):

        pd.testing.assert_series_equal(
            frame[
                column
            ],
            result[
                column
            ],
        )


def test_input_frame_is_not_mutated() -> None:

    frame = _frame()

    original = frame.copy(
        deep=True
    )

    _ = Engine.generate(
        frame
    )

    pd.testing.assert_frame_equal(
        frame,
        original,
    )


def test_rejects_hindsight_columns() -> None:

    frame = _frame()

    frame[
        "cslabel_future_direction"
    ] = "BULLISH"

    with pytest.raises(
        ValueError,
        match="cslabel",
    ):

        Engine.generate(
            frame
        )


def test_rejects_non_live_safe_research() -> None:

    frame = _frame()

    frame.loc[
        0,
        "research_live_safe",
    ] = 0

    with pytest.raises(
        ValueError,
        match="research_live_safe",
    ):

        Engine.generate(
            frame
        )


def test_rerun_is_deterministic() -> None:

    first = Engine.generate(
        _frame()
    )

    second = Engine.generate(
        first
    )

    columns = [
        column
        for column in first.columns
        if column.startswith(
            "rwei_"
        )
    ]

    pd.testing.assert_frame_equal(
        first[
            columns
        ],
        second[
            columns
        ],
    )