"""
===============================================================================
Module      : liquidity_engine.py
Project     : PulseViper XAU AI
Version     : 2.0
Purpose     : Stateful Institutional Liquidity Detection Engine
===============================================================================
"""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pandas as pd


# ==========================================================
# Shared Objects / Enums
# ==========================================================

types_module = importlib.import_module(
    "02_AI.Common.types"
)

Liquidity = types_module.Liquidity

enums_module = importlib.import_module(
    "02_AI.Common.enums"
)

LiquidityType = enums_module.LiquidityType


# ==========================================================
# Memory
# ==========================================================

memory_module = importlib.import_module(
    "02_AI.Memory.liquidity_memory"
)

LiquidityMemory = memory_module.LiquidityMemory


class LiquidityEngine:

    def __init__(
        self,
        tolerance: float = 0.10,
        lookback: int = 20,
        memory: Any | None = None,
    ) -> None:

        self.tolerance = tolerance
        self.lookback = lookback

        self.memory = (
            memory
            if memory is not None
            else LiquidityMemory(
                price_tolerance=tolerance
            )
        )

    # ==========================================================
    # Reset Runtime State
    # ==========================================================

    def reset(self) -> None:

        self.memory.reset()

    # ==========================================================
    # Detect Equal High
    # ==========================================================

    def _detect_equal_high(
        self,
        df: pd.DataFrame,
        index: int,
    ) -> tuple[bool, float]:

        current_high = float(
            df.iloc[index]["high"]
        )

        history = df.iloc[
            index - self.lookback:index
        ]

        high_match = history[
            (
                history["high"]
                >= current_high - self.tolerance
            )
            &
            (
                history["high"]
                <= current_high + self.tolerance
            )
        ]

        if len(high_match) >= 2:

            return True, current_high

        return False, current_high

    # ==========================================================
    # Detect Equal Low
    # ==========================================================

    def _detect_equal_low(
        self,
        df: pd.DataFrame,
        index: int,
    ) -> tuple[bool, float]:

        current_low = float(
            df.iloc[index]["low"]
        )

        history = df.iloc[
            index - self.lookback:index
        ]

        low_match = history[
            (
                history["low"]
                >= current_low - self.tolerance
            )
            &
            (
                history["low"]
                <= current_low + self.tolerance
            )
        ]

        if len(low_match) >= 2:

            return True, current_low

        return False, current_low

    # ==========================================================
    # Create Liquidity Object
    # ==========================================================

    def _create_liquidity(
        self,
        liquidity_type: Any,
        price: float,
        index: int,
        timestamp: Any = None,
    ) -> Any:

        liquidity = Liquidity(
            liquidity_id=self.memory.generate_id(),
            liquidity_type=liquidity_type,
            price=price,
            touches=1,
            first_index=index,
            last_index=index,
            first_time=timestamp,
            last_time=timestamp,
        )

        return self.memory.register(
            liquidity
        )

    # ==========================================================
    # Main
    # ==========================================================

    def generate(
        self,
        data: pd.DataFrame,
        reset_memory: bool = True,
    ) -> pd.DataFrame:

        if data.empty:
            return data.copy()

        required_columns = {
            "high",
            "low",
            "open",
            "close",
        }

        missing = required_columns.difference(
            data.columns
        )

        if missing:
            raise ValueError(
                "Missing required columns: "
                + ", ".join(sorted(missing))
            )

        if reset_memory:
            self.reset()

        df = data.copy()

        # ======================================================
        # Output Columns
        # ======================================================

        df["equal_high"] = 0
        df["equal_low"] = 0

        df["eqh_price"] = np.nan
        df["eql_price"] = np.nan

        df["buy_side_liquidity"] = 0
        df["sell_side_liquidity"] = 0

        df["liquidity_id"] = -1

        # ======================================================
        # Detection
        # ======================================================

        for i in range(
            self.lookback,
            len(df)
        ):

            timestamp = df.index[i]

            # ==================================================
            # Equal High / Buy-side Liquidity
            # ==================================================

            equal_high, high_price = (
                self._detect_equal_high(
                    df,
                    i,
                )
            )

            if equal_high:

                df.at[
                    timestamp,
                    "equal_high"
                ] = 1

                df.at[
                    timestamp,
                    "eqh_price"
                ] = high_price

                df.at[
                    timestamp,
                    "buy_side_liquidity"
                ] = 1

                liquidity = (
                    self._create_liquidity(
                        liquidity_type=(
                            LiquidityType.BUY_SIDE
                        ),
                        price=high_price,
                        index=i,
                        timestamp=timestamp,
                    )
                )

                df.at[
                    timestamp,
                    "liquidity_id"
                ] = liquidity.liquidity_id

            # ==================================================
            # Equal Low / Sell-side Liquidity
            # ==================================================

            equal_low, low_price = (
                self._detect_equal_low(
                    df,
                    i,
                )
            )

            if equal_low:

                df.at[
                    timestamp,
                    "equal_low"
                ] = 1

                df.at[
                    timestamp,
                    "eql_price"
                ] = low_price

                df.at[
                    timestamp,
                    "sell_side_liquidity"
                ] = 1

                liquidity = (
                    self._create_liquidity(
                        liquidity_type=(
                            LiquidityType.SELL_SIDE
                        ),
                        price=low_price,
                        index=i,
                        timestamp=timestamp,
                    )
                )

                df.at[
                    timestamp,
                    "liquidity_id"
                ] = liquidity.liquidity_id

        return df

    # ==========================================================
    # Runtime State
    # ==========================================================

    def get_active_liquidity(
        self,
    ) -> list[Any]:

        return self.memory.get_active()

    # ==========================================================
    # Swept State
    # ==========================================================

    def get_swept_liquidity(
        self,
    ) -> list[Any]:

        return self.memory.get_swept()


liquidity_engine = LiquidityEngine()