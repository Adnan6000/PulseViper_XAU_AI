from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

fetcher = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher

market_structure = importlib.import_module(
    "02_AI.Core.market_structure"
).market_structure


def test_market_structure():

    df = fetcher.fetch(bars=5000)

    df = market_structure.generate(df)

    assert "atr" in df.columns
    assert "pivot_high" in df.columns
    assert "pivot_low" in df.columns
    assert "pivot_strength" in df.columns
    assert "major_swing" in df.columns

    assert df["pivot_high"].sum() > 5
    assert df["pivot_low"].sum() > 5