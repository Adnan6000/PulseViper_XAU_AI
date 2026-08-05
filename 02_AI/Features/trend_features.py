"""
PulseViper Trend Features
"""

import numpy as np
import pandas as pd


class TrendFeatures:

    @staticmethod
    def ema(series: pd.Series, period: int):

        return series.ewm(span=period, adjust=False).mean()

    def generate(self, df: pd.DataFrame):

        data = df.copy()

        # EMA
        data["ema20"] = self.ema(data["close"], 20)
        data["ema50"] = self.ema(data["close"], 50)
        data["ema200"] = self.ema(data["close"], 200)

        # Distance
        data["dist_ema20"] = data["close"] - data["ema20"]
        data["dist_ema50"] = data["close"] - data["ema50"]
        data["dist_ema200"] = data["close"] - data["ema200"]

        # EMA Slopes
        data["ema20_slope"] = data["ema20"].diff()
        data["ema50_slope"] = data["ema50"].diff()
        data["ema200_slope"] = data["ema200"].diff()

        # Trend Strength
        data["trend_strength"] = (
            abs(data["ema20"] - data["ema50"])
            + abs(data["ema50"] - data["ema200"])
        )

        # Trend Direction
        data["trend_direction"] = np.where(

            (data["ema20"] > data["ema50"])
            &
            (data["ema50"] > data["ema200"]),

            1,

            np.where(

                (data["ema20"] < data["ema50"])
                &
                (data["ema50"] < data["ema200"]),

                -1,

                0
            )
        )

        return data


trend = TrendFeatures()