"""
Offline tests for ResearchZoneContextForwardLedger v1.0.
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
    "02_AI.Shadow.research_zone_context_forward_ledger"
)

Ledger: Any = (
    module.ResearchZoneContextForwardLedger
)


# =============================================================================
# Deterministic causal fixture
# =============================================================================


def _frame() -> pd.DataFrame:
    """
    Important fixture contract
    --------------------------
    08:59 is deliberate PRE-ANCHOR HISTORY.

    Candidate sequence:

    09:00 LONG BREAK_ACCEPTANCE
    09:01 LONG BREAK_ACCEPTANCE   -> same episode
    09:03 LONG FAILED_BREAKOUT    -> new episode
    09:06 SHORT BREAK_ACCEPTANCE  -> new episode
    """

    times = pd.date_range(
        "2026-08-13 08:59:00+00:00",
        periods=8,
        freq="min",
    )

    return pd.DataFrame(
        {
            "time": times,

            "open": [
                99.5,
                100.0,
                100.5,
                101.0,
                101.5,
                102.0,
                102.5,
                103.0,
            ],

            "high": [
                100.5,
                101.0,
                101.5,
                102.0,
                102.5,
                103.0,
                103.5,
                104.0,
            ],

            "low": [
                98.5,
                99.0,
                99.5,
                100.0,
                100.5,
                101.0,
                101.5,
                102.0,
            ],

            "close": [
                99.5,
                100.0,
                100.5,
                101.0,
                101.5,
                102.0,
                102.5,
                103.0,
            ],

            "lei_candidate_flag": [
                0,  # 08:59 anchor history
                1,  # 09:00 episode 1
                1,  # 09:01 continuation
                0,
                1,  # 09:03 episode 2
                0,
                0,
                1,  # 09:06 episode 3
            ],

            "lei_direction": [
                "NONE",
                "LONG",
                "LONG",
                "NONE",
                "LONG",
                "NONE",
                "NONE",
                "SHORT",
            ],

            "lei_entry_family": [
                "NONE",
                "BREAK_ACCEPTANCE",
                "BREAK_ACCEPTANCE",
                "NONE",
                "FAILED_BREAKOUT",
                "NONE",
                "NONE",
                "BREAK_ACCEPTANCE",
            ],

            "liqintel_event_interpretation": [
                "NONE",
                "ACCEPTED_HIGH",
                "ACCEPTED_HIGH",
                "NONE",
                "RECLAIMED_LOW",
                "NONE",
                "NONE",
                "ACCEPTED_LOW",
            ],

            "lei_reference_source": [
                "NONE",
                "INTERNAL_HIGH",
                "INTERNAL_HIGH",
                "NONE",
                "INTERNAL_LOW",
                "NONE",
                "NONE",
                "MAJOR_LOW",
            ],

            "lei_confirmation_type": [
                "NONE",
                "BREAKOUT_ACCEPTANCE",
                "BREAKOUT_ACCEPTANCE",
                "NONE",
                "BULLISH_DISPLACEMENT",
                "NONE",
                "NONE",
                "BEARISH_DISPLACEMENT",
            ],

            "confidence_score": [
                50.0,
                75.0,
                75.0,
                50.0,
                70.0,
                50.0,
                50.0,
                65.0,
            ],

            "regime_state": [
                "RANGE_NORMAL_VOL",
                "BULLISH_LOW_VOL",
                "BULLISH_LOW_VOL",
                "RANGE_NORMAL_VOL",
                "BULLISH_NORMAL_VOL",
                "RANGE_NORMAL_VOL",
                "RANGE_NORMAL_VOL",
                "BEARISH_NORMAL_VOL",
            ],

            # -----------------------------------------------------------------
            # Bullish zone context
            # -----------------------------------------------------------------

            "izctx_active_bullish_count": [
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
            ],

            "izctx_bullish_event_id": [
                "B0",
                "B1",
                "B1",
                "B1",
                "B2",
                "B2",
                "B2",
                "B3",
            ],

            "izctx_bullish_state": [
                "FRESH",
                "ACCEPTED",
                "ACCEPTED",
                "ACCEPTED",
                "FRESH",
                "FRESH",
                "FRESH",
                "ACCEPTED",
            ],

            "izctx_bullish_distance_atr": [
                1.50,
                0.60,
                0.60,
                0.60,
                0.00,
                0.00,
                0.00,
                0.20,
            ],

            "izctx_bullish_inside_flag": [
                0,
                0,
                0,
                0,
                1,
                1,
                1,
                0,
            ],

            "izctx_bullish_overlap_flag": [
                0,
                0,
                0,
                0,
                1,
                1,
                1,
                0,
            ],

            # -----------------------------------------------------------------
            # Bearish zone context
            # -----------------------------------------------------------------

            "izctx_active_bearish_count": [
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
            ],

            "izctx_bearish_event_id": [
                "S0",
                "S1",
                "S1",
                "S1",
                "S2",
                "S2",
                "S2",
                "S3",
            ],

            "izctx_bearish_state": [
                "FRESH",
                "FRESH",
                "FRESH",
                "FRESH",
                "ACCEPTED",
                "ACCEPTED",
                "ACCEPTED",
                "ACCEPTED",
            ],

            "izctx_bearish_distance_atr": [
                1.50,
                1.20,
                1.20,
                1.20,
                0.15,
                0.15,
                0.15,
                0.40,
            ],

            "izctx_bearish_inside_flag": [
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            ],

            "izctx_bearish_overlap_flag": [
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                1,
            ],

            # -----------------------------------------------------------------
            # Safety metadata
            # -----------------------------------------------------------------

            "izctx_live_safe": [
                1,
            ] * 8,

            "izctx_version": [
                "1.0",
            ] * 8,

            "izctx_mode": [
                "SHADOW_CAUSAL_ZONE_CONTEXT_ONLY",
            ] * 8,

            "research_live_safe": [
                1,
            ] * 8,

            "research_trade_ready_unchanged": [
                1,
            ] * 8,
        }
    )


def _capture_seed() -> pd.DataFrame:
    """
    Minimal valid capture frame:

    08:59 = anchor history
    09:00 = forward candidate

    This preserves the forward episode-boundary contract.
    """

    return (
        _frame()
        .iloc[
            :2
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )


# =============================================================================
# Anchor
# =============================================================================


def test_anchor_round_trip(
    tmp_path: Path,
) -> None:

    store = Ledger(
        tmp_path
        /
        "forward_zone.csv"
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
        "forward_zone.csv"
    )

    assert store.load_anchor() is None


def test_latest_market_time() -> None:

    latest = Ledger.latest_market_time(
        _frame()
    )

    assert latest == pd.Timestamp(
        "2026-08-13 09:06:00"
    )


# =============================================================================
# Forward boundary + episode construction
# =============================================================================


def test_capture_is_strictly_after_anchor() -> None:

    store = Ledger()

    result = store.capture_after_anchor(
        _frame(),
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

    # Candidate exactly at anchor is historical boundary.
    assert pd.Timestamp(
        "2026-08-13 09:00:00"
    ) not in times

    # Same episode as candidate at anchor.
    assert pd.Timestamp(
        "2026-08-13 09:01:00"
    ) not in times

    # Genuine later episode starts.
    assert pd.Timestamp(
        "2026-08-13 09:03:00"
    ) in times

    assert pd.Timestamp(
        "2026-08-13 09:06:00"
    ) in times


def test_same_episode_is_not_duplicated() -> None:

    store = Ledger()

    result = store.capture_after_anchor(
        _frame(),
        anchor_time="2026-08-13 08:59:00",
        requested_symbol="XAUUSDm",
        resolved_symbol="XAUUSDm",
    )

    assert len(
        result
    ) == 3

    times = set(
        pd.to_datetime(
            result[
                "signal_time"
            ]
        )
    )

    assert pd.Timestamp(
        "2026-08-13 09:00:00"
    ) in times

    assert pd.Timestamp(
        "2026-08-13 09:01:00"
    ) not in times

    assert pd.Timestamp(
        "2026-08-13 09:03:00"
    ) in times

    assert pd.Timestamp(
        "2026-08-13 09:06:00"
    ) in times


def test_capture_requires_anchor_history() -> None:

    store = Ledger()

    frame = _frame().loc[
        lambda x: pd.to_datetime(
            x[
                "time"
            ],
            utc=True,
        ).ge(
            pd.Timestamp(
                "2026-08-13 09:03:00+00:00"
            )
        )
    ].copy()

    with pytest.raises(
        ValueError,
        match="include history",
    ):

        store.capture_after_anchor(
            frame,
            anchor_time="2026-08-13 09:00:00",
            requested_symbol="XAUUSDm",
            resolved_symbol="XAUUSDm",
        )


# =============================================================================
# Signal snapshot
# =============================================================================


def test_signal_close_is_frozen_as_entry() -> None:

    store = Ledger()

    result = store.capture_after_anchor(
        _frame(),
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


def test_z1_accepted_is_frozen() -> None:

    store = Ledger()

    result = store.capture_after_anchor(
        _frame(),
        anchor_time="2026-08-13 08:59:00",
        requested_symbol="XAUUSDm",
        resolved_symbol="XAUUSDm",
    )

    first = result.iloc[
        0
    ]

    assert (
        first[
            "signal_time"
        ]
        ==
        pd.Timestamp(
            "2026-08-13 09:00:00"
        )
    )

    assert (
        first[
            "aligned_zone_state"
        ]
        ==
        "ACCEPTED"
    )

    assert int(
        first[
            "z1_aligned_accepted"
        ]
    ) == 1

    assert (
        "Z1"
        in str(
            first[
                "hypothesis_tags"
            ]
        )
    )


def test_z2_and_z3_capture_fresh_inside_long() -> None:

    store = Ledger()

    result = store.capture_after_anchor(
        _frame(),
        anchor_time="2026-08-13 09:00:00",
        requested_symbol="XAUUSDm",
        resolved_symbol="XAUUSDm",
    )

    row = result.loc[
        pd.to_datetime(
            result[
                "signal_time"
            ]
        ).eq(
            pd.Timestamp(
                "2026-08-13 09:03:00"
            )
        )
    ].iloc[
        0
    ]

    assert (
        row[
            "direction"
        ]
        ==
        "LONG"
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
        "INSIDE"
    )

    assert int(
        row[
            "z2_aligned_fresh"
        ]
    ) == 1

    assert int(
        row[
            "z3_aligned_inside"
        ]
    ) == 1


def test_short_uses_bearish_zone_as_aligned() -> None:

    store = Ledger()

    result = store.capture_after_anchor(
        _frame(),
        anchor_time="2026-08-13 09:05:00",
        requested_symbol="XAUUSDm",
        resolved_symbol="XAUUSDm",
    )

    assert len(
        result
    ) == 1

    row = result.iloc[
        0
    ]

    assert (
        row[
            "direction"
        ]
        ==
        "SHORT"
    )

    assert (
        row[
            "aligned_zone_event_id"
        ]
        ==
        "S3"
    )

    assert (
        row[
            "aligned_zone_state"
        ]
        ==
        "ACCEPTED"
    )

    assert (
        row[
            "aligned_location"
        ]
        ==
        "OVERLAP"
    )

    assert int(
        row[
            "z4_short_aligned_overlap"
        ]
    ) == 1


def test_z5_short_aligned_inside() -> None:

    frame = _frame()

    short_time = pd.Timestamp(
        "2026-08-13 09:06:00+00:00"
    )

    mask = pd.to_datetime(
        frame[
            "time"
        ],
        utc=True,
    ).eq(
        short_time
    )

    frame.loc[
        mask,
        "izctx_bearish_distance_atr",
    ] = 0.0

    frame.loc[
        mask,
        "izctx_bearish_inside_flag",
    ] = 1

    frame.loc[
        mask,
        "izctx_bearish_overlap_flag",
    ] = 1

    store = Ledger()

    result = store.capture_after_anchor(
        frame,
        anchor_time="2026-08-13 09:05:00",
        requested_symbol="XAUUSDm",
        resolved_symbol="XAUUSDm",
    )

    row = result.iloc[
        0
    ]

    assert (
        row[
            "aligned_location"
        ]
        ==
        "INSIDE"
    )

    assert int(
        row[
            "z5_short_aligned_inside"
        ]
    ) == 1


def test_z6_both_close_is_direction_relative() -> None:

    store = Ledger()

    result = store.capture_after_anchor(
        _frame(),
        anchor_time="2026-08-13 09:05:00",
        requested_symbol="XAUUSDm",
        resolved_symbol="XAUUSDm",
    )

    row = result.iloc[
        0
    ]

    # SHORT:
    # aligned  = bearish S3 OVERLAP
    # opposing = bullish B3 NEAR
    assert (
        row[
            "zone_relation"
        ]
        ==
        "BOTH_CLOSE"
    )

    assert int(
        row[
            "z6_both_close"
        ]
    ) == 1


# =============================================================================
# Merge
# =============================================================================


def test_merge_deduplicates_events() -> None:

    store = Ledger()

    captured = store.capture_after_anchor(
        _frame(),
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


# =============================================================================
# Future outcomes
# =============================================================================


def _long_market() -> pd.DataFrame:

    times = pd.date_range(
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
            "time": times,

            "open": close,

            "high": (
                close
                +
                0.5
            ),

            "low": (
                close
                -
                0.3
            ),

            "close": close,
        }
    )


def test_future_outcome_starts_after_signal_bar() -> None:

    store = Ledger()

    ledger = store.capture_after_anchor(
        _capture_seed(),
        anchor_time="2026-08-13 08:59:00",
        requested_symbol="XAUUSDm",
        resolved_symbol="XAUUSDm",
    )

    assert len(
        ledger
    ) == 1

    market = _long_market()

    # Giant SIGNAL candle high.
    # Must never enter future MFE calculation.
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
    ) < 20.0

    assert int(
        row[
            "positive_20"
        ]
    ) == 1


def test_hypothesis_dashboard_uses_matured_rows() -> None:

    store = Ledger()

    ledger = store.capture_after_anchor(
        _capture_seed(),
        anchor_time="2026-08-13 08:59:00",
        requested_symbol="XAUUSDm",
        resolved_symbol="XAUUSDm",
    )

    result = store.evaluate(
        ledger,
        _long_market(),
    )

    dashboard = store.hypothesis_dashboard(
        result
    )

    z1 = dashboard.loc[
        dashboard[
            "hypothesis"
        ].eq(
            "Z1"
        )
    ].iloc[
        0
    ]

    assert int(
        z1[
            "n"
        ]
    ) == 1

    assert float(
        z1[
            "net20_med"
        ]
    ) > 0.0


# =============================================================================
# Safety
# =============================================================================


def test_hindsight_is_rejected() -> None:

    frame = _frame()

    frame[
        "izlabel_future"
    ] = 1

    store = Ledger()

    with pytest.raises(
        ValueError,
        match="Hindsight",
    ):

        store.capture_after_anchor(
            frame,
            anchor_time="2026-08-13 08:59:00",
            requested_symbol="XAUUSDm",
            resolved_symbol="XAUUSDm",
        )


def test_non_live_safe_zone_context_is_rejected() -> None:

    frame = _frame()

    frame.loc[
        0,
        "izctx_live_safe",
    ] = 0

    store = Ledger()

    with pytest.raises(
        ValueError,
        match="izctx_live_safe",
    ):

        store.capture_after_anchor(
            frame,
            anchor_time="2026-08-13 08:59:00",
            requested_symbol="XAUUSDm",
            resolved_symbol="XAUUSDm",
        )


def test_input_is_not_mutated() -> None:

    frame = _frame()

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