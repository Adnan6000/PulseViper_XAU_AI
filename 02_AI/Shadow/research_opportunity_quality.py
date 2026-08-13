"""
===============================================================================
Module      : research_opportunity_quality.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Retrospective Opportunity Quality Profiling
===============================================================================

Purpose
-------
Analyze matured research opportunity episodes across combinations such as:

- LONG / SHORT
- confidence band
- entry family
- reference class
- confirmation type
- regime
- distance-to-level band

This module is RESEARCH ONLY.

It does NOT:
- create trade_ready
- block trades
- authorize entries
- modify production Confidence
- modify LEI / MDC
- place orders
- modify risk

Important
---------
Outcome columns such as net_20 / MFE / MAE are retrospective research labels.
They must never be attached back into the causal live decision chain.
"""

from __future__ import annotations

from itertools import combinations
from typing import Any, Iterable

import numpy as np
import pandas as pd


class ResearchOpportunityQualityProfiler:
    VERSION = "1.0"

    MODE = "RETROSPECTIVE_RESEARCH_PROFILE_ONLY"

    REQUIRED_COLUMNS = {
        "direction",
        "lei_entry_family",
        "lei_reference_source",
        "lei_confirmation_type",
        "first_distance_atr",
        "first_confidence_score",
        "first_regime_state",
        "first_status",
        "first_net_5",
        "first_net_10",
        "first_net_20",
        "first_mfe_20",
        "first_mae_20",
        "first_positive_20",
    }

    PROFILE_COLUMNS = (
        "profile_dimensions",
        "profile_key",

        "n",
        "sample_share_pct",

        "net5_med",
        "net10_med",
        "net20_med",

        "positive20_pct",

        "mfe20_med",
        "mae20_med",

        "excursion_balance_med",

        "profiler_version",
        "profiler_mode",
    )

    DEFAULT_DIMENSIONS = (
        "direction",
        "confidence_band",
        "lei_entry_family",
        "reference_class",
        "lei_confirmation_type",
        "regime_state",
        "distance_band",
    )

    # =========================================================================
    # Validation
    # =========================================================================

    @classmethod
    def _validate(
        cls,
        episodes: pd.DataFrame,
    ) -> None:

        if not isinstance(
            episodes,
            pd.DataFrame,
        ):
            raise TypeError(
                "Opportunity quality input must be a pandas DataFrame"
            )

        if not episodes.columns.is_unique:
            raise ValueError(
                "Opportunity quality input contains duplicate column names"
            )

        missing = (
            cls.REQUIRED_COLUMNS
            -
            set(
                episodes.columns
            )
        )

        if missing:
            raise ValueError(
                "Missing opportunity quality columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )

    # =========================================================================
    # Normalization helpers
    # =========================================================================

    @staticmethod
    def _text_series(
        frame: pd.DataFrame,
        column: str,
        default: str = "UNKNOWN",
    ) -> pd.Series:

        values = (
            frame[
                column
            ]
            .astype(
                "string"
            )
            .fillna(
                default
            )
            .str
            .strip()
            .str
            .upper()
        )

        return values.mask(
            values.eq(
                ""
            ),
            default,
        )

    @staticmethod
    def _confidence_band(
        value: Any,
    ) -> str:

        number = pd.to_numeric(
            pd.Series(
                [
                    value
                ]
            ),
            errors="coerce",
        ).iloc[
            0
        ]

        if pd.isna(
            number
        ):
            return "UNKNOWN"

        number = float(
            number
        )

        if number < 50.0:
            return "<50"

        if number < 70.0:
            return "50-69"

        if number < 85.0:
            return "70-84"

        return "85+"

    @staticmethod
    def _distance_band(
        value: Any,
    ) -> str:

        number = pd.to_numeric(
            pd.Series(
                [
                    value
                ]
            ),
            errors="coerce",
        ).iloc[
            0
        ]

        if pd.isna(
            number
        ):
            return "UNKNOWN"

        number = float(
            number
        )

        if number <= 0.10:
            return "<=0.10 ATR"

        if number <= 0.25:
            return "0.10-0.25 ATR"

        if number <= 0.50:
            return "0.25-0.50 ATR"

        return ">0.50 ATR"

    @staticmethod
    def _reference_class(
        value: Any,
    ) -> str:

        if value is None:
            return "UNKNOWN"

        try:
            if pd.isna(
                value
            ):
                return "UNKNOWN"

        except (
            TypeError,
            ValueError,
        ):
            pass

        text = str(
            value
        ).strip().upper()

        if not text:
            return "UNKNOWN"

        if text.startswith(
            "MICRO_"
        ):
            return "MICRO"

        if text.startswith(
            "INTERNAL_"
        ):
            return "INTERNAL"

        if text.startswith(
            "MAJOR_"
        ):
            return "MAJOR"

        if text in {
            "PDH",
            "PDL",
            "PWH",
            "PWL",
        }:
            return "HTF_CONTEXT"

        if (
            "SESSION" in text
            or
            "ASIA" in text
            or
            "LONDON" in text
            or
            "NEW_YORK" in text
            or
            text.startswith(
                "NY_"
            )
        ):
            return "SESSION_CONTEXT"

        return "OTHER"

    # =========================================================================
    # Prepared matured research frame
    # =========================================================================

    @classmethod
    def prepare(
        cls,
        episodes: pd.DataFrame,
    ) -> pd.DataFrame:

        cls._validate(
            episodes
        )

        if episodes.empty:
            return pd.DataFrame(
                columns=[
                    *episodes.columns,
                    "confidence_band",
                    "distance_band",
                    "reference_class",
                    "regime_state",
                    "excursion_balance",
                ]
            )

        matured = episodes.loc[
            cls._text_series(
                episodes,
                "first_status",
            ).eq(
                "MATURED_20"
            )
        ].copy()

        if matured.empty:
            matured[
                "confidence_band"
            ] = pd.Series(
                dtype="object"
            )

            matured[
                "distance_band"
            ] = pd.Series(
                dtype="object"
            )

            matured[
                "reference_class"
            ] = pd.Series(
                dtype="object"
            )

            matured[
                "regime_state"
            ] = pd.Series(
                dtype="object"
            )

            matured[
                "excursion_balance"
            ] = pd.Series(
                dtype=float
            )

            return matured

        matured[
            "direction"
        ] = cls._text_series(
            matured,
            "direction",
        )

        matured[
            "lei_entry_family"
        ] = cls._text_series(
            matured,
            "lei_entry_family",
        )

        matured[
            "lei_confirmation_type"
        ] = cls._text_series(
            matured,
            "lei_confirmation_type",
        )

        matured[
            "regime_state"
        ] = cls._text_series(
            matured,
            "first_regime_state",
        )

        matured[
            "confidence_band"
        ] = (
            matured[
                "first_confidence_score"
            ]
            .map(
                cls._confidence_band
            )
        )

        matured[
            "distance_band"
        ] = (
            matured[
                "first_distance_atr"
            ]
            .map(
                cls._distance_band
            )
        )

        matured[
            "reference_class"
        ] = (
            matured[
                "lei_reference_source"
            ]
            .map(
                cls._reference_class
            )
        )

        mfe = pd.to_numeric(
            matured[
                "first_mfe_20"
            ],
            errors="coerce",
        )

        mae = pd.to_numeric(
            matured[
                "first_mae_20"
            ],
            errors="coerce",
        )

        matured[
            "excursion_balance"
        ] = (
            mfe
            -
            mae
        )

        return matured.reset_index(
            drop=True
        )

    # =========================================================================
    # Metric helpers
    # =========================================================================

    @staticmethod
    def _median(
        frame: pd.DataFrame,
        column: str,
    ) -> float:

        values = pd.to_numeric(
            frame[
                column
            ],
            errors="coerce",
        ).dropna()

        if values.empty:
            return np.nan

        return round(
            float(
                values.median()
            ),
            3,
        )

    @staticmethod
    def _percentage(
        frame: pd.DataFrame,
        column: str,
    ) -> float:

        values = pd.to_numeric(
            frame[
                column
            ],
            errors="coerce",
        ).dropna()

        if values.empty:
            return np.nan

        return round(
            float(
                values.mean()
                *
                100.0
            ),
            3,
        )

    @classmethod
    def _metrics(
        cls,
        frame: pd.DataFrame,
        total_sample: int,
    ) -> dict[
        str,
        Any,
    ]:

        return {
            "n": len(
                frame
            ),

            "sample_share_pct": (
                round(
                    (
                        len(
                            frame
                        )
                        /
                        total_sample
                    )
                    *
                    100.0,
                    3,
                )
                if total_sample
                else 0.0
            ),

            "net5_med": cls._median(
                frame,
                "first_net_5",
            ),

            "net10_med": cls._median(
                frame,
                "first_net_10",
            ),

            "net20_med": cls._median(
                frame,
                "first_net_20",
            ),

            "positive20_pct": cls._percentage(
                frame,
                "first_positive_20",
            ),

            "mfe20_med": cls._median(
                frame,
                "first_mfe_20",
            ),

            "mae20_med": cls._median(
                frame,
                "first_mae_20",
            ),

            "excursion_balance_med": cls._median(
                frame,
                "excursion_balance",
            ),
        }

    # =========================================================================
    # Generic profile
    # =========================================================================

    @classmethod
    def profile(
        cls,
        episodes: pd.DataFrame,
        dimensions: Iterable[
            str
        ],
        minimum_n: int = 1,
    ) -> pd.DataFrame:

        if minimum_n < 1:
            raise ValueError(
                "minimum_n must be >= 1"
            )

        prepared = cls.prepare(
            episodes
        )

        dimensions = tuple(
            dimensions
        )

        if not dimensions:
            raise ValueError(
                "At least one profile dimension is required"
            )

        allowed = set(
            cls.DEFAULT_DIMENSIONS
        )

        unknown = (
            set(
                dimensions
            )
            -
            allowed
        )

        if unknown:
            raise ValueError(
                "Unsupported profile dimensions: "
                +
                ", ".join(
                    sorted(
                        unknown
                    )
                )
            )

        if prepared.empty:
            return pd.DataFrame(
                columns=list(
                    cls.PROFILE_COLUMNS
                )
            )

        total_sample = len(
            prepared
        )

        rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        grouper: Any = (
            dimensions[
                0
            ]
            if len(
                dimensions
            ) == 1
            else list(
                dimensions
            )
        )

        grouped = prepared.groupby(
            grouper,
            dropna=False,
            sort=True,
        )

        for key, frame in grouped:

            if len(
                frame
            ) < minimum_n:
                continue

            if not isinstance(
                key,
                tuple,
            ):
                key = (
                    key,
                )

            key_parts = [
                f"{dimension}={value}"
                for dimension, value
                in zip(
                    dimensions,
                    key,
                    strict=True,
                )
            ]

            record = {
                "profile_dimensions": (
                    " × ".join(
                        dimensions
                    )
                ),

                "profile_key": (
                    " | ".join(
                        key_parts
                    )
                ),

                **cls._metrics(
                    frame,
                    total_sample,
                ),

                "profiler_version": (
                    cls.VERSION
                ),

                "profiler_mode": (
                    cls.MODE
                ),
            }

            rows.append(
                record
            )

        result = pd.DataFrame(
            rows,
            columns=list(
                cls.PROFILE_COLUMNS
            ),
        )

        if result.empty:
            return result

        return (
            result
            .sort_values(
                by=[
                    "net20_med",
                    "positive20_pct",
                    "n",
                ],
                ascending=[
                    False,
                    False,
                    False,
                ],
                na_position="last",
            )
            .reset_index(
                drop=True
            )
        )

    # =========================================================================
    # Standard dashboards
    # =========================================================================

    @classmethod
    def single_dimension_profiles(
        cls,
        episodes: pd.DataFrame,
        minimum_n: int = 10,
    ) -> pd.DataFrame:

        frames: list[
            pd.DataFrame
        ] = []

        for dimension in cls.DEFAULT_DIMENSIONS:

            profile = cls.profile(
                episodes,
                dimensions=(
                    dimension,
                ),
                minimum_n=minimum_n,
            )

            if not profile.empty:
                frames.append(
                    profile
                )

        if not frames:
            return pd.DataFrame(
                columns=list(
                    cls.PROFILE_COLUMNS
                )
            )

        return pd.concat(
            frames,
            ignore_index=True,
        )

    @classmethod
    def direction_interactions(
        cls,
        episodes: pd.DataFrame,
        minimum_n: int = 15,
    ) -> pd.DataFrame:

        dimensions = (
            "confidence_band",
            "lei_entry_family",
            "reference_class",
            "lei_confirmation_type",
            "regime_state",
            "distance_band",
        )

        frames: list[
            pd.DataFrame
        ] = []

        for dimension in dimensions:

            profile = cls.profile(
                episodes,
                dimensions=(
                    "direction",
                    dimension,
                ),
                minimum_n=minimum_n,
            )

            if not profile.empty:
                frames.append(
                    profile
                )

        if not frames:
            return pd.DataFrame(
                columns=list(
                    cls.PROFILE_COLUMNS
                )
            )

        result = pd.concat(
            frames,
            ignore_index=True,
        )

        return (
            result
            .sort_values(
                by=[
                    "net20_med",
                    "positive20_pct",
                    "n",
                ],
                ascending=[
                    False,
                    False,
                    False,
                ],
                na_position="last",
            )
            .reset_index(
                drop=True
            )
        )

    @classmethod
    def three_way_profiles(
        cls,
        episodes: pd.DataFrame,
        minimum_n: int = 15,
    ) -> pd.DataFrame:

        third_dimensions = (
            "lei_entry_family",
            "reference_class",
            "lei_confirmation_type",
            "regime_state",
            "distance_band",
        )

        frames: list[
            pd.DataFrame
        ] = []

        for third in third_dimensions:

            profile = cls.profile(
                episodes,
                dimensions=(
                    "direction",
                    "confidence_band",
                    third,
                ),
                minimum_n=minimum_n,
            )

            if not profile.empty:
                frames.append(
                    profile
                )

        if not frames:
            return pd.DataFrame(
                columns=list(
                    cls.PROFILE_COLUMNS
                )
            )

        result = pd.concat(
            frames,
            ignore_index=True,
        )

        return (
            result
            .sort_values(
                by=[
                    "net20_med",
                    "positive20_pct",
                    "n",
                ],
                ascending=[
                    False,
                    False,
                    False,
                ],
                na_position="last",
            )
            .reset_index(
                drop=True
            )
        )

    # =========================================================================
    # Exhaustive limited-depth research
    # =========================================================================

    @classmethod
    def combination_search(
        cls,
        episodes: pd.DataFrame,
        max_dimensions: int = 3,
        minimum_n: int = 20,
    ) -> pd.DataFrame:
        """
        Research-only search across combinations up to max_dimensions.

        This is diagnostic exploration, not automatic strategy selection.
        """

        if max_dimensions < 1:
            raise ValueError(
                "max_dimensions must be >= 1"
            )

        max_dimensions = min(
            max_dimensions,
            len(
                cls.DEFAULT_DIMENSIONS
            ),
        )

        frames: list[
            pd.DataFrame
        ] = []

        for size in range(
            1,
            max_dimensions + 1,
        ):

            for dimension_group in combinations(
                cls.DEFAULT_DIMENSIONS,
                size,
            ):

                profile = cls.profile(
                    episodes,
                    dimensions=dimension_group,
                    minimum_n=minimum_n,
                )

                if not profile.empty:
                    frames.append(
                        profile
                    )

        if not frames:
            return pd.DataFrame(
                columns=list(
                    cls.PROFILE_COLUMNS
                )
            )

        result = pd.concat(
            frames,
            ignore_index=True,
        )

        return (
            result
            .sort_values(
                by=[
                    "net20_med",
                    "positive20_pct",
                    "n",
                ],
                ascending=[
                    False,
                    False,
                    False,
                ],
                na_position="last",
            )
            .reset_index(
                drop=True
            )
        )

    # =========================================================================
    # Evidence shortlist
    # =========================================================================

    @classmethod
    def evidence_shortlist(
        cls,
        profiles: pd.DataFrame,
        minimum_n: int = 20,
    ) -> pd.DataFrame:
        """
        Return statistically non-tiny positive research groups.

        IMPORTANT:
        This is NOT a production authorization list and NOT a blocker table.
        """

        if minimum_n < 1:
            raise ValueError(
                "minimum_n must be >= 1"
            )

        if profiles.empty:
            return profiles.copy()

        required = {
            "n",
            "net20_med",
            "positive20_pct",
        }

        missing = (
            required
            -
            set(
                profiles.columns
            )
        )

        if missing:
            raise ValueError(
                "Missing profile evidence columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )

        n = pd.to_numeric(
            profiles[
                "n"
            ],
            errors="coerce",
        )

        net20 = pd.to_numeric(
            profiles[
                "net20_med"
            ],
            errors="coerce",
        )

        positive = pd.to_numeric(
            profiles[
                "positive20_pct"
            ],
            errors="coerce",
        )

        mask = (
            n.ge(
                minimum_n
            )
            &
            net20.gt(
                0.0
            )
            &
            positive.gt(
                50.0
            )
        )

        return (
            profiles
            .loc[
                mask
            ]
            .sort_values(
                by=[
                    "net20_med",
                    "positive20_pct",
                    "n",
                ],
                ascending=[
                    False,
                    False,
                    False,
                ],
            )
            .reset_index(
                drop=True
            )
        )


research_opportunity_quality_profiler = (
    ResearchOpportunityQualityProfiler()
)