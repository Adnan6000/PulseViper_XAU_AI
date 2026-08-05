"""
PulseViper History Downloader
Downloads complete MT5 history and stores it as CSV.
"""

from pathlib import Path
from datetime import datetime
import importlib
import sys

import MetaTrader5 as mt5
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

fetcher_module = importlib.import_module("02_AI.Dataset.data_fetcher")

fetcher = fetcher_module.fetcher

RAW_DIR = ROOT_DIR / "01_Data" / "Raw"
RAW_DIR.mkdir(exist_ok=True)


class HistoryDownloader:

    TIMEFRAMES = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
    }

    def download(self, symbol="XAUUSDm", bars=100000):

        exported = []

        for tf_name, tf_value in self.TIMEFRAMES.items():

            print(f"Downloading {tf_name}...")

            df = fetcher.fetch(
                symbol=symbol,
                timeframe=tf_value,
                bars=bars,
            )

            filename = (
                f"{symbol}_{tf_name}_{datetime.now():%Y%m%d}.csv"
            )

            path = RAW_DIR / filename

            df.to_csv(path, index=False)

            exported.append(path)

            print(f"{tf_name}: {len(df)} candles saved")

        return exported


downloader = HistoryDownloader()