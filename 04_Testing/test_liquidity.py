from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

fetcher = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher

liquidity_engine = importlib.import_module(
    "02_AI.Core.liquidity_engine"
).liquidity_engine


def test_liquidity():

    df = fetcher.fetch(bars=1000)

    df = liquidity_engine.generate(df)

    assert "equal_high" in df.columns
    assert "equal_low" in df.columns
    assert "eqh_price" in df.columns
    assert "eql_price" in df.columns

    assert len(df) > 0