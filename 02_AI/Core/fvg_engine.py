"""
===============================================================================
Module      : fvg_engine.py
Project     : PulseViper XAU AI
Version     : 1.1
Author      : Muhammad Adnan
Purpose     : Institutional Fair Value Gap Detection Engine
===============================================================================

Architecture
------------
FVGEngine owns ONLY FVG creation/detection.

FVG lifecycle responsibilities such as:
- mitigation
- fill percentage
- rejection
- lifecycle state

belong to:

    02_AI.Core.fvg_mitigation_engine.FVGMitigationEngine

Keeping lifecycle logic out of this detector avoids duplicate calculations
and prevents historical FVG scans from becoming increasingly expensive as
the dataset grows.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class FVGEngine:
    """
    Detect bullish and bearish three-candle Fair Value Gaps.

    Bullish FVG:
        current low > high two candles earlier

    Bearish FVG:
        current high < low two candles earlier

    Gap size is normalized by ATR so extremely small/noisy gaps
    can be rejected while preserving timeframe independence.
    """

    def __init__(
        self,
        atr_period: int = 14,
        min_gap_atr: float = 0.10,
        max_gap_atr: float = 5.00,
    ) -> None:

        if atr_period <= 0:
            raise ValueError(
                "atr_period must be greater than zero"
            )

        if min_gap_atr < 0:
            raise ValueError(
                "min_gap_atr cannot be negative"
            )

        if max_gap_atr <= min_gap_atr:
            raise ValueError(
                "max_gap_atr must be greater than min_gap_atr"
            )

        self.atr_period = int(
            atr_period
        )

        self.min_gap_atr = float(
            min_gap_atr
        )

        self.max_gap_atr = float(
            max_gap_atr
        )

    # =========================================================================
    # Input Validation
    # =========================================================================

    @staticmethod
    def _validate_input(
        df: pd.DataFrame,
    ) -> None:

        required = {
            "open",
            "high",
            "low",
            "close",
        }

        missing = (
            required
            - set(df.columns)
        )

        if missing:

            raise ValueError(
                "Missing required columns: "
                + ", ".join(
                    sorted(missing)
                )
            )

    # =========================================================================
    # ATR
    # =========================================================================

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

        previous_close = (
            close.shift(1)
        )

        true_range = pd.concat(
            [
                high - low,
                (
                    high
                    - previous_close
                ).abs(),
                (
                    low
                    - previous_close
                ).abs(),
            ],
            axis=1,
        ).max(
            axis=1
        )

        return (
            true_range
            .rolling(
                window=self.atr_period,
                min_periods=1,
            )
            .mean()
            .astype(
                "float64"
            )
        )

    # =========================================================================
    # Main Detection
    # =========================================================================

    def generate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        self._validate_input(
            data
        )

        df = data.copy()

        # ---------------------------------------------------------------------
        # ATR
        # ---------------------------------------------------------------------

        if "atr" not in df.columns:

            df["atr"] = (
                self.calculate_atr(
                    df
                )
            )

        # ---------------------------------------------------------------------
        # Output Contract
        #
        # Lifecycle fields are initialized here because downstream modules
        # expect them, but FVGEngine does NOT calculate historical mitigation.
        # FVGMitigationEngine owns that responsibility.
        # ---------------------------------------------------------------------

        df["fvg_id"] = 0

        df["bullish_fvg"] = 0
        df["bearish_fvg"] = 0

        df["fvg_direction"] = (
            "NONE"
        )

        df["fvg_high"] = np.nan
        df["fvg_low"] = np.nan

        df["fvg_size"] = 0.0
        df["fvg_atr_ratio"] = 0.0

        df["fvg_active"] = 0
        df["fvg_mitigated"] = 0
        df["fvg_fill_percent"] = 0.0

        df["fvg_origin_index"] = -1

        # ---------------------------------------------------------------------
        # Numeric Arrays
        # ---------------------------------------------------------------------

        high = np.asarray(
            pd.to_numeric(
                df["high"],
                errors="coerce",
            ),
            dtype=np.float64,
        )

        low = np.asarray(
            pd.to_numeric(
                df["low"],
                errors="coerce",
            ),
            dtype=np.float64,
        )

        atr = np.asarray(
            pd.to_numeric(
                df["atr"],
                errors="coerce",
            ),
            dtype=np.float64,
        )

        row_count = len(
            df
        )

        # ---------------------------------------------------------------------
        # Preallocated Result Arrays
        #
        # This avoids repeated df.at/df.iloc writes inside the hot loop.
        # ---------------------------------------------------------------------

        fvg_ids = np.zeros(
            row_count,
            dtype=np.int64,
        )

        bullish_fvg = np.zeros(
            row_count,
            dtype=np.int8,
        )

        bearish_fvg = np.zeros(
            row_count,
            dtype=np.int8,
        )

        fvg_direction = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        fvg_high = np.full(
            row_count,
            np.nan,
            dtype=np.float64,
        )

        fvg_low = np.full(
            row_count,
            np.nan,
            dtype=np.float64,
        )

        fvg_size = np.zeros(
            row_count,
            dtype=np.float64,
        )

        fvg_atr_ratio = np.zeros(
            row_count,
            dtype=np.float64,
        )

        fvg_active = np.zeros(
            row_count,
            dtype=np.int8,
        )

        fvg_origin_index = np.full(
            row_count,
            -1,
            dtype=np.int64,
        )

        # =========================================================================
        # FVG Detection
        # =========================================================================

        next_fvg_id = 1

        for i in range(
            2,
            row_count,
        ):

            current_high = (
                high[i]
            )

            current_low = (
                low[i]
            )

            previous_two_high = (
                high[i - 2]
            )

            previous_two_low = (
                low[i - 2]
            )

            atr_value = (
                atr[i]
            )

            if not (
                np.isfinite(
                    current_high
                )
                and np.isfinite(
                    current_low
                )
                and np.isfinite(
                    previous_two_high
                )
                and np.isfinite(
                    previous_two_low
                )
                and np.isfinite(
                    atr_value
                )
                and atr_value > 0.0
            ):
                continue

            # =================================================================
            # Bullish FVG
            # =================================================================

            if (
                current_low
                >
                previous_two_high
            ):

                gap_low = (
                    previous_two_high
                )

                gap_high = (
                    current_low
                )

                gap_size = (
                    gap_high
                    - gap_low
                )

                atr_ratio = (
                    gap_size
                    / atr_value
                )

                if (
                    self.min_gap_atr
                    <= atr_ratio
                    <= self.max_gap_atr
                ):

                    fvg_ids[i] = (
                        next_fvg_id
                    )

                    bullish_fvg[i] = 1

                    fvg_direction[i] = (
                        "BULLISH"
                    )

                    fvg_high[i] = (
                        gap_high
                    )

                    fvg_low[i] = (
                        gap_low
                    )

                    fvg_size[i] = (
                        gap_size
                    )

                    fvg_atr_ratio[i] = (
                        atr_ratio
                    )

                    fvg_active[i] = 1

                    fvg_origin_index[i] = (
                        i - 2
                    )

                    next_fvg_id += 1

            # =================================================================
            # Bearish FVG
            # =================================================================

            elif (
                current_high
                <
                previous_two_low
            ):

                gap_high = (
                    previous_two_low
                )

                gap_low = (
                    current_high
                )

                gap_size = (
                    gap_high
                    - gap_low
                )

                atr_ratio = (
                    gap_size
                    / atr_value
                )

                if (
                    self.min_gap_atr
                    <= atr_ratio
                    <= self.max_gap_atr
                ):

                    fvg_ids[i] = (
                        next_fvg_id
                    )

                    bearish_fvg[i] = 1

                    fvg_direction[i] = (
                        "BEARISH"
                    )

                    fvg_high[i] = (
                        gap_high
                    )

                    fvg_low[i] = (
                        gap_low
                    )

                    fvg_size[i] = (
                        gap_size
                    )

                    fvg_atr_ratio[i] = (
                        atr_ratio
                    )

                    fvg_active[i] = 1

                    fvg_origin_index[i] = (
                        i - 2
                    )

                    next_fvg_id += 1

        # =========================================================================
        # Assign Results
        # =========================================================================

        df["fvg_id"] = (
            fvg_ids
        )

        df["bullish_fvg"] = (
            bullish_fvg
        )

        df["bearish_fvg"] = (
            bearish_fvg
        )

        df["fvg_direction"] = (
            fvg_direction
        )

        df["fvg_high"] = (
            fvg_high
        )

        df["fvg_low"] = (
            fvg_low
        )

        df["fvg_size"] = (
            fvg_size
        )

        df["fvg_atr_ratio"] = (
            fvg_atr_ratio
        )

        df["fvg_active"] = (
            fvg_active
        )

        df["fvg_origin_index"] = (
            fvg_origin_index
        )

        return df


# =============================================================================
# Global Engine Instance
# =============================================================================

fvg_engine = FVGEngine()