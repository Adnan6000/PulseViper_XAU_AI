"""
===============================================================================
Module      : liquidity_engine.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Institutional Liquidity Detection Engine
===============================================================================
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class LiquidityEngine:

    def __init__(
        self,
        tolerance: float = 0.10,
        lookback: int = 20,
    ):

        self.tolerance = tolerance
        self.lookback = lookback

    # ==========================================================
    # Main
    # ==========================================================

    def generate(
        self,
        data: pd.DataFrame
    ) -> pd.DataFrame:

        df = data.copy()

        # ------------------------------------------

        df["equal_high"] = 0

        df["equal_low"] = 0

        df["eqh_price"] = np.nan

        df["eql_price"] = np.nan

        # ------------------------------------------

        for i in range(self.lookback, len(df)):

            current_high = df.iloc[i]["high"]

            current_low = df.iloc[i]["low"]

            history = df.iloc[
                i-self.lookback:i
            ]

            # ======================================
            # Equal High
            # ======================================

            high_match = history[
                (
                    history["high"]
                    >=
                    current_high - self.tolerance
                )
                &
                (
                    history["high"]
                    <=
                    current_high + self.tolerance
                )
            ]

            if len(high_match) >= 2:

                df.at[
                    df.index[i],
                    "equal_high"
                ] = 1

                df.at[
                    df.index[i],
                    "eqh_price"
                ] = current_high

            # ======================================
            # Equal Low
            # ======================================

            low_match = history[
                (
                    history["low"]
                    >=
                    current_low - self.tolerance
                )
                &
                (
                    history["low"]
                    <=
                    current_low + self.tolerance
                )
            ]

            if len(low_match) >= 2:

                df.at[
                    df.index[i],
                    "equal_low"
                ] = 1

                df.at[
                    df.index[i],
                    "eql_price"
                ] = current_low

        return df


liquidity_engine = LiquidityEngine()