"""
===============================================================================
Test        : test_confidence_integration.py
Project     : PulseViper XAU AI
Purpose     : Confidence Engine pipeline integration validation
===============================================================================
"""

import importlib

import pandas as pd


def test_confidence_engine_with_fvg_quality_pipeline():
    """
    Validate:

    FVG
      ↓
    FVG Mitigation
      ↓
    FVG Quality
      ↓
    Confidence
    """

    fvg_module = importlib.import_module(
        "02_AI.Core.fvg_engine"
    )

    mitigation_module = importlib.import_module(
        "02_AI.Core.fvg_mitigation_engine"
    )

    quality_module = importlib.import_module(
        "02_AI.Core.fvg_quality_engine"
    )

    confidence_module = importlib.import_module(
        "02_AI.Core.confidence_engine"
    )

    fvg_engine = fvg_module.fvg_engine
    mitigation_engine = mitigation_module.fvg_mitigation_engine
    quality_engine = quality_module.fvg_quality_engine
    confidence_engine = confidence_module.confidence_engine

    df = pd.DataFrame(
        {
            "open": [
                2000.0,
                2000.0,
                2005.0,
                2006.0,
                2007.0,
                2008.0,
            ],
            "high": [
                2002.0,
                2003.0,
                2010.0,
                2012.0,
                2015.0,
                2017.0,
            ],
            "low": [
                1998.0,
                1999.0,
                2004.0,
                2005.0,
                2006.0,
                2007.0,
            ],
            "close": [
                2001.0,
                2002.0,
                2009.0,
                2011.0,
                2014.0,
                2016.0,
            ],
            "tick_volume": [
                100,
                120,
                300,
                350,
                400,
                450,
            ],
        }
    )

    # -------------------------------------------------------------------------
    # FVG
    # -------------------------------------------------------------------------

    df = fvg_engine.generate(df)

    assert "fvg_id" in df.columns
    assert "bullish_fvg" in df.columns
    assert "bearish_fvg" in df.columns

    # -------------------------------------------------------------------------
    # FVG Mitigation
    # -------------------------------------------------------------------------

    df = mitigation_engine.generate(df)

    assert "fvg_mitigated" in df.columns

    # -------------------------------------------------------------------------
    # FVG Quality
    # -------------------------------------------------------------------------

    df = quality_engine.generate(df)

    assert "fvg_quality_score" in df.columns
    assert "fvg_quality_grade" in df.columns
    assert "fvg_confluence_count" in df.columns
    assert "fvg_institutional" in df.columns

    # -------------------------------------------------------------------------
    # Confidence
    # -------------------------------------------------------------------------

    df = confidence_engine.generate(df)

    assert "confidence_score" in df.columns
    assert "confidence_grade" in df.columns
    assert "confidence_direction" in df.columns
    assert "confidence_confluence" in df.columns
    assert "trade_ready" in df.columns

    # -------------------------------------------------------------------------
    # Data integrity
    # -------------------------------------------------------------------------

    assert len(df) == 6

    assert df["confidence_score"].notna().all()
    assert df["confidence_grade"].notna().all()
    assert df["confidence_direction"].notna().all()

    assert (
        df["confidence_score"]
        .between(0.0, 100.0)
        .all()
    )

    assert (
        df["confidence_confluence"]
        .between(0, 6)
        .all()
    )

    assert set(
        df["confidence_direction"].unique()
    ).issubset(
        {
            "BULLISH",
            "BEARISH",
            "NEUTRAL",
        }
    )

    assert set(
        df["confidence_grade"].unique()
    ).issubset(
        {
            "A+",
            "A",
            "B",
            "C",
            "D",
            "NONE",
        }
    )


def test_confidence_engine_does_not_modify_source_dataframe():
    """
    Confidence engine must operate on a copy and must not
    mutate the caller's original DataFrame.
    """

    module = importlib.import_module(
        "02_AI.Core.confidence_engine"
    )

    engine = module.confidence_engine

    source = pd.DataFrame(
        {
            "close": [
                2000.0,
                2001.0,
            ],
            "fvg_quality_score": [
                80.0,
                0.0,
            ],
            "fvg_displacement_score": [
                100.0,
                0.0,
            ],
            "fvg_bos_score": [
                100.0,
                0.0,
            ],
            "fvg_liquidity_score": [
                100.0,
                0.0,
            ],
            "fvg_structure_score": [
                100.0,
                0.0,
            ],
            "fvg_mitigation_score": [
                100.0,
                0.0,
            ],
            "bullish_fvg": [
                1,
                0,
            ],
            "bearish_fvg": [
                0,
                0,
            ],
            "bullish_bos": [
                1,
                0,
            ],
            "bearish_bos": [
                0,
                0,
            ],
            "bullish_sweep": [
                1,
                0,
            ],
            "bearish_sweep": [
                0,
                0,
            ],
        }
    )

    original_columns = list(
        source.columns
    )

    result = engine.generate(source)

    assert list(
        source.columns
    ) == original_columns

    assert "confidence_score" not in source.columns
    assert "trade_ready" not in source.columns

    assert "confidence_score" in result.columns
    assert "trade_ready" in result.columns