
"""PulseViper Adaptive Event Discovery V1.1.

Typed market observations, unsupervised market-state discovery,
chronological evaluation. Research only; never trades.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import shutil
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import numpy as np
from numpy.typing import NDArray
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "01_Data" / "VolumeMemory"

FEATURES = DATA / "pattern_features_v1.csv"
OUTCOMES = DATA / "reaction_outcomes_v1.csv"

EVENT_OUTPUT = DATA / "adaptive_events_v1.csv"
SUMMARY_OUTPUT = DATA / "adaptive_event_summary_v1.csv"

HORIZON = 60
SAMPLE_MS = 15_000
EMBARGO_MS = 120_000

COLUMNS = (
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

LABELS = frozenset((
    "BUY_POSITIVE",
    "SELL_POSITIVE",
    "NEITHER_POSITIVE",
))


@dataclass(frozen=True)
class Observation:
    symbol: str
    timestamp: int
    vector: NDArray[np.float64]
    outcome: str
    buy_pct: float
    poc: float
    mid: float


@dataclass(frozen=True)
class Event:
    observation: Observation
    split: str
    state: int
    anomaly_score: float
    unusual: bool


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        return list(csv.DictReader(handle))


def snapshot_inputs(
    directory: Path,
    first: Path,
    second: Path,
) -> tuple[Path, Path]:
    dest_a = directory / "features.csv"
    dest_b = directory / "labels.csv"

    for _ in range(5):
        before = [
            (p.stat().st_size, p.stat().st_mtime_ns)
            for p in (first, second)
        ]

        shutil.copyfile(first, dest_a)
        shutil.copyfile(second, dest_b)

        after = [
            (p.stat().st_size, p.stat().st_mtime_ns)
            for p in (first, second)
        ]

        if before == after:
            return dest_a, dest_b

    raise RuntimeError(
        "Inputs changed during copying; retry after refresh"
    )


def prepare(
    features_path: Path,
    labels_path: Path,
) -> list[Observation]:
    features = read_csv(features_path)
    labels = read_csv(labels_path)

    if not features:
        raise RuntimeError("Empty features CSV")

    absent = set(COLUMNS) - features[0].keys()

    if absent:
        raise RuntimeError(
            f"Missing feature columns: {sorted(absent)}"
        )

    outcomes: dict[tuple[str, int], str] = {}

    for raw in labels:
        try:
            if (
                int(raw["horizon_seconds"]) == HORIZON
                and raw["outcome"] in LABELS
            ):
                key = (
                    raw["symbol"],
                    int(raw["entry_tick_msc"]),
                )
                outcomes[key] = raw["outcome"]

        except (ValueError, KeyError, TypeError):
            continue

    observations: dict[
        tuple[str, int], Observation
    ] = {}

    for raw in features:
        try:
            symbol = raw["symbol"]
            timestamp = int(raw["tick_server_msc"])

            label = outcomes.get((symbol, timestamp))

            if label is None:
                continue

            numbers: list[float] = [
                float(raw[name])
                for name in COLUMNS
            ]

            if not all(math.isfinite(x) for x in numbers):
                continue

            bid = float(raw["bid"])
            ask = float(raw["ask"])

            observations[(symbol, timestamp)] = Observation(
                symbol=symbol,
                timestamp=timestamp,
                vector=np.asarray(
                    numbers,
                    dtype=np.float64,
                ),
                outcome=label,
                buy_pct=float(raw["buy_pct_est"]),
                poc=float(raw["poc_price"]),
                mid=(bid + ask) / 2,
            )

        except (ValueError, KeyError, TypeError):
            continue

    return sorted(
        observations.values(),
        key=lambda r: (r.timestamp, r.symbol),
    )


def sample(
    rows: list[Observation],
) -> list[Observation]:
    previous: dict[str, int] = {}
    picked: list[Observation] = []

    for row in rows:
        last = previous.get(row.symbol)

        if (
            last is None
            or row.timestamp - last >= SAMPLE_MS
        ):
            picked.append(row)
            previous[row.symbol] = row.timestamp

    return picked


def matrix(
    rows: list[Observation],
) -> NDArray[np.float64]:
    return np.stack(
        [row.vector for row in rows],
        axis=0,
    )


def write_csv(
    path: Path,
    columns: list[str],
    rows: list[dict[str, object]],
) -> None:
    with path.open(
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


def summarize(
    events: list[Event],
) -> list[dict[str, object]]:
    groups: dict[
        tuple[str, int],
        list[Event],
    ] = defaultdict(list)

    for event in events:
        groups[
            (event.split, event.state)
        ].append(event)

    result: list[dict[str, object]] = []

    for (split, state), group in sorted(groups.items()):
        counts = Counter(
            event.observation.outcome
            for event in group
        )

        n = len(group)

        result.append({
            "split": split,
            "state": state,
            "observations": n,
            "buy_positive": counts["BUY_POSITIVE"],
            "sell_positive": counts["SELL_POSITIVE"],
            "neither_positive": counts["NEITHER_POSITIVE"],
            "buy_rate": round(
                counts["BUY_POSITIVE"] / n, 5
            ),
            "sell_rate": round(
                counts["SELL_POSITIVE"] / n, 5
            ),
            "neither_rate": round(
                counts["NEITHER_POSITIVE"] / n, 5
            ),
            "mean_anomaly_score": round(
                sum(
                    event.anomaly_score
                    for event in group
                ) / n,
                6,
            ),
        })

    return result


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--features",
        type=Path,
        default=FEATURES,
    )

    parser.add_argument(
        "--outcomes",
        type=Path,
        default=OUTCOMES,
    )

    args = parser.parse_args()

    print("PV_ADAPTIVE_DISCOVERY=V1.1")
    print("TRADING_ENABLED=NO")

    DATA.mkdir(
        parents=True,
        exist_ok=True,
    )

    with tempfile.TemporaryDirectory(
        prefix=".pv_discovery_",
        dir=DATA,
    ) as temp:
        directory = Path(temp)

        feature_path, label_path = snapshot_inputs(
            directory,
            args.features,
            args.outcomes,
        )

        observations = prepare(
            feature_path,
            label_path,
        )

        selected = sample(observations)

        print(
            f"ALIGNED_LABELED_ROWS={len(observations)}"
        )
        print(
            f"SAMPLED_EVENTS={len(selected)}"
        )
        print(
            f"FEATURE_DIMENSIONS={len(COLUMNS)}"
        )

        if len(selected) < 60:
            print("STATUS=MORE_SAMPLES_REQUIRED")
            return

        start = selected[0].timestamp
        end = selected[-1].timestamp
        span = end - start

        cut = start + int(span * 0.70)

        train = [
            row
            for row in selected
            if row.timestamp < cut - EMBARGO_MS
        ]

        test = [
            row
            for row in selected
            if row.timestamp >= cut + EMBARGO_MS
        ]

        print(
            f"OBSERVED_MINUTES={span / 60000:.2f}"
        )
        print(f"TRAIN_EVENTS={len(train)}")
        print(f"TEST_EVENTS={len(test)}")

        if len(train) < 40 or len(test) < 10:
            print("STATUS=MORE_SPLIT_DATA_REQUIRED")
            return

        scaler = RobustScaler()

        train_x = np.asarray(
            scaler.fit_transform(matrix(train)),
            dtype=np.float64,
        )

        test_x = np.asarray(
            scaler.transform(matrix(test)),
            dtype=np.float64,
        )

        state_count = min(
            5,
            max(2, len(train) // 20),
        )

        clusters = KMeans(
            n_clusters=state_count,
            n_init="auto",
            random_state=42,
        )

        clusters.fit(train_x)

        detector = IsolationForest(
            n_estimators=100,
            contamination="auto",
            random_state=42,
            n_jobs=1,
        )

        detector.fit(train_x)

        events: list[Event] = []

        for split, rows, values in (
            ("TRAIN", train, train_x),
            ("TEST", test, test_x),
        ):
            states = clusters.predict(values)
            scores = detector.decision_function(values)

            for observation, state, score in zip(
                rows,
                states,
                scores,
            ):
                events.append(
                    Event(
                        observation=observation,
                        split=split,
                        state=int(state),
                        anomaly_score=float(score),
                        unusual=bool(score < 0),
                    )
                )

        report = summarize(events)

        event_rows: list[dict[str, object]] = []

        for event in events:
            observation = event.observation

            event_rows.append({
                "symbol": observation.symbol,
                "timestamp_msc": observation.timestamp,
                "split": event.split,
                "market_state": event.state,
                "anomaly_score": round(
                    event.anomaly_score, 6
                ),
                "unusual_state": int(event.unusual),
                "buy_pct_est": observation.buy_pct,
                "poc_price": observation.poc,
                "mid_price": observation.mid,
                "horizon_seconds": HORIZON,
                "outcome": observation.outcome,
            })

        events_tmp = directory / "events.csv"
        summary_tmp = directory / "summary.csv"

        write_csv(
            events_tmp,
            [
                "symbol",
                "timestamp_msc",
                "split",
                "market_state",
                "anomaly_score",
                "unusual_state",
                "buy_pct_est",
                "poc_price",
                "mid_price",
                "horizon_seconds",
                "outcome",
            ],
            event_rows,
        )

        write_csv(
            summary_tmp,
            [
                "split",
                "state",
                "observations",
                "buy_positive",
                "sell_positive",
                "neither_positive",
                "buy_rate",
                "sell_rate",
                "neither_rate",
                "mean_anomaly_score",
            ],
            report,
        )

        os.replace(events_tmp, EVENT_OUTPUT)
        os.replace(summary_tmp, SUMMARY_OUTPUT)

        print(
            f"DISCOVERED_MARKET_STATES={state_count}"
        )

        print(
            "=== LATER-PERIOD STATE REACTIONS ==="
        )

        for row in report:
            if row["split"] == "TEST":
                print(
                    f"STATE={row['state']} "
                    f"N={row['observations']} "
                    f"BUY={cast(float, row['buy_rate']):.1%} "
                    f"SELL={cast(float, row['sell_rate']):.1%} "
                    f"NEITHER={cast(float, row['neither_rate']):.1%}"
                )

        print(f"EVENT_OUTPUT={EVENT_OUTPUT}")
        print(f"SUMMARY_OUTPUT={SUMMARY_OUTPUT}")

        print("PV_ADAPTIVE_DISCOVERY_STATUS=PASS")
        print("PROFITABILITY_PROVEN=NO")
        print("TRADING_ENABLED=NO")

        if span < 300 * 60_000:
            print(
                "ASSESSMENT=EXPLORATORY_ONLY_"
                "MORE_SESSIONS_REQUIRED"
            )


if __name__ == "__main__":
    main()
