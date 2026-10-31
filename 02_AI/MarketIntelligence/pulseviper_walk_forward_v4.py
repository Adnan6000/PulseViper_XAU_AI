
"""
PulseViper Walk-Forward Validation V4

Expanding chronological training, purged future testing.
Compares:
  1. Majority baseline
  2. KMeans state-based classifier
  3. Random Forest challenger

No checkpoint overwrite, promotion or trading.
Exploratory research, NOT proven trading performance.
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
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import RobustScaler


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "01_Data" / "VolumeMemory"
MEMORY = DATA / "StableMemoryV2"

FEATURE_FILE = DATA / "pattern_features_v1.csv"
LABEL_FILE = DATA / "reaction_outcomes_v1.csv"

ACTIVE = MEMORY / "active_checkpoint.json"
CHECKPOINTS = MEMORY / "checkpoints"
OUTPUT = MEMORY / "WalkForwardV4"

HORIZON = 60
SAMPLE_MS = 15_000
PURGE_MS = 120_000

LABELS = (
    "BUY_POSITIVE",
    "SELL_POSITIVE",
    "NEITHER_POSITIVE",
)


@dataclass(frozen=True)
class Sample:
    symbol: str
    timestamp: int
    features: NDArray[np.float64]
    outcome: str


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(
            lambda: f.read(1024 * 1024), b""
        ):
            h.update(chunk)
    return h.hexdigest()


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as f:
        return list(csv.DictReader(f))


def snapshot_inputs(
    folder: Path,
) -> tuple[Path, Path]:
    paths = (FEATURE_FILE, LABEL_FILE)
    copies = (
        folder / "features.csv",
        folder / "labels.csv",
    )

    for _ in range(5):
        before = [
            (p.stat().st_size, p.stat().st_mtime_ns)
            for p in paths
        ]

        for source, destination in zip(paths, copies):
            shutil.copyfile(source, destination)

        after = [
            (p.stat().st_size, p.stat().st_mtime_ns)
            for p in paths
        ]

        if before == after:
            return copies

    raise RuntimeError(
        "Input files changed during snapshot; retry"
    )


def checkpoint_features() -> tuple[str, list[str]]:
    active = json.loads(
        ACTIVE.read_text(encoding="utf-8")
    )
    identity = str(active["checkpoint_id"])

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


def prepare(
    feature_path: Path,
    label_path: Path,
    names: list[str],
) -> tuple[list[Sample], int]:
    labels: dict[tuple[str, int], str] = {}

    for row in load_csv(label_path):
        try:
            if int(row["horizon_seconds"]) != HORIZON:
                continue

            outcome = row["outcome"]
            if outcome not in LABELS:
                continue

            entry = int(row["entry_tick_msc"])
            exit_time = int(row["exit_tick_msc"])

            lag = exit_time - entry - HORIZON * 1000
            if not 0 <= lag <= 3000:
                continue

            key = (row["symbol"], entry)

            if key in labels:
                raise RuntimeError(
                    f"Duplicate label key: {key}"
                )

            labels[key] = outcome

        except (KeyError, ValueError, TypeError):
            continue

    raw_features = load_csv(feature_path)

    if not raw_features:
        raise RuntimeError("No feature rows")

    required = set(names) | {
        "symbol", "tick_server_msc"
    }

    absent = required - raw_features[0].keys()
    if absent:
        raise RuntimeError(
            f"Missing features: {sorted(absent)}"
        )

    raw_features.sort(
        key=lambda r: (
            int(r["tick_server_msc"]),
            r["symbol"],
        )
    )

    result: list[Sample] = []
    previous: dict[str, int] = {}
    seen: set[tuple[str, int]] = set()
    skipped = 0

    for row in raw_features:
        symbol = row["symbol"]
        timestamp = int(row["tick_server_msc"])
        key = (symbol, timestamp)

        if key in seen:
            raise RuntimeError(
                f"Duplicate feature timestamp: {key}"
            )

        seen.add(key)

        try:
            vector = np.asarray(
                [float(row[name]) for name in names],
                dtype=np.float64,
            )
            if not bool(np.all(np.isfinite(vector))):
                skipped += 1
                continue

        except (ValueError, TypeError):
            skipped += 1
            continue

        last = previous.get(symbol)

        if (
            last is not None
            and timestamp - last < SAMPLE_MS
        ):
            continue

        previous[symbol] = timestamp

        outcome = labels.get(key)
        if outcome is None:
            continue

        result.append(
            Sample(
                symbol=symbol,
                timestamp=timestamp,
                features=vector,
                outcome=outcome,
            )
        )

    return result, skipped


def matrix(
    rows: list[Sample],
) -> NDArray[np.float64]:
    return np.asarray(
        np.stack([r.features for r in rows]),
        dtype=np.float64,
    )


def outcome_array(
    rows: list[Sample],
) -> NDArray[np.str_]:
    return np.asarray(
        [r.outcome for r in rows],
        dtype=np.str_,
    )


def score(
    actual: NDArray[np.str_],
    predictions: NDArray[np.str_],
) -> dict[str, float]:
    truth = actual.tolist()
    predicted = predictions.tolist()

    n = len(truth)
    correct = sum(
        a == p for a, p in zip(truth, predicted)
    )

    recall: list[float] = []

    for label in LABELS:
        support = sum(a == label for a in truth)

        if support:
            hits = sum(
                a == label and p == label
                for a, p in zip(truth, predicted)
            )
            recall.append(hits / support)

    return {
        "accuracy": correct / n,
        "balanced_accuracy": (
            sum(recall) / len(recall)
            if recall else 0.0
        ),
    }


def fold_predict(
    train: list[Sample],
    test: list[Sample],
) -> dict[str, NDArray[np.str_]]:
    x_train = matrix(train)
    y_train = outcome_array(train)
    x_test = matrix(test)

    train_counts = Counter(y_train.tolist())
    majority = train_counts.most_common(1)[0][0]

    baseline: NDArray[np.str_] = np.asarray(
        [majority] * len(test),
        dtype=np.str_,
    )

    scaler = RobustScaler()
    transformed_train = np.asarray(
        scaler.fit_transform(x_train),
        dtype=np.float64,
    )
    transformed_test = np.asarray(
        scaler.transform(x_test),
        dtype=np.float64,
    )

    state_count = min(
        5, max(2, len(train) // 30)
    )

    clusters = KMeans(
        n_clusters=state_count,
        n_init="auto",
        random_state=42,
    )

    train_states = clusters.fit_predict(
        transformed_train
    )
    test_states = clusters.predict(
        transformed_test
    )

    state_labels: dict[int, Counter[str]] = (
        defaultdict(Counter)
    )

    for state, label in zip(
        train_states, y_train
    ):
        state_labels[int(state)][str(label)] += 1

    state_map = {
        state: counts.most_common(1)[0][0]
        for state, counts in state_labels.items()
        if sum(counts.values()) >= 5
    }

    # Unknown/low-support states fall back to
    # the TRAIN majority class, not future labels.
    state_predictions: NDArray[np.str_] = np.asarray(
        [
            state_map.get(int(s), majority)
            for s in test_states
        ],
        dtype=np.str_,
    )

    forest = RandomForestClassifier(
        n_estimators=150,
        max_depth=4,
        min_samples_leaf=8,
        class_weight="balanced",
        random_state=42,
        n_jobs=1,
    )

    forest.fit(x_train, y_train)

    challenger: NDArray[np.str_] = np.asarray(
        forest.predict(x_test),
        dtype=np.str_,
    )

    return {
        "BASELINE": baseline,
        "STATE_MODEL": state_predictions,
        "CHALLENGER_RF": challenger,
    }


def run() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--min-train",
        type=int,
        default=80,
    )
    parser.add_argument(
        "--min-test",
        type=int,
        default=20,
    )

    args = parser.parse_args()

    if args.min_train < 50 or args.min_test < 10:
        parser.error("Invalid minimum sample settings")

    print("PV_WALK_FORWARD=V4")
    print("TRADING_ENABLED=NO")
    print("CHECKPOINT_CHANGED=NO")

    identity, names = checkpoint_features()

    OUTPUT.mkdir(
        parents=True, exist_ok=True
    )

    with tempfile.TemporaryDirectory(
        prefix=".pv_walk_",
        dir=OUTPUT,
    ) as folder_name:
        folder = Path(folder_name)

        feature_copy, label_copy = snapshot_inputs(
            folder
        )

        samples, skipped = prepare(
            feature_copy, label_copy, names
        )

        print(f"CHECKPOINT_ID={identity}")
        print(f"FEATURE_DIMENSIONS={len(names)}")
        print(f"SAMPLED_DECISIONS={len(samples)}")
        print(f"SKIPPED_FEATURE_ROWS={skipped}")

        if len(samples) < args.min_train + args.min_test:
            print("STATUS=MORE_DATA_REQUIRED")
            return

        n = len(samples)

        # Expanding folds, never shuffled.
        # Each test region is later in time than
        # its associated training region.
        boundaries = (
            (0.55, 0.70),
            (0.70, 0.85),
            (0.85, 1.00),
        )

        reports: list[dict[str, Any]] = []
        prediction_rows: list[dict[str, Any]] = []

        for fold_number, (start_ratio, end_ratio) in enumerate(
            boundaries, start=1
        ):
            start_index = int(n * start_ratio)
            end_index = (
                n if end_ratio == 1.0
                else int(n * end_ratio)
            )

            test = samples[start_index:end_index]

            if not test:
                print(
                    f"FOLD_{fold_number}=SKIPPED_EMPTY"
                )
                continue

            test_start = test[0].timestamp

            # Train must end >=120s before test starts.
            train = [
                sample
                for sample in samples[:start_index]
                if (
                    sample.timestamp
                    < test_start - PURGE_MS
                )
            ]

            if (
                len(train) < args.min_train
                or len(test) < args.min_test
            ):
                print(
                    f"FOLD_{fold_number}="
                    "SKIPPED_INSUFFICIENT_DATA"
                )
                continue

            if len({
                item.outcome for item in train
            }) < 2:
                print(
                    f"FOLD_{fold_number}="
                    "SKIPPED_CLASS_DIVERSITY"
                )
                continue

            # No sample in training can have an
            # entry within the 120s embargo.
            assert (
                max(item.timestamp for item in train)
                < min(item.timestamp for item in test)
                - PURGE_MS
            )

            models = fold_predict(train, test)
            y_test = outcome_array(test)

            fold_result: dict[str, Any] = {
                "fold": fold_number,
                "train_count": len(train),
                "test_count": len(test),
                "train_last_msc": train[-1].timestamp,
                "test_first_msc": test[0].timestamp,
                "test_last_msc": test[-1].timestamp,
                "metrics": {},
            }

            for model_name, predictions in models.items():
                metrics = score(
                    y_test, predictions
                )

                fold_result["metrics"][
                    model_name
                ] = metrics

                for sample, predicted in zip(
                    test, predictions
                ):
                    prediction_rows.append({
                        "fold": fold_number,
                        "model": model_name,
                        "symbol": sample.symbol,
                        "timestamp_msc": sample.timestamp,
                        "actual": sample.outcome,
                        "predicted": str(predicted),
                        "correct": int(
                            sample.outcome == str(predicted)
                        ),
                        "date_utc": datetime.fromtimestamp(
                            sample.timestamp / 1000,
                            tz=timezone.utc,
                        ).date().isoformat(),
                    })

            reports.append(fold_result)

            print(
                f"\nFOLD={fold_number} "
                f"TRAIN={len(train)} "
                f"TEST={len(test)}"
            )

            for name, metric in fold_result["metrics"].items():
                print(
                    f"{name}_ACCURACY="
                    f"{metric['accuracy']:.2%} "
                    f"BALANCED="
                    f"{metric['balanced_accuracy']:.2%}"
                )

        if not reports:
            print("STATUS=NO_VALID_FOLDS")
            return

        # Aggregate pooled predictions on identical
        # TEST observations for all three methods.
        totals: dict[str, dict[str, Any]] = {}

        for model in (
            "BASELINE",
            "STATE_MODEL",
            "CHALLENGER_RF",
        ):
            subset = [
                r for r in prediction_rows
                if r["model"] == model
            ]

            truth: NDArray[np.str_] = np.asarray(
                [str(r["actual"]) for r in subset],
                dtype=np.str_,
            )

            predicted: NDArray[np.str_] = np.asarray(
                [str(r["predicted"]) for r in subset],
                dtype=np.str_,
            )

            totals[model] = {
                "samples": len(subset),
                **score(truth, predicted),
            }

        days = sorted({
            str(r["date_utc"])
            for r in prediction_rows
        })

        fingerprint = hashlib.sha256(
            (
                identity
                + sha256(feature_copy)
                + sha256(label_copy)
                + "WALK_FORWARD_V4"
            ).encode()
        ).hexdigest()[:16]

        destination = OUTPUT / fingerprint
        destination.mkdir(
            parents=True, exist_ok=True
        )

        report = {
            "schema": "PV_WALK_FORWARD_V4",
            "run_id": fingerprint,
            "checkpoint_id": identity,
            "created_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "source_feature_sha256": sha256(
                feature_copy
            ),
            "source_label_sha256": sha256(
                label_copy
            ),
            "purge_seconds": PURGE_MS // 1000,
            "horizon_seconds": HORIZON,
            "sample_interval_seconds": SAMPLE_MS // 1000,
            "test_dates_utc": days,
            "folds": reports,
            "aggregate": totals,
            "checkpoint_modified": False,
            "trading_enabled": False,
            "limitations": [
                "Existing data may have been inspected before",
                "Folds may occur within a single trading day",
                "Overlapping outcome windows remain dependent",
                "This does not measure actual trade profitability",
                "Different folds train fresh models",
                "This does not evaluate the original frozen champion",
                "No automatic model promotion",
            ],
        }

        (destination / "report.json").write_text(
            json.dumps(report, indent=2),
            encoding="utf-8",
        )

        with (
            destination / "predictions.csv"
        ).open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            fields = [
                "fold",
                "model",
                "symbol",
                "timestamp_msc",
                "actual",
                "predicted",
                "correct",
                "date_utc",
            ]
            writer = csv.DictWriter(
                handle, fieldnames=fields
            )
            writer.writeheader()
            writer.writerows(prediction_rows)

        print("\n=== WALK-FORWARD AGGREGATE ===")

        for name, result in totals.items():
            print(
                f"{name}_ACCURACY="
                f"{result['accuracy']:.2%}"
            )
            print(
                f"{name}_BALANCED_ACCURACY="
                f"{result['balanced_accuracy']:.2%}"
            )

        print(f"VALID_FOLDS={len(reports)}")
        print(f"TEST_DATES_UTC={days}")
        print(f"REPORT_DIRECTORY={destination}")
        print("PV_WALK_FORWARD_STATUS=PASS")
        print("CHECKPOINT_CHANGED=NO")
        print("MODEL_PROMOTED=NO")
        print("PROFITABILITY_PROVEN=NO")
        print("TRADING_ENABLED=NO")


if __name__ == "__main__":
    run()
