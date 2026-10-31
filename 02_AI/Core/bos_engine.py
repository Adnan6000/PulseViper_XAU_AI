"""
===============================================================================
Module      : bos_engine.py
Project     : PulseViper XAU AI
Version     : 3.0
Author      : Muhammad Adnan
Purpose     : Causal Scalping Break of Structure Engine
===============================================================================

Design
------
Built for the MarketStructure v6 adaptive swing contract.

The engine:

- consumes CONFIRMED swings only
- uses swing_price, not confirmation-candle high/low
- supports MICRO / INTERNAL / MAJOR structure
- detects breaks chronologically
- never breaks a swing before that swing is known
- never emits duplicate BOS for the same swing
- preserves legacy bullish_bos / bearish_bos outputs
- exposes normalized ATR break strength
- labels continuation vs reversal context

Important causality rule
------------------------
At candle i:

    1. test price against structure known BEFORE candle i
    2. emit BOS if a previous level is broken
    3. only then register any new swing confirmed on candle i

Therefore a newly confirmed swing cannot be retrospectively broken
on its own confirmation candle.
"""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pandas as pd


# =============================================================================
# BOS Memory
# =============================================================================

memory_module = importlib.import_module(
    "02_AI.Memory.bos_memory"
)

BOSMemory = (
    memory_module.BOSMemory
)

shared_bos_memory = (
    memory_module.bos_memory
)


