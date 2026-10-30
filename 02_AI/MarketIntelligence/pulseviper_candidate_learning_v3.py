
"""
PulseViper Candidate Learning V3
Research-only champion/challenger comparison.

- Uses frozen StableMemoryV2 checkpoint
- Trains challenger on chronological past only
- Evaluates on identical later observations
- Includes majority baseline
- Never promotes a model or trades

Dependencies: numpy, scikit-learn, joblib
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

import joblib
import numpy as np
from numpy.typing import NDArray
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "01_Data" / "VolumeMemory"
MEMORY = DATA / "StableMemoryV2"

FEATURE_FILE = DATA / "pattern_features_v1.csv"
LABEL_FILE = DATA / "reaction_outcomes_v1.csv"

ACTIVE = MEMORY / "active_checkpoint.json"
CHECKPOINTS = MEMORY / "checkpoints"
CANDIDATES = MEMORY / "CandidateLearningV3"

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
    time: int
    x: NDArray[np.float64]
    outcome: str


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024), b""
        ):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        return list(csv.DictReader(handle))


def copy_inputs(folder: Path) -> tuple[Path, Path]:
    copied = (
        folder / "features.csv",
        folder / "outcomes.csv",
    )
    originals = (FEATURE_FILE, LABEL_FILE)

    for _ in range(5):
        before = [
            (p.stat().st_size, p.stat().st_mtime_ns)
            for p in originals
        ]

        for src, dst in zip(originals, copied):
            shutil.copyfile(src, dst)

        after = [
            (p.stat().st_size, p.stat().st_mtime_ns)
            for p in originals
        ]

        if before == after:
            return copied

    raise RuntimeError(
        "Live data changed during copying; retry"
    )


def checkpoint() -> tuple[
    dict[str, Any], Any, Any
]:
    active = json.loads(
        ACTIVE.read_text(encoding="utf-8")
    )
    identity = str(active["checkpoint_id"])

    if (
        len(identity) != 16
        or any(
            c not in "0123456789abcdef"
            for c in identity
        )
    ):
        raise RuntimeError("Invalid checkpoint ID")

    folder = CHECKPOINTS / identity
    metadata: dict[str, Any] = json.loads(
        (folder / "metadata.json").read_text(
            encoding="utf-8"
        )
    )

    model_path = folder / "models.joblib"

    if (
        metadata["checkpoint_id"] != identity
        or digest(model_path)
        != metadata["model_sha256"]
    ):
        raise RuntimeError(
            "Checkpoint integrity mismatch"
        )

    # Only load trusted, locally generated joblib.
    models = joblib.load(model_path)

    return (
        metadata,
        models["scaler"],
        models["clusters"],
    )


def prepare(
    feature_path: Path,
    label_path: Path,
    names: list[str],
) -> list[Sample]:
    outcome_map: dict[tuple[str, int], str] = {}

    for row in read_csv(label_path):
        try:
            if int(row["horizon_seconds"]) != HORIZON:
                continue

            outcome = row["outcome"]

            if outcome not in LABELS:
                continue

            entry = int(row["entry_tick_msc"])
            exit_time = int(row["exit_tick_msc"])

            if not (
                entry + HORIZON * 1000
                <= exit_time
                <= entry + (HORIZON + 3) * 1000
            ):
                continue

            key = (row["symbol"], entry)

            if key in outcome_map:
                raise RuntimeError(
                    f"Duplicate label: {key}"
                )

            outcome_map[key] = outcome

        except (KeyError, TypeError, ValueError):
            continue

    selected: list[Sample] = []
    previous: dict[str, int] = {}
    seen: set[tuple[str, int]] = set()

    for row in sorted(
        read_csv(feature_path),
        key=lambda r: int(r["tick_server_msc"]),
    ):
        try:
            symbol = row["symbol"]
            time = int(row["tick_server_msc"])
            key = (symbol, time)

            if key in seen:
                raise RuntimeError(
                    f"Duplicate feature: {key}"
                )

            seen.add(key)

            x = np.asarray(
                [float(row[name]) for name in names],
                dtype=np.float64,
            )

            if not bool(np.all(np.isfinite(x))):
                continue

            last = previous.get(symbol)

            # Match StableMemoryV2 sampling:
            # sampling occurs before label filtering.
            if (
                last is not None
                and time - last < SAMPLE_MS
            ):
                continue

            previous[symbol] = time

            outcome = outcome_map.get(key)

            if outcome is None:
                continue

            selected.append(
                Sample(symbol, time, x, outcome)
            )

        except (KeyError, ValueError, TypeError):
            continue

    return selected


def matrix(rows: list[Sample]) -> NDArray[np.float64]:
    return np.asarray(
        np.stack([s.x for s in rows]),
        dtype=np.float64,
    )


def evaluate(
    truth: NDArray[np.str_],
    predicted: NDArray[np.str_],
) -> dict[str, float]:
    return {
        "accuracy": float(
            accuracy_score(truth, predicted)
        ),
        "balanced_accuracy": float(
            balanced_accuracy_score(
                truth, predicted
            )
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--minimum-test",
        type=int,
        default=30,
    )
    args = parser.parse_args()

    if args.minimum_test < 10:
        parser.error(
            "--minimum-test must be >= 10"
        )

    print("PV_CANDIDATE_LEARNING=V3")
    print("CHAMPION_CHANGED=NO")
    print("TRADING_ENABLED=NO")

    metadata, scaler, clusters = checkpoint()

    identity = str(metadata["checkpoint_id"])
    names = list(metadata["feature_names"])

    if len(set(names)) != len(names):
        raise RuntimeError(
            "Duplicate checkpoint feature names"
        )

    CANDIDATES.mkdir(
        parents=True, exist_ok=True
    )

    with tempfile.TemporaryDirectory(
        prefix=".candidate_",
        dir=CANDIDATES,
    ) as folder_name:
        folder = Path(folder_name)

        feature_copy, label_copy = copy_inputs(folder)

        all_rows = prepare(
            feature_copy,
            label_copy,
            names,
        )

        train_end = int(metadata["train_end"])
        holdout = int(
            metadata["holdout_boundary"]
        )
        purge = max(
            PURGE_MS,
            int(metadata["purge_ms"]),
        )

        train = [
            s for s in all_rows
            if s.time <= train_end
        ]

        test = [
            s for s in all_rows
            if s.time >= holdout + purge
        ]

        print(f"CHECKPOINT_ID={identity}")
        print(f"ALIGNED_SAMPLES={len(all_rows)}")
        print(f"TRAIN_SAMPLES={len(train)}")
        print(f"TEST_SAMPLES={len(test)}")

        if (
            len(train) < 60
            or len(test) < args.minimum_test
        ):
            print("STATUS=MORE_DATA_REQUIRED")
            return

        x_train = matrix(train)
        x_test = matrix(test)

        y_train: NDArray[np.str_] = np.asarray(
            [s.outcome for s in train],
            dtype=np.str_,
        )
        y_test: NDArray[np.str_] = np.asarray(
            [s.outcome for s in test],
            dtype=np.str_,
        )

        if len(set(y_train.tolist())) < 2:
            print("STATUS=INSUFFICIENT_CLASS_DIVERSITY")
            return

        # Champion market states stay frozen.
        train_states = clusters.predict(
            scaler.transform(x_train)
        )
        test_states = clusters.predict(
            scaler.transform(x_test)
        )

        train_outcomes = Counter(y_train.tolist())
        majority = train_outcomes.most_common(1)[0][0]

        state_labels: dict[int, Counter[str]] = (
            defaultdict(Counter)
        )

        for state, label in zip(
            train_states, y_train
        ):
            state_labels[int(state)][str(label)] += 1

        champion_map = {
            state: counts.most_common(1)[0][0]
            for state, counts in state_labels.items()
            if sum(counts.values()) >= 5
        }

        # Same test subset for all models.
        eligible_indices = [
            index
            for index, state in enumerate(test_states)
            if int(state) in champion_map
        ]

        print(
            f"COMMON_TEST_SAMPLES={len(eligible_indices)}"
        )

        if len(eligible_indices) < args.minimum_test:
            print("STATUS=INSUFFICIENT_COMMON_TEST")
            return

        # Challenger learns labels ONLY from train.
        challenger = RandomForestClassifier(
            n_estimators=150,
            max_depth=4,
            min_samples_leaf=8,
            class_weight="balanced",
            random_state=42,
            n_jobs=1,
        )

        challenger.fit(x_train, y_train)

        x_common = x_test[eligible_indices]
        y_common = y_test[eligible_indices]

        champion_pred: NDArray[np.str_] = np.asarray(
            [
                champion_map[int(test_states[i])]
                for i in eligible_indices
            ],
            dtype=np.str_,
        )

        challenger_pred: NDArray[np.str_] = np.asarray(
            challenger.predict(x_common),
            dtype=np.str_,
        )

        baseline_pred: NDArray[np.str_] = np.asarray(
            [majority] * len(eligible_indices),
            dtype=np.str_,
        )

        results = {
            "champion": evaluate(
                y_common, champion_pred
            ),
            "challenger": evaluate(
                y_common, challenger_pred
            ),
            "baseline": evaluate(
                y_common, baseline_pred
            ),
        }

        fingerprint = hashlib.sha256(
            (
                identity
                + digest(feature_copy)
                + digest(label_copy)
                + "CANDIDATE_V3_RF150"
            ).encode()
        ).hexdigest()[:16]

        destination = CANDIDATES / fingerprint

        report = {
            "schema": "PV_CANDIDATE_V3",
            "checkpoint_id": identity,
            "candidate_id": fingerprint,
            "created_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "horizon_seconds": HORIZON,
            "training_samples": len(train),
            "test_samples": len(test),
            "common_test_samples": len(
                eligible_indices
            ),
            "results": results,
            "feature_sha256": digest(
                feature_copy
            ),
            "label_sha256": digest(
                label_copy
            ),
            "warnings": [
                "Previously examined holdout: not independent",
                "Overlapping labels; small market history",
                "No transaction-cost profitability test",
                "No automatic model promotion",
            ],
            "model_promoted": False,
            "trading_enabled": False,
        }

        report_path = folder / "comparison.json"
        report_path.write_text(
            json.dumps(report, indent=2),
            encoding="utf-8",
        )

        # Preserve challenger separately.
        # Never overwrite champion checkpoint.
        joblib.dump(
            {
                "model": challenger,
                "feature_names": names,
                "champion_checkpoint": identity,
            },
            folder / "challenger.joblib",
        )

        with (
            folder / "test_predictions.csv"
        ).open(
            "w",
            newline="",
            encoding="utf-8",
        ) as handle:
            writer = csv.writer(handle)
            writer.writerow([
                "symbol",
                "timestamp_msc",
                "actual",
                "champion",
                "challenger",
                "baseline",
            ])

            for position, index in enumerate(
                eligible_indices
            ):
                sample = test[index]
                writer.writerow([
                    sample.symbol,
                    sample.time,
                    str(y_common[position]),
                    str(champion_pred[position]),
                    str(challenger_pred[position]),
                    str(baseline_pred[position]),
                ])

        # Publish a complete candidate directory.
        if destination.exists():
            print("CANDIDATE_ALREADY_EXISTS=YES")
        else:
            os.rename(folder, destination)

        for name, metric in results.items():
            prefix = name.upper()
            print(
                f"{prefix}_ACCURACY="
                f"{metric['accuracy']:.2%}"
            )
            print(
                f"{prefix}_BALANCED_ACCURACY="
                f"{metric['balanced_accuracy']:.2%}"
            )

        print(f"CANDIDATE_ID={fingerprint}")
        print(f"CANDIDATE_DIRECTORY={destination}")
        print("EVALUATION=EXPLORATORY_ONLY")
        print("AUTO_PROMOTION=NO")
        print("CHAMPION_CHANGED=NO")
        print("PV_CANDIDATE_STATUS=PASS")
        print("TRADING_ENABLED=NO")


if __name__ == "__main__":
    main()
