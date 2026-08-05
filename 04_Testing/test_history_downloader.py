from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

module = importlib.import_module("02_AI.Dataset.history_downloader")

downloader = module.downloader


def test_history():

    files = downloader.download(bars=500)

    assert len(files) == 7