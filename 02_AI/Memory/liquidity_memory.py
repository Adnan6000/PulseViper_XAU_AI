"""
===============================================================================
Module      : liquidity_memory.py
Project     : PulseViper XAU AI
Version     : 2.0
Purpose     : Stateful Liquidity Memory Manager
===============================================================================
"""

from __future__ import annotations

from typing import Any

import importlib

types_module = importlib.import_module(
    "02_AI.Common.types"
)

Liquidity = types_module.Liquidity


class LiquidityMemory:

    def __init__(
        self,
        price_tolerance: float = 0.20,
    ) -> None:

        self.price_tolerance = price_tolerance

        self.reset()

    # ==========================================================
    # Reset
    # ==========================================================

    def reset(self) -> None:

        self.next_id = 1

        self.active: dict[int, Any] = {}

        self.swept: dict[int, Any] = {}

    # ==========================================================
    # Generate ID
    # ==========================================================

    def generate_id(self) -> int:

        liquidity_id = self.next_id

        self.next_id += 1

        return liquidity_id

    # ==========================================================
    # Register
    # ==========================================================

    def register(
        self,
        liquidity: Any,
    ) -> Any:

        existing = self.find_matching(
            liquidity.liquidity_type,
            liquidity.price,
        )

        if existing is not None:

            existing.increase_touch(
                index=liquidity.last_index,
                time=liquidity.last_time,
                price=liquidity.price,
                touch_type="RETEST",
            )

            return existing

        self.active[
            liquidity.liquidity_id
        ] = liquidity

        return liquidity

    # ==========================================================
    # Find Matching Liquidity
    # ==========================================================

    def find_matching(
        self,
        liquidity_type: Any,
        price: float,
    ) -> Any | None:

        for liquidity in self.active.values():

            if liquidity.liquidity_type != liquidity_type:
                continue

            if abs(
                liquidity.price - price
            ) <= self.price_tolerance:

                return liquidity

        return None

    # ==========================================================
    # Sweep
    # ==========================================================

    def mark_swept(
        self,
        liquidity_id: int,
        index: int,
        time: Any = None,
    ) -> None:

        if liquidity_id not in self.active:
            return

        liquidity = self.active.pop(
            liquidity_id
        )

        liquidity.mark_swept(
            index=index,
            time=time,
        )

        self.swept[
            liquidity_id
        ] = liquidity

    # ==========================================================
    # Active Liquidity
    # ==========================================================

    def get_active(self) -> list[Any]:

        return list(
            self.active.values()
        )

    # ==========================================================
    # Swept Liquidity
    # ==========================================================

    def get_swept(self) -> list[Any]:

        return list(
            self.swept.values()
        )

    # ==========================================================
    # Active Count
    # ==========================================================

    def active_count(self) -> int:

        return len(self.active)

    # ==========================================================
    # Swept Count
    # ==========================================================

    def swept_count(self) -> int:

        return len(self.swept)


liquidity_memory = LiquidityMemory()