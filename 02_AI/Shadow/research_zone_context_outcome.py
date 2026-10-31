"""
===============================================================================
Module      : research_zone_context_outcome.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Retrospective Outcome Profiling for Causal Zone Context
===============================================================================

Purpose
-------
Join already-formed research opportunity episodes to the CAUSAL
Institutional Zone context that existed at the episode's first signal time.

This lets research answer questions such as:

- Do LONG opportunities near bullish demand perform better?
- Do SHORT opportunities near bearish supply perform better?
- Does FRESH vs MITIGATED vs ACCEPTED context matter?
- Does being inside an aligned zone help?
- Does proximity to an opposing zone hurt?
- Is zone context useful evidence, or merely additional noise?

Critical architecture rule
--------------------------
The causal zone context comes from the SAME signal-time row.

Outcome columns are retrospective labels used only AFTER that join.

This module does NOT:
- change candidate ledger rows
- rewrite old event metadata
- change LEI
- change MDC
- change RWEI
- change trade_ready
- block trades
- authorize entries
- place orders
- modify risk
"""

from __future__ import annotations

from itertools import combinations
from typing import Any, Iterable

import numpy as np
import pandas as pd


class ResearchZoneContextOutcomeProfiler:
    VERSION = "1.0"

    MODE = "RETROSPECTIVE_ZONE_CONTEXT_OUTCOME_PROFILE_ONLY"

    REQUIRED_EPISODE_COLUMNS = {
        "episode_id",
        "first_signal_time",
        "direction",

        "first_status",

        "first_confidence_score",
        "first_regime_state",

        "first_net_5",
        "first_net_10",
        "first_net_20",

        "first_mfe_20",
        "first_mae_20",

        "first_positive_20",
    }

    REQUIRED_PIPELINE_COLUMNS = {
        "time",

        "izctx_active_bullish_count",
        "izctx_active_bearish_count",

        "izctx_bullish_event_id",
        "izctx_bullish_state",
        "izctx_bullish_distance_atr",
        "izctx_bullish_inside_flag",
        "izctx_bullish_overlap_flag",

        "izctx_bearish_event_id",
        "izctx_bearish_state",
        "izctx_bearish_distance_atr",
        "izctx_bearish_inside_flag",
        "izctx_bearish_overlap_flag",

        "izctx_live_safe",

        "research_live_safe",
        "research_trade_ready_unchanged",
    }

    DEFAULT_DIMENSIONS = (
        "direction",
        "aligned_zone_state",
        "aligned_distance_band",
        "aligned_location",
        "opposing_zone_state",
        "opposing_distance_band",
        "opposing_location",
        "zone_relation",
    )

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

    # =========================================================================
    # Helpers
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
    def _time_series(
        frame: pd.DataFrame,
        column: str,
    ) -> pd.Series:

        return pd.to_datetime(
            frame[
                column
            ],
            errors="coerce",
            utc=True,
        )

    @staticmethod
    def _median(
        values: pd.Series,
    ) -> float:

        numeric = pd.to_numeric(
            values,
            errors="coerce",
        ).dropna()

        if numeric.empty:
            return np.nan

        return float(
            numeric.median()
        )

    # =========================================================================
    # Validation
    # =========================================================================

    @classmethod
    def _validate(
        cls,
        episodes: pd.DataFrame,
        pipeline: pd.DataFrame,
    ) -> None:

        if not isinstance(
            episodes,
            pd.DataFrame,
        ):
            raise TypeError(
                "episodes must be a pandas DataFrame"
            )

        if not isinstance(
            pipeline,
            pd.DataFrame,
        ):
            raise TypeError(
                "pipeline must be a pandas DataFrame"
            )

        if not episodes.columns.is_unique:
            raise ValueError(
                "episodes contains duplicate columns"
            )

        if not pipeline.columns.is_unique:
            raise ValueError(
                "pipeline contains duplicate columns"
            )

        missing_episodes = (
            cls.REQUIRED_EPISODE_COLUMNS
            -
            set(
                episodes.columns
            )
        )

        if missing_episodes:
            raise ValueError(
                "Missing episode columns: "
                +
                ", ".join(
                    sorted(
                        missing_episodes
                    )
                )
            )

        missing_pipeline = (
            cls.REQUIRED_PIPELINE_COLUMNS
            -
            set(
                pipeline.columns
            )
        )

        if missing_pipeline:
            raise ValueError(
                "Missing causal pipeline columns: "
                +
                ", ".join(
                    sorted(
                        missing_pipeline
                    )
                )
            )

        hindsight = [
            column
            for column in pipeline.columns
            if (
                isinstance(
                    column,
                    str,
                )
                and
                column.startswith(
                    (
                        "cslabel_",
                        "izlabel_",
                    )
                )
            )
        ]

        if hindsight:
            raise ValueError(
                "Causal pipeline contains hindsight columns"
            )

        if not pipeline.empty:

            zone_safe = (
                pd.to_numeric(
                    pipeline[
                        "izctx_live_safe"
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

            research_safe = (
                pd.to_numeric(
                    pipeline[
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

            invariant = (
                pd.to_numeric(
                    pipeline[
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
                zone_safe.all()
            ):
                raise ValueError(
                    "izctx_live_safe must equal 1"
                )

            if not bool(
                research_safe.all()
            ):
                raise ValueError(
                    "research_live_safe must equal 1"
                )

            if not bool(
                invariant.all()
            ):
                raise ValueError(
                    "research_trade_ready_unchanged must equal 1"
                )

    # =========================================================================
    # Bands
    # =========================================================================

    @staticmethod
    def _distance_band(
        value: Any,
    ) -> str:

        number = (
            ResearchZoneContextOutcomeProfiler._number(
                value
            )
        )

        if not np.isfinite(
            number
        ):
            return "NO_ZONE"

        if number <= 0.0:
            return "INSIDE"

        if number <= 0.10:
            return "<=0.10 ATR"

        if number <= 0.25:
            return "0.10-0.25 ATR"

        if number <= 0.50:
            return "0.25-0.50 ATR"

        if number <= 1.00:
            return "0.50-1.00 ATR"

        return ">1.00 ATR"

    @staticmethod
    def _location(
        event_id: Any,
        inside_flag: Any,
        overlap_flag: Any,
        distance_atr: Any,
    ) -> str:

        event = (
            ResearchZoneContextOutcomeProfiler._text(
                event_id,
                "NONE",
            )
        )

        if event == "NONE":
            return "NO_ZONE"

        inside = (
            ResearchZoneContextOutcomeProfiler._number(
                inside_flag
            )
        )

        overlap = (
            ResearchZoneContextOutcomeProfiler._number(
                overlap_flag
            )
        )

        distance = (
            ResearchZoneContextOutcomeProfiler._number(
                distance_atr
            )
        )

        if (
            np.isfinite(
                inside
            )
            and
            inside >= 1.0
        ):
            return "INSIDE"

        if (
            np.isfinite(
                overlap
            )
            and
            overlap >= 1.0
        ):
            return "OVERLAP"

        if not np.isfinite(
            distance
        ):
            return "UNKNOWN"

        if distance <= 0.10:
            return "VERY_NEAR"

        if distance <= 0.25:
            return "NEAR"

        if distance <= 0.50:
            return "MODERATE"

        return "FAR"

    # =========================================================================
    # Zone relation
    # =========================================================================

    @classmethod
    def _zone_relation(
        cls,
        aligned_location: str,
        opposing_location: str,
    ) -> str:

        aligned_close = aligned_location in {
            "INSIDE",
            "OVERLAP",
            "VERY_NEAR",
            "NEAR",
        }

        opposing_close = opposing_location in {
            "INSIDE",
            "OVERLAP",
            "VERY_NEAR",
            "NEAR",
        }

        if (
            aligned_close
            and
            opposing_close
        ):
            return "BOTH_CLOSE"

        if aligned_close:
            return "ALIGNED_CLOSE"

        if opposing_close:
            return "OPPOSING_CLOSE"

        if (
            aligned_location == "NO_ZONE"
            and
            opposing_location == "NO_ZONE"
        ):
            return "NO_ZONE_CONTEXT"

        return "DISTANT_OR_MIXED"

    # =========================================================================
    # Join causal signal-time context
    # =========================================================================

    @classmethod
    def prepare(
        cls,
        episodes: pd.DataFrame,
        pipeline: pd.DataFrame,
    ) -> pd.DataFrame:

        cls._validate(
            episodes,
            pipeline,
        )

        episode_frame = episodes.copy(
            deep=True
        )

        pipeline_frame = pipeline.copy(
            deep=True
        )

        episode_frame[
            "_rzco_signal_time"
        ] = cls._time_series(
            episode_frame,
            "first_signal_time",
        )

        pipeline_frame[
            "_rzco_signal_time"
        ] = cls._time_series(
            pipeline_frame,
            "time",
        )

        if bool(
            pipeline_frame[
                "_rzco_signal_time"
            ].duplicated().any()
        ):
            raise ValueError(
                "Pipeline contains duplicate signal times"
            )

        context_columns = [
            "_rzco_signal_time",

            "izctx_active_bullish_count",
            "izctx_active_bearish_count",

            "izctx_bullish_event_id",
            "izctx_bullish_state",
            "izctx_bullish_distance_atr",
            "izctx_bullish_inside_flag",
            "izctx_bullish_overlap_flag",

            "izctx_bearish_event_id",
            "izctx_bearish_state",
            "izctx_bearish_distance_atr",
            "izctx_bearish_inside_flag",
            "izctx_bearish_overlap_flag",

            "izctx_version",
            "izctx_mode",
        ]

        available_context_columns = [
            column
            for column in context_columns
            if column in pipeline_frame.columns
        ]

        joined = episode_frame.merge(
            pipeline_frame[
                available_context_columns
            ],
            how="left",
            on="_rzco_signal_time",
            validate="many_to_one",
            indicator="_rzco_join",
        )

        joined[
            "zone_context_matched"
        ] = (
            joined[
                "_rzco_join"
            ]
            .eq(
                "both"
            )
            .astype(
                int
            )
        )

        # ---------------------------------------------------------------------
        # Matured outcome population only.
        # ---------------------------------------------------------------------

        joined = joined.loc[
            joined[
                "first_status"
            ]
            .astype(
                "string"
            )
            .str
            .upper()
            .eq(
                "MATURED_20"
            )
        ].copy()

        # ---------------------------------------------------------------------
        # Direction-relative context.
        # ---------------------------------------------------------------------

        aligned_event: list[str] = []
        aligned_state: list[str] = []
        aligned_distance: list[float] = []
        aligned_inside: list[int] = []
        aligned_overlap: list[int] = []
        aligned_count: list[float] = []

        opposing_event: list[str] = []
        opposing_state: list[str] = []
        opposing_distance: list[float] = []
        opposing_inside: list[int] = []
        opposing_overlap: list[int] = []
        opposing_count: list[float] = []

        for _, row in joined.iterrows():

            direction = cls._text(
                row.get(
                    "direction"
                )
            )

            if direction == "LONG":

                aligned_prefix = "bullish"
                opposing_prefix = "bearish"

            elif direction == "SHORT":

                aligned_prefix = "bearish"
                opposing_prefix = "bullish"

            else:

                aligned_prefix = "bullish"
                opposing_prefix = "bearish"

            aligned_event.append(
                cls._text(
                    row.get(
                        f"izctx_{aligned_prefix}_event_id"
                    ),
                    "NONE",
                )
            )

            aligned_state.append(
                cls._text(
                    row.get(
                        f"izctx_{aligned_prefix}_state"
                    ),
                    "NONE",
                )
            )

            aligned_distance.append(
                cls._number(
                    row.get(
                        f"izctx_{aligned_prefix}_distance_atr"
                    )
                )
            )

            aligned_inside.append(
                int(
                    cls._number(
                        row.get(
                            f"izctx_{aligned_prefix}_inside_flag"
                        )
                    )
                    >=
                    1.0
                )
            )

            aligned_overlap.append(
                int(
                    cls._number(
                        row.get(
                            f"izctx_{aligned_prefix}_overlap_flag"
                        )
                    )
                    >=
                    1.0
                )
            )

            aligned_count.append(
                cls._number(
                    row.get(
                        f"izctx_active_{aligned_prefix}_count"
                    )
                )
            )

            opposing_event.append(
                cls._text(
                    row.get(
                        f"izctx_{opposing_prefix}_event_id"
                    ),
                    "NONE",
                )
            )

            opposing_state.append(
                cls._text(
                    row.get(
                        f"izctx_{opposing_prefix}_state"
                    ),
                    "NONE",
                )
            )

            opposing_distance.append(
                cls._number(
                    row.get(
                        f"izctx_{opposing_prefix}_distance_atr"
                    )
                )
            )

            opposing_inside.append(
                int(
                    cls._number(
                        row.get(
                            f"izctx_{opposing_prefix}_inside_flag"
                        )
                    )
                    >=
                    1.0
                )
            )

            opposing_overlap.append(
                int(
                    cls._number(
                        row.get(
                            f"izctx_{opposing_prefix}_overlap_flag"
                        )
                    )
                    >=
                    1.0
                )
            )

            opposing_count.append(
                cls._number(
                    row.get(
                        f"izctx_active_{opposing_prefix}_count"
                    )
                )
            )

        joined[
            "aligned_zone_event_id"
        ] = aligned_event

        joined[
            "aligned_zone_state"
        ] = aligned_state

        joined[
            "aligned_distance_atr"
        ] = aligned_distance

        joined[
            "aligned_inside_flag"
        ] = aligned_inside

        joined[
            "aligned_overlap_flag"
        ] = aligned_overlap

        joined[
            "aligned_active_count"
        ] = aligned_count

        joined[
            "opposing_zone_event_id"
        ] = opposing_event

        joined[
            "opposing_zone_state"
        ] = opposing_state

        joined[
            "opposing_distance_atr"
        ] = opposing_distance

        joined[
            "opposing_inside_flag"
        ] = opposing_inside

        joined[
            "opposing_overlap_flag"
        ] = opposing_overlap

        joined[
            "opposing_active_count"
        ] = opposing_count

        joined[
            "aligned_distance_band"
        ] = joined[
            "aligned_distance_atr"
        ].map(
            cls._distance_band
        )

        joined[
            "opposing_distance_band"
        ] = joined[
            "opposing_distance_atr"
        ].map(
            cls._distance_band
        )

        joined[
            "aligned_location"
        ] = [
            cls._location(
                event_id=event_id,
                inside_flag=inside,
                overlap_flag=overlap,
                distance_atr=distance,
            )
            for (
                event_id,
                inside,
                overlap,
                distance,
            )
            in zip(
                joined[
                    "aligned_zone_event_id"
                ],
                joined[
                    "aligned_inside_flag"
                ],
                joined[
                    "aligned_overlap_flag"
                ],
                joined[
                    "aligned_distance_atr"
                ],
            )
        ]

        joined[
            "opposing_location"
        ] = [
            cls._location(
                event_id=event_id,
                inside_flag=inside,
                overlap_flag=overlap,
                distance_atr=distance,
            )
            for (
                event_id,
                inside,
                overlap,
                distance,
            )
            in zip(
                joined[
                    "opposing_zone_event_id"
                ],
                joined[
                    "opposing_inside_flag"
                ],
                joined[
                    "opposing_overlap_flag"
                ],
                joined[
                    "opposing_distance_atr"
                ],
            )
        ]

        joined[
            "zone_relation"
        ] = [
            cls._zone_relation(
                aligned,
                opposing,
            )
            for (
                aligned,
                opposing,
            )
            in zip(
                joined[
                    "aligned_location"
                ],
                joined[
                    "opposing_location"
                ],
            )
        ]

        joined[
            "excursion_balance"
        ] = (
            pd.to_numeric(
                joined[
                    "first_mfe_20"
                ],
                errors="coerce",
            )
            -
            pd.to_numeric(
                joined[
                    "first_mae_20"
                ],
                errors="coerce",
            )
        )

        return (
            joined.drop(
                columns=[
                    "_rzco_join",
                ],
                errors="ignore",
            )
            .reset_index(
                drop=True
            )
        )

    # =========================================================================
    # Coverage
    # =========================================================================

    @classmethod
    def coverage(
        cls,
        prepared: pd.DataFrame,
    ) -> pd.DataFrame:

        total = len(
            prepared
        )

        matched = int(
            pd.to_numeric(
                prepared.get(
                    "zone_context_matched",
                    pd.Series(
                        dtype=float
                    ),
                ),
                errors="coerce",
            )
            .fillna(
                0
            )
            .eq(
                1
            )
            .sum()
        )

        aligned_zone = int(
            prepared.get(
                "aligned_zone_event_id",
                pd.Series(
                    dtype=object
                ),
            )
            .astype(
                str
            )
            .ne(
                "NONE"
            )
            .sum()
        )

        opposing_zone = int(
            prepared.get(
                "opposing_zone_event_id",
                pd.Series(
                    dtype=object
                ),
            )
            .astype(
                str
            )
            .ne(
                "NONE"
            )
            .sum()
        )

        return pd.DataFrame(
            [
                {
                    "episodes": total,

                    "matched_context": matched,

                    "matched_pct": (
                        matched
                        /
                        total
                        *
                        100.0
                        if total
                        else 0.0
                    ),

                    "aligned_zone_present": (
                        aligned_zone
                    ),

                    "aligned_zone_pct": (
                        aligned_zone
                        /
                        total
                        *
                        100.0
                        if total
                        else 0.0
                    ),

                    "opposing_zone_present": (
                        opposing_zone
                    ),

                    "opposing_zone_pct": (
                        opposing_zone
                        /
                        total
                        *
                        100.0
                        if total
                        else 0.0
                    ),
                }
            ]
        )

    # =========================================================================
    # Profiling
    # =========================================================================

    @classmethod
    def profile(
        cls,
        prepared: pd.DataFrame,
        dimensions: Iterable[str] | None = None,
        max_dimension_count: int = 2,
        min_n: int = 5,
    ) -> pd.DataFrame:

        selected_dimensions = tuple(
            dimensions
            if dimensions is not None
            else cls.DEFAULT_DIMENSIONS
        )

        missing = [
            dimension
            for dimension in selected_dimensions
            if dimension not in prepared.columns
        ]

        if missing:
            raise ValueError(
                "Missing profile dimensions: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )

        if max_dimension_count < 1:
            raise ValueError(
                "max_dimension_count must be >= 1"
            )

        if min_n < 1:
            raise ValueError(
                "min_n must be >= 1"
            )

        total = len(
            prepared
        )

        rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        upper = min(
            max_dimension_count,
            len(
                selected_dimensions
            ),
        )

        for dimension_count in range(
            1,
            upper + 1,
        ):

            for dimension_set in combinations(
                selected_dimensions,
                dimension_count,
            ):

                grouped = prepared.groupby(
                    list(
                        dimension_set
                    ),
                    dropna=False,
                    sort=True,
                )

                for key, group in grouped:

                    if len(
                        group
                    ) < min_n:
                        continue

                    if not isinstance(
                        key,
                        tuple,
                    ):
                        key = (
                            key,
                        )

                    profile_key = " | ".join(
                        f"{dimension}={cls._text(value)}"
                        for (
                            dimension,
                            value,
                        )
                        in zip(
                            dimension_set,
                            key,
                        )
                    )

                    rows.append(
                        {
                            "profile_dimensions": (
                                "+".join(
                                    dimension_set
                                )
                            ),

                            "profile_key": (
                                profile_key
                            ),

                            "n": len(
                                group
                            ),

                            "sample_share_pct": (
                                len(
                                    group
                                )
                                /
                                total
                                *
                                100.0
                                if total
                                else 0.0
                            ),

                            "net5_med": cls._median(
                                group[
                                    "first_net_5"
                                ]
                            ),

                            "net10_med": cls._median(
                                group[
                                    "first_net_10"
                                ]
                            ),

                            "net20_med": cls._median(
                                group[
                                    "first_net_20"
                                ]
                            ),

                            "positive20_pct": (
                                pd.to_numeric(
                                    group[
                                        "first_positive_20"
                                    ],
                                    errors="coerce",
                                )
                                .dropna()
                                .mean()
                                *
                                100.0
                            ),

                            "mfe20_med": cls._median(
                                group[
                                    "first_mfe_20"
                                ]
                            ),

                            "mae20_med": cls._median(
                                group[
                                    "first_mae_20"
                                ]
                            ),

                            "excursion_balance_med": (
                                cls._median(
                                    group[
                                        "excursion_balance"
                                    ]
                                )
                            ),

                            "profiler_version": (
                                cls.VERSION
                            ),

                            "profiler_mode": (
                                cls.MODE
                            ),
                        }
                    )

        if not rows:

            return pd.DataFrame(
                columns=list(
                    cls.PROFILE_COLUMNS
                )
            )

        result = pd.DataFrame(
            rows,
            columns=list(
                cls.PROFILE_COLUMNS
            ),
        )

        return (
            result
            .sort_values(
                [
                    "net20_med",
                    "n",
                ],
                ascending=[
                    False,
                    False,
                ],
            )
            .reset_index(
                drop=True
            )
        )


research_zone_context_outcome = (
    ResearchZoneContextOutcomeProfiler()
)