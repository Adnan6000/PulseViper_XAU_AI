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

    bos_engine.reset()

    df = fetcher.fetch(bars=5000)

    df = market_structure.generate(df)

    df = bos_engine.generate(df)

    assert "bos_id" in df.columns
    assert "bos_active" in df.columns
    assert "bos_confirmed" in df.columns
    assert "broken_swing_id" in df.columns
    assert "break_distance" in df.columns

    ids = df[df["bos_id"] > 0]["bos_id"]

    assert ids.is_unique