"""
===============================================================================
Module      : liquidity_memory.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Runtime Liquidity Memory Manager
===============================================================================
"""

from __future__ import annotations

from typing import Dict
import importlib

types_module = importlib.import_module(
    "02_AI.Common.types"
)

Liquidity = types_module.Liquidity


class LiquidityMemory:

    def __init__(self):

        self.reset()

    # ==========================================================
    # Reset
    # ==========================================================

    def reset(self):

        self.next_id = 1

        self.active: Dict[int, object] = {}

        self.swept: Dict[int, object] = {}

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
    liquidity: object
    ) -> None:

        self.active[
            liquidity.liquidity_id
        ] = liquidity

    # ==========================================================
    # Sweep
    # ==========================================================

    def mark_swept(
        self,
        liquidity_id: int,
        index: int,
        time=None
    ) -> None:

        if liquidity_id not in self.active:
            return

        obj = self.active.pop(liquidity_id)

        obj.mark_swept(
            index=index,
            time=time
        )

        self.swept[
            liquidity_id
        ] = obj

    # ==========================================================
    # Get Active
    # ==========================================================

    def get_active(self):

        return list(
            self.active.values()
        )

    # ==========================================================
    # Get Swept
    # ==========================================================

    def get_swept(self):

        return list(
            self.swept.values()
        )


liquidity_memory = LiquidityMemory()