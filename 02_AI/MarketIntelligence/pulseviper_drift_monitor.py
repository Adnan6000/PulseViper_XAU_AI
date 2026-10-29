
"""
PulseViper Quantum Brain - Drift Monitor V1

Read-only monitoring of a frozen StableMemoryV2 checkpoint.

Checks:
- State distribution drift (Jensen-Shannon divergence)
- Anomaly frequency changes
- State transitions
- State-based outcome accuracy vs majority baseline
- Recent performance compared with checkpoint training

No retraining, model changes, order placement or trading.

Python standard library only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "01_Data" / "VolumeMemory" / "StableMemoryV2"
ACTIVE = MEMORY / "active_checkpoint.json"
RUNS = MEMORY / "runs"
CHECKPOINTS = MEMORY / "checkpoints"
REPORTS = MEMORY / "DriftReports"

VERSION = "PV_DRIFT_MONITOR_V1"
MAX_GAP_MS = 45_000
MIN_STATE_SUPPORT = 5
MIN_EVALUATION = 30

OUTCOMES = (
    "BUY_POSITIVE",
    "SELL_POSITIVE",
    "NEITHER_POSITIVE",
)


@dataclass(frozen=True)
class Event:
    symbol: str
    time: int
    split: str
    state: int
    unusual: bool
    anomaly_score: float
    outcome: str


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        result = json.load(handle)

    if not isinstance(result, dict):
        raise ValueError(f"Invalid JSON object: {path}")

    return result


def load_events(path: Path, checkpoint: str) -> list[Event]:
    result: list[Event] = []
    seen: set[tuple[str, int]] = set()

    with path.open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        for raw in csv.DictReader(handle):
            if raw["checkpoint_id"] != checkpoint:
                raise ValueError("Mixed checkpoint IDs")

            event = Event(
                symbol=raw["symbol"],
                time=int(raw["timestamp_msc"]),
                split=raw["split"],
                state=int(raw["market_state"]),
                unusual=bool(int(raw["unusual"])),
                anomaly_score=float(raw["anomaly_score"]),
                outcome=raw["outcome_60s"],
            )

            if (
                not event.symbol
                or event.time <= 0
                or event.state < 0
                or event.split not in ("TRAIN", "TEST", "EMBARGO")
                or event.outcome not in ("", *OUTCOMES)
                or not math.isfinite(event.anomaly_score)
            ):
                raise ValueError("Invalid market-state event")

            key = (event.symbol, event.time)

            if key in seen:
                raise ValueError("Duplicate market-state event")

            seen.add(key)
            result.append(event)

    return sorted(
        result,
        key=lambda e: (e.time, e.symbol),
    )


def find_latest_run(checkpoint: str) -> tuple[Path, list[Event]]:
    candidates: list[tuple[int, Path, list[Event]]] = []

    if not RUNS.exists():
        raise FileNotFoundError(RUNS)

    for directory in RUNS.iterdir():
        if not directory.is_dir():
            continue

        manifest = directory / "run_manifest.json"
        event_file = directory / "market_states.csv"

        if not manifest.is_file() or not event_file.is_file():
            continue

        metadata = load_json(manifest)

        if metadata.get("checkpoint_id") != checkpoint:
            continue

        events = load_events(event_file, checkpoint)

        if events:
            candidates.append((
                max(e.time for e in events),
                directory,
                events,
            ))

    if not candidates:
        raise RuntimeError(
            "No valid StableMemoryV2 run for active checkpoint"
        )

    candidates.sort(
        key=lambda value: (value[0], str(value[1]))
    )

    _, path, events = candidates[-1]
    return path, events


def probability(
    counts: Counter[int],
    states: list[int],
) -> list[float]:
    # Laplace smoothing avoids division by zero.
    total = sum(counts.values()) + len(states)

    return [
        (counts[state] + 1) / total
        for state in states
    ]


def js_divergence(
    first: list[float],
    second: list[float],
) -> float:
    middle = [
        (a + b) / 2
        for a, b in zip(first, second)
    ]

    def kl(p: list[float], q: list[float]) -> float:
        return sum(
            a * math.log2(a / b)
            for a, b in zip(p, q)
            if a > 0 and b > 0
        )

    return (
        kl(first, middle)
        + kl(second, middle)
    ) / 2


def transitions(events: list[Event]) -> Counter[str]:
    groups: dict[str, list[Event]] = defaultdict(list)

    for event in events:
        groups[event.symbol].append(event)

    counts: Counter[str] = Counter()

    for group in groups.values():
        group.sort(key=lambda e: e.time)

        for previous, current in zip(group, group[1:]):
            gap = current.time - previous.time

            if 0 < gap <= MAX_GAP_MS:
                counts[
                    f"{previous.state}>{current.state}"
                ] += 1

    return counts


def performance(
    training: list[Event],
    evaluation: list[Event],
) -> dict[str, Any]:
    by_state: dict[int, Counter[str]] = defaultdict(Counter)

    train_outcomes = Counter(
        e.outcome for e in training
        if e.outcome in OUTCOMES
    )

    for event in training:
        if event.outcome in OUTCOMES:
            by_state[event.state][event.outcome] += 1

    if not train_outcomes:
        return {"status": "NO_TRAINING_LABELS"}

    # Freeze predictions based on training labels ONLY.
    baseline = train_outcomes.most_common(1)[0][0]

    predictions = {
        state: counts.most_common(1)[0][0]
        for state, counts in by_state.items()
        if sum(counts.values()) >= MIN_STATE_SUPPORT
    }

    labeled = [
        event for event in evaluation
        if event.outcome in OUTCOMES
    ]

    covered = [
        event for event in labeled
        if event.state in predictions
    ]

    if not covered:
        return {
            "status": "NO_COVERED_LABELS",
            "labeled_events": len(labeled),
            "baseline_class": baseline,
        }

    correct = sum(
        event.outcome == predictions[event.state]
        for event in covered
    )

    baseline_correct = sum(
        event.outcome == baseline
        for event in covered
    )

    n = len(covered)
    model_accuracy = correct / n
    baseline_accuracy = baseline_correct / n

    return {
        "status": (
            "EXPLORATORY"
            if n >= MIN_EVALUATION
            else "SMALL_SAMPLE"
        ),
        "labeled_events": len(labeled),
        "covered_events": n,
        "coverage": n / len(labeled) if labeled else 0.0,
        "model_accuracy": model_accuracy,
        "baseline_accuracy": baseline_accuracy,
        "lift_percentage_points": (
            model_accuracy - baseline_accuracy
        ) * 100,
        "baseline_class": baseline,
        "state_predictions": predictions,
    }


def atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, name = tempfile.mkstemp(
        prefix=".pv_drift_",
        suffix=".tmp",
        dir=path.parent,
    )
    os.close(fd)

    temporary = Path(name)

    try:
        temporary.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--recent",
        type=int,
        default=60,
        help="Last N TEST events for recent drift analysis",
    )

    args = parser.parse_args()

    if args.recent < 20:
        parser.error("--recent must be at least 20")

    if not ACTIVE.is_file():
        raise FileNotFoundError(
            "No active checkpoint; initialize StableMemoryV2"
        )

    pointer = load_json(ACTIVE)
    checkpoint = str(pointer["checkpoint_id"])

    if (
        len(checkpoint) != 16
        or any(c not in "0123456789abcdef" for c in checkpoint)
    ):
        raise ValueError("Invalid checkpoint identifier")

    metadata = load_json(
        CHECKPOINTS / checkpoint / "metadata.json"
    )

    if metadata.get("checkpoint_id") != checkpoint:
        raise ValueError("Checkpoint metadata mismatch")

    run_directory, events = find_latest_run(checkpoint)

    training = [
        e for e in events if e.split == "TRAIN"
    ]

    testing = [
        e for e in events if e.split == "TEST"
    ]

    if not training or not testing:
        print("PV_DRIFT_STATUS=MORE_DATA_REQUIRED")
        return

    recent = testing[-args.recent:]

    state_count = int(metadata["market_states"])
    states = list(range(state_count))

    all_state_counts = Counter(
        event.state for event in events
    )

    if any(state not in states for state in all_state_counts):
        raise ValueError(
            "Observed state outside checkpoint definition"
        )

    train_counts = Counter(
        event.state for event in training
    )

    recent_counts = Counter(
        event.state for event in recent
    )

    train_probability = probability(
        train_counts, states
    )

    recent_probability = probability(
        recent_counts, states
    )

    jsd = js_divergence(
        train_probability, recent_probability
    )

    train_anomaly = sum(
        e.unusual for e in training
    ) / len(training)

    recent_anomaly = sum(
        e.unusual for e in recent
    ) / len(recent)

    full_performance = performance(
        training, testing
    )

    recent_performance = performance(
        training, recent
    )

    train_transitions = transitions(training)
    recent_transitions = transitions(recent)

    # These are exploratory screening thresholds,
    # NOT statistically calibrated drift alarms.
    flags: list[str] = []

    if len(recent) < 30:
        flags.append("INSUFFICIENT_RECENT_OBSERVATIONS")
    else:
        if jsd >= 0.10:
            flags.append("STATE_DISTRIBUTION_SHIFT")

        if recent_anomaly - train_anomaly >= 0.15:
            flags.append("ANOMALY_RATE_INCREASE")

    if (
        recent_performance.get("status") == "EXPLORATORY"
        and recent_performance["lift_percentage_points"] < 0
    ):
        flags.append("MODEL_BELOW_BASELINE_RECENTLY")

    report = {
        "schema": VERSION,
        "created_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "checkpoint_id": checkpoint,
        "source_run": str(run_directory),
        "train_events": len(training),
        "test_events": len(testing),
        "recent_events": len(recent),
        "state_distribution_train": dict(train_counts),
        "state_distribution_recent": dict(recent_counts),
        "state_js_divergence_bits": jsd,
        "train_anomaly_rate": train_anomaly,
        "recent_anomaly_rate": recent_anomaly,
        "train_top_transitions": train_transitions.most_common(10),
        "recent_top_transitions": recent_transitions.most_common(10),
        "full_test_performance": full_performance,
        "recent_performance": recent_performance,
        "flags": flags,
        "interpretation": (
            "Exploratory within-sample-period monitoring; "
            "no statistically validated drift or trading edge"
        ),
        "model_changed": False,
        "trading_enabled": False,
    }

    # Deterministic report identity for this source
    # run and monitor configuration.
    identity = hashlib.sha256(
        (
            checkpoint
            + run_directory.name
            + VERSION
            + str(args.recent)
        ).encode()
    ).hexdigest()[:16]

    output = REPORTS / f"drift_{identity}.json"

    atomic_json(output, report)

    print("PV_QUANTUM_DRIFT_MONITOR=V1")
    print(f"CHECKPOINT_ID={checkpoint}")
    print(f"TRAIN_EVENTS={len(training)}")
    print(f"TEST_EVENTS={len(testing)}")
    print(f"RECENT_EVENTS={len(recent)}")
    print(f"STATE_DISTRIBUTION_JSD={jsd:.5f}")
    print(f"TRAIN_ANOMALY_RATE={train_anomaly:.2%}")
    print(f"RECENT_ANOMALY_RATE={recent_anomaly:.2%}")

    for label, result in (
        ("FULL_TEST", full_performance),
        ("RECENT", recent_performance),
    ):
        print(f"{label}_STATUS={result['status']}")

        if "model_accuracy" in result:
            print(
                f"{label}_STATE_ACCURACY="
                f"{result['model_accuracy']:.2%}"
            )
            print(
                f"{label}_BASELINE="
                f"{result['baseline_accuracy']:.2%}"
            )
            print(
                f"{label}_LIFT_PP="
                f"{result['lift_percentage_points']:+.2f}"
            )

    print(f"DRIFT_FLAGS={flags or ['NONE']}")
    print(f"REPORT={output}")
    print("PV_DRIFT_STATUS=PASS")
    print("MODEL_CHANGED=NO")
    print("PROFITABILITY_PROVEN=NO")
    print("TRADING_ENABLED=NO")


if __name__ == "__main__":
    main()
