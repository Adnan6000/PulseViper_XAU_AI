"""
Offline tests for ResearchWeightForwardLedger v1.0.
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
    "02_AI.Shadow.research_weight_forward_ledger"
)

Ledger: Any = (
    module.ResearchWeightForwardLedger
)


def _weighted_frame() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "time": pd.date_range(
                "2026-08-13 09:00:00+00:00",
                periods=4,
                freq="min",
            ),

            "open": [
                100.0,
                101.0,
                102.0,
                103.0,
            ],

            "high": [
                101.0,
                102.0,
                103.0,
                104.0,
            ],

            "low": [
                99.0,
                100.0,
                101.0,
                102.0,
            ],

            "close": [
                100.0,
                101.0,
                102.0,
                103.0,
            ],

            "lei_candidate_flag": [
                1,
                1,
                0,
                1,
            ],

            "lei_direction": [
                "LONG",
                "SHORT",
                "NONE",
                "LONG",
            ],

            "lei_entry_family": [
                "BREAK_ACCEPTANCE",
                "FAILED_BREAKOUT",
                "NONE",
                "BREAK_ACCEPTANCE",
            ],

            "lei_reference_source": [
                "INTERNAL_HIGH",
                "INTERNAL_LOW",
                "NONE",
                "MAJOR_HIGH",
            ],

            "lei_confirmation_type": [
                "BREAKOUT_ACCEPTANCE",
                "BEARISH_DISPLACEMENT",
                "NONE",
                "BREAKOUT_ACCEPTANCE",
            ],

            "lei_distance_atr": [
                0.08,
                0.20,
                np.nan,
                0.30,
            ],

            "confidence_score": [
                75.0,
                75.0,
                50.0,
                60.0,
            ],

            "regime_state": [
                "BULLISH_LOW_VOL",
                "BEARISH_LOW_VOL",
                "RANGE_NORMAL_VOL",
                "RANGE_NORMAL_VOL",
            ],

            "rwei_active": [
                1,
                1,
                0,
                1,
            ],

            "rwei_score": [
                4.5,
                4.0,
                np.nan,
                2.0,
            ],

            "rwei_tier": [
                "A",
                "A",
                "NONE",
                "B",
            ],

            "rwei_components": [
                "TEST_A_LONG",
                "TEST_A_SHORT",
                "NOT_CANDIDATE",
                "TEST_B_LONG",
            ],

            "rwei_live_safe": [
                1,
                1,
                1,
                1,
            ],

            "rwei_version": [
                "1.0",
            ] * 4,

            "rwei_mode": [
                "SHADOW_CAUSAL_WEIGHTING_ONLY",
            ] * 4,

            "rwei_policy": [
                "HYPOTHESIS_WEIGHTS_V1",
            ] * 4,

            "research_live_safe": [
                1,
            ] * 4,

            "research_trade_ready_unchanged": [
                1,
            ] * 4,
        }
    )


def test_anchor_round_trip(
    tmp_path: Path,
) -> None:

    store = Ledger(
        tmp_path
        /
        "forward.csv"
    )

    expected = pd.Timestamp(
        "2026-08-13 09:05:00"
    )

    saved = store.save_anchor(
        expected
    )

    loaded = store.load_anchor()

    assert saved == expected
    assert loaded == expected


def test_missing_anchor_returns_none(
    tmp_path: Path,
) -> None:

    store = Ledger(
        tmp_path
        /
        "forward.csv"
    )

    assert store.load_anchor() is None


def test_capture_is_strictly_after_anchor() -> None:

    store = Ledger()

    result = store.capture_after_anchor(
        _weighted_frame(),
        anchor_time="2026-08-13 09:00:00",
        requested_symbol="XAUUSDm",
        resolved_symbol="XAUUSDm",
    )

    times = set(
        pd.to_datetime(
            result[
                "signal_time"
            ]
        )
    )

    assert pd.Timestamp(
        "2026-08-13 09:00:00"
    ) not in times

    assert pd.Timestamp(
        "2026-08-13 09:01:00"
    ) in times

    assert pd.Timestamp(
        "2026-08-13 09:03:00"
    ) in times


def test_non_candidate_is_not_captured() -> None:

    store = Ledger()

    result = store.capture_after_anchor(
        _weighted_frame(),
        anchor_time="2026-08-13 08:59:00",
        requested_symbol="XAUUSDm",
        resolved_symbol="XAUUSDm",
    )

    assert len(
        result
    ) == 3


def test_signal_close_is_used_as_entry() -> None:

    store = Ledger()

    result = store.capture_after_anchor(
        _weighted_frame(),
        anchor_time="2026-08-13 08:59:00",
        requested_symbol="XAUUSDm",
        resolved_symbol="XAUUSDm",
    )

    first = result.iloc[
        0
    ]

    assert float(
        first[
            "entry_close"
        ]
    ) == pytest.approx(
        100.0
    )


def test_score_and_tier_are_frozen_at_signal() -> None:

    store = Ledger()

    result = store.capture_after_anchor(
        _weighted_frame(),
        anchor_time="2026-08-13 08:59:00",
        requested_symbol="XAUUSDm",
        resolved_symbol="XAUUSDm",
    )

    first = result.iloc[
        0
    ]

    assert float(
        first[
            "rwei_score"
        ]
    ) == pytest.approx(
        4.5
    )

    assert (
        first[
            "rwei_tier"
        ]
        ==
        "A"
    )


def test_merge_deduplicates_events() -> None:

    store = Ledger()

    captured = store.capture_after_anchor(
        _weighted_frame(),
        anchor_time="2026-08-13 08:59:00",
        requested_symbol="XAUUSDm",
        resolved_symbol="XAUUSDm",
    )

    first, new1 = store.merge(
        store._empty_frame(),
        captured,
    )

    second, new2 = store.merge(
        first,
        captured,
    )

    assert new1 == 3
    assert new2 == 0
    assert len(
        second
    ) == 3


def _long_market() -> pd.DataFrame:

    time = pd.date_range(
        "2026-08-13 09:00:00+00:00",
        periods=25,
        freq="min",
    )

    close = np.linspace(
        100.0,
        110.0,
        25,
    )

    return pd.DataFrame(
        {
            "time": time,
            "open": close,
            "high": close + 0.5,
            "low": close - 0.3,
            "close": close,
        }
    )


def test_long_forward_outcome_is_positive() -> None:

    frame = _weighted_frame().iloc[
        [
            0
        ]
    ].copy()

    store = Ledger()

    ledger = store.capture_after_anchor(
        frame,
        anchor_time="2026-08-13 08:59:00",
        requested_symbol="XAUUSDm",
        resolved_symbol="XAUUSDm",
    )

    result = store.evaluate(
        ledger,
        _long_market(),
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

    assert int(
        row[
            "positive_20"
        ]
    ) == 1


def test_signal_bar_is_not_counted_in_future_mfe() -> None:

    frame = _weighted_frame().iloc[
        [
            0
        ]
    ].copy()

    store = Ledger()

    ledger = store.capture_after_anchor(
        frame,
        anchor_time="2026-08-13 08:59:00",
        requested_symbol="XAUUSDm",
        resolved_symbol="XAUUSDm",
    )

    market = _long_market()

    market.loc[
        0,
        "high",
    ] = 1000.0

    result = store.evaluate(
        ledger,
        market,
    )

    assert float(
        result.iloc[
            0
        ][
            "mfe_20"
        ]
    ) < 20.0


def test_tier_dashboard_uses_matured_only() -> None:

    frame = _weighted_frame().iloc[
        [
            0
        ]
    ].copy()

    store = Ledger()

    ledger = store.capture_after_anchor(
        frame,
        anchor_time="2026-08-13 08:59:00",
        requested_symbol="XAUUSDm",
        resolved_symbol="XAUUSDm",
    )

    result = store.evaluate(
        ledger,
        _long_market(),
    )

    dashboard = store.tier_dashboard(
        result
    )

    tier_a = dashboard.loc[
        dashboard[
            "tier"
        ].eq(
            "A"
        )
    ].iloc[
        0
    ]

    assert int(
        tier_a[
            "n"
        ]
    ) == 1

    assert float(
        tier_a[
            "net20_med"
        ]
    ) > 0.0


def test_input_is_not_mutated() -> None:

    frame = _weighted_frame()

    original = frame.copy(
        deep=True
    )

    store = Ledger()

    _ = store.capture_after_anchor(
        frame,
        anchor_time="2026-08-13 08:59:00",
        requested_symbol="XAUUSDm",
        resolved_symbol="XAUUSDm",
    )

    pd.testing.assert_frame_equal(
        frame,
        original,
    )


def test_hindsight_is_rejected() -> None:

    frame = _weighted_frame()

    frame[
        "cslabel_future"
    ] = 1

    store = Ledger()

    with pytest.raises(
        ValueError,
        match="cslabel",
    ):

        store.capture_after_anchor(
            frame,
            anchor_time="2026-08-13 08:59:00",
            requested_symbol="XAUUSDm",
            resolved_symbol="XAUUSDm",
        )