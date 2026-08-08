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
    "02_AI.Core.bos_engine"
)

BOSEngine = (
    module.BOSEngine
)


# =============================================================================
# Helper
# =============================================================================

def _frame(
    close,
    swing_id,
    swing_type,
    swing_price,
    swing_scale,
    atr=None,
    structure_bias=None,
    confirmation_index=None,
):

    size = len(
        close
    )

    if atr is None:

        atr = [
            1.0
        ] * size

    if structure_bias is None:

        structure_bias = [
            "NEUTRAL"
        ] * size

    if confirmation_index is None:

        confirmation_index = list(
            range(
                size
            )
        )

    return pd.DataFrame(
        {
            "close": (
                close
            ),
            "atr": (
                atr
            ),
            "swing_id": (
                swing_id
            ),
            "swing_type": (
                swing_type
            ),
            "swing_price": (
                swing_price
            ),
            "swing_scale": (
                swing_scale
            ),
            "structure_bias": (
                structure_bias
            ),
            "swing_confirmation_index": (
                confirmation_index
            ),
        }
    )


# =============================================================================
# Output Contract
# =============================================================================

def test_bos_v3_contract():

    df = _frame(
        close=[
            99.0,
            101.0,
        ],
        swing_id=[
            1,
            0,
        ],
        swing_type=[
            "HIGH",
            "NONE",
        ],
        swing_price=[
            100.0,
            float("nan"),
        ],
        swing_scale=[
            "MICRO",
            "NONE",
        ],
    )

    result = (
        BOSEngine()
        .generate(
            df
        )
    )

    required = {
        "bos_id",
        "bullish_bos",
        "bearish_bos",
        "bos_direction",
        "bos_price",
        "bos_strength",
        "bos_strength_atr",
        "bos_active",
        "bos_confirmed",
        "bos_invalidated",
        "broken_swing_id",
        "broken_swing_scale",
        "broken_swing_confirmation_index",
        "break_index",
        "break_time",
        "break_distance",
        "break_distance_atr",
        "bos_scope",
        "bos_context",
        "micro_bos",
        "internal_bos",
        "major_bos",
    }

    assert required.issubset(
        result.columns
    )


# =============================================================================
# Bullish BOS
# =============================================================================

def test_bullish_bos_breaks_confirmed_high():

    df = _frame(
        close=[
            99.0,
            100.02,
            100.20,
        ],
        swing_id=[
            11,
            0,
            0,
        ],
        swing_type=[
            "HIGH",
            "NONE",
            "NONE",
        ],
        swing_price=[
            100.0,
            float("nan"),
            float("nan"),
        ],
        swing_scale=[
            "INTERNAL",
            "NONE",
            "NONE",
        ],
        structure_bias=[
            "BULLISH",
            "BULLISH",
            "BULLISH",
        ],
    )

    result = (
        BOSEngine(
            break_buffer_atr=0.05
        )
        .generate(
            df
        )
    )

    # 0.02 ATR break is too small.
    assert (
        result.loc[
            1,
            "bullish_bos",
        ]
        == 0
    )

    assert (
        result.loc[
            2,
            "bullish_bos",
        ]
        == 1
    )

    assert (
        result.loc[
            2,
            "bos_price",
        ]
        == pytest.approx(
            100.0
        )
    )

    assert (
        result.loc[
            2,
            "broken_swing_id",
        ]
        == 11
    )

    assert (
        result.loc[
            2,
            "bos_scope",
        ]
        == "INTERNAL"
    )

    assert (
        result.loc[
            2,
            "internal_bos",
        ]
        == 1
    )

    assert (
        result.loc[
            2,
            "bos_context",
        ]
        == "CONTINUATION"
    )


# =============================================================================
# Bearish BOS
# =============================================================================

def test_bearish_bos_breaks_confirmed_low():

    df = _frame(
        close=[
            101.0,
            99.80,
        ],
        swing_id=[
            21,
            0,
        ],
        swing_type=[
            "LOW",
            "NONE",
        ],
        swing_price=[
            100.0,
            float("nan"),
        ],
        swing_scale=[
            "MICRO",
            "NONE",
        ],
        structure_bias=[
            "BULLISH",
            "BULLISH",
        ],
    )

    result = (
        BOSEngine()
        .generate(
            df
        )
    )

    assert (
        result.loc[
            1,
            "bearish_bos",
        ]
        == 1
    )

    assert (
        result.loc[
            1,
            "bos_scope",
        ]
        == "MICRO"
    )

    assert (
        result.loc[
            1,
            "micro_bos",
        ]
        == 1
    )

    # Bearish break while bias was bullish.
    assert (
        result.loc[
            1,
            "bos_context",
        ]
        == "REVERSAL"
    )


