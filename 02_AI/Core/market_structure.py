"""
===============================================================================
Module      : market_structure.py
Project     : PulseViper XAU AI
Version     : 4.0
Purpose     : Institutional Market Structure Engine
===============================================================================
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class MarketStructure:

    def __init__(
        self,
        pivot_window: int = 5,
        atr_period: int = 14,
        min_strength: float = 1.20,
    ):

        self.pivot_window = pivot_window
        self.atr_period = atr_period
        self.min_strength = min_strength

    # ============================================================
    # ATR
    # ============================================================

    def _calculate_atr(
        self,
        data: pd.DataFrame
    ) -> pd.Series:

        high_low = data["high"] - data["low"]

        high_close = (
            data["high"]
            - data["close"].shift()
        ).abs()

        low_close = (
            data["low"]
            - data["close"].shift()
        ).abs()

        tr = pd.concat(
            [
                high_low,
                high_close,
                low_close,
            ],
            axis=1,
        ).max(axis=1)

        return tr.rolling(
            self.atr_period,
            min_periods=1,
        ).mean()

    # ============================================================
    # Main
    # ============================================================

    def generate(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:

        data = df.copy()

        # ATR

        data["atr"] = self._calculate_atr(data)

        # Pivot Columns

        data["pivot_high"] = 0
        data["pivot_low"] = 0

        data["pivot_strength"] = 0.0
        data["major_swing"] = 0

        window = self.pivot_window

        for i in range(window, len(data) - window):

            current_high = data.iloc[i]["high"]
            current_low = data.iloc[i]["low"]

            left_high = data.iloc[i-window:i]["high"].max()
            right_high = data.iloc[i+1:i+window+1]["high"].max()

            left_low = data.iloc[i-window:i]["low"].min()
            right_low = data.iloc[i+1:i+window+1]["low"].min()

            # -------------------------
            # Pivot High
            # -------------------------

            if (
                current_high > left_high
                and
                current_high >= right_high
            ):

                atr = data.iloc[i]["atr"]

                strength = (
                    current_high
                    -
                    max(left_high, right_high)
                ) / max(atr, 0.00001)

                data.at[
                    data.index[i],
                    "pivot_high"
                ] = 1

                data.at[
                    data.index[i],
                    "pivot_strength"
                ] = strength

                if strength >= self.min_strength:

                    data.at[
                        data.index[i],
                        "major_swing"
                    ] = 1

            # -------------------------
            # Pivot Low
            # -------------------------

            if (
                current_low < left_low
                and
                current_low <= right_low
            ):

                atr = data.iloc[i]["atr"]

                strength = (
                    min(left_low, right_low)
                    -
                    current_low
                ) / max(atr, 0.00001)

                data.at[
                    data.index[i],
                    "pivot_low"
                ] = 1

                data.at[
                    data.index[i],
                    "pivot_strength"
                ] = max(
                    data.at[
                        data.index[i],
                        "pivot_strength"
                    ],
                    strength,
                )

                if strength >= self.min_strength:

                    data.at[
                        data.index[i],
                        "major_swing"
                    ] = 1

        return data


market_structure = MarketStructure()