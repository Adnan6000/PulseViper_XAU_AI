"""
===============================================================================
Module      : bos_memory.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Runtime BOS Memory Manager
===============================================================================
"""

from __future__ import annotations


class BOSMemory:

    def __init__(self):

        self.reset()

    # ==========================================================
    # Reset
    # ==========================================================

    def reset(self):

        self.next_bos_id = 1

        self.broken_high_swings = set()
        self.broken_low_swings = set()

        self.active_bos = {}

        self.completed_bos = {}

        self.invalidated_bos = {}

    # ==========================================================
    # ID Generator
    # ==========================================================

    def generate_id(self):

        bos_id = self.next_bos_id

        self.next_bos_id += 1

        return bos_id

    # ==========================================================
    # Duplicate Check
    # ==========================================================

    def high_already_broken(
        self,
        swing_id: int
    ) -> bool:

        return swing_id in self.broken_high_swings

    def low_already_broken(
        self,
        swing_id: int
    ) -> bool:

        return swing_id in self.broken_low_swings

    # ==========================================================
    # Register
    # ==========================================================

    def register_high_break(
        self,
        swing_id: int
    ):

        self.broken_high_swings.add(swing_id)

    def register_low_break(
        self,
        swing_id: int
    ):

        self.broken_low_swings.add(swing_id)

    # ==========================================================
    # Active BOS
    # ==========================================================

    def activate(
        self,
        bos: dict
    ):

        self.active_bos[
            bos["bos_id"]
        ] = bos

    # ==========================================================
    # Complete
    # ==========================================================

    def complete(
        self,
        bos_id: int
    ):

        if bos_id in self.active_bos:

            self.completed_bos[
                bos_id
            ] = self.active_bos.pop(
                bos_id
            )

    # ==========================================================
    # Invalidate
    # ==========================================================

    def invalidate(
        self,
        bos_id: int
    ):

        if bos_id in self.active_bos:

            self.invalidated_bos[
                bos_id
            ] = self.active_bos.pop(
                bos_id
            )


bos_memory = BOSMemory()