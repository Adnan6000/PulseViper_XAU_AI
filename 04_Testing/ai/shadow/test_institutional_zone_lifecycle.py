"""
Offline causal tests for InstitutionalZoneLifecycle v1.0.
"""

from __future__ import annotations

import importlib
from typing import Any

import pandas as pd
import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Shadow.institutional_zone_lifecycle"
)

Lifecycle: Any = (
    module.InstitutionalZoneLifecycle
)


def _bullish_market() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "time": pd.date_range(
                "2026-08-13 10:00:00+00:00",
                periods=5,
                freq="min",
            ),

            "open": [
                102.0,
                101.5,
                100.5,
                99.8,
                100.5,
            ],

            "high": [
                103.0,
                102.0,
                101.0,
                101.2,
                100.8,
            ],

            "low": [
                101.0,
                100.5,
                99.5,
                99.4,
                98.5,
            ],

            "close": [
                102.5,
                101.0,
                99.8,
                100.8,
                98.8,
            ],
        }
    )


def _bullish_event() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "iz_event_id": [
                "IZ-BULLISH-0-0",
            ],

            "iz_event_flag": [
                1,
            ],

            "iz_direction": [
                "BULLISH",
            ],

            "iz_zone_type": [
                "DEMAND",
            ],

            "iz_origin_position": [
                0,
            ],

            "iz_confirmation_position": [
                0,
            ],

            "iz_origin_time": [
                pd.Timestamp(
                    "2026-08-13 09:59:00"
                ),
            ],

            "iz_confirmation_time": [
                pd.Timestamp(
                    "2026-08-13 10:00:00"
                ),
            ],

            "iz_zone_high": [
                100.0,
            ],

            "iz_zone_low": [
                99.0,
            ],

            "iz_live_safe": [
                1,
            ],
        }
    )


def _bearish_market() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "time": pd.date_range(
                "2026-08-13 11:00:00+00:00",
                periods=5,
                freq="min",
            ),

            "open": [
                98.0,
                98.5,
                99.5,
                100.2,
                100.5,
            ],

            "high": [
                99.0,
                99.5,
                100.5,
                100.6,
                101.5,
            ],

            "low": [
                97.0,
                97.8,
                99.0,
                98.5,
                100.0,
            ],

            "close": [
                97.5,
                98.8,
                100.2,
                99.5,
                101.2,
            ],
        }
    )


def _bearish_event() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "iz_event_id": [
                "IZ-BEARISH-0-0",
            ],

            "iz_event_flag": [
                1,
            ],

            "iz_direction": [
                "BEARISH",
            ],

            "iz_zone_type": [
                "SUPPLY",
            ],

            "iz_origin_position": [
                0,
            ],

            "iz_confirmation_position": [
                0,
            ],

            "iz_origin_time": [
                pd.Timestamp(
                    "2026-08-13 10:59:00"
                ),
            ],

            "iz_confirmation_time": [
                pd.Timestamp(
                    "2026-08-13 11:00:00"
                ),
            ],

            "iz_zone_high": [
                101.0,
            ],

            "iz_zone_low": [
                100.0,
            ],

            "iz_live_safe": [
                1,
            ],
        }
    )


def test_confirmation_row_is_fresh() -> None:

    result = Lifecycle.generate(
        _bullish_market(),
        _bullish_event(),
    )

    first = result.iloc[
        0
    ]

    assert (
        first[
            "izl_state"
        ]
        ==
        "FRESH"
    )

    assert int(
        first[
            "izl_age_bars"
        ]
    ) == 0

    assert int(
        first[
            "izl_overlap_flag"
        ]
    ) == 0

    assert int(
        first[
            "izl_touch_count"
        ]
    ) == 0


def test_bullish_zone_stays_fresh_before_touch() -> None:

    result = Lifecycle.generate(
        _bullish_market(),
        _bullish_event(),
    )

    row = result.loc[
        result[
            "izl_observation_position"
        ].eq(
            1
        )
    ].iloc[
        0
    ]

    assert (
        row[
            "izl_state"
        ]
        ==
        "FRESH"
    )


def test_bullish_zone_becomes_mitigated() -> None:

    result = Lifecycle.generate(
        _bullish_market(),
        _bullish_event(),
    )

    row = result.loc[
        result[
            "izl_observation_position"
        ].eq(
            2
        )
    ].iloc[
        0
    ]

    assert (
        row[
            "izl_state"
        ]
        ==
        "MITIGATED"
    )

    assert int(
        row[
            "izl_touch_count"
        ]
    ) == 1

    assert int(
        row[
            "izl_mitigated_flag"
        ]
    ) == 1


