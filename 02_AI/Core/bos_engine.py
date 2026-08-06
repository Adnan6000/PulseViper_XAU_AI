"""
===============================================================================
Module      : bos_engine.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Break of Structure (BOS) Detection Engine
===============================================================================
"""

from __future__ import annotations

import pandas as pd


class BOSEngine:

    def generate(
        self,
        data: pd.DataFrame
    ) -> pd.DataFrame:

        df = data.copy()

        df["bullish_bos"] = 0
        df["bearish_bos"] = 0

        df["bos_direction"] = "NONE"
        df["bos_price"] = 0.0
        df["bos_strength"] = 0.0

        last_major_high = None
        last_major_low = None

        for i in range(len(df)):

            if df.iloc[i]["major_high"] == 1:
                last_major_high = df.iloc[i]["high"]

            if df.iloc[i]["major_low"] == 1:
                last_major_low = df.iloc[i]["low"]

            close = df.iloc[i]["close"]

            # Bullish BOS
            if (
                last_major_high is not None
                and close > last_major_high
            ):

                df.at[df.index[i], "bullish_bos"] = 1
                df.at[df.index[i], "bos_direction"] = "BULLISH"
                df.at[df.index[i], "bos_price"] = last_major_high
                df.at[df.index[i], "bos_strength"] = (
                    close - last_major_high
                )

            # Bearish BOS
            if (
                last_major_low is not None
                and close < last_major_low
            ):

                df.at[df.index[i], "bearish_bos"] = 1
                df.at[df.index[i], "bos_direction"] = "BEARISH"
                df.at[df.index[i], "bos_price"] = last_major_low
                df.at[df.index[i], "bos_strength"] = (
                    last_major_low - close
                )

        return df


bos_engine = BOSEngine()