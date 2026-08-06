"""
===============================================================================
Module      : bos_engine.py
Project     : PulseViper XAU AI
Version     : 2.0
Purpose     : Institutional Break of Structure Engine
===============================================================================
"""

from __future__ import annotations

import pandas as pd

import importlib

memory_module = importlib.import_module(
    "02_AI.Memory.bos_memory"
)

bos_memory = memory_module.bos_memory

class BOSEngine:

    def __init__(self):

        self.reset()

    # ==========================================================
    # Reset Runtime Memory
    # ==========================================================

    def reset(self):

        self.bos_counter = 1

        self.last_broken_high = None
        self.last_broken_low = None

    # ==========================================================
    # BOS Engine
    # ==========================================================

    def generate(
        self,
        data: pd.DataFrame
    ) -> pd.DataFrame:

        df = data.copy()

        # ------------------------------------------------------

        df["bos_id"] = 0

        df["bullish_bos"] = 0
        df["bearish_bos"] = 0

        df["bos_direction"] = "NONE"

        df["bos_price"] = 0.0

        df["bos_strength"] = 0.0

        df["bos_active"] = 0

        df["bos_confirmed"] = 0

        df["bos_invalidated"] = 0

        df["broken_swing_id"] = 0

        df["break_index"] = -1

        df["break_time"] = None

        df["break_distance"] = 0.0

        # ------------------------------------------------------

        last_major_high = None
        last_major_high_id = None

        last_major_low = None
        last_major_low_id = None

        # ------------------------------------------------------

        for i in range(len(df)):

            # ---------------------------------------------

            if df.iloc[i]["major_high"] == 1:

                last_major_high = df.iloc[i]["high"]

                last_major_high_id = df.iloc[i]["swing_id"]

            if df.iloc[i]["major_low"] == 1:

                last_major_low = df.iloc[i]["low"]

                last_major_low_id = df.iloc[i]["swing_id"]

            # ---------------------------------------------

            close = df.iloc[i]["close"]

            # =====================================================
            # Bullish BOS
            # =====================================================

            if (
                last_major_high is not None
                and
                close > last_major_high
                and
                self.last_broken_high != last_major_high
            ):

                self.last_broken_high = last_major_high

                df.at[df.index[i], "bos_id"] = self.bos_counter

                df.at[df.index[i], "bullish_bos"] = 1

                df.at[df.index[i], "bos_direction"] = "BULLISH"

                df.at[df.index[i], "bos_price"] = last_major_high

                df.at[df.index[i], "bos_strength"] = (
                    close - last_major_high
                )

                df.at[df.index[i], "bos_active"] = 1

                df.at[df.index[i], "bos_confirmed"] = 1

                df.at[df.index[i], "broken_swing_id"] = (
                    last_major_high_id
                )

                df.at[df.index[i], "break_index"] = i

                if "time" in df.columns:

                    df.at[df.index[i], "break_time"] = (
                        df.iloc[i]["time"]
                    )

                df.at[df.index[i], "break_distance"] = (
                    close - last_major_high
                )

                self.bos_counter += 1

            # =====================================================
            # Bearish BOS
            # =====================================================

            if (
                last_major_low is not None
                and
                close < last_major_low
                and
                self.last_broken_low != last_major_low
            ):

                self.last_broken_low = last_major_low

                df.at[df.index[i], "bos_id"] = self.bos_counter

                df.at[df.index[i], "bearish_bos"] = 1

                df.at[df.index[i], "bos_direction"] = "BEARISH"

                df.at[df.index[i], "bos_price"] = last_major_low

                df.at[df.index[i], "bos_strength"] = (
                    last_major_low - close
                )

                df.at[df.index[i], "bos_active"] = 1

                df.at[df.index[i], "bos_confirmed"] = 1

                df.at[df.index[i], "broken_swing_id"] = (
                    last_major_low_id
                )

                df.at[df.index[i], "break_index"] = i

                if "time" in df.columns:

                    df.at[df.index[i], "break_time"] = (
                        df.iloc[i]["time"]
                    )

                df.at[df.index[i], "break_distance"] = (
                    last_major_low - close
                )

                self.bos_counter += 1

        return df


bos_engine = BOSEngine()