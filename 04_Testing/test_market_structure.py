from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pandas as pd
import pytest


ROOT_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(ROOT_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


module = importlib.import_module(
    "02_AI.Core.market_structure"
)

MarketStructure = (
    module.MarketStructure
)


def _engine() -> MarketStructure:

    return MarketStructure(
        reversal_atr=0.55,
        min_swing_atr=0.80,
        internal_swing_atr=1.50,
        major_swing_atr=2.50,
    )


def _frame(
    high: list[float],
    low: list[float],
    close: list[float],
    atr: list[float] | None = None,
) -> pd.DataFrame:

    df = pd.DataFrame(
        {
            "open": close,
            "high": high,
            "low": low,
            "close": close,
        }
    )

    if atr is not None:

        df["atr"] = atr

    return df


# =============================================================================
# Validation
# =============================================================================

@pytest.mark.parametrize(
    "column",
    [
        "open",
        "high",
        "low",
        "close",
    ],
)
def test_missing_ohlc_raises(
    column: str,
):

    df = _frame(
        high=[
            101.0,
            102.0,
        ],
        low=[
            99.0,
            100.0,
        ],
        close=[
            100.0,
            101.0,
        ],
    ).drop(
        columns=[
            column
        ]
    )

    with pytest.raises(
        ValueError
    ):

        _engine().generate(
            df
        )


# =============================================================================
# Contract
# =============================================================================

def test_generate_exposes_v61_contract():

    df = _frame(
        high=[
            100.0,
            102.0,
            102.0,
            101.0,
        ],
        low=[
            99.0,
            101.0,
            100.5,
            99.5,
        ],
        close=[
            99.5,
            101.5,
            101.0,
            100.0,
        ],
    )

    result = (
        _engine()
        .generate(
            df
        )
    )

    required = {
        "atr",
        "pivot_high",
        "pivot_low",
        "pivot_strength",
        "micro_high",
        "micro_low",
        "internal_high",
        "internal_low",
        "major_high",
        "major_low",
        "major_swing",
        "minor_high",
        "minor_low",
        "swing_id",
        "swing_type",
        "swing_price",
        "swing_score",
        "swing_scale",
        "swing_origin_index",
        "swing_confirmation_index",
        "swing_origin_time",
        "swing_confirmation_time",
        "swing_leg_bars",
        "swing_confirmation_bars",
        "swing_excursion",
        "swing_excursion_atr",
        "swing_reversal",
        "swing_reversal_atr",
        "HH",
        "HL",
        "LH",
        "LL",
        "structure",
        "structure_bias",
        "last_swing_high",
        "last_swing_low",
        "last_major_high",
        "last_major_low",
    }

    assert required.issubset(
        result.columns
    )


# =============================================================================
# Bootstrap causality
# =============================================================================

def test_initial_low_then_high_confirms_low_first():

    df = _frame(
        high=[
            100.0,
            102.0,
            102.0,
        ],
        low=[
            99.0,
            101.0,
            100.5,
        ],
        close=[
            99.5,
            101.5,
            101.0,
        ],
        atr=[
            1.0,
            1.0,
            1.0,
        ],
    )

    result = (
        _engine()
        .detect_swings(
            df
        )
    )

    swings = result[
        result["swing_id"] > 0
    ]

    assert len(
        swings
    ) >= 1

    first = swings.iloc[
        0
    ]

    assert (
        first[
            "swing_type"
        ]
        == "LOW"
    )

    assert (
        first[
            "swing_price"
        ]
        == pytest.approx(
            99.0
        )
    )


# =============================================================================
# Regression: v6.0 state-lock bug
# =============================================================================

def test_shallow_valid_pullback_does_not_freeze_state_machine():

    """
    HIGH -> pullback is only 0.65 ATR.

    v6.0 required:
        reversal >= 0.55 ATR
        AND leg >= 0.80 ATR

    so this LOW could never confirm and the state machine could freeze.

    v6.1 must confirm it because reversal threshold is the causal
    swing-confirmation rule.
    """

    df = _frame(
        high=[
            100.0,
            102.0,
            102.1,
            102.0,
            102.2,
            102.1,
        ],
        low=[
            99.0,
            101.0,
            101.4,
            101.45,
            101.5,
            101.4,
        ],
        close=[
            99.5,
            101.7,
            101.8,
            101.6,
            102.0,
            101.8,
        ],
        atr=[
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
        ],
    )

    result = (
        _engine()
        .detect_swings(
            df
        )
    )

    swings = result[
        result["swing_id"] > 0
    ].reset_index(
        drop=True
    )

    assert len(
        swings
    ) >= 3

    assert (
        swings.loc[
            0,
            "swing_type",
        ]
        == "LOW"
    )

    assert (
        swings.loc[
            1,
            "swing_type",
        ]
        == "HIGH"
    )

    assert (
        swings.loc[
            2,
            "swing_type",
        ]
        == "LOW"
    )

    # This leg is deliberately smaller than min_swing_atr=0.80.
    assert (
        swings.loc[
            2,
            "swing_excursion_atr",
        ]
        < 0.80
    )


# =============================================================================
# Candidate replacement
# =============================================================================

def test_higher_high_replaces_candidate_before_confirmation():

    df = _frame(
        high=[
            100.0,
            102.0,
            103.0,
            105.0,
            104.5,
        ],
        low=[
            99.0,
            101.0,
            102.0,
            104.0,
            103.0,
        ],
        close=[
            99.5,
            101.5,
            102.5,
            104.5,
            103.5,
        ],
        atr=[
            1.0
        ] * 5,
    )

    result = (
        _engine()
        .detect_swings(
            df
        )
    )

    highs = result[
        result[
            "swing_type"
        ]
        == "HIGH"
    ]

    assert not highs.empty

    event = highs.iloc[
        0
    ]

    assert (
        event[
            "swing_price"
        ]
        == pytest.approx(
            105.0
        )
    )

    assert (
        int(
            event[
                "swing_origin_index"
            ]
        )
        == 3
    )


# =============================================================================
# Confirmation row
# =============================================================================

def test_event_is_emitted_on_confirmation_row_not_origin():

    df = _frame(
        high=[
            100.0,
            102.0,
            103.0,
            102.5,
        ],
        low=[
            99.0,
            101.0,
            102.0,
            101.5,
        ],
        close=[
            99.5,
            101.5,
            102.7,
            102.0,
        ],
        atr=[
            1.0
        ] * 4,
    )

    result = (
        _engine()
        .detect_swings(
            df
        )
    )

    swings = result[
        result["swing_id"] > 0
    ]

    assert not swings.empty

    for (
        confirmation_row,
        event,
    ) in swings.iterrows():

        assert (
            int(
                event[
                    "swing_origin_index"
                ]
            )
            <
            int(
                event[
                    "swing_confirmation_index"
                ]
            )
        )

        assert (
            int(
                event[
                    "swing_confirmation_index"
                ]
            )
            == confirmation_row
        )


# =============================================================================
# Strict alternating sequence
# =============================================================================

def test_confirmed_swings_strictly_alternate():

    df = _frame(
        high=[
            100.0,
            103.0,
            102.5,
            100.5,
            101.0,
            104.0,
            103.5,
            101.0,
            101.5,
        ],
        low=[
            99.0,
            102.0,
            101.0,
            98.0,
            99.0,
            103.0,
            102.0,
            99.0,
            100.0,
        ],
        close=[
            99.5,
            102.5,
            101.5,
            98.5,
            100.0,
            103.5,
            102.5,
            99.5,
            101.0,
        ],
        atr=[
            1.0
        ] * 9,
    )

    result = (
        _engine()
        .detect_swings(
            df
        )
    )

    types = result.loc[
        result["swing_id"] > 0,
        "swing_type",
    ].tolist()

    assert len(
        types
    ) >= 4

    for (
        previous,
        current,
    ) in zip(
        types,
        types[1:],
    ):

        assert (
            previous
            != current
        )


# =============================================================================
# Variable duration
# =============================================================================

def test_long_leg_is_not_forced_into_fixed_window():

    high = [
        100.0,
        101.0,
        102.0,
        103.0,
        104.0,
        105.0,
        106.0,
        107.0,
        108.0,
        109.0,
        110.0,
        111.0,
        112.0,
        111.5,
    ]

    low = [
        99.0,
        100.0,
        101.0,
        102.0,
        103.0,
        104.0,
        105.0,
        106.0,
        107.0,
        108.0,
        109.0,
        110.0,
        111.0,
        110.0,
    ]

    close = [
        99.5,
        100.7,
        101.7,
        102.7,
        103.7,
        104.7,
        105.7,
        106.7,
        107.7,
        108.7,
        109.7,
        110.7,
        111.7,
        110.5,
    ]

    df = _frame(
        high=high,
        low=low,
        close=close,
        atr=[
            1.0
        ] * len(
            high
        ),
    )

    result = (
        _engine()
        .detect_swings(
            df
        )
    )

    highs = result[
        result[
            "swing_type"
        ]
        == "HIGH"
    ]

    assert not highs.empty

    high_event = highs.iloc[
        0
    ]

    assert (
        high_event[
            "swing_price"
        ]
        == pytest.approx(
            112.0
        )
    )

    assert (
        int(
            high_event[
                "swing_origin_index"
            ]
        )
        >= 10
    )


# =============================================================================
# Hierarchy
# =============================================================================

def test_large_leg_is_classified_major():

    df = _frame(
        high=[
            100.0,
            104.0,
            104.0,
        ],
        low=[
            99.0,
            103.0,
            102.5,
        ],
        close=[
            99.5,
            103.5,
            103.0,
        ],
        atr=[
            1.0,
            1.0,
            1.0,
        ],
    )

    result = (
        _engine()
        .detect_swings(
            df
        )
    )

    swings = result[
        result["swing_id"] > 0
    ]

    assert not swings.empty

    # First low reversal itself moved many ATR.
    event = swings.iloc[
        0
    ]

    assert (
        event[
            "swing_scale"
        ]
        == "MAJOR"
    )


# =============================================================================
# Structure uses actual swing_price
# =============================================================================

def test_structure_uses_swing_price():

    engine = (
        _engine()
    )

    df = pd.DataFrame(
        {
            "swing_id": [
                1,
                2,
                3,
                4,
                5,
                6,
            ],

            "swing_type": [
                "HIGH",
                "LOW",
                "HIGH",
                "LOW",
                "HIGH",
                "LOW",
            ],

            "swing_price": [
                100.0,
                90.0,
                110.0,
                95.0,
                105.0,
                85.0,
            ],

            "major_high": [
                1,
                0,
                1,
                0,
                1,
                0,
            ],

            "major_low": [
                0,
                1,
                0,
                1,
                0,
                1,
            ],
        }
    )

    result = (
        engine.detect_structure(
            df
        )
    )

    assert (
        result.loc[
            2,
            "HH",
        ]
        == 1
    )

    assert (
        result.loc[
            3,
            "HL",
        ]
        == 1
    )

    assert (
        result.loc[
            4,
            "LH",
        ]
        == 1
    )

    assert (
        result.loc[
            5,
            "LL",
        ]
        == 1
    )


# =============================================================================
# Bias
# =============================================================================

def test_structure_bias_requires_high_and_low_relationship():

    df = pd.DataFrame(
        {
            "structure": [
                "NONE",
                "HH",
                "NONE",
                "HL",
                "LH",
                "NONE",
                "LL",
            ]
        }
    )

    result = (
        _engine()
        .add_structure_state(
            df
        )
    )

    assert (
        result.loc[
            1,
            "structure_bias",
        ]
        == "NEUTRAL"
    )

    assert (
        result.loc[
            3,
            "structure_bias",
        ]
        == "BULLISH"
    )

    assert (
        result.loc[
            4,
            "structure_bias",
        ]
        == "BULLISH"
    )

    assert (
        result.loc[
            6,
            "structure_bias",
        ]
        == "BEARISH"
    )


# =============================================================================
# Invalid ATR
# =============================================================================

def test_invalid_atr_does_not_create_false_swings():

    df = _frame(
        high=[
            100.0,
            110.0,
            90.0,
        ],
        low=[
            99.0,
            80.0,
            70.0,
        ],
        close=[
            99.5,
            90.0,
            80.0,
        ],
        atr=[
            0.0,
            0.0,
            0.0,
        ],
    )

    result = (
        _engine()
        .detect_swings(
            df
        )
    )

    assert (
        result[
            "swing_id"
        ].sum()
        == 0
    )