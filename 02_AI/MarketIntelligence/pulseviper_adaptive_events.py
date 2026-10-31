
"""
PulseViper Adaptive Event Discovery V1

Learns unusual Volume Profile changes relative to
PREVIOUS observations, then associates mature future
outcomes for research.

No fixed BUY/SELL rules.
No external API.
No model deployment or trading.
Standard Python library only.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import statistics
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "01_Data" / "VolumeMemory"

FEATURES = DATA / "pattern_features_v1.csv"
LABELS = DATA / "reaction_outcomes_v1.csv"
EVENTS = DATA / "adaptive_events_v1.csv"
SUMMARY = DATA / "adaptive_event_summary_v1.csv"

HORIZONS = (15, 30, 60, 120)

# Trailing historical reference only.
HISTORY_SIZE = 120
MIN_HISTORY = 60

# Surprise detection, not a trading threshold.
SURPRISE_PERCENTILE = 0.98
EVENT_COOLDOWN_MS = 20_000

# Features already calculated using past market data.
SIGNALS = {
    "PRESSURE_SHIFT": "w10_delta_change_pp",
    "PROFILE_RESHAPE": "w10_profile_l1",
    "GREEN_RED_SHIFT": "w10_green_l1",
    "POC_RELOCATION": "w10_poc_change",
    "PRICE_IMPULSE": "w10_price_change",
    "LOCAL_VOLUME_SHIFT": "w10_near_price_volume_change",
    "PRESSURE_ACCELERATION": "pressure_acceleration_10s",
}


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)

    with path.open(
        "r", newline="", encoding="utf-8-sig"
    ) as handle:
        return list(csv.DictReader(handle))


def number(value: str | None) -> float | None:
    if value is None or value == "":
        return None

    try:
        result = float(value)
    except (TypeError, ValueError):
        return None

    return result if math.isfinite(result) else None


def quantile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)

    if not ordered:
        raise ValueError("Empty quantile")

    position = fraction * (len(ordered) - 1)
    left = int(position)
    right = min(left + 1, len(ordered) - 1)
    weight = position - left

    return (
        ordered[left] * (1 - weight)
        + ordered[right] * weight
    )


def utc_time(milliseconds: int) -> str:
    return datetime.fromtimestamp(
        milliseconds / 1000,
        tz=timezone.utc,
    ).isoformat()


def write_atomic(path: Path, rows: list[dict], columns: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary = path.with_name(path.name + ".tmp")

    with temporary.open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=columns
        )
        writer.writeheader()
        writer.writerows(rows)

    os.replace(temporary, path)


def load_labels() -> dict[tuple[str, int, int], str]:
    joined: dict[tuple[str, int, int], str] = {}

    for row in load_csv(LABELS):
        try:
            horizon = int(row["horizon_seconds"])
            timestamp = int(row["entry_tick_msc"])

            if horizon not in HORIZONS:
                continue

            outcome = row["outcome"]

            if outcome not in {
                "BUY_POSITIVE",
                "SELL_POSITIVE",
                "NEITHER_POSITIVE",
            }:
                continue

            key = (row["symbol"], timestamp, horizon)
            joined[key] = outcome

        except (KeyError, TypeError, ValueError):
            continue

    return joined


def fingerprint(row: dict[str, str]) -> str:
    """
    Compact description of the CURRENT market state.

    This is an event-family identifier, not an
    instruction to buy or sell.
    """

    pressure = number(row.get("w10_delta_change_pp"))
    price = number(row.get("w10_price_change"))
    poc = number(row.get("w10_poc_change"))

    def direction(value: float | None) -> str:
        if value is None:
            return "U"
        if value > 0:
            return "+"
        if value < 0:
            return "-"
        return "0"

    return (
        f"PRESSURE{direction(pressure)}_"
        f"PRICE{direction(price)}_"
        f"POC{direction(poc)}"
    )


def discover(
    feature_rows: list[dict[str, str]],
    labels: dict[tuple[str, int, int], str],
) -> tuple[list[dict], list[dict]]:

    by_symbol: dict[str, list[dict[str, str]]] = defaultdict(list)

    for row in feature_rows:
        by_symbol[row["symbol"]].append(row)

    events: list[dict] = []
    summaries: dict[str, Counter] = defaultdict(Counter)

    for symbol, rows in by_symbol.items():
        rows.sort(key=lambda r: int(r["tick_server_msc"]))

        history = {
            signal: deque(maxlen=HISTORY_SIZE)
            for signal in SIGNALS
        }

        last_event_time = -10**20

        for row in rows:
            timestamp = int(row["tick_server_msc"])

            current = {
                name: number(row.get(column))
                for name, column in SIGNALS.items()
            }

            candidates: list[tuple[str, float, float]] = []

            # IMPORTANT:
            # Compare current observation against
            # HISTORY ONLY, before adding current data.
            for name, value in current.items():
                if value is None:
                    continue

                magnitude = abs(value)
                previous = list(history[name])

                if len(previous) < MIN_HISTORY:
                    continue

                boundary = quantile(
                    previous, SURPRISE_PERCENTILE
                )

                # Avoid reporting zero-movement noise.
                if boundary <= 0 or magnitude <= boundary:
                    continue

                median = statistics.median(previous)
                deviations = [
                    abs(x - median) for x in previous
                ]
                mad = statistics.median(deviations)

                # Normalized magnitude relative to
                # previous dispersion (not future data).
                score = (
                    (magnitude - median)
                    / max(1.4826 * mad, 1e-9)
                )

                candidates.append(
                    (name, score, magnitude)
                )

            # Advance historical memory even if
            # this timestamp generates no event.
            for name, value in current.items():
                if value is not None:
                    history[name].append(abs(value))

            if not candidates:
                continue

            if (
                timestamp - last_event_time
                < EVENT_COOLDOWN_MS
            ):
                continue

            candidates.sort(
                key=lambda item: item[1],
                reverse=True,
            )

            dominant, score, magnitude = candidates[0]
            family = fingerprint(row)
            group = f"{dominant}|{family}"

            event = {
                "symbol": symbol,
                "timestamp_msc": timestamp,
                "time_utc": utc_time(timestamp),
                "event_type": dominant,
                "event_family": family,
                "event_group": group,
                "surprise_score": round(score, 6),
                "event_magnitude": round(magnitude, 8),
                "buy_pct_est": row.get("buy_pct_est", ""),
                "sell_pct_est": row.get("sell_pct_est", ""),
                "delta_pp_est": row.get("delta_pp_est", ""),
                "poc_price": row.get("poc_price", ""),
                "mid_price": (
                    (
                        float(row["bid"])
                        + float(row["ask"])
                    ) / 2
                ),
            }

            summaries[group]["events"] += 1

            for horizon in HORIZONS:
                outcome = labels.get(
                    (symbol, timestamp, horizon)
                )

                event[f"outcome_{horizon}s"] = (
                    outcome or "PENDING"
                )

                if outcome:
                    summaries[group][
                        f"{horizon}s_{outcome}"
                    ] += 1

            events.append(event)
            last_event_time = timestamp

    summary_rows = []

    for group, counter in sorted(
        summaries.items(),
        key=lambda item: -item[1]["events"],
    ):
        event_type, event_family = group.split("|", 1)

        item = {
            "event_type": event_type,
            "event_family": event_family,
            "event_count": counter["events"],
        }

        for horizon in HORIZONS:
            counts = {
                outcome: counter[
                    f"{horizon}s_{outcome}"
                ]
                for outcome in (
                    "BUY_POSITIVE",
                    "SELL_POSITIVE",
                    "NEITHER_POSITIVE",
                )
            }

            matured = sum(counts.values())

            item[f"matured_{horizon}s"] = matured

            for outcome, count in counts.items():
                item[
                    f"{horizon}s_{outcome.lower()}_count"
                ] = count

            item[f"buy_rate_{horizon}s"] = (
                round(
                    counts["BUY_POSITIVE"] / matured,
                    4,
                )
                if matured
                else ""
            )

        summary_rows.append(item)

    return events, summary_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--once", action="store_true"
    )
    args = parser.parse_args()

    feature_rows = load_csv(FEATURES)
    labels = load_labels()

    if not feature_rows:
        raise RuntimeError("No feature rows available")

    required_columns = {
        "symbol",
        "tick_server_msc",
        "bid",
        "ask",
        *SIGNALS.values(),
    }

    missing = required_columns - set(feature_rows[0])

    if missing:
        raise RuntimeError(
            f"Required features missing: {sorted(missing)}"
        )

    events, summaries = discover(
        feature_rows, labels
    )

    event_columns = [
        "symbol",
        "timestamp_msc",
        "time_utc",
        "event_type",
        "event_family",
        "event_group",
        "surprise_score",
        "event_magnitude",
        "buy_pct_est",
        "sell_pct_est",
        "delta_pp_est",
        "poc_price",
        "mid_price",
        *[
            f"outcome_{h}s"
            for h in HORIZONS
        ],
    ]

    summary_columns = [
        "event_type",
        "event_family",
        "event_count",
    ]

    for h in HORIZONS:
        summary_columns += [
            f"matured_{h}s",
            "dummy_placeholder",
        ][0:1]

        summary_columns += [
            f"{h}s_{outcome.lower()}_count"
            for outcome in (
                "BUY_POSITIVE",
                "SELL_POSITIVE",
                "NEITHER_POSITIVE",
            )
        ]

        summary_columns.append(
            f"buy_rate_{h}s"
        )

    write_atomic(
        EVENTS, events, event_columns
    )
    write_atomic(
        SUMMARY, summaries, summary_columns
    )

    types = Counter(
        event["event_type"]
        for event in events
    )

    mature60 = sum(
        event["outcome_60s"] != "PENDING"
        for event in events
    )

    print("PV_ADAPTIVE_EVENTS=PASS")
    print(f"FEATURE_ROWS={len(feature_rows)}")
    print(f"EVENTS_DISCOVERED={len(events)}")
    print(f"EVENT_FAMILIES={len(summaries)}")
    print(f"EVENT_TYPES={dict(types)}")
    print(f"EVENTS_WITH_60S_LABEL={mature60}")
    print(f"EVENT_FILE={EVENTS}")
    print(f"SUMMARY_FILE={SUMMARY}")
    print("FEATURES_USE_FUTURE=NO")
    print("PROFITABILITY_PROVEN=NO")
    print("TRADING_ENABLED=NO")


if __name__ == "__main__":
    main()
