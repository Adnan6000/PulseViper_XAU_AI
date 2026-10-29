
"""
PulseViper Quantum Brain - Stable Memory V2
===========================================

Frozen, versioned market-state intelligence.

Features:
- Consistent input snapshots
- Chronological initial fitting
- Persistent scaler/KMeans/anomaly detector
- Frozen state identities across refreshes
- 15-second market observations
- State transitions and anomaly memory
- Later-period 60s reaction evaluation
- Versioned output runs

Research only. No trades, no model deployment.

Dependencies:
    numpy
    scikit-learn
    joblib
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
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "01_Data" / "VolumeMemory"

FEATURES = DATA / "pattern_features_v1.csv"
LABELS = DATA / "reaction_outcomes_v1.csv"

MEMORY = DATA / "StableMemoryV2"
CHECKPOINTS = MEMORY / "checkpoints"
RUNS = MEMORY / "runs"
ACTIVE = MEMORY / "active_checkpoint.json"

HORIZON = 60
SAMPLE_MS = 15_000
PURGE_MS = 120_000
MAX_TRANSITION_GAP_MS = 45_000

FEATURE_NAMES = (
    "buy_pct_est",
    "delta_pp_est",
    "spread_price",
    "distance_to_poc",
    "distance_to_vah",
    "distance_to_val",
    "profile_concentration",
    "near_price_volume_share",
    "price_bin_volume_share",
    "buy_50_crossover",
    "w10_buy_change_pp",
    "w10_delta_change_pp",
    "w10_price_change",
    "w10_poc_change",
    "w10_profile_l1",
    "w10_green_l1",
    "w10_red_l1",
    "w10_profile_overlap",
    "w10_near_price_volume_change",
    "w30_delta_change_pp",
    "w30_price_change",
    "w30_poc_change",
    "w30_profile_l1",
    "w30_green_l1",
    "w30_red_l1",
    "w60_delta_change_pp",
    "w60_price_change",
    "w60_poc_change",
    "w60_profile_l1",
    "w60_green_l1",
    "w60_red_l1",
    "pressure_acceleration_10s",
)

OUTCOMES = (
    "BUY_POSITIVE",
    "SELL_POSITIVE",
    "NEITHER_POSITIVE",
)


@dataclass(frozen=True)
class Snapshot:
    symbol: str
    time: int
    vector: NDArray[np.float64]
    mid: float
    buy_pct: float
    poc: float


@dataclass(frozen=True)
class StateEvent:
    symbol: str
    time: int
    split: str
    state: int
    previous_state: int | None
    transition: str
    anomaly: float
    unusual: bool
    outcome: str
    mid: float
    buy_pct: float
    poc: float


def sha256(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1048576), b""
        ):
            h.update(block)

    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        return list(csv.DictReader(handle))


def copy_inputs(directory: Path) -> tuple[Path, Path]:
    first = directory / "features.csv"
    second = directory / "labels.csv"

    for _ in range(5):
        before = tuple(
            (p.stat().st_size, p.stat().st_mtime_ns)
            for p in (FEATURES, LABELS)
        )

        shutil.copyfile(FEATURES, first)
        shutil.copyfile(LABELS, second)

        after = tuple(
            (p.stat().st_size, p.stat().st_mtime_ns)
            for p in (FEATURES, LABELS)
        )

        if before == after:
            return first, second

    raise RuntimeError(
        "Input changed during copying. Retry."
    )


def parse_features(path: Path) -> list[Snapshot]:
    rows = read_csv(path)
    if not rows:
        raise RuntimeError("Empty feature dataset")

    missing = set(FEATURE_NAMES) - set(rows[0])

    if missing:
        raise RuntimeError(
            f"Missing columns: {sorted(missing)}"
        )

    collected: dict[
        tuple[str, int], Snapshot
    ] = {}

    for row in rows:
        try:
            vector = np.asarray(
                [float(row[k]) for k in FEATURE_NAMES],
                dtype=np.float64,
            )

            if not bool(np.all(np.isfinite(vector))):
                continue

            symbol = row["symbol"]
            time = int(row["tick_server_msc"])

            bid = float(row["bid"])
            ask = float(row["ask"])

            if (
                not symbol
                or time <= 0
                or ask < bid
                or bid <= 0
            ):
                continue

            collected[(symbol, time)] = Snapshot(
                symbol=symbol,
                time=time,
                vector=vector,
                mid=(bid + ask) / 2,
                buy_pct=float(row["buy_pct_est"]),
                poc=float(row["poc_price"]),
            )

        except (ValueError, TypeError, KeyError):
            continue

    snapshots = sorted(
        collected.values(),
        key=lambda r: (r.time, r.symbol),
    )

    # Sample separately by symbol.
    selected: list[Snapshot] = []
    previous: dict[str, int] = {}

    for row in snapshots:
        last = previous.get(row.symbol)

        if last is None or row.time - last >= SAMPLE_MS:
            selected.append(row)
            previous[row.symbol] = row.time

    return selected


def read_labels(
    path: Path,
) -> dict[tuple[str, int], str]:
    result: dict[tuple[str, int], str] = {}

    for row in read_csv(path):
        try:
            if int(row["horizon_seconds"]) != HORIZON:
                continue

            label = row["outcome"]

            if label not in OUTCOMES:
                continue

            result[(
                row["symbol"],
                int(row["entry_tick_msc"]),
            )] = label

        except (ValueError, TypeError, KeyError):
            continue

    return result


def to_matrix(
    rows: list[Snapshot],
) -> NDArray[np.float64]:
    return np.asarray(
        np.stack([r.vector for r in rows]),
        dtype=np.float64,
    )


def save_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2),
        encoding="utf-8",
    )


def initialize(
    records: list[Snapshot],
) -> dict[str, Any]:
    if ACTIVE.exists():
        raise RuntimeError(
            "Active checkpoint already exists. "
            "Do not overwrite learned state identities."
        )

    if len(records) < 100:
        raise RuntimeError(
            "At least 100 sampled observations required"
        )

    first = records[0].time
    last = records[-1].time

    boundary = first + int(
        (last - first) * 0.70
    )

    train = [
        r for r in records
        if r.time < boundary - PURGE_MS
    ]

    if len(train) < 60:
        raise RuntimeError(
            "Insufficient chronological training data"
        )

    x_train = to_matrix(train)

    scaler = RobustScaler()
    normalized = np.asarray(
        scaler.fit_transform(x_train),
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

    clusters.fit(normalized)

    anomalies = IsolationForest(
        n_estimators=100,
        contamination="auto",
        random_state=42,
        n_jobs=1,
    )

    anomalies.fit(normalized)

    identity = hashlib.sha256(
        (
            str(boundary)
            + str(first)
            + str(last)
            + "|".join(FEATURE_NAMES)
            + str(state_count)
        ).encode()
    ).hexdigest()[:16]

    checkpoint = CHECKPOINTS / identity

    if checkpoint.exists():
        raise RuntimeError(
            "Checkpoint directory already exists; "
            "inspect before initializing again."
        )

    CHECKPOINTS.mkdir(
        parents=True, exist_ok=True
    )

    with tempfile.TemporaryDirectory(
        prefix=".checkpoint_",
        dir=CHECKPOINTS,
    ) as folder:
        staging = Path(folder)

        model_file = staging / "models.joblib"

        joblib.dump(
            {
                "scaler": scaler,
                "clusters": clusters,
                "anomalies": anomalies,
            },
            model_file,
        )

        metadata: dict[str, Any] = {
            "schema": "PV_STABLE_MEMORY_V2",
            "checkpoint_id": identity,
            "created_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "feature_names": list(FEATURE_NAMES),
            "feature_dimensions": len(FEATURE_NAMES),
            "train_start": first,
            "train_end": max(
                r.time for r in train
            ),
            "holdout_boundary": boundary,
            "purge_ms": PURGE_MS,
            "train_samples": len(train),
            "market_states": state_count,
            "model_sha256": sha256(model_file),
            "training_labels_used": False,
            "trading_enabled": False,
        }

        save_json(
            staging / "metadata.json",
            metadata,
        )

        os.rename(staging, checkpoint)

    # Publish checkpoint pointer last.
    pointer_temp = MEMORY / ".active_tmp.json"

    save_json(
        pointer_temp,
        {"checkpoint_id": identity},
    )

    os.replace(pointer_temp, ACTIVE)

    print("PV_MODEL_CHECKPOINT_CREATED=YES")
    print(f"CHECKPOINT_ID={identity}")
    print(f"TRAIN_SAMPLES={len(train)}")
    print(f"MARKET_STATES={state_count}")

    return metadata


def load_checkpoint() -> tuple[
    dict[str, Any],
    RobustScaler,
    KMeans,
    IsolationForest,
]:
    if not ACTIVE.is_file():
        raise RuntimeError(
            "No active checkpoint. Run --init first."
        )

    pointer = json.loads(
        ACTIVE.read_text(encoding="utf-8")
    )

    identity = str(pointer["checkpoint_id"])

    if not (
        len(identity) == 16
        and all(c in "0123456789abcdef" for c in identity)
    ):
        raise RuntimeError("Invalid checkpoint ID")

    directory = CHECKPOINTS / identity

    metadata: dict[str, Any] = json.loads(
        (directory / "metadata.json").read_text(
            encoding="utf-8"
        )
    )

    if (
        metadata["checkpoint_id"] != identity
        or tuple(metadata["feature_names"]) != FEATURE_NAMES
    ):
        raise RuntimeError(
            "Checkpoint identity/schema mismatch"
        )

    model_path = directory / "models.joblib"

    if sha256(model_path) != metadata["model_sha256"]:
        raise RuntimeError(
            "Model integrity verification failed"
        )

    # Load only locally generated, trusted checkpoints.
    models = joblib.load(model_path)

    return (
        metadata,
        models["scaler"],
        models["clusters"],
        models["anomalies"],
    )


def classify(
    records: list[Snapshot],
    labels: dict[tuple[str, int], str],
    metadata: dict[str, Any],
    scaler: RobustScaler,
    clusters: KMeans,
    anomalies: IsolationForest,
) -> list[StateEvent]:
    matrix = to_matrix(records)

    normalized = np.asarray(
        scaler.transform(matrix),
        dtype=np.float64,
    )

    states = clusters.predict(normalized)

    scores = anomalies.decision_function(
        normalized
    )

    train_end = int(metadata["train_end"])
    boundary = int(
        metadata["holdout_boundary"]
    )

    previous: dict[
        str, tuple[int, int]
    ] = {}

    events: list[StateEvent] = []

    for row, state_raw, score_raw in zip(
        records, states, scores
    ):
        state = int(state_raw)
        score = float(score_raw)

        if row.time <= train_end:
            split = "TRAIN"
        elif row.time < boundary + PURGE_MS:
            split = "EMBARGO"
        else:
            split = "TEST"

        old = previous.get(row.symbol)

        previous_state: int | None = None
        transition = ""

        if old is not None:
            prior_time, prior_state = old

            if (
                0 < row.time - prior_time
                <= MAX_TRANSITION_GAP_MS
            ):
                previous_state = prior_state
                transition = (
                    f"{prior_state}>{state}"
                )

        previous[row.symbol] = (
            row.time, state
        )

        events.append(
            StateEvent(
                symbol=row.symbol,
                time=row.time,
                split=split,
                state=state,
                previous_state=previous_state,
                transition=transition,
                anomaly=score,
                unusual=score < 0,
                outcome=labels.get(
                    (row.symbol, row.time),
                    "",
                ),
                mid=row.mid,
                buy_pct=row.buy_pct,
                poc=row.poc,
            )
        )

    return events


def save_events(
    path: Path,
    events: list[StateEvent],
    identity: str,
) -> None:
    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.writer(handle)

        writer.writerow([
            "checkpoint_id",
            "symbol",
            "timestamp_msc",
            "split",
            "market_state",
            "previous_state",
            "transition",
            "anomaly_score",
            "unusual",
            "outcome_60s",
            "mid_price",
            "buy_pct_est",
            "poc_price",
        ])

        for e in events:
            writer.writerow([
                identity,
                e.symbol,
                e.time,
                e.split,
                e.state,
                (
                    e.previous_state
                    if e.previous_state is not None
                    else ""
                ),
                e.transition,
                round(e.anomaly, 6),
                int(e.unusual),
                e.outcome,
                e.mid,
                e.buy_pct,
                e.poc,
            ])


def evaluate(
    events: list[StateEvent],
) -> dict[str, Any]:
    train_counts: dict[
        int, Counter[str]
    ] = defaultdict(Counter)

    for e in events:
        if e.split == "TRAIN" and e.outcome:
            train_counts[e.state][e.outcome] += 1

    training_base = Counter(
        e.outcome
        for e in events
        if e.split == "TRAIN" and e.outcome
    )

    if not training_base:
        return {
            "status": "INSUFFICIENT_TRAIN_LABELS"
        }

    baseline = training_base.most_common(1)[0][0]

    test = [
        e for e in events
        if e.split == "TEST" and e.outcome
    ]

    if not test:
        return {
            "status": "INSUFFICIENT_TEST_LABELS"
        }

    # Only make a state-level prediction when
    # the state has minimum TRAIN label support.
    eligible = {
        state: counts.most_common(1)[0][0]
        for state, counts in train_counts.items()
        if sum(counts.values()) >= 5
    }

    covered = [
        e for e in test
        if e.state in eligible
    ]

    per_state: list[dict[str, Any]] = []

    for state in sorted(
        {e.state for e in test}
    ):
        group = [
            e for e in test
            if e.state == state
        ]

        counts = Counter(
            e.outcome for e in group
        )

        per_state.append({
            "state": state,
            "test_samples": len(group),
            "actual_outcomes": dict(counts),
            "train_support": sum(
                train_counts[state].values()
            ),
            "train_predicted_outcome": (
                eligible.get(state)
            ),
        })

    correct = sum(
        e.outcome == eligible[e.state]
        for e in covered
    )

    baseline_correct = sum(
        e.outcome == baseline
        for e in covered
    )

    return {
        "status": "EXPLORATORY",
        "test_labeled_events": len(test),
        "covered_test_events": len(covered),
        "coverage": (
            len(covered) / len(test)
        ),
        "state_accuracy": (
            correct / len(covered)
            if covered else None
        ),
        "baseline_same_events": (
            baseline_correct / len(covered)
            if covered else None
        ),
        "baseline_class": baseline,
        "per_state": per_state,
        "overlapping_outcomes": True,
        "profitability_proven": False,
    }


def run() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--init",
        action="store_true",
        help="Create frozen checkpoint once",
    )

    args = parser.parse_args()

    MEMORY.mkdir(
        parents=True, exist_ok=True
    )

    RUNS.mkdir(
        parents=True, exist_ok=True
    )

    with tempfile.TemporaryDirectory(
        prefix=".inputs_",
        dir=MEMORY,
    ) as temp:
        copied_features, copied_labels = (
            copy_inputs(Path(temp))
        )

        records = parse_features(
            copied_features
        )

        labels = read_labels(
            copied_labels
        )

        print("PV_STABLE_MEMORY=V2")
        print(f"SAMPLED_OBSERVATIONS={len(records)}")
        print(f"ALIGNED_LABELS={len(labels)}")

        if len(records) < 100:
            print("STATUS=MORE_DATA_REQUIRED")
            return

        if args.init:
            initialize(records)

        (
            metadata,
            scaler,
            clusters,
            anomalies,
        ) = load_checkpoint()

        identity = str(
            metadata["checkpoint_id"]
        )

        events = classify(
            records,
            labels,
            metadata,
            scaler,
            clusters,
            anomalies,
        )

        assessment = evaluate(events)

        fingerprint = hashlib.sha256(
            (
                identity
                + sha256(copied_features)
                + sha256(copied_labels)
            ).encode()
        ).hexdigest()[:16]

        run_dir = RUNS / fingerprint

        if run_dir.exists():
            print("RUN_ALREADY_EXISTS=YES")
        else:
            with tempfile.TemporaryDirectory(
                prefix=".run_",
                dir=RUNS,
            ) as staging_name:
                staging = Path(staging_name)

                save_events(
                    staging / "market_states.csv",
                    events,
                    identity,
                )

                save_json(
                    staging / "evaluation.json",
                    assessment,
                )

                save_json(
                    staging / "run_manifest.json",
                    {
                        "schema": "PV_STABLE_RUN_V2",
                        "run_id": fingerprint,
                        "checkpoint_id": identity,
                        "features_sha256": sha256(
                            copied_features
                        ),
                        "labels_sha256": sha256(
                            copied_labels
                        ),
                        "created_utc": datetime.now(
                            timezone.utc
                        ).isoformat(),
                        "state_ids_frozen": True,
                        "training_enabled": False,
                        "trading_enabled": False,
                    },
                )

                os.rename(
                    staging,
                    run_dir,
                )

        state_counts = Counter(
            e.state for e in events
        )

        unusual_count = sum(
            e.unusual for e in events
        )

        transitions = sum(
            bool(e.transition) for e in events
        )

        print(f"CHECKPOINT_ID={identity}")
        print("STATE_IDS_FROZEN=YES")
        print(
            f"MARKET_STATE_COUNTS={dict(state_counts)}"
        )
        print(
            f"UNUSUAL_OBSERVATIONS={unusual_count}"
        )
        print(
            f"VALID_TRANSITIONS={transitions}"
        )

        print(
            f"EVALUATION_STATUS="
            f"{assessment['status']}"
        )

        if assessment["status"] == "EXPLORATORY":
            coverage = float(
                assessment["coverage"]
            )

            accuracy = assessment[
                "state_accuracy"
            ]

            baseline = assessment[
                "baseline_same_events"
            ]

            print(
                f"TEST_COVERAGE={coverage:.2%}"
            )

            if accuracy is not None:
                print(
                    f"STATE_ACCURACY={accuracy:.2%}"
                )
                print(
                    f"BASELINE_SAME_EVENTS="
                    f"{baseline:.2%}"
                )

        print(f"MEMORY_RUN={run_dir}")
        print("PV_STABLE_MEMORY_STATUS=PASS")
        print("MODEL_DEPLOYED=NO")
        print("PROFITABILITY_PROVEN=NO")
        print("TRADING_ENABLED=NO")


if __name__ == "__main__":
    run()
