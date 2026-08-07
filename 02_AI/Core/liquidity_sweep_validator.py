"""
===============================================================================
Module      : liquidity_sweep_validator.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Institutional Liquidity Sweep Validation Engine
===============================================================================
"""

from __future__ import annotations

import pandas as pd


class LiquiditySweepValidator:

    def __init__(
        self,
        require_displacement: bool = True,
        require_bos: bool = True,
        min_displacement_score: float = 60.0,
    ) -> None:

        self.require_displacement = (
            require_displacement
        )

        self.require_bos = require_bos

        self.min_displacement_score = (
            min_displacement_score
        )

    # ==========================================================
    # Validate Required Columns
    # ==========================================================

    def _validate_columns(
        self,
        df: pd.DataFrame,
    ) -> None:

        required = {
            "buy_side_sweep",
            "sell_side_sweep",
            "sweep_price",
            "sweep_liquidity_id",
            "is_displacement",
            "displacement_score",
            "institutional_move",
            "bullish_bos",
            "bearish_bos",
        }

        missing = required.difference(
            df.columns
        )

        if missing:

            raise ValueError(
                "Missing required columns: "
                + ", ".join(
                    sorted(missing)
                )
            )

    # ==========================================================
    # Main
    # ==========================================================

    def generate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        self._validate_columns(df)

        # ======================================================
        # Output
        # ======================================================

        df["valid_buy_side_sweep"] = 0

        df["valid_sell_side_sweep"] = 0

        df["sweep_validated"] = 0

        df["sweep_direction"] = "NONE"

        df["sweep_confirmation_score"] = 0.0

        # ======================================================
        # Validate each candle
        # ======================================================

        for i in range(len(df)):

            row = df.iloc[i]

            buy_sweep = (
                row["buy_side_sweep"] == 1
            )

            sell_sweep = (
                row["sell_side_sweep"] == 1
            )

            if not buy_sweep and not sell_sweep:
                continue

            # ==================================================
            # Displacement Confirmation
            # ==================================================

            displacement_valid = True

            if self.require_displacement:

                displacement_valid = (
                    row["is_displacement"] == 1
                    and
                    row["displacement_score"]
                    >= self.min_displacement_score
                )

            # ==================================================
            # BOS Confirmation
            # ==================================================

            bullish_bos = (
                row["bullish_bos"] == 1
            )

            bearish_bos = (
                row["bearish_bos"] == 1
            )

            # ==================================================
            # BUY-SIDE SWEEP
            #
            # Buy-side liquidity above price.
            #
            # A valid raid should preferably produce
            # bearish displacement and bearish BOS.
            # ==================================================

            if buy_sweep:

                bos_valid = True

                if self.require_bos:

                    bos_valid = (
                        bearish_bos
                    )

                direction_valid = (
                    row["institutional_move"]
                    == -1
                )

                if (
                    displacement_valid
                    and
                    bos_valid
                    and
                    direction_valid
                ):

                    df.at[
                        df.index[i],
                        "valid_buy_side_sweep"
                    ] = 1

                    df.at[
                        df.index[i],
                        "sweep_validated"
                    ] = 1

                    df.at[
                        df.index[i],
                        "sweep_direction"
                    ] = "BEARISH"

            # ==================================================
            # SELL-SIDE SWEEP
            #
            # Sell-side liquidity below price.
            #
            # A valid raid should preferably produce
            # bullish displacement and bullish BOS.
            # ==================================================

            if sell_sweep:

                bos_valid = True

                if self.require_bos:

                    bos_valid = (
                        bullish_bos
                    )

                direction_valid = (
                    row["institutional_move"]
                    == 1
                )

                if (
                    displacement_valid
                    and
                    bos_valid
                    and
                    direction_valid
                ):

                    df.at[
                        df.index[i],
                        "valid_sell_side_sweep"
                    ] = 1

                    df.at[
                        df.index[i],
                        "sweep_validated"
                    ] = 1

                    df.at[
                        df.index[i],
                        "sweep_direction"
                    ] = "BULLISH"

            # ==================================================
            # Confirmation Score
            # ==================================================

            score = 0.0

            if displacement_valid:
                score += 50.0

            if buy_sweep or sell_sweep:
                score += 20.0

            if bullish_bos or bearish_bos:
                score += 30.0

            df.at[
                df.index[i],
                "sweep_confirmation_score"
            ] = min(score, 100.0)

        return df


liquidity_sweep_validator = (
    LiquiditySweepValidator()
)