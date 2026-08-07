"""
===============================================================================
Module      : fvg_mitigation_engine.py
Project     : PulseViper XAU AI
Version     : 1.1
Purpose     : Institutional FVG Mitigation & Lifecycle Engine
===============================================================================
"""

from __future__ import annotations

from typing import Any

import pandas as pd


class FVGMitigationEngine:

    def __init__(
        self,
        full_mitigation: float = 1.0,
        rejection_threshold: float = 0.25,
    ) -> None:

        self.full_mitigation = float(full_mitigation)
        self.rejection_threshold = float(rejection_threshold)

    # =========================================================================
    # Type-safe helpers
    # =========================================================================

    @staticmethod
    def _to_float(value: Any, default: float = 0.0) -> float:
        """
        Safely convert Pandas/NumPy scalar values to Python float.
        """

        if value is None:
            return default

        try:
            if pd.isna(value):
                return default
        except (TypeError, ValueError):
            return default

        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    # =========================================================================
    # Main
    # =========================================================================

    def generate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        # ---------------------------------------------------------------------
        # Required columns
        # ---------------------------------------------------------------------

        required_columns = [
            "fvg_id",
            "bullish_fvg",
            "bearish_fvg",
            "fvg_high",
            "fvg_low",
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Missing required FVG columns: {missing_columns}"
            )

        # ---------------------------------------------------------------------
        # Output columns
        # ---------------------------------------------------------------------

        df["fvg_mitigated"] = 0
        df["fvg_active"] = 0
        df["fvg_fill_percent"] = 0.0

        df["fvg_mitigation_index"] = -1
        df["fvg_mitigation_price"] = float("nan")

        df["fvg_rejection"] = 0
        df["fvg_rejection_strength"] = 0.0

        # ---------------------------------------------------------------------
        # Active FVG registry
        # ---------------------------------------------------------------------

        active_fvgs: dict[int, dict[str, Any]] = {}

        # =========================================================================
        # Candle processing
        # =========================================================================

        for i in range(len(df)):

            row = df.iloc[i]

            # -----------------------------------------------------------------
            # Register new FVG
            # -----------------------------------------------------------------

            raw_fvg_id = row["fvg_id"]

            fvg_id_float = self._to_float(
                raw_fvg_id,
                default=0.0,
            )

            if fvg_id_float != 0.0:

                fvg_id = int(fvg_id_float)

                bullish = self._to_float(
                    row["bullish_fvg"],
                    default=0.0,
                )

                bearish = self._to_float(
                    row["bearish_fvg"],
                    default=0.0,
                )

                direction = "NONE"

                if bullish == 1.0:
                    direction = "BULLISH"

                elif bearish == 1.0:
                    direction = "BEARISH"

                if direction != "NONE":

                    zone_high = self._to_float(
                        row["fvg_high"]
                    )

                    zone_low = self._to_float(
                        row["fvg_low"]
                    )

                    if zone_high > zone_low:

                        active_fvgs[fvg_id] = {
                            "direction": direction,
                            "high": zone_high,
                            "low": zone_low,
                            "origin_index": i,
                        }

            # -----------------------------------------------------------------
            # Nothing to process
            # -----------------------------------------------------------------

            if not active_fvgs:
                continue

            # -----------------------------------------------------------------
            # Current candle values
            # -----------------------------------------------------------------

            candle_high = self._to_float(
                row["high"]
            )

            candle_low = self._to_float(
                row["low"]
            )

            candle_close = self._to_float(
                row["close"]
            )

            # -----------------------------------------------------------------
            # Process active FVGs
            # -----------------------------------------------------------------

            for current_id, zone in list(
                active_fvgs.items()
            ):

                origin_index = int(
                    zone["origin_index"]
                )

                # Never mitigate on creation candle.
                if i <= origin_index:
                    continue

                direction = str(
                    zone["direction"]
                )

                zone_high = self._to_float(
                    zone["high"]
                )

                zone_low = self._to_float(
                    zone["low"]
                )

                zone_size = zone_high - zone_low

                if zone_size <= 0.0:
                    del active_fvgs[current_id]
                    continue

                # =================================================================
                # BULLISH FVG
                # =================================================================

                if direction == "BULLISH":

                    # Price is completely above the FVG.
                    if candle_low > zone_high:
                        continue

                    # -------------------------------------------------------------
                    # Calculate penetration
                    # -------------------------------------------------------------

                    penetration = (
                        zone_high - candle_low
                    )

                    fill_ratio = (
                        penetration / zone_size
                    )

                    if fill_ratio < 0.0:
                        fill_ratio = 0.0

                    if fill_ratio > 1.0:
                        fill_ratio = 1.0

                    fill_percent = (
                        fill_ratio * 100.0
                    )

                    # -------------------------------------------------------------
                    # Rejection
                    #
                    # Price enters FVG and closes back above it.
                    # -------------------------------------------------------------

                    rejection = (
                        candle_close > zone_high
                        and
                        fill_ratio >= self.rejection_threshold
                    )

                    # -------------------------------------------------------------
                    # Full mitigation
                    # -------------------------------------------------------------

                    fully_mitigated = (
                        candle_low <= zone_low
                    )

                    current_fill = self._to_float(
                        df.at[
                            df.index[i],
                            "fvg_fill_percent",
                        ]
                    )

                    if fill_percent > current_fill:

                        df.at[
                            df.index[i],
                            "fvg_fill_percent",
                        ] = round(
                            fill_percent,
                            2,
                        )

                    # -------------------------------------------------------------
                    # Rejection event
                    # -------------------------------------------------------------

                    if rejection:

                        df.at[
                            df.index[i],
                            "fvg_rejection",
                        ] = 1

                        df.at[
                            df.index[i],
                            "fvg_rejection_strength",
                        ] = round(
                            fill_percent,
                            2,
                        )

                    # -------------------------------------------------------------
                    # Full mitigation event
                    # -------------------------------------------------------------

                    if fully_mitigated:

                        df.at[
                            df.index[i],
                            "fvg_mitigated",
                        ] = 1

                        df.at[
                            df.index[i],
                            "fvg_active",
                        ] = 0

                        df.at[
                            df.index[i],
                            "fvg_mitigation_index",
                        ] = i

                        df.at[
                            df.index[i],
                            "fvg_mitigation_price",
                        ] = candle_low

                        del active_fvgs[current_id]

                        continue

                    # -------------------------------------------------------------
                    # FVG remains active
                    # -------------------------------------------------------------

                    df.at[
                        df.index[i],
                        "fvg_active",
                    ] = 1

                # =================================================================
                # BEARISH FVG
                # =================================================================

                elif direction == "BEARISH":

                    # Price is completely below the FVG.
                    if candle_high < zone_low:
                        continue

                    # -------------------------------------------------------------
                    # Calculate penetration
                    # -------------------------------------------------------------

                    penetration = (
                        candle_high - zone_low
                    )

                    fill_ratio = (
                        penetration / zone_size
                    )

                    if fill_ratio < 0.0:
                        fill_ratio = 0.0

                    if fill_ratio > 1.0:
                        fill_ratio = 1.0

                    fill_percent = (
                        fill_ratio * 100.0
                    )

                    # -------------------------------------------------------------
                    # Rejection
                    #
                    # Price enters FVG and closes back below it.
                    # -------------------------------------------------------------

                    rejection = (
                        candle_close < zone_low
                        and
                        fill_ratio >= self.rejection_threshold
                    )

                    # -------------------------------------------------------------
                    # Full mitigation
                    # -------------------------------------------------------------

                    fully_mitigated = (
                        candle_high >= zone_high
                    )

                    current_fill = self._to_float(
                        df.at[
                            df.index[i],
                            "fvg_fill_percent",
                        ]
                    )

                    if fill_percent > current_fill:

                        df.at[
                            df.index[i],
                            "fvg_fill_percent",
                        ] = round(
                            fill_percent,
                            2,
                        )

                    # -------------------------------------------------------------
                    # Rejection event
                    # -------------------------------------------------------------

                    if rejection:

                        df.at[
                            df.index[i],
                            "fvg_rejection",
                        ] = 1

                        df.at[
                            df.index[i],
                            "fvg_rejection_strength",
                        ] = round(
                            fill_percent,
                            2,
                        )

                    # -------------------------------------------------------------
                    # Full mitigation event
                    # -------------------------------------------------------------

                    if fully_mitigated:

                        df.at[
                            df.index[i],
                            "fvg_mitigated",
                        ] = 1

                        df.at[
                            df.index[i],
                            "fvg_active",
                        ] = 0

                        df.at[
                            df.index[i],
                            "fvg_mitigation_index",
                        ] = i

                        df.at[
                            df.index[i],
                            "fvg_mitigation_price",
                        ] = candle_high

                        del active_fvgs[current_id]

                        continue

                    # -------------------------------------------------------------
                    # FVG remains active
                    # -------------------------------------------------------------

                    df.at[
                        df.index[i],
                        "fvg_active",
                    ] = 1

        return df


fvg_mitigation_engine = FVGMitigationEngine()