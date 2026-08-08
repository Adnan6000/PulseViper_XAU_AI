"""
===============================================================================
Module      : market_structure.py
Project     : PulseViper XAU AI
Version     : 6.0
Author      : Muhammad Adnan
Purpose     : Adaptive Scalping Market Structure & Swing Engine
===============================================================================

Design
------
This engine is built for XAUUSD scalping.

It does NOT assume that a swing must contain a fixed number of candles.

A swing may take:
- 2-3 candles
- 5 candles
- 14 candles
- 20+ candles

The market decides swing length.

Core principles
---------------
1. Chronological / causal processing.
2. Candidate extremes extend until a meaningful reversal confirms them.
3. Confirmed swings alternate HIGH -> LOW -> HIGH -> LOW.
4. A stronger/newer extreme replaces the previous candidate.
5. Swing origin and confirmation are stored separately.
6. Swing importance is based on actual excursion relative to ATR.
7. MICRO / INTERNAL / MAJOR hierarchy supports scalping.
8. HH / HL / LH / LL operate on confirmed swings.
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

        # ---------------------------------------------------------------------
        # Legacy compatibility
        #
        # Old callers may still provide these arguments.
        # pivot_window is intentionally ignored because v6 is not window based.
        # min_strength / major_strength map to the new ATR swing hierarchy.
        # ---------------------------------------------------------------------
        pivot_window: int | None = None,
        min_strength: float | None = None,
        major_strength: float | None = None,
    ) -> None:

        if atr_period <= 0:
            raise ValueError(
                "atr_period must be greater than zero"
            )

        if reversal_atr <= 0:
            raise ValueError(
                "reversal_atr must be greater than zero"
            )

        if min_strength is not None:
            min_swing_atr = float(
                min_strength
            )

        if major_strength is not None:
            major_swing_atr = float(
                major_strength
            )

            # Legacy diagnostics may provide:
            # min=0.50, major=1.00.
            #
            # Keep INTERNAL logically between them.
            if (
                major_swing_atr
                <= internal_swing_atr
            ):
                internal_swing_atr = (
                    min_swing_atr
                    + major_swing_atr
                ) / 2.0

        if min_swing_atr <= 0:
            raise ValueError(
                "min_swing_atr must be greater than zero"
            )

        if (
            internal_swing_atr
            <= min_swing_atr
        ):
            raise ValueError(
                "internal_swing_atr must be greater "
                "than min_swing_atr"
            )

        if (
            major_swing_atr
            <= internal_swing_atr
        ):
            raise ValueError(
                "major_swing_atr must be greater "
                "than internal_swing_atr"
            )

        self.atr_period = int(
            atr_period
        )

        self.reversal_atr = float(
            reversal_atr
        )

        self.min_swing_atr = float(
            min_swing_atr
        )

        self.internal_swing_atr = float(
            internal_swing_atr
        )

        self.major_swing_atr = float(
            major_swing_atr
        )

        # Legacy public attributes.
        self.pivot_window = pivot_window

        self.min_strength = (
            self.min_swing_atr
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
            - set(df.columns)
        )

        if missing:

            raise ValueError(
                "Missing required columns: "
                + ", ".join(
                    sorted(missing)
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
    # Swing Scale
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
    # Adaptive Swing Detection
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
            - set(df.columns)
        )

        if missing:

            raise ValueError(
                "Missing required swing columns: "
                + ", ".join(
                    sorted(missing)
                )
            )

        row_count = len(
            df
        )

        # ---------------------------------------------------------------------
        # Numeric arrays
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

        # ---------------------------------------------------------------------
        # Legacy output contract
        # ---------------------------------------------------------------------

        pivot_high = np.zeros(
            row_count,
            dtype=np.int8,
        )

        pivot_low = np.zeros(
            row_count,
            dtype=np.int8,
        )

        pivot_strength = np.zeros(
            row_count,
            dtype=np.float64,
        )

        minor_high = np.zeros(
            row_count,
            dtype=np.int8,
        )

        minor_low = np.zeros(
            row_count,
            dtype=np.int8,
        )

        major_high = np.zeros(
            row_count,
            dtype=np.int8,
        )

        major_low = np.zeros(
            row_count,
            dtype=np.int8,
        )

        major_swing = np.zeros(
            row_count,
            dtype=np.int8,
        )

        swing_score = np.zeros(
            row_count,
            dtype=np.float64,
        )

        swing_id = np.zeros(
            row_count,
            dtype=np.int64,
        )

        swing_type = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        swing_price = np.full(
            row_count,
            np.nan,
            dtype=np.float64,
        )

        # ---------------------------------------------------------------------
        # New scalping hierarchy
        # ---------------------------------------------------------------------

        micro_high = np.zeros(
            row_count,
            dtype=np.int8,
        )

        micro_low = np.zeros(
            row_count,
            dtype=np.int8,
        )

        internal_high = np.zeros(
            row_count,
            dtype=np.int8,
        )

        internal_low = np.zeros(
            row_count,
            dtype=np.int8,
        )

        swing_scale = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        # ---------------------------------------------------------------------
        # Causal timing / geometry
        # ---------------------------------------------------------------------

        swing_origin_index = np.full(
            row_count,
            -1,
            dtype=np.int64,
        )

        swing_confirmation_index = np.full(
            row_count,
            -1,
            dtype=np.int64,
        )

        swing_origin_time = np.full(
            row_count,
            None,
            dtype=object,
        )

        swing_confirmation_time = np.full(
            row_count,
            None,
            dtype=object,
        )

        swing_leg_bars = np.zeros(
            row_count,
            dtype=np.int64,
        )

        swing_confirmation_bars = np.zeros(
            row_count,
            dtype=np.int64,
        )

        swing_excursion = np.zeros(
            row_count,
            dtype=np.float64,
        )

        swing_excursion_atr = np.zeros(
            row_count,
            dtype=np.float64,
        )

        swing_reversal = np.zeros(
            row_count,
            dtype=np.float64,
        )

        swing_reversal_atr = np.zeros(
            row_count,
            dtype=np.float64,
        )

        # ---------------------------------------------------------------------
        # Empty / unusable data
        # ---------------------------------------------------------------------

        if row_count == 0:

            return self._assign_swing_outputs(
                df=df,
                pivot_high=pivot_high,
                pivot_low=pivot_low,
                pivot_strength=pivot_strength,
                minor_high=minor_high,
                minor_low=minor_low,
                major_high=major_high,
                major_low=major_low,
                major_swing=major_swing,
                swing_score=swing_score,
                swing_id=swing_id,
                swing_type=swing_type,
                swing_price=swing_price,
                micro_high=micro_high,
                micro_low=micro_low,
                internal_high=internal_high,
                internal_low=internal_low,
                swing_scale=swing_scale,
                swing_origin_index=swing_origin_index,
                swing_confirmation_index=(
                    swing_confirmation_index
                ),
                swing_origin_time=swing_origin_time,
                swing_confirmation_time=(
                    swing_confirmation_time
                ),
                swing_leg_bars=swing_leg_bars,
                swing_confirmation_bars=(
                    swing_confirmation_bars
                ),
                swing_excursion=swing_excursion,
                swing_excursion_atr=(
                    swing_excursion_atr
                ),
                swing_reversal=swing_reversal,
                swing_reversal_atr=(
                    swing_reversal_atr
                ),
            )

        valid = (
            np.isfinite(high)
            &
            np.isfinite(low)
            &
            np.isfinite(close)
            &
            np.isfinite(atr)
            &
            (atr > 0)
        )

        valid_indices = np.flatnonzero(
            valid
        )

        if len(valid_indices) == 0:

            return self._assign_swing_outputs(
                df=df,
                pivot_high=pivot_high,
                pivot_low=pivot_low,
                pivot_strength=pivot_strength,
                minor_high=minor_high,
                minor_low=minor_low,
                major_high=major_high,
                major_low=major_low,
                major_swing=major_swing,
                swing_score=swing_score,
                swing_id=swing_id,
                swing_type=swing_type,
                swing_price=swing_price,
                micro_high=micro_high,
                micro_low=micro_low,
                internal_high=internal_high,
                internal_low=internal_low,
                swing_scale=swing_scale,
                swing_origin_index=swing_origin_index,
                swing_confirmation_index=(
                    swing_confirmation_index
                ),
                swing_origin_time=swing_origin_time,
                swing_confirmation_time=(
                    swing_confirmation_time
                ),
                swing_leg_bars=swing_leg_bars,
                swing_confirmation_bars=(
                    swing_confirmation_bars
                ),
                swing_excursion=swing_excursion,
                swing_excursion_atr=(
                    swing_excursion_atr
                ),
                swing_reversal=swing_reversal,
                swing_reversal_atr=(
                    swing_reversal_atr
                ),
            )

        next_swing_id = 1

        last_swing_price: float | None = None
        last_swing_origin: int | None = None
        last_swing_type: str | None = None

        # ---------------------------------------------------------------------
        # Event writer
        #
        # IMPORTANT:
        # Event is written on CONFIRMATION candle.
        # Actual turning point is stored in swing_origin_index.
        # ---------------------------------------------------------------------

        def confirm_swing(
            kind: str,
            origin_index: int,
            confirmation_index: int,
            price: float,
            excursion_value: float,
            reversal_value: float,
            excursion_atr_value: float,
            reversal_atr_value: float,
        ) -> None:

            nonlocal next_swing_id
            nonlocal last_swing_price
            nonlocal last_swing_origin
            nonlocal last_swing_type

            event_index = (
                confirmation_index
            )

            scale = self._swing_scale(
                excursion_atr_value
            )

            if kind == "HIGH":

                pivot_high[
                    event_index
                ] = 1

                if scale == "MICRO":
                    micro_high[
                        event_index
                    ] = 1

                    minor_high[
                        event_index
                    ] = 1

                elif scale == "INTERNAL":
                    internal_high[
                        event_index
                    ] = 1

                    minor_high[
                        event_index
                    ] = 1

                else:
                    major_high[
                        event_index
                    ] = 1

                    major_swing[
                        event_index
                    ] = 1

            else:

                pivot_low[
                    event_index
                ] = 1

                if scale == "MICRO":
                    micro_low[
                        event_index
                    ] = 1

                    minor_low[
                        event_index
                    ] = 1

                elif scale == "INTERNAL":
                    internal_low[
                        event_index
                    ] = 1

                    minor_low[
                        event_index
                    ] = 1

                else:
                    major_low[
                        event_index
                    ] = 1

                    major_swing[
                        event_index
                    ] = 1

            pivot_strength[
                event_index
            ] = excursion_atr_value

            swing_id[
                event_index
            ] = next_swing_id

            swing_type[
                event_index
            ] = kind

            swing_price[
                event_index
            ] = price

            swing_scale[
                event_index
            ] = scale

            swing_origin_index[
                event_index
            ] = origin_index

            swing_confirmation_index[
                event_index
            ] = confirmation_index

            swing_origin_time[
                event_index
            ] = time_values[
                origin_index
            ]

            swing_confirmation_time[
                event_index
            ] = time_values[
                confirmation_index
            ]

            swing_confirmation_bars[
                event_index
            ] = max(
                0,
                confirmation_index
                - origin_index,
            )

            if last_swing_origin is not None:

                swing_leg_bars[
                    event_index
                ] = abs(
                    origin_index
                    - last_swing_origin
                )

            swing_excursion[
                event_index
            ] = excursion_value

            swing_excursion_atr[
                event_index
            ] = excursion_atr_value

            swing_reversal[
                event_index
            ] = reversal_value

            swing_reversal_atr[
                event_index
            ] = reversal_atr_value

            score = (
                excursion_atr_value
                * 18.0
                +
                reversal_atr_value
                * 22.0
            )

            swing_score[
                event_index
            ] = round(
                min(
                    100.0,
                    max(
                        0.0,
                        score,
                    ),
                ),
                2,
            )

            next_swing_id += 1

            last_swing_price = price

            last_swing_origin = (
                origin_index
            )

            last_swing_type = kind

        # =========================================================================
        # Bootstrap
        # =========================================================================

        first = int(
            valid_indices[0]
        )

        running_high = float(
            high[first]
        )

        running_high_index = first

        running_low = float(
            low[first]
        )

        running_low_index = first

        mode = "SEEK_INITIAL"

        candidate_high = np.nan
        candidate_high_index = -1

        candidate_low = np.nan
        candidate_low_index = -1

        # =========================================================================
        # Chronological State Machine
        # =========================================================================

        for i in range(
            first + 1,
            row_count,
        ):

            if not valid[i]:
                continue

            # =====================================================================
            # Find first confirmed turning point.
            # =====================================================================

            if mode == "SEEK_INITIAL":

                if (
                    high[i]
                    > running_high
                ):
                    running_high = float(
                        high[i]
                    )

                    running_high_index = i

                if (
                    low[i]
                    < running_low
                ):
                    running_low = float(
                        low[i]
                    )

                    running_low_index = i

                low_atr = float(
                    atr[
                        running_low_index
                    ]
                )

                high_atr = float(
                    atr[
                        running_high_index
                    ]
                )

                upward_departure = (
                    close[i]
                    - running_low
                )

                downward_departure = (
                    running_high
                    - close[i]
                )

                low_ready = (
                    running_low_index < i
                    and
                    upward_departure
                    >= (
                        self.min_swing_atr
                        * low_atr
                    )
                )

                high_ready = (
                    running_high_index < i
                    and
                    downward_departure
                    >= (
                        self.min_swing_atr
                        * high_atr
                    )
                )

                # -------------------------------------------------------------
                # If both are technically possible, prefer the older extreme.
                # Same-candle ambiguity is deliberately not guessed.
                # -------------------------------------------------------------

                if low_ready and high_ready:

                    if (
                        running_low_index
                        == running_high_index
                    ):
                        continue

                    low_ready = (
                        running_low_index
                        < running_high_index
                    )

                    high_ready = (
                        running_high_index
                        < running_low_index
                    )

                if low_ready:

                    excursion_value = (
                        upward_departure
                    )

                    excursion_atr_value = (
                        excursion_value
                        / low_atr
                    )

                    confirm_swing(
                        kind="LOW",
                        origin_index=(
                            running_low_index
                        ),
                        confirmation_index=i,
                        price=running_low,
                        excursion_value=(
                            excursion_value
                        ),
                        reversal_value=(
                            upward_departure
                        ),
                        excursion_atr_value=(
                            excursion_atr_value
                        ),
                        reversal_atr_value=(
                            excursion_atr_value
                        ),
                    )

                    mode = "SEEK_HIGH"

                    # Seed next leg from close, not current high/low,
                    # avoiding intrabar ordering assumptions.
                    candidate_high = float(
                        close[i]
                    )

                    candidate_high_index = i

                    continue

                if high_ready:

                    excursion_value = (
                        downward_departure
                    )

                    excursion_atr_value = (
                        excursion_value
                        / high_atr
                    )

                    confirm_swing(
                        kind="HIGH",
                        origin_index=(
                            running_high_index
                        ),
                        confirmation_index=i,
                        price=running_high,
                        excursion_value=(
                            excursion_value
                        ),
                        reversal_value=(
                            downward_departure
                        ),
                        excursion_atr_value=(
                            excursion_atr_value
                        ),
                        reversal_atr_value=(
                            excursion_atr_value
                        ),
                    )

                    mode = "SEEK_LOW"

                    candidate_low = float(
                        close[i]
                    )

                    candidate_low_index = i

                    continue

            # =====================================================================
            # After LOW -> seek next HIGH
            # =====================================================================

            elif mode == "SEEK_HIGH":

                if (
                    high[i]
                    > candidate_high
                ):

                    candidate_high = float(
                        high[i]
                    )

                    candidate_high_index = i

                if (
                    last_swing_price
                    is None
                ):
                    continue

                candidate_atr = float(
                    atr[
                        candidate_high_index
                    ]
                )

                excursion_value = (
                    candidate_high
                    - last_swing_price
                )

                reversal_value = (
                    candidate_high
                    - close[i]
                )

                excursion_atr_value = (
                    excursion_value
                    / candidate_atr
                )

                reversal_atr_value = (
                    reversal_value
                    / candidate_atr
                )

                excursion_ready = (
                    excursion_atr_value
                    >= self.min_swing_atr
                )

                reversal_ready = (
                    reversal_atr_value
                    >= self.reversal_atr
                )

                # Do not confirm a candidate on the exact
                # candle that created the candidate extreme.
                confirmation_ready = (
                    i
                    > candidate_high_index
                )

                if (
                    excursion_ready
                    and
                    reversal_ready
                    and
                    confirmation_ready
                ):

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
                        reversal_value=(
                            reversal_value
                        ),
                        excursion_atr_value=(
                            excursion_atr_value
                        ),
                        reversal_atr_value=(
                            reversal_atr_value
                        ),
                    )

                    mode = "SEEK_LOW"

                    candidate_low = float(
                        close[i]
                    )

                    candidate_low_index = i

                    continue

            # =====================================================================
            # After HIGH -> seek next LOW
            # =====================================================================

            elif mode == "SEEK_LOW":

                if (
                    low[i]
                    < candidate_low
                ):

                    candidate_low = float(
                        low[i]
                    )

                    candidate_low_index = i

                if (
                    last_swing_price
                    is None
                ):
                    continue

                candidate_atr = float(
                    atr[
                        candidate_low_index
                    ]
                )

                excursion_value = (
                    last_swing_price
                    - candidate_low
                )

                reversal_value = (
                    close[i]
                    - candidate_low
                )

                excursion_atr_value = (
                    excursion_value
                    / candidate_atr
                )

                reversal_atr_value = (
                    reversal_value
                    / candidate_atr
                )

                excursion_ready = (
                    excursion_atr_value
                    >= self.min_swing_atr
                )

                reversal_ready = (
                    reversal_atr_value
                    >= self.reversal_atr
                )

                confirmation_ready = (
                    i
                    > candidate_low_index
                )

                if (
                    excursion_ready
                    and
                    reversal_ready
                    and
                    confirmation_ready
                ):

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
                        reversal_value=(
                            reversal_value
                        ),
                        excursion_atr_value=(
                            excursion_atr_value
                        ),
                        reversal_atr_value=(
                            reversal_atr_value
                        ),
                    )

                    mode = "SEEK_HIGH"

                    candidate_high = float(
                        close[i]
                    )

                    candidate_high_index = i

                    continue

        return self._assign_swing_outputs(
            df=df,
            pivot_high=pivot_high,
            pivot_low=pivot_low,
            pivot_strength=pivot_strength,
            minor_high=minor_high,
            minor_low=minor_low,
            major_high=major_high,
            major_low=major_low,
            major_swing=major_swing,
            swing_score=swing_score,
            swing_id=swing_id,
            swing_type=swing_type,
            swing_price=swing_price,
            micro_high=micro_high,
            micro_low=micro_low,
            internal_high=internal_high,
            internal_low=internal_low,
            swing_scale=swing_scale,
            swing_origin_index=swing_origin_index,
            swing_confirmation_index=(
                swing_confirmation_index
            ),
            swing_origin_time=swing_origin_time,
            swing_confirmation_time=(
                swing_confirmation_time
            ),
            swing_leg_bars=swing_leg_bars,
            swing_confirmation_bars=(
                swing_confirmation_bars
            ),
            swing_excursion=swing_excursion,
            swing_excursion_atr=(
                swing_excursion_atr
            ),
            swing_reversal=swing_reversal,
            swing_reversal_atr=(
                swing_reversal_atr
            ),
        )

    # =========================================================================
    # Output Assignment
    # =========================================================================

    @staticmethod
    def _assign_swing_outputs(
        df: pd.DataFrame,
        **outputs: Any,
    ) -> pd.DataFrame:

        result = df.copy()

        for (
            column,
            values,
        ) in outputs.items():

            result[column] = values

        return result

    # =========================================================================
    # Structure Classification
    # =========================================================================

    def detect_structure(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        row_count = len(
            df
        )

        df["HH"] = 0
        df["HL"] = 0
        df["LH"] = 0
        df["LL"] = 0

        df["structure"] = "NONE"

        df["last_swing_high"] = np.nan
        df["last_swing_low"] = np.nan

        df["last_major_high"] = np.nan
        df["last_major_low"] = np.nan

        swing_ids = np.asarray(
            df["swing_id"],
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

        major_high_values = np.asarray(
            df["major_high"],
            dtype=np.int8,
        )

        major_low_values = np.asarray(
            df["major_low"],
            dtype=np.int8,
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

        previous_high: float | None = None
        previous_low: float | None = None

        last_swing_high: float | None = None
        last_swing_low: float | None = None

        last_major_high: float | None = None
        last_major_low: float | None = None

        for i in range(
            row_count
        ):

            if swing_ids[i] > 0:

                price = prices[i]

                if (
                    np.isfinite(
                        price
                    )
                ):

                    if (
                        swing_types[i]
                        == "HIGH"
                    ):

                        if (
                            previous_high
                            is not None
                        ):

                            if (
                                price
                                > previous_high
                            ):

                                hh[i] = 1
                                structure[i] = "HH"

                            elif (
                                price
                                < previous_high
                            ):

                                lh[i] = 1
                                structure[i] = "LH"

                        previous_high = price
                        last_swing_high = price

                    elif (
                        swing_types[i]
                        == "LOW"
                    ):

                        if (
                            previous_low
                            is not None
                        ):

                            if (
                                price
                                > previous_low
                            ):

                                hl[i] = 1
                                structure[i] = "HL"

                            elif (
                                price
                                < previous_low
                            ):

                                ll[i] = 1
                                structure[i] = "LL"

                        previous_low = price
                        last_swing_low = price

            if (
                major_high_values[i]
                == 1
                and
                np.isfinite(
                    prices[i]
                )
            ):
                last_major_high = (
                    prices[i]
                )

            if (
                major_low_values[i]
                == 1
                and
                np.isfinite(
                    prices[i]
                )
            ):
                last_major_low = (
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

        df["structure"] = (
            structure
        )

        df["last_swing_high"] = (
            last_swing_high_values
        )

        df["last_swing_low"] = (
            last_swing_low_values
        )

        df["last_major_high"] = (
            last_major_high_values
        )

        df["last_major_low"] = (
            last_major_low_values
        )

        return df

    # =========================================================================
    # Persistent Structure Bias
    # =========================================================================

    def add_structure_state(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        structure_values = np.asarray(
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

            event = (
                structure_values[i]
            )

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

            # Bullish structure needs BOTH:
            # higher highs + higher lows.
            if (
                latest_high_relation
                == "HH"
                and
                latest_low_relation
                == "HL"
            ):

                bias = "BULLISH"

            # Bearish structure needs BOTH:
            # lower highs + lower lows.
            elif (
                latest_high_relation
                == "LH"
                and
                latest_low_relation
                == "LL"
            ):

                bias = "BEARISH"

            bias_values[i] = bias

        df["structure_bias"] = (
            bias_values
        )

        return df

    # =========================================================================
    # Main Pipeline
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


# =============================================================================
# Global Engine
# =============================================================================

market_structure = (
    MarketStructure()
)