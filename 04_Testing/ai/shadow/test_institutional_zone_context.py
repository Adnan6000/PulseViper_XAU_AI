"""
Offline causal tests for InstitutionalZoneContext v1.0.
"""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pandas as pd
import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Shadow.institutional_zone_context"
)

Context: Any = (
    module.InstitutionalZoneContext
)


def _market() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "time": pd.date_range(
                "2026-08-13 10:00:00+00:00",
                periods=6,
                freq="min",
            ),

            "open": [
                101.0,
                101.0,
                100.5,
                100.0,
                100.0,
                99.0,
            ],

            "high": [
                101.5,
                101.5,
                100.8,
                102.2,
                100.5,
                104.5,
            ],

            "low": [
                100.5,
                100.5,
                99.2,
                99.8,
                98.2,
                98.8,
            ],

            "close": [
                101.0,
                101.0,
                99.5,
                101.5,
                98.5,
                104.0,
            ],

            "atr": [
                1.0,
            ] * 6,

            "trade_ready": [
                0,
                1,
                0,
                0,
                1,
                0,
            ],

            "confidence_score": [
                50.0,
                60.0,
                70.0,
                80.0,
                90.0,
                40.0,
            ],

            "setup_state": [
                "TEST",
            ] * 6,

            "bos_direction": [
                "NONE",
            ] * 6,
        }
    )


def _events() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "iz_event_id": [
                "BULL-1",
                "BEAR-2",
            ],

            "iz_event_flag": [
                1,
                1,
            ],

            "iz_direction": [
                "BULLISH",
                "BEARISH",
            ],

            "iz_zone_type": [
                "DEMAND",
                "SUPPLY",
            ],

            "iz_confirmation_position": [
                1,
                2,
            ],

            "iz_zone_high": [
                100.0,
                103.0,
            ],

            "iz_zone_low": [
                99.0,
                102.0,
            ],

            "iz_strength": [
                75.0,
                70.0,
            ],

            "iz_live_safe": [
                1,
                1,
            ],
        }
    )


def _lifecycle() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "izl_event_id": [
                "BULL-1",
                "BULL-1",
                "BULL-1",
                "BULL-1",

                "BEAR-2",
                "BEAR-2",
                "BEAR-2",
                "BEAR-2",
            ],

            "izl_observation_position": [
                1,
                2,
                3,
                4,

                2,
                3,
                4,
                5,
            ],

            "izl_state": [
                "FRESH",
                "MITIGATED",
                "ACCEPTED",
                "INVALIDATED",

                "FRESH",
                "MITIGATED",
                "ACCEPTED",
                "INVALIDATED",
            ],

            "izl_touch_count": [
                0,
                1,
                1,
                2,

                0,
                1,
                1,
                2,
            ],

            "izl_age_bars": [
                0,
                1,
                2,
                3,

                0,
                1,
                2,
                3,
            ],

            "izl_live_safe": [
                1,
            ] * 8,
        }
    )


def test_before_confirmation_has_no_zone() -> None:

    result = Context.generate(
        _market(),
        _events(),
        _lifecycle(),
    )

    first = result.iloc[
        0
    ]

    assert int(
        first[
            "izctx_active_bullish_count"
        ]
    ) == 0

    assert (
        first[
            "izctx_bullish_event_id"
        ]
        ==
        "NONE"
    )


def test_bullish_zone_appears_on_confirmation_bar() -> None:

    result = Context.generate(
        _market(),
        _events(),
        _lifecycle(),
    )

    row = result.iloc[
        1
    ]

    assert (
        row[
            "izctx_bullish_event_id"
        ]
        ==
        "BULL-1"
    )

    assert (
        row[
            "izctx_bullish_state"
        ]
        ==
        "FRESH"
    )


def test_inside_zone_has_zero_distance() -> None:

    result = Context.generate(
        _market(),
        _events(),
        _lifecycle(),
    )

    row = result.iloc[
        2
    ]

    assert (
        row[
            "izctx_bullish_state"
        ]
        ==
        "MITIGATED"
    )

    assert int(
        row[
            "izctx_bullish_inside_flag"
        ]
    ) == 1

    assert float(
        row[
            "izctx_bullish_distance"
        ]
    ) == pytest.approx(
        0.0
    )

    assert float(
        row[
            "izctx_bullish_distance_atr"
        ]
    ) == pytest.approx(
        0.0
    )


def test_bearish_zone_appears_causally() -> None:

    result = Context.generate(
        _market(),
        _events(),
        _lifecycle(),
    )

    row = result.iloc[
        2
    ]

    assert (
        row[
            "izctx_bearish_event_id"
        ]
        ==
        "BEAR-2"
    )

    assert (
        row[
            "izctx_bearish_state"
        ]
        ==
        "FRESH"
    )


