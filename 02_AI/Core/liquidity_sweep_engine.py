"""
===============================================================================
Module      : liquidity_sweep_engine.py
Project     : PulseViper XAU AI
Version     : 1.2
Author      : Muhammad Adnan
Purpose     : Causal Institutional Liquidity Sweep Detection
===============================================================================

Architecture
------------
LiquidityEngine detects candidate liquidity observations.

LiquiditySweepEngine replays those observations chronologically:

    existing active liquidity
        ↓
    current candle sweep check
        ↓
    swept liquidity removed
        ↓
    current candle new liquidity registered

This guarantees that:

- future liquidity cannot affect past candles
- a level cannot sweep itself on its creation candle
- a swept level is removed from the active pool
- the same price can form a new liquidity pool later
- bullish/bearish canonical sweep aliases are produced

Directional semantics
---------------------
BUY_SIDE liquidity:
    resting liquidity above price.
    Sweep + close back below = bearish raid.

SELL_SIDE liquidity:
    resting liquidity below price.
    Sweep + close back above = bullish raid.
"""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pandas as pd


# =============================================================================
# Shared Types
# =============================================================================

memory_module = importlib.import_module(
    "02_AI.Memory.liquidity_memory"
)

LiquidityMemory = (
    memory_module.LiquidityMemory
)

types_module = importlib.import_module(
    "02_AI.Common.types"
)

Liquidity = (
    types_module.Liquidity
)

enums_module = importlib.import_module(
    "02_AI.Common.enums"
)

LiquidityType = (
    enums_module.LiquidityType
)


