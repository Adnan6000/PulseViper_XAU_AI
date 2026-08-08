"""
===============================================================================
Module      : market_structure.py
Project     : PulseViper XAU AI
Version     : 5.2
Author      : PulseViper AI
Purpose     : Institutional Market Structure & Swing Contract Engine
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
        major_strength: float = 2.50,
    ) -> None:

        self.pivot_window = pivot_window
        self.atr_period = atr_period
        self.min_strength = min_strength
        self.major_strength = major_strength

    # ==========================================================
    # Validation
    # ==========================================================

    @staticmethod
    def _validate_input(
        df: pd.DataFrame,
    ) -> None:

        required_columns = {
            "open",
            "high",
            "low",
            "close",
        }

        missing_columns = (
            required_columns
            - set(df.columns)
        )

        if missing_columns:

            raise ValueError(
                "Missing required columns: "
                + ", ".join(
                    sorted(missing_columns)
                )
            )

    # ==========================================================
    # ATR
    # ==========================================================

    def calculate_atr(
        self,
        df: pd.DataFrame,
    ) -> pd.Series:

        high = pd.to_numeric(
            df["high"],
            errors="coerce",
        )

        low = pd.to_numeric(
            df["low"],
            errors="coerce",
        )

        close = pd.to_numeric(
            df["close"],
            errors="coerce",
        )

        high_low = (
            high - low
        )

        high_close = (
            high - close.shift(1)
        ).abs()

        low_close = (
            low - close.shift(1)
        ).abs()

        true_range = pd.concat(
            [
                high_low,
                high_close,
                low_close,
            ],
            axis=1,
        ).max(axis=1)

        atr = true_range.rolling(
            window=self.atr_period,
            min_periods=1,
        ).mean()

        return atr.astype("float64")

    # ==========================================================
    # Pivot Detection
    # ==========================================================

    def detect_pivots(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        window = self.pivot_window

        df["pivot_high"] = 0
        df["pivot_low"] = 0
        df["pivot_strength"] = 0.0

        if len(df) <= window * 2:

            return df

        # ------------------------------------------------------
        # Convert to NumPy arrays.
        #
        # This avoids Pandas Scalar typing problems in Pylance.
        # ------------------------------------------------------

        high_values = np.asarray(
            pd.to_numeric(
                df["high"],
                errors="coerce",
            ),
            dtype=np.float64,
        )

        low_values = np.asarray(
            pd.to_numeric(
                df["low"],
                errors="coerce",
            ),
            dtype=np.float64,
        )

        atr_values = np.asarray(
            pd.to_numeric(
                df["atr"],
                errors="coerce",
            ),
            dtype=np.float64,
        )

        pivot_high = np.zeros(
            len(df),
            dtype=np.int8,
        )

        pivot_low = np.zeros(
            len(df),
            dtype=np.int8,
        )

        pivot_strength = np.zeros(
            len(df),
            dtype=np.float64,
        )

        # ======================================================
        # Pivot Scan
        # ======================================================

        for i in range(
            window,
            len(df) - window,
        ):

            current_high = high_values[i]
            current_low = low_values[i]

            left_high = np.max(
                high_values[
                    i - window:i
                ]
            )

            right_high = np.max(
                high_values[
                    i + 1:i + window + 1
                ]
            )

            left_low = np.min(
                low_values[
                    i - window:i
                ]
            )

            right_low = np.min(
                low_values[
                    i + 1:i + window + 1
                ]
            )

            atr_value = atr_values[i]

            if (
                not np.isfinite(
                    current_high
                )
                or
                not np.isfinite(
                    current_low
                )
            ):
                continue

            # --------------------------------------------------
            # ATR validity
            #
            # Geometry can still identify a pivot even when ATR
            # is invalid, but invalid ATR must never manufacture
            # artificial structural strength.
            # --------------------------------------------------

            atr_is_valid = (
                np.isfinite(
                    atr_value
                )
                and
                atr_value > 0
            )

            # ==================================================
            # Pivot High
            # ==================================================

            if (
                current_high > left_high
                and
                current_high >= right_high
            ):

                pivot_high[i] = 1

                if atr_is_valid:

                    strength = (
                        current_high
                        - max(
                            left_high,
                            right_high,
                        )
                    ) / atr_value

                    pivot_strength[i] = max(
                        pivot_strength[i],
                        strength,
                    )

            # ==================================================
            # Pivot Low
            # ==================================================

            if (
                current_low < left_low
                and
                current_low <= right_low
            ):

                pivot_low[i] = 1

                if atr_is_valid:

                    strength = (
                        min(
                            left_low,
                            right_low,
                        )
                        - current_low
                    ) / atr_value

                    pivot_strength[i] = max(
                        pivot_strength[i],
                        strength,
                    )

        # ------------------------------------------------------
        # Assign back to DataFrame
        # ------------------------------------------------------

        df["pivot_high"] = pivot_high

        df["pivot_low"] = pivot_low

        df["pivot_strength"] = (
            pivot_strength
        )

        return df

    # ==========================================================
    # Swing Classification
    # ==========================================================

    def classify_swings(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        df["major_high"] = 0
        df["major_low"] = 0

        df["minor_high"] = 0
        df["minor_low"] = 0

        df["major_swing"] = 0

        df["swing_score"] = 0.0

        df["swing_id"] = 0

        df["swing_type"] = "NONE"

        df["swing_price"] = np.nan

        # ------------------------------------------------------
        # NumPy arrays for type-safe iteration
        # ------------------------------------------------------

        pivot_high_values = np.asarray(
            df["pivot_high"],
            dtype=np.int8,
        )

        pivot_low_values = np.asarray(
            df["pivot_low"],
            dtype=np.int8,
        )

        strength_values = np.asarray(
            df["pivot_strength"],
            dtype=np.float64,
        )

        high_values = np.asarray(
            pd.to_numeric(
                df["high"],
                errors="coerce",
            ),
            dtype=np.float64,
        )

        low_values = np.asarray(
            pd.to_numeric(
                df["low"],
                errors="coerce",
            ),
            dtype=np.float64,
        )

        major_high = np.zeros(
            len(df),
            dtype=np.int8,
        )

        major_low = np.zeros(
            len(df),
            dtype=np.int8,
        )

        minor_high = np.zeros(
            len(df),
            dtype=np.int8,
        )

        minor_low = np.zeros(
            len(df),
            dtype=np.int8,
        )

        major_swing = np.zeros(
            len(df),
            dtype=np.int8,
        )

        swing_score = np.zeros(
            len(df),
            dtype=np.float64,
        )

        swing_id_values = np.zeros(
            len(df),
            dtype=np.int64,
        )

        swing_type = np.full(
            len(df),
            "NONE",
            dtype=object,
        )

        swing_price = np.full(
            len(df),
            np.nan,
            dtype=np.float64,
        )

        swing_id = 1

        # ======================================================
        # Classification
        # ======================================================

        for i in range(len(df)):

            is_high = (
                pivot_high_values[i] == 1
            )

            is_low = (
                pivot_low_values[i] == 1
            )

            if not is_high and not is_low:
                continue

            score = strength_values[i]

            # --------------------------------------------------
            # A geometric pivot does NOT automatically become
            # a structural swing.
            #
            # Only pivots meeting min_strength receive:
            # - swing_id
            # - swing_type
            # - swing_score
            # - major/minor classification
            # --------------------------------------------------

            if (
                not np.isfinite(
                    score
                )
                or
                score < self.min_strength
            ):
                continue

            swing_score[i] = score

            swing_id_values[i] = (
                swing_id
            )

            # ==================================================
            # HIGH SWING
            # ==================================================

            if is_high:

                swing_type[i] = "HIGH"

                swing_price[i] = (
                    high_values[i]
                )

                if (
                    score >=
                    self.major_strength
                ):

                    major_high[i] = 1
                    major_swing[i] = 1

                elif (
                    score >=
                    self.min_strength
                ):

                    minor_high[i] = 1

            # ==================================================
            # LOW SWING
            # ==================================================

            elif is_low:

                swing_type[i] = "LOW"

                swing_price[i] = (
                    low_values[i]
                )

                if (
                    score >=
                    self.major_strength
                ):

                    major_low[i] = 1
                    major_swing[i] = 1

                elif (
                    score >=
                    self.min_strength
                ):

                    minor_low[i] = 1

            swing_id += 1

        # ------------------------------------------------------
        # Assign results
        # ------------------------------------------------------

        df["major_high"] = major_high
        df["major_low"] = major_low

        df["minor_high"] = minor_high
        df["minor_low"] = minor_low

        df["major_swing"] = major_swing

        df["swing_score"] = swing_score

        df["swing_id"] = swing_id_values

        df["swing_type"] = swing_type

        df["swing_price"] = swing_price

        return df

    # ==========================================================
    # Market Structure Classification
    # ==========================================================

    def detect_structure(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        df["HH"] = 0
        df["HL"] = 0

        df["LH"] = 0
        df["LL"] = 0

        df["structure"] = "NONE"

        df["last_major_high"] = np.nan
        df["last_major_low"] = np.nan

        # ------------------------------------------------------
        # NumPy arrays
        # ------------------------------------------------------

        major_high_values = np.asarray(
            df["major_high"],
            dtype=np.int8,
        )

        major_low_values = np.asarray(
            df["major_low"],
            dtype=np.int8,
        )

        high_values = np.asarray(
            pd.to_numeric(
                df["high"],
                errors="coerce",
            ),
            dtype=np.float64,
        )

        low_values = np.asarray(
            pd.to_numeric(
                df["low"],
                errors="coerce",
            ),
            dtype=np.float64,
        )

        hh = np.zeros(
            len(df),
            dtype=np.int8,
        )

        hl = np.zeros(
            len(df),
            dtype=np.int8,
        )

        lh = np.zeros(
            len(df),
            dtype=np.int8,
        )

        ll = np.zeros(
            len(df),
            dtype=np.int8,
        )

        structure = np.full(
            len(df),
            "NONE",
            dtype=object,
        )

        last_major_high_values = (
            np.full(
                len(df),
                np.nan,
                dtype=np.float64,
            )
        )

        last_major_low_values = (
            np.full(
                len(df),
                np.nan,
                dtype=np.float64,
            )
        )

        last_high: float | None = None
        last_low: float | None = None

        # ======================================================
        # Structure Scan
        # ======================================================

        for i in range(len(df)):

            # ==================================================
            # Major High
            # ==================================================

            if major_high_values[i] == 1:

                price = high_values[i]

                if (
                    last_high is not None
                ):

                    if price > last_high:

                        hh[i] = 1
                        structure[i] = "HH"

                    elif price < last_high:

                        lh[i] = 1
                        structure[i] = "LH"

                last_high = price

            # ==================================================
            # Major Low
            # ==================================================

            if major_low_values[i] == 1:

                price = low_values[i]

                if (
                    last_low is not None
                ):

                    if price > last_low:

                        hl[i] = 1
                        structure[i] = "HL"

                    elif price < last_low:

                        ll[i] = 1
                        structure[i] = "LL"

                last_low = price

            if last_high is not None:

                last_major_high_values[i] = (
                    last_high
                )

            if last_low is not None:

                last_major_low_values[i] = (
                    last_low
                )

        # ------------------------------------------------------
        # Assign results
        # ------------------------------------------------------

        df["HH"] = hh
        df["HL"] = hl

        df["LH"] = lh
        df["LL"] = ll

        df["structure"] = structure

        df["last_major_high"] = (
            last_major_high_values
        )

        df["last_major_low"] = (
            last_major_low_values
        )

        return df

    # ==========================================================
    # Persistent Structure Bias
    # ==========================================================

    def add_structure_state(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        structure_values = (
            np.asarray(
                df["structure"],
                dtype=object,
            )
        )

        bias_values = np.full(
            len(df),
            "NEUTRAL",
            dtype=object,
        )

        bias = "NEUTRAL"

        for i in range(len(df)):

            current_structure = (
                structure_values[i]
            )

            if current_structure in (
                "HH",
                "HL",
            ):

                bias = "BULLISH"

            elif current_structure in (
                "LH",
                "LL",
            ):

                bias = "BEARISH"

            bias_values[i] = bias

        df["structure_bias"] = (
            bias_values
        )

        return df

    # ==========================================================
    # Main Pipeline
    # ==========================================================

    def generate(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        self._validate_input(df)

        data = df.copy()

        # ------------------------------------------------------
        # 1. ATR
        # ------------------------------------------------------

        data["atr"] = (
            self.calculate_atr(data)
        )

        # ------------------------------------------------------
        # 2. Pivot Detection
        # ------------------------------------------------------

        data = self.detect_pivots(
            data
        )

        # ------------------------------------------------------
        # 3. Swing Classification
        # ------------------------------------------------------

        data = self.classify_swings(
            data
        )

        # ------------------------------------------------------
        # 4. HH / HL / LH / LL
        # ------------------------------------------------------

        data = self.detect_structure(
            data
        )

        # ------------------------------------------------------
        # 5. Persistent Bias
        # ------------------------------------------------------

        data = self.add_structure_state(
            data
        )

        return data


# ==============================================================
# Global Engine Instance
# ==============================================================

market_structure = MarketStructure()