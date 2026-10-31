
"""
PulseViper Temporal Memory V1
============================

Research-only sequence memory:
- Reads Adaptive Discovery V1.1 events.
- Discovers state transitions and sequences.
- Uses TRAIN data to estimate pattern outcomes.
- Evaluates patterns on later TEST events.
- Keeps each discovery run in a separate version.
- Never places trades or deploys trading signals.

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
DATA = ROOT / "01_Data" / "VolumeMemory"

SOURCE = DATA / "adaptive_events_v1.csv"
MEMORY_ROOT = DATA / "TemporalMemory"

MAX_GAP_MS = 45_000
MIN_TRAIN_SUPPORT = 5

LABELS = (
    "BUY_POSITIVE",
    "SELL_POSITIVE",
    "NEITHER_POSITIVE",
)


@dataclass(frozen=True)
class Event:
    symbol: str
    timestamp: int
    split: str
    state: int
    outcome: str
    anomaly_score: float


@dataclass(frozen=True)
class SequenceRecord:
    symbol: str
    timestamp: int
    split: str
    pattern: tuple[int, ...]
    outcome: str


def read_events(path: Path) -> list[Event]:
    result: list[Event] = []
    seen: set[tuple[str, int, str]] = set()

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)

        for row in reader:
            symbol = row["symbol"]
            timestamp = int(row["timestamp_msc"])
            split = row["split"]
            state = int(row["market_state"])
            outcome = row["outcome"]
            anomaly = float(row["anomaly_score"])

            if (
                not symbol
                or timestamp <= 0
                or split not in ("TRAIN", "TEST")
                or state < 0
                or outcome not in LABELS
                or not math.isfinite(anomaly)
            ):
                raise ValueError(
                    f"Invalid event: {row}"
                )

            key = (symbol, timestamp, split)

            if key in seen:
                raise ValueError(
                    f"Duplicate event: {key}"
                )

            seen.add(key)

            result.append(
                Event(
                    symbol=symbol,
                    timestamp=timestamp,
                    split=split,
                    state=state,
                    outcome=outcome,
                    anomaly_score=anomaly,
                )
            )

    return sorted(
        result,
        key=lambda e: (
            e.symbol,
            e.split,
            e.timestamp,
        ),
    )


def event_version(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()[:16]


def build_sequences(
    events: list[Event],
    length: int,
    gap_ms: int,
) -> list[SequenceRecord]:
    groups: dict[
        tuple[str, str], list[Event]
    ] = defaultdict(list)

    for event in events:
        groups[
            (event.symbol, event.split)
        ].append(event)

    result: list[SequenceRecord] = []

    for (symbol, split), group in groups.items():
        group.sort(key=lambda e: e.timestamp)

        for index in range(length - 1, len(group)):
            window = group[
                index - length + 1:index + 1
            ]

            # A sequence must be a continuous
            # chain of temporally nearby events.
            gaps_valid = all(
                0 < right.timestamp - left.timestamp
                <= gap_ms
                for left, right in zip(
                    window, window[1:]
                )
            )

            if not gaps_valid:
                continue

            result.append(
                SequenceRecord(
                    symbol=symbol,
                    timestamp=window[-1].timestamp,
                    split=split,
                    pattern=tuple(
                        e.state for e in window
                    ),
                    outcome=window[-1].outcome,
                )
            )

    return result


def distribution(
    counts: Counter[str],
) -> dict[str, float]:
    total = sum(counts.values())

    if total == 0:
        return {
            label: 0.0 for label in LABELS
        }

    return {
        label: counts[label] / total
        for label in LABELS
    }


def state_transitions(
    events: list[Event],
    gap_ms: int,
) -> dict[str, Counter[tuple[int, int]]]:
    groups: dict[
        tuple[str, str], list[Event]
    ] = defaultdict(list)

    for event in events:
        groups[
            (event.symbol, event.split)
        ].append(event)

    transitions: dict[
        str, Counter[tuple[int, int]]
    ] = {
        "TRAIN": Counter(),
        "TEST": Counter(),
    }

    for (_, split), group in groups.items():
        group.sort(key=lambda e: e.timestamp)

        for previous, current in zip(
            group, group[1:]
        ):
            if (
                0 < current.timestamp - previous.timestamp
                <= gap_ms
            ):
                transitions[split][
                    (previous.state, current.state)
                ] += 1

    return transitions


def evaluate_sequences(
    train: list[SequenceRecord],
    test: list[SequenceRecord],
    length: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    train_patterns: dict[
        tuple[int, ...], Counter[str]
    ] = defaultdict(Counter)

    test_patterns: dict[
        tuple[int, ...], Counter[str]
    ] = defaultdict(Counter)

    for record in train:
        train_patterns[
            record.pattern
        ][record.outcome] += 1

    for record in test:
        test_patterns[
            record.pattern
        ][record.outcome] += 1

    train_base = Counter(
        record.outcome for record in train
    )

    base_label = (
        train_base.most_common(1)[0][0]
        if train_base else "NEITHER_POSITIVE"
    )

    rows: list[dict[str, Any]] = []

    covered = 0
    correct = 0
    baseline_correct = 0

    for pattern in sorted(train_patterns):
        train_counts = train_patterns[pattern]
        test_counts = test_patterns[pattern]

        support = sum(train_counts.values())
        test_n = sum(test_counts.values())

        # Avoid describing one-off clusters
        # as meaningful discovered patterns.
        if support < MIN_TRAIN_SUPPORT:
            continue

        probabilities = distribution(train_counts)

        predicted = max(
            LABELS,
            key=lambda label: (
                probabilities[label],
                -LABELS.index(label),
            ),
        )

        covered += test_n
        correct += test_counts[predicted]
        baseline_correct += test_counts[base_label]

        rows.append({
            "sequence_length": length,
            "pattern": ">".join(
                str(x) for x in pattern
            ),
            "train_count": support,
            "test_count": test_n,
            "train_buy_rate": round(
                probabilities["BUY_POSITIVE"], 5
            ),
            "train_sell_rate": round(
                probabilities["SELL_POSITIVE"], 5
            ),
            "train_neither_rate": round(
                probabilities["NEITHER_POSITIVE"], 5
            ),
            "predicted_outcome": predicted,
            "test_buy_count": test_counts[
                "BUY_POSITIVE"
            ],
            "test_sell_count": test_counts[
                "SELL_POSITIVE"
            ],
            "test_neither_count": test_counts[
                "NEITHER_POSITIVE"
            ],
            "test_correct": test_counts[predicted],
        })

    summary: dict[str, Any] = {
        "sequence_length": length,
        "train_sequences": len(train),
        "test_sequences": len(test),
        "train_unique_patterns": len(
            train_patterns
        ),
        "test_unique_patterns": len(
            test_patterns
        ),
        "qualified_patterns": len(rows),
        "covered_test_events": covered,
        "test_coverage": (
            covered / len(test)
            if test else 0.0
        ),
        "sequence_accuracy": (
            correct / covered
            if covered else None
        ),
        "baseline_accuracy_on_covered": (
            baseline_correct / covered
            if covered else None
        ),
        "train_majority_outcome": base_label,
    }

    return rows, summary


def write_csv(
    path: Path,
    rows: list[dict[str, Any]],
    columns: list[str],
) -> None:
    # Atomic publication on the same drive.
    path.parent.mkdir(
        parents=True, exist_ok=True
    )

    descriptor, name = tempfile.mkstemp(
        prefix=".pv_",
        suffix=".tmp",
        dir=path.parent,
    )
    os.close(descriptor)

    temporary = Path(name)

    try:
        with temporary.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=columns,
            )
            writer.writeheader()
            writer.writerows(rows)

        os.replace(temporary, path)
    finally:
        temporary.unlink(
            missing_ok=True
        )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--source",
        type=Path,
        default=SOURCE,
    )

    parser.add_argument(
        "--max-gap",
        type=int,
        default=45,
        help="Maximum seconds between events",
    )

    args = parser.parse_args()

    if args.max_gap < 15:
        parser.error(
            "--max-gap must be at least 15 seconds"
        )

    if not args.source.is_file():
        raise FileNotFoundError(
            args.source
        )

    # Snapshot the discovery output first.
    # Its hash identifies this specific
    # discovery-run artifact, NOT stable cluster
    # identity across retraining.
    raw = args.source.read_bytes()

    version = hashlib.sha256(
        raw
    ).hexdigest()[:16]

    version_dir = (
        MEMORY_ROOT / f"discovery_{version}"
    )

    version_dir.mkdir(
        parents=True, exist_ok=True
    )

    snapshot = version_dir / "input_events.csv"

    if snapshot.exists():
        if snapshot.read_bytes() != raw:
            raise RuntimeError(
                "Checkpoint hash collision"
            )
    else:
        descriptor, temp_name = tempfile.mkstemp(
            prefix=".input_",
            dir=version_dir,
        )
        os.close(descriptor)

        temporary = Path(temp_name)

        try:
            temporary.write_bytes(raw)
            os.replace(temporary, snapshot)
        finally:
            temporary.unlink(
                missing_ok=True
            )

    events = read_events(snapshot)

    train_events = [
        e for e in events
        if e.split == "TRAIN"
    ]

    test_events = [
        e for e in events
        if e.split == "TEST"
    ]

    print("PV_TEMPORAL_MEMORY=V1")
    print(f"DISCOVERY_VERSION={version}")
    print(f"TRAIN_EVENTS={len(train_events)}")
    print(f"TEST_EVENTS={len(test_events)}")

    if len(train_events) < 30 or len(test_events) < 10:
        print("STATUS=MORE_DATA_REQUIRED")
        print("TRADING_ENABLED=NO")
        return

    gap_ms = args.max_gap * 1000

    transitions = state_transitions(
        events, gap_ms
    )

    transition_rows: list[dict[str, Any]] = []

    for split in ("TRAIN", "TEST"):
        for (a, b), count in sorted(
            transitions[split].items()
        ):
            transition_rows.append({
                "split": split,
                "from_state": a,
                "to_state": b,
                "count": count,
            })

    reports: list[dict[str, Any]] = []

    for length in (2, 3):
        sequences = build_sequences(
            events, length, gap_ms
        )

        train = [
            s for s in sequences
            if s.split == "TRAIN"
        ]

        test = [
            s for s in sequences
            if s.split == "TEST"
        ]

        rows, summary = evaluate_sequences(
            train, test, length
        )

        output = (
            version_dir
            / f"sequences_{length}_states.csv"
        )

        write_csv(
            output,
            rows,
            [
                "sequence_length",
                "pattern",
                "train_count",
                "test_count",
                "train_buy_rate",
                "train_sell_rate",
                "train_neither_rate",
                "predicted_outcome",
                "test_buy_count",
                "test_sell_count",
                "test_neither_count",
                "test_correct",
            ],
        )

        reports.append(summary)

        print(f"\nSEQUENCE_LENGTH={length}")
        print(
            f"TRAIN_SEQUENCES={len(train)}"
        )
        print(
            f"TEST_SEQUENCES={len(test)}"
        )
        print(
            f"QUALIFIED_PATTERNS="
            f"{summary['qualified_patterns']}"
        )
        print(
            f"TEST_COVERAGE="
            f"{summary['test_coverage']:.2%}"
        )

        if summary["sequence_accuracy"] is None:
            print("SEQUENCE_ACCURACY=NOT_AVAILABLE")
        else:
            print(
                "SEQUENCE_ACCURACY="
                f"{summary['sequence_accuracy']:.2%}"
            )
            print(
                "BASELINE_SAME_EVENTS="
                f"{summary['baseline_accuracy_on_covered']:.2%}"
            )

    write_csv(
        version_dir / "state_transitions.csv",
        transition_rows,
        [
            "split",
            "from_state",
            "to_state",
            "count",
        ],
    )

    report_data = {
        "schema": "PV_TEMPORAL_MEMORY_V1",
        "discovery_version": version,
        "created_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "max_gap_seconds": args.max_gap,
        "horizon_seconds": 60,
        "training_events": len(train_events),
        "test_events": len(test_events),
        "sequence_reports": reports,
        "warnings": [
            "Discovery state IDs are not stable across retraining",
            "Outcome observations overlap in time",
            "Short-window results cannot establish profitability",
            "State sequences are descriptive, not trade instructions",
        ],
        "trading_enabled": False,
    }

    report_path = version_dir / "memory_report.json"

    descriptor, temp_name = tempfile.mkstemp(
        prefix=".report_",
        dir=version_dir,
    )
    os.close(descriptor)
    temp_report = Path(temp_name)

    try:
        temp_report.write_text(
            json.dumps(report_data, indent=2),
            encoding="utf-8",
        )
        os.replace(temp_report, report_path)
    finally:
        temp_report.unlink(missing_ok=True)

    print(f"\nMEMORY_DIRECTORY={version_dir}")
    print("PV_TEMPORAL_MEMORY_STATUS=PASS")
    print("MODEL_DEPLOYED=NO")
    print("PROFITABILITY_PROVEN=NO")
    print("TRADING_ENABLED=NO")


if __name__ == "__main__":
    main()
