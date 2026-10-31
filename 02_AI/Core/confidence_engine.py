"""
===============================================================================
Module      : confidence_engine.py
Project     : PulseViper XAU AI
Version     : 2.0
Author      : Muhammad Adnan
Purpose     : Temporal Scalping Confidence & Trade Trigger Engine
===============================================================================

Architecture
------------
Primary mode:

    SetupStateEngine
        ↓
    accumulated temporal evidence
        ↓
    ConfidenceEngine v2

Example:

    sweep       bar 100
    displacement bar 101
    BOS         bar 103
    FVG         bar 104
    rejection   bar 108
        ↓
    confidence calculated from SAME setup_id
        ↓
    one trade-ready trigger on bar 108

Important
---------
Confidence is a confluence score, not a guaranteed probability of profit.

Trade trigger is emitted only on setup_ready_event, preventing the same
READY setup from firing repeatedly on every later candle.

Compatibility
-------------
If SetupStateEngine columns are absent, the engine falls back to the
legacy same-row confidence contract so older pipeline code can still run.
"""

from __future__ import annotations

from numbers import Real
from typing import Any

import pandas as pd


class ConfidenceEngine:

    BOS_SCOPE_SCORE = {
        "NONE": 0.0,
        "MICRO": 70.0,
        "INTERNAL": 85.0,
        "MAJOR": 100.0,
    }

    def __init__(
        self,
        fvg_weight: float = 25.0,
        displacement_weight: float = 20.0,
        bos_weight: float = 20.0,
        liquidity_weight: float = 15.0,
        structure_weight: float = 10.0,
        mitigation_weight: float = 10.0,
        trade_threshold: float = 65.0,
        temporal_min_confluence: int = 5,
    ) -> None:

        self.fvg_weight = float(
            fvg_weight
        )

        self.displacement_weight = float(
            displacement_weight
        )

        self.bos_weight = float(
            bos_weight
        )

        self.liquidity_weight = float(
            liquidity_weight
        )

        self.structure_weight = float(
            structure_weight
        )

        self.mitigation_weight = float(
            mitigation_weight
        )

        self.trade_threshold = float(
            trade_threshold
        )

        self.temporal_min_confluence = int(
            temporal_min_confluence
        )

        self.total_weight = (
            self.fvg_weight
            + self.displacement_weight
            + self.bos_weight
            + self.liquidity_weight
            + self.structure_weight
            + self.mitigation_weight
        )

        if self.total_weight <= 0.0:

            raise ValueError(
                "Confidence weights must have a positive total"
            )

        if not (
            0.0
            <= self.trade_threshold
            <= 100.0
        ):

            raise ValueError(
                "trade_threshold must be between 0 and 100"
            )

        if (
            self.temporal_min_confluence
            < 1
            or
            self.temporal_min_confluence
            > 6
        ):

            raise ValueError(
                "temporal_min_confluence must be between 1 and 6"
            )

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _to_float(
        value: Any,
        default: float = 0.0,
    ) -> float:

        if value is None:
            return default

        if isinstance(
            value,
            bool,
        ):
            return float(
                value
            )

        if isinstance(
            value,
            Real,
        ):
            return float(
                value
            )

        try:

            if pd.isna(
                value
            ):
                return default

        except (
            TypeError,
            ValueError,
        ):
            return default

        try:

            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return default

    @classmethod
    def _flag(
        cls,
        row: pd.Series,
        column: str,
    ) -> bool:

        if column not in row.index:
            return False

        return (
            cls._to_float(
                row[column]
            )
            == 1.0
        )

    @staticmethod
    def _clamp(
        value: float,
        minimum: float = 0.0,
        maximum: float = 100.0,
    ) -> float:

        return max(
            minimum,
            min(
                maximum,
                value,
            ),
        )

    @staticmethod
    def _grade(
        score: float,
    ) -> str:

        if score >= 85.0:
            return "A+"

        if score >= 75.0:
            return "A"

        if score >= 65.0:
            return "B"

        if score >= 50.0:
            return "C"

        if score > 0.0:
            return "D"

        return "NONE"

    # =========================================================================
    # Validation
    # =========================================================================

    @staticmethod
    def _ensure_columns(
        df: pd.DataFrame,
    ) -> None:

        if "close" not in df.columns:

            raise ValueError(
                "Missing required confidence columns: ['close']"
            )

    # =========================================================================
    # Temporal Contract Detection
    # =========================================================================

    @staticmethod
    def _has_temporal_contract(
        df: pd.DataFrame,
    ) -> bool:

        required = {
            "setup_id",
            "setup_direction",
            "setup_state",
            "setup_ready",
            "setup_ready_event",
            "setup_evidence_count",
            "setup_has_sweep",
            "setup_has_displacement",
            "setup_has_bos",
            "setup_has_fvg",
            "setup_has_rejection",
            "setup_structure_alignment",
            "setup_bos_scope",
        }

        return required.issubset(
            df.columns
        )

    # =========================================================================
    # Temporal Scores
    # =========================================================================

    def _temporal_liquidity_score(
        self,
        row: pd.Series,
    ) -> float:

        if self._flag(
            row,
            "setup_has_sweep",
        ):
            return 100.0

        return 0.0

    def _temporal_displacement_score(
        self,
        row: pd.Series,
    ) -> float:

        if self._flag(
            row,
            "setup_has_displacement",
        ):
            return 100.0

        return 0.0

    def _temporal_bos_score(
        self,
        row: pd.Series,
    ) -> float:

        if not self._flag(
            row,
            "setup_has_bos",
        ):
            return 0.0

        scope = str(
            row.get(
                "setup_bos_scope",
                "MICRO",
            )
        ).upper()

        return self.BOS_SCOPE_SCORE.get(
            scope,
            70.0,
        )

    def _temporal_fvg_score(
        self,
        row: pd.Series,
    ) -> float:

        if self._flag(
            row,
            "setup_has_fvg",
        ):
            return 100.0

        return 0.0

    def _temporal_rejection_score(
        self,
        row: pd.Series,
    ) -> float:
        """
        Legacy output name is confidence_mitigation.

        In temporal mode the entry-confirmation component is specifically
        an attached FVG rejection.

        Full mitigation alone is NOT treated as bullish/bearish confirmation.
        """

        if self._flag(
            row,
            "setup_has_rejection",
        ):
            return 100.0

        return 0.0

    def _temporal_structure_score(
        self,
        row: pd.Series,
    ) -> float:
        """
        Higher structure is soft context.

        +1 alignment -> full context score
         0 unknown   -> neutral partial context
        -1 conflict  -> zero context contribution

        Conflict does NOT automatically invalidate an M1 scalp.
        """

        alignment = int(
            self._to_float(
                row.get(
                    "setup_structure_alignment",
                    0,
                )
            )
        )

        if alignment > 0:
            return 100.0

        if alignment == 0:
            return 50.0

        return 0.0

    # =========================================================================
    # Temporal Confluence
    # =========================================================================

    def _temporal_confluence(
        self,
        row: pd.Series,
    ) -> int:

        count = 0

        for column in (
            "setup_has_sweep",
            "setup_has_displacement",
            "setup_has_bos",
            "setup_has_fvg",
            "setup_has_rejection",
        ):

            if self._flag(
                row,
                column,
            ):
                count += 1

        alignment = int(
            self._to_float(
                row.get(
                    "setup_structure_alignment",
                    0,
                )
            )
        )

        if alignment > 0:
            count += 1

        return count

    # =========================================================================
    # Weighted Score
    # =========================================================================

    def _weighted_score(
        self,
        fvg_score: float,
        displacement_score: float,
        bos_score: float,
        liquidity_score: float,
        structure_score: float,
        mitigation_score: float,
    ) -> float:

        weighted = (
            fvg_score
            * self.fvg_weight

            + displacement_score
            * self.displacement_weight

            + bos_score
            * self.bos_weight

            + liquidity_score
            * self.liquidity_weight

            + structure_score
            * self.structure_weight

            + mitigation_score
            * self.mitigation_weight
        )

        final_score = (
            weighted
            / self.total_weight
        )

        return self._clamp(
            final_score
        )

    # =========================================================================
    # Temporal Mode
    # =========================================================================

    def _generate_temporal(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        for i in range(
            len(df)
        ):

            row = df.iloc[i]

            index = df.index[i]

            setup_id = int(
                self._to_float(
                    row.get(
                        "setup_id",
                        0,
                    )
                )
            )

            direction = str(
                row.get(
                    "setup_direction",
                    "NONE",
                )
            ).upper()

            conflict = self._flag(
                row,
                "setup_conflict",
            )

            # -----------------------------------------------------------------
            # No usable directional setup
            # -----------------------------------------------------------------

            if (
                setup_id <= 0
                or
                direction
                not in (
                    "BULLISH",
                    "BEARISH",
                )
                or
                conflict
            ):

                df.at[
                    index,
                    "confidence_mode",
                ] = (
                    "TEMPORAL_SETUP"
                )

                if conflict:

                    df.at[
                        index,
                        "confidence_setup_state",
                    ] = "CONFLICT"

                continue

            # -----------------------------------------------------------------
            # Evidence accumulated by SetupStateEngine
            # -----------------------------------------------------------------

            liquidity_score = (
                self._temporal_liquidity_score(
                    row
                )
            )

            displacement_score = (
                self._temporal_displacement_score(
                    row
                )
            )

            bos_score = (
                self._temporal_bos_score(
                    row
                )
            )

            fvg_score = (
                self._temporal_fvg_score(
                    row
                )
            )

            structure_score = (
                self._temporal_structure_score(
                    row
                )
            )

            rejection_score = (
                self._temporal_rejection_score(
                    row
                )
            )

            score = self._weighted_score(
                fvg_score=(
                    fvg_score
                ),
                displacement_score=(
                    displacement_score
                ),
                bos_score=(
                    bos_score
                ),
                liquidity_score=(
                    liquidity_score
                ),
                structure_score=(
                    structure_score
                ),
                mitigation_score=(
                    rejection_score
                ),
            )

            confluence = (
                self._temporal_confluence(
                    row
                )
            )

            setup_ready = self._flag(
                row,
                "setup_ready",
            )

            setup_ready_event = (
                self._flag(
                    row,
                    "setup_ready_event",
                )
            )

            trade_ready = 0

            # -----------------------------------------------------------------
            # ONE-SHOT SCALPING TRIGGER
            #
            # setup_ready may stay 1 for multiple bars.
            # setup_ready_event is 1 only on transition into READY.
            # -----------------------------------------------------------------

            if (
                setup_ready
                and
                setup_ready_event
                and
                score
                >= self.trade_threshold
                and
                confluence
                >= self.temporal_min_confluence
            ):

                trade_ready = 1

            df.at[
                index,
                "confidence_score",
            ] = round(
                score,
                2,
            )

            df.at[
                index,
                "confidence_grade",
            ] = self._grade(
                score
            )

            df.at[
                index,
                "confidence_direction",
            ] = direction

            df.at[
                index,
                "confidence_fvg",
            ] = round(
                fvg_score,
                2,
            )

            df.at[
                index,
                "confidence_displacement",
            ] = round(
                displacement_score,
                2,
            )

            df.at[
                index,
                "confidence_bos",
            ] = round(
                bos_score,
                2,
            )

            df.at[
                index,
                "confidence_liquidity",
            ] = round(
                liquidity_score,
                2,
            )

            df.at[
                index,
                "confidence_structure",
            ] = round(
                structure_score,
                2,
            )

            # Existing public output preserved.
            df.at[
                index,
                "confidence_mitigation",
            ] = round(
                rejection_score,
                2,
            )

            # Explicit v2 name.
            df.at[
                index,
                "confidence_rejection",
            ] = round(
                rejection_score,
                2,
            )

            df.at[
                index,
                "confidence_confluence",
            ] = confluence

            df.at[
                index,
                "trade_ready",
            ] = trade_ready

            # -----------------------------------------------------------------
            # Temporal audit metadata
            # -----------------------------------------------------------------

            df.at[
                index,
                "confidence_mode",
            ] = (
                "TEMPORAL_SETUP"
            )

            df.at[
                index,
                "confidence_setup_id",
            ] = setup_id

            df.at[
                index,
                "confidence_setup_state",
            ] = str(
                row.get(
                    "setup_state",
                    "NONE",
                )
            )

            df.at[
                index,
                "confidence_setup_age_bars",
            ] = int(
                self._to_float(
                    row.get(
                        "setup_age_bars",
                        -1,
                    ),
                    default=-1.0,
                )
            )

            df.at[
                index,
                "confidence_setup_ready_event",
            ] = int(
                setup_ready_event
            )

            df.at[
                index,
                "confidence_structure_alignment",
            ] = int(
                self._to_float(
                    row.get(
                        "setup_structure_alignment",
                        0,
                    )
                )
            )

            df.at[
                index,
                "confidence_bos_scope",
            ] = str(
                row.get(
                    "setup_bos_scope",
                    "NONE",
                )
            ).upper()

        return df

    # =========================================================================
    # Legacy Row-Based Helpers
    # =========================================================================

    def _legacy_fvg_score(
        self,
        row: pd.Series,
    ) -> float:

        if (
            "fvg_quality_score"
            in row.index
        ):

            return self._clamp(
                self._to_float(
                    row[
                        "fvg_quality_score"
                    ]
                )
            )

        return 0.0

    def _legacy_displacement_score(
        self,
        row: pd.Series,
    ) -> float:

        if (
            "fvg_displacement_score"
            in row.index
        ):

            return self._clamp(
                self._to_float(
                    row[
                        "fvg_displacement_score"
                    ]
                )
            )

        if (
            "displacement_score"
            in row.index
        ):

            return self._clamp(
                self._to_float(
                    row[
                        "displacement_score"
                    ]
                )
            )

        if self._flag(
            row,
            "is_displacement",
        ):
            return 100.0

        return 0.0

    def _legacy_bos_score(
        self,
        row: pd.Series,
    ) -> float:

        if (
            "fvg_bos_score"
            in row.index
        ):

            return self._clamp(
                self._to_float(
                    row[
                        "fvg_bos_score"
                    ]
                )
            )

        if (
            self._flag(
                row,
                "bullish_bos",
            )
            or
            self._flag(
                row,
                "bearish_bos",
            )
        ):

            strength = (
                self._to_float(
                    row.get(
                        "bos_strength",
                        0.0,
                    )
                )
            )

            return self._clamp(
                50.0
                + (
                    strength
                    * 50.0
                )
            )

        return 0.0

    def _legacy_liquidity_score(
        self,
        row: pd.Series,
    ) -> float:

        if (
            "fvg_liquidity_score"
            in row.index
        ):

            return self._clamp(
                self._to_float(
                    row[
                        "fvg_liquidity_score"
                    ]
                )
            )

        for column in (
            "liquidity_sweep",
            "bullish_sweep",
            "bearish_sweep",
            "liquidity_swept",
        ):

            if self._flag(
                row,
                column,
            ):
                return 100.0

        return 0.0

    def _legacy_structure_score(
        self,
        row: pd.Series,
    ) -> float:

        if (
            "fvg_structure_score"
            in row.index
        ):

            return self._clamp(
                self._to_float(
                    row[
                        "fvg_structure_score"
                    ]
                )
            )

        for column in (
            "HH",
            "HL",
            "LH",
            "LL",
        ):

            if self._flag(
                row,
                column,
            ):
                return 100.0

        return 0.0

    def _legacy_mitigation_score(
        self,
        row: pd.Series,
    ) -> float:

        if (
            "fvg_mitigation_score"
            in row.index
        ):

            return self._clamp(
                self._to_float(
                    row[
                        "fvg_mitigation_score"
                    ]
                )
            )

        if self._flag(
            row,
            "fvg_mitigated",
        ):
            return 100.0

        if self._flag(
            row,
            "fvg_rejection",
        ):

            return self._clamp(
                self._to_float(
                    row.get(
                        "fvg_rejection_strength",
                        50.0,
                    ),
                    default=50.0,
                )
            )

        return 0.0

    def _legacy_direction(
        self,
        row: pd.Series,
    ) -> str:

        bullish = 0
        bearish = 0

        for column in (
            "bullish_fvg",
            "bullish_bos",
            "bullish_sweep",
        ):

            if self._flag(
                row,
                column,
            ):
                bullish += 1

        for column in (
            "bearish_fvg",
            "bearish_bos",
            "bearish_sweep",
        ):

            if self._flag(
                row,
                column,
            ):
                bearish += 1

        if bullish > bearish:
            return "BULLISH"

        if bearish > bullish:
            return "BEARISH"

        return "NEUTRAL"

    # =========================================================================
    # Legacy Mode
    # =========================================================================

    def _generate_legacy(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        for i in range(
            len(df)
        ):

            row = df.iloc[i]

            index = df.index[i]

            fvg_score = (
                self._legacy_fvg_score(
                    row
                )
            )

            displacement_score = (
                self._legacy_displacement_score(
                    row
                )
            )

            bos_score = (
                self._legacy_bos_score(
                    row
                )
            )

            liquidity_score = (
                self._legacy_liquidity_score(
                    row
                )
            )

            structure_score = (
                self._legacy_structure_score(
                    row
                )
            )

            mitigation_score = (
                self._legacy_mitigation_score(
                    row
                )
            )

            score = self._weighted_score(
                fvg_score=(
                    fvg_score
                ),
                displacement_score=(
                    displacement_score
                ),
                bos_score=(
                    bos_score
                ),
                liquidity_score=(
                    liquidity_score
                ),
                structure_score=(
                    structure_score
                ),
                mitigation_score=(
                    mitigation_score
                ),
            )

            components = (
                fvg_score,
                displacement_score,
                bos_score,
                liquidity_score,
                structure_score,
                mitigation_score,
            )

            confluence = sum(
                1
                for component
                in components
                if component > 0.0
            )

            direction = (
                self._legacy_direction(
                    row
                )
            )

            trade_ready = 0

            # Legacy behavior intentionally preserved.
            if (
                score
                >= self.trade_threshold
                and
                confluence
                >= 3
                and
                direction
                != "NEUTRAL"
            ):

                trade_ready = 1

            df.at[
                index,
                "confidence_score",
            ] = round(
                score,
                2,
            )

            df.at[
                index,
                "confidence_grade",
            ] = self._grade(
                score
            )

            df.at[
                index,
                "confidence_direction",
            ] = direction

            df.at[
                index,
                "confidence_fvg",
            ] = round(
                fvg_score,
                2,
            )

            df.at[
                index,
                "confidence_displacement",
            ] = round(
                displacement_score,
                2,
            )

            df.at[
                index,
                "confidence_bos",
            ] = round(
                bos_score,
                2,
            )

            df.at[
                index,
                "confidence_liquidity",
            ] = round(
                liquidity_score,
                2,
            )

            df.at[
                index,
                "confidence_structure",
            ] = round(
                structure_score,
                2,
            )

            df.at[
                index,
                "confidence_mitigation",
            ] = round(
                mitigation_score,
                2,
            )

            df.at[
                index,
                "confidence_rejection",
            ] = 0.0

            df.at[
                index,
                "confidence_confluence",
            ] = confluence

            df.at[
                index,
                "trade_ready",
            ] = trade_ready

            df.at[
                index,
                "confidence_mode",
            ] = (
                "LEGACY_ROW"
            )

        return df

    # =========================================================================
    # Main
    # =========================================================================

    def generate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        self._ensure_columns(
            df
        )

        # ---------------------------------------------------------------------
        # Existing public outputs
        # ---------------------------------------------------------------------

        df[
            "confidence_score"
        ] = 0.0

        df[
            "confidence_grade"
        ] = "NONE"

        df[
            "confidence_direction"
        ] = "NEUTRAL"

        df[
            "confidence_fvg"
        ] = 0.0

        df[
            "confidence_displacement"
        ] = 0.0

        df[
            "confidence_bos"
        ] = 0.0

        df[
            "confidence_liquidity"
        ] = 0.0

        df[
            "confidence_structure"
        ] = 0.0

        df[
            "confidence_mitigation"
        ] = 0.0

        df[
            "confidence_confluence"
        ] = 0

        df[
            "trade_ready"
        ] = 0

        # ---------------------------------------------------------------------
        # v2 audit outputs
        # ---------------------------------------------------------------------

        df[
            "confidence_rejection"
        ] = 0.0

        df[
            "confidence_mode"
        ] = "NONE"

        df[
            "confidence_setup_id"
        ] = 0

        df[
            "confidence_setup_state"
        ] = "NONE"

        df[
            "confidence_setup_age_bars"
        ] = -1

        df[
            "confidence_setup_ready_event"
        ] = 0

        df[
            "confidence_structure_alignment"
        ] = 0

        df[
            "confidence_bos_scope"
        ] = "NONE"

        # ---------------------------------------------------------------------
        # Select architecture
        # ---------------------------------------------------------------------

        if self._has_temporal_contract(
            df
        ):

            return self._generate_temporal(
                df
            )

        return self._generate_legacy(
            df
        )


confidence_engine = (
    ConfidenceEngine()
)