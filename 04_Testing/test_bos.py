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

bos_engine = importlib.import_module(
    "02_AI.Core.bos_engine"
).bos_engine


def test_bos():

    df = fetcher.fetch(bars=5000)

    df = market_structure.generate(df)

    df = bos_engine.generate(df)

    assert "bullish_bos" in df.columns
    assert "bearish_bos" in df.columns
    assert "bos_direction" in df.columns
    assert "bos_strength" in df.columns