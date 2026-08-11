"""
===============================================================================
Module      : market_structure_diagnostic.py
Project     : PulseViper XAU AI
Author      : Muhammad Adnan
Purpose     : Real XAUUSD Market Structure Calibration Diagnostic
===============================================================================

This script does NOT modify production logic.

It measures the current MarketStructure engine against real MT5 XAUUSD data
across multiple timeframes so pivot-strength thresholds and double-pivot
policy can be calibrated from actual Gold behaviour rather than guesswork.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Iterable

import MetaTrader5 as mt5
import numpy as np
import pandas as pd


# =============================================================================
# Project Root
# =============================================================================

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# =============================================================================
# Project Imports
# =============================================================================

market_structure_module = importlib.import_module(
    "02_AI.Core.market_structure"
)

data_fetcher_module = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
)

MarketStructure = market_structure_module.MarketStructure
fetcher = data_fetcher_module.fetcher


# =============================================================================
# MT5 Timeframes
# =============================================================================

TIMEFRAMES = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}


# =============================================================================
# Helpers
# =============================================================================

def _finite_series(
    series: pd.Series,
    positive_only: bool = False,
) -> pd.Series:

    values = pd.to_numeric(
        series,
        errors="coerce",
    ).astype("float64")

    values = values[
        np.isfinite(values)
    ]

    if positive_only:
        values = values[
            values > 0
        ]

    return values


def _stats(
    series: pd.Series,
) -> dict[str, float]:

    values = _finite_series(
        series,
    )

    if values.empty:
        return {
            "min": np.nan,
            "mean": np.nan,
            "median": np.nan,
            "p75": np.nan,
            "p90": np.nan,
            "p95": np.nan,
            "p99": np.nan,
            "max": np.nan,
        }

    return {
        "min": float(values.min()),
        "mean": float(values.mean()),
        "median": float(values.median()),
        "p75": float(values.quantile(0.75)),
        "p90": float(values.quantile(0.90)),
        "p95": float(values.quantile(0.95)),
        "p99": float(values.quantile(0.99)),
        "max": float(values.max()),
    }


def _spacing_stats(
    indices: Iterable[int],
) -> dict[str, float]:

    values = np.asarray(
        list(indices),
        dtype=np.int64,
    )

    if len(values) < 2:
        return {
            "mean": np.nan,
            "median": np.nan,
            "p90": np.nan,
            "max": np.nan,
        }

    spacing = np.diff(
        values
    ).astype(np.float64)

    return {
        "mean": float(np.mean(spacing)),
        "median": float(np.median(spacing)),
        "p90": float(
            np.quantile(
                spacing,
                0.90,
            )
        ),
        "max": float(np.max(spacing)),
    }


def _percent(
    numerator: int,
    denominator: int,
) -> float:

    if denominator <= 0:
        return 0.0

    return (
        float(numerator)
        / float(denominator)
        * 100.0
    )


# =============================================================================
# Directional Pivot Strength
# =============================================================================

def calculate_directional_pivot_strengths(
    data: pd.DataFrame,
    engine: MarketStructure,
) -> pd.DataFrame:
    """
    Recalculate HIGH and LOW pivot strengths separately.

    Production MarketStructure stores a single pivot_strength.
    On a double-pivot candle that value is the maximum of the
    HIGH and LOW strength.

    This diagnostic keeps the two values separate so the eventual
    double-pivot representation policy can be evidence-based.
    """

    df = data.copy()

    df["pivot_high_strength_diag"] = np.nan
    df["pivot_low_strength_diag"] = np.nan

    window = engine.pivot_window

    if len(df) <= window * 2:
        return df

    high = np.asarray(
        pd.to_numeric(
            df["high"],
            errors="coerce",
        ),
        dtype=np.float64,
    )

    low = np.asarray(
        pd.to_numeric(
            df["low"],
            errors="coerce",
        ),
        dtype=np.float64,
    )

    atr = np.asarray(
        pd.to_numeric(
            df["atr"],
            errors="coerce",
        ),
        dtype=np.float64,
    )

    high_strength = np.full(
        len(df),
        np.nan,
        dtype=np.float64,
    )

    low_strength = np.full(
        len(df),
        np.nan,
        dtype=np.float64,
    )

    for i in range(
        window,
        len(df) - window,
    ):

        atr_value = atr[i]

        if (
            not np.isfinite(atr_value)
            or atr_value <= 0
        ):
            continue

        current_high = high[i]
        current_low = low[i]

        if (
            not np.isfinite(current_high)
            or not np.isfinite(current_low)
        ):
            continue

        left_high = np.max(
            high[
                i - window:i
            ]
        )

        right_high = np.max(
            high[
                i + 1:i + window + 1
            ]
        )

        left_low = np.min(
            low[
                i - window:i
            ]
        )

        right_low = np.min(
            low[
                i + 1:i + window + 1
            ]
        )

        if df.iloc[i]["pivot_high"] == 1:

            value = (
                current_high
                - max(
                    left_high,
                    right_high,
                )
            ) / atr_value

            if np.isfinite(value):
                high_strength[i] = max(
                    0.0,
                    float(value),
                )

        if df.iloc[i]["pivot_low"] == 1:

            value = (
                min(
                    left_low,
                    right_low,
                )
                - current_low
            ) / atr_value

            if np.isfinite(value):
                low_strength[i] = max(
                    0.0,
                    float(value),
                )

    df["pivot_high_strength_diag"] = (
        high_strength
    )

    df["pivot_low_strength_diag"] = (
        low_strength
    )

    return df


# =============================================================================
# Timeframe Analysis
# =============================================================================

def analyze_timeframe(
    symbol: str,
    timeframe_name: str,
    bars: int,
    pivot_window: int,
    min_strength: float,
    major_strength: float,
) -> dict:

    timeframe = TIMEFRAMES[
        timeframe_name
    ]

    engine = MarketStructure(
        pivot_window=pivot_window,
        min_strength=min_strength,
        major_strength=major_strength,
    )

    raw = fetcher.fetch(
        symbol=symbol,
        timeframe=timeframe,
        bars=bars,
    )

    if raw is None or raw.empty:
        raise RuntimeError(
            f"No data returned for "
            f"{symbol} {timeframe_name}"
        )

    result = engine.generate(
        raw
    )

    result = (
        calculate_directional_pivot_strengths(
            result,
            engine,
        )
    )

    # -------------------------------------------------------------------------
    # Pivot masks
    # -------------------------------------------------------------------------

    pivot_high_mask = (
        result["pivot_high"] == 1
    )

    pivot_low_mask = (
        result["pivot_low"] == 1
    )

    pivot_mask = (
        pivot_high_mask
        | pivot_low_mask
    )

    double_mask = (
        pivot_high_mask
        & pivot_low_mask
    )

    # -------------------------------------------------------------------------
    # Structural swing masks
    # -------------------------------------------------------------------------

    valid_swing_mask = (
        result["swing_id"] > 0
    )

    minor_mask = (
        (result["minor_high"] == 1)
        |
        (result["minor_low"] == 1)
    )

    major_mask = (
        (result["major_high"] == 1)
        |
        (result["major_low"] == 1)
    )

    # -------------------------------------------------------------------------
    # Strength
    # -------------------------------------------------------------------------

    pivot_strength = _finite_series(
        result.loc[
            pivot_mask,
            "pivot_strength",
        ]
    )

    positive_strength = pivot_strength[
        pivot_strength > 0
    ]

    weak_count = int(
        (
            positive_strength
            < min_strength
        ).sum()
    )

    minor_strength_count = int(
        (
            (
                positive_strength
                >= min_strength
            )
            &
            (
                positive_strength
                < major_strength
            )
        ).sum()
    )

    major_strength_count = int(
        (
            positive_strength
            >= major_strength
        ).sum()
    )

    zero_strength_count = int(
        (
            pivot_strength
            <= 0
        ).sum()
    )

    # -------------------------------------------------------------------------
    # Double Pivot Dominance
    # -------------------------------------------------------------------------

    doubles = result.loc[
        double_mask,
        [
            "pivot_high_strength_diag",
            "pivot_low_strength_diag",
        ],
    ].copy()

    double_high_dominant = 0
    double_low_dominant = 0
    double_ties = 0

    if not doubles.empty:

        high_values = (
            doubles[
                "pivot_high_strength_diag"
            ]
            .fillna(0.0)
            .to_numpy(
                dtype=np.float64
            )
        )

        low_values = (
            doubles[
                "pivot_low_strength_diag"
            ]
            .fillna(0.0)
            .to_numpy(
                dtype=np.float64
            )
        )

        tolerance = 1e-12

        double_high_dominant = int(
            (
                high_values
                >
                low_values + tolerance
            ).sum()
        )

        double_low_dominant = int(
            (
                low_values
                >
                high_values + tolerance
            ).sum()
        )

        double_ties = int(
            np.isclose(
                high_values,
                low_values,
                rtol=0.0,
                atol=tolerance,
            ).sum()
        )

    # -------------------------------------------------------------------------
    # Structure Events
    # -------------------------------------------------------------------------

    hh = int(result["HH"].sum())
    hl = int(result["HL"].sum())
    lh = int(result["LH"].sum())
    ll = int(result["LL"].sum())

    bullish_bias = int(
        (
            result[
                "structure_bias"
            ]
            == "BULLISH"
        ).sum()
    )

    bearish_bias = int(
        (
            result[
                "structure_bias"
            ]
            == "BEARISH"
        ).sum()
    )

    neutral_bias = int(
        (
            result[
                "structure_bias"
            ]
            == "NEUTRAL"
        ).sum()
    )

    # -------------------------------------------------------------------------
    # Swing Type Continuity
    # -------------------------------------------------------------------------

    swing_types = (
        result.loc[
            valid_swing_mask,
            "swing_type",
        ]
        .astype(str)
        .tolist()
    )

    repeated_swing_type = 0

    if len(swing_types) >= 2:

        repeated_swing_type = sum(
            1
            for previous, current
            in zip(
                swing_types[:-1],
                swing_types[1:],
            )
            if previous == current
        )

    # -------------------------------------------------------------------------
    # Spacing
    # -------------------------------------------------------------------------

    pivot_spacing = _spacing_stats(
        np.flatnonzero(
            pivot_mask.to_numpy()
        )
    )

    swing_spacing = _spacing_stats(
        np.flatnonzero(
            valid_swing_mask.to_numpy()
        )
    )

    major_spacing = _spacing_stats(
        np.flatnonzero(
            major_mask.to_numpy()
        )
    )

    # -------------------------------------------------------------------------
    # Threshold Sensitivity
    # -------------------------------------------------------------------------

    threshold_levels = [
        0.50,
        0.75,
        1.00,
        1.20,
        1.50,
        2.00,
        2.50,
        3.00,
        4.00,
    ]

    threshold_sensitivity = {}

    positive_count = len(
        positive_strength
    )

    for threshold in threshold_levels:

        count = int(
            (
                positive_strength
                >= threshold
            ).sum()
        )

        threshold_sensitivity[
            threshold
        ] = {
            "count": count,
            "percent": _percent(
                count,
                positive_count,
            ),
        }

    # -------------------------------------------------------------------------
    # Directional statistics
    # -------------------------------------------------------------------------

    high_strength_stats = _stats(
        result.loc[
            pivot_high_mask,
            "pivot_high_strength_diag",
        ]
    )

    low_strength_stats = _stats(
        result.loc[
            pivot_low_mask,
            "pivot_low_strength_diag",
        ]
    )

    # -------------------------------------------------------------------------
    # Final report
    # -------------------------------------------------------------------------

    return {
        "symbol": symbol,
        "timeframe": timeframe_name,
        "requested_bars": bars,
        "candles": len(result),

        "pivot_highs": int(
            pivot_high_mask.sum()
        ),
        "pivot_lows": int(
            pivot_low_mask.sum()
        ),
        "pivot_rows": int(
            pivot_mask.sum()
        ),
        "double_pivots": int(
            double_mask.sum()
        ),

        "double_pivot_percent": _percent(
            int(double_mask.sum()),
            int(pivot_mask.sum()),
        ),

        "double_high_dominant": (
            double_high_dominant
        ),
        "double_low_dominant": (
            double_low_dominant
        ),
        "double_ties": (
            double_ties
        ),

        "valid_swings": int(
            valid_swing_mask.sum()
        ),
        "minor_swings": int(
            minor_mask.sum()
        ),
        "major_swings": int(
            major_mask.sum()
        ),

        "weak_positive_pivots": weak_count,
        "zero_strength_pivots": (
            zero_strength_count
        ),

        "minor_strength_bucket": (
            minor_strength_count
        ),
        "major_strength_bucket": (
            major_strength_count
        ),

        "HH": hh,
        "HL": hl,
        "LH": lh,
        "LL": ll,

        "bullish_bias_bars": bullish_bias,
        "bearish_bias_bars": bearish_bias,
        "neutral_bias_bars": neutral_bias,

        "repeated_swing_type": (
            repeated_swing_type
        ),

        "pivot_strength_stats": _stats(
            positive_strength
        ),

        "pivot_high_strength_stats": (
            high_strength_stats
        ),

        "pivot_low_strength_stats": (
            low_strength_stats
        ),

        "atr_stats": _stats(
            result["atr"]
        ),

        "pivot_spacing": pivot_spacing,
        "swing_spacing": swing_spacing,
        "major_spacing": major_spacing,

        "threshold_sensitivity": (
            threshold_sensitivity
        ),

        "final_structure_bias": (
            str(
                result[
                    "structure_bias"
                ].iloc[-1]
            )
        ),
    }


# =============================================================================
# Printing
# =============================================================================

def _print_stats(
    title: str,
    stats: dict[str, float],
) -> None:

    print(
        f"\n{title}"
    )

    for key, value in stats.items():

        if np.isnan(value):
            display = "n/a"
        else:
            display = f"{value:.4f}"

        print(
            f"  {key:>8}: {display}"
        )


def print_report(
    report: dict,
    min_strength: float,
    major_strength: float,
) -> None:

    print(
        "\n"
        + "=" * 78
    )

    print(
        f"{report['symbol']} "
        f"{report['timeframe']} "
        f"MARKET STRUCTURE DIAGNOSTIC"
    )

    print(
        "=" * 78
    )

    print(
        f"Candles                  : "
        f"{report['candles']}"
    )

    print(
        f"Pivot highs              : "
        f"{report['pivot_highs']}"
    )

    print(
        f"Pivot lows               : "
        f"{report['pivot_lows']}"
    )

    print(
        f"Unique pivot rows        : "
        f"{report['pivot_rows']}"
    )

    print(
        f"Double pivots            : "
        f"{report['double_pivots']} "
        f"({report['double_pivot_percent']:.3f}%)"
    )

    print(
        f"  HIGH dominant          : "
        f"{report['double_high_dominant']}"
    )

    print(
        f"  LOW dominant           : "
        f"{report['double_low_dominant']}"
    )

    print(
        f"  Equal strength         : "
        f"{report['double_ties']}"
    )

    print()

    print(
        f"Valid structural swings  : "
        f"{report['valid_swings']}"
    )

    print(
        f"Minor swings             : "
        f"{report['minor_swings']}"
    )

    print(
        f"Major swings             : "
        f"{report['major_swings']}"
    )

    print(
        f"Weak positive pivots     : "
        f"{report['weak_positive_pivots']}"
    )

    print(
        f"Zero-strength pivots     : "
        f"{report['zero_strength_pivots']}"
    )

    print()

    print(
        f"Strength < {min_strength:.2f}"
        f"       : "
        f"{report['weak_positive_pivots']}"
    )

    print(
        f"{min_strength:.2f} <= strength "
        f"< {major_strength:.2f}: "
        f"{report['minor_strength_bucket']}"
    )

    print(
        f"Strength >= {major_strength:.2f}"
        f"      : "
        f"{report['major_strength_bucket']}"
    )

    print()

    print(
        f"HH / HL / LH / LL        : "
        f"{report['HH']} / "
        f"{report['HL']} / "
        f"{report['LH']} / "
        f"{report['LL']}"
    )

    print(
        f"Repeated swing direction : "
        f"{report['repeated_swing_type']}"
    )

    print(
        f"Final structure bias     : "
        f"{report['final_structure_bias']}"
    )

    _print_stats(
        "Pivot strength distribution",
        report[
            "pivot_strength_stats"
        ],
    )

    _print_stats(
        "Pivot HIGH strength",
        report[
            "pivot_high_strength_stats"
        ],
    )

    _print_stats(
        "Pivot LOW strength",
        report[
            "pivot_low_strength_stats"
        ],
    )

    _print_stats(
        "ATR distribution",
        report[
            "atr_stats"
        ],
    )

    _print_stats(
        "Pivot spacing (bars)",
        report[
            "pivot_spacing"
        ],
    )

    _print_stats(
        "Valid swing spacing (bars)",
        report[
            "swing_spacing"
        ],
    )

    _print_stats(
        "Major swing spacing (bars)",
        report[
            "major_spacing"
        ],
    )

    print(
        "\nThreshold sensitivity"
    )

    for (
        threshold,
        values,
    ) in report[
        "threshold_sensitivity"
    ].items():

        print(
            f"  >= {threshold:>4.2f}: "
            f"{values['count']:>6} "
            f"({values['percent']:>6.2f}%)"
        )


# =============================================================================
# Cross-Timeframe Summary
# =============================================================================

def print_summary(
    reports: list[dict],
) -> None:

    rows = []

    for report in reports:

        strength = report[
            "pivot_strength_stats"
        ]

        rows.append(
            {
                "TF": report[
                    "timeframe"
                ],
                "Candles": report[
                    "candles"
                ],
                "Pivots": report[
                    "pivot_rows"
                ],
                "Double": report[
                    "double_pivots"
                ],
                "Double%": round(
                    report[
                        "double_pivot_percent"
                    ],
                    3,
                ),
                "Swings": report[
                    "valid_swings"
                ],
                "Minor": report[
                    "minor_swings"
                ],
                "Major": report[
                    "major_swings"
                ],
                "MedianStr": round(
                    strength["median"],
                    3,
                )
                if np.isfinite(
                    strength["median"]
                )
                else np.nan,
                "P90Str": round(
                    strength["p90"],
                    3,
                )
                if np.isfinite(
                    strength["p90"]
                )
                else np.nan,
                "P95Str": round(
                    strength["p95"],
                    3,
                )
                if np.isfinite(
                    strength["p95"]
                )
                else np.nan,
                "HH": report["HH"],
                "HL": report["HL"],
                "LH": report["LH"],
                "LL": report["LL"],
            }
        )

    summary = pd.DataFrame(
        rows
    )

    print(
        "\n\n"
        + "#" * 100
    )

    print(
        "CROSS-TIMEFRAME SUMMARY"
    )

    print(
        "#" * 100
    )

    print(
        summary.to_string(
            index=False
        )
    )


# =============================================================================
# CLI
# =============================================================================

def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "PulseViper XAUUSD "
            "Market Structure Diagnostic"
        )
    )

    parser.add_argument(
        "--symbol",
        default="XAUUSDm",
    )

    parser.add_argument(
        "--bars",
        type=int,
        default=10000,
    )

    parser.add_argument(
        "--timeframes",
        nargs="+",
        default=[
            "M1",
            "M5",
            "M15",
            "M30",
            "H1",
            "H4",
            "D1",
        ],
        choices=list(
            TIMEFRAMES.keys()
        ),
    )

    parser.add_argument(
        "--pivot-window",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--min-strength",
        type=float,
        default=1.20,
    )

    parser.add_argument(
        "--major-strength",
        type=float,
        default=2.50,
    )

    return parser.parse_args()


# =============================================================================
# Main
# =============================================================================

def main() -> None:

    args = parse_args()

    if args.bars <= 0:
        raise ValueError(
            "--bars must be greater than zero"
        )

    if args.pivot_window <= 0:
        raise ValueError(
            "--pivot-window must be "
            "greater than zero"
        )

    if args.min_strength < 0:
        raise ValueError(
            "--min-strength cannot be negative"
        )

    if (
        args.major_strength
        <= args.min_strength
    ):
        raise ValueError(
            "--major-strength must be "
            "greater than --min-strength"
        )

    print(
        "=" * 78
    )

    print(
        "PulseViper XAU AI"
    )

    print(
        "Real Gold Market Structure Calibration"
    )

    print(
        "=" * 78
    )

    print(
        f"Symbol          : {args.symbol}"
    )

    print(
        f"Requested bars  : {args.bars}"
    )

    print(
        f"Pivot window    : {args.pivot_window}"
    )

    print(
        f"Min strength    : {args.min_strength}"
    )

    print(
        f"Major strength  : {args.major_strength}"
    )

    print(
        "Timeframes      : "
        + ", ".join(
            args.timeframes
        )
    )

    reports: list[dict] = []

    for timeframe_name in args.timeframes:

        try:

            report = analyze_timeframe(
                symbol=args.symbol,
                timeframe_name=(
                    timeframe_name
                ),
                bars=args.bars,
                pivot_window=(
                    args.pivot_window
                ),
                min_strength=(
                    args.min_strength
                ),
                major_strength=(
                    args.major_strength
                ),
            )

            reports.append(
                report
            )

            print_report(
                report,
                min_strength=(
                    args.min_strength
                ),
                major_strength=(
                    args.major_strength
                ),
            )

        except Exception as exc:

            print(
                "\n"
                + "!" * 78
            )

            print(
                f"{timeframe_name} FAILED"
            )

            print(
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            print(
                "!" * 78
            )

    if reports:
        print_summary(
            reports
        )

    else:
        raise RuntimeError(
            "No timeframe diagnostics "
            "completed successfully."
        )


if __name__ == "__main__":
    main()