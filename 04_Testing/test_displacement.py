from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

fetcher = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher

displacement_engine = importlib.import_module(
    "02_AI.Core.displacement_engine"
).displacement_engine


def test_displacement():

    df = fetcher.fetch(bars=1000)

    df = displacement_engine.generate(df)

    required = [
        "body_size",
        "upper_wick",
        "lower_wick",
        "body_ratio",
        "range_size",
        "atr_expansion",
        "is_displacement",
        "displacement_score",
        "impulse_strength",
        "institutional_move",
    ]

    for column in required:
        assert column in df.columns

    assert len(df) > 0