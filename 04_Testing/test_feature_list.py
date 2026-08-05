from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

feature_list = importlib.import_module(
    "02_AI.Features.feature_list"
)

FEATURE_COLUMNS = feature_list.FEATURE_COLUMNS


def test_feature_list():

    assert len(FEATURE_COLUMNS) > 0

    assert "ema20" in FEATURE_COLUMNS

    assert "rsi14" in FEATURE_COLUMNS