"""
===============================================================================
Module      : candle_swing_intelligence.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Causal Candle Anatomy + Research Swing-Origin Intelligence
===============================================================================

Architecture
------------
This module has TWO deliberately separated paths:

1. generate(data)
   Produces CAUSAL candle/anatomy/context features only.
   Safe for shadow/live feature generation at candle close.

2. generate_research(data)
   Calls generate(data), then attaches RETROSPECTIVE swing-origin labels using
   already-confirmed MarketStructure swing metadata.

Research labels are NOT live features.

A swing confirmed in the future may label its historical origin candle for
supervised research, but generate() never writes future-confirmed information
back into the past.

The module does NOT:
- open trades
- modify trade_ready
- modify Confidence
- modify SetupState
- modify BOS
- modify risk
- predict guaranteed reversals
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class CandleSwingIntelligence:
    VERSION = "1.0"

    MODE = (
        "CAUSAL_FEATURES_WITH_SEPARATE_RESEARCH_LABELS"
    )

    REQUIRED_COLUMNS = (
        "open",
        "high",
        "low",
        "close",
    )

    def __init__(
        self,
        doji_body_ratio: float = 0.10,
        rejection_wick_body_multiple: float = 2.0,
        rejection_min_wick_ratio: float = 0.50,
        displacement_min_body_ratio: float = 0.60,
        displacement_min_range_atr: float = 0.80,
        close_extreme_threshold: float = 0.70,
    ) -> None:

        if not (
            0.0
            <= doji_body_ratio
            <= 1.0
        ):
            raise ValueError(
                "doji_body_ratio must be between 0 and 1"
            )

        if (
            rejection_wick_body_multiple
            <
            0.0
        ):
            raise ValueError(
                "rejection_wick_body_multiple "
                "cannot be negative"
            )

        if not (
            0.0
            <= rejection_min_wick_ratio
            <= 1.0
        ):
            raise ValueError(
                "rejection_min_wick_ratio "
                "must be between 0 and 1"
            )

        if not (
            0.0
            <= displacement_min_body_ratio
            <= 1.0
        ):
            raise ValueError(
                "displacement_min_body_ratio "
                "must be between 0 and 1"
            )

        if (
            displacement_min_range_atr
            <
            0.0
        ):
            raise ValueError(
                "displacement_min_range_atr "
                "cannot be negative"
            )

        if not (
            0.5
            <= close_extreme_threshold
            <= 1.0
        ):
            raise ValueError(
                "close_extreme_threshold "
                "must be between 0.5 and 1"
            )

        self.doji_body_ratio = float(
            doji_body_ratio
        )

        self.rejection_wick_body_multiple = float(
            rejection_wick_body_multiple
        )

        self.rejection_min_wick_ratio = float(
            rejection_min_wick_ratio
        )

        self.displacement_min_body_ratio = float(
            displacement_min_body_ratio
        )

        self.displacement_min_range_atr = float(
            displacement_min_range_atr
        )

        self.close_extreme_threshold = float(
            close_extreme_threshold
        )

    # =========================================================================
    # Validation / conversion
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
                "CandleSwingIntelligence input "
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
                "Missing required candle columns: "
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

        Avoids pandas Scalar -> float Pylance errors.
        """

        if (
            value is None
            or isinstance(
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
    def _numeric(
        series: pd.Series,
    ) -> pd.Series:

        return (
            pd.to_numeric(
                series,
                errors="coerce",
            )
            .astype(
                "float64"
            )
        )

    @staticmethod
    def _safe_divide(
        numerator: np.ndarray,
        denominator: np.ndarray,
    ) -> np.ndarray:

        output = np.full(
            len(
                numerator
            ),
            np.nan,
            dtype=np.float64,
        )

        valid = (
            np.isfinite(
                numerator
            )
            &
            np.isfinite(
                denominator
            )
            &
            (
                denominator
                >
                0.0
            )
        )

        np.divide(
            numerator,
            denominator,
            out=output,
            where=valid,
        )

        return output

    # =========================================================================
    # ATR
    # =========================================================================

    def _atr(
        self,
        df: pd.DataFrame,
    ) -> pd.Series:

        if "atr" in df.columns:

            provided = self._numeric(
                df[
                    "atr"
                ]
            )

            if bool(
                (
                    provided
                    >
                    0.0
                ).any()
            ):
                return provided

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

        return (
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

    # =========================================================================
    # Context copy
    # =========================================================================

    @staticmethod
    def _copy_context(
        result: pd.DataFrame,
        source: pd.DataFrame,
    ) -> None:

        text_columns = {
            "csi_liquidity_event":
                "liqintel_event_interpretation",

            "csi_liquidity_bias":
                "liqintel_event_bias",

            "csi_range_location":
                "liqintel_range_location",

            "csi_above_cluster_type":
                "liqintel_above_cluster_type",

            "csi_below_cluster_type":
                "liqintel_below_cluster_type",
        }

        numeric_columns = {
            "csi_trap_flag":
                "liqintel_trap_flag",

            "csi_breakout_attempt_flag":
                "liqintel_breakout_attempt_flag",

            "csi_breakout_accepted_flag":
                "liqintel_breakout_accepted_flag",

            "csi_failed_breakout_flag":
                "liqintel_failed_breakout_flag",

            "csi_above_cluster_count":
                "liqintel_above_cluster_count",

            "csi_below_cluster_count":
                "liqintel_below_cluster_count",

            "csi_above_distance_atr":
                "liqintel_above_distance_atr",

            "csi_below_distance_atr":
                "liqintel_below_distance_atr",
        }

        for (
            target,
            original,
        ) in text_columns.items():

            if original in source.columns:

                result[
                    target
                ] = (
                    source[
                        original
                    ]
                    .astype(
                        str
                    )
                )

            else:

                result[
                    target
                ] = (
                    "UNKNOWN"
                )

        for (
            target,
            original,
        ) in numeric_columns.items():

            if original in source.columns:

                result[
                    target
                ] = (
                    pd.to_numeric(
                        source[
                            original
                        ],
                        errors="coerce",
                    )
                )

            else:

                result[
                    target
                ] = np.nan

    # =========================================================================
    # Primary pattern
    # =========================================================================

    @staticmethod
    def _primary_pattern(
        bullish_engulfing: np.ndarray,
        bearish_engulfing: np.ndarray,
        bullish_rejection: np.ndarray,
        bearish_rejection: np.ndarray,
        bullish_displacement: np.ndarray,
        bearish_displacement: np.ndarray,
        outside_bar: np.ndarray,
        inside_bar: np.ndarray,
        doji: np.ndarray,
    ) -> np.ndarray:

        row_count = len(
            doji
        )

        pattern = np.full(
            row_count,
            "NORMAL",
            dtype=object,
        )

        # Lower-priority states first.
        # Higher-information patterns overwrite them.

        pattern[
            doji
            ==
            1
        ] = (
            "DOJI_LIKE"
        )

        pattern[
            inside_bar
            ==
            1
        ] = (
            "INSIDE_BAR"
        )

        pattern[
            outside_bar
            ==
            1
        ] = (
            "OUTSIDE_BAR"
        )

        pattern[
            bullish_rejection
            ==
            1
        ] = (
            "BULLISH_REJECTION"
        )

        pattern[
            bearish_rejection
            ==
            1
        ] = (
            "BEARISH_REJECTION"
        )

        pattern[
            bullish_engulfing
            ==
            1
        ] = (
            "BULLISH_ENGULFING"
        )

        pattern[
            bearish_engulfing
            ==
            1
        ] = (
            "BEARISH_ENGULFING"
        )

        pattern[
            bullish_displacement
            ==
            1
        ] = (
            "BULLISH_DISPLACEMENT"
        )

        pattern[
            bearish_displacement
            ==
            1
        ] = (
            "BEARISH_DISPLACEMENT"
        )

        return pattern

    # =========================================================================
    # Causal generation
    # =========================================================================

    def generate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Generate LIVE-SAFE causal candle features.

        No cslabel_* research labels are created here.
        """

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

        for column in self.REQUIRED_COLUMNS:

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
                "CandleSwingIntelligence received "
                "invalid OHLC relationships"
            )

        open_price = (
            df[
                "open"
            ]
            .to_numpy(
                dtype=float
            )
        )

        high = (
            df[
                "high"
            ]
            .to_numpy(
                dtype=float
            )
        )

        low = (
            df[
                "low"
            ]
            .to_numpy(
                dtype=float
            )
        )

        close = (
            df[
                "close"
            ]
            .to_numpy(
                dtype=float
            )
        )

        atr_series = self._atr(
            df
        )

        atr = (
            atr_series
            .to_numpy(
                dtype=float
            )
        )

        # ---------------------------------------------------------------------
        # Raw candle anatomy
        # ---------------------------------------------------------------------

        candle_range = (
            high
            -
            low
        )

        body = np.abs(
            close
            -
            open_price
        )

        upper_wick = (
            high
            -
            np.maximum(
                open_price,
                close,
            )
        )

        lower_wick = (
            np.minimum(
                open_price,
                close,
            )
            -
            low
        )

        body_ratio = self._safe_divide(
            body,
            candle_range,
        )

        upper_wick_ratio = self._safe_divide(
            upper_wick,
            candle_range,
        )

        lower_wick_ratio = self._safe_divide(
            lower_wick,
            candle_range,
        )

        close_location = self._safe_divide(
            (
                close
                -
                low
            ),
            candle_range,
        )

        body_atr = self._safe_divide(
            body,
            atr,
        )

        range_atr = self._safe_divide(
            candle_range,
            atr,
        )

        upper_wick_atr = self._safe_divide(
            upper_wick,
            atr,
        )

        lower_wick_atr = self._safe_divide(
            lower_wick,
            atr,
        )

        # ---------------------------------------------------------------------
        # Candle direction
        # ---------------------------------------------------------------------

        bullish = (
            close
            >
            open_price
        )

        bearish = (
            close
            <
            open_price
        )

        direction = np.full(
            len(
                df
            ),
            "DOJI",
            dtype=object,
        )

        direction[
            bullish
        ] = (
            "BULLISH"
        )

        direction[
            bearish
        ] = (
            "BEARISH"
        )

        # ---------------------------------------------------------------------
        # Doji-like anatomy
        # ---------------------------------------------------------------------

        doji = np.where(
            (
                np.isfinite(
                    body_ratio
                )
                &
                (
                    body_ratio
                    <=
                    self.doji_body_ratio
                )
            ),
            1,
            0,
        ).astype(
            np.int8
        )

        # ---------------------------------------------------------------------
        # Wick rejection anatomy
        # ---------------------------------------------------------------------

        body_reference = np.maximum(
            body,
            np.finfo(
                np.float64
            ).eps,
        )

        bullish_rejection = np.where(
            (
                np.isfinite(
                    lower_wick_ratio
                )
                &
                np.isfinite(
                    close_location
                )
                &
                (
                    lower_wick
                    >=
                    (
                        body_reference
                        *
                        self.rejection_wick_body_multiple
                    )
                )
                &
                (
                    lower_wick_ratio
                    >=
                    self.rejection_min_wick_ratio
                )
                &
                (
                    close_location
                    >=
                    0.55
                )
            ),
            1,
            0,
        ).astype(
            np.int8
        )

        bearish_rejection = np.where(
            (
                np.isfinite(
                    upper_wick_ratio
                )
                &
                np.isfinite(
                    close_location
                )
                &
                (
                    upper_wick
                    >=
                    (
                        body_reference
                        *
                        self.rejection_wick_body_multiple
                    )
                )
                &
                (
                    upper_wick_ratio
                    >=
                    self.rejection_min_wick_ratio
                )
                &
                (
                    close_location
                    <=
                    0.45
                )
            ),
            1,
            0,
        ).astype(
            np.int8
        )

        # ---------------------------------------------------------------------
        # Strong displacement-like candles
        # ---------------------------------------------------------------------

        bullish_displacement = np.where(
            (
                bullish
                &
                np.isfinite(
                    body_ratio
                )
                &
                np.isfinite(
                    range_atr
                )
                &
                np.isfinite(
                    close_location
                )
                &
                (
                    body_ratio
                    >=
                    self.displacement_min_body_ratio
                )
                &
                (
                    range_atr
                    >=
                    self.displacement_min_range_atr
                )
                &
                (
                    close_location
                    >=
                    self.close_extreme_threshold
                )
            ),
            1,
            0,
        ).astype(
            np.int8
        )

        bearish_displacement = np.where(
            (
                bearish
                &
                np.isfinite(
                    body_ratio
                )
                &
                np.isfinite(
                    range_atr
                )
                &
                np.isfinite(
                    close_location
                )
                &
                (
                    body_ratio
                    >=
                    self.displacement_min_body_ratio
                )
                &
                (
                    range_atr
                    >=
                    self.displacement_min_range_atr
                )
                &
                (
                    close_location
                    <=
                    (
                        1.0
                        -
                        self.close_extreme_threshold
                    )
                )
            ),
            1,
            0,
        ).astype(
            np.int8
        )

        # ---------------------------------------------------------------------
        # Two-candle relationships
        # ---------------------------------------------------------------------

        row_count = len(
            df
        )

        bullish_engulfing = np.zeros(
            row_count,
            dtype=np.int8,
        )

        bearish_engulfing = np.zeros(
            row_count,
            dtype=np.int8,
        )

        inside_bar = np.zeros(
            row_count,
            dtype=np.int8,
        )

        outside_bar = np.zeros(
            row_count,
            dtype=np.int8,
        )

        higher_close = np.zeros(
            row_count,
            dtype=np.int8,
        )

        lower_close = np.zeros(
            row_count,
            dtype=np.int8,
        )

        if row_count > 1:

            previous_open = (
                open_price[
                    :-1
                ]
            )

            previous_close = (
                close[
                    :-1
                ]
            )

            previous_high = (
                high[
                    :-1
                ]
            )

            previous_low = (
                low[
                    :-1
                ]
            )

            bullish_engulfing[
                1:
            ] = (
                bullish[
                    1:
                ]
                &
                (
                    previous_close
                    <
                    previous_open
                )
                &
                (
                    open_price[
                        1:
                    ]
                    <=
                    previous_close
                )
                &
                (
                    close[
                        1:
                    ]
                    >=
                    previous_open
                )
            ).astype(
                np.int8
            )

            bearish_engulfing[
                1:
            ] = (
                bearish[
                    1:
                ]
                &
                (
                    previous_close
                    >
                    previous_open
                )
                &
                (
                    open_price[
                        1:
                    ]
                    >=
                    previous_close
                )
                &
                (
                    close[
                        1:
                    ]
                    <=
                    previous_open
                )
            ).astype(
                np.int8
            )

            inside_bar[
                1:
            ] = (
                (
                    high[
                        1:
                    ]
                    <=
                    previous_high
                )
                &
                (
                    low[
                        1:
                    ]
                    >=
                    previous_low
                )
            ).astype(
                np.int8
            )

            outside_bar[
                1:
            ] = (
                (
                    high[
                        1:
                    ]
                    >
                    previous_high
                )
                &
                (
                    low[
                        1:
                    ]
                    <
                    previous_low
                )
            ).astype(
                np.int8
            )

            higher_close[
                1:
            ] = (
                close[
                    1:
                ]
                >
                previous_close
            ).astype(
                np.int8
            )

            lower_close[
                1:
            ] = (
                close[
                    1:
                ]
                <
                previous_close
            ).astype(
                np.int8
            )

        primary_pattern = (
            self._primary_pattern(
                bullish_engulfing=bullish_engulfing,
                bearish_engulfing=bearish_engulfing,
                bullish_rejection=bullish_rejection,
                bearish_rejection=bearish_rejection,
                bullish_displacement=bullish_displacement,
                bearish_displacement=bearish_displacement,
                outside_bar=outside_bar,
                inside_bar=inside_bar,
                doji=doji,
            )
        )

        # ---------------------------------------------------------------------
        # Assign causal outputs
        # ---------------------------------------------------------------------

        result = df.copy()

        result[
            "csi_direction"
        ] = direction

        result[
            "csi_range"
        ] = candle_range

        result[
            "csi_body"
        ] = body

        result[
            "csi_upper_wick"
        ] = upper_wick

        result[
            "csi_lower_wick"
        ] = lower_wick

        result[
            "csi_body_ratio"
        ] = body_ratio

        result[
            "csi_upper_wick_ratio"
        ] = upper_wick_ratio

        result[
            "csi_lower_wick_ratio"
        ] = lower_wick_ratio

        result[
            "csi_close_location"
        ] = close_location

        result[
            "csi_body_atr"
        ] = body_atr

        result[
            "csi_range_atr"
        ] = range_atr

        result[
            "csi_upper_wick_atr"
        ] = upper_wick_atr

        result[
            "csi_lower_wick_atr"
        ] = lower_wick_atr

        result[
            "csi_doji_flag"
        ] = doji

        result[
            "csi_bullish_rejection_flag"
        ] = bullish_rejection

        result[
            "csi_bearish_rejection_flag"
        ] = bearish_rejection

        result[
            "csi_bullish_engulfing_flag"
        ] = bullish_engulfing

        result[
            "csi_bearish_engulfing_flag"
        ] = bearish_engulfing

        result[
            "csi_inside_bar_flag"
        ] = inside_bar

        result[
            "csi_outside_bar_flag"
        ] = outside_bar

        result[
            "csi_bullish_displacement_flag"
        ] = bullish_displacement

        result[
            "csi_bearish_displacement_flag"
        ] = bearish_displacement

        result[
            "csi_higher_close_flag"
        ] = higher_close

        result[
            "csi_lower_close_flag"
        ] = lower_close

        result[
            "csi_primary_pattern"
        ] = primary_pattern

        # ---------------------------------------------------------------------
        # Liquidity / range intelligence context
        # ---------------------------------------------------------------------

        self._copy_context(
            result,
            df,
        )

        liquidity_bias = (
            result[
                "csi_liquidity_bias"
            ]
            .astype(
                str
            )
            .str
            .upper()
        )

        trap = (
            pd.to_numeric(
                result[
                    "csi_trap_flag"
                ],
                errors="coerce",
            )
            .fillna(
                0
            )
        )

        failed_breakout = (
            pd.to_numeric(
                result[
                    "csi_failed_breakout_flag"
                ],
                errors="coerce",
            )
            .fillna(
                0
            )
        )

        # ---------------------------------------------------------------------
        # Context-aware rejection telemetry
        #
        # Still NOT a trade signal.
        # ---------------------------------------------------------------------

        result[
            "csi_bullish_liquidity_rejection_flag"
        ] = (
            (
                bullish_rejection
                ==
                1
            )
            &
            liquidity_bias.eq(
                "BULLISH"
            ).to_numpy()
            &
            (
                (
                    trap.to_numpy()
                    ==
                    1
                )
                |
                (
                    failed_breakout.to_numpy()
                    ==
                    1
                )
            )
        ).astype(
            np.int8
        )

        result[
            "csi_bearish_liquidity_rejection_flag"
        ] = (
            (
                bearish_rejection
                ==
                1
            )
            &
            liquidity_bias.eq(
                "BEARISH"
            ).to_numpy()
            &
            (
                (
                    trap.to_numpy()
                    ==
                    1
                )
                |
                (
                    failed_breakout.to_numpy()
                    ==
                    1
                )
            )
        ).astype(
            np.int8
        )

        result[
            "csi_atr"
        ] = atr_series

        result[
            "csi_version"
        ] = self.VERSION

        result[
            "csi_mode"
        ] = self.MODE

        # Explicit guardrail:
        # every csi_* column comes from current/past causal information.

        result[
            "csi_live_safe"
        ] = 1

        return result

    # =========================================================================
    # Retrospective research labels
    # =========================================================================

    def _attach_research_labels(
        self,
        causal: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Attach confirmed swing results to historical swing-origin candles.

        IMPORTANT:
        cslabel_* columns are hindsight RESEARCH LABELS.

        They may only be used for:
        - supervised research
        - pattern statistics
        - swing-origin studies

        They must NEVER become live model inputs.
        """

        result = causal.copy()

        row_count = len(
            result
        )

        result[
            "cslabel_swing_start"
        ] = np.zeros(
            row_count,
            dtype=np.int8,
        )

        result[
            "cslabel_swing_direction"
        ] = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        result[
            "cslabel_swing_scale"
        ] = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        result[
            "cslabel_swing_id"
        ] = np.zeros(
            row_count,
            dtype=np.int64,
        )

        result[
            "cslabel_confirmation_index"
        ] = np.full(
            row_count,
            -1,
            dtype=np.int64,
        )

        result[
            "cslabel_confirmation_bars"
        ] = np.full(
            row_count,
            -1,
            dtype=np.int64,
        )

        result[
            "cslabel_swing_price"
        ] = np.full(
            row_count,
            np.nan,
            dtype=np.float64,
        )

        result[
            "cslabel_excursion_atr"
        ] = np.full(
            row_count,
            np.nan,
            dtype=np.float64,
        )

        result[
            "cslabel_reversal_atr"
        ] = np.full(
            row_count,
            np.nan,
            dtype=np.float64,
        )

        result[
            "cslabel_micro_swing_start"
        ] = np.zeros(
            row_count,
            dtype=np.int8,
        )

        result[
            "cslabel_internal_swing_start"
        ] = np.zeros(
            row_count,
            dtype=np.int8,
        )

        result[
            "cslabel_major_swing_start"
        ] = np.zeros(
            row_count,
            dtype=np.int8,
        )

        result[
            "cslabel_research_only"
        ] = 1

        required = {
            "swing_id",
            "swing_type",
            "swing_price",
            "swing_scale",
            "swing_origin_index",
            "swing_confirmation_index",
        }

        if not required.issubset(
            result.columns
        ):
            return result

        for confirmation_row in range(
            row_count
        ):

            swing_id_value = (
                self._safe_float(
                    result[
                        "swing_id"
                    ].iat[
                        confirmation_row
                    ]
                )
            )

            if (
                not np.isfinite(
                    swing_id_value
                )
                or
                int(
                    swing_id_value
                )
                <=
                0
            ):
                continue

            origin_value = (
                self._safe_float(
                    result[
                        "swing_origin_index"
                    ].iat[
                        confirmation_row
                    ]
                )
            )

            confirmation_value = (
                self._safe_float(
                    result[
                        "swing_confirmation_index"
                    ].iat[
                        confirmation_row
                    ]
                )
            )

            if not np.isfinite(
                origin_value
            ):
                continue

            origin_index = int(
                origin_value
            )

            confirmation_index = (
                int(
                    confirmation_value
                )
                if np.isfinite(
                    confirmation_value
                )
                else confirmation_row
            )

            if not (
                0
                <=
                origin_index
                <
                row_count
            ):
                continue

            # Defensive causality validation.
            #
            # Confirmation cannot logically precede the swing origin.

            if (
                confirmation_index
                <
                origin_index
            ):
                continue

            # The event cannot claim confirmation later than the row
            # carrying the confirmed swing event.

            if (
                confirmation_index
                >
                confirmation_row
            ):
                continue

            swing_type = str(
                result[
                    "swing_type"
                ].iat[
                    confirmation_row
                ]
            ).upper()

            swing_scale = str(
                result[
                    "swing_scale"
                ].iat[
                    confirmation_row
                ]
            ).upper()

            if swing_type not in {
                "HIGH",
                "LOW",
            }:
                continue

            if swing_scale not in {
                "MICRO",
                "INTERNAL",
                "MAJOR",
            }:
                continue

            swing_direction = (
                "BULLISH"
                if swing_type
                ==
                "LOW"
                else
                "BEARISH"
            )

            result.at[
                origin_index,
                "cslabel_swing_start",
            ] = 1

            result.at[
                origin_index,
                "cslabel_swing_direction",
            ] = swing_direction

            result.at[
                origin_index,
                "cslabel_swing_scale",
            ] = swing_scale

            result.at[
                origin_index,
                "cslabel_swing_id",
            ] = int(
                swing_id_value
            )

            result.at[
                origin_index,
                "cslabel_confirmation_index",
            ] = confirmation_index

            result.at[
                origin_index,
                "cslabel_confirmation_bars",
            ] = (
                confirmation_index
                -
                origin_index
            )

            swing_price = (
                self._safe_float(
                    result[
                        "swing_price"
                    ].iat[
                        confirmation_row
                    ]
                )
            )

            if np.isfinite(
                swing_price
            ):
                result.at[
                    origin_index,
                    "cslabel_swing_price",
                ] = swing_price

            if (
                "swing_excursion_atr"
                in result.columns
            ):

                excursion = (
                    self._safe_float(
                        result[
                            "swing_excursion_atr"
                        ].iat[
                            confirmation_row
                        ]
                    )
                )

                if np.isfinite(
                    excursion
                ):
                    result.at[
                        origin_index,
                        "cslabel_excursion_atr",
                    ] = excursion

            if (
                "swing_reversal_atr"
                in result.columns
            ):

                reversal = (
                    self._safe_float(
                        result[
                            "swing_reversal_atr"
                        ].iat[
                            confirmation_row
                        ]
                    )
                )

                if np.isfinite(
                    reversal
                ):
                    result.at[
                        origin_index,
                        "cslabel_reversal_atr",
                    ] = reversal

            scale_column = (
                "cslabel_"
                +
                swing_scale.lower()
                +
                "_swing_start"
            )

            result.at[
                origin_index,
                scale_column,
            ] = 1

        return result

    def generate_research(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Generate causal candle features plus retrospective swing-origin labels.

        WARNING:
        Columns prefixed cslabel_ are RESEARCH LABELS.

        They can contain information learned only after future candles
        confirmed a swing.

        Never use cslabel_* columns as live model inputs.
        """

        causal = self.generate(
            data
        )

        return (
            self._attach_research_labels(
                causal
            )
        )


candle_swing_intelligence = (
    CandleSwingIntelligence()
)