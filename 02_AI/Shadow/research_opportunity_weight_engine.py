"""
===============================================================================
Module      : research_opportunity_weight_engine.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Causal Shadow Opportunity Weight Engine
===============================================================================

Purpose
-------
Convert causal research-entry context into a SOFT opportunity score.

This is NOT a production authorization engine.

The scoring policy is based on research hypotheses discovered in the
retrospective opportunity profiler. These hypotheses must still survive
forward / out-of-sample validation.

Architecture
------------
Causal candidate
    +
direction / regime
    +
confidence band
    +
distance
    +
reference class
    +
confirmation
    +
selected research interactions
    ↓
shadow weighted score
    ↓
A / B / C / D research tier

Safety
------
- no orders
- no position modification
- no risk sizing
- no hard trade blocker
- no trade_ready modification
- no Confidence modification
- no SetupState modification
- no BOS modification
- no future candles
- no retrospective outcome columns
- no cslabel_* hindsight data

Important
---------
Positive points = supporting evidence.

Negative points = warning evidence.

A negative score does NOT automatically mean NO TRADE.
It means the research context currently carries more negative than positive
evidence.

Production remains frozen.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class ResearchOpportunityWeightEngine:
    VERSION = "1.0"

    MODE = "SHADOW_CAUSAL_WEIGHTING_ONLY"

    POLICY = "HYPOTHESIS_WEIGHTS_V1"

    OUTPUT_PREFIX = "rwei_"

    REQUIRED_COLUMNS = {
        "trade_ready",

        "lei_candidate_flag",
        "lei_direction",
        "lei_entry_family",
        "lei_reference_source",
        "lei_confirmation_type",
        "lei_distance_atr",

        "confidence_score",

        "regime_state",

        "research_live_safe",
        "research_trade_ready_unchanged",
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

    # =========================================================================
    # Basic helpers
    # =========================================================================

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

    @staticmethod
    def _confidence_band(
        score: float,
    ) -> str:

        if not np.isfinite(
            score
        ):
            return "UNKNOWN"

        if score < 50.0:
            return "<50"

        if score < 70.0:
            return "50-69"

        if score < 85.0:
            return "70-84"

        return "85+"

    @staticmethod
    def _distance_band(
        distance: float,
    ) -> str:

        if not np.isfinite(
            distance
        ):
            return "UNKNOWN"

        if distance <= 0.10:
            return "<=0.10 ATR"

        if distance <= 0.25:
            return "0.10-0.25 ATR"

        if distance <= 0.50:
            return "0.25-0.50 ATR"

        return ">0.50 ATR"

    @staticmethod
    def _reference_class(
        source: str,
    ) -> str:

        source = source.upper()

        if source.startswith(
            "MICRO_"
        ):
            return "MICRO"

        if source.startswith(
            "INTERNAL_"
        ):
            return "INTERNAL"

        if source.startswith(
            "MAJOR_"
        ):
            return "MAJOR"

        if source in {
            "PDH",
            "PDL",
            "PWH",
            "PWL",
        }:
            return "HTF_CONTEXT"

        if (
            "SESSION" in source
            or
            "ASIA" in source
            or
            "LONDON" in source
            or
            "NEW_YORK" in source
            or
            source.startswith(
                "NY_"
            )
        ):
            return "SESSION_CONTEXT"

        return "OTHER"

    @staticmethod
    def _tier(
        score: float,
    ) -> str:

        if not np.isfinite(
            score
        ):
            return "NONE"

        if score >= 3.0:
            return "A"

        if score >= 1.5:
            return "B"

        if score >= 0.0:
            return "C"

        return "D"

    # =========================================================================
    # Safety validation
    # =========================================================================

    @classmethod
    def _validate(
        cls,
        frame: pd.DataFrame,
    ) -> None:

        if not isinstance(
            frame,
            pd.DataFrame,
        ):
            raise TypeError(
                "Research weight engine input "
                "must be a pandas DataFrame"
            )

        if not frame.columns.is_unique:
            raise ValueError(
                "Research weight engine input "
                "contains duplicate columns"
            )

        missing = (
            cls.REQUIRED_COLUMNS
            -
            set(
                frame.columns
            )
        )

        if missing:
            raise ValueError(
                "Missing research weight columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )

        hindsight = [
            column
            for column in frame.columns
            if (
                isinstance(
                    column,
                    str,
                )
                and
                column.startswith(
                    "cslabel_"
                )
            )
        ]

        if hindsight:
            raise ValueError(
                "cslabel_* hindsight columns are forbidden"
            )

        live_safe = (
            pd.to_numeric(
                frame[
                    "research_live_safe"
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
                "Research weight engine requires "
                "research_live_safe == 1"
            )

        unchanged = (
            pd.to_numeric(
                frame[
                    "research_trade_ready_unchanged"
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
            unchanged.all()
        ):
            raise ValueError(
                "Research weight engine requires "
                "research_trade_ready_unchanged == 1"
            )

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
                column in cls.PROTECTED_EXACT
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
    def _assert_protected_unchanged(
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

            current = after[
                column
            ]

            if not original.equals(
                current
            ):
                raise RuntimeError(
                    "Research weight engine modified "
                    f"protected column: {column}"
                )

    # =========================================================================
    # Scoring
    # =========================================================================

    @classmethod
    def _score_candidate(
        cls,
        row: pd.Series,
    ) -> dict[
        str,
        Any,
    ]:

        direction = cls._text(
            row.get(
                "lei_direction"
            ),
            "NONE",
        )

        family = cls._text(
            row.get(
                "lei_entry_family"
            ),
            "NONE",
        )

        reference_source = cls._text(
            row.get(
                "lei_reference_source"
            ),
            "NONE",
        )

        confirmation = cls._text(
            row.get(
                "lei_confirmation_type"
            ),
            "NONE",
        )

        regime = cls._text(
            row.get(
                "regime_state"
            ),
            "UNKNOWN",
        )

        confidence = cls._number(
            row.get(
                "confidence_score"
            )
        )

        distance = cls._number(
            row.get(
                "lei_distance_atr"
            )
        )

        confidence_band = (
            cls._confidence_band(
                confidence
            )
        )

        distance_band = (
            cls._distance_band(
                distance
            )
        )

        reference_class = (
            cls._reference_class(
                reference_source
            )
        )

        positive_points = 0.0
        negative_points = 0.0

        components: list[
            str
        ] = []

        # =====================================================================
        # Confidence evidence
        # =====================================================================

        if confidence_band == "<50":

            negative_points += 0.75

            components.append(
                "CONF_<50:-0.75"
            )

        elif confidence_band == "50-69":

            positive_points += 0.25

            components.append(
                "CONF_50_69:+0.25"
            )

        elif confidence_band == "70-84":

            positive_points += 0.75

            components.append(
                "CONF_70_84:+0.75"
            )

        elif confidence_band == "85+":

            # High confidence was not reliably superior in the
            # retrospective sample, therefore it receives no bonus.
            components.append(
                "CONF_85_PLUS:+0.00"
            )

        # =====================================================================
        # Distance evidence
        # =====================================================================

        if distance_band == "<=0.10 ATR":

            positive_points += 0.50

            components.append(
                "DIST_LE_0.10:+0.50"
            )

        elif distance_band == "0.25-0.50 ATR":

            if direction == "LONG":

                positive_points += 0.25

                components.append(
                    "LONG_DIST_0.25_0.50:+0.25"
                )

        elif distance_band == ">0.50 ATR":

            negative_points += 0.50

            components.append(
                "DIST_GT_0.50:-0.50"
            )

        # =====================================================================
        # Reference-class evidence
        # =====================================================================

        if reference_class == "INTERNAL":

            positive_points += 0.25

            components.append(
                "REFERENCE_INTERNAL:+0.25"
            )

        # =====================================================================
        # Direction × regime interactions
        # =====================================================================

        if (
            direction == "LONG"
            and
            regime == "BULLISH_LOW_VOL"
        ):

            positive_points += 2.00

            components.append(
                "LONG_BULLISH_LOW_VOL:+2.00"
            )

        elif (
            direction == "LONG"
            and
            regime == "RANGE_NORMAL_VOL"
        ):

            positive_points += 1.25

            components.append(
                "LONG_RANGE_NORMAL:+1.25"
            )

        elif (
            direction == "LONG"
            and
            regime == "BULLISH_HIGH_VOL"
        ):

            negative_points += 2.00

            components.append(
                "LONG_BULLISH_HIGH_VOL:-2.00"
            )

        elif (
            direction == "SHORT"
            and
            regime == "BEARISH_LOW_VOL"
        ):

            positive_points += 2.00

            components.append(
                "SHORT_BEARISH_LOW_VOL:+2.00"
            )

        elif (
            direction == "SHORT"
            and
            regime == "RANGE_NORMAL_VOL"
        ):

            positive_points += 0.50

            components.append(
                "SHORT_RANGE_NORMAL:+0.50"
            )

        # =====================================================================
        # Confirmation evidence
        # =====================================================================

        if (
            direction == "SHORT"
            and
            confirmation == "BEARISH_DISPLACEMENT"
        ):

            positive_points += 1.50

            components.append(
                "SHORT_BEARISH_DISPLACEMENT:+1.50"
            )

        # =====================================================================
        # Selected positive interaction hypotheses
        # =====================================================================

        if (
            direction == "LONG"
            and
            confidence_band == "50-69"
            and
            regime == "RANGE_NORMAL_VOL"
        ):

            positive_points += 1.00

            components.append(
                "LONG_50_69_RANGE_NORMAL:+1.00"
            )

        if (
            direction == "LONG"
            and
            confidence_band == "70-84"
            and
            distance_band == "<=0.10 ATR"
        ):

            positive_points += 1.00

            components.append(
                "LONG_70_84_NEAR_LEVEL:+1.00"
            )

        if (
            direction == "SHORT"
            and
            confidence_band == "70-84"
            and
            confirmation == "BEARISH_DISPLACEMENT"
        ):

            positive_points += 1.00

            components.append(
                "SHORT_70_84_BEAR_DISP:+1.00"
            )

        if (
            direction == "SHORT"
            and
            family == "FAILED_BREAKOUT"
            and
            reference_class == "INTERNAL"
        ):

            positive_points += 0.75

            components.append(
                "SHORT_FAILED_BREAK_INTERNAL:+0.75"
            )

        # =====================================================================
        # Selected negative interaction hypotheses
        # =====================================================================

        if (
            family == "FAILED_BREAKOUT"
            and
            regime == "RANGE_LOW_VOL"
            and
            distance_band == "0.25-0.50 ATR"
        ):

            negative_points += 1.50

            components.append(
                "FAILED_RANGE_LOW_DIST_025_050:-1.50"
            )

        if (
            direction == "SHORT"
            and
            family == "BREAK_ACCEPTANCE"
            and
            regime == "BEARISH_HIGH_VOL"
        ):

            negative_points += 1.50

            components.append(
                "SHORT_BREAK_BEAR_HIGH_VOL:-1.50"
            )

        if (
            direction == "LONG"
            and
            family == "BREAK_ACCEPTANCE"
            and
            regime == "BULLISH_HIGH_VOL"
        ):

            negative_points += 1.50

            components.append(
                "LONG_BREAK_BULL_HIGH_VOL:-1.50"
            )

        score = (
            positive_points
            -
            negative_points
        )

        return {
            "direction": direction,

            "confidence_band": (
                confidence_band
            ),

            "distance_band": (
                distance_band
            ),

            "reference_class": (
                reference_class
            ),

            "positive_points": round(
                positive_points,
                3,
            ),

            "negative_points": round(
                negative_points,
                3,
            ),

            "score": round(
                score,
                3,
            ),

            "tier": cls._tier(
                score
            ),

            "components": (
                " | ".join(
                    components
                )
                if components
                else
                "NO_WEIGHTED_EVIDENCE"
            ),
        }

    # =========================================================================
    # Public API
    # =========================================================================

    @classmethod
    def generate(
        cls,
        frame: pd.DataFrame,
    ) -> pd.DataFrame:

        cls._validate(
            frame
        )

        protected = cls._protected_snapshot(
            frame
        )

        # Remove stale outputs so rerunning is deterministic.
        stale_outputs = [
            column
            for column in frame.columns
            if (
                isinstance(
                    column,
                    str,
                )
                and
                column.startswith(
                    cls.OUTPUT_PREFIX
                )
            )
        ]

        result = frame.drop(
            columns=stale_outputs,
            errors="ignore",
        ).copy()

        candidate_mask = (
            pd.to_numeric(
                result[
                    "lei_candidate_flag"
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

        output_rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for _, row in result.iterrows():

            candidate = bool(
                pd.to_numeric(
                    pd.Series(
                        [
                            row.get(
                                "lei_candidate_flag"
                            )
                        ]
                    ),
                    errors="coerce",
                )
                .fillna(
                    0
                )
                .iloc[
                    0
                ]
                ==
                1
            )

            if not candidate:

                output_rows.append(
                    {
                        "rwei_active": 0,

                        "rwei_direction": "NONE",

                        "rwei_confidence_band": "NONE",

                        "rwei_distance_band": "NONE",

                        "rwei_reference_class": "NONE",

                        "rwei_positive_points": 0.0,

                        "rwei_negative_points": 0.0,

                        "rwei_score": np.nan,

                        "rwei_tier": "NONE",

                        "rwei_components": "NOT_CANDIDATE",

                        "rwei_live_safe": 1,

                        "rwei_version": cls.VERSION,

                        "rwei_mode": cls.MODE,

                        "rwei_policy": cls.POLICY,
                    }
                )

                continue

            scored = cls._score_candidate(
                row
            )

            output_rows.append(
                {
                    "rwei_active": 1,

                    "rwei_direction": (
                        scored[
                            "direction"
                        ]
                    ),

                    "rwei_confidence_band": (
                        scored[
                            "confidence_band"
                        ]
                    ),

                    "rwei_distance_band": (
                        scored[
                            "distance_band"
                        ]
                    ),

                    "rwei_reference_class": (
                        scored[
                            "reference_class"
                        ]
                    ),

                    "rwei_positive_points": (
                        scored[
                            "positive_points"
                        ]
                    ),

                    "rwei_negative_points": (
                        scored[
                            "negative_points"
                        ]
                    ),

                    "rwei_score": (
                        scored[
                            "score"
                        ]
                    ),

                    "rwei_tier": (
                        scored[
                            "tier"
                        ]
                    ),

                    "rwei_components": (
                        scored[
                            "components"
                        ]
                    ),

                    "rwei_live_safe": 1,

                    "rwei_version": cls.VERSION,

                    "rwei_mode": cls.MODE,

                    "rwei_policy": cls.POLICY,
                }
            )

        outputs = pd.DataFrame(
            output_rows,
            index=result.index,
        )

        result = result.join(
            outputs
        )

        if len(
            result
        ) != len(
            frame
        ):
            raise RuntimeError(
                "Research weight engine changed row count"
            )

        if not result.index.equals(
            frame.index
        ):
            raise RuntimeError(
                "Research weight engine changed row alignment"
            )

        if int(
            candidate_mask.sum()
        ) != int(
            pd.to_numeric(
                result[
                    "rwei_active"
                ],
                errors="coerce",
            )
            .fillna(
                0
            )
            .eq(
                1
            )
            .sum()
        ):
            raise RuntimeError(
                "Research weight candidate count mismatch"
            )

        cls._assert_protected_unchanged(
            protected,
            result,
        )

        return result


research_opportunity_weight_engine = (
    ResearchOpportunityWeightEngine()
)