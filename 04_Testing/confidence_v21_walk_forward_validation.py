"""
PulseViper XAU AI
Confidence v2.1 Frozen-Hypothesis Multi-Fold Historical Robustness Validator

Research only. Production Confidence is NOT modified.

Default:
python 04_Testing/confidence_v21_walk_forward_validation.py --bars 160000 --cutoff-date 2026-06-29 --discovery-days 10 --embargo-days 1 --oos-days 5 --step-days 5 --max-folds 8

The default cutoff keeps the already-inspected 2026-06-29 onward sample out of
this validation set. Hypothesis thresholds are frozen before this script runs.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd


# =============================================================================
# Project/bootstrap and reuse of the already-pushed holdout validator
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_TEXT = str(PROJECT_ROOT)

if PROJECT_ROOT_TEXT not in sys.path:
    sys.path.insert(
        0,
        PROJECT_ROOT_TEXT,
    )


research: Any = importlib.import_module(
    "04_Testing.confidence_v21_research_validation"
)

fetcher: Any = research.fetcher
scalping_pipeline: Any = research.scalping_pipeline

_complete_dates: Any = research._complete_dates
_build_event_frame: Any = research._build_event_frame
_summary: Any = research._summary
_to_numeric: Any = research._to_numeric
_as_float: Any = research._as_float
_fmt: Any = research._fmt

_confidence_table: Any = research._confidence_table
_confidence_monotonicity: Any = research._confidence_monotonicity
_redundancy_table: Any = research._redundancy_table


Predicate = Callable[
    [
        pd.DataFrame,
    ],
    pd.Series,
]


# =============================================================================
# Frozen hypotheses
#
# expected_sign:
#
#   +1 = selected setups should OUTPERFORM the rest at 20 bars
#   -1 = selected setups should UNDERPERFORM the rest at 20 bars
#
# IMPORTANT:
# Do NOT edit these thresholds after seeing this validator's output.
# =============================================================================


def _numeric(
    frame: pd.DataFrame,
    column: str,
) -> pd.Series:

    if column not in frame.columns:

        return pd.Series(
            np.nan,
            index=frame.index,
            dtype="float64",
        )

    return _to_numeric(
        frame[
            column
        ]
    )


def _direction(
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
            str(
                value
            ).upper()
            for value
            in frame[
                "direction"
            ].tolist()
        ],
        index=frame.index,
        dtype="object",
    )


# =============================================================================
# Primary hypotheses
# =============================================================================


def _rejection_high(
    frame: pd.DataFrame,
) -> pd.Series:

    values = _numeric(
        frame,
        "setup_rejection_fill_percent",
    )

    return (
        values
        >= 90.0
    )


def _rejection_low(
    frame: pd.DataFrame,
) -> pd.Series:

    values = _numeric(
        frame,
        "setup_rejection_fill_percent",
    )

    return (
        values
        <= 38.0
    )


def _fvg_single(
    frame: pd.DataFrame,
) -> pd.Series:

    values = _numeric(
        frame,
        "setup_fvg_count",
    )

    return (
        values
        == 1.0
    )


def _fvg_crowded(
    frame: pd.DataFrame,
) -> pd.Series:

    values = _numeric(
        frame,
        "setup_fvg_count",
    )

    return (
        values
        >= 4.0
    )


def _impulse_moderate(
    frame: pd.DataFrame,
) -> pd.Series:

    values = _numeric(
        frame,
        "setup_impulse_strength",
    )

    return (
        (
            values
            >= 1.40
        )
        &
        (
            values
            <= 1.65
        )
    )


# =============================================================================
# Secondary / interaction hypotheses
# =============================================================================


def _bullish_extreme_impulse(
    frame: pd.DataFrame,
) -> pd.Series:

    values = _numeric(
        frame,
        "setup_impulse_strength",
    )

    directions = _direction(
        frame
    )

    return (
        (
            directions
            == "BULLISH"
        )
        &
        (
            values
            >= 1.90
        )
    )


def _bearish_extreme_impulse(
    frame: pd.DataFrame,
) -> pd.Series:

    values = _numeric(
        frame,
        "setup_impulse_strength",
    )

    directions = _direction(
        frame
    )

    return (
        (
            directions
            == "BEARISH"
        )
        &
        (
            values
            >= 1.90
        )
    )


def _displacement_mid_high(
    frame: pd.DataFrame,
) -> pd.Series:

    values = _numeric(
        frame,
        "setup_displacement_score",
    )

    return (
        (
            values
            >= 93.5
        )
        &
        (
            values
            < 97.0
        )
    )


def _timing_6_to_8(
    frame: pd.DataFrame,
) -> pd.Series:

    values = _numeric(
        frame,
        "setup_sweep_to_ready_bars",
    )

    return (
        (
            values
            >= 6.0
        )
        &
        (
            values
            <= 8.0
        )
    )


def _timing_9_to_13(
    frame: pd.DataFrame,
) -> pd.Series:

    values = _numeric(
        frame,
        "setup_sweep_to_ready_bars",
    )

    return (
        (
            values
            >= 9.0
        )
        &
        (
            values
            <= 13.0
        )
    )


# =============================================================================
# Frozen hypothesis registry
# =============================================================================

HYPOTHESES: tuple[
    dict[
        str,
        Any,
    ],
    ...,
] = (

    {
        "key": "REJECTION_HIGH",
        "name": "High rejection >= 90%",
        "tier": "PRIMARY",
        "expected_sign": 1,
        "predicate": _rejection_high,
    },

    {
        "key": "REJECTION_LOW",
        "name": "Low rejection <= 38%",
        "tier": "PRIMARY",
        "expected_sign": -1,
        "predicate": _rejection_low,
    },

    {
        "key": "FVG_SINGLE",
        "name": "Single FVG",
        "tier": "PRIMARY",
        "expected_sign": 1,
        "predicate": _fvg_single,
    },

    {
        "key": "FVG_CROWDED",
        "name": "Crowded FVG count >= 4",
        "tier": "PRIMARY",
        "expected_sign": -1,
        "predicate": _fvg_crowded,
    },

    {
        "key": "IMPULSE_MODERATE",
        "name": "Moderate impulse 1.40-1.65",
        "tier": "PRIMARY",
        "expected_sign": 1,
        "predicate": _impulse_moderate,
    },

    {
        "key": "BULL_EXTREME_IMPULSE",
        "name": "Bullish extreme impulse >= 1.90",
        "tier": "SECONDARY",
        "expected_sign": -1,
        "predicate": _bullish_extreme_impulse,
    },

    {
        "key": "BEAR_EXTREME_IMPULSE",
        "name": "Bearish extreme impulse >= 1.90",
        "tier": "SECONDARY",
        "expected_sign": 1,
        "predicate": _bearish_extreme_impulse,
    },

    {
        "key": "DISPLACEMENT_MID_HIGH",
        "name": "Displacement 93.5-97.0",
        "tier": "SECONDARY",
        "expected_sign": -1,
        "predicate": _displacement_mid_high,
    },

    {
        "key": "TIMING_6_8",
        "name": "Sweep->READY 6-8 bars",
        "tier": "SECONDARY",
        "expected_sign": 1,
        "predicate": _timing_6_to_8,
    },

    {
        "key": "TIMING_9_13",
        "name": "Sweep->READY 9-13 bars",
        "tier": "SECONDARY",
        "expected_sign": -1,
        "predicate": _timing_9_to_13,
    },
)


# =============================================================================
# Output helpers
# =============================================================================


def _separator(
    char: str = "=",
    width: int = 108,
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
            108,
            max(
                24,
                len(
                    title
                ),
            ),
        )
    )


def _expected_text(
    sign: int,
) -> str:

    if sign > 0:

        return "OUTPERFORM"

    return "UNDERPERFORM"


# =============================================================================
# Rolling fold construction
# =============================================================================


def _build_folds(
    dates: list[
        str
    ],
    discovery_days: int,
    embargo_days: int,
    oos_days: int,
    step_days: int,
    max_folds: int,
) -> list[
    dict[
        str,
        Any,
    ]
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

    if step_days <= 0:

        raise ValueError(
            "--step-days must be > 0"
        )

    if max_folds <= 0:

        raise ValueError(
            "--max-folds must be > 0"
        )

    window = (
        discovery_days
        + embargo_days
        + oos_days
    )

    if len(
        dates
    ) < window:

        raise RuntimeError(
            (
                f"Need at least {window} complete dates "
                f"before cutoff; found {len(dates)}. "
                "Increase --bars."
            )
        )

    starts = list(
        range(
            0,
            len(
                dates
            )
            - window
            + 1,
            step_days,
        )
    )

    if len(
        starts
    ) > max_folds:

        starts = starts[
            -max_folds:
        ]

    folds: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for (
        fold_number,
        start,
    ) in enumerate(
        starts,
        start=1,
    ):

        discovery_end = (
            start
            + discovery_days
        )

        embargo_end = (
            discovery_end
            + embargo_days
        )

        oos_end = (
            embargo_end
            + oos_days
        )

        folds.append(
            {
                "fold": (
                    fold_number
                ),

                "discovery_dates": (
                    dates[
                        start:
                        discovery_end
                    ]
                ),

                "embargo_dates": (
                    dates[
                        discovery_end:
                        embargo_end
                    ]
                ),

                "oos_dates": (
                    dates[
                        embargo_end:
                        oos_end
                    ]
                ),
            }
        )

    return folds


# =============================================================================
# Candidate measurements
# =============================================================================


def _safe_mask(
    frame: pd.DataFrame,
    predicate: Predicate,
) -> pd.Series:

    raw = predicate(
        frame
    )

    return pd.Series(
        raw.to_numpy(
            dtype=bool
        ),
        index=frame.index,
        dtype="bool",
    )


def _candidate_stats(
    frame: pd.DataFrame,
    predicate: Predicate,
) -> dict[
    str,
    Any,
]:

    if frame.empty:

        return {

            "selected_n": 0,

            "rest_n": 0,

            "selected_net5": np.nan,

            "selected_net10": np.nan,

            "selected_net20": np.nan,

            "rest_net20": np.nan,

            "spread20": np.nan,

            "selected_pos20": np.nan,

            "selected_1r": np.nan,
        }

    mask = _safe_mask(
        frame,
        predicate,
    )

    selected = frame.loc[
        mask
    ]

    rest = frame.loc[
        ~mask
    ]

    selected_summary = _summary(
        selected
    )

    rest_summary = _summary(
        rest
    )

    selected_net20 = _as_float(
        selected_summary.get(
            "net20_median",
            np.nan,
        )
    )

    rest_net20 = _as_float(
        rest_summary.get(
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
            rest_net20
        )
    ):

        spread20 = (
            selected_net20
            - rest_net20
        )

    else:

        spread20 = np.nan

    return {

        "selected_n": (
            len(
                selected
            )
        ),

        "rest_n": (
            len(
                rest
            )
        ),

        "selected_net5": _as_float(
            selected_summary.get(
                "net5_median",
                np.nan,
            )
        ),

        "selected_net10": _as_float(
            selected_summary.get(
                "net10_median",
                np.nan,
            )
        ),

        "selected_net20": (
            selected_net20
        ),

        "rest_net20": (
            rest_net20
        ),

        "spread20": (
            spread20
        ),

        "selected_pos20": _as_float(
            selected_summary.get(
                "positive20_pct",
                np.nan,
            )
        ),

        "selected_1r": _as_float(
            selected_summary.get(
                "target_1_to_1_pct",
                np.nan,
            )
        ),
    }


def _expected_holds(
    spread: float,
    expected_sign: int,
) -> bool:

    if not np.isfinite(
        spread
    ):

        return False

    if expected_sign > 0:

        return (
            spread
            > 0.0
        )

    return (
        spread
        < 0.0
    )


def _fold_result(
    discovery: pd.DataFrame,
    oos: pd.DataFrame,
    hypothesis: dict[
        str,
        Any,
    ],
    min_selected: int,
    min_rest: int,
) -> dict[
    str,
    Any,
]:

    predicate: Predicate = (
        hypothesis[
            "predicate"
        ]
    )

    expected_sign = int(
        hypothesis[
            "expected_sign"
        ]
    )

    discovery_stats = _candidate_stats(
        discovery,
        predicate,
    )

    oos_stats = _candidate_stats(
        oos,
        predicate,
    )

    spread = _as_float(
        oos_stats[
            "spread20"
        ]
    )

    eligible = (
        int(
            oos_stats[
                "selected_n"
            ]
        )
        >= min_selected
        and
        int(
            oos_stats[
                "rest_n"
            ]
        )
        >= min_rest
        and
        np.isfinite(
            spread
        )
    )

    confirmed = (
        eligible
        and
        _expected_holds(
            spread,
            expected_sign,
        )
    )

    strong_confirmed = (
        confirmed
        and
        abs(
            spread
        )
        >= 0.20
    )

    return {

        "discovery": (
            discovery_stats
        ),

        "oos": (
            oos_stats
        ),

        "eligible": (
            eligible
        ),

        "confirmed": (
            confirmed
        ),

        "strong_confirmed": (
            strong_confirmed
        ),
    }


# =============================================================================
# Current Confidence v2 benchmark
# =============================================================================


def _spearman_confidence_net20(
    frame: pd.DataFrame,
) -> float:

    if (
        frame.empty
        or
        "confidence_score"
        not in frame.columns
        or
        "net_20"
        not in frame.columns
    ):

        return np.nan

    working = pd.DataFrame(
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
    )

    working = working.dropna()

    if len(
        working
    ) < 3:

        return np.nan

    correlation = working.corr(
        method="spearman"
    )

    matrix = correlation.to_numpy(
        dtype=np.float64
    )

    if matrix.shape != (
        2,
        2,
    ):

        return np.nan

    rho: float = float(
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


def _confidence_fold_row(
    fold_number: int,
    oos: pd.DataFrame,
) -> dict[
    str,
    Any,
]:

    table = _confidence_table(
        oos
    )

    return {

        "fold": (
            fold_number
        ),

        "oos_n": (
            len(
                oos
            )
        ),

        "spearman_conf_net20": round(
            _spearman_confidence_net20(
                oos
            ),
            3,
        ),

        "monotonicity": (
            _confidence_monotonicity(
                table
            )
        ),
    }


# =============================================================================
# Aggregate robustness
# =============================================================================


def _aggregate_candidate(
    hypothesis: dict[
        str,
        Any,
    ],
    fold_results: list[
        dict[
            str,
            Any,
        ]
    ],
    pooled_oos: pd.DataFrame,
    min_selected: int,
    min_rest: int,
) -> dict[
    str,
    Any,
]:

    expected_sign = int(
        hypothesis[
            "expected_sign"
        ]
    )

    predicate: Predicate = (
        hypothesis[
            "predicate"
        ]
    )

    eligible_results = [
        result
        for result
        in fold_results
        if bool(
            result[
                "eligible"
            ]
        )
    ]

    eligible_folds = len(
        eligible_results
    )

    confirmed_folds = sum(
        bool(
            result[
                "confirmed"
            ]
        )
        for result
        in eligible_results
    )

    strong_folds = sum(
        bool(
            result[
                "strong_confirmed"
            ]
        )
        for result
        in eligible_results
    )

    spreads = np.asarray(
        [
            _as_float(
                result[
                    "oos"
                ][
                    "spread20"
                ]
            )
            for result
            in eligible_results
        ],
        dtype=np.float64,
    )

    finite_spreads = spreads[
        np.isfinite(
            spreads
        )
    ]

    if finite_spreads.size > 0:

        median_spread = float(
            np.median(
                finite_spreads
            )
        )

    else:

        median_spread = np.nan

    if eligible_folds > 0:

        confirm_rate = (
            confirmed_folds
            / eligible_folds
            * 100.0
        )

        strong_rate = (
            strong_folds
            / eligible_folds
            * 100.0
        )

    else:

        confirm_rate = np.nan

        strong_rate = np.nan

    pooled = _candidate_stats(
        pooled_oos,
        predicate,
    )

    pooled_spread = _as_float(
        pooled[
            "spread20"
        ]
    )

    bullish = pooled_oos.loc[
        _direction(
            pooled_oos
        )
        == "BULLISH"
    ]

    bearish = pooled_oos.loc[
        _direction(
            pooled_oos
        )
        == "BEARISH"
    ]

    bullish_stats = _candidate_stats(
        bullish,
        predicate,
    )

    bearish_stats = _candidate_stats(
        bearish,
        predicate,
    )

    bull_spread = _as_float(
        bullish_stats[
            "spread20"
        ]
    )

    bear_spread = _as_float(
        bearish_stats[
            "spread20"
        ]
    )

    pooled_eligible = (

        int(
            pooled[
                "selected_n"
            ]
        )
        >= max(
            20,
            min_selected
            * 3,
        )

        and

        int(
            pooled[
                "rest_n"
            ]
        )
        >= max(
            30,
            min_rest
            * 3,
        )

        and

        np.isfinite(
            pooled_spread
        )
    )

    pooled_holds = (
        pooled_eligible
        and
        _expected_holds(
            pooled_spread,
            expected_sign,
        )
    )

    median_holds = (
        np.isfinite(
            median_spread
        )
        and
        _expected_holds(
            median_spread,
            expected_sign,
        )
    )

    direction_reversals = 0

    direction_eligible = 0

    for (
        side_stats,
        side_spread,
    ) in (
        (
            bullish_stats,
            bull_spread,
        ),
        (
            bearish_stats,
            bear_spread,
        ),
    ):

        side_is_eligible = (

            int(
                side_stats[
                    "selected_n"
                ]
            )
            >= max(
                10,
                min_selected
                * 2,
            )

            and

            int(
                side_stats[
                    "rest_n"
                ]
            )
            >= max(
                15,
                min_rest
                * 2,
            )

            and

            np.isfinite(
                side_spread
            )
        )

        if not side_is_eligible:

            continue

        direction_eligible += 1

        if (
            not _expected_holds(
                side_spread,
                expected_sign,
            )
            and
            abs(
                side_spread
            )
            >= 0.20
        ):

            direction_reversals += 1

    tier = str(
        hypothesis[
            "tier"
        ]
    )

    # =========================================================================
    # Verdict
    # =========================================================================

    if (
        eligible_folds
        < 3
        or
        not pooled_eligible
    ):

        verdict = (
            "INSUFFICIENT"
        )

    elif (
        pooled_holds
        and
        median_holds
        and
        confirm_rate
        >= 70.0
        and
        abs(
            pooled_spread
        )
        >= 0.20
        and
        direction_reversals
        == 0
        and
        (
            tier
            != "PRIMARY"
            or
            eligible_folds
            >= 4
        )
    ):

        verdict = (
            "ROBUST"
        )

    elif (
        pooled_holds
        and
        median_holds
        and
        confirm_rate
        >= 60.0
        and
        direction_reversals
        <= 1
    ):

        verdict = (
            "PROMISING"
        )

    elif (
        pooled_eligible
        and
        not pooled_holds
        and
        confirm_rate
        <= 40.0
    ):

        verdict = (
            "REVERSED"
        )

    else:

        verdict = (
            "UNSTABLE"
        )

    return {

        "key": (
            hypothesis[
                "key"
            ]
        ),

        "tier": (
            tier
        ),

        "expected": (
            _expected_text(
                expected_sign
            )
        ),

        "eligible_folds": (
            eligible_folds
        ),

        "confirmed_folds": (
            confirmed_folds
        ),

        "strong_folds": (
            strong_folds
        ),

        "confirm_pct": round(
            confirm_rate,
            1,
        ),

        "strong_pct": round(
            strong_rate,
            1,
        ),

        "median_fold_spread20": round(
            median_spread,
            3,
        ),

        "pooled_selected_n": int(
            pooled[
                "selected_n"
            ]
        ),

        "pooled_spread20": round(
            pooled_spread,
            3,
        ),

        "bull_spread20": round(
            bull_spread,
            3,
        ),

        "bear_spread20": round(
            bear_spread,
            3,
        ),

        "direction_reversals": (
            direction_reversals
        ),

        "direction_eligible": (
            direction_eligible
        ),

        "verdict": (
            verdict
        ),
    }


# =============================================================================
# Main
# =============================================================================


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "PulseViper Confidence v2.1 "
            "frozen-hypothesis multi-fold historical validator"
        )
    )

    parser.add_argument(
        "--bars",
        type=int,
        default=160000,
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
        default=5,
    )

    parser.add_argument(
        "--step-days",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--max-folds",
        type=int,
        default=8,
    )

    parser.add_argument(
        "--min-selected-events",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--min-rest-events",
        type=int,
        default=10,
    )

    args = parser.parse_args()

    if args.bars <= 0:

        raise ValueError(
            "--bars must be > 0"
        )

    if args.min_selected_events <= 0:

        raise ValueError(
            "--min-selected-events must be > 0"
        )

    if args.min_rest_events <= 0:

        raise ValueError(
            "--min-rest-events must be > 0"
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
        "PulseViper Confidence v2.1 Multi-Fold Historical Robustness Validation"
    )

    print(
        f"Project root        : "
        f"{PROJECT_ROOT_TEXT}"
    )

    print(
        f"Requested symbol    : "
        f"{args.symbol}"
    )

    print(
        f"Requested M1 bars   : "
        f"{args.bars}"
    )

    print(
        f"Strict cutoff       : "
        f"dates < {cutoff_label}"
    )

    print(
        f"Discovery / fold    : "
        f"{args.discovery_days} days"
    )

    print(
        f"Embargo / fold      : "
        f"{args.embargo_days} days"
    )

    print(
        f"OOS / fold          : "
        f"{args.oos_days} days"
    )

    print(
        f"Step                : "
        f"{args.step_days} days"
    )

    print(
        f"Maximum folds       : "
        f"{args.max_folds}"
    )

    print()

    print(
        "Frozen hypotheses:"
    )

    for hypothesis in (
        HYPOTHESES
    ):

        print(
            (
                f"  [{hypothesis['tier']}] "
                f"{hypothesis['key']}: "
                f"{hypothesis['name']} "
                f"=> "
                f"{_expected_text(int(hypothesis['expected_sign']))}"
            )
        )

    # =========================================================================
    # Fetch
    # =========================================================================

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
        f"Fetched valid bars  : "
        f"{len(raw)}"
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
            f"Resolved symbol     : "
            f"{resolved_symbol}"
        )

    # =========================================================================
    # Pipeline
    # =========================================================================

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

    complete_dates: list[
        str
    ] = (
        _complete_dates(
            enriched
        )
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

    if not eligible_dates:

        raise RuntimeError(
            (
                "No complete dates exist before cutoff. "
                "Increase --bars."
            )
        )

    folds = _build_folds(
        dates=eligible_dates,
        discovery_days=args.discovery_days,
        embargo_days=args.embargo_days,
        oos_days=args.oos_days,
        step_days=args.step_days,
        max_folds=args.max_folds,
    )

    _section(
        "UNTOUCHED HISTORICAL DATE UNIVERSE"
    )

    print(
        f"Complete dates before cutoff : "
        f"{len(eligible_dates)}"
    )

    print(
        f"Earliest eligible date       : "
        f"{eligible_dates[0]}"
    )

    print(
        f"Latest eligible date         : "
        f"{eligible_dates[-1]}"
    )

    print(
        f"Generated folds              : "
        f"{len(folds)}"
    )

    print()

    print(
        "Building one-shot trade_ready event dataset..."
    )

    events: pd.DataFrame = (
        _build_event_frame(
            enriched
        )
    )

    if events.empty:

        raise RuntimeError(
            "Pipeline produced no trade_ready events."
        )

    historical_events = events.loc[
        events[
            "date_label"
        ].isin(
            eligible_dates
        )
    ].copy()

    print(
        (
            "Trade-ready events before cutoff: "
            f"{len(historical_events)}"
        )
    )

    # =========================================================================
    # Containers
    # =========================================================================

    fold_results_by_key: dict[
        str,
        list[
            dict[
                str,
                Any,
            ]
        ],
    ] = {

        str(
            hypothesis[
                "key"
            ]
        ): []

        for hypothesis

        in HYPOTHESES
    }

    pooled_oos_parts: list[
        pd.DataFrame
    ] = []

    confidence_rows: list[
        dict[
            str,
            Any,
        ]
    ] = []

    # =========================================================================
    # Fold loop
    # =========================================================================

    for fold in folds:

        fold_number = int(
            fold[
                "fold"
            ]
        )

        discovery_dates: list[
            str
        ] = (
            fold[
                "discovery_dates"
            ]
        )

        embargo_dates: list[
            str
        ] = (
            fold[
                "embargo_dates"
            ]
        )

        oos_dates: list[
            str
        ] = (
            fold[
                "oos_dates"
            ]
        )

        discovery = events.loc[
            events[
                "date_label"
            ].isin(
                discovery_dates
            )
        ].copy()

        oos = events.loc[
            events[
                "date_label"
            ].isin(
                oos_dates
            )
        ].copy()

        pooled_oos_parts.append(
            oos
        )

        _section(
            f"FOLD {fold_number}"
        )

        print(
            (
                f"DISCOVERY : "
                f"{discovery_dates[0]} -> "
                f"{discovery_dates[-1]} "
                f"| events={len(discovery)}"
            )
        )

        if embargo_dates:

            print(
                (
                    f"EMBARGO   : "
                    f"{embargo_dates[0]} -> "
                    f"{embargo_dates[-1]}"
                )
            )

        else:

            print(
                "EMBARGO   : <none>"
            )

        print(
            (
                f"OOS       : "
                f"{oos_dates[0]} -> "
                f"{oos_dates[-1]} "
                f"| events={len(oos)}"
            )
        )

        # ---------------------------------------------------------------------
        # Baseline
        # ---------------------------------------------------------------------

        discovery_base = _summary(
            discovery
        )

        oos_base = _summary(
            oos
        )

        print(
            (
                "Baseline median NET20 "
                f"| DISC="
                f"{_fmt(discovery_base.get('net20_median'))} "
                f"| OOS="
                f"{_fmt(oos_base.get('net20_median'))}"
            )
        )

        # ---------------------------------------------------------------------
        # Current Confidence benchmark
        # ---------------------------------------------------------------------

        confidence_row = _confidence_fold_row(
            fold_number,
            oos,
        )

        confidence_rows.append(
            confidence_row
        )

        print(
            (
                "Current Confidence v2 "
                f"| rho(conf,net20)="
                f"{_fmt(confidence_row['spearman_conf_net20'])} "
                f"| "
                f"{confidence_row['monotonicity']}"
            )
        )

        # ---------------------------------------------------------------------
        # Frozen hypotheses
        # ---------------------------------------------------------------------

        fold_rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for hypothesis in (
            HYPOTHESES
        ):

            key = str(
                hypothesis[
                    "key"
                ]
            )

            result = _fold_result(
                discovery=discovery,
                oos=oos,
                hypothesis=hypothesis,
                min_selected=(
                    args.min_selected_events
                ),
                min_rest=(
                    args.min_rest_events
                ),
            )

            fold_results_by_key[
                key
            ].append(
                result
            )

            discovery_stats = (
                result[
                    "discovery"
                ]
            )

            oos_stats = (
                result[
                    "oos"
                ]
            )

            if not bool(
                result[
                    "eligible"
                ]
            ):

                status = (
                    "INSUFFICIENT"
                )

            elif bool(
                result[
                    "strong_confirmed"
                ]
            ):

                status = (
                    "STRONG"
                )

            elif bool(
                result[
                    "confirmed"
                ]
            ):

                status = (
                    "CONFIRM"
                )

            else:

                status = (
                    "REVERSE"
                )

            fold_rows.append(
                {

                    "key": (
                        key
                    ),

                    "tier": (
                        hypothesis[
                            "tier"
                        ]
                    ),

                    "disc_n": int(
                        discovery_stats[
                            "selected_n"
                        ]
                    ),

                    "disc_spread20": round(
                        _as_float(
                            discovery_stats[
                                "spread20"
                            ]
                        ),
                        3,
                    ),

                    "oos_n": int(
                        oos_stats[
                            "selected_n"
                        ]
                    ),

                    "oos_spread20": round(
                        _as_float(
                            oos_stats[
                                "spread20"
                            ]
                        ),
                        3,
                    ),

                    "oos_net20": round(
                        _as_float(
                            oos_stats[
                                "selected_net20"
                            ]
                        ),
                        3,
                    ),

                    "oos_pos20": round(
                        _as_float(
                            oos_stats[
                                "selected_pos20"
                            ]
                        ),
                        1,
                    ),

                    "status": (
                        status
                    ),
                }
            )

        print()

        print(
            pd.DataFrame(
                fold_rows
            ).to_string(
                index=False
            )
        )

    # =========================================================================
    # Unique pooled OOS
    # =========================================================================

    if pooled_oos_parts:

        pooled_oos = (
            pd.concat(
                pooled_oos_parts,
                axis=0,
            )
            .drop_duplicates(
                subset=[
                    "position"
                ]
            )
            .sort_values(
                "position"
            )
            .reset_index(
                drop=True
            )
        )

    else:

        pooled_oos = pd.DataFrame()

    # =========================================================================
    # Current Confidence v2 multi-fold benchmark
    # =========================================================================

    _section(
        "CURRENT CONFIDENCE v2 — MULTI-FOLD BENCHMARK"
    )

    confidence_frame = pd.DataFrame(
        confidence_rows
    )

    if confidence_frame.empty:

        print(
            "No Confidence fold rows."
        )

    else:

        print(
            confidence_frame.to_string(
                index=False
            )
        )

        rho_values = (
            _to_numeric(
                confidence_frame[
                    "spearman_conf_net20"
                ]
            )
            .dropna()
        )

        if not rho_values.empty:

            print()

            print(
                (
                    "Median fold Spearman rho "
                    "(Confidence vs NET20): "
                    f"{_fmt(rho_values.median())}"
                )
            )

    if not pooled_oos.empty:

        _subsection(
            "Pooled unique OOS Confidence buckets"
        )

        pooled_confidence = (
            _confidence_table(
                pooled_oos
            )
        )

        if pooled_confidence.empty:

            print(
                "No pooled Confidence bucket data."
            )

        else:

            print(
                pooled_confidence.to_string(
                    index=False
                )
            )

            print(
                (
                    "Pooled monotonicity: "
                    f"{_confidence_monotonicity(pooled_confidence)}"
                )
            )

    # =========================================================================
    # Aggregate frozen hypotheses
    # =========================================================================

    _section(
        "FROZEN HYPOTHESIS ROBUSTNESS MATRIX"
    )

    aggregate_rows: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for hypothesis in (
        HYPOTHESES
    ):

        key = str(
            hypothesis[
                "key"
            ]
        )

        aggregate_rows.append(
            _aggregate_candidate(
                hypothesis=hypothesis,
                fold_results=(
                    fold_results_by_key[
                        key
                    ]
                ),
                pooled_oos=pooled_oos,
                min_selected=(
                    args.min_selected_events
                ),
                min_rest=(
                    args.min_rest_events
                ),
            )
        )

    aggregate = pd.DataFrame(
        aggregate_rows
    )

    if aggregate.empty:

        print(
            "No aggregate results."
        )

    else:

        print(
            aggregate.to_string(
                index=False
            )
        )

    # =========================================================================
    # Redundancy
    # =========================================================================

    _section(
        "REDUNDANCY CHECK — UNIQUE POOLED OOS EVENTS"
    )

    redundancy = _redundancy_table(
        pooled_oos
    )

    if redundancy.empty:

        print(
            "No |Spearman rho| >= 0.70 pairs."
        )

    else:

        print(
            redundancy.to_string(
                index=False
            )
        )

    # =========================================================================
    # Production gate
    # =========================================================================

    _section(
        "CONFIDENCE v2.1 PRODUCTION GATE"
    )

    if aggregate.empty:

        print(
            "No candidates available."
        )

    else:

        primary = aggregate.loc[
            aggregate[
                "tier"
            ]
            == "PRIMARY"
        ]

        robust = primary.loc[
            primary[
                "verdict"
            ]
            == "ROBUST"
        ]

        promising = primary.loc[
            primary[
                "verdict"
            ]
            == "PROMISING"
        ]

        unstable = primary.loc[
            primary[
                "verdict"
            ].isin(
                [
                    "UNSTABLE",
                    "REVERSED",
                ]
            )
        ]

        print(
            (
                "ROBUST primary candidates     : "
                f"{len(robust)}"
            )
        )

        print(
            (
                "PROMISING primary candidates  : "
                f"{len(promising)}"
            )
        )

        print(
            (
                "UNSTABLE/REVERSED primary     : "
                f"{len(unstable)}"
            )
        )

        if not robust.empty:

            print()

            print(
                (
                    "Eligible for Confidence v2.1 "
                    "shadow-score design review:"
                )
            )

            for value in (
                robust[
                    "key"
                ].tolist()
            ):

                print(
                    f"  {value}"
                )

    print()

    print(
        (
            "ROBUST means a frozen market-behavior hypothesis "
            "survived this historical test. It does NOT prove "
            "profitability after costs and does NOT authorize "
            "live deployment."
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
            "Multi-fold historical robustness validator "
            "completed successfully."
        )
    )

    print()

    print(
        (
            "Next action: review robust primary hypotheses, "
            "then build a SHADOW Confidence v2.1 scorer and "
            "compare it against current Confidence v2 without "
            "changing trade execution."
        )
    )


if __name__ == "__main__":

    main()