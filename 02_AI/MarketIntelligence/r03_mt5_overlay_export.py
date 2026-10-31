
"""PulseViper read-only MT5 chart overlay exporter."""

from __future__ import annotations

import argparse
import importlib
import os
import time
from pathlib import Path
from typing import Any

MTF_ORCHESTRATOR = (
    "04_Testing.production_portability."
    "run_xauusd_r03_v2_orchestrator"
)

SIGNAL_PLANNER = (
    "02_AI.MarketIntelligence.r03_signal_planner"
)

FILE_NAME = "PulseViper_Signal_Levels.csv"


def locate_common_file() -> Path:
    """Get the actual MT5 common files path."""
    mt5: Any = importlib.import_module("MetaTrader5")

    if not mt5.initialize():
        raise RuntimeError(
            f"MT5_INITIALIZE_FAILED: {mt5.last_error()}"
        )

    try:
        info = mt5.terminal_info()

        if info is None:
            raise RuntimeError(
                "MT5_TERMINAL_INFO_UNAVAILABLE"
            )

        common_path = getattr(
            info, "commondata_path", None
        )

        if not common_path:
            raise RuntimeError(
                "MT5_COMMONDATA_PATH_UNAVAILABLE"
            )

        folder = Path(str(common_path)) / "Files"
        folder.mkdir(parents=True, exist_ok=True)

        return folder / FILE_NAME

    finally:
        mt5.shutdown()


def export_once(destination: Path) -> dict[str, Any]:
    orchestrator: Any = importlib.import_module(
        MTF_ORCHESTRATOR
    )
    planner: Any = importlib.import_module(
        SIGNAL_PLANNER
    )

    snapshot = orchestrator.acquire_genuine_snapshot()
    orchestrator.verify_snapshot_authority(snapshot)

    if snapshot.is_synthetic is not False:
        raise RuntimeError("SYNTHETIC_DATA_FORBIDDEN")

    if snapshot.canonical_instrument != "XAUUSD":
        raise RuntimeError("XAUUSD_REQUIRED")

    report: dict[str, Any] = planner.plan(
        snapshot.market_data,
        snapshot.decision_time_utc,
    )

    symbol = str(snapshot.broker_symbol)

    if (
        not symbol
        or "," in symbol
        or "\n" in symbol
        or "\r" in symbol
    ):
        raise RuntimeError("INVALID_SYMBOL")

    decision = planner.MTF.utc_timestamp(
        snapshot.decision_time_utc
    )

    buy = report["buy_setup"]
    sell = report["sell_setup"]

    def level(value: Any) -> str:
        if value is None:
            return "0"
        return str(float(value))

    fields = [
        "PV1",
        symbol,
        str(int(decision.timestamp())),
        str(report["decision"]),
        level(buy["trigger_above"]),
        level(buy["stop_loss"]),
        level(buy["target_1"]),
        level(buy["target_2"]),
        "1" if buy["eligible"] else "0",
        level(sell["trigger_below"]),
        level(sell["stop_loss"]),
        level(sell["target_1"]),
        level(sell["target_2"]),
        "1" if sell["eligible"] else "0",
    ]

    temporary = destination.with_name(
        destination.name + ".tmp"
    )

    temporary.write_text(
        ",".join(fields) + "\n",
        encoding="ascii",
    )

    os.replace(temporary, destination)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true")
    parser.add_argument(
        "--interval", type=int, default=60
    )

    args = parser.parse_args()

    if args.interval < 15:
        parser.error("Minimum interval is 15 seconds")

    try:
        destination = locate_common_file()

    except Exception as exc:
        print("MT5_OVERLAY_STATUS=BLOCKED")
        print(
            "REASON="
            + type(exc).__name__
            + ": "
            + str(exc)
        )
        return 2

    print("MT5_OVERLAY_FILE=" + str(destination))

    try:
        while True:
            try:
                report = export_once(destination)

                print(
                    "MT5_OVERLAY_STATUS=PASS_READ_ONLY"
                )
                print(
                    "DECISION=" + str(report["decision"])
                )
                print(
                    "SNAPSHOT="
                    + str(report["decision_time_utc"])
                )

            except Exception as exc:
                print("MT5_OVERLAY_STATUS=BLOCKED")
                print(
                    "REASON="
                    + type(exc).__name__
                    + ": "
                    + str(exc)
                )

                if not args.watch:
                    return 2

            if not args.watch:
                return 0

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("MT5_OVERLAY_STATUS=STOPPED")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
