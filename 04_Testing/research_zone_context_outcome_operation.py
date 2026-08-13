"""
===============================================================================
Module      : research_zone_context_outcome_operation.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : MT5 Read-Only Institutional Zone Context Outcome Evidence
===============================================================================

Flow
----
Existing Research Candidate Ledger
        ↓
Candidate Episode Compression
        ↓
Fetch CLOSED MT5 M1 history
        ↓
Frozen production + causal research pipeline
        ↓
Causal Institutional Zone Context
        ↓
Exact signal-time join
        ↓
Matched matured episodes only
        ↓
Retrospective zone-context outcome profiles

Critical coverage rule
----------------------
Historical episodes outside the fetched MT5 window are NOT interpreted as
"NO_ZONE".

Only rows with:

    zone_context_matched == 1

are included in zone performance profiling.

This avoids confusing missing historical coverage with genuine absence of
Institutional Zone context.

Safety
------
- MT5 READ ONLY
- no order_send
- no orders
- no position modification
- no ledger writes
- no risk execution
- no trade_ready modification
- no LEI modification
- no RWEI modification
- no automatic strategy promotion
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
# MT5 data
# =============================================================================

fetcher: Any = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher


# =============================================================================
# Causal research pipeline
# =============================================================================

research_pipeline: Any = importlib.import_module(
    "02_AI.Shadow.research_intelligence_pipeline"
).research_intelligence_pipeline


# =============================================================================
# Candidate ledger
# =============================================================================

candidate_module: Any = importlib.import_module(
    "02_AI.Shadow.research_candidate_ledger"
)

ResearchCandidateLedger: Any = (
    candidate_module.ResearchCandidateLedger
)

DEFAULT_RESEARCH_CANDIDATE_LEDGER_PATH: Path = (
    candidate_module.DEFAULT_RESEARCH_CANDIDATE_LEDGER_PATH
)


# =============================================================================
# Episode analyzer
# =============================================================================

episode_module: Any = importlib.import_module(
    "02_AI.Shadow.research_candidate_episode"
)

EpisodeAnalyzer: Any = (
    episode_module.ResearchCandidateEpisodeAnalyzer
)


# =============================================================================
# Zone context outcome profiler
# =============================================================================

zone_profile_module: Any = importlib.import_module(
    "02_AI.Shadow.research_zone_context_outcome"
)

Profiler: Any = (
    zone_profile_module.ResearchZoneContextOutcomeProfiler
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
    limit: int | None = None,
) -> None:

    if frame.empty:

        print(
            empty_message
        )

        return

    output = frame.copy()

    if (
        limit is not None
        and
        limit > 0
    ):

        output = output.head(
            limit
        )

    numeric_columns = (
        "sample_share_pct",

        "net5_med",
        "net10_med",
        "net20_med",

        "positive20_pct",

        "mfe20_med",
        "mae20_med",

        "excursion_balance_med",

        "matched_pct",

        "aligned_zone_pct",
        "opposing_zone_pct",

        "aligned_distance_atr",
        "opposing_distance_atr",

        "first_net_5",
        "first_net_10",
        "first_net_20",

        "first_mfe_20",
        "first_mae_20",
    )

    for column in numeric_columns:

        if column not in output.columns:
            continue

        output[
            column
        ] = (
            pd.to_numeric(
                output[
                    column
                ],
                errors="coerce",
            )
            .round(
                3
            )
        )

    print(
        output.to_string(
            index=False
        )
    )


# =============================================================================
# Coverage by direction
# =============================================================================


def direction_coverage(
    prepared: pd.DataFrame,
) -> pd.DataFrame:

    if prepared.empty:

        return pd.DataFrame(
            columns=[
                "direction",
                "episodes",
                "matched",
                "matched_pct",
                "aligned_zone_present",
                "aligned_zone_pct",
                "opposing_zone_present",
                "opposing_zone_pct",
            ]
        )

    rows: list[
        dict[
            str,
            Any,
        ]
    ] = []

    direction_series = (
        prepared[
            "direction"
        ]
        .astype(
            "string"
        )
        .fillna(
            "UNKNOWN"
        )
        .str
        .upper()
    )

    for direction in sorted(
        direction_series.unique()
    ):

        group = prepared.loc[
            direction_series.eq(
                direction
            )
        ].copy()

        total = len(
            group
        )

        matched = int(
            pd.to_numeric(
                group[
                    "zone_context_matched"
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

        aligned_present = int(
            group[
                "aligned_zone_event_id"
            ]
            .astype(
                str
            )
            .ne(
                "NONE"
            )
            .sum()
        )

        opposing_present = int(
            group[
                "opposing_zone_event_id"
            ]
            .astype(
                str
            )
            .ne(
                "NONE"
            )
            .sum()
        )

        rows.append(
            {
                "direction": (
                    direction
                ),

                "episodes": (
                    total
                ),

                "matched": (
                    matched
                ),

                "matched_pct": (
                    matched
                    /
                    total
                    *
                    100.0
                    if total
                    else
                    0.0
                ),

                "aligned_zone_present": (
                    aligned_present
                ),

                "aligned_zone_pct": (
                    aligned_present
                    /
                    total
                    *
                    100.0
                    if total
                    else
                    0.0
                ),

                "opposing_zone_present": (
                    opposing_present
                ),

                "opposing_zone_pct": (
                    opposing_present
                    /
                    total
                    *
                    100.0
                    if total
                    else
                    0.0
                ),
            }
        )

    return pd.DataFrame(
        rows
    )


# =============================================================================
# Exact interaction extraction
# =============================================================================


def exact_dimension(
    profiles: pd.DataFrame,
    dimension_name: str,
) -> pd.DataFrame:

    if profiles.empty:

        return profiles.copy()

    return (
        profiles.loc[
            profiles[
                "profile_dimensions"
            ]
            .astype(
                str
            )
            .eq(
                dimension_name
            )
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )


# =============================================================================
# Evidence shortlist
# =============================================================================


def positive_profiles(
    profiles: pd.DataFrame,
) -> pd.DataFrame:

    if profiles.empty:

        return profiles.copy()

    net20 = pd.to_numeric(
        profiles[
            "net20_med"
        ],
        errors="coerce",
    )

    positive20 = pd.to_numeric(
        profiles[
            "positive20_pct"
        ],
        errors="coerce",
    )

    result = profiles.loc[
        net20.gt(
            0.0
        )
        &
        positive20.gt(
            50.0
        )
    ].copy()

    if result.empty:

        return result

    return (
        result
        .sort_values(
            by=[
                "net20_med",
                "positive20_pct",
                "n",
            ],
            ascending=[
                False,
                False,
                False,
            ],
            na_position="last",
        )
        .reset_index(
            drop=True
        )
    )


def negative_profiles(
    profiles: pd.DataFrame,
) -> pd.DataFrame:

    if profiles.empty:

        return profiles.copy()

    net20 = pd.to_numeric(
        profiles[
            "net20_med"
        ],
        errors="coerce",
    )

    result = profiles.loc[
        net20.lt(
            0.0
        )
    ].copy()

    if result.empty:

        return result

    return (
        result
        .sort_values(
            by=[
                "net20_med",
                "positive20_pct",
                "n",
            ],
            ascending=[
                True,
                True,
                False,
            ],
            na_position="last",
        )
        .reset_index(
            drop=True
        )
    )


# =============================================================================
# Latest matched evidence
# =============================================================================


def latest_matched_table(
    matched: pd.DataFrame,
    limit: int,
) -> pd.DataFrame:

    if matched.empty:

        return matched.copy()

    preferred = [
        "first_signal_time",

        "direction",

        "aligned_zone_state",
        "aligned_location",
        "aligned_distance_atr",

        "opposing_zone_state",
        "opposing_location",
        "opposing_distance_atr",

        "zone_relation",

        "first_confidence_score",
        "first_regime_state",

        "first_net_5",
        "first_net_10",
        "first_net_20",

        "first_mfe_20",
        "first_mae_20",

        "first_positive_20",
    ]

    columns = [
        column
        for column in preferred
        if column in matched.columns
    ]

    return (
        matched
        .sort_values(
            "first_signal_time"
        )
        .tail(
            limit
        )
        .loc[
            :,
            columns,
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )


# =============================================================================
# Main
# =============================================================================


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "PulseViper Institutional Zone "
            "Context Outcome Evidence Operation"
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
        "--candidate-ledger",
        type=str,
        default=str(
            DEFAULT_RESEARCH_CANDIDATE_LEDGER_PATH
        ),
    )

    parser.add_argument(
        "--episode-gap",
        type=int,
        default=3,
    )

    parser.add_argument(
        "--minimum-n",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--interaction-minimum-n",
        type=int,
        default=15,
    )

    parser.add_argument(
        "--top",
        type=int,
        default=20,
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

    if args.minimum_n < 1:

        raise ValueError(
            "--minimum-n must be >= 1"
        )

    if args.interaction_minimum_n < 1:

        raise ValueError(
            "--interaction-minimum-n must be >= 1"
        )

    if args.top < 1:

        raise ValueError(
            "--top must be >= 1"
        )

    if args.latest < 1:

        raise ValueError(
            "--latest must be >= 1"
        )

    ledger_path = Path(
        args.candidate_ledger
    )

    # =========================================================================
    # Header
    # =========================================================================

    section(
        "PulseViper XAU AI — "
        "INSTITUTIONAL ZONE CONTEXT OUTCOME EVIDENCE v1.0"
    )

    print(
        f"Requested symbol          : {args.symbol}"
    )

    print(
        f"Requested bars            : {args.bars}"
    )

    print(
        f"Candidate ledger          : {ledger_path}"
    )

    print(
        f"Episode gap               : {args.episode_gap} min"
    )

    print(
        f"Evidence minimum N        : {args.minimum_n}"
    )

    print(
        (
            "Interaction minimum N    : "
            f"{args.interaction_minimum_n}"
        )
    )

    print(
        "MT5 access                : READ ONLY"
    )

    print(
        "Candidate ledger writes   : DISABLED"
    )

    print(
        "Trading/orders            : DISABLED"
    )

    print(
        "Position modification     : DISABLED"
    )

    print(
        "Production trade_ready    : FROZEN"
    )

    print(
        "Zone hard blockers        : NONE"
    )

    print(
        "LEI / RWEI changes        : NONE"
    )

    # =========================================================================
    # Existing candidate ledger
    # =========================================================================

    section(
        "LOAD EXISTING RESEARCH CANDIDATE LEDGER"
    )

    candidate_store = (
        ResearchCandidateLedger(
            ledger_path
        )
    )

    ledger = (
        candidate_store.load()
    )

    if ledger.empty:

        raise RuntimeError(
            "Research candidate ledger is empty"
        )

    print(
        f"Candidate ledger rows     : {len(ledger)}"
    )

    # =========================================================================
    # Build episodes
    # =========================================================================

    episodes = (
        EpisodeAnalyzer.build(
            ledger,
            max_gap_minutes=args.episode_gap,
        )
    )

    if episodes.empty:

        raise RuntimeError(
            "No research opportunity episodes available"
        )

    matured_mask = (
        episodes[
            "first_status"
        ]
        .astype(
            "string"
        )
        .fillna(
            "UNKNOWN"
        )
        .str
        .upper()
        .eq(
            "MATURED_20"
        )
    )

    matured_episode_count = int(
        matured_mask.sum()
    )

    print(
        f"Opportunity episodes      : {len(episodes)}"
    )

    print(
        f"Matured episodes          : {matured_episode_count}"
    )

    # =========================================================================
    # Fetch MT5 history
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
            "Need at least two MT5 bars"
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
        raw.iloc[
            :-1
        ]
        .copy()
        .reset_index(
            drop=True
        )
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
        f"Fetched bars              : {len(raw)}"
    )

    print(
        f"Closed bars analysed      : {len(closed)}"
    )

    print(
        f"Resolved symbol           : {resolved_symbol}"
    )

    print(
        f"Excluded forming bar      : {forming_time}"
    )

    if not closed.empty:

        print(
            (
                "Closed history start     : "
                f"{closed.iloc[0]['time']}"
            )
        )

        print(
            (
                "Closed history end       : "
                f"{closed.iloc[-1]['time']}"
            )
        )

    # =========================================================================
    # Causal pipeline replay
    # =========================================================================

    section(
        "RUN CAUSAL RESEARCH PIPELINE"
    )

    print(
        (
            "Running frozen production + causal "
            "research + Institutional Zone context..."
        )
    )

    enriched = (
        research_pipeline.generate(
            closed
        )
    )

    required_runtime = {
        "izctx_live_safe",
        "izctx_version",
        "izctx_mode",

        "research_live_safe",
        "research_trade_ready_unchanged",
    }

    missing_runtime = (
        required_runtime
        -
        set(
            enriched.columns
        )
    )

    if missing_runtime:

        raise RuntimeError(
            "Research pipeline missing Institutional "
            "Zone runtime columns: "
            +
            ", ".join(
                sorted(
                    missing_runtime
                )
            )
        )

    print(
        (
            "Research pipeline version : "
            f"{enriched['research_pipeline_version'].iloc[-1]}"
        )
    )

    print(
        (
            "Zone context version      : "
            f"{enriched['izctx_version'].iloc[-1]}"
        )
    )

    print(
        (
            "Zone context mode         : "
            f"{enriched['izctx_mode'].iloc[-1]}"
        )
    )

    # =========================================================================
    # Exact signal-time join
    # =========================================================================

    section(
        "EXACT SIGNAL-TIME ZONE CONTEXT JOIN"
    )

    prepared = Profiler.prepare(
        episodes=episodes,
        pipeline=enriched,
    )

    coverage = Profiler.coverage(
        prepared
    )

    show(
        coverage,
        "No coverage information.",
    )

    show(
        direction_coverage(
            prepared
        ),
        "No direction coverage information.",
    )

    # -------------------------------------------------------------------------
    # CRITICAL:
    # Profile ONLY exact signal-time matches.
    # -------------------------------------------------------------------------

    matched = prepared.loc[
        pd.to_numeric(
            prepared[
                "zone_context_matched"
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

    matched = matched.reset_index(
        drop=True
    )

    unmatched_count = (
        len(
            prepared
        )
        -
        len(
            matched
        )
    )

    print()

    print(
        f"Matured prepared episodes : {len(prepared)}"
    )

    print(
        f"Exact context matches      : {len(matched)}"
    )

    print(
        f"Outside/unmatched episodes : {unmatched_count}"
    )

    print(
        (
            "Unmatched interpretation  : COVERAGE GAP "
            "(NOT NO_ZONE)"
        )
    )

    if matched.empty:

        section(
            "NO MATCHED EVIDENCE"
        )

        print(
            (
                "No matured episode signal times overlap "
                "the fetched MT5 history window."
            )
        )

        print(
            (
                "Increase --bars or refresh the candidate "
                "ledger with the same market-history window."
            )
        )

        return

    # =========================================================================
    # Matched baseline
    # =========================================================================

    section(
        "MATCHED EPISODE BASELINE — LONG vs SHORT"
    )

    show(
        EpisodeAnalyzer.performance_dashboard(
            matched
        ),
        "No matched episode baseline.",
    )

    # =========================================================================
    # Single zone dimensions
    # =========================================================================

    single_dimensions = (
        "zone_relation",
        "aligned_zone_state",
        "aligned_location",
        "aligned_distance_band",
        "opposing_zone_state",
        "opposing_location",
        "opposing_distance_band",
    )

    for dimension in single_dimensions:

        profiles = Profiler.profile(
            prepared=matched,
            dimensions=[
                dimension,
            ],
            max_dimension_count=1,
            min_n=args.minimum_n,
        )

        section(
            f"ZONE PROFILE — {dimension.upper()}"
        )

        show(
            profiles,
            (
                "No qualifying profile at the "
                "requested minimum-N."
            ),
            limit=args.top,
        )

    # =========================================================================
    # Direction interactions
    # =========================================================================

    interaction_dimensions = (
        "zone_relation",
        "aligned_zone_state",
        "aligned_location",
        "aligned_distance_band",
        "opposing_zone_state",
        "opposing_location",
        "opposing_distance_band",
    )

    combined_interactions: list[
        pd.DataFrame
    ] = []

    for dimension in interaction_dimensions:

        profiles = Profiler.profile(
            prepared=matched,
            dimensions=[
                "direction",
                dimension,
            ],
            max_dimension_count=2,
            min_n=args.interaction_minimum_n,
        )

        exact = exact_dimension(
            profiles,
            f"direction+{dimension}",
        )

        if not exact.empty:

            combined_interactions.append(
                exact
            )

        section(
            (
                "DIRECTION × ZONE — "
                f"{dimension.upper()}"
            )
        )

        show(
            exact,
            (
                "No qualifying direction interaction "
                "at the requested minimum-N."
            ),
            limit=args.top,
        )

    if combined_interactions:

        interaction_pool = pd.concat(
            combined_interactions,
            ignore_index=True,
        )

    else:

        interaction_pool = pd.DataFrame(
            columns=list(
                Profiler.PROFILE_COLUMNS
            )
        )

    # =========================================================================
    # Broad zone evidence search
    # =========================================================================

    section(
        "BROAD ZONE CONTEXT EVIDENCE — UP TO 2 DIMENSIONS"
    )

    broad = Profiler.profile(
        prepared=matched,
        dimensions=Profiler.DEFAULT_DIMENSIONS,
        max_dimension_count=2,
        min_n=args.interaction_minimum_n,
    )

    show(
        broad,
        "No qualifying broad zone-context profiles.",
        limit=args.top,
    )

    # =========================================================================
    # Positive evidence hypotheses
    # =========================================================================

    section(
        "POSITIVE ZONE-CONTEXT HYPOTHESES"
    )

    positives = positive_profiles(
        broad
    )

    show(
        positives,
        (
            "No sufficiently sampled zone profile "
            "currently has both positive NET20 median "
            "and >50% positive20."
        ),
        limit=args.top,
    )

    # =========================================================================
    # Weak / negative evidence
    # =========================================================================

    section(
        "WEAKEST ZONE-CONTEXT EVIDENCE"
    )

    negatives = negative_profiles(
        broad
    )

    show(
        negatives,
        (
            "No sufficiently sampled negative "
            "zone-context profiles."
        ),
        limit=args.top,
    )

    # =========================================================================
    # Latest matched events
    # =========================================================================

    section(
        "LATEST MATCHED ZONE-CONTEXT EPISODES"
    )

    show(
        latest_matched_table(
            matched,
            args.latest,
        ),
        "No matched episode details.",
    )

    # =========================================================================
    # Diagnostics
    # =========================================================================

    section(
        "ZONE-CONTEXT DIAGNOSTICS"
    )

    aligned_present = (
        matched[
            "aligned_zone_event_id"
        ]
        .astype(
            str
        )
        .ne(
            "NONE"
        )
    )

    opposing_present = (
        matched[
            "opposing_zone_event_id"
        ]
        .astype(
            str
        )
        .ne(
            "NONE"
        )
    )

    aligned_inside = (
        pd.to_numeric(
            matched[
                "aligned_inside_flag"
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

    opposing_inside = (
        pd.to_numeric(
            matched[
                "opposing_inside_flag"
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

    print(
        (
            "Matched episodes          : "
            f"{len(matched)}"
        )
    )

    print(
        (
            "Aligned zone present      : "
            f"{int(aligned_present.sum())} "
            f"({aligned_present.mean() * 100.0:.3f}%)"
        )
    )

    print(
        (
            "Opposing zone present     : "
            f"{int(opposing_present.sum())} "
            f"({opposing_present.mean() * 100.0:.3f}%)"
        )
    )

    print(
        (
            "Inside aligned zone       : "
            f"{int(aligned_inside.sum())} "
            f"({aligned_inside.mean() * 100.0:.3f}%)"
        )
    )

    print(
        (
            "Inside opposing zone      : "
            f"{int(opposing_inside.sum())} "
            f"({opposing_inside.mean() * 100.0:.3f}%)"
        )
    )

    relation_counts = (
        matched[
            "zone_relation"
        ]
        .astype(
            str
        )
        .value_counts(
            dropna=False
        )
        .rename_axis(
            "zone_relation"
        )
        .reset_index(
            name="n"
        )
    )

    show(
        relation_counts,
        "No zone-relation counts.",
    )

    # =========================================================================
    # Interpretation
    # =========================================================================

    section(
        "INTERPRETATION RULES"
    )

    print(
        (
            "- Only exact signal-time matched episodes "
            "are used for zone outcome profiling."
        )
    )

    print(
        (
            "- Unmatched historical episodes represent "
            "missing MT5 coverage, NOT absence of a zone."
        )
    )

    print(
        (
            "- Positive zone context is evidence for a "
            "possible future weight, not a live entry rule."
        )
    )

    print(
        (
            "- Weak zone context is negative evidence, "
            "not an automatic NO TRADE blocker."
        )
    )

    print(
        (
            "- Multiple profile rows overlap and are not "
            "independent strategy discoveries."
        )
    )

    print(
        (
            "- Small-N profiles remain exploratory and "
            "must not be promoted."
        )
    )

    print(
        (
            "- Production trade_ready, LEI, RWEI, risk "
            "and execution remain unchanged."
        )
    )

    print(
        "- Trading/orders remain DISABLED."
    )


if __name__ == "__main__":

    main()