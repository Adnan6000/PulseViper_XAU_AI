"""
===============================================================================
Module      : volatility_features.py
Project     : PulseViper XAU AI
Version     : 3.1
Purpose     : Volatility Feature Engineering
===============================================================================
"""

import pandas as pd


class VolatilityFeatures:

    def atr(self, df: pd.DataFrame, period: int = 14):

        high_low = df["high"] - df["low"]

        high_close = (df["high"] - df["close"].shift()).abs()

        low_close = (df["low"] - df["close"].shift()).abs()

        tr = pd.concat(
            [high_low, high_close, low_close],
            axis=1
        ).max(axis=1)

        atr = tr.rolling(period).mean()

        return tr, atr

    def generate(self, df: pd.DataFrame):

        data = df.copy()

        tr, atr = self.atr(data)

        data["true_range"] = tr

        data["atr14"] = atr

        data["atr_percent"] = (
            atr / data["close"]
        ) * 100

        data["candle_range"] = (
            data["high"]
            - data["low"]
        )

        data["avg_range20"] = (
            data["candle_range"]
            .rolling(20)
            .mean()
        )

        data["volatility_ratio"] = (
            data["candle_range"]
            /
            data["avg_range20"]
        )

        data["rolling_std20"] = (
            data["close"]
            .rolling(20)
            .std()
        )

        return data


volatility = VolatilityFeatures()