# =============================================================================
# Causality
# =============================================================================

def test_new_swing_cannot_break_on_own_confirmation_candle():

    df = _frame(
        close=[
            101.0,
            101.0,
        ],
        swing_id=[
            31,
            0,
        ],
        swing_type=[
            "HIGH",
            "NONE",
        ],
        swing_price=[
            100.0,
            float("nan"),
        ],
        swing_scale=[
            "MICRO",
            "NONE",
        ],
    )

    result = (
        BOSEngine()
        .generate(
            df
        )
    )

    # Swing becomes known only at end of row 0.
    assert (
        result.loc[
            0,
            "bullish_bos",
        ]
        == 0
    )

    # Next candle may legitimately break it.
    assert (
        result.loc[
            1,
            "bullish_bos",
        ]
        == 1
    )


# =============================================================================
# No Duplicate BOS
# =============================================================================

def test_same_swing_breaks_only_once():

    df = _frame(
        close=[
            99.0,
            100.20,
            100.50,
            101.00,
        ],
        swing_id=[
            41,
            0,
            0,
            0,
        ],
        swing_type=[
            "HIGH",
            "NONE",
            "NONE",
            "NONE",
        ],
        swing_price=[
            100.0,
            float("nan"),
            float("nan"),
            float("nan"),
        ],
        swing_scale=[
            "MICRO",
            "NONE",
            "NONE",
            "NONE",
        ],
    )

    result = (
        BOSEngine()
        .generate(
            df
        )
    )

    assert int(
        result[
            "bullish_bos"
        ].sum()
    ) == 1

    ids = result.loc[
        result["bos_id"] > 0,
        "bos_id",
    ]

    assert ids.is_unique


# =============================================================================
# Swing Price Contract
# =============================================================================

def test_bos_uses_swing_price_not_confirmation_candle_extreme():

    # In MarketStructure v6 the swing itself may have originated
    # many bars earlier. The confirmation candle is NOT the level.
    #
    # swing_price = 100
    # hypothetical confirmation candle high could have been 110.
    #
    # A later close at 100.20 must break the structural level 100.

    df = _frame(
        close=[
            99.0,
            100.20,
        ],
        swing_id=[
            51,
            0,
        ],
        swing_type=[
            "HIGH",
            "NONE",
        ],
        swing_price=[
            100.0,
            float("nan"),
        ],
        swing_scale=[
            "INTERNAL",
            "NONE",
        ],
    )

    # Extra columns deliberately contain unrelated candle extremes.
    df["high"] = [
        110.0,
        100.30,
    ]

    df["low"] = [
        98.0,
        99.50,
    ]

    result = (
        BOSEngine()
        .generate(
            df
        )
    )

    assert (
        result.loc[
            1,
            "bullish_bos",
        ]
        == 1
    )

    assert (
        result.loc[
            1,
            "bos_price",
        ]
        == pytest.approx(
            100.0
        )
    )


# =============================================================================
# Major Scope
# =============================================================================

def test_major_swing_break_is_major_bos():

    df = _frame(
        close=[
            99.0,
            101.0,
        ],
        swing_id=[
            61,
            0,
        ],
        swing_type=[
            "HIGH",
            "NONE",
        ],
        swing_price=[
            100.0,
            float("nan"),
        ],
        swing_scale=[
            "MAJOR",
            "NONE",
        ],
    )

    result = (
        BOSEngine()
        .generate(
            df
        )
    )

    assert (
        result.loc[
            1,
            "bullish_bos",
        ]
        == 1
    )

    assert (
        result.loc[
            1,
            "major_bos",
        ]
        == 1
    )

    assert (
        result.loc[
            1,
            "bos_scope",
        ]
        == "MAJOR"
    )


# =============================================================================
# Future Confirmation Guard
# =============================================================================

def test_future_confirmed_swing_does_not_leak_backward():

    df = _frame(
        close=[
            99.0,
            101.0,
            101.0,
        ],
        swing_id=[
            71,
            0,
            0,
        ],
        swing_type=[
            "HIGH",
            "NONE",
            "NONE",
        ],
        swing_price=[
            100.0,
            float("nan"),
            float("nan"),
        ],
        swing_scale=[
            "MICRO",
            "NONE",
            "NONE",
        ],
        confirmation_index=[
            2,
            1,
            2,
        ],
    )

    result = (
        BOSEngine()
        .generate(
            df
        )
    )

    # Swing claims confirmation at future row 2,
    # therefore row 0 must not register it.
    assert int(
        result[
            "bullish_bos"
        ].sum()
    ) == 0