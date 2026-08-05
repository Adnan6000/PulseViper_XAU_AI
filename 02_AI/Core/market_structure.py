"""
===============================================================================
Module      : market_structure.py
Project     : PulseViper XAU AI
Version     : 3.2
Purpose     : Market Structure Engine (Phase 1 - Swing Detection)
===============================================================================
"""

import pandas as pd
import numpy as np


class MarketStructure:

    def __init__(
        self,
        swing_window: int = 5,
        min_distance: int = 3
    ):

        self.swing_window = swing_window
        self.min_distance = min_distance

    def generate(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:

        data = df.copy()

        data["swing_high"] = 0
        data["swing_low"] = 0

        data["swing_high_price"] = np.nan
        data["swing_low_price"] = np.nan

        data["bars_since_high"] = np.nan
        data["bars_since_low"] = np.nan

        last_high = None
        last_low = None

        w = self.swing_window

        for i in range(w, len(data) - w):

            current_high = data.iloc[i]["high"]

            left_high = data.iloc[i-w:i]["high"].max()

            right_high = data.iloc[i+1:i+w+1]["high"].max()

            if (
                current_high > left_high
                and
                current_high >= right_high
            ):

                data.at[data.index[i], "swing_high"] = 1
                data.at[data.index[i], "swing_high_price"] = current_high

                last_high = i

            current_low = data.iloc[i]["low"]

            left_low = data.iloc[i-w:i]["low"].min()

            right_low = data.iloc[i+1:i+w+1]["low"].min()

            if (
                current_low < left_low
                and
                current_low <= right_low
            ):

                data.at[data.index[i], "swing_low"] = 1
                data.at[data.index[i], "swing_low_price"] = current_low

                last_low = i

            if last_high is not None:

                data.at[
                    data.index[i],
                    "bars_since_high"
                ] = i - last_high

            if last_low is not None:

                data.at[
                    data.index[i],
                    "bars_since_low"
                ] = i - last_low

        return data


market_structure = MarketStructure()