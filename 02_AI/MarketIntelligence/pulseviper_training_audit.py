
"""PulseViper training-readiness audit. Research only."""

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT / "01_Data" / "VolumeMemory"
    / "reaction_outcomes_v1.csv"
)

HORIZONS = (15, 30, 60, 120)


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)

    counts: Counter[int] = Counter()
    outcomes: dict[int, Counter[str]] = {
        h: Counter() for h in HORIZONS
    }
    times: set[int] = set()
    first_time: int | None = None
    last_time: int | None = None
    bad_rows = 0
    total_rows = 0

    with SOURCE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            try:
                h = int(row["horizon_seconds"])
                t = int(row["entry_tick_msc"])
                bid = float(row["bid"])
                ask = float(row["ask"])
                buy = float(row["buy_pct_est"])
                sell = float(row["sell_pct_est"])
                n = int(row["bin_count"])

                bins = [
                    float(v)
                    for v in row["volume_bins"].split("|")
                ]

                if (
                    h not in HORIZONS
                    or t <= 0
                    or bid <= 0
                    or ask < bid
                    or abs(buy + sell - 100) > 0.02
                    or len(bins) != n
                    or n <= 0
                ):
                    bad_rows += 1
                    continue

                total_rows += 1
                times.add(t)
                counts[h] += 1
                outcomes[h][row["outcome"]] += 1

                first_time = (
                    t if first_time is None
                    else min(first_time, t)
                )
                last_time = (
                    t if last_time is None
                    else max(last_time, t)
                )

            except (ValueError, KeyError, TypeError):
                bad_rows += 1

    if not times or first_time is None or last_time is None:
        raise RuntimeError("No valid labeled observations")

    duration = (last_time - first_time) / 1000
    distinct_minutes = len({
        t // 60_000 for t in times
    })

    print("PV_TRAINING_AUDIT=COMPLETE")
    print(f"VALID_LABEL_ROWS={total_rows}")
    print(f"INVALID_ROWS={bad_rows}")
    print(f"UNIQUE_SNAPSHOT_TIMES={len(times)}")
    print(f"DISTINCT_MINUTES={distinct_minutes}")
    print(f"OBSERVED_SPAN_MINUTES={duration / 60:.2f}")

    for h in HORIZONS:
        print(f"\nHORIZON_{h}S_ROWS={counts[h]}")
        print(f"HORIZON_{h}S_OUTCOMES={dict(outcomes[h])}")

    print("\nTRAINING_ASSESSMENT=" +
          ("MORE_DATA_REQUIRED"
           if distinct_minutes < 300
           else "READY_FOR_FURTHER_VALIDATION"))

    print("IMPORTANT=Rows are overlapping, not independent trades")
    print("TRADING_ENABLED=NO")


if __name__ == "__main__":
    main()
