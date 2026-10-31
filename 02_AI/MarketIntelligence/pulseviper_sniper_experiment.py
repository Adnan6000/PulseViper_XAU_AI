
"""
PulseViper Sniper Experiment V0.1

Fixes:
- Explicit NumPy arrays for sklearn / Pylance.
- Chronological diagnostic split.
- 120-second embargo around split boundary.
- Majority-class baseline comparison.
- No model saved, no trades.

Research-only diagnostic, not validated profitability.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import Counter
from pathlib import Path
from typing import NamedTuple

import numpy as np
from numpy.typing import NDArray
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "01_Data" / "VolumeMemory"

FEATURES_FILE = DATA / "pattern_features_v1.csv"
LABELS_FILE = DATA / "reaction_outcomes_v1.csv"

HORIZON_SECONDS = 60
SAMPLE_INTERVAL_MS = 15_000
EMBARGO_MS = 120_000

LABELS = (
    "BUY_POSITIVE",
    "SELL_POSITIVE",
    "NEITHER_POSITIVE",
)

EXCLUDED = {
    "symbol",
    "tick_server_msc",
    "bid",
    "ask",
}


class Sample(NamedTuple):
    timestamp: int
    values: list[float]
    label: str


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        return list(csv.DictReader(handle))


def prepare_samples() -> tuple[list[Sample], list[str]]:
    feature_rows = read_csv(FEATURES_FILE)
    label_rows = read_csv(LABELS_FILE)

    if not feature_rows:
        raise RuntimeError("Feature dataset is empty")

    feature_names = [
        name
        for name in feature_rows[0]
        if name not in EXCLUDED
    ]

    outcomes: dict[tuple[str, int], str] = {}

    for row in label_rows:
        try:
            if int(row["horizon_seconds"]) != HORIZON_SECONDS:
                continue

            label = row["outcome"]

            if label not in LABELS:
                continue

            key = (
                row["symbol"],
                int(row["entry_tick_msc"]),
            )

            outcomes[key] = label

        except (KeyError, TypeError, ValueError):
            continue

    collected: list[Sample] = []

    for row in feature_rows:
        try:
            timestamp = int(row["tick_server_msc"])
            key = (row["symbol"], timestamp)

            label = outcomes.get(key)

            if label is None:
                continue

            vector: list[float] = []

            for name in feature_names:
                value = row.get(name, "")

                if value is None or value == "":
                    raise ValueError("Missing feature history")

                number = float(value)

                if not math.isfinite(number):
                    raise ValueError("Nonfinite feature")

                vector.append(number)

            collected.append(
                Sample(timestamp, vector, label)
            )

        except (KeyError, TypeError, ValueError):
            continue

    collected.sort(key=lambda item: item.timestamp)

    # Keep decisions separated by at least 15 seconds.
    # Observations may still be statistically dependent.
    selected: list[Sample] = []
    previous_time = -10**30

    for sample in collected:
        if sample.timestamp - previous_time >= SAMPLE_INTERVAL_MS:
            selected.append(sample)
            previous_time = sample.timestamp

    return selected, feature_names


def to_arrays(
    samples: list[Sample],
) -> tuple[NDArray[np.float64], NDArray[np.str_]]:
    x: NDArray[np.float64] = np.asarray(
        [sample.values for sample in samples],
        dtype=np.float64,
    )

    y: NDArray[np.str_] = np.asarray(
        [sample.label for sample in samples],
        dtype=np.str_,
    )

    return x, y


def chronological_split(
    samples: list[Sample],
    diagnostic: bool,
) -> tuple[list[Sample], list[Sample], list[Sample]]:
    start = samples[0].timestamp
    end = samples[-1].timestamp
    span = end - start

    if diagnostic:
        # A small-data engineering check:
        # 70% history for training, 30% for testing.
        cut = start + int(span * 0.70)

        train = [
            s for s in samples
            if s.timestamp < cut - EMBARGO_MS
        ]

        test = [
            s for s in samples
            if s.timestamp >= cut + EMBARGO_MS
        ]

        return train, [], test

    # Larger-data research split:
    # 60% train, 20% validation, 20% test.
    train_cut = start + int(span * 0.60)
    test_cut = start + int(span * 0.80)

    train = [
        s for s in samples
        if s.timestamp < train_cut - EMBARGO_MS
    ]

    validation = [
        s for s in samples
        if (
            train_cut + EMBARGO_MS <= s.timestamp
            < test_cut - EMBARGO_MS
        )
    ]

    test = [
        s for s in samples
        if s.timestamp >= test_cut + EMBARGO_MS
    ]

    return train, validation, test


def evaluate(
    name: str,
    predictions: NDArray[np.str_],
    truth: NDArray[np.str_],
) -> None:
    print(f"\nMODEL={name}")

    print(
        "ACCURACY=",
        round(float(accuracy_score(truth, predictions)), 4),
    )

    print(
        "BALANCED_ACCURACY=",
        round(
            float(
                balanced_accuracy_score(
                    truth, predictions
                )
            ),
            4,
        ),
    )

    print(
        "PREDICTION_COUNTS=",
        dict(Counter(predictions.tolist())),
    )

    print(
        "ACTUAL_COUNTS=",
        dict(Counter(truth.tolist())),
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--diagnostic",
        action="store_true",
        help="Engineering check using a 2-way time split",
    )

    args = parser.parse_args()

    samples, columns = prepare_samples()

    print("PV_SNIPER_EXPERIMENT=V0.1")
    print(f"FEATURE_COLUMNS={len(columns)}")
    print(f"SAMPLED_DECISIONS={len(samples)}")

    if len(samples) < 30:
        print("STATUS=INSUFFICIENT_SAMPLES")
        print("TRADING_ENABLED=NO")
        return

    span_minutes = (
        samples[-1].timestamp - samples[0].timestamp
    ) / 60_000

    print(
        f"OBSERVED_SPAN_MINUTES={span_minutes:.2f}"
    )

    if not args.diagnostic and span_minutes < 300:
        print("STATUS=MORE_DATA_REQUIRED")
        print("TIP=Run with --diagnostic")
        print("TRADING_ENABLED=NO")
        return

    train, validation, test = chronological_split(
        samples,
        diagnostic=args.diagnostic,
    )

    print(
        "SPLIT_MODE=" +
        ("TWO_WAY_DIAGNOSTIC"
         if args.diagnostic
         else "THREE_WAY_RESEARCH")
    )

    print(f"TRAIN_SAMPLES={len(train)}")
    print(f"VALIDATION_SAMPLES={len(validation)}")
    print(f"TEST_SAMPLES={len(test)}")
    print(f"EMBARGO_SECONDS={EMBARGO_MS // 1000}")

    minimum = 10 if args.diagnostic else 30

    if len(train) < minimum or len(test) < minimum:
        print("STATUS=INSUFFICIENT_SPLIT_DATA")
        print("TRADING_ENABLED=NO")
        return

    if not args.diagnostic and len(validation) < 30:
        print("STATUS=INSUFFICIENT_VALIDATION_DATA")
        print("TRADING_ENABLED=NO")
        return

    x_train, y_train = to_arrays(train)
    x_test, y_test = to_arrays(test)

    print("TRAIN_CLASS_COUNTS=", dict(Counter(y_train.tolist())))
    print("TEST_CLASS_COUNTS=", dict(Counter(y_test.tolist())))

    if len(set(y_train.tolist())) < 2:
        print("STATUS=INSUFFICIENT_CLASS_DIVERSITY")
        print("TRADING_ENABLED=NO")
        return

    baseline = DummyClassifier(
        strategy="most_frequent"
    )

    forest = RandomForestClassifier(
        n_estimators=100,
        max_depth=4,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=1,
    )

    baseline.fit(x_train, y_train)
    forest.fit(x_train, y_train)

    baseline_predictions: NDArray[np.str_] = np.asarray(
        baseline.predict(x_test),
        dtype=np.str_,
    )

    forest_predictions: NDArray[np.str_] = np.asarray(
        forest.predict(x_test),
        dtype=np.str_,
    )

    evaluate(
        "MAJORITY_BASELINE",
        baseline_predictions,
        y_test,
    )

    evaluate(
        "RANDOM_FOREST",
        forest_predictions,
        y_test,
    )

    print("\nSTATUS=DIAGNOSTIC_ONLY" if args.diagnostic
          else "\nSTATUS=RESEARCH_EXPERIMENT_ONLY")
    print("MODEL_SAVED=NO")
    print("PROFITABILITY_PROVEN=NO")
    print("TRADING_ENABLED=NO")


if __name__ == "__main__":
    main()
