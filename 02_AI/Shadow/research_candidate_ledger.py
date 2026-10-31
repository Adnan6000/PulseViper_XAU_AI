"""
===============================================================================
Module      : research_candidate_ledger.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Persistent Outcome Ledger for Causal Research Entry Candidates
===============================================================================

Important
---------
This ledger evaluates LEI research candidates only.

It does NOT:
- open trades
- modify trade_ready
- authorize execution
- modify Confidence / SetupState / BOS
- assume a perfect fill at lei_reference_price
- use the signal candle as future outcome data

Paper entry
-----------
The candidate signal-bar CLOSE is used as the paper entry reference.

lei_reference_price is stored as context only. This prevents optimistic
"perfect level fill" assumptions.

Outcome window
--------------
Only candles AFTER the candidate signal are evaluated.

First-passage ambiguity
-----------------------
If the same M1 candle touches both +$X and -$X, the result is
AMBIGUOUS_SAME_BAR. Intrabar order is never guessed.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(
    __file__
).resolve().parents[
    2
]

DEFAULT_RESEARCH_CANDIDATE_LEDGER_PATH = (
    PROJECT_ROOT
    / "01_Data"
    / "Processed"
    / "pulseviper_research_candidate_ledger.csv"
)


class ResearchCandidateLedger:
    """Persistent causal research-candidate outcome ledger."""

    VERSION = "1.0"

    HORIZONS = (
        5,
        10,
        20,
    )

    TARGETS = (
        1.0,
        2.0,
        3.0,
        5.0,
    )

    BASE_COLUMNS = (
        "event_id",
        "capture_mode",
        "signal_time",
        "requested_symbol",
        "resolved_symbol",
        "timeframe",

        "direction",
        "paper_direction",

        "entry_close",

        "production_ready_overlap",

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

        "lei_status",
        "lei_entry_family",
        "lei_reference_price",
        "lei_reference_source",
        "lei_reference_origin",
        "lei_level_class",
        "lei_structure_scale",
        "lei_distance_atr",
        "lei_trigger_strength",
        "lei_confirmation_type",
        "lei_invalidation_price",

        "regime_state",
        "regime_trend",
        "regime_volatility",
        "regime_time_bucket_utc",

        "pipeline_version",
        "pipeline_mode",

        "research_pipeline_version",
        "research_pipeline_mode",

        "lei_version",

        "candidate_ledger_version",

        "bars_available",
        "status",
        "last_evaluated_time",
    )

    OUTCOME_COLUMNS = tuple(
        column
        for horizon in HORIZONS
        for column in (
            f"close_{horizon}",
            f"net_{horizon}",
            f"mfe_{horizon}",
            f"mae_{horizon}",
        )
    )

    FIRST_PASSAGE_COLUMNS = tuple(
        column
        for target in TARGETS
        for column in (
            f"fp_{int(target)}_result",
            f"fp_{int(target)}_bar",
        )
    )

    LEDGER_COLUMNS = (
        BASE_COLUMNS
        +
        OUTCOME_COLUMNS
        +
        FIRST_PASSAGE_COLUMNS
        +
        (
            "positive_20",
        )
    )

    TEXT_COLUMNS = (
        "event_id",
        "capture_mode",
        "requested_symbol",
        "resolved_symbol",
        "timeframe",

        "direction",
        "paper_direction",

        "confidence_direction",

        "mdc_state",
        "mdc_direction",

        "liqintel_event_interpretation",
        "liqintel_event_bias",

        "lei_status",
        "lei_entry_family",
        "lei_reference_source",
        "lei_reference_origin",
        "lei_level_class",
        "lei_structure_scale",
        "lei_confirmation_type",

        "regime_state",
        "regime_trend",
        "regime_volatility",
        "regime_time_bucket_utc",

        "pipeline_version",
        "pipeline_mode",

        "research_pipeline_version",
        "research_pipeline_mode",

        "lei_version",

        "candidate_ledger_version",
        "status",
    ) + tuple(
        f"fp_{int(target)}_result"
        for target in TARGETS
    )

    REQUIRED_CANDIDATE_COLUMNS = {
        "time",
        "close",
        "trade_ready",
        "lei_candidate_flag",
        "lei_status",
        "lei_direction",
        "lei_entry_family",
        "research_live_safe",
        "research_trade_ready_unchanged",
    }

    def __init__(
        self,
        path: str | Path | None = None,
    ) -> None:

        self.path = Path(
            path
            if path is not None
            else DEFAULT_RESEARCH_CANDIDATE_LEDGER_PATH
        )

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _numeric(
        value: Any,
        default: float = np.nan,
    ) -> float:

        try:
            result = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return default

        if not np.isfinite(
            result
        ):
            return default

        return result

    @staticmethod
    def _text(
        value: Any,
        default: str = "",
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

        result = str(
            value
        ).strip()

        return (
            result
            if result
            else default
        )

    @staticmethod
    def _timestamp(
        value: Any,
    ) -> pd.Timestamp | None:

        parsed = pd.to_datetime(
            value,
            errors="coerce",
            utc=True,
        )

        if pd.isna(
            parsed
        ):
            return None

        timestamp = pd.Timestamp(
            parsed
        )

        return timestamp.tz_convert(
            None
        )

    @classmethod
    def _event_id(
        cls,
        resolved_symbol: str,
        timeframe: str,
        signal_time: pd.Timestamp,
        direction: str,
        family: str,
        research_version: str,
        lei_version: str,
    ) -> str:

        identity = "|".join(
            (
                resolved_symbol.upper(),
                timeframe.upper(),

                signal_time.strftime(
                    "%Y-%m-%dT%H:%M:%S"
                ),

                direction.upper(),
                family.upper(),
                research_version,
                lei_version,
            )
        )

        return hashlib.sha1(
            identity.encode(
                "utf-8"
            )
        ).hexdigest()[
            :20
        ]

    @classmethod
    def _empty_frame(
        cls,
    ) -> pd.DataFrame:

        return pd.DataFrame(
            columns=list(
                cls.LEDGER_COLUMNS
            )
        )

    @classmethod
    def _normalize_columns(
        cls,
        frame: pd.DataFrame,
    ) -> pd.DataFrame:

        result = (
            frame
            .copy()
            .reindex(
                columns=list(
                    cls.LEDGER_COLUMNS
                )
            )
        )

        for column in cls.TEXT_COLUMNS:

            result[
                column
            ] = (
                result[
                    column
                ]
                .map(
                    lambda value:
                    None
                    if pd.isna(
                        value
                    )
                    else str(
                        value
                    )
                )
                .astype(
                    "object"
                )
            )

        for column in (
            "signal_time",
            "last_evaluated_time",
        ):

            result[
                column
            ] = pd.to_datetime(
                result[
                    column
                ],
                errors="coerce",
            )

        return result.reset_index(
            drop=True
        )

    # =========================================================================
    # Persistence
    # =========================================================================

    def load(
        self,
    ) -> pd.DataFrame:

        if not self.path.exists():
            return self._empty_frame()

        frame = pd.read_csv(
            self.path
        )

        return (
            self._normalize_columns(
                frame
            )
            .drop_duplicates(
                "event_id",
                keep="last",
            )
            .sort_values(
                "signal_time"
            )
            .reset_index(
                drop=True
            )
        )

    def save(
        self,
        frame: pd.DataFrame,
    ) -> None:

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        clean = (
            self._normalize_columns(
                frame
            )
            .drop_duplicates(
                "event_id",
                keep="last",
            )
            .sort_values(
                "signal_time"
            )
            .reset_index(
                drop=True
            )
        )

        temporary = self.path.with_suffix(
            self.path.suffix
            +
            ".tmp"
        )

        clean.to_csv(
            temporary,
            index=False,
        )

        temporary.replace(
            self.path
        )

    # =========================================================================
    # Candidate capture
    # =========================================================================

    @classmethod
    def _validate_candidate_frame(
        cls,
        enriched: pd.DataFrame,
    ) -> None:

        missing = (
            cls.REQUIRED_CANDIDATE_COLUMNS
            -
            set(
                enriched.columns
            )
        )

        if missing:
            raise ValueError(
                "Missing research candidate columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )

        hindsight = [
            column
            for column in enriched.columns
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
                "Retrospective cslabel_* columns "
                "are forbidden"
            )

        live_safe = (
            pd.to_numeric(
                enriched[
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
                "Research candidate ledger requires "
                "research_live_safe == 1"
            )

        unchanged = (
            pd.to_numeric(
                enriched[
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
                "Research candidate ledger requires "
                "research_trade_ready_unchanged == 1"
            )

    def capture_candidates(
        self,
        enriched: pd.DataFrame,
        requested_symbol: str,
        resolved_symbol: str,
        timeframe: str = "M1",
    ) -> pd.DataFrame:

        self._validate_candidate_frame(
            enriched
        )

        candidate_mask = (
            pd.to_numeric(
                enriched[
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

        rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for _, row in enriched.loc[
            candidate_mask
        ].iterrows():

            signal_time = self._timestamp(
                row.get(
                    "time"
                )
            )

            if signal_time is None:
                continue

            direction = self._text(
                row.get(
                    "lei_direction"
                ),
                "NONE",
            ).upper()

            if direction not in (
                "LONG",
                "SHORT",
            ):
                continue

            status = self._text(
                row.get(
                    "lei_status"
                ),
                "NONE",
            ).upper()

            expected_status = (
                "LONG_CANDIDATE"
                if direction == "LONG"
                else
                "SHORT_CANDIDATE"
            )

            if status != expected_status:
                continue

            family = self._text(
                row.get(
                    "lei_entry_family"
                ),
                "NONE",
            ).upper()

            research_version = self._text(
                row.get(
                    "research_pipeline_version"
                ),
                "UNKNOWN",
            )

            lei_version = self._text(
                row.get(
                    "lei_version"
                ),
                "UNKNOWN",
            )

            paper_direction = (
                "BULLISH"
                if direction == "LONG"
                else
                "BEARISH"
            )

            record: dict[
                str,
                Any,
            ] = {
                column: np.nan
                for column in self.LEDGER_COLUMNS
            }

            record.update(
                {
                    "event_id": self._event_id(
                        resolved_symbol=resolved_symbol,
                        timeframe=timeframe,
                        signal_time=signal_time,
                        direction=direction,
                        family=family,
                        research_version=research_version,
                        lei_version=lei_version,
                    ),

                    "signal_time": signal_time,

                    "requested_symbol": (
                        requested_symbol
                    ),

                    "resolved_symbol": (
                        resolved_symbol
                    ),

                    "timeframe": timeframe,

                    "direction": direction,

                    "paper_direction": (
                        paper_direction
                    ),

                    # ---------------------------------------------------------
                    # Important:
                    # immediate causal paper entry = signal close.
                    # ---------------------------------------------------------
                    "entry_close": self._numeric(
                        row.get(
                            "close"
                        )
                    ),

                    "production_ready_overlap": int(
                        self._numeric(
                            row.get(
                                "trade_ready"
                            ),
                            0.0,
                        )
                        == 1.0
                    ),

                    "confidence_direction": self._text(
                        row.get(
                            "confidence_direction"
                        ),
                        "NONE",
                    ),

                    "confidence_score": self._numeric(
                        row.get(
                            "confidence_score"
                        )
                    ),

                    "mdc_state": self._text(
                        row.get(
                            "mdc_state"
                        ),
                        "UNKNOWN",
                    ),

                    "mdc_direction": self._text(
                        row.get(
                            "mdc_direction"
                        ),
                        "UNKNOWN",
                    ),

                    "mdc_bullish_score": self._numeric(
                        row.get(
                            "mdc_bullish_score"
                        )
                    ),

                    "mdc_bearish_score": self._numeric(
                        row.get(
                            "mdc_bearish_score"
                        )
                    ),

                    "mdc_score_spread": self._numeric(
                        row.get(
                            "mdc_score_spread"
                        )
                    ),

                    "mdc_conflict_flag": self._numeric(
                        row.get(
                            "mdc_conflict_flag"
                        )
                    ),

                    "liqintel_event_interpretation": self._text(
                        row.get(
                            "liqintel_event_interpretation"
                        ),
                        "NONE",
                    ),

                    "liqintel_event_bias": self._text(
                        row.get(
                            "liqintel_event_bias"
                        ),
                        "NEUTRAL",
                    ),

                    "lei_status": status,

                    "lei_entry_family": family,

                    "lei_reference_price": self._numeric(
                        row.get(
                            "lei_reference_price"
                        )
                    ),

                    "lei_reference_source": self._text(
                        row.get(
                            "lei_reference_source"
                        ),
                        "NONE",
                    ),

                    "lei_reference_origin": self._text(
                        row.get(
                            "lei_reference_origin"
                        ),
                        "NONE",
                    ),

                    "lei_level_class": self._text(
                        row.get(
                            "lei_level_class"
                        ),
                        "UNKNOWN",
                    ),

                    "lei_structure_scale": self._text(
                        row.get(
                            "lei_structure_scale"
                        ),
                        "UNKNOWN",
                    ),

                    "lei_distance_atr": self._numeric(
                        row.get(
                            "lei_distance_atr"
                        )
                    ),

                    "lei_trigger_strength": self._numeric(
                        row.get(
                            "lei_trigger_strength"
                        )
                    ),

                    "lei_confirmation_type": self._text(
                        row.get(
                            "lei_confirmation_type"
                        ),
                        "NONE",
                    ),

                    "lei_invalidation_price": self._numeric(
                        row.get(
                            "lei_invalidation_price"
                        )
                    ),

                    "regime_state": self._text(
                        row.get(
                            "regime_state"
                        ),
                        "UNKNOWN",
                    ),

                    "regime_trend": self._text(
                        row.get(
                            "regime_trend"
                        ),
                        "UNKNOWN",
                    ),

                    "regime_volatility": self._text(
                        row.get(
                            "regime_volatility"
                        ),
                        "UNKNOWN",
                    ),

                    "regime_time_bucket_utc": self._text(
                        row.get(
                            "regime_time_bucket_utc"
                        ),
                        "UNKNOWN",
                    ),

                    "pipeline_version": self._text(
                        row.get(
                            "pipeline_version"
                        ),
                        "UNKNOWN",
                    ),

                    "pipeline_mode": self._text(
                        row.get(
                            "pipeline_mode"
                        ),
                        "UNKNOWN",
                    ),

                    "research_pipeline_version": (
                        research_version
                    ),

                    "research_pipeline_mode": self._text(
                        row.get(
                            "research_pipeline_mode"
                        ),
                        "UNKNOWN",
                    ),

                    "lei_version": lei_version,

                    "candidate_ledger_version": (
                        self.VERSION
                    ),

                    "bars_available": 0,

                    "status": "OPEN",
                }
            )

            rows.append(
                record
            )

        if not rows:
            return self._empty_frame()

        return self._normalize_columns(
            pd.DataFrame(
                rows
            )
        )

    # =========================================================================
    # Merge
    # =========================================================================

    def merge_new_candidates(
        self,
        existing: pd.DataFrame,
        candidates: pd.DataFrame,
        capture_mode: str,
    ) -> tuple[
        pd.DataFrame,
        int,
    ]:

        current = self._normalize_columns(
            existing
        )

        incoming = self._normalize_columns(
            candidates
        )

        if incoming.empty:
            return (
                current,
                0,
            )

        known = set(
            current[
                "event_id"
            ]
            .dropna()
            .astype(
                str
            )
        )

        new_rows = incoming.loc[
            ~incoming[
                "event_id"
            ]
            .astype(
                str
            )
            .isin(
                known
            )
        ].copy()

        if new_rows.empty:
            return (
                current,
                0,
            )

        new_rows[
            "capture_mode"
        ] = capture_mode

        if current.empty:
            combined = new_rows.copy()

        else:
            combined = pd.concat(
                [
                    current,
                    new_rows,
                ],
                ignore_index=True,
            )

        combined = (
            combined
            .drop_duplicates(
                "event_id",
                keep="last",
            )
            .sort_values(
                "signal_time"
            )
            .reset_index(
                drop=True
            )
        )

        return (
            self._normalize_columns(
                combined
            ),
            len(
                new_rows
            ),
        )

    # =========================================================================
    # Price-path logic
    # =========================================================================

    @staticmethod
    def _favorable_series(
        direction: str,
        entry: float,
        future: pd.DataFrame,
    ) -> np.ndarray:

        if direction == "BULLISH":

            return (
                pd.to_numeric(
                    future[
                        "high"
                    ],
                    errors="coerce",
                )
                .to_numpy(
                    dtype=float
                )
                -
                entry
            )

        return (
            entry
            -
            pd.to_numeric(
                future[
                    "low"
                ],
                errors="coerce",
            )
            .to_numpy(
                dtype=float
            )
        )

    @staticmethod
    def _adverse_series(
        direction: str,
        entry: float,
        future: pd.DataFrame,
    ) -> np.ndarray:

        if direction == "BULLISH":

            return (
                entry
                -
                pd.to_numeric(
                    future[
                        "low"
                    ],
                    errors="coerce",
                )
                .to_numpy(
                    dtype=float
                )
            )

        return (
            pd.to_numeric(
                future[
                    "high"
                ],
                errors="coerce",
            )
            .to_numpy(
                dtype=float
            )
            -
            entry
        )

    @classmethod
    def _mfe_mae(
        cls,
        direction: str,
        entry: float,
        future: pd.DataFrame,
    ) -> tuple[
        float,
        float,
    ]:

        favorable = cls._favorable_series(
            direction,
            entry,
            future,
        )

        adverse = cls._adverse_series(
            direction,
            entry,
            future,
        )

        finite_favorable = favorable[
            np.isfinite(
                favorable
            )
        ]

        finite_adverse = adverse[
            np.isfinite(
                adverse
            )
        ]

        mfe = (
            max(
                0.0,
                float(
                    np.max(
                        finite_favorable
                    )
                ),
            )
            if finite_favorable.size
            else np.nan
        )

        mae = (
            max(
                0.0,
                float(
                    np.max(
                        finite_adverse
                    )
                ),
            )
            if finite_adverse.size
            else np.nan
        )

        return (
            mfe,
            mae,
        )

    @classmethod
    def _first_passage(
        cls,
        direction: str,
        entry: float,
        future: pd.DataFrame,
        threshold: float,
    ) -> tuple[
        str,
        int | None,
    ]:

        favorable = cls._favorable_series(
            direction,
            entry,
            future,
        )

        adverse = cls._adverse_series(
            direction,
            entry,
            future,
        )

        for index in range(
            len(
                future
            )
        ):

            favorable_hit = bool(
                np.isfinite(
                    favorable[
                        index
                    ]
                )
                and
                favorable[
                    index
                ]
                >=
                threshold
            )

            adverse_hit = bool(
                np.isfinite(
                    adverse[
                        index
                    ]
                )
                and
                adverse[
                    index
                ]
                >=
                threshold
            )

            if (
                favorable_hit
                and
                adverse_hit
            ):
                return (
                    "AMBIGUOUS_SAME_BAR",
                    index + 1,
                )

            if favorable_hit:
                return (
                    "PROFIT_FIRST",
                    index + 1,
                )

            if adverse_hit:
                return (
                    "LOSS_FIRST",
                    index + 1,
                )

        return (
            "NEITHER",
            None,
        )

    # =========================================================================
    # Evaluation
    # =========================================================================

    def evaluate(
        self,
        ledger: pd.DataFrame,
        market: pd.DataFrame,
    ) -> pd.DataFrame:

        required = {
            "time",
            "high",
            "low",
            "close",
        }

        missing = (
            required
            -
            set(
                market.columns
            )
        )

        if missing:
            raise ValueError(
                "Missing candidate outcome columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )

        result = self._normalize_columns(
            ledger
        )

        if result.empty:
            return result

        data = market.copy()

        data[
            "time"
        ] = pd.to_datetime(
            data[
                "time"
            ],
            errors="coerce",
            utc=True,
        )

        data[
            "time"
        ] = (
            data[
                "time"
            ]
            .dt
            .tz_convert(
                None
            )
        )

        data = (
            data
            .dropna(
                subset=[
                    "time",
                    "high",
                    "low",
                    "close",
                ]
            )
            .drop_duplicates(
                "time",
                keep="last",
            )
            .sort_values(
                "time"
            )
            .reset_index(
                drop=True
            )
        )

        if data.empty:
            return result

        time_to_position = {
            pd.Timestamp(
                timestamp
            ): index
            for index, timestamp
            in enumerate(
                data[
                    "time"
                ].tolist()
            )
        }

        latest_time = data[
            "time"
        ].iloc[
            -1
        ]

        for ledger_index in range(
            len(
                result
            )
        ):

            signal_time = self._timestamp(
                result.at[
                    ledger_index,
                    "signal_time",
                ]
            )

            if (
                signal_time is None
                or
                signal_time
                not in time_to_position
            ):
                continue

            position = time_to_position[
                signal_time
            ]

            direction = self._text(
                result.at[
                    ledger_index,
                    "paper_direction",
                ]
            ).upper()

            if direction not in (
                "BULLISH",
                "BEARISH",
            ):
                continue

            entry = self._numeric(
                result.at[
                    ledger_index,
                    "entry_close",
                ]
            )

            if not np.isfinite(
                entry
            ):
                continue

            available = max(
                0,
                len(
                    data
                )
                -
                position
                -
                1,
            )

            capped_available = min(
                available,
                20,
            )

            result.at[
                ledger_index,
                "candidate_ledger_version",
            ] = self.VERSION

            result.at[
                ledger_index,
                "bars_available",
            ] = capped_available

            result.at[
                ledger_index,
                "last_evaluated_time",
            ] = latest_time

            result.at[
                ledger_index,
                "status",
            ] = (
                "MATURED_20"
                if available >= 20
                else
                "PARTIAL_10"
                if available >= 10
                else
                "PARTIAL_5"
                if available >= 5
                else
                "OPEN"
            )

            sign = (
                1.0
                if direction == "BULLISH"
                else
                -1.0
            )

            # -----------------------------------------------------------------
            # Standard horizons
            # -----------------------------------------------------------------

            for horizon in self.HORIZONS:

                if available < horizon:
                    continue

                future = data.iloc[
                    position + 1
                    :
                    position + horizon + 1
                ]

                horizon_close = self._numeric(
                    data.iloc[
                        position
                        +
                        horizon
                    ][
                        "close"
                    ]
                )

                net = (
                    sign
                    *
                    (
                        horizon_close
                        -
                        entry
                    )
                )

                (
                    mfe,
                    mae,
                ) = self._mfe_mae(
                    direction=direction,
                    entry=entry,
                    future=future,
                )

                result.at[
                    ledger_index,
                    f"close_{horizon}",
                ] = horizon_close

                result.at[
                    ledger_index,
                    f"net_{horizon}",
                ] = net

                result.at[
                    ledger_index,
                    f"mfe_{horizon}",
                ] = mfe

                result.at[
                    ledger_index,
                    f"mae_{horizon}",
                ] = mae

            # -----------------------------------------------------------------
            # First passage over maximum available 20-bar window
            # -----------------------------------------------------------------

            if capped_available > 0:

                future20 = data.iloc[
                    position + 1
                    :
                    position + capped_available + 1
                ]

                for target in self.TARGETS:

                    (
                        fp_result,
                        fp_bar,
                    ) = self._first_passage(
                        direction=direction,
                        entry=entry,
                        future=future20,
                        threshold=target,
                    )

                    name = int(
                        target
                    )

                    result.at[
                        ledger_index,
                        f"fp_{name}_result",
                    ] = fp_result

                    result.at[
                        ledger_index,
                        f"fp_{name}_bar",
                    ] = (
                        fp_bar
                        if fp_bar is not None
                        else np.nan
                    )

            if available >= 20:

                net20 = self._numeric(
                    result.at[
                        ledger_index,
                        "net_20",
                    ]
                )

                if np.isfinite(
                    net20
                ):
                    result.at[
                        ledger_index,
                        "positive_20",
                    ] = int(
                        net20 > 0.0
                    )

        return self._normalize_columns(
            result
        )

    # =========================================================================
    # Analysis helpers
    # =========================================================================

    @classmethod
    def matured_only(
        cls,
        ledger: pd.DataFrame,
    ) -> pd.DataFrame:

        if ledger.empty:
            return ledger.copy()

        return ledger.loc[
            ledger[
                "status"
            ]
            .astype(
                str
            )
            .eq(
                "MATURED_20"
            )
        ].copy()

    @staticmethod
    def _median(
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
    def _percentage(
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
    def performance_dashboard(
        cls,
        ledger: pd.DataFrame,
    ) -> pd.DataFrame:

        matured = cls.matured_only(
            ledger
        )

        groups: list[
            tuple[
                str,
                pd.DataFrame,
            ]
        ] = [
            (
                "ALL",
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
                ].copy(),
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
                ].copy(),
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

                    "net5_med": cls._median(
                        frame,
                        "net_5",
                    ),

                    "net10_med": cls._median(
                        frame,
                        "net_10",
                    ),

                    "net20_med": cls._median(
                        frame,
                        "net_20",
                    ),

                    "positive20_pct": cls._percentage(
                        frame,
                        "positive_20",
                    ),

                    "mfe20_med": cls._median(
                        frame,
                        "mfe_20",
                    ),

                    "mae20_med": cls._median(
                        frame,
                        "mae_20",
                    ),
                }
            )

        return pd.DataFrame(
            rows
        )

    @classmethod
    def family_dashboard(
        cls,
        ledger: pd.DataFrame,
    ) -> pd.DataFrame:

        matured = cls.matured_only(
            ledger
        )

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

        families = (
            matured[
                "lei_entry_family"
            ]
            .fillna(
                "NONE"
            )
            .astype(
                str
            )
            .unique()
        )

        for family in sorted(
            families
        ):

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

                    "net20_med": cls._median(
                        frame,
                        "net_20",
                    ),

                    "positive20_pct": cls._percentage(
                        frame,
                        "positive_20",
                    ),

                    "mfe20_med": cls._median(
                        frame,
                        "mfe_20",
                    ),

                    "mae20_med": cls._median(
                        frame,
                        "mae_20",
                    ),
                }
            )

        return pd.DataFrame(
            rows
        )

    @classmethod
    def confidence_dashboard(
        cls,
        ledger: pd.DataFrame,
    ) -> pd.DataFrame:

        matured = cls.matured_only(
            ledger
        )

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
                "confidence_score"
            ],
            errors="coerce",
        )

        bands = pd.cut(
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

        working = matured.copy()

        working[
            "_confidence_band"
        ] = bands

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

            frame = working.loc[
                working[
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

                    "net20_med": cls._median(
                        frame,
                        "net_20",
                    ),

                    "positive20_pct": cls._percentage(
                        frame,
                        "positive_20",
                    ),

                    "mfe20_med": cls._median(
                        frame,
                        "mfe_20",
                    ),

                    "mae20_med": cls._median(
                        frame,
                        "mae_20",
                    ),
                }
            )

        return pd.DataFrame(
            rows
        )

    @classmethod
    def first_passage_dashboard(
        cls,
        ledger: pd.DataFrame,
    ) -> pd.DataFrame:

        matured = cls.matured_only(
            ledger
        )

        rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for target in cls.TARGETS:

            name = int(
                target
            )

            column = (
                f"fp_{name}_result"
            )

            values = (
                matured[
                    column
                ]
                .fillna(
                    "UNKNOWN"
                )
                .astype(
                    str
                )
                if (
                    not matured.empty
                    and
                    column in matured.columns
                )
                else pd.Series(
                    dtype="object"
                )
            )

            profit = int(
                values.eq(
                    "PROFIT_FIRST"
                ).sum()
            )

            loss = int(
                values.eq(
                    "LOSS_FIRST"
                ).sum()
            )

            ambiguous = int(
                values.eq(
                    "AMBIGUOUS_SAME_BAR"
                ).sum()
            )

            neither = int(
                values.eq(
                    "NEITHER"
                ).sum()
            )

            resolved = (
                profit
                +
                loss
            )

            rows.append(
                {
                    "threshold": (
                        f"±${name}"
                    ),

                    "n": len(
                        matured
                    ),

                    "profit_first": profit,

                    "loss_first": loss,

                    "ambiguous": ambiguous,

                    "neither": neither,

                    "profit_first_resolved_pct": (
                        round(
                            (
                                profit
                                /
                                resolved
                            )
                            *
                            100.0,
                            3,
                        )
                        if resolved
                        else np.nan
                    ),
                }
            )

        return pd.DataFrame(
            rows
        )


research_candidate_ledger = (
    ResearchCandidateLedger()
)