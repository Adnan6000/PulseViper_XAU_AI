"""
===============================================================================
Module      : level_entry_intelligence.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Causal Level-Specific Entry Intelligence
===============================================================================

Research contract
-----------------
This module converts an already-resolved directional WATCH state into a
structured entry candidate.

It does NOT:
- place trades
- modify trade_ready
- modify Confidence
- modify SetupState
- modify BOS
- modify risk
- use future candles
- guarantee an entry
- treat LONG_WATCH / SHORT_WATCH as an automatic trade

Core principle
--------------
STRUCTURE
+
LOCATION
+
LIQUIDITY EVENT
+
TRIGGER
+
CONFIRMATION
+
OBJECTIVE INVALIDATION
=
ENTRY CANDIDATE

Possible outputs
----------------
NO_DIRECTION
WAIT_CONFLICT
WAIT_LOCATION
WAIT_TRIGGER
WAIT_CONFIRMATION
LONG_CANDIDATE
SHORT_CANDIDATE

Entry families
--------------
SWEEP_RECLAIM
FAILED_BREAKOUT
BREAK_ACCEPTANCE
RANGE_EDGE_REJECTION
STRUCTURE_CONTINUATION
GENERIC_CONTEXT_CONFIRMATION

Important
---------
This remains research/shadow intelligence only.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class LevelEntryIntelligence:
    VERSION = "1.0"

    MODE = "CAUSAL_RESEARCH_ENTRY_INTELLIGENCE"

    LONG_STATES = {
        "LONG_WATCH",
        "HOLD_BULLISH",
    }

    SHORT_STATES = {
        "SHORT_WATCH",
        "HOLD_BEARISH",
    }

    BLOCK_STATES = {
        "WAIT_CONFLICT",
        "NEUTRAL",
    }

    EXTERNAL_SOURCES = {
        "PDH",
        "PDL",
        "PWH",
        "PWL",
        "PREV_ASIA_HIGH",
        "PREV_ASIA_LOW",
        "PREV_LONDON_HIGH",
        "PREV_LONDON_LOW",
        "PREV_NEW_YORK_HIGH",
        "PREV_NEW_YORK_LOW",
        "MAJOR_HIGH",
        "MAJOR_LOW",
    }

    INTERNAL_SOURCES = {
        "MICRO_HIGH",
        "MICRO_LOW",
        "INTERNAL_HIGH",
        "INTERNAL_LOW",
    }

    def __init__(
        self,
        max_entry_distance_atr: float = 0.35,
        invalidation_buffer_atr: float = 0.10,
        minimum_trigger_strength: float = 1.0,
    ) -> None:

        if max_entry_distance_atr < 0.0:
            raise ValueError(
                "max_entry_distance_atr cannot be negative"
            )

        if invalidation_buffer_atr < 0.0:
            raise ValueError(
                "invalidation_buffer_atr cannot be negative"
            )

        if minimum_trigger_strength < 0.0:
            raise ValueError(
                "minimum_trigger_strength cannot be negative"
            )

        self.max_entry_distance_atr = float(
            max_entry_distance_atr
        )

        self.invalidation_buffer_atr = float(
            invalidation_buffer_atr
        )

        self.minimum_trigger_strength = float(
            minimum_trigger_strength
        )

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _validate(
        data: pd.DataFrame,
    ) -> None:

        if not isinstance(
            data,
            pd.DataFrame,
        ):
            raise TypeError(
                "LevelEntryIntelligence input "
                "must be a pandas DataFrame"
            )

        required = {
            "close",
        }

        missing = (
            required
            -
            set(
                data.columns
            )
        )

        if missing:
            raise ValueError(
                "Missing required entry-intelligence columns: "
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

    @classmethod
    def _number(
        cls,
        df: pd.DataFrame,
        column: str,
        index: int,
        default: float = 0.0,
    ) -> float:

        if column not in df.columns:
            return default

        number = cls._safe_float(
            df[
                column
            ].iat[
                index
            ]
        )

        if not np.isfinite(
            number
        ):
            return default

        return number

    @staticmethod
    def _text(
        df: pd.DataFrame,
        column: str,
        index: int,
        default: str = "NONE",
    ) -> str:

        if column not in df.columns:
            return default

        value = df[
            column
        ].iat[
            index
        ]

        if value is None:
            return default

        return str(
            value
        ).strip().upper()

    @classmethod
    def _atr(
        cls,
        df: pd.DataFrame,
        index: int,
    ) -> float:

        for column in (
            "csi_atr",
            "atr",
        ):

            if column in df.columns:

                value = cls._number(
                    df,
                    column,
                    index,
                    default=np.nan,
                )

                if (
                    np.isfinite(
                        value
                    )
                    and
                    value > 0.0
                ):
                    return value

        return float(
            "nan"
        )

    # =========================================================================
    # Direction
    # =========================================================================

    def _decision_direction(
        self,
        df: pd.DataFrame,
        index: int,
    ) -> tuple[
        str,
        str,
    ]:

        state = self._text(
            df,
            "mdc_state",
            index,
            default="NEUTRAL",
        )

        direction = self._text(
            df,
            "mdc_direction",
            index,
            default="NEUTRAL",
        )

        if state in self.BLOCK_STATES:

            return (
                "NONE",
                state,
            )

        if (
            state in self.LONG_STATES
            and
            direction == "BULLISH"
        ):
            return (
                "LONG",
                state,
            )

        if (
            state in self.SHORT_STATES
            and
            direction == "BEARISH"
        ):
            return (
                "SHORT",
                state,
            )

        return (
            "NONE",
            state,
        )

    # =========================================================================
    # Liquidity event reference
    # =========================================================================

    def _event_reference(
        self,
        df: pd.DataFrame,
        index: int,
    ) -> tuple[
        float,
        str,
        str,
        str,
    ]:

        event_price = self._number(
            df,
            "liq_event_price",
            index,
            default=np.nan,
        )

        event_source = self._text(
            df,
            "liq_event_source",
            index,
        )

        event_side = self._text(
            df,
            "liq_event_side",
            index,
        )

        event_type = self._text(
            df,
            "liq_event_type",
            index,
        )

        if np.isfinite(
            event_price
        ):

            return (
                event_price,
                event_source,
                event_side,
                event_type,
            )

        return (
            float(
                "nan"
            ),
            "NONE",
            "NONE",
            "NONE",
        )

    # =========================================================================
    # Nearest contextual reference
    # =========================================================================

    def _nearest_reference(
        self,
        df: pd.DataFrame,
        index: int,
        direction: str,
    ) -> tuple[
        float,
        str,
        str,
    ]:

        if direction == "LONG":

            price = self._number(
                df,
                "liq_nearest_below_price",
                index,
                default=np.nan,
            )

            source = self._text(
                df,
                "liq_nearest_below_source",
                index,
            )

            state = self._text(
                df,
                "liq_nearest_below_state",
                index,
            )

        else:

            price = self._number(
                df,
                "liq_nearest_above_price",
                index,
                default=np.nan,
            )

            source = self._text(
                df,
                "liq_nearest_above_source",
                index,
            )

            state = self._text(
                df,
                "liq_nearest_above_state",
                index,
            )

        return (
            price,
            source,
            state,
        )

    # =========================================================================
    # Level classification
    # =========================================================================

    @classmethod
    def _level_class(
        cls,
        source: str,
    ) -> str:

        if source in cls.EXTERNAL_SOURCES:
            return "EXTERNAL"

        if source in cls.INTERNAL_SOURCES:
            return "INTERNAL"

        return "UNKNOWN"

    @staticmethod
    def _structure_scale(
        source: str,
    ) -> str:

        if source.startswith(
            "MAJOR_"
        ):
            return "MAJOR"

        if source.startswith(
            "INTERNAL_"
        ):
            return "INTERNAL"

        if source.startswith(
            "MICRO_"
        ):
            return "MICRO"

        return "CONTEXT"

    # =========================================================================
    # Trigger classification
    # =========================================================================

    def _trigger(
        self,
        df: pd.DataFrame,
        index: int,
        direction: str,
    ) -> tuple[
        str,
        float,
    ]:

        interpretation = self._text(
            df,
            "liqintel_event_interpretation",
            index,
        )

        event_bias = self._text(
            df,
            "liqintel_event_bias",
            index,
            default="NEUTRAL",
        )

        trap = (
            self._number(
                df,
                "liqintel_trap_flag",
                index,
            )
            >
            0.0
        )

        failed_breakout = (
            self._number(
                df,
                "liqintel_failed_breakout_flag",
                index,
            )
            >
            0.0
        )

        accepted_breakout = (
            self._number(
                df,
                "liqintel_breakout_accepted_flag",
                index,
            )
            >
            0.0
        )

        bullish_context_rejection = (
            self._number(
                df,
                "csi_bullish_liquidity_rejection_flag",
                index,
            )
            >
            0.0
        )

        bearish_context_rejection = (
            self._number(
                df,
                "csi_bearish_liquidity_rejection_flag",
                index,
            )
            >
            0.0
        )

        bullish_displacement = (
            self._number(
                df,
                "csi_bullish_displacement_flag",
                index,
            )
            >
            0.0
        )

        bearish_displacement = (
            self._number(
                df,
                "csi_bearish_displacement_flag",
                index,
            )
            >
            0.0
        )

        bullish_engulfing = (
            self._number(
                df,
                "csi_bullish_engulfing_flag",
                index,
            )
            >
            0.0
        )

        bearish_engulfing = (
            self._number(
                df,
                "csi_bearish_engulfing_flag",
                index,
            )
            >
            0.0
        )

        if direction == "LONG":

            if (
                trap
                and
                event_bias == "BULLISH"
            ):
                return (
                    "SWEEP_RECLAIM",
                    4.0,
                )

            if (
                failed_breakout
                and
                event_bias == "BULLISH"
            ):
                return (
                    "FAILED_BREAKOUT",
                    4.0,
                )

            if (
                accepted_breakout
                and
                event_bias == "BULLISH"
            ):
                return (
                    "BREAK_ACCEPTANCE",
                    4.0,
                )

            if bullish_context_rejection:
                return (
                    "RANGE_EDGE_REJECTION",
                    3.0,
                )

            if bullish_displacement:
                return (
                    "STRUCTURE_CONTINUATION",
                    2.0,
                )

            if bullish_engulfing:
                return (
                    "GENERIC_CONTEXT_CONFIRMATION",
                    1.0,
                )

        if direction == "SHORT":

            if (
                trap
                and
                event_bias == "BEARISH"
            ):
                return (
                    "SWEEP_RECLAIM",
                    4.0,
                )

            if (
                failed_breakout
                and
                event_bias == "BEARISH"
            ):
                return (
                    "FAILED_BREAKOUT",
                    4.0,
                )

            if (
                accepted_breakout
                and
                event_bias == "BEARISH"
            ):
                return (
                    "BREAK_ACCEPTANCE",
                    4.0,
                )

            if bearish_context_rejection:
                return (
                    "RANGE_EDGE_REJECTION",
                    3.0,
                )

            if bearish_displacement:
                return (
                    "STRUCTURE_CONTINUATION",
                    2.0,
                )

            if bearish_engulfing:
                return (
                    "GENERIC_CONTEXT_CONFIRMATION",
                    1.0,
                )

        return (
            "NONE",
            0.0,
        )

    # =========================================================================
    # Confirmation
    # =========================================================================

    def _confirmation(
        self,
        df: pd.DataFrame,
        index: int,
        direction: str,
    ) -> tuple[
        int,
        str,
    ]:

        bos_direction = self._text(
            df,
            "bos_direction",
            index,
        )

        internal_bos = (
            self._number(
                df,
                "internal_bos",
                index,
            )
            >
            0.0
        )

        major_bos = (
            self._number(
                df,
                "major_bos",
                index,
            )
            >
            0.0
        )

        micro_bos = (
            self._number(
                df,
                "micro_bos",
                index,
            )
            >
            0.0
        )

        breakout_accepted = (
            self._number(
                df,
                "liqintel_breakout_accepted_flag",
                index,
            )
            >
            0.0
        )

        event_bias = self._text(
            df,
            "liqintel_event_bias",
            index,
            default="NEUTRAL",
        )

        required_bias = (
            "BULLISH"
            if direction == "LONG"
            else
            "BEARISH"
        )

        if (
            major_bos
            and
            bos_direction == required_bias
        ):
            return (
                1,
                "MAJOR_BOS",
            )

        if (
            internal_bos
            and
            bos_direction == required_bias
        ):
            return (
                1,
                "INTERNAL_BOS",
            )

        if (
            breakout_accepted
            and
            event_bias == required_bias
        ):
            return (
                1,
                "BREAKOUT_ACCEPTANCE",
            )

        if (
            micro_bos
            and
            bos_direction == required_bias
        ):
            return (
                1,
                "MICRO_BOS",
            )

        # Candle confirmation remains weaker than structural confirmation.

        if direction == "LONG":

            bullish_displacement = (
                self._number(
                    df,
                    "csi_bullish_displacement_flag",
                    index,
                )
                >
                0.0
            )

            if bullish_displacement:
                return (
                    1,
                    "BULLISH_DISPLACEMENT",
                )

        else:

            bearish_displacement = (
                self._number(
                    df,
                    "csi_bearish_displacement_flag",
                    index,
                )
                >
                0.0
            )

            if bearish_displacement:
                return (
                    1,
                    "BEARISH_DISPLACEMENT",
                )

        return (
            0,
            "NONE",
        )

    # =========================================================================
    # Invalidation
    # =========================================================================

    def _invalidation(
        self,
        df: pd.DataFrame,
        index: int,
        direction: str,
        reference_price: float,
        atr: float,
    ) -> float:

        if not np.isfinite(
            reference_price
        ):
            return float(
                "nan"
            )

        buffer_value = (
            atr
            *
            self.invalidation_buffer_atr
            if (
                np.isfinite(
                    atr
                )
                and
                atr > 0.0
            )
            else
            0.0
        )

        if direction == "LONG":

            return (
                reference_price
                -
                buffer_value
            )

        return (
            reference_price
            +
            buffer_value
        )

    # =========================================================================
    # Location validation
    # =========================================================================

    def _location_valid(
        self,
        close: float,
        reference_price: float,
        atr: float,
    ) -> tuple[
        int,
        float,
    ]:

        if (
            not np.isfinite(
                close
            )
            or
            not np.isfinite(
                reference_price
            )
        ):
            return (
                0,
                float(
                    "nan"
                ),
            )

        distance = abs(
            close
            -
            reference_price
        )

        if (
            not np.isfinite(
                atr
            )
            or
            atr <= 0.0
        ):
            return (
                1,
                float(
                    "nan"
                ),
            )

        distance_atr = (
            distance
            /
            atr
        )

        return (
            int(
                distance_atr
                <=
                self.max_entry_distance_atr
            ),
            distance_atr,
        )

    # =========================================================================
    # Main
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

        status = np.full(
            row_count,
            "NO_DIRECTION",
            dtype=object,
        )

        direction_output = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        family_output = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        level_price_output = np.full(
            row_count,
            np.nan,
            dtype=np.float64,
        )

        level_source_output = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        level_class_output = np.full(
            row_count,
            "UNKNOWN",
            dtype=object,
        )

        structure_scale_output = np.full(
            row_count,
            "CONTEXT",
            dtype=object,
        )

        location_valid_output = np.zeros(
            row_count,
            dtype=np.int8,
        )

        distance_atr_output = np.full(
            row_count,
            np.nan,
            dtype=np.float64,
        )

        trigger_strength_output = np.zeros(
            row_count,
            dtype=np.float64,
        )

        confirmation_flag_output = np.zeros(
            row_count,
            dtype=np.int8,
        )

        confirmation_type_output = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        invalidation_output = np.full(
            row_count,
            np.nan,
            dtype=np.float64,
        )

        candidate_flag_output = np.zeros(
            row_count,
            dtype=np.int8,
        )

        decision_state_output = np.full(
            row_count,
            "NEUTRAL",
            dtype=object,
        )

        reference_origin_output = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        for i in range(
            row_count
        ):

            close = self._number(
                df,
                "close",
                i,
                default=np.nan,
            )

            atr = self._atr(
                df,
                i,
            )

            (
                direction,
                decision_state,
            ) = self._decision_direction(
                df,
                i,
            )

            decision_state_output[
                i
            ] = decision_state

            if direction == "NONE":

                if (
                    decision_state
                    ==
                    "WAIT_CONFLICT"
                ):

                    status[
                        i
                    ] = (
                        "WAIT_CONFLICT"
                    )

                else:

                    status[
                        i
                    ] = (
                        "NO_DIRECTION"
                    )

                continue

            direction_output[
                i
            ] = direction

            # -----------------------------------------------------------------
            # First preference:
            # actual liquidity event level on this candle.
            # -----------------------------------------------------------------

            (
                event_price,
                event_source,
                event_side,
                event_type,
            ) = self._event_reference(
                df,
                i,
            )

            expected_side = (
                "LOW"
                if direction == "LONG"
                else
                "HIGH"
            )

            use_event_level = (
                np.isfinite(
                    event_price
                )
                and
                event_side == expected_side
            )

            if use_event_level:

                reference_price = (
                    event_price
                )

                reference_source = (
                    event_source
                )

                reference_origin_output[
                    i
                ] = (
                    "EVENT_LEVEL"
                )

            else:

                (
                    reference_price,
                    reference_source,
                    _nearest_state,
                ) = self._nearest_reference(
                    df,
                    i,
                    direction,
                )

                reference_origin_output[
                    i
                ] = (
                    "NEAREST_LEVEL"
                )

            level_price_output[
                i
            ] = reference_price

            level_source_output[
                i
            ] = reference_source

            level_class_output[
                i
            ] = self._level_class(
                reference_source
            )

            structure_scale_output[
                i
            ] = self._structure_scale(
                reference_source
            )

            # -----------------------------------------------------------------
            # Location
            # -----------------------------------------------------------------

            (
                location_valid,
                distance_atr,
            ) = self._location_valid(
                close=close,
                reference_price=reference_price,
                atr=atr,
            )

            location_valid_output[
                i
            ] = location_valid

            distance_atr_output[
                i
            ] = distance_atr

            if not np.isfinite(
                reference_price
            ):

                status[
                    i
                ] = (
                    "WAIT_LOCATION"
                )

                continue

            if location_valid != 1:

                status[
                    i
                ] = (
                    "WAIT_LOCATION"
                )

                continue

            # -----------------------------------------------------------------
            # Trigger
            # -----------------------------------------------------------------

            (
                family,
                trigger_strength,
            ) = self._trigger(
                df,
                i,
                direction,
            )

            family_output[
                i
            ] = family

            trigger_strength_output[
                i
            ] = trigger_strength

            if (
                family == "NONE"
                or
                trigger_strength
                <
                self.minimum_trigger_strength
            ):

                status[
                    i
                ] = (
                    "WAIT_TRIGGER"
                )

                continue

            # -----------------------------------------------------------------
            # Confirmation
            # -----------------------------------------------------------------

            (
                confirmation_flag,
                confirmation_type,
            ) = self._confirmation(
                df,
                i,
                direction,
            )

            confirmation_flag_output[
                i
            ] = confirmation_flag

            confirmation_type_output[
                i
            ] = confirmation_type

            if confirmation_flag != 1:

                status[
                    i
                ] = (
                    "WAIT_CONFIRMATION"
                )

                continue

            # -----------------------------------------------------------------
            # Invalidation
            # -----------------------------------------------------------------

            invalidation = self._invalidation(
                df=df,
                index=i,
                direction=direction,
                reference_price=reference_price,
                atr=atr,
            )

            invalidation_output[
                i
            ] = invalidation

            if not np.isfinite(
                invalidation
            ):

                status[
                    i
                ] = (
                    "WAIT_LOCATION"
                )

                continue

            # -----------------------------------------------------------------
            # Candidate
            # -----------------------------------------------------------------

            candidate_flag_output[
                i
            ] = 1

            if direction == "LONG":

                status[
                    i
                ] = (
                    "LONG_CANDIDATE"
                )

            else:

                status[
                    i
                ] = (
                    "SHORT_CANDIDATE"
                )

        # =====================================================================
        # Assign
        # =====================================================================

        result = df.copy()

        result[
            "lei_status"
        ] = status

        result[
            "lei_direction"
        ] = direction_output

        result[
            "lei_entry_family"
        ] = family_output

        result[
            "lei_reference_price"
        ] = level_price_output

        result[
            "lei_reference_source"
        ] = level_source_output

        result[
            "lei_reference_origin"
        ] = reference_origin_output

        result[
            "lei_level_class"
        ] = level_class_output

        result[
            "lei_structure_scale"
        ] = structure_scale_output

        result[
            "lei_location_valid"
        ] = location_valid_output

        result[
            "lei_distance_atr"
        ] = distance_atr_output

        result[
            "lei_trigger_strength"
        ] = trigger_strength_output

        result[
            "lei_confirmation_flag"
        ] = confirmation_flag_output

        result[
            "lei_confirmation_type"
        ] = confirmation_type_output

        result[
            "lei_invalidation_price"
        ] = invalidation_output

        result[
            "lei_candidate_flag"
        ] = candidate_flag_output

        result[
            "lei_decision_state"
        ] = decision_state_output

        result[
            "lei_live_safe"
        ] = 1

        result[
            "lei_version"
        ] = self.VERSION

        result[
            "lei_mode"
        ] = self.MODE

        return result


level_entry_intelligence = (
    LevelEntryIntelligence()
)