"""
===============================================================================
Diagnostic  : scalping_setup_outcome_diagnostic.py
Project     : PulseViper XAU AI
Author      : Muhammad Adnan
Purpose     : Forward MFE / MAE analysis for temporal scalping setups
===============================================================================

This is NOT a profitability backtest.

It measures what price did AFTER each trade_ready event.

Metrics
-------
MFE ATR:
    Maximum Favorable Excursion normalized by ATR.

MAE ATR:
    Maximum Adverse Excursion normalized by ATR.

Net ATR:
    Directional close-to-close movement at the end of each horizon.

Horizons are measured in future M1 bars.

The diagnostic helps answer:

- Are READY setups followed by meaningful favorable movement?
- Does structure alignment matter?
- Does MICRO / INTERNAL / MAJOR BOS matter?
- Are long-duration setups weaker?
- Is Confidence currently ranking setup quality correctly?
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(ROOT_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


fetcher = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher


scalping_pipeline = importlib.import_module(
    "02_AI.Core.scalping_pipeline"
).scalping_pipeline


# =============================================================================
# Helpers
# =============================================================================

def _prepare_time(
    df: pd.DataFrame,
) -> pd.DataFrame:

    result = df.copy()

    if "time" in result.columns:

        result["time"] = pd.to_datetime(
            result["time"],
            errors="coerce",
        )

        return result

    if isinstance(
        result.index,
        pd.DatetimeIndex,
    ):

        result["time"] = (
            result.index
        )

        return result

    raise ValueError(
        "Dataset contains neither a time column "
        "nor a DatetimeIndex."
    )


def _to_float(
    value: Any,
    default: float = float("nan"),
) -> float:

    try:

        converted = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return default

    if not np.isfinite(
        converted
    ):

        return default

    return converted


def _safe_median(
    series: pd.Series,
) -> float:

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if numeric.empty:
        return float(
            "nan"
        )

    return float(
        numeric.median()
    )


def _safe_mean(
    series: pd.Series,
) -> float:

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if numeric.empty:
        return float(
            "nan"
        )

    return float(
        numeric.mean()
    )


def _percentage(
    condition: pd.Series,
) -> float:

    if len(
        condition
    ) == 0:

        return 0.0

    return float(
        condition.mean()
        * 100.0
    )


# =============================================================================
# Forward Excursion
# =============================================================================

def _forward_metrics(
    df: pd.DataFrame,
    position: int,
    direction: str,
    horizon: int,
) -> dict[str, float]:

    if (
        horizon <= 0
        or
        position < 0
        or
        position >= len(df)
    ):

        return {
            "mfe_atr": float("nan"),
            "mae_atr": float("nan"),
            "net_atr": float("nan"),
        }

    end_position = (
        position
        + horizon
    )

    if (
        end_position
        >= len(df)
    ):

        return {
            "mfe_atr": float("nan"),
            "mae_atr": float("nan"),
            "net_atr": float("nan"),
        }

    entry_row = df.iloc[
        position
    ]

    entry_price = _to_float(
        entry_row[
            "close"
        ]
    )

    entry_atr = _to_float(
        entry_row[
            "atr"
        ]
    )

    if (
        not np.isfinite(
            entry_price
        )
        or
        not np.isfinite(
            entry_atr
        )
        or
        entry_atr <= 0.0
    ):

        return {
            "mfe_atr": float("nan"),
            "mae_atr": float("nan"),
            "net_atr": float("nan"),
        }

    future = df.iloc[
        position + 1:
        end_position + 1
    ]

    if len(
        future
    ) != horizon:

        return {
            "mfe_atr": float("nan"),
            "mae_atr": float("nan"),
            "net_atr": float("nan"),
        }

    future_high = _to_float(
        pd.to_numeric(
            future["high"],
            errors="coerce",
        ).max()
    )

    future_low = _to_float(
        pd.to_numeric(
            future["low"],
            errors="coerce",
        ).min()
    )

    future_close = _to_float(
        future[
            "close"
        ].iloc[-1]
    )

    normalized_direction = str(
        direction
    ).upper()

    if (
        normalized_direction
        == "BULLISH"
    ):

        favorable = (
            future_high
            - entry_price
        )

        adverse = (
            entry_price
            - future_low
        )

        net_move = (
            future_close
            - entry_price
        )

    elif (
        normalized_direction
        == "BEARISH"
    ):

        favorable = (
            entry_price
            - future_low
        )

        adverse = (
            future_high
            - entry_price
        )

        net_move = (
            entry_price
            - future_close
        )

    else:

        return {
            "mfe_atr": float("nan"),
            "mae_atr": float("nan"),
            "net_atr": float("nan"),
        }

    favorable = max(
        0.0,
        favorable,
    )

    adverse = max(
        0.0,
        adverse,
    )

    return {
        "mfe_atr": (
            favorable
            / entry_atr
        ),

        "mae_atr": (
            adverse
            / entry_atr
        ),

        "net_atr": (
            net_move
            / entry_atr
        ),
    }


# =============================================================================
# Event Table
# =============================================================================

def _build_events(
    result: pd.DataFrame,
    date_text: str,
    horizons: list[int],
) -> pd.DataFrame:

    target_date = (
        pd.Timestamp(
            date_text
        )
        .date()
    )

    trade_ready = pd.to_numeric(
        result.get(
            "trade_ready",
            pd.Series(
                0,
                index=result.index,
            ),
        ),
        errors="coerce",
    ).fillna(
        0
    )

    date_mask = (
        result["time"]
        .dt.date
        == target_date
    )

    positions = np.flatnonzero(
        np.asarray(
            date_mask
            &
            (
                trade_ready
                == 1
            ),
            dtype=bool,
        )
    )

    rows: list[
        dict[str, Any]
    ] = []

    for position_value in positions:

        position = int(
            position_value
        )

        row = result.iloc[
            position
        ]

        event: dict[
            str,
            Any
        ] = {
            "position": (
                position
            ),

            "time": (
                row[
                    "time"
                ]
            ),

            "entry": _to_float(
                row[
                    "close"
                ]
            ),

            "atr": _to_float(
                row[
                    "atr"
                ]
            ),

            "setup_id": int(
                _to_float(
                    row.get(
                        "setup_id",
                        0,
                    ),
                    default=0.0,
                )
            ),

            "direction": str(
                row.get(
                    "setup_direction",
                    "NONE",
                )
            ).upper(),

            "setup_age": int(
                _to_float(
                    row.get(
                        "setup_age_bars",
                        -1,
                    ),
                    default=-1.0,
                )
            ),

            "bos_scope": str(
                row.get(
                    "setup_bos_scope",
                    "NONE",
                )
            ).upper(),

            "structure_alignment": int(
                _to_float(
                    row.get(
                        "setup_structure_alignment",
                        0,
                    ),
                    default=0.0,
                )
            ),

            "confidence": _to_float(
                row.get(
                    "confidence_score",
                    0.0,
                ),
                default=0.0,
            ),

            "confluence": int(
                _to_float(
                    row.get(
                        "confidence_confluence",
                        0,
                    ),
                    default=0.0,
                )
            ),
        }

        for horizon in horizons:

            metrics = (
                _forward_metrics(
                    df=result,
                    position=position,
                    direction=(
                        event[
                            "direction"
                        ]
                    ),
                    horizon=horizon,
                )
            )

            event[
                f"mfe_{horizon}"
            ] = round(
                metrics[
                    "mfe_atr"
                ],
                3,
            )

            event[
                f"mae_{horizon}"
            ] = round(
                metrics[
                    "mae_atr"
                ],
                3,
            )

            event[
                f"net_{horizon}"
            ] = round(
                metrics[
                    "net_atr"
                ],
                3,
            )

        rows.append(
            event
        )

    return pd.DataFrame(
        rows
    )


# =============================================================================
# Summary
# =============================================================================

def _print_horizon_summary(
    events: pd.DataFrame,
    horizon: int,
) -> None:

    mfe_column = (
        f"mfe_{horizon}"
    )

    mae_column = (
        f"mae_{horizon}"
    )

    net_column = (
        f"net_{horizon}"
    )

    valid = events[
        events[
            mfe_column
        ].notna()
        &
        events[
            mae_column
        ].notna()
        &
        events[
            net_column
        ].notna()
    ].copy()

    print()
    print(
        "-" * 79
    )
    print(
        f"FORWARD {horizon} M1 BARS"
    )
    print(
        "-" * 79
    )

    if valid.empty:

        print(
            "No complete samples."
        )

        return

    print(
        "Samples:",
        len(
            valid
        ),
    )

    print(
        "Median MFE ATR:",
        round(
            _safe_median(
                valid[
                    mfe_column
                ]
            ),
            3,
        ),
    )

    print(
        "Median MAE ATR:",
        round(
            _safe_median(
                valid[
                    mae_column
                ]
            ),
            3,
        ),
    )

    print(
        "Median NET ATR:",
        round(
            _safe_median(
                valid[
                    net_column
                ]
            ),
            3,
        ),
    )

    print(
        "Average NET ATR:",
        round(
            _safe_mean(
                valid[
                    net_column
                ]
            ),
            3,
        ),
    )

    print(
        "MFE >= 0.50 ATR:",
        f"{_percentage(valid[mfe_column] >= 0.50):.1f}%",
    )

    print(
        "MFE >= 1.00 ATR:",
        f"{_percentage(valid[mfe_column] >= 1.00):.1f}%",
    )

    print(
        "Net positive:",
        f"{_percentage(valid[net_column] > 0.0):.1f}%",
    )


def _print_group_summary(
    events: pd.DataFrame,
    horizon: int,
    group_column: str,
) -> None:

    mfe_column = (
        f"mfe_{horizon}"
    )

    mae_column = (
        f"mae_{horizon}"
    )

    net_column = (
        f"net_{horizon}"
    )

    if (
        group_column
        not in events.columns
    ):

        return

    print()
    print(
        "-" * 79
    )
    print(
        f"{horizon}-BAR RESULTS BY {group_column.upper()}"
    )
    print(
        "-" * 79
    )

    grouped = events.groupby(
        group_column,
        dropna=False,
    )

    summary_rows: list[
        dict[str, Any]
    ] = []

    for (
        group_value,
        group,
    ) in grouped:

        valid = group[
            group[
                mfe_column
            ].notna()
        ].copy()

        if valid.empty:
            continue

        summary_rows.append(
            {
                group_column: (
                    group_value
                ),

                "samples": (
                    len(
                        valid
                    )
                ),

                "median_mfe": round(
                    _safe_median(
                        valid[
                            mfe_column
                        ]
                    ),
                    3,
                ),

                "median_mae": round(
                    _safe_median(
                        valid[
                            mae_column
                        ]
                    ),
                    3,
                ),

                "median_net": round(
                    _safe_median(
                        valid[
                            net_column
                        ]
                    ),
                    3,
                ),

                "positive_pct": round(
                    _percentage(
                        valid[
                            net_column
                        ]
                        > 0.0
                    ),
                    1,
                ),
            }
        )

    summary = pd.DataFrame(
        summary_rows
    )

    if summary.empty:

        print(
            "No samples."
        )

        return

    print(
        summary.to_string(
            index=False
        )
    )


# =============================================================================
# Run
# =============================================================================

def run(
    date_text: str,
    bars: int,
    symbol: str,
    horizons: list[int],
) -> None:

    print()
    print(
        "=" * 79
    )
    print(
        "PULSEVIPER — TEMPORAL SCALPING FORWARD OUTCOME DIAGNOSTIC"
    )
    print(
        "=" * 79
    )

    print(
        "Date:",
        date_text,
    )

    print(
        "Symbol:",
        symbol,
    )

    print(
        "Horizons:",
        horizons,
    )

    raw = fetcher.fetch(
        symbol=symbol,
        bars=bars,
    )

    if raw is None:

        raise RuntimeError(
            "MT5 fetch returned None."
        )

    if len(
        raw
    ) == 0:

        raise RuntimeError(
            "MT5 fetch returned zero rows."
        )

    raw = _prepare_time(
        raw
    )

    # Run complete chronological history first.
    result = (
        scalping_pipeline
        .generate(
            raw
        )
    )

    result = (
        _prepare_time(
            result
        )
        .reset_index(
            drop=True
        )
    )

    events = _build_events(
        result=result,
        date_text=date_text,
        horizons=horizons,
    )

    print()
    print(
        "=" * 79
    )
    print(
        "TRADE READY SAMPLE"
    )
    print(
        "=" * 79
    )

    print(
        "Events:",
        len(
            events
        ),
    )

    if events.empty:

        print(
            "No trade_ready events found."
        )

        return

    display_columns = [
        "time",
        "setup_id",
        "direction",
        "setup_age",
        "bos_scope",
        "structure_alignment",
        "confidence",
    ]

    for horizon in horizons:

        display_columns.extend(
            [
                f"mfe_{horizon}",
                f"mae_{horizon}",
                f"net_{horizon}",
            ]
        )

    print()
    print(
        events[
            display_columns
        ].to_string(
            index=False
        )
    )

    print()
    print(
        "=" * 79
    )
    print(
        "FORWARD EXCURSION SUMMARY"
    )
    print(
        "=" * 79
    )

    for horizon in horizons:

        _print_horizon_summary(
            events,
            horizon,
        )

    largest_horizon = max(
        horizons
    )

    _print_group_summary(
        events,
        largest_horizon,
        "direction",
    )

    _print_group_summary(
        events,
        largest_horizon,
        "bos_scope",
    )

    _print_group_summary(
        events,
        largest_horizon,
        "structure_alignment",
    )

    print()
    print(
        "=" * 79
    )
    print(
        "INTERPRETATION"
    )
    print(
        "=" * 79
    )

    print(
        "Do not treat these numbers as PnL or a backtest."
    )

    print(
        "Use them to determine which temporal setup attributes "
        "actually separate stronger and weaker scalp opportunities."
    )

    print()


# =============================================================================
# CLI
# =============================================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Analyze forward ATR-normalized movement "
            "after temporal scalp setup triggers."
        )
    )

    parser.add_argument(
        "--date",
        default="2026-08-07",
    )

    parser.add_argument(
        "--bars",
        type=int,
        default=10000,
    )

    parser.add_argument(
        "--symbol",
        default="XAUUSDm",
    )

    parser.add_argument(
        "--horizons",
        default="5,10,20",
    )

    args = parser.parse_args()

    horizons = [
        int(
            value.strip()
        )
        for value
        in args.horizons.split(
            ","
        )
        if value.strip()
    ]

    if not horizons:

        raise ValueError(
            "At least one horizon is required."
        )

    if any(
        horizon <= 0
        for horizon in horizons
    ):

        raise ValueError(
            "All horizons must be positive."
        )

    run(
        date_text=args.date,
        bars=args.bars,
        symbol=args.symbol,
        horizons=horizons,
    )


if __name__ == "__main__":

    main()