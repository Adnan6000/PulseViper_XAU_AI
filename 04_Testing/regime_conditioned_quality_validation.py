"""
PulseViper XAU AI
Causal Regime Discovery Diagnostic

Research only:
- does not modify production pipeline
- does not change Confidence, trade_ready, risk, or execution
- uses fixed MarketRegimeEngine defaults
- computes regime metadata from raw OHLC before the trading pipeline
"""

from __future__ import annotations

import argparse
import importlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


research: Any = importlib.import_module(
    "04_Testing.confidence_v21_research_validation"
)

regime_module: Any = importlib.import_module(
    "02_AI.Core.market_regime"
)


fetcher: Any = research.fetcher
scalping_pipeline: Any = research.scalping_pipeline
market_regime: Any = regime_module.market_regime

_complete_dates: Any = research._complete_dates
_build_event_frame: Any = research._build_event_frame
_summary: Any = research._summary
_to_numeric: Any = research._to_numeric
_as_float: Any = research._as_float
_fmt: Any = research._fmt
_confidence_table: Any = research._confidence_table
_confidence_monotonicity: Any = research._confidence_monotonicity


REGIME_COLUMNS = (
    "regime_ready",
    "regime_atr",
    "regime_atr_percentile",
    "regime_range_atr",
    "regime_efficiency",
    "regime_directional_move_atr",
    "regime_volatility",
    "regime_trend",
    "regime_state",
    "regime_trend_strength",
    "regime_time_bucket_utc",
    "regime_version",
)


def _section(
    title: str,
) -> None:

    print()

    print(
        "=" * 116
    )

    print(
        title
    )

    print(
        "=" * 116
    )


def _safe_direction(
    frame: pd.DataFrame,
) -> pd.Series:

    if "direction" not in frame.columns:

        return pd.Series(
            "",
            index=frame.index,
            dtype="object",
        )

    return pd.Series(
        [
            str(value).upper()
            for value in frame[
                "direction"
            ].tolist()
        ],
        index=frame.index,
        dtype="object",
    )


def _spearman_confidence_net20(
    frame: pd.DataFrame,
) -> float:

    if (
        frame.empty
        or "confidence_score" not in frame.columns
        or "net_20" not in frame.columns
    ):

        return np.nan

    values = pd.DataFrame(
        {
            "confidence": _to_numeric(
                frame[
                    "confidence_score"
                ]
            ),

            "net20": _to_numeric(
                frame[
                    "net_20"
                ]
            ),
        }
    ).dropna()

    if len(values) < 5:

        return np.nan

    matrix = values.corr(
        method="spearman"
    ).to_numpy(
        dtype=np.float64
    )

    if matrix.shape != (
        2,
        2,
    ):

        return np.nan

    rho = float(
        matrix[
            0,
            1,
        ]
    )

    if not np.isfinite(
        rho
    ):

        return np.nan

    return rho


def _series_mean(
    frame: pd.DataFrame,
    column: str,
) -> float:

    if (
        frame.empty
        or column not in frame.columns
    ):

        return np.nan

    values = _to_numeric(
        frame[
            column
        ]
    ).dropna()

    if values.empty:

        return np.nan

    return float(
        values.mean()
    )


def _series_median(
    frame: pd.DataFrame,
    column: str,
) -> float:

    if (
        frame.empty
        or column not in frame.columns
    ):

        return np.nan

    values = _to_numeric(
        frame[
            column
        ]
    ).dropna()

    if values.empty:

        return np.nan

    return float(
        values.median()
    )


