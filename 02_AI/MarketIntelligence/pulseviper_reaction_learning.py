
"""
PulseViper Market Reaction Learning V1

Research-only outcome builder.
Reads live Volume Profile snapshots.
Labels future 15/30/60/120-second reactions.
Does NOT train a model or place trades.

Python standard library only.
"""

from __future__ import annotations

import argparse
import csv
import os
from bisect import bisect_left
from datetime import datetime, timezone
from pathlib import Path


HORIZONS = (15, 30, 60, 120)
MAX_DELAY_SECONDS = 3.0

REQUIRED = (
    "tick_server_msc",
    "symbol",
    "bid",
    "ask",
    "buy_pct_est",
    "sell_pct_est",
    "delta_pp_est",
    "poc_price",
    "vah_price",
    "val_price",
    "profile_min",
    "profile_step",
    "bin_count",
    "buy_bins",
    "sell_bins",
    "volume_bins",
)

OUTPUT_FIELDS = [
    "symbol",
    "entry_time_utc",
    "entry_tick_msc",
    "bid",
    "ask",
    "spread_price",
    "buy_pct_est",
    "sell_pct_est",
    "delta_pp_est",
    "poc_price",
    "vah_price",
    "val_price",
    "distance_to_poc",
    "profile_min",
    "profile_step",
    "bin_count",
    "buy_bins",
    "sell_bins",
    "volume_bins",
    "horizon_seconds",
    "exit_tick_msc",
    "elapsed_seconds",
    "exit_bid",
    "exit_ask",
    "mid_price_change",
    "buy_net_price_change",
    "sell_net_price_change",
    "outcome",
]


def default_source() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA environment variable missing")

    return (
        Path(appdata)
        / "MetaQuotes"
        / "Terminal"
        / "Common"
        / "Files"
        / "PulseViper"
        / "VolumeMemory"
        / "XAUUSD_PERIOD_M1_observations.csv"
    )


def parse_vector(value: str, expected: int) -> list[float]:
    numbers = [float(x) for x in value.split("|")]

    if len(numbers) != expected:
        raise ValueError(
            f"Expected {expected} bins, got {len(numbers)}"
        )

    return numbers


def load_snapshots(path: Path) -> list[dict]:
    rows: list[dict] = []
    seen: set[tuple[str, int]] = set()

    with path.open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)

        if not reader.fieldnames:
            raise ValueError("CSV header missing")

        missing = set(REQUIRED) - set(reader.fieldnames)
        if missing:
            raise ValueError(f"Missing fields: {sorted(missing)}")

        for raw in reader:
            try:
                symbol = str(raw["symbol"]).strip()
                time_msc = int(raw["tick_server_msc"])
                bid = float(raw["bid"])
                ask = float(raw["ask"])
                buy = float(raw["buy_pct_est"])
                sell = float(raw["sell_pct_est"])
                count = int(raw["bin_count"])

                if not symbol or time_msc <= 0:
                    continue

                if bid <= 0 or ask < bid:
                    continue

                if count < 1 or count > 512:
                    continue

                if abs((buy + sell) - 100.0) > 0.02:
                    continue

                key = (symbol, time_msc)
                if key in seen:
                    continue

                buy_bins = parse_vector(raw["buy_bins"], count)
                sell_bins = parse_vector(raw["sell_bins"], count)
                volume_bins = parse_vector(
                    raw["volume_bins"], count
                )

                if any(v < 0 for v in volume_bins):
                    continue

                seen.add(key)

                rows.append(
                    {
                        "symbol": symbol,
                        "t": time_msc,
                        "bid": bid,
                        "ask": ask,
                        "buy": buy,
                        "sell": sell,
                        "delta": float(raw["delta_pp_est"]),
                        "poc": float(raw["poc_price"]),
                        "vah": float(raw["vah_price"]),
                        "val": float(raw["val_price"]),
                        "profile_min": float(
                            raw["profile_min"]
                        ),
                        "profile_step": float(
                            raw["profile_step"]
                        ),
                        "bin_count": count,
                        "buy_bins": buy_bins,
                        "sell_bins": sell_bins,
                        "volume_bins": volume_bins,
                    }
                )
            except (ValueError, TypeError, KeyError):
                # A recorder may be writing a partial
                # final line while the file is read.
                continue

    rows.sort(key=lambda row: (row["symbol"], row["t"]))
    return rows


def create_outcomes(
    snapshots: list[dict],
    output: Path,
) -> tuple[int, int]:
    grouped: dict[str, list[dict]] = {}

    for row in snapshots:
        grouped.setdefault(row["symbol"], []).append(row)

    output.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped = 0

    with output.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=OUTPUT_FIELDS
        )
        writer.writeheader()

        for symbol, series in grouped.items():
            timestamps = [row["t"] for row in series]

            for entry in series:
                t = entry["t"]

                entry_mid = (
                    entry["bid"] + entry["ask"]
                ) / 2.0

                for seconds in HORIZONS:
                    target = t + seconds * 1000

                    # Use the first available quote
                    # at or AFTER the target timestamp.
                    index = bisect_left(timestamps, target)

                    if index >= len(series):
                        skipped += 1
                        continue

                    exit_row = series[index]
                    elapsed = (
                        exit_row["t"] - t
                    ) / 1000.0

                    if elapsed > (
                        seconds + MAX_DELAY_SECONDS
                    ):
                        skipped += 1
                        continue

                    exit_mid = (
                        exit_row["bid"] + exit_row["ask"]
                    ) / 2.0

                    # BUY enters at ask, exits at bid.
                    buy_change = (
                        exit_row["bid"] - entry["ask"]
                    )

                    # SELL enters at bid, exits at ask.
                    sell_change = (
                        entry["bid"] - exit_row["ask"]
                    )

                    if buy_change > 0 and sell_change <= 0:
                        outcome = "BUY_POSITIVE"
                    elif sell_change > 0 and buy_change <= 0:
                        outcome = "SELL_POSITIVE"
                    else:
                        outcome = "NEITHER_POSITIVE"

                    utc_time = datetime.fromtimestamp(
                        t / 1000.0,
                        tz=timezone.utc,
                    ).isoformat()

                    writer.writerow(
                        {
                            "symbol": symbol,
                            "entry_time_utc": utc_time,
                            "entry_tick_msc": t,
                            "bid": entry["bid"],
                            "ask": entry["ask"],
                            "spread_price": (
                                entry["ask"] - entry["bid"]
                            ),
                            "buy_pct_est": entry["buy"],
                            "sell_pct_est": entry["sell"],
                            "delta_pp_est": entry["delta"],
                            "poc_price": entry["poc"],
                            "vah_price": entry["vah"],
                            "val_price": entry["val"],
                            "distance_to_poc": (
                                entry_mid - entry["poc"]
                            ),
                            "profile_min": entry["profile_min"],
                            "profile_step": entry["profile_step"],
                            "bin_count": entry["bin_count"],
                            "buy_bins": "|".join(
                                str(v) for v in entry["buy_bins"]
                            ),
                            "sell_bins": "|".join(
                                str(v) for v in entry["sell_bins"]
                            ),
                            "volume_bins": "|".join(
                                str(v) for v in entry["volume_bins"]
                            ),
                            "horizon_seconds": seconds,
                            "exit_tick_msc": exit_row["t"],
                            "elapsed_seconds": round(
                                elapsed, 3
                            ),
                            "exit_bid": exit_row["bid"],
                            "exit_ask": exit_row["ask"],
                            "mid_price_change": round(
                                exit_mid - entry_mid, 6
                            ),
                            "buy_net_price_change": round(
                                buy_change, 6
                            ),
                            "sell_net_price_change": round(
                                sell_change, 6
                            ),
                            "outcome": outcome,
                        }
                    )
                    written += 1

    return written, skipped


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--source",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("01_Data")
        / "VolumeMemory"
        / "reaction_outcomes_v1.csv",
    )

    args = parser.parse_args()

    source = args.source or default_source()

    if not source.is_file():
        raise FileNotFoundError(
            f"Recorder CSV not found: {source}"
        )

    snapshots = load_snapshots(source)

    if not snapshots:
        raise RuntimeError(
            "No valid snapshots in recorder CSV"
        )

    written, skipped = create_outcomes(
        snapshots, args.output
    )

    print("PV_REACTION_STATUS=PASS")
    print(f"VALID_SNAPSHOTS={len(snapshots)}")
    print(f"LABELED_ROWS={written}")
    print(f"SKIPPED_HORIZONS={skipped}")
    print(f"OUTPUT={args.output.resolve()}")
    print("TRADING_ENABLED=NO")


if __name__ == "__main__":
    main()
