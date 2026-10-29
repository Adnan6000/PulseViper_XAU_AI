
"""
PulseViper Live Alignment Audit V2

Checks:
- Recorder, features and outcomes share the same keys.
- Missing feature rows are evaluated against an
  actual timestamp watermark, not file modified time.
- Outcome timestamps cannot precede their horizons.
- Feature values match their source recorder snapshot.
- Recent still-arriving observations are allowed.

Read-only. No orders. No model training.
"""

from __future__ import annotations

import csv
import math
import os
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "01_Data" / "VolumeMemory"

SOURCE = (
    Path(os.environ["APPDATA"])
    / "MetaQuotes/Terminal/Common/Files"
    / "PulseViper/VolumeMemory"
    / "XAUUSD_PERIOD_M1_observations.csv"
)

FEATURES = DATA / "pattern_features_v1.csv"
OUTCOMES = DATA / "reaction_outcomes_v1.csv"

HORIZONS = (15, 30, 60, 120)
GRACE_MS = 5_000


def load(path: Path) -> list[dict[str, str]]:
    with path.open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        return list(csv.DictReader(handle))


def make_key(
    row: dict[str, str],
    time_field: str,
) -> tuple[str, int]:
    return (
        row["symbol"],
        int(row[time_field]),
    )


def close(a: str, b: str, tol: float = 0.0001) -> bool:
    x = float(a)
    y = float(b)

    return (
        math.isfinite(x)
        and math.isfinite(y)
        and abs(x - y) <= tol
    )


def main() -> None:
    recorder_rows = load(SOURCE)
    feature_rows = load(FEATURES)
    outcome_rows = load(OUTCOMES)

    if not recorder_rows or not feature_rows:
        raise RuntimeError("Missing recorder or feature rows")

    recorder = {
        make_key(r, "tick_server_msc"): r
        for r in recorder_rows
    }

    features = {
        make_key(r, "tick_server_msc"): r
        for r in feature_rows
    }

    outcome_keys: set[tuple[str, int, int]] = set()
    outcome_counts: Counter[int] = Counter()

    errors: list[str] = []
    warnings: list[str] = []

    feature_watermark = max(
        t for _, t in features
    )

    # Any source observation older than the last
    # generated feature timestamp should ordinarily
    # have a matching feature row.
    mature_source = {
        key
        for key in recorder
        if key[1] <= feature_watermark
    }

    missing = mature_source - features.keys()

    if missing:
        errors.append(
            f"MISSING_MATURE_FEATURES={len(missing)}"
        )

    for key, feature in features.items():
        source = recorder.get(key)

        if source is None:
            errors.append(
                f"FEATURE_SOURCE_MISSING={key}"
            )
            continue

        for column in (
            "buy_pct_est",
            "sell_pct_est",
            "delta_pp_est",
            "poc_price",
            "profile_min",
            "profile_step",
        ):
            if not close(
                source[column],
                feature[column],
            ):
                errors.append(
                    f"FEATURE_MISMATCH={key}:{column}"
                )

    # A label is permitted only if its future
    # timestamp really follows the target horizon.
    for row in outcome_rows:
        entry = make_key(row, "entry_tick_msc")
        horizon = int(row["horizon_seconds"])
        exit_time = int(row["exit_tick_msc"])

        label_key = (
            entry[0],
            entry[1],
            horizon,
        )

        if label_key in outcome_keys:
            errors.append(
                f"DUPLICATE_LABEL={label_key}"
            )

        outcome_keys.add(label_key)
        outcome_counts[horizon] += 1

        if entry not in recorder:
            errors.append(
                f"LABEL_SOURCE_MISSING={entry}"
            )

        if (
            horizon not in HORIZONS
            or exit_time < entry[1] + horizon * 1000
            or exit_time > (
                entry[1] + horizon * 1000 + 3000
            )
        ):
            errors.append(
                f"INVALID_LABEL_TIMING={label_key}"
            )

    latest_recorder = max(t for _, t in recorder)

    new_unprocessed = {
        key
        for key in recorder
        if key[1] > feature_watermark
    }

    if new_unprocessed:
        warnings.append(
            f"LIVE_PENDING_FEATURES={len(new_unprocessed)}"
        )

    if latest_recorder - feature_watermark > 60_000:
        warnings.append(
            "FEATURE_PIPELINE_LAG_EXCEEDS_60_SECONDS"
        )

    print("PV_LIVE_ALIGNMENT_V2")
    print(f"RECORDER_ROWS={len(recorder_rows)}")
    print(f"FEATURE_ROWS={len(feature_rows)}")
    print(f"OUTCOME_ROWS={len(outcome_rows)}")
    print(f"MATURE_FEATURE_GAPS={len(missing)}")
    print(f"LIVE_PENDING_FEATURES={len(new_unprocessed)}")
    print(f"OUTCOME_COUNTS={dict(outcome_counts)}")

    print(f"ERROR_COUNT={len(errors)}")
    print(f"WARNING_COUNT={len(warnings)}")

    for error in errors[:15]:
        print(f"ERROR={error}")

    for warning in warnings:
        print(f"WARNING={warning}")

    if errors:
        print("PV_LIVE_ALIGNMENT=FAIL")
        raise SystemExit(1)

    if warnings:
        print("PV_LIVE_ALIGNMENT=PASS_WITH_LIVE_LAG")
    else:
        print("PV_LIVE_ALIGNMENT=PASS")

    print("TRADING_ENABLED=NO")


if __name__ == "__main__":
    main()
