"""
===============================================================================
Module      : research_opportunity_quality_operation.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Offline Opportunity Quality Evidence Operation
===============================================================================

Reads the existing research candidate ledger and performs:

1. Candidate episode compression
2. Single-dimension quality profiling
3. Direction interactions
4. Direction + confidence + context interactions
5. Positive evidence shortlist
6. LONG 70-84 focused research
7. Weak / negative profile diagnostics

IMPORTANT
---------
This is retrospective research only.

It does NOT:
- place orders
- modify trade_ready
- modify production pipeline
- modify LEI / MDC / Confidence
- authorize a trading rule
- automatically turn a profitable historical bucket into a live blocker/filter

Positive historical groups are hypotheses for forward validation, not proof of
future profitability.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any

import pandas as pd


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


candidate_module: Any = importlib.import_module(
    "02_AI.Shadow.research_candidate_ledger"
)

episode_module: Any = importlib.import_module(
    "02_AI.Shadow.research_candidate_episode"
)

quality_module: Any = importlib.import_module(
    "02_AI.Shadow.research_opportunity_quality"
)


ResearchCandidateLedger: Any = (
    candidate_module.ResearchCandidateLedger
)

DEFAULT_RESEARCH_CANDIDATE_LEDGER_PATH: Path = (
    candidate_module.DEFAULT_RESEARCH_CANDIDATE_LEDGER_PATH
)

EpisodeAnalyzer: Any = (
    episode_module.ResearchCandidateEpisodeAnalyzer
)

Profiler: Any = (
    quality_module.ResearchOpportunityQualityProfiler
)


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

    print(
        output.to_string(
            index=False
        )
    )


def positive_long_70_84(
    profiles: pd.DataFrame,
    minimum_n: int,
) -> pd.DataFrame:

    if profiles.empty:
        return profiles.copy()

    key = profiles[
        "profile_key"
    ].astype(
        str
    )

    n = pd.to_numeric(
        profiles[
            "n"
        ],
        errors="coerce",
    )

    net20 = pd.to_numeric(
        profiles[
            "net20_med"
        ],
        errors="coerce",
    )

    positive = pd.to_numeric(
        profiles[
            "positive20_pct"
        ],
        errors="coerce",
    )

    mask = (
        key.str.contains(
            "direction=LONG",
            regex=False,
        )
        &
        key.str.contains(
            "confidence_band=70-84",
            regex=False,
        )
        &
        n.ge(
            minimum_n
        )
        &
        net20.gt(
            0.0
        )
        &
        positive.gt(
            50.0
        )
    )

    return (
        profiles
        .loc[
            mask
        ]
        .drop_duplicates(
            subset=[
                "profile_dimensions",
                "profile_key",
            ],
            keep="first",
        )
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
        )
        .reset_index(
            drop=True
        )
    )


def negative_profiles(
    profiles: pd.DataFrame,
    minimum_n: int,
) -> pd.DataFrame:

    if profiles.empty:
        return profiles.copy()

    n = pd.to_numeric(
        profiles[
            "n"
        ],
        errors="coerce",
    )

    net20 = pd.to_numeric(
        profiles[
            "net20_med"
        ],
        errors="coerce",
    )

    result = profiles.loc[
        n.ge(
            minimum_n
        )
        &
        net20.lt(
            0.0
        )
    ].copy()

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


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "PulseViper research opportunity "
            "quality profiling operation"
        )
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
        default=25,
    )

    args = parser.parse_args()

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

    ledger_path = Path(
        args.candidate_ledger
    )

    section(
        "PulseViper — OPPORTUNITY QUALITY PROFILER"
    )

    print(
        f"Candidate ledger     : {ledger_path}"
    )

    print(
        f"Episode gap          : {args.episode_gap} minutes"
    )

    print(
        f"Evidence minimum N   : {args.minimum_n}"
    )

    print(
        (
            "Interaction minimum N : "
            f"{args.interaction_minimum_n}"
        )
    )

    print(
        "Mode                 : RETROSPECTIVE RESEARCH ONLY"
    )

    print(
        "Production changes   : NONE"
    )

    print(
        "Hard blockers        : NONE"
    )

    print(
        "Trading/orders       : DISABLED"
    )

    # =========================================================================
    # Candidate ledger
    # =========================================================================

    store = ResearchCandidateLedger(
        ledger_path
    )

    ledger = store.load()

    if ledger.empty:
        raise RuntimeError(
            "Research candidate ledger is empty"
        )

    # =========================================================================
    # Episodes
    # =========================================================================

    episodes = EpisodeAnalyzer.build(
        ledger,
        max_gap_minutes=args.episode_gap,
    )

    compression = (
        EpisodeAnalyzer
        .compression_summary(
            ledger,
            episodes,
        )
    )

    matured_episodes = episodes.loc[
        episodes[
            "first_status"
        ]
        .astype(
            str
        )
        .eq(
            "MATURED_20"
        )
    ].copy()

    section(
        "DATASET STATUS"
    )

    print(
        f"Candidate ledger rows : {len(ledger)}"
    )

    print(
        f"Opportunity episodes  : {len(episodes)}"
    )

    print(
        f"Matured episodes      : {len(matured_episodes)}"
    )

    section(
        "EPISODE COMPRESSION"
    )

    show(
        compression,
        "No compression data.",
    )

    # =========================================================================
    # Baseline episode performance
    # =========================================================================

    section(
        "EPISODE BASELINE — LONG vs SHORT"
    )

    show(
        EpisodeAnalyzer
        .performance_dashboard(
            episodes
        ),
        "No matured episode performance.",
    )

    # =========================================================================
    # Single dimensions
    # =========================================================================

    singles = (
        Profiler
        .single_dimension_profiles(
            episodes,
            minimum_n=args.minimum_n,
        )
    )

    singles = (
        singles
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
        if not singles.empty
        else singles
    )

    section(
        "BEST SINGLE-DIMENSION PROFILES"
    )

    show(
        singles,
        "No qualifying single-dimension profiles.",
        limit=args.top,
    )

    # =========================================================================
    # Direction interactions
    # =========================================================================

    direction_profiles = (
        Profiler
        .direction_interactions(
            episodes,
            minimum_n=args.interaction_minimum_n,
        )
    )

    section(
        "BEST DIRECTION × CONTEXT INTERACTIONS"
    )

    show(
        direction_profiles,
        "No qualifying direction interactions.",
        limit=args.top,
    )

    # =========================================================================
    # Three-way interactions
    # =========================================================================

    three_way = (
        Profiler
        .three_way_profiles(
            episodes,
            minimum_n=args.interaction_minimum_n,
        )
    )

    section(
        "BEST DIRECTION × CONFIDENCE × CONTEXT"
    )

    show(
        three_way,
        "No qualifying three-way profiles.",
        limit=args.top,
    )

    # =========================================================================
    # Broad limited-depth search
    # =========================================================================

    combinations = (
        Profiler
        .combination_search(
            episodes,
            max_dimensions=3,
            minimum_n=args.minimum_n,
        )
    )

    shortlist = (
        Profiler
        .evidence_shortlist(
            combinations,
            minimum_n=args.minimum_n,
        )
    )

    section(
        "POSITIVE EVIDENCE SHORTLIST"
    )

    show(
        shortlist,
        (
            "No profile currently has both "
            "positive NET20 median and >50% positive20 "
            "with the requested sample floor."
        ),
        limit=args.top,
    )

    # =========================================================================
    # Focus on currently promising LONG 70-84 region
    # =========================================================================

    long_70_84 = positive_long_70_84(
        combinations,
        minimum_n=args.minimum_n,
    )

    section(
        "LONG + CONFIDENCE 70-84 — POSITIVE SUBGROUPS"
    )

    show(
        long_70_84,
        (
            "No sufficiently sampled positive "
            "LONG + 70-84 subgroup found."
        ),
        limit=args.top,
    )

    # =========================================================================
    # Weak profiles
    # =========================================================================

    weak = negative_profiles(
        combinations,
        minimum_n=args.minimum_n,
    )

    section(
        "WEAKEST SUFFICIENTLY-SAMPLED PROFILES"
    )

    show(
        weak,
        "No negative sufficiently sampled profiles.",
        limit=args.top,
    )

    # =========================================================================
    # Interpretation
    # =========================================================================

    section(
        "INTERPRETATION RULES"
    )

    print(
        (
            "- A positive historical subgroup is NOT "
            "automatically promoted into a live rule."
        )
    )

    print(
        (
            "- These profiles overlap with each other, "
            "so they must not be counted as independent "
            "strategy discoveries."
        )
    )

    print(
        (
            "- Small sample groups are excluded using "
            "minimum-N thresholds."
        )
    )

    print(
        (
            "- Strong groups become weighting hypotheses "
            "for forward validation."
        )
    )

    print(
        (
            "- Weak groups become negative evidence, "
            "not automatic hard blockers."
        )
    )

    print(
        (
            "- Production trade_ready and all order/risk "
            "logic remain unchanged."
        )
    )


if __name__ == "__main__":
    main()