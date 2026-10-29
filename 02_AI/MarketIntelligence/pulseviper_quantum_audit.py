
"""
PulseViper Quantum Brain - Alignment Audit V1

Read-only validation of:
1. MT5 live Volume Profile observations
2. Pattern Intelligence features
3. Future reaction labels
4. Timestamp alignment and data integrity

No trading. No model changes. No file overwrites.
"""

from __future__ import annotations

import csv
import math
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "01_Data" / "VolumeMemory"

FEATURES = DATA / "pattern_features_v1.csv"
OUTCOMES = DATA / "reaction_outcomes_v1.csv"

APPDATA = Path(os.environ["APPDATA"])
RECORDER = (
    APPDATA / "MetaQuotes" / "Terminal"
    / "Common" / "Files" / "PulseViper"
    / "VolumeMemory"
    / "XAUUSD_PERIOD_M1_observations.csv"
)

HORIZONS = (15, 30, 60, 120)

failures: list[str] = []
warnings: list[str] = []


def check(condition: bool, message: str) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {message}")
    if not condition:
        failures.append(message)


def warn(message: str) -> None:
    warnings.append(message)
    print(f"[WARN] {message}")


def load(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)

    with path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        return list(csv.DictReader(handle))


def numeric(value: Any) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Non-finite numeric value")
    return result


def timestamp_info(value: int) -> str:
    return datetime.fromtimestamp(
        value / 1000, tz=timezone.utc
    ).isoformat()


def key(row: dict[str, str], field: str) -> tuple[str, int]:
    return row["symbol"], int(row[field])


def validate_recorder(
    rows: list[dict[str, str]],
) -> set[tuple[str, int]]:
    print("\n=== LIVE RECORDER ===")
    print(f"ROWS={len(rows)}")

    valid: set[tuple[str, int]] = set()
    bad = 0
    duplicate = 0
    wrong_formula = 0
    timeline: list[int] = []

    for row in rows:
        try:
            n = int(row["bin_count"])
            t = int(row["tick_server_msc"])
            k = key(row, "tick_server_msc")

            buy = numeric(row["buy_pct_est"])
            sell = numeric(row["sell_pct_est"])
            delta = numeric(row["delta_pp_est"])
            bid = numeric(row["bid"])
            ask = numeric(row["ask"])
            step = numeric(row["profile_step"])

            b = [
                numeric(x)
                for x in row["buy_bins"].split("|")
            ]
            s = [
                numeric(x)
                for x in row["sell_bins"].split("|")
            ]
            v = [
                numeric(x)
                for x in row["volume_bins"].split("|")
            ]

            if (
                n != 64
                or len(b) != n
                or len(s) != n
                or len(v) != n
                or t <= 0
                or bid <= 0
                or ask < bid
                or step <= 0
                or abs(buy + sell - 100) > 0.02
                or abs(delta - (buy - sell)) > 0.02
            ):
                bad += 1
                continue

            if any(
                x < 0 or abs((x + y) - z)
                > max(0.05, z * 0.0001)
                for x, y, z in zip(b, s, v)
            ):
                bad += 1
                continue

            total = sum(v)

            if total <= 0 or (
                abs(sum(b) / total * 100 - buy) > 0.02
            ):
                bad += 1
                continue

            if k in valid:
                duplicate += 1

            valid.add(k)
            timeline.append(t)

            if row.get("formula_version") != (
                "OHLC_TICK_RANGE_V4_EST"
            ):
                wrong_formula += 1

        except (ValueError, KeyError, TypeError):
            bad += 1

    check(bad == 0, f"Recorder invalid rows = {bad}")
    check(
        duplicate == 0,
        f"Duplicate sample timestamps = {duplicate}"
    )
    check(
        wrong_formula == 0,
        f"Unexpected formula versions = {wrong_formula}"
    )
    check(bool(valid), "Valid observations available")

    if timeline:
        check(
            all(a <= b for a, b in zip(
                timeline, timeline[1:]
            )),
            "Recorder timestamps monotonic"
        )

        print(f"FIRST_TICK_UTC={timestamp_info(min(timeline))}")
        print(f"LAST_TICK_UTC={timestamp_info(max(timeline))}")
        print(f"DISTINCT_MINUTES={len({t // 60000 for t in timeline})}")

    return valid


def validate_features(
    rows: list[dict[str, str]],
    recorder_keys: set[tuple[str, int]],
) -> set[tuple[str, int]]:
    print("\n=== PATTERN FEATURES ===")
    print(f"ROWS={len(rows)}")

    keys: set[tuple[str, int]] = set()
    invalid = 0
    mismatched = 0

    for row in rows:
        try:
            k = key(row, "tick_server_msc")
            numeric(row["buy_pct_est"])
            numeric(row["sell_pct_est"])
            numeric(row["profile_step"])

            if k in keys:
                invalid += 1

            keys.add(k)

            if k not in recorder_keys:
                mismatched += 1

            for window in (10, 30, 60):
                flag = row.get(
                    f"w{window}_observed", ""
                )

                if flag not in ("", "1"):
                    invalid += 1

                if flag == "1":
                    numeric(row[f"w{window}_buy_change_pp"])
                    numeric(row[f"w{window}_profile_l1"])

        except (ValueError, KeyError, TypeError):
            invalid += 1

    check(invalid == 0, f"Feature invalid rows = {invalid}")
    check(
        mismatched == 0,
        f"Features missing recorder source = {mismatched}"
    )
    print(f"RECORDER_KEYS_WITHOUT_FEATURES={len(recorder_keys-keys)}")

    return keys


def validate_outcomes(
    rows: list[dict[str, str]],
    recorder_keys: set[tuple[str, int]],
    feature_keys: set[tuple[str, int]],
) -> None:
    print("\n=== FUTURE REACTION LABELS ===")
    print(f"ROWS={len(rows)}")

    counts: Counter[int] = Counter()
    classes: Counter[str] = Counter()

    invalid = 0
    missing_recorder = 0
    missing_features = 0
    duplicates = 0

    seen: set[tuple[str, int, int]] = set()

    for row in rows:
        try:
            k = key(row, "entry_tick_msc")
            h = int(row["horizon_seconds"])
            start = k[1]
            end = int(row["exit_tick_msc"])
            elapsed = numeric(row["elapsed_seconds"])

            label = row["outcome"]

            if (
                h not in HORIZONS
                or label not in {
                    "BUY_POSITIVE",
                    "SELL_POSITIVE",
                    "NEITHER_POSITIVE",
                }
                or end < start + h * 1000
                or elapsed < h
                or abs((end - start) / 1000 - elapsed) > 0.01
            ):
                invalid += 1
                continue

            unique = (k[0], start, h)

            if unique in seen:
                duplicates += 1

            seen.add(unique)

            if k not in recorder_keys:
                missing_recorder += 1

            if k not in feature_keys:
                missing_features += 1

            counts[h] += 1
            classes[label] += 1

        except (ValueError, KeyError, TypeError):
            invalid += 1

    check(invalid == 0, f"Invalid outcome rows = {invalid}")
    check(duplicates == 0, f"Duplicate outcome rows = {duplicates}")
    check(
        missing_recorder == 0,
        f"Labels missing recorder entry = {missing_recorder}"
    )

    if missing_features:
        warn(
            f"{missing_features} labels do not yet have "
            "matching feature snapshots"
        )

    for h in HORIZONS:
        print(f"HORIZON_{h}S={counts[h]}")

    print(f"CLASS_COUNTS={dict(classes)}")
    print(
        f"LABELS_WITHOUT_FEATURES={missing_features}"
    )


def freshness() -> None:
    print("\n=== FILE FRESHNESS ===")

    for name, path in (
        ("RECORDER", RECORDER),
        ("FEATURES", FEATURES),
        ("OUTCOMES", OUTCOMES),
    ):
        modified = datetime.fromtimestamp(
            path.stat().st_mtime,
            tz=timezone.utc,
        )

        print(
            f"{name}_MODIFIED_UTC={modified.isoformat()}"
        )

    if FEATURES.stat().st_mtime < RECORDER.stat().st_mtime:
        warn(
            "Feature dataset is older than recorder. "
            "Refresh features before model training."
        )

    if OUTCOMES.stat().st_mtime < RECORDER.stat().st_mtime:
        warn(
            "Reaction labels are older than recorder. "
            "Refresh outcomes before model training."
        )


def main() -> None:
    print("PULSEVIPER_QUANTUM_ALIGNMENT_AUDIT_V1")
    print("MODE=READ_ONLY")
    print("TRADING_ENABLED=NO")

    for path in (RECORDER, FEATURES, OUTCOMES):
        if not path.is_file():
            raise FileNotFoundError(path)

    source = load(RECORDER)
    feature_rows = load(FEATURES)
    label_rows = load(OUTCOMES)

    recorder_keys = validate_recorder(source)
    feature_keys = validate_features(
        feature_rows, recorder_keys
    )
    validate_outcomes(
        label_rows, recorder_keys, feature_keys
    )
    freshness()

    print("\n=== FINAL RESULT ===")
    print(f"FAILURES={len(failures)}")
    print(f"WARNINGS={len(warnings)}")

    if failures:
        print("PV_QUANTUM_ALIGNMENT=FAIL")
        raise SystemExit(1)

    if warnings:
        print("PV_QUANTUM_ALIGNMENT=PASS_WITH_WARNINGS")
    else:
        print("PV_QUANTUM_ALIGNMENT=PASS")

    print("MODEL_TRAINED=NO")
    print("PROFITABILITY_PROVEN=NO")


if __name__ == "__main__":
    main()
