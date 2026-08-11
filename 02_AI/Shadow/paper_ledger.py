"""
===============================================================================
Module      : paper_ledger.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Persistent shadow/paper signal ledger and causal outcome tracker
===============================================================================

Contract
--------
- Does not open trades.
- Does not modify trade_ready.
- Does not modify Confidence, SetupState, risk, or execution.
- Uses the signal-bar CLOSE only as a paper reference price.
- Evaluates outcomes only from bars that occur after the signal bar.
- Generated CSV data is stored under 01_Data/Processed by default.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_LEDGER_PATH = (
    PROJECT_ROOT
    / "01_Data"
    / "Processed"
    / "pulseviper_shadow_ledger.csv"
)


class PaperLedger:

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
        "setup_id",
        "setup_state",
        "confidence_score",
        "confidence_grade",
        "confidence_confluence",
        "entry_reference",
        "signal_atr",
        "spread_points",
        "tick_volume",
        "real_volume",
        "setup_age_bars",
        "setup_displacement_score",
        "setup_impulse_strength",
        "setup_bos_strength_atr",
        "setup_break_distance_atr",
        "setup_rejection_fill_percent",
        "setup_sweep_to_ready_bars",
        "setup_fvg_count",
        "setup_structure_alignment",
        "setup_bos_scope",
        "regime_ready",
        "regime_volatility",
        "regime_trend",
        "regime_state",
        "regime_trend_strength",
        "regime_time_bucket_utc",
        "pipeline_version",
        "pipeline_mode",
        "ledger_version",
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
            f"net_{horizon}_atr",
            f"mfe_{horizon}_atr",
            f"mae_{horizon}_atr",
        )
    )

    TARGET_COLUMNS = tuple(
        column
        for target in TARGETS
        for column in (
            f"target_{int(target)}_hit",
            f"target_{int(target)}_bars",
        )
    )

    LEDGER_COLUMNS = (
        BASE_COLUMNS
        + OUTCOME_COLUMNS
        + TARGET_COLUMNS
        + (
            "positive_20",
        )
    )

    def __init__(
        self,
        path: str | Path | None = None,
    ) -> None:

        self.path = Path(
            path
            if path is not None
            else DEFAULT_LEDGER_PATH
        )

    @staticmethod
    def _numeric(
        value: Any,
        default: float = np.nan,
    ) -> float:

        try:

            number = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return default

        if not np.isfinite(
            number
        ):

            return default

        return number

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
        """
        Convert a value to a timezone-naive pandas Timestamp.

        Invalid/missing values return None rather than pd.NaT so the static
        return contract remains precise for Pylance/Pyright.
        """

        timestamp = pd.to_datetime(
            value,
            errors="coerce",
        )

        if pd.isna(
            timestamp
        ):

            return None

        result = pd.Timestamp(
            timestamp
        )

        if result.tzinfo is not None:

            result = result.tz_convert(
                None
            )

        return result

    @classmethod
    def _event_id(
        cls,
        resolved_symbol: str,
        timeframe: str,
        signal_time: pd.Timestamp,
        direction: str,
    ) -> str:

        identity = "|".join(
            (
                resolved_symbol.upper(),
                timeframe.upper(),

                signal_time.strftime(
                    "%Y-%m-%dT%H:%M:%S"
                ),

                direction.upper(),
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

        result = frame.copy()

        for column in cls.LEDGER_COLUMNS:

            if column not in result.columns:

                result[
                    column
                ] = np.nan

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

        return result.loc[
            :,
            list(
                cls.LEDGER_COLUMNS
            ),
        ]

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

        frame = self._normalize_columns(
            frame
        )

        return (
            frame
            .drop_duplicates(
                subset=[
                    "event_id",
                ],
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

        clean = self._normalize_columns(
            frame
        )

        clean = (
            clean
            .drop_duplicates(
                subset=[
                    "event_id",
                ],
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
            + ".tmp"
        )

        clean.to_csv(
            temporary,
            index=False,
        )

        temporary.replace(
            self.path
        )

    # =========================================================================
    # Signal capture
    # =========================================================================

    def capture_signals(
        self,
        enriched: pd.DataFrame,
        requested_symbol: str,
        resolved_symbol: str,
        timeframe: str = "M1",
    ) -> pd.DataFrame:

        required = {
            "time",
            "close",
            "trade_ready",
        }

        missing = (
            required
            - set(
                enriched.columns
            )
        )

        if missing:

            raise ValueError(
                "Missing shadow signal columns: "
                + ", ".join(
                    sorted(
                        missing
                    )
                )
            )

        trade_ready = (
            pd.to_numeric(
                enriched[
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
        )

        rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for _, row in enriched.loc[
            trade_ready
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
                    "confidence_direction",
                    row.get(
                        "setup_direction",
                        "NONE",
                    ),
                ),
                default="NONE",
            ).upper()

            if direction not in (
                "BULLISH",
                "BEARISH",
            ):

                continue

            event_id = self._event_id(
                resolved_symbol=(
                    resolved_symbol
                ),
                timeframe=(
                    timeframe
                ),
                signal_time=(
                    signal_time
                ),
                direction=(
                    direction
                ),
            )

            record: dict[
                str,
                Any,
            ] = {
                column: np.nan
                for column
                in self.LEDGER_COLUMNS
            }

            record.update(
                {
                    "event_id": event_id,

                    "signal_time": signal_time,

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

                    "setup_id": self._numeric(
                        row.get(
                            "setup_id"
                        )
                    ),

                    "setup_state": self._text(
                        row.get(
                            "setup_state"
                        ),
                        "NONE",
                    ),

                    "confidence_score": self._numeric(
                        row.get(
                            "confidence_score"
                        )
                    ),

                    "confidence_grade": self._text(
                        row.get(
                            "confidence_grade"
                        ),
                        "NONE",
                    ),

                    "confidence_confluence": self._numeric(
                        row.get(
                            "confidence_confluence"
                        )
                    ),

                    "entry_reference": self._numeric(
                        row.get(
                            "close"
                        )
                    ),

                    "signal_atr": self._numeric(
                        row.get(
                            "atr",
                            row.get(
                                "regime_atr"
                            ),
                        )
                    ),

                    "spread_points": self._numeric(
                        row.get(
                            "spread"
                        )
                    ),

                    "tick_volume": self._numeric(
                        row.get(
                            "tick_volume"
                        )
                    ),

                    "real_volume": self._numeric(
                        row.get(
                            "real_volume"
                        )
                    ),

                    "setup_age_bars": self._numeric(
                        row.get(
                            "setup_age_bars"
                        )
                    ),

                    "setup_displacement_score": self._numeric(
                        row.get(
                            "setup_displacement_score"
                        )
                    ),

                    "setup_impulse_strength": self._numeric(
                        row.get(
                            "setup_impulse_strength"
                        )
                    ),

                    "setup_bos_strength_atr": self._numeric(
                        row.get(
                            "setup_bos_strength_atr"
                        )
                    ),

                    "setup_break_distance_atr": self._numeric(
                        row.get(
                            "setup_break_distance_atr"
                        )
                    ),

                    "setup_rejection_fill_percent": self._numeric(
                        row.get(
                            "setup_rejection_fill_percent"
                        )
                    ),

                    "setup_sweep_to_ready_bars": self._numeric(
                        row.get(
                            "setup_sweep_to_ready_bars"
                        )
                    ),

                    "setup_fvg_count": self._numeric(
                        row.get(
                            "setup_fvg_count"
                        )
                    ),

                    "setup_structure_alignment": self._numeric(
                        row.get(
                            "setup_structure_alignment"
                        )
                    ),

                    "setup_bos_scope": self._text(
                        row.get(
                            "setup_bos_scope"
                        ),
                        "NONE",
                    ),

                    "regime_ready": self._numeric(
                        row.get(
                            "regime_ready"
                        )
                    ),

                    "regime_volatility": self._text(
                        row.get(
                            "regime_volatility"
                        ),
                        "UNKNOWN",
                    ),

                    "regime_trend": self._text(
                        row.get(
                            "regime_trend"
                        ),
                        "UNKNOWN",
                    ),

                    "regime_state": self._text(
                        row.get(
                            "regime_state"
                        ),
                        "UNKNOWN",
                    ),

                    "regime_trend_strength": self._numeric(
                        row.get(
                            "regime_trend_strength"
                        )
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
                        )
                    ),

                    "pipeline_mode": self._text(
                        row.get(
                            "pipeline_mode"
                        )
                    ),

                    "ledger_version": (
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

    def merge_new_signals(
        self,
        existing: pd.DataFrame,
        signals: pd.DataFrame,
        capture_mode: str,
    ) -> tuple[
        pd.DataFrame,
        int,
    ]:

        current = self._normalize_columns(
            existing
        )

        incoming = self._normalize_columns(
            signals
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
            .tolist()
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
                subset=[
                    "event_id",
                ],
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
    # Outcome calculations
    # =========================================================================

    @staticmethod
    def _directional_metrics(
        direction: str,
        entry: float,
        future: pd.DataFrame,
    ) -> tuple[
        float,
        float,
    ]:

        high = pd.to_numeric(
            future[
                "high"
            ],
            errors="coerce",
        ).to_numpy(
            dtype=float
        )

        low = pd.to_numeric(
            future[
                "low"
            ],
            errors="coerce",
        ).to_numpy(
            dtype=float
        )

        if direction == "BULLISH":

            mfe = (
                np.nanmax(
                    high
                )
                - entry
            )

            mae = (
                entry
                - np.nanmin(
                    low
                )
            )

        else:

            mfe = (
                entry
                - np.nanmin(
                    low
                )
            )

            mae = (
                np.nanmax(
                    high
                )
                - entry
            )

        return (
            max(
                0.0,
                float(
                    mfe
                ),
            ),

            max(
                0.0,
                float(
                    mae
                ),
            ),
        )

    @staticmethod
    def _target_first_bar(
        direction: str,
        entry: float,
        future: pd.DataFrame,
        target: float,
    ) -> int | None:

        if direction == "BULLISH":

            reached = (
                pd.to_numeric(
                    future[
                        "high"
                    ],
                    errors="coerce",
                )
                >=
                entry
                +
                target
            )

        else:

            reached = (
                pd.to_numeric(
                    future[
                        "low"
                    ],
                    errors="coerce",
                )
                <=
                entry
                -
                target
            )

        positions = np.flatnonzero(
            reached.to_numpy(
                dtype=bool
            )
        )

        if positions.size == 0:

            return None

        return int(
            positions[
                0
            ]
            +
            1
        )

    # =========================================================================
    # Causal outcome update
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
            - set(
                market.columns
            )
        )

        if missing:

            raise ValueError(
                "Missing shadow outcome columns: "
                + ", ".join(
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
                subset=[
                    "time",
                ],
                keep="last",
            )
            .sort_values(
                "time"
            )
            .reset_index(
                drop=True
            )
        )

        time_to_position = {
            pd.Timestamp(
                timestamp
            ): position

            for position, timestamp
            in enumerate(
                data[
                    "time"
                ].tolist()
            )
        }

        latest_time = (
            data[
                "time"
            ].iloc[
                -1
            ]
            if not data.empty
            else pd.NaT
        )

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

            if signal_time is None:

                continue

            position = time_to_position.get(
                signal_time
            )

            if position is None:

                continue

            direction = self._text(
                result.at[
                    ledger_index,
                    "direction",
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
                    "entry_reference",
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

            result.at[
                ledger_index,
                "bars_available",
            ] = min(
                available,
                max(
                    self.HORIZONS
                ),
            )

            result.at[
                ledger_index,
                "last_evaluated_time",
            ] = latest_time

            if available >= 20:

                status = "MATURED_20"

            elif available >= 10:

                status = "PARTIAL_10"

            elif available >= 5:

                status = "PARTIAL_5"

            else:

                status = "OPEN"

            result.at[
                ledger_index,
                "status",
            ] = status

            signal_atr = self._numeric(
                result.at[
                    ledger_index,
                    "signal_atr",
                ]
            )

            sign = (
                1.0
                if direction
                ==
                "BULLISH"
                else -1.0
            )

            for horizon in self.HORIZONS:

                if available < horizon:

                    continue

                future = data.iloc[
                    position
                    +
                    1
                    :
                    position
                    +
                    horizon
                    +
                    1
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
                ) = self._directional_metrics(
                    direction=(
                        direction
                    ),
                    entry=(
                        entry
                    ),
                    future=(
                        future
                    ),
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

                if (
                    np.isfinite(
                        signal_atr
                    )
                    and
                    signal_atr
                    >
                    0.0
                ):

                    result.at[
                        ledger_index,
                        f"net_{horizon}_atr",
                    ] = (
                        net
                        /
                        signal_atr
                    )

                    result.at[
                        ledger_index,
                        f"mfe_{horizon}_atr",
                    ] = (
                        mfe
                        /
                        signal_atr
                    )

                    result.at[
                        ledger_index,
                        f"mae_{horizon}_atr",
                    ] = (
                        mae
                        /
                        signal_atr
                    )

            target_window_size = min(
                available,
                20,
            )

            if target_window_size > 0:

                future_for_targets = (
                    data.iloc[
                        position
                        +
                        1
                        :
                        position
                        +
                        target_window_size
                        +
                        1
                    ]
                )

                for target in self.TARGETS:

                    target_name = int(
                        target
                    )

                    first_bar = self._target_first_bar(
                        direction=(
                            direction
                        ),
                        entry=(
                            entry
                        ),
                        future=(
                            future_for_targets
                        ),
                        target=(
                            target
                        ),
                    )

                    if first_bar is not None:

                        result.at[
                            ledger_index,
                            f"target_{target_name}_hit",
                        ] = 1

                        result.at[
                            ledger_index,
                            f"target_{target_name}_bars",
                        ] = first_bar

                    elif available >= 20:

                        result.at[
                            ledger_index,
                            f"target_{target_name}_hit",
                        ] = 0

                        result.at[
                            ledger_index,
                            f"target_{target_name}_bars",
                        ] = np.nan

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
                        net20
                        >
                        0.0
                    )

        return result


paper_ledger = PaperLedger()