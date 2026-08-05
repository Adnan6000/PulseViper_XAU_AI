from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

fetcher = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher

cleaner = importlib.import_module(
    "02_AI.Dataset.history_cleaner"
).cleaner


def test_cleaner():

    df = fetcher.fetch(bars=1000)

    df = cleaner.clean(df)

    df = cleaner.remove_invalid_prices(df)

    assert len(df) > 0