"""
===============================================================================
Module      : paper_ledger.py
Project     : PulseViper XAU AI
Version     : 1.1
Purpose     : Shadow signal, first-passage, BE and continuation telemetry
===============================================================================

v1.1
----
Adds research-only telemetry for:

- symmetric first-passage ordering:
      +$1 vs -$1
      +$2 vs -$2
      +$3 vs -$3
      +$5 vs -$5

- breakeven simulations activated after:
      +$1
      +$2
      +$3
      +$5

- continuation / runner telemetry:
      MFE timing
      profit giveback
      extension after target
      directional/opposing BOS
      internal/major BOS
      internal/major swings
      structure evolution
      regime evolution

Contract
--------
- Does NOT open trades.
- Does NOT modify trade_ready.
- Does NOT modify Confidence.
- Does NOT modify SetupState.
- Does NOT modify BOS.
- Does NOT modify risk or execution.
- Uses signal-bar CLOSE only as paper reference price.
- Evaluates only bars after the signal.
- Never guesses intrabar order when one M1 candle hits both thresholds.
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

    VERSION = "1.1"

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

    FIRST_PASSAGE_COLUMNS = tuple(
        column
        for target in TARGETS
        for column in (
            f"fp_{int(target)}_result",
            f"fp_{int(target)}_bar",
        )
    )

    BREAKEVEN_COLUMNS = tuple(
        column
        for target in TARGETS
        for column in (
            f"be_after_{int(target)}_status",
            f"be_after_{int(target)}_activation_bar",
            f"be_after_{int(target)}_exit_bar",
            f"be_after_{int(target)}_net_20",
        )
    )

    CONTINUATION_COLUMNS = (
        "bars_to_mfe_20",
        "giveback_20",
        "net_to_mfe_ratio_20",

        "directional_bos_count_20",
        "opposing_bos_count_20",

        "directional_bos_first_bar_20",
        "opposing_bos_first_bar_20",

        "directional_internal_bos_count_20",
        "directional_major_bos_count_20",

        "internal_swing_count_20",
        "major_swing_count_20",

        "structure_bias_5",
        "structure_bias_10",
        "structure_bias_20",

        "structure_aligned_5",
        "structure_aligned_10",
        "structure_aligned_20",

        "regime_state_5",
        "regime_state_10",
        "regime_state_20",

        "regime_trend_5",
        "regime_trend_10",
        "regime_trend_20",

        "regime_volatility_5",
        "regime_volatility_10",
        "regime_volatility_20",
    )

    EXTENSION_COLUMNS = tuple(
        column
        for target in TARGETS
        for column in (
            f"mfe_after_{int(target)}_20",
            f"extension_after_{int(target)}_20",
        )
    )

    LEDGER_COLUMNS = (
        BASE_COLUMNS
        + OUTCOME_COLUMNS
        + TARGET_COLUMNS
        + FIRST_PASSAGE_COLUMNS
        + BREAKEVEN_COLUMNS
        + CONTINUATION_COLUMNS
        + EXTENSION_COLUMNS
        + (
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
        "setup_state",
        "confidence_grade",
        "setup_bos_scope",
        "regime_volatility",
        "regime_trend",
        "regime_state",
        "regime_time_bucket_utc",
        "pipeline_version",
        "pipeline_mode",
        "ledger_version",
        "status",
    ) + tuple(
        f"fp_{int(target)}_result"
        for target in TARGETS
    ) + tuple(
        f"be_after_{int(target)}_status"
        for target in TARGETS
    ) + (
        "structure_bias_5",
        "structure_bias_10",
        "structure_bias_20",

        "regime_state_5",
        "regime_state_10",
        "regime_state_20",

        "regime_trend_5",
        "regime_trend_10",
        "regime_trend_20",

        "regime_volatility_5",
        "regime_volatility_10",
        "regime_volatility_20",
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
            value = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return default

        return (
            value
            if np.isfinite(
                value
            )
            else default
        )

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

        value = pd.to_datetime(
            value,
            errors="coerce",
        )

        if pd.isna(
            value
        ):
            return None

        value = pd.Timestamp(
            value
        )

        if value.tzinfo is not None:
            value = value.tz_convert(
                None
            )

        return value

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

        missing = [
            column
            for column in cls.LEDGER_COLUMNS
            if column not in result.columns
        ]

        if missing:

            additions: dict[
                str,
                pd.Series,
            ] = {}

            for column in missing:

                if column in cls.TEXT_COLUMNS:

                    additions[
                        column
                    ] = pd.Series(
                        [None]
                        *
                        len(
                            result
                        ),
                        index=result.index,
                        dtype="object",
                    )

                else:

                    additions[
                        column
                    ] = pd.Series(
                        np.nan,
                        index=result.index,
                        dtype="float64",
                    )

            result = pd.concat(
                [
                    result,
                    pd.DataFrame(
                        additions,
                        index=result.index,
                    ),
                ],
                axis=1,
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
            -
            set(
                enriched.columns
            )
        )

        if missing:

            raise ValueError(
                "Missing shadow signal columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )

        ready = (
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
            ready
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
                "NONE",
            ).upper()

            if direction not in (
                "BULLISH",
                "BEARISH",
            ):
                continue

            record: dict[str, Any] = {
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

        combined = (
            new_rows
            if current.empty
            else pd.concat(
                [
                    current,
                    new_rows,
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
            self._normalize_columns(
                combined
            ),
            len(
                new_rows
            ),
        )

    # =========================================================================
    # Price-path helpers
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
                    float
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
                float
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
                    float
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
                float
            )
            -
            entry
        )

    @classmethod
    def _directional_metrics(
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

        return (
            max(
                0.0,
                float(
                    np.nanmax(
                        favorable
                    )
                ),
            ),

            max(
                0.0,
                float(
                    np.nanmax(
                        adverse
                    )
                ),
            ),
        )

    @classmethod
    def _target_first_bar(
        cls,
        direction: str,
        entry: float,
        future: pd.DataFrame,
        target: float,
    ) -> int | None:

        positions = np.flatnonzero(
            cls._favorable_series(
                direction,
                entry,
                future,
            )
            >=
            target
        )

        if not positions.size:
            return None

        return int(
            positions[
                0
            ]
            +
            1
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

    @classmethod
    def _breakeven_simulation(
        cls,
        direction: str,
        entry: float,
        future20: pd.DataFrame,
        activation_target: float,
        net20: float,
    ) -> tuple[
        str,
        int | None,
        int | None,
        float,
    ]:
        """
        Activate BE when favorable price first reaches +activation_target.

        BE stop checking starts from the NEXT candle.

        We deliberately do not use the activation candle itself because
        M1 OHLC does not reveal whether target or entry was touched first.
        """

        activation_bar = cls._target_first_bar(
            direction,
            entry,
            future20,
            activation_target,
        )

        if activation_bar is None:

            return (
                "NOT_ACTIVATED",
                None,
                None,
                net20,
            )

        # activation_bar is 1-based.
        # zero_based == activation_bar is the NEXT candle.

        for zero_based in range(
            activation_bar,
            len(
                future20
            ),
        ):

            row = future20.iloc[
                zero_based
            ]

            low = cls._numeric(
                row.get(
                    "low"
                )
            )

            high = cls._numeric(
                row.get(
                    "high"
                )
            )

            if direction == "BULLISH":

                stop_hit = bool(
                    np.isfinite(
                        low
                    )
                    and
                    low
                    <=
                    entry
                )

            else:

                stop_hit = bool(
                    np.isfinite(
                        high
                    )
                    and
                    high
                    >=
                    entry
                )

            if stop_hit:

                return (
                    "STOPPED_BE",
                    activation_bar,
                    zero_based + 1,
                    0.0,
                )

        return (
            "HELD_20",
            activation_bar,
            None,
            net20,
        )

    @classmethod
    def _bars_to_mfe(
        cls,
        direction: str,
        entry: float,
        future: pd.DataFrame,
    ) -> int | None:

        favorable = cls._favorable_series(
            direction,
            entry,
            future,
        )

        if (
            not favorable.size
            or
            not np.isfinite(
                favorable
            ).any()
        ):
            return None

        return int(
            np.nanargmax(
                favorable
            )
            +
            1
        )

    @classmethod
    def _mfe_after_activation(
        cls,
        direction: str,
        entry: float,
        future20: pd.DataFrame,
        activation_bar: int | None,
    ) -> float:

        if activation_bar is None:
            return np.nan

        remaining = future20.iloc[
            max(
                0,
                activation_bar
                -
                1,
            ):
        ]

        favorable = cls._favorable_series(
            direction,
            entry,
            remaining,
        )

        if (
            not favorable.size
            or
            not np.isfinite(
                favorable
            ).any()
        ):
            return np.nan

        return max(
            0.0,
            float(
                np.nanmax(
                    favorable
                )
            ),
        )

    @staticmethod
    def _structure_aligned(
        direction: str,
        bias: str,
    ) -> int:

        return int(
            (
                direction.upper(),
                bias.upper(),
            )
            in (
                (
                    "BULLISH",
                    "BULLISH",
                ),
                (
                    "BEARISH",
                    "BEARISH",
                ),
            )
        )

    @staticmethod
    def _first_true_bar(
        mask: pd.Series,
    ) -> int | None:

        positions = np.flatnonzero(
            mask.to_numpy(
                dtype=bool
            )
        )

        if not positions.size:
            return None

        return int(
            positions[
                0
            ]
            +
            1
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
                "Missing shadow outcome columns: "
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
                "ledger_version",
            ] = self.VERSION

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

            # =================================================================
            # Standard 5 / 10 / 20 outcomes
            # =================================================================

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
                ) = self._directional_metrics(
                    direction,
                    entry,
                    future,
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
                    signal_atr > 0
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

            # =================================================================
            # Target + first passage
            # =================================================================

            target_window_size = min(
                available,
                20,
            )

            if target_window_size <= 0:
                continue

            future_targets = data.iloc[
                position + 1
                :
                position
                +
                target_window_size
                +
                1
            ]

            for target in self.TARGETS:

                name = int(
                    target
                )

                first_bar = self._target_first_bar(
                    direction,
                    entry,
                    future_targets,
                    target,
                )

                if first_bar is not None:

                    result.at[
                        ledger_index,
                        f"target_{name}_hit",
                    ] = 1

                    result.at[
                        ledger_index,
                        f"target_{name}_bars",
                    ] = first_bar

                elif available >= 20:

                    result.at[
                        ledger_index,
                        f"target_{name}_hit",
                    ] = 0

                    result.at[
                        ledger_index,
                        f"target_{name}_bars",
                    ] = np.nan

                (
                    first_passage_result,
                    first_passage_bar,
                ) = self._first_passage(
                    direction,
                    entry,
                    future_targets,
                    target,
                )

                if (
                    first_passage_result
                    !=
                    "NEITHER"
                    or
                    available >= 20
                ):

                    result.at[
                        ledger_index,
                        f"fp_{name}_result",
                    ] = first_passage_result

                    result.at[
                        ledger_index,
                        f"fp_{name}_bar",
                    ] = (
                        first_passage_bar
                        if first_passage_bar
                        is not None
                        else np.nan
                    )

            if available < 20:
                continue

            future20 = data.iloc[
                position + 1
                :
                position + 21
            ]

            net20 = self._numeric(
                result.at[
                    ledger_index,
                    "net_20",
                ]
            )

            mfe20 = self._numeric(
                result.at[
                    ledger_index,
                    "mfe_20",
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
                    0
                )

            # =================================================================
            # Breakeven simulations
            # =================================================================

            for target in self.TARGETS:

                name = int(
                    target
                )

                (
                    be_status,
                    activation_bar,
                    exit_bar,
                    be_net,
                ) = self._breakeven_simulation(
                    direction,
                    entry,
                    future20,
                    target,
                    net20,
                )

                result.at[
                    ledger_index,
                    f"be_after_{name}_status",
                ] = be_status

                result.at[
                    ledger_index,
                    f"be_after_{name}_activation_bar",
                ] = (
                    activation_bar
                    if activation_bar
                    is not None
                    else np.nan
                )

                result.at[
                    ledger_index,
                    f"be_after_{name}_exit_bar",
                ] = (
                    exit_bar
                    if exit_bar
                    is not None
                    else np.nan
                )

                result.at[
                    ledger_index,
                    f"be_after_{name}_net_20",
                ] = be_net

                mfe_after = self._mfe_after_activation(
                    direction,
                    entry,
                    future20,
                    activation_bar,
                )

                result.at[
                    ledger_index,
                    f"mfe_after_{name}_20",
                ] = mfe_after

                if np.isfinite(
                    mfe_after
                ):

                    result.at[
                        ledger_index,
                        f"extension_after_{name}_20",
                    ] = max(
                        0.0,
                        mfe_after
                        -
                        target,
                    )

            # =================================================================
            # Runner / continuation
            # =================================================================

            bars_to_mfe = self._bars_to_mfe(
                direction,
                entry,
                future20,
            )

            result.at[
                ledger_index,
                "bars_to_mfe_20",
            ] = (
                bars_to_mfe
                if bars_to_mfe
                is not None
                else np.nan
            )

            if (
                np.isfinite(
                    mfe20
                )
                and
                np.isfinite(
                    net20
                )
            ):

                result.at[
                    ledger_index,
                    "giveback_20",
                ] = (
                    mfe20
                    -
                    net20
                )

                if mfe20 > 0:

                    result.at[
                        ledger_index,
                        "net_to_mfe_ratio_20",
                    ] = (
                        net20
                        /
                        mfe20
                    )

            # =================================================================
            # Post-entry BOS
            # =================================================================

            if "bos_direction" in future20.columns:

                bos_direction = (
                    future20[
                        "bos_direction"
                    ]
                    .astype(
                        str
                    )
                    .str
                    .upper()
                )

                same = bos_direction.eq(
                    direction
                )

                opposite_direction = (
                    "BEARISH"
                    if direction
                    ==
                    "BULLISH"
                    else
                    "BULLISH"
                )

                opposite = bos_direction.eq(
                    opposite_direction
                )

                result.at[
                    ledger_index,
                    "directional_bos_count_20",
                ] = int(
                    same.sum()
                )

                result.at[
                    ledger_index,
                    "opposing_bos_count_20",
                ] = int(
                    opposite.sum()
                )

                same_first = self._first_true_bar(
                    same
                )

                opposite_first = self._first_true_bar(
                    opposite
                )

                result.at[
                    ledger_index,
                    "directional_bos_first_bar_20",
                ] = (
                    same_first
                    if same_first
                    is not None
                    else np.nan
                )

                result.at[
                    ledger_index,
                    "opposing_bos_first_bar_20",
                ] = (
                    opposite_first
                    if opposite_first
                    is not None
                    else np.nan
                )

                if "internal_bos" in future20.columns:

                    internal = (
                        pd.to_numeric(
                            future20[
                                "internal_bos"
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

                    result.at[
                        ledger_index,
                        "directional_internal_bos_count_20",
                    ] = int(
                        (
                            same
                            &
                            internal
                        ).sum()
                    )

                if "major_bos" in future20.columns:

                    major = (
                        pd.to_numeric(
                            future20[
                                "major_bos"
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

                    result.at[
                        ledger_index,
                        "directional_major_bos_count_20",
                    ] = int(
                        (
                            same
                            &
                            major
                        ).sum()
                    )

            # =================================================================
            # Post-entry swing expansion
            # =================================================================

            if "swing_scale" in future20.columns:

                scales = (
                    future20[
                        "swing_scale"
                    ]
                    .astype(
                        str
                    )
                    .str
                    .upper()
                )

                result.at[
                    ledger_index,
                    "internal_swing_count_20",
                ] = int(
                    scales.eq(
                        "INTERNAL"
                    ).sum()
                )

                result.at[
                    ledger_index,
                    "major_swing_count_20",
                ] = int(
                    scales.eq(
                        "MAJOR"
                    ).sum()
                )

            # =================================================================
            # Structure + regime snapshots
            # =================================================================

            for horizon in self.HORIZONS:

                horizon_row = data.iloc[
                    position
                    +
                    horizon
                ]

                if "structure_bias" in data.columns:

                    bias = self._text(
                        horizon_row.get(
                            "structure_bias"
                        ),
                        "UNKNOWN",
                    ).upper()

                    result.at[
                        ledger_index,
                        f"structure_bias_{horizon}",
                    ] = bias

                    result.at[
                        ledger_index,
                        f"structure_aligned_{horizon}",
                    ] = self._structure_aligned(
                        direction,
                        bias,
                    )

                if "regime_state" in data.columns:

                    result.at[
                        ledger_index,
                        f"regime_state_{horizon}",
                    ] = self._text(
                        horizon_row.get(
                            "regime_state"
                        ),
                        "UNKNOWN",
                    )

                if "regime_trend" in data.columns:

                    result.at[
                        ledger_index,
                        f"regime_trend_{horizon}",
                    ] = self._text(
                        horizon_row.get(
                            "regime_trend"
                        ),
                        "UNKNOWN",
                    )

                if "regime_volatility" in data.columns:

                    result.at[
                        ledger_index,
                        f"regime_volatility_{horizon}",
                    ] = self._text(
                        horizon_row.get(
                            "regime_volatility"
                        ),
                        "UNKNOWN",
                    )

        return result


paper_ledger = PaperLedger()