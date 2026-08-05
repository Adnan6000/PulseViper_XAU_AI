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

        # New Structure Columns
        data["HH"] = 0
        data["HL"] = 0
        data["LH"] = 0
        data["LL"] = 0

        last_high = None
        last_low = None

        previous_high_price = None
        previous_low_price = None

        w = self.swing_window

        for i in range(w, len(data) - w):

            current_high = data.iloc[i]["high"]

            if (
                current_high > data.iloc[i-w:i]["high"].max()
                and
                current_high >= data.iloc[i+1:i+w+1]["high"].max()
            ):

                data.at[data.index[i], "swing_high"] = 1
                data.at[data.index[i], "swing_high_price"] = current_high

                if previous_high_price is not None:

                    if current_high > previous_high_price:
                        data.at[data.index[i], "HH"] = 1
                    else:
                        data.at[data.index[i], "LH"] = 1

                previous_high_price = current_high
                last_high = i

            current_low = data.iloc[i]["low"]

            if (
                current_low < data.iloc[i-w:i]["low"].min()
                and
                current_low <= data.iloc[i+1:i+w+1]["low"].min()
            ):

                data.at[data.index[i], "swing_low"] = 1
                data.at[data.index[i], "swing_low_price"] = current_low

                if previous_low_price is not None:

                    if current_low > previous_low_price:
                        data.at[data.index[i], "HL"] = 1
                    else:
                        data.at[data.index[i], "LL"] = 1

                previous_low_price = current_low
                last_low = i

            if last_high is not None:
                data.at[data.index[i], "bars_since_high"] = i - last_high

            if last_low is not None:
                data.at[data.index[i], "bars_since_low"] = i - last_low

        return data


market_structure = MarketStructure()