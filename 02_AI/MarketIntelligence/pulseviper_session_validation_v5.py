
"""
PulseViper Session & Cost Validation V5

Read-only research evaluation.

- Reuses saved V4 fold predictions.
- Evaluates identical decisions across all models.
- Uses historical MT5 bid/ask observations.
- Calculates spread-inclusive hypothetical exit results.
- Evaluates non-overlapping 60-second decisions.
- Reports results by UTC date and approximate session.
- Never trains, promotes models or places orders.

Python standard library only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shutil
import tempfile
from bisect import bisect_left
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "01_Data" / "VolumeMemory"

WALK = DATA / "StableMemoryV2" / "WalkForwardV4"
OUTPUT = DATA / "StableMemoryV2" / "SessionValidationV5"

SOURCE = (
    Path(os.environ["APPDATA"])
    / "MetaQuotes" / "Terminal" / "Common" / "Files"
    / "PulseViper" / "VolumeMemory"
    / "XAUUSD_PERIOD_M1_observations.csv"
)

MODELS = (
    "BASELINE",
    "STATE_MODEL",
    "CHALLENGER_RF",
)

LABELS = (
    "BUY_POSITIVE",
    "SELL_POSITIVE",
    "NEITHER_POSITIVE",
)

HORIZON_MS = 60_000
MAX_EXIT_LAG_MS = 3_000


@dataclass(frozen=True)
class Quote:
    time: int
    bid: float
    ask: float


@dataclass(frozen=True)
class Decision:
    fold: int
    symbol: str
    time: int
    actual: str
    predictions: dict[str, str]
    buy_net: float
    sell_net: float
    date: str
    session: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        return list(csv.DictReader(handle))


def session_name(timestamp: int) -> str:
    """Approximate UTC monitoring windows, not exchange sessions."""
    hour = datetime.fromtimestamp(
        timestamp / 1000,
        tz=timezone.utc,
    ).hour

    if 0 <= hour < 7:
        return "ASIA_UTC"
    if 7 <= hour < 13:
        return "LONDON_UTC"
    if 13 <= hour < 21:
        return "NY_UTC"
    return "ROLLOVER_UTC"


def latest_v4() -> Path:
    candidates = [
        p for p in WALK.iterdir()
        if p.is_dir()
        and (p / "predictions.csv").is_file()
        and (p / "report.json").is_file()
    ]

    if not candidates:
        raise RuntimeError("No V4 prediction run found")

    return max(
        candidates,
        key=lambda p: (
            (p / "report.json").stat().st_mtime_ns,
            p.name,
        ),
    )


def copy_recorder(destination: Path) -> None:
    """Frozen file copy; discard an incomplete final line."""
    shutil.copyfile(SOURCE, destination)

    with destination.open("rb+") as handle:
        content = handle.read()
        last = content.rfind(b"\n")

        if last < 0:
            raise RuntimeError("No complete recorder lines")

        handle.truncate(last + 1)


def load_quotes(
    path: Path,
) -> dict[str, list[Quote]]:
    grouped: dict[str, dict[int, Quote]] = defaultdict(dict)

    for row in read_csv(path):
        try:
            symbol = row["symbol"]
            t = int(row["tick_server_msc"])
            bid = float(row["bid"])
            ask = float(row["ask"])

            if (
                not symbol
                or t <= 0
                or not math.isfinite(bid)
                or not math.isfinite(ask)
                or bid <= 0
                or ask < bid
            ):
                continue

            grouped[symbol][t] = Quote(t, bid, ask)

        except (KeyError, ValueError, TypeError):
            continue

    return {
        symbol: sorted(
            values.values(), key=lambda q: q.time
        )
        for symbol, values in grouped.items()
    }


def prepare_decisions(
    prediction_path: Path,
    quotes: dict[str, list[Quote]],
    cost: float,
) -> tuple[list[Decision], Counter[str]]:
    prediction_map: dict[
        tuple[int, str, int], dict[str, str]
    ] = {}

    counts: Counter[str] = Counter()

    for row in read_csv(prediction_path):
        fold = int(row["fold"])
        symbol = row["symbol"]
        time = int(row["timestamp_msc"])
        model = row["model"]
        actual = row["actual"]
        predicted = row["predicted"]

        if model not in MODELS:
            raise RuntimeError(f"Unknown model: {model}")

        if actual not in LABELS or predicted not in LABELS:
            raise RuntimeError("Invalid prediction label")

        key = (fold, symbol, time)

        if key not in prediction_map:
            prediction_map[key] = {"actual": actual}

        item = prediction_map[key]

        if item["actual"] != actual:
            raise RuntimeError(
                f"Inconsistent actual label: {key}"
            )

        if model in item:
            raise RuntimeError(
                f"Duplicate model prediction: {key}/{model}"
            )

        item[model] = predicted

    indexed = {
        symbol: [q.time for q in rows]
        for symbol, rows in quotes.items()
    }

    quote_lookup = {
        symbol: {q.time: q for q in rows}
        for symbol, rows in quotes.items()
    }

    decisions: list[Decision] = []

    for (fold, symbol, t), item in sorted(
        prediction_map.items()
    ):
        if any(model not in item for model in MODELS):
            counts["INCOMPLETE_MODEL_SET"] += 1
            continue

        series = quotes.get(symbol, [])
        times = indexed.get(symbol, [])

        entry = quote_lookup.get(symbol, {}).get(t)

        if entry is None:
            counts["ENTRY_NOT_FOUND"] += 1
            continue

        target = t + HORIZON_MS
        position = bisect_left(times, target)

        if position >= len(series):
            counts["FUTURE_NOT_AVAILABLE"] += 1
            continue

        exit_quote = series[position]

        if exit_quote.time > target + MAX_EXIT_LAG_MS:
            counts["EXIT_TOO_LATE"] += 1
            continue

        buy_net = (
            exit_quote.bid - entry.ask - cost
        )

        sell_net = (
            entry.bid - exit_quote.ask - cost
        )

        # Check against the original labeling logic.
        if buy_net + cost > 0:
            derived = "BUY_POSITIVE"
        elif sell_net + cost > 0:
            derived = "SELL_POSITIVE"
        else:
            derived = "NEITHER_POSITIVE"

        if item["actual"] != derived:
            counts["LABEL_MISMATCH"] += 1
            continue

        utc = datetime.fromtimestamp(
            t / 1000, tz=timezone.utc
        )

        decisions.append(
            Decision(
                fold=fold,
                symbol=symbol,
                time=t,
                actual=item["actual"],
                predictions={
                    name: item[name] for name in MODELS
                },
                buy_net=buy_net,
                sell_net=sell_net,
                date=utc.date().isoformat(),
                session=session_name(t),
            )
        )

    return decisions, counts


def nonoverlap(
    decisions: list[Decision],
) -> list[Decision]:
    selected: list[Decision] = []
    previous: dict[str, int] = {}

    for d in sorted(
        decisions,
        key=lambda x: (x.time, x.symbol),
    ):
        last = previous.get(d.symbol)

        if (
            last is None
            or d.time - last >= HORIZON_MS
        ):
            selected.append(d)
            previous[d.symbol] = d.time

    return selected


def metrics(
    decisions: list[Decision],
    model: str,
) -> dict[str, Any]:
    n = len(decisions)

    if n == 0:
        return {"decisions": 0}

    correct = 0
    pnl = 0.0
    traded = 0
    wins = 0
    realized: list[float] = []
    class_recall: list[float] = []

    for label in LABELS:
        relevant = [
            d for d in decisions
            if d.actual == label
        ]

        if relevant:
            hits = sum(
                d.predictions[model] == label
                for d in relevant
            )
            class_recall.append(
                hits / len(relevant)
            )

    for d in decisions:
        prediction = d.predictions[model]

        if prediction == d.actual:
            correct += 1

        if prediction == "BUY_POSITIVE":
            net = d.buy_net
        elif prediction == "SELL_POSITIVE":
            net = d.sell_net
        else:
            net = 0.0

        pnl += net
        realized.append(net)

        if prediction != "NEITHER_POSITIVE":
            traded += 1
            wins += int(net > 0)

    return {
        "decisions": n,
        "accuracy": correct / n,
        "balanced_accuracy": (
            sum(class_recall) / len(class_recall)
            if class_recall else None
        ),
        "hypothetical_trades": traded,
        "trade_fraction": traded / n,
        "positive_trade_fraction": (
            wins / traded if traded else None
        ),
        "net_price_sum": pnl,
        "net_price_per_decision": pnl / n,
        "net_price_per_trade": (
            pnl / traded if traded else None
        ),
        "worst_single_decision": min(realized),
        "best_single_decision": max(realized),
    }


def make_report(
    decisions: list[Decision],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for model in MODELS:
        result[model] = metrics(decisions, model)

    return result


def write_rows(
    path: Path,
    rows: list[Decision],
) -> None:
    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle)

        writer.writerow([
            "fold", "symbol", "timestamp_msc",
            "date_utc", "session_utc",
            "actual", "buy_net_price",
            "sell_net_price",
            *MODELS,
        ])

        for d in rows:
            writer.writerow([
                d.fold, d.symbol, d.time,
                d.date, d.session,
                d.actual,
                round(d.buy_net, 6),
                round(d.sell_net, 6),
                *[d.predictions[m] for m in MODELS],
            ])


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--extra-cost",
        type=float,
        default=0.0,
        help=(
            "Additional round-trip execution cost "
            "in XAUUSD price units per hypothetical trade"
        ),
    )

    args = parser.parse_args()

    if (
        not math.isfinite(args.extra_cost)
        or args.extra_cost < 0
    ):
        parser.error("--extra-cost must be >= 0")

    OUTPUT.mkdir(
        parents=True, exist_ok=True
    )

    source_run = latest_v4()

    with tempfile.TemporaryDirectory(
        prefix=".pv_v5_",
        dir=OUTPUT,
    ) as temporary:
        folder = Path(temporary)

        recorder_copy = folder / "recorder.csv"
        copy_recorder(recorder_copy)

        quotes = load_quotes(recorder_copy)

        decisions, skipped = prepare_decisions(
            source_run / "predictions.csv",
            quotes,
            args.extra_cost,
        )

        if not decisions:
            print("PV_SESSION_VALIDATION=NO_MATCHED_DATA")
            print(f"SKIPPED={dict(skipped)}")
            return

        reduced = nonoverlap(decisions)

        dates = sorted({d.date for d in decisions})

        grouped: dict[
            tuple[str, str], list[Decision]
        ] = defaultdict(list)

        for d in reduced:
            grouped[(d.date, d.session)].append(d)

        session_reports: list[dict[str, Any]] = []

        for (day, session), events in sorted(
            grouped.items()
        ):
            session_reports.append({
                "date_utc": day,
                "session": session,
                "samples": len(events),
                "models": make_report(events),
            })

        report = {
            "schema": "PV_SESSION_VALIDATION_V5",
            "created_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "v4_run": source_run.name,
            "horizon_seconds": 60,
            "additional_cost_price_units": args.extra_cost,
            "all_decisions": len(decisions),
            "nonoverlap_decisions": len(reduced),
            "utc_dates": dates,
            "skipped": dict(skipped),
            "all_metrics": make_report(decisions),
            "nonoverlap_metrics": make_report(reduced),
            "session_results": session_reports,
            "limitations": [
                "Historical research; not live execution",
                "Bid/ask outcomes include quoted spread",
                "No commissions/slippage unless supplied",
                "WAIT assumes zero market exposure",
                "No TP, SL, drawdown, position sizing or margin",
                "Test periods were previously inspected",
                "Nonoverlap does not establish independence",
                "UTC sessions are approximate monitoring windows",
            ],
            "trading_enabled": False,
            "model_promoted": False,
        }

        run_id = (
            f"{source_run.name}_cost_"
            f"{str(args.extra_cost).replace('.', '_')}"
        )

        destination = OUTPUT / run_id
        destination.mkdir(
            parents=True, exist_ok=True
        )

        (destination / "report.json").write_text(
            json.dumps(report, indent=2),
            encoding="utf-8",
        )

        write_rows(
            destination / "nonoverlap_decisions.csv",
            reduced,
        )

        print("PV_SESSION_VALIDATION=V5")
        print(f"V4_RUN={source_run.name}")
        print(f"ALL_DECISIONS={len(decisions)}")
        print(f"NONOVERLAP_DECISIONS={len(reduced)}")
        print(f"UTC_DATES={dates}")
        print(f"SKIPPED={dict(skipped)}")

        print("\n=== NONOVERLAPPING EVALUATION ===")

        results = report["nonoverlap_metrics"]

        for model in MODELS:
            value = results[model]

            print(f"MODEL={model}")
            print(
                f"  ACCURACY={value['accuracy']:.2%}"
            )
            print(
                "  BALANCED_ACCURACY="
                f"{value['balanced_accuracy']:.2%}"
            )
            print(
                "  HYPOTHETICAL_TRADES="
                f"{value['hypothetical_trades']}"
            )
            print(
                "  NET_PRICE_PER_DECISION="
                f"{value['net_price_per_decision']:.5f}"
            )
            print(
                "  POSITIVE_TRADE_FRACTION="
                + (
                    f"{value['positive_trade_fraction']:.2%}"
                    if value["positive_trade_fraction"] is not None
                    else "N/A"
                )
            )

        print("\n=== SESSION COVERAGE ===")
        for row in session_reports:
            print(
                f"{row['date_utc']} "
                f"{row['session']} "
                f"N={row['samples']}"
            )

        print(f"\nREPORT={destination / 'report.json'}")
        print("PV_SESSION_VALIDATION_STATUS=PASS")
        print("INDEPENDENT_EDGE_PROVEN=NO")
        print("MODEL_PROMOTED=NO")
        print("TRADING_ENABLED=NO")


if __name__ == "__main__":
    main()
