"""
===============================================================================
Module      : research_telemetry.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Shadow-Only Research Intelligence Telemetry Observer
===============================================================================

Purpose
-------
Observe the causal ResearchIntelligencePipeline without influencing it.

This module measures:

- production trade_ready frequency
- research LEI candidate frequency
- production/research overlap
- LONG / SHORT candidate balance
- MDC directional states
- LEI blocking stages
- candidate families
- liquidity event context
- research context visible on production READY events

Safety contract
---------------
This module:

- does NOT place trades
- does NOT modify trade_ready
- does NOT modify Confidence
- does NOT modify SetupState
- does NOT modify BOS
- does NOT modify LEI / MDC decisions
- does NOT calculate account risk
- does NOT communicate with MT5
- rejects retrospective cslabel_* columns
- requires ResearchIntelligencePipeline live-safe metadata

It is an observer only.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


class ResearchTelemetryObserver:
    """Read-only telemetry for causal shadow research intelligence."""

    VERSION = "1.0"

    MODE = "SHADOW_RESEARCH_OBSERVER_ONLY"

    CANDIDATE_STATUSES = {
        "LONG_CANDIDATE",
        "SHORT_CANDIDATE",
    }

    REQUIRED_COLUMNS = (
        "time",
        "trade_ready",
        "mdc_state",
        "mdc_direction",
        "lei_status",
        "lei_direction",
        "lei_entry_family",
        "lei_candidate_flag",
        "research_trade_ready_unchanged",
        "research_live_safe",
    )

    EVENT_COLUMNS = (
        "time",
        "close",

        "trade_ready",
        "confidence_direction",
        "confidence_score",

        "mdc_state",
        "mdc_direction",
        "mdc_bullish_score",
        "mdc_bearish_score",
        "mdc_score_spread",
        "mdc_conflict_flag",

        "liqintel_event_interpretation",
        "liqintel_event_bias",
        "liqintel_trap_flag",
        "liqintel_breakout_attempt_flag",
        "liqintel_breakout_accepted_flag",
        "liqintel_failed_breakout_flag",

        "lei_status",
        "lei_direction",
        "lei_entry_family",
        "lei_reference_price",
        "lei_reference_source",
        "lei_reference_origin",
        "lei_level_class",
        "lei_structure_scale",
        "lei_location_valid",
        "lei_distance_atr",
        "lei_trigger_strength",
        "lei_confirmation_flag",
        "lei_confirmation_type",
        "lei_invalidation_price",
        "lei_candidate_flag",
        "lei_decision_state",

        "research_pipeline_version",
        "research_pipeline_mode",
        "research_live_safe",
    )

    # =========================================================================
    # Validation helpers
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
                "ResearchTelemetryObserver input "
                "must be a pandas DataFrame"
            )

        missing = (
            set(
                cls.REQUIRED_COLUMNS
            )
            -
            set(
                frame.columns
            )
        )

        if missing:
            raise ValueError(
                "Missing research telemetry columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )

        if not frame.columns.is_unique:
            raise ValueError(
                "Research telemetry input contains "
                "duplicate column names"
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
                "Research telemetry received forbidden "
                "retrospective cslabel_* columns: "
                +
                ", ".join(
                    hindsight
                )
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
        )

        if not bool(
            live_safe.eq(
                1
            ).all()
        ):
            raise ValueError(
                "Research telemetry requires "
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
        )

        if not bool(
            unchanged.eq(
                1
            ).all()
        ):
            raise ValueError(
                "Research telemetry requires "
                "research_trade_ready_unchanged == 1"
            )

        candidate = cls._candidate_mask(
            frame
        )

        status_candidate = (
            frame[
                "lei_status"
            ]
            .fillna(
                "NONE"
            )
            .astype(
                str
            )
            .str
            .upper()
            .isin(
                cls.CANDIDATE_STATUSES
            )
        )

        if not candidate.equals(
            status_candidate
        ):
            raise ValueError(
                "LEI candidate flag/status contract mismatch"
            )

    # =========================================================================
    # Generic helpers
    # =========================================================================

    @staticmethod
    def _flag(
        frame: pd.DataFrame,
        column: str,
    ) -> pd.Series:

        if column not in frame.columns:
            return pd.Series(
                False,
                index=frame.index,
                dtype=bool,
            )

        return (
            pd.to_numeric(
                frame[
                    column
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

    @staticmethod
    def _text(
        frame: pd.DataFrame,
        column: str,
        default: str = "NONE",
    ) -> pd.Series:

        if column not in frame.columns:
            return pd.Series(
                default,
                index=frame.index,
                dtype="object",
            )

        return (
            frame[
                column
            ]
            .fillna(
                default
            )
            .astype(
                str
            )
            .str
            .upper()
        )

    @classmethod
    def _ready_mask(
        cls,
        frame: pd.DataFrame,
    ) -> pd.Series:

        return cls._flag(
            frame,
            "trade_ready",
        )

    @classmethod
    def _candidate_mask(
        cls,
        frame: pd.DataFrame,
    ) -> pd.Series:

        return cls._flag(
            frame,
            "lei_candidate_flag",
        )

    @staticmethod
    def _percent(
        numerator: int,
        denominator: int,
    ) -> float:

        if denominator <= 0:
            return 0.0

        return round(
            (
                float(
                    numerator
                )
                /
                float(
                    denominator
                )
            )
            *
            100.0,
            3,
        )

    @staticmethod
    def _consistent_text(
        frame: pd.DataFrame,
        column: str,
        default: str = "UNKNOWN",
    ) -> str:

        if (
            frame.empty
            or
            column not in frame.columns
        ):
            return default

        values = (
            frame[
                column
            ]
            .dropna()
            .astype(
                str
            )
            .str
            .strip()
        )

        values = values.loc[
            values.ne(
                ""
            )
        ]

        unique = (
            values
            .drop_duplicates()
            .tolist()
        )

        if not unique:
            return default

        if len(
            unique
        ) == 1:
            return str(
                unique[
                    0
                ]
            )

        return "MIXED"

    # =========================================================================
    # Summary
    # =========================================================================

    @classmethod
    def summary(
        cls,
        frame: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Return one-row operational research telemetry summary.
        """

        cls._validate(
            frame
        )

        total = len(
            frame
        )

        ready = cls._ready_mask(
            frame
        )

        candidate = cls._candidate_mask(
            frame
        )

        overlap = (
            ready
            &
            candidate
        )

        ready_count = int(
            ready.sum()
        )

        candidate_count = int(
            candidate.sum()
        )

        overlap_count = int(
            overlap.sum()
        )

        ready_without_candidate = int(
            (
                ready
                &
                ~candidate
            ).sum()
        )

        candidate_without_ready = int(
            (
                candidate
                &
                ~ready
            ).sum()
        )

        lei_direction = cls._text(
            frame,
            "lei_direction",
        )

        mdc_state = cls._text(
            frame,
            "mdc_state",
        )

        lei_status = cls._text(
            frame,
            "lei_status",
        )

        long_candidates = int(
            (
                candidate
                &
                lei_direction.eq(
                    "LONG"
                )
            ).sum()
        )

        short_candidates = int(
            (
                candidate
                &
                lei_direction.eq(
                    "SHORT"
                )
            ).sum()
        )

        record: dict[str, Any] = {
            "observer_version": cls.VERSION,

            "observer_mode": cls.MODE,

            "research_pipeline_version": (
                cls._consistent_text(
                    frame,
                    "research_pipeline_version",
                )
            ),

            "research_pipeline_mode": (
                cls._consistent_text(
                    frame,
                    "research_pipeline_mode",
                )
            ),

            "total_bars": total,

            "production_ready_count": (
                ready_count
            ),

            "research_candidate_count": (
                candidate_count
            ),

            "long_candidate_count": (
                long_candidates
            ),

            "short_candidate_count": (
                short_candidates
            ),

            "ready_and_candidate_count": (
                overlap_count
            ),

            "ready_without_candidate_count": (
                ready_without_candidate
            ),

            "candidate_without_ready_count": (
                candidate_without_ready
            ),

            "ready_candidate_overlap_pct": (
                cls._percent(
                    overlap_count,
                    ready_count,
                )
            ),

            "candidate_ready_overlap_pct": (
                cls._percent(
                    overlap_count,
                    candidate_count,
                )
            ),

            "mdc_long_watch_count": int(
                mdc_state.eq(
                    "LONG_WATCH"
                ).sum()
            ),

            "mdc_short_watch_count": int(
                mdc_state.eq(
                    "SHORT_WATCH"
                ).sum()
            ),

            "mdc_hold_bullish_count": int(
                mdc_state.eq(
                    "HOLD_BULLISH"
                ).sum()
            ),

            "mdc_hold_bearish_count": int(
                mdc_state.eq(
                    "HOLD_BEARISH"
                ).sum()
            ),

            "mdc_conflict_count": int(
                mdc_state.eq(
                    "WAIT_CONFLICT"
                ).sum()
            ),

            "lei_wait_location_count": int(
                lei_status.eq(
                    "WAIT_LOCATION"
                ).sum()
            ),

            "lei_wait_trigger_count": int(
                lei_status.eq(
                    "WAIT_TRIGGER"
                ).sum()
            ),

            "lei_wait_confirmation_count": int(
                lei_status.eq(
                    "WAIT_CONFIRMATION"
                ).sum()
            ),

            "liq_trap_count": int(
                cls._flag(
                    frame,
                    "liqintel_trap_flag",
                ).sum()
            ),

            "liq_failed_breakout_count": int(
                cls._flag(
                    frame,
                    "liqintel_failed_breakout_flag",
                ).sum()
            ),

            "liq_accepted_breakout_count": int(
                cls._flag(
                    frame,
                    "liqintel_breakout_accepted_flag",
                ).sum()
            ),
        }

        return pd.DataFrame(
            [
                record,
            ]
        )

    # =========================================================================
    # Distribution tables
    # =========================================================================

    @classmethod
    def status_distribution(
        cls,
        frame: pd.DataFrame,
    ) -> pd.DataFrame:

        cls._validate(
            frame
        )

        values = cls._text(
            frame,
            "lei_status",
        )

        counts = (
            values
            .value_counts(
                dropna=False
            )
        )

        total = len(
            frame
        )

        rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for (
            status,
            count,
        ) in counts.items():

            numeric_count = int(
                count
            )

            rows.append(
                {
                    "lei_status": str(
                        status
                    ),

                    "count": numeric_count,

                    "pct": cls._percent(
                        numeric_count,
                        total,
                    ),
                }
            )

        return pd.DataFrame(
            rows,
            columns=[
                "lei_status",
                "count",
                "pct",
            ],
        )

    @classmethod
    def family_distribution(
        cls,
        frame: pd.DataFrame,
    ) -> pd.DataFrame:

        cls._validate(
            frame
        )

        candidate = cls._candidate_mask(
            frame
        )

        candidates = frame.loc[
            candidate
        ]

        if candidates.empty:
            return pd.DataFrame(
                columns=[
                    "lei_entry_family",
                    "count",
                    "pct_of_candidates",
                ]
            )

        families = (
            candidates[
                "lei_entry_family"
            ]
            .fillna(
                "NONE"
            )
            .astype(
                str
            )
            .str
            .upper()
        )

        counts = families.value_counts(
            dropna=False
        )

        total = len(
            candidates
        )

        rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for (
            family,
            count,
        ) in counts.items():

            numeric_count = int(
                count
            )

            rows.append(
                {
                    "lei_entry_family": str(
                        family
                    ),

                    "count": numeric_count,

                    "pct_of_candidates": (
                        cls._percent(
                            numeric_count,
                            total,
                        )
                    ),
                }
            )

        return pd.DataFrame(
            rows,
            columns=[
                "lei_entry_family",
                "count",
                "pct_of_candidates",
            ],
        )

    # =========================================================================
    # Candidate event view
    # =========================================================================

    @classmethod
    def candidate_events(
        cls,
        frame: pd.DataFrame,
        limit: int | None = None,
    ) -> pd.DataFrame:

        cls._validate(
            frame
        )

        if (
            limit is not None
            and
            limit <= 0
        ):
            raise ValueError(
                "limit must be greater than zero"
            )

        candidate = cls._candidate_mask(
            frame
        )

        columns = [
            column
            for column in cls.EVENT_COLUMNS
            if column in frame.columns
        ]

        result = (
            frame
            .loc[
                candidate,
                columns,
            ]
            .copy()
        )

        result[
            "production_ready_overlap"
        ] = (
            pd.to_numeric(
                result[
                    "trade_ready"
                ],
                errors="coerce",
            )
            .fillna(
                0
            )
            .eq(
                1
            )
            .astype(
                "int8"
            )
        )

        if limit is not None:
            result = result.tail(
                limit
            )

        return result.reset_index(
            drop=True
        )

    # =========================================================================
    # Production READY context
    # =========================================================================

    @classmethod
    def production_ready_context(
        cls,
        frame: pd.DataFrame,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """
        Show research intelligence that existed on production READY bars.

        This is observational only. Research did not authorize trade_ready.
        """

        cls._validate(
            frame
        )

        if (
            limit is not None
            and
            limit <= 0
        ):
            raise ValueError(
                "limit must be greater than zero"
            )

        ready = cls._ready_mask(
            frame
        )

        columns = [
            column
            for column in cls.EVENT_COLUMNS
            if column in frame.columns
        ]

        result = (
            frame
            .loc[
                ready,
                columns,
            ]
            .copy()
        )

        result[
            "research_candidate_overlap"
        ] = (
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
            .astype(
                "int8"
            )
        )

        if limit is not None:
            result = result.tail(
                limit
            )

        return result.reset_index(
            drop=True
        )


research_telemetry = (
    ResearchTelemetryObserver()
)