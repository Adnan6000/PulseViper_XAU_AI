from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

fetcher_module = importlib.import_module("02_AI.Dataset.data_fetcher")

fetcher = fetcher_module.fetcher


def test_fetch():

    df = fetcher.fetch(bars=100)

    assert len(df) == 100