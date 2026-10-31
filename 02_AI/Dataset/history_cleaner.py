"""
===============================================================================
Module      : history_cleaner.py
Project     : PulseViper XAU AI
Version     : 3.0
Purpose     : Clean historical market data before feature generation.
===============================================================================
"""

import pandas as pd


class HistoryCleaner:

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:

        data = df.copy()

        # Remove duplicate candles
        data = data.drop_duplicates()

        # Sort by time
        data = data.sort_values("time")

        # Reset index
        data = data.reset_index(drop=True)

        return data

    def remove_invalid_prices(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:

        data = df.copy()

        data = data[
            (data["high"] >= data["low"])
            &
            (data["open"] > 0)
            &
            (data["high"] > 0)
            &
            (data["low"] > 0)
            &
            (data["close"] > 0)
        ]

        return data.reset_index(drop=True)


cleaner = HistoryCleaner()