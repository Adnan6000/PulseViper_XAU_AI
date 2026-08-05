from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

module = importlib.import_module(
    "02_AI.Dataset.history_manager"
)

history = module.history


def test_history():

    files = history.build_dataset(bars=100)

    assert len(files) == 7