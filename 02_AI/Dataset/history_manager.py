"""
PulseViper History Manager
Enterprise Data Pipeline
"""

from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

downloader_module = importlib.import_module(
    "02_AI.Dataset.history_downloader"
)

exporter_module = importlib.import_module(
    "02_AI.Dataset.export_dataset"
)

downloader = downloader_module.downloader
exporter = exporter_module.exporter


class HistoryManager:

    def build_dataset(
        self,
        symbol="XAUUSDm",
        bars=100000,
    ):

        exported_files = downloader.download(
            symbol=symbol,
            bars=bars,
        )

        return exported_files


history = HistoryManager()