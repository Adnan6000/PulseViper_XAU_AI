"""
===============================================================================
Test        : test_confidence.py
Project     : PulseViper XAU AI
Purpose     : Confidence Engine validation
===============================================================================
"""

import importlib

import pandas as pd


def test_confidence_engine_basic():
    module = importlib.import_module(
        "02_AI.Core.confidence_engine"
    )

    engine = module.confidence_engine

    df = pd.DataFrame(
        {
            "close": [2000.0, 2001.0, 2002.0],

            "fvg_quality_score": [
                90.0,
                0.0,
                70.0,
            ],

            "fvg_displacement_score": [
                100.0,
                0.0,
                80.0,
            ],

            "fvg_bos_score": [
                100.0,
                0.0,
                60.0,
            ],

            "fvg_liquidity_score": [
                100.0,
                0.0,
                100.0,
            ],

            "fvg_structure_score": [
                100.0,
                0.0,
                70.0,
            ],

            "fvg_mitigation_score": [
                100.0,
                0.0,
                50.0,
            ],

            "bullish_fvg": [
                1,
                0,
                1,
            ],

            "bearish_fvg": [
                0,
                0,
                0,
            ],

            "bullish_bos": [
                1,
                0,
                1,
            ],

            "bearish_bos": [
                0,
                0,
                0,
            ],

            "bullish_sweep": [
                1,
                0,
                1,
            ],

            "bearish_sweep": [
                0,
                0,
                0,
            ],
        }
    )

    result = engine.generate(df)

    assert "confidence_score" in result.columns
    assert "confidence_grade" in result.columns
    assert "confidence_direction" in result.columns
    assert "confidence_confluence" in result.columns
    assert "trade_ready" in result.columns

    assert result.loc[0, "confidence_score"] > 80.0
    assert result.loc[0, "confidence_direction"] == "BULLISH"
    assert result.loc[0, "confidence_confluence"] == 6
    assert result.loc[0, "trade_ready"] == 1

    assert result.loc[1, "confidence_score"] == 0.0
    assert result.loc[1, "confidence_grade"] == "NONE"
    assert result.loc[1, "confidence_direction"] == "NEUTRAL"
    assert result.loc[1, "trade_ready"] == 0


def test_confidence_engine_bearish():

    module = importlib.import_module(
        "02_AI.Core.confidence_engine"
    )

    engine = module.confidence_engine

    df = pd.DataFrame(
        {
            "close": [
                2000.0,
                1998.0,
                1995.0,
            ],

            "fvg_quality_score": [
                85.0,
                75.0,
                90.0,
            ],

            "fvg_displacement_score": [
                90.0,
                80.0,
                100.0,
            ],

            "fvg_bos_score": [
                100.0,
                90.0,
                100.0,
            ],

            "fvg_liquidity_score": [
                100.0,
                80.0,
                100.0,
            ],

            "fvg_structure_score": [
                100.0,
                70.0,
                100.0,
            ],

            "fvg_mitigation_score": [
                80.0,
                60.0,
                100.0,
            ],

            "bullish_fvg": [
                0,
                0,
                0,
            ],

            "bearish_fvg": [
                1,
                1,
                1,
            ],

            "bullish_bos": [
                0,
                0,
                0,
            ],

            "bearish_bos": [
                1,
                1,
                1,
            ],

            "bullish_sweep": [
                0,
                0,
                0,
            ],

            "bearish_sweep": [
                1,
                1,
                1,
            ],
        }
    )

    result = engine.generate(df)

    assert result.loc[0, "confidence_score"] > 75.0
    assert result.loc[0, "confidence_direction"] == "BEARISH"
    assert result.loc[0, "confidence_confluence"] == 6
    assert result.loc[0, "trade_ready"] == 1


def test_confidence_engine_missing_required_column():

    module = importlib.import_module(
        "02_AI.Core.confidence_engine"
    )

    engine = module.confidence_engine

    df = pd.DataFrame(
        {
            "open": [1.0, 2.0],
            "high": [2.0, 3.0],
            "low": [0.5, 1.5],
        }
    )

    try:
        engine.generate(df)
    except ValueError as exc:
        assert "close" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for missing close column"
        )