def test_lifecycle_state_advances_bar_by_bar() -> None:

    result = Context.generate(
        _market(),
        _events(),
        _lifecycle(),
    )

    assert (
        result.iloc[
            3
        ][
            "izctx_bullish_state"
        ]
        ==
        "ACCEPTED"
    )

    assert (
        result.iloc[
            3
        ][
            "izctx_bearish_state"
        ]
        ==
        "MITIGATED"
    )


def test_invalidated_zone_is_excluded_from_nearest() -> None:

    result = Context.generate(
        _market(),
        _events(),
        _lifecycle(),
    )

    row = result.iloc[
        4
    ]

    assert (
        row[
            "izctx_bullish_event_id"
        ]
        ==
        "NONE"
    )

    assert int(
        row[
            "izctx_active_bullish_count"
        ]
    ) == 0

    assert int(
        row[
            "izctx_invalidated_count"
        ]
    ) == 1


def test_bearish_zone_is_excluded_after_invalidation() -> None:

    result = Context.generate(
        _market(),
        _events(),
        _lifecycle(),
    )

    row = result.iloc[
        5
    ]

    assert (
        row[
            "izctx_bearish_event_id"
        ]
        ==
        "NONE"
    )

    assert int(
        row[
            "izctx_active_bearish_count"
        ]
    ) == 0

    assert int(
        row[
            "izctx_invalidated_count"
        ]
    ) == 2


def test_range_overlap_is_observational() -> None:

    result = Context.generate(
        _market(),
        _events(),
        _lifecycle(),
    )

    row = result.iloc[
        3
    ]

    assert int(
        row[
            "izctx_bearish_overlap_flag"
        ]
    ) == 1


def test_prefix_invariance() -> None:

    full_market = _market()

    prefix_market = full_market.iloc[
        :4
    ].copy()

    full = Context.generate(
        full_market,
        _events(),
        _lifecycle(),
    )

    prefix_lifecycle = _lifecycle().loc[
        pd.to_numeric(
            _lifecycle()[
                "izl_observation_position"
            ],
            errors="coerce",
        ).le(
            3
        )
    ].copy()

    prefix_events = _events().loc[
        pd.to_numeric(
            _events()[
                "iz_confirmation_position"
            ],
            errors="coerce",
        ).le(
            3
        )
    ].copy()

    prefix = Context.generate(
        prefix_market,
        prefix_events,
        prefix_lifecycle,
    )

    comparable = (
        full.iloc[
            :4
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    pd.testing.assert_frame_equal(
        prefix.reset_index(
            drop=True
        ),
        comparable,
    )


def test_future_lifecycle_rows_do_not_rewrite_past() -> None:

    market = _market()

    early_lifecycle = _lifecycle().loc[
        pd.to_numeric(
            _lifecycle()[
                "izl_observation_position"
            ],
            errors="coerce",
        ).le(
            3
        )
    ].copy()

    early = Context.generate(
        market.iloc[
            :4
        ].copy(),
        _events(),
        early_lifecycle,
    )

    full = Context.generate(
        market,
        _events(),
        _lifecycle(),
    )

    pd.testing.assert_frame_equal(
        early.reset_index(
            drop=True
        ),
        full.iloc[
            :4
        ].reset_index(
            drop=True
        ),
    )


def test_hindsight_columns_are_rejected() -> None:

    events = _events()

    events[
        "izlabel_future_quality"
    ] = "GOOD"

    with pytest.raises(
        ValueError,
        match="izlabel",
    ):

        Context.generate(
            _market(),
            events,
            _lifecycle(),
        )


def test_non_live_safe_inputs_are_rejected() -> None:

    lifecycle = _lifecycle()

    lifecycle.loc[
        0,
        "izl_live_safe",
    ] = 0

    with pytest.raises(
        ValueError,
        match="izl_live_safe",
    ):

        Context.generate(
            _market(),
            _events(),
            lifecycle,
        )


def test_protected_columns_are_unchanged() -> None:

    market = _market()

    result = Context.generate(
        market,
        _events(),
        _lifecycle(),
    )

    for column in (
        "trade_ready",
        "confidence_score",
        "setup_state",
        "bos_direction",
    ):

        pd.testing.assert_series_equal(
            market[
                column
            ],
            result[
                column
            ],
        )


def test_input_frames_are_not_mutated() -> None:

    market = _market()

    events = _events()

    lifecycle = _lifecycle()

    market_before = market.copy(
        deep=True
    )

    events_before = events.copy(
        deep=True
    )

    lifecycle_before = lifecycle.copy(
        deep=True
    )

    _ = Context.generate(
        market,
        events,
        lifecycle,
    )

    pd.testing.assert_frame_equal(
        market,
        market_before,
    )

    pd.testing.assert_frame_equal(
        events,
        events_before,
    )

    pd.testing.assert_frame_equal(
        lifecycle,
        lifecycle_before,
    )


def test_rerun_is_deterministic() -> None:

    first = Context.generate(
        _market(),
        _events(),
        _lifecycle(),
    )

    second = Context.generate(
        first,
        _events(),
        _lifecycle(),
    )

    columns = [
        column
        for column in first.columns
        if column.startswith(
            "izctx_"
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