"""
===============================================================================
Module      : institutional_zone_lifecycle.py
Project     : PulseViper XAU AI
Version     : 1.0.2
Purpose     : Causal Institutional Zone Lifecycle Intelligence
===============================================================================

Lifecycle
---------
Zone confirmation
    ↓
FRESH
    ↓
MITIGATED
    ↓
ACCEPTED
    ↓
INVALIDATED

Definitions
-----------
FRESH
    Confirmed causal zone has not yet been revisited.

MITIGATED
    A later candle overlaps the zone.

ACCEPTED
    The zone has been mitigated and price subsequently closes away from the
    zone in the intended direction.

INVALIDATED
    Bullish demand:
        close < zone_low

    Bearish supply:
        close > zone_high

INVALIDATED is terminal.

Causality
---------
- confirmation candle only creates the zone
- lifecycle evaluation starts from the NEXT candle
- no future candles used for earlier states
- prefix output must remain identical when later candles are appended
- datetime output resolution is explicitly normalized to datetime64[ns]

Safety
------
- shadow research only
- no orders
- no risk sizing
- no trade_ready modification
- no Confidence modification
- no SetupState modification
- rejects izlabel_* hindsight columns
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class InstitutionalZoneLifecycle:
    VERSION = "1.0.2"

    MODE = "SHADOW_CAUSAL_ZONE_LIFECYCLE_ONLY"

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
        "iz_origin_position",
        "iz_confirmation_position",
        "iz_zone_high",
        "iz_zone_low",
        "iz_live_safe",
    }

    OUTPUT_COLUMNS = (
        "izl_event_id",
        "izl_direction",
        "izl_zone_type",

        "izl_zone_high",
        "izl_zone_low",
        "izl_zone_midpoint",

        "izl_confirmation_position",
        "izl_confirmation_time",

        "izl_observation_position",
        "izl_observation_time",

        "izl_age_bars",

        "izl_previous_state",
        "izl_state",
        "izl_state_changed",

        "izl_overlap_flag",
        "izl_touch_count",

        "izl_fresh_flag",
        "izl_mitigated_flag",
        "izl_accepted_flag",
        "izl_invalidated_flag",

        "izl_first_mitigation_time",
        "izl_acceptance_time",
        "izl_invalidation_time",

        "izl_terminal_flag",

        "izl_live_safe",
        "izl_version",
        "izl_mode",
    )

    DATETIME_COLUMNS = (
        "izl_confirmation_time",
        "izl_observation_time",
        "izl_first_mitigation_time",
        "izl_acceptance_time",
        "izl_invalidation_time",
    )

    # =========================================================================
    # Basic helpers
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
        default: str = "UNKNOWN",
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
    def _timestamp(
        value: Any,
    ) -> pd.Timestamp | None:

        if value is None:
            return None

        timestamp = pd.to_datetime(
            value,
            errors="coerce",
            utc=True,
        )

        if pd.isna(
            timestamp
        ):
            return None

        return pd.Timestamp(
            timestamp
        ).tz_convert(
            None
        )

    # =========================================================================
    # Deterministic output schema
    # =========================================================================

    @classmethod
    def _normalize_result(
        cls,
        frame: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Enforce deterministic output schema.

        Pandas can infer different datetime resolutions depending on values:

            all NaT        -> datetime64[s]
            actual values  -> datetime64[us]

        That breaks strict causal prefix invariance even when the values
        themselves are identical.

        Every lifecycle datetime column is therefore explicitly converted to:

            datetime64[ns]
        """

        result = (
            frame.copy()
            .reindex(
                columns=list(
                    cls.OUTPUT_COLUMNS
                )
            )
            .reset_index(
                drop=True
            )
        )

        for column in cls.DATETIME_COLUMNS:

            converted = pd.to_datetime(
                result[
                    column
                ],
                errors="coerce",
            )

            # CRITICAL:
            # force one deterministic datetime resolution regardless of
            # whether the current prefix contains only NaT or real timestamps.
            result[
                column
            ] = converted.astype(
                "datetime64[ns]"
            )

        return result

    @classmethod
    def _empty_result(
        cls,
    ) -> pd.DataFrame:

        return cls._normalize_result(
            pd.DataFrame(
                columns=list(
                    cls.OUTPUT_COLUMNS
                )
            )
        )

    # =========================================================================
    # Validation
    # =========================================================================

    @classmethod
    def _validate(
        cls,
        market: pd.DataFrame,
        zone_events: pd.DataFrame,
    ) -> None:

        if not isinstance(
            market,
            pd.DataFrame,
        ):
            raise TypeError(
                "market must be a pandas DataFrame"
            )

        if not isinstance(
            zone_events,
            pd.DataFrame,
        ):
            raise TypeError(
                "zone_events must be a pandas DataFrame"
            )

        if not market.columns.is_unique:
            raise ValueError(
                "market contains duplicate columns"
            )

        if not zone_events.columns.is_unique:
            raise ValueError(
                "zone_events contains duplicate columns"
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
                "Missing zone-event columns: "
                +
                ", ".join(
                    sorted(
                        missing_zones
                    )
                )
            )

        hindsight_columns = [
            column
            for column in (
                list(
                    market.columns
                )
                +
                list(
                    zone_events.columns
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

        if hindsight_columns:

            raise ValueError(
                "izlabel_* hindsight columns are forbidden"
            )

        live_safe = (
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
            live_safe.all()
        ):

            raise ValueError(
                "Zone lifecycle requires iz_live_safe == 1"
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
                "Zone lifecycle requires iz_event_flag == 1"
            )

        event_ids = (
            zone_events[
                "iz_event_id"
            ]
            .astype(
                str
            )
        )

        if bool(
            event_ids.duplicated().any()
        ):

            raise ValueError(
                "Duplicate iz_event_id values are forbidden"
            )

    # =========================================================================
    # Market preparation
    # =========================================================================

    @classmethod
    def _prepare_market(
        cls,
        market: pd.DataFrame,
    ) -> pd.DataFrame:

        frame = market.copy(
            deep=True
        )

        frame[
            "_izl_source_position"
        ] = range(
            len(
                frame
            )
        )

        for column in (
            "open",
            "high",
            "low",
            "close",
        ):

            frame[
                column
            ] = pd.to_numeric(
                frame[
                    column
                ],
                errors="coerce",
            )

        if "time" in frame.columns:

            frame[
                "_izl_time"
            ] = (
                pd.to_datetime(
                    frame[
                        "time"
                    ],
                    errors="coerce",
                    utc=True,
                )
                .dt
                .tz_convert(
                    None
                )
                .astype(
                    "datetime64[ns]"
                )
            )

        else:

            frame[
                "_izl_time"
            ] = pd.Series(
                pd.NaT,
                index=frame.index,
                dtype="datetime64[ns]",
            )

        valid = (
            frame[
                [
                    "open",
                    "high",
                    "low",
                    "close",
                ]
            ]
            .notna()
            .all(
                axis=1
            )
        )

        valid = (
            valid
            &
            frame[
                "high"
            ].ge(
                frame[
                    "low"
                ]
            )
            &
            frame[
                "high"
            ].ge(
                frame[
                    "open"
                ]
            )
            &
            frame[
                "high"
            ].ge(
                frame[
                    "close"
                ]
            )
            &
            frame[
                "low"
            ].le(
                frame[
                    "open"
                ]
            )
            &
            frame[
                "low"
            ].le(
                frame[
                    "close"
                ]
            )
        )

        return (
            frame.loc[
                valid
            ]
            .copy()
            .reset_index(
                drop=True
            )
        )

    # =========================================================================
    # Confirmation lookup
    # =========================================================================

    @classmethod
    def _confirmation_row(
        cls,
        market: pd.DataFrame,
        event: pd.Series,
    ) -> int | None:

        confirmation_time = cls._timestamp(
            event.get(
                "iz_confirmation_time"
            )
        )

        if (
            confirmation_time is not None
            and
            "_izl_time"
            in market.columns
        ):

            confirmation_time = pd.Timestamp(
                confirmation_time
            ).as_unit(
                "ns"
            )

            matches = market.index[
                market[
                    "_izl_time"
                ].eq(
                    confirmation_time
                )
            ].tolist()

            if matches:

                return int(
                    matches[
                        0
                    ]
                )

        confirmation_position = cls._integer(
            event.get(
                "iz_confirmation_position"
            )
        )

        if confirmation_position is None:
            return None

        matches = market.index[
            pd.to_numeric(
                market[
                    "_izl_source_position"
                ],
                errors="coerce",
            ).eq(
                confirmation_position
            )
        ].tolist()

        if not matches:
            return None

        return int(
            matches[
                0
            ]
        )

    # =========================================================================
    # State rules
    # =========================================================================

    @staticmethod
    def _overlaps(
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

    @staticmethod
    def _invalidated(
        direction: str,
        close: float,
        zone_high: float,
        zone_low: float,
    ) -> bool:

        if direction == "BULLISH":

            return bool(
                close
                <
                zone_low
            )

        if direction == "BEARISH":

            return bool(
                close
                >
                zone_high
            )

        return False

    @staticmethod
    def _accepted(
        direction: str,
        close: float,
        zone_high: float,
        zone_low: float,
    ) -> bool:

        if direction == "BULLISH":

            return bool(
                close
                >
                zone_high
            )

        if direction == "BEARISH":

            return bool(
                close
                <
                zone_low
            )

        return False

    # =========================================================================
    # Timeline row
    # =========================================================================

    @classmethod
    def _timeline_row(
        cls,
        *,
        event_id: str,
        direction: str,
        zone_type: str,

        zone_high: float,
        zone_low: float,

        confirmation_position: int,
        confirmation_time: pd.Timestamp | None,

        observation_position: int,
        observation_time: pd.Timestamp | None,

        age_bars: int,

        previous_state: str,
        state: str,

        overlap_flag: int,
        touch_count: int,

        first_mitigation_time: pd.Timestamp | None,
        acceptance_time: pd.Timestamp | None,
        invalidation_time: pd.Timestamp | None,
    ) -> dict[
        str,
        Any,
    ]:

        return {
            "izl_event_id": (
                event_id
            ),

            "izl_direction": (
                direction
            ),

            "izl_zone_type": (
                zone_type
            ),

            "izl_zone_high": (
                zone_high
            ),

            "izl_zone_low": (
                zone_low
            ),

            "izl_zone_midpoint": (
                (
                    zone_high
                    +
                    zone_low
                )
                /
                2.0
            ),

            "izl_confirmation_position": (
                confirmation_position
            ),

            "izl_confirmation_time": (
                confirmation_time
            ),

            "izl_observation_position": (
                observation_position
            ),

            "izl_observation_time": (
                observation_time
            ),

            "izl_age_bars": (
                age_bars
            ),

            "izl_previous_state": (
                previous_state
            ),

            "izl_state": (
                state
            ),

            "izl_state_changed": int(
                state
                !=
                previous_state
            ),

            "izl_overlap_flag": (
                overlap_flag
            ),

            "izl_touch_count": (
                touch_count
            ),

            "izl_fresh_flag": int(
                state
                ==
                "FRESH"
            ),

            "izl_mitigated_flag": int(
                (
                    state
                    in {
                        "MITIGATED",
                        "ACCEPTED",
                        "INVALIDATED",
                    }
                )
                and
                first_mitigation_time
                is not None
            ),

            "izl_accepted_flag": int(
                state
                ==
                "ACCEPTED"
                or
                acceptance_time
                is not None
            ),

            "izl_invalidated_flag": int(
                state
                ==
                "INVALIDATED"
            ),

            "izl_first_mitigation_time": (
                first_mitigation_time
            ),

            "izl_acceptance_time": (
                acceptance_time
            ),

            "izl_invalidation_time": (
                invalidation_time
            ),

            "izl_terminal_flag": int(
                state
                ==
                "INVALIDATED"
            ),

            "izl_live_safe": 1,

            "izl_version": (
                cls.VERSION
            ),

            "izl_mode": (
                cls.MODE
            ),
        }

    # =========================================================================
    # Generation
    # =========================================================================

    @classmethod
    def generate(
        cls,
        market: pd.DataFrame,
        zone_events: pd.DataFrame,
    ) -> pd.DataFrame:

        cls._validate(
            market,
            zone_events,
        )

        data = cls._prepare_market(
            market
        )

        if (
            data.empty
            or
            zone_events.empty
        ):

            return cls._empty_result()

        rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for _, event in zone_events.iterrows():

            event_id = cls._text(
                event.get(
                    "iz_event_id"
                ),
                "UNKNOWN",
            )

            direction = cls._text(
                event.get(
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

            zone_type = cls._text(
                event.get(
                    "iz_zone_type"
                ),
                "UNKNOWN",
            )

            zone_high = cls._number(
                event.get(
                    "iz_zone_high"
                )
            )

            zone_low = cls._number(
                event.get(
                    "iz_zone_low"
                )
            )

            if (
                not np.isfinite(
                    zone_high
                )
                or
                not np.isfinite(
                    zone_low
                )
                or
                zone_high
                <=
                zone_low
            ):

                raise ValueError(
                    f"Invalid zone bounds for {event_id}"
                )

            confirmation_row = (
                cls._confirmation_row(
                    data,
                    event,
                )
            )

            if confirmation_row is None:
                continue

            confirmation = data.iloc[
                confirmation_row
            ]

            confirmation_position = int(
                confirmation[
                    "_izl_source_position"
                ]
            )

            confirmation_time = cls._timestamp(
                confirmation.get(
                    "_izl_time"
                )
            )

            if confirmation_time is not None:

                confirmation_time = (
                    pd.Timestamp(
                        confirmation_time
                    )
                    .as_unit(
                        "ns"
                    )
                )

            state = "FRESH"

            touch_count = 0

            first_mitigation_time: (
                pd.Timestamp
                |
                None
            ) = None

            acceptance_time: (
                pd.Timestamp
                |
                None
            ) = None

            invalidation_time: (
                pd.Timestamp
                |
                None
            ) = None

            # -----------------------------------------------------------------
            # Confirmation candle.
            # -----------------------------------------------------------------

            rows.append(
                cls._timeline_row(
                    event_id=event_id,

                    direction=direction,

                    zone_type=zone_type,

                    zone_high=zone_high,

                    zone_low=zone_low,

                    confirmation_position=(
                        confirmation_position
                    ),

                    confirmation_time=(
                        confirmation_time
                    ),

                    observation_position=(
                        confirmation_position
                    ),

                    observation_time=(
                        confirmation_time
                    ),

                    age_bars=0,

                    previous_state="UNCONFIRMED",

                    state="FRESH",

                    overlap_flag=0,

                    touch_count=0,

                    first_mitigation_time=None,

                    acceptance_time=None,

                    invalidation_time=None,
                )
            )

            # -----------------------------------------------------------------
            # Lifecycle starts NEXT candle.
            # -----------------------------------------------------------------

            for market_row in range(
                confirmation_row + 1,
                len(
                    data
                ),
            ):

                candle = data.iloc[
                    market_row
                ]

                observation_position = int(
                    candle[
                        "_izl_source_position"
                    ]
                )

                observation_time = cls._timestamp(
                    candle.get(
                        "_izl_time"
                    )
                )

                if observation_time is not None:

                    observation_time = (
                        pd.Timestamp(
                            observation_time
                        )
                        .as_unit(
                            "ns"
                        )
                    )

                candle_high = cls._number(
                    candle.get(
                        "high"
                    )
                )

                candle_low = cls._number(
                    candle.get(
                        "low"
                    )
                )

                candle_close = cls._number(
                    candle.get(
                        "close"
                    )
                )

                previous_state = (
                    state
                )

                overlap = cls._overlaps(
                    candle_high=candle_high,

                    candle_low=candle_low,

                    zone_high=zone_high,

                    zone_low=zone_low,
                )

                if overlap:

                    touch_count += 1

                    if (
                        first_mitigation_time
                        is None
                    ):

                        first_mitigation_time = (
                            observation_time
                        )

                # -------------------------------------------------------------
                # Highest priority: invalidation.
                # -------------------------------------------------------------

                if cls._invalidated(
                    direction=direction,

                    close=candle_close,

                    zone_high=zone_high,

                    zone_low=zone_low,
                ):

                    state = (
                        "INVALIDATED"
                    )

                    if (
                        invalidation_time
                        is None
                    ):

                        invalidation_time = (
                            observation_time
                        )

                # -------------------------------------------------------------
                # Accepted remains accepted until invalidated.
                # -------------------------------------------------------------

                elif (
                    previous_state
                    ==
                    "ACCEPTED"
                ):

                    state = (
                        "ACCEPTED"
                    )

                # -------------------------------------------------------------
                # Acceptance requires prior/current mitigation.
                # -------------------------------------------------------------

                elif (
                    first_mitigation_time
                    is not None
                    and
                    cls._accepted(
                        direction=direction,

                        close=candle_close,

                        zone_high=zone_high,

                        zone_low=zone_low,
                    )
                ):

                    state = (
                        "ACCEPTED"
                    )

                    if (
                        acceptance_time
                        is None
                    ):

                        acceptance_time = (
                            observation_time
                        )

                # -------------------------------------------------------------
                # Otherwise mitigated after first overlap.
                # -------------------------------------------------------------

                elif (
                    first_mitigation_time
                    is not None
                ):

                    state = (
                        "MITIGATED"
                    )

                else:

                    state = (
                        "FRESH"
                    )

                age_bars = (
                    observation_position
                    -
                    confirmation_position
                )

                rows.append(
                    cls._timeline_row(
                        event_id=event_id,

                        direction=direction,

                        zone_type=zone_type,

                        zone_high=zone_high,

                        zone_low=zone_low,

                        confirmation_position=(
                            confirmation_position
                        ),

                        confirmation_time=(
                            confirmation_time
                        ),

                        observation_position=(
                            observation_position
                        ),

                        observation_time=(
                            observation_time
                        ),

                        age_bars=(
                            age_bars
                        ),

                        previous_state=(
                            previous_state
                        ),

                        state=(
                            state
                        ),

                        overlap_flag=int(
                            overlap
                        ),

                        touch_count=(
                            touch_count
                        ),

                        first_mitigation_time=(
                            first_mitigation_time
                        ),

                        acceptance_time=(
                            acceptance_time
                        ),

                        invalidation_time=(
                            invalidation_time
                        ),
                    )
                )

                # Invalidation is terminal.
                if state == "INVALIDATED":
                    break

        if not rows:
            return cls._empty_result()

        result = (
            pd.DataFrame(
                rows,
                columns=list(
                    cls.OUTPUT_COLUMNS
                ),
            )
            .sort_values(
                [
                    "izl_observation_position",
                    "izl_event_id",
                ]
            )
            .reset_index(
                drop=True
            )
        )

        return cls._normalize_result(
            result
        )

    # =========================================================================
    # Latest snapshot
    # =========================================================================

    @classmethod
    def latest_snapshot(
        cls,
        timeline: pd.DataFrame,
    ) -> pd.DataFrame:

        if timeline.empty:

            return cls._normalize_result(
                timeline
            )

        required = {
            "izl_event_id",
            "izl_observation_position",
        }

        missing = (
            required
            -
            set(
                timeline.columns
            )
        )

        if missing:

            raise ValueError(
                "Missing lifecycle timeline columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )

        result = (
            timeline
            .sort_values(
                [
                    "izl_event_id",
                    "izl_observation_position",
                ]
            )
            .drop_duplicates(
                "izl_event_id",
                keep="last",
            )
            .reset_index(
                drop=True
            )
        )

        return cls._normalize_result(
            result
        )

    # =========================================================================
    # State dashboard
    # =========================================================================

    @classmethod
    def state_distribution(
        cls,
        timeline: pd.DataFrame,
    ) -> pd.DataFrame:

        snapshot = cls.latest_snapshot(
            timeline
        )

        states = (
            "FRESH",
            "MITIGATED",
            "ACCEPTED",
            "INVALIDATED",
        )

        if snapshot.empty:

            return pd.DataFrame(
                {
                    "state": list(
                        states
                    ),

                    "count": [
                        0,
                    ] * len(
                        states
                    ),
                }
            )

        counts = (
            snapshot[
                "izl_state"
            ]
            .astype(
                str
            )
            .value_counts()
        )

        return pd.DataFrame(
            {
                "state": list(
                    states
                ),

                "count": [
                    int(
                        counts.get(
                            state,
                            0,
                        )
                    )
                    for state
                    in states
                ],
            }
        )


institutional_zone_lifecycle = (
    InstitutionalZoneLifecycle()
)