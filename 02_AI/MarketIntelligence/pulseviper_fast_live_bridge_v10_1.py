
"""
PulseViper Fast Live Feature Bridge V10.1

COMPLETE REPLACEMENT FILE

Purpose:
    Produce fresh feature snapshots using the existing
    PulseViper Pattern Intelligence generator.

Safety:
    - Historical pipeline remains unchanged.
    - No trading or order execution.
    - No checkpoint promotion or model retraining.
    - Feature parity checked before publication.
    - Atomic live-output replacement.
    - Prevents simultaneous bridge instances.
    - Handles Windows temporary-file cleanup failures.

Python 3.12 compatible.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import subprocess
import sys
import tempfile
import time

from collections import deque
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DATA = ROOT / "01_Data" / "VolumeMemory"

MEMORY = DATA / "StableMemoryV2"

HISTORICAL = DATA / "pattern_features_v1.csv"

LIVE_OUTPUT = DATA / "live_pattern_features_v1.csv"

PATTERN_SCRIPT = (
    ROOT
    / "02_AI"
    / "MarketIntelligence"
    / "pulseviper_pattern_intelligence.py"
)

RECORDER = (
    Path(os.environ["APPDATA"])
    / "MetaQuotes"
    / "Terminal"
    / "Common"
    / "Files"
    / "PulseViper"
    / "VolumeMemory"
    / "XAUUSD_PERIOD_M1_observations.csv"
)

ACTIVE = MEMORY / "active_checkpoint.json"

LOCK = DATA / ".pulseviper_fast_bridge.lock"


# ============================================================
# VALIDATION SETTINGS
# ============================================================

ABS_TOLERANCE = 1e-6
REL_TOLERANCE = 1e-5

MIN_INPUT_ROWS = 200
MIN_PARITY_ROWS = 5
PARITY_CHECK_ROWS = 10

PATTERN_TIMEOUT_SECONDS = 180

PUBLISH_RETRIES = 5
PUBLISH_RETRY_DELAY = 0.2


# ============================================================
# CHECKPOINT FEATURE SCHEMA
# ============================================================

def feature_schema() -> list[str]:
    if not ACTIVE.is_file():
        raise FileNotFoundError(
            f"Active checkpoint missing: {ACTIVE}"
        )

    pointer = json.loads(
        ACTIVE.read_text(encoding="utf-8")
    )

    checkpoint_id = str(
        pointer["checkpoint_id"]
    )

    if (
        len(checkpoint_id) != 16
        or any(
            char not in "0123456789abcdef"
            for char in checkpoint_id
        )
    ):
        raise RuntimeError(
            "Invalid active checkpoint identifier"
        )

    metadata_path = (
        MEMORY
        / "checkpoints"
        / checkpoint_id
        / "metadata.json"
    )

    metadata = json.loads(
        metadata_path.read_text(
            encoding="utf-8"
        )
    )

    if metadata["checkpoint_id"] != checkpoint_id:
        raise RuntimeError(
            "Checkpoint metadata mismatch"
        )

    names: list[str] = list(
        metadata["feature_names"]
    )

    if not names:
        raise RuntimeError(
            "Checkpoint feature schema is empty"
        )

    if len(names) != len(set(names)):
        raise RuntimeError(
            "Duplicate checkpoint feature names"
        )

    return names


# ============================================================
# RECORDER SNAPSHOT
# ============================================================

def copy_recent_rows(
    destination: Path,
    limit: int,
) -> int:
    """
    Copy the most recent complete recorder rows.

    Initializes all variables explicitly for Pyright.

    Retry if recorder changes while reading.
    """
    header: bytes = b""

    recent: deque[bytes] = deque(
        maxlen=limit
    )

    stable = False

    for _ in range(3):
        before = RECORDER.stat()

        current_rows: deque[bytes] = deque(
            maxlen=limit
        )

        with RECORDER.open("rb") as source:
            current_header = source.readline()

            if not current_header.endswith(b"\n"):
                raise RuntimeError(
                    "Recorder CSV header incomplete"
                )

            for line in source:
                if line.endswith(b"\n"):
                    current_rows.append(line)

        after = RECORDER.stat()

        if (
            before.st_size == after.st_size
            and before.st_mtime_ns == after.st_mtime_ns
        ):
            header = current_header
            recent = current_rows
            stable = True
            break

    if not stable:
        raise RuntimeError(
            "Recorder changed during snapshot"
        )

    if len(recent) < MIN_INPUT_ROWS:
        raise RuntimeError(
            "Insufficient recorder observations"
        )

    with destination.open("wb") as target:
        target.write(header)
        target.writelines(recent)

    return len(recent)


# ============================================================
# EXISTING PATTERN GENERATOR
# ============================================================

def run_pattern(
    source: Path,
    destination: Path,
) -> None:
    """
    Reuse the project's original feature formulas.
    """
    if not PATTERN_SCRIPT.is_file():
        raise FileNotFoundError(
            f"Pattern generator missing: {PATTERN_SCRIPT}"
        )

    command = [
        sys.executable,
        str(PATTERN_SCRIPT),
        "--source",
        str(source),
        "--output",
        str(destination),
    ]

    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=PATTERN_TIMEOUT_SECONDS,
        check=False,
    )

    if completed.returncode != 0:
        raise RuntimeError(
            "Pattern generator failed\n"
            + completed.stdout[-2000:]
            + "\n"
            + completed.stderr[-2000:]
        )

    if not destination.is_file():
        raise RuntimeError(
            "Pattern generator output missing"
        )


# ============================================================
# FEATURE READING
# ============================================================

def load_features(
    path: Path,
    names: list[str],
) -> dict[tuple[str, int], list[float]]:
    result: dict[
        tuple[str, int],
        list[float],
    ] = {}

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)

        if not reader.fieldnames:
            raise RuntimeError(
                f"Missing feature header: {path}"
            )

        required = set(names) | {
            "symbol",
            "tick_server_msc",
        }

        missing = required - set(
            reader.fieldnames
        )

        if missing:
            raise RuntimeError(
                "Feature schema mismatch: "
                + str(sorted(missing))
            )

        for row in reader:
            try:
                symbol = row["symbol"]

                timestamp = int(
                    row["tick_server_msc"]
                )

                values = [
                    float(row[name])
                    for name in names
                ]

                if (
                    not symbol
                    or timestamp <= 0
                    or not all(
                        math.isfinite(value)
                        for value in values
                    )
                ):
                    continue

                key = (symbol, timestamp)

                if key in result:
                    raise RuntimeError(
                        f"Duplicate feature timestamp: {key}"
                    )

                result[key] = values

            except (
                KeyError,
                TypeError,
                ValueError,
            ):
                continue

    return result


# ============================================================
# HISTORICAL / LIVE PARITY
# ============================================================

def verify_parity(
    candidate: Path,
    names: list[str],
) -> tuple[int, int, float]:
    """
    Compare numerical feature values between
    historical output and proposed live output.

    If fewer than 5 overlapping complete rows exist,
    publication is blocked.
    """
    historical = load_features(
        HISTORICAL,
        names,
    )

    live = load_features(
        candidate,
        names,
    )

    if not live:
        raise RuntimeError(
            "No complete candidate feature vectors"
        )

    common = sorted(
        set(historical).intersection(live),
        key=lambda key: (
            key[1],
            key[0],
        ),
    )

    if len(common) < MIN_PARITY_ROWS:
        raise RuntimeError(
            "PARITY_UNVERIFIED: "
            "Insufficient common feature rows"
        )

    checked = common[-PARITY_CHECK_ROWS:]

    maximum_error = 0.0
    mismatches = 0

    for key in checked:
        old_values = historical[key]
        new_values = live[key]

        if len(old_values) != len(new_values):
            raise RuntimeError(
                "Feature dimension mismatch"
            )

        for old, new in zip(
            old_values,
            new_values,
        ):
            difference = abs(old - new)

            maximum_error = max(
                maximum_error,
                difference,
            )

            tolerance = (
                ABS_TOLERANCE
                + REL_TOLERANCE
                * max(
                    abs(old),
                    abs(new),
                )
            )

            if difference > tolerance:
                mismatches += 1

    return (
        len(checked),
        mismatches,
        maximum_error,
    )


# ============================================================
# LIVE OUTPUT PUBLICATION
# ============================================================

def publish_atomic(
    candidate: Path,
) -> None:
    """
    Atomically replace the dedicated live feature file.

    Historical feature and reaction files are untouched.
    """
    for attempt in range(PUBLISH_RETRIES):
        try:
            os.replace(
                candidate,
                LIVE_OUTPUT,
            )
            return

        except PermissionError:
            if attempt == PUBLISH_RETRIES - 1:
                raise

            time.sleep(
                PUBLISH_RETRY_DELAY
            )

    raise RuntimeError(
        "Live feature publication failed"
    )


# ============================================================
# SINGLE BRIDGE CYCLE
# ============================================================

def one_cycle(
    names: list[str],
    tail_rows: int,
) -> None:
    started = time.perf_counter()

    with tempfile.TemporaryDirectory(
        prefix=".pv_fast_bridge_",
        dir=DATA,
        ignore_cleanup_errors=True,
    ) as temporary:
        folder = Path(temporary)

        source = folder / "recent_recorder.csv"

        candidate = folder / "recent_features.csv"

        input_count = copy_recent_rows(
            source,
            tail_rows,
        )

        run_pattern(
            source,
            candidate,
        )

        checked, mismatches, max_error = (
            verify_parity(
                candidate,
                names,
            )
        )

        if mismatches:
            print(
                "PV_FAST_BRIDGE_STATUS=PARITY_FAILED "
                f"CHECKED={checked} "
                f"MISMATCHES={mismatches} "
                f"MAX_ERROR={max_error:.8f}",
                flush=True,
            )
            return

        # Confirm publication candidate includes
        # valid complete feature vectors.
        available = load_features(
            candidate,
            names,
        )

        if not available:
            raise RuntimeError(
                "No valid feature vectors for publication"
            )

        latest_timestamp = max(
            timestamp
            for _, timestamp in available
        )

        publish_atomic(candidate)

        elapsed = (
            time.perf_counter() - started
        )

        print(
            "PV_FAST_BRIDGE_STATUS=PASS "
            f"INPUT_ROWS={input_count} "
            f"PARITY_CHECKED={checked} "
            "PARITY_MISMATCHES=0 "
            f"MAX_ERROR={max_error:.8f} "
            f"LATEST_FEATURE_TIMESTAMP={latest_timestamp} "
            f"DURATION_SEC={elapsed:.2f} "
            f"OUTPUT={LIVE_OUTPUT}",
            flush=True,
        )


# ============================================================
# PROCESS LOCK
# ============================================================

def acquire_lock() -> None:
    """
    Create a lock file exclusively.

    Never silently remove an existing lock,
    because another bridge may be running.
    """
    try:
        descriptor = os.open(
            str(LOCK),
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
        )

    except FileExistsError as exc:
        raise RuntimeError(
            "Fast bridge lock already exists. "
            "Check for an active bridge instance."
        ) from exc

    with os.fdopen(
        descriptor,
        "w",
        encoding="utf-8",
    ) as handle:
        handle.write(
            json.dumps({
                "pid": os.getpid(),
                "started_at_unix": time.time(),
            })
        )


def release_lock() -> None:
    try:
        LOCK.unlink(missing_ok=True)

    except OSError:
        print(
            "WARNING=LOCK_CLEANUP_FAILED",
            flush=True,
        )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "PulseViper Fast Live Feature Bridge V10.1"
        )
    )

    parser.add_argument(
        "--once",
        action="store_true",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--tail-rows",
        type=int,
        default=4000,
    )

    args = parser.parse_args()

    if not 5 <= args.interval <= 300:
        parser.error(
            "Interval must be between 5 and 300 seconds"
        )

    if not 500 <= args.tail_rows <= 100000:
        parser.error(
            "Tail rows must be between 500 and 100000"
        )

    DATA.mkdir(
        parents=True,
        exist_ok=True,
    )

    acquire_lock()

    try:
        names = feature_schema()

        print("PV_FAST_LIVE_BRIDGE=V10.1")
        print(f"FEATURE_DIMENSIONS={len(names)}")
        print(f"TAIL_ROWS={args.tail_rows}")
        print(
            "HISTORICAL_PIPELINE_MODIFIED=NO"
        )
        print("CHAMPION_CHANGED=NO")
        print("TRADING_ENABLED=NO")

        while True:
            try:
                one_cycle(
                    names,
                    args.tail_rows,
                )

            except (
                OSError,
                RuntimeError,
                ValueError,
                subprocess.TimeoutExpired,
                csv.Error,
            ) as exc:
                print(
                    "PV_FAST_BRIDGE_STATUS=ERROR "
                    f"TYPE={type(exc).__name__} "
                    f"MESSAGE={exc}",
                    flush=True,
                )

            if args.once:
                break

            time.sleep(
                args.interval
            )

    except KeyboardInterrupt:
        print(
            "FAST_BRIDGE_STOPPED=YES",
            flush=True,
        )

    finally:
        release_lock()


if __name__ == "__main__":
    main()
