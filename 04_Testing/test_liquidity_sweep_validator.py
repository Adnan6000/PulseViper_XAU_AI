"""
===============================================================================
Test        : test_liquidity_sweep_validator.py
Project     : PulseViper XAU AI
Purpose     : Validate Liquidity Sweep Validation Engine
===============================================================================
"""

from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def test_liquidity_sweep_validator():

    fetcher = importlib.import_module(
        "02_AI.Dataset.data_fetcher"
    ).fetcher

    liquidity_module = importlib.import_module(
        "02_AI.Core.liquidity_engine"
    )

    sweep_module = importlib.import_module(
        "02_AI.Core.liquidity_sweep_engine"
    )

    displacement_engine = importlib.import_module(
        "02_AI.Core.displacement_engine"
    ).displacement_engine

    validator_module = importlib.import_module(
        "02_AI.Core.liquidity_sweep_validator"
    )

    liquidity_engine = (
        liquidity_module.liquidity_engine
    )

    validator = (
        validator_module.LiquiditySweepValidator()
    )

    # ==========================================================
    # Fetch Data
    # ==========================================================

    df = fetcher.fetch(
        bars=1000
    )

    assert len(df) > 0

    # ==========================================================
    # Liquidity Detection
    # ==========================================================

    df = liquidity_engine.generate(
        df
    )

    # ==========================================================
    # Liquidity Sweep Detection
    # ==========================================================

    sweep_engine = (
        sweep_module.LiquiditySweepEngine(
            sweep_buffer=0.05,
            memory=liquidity_engine.memory,
        )
    )

    df = sweep_engine.generate(
        df
    )

    # ==========================================================
    # Displacement
    # ==========================================================

    df = displacement_engine.generate(
        df
    )

    # ==========================================================
    # BOS Contract
    #
    # BOS is tested independently in test_bos.py.
    # Here we provide its expected output contract
    # because this test is specifically for the validator.
    # ==========================================================

    df["bullish_bos"] = 0
    df["bearish_bos"] = 0

    # ==========================================================
    # Validation
    # ==========================================================

    result = validator.generate(
        df
    )

    # ==========================================================
    # Required Output
    # ==========================================================

    required = [
        "valid_buy_side_sweep",
        "valid_sell_side_sweep",
        "sweep_validated",
        "sweep_direction",
        "sweep_confirmation_score",
    ]

    for column in required:

        assert column in result.columns

    # ==========================================================
    # Basic Integrity
    # ==========================================================

    assert len(result) > 0

    assert (
        result["sweep_confirmation_score"]
        .between(0, 100)
        .all()
    )

    assert (
        result["valid_buy_side_sweep"]
        .isin([0, 1])
        .all()
    )

    assert (
        result["valid_sell_side_sweep"]
        .isin([0, 1])
        .all()
    )