class BOSEngine:

    VALID_SCOPES = {
        "MICRO",
        "INTERNAL",
        "MAJOR",
    }

    def __init__(
        self,
        break_buffer_atr: float = 0.05,
        memory: Any | None = None,
    ) -> None:

        if break_buffer_atr < 0.0:

            raise ValueError(
                "break_buffer_atr cannot be negative"
            )

        self.break_buffer_atr = float(
            break_buffer_atr
        )

        self.memory = (
            memory
            if memory is not None
            else BOSMemory()
        )

        self.reset()

    # =========================================================================
    # Reset
    # =========================================================================

    def reset(
        self,
    ) -> None:

        self.memory.reset()

    # =========================================================================
    # Validation
    # =========================================================================

    @staticmethod
    def _validate_input(
        df: pd.DataFrame,
    ) -> None:

        required = {
            "close",
            "atr",
            "swing_id",
            "swing_type",
            "swing_price",
        }

        missing = (
            required
            - set(
                df.columns
            )
        )

        if missing:

            raise ValueError(
                "Missing required BOS columns: "
                + ", ".join(
                    sorted(
                        missing
                    )
                )
            )

    # =========================================================================
    # BOS Context
    # =========================================================================

    @staticmethod
    def _context(
        direction: str,
        structure_bias: str,
    ) -> str:

        if direction == "BULLISH":

            if structure_bias == "BULLISH":
                return "CONTINUATION"

            if structure_bias == "BEARISH":
                return "REVERSAL"

        elif direction == "BEARISH":

            if structure_bias == "BEARISH":
                return "CONTINUATION"

            if structure_bias == "BULLISH":
                return "REVERSAL"

        return "UNCLASSIFIED"

    # =========================================================================
    # Main
    # =========================================================================

    def generate(
        self,
        data: pd.DataFrame,
        reset_memory: bool = True,
    ) -> pd.DataFrame:

        df = data.copy()

        self._validate_input(
            df
        )

        if reset_memory:
            self.reset()

        row_count = len(
            df
        )

        # ---------------------------------------------------------------------
        # Inputs
        # ---------------------------------------------------------------------

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

        swing_id = np.asarray(
            pd.to_numeric(
                df["swing_id"],
                errors="coerce",
            ).fillna(0),
            dtype=np.int64,
        )

        swing_type = np.asarray(
            df["swing_type"],
            dtype=object,
        )

        swing_price = np.asarray(
            pd.to_numeric(
                df["swing_price"],
                errors="coerce",
            ),
            dtype=np.float64,
        )

        # ---------------------------------------------------------------------
        # Swing scale
        # ---------------------------------------------------------------------

        if "swing_scale" in df.columns:

            swing_scale = np.asarray(
                df["swing_scale"],
                dtype=object,
            )

        else:

            # Backward-compatible fallback.
            swing_scale = np.full(
                row_count,
                "MICRO",
                dtype=object,
            )

            if (
                "major_high" in df.columns
                and
                "major_low" in df.columns
            ):

                major = (
                    np.asarray(
                        df["major_high"],
                        dtype=np.int8,
                    )
                    |
                    np.asarray(
                        df["major_low"],
                        dtype=np.int8,
                    )
                )

                swing_scale[
                    major == 1
                ] = "MAJOR"

        # ---------------------------------------------------------------------
        # Confirmation index
        # ---------------------------------------------------------------------

        if (
            "swing_confirmation_index"
            in df.columns
        ):

            confirmation_index = np.asarray(
                pd.to_numeric(
                    df[
                        "swing_confirmation_index"
                    ],
                    errors="coerce",
                ).fillna(-1),
                dtype=np.int64,
            )

        else:

            confirmation_index = np.arange(
                row_count,
                dtype=np.int64,
            )

        # ---------------------------------------------------------------------
        # Structure bias
        # ---------------------------------------------------------------------

        if (
            "structure_bias"
            in df.columns
        ):

            structure_bias = np.asarray(
                df["structure_bias"],
                dtype=object,
            )

        else:

            structure_bias = np.full(
                row_count,
                "NEUTRAL",
                dtype=object,
            )

        # ---------------------------------------------------------------------
        # Time
        # ---------------------------------------------------------------------

        if "time" in df.columns:

            time_values = np.asarray(
                df["time"],
                dtype=object,
            )

        else:

            time_values = np.asarray(
                df.index,
                dtype=object,
            )

        # =========================================================================
        # Legacy Outputs
        # =========================================================================

        bos_id = np.zeros(
            row_count,
            dtype=np.int64,
        )

        bullish_bos = np.zeros(
            row_count,
            dtype=np.int8,
        )

        bearish_bos = np.zeros(
            row_count,
            dtype=np.int8,
        )

        bos_direction = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        bos_price = np.zeros(
            row_count,
            dtype=np.float64,
        )

        bos_strength = np.zeros(
            row_count,
            dtype=np.float64,
        )

        bos_active = np.zeros(
            row_count,
            dtype=np.int8,
        )

        bos_confirmed = np.zeros(
            row_count,
            dtype=np.int8,
        )

        bos_invalidated = np.zeros(
            row_count,
            dtype=np.int8,
        )

        broken_swing_id = np.zeros(
            row_count,
            dtype=np.int64,
        )

        break_index = np.full(
            row_count,
            -1,
            dtype=np.int64,
        )

        break_time = np.full(
            row_count,
            None,
            dtype=object,
        )

        break_distance = np.zeros(
            row_count,
            dtype=np.float64,
        )

        # =========================================================================
        # New Scalping BOS Outputs
        # =========================================================================

        bos_scope = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        bos_context = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        micro_bos = np.zeros(
            row_count,
            dtype=np.int8,
        )

        internal_bos = np.zeros(
            row_count,
            dtype=np.int8,
        )

        major_bos = np.zeros(
            row_count,
            dtype=np.int8,
        )

        bos_strength_atr = np.zeros(
            row_count,
            dtype=np.float64,
        )

        break_distance_atr = np.zeros(
            row_count,
            dtype=np.float64,
        )

        broken_swing_scale = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        broken_swing_confirmation_index = np.full(
            row_count,
            -1,
            dtype=np.int64,
        )

        # =========================================================================
        # Last confirmed structure known to the engine
        # =========================================================================

        last_high: dict[str, Any] | None = None
        last_low: dict[str, Any] | None = None

        # =========================================================================
        # Chronological Replay
        # =========================================================================

        for i in range(
            row_count
        ):

            current_close = (
                close[i]
            )

            current_atr = (
                atr[i]
            )

            valid_price = (
                np.isfinite(
                    current_close
                )
                and
                np.isfinite(
                    current_atr
                )
                and
                current_atr > 0.0
            )

            # =====================================================================
            # STEP 1:
            # Break only structure that existed BEFORE this candle.
            # =====================================================================

            candidates: list[
                dict[str, Any]
            ] = []

            if valid_price:

                # =============================================================
                # Bullish BOS
                # =============================================================

                if (
                    last_high
                    is not None
                ):

                    reference_id = int(
                        last_high[
                            "swing_id"
                        ]
                    )

                    reference_price = float(
                        last_high[
                            "price"
                        ]
                    )

                    already_broken = (
                        self.memory
                        .high_already_broken(
                            reference_id
                        )
                    )

                    if not already_broken:

                        distance = (
                            current_close
                            - reference_price
                        )

                        minimum_break = (
                            self.break_buffer_atr
                            * current_atr
                        )

                        if (
                            distance
                            > minimum_break
                        ):

                            candidates.append(
                                {
                                    "direction": (
                                        "BULLISH"
                                    ),
                                    "distance": (
                                        distance
                                    ),
                                    "distance_atr": (
                                        distance
                                        / current_atr
                                    ),
                                    "reference": (
                                        last_high
                                    ),
                                }
                            )

                # =============================================================
                # Bearish BOS
                # =============================================================

                if (
                    last_low
                    is not None
                ):

                    reference_id = int(
                        last_low[
                            "swing_id"
                        ]
                    )

                    reference_price = float(
                        last_low[
                            "price"
                        ]
                    )

                    already_broken = (
                        self.memory
                        .low_already_broken(
                            reference_id
                        )
                    )

                    if not already_broken:

                        distance = (
                            reference_price
                            - current_close
                        )

                        minimum_break = (
                            self.break_buffer_atr
                            * current_atr
                        )

                        if (
                            distance
                            > minimum_break
                        ):

                            candidates.append(
                                {
                                    "direction": (
                                        "BEARISH"
                                    ),
                                    "distance": (
                                        distance
                                    ),
                                    "distance_atr": (
                                        distance
                                        / current_atr
                                    ),
                                    "reference": (
                                        last_low
                                    ),
                                }
                            )

            # -----------------------------------------------------------------
            # Normally only one side can break.
            #
            # Defensive handling:
            # if malformed structure makes both possible,
            # keep the stronger normalized break.
            # -----------------------------------------------------------------

            if candidates:

                event = max(
                    candidates,
                    key=lambda item: (
                        item[
                            "distance_atr"
                        ]
                    ),
                )

                direction = (
                    event[
                        "direction"
                    ]
                )

                reference = (
                    event[
                        "reference"
                    ]
                )

                reference_id = int(
                    reference[
                        "swing_id"
                    ]
                )

                reference_price = float(
                    reference[
                        "price"
                    ]
                )

                scope = str(
                    reference[
                        "scale"
                    ]
                ).upper()

                if (
                    scope
                    not in self.VALID_SCOPES
                ):
                    scope = "MICRO"

                event_id = (
                    self.memory
                    .generate_id()
                )

                bos_id[i] = (
                    event_id
                )

                bos_direction[i] = (
                    direction
                )

                bos_price[i] = (
                    reference_price
                )

                raw_distance = float(
                    event[
                        "distance"
                    ]
                )

                normalized_distance = float(
                    event[
                        "distance_atr"
                    ]
                )

                # Legacy bos_strength remains raw price distance.
                bos_strength[i] = (
                    raw_distance
                )

                bos_strength_atr[i] = (
                    normalized_distance
                )

                bos_active[i] = 1
                bos_confirmed[i] = 1

                broken_swing_id[i] = (
                    reference_id
                )

                broken_swing_scale[i] = (
                    scope
                )

                broken_swing_confirmation_index[i] = int(
                    reference[
                        "confirmation_index"
                    ]
                )

                break_index[i] = i

                break_time[i] = (
                    time_values[i]
                )

                break_distance[i] = (
                    raw_distance
                )

                break_distance_atr[i] = (
                    normalized_distance
                )

                bos_scope[i] = (
                    scope
                )

                bias = str(
                    structure_bias[i]
                ).upper()

                bos_context[i] = (
                    self._context(
                        direction=(
                            direction
                        ),
                        structure_bias=(
                            bias
                        ),
                    )
                )

                # =============================================================
                # Direction
                # =============================================================

                if (
                    direction
                    == "BULLISH"
                ):

                    bullish_bos[i] = 1

                    self.memory.register_high_break(
                        reference_id
                    )

                else:

                    bearish_bos[i] = 1

                    self.memory.register_low_break(
                        reference_id
                    )

                # =============================================================
                # Scope
                # =============================================================

                if scope == "MICRO":

                    micro_bos[i] = 1

                elif (
                    scope
                    == "INTERNAL"
                ):

                    internal_bos[i] = 1

                elif (
                    scope
                    == "MAJOR"
                ):

                    major_bos[i] = 1

                # =============================================================
                # Runtime Memory
                # =============================================================

                self.memory.activate(
                    {
                        "bos_id": (
                            event_id
                        ),
                        "direction": (
                            direction
                        ),
                        "scope": (
                            scope
                        ),
                        "context": (
                            bos_context[i]
                        ),
                        "bos_price": (
                            reference_price
                        ),
                        "broken_swing_id": (
                            reference_id
                        ),
                        "break_index": (
                            i
                        ),
                        "break_time": (
                            time_values[i]
                        ),
                        "break_distance": (
                            raw_distance
                        ),
                        "break_distance_atr": (
                            normalized_distance
                        ),
                    }
                )

            # =====================================================================
            # STEP 2:
            # Register swing confirmed ON this candle.
            #
            # This is deliberately after break detection.
            # =====================================================================

            current_swing_id = int(
                swing_id[i]
            )

            if (
                current_swing_id
                <= 0
            ):
                continue

            current_swing_price = (
                swing_price[i]
            )

            if not np.isfinite(
                current_swing_price
            ):
                continue

            current_confirmation_index = int(
                confirmation_index[i]
            )

            # A future-confirmed swing must never leak backward.
            if (
                current_confirmation_index
                > i
            ):
                continue

            current_type = str(
                swing_type[i]
            ).upper()

            current_scale = str(
                swing_scale[i]
            ).upper()

            if (
                current_scale
                not in self.VALID_SCOPES
            ):
                current_scale = "MICRO"

            reference = {
                "swing_id": (
                    current_swing_id
                ),
                "price": float(
                    current_swing_price
                ),
                "scale": (
                    current_scale
                ),
                "confirmation_index": (
                    current_confirmation_index
                ),
            }

            if (
                current_type
                == "HIGH"
            ):

                last_high = (
                    reference
                )

            elif (
                current_type
                == "LOW"
            ):

                last_low = (
                    reference
                )

        # =========================================================================
        # Assign
        # =========================================================================

        df["bos_id"] = bos_id

        df["bullish_bos"] = (
            bullish_bos
        )

        df["bearish_bos"] = (
            bearish_bos
        )

        df["bos_direction"] = (
            bos_direction
        )

        df["bos_price"] = (
            bos_price
        )

        df["bos_strength"] = (
            bos_strength
        )

        df["bos_strength_atr"] = (
            bos_strength_atr
        )

        df["bos_active"] = (
            bos_active
        )

        df["bos_confirmed"] = (
            bos_confirmed
        )

        df["bos_invalidated"] = (
            bos_invalidated
        )

        df["broken_swing_id"] = (
            broken_swing_id
        )

        df["broken_swing_scale"] = (
            broken_swing_scale
        )

        df[
            "broken_swing_confirmation_index"
        ] = (
            broken_swing_confirmation_index
        )

        df["break_index"] = (
            break_index
        )

        df["break_time"] = (
            break_time
        )

        df["break_distance"] = (
            break_distance
        )

        df["break_distance_atr"] = (
            break_distance_atr
        )

        df["bos_scope"] = (
            bos_scope
        )

        df["bos_context"] = (
            bos_context
        )

        df["micro_bos"] = (
            micro_bos
        )

        df["internal_bos"] = (
            internal_bos
        )

        df["major_bos"] = (
            major_bos
        )

        return df


# =============================================================================
# Global Engine
# =============================================================================

bos_engine = BOSEngine(
    memory=shared_bos_memory
)