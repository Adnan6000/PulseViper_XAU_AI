"""
Offline tests for ResearchZoneContextOutcomeProfiler v1.0.
"""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pandas as pd
import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Shadow.research_zone_context_outcome"
)

Profiler: Any = (
    module.ResearchZoneContextOutcomeProfiler
)


def _episodes() -> pd.DataFrame:

    times = pd.date_range(
        "2026-08-13 10:00:00+00:00",
        periods=6,
        freq="min",
    )

    return pd.DataFrame(
        {
            "episode_id": [
                f"E{i}"
                for i in range(
                    6
                )
            ],

            "first_signal_time": (
                times
            ),

            "direction": [
                "LONG",
                "LONG",
                "SHORT",
                "SHORT",
                "LONG",
                "SHORT",
            ],

            "first_status": [
                "MATURED_20",
                "MATURED_20",
                "MATURED_20",
                "MATURED_20",
                "MATURED_20",
                "OPEN",
            ],

            "first_confidence_score": [
                72.0,
                60.0,
                76.0,
                55.0,
                88.0,
                80.0,
            ],

            "first_regime_state": [
                "BULLISH_LOW_VOL",
                "RANGE_NORMAL_VOL",
                "BEARISH_LOW_VOL",
                "RANGE_NORMAL_VOL",
                "BULLISH_HIGH_VOL",
                "BEARISH_LOW_VOL",
            ],

            "first_net_5": [
                1.0,
                0.5,
                1.5,
                -1.0,
                -0.5,
                2.0,
            ],

            "first_net_10": [
                2.0,
                1.0,
                2.0,
                -1.5,
                -1.0,
                2.5,
            ],

            "first_net_20": [
                3.0,
                2.0,
                4.0,
                -2.0,
                -1.5,
                3.0,
            ],

            "first_mfe_20": [
                4.0,
                3.0,
                5.0,
                1.0,
                2.0,
                4.0,
            ],

            "first_mae_20": [
                1.0,
                1.5,
                1.0,
                3.0,
                3.0,
                1.0,
            ],

            "first_positive_20": [
                1,
                1,
                1,
                0,
                0,
                1,
            ],
        }
    )


def _pipeline() -> pd.DataFrame:

    times = pd.date_range(
        "2026-08-13 10:00:00+00:00",
        periods=6,
        freq="min",
    )

    return pd.DataFrame(
        {
            "time": times,

            "izctx_active_bullish_count": [
                1,
                1,
                0,
                1,
                1,
                0,
            ],

            "izctx_active_bearish_count": [
                0,
                1,
                1,
                1,
                1,
                1,
            ],

            "izctx_bullish_event_id": [
                "B1",
                "B1",
                "NONE",
                "B2",
                "B3",
                "NONE",
            ],

            "izctx_bullish_state": [
                "FRESH",
                "MITIGATED",
                "NONE",
                "FRESH",
                "ACCEPTED",
                "NONE",
            ],

            # E3 is SHORT.
            # At index 3, bullish is the OPPOSING zone.
            # 0.20 ATR makes it genuinely close so BOTH_CLOSE is expected.
            "izctx_bullish_distance_atr": [
                0.05,
                0.20,
                np.nan,
                0.20,
                0.0,
                np.nan,
            ],

            "izctx_bullish_inside_flag": [
                0,
                0,
                0,
                0,
                1,
                0,
            ],

            "izctx_bullish_overlap_flag": [
                0,
                1,
                0,
                0,
                1,
                0,
            ],

            "izctx_bearish_event_id": [
                "NONE",
                "S1",
                "S2",
                "S3",
                "S4",
                "S5",
            ],

            "izctx_bearish_state": [
                "NONE",
                "FRESH",
                "FRESH",
                "MITIGATED",
                "FRESH",
                "ACCEPTED",
            ],

            "izctx_bearish_distance_atr": [
                np.nan,
                0.70,
                0.04,
                0.15,
                0.30,
                0.0,
            ],

            "izctx_bearish_inside_flag": [
                0,
                0,
                0,
                0,
                0,
                1,
            ],

            "izctx_bearish_overlap_flag": [
                0,
                0,
                0,
                1,
                0,
                1,
            ],

            "izctx_live_safe": [
                1,
            ] * 6,

            "izctx_version": [
                "1.0",
            ] * 6,

            "izctx_mode": [
                "SHADOW_CAUSAL_ZONE_CONTEXT_ONLY",
            ] * 6,

            "research_live_safe": [
                1,
            ] * 6,

            "research_trade_ready_unchanged": [
                1,
            ] * 6,
        }
    )


def test_prepare_keeps_only_matured_episodes() -> None:

    prepared = Profiler.prepare(
        _episodes(),
        _pipeline(),
    )

    assert len(
        prepared
    ) == 5

    assert bool(
        prepared[
            "first_status"
        ]
        .eq(
            "MATURED_20"
        )
        .all()
    )


def test_long_uses_bullish_zone_as_aligned() -> None:

    prepared = Profiler.prepare(
        _episodes(),
        _pipeline(),
    )

    first = prepared.loc[
        prepared[
            "episode_id"
        ].eq(
            "E0"
        )
    ].iloc[
        0
    ]

    assert (
        first[
            "aligned_zone_event_id"
        ]
        ==
        "B1"
    )

    assert (
        first[
            "aligned_zone_state"
        ]
        ==
        "FRESH"
    )

    assert float(
        first[
            "aligned_distance_atr"
        ]
    ) == pytest.approx(
        0.05
    )


