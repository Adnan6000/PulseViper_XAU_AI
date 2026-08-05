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

    df = fetcher.fetch(bars=2000)

    df = market_structure.generate(df)

    assert "HH" in df.columns
    assert "HL" in df.columns
    assert "LH" in df.columns
    assert "LL" in df.columns

    assert df["HH"].sum() >= 0
    assert df["HL"].sum() >= 0
    assert df["LH"].sum() >= 0
    assert df["LL"].sum() >= 0