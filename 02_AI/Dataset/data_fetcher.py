"""
PulseViper MT5 Data Fetcher
"""

from pathlib import Path
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime


class MT5DataFetcher:

    def initialize(self):

        if not mt5.initialize():
            raise RuntimeError(f"MT5 Initialization Failed: {mt5.last_error()}")

    def shutdown(self):

        mt5.shutdown()

    def fetch(
        self,
        symbol="XAUUSDm",
        timeframe=mt5.TIMEFRAME_M1,
        bars=10000,
    ):

        self.initialize()

        if not mt5.symbol_select(symbol, True):
            self.shutdown()
            raise RuntimeError(f"Cannot select symbol: {symbol}")

        rates = mt5.copy_rates_from_pos(
            symbol,
            timeframe,
            0,
            bars
        )

        self.shutdown()

        if rates is None:
            raise RuntimeError(f"No data returned for {symbol}")

        import pandas as pd

        df = pd.DataFrame(rates)

        df["time"] = pd.to_datetime(df["time"], unit="s")

        return df


fetcher = MT5DataFetcher()