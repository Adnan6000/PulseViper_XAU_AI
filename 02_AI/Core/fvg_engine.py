"""
===============================================================================
Module      : fvg_engine.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Institutional Fair Value Gap Detection Engine
===============================================================================
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class FVGEngine:

    def __init__(
        self,
        atr_period: int = 14,
        min_gap_atr: float = 0.10,
        max_gap_atr: float = 5.00,
    ) -> None:

        self.atr_period = atr_period
        self.min_gap_atr = min_gap_atr
        self.max_gap_atr = max_gap_atr

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

        previous_close = close.shift(1)

        true_range = pd.concat(
            [
                high - low,
                (high - previous_close).abs(),
                (low - previous_close).abs(),
            ],
            axis=1,
        ).max(axis=1)

        return (
            true_range
            .rolling(
                self.atr_period,
                min_periods=1,
            )
            .mean()
            .astype("float64")
        )

    # ==========================================================
    # Validation
    # ==========================================================

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
            required - set(df.columns)
        )

        if missing:

            raise ValueError(
                "Missing required columns: "
                + ", ".join(
                    sorted(missing)
                )
            )

    # ==========================================================
    # Main Detection
    # ==========================================================

    def generate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        self._validate_input(data)

        df = data.copy()

        # ------------------------------------------------------
        # ATR
        # ------------------------------------------------------

        if "atr" not in df.columns:

            df["atr"] = (
                self.calculate_atr(df)
            )

        # ------------------------------------------------------
        # Output Columns
        # ------------------------------------------------------

        df["fvg_id"] = 0

        df["bullish_fvg"] = 0
        df["bearish_fvg"] = 0

        df["fvg_direction"] = "NONE"

        df["fvg_high"] = np.nan
        df["fvg_low"] = np.nan

        df["fvg_size"] = 0.0
        df["fvg_atr_ratio"] = 0.0

        df["fvg_active"] = 0
        df["fvg_mitigated"] = 0

        df["fvg_fill_percent"] = 0.0

        df["fvg_origin_index"] = -1

        # ------------------------------------------------------
        # NumPy arrays
        # ------------------------------------------------------

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

        close = np.asarray(
            pd.to_numeric(
                df["close"],
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

        # ======================================================
        # FVG Scan
        #
        # Bullish:
        # candle[i].low > candle[i-2].high
        #
        # Bearish:
        # candle[i].high < candle[i-2].low
        # ======================================================

        fvg_id = 1

        for i in range(
            2,
            len(df),
        ):

            if not (
                np.isfinite(
                    high[i]
                )
                and np.isfinite(
                    low[i]
                )
                and np.isfinite(
                    high[i - 2]
                )
                and np.isfinite(
                    low[i - 2]
                )
            ):
                continue

            atr_value = atr[i]

            if (
                not np.isfinite(
                    atr_value
                )
                or atr_value <= 0
            ):
                continue

            # ==================================================
            # Bullish FVG
            # ==================================================

            if low[i] > high[i - 2]:

                gap_low = high[i - 2]
                gap_high = low[i]

                gap_size = (
                    gap_high - gap_low
                )

                atr_ratio = (
                    gap_size / atr_value
                )

                if (
                    self.min_gap_atr
                    <= atr_ratio
                    <= self.max_gap_atr
                ):

                    df.at[
                        df.index[i],
                        "fvg_id"
                    ] = fvg_id

                    df.at[
                        df.index[i],
                        "bullish_fvg"
                    ] = 1

                    df.at[
                        df.index[i],
                        "fvg_direction"
                    ] = "BULLISH"

                    df.at[
                        df.index[i],
                        "fvg_high"
                    ] = gap_high

                    df.at[
                        df.index[i],
                        "fvg_low"
                    ] = gap_low

                    df.at[
                        df.index[i],
                        "fvg_size"
                    ] = gap_size

                    df.at[
                        df.index[i],
                        "fvg_atr_ratio"
                    ] = atr_ratio

                    df.at[
                        df.index[i],
                        "fvg_active"
                    ] = 1

                    df.at[
                        df.index[i],
                        "fvg_origin_index"
                    ] = i - 2

                    fvg_id += 1

            # ==================================================
            # Bearish FVG
            # ==================================================

            elif high[i] < low[i - 2]:

                gap_high = low[i - 2]
                gap_low = high[i]

                gap_size = (
                    gap_high - gap_low
                )

                atr_ratio = (
                    gap_size / atr_value
                )

                if (
                    self.min_gap_atr
                    <= atr_ratio
                    <= self.max_gap_atr
                ):

                    df.at[
                        df.index[i],
                        "fvg_id"
                    ] = fvg_id

                    df.at[
                        df.index[i],
                        "bearish_fvg"
                    ] = 1

                    df.at[
                        df.index[i],
                        "fvg_direction"
                    ] = "BEARISH"

                    df.at[
                        df.index[i],
                        "fvg_high"
                    ] = gap_high

                    df.at[
                        df.index[i],
                        "fvg_low"
                    ] = gap_low

                    df.at[
                        df.index[i],
                        "fvg_size"
                    ] = gap_size

                    df.at[
                        df.index[i],
                        "fvg_atr_ratio"
                    ] = atr_ratio

                    df.at[
                        df.index[i],
                        "fvg_active"
                    ] = 1

                    df.at[
                        df.index[i],
                        "fvg_origin_index"
                    ] = i - 2

                    fvg_id += 1

        # ======================================================
        # Historical Mitigation Tracking
        # ======================================================

        active_fvgs: list[dict[str, float | int | str]] = []

        for i in range(len(df)):

            current_high = high[i]
            current_low = low[i]

            if not (
                np.isfinite(
                    current_high
                )
                and np.isfinite(
                    current_low
                )
            ):
                continue

            # --------------------------------------------------
            # Register newly created FVG
            # --------------------------------------------------

            created_id = int(
                df.iloc[i]["fvg_id"]
            )

            if created_id > 0:

                direction = str(
                    df.iloc[i][
                        "fvg_direction"
                    ]
                )

                zone_high = float(
                    df.iloc[i]["fvg_high"]
                )

                zone_low = float(
                    df.iloc[i]["fvg_low"]
                )

                active_fvgs.append(
                    {
                        "id": created_id,
                        "direction": direction,
                        "high": zone_high,
                        "low": zone_low,
                        "fill": 0.0,
                    }
                )

            # --------------------------------------------------
            # Update existing zones
            # --------------------------------------------------

            for zone in active_fvgs:

                if zone["direction"] == "BULLISH":

                    zone_high = float(
                        zone["high"]
                    )

                    zone_low = float(
                        zone["low"]
                    )

                    zone_size = (
                        zone_high
                        - zone_low
                    )

                    if (
                        current_low
                        <= zone_high
                    ):

                        penetration = (
                            zone_high
                            - max(
                                current_low,
                                zone_low,
                            )
                        )

                        fill = (
                            penetration
                            / zone_size
                            * 100.0
                        )

                        zone["fill"] = float(
                            np.clip(
                                fill,
                                0.0,
                                100.0,
                            )
                        )

                    if (
                        current_low
                        <= zone_low
                    ):

                        zone["fill"] = 100.0

                elif zone["direction"] == "BEARISH":

                    zone_high = float(
                        zone["high"]
                    )

                    zone_low = float(
                        zone["low"]
                    )

                    zone_size = (
                        zone_high
                        - zone_low
                    )

                    if (
                        current_high
                        >= zone_low
                    ):

                        penetration = (
                            min(
                                current_high,
                                zone_high,
                            )
                            - zone_low
                        )

                        fill = (
                            penetration
                            / zone_size
                            * 100.0
                        )

                        zone["fill"] = float(
                            np.clip(
                                fill,
                                0.0,
                                100.0,
                            )
                        )

                    if (
                        current_high
                        >= zone_high
                    ):

                        zone["fill"] = 100.0

            # --------------------------------------------------
            # Write latest state to originating FVG
            # --------------------------------------------------

            for zone in active_fvgs:

                if int(zone["id"]) == int(
                    df.iloc[i]["fvg_id"]
                ):

                    continue

                # State is represented on
                # the latest candle only when
                # the FVG is interacted with.

                fill_value = float(
                    zone["fill"]
                )

                if fill_value <= 0:
                    continue

                # Find the original row.
                matches = np.flatnonzero(
                    df["fvg_id"].to_numpy()
                    == int(zone["id"])
                )

                if len(matches) == 0:
                    continue

                origin_row = int(
                    matches[0]
                )

                df.at[
                    df.index[origin_row],
                    "fvg_fill_percent"
                ] = fill_value

                if fill_value >= 100.0:

                    df.at[
                        df.index[origin_row],
                        "fvg_mitigated"
                    ] = 1

                    df.at[
                        df.index[origin_row],
                        "fvg_active"
                    ] = 0

        return df


# ==============================================================
# Global Engine Instance
# ==============================================================

fvg_engine = FVGEngine()