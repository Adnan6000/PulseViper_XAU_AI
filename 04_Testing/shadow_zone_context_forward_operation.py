"""
===============================================================================
Module      : shadow_zone_context_forward_operation.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Forward-Only Institutional Zone Hypothesis Validation Operation
===============================================================================

Flow
----
MT5 CLOSED M1 history
        ↓
Frozen production + causal research pipeline
        ↓
Causal regime metadata
        ↓
Institutional Zone causal context
        ↓
Strict previous forward anchor
        ↓
Causal episode-start detection
        ↓
ONLY episode starts after previous anchor
        ↓
Freeze Z1-Z6 signal-time hypotheses
        ↓
Future-only 5 / 10 / 20-bar outcomes
        ↓
Forward hypothesis dashboard

Critical anti-backfill rule
---------------------------
FIRST RUN
    latest CLOSED candle becomes anchor
    ZERO historical episodes captured

SUBSEQUENT RUNS
    capture only causal episode starts with:
        signal_time > previous anchor

    scan completes
        ↓
    merge/evaluate
        ↓
    ledger persists successfully
        ↓
    ONLY THEN anchor advances

Safety
------
- MT5 READ ONLY
- no order_send
- no orders
- no position modification
- no lot sizing
- no SL / TP
- no BE / trailing
- no risk execution
- no production trade_ready changes
- no LEI changes
- no RWEI changes
- no historical backfill
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
# Project path
# =============================================================================

PROJECT_ROOT = Path(
    __file__
).resolve().parents[
    1
]

if str(
    PROJECT_ROOT
) not in sys.path:

    sys.path.insert(
        0,
        str(
            PROJECT_ROOT
        ),
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


forward_module: Any = importlib.import_module(
    "02_AI.Shadow.research_zone_context_forward_ledger"
)

ResearchZoneContextForwardLedger: Any = (
    forward_module.ResearchZoneContextForwardLedger
)

DEFAULT_FORWARD_ZONE_CONTEXT_LEDGER_PATH: Path = (
    forward_module.DEFAULT_FORWARD_ZONE_CONTEXT_LEDGER_PATH
)


paper_operation: Any = importlib.import_module(
    "04_Testing.shadow_paper_operation"
)

attach_regime: Any = (
    paper_operation.attach_regime
)


# =============================================================================
# Display
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


# =============================================================================
# Time helpers
# =============================================================================


def normalized_time_series(
    frame: pd.DataFrame,
) -> pd.Series:

    return (
        pd.to_datetime(
            frame[
                "time"
            ],
            errors="coerce",
            utc=True,
        )
        .dt
        .tz_convert(
            None
        )
    )


# =============================================================================
# Metrics
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
        "positive_20" not in frame.columns
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
# Status dashboard
# =============================================================================


def status_dashboard(
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
                for status
                in statuses
            ],
        }
    )


# =============================================================================
# Direction dashboard
# =============================================================================


def direction_dashboard(
    ledger: pd.DataFrame,
) -> pd.DataFrame:

    columns = [
        "direction",
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
        ]

        rows.append(
            {
                "direction": (
                    direction
                ),

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
# Latest forward events
# =============================================================================


def latest_events(
    ledger: pd.DataFrame,
    limit: int,
) -> pd.DataFrame:

    if ledger.empty:

        return ledger.copy()

    preferred = [
        "signal_time",

        "direction",

        "aligned_zone_state",
        "aligned_location",
        "aligned_distance_atr",

        "opposing_zone_state",
        "opposing_location",
        "opposing_distance_atr",

        "zone_relation",

        "hypothesis_tags",

        "confidence_score",
        "regime_state",

        "entry_close",

        "status",
        "bars_available",

        "net_5",
        "net_10",
        "net_20",

        "mfe_20",
        "mae_20",

        "positive_20",
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
        "aligned_distance_atr",
        "opposing_distance_atr",

        "confidence_score",
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

    return result.reset_index(
        drop=True
    )


# =============================================================================
# Unresolved evidence coverage guard
# =============================================================================


def unresolved_before_history(
    ledger: pd.DataFrame,
    earliest_closed: pd.Timestamp,
) -> pd.DataFrame:
    """
    An OPEN / PARTIAL event older than current fetched history cannot be
    correctly matured from this window.

    Refuse to advance the forward boundary in that case.
    """

    if ledger.empty:

        return ledger.copy()

    times = pd.to_datetime(
        ledger[
            "signal_time"
        ],
        errors="coerce",
    )

    matured = (
        ledger[
            "status"
        ]
        .astype(
            str
        )
        .eq(
            "MATURED_20"
        )
    )

    mask = (
        ~matured
        &
        times.notna()
        &
        times.lt(
            earliest_closed
        )
    )

    return ledger.loc[
        mask
    ].copy()


# =============================================================================
# Main
# =============================================================================


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "PulseViper forward-only Institutional "
            "Zone hypothesis validation v1.0"
        )
    )

    parser.add_argument(
        "--symbol",
        type=str,
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
            DEFAULT_FORWARD_ZONE_CONTEXT_LEDGER_PATH
        ),
    )

    parser.add_argument(
        "--episode-gap",
        type=int,
        default=3,
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

    if args.episode_gap < 1:

        raise ValueError(
            "--episode-gap must be >= 1"
        )

    if args.latest < 1:

        raise ValueError(
            "--latest must be >= 1"
        )

    ledger_path = Path(
        args.ledger
    )

    store = (
        ResearchZoneContextForwardLedger(
            ledger_path
        )
    )

    # =========================================================================
    # Header
    # =========================================================================

    section(
        "PulseViper XAU AI — "
        "FORWARD-ONLY INSTITUTIONAL ZONE VALIDATION v1.0"
    )

    print(
        f"Requested symbol       : {args.symbol}"
    )

    print(
        f"Requested bars         : {args.bars}"
    )

    print(
        f"Episode max gap        : {args.episode_gap} min"
    )

    print(
        f"Forward ledger         : {ledger_path}"
    )

    print(
        f"Forward anchor         : {store.anchor_path}"
    )

    print(
        (
            "Hypothesis policy      : "
            f"{store.POLICY}"
        )
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
        "LEI / RWEI             : UNCHANGED"
    )

    print(
        "Historical backfill    : FORBIDDEN"
    )

    # =========================================================================
    # Fetch MT5
    # =========================================================================

    section(
        "FETCH CLOSED MT5 M1 HISTORY"
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
        .sort_values()
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
    # Causal research replay
    # =========================================================================

    section(
        "RUN CAUSAL RESEARCH + ZONE CONTEXT"
    )

    print(
        (
            "Running frozen production + causal "
            "research pipeline..."
        )
    )

    enriched = research_pipeline.generate(
        closed
    )

    print(
        "Attaching causal regime metadata..."
    )

    enriched = attach_regime(
        closed,
        enriched,
    )

    required_runtime_columns = {
        "time",
        "close",

        "lei_candidate_flag",

        "izctx_live_safe",
        "izctx_version",
        "izctx_mode",

        "research_live_safe",
        "research_trade_ready_unchanged",
    }

    missing_runtime = (
        required_runtime_columns
        -
        set(
            enriched.columns
        )
    )

    if missing_runtime:

        raise RuntimeError(
            "Forward zone runtime missing columns: "
            +
            ", ".join(
                sorted(
                    missing_runtime
                )
            )
        )

    if not enriched.empty:

        print(
            (
                "Research pipeline       : "
                f"{enriched['research_pipeline_version'].iloc[-1]}"
            )
        )

        print(
            (
                "Zone context version    : "
                f"{enriched['izctx_version'].iloc[-1]}"
            )
        )

        print(
            (
                "Zone context mode       : "
                f"{enriched['izctx_mode'].iloc[-1]}"
            )
        )

    # =========================================================================
    # Load persistent forward state
    # =========================================================================

    section(
        "FORWARD VALIDATION BOUNDARY"
    )

    existing = store.load()

    previous_anchor = store.load_anchor()

    print(
        f"Existing ledger events : {len(existing)}"
    )

    print(
        f"Previous anchor        : {previous_anchor}"
    )

    # =========================================================================
    # First-run anchor
    # =========================================================================

    if previous_anchor is None:

        if not existing.empty:

            raise RuntimeError(
                "Forward zone ledger exists but anchor is missing. "
                "Refusing to establish a new boundary over existing evidence."
            )

        saved_anchor = store.save_anchor(
            latest_closed
        )

        print()
        print(
            "FIRST FORWARD RUN"
        )

        print(
            (
                "Forward anchor created  : "
                f"{saved_anchor}"
            )
        )

        print(
            "Historical capture       : 0"
        )

        print(
            "Historical backfill      : FORBIDDEN"
        )

        print(
            (
                "Next run will capture only genuine episode "
                "starts AFTER this anchor."
            )
        )

        print(
            (
                "Z1-Z6 historical evidence was NOT copied "
                "into the forward ledger."
            )
        )

        return

    # =========================================================================
    # Boundary sanity
    # =========================================================================

    if latest_closed < previous_anchor:

        raise RuntimeError(
            "Latest closed market candle is older than "
            "the stored forward anchor"
        )

    if earliest_closed > previous_anchor:

        raise RuntimeError(
            (
                "Fetched MT5 history does not reach the previous "
                f"anchor {previous_anchor}. Earliest available is "
                f"{earliest_closed}. Increase --bars before continuing."
            )
        )

    unresolved_old = unresolved_before_history(
        existing,
        earliest_closed,
    )

    if not unresolved_old.empty:

        oldest = pd.to_datetime(
            unresolved_old[
                "signal_time"
            ],
            errors="coerce",
        ).min()

        raise RuntimeError(
            (
                "Unresolved forward events are older than the "
                "current MT5 history window. Oldest unresolved event: "
                f"{oldest}. Increase --bars before continuing so "
                "future outcomes are not lost."
            )
        )

    # =========================================================================
    # Capture genuine post-anchor episode starts
    # =========================================================================

    section(
        "CAPTURE NEW FORWARD EPISODE STARTS"
    )

    incoming = store.capture_after_anchor(
        frame=enriched,
        anchor_time=previous_anchor,
        requested_symbol=args.symbol,
        resolved_symbol=resolved_symbol,
        timeframe="M1",
        max_gap_minutes=args.episode_gap,
    )

    combined, new_count = store.merge(
        existing,
        incoming,
    )

    print(
        f"Candidate episode starts after anchor : {len(incoming)}"
    )

    print(
        f"New unique forward events             : {new_count}"
    )

    # =========================================================================
    # Future-only evaluation
    # =========================================================================

    section(
        "EVALUATE FUTURE-ONLY OUTCOMES"
    )

    evaluated = store.evaluate(
        combined,
        closed,
    )

    # =========================================================================
    # Persist ledger FIRST
    # =========================================================================

    store.save(
        evaluated
    )

    print(
        f"Persisted forward events : {len(evaluated)}"
    )

    # =========================================================================
    # Advance anchor ONLY after successful persistence
    # =========================================================================

    new_anchor = store.save_anchor(
        latest_closed
    )

    print(
        f"Previous anchor          : {previous_anchor}"
    )

    print(
        f"Advanced anchor          : {new_anchor}"
    )

    # =========================================================================
    # Status
    # =========================================================================

    section(
        "FORWARD MATURITY STATUS"
    )

    show(
        status_dashboard(
            evaluated
        ),
        "No forward events.",
    )

    # =========================================================================
    # Z1-Z6 dashboard
    # =========================================================================

    section(
        "PRE-REGISTERED Z1-Z6 FORWARD EVIDENCE"
    )

    hypothesis = store.hypothesis_dashboard(
        evaluated
    )

    show(
        hypothesis,
        "No matured forward hypotheses yet.",
    )

    # =========================================================================
    # Direction baseline
    # =========================================================================

    section(
        "FORWARD DIRECTION BASELINE"
    )

    show(
        direction_dashboard(
            evaluated
        ),
        "No matured forward direction evidence.",
    )

    # =========================================================================
    # Latest events
    # =========================================================================

    section(
        "LATEST FORWARD ZONE EVENTS"
    )

    show(
        latest_events(
            evaluated,
            args.latest,
        ),
        "No forward zone events captured yet.",
    )

    # =========================================================================
    # Interpretation
    # =========================================================================

    section(
        "INTERPRETATION"
    )

    matured_count = int(
        evaluated[
            "status"
        ]
        .astype(
            str
        )
        .eq(
            "MATURED_20"
        )
        .sum()
        if not evaluated.empty
        else
        0
    )

    print(
        f"Total forward events    : {len(evaluated)}"
    )

    print(
        f"Matured 20-bar events   : {matured_count}"
    )

    print(
        (
            "Z1 aligned ACCEPTED   : historical hypothesis, "
            "forward evidence only from this ledger"
        )
    )

    print(
        (
            "Z2 aligned FRESH      : historical negative hypothesis, "
            "NOT a blocker"
        )
    )

    print(
        (
            "Z3 aligned INSIDE     : historical negative hypothesis, "
            "NOT a blocker"
        )
    )

    print(
        (
            "Z4 SHORT + OVERLAP    : historical positive hypothesis, "
            "NOT entry authorization"
        )
    )

    print(
        (
            "Z5 SHORT + INSIDE     : historical strong-negative hypothesis, "
            "NOT a blocker"
        )
    )

    print(
        (
            "Z6 BOTH_CLOSE         : tentative historical positive hypothesis, "
            "requires forward evidence"
        )
    )

    print(
        (
            "No RWEI policy change should be made from "
            "small forward sample sizes."
        )
    )

    print(
        (
            "Production trade_ready, LEI, risk and execution "
            "remain unchanged."
        )
    )

    print(
        "Trading/orders remain DISABLED."
    )


if __name__ == "__main__":

    main()