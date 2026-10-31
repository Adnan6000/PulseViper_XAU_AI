
"""
PulseViper Quantum Brain - Decision Intelligence V7

Cost-sensitive multi-output regression:
- Predicts BUY and SELL net XAUUSD price changes.
- Uses a chronological TRAIN/CALIBRATION/TEST split.
- Estimates typical prediction error on calibration.
- Selects BUY, SELL or WAIT using adjusted payoff.
- Compares fixed baselines on identical test samples.
- Uses a 60-second holdout sampling interval.
- Does NOT modify the champion checkpoint or trade.

Research only. Not a validated profitable strategy.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from sklearn.ensemble import RandomForestRegressor


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "01_Data" / "VolumeMemory"
MEMORY = DATA / "StableMemoryV2"
OUTPUT = MEMORY / "DecisionIntelligenceV7"

FEATURES = DATA / "pattern_features_v1.csv"
LABELS_FILE = DATA / "reaction_outcomes_v1.csv"

RECORDER = (
    Path(os.environ["APPDATA"])
    / "MetaQuotes" / "Terminal" / "Common"
    / "Files" / "PulseViper" / "VolumeMemory"
    / "XAUUSD_PERIOD_M1_observations.csv"
)

ACTIVE = MEMORY / "active_checkpoint.json"
CHECKPOINTS = MEMORY / "checkpoints"

HORIZON_MS = 60_000
PURGE_MS = 120_000
SAMPLE_MS = 15_000
TEST_SPACING_MS = 60_000
MAX_EXIT_LAG_MS = 3_000


@dataclass(frozen=True)
class Quote:
    time: int
    bid: float
    ask: float


@dataclass(frozen=True)
class Sample:
    symbol: str
    time: int
    vector: NDArray[np.float64]
    buy_raw: float
    sell_raw: float


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024), b""
        ):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        return list(csv.DictReader(handle))


def checkpoint_schema() -> tuple[str, list[str]]:
    pointer = json.loads(
        ACTIVE.read_text(encoding="utf-8")
    )
    identity = str(pointer["checkpoint_id"])

    if (
        len(identity) != 16
        or any(c not in "0123456789abcdef" for c in identity)
    ):
        raise RuntimeError("Invalid checkpoint ID")

    metadata = json.loads(
        (
            CHECKPOINTS / identity / "metadata.json"
        ).read_text(encoding="utf-8")
    )

    if metadata["checkpoint_id"] != identity:
        raise RuntimeError("Checkpoint metadata mismatch")

    names = list(metadata["feature_names"])

    if not names or len(names) != len(set(names)):
        raise RuntimeError("Invalid feature schema")

    return identity, names


def stable_copies(
    directory: Path,
) -> tuple[Path, Path, Path]:
    sources = (FEATURES, LABELS_FILE, RECORDER)
    copies = (
        directory / "features.csv",
        directory / "outcomes.csv",
        directory / "recorder.csv",
    )

    for _ in range(5):
        before = tuple(
            (p.stat().st_size, p.stat().st_mtime_ns)
            for p in sources
        )

        for source, target in zip(sources, copies):
            shutil.copyfile(source, target)

        after = tuple(
            (p.stat().st_size, p.stat().st_mtime_ns)
            for p in sources
        )

        if before != after:
            continue

        # Recorder can be actively written by MT5.
        # Ignore an incomplete final CSV line.
        with copies[2].open("rb+") as handle:
            raw = handle.read()
            ending = raw.rfind(b"\n")
            if ending < 0:
                raise RuntimeError("Empty recorder snapshot")
            handle.truncate(ending + 1)

        return copies

    raise RuntimeError(
        "Input changed while copying; retry"
    )


def load_quotes(
    path: Path,
) -> dict[tuple[str, int], Quote]:
    result: dict[tuple[str, int], Quote] = {}

    for row in read_csv(path):
        try:
            symbol = row["symbol"]
            time = int(row["tick_server_msc"])
            bid = float(row["bid"])
            ask = float(row["ask"])

            if (
                not symbol
                or time <= 0
                or not math.isfinite(bid)
                or not math.isfinite(ask)
                or bid <= 0
                or ask < bid
            ):
                continue

            result[(symbol, time)] = Quote(
                time, bid, ask
            )

        except (KeyError, TypeError, ValueError):
            continue

    return result


def prepare(
    feature_path: Path,
    label_path: Path,
    recorder_path: Path,
    feature_names: list[str],
) -> tuple[list[Sample], Counter[str]]:
    quotes = load_quotes(recorder_path)
    outcomes: dict[tuple[str, int], int] = {}

    for row in read_csv(label_path):
        try:
            if int(row["horizon_seconds"]) != 60:
                continue

            symbol = row["symbol"]
            entry = int(row["entry_tick_msc"])
            exit_time = int(row["exit_tick_msc"])

            lag = (
                exit_time - entry - HORIZON_MS
            )

            if not 0 <= lag <= MAX_EXIT_LAG_MS:
                continue

            key = (symbol, entry)

            if key in outcomes:
                raise RuntimeError(
                    f"Duplicate outcome: {key}"
                )

            outcomes[key] = exit_time

        except (ValueError, TypeError, KeyError):
            continue

    raw = read_csv(feature_path)

    if not raw:
        raise RuntimeError("Empty feature dataset")

    required = (
        set(feature_names)
        | {"symbol", "tick_server_msc"}
    )

    missing = required - raw[0].keys()

    if missing:
        raise RuntimeError(
            f"Missing feature fields: {sorted(missing)}"
        )

    raw.sort(
        key=lambda r: (
            int(r["tick_server_msc"]),
            r["symbol"],
        )
    )

    samples: list[Sample] = []
    previous: dict[str, int] = {}
    seen: set[tuple[str, int]] = set()
    skipped: Counter[str] = Counter()

    for row in raw:
        symbol = row["symbol"]
        time = int(row["tick_server_msc"])
        key = (symbol, time)

        if key in seen:
            raise RuntimeError(
                f"Duplicate feature record: {key}"
            )

        seen.add(key)

        try:
            vector = np.asarray(
                [float(row[k]) for k in feature_names],
                dtype=np.float64,
            )

            if not bool(np.all(np.isfinite(vector))):
                skipped["INVALID_FEATURES"] += 1
                continue

        except (ValueError, TypeError, KeyError):
            skipped["INCOMPLETE_FEATURES"] += 1
            continue

        last = previous.get(symbol)

        if last is not None and time - last < SAMPLE_MS:
            continue

        previous[symbol] = time

        exit_time = outcomes.get(key)

        if exit_time is None:
            skipped["NO_MATURE_OUTCOME"] += 1
            continue

        entry_quote = quotes.get(key)
        exit_quote = quotes.get(
            (symbol, exit_time)
        )

        if entry_quote is None or exit_quote is None:
            skipped["QUOTE_NOT_FOUND"] += 1
            continue

        # BUY enters at Ask and exits at Bid.
        # SELL enters at Bid and exits at Ask.
        # Thus quoted spread is already included.
        buy_raw = (
            exit_quote.bid - entry_quote.ask
        )
        sell_raw = (
            entry_quote.bid - exit_quote.ask
        )

        samples.append(
            Sample(
                symbol=symbol,
                time=time,
                vector=vector,
                buy_raw=buy_raw,
                sell_raw=sell_raw,
            )
        )

    return samples, skipped


def matrix(
    rows: list[Sample],
) -> NDArray[np.float64]:
    return np.asarray(
        np.stack([row.vector for row in rows]),
        dtype=np.float64,
    )


def targets(
    rows: list[Sample],
) -> NDArray[np.float64]:
    return np.asarray(
        [
            [row.buy_raw, row.sell_raw]
            for row in rows
        ],
        dtype=np.float64,
    )


def nonoverlap_indices(
    rows: list[Sample],
) -> list[int]:
    picked: list[int] = []
    previous: dict[str, int] = {}

    for i, row in enumerate(rows):
        last = previous.get(row.symbol)

        if (
            last is None
            or row.time - last >= TEST_SPACING_MS
        ):
            picked.append(i)
            previous[row.symbol] = row.time

    return picked


def choose_actions(
    predictions: NDArray[np.float64],
    errors: NDArray[np.float64],
    additional_cost: float,
    risk_multiplier: float,
) -> list[str]:
    actions: list[str] = []

    for estimate in predictions:
        buy_adjusted = (
            float(estimate[0])
            - additional_cost
            - risk_multiplier * float(errors[0])
        )

        sell_adjusted = (
            float(estimate[1])
            - additional_cost
            - risk_multiplier * float(errors[1])
        )

        if max(buy_adjusted, sell_adjusted) <= 0:
            actions.append("WAIT")
        elif buy_adjusted >= sell_adjusted:
            actions.append("BUY")
        else:
            actions.append("SELL")

    return actions


def payoff(
    row: Sample,
    action: str,
    extra_cost: float,
) -> float:
    if action == "BUY":
        return row.buy_raw - extra_cost

    if action == "SELL":
        return row.sell_raw - extra_cost

    return 0.0


def evaluate(
    rows: list[Sample],
    actions: list[str],
    extra_cost: float,
) -> dict[str, Any]:
    if len(rows) != len(actions):
        raise RuntimeError("Decision alignment failure")

    n = len(rows)
    returns = [
        payoff(row, action, extra_cost)
        for row, action in zip(rows, actions)
    ]

    traded = [
        value
        for value, action in zip(returns, actions)
        if action != "WAIT"
    ]

    return {
        "decisions": n,
        "trades": len(traded),
        "waits": n - len(traded),
        "positive_trades": sum(
            x > 0 for x in traded
        ),
        "trade_win_fraction": (
            sum(x > 0 for x in traded) / len(traded)
            if traded else None
        ),
        "net_price_sum": sum(returns),
        "net_price_per_decision": (
            sum(returns) / n if n else None
        ),
        "net_price_per_trade": (
            sum(traded) / len(traded)
            if traded else None
        ),
        "worst_decision": (
            min(returns) if returns else None
        ),
        "best_decision": (
            max(returns) if returns else None
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--extra-cost",
        type=float,
        default=0.0,
    )

    parser.add_argument(
        "--risk-multiplier",
        type=float,
        default=0.5,
    )

    args = parser.parse_args()

    if (
        not math.isfinite(args.extra_cost)
        or args.extra_cost < 0
        or not math.isfinite(args.risk_multiplier)
        or args.risk_multiplier < 0
    ):
        parser.error(
            "Cost and risk multiplier must be finite "
            "nonnegative numbers"
        )

    print("PV_DECISION_INTELLIGENCE=V7")
    print("LEARNING_TARGET=BUY_SELL_NET_PRICE")
    print("CHAMPION_CHANGED=NO")
    print("TRADING_ENABLED=NO")

    checkpoint_id, features = checkpoint_schema()

    OUTPUT.mkdir(
        parents=True, exist_ok=True
    )

    with tempfile.TemporaryDirectory(
        prefix=".pv_v7_",
        dir=OUTPUT,
        ignore_cleanup_errors=True,
    ) as temporary:
        folder = Path(temporary)

        fpath, lpath, rpath = stable_copies(folder)

        samples, skipped = prepare(
            fpath, lpath, rpath, features
        )

        samples.sort(
            key=lambda item: (item.time, item.symbol)
        )

        print(f"CHECKPOINT_ID={checkpoint_id}")
        print(f"ALIGNED_SAMPLES={len(samples)}")
        print(f"SKIPPED={dict(skipped)}")

        if len(samples) < 150:
            print("STATUS=MORE_DATA_REQUIRED")
            return

        n = len(samples)

        first_cut = int(n * 0.55)
        second_cut = int(n * 0.80)

        calibration_start = samples[first_cut].time
        test_start = samples[second_cut].time

        train = [
            x for x in samples[:first_cut]
            if x.time + PURGE_MS < calibration_start
        ]

        calibration = [
            x for x in samples[first_cut:second_cut]
            if x.time + PURGE_MS < test_start
        ]

        test = samples[second_cut:]

        print(f"TRAIN_SAMPLES={len(train)}")
        print(f"CALIBRATION_SAMPLES={len(calibration)}")
        print(f"TEST_SAMPLES={len(test)}")

        if (
            len(train) < 80
            or len(calibration) < 30
            or len(test) < 20
        ):
            print("STATUS=INSUFFICIENT_SPLIT_DATA")
            return

        model = RandomForestRegressor(
            n_estimators=200,
            max_depth=5,
            min_samples_leaf=8,
            random_state=42,
            n_jobs=1,
        )

        model.fit(
            matrix(train),
            targets(train),
        )

        cal_predictions = np.asarray(
            model.predict(matrix(calibration)),
            dtype=np.float64,
        )

        # Mean absolute error is an empirical
        # error measure, NOT a confidence bound.
        cal_errors = np.abs(
            cal_predictions - targets(calibration)
        )

        error_estimates = np.asarray(
            np.mean(cal_errors, axis=0),
            dtype=np.float64,
        )

        test_predictions = np.asarray(
            model.predict(matrix(test)),
            dtype=np.float64,
        )

        picked = nonoverlap_indices(test)

        test_rows = [test[i] for i in picked]
        predicted = test_predictions[picked]

        if len(test_rows) < 10:
            print("STATUS=MORE_NONOVERLAP_DATA_REQUIRED")
            return

        model_actions = choose_actions(
            predicted,
            error_estimates,
            args.extra_cost,
            args.risk_multiplier,
        )

        strategies = {
            "DECISION_AI": model_actions,
            "ALWAYS_BUY": ["BUY"] * len(test_rows),
            "ALWAYS_SELL": ["SELL"] * len(test_rows),
            "ALWAYS_WAIT": ["WAIT"] * len(test_rows),
        }

        results = {
            name: evaluate(
                test_rows, actions, args.extra_cost
            )
            for name, actions in strategies.items()
        }

        # Keep a record of session coverage.
        dates = sorted({
            datetime.fromtimestamp(
                item.time / 1000,
                tz=timezone.utc,
            ).date().isoformat()
            for item in test_rows
        })

        run_id = hashlib.sha256(
            (
                checkpoint_id
                + file_hash(fpath)
                + file_hash(lpath)
                + file_hash(rpath)
                + str(args.extra_cost)
                + str(args.risk_multiplier)
                + "V7"
            ).encode()
        ).hexdigest()[:16]

        destination = OUTPUT / run_id
        destination.mkdir(
            parents=True, exist_ok=True
        )

        report: dict[str, Any] = {
            "schema": "PV_DECISION_INTELLIGENCE_V7",
            "run_id": run_id,
            "checkpoint_id": checkpoint_id,
            "created_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "feature_dimensions": len(features),
            "train_samples": len(train),
            "calibration_samples": len(calibration),
            "test_samples": len(test),
            "nonoverlap_test_samples": len(test_rows),
            "utc_dates": dates,
            "extra_cost_price_units": args.extra_cost,
            "risk_multiplier": args.risk_multiplier,
            "calibration_buy_mae": float(
                error_estimates[0]
            ),
            "calibration_sell_mae": float(
                error_estimates[1]
            ),
            "results": results,
            "limitations": [
                "Previously inspected historical market data",
                "Calibration MAE is not a confidence interval",
                "No intratrade TP/SL or drawdown modeling",
                "No actual broker order execution",
                "Quoted spread included; additional costs optional",
                "Short market history and dependent observations",
                "No independent profit evidence",
                "No model deployment or promotion",
            ],
            "trading_enabled": False,
        }

        (destination / "report.json").write_text(
            json.dumps(report, indent=2),
            encoding="utf-8",
        )

        with (
            destination / "test_decisions.csv"
        ).open(
            "w",
            encoding="utf-8",
            newline="",
        ) as handle:
            writer = csv.writer(handle)

            writer.writerow([
                "symbol",
                "timestamp_msc",
                "predicted_buy_raw",
                "predicted_sell_raw",
                "calibration_buy_mae",
                "calibration_sell_mae",
                "action",
                "actual_buy_raw",
                "actual_sell_raw",
                "realized_net",
            ])

            for row, estimate, action in zip(
                test_rows, predicted, model_actions
            ):
                writer.writerow([
                    row.symbol,
                    row.time,
                    float(estimate[0]),
                    float(estimate[1]),
                    float(error_estimates[0]),
                    float(error_estimates[1]),
                    action,
                    row.buy_raw,
                    row.sell_raw,
                    payoff(
                        row, action, args.extra_cost
                    ),
                ])

        print(
            f"CALIBRATION_BUY_MAE="
            f"{error_estimates[0]:.5f}"
        )
        print(
            f"CALIBRATION_SELL_MAE="
            f"{error_estimates[1]:.5f}"
        )
        print(
            f"RISK_MULTIPLIER={args.risk_multiplier:.2f}"
        )
        print(
            f"NONOVERLAP_TEST_SAMPLES="
            f"{len(test_rows)}"
        )

        print("\n=== COST-SENSITIVE TEST ===")

        for name, result in results.items():
            print(
                f"{name}: "
                f"TRADES={result['trades']} "
                f"WAITS={result['waits']} "
                f"NET_PER_DECISION="
                f"{result['net_price_per_decision']:.5f}"
            )

        print(f"UTC_DATES={dates}")
        print(f"REPORT={destination / 'report.json'}")
        print("PV_DECISION_INTELLIGENCE_STATUS=PASS")
        print("MODEL_SAVED=NO")
        print("CHAMPION_CHANGED=NO")
        print("PROFITABILITY_PROVEN=NO")
        print("TRADING_ENABLED=NO")


if __name__ == "__main__":
    main()
