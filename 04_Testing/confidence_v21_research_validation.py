"""
PulseViper XAU AI
Confidence v2.1 Historical Holdout / OOS Research Validator

Research-only. Does not modify production engines or model live profitability.

Default:
python 04_Testing/confidence_v21_research_validation.py --bars 60000 --discovery-days 10 --embargo-days 1 --oos-days 10 --skip-recent-days 10
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# -----------------------------------------------------------------------------
# Project bootstrap
# -----------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


fetcher_module: Any = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
)

pipeline_module: Any = importlib.import_module(
    "02_AI.Core.scalping_pipeline"
)

fetcher: Any = (
    fetcher_module.fetcher
)

scalping_pipeline: Any = (
    pipeline_module.scalping_pipeline
)


# -----------------------------------------------------------------------------
# Research contract
# -----------------------------------------------------------------------------

FORWARD_HORIZONS: tuple[
    int,
    ...,
] = (
    5,
    10,
    20,
)


FEATURES: tuple[
    tuple[
        str,
        str,
    ],
    ...,
] = (
    (
        "Sweep -> READY Bars",
        "setup_sweep_to_ready_bars",
    ),
    (
        "Rejection Fill %",
        "setup_rejection_fill_percent",
    ),
    (
        "Impulse Strength",
        "setup_impulse_strength",
    ),
    (
        "BOS Strength ATR",
        "setup_bos_strength_atr",
    ),
    (
        "Displacement Score",
        "setup_displacement_score",
    ),
    (
        "FVG Count",
        "setup_fvg_count",
    ),
    (
        "Setup Age Bars",
        "setup_age_bars",
    ),
)


REDUNDANCY_FEATURES: tuple[
    str,
    ...,
] = (
    "setup_sweep_to_ready_bars",
    "setup_age_bars",
    "setup_rejection_fill_percent",
    "setup_impulse_strength",
    "setup_bos_strength_atr",
    "setup_break_distance_atr",
    "setup_displacement_score",
    "setup_fvg_count",
)


CONFIDENCE_BUCKET_ORDER: tuple[
    str,
    ...,
] = (
    "<85",
    "85-89",
    "90-94",
    "95-99",
    "100",
)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _separator(
    char: str = "=",
    width: int = 96,
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


def _subsection(
    title: str,
) -> None:

    print()

    print(
        title
    )

    print(
        "-"
        * min(
            96,
            max(
                20,
                len(
                    title
                ),
            ),
        )
    )


def _to_numeric(
    series: pd.Series,
) -> pd.Series:

    converted: Any = pd.to_numeric(
        series,
        errors="coerce",
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

    number = _as_float(
        value
    )

    if not np.isfinite(
        number
    ):

        return "NA"

    return (
        f"{number:.{decimals}f}"
    )


def _safe_median(
    series: pd.Series,
) -> float:

    numeric = (
        _to_numeric(
            series
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

    if numeric.empty:

        return np.nan

    return _as_float(
        numeric.median()
    )


def _date_labels(
    df: pd.DataFrame,
) -> pd.Series:

    times: Any = pd.to_datetime(
        df[
            "time"
        ],
        errors="coerce",
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


# -----------------------------------------------------------------------------
# Complete-day detection
# -----------------------------------------------------------------------------

def _complete_dates(
    df: pd.DataFrame,
) -> list[
    str
]:

    labels = (
        _date_labels(
            df
        )
        .dropna()
    )

    if labels.empty:

        raise RuntimeError(
            "No valid dates found in pipeline output."
        )

    counts = (
        labels
        .value_counts()
        .sort_index()
    )

    if counts.empty:

        raise RuntimeError(
            "No date counts could be calculated."
        )

    maximum_bars = int(
        _as_float(
            counts.max(),
            0.0,
        )
    )

    completeness_floor = max(
        300,
        int(
            np.ceil(
                maximum_bars
                * 0.80
            )
        ),
    )

    result: list[
        str
    ] = []

    for (
        date_value,
        count_value,
    ) in (
        counts.items()
    ):

        count_number = _as_float(
            count_value,
            0.0,
        )

        if (
            count_number
            >= float(
                completeness_floor
            )
        ):

            result.append(
                str(
                    date_value
                )
            )

    if not result:

        raise RuntimeError(
            "No sufficiently complete trading dates found."
        )

    return result


# -----------------------------------------------------------------------------
# Discovery / embargo / OOS split
# -----------------------------------------------------------------------------

def _build_research_split(
    all_complete_dates: list[
        str
    ],
    discovery_days: int,
    embargo_days: int,
    oos_days: int,
    skip_recent_days: int,
) -> tuple[
    list[str],
    list[str],
    list[str],
    list[str],
]:

    if discovery_days <= 0:

        raise ValueError(
            "--discovery-days must be > 0"
        )

    if embargo_days < 0:

        raise ValueError(
            "--embargo-days cannot be negative"
        )

    if oos_days <= 0:

        raise ValueError(
            "--oos-days must be > 0"
        )

    if skip_recent_days < 0:

        raise ValueError(
            "--skip-recent-days cannot be negative"
        )

    needed = (
        discovery_days
        + embargo_days
        + oos_days
        + skip_recent_days
    )

    if (
        len(
            all_complete_dates
        )
        < needed
    ):

        raise RuntimeError(
            (
                f"Need at least {needed} complete dates, "
                f"found {len(all_complete_dates)}. "
                "Increase --bars or reduce split sizes."
            )
        )

    if (
        skip_recent_days
        > 0
    ):

        skipped_recent = (
            all_complete_dates[
                -skip_recent_days:
            ]
        )

        eligible = (
            all_complete_dates[
                :-skip_recent_days
            ]
        )

    else:

        skipped_recent = []

        eligible = (
            all_complete_dates.copy()
        )

    window_size = (
        discovery_days
        + embargo_days
        + oos_days
    )

    research_dates = (
        eligible[
            -window_size:
        ]
    )

    discovery = (
        research_dates[
            :discovery_days
        ]
    )

    embargo_end = (
        discovery_days
        + embargo_days
    )

    embargo = (
        research_dates[
            discovery_days:
            embargo_end
        ]
    )

    oos = (
        research_dates[
            embargo_end:
        ]
    )

    return (
        discovery,
        embargo,
        oos,
        skipped_recent,
    )


# -----------------------------------------------------------------------------
# Forward outcome
# -----------------------------------------------------------------------------

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

    entry = _as_float(
        df.iloc[
            position
        ][
            "close"
        ]
    )

    if not np.isfinite(
        entry
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

    endpoint = _as_float(
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
            endpoint,
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
            - entry
        ) / atr_value

        mae = (
            entry
            - future_low
        ) / atr_value

        net = (
            endpoint
            - entry
        ) / atr_value

    elif (
        normalized_direction
        == "BEARISH"
    ):

        mfe = (
            entry
            - future_low
        ) / atr_value

        mae = (
            future_high
            - entry
        ) / atr_value

        net = (
            entry
            - endpoint
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


# -----------------------------------------------------------------------------
# 1 ATR / 1 ATR first-touch
# -----------------------------------------------------------------------------

def _first_touch_1_to_1(
    df: pd.DataFrame,
    position: int,
    direction: str,
    atr_value: float,
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

    entry = _as_float(
        df.iloc[
            position
        ][
            "close"
        ]
    )

    if not np.isfinite(
        entry
    ):

        return "INVALID"

    normalized_direction = (
        direction.upper()
    )

    if (
        normalized_direction
        == "BULLISH"
    ):

        target = (
            entry
            + atr_value
        )

        stop = (
            entry
            - atr_value
        )

    elif (
        normalized_direction
        == "BEARISH"
    ):

        target = (
            entry
            - atr_value
        )

        stop = (
            entry
            + atr_value
        )

    else:

        return "INVALID"

    for future_position in range(
        position + 1,
        end_position + 1,
    ):

        row = df.iloc[
            future_position
        ]

        high = _as_float(
            row.get(
                "high",
                np.nan,
            )
        )

        low = _as_float(
            row.get(
                "low",
                np.nan,
            )
        )

        if (
            not np.isfinite(
                high
            )
            or
            not np.isfinite(
                low
            )
        ):

            continue

        if (
            normalized_direction
            == "BULLISH"
        ):

            target_hit = (
                high
                >= target
            )

            stop_hit = (
                low
                <= stop
            )

        else:

            target_hit = (
                low
                <= target
            )

            stop_hit = (
                high
                >= stop
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


# -----------------------------------------------------------------------------
# Build trade-ready event frame
# -----------------------------------------------------------------------------

def _build_event_frame(
    df: pd.DataFrame,
) -> pd.DataFrame:

    required = {
        "time",
        "open",
        "high",
        "low",
        "close",
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

        raise RuntimeError(
            (
                "Pipeline output missing required columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )
        )

    date_labels = _date_labels(
        df
    )

    time_values: Any = pd.to_datetime(
        df[
            "time"
        ],
        errors="coerce",
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

    positions = (
        np.flatnonzero(
            ready_mask
        )
    )

    snapshot_columns: tuple[
        str,
        ...,
    ] = (
        "setup_id",
        "setup_age_bars",
        "setup_structure_alignment",
        "setup_bos_scope",
        "setup_bos_event_scope",
        "setup_bos_context",
        "setup_displacement_score",
        "setup_impulse_strength",
        "setup_bos_strength_atr",
        "setup_break_distance_atr",
        "setup_rejection_fill_percent",
        "setup_sweep_to_ready_bars",
        "setup_fvg_count",
        "confidence_score",
        "confidence_confluence",
    )

    records: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for raw_position in (
        positions.tolist()
    ):

        position = int(
            raw_position
        )

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

        raw_date = (
            date_labels.iloc[
                position
            ]
        )

        if pd.isna(
            raw_date
        ):

            continue

        atr_value = _as_float(
            row.get(
                "atr",
                np.nan,
            )
        )

        record: dict[
            str,
            Any,
        ] = {
            "position": position,

            "time": (
                time_values.iloc[
                    position
                ]
            ),

            "date_label": (
                str(
                    raw_date
                )
            ),

            "direction": (
                direction
            ),

            "atr": (
                atr_value
            ),

            "entry_close": (
                _as_float(
                    row.get(
                        "close",
                        np.nan,
                    )
                )
            ),
        }

        for column in (
            snapshot_columns
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

        record[
            "first_touch_1_to_1"
        ] = _first_touch_1_to_1(
            df=df,
            position=position,
            direction=direction,
            atr_value=atr_value,
            horizon=20,
        )

        records.append(
            record
        )

    return pd.DataFrame(
        records
    )


# -----------------------------------------------------------------------------
# Outcome statistics
# -----------------------------------------------------------------------------

def _summary(
    frame: pd.DataFrame,
) -> dict[
    str,
    Any,
]:

    result: dict[
        str,
        Any,
    ] = {
        "n": int(
            len(
                frame
            )
        ),
    }

    for horizon in (
        FORWARD_HORIZONS
    ):

        net_column = (
            f"net_{horizon}"
        )

        mfe_column = (
            f"mfe_{horizon}"
        )

        if (
            net_column
            not in frame.columns
            or
            mfe_column
            not in frame.columns
        ):

            result[
                f"net{horizon}_median"
            ] = np.nan

            result[
                f"net{horizon}_mean"
            ] = np.nan

            result[
                f"positive{horizon}_pct"
            ] = np.nan

            result[
                f"mfe{horizon}_1atr_pct"
            ] = np.nan

            continue

        net = (
            _to_numeric(
                frame[
                    net_column
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

        mfe = (
            _to_numeric(
                frame[
                    mfe_column
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

        if net.empty:

            result[
                f"net{horizon}_median"
            ] = np.nan

            result[
                f"net{horizon}_mean"
            ] = np.nan

            result[
                f"positive{horizon}_pct"
            ] = np.nan

        else:

            result[
                f"net{horizon}_median"
            ] = _as_float(
                net.median()
            )

            result[
                f"net{horizon}_mean"
            ] = _as_float(
                net.mean()
            )

            result[
                f"positive{horizon}_pct"
            ] = float(
                (
                    net
                    > 0.0
                ).mean()
                * 100.0
            )

        if mfe.empty:

            result[
                f"mfe{horizon}_1atr_pct"
            ] = np.nan

        else:

            result[
                f"mfe{horizon}_1atr_pct"
            ] = float(
                (
                    mfe
                    >= 1.0
                ).mean()
                * 100.0
            )

    if (
        "first_touch_1_to_1"
        in frame.columns
    ):

        resolved = frame.loc[
            frame[
                "first_touch_1_to_1"
            ].isin(
                [
                    "TARGET",
                    "STOP",
                ]
            ),
            "first_touch_1_to_1",
        ]

        if resolved.empty:

            result[
                "target_1_to_1_pct"
            ] = np.nan

        else:

            result[
                "target_1_to_1_pct"
            ] = float(
                (
                    resolved
                    == "TARGET"
                ).mean()
                * 100.0
            )

    else:

        result[
            "target_1_to_1_pct"
        ] = np.nan

    return result


def _print_summary(
    label: str,
    frame: pd.DataFrame,
) -> None:

    stats = _summary(
        frame
    )

    print(
        f"{label:<12}"
        f" n={stats['n']:<4}"
        f" net5={_fmt(stats['net5_median']):>7}"
        f" net10={_fmt(stats['net10_median']):>7}"
        f" net20={_fmt(stats['net20_median']):>7}"
        f" pos20={_fmt(stats['positive20_pct'], 1):>6}%"
        f" 1R-first={_fmt(stats['target_1_to_1_pct'], 1):>6}%"
    )


# -----------------------------------------------------------------------------
# Discovery-fitted quantile edges
# -----------------------------------------------------------------------------

def _fit_quantile_edges(
    values: pd.Series,
    requested_bins: int = 4,
) -> list[
    float
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
        .dropna()
    )

    if numeric.empty:

        return []

    unique_count = int(
        numeric.nunique()
    )

    if unique_count <= 1:

        return [
            _as_float(
                numeric.iloc[
                    0
                ]
            )
        ]

    bins = min(
        requested_bins,
        unique_count,
    )

    quantiles = np.linspace(
        0.0,
        1.0,
        bins + 1,
        dtype=np.float64,
    )

    raw_edges = np.quantile(
        numeric.to_numpy(
            dtype=np.float64
        ),
        quantiles,
    )

    edges: list[
        float
    ] = sorted(
        {
            float(
                value
            )
            for value
            in raw_edges.tolist()
        }
    )

    return edges


def _apply_edges(
    values: pd.Series,
    edges: list[
        float
    ],
) -> pd.Series:

    numeric = _to_numeric(
        values
    )

    if not edges:

        return pd.Series(
            [
                "NA"
            ]
            * len(
                values
            ),
            index=values.index,
            dtype="object",
        )

    if len(
        edges
    ) == 1:

        labels = [
            (
                "ALL"
                if np.isfinite(
                    _as_float(
                        value
                    )
                )
                else "NA"
            )
            for value
            in numeric.tolist()
        ]

        return pd.Series(
            labels,
            index=values.index,
            dtype="object",
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
            number,
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
                    f"Q{number}"
                )

        return (
            f"Q{len(internal_edges) + 1}"
        )

    labels = [
        classify(
            value
        )
        for value
        in numeric.tolist()
    ]

    return pd.Series(
        labels,
        index=values.index,
        dtype="object",
    )


def _bucket_order(
    label: str,
) -> int:

    if label.startswith(
        "Q"
    ):

        try:

            return int(
                label[
                    1:
                ]
            )

        except ValueError:

            return 999

    if (
        label
        == "ALL"
    ):

        return 0

    return 999


# -----------------------------------------------------------------------------
# Bucket summary
# -----------------------------------------------------------------------------

def _bucket_table(
    frame: pd.DataFrame,
    bucket: pd.Series,
) -> pd.DataFrame:

    if frame.empty:

        return pd.DataFrame()

    working = frame.copy()

    working[
        "_research_bucket"
    ] = pd.Series(
        bucket.tolist(),
        index=working.index,
        dtype="object",
    )

    records: list[
        dict[
            str,
            Any,
        ]
    ] = []

    grouped = working.groupby(
        "_research_bucket",
        observed=True,
        dropna=False,
    )

    for (
        raw_bucket,
        group,
    ) in grouped:

        bucket_name = str(
            raw_bucket
        )

        if (
            bucket_name
            == "NA"
        ):

            continue

        stats = _summary(
            group
        )

        records.append(
            {
                "bucket": (
                    bucket_name
                ),

                "n": (
                    stats[
                        "n"
                    ]
                ),

                "net5_med": round(
                    _as_float(
                        stats[
                            "net5_median"
                        ]
                    ),
                    3,
                ),

                "net10_med": round(
                    _as_float(
                        stats[
                            "net10_median"
                        ]
                    ),
                    3,
                ),

                "net20_med": round(
                    _as_float(
                        stats[
                            "net20_median"
                        ]
                    ),
                    3,
                ),

                "pos20_pct": round(
                    _as_float(
                        stats[
                            "positive20_pct"
                        ]
                    ),
                    1,
                ),

                "1R_first_pct": round(
                    _as_float(
                        stats[
                            "target_1_to_1_pct"
                        ]
                    ),
                    1,
                ),
            }
        )

    if not records:

        return pd.DataFrame()

    result = pd.DataFrame(
        records
    )

    result[
        "_sort_order"
    ] = [
        _bucket_order(
            str(
                value
            )
        )
        for value
        in result[
            "bucket"
        ].tolist()
    ]

    result = (
        result
        .sort_values(
            [
                "_sort_order",
                "bucket",
            ]
        )
        .drop(
            columns=[
                "_sort_order"
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return result


# -----------------------------------------------------------------------------
# Discovery best/worst selection
# -----------------------------------------------------------------------------

def _select_discovery_bucket(
    table: pd.DataFrame,
    best: bool,
    minimum_events: int,
) -> str:

    if table.empty:

        return ""

    eligible = table.loc[
        _to_numeric(
            table[
                "n"
            ]
        )
        >= float(
            minimum_events
        )
    ].copy()

    if eligible.empty:

        return ""

    eligible = eligible.sort_values(
        [
            "net20_med",
            "net10_med",
            "pos20_pct",
        ],
        ascending=(
            not best,
            not best,
            not best,
        ),
    )

    return str(
        eligible.iloc[
            0
        ][
            "bucket"
        ]
    )


def _selected_vs_rest(
    frame: pd.DataFrame,
    bucket: pd.Series,
    selected_bucket: str,
) -> dict[
    str,
    Any,
]:

    if (
        frame.empty
        or
        not selected_bucket
    ):

        return {
            "selected_n": 0,
            "rest_n": 0,
            "selected_net20": np.nan,
            "rest_net20": np.nan,
            "spread20": np.nan,
        }

    labels = pd.Series(
        bucket.tolist(),
        index=frame.index,
        dtype="object",
    )

    selected_mask = (
        labels
        == selected_bucket
    )

    selected = frame.loc[
        selected_mask
    ]

    rest = frame.loc[
        ~selected_mask
    ]

    selected_stats = _summary(
        selected
    )

    rest_stats = _summary(
        rest
    )

    selected_net20 = _as_float(
        selected_stats[
            "net20_median"
        ]
    )

    rest_net20 = _as_float(
        rest_stats[
            "net20_median"
        ]
    )

    if (
        np.isfinite(
            selected_net20
        )
        and
        np.isfinite(
            rest_net20
        )
    ):

        spread = (
            selected_net20
            - rest_net20
        )

    else:

        spread = np.nan

    return {
        "selected_n": int(
            len(
                selected
            )
        ),

        "rest_n": int(
            len(
                rest
            )
        ),

        "selected_net20": (
            selected_net20
        ),

        "rest_net20": (
            rest_net20
        ),

        "spread20": (
            spread
        ),
    }


def _bucket_verdict(
    discovery_result: dict[
        str,
        Any,
    ],
    oos_result: dict[
        str,
        Any,
    ],
    minimum_events: int,
    best: bool,
) -> str:

    oos_n = int(
        oos_result.get(
            "selected_n",
            0,
        )
    )

    if (
        oos_n
        < minimum_events
    ):

        return "INSUFFICIENT_OOS"

    discovery_spread = _as_float(
        discovery_result.get(
            "spread20",
            np.nan,
        )
    )

    oos_spread = _as_float(
        oos_result.get(
            "spread20",
            np.nan,
        )
    )

    if (
        not np.isfinite(
            discovery_spread
        )
        or
        not np.isfinite(
            oos_spread
        )
    ):

        return "INSUFFICIENT"

    if best:

        discovery_correct = (
            discovery_spread
            > 0.0
        )

        oos_correct = (
            oos_spread
            > 0.0
        )

    else:

        discovery_correct = (
            discovery_spread
            < 0.0
        )

        oos_correct = (
            oos_spread
            < 0.0
        )

    if (
        discovery_correct
        and
        oos_correct
        and
        abs(
            oos_spread
        )
        >= 0.20
    ):

        return "OOS_CONFIRMED"

    if (
        discovery_correct
        and
        oos_correct
    ):

        return "OOS_WEAK_CONFIRM"

    if (
        discovery_correct
        and
        not oos_correct
    ):

        return "OOS_REVERSED"

    return "DISCOVERY_UNCLEAR"


# -----------------------------------------------------------------------------
# Median HIGH / LOW
# -----------------------------------------------------------------------------

def _high_low_frames(
    frame: pd.DataFrame,
    feature_column: str,
    boundary: float,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:

    numeric = _to_numeric(
        frame[
            feature_column
        ]
    )

    high = frame.loc[
        numeric
        > boundary
    ]

    low = frame.loc[
        numeric
        <= boundary
    ]

    return (
        high,
        low,
    )


def _median_split_spread(
    frame: pd.DataFrame,
    feature_column: str,
    boundary: float,
    horizon: int,
) -> float:

    if (
        frame.empty
        or
        not np.isfinite(
            boundary
        )
    ):

        return np.nan

    (
        high,
        low,
    ) = _high_low_frames(
        frame,
        feature_column,
        boundary,
    )

    if (
        high.empty
        or
        low.empty
    ):

        return np.nan

    high_median = _safe_median(
        high[
            f"net_{horizon}"
        ]
    )

    low_median = _safe_median(
        low[
            f"net_{horizon}"
        ]
    )

    if (
        not np.isfinite(
            high_median
        )
        or
        not np.isfinite(
            low_median
        )
    ):

        return np.nan

    return (
        high_median
        - low_median
    )


def _date_support(
    frame: pd.DataFrame,
    feature_column: str,
    boundary: float,
    horizon: int,
    minimum_side_events: int = 2,
) -> tuple[
    int,
    int,
    int,
]:

    supports = 0
    contradicts = 0
    eligible = 0

    if frame.empty:

        return (
            supports,
            contradicts,
            eligible,
        )

    grouped = frame.groupby(
        "date_label",
        observed=True,
    )

    for (
        _,
        day,
    ) in grouped:

        (
            high,
            low,
        ) = _high_low_frames(
            day,
            feature_column,
            boundary,
        )

        if (
            len(
                high
            )
            < minimum_side_events
            or
            len(
                low
            )
            < minimum_side_events
        ):

            continue

        high_median = _safe_median(
            high[
                f"net_{horizon}"
            ]
        )

        low_median = _safe_median(
            low[
                f"net_{horizon}"
            ]
        )

        if (
            not np.isfinite(
                high_median
            )
            or
            not np.isfinite(
                low_median
            )
        ):

            continue

        eligible += 1

        if (
            high_median
            > low_median
        ):

            supports += 1

        else:

            contradicts += 1

    return (
        supports,
        contradicts,
        eligible,
    )


# -----------------------------------------------------------------------------
# Current Confidence benchmark
# -----------------------------------------------------------------------------

def _confidence_bucket_label(
    value: Any,
) -> str:

    score = _as_float(
        value
    )

    if not np.isfinite(
        score
    ):

        return "NA"

    if score < 85.0:

        return "<85"

    if score < 90.0:

        return "85-89"

    if score < 95.0:

        return "90-94"

    if score < 100.0:

        return "95-99"

    return "100"


def _confidence_table(
    frame: pd.DataFrame,
) -> pd.DataFrame:

    if (
        frame.empty
        or
        "confidence_score"
        not in frame.columns
    ):

        return pd.DataFrame()

    labels = pd.Series(
        [
            _confidence_bucket_label(
                value
            )
            for value
            in frame[
                "confidence_score"
            ].tolist()
        ],
        index=frame.index,
        dtype="object",
    )

    records: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for bucket_name in (
        CONFIDENCE_BUCKET_ORDER
    ):

        group = frame.loc[
            labels
            == bucket_name
        ]

        if group.empty:

            continue

        stats = _summary(
            group
        )

        records.append(
            {
                "confidence_bucket": (
                    bucket_name
                ),

                "n": (
                    stats[
                        "n"
                    ]
                ),

                "net5_med": round(
                    _as_float(
                        stats[
                            "net5_median"
                        ]
                    ),
                    3,
                ),

                "net10_med": round(
                    _as_float(
                        stats[
                            "net10_median"
                        ]
                    ),
                    3,
                ),

                "net20_med": round(
                    _as_float(
                        stats[
                            "net20_median"
                        ]
                    ),
                    3,
                ),

                "pos20_pct": round(
                    _as_float(
                        stats[
                            "positive20_pct"
                        ]
                    ),
                    1,
                ),

                "1R_first_pct": round(
                    _as_float(
                        stats[
                            "target_1_to_1_pct"
                        ]
                    ),
                    1,
                ),
            }
        )

    return pd.DataFrame(
        records
    )


def _confidence_monotonicity(
    table: pd.DataFrame,
) -> str:

    if (
        table.empty
        or
        len(
            table
        )
        < 3
    ):

        return "INSUFFICIENT"

    values = _to_numeric(
        table[
            "net20_med"
        ]
    ).to_numpy(
        dtype=np.float64
    )

    differences = np.diff(
        values
    )

    if np.all(
        differences
        >= 0.0
    ):

        return "MONOTONIC"

    positive_steps = int(
        np.sum(
            differences
            > 0.0
        )
    )

    negative_steps = int(
        np.sum(
            differences
            < 0.0
        )
    )

    if (
        positive_steps
        > negative_steps
    ):

        return "MOSTLY_INCREASING"

    return "NON_MONOTONIC"


# -----------------------------------------------------------------------------
# Correlation / redundancy
# -----------------------------------------------------------------------------

def _redundancy_table(
    frame: pd.DataFrame,
    threshold: float = 0.70,
) -> pd.DataFrame:

    available = [
        column
        for column
        in REDUNDANCY_FEATURES
        if column
        in frame.columns
    ]

    if (
        len(
            available
        )
        < 2
    ):

        return pd.DataFrame()

    numeric = pd.DataFrame(
        {
            column: _to_numeric(
                frame[
                    column
                ]
            )
            for column
            in available
        }
    )

    correlation = numeric.corr(
        method="spearman"
    )

    matrix = correlation.to_numpy(
        dtype=np.float64
    )

    records: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for left in range(
        len(
            available
        )
    ):

        for right in range(
            left + 1,
            len(
                available
            ),
        ):

            rho: float = float(
                matrix[
                    left,
                    right,
                ]
            )

            if (
                np.isfinite(
                    rho
                )
                and
                abs(
                    rho
                )
                >= threshold
            ):

                records.append(
                    {
                        "feature_a": (
                            available[
                                left
                            ]
                        ),

                        "feature_b": (
                            available[
                                right
                            ]
                        ),

                        "spearman_rho": round(
                            rho,
                            3,
                        ),
                    }
                )

    if not records:

        return pd.DataFrame()

    result = pd.DataFrame(
        records
    )

    result[
        "_abs"
    ] = _to_numeric(
        result[
            "spearman_rho"
        ]
    ).abs()

    result = (
        result
        .sort_values(
            "_abs",
            ascending=False,
        )
        .drop(
            columns=[
                "_abs"
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return result


# -----------------------------------------------------------------------------
# Direction bucket output
# -----------------------------------------------------------------------------

def _print_direction_buckets(
    frame: pd.DataFrame,
    feature_column: str,
    edges: list[
        float
    ],
    label: str,
) -> None:

    _subsection(
        f"{label} direction split"
    )

    for direction in (
        "BULLISH",
        "BEARISH",
    ):

        subset = frame.loc[
            frame[
                "direction"
            ]
            == direction
        ]

        if subset.empty:

            continue

        bucket = _apply_edges(
            subset[
                feature_column
            ],
            edges,
        )

        table = _bucket_table(
            subset,
            bucket,
        )

        print()

        print(
            direction
        )

        if table.empty:

            print(
                "No usable samples."
            )

        else:

            print(
                table.to_string(
                    index=False
                )
            )


# -----------------------------------------------------------------------------
# Individual feature research
# -----------------------------------------------------------------------------

def _feature_research(
    discovery: pd.DataFrame,
    oos: pd.DataFrame,
    feature_name: str,
    feature_column: str,
    minimum_bucket_events: int,
) -> dict[
    str,
    Any,
]:

    _section(
        f"FEATURE HOLDOUT TEST: {feature_name}"
    )

    if (
        feature_column
        not in discovery.columns
        or
        feature_column
        not in oos.columns
    ):

        print(
            f"Missing feature column: {feature_column}"
        )

        return {
            "feature": feature_name,
            "best_bucket": "",
            "best_verdict": "MISSING",
            "worst_bucket": "",
            "worst_verdict": "MISSING",
        }

    discovery_values = (
        _to_numeric(
            discovery[
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

    oos_values = (
        _to_numeric(
            oos[
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

    edges = _fit_quantile_edges(
        discovery_values
    )

    if not edges:

        print(
            "No usable DISCOVERY values."
        )

        return {
            "feature": feature_name,
            "best_bucket": "",
            "best_verdict": "NO_DATA",
            "worst_bucket": "",
            "worst_verdict": "NO_DATA",
        }

    print(
        (
            "DISCOVERY-fitted boundaries: "
            +
            ", ".join(
                _fmt(
                    value
                )
                for value
                in edges
            )
        )
    )

    discovery_bucket = _apply_edges(
        discovery_values,
        edges,
    )

    oos_bucket = _apply_edges(
        oos_values,
        edges,
    )

    discovery_table = _bucket_table(
        discovery,
        discovery_bucket,
    )

    oos_table = _bucket_table(
        oos,
        oos_bucket,
    )

    _subsection(
        "DISCOVERY buckets"
    )

    if discovery_table.empty:

        print(
            "No usable buckets."
        )

    else:

        print(
            discovery_table.to_string(
                index=False
            )
        )

    _subsection(
        "OOS buckets — frozen DISCOVERY boundaries"
    )

    if oos_table.empty:

        print(
            "No usable OOS buckets."
        )

    else:

        print(
            oos_table.to_string(
                index=False
            )
        )

    best_bucket = _select_discovery_bucket(
        discovery_table,
        best=True,
        minimum_events=minimum_bucket_events,
    )

    worst_bucket = _select_discovery_bucket(
        discovery_table,
        best=False,
        minimum_events=minimum_bucket_events,
    )

    discovery_best = _selected_vs_rest(
        discovery,
        discovery_bucket,
        best_bucket,
    )

    oos_best = _selected_vs_rest(
        oos,
        oos_bucket,
        best_bucket,
    )

    discovery_worst = _selected_vs_rest(
        discovery,
        discovery_bucket,
        worst_bucket,
    )

    oos_worst = _selected_vs_rest(
        oos,
        oos_bucket,
        worst_bucket,
    )

    best_verdict = _bucket_verdict(
        discovery_best,
        oos_best,
        minimum_bucket_events,
        best=True,
    )

    worst_verdict = _bucket_verdict(
        discovery_worst,
        oos_worst,
        minimum_bucket_events,
        best=False,
    )

    _subsection(
        "Discovery-selected bucket transfer"
    )

    print(
        (
            f"BEST {best_bucket or 'NA'}"
            f" | DISC spread20={_fmt(discovery_best['spread20'])}"
            f" | OOS spread20={_fmt(oos_best['spread20'])}"
            f" | OOS n={oos_best['selected_n']}"
            f" | {best_verdict}"
        )
    )

    print(
        (
            f"WORST {worst_bucket or 'NA'}"
            f" | DISC spread20={_fmt(discovery_worst['spread20'])}"
            f" | OOS spread20={_fmt(oos_worst['spread20'])}"
            f" | OOS n={oos_worst['selected_n']}"
            f" | {worst_verdict}"
        )
    )

    median_boundary = _safe_median(
        discovery_values
    )

    _subsection(
        "DISCOVERY median HIGH vs LOW transfer"
    )

    print(
        f"Frozen median boundary: {_fmt(median_boundary)}"
    )

    median_oos_spread20 = np.nan

    oos_support20: tuple[
        int,
        int,
        int,
    ] = (
        0,
        0,
        0,
    )

    for horizon in (
        FORWARD_HORIZONS
    ):

        discovery_spread = _median_split_spread(
            discovery,
            feature_column,
            median_boundary,
            horizon,
        )

        oos_spread = _median_split_spread(
            oos,
            feature_column,
            median_boundary,
            horizon,
        )

        discovery_support = _date_support(
            discovery,
            feature_column,
            median_boundary,
            horizon,
        )

        oos_support = _date_support(
            oos,
            feature_column,
            median_boundary,
            horizon,
        )

        if (
            horizon
            == 20
        ):

            median_oos_spread20 = (
                oos_spread
            )

            oos_support20 = (
                oos_support
            )

        print(
            (
                f"{horizon:>2} bars"
                f" | DISC high-low={_fmt(discovery_spread):>7}"
                f" | OOS high-low={_fmt(oos_spread):>7}"
                f" | DISC dates={discovery_support[0]}/{discovery_support[2]}"
                f" | OOS dates={oos_support[0]}/{oos_support[2]}"
            )
        )

    _print_direction_buckets(
        discovery,
        feature_column,
        edges,
        "DISCOVERY",
    )

    _print_direction_buckets(
        oos,
        feature_column,
        edges,
        "OOS",
    )

    return {
        "feature": (
            feature_name
        ),

        "best_bucket": (
            best_bucket
        ),

        "best_disc_spread20": (
            discovery_best[
                "spread20"
            ]
        ),

        "best_oos_spread20": (
            oos_best[
                "spread20"
            ]
        ),

        "best_verdict": (
            best_verdict
        ),

        "worst_bucket": (
            worst_bucket
        ),

        "worst_oos_spread20": (
            oos_worst[
                "spread20"
            ]
        ),

        "worst_verdict": (
            worst_verdict
        ),

        "median_oos_spread20": (
            median_oos_spread20
        ),

        "median_oos_support_dates": (
            oos_support20[
                0
            ]
        ),

        "median_oos_eligible_dates": (
            oos_support20[
                2
            ]
        ),
    }


# -----------------------------------------------------------------------------
# Daily baseline
# -----------------------------------------------------------------------------

def _daily_outcome_table(
    frame: pd.DataFrame,
) -> pd.DataFrame:

    if frame.empty:

        return pd.DataFrame()

    records: list[
        dict[
            str,
            Any,
        ]
    ] = []

    grouped = frame.groupby(
        "date_label",
        observed=True,
    )

    for (
        raw_date,
        day,
    ) in grouped:

        stats = _summary(
            day
        )

        records.append(
            {
                "date": (
                    str(
                        raw_date
                    )
                ),

                "n": (
                    stats[
                        "n"
                    ]
                ),

                "net5_med": round(
                    _as_float(
                        stats[
                            "net5_median"
                        ]
                    ),
                    3,
                ),

                "net10_med": round(
                    _as_float(
                        stats[
                            "net10_median"
                        ]
                    ),
                    3,
                ),

                "net20_med": round(
                    _as_float(
                        stats[
                            "net20_median"
                        ]
                    ),
                    3,
                ),

                "pos20_pct": round(
                    _as_float(
                        stats[
                            "positive20_pct"
                        ]
                    ),
                    1,
                ),

                "1R_first_pct": round(
                    _as_float(
                        stats[
                            "target_1_to_1_pct"
                        ]
                    ),
                    1,
                ),
            }
        )

    return pd.DataFrame(
        records
    )


# -----------------------------------------------------------------------------
# Final candidate matrix
# -----------------------------------------------------------------------------

def _candidate_matrix(
    results: list[
        dict[
            str,
            Any,
        ]
    ],
) -> pd.DataFrame:

    rows: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for result in (
        results
    ):

        eligible = int(
            result.get(
                "median_oos_eligible_dates",
                0,
            )
        )

        support = int(
            result.get(
                "median_oos_support_dates",
                0,
            )
        )

        if eligible > 0:

            support_rate = (
                support
                / eligible
                * 100.0
            )

        else:

            support_rate = np.nan

        rows.append(
            {
                "feature": (
                    result.get(
                        "feature",
                        "",
                    )
                ),

                "best_bucket": (
                    result.get(
                        "best_bucket",
                        "",
                    )
                ),

                "best_disc_spread20": round(
                    _as_float(
                        result.get(
                            "best_disc_spread20",
                            np.nan,
                        )
                    ),
                    3,
                ),

                "best_oos_spread20": round(
                    _as_float(
                        result.get(
                            "best_oos_spread20",
                            np.nan,
                        )
                    ),
                    3,
                ),

                "best_verdict": (
                    result.get(
                        "best_verdict",
                        "",
                    )
                ),

                "worst_bucket": (
                    result.get(
                        "worst_bucket",
                        "",
                    )
                ),

                "worst_oos_spread20": round(
                    _as_float(
                        result.get(
                            "worst_oos_spread20",
                            np.nan,
                        )
                    ),
                    3,
                ),

                "worst_verdict": (
                    result.get(
                        "worst_verdict",
                        "",
                    )
                ),

                "median_oos_high_low20": round(
                    _as_float(
                        result.get(
                            "median_oos_spread20",
                            np.nan,
                        )
                    ),
                    3,
                ),

                "oos_high_support_pct": round(
                    support_rate,
                    1,
                ),
            }
        )

    return pd.DataFrame(
        rows
    )


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "PulseViper Confidence v2.1 "
            "historical holdout validator"
        )
    )

    parser.add_argument(
        "--bars",
        type=int,
        default=60000,
    )

    parser.add_argument(
        "--symbol",
        type=str,
        default="XAUUSDm",
    )

    parser.add_argument(
        "--discovery-days",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--embargo-days",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--oos-days",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--skip-recent-days",
        type=int,
        default=10,
        help=(
            "Exclude most-recent complete days "
            "already inspected."
        ),
    )

    parser.add_argument(
        "--min-bucket-events",
        type=int,
        default=8,
    )

    args = parser.parse_args()

    if (
        args.bars
        <= 0
    ):

        raise ValueError(
            "--bars must be > 0"
        )

    if (
        args.min_bucket_events
        <= 0
    ):

        raise ValueError(
            "--min-bucket-events must be > 0"
        )

    _section(
        "PulseViper Confidence v2.1 Research Validation"
    )

    print(
        f"Project root       : {PROJECT_ROOT}"
    )

    print(
        f"Requested symbol   : {args.symbol}"
    )

    print(
        f"Requested M1 bars  : {args.bars}"
    )

    print(
        f"Discovery days     : {args.discovery_days}"
    )

    print(
        f"Embargo days       : {args.embargo_days}"
    )

    print(
        f"OOS days           : {args.oos_days}"
    )

    print(
        f"Skip recent days   : {args.skip_recent_days}"
    )

    print()

    print(
        "Fetching MT5 history..."
    )

    raw: pd.DataFrame = fetcher.fetch(
        symbol=args.symbol,
        bars=args.bars,
    )

    if raw.empty:

        raise RuntimeError(
            "MT5 returned no usable bars."
        )

    print(
        f"Fetched valid bars : {len(raw)}"
    )

    resolved_symbol = str(
        getattr(
            fetcher,
            "last_resolved_symbol",
            "",
        )
    )

    if resolved_symbol:

        print(
            f"Resolved symbol    : {resolved_symbol}"
        )

    print()

    print(
        "Running canonical temporal scalping pipeline..."
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

    all_dates = _complete_dates(
        enriched
    )

    (
        discovery_dates,
        embargo_dates,
        oos_dates,
        skipped_recent_dates,
    ) = _build_research_split(
        all_complete_dates=all_dates,
        discovery_days=args.discovery_days,
        embargo_days=args.embargo_days,
        oos_days=args.oos_days,
        skip_recent_days=args.skip_recent_days,
    )

    _section(
        "CHRONOLOGICAL RESEARCH SPLIT"
    )

    print(
        "DISCOVERY:"
    )

    for value in (
        discovery_dates
    ):

        print(
            f"  {value}"
        )

    print()

    print(
        "EMBARGO:"
    )

    if embargo_dates:

        for value in (
            embargo_dates
        ):

            print(
                f"  {value}"
            )

    else:

        print(
            "  <none>"
        )

    print()

    print(
        "OOS:"
    )

    for value in (
        oos_dates
    ):

        print(
            f"  {value}"
        )

    print()

    print(
        "SKIPPED RECENT / PREVIOUSLY INSPECTED:"
    )

    if skipped_recent_dates:

        for value in (
            skipped_recent_dates
        ):

            print(
                f"  {value}"
            )

    else:

        print(
            "  <none>"
        )

    print()

    print(
        "Building one-shot trade_ready event dataset..."
    )

    events = _build_event_frame(
        enriched
    )

    if events.empty:

        raise RuntimeError(
            "Pipeline produced no trade_ready events."
        )

    discovery = events.loc[
        events[
            "date_label"
        ].isin(
            discovery_dates
        )
    ].copy()

    embargo = events.loc[
        events[
            "date_label"
        ].isin(
            embargo_dates
        )
    ].copy()

    oos = events.loc[
        events[
            "date_label"
        ].isin(
            oos_dates
        )
    ].copy()

    skipped_recent = events.loc[
        events[
            "date_label"
        ].isin(
            skipped_recent_dates
        )
    ].copy()

    # -------------------------------------------------------------------------
    # Baseline
    # -------------------------------------------------------------------------

    _section(
        "BASELINE POPULATION"
    )

    _print_summary(
        "DISCOVERY",
        discovery,
    )

    _print_summary(
        "EMBARGO",
        embargo,
    )

    _print_summary(
        "OOS",
        oos,
    )

    _print_summary(
        "SKIPPED",
        skipped_recent,
    )

    _subsection(
        "DISCOVERY daily baseline"
    )

    discovery_daily = _daily_outcome_table(
        discovery
    )

    if discovery_daily.empty:

        print(
            "No discovery events."
        )

    else:

        print(
            discovery_daily.to_string(
                index=False
            )
        )

    _subsection(
        "OOS daily baseline"
    )

    oos_daily = _daily_outcome_table(
        oos
    )

    if oos_daily.empty:

        print(
            "No OOS events."
        )

    else:

        print(
            oos_daily.to_string(
                index=False
            )
        )

    # -------------------------------------------------------------------------
    # Current Confidence benchmark
    # -------------------------------------------------------------------------

    _section(
        "CURRENT CONFIDENCE v2 BENCHMARK"
    )

    discovery_confidence = _confidence_table(
        discovery
    )

    oos_confidence = _confidence_table(
        oos
    )

    _subsection(
        "DISCOVERY Confidence v2 buckets"
    )

    if discovery_confidence.empty:

        print(
            "No Confidence data."
        )

    else:

        print(
            discovery_confidence.to_string(
                index=False
            )
        )

    print(
        (
            "Monotonicity: "
            f"{_confidence_monotonicity(discovery_confidence)}"
        )
    )

    _subsection(
        "OOS Confidence v2 buckets"
    )

    if oos_confidence.empty:

        print(
            "No Confidence data."
        )

    else:

        print(
            oos_confidence.to_string(
                index=False
            )
        )

    print(
        (
            "Monotonicity: "
            f"{_confidence_monotonicity(oos_confidence)}"
        )
    )

    # -------------------------------------------------------------------------
    # Feature research
    # -------------------------------------------------------------------------

    feature_results: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for (
        feature_name,
        feature_column,
    ) in FEATURES:

        result = _feature_research(
            discovery=discovery,
            oos=oos,
            feature_name=feature_name,
            feature_column=feature_column,
            minimum_bucket_events=args.min_bucket_events,
        )

        feature_results.append(
            result
        )

    # -------------------------------------------------------------------------
    # Redundancy
    # -------------------------------------------------------------------------

    _section(
        "FEATURE REDUNDANCY — SPEARMAN |rho| >= 0.70"
    )

    _subsection(
        "DISCOVERY"
    )

    discovery_redundancy = _redundancy_table(
        discovery
    )

    if discovery_redundancy.empty:

        print(
            "No high-correlation pairs."
        )

    else:

        print(
            discovery_redundancy.to_string(
                index=False
            )
        )

    _subsection(
        "OOS"
    )

    oos_redundancy = _redundancy_table(
        oos
    )

    if oos_redundancy.empty:

        print(
            "No high-correlation pairs."
        )

    else:

        print(
            oos_redundancy.to_string(
                index=False
            )
        )

    # -------------------------------------------------------------------------
    # Candidate matrix
    # -------------------------------------------------------------------------

    _section(
        "CONFIDENCE v2.1 CANDIDATE MATRIX"
    )

    matrix = _candidate_matrix(
        feature_results
    )

    if matrix.empty:

        print(
            "No candidate results."
        )

    else:

        print(
            matrix.to_string(
                index=False
            )
        )

    # -------------------------------------------------------------------------
    # Decision rules
    # -------------------------------------------------------------------------

    _section(
        "RESEARCH DECISION RULES"
    )

    print(
        (
            "OOS_CONFIRMED      = discovery-selected bucket "
            "preserves expected 20-bar direction on OOS with "
            ">= 0.20 ATR selected-vs-rest separation."
        )
    )

    print(
        (
            "OOS_WEAK_CONFIRM   = direction survives OOS "
            "but separation is < 0.20 ATR."
        )
    )

    print(
        (
            "OOS_REVERSED       = discovery relationship "
            "reverses on OOS; do not promote."
        )
    )

    print(
        (
            "REDUNDANCY         = |Spearman rho| >= 0.70 "
            "means correlated features must not receive "
            "independent large production weights."
        )
    )

    print(
        (
            "PRODUCTION         = this validator does not "
            "authorize Confidence v2.1 production changes "
            "by itself."
        )
    )

    # -------------------------------------------------------------------------
    # Complete
    # -------------------------------------------------------------------------

    _section(
        "STATUS"
    )

    print(
        "Research validator completed successfully."
    )

    print()

    print(
        (
            "Next action: review Candidate Matrix, "
            "Confidence monotonicity, direction splits, "
            "and redundancy before writing Confidence v2.1."
        )
    )


if __name__ == "__main__":

    main()