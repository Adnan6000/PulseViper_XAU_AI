from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

fetcher_module = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
)

validator_module = importlib.import_module(
    "02_AI.Dataset.history_validator"
)

fetcher = fetcher_module.fetcher
validator = validator_module.validator


def test_validator():

    df = fetcher.fetch(bars=500)

    assert validator.validate_columns(df)
    assert validator.validate_empty(df)
    assert validator.validate_duplicates(df)
    assert validator.validate_nulls(df)