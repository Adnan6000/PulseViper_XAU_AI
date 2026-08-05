from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

fetcher_module = importlib.import_module("02_AI.Dataset.data_fetcher")
exporter_module = importlib.import_module("02_AI.Dataset.export_dataset")

fetcher = fetcher_module.fetcher
exporter = exporter_module.exporter


def test_export():

    df = fetcher.fetch(bars=100)

    file = exporter.export(df, "xauusd_m1_test.csv")

    assert file.exists()