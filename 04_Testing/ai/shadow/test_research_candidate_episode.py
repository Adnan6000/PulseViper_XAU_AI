"""
Offline tests for ResearchCandidateEpisodeAnalyzer v1.0.
"""

from __future__ import annotations

import importlib
from typing import Any

import pandas as pd
import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Shadow.research_candidate_episode"
)

ResearchCandidateEpisodeAnalyzer: Any = (
    module.ResearchCandidateEpisodeAnalyzer
)


def _ledger() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "event_id": [
                "A1",
                "A2",
                "A3",
                "B1",
                "B2",
                "C1",
            ],

            "signal_time": pd.to_datetime(
                [
                    "2026-08-13 07:00:00+00:00",
                    "2026-08-13 07:01:00+00:00",
                    "2026-08-13 07:03:00+00:00",

                    "2026-08-13 07:04:00+00:00",
                    "2026-08-13 07:05:00+00:00",

                    "2026-08-13 07:20:00+00:00",
                ]
            ),

            "direction": [
                "SHORT",
                "SHORT",
                "SHORT",
                "SHORT",
                "SHORT",
                "LONG",
            ],

            "lei_entry_family": [
                "BREAK_ACCEPTANCE",
                "BREAK_ACCEPTANCE",
                "BREAK_ACCEPTANCE",

                "FAILED_BREAKOUT",
                "FAILED_BREAKOUT",

                "BREAK_ACCEPTANCE",
            ],

            "liqintel_event_interpretation": [
                "DOWNSIDE_BREAKOUT_ACCEPTED",
                "DOWNSIDE_BREAKOUT_ACCEPTED",
                "DOWNSIDE_BREAKOUT_ACCEPTED",

                "FAILED_UPSIDE_BREAKOUT",
                "FAILED_UPSIDE_BREAKOUT",

                "UPSIDE_BREAKOUT_ACCEPTED",
            ],

            "lei_reference_source": [
                "MICRO_LOW",
                "MICRO_LOW",
                "MICRO_LOW",

                "MICRO_HIGH",
                "MICRO_HIGH",

                "INTERNAL_HIGH",
            ],

            "lei_confirmation_type": [
                "BREAKOUT_ACCEPTANCE",
                "BREAKOUT_ACCEPTANCE",
                "BREAKOUT_ACCEPTANCE",

                "INTERNAL_BOS",
                "INTERNAL_BOS",

                "BREAKOUT_ACCEPTANCE",
            ],

            "entry_close": [
                100.0,
                99.8,
                99.5,
                99.1,
                99.0,
                101.0,
            ],

            "lei_reference_price": [
                100.2,
                100.0,
                99.7,
                99.4,
                99.3,
                100.8,
            ],

            "lei_distance_atr": [
                0.10,
                0.12,
                0.11,
                0.20,
                0.18,
                0.08,
            ],

            "confidence_score": [
                72.0,
                75.0,
                77.0,
                60.0,
                61.0,
                80.0,
            ],

            "production_ready_overlap": [
                0,
                0,
                1,
                0,
                0,
                1,
            ],

            "mdc_state": [
                "SHORT_WATCH",
                "SHORT_WATCH",
                "SHORT_WATCH",
                "SHORT_WATCH",
                "SHORT_WATCH",
                "LONG_WATCH",
            ],

            "regime_state": [
                "TREND",
                "TREND",
                "TREND",
                "TREND",
                "TREND",
                "TREND",
            ],

            "status": [
                "MATURED_20",
                "MATURED_20",
                "MATURED_20",
                "MATURED_20",
                "MATURED_20",
                "MATURED_20",
            ],

            "net_5": [
                1.0,
                0.5,
                -0.2,
                -1.0,
                -0.5,
                2.0,
            ],

            "net_10": [
                1.5,
                0.8,
                0.1,
                -1.2,
                -0.4,
                2.5,
            ],

            "net_20": [
                2.0,
                1.0,
                -0.5,
                -2.0,
                -1.0,
                3.0,
            ],

            "mfe_20": [
                4.0,
                3.0,
                2.0,
                2.0,
                2.5,
                5.0,
            ],

            "mae_20": [
                1.0,
                1.5,
                2.0,
                4.0,
                3.0,
                1.0,
            ],

            "positive_20": [
                1,
                1,
                0,
                0,
                0,
                1,
            ],

            "fp_1_result": [
                "PROFIT_FIRST",
                "PROFIT_FIRST",
                "LOSS_FIRST",
                "LOSS_FIRST",
                "LOSS_FIRST",
                "PROFIT_FIRST",
            ],

            "fp_2_result": [
                "PROFIT_FIRST",
                "NEITHER",
                "LOSS_FIRST",
                "LOSS_FIRST",
                "LOSS_FIRST",
                "PROFIT_FIRST",
            ],

            "fp_3_result": [
                "NEITHER",
                "NEITHER",
                "NEITHER",
                "LOSS_FIRST",
                "NEITHER",
                "PROFIT_FIRST",
            ],

            "fp_5_result": [
                "NEITHER",
                "NEITHER",
                "NEITHER",
                "NEITHER",
                "NEITHER",
                "PROFIT_FIRST",
            ],
        }
    )


def test_build_compresses_candidate_streaks() -> None:

    episodes = (
        ResearchCandidateEpisodeAnalyzer
        .build(
            _ledger()
        )
    )

    assert len(
        episodes
    ) == 3

    assert list(
        episodes[
            "candidate_count"
        ]
    ) == [
        3,
        2,
        1,
    ]


def test_episode_uses_first_candidate_as_entry_observation() -> None:

    episodes = (
        ResearchCandidateEpisodeAnalyzer
        .build(
            _ledger()
        )
    )

    first = episodes.iloc[
        0
    ]

    assert (
        first[
            "first_event_id"
        ]
        ==
        "A1"
    )

    assert float(
        first[
            "first_entry_close"
        ]
    ) == pytest.approx(
        100.0
    )

    assert float(
        first[
            "first_net_20"
        ]
    ) == pytest.approx(
        2.0
    )


def test_production_overlap_any_is_preserved() -> None:

    episodes = (
        ResearchCandidateEpisodeAnalyzer
        .build(
            _ledger()
        )
    )

    first = episodes.iloc[
        0
    ]

    assert int(
        first[
            "first_production_ready_overlap"
        ]
    ) == 0

    assert int(
        first[
            "any_production_ready_overlap"
        ]
    ) == 1


def test_family_change_starts_new_episode() -> None:

    episodes = (
        ResearchCandidateEpisodeAnalyzer
        .build(
            _ledger()
        )
    )

    assert (
        episodes.iloc[
            0
        ][
            "lei_entry_family"
        ]
        ==
        "BREAK_ACCEPTANCE"
    )

    assert (
        episodes.iloc[
            1
        ][
            "lei_entry_family"
        ]
        ==
        "FAILED_BREAKOUT"
    )


def test_large_time_gap_starts_new_episode() -> None:

    frame = _ledger().iloc[
        :3
    ].copy()

    frame.loc[
        2,
        "signal_time",
    ] = pd.Timestamp(
        "2026-08-13 07:10:00+00:00"
    )

    episodes = (
        ResearchCandidateEpisodeAnalyzer
        .build(
            frame
        )
    )

    assert len(
        episodes
    ) == 2


def test_reference_source_change_starts_new_episode() -> None:

    frame = _ledger().iloc[
        :3
    ].copy()

    frame.loc[
        1,
        "lei_reference_source",
    ] = "MAJOR_LOW"

    episodes = (
        ResearchCandidateEpisodeAnalyzer
        .build(
            frame
        )
    )

    assert len(
        episodes
    ) == 3


def test_confirmation_change_starts_new_episode() -> None:

    frame = _ledger().iloc[
        :3
    ].copy()

    frame.loc[
        1,
        "lei_confirmation_type",
    ] = "INTERNAL_BOS"

    episodes = (
        ResearchCandidateEpisodeAnalyzer
        .build(
            frame
        )
    )

    assert len(
        episodes
    ) == 3


def test_compression_summary_is_correct() -> None:

    ledger = _ledger()

    episodes = (
        ResearchCandidateEpisodeAnalyzer
        .build(
            ledger
        )
    )

    summary = (
        ResearchCandidateEpisodeAnalyzer
        .compression_summary(
            ledger,
            episodes,
        )
    )

    row = summary.iloc[
        0
    ]

    assert int(
        row[
            "raw_candidates"
        ]
    ) == 6

    assert int(
        row[
            "episodes"
        ]
    ) == 3

    assert int(
        row[
            "repeated_candidates"
        ]
    ) == 3

    assert float(
        row[
            "compression_pct"
        ]
    ) == pytest.approx(
        50.0
    )


def test_performance_dashboard_uses_episode_firsts() -> None:

    episodes = (
        ResearchCandidateEpisodeAnalyzer
        .build(
            _ledger()
        )
    )

    dashboard = (
        ResearchCandidateEpisodeAnalyzer
        .performance_dashboard(
            episodes
        )
    )

    all_row = dashboard.loc[
        dashboard[
            "group"
        ].eq(
            "ALL_EPISODES"
        )
    ].iloc[
        0
    ]

    assert int(
        all_row[
            "n"
        ]
    ) == 3

    assert float(
        all_row[
            "net20_med"
        ]
    ) == pytest.approx(
        2.0
    )


def test_confidence_dashboard_counts_all_matured_episodes() -> None:

    episodes = (
        ResearchCandidateEpisodeAnalyzer
        .build(
            _ledger()
        )
    )

    dashboard = (
        ResearchCandidateEpisodeAnalyzer
        .confidence_dashboard(
            episodes
        )
    )

    assert int(
        dashboard[
            "n"
        ].sum()
    ) == 3


def test_invalid_gap_rejected() -> None:

    with pytest.raises(
        ValueError,
        match="max_gap_minutes",
    ):

        ResearchCandidateEpisodeAnalyzer.build(
            _ledger(),
            max_gap_minutes=0,
        )