"""
===============================================================================
Module      : liquidity_lifecycle.py
Project     : PulseViper XAU AI
Version     : 1.2
Purpose     : Causal Contextual Liquidity Lifecycle Engine
===============================================================================

Research contract
-----------------
This module tracks the lifecycle of already-known contextual liquidity levels.

It does NOT:
- open trades
- change trade_ready
- change Confidence
- change SetupState
- change BOS
- change risk
- use future candles
- assume every liquidity interaction is tradable

Supported contextual liquidity
------------------------------
External/context levels:
- PDH / PDL
- PWH / PWL
- Previous Asia High / Low
- Previous London High / Low
- Previous New York High / Low

Structural liquidity:
- MICRO swing High / Low
- INTERNAL swing High / Low
- MAJOR swing High / Low

Lifecycle states
----------------
UNTOUCHED
TESTED
SWEPT
BROKEN
ACCEPTED_BEYOND
RECLAIMED

Causality rules
---------------
1. Completed previous-period context (PDH/PDL/PWH/PWL/previous sessions) is
   already known when the current period begins, so it may be evaluated on the
   same row on which that contextual value first appears in this dataframe.

2. Confirmed MarketStructure swings become known only on their confirmation
   candle. They are registered on that candle but cannot be evaluated against
   the same candle. Swing lifecycle evaluation begins on the next candle.

3. Static contextual sources rotate with their causal period. When a new PDH,
   PDL, previous-session level, etc. replaces the prior one, the old contextual
   instance is deactivated and no longer competes as current liquidity.

4. Confirmed structural swings use swing_id identity, not only price identity.
   Two separate swings at the same price therefore remain separate events.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class _LiquidityLevel:
    """Internal mutable representation of one causal liquidity instance."""

    level_id: int
    identity_key: str
    source: str
    side: str
    price: float
    first_seen_index: int
    eligible_from_index: int
    active: bool = True

    state: str = "UNTOUCHED"
    touches: int = 0

    first_touch_index: int = -1
    last_touch_index: int = -1

    sweep_index: int = -1
    break_index: int = -1
    accept_index: int = -1
    reclaim_index: int = -1

    consecutive_beyond: int = 0


class LiquidityLifecycleMap:
    """Causal liquidity lifecycle research engine."""

    VERSION = "1.2"
    MODE = "CAUSAL_RESEARCH_METADATA_ONLY"

    STATIC_CONTEXT_SOURCES: tuple[tuple[str, str, str], ...] = (
        ("PDH", "HIGH", "ctx_pdh"),
        ("PDL", "LOW", "ctx_pdl"),
        ("PWH", "HIGH", "ctx_pwh"),
        ("PWL", "LOW", "ctx_pwl"),
        ("PREV_ASIA_HIGH", "HIGH", "ctx_prev_asia_high"),
        ("PREV_ASIA_LOW", "LOW", "ctx_prev_asia_low"),
        ("PREV_LONDON_HIGH", "HIGH", "ctx_prev_london_high"),
        ("PREV_LONDON_LOW", "LOW", "ctx_prev_london_low"),
        ("PREV_NEW_YORK_HIGH", "HIGH", "ctx_prev_new_york_high"),
        ("PREV_NEW_YORK_LOW", "LOW", "ctx_prev_new_york_low"),
    )

    WEEKLY_CONTEXT_SOURCES = {
        "PWH",
        "PWL",
    }

    def __init__(
        self,
        touch_buffer_atr: float = 0.03,
        sweep_buffer_atr: float = 0.03,
        break_buffer_atr: float = 0.02,
        reclaim_buffer_atr: float = 0.00,
        acceptance_closes: int = 2,
        equality_tolerance: float = 1e-9,
    ) -> None:
        values = (
            ("touch_buffer_atr", touch_buffer_atr),
            ("sweep_buffer_atr", sweep_buffer_atr),
            ("break_buffer_atr", break_buffer_atr),
            ("reclaim_buffer_atr", reclaim_buffer_atr),
        )

        for name, value in values:
            if float(value) < 0.0:
                raise ValueError(
                    f"{name} cannot be negative"
                )

        if int(acceptance_closes) < 1:
            raise ValueError(
                "acceptance_closes must be at least one"
            )

        if float(equality_tolerance) < 0.0:
            raise ValueError(
                "equality_tolerance cannot be negative"
            )

        self.touch_buffer_atr = float(
            touch_buffer_atr
        )

        self.sweep_buffer_atr = float(
            sweep_buffer_atr
        )

        self.break_buffer_atr = float(
            break_buffer_atr
        )

        self.reclaim_buffer_atr = float(
            reclaim_buffer_atr
        )

        self.acceptance_closes = int(
            acceptance_closes
        )

        self.equality_tolerance = float(
            equality_tolerance
        )

    # =========================================================================
    # Validation / conversion
    # =========================================================================

    @staticmethod
    def _validate(
        df: pd.DataFrame,
    ) -> None:
        if not isinstance(
            df,
            pd.DataFrame,
        ):
            raise TypeError(
                "LiquidityLifecycleMap input "
                "must be a pandas DataFrame"
            )

        required = {
            "high",
            "low",
            "close",
        }

        missing = (
            required
            -
            set(
                df.columns
            )
        )

        if missing:
            raise ValueError(
                "Missing required liquidity-lifecycle columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )

    @staticmethod
    def _safe_float(
        value: Any,
    ) -> float:
        """
        Convert pandas/numpy/Python scalar to finite float safely.

        This helper intentionally accepts Any so pandas Scalar unions do not
        propagate Pylance float-conversion warnings through the engine.
        """

        if (
            value is None
            or
            isinstance(
                value,
                complex,
            )
        ):
            return float(
                "nan"
            )

        try:
            if bool(
                pd.isna(
                    value
                )
            ):
                return float(
                    "nan"
                )

        except (
            TypeError,
            ValueError,
        ):
            return float(
                "nan"
            )

        try:
            number = float(
                value
            )

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return float(
                "nan"
            )

        if not np.isfinite(
            number
        ):
            return float(
                "nan"
            )

        return number

    @staticmethod
    def _numeric_array(
        df: pd.DataFrame,
        column: str,
    ) -> np.ndarray:
        return (
            pd.to_numeric(
                df[
                    column
                ],
                errors="coerce",
            )
            .to_numpy(
                dtype=float
            )
        )

    @staticmethod
    def _safe_text(
        value: Any,
        default: str = "NONE",
    ) -> str:
        if value is None:
            return default

        try:
            if bool(
                pd.isna(
                    value
                )
            ):
                return default

        except (
            TypeError,
            ValueError,
        ):
            return default

        text = (
            str(
                value
            )
            .strip()
            .upper()
        )

        if not text:
            return default

        return text

    # =========================================================================
    # Context identity / registration
    # =========================================================================

    def _period_token(
        self,
        df: pd.DataFrame,
        index: int,
        source: str,
        price: float,
    ) -> str:
        """
        Return a causal token for the active contextual period.

        With a time column:
        - PDH/PDL and previous-session levels rotate daily.
        - PWH/PWL rotate weekly.

        Without time, price identity is used as a safe fallback. This keeps
        deterministic standalone tests working even when no timestamp exists.
        """

        fallback = (
            "PRICE:"
            +
            f"{round(float(price), 8):.8f}"
        )

        if "time" not in df.columns:
            return fallback

        raw_time: Any = (
            df[
                "time"
            ]
            .iat[
                index
            ]
        )

        try:
            parsed: Any = pd.to_datetime(
                raw_time,
                utc=True,
                errors="coerce",
            )

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return fallback

        if not isinstance(
            parsed,
            pd.Timestamp,
        ):
            return fallback

        if pd.isna(
            parsed
        ):
            return fallback

        if source in self.WEEKLY_CONTEXT_SOURCES:
            iso: Any = (
                parsed
                .isocalendar()
            )

            return (
                f"{int(iso.year):04d}"
                f"-W{int(iso.week):02d}"
            )

        return parsed.strftime(
            "%Y-%m-%d"
        )

    @staticmethod
    def _deactivate_position(
        registry: list[
            _LiquidityLevel
        ],
        position: int | None,
    ) -> None:
        if position is None:
            return

        if (
            0
            <=
            position
            <
            len(
                registry
            )
        ):
            registry[
                position
            ].active = False

    def _register(
        self,
        registry: list[
            _LiquidityLevel
        ],
        lookup: dict[
            str,
            int,
        ],
        next_id: int,
        identity_key: str,
        source: str,
        side: str,
        price: float,
        index: int,
        eligible_from_index: int,
    ) -> tuple[
        int,
        int | None,
    ]:
        if not np.isfinite(
            price
        ):
            return (
                next_id,
                None,
            )

        existing_position = (
            lookup.get(
                identity_key
            )
        )

        if existing_position is not None:
            if (
                0
                <=
                existing_position
                <
                len(
                    registry
                )
            ):
                registry[
                    existing_position
                ].active = True

                return (
                    next_id,
                    existing_position,
                )

            lookup.pop(
                identity_key,
                None,
            )

        position = len(
            registry
        )

        registry.append(
            _LiquidityLevel(
                level_id=next_id,
                identity_key=identity_key,
                source=source,
                side=side,
                price=float(
                    price
                ),
                first_seen_index=int(
                    index
                ),
                eligible_from_index=int(
                    eligible_from_index
                ),
            )
        )

        lookup[
            identity_key
        ] = position

        return (
            next_id
            +
            1,
            position,
        )

    def _register_context_levels(
        self,
        df: pd.DataFrame,
        index: int,
        registry: list[
            _LiquidityLevel
        ],
        lookup: dict[
            str,
            int,
        ],
        active_static: dict[
            str,
            int,
        ],
        next_id: int,
    ) -> int:
        # ---------------------------------------------------------------------
        # Completed previous-period context.
        #
        # These values are already known for the current period and therefore
        # are eligible on the same row where they first appear.
        # ---------------------------------------------------------------------

        for (
            source,
            side,
            column,
        ) in self.STATIC_CONTEXT_SOURCES:
            if column not in df.columns:
                continue

            price = self._safe_float(
                df[
                    column
                ]
                .iat[
                    index
                ]
            )

            previous_position = (
                active_static.get(
                    source
                )
            )

            if not np.isfinite(
                price
            ):
                self._deactivate_position(
                    registry,
                    previous_position,
                )

                active_static.pop(
                    source,
                    None,
                )

                continue

            token = self._period_token(
                df=df,
                index=index,
                source=source,
                price=price,
            )

            identity_key = (
                f"STATIC|{source}|"
                f"{token}|"
                f"{round(float(price), 8):.8f}"
            )

            if previous_position is not None:
                if (
                    0
                    <=
                    previous_position
                    <
                    len(
                        registry
                    )
                ):
                    previous_level = (
                        registry[
                            previous_position
                        ]
                    )

                    if (
                        previous_level.identity_key
                        !=
                        identity_key
                    ):
                        previous_level.active = False

                        active_static.pop(
                            source,
                            None,
                        )

            (
                next_id,
                position,
            ) = self._register(
                registry=registry,
                lookup=lookup,
                next_id=next_id,
                identity_key=identity_key,
                source=source,
                side=side,
                price=price,
                index=index,
                eligible_from_index=index,
            )

            if position is not None:
                active_static[
                    source
                ] = position

        # ---------------------------------------------------------------------
        # Confirmed causal MarketStructure swings.
        #
        # swing_id is the unique identity.
        # Evaluation starts on the next candle.
        # ---------------------------------------------------------------------

        swing_required = {
            "swing_id",
            "swing_type",
            "swing_price",
            "swing_scale",
        }

        if not swing_required.issubset(
            df.columns
        ):
            return next_id

        swing_id_value = self._safe_float(
            df[
                "swing_id"
            ]
            .iat[
                index
            ]
        )

        swing_price = self._safe_float(
            df[
                "swing_price"
            ]
            .iat[
                index
            ]
        )

        swing_type = self._safe_text(
            df[
                "swing_type"
            ]
            .iat[
                index
            ]
        )

        swing_scale = self._safe_text(
            df[
                "swing_scale"
            ]
            .iat[
                index
            ]
        )

        if not (
            np.isfinite(
                swing_id_value
            )
            and
            int(
                swing_id_value
            )
            >
            0
            and
            np.isfinite(
                swing_price
            )
            and
            swing_type
            in {
                "HIGH",
                "LOW",
            }
            and
            swing_scale
            in {
                "MICRO",
                "INTERNAL",
                "MAJOR",
            }
        ):
            return next_id

        swing_id = int(
            swing_id_value
        )

        identity_key = (
            f"SWING|{swing_id}"
        )

        (
            next_id,
            _,
        ) = self._register(
            registry=registry,
            lookup=lookup,
            next_id=next_id,
            identity_key=identity_key,
            source=(
                f"{swing_scale}_"
                f"{swing_type}"
            ),
            side=swing_type,
            price=swing_price,
            index=index,
            eligible_from_index=(
                index
                +
                1
            ),
        )

        return next_id

    # =========================================================================
    # ATR buffers
    # =========================================================================

    def _buffers(
        self,
        atr: float,
    ) -> tuple[
        float,
        float,
        float,
        float,
    ]:
        if (
            not np.isfinite(
                atr
            )
            or
            atr <= 0.0
        ):
            return (
                0.0,
                0.0,
                0.0,
                0.0,
            )

        return (
            atr
            *
            self.touch_buffer_atr,

            atr
            *
            self.sweep_buffer_atr,

            atr
            *
            self.break_buffer_atr,

            atr
            *
            self.reclaim_buffer_atr,
        )

    # =========================================================================
    # Touch geometry
    # =========================================================================

    def _range_overlaps_level(
        self,
        high: float,
        low: float,
        price: float,
        buffer_value: float,
    ) -> bool:
        """
        True only when the candle range actually overlaps the level zone.

        This prevents candles trading completely beyond a level from being
        counted as repeated touches merely because their high/low remains on
        the far side of the level.
        """

        lower_bound = (
            price
            -
            buffer_value
            -
            self.equality_tolerance
        )

        upper_bound = (
            price
            +
            buffer_value
            +
            self.equality_tolerance
        )

        return (
            high
            >=
            lower_bound
            and
            low
            <=
            upper_bound
        )

    @staticmethod
    def _record_touch(
        level: _LiquidityLevel,
        index: int,
    ) -> None:
        level.touches += 1

        if (
            level.first_touch_index
            <
            0
        ):
            level.first_touch_index = (
                index
            )

        level.last_touch_index = (
            index
        )

    # =========================================================================
    # HIGH-side lifecycle
    # =========================================================================

    def _update_high_level(
        self,
        level: _LiquidityLevel,
        high: float,
        low: float,
        close: float,
        index: int,
        touch_buffer: float,
        sweep_buffer: float,
        break_buffer: float,
        reclaim_buffer: float,
    ) -> str | None:
        price = level.price

        touched = self._range_overlaps_level(
            high=high,
            low=low,
            price=price,
            buffer_value=touch_buffer,
        )

        swept = (
            high
            >
            (
                price
                +
                sweep_buffer
            )
            and
            close
            <
            price
        )

        beyond = (
            close
            >
            (
                price
                +
                break_buffer
            )
        )

        reclaimed = (
            level.state
            in {
                "BROKEN",
                "ACCEPTED_BEYOND",
            }
            and
            close
            <
            (
                price
                -
                reclaim_buffer
            )
        )

        if touched:
            self._record_touch(
                level,
                index,
            )

        if reclaimed:
            level.state = (
                "RECLAIMED"
            )

            if (
                level.reclaim_index
                <
                0
            ):
                level.reclaim_index = (
                    index
                )

            level.consecutive_beyond = 0

            return (
                "RECLAIMED"
            )

        if beyond:
            event: str | None = None

            if level.state not in {
                "BROKEN",
                "ACCEPTED_BEYOND",
            }:
                level.state = (
                    "BROKEN"
                )

                if (
                    level.break_index
                    <
                    0
                ):
                    level.break_index = (
                        index
                    )

                event = (
                    "BROKEN"
                )

            level.consecutive_beyond += 1

            if (
                level.consecutive_beyond
                >=
                self.acceptance_closes
            ):
                if (
                    level.state
                    !=
                    "ACCEPTED_BEYOND"
                ):
                    level.state = (
                        "ACCEPTED_BEYOND"
                    )

                    if (
                        level.accept_index
                        <
                        0
                    ):
                        level.accept_index = (
                            index
                        )

                    event = (
                        "ACCEPTED_BEYOND"
                    )

            return event

        level.consecutive_beyond = 0

        if swept:
            level.state = (
                "SWEPT"
            )

            if (
                level.sweep_index
                <
                0
            ):
                level.sweep_index = (
                    index
                )

            return (
                "SWEPT"
            )

        if (
            touched
            and
            level.state
            ==
            "UNTOUCHED"
        ):
            level.state = (
                "TESTED"
            )

            return (
                "TESTED"
            )

        return None

    # =========================================================================
    # LOW-side lifecycle
    # =========================================================================

    def _update_low_level(
        self,
        level: _LiquidityLevel,
        high: float,
        low: float,
        close: float,
        index: int,
        touch_buffer: float,
        sweep_buffer: float,
        break_buffer: float,
        reclaim_buffer: float,
    ) -> str | None:
        price = level.price

        touched = self._range_overlaps_level(
            high=high,
            low=low,
            price=price,
            buffer_value=touch_buffer,
        )

        swept = (
            low
            <
            (
                price
                -
                sweep_buffer
            )
            and
            close
            >
            price
        )

        beyond = (
            close
            <
            (
                price
                -
                break_buffer
            )
        )

        reclaimed = (
            level.state
            in {
                "BROKEN",
                "ACCEPTED_BEYOND",
            }
            and
            close
            >
            (
                price
                +
                reclaim_buffer
            )
        )

        if touched:
            self._record_touch(
                level,
                index,
            )

        if reclaimed:
            level.state = (
                "RECLAIMED"
            )

            if (
                level.reclaim_index
                <
                0
            ):
                level.reclaim_index = (
                    index
                )

            level.consecutive_beyond = 0

            return (
                "RECLAIMED"
            )

        if beyond:
            event: str | None = None

            if level.state not in {
                "BROKEN",
                "ACCEPTED_BEYOND",
            }:
                level.state = (
                    "BROKEN"
                )

                if (
                    level.break_index
                    <
                    0
                ):
                    level.break_index = (
                        index
                    )

                event = (
                    "BROKEN"
                )

            level.consecutive_beyond += 1

            if (
                level.consecutive_beyond
                >=
                self.acceptance_closes
            ):
                if (
                    level.state
                    !=
                    "ACCEPTED_BEYOND"
                ):
                    level.state = (
                        "ACCEPTED_BEYOND"
                    )

                    if (
                        level.accept_index
                        <
                        0
                    ):
                        level.accept_index = (
                            index
                        )

                    event = (
                        "ACCEPTED_BEYOND"
                    )

            return event

        level.consecutive_beyond = 0

        if swept:
            level.state = (
                "SWEPT"
            )

            if (
                level.sweep_index
                <
                0
            ):
                level.sweep_index = (
                    index
                )

            return (
                "SWEPT"
            )

        if (
            touched
            and
            level.state
            ==
            "UNTOUCHED"
        ):
            level.state = (
                "TESTED"
            )

            return (
                "TESTED"
            )

        return None

    # =========================================================================
    # Nearest active contextual liquidity
    # =========================================================================

    @staticmethod
    def _nearest(
        registry: list[
            _LiquidityLevel
        ],
        current_price: float,
        side: str,
    ) -> _LiquidityLevel | None:
        candidates: list[
            tuple[
                float,
                int,
                _LiquidityLevel,
            ]
        ] = []

        for level in registry:
            if (
                not level.active
                or
                level.side
                !=
                side
            ):
                continue

            if side == "HIGH":
                distance = (
                    level.price
                    -
                    current_price
                )

            else:
                distance = (
                    current_price
                    -
                    level.price
                )

            if distance < 0.0:
                continue

            candidates.append(
                (
                    distance,
                    level.level_id,
                    level,
                )
            )

        if not candidates:
            return None

        return min(
            candidates,
            key=lambda item: (
                item[
                    0
                ],
                item[
                    1
                ],
            ),
        )[
            2
        ]

    # =========================================================================
    # ATR fallback
    # =========================================================================

    @staticmethod
    def _atr_array(
        df: pd.DataFrame,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
    ) -> np.ndarray:
        if "atr" in df.columns:
            return (
                pd.to_numeric(
                    df[
                        "atr"
                    ],
                    errors="coerce",
                )
                .to_numpy(
                    dtype=float
                )
            )

        previous_close = (
            pd.Series(
                close,
                dtype="float64",
            )
            .shift(
                1
            )
        )

        true_range = pd.concat(
            [
                pd.Series(
                    high
                    -
                    low,
                    dtype="float64",
                ),

                (
                    pd.Series(
                        high,
                        dtype="float64",
                    )
                    -
                    previous_close
                ).abs(),

                (
                    pd.Series(
                        low,
                        dtype="float64",
                    )
                    -
                    previous_close
                ).abs(),
            ],
            axis=1,
        ).max(
            axis=1
        )

        return (
            true_range
            .rolling(
                window=14,
                min_periods=1,
            )
            .mean()
            .to_numpy(
                dtype=float
            )
        )

    # =========================================================================
    # Generate
    # =========================================================================

    def generate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        self._validate(
            data
        )

        df = (
            data
            .copy()
            .reset_index(
                drop=True
            )
        )

        row_count = len(
            df
        )

        high = self._numeric_array(
            df,
            "high",
        )

        low = self._numeric_array(
            df,
            "low",
        )

        close = self._numeric_array(
            df,
            "close",
        )

        atr = self._atr_array(
            df,
            high,
            low,
            close,
        )

        # ---------------------------------------------------------------------
        # Row outputs
        # ---------------------------------------------------------------------

        nearest_above_price = np.full(
            row_count,
            np.nan,
            dtype=np.float64,
        )

        nearest_below_price = np.full(
            row_count,
            np.nan,
            dtype=np.float64,
        )

        nearest_above_source = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        nearest_below_source = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        nearest_above_state = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        nearest_below_state = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        nearest_above_touches = np.zeros(
            row_count,
            dtype=np.int64,
        )

        nearest_below_touches = np.zeros(
            row_count,
            dtype=np.int64,
        )

        nearest_above_age = np.full(
            row_count,
            -1,
            dtype=np.int64,
        )

        nearest_below_age = np.full(
            row_count,
            -1,
            dtype=np.int64,
        )

        # ---------------------------------------------------------------------
        # Primary event outputs
        # ---------------------------------------------------------------------

        event_type = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        event_source = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        event_side = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        event_price = np.full(
            row_count,
            np.nan,
            dtype=np.float64,
        )

        # ---------------------------------------------------------------------
        # Per-bar event counters
        # ---------------------------------------------------------------------

        touch_count = np.zeros(
            row_count,
            dtype=np.int64,
        )

        sweep_count = np.zeros(
            row_count,
            dtype=np.int64,
        )

        break_count = np.zeros(
            row_count,
            dtype=np.int64,
        )

        accept_count = np.zeros(
            row_count,
            dtype=np.int64,
        )

        reclaim_count = np.zeros(
            row_count,
            dtype=np.int64,
        )

        # ---------------------------------------------------------------------
        # Registry state counters
        # ---------------------------------------------------------------------

        untouched_above_count = np.zeros(
            row_count,
            dtype=np.int64,
        )

        untouched_below_count = np.zeros(
            row_count,
            dtype=np.int64,
        )

        tested_count = np.zeros(
            row_count,
            dtype=np.int64,
        )

        swept_count = np.zeros(
            row_count,
            dtype=np.int64,
        )

        broken_count = np.zeros(
            row_count,
            dtype=np.int64,
        )

        accepted_count = np.zeros(
            row_count,
            dtype=np.int64,
        )

        reclaimed_count = np.zeros(
            row_count,
            dtype=np.int64,
        )

        total_registered = np.zeros(
            row_count,
            dtype=np.int64,
        )

        # ---------------------------------------------------------------------
        # Internal chronological registry
        # ---------------------------------------------------------------------

        registry: list[
            _LiquidityLevel
        ] = []

        lookup: dict[
            str,
            int,
        ] = {}

        active_static: dict[
            str,
            int,
        ] = {}

        next_id = 1

        # =====================================================================
        # Chronological replay
        # =====================================================================

        for i in range(
            row_count
        ):
            if not (
                np.isfinite(
                    high[
                        i
                    ]
                )
                and
                np.isfinite(
                    low[
                        i
                    ]
                )
                and
                np.isfinite(
                    close[
                        i
                    ]
                )
            ):
                continue

            # -----------------------------------------------------------------
            # Register all context known by this candle close.
            # -----------------------------------------------------------------

            next_id = self._register_context_levels(
                df=df,
                index=i,
                registry=registry,
                lookup=lookup,
                active_static=active_static,
                next_id=next_id,
            )

            (
                touch_buffer,
                sweep_buffer,
                break_buffer,
                reclaim_buffer,
            ) = self._buffers(
                atr[
                    i
                ]
            )

            events: list[
                tuple[
                    int,
                    str,
                    _LiquidityLevel,
                ]
            ] = []

            # -----------------------------------------------------------------
            # Evaluate only active and causally eligible levels.
            # -----------------------------------------------------------------

            for level in registry:
                if not level.active:
                    continue

                if (
                    i
                    <
                    level.eligible_from_index
                ):
                    continue

                previous_touches = (
                    level.touches
                )

                if level.side == "HIGH":
                    event = self._update_high_level(
                        level=level,
                        high=high[
                            i
                        ],
                        low=low[
                            i
                        ],
                        close=close[
                            i
                        ],
                        index=i,
                        touch_buffer=touch_buffer,
                        sweep_buffer=sweep_buffer,
                        break_buffer=break_buffer,
                        reclaim_buffer=reclaim_buffer,
                    )

                else:
                    event = self._update_low_level(
                        level=level,
                        high=high[
                            i
                        ],
                        low=low[
                            i
                        ],
                        close=close[
                            i
                        ],
                        index=i,
                        touch_buffer=touch_buffer,
                        sweep_buffer=sweep_buffer,
                        break_buffer=break_buffer,
                        reclaim_buffer=reclaim_buffer,
                    )

                if (
                    level.touches
                    >
                    previous_touches
                ):
                    touch_count[
                        i
                    ] += 1

                if event is None:
                    continue

                priority = {
                    "ACCEPTED_BEYOND": 5,
                    "RECLAIMED": 4,
                    "SWEPT": 3,
                    "BROKEN": 2,
                    "TESTED": 1,
                }[
                    event
                ]

                events.append(
                    (
                        priority,
                        event,
                        level,
                    )
                )

                if event == "SWEPT":
                    sweep_count[
                        i
                    ] += 1

                elif event == "BROKEN":
                    break_count[
                        i
                    ] += 1

                elif event == "ACCEPTED_BEYOND":
                    accept_count[
                        i
                    ] += 1

                elif event == "RECLAIMED":
                    reclaim_count[
                        i
                    ] += 1

            # -----------------------------------------------------------------
            # Primary lifecycle event.
            # -----------------------------------------------------------------

            if events:
                (
                    _,
                    selected_event,
                    selected_level,
                ) = max(
                    events,
                    key=lambda item: (
                        item[
                            0
                        ],
                        -
                        item[
                            2
                        ].level_id,
                    ),
                )

                event_type[
                    i
                ] = selected_event

                event_source[
                    i
                ] = selected_level.source

                event_side[
                    i
                ] = selected_level.side

                event_price[
                    i
                ] = selected_level.price

            # -----------------------------------------------------------------
            # Nearest current active liquidity.
            # -----------------------------------------------------------------

            nearest_above = self._nearest(
                registry=registry,
                current_price=close[
                    i
                ],
                side="HIGH",
            )

            nearest_below = self._nearest(
                registry=registry,
                current_price=close[
                    i
                ],
                side="LOW",
            )

            if nearest_above is not None:
                nearest_above_price[
                    i
                ] = nearest_above.price

                nearest_above_source[
                    i
                ] = nearest_above.source

                nearest_above_state[
                    i
                ] = nearest_above.state

                nearest_above_touches[
                    i
                ] = nearest_above.touches

                nearest_above_age[
                    i
                ] = (
                    i
                    -
                    nearest_above.first_seen_index
                )

            if nearest_below is not None:
                nearest_below_price[
                    i
                ] = nearest_below.price

                nearest_below_source[
                    i
                ] = nearest_below.source

                nearest_below_state[
                    i
                ] = nearest_below.state

                nearest_below_touches[
                    i
                ] = nearest_below.touches

                nearest_below_age[
                    i
                ] = (
                    i
                    -
                    nearest_below.first_seen_index
                )

            # -----------------------------------------------------------------
            # Active registry distribution only.
            #
            # Expired PDH/session/etc instances are intentionally excluded.
            # -----------------------------------------------------------------

            active_levels = [
                level
                for level in registry
                if level.active
            ]

            total_registered[
                i
            ] = len(
                active_levels
            )

            for level in active_levels:
                if level.state == "UNTOUCHED":
                    if (
                        level.side
                        ==
                        "HIGH"
                        and
                        level.price
                        >=
                        close[
                            i
                        ]
                    ):
                        untouched_above_count[
                            i
                        ] += 1

                    elif (
                        level.side
                        ==
                        "LOW"
                        and
                        level.price
                        <=
                        close[
                            i
                        ]
                    ):
                        untouched_below_count[
                            i
                        ] += 1

                elif level.state == "TESTED":
                    tested_count[
                        i
                    ] += 1

                elif level.state == "SWEPT":
                    swept_count[
                        i
                    ] += 1

                elif level.state == "BROKEN":
                    broken_count[
                        i
                    ] += 1

                elif level.state == "ACCEPTED_BEYOND":
                    accepted_count[
                        i
                    ] += 1

                elif level.state == "RECLAIMED":
                    reclaimed_count[
                        i
                    ] += 1

        # =====================================================================
        # Assign outputs
        # =====================================================================

        result = df.copy()

        result[
            "liq_nearest_above_price"
        ] = nearest_above_price

        result[
            "liq_nearest_above_source"
        ] = nearest_above_source

        result[
            "liq_nearest_above_state"
        ] = nearest_above_state

        result[
            "liq_nearest_above_touches"
        ] = nearest_above_touches

        result[
            "liq_nearest_above_age_bars"
        ] = nearest_above_age

        result[
            "liq_nearest_below_price"
        ] = nearest_below_price

        result[
            "liq_nearest_below_source"
        ] = nearest_below_source

        result[
            "liq_nearest_below_state"
        ] = nearest_below_state

        result[
            "liq_nearest_below_touches"
        ] = nearest_below_touches

        result[
            "liq_nearest_below_age_bars"
        ] = nearest_below_age

        # ---------------------------------------------------------------------
        # Price distances
        # ---------------------------------------------------------------------

        result[
            "liq_nearest_above_distance"
        ] = (
            nearest_above_price
            -
            close
        )

        result[
            "liq_nearest_below_distance"
        ] = (
            close
            -
            nearest_below_price
        )

        safe_atr = np.where(
            (
                np.isfinite(
                    atr
                )
                &
                (
                    atr
                    >
                    0.0
                )
            ),
            atr,
            np.nan,
        )

        result[
            "liq_nearest_above_atr"
        ] = (
            result[
                "liq_nearest_above_distance"
            ]
            .to_numpy(
                dtype=float
            )
            /
            safe_atr
        )

        result[
            "liq_nearest_below_atr"
        ] = (
            result[
                "liq_nearest_below_distance"
            ]
            .to_numpy(
                dtype=float
            )
            /
            safe_atr
        )

        # ---------------------------------------------------------------------
        # Primary event
        # ---------------------------------------------------------------------

        result[
            "liq_event_type"
        ] = event_type

        result[
            "liq_event_source"
        ] = event_source

        result[
            "liq_event_side"
        ] = event_side

        result[
            "liq_event_price"
        ] = event_price

        # ---------------------------------------------------------------------
        # Per-bar event telemetry
        # ---------------------------------------------------------------------

        result[
            "liq_touch_count_bar"
        ] = touch_count

        result[
            "liq_sweep_count_bar"
        ] = sweep_count

        result[
            "liq_break_count_bar"
        ] = break_count

        result[
            "liq_accept_count_bar"
        ] = accept_count

        result[
            "liq_reclaim_count_bar"
        ] = reclaim_count

        # ---------------------------------------------------------------------
        # Active registry distribution
        # ---------------------------------------------------------------------

        result[
            "liq_untouched_above_count"
        ] = untouched_above_count

        result[
            "liq_untouched_below_count"
        ] = untouched_below_count

        result[
            "liq_tested_count"
        ] = tested_count

        result[
            "liq_swept_count"
        ] = swept_count

        result[
            "liq_broken_count"
        ] = broken_count

        result[
            "liq_accepted_count"
        ] = accepted_count

        result[
            "liq_reclaimed_count"
        ] = reclaimed_count

        result[
            "liq_registered_count"
        ] = total_registered

        # ---------------------------------------------------------------------
        # Metadata
        # ---------------------------------------------------------------------

        result[
            "liq_lifecycle_version"
        ] = self.VERSION

        result[
            "liq_lifecycle_mode"
        ] = self.MODE

        return result


liquidity_lifecycle = (
    LiquidityLifecycleMap()
)