class LiquiditySweepEngine:
    """
    Chronological liquidity lifecycle and sweep detector.
    """

    def __init__(
        self,
        sweep_buffer: float = 0.05,
        memory: Any | None = None,
    ) -> None:

        if sweep_buffer < 0.0:
            raise ValueError(
                "sweep_buffer cannot be negative"
            )

        self.sweep_buffer = float(
            sweep_buffer
        )

        self.memory = (
            memory
            if memory is not None
            else LiquidityMemory()
        )

    # =========================================================================
    # Validation
    # =========================================================================

    @staticmethod
    def _validate_columns(
        df: pd.DataFrame,
    ) -> None:

        required = {
            "high",
            "low",
            "close",
            "buy_side_liquidity",
            "sell_side_liquidity",
            "eqh_price",
            "eql_price",
        }

        missing = (
            required
            .difference(
                df.columns
            )
        )

        if missing:

            raise ValueError(
                "Missing required columns: "
                + ", ".join(
                    sorted(missing)
                )
            )

    # =========================================================================
    # Register Liquidity
    # =========================================================================

    def _register_liquidity(
        self,
        liquidity_type: Any,
        price: float,
        index: int,
        timestamp: Any,
    ) -> Any | None:

        if not np.isfinite(
            price
        ):
            return None

        liquidity = Liquidity(
            liquidity_id=(
                self.memory
                .generate_id()
            ),
            liquidity_type=(
                liquidity_type
            ),
            price=float(
                price
            ),
            touches=1,
            first_index=index,
            last_index=index,
            first_time=timestamp,
            last_time=timestamp,
        )

        return self.memory.register(
            liquidity
        )

    # =========================================================================
    # Main
    # =========================================================================

    def generate(
        self,
        data: pd.DataFrame,
        reset_memory: bool = True,
    ) -> pd.DataFrame:

        df = data.copy()

        self._validate_columns(
            df
        )

        # ---------------------------------------------------------------------
        # IMPORTANT
        #
        # LiquidityEngine may already have populated this shared memory using
        # the complete DataFrame.
        #
        # Historical sweep replay must NOT use that future-complete memory.
        # Rebuild the pool candle-by-candle instead.
        # ---------------------------------------------------------------------

        if reset_memory:
            self.memory.reset()

        row_count = len(
            df
        )

        # ---------------------------------------------------------------------
        # Numeric inputs
        # ---------------------------------------------------------------------

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

        buy_liquidity = np.asarray(
            pd.to_numeric(
                df[
                    "buy_side_liquidity"
                ],
                errors="coerce",
            ).fillna(0),
            dtype=np.int8,
        )

        sell_liquidity = np.asarray(
            pd.to_numeric(
                df[
                    "sell_side_liquidity"
                ],
                errors="coerce",
            ).fillna(0),
            dtype=np.int8,
        )

        eqh_price = np.asarray(
            pd.to_numeric(
                df["eqh_price"],
                errors="coerce",
            ),
            dtype=np.float64,
        )

        eql_price = np.asarray(
            pd.to_numeric(
                df["eql_price"],
                errors="coerce",
            ),
            dtype=np.float64,
        )

        # ---------------------------------------------------------------------
        # Outputs
        # ---------------------------------------------------------------------

        buy_side_sweep = np.zeros(
            row_count,
            dtype=np.int8,
        )

        sell_side_sweep = np.zeros(
            row_count,
            dtype=np.int8,
        )

        bullish_sweep = np.zeros(
            row_count,
            dtype=np.int8,
        )

        bearish_sweep = np.zeros(
            row_count,
            dtype=np.int8,
        )

        liquidity_sweep = np.zeros(
            row_count,
            dtype=np.int8,
        )

        liquidity_swept = np.zeros(
            row_count,
            dtype=np.int8,
        )

        sweep_price = np.full(
            row_count,
            np.nan,
            dtype=np.float64,
        )

        sweep_liquidity_id = np.full(
            row_count,
            -1,
            dtype=np.int64,
        )

        causal_liquidity_id = np.full(
            row_count,
            -1,
            dtype=np.int64,
        )

        # =========================================================================
        # Chronological Replay
        # =========================================================================

        for i in range(
            row_count
        ):

            current_high = (
                high[i]
            )

            current_low = (
                low[i]
            )

            current_close = (
                close[i]
            )

            if not (
                np.isfinite(
                    current_high
                )
                and np.isfinite(
                    current_low
                )
                and np.isfinite(
                    current_close
                )
            ):
                continue

            timestamp = (
                df.index[i]
            )

            # =====================================================================
            # STEP 1
            # Check CURRENT candle against liquidity that existed BEFORE it.
            # =====================================================================

            active_liquidity = (
                self.memory
                .get_active()
            )

            for liquidity in (
                active_liquidity
            ):

                if not liquidity.active:
                    continue

                # Defensive causality protection.
                #
                # Because registration happens after the sweep check,
                # this should naturally always be true for active levels.
                if (
                    int(
                        liquidity.first_index
                    )
                    >= i
                ):
                    continue

                price = float(
                    liquidity.price
                )

                liquidity_type = (
                    liquidity
                    .liquidity_type
                )

                # =============================================================
                # BUY-SIDE SWEEP
                # =============================================================

                if (
                    liquidity_type
                    == LiquidityType.BUY_SIDE
                ):

                    swept = (
                        current_high
                        >
                        price
                        + self.sweep_buffer
                        and
                        current_close
                        <
                        price
                    )

                    if not swept:
                        continue

                    buy_side_sweep[i] = 1

                    # Buy-side raid is bearish evidence.
                    bearish_sweep[i] = 1

                    liquidity_sweep[i] = 1
                    liquidity_swept[i] = 1

                    sweep_price[i] = (
                        price
                    )

                    sweep_liquidity_id[i] = int(
                        liquidity
                        .liquidity_id
                    )

                    self.memory.mark_swept(
                        liquidity_id=int(
                            liquidity
                            .liquidity_id
                        ),
                        index=i,
                        time=timestamp,
                    )

                    # Current contract represents one
                    # primary liquidity raid per candle.
                    break

                # =============================================================
                # SELL-SIDE SWEEP
                # =============================================================

                if (
                    liquidity_type
                    == LiquidityType.SELL_SIDE
                ):

                    swept = (
                        current_low
                        <
                        price
                        - self.sweep_buffer
                        and
                        current_close
                        >
                        price
                    )

                    if not swept:
                        continue

                    sell_side_sweep[i] = 1

                    # Sell-side raid is bullish evidence.
                    bullish_sweep[i] = 1

                    liquidity_sweep[i] = 1
                    liquidity_swept[i] = 1

                    sweep_price[i] = (
                        price
                    )

                    sweep_liquidity_id[i] = int(
                        liquidity
                        .liquidity_id
                    )

                    self.memory.mark_swept(
                        liquidity_id=int(
                            liquidity
                            .liquidity_id
                        ),
                        index=i,
                        time=timestamp,
                    )

                    break

            # =====================================================================
            # STEP 2
            # Register liquidity CONFIRMED by the current candle.
            #
            # Registration occurs AFTER sweep detection so a newly created level
            # cannot sweep itself on its own confirmation candle.
            # =====================================================================

            if (
                buy_liquidity[i]
                == 1
            ):

                registered = (
                    self._register_liquidity(
                        liquidity_type=(
                            LiquidityType.BUY_SIDE
                        ),
                        price=(
                            eqh_price[i]
                        ),
                        index=i,
                        timestamp=timestamp,
                    )
                )

                if (
                    registered
                    is not None
                ):

                    causal_liquidity_id[i] = int(
                        registered
                        .liquidity_id
                    )

            if (
                sell_liquidity[i]
                == 1
            ):

                registered = (
                    self._register_liquidity(
                        liquidity_type=(
                            LiquidityType.SELL_SIDE
                        ),
                        price=(
                            eql_price[i]
                        ),
                        index=i,
                        timestamp=timestamp,
                    )
                )

                if (
                    registered
                    is not None
                ):

                    causal_liquidity_id[i] = int(
                        registered
                        .liquidity_id
                    )

        # =========================================================================
        # Assign Outputs
        # =========================================================================

        df["buy_side_sweep"] = (
            buy_side_sweep
        )

        df["sell_side_sweep"] = (
            sell_side_sweep
        )

        df["bullish_sweep"] = (
            bullish_sweep
        )

        df["bearish_sweep"] = (
            bearish_sweep
        )

        df["liquidity_sweep"] = (
            liquidity_sweep
        )

        df["liquidity_swept"] = (
            liquidity_swept
        )

        df["sweep_price"] = (
            sweep_price
        )

        df["sweep_liquidity_id"] = (
            sweep_liquidity_id
        )

        # Keep original LiquidityEngine ID contract untouched
        # and expose the replay ID separately.
        df["causal_liquidity_id"] = (
            causal_liquidity_id
        )

        return df


# =============================================================================
# Global Instance
# =============================================================================

liquidity_sweep_engine = (
    LiquiditySweepEngine()
)