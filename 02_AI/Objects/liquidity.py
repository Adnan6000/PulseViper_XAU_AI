"""
===============================================================================
Module      : liquidity.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Liquidity Object Definition
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Liquidity:

    liquidity_id: int

    liquidity_type: str

    price: float

    touches: int

    first_index: int

    last_index: int

    first_time: object = None

    last_time: object = None

    active: bool = True

    swept: bool = False

    sweep_index: int = -1

    sweep_time: object = None

    score: float = 0.0

    def mark_swept(
        self,
        index: int,
        time=None
    ) -> None:

        self.swept = True

        self.active = False

        self.sweep_index = index

        self.sweep_time = time

    def increase_touch(self) -> None:

        self.touches += 1

    def update_last_touch(
        self,
        index: int,
        time=None
    ) -> None:

        self.last_index = index

        self.last_time = time