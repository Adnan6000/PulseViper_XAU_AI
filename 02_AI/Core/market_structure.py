"""
===============================================================================
Module      : market_structure.py
Project     : PulseViper XAU AI
Version     : 6.1
Author      : Muhammad Adnan
Purpose     : Causal Adaptive XAUUSD Scalping Swing Engine
===============================================================================

Core design
-----------
- No fixed candle window.
- No centered/look-ahead pivots.
- Swing duration is market-driven.
- Candidate extreme keeps extending until an ATR reversal confirms it.
- Confirmed swing events are written on confirmation rows.
- Actual turning-point price/index/time are preserved separately.
- Confirmed swing types strictly alternate HIGH / LOW.
- MICRO / INTERNAL / MAJOR describe importance, not candle count.

v6.1 correction
---------------
v6.0 could freeze after a shallow but valid reversal because:

    reversal_atr < min_swing_atr

A swing could be confirmed with one threshold while the opposite swing
required a larger excursion threshold.

v6.1 uses ONE causal reversal threshold for swing confirmation.

Leg excursion remains useful for:
- MICRO / INTERNAL / MAJOR classification
- swing scoring
- diagnostics

but it does NOT block the state machine.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class MarketStructure:

    def __init__(
        self,
        atr_period: int = 14,
        reversal_atr: float = 0.55,
        min_swing_atr: float = 0.80,
        internal_swing_atr: float = 1.50,
        major_swing_atr: float = 2.50,
        equality_atr: float = 0.05,

        # Legacy compatibility.
        pivot_window: int | None = None,
        min_strength: float | None = None,
        major_strength: float | None = None,
    ) -> None:

        if atr_period <= 0:
            raise ValueError(
                "atr_period must be greater than zero"
            )

        if min_strength is not None:
            reversal_atr = float(
                min_strength
            )

        if major_strength is not None:
            major_swing_atr = float(
                major_strength
            )

        if reversal_atr <= 0.0:
            raise ValueError(
                "reversal_atr must be greater than zero"
            )

        if min_swing_atr <= 0.0:
            raise ValueError(
                "min_swing_atr must be greater than zero"
            )

        if internal_swing_atr <= 0.0:
            raise ValueError(
                "internal_swing_atr must be greater than zero"
            )

        if major_swing_atr <= internal_swing_atr:
            raise ValueError(
                "major_swing_atr must be greater "
                "than internal_swing_atr"
            )

        if equality_atr < 0.0:
            raise ValueError(
                "equality_atr cannot be negative"
            )

        self.atr_period = int(
            atr_period
        )

        self.reversal_atr = float(
            reversal_atr
        )

        # Preserved for compatibility / diagnostics.
        # It is NOT a confirmation gate in v6.1.
        self.min_swing_atr = float(
            min_swing_atr
        )

        self.internal_swing_atr = float(
            internal_swing_atr
        )

        self.major_swing_atr = float(
            major_swing_atr
        )

        self.equality_atr = float(
            equality_atr
        )

        self.pivot_window = (
            pivot_window
        )

        self.min_strength = (
            self.reversal_atr
        )

        self.major_strength = (
            self.major_swing_atr
        )

    # =========================================================================
    # Validation
    # =========================================================================

    @staticmethod
    def _validate_input(
        df: pd.DataFrame,
    ) -> None:

        required = {
            "open",
            "high",
            "low",
            "close",
        }

        missing = (
            required
            - set(
                df.columns
            )
        )

        if missing:

            raise ValueError(
                "Missing required columns: "
                + ", ".join(
                    sorted(
                        missing
                    )
                )
            )

    # =========================================================================
    # ATR
    # =========================================================================

    def calculate_atr(
        self,
        df: pd.DataFrame,
    ) -> pd.Series:

        high = pd.to_numeric(
            df["high"],
            errors="coerce",
        )

        low = pd.to_numeric(
            df["low"],
            errors="coerce",
        )

        close = pd.to_numeric(
            df["close"],
            errors="coerce",
        )

        previous_close = (
            close.shift(1)
        )

        true_range = pd.concat(
            [
                high - low,

                (
                    high
                    - previous_close
                ).abs(),

                (
                    low
                    - previous_close
                ).abs(),
            ],
            axis=1,
        ).max(
            axis=1
        )

        return (
            true_range
            .rolling(
                window=self.atr_period,
                min_periods=1,
            )
            .mean()
            .astype(
                "float64"
            )
        )

    # =========================================================================
    # ATR reference
    # =========================================================================

    @staticmethod
    def _atr_reference(
        candidate_atr: float,
        current_atr: float,
    ) -> float:

        values = [
            value
            for value in (
                candidate_atr,
                current_atr,
            )
            if (
                np.isfinite(
                    value
                )
                and value > 0.0
            )
        ]

        if not values:
            return float(
                "nan"
            )

        # Do not allow an ATR collapse on the confirmation candle
        # to make reversal artificially easy.
        return float(
            max(
                values
            )
        )

    # =========================================================================
    # Swing hierarchy
    # =========================================================================

    def _swing_scale(
        self,
        excursion_atr: float,
    ) -> str:

        if (
            excursion_atr
            >= self.major_swing_atr
        ):
            return "MAJOR"

        if (
            excursion_atr
            >= self.internal_swing_atr
        ):
            return "INTERNAL"

        return "MICRO"

    # =========================================================================
    # Output allocator
    # =========================================================================

    @staticmethod
    def _empty_outputs(
        row_count: int,
    ) -> dict[str, Any]:

        return {
            "pivot_high": np.zeros(
                row_count,
                dtype=np.int8,
            ),

            "pivot_low": np.zeros(
                row_count,
                dtype=np.int8,
            ),

            "pivot_strength": np.zeros(
                row_count,
                dtype=np.float64,
            ),

            "major_high": np.zeros(
                row_count,
                dtype=np.int8,
            ),

            "major_low": np.zeros(
                row_count,
                dtype=np.int8,
            ),

            "minor_high": np.zeros(
                row_count,
                dtype=np.int8,
            ),

            "minor_low": np.zeros(
                row_count,
                dtype=np.int8,
            ),

            "micro_high": np.zeros(
                row_count,
                dtype=np.int8,
            ),

            "micro_low": np.zeros(
                row_count,
                dtype=np.int8,
            ),

            "internal_high": np.zeros(
                row_count,
                dtype=np.int8,
            ),

            "internal_low": np.zeros(
                row_count,
                dtype=np.int8,
            ),

            "major_swing": np.zeros(
                row_count,
                dtype=np.int8,
            ),

            "swing_score": np.zeros(
                row_count,
                dtype=np.float64,
            ),

            "swing_id": np.zeros(
                row_count,
                dtype=np.int64,
            ),

            "swing_type": np.full(
                row_count,
                "NONE",
                dtype=object,
            ),

            "swing_price": np.full(
                row_count,
                np.nan,
                dtype=np.float64,
            ),

            "swing_scale": np.full(
                row_count,
                "NONE",
                dtype=object,
            ),

            "swing_origin_index": np.full(
                row_count,
                -1,
                dtype=np.int64,
            ),

            "swing_confirmation_index": np.full(
                row_count,
                -1,
                dtype=np.int64,
            ),

            "swing_origin_time": np.full(
                row_count,
                None,
                dtype=object,
            ),

            "swing_confirmation_time": np.full(
                row_count,
                None,
                dtype=object,
            ),

            "swing_leg_bars": np.zeros(
                row_count,
                dtype=np.int64,
            ),

            "swing_confirmation_bars": np.zeros(
                row_count,
                dtype=np.int64,
            ),

            "swing_excursion": np.zeros(
                row_count,
                dtype=np.float64,
            ),

            "swing_excursion_atr": np.zeros(
                row_count,
                dtype=np.float64,
            ),

            "swing_reversal": np.zeros(
                row_count,
                dtype=np.float64,
            ),

            "swing_reversal_atr": np.zeros(
                row_count,
                dtype=np.float64,
            ),
        }

    # =========================================================================
    # Assign swing outputs
    # =========================================================================

    @staticmethod
    def _assign_swing_outputs(
        df: pd.DataFrame,
        outputs: dict[
            str,
            Any,
        ],
    ) -> pd.DataFrame:

        result = df.copy()

        for (
            column,
            values,
        ) in outputs.items():

            result[
                column
            ] = values

        return result

    # =========================================================================
    # Adaptive causal swings
    # =========================================================================

    def detect_swings(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        required = {
            "high",
            "low",
            "close",
            "atr",
        }

        missing = (
            required
            - set(
                df.columns
            )
        )

        if missing:

            raise ValueError(
                "Missing required swing columns: "
                + ", ".join(
                    sorted(
                        missing
                    )
                )
            )

        row_count = len(
            df
        )

        outputs = (
            self._empty_outputs(
                row_count
            )
        )

        if row_count == 0:

            return (
                self._assign_swing_outputs(
                    df,
                    outputs,
                )
            )

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

        atr = np.asarray(
            pd.to_numeric(
                df["atr"],
                errors="coerce",
            ),
            dtype=np.float64,
        )

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

        valid = (
            np.isfinite(
                high
            )
            &
            np.isfinite(
                low
            )
            &
            np.isfinite(
                close
            )
            &
            np.isfinite(
                atr
            )
            &
            (atr > 0.0)
        )

        valid_indices = np.flatnonzero(
            valid
        )

        if len(
            valid_indices
        ) == 0:

            return (
                self._assign_swing_outputs(
                    df,
                    outputs,
                )
            )

        next_swing_id = 1

        last_swing_price: (
            float | None
        ) = None

        last_swing_origin: (
            int | None
        ) = None

        # =====================================================================
        # Event writer
        # =====================================================================

        def confirm_swing(
            kind: str,
            origin_index: int,
            confirmation_index: int,
            price: float,
            excursion_value: float,
            excursion_atr_value: float,
            reversal_value: float,
            reversal_atr_value: float,
        ) -> None:

            nonlocal next_swing_id
            nonlocal last_swing_price
            nonlocal last_swing_origin

            event_index = (
                confirmation_index
            )

            safe_excursion_atr = max(
                0.0,
                float(
                    excursion_atr_value
                ),
            )

            safe_reversal_atr = max(
                0.0,
                float(
                    reversal_atr_value
                ),
            )

            scale = (
                self._swing_scale(
                    safe_excursion_atr
                )
            )

            if kind == "HIGH":

                outputs[
                    "pivot_high"
                ][event_index] = 1

                if scale == "MICRO":

                    outputs[
                        "micro_high"
                    ][event_index] = 1

                    outputs[
                        "minor_high"
                    ][event_index] = 1

                elif scale == "INTERNAL":

                    outputs[
                        "internal_high"
                    ][event_index] = 1

                    outputs[
                        "minor_high"
                    ][event_index] = 1

                else:

                    outputs[
                        "major_high"
                    ][event_index] = 1

                    outputs[
                        "major_swing"
                    ][event_index] = 1

            else:

                outputs[
                    "pivot_low"
                ][event_index] = 1

                if scale == "MICRO":

                    outputs[
                        "micro_low"
                    ][event_index] = 1

                    outputs[
                        "minor_low"
                    ][event_index] = 1

                elif scale == "INTERNAL":

                    outputs[
                        "internal_low"
                    ][event_index] = 1

                    outputs[
                        "minor_low"
                    ][event_index] = 1

                else:

                    outputs[
                        "major_low"
                    ][event_index] = 1

                    outputs[
                        "major_swing"
                    ][event_index] = 1

            outputs[
                "pivot_strength"
            ][event_index] = (
                safe_excursion_atr
            )

            outputs[
                "swing_score"
            ][event_index] = round(
                min(
                    100.0,
                    (
                        safe_excursion_atr
                        * 20.0
                    )
                    +
                    (
                        safe_reversal_atr
                        * 20.0
                    ),
                ),
                2,
            )

            outputs[
                "swing_id"
            ][event_index] = (
                next_swing_id
            )

            outputs[
                "swing_type"
            ][event_index] = (
                kind
            )

            outputs[
                "swing_price"
            ][event_index] = (
                price
            )

            outputs[
                "swing_scale"
            ][event_index] = (
                scale
            )

            outputs[
                "swing_origin_index"
            ][event_index] = (
                origin_index
            )

            outputs[
                "swing_confirmation_index"
            ][event_index] = (
                confirmation_index
            )

            outputs[
                "swing_origin_time"
            ][event_index] = (
                time_values[
                    origin_index
                ]
            )

            outputs[
                "swing_confirmation_time"
            ][event_index] = (
                time_values[
                    confirmation_index
                ]
            )

            outputs[
                "swing_confirmation_bars"
            ][event_index] = max(
                0,
                (
                    confirmation_index
                    - origin_index
                ),
            )

            if (
                last_swing_origin
                is not None
            ):

                outputs[
                    "swing_leg_bars"
                ][event_index] = abs(
                    origin_index
                    - last_swing_origin
                )

            outputs[
                "swing_excursion"
            ][event_index] = max(
                0.0,
                excursion_value,
            )

            outputs[
                "swing_excursion_atr"
            ][event_index] = (
                safe_excursion_atr
            )

            outputs[
                "swing_reversal"
            ][event_index] = max(
                0.0,
                reversal_value,
            )

            outputs[
                "swing_reversal_atr"
            ][event_index] = (
                safe_reversal_atr
            )

            next_swing_id += 1

            last_swing_price = (
                price
            )

            last_swing_origin = (
                origin_index
            )

        # =====================================================================
        # Bootstrap
        # =====================================================================

        first = int(
            valid_indices[0]
        )

        running_high = float(
            high[first]
        )

        running_high_index = (
            first
        )

        running_high_atr = float(
            atr[first]
        )

        running_low = float(
            low[first]
        )

        running_low_index = (
            first
        )

        running_low_atr = float(
            atr[first]
        )

        mode = "SEEK_INITIAL"

        candidate_high = float(
            "nan"
        )

        candidate_high_index = -1

        candidate_high_atr = float(
            "nan"
        )

        candidate_low = float(
            "nan"
        )

        candidate_low_index = -1

        candidate_low_atr = float(
            "nan"
        )

        # =====================================================================
        # Chronological state machine
        # =====================================================================

        for i in range(
            first + 1,
            row_count,
        ):

            if not valid[i]:
                continue

            current_atr = float(
                atr[i]
            )

            # =================================================================
            # Initial state:
            # determine which terminal extreme gets reversed first.
            # =================================================================

            if mode == "SEEK_INITIAL":

                if (
                    high[i]
                    > running_high
                ):

                    running_high = float(
                        high[i]
                    )

                    running_high_index = (
                        i
                    )

                    running_high_atr = (
                        current_atr
                    )

                if (
                    low[i]
                    < running_low
                ):

                    running_low = float(
                        low[i]
                    )

                    running_low_index = (
                        i
                    )

                    running_low_atr = (
                        current_atr
                    )

                high_atr_ref = (
                    self._atr_reference(
                        running_high_atr,
                        current_atr,
                    )
                )

                low_atr_ref = (
                    self._atr_reference(
                        running_low_atr,
                        current_atr,
                    )
                )

                high_reversal = (
                    running_high
                    - float(
                        low[i]
                    )
                )

                low_reversal = (
                    float(
                        high[i]
                    )
                    - running_low
                )

                high_ready = bool(
                    running_high_index
                    < i
                    and
                    np.isfinite(
                        high_atr_ref
                    )
                    and
                    (
                        high_reversal
                        / high_atr_ref
                    )
                    >= self.reversal_atr
                )

                low_ready = bool(
                    running_low_index
                    < i
                    and
                    np.isfinite(
                        low_atr_ref
                    )
                    and
                    (
                        low_reversal
                        / low_atr_ref
                    )
                    >= self.reversal_atr
                )

                first_kind: (
                    str | None
                ) = None

                # -------------------------------------------------------------
                # If both are possible, confirm the MORE RECENT terminal
                # extreme, not the older one.
                # -------------------------------------------------------------

                if (
                    high_ready
                    and low_ready
                ):

                    if (
                        running_high_index
                        > running_low_index
                    ):

                        first_kind = "HIGH"

                    elif (
                        running_low_index
                        > running_high_index
                    ):

                        first_kind = "LOW"

                elif high_ready:

                    first_kind = "HIGH"

                elif low_ready:

                    first_kind = "LOW"

                if first_kind == "HIGH":

                    reversal_atr_value = (
                        high_reversal
                        / high_atr_ref
                    )

                    confirm_swing(
                        kind="HIGH",
                        origin_index=(
                            running_high_index
                        ),
                        confirmation_index=i,
                        price=(
                            running_high
                        ),
                        excursion_value=(
                            high_reversal
                        ),
                        excursion_atr_value=(
                            reversal_atr_value
                        ),
                        reversal_value=(
                            high_reversal
                        ),
                        reversal_atr_value=(
                            reversal_atr_value
                        ),
                    )

                    mode = "SEEK_LOW"

                    # Candidate low belongs to a later candle than
                    # the confirmed high origin, so chronology is known.
                    candidate_low = float(
                        low[i]
                    )

                    candidate_low_index = (
                        i
                    )

                    candidate_low_atr = (
                        current_atr
                    )

                    continue

                if first_kind == "LOW":

                    reversal_atr_value = (
                        low_reversal
                        / low_atr_ref
                    )

                    confirm_swing(
                        kind="LOW",
                        origin_index=(
                            running_low_index
                        ),
                        confirmation_index=i,
                        price=(
                            running_low
                        ),
                        excursion_value=(
                            low_reversal
                        ),
                        excursion_atr_value=(
                            reversal_atr_value
                        ),
                        reversal_value=(
                            low_reversal
                        ),
                        reversal_atr_value=(
                            reversal_atr_value
                        ),
                    )

                    mode = "SEEK_HIGH"

                    candidate_high = float(
                        high[i]
                    )

                    candidate_high_index = (
                        i
                    )

                    candidate_high_atr = (
                        current_atr
                    )

                    continue

            # =================================================================
            # Previous confirmed swing = LOW.
            # Seek a terminal HIGH.
            # =================================================================

            elif mode == "SEEK_HIGH":

                candidate_updated = False

                if (
                    not np.isfinite(
                        candidate_high
                    )
                    or
                    high[i]
                    > candidate_high
                ):

                    candidate_high = float(
                        high[i]
                    )

                    candidate_high_index = (
                        i
                    )

                    candidate_high_atr = (
                        current_atr
                    )

                    candidate_updated = True

                # Same candle created the candidate high.
                # Intrabar high/low ordering is unknown.
                if candidate_updated:
                    continue

                if (
                    last_swing_price
                    is None
                ):
                    continue

                atr_ref = (
                    self._atr_reference(
                        candidate_high_atr,
                        current_atr,
                    )
                )

                if not np.isfinite(
                    atr_ref
                ):
                    continue

                reversal_value = (
                    candidate_high
                    - float(
                        low[i]
                    )
                )

                reversal_atr_value = (
                    reversal_value
                    / atr_ref
                )

                if (
                    reversal_atr_value
                    < self.reversal_atr
                ):
                    continue

                excursion_value = max(
                    0.0,
                    (
                        candidate_high
                        - last_swing_price
                    ),
                )

                excursion_atr_value = (
                    excursion_value
                    / atr_ref
                )

                confirm_swing(
                    kind="HIGH",
                    origin_index=(
                        candidate_high_index
                    ),
                    confirmation_index=i,
                    price=(
                        candidate_high
                    ),
                    excursion_value=(
                        excursion_value
                    ),
                    excursion_atr_value=(
                        excursion_atr_value
                    ),
                    reversal_value=(
                        reversal_value
                    ),
                    reversal_atr_value=(
                        reversal_atr_value
                    ),
                )

                mode = "SEEK_LOW"

                candidate_low = float(
                    low[i]
                )

                candidate_low_index = (
                    i
                )

                candidate_low_atr = (
                    current_atr
                )

                continue

            # =================================================================
            # Previous confirmed swing = HIGH.
            # Seek a terminal LOW.
            # =================================================================

            elif mode == "SEEK_LOW":

                candidate_updated = False

                if (
                    not np.isfinite(
                        candidate_low
                    )
                    or
                    low[i]
                    < candidate_low
                ):

                    candidate_low = float(
                        low[i]
                    )

                    candidate_low_index = (
                        i
                    )

                    candidate_low_atr = (
                        current_atr
                    )

                    candidate_updated = True

                if candidate_updated:
                    continue

                if (
                    last_swing_price
                    is None
                ):
                    continue

                atr_ref = (
                    self._atr_reference(
                        candidate_low_atr,
                        current_atr,
                    )
                )

                if not np.isfinite(
                    atr_ref
                ):
                    continue

                reversal_value = (
                    float(
                        high[i]
                    )
                    - candidate_low
                )

                reversal_atr_value = (
                    reversal_value
                    / atr_ref
                )

                if (
                    reversal_atr_value
                    < self.reversal_atr
                ):
                    continue

                excursion_value = max(
                    0.0,
                    (
                        last_swing_price
                        - candidate_low
                    ),
                )

                excursion_atr_value = (
                    excursion_value
                    / atr_ref
                )

                confirm_swing(
                    kind="LOW",
                    origin_index=(
                        candidate_low_index
                    ),
                    confirmation_index=i,
                    price=(
                        candidate_low
                    ),
                    excursion_value=(
                        excursion_value
                    ),
                    excursion_atr_value=(
                        excursion_atr_value
                    ),
                    reversal_value=(
                        reversal_value
                    ),
                    reversal_atr_value=(
                        reversal_atr_value
                    ),
                )

                mode = "SEEK_HIGH"

                candidate_high = float(
                    high[i]
                )

                candidate_high_index = (
                    i
                )

                candidate_high_atr = (
                    current_atr
                )

                continue

        return (
            self._assign_swing_outputs(
                df,
                outputs,
            )
        )

    # =========================================================================
    # Legacy method alias
    # =========================================================================

    def detect_pivots(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        if "atr" not in df.columns:

            df["atr"] = (
                self.calculate_atr(
                    df
                )
            )

        return self.detect_swings(
            df
        )

    # =========================================================================
    # Structure
    # =========================================================================

    def detect_structure(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        required = {
            "swing_id",
            "swing_type",
            "swing_price",
            "major_high",
            "major_low",
        }

        missing = (
            required
            - set(
                df.columns
            )
        )

        if missing:

            raise ValueError(
                "Missing required structure columns: "
                + ", ".join(
                    sorted(
                        missing
                    )
                )
            )

        row_count = len(
            df
        )

        swing_ids = np.asarray(
            pd.to_numeric(
                df["swing_id"],
                errors="coerce",
            ).fillna(
                0
            ),
            dtype=np.int64,
        )

        swing_types = np.asarray(
            df["swing_type"],
            dtype=object,
        )

        prices = np.asarray(
            pd.to_numeric(
                df["swing_price"],
                errors="coerce",
            ),
            dtype=np.float64,
        )

        major_high = np.asarray(
            pd.to_numeric(
                df["major_high"],
                errors="coerce",
            ).fillna(
                0
            ),
            dtype=np.int8,
        )

        major_low = np.asarray(
            pd.to_numeric(
                df["major_low"],
                errors="coerce",
            ).fillna(
                0
            ),
            dtype=np.int8,
        )

        if "atr" in df.columns:

            atr = np.asarray(
                pd.to_numeric(
                    df["atr"],
                    errors="coerce",
                ),
                dtype=np.float64,
            )

        else:

            atr = np.full(
                row_count,
                np.nan,
                dtype=np.float64,
            )

        hh = np.zeros(
            row_count,
            dtype=np.int8,
        )

        hl = np.zeros(
            row_count,
            dtype=np.int8,
        )

        lh = np.zeros(
            row_count,
            dtype=np.int8,
        )

        ll = np.zeros(
            row_count,
            dtype=np.int8,
        )

        structure = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        last_swing_high_values = np.full(
            row_count,
            np.nan,
            dtype=np.float64,
        )

        last_swing_low_values = np.full(
            row_count,
            np.nan,
            dtype=np.float64,
        )

        last_major_high_values = np.full(
            row_count,
            np.nan,
            dtype=np.float64,
        )

        last_major_low_values = np.full(
            row_count,
            np.nan,
            dtype=np.float64,
        )

        previous_high: (
            float | None
        ) = None

        previous_low: (
            float | None
        ) = None

        last_swing_high: (
            float | None
        ) = None

        last_swing_low: (
            float | None
        ) = None

        last_major_high: (
            float | None
        ) = None

        last_major_low: (
            float | None
        ) = None

        for i in range(
            row_count
        ):

            tolerance = 0.0

            if (
                np.isfinite(
                    atr[i]
                )
                and atr[i] > 0.0
            ):

                tolerance = (
                    atr[i]
                    * self.equality_atr
                )

            if (
                swing_ids[i]
                > 0
                and
                np.isfinite(
                    prices[i]
                )
            ):

                price = float(
                    prices[i]
                )

                current_type = str(
                    swing_types[i]
                ).upper()

                if current_type == "HIGH":

                    if (
                        previous_high
                        is not None
                    ):

                        if (
                            price
                            > previous_high
                            + tolerance
                        ):

                            hh[i] = 1

                            structure[i] = (
                                "HH"
                            )

                        elif (
                            price
                            < previous_high
                            - tolerance
                        ):

                            lh[i] = 1

                            structure[i] = (
                                "LH"
                            )

                    previous_high = price

                    last_swing_high = (
                        price
                    )

                elif current_type == "LOW":

                    if (
                        previous_low
                        is not None
                    ):

                        if (
                            price
                            > previous_low
                            + tolerance
                        ):

                            hl[i] = 1

                            structure[i] = (
                                "HL"
                            )

                        elif (
                            price
                            < previous_low
                            - tolerance
                        ):

                            ll[i] = 1

                            structure[i] = (
                                "LL"
                            )

                    previous_low = price

                    last_swing_low = (
                        price
                    )

            if (
                major_high[i]
                == 1
                and
                np.isfinite(
                    prices[i]
                )
            ):

                last_major_high = float(
                    prices[i]
                )

            if (
                major_low[i]
                == 1
                and
                np.isfinite(
                    prices[i]
                )
            ):

                last_major_low = float(
                    prices[i]
                )

            if (
                last_swing_high
                is not None
            ):

                last_swing_high_values[
                    i
                ] = last_swing_high

            if (
                last_swing_low
                is not None
            ):

                last_swing_low_values[
                    i
                ] = last_swing_low

            if (
                last_major_high
                is not None
            ):

                last_major_high_values[
                    i
                ] = last_major_high

            if (
                last_major_low
                is not None
            ):

                last_major_low_values[
                    i
                ] = last_major_low

        df["HH"] = hh
        df["HL"] = hl
        df["LH"] = lh
        df["LL"] = ll

        df[
            "structure"
        ] = structure

        df[
            "last_swing_high"
        ] = last_swing_high_values

        df[
            "last_swing_low"
        ] = last_swing_low_values

        df[
            "last_major_high"
        ] = last_major_high_values

        df[
            "last_major_low"
        ] = last_major_low_values

        return df

    # =========================================================================
    # Persistent structure state
    # =========================================================================

    def add_structure_state(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        if "structure" not in df.columns:

            raise ValueError(
                "Missing required structure column: structure"
            )

        values = np.asarray(
            df["structure"],
            dtype=object,
        )

        bias_values = np.full(
            len(df),
            "NEUTRAL",
            dtype=object,
        )

        latest_high_relation: (
            str | None
        ) = None

        latest_low_relation: (
            str | None
        ) = None

        bias = "NEUTRAL"

        for i in range(
            len(df)
        ):

            event = str(
                values[i]
            ).upper()

            if event in (
                "HH",
                "LH",
            ):

                latest_high_relation = (
                    event
                )

            elif event in (
                "HL",
                "LL",
            ):

                latest_low_relation = (
                    event
                )

            if (
                latest_high_relation
                == "HH"
                and
                latest_low_relation
                == "HL"
            ):

                bias = "BULLISH"

            elif (
                latest_high_relation
                == "LH"
                and
                latest_low_relation
                == "LL"
            ):

                bias = "BEARISH"

            bias_values[i] = (
                bias
            )

        df[
            "structure_bias"
        ] = bias_values

        return df

    # =========================================================================
    # Main
    # =========================================================================

    def generate(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        self._validate_input(
            df
        )

        data = df.copy()

        data["atr"] = (
            self.calculate_atr(
                data
            )
        )

        data = self.detect_swings(
            data
        )

        data = self.detect_structure(
            data
        )

        data = self.add_structure_state(
            data
        )

        return data


market_structure = (
    MarketStructure()
)