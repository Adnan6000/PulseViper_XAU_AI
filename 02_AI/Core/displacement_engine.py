"""
===============================================================================
Module      : displacement_engine.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Institutional Displacement Detection Engine
===============================================================================
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class DisplacementEngine:

    def __init__(
        self,
        atr_period: int = 14,
        body_ratio_threshold: float = 0.70,
        atr_multiplier: float = 1.50,
    ):

        self.atr_period = atr_period
        self.body_ratio_threshold = body_ratio_threshold
        self.atr_multiplier = atr_multiplier

    # ==========================================================
    # ATR
    # ==========================================================

    def _atr(
        self,
        df: pd.DataFrame
    ) -> pd.Series:

        high_low = df["high"] - df["low"]

        high_close = (
            df["high"] -
            df["close"].shift()
        ).abs()

        low_close = (
            df["low"] -
            df["close"].shift()
        ).abs()

        tr = pd.concat(
            [
                high_low,
                high_close,
                low_close
            ],
            axis=1
        ).max(axis=1)

        return tr.rolling(
            self.atr_period,
            min_periods=1
        ).mean()

    # ==========================================================
    # Generate
    # ==========================================================

    def generate(
        self,
        data: pd.DataFrame
    ) -> pd.DataFrame:

        df = data.copy()

        df["atr"] = self._atr(df)

        df["body_size"] = (
            df["close"] - df["open"]
        ).abs()

        df["range_size"] = (
            df["high"] - df["low"]
        )

        df["upper_wick"] = (
            df["high"] -
            df[["open", "close"]].max(axis=1)
        )

        df["lower_wick"] = (
            df[["open", "close"]].min(axis=1) -
            df["low"]
        )

        df["body_ratio"] = (
            df["body_size"] /
            df["range_size"].replace(0, np.nan)
        ).fillna(0)

        df["atr_expansion"] = (
            df["range_size"] /
            df["atr"].replace(0, np.nan)
        ).fillna(0)

                # ======================================================
        # Institutional Displacement Logic
        # ======================================================

        df["is_displacement"] = (
            (df["body_ratio"] >= self.body_ratio_threshold)
            &
            (df["atr_expansion"] >= self.atr_multiplier)
        ).astype(int)

        # ======================================================
        # Displacement Score (0 - 100)
        # ======================================================

        score = (
            (df["body_ratio"] * 50)
            +
            (
                (
                    df["atr_expansion"] /
                    self.atr_multiplier
                ).clip(0, 1)
                * 50
            )
        )

        df["displacement_score"] = (
            score.clip(0, 100)
            .round(2)
        )

        # ======================================================
        # Impulse Strength
        # ======================================================

        df["impulse_strength"] = (
            df["body_size"] /
            df["atr"].replace(0, np.nan)
        ).fillna(0)

        # ======================================================
        # Institutional Move
        # ======================================================

        df["institutional_move"] = 0

        df.loc[
            (
                (df["is_displacement"] == 1)
                &
                (df["close"] > df["open"])
            ),
            "institutional_move"
        ] = 1

        df.loc[
            (
                (df["is_displacement"] == 1)
                &
                (df["close"] < df["open"])
            ),
            "institutional_move"
        ] = -1

        return df


displacement_engine = DisplacementEngine()