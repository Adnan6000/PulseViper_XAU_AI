"""
===============================================================================
Module      : market_structure.py
Project     : PulseViper XAU AI
Version     : 4.1
Author      : PulseViper AI
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

    # ==========================================================
    # ATR
    # ==========================================================

    def calculate_atr(
        self,
        df: pd.DataFrame
    ) -> pd.Series:

        hl = df["high"] - df["low"]

        hc = (
            df["high"]
            - df["close"].shift()
        ).abs()

        lc = (
            df["low"]
            - df["close"].shift()
        ).abs()

        tr = pd.concat(
            [
                hl,
                hc,
                lc,
            ],
            axis=1,
        ).max(axis=1)

        atr = tr.rolling(
            self.atr_period,
            min_periods=1
        ).mean()

        return atr

    # ==========================================================
    # Pivot Detection
    # ==========================================================

    def detect_pivots(
        self,
        data: pd.DataFrame
    ) -> pd.DataFrame:

        window = self.pivot_window

        data["pivot_high"] = 0
        data["pivot_low"] = 0

        data["pivot_strength"] = 0.0

        for i in range(
            window,
            len(data) - window
        ):

            current_high = data.iloc[i]["high"]

            left_high = (
                data.iloc[
                    i-window:i
                ]["high"].max()
            )

            right_high = (
                data.iloc[
                    i+1:i+window+1
                ]["high"].max()
            )

            if (
                current_high > left_high
                and
                current_high >= right_high
            ):

                atr = max(
                    data.iloc[i]["atr"],
                    0.00001
                )

                strength = (
                    current_high
                    -
                    max(
                        left_high,
                        right_high
                    )
                ) / atr

                data.at[
                    data.index[i],
                    "pivot_high"
                ] = 1

                data.at[
                    data.index[i],
                    "pivot_strength"
                ] = strength

            current_low = data.iloc[i]["low"]

            left_low = (
                data.iloc[
                    i-window:i
                ]["low"].min()
            )

            right_low = (
                data.iloc[
                    i+1:i+window+1
                ]["low"].min()
            )

            if (
                current_low < left_low
                and
                current_low <= right_low
            ):

                atr = max(
                    data.iloc[i]["atr"],
                    0.00001
                )

                strength = (
                    min(
                        left_low,
                        right_low
                    )
                    -
                    current_low
                ) / atr

                data.at[
                    data.index[i],
                    "pivot_low"
                ] = 1

                if (
                    strength >
                    data.at[
                        data.index[i],
                        "pivot_strength"
                    ]
                ):

                    data.at[
                        data.index[i],
                        "pivot_strength"
                    ] = strength

        return data

    # ==========================================================
    # Swing Ranking
    # ==========================================================

    def classify_swings(
        self,
        data: pd.DataFrame
    ) -> pd.DataFrame:

        data["major_high"] = 0
        data["major_low"] = 0

        data["minor_high"] = 0
        data["minor_low"] = 0

        data["major_swing"] = 0

        data["swing_score"] = 0.0

        data["swing_id"] = 0

        swing_id = 1

        for i in range(len(data)):

            is_high = (
                data.iloc[i]["pivot_high"] == 1
            )

            is_low = (
                data.iloc[i]["pivot_low"] == 1
            )

            if not (is_high or is_low):
                continue

            score = float(
                data.iloc[i]["pivot_strength"]
            )

            data.at[
                data.index[i],
                "swing_score"
            ] = score

            data.at[
                data.index[i],
                "swing_id"
            ] = swing_id

            swing_id += 1

            if score >= 2.50:

                data.at[
                    data.index[i],
                    "major_swing"
                ] = 1

                if is_high:

                    data.at[
                        data.index[i],
                        "major_high"
                    ] = 1

                else:

                    data.at[
                        data.index[i],
                        "major_low"
                    ] = 1

            else:

                if is_high:

                    data.at[
                        data.index[i],
                        "minor_high"
                    ] = 1

                else:

                    data.at[
                        data.index[i],
                        "minor_low"
                    ] = 1

        return data

    # ==========================================================
    # Market Structure
    # ==========================================================

    def detect_structure(
        self,
        data: pd.DataFrame
    ) -> pd.DataFrame:

        data["HH"] = 0
        data["HL"] = 0
        data["LH"] = 0
        data["LL"] = 0

        data["structure"] = "NONE"

        data["last_major_high"] = np.nan
        data["last_major_low"] = np.nan

        last_high = None
        last_low = None

        for i in range(len(data)):

            if data.iloc[i]["major_high"] == 1:

                price = data.iloc[i]["high"]

                if last_high is not None:

                    if price > last_high:

                        data.at[data.index[i], "HH"] = 1
                        data.at[data.index[i], "structure"] = "HH"

                    else:

                        data.at[data.index[i], "LH"] = 1
                        data.at[data.index[i], "structure"] = "LH"

                last_high = price

            if data.iloc[i]["major_low"] == 1:

                price = data.iloc[i]["low"]

                if last_low is not None:

                    if price > last_low:

                        data.at[data.index[i], "HL"] = 1
                        data.at[data.index[i], "structure"] = "HL"

                    else:

                        data.at[data.index[i], "LL"] = 1
                        data.at[data.index[i], "structure"] = "LL"

                last_low = price

            data.at[data.index[i], "last_major_high"] = last_high
            data.at[data.index[i], "last_major_low"] = last_low

        return data

    # ==========================================================
    # Main Pipeline
    # ==========================================================

    def generate(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:

        data = df.copy()

        data["atr"] = self.calculate_atr(data)

        data = self.detect_pivots(data)

        data = self.classify_swings(data)

        data = self.detect_structure(data)

        return data


market_structure = MarketStructure()