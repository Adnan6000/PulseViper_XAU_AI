"""
===============================================================================
Module      : liquidity.py
Project     : PulseViper XAU AI
Version     : 2.0
Purpose     : Institutional Liquidity Object
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Liquidity:

    liquidity_id: int

    liquidity_type: Any

    price: float

    touches: int

    first_index: int

    last_index: int

    first_time: Any = None

    last_time: Any = None

    active: bool = True

    swept: bool = False

    sweep_index: int = -1

    sweep_time: Any = None

    score: float = 0.0

    # Complete touch history.
    # Each entry can later contain:
    # index, time, price, type, session, etc.
    touch_history: list[dict[str, Any]] = field(
        default_factory=list
    )

    # ==========================================================
    # Touch Management
    # ==========================================================

    def increase_touch(
        self,
        index: int | None = None,
        time: Any = None,
        price: float | None = None,
        touch_type: str = "RETEST",
    ) -> None:

        self.touches += 1

        if index is not None:
            self.last_index = index

        if time is not None:
            self.last_time = time

        self.touch_history.append(
            {
                "index": index,
                "time": time,
                "price": price,
                "type": touch_type,
            }
        )

    # ==========================================================
    # Last Touch
    # ==========================================================

    def update_last_touch(
        self,
        index: int,
        time: Any = None,
        price: float | None = None,
        touch_type: str = "RETEST",
    ) -> None:

        self.last_index = index

        if time is not None:
            self.last_time = time

        self.touch_history.append(
            {
                "index": index,
                "time": time,
                "price": price,
                "type": touch_type,
            }
        )

    # ==========================================================
    # Sweep
    # ==========================================================

    def mark_swept(
        self,
        index: int,
        time: Any = None,
    ) -> None:

        self.swept = True

        self.active = False

        self.sweep_index = index

        self.sweep_time = time

    # ==========================================================
    # Reactivate
    # ==========================================================

    def reactivate(self) -> None:

        if not self.swept:
            self.active = True

    # ==========================================================
    # Metadata
    # ==========================================================

    def to_dict(self) -> dict[str, Any]:

        return {
            "liquidity_id": self.liquidity_id,
            "liquidity_type": (
                self.liquidity_type.value
                if hasattr(self.liquidity_type, "value")
                else self.liquidity_type
            ),
            "price": self.price,
            "touches": self.touches,
            "first_index": self.first_index,
            "last_index": self.last_index,
            "first_time": self.first_time,
            "last_time": self.last_time,
            "active": self.active,
            "swept": self.swept,
            "sweep_index": self.sweep_index,
            "sweep_time": self.sweep_time,
            "score": self.score,
            "touch_history": self.touch_history,
        }