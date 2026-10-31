
"""
PulseViper Quantum Brain - Confidence & WAIT V6

Research-only, chronological confidence experiment.

TRAIN: Random Forest learns historical labels.
CALIBRATE: Logistic recalibration and threshold selection.
TEST: Untouched later-period evaluation.

- No model promotion
- No order execution
- No checkpoint overwrite
- No external AI APIs

Requires numpy and scikit-learn.
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
from bisect import bisect_left
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "01_Data" / "VolumeMemory"
MEMORY = DATA / "StableMemoryV2"

FEATURE_FILE = DATA / "pattern_features_v1.csv"
LABEL_FILE = DATA / "reaction_outcomes_v1.csv"

ACTIVE = MEMORY / "active_checkpoint.json"
CHECKPOINTS = MEMORY / "checkpoints"
OUTPUT = MEMORY / "ConfidenceWaitV6"

RECORDER = (
    Path(os.environ["APPDATA"])
    / "MetaQuotes" / "Terminal" / "Common"
    / "Files" / "PulseViper" / "VolumeMemory"
    / "XAUUSD_PERIOD_M1_observations.csv"
)

LABELS = (
    "BUY_POSITIVE",
    "SELL_POSITIVE",
    "NEITHER_POSITIVE",
)

HORIZON_MS = 60_000
PURGE_MS = 120_000
SAMPLE_MS = 15_000
EVALUATION_SPACING_MS = 60_000
MAX_EXIT_LAG_MS = 3_000
THRESHOLDS = (0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75)


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
    outcome: str
    buy_net: float
    sell_net: float


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        return list(csv.DictReader(handle))


def snapshot_inputs(directory: Path) -> tuple[Path, Path, Path]:
    original = (FEATURE_FILE, LABEL_FILE, RECORDER)
    copied = (
        directory / "features.csv",
        directory / "labels.csv",
        directory / "recorder.csv",
    )

    for _ in range(5):
        before = [
            (p.stat().st_size, p.stat().st_mtime_ns)
            for p in original
        ]

        for source, dest in zip(original, copied):
            shutil.copyfile(source, dest)

        after = [
            (p.stat().st_size, p.stat().st_mtime_ns)
            for p in original
        ]

        if before != after:
            continue

        # The live recorder may end with an incomplete row.
        with copied[2].open("rb+") as handle:
            raw = handle.read()
            last = raw.rfind(b"\n")

            if last < 0:
                raise RuntimeError("Recorder snapshot incomplete")

            handle.truncate(last + 1)

        return copied

    raise RuntimeError("Input files changed while copying")


def checkpoint_schema() -> tuple[str, list[str]]:
    pointer = json.loads(
        ACTIVE.read_text(encoding="utf-8")
    )

    identity = str(pointer["checkpoint_id"])

    if len(identity) != 16 or any(
        char not in "0123456789abcdef"
        for char in identity
    ):
        raise RuntimeError("Invalid checkpoint ID")

    metadata = json.loads(
        (
            CHECKPOINTS / identity / "metadata.json"
        ).read_text(encoding="utf-8")
    )

    if metadata["checkpoint_id"] != identity:
        raise RuntimeError("Checkpoint metadata mismatch")

    names: list[str] = list(metadata["feature_names"])

    if not names or len(set(names)) != len(names):
        raise RuntimeError("Invalid feature schema")

    return identity, names


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
            quotes.values(),
            key=lambda q: q.time,
        )
        for symbol, quotes in grouped.items()
    }


def prepare(
    features_path: Path,
    labels_path: Path,
    recorder_path: Path,
    feature_names: list[str],
    extra_cost: float,
) -> tuple[list[Sample], Counter[str]]:
    outcomes: dict[tuple[str, int], str] = {}

    for row in read_csv(labels_path):
        try:
            if int(row["horizon_seconds"]) != 60:
                continue

            entry = int(row["entry_tick_msc"])
            exit_t = int(row["exit_tick_msc"])
            label = row["outcome"]

            if (
                label not in LABELS
                or not 0 <= exit_t - entry - HORIZON_MS
                <= MAX_EXIT_LAG_MS
            ):
                continue

            key = (row["symbol"], entry)

            if key in outcomes:
                raise RuntimeError(f"Duplicate label: {key}")

            outcomes[key] = label

        except (KeyError, TypeError, ValueError):
            continue

    quotes = load_quotes(recorder_path)

    times = {
        symbol: [q.time for q in series]
        for symbol, series in quotes.items()
    }

    lookup = {
        symbol: {q.time: q for q in series}
        for symbol, series in quotes.items()
    }

    features = read_csv(features_path)

    if not features:
        raise RuntimeError("Empty features")

    absent = (
        set(feature_names)
        | {"symbol", "tick_server_msc"}
    ) - features[0].keys()

    if absent:
        raise RuntimeError(
            f"Missing columns: {sorted(absent)}"
        )

    features.sort(
        key=lambda row: (
            int(row["tick_server_msc"]),
            row["symbol"],
        )
    )

    selected: list[Sample] = []
    last_sample: dict[str, int] = {}
    seen: set[tuple[str, int]] = set()
    skipped: Counter[str] = Counter()

    for row in features:
        symbol = row["symbol"]
        t = int(row["tick_server_msc"])
        key = (symbol, t)

        if key in seen:
            raise RuntimeError(f"Duplicate feature: {key}")

        seen.add(key)

        try:
            vector = np.asarray(
                [float(row[name]) for name in feature_names],
                dtype=np.float64,
            )

            if not bool(np.all(np.isfinite(vector))):
                skipped["INCOMPLETE_FEATURES"] += 1
                continue

        except (KeyError, ValueError, TypeError):
            skipped["INCOMPLETE_FEATURES"] += 1
            continue

        # Match the historical 15-second sampling rhythm.
        previous = last_sample.get(symbol)

        if previous is not None and t - previous < SAMPLE_MS:
            continue

        last_sample[symbol] = t

        label = outcomes.get(key)

        if label is None:
            skipped["NO_MATURE_LABEL"] += 1
            continue

        entry = lookup.get(symbol, {}).get(t)
        series = quotes.get(symbol, [])
        symbol_times = times.get(symbol, [])

        if entry is None:
            skipped["ENTRY_QUOTE_MISSING"] += 1
            continue

        index = bisect_left(symbol_times, t + HORIZON_MS)

        if index >= len(series):
            skipped["EXIT_QUOTE_MISSING"] += 1
            continue

        exit_quote = series[index]

        if exit_quote.time > t + HORIZON_MS + MAX_EXIT_LAG_MS:
            skipped["EXIT_QUOTE_LATE"] += 1
            continue

        buy_raw = exit_quote.bid - entry.ask
        sell_raw = entry.bid - exit_quote.ask

        if buy_raw > 0:
            derived = "BUY_POSITIVE"
        elif sell_raw > 0:
            derived = "SELL_POSITIVE"
        else:
            derived = "NEITHER_POSITIVE"

        if derived != label:
            skipped["LABEL_MISMATCH"] += 1
            continue

        selected.append(
            Sample(
                symbol=symbol,
                time=t,
                vector=vector,
                outcome=label,
                buy_net=buy_raw - extra_cost,
                sell_net=sell_raw - extra_cost,
            )
        )

    return selected, skipped


def matrix(rows: list[Sample]) -> NDArray[np.float64]:
    return np.asarray(
        np.stack([row.vector for row in rows]),
        dtype=np.float64,
    )


def label_array(rows: list[Sample]) -> NDArray[np.str_]:
    return np.asarray(
        [row.outcome for row in rows],
        dtype=np.str_,
    )


def nonoverlap(rows: list[Sample]) -> list[int]:
    selected: list[int] = []
    previous: dict[str, int] = {}

    for index, row in enumerate(rows):
        last = previous.get(row.symbol)

        if (
            last is None
            or row.time - last >= EVALUATION_SPACING_MS
        ):
            selected.append(index)
            previous[row.symbol] = row.time

    return selected


def decide(
    probabilities: NDArray[np.float64],
    threshold: float,
) -> list[str]:
    actions: list[str] = []

    for probability in probabilities:
        buy, sell, neither = (
            float(probability[0]),
            float(probability[1]),
            float(probability[2]),
        )

        if buy >= sell and buy > neither and buy >= threshold:
            actions.append("BUY")
        elif sell > buy and sell > neither and sell >= threshold:
            actions.append("SELL")
        else:
            actions.append("WAIT")

    return actions


def outcome_for(
    sample: Sample,
    action: str,
) -> float:
    if action == "BUY":
        return sample.buy_net

    if action == "SELL":
        return sample.sell_net

    return 0.0


def evaluate_actions(
    rows: list[Sample],
    actions: list[str],
) -> dict[str, Any]:
    if len(rows) != len(actions):
        raise RuntimeError("Action alignment mismatch")

    n = len(rows)
    trades = 0
    positives = 0
    net_sum = 0.0

    for row, action in zip(rows, actions):
        net = outcome_for(row, action)
        net_sum += net

        if action != "WAIT":
            trades += 1
            positives += int(net > 0)

    return {
        "decisions": n,
        "trades": trades,
        "waits": n - trades,
        "trade_fraction": trades / n if n else None,
        "positive_trade_fraction": (
            positives / trades if trades else None
        ),
        "net_price_sum": net_sum,
        "net_price_per_decision": (
            net_sum / n if n else None
        ),
        "net_price_per_trade": (
            net_sum / trades if trades else None
        ),
    }


def quality(
    probabilities: NDArray[np.float64],
    truth: NDArray[np.str_],
) -> dict[str, float]:
    indices = {
        label: index
        for index, label in enumerate(LABELS)
    }

    one_hot = np.zeros_like(probabilities)

    for i, label in enumerate(truth):
        one_hot[i, indices[str(label)]] = 1.0

    brier = float(
        np.mean(np.sum((probabilities - one_hot) ** 2, axis=1))
    )

    confidence = probabilities.max(axis=1)
    predicted = probabilities.argmax(axis=1)
    actual = one_hot.argmax(axis=1)

    ece = 0.0

    for lower in np.linspace(0.0, 0.9, 10):
        upper = lower + 0.1
        mask = (
            (confidence >= lower)
            & (
                (confidence < upper)
                if upper < 1.0
                else (confidence <= upper)
            )
        )

        if not bool(np.any(mask)):
            continue

        accuracy = float(np.mean(predicted[mask] == actual[mask]))
        avg_conf = float(np.mean(confidence[mask]))

        ece += (
            float(np.mean(mask))
            * abs(accuracy - avg_conf)
        )

    return {
        "multiclass_brier": brier,
        "ece_10_bins": ece,
    }


def probabilities_for(
    forest: RandomForestClassifier,
    calibrator: LogisticRegression,
    x: NDArray[np.float64],
) -> NDArray[np.float64]:
    raw = np.asarray(
        forest.predict_proba(x),
        dtype=np.float64,
    )

    logits = np.log(np.clip(raw, 1e-6, 1.0))

    calibrated = np.asarray(
        calibrator.predict_proba(logits),
        dtype=np.float64,
    )

    # The LogisticRegression class order is
    # explicitly reordered to LABELS.
    result = np.zeros(
        (len(x), len(LABELS)),
        dtype=np.float64,
    )

    for index, label in enumerate(LABELS):
        matches = np.flatnonzero(
            calibrator.classes_ == label
        )

        if len(matches) != 1:
            raise RuntimeError(
                f"Calibration class missing: {label}"
            )

        result[:, index] = calibrated[:, int(matches[0])]

    return result


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--extra-cost",
        type=float,
        default=0.0,
    )

    args = parser.parse_args()

    if not math.isfinite(args.extra_cost) or args.extra_cost < 0:
        parser.error("--extra-cost must be nonnegative")

    print("PV_CONFIDENCE_WAIT=V6")
    print("CHAMPION_CHANGED=NO")
    print("TRADING_ENABLED=NO")

    identity, names = checkpoint_schema()
    OUTPUT.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix=".pv_v6_",
        dir=OUTPUT,
        ignore_cleanup_errors=True,
    ) as temporary:
        folder = Path(temporary)

        features, labels, recorder = snapshot_inputs(folder)

        rows, skipped = prepare(
            features,
            labels,
            recorder,
            names,
            args.extra_cost,
        )

        print(f"CHECKPOINT_ID={identity}")
        print(f"ALIGNED_SAMPLES={len(rows)}")
        print(f"SKIPPED={dict(skipped)}")

        if len(rows) < 150:
            print("STATUS=MORE_DATA_REQUIRED")
            return

        rows.sort(key=lambda row: (row.time, row.symbol))

        total = len(rows)
        cal_index = int(total * 0.55)
        test_index = int(total * 0.80)
        cal_start_time = rows[cal_index].time
        test_start_time = rows[test_index].time

        train = [
            row for row in rows[:cal_index]
            if row.time + PURGE_MS < cal_start_time
        ]
        calibration = [
            row for row in rows[cal_index:test_index]
            if row.time + PURGE_MS < test_start_time
        ]
        test = rows[test_index:]

        print("SPLIT_METHOD=CHRONOLOGICAL_SAMPLE_COUNT")
        print("PURGE_SECONDS=120")
        print(
            "TRAIN_CALIBRATION_GAP_SECONDS="
            + (
                str((cal_start_time - train[-1].time) / 1000)
                if train else "N/A"
            )
        )

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

        if (
            len({row.outcome for row in train}) < 3
            or len({row.outcome for row in calibration}) < 3
        ):
            print("STATUS=INSUFFICIENT_CLASS_DIVERSITY")
            return

        forest = RandomForestClassifier(
            n_estimators=150,
            max_depth=4,
            min_samples_leaf=8,
            class_weight="balanced",
            random_state=42,
            n_jobs=1,
        )

        forest.fit(matrix(train), label_array(train))

        raw_calibration = np.asarray(
            forest.predict_proba(matrix(calibration)),
            dtype=np.float64,
        )

        calibrator = LogisticRegression(
            max_iter=1000,
            C=1.0,
        )

        calibrator.fit(
            np.log(np.clip(raw_calibration, 1e-6, 1.0)),
            label_array(calibration),
        )

        calibration_prob = probabilities_for(
            forest, calibrator, matrix(calibration)
        )

        test_prob = probabilities_for(
            forest, calibrator, matrix(test)
        )

        calibration_indices = nonoverlap(calibration)
        test_indices = nonoverlap(test)

        calibration_subset = [
            calibration[i] for i in calibration_indices
        ]

        test_subset = [
            test[i] for i in test_indices
        ]

        cal_probs = calibration_prob[calibration_indices]
        final_probs = test_prob[test_indices]

        print(
            f"CALIBRATION_NONOVERLAP={len(calibration_subset)}"
        )
        print(
            f"TEST_NONOVERLAP={len(test_subset)}"
        )

        if (
            len(calibration_subset) < 10
            or len(test_subset) < 10
        ):
            print("STATUS=MORE_NONOVERLAP_DATA_REQUIRED")
            return

        evaluations: list[dict[str, Any]] = []

        for threshold in THRESHOLDS:
            actions = decide(cal_probs, threshold)

            metrics = evaluate_actions(
                calibration_subset, actions
            )

            if metrics["trades"] < 5:
                continue

            evaluations.append({
                "threshold": threshold,
                **metrics,
            })

        if not evaluations:
            print("STATUS=NO_ELIGIBLE_THRESHOLD")
            return

        # Threshold selected ONLY using calibration data.
        # Test labels and test PnL are not used here.
        chosen = max(
            evaluations,
            key=lambda result: (
                float(result["net_price_per_decision"]),
                float(result["threshold"]),
            ),
        )

        threshold = float(chosen["threshold"])
        test_actions = decide(final_probs, threshold)

        model_result = evaluate_actions(
            test_subset, test_actions
        )

        buy_result = evaluate_actions(
            test_subset,
            ["BUY"] * len(test_subset),
        )

        sell_result = evaluate_actions(
            test_subset,
            ["SELL"] * len(test_subset),
        )

        wait_result = evaluate_actions(
            test_subset,
            ["WAIT"] * len(test_subset),
        )

        calibration_quality = quality(
            calibration_prob,
            label_array(calibration),
        )

        test_quality = quality(
            test_prob,
            label_array(test),
        )

        fingerprint = hashlib.sha256(
            (
                identity
                + sha256(features)
                + sha256(labels)
                + sha256(recorder)
                + str(args.extra_cost)
                + "V6"
            ).encode()
        ).hexdigest()[:16]

        destination = OUTPUT / fingerprint
        destination.mkdir(parents=True, exist_ok=True)

        report = {
            "schema": "PV_CONFIDENCE_WAIT_V6",
            "checkpoint_id": identity,
            "run_id": fingerprint,
            "created_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "train_samples": len(train),
            "calibration_samples": len(calibration),
            "test_samples": len(test),
            "calibration_nonoverlap": len(
                calibration_subset
            ),
            "test_nonoverlap": len(test_subset),
            "selected_threshold": threshold,
            "threshold_selection_data": "CALIBRATION_ONLY",
            "calibration_threshold_trials": evaluations,
            "calibration_quality": calibration_quality,
            "test_quality": test_quality,
            "test_model": model_result,
            "test_always_buy": buy_result,
            "test_always_sell": sell_result,
            "test_always_wait": wait_result,
            "extra_cost_price_units": args.extra_cost,
            "limitations": [
                "Data previously inspected in V1-V5",
                "Short historical window",
                "Training/calibration observations may overlap",
                "Calibration threshold can overfit a small sample",
                "60-second observation gaps do not ensure independence",
                "No commission or slippage unless supplied",
                "No real order execution or stop-loss simulation",
                "Calibrated probabilities not yet independently validated",
                "No automatic retraining or promotion",
            ],
            "model_promoted": False,
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
                "utc_date",
                "actual",
                "prob_buy",
                "prob_sell",
                "prob_neither",
                "threshold",
                "action",
                "net_price",
            ])

            for row, probability, action in zip(
                test_subset, final_probs, test_actions
            ):
                writer.writerow([
                    row.symbol,
                    row.time,
                    datetime.fromtimestamp(
                        row.time / 1000,
                        tz=timezone.utc,
                    ).date().isoformat(),
                    row.outcome,
                    round(float(probability[0]), 6),
                    round(float(probability[1]), 6),
                    round(float(probability[2]), 6),
                    threshold,
                    action,
                    round(outcome_for(row, action), 6),
                ])

        print(f"SELECTED_THRESHOLD={threshold:.2f}")
        print(
            f"TEST_MULTICLASS_BRIER="
            f"{test_quality['multiclass_brier']:.5f}"
        )
        print(
            f"TEST_ECE="
            f"{test_quality['ece_10_bins']:.5f}"
        )

        print("\n=== HELD-OUT TEST ===")

        for name, result in (
            ("CONFIDENCE_MODEL", model_result),
            ("ALWAYS_BUY", buy_result),
            ("ALWAYS_SELL", sell_result),
            ("ALWAYS_WAIT", wait_result),
        ):
            print(
                f"{name}: "
                f"TRADES={result['trades']} "
                f"WAITS={result['waits']} "
                f"NET_PER_DECISION="
                f"{result['net_price_per_decision']:.5f}"
            )

        print(f"REPORT={destination / 'report.json'}")
        print(f"DECISIONS={destination / 'test_decisions.csv'}")
        print("PV_CONFIDENCE_WAIT_STATUS=PASS")
        print("MODEL_PROMOTED=NO")
        print("INDEPENDENT_EDGE_PROVEN=NO")
        print("TRADING_ENABLED=NO")


if __name__ == "__main__":
    main()