def test_bullish_zone_becomes_accepted() -> None:

    result = Lifecycle.generate(
        _bullish_market(),
        _bullish_event(),
    )

    row = result.loc[
        result[
            "izl_observation_position"
        ].eq(
            3
        )
    ].iloc[
        0
    ]

    assert (
        row[
            "izl_state"
        ]
        ==
        "ACCEPTED"
    )

    assert int(
        row[
            "izl_accepted_flag"
        ]
    ) == 1


def test_bullish_zone_can_later_invalidate() -> None:

    result = Lifecycle.generate(
        _bullish_market(),
        _bullish_event(),
    )

    final = result.iloc[
        -1
    ]

    assert (
        final[
            "izl_state"
        ]
        ==
        "INVALIDATED"
    )

    assert int(
        final[
            "izl_terminal_flag"
        ]
    ) == 1


def test_bearish_lifecycle() -> None:

    result = Lifecycle.generate(
        _bearish_market(),
        _bearish_event(),
    )

    states = dict(
        zip(
            result[
                "izl_observation_position"
            ].astype(
                int
            ),

            result[
                "izl_state"
            ],
        )
    )

    assert states[
        0
    ] == "FRESH"

    assert states[
        1
    ] == "FRESH"

    assert states[
        2
    ] == "MITIGATED"

    assert states[
        3
    ] == "ACCEPTED"

    assert states[
        4
    ] == "INVALIDATED"


def test_prefix_invariance() -> None:

    full_market = (
        _bullish_market()
    )

    prefix_market = (
        full_market.iloc[
            :4
        ].copy()
    )

    prefix = Lifecycle.generate(
        prefix_market,
        _bullish_event(),
    )

    full = Lifecycle.generate(
        full_market,
        _bullish_event(),
    )

    comparable = (
        full.loc[
            pd.to_numeric(
                full[
                    "izl_observation_position"
                ],
                errors="coerce",
            )
            .le(
                3
            )
        ]
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


def test_future_mutation_does_not_change_earlier_states() -> None:

    baseline = (
        _bullish_market()
    )

    changed = baseline.copy(
        deep=True
    )

    changed.loc[
        4,
        [
            "open",
            "high",
            "low",
            "close",
        ],
    ] = [
        150.0,
        155.0,
        145.0,
        152.0,
    ]

    first = Lifecycle.generate(
        baseline.iloc[
            :4
        ],
        _bullish_event(),
    )

    second = Lifecycle.generate(
        changed,
        _bullish_event(),
    )

    second_early = (
        second.loc[
            pd.to_numeric(
                second[
                    "izl_observation_position"
                ],
                errors="coerce",
            )
            .le(
                3
            )
        ]
        .reset_index(
            drop=True
        )
    )

    pd.testing.assert_frame_equal(
        first.reset_index(
            drop=True
        ),
        second_early,
    )


def test_hindsight_columns_are_rejected() -> None:

    events = _bullish_event()

    events[
        "izlabel_future_state"
    ] = "GOOD"

    with pytest.raises(
        ValueError,
        match="izlabel",
    ):

        Lifecycle.generate(
            _bullish_market(),
            events,
        )


def test_non_live_safe_zone_is_rejected() -> None:

    events = (
        _bullish_event()
    )

    events.loc[
        0,
        "iz_live_safe",
    ] = 0

    with pytest.raises(
        ValueError,
        match="iz_live_safe",
    ):

        Lifecycle.generate(
            _bullish_market(),
            events,
        )


def test_inputs_are_not_mutated() -> None:

    market = (
        _bullish_market()
    )

    events = (
        _bullish_event()
    )

    market_before = market.copy(
        deep=True
    )

    events_before = events.copy(
        deep=True
    )

    _ = Lifecycle.generate(
        market,
        events,
    )

    pd.testing.assert_frame_equal(
        market,
        market_before,
    )

    pd.testing.assert_frame_equal(
        events,
        events_before,
    )


def test_latest_snapshot_returns_one_row_per_zone() -> None:

    bullish = Lifecycle.generate(
        _bullish_market(),
        _bullish_event(),
    )

    bearish = Lifecycle.generate(
        _bearish_market(),
        _bearish_event(),
    )

    combined = pd.concat(
        [
            bullish,
            bearish,
        ],
        ignore_index=True,
    )

    snapshot = (
        Lifecycle.latest_snapshot(
            combined
        )
    )

    assert len(
        snapshot
    ) == 2

    assert set(
        snapshot[
            "izl_state"
        ]
    ) == {
        "INVALIDATED",
    }