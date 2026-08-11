"""
PulseViper XAU AI
Frozen Regime Hypothesis Historical Validation

Research only. Does not modify Confidence, trade_ready, risk, sizing, or execution.

Frozen from regime discovery:
2026-05-18 -> 2026-06-26

Default validation:
strictly before 2025-12-17, using 5 non-overlapping 10-day blocks.
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


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

research: Any = importlib.import_module(
    "04_Testing.confidence_v21_research_validation"
)
regime_diag: Any = importlib.import_module(
    "04_Testing.regime_conditioned_quality_validation"
)

fetcher: Any = research.fetcher
scalping_pipeline: Any = research.scalping_pipeline
_complete_dates: Any = research._complete_dates
_build_event_frame: Any = research._build_event_frame
_summary: Any = research._summary
_to_numeric: Any = research._to_numeric
_as_float: Any = research._as_float
_fmt: Any = research._fmt
_attach_regime: Any = regime_diag._attach_regime
_ensure_event_regime: Any = regime_diag._ensure_event_regime

Predicate = Callable[[pd.DataFrame], pd.Series]


def _section(title: str) -> None:
    print()
    print("=" * 118)
    print(title)
    print("=" * 118)


def _text(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series("", index=frame.index, dtype="object")

    return pd.Series(
        [str(value).upper() for value in frame[column].tolist()],
        index=frame.index,
        dtype="object",
    )


def _state(frame: pd.DataFrame, wanted: str) -> pd.Series:
    values = _text(frame, "regime_state")

    return pd.Series(
        (values == wanted.upper()).to_numpy(dtype=bool),
        index=frame.index,
        dtype="bool",
    )


def _trend_aligned(frame: pd.DataFrame) -> pd.Series:
    direction = _text(frame, "direction")
    trend = _text(frame, "regime_trend")

    mask = (
        ((direction == "BULLISH") & (trend == "BULLISH"))
        | ((direction == "BEARISH") & (trend == "BEARISH"))
    )

    return pd.Series(
        mask.to_numpy(dtype=bool),
        index=frame.index,
        dtype="bool",
    )


def _bearish_low(frame: pd.DataFrame) -> pd.Series:
    return _state(frame, "BEARISH_LOW_VOL")


def _bearish_normal(frame: pd.DataFrame) -> pd.Series:
    return _state(frame, "BEARISH_NORMAL_VOL")


def _bullish_high(frame: pd.DataFrame) -> pd.Series:
    return _state(frame, "BULLISH_HIGH_VOL")


def _bullish_low(frame: pd.DataFrame) -> pd.Series:
    return _state(frame, "BULLISH_LOW_VOL")


def _range_normal(frame: pd.DataFrame) -> pd.Series:
    return _state(frame, "RANGE_NORMAL_VOL")


HYPOTHESES: tuple[dict[str, Any], ...] = (
    {
        "key": "TREND_ALIGNED",
        "expected_sign": 1,
        "predicate": _trend_aligned,
    },
    {
        "key": "BEARISH_LOW_VOL",
        "expected_sign": 1,
        "predicate": _bearish_low,
    },
    {
        "key": "BEARISH_NORMAL_VOL",
        "expected_sign": 1,
        "predicate": _bearish_normal,
    },
    {
        "key": "BULLISH_HIGH_VOL",
        "expected_sign": 1,
        "predicate": _bullish_high,
    },
    {
        "key": "BULLISH_LOW_VOL",
        "expected_sign": -1,
        "predicate": _bullish_low,
    },
    {
        "key": "RANGE_NORMAL_VOL",
        "expected_sign": -1,
        "predicate": _range_normal,
    },
)


def _expected_text(sign: int) -> str:
    return "OUTPERFORM" if sign > 0 else "UNDERPERFORM"


def _build_blocks(
    dates: list[str],
    block_days: int,
    max_blocks: int,
) -> list[list[str]]:

    if block_days <= 0:
        raise ValueError("--block-days must be > 0")

    if max_blocks <= 0:
        raise ValueError("--max-blocks must be > 0")

    required = block_days * max_blocks

    if len(dates) < required:
        raise RuntimeError(
            f"Need at least {required} complete dates before cutoff; "
            f"found {len(dates)}. Increase --bars."
        )

    selected = dates[-required:]

    return [
        selected[start:start + block_days]
        for start in range(0, required, block_days)
    ]


def _safe_mask(
    frame: pd.DataFrame,
    predicate: Predicate,
) -> pd.Series:

    raw = predicate(frame)

    return pd.Series(
        raw.to_numpy(dtype=bool),
        index=frame.index,
        dtype="bool",
    )


def _spread(
    left: float,
    right: float,
) -> float:

    if np.isfinite(left) and np.isfinite(right):
        return float(left - right)

    return np.nan


def _stats(
    frame: pd.DataFrame,
    predicate: Predicate,
) -> dict[str, Any]:

    mask = _safe_mask(frame, predicate)

    selected = frame.loc[mask]
    rest = frame.loc[~mask]

    selected_summary = _summary(selected)
    rest_summary = _summary(rest)

    def value(
        summary: dict[str, Any],
        key: str,
    ) -> float:

        return _as_float(
            summary.get(
                key,
                np.nan,
            )
        )

    selected_5 = value(
        selected_summary,
        "net5_median",
    )

    rest_5 = value(
        rest_summary,
        "net5_median",
    )

    selected_10 = value(
        selected_summary,
        "net10_median",
    )

    rest_10 = value(
        rest_summary,
        "net10_median",
    )

    selected_20 = value(
        selected_summary,
        "net20_median",
    )

    rest_20 = value(
        rest_summary,
        "net20_median",
    )

    return {
        "selected_n": len(selected),
        "rest_n": len(rest),

        "selected_net5": selected_5,
        "spread5": _spread(
            selected_5,
            rest_5,
        ),

        "selected_net10": selected_10,
        "spread10": _spread(
            selected_10,
            rest_10,
        ),

        "selected_net20": selected_20,
        "rest_net20": rest_20,
        "spread20": _spread(
            selected_20,
            rest_20,
        ),

        "selected_pos20": value(
            selected_summary,
            "positive20_pct",
        ),
    }


def _expected_holds(
    value: float,
    sign: int,
) -> bool:

    if not np.isfinite(value):
        return False

    return (
        value > 0.0
        if sign > 0
        else value < 0.0
    )


def _daily_support(
    frame: pd.DataFrame,
    predicate: Predicate,
    sign: int,
) -> tuple[int, float, float]:

    spreads: list[float] = []

    for _, daily in frame.groupby("date_label"):

        stats = _stats(
            daily,
            predicate,
        )

        if (
            int(stats["selected_n"]) < 1
            or
            int(stats["rest_n"]) < 3
        ):
            continue

        spread20 = _as_float(
            stats[
                "spread20"
            ]
        )

        if np.isfinite(spread20):
            spreads.append(
                spread20
            )

    if not spreads:
        return (
            0,
            np.nan,
            np.nan,
        )

    confirmations = sum(
        _expected_holds(
            value,
            sign,
        )
        for value
        in spreads
    )

    confirm_pct = (
        confirmations
        /
        len(spreads)
        *
        100.0
    )

    median_spread = float(
        np.median(
            np.asarray(
                spreads,
                dtype=np.float64,
            )
        )
    )

    return (
        len(spreads),
        confirm_pct,
        median_spread,
    )


def _alignment_audit(
    events: pd.DataFrame,
) -> pd.DataFrame:

    direction = _text(
        events,
        "direction",
    )

    trend = _text(
        events,
        "regime_trend",
    )

    labels: list[str] = []

    for setup_direction, regime_trend in zip(
        direction.tolist(),
        trend.tolist(),
    ):

        if (
            setup_direction not in (
                "BULLISH",
                "BEARISH",
            )
            or regime_trend == "UNKNOWN"
        ):

            labels.append(
                "UNKNOWN"
            )

        elif regime_trend == "RANGE":

            labels.append(
                "RANGE"
            )

        elif setup_direction == regime_trend:

            labels.append(
                "ALIGNED"
            )

        else:

            labels.append(
                "OPPOSED"
            )

    table = (
        pd.Series(
            labels,
            dtype="object",
        )
        .value_counts(
            dropna=False
        )
        .rename_axis(
            "alignment"
        )
        .reset_index(
            name="events"
        )
    )

    table["pct"] = (
        table[
            "events"
        ]
        /
        len(events)
        *
        100.0
    ).round(1)

    return table


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "PulseViper frozen regime "
            "hypothesis validation"
        )
    )

    parser.add_argument(
        "--bars",
        type=int,
        default=320000,
    )

    parser.add_argument(
        "--symbol",
        type=str,
        default="XAUUSDm",
    )

    parser.add_argument(
        "--cutoff-date",
        type=str,
        default="2025-12-17",
    )

    parser.add_argument(
        "--block-days",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--max-blocks",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--min-selected-events",
        type=int,
        default=4,
    )

    parser.add_argument(
        "--min-rest-events",
        type=int,
        default=20,
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

    _section(
        "PulseViper Frozen Regime "
        "Hypothesis Historical Validation"
    )

    print(
        f"Requested bars    : "
        f"{args.bars}"
    )

    print(
        f"Strict cutoff     : "
        f"dates < {cutoff_label}"
    )

    print(
        f"Block days        : "
        f"{args.block_days}"
    )

    print(
        f"Blocks            : "
        f"{args.max_blocks}"
    )

    print(
        "Threshold tuning  : DISABLED"
    )

    print(
        "Production impact : NONE"
    )

    print()

    for hypothesis in HYPOTHESES:

        print(
            (
                f"{hypothesis['key']}: "
                f"{_expected_text(int(hypothesis['expected_sign']))}"
            )
        )

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
        f"Fetched bars      : "
        f"{len(raw)}"
    )

    resolved = str(
        getattr(
            fetcher,
            "last_resolved_symbol",
            "",
        )
    )

    if resolved:

        print(
            f"Resolved symbol   : "
            f"{resolved}"
        )

    print()

    print(
        "Running canonical trading pipeline..."
    )

    enriched: pd.DataFrame = (
        scalping_pipeline.generate(
            raw
        )
    )

    print(
        "Calculating independent causal "
        "regime metadata..."
    )

    enriched = _attach_regime(
        raw=raw,
        enriched=enriched,
    )

    complete_dates: list[str] = (
        _complete_dates(
            enriched
        )
    )

    eligible_dates = [
        date_label
        for date_label
        in complete_dates
        if date_label < cutoff_label
    ]

    blocks = _build_blocks(
        eligible_dates,
        args.block_days,
        args.max_blocks,
    )

    selected_dates = [
        date_label
        for block
        in blocks
        for date_label
        in block
    ]

    events: pd.DataFrame = (
        _build_event_frame(
            enriched
        )
    )

    events = _ensure_event_regime(
        events=events,
        enriched=enriched,
    )

    validation = events.loc[
        events[
            "date_label"
        ].isin(
            selected_dates
        )
    ].copy()

    if validation.empty:
        raise RuntimeError(
            "No trade_ready events in validation window."
        )

    _section(
        "OLDER NON-OVERLAPPING "
        "VALIDATION UNIVERSE"
    )

    print(
        f"Start date         : "
        f"{selected_dates[0]}"
    )

    print(
        f"End date           : "
        f"{selected_dates[-1]}"
    )

    print(
        f"Complete days      : "
        f"{len(selected_dates)}"
    )

    print(
        f"Trade-ready events : "
        f"{len(validation)}"
    )

    baseline = _summary(
        validation
    )

    print(
        (
            "Baseline NET20     : "
            f"{_fmt(baseline.get('net20_median'))}"
        )
    )

    _section(
        "ALIGNMENT CONTRACT AUDIT"
    )

    print(
        _alignment_audit(
            validation
        ).to_string(
            index=False
        )
    )

    results: dict[
        str,
        list[
            dict[str, Any]
        ],
    ] = {
        str(
            item[
                "key"
            ]
        ): []
        for item
        in HYPOTHESES
    }

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

        _section(
            (
                f"BLOCK {block_number}: "
                f"{block_dates[0]} -> "
                f"{block_dates[-1]}"
            )
        )

        rows: list[
            dict[str, Any]
        ] = []

        for hypothesis in HYPOTHESES:

            key = str(
                hypothesis[
                    "key"
                ]
            )

            sign = int(
                hypothesis[
                    "expected_sign"
                ]
            )

            predicate: Predicate = (
                hypothesis[
                    "predicate"
                ]
            )

            stats = _stats(
                block,
                predicate,
            )

            spread20 = _as_float(
                stats[
                    "spread20"
                ]
            )

            eligible = (
                int(
                    stats[
                        "selected_n"
                    ]
                )
                >= args.min_selected_events
                and
                int(
                    stats[
                        "rest_n"
                    ]
                )
                >= args.min_rest_events
                and
                np.isfinite(
                    spread20
                )
            )

            confirmed = (
                eligible
                and
                _expected_holds(
                    spread20,
                    sign,
                )
            )

            strong = (
                confirmed
                and
                abs(
                    spread20
                )
                >= 0.20
            )

            results[
                key
            ].append(
                {
                    "eligible": eligible,
                    "confirmed": confirmed,
                    "strong": strong,
                    "spread20": spread20,
                }
            )

            if not eligible:
                status = "INSUFFICIENT"

            elif strong:
                status = "STRONG"

            elif confirmed:
                status = "CONFIRM"

            else:
                status = "REVERSE"

            rows.append(
                {
                    "key": key,
                    "n": int(
                        stats[
                            "selected_n"
                        ]
                    ),
                    "net5": round(
                        _as_float(
                            stats[
                                "selected_net5"
                            ]
                        ),
                        3,
                    ),
                    "net10": round(
                        _as_float(
                            stats[
                                "selected_net10"
                            ]
                        ),
                        3,
                    ),
                    "net20": round(
                        _as_float(
                            stats[
                                "selected_net20"
                            ]
                        ),
                        3,
                    ),
                    "spread20": round(
                        spread20,
                        3,
                    ),
                    "pos20": round(
                        _as_float(
                            stats[
                                "selected_pos20"
                            ]
                        ),
                        1,
                    ),
                    "status": status,
                }
            )

        print(
            pd.DataFrame(
                rows
            ).to_string(
                index=False
            )
        )

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

    _section(
        "FROZEN REGIME ROBUSTNESS MATRIX"
    )

    aggregate_rows: list[
        dict[str, Any]
    ] = []

    for hypothesis in HYPOTHESES:

        key = str(
            hypothesis[
                "key"
            ]
        )

        sign = int(
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
            item
            for item
            in results[
                key
            ]
            if bool(
                item[
                    "eligible"
                ]
            )
        ]

        eligible_blocks = len(
            eligible_results
        )

        confirmations = sum(
            bool(
                item[
                    "confirmed"
                ]
            )
            for item
            in eligible_results
        )

        strong_blocks = sum(
            bool(
                item[
                    "strong"
                ]
            )
            for item
            in eligible_results
        )

        spreads = np.asarray(
            [
                _as_float(
                    item[
                        "spread20"
                    ]
                )
                for item
                in eligible_results
            ],
            dtype=np.float64,
        )

        spreads = spreads[
            np.isfinite(
                spreads
            )
        ]

        median_block_spread = (
            float(
                np.median(
                    spreads
                )
            )
            if spreads.size
            else np.nan
        )

        confirm_pct = (
            confirmations
            /
            eligible_blocks
            *
            100.0
            if eligible_blocks
            else np.nan
        )

        pooled_stats = _stats(
            pooled,
            predicate,
        )

        pooled_n = int(
            pooled_stats[
                "selected_n"
            ]
        )

        pooled_spread = _as_float(
            pooled_stats[
                "spread20"
            ]
        )

        pooled_holds = (
            pooled_n >= 20
            and
            _expected_holds(
                pooled_spread,
                sign,
            )
        )

        (
            daily_dates,
            daily_confirm_pct,
            median_daily_spread,
        ) = _daily_support(
            pooled,
            predicate,
            sign,
        )

        if (
            eligible_blocks >= 4
            and
            pooled_holds
            and
            _expected_holds(
                median_block_spread,
                sign,
            )
            and
            confirm_pct >= 66.7
            and
            abs(
                pooled_spread
            )
            >= 0.20
            and
            (
                not np.isfinite(
                    daily_confirm_pct
                )
                or
                daily_confirm_pct
                >= 55.0
            )
        ):

            verdict = (
                "ROBUST"
            )

        elif (
            eligible_blocks >= 3
            and
            pooled_holds
            and
            _expected_holds(
                median_block_spread,
                sign,
            )
            and
            confirm_pct >= 60.0
        ):

            verdict = (
                "PROMISING"
            )

        elif pooled_n < 20:

            verdict = (
                "INSUFFICIENT"
            )

        elif (
            not pooled_holds
            and
            (
                not np.isfinite(
                    confirm_pct
                )
                or
                confirm_pct <= 40.0
            )
        ):

            verdict = (
                "REVERSED"
            )

        else:

            verdict = (
                "UNSTABLE"
            )

        aggregate_rows.append(
            {
                "key": key,

                "expected": (
                    _expected_text(
                        sign
                    )
                ),

                "eligible_blocks": (
                    eligible_blocks
                ),

                "confirm_pct": round(
                    confirm_pct,
                    1,
                ),

                "strong_blocks": (
                    strong_blocks
                ),

                "median_block_spread20": round(
                    median_block_spread,
                    3,
                ),

                "pooled_n": (
                    pooled_n
                ),

                "pooled_net20": round(
                    _as_float(
                        pooled_stats[
                            "selected_net20"
                        ]
                    ),
                    3,
                ),

                "pooled_spread20": round(
                    pooled_spread,
                    3,
                ),

                "daily_dates": (
                    daily_dates
                ),

                "daily_confirm_pct": round(
                    daily_confirm_pct,
                    1,
                ),

                "median_daily_spread20": round(
                    median_daily_spread,
                    3,
                ),

                "verdict": (
                    verdict
                ),
            }
        )

    aggregate = pd.DataFrame(
        aggregate_rows
    )

    print(
        aggregate.to_string(
            index=False
        )
    )

    _section(
        "RESEARCH GATE"
    )

    robust = aggregate.loc[
        aggregate[
            "verdict"
        ]
        ==
        "ROBUST"
    ]

    print(
        f"ROBUST hypotheses: "
        f"{len(robust)}"
    )

    if not robust.empty:

        print()

        print(
            (
                "Eligible for later "
                "shadow-only regime policy research:"
            )
        )

        for key in robust[
            "key"
        ].tolist():

            print(
                f"  {key}"
            )

    print()

    print(
        (
            "No result here authorizes changes to "
            "Confidence, trade_ready, risk, "
            "or live execution."
        )
    )

    _section(
        "STATUS"
    )

    print(
        (
            "Frozen regime hypothesis historical "
            "validation completed successfully."
        )
    )


if __name__ == "__main__":
    main()