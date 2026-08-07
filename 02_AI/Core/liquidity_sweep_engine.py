"""
===============================================================================
Module      : liquidity_sweep_engine.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Institutional Liquidity Sweep Detection
===============================================================================
"""

from __future__ import annotations

import importlib
from typing import Any

import pandas as pd


memory_module = importlib.import_module(
    "02_AI.Memory.liquidity_memory"
)

LiquidityMemory = memory_module.LiquidityMemory


class LiquiditySweepEngine:

    def __init__(
        self,
        sweep_buffer: float = 0.05,
        memory: Any | None = None,
    ) -> None:

        self.sweep_buffer = sweep_buffer

        self.memory = memory

    # ==========================================================
    # Main
    # ==========================================================

    def generate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        required = {
            "high",
            "low",
            "close",
        }

        missing = required.difference(
            df.columns
        )

        if missing:
            raise ValueError(
                "Missing required columns: "
                + ", ".join(sorted(missing))
            )

        df["buy_side_sweep"] = 0
        df["sell_side_sweep"] = 0

        df["sweep_price"] = pd.NA

        df["sweep_liquidity_id"] = -1

        # ======================================================
        # No Memory = Nothing to Sweep
        # ======================================================

        if self.memory is None:

            return df

        # ======================================================
        # Scan Active Liquidity
        # ======================================================

        for i in range(len(df)):

            high = float(
                df.iloc[i]["high"]
            )

            low = float(
                df.iloc[i]["low"]
            )

            timestamp = df.index[i]

            active_liquidity = (
                self.memory.get_active()
            )

            for liquidity in active_liquidity:

                if not liquidity.active:
                    continue

                price = float(
                    liquidity.price
                )

                # ==================================================
                # BUY-SIDE LIQUIDITY
                #
                # Price trades ABOVE liquidity
                # but closes back BELOW it.
                # ==================================================

                if (
                    liquidity.liquidity_type.value
                    == "BUY_SIDE"
                ):

                    swept = (
                        high
                        >
                        price + self.sweep_buffer
                        and
                        float(
                            df.iloc[i]["close"]
                        )
                        <
                        price
                    )

                    if swept:

                        df.at[
                            timestamp,
                            "buy_side_sweep"
                        ] = 1

                        df.at[
                            timestamp,
                            "sweep_price"
                        ] = price

                        df.at[
                            timestamp,
                            "sweep_liquidity_id"
                        ] = (
                            liquidity.liquidity_id
                        )

                        self.memory.mark_swept(
                            liquidity_id=(
                                liquidity.liquidity_id
                            ),
                            index=i,
                            time=timestamp,
                        )

                        break

                # ==================================================
                # SELL-SIDE LIQUIDITY
                #
                # Price trades BELOW liquidity
                # but closes back ABOVE it.
                # ==================================================

                elif (
                    liquidity.liquidity_type.value
                    == "SELL_SIDE"
                ):

                    swept = (
                        low
                        <
                        price - self.sweep_buffer
                        and
                        float(
                            df.iloc[i]["close"]
                        )
                        >
                        price
                    )

                    if swept:

                        df.at[
                            timestamp,
                            "sell_side_sweep"
                        ] = 1

                        df.at[
                            timestamp,
                            "sweep_price"
                        ] = price

                        df.at[
                            timestamp,
                            "sweep_liquidity_id"
                        ] = (
                            liquidity.liquidity_id
                        )

                        self.memory.mark_swept(
                            liquidity_id=(
                                liquidity.liquidity_id
                            ),
                            index=i,
                            time=timestamp,
                        )

                        break

        return df


liquidity_sweep_engine = LiquiditySweepEngine()