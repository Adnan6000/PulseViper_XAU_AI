"""
===============================================================================
Module      : multi_day_scalping_validation.py
Project     : PulseViper XAU AI
Purpose     : Multi-Day Temporal Scalping + Setup Quality Diagnostic
===============================================================================

IMPORTANT
---------
This is NOT a profitability backtest.

It does not model:
- spread
- slippage
- commissions
- execution latency
- position sizing
- account risk

Purpose
-------
Evaluate:
1. Current temporal READY / trade_ready population.
2. Forward 5 / 10 / 20 bar behavior.
3. First-touch ATR scenarios.
4. SetupState v1.1 continuous quality telemetry.
5. Whether quality relationships remain directionally stable across dates.

Production scoring is NOT modified here.

Run
---
python 04_Testing/multi_day_scalping_validation.py --days 10 --bars 30000
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# =============================================================================
# Project path bootstrap
# =============================================================================

# When this file is executed as:
#
#     python 04_Testing/multi_day_scalping_validation.py
#
# Python places 04_Testing on sys.path, not necessarily the repository root.
# The project modules live under <repo>/02_AI, so add the repository root before
# importing them.

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROJECT_ROOT_TEXT = str(
    PROJECT_ROOT
)

if (
    PROJECT_ROOT_TEXT
    not in sys.path
):
    sys.path.insert(
        0,
        PROJECT_ROOT_TEXT,
    )


# =============================================================================
# Dynamic project imports
# =============================================================================

fetcher_module: Any = (
    importlib.import_module(
        "02_AI.Dataset.data_fetcher"
    )
)

pipeline_module: Any = (
    importlib.import_module(
        "02_AI.Core.scalping_pipeline"
    )
)

fetcher: Any = (
    fetcher_module.fetcher
)

scalping_pipeline: Any = (
    pipeline_module.scalping_pipeline
)


# =============================================================================
# Configuration
# =============================================================================

FORWARD_HORIZONS: tuple[
    int,
    ...,
] = (
    5,
    10,
    20,
)

QUALITY_FEATURES: dict[
    str,
    str,
] = {
    "Displacement Score": (
        "setup_displacement_score"
    ),
    "Impulse Strength": (
        "setup_impulse_strength"
    ),
    "BOS Strength ATR": (
        "setup_bos_strength_atr"
    ),
    "Break Distance ATR": (
        "setup_break_distance_atr"
    ),
    "Rejection Fill %": (
        "setup_rejection_fill_percent"
    ),
    "Sweep -> READY Bars": (
        "setup_sweep_to_ready_bars"
    ),
    "FVG Count": (
        "setup_fvg_count"
    ),
}

FIRST_TOUCH_CONFIGS: tuple[
    tuple[
        str,
        float,
        float,
    ],
    ...,
] = (
    (
        "TP0.50_SL0.50",
        0.50,
        0.50,
    ),
    (
        "TP1.00_SL0.50",
        1.00,
        0.50,
    ),
    (
        "TP1.00_SL1.00",
        1.00,
        1.00,
    ),
)


# =============================================================================
# Helpers
# =============================================================================

def _to_numeric(
    series: pd.Series,
) -> pd.Series:

    converted: Any = (
        pd.to_numeric(
            series,
            errors="coerce",
        )
    )

    return pd.Series(
        converted,
        index=series.index,
        dtype="float64",
    )


def _as_float(
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
        OverflowError,
    ):

        return default

    if not np.isfinite(
        result
    ):

        return default

    return result


def _fmt(
    value: Any,
    decimals: int = 3,
) -> str:

    numeric = _as_float(
        value
    )

    if not np.isfinite(
        numeric
    ):

        return "NA"

    return (
        f"{numeric:.{decimals}f}"
    )


def _separator(
    char: str = "=",
    width: int = 88,
) -> None:

    print(
        char
        * width
    )


def _section(
    title: str,
) -> None:

    print()

    _separator()

    print(
        title
    )

    _separator()


def _date_labels(
    df: pd.DataFrame,
) -> pd.Series:

    times: Any = (
        pd.to_datetime(
            df[
                "time"
            ],
            errors="coerce",
        )
    )

    labels: Any = (
        times
        .dt
        .strftime(
            "%Y-%m-%d"
        )
    )

    return pd.Series(
        labels,
        index=df.index,
        dtype="object",
    )


# =============================================================================
# Date selection
# =============================================================================

def _select_days(
    df: pd.DataFrame,
    days: int,
) -> list[
    str
]:

    if days <= 0:

        raise ValueError(
            "--days must be greater than zero"
        )

    if (
        "time"
        not in df.columns
    ):

        raise ValueError(
            "Pipeline output has no time column"
        )

    labels = (
        _date_labels(
            df
        )
        .dropna()
    )

    if labels.empty:

        raise ValueError(
            "No valid timestamps found"
        )

    counts = (
        labels
        .value_counts()
        .sort_index()
    )

    if counts.empty:

        raise ValueError(
            "No date groups found"
        )

    maximum_bars = int(
        _as_float(
            counts.max(),
            0.0,
        )
    )

    dynamic_floor = max(
        300,
        int(
            np.ceil(
                maximum_bars
                * 0.80
            )
        ),
    )

    complete_dates: list[
        str
    ] = []

    for (
        date_value,
        raw_count,
    ) in (
        counts.items()
    ):

        count_value = _as_float(
            raw_count,
            0.0,
        )

        if (
            count_value
            >= float(
                dynamic_floor
            )
        ):

            complete_dates.append(
                str(
                    date_value
                )
            )

    if not complete_dates:

        raise ValueError(
            "No sufficiently complete trading days found"
        )

    return complete_dates[
        -days:
    ]


# =============================================================================
# Forward outcomes
# =============================================================================

def _forward_outcome(
    df: pd.DataFrame,
    position: int,
    direction: str,
    horizon: int,
    atr_value: float,
) -> tuple[
    float,
    float,
    float,
]:

    if (
        not np.isfinite(
            atr_value
        )
        or
        atr_value <= 0.0
    ):

        return (
            np.nan,
            np.nan,
            np.nan,
        )

    end_position = (
        position
        + horizon
    )

    if (
        end_position
        >= len(
            df
        )
    ):

        return (
            np.nan,
            np.nan,
            np.nan,
        )

    entry_close = _as_float(
        df.iloc[
            position
        ][
            "close"
        ]
    )

    if not np.isfinite(
        entry_close
    ):

        return (
            np.nan,
            np.nan,
            np.nan,
        )

    future = df.iloc[
        position + 1:
        end_position + 1
    ]

    if future.empty:

        return (
            np.nan,
            np.nan,
            np.nan,
        )

    future_high = _as_float(
        _to_numeric(
            future[
                "high"
            ]
        ).max()
    )

    future_low = _as_float(
        _to_numeric(
            future[
                "low"
            ]
        ).min()
    )

    endpoint_close = _as_float(
        df.iloc[
            end_position
        ][
            "close"
        ]
    )

    if not all(
        np.isfinite(
            value
        )
        for value
        in (
            future_high,
            future_low,
            endpoint_close,
        )
    ):

        return (
            np.nan,
            np.nan,
            np.nan,
        )

    normalized_direction = (
        direction.upper()
    )

    if (
        normalized_direction
        == "BULLISH"
    ):

        mfe = (
            future_high
            - entry_close
        ) / atr_value

        mae = (
            entry_close
            - future_low
        ) / atr_value

        net = (
            endpoint_close
            - entry_close
        ) / atr_value

    elif (
        normalized_direction
        == "BEARISH"
    ):

        mfe = (
            entry_close
            - future_low
        ) / atr_value

        mae = (
            future_high
            - entry_close
        ) / atr_value

        net = (
            entry_close
            - endpoint_close
        ) / atr_value

    else:

        return (
            np.nan,
            np.nan,
            np.nan,
        )

    return (
        float(
            mfe
        ),
        float(
            mae
        ),
        float(
            net
        ),
    )


# =============================================================================
# First-touch outcomes
# =============================================================================

def _first_touch(
    df: pd.DataFrame,
    position: int,
    direction: str,
    atr_value: float,
    target_atr: float,
    stop_atr: float,
    horizon: int = 20,
) -> str:

    if (
        not np.isfinite(
            atr_value
        )
        or
        atr_value <= 0.0
    ):

        return "INVALID"

    end_position = (
        position
        + horizon
    )

    if (
        end_position
        >= len(
            df
        )
    ):

        return "INSUFFICIENT"

    entry_close = _as_float(
        df.iloc[
            position
        ][
            "close"
        ]
    )

    if not np.isfinite(
        entry_close
    ):

        return "INVALID"

    normalized_direction = (
        direction.upper()
    )

    if (
        normalized_direction
        == "BULLISH"
    ):

        target_price = (
            entry_close
            +
            target_atr
            * atr_value
        )

        stop_price = (
            entry_close
            -
            stop_atr
            * atr_value
        )

    elif (
        normalized_direction
        == "BEARISH"
    ):

        target_price = (
            entry_close
            -
            target_atr
            * atr_value
        )

        stop_price = (
            entry_close
            +
            stop_atr
            * atr_value
        )

    else:

        return "INVALID"

    for future_position in range(
        position + 1,
        end_position + 1,
    ):

        candle = df.iloc[
            future_position
        ]

        candle_high = _as_float(
            candle.get(
                "high",
                np.nan,
            )
        )

        candle_low = _as_float(
            candle.get(
                "low",
                np.nan,
            )
        )

        if (
            not np.isfinite(
                candle_high
            )
            or
            not np.isfinite(
                candle_low
            )
        ):

            continue

        if (
            normalized_direction
            == "BULLISH"
        ):

            target_hit = (
                candle_high
                >= target_price
            )

            stop_hit = (
                candle_low
                <= stop_price
            )

        else:

            target_hit = (
                candle_low
                <= target_price
            )

            stop_hit = (
                candle_high
                >= stop_price
            )

        if (
            target_hit
            and
            stop_hit
        ):

            return "AMBIGUOUS"

        if target_hit:

            return "TARGET"

        if stop_hit:

            return "STOP"

    return "NONE"


# =============================================================================
# Build READY event frame
# =============================================================================

def _build_event_frame(
    df: pd.DataFrame,
    selected_dates: list[
        str
    ],
) -> pd.DataFrame:

    required = {
        "time",
        "close",
        "high",
        "low",
        "atr",
        "trade_ready",
        "setup_direction",
    }

    missing = (
        required
        - set(
            df.columns
        )
    )

    if missing:

        raise ValueError(
            (
                "Missing required diagnostic columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )
        )

    time_series: Any = (
        pd.to_datetime(
            df[
                "time"
            ],
            errors="coerce",
        )
    )

    date_labels = _date_labels(
        df
    )

    selected_set = set(
        selected_dates
    )

    trade_ready = (
        _to_numeric(
            df[
                "trade_ready"
            ]
        )
        .fillna(
            0.0
        )
        .astype(
            int
        )
    )

    ready_mask = (
        trade_ready
        == 1
    ).to_numpy(
        dtype=bool
    )

    candidate_positions = (
        np.flatnonzero(
            ready_mask
        )
    )

    metadata_columns: tuple[
        str,
        ...,
    ] = (
        "setup_id",
        "setup_age_bars",
        "setup_bos_scope",
        "setup_bos_event_scope",
        "setup_bos_context",
        "setup_structure_alignment",
        "confidence_score",

        "setup_displacement_score",
        "setup_impulse_strength",
        "setup_bos_strength_atr",
        "setup_break_distance_atr",
        "setup_rejection_fill_percent",
        "setup_sweep_to_ready_bars",
        "setup_fvg_count",
    )

    event_records: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for raw_position in (
        candidate_positions.tolist()
    ):

        position = int(
            raw_position
        )

        raw_date = (
            date_labels.iloc[
                position
            ]
        )

        if pd.isna(
            raw_date
        ):

            continue

        date_label = str(
            raw_date
        )

        if (
            date_label
            not in selected_set
        ):

            continue

        row = df.iloc[
            position
        ]

        direction = str(
            row.get(
                "setup_direction",
                "NONE",
            )
        ).upper()

        if direction not in (
            "BULLISH",
            "BEARISH",
        ):

            continue

        atr_value = _as_float(
            row.get(
                "atr",
                np.nan,
            )
        )

        entry_close = _as_float(
            row.get(
                "close",
                np.nan,
            )
        )

        record: dict[
            str,
            Any,
        ] = {
            "position": (
                position
            ),
            "time": (
                time_series.iloc[
                    position
                ]
            ),
            "date_label": (
                date_label
            ),
            "direction": (
                direction
            ),
            "entry_close": (
                entry_close
            ),
            "atr": (
                atr_value
            ),
        }

        for column in (
            metadata_columns
        ):

            record[
                column
            ] = row.get(
                column,
                np.nan,
            )

        for horizon in (
            FORWARD_HORIZONS
        ):

            (
                mfe,
                mae,
                net,
            ) = _forward_outcome(
                df=df,
                position=position,
                direction=direction,
                horizon=horizon,
                atr_value=atr_value,
            )

            record[
                f"mfe_{horizon}"
            ] = mfe

            record[
                f"mae_{horizon}"
            ] = mae

            record[
                f"net_{horizon}"
            ] = net

        for (
            label,
            target_atr,
            stop_atr,
        ) in (
            FIRST_TOUCH_CONFIGS
        ):

            record[
                f"first_touch_{label}"
            ] = _first_touch(
                df=df,
                position=position,
                direction=direction,
                atr_value=atr_value,
                target_atr=target_atr,
                stop_atr=stop_atr,
                horizon=20,
            )

        event_records.append(
            record
        )

    return pd.DataFrame(
        event_records
    )


# =============================================================================
# Daily summary
# =============================================================================

def _daily_summary(
    df: pd.DataFrame,
    selected_dates: list[
        str
    ],
) -> pd.DataFrame:

    labels = _date_labels(
        df
    )

    records: list[
        dict[
            str,
            Any,
        ]
    ] = []

    def numeric_flag(
        frame: pd.DataFrame,
        column: str,
    ) -> int:

        if (
            column
            not in frame.columns
        ):

            return 0

        values = (
            _to_numeric(
                frame[
                    column
                ]
            )
            .fillna(
                0.0
            )
        )

        return int(
            _as_float(
                values.sum(),
                0.0,
            )
        )

    for date_label in (
        selected_dates
    ):

        day = df.loc[
            labels
            == date_label
        ]

        bullish_starts = (
            numeric_flag(
                day,
                "bullish_setup_started_event",
            )
        )

        bearish_starts = (
            numeric_flag(
                day,
                "bearish_setup_started_event",
            )
        )

        bullish_ready = (
            numeric_flag(
                day,
                "bullish_setup_ready_event",
            )
        )

        bearish_ready = (
            numeric_flag(
                day,
                "bearish_setup_ready_event",
            )
        )

        starts = (
            bullish_starts
            + bearish_starts
        )

        ready = (
            bullish_ready
            + bearish_ready
        )

        trade_ready = (
            numeric_flag(
                day,
                "trade_ready",
            )
        )

        ready_pct = (
            (
                ready
                / starts
                * 100.0
            )
            if starts > 0
            else 0.0
        )

        records.append(
            {
                "date": (
                    date_label
                ),
                "bars": (
                    len(
                        day
                    )
                ),
                "starts": (
                    starts
                ),
                "bull_starts": (
                    bullish_starts
                ),
                "bear_starts": (
                    bearish_starts
                ),
                "ready": (
                    ready
                ),
                "bull_ready": (
                    bullish_ready
                ),
                "bear_ready": (
                    bearish_ready
                ),
                "ready_pct": round(
                    ready_pct,
                    1,
                ),
                "trade_ready": (
                    trade_ready
                ),
            }
        )

    return pd.DataFrame(
        records
    )


# =============================================================================
# Outcome summary
# =============================================================================

def _empty_outcome_summary() -> dict[
    str,
    Any,
]:

    return {
        "n": 0,
        "median_mfe": np.nan,
        "median_mae": np.nan,
        "median_net": np.nan,
        "avg_net": np.nan,
        "positive_pct": np.nan,
        "mfe_05_pct": np.nan,
        "mfe_10_pct": np.nan,
    }


def _outcome_summary(
    frame: pd.DataFrame,
    horizon: int,
) -> dict[
    str,
    Any,
]:

    mfe_column = (
        f"mfe_{horizon}"
    )

    mae_column = (
        f"mae_{horizon}"
    )

    net_column = (
        f"net_{horizon}"
    )

    required = {
        mfe_column,
        mae_column,
        net_column,
    }

    if (
        frame.empty
        or
        not required.issubset(
            frame.columns
        )
    ):

        return (
            _empty_outcome_summary()
        )

    usable = pd.DataFrame(
        {
            mfe_column: (
                _to_numeric(
                    frame[
                        mfe_column
                    ]
                )
            ),
            mae_column: (
                _to_numeric(
                    frame[
                        mae_column
                    ]
                )
            ),
            net_column: (
                _to_numeric(
                    frame[
                        net_column
                    ]
                )
            ),
        }
    )

    usable = usable.replace(
        [
            np.inf,
            -np.inf,
        ],
        np.nan,
    )

    usable = usable.dropna(
        subset=[
            net_column
        ]
    )

    if usable.empty:

        return (
            _empty_outcome_summary()
        )

    return {
        "n": int(
            len(
                usable
            )
        ),

        "median_mfe": (
            _as_float(
                usable[
                    mfe_column
                ].median()
            )
        ),

        "median_mae": (
            _as_float(
                usable[
                    mae_column
                ].median()
            )
        ),

        "median_net": (
            _as_float(
                usable[
                    net_column
                ].median()
            )
        ),

        "avg_net": (
            _as_float(
                usable[
                    net_column
                ].mean()
            )
        ),

        "positive_pct": float(
            (
                usable[
                    net_column
                ]
                > 0.0
            ).mean()
            * 100.0
        ),

        "mfe_05_pct": float(
            (
                usable[
                    mfe_column
                ]
                >= 0.50
            ).mean()
            * 100.0
        ),

        "mfe_10_pct": float(
            (
                usable[
                    mfe_column
                ]
                >= 1.00
            ).mean()
            * 100.0
        ),
    }


def _print_forward_summary(
    events: pd.DataFrame,
) -> None:

    _section(
        "FORWARD OUTCOME SUMMARY"
    )

    for horizon in (
        FORWARD_HORIZONS
    ):

        stats = (
            _outcome_summary(
                events,
                horizon,
            )
        )

        print()

        print(
            f"Forward {horizon} bars"
        )

        print(
            f"  samples        : "
            f"{stats['n']}"
        )

        print(
            f"  median MFE ATR : "
            f"{_fmt(stats['median_mfe'])}"
        )

        print(
            f"  median MAE ATR : "
            f"{_fmt(stats['median_mae'])}"
        )

        print(
            f"  median NET ATR : "
            f"{_fmt(stats['median_net'])}"
        )

        print(
            f"  avg NET ATR    : "
            f"{_fmt(stats['avg_net'])}"
        )

        print(
            f"  NET positive % : "
            f"{_fmt(stats['positive_pct'], 1)}"
        )

        print(
            f"  MFE >= 0.50 %  : "
            f"{_fmt(stats['mfe_05_pct'], 1)}"
        )

        print(
            f"  MFE >= 1.00 %  : "
            f"{_fmt(stats['mfe_10_pct'], 1)}"
        )


# =============================================================================
# First-touch summary
# =============================================================================

def _print_first_touch_summary(
    events: pd.DataFrame,
) -> None:

    _section(
        "FIRST-TOUCH OUTCOMES — 20 FUTURE BARS"
    )

    for (
        label,
        target_atr,
        stop_atr,
    ) in (
        FIRST_TOUCH_CONFIGS
    ):

        column = (
            f"first_touch_{label}"
        )

        if (
            column
            not in events.columns
        ):

            continue

        usable = events[
            events[
                column
            ].isin(
                [
                    "TARGET",
                    "STOP",
                    "AMBIGUOUS",
                    "NONE",
                ]
            )
        ]

        counts = (
            usable[
                column
            ]
            .value_counts()
        )

        target = int(
            _as_float(
                counts.get(
                    "TARGET",
                    0,
                ),
                0.0,
            )
        )

        stop = int(
            _as_float(
                counts.get(
                    "STOP",
                    0,
                ),
                0.0,
            )
        )

        ambiguous = int(
            _as_float(
                counts.get(
                    "AMBIGUOUS",
                    0,
                ),
                0.0,
            )
        )

        none = int(
            _as_float(
                counts.get(
                    "NONE",
                    0,
                ),
                0.0,
            )
        )

        resolved = (
            target
            + stop
        )

        target_rate = (
            (
                target
                / resolved
                * 100.0
            )
            if resolved > 0
            else np.nan
        )

        print()

        print(
            (
                f"TP {target_atr:.2f} ATR "
                f"/ SL {stop_atr:.2f} ATR"
            )
        )

        print(
            f"  target first   : "
            f"{target}"
        )

        print(
            f"  stop first     : "
            f"{stop}"
        )

        print(
            f"  ambiguous      : "
            f"{ambiguous}"
        )

        print(
            f"  none           : "
            f"{none}"
        )

        print(
            f"  resolved target: "
            f"{_fmt(target_rate, 1)}%"
        )


# =============================================================================
# Group outcome tables
# =============================================================================

def _group_outcome_table(
    events: pd.DataFrame,
    group_column: str,
    horizon: int = 20,
) -> pd.DataFrame:

    if (
        events.empty
        or
        group_column
        not in events.columns
    ):

        return pd.DataFrame()

    records: list[
        dict[
            str,
            Any,
        ]
    ] = []

    grouped = events.groupby(
        group_column,
        dropna=False,
        observed=True,
    )

    for (
        group_value,
        group,
    ) in grouped:

        stats = (
            _outcome_summary(
                group,
                horizon,
            )
        )

        records.append(
            {
                group_column: (
                    str(
                        group_value
                    )
                ),

                "n": (
                    stats[
                        "n"
                    ]
                ),

                "median_mfe": round(
                    _as_float(
                        stats[
                            "median_mfe"
                        ]
                    ),
                    3,
                ),

                "median_mae": round(
                    _as_float(
                        stats[
                            "median_mae"
                        ]
                    ),
                    3,
                ),

                "median_net": round(
                    _as_float(
                        stats[
                            "median_net"
                        ]
                    ),
                    3,
                ),

                "avg_net": round(
                    _as_float(
                        stats[
                            "avg_net"
                        ]
                    ),
                    3,
                ),

                "positive_pct": round(
                    _as_float(
                        stats[
                            "positive_pct"
                        ]
                    ),
                    1,
                ),
            }
        )

    return pd.DataFrame(
        records
    )


def _age_bucket(
    value: Any,
) -> str:

    number = _as_float(
        value
    )

    if not np.isfinite(
        number
    ):

        return "NA"

    if number <= 5:

        return "01-05"

    if number <= 10:

        return "06-10"

    if number <= 15:

        return "11-15"

    return "16+"


def _hour_bucket(
    value: Any,
) -> str:

    number = _as_float(
        value
    )

    if not np.isfinite(
        number
    ):

        return "NA"

    hour = int(
        number
    )

    if (
        0
        <= hour
        <= 5
    ):

        return "00-05"

    if (
        6
        <= hour
        <= 11
    ):

        return "06-11"

    if (
        12
        <= hour
        <= 17
    ):

        return "12-17"

    if (
        18
        <= hour
        <= 23
    ):

        return "18-23"

    return "NA"


def _confidence_bucket(
    value: Any,
) -> str:

    number = _as_float(
        value
    )

    if not np.isfinite(
        number
    ):

        return "NA"

    if number < 85.0:

        return "<85"

    if number < 90.0:

        return "85-89"

    if number < 95.0:

        return "90-94"

    if number < 100.0:

        return "95-99"

    return "100"


def _print_group_view(
    working: pd.DataFrame,
    title: str,
    column: str,
) -> None:

    print()

    print(
        title
    )

    table = (
        _group_outcome_table(
            working,
            column,
            20,
        )
    )

    if table.empty:

        print(
            "  No usable samples."
        )

    else:

        print(
            table.to_string(
                index=False
            )
        )


def _print_context_views(
    events: pd.DataFrame,
) -> None:

    _section(
        "20-BAR CONTEXT VIEWS"
    )

    working = events.copy()

    if (
        "date_label"
        in working.columns
    ):

        _print_group_view(
            working,
            "By date",
            "date_label",
        )

    _print_group_view(
        working,
        "By direction",
        "direction",
    )

    if (
        "setup_bos_scope"
        in working.columns
    ):

        _print_group_view(
            working,
            "By BOS scope",
            "setup_bos_scope",
        )

    if (
        "setup_structure_alignment"
        in working.columns
    ):

        working[
            "structure_alignment"
        ] = _to_numeric(
            working[
                "setup_structure_alignment"
            ]
        )

        _print_group_view(
            working,
            "By structure alignment",
            "structure_alignment",
        )

    if (
        "setup_age_bars"
        in working.columns
    ):

        working[
            "age_bucket"
        ] = pd.Series(
            [
                _age_bucket(
                    value
                )
                for value
                in working[
                    "setup_age_bars"
                ].tolist()
            ],
            index=working.index,
            dtype="object",
        )

        _print_group_view(
            working,
            "By setup age",
            "age_bucket",
        )

    if (
        "time"
        in working.columns
    ):

        event_times: Any = (
            pd.to_datetime(
                working[
                    "time"
                ],
                errors="coerce",
            )
        )

        event_hours: Any = (
            event_times
            .dt
            .hour
        )

        working[
            "raw_hour_bucket"
        ] = pd.Series(
            [
                _hour_bucket(
                    value
                )
                for value
                in event_hours.tolist()
            ],
            index=working.index,
            dtype="object",
        )

        _print_group_view(
            working,
            (
                "By raw hour bucket "
                "(timestamp timezone is not labelled)"
            ),
            "raw_hour_bucket",
        )

    if (
        "confidence_score"
        in working.columns
    ):

        working[
            "confidence_bucket"
        ] = pd.Series(
            [
                _confidence_bucket(
                    value
                )
                for value
                in working[
                    "confidence_score"
                ].tolist()
            ],
            index=working.index,
            dtype="object",
        )

        _print_group_view(
            working,
            "By current Confidence v2 bucket",
            "confidence_bucket",
        )


# =============================================================================
# Quality bucketing
# =============================================================================

def _global_quantile_bucket(
    values: pd.Series,
) -> tuple[
    pd.Series,
    list[
        float
    ],
]:

    numeric = (
        _to_numeric(
            values
        )
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
    )

    valid = (
        numeric
        .dropna()
    )

    if valid.empty:

        return (
            pd.Series(
                [
                    "NA"
                ]
                * len(
                    values
                ),
                index=values.index,
                dtype="object",
            ),
            [],
        )

    unique_count = int(
        valid.nunique()
    )

    if unique_count <= 1:

        only_value = _as_float(
            valid.iloc[
                0
            ]
        )

        labels = [
            (
                "ALL"
                if np.isfinite(
                    _as_float(
                        raw_value
                    )
                )
                else "NA"
            )
            for raw_value
            in numeric.tolist()
        ]

        return (
            pd.Series(
                labels,
                index=values.index,
                dtype="object",
            ),
            [
                only_value
            ],
        )

    requested_quantiles = min(
        4,
        unique_count,
    )

    quantile_points = np.linspace(
        0.0,
        1.0,
        requested_quantiles + 1,
        dtype=np.float64,
    )

    raw_edges = np.quantile(
        valid.to_numpy(
            dtype=np.float64
        ),
        quantile_points,
    )

    edges: list[
        float
    ] = sorted(
        {
            float(
                raw_edge
            )
            for raw_edge
            in raw_edges.tolist()
        }
    )

    if len(
        edges
    ) <= 2:

        median = _as_float(
            valid.median()
        )

        labels: list[
            str
        ] = []

        for raw_value in (
            numeric.tolist()
        ):

            value = _as_float(
                raw_value
            )

            if not np.isfinite(
                value
            ):

                labels.append(
                    "NA"
                )

            elif (
                value
                <= median
            ):

                labels.append(
                    "LOW"
                )

            else:

                labels.append(
                    "HIGH"
                )

        return (
            pd.Series(
                labels,
                index=values.index,
                dtype="object",
            ),
            [
                _as_float(
                    valid.min()
                ),
                median,
                _as_float(
                    valid.max()
                ),
            ],
        )

    internal_edges = (
        edges[
            1:
            -1
        ]
    )

    def classify(
        raw_value: Any,
    ) -> str:

        value = _as_float(
            raw_value
        )

        if not np.isfinite(
            value
        ):

            return "NA"

        for (
            edge_number,
            boundary,
        ) in enumerate(
            internal_edges,
            start=1,
        ):

            if (
                value
                <= boundary
            ):

                return (
                    f"Q{edge_number}"
                )

        return (
            f"Q{len(internal_edges) + 1}"
        )

    bucket_labels = [
        classify(
            raw_value
        )
        for raw_value
        in numeric.tolist()
    ]

    return (
        pd.Series(
            bucket_labels,
            index=values.index,
            dtype="object",
        ),
        edges,
    )


def _fvg_count_bucket(
    values: pd.Series,
) -> pd.Series:

    numeric = (
        _to_numeric(
            values
        )
        .fillna(
            0.0
        )
    )

    labels: list[
        str
    ] = []

    for raw_value in (
        numeric.tolist()
    ):

        count = int(
            _as_float(
                raw_value,
                0.0,
            )
        )

        if count <= 0:

            labels.append(
                "0"
            )

        elif count == 1:

            labels.append(
                "1"
            )

        elif count == 2:

            labels.append(
                "2"
            )

        else:

            labels.append(
                "3+"
            )

    return pd.Series(
        labels,
        index=values.index,
        dtype="object",
    )


# =============================================================================
# Quality bucket metrics
# =============================================================================

def _quality_bucket_table(
    events: pd.DataFrame,
    bucket_column: str,
) -> pd.DataFrame:

    if (
        events.empty
        or
        bucket_column
        not in events.columns
    ):

        return pd.DataFrame()

    records: list[
        dict[
            str,
            Any,
        ]
    ] = []

    total = len(
        events
    )

    grouped = events.groupby(
        bucket_column,
        dropna=False,
        observed=True,
    )

    for (
        bucket_value,
        group,
    ) in grouped:

        bucket_name = str(
            bucket_value
        )

        if (
            bucket_name
            == "NA"
        ):

            continue

        record: dict[
            str,
            Any,
        ] = {
            "bucket": (
                bucket_name
            ),

            "n": int(
                len(
                    group
                )
            ),

            "population_pct": round(
                (
                    len(
                        group
                    )
                    / total
                    * 100.0
                )
                if total > 0
                else 0.0,
                1,
            ),
        }

        for horizon in (
            FORWARD_HORIZONS
        ):

            stats = (
                _outcome_summary(
                    group,
                    horizon,
                )
            )

            record[
                f"net{horizon}_med"
            ] = round(
                _as_float(
                    stats[
                        "median_net"
                    ]
                ),
                3,
            )

            record[
                f"net{horizon}_avg"
            ] = round(
                _as_float(
                    stats[
                        "avg_net"
                    ]
                ),
                3,
            )

            record[
                f"pos{horizon}_pct"
            ] = round(
                _as_float(
                    stats[
                        "positive_pct"
                    ]
                ),
                1,
            )

        for (
            label,
            _,
            _,
        ) in (
            FIRST_TOUCH_CONFIGS
        ):

            column = (
                f"first_touch_{label}"
            )

            if (
                column
                not in group.columns
            ):

                record[
                    f"{label}_target_pct"
                ] = np.nan

                continue

            resolved = group.loc[
                group[
                    column
                ].isin(
                    [
                        "TARGET",
                        "STOP",
                    ]
                ),
                column,
            ]

            if resolved.empty:

                record[
                    f"{label}_target_pct"
                ] = np.nan

            else:

                record[
                    f"{label}_target_pct"
                ] = round(
                    float(
                        (
                            resolved
                            == "TARGET"
                        ).mean()
                        * 100.0
                    ),
                    1,
                )

        records.append(
            record
        )

    return pd.DataFrame(
        records
    )


def _print_direction_quality(
    events: pd.DataFrame,
    bucket_column: str,
) -> None:

    for direction in (
        "BULLISH",
        "BEARISH",
    ):

        subset = events.loc[
            events[
                "direction"
            ]
            == direction
        ]

        if subset.empty:

            continue

        table = (
            _quality_bucket_table(
                subset,
                bucket_column,
            )
        )

        print()

        print(
            direction
        )

        if table.empty:

            print(
                "  No usable samples."
            )

        else:

            print(
                table.to_string(
                    index=False
                )
            )


# =============================================================================
# Date stability
# =============================================================================

def _date_stability_table(
    events: pd.DataFrame,
    feature_column: str,
) -> tuple[
    pd.DataFrame,
    float,
]:

    if (
        feature_column
        not in events.columns
        or
        "date_label"
        not in events.columns
    ):

        return (
            pd.DataFrame(),
            np.nan,
        )

    numeric = (
        _to_numeric(
            events[
                feature_column
            ]
        )
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
    )

    valid_mask = (
        numeric
        .notna()
    )

    valid = events.loc[
        valid_mask
    ].copy()

    if valid.empty:

        return (
            pd.DataFrame(),
            np.nan,
        )

    valid[
        "_quality_numeric"
    ] = numeric.loc[
        valid.index
    ]

    median_boundary = (
        _as_float(
            valid[
                "_quality_numeric"
            ].median()
        )
    )

    valid[
        "_quality_side"
    ] = pd.Series(
        [
            (
                "HIGH"
                if (
                    _as_float(
                        value
                    )
                    > median_boundary
                )
                else "LOW"
            )
            for value
            in valid[
                "_quality_numeric"
            ].tolist()
        ],
        index=valid.index,
        dtype="object",
    )

    records: list[
        dict[
            str,
            Any,
        ]
    ] = []

    grouped = valid.groupby(
        "date_label",
        observed=True,
    )

    for (
        raw_date,
        day,
    ) in grouped:

        date_label = str(
            raw_date
        )

        low = day.loc[
            day[
                "_quality_side"
            ]
            == "LOW"
        ]

        high = day.loc[
            day[
                "_quality_side"
            ]
            == "HIGH"
        ]

        if (
            len(
                low
            )
            < 2
            or
            len(
                high
            )
            < 2
        ):

            continue

        record: dict[
            str,
            Any,
        ] = {
            "date": (
                date_label
            ),

            "low_n": int(
                len(
                    low
                )
            ),

            "high_n": int(
                len(
                    high
                )
            ),
        }

        for horizon in (
            FORWARD_HORIZONS
        ):

            low_net = (
                _to_numeric(
                    low[
                        f"net_{horizon}"
                    ]
                )
                .replace(
                    [
                        np.inf,
                        -np.inf,
                    ],
                    np.nan,
                )
                .dropna()
            )

            high_net = (
                _to_numeric(
                    high[
                        f"net_{horizon}"
                    ]
                )
                .replace(
                    [
                        np.inf,
                        -np.inf,
                    ],
                    np.nan,
                )
                .dropna()
            )

            if (
                low_net.empty
                or
                high_net.empty
            ):

                spread = np.nan

            else:

                spread = (
                    _as_float(
                        high_net.median()
                    )
                    -
                    _as_float(
                        low_net.median()
                    )
                )

            record[
                f"spread_{horizon}"
            ] = (
                round(
                    spread,
                    3,
                )
                if np.isfinite(
                    spread
                )
                else np.nan
            )

            if np.isfinite(
                spread
            ):

                record[
                    f"supports_{horizon}"
                ] = (
                    "YES"
                    if spread > 0.0
                    else "NO"
                )

            else:

                record[
                    f"supports_{horizon}"
                ] = "NA"

        records.append(
            record
        )

    return (
        pd.DataFrame(
            records
        ),
        median_boundary,
    )


def _print_stability_summary(
    stability: pd.DataFrame,
) -> None:

    if stability.empty:

        print(
            (
                "No dates had enough HIGH/LOW "
                "samples for stability comparison."
            )
        )

        return

    print(
        stability.to_string(
            index=False
        )
    )

    print()

    print(
        (
            "Support counts "
            "(HIGH median NET > LOW median NET)"
        )
    )

    for horizon in (
        FORWARD_HORIZONS
    ):

        column = (
            f"supports_{horizon}"
        )

        if (
            column
            not in stability.columns
        ):

            continue

        yes = int(
            (
                stability[
                    column
                ]
                == "YES"
            ).sum()
        )

        no = int(
            (
                stability[
                    column
                ]
                == "NO"
            ).sum()
        )

        eligible = (
            yes
            + no
        )

        print(
            (
                f"  {horizon:>2} bars: "
                f"{yes}/{eligible} dates support, "
                f"{no}/{eligible} contradict"
            )
        )


# =============================================================================
# Feature diagnostic
# =============================================================================

def _print_feature_diagnostic(
    events: pd.DataFrame,
    feature_name: str,
    feature_column: str,
) -> None:

    _section(
        f"QUALITY FEATURE: {feature_name}"
    )

    if (
        feature_column
        not in events.columns
    ):

        print(
            f"Missing column: "
            f"{feature_column}"
        )

        return

    numeric = (
        _to_numeric(
            events[
                feature_column
            ]
        )
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
    )

    finite = (
        numeric
        .dropna()
    )

    if finite.empty:

        print(
            "No usable numeric values."
        )

        return

    print(
        f"Column   : "
        f"{feature_column}"
    )

    print(
        f"Samples  : "
        f"{len(finite)}"
    )

    print(
        f"Unique   : "
        f"{finite.nunique()}"
    )

    print(
        f"Min      : "
        f"{_fmt(finite.min())}"
    )

    print(
        f"Median   : "
        f"{_fmt(finite.median())}"
    )

    print(
        f"Max      : "
        f"{_fmt(finite.max())}"
    )

    working = events.copy()

    if (
        feature_column
        == "setup_fvg_count"
    ):

        working[
            "_quality_bucket"
        ] = _fvg_count_bucket(
            working[
                feature_column
            ]
        )

        boundaries: list[
            float
        ] = []

    else:

        (
            bucket,
            boundaries,
        ) = _global_quantile_bucket(
            working[
                feature_column
            ]
        )

        working[
            "_quality_bucket"
        ] = bucket

    if boundaries:

        print(
            (
                "Global bucket raw boundaries: "
                +
                ", ".join(
                    _fmt(
                        value
                    )
                    for value
                    in boundaries
                )
            )
        )

    print()

    print(
        "OVERALL"
    )

    overall_table = (
        _quality_bucket_table(
            working,
            "_quality_bucket",
        )
    )

    if overall_table.empty:

        print(
            "No usable buckets."
        )

    else:

        print(
            overall_table.to_string(
                index=False
            )
        )

    print()

    print(
        "DIRECTION SPLIT — SAME GLOBAL BUCKETS"
    )

    _print_direction_quality(
        working,
        "_quality_bucket",
    )

    print()

    print(
        "DATE STABILITY — GLOBAL MEDIAN HIGH vs LOW"
    )

    (
        stability,
        median_boundary,
    ) = _date_stability_table(
        working,
        feature_column,
    )

    print(
        (
            "Global median split boundary: "
            f"{_fmt(median_boundary)}"
        )
    )

    _print_stability_summary(
        stability
    )

    print()

    print(
        (
            "Interpretation note: "
            "HIGH-vs-LOW stability only checks broad "
            "direction. The overall bucket table must "
            "still be inspected for nonlinear / "
            "middle-is-best behavior."
        )
    )


# =============================================================================
# Telemetry redundancy
# =============================================================================

def _print_quality_correlations(
    events: pd.DataFrame,
) -> None:

    _section(
        "QUALITY TELEMETRY REDUNDANCY CHECK"
    )

    available_columns = [
        column
        for column
        in QUALITY_FEATURES.values()
        if column
        in events.columns
    ]

    if len(
        available_columns
    ) < 2:

        print(
            (
                "Not enough telemetry columns "
                "for correlation analysis."
            )
        )

        return

    numeric = pd.DataFrame(
        {
            column: (
                _to_numeric(
                    events[
                        column
                    ]
                )
            )
            for column
            in available_columns
        }
    )

    correlation = numeric.corr(
        method="spearman"
    )

    correlation_values = (
        correlation
        .to_numpy(
            dtype=np.float64
        )
    )

    pairs: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for left_index in range(
        len(
            available_columns
        )
    ):

        for right_index in range(
            left_index + 1,
            len(
                available_columns
            ),
        ):

            rho: float = float(
                correlation_values[
                    left_index,
                    right_index,
                ]
            )

            if not np.isfinite(
                rho
            ):

                continue

            if abs(
                rho
            ) >= 0.70:

                pairs.append(
                    {
                        "feature_a": (
                            available_columns[
                                left_index
                            ]
                        ),

                        "feature_b": (
                            available_columns[
                                right_index
                            ]
                        ),

                        "spearman_rho": round(
                            rho,
                            3,
                        ),

                        "abs_rho": round(
                            abs(
                                rho
                            ),
                            3,
                        ),
                    }
                )

    if not pairs:

        print(
            (
                "No |Spearman rho| >= 0.70 "
                "relationships found."
            )
        )

        return

    pair_frame = (
        pd.DataFrame(
            pairs
        )
    )

    pair_frame = (
        pair_frame
        .sort_values(
            "abs_rho",
            ascending=False,
        )
        .drop(
            columns=[
                "abs_rho"
            ]
        )
    )

    print(
        (
            "Highly correlated telemetry may represent "
            "duplicate information and should not "
            "automatically receive separate large "
            "Confidence weights."
        )
    )

    print()

    print(
        pair_frame.to_string(
            index=False
        )
    )


# =============================================================================
# Population
# =============================================================================

def _print_population(
    daily: pd.DataFrame,
    events: pd.DataFrame,
) -> None:

    _section(
        "MULTI-DAY TEMPORAL SCALPING POPULATION"
    )

    print(
        daily.to_string(
            index=False
        )
    )

    print()

    total = len(
        events
    )

    if events.empty:

        bullish = 0
        bearish = 0

    else:

        bullish = int(
            (
                events[
                    "direction"
                ]
                == "BULLISH"
            ).sum()
        )

        bearish = int(
            (
                events[
                    "direction"
                ]
                == "BEARISH"
            ).sum()
        )

    print(
        f"Total trade-ready events : "
        f"{total}"
    )

    print(
        f"Bullish                  : "
        f"{bullish}"
    )

    print(
        f"Bearish                  : "
        f"{bearish}"
    )

    if not daily.empty:

        daily_trade_ready = (
            _to_numeric(
                daily[
                    "trade_ready"
                ]
            )
        )

        print(
            (
                "Average / selected day    : "
                f"{_fmt(daily_trade_ready.mean(), 1)}"
            )
        )

        print(
            (
                "Range / selected day      : "
                f"{int(_as_float(daily_trade_ready.min(), 0.0))}"
                " - "
                f"{int(_as_float(daily_trade_ready.max(), 0.0))}"
            )
        )


# =============================================================================
# Main
# =============================================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "PulseViper multi-day temporal "
            "scalping quality diagnostic"
        )
    )

    parser.add_argument(
        "--days",
        type=int,
        default=10,
        help=(
            "Number of complete trading "
            "days to analyze"
        ),
    )

    parser.add_argument(
        "--bars",
        type=int,
        default=30000,
        help=(
            "Number of M1 bars to fetch "
            "from MT5"
        ),
    )

    parser.add_argument(
        "--symbol",
        type=str,
        default="XAUUSDm",
        help=(
            "MT5 symbol"
        ),
    )

    args = parser.parse_args()

    if (
        args.bars
        <= 0
    ):

        raise ValueError(
            "--bars must be greater than zero"
        )

    print()

    _separator()

    print(
        "PulseViper XAU AI"
    )

    print(
        "Multi-Day SetupState v1.1 Quality Diagnostic"
    )

    _separator()

    print()

    print(
        f"Project root: "
        f"{PROJECT_ROOT_TEXT}"
    )

    print(
        (
            f"Fetching {args.bars} M1 bars "
            f"for {args.symbol}..."
        )
    )

    raw: pd.DataFrame = (
        fetcher.fetch(
            symbol=args.symbol,
            bars=args.bars,
        )
    )

    if raw.empty:

        raise RuntimeError(
            "MT5 returned an empty dataset"
        )

    raw = (
        raw
        .sort_values(
            "time"
        )
        .reset_index(
            drop=True
        )
    )

    print(
        f"Fetched bars: "
        f"{len(raw)}"
    )

    print(
        (
            "Running canonical temporal "
            "scalping pipeline..."
        )
    )

    enriched: pd.DataFrame = (
        scalping_pipeline.generate(
            raw
        )
    )

    enriched = (
        enriched
        .sort_values(
            "time"
        )
        .reset_index(
            drop=True
        )
    )

    selected_dates = (
        _select_days(
            enriched,
            days=args.days,
        )
    )

    print()

    print(
        "Selected dates:"
    )

    for date_label in (
        selected_dates
    ):

        print(
            f"  {date_label}"
        )

    daily = (
        _daily_summary(
            enriched,
            selected_dates,
        )
    )

    events = (
        _build_event_frame(
            enriched,
            selected_dates,
        )
    )

    _print_population(
        daily,
        events,
    )

    if events.empty:

        print()

        print(
            (
                "No trade_ready events found "
                "for selected dates."
            )
        )

        return

    _print_forward_summary(
        events
    )

    _print_first_touch_summary(
        events
    )

    _print_context_views(
        events
    )

    for (
        feature_name,
        feature_column,
    ) in (
        QUALITY_FEATURES.items()
    ):

        _print_feature_diagnostic(
            events=events,
            feature_name=feature_name,
            feature_column=feature_column,
        )

    _print_quality_correlations(
        events
    )

    _section(
        "DIAGNOSTIC STATUS"
    )

    print(
        (
            "This report measures forward market "
            "behavior from temporal READY/trade_ready "
            "events."
        )
    )

    print()

    print(
        (
            "It is NOT a profitability backtest and "
            "does not include spread, slippage, "
            "execution latency, commissions, "
            "position sizing, or account risk."
        )
    )

    print()

    print(
        (
            "Do NOT change Confidence weights from "
            "one attractive bucket. Look for "
            "separation + multi-date stability + "
            "direction robustness + non-redundancy."
        )
    )


if __name__ == "__main__":

    main()