def test_short_uses_bearish_zone_as_aligned() -> None:

    prepared = Profiler.prepare(
        _episodes(),
        _pipeline(),
    )

    row = prepared.loc[
        prepared[
            "episode_id"
        ].eq(
            "E2"
        )
    ].iloc[
        0
    ]

    assert (
        row[
            "aligned_zone_event_id"
        ]
        ==
        "S2"
    )

    assert (
        row[
            "aligned_zone_state"
        ]
        ==
        "FRESH"
    )

    assert (
        row[
            "aligned_location"
        ]
        ==
        "VERY_NEAR"
    )


def test_opposing_zone_is_direction_relative() -> None:

    prepared = Profiler.prepare(
        _episodes(),
        _pipeline(),
    )

    row = prepared.loc[
        prepared[
            "episode_id"
        ].eq(
            "E1"
        )
    ].iloc[
        0
    ]

    assert (
        row[
            "opposing_zone_event_id"
        ]
        ==
        "S1"
    )


def test_inside_zone_classification() -> None:

    prepared = Profiler.prepare(
        _episodes(),
        _pipeline(),
    )

    row = prepared.loc[
        prepared[
            "episode_id"
        ].eq(
            "E4"
        )
    ].iloc[
        0
    ]

    assert (
        row[
            "aligned_location"
        ]
        ==
        "INSIDE"
    )

    assert (
        row[
            "aligned_distance_band"
        ]
        ==
        "INSIDE"
    )


def test_zone_relation_detects_aligned_close() -> None:

    prepared = Profiler.prepare(
        _episodes(),
        _pipeline(),
    )

    row = prepared.loc[
        prepared[
            "episode_id"
        ].eq(
            "E0"
        )
    ].iloc[
        0
    ]

    assert (
        row[
            "zone_relation"
        ]
        ==
        "ALIGNED_CLOSE"
    )


def test_zone_relation_detects_both_close() -> None:

    prepared = Profiler.prepare(
        _episodes(),
        _pipeline(),
    )

    row = prepared.loc[
        prepared[
            "episode_id"
        ].eq(
            "E3"
        )
    ].iloc[
        0
    ]

    assert (
        row[
            "zone_relation"
        ]
        ==
        "BOTH_CLOSE"
    )


def test_coverage_reports_signal_time_matching() -> None:

    prepared = Profiler.prepare(
        _episodes(),
        _pipeline(),
    )

    coverage = Profiler.coverage(
        prepared
    )

    row = coverage.iloc[
        0
    ]

    assert int(
        row[
            "episodes"
        ]
    ) == 5

    assert int(
        row[
            "matched_context"
        ]
    ) == 5

    assert float(
        row[
            "matched_pct"
        ]
    ) == pytest.approx(
        100.0
    )


def test_profile_calculates_retrospective_metrics() -> None:

    prepared = Profiler.prepare(
        _episodes(),
        _pipeline(),
    )

    profile = Profiler.profile(
        prepared,
        dimensions=[
            "direction",
        ],
        max_dimension_count=1,
        min_n=1,
    )

    long_row = profile.loc[
        profile[
            "profile_key"
        ].eq(
            "direction=LONG"
        )
    ].iloc[
        0
    ]

    assert int(
        long_row[
            "n"
        ]
    ) == 3

    assert float(
        long_row[
            "net20_med"
        ]
    ) == pytest.approx(
        2.0
    )


def test_profile_can_use_zone_dimensions() -> None:

    prepared = Profiler.prepare(
        _episodes(),
        _pipeline(),
    )

    profile = Profiler.profile(
        prepared,
        dimensions=[
            "aligned_zone_state",
            "zone_relation",
        ],
        max_dimension_count=2,
        min_n=1,
    )

    assert not profile.empty

    assert (
        "aligned_zone_state"
        in set(
            profile[
                "profile_dimensions"
            ]
        )
    )


def test_hindsight_pipeline_columns_are_rejected() -> None:

    pipeline = _pipeline()

    pipeline[
        "izlabel_future_quality"
    ] = 1

    with pytest.raises(
        ValueError,
        match="hindsight",
    ):

        Profiler.prepare(
            _episodes(),
            pipeline,
        )


def test_non_live_safe_pipeline_is_rejected() -> None:

    pipeline = _pipeline()

    pipeline.loc[
        0,
        "izctx_live_safe",
    ] = 0

    with pytest.raises(
        ValueError,
        match="izctx_live_safe",
    ):

        Profiler.prepare(
            _episodes(),
            pipeline,
        )


def test_trade_ready_invariance_failure_is_rejected() -> None:

    pipeline = _pipeline()

    pipeline.loc[
        0,
        "research_trade_ready_unchanged",
    ] = 0

    with pytest.raises(
        ValueError,
        match="research_trade_ready_unchanged",
    ):

        Profiler.prepare(
            _episodes(),
            pipeline,
        )


def test_duplicate_pipeline_times_are_rejected() -> None:

    pipeline = _pipeline()

    pipeline.loc[
        1,
        "time",
    ] = pipeline.loc[
        0,
        "time",
    ]

    with pytest.raises(
        ValueError,
        match="duplicate signal times",
    ):

        Profiler.prepare(
            _episodes(),
            pipeline,
        )


def test_inputs_are_not_mutated() -> None:

    episodes = _episodes()

    pipeline = _pipeline()

    episodes_before = episodes.copy(
        deep=True
    )

    pipeline_before = pipeline.copy(
        deep=True
    )

    _ = Profiler.prepare(
        episodes,
        pipeline,
    )

    pd.testing.assert_frame_equal(
        episodes,
        episodes_before,
    )

    pd.testing.assert_frame_equal(
        pipeline,
        pipeline_before,
    )