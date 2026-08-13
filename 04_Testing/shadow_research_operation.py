"""
===============================================================================
Module      : shadow_research_operation.py
Project     : PulseViper XAU AI
Version     : 1.2
Purpose     : MT5 Read-Only Research Shadow + Candidate + Episode Analysis
===============================================================================

Runs CLOSED M1 candles only.

Flow
----
MT5 history
    ↓
Frozen production pipeline
    ↓
Causal research intelligence
    ↓
Regime metadata
    ↓
Research telemetry
    ↓
Production PaperLedger
    ↓
Research Candidate Outcome Ledger
    ↓
Candidate Episode Compression

Safety
------
- No orders.
- No position modification.
- No risk execution.
- Production trade_ready unchanged.
- LEI/MDC do not block production.
- Candidate paper entry = signal-bar close.
- Episode formation uses only causal candidate metadata + time.
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
).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# =============================================================================
# Core / research
# =============================================================================

fetcher: Any = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher

research_pipeline: Any = importlib.import_module(
    "02_AI.Shadow.research_intelligence_pipeline"
).research_intelligence_pipeline

research_telemetry: Any = importlib.import_module(
    "02_AI.Shadow.research_telemetry"
).research_telemetry


# =============================================================================
# Production PaperLedger
# =============================================================================

paper_module: Any = importlib.import_module(
    "02_AI.Shadow.paper_ledger"
)

PaperLedger: Any = paper_module.PaperLedger

DEFAULT_LEDGER_PATH: Path = (
    paper_module.DEFAULT_LEDGER_PATH
)


# =============================================================================
# Research Candidate Ledger
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
# Research Candidate Episode Analyzer
# =============================================================================

episode_module: Any = importlib.import_module(
    "02_AI.Shadow.research_candidate_episode"
)

ResearchCandidateEpisodeAnalyzer: Any = (
    episode_module.ResearchCandidateEpisodeAnalyzer
)


# =============================================================================
# Existing proven production-shadow helpers
# =============================================================================

paper_operation: Any = importlib.import_module(
    "04_Testing.shadow_paper_operation"
)

section: Any = paper_operation.section
attach_regime: Any = paper_operation.attach_regime

performance_dashboard: Any = (
    paper_operation.performance_dashboard
)

first_passage_dashboard: Any = (
    paper_operation.first_passage_dashboard
)

breakeven_dashboard: Any = (
    paper_operation.breakeven_dashboard
)

continuation_dashboard: Any = (
    paper_operation.continuation_dashboard
)


# =============================================================================
# Display
# =============================================================================

def display_frame(
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


def compact_event_table(
    frame: pd.DataFrame,
) -> pd.DataFrame:

    if frame.empty:
        return frame.copy()

    preferred = [
        "time",
        "close",

        "trade_ready",
        "confidence_direction",
        "confidence_score",

        "mdc_state",
        "mdc_direction",

        "liqintel_event_interpretation",
        "liqintel_event_bias",

        "lei_status",
        "lei_direction",
        "lei_entry_family",

        "lei_reference_price",
        "lei_reference_source",

        "lei_distance_atr",
        "lei_trigger_strength",

        "lei_confirmation_type",
        "lei_invalidation_price",

        "production_ready_overlap",
        "research_candidate_overlap",
    ]

    columns = [
        column
        for column in preferred
        if column in frame.columns
    ]

    result = frame.loc[
        :,
        columns,
    ].copy()

    for column in (
        "close",
        "confidence_score",
        "lei_reference_price",
        "lei_distance_atr",
        "lei_trigger_strength",
        "lei_invalidation_price",
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
            .round(3)
        )

    return result


def latest_candidate_outcomes(
    ledger: pd.DataFrame,
    limit: int,
) -> pd.DataFrame:

    if ledger.empty:
        return ledger.copy()

    preferred = [
        "signal_time",
        "capture_mode",

        "direction",
        "lei_entry_family",

        "entry_close",
        "lei_reference_price",
        "lei_reference_source",

        "confidence_score",
        "production_ready_overlap",

        "status",

        "net_5",
        "net_10",
        "net_20",

        "mfe_20",
        "mae_20",

        "fp_1_result",
        "fp_2_result",
        "fp_3_result",
        "fp_5_result",
    ]

    columns = [
        column
        for column in preferred
        if column in ledger.columns
    ]

    result = (
        ledger
        .tail(limit)
        .loc[
            :,
            columns,
        ]
        .copy()
    )

    for column in (
        "entry_close",
        "lei_reference_price",
        "confidence_score",
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
            .round(3)
        )

    return result


def latest_episode_table(
    episodes: pd.DataFrame,
    limit: int,
) -> pd.DataFrame:

    if episodes.empty:
        return episodes.copy()

    preferred = [
        "episode_start",
        "episode_end",

        "candidate_count",

        "direction",
        "lei_entry_family",

        "liqintel_event_interpretation",
        "lei_reference_source",
        "lei_confirmation_type",

        "first_entry_close",
        "first_reference_price",
        "first_distance_atr",

        "first_confidence_score",

        "first_production_ready_overlap",
        "any_production_ready_overlap",

        "first_mdc_state",
        "first_regime_state",

        "first_status",

        "first_net_5",
        "first_net_10",
        "first_net_20",

        "first_mfe_20",
        "first_mae_20",

        "first_fp_1_result",
        "first_fp_2_result",
        "first_fp_3_result",
        "first_fp_5_result",
    ]

    columns = [
        column
        for column in preferred
        if column in episodes.columns
    ]

    result = (
        episodes
        .tail(limit)
        .loc[
            :,
            columns,
        ]
        .copy()
    )

    for column in (
        "first_entry_close",
        "first_reference_price",
        "first_distance_atr",
        "first_confidence_score",

        "first_net_5",
        "first_net_10",
        "first_net_20",

        "first_mfe_20",
        "first_mae_20",
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
            .round(3)
        )

    return result


# =============================================================================
# Main
# =============================================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "PulseViper causal research shadow "
            "operation v1.2"
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
            DEFAULT_LEDGER_PATH
        ),
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
        "--latest",
        type=int,
        default=12,
    )

    args = parser.parse_args()

    if args.bars < 500:
        raise ValueError(
            "--bars must be >= 500"
        )

    if args.latest <= 0:
        raise ValueError(
            "--latest must be > 0"
        )

    if args.episode_gap < 1:
        raise ValueError(
            "--episode-gap must be >= 1"
        )

    # =========================================================================
    # Header
    # =========================================================================

    section(
        "PulseViper XAU AI — "
        "CAUSAL RESEARCH SHADOW OPERATION v1.2"
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
        f"Production ledger      : {Path(args.ledger)}"
    )

    print(
        (
            "Research candidate ledger : "
            f"{Path(args.candidate_ledger)}"
        )
    )

    print(
        "MT5 data               : READ ONLY"
    )

    print(
        "Trading/orders         : DISABLED"
    )

    print(
        "Position modification  : DISABLED"
    )

    print(
        "Production trade_ready : FROZEN / UNCHANGED"
    )

    print(
        "Research candidates    : OBSERVATION ONLY"
    )

    # =========================================================================
    # Fetch MT5
    # =========================================================================

    print(
        "\nFetching current MT5 M1 history..."
    )

    raw = fetcher.fetch(
        symbol=args.symbol,
        bars=args.bars,
    )

    if len(raw) < 2:
        raise RuntimeError(
            "Need at least two MT5 bars"
        )

    forming_time = pd.to_datetime(
        raw.iloc[-1][
            "time"
        ],
        errors="coerce",
    )

    closed = (
        raw
        .iloc[:-1]
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
        f"Fetched bars           : {len(raw)}"
    )

    print(
        f"Closed bars analysed   : {len(closed)}"
    )

    print(
        f"Resolved symbol        : {resolved_symbol}"
    )

    print(
        f"Excluded forming bar   : {forming_time}"
    )

    # =========================================================================
    # Research chain
    # =========================================================================

    print(
        "\nRunning frozen production + "
        "causal research pipeline..."
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

    # =========================================================================
    # Research telemetry
    # =========================================================================

    research_summary = (
        research_telemetry.summary(
            enriched
        )
    )

    research_statuses = (
        research_telemetry
        .status_distribution(
            enriched
        )
    )

    research_families = (
        research_telemetry
        .family_distribution(
            enriched
        )
    )

    latest_candidates = (
        research_telemetry
        .candidate_events(
            enriched,
            limit=args.latest,
        )
    )

    latest_ready = (
        research_telemetry
        .production_ready_context(
            enriched,
            limit=args.latest,
        )
    )

    # =========================================================================
    # Production PaperLedger
    # =========================================================================

    production_store = PaperLedger(
        args.ledger
    )

    existing_production = (
        production_store.load()
    )

    production_capture_mode = (
        "BOOTSTRAP_BACKFILL"
        if existing_production.empty
        else
        "LIVE_SHADOW"
    )

    visible_production = (
        production_store.capture_signals(
            enriched,
            args.symbol,
            resolved_symbol,
            "M1",
        )
    )

    (
        production_ledger,
        new_production_count,
    ) = production_store.merge_new_signals(
        existing_production,
        visible_production,
        production_capture_mode,
    )

    production_ledger = (
        production_store.evaluate(
            production_ledger,
            enriched,
        )
    )

    production_store.save(
        production_ledger
    )

    # =========================================================================
    # Candidate Outcome Ledger
    # =========================================================================

    candidate_store = ResearchCandidateLedger(
        args.candidate_ledger
    )

    existing_candidates = (
        candidate_store.load()
    )

    candidate_capture_mode = (
        "BOOTSTRAP_BACKFILL"
        if existing_candidates.empty
        else
        "LIVE_SHADOW"
    )

    visible_candidates = (
        candidate_store.capture_candidates(
            enriched=enriched,
            requested_symbol=args.symbol,
            resolved_symbol=resolved_symbol,
            timeframe="M1",
        )
    )

    (
        candidate_ledger,
        new_candidate_count,
    ) = candidate_store.merge_new_candidates(
        existing=existing_candidates,
        candidates=visible_candidates,
        capture_mode=candidate_capture_mode,
    )

    candidate_ledger = (
        candidate_store.evaluate(
            ledger=candidate_ledger,
            market=enriched,
        )
    )

    candidate_store.save(
        candidate_ledger
    )

    # =========================================================================
    # Candidate Episode Compression
    # =========================================================================

    episodes = (
        ResearchCandidateEpisodeAnalyzer
        .build(
            candidate_ledger,
            max_gap_minutes=args.episode_gap,
        )
    )

    compression = (
        ResearchCandidateEpisodeAnalyzer
        .compression_summary(
            candidate_ledger,
            episodes,
        )
    )

    episode_performance = (
        ResearchCandidateEpisodeAnalyzer
        .performance_dashboard(
            episodes
        )
    )

    episode_family = (
        ResearchCandidateEpisodeAnalyzer
        .family_dashboard(
            episodes
        )
    )

    episode_confidence = (
        ResearchCandidateEpisodeAnalyzer
        .confidence_dashboard(
            episodes
        )
    )

    # =========================================================================
    # Run status
    # =========================================================================

    section(
        "RUN STATUS"
    )

    production_status_counts = (
        production_ledger[
            "status"
        ]
        .astype(str)
        .value_counts()
        if not production_ledger.empty
        else pd.Series(
            dtype=int
        )
    )

    production_matured = int(
        production_status_counts.get(
            "MATURED_20",
            0,
        )
    )

    candidate_status_counts = (
        candidate_ledger[
            "status"
        ]
        .astype(str)
        .value_counts()
        if not candidate_ledger.empty
        else pd.Series(
            dtype=int
        )
    )

    candidate_matured = int(
        candidate_status_counts.get(
            "MATURED_20",
            0,
        )
    )

    print(
        (
            "Production READY visible       : "
            f"{len(visible_production)}"
        )
    )

    print(
        (
            "New production events         : "
            f"{new_production_count}"
        )
    )

    print(
        (
            "Production ledger total        : "
            f"{len(production_ledger)}"
        )
    )

    print(
        (
            "Production matured 20          : "
            f"{production_matured}"
        )
    )

    print()

    print(
        (
            "Research candidates visible    : "
            f"{len(visible_candidates)}"
        )
    )

    print(
        (
            "New research candidates        : "
            f"{new_candidate_count}"
        )
    )

    print(
        (
            "Candidate ledger total         : "
            f"{len(candidate_ledger)}"
        )
    )

    print(
        (
            "Candidate matured 20           : "
            f"{candidate_matured}"
        )
    )

    print(
        (
            "Opportunity episodes           : "
            f"{len(episodes)}"
        )
    )

    # =========================================================================
    # Raw research
    # =========================================================================

    section(
        "RESEARCH INTELLIGENCE SUMMARY"
    )

    display_frame(
        research_summary,
        "No research summary.",
    )

    section(
        "LEI STATUS DISTRIBUTION"
    )

    display_frame(
        research_statuses,
        "No LEI statuses.",
    )

    section(
        "RAW CANDIDATE FAMILY DISTRIBUTION"
    )

    display_frame(
        research_families,
        "No candidate families.",
    )

    # =========================================================================
    # Raw candidate performance
    # =========================================================================

    section(
        "RAW CANDIDATE PERFORMANCE — LONG vs SHORT"
    )

    display_frame(
        candidate_store.performance_dashboard(
            candidate_ledger
        ),
        "No matured candidates.",
    )

    section(
        "RAW CANDIDATE PERFORMANCE — FAMILY"
    )

    display_frame(
        candidate_store.family_dashboard(
            candidate_ledger
        ),
        "No matured family results.",
    )

    section(
        "RAW CANDIDATE PERFORMANCE — CONFIDENCE"
    )

    display_frame(
        candidate_store.confidence_dashboard(
            candidate_ledger
        ),
        "No matured confidence results.",
    )

    # =========================================================================
    # Episode analysis — MAIN NEW RESULT
    # =========================================================================

    section(
        "OPPORTUNITY EPISODE COMPRESSION"
    )

    display_frame(
        compression,
        "No episode compression data.",
    )

    section(
        "EPISODE-FIRST PERFORMANCE — LONG vs SHORT"
    )

    display_frame(
        episode_performance,
        "No matured episodes.",
    )

    section(
        "EPISODE-FIRST PERFORMANCE — ENTRY FAMILY"
    )

    display_frame(
        episode_family,
        "No matured episode-family results.",
    )

    section(
        "EPISODE-FIRST PERFORMANCE — CONFIDENCE BAND"
    )

    display_frame(
        episode_confidence,
        "No matured episode-confidence results.",
    )

    section(
        "LATEST OPPORTUNITY EPISODES"
    )

    display_frame(
        latest_episode_table(
            episodes,
            args.latest,
        ),
        "No opportunity episodes.",
    )

    # =========================================================================
    # Latest events
    # =========================================================================

    section(
        "LATEST RAW RESEARCH CANDIDATES"
    )

    display_frame(
        compact_event_table(
            latest_candidates
        ),
        "No current candidates.",
    )

    section(
        "LATEST RAW CANDIDATE OUTCOMES"
    )

    display_frame(
        latest_candidate_outcomes(
            candidate_ledger,
            args.latest,
        ),
        "No candidate outcomes.",
    )

    section(
        "LATEST PRODUCTION READY + RESEARCH CONTEXT"
    )

    display_frame(
        compact_event_table(
            latest_ready
        ),
        "No production READY events.",
    )

    # =========================================================================
    # Production benchmark
    # =========================================================================

    section(
        "PRODUCTION SHADOW PERFORMANCE"
    )

    display_frame(
        performance_dashboard(
            production_ledger
        ),
        "No production performance.",
    )

    section(
        "PRODUCTION FIRST PASSAGE"
    )

    display_frame(
        first_passage_dashboard(
            production_ledger
        ),
        "No production first-passage.",
    )

    section(
        "PRODUCTION BREAKEVEN"
    )

    display_frame(
        breakeven_dashboard(
            production_ledger
        ),
        "No production BE data.",
    )

    section(
        "PRODUCTION CONTINUATION / RUNNER"
    )

    display_frame(
        continuation_dashboard(
            production_ledger
        ),
        "No production continuation data.",
    )

    # =========================================================================
    # Interpretation
    # =========================================================================

    section(
        "INTERPRETATION"
    )

    print(
        (
            "- Raw candidate count is NOT treated as "
            "independent trade count."
        )
    )

    print(
        (
            "- Nearby structurally equivalent candidates "
            "are compressed into opportunity episodes."
        )
    )

    print(
        (
            "- Episode performance uses the FIRST causal "
            "candidate, preventing cherry-picking of the "
            "best later entry."
        )
    )

    print(
        (
            "- LEI/MDC remain weighted research evidence, "
            "not hard production blockers."
        )
    )

    print(
        (
            "- No production trade_ready, order, lot, SL, "
            "TP, BE or trailing logic changed."
        )
    )


if __name__ == "__main__":
    main()