"""
Offline causal-safety tests for InstitutionalZonesEngine v2.0.
"""

from __future__ import annotations

import importlib
from typing import Any

import pandas as pd
import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Core.institutional_zones"
)

Engine: Any = (
    module.InstitutionalZonesEngine
)


def _engine() -> Any:

    return Engine(
        {
            "lookahead": 3,
            "merge_overlapping": False,
            "max_zones": 100,
        }
    )


def _bullish_data() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "time": pd.date_range(
                "2026-08-13 10:00:00+00:00",
                periods=6,
                freq="min",
            ),

            "open": [
                100.0,
                99.0,
                103.0,
                103.5,
                103.2,
                103.3,
            ],

            "high": [
                101.0,
                104.0,
                104.0,
                104.0,
                103.8,
                103.9,
            ],

            "low": [
                98.0,
                99.0,
                102.0,
                102.8,
                102.9,
                103.0,
            ],

            "close": [
                99.0,
                103.0,
                103.5,
                103.2,
                103.3,
                103.4,
            ],
        }
    )


def _bearish_data() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "time": pd.date_range(
                "2026-08-13 11:00:00+00:00",
                periods=6,
                freq="min",
            ),

            "open": [
                100.0,
                101.0,
                97.0,
                96.8,
                97.0,
                96.9,
            ],

            "high": [
                102.0,
                101.0,
                98.0,
                97.4,
                97.5,
                97.3,
            ],

            "low": [
                99.0,
                96.0,
                96.0,
                96.2,
                96.5,
                96.4,
            ],

            "close": [
                101.0,
                97.0,
                96.8,
                97.0,
                96.9,
                96.8,
            ],
        }
    )


def test_generate_is_causal_alias() -> None:

    engine = _engine()

    result = engine.generate(
        _bullish_data()
    )

    assert not result.empty

    assert bool(
        result[
            "iz_live_safe"
        ]
        .eq(
            1
        )
        .all()
    )

    assert bool(
        result[
            "iz_mode"
        ]
        .eq(
            engine.CAUSAL_MODE
        )
        .all()
    )


def test_bullish_zone_emitted_after_origin() -> None:

    result = _engine().generate(
        _bullish_data()
    )

    bullish = result.loc[
        result[
            "iz_direction"
        ].eq(
            "BULLISH"
        )
        &
        result[
            "iz_origin_position"
        ].eq(
            0
        )
    ]

    assert len(
        bullish
    ) == 1

    row = bullish.iloc[
        0
    ]

    assert int(
        row[
            "iz_confirmation_position"
        ]
    ) > int(
        row[
            "iz_origin_position"
        ]
    )

    assert int(
        row[
            "iz_confirmation_delay_bars"
        ]
    ) >= 1

    assert float(
        row[
            "iz_zone_high"
        ]
    ) == pytest.approx(
        100.0
    )

    assert float(
        row[
            "iz_zone_low"
        ]
    ) == pytest.approx(
        98.0
    )


def test_bearish_zone_emitted_after_origin() -> None:

    result = _engine().generate(
        _bearish_data()
    )

    bearish = result.loc[
        result[
            "iz_direction"
        ].eq(
            "BEARISH"
        )
        &
        result[
            "iz_origin_position"
        ].eq(
            0
        )
    ]

    assert len(
        bearish
    ) == 1

    row = bearish.iloc[
        0
    ]

    assert int(
        row[
            "iz_confirmation_position"
        ]
    ) > 0

    assert float(
        row[
            "iz_zone_high"
        ]
    ) == pytest.approx(
        102.0
    )

    assert float(
        row[
            "iz_zone_low"
        ]
    ) == pytest.approx(
        100.0
    )


def test_origin_alone_cannot_form_causal_zone() -> None:

    frame = (
        _bullish_data()
        .iloc[
            :1
        ]
        .copy()
    )

    result = _engine().generate(
        frame
    )

    assert result.empty


def test_prefix_invariance() -> None:
    """
    Adding future candles must not rewrite already-confirmed causal events.
    """

    engine = _engine()

    full = _bullish_data()

    prefix = full.iloc[
        :3
    ].copy()

    prefix_events = (
        engine.generate(
            prefix
        )
        .sort_values(
            "iz_event_id"
        )
        .reset_index(
            drop=True
        )
    )

    full_events = engine.generate(
        full
    )

    comparable = (
        full_events.loc[
            pd.to_numeric(
                full_events[
                    "iz_confirmation_position"
                ],
                errors="coerce",
            )
            .le(
                2
            )
        ]
        .sort_values(
            "iz_event_id"
        )
        .reset_index(
            drop=True
        )
    )

    pd.testing.assert_frame_equal(
        prefix_events,
        comparable,
    )


def test_future_mutation_does_not_change_earlier_event() -> None:

    engine = _engine()

    baseline = _bullish_data()

    changed = baseline.copy(
        deep=True
    )

    # Mutate only candles well after the first confirmation.
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
        160.0,
        140.0,
        155.0,
    ]

    changed.loc[
        5,
        [
            "open",
            "high",
            "low",
            "close",
        ],
    ] = [
        155.0,
        170.0,
        130.0,
        135.0,
    ]

    first = engine.generate(
        baseline
    )

    second = engine.generate(
        changed
    )

    first_event = (
        first.loc[
            first[
                "iz_origin_position"
            ].eq(
                0
            )
        ]
        .iloc[
            0
        ]
    )

    second_event = (
        second.loc[
            second[
                "iz_origin_position"
            ].eq(
                0
            )
        ]
        .iloc[
            0
        ]
    )

    columns = [
        "iz_event_id",
        "iz_direction",
        "iz_zone_type",
        "iz_origin_position",
        "iz_confirmation_position",
        "iz_zone_high",
        "iz_zone_low",
        "iz_displacement_score",
        "iz_strength",
    ]

    for column in columns:

        assert (
            first_event[
                column
            ]
            ==
            second_event[
                column
            ]
        )


def test_causal_output_contains_no_hindsight_label_columns() -> None:

    result = _engine().generate(
        _bullish_data()
    )

    assert not any(
        str(
            column
        ).startswith(
            "izlabel_"
        )
        for column
        in result.columns
    )


def test_generate_research_is_explicitly_hindsight() -> None:

    result = (
        _engine()
        .generate_research(
            _bullish_data()
        )
    )

    assert not result.empty

    assert all(
        str(
            column
        ).startswith(
            "izlabel_"
        )
        for column
        in result.columns
    )

    assert bool(
        result[
            "izlabel_live_safe"
        ]
        .eq(
            0
        )
        .all()
    )


def test_detect_remains_retrospective_compatibility_path() -> None:

    result = _engine().detect(
        _bullish_data()
    )

    assert not result.empty

    bullish = result.loc[
        result[
            "direction"
        ].eq(
            "BULLISH"
        )
    ]

    assert not bullish.empty


def test_confirmation_must_respect_max_delay() -> None:

    frame = pd.DataFrame(
        {
            "time": pd.date_range(
                "2026-08-13 12:00:00+00:00",
                periods=5,
                freq="min",
            ),

            "open": [
                100.0,
                99.0,
                99.1,
                99.2,
                99.3,
            ],

            "high": [
                101.0,
                99.5,
                99.6,
                99.7,
                105.0,
            ],

            "low": [
                98.0,
                98.8,
                98.9,
                99.0,
                99.2,
            ],

            "close": [
                99.0,
                99.1,
                99.2,
                99.3,
                104.0,
            ],
        }
    )

    result = _engine().generate(
        frame
    )

    # Origin 0 is allowed max 3 bars.
    # Strong displacement arrives at bar 4, therefore origin 0 must never
    # suddenly become a causal event.
    origin_zero = result.loc[
        result[
            "iz_origin_position"
        ].eq(
            0
        )
    ]

    assert origin_zero.empty


def test_input_dataframe_is_not_mutated() -> None:

    frame = _bullish_data()

    original = frame.copy(
        deep=True
    )

    _ = _engine().generate(
        frame
    )

    pd.testing.assert_frame_equal(
        frame,
        original,
    )


def test_trade_ready_input_is_not_modified() -> None:

    frame = _bullish_data()

    frame[
        "trade_ready"
    ] = [
        0,
        1,
        0,
        1,
        0,
        0,
    ]

    before = frame[
        "trade_ready"
    ].copy()

    _ = _engine().generate(
        frame
    )

    pd.testing.assert_series_equal(
        before,
        frame[
            "trade_ready"
        ],
    )