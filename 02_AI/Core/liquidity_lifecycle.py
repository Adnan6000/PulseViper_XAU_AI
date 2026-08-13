"""
===============================================================================
Module      : liquidity_lifecycle.py
Project     : PulseViper XAU AI
Version     : 1.1
Purpose     : Causal Contextual Liquidity Lifecycle Engine
===============================================================================

Research contract
-----------------
This module tracks the lifecycle of already-known market liquidity levels.

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

Important causality rule
------------------------
A liquidity level discovered/confirmed on candle i is registered on candle i,
but candle i is NOT allowed to retrospectively test/sweep/break that level.

Lifecycle evaluation begins from candle i + 1.

This is especially important for confirmed MarketStructure swings because their
origin price may be in the past, but the swing only becomes known on its causal
confirmation candle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class _LiquidityLevel:
    """
    Internal mutable research representation of one liquidity level.
    """

    level_id: int
    source: str
    side: str
    price: float
    first_seen_index: int

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
    """
    Causal liquidity lifecycle research engine.
    """

    VERSION = "1.1"

    MODE = "CAUSAL_RESEARCH_METADATA_ONLY"

    STATIC_CONTEXT_SOURCES = (
        (
            "PDH",
            "HIGH",
            "ctx_pdh",
        ),
        (
            "PDL",
            "LOW",
            "ctx_pdl",
        ),
        (
            "PWH",
            "HIGH",
            "ctx_pwh",
        ),
        (
            "PWL",
            "LOW",
            "ctx_pwl",
        ),
        (
            "PREV_ASIA_HIGH",
            "HIGH",
            "ctx_prev_asia_high",
        ),
        (
            "PREV_ASIA_LOW",
            "LOW",
            "ctx_prev_asia_low",
        ),
        (
            "PREV_LONDON_HIGH",
            "HIGH",
            "ctx_prev_london_high",
        ),
        (
            "PREV_LONDON_LOW",
            "LOW",
            "ctx_prev_london_low",
        ),
        (
            "PREV_NEW_YORK_HIGH",
            "HIGH",
            "ctx_prev_new_york_high",
        ),
        (
            "PREV_NEW_YORK_LOW",
            "LOW",
            "ctx_prev_new_york_low",
        ),
    )

    def __init__(
        self,
        touch_buffer_atr: float = 0.03,
        sweep_buffer_atr: float = 0.03,
        break_buffer_atr: float = 0.02,
        reclaim_buffer_atr: float = 0.00,
        acceptance_closes: int = 2,
        equality_tolerance: float = 1e-9,
    ) -> None:

        for (
            name,
            value,
        ) in (
            (
                "touch_buffer_atr",
                touch_buffer_atr,
            ),
            (
                "sweep_buffer_atr",
                sweep_buffer_atr,
            ),
            (
                "break_buffer_atr",
                break_buffer_atr,
            ),
            (
                "reclaim_buffer_atr",
                reclaim_buffer_atr,
            ),
        ):

            if float(
                value
            ) < 0.0:

                raise ValueError(
                    f"{name} cannot be negative"
                )

        if int(
            acceptance_closes
        ) < 1:

            raise ValueError(
                "acceptance_closes must be at least one"
            )

        if float(
            equality_tolerance
        ) < 0.0:

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
        Safe pandas/numpy/Python scalar conversion.

        Prevents Pylance Scalar -> float typing problems and rejects
        complex / invalid / missing values.
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

    # =========================================================================
    # Level registration
    # =========================================================================

    def _register(
        self,
        registry: list[
            _LiquidityLevel
        ],
        lookup: dict[
            tuple[
                str,
                str,
                float,
            ],
            int,
        ],
        next_id: int,
        source: str,
        side: str,
        price: float,
        index: int,
    ) -> int:

        if not np.isfinite(
            price
        ):

            return next_id

        key = (
            source,
            side,
            round(
                price,
                8,
            ),
        )

        if key in lookup:

            return next_id

        registry.append(
            _LiquidityLevel(
                level_id=next_id,
                source=source,
                side=side,
                price=float(
                    price
                ),
                first_seen_index=int(
                    index
                ),
            )
        )

        lookup[
            key
        ] = next_id

        return (
            next_id
            +
            1
        )

    def _register_context_levels(
        self,
        df: pd.DataFrame,
        index: int,
        registry: list[
            _LiquidityLevel
        ],
        lookup: dict[
            tuple[
                str,
                str,
                float,
            ],
            int,
        ],
        next_id: int,
    ) -> int:

        # ---------------------------------------------------------------------
        # Previous day/week/session contextual levels
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
                ].iat[
                    index
                ]
            )

            next_id = self._register(
                registry=registry,
                lookup=lookup,
                next_id=next_id,
                source=source,
                side=side,
                price=price,
                index=index,
            )

        # ---------------------------------------------------------------------
        # Confirmed causal MarketStructure swings
        # ---------------------------------------------------------------------

        swing_required = {
            "swing_id",
            "swing_type",
            "swing_price",
            "swing_scale",
        }

        if swing_required.issubset(
            df.columns
        ):

            swing_id = self._safe_float(
                df[
                    "swing_id"
                ].iat[
                    index
                ]
            )

            swing_price = self._safe_float(
                df[
                    "swing_price"
                ].iat[
                    index
                ]
            )

            swing_type = str(
                df[
                    "swing_type"
                ].iat[
                    index
                ]
            ).upper()

            swing_scale = str(
                df[
                    "swing_scale"
                ].iat[
                    index
                ]
            ).upper()

            if (
                np.isfinite(
                    swing_id
                )
                and
                int(
                    swing_id
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

                next_id = self._register(
                    registry=registry,
                    lookup=lookup,
                    next_id=next_id,
                    source=(
                        f"{swing_scale}_{swing_type}"
                    ),
                    side=swing_type,
                    price=swing_price,
                    index=index,
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

        _ = low

        price = (
            level.price
        )

        touched = (
            high
            >=
            (
                price
                -
                touch_buffer
            )
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

        event: str | None = None

        if touched:

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

        # ---------------------------------------------------------------------
        # Previously broken/accepted high reclaimed back below.
        # ---------------------------------------------------------------------

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

        # ---------------------------------------------------------------------
        # Close decisively above high-side liquidity.
        # ---------------------------------------------------------------------

        if beyond:

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

        # ---------------------------------------------------------------------
        # Wick through liquidity but close back below.
        # ---------------------------------------------------------------------

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

        # ---------------------------------------------------------------------
        # Simple interaction/touch.
        # ---------------------------------------------------------------------

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

        _ = high

        price = (
            level.price
        )

        touched = (
            low
            <=
            (
                price
                +
                touch_buffer
            )
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

        event: str | None = None

        if touched:

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

        # ---------------------------------------------------------------------
        # Previously broken/accepted low reclaimed back above.
        # ---------------------------------------------------------------------

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

        # ---------------------------------------------------------------------
        # Close decisively below low-side liquidity.
        # ---------------------------------------------------------------------

        if beyond:

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

        # ---------------------------------------------------------------------
        # Wick below liquidity but close back above.
        # ---------------------------------------------------------------------

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
                item[0],
                item[1],
            ),
        )[2]

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

        # ---------------------------------------------------------------------
        # ATR
        # ---------------------------------------------------------------------

        if "atr" in df.columns:

            atr = self._numeric_array(
                df,
                "atr",
            )

        else:

            previous_close = (
                pd.Series(
                    close
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
                        low
                    ),

                    (
                        pd.Series(
                            high
                        )
                        -
                        previous_close
                    ).abs(),

                    (
                        pd.Series(
                            low
                        )
                        -
                        previous_close
                    ).abs(),
                ],
                axis=1,
            ).max(
                axis=1
            )

            atr = (
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
        # Primary event telemetry
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
        # Per-bar event counts
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
        # Registry state counts
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
            tuple[
                str,
                str,
                float,
            ],
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
            # STEP 1
            #
            # Register contextual levels that are known by the close of this
            # candle.
            #
            # Newly registered levels are deliberately NOT evaluated against
            # this same candle.
            # -----------------------------------------------------------------

            next_id = (
                self._register_context_levels(
                    df=df,
                    index=i,
                    registry=registry,
                    lookup=lookup,
                    next_id=next_id,
                )
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
            # STEP 2
            #
            # Evaluate this candle against liquidity known BEFORE this candle.
            # -----------------------------------------------------------------

            for level in registry:

                if (
                    level.first_seen_index
                    >=
                    i
                ):

                    continue

                previous_touches = (
                    level.touches
                )

                if (
                    level.side
                    ==
                    "HIGH"
                ):

                    event = (
                        self._update_high_level(
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
                    )

                else:

                    event = (
                        self._update_low_level(
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
            # Choose primary lifecycle event for the candle.
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
                ] = (
                    selected_level.source
                )

                event_side[
                    i
                ] = (
                    selected_level.side
                )

                event_price[
                    i
                ] = (
                    selected_level.price
                )

            # -----------------------------------------------------------------
            # Nearest high/low liquidity relative to current close.
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
                ] = (
                    nearest_above.price
                )

                nearest_above_source[
                    i
                ] = (
                    nearest_above.source
                )

                nearest_above_state[
                    i
                ] = (
                    nearest_above.state
                )

                nearest_above_touches[
                    i
                ] = (
                    nearest_above.touches
                )

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
                ] = (
                    nearest_below.price
                )

                nearest_below_source[
                    i
                ] = (
                    nearest_below.source
                )

                nearest_below_state[
                    i
                ] = (
                    nearest_below.state
                )

                nearest_below_touches[
                    i
                ] = (
                    nearest_below.touches
                )

                nearest_below_age[
                    i
                ] = (
                    i
                    -
                    nearest_below.first_seen_index
                )

            # -----------------------------------------------------------------
            # Current state distribution
            # -----------------------------------------------------------------

            total_registered[
                i
            ] = len(
                registry
            )

            for level in registry:

                if (
                    level.state
                    ==
                    "UNTOUCHED"
                ):

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

                elif (
                    level.state
                    ==
                    "TESTED"
                ):

                    tested_count[
                        i
                    ] += 1

                elif (
                    level.state
                    ==
                    "SWEPT"
                ):

                    swept_count[
                        i
                    ] += 1

                elif (
                    level.state
                    ==
                    "BROKEN"
                ):

                    broken_count[
                        i
                    ] += 1

                elif (
                    level.state
                    ==
                    "ACCEPTED_BEYOND"
                ):

                    accepted_count[
                        i
                    ] += 1

                elif (
                    level.state
                    ==
                    "RECLAIMED"
                ):

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
        # Primary candle event
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
        # Per-bar event counts
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
        # Registry state distribution
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