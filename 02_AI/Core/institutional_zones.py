"""
===============================================================================
Module      : institutional_zones.py
Project     : PulseViper XAU AI
Version     : 2.0
Purpose     : Institutional Zone / Order-Block Proxy Engine
===============================================================================

Architecture
------------
This module supports TWO explicitly separated modes.

1. Causal mode
   generate()
   generate_causal()

   - uses only information available through the confirmation candle
   - emits the zone on the CONFIRMATION candle
   - preserves origin-candle metadata separately
   - no future candles
   - no global future-dependent merging or ranking
   - safe for shadow research metadata

2. Retrospective research mode
   detect()
   generate_research()

   - legacy lookahead detector
   - can inspect later candles
   - NOT live safe
   - generate_research() prefixes every output with izlabel_ so hindsight
     labels cannot silently enter the causal chain

Important
---------
These zones are price-action proxies. They do not prove institutional orders.

This module:
- does not open trades
- does not modify trade_ready
- does not calculate account risk
- does not size positions
- does not authorize BUY / SELL execution
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import math

import pandas as pd


# =============================================================================
# DATA MODEL
# =============================================================================


@dataclass(frozen=True)
class InstitutionalZone:
    """Immutable representation of an institutional-style price zone."""

    zone_id: int

    direction: str
    zone_type: str

    index: Any

    high: float
    low: float
    midpoint: float
    size: float

    candle_open: float
    candle_close: float
    candle_high: float
    candle_low: float

    body_ratio: float
    displacement_score: float
    strength: float

    active: bool = True

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return asdict(
            self
        )


# =============================================================================
# ENGINE
# =============================================================================


class InstitutionalZonesEngine:
    """
    Detect institutional-style supply / demand zone proxies.

    Causal contract
    ---------------
    A zone origin is NOT exposed at the origin candle.

    It becomes observable only when sufficient displacement has actually
    occurred on a later confirmation candle.

    Example:

        origin candle
            ↓
        next candle
            ↓
        displacement reaches threshold
            ↓
        causal zone event emitted HERE

    Therefore an earlier dataframe prefix must always produce the same earlier
    causal events as a longer dataframe containing additional future candles.
    """

    VERSION = "2.0"

    CAUSAL_MODE = "CAUSAL_CONFIRMATION_EVENT_ONLY"

    RESEARCH_MODE = "RETROSPECTIVE_LOOKAHEAD_LABEL_ONLY"

    REQUIRED_COLUMNS = (
        "open",
        "high",
        "low",
        "close",
    )

    OPTIONAL_COLUMNS = (
        "time",
        "volume",
        "atr",
    )

    DEFAULT_CONFIG = {
        "min_body_ratio": 0.25,

        "min_displacement_score": 55.0,

        "min_zone_size": 0.0,

        "max_zone_size_atr": 3.0,

        # In retrospective mode this is lookahead.
        #
        # In causal mode this becomes the maximum allowed number of bars
        # between origin and confirmation.
        "lookahead": 3,

        "min_strength": 0.0,

        # Retrospective detect() only.
        "merge_overlapping": True,

        # Retrospective detect() only.
        "max_zones": 100,
    }

    # -------------------------------------------------------------------------
    # Legacy retrospective output
    # -------------------------------------------------------------------------

    OUTPUT_COLUMNS = (
        "zone_id",

        "direction",
        "zone_type",

        "index",

        "high",
        "low",
        "midpoint",
        "size",

        "candle_open",
        "candle_close",
        "candle_high",
        "candle_low",

        "body_ratio",
        "displacement_score",
        "strength",

        "active",
    )

    # -------------------------------------------------------------------------
    # Causal event output
    # -------------------------------------------------------------------------

    CAUSAL_OUTPUT_COLUMNS = (
        "iz_event_id",
        "iz_event_flag",

        "iz_direction",
        "iz_zone_type",

        "iz_origin_position",
        "iz_confirmation_position",

        "iz_origin_index",
        "iz_confirmation_index",

        "iz_origin_time",
        "iz_confirmation_time",

        "iz_zone_high",
        "iz_zone_low",
        "iz_zone_midpoint",
        "iz_zone_size",

        "iz_origin_open",
        "iz_origin_close",
        "iz_origin_high",
        "iz_origin_low",

        "iz_body_ratio",
        "iz_displacement_score",
        "iz_strength",

        "iz_confirmation_delay_bars",

        "iz_live_safe",
        "iz_version",
        "iz_mode",
    )

    def __init__(
        self,
        config: Optional[
            Dict[str, Any]
        ] = None,
    ) -> None:

        self.config = (
            self.DEFAULT_CONFIG.copy()
        )

        if config:
            self.config.update(
                config
            )

        self._validate_config()

    # =========================================================================
    # PUBLIC API — CAUSAL
    # =========================================================================

    def generate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Primary safe interface.

        Equivalent to generate_causal().
        """

        return self.generate_causal(
            data
        )

    def generate_causal(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Generate causal zone-confirmation events.

        Rules
        -----
        - origin candle is historical relative to confirmation
        - only candles <= current confirmation candle are inspected
        - each origin can confirm at most once
        - confirmation is emitted at earliest valid causal point
        - no retrospective merging
        - no global strength ranking
        - no max_zones future-dependent truncation
        """

        df = self._prepare_dataframe(
            data
        )

        if len(
            df
        ) < 2:

            return self._empty_causal_result()

        lookahead = int(
            self.config[
                "lookahead"
            ]
        )

        confirmed_origins: set[
            int
        ] = set()

        events: list[
            dict[
                str,
                Any,
            ]
        ] = []

        # Confirmation moves strictly left -> right.
        for confirmation_position in range(
            1,
            len(
                df
            ),
        ):

            earliest_origin = max(
                0,
                confirmation_position
                -
                lookahead,
            )

            for origin_position in range(
                earliest_origin,
                confirmation_position,
            ):

                if (
                    origin_position
                    in confirmed_origins
                ):
                    continue

                zone = (
                    self._detect_origin_until_confirmation(
                        df=df,
                        origin_position=origin_position,
                        confirmation_position=confirmation_position,
                    )
                )

                if zone is None:
                    continue

                event = self._build_causal_event(
                    df=df,
                    zone=zone,
                    origin_position=origin_position,
                    confirmation_position=confirmation_position,
                )

                if event is None:
                    continue

                events.append(
                    event
                )

                # Earliest confirmation wins.
                confirmed_origins.add(
                    origin_position
                )

        if not events:
            return self._empty_causal_result()

        return pd.DataFrame(
            events,
            columns=list(
                self.CAUSAL_OUTPUT_COLUMNS
            ),
        ).reset_index(
            drop=True
        )

    # =========================================================================
    # PUBLIC API — RETROSPECTIVE RESEARCH
    # =========================================================================

    def detect(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Legacy retrospective detector.

        WARNING
        -------
        This function intentionally uses future candles according to
        config["lookahead"].

        It is research / hindsight functionality and must NOT be attached
        directly to the live-safe causal research chain.
        """

        df = self._prepare_dataframe(
            data
        )

        if df.empty:
            return self._empty_result()

        zones: List[
            InstitutionalZone
        ] = []

        for position in range(
            len(
                df
            )
            -
            1
        ):

            zone = self._detect_at_position(
                df,
                position,
            )

            if zone is not None:
                zones.append(
                    zone
                )

        if not zones:
            return self._empty_result()

        if bool(
            self.config[
                "merge_overlapping"
            ]
        ):

            zones = (
                self._merge_overlapping_zones(
                    zones
                )
            )

        # Retrospective ranking is allowed here because this path is explicitly
        # labeled hindsight research.
        zones.sort(
            key=lambda zone: (
                -zone.strength,
                zone.zone_id,
            )
        )

        max_zones = int(
            self.config[
                "max_zones"
            ]
        )

        if max_zones > 0:
            zones = zones[
                :max_zones
            ]

        return pd.DataFrame(
            [
                zone.to_dict()
                for zone in zones
            ],
            columns=list(
                self.OUTPUT_COLUMNS
            ),
        )

    def generate_research(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Generate explicit hindsight labels.

        Every column starts with izlabel_.

        These outputs must never be attached to a live-safe chain.
        """

        result = self.detect(
            data
        )

        renamed_columns = {
            column: (
                f"izlabel_{column}"
            )
            for column
            in self.OUTPUT_COLUMNS
        }

        result = result.rename(
            columns=renamed_columns
        )

        result[
            "izlabel_version"
        ] = self.VERSION

        result[
            "izlabel_mode"
        ] = self.RESEARCH_MODE

        result[
            "izlabel_live_safe"
        ] = 0

        return result

    # =========================================================================
    # CONFIG VALIDATION
    # =========================================================================

    def _validate_config(
        self,
    ) -> None:

        min_body_ratio = float(
            self.config[
                "min_body_ratio"
            ]
        )

        min_displacement_score = float(
            self.config[
                "min_displacement_score"
            ]
        )

        min_zone_size = float(
            self.config[
                "min_zone_size"
            ]
        )

        max_zone_size_atr = float(
            self.config[
                "max_zone_size_atr"
            ]
        )

        lookahead = int(
            self.config[
                "lookahead"
            ]
        )

        min_strength = float(
            self.config[
                "min_strength"
            ]
        )

        max_zones = int(
            self.config[
                "max_zones"
            ]
        )

        if not (
            0.0
            <=
            min_body_ratio
            <=
            1.0
        ):

            raise ValueError(
                "min_body_ratio must be between 0 and 1."
            )

        if min_displacement_score < 0.0:

            raise ValueError(
                "min_displacement_score cannot be negative."
            )

        if min_zone_size < 0.0:

            raise ValueError(
                "min_zone_size cannot be negative."
            )

        if max_zone_size_atr <= 0.0:

            raise ValueError(
                "max_zone_size_atr must be greater than zero."
            )

        if lookahead < 1:

            raise ValueError(
                "lookahead must be at least 1."
            )

        if min_strength < 0.0:

            raise ValueError(
                "min_strength cannot be negative."
            )

        if max_zones < 0:

            raise ValueError(
                "max_zones cannot be negative."
            )

    @classmethod
    def _ensure_columns(
        cls,
        data: pd.DataFrame,
    ) -> None:

        if not isinstance(
            data,
            pd.DataFrame,
        ):

            raise TypeError(
                "data must be a pandas DataFrame."
            )

        if not data.columns.is_unique:

            raise ValueError(
                "data contains duplicate column names."
            )

        missing = [
            column
            for column
            in cls.REQUIRED_COLUMNS
            if column
            not in data.columns
        ]

        if missing:

            raise ValueError(
                "Missing required OHLC columns: "
                f"{missing}"
            )

    # =========================================================================
    # DATA PREPARATION
    # =========================================================================

    def _prepare_dataframe(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        self._ensure_columns(
            data
        )

        df = data.copy(
            deep=True
        )

        # Preserve original identity before any validation/filtering.
        df[
            "_iz_source_position"
        ] = range(
            len(
                df
            )
        )

        df[
            "_iz_source_index"
        ] = list(
            data.index
        )

        for column in self.REQUIRED_COLUMNS:

            df[
                column
            ] = pd.to_numeric(
                df[
                    column
                ],
                errors="coerce",
            )

        df = df.dropna(
            subset=list(
                self.REQUIRED_COLUMNS
            )
        )

        if df.empty:
            return df

        valid_ohlc = (
            (
                df[
                    "high"
                ]
                >=
                df[
                    "low"
                ]
            )
            &
            (
                df[
                    "high"
                ]
                >=
                df[
                    "open"
                ]
            )
            &
            (
                df[
                    "high"
                ]
                >=
                df[
                    "close"
                ]
            )
            &
            (
                df[
                    "low"
                ]
                <=
                df[
                    "open"
                ]
            )
            &
            (
                df[
                    "low"
                ]
                <=
                df[
                    "close"
                ]
            )
        )

        df = df.loc[
            valid_ohlc
        ].copy()

        if df.empty:
            return df

        if "atr" in df.columns:

            df[
                "atr"
            ] = pd.to_numeric(
                df[
                    "atr"
                ],
                errors="coerce",
            )

        else:

            df[
                "atr"
            ] = self._calculate_atr(
                df
            )

        df[
            "atr"
        ] = df[
            "atr"
        ].replace(
            [
                math.inf,
                -math.inf,
            ],
            math.nan,
        )

        fallback_atr = (
            (
                df[
                    "high"
                ]
                -
                df[
                    "low"
                ]
            )
            .rolling(
                window=14,
                min_periods=1,
            )
            .mean()
        )

        df[
            "atr"
        ] = (
            df[
                "atr"
            ]
            .fillna(
                fallback_atr
            )
            .replace(
                0.0,
                math.nan,
            )
        )

        return df.reset_index(
            drop=True
        )

    @staticmethod
    def _calculate_atr(
        df: pd.DataFrame,
        period: int = 14,
    ) -> pd.Series:

        previous_close = (
            df[
                "close"
            ]
            .shift(
                1
            )
        )

        true_range = pd.concat(
            [
                (
                    df[
                        "high"
                    ]
                    -
                    df[
                        "low"
                    ]
                ),

                (
                    df[
                        "high"
                    ]
                    -
                    previous_close
                ).abs(),

                (
                    df[
                        "low"
                    ]
                    -
                    previous_close
                ).abs(),
            ],
            axis=1,
        ).max(
            axis=1
        )

        return true_range.rolling(
            window=period,
            min_periods=1,
        ).mean()

    # =========================================================================
    # RETROSPECTIVE DETECTION
    # =========================================================================

    def _detect_at_position(
        self,
        df: pd.DataFrame,
        position: int,
    ) -> Optional[
        InstitutionalZone
    ]:

        lookahead = int(
            self.config[
                "lookahead"
            ]
        )

        future_end = min(
            position
            +
            1
            +
            lookahead,
            len(
                df
            ),
        )

        confirmation_position = (
            future_end
            -
            1
        )

        if (
            confirmation_position
            <=
            position
        ):
            return None

        return (
            self._detect_origin_until_confirmation(
                df=df,
                origin_position=position,
                confirmation_position=confirmation_position,
            )
        )

    # =========================================================================
    # SHARED ORIGIN DETECTION
    # =========================================================================

    def _detect_origin_until_confirmation(
        self,
        df: pd.DataFrame,
        origin_position: int,
        confirmation_position: int,
    ) -> Optional[
        InstitutionalZone
    ]:

        if origin_position < 0:
            return None

        if confirmation_position >= len(
            df
        ):
            return None

        if (
            confirmation_position
            <=
            origin_position
        ):
            return None

        if (
            confirmation_position
            -
            origin_position
            >
            int(
                self.config[
                    "lookahead"
                ]
            )
        ):
            return None

        candle = df.iloc[
            origin_position
        ]

        candle_open = self._safe_float(
            candle[
                "open"
            ]
        )

        candle_high = self._safe_float(
            candle[
                "high"
            ]
        )

        candle_low = self._safe_float(
            candle[
                "low"
            ]
        )

        candle_close = self._safe_float(
            candle[
                "close"
            ]
        )

        atr = self._safe_float(
            candle[
                "atr"
            ]
        )

        if any(
            value is None
            for value in (
                candle_open,
                candle_high,
                candle_low,
                candle_close,
            )
        ):
            return None

        assert candle_open is not None
        assert candle_high is not None
        assert candle_low is not None
        assert candle_close is not None

        if candle_high <= candle_low:
            return None

        body = abs(
            candle_close
            -
            candle_open
        )

        range_size = (
            candle_high
            -
            candle_low
        )

        if range_size <= 0.0:
            return None

        body_ratio = (
            body
            /
            range_size
        )

        if (
            body_ratio
            <
            float(
                self.config[
                    "min_body_ratio"
                ]
            )
        ):
            return None

        future = df.iloc[
            origin_position + 1
            :
            confirmation_position + 1
        ]

        if future.empty:
            return None

        # ---------------------------------------------------------------------
        # Bullish demand / bullish OB-style proxy
        # ---------------------------------------------------------------------

        if candle_close < candle_open:

            bullish_displacement = (
                self._bullish_displacement(
                    future=future,
                    reference_high=candle_high,
                    reference_close=candle_close,
                    atr=atr,
                )
            )

            if (
                bullish_displacement
                is not None
                and
                bullish_displacement
                >=
                float(
                    self.config[
                        "min_displacement_score"
                    ]
                )
            ):

                return self._build_zone(
                    df=df,
                    position=origin_position,
                    direction="BULLISH",
                    zone_type="DEMAND",
                    high=candle_open,
                    low=candle_low,
                    body_ratio=body_ratio,
                    displacement_score=(
                        bullish_displacement
                    ),
                )

        # ---------------------------------------------------------------------
        # Bearish supply / bearish OB-style proxy
        # ---------------------------------------------------------------------

        if candle_close > candle_open:

            bearish_displacement = (
                self._bearish_displacement(
                    future=future,
                    reference_low=candle_low,
                    reference_close=candle_close,
                    atr=atr,
                )
            )

            if (
                bearish_displacement
                is not None
                and
                bearish_displacement
                >=
                float(
                    self.config[
                        "min_displacement_score"
                    ]
                )
            ):

                return self._build_zone(
                    df=df,
                    position=origin_position,
                    direction="BEARISH",
                    zone_type="SUPPLY",
                    high=candle_high,
                    low=candle_open,
                    body_ratio=body_ratio,
                    displacement_score=(
                        bearish_displacement
                    ),
                )

        return None

    # =========================================================================
    # DISPLACEMENT
    # =========================================================================

    @classmethod
    def _bullish_displacement(
        cls,
        future: pd.DataFrame,
        reference_high: float,
        reference_close: float,
        atr: Optional[
            float
        ],
    ) -> Optional[
        float
    ]:

        max_close = cls._safe_float(
            future[
                "close"
            ].max()
        )

        max_high = cls._safe_float(
            future[
                "high"
            ].max()
        )

        if (
            max_close is None
            or
            max_high is None
        ):
            return None

        move = (
            max_close
            -
            reference_close
        )

        if move <= 0.0:
            return 0.0

        breakout = (
            100.0
            if (
                max_high
                >
                reference_high
            )
            else
            0.0
        )

        atr_component = (
            cls._atr_displacement_score(
                move,
                atr,
            )
        )

        return min(
            100.0,
            (
                atr_component
                *
                0.70
            )
            +
            (
                breakout
                *
                0.30
            ),
        )

    @classmethod
    def _bearish_displacement(
        cls,
        future: pd.DataFrame,
        reference_low: float,
        reference_close: float,
        atr: Optional[
            float
        ],
    ) -> Optional[
        float
    ]:

        min_close = cls._safe_float(
            future[
                "close"
            ].min()
        )

        min_low = cls._safe_float(
            future[
                "low"
            ].min()
        )

        if (
            min_close is None
            or
            min_low is None
        ):
            return None

        move = (
            reference_close
            -
            min_close
        )

        if move <= 0.0:
            return 0.0

        breakout = (
            100.0
            if (
                min_low
                <
                reference_low
            )
            else
            0.0
        )

        atr_component = (
            cls._atr_displacement_score(
                move,
                atr,
            )
        )

        return min(
            100.0,
            (
                atr_component
                *
                0.70
            )
            +
            (
                breakout
                *
                0.30
            ),
        )

    @staticmethod
    def _atr_displacement_score(
        move: float,
        atr: Optional[
            float
        ],
    ) -> float:

        if (
            atr is None
            or
            atr <= 0.0
        ):

            return min(
                100.0,
                max(
                    0.0,
                    move
                    *
                    100.0,
                ),
            )

        ratio = (
            move
            /
            atr
        )

        return min(
            100.0,
            max(
                0.0,
                ratio
                *
                50.0,
            ),
        )

    # =========================================================================
    # ZONE CONSTRUCTION
    # =========================================================================

    def _build_zone(
        self,
        df: pd.DataFrame,
        position: int,
        direction: str,
        zone_type: str,
        high: float,
        low: float,
        body_ratio: float,
        displacement_score: float,
    ) -> Optional[
        InstitutionalZone
    ]:

        if not math.isfinite(
            high
        ):
            return None

        if not math.isfinite(
            low
        ):
            return None

        if high <= low:
            return None

        size = (
            high
            -
            low
        )

        min_size = float(
            self.config[
                "min_zone_size"
            ]
        )

        if size < min_size:
            return None

        candle = df.iloc[
            position
        ]

        atr = self._safe_float(
            candle[
                "atr"
            ]
        )

        max_zone_size_atr = float(
            self.config[
                "max_zone_size_atr"
            ]
        )

        if (
            atr is not None
            and
            atr > 0.0
            and
            (
                size
                /
                atr
            )
            >
            max_zone_size_atr
        ):

            return None

        strength = (
            self._calculate_strength(
                body_ratio=body_ratio,
                displacement_score=displacement_score,
                zone_size=size,
                atr=atr,
            )
        )

        if (
            strength
            <
            float(
                self.config[
                    "min_strength"
                ]
            )
        ):
            return None

        candle_open = self._safe_float(
            candle[
                "open"
            ]
        )

        candle_close = self._safe_float(
            candle[
                "close"
            ]
        )

        candle_high = self._safe_float(
            candle[
                "high"
            ]
        )

        candle_low = self._safe_float(
            candle[
                "low"
            ]
        )

        if any(
            value is None
            for value in (
                candle_open,
                candle_close,
                candle_high,
                candle_low,
            )
        ):
            return None

        assert candle_open is not None
        assert candle_close is not None
        assert candle_high is not None
        assert candle_low is not None

        source_position = int(
            candle[
                "_iz_source_position"
            ]
        )

        source_index = candle[
            "_iz_source_index"
        ]

        return InstitutionalZone(
            zone_id=source_position,

            direction=direction,
            zone_type=zone_type,

            index=source_index,

            high=float(
                high
            ),

            low=float(
                low
            ),

            midpoint=float(
                (
                    high
                    +
                    low
                )
                /
                2.0
            ),

            size=float(
                size
            ),

            candle_open=float(
                candle_open
            ),

            candle_close=float(
                candle_close
            ),

            candle_high=float(
                candle_high
            ),

            candle_low=float(
                candle_low
            ),

            body_ratio=float(
                body_ratio
            ),

            displacement_score=float(
                displacement_score
            ),

            strength=float(
                strength
            ),

            active=True,
        )

    @staticmethod
    def _calculate_strength(
        body_ratio: float,
        displacement_score: float,
        zone_size: float,
        atr: Optional[
            float
        ],
    ) -> float:

        body_component = min(
            100.0,
            max(
                0.0,
                body_ratio
                *
                100.0,
            ),
        )

        if (
            atr is not None
            and
            atr > 0.0
        ):

            size_ratio = (
                zone_size
                /
                atr
            )

            size_component = max(
                0.0,
                100.0
                -
                (
                    size_ratio
                    *
                    25.0
                ),
            )

        else:

            size_component = 50.0

        score = (
            body_component
            *
            0.30
            +
            displacement_score
            *
            0.55
            +
            size_component
            *
            0.15
        )

        return min(
            100.0,
            max(
                0.0,
                score,
            ),
        )

    # =========================================================================
    # CAUSAL EVENT CONSTRUCTION
    # =========================================================================

    def _build_causal_event(
        self,
        df: pd.DataFrame,
        zone: InstitutionalZone,
        origin_position: int,
        confirmation_position: int,
    ) -> Optional[
        dict[
            str,
            Any,
        ]
    ]:

        origin = df.iloc[
            origin_position
        ]

        confirmation = df.iloc[
            confirmation_position
        ]

        origin_source_position = int(
            origin[
                "_iz_source_position"
            ]
        )

        confirmation_source_position = int(
            confirmation[
                "_iz_source_position"
            ]
        )

        origin_index = origin[
            "_iz_source_index"
        ]

        confirmation_index = confirmation[
            "_iz_source_index"
        ]

        origin_time = self._safe_timestamp(
            origin.get(
                "time"
            )
        )

        confirmation_time = self._safe_timestamp(
            confirmation.get(
                "time"
            )
        )

        delay = (
            confirmation_source_position
            -
            origin_source_position
        )

        if delay < 1:
            return None

        event_id = (
            "IZ-"
            f"{zone.direction}-"
            f"{origin_source_position}-"
            f"{confirmation_source_position}"
        )

        return {
            "iz_event_id": event_id,

            "iz_event_flag": 1,

            "iz_direction": (
                zone.direction
            ),

            "iz_zone_type": (
                zone.zone_type
            ),

            "iz_origin_position": (
                origin_source_position
            ),

            "iz_confirmation_position": (
                confirmation_source_position
            ),

            "iz_origin_index": (
                origin_index
            ),

            "iz_confirmation_index": (
                confirmation_index
            ),

            "iz_origin_time": (
                origin_time
            ),

            "iz_confirmation_time": (
                confirmation_time
            ),

            "iz_zone_high": (
                zone.high
            ),

            "iz_zone_low": (
                zone.low
            ),

            "iz_zone_midpoint": (
                zone.midpoint
            ),

            "iz_zone_size": (
                zone.size
            ),

            "iz_origin_open": (
                zone.candle_open
            ),

            "iz_origin_close": (
                zone.candle_close
            ),

            "iz_origin_high": (
                zone.candle_high
            ),

            "iz_origin_low": (
                zone.candle_low
            ),

            "iz_body_ratio": (
                zone.body_ratio
            ),

            "iz_displacement_score": (
                zone.displacement_score
            ),

            "iz_strength": (
                zone.strength
            ),

            "iz_confirmation_delay_bars": (
                delay
            ),

            "iz_live_safe": 1,

            "iz_version": (
                self.VERSION
            ),

            "iz_mode": (
                self.CAUSAL_MODE
            ),
        }

    # =========================================================================
    # RETROSPECTIVE MERGING
    # =========================================================================

    def _merge_overlapping_zones(
        self,
        zones: List[
            InstitutionalZone
        ],
    ) -> List[
        InstitutionalZone
    ]:

        if len(
            zones
        ) < 2:
            return zones

        ordered = sorted(
            zones,
            key=lambda zone: (
                zone.direction,
                zone.low,
                zone.high,
            ),
        )

        merged: List[
            InstitutionalZone
        ] = []

        for zone in ordered:

            if not merged:

                merged.append(
                    zone
                )

                continue

            previous = merged[
                -1
            ]

            if (
                previous.direction
                ==
                zone.direction
                and
                self._zones_overlap(
                    previous,
                    zone,
                )
            ):

                merged[
                    -1
                ] = (
                    self._merge_two_zones(
                        previous,
                        zone,
                    )
                )

            else:

                merged.append(
                    zone
                )

        return merged

    @staticmethod
    def _zones_overlap(
        first: InstitutionalZone,
        second: InstitutionalZone,
    ) -> bool:

        return (
            first.low
            <=
            second.high
            and
            second.low
            <=
            first.high
        )

    @staticmethod
    def _merge_two_zones(
        first: InstitutionalZone,
        second: InstitutionalZone,
    ) -> InstitutionalZone:

        high = max(
            first.high,
            second.high,
        )

        low = min(
            first.low,
            second.low,
        )

        return InstitutionalZone(
            zone_id=min(
                first.zone_id,
                second.zone_id,
            ),

            direction=(
                first.direction
            ),

            zone_type=(
                first.zone_type
            ),

            index=(
                first.index
            ),

            high=float(
                high
            ),

            low=float(
                low
            ),

            midpoint=float(
                (
                    high
                    +
                    low
                )
                /
                2.0
            ),

            size=float(
                high
                -
                low
            ),

            candle_open=(
                first.candle_open
            ),

            candle_close=(
                first.candle_close
            ),

            candle_high=max(
                first.candle_high,
                second.candle_high,
            ),

            candle_low=min(
                first.candle_low,
                second.candle_low,
            ),

            body_ratio=max(
                first.body_ratio,
                second.body_ratio,
            ),

            displacement_score=max(
                first.displacement_score,
                second.displacement_score,
            ),

            strength=max(
                first.strength,
                second.strength,
            ),

            active=(
                first.active
                and
                second.active
            ),
        )

    # =========================================================================
    # HELPERS
    # =========================================================================

    @staticmethod
    def _safe_float(
        value: Any,
    ) -> Optional[
        float
    ]:

        try:

            if value is None:
                return None

            number = float(
                value
            )

            if not math.isfinite(
                number
            ):
                return None

            return number

        except (
            TypeError,
            ValueError,
        ):

            return None

    @staticmethod
    def _safe_timestamp(
        value: Any,
    ) -> Optional[
        pd.Timestamp
    ]:

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

    @classmethod
    def _empty_result(
        cls,
    ) -> pd.DataFrame:

        return pd.DataFrame(
            columns=list(
                cls.OUTPUT_COLUMNS
            )
        )

    @classmethod
    def _empty_causal_result(
        cls,
    ) -> pd.DataFrame:

        return pd.DataFrame(
            columns=list(
                cls.CAUSAL_OUTPUT_COLUMNS
            )
        )


# =============================================================================
# MODULE SINGLETON
# =============================================================================


institutional_zones = (
    InstitutionalZonesEngine()
)


__all__ = [
    "InstitutionalZone",
    "InstitutionalZonesEngine",
    "institutional_zones",
]