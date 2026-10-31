"""
===============================================================================
Module      : momentum_features.py
Project     : PulseViper XAU AI
Version     : 3.1
Purpose     : Momentum Feature Engineering
===============================================================================
"""

import numpy as np
import pandas as pd


class MomentumFeatures:

    def rsi(self, close: pd.Series, period: int = 14):

        delta = close.diff()

        gain = delta.clip(lower=0)

        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(
            alpha=1 / period,
            min_periods=period,
            adjust=False
        ).mean()

        avg_loss = loss.ewm(
            alpha=1 / period,
            min_periods=period,
            adjust=False
        ).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)

        return 100 - (100 / (1 + rs))

    def ema(self, series, period):

        return series.ewm(
            span=period,
            adjust=False
        ).mean()

    def generate(self, df: pd.DataFrame):

        data = df.copy()

        # RSI
        data["rsi14"] = self.rsi(data["close"])

        data["rsi_slope"] = data["rsi14"].diff()

        # MACD
        ema12 = self.ema(data["close"], 12)

        ema26 = self.ema(data["close"], 26)

        data["macd"] = ema12 - ema26

        data["macd_signal"] = self.ema(
            data["macd"],
            9
        )

        data["macd_hist"] = (
            data["macd"]
            - data["macd_signal"]
        )

        # Rate of Change

        data["roc10"] = (
            (
                data["close"]
                - data["close"].shift(10)
            )
            /
            data["close"].shift(10)
        ) * 100

        # Momentum

        data["momentum10"] = (
            data["close"]
            - data["close"].shift(10)
        )

        return data


momentum = MomentumFeatures()