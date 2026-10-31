"""
===============================================================================
Module      : research_weight_forward_ledger.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Forward-Only Shadow Validation Ledger for RWEI Scores
===============================================================================

Why this exists
---------------
ResearchOpportunityWeightEngine weights were derived from historical research.

Therefore historical candidates MUST NOT be backfilled and presented as
out-of-sample evidence.

This ledger creates a forward-validation boundary:

FIRST RUN
    latest closed candle
        ↓
    establish anchor
        ↓
    capture NOTHING historical

LATER RUNS
    only candidates with signal_time > previous anchor
        ↓
    persist RWEI A/B/C/D tier + causal context
        ↓
    evaluate future 5 / 10 / 20 candle outcomes

Safety
------
- no orders
- no trade_ready changes
- no execution
- no position modification
- no risk sizing
- no retrospective cslabel_* inputs
- signal-bar CLOSE is paper entry
- outcome starts from NEXT candle
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(
    __file__
).resolve().parents[
    2
]


DEFAULT_FORWARD_WEIGHT_LEDGER_PATH = (
    PROJECT_ROOT
    / "01_Data"
    / "Processed"
    / "pulseviper_forward_weight_ledger.csv"
)


class ResearchWeightForwardLedger:
    VERSION = "1.0"

    MODE = "FORWARD_ONLY_SHADOW_VALIDATION"

    HORIZONS = (
        5,
        10,
        20,
    )

    REQUIRED_COLUMNS = {
        "time",
        "close",

        "lei_candidate_flag",
        "lei_direction",
        "lei_entry_family",
        "lei_reference_source",
        "lei_confirmation_type",
        "lei_distance_atr",

        "confidence_score",
        "regime_state",

        "rwei_active",
        "rwei_score",
        "rwei_tier",
        "rwei_components",
        "rwei_live_safe",
        "rwei_version",
        "rwei_mode",
        "rwei_policy",

        "research_live_safe",
        "research_trade_ready_unchanged",
    }

    LEDGER_COLUMNS = (
        "event_id",

        "signal_time",

        "requested_symbol",
        "resolved_symbol",
        "timeframe",

        "direction",
        "paper_direction",

        "entry_close",

        "lei_entry_family",
        "lei_reference_source",
        "lei_confirmation_type",
        "lei_distance_atr",

        "confidence_score",
        "regime_state",

        "rwei_score",
        "rwei_tier",
        "rwei_components",
        "rwei_version",
        "rwei_mode",
        "rwei_policy",

        "forward_ledger_version",
        "forward_ledger_mode",

        "bars_available",
        "status",
        "last_evaluated_time",

        "close_5",
        "net_5",

        "close_10",
        "net_10",

        "close_20",
        "net_20",

        "mfe_20",
        "mae_20",

        "positive_20",
    )

    # =========================================================================
    # Init
    # =========================================================================

    def __init__(
        self,
        path: str | Path | None = None,
    ) -> None:

        self.path = Path(
            path
            if path is not None
            else DEFAULT_FORWARD_WEIGHT_LEDGER_PATH
        )

        self.anchor_path = self.path.with_suffix(
            self.path.suffix
            +
            ".anchor.json"
        )

    # =========================================================================
    # Helpers
    # =========================================================================

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
            text
            if text
            else default
        )

    @staticmethod
    def _timestamp(
        value: Any,
    ) -> pd.Timestamp | None:

        timestamp = pd.to_datetime(
            value,
            errors="coerce",
            utc=True,
        )

        if pd.isna(
            timestamp
        ):
            return None

        return pd.Timestamp(
            timestamp
        ).tz_convert(
            None
        )

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
    def _normalize(
        cls,
        frame: pd.DataFrame,
    ) -> pd.DataFrame:

        result = frame.copy().reindex(
            columns=list(
                cls.LEDGER_COLUMNS
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

    @staticmethod
    def _event_id(
        symbol: str,
        timeframe: str,
        signal_time: pd.Timestamp,
        direction: str,
        family: str,
        rwei_version: str,
        rwei_policy: str,
    ) -> str:

        identity = "|".join(
            (
                symbol.upper(),
                timeframe.upper(),

                signal_time.strftime(
                    "%Y-%m-%dT%H:%M:%S"
                ),

                direction.upper(),
                family.upper(),

                rwei_version,
                rwei_policy,
            )
        )

        return hashlib.sha1(
            identity.encode(
                "utf-8"
            )
        ).hexdigest()[
            :20
        ]

    # =========================================================================
    # Safety validation
    # =========================================================================

    @classmethod
    def _validate_input(
        cls,
        frame: pd.DataFrame,
    ) -> None:

        if not isinstance(
            frame,
            pd.DataFrame,
        ):
            raise TypeError(
                "Forward weight input must be a pandas DataFrame"
            )

        if not frame.columns.is_unique:
            raise ValueError(
                "Forward weight input contains duplicate columns"
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
                "Missing forward weight columns: "
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

        research_safe = (
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
            research_safe.all()
        ):
            raise ValueError(
                "Forward ledger requires research_live_safe == 1"
            )

        rwei_safe = (
            pd.to_numeric(
                frame[
                    "rwei_live_safe"
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
            rwei_safe.all()
        ):
            raise ValueError(
                "Forward ledger requires rwei_live_safe == 1"
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
                "Forward ledger requires "
                "research_trade_ready_unchanged == 1"
            )

    # =========================================================================
    # Forward anchor
    # =========================================================================

    def load_anchor(
        self,
    ) -> pd.Timestamp | None:

        if not self.anchor_path.exists():
            return None

        payload = json.loads(
            self.anchor_path.read_text(
                encoding="utf-8"
            )
        )

        return self._timestamp(
            payload.get(
                "anchor_time"
            )
        )

    def save_anchor(
        self,
        anchor_time: Any,
    ) -> pd.Timestamp:

        timestamp = self._timestamp(
            anchor_time
        )

        if timestamp is None:
            raise ValueError(
                "Invalid forward anchor time"
            )

        self.anchor_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = {
            "anchor_time": (
                timestamp.isoformat()
            ),

            "forward_ledger_version": (
                self.VERSION
            ),

            "forward_ledger_mode": (
                self.MODE
            ),
        }

        temporary = self.anchor_path.with_suffix(
            self.anchor_path.suffix
            +
            ".tmp"
        )

        temporary.write_text(
            json.dumps(
                payload,
                indent=2,
            ),
            encoding="utf-8",
        )

        temporary.replace(
            self.anchor_path
        )

        return timestamp

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
            self._normalize(
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

        result = (
            self._normalize(
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

        result.to_csv(
            temporary,
            index=False,
        )

        temporary.replace(
            self.path
        )

    # =========================================================================
    # Forward-only capture
    # =========================================================================

    def capture_after_anchor(
        self,
        frame: pd.DataFrame,
        anchor_time: Any,
        requested_symbol: str,
        resolved_symbol: str,
        timeframe: str = "M1",
    ) -> pd.DataFrame:

        self._validate_input(
            frame
        )

        anchor = self._timestamp(
            anchor_time
        )

        if anchor is None:
            raise ValueError(
                "Forward capture requires a valid anchor"
            )

        times = pd.to_datetime(
            frame[
                "time"
            ],
            errors="coerce",
            utc=True,
        ).dt.tz_convert(
            None
        )

        candidate = (
            pd.to_numeric(
                frame[
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

        weighted = (
            pd.to_numeric(
                frame[
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
        )

        new_time = times.gt(
            anchor
        )

        selected = frame.loc[
            candidate
            &
            weighted
            &
            new_time
        ].copy()

        if selected.empty:
            return self._empty_frame()

        selected[
            "_forward_time"
        ] = times.loc[
            selected.index
        ]

        rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for _, row in selected.iterrows():

            signal_time = self._timestamp(
                row.get(
                    "_forward_time"
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

            family = self._text(
                row.get(
                    "lei_entry_family"
                ),
                "NONE",
            ).upper()

            rwei_version = self._text(
                row.get(
                    "rwei_version"
                ),
                "UNKNOWN",
            )

            rwei_policy = self._text(
                row.get(
                    "rwei_policy"
                ),
                "UNKNOWN",
            )

            # Explicit Any annotation is intentional:
            # the record contains strings, timestamps,
            # integers and floating-point values.
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
                        resolved_symbol,
                        timeframe,
                        signal_time,
                        direction,
                        family,
                        rwei_version,
                        rwei_policy,
                    ),

                    "signal_time": (
                        signal_time
                    ),

                    "requested_symbol": (
                        requested_symbol
                    ),

                    "resolved_symbol": (
                        resolved_symbol
                    ),

                    "timeframe": (
                        timeframe
                    ),

                    "direction": (
                        direction
                    ),

                    "paper_direction": (
                        "BULLISH"
                        if direction == "LONG"
                        else
                        "BEARISH"
                    ),

                    # Forward paper entry is signal close.
                    "entry_close": self._number(
                        row.get(
                            "close"
                        )
                    ),

                    "lei_entry_family": (
                        family
                    ),

                    "lei_reference_source": self._text(
                        row.get(
                            "lei_reference_source"
                        )
                    ),

                    "lei_confirmation_type": self._text(
                        row.get(
                            "lei_confirmation_type"
                        )
                    ),

                    "lei_distance_atr": self._number(
                        row.get(
                            "lei_distance_atr"
                        )
                    ),

                    "confidence_score": self._number(
                        row.get(
                            "confidence_score"
                        )
                    ),

                    "regime_state": self._text(
                        row.get(
                            "regime_state"
                        )
                    ),

                    "rwei_score": self._number(
                        row.get(
                            "rwei_score"
                        )
                    ),

                    "rwei_tier": self._text(
                        row.get(
                            "rwei_tier"
                        ),
                        "NONE",
                    ).upper(),

                    "rwei_components": self._text(
                        row.get(
                            "rwei_components"
                        ),
                        "NONE",
                    ),

                    "rwei_version": (
                        rwei_version
                    ),

                    "rwei_mode": self._text(
                        row.get(
                            "rwei_mode"
                        )
                    ),

                    "rwei_policy": (
                        rwei_policy
                    ),

                    "forward_ledger_version": (
                        self.VERSION
                    ),

                    "forward_ledger_mode": (
                        self.MODE
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

        return self._normalize(
            pd.DataFrame(
                rows
            )
        )

    # =========================================================================
    # Merge
    # =========================================================================

    def merge(
        self,
        existing: pd.DataFrame,
        incoming: pd.DataFrame,
    ) -> tuple[
        pd.DataFrame,
        int,
    ]:

        current = self._normalize(
            existing
        )

        new = self._normalize(
            incoming
        )

        if new.empty:
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

        new = new.loc[
            ~new[
                "event_id"
            ]
            .astype(
                str
            )
            .isin(
                known
            )
        ].copy()

        if new.empty:
            return (
                current,
                0,
            )

        combined = (
            new
            if current.empty
            else pd.concat(
                [
                    current,
                    new,
                ],
                ignore_index=True,
            )
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
            self._normalize(
                combined
            ),
            len(
                new
            ),
        )

    # =========================================================================
    # Outcome helpers
    # =========================================================================

    @staticmethod
    def _favorable(
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
    def _adverse(
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
                "Missing forward outcome columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )

        result = self._normalize(
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
        ).dt.tz_convert(
            None
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

        positions = {
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
                signal_time not in positions
            ):
                continue

            position = positions[
                signal_time
            ]

            entry = self._number(
                result.at[
                    ledger_index,
                    "entry_close",
                ]
            )

            if not np.isfinite(
                entry
            ):
                continue

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

            result.at[
                ledger_index,
                "bars_available",
            ] = min(
                available,
                20,
            )

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

            for horizon in self.HORIZONS:

                if available < horizon:
                    continue

                future_close = self._number(
                    data.iloc[
                        position
                        +
                        horizon
                    ][
                        "close"
                    ]
                )

                result.at[
                    ledger_index,
                    f"close_{horizon}",
                ] = future_close

                result.at[
                    ledger_index,
                    f"net_{horizon}",
                ] = (
                    sign
                    *
                    (
                        future_close
                        -
                        entry
                    )
                )

            if available >= 20:

                future20 = data.iloc[
                    position + 1
                    :
                    position + 21
                ]

                favorable = self._favorable(
                    direction,
                    entry,
                    future20,
                )

                adverse = self._adverse(
                    direction,
                    entry,
                    future20,
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

                if finite_favorable.size:

                    result.at[
                        ledger_index,
                        "mfe_20",
                    ] = max(
                        0.0,
                        float(
                            np.max(
                                finite_favorable
                            )
                        ),
                    )

                if finite_adverse.size:

                    result.at[
                        ledger_index,
                        "mae_20",
                    ] = max(
                        0.0,
                        float(
                            np.max(
                                finite_adverse
                            )
                        ),
                    )

                net20 = self._number(
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

        return self._normalize(
            result
        )

    # =========================================================================
    # Tier performance
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
    def _positive_pct(
        frame: pd.DataFrame,
    ) -> float:

        values = pd.to_numeric(
            frame[
                "positive_20"
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
    def tier_dashboard(
        cls,
        ledger: pd.DataFrame,
    ) -> pd.DataFrame:

        matured = ledger.loc[
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

        rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for tier in (
            "A",
            "B",
            "C",
            "D",
        ):

            frame = matured.loc[
                matured[
                    "rwei_tier"
                ]
                .astype(
                    str
                )
                .str
                .upper()
                .eq(
                    tier
                )
            ]

            rows.append(
                {
                    "tier": tier,

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

                    "positive20_pct": (
                        cls._positive_pct(
                            frame
                        )
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


research_weight_forward_ledger = (
    ResearchWeightForwardLedger()
)