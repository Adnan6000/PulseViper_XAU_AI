"""
PulseViper XAU AI - Shadow/Paper Operation v1

Runs the frozen canonical pipeline on CLOSED M1 candles, persists trade_ready
signals, and updates 5/10/20-bar paper outcomes.

No orders are sent.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:

    sys.path.insert(
        0,
        str(
            PROJECT_ROOT
        ),
    )


fetcher: Any = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher

scalping_pipeline: Any = importlib.import_module(
    "02_AI.Core.scalping_pipeline"
).scalping_pipeline

market_regime: Any = importlib.import_module(
    "02_AI.Core.market_regime"
).market_regime

paper_module: Any = importlib.import_module(
    "02_AI.Shadow.paper_ledger"
)

PaperLedger: Any = (
    paper_module.PaperLedger
)

DEFAULT_LEDGER_PATH: Path = (
    paper_module.DEFAULT_LEDGER_PATH
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


def attach_regime(
    raw: pd.DataFrame,
    enriched: pd.DataFrame,
) -> pd.DataFrame:

    regime = market_regime.generate(
        raw
    )

    if len(
        regime
    ) != len(
        enriched
    ):

        raise RuntimeError(
            "Regime/pipeline row-count mismatch"
        )

    if (
        "time" in raw.columns
        and
        "time" in enriched.columns
    ):

        left = pd.to_datetime(
            raw[
                "time"
            ],
            errors="coerce",
        ).reset_index(
            drop=True
        )

        right = pd.to_datetime(
            enriched[
                "time"
            ],
            errors="coerce",
        ).reset_index(
            drop=True
        )

        if not left.equals(
            right
        ):

            raise RuntimeError(
                "Regime/pipeline time alignment mismatch"
            )

    result = enriched.copy()

    for column in market_regime.OUTPUT_COLUMNS:

        result[
            column
        ] = regime[
            column
        ].to_numpy(
            copy=True
        )

    return result


def number(
    series: pd.Series,
) -> pd.Series:

    return pd.to_numeric(
        series,
        errors="coerce",
    )


def median(
    frame: pd.DataFrame,
    column: str,
) -> float:

    values = number(
        frame[
            column
        ]
    ).dropna()

    if len(
        values
    ) == 0:

        return np.nan

    return float(
        values.median()
    )


def percentage(
    frame: pd.DataFrame,
    column: str,
) -> float:

    values = number(
        frame[
            column
        ]
    ).dropna()

    if len(
        values
    ) == 0:

        return np.nan

    return float(
        values.mean()
        *
        100.0
    )


def dashboard_rows(
    ledger: pd.DataFrame,
) -> pd.DataFrame:

    matured = ledger.loc[
        ledger[
            "status"
        ].astype(
            str
        )
        ==
        "MATURED_20"
    ].copy()

    rows: list[
        dict[
            str,
            Any,
        ]
    ] = []

    groups = [
        (
            "ALL",
            matured,
        )
    ]

    for direction in (
        "BULLISH",
        "BEARISH",
    ):

        groups.append(
            (
                direction,

                matured.loc[
                    matured[
                        "direction"
                    ]
                    .astype(
                        str
                    )
                    .str
                    .upper()
                    ==
                    direction
                ],
            )
        )

    for label, frame in groups:

        rows.append(
            {
                "group": label,

                "n": len(
                    frame
                ),

                "net5_med": median(
                    frame,
                    "net_5",
                ),

                "net10_med": median(
                    frame,
                    "net_10",
                ),

                "net20_med": median(
                    frame,
                    "net_20",
                ),

                "pos20_pct": percentage(
                    frame,
                    "positive_20",
                ),

                "mfe20_med": median(
                    frame,
                    "mfe_20",
                ),

                "mae20_med": median(
                    frame,
                    "mae_20",
                ),

                "$1_hit_pct": percentage(
                    frame,
                    "target_1_hit",
                ),

                "$2_hit_pct": percentage(
                    frame,
                    "target_2_hit",
                ),

                "$3_hit_pct": percentage(
                    frame,
                    "target_3_hit",
                ),

                "$5_hit_pct": percentage(
                    frame,
                    "target_5_hit",
                ),
            }
        )

    output = pd.DataFrame(
        rows
    )

    for column in output.columns:

        if column not in (
            "group",
            "n",
        ):

            output[
                column
            ] = pd.to_numeric(
                output[
                    column
                ],
                errors="coerce",
            ).round(
                3
            )

    return output


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "PulseViper V1 shadow/paper operation"
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
        "--latest",
        type=int,
        default=12,
    )

    args = parser.parse_args()

    if args.bars < 500:

        raise ValueError(
            "--bars must be >= 500 for safe pipeline warm-up"
        )

    if args.latest <= 0:

        raise ValueError(
            "--latest must be > 0"
        )

    section(
        "PulseViper V1 Shadow / Paper Operation"
    )

    print(
        f"Requested symbol  : {args.symbol}"
    )

    print(
        f"Requested bars    : {args.bars}"
    )

    print(
        f"Ledger path       : {Path(args.ledger)}"
    )

    print(
        "Trading/orders    : DISABLED"
    )

    print(
        "Production logic  : UNCHANGED"
    )

    print()

    print(
        "Fetching current MT5 M1 history..."
    )

    raw = fetcher.fetch(
        symbol=args.symbol,
        bars=args.bars,
    )

    if len(
        raw
    ) < 2:

        raise RuntimeError(
            "Need at least two bars"
        )

    # MT5 copy_rates position zero may include the currently forming candle.
    # Never allow a potentially incomplete candle to generate or mature
    # a shadow signal.

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
        f"Fetched bars      : {len(raw)}"
    )

    print(
        f"Closed bars used  : {len(closed)}"
    )

    print(
        f"Resolved symbol   : {resolved_symbol}"
    )

    print(
        (
            "Excluded last bar : "
            f"{forming_time} "
            "(treated as potentially forming)"
        )
    )

    print()

    print(
        "Running frozen canonical pipeline..."
    )

    enriched = scalping_pipeline.generate(
        closed
    )

    print(
        "Attaching causal regime metadata..."
    )

    enriched = attach_regime(
        closed,
        enriched,
    )

    ledger_store = PaperLedger(
        args.ledger
    )

    existing = ledger_store.load()

    capture_mode = (
        "BOOTSTRAP_BACKFILL"
        if existing.empty
        else
        "LIVE_SHADOW"
    )

    visible_signals = (
        ledger_store.capture_signals(
            enriched=enriched,
            requested_symbol=args.symbol,
            resolved_symbol=resolved_symbol,
            timeframe="M1",
        )
    )

    (
        ledger,
        new_count,
    ) = ledger_store.merge_new_signals(
        existing=existing,
        signals=visible_signals,
        capture_mode=capture_mode,
    )

    ledger = ledger_store.evaluate(
        ledger,
        closed,
    )

    ledger_store.save(
        ledger
    )

    section(
        "RUN STATUS"
    )

    if ledger.empty:

        statuses = pd.Series(
            dtype=int
        )

    else:

        statuses = (
            ledger[
                "status"
            ]
            .astype(
                str
            )
            .value_counts()
        )

    matured_count = int(
        statuses.get(
            "MATURED_20",
            0,
        )
    )

    print(
        (
            "Visible READY events in fetched window : "
            f"{len(visible_signals)}"
        )
    )

    print(
        (
            "New ledger events this run             : "
            f"{new_count}"
        )
    )

    print(
        (
            "Total ledger events                    : "
            f"{len(ledger)}"
        )
    )

    print(
        (
            "Matured 20-bar events                  : "
            f"{matured_count}"
        )
    )

    print(
        (
            "Partial/Open events                    : "
            f"{len(ledger) - matured_count}"
        )
    )

    print(
        (
            "Ledger saved                           : "
            f"{ledger_store.path}"
        )
    )

    section(
        "SHADOW PERFORMANCE DASHBOARD"
    )

    dashboard = dashboard_rows(
        ledger
    )

    print(
        dashboard.to_string(
            index=False
        )
    )

    section(
        "LATEST LEDGER EVENTS"
    )

    if ledger.empty:

        print(
            "No trade_ready events captured yet."
        )

    else:

        columns = [
            "signal_time",
            "capture_mode",
            "direction",
            "entry_reference",
            "confidence_score",
            "regime_state",
            "status",
            "net_5",
            "net_10",
            "net_20",
            "mfe_20",
            "mae_20",
            "target_1_hit",
            "target_2_hit",
            "target_3_hit",
            "target_5_hit",
        ]

        latest = (
            ledger
            .tail(
                args.latest
            )
            .loc[
                :,
                columns
            ]
            .copy()
        )

        for column in (
            "entry_reference",
            "confidence_score",
            "net_5",
            "net_10",
            "net_20",
            "mfe_20",
            "mae_20",
        ):

            latest[
                column
            ] = pd.to_numeric(
                latest[
                    column
                ],
                errors="coerce",
            ).round(
                3
            )

        print(
            latest.to_string(
                index=False
            )
        )

    section(
        "INTERPRETATION"
    )

    print(
        (
            "- BOOTSTRAP_BACKFILL = initial recent-history "
            "ledger seed; not forward proof."
        )
    )

    print(
        (
            "- LIVE_SHADOW = signal first observed "
            "after the ledger already existed."
        )
    )

    print(
        (
            "- NET uses signal-bar close as the "
            "paper reference and is direction-adjusted."
        )
    )

    print(
        (
            "- MFE/MAE are raw price excursions "
            "before execution costs."
        )
    )

    print(
        (
            "- $1/$2/$3/$5 hit means that favorable "
            "price excursion was reached within "
            "20 closed M1 bars."
        )
    )

    print(
        (
            "- No order, lot size, stop loss, "
            "or production trade decision is "
            "changed by this runner."
        )
    )


if __name__ == "__main__":

    main()