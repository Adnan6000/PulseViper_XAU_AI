
"""
PulseViper Auto Intelligence Pipeline V1.1

Fixes Windows cross-drive publishing error.

- Frozen recorder snapshot
- Features and labels from same source
- Temporary files on project D: drive
- Validated publication
- Automatic periodic updates
- No model training or trading
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULES = Path(__file__).resolve().parent
DATA = ROOT / "01_Data" / "VolumeMemory"

SOURCE = (
    Path(os.environ["APPDATA"])
    / "MetaQuotes"
    / "Terminal"
    / "Common"
    / "Files"
    / "PulseViper"
    / "VolumeMemory"
    / "XAUUSD_PERIOD_M1_observations.csv"
)

FEATURE_SCRIPT = (
    MODULES / "pulseviper_pattern_intelligence.py"
)
REACTION_SCRIPT = (
    MODULES / "pulseviper_reaction_learning.py"
)

FEATURE_OUTPUT = DATA / "pattern_features_v1.csv"
REACTION_OUTPUT = DATA / "reaction_outcomes_v1.csv"


def read_keys(
    path: Path,
    time_field: str,
) -> set[tuple[str, int]]:
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        return {
            (row["symbol"], int(row[time_field]))
            for row in csv.DictReader(handle)
        }


def run_script(
    script: Path,
    source: Path,
    output: Path,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--source",
            str(source),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"{script.name} failed\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    print(result.stdout.strip())


def synchronized_build() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)

    DATA.mkdir(
        parents=True,
        exist_ok=True,
    )

    # CRITICAL:
    # TemporaryDirectory is now created on D:
    # where the final datasets also reside.
    with tempfile.TemporaryDirectory(
        prefix=".pv_pipeline_",
        dir=DATA,
    ) as temporary:
        temp = Path(temporary)

        snapshot = temp / "snapshot.csv"
        temp_features = temp / "features.csv"
        temp_reactions = temp / "reactions.csv"

        # Copy live recorder without modifying it.
        shutil.copyfile(SOURCE, snapshot)

        # Remove incomplete trailing record.
        with snapshot.open("rb+") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()

            if size == 0:
                raise RuntimeError(
                    "Recorder snapshot is empty"
                )

            # Search for last complete line.
            handle.seek(0)
            content = handle.read()

            newline = content.rfind(b"\n")

            if newline < 0:
                raise RuntimeError(
                    "No complete CSV records available"
                )

            handle.truncate(newline + 1)

        run_script(
            FEATURE_SCRIPT,
            snapshot,
            temp_features,
        )

        run_script(
            REACTION_SCRIPT,
            snapshot,
            temp_reactions,
        )

        source_keys = read_keys(
            snapshot,
            "tick_server_msc",
        )

        feature_keys = read_keys(
            temp_features,
            "tick_server_msc",
        )

        reaction_keys = read_keys(
            temp_reactions,
            "entry_tick_msc",
        )

        if not source_keys:
            raise RuntimeError(
                "No valid source observations"
            )

        if source_keys != feature_keys:
            raise RuntimeError(
                "Feature alignment failed"
            )

        if not reaction_keys.issubset(
            feature_keys
        ):
            raise RuntimeError(
                "Reaction alignment failed"
            )

        # Same-drive atomic file replacement.
        # Each output is individually atomic.
        os.replace(
            temp_features,
            FEATURE_OUTPUT,
        )

        os.replace(
            temp_reactions,
            REACTION_OUTPUT,
        )

        print("PV_AUTO_PIPELINE=PASS")
        print(
            f"SOURCE_SNAPSHOTS={len(source_keys)}"
        )
        print(
            f"FEATURE_SNAPSHOTS={len(feature_keys)}"
        )
        print(
            f"LABELED_ENTRY_TIMES={len(reaction_keys)}"
        )
        print("SAME_SOURCE_CHECKPOINT=YES")
        print("TRADING_ENABLED=NO")


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--once",
        action="store_true",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=60,
    )

    args = parser.parse_args()

    if args.interval < 10:
        parser.error(
            "Minimum interval is 10 seconds"
        )

    while True:
        try:
            synchronized_build()

        except (
            OSError,
            ValueError,
            RuntimeError,
        ) as error:
            print(
                f"PV_AUTO_PIPELINE=ERROR: {error}",
                file=sys.stderr,
            )

            if args.once:
                raise SystemExit(1)

        if args.once:
            return

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
