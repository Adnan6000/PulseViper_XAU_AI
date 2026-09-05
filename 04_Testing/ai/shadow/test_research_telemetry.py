"""
Deterministic offline tests for ResearchTelemetryObserver v1.0.
"""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pandas as pd
import pytest


pytestmark = pytest.mark.offline


telemetry_module: Any = importlib.import_module(
    "02_AI.Shadow.research_telemetry"
)

ResearchTelemetryObserver: Any = (
    telemetry_module.ResearchTelemetryObserver
)


def _telemetry_frame() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "time": pd.date_range(
                "2026-08-13 00:00:00+00:00",
                periods=8,
                freq="min",
            ),

            "close": [
                2400.0,
                2400.4,
                2400.6,
                2400.8,
                2400.5,
                2400.2,
                2399.9,
                2399.7,
            ],

            "trade_ready": [
                0,
                1,
                0,
                1,
                0,
                0,
                1,
                0,
            ],

            "confidence_direction": [
                "NEUTRAL",
                "BULLISH",
                "BULLISH",
                "BULLISH",
                "BEARISH",
                "NEUTRAL",
                "BEARISH",
                "BEARISH",
            ],

            "confidence_score": [
                0.0,
                82.0,
                55.0,
                78.0,
                66.0,
                20.0,
                74.0,
                62.0,
            ],

            "mdc_state": [
                "NEUTRAL",
                "LONG_WATCH",
                "LONG_WATCH",
                "HOLD_BULLISH",
                "SHORT_WATCH",
                "WAIT_CONFLICT",
                "HOLD_BEARISH",
                "SHORT_WATCH",
            ],

            "mdc_direction": [
                "NEUTRAL",
                "BULLISH",
                "BULLISH",
                "BULLISH",
                "BEARISH",
                "NEUTRAL",
                "BEARISH",
                "BEARISH",
            ],

            "mdc_bullish_score": [
                0.0,
                5.0,
                4.0,
                4.0,
                1.0,
                3.0,
                1.0,
                0.0,
            ],

            "mdc_bearish_score": [
                0.0,
                1.0,
                1.0,
                1.0,
                5.0,
                3.0,
                4.0,
                5.0,
            ],

            "mdc_score_spread": [
                0.0,
                4.0,
                3.0,
                3.0,
                -4.0,
                0.0,
                -3.0,
                -5.0,
            ],

            "mdc_conflict_flag": [
                0,
                0,
                0,
                0,
                0,
                1,
                0,
                0,
            ],

            "lei_status": [
                "NO_DIRECTION",
                "LONG_CANDIDATE",
                "WAIT_CONFIRMATION",
                "LONG_CANDIDATE",
                "SHORT_CANDIDATE",
                "WAIT_CONFLICT",
                "WAIT_TRIGGER",
                "WAIT_LOCATION",
            ],

            "lei_direction": [
                "NONE",
                "LONG",
                "LONG",
                "LONG",
                "SHORT",
                "NONE",
                "SHORT",
                "SHORT",
            ],

            "lei_entry_family": [
                "NONE",
                "SWEEP_RECLAIM",
                "STRUCTURE_CONTINUATION",
                "BREAK_ACCEPTANCE",
                "FAILED_BREAKOUT",
                "NONE",
                "GENERIC_CONTEXT_CONFIRMATION",
                "RANGE_EDGE_REJECTION",
            ],

            "lei_reference_price": [
                np.nan,
                2400.1,
                2400.2,
                2400.7,
                2400.7,
                np.nan,
                2400.1,
                2400.0,
            ],

            "lei_reference_source": [
                "NONE",
                "PDL",
                "MICRO_LOW",
                "PDH",
                "PWH",
                "NONE",
                "INTERNAL_HIGH",
                "PREV_ASIA_HIGH",
            ],

            "lei_reference_origin": [
                "NONE",
                "EVENT_LEVEL",
                "NEAREST_LEVEL",
                "EVENT_LEVEL",
                "EVENT_LEVEL",
                "NONE",
                "NEAREST_LEVEL",
                "NEAREST_LEVEL",
            ],

            "lei_level_class": [
                "UNKNOWN",
                "EXTERNAL",
                "INTERNAL",
                "EXTERNAL",
                "EXTERNAL",
                "UNKNOWN",
                "INTERNAL",
                "EXTERNAL",
            ],

            "lei_structure_scale": [
                "CONTEXT",
                "CONTEXT",
                "MICRO",
                "CONTEXT",
                "CONTEXT",
                "CONTEXT",
                "INTERNAL",
                "CONTEXT",
            ],

            "lei_location_valid": [
                0,
                1,
                1,
                1,
                1,
                0,
                1,
                0,
            ],

            "lei_distance_atr": [
                np.nan,
                0.10,
                0.12,
                0.08,
                0.15,
                np.nan,
                0.18,
                0.50,
            ],

            "lei_trigger_strength": [
                0.0,
                4.0,
                2.0,
                4.0,
                4.0,
                0.0,
                1.0,
                3.0,
            ],

            "lei_confirmation_flag": [
                0,
                1,
                0,
                1,
                1,
                0,
                0,
                0,
            ],

            "lei_confirmation_type": [
                "NONE",
                "MICRO_BOS",
                "NONE",
                "BREAKOUT_ACCEPTANCE",
                "INTERNAL_BOS",
                "NONE",
                "NONE",
                "NONE",
            ],

            "lei_invalidation_price": [
                np.nan,
                2399.9,
                np.nan,
                2400.5,
                2400.9,
                np.nan,
                np.nan,
                np.nan,
            ],

            "lei_candidate_flag": [
                0,
                1,
                0,
                1,
                1,
                0,
                0,
                0,
            ],

            "lei_decision_state": [
                "NEUTRAL",
                "LONG_WATCH",
                "LONG_WATCH",
                "HOLD_BULLISH",
                "SHORT_WATCH",
                "WAIT_CONFLICT",
                "HOLD_BEARISH",
                "SHORT_WATCH",
            ],

            "liqintel_trap_flag": [
                0,
                1,
                0,
                0,
                0,
                0,
                0,
                0,
            ],

            "liqintel_failed_breakout_flag": [
                0,
                0,
                0,
                0,
                1,
                0,
                0,
                0,
            ],

            "liqintel_breakout_accepted_flag": [
                0,
                0,
                0,
                1,
                0,
                0,
                0,
                0,
            ],

            "research_pipeline_version": [
                "1.0.1",
            ] * 8,

            "research_pipeline_mode": [
                "SHADOW_CAUSAL_RESEARCH_ONLY",
            ] * 8,

            "research_trade_ready_unchanged": [
                1,
            ] * 8,

            "research_live_safe": [
                1,
            ] * 8,
        }
    )


def test_summary_counts_overlap_correctly() -> None:

    frame = _telemetry_frame()

    summary = (
        ResearchTelemetryObserver
        .summary(
            frame
        )
    )

    row = summary.iloc[
        0
    ]

    assert int(
        row[
            "total_bars"
        ]
    ) == 8

    assert int(
        row[
            "production_ready_count"
        ]
    ) == 3

    assert int(
        row[
            "research_candidate_count"
        ]
    ) == 3

    assert int(
        row[
            "long_candidate_count"
        ]
    ) == 2

    assert int(
        row[
            "short_candidate_count"
        ]
    ) == 1

    assert int(
        row[
            "ready_and_candidate_count"
        ]
    ) == 2

    assert int(
        row[
            "ready_without_candidate_count"
        ]
    ) == 1

    assert int(
        row[
            "candidate_without_ready_count"
        ]
    ) == 1

    assert float(
        row[
            "ready_candidate_overlap_pct"
        ]
    ) == pytest.approx(
        66.667
    )

    assert float(
        row[
            "candidate_ready_overlap_pct"
        ]
    ) == pytest.approx(
        66.667
    )


def test_summary_counts_decision_and_liquidity_states() -> None:

    summary = (
        ResearchTelemetryObserver
        .summary(
            _telemetry_frame()
        )
    )

    row = summary.iloc[
        0
    ]

    assert int(
        row[
            "mdc_long_watch_count"
        ]
    ) == 2

    assert int(
        row[
            "mdc_short_watch_count"
        ]
    ) == 2

    assert int(
        row[
            "mdc_hold_bullish_count"
        ]
    ) == 1

    assert int(
        row[
            "mdc_hold_bearish_count"
        ]
    ) == 1

    assert int(
        row[
            "mdc_conflict_count"
        ]
    ) == 1

    assert int(
        row[
            "lei_wait_location_count"
        ]
    ) == 1

    assert int(
        row[
            "lei_wait_trigger_count"
        ]
    ) == 1

    assert int(
        row[
            "lei_wait_confirmation_count"
        ]
    ) == 1

    assert int(
        row[
            "liq_trap_count"
        ]
    ) == 1

    assert int(
        row[
            "liq_failed_breakout_count"
        ]
    ) == 1

    assert int(
        row[
            "liq_accepted_breakout_count"
        ]
    ) == 1


def test_candidate_events_only_returns_candidates() -> None:

    result = (
        ResearchTelemetryObserver
        .candidate_events(
            _telemetry_frame()
        )
    )

    assert len(
        result
    ) == 3

    assert (
        pd.to_numeric(
            result[
                "lei_candidate_flag"
            ],
            errors="coerce",
        )
        .eq(
            1
        )
        .all()
    )

    assert (
        "production_ready_overlap"
        in result.columns
    )

    assert int(
        result[
            "production_ready_overlap"
        ].sum()
    ) == 2


def test_production_ready_context_only_returns_ready_rows() -> None:

    result = (
        ResearchTelemetryObserver
        .production_ready_context(
            _telemetry_frame()
        )
    )

    assert len(
        result
    ) == 3

    assert (
        pd.to_numeric(
            result[
                "trade_ready"
            ],
            errors="coerce",
        )
        .eq(
            1
        )
        .all()
    )

    assert (
        "research_candidate_overlap"
        in result.columns
    )

    assert int(
        result[
            "research_candidate_overlap"
        ].sum()
    ) == 2


def test_status_distribution_totals_all_rows() -> None:

    frame = _telemetry_frame()

    result = (
        ResearchTelemetryObserver
        .status_distribution(
            frame
        )
    )

    assert int(
        result[
            "count"
        ].sum()
    ) == len(
        frame
    )

    statuses = set(
        result[
            "lei_status"
        ].astype(
            str
        )
    )

    assert (
        "LONG_CANDIDATE"
        in statuses
    )

    assert (
        "SHORT_CANDIDATE"
        in statuses
    )


def test_family_distribution_only_uses_candidates() -> None:

    result = (
        ResearchTelemetryObserver
        .family_distribution(
            _telemetry_frame()
        )
    )

    assert int(
        result[
            "count"
        ].sum()
    ) == 3

    assert set(
        result[
            "lei_entry_family"
        ].astype(
            str
        )
    ) == {
        "SWEEP_RECLAIM",
        "BREAK_ACCEPTANCE",
        "FAILED_BREAKOUT",
    }


def test_rejects_hindsight_columns() -> None:

    frame = _telemetry_frame()

    frame[
        "cslabel_future_information"
    ] = 1

    with pytest.raises(
        ValueError,
        match="cslabel",
    ):

        ResearchTelemetryObserver.summary(
            frame
        )


def test_rejects_broken_live_safe_contract() -> None:

    frame = _telemetry_frame()

    frame.loc[
        3,
        "research_live_safe",
    ] = 0

    with pytest.raises(
        ValueError,
        match="research_live_safe",
    ):

        ResearchTelemetryObserver.summary(
            frame
        )


def test_rejects_candidate_status_contract_mismatch() -> None:

    frame = _telemetry_frame()

    frame.loc[
        1,
        "lei_candidate_flag",
    ] = 0

    with pytest.raises(
        ValueError,
        match="candidate flag/status",
    ):

        ResearchTelemetryObserver.summary(
            frame
        )


def test_observer_does_not_mutate_input() -> None:

    frame = _telemetry_frame()

    before = frame.copy(
        deep=True
    )

    ResearchTelemetryObserver.summary(
        frame
    )

    ResearchTelemetryObserver.candidate_events(
        frame
    )

    ResearchTelemetryObserver.production_ready_context(
        frame
    )

    pd.testing.assert_frame_equal(
        frame,
        before,
    )


def test_real_research_pipeline_output_is_accepted() -> None:

    pipeline_module: Any = importlib.import_module(
        "02_AI.Shadow.research_intelligence_pipeline"
    )

    research_pipeline: Any = (
        pipeline_module
        .research_intelligence_pipeline
    )

    rows = 180

    sequence = np.arange(
        rows,
        dtype=float,
    )

    anchor = (
        2400.0
        +
        sequence
        *
        0.002
        +
        np.sin(
            sequence
            /
            8.0
        )
        *
        0.75
    )

    open_price = (
        anchor
        +
        np.sin(
            sequence
            /
            5.0
        )
        *
        0.04
    )

    close_price = (
        anchor
        +
        np.cos(
            sequence
            /
            6.0
        )
        *
        0.04
    )

    high = (
        np.maximum(
            open_price,
            close_price,
        )
        +
        0.24
    )

    low = (
        np.minimum(
            open_price,
            close_price,
        )
        -
        0.24
    )

    raw = pd.DataFrame(
        {
            "time": pd.date_range(
                "2026-08-10 00:00:00+00:00",
                periods=rows,
                freq="min",
            ),

            "open": open_price,

            "high": high,

            "low": low,

            "close": close_price,

            "tick_volume": np.full(
                rows,
                100,
                dtype=np.int64,
            ),
        }
    )

    enriched = research_pipeline.generate(
        raw
    )

    summary = (
        ResearchTelemetryObserver
        .summary(
            enriched
        )
    )

    assert len(
        summary
    ) == 1

    assert int(
        summary.iloc[
            0
        ][
            "total_bars"
        ]
    ) == rows