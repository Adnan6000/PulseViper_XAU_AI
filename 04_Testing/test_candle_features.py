from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

fetcher = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher

candle = importlib.import_module(
    "02_AI.Features.candle_features"
).candle


def test_candle_features():

    df = fetcher.fetch(bars=1000)

    df = candle.generate(df)

    assert "body" in df.columns
    assert "upper_wick" in df.columns
    assert "lower_wick" in df.columns
    assert "pinbar" in df.columns
    assert "doji" in df.columns
    assert "inside_bar" in df.columns
    assert "outside_bar" in df.columns