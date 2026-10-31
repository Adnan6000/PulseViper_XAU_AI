"""
===============================================================================
Module      : research_candidate_episode.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Causal Research Candidate Episode / Opportunity Compression
===============================================================================

Problem
-------
LEI can emit the same directional thesis on several nearby M1 candles.

Example:

SHORT BREAK_ACCEPTANCE
SHORT BREAK_ACCEPTANCE
SHORT BREAK_ACCEPTANCE
SHORT BREAK_ACCEPTANCE

These are not necessarily four independent trading opportunities.

Purpose
-------
Compress nearby, structurally equivalent research-candidate streaks into one
research opportunity episode.

Episode identity
----------------
Two consecutive candidate rows belong to the same episode when:

1. direction is unchanged
2. LEI entry family is unchanged
3. liquidity interpretation is unchanged
4. LEI reference source is unchanged
5. LEI confirmation type is unchanged
6. time gap is <= max_gap_minutes

Important
---------
This is intentionally called an EPISODE rather than "same exact level".

The current candidate ledger does not persist a canonical liquidity level ID,
so this module does NOT invent an arbitrary XAUUSD price-distance threshold.

Safety
------
- research only
- no orders
- no trade_ready modification
- no Confidence modification
- no future information used to FORM an episode
- outcome columns are only read after episode construction
"""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
import pandas as pd


class ResearchCandidateEpisodeAnalyzer:
    VERSION = "1.0"

    MODE = "RESEARCH_CANDIDATE_EPISODE_ANALYSIS_ONLY"

    DEFAULT_MAX_GAP_MINUTES = 3

    REQUIRED_COLUMNS = {
        "event_id",
        "signal_time",
        "direction",
        "lei_entry_family",
        "lei_reference_source",
        "lei_confirmation_type",
        "liqintel_event_interpretation",
        "status",
    }

    EPISODE_COLUMNS = (
        "episode_id",
        "episode_version",
        "episode_mode",

        "episode_start",
        "episode_end",
        "episode_span_minutes",
        "candidate_count",

        "direction",
        "lei_entry_family",
        "liqintel_event_interpretation",
        "lei_reference_source",
        "lei_confirmation_type",

        "first_event_id",
        "first_signal_time",
        "last_signal_time",

        "first_entry_close",
        "first_reference_price",
        "first_distance_atr",

        "first_confidence_score",
        "median_confidence_score",

        "first_production_ready_overlap",
        "any_production_ready_overlap",

        "first_mdc_state",
        "first_regime_state",

        "first_status",

        "first_net_5",
        "first_net_10",
        "first_net_20",

        "first_mfe_20",
        "first_mae_20",

        "first_positive_20",

        "first_fp_1_result",
        "first_fp_2_result",
        "first_fp_3_result",
        "first_fp_5_result",
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
        ).strip()

        return (
            text.upper()
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

    @classmethod
    def _validate(
        cls,
        ledger: pd.DataFrame,
    ) -> None:

        if not isinstance(
            ledger,
            pd.DataFrame,
        ):
            raise TypeError(
                "Research candidate episode input "
                "must be a pandas DataFrame"
            )

        missing = (
            cls.REQUIRED_COLUMNS
            -
            set(
                ledger.columns
            )
        )

        if missing:
            raise ValueError(
                "Missing research candidate episode columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )

        if not ledger.columns.is_unique:
            raise ValueError(
                "Research candidate episode input "
                "contains duplicate column names"
            )

    @classmethod
    def _episode_key(
        cls,
        row: pd.Series,
    ) -> tuple[
        str,
        str,
        str,
        str,
        str,
    ]:

        return (
            cls._text(
                row.get(
                    "direction"
                )
            ),

            cls._text(
                row.get(
                    "lei_entry_family"
                )
            ),

            cls._text(
                row.get(
                    "liqintel_event_interpretation"
                )
            ),

            cls._text(
                row.get(
                    "lei_reference_source"
                )
            ),

            cls._text(
                row.get(
                    "lei_confirmation_type"
                )
            ),
        )

    @classmethod
    def _episode_id(
        cls,
        first_event_id: str,
        key: tuple[
            str,
            str,
            str,
            str,
            str,
        ],
    ) -> str:

        identity = "|".join(
            (
                first_event_id,
                *key,
            )
        )

        return hashlib.sha1(
            identity.encode(
                "utf-8"
            )
        ).hexdigest()[
            :20
        ]

    @staticmethod
    def _value(
        row: pd.Series,
        column: str,
        default: Any = np.nan,
    ) -> Any:

        if column not in row.index:
            return default

        return row.get(
            column,
            default,
        )

    # =========================================================================
    # Episode construction
    # =========================================================================

    @classmethod
    def build(
        cls,
        ledger: pd.DataFrame,
        max_gap_minutes: int = DEFAULT_MAX_GAP_MINUTES,
    ) -> pd.DataFrame:
        """
        Build causal candidate episodes.

        Episode membership uses only current/past candidate metadata and time.
        Outcome columns are copied only after the episode boundaries exist.
        """

        cls._validate(
            ledger
        )

        if max_gap_minutes < 1:
            raise ValueError(
                "max_gap_minutes must be >= 1"
            )

        if ledger.empty:
            return pd.DataFrame(
                columns=list(
                    cls.EPISODE_COLUMNS
                )
            )

        data = ledger.copy()

        data[
            "signal_time"
        ] = pd.to_datetime(
            data[
                "signal_time"
            ],
            errors="coerce",
            utc=True,
        )

        data = (
            data
            .dropna(
                subset=[
                    "signal_time",
                ]
            )
            .sort_values(
                "signal_time"
            )
            .reset_index(
                drop=True
            )
        )

        if data.empty:
            return pd.DataFrame(
                columns=list(
                    cls.EPISODE_COLUMNS
                )
            )

        episode_numbers: list[int] = []

        current_episode = 0

        previous_time: pd.Timestamp | None = None

        previous_key: tuple[
            str,
            str,
            str,
            str,
            str,
        ] | None = None

        for index in range(
            len(
                data
            )
        ):

            row = data.iloc[
                index
            ]

            current_time = pd.Timestamp(
                row[
                    "signal_time"
                ]
            )

            current_key = cls._episode_key(
                row
            )

            same_episode = False

            if (
                previous_time is not None
                and
                previous_key is not None
                and
                current_key == previous_key
            ):

                gap_minutes = (
                    current_time
                    -
                    previous_time
                ).total_seconds() / 60.0

                same_episode = bool(
                    0.0
                    <=
                    gap_minutes
                    <=
                    float(
                        max_gap_minutes
                    )
                )

            if not same_episode:
                current_episode += 1

            episode_numbers.append(
                current_episode
            )

            previous_time = (
                current_time
            )

            previous_key = (
                current_key
            )

        data[
            "_episode_number"
        ] = episode_numbers

        rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for _, episode in data.groupby(
            "_episode_number",
            sort=True,
        ):

            episode = (
                episode
                .sort_values(
                    "signal_time"
                )
                .reset_index(
                    drop=True
                )
            )

            first = episode.iloc[
                0
            ]

            last = episode.iloc[
                -1
            ]

            first_time = pd.Timestamp(
                first[
                    "signal_time"
                ]
            )

            last_time = pd.Timestamp(
                last[
                    "signal_time"
                ]
            )

            key = cls._episode_key(
                first
            )

            first_event_id = cls._text(
                first.get(
                    "event_id"
                ),
                "UNKNOWN",
            )

            confidence_series = (
                episode[
                    "confidence_score"
                ]
                if (
                    "confidence_score"
                    in episode.columns
                )
                else pd.Series(
                    dtype=float
                )
            )

            production_overlap = (
                pd.to_numeric(
                    episode[
                        "production_ready_overlap"
                    ],
                    errors="coerce",
                )
                .fillna(
                    0
                )
                .eq(
                    1
                )
                if (
                    "production_ready_overlap"
                    in episode.columns
                )
                else pd.Series(
                    False,
                    index=episode.index,
                    dtype=bool,
                )
            )

            rows.append(
                {
                    "episode_id": cls._episode_id(
                        first_event_id,
                        key,
                    ),

                    "episode_version": (
                        cls.VERSION
                    ),

                    "episode_mode": (
                        cls.MODE
                    ),

                    "episode_start": (
                        first_time
                    ),

                    "episode_end": (
                        last_time
                    ),

                    "episode_span_minutes": (
                        (
                            last_time
                            -
                            first_time
                        ).total_seconds()
                        /
                        60.0
                    ),

                    "candidate_count": len(
                        episode
                    ),

                    "direction": key[
                        0
                    ],

                    "lei_entry_family": key[
                        1
                    ],

                    "liqintel_event_interpretation": key[
                        2
                    ],

                    "lei_reference_source": key[
                        3
                    ],

                    "lei_confirmation_type": key[
                        4
                    ],

                    "first_event_id": (
                        first_event_id
                    ),

                    "first_signal_time": (
                        first_time
                    ),

                    "last_signal_time": (
                        last_time
                    ),

                    "first_entry_close": cls._number(
                        cls._value(
                            first,
                            "entry_close",
                        )
                    ),

                    "first_reference_price": cls._number(
                        cls._value(
                            first,
                            "lei_reference_price",
                        )
                    ),

                    "first_distance_atr": cls._number(
                        cls._value(
                            first,
                            "lei_distance_atr",
                        )
                    ),

                    "first_confidence_score": cls._number(
                        cls._value(
                            first,
                            "confidence_score",
                        )
                    ),

                    "median_confidence_score": cls._median(
                        confidence_series
                    ),

                    "first_production_ready_overlap": int(
                        cls._number(
                            cls._value(
                                first,
                                "production_ready_overlap",
                                0,
                            )
                        )
                        ==
                        1.0
                    ),

                    "any_production_ready_overlap": int(
                        production_overlap.any()
                    ),

                    "first_mdc_state": cls._text(
                        cls._value(
                            first,
                            "mdc_state",
                        )
                    ),

                    "first_regime_state": cls._text(
                        cls._value(
                            first,
                            "regime_state",
                        )
                    ),

                    "first_status": cls._text(
                        cls._value(
                            first,
                            "status",
                        )
                    ),

                    "first_net_5": cls._number(
                        cls._value(
                            first,
                            "net_5",
                        )
                    ),

                    "first_net_10": cls._number(
                        cls._value(
                            first,
                            "net_10",
                        )
                    ),

                    "first_net_20": cls._number(
                        cls._value(
                            first,
                            "net_20",
                        )
                    ),

                    "first_mfe_20": cls._number(
                        cls._value(
                            first,
                            "mfe_20",
                        )
                    ),

                    "first_mae_20": cls._number(
                        cls._value(
                            first,
                            "mae_20",
                        )
                    ),

                    "first_positive_20": cls._number(
                        cls._value(
                            first,
                            "positive_20",
                        )
                    ),

                    "first_fp_1_result": cls._text(
                        cls._value(
                            first,
                            "fp_1_result",
                        )
                    ),

                    "first_fp_2_result": cls._text(
                        cls._value(
                            first,
                            "fp_2_result",
                        )
                    ),

                    "first_fp_3_result": cls._text(
                        cls._value(
                            first,
                            "fp_3_result",
                        )
                    ),

                    "first_fp_5_result": cls._text(
                        cls._value(
                            first,
                            "fp_5_result",
                        )
                    ),
                }
            )

        return pd.DataFrame(
            rows,
            columns=list(
                cls.EPISODE_COLUMNS
            ),
        )

    # =========================================================================
    # Analysis
    # =========================================================================

    @staticmethod
    def _metric_median(
        frame: pd.DataFrame,
        column: str,
    ) -> float:

        if (
            frame.empty
            or
            column not in frame.columns
        ):
            return np.nan

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
    def _metric_percent(
        frame: pd.DataFrame,
        column: str,
    ) -> float:

        if (
            frame.empty
            or
            column not in frame.columns
        ):
            return np.nan

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
    def compression_summary(
        cls,
        ledger: pd.DataFrame,
        episodes: pd.DataFrame,
    ) -> pd.DataFrame:

        cls._validate(
            ledger
        )

        raw_count = len(
            ledger
        )

        episode_count = len(
            episodes
        )

        repeated = max(
            0,
            raw_count
            -
            episode_count,
        )

        compression_pct = (
            (
                repeated
                /
                raw_count
            )
            *
            100.0
            if raw_count
            else 0.0
        )

        candidate_counts = (
            pd.to_numeric(
                episodes[
                    "candidate_count"
                ],
                errors="coerce",
            )
            .dropna()
            if (
                not episodes.empty
                and
                "candidate_count"
                in episodes.columns
            )
            else pd.Series(
                dtype=float
            )
        )

        return pd.DataFrame(
            [
                {
                    "raw_candidates": (
                        raw_count
                    ),

                    "episodes": (
                        episode_count
                    ),

                    "repeated_candidates": (
                        repeated
                    ),

                    "compression_pct": round(
                        compression_pct,
                        3,
                    ),

                    "median_candidates_per_episode": (
                        round(
                            float(
                                candidate_counts.median()
                            ),
                            3,
                        )
                        if not candidate_counts.empty
                        else np.nan
                    ),

                    "max_candidates_per_episode": (
                        int(
                            candidate_counts.max()
                        )
                        if not candidate_counts.empty
                        else 0
                    ),
                }
            ]
        )

    @classmethod
    def performance_dashboard(
        cls,
        episodes: pd.DataFrame,
    ) -> pd.DataFrame:

        matured = episodes.loc[
            episodes[
                "first_status"
            ]
            .astype(
                str
            )
            .eq(
                "MATURED_20"
            )
        ].copy()

        groups = [
            (
                "ALL_EPISODES",
                matured,
            ),

            (
                "LONG",
                matured.loc[
                    matured[
                        "direction"
                    ]
                    .astype(
                        str
                    )
                    .eq(
                        "LONG"
                    )
                ],
            ),

            (
                "SHORT",
                matured.loc[
                    matured[
                        "direction"
                    ]
                    .astype(
                        str
                    )
                    .eq(
                        "SHORT"
                    )
                ],
            ),
        ]

        rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for label, frame in groups:

            rows.append(
                {
                    "group": label,

                    "n": len(
                        frame
                    ),

                    "net5_med": cls._metric_median(
                        frame,
                        "first_net_5",
                    ),

                    "net10_med": cls._metric_median(
                        frame,
                        "first_net_10",
                    ),

                    "net20_med": cls._metric_median(
                        frame,
                        "first_net_20",
                    ),

                    "positive20_pct": cls._metric_percent(
                        frame,
                        "first_positive_20",
                    ),

                    "mfe20_med": cls._metric_median(
                        frame,
                        "first_mfe_20",
                    ),

                    "mae20_med": cls._metric_median(
                        frame,
                        "first_mae_20",
                    ),
                }
            )

        return pd.DataFrame(
            rows
        )

    @classmethod
    def family_dashboard(
        cls,
        episodes: pd.DataFrame,
    ) -> pd.DataFrame:

        matured = episodes.loc[
            episodes[
                "first_status"
            ]
            .astype(
                str
            )
            .eq(
                "MATURED_20"
            )
        ].copy()

        if matured.empty:
            return pd.DataFrame(
                columns=[
                    "family",
                    "n",
                    "net20_med",
                    "positive20_pct",
                    "mfe20_med",
                    "mae20_med",
                ]
            )

        rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        families = sorted(
            matured[
                "lei_entry_family"
            ]
            .fillna(
                "UNKNOWN"
            )
            .astype(
                str
            )
            .unique()
            .tolist()
        )

        for family in families:

            frame = matured.loc[
                matured[
                    "lei_entry_family"
                ]
                .astype(
                    str
                )
                .eq(
                    family
                )
            ]

            rows.append(
                {
                    "family": family,

                    "n": len(
                        frame
                    ),

                    "net20_med": cls._metric_median(
                        frame,
                        "first_net_20",
                    ),

                    "positive20_pct": cls._metric_percent(
                        frame,
                        "first_positive_20",
                    ),

                    "mfe20_med": cls._metric_median(
                        frame,
                        "first_mfe_20",
                    ),

                    "mae20_med": cls._metric_median(
                        frame,
                        "first_mae_20",
                    ),
                }
            )

        return pd.DataFrame(
            rows
        )

    @classmethod
    def confidence_dashboard(
        cls,
        episodes: pd.DataFrame,
    ) -> pd.DataFrame:

        matured = episodes.loc[
            episodes[
                "first_status"
            ]
            .astype(
                str
            )
            .eq(
                "MATURED_20"
            )
        ].copy()

        if matured.empty:
            return pd.DataFrame(
                columns=[
                    "confidence_band",
                    "n",
                    "net20_med",
                    "positive20_pct",
                    "mfe20_med",
                    "mae20_med",
                ]
            )

        scores = pd.to_numeric(
            matured[
                "first_confidence_score"
            ],
            errors="coerce",
        )

        matured[
            "_confidence_band"
        ] = pd.cut(
            scores,
            bins=[
                -np.inf,
                49.999,
                69.999,
                84.999,
                np.inf,
            ],
            labels=[
                "<50",
                "50-69",
                "70-84",
                "85+",
            ],
        )

        rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for band in (
            "<50",
            "50-69",
            "70-84",
            "85+",
        ):

            frame = matured.loc[
                matured[
                    "_confidence_band"
                ]
                .astype(
                    str
                )
                .eq(
                    band
                )
            ]

            rows.append(
                {
                    "confidence_band": band,

                    "n": len(
                        frame
                    ),

                    "net20_med": cls._metric_median(
                        frame,
                        "first_net_20",
                    ),

                    "positive20_pct": cls._metric_percent(
                        frame,
                        "first_positive_20",
                    ),

                    "mfe20_med": cls._metric_median(
                        frame,
                        "first_mfe_20",
                    ),

                    "mae20_med": cls._metric_median(
                        frame,
                        "first_mae_20",
                    ),
                }
            )

        return pd.DataFrame(
            rows
        )


research_candidate_episode_analyzer = (
    ResearchCandidateEpisodeAnalyzer()
)