def _stats_row(
    label: str,
    frame: pd.DataFrame,
    total_n: int,
) -> dict[
    str,
    Any,
]:

    stats = _summary(
        frame
    )

    coverage = (
        len(frame)
        /
        total_n
        *
        100.0
        if total_n > 0
        else np.nan
    )

    return {

        "group": (
            label
        ),

        "n": (
            len(
                frame
            )
        ),

        "coverage_pct": round(
            coverage,
            1,
        ),

        "net5_med": round(
            _as_float(
                stats.get(
                    "net5_median",
                    np.nan,
                )
            ),
            3,
        ),

        "net10_med": round(
            _as_float(
                stats.get(
                    "net10_median",
                    np.nan,
                )
            ),
            3,
        ),

        "net20_med": round(
            _as_float(
                stats.get(
                    "net20_median",
                    np.nan,
                )
            ),
            3,
        ),

        "net20_avg": round(
            _series_mean(
                frame,
                "net_20",
            ),
            3,
        ),

        "pos20_pct": round(
            _as_float(
                stats.get(
                    "positive20_pct",
                    np.nan,
                )
            ),
            1,
        ),

        "mfe20_med": round(
            _series_median(
                frame,
                "mfe_20",
            ),
            3,
        ),

        "mae20_med": round(
            _series_median(
                frame,
                "mae_20",
            ),
            3,
        ),

        "1R_first_pct": round(
            _as_float(
                stats.get(
                    "target_1_to_1_pct",
                    np.nan,
                )
            ),
            1,
        ),
    }


def _labels(
    frame: pd.DataFrame,
    column: str,
) -> list[str]:

    if column not in frame.columns:

        return []

    return sorted(
        {
            str(value)

            for value

            in frame[
                column
            ].dropna().tolist()

            if str(value)
            not in (
                "",
                "UNKNOWN",
                "nan",
            )
        }
    )


def _group_table(
    frame: pd.DataFrame,
    column: str,
    min_events: int,
) -> pd.DataFrame:

    if (
        frame.empty
        or column not in frame.columns
    ):

        return pd.DataFrame()

    total_n = len(
        frame
    )

    rows: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for label in _labels(
        frame,
        column,
    ):

        subset = frame.loc[
            frame[
                column
            ].astype(
                str
            )
            ==
            label
        ]

        if len(
            subset
        ) < min_events:

            continue

        rows.append(
            _stats_row(
                label,
                subset,
                total_n,
            )
        )

    return pd.DataFrame(
        rows
    )


def _direction_regime_table(
    events: pd.DataFrame,
    min_events: int,
) -> pd.DataFrame:

    if (
        events.empty
        or "regime_state" not in events.columns
    ):

        return pd.DataFrame()

    directions = _safe_direction(
        events
    )

    rows: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for direction in (
        "BULLISH",
        "BEARISH",
    ):

        side = events.loc[
            directions
            ==
            direction
        ]

        total_n = len(
            side
        )

        for label in _labels(
            side,
            "regime_state",
        ):

            subset = side.loc[
                side[
                    "regime_state"
                ].astype(
                    str
                )
                ==
                label
            ]

            if len(
                subset
            ) < min_events:

                continue

            row = _stats_row(
                label,
                subset,
                total_n,
            )

            row[
                "direction"
            ] = direction

            rows.append(
                row
            )

    if not rows:

        return pd.DataFrame()

    table = pd.DataFrame(
        rows
    )

    columns = [
        "direction",
        "group",
        "n",
        "coverage_pct",
        "net5_med",
        "net10_med",
        "net20_med",
        "net20_avg",
        "pos20_pct",
        "mfe20_med",
        "mae20_med",
        "1R_first_pct",
    ]

    return table[
        columns
    ]


def _alignment_label(
    frame: pd.DataFrame,
) -> pd.Series:

    directions = _safe_direction(
        frame
    )

    if (
        "regime_trend"
        not in frame.columns
    ):

        return pd.Series(
            "UNKNOWN",
            index=frame.index,
            dtype="object",
        )

    trends = pd.Series(
        [
            str(value).upper()

            for value

            in frame[
                "regime_trend"
            ].tolist()
        ],
        index=frame.index,
        dtype="object",
    )

    labels: list[
        str
    ] = []

    for (
        direction,
        trend,
    ) in zip(
        directions.tolist(),
        trends.tolist(),
    ):

        if direction not in (
            "BULLISH",
            "BEARISH",
        ):

            labels.append(
                "UNKNOWN"
            )

        elif trend == "RANGE":

            labels.append(
                "RANGE"
            )

        elif trend == direction:

            labels.append(
                "ALIGNED"
            )

        elif trend in (
            "BULLISH",
            "BEARISH",
        ):

            labels.append(
                "OPPOSED"
            )

        else:

            labels.append(
                "UNKNOWN"
            )

    return pd.Series(
        labels,
        index=frame.index,
        dtype="object",
    )


def _confidence_by_regime(
    events: pd.DataFrame,
    min_events: int,
) -> pd.DataFrame:

    if (
        events.empty
        or "regime_state" not in events.columns
    ):

        return pd.DataFrame()

    rows: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for label in _labels(
        events,
        "regime_state",
    ):

        subset = events.loc[
            events[
                "regime_state"
            ].astype(
                str
            )
            ==
            label
        ]

        if len(
            subset
        ) < min_events:

            continue

        confidence_table = (
            _confidence_table(
                subset
            )
        )

        rows.append(
            {

                "regime_state": (
                    label
                ),

                "n": (
                    len(
                        subset
                    )
                ),

                "conf_net20_rho": round(
                    _spearman_confidence_net20(
                        subset
                    ),
                    3,
                ),

                "monotonicity": (
                    _confidence_monotonicity(
                        confidence_table
                    )
                ),
            }
        )

    return pd.DataFrame(
        rows
    )


def _date_stability(
    events: pd.DataFrame,
    min_events_per_date: int,
    min_dates: int,
) -> pd.DataFrame:

    required = {
        "date_label",
        "regime_state",
        "net_20",
    }

    if (
        events.empty
        or not required.issubset(
            events.columns
        )
    ):

        return pd.DataFrame()

    rows: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for state in _labels(
        events,
        "regime_state",
    ):

        state_events = events.loc[
            events[
                "regime_state"
            ].astype(
                str
            )
            ==
            state
        ]

        daily_values: list[
            float
        ] = []

        for (
            _,
            daily,
        ) in state_events.groupby(
            "date_label"
        ):

            if len(
                daily
            ) < min_events_per_date:

                continue

            values = _to_numeric(
                daily[
                    "net_20"
                ]
            ).dropna()

            if values.empty:

                continue

            daily_values.append(
                float(
                    values.median()
                )
            )

        if len(
            daily_values
        ) < min_dates:

            continue

        positive_dates = sum(
            value > 0.0
            for value
            in daily_values
        )

        rows.append(
            {

                "regime_state": (
                    state
                ),

                "events": (
                    len(
                        state_events
                    )
                ),

                "eligible_dates": (
                    len(
                        daily_values
                    )
                ),

                "positive_dates": (
                    positive_dates
                ),

                "positive_date_pct": round(
                    (
                        positive_dates
                        /
                        len(
                            daily_values
                        )
                        *
                        100.0
                    ),
                    1,
                ),

                "median_daily_net20": round(
                    float(
                        np.median(
                            daily_values
                        )
                    ),
                    3,
                ),

                "worst_daily_net20": round(
                    float(
                        np.min(
                            daily_values
                        )
                    ),
                    3,
                ),

                "best_daily_net20": round(
                    float(
                        np.max(
                            daily_values
                        )
                    ),
                    3,
                ),
            }
        )

    return pd.DataFrame(
        rows
    )


def _candidate_matrix(
    events: pd.DataFrame,
    min_events: int,
    min_direction_events: int,
) -> pd.DataFrame:

    if (
        events.empty
        or "regime_state" not in events.columns
    ):

        return pd.DataFrame()

    baseline_stats = _summary(
        events
    )

    baseline_net20 = _as_float(
        baseline_stats.get(
            "net20_median",
            np.nan,
        )
    )

    directions = _safe_direction(
        events
    )

    rows: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for state in _labels(
        events,
        "regime_state",
    ):

        selected = events.loc[
            events[
                "regime_state"
            ].astype(
                str
            )
            ==
            state
        ]

        if len(
            selected
        ) < min_events:

            continue

        selected_stats = _summary(
            selected
        )

        selected_net20 = _as_float(
            selected_stats.get(
                "net20_median",
                np.nan,
            )
        )

        if (
            np.isfinite(
                selected_net20
            )
            and
            np.isfinite(
                baseline_net20
            )
        ):

            spread_vs_all = (
                selected_net20
                -
                baseline_net20
            )

        else:

            spread_vs_all = (
                np.nan
            )

        selected_directions = (
            directions.loc[
                selected.index
            ]
        )

        bull = selected.loc[
            selected_directions
            ==
            "BULLISH"
        ]

        bear = selected.loc[
            selected_directions
            ==
            "BEARISH"
        ]

        bull_stats = _summary(
            bull
        )

        bear_stats = _summary(
            bear
        )

        if len(
            bull
        ) >= min_direction_events:

            bull_net20 = _as_float(
                bull_stats.get(
                    "net20_median",
                    np.nan,
                )
            )

        else:

            bull_net20 = (
                np.nan
            )

        if len(
            bear
        ) >= min_direction_events:

            bear_net20 = _as_float(
                bear_stats.get(
                    "net20_median",
                    np.nan,
                )
            )

        else:

            bear_net20 = (
                np.nan
            )

        rows.append(
            {

                "regime_state": (
                    state
                ),

                "n": (
                    len(
                        selected
                    )
                ),

                "net20_med": round(
                    selected_net20,
                    3,
                ),

                "spread_vs_all": round(
                    spread_vs_all,
                    3,
                ),

                "pos20_pct": round(
                    _as_float(
                        selected_stats.get(
                            "positive20_pct",
                            np.nan,
                        )
                    ),
                    1,
                ),

                "bull_n": (
                    len(
                        bull
                    )
                ),

                "bull_net20": round(
                    bull_net20,
                    3,
                ),

                "bear_n": (
                    len(
                        bear
                    )
                ),

                "bear_net20": round(
                    bear_net20,
                    3,
                ),
            }
        )

    if not rows:

        return pd.DataFrame()

    return (
        pd.DataFrame(
            rows
        )
        .sort_values(
            [
                "spread_vs_all",
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


def _attach_regime(
    raw: pd.DataFrame,
    enriched: pd.DataFrame,
) -> pd.DataFrame:

    # Regime is calculated from raw OHLC independently.
    # Trading-pipeline outputs cannot contaminate classification.

    regime_frame = (
        market_regime.generate(
            raw
        )
    )

    if len(
        regime_frame
    ) != len(
        enriched
    ):

        raise RuntimeError(
            "Regime/pipeline row-count mismatch."
        )

    if (
        "time" in regime_frame.columns
        and
        "time" in enriched.columns
    ):

        regime_time = pd.to_datetime(
            regime_frame[
                "time"
            ],
            errors="coerce",
        ).reset_index(
            drop=True
        )

        pipeline_time = pd.to_datetime(
            enriched[
                "time"
            ],
            errors="coerce",
        ).reset_index(
            drop=True
        )

        if not regime_time.equals(
            pipeline_time
        ):

            raise RuntimeError(
                "Regime/pipeline time alignment mismatch."
            )

    missing = [
        column

        for column

        in REGIME_COLUMNS

        if column
        not in regime_frame.columns
    ]

    if missing:

        raise RuntimeError(
            (
                "MarketRegimeEngine missing outputs: "
                +
                ", ".join(
                    missing
                )
            )
        )

    result = enriched.copy()

    for column in REGIME_COLUMNS:

        result[
            column
        ] = regime_frame[
            column
        ].to_numpy(
            copy=True
        )

    return result


def _ensure_event_regime(
    events: pd.DataFrame,
    enriched: pd.DataFrame,
) -> pd.DataFrame:
    """
    Ensure regime metadata exists on event rows.

    If _build_event_frame ever stops preserving arbitrary metadata,
    each trade-ready event's causal source-row position is used.
    """

    if events.empty:

        return events.copy()

    result = events.copy()

    missing = [
        column

        for column

        in REGIME_COLUMNS

        if column
        not in result.columns
    ]

    if not missing:

        return result

    if (
        "position"
        not in result.columns
    ):

        raise RuntimeError(
            (
                "Event frame is missing regime metadata "
                "and has no position column for recovery."
            )
        )

    positions = _to_numeric(
        result[
            "position"
        ]
    )

    if positions.isna().any():

        raise RuntimeError(
            "Event frame contains invalid positions."
        )

    integer_positions = positions.astype(
        "int64"
    )

    if (
        (
            integer_positions
            < 0
        ).any()
        or
        (
            integer_positions
            >= len(
                enriched
            )
        ).any()
    ):

        raise RuntimeError(
            (
                "Event position is outside "
                "enriched pipeline bounds."
            )
        )

    source = enriched.iloc[
        integer_positions.to_numpy(
            dtype=np.int64
        )
    ]

    for column in missing:

        result[
            column
        ] = source[
            column
        ].to_numpy(
            copy=True
        )

    return result


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "PulseViper causal market-regime "
            "discovery diagnostic"
        )
    )

    parser.add_argument(
        "--bars",
        type=int,
        default=90000,
    )

    parser.add_argument(
        "--symbol",
        type=str,
        default="XAUUSDm",
    )

    parser.add_argument(
        "--cutoff-date",
        type=str,
        default="2026-06-29",
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--min-events",
        type=int,
        default=15,
    )

    parser.add_argument(
        "--min-direction-events",
        type=int,
        default=8,
    )

    parser.add_argument(
        "--min-events-per-date",
        type=int,
        default=2,
    )

    parser.add_argument(
        "--min-dates",
        type=int,
        default=5,
    )

    args = parser.parse_args()

    if args.bars <= 0:

        raise ValueError(
            "--bars must be > 0"
        )

    if args.days <= 0:

        raise ValueError(
            "--days must be > 0"
        )

    try:

        cutoff = datetime.strptime(
            args.cutoff_date,
            "%Y-%m-%d",
        )

    except ValueError as exc:

        raise ValueError(
            "--cutoff-date must use YYYY-MM-DD"
        ) from exc

    cutoff_label = cutoff.strftime(
        "%Y-%m-%d"
    )

    # =========================================================================
    # Header
    # =========================================================================

    _section(
        "PulseViper Causal Regime Discovery Diagnostic"
    )

    print(
        f"Project root      : "
        f"{PROJECT_ROOT}"
    )

    print(
        f"Requested symbol  : "
        f"{args.symbol}"
    )

    print(
        f"Requested bars    : "
        f"{args.bars}"
    )

    print(
        f"Strict cutoff     : "
        f"dates < {cutoff_label}"
    )

    print(
        f"Discovery days    : "
        f"{args.days}"
    )

    print(
        "Regime tuning     : DISABLED"
    )

    print(
        "Production impact : NONE"
    )

    # =========================================================================
    # Fetch
    # =========================================================================

    print()

    print(
        "Fetching MT5 history..."
    )

    raw: pd.DataFrame = (
        fetcher.fetch(
            symbol=args.symbol,
            bars=args.bars,
        )
    )

    if raw.empty:

        raise RuntimeError(
            "MT5 returned no usable bars."
        )

    print(
        f"Fetched bars      : "
        f"{len(raw)}"
    )

    resolved = str(
        getattr(
            fetcher,
            "last_resolved_symbol",
            "",
        )
    )

    if resolved:

        print(
            f"Resolved symbol   : "
            f"{resolved}"
        )

    # =========================================================================
    # Pipeline + independent regime
    # =========================================================================

    print()

    print(
        "Running canonical trading pipeline..."
    )

    enriched: pd.DataFrame = (
        scalping_pipeline.generate(
            raw
        )
    )

    print(
        "Calculating independent causal regime metadata..."
    )

    enriched = _attach_regime(
        raw=raw,
        enriched=enriched,
    )

    # =========================================================================
    # Date universe
    # =========================================================================

    complete_dates: list[
        str
    ] = _complete_dates(
        enriched
    )

    eligible_dates = [

        date_label

        for date_label

        in complete_dates

        if (
            date_label
            < cutoff_label
        )
    ]

    if len(
        eligible_dates
    ) < args.days:

        raise RuntimeError(
            (
                f"Need at least {args.days} complete dates "
                f"before {cutoff_label}; "
                f"found {len(eligible_dates)}. "
                "Increase --bars or reduce --days."
            )
        )

    selected_dates = (
        eligible_dates[
            -args.days:
        ]
    )

    if (
        "time"
        not in enriched.columns
    ):

        raise RuntimeError(
            "Pipeline output is missing time."
        )

    enriched = enriched.copy()

    enriched[
        "date_label"
    ] = (
        pd.to_datetime(
            enriched[
                "time"
            ],
            errors="coerce",
        )
        .dt
        .strftime(
            "%Y-%m-%d"
        )
    )

    discovery_bars = enriched.loc[
        enriched[
            "date_label"
        ].isin(
            selected_dates
        )
    ].copy()

    # =========================================================================
    # Events
    # =========================================================================

    events: pd.DataFrame = (
        _build_event_frame(
            enriched
        )
    )

    events = _ensure_event_regime(
        events=events,
        enriched=enriched,
    )

    discovery_events = events.loc[
        events[
            "date_label"
        ].isin(
            selected_dates
        )
    ].copy()

    if discovery_events.empty:

        raise RuntimeError(
            (
                "No trade_ready events in "
                "selected discovery dates."
            )
        )

    # =========================================================================
    # Universe output
    # =========================================================================

    _section(
        "DISCOVERY UNIVERSE"
    )

    print(
        f"Start date         : "
        f"{selected_dates[0]}"
    )

    print(
        f"End date           : "
        f"{selected_dates[-1]}"
    )

    print(
        f"Complete days      : "
        f"{len(selected_dates)}"
    )

    print(
        f"Bars               : "
        f"{len(discovery_bars)}"
    )

    print(
        f"Trade-ready events : "
        f"{len(discovery_events)}"
    )

    ready_bars = discovery_bars.loc[
        _to_numeric(
            discovery_bars[
                "regime_ready"
            ]
        )
        ==
        1.0
    ]

    ready_pct = (

        len(
            ready_bars
        )
        /
        len(
            discovery_bars
        )
        *
        100.0

        if len(
            discovery_bars
        ) > 0

        else np.nan
    )

    print(
        (
            f"Regime-ready bars  : "
            f"{len(ready_bars)} "
            f"({_fmt(ready_pct, 1)}%)"
        )
    )

    # =========================================================================
    # Bar distribution
    # =========================================================================

    _section(
        "BAR-LEVEL REGIME DISTRIBUTION"
    )

    if ready_bars.empty:

        print(
            "No regime-ready bars."
        )

    else:

        bar_distribution = (
            ready_bars[
                "regime_state"
            ]
            .astype(
                str
            )
            .value_counts(
                dropna=False
            )
            .rename_axis(
                "regime_state"
            )
            .reset_index(
                name="bars"
            )
        )

        bar_distribution[
            "pct"
        ] = (
            bar_distribution[
                "bars"
            ]
            /
            len(
                ready_bars
            )
            *
            100.0
        ).round(
            1
        )

        print(
            bar_distribution.to_string(
                index=False
            )
        )

    # =========================================================================
    # Baseline
    # =========================================================================

    _section(
        "TRADE-READY BASELINE"
    )

    baseline = pd.DataFrame(
        [
            _stats_row(
                label="ALL_READY",
                frame=discovery_events,
                total_n=len(
                    discovery_events
                ),
            )
        ]
    )

    print(
        baseline.to_string(
            index=False
        )
    )

    # =========================================================================
    # Main regime groups
    # =========================================================================

    grouped_sections = (

        (
            "READY OUTCOMES BY VOLATILITY REGIME",
            "regime_volatility",
        ),

        (
            "READY OUTCOMES BY TREND REGIME",
            "regime_trend",
        ),

        (
            "READY OUTCOMES BY COMBINED REGIME",
            "regime_state",
        ),

        (
            "READY OUTCOMES BY UTC TIME BUCKET",
            "regime_time_bucket_utc",
        ),
    )

    for (
        title,
        column,
    ) in grouped_sections:

        _section(
            title
        )

        table = _group_table(
            frame=discovery_events,
            column=column,
            min_events=args.min_events,
        )

        if table.empty:

            print(
                "No groups meet minimum event count."
            )

        else:

            print(
                table.to_string(
                    index=False
                )
            )

    # =========================================================================
    # Direction interaction
    # =========================================================================

    _section(
        "DIRECTION × COMBINED REGIME"
    )

    direction_table = (
        _direction_regime_table(
            events=discovery_events,
            min_events=(
                args.min_direction_events
            ),
        )
    )

    if direction_table.empty:

        print(
            (
                "No direction/regime groups "
                "meet minimum event count."
            )
        )

    else:

        print(
            direction_table.to_string(
                index=False
            )
        )

    # =========================================================================
    # Alignment
    # =========================================================================

    _section(
        "SETUP DIRECTION × REGIME TREND ALIGNMENT"
    )

    aligned_events = (
        discovery_events.copy()
    )

    aligned_events[
        "regime_alignment"
    ] = _alignment_label(
        aligned_events
    )

    alignment_table = (
        _group_table(
            frame=aligned_events,
            column="regime_alignment",
            min_events=args.min_events,
        )
    )

    if alignment_table.empty:

        print(
            (
                "No alignment groups meet "
                "minimum event count."
            )
        )

    else:

        print(
            alignment_table.to_string(
                index=False
            )
        )

    # =========================================================================
    # Current Confidence within regime
    # =========================================================================

    _section(
        "CURRENT CONFIDENCE v2 INSIDE REGIMES"
    )

    confidence_regime = (
        _confidence_by_regime(
            events=discovery_events,
            min_events=args.min_events,
        )
    )

    if confidence_regime.empty:

        print(
            "No regimes meet minimum event count."
        )

    else:

        print(
            confidence_regime.to_string(
                index=False
            )
        )

    # =========================================================================
    # Date stability
    # =========================================================================

    _section(
        "COMBINED REGIME DATE STABILITY"
    )

    stability = _date_stability(
        events=discovery_events,
        min_events_per_date=(
            args.min_events_per_date
        ),
        min_dates=args.min_dates,
    )

    if stability.empty:

        print(
            (
                "No regimes meet "
                "date-stability requirements."
            )
        )

    else:

        print(
            stability.to_string(
                index=False
            )
        )

    # =========================================================================
    # Candidate matrix
    # =========================================================================

    _section(
        "DISCOVERY-ONLY REGIME CANDIDATE MATRIX"
    )

    candidates = _candidate_matrix(
        events=discovery_events,
        min_events=args.min_events,
        min_direction_events=(
            args.min_direction_events
        ),
    )

    if candidates.empty:

        print(
            "No regimes meet minimum event count."
        )

    else:

        print(
            candidates.to_string(
                index=False
            )
        )

    print()

    print(
        "IMPORTANT:"
    )

    print(
        "- This matrix is discovery only."
    )

    print(
        (
            "- Do not change Confidence, "
            "trade_ready, or risk from this output."
        )
    )

    print(
        (
            "- Any attractive regime relationship must be "
            "frozen and validated on an older "
            "non-overlapping historical window."
        )
    )

    # =========================================================================
    # Complete
    # =========================================================================

    _section(
        "STATUS"
    )

    print(
        (
            "Causal regime discovery diagnostic "
            "completed successfully."
        )
    )


if __name__ == "__main__":

    main()