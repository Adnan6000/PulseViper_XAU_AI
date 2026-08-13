"""
===============================================================================
Module      : shadow_weight_forward_operation.py
Project     : PulseViper XAU AI
Version     : 1.0.1
Purpose     : Forward-Only Shadow Validation of RWEI Opportunity Weights
===============================================================================

Flow
----
MT5 closed M1 history
    ↓
Frozen production + causal research pipeline
    ↓
Causal market regime
    ↓
Research Opportunity Weight Engine
    ↓
Forward-only boundary
    ↓
ONLY candidates after previous anchor
    ↓
Forward Weight Ledger
    ↓
5 / 10 / 20-bar paper outcomes
    ↓
A / B / C / D tier performance

Critical anti-overfitting rule
------------------------------
FIRST RUN:
    - set forward anchor to latest CLOSED candle
    - capture ZERO historical candidates

SUBSEQUENT RUNS:
    - capture only candidate signal_time > previous anchor
    - evaluate using later CLOSED candles
    - advance anchor only after successful ledger persistence

Safety
------
- MT5 data read only
- no order_send
- no positions
- no lot sizing
- no SL / TP
- no BE / trailing
- no production trade_ready modification
- RWEI remains shadow evidence only
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# =============================================================================
# Existing project components
# =============================================================================

fetcher: Any = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher


research_pipeline: Any = importlib.import_module(
    "02_AI.Shadow.research_intelligence_pipeline"
).research_intelligence_pipeline


weight_module: Any = importlib.import_module(
    "02_AI.Shadow.research_opportunity_weight_engine"
)

weight_engine: Any = (
    weight_module.research_opportunity_weight_engine
)


forward_module: Any = importlib.import_module(
    "02_AI.Shadow.research_weight_forward_ledger"
)

ResearchWeightForwardLedger: Any = (
    forward_module.ResearchWeightForwardLedger
)

DEFAULT_FORWARD_WEIGHT_LEDGER_PATH: Path = (
    forward_module.DEFAULT_FORWARD_WEIGHT_LEDGER_PATH
)


paper_operation: Any = importlib.import_module(
    "04_Testing.shadow_paper_operation"
)

attach_regime: Any = (
    paper_operation.attach_regime
)


# =============================================================================
# Display helpers
# =============================================================================

def section(
    title: str,
) -> None:

    print()

    print(
        "=" * 118
    )

    print(
        title
    )

    print(
        "=" * 118
    )


def show(
    frame: pd.DataFrame,
    empty_message: str,
) -> None:

    if frame.empty:
        print(
            empty_message
        )
        return

    print(
        frame.to_string(
            index=False
        )
    )


def normalized_time_series(
    frame: pd.DataFrame,
) -> pd.Series:

    return pd.to_datetime(
        frame[
            "time"
        ],
        errors="coerce",
        utc=True,
    ).dt.tz_convert(
        None
    )


# =============================================================================
# Current weighted-candidate distribution
# =============================================================================

def current_weight_distribution(
    weighted: pd.DataFrame,
) -> pd.DataFrame:

    active = weighted.loc[
        pd.to_numeric(
            weighted[
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
    ].copy()

    total = len(
        active
    )

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

        frame = active.loc[
            active[
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

        scores = pd.to_numeric(
            frame[
                "rwei_score"
            ],
            errors="coerce",
        ).dropna()

        rows.append(
            {
                "tier": tier,

                "current_candidates": len(
                    frame
                ),

                "pct_of_current_candidates": (
                    round(
                        (
                            len(
                                frame
                            )
                            /
                            total
                        )
                        *
                        100.0,
                        3,
                    )
                    if total
                    else 0.0
                ),

                "score_median": (
                    round(
                        float(
                            scores.median()
                        ),
                        3,
                    )
                    if not scores.empty
                    else np.nan
                ),
            }
        )

    return pd.DataFrame(
        rows
    )


# =============================================================================
# Generic metric helpers
# =============================================================================

def metric_median(
    frame: pd.DataFrame,
    column: str,
) -> float:

    if (
        frame.empty
        or
        column not in frame.columns
    ):
        return np.nan

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


def positive20_pct(
    frame: pd.DataFrame,
) -> float:

    if (
        frame.empty
        or
        "positive_20"
        not in frame.columns
    ):
        return np.nan

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


# =============================================================================
# Forward direction × tier dashboard
# =============================================================================

def direction_tier_dashboard(
    ledger: pd.DataFrame,
) -> pd.DataFrame:

    columns = [
        "direction",
        "tier",
        "n",
        "net5_med",
        "net10_med",
        "net20_med",
        "positive20_pct",
        "mfe20_med",
        "mae20_med",
    ]

    if ledger.empty:
        return pd.DataFrame(
            columns=columns
        )

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

    for direction in (
        "LONG",
        "SHORT",
    ):

        for tier in (
            "A",
            "B",
            "C",
            "D",
        ):

            frame = matured.loc[
                matured[
                    "direction"
                ]
                .astype(
                    str
                )
                .str
                .upper()
                .eq(
                    direction
                )
                &
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
                    "direction": direction,

                    "tier": tier,

                    "n": len(
                        frame
                    ),

                    "net5_med": metric_median(
                        frame,
                        "net_5",
                    ),

                    "net10_med": metric_median(
                        frame,
                        "net_10",
                    ),

                    "net20_med": metric_median(
                        frame,
                        "net_20",
                    ),

                    "positive20_pct": (
                        positive20_pct(
                            frame
                        )
                    ),

                    "mfe20_med": metric_median(
                        frame,
                        "mfe_20",
                    ),

                    "mae20_med": metric_median(
                        frame,
                        "mae_20",
                    ),
                }
            )

    return pd.DataFrame(
        rows,
        columns=columns,
    )


# =============================================================================
# Forward maturity dashboard
# =============================================================================

def forward_status_dashboard(
    ledger: pd.DataFrame,
) -> pd.DataFrame:

    statuses = (
        "OPEN",
        "PARTIAL_5",
        "PARTIAL_10",
        "MATURED_20",
    )

    if ledger.empty:

        return pd.DataFrame(
            {
                "status": list(
                    statuses
                ),

                "count": [
                    0,
                ] * len(
                    statuses
                ),
            }
        )

    counts = (
        ledger[
            "status"
        ]
        .astype(
            str
        )
        .value_counts()
    )

    return pd.DataFrame(
        {
            "status": list(
                statuses
            ),

            "count": [
                int(
                    counts.get(
                        status,
                        0,
                    )
                )
                for status in statuses
            ],
        }
    )


# =============================================================================
# Latest events
# =============================================================================

def latest_forward_events(
    ledger: pd.DataFrame,
    limit: int,
) -> pd.DataFrame:

    if ledger.empty:
        return ledger.copy()

    preferred = [
        "signal_time",

        "direction",

        "rwei_tier",
        "rwei_score",

        "confidence_score",
        "regime_state",

        "lei_entry_family",
        "lei_reference_source",
        "lei_confirmation_type",
        "lei_distance_atr",

        "entry_close",

        "status",
        "bars_available",

        "net_5",
        "net_10",
        "net_20",

        "mfe_20",
        "mae_20",

        "rwei_components",
    ]

    columns = [
        column
        for column in preferred
        if column in ledger.columns
    ]

    result = (
        ledger
        .sort_values(
            "signal_time"
        )
        .tail(
            limit
        )
        .loc[
            :,
            columns,
        ]
        .copy()
    )

    for column in (
        "rwei_score",
        "confidence_score",
        "lei_distance_atr",
        "entry_close",

        "net_5",
        "net_10",
        "net_20",

        "mfe_20",
        "mae_20",
    ):

        if column not in result.columns:
            continue

        result[
            column
        ] = (
            pd.to_numeric(
                result[
                    column
                ],
                errors="coerce",
            )
            .round(
                3
            )
        )

    return result


# =============================================================================
# Main
# =============================================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "PulseViper forward-only "
            "RWEI shadow validation v1.0.1"
        )
    )

    parser.add_argument(
        "--symbol",
        default="XAUUSDm",
    )

    parser.add_argument(
        "--bars",
        type=int,
        default=6000,
    )

    parser.add_argument(
        "--ledger",
        type=str,
        default=str(
            DEFAULT_FORWARD_WEIGHT_LEDGER_PATH
        ),
    )

    parser.add_argument(
        "--latest",
        type=int,
        default=15,
    )

    args = parser.parse_args()

    if args.bars < 500:
        raise ValueError(
            "--bars must be >= 500"
        )

    if args.latest < 1:
        raise ValueError(
            "--latest must be >= 1"
        )

    ledger_path = Path(
        args.ledger
    )

    store = ResearchWeightForwardLedger(
        ledger_path
    )

    # =========================================================================
    # Header
    # =========================================================================

    section(
        "PulseViper XAU AI — "
        "FORWARD-ONLY RWEI SHADOW VALIDATION v1.0.1"
    )

    print(
        f"Requested symbol       : {args.symbol}"
    )

    print(
        f"Requested bars         : {args.bars}"
    )

    print(
        f"Forward ledger         : {ledger_path}"
    )

    print(
        f"Forward anchor         : {store.anchor_path}"
    )

    print(
        "MT5                    : READ ONLY"
    )

    print(
        "Trading/orders         : DISABLED"
    )

    print(
        "Position modification  : DISABLED"
    )

    print(
        "Production trade_ready : FROZEN"
    )

    print(
        "RWEI                   : SHADOW EVIDENCE ONLY"
    )

    print(
        "Historical backfill    : FORBIDDEN"
    )

    # =========================================================================
    # Fetch MT5 M1 data
    # =========================================================================

    print(
        "\nFetching MT5 M1 history..."
    )

    raw = fetcher.fetch(
        symbol=args.symbol,
        bars=args.bars,
    )

    if len(
        raw
    ) < 2:

        raise RuntimeError(
            "Need at least two MT5 candles"
        )

    forming_time = pd.to_datetime(
        raw.iloc[
            -1
        ][
            "time"
        ],
        errors="coerce",
    )

    closed = (
        raw
        .iloc[
            :-1
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    closed_times = normalized_time_series(
        closed
    )

    valid_times = (
        closed_times
        .dropna()
    )

    if valid_times.empty:
        raise RuntimeError(
            "No valid closed-bar timestamps"
        )

    earliest_closed = pd.Timestamp(
        valid_times.iloc[
            0
        ]
    )

    latest_closed = pd.Timestamp(
        valid_times.iloc[
            -1
        ]
    )

    resolved_symbol = (
        str(
            getattr(
                fetcher,
                "last_resolved_symbol",
                "",
            )
        )
        or
        args.symbol
    )

    print(
        f"Fetched bars           : {len(raw)}"
    )

    print(
        f"Closed bars            : {len(closed)}"
    )

    print(
        f"Resolved symbol        : {resolved_symbol}"
    )

    print(
        f"Earliest closed        : {earliest_closed}"
    )

    print(
        f"Latest closed          : {latest_closed}"
    )

    print(
        f"Excluded forming bar   : {forming_time}"
    )

    # =========================================================================
    # Frozen production + causal research
    # =========================================================================

    print(
        "\nRunning causal research chain..."
    )

    enriched = research_pipeline.generate(
        closed
    )

    print(
        "Attaching causal regime..."
    )

    enriched = attach_regime(
        closed,
        enriched,
    )

    print(
        "Attaching shadow opportunity weights..."
    )

    weighted = weight_engine.generate(
        enriched
    )

    # =========================================================================
    # Coverage invariant
    # =========================================================================

    candidate_count = int(
        pd.to_numeric(
            weighted[
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
        .sum()
    )

    weighted_count = int(
        pd.to_numeric(
            weighted[
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
        .sum()
    )

    if candidate_count != weighted_count:

        raise RuntimeError(
            "RWEI candidate coverage mismatch"
        )

    # =========================================================================
    # Persistent state
    # =========================================================================

    existing = store.load()

    previous_anchor = (
        store.load_anchor()
    )

    # =========================================================================
    # First run — establish strict boundary
    # =========================================================================

    if previous_anchor is None:

        if not existing.empty:

            raise RuntimeError(
                "Forward ledger contains events but "
                "anchor is missing. Refusing to infer "
                "a historical validation boundary."
            )

        initialized_anchor = (
            store.save_anchor(
                latest_closed
            )
        )

        store.save(
            existing
        )

        section(
            "FORWARD BOUNDARY INITIALIZED"
        )

        print(
            f"Anchor set to           : {initialized_anchor}"
        )

        print(
            "Historical captures     : 0"
        )

        print(
            "Forward ledger events   : 0"
        )

        print(
            (
                "Meaning                 : candidates at "
                "or before this candle are excluded from "
                "forward validation."
            )
        )

        section(
            "CURRENT RWEI DISTRIBUTION — OBSERVATION ONLY"
        )

        show(
            current_weight_distribution(
                weighted
            ),
            "No weighted candidates.",
        )

        section(
            "NEXT RUN"
        )

        print(
            (
                "Only candidates with signal_time > "
                f"{initialized_anchor} are eligible."
            )
        )

        print(
            (
                "No production decision or execution "
                "logic has changed."
            )
        )

        return

    # =========================================================================
    # Anchor integrity
    # =========================================================================

    if latest_closed < previous_anchor:

        raise RuntimeError(
            "Latest MT5 closed candle is older than "
            "stored forward anchor. Boundary cannot "
            "move backward."
        )

    if previous_anchor < earliest_closed:

        raise RuntimeError(
            "Stored forward anchor is older than "
            "earliest fetched candle. Possible "
            "observation gap. Increase --bars."
        )

    # =========================================================================
    # Strictly forward capture
    # =========================================================================

    incoming = store.capture_after_anchor(
        frame=weighted,
        anchor_time=previous_anchor,
        requested_symbol=args.symbol,
        resolved_symbol=resolved_symbol,
        timeframe="M1",
    )

    (
        ledger,
        new_count,
    ) = store.merge(
        existing=existing,
        incoming=incoming,
    )

    # =========================================================================
    # Future outcome evaluation
    # =========================================================================

    ledger = store.evaluate(
        ledger=ledger,
        market=weighted,
    )

    # =========================================================================
    # Persist ledger before advancing anchor
    # =========================================================================

    store.save(
        ledger
    )

    current_anchor = (
        store.save_anchor(
            latest_closed
        )
    )

    # =========================================================================
    # Counts
    # =========================================================================

    matured_count = int(
        ledger[
            "status"
        ]
        .astype(
            str
        )
        .eq(
            "MATURED_20"
        )
        .sum()
    )

    # v1.0.1 FIX:
    # Use .ne() rather than bitwise inversion of an integer sum.
    open_partial_count = int(
        ledger[
            "status"
        ]
        .astype(
            str
        )
        .ne(
            "MATURED_20"
        )
        .sum()
    )

    # =========================================================================
    # Run status
    # =========================================================================

    section(
        "FORWARD RUN STATUS"
    )

    print(
        f"Previous anchor         : {previous_anchor}"
    )

    print(
        f"Current anchor          : {current_anchor}"
    )

    print(
        f"New weighted candidates : {new_count}"
    )

    print(
        f"Forward ledger total    : {len(ledger)}"
    )

    print(
        f"Matured 20              : {matured_count}"
    )

    print(
        f"Open / partial          : {open_partial_count}"
    )

    # =========================================================================
    # Distribution
    # =========================================================================

    section(
        "CURRENT RWEI DISTRIBUTION — OBSERVATION ONLY"
    )

    show(
        current_weight_distribution(
            weighted
        ),
        "No current weighted candidates.",
    )

    # =========================================================================
    # Maturity
    # =========================================================================

    section(
        "FORWARD LEDGER MATURITY"
    )

    show(
        forward_status_dashboard(
            ledger
        ),
        "Forward ledger empty.",
    )

    # =========================================================================
    # Tier performance
    # =========================================================================

    section(
        "FORWARD PERFORMANCE — RWEI TIER"
    )

    show(
        store.tier_dashboard(
            ledger
        ),
        "No matured forward events yet.",
    )

    # =========================================================================
    # Direction × tier
    # =========================================================================

    section(
        "FORWARD PERFORMANCE — DIRECTION × RWEI TIER"
    )

    show(
        direction_tier_dashboard(
            ledger
        ),
        "No matured direction-tier evidence yet.",
    )

    # =========================================================================
    # Latest events
    # =========================================================================

    section(
        "LATEST FORWARD WEIGHTED EVENTS"
    )

    show(
        latest_forward_events(
            ledger,
            args.latest,
        ),
        (
            "No forward candidates captured since "
            "the previous validation anchor."
        ),
    )

    # =========================================================================
    # Interpretation
    # =========================================================================

    section(
        "INTERPRETATION"
    )

    print(
        (
            "- Every recorded event occurred after the "
            "stored forward-validation boundary."
        )
    )

    print(
        (
            "- A/B/C/D are quality evidence tiers, "
            "not trade permissions."
        )
    )

    print(
        (
            "- Zero new candidates is a valid result; "
            "the engine must not manufacture trades."
        )
    )

    print(
        (
            "- We need genuinely forward matured events "
            "before judging RWEI generalization."
        )
    )

    print(
        (
            "- Production trade_ready, execution and "
            "risk remain unchanged."
        )
    )


if __name__ == "__main__":
    main()