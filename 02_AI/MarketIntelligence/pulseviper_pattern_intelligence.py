
"""
PulseViper Pattern Intelligence V1
=================================
Creates causal, model-ready Volume Profile features.

- Reads the existing live MT5 recorder CSV.
- Uses current and PAST observations only.
- Aligns changing volume-bin price grids.
- Does not train models or place trades.
- Python standard library only.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
from bisect import bisect_right
from collections import Counter
from pathlib import Path
from typing import Any


WINDOWS = (10, 30, 60)
MAX_STALENESS_MS = 5000


def default_source() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA not found")

    return (
        Path(appdata)
        / "MetaQuotes/Terminal/Common/Files"
        / "PulseViper/VolumeMemory"
        / "XAUUSD_PERIOD_M1_observations.csv"
    )


def default_output() -> Path:
    root = Path(__file__).resolve().parents[2]
    return (
        root
        / "01_Data/VolumeMemory"
        / "pattern_features_v1.csv"
    )


def finite(value: Any) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Nonfinite numeric value")
    return number


def read_vector(value: str, count: int) -> list[float]:
    values = [finite(v) for v in value.split("|")]

    if len(values) != count or any(v < 0 for v in values):
        raise ValueError("Invalid profile vector")

    return values


def load_snapshots(path: Path) -> list[dict[str, Any]]:
    data: dict[tuple[str, int], dict[str, Any]] = {}
    invalid = 0

    with path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        for raw in reader:
            try:
                n = int(raw["bin_count"])
                if not 16 <= n <= 128:
                    raise ValueError("Invalid bin count")

                buy_bins = read_vector(raw["buy_bins"], n)
                sell_bins = read_vector(raw["sell_bins"], n)
                volume_bins = read_vector(
                    raw["volume_bins"], n
                )

                t = int(raw["tick_server_msc"])
                bid = finite(raw["bid"])
                ask = finite(raw["ask"])
                buy_pct = finite(raw["buy_pct_est"])
                sell_pct = finite(raw["sell_pct_est"])
                grid_min = finite(raw["profile_min"])
                step = finite(raw["profile_step"])
                poc = finite(raw["poc_price"])
                vah = finite(raw["vah_price"])
                val = finite(raw["val_price"])
                symbol = raw["symbol"].strip()

                if (
                    not symbol
                    or t <= 0
                    or bid <= 0
                    or ask < bid
                    or step <= 0
                    or not 0 <= buy_pct <= 100
                    or abs(buy_pct + sell_pct - 100) > 0.02
                ):
                    raise ValueError("Invalid observation")

                total = sum(volume_bins)
                if total <= 0:
                    raise ValueError("Empty volume profile")

                for b, s, v in zip(
                    buy_bins, sell_bins, volume_bins
                ):
                    if abs((b + s) - v) > max(
                        0.05, v * 0.0001
                    ):
                        raise ValueError("Inconsistent bin volume")

                item = {
                    "symbol": symbol,
                    "t": t,
                    "bid": bid,
                    "ask": ask,
                    "mid": (bid + ask) / 2,
                    "buy": buy_pct,
                    "sell": sell_pct,
                    "delta": buy_pct - sell_pct,
                    "min": grid_min,
                    "step": step,
                    "n": n,
                    "poc": poc,
                    "vah": vah,
                    "val": val,
                    "buy_bins": buy_bins,
                    "sell_bins": sell_bins,
                    "vol_bins": volume_bins,
                    "total": total,
                }
                data[(symbol, t)] = item

            except (ValueError, TypeError, KeyError):
                # Ignore a partially written final CSV row.
                invalid += 1

    rows = sorted(
        data.values(),
        key=lambda r: (r["symbol"], r["t"]),
    )

    print(f"INPUT_SNAPSHOTS={len(rows)}")
    print(f"SKIPPED_INPUT_ROWS={invalid}")
    return rows


def normalize(values: list[float]) -> list[float]:
    total = sum(values)
    if total <= 0:
        return [0.0] * len(values)
    return [v / total for v in values]


def project_profile(
    source: dict[str, Any],
    target: dict[str, Any],
    field: str,
) -> list[float]:
    """
    Move the source profile onto the TARGET price grid.

    Each source bin is spread proportionally across
    overlapping target bins. Thus source bin index 20
    is never blindly compared to target bin index 20.
    """
    result = [0.0] * target["n"]
    source_values = normalize(source[field])

    for i, value in enumerate(source_values):
        if value <= 0:
            continue

        lo = source["min"] + i * source["step"]
        hi = lo + source["step"]

        j_start = max(
            0,
            int(math.floor(
                (lo - target["min"]) / target["step"]
            )),
        )

        j_end = min(
            target["n"] - 1,
            int(math.floor(
                (hi - target["min"]) / target["step"]
            )),
        )

        for j in range(j_start, j_end + 1):
            target_lo = target["min"] + j * target["step"]
            target_hi = target_lo + target["step"]

            overlap = max(
                0.0,
                min(hi, target_hi) - max(lo, target_lo),
            )

            if overlap > 0:
                result[j] += (
                    value * overlap / source["step"]
                )

    return result


def find_past(
    series: list[dict[str, Any]],
    times: list[int],
    index: int,
    seconds: int,
) -> dict[str, Any] | None:
    target = times[index] - seconds * 1000

    j = bisect_right(times, target, 0, index) - 1

    if j < 0:
        return None

    if target - times[j] > MAX_STALENESS_MS:
        return None

    return series[j]


def concentration(values: list[float]) -> float:
    normalized = normalize(values)
    return sum(v * v for v in normalized)


def nearby_activity(row: dict[str, Any]) -> float:
    normalized = normalize(row["vol_bins"])

    # Current mid-price neighborhood: +/- 2 bins.
    center = int(
        (row["mid"] - row["min"]) / row["step"]
    )

    left = max(0, center - 2)
    right = min(row["n"], center + 3)

    return sum(normalized[left:right])


def features(
    now: dict[str, Any],
    past: dict[str, Any] | None,
    seconds: int,
) -> dict[str, Any]:
    prefix = f"w{seconds}_"

    names = [
        "observed",
        "buy_change_pp",
        "delta_change_pp",
        "price_change",
        "poc_change",
        "profile_l1",
        "green_l1",
        "red_l1",
        "profile_overlap",
        "near_price_volume_change",
        "pressure_price_agreement",
    ]

    if past is None:
        return {prefix + key: "" for key in names}

    current_vol = normalize(now["vol_bins"])
    current_buy = normalize(now["buy_bins"])
    current_sell = normalize(now["sell_bins"])

    past_vol = project_profile(
        past, now, "vol_bins"
    )
    past_buy = project_profile(
        past, now, "buy_bins"
    )
    past_sell = project_profile(
        past, now, "sell_bins"
    )

    profile_l1 = sum(
        abs(a - b)
        for a, b in zip(current_vol, past_vol)
    )

    buy_l1 = sum(
        abs(a - b)
        for a, b in zip(current_buy, past_buy)
    )

    sell_l1 = sum(
        abs(a - b)
        for a, b in zip(current_sell, past_sell)
    )

    overlap = sum(
        min(a, b)
        for a, b in zip(current_vol, past_vol)
    )

    center = int(
        (now["mid"] - now["min"]) / now["step"]
    )

    left = max(0, center - 2)
    right = min(now["n"], center + 3)

    near_change = (
        sum(current_vol[left:right])
        - sum(past_vol[left:right])
    )

    price_change = now["mid"] - past["mid"]
    pressure_change = now["delta"] - past["delta"]

    if abs(price_change) < 1e-12 or abs(pressure_change) < 1e-12:
        agreement = 0
    elif price_change * pressure_change > 0:
        agreement = 1
    else:
        agreement = -1

    values = {
        "observed": 1,
        "buy_change_pp": now["buy"] - past["buy"],
        "delta_change_pp": pressure_change,
        "price_change": price_change,
        "poc_change": now["poc"] - past["poc"],
        "profile_l1": profile_l1,
        "green_l1": buy_l1,
        "red_l1": sell_l1,
        "profile_overlap": overlap,
        "near_price_volume_change": near_change,
        "pressure_price_agreement": agreement,
    }

    return {
        prefix + key: value
        for key, value in values.items()
    }


def build_dataset(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}

    for item in rows:
        groups.setdefault(item["symbol"], []).append(item)

    output: list[dict[str, Any]] = []

    for symbol, series in groups.items():
        times = [r["t"] for r in series]

        for i, now in enumerate(series):
            previous = series[i - 1] if i > 0 else None

            mid = now["mid"]
            step = now["step"]
            current_volume = normalize(now["vol_bins"])

            current_bin = int(
                (mid - now["min"]) / step
            )

            current_bin = max(
                0, min(now["n"] - 1, current_bin)
            )

            row: dict[str, Any] = {
                "symbol": symbol,
                "tick_server_msc": now["t"],
                "bid": now["bid"],
                "ask": now["ask"],
                "spread_price": now["ask"] - now["bid"],
                "buy_pct_est": now["buy"],
                "sell_pct_est": now["sell"],
                "delta_pp_est": now["delta"],
                "buy_above_50": int(now["buy"] > 50),
                "distance_to_poc": mid - now["poc"],
                "distance_to_vah": mid - now["vah"],
                "distance_to_val": mid - now["val"],
                "poc_price": now["poc"],
                "profile_concentration": concentration(
                    now["vol_bins"]
                ),
                "near_price_volume_share": nearby_activity(
                    now
                ),
                "price_bin_volume_share": current_volume[
                    current_bin
                ],
                "profile_total_activity": now["total"],
                "profile_min": now["min"],
                "profile_step": step,
                "bin_count": now["n"],
            }

            if previous is None:
                row["buy_50_crossover"] = 0
            elif previous["buy"] <= 50 < now["buy"]:
                row["buy_50_crossover"] = 1
            elif previous["buy"] >= 50 > now["buy"]:
                row["buy_50_crossover"] = -1
            else:
                row["buy_50_crossover"] = 0

            for seconds in WINDOWS:
                past = find_past(
                    series, times, i, seconds
                )
                row.update(
                    features(now, past, seconds)
                )

            # Pressure acceleration: difference of
            # two trailing 10-second pressure shifts.
            past10 = find_past(series, times, i, 10)
            past20 = find_past(series, times, i, 20)

            if past10 is not None and past20 is not None:
                row["pressure_acceleration_10s"] = (
                    (now["delta"] - past10["delta"])
                    - (past10["delta"] - past20["delta"])
                )
            else:
                row["pressure_acceleration_10s"] = ""

            output.append(row)

    return output


def save_dataset(
    rows: list[dict[str, Any]],
    path: Path,
) -> None:
    if not rows:
        raise RuntimeError("No features to save")

    path.parent.mkdir(
        parents=True, exist_ok=True
    )

    # Write a new output atomically; never
    # modify the source recorder CSV.
    temporary = path.with_suffix(".csv.tmp")

    with temporary.open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

    os.replace(temporary, path)


def self_test() -> None:
    source = {
        "min": 100.0,
        "step": 1.0,
        "n": 2,
        "vol_bins": [5.0, 5.0],
    }

    target = {
        "min": 100.0,
        "step": 0.5,
        "n": 4,
    }

    actual = project_profile(
        source, target, "vol_bins"
    )

    assert len(actual) == 4
    assert all(
        abs(x - 0.25) < 1e-9 for x in actual
    ), actual

    assert abs(sum(actual) - 1) < 1e-9
    print("PV_PATTERN_SELF_TEST=PASS")


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--source", type=Path,
        default=None
    )

    parser.add_argument(
        "--output", type=Path,
        default=default_output()
    )

    parser.add_argument(
        "--self-test", action="store_true"
    )

    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    source = args.source or default_source()

    if not source.exists():
        raise FileNotFoundError(source)

    snapshots = load_snapshots(source)
    dataset = build_dataset(snapshots)

    save_dataset(dataset, args.output)

    coverage = Counter()

    for row in dataset:
        for seconds in WINDOWS:
            if row.get(f"w{seconds}_observed") == 1:
                coverage[seconds] += 1

    print("PV_PATTERN_STATUS=PASS")
    print(f"FEATURE_ROWS={len(dataset)}")
    print(f"FEATURE_COLUMNS={len(dataset[0])}")
    print(f"10S_HISTORY_AVAILABLE={coverage[10]}")
    print(f"30S_HISTORY_AVAILABLE={coverage[30]}")
    print(f"60S_HISTORY_AVAILABLE={coverage[60]}")
    print(f"OUTPUT={args.output}")
    print("FUTURE_LABELS_USED=NO")
    print("TRADING_ENABLED=NO")


if __name__ == "__main__":
    main()
