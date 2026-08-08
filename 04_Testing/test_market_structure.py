from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np
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


# =============================================================================
# Helpers
# =============================================================================

def _frame(
    high,
    low,
    close,
    atr=None,
):

    size = len(
        high
    )

    data = {
        "open": close,
        "high": high,
        "low": low,
        "close": close,
    }

    if atr is not None:

        data["atr"] = atr

    return pd.DataFrame(
        data
    )


def _engine():

    return MarketStructure(
        reversal_atr=0.55,
        min_swing_atr=0.80,
        internal_swing_atr=1.50,
        major_swing_atr=2.50,
    )


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
    column,
):

    df = _frame(
        high=[
            101,
            102,
        ],
        low=[
            99,
            100,
        ],
        close=[
            100,
            101,
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
# Output Contract
# =============================================================================

def test_generate_exposes_v6_contract():

    df = _frame(
        high=[
            100,
            101,
            103,
            102,
            101,
        ],
        low=[
            99,
            100,
            102,
            101,
            100,
        ],
        close=[
            99.5,
            100.8,
            102.8,
            101.5,
            100.5,
        ],
    )

    result = _engine().generate(
        df
    )

    required = {
        "atr",

        "pivot_high",
        "pivot_low",
        "pivot_strength",

        "minor_high",
        "minor_low",

        "major_high",
        "major_low",
        "major_swing",

        "micro_high",
        "micro_low",

        "internal_high",
        "internal_low",

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
# Short Swing
# =============================================================================

def test_detects_short_variable_length_swing():

    df = _frame(
        high=[
            100.0,
            101.0,
            103.0,
            102.0,
            101.0,
        ],
        low=[
            99.0,
            100.0,
            102.0,
            101.0,
            100.0,
        ],
        close=[
            99.5,
            100.8,
            102.8,
            101.5,
            100.5,
        ],
        atr=[
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
        ],
    )

    result = _engine().detect_swings(
        df
    )

    swings = result[
        result["swing_id"] > 0
    ]

    assert len(swings) >= 2

    first = swings.iloc[0]

    assert (
        first["swing_type"]
        == "LOW"
    )

    assert (
        first["swing_price"]
        == pytest.approx(
            99.0
        )
    )

    second = swings.iloc[1]

    assert (
        second["swing_type"]
        == "HIGH"
    )

    assert (
        second["swing_price"]
        == pytest.approx(
            103.0
        )
    )


# =============================================================================
# Candidate Extreme Replacement
# =============================================================================

def test_higher_high_replaces_old_candidate():

    df = _frame(
        high=[
            100.0,
            101.0,
            103.0,
            105.0,
            104.0,
        ],
        low=[
            99.0,
            100.0,
            101.0,
            103.0,
            102.0,
        ],
        close=[
            99.5,
            100.8,
            102.7,
            104.5,
            103.0,
        ],
        atr=[
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
        ],
    )

    result = _engine().detect_swings(
        df
    )

    highs = result[
        result["swing_type"]
        == "HIGH"
    ]

    assert len(highs) >= 1

    high = highs.iloc[0]

    assert (
        high["swing_price"]
        == pytest.approx(
            105.0
        )
    )

    assert (
        int(
            high[
                "swing_origin_index"
            ]
        )
        == 3
    )


# =============================================================================
# Causal Confirmation
# =============================================================================

def test_swing_is_written_on_confirmation_not_origin():

    df = _frame(
        high=[
            100.0,
            101.0,
            103.0,
            102.0,
        ],
        low=[
            99.0,
            100.0,
            102.0,
            101.0,
        ],
        close=[
            99.5,
            100.8,
            102.8,
            101.5,
        ],
        atr=[
            1.0,
            1.0,
            1.0,
            1.0,
        ],
    )

    result = _engine().detect_swings(
        df
    )

    swings = result[
        result["swing_id"] > 0
    ]

    assert len(swings) > 0

    for (
        confirmation_row,
        row,
    ) in swings.iterrows():

        assert (
            int(
                row[
                    "swing_origin_index"
                ]
            )
            <
            int(
                row[
                    "swing_confirmation_index"
                ]
            )
        )

        assert (
            int(
                row[
                    "swing_confirmation_index"
                ]
            )
            == confirmation_row
        )


# =============================================================================
# Strict Alternation
# =============================================================================

def test_confirmed_swings_strictly_alternate():

    df = _frame(
        high=[
            100,
            101,
            104,
            102,
            101,
            100,
            103,
            105,
            103,
            101,
            100,
            103,
        ],
        low=[
            99,
            100,
            102,
            100,
            98,
            97,
            100,
            103,
            101,
            99,
            97,
            100,
        ],
        close=[
            99.5,
            100.8,
            103.5,
            101.0,
            99.0,
            97.5,
            102.0,
            104.5,
            102.0,
            100.0,
            97.5,
            102.5,
        ],
        atr=[
            1.0
        ] * 12,
    )

    result = _engine().detect_swings(
        df
    )

    types = (
        result.loc[
            result["swing_id"] > 0,
            "swing_type",
        ]
        .tolist()
    )

    assert len(types) >= 3

    for previous, current in zip(
        types,
        types[1:],
    ):

        assert (
            previous
            != current
        )


# =============================================================================
# No Fixed Candle Count
# =============================================================================

def test_long_leg_can_extend_until_reversal():

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
        111.0,
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
        109.0,
    ]

    close = [
        99.5,
        100.8,
        101.8,
        102.8,
        103.8,
        104.8,
        105.8,
        106.8,
        107.8,
        108.8,
        109.8,
        110.8,
        111.8,
        109.5,
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

    result = _engine().detect_swings(
        df
    )

    highs = result[
        result["swing_type"]
        == "HIGH"
    ]

    assert len(highs) >= 1

    high_event = (
        highs.iloc[0]
    )

    assert (
        high_event[
            "swing_price"
        ]
        == pytest.approx(
            112.0
        )
    )

    # Engine allowed a long leg;
    # it did not force a five-candle pivot.
    assert (
        int(
            high_event[
                "swing_leg_bars"
            ]
        )
        >= 5
    )


# =============================================================================
# Hierarchy
# =============================================================================

def test_large_excursion_becomes_major_swing():

    df = _frame(
        high=[
            100.0,
            101.0,
            103.5,
            102.0,
        ],
        low=[
            99.0,
            100.0,
            102.0,
            101.0,
        ],
        close=[
            99.5,
            100.8,
            103.2,
            101.8,
        ],
        atr=[
            1.0,
            1.0,
            1.0,
            1.0,
        ],
    )

    result = _engine().detect_swings(
        df
    )

    highs = result[
        result["swing_type"]
        == "HIGH"
    ]

    assert len(highs) == 1

    event = highs.iloc[0]

    assert (
        event["swing_scale"]
        == "MAJOR"
    )

    assert (
        event["major_high"]
        == 1
    )


# =============================================================================
# HH / HL / LH / LL
# =============================================================================

def test_structure_uses_confirmed_swing_prices():

    engine = _engine()

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

    assert result.loc[
        2,
        "HH",
    ] == 1

    assert result.loc[
        3,
        "HL",
    ] == 1

    assert result.loc[
        4,
        "LH",
    ] == 1

    assert result.loc[
        5,
        "LL",
    ] == 1


# =============================================================================
# Stable Bias
# =============================================================================

def test_bias_requires_high_and_low_confirmation():

    engine = _engine()

    df = pd.DataFrame(
        {
            "structure": [
                "NONE",
                "HH",
                "NONE",
                "HL",
                "NONE",
                "LH",
                "NONE",
                "LL",
            ]
        }
    )

    result = (
        engine.add_structure_state(
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

    # A single LH alone does not instantly
    # destroy established bullish structure.
    assert (
        result.loc[
            5,
            "structure_bias",
        ]
        == "BULLISH"
    )

    assert (
        result.loc[
            7,
            "structure_bias",
        ]
        == "BEARISH"
    )