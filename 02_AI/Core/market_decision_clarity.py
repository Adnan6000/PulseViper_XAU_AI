"""
===============================================================================
Module      : market_decision_clarity.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Causal Market Decision / Conflict Resolution Intelligence
===============================================================================

Research contract
-----------------
This layer resolves conflicting causal evidence into a stable market state.

It does NOT:
- open trades
- modify trade_ready
- modify Confidence
- modify SetupState
- modify BOS
- modify risk
- use future candles
- guarantee market direction

Primary objective
-----------------
Prevent the system from becoming confused when:

- micro structure disagrees with internal structure
- candle pattern disagrees with liquidity context
- breakout attempt conflicts with rejection
- one candle temporarily moves against an established move
- bullish and bearish evidence appear simultaneously

Hierarchy
---------
Higher-level evidence has greater authority:

1. MAJOR / INTERNAL structure
2. Accepted breakout / failed breakout / liquidity trap
3. Directional BOS
4. Context-aware candle confirmation
5. Raw candle pattern
6. MICRO evidence

Important
---------
This is a research / shadow decision-clarity layer.

Its outputs are NOT production trade authorization.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class MarketDecisionClarity:
    VERSION = "1.0"

    MODE = "CAUSAL_RESEARCH_DECISION_CLARITY"

    def __init__(
        self,
        minimum_watch_score: float = 4.0,
        dominance_margin: float = 1.5,
        conflict_score: float = 2.5,
        flip_confirmations: int = 2,
        weak_hold_bars: int = 3,
    ) -> None:

        if minimum_watch_score < 0.0:
            raise ValueError(
                "minimum_watch_score cannot be negative"
            )

        if dominance_margin < 0.0:
            raise ValueError(
                "dominance_margin cannot be negative"
            )

        if conflict_score < 0.0:
            raise ValueError(
                "conflict_score cannot be negative"
            )

        if flip_confirmations < 1:
            raise ValueError(
                "flip_confirmations must be at least one"
            )

        if weak_hold_bars < 0:
            raise ValueError(
                "weak_hold_bars cannot be negative"
            )

        self.minimum_watch_score = float(
            minimum_watch_score
        )

        self.dominance_margin = float(
            dominance_margin
        )

        self.conflict_score = float(
            conflict_score
        )

        self.flip_confirmations = int(
            flip_confirmations
        )

        self.weak_hold_bars = int(
            weak_hold_bars
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
                "MarketDecisionClarity input "
                "must be a pandas DataFrame"
            )

        if "close" not in data.columns:
            raise ValueError(
                "MarketDecisionClarity requires close column"
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
    def _number(
        cls,
        df: pd.DataFrame,
        column: str,
        index: int,
        default: float = 0.0,
    ) -> float:

        if column not in df.columns:
            return default

        value = cls._safe_float(
            df[
                column
            ].iat[
                index
            ]
        )

        if not np.isfinite(
            value
        ):
            return default

        return value

    @staticmethod
    def _add(
        bullish: float,
        bearish: float,
        direction: str,
        weight: float,
    ) -> tuple[
        float,
        float,
    ]:

        if direction == "BULLISH":
            bullish += weight

        elif direction == "BEARISH":
            bearish += weight

        return (
            bullish,
            bearish,
        )

    # =========================================================================
    # Evidence extraction
    # =========================================================================

    def _score_row(
        self,
        df: pd.DataFrame,
        index: int,
    ) -> tuple[
        float,
        float,
        list[str],
        list[str],
    ]:

        bullish = 0.0
        bearish = 0.0

        bullish_reasons: list[
            str
        ] = []

        bearish_reasons: list[
            str
        ] = []

        # =====================================================================
        # 1. Structure bias
        # =====================================================================

        structure_bias = self._text(
            df,
            "structure_bias",
            index,
        )

        if structure_bias == "BULLISH":

            bullish += 3.0

            bullish_reasons.append(
                "STRUCTURE_BULLISH"
            )

        elif structure_bias == "BEARISH":

            bearish += 3.0

            bearish_reasons.append(
                "STRUCTURE_BEARISH"
            )

        # =====================================================================
        # 2. BOS hierarchy
        # =====================================================================

        bos_direction = self._text(
            df,
            "bos_direction",
            index,
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

        internal_bos = (
            self._number(
                df,
                "internal_bos",
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

        bos_weight = 0.0

        if major_bos:
            bos_weight = 4.0

        elif internal_bos:
            bos_weight = 3.0

        elif micro_bos:
            bos_weight = 1.0

        elif bos_direction in {
            "BULLISH",
            "BEARISH",
        }:
            bos_weight = 1.5

        if (
            bos_weight
            >
            0.0
            and
            bos_direction
            in {
                "BULLISH",
                "BEARISH",
            }
        ):

            bullish, bearish = (
                self._add(
                    bullish,
                    bearish,
                    bos_direction,
                    bos_weight,
                )
            )

            reason = (
                f"{bos_direction}_BOS"
            )

            if major_bos:
                reason += "_MAJOR"

            elif internal_bos:
                reason += "_INTERNAL"

            elif micro_bos:
                reason += "_MICRO"

            if bos_direction == "BULLISH":

                bullish_reasons.append(
                    reason
                )

            else:

                bearish_reasons.append(
                    reason
                )

        # =====================================================================
        # 3. Liquidity intelligence
        # =====================================================================

        liquidity_bias = self._text(
            df,
            "liqintel_event_bias",
            index,
            default="NEUTRAL",
        )

        trap_flag = (
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

        breakout_attempt = (
            self._number(
                df,
                "liqintel_breakout_attempt_flag",
                index,
            )
            >
            0.0
        )

        liquidity_weight = 0.0

        if accepted_breakout:
            liquidity_weight = 4.0

        elif failed_breakout:
            liquidity_weight = 3.5

        elif trap_flag:
            liquidity_weight = 3.5

        elif breakout_attempt:
            liquidity_weight = 1.0

        elif liquidity_bias in {
            "BULLISH",
            "BEARISH",
        }:
            liquidity_weight = 1.0

        if (
            liquidity_weight
            >
            0.0
            and
            liquidity_bias
            in {
                "BULLISH",
                "BEARISH",
            }
        ):

            bullish, bearish = (
                self._add(
                    bullish,
                    bearish,
                    liquidity_bias,
                    liquidity_weight,
                )
            )

            if accepted_breakout:
                reason = (
                    "ACCEPTED_BREAKOUT"
                )

            elif failed_breakout:
                reason = (
                    "FAILED_BREAKOUT"
                )

            elif trap_flag:
                reason = (
                    "LIQUIDITY_TRAP"
                )

            elif breakout_attempt:
                reason = (
                    "BREAKOUT_ATTEMPT"
                )

            else:
                reason = (
                    "LIQUIDITY_BIAS"
                )

            reason = (
                liquidity_bias
                +
                "_"
                +
                reason
            )

            if liquidity_bias == "BULLISH":

                bullish_reasons.append(
                    reason
                )

            else:

                bearish_reasons.append(
                    reason
                )

        # =====================================================================
        # 4. Context-aware candle evidence
        # =====================================================================

        bullish_liquidity_rejection = (
            self._number(
                df,
                "csi_bullish_liquidity_rejection_flag",
                index,
            )
            >
            0.0
        )

        bearish_liquidity_rejection = (
            self._number(
                df,
                "csi_bearish_liquidity_rejection_flag",
                index,
            )
            >
            0.0
        )

        if bullish_liquidity_rejection:

            bullish += 3.0

            bullish_reasons.append(
                "BULLISH_CONTEXT_REJECTION"
            )

        if bearish_liquidity_rejection:

            bearish += 3.0

            bearish_reasons.append(
                "BEARISH_CONTEXT_REJECTION"
            )

        # =====================================================================
        # 5. Displacement
        # =====================================================================

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

        if bullish_displacement:

            bullish += 2.0

            bullish_reasons.append(
                "BULLISH_DISPLACEMENT"
            )

        if bearish_displacement:

            bearish += 2.0

            bearish_reasons.append(
                "BEARISH_DISPLACEMENT"
            )

        # =====================================================================
        # 6. Engulfing
        # =====================================================================

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

        if bullish_engulfing:

            bullish += 1.0

            bullish_reasons.append(
                "BULLISH_ENGULFING"
            )

        if bearish_engulfing:

            bearish += 1.0

            bearish_reasons.append(
                "BEARISH_ENGULFING"
            )

        # =====================================================================
        # 7. Raw rejection
        # =====================================================================

        bullish_rejection = (
            self._number(
                df,
                "csi_bullish_rejection_flag",
                index,
            )
            >
            0.0
        )

        bearish_rejection = (
            self._number(
                df,
                "csi_bearish_rejection_flag",
                index,
            )
            >
            0.0
        )

        if bullish_rejection:

            bullish += 0.75

            bullish_reasons.append(
                "BULLISH_REJECTION"
            )

        if bearish_rejection:

            bearish += 0.75

            bearish_reasons.append(
                "BEARISH_REJECTION"
            )

        return (
            bullish,
            bearish,
            bullish_reasons,
            bearish_reasons,
        )

    # =========================================================================
    # Raw classification
    # =========================================================================

    def _raw_decision(
        self,
        bullish_score: float,
        bearish_score: float,
    ) -> tuple[
        str,
        str,
        float,
    ]:

        difference = (
            bullish_score
            -
            bearish_score
        )

        dominance = abs(
            difference
        )

        bullish_active = (
            bullish_score
            >=
            self.conflict_score
        )

        bearish_active = (
            bearish_score
            >=
            self.conflict_score
        )

        if (
            bullish_active
            and
            bearish_active
            and
            dominance
            <
            self.dominance_margin
        ):
            return (
                "WAIT_CONFLICT",
                "NEUTRAL",
                dominance,
            )

        if (
            bullish_score
            >=
            self.minimum_watch_score
            and
            difference
            >=
            self.dominance_margin
        ):
            return (
                "LONG_WATCH",
                "BULLISH",
                dominance,
            )

        if (
            bearish_score
            >=
            self.minimum_watch_score
            and
            (
                -difference
            )
            >=
            self.dominance_margin
        ):
            return (
                "SHORT_WATCH",
                "BEARISH",
                dominance,
            )

        if (
            bullish_score
            >
            bearish_score
        ):
            return (
                "WAIT_WEAK",
                "BULLISH",
                dominance,
            )

        if (
            bearish_score
            >
            bullish_score
        ):
            return (
                "WAIT_WEAK",
                "BEARISH",
                dominance,
            )

        return (
            "NEUTRAL",
            "NEUTRAL",
            dominance,
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

        bullish_scores = np.zeros(
            row_count,
            dtype=np.float64,
        )

        bearish_scores = np.zeros(
            row_count,
            dtype=np.float64,
        )

        dominance_values = np.zeros(
            row_count,
            dtype=np.float64,
        )

        raw_state = np.full(
            row_count,
            "NEUTRAL",
            dtype=object,
        )

        raw_direction = np.full(
            row_count,
            "NEUTRAL",
            dtype=object,
        )

        final_state = np.full(
            row_count,
            "NEUTRAL",
            dtype=object,
        )

        final_direction = np.full(
            row_count,
            "NEUTRAL",
            dtype=object,
        )

        conflict_flag = np.zeros(
            row_count,
            dtype=np.int8,
        )

        flip_pending = np.zeros(
            row_count,
            dtype=np.int8,
        )

        stability_bars = np.zeros(
            row_count,
            dtype=np.int64,
        )

        bullish_reason_text = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        bearish_reason_text = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        # ---------------------------------------------------------------------
        # Stateful clarity memory
        # ---------------------------------------------------------------------

        stable_direction = (
            "NEUTRAL"
        )

        stable_bars = 0

        weak_bars = 0

        pending_flip_direction = (
            "NEUTRAL"
        )

        pending_flip_count = 0

        for i in range(
            row_count
        ):

            (
                bullish_score,
                bearish_score,
                bullish_reasons,
                bearish_reasons,
            ) = self._score_row(
                df,
                i,
            )

            bullish_scores[
                i
            ] = bullish_score

            bearish_scores[
                i
            ] = bearish_score

            bullish_reason_text[
                i
            ] = (
                "|".join(
                    bullish_reasons
                )
                if bullish_reasons
                else
                "NONE"
            )

            bearish_reason_text[
                i
            ] = (
                "|".join(
                    bearish_reasons
                )
                if bearish_reasons
                else
                "NONE"
            )

            (
                current_raw_state,
                current_raw_direction,
                dominance,
            ) = self._raw_decision(
                bullish_score,
                bearish_score,
            )

            raw_state[
                i
            ] = current_raw_state

            raw_direction[
                i
            ] = current_raw_direction

            dominance_values[
                i
            ] = dominance

            if (
                current_raw_state
                ==
                "WAIT_CONFLICT"
            ):
                conflict_flag[
                    i
                ] = 1

            # =================================================================
            # No established direction yet
            # =================================================================

            if stable_direction == "NEUTRAL":

                if current_raw_state in {
                    "LONG_WATCH",
                    "SHORT_WATCH",
                }:

                    stable_direction = (
                        current_raw_direction
                    )

                    stable_bars = 1

                    weak_bars = 0

                    pending_flip_direction = (
                        "NEUTRAL"
                    )

                    pending_flip_count = 0

                    final_state[
                        i
                    ] = (
                        current_raw_state
                    )

                    final_direction[
                        i
                    ] = (
                        stable_direction
                    )

                else:

                    final_state[
                        i
                    ] = (
                        current_raw_state
                    )

                    final_direction[
                        i
                    ] = (
                        "NEUTRAL"
                    )

                stability_bars[
                    i
                ] = stable_bars

                continue

            # =================================================================
            # Current evidence agrees with stable direction
            # =================================================================

            if (
                current_raw_direction
                ==
                stable_direction
            ):

                pending_flip_direction = (
                    "NEUTRAL"
                )

                pending_flip_count = 0

                if current_raw_state in {
                    "LONG_WATCH",
                    "SHORT_WATCH",
                }:

                    stable_bars += 1
                    weak_bars = 0

                    final_state[
                        i
                    ] = (
                        current_raw_state
                    )

                    final_direction[
                        i
                    ] = (
                        stable_direction
                    )

                elif (
                    current_raw_state
                    ==
                    "WAIT_WEAK"
                ):

                    weak_bars += 1

                    if (
                        weak_bars
                        <=
                        self.weak_hold_bars
                    ):

                        final_state[
                            i
                        ] = (
                            "HOLD_BULLISH"
                            if stable_direction
                            ==
                            "BULLISH"
                            else
                            "HOLD_BEARISH"
                        )

                        final_direction[
                            i
                        ] = (
                            stable_direction
                        )

                    else:

                        final_state[
                            i
                        ] = (
                            "WAIT_WEAK"
                        )

                        final_direction[
                            i
                        ] = (
                            stable_direction
                        )

                else:

                    final_state[
                        i
                    ] = (
                        current_raw_state
                    )

                    final_direction[
                        i
                    ] = (
                        stable_direction
                    )

                stability_bars[
                    i
                ] = stable_bars

                continue

            # =================================================================
            # Explicit conflict
            # =================================================================

            if (
                current_raw_state
                ==
                "WAIT_CONFLICT"
            ):

                final_state[
                    i
                ] = (
                    "WAIT_CONFLICT"
                )

                final_direction[
                    i
                ] = (
                    stable_direction
                )

                flip_pending[
                    i
                ] = 0

                stability_bars[
                    i
                ] = stable_bars

                continue

            # =================================================================
            # Opposite strong evidence
            # =================================================================

            if (
                current_raw_direction
                in {
                    "BULLISH",
                    "BEARISH",
                }
                and
                current_raw_direction
                !=
                stable_direction
                and
                current_raw_state
                in {
                    "LONG_WATCH",
                    "SHORT_WATCH",
                }
            ):

                if (
                    pending_flip_direction
                    ==
                    current_raw_direction
                ):

                    pending_flip_count += 1

                else:

                    pending_flip_direction = (
                        current_raw_direction
                    )

                    pending_flip_count = 1

                flip_pending[
                    i
                ] = 1

                if (
                    pending_flip_count
                    >=
                    self.flip_confirmations
                ):

                    stable_direction = (
                        current_raw_direction
                    )

                    stable_bars = 1

                    weak_bars = 0

                    pending_flip_direction = (
                        "NEUTRAL"
                    )

                    pending_flip_count = 0

                    flip_pending[
                        i
                    ] = 0

                    final_state[
                        i
                    ] = (
                        current_raw_state
                    )

                    final_direction[
                        i
                    ] = (
                        stable_direction
                    )

                else:

                    final_state[
                        i
                    ] = (
                        "HOLD_BULLISH"
                        if stable_direction
                        ==
                        "BULLISH"
                        else
                        "HOLD_BEARISH"
                    )

                    final_direction[
                        i
                    ] = (
                        stable_direction
                    )

                stability_bars[
                    i
                ] = stable_bars

                continue

            # =================================================================
            # Weak opposite evidence
            # =================================================================

            pending_flip_direction = (
                "NEUTRAL"
            )

            pending_flip_count = 0

            weak_bars += 1

            if (
                weak_bars
                <=
                self.weak_hold_bars
            ):

                final_state[
                    i
                ] = (
                    "HOLD_BULLISH"
                    if stable_direction
                    ==
                    "BULLISH"
                    else
                    "HOLD_BEARISH"
                )

                final_direction[
                    i
                ] = (
                    stable_direction
                )

            else:

                final_state[
                    i
                ] = (
                    "WAIT_WEAK"
                )

                final_direction[
                    i
                ] = (
                    stable_direction
                )

            stability_bars[
                i
            ] = stable_bars

        # =====================================================================
        # Assign
        # =====================================================================

        result = df.copy()

        result[
            "mdc_bullish_score"
        ] = bullish_scores

        result[
            "mdc_bearish_score"
        ] = bearish_scores

        result[
            "mdc_score_spread"
        ] = (
            bullish_scores
            -
            bearish_scores
        )

        result[
            "mdc_dominance"
        ] = dominance_values

        result[
            "mdc_raw_state"
        ] = raw_state

        result[
            "mdc_raw_direction"
        ] = raw_direction

        result[
            "mdc_state"
        ] = final_state

        result[
            "mdc_direction"
        ] = final_direction

        result[
            "mdc_conflict_flag"
        ] = conflict_flag

        result[
            "mdc_flip_pending"
        ] = flip_pending

        result[
            "mdc_stability_bars"
        ] = stability_bars

        result[
            "mdc_bullish_reasons"
        ] = bullish_reason_text

        result[
            "mdc_bearish_reasons"
        ] = bearish_reason_text

        result[
            "mdc_live_safe"
        ] = 1

        result[
            "mdc_version"
        ] = self.VERSION

        result[
            "mdc_mode"
        ] = self.MODE

        return result


market_decision_clarity = (
    MarketDecisionClarity()
)