"""
===============================================================================
Module      : institutional_zone_context.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Causal Institutional Zone Context Adapter
===============================================================================

Purpose
-------
Convert causal Institutional Zone events + causal lifecycle state into
bar-aligned observational metadata.

For every market candle the adapter can describe:

- nearest active bullish institutional zone
- nearest active bearish institutional zone
- zone lifecycle state
- distance from current close in ATR units
- whether current close is inside the zone
- whether current candle range overlaps the zone
- active zone counts
- lifecycle state counts

Important
---------
This module does NOT decide whether a trade may occur.

Zone context is evidence, not a hard blocker.

Safety
------
- shadow research only
- no orders
- no risk sizing
- no trade_ready modification
- no confidence modification
- no setup-state modification
- no BOS modification
- no future candles
- rejects izlabel_* hindsight data
- INVALIDATED zones are excluded from active nearest-zone context
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class InstitutionalZoneContext:
    VERSION = "1.0"

    MODE = "SHADOW_CAUSAL_ZONE_CONTEXT_ONLY"

    PREFIX = "izctx_"

    REQUIRED_MARKET_COLUMNS = {
        "open",
        "high",
        "low",
        "close",
    }

    REQUIRED_ZONE_COLUMNS = {
        "iz_event_id",
        "iz_event_flag",
        "iz_direction",
        "iz_zone_type",

        "iz_confirmation_position",

        "iz_zone_high",
        "iz_zone_low",

        "iz_live_safe",
    }

    REQUIRED_LIFECYCLE_COLUMNS = {
        "izl_event_id",
        "izl_observation_position",
        "izl_state",
        "izl_live_safe",
    }

    PROTECTED_EXACT = {
        "trade_ready",
        "pipeline_version",
        "pipeline_mode",
    }

    PROTECTED_PREFIXES = (
        "confidence_",
        "setup_",
        "bos_",
    )

    OUTPUT_COLUMNS = (
        "izctx_active_bullish_count",
        "izctx_active_bearish_count",

        "izctx_fresh_count",
        "izctx_mitigated_count",
        "izctx_accepted_count",
        "izctx_invalidated_count",

        "izctx_bullish_event_id",
        "izctx_bullish_state",
        "izctx_bullish_zone_type",

        "izctx_bullish_zone_high",
        "izctx_bullish_zone_low",
        "izctx_bullish_zone_midpoint",

        "izctx_bullish_distance",
        "izctx_bullish_distance_atr",

        "izctx_bullish_inside_flag",
        "izctx_bullish_overlap_flag",

        "izctx_bullish_age_bars",
        "izctx_bullish_touch_count",

        "izctx_bearish_event_id",
        "izctx_bearish_state",
        "izctx_bearish_zone_type",

        "izctx_bearish_zone_high",
        "izctx_bearish_zone_low",
        "izctx_bearish_zone_midpoint",

        "izctx_bearish_distance",
        "izctx_bearish_distance_atr",

        "izctx_bearish_inside_flag",
        "izctx_bearish_overlap_flag",

        "izctx_bearish_age_bars",
        "izctx_bearish_touch_count",

        "izctx_any_inside_flag",

        "izctx_live_safe",
        "izctx_version",
        "izctx_mode",
    )

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _number(
        value: Any,
    ) -> float:

        try:
            number = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return np.nan

        if not np.isfinite(
            number
        ):
            return np.nan

        return number

    @classmethod
    def _integer(
        cls,
        value: Any,
    ) -> int | None:

        number = cls._number(
            value
        )

        if not np.isfinite(
            number
        ):
            return None

        return int(
            number
        )

    @staticmethod
    def _text(
        value: Any,
        default: str = "NONE",
    ) -> str:

        if value is None:
            return default

        try:
            if pd.isna(
                value
            ):
                return default

        except (
            TypeError,
            ValueError,
        ):
            pass

        text = str(
            value
        ).strip().upper()

        return (
            text
            if text
            else default
        )

    @staticmethod
    def _distance_to_zone(
        close: float,
        zone_high: float,
        zone_low: float,
    ) -> float:

        if close < zone_low:
            return float(
                zone_low
                -
                close
            )

        if close > zone_high:
            return float(
                close
                -
                zone_high
            )

        return 0.0

    @staticmethod
    def _inside(
        close: float,
        zone_high: float,
        zone_low: float,
    ) -> bool:

        return bool(
            zone_low
            <=
            close
            <=
            zone_high
        )

    @staticmethod
    def _overlap(
        candle_high: float,
        candle_low: float,
        zone_high: float,
        zone_low: float,
    ) -> bool:

        return bool(
            candle_low
            <=
            zone_high
            and
            candle_high
            >=
            zone_low
        )

    # =========================================================================
    # Validation
    # =========================================================================

    @classmethod
    def _validate(
        cls,
        market: pd.DataFrame,
        zone_events: pd.DataFrame,
        lifecycle: pd.DataFrame,
    ) -> None:

        for name, frame in (
            (
                "market",
                market,
            ),
            (
                "zone_events",
                zone_events,
            ),
            (
                "lifecycle",
                lifecycle,
            ),
        ):

            if not isinstance(
                frame,
                pd.DataFrame,
            ):
                raise TypeError(
                    f"{name} must be a pandas DataFrame"
                )

            if not frame.columns.is_unique:
                raise ValueError(
                    f"{name} contains duplicate columns"
                )

        missing_market = (
            cls.REQUIRED_MARKET_COLUMNS
            -
            set(
                market.columns
            )
        )

        if missing_market:
            raise ValueError(
                "Missing market columns: "
                +
                ", ".join(
                    sorted(
                        missing_market
                    )
                )
            )

        missing_zones = (
            cls.REQUIRED_ZONE_COLUMNS
            -
            set(
                zone_events.columns
            )
        )

        if missing_zones:
            raise ValueError(
                "Missing zone columns: "
                +
                ", ".join(
                    sorted(
                        missing_zones
                    )
                )
            )

        missing_lifecycle = (
            cls.REQUIRED_LIFECYCLE_COLUMNS
            -
            set(
                lifecycle.columns
            )
        )

        if missing_lifecycle:
            raise ValueError(
                "Missing lifecycle columns: "
                +
                ", ".join(
                    sorted(
                        missing_lifecycle
                    )
                )
            )

        hindsight = [
            column
            for column in (
                list(
                    market.columns
                )
                +
                list(
                    zone_events.columns
                )
                +
                list(
                    lifecycle.columns
                )
            )
            if (
                isinstance(
                    column,
                    str,
                )
                and
                column.startswith(
                    "izlabel_"
                )
            )
        ]

        if hindsight:
            raise ValueError(
                "izlabel_* hindsight columns are forbidden"
            )

        if not zone_events.empty:

            zone_safe = (
                pd.to_numeric(
                    zone_events[
                        "iz_live_safe"
                    ],
                    errors="coerce",
                )
                .fillna(
                    0
                )
                .eq(
                    1
                )
            )

            if not bool(
                zone_safe.all()
            ):
                raise ValueError(
                    "Zone context requires iz_live_safe == 1"
                )

            event_flags = (
                pd.to_numeric(
                    zone_events[
                        "iz_event_flag"
                    ],
                    errors="coerce",
                )
                .fillna(
                    0
                )
                .eq(
                    1
                )
            )

            if not bool(
                event_flags.all()
            ):
                raise ValueError(
                    "Zone context requires iz_event_flag == 1"
                )

        if not lifecycle.empty:

            lifecycle_safe = (
                pd.to_numeric(
                    lifecycle[
                        "izl_live_safe"
                    ],
                    errors="coerce",
                )
                .fillna(
                    0
                )
                .eq(
                    1
                )
            )

            if not bool(
                lifecycle_safe.all()
            ):
                raise ValueError(
                    "Zone context requires izl_live_safe == 1"
                )

    # =========================================================================
    # Protected fields
    # =========================================================================

    @classmethod
    def _protected_snapshot(
        cls,
        frame: pd.DataFrame,
    ) -> dict[
        str,
        pd.Series,
    ]:

        protected: dict[
            str,
            pd.Series,
        ] = {}

        for column in frame.columns:

            if (
                column
                in cls.PROTECTED_EXACT
                or
                any(
                    column.startswith(
                        prefix
                    )
                    for prefix
                    in cls.PROTECTED_PREFIXES
                )
            ):

                protected[
                    column
                ] = frame[
                    column
                ].copy(
                    deep=True
                )

        return protected

    @staticmethod
    def _assert_protected(
        before: dict[
            str,
            pd.Series,
        ],
        after: pd.DataFrame,
    ) -> None:

        for column, original in before.items():

            if column not in after.columns:
                raise RuntimeError(
                    f"Protected column disappeared: {column}"
                )

            if not original.equals(
                after[
                    column
                ]
            ):
                raise RuntimeError(
                    "Zone context modified protected "
                    f"column: {column}"
                )

    # =========================================================================
    # ATR
    # =========================================================================

    @classmethod
    def _causal_atr(
        cls,
        market: pd.DataFrame,
        period: int = 14,
    ) -> pd.Series:

        if "atr" in market.columns:

            supplied = pd.to_numeric(
                market[
                    "atr"
                ],
                errors="coerce",
            )

        else:

            supplied = pd.Series(
                np.nan,
                index=market.index,
                dtype=float,
            )

        high = pd.to_numeric(
            market[
                "high"
            ],
            errors="coerce",
        )

        low = pd.to_numeric(
            market[
                "low"
            ],
            errors="coerce",
        )

        close = pd.to_numeric(
            market[
                "close"
            ],
            errors="coerce",
        )

        previous_close = close.shift(
            1
        )

        true_range = pd.concat(
            [
                high
                -
                low,

                (
                    high
                    -
                    previous_close
                ).abs(),

                (
                    low
                    -
                    previous_close
                ).abs(),
            ],
            axis=1,
        ).max(
            axis=1
        )

        calculated = (
            true_range
            .rolling(
                window=period,
                min_periods=1,
            )
            .mean()
        )

        atr = (
            supplied
            .where(
                supplied
                >
                0.0,
                calculated,
            )
            .fillna(
                calculated
            )
        )

        return atr

    # =========================================================================
    # Event preparation
    # =========================================================================

    @classmethod
    def _prepare_events(
        cls,
        zone_events: pd.DataFrame,
    ) -> dict[
        int,
        list[
            dict[
                str,
                Any,
            ]
        ],
    ]:

        by_confirmation: dict[
            int,
            list[
                dict[
                    str,
                    Any,
                ]
            ],
        ] = {}

        for _, row in zone_events.iterrows():

            confirmation = cls._integer(
                row.get(
                    "iz_confirmation_position"
                )
            )

            if confirmation is None:
                continue

            event_id = cls._text(
                row.get(
                    "iz_event_id"
                ),
                "UNKNOWN",
            )

            direction = cls._text(
                row.get(
                    "iz_direction"
                ),
                "UNKNOWN",
            )

            if direction not in {
                "BULLISH",
                "BEARISH",
            }:
                raise ValueError(
                    f"Unsupported iz_direction: {direction}"
                )

            high = cls._number(
                row.get(
                    "iz_zone_high"
                )
            )

            low = cls._number(
                row.get(
                    "iz_zone_low"
                )
            )

            if (
                not np.isfinite(
                    high
                )
                or
                not np.isfinite(
                    low
                )
                or
                high
                <=
                low
            ):
                raise ValueError(
                    f"Invalid institutional zone: {event_id}"
                )

            event = {
                "event_id": event_id,

                "direction": direction,

                "zone_type": cls._text(
                    row.get(
                        "iz_zone_type"
                    ),
                    "UNKNOWN",
                ),

                "confirmation_position": (
                    confirmation
                ),

                "high": high,

                "low": low,

                "midpoint": (
                    (
                        high
                        +
                        low
                    )
                    /
                    2.0
                ),

                "strength": cls._number(
                    row.get(
                        "iz_strength"
                    )
                ),

                "state": "FRESH",

                "touch_count": 0,

                "age_bars": 0,
            }

            by_confirmation.setdefault(
                confirmation,
                [],
            ).append(
                event
            )

        return by_confirmation

    # =========================================================================
    # Lifecycle preparation
    # =========================================================================

    @classmethod
    def _prepare_lifecycle(
        cls,
        lifecycle: pd.DataFrame,
    ) -> dict[
        int,
        list[
            dict[
                str,
                Any,
            ]
        ],
    ]:

        updates: dict[
            int,
            list[
                dict[
                    str,
                    Any,
                ]
            ],
        ] = {}

        for _, row in lifecycle.iterrows():

            position = cls._integer(
                row.get(
                    "izl_observation_position"
                )
            )

            if position is None:
                continue

            update = {
                "event_id": cls._text(
                    row.get(
                        "izl_event_id"
                    ),
                    "UNKNOWN",
                ),

                "state": cls._text(
                    row.get(
                        "izl_state"
                    ),
                    "UNKNOWN",
                ),

                "touch_count": (
                    cls._integer(
                        row.get(
                            "izl_touch_count"
                        )
                    )
                    or
                    0
                ),

                "age_bars": (
                    cls._integer(
                        row.get(
                            "izl_age_bars"
                        )
                    )
                    or
                    0
                ),
            }

            updates.setdefault(
                position,
                [],
            ).append(
                update
            )

        return updates

    # =========================================================================
    # Empty nearest-zone metadata
    # =========================================================================

    @staticmethod
    def _empty_nearest(
        prefix: str,
    ) -> dict[
        str,
        Any,
    ]:

        return {
            f"izctx_{prefix}_event_id": "NONE",

            f"izctx_{prefix}_state": "NONE",

            f"izctx_{prefix}_zone_type": "NONE",

            f"izctx_{prefix}_zone_high": np.nan,

            f"izctx_{prefix}_zone_low": np.nan,

            f"izctx_{prefix}_zone_midpoint": np.nan,

            f"izctx_{prefix}_distance": np.nan,

            f"izctx_{prefix}_distance_atr": np.nan,

            f"izctx_{prefix}_inside_flag": 0,

            f"izctx_{prefix}_overlap_flag": 0,

            f"izctx_{prefix}_age_bars": np.nan,

            f"izctx_{prefix}_touch_count": 0,
        }

    # =========================================================================
    # Nearest-zone selection
    # =========================================================================

    @classmethod
    def _nearest(
        cls,
        active: dict[
            str,
            dict[
                str,
                Any,
            ],
        ],
        direction: str,
        close: float,
        candle_high: float,
        candle_low: float,
        atr: float,
    ) -> dict[
        str,
        Any,
    ]:

        candidates: list[
            tuple[
                float,
                float,
                int,
                dict[
                    str,
                    Any,
                ],
            ]
        ] = []

        for event in active.values():

            if (
                event[
                    "direction"
                ]
                !=
                direction
            ):
                continue

            if (
                event[
                    "state"
                ]
                ==
                "INVALIDATED"
            ):
                continue

            distance = (
                cls._distance_to_zone(
                    close=close,

                    zone_high=float(
                        event[
                            "high"
                        ]
                    ),

                    zone_low=float(
                        event[
                            "low"
                        ]
                    ),
                )
            )

            strength = cls._number(
                event.get(
                    "strength"
                )
            )

            if not np.isfinite(
                strength
            ):
                strength = 0.0

            confirmation = int(
                event[
                    "confirmation_position"
                ]
            )

            candidates.append(
                (
                    distance,

                    -strength,

                    -confirmation,

                    event,
                )
            )

        prefix = (
            "bullish"
            if direction == "BULLISH"
            else
            "bearish"
        )

        if not candidates:
            return cls._empty_nearest(
                prefix
            )

        candidates.sort(
            key=lambda item: (
                item[
                    0
                ],
                item[
                    1
                ],
                item[
                    2
                ],
                item[
                    3
                ][
                    "event_id"
                ],
            )
        )

        distance, _, _, event = (
            candidates[
                0
            ]
        )

        zone_high = float(
            event[
                "high"
            ]
        )

        zone_low = float(
            event[
                "low"
            ]
        )

        inside = cls._inside(
            close=close,

            zone_high=zone_high,

            zone_low=zone_low,
        )

        overlap = cls._overlap(
            candle_high=candle_high,

            candle_low=candle_low,

            zone_high=zone_high,

            zone_low=zone_low,
        )

        distance_atr = (
            distance
            /
            atr
            if (
                np.isfinite(
                    atr
                )
                and
                atr
                >
                0.0
            )
            else
            np.nan
        )

        return {
            f"izctx_{prefix}_event_id": (
                event[
                    "event_id"
                ]
            ),

            f"izctx_{prefix}_state": (
                event[
                    "state"
                ]
            ),

            f"izctx_{prefix}_zone_type": (
                event[
                    "zone_type"
                ]
            ),

            f"izctx_{prefix}_zone_high": (
                zone_high
            ),

            f"izctx_{prefix}_zone_low": (
                zone_low
            ),

            f"izctx_{prefix}_zone_midpoint": (
                event[
                    "midpoint"
                ]
            ),

            f"izctx_{prefix}_distance": (
                distance
            ),

            f"izctx_{prefix}_distance_atr": (
                distance_atr
            ),

            f"izctx_{prefix}_inside_flag": int(
                inside
            ),

            f"izctx_{prefix}_overlap_flag": int(
                overlap
            ),

            f"izctx_{prefix}_age_bars": (
                event[
                    "age_bars"
                ]
            ),

            f"izctx_{prefix}_touch_count": (
                event[
                    "touch_count"
                ]
            ),
        }

    # =========================================================================
    # Public API
    # =========================================================================

    @classmethod
    def generate(
        cls,
        market: pd.DataFrame,
        zone_events: pd.DataFrame,
        lifecycle: pd.DataFrame,
    ) -> pd.DataFrame:

        cls._validate(
            market,
            zone_events,
            lifecycle,
        )

        protected = (
            cls._protected_snapshot(
                market
            )
        )

        stale = [
            column
            for column in market.columns
            if (
                isinstance(
                    column,
                    str,
                )
                and
                column.startswith(
                    cls.PREFIX
                )
            )
        ]

        result = market.drop(
            columns=stale,
            errors="ignore",
        ).copy(
            deep=True
        )

        if result.empty:

            for column in cls.OUTPUT_COLUMNS:

                if column not in result.columns:
                    result[
                        column
                    ] = pd.Series(
                        dtype=object
                    )

            return result

        atr_series = cls._causal_atr(
            result
        )

        confirmations = (
            cls._prepare_events(
                zone_events
            )
        )

        lifecycle_updates = (
            cls._prepare_lifecycle(
                lifecycle
            )
        )

        active: dict[
            str,
            dict[
                str,
                Any,
            ],
        ] = {}

        context_rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for position in range(
            len(
                result
            )
        ):

            # -----------------------------------------------------------------
            # New confirmations become observable on this candle.
            # -----------------------------------------------------------------

            for event in confirmations.get(
                position,
                [],
            ):

                active[
                    event[
                        "event_id"
                    ]
                ] = event.copy()

            # -----------------------------------------------------------------
            # Apply lifecycle information known by THIS candle.
            # -----------------------------------------------------------------

            for update in lifecycle_updates.get(
                position,
                [],
            ):

                event_id = (
                    update[
                        "event_id"
                    ]
                )

                if event_id not in active:
                    continue

                active[
                    event_id
                ][
                    "state"
                ] = (
                    update[
                        "state"
                    ]
                )

                active[
                    event_id
                ][
                    "touch_count"
                ] = (
                    update[
                        "touch_count"
                    ]
                )

                active[
                    event_id
                ][
                    "age_bars"
                ] = (
                    update[
                        "age_bars"
                    ]
                )

            row = result.iloc[
                position
            ]

            close = cls._number(
                row.get(
                    "close"
                )
            )

            candle_high = cls._number(
                row.get(
                    "high"
                )
            )

            candle_low = cls._number(
                row.get(
                    "low"
                )
            )

            atr = cls._number(
                atr_series.iloc[
                    position
                ]
            )

            active_bullish = 0
            active_bearish = 0

            fresh = 0
            mitigated = 0
            accepted = 0
            invalidated = 0

            for event in active.values():

                state = cls._text(
                    event.get(
                        "state"
                    ),
                    "UNKNOWN",
                )

                if state == "INVALIDATED":

                    invalidated += 1

                    continue

                if (
                    event[
                        "direction"
                    ]
                    ==
                    "BULLISH"
                ):

                    active_bullish += 1

                elif (
                    event[
                        "direction"
                    ]
                    ==
                    "BEARISH"
                ):

                    active_bearish += 1

                if state == "FRESH":
                    fresh += 1

                elif state == "MITIGATED":
                    mitigated += 1

                elif state == "ACCEPTED":
                    accepted += 1

            bullish = cls._nearest(
                active=active,

                direction="BULLISH",

                close=close,

                candle_high=candle_high,

                candle_low=candle_low,

                atr=atr,
            )

            bearish = cls._nearest(
                active=active,

                direction="BEARISH",

                close=close,

                candle_high=candle_high,

                candle_low=candle_low,

                atr=atr,
            )

            context: dict[
                str,
                Any,
            ] = {
                "izctx_active_bullish_count": (
                    active_bullish
                ),

                "izctx_active_bearish_count": (
                    active_bearish
                ),

                "izctx_fresh_count": fresh,

                "izctx_mitigated_count": (
                    mitigated
                ),

                "izctx_accepted_count": (
                    accepted
                ),

                "izctx_invalidated_count": (
                    invalidated
                ),
            }

            context.update(
                bullish
            )

            context.update(
                bearish
            )

            context[
                "izctx_any_inside_flag"
            ] = int(
                bool(
                    context[
                        "izctx_bullish_inside_flag"
                    ]
                )
                or
                bool(
                    context[
                        "izctx_bearish_inside_flag"
                    ]
                )
            )

            context[
                "izctx_live_safe"
            ] = 1

            context[
                "izctx_version"
            ] = cls.VERSION

            context[
                "izctx_mode"
            ] = cls.MODE

            context_rows.append(
                context
            )

        context_frame = pd.DataFrame(
            context_rows,
            index=result.index,
        )

        result = result.join(
            context_frame
        )

        if len(
            result
        ) != len(
            market
        ):
            raise RuntimeError(
                "Zone context changed row count"
            )

        if not result.index.equals(
            market.index
        ):
            raise RuntimeError(
                "Zone context changed market alignment"
            )

        cls._assert_protected(
            protected,
            result,
        )

        return result


institutional_zone_context = (
    InstitutionalZoneContext()
)