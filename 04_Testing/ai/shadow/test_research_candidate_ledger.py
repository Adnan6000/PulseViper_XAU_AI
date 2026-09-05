"""
Offline deterministic tests for ResearchCandidateLedger v1.0.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Shadow.research_candidate_ledger"
)

ResearchCandidateLedger: Any = (
    module.ResearchCandidateLedger
)


def _candidate_frame() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "time": pd.date_range(
                "2026-08-13 00:00:00+00:00",
                periods=3,
                freq="min",
            ),

            "close": [
                100.0,
                110.0,
                120.0,
            ],

            "trade_ready": [
                0,
                1,
                0,
            ],

            "lei_candidate_flag": [
                1,
                1,
                0,
            ],

            "lei_status": [
                "LONG_CANDIDATE",
                "SHORT_CANDIDATE",
                "WAIT_TRIGGER",
            ],

            "lei_direction": [
                "LONG",
                "SHORT",
                "LONG",
            ],

            "lei_entry_family": [
                "BREAK_ACCEPTANCE",
                "FAILED_BREAKOUT",
                "NONE",
            ],

            "lei_reference_price": [
                99.5,
                111.0,
                119.0,
            ],

            "lei_reference_source": [
                "INTERNAL_HIGH",
                "MAJOR_HIGH",
                "MICRO_LOW",
            ],

            "lei_reference_origin": [
                "EVENT_LEVEL",
                "EVENT_LEVEL",
                "NEAREST_LEVEL",
            ],

            "lei_level_class": [
                "INTERNAL",
                "EXTERNAL",
                "INTERNAL",
            ],

            "lei_structure_scale": [
                "INTERNAL",
                "MAJOR",
                "MICRO",
            ],

            "lei_distance_atr": [
                0.10,
                0.20,
                0.30,
            ],

            "lei_trigger_strength": [
                4.0,
                4.0,
                1.0,
            ],

            "lei_confirmation_type": [
                "BREAKOUT_ACCEPTANCE",
                "INTERNAL_BOS",
                "NONE",
            ],

            "lei_invalidation_price": [
                99.0,
                111.5,
                np.nan,
            ],

            "confidence_direction": [
                "BULLISH",
                "BEARISH",
                "BULLISH",
            ],

            "confidence_score": [
                60.0,
                90.0,
                50.0,
            ],

            "mdc_state": [
                "LONG_WATCH",
                "SHORT_WATCH",
                "LONG_WATCH",
            ],

            "mdc_direction": [
                "BULLISH",
                "BEARISH",
                "BULLISH",
            ],

            "mdc_bullish_score": [
                5.0,
                1.0,
                4.0,
            ],

            "mdc_bearish_score": [
                1.0,
                5.0,
                1.0,
            ],

            "mdc_score_spread": [
                4.0,
                -4.0,
                3.0,
            ],

            "mdc_conflict_flag": [
                0,
                0,
                0,
            ],

            "liqintel_event_interpretation": [
                "UPSIDE_BREAKOUT_ACCEPTED",
                "FAILED_UPSIDE_BREAKOUT",
                "NONE",
            ],

            "liqintel_event_bias": [
                "BULLISH",
                "BEARISH",
                "NEUTRAL",
            ],

            "regime_state": [
                "TREND",
                "TREND",
                "RANGE",
            ],

            "regime_trend": [
                "UP",
                "DOWN",
                "FLAT",
            ],

            "regime_volatility": [
                "NORMAL",
                "HIGH",
                "LOW",
            ],

            "regime_time_bucket_utc": [
                "LONDON",
                "LONDON",
                "LONDON",
            ],

            "pipeline_version": [
                "X",
            ] * 3,

            "pipeline_mode": [
                "PRODUCTION",
            ] * 3,

            "research_pipeline_version": [
                "1.0.1",
            ] * 3,

            "research_pipeline_mode": [
                "SHADOW_CAUSAL_RESEARCH_ONLY",
            ] * 3,

            "research_live_safe": [
                1,
            ] * 3,

            "research_trade_ready_unchanged": [
                1,
            ] * 3,

            "lei_version": [
                "1.1",
            ] * 3,
        }
    )


def test_capture_only_candidate_rows() -> None:

    store = ResearchCandidateLedger()

    result = store.capture_candidates(
        _candidate_frame(),
        "XAUUSDm",
        "XAUUSDm",
        "M1",
    )

    assert len(
        result
    ) == 2

    assert set(
        result[
            "direction"
        ].astype(
            str
        )
    ) == {
        "LONG",
        "SHORT",
    }


def test_capture_uses_signal_close_not_perfect_reference_fill() -> None:

    store = ResearchCandidateLedger()

    result = store.capture_candidates(
        _candidate_frame(),
        "XAUUSDm",
        "XAUUSDm",
    )

    assert float(
        result.iloc[
            0
        ][
            "entry_close"
        ]
    ) == pytest.approx(
        100.0
    )

    assert float(
        result.iloc[
            0
        ][
            "lei_reference_price"
        ]
    ) == pytest.approx(
        99.5
    )

    assert (
        float(
            result.iloc[
                0
            ][
                "entry_close"
            ]
        )
        !=
        float(
            result.iloc[
                0
            ][
                "lei_reference_price"
            ]
        )
    )


def test_production_overlap_is_observational() -> None:

    store = ResearchCandidateLedger()

    result = store.capture_candidates(
        _candidate_frame(),
        "XAUUSDm",
        "XAUUSDm",
    )

    assert int(
        result.iloc[
            0
        ][
            "production_ready_overlap"
        ]
    ) == 0

    assert int(
        result.iloc[
            1
        ][
            "production_ready_overlap"
        ]
    ) == 1


def test_merge_deduplicates_same_candidate() -> None:

    store = ResearchCandidateLedger()

    candidates = store.capture_candidates(
        _candidate_frame(),
        "XAUUSDm",
        "XAUUSDm",
    )

    first, count1 = store.merge_new_candidates(
        store._empty_frame(),
        candidates,
        "BOOTSTRAP_BACKFILL",
    )

    second, count2 = store.merge_new_candidates(
        first,
        candidates,
        "LIVE_SHADOW",
    )

    assert count1 == 2
    assert count2 == 0
    assert len(
        second
    ) == 2


def _market_for_long() -> pd.DataFrame:

    rows = 25

    time = pd.date_range(
        "2026-08-13 00:00:00+00:00",
        periods=rows,
        freq="min",
    )

    close = np.full(
        rows,
        100.0,
        dtype=float,
    )

    close[
        1:
    ] = np.linspace(
        100.5,
        105.0,
        rows - 1,
    )

    high = close + 0.5
    low = close - 0.3

    return pd.DataFrame(
        {
            "time": time,
            "open": close,
            "high": high,
            "low": low,
            "close": close,
        }
    )


def test_bullish_candidate_evaluates_future_only() -> None:

    store = ResearchCandidateLedger()

    candidate = _candidate_frame().iloc[
        [
            0
        ]
    ].copy()

    ledger = store.capture_candidates(
        candidate,
        "XAUUSDm",
        "XAUUSDm",
    )

    market = _market_for_long()

    # Huge signal-bar high must NOT count as future MFE.
    market.loc[
        0,
        "high",
    ] = 1000.0

    result = store.evaluate(
        ledger,
        market,
    )

    row = result.iloc[
        0
    ]

    assert (
        row[
            "status"
        ]
        ==
        "MATURED_20"
    )

    assert float(
        row[
            "net_20"
        ]
    ) > 0.0

    assert float(
        row[
            "mfe_20"
        ]
    ) < 10.0

    assert int(
        row[
            "positive_20"
        ]
    ) == 1


def test_short_candidate_profit_is_signed_correctly() -> None:

    store = ResearchCandidateLedger()

    candidate = _candidate_frame().iloc[
        [
            1
        ]
    ].copy()

    # Make signal timestamp first row for clean evaluation.
    candidate.loc[
        candidate.index[
            0
        ],
        "time",
    ] = pd.Timestamp(
        "2026-08-13 00:00:00+00:00"
    )

    candidate.loc[
        candidate.index[
            0
        ],
        "close",
    ] = 110.0

    ledger = store.capture_candidates(
        candidate,
        "XAUUSDm",
        "XAUUSDm",
    )

    rows = 25

    time = pd.date_range(
        "2026-08-13 00:00:00+00:00",
        periods=rows,
        freq="min",
    )

    close = np.linspace(
        110.0,
        100.0,
        rows,
    )

    market = pd.DataFrame(
        {
            "time": time,
            "open": close,
            "high": close + 0.4,
            "low": close - 0.4,
            "close": close,
        }
    )

    result = store.evaluate(
        ledger,
        market,
    )

    assert float(
        result.iloc[
            0
        ][
            "net_20"
        ]
    ) > 0.0


def test_first_passage_marks_same_bar_ambiguity() -> None:

    store = ResearchCandidateLedger()

    candidate = _candidate_frame().iloc[
        [
            0
        ]
    ].copy()

    ledger = store.capture_candidates(
        candidate,
        "XAUUSDm",
        "XAUUSDm",
    )

    market = _market_for_long()

    market.loc[
        1,
        "high",
    ] = 101.5

    market.loc[
        1,
        "low",
    ] = 98.5

    result = store.evaluate(
        ledger,
        market,
    )

    assert (
        result.iloc[
            0
        ][
            "fp_1_result"
        ]
        ==
        "AMBIGUOUS_SAME_BAR"
    )


def test_partial_candidate_not_falsely_matured() -> None:

    store = ResearchCandidateLedger()

    candidate = _candidate_frame().iloc[
        [
            0
        ]
    ].copy()

    ledger = store.capture_candidates(
        candidate,
        "XAUUSDm",
        "XAUUSDm",
    )

    market = _market_for_long().iloc[
        :8
    ].copy()

    result = store.evaluate(
        ledger,
        market,
    )

    assert (
        result.iloc[
            0
        ][
            "status"
        ]
        ==
        "PARTIAL_5"
    )

    assert pd.isna(
        result.iloc[
            0
        ][
            "net_10"
        ]
    )

    assert pd.isna(
        result.iloc[
            0
        ][
            "net_20"
        ]
    )


def test_persistence_round_trip(
    tmp_path: Path,
) -> None:

    path = (
        tmp_path
        /
        "candidate_ledger.csv"
    )

    store = ResearchCandidateLedger(
        path
    )

    candidates = store.capture_candidates(
        _candidate_frame(),
        "XAUUSDm",
        "XAUUSDm",
    )

    store.save(
        candidates
    )

    loaded = store.load()

    assert len(
        loaded
    ) == 2

    assert set(
        loaded[
            "event_id"
        ].astype(
            str
        )
    ) == set(
        candidates[
            "event_id"
        ].astype(
            str
        )
    )


def test_dashboards_use_only_matured_rows() -> None:

    store = ResearchCandidateLedger()

    candidate = _candidate_frame().iloc[
        [
            0
        ]
    ].copy()

    ledger = store.capture_candidates(
        candidate,
        "XAUUSDm",
        "XAUUSDm",
    )

    result = store.evaluate(
        ledger,
        _market_for_long(),
    )

    performance = (
        store.performance_dashboard(
            result
        )
    )

    family = (
        store.family_dashboard(
            result
        )
    )

    confidence = (
        store.confidence_dashboard(
            result
        )
    )

    first_passage = (
        store.first_passage_dashboard(
            result
        )
    )

    assert int(
        performance.iloc[
            0
        ][
            "n"
        ]
    ) == 1

    assert int(
        family[
            "n"
        ].sum()
    ) == 1

    assert int(
        confidence[
            "n"
        ].sum()
    ) == 1

    assert (
        len(
            first_passage
        )
        ==
        4
    )


def test_rejects_hindsight_input() -> None:

    frame = _candidate_frame()

    frame[
        "cslabel_future"
    ] = 1

    store = ResearchCandidateLedger()

    with pytest.raises(
        ValueError,
        match="cslabel",
    ):

        store.capture_candidates(
            frame,
            "XAUUSDm",
            "XAUUSDm",
        )