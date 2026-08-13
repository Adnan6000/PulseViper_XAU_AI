"""
===============================================================================
Module      : market_context_liquidity.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Causal Market Context & Liquidity Map
===============================================================================

Research contract
-----------------
This engine creates causal market-location metadata.

It does NOT:
- open trades
- change trade_ready
- change Confidence
- change SetupState
- change BOS
- change risk
- use future candles
- claim that a liquidity level is automatically tradable

Primary context
---------------
- Previous Day High / Low
- Previous Week High / Low
- Asia / London / New York session context
- previous same-session high / low
- current-session running high / low
- confirmed MICRO / INTERNAL / MAJOR swing levels
- nearest contextual liquidity above / below price
- distance to levels
- rolling range location

Session windows
---------------
Research definitions in UTC:

Asia       00:00 <= hour < 08:00
London     07:00 <= hour < 16:00
New York   13:00 <= hour < 22:00

These windows intentionally overlap.

They are contextual definitions, NOT claimed profitable thresholds.
"""

from __future__ import annotations

from bisect import (
    bisect_left,
    bisect_right,
    insort,
)
from typing import Any

import numpy as np
import pandas as pd


class MarketContextLiquidityMap:

    VERSION = "1.0"

    MODE = "CAUSAL_RESEARCH_METADATA_ONLY"

    REQUIRED_COLUMNS = (
        "time",
        "open",
        "high",
        "low",
        "close",
    )

    DEFAULT_SESSION_WINDOWS_UTC = {
        "asia": (
            0,
            8,
        ),

        "london": (
            7,
            16,
        ),

        "new_york": (
            13,
            22,
        ),
    }

    def __init__(
        self,
        range_lookback: int = 20,
        session_windows_utc: (
            dict[
                str,
                tuple[
                    int,
                    int,
                ],
            ]
            | None
        ) = None,
    ) -> None:

        if range_lookback <= 1:

            raise ValueError(
                "range_lookback must be greater than one"
            )

        self.range_lookback = int(
            range_lookback
        )

        self.session_windows_utc = dict(
            session_windows_utc
            if session_windows_utc is not None
            else self.DEFAULT_SESSION_WINDOWS_UTC
        )

        for (
            name,
            window,
        ) in self.session_windows_utc.items():

            if not name:

                raise ValueError(
                    "session name cannot be empty"
                )

            if len(
                window
            ) != 2:

                raise ValueError(
                    f"session {name} must contain (start_hour, end_hour)"
                )

            (
                start_hour,
                end_hour,
            ) = window

            if not (
                0
                <=
                int(
                    start_hour
                )
                <
                24
            ):

                raise ValueError(
                    f"invalid start hour for session {name}"
                )

            if not (
                0
                <
                int(
                    end_hour
                )
                <=
                24
            ):

                raise ValueError(
                    f"invalid end hour for session {name}"
                )

            if (
                int(
                    start_hour
                )
                >=
                int(
                    end_hour
                )
            ):

                raise ValueError(
                    "MarketContextLiquidityMap v1 "
                    "does not support sessions crossing midnight"
                )

    # =========================================================================
    # Validation
    # =========================================================================

    @classmethod
    def _validate(
        cls,
        data: pd.DataFrame,
    ) -> None:

        if not isinstance(
            data,
            pd.DataFrame,
        ):

            raise TypeError(
                "MarketContextLiquidityMap input "
                "must be a pandas DataFrame"
            )

        missing = (
            set(
                cls.REQUIRED_COLUMNS
            )
            -
            set(
                data.columns
            )
        )

        if missing:

            raise ValueError(
                "Missing required market-context columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )

    @staticmethod
    def _numeric(
        series: pd.Series,
    ) -> pd.Series:

        return pd.to_numeric(
            series,
            errors="coerce",
        ).astype(
            "float64"
        )

    @staticmethod
    def _scalar_float(
        value: Any,
    ) -> float:
        """
        Safely convert a pandas / numpy / Python scalar to float.

        This helper deliberately accepts Any so static analyzers do not
        propagate pandas' broad Scalar union (which includes complex) into
        float(...). Complex and invalid values are rejected as NaN.
        """

        if value is None:
            return float(
                "nan"
            )

        if isinstance(
            value,
            complex,
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

            converted = float(
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
            converted
        ):

            return float(
                "nan"
            )

        return converted

    # =========================================================================
    # Previous period levels
    # =========================================================================

    @staticmethod
    def _previous_period_levels(
        df: pd.DataFrame,
        key: pd.Series,
    ) -> tuple[
        pd.Series,
        pd.Series,
    ]:

        working = pd.DataFrame(
            {
                "_key": (
                    key.to_numpy()
                ),

                "_high": (
                    df[
                        "high"
                    ].to_numpy()
                ),

                "_low": (
                    df[
                        "low"
                    ].to_numpy()
                ),
            },
            index=df.index,
        )

        stats = (
            working
            .groupby(
                "_key",
                sort=True,
            )
            .agg(
                period_high=(
                    "_high",
                    "max",
                ),

                period_low=(
                    "_low",
                    "min",
                ),
            )
        )

        previous = stats.shift(
            1
        )

        high_map = (
            previous[
                "period_high"
            ]
            .to_dict()
        )

        low_map = (
            previous[
                "period_low"
            ]
            .to_dict()
        )

        previous_high = key.map(
            high_map
        ).astype(
            "float64"
        )

        previous_low = key.map(
            low_map
        ).astype(
            "float64"
        )

        return (
            previous_high,
            previous_low,
        )

    # =========================================================================
    # Sessions
    # =========================================================================

    def _session_columns(
        self,
        df: pd.DataFrame,
        timestamps: pd.Series,
        date_key: pd.Series,
    ) -> dict[
        str,
        pd.Series,
    ]:

        outputs: dict[
            str,
            pd.Series,
        ] = {}

        hours = (
            timestamps
            .dt
            .hour
        )

        for (
            name,
            (
                start_hour,
                end_hour,
            ),
        ) in (
            self.session_windows_utc
            .items()
        ):

            mask = (
                hours.ge(
                    start_hour
                )
                &
                hours.lt(
                    end_hour
                )
            )

            outputs[
                f"ctx_in_{name}_session"
            ] = mask.astype(
                "int8"
            )

            running_high = pd.Series(
                np.nan,
                index=df.index,
                dtype="float64",
            )

            running_low = pd.Series(
                np.nan,
                index=df.index,
                dtype="float64",
            )

            if bool(
                mask.any()
            ):

                session_high = (
                    df[
                        "high"
                    ]
                    .where(
                        mask
                    )
                )

                session_low = (
                    df[
                        "low"
                    ]
                    .where(
                        mask
                    )
                )

                running_high.loc[
                    mask
                ] = (
                    session_high.loc[
                        mask
                    ]
                    .groupby(
                        date_key.loc[
                            mask
                        ],
                        sort=False,
                    )
                    .cummax()
                    .astype(
                        "float64"
                    )
                )

                running_low.loc[
                    mask
                ] = (
                    session_low.loc[
                        mask
                    ]
                    .groupby(
                        date_key.loc[
                            mask
                        ],
                        sort=False,
                    )
                    .cummin()
                    .astype(
                        "float64"
                    )
                )

                session_rows = pd.DataFrame(
                    {
                        "_date": (
                            date_key.loc[
                                mask
                            ]
                            .to_numpy()
                        ),

                        "_high": (
                            df.loc[
                                mask,
                                "high",
                            ]
                            .to_numpy()
                        ),

                        "_low": (
                            df.loc[
                                mask,
                                "low",
                            ]
                            .to_numpy()
                        ),
                    }
                )

                stats = (
                    session_rows
                    .groupby(
                        "_date",
                        sort=True,
                    )
                    .agg(
                        high=(
                            "_high",
                            "max",
                        ),

                        low=(
                            "_low",
                            "min",
                        ),
                    )
                )

                previous = stats.shift(
                    1
                )

                previous_high = (
                    date_key
                    .map(
                        previous[
                            "high"
                        ].to_dict()
                    )
                    .astype(
                        "float64"
                    )
                )

                previous_low = (
                    date_key
                    .map(
                        previous[
                            "low"
                        ].to_dict()
                    )
                    .astype(
                        "float64"
                    )
                )

            else:

                previous_high = pd.Series(
                    np.nan,
                    index=df.index,
                    dtype="float64",
                )

                previous_low = pd.Series(
                    np.nan,
                    index=df.index,
                    dtype="float64",
                )

            outputs[
                f"ctx_{name}_running_high"
            ] = running_high

            outputs[
                f"ctx_{name}_running_low"
            ] = running_low

            outputs[
                f"ctx_prev_{name}_high"
            ] = previous_high

            outputs[
                f"ctx_prev_{name}_low"
            ] = previous_low

        return outputs

    # =========================================================================
    # Confirmed swing hierarchy
    # =========================================================================

    @staticmethod
    def _nearest_from_sorted(
        values: list[
            float
        ],
        price: float,
        side: str,
    ) -> float:

        if (
            not values
            or
            not np.isfinite(
                price
            )
        ):

            return float(
                "nan"
            )

        if side == "ABOVE":

            position = bisect_right(
                values,
                price,
            )

            if position >= len(
                values
            ):

                return float(
                    "nan"
                )

            return float(
                values[
                    position
                ]
            )

        position = (
            bisect_left(
                values,
                price,
            )
            -
            1
        )

        if position < 0:

            return float(
                "nan"
            )

        return float(
            values[
                position
            ]
        )

    def _confirmed_swing_context(
        self,
        df: pd.DataFrame,
    ) -> dict[
        str,
        np.ndarray,
    ]:

        row_count = len(
            df
        )

        outputs: dict[
            str,
            np.ndarray,
        ] = {}

        for scale in (
            "MICRO",
            "INTERNAL",
            "MAJOR",
        ):

            outputs[
                f"ctx_nearest_{scale.lower()}_high"
            ] = np.full(
                row_count,
                np.nan,
                dtype=np.float64,
            )

            outputs[
                f"ctx_nearest_{scale.lower()}_low"
            ] = np.full(
                row_count,
                np.nan,
                dtype=np.float64,
            )

        required = {
            "swing_id",
            "swing_type",
            "swing_price",
            "swing_scale",
        }

        if not required.issubset(
            df.columns
        ):

            return outputs

        known: dict[
            str,
            dict[
                str,
                list[
                    float
                ],
            ],
        ] = {
            scale: {
                "HIGH": [],
                "LOW": [],
            }

            for scale in (
                "MICRO",
                "INTERNAL",
                "MAJOR",
            )
        }

        swing_id = (
            pd.to_numeric(
                df[
                    "swing_id"
                ],
                errors="coerce",
            )
            .fillna(
                0
            )
            .to_numpy()
        )

        swing_price = (
            pd.to_numeric(
                df[
                    "swing_price"
                ],
                errors="coerce",
            )
            .to_numpy(
                dtype=float
            )
        )

        swing_type = (
            df[
                "swing_type"
            ]
            .astype(
                str
            )
            .str
            .upper()
            .to_numpy()
        )

        swing_scale = (
            df[
                "swing_scale"
            ]
            .astype(
                str
            )
            .str
            .upper()
            .to_numpy()
        )

        close = (
            df[
                "close"
            ]
            .to_numpy(
                dtype=float
            )
        )

        for i in range(
            row_count
        ):

            current_swing_id = int(
                swing_id[
                    i
                ]
            )

            current_scale = str(
                swing_scale[
                    i
                ]
            )

            current_type = str(
                swing_type[
                    i
                ]
            )

            current_swing_price = (
                float(
                    swing_price[
                        i
                    ]
                )
                if np.isfinite(
                    swing_price[
                        i
                    ]
                )
                else np.nan
            )

            # MarketStructure writes swings on the causal confirmation row.
            #
            # From this candle close onward, the swing origin price
            # is known and may be used as context.

            if (
                current_swing_id > 0
                and
                current_scale
                in known
                and
                current_type
                in (
                    "HIGH",
                    "LOW",
                )
                and
                np.isfinite(
                    current_swing_price
                )
            ):

                insort(
                    known[
                        current_scale
                    ][
                        current_type
                    ],
                    current_swing_price,
                )

            current_price = float(
                close[
                    i
                ]
            )

            for scale in (
                "MICRO",
                "INTERNAL",
                "MAJOR",
            ):

                outputs[
                    f"ctx_nearest_{scale.lower()}_high"
                ][
                    i
                ] = (
                    self._nearest_from_sorted(
                        known[
                            scale
                        ][
                            "HIGH"
                        ],
                        current_price,
                        "ABOVE",
                    )
                )

                outputs[
                    f"ctx_nearest_{scale.lower()}_low"
                ][
                    i
                ] = (
                    self._nearest_from_sorted(
                        known[
                            scale
                        ][
                            "LOW"
                        ],
                        current_price,
                        "BELOW",
                    )
                )

        return outputs

    # =========================================================================
    # Nearest combined liquidity
    # =========================================================================

    @staticmethod
    def _nearest_liquidity(
        df: pd.DataFrame,
    ) -> tuple[
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
    ]:

        high_sources = (
            (
                "PDH",
                "ctx_pdh",
            ),

            (
                "PWH",
                "ctx_pwh",
            ),

            (
                "PREV_ASIA_HIGH",
                "ctx_prev_asia_high",
            ),

            (
                "PREV_LONDON_HIGH",
                "ctx_prev_london_high",
            ),

            (
                "PREV_NEW_YORK_HIGH",
                "ctx_prev_new_york_high",
            ),

            (
                "MICRO_HIGH",
                "ctx_nearest_micro_high",
            ),

            (
                "INTERNAL_HIGH",
                "ctx_nearest_internal_high",
            ),

            (
                "MAJOR_HIGH",
                "ctx_nearest_major_high",
            ),
        )

        low_sources = (
            (
                "PDL",
                "ctx_pdl",
            ),

            (
                "PWL",
                "ctx_pwl",
            ),

            (
                "PREV_ASIA_LOW",
                "ctx_prev_asia_low",
            ),

            (
                "PREV_LONDON_LOW",
                "ctx_prev_london_low",
            ),

            (
                "PREV_NEW_YORK_LOW",
                "ctx_prev_new_york_low",
            ),

            (
                "MICRO_LOW",
                "ctx_nearest_micro_low",
            ),

            (
                "INTERNAL_LOW",
                "ctx_nearest_internal_low",
            ),

            (
                "MAJOR_LOW",
                "ctx_nearest_major_low",
            ),
        )

        row_count = len(
            df
        )

        above_price = np.full(
            row_count,
            np.nan,
            dtype=np.float64,
        )

        below_price = np.full(
            row_count,
            np.nan,
            dtype=np.float64,
        )

        above_source = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        below_source = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        close = (
            df[
                "close"
            ]
            .to_numpy(
                dtype=float
            )
        )

        for i in range(
            row_count
        ):

            current_price = float(
                close[
                    i
                ]
            )

            best_above_distance = np.inf
            best_below_distance = np.inf

            for (
                label,
                column,
            ) in high_sources:

                if column not in df.columns:
                    continue

                value = df[
                    column
                ].iat[
                    i
                ]

                if pd.isna(
                    value
                ):
                    continue

                level = (
                    MarketContextLiquidityMap
                    ._scalar_float(
                        value
                    )
                )

                if not np.isfinite(
                    level
                ):
                    continue

                distance = (
                    level
                    -
                    current_price
                )

                if (
                    distance >= 0.0
                    and
                    distance
                    <
                    best_above_distance
                ):

                    best_above_distance = (
                        distance
                    )

                    above_price[
                        i
                    ] = level

                    above_source[
                        i
                    ] = label

            for (
                label,
                column,
            ) in low_sources:

                if column not in df.columns:
                    continue

                value = df[
                    column
                ].iat[
                    i
                ]

                if pd.isna(
                    value
                ):
                    continue

                level = (
                    MarketContextLiquidityMap
                    ._scalar_float(
                        value
                    )
                )

                if not np.isfinite(
                    level
                ):
                    continue

                distance = (
                    current_price
                    -
                    level
                )

                if (
                    distance >= 0.0
                    and
                    distance
                    <
                    best_below_distance
                ):

                    best_below_distance = (
                        distance
                    )

                    below_price[
                        i
                    ] = level

                    below_source[
                        i
                    ] = label

        return (
            above_price,
            above_source,
            below_price,
            below_source,
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

        timestamps = pd.to_datetime(
            df[
                "time"
            ],
            errors="coerce",
            utc=True,
        )

        if bool(
            timestamps.isna().any()
        ):

            raise ValueError(
                "Market context requires valid timestamps"
            )

        timestamps = (
            timestamps
            .dt
            .tz_convert(
                None
            )
        )

        df[
            "time"
        ] = timestamps

        for column in (
            "open",
            "high",
            "low",
            "close",
        ):

            df[
                column
            ] = self._numeric(
                df[
                    column
                ]
            )

        valid_ohlc = (
            df[
                "high"
            ].ge(
                df[
                    "low"
                ]
            )
            &
            df[
                "high"
            ].ge(
                df[
                    "open"
                ]
            )
            &
            df[
                "high"
            ].ge(
                df[
                    "close"
                ]
            )
            &
            df[
                "low"
            ].le(
                df[
                    "open"
                ]
            )
            &
            df[
                "low"
            ].le(
                df[
                    "close"
                ]
            )
        )

        if not bool(
            valid_ohlc.all()
        ):

            raise ValueError(
                "Market context received invalid OHLC relationships"
            )

        # ---------------------------------------------------------------------
        # ATR
        # ---------------------------------------------------------------------

        if "atr" in df.columns:

            atr = self._numeric(
                df[
                    "atr"
                ]
            )

        else:

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

            atr = (
                true_range
                .rolling(
                    window=14,
                    min_periods=1,
                )
                .mean()
                .astype(
                    "float64"
                )
            )

        # ---------------------------------------------------------------------
        # Calendar keys
        # ---------------------------------------------------------------------

        date_key = (
            timestamps
            .dt
            .floor(
                "D"
            )
        )

        week_key = (
            timestamps
            .dt
            .to_period(
                "W-SUN"
            )
            .dt
            .start_time
        )

        # ---------------------------------------------------------------------
        # Previous day / previous week
        # ---------------------------------------------------------------------

        (
            pdh,
            pdl,
        ) = self._previous_period_levels(
            df,
            date_key,
        )

        (
            pwh,
            pwl,
        ) = self._previous_period_levels(
            df,
            week_key,
        )

        context: dict[
            str,
            Any,
        ] = {
            "ctx_pdh": pdh,
            "ctx_pdl": pdl,
            "ctx_pwh": pwh,
            "ctx_pwl": pwl,
        }

        # ---------------------------------------------------------------------
        # Session context
        # ---------------------------------------------------------------------

        context.update(
            self._session_columns(
                df,
                timestamps,
                date_key,
            )
        )

        # ---------------------------------------------------------------------
        # Confirmed swing hierarchy
        # ---------------------------------------------------------------------

        swing_context = (
            self._confirmed_swing_context(
                df
            )
        )

        context.update(
            swing_context
        )

        result = pd.concat(
            [
                df,

                pd.DataFrame(
                    context,
                    index=df.index,
                ),
            ],
            axis=1,
        )

        # ---------------------------------------------------------------------
        # Day/week distances
        #
        # Positive distance = level above price.
        # Negative distance = level below price.
        # ---------------------------------------------------------------------

        close = result[
            "close"
        ]

        result[
            "ctx_distance_to_pdh"
        ] = (
            result[
                "ctx_pdh"
            ]
            -
            close
        )

        result[
            "ctx_distance_to_pdl"
        ] = (
            result[
                "ctx_pdl"
            ]
            -
            close
        )

        result[
            "ctx_distance_to_pwh"
        ] = (
            result[
                "ctx_pwh"
            ]
            -
            close
        )

        result[
            "ctx_distance_to_pwl"
        ] = (
            result[
                "ctx_pwl"
            ]
            -
            close
        )

        safe_atr = atr.where(
            atr > 0.0
        )

        for name in (
            "pdh",
            "pdl",
            "pwh",
            "pwl",
        ):

            result[
                f"ctx_atr_distance_to_{name}"
            ] = (
                result[
                    f"ctx_distance_to_{name}"
                ]
                /
                safe_atr
            )

        # ---------------------------------------------------------------------
        # Rolling range location
        # ---------------------------------------------------------------------

        rolling_high = (
            result[
                "high"
            ]
            .rolling(
                window=self.range_lookback,
                min_periods=2,
            )
            .max()
        )

        rolling_low = (
            result[
                "low"
            ]
            .rolling(
                window=self.range_lookback,
                min_periods=2,
            )
            .min()
        )

        range_width = (
            rolling_high
            -
            rolling_low
        ).replace(
            0.0,
            np.nan,
        )

        range_position = (
            (
                close
                -
                rolling_low
            )
            /
            range_width
        ).clip(
            0.0,
            1.0,
        )

        result[
            "ctx_range_high"
        ] = rolling_high

        result[
            "ctx_range_low"
        ] = rolling_low

        result[
            "ctx_range_position"
        ] = range_position

        result[
            "ctx_range_zone"
        ] = np.select(
            [
                range_position.le(
                    0.25
                ),

                range_position.ge(
                    0.75
                ),

                range_position.notna(),
            ],
            [
                "LOWER_EDGE",
                "UPPER_EDGE",
                "MIDDLE",
            ],
            default="UNKNOWN",
        )

        # ---------------------------------------------------------------------
        # Nearest contextual liquidity
        # ---------------------------------------------------------------------

        (
            above_price,
            above_source,
            below_price,
            below_source,
        ) = self._nearest_liquidity(
            result
        )

        result[
            "ctx_nearest_liquidity_above"
        ] = above_price

        result[
            "ctx_nearest_liquidity_above_source"
        ] = above_source

        result[
            "ctx_nearest_liquidity_below"
        ] = below_price

        result[
            "ctx_nearest_liquidity_below_source"
        ] = below_source

        result[
            "ctx_nearest_liquidity_above_distance"
        ] = (
            above_price
            -
            close.to_numpy(
                dtype=float
            )
        )

        result[
            "ctx_nearest_liquidity_below_distance"
        ] = (
            close.to_numpy(
                dtype=float
            )
            -
            below_price
        )

        atr_array = safe_atr.to_numpy(
            dtype=float
        )

        result[
            "ctx_nearest_liquidity_above_atr"
        ] = (
            result[
                "ctx_nearest_liquidity_above_distance"
            ]
            .to_numpy(
                dtype=float
            )
            /
            atr_array
        )

        result[
            "ctx_nearest_liquidity_below_atr"
        ] = (
            result[
                "ctx_nearest_liquidity_below_distance"
            ]
            .to_numpy(
                dtype=float
            )
            /
            atr_array
        )

        # ---------------------------------------------------------------------
        # Metadata
        # ---------------------------------------------------------------------

        result[
            "ctx_version"
        ] = self.VERSION

        result[
            "ctx_mode"
        ] = self.MODE

        return result


market_context_liquidity = (
    MarketContextLiquidityMap()
)