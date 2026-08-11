"""
PulseViper XAU AI
Confidence v2.1 Shadow Moderate-Impulse Confirmation Validator

Research only. Does NOT modify production Confidence, trade_ready, risk,
or execution.

Frozen hypothesis:
    1.40 <= setup_impulse_strength <= 1.65

Default:
    python 04_Testing/confidence_v21_shadow_validation.py \
        --bars 450000 \
        --cutoff-date 2026-02-27 \
        --block-days 5 \
        --max-blocks 10
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


# =============================================================================
# Project bootstrap
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:

    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


research: Any = importlib.import_module(
    "04_Testing.confidence_v21_research_validation"
)


fetcher: Any = (
    research.fetcher
)

scalping_pipeline: Any = (
    research.scalping_pipeline
)

_complete_dates: Any = (
    research._complete_dates
)

_build_event_frame: Any = (
    research._build_event_frame
)

_summary: Any = (
    research._summary
)

_to_numeric: Any = (
    research._to_numeric
)

_as_float: Any = (
    research._as_float
)

_fmt: Any = (
    research._fmt
)

_confidence_table: Any = (
    research._confidence_table
)

_confidence_monotonicity: Any = (
    research._confidence_monotonicity
)


# =============================================================================
# Frozen hypothesis
# =============================================================================

IMPULSE_LOW = 1.40

IMPULSE_HIGH = 1.65


# =============================================================================
# Output
# =============================================================================

def _section(
    title: str,
) -> None:

    print()

    print(
        "="
        * 104
    )

    print(
        title
    )

    print(
        "="
        * 104
    )


# =============================================================================
# Moderate impulse
# =============================================================================

def _moderate_mask(
    frame: pd.DataFrame,
) -> pd.Series:

    if (
        "setup_impulse_strength"
        not in frame.columns
    ):

        return pd.Series(
            False,
            index=frame.index,
            dtype="bool",
        )

    impulse = _to_numeric(
        frame[
            "setup_impulse_strength"
        ]
    )

    mask = (
        (
            impulse
            >= IMPULSE_LOW
        )
        &
        (
            impulse
            <= IMPULSE_HIGH
        )
    )

    return pd.Series(
        mask.to_numpy(
            dtype=bool
        ),
        index=frame.index,
        dtype="bool",
    )


def _direction_mask(
    frame: pd.DataFrame,
    direction: str,
) -> pd.Series:

    if (
        "direction"
        not in frame.columns
    ):

        return pd.Series(
            False,
            index=frame.index,
            dtype="bool",
        )

    wanted = (
        direction.upper()
    )

    values = [

        (
            str(
                value
            ).upper()
            ==
            wanted
        )

        for value
        in frame[
            "direction"
        ].tolist()
    ]

    return pd.Series(
        values,
        index=frame.index,
        dtype="bool",
    )


# =============================================================================
# Statistics
# =============================================================================

def _basic_stats(
    frame: pd.DataFrame,
) -> dict[
    str,
    Any,
]:

    stats = _summary(
        frame
    )

    return {

        "n": int(
            stats.get(
                "n",
                0,
            )
        ),

        "net5": _as_float(
            stats.get(
                "net5_median",
                np.nan,
            )
        ),

        "net10": _as_float(
            stats.get(
                "net10_median",
                np.nan,
            )
        ),

        "net20": _as_float(
            stats.get(
                "net20_median",
                np.nan,
            )
        ),

        "pos20": _as_float(
            stats.get(
                "positive20_pct",
                np.nan,
            )
        ),

        "one_r": _as_float(
            stats.get(
                "target_1_to_1_pct",
                np.nan,
            )
        ),
    }


def _difference(
    selected_value: float,
    rest_value: float,
) -> float:

    if (
        np.isfinite(
            selected_value
        )
        and
        np.isfinite(
            rest_value
        )
    ):

        return float(
            selected_value
            - rest_value
        )

    return np.nan


def _selected_vs_rest(
    frame: pd.DataFrame,
) -> dict[
    str,
    Any,
]:

    if frame.empty:

        return {

            "total_n": 0,

            "selected_n": 0,

            "rest_n": 0,

            "coverage_pct": np.nan,

            "selected_net5": np.nan,

            "selected_net10": np.nan,

            "selected_net20": np.nan,

            "rest_net5": np.nan,

            "rest_net10": np.nan,

            "rest_net20": np.nan,

            "spread5": np.nan,

            "spread10": np.nan,

            "spread20": np.nan,

            "selected_pos20": np.nan,

            "selected_1r": np.nan,
        }

    mask = _moderate_mask(
        frame
    )

    selected = frame.loc[
        mask
    ]

    rest = frame.loc[
        ~mask
    ]

    selected_stats = _basic_stats(
        selected
    )

    rest_stats = _basic_stats(
        rest
    )

    total_n = len(
        frame
    )

    selected_n = len(
        selected
    )

    rest_n = len(
        rest
    )

    if (
        total_n
        > 0
    ):

        coverage_pct = (
            selected_n
            /
            total_n
            *
            100.0
        )

    else:

        coverage_pct = (
            np.nan
        )

    return {

        "total_n": (
            total_n
        ),

        "selected_n": (
            selected_n
        ),

        "rest_n": (
            rest_n
        ),

        "coverage_pct": (
            coverage_pct
        ),

        "selected_net5": (
            selected_stats[
                "net5"
            ]
        ),

        "selected_net10": (
            selected_stats[
                "net10"
            ]
        ),

        "selected_net20": (
            selected_stats[
                "net20"
            ]
        ),

        "rest_net5": (
            rest_stats[
                "net5"
            ]
        ),

        "rest_net10": (
            rest_stats[
                "net10"
            ]
        ),

        "rest_net20": (
            rest_stats[
                "net20"
            ]
        ),

        "spread5": _difference(
            selected_stats[
                "net5"
            ],
            rest_stats[
                "net5"
            ],
        ),

        "spread10": _difference(
            selected_stats[
                "net10"
            ],
            rest_stats[
                "net10"
            ],
        ),

        "spread20": _difference(
            selected_stats[
                "net20"
            ],
            rest_stats[
                "net20"
            ],
        ),

        "selected_pos20": (
            selected_stats[
                "pos20"
            ]
        ),

        "selected_1r": (
            selected_stats[
                "one_r"
            ]
        ),
    }


# =============================================================================
# Confidence benchmark
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
    )

    values = (
        values
        .dropna()
    )

    if (
        len(
            values
        )
        < 3
    ):

        return np.nan

    correlation = values.corr(
        method="spearman"
    )

    matrix = correlation.to_numpy(
        dtype=np.float64
    )

    if (
        matrix.shape
        != (
            2,
            2,
        )
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


# =============================================================================
# Blocks
# =============================================================================

def _build_blocks(
    dates: list[
        str
    ],
    block_days: int,
    max_blocks: int,
) -> list[
    list[
        str
    ]
]:

    if (
        block_days
        <= 0
    ):

        raise ValueError(
            "--block-days must be > 0"
        )

    if (
        max_blocks
        <= 0
    ):

        raise ValueError(
            "--max-blocks must be > 0"
        )

    needed = (
        block_days
        *
        max_blocks
    )

    if (
        len(
            dates
        )
        < needed
    ):

        raise RuntimeError(
            (
                f"Need at least {needed} complete dates "
                f"before cutoff; found {len(dates)}. "
                "Increase --bars or reduce --max-blocks."
            )
        )

    selected_dates = (
        dates[
            -needed:
        ]
    )

    blocks: list[
        list[
            str
        ]
    ] = []

    for start in range(
        0,
        needed,
        block_days,
    ):

        blocks.append(
            selected_dates[
                start:
                start
                + block_days
            ]
        )

    return blocks


# =============================================================================
# Direction
# =============================================================================

def _direction_stats(
    frame: pd.DataFrame,
    direction: str,
) -> dict[
    str,
    Any,
]:

    subset = frame.loc[
        _direction_mask(
            frame,
            direction,
        )
    ]

    return _selected_vs_rest(
        subset
    )


# =============================================================================
# Final gate
# =============================================================================

def _aggregate_verdict(
    block_frame: pd.DataFrame,
    pooled: dict[
        str,
        Any,
    ],
    bullish: dict[
        str,
        Any,
    ],
    bearish: dict[
        str,
        Any,
    ],
    min_selected: int,
    min_rest: int,
) -> tuple[
    str,
    dict[
        str,
        Any,
    ],
]:

    required_columns = {

        "selected_n",

        "rest_n",

        "spread5",

        "spread10",

        "spread20",
    }

    missing = (
        required_columns
        -
        set(
            block_frame.columns
        )
    )

    if missing:

        raise RuntimeError(
            (
                "Internal shadow-validation table "
                "is missing columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )
        )

    if block_frame.empty:

        return (
            "INSUFFICIENT",
            {},
        )

    selected_n = _to_numeric(
        block_frame[
            "selected_n"
        ]
    )

    rest_n = _to_numeric(
        block_frame[
            "rest_n"
        ]
    )

    eligible = block_frame.loc[
        (
            selected_n
            >= float(
                min_selected
            )
        )
        &
        (
            rest_n
            >= float(
                min_rest
            )
        )
    ].copy()

    eligible_blocks = len(
        eligible
    )

    if (
        eligible_blocks
        == 0
    ):

        return (
            "INSUFFICIENT",
            {
                "eligible_blocks": 0,
            },
        )

    spread5 = (
        _to_numeric(
            eligible[
                "spread5"
            ]
        )
        .dropna()
    )

    spread10 = (
        _to_numeric(
            eligible[
                "spread10"
            ]
        )
        .dropna()
    )

    spread20 = (
        _to_numeric(
            eligible[
                "spread20"
            ]
        )
        .dropna()
    )

    confirmed5 = int(
        (
            spread5
            > 0.0
        ).sum()
    )

    confirmed10 = int(
        (
            spread10
            > 0.0
        ).sum()
    )

    confirmed20 = int(
        (
            spread20
            > 0.0
        ).sum()
    )

    strong20 = int(
        (
            spread20
            >= 0.20
        ).sum()
    )

    confirm5_pct = (
        confirmed5
        /
        eligible_blocks
        *
        100.0
    )

    confirm10_pct = (
        confirmed10
        /
        eligible_blocks
        *
        100.0
    )

    confirm20_pct = (
        confirmed20
        /
        eligible_blocks
        *
        100.0
    )

    strong20_pct = (
        strong20
        /
        eligible_blocks
        *
        100.0
    )

    median_spread5 = _as_float(
        spread5.median()
    )

    median_spread10 = _as_float(
        spread10.median()
    )

    median_spread20 = _as_float(
        spread20.median()
    )

    pooled_spread20 = _as_float(
        pooled.get(
            "spread20",
            np.nan,
        )
    )

    bullish_spread20 = _as_float(
        bullish.get(
            "spread20",
            np.nan,
        )
    )

    bearish_spread20 = _as_float(
        bearish.get(
            "spread20",
            np.nan,
        )
    )

    severe_direction_reversal = False

    for (
        side,
        side_spread,
    ) in (
        (
            bullish,
            bullish_spread20,
        ),
        (
            bearish,
            bearish_spread20,
        ),
    ):

        side_selected = int(
            side.get(
                "selected_n",
                0,
            )
        )

        side_rest = int(
            side.get(
                "rest_n",
                0,
            )
        )

        if (
            side_selected
            >= 25
            and
            side_rest
            >= 40
            and
            np.isfinite(
                side_spread
            )
            and
            side_spread
            <= -0.20
        ):

            severe_direction_reversal = True

    # =========================================================================
    # Gate
    # =========================================================================

    if (
        eligible_blocks
        >= 8
        and
        confirm20_pct
        >= 70.0
        and
        strong20_pct
        >= 60.0
        and
        median_spread20
        >= 0.20
        and
        pooled_spread20
        >= 0.20
        and
        not severe_direction_reversal
    ):

        verdict = (
            "SHADOW_GATE_CANDIDATE"
        )

    elif (
        eligible_blocks
        >= 6
        and
        confirm20_pct
        >= 70.0
        and
        median_spread20
        > 0.0
        and
        pooled_spread20
        > 0.0
        and
        not severe_direction_reversal
    ):

        verdict = (
            "SHADOW_BONUS_CANDIDATE"
        )

    else:

        verdict = (
            "UNSTABLE"
        )

    details = {

        "eligible_blocks": (
            eligible_blocks
        ),

        "confirmed5": (
            confirmed5
        ),

        "confirmed10": (
            confirmed10
        ),

        "confirmed20": (
            confirmed20
        ),

        "strong20": (
            strong20
        ),

        "confirm5_pct": (
            confirm5_pct
        ),

        "confirm10_pct": (
            confirm10_pct
        ),

        "confirm20_pct": (
            confirm20_pct
        ),

        "strong20_pct": (
            strong20_pct
        ),

        "median_spread5": (
            median_spread5
        ),

        "median_spread10": (
            median_spread10
        ),

        "median_spread20": (
            median_spread20
        ),

        "pooled_spread20": (
            pooled_spread20
        ),

        "bull_spread20": (
            bullish_spread20
        ),

        "bear_spread20": (
            bearish_spread20
        ),

        "severe_direction_reversal": (
            severe_direction_reversal
        ),
    }

    return (
        verdict,
        details,
    )


# =============================================================================
# Main
# =============================================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "PulseViper Confidence v2.1 "
            "frozen moderate-impulse shadow validator"
        )
    )

    parser.add_argument(
        "--bars",
        type=int,
        default=450000,
    )

    parser.add_argument(
        "--symbol",
        type=str,
        default="XAUUSDm",
    )

    parser.add_argument(
        "--cutoff-date",
        type=str,
        default="2026-02-27",
    )

    parser.add_argument(
        "--block-days",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--max-blocks",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--min-selected-events",
        type=int,
        default=12,
    )

    parser.add_argument(
        "--min-rest-events",
        type=int,
        default=20,
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
        args.min_selected_events
        <= 0
    ):

        raise ValueError(
            "--min-selected-events must be > 0"
        )

    if (
        args.min_rest_events
        <= 0
    ):

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
        "PulseViper Confidence v2.1 "
        "Shadow Moderate-Impulse Validation"
    )

    print(
        f"Project root        : "
        f"{PROJECT_ROOT}"
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
        f"Block size          : "
        f"{args.block_days} complete days"
    )

    print(
        f"Maximum blocks      : "
        f"{args.max_blocks}"
    )

    print(
        (
            "Frozen impulse band : "
            f"{IMPULSE_LOW:.2f} "
            "<= impulse <= "
            f"{IMPULSE_HIGH:.2f}"
        )
    )

    print(
        "Threshold optimization: DISABLED"
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

    if not eligible_dates:

        raise RuntimeError(
            (
                "No complete dates exist before cutoff. "
                "Increase --bars."
            )
        )

    blocks = _build_blocks(
        dates=eligible_dates,
        block_days=args.block_days,
        max_blocks=args.max_blocks,
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

    historical = events.loc[
        events[
            "date_label"
        ].isin(
            eligible_dates
        )
    ].copy()

    # =========================================================================
    # Universe
    # =========================================================================

    _section(
        "OLDER UNTOUCHED CONFIRMATION UNIVERSE"
    )

    print(
        (
            "Complete dates before cutoff : "
            f"{len(eligible_dates)}"
        )
    )

    print(
        (
            "Earliest eligible date       : "
            f"{eligible_dates[0]}"
        )
    )

    print(
        (
            "Latest eligible date         : "
            f"{eligible_dates[-1]}"
        )
    )

    print(
        (
            "Trade-ready events           : "
            f"{len(historical)}"
        )
    )

    print(
        (
            "Confirmation blocks          : "
            f"{len(blocks)}"
        )
    )

    # =========================================================================
    # Block evaluation
    # =========================================================================

    block_records: list[
        dict[
            str,
            Any,
        ]
    ] = []

    pooled_parts: list[
        pd.DataFrame
    ] = []

    for (
        block_number,
        block_dates,
    ) in enumerate(
        blocks,
        start=1,
    ):

        block = events.loc[
            events[
                "date_label"
            ].isin(
                block_dates
            )
        ].copy()

        pooled_parts.append(
            block
        )

        stats = _selected_vs_rest(
            block
        )

        moderate = block.loc[
            _moderate_mask(
                block
            )
        ]

        confidence_table = (
            _confidence_table(
                moderate
            )
        )

        block_records.append(
            {

                "block": (
                    block_number
                ),

                "start": (
                    block_dates[
                        0
                    ]
                ),

                "end": (
                    block_dates[
                        -1
                    ]
                ),

                "total_n": (
                    stats[
                        "total_n"
                    ]
                ),

                "selected_n": (
                    stats[
                        "selected_n"
                    ]
                ),

                # =============================================================
                # IMPORTANT FIX
                #
                # Previous version forgot this column while _aggregate_verdict
                # requires it.
                # =============================================================

                "rest_n": (
                    stats[
                        "rest_n"
                    ]
                ),

                "coverage_pct": round(
                    _as_float(
                        stats[
                            "coverage_pct"
                        ]
                    ),
                    1,
                ),

                "spread5": round(
                    _as_float(
                        stats[
                            "spread5"
                        ]
                    ),
                    3,
                ),

                "spread10": round(
                    _as_float(
                        stats[
                            "spread10"
                        ]
                    ),
                    3,
                ),

                "spread20": round(
                    _as_float(
                        stats[
                            "spread20"
                        ]
                    ),
                    3,
                ),

                "selected_net20": round(
                    _as_float(
                        stats[
                            "selected_net20"
                        ]
                    ),
                    3,
                ),

                "selected_pos20": round(
                    _as_float(
                        stats[
                            "selected_pos20"
                        ]
                    ),
                    1,
                ),

                "selected_1r": round(
                    _as_float(
                        stats[
                            "selected_1r"
                        ]
                    ),
                    1,
                ),

                "conf_rho_inside": round(
                    _spearman_confidence_net20(
                        moderate
                    ),
                    3,
                ),

                "conf_monotonic_inside": (
                    _confidence_monotonicity(
                        confidence_table
                    )
                ),
            }
        )

    block_frame = pd.DataFrame(
        block_records
    )

    _section(
        "BLOCK-BY-BLOCK FROZEN IMPULSE RESULT"
    )

    print(
        block_frame.to_string(
            index=False
        )
    )

    # =========================================================================
    # Pooled
    # =========================================================================

    pooled = (
        pd.concat(
            pooled_parts,
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

    pooled_stats = _selected_vs_rest(
        pooled
    )

    bullish_stats = _direction_stats(
        pooled,
        "BULLISH",
    )

    bearish_stats = _direction_stats(
        pooled,
        "BEARISH",
    )

    # =========================================================================
    # Pooled output
    # =========================================================================

    _section(
        "POOLED UNIQUE CONFIRMATION RESULT"
    )

    pooled_rows: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for (
        scope,
        stats,
    ) in (
        (
            "ALL",
            pooled_stats,
        ),
        (
            "BULLISH",
            bullish_stats,
        ),
        (
            "BEARISH",
            bearish_stats,
        ),
    ):

        pooled_rows.append(
            {

                "scope": (
                    scope
                ),

                "total_n": (
                    stats[
                        "total_n"
                    ]
                ),

                "selected_n": (
                    stats[
                        "selected_n"
                    ]
                ),

                "rest_n": (
                    stats[
                        "rest_n"
                    ]
                ),

                "coverage_pct": round(
                    _as_float(
                        stats[
                            "coverage_pct"
                        ]
                    ),
                    1,
                ),

                "spread5": round(
                    _as_float(
                        stats[
                            "spread5"
                        ]
                    ),
                    3,
                ),

                "spread10": round(
                    _as_float(
                        stats[
                            "spread10"
                        ]
                    ),
                    3,
                ),

                "spread20": round(
                    _as_float(
                        stats[
                            "spread20"
                        ]
                    ),
                    3,
                ),

                "selected_net20": round(
                    _as_float(
                        stats[
                            "selected_net20"
                        ]
                    ),
                    3,
                ),

                "selected_pos20": round(
                    _as_float(
                        stats[
                            "selected_pos20"
                        ]
                    ),
                    1,
                ),

                "selected_1r": round(
                    _as_float(
                        stats[
                            "selected_1r"
                        ]
                    ),
                    1,
                ),
            }
        )

    pooled_table = pd.DataFrame(
        pooled_rows
    )

    print(
        pooled_table.to_string(
            index=False
        )
    )

    # =========================================================================
    # Current Confidence
    # =========================================================================

    _section(
        "CURRENT CONFIDENCE v2 "
        "INSIDE MODERATE-IMPULSE BAND"
    )

    moderate_pooled = pooled.loc[
        _moderate_mask(
            pooled
        )
    ]

    confidence_table = (
        _confidence_table(
            moderate_pooled
        )
    )

    if confidence_table.empty:

        print(
            "No Confidence data inside impulse band."
        )

    else:

        print(
            confidence_table.to_string(
                index=False
            )
        )

        print()

        print(
            (
                "Monotonicity inside band : "
                f"{_confidence_monotonicity(confidence_table)}"
            )
        )

        print(
            (
                "Spearman rho conf/net20  : "
                f"{_fmt(_spearman_confidence_net20(moderate_pooled))}"
            )
        )

    # =========================================================================
    # Final verdict
    # =========================================================================

    (
        verdict,
        details,
    ) = _aggregate_verdict(
        block_frame=block_frame,
        pooled=pooled_stats,
        bullish=bullish_stats,
        bearish=bearish_stats,
        min_selected=args.min_selected_events,
        min_rest=args.min_rest_events,
    )

    _section(
        "SHADOW CONFIDENCE v2.1 GATE"
    )

    if details:

        eligible = int(
            details[
                "eligible_blocks"
            ]
        )

        print(
            (
                "Eligible blocks              : "
                f"{eligible}"
            )
        )

        print(
            (
                "5-bar positive-spread blocks : "
                f"{details['confirmed5']}/{eligible} "
                f"({_fmt(details['confirm5_pct'], 1)}%)"
            )
        )

        print(
            (
                "10-bar positive-spread blocks: "
                f"{details['confirmed10']}/{eligible} "
                f"({_fmt(details['confirm10_pct'], 1)}%)"
            )
        )

        print(
            (
                "20-bar positive-spread blocks: "
                f"{details['confirmed20']}/{eligible} "
                f"({_fmt(details['confirm20_pct'], 1)}%)"
            )
        )

        print(
            (
                "20-bar strong blocks >= .20 : "
                f"{details['strong20']}/{eligible} "
                f"({_fmt(details['strong20_pct'], 1)}%)"
            )
        )

        print()

        print(
            (
                "Median block spread 5        : "
                f"{_fmt(details['median_spread5'])}"
            )
        )

        print(
            (
                "Median block spread 10       : "
                f"{_fmt(details['median_spread10'])}"
            )
        )

        print(
            (
                "Median block spread 20       : "
                f"{_fmt(details['median_spread20'])}"
            )
        )

        print(
            (
                "Pooled spread 20             : "
                f"{_fmt(details['pooled_spread20'])}"
            )
        )

        print(
            (
                "Bullish pooled spread 20     : "
                f"{_fmt(details['bull_spread20'])}"
            )
        )

        print(
            (
                "Bearish pooled spread 20     : "
                f"{_fmt(details['bear_spread20'])}"
            )
        )

        print(
            (
                "Severe direction reversal    : "
                f"{details['severe_direction_reversal']}"
            )
        )

    print()

    print(
        f"FINAL VERDICT: "
        f"{verdict}"
    )

    print()

    print(
        (
            "SHADOW_GATE_CANDIDATE = may proceed "
            "to non-live gate research."
        )
    )

    print(
        (
            "SHADOW_BONUS_CANDIDATE = may proceed "
            "only as a shadow bonus/flag."
        )
    )

    print(
        (
            "UNSTABLE = do not promote this static "
            "hypothesis to Confidence v2.1."
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
            "Shadow moderate-impulse confirmation "
            "validator completed successfully."
        )
    )


if __name__ == "__main__":

    main()