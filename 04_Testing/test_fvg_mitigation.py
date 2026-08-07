"""
===============================================================================
Test        : test_fvg_mitigation.py
Project     : PulseViper XAU AI
Purpose     : Validate FVG mitigation lifecycle
===============================================================================
"""

import importlib

import pandas as pd


def test_bullish_fvg_mitigation():

    module = importlib.import_module(
        "02_AI.Core.fvg_mitigation_engine"
    )

    engine = module.FVGMitigationEngine()

    df = pd.DataFrame(
        {
            "open": [100.0, 103.0, 104.0],
            "high": [101.0, 105.0, 105.0],
            "low": [99.0, 102.0, 99.0],
            "close": [100.5, 104.0, 99.5],

            "fvg_id": [0, 1, 0],
            "bullish_fvg": [0, 1, 0],
            "bearish_fvg": [0, 0, 0],

            "fvg_high": [0.0, 102.0, 0.0],
            "fvg_low": [0.0, 100.0, 0.0],
        }
    )

    result = engine.generate(df)

    assert "fvg_mitigated" in result.columns
    assert "fvg_fill_percent" in result.columns
    assert "fvg_mitigation_index" in result.columns

    assert result.loc[2, "fvg_mitigated"] == 1

    assert result.loc[2, "fvg_mitigation_index"] == 2

    assert result.loc[2, "fvg_mitigation_price"] == 99.0


def test_bearish_fvg_mitigation():

    module = importlib.import_module(
        "02_AI.Core.fvg_mitigation_engine"
    )

    engine = module.FVGMitigationEngine()

    df = pd.DataFrame(
        {
            "open": [100.0, 97.0, 96.0],
            "high": [101.0, 98.0, 101.0],
            "low": [99.0, 95.0, 95.0],
            "close": [100.0, 96.0, 100.5],

            "fvg_id": [0, 1, 0],
            "bullish_fvg": [0, 0, 0],
            "bearish_fvg": [0, 1, 0],

            "fvg_high": [0.0, 100.0, 0.0],
            "fvg_low": [0.0, 98.0, 0.0],
        }
    )

    result = engine.generate(df)

    assert "fvg_mitigated" in result.columns

    assert result.loc[2, "fvg_mitigated"] == 1

    assert result.loc[2, "fvg_mitigation_index"] == 2

    assert result.loc[2, "fvg_mitigation_price"] == 101.0