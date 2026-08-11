"""
===============================================================================
Diagnostic  : daily_trade_readiness_diagnostic.py
Project     : PulseViper XAU AI
Author      : Muhammad Adnan
Purpose     : One-Day Temporal Scalping Pipeline Replay Diagnostic
===============================================================================

This is NOT a profitability backtest.

It answers:

- Did the scalping pipeline detect market activity?
- How many temporal setups started?
- How far did setups progress?
- How many expired?
- How many became READY?
- How many one-shot trade_ready events occurred?
- Which stage is starving the pipeline?
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

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


# =============================================================================
# Modules
# =============================================================================

fetcher = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher

scalping_pipeline = importlib.import_module(
    "02_AI.Core.scalping_pipeline"
).scalping_pipeline


# =============================================================================
# Helpers
# =============================================================================

def _count(
    df: pd.DataFrame,
    column: str,
) -> int:

    if column not in df.columns:
        return 0

    values = pd.to_numeric(
        df[column],
        errors="coerce",
    ).fillna(
        0
    )

    return int(
        values.sum()
    )


def _direction_count(
    df: pd.DataFrame,
    column: str,
    value: str,
) -> int:

    if column not in df.columns:
        return 0

    return int(
        (
            df[column]
            .astype(str)
            .str.upper()
            == value
        ).sum()
    )


def _print_metric(
    label: str,
    value: object,
) -> None:

    print(
        f"{label:<40} {value}"
    )


# =============================================================================
# Date Extraction
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
        "Dataset contains neither a 'time' column "
        "nor a DatetimeIndex."
    )


def _filter_date(
    df: pd.DataFrame,
    date_text: str,
) -> pd.DataFrame:

    target_date = (
        pd.Timestamp(
            date_text
        )
        .date()
    )

    mask = (
        df["time"]
        .dt.date
        == target_date
    )

    return (
        df.loc[
            mask
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )


# =============================================================================
# Setup Funnel
# =============================================================================

def _print_setup_funnel(
    df: pd.DataFrame,
    prefix: str,
    title: str,
) -> None:

    print()
    print(
        "=" * 79
    )
    print(
        title
    )
    print(
        "=" * 79
    )

    started = _count(
        df,
        f"{prefix}_setup_started_event",
    )

    expired = _count(
        df,
        f"{prefix}_setup_expired_event",
    )

    ready_events = _count(
        df,
        f"{prefix}_setup_ready_event",
    )

    displacement_rows = _count(
        df,
        f"{prefix}_setup_has_displacement",
    )

    bos_rows = _count(
        df,
        f"{prefix}_setup_has_bos",
    )

    fvg_rows = _count(
        df,
        f"{prefix}_setup_has_fvg",
    )

    rejection_rows = _count(
        df,
        f"{prefix}_setup_has_rejection",
    )

    _print_metric(
        "Setup starts:",
        started,
    )

    _print_metric(
        "Expired setups:",
        expired,
    )

    _print_metric(
        "READY transitions:",
        ready_events,
    )

    print()

    _print_metric(
        "Rows with displacement evidence:",
        displacement_rows,
    )

    _print_metric(
        "Rows with BOS evidence:",
        bos_rows,
    )

    _print_metric(
        "Rows with FVG evidence:",
        fvg_rows,
    )

    _print_metric(
        "Rows with rejection evidence:",
        rejection_rows,
    )

    # -------------------------------------------------------------------------
    # Maximum progress achieved by each setup ID
    # -------------------------------------------------------------------------

    id_column = (
        f"{prefix}_setup_id"
    )

    evidence_column = (
        f"{prefix}_setup_evidence_count"
    )

    if (
        id_column in df.columns
        and
        evidence_column in df.columns
    ):

        setup_rows = df[
            pd.to_numeric(
                df[id_column],
                errors="coerce",
            ).fillna(
                0
            )
            > 0
        ].copy()

        if not setup_rows.empty:

            progress = (
                setup_rows.groupby(
                    id_column
                )[
                    evidence_column
                ]
                .max()
            )

            print()

            for evidence in range(
                1,
                6,
            ):

                count = int(
                    (
                        progress
                        >= evidence
                    ).sum()
                )

                _print_metric(
                    (
                        f"Unique setups reaching "
                        f"{evidence}/5 evidence:"
                    ),
                    count,
                )


# =============================================================================
# READY Events
# =============================================================================

def _print_ready_events(
    df: pd.DataFrame,
) -> None:

    print()
    print(
        "=" * 79
    )
    print(
        "TEMPORAL READY EVENTS"
    )
    print(
        "=" * 79
    )

    if (
        "setup_ready_event"
        not in df.columns
    ):
        print(
            "setup_ready_event column missing."
        )
        return

    ready = df[
        pd.to_numeric(
            df[
                "setup_ready_event"
            ],
            errors="coerce",
        ).fillna(
            0
        )
        == 1
    ].copy()

    if ready.empty:

        print(
            "No temporal setup reached READY."
        )
        return

    columns = [
        "time",
        "setup_id",
        "setup_direction",
        "setup_age_bars",
        "setup_bos_scope",
        "setup_structure_alignment",
        "setup_fvg_id",
        "setup_rejection_fvg_id",
        "confidence_score",
        "confidence_grade",
        "confidence_confluence",
        "trade_ready",
    ]

    columns = [
        column
        for column in columns
        if column in ready.columns
    ]

    print(
        ready[
            columns
        ].to_string(
            index=False
        )
    )


# =============================================================================
# Trade Ready Events
# =============================================================================

def _print_trade_ready(
    df: pd.DataFrame,
) -> None:

    print()
    print(
        "=" * 79
    )
    print(
        "TRADE READY EVENTS"
    )
    print(
        "=" * 79
    )

    if "trade_ready" not in df.columns:

        print(
            "trade_ready column missing."
        )
        return

    trades = df[
        pd.to_numeric(
            df["trade_ready"],
            errors="coerce",
        ).fillna(
            0
        )
        == 1
    ].copy()

    if trades.empty:

        print(
            "No trade_ready events."
        )
        return

    columns = [
        "time",
        "close",
        "setup_id",
        "setup_direction",
        "setup_age_bars",
        "setup_bos_scope",
        "setup_structure_alignment",
        "confidence_score",
        "confidence_grade",
        "confidence_confluence",
    ]

    columns = [
        column
        for column in columns
        if column in trades.columns
    ]

    print(
        trades[
            columns
        ].to_string(
            index=False
        )
    )


# =============================================================================
# Main Diagnostic
# =============================================================================

def run(
    date_text: str,
    bars: int,
    symbol: str,
) -> None:

    print()
    print(
        "=" * 79
    )
    print(
        "PULSEVIPER XAU AI — TEMPORAL SCALPING REPLAY"
    )
    print(
        "=" * 79
    )

    print(
        f"Requested date : {date_text}"
    )

    print(
        f"Symbol         : {symbol}"
    )

    print(
        f"Fetch bars     : {bars}"
    )

    # =========================================================================
    # Fetch
    # =========================================================================

    raw = fetcher.fetch(
        symbol=symbol,
        bars=bars,
    )

    if raw is None:

        raise RuntimeError(
            "MT5 fetch returned None."
        )

    if len(raw) == 0:

        raise RuntimeError(
            "MT5 fetch returned zero rows."
        )

    raw = _prepare_time(
        raw
    )

    # =========================================================================
    # IMPORTANT
    #
    # Run the pipeline on the complete fetched chronological history FIRST.
    #
    # Then filter the target day.
    #
    # This preserves pre-day context for ATR, swings, liquidity and setup state.
    # =========================================================================

    result = (
        scalping_pipeline
        .generate(
            raw
        )
    )

    result = _prepare_time(
        result
    )

    day = _filter_date(
        result,
        date_text,
    )

    if day.empty:

        available_start = (
            result["time"]
            .min()
        )

        available_end = (
            result["time"]
            .max()
        )

        raise RuntimeError(
            "No rows found for requested date. "
            f"Available range: "
            f"{available_start} -> {available_end}"
        )

    # =========================================================================
    # Market Summary
    # =========================================================================

    print()
    print(
        "=" * 79
    )
    print(
        "MARKET DAY"
    )
    print(
        "=" * 79
    )

    _print_metric(
        "Bars:",
        len(day),
    )

    _print_metric(
        "First candle:",
        day[
            "time"
        ].iloc[0],
    )

    _print_metric(
        "Last candle:",
        day[
            "time"
        ].iloc[-1],
    )

    day_high = float(
        pd.to_numeric(
            day["high"],
            errors="coerce",
        ).max()
    )

    day_low = float(
        pd.to_numeric(
            day["low"],
            errors="coerce",
        ).min()
    )

    _print_metric(
        "Day high:",
        round(
            day_high,
            2,
        ),
    )

    _print_metric(
        "Day low:",
        round(
            day_low,
            2,
        ),
    )

    _print_metric(
        "Day range:",
        round(
            day_high
            - day_low,
            2,
        ),
    )

    # =========================================================================
    # Raw Signal Activity
    # =========================================================================

    print()
    print(
        "=" * 79
    )
    print(
        "RAW SCALPING ACTIVITY"
    )
    print(
        "=" * 79
    )

    _print_metric(
        "Bullish liquidity sweeps:",
        _count(
            day,
            "bullish_sweep",
        ),
    )

    _print_metric(
        "Bearish liquidity sweeps:",
        _count(
            day,
            "bearish_sweep",
        ),
    )

    _print_metric(
        "Bullish displacement:",
        int(
            (
                pd.to_numeric(
                    day.get(
                        "institutional_move",
                        pd.Series(
                            0,
                            index=day.index,
                        ),
                    ),
                    errors="coerce",
                ).fillna(
                    0
                )
                == 1
            ).sum()
        ),
    )

    _print_metric(
        "Bearish displacement:",
        int(
            (
                pd.to_numeric(
                    day.get(
                        "institutional_move",
                        pd.Series(
                            0,
                            index=day.index,
                        ),
                    ),
                    errors="coerce",
                ).fillna(
                    0
                )
                == -1
            ).sum()
        ),
    )

    _print_metric(
        "Micro swings:",
        (
            _count(
                day,
                "micro_high",
            )
            +
            _count(
                day,
                "micro_low",
            )
        ),
    )

    _print_metric(
        "Internal swings:",
        (
            _count(
                day,
                "internal_high",
            )
            +
            _count(
                day,
                "internal_low",
            )
        ),
    )

    _print_metric(
        "Major swings:",
        (
            _count(
                day,
                "major_high",
            )
            +
            _count(
                day,
                "major_low",
            )
        ),
    )

    _print_metric(
        "Bullish BOS:",
        _count(
            day,
            "bullish_bos",
        ),
    )

    _print_metric(
        "Bearish BOS:",
        _count(
            day,
            "bearish_bos",
        ),
    )

    _print_metric(
        "Micro BOS:",
        _count(
            day,
            "micro_bos",
        ),
    )

    _print_metric(
        "Internal BOS:",
        _count(
            day,
            "internal_bos",
        ),
    )

    _print_metric(
        "Major BOS:",
        _count(
            day,
            "major_bos",
        ),
    )

    _print_metric(
        "Bullish FVG:",
        _count(
            day,
            "bullish_fvg",
        ),
    )

    _print_metric(
        "Bearish FVG:",
        _count(
            day,
            "bearish_fvg",
        ),
    )

    _print_metric(
        "FVG rejections:",
        _count(
            day,
            "fvg_rejection",
        ),
    )

    _print_metric(
        "FVG mitigations:",
        _count(
            day,
            "fvg_mitigated",
        ),
    )

    # =========================================================================
    # Setup State
    # =========================================================================

    _print_setup_funnel(
        day,
        prefix="bullish",
        title=(
            "BULLISH TEMPORAL SETUP FUNNEL"
        ),
    )

    _print_setup_funnel(
        day,
        prefix="bearish",
        title=(
            "BEARISH TEMPORAL SETUP FUNNEL"
        ),
    )

    # =========================================================================
    # Overall Setup Summary
    # =========================================================================

    print()
    print(
        "=" * 79
    )
    print(
        "OVERALL SETUP SUMMARY"
    )
    print(
        "=" * 79
    )

    bullish_starts = _count(
        day,
        "bullish_setup_started_event",
    )

    bearish_starts = _count(
        day,
        "bearish_setup_started_event",
    )

    bullish_ready = _count(
        day,
        "bullish_setup_ready_event",
    )

    bearish_ready = _count(
        day,
        "bearish_setup_ready_event",
    )

    _print_metric(
        "Total setup starts:",
        (
            bullish_starts
            + bearish_starts
        ),
    )

    _print_metric(
        "Bullish starts:",
        bullish_starts,
    )

    _print_metric(
        "Bearish starts:",
        bearish_starts,
    )

    _print_metric(
        "Total READY transitions:",
        (
            bullish_ready
            + bearish_ready
        ),
    )

    _print_metric(
        "Bullish READY:",
        bullish_ready,
    )

    _print_metric(
        "Bearish READY:",
        bearish_ready,
    )

    _print_metric(
        "Setup conflicts:",
        _count(
            day,
            "setup_conflict",
        ),
    )

    _print_metric(
        "Trade ready events:",
        _count(
            day,
            "trade_ready",
        ),
    )

    # =========================================================================
    # Confidence
    # =========================================================================

    print()
    print(
        "=" * 79
    )
    print(
        "TEMPORAL CONFIDENCE"
    )
    print(
        "=" * 79
    )

    if (
        "confidence_score"
        in day.columns
    ):

        confidence = pd.to_numeric(
            day[
                "confidence_score"
            ],
            errors="coerce",
        ).fillna(
            0.0
        )

        _print_metric(
            "Average confidence:",
            round(
                float(
                    confidence.mean()
                ),
                2,
            ),
        )

        _print_metric(
            "Median confidence:",
            round(
                float(
                    confidence.median()
                ),
                2,
            ),
        )

        _print_metric(
            "Maximum confidence:",
            round(
                float(
                    confidence.max()
                ),
                2,
            ),
        )

        _print_metric(
            "Confidence >= 50:",
            int(
                (
                    confidence
                    >= 50.0
                ).sum()
            ),
        )

        _print_metric(
            "Confidence >= 65:",
            int(
                (
                    confidence
                    >= 65.0
                ).sum()
            ),
        )

        _print_metric(
            "Confidence >= 75:",
            int(
                (
                    confidence
                    >= 75.0
                ).sum()
            ),
        )

    _print_metric(
        "Temporal confidence rows:",
        _direction_count(
            day,
            "confidence_mode",
            "TEMPORAL_SETUP",
        ),
    )

    _print_metric(
        "Bullish confidence rows:",
        _direction_count(
            day,
            "confidence_direction",
            "BULLISH",
        ),
    )

    _print_metric(
        "Bearish confidence rows:",
        _direction_count(
            day,
            "confidence_direction",
            "BEARISH",
        ),
    )

    # =========================================================================
    # READY Details
    # =========================================================================

    _print_ready_events(
        day
    )

    _print_trade_ready(
        day
    )

    # =========================================================================
    # Diagnostic Interpretation
    # =========================================================================

    print()
    print(
        "=" * 79
    )
    print(
        "PIPELINE BOTTLENECK HINT"
    )
    print(
        "=" * 79
    )

    total_starts = (
        bullish_starts
        + bearish_starts
    )

    total_ready = (
        bullish_ready
        + bearish_ready
    )

    if total_starts == 0:

        print(
            "STARVATION: no directional setup seeds were created."
        )

    elif total_ready > 0:

        print(
            "TEMPORAL PIPELINE ACTIVE: at least one setup reached READY."
        )

    else:

        print(
            "No setup reached READY. Inspect the unique setup progress "
            "funnel above to identify the first missing stage."
        )

    print()


# =============================================================================
# CLI
# =============================================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Run one-day PulseViper temporal "
            "XAUUSD scalping replay."
        )
    )

    parser.add_argument(
        "--date",
        default="2026-08-07",
        help=(
            "Target date in YYYY-MM-DD format."
        ),
    )

    parser.add_argument(
        "--bars",
        type=int,
        default=10000,
        help=(
            "Number of M1 bars to fetch before filtering."
        ),
    )

    parser.add_argument(
        "--symbol",
        default="XAUUSDm",
        help=(
            "MT5 trading symbol."
        ),
    )

    args = parser.parse_args()

    run(
        date_text=args.date,
        bars=args.bars,
        symbol=args.symbol,
    )


if __name__ == "__main__":

    main()