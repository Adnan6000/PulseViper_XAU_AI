from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

fetcher = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher

momentum = importlib.import_module(
    "02_AI.Features.momentum_features"
).momentum


def test_momentum():

    df = fetcher.fetch(bars=500)

    df = momentum.generate(df)

    assert "rsi14" in df.columns
    assert "macd" in df.columns
    assert "macd_signal" in df.columns
    assert "macd_hist" in df.columns
    assert "roc10" in df.columns