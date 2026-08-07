"""
===============================================================================
Test        : test_fvg.py
Project     : PulseViper XAU AI
Purpose     : FVG Engine Validation
===============================================================================
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pandas as pd


# =============================================================================
# Project Root
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# Engine Loader
# =============================================================================

def load_fvg_engine():

    module = importlib.import_module(
        "02_AI.Core.fvg_engine"
    )

    return module.FVGEngine


# =============================================================================
# Bullish FVG
# =============================================================================

def test_fvg_engine():

    FVGEngine = load_fvg_engine()

    engine = FVGEngine(
        atr_period=3,
        min_gap_atr=0.01,
        max_gap_atr=10.0,
    )

    data = pd.DataFrame(
        {
            "open": [
                99.0,
                100.0,
                102.5,
                102.0,
                103.0,
                104.0,
            ],
            "high": [
                100.0,
                101.0,
                104.0,
                103.0,
                105.0,
                106.0,
            ],
            "low": [
                98.0,
                99.5,
                102.0,
                101.5,
                102.0,
                103.0,
            ],
            "close": [
                99.5,
                100.5,
                103.5,
                102.0,
                104.0,
                105.0,
            ],
        }
    )

    result = engine.generate(data)

    # ----------------------------------------------------------
    # Required columns
    # ----------------------------------------------------------

    required_columns = [
        "fvg_id",
        "bullish_fvg",
        "bearish_fvg",
        "fvg_direction",
        "fvg_high",
        "fvg_low",
        "fvg_size",
        "fvg_atr_ratio",
        "fvg_active",
        "fvg_mitigated",
        "fvg_fill_percent",
        "fvg_origin_index",
    ]

    for column in required_columns:

        assert column in result.columns, (
            f"Missing FVG column: {column}"
        )

    # ----------------------------------------------------------
    # Bullish FVG must exist
    # ----------------------------------------------------------

    bullish_rows = result[
        result["bullish_fvg"] == 1
    ]

    assert len(bullish_rows) >= 1

    row = bullish_rows.iloc[0]

    assert row["fvg_direction"] == "BULLISH"

    assert row["fvg_low"] == 100.0

    assert row["fvg_high"] == 102.0

    assert row["fvg_size"] == 2.0

    assert row["fvg_id"] > 0

    assert row["fvg_origin_index"] == 0


# =============================================================================
# Bearish FVG
# =============================================================================

def test_fvg_engine_detects_bearish_gap():

    FVGEngine = load_fvg_engine()

    engine = FVGEngine(
        atr_period=3,
        min_gap_atr=0.01,
        max_gap_atr=10.0,
    )

    data = pd.DataFrame(
        {
            "open": [
                101.0,
                100.5,
                97.5,
                98.0,
                97.0,
            ],
            "high": [
                102.0,
                101.0,
                98.0,
                99.0,
                98.0,
            ],
            "low": [
                100.0,
                99.5,
                96.5,
                97.0,
                96.0,
            ],
            "close": [
                101.5,
                100.0,
                97.0,
                98.0,
                96.5,
            ],
        }
    )

    result = engine.generate(data)

    # ----------------------------------------------------------
    # Bearish FVG must exist
    # ----------------------------------------------------------

    bearish_rows = result[
        result["bearish_fvg"] == 1
    ]

    assert len(bearish_rows) >= 1

    row = bearish_rows.iloc[0]

    assert row["fvg_direction"] == "BEARISH"

    assert row["fvg_high"] == 100.0

    assert row["fvg_low"] == 98.0

    assert row["fvg_size"] == 2.0

    assert row["fvg_id"] > 0

    assert row["fvg_origin_index"] == 0