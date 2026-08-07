from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def test_liquidity_sweep():

    liquidity_module = importlib.import_module(
        "02_AI.Core.liquidity_engine"
    )

    sweep_module = importlib.import_module(
        "02_AI.Core.liquidity_sweep_engine"
    )

    fetcher = importlib.import_module(
        "02_AI.Dataset.data_fetcher"
    ).fetcher

    liquidity_engine = (
        liquidity_module.liquidity_engine
    )

    sweep_engine = (
        sweep_module.LiquiditySweepEngine(
            sweep_buffer=0.05,
            memory=liquidity_engine.memory,
        )
    )

    df = fetcher.fetch(
        bars=1000
    )

    df = liquidity_engine.generate(
        df
    )

    result = sweep_engine.generate(
        df
    )

    required = [
        "buy_side_sweep",
        "sell_side_sweep",
        "sweep_price",
        "sweep_liquidity_id",
    ]

    for column in required:

        assert column in result.columns

    assert len(result) > 0