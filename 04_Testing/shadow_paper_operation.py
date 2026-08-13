"""
PulseViper XAU AI - Shadow/Paper Operation v1.1

Runs the frozen canonical pipeline on CLOSED M1 candles.

Adds:
- first-passage analysis
- breakeven simulations
- continuation / runner telemetry
- post-entry BOS
- swing hierarchy
- structure evolution
- regime evolution

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

if str(
    PROJECT_ROOT
) not in sys.path:

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


def numeric(
    frame: pd.DataFrame,
    column: str,
) -> pd.Series:

    return pd.to_numeric(
        frame[
            column
        ],
        errors="coerce",
    )


def median(
    frame: pd.DataFrame,
    column: str,
) -> float:

    values = numeric(
        frame,
        column,
    ).dropna()

    if not len(
        values
    ):
        return np.nan

    return float(
        values.median()
    )


def percentage(
    frame: pd.DataFrame,
    column: str,
) -> float:

    values = numeric(
        frame,
        column,
    ).dropna()

    if not len(
        values
    ):
        return np.nan

    return float(
        values.mean()
        *
        100.0
    )


def matured_only(
    ledger: pd.DataFrame,
) -> pd.DataFrame:

    return ledger.loc[
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


def performance_dashboard(
    ledger: pd.DataFrame,
) -> pd.DataFrame:

    matured = matured_only(
        ledger
    )

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
                    .eq(
                        direction
                    )
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


def first_passage_dashboard(
    ledger: pd.DataFrame,
) -> pd.DataFrame:

    matured = matured_only(
        ledger
    )

    rows: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for target in (
        1,
        2,
        3,
        5,
    ):

        values = (
            matured[
                f"fp_{target}_result"
            ]
            .fillna(
                "UNKNOWN"
            )
            .astype(
                str
            )
        )

        profit = int(
            values.eq(
                "PROFIT_FIRST"
            ).sum()
        )

        loss = int(
            values.eq(
                "LOSS_FIRST"
            ).sum()
        )

        ambiguous = int(
            values.eq(
                "AMBIGUOUS_SAME_BAR"
            ).sum()
        )

        neither = int(
            values.eq(
                "NEITHER"
            ).sum()
        )

        resolved = (
            profit
            +
            loss
        )

        rows.append(
            {
                "threshold": (
                    f"±${target}"
                ),

                "n": len(
                    matured
                ),

                "profit_first": (
                    profit
                ),

                "loss_first": (
                    loss
                ),

                "ambiguous": (
                    ambiguous
                ),

                "neither": (
                    neither
                ),

                "profit_first_resolved_pct": (
                    round(
                        profit
                        /
                        resolved
                        *
                        100.0,
                        3,
                    )
                    if resolved
                    else np.nan
                ),
            }
        )

    return pd.DataFrame(
        rows
    )


def breakeven_dashboard(
    ledger: pd.DataFrame,
) -> pd.DataFrame:

    matured = matured_only(
        ledger
    )

    raw = (
        numeric(
            matured,
            "net_20",
        )
        if len(
            matured
        )
        else pd.Series(
            dtype=float
        )
    )

    rows: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for target in (
        1,
        2,
        3,
        5,
    ):

        status = (
            matured[
                f"be_after_{target}_status"
            ]
            .fillna(
                "UNKNOWN"
            )
            .astype(
                str
            )
        )

        simulated = (
            numeric(
                matured,
                f"be_after_{target}_net_20",
            )
            if len(
                matured
            )
            else pd.Series(
                dtype=float
            )
        )

        stopped = status.eq(
            "STOPPED_BE"
        )

        rows.append(
            {
                "activate_after": (
                    f"+${target}"
                ),

                "n": len(
                    matured
                ),

                "activated": int(
                    status.isin(
                        [
                            "STOPPED_BE",
                            "HELD_20",
                        ]
                    ).sum()
                ),

                "stopped_be": int(
                    stopped.sum()
                ),

                "held_20": int(
                    status.eq(
                        "HELD_20"
                    ).sum()
                ),

                "not_activated": int(
                    status.eq(
                        "NOT_ACTIVATED"
                    ).sum()
                ),

                "losers_saved": int(
                    (
                        stopped
                        &
                        raw.lt(
                            0
                        )
                    ).sum()
                )
                if len(
                    matured
                )
                else 0,

                "positive_20_cut_to_be": int(
                    (
                        stopped
                        &
                        raw.gt(
                            0
                        )
                    ).sum()
                )
                if len(
                    matured
                )
                else 0,

                "raw_net20_med": (
                    round(
                        float(
                            raw.median()
                        ),
                        3,
                    )
                    if len(
                        raw.dropna()
                    )
                    else np.nan
                ),

                "be_net20_med": (
                    round(
                        float(
                            simulated.median()
                        ),
                        3,
                    )
                    if len(
                        simulated.dropna()
                    )
                    else np.nan
                ),

                "median_delta": (
                    round(
                        float(
                            (
                                simulated
                                -
                                raw
                            ).median()
                        ),
                        3,
                    )
                    if len(
                        matured
                    )
                    else np.nan
                ),
            }
        )

    return pd.DataFrame(
        rows
    )


def continuation_dashboard(
    ledger: pd.DataFrame,
) -> pd.DataFrame:

    matured = matured_only(
        ledger
    )

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
                    .eq(
                        direction
                    )
                ],
            )
        )

    for label, frame in groups:

        directional_bos = (
            numeric(
                frame,
                "directional_bos_count_20",
            )
            if len(
                frame
            )
            else pd.Series(
                dtype=float
            )
        )

        opposing_bos = (
            numeric(
                frame,
                "opposing_bos_count_20",
            )
            if len(
                frame
            )
            else pd.Series(
                dtype=float
            )
        )

        rows.append(
            {
                "group": (
                    label
                ),

                "n": len(
                    frame
                ),

                "mfe20_med": median(
                    frame,
                    "mfe_20",
                ),

                "giveback20_med": median(
                    frame,
                    "giveback_20",
                ),

                "bars_to_mfe_med": median(
                    frame,
                    "bars_to_mfe_20",
                ),

                "ext_after_$1_med": median(
                    frame,
                    "extension_after_1_20",
                ),

                "ext_after_$2_med": median(
                    frame,
                    "extension_after_2_20",
                ),

                "dir_bos_any_pct": (
                    round(
                        float(
                            directional_bos
                            .gt(
                                0
                            )
                            .mean()
                            *
                            100.0
                        ),
                        3,
                    )
                    if len(
                        directional_bos
                    )
                    else np.nan
                ),

                "opp_bos_any_pct": (
                    round(
                        float(
                            opposing_bos
                            .gt(
                                0
                            )
                            .mean()
                            *
                            100.0
                        ),
                        3,
                    )
                    if len(
                        opposing_bos
                    )
                    else np.nan
                ),

                "structure_aligned20_pct": percentage(
                    frame,
                    "structure_aligned_20",
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
            "PulseViper V1 shadow/paper operation v1.1"
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
        "PulseViper V1 Shadow / Paper Operation v1.1"
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

    print(
        "\nFetching current MT5 M1 history..."
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

    print(
        "\nRunning frozen canonical pipeline..."
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

    store = PaperLedger(
        args.ledger
    )

    existing = store.load()

    capture_mode = (
        "BOOTSTRAP_BACKFILL"
        if existing.empty
        else
        "LIVE_SHADOW"
    )

    visible_signals = store.capture_signals(
        enriched,
        args.symbol,
        resolved_symbol,
        "M1",
    )

    (
        ledger,
        new_count,
    ) = store.merge_new_signals(
        existing,
        visible_signals,
        capture_mode,
    )

    # Important:
    # Evaluate against enriched causal frame, not raw OHLC only.
    # This allows shadow-only observation of BOS / structure / regime.

    ledger = store.evaluate(
        ledger,
        enriched,
    )

    store.save(
        ledger
    )

    section(
        "RUN STATUS"
    )

    statuses = (
        ledger[
            "status"
        ]
        .astype(
            str
        )
        .value_counts()
        if not ledger.empty
        else pd.Series(
            dtype=int
        )
    )

    matured_count = int(
        statuses.get(
            "MATURED_20",
            0,
        )
    )

    v11_count = (
        int(
            ledger[
                "ledger_version"
            ]
            .astype(
                str
            )
            .eq(
                "1.1"
            )
            .sum()
        )
        if not ledger.empty
        else 0
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
            "Ledger rows upgraded/evaluated v1.1    : "
            f"{v11_count}"
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
            f"{store.path}"
        )
    )

    section(
        "SHADOW PERFORMANCE DASHBOARD"
    )

    print(
        performance_dashboard(
            ledger
        ).to_string(
            index=False
        )
    )

    section(
        "FIRST PASSAGE DASHBOARD"
    )

    print(
        first_passage_dashboard(
            ledger
        ).to_string(
            index=False
        )
    )

    section(
        "BREAKEVEN SIMULATION — RAW PRICE, BEFORE COSTS"
    )

    print(
        breakeven_dashboard(
            ledger
        ).to_string(
            index=False
        )
    )

    section(
        "CONTINUATION / RUNNER DASHBOARD"
    )

    print(
        continuation_dashboard(
            ledger
        ).to_string(
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
            "net_20",
            "mfe_20",
            "mae_20",

            "fp_1_result",
            "fp_2_result",
            "fp_3_result",
            "fp_5_result",

            "be_after_1_status",
            "be_after_2_status",

            "bars_to_mfe_20",
            "giveback_20",

            "directional_bos_count_20",
            "opposing_bos_count_20",

            "structure_bias_20",
            "regime_state_20",
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
            "net_20",
            "mfe_20",
            "mae_20",
            "bars_to_mfe_20",
            "giveback_20",
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
            "- First passage asks whether +$X or -$X "
            "was reached first after the signal."
        )
    )

    print(
        (
            "- AMBIGUOUS_SAME_BAR means M1 OHLC cannot "
            "prove intrabar ordering; no guess is made."
        )
    )

    print(
        (
            "- BE simulation activates after favorable "
            "+$1/+2/+3/+5 and checks return to entry "
            "from the NEXT candle onward."
        )
    )

    print(
        (
            "- BE results are raw-price research only: "
            "spread, commission, slippage and real fill "
            "are not yet deducted."
        )
    )

    print(
        (
            "- Continuation telemetry measures MFE extension, "
            "giveback, BOS, swing scale, structure and regime."
        )
    )

    print(
        (
            "- No order, stop, lot size, trailing rule or "
            "production trade decision is changed."
        )
    )


if __name__ == "__main__":

    main()