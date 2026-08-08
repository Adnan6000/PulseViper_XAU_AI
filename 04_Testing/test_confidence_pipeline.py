"""
===============================================================================
Test        : test_confidence_pipeline.py
Project     : PulseViper XAU AI
Purpose     : Full AI confidence pipeline integration test
===============================================================================
"""

import importlib

importlib.import_module("02_AI.Core.bos_engine")

market_structure_engine = importlib.import_module(
    "02_AI.Core.market_structure"
).market_structure


def test_full_confidence_pipeline():

    # =========================================================================
    # Imports
    # =========================================================================

    fetcher = importlib.import_module(
        "02_AI.Dataset.data_fetcher"
    ).fetcher

    liquidity_engine = importlib.import_module(
        "02_AI.Core.liquidity_engine"
    ).liquidity_engine

    sweep_module = importlib.import_module(
        "02_AI.Core.liquidity_sweep_engine"
    )

    displacement_engine = importlib.import_module(
        "02_AI.Core.displacement_engine"
    ).displacement_engine

    bos_engine = importlib.import_module(
        "02_AI.Core.bos_engine"
    ).bos_engine

    fvg_engine = importlib.import_module(
        "02_AI.Core.fvg_engine"
    ).fvg_engine

    mitigation_engine = importlib.import_module(
        "02_AI.Core.fvg_mitigation_engine"
    ).fvg_mitigation_engine

    quality_engine = importlib.import_module(
        "02_AI.Core.fvg_quality_engine"
    ).fvg_quality_engine

    confidence_engine = importlib.import_module(
        "02_AI.Core.confidence_engine"
    ).confidence_engine

    # =========================================================================
    # Fetch market data
    # =========================================================================

    df = fetcher.fetch(
        bars=1000
    )

    assert df is not None
    assert len(df) > 0

    # =========================================================================
    # Liquidity
    # =========================================================================

    df = liquidity_engine.generate(
        df
    )

    assert "equal_high" in df.columns
    assert "equal_low" in df.columns

    # =========================================================================
    # Liquidity Sweep
    # =========================================================================

    sweep_engine = sweep_module.LiquiditySweepEngine(
        sweep_buffer=0.05,
        memory=liquidity_engine.memory,
    )

    df = sweep_engine.generate(
        df
    )

    # =========================================================================
    # Displacement
    # =========================================================================

    df = displacement_engine.generate(
        df
    )

    assert "is_displacement" in df.columns

    # =========================================================================
    # Market Structure
    # =========================================================================

    df = market_structure_engine.generate(
        df
    )

    assert "major_high" in df.columns
    assert "major_low" in df.columns
    assert "HH" in df.columns
    assert "HL" in df.columns
    assert "LH" in df.columns
    assert "LL" in df.columns

    # =========================================================================
    # BOS
    # =========================================================================

    df = bos_engine.generate(
        df
    )

    assert "bullish_bos" in df.columns
    assert "bearish_bos" in df.columns

    # =========================================================================
    # FVG
    # =========================================================================

    df = fvg_engine.generate(
        df
    )

    assert "fvg_id" in df.columns
    assert "bullish_fvg" in df.columns
    assert "bearish_fvg" in df.columns

    # =========================================================================
    # FVG Mitigation
    # =========================================================================

    df = mitigation_engine.generate(
        df
    )

    assert "fvg_mitigated" in df.columns

    # =========================================================================
    # FVG Quality
    # =========================================================================

    df = quality_engine.generate(
        df
    )

    assert "fvg_quality_score" in df.columns
    assert "fvg_quality_grade" in df.columns
    assert "fvg_confluence_count" in df.columns
    assert "fvg_institutional" in df.columns

    # =========================================================================
    # Confidence
    # =========================================================================

    df = confidence_engine.generate(
        df
    )

    # =========================================================================
    # Validate output
    # =========================================================================

    required_columns = [
        "confidence_score",
        "confidence_grade",
        "confidence_direction",
        "confidence_confluence",
        "trade_ready",
    ]

    for column in required_columns:

        assert column in df.columns

    # =========================================================================
    # Validate values
    # =========================================================================

    assert (
        df["confidence_score"]
        .notna()
        .all()
    )

    assert (
        df["confidence_score"]
        .between(
            0.0,
            100.0,
        )
        .all()
    )

    assert (
        df["confidence_confluence"]
        .between(
            0,
            6,
        )
        .all()
    )

    assert (
        df["trade_ready"]
        .isin(
            [
                0,
                1,
            ]
        )
        .all()
    )

    assert (
        df["confidence_direction"]
        .isin(
            [
                "BULLISH",
                "BEARISH",
                "NEUTRAL",
            ]
        )
        .all()
    )

    assert (
        df["confidence_grade"]
        .isin(
            [
                "A+",
                "A",
                "B",
                "C",
                "D",
                "NONE",
            ]
        )
        .all()
    )

    # =========================================================================
    # Final sanity check
    # =========================================================================

    print(
        "\nConfidence Pipeline Summary"
    )

    print(
        "Bars:",
        len(df),
    )

    print(
        "Max Confidence:",
        df["confidence_score"].max(),
    )

    print(
        "Average Confidence:",
        round(
            df["confidence_score"].mean(),
            2,
        ),
    )

    print(
        "Trade Ready:",
        int(
            df["trade_ready"].sum()
        ),
    )

    print(
        "Bullish:",
        int(
            (
                df["confidence_direction"]
                == "BULLISH"
            ).sum()
        ),
    )

    print(
        "Bearish:",
        int(
            (
                df["confidence_direction"]
                == "BEARISH"
            ).sum()
        ),
    )