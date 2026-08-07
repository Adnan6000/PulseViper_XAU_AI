"""
===============================================================================
Module      : fvg_quality_engine.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Institutional FVG Quality & Confluence Engine
===============================================================================
"""

from __future__ import annotations

from typing import Any

import pandas as pd


class FVGQualityEngine:

    def __init__(
        self,
        displacement_weight: float = 25.0,
        bos_weight: float = 25.0,
        liquidity_weight: float = 20.0,
        mitigation_weight: float = 15.0,
        structure_weight: float = 15.0,
    ) -> None:

        self.displacement_weight = float(
            displacement_weight
        )

        self.bos_weight = float(
            bos_weight
        )

        self.liquidity_weight = float(
            liquidity_weight
        )

        self.mitigation_weight = float(
            mitigation_weight
        )

        self.structure_weight = float(
            structure_weight
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

        try:
            if pd.isna(value):
                return default
        except (TypeError, ValueError):
            return default

        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    # =========================================================================
    # Required columns
    # =========================================================================

    @staticmethod
    def _ensure_columns(
        df: pd.DataFrame,
    ) -> None:

        required = [
            "fvg_id",
            "bullish_fvg",
            "bearish_fvg",
        ]

        missing = [
            column
            for column in required
            if column not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing required FVG columns: {missing}"
            )

    # =========================================================================
    # Generate
    # =========================================================================

    def generate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        self._ensure_columns(df)

        # ---------------------------------------------------------------------
        # Output columns
        # ---------------------------------------------------------------------

        df["fvg_quality_score"] = 0.0

        df["fvg_quality_grade"] = "NONE"

        df["fvg_displacement_score"] = 0.0
        df["fvg_bos_score"] = 0.0
        df["fvg_liquidity_score"] = 0.0
        df["fvg_mitigation_score"] = 0.0
        df["fvg_structure_score"] = 0.0

        df["fvg_confluence_count"] = 0

        df["fvg_institutional"] = 0

        # =========================================================================
        # Process candles
        # =========================================================================

        for i in range(len(df)):

            row = df.iloc[i]

            fvg_id = self._to_float(
                row["fvg_id"]
            )

            if fvg_id <= 0:
                continue

            # =====================================================================
            # 1. Displacement
            # =====================================================================

            displacement_score = 0.0

            if "is_displacement" in df.columns:

                displacement = self._to_float(
                    row["is_displacement"]
                )

                if displacement == 1.0:

                    raw_score = self._to_float(
                        row.get(
                            "displacement_score",
                            100.0,
                        ),
                        default=100.0,
                    )

                    displacement_score = max(
                        0.0,
                        min(100.0, raw_score),
                    )

            # =====================================================================
            # 2. BOS
            # =====================================================================

            bos_score = 0.0

            bullish_bos = self._to_float(
                row.get("bullish_bos", 0)
            )

            bearish_bos = self._to_float(
                row.get("bearish_bos", 0)
            )

            if bullish_bos == 1.0 or bearish_bos == 1.0:

                bos_strength = self._to_float(
                    row.get(
                        "bos_strength",
                        0.0,
                    )
                )

                bos_score = min(
                    100.0,
                    50.0 + (
                        bos_strength * 50.0
                    ),
                )

            # =====================================================================
            # 3. Liquidity
            # =====================================================================

            liquidity_score = 0.0

            liquidity_signal = False

            liquidity_columns = [
                "liquidity_sweep",
                "bullish_sweep",
                "bearish_sweep",
                "liquidity_swept",
            ]

            for column in liquidity_columns:

                if column in df.columns:

                    value = self._to_float(
                        row[column]
                    )

                    if value == 1.0:
                        liquidity_signal = True
                        break

            if liquidity_signal:
                liquidity_score = 100.0

            # =====================================================================
            # 4. Mitigation
            # =====================================================================

            mitigation_score = 0.0

            if "fvg_mitigated" in df.columns:

                mitigated = self._to_float(
                    row["fvg_mitigated"]
                )

                if mitigated == 1.0:
                    mitigation_score = 100.0

            if "fvg_rejection" in df.columns:

                rejection = self._to_float(
                    row["fvg_rejection"]
                )

                if rejection == 1.0:

                    rejection_strength = self._to_float(
                        row.get(
                            "fvg_rejection_strength",
                            50.0,
                        ),
                        default=50.0,
                    )

                    mitigation_score = max(
                        mitigation_score,
                        min(
                            100.0,
                            rejection_strength,
                        ),
                    )

            # =====================================================================
            # 5. Market Structure
            # =====================================================================

            structure_score = 0.0

            structure_signal = False

            structure_columns = [
                "HH",
                "HL",
                "LH",
                "LL",
            ]

            for column in structure_columns:

                if column in df.columns:

                    value = self._to_float(
                        row[column]
                    )

                    if value == 1.0:
                        structure_signal = True
                        break

            if structure_signal:
                structure_score = 100.0

            # =====================================================================
            # Weighted score
            # =====================================================================

            weighted_score = (
                (
                    displacement_score
                    / 100.0
                )
                * self.displacement_weight
            )

            weighted_score += (
                (
                    bos_score
                    / 100.0
                )
                * self.bos_weight
            )

            weighted_score += (
                (
                    liquidity_score
                    / 100.0
                )
                * self.liquidity_weight
            )

            weighted_score += (
                (
                    mitigation_score
                    / 100.0
                )
                * self.mitigation_weight
            )

            weighted_score += (
                (
                    structure_score
                    / 100.0
                )
                * self.structure_weight
            )

            final_score = max(
                0.0,
                min(
                    100.0,
                    weighted_score,
                ),
            )

            # =====================================================================
            # Confluence count
            # =====================================================================

            confluence_count = 0

            if displacement_score > 0:
                confluence_count += 1

            if bos_score > 0:
                confluence_count += 1

            if liquidity_score > 0:
                confluence_count += 1

            if mitigation_score > 0:
                confluence_count += 1

            if structure_score > 0:
                confluence_count += 1

            # =====================================================================
            # Quality grade
            # =====================================================================

            if final_score >= 80.0:

                grade = "A"
                institutional = 1

            elif final_score >= 65.0:

                grade = "B"
                institutional = 1

            elif final_score >= 50.0:

                grade = "C"
                institutional = 0

            elif final_score > 0.0:

                grade = "D"
                institutional = 0

            else:

                grade = "NONE"
                institutional = 0

            # =====================================================================
            # Store
            # =====================================================================

            index = df.index[i]

            df.at[
                index,
                "fvg_displacement_score",
            ] = round(
                displacement_score,
                2,
            )

            df.at[
                index,
                "fvg_bos_score",
            ] = round(
                bos_score,
                2,
            )

            df.at[
                index,
                "fvg_liquidity_score",
            ] = round(
                liquidity_score,
                2,
            )

            df.at[
                index,
                "fvg_mitigation_score",
            ] = round(
                mitigation_score,
                2,
            )

            df.at[
                index,
                "fvg_structure_score",
            ] = round(
                structure_score,
                2,
            )

            df.at[
                index,
                "fvg_quality_score",
            ] = round(
                final_score,
                2,
            )

            df.at[
                index,
                "fvg_quality_grade",
            ] = grade

            df.at[
                index,
                "fvg_confluence_count",
            ] = confluence_count

            df.at[
                index,
                "fvg_institutional",
            ] = institutional

        return df


fvg_quality_engine = FVGQualityEngine()