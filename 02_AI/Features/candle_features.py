"""
===============================================================================
Module      : candle_features.py
Project     : PulseViper XAU AI
Version     : 3.1
Purpose     : Institutional Candle Feature Engineering
===============================================================================
"""

import numpy as np
import pandas as pd


class CandleFeatures:

    def generate(self, df: pd.DataFrame) -> pd.DataFrame:

        data = df.copy()

        # -------------------------------------------------------
        # Basic Candle
        # -------------------------------------------------------

        data["body"] = (
            data["close"] - data["open"]
        ).abs()

        data["range"] = (
            data["high"] - data["low"]
        )

        data["upper_wick"] = (
            data["high"]
            - data[["open", "close"]].max(axis=1)
        )

        data["lower_wick"] = (
            data[["open", "close"]].min(axis=1)
            - data["low"]
        )

        # -------------------------------------------------------
        # Ratios
        # -------------------------------------------------------

        data["body_ratio"] = (
            data["body"]
            /
            data["range"].replace(0, np.nan)
        )

        data["upper_wick_ratio"] = (
            data["upper_wick"]
            /
            data["range"].replace(0, np.nan)
        )

        data["lower_wick_ratio"] = (
            data["lower_wick"]
            /
            data["range"].replace(0, np.nan)
        )

        # -------------------------------------------------------
        # Direction
        # -------------------------------------------------------

        data["bullish"] = (
            data["close"] > data["open"]
        ).astype(int)

        data["bearish"] = (
            data["close"] < data["open"]
        ).astype(int)

        # -------------------------------------------------------
        # Patterns
        # -------------------------------------------------------

        data["doji"] = (
            data["body_ratio"] < 0.10
        ).astype(int)

        data["marubozu"] = (
            data["body_ratio"] > 0.90
        ).astype(int)

        data["pinbar"] = (
            (
                data["upper_wick_ratio"] > 0.60
            )
            |
            (
                data["lower_wick_ratio"] > 0.60
            )
        ).astype(int)

        # -------------------------------------------------------
        # Engulfing
        # -------------------------------------------------------

        prev_open = data["open"].shift(1)
        prev_close = data["close"].shift(1)

        data["bullish_engulfing"] = (
            (prev_close < prev_open)
            &
            (data["close"] > data["open"])
            &
            (data["close"] > prev_open)
            &
            (data["open"] < prev_close)
        ).astype(int)

        data["bearish_engulfing"] = (
            (prev_close > prev_open)
            &
            (data["close"] < data["open"])
            &
            (data["open"] > prev_close)
            &
            (data["close"] < prev_open)
        ).astype(int)

        # -------------------------------------------------------
        # Inside / Outside Bar
        # -------------------------------------------------------

        prev_high = data["high"].shift(1)
        prev_low = data["low"].shift(1)

        data["inside_bar"] = (
            (data["high"] < prev_high)
            &
            (data["low"] > prev_low)
        ).astype(int)

        data["outside_bar"] = (
            (data["high"] > prev_high)
            &
            (data["low"] < prev_low)
        ).astype(int)

        # -------------------------------------------------------
        # Expansion Candle
        # -------------------------------------------------------

        avg_range = (
            data["range"]
            .rolling(20)
            .mean()
        )

        data["expansion"] = (
            data["range"] > avg_range * 1.5
        ).astype(int)

        data["compression"] = (
            data["range"] < avg_range * 0.5
        ).astype(int)

        return data


candle = CandleFeatures()