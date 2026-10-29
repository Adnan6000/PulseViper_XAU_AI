
"""PulseViper: listen to the active MT5 chart timeframe."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import importlib

MT5: Any = importlib.import_module("MetaTrader5")

SUPPORTED = {
    "M5", "M15", "M30", "H1", "H4"
}

def chart_file() -> Path:
    if not MT5.initialize():
        raise RuntimeError(
            f"MT5_INITIALIZE_FAILED: {MT5.last_error()}"
        )

    try:
        info = MT5.terminal_info()

        if info is None:
            raise RuntimeError("TERMINAL_INFO_MISSING")

        return (
            Path(str(info.commondata_path))
            / "Files"
            / "PulseViper_Active_Chart.csv"
        )
    finally:
        MT5.shutdown()


def read_chart(path: Path) -> tuple[str, str, str] | None:
    if not path.is_file():
        return None

    fields = path.read_text(
        encoding="ascii"
    ).strip().split(",")

    if len(fields) != 5:
        return None

    version, symbol, timeframe, chart_id, stamp = fields

    if version != "PV_CHART_V1":
        return None

    if not stamp.isdigit():
        return None

    # Prevent an old saved file being treated as live.
    if abs(time.time() - int(stamp)) > 30:
        return None

    if not chart_id.lstrip("-").isdigit():
        return None

    return symbol, timeframe, chart_id


def explain(symbol: str, timeframe: str) -> None:
    print()
    print("=== PULSEVIPER CHART INTELLIGENCE ===")
    print(f"Active symbol: {symbol}")
    print(f"Active timeframe: {timeframe}")

    if timeframe == "M1":
        print(
            "M1 scalping chart detect ho gaya. "
            "Native M1 research abhi integrate hona baqi hai."
        )
    elif timeframe in SUPPORTED:
        print(
            f"{timeframe} structure research ke liye "
            "supported hai. Timeframe-specific signal "
            "generation abhi pending hai."
        )
    elif timeframe == "D1":
        print(
            "D1 chart detect ho gaya. "
            "Canonical daily reconstruction pending hai."
        )
    else:
        print(
            "Timeframe detect ho gaya, lekin "
            "research support abhi available nahi."
        )


def main() -> int:
    try:
        path = chart_file()
    except Exception as exc:
        print("CHART_LISTENER_STATUS=BLOCKED")
        print(type(exc).__name__, str(exc))
        return 2

    print("CHART_LISTENER_STATUS=WATCHING")
    print("FILE=" + str(path))

    previous: tuple[str, str, str] | None = None

    try:
        while True:
            current = read_chart(path)

            if current is not None and current != previous:
                symbol, timeframe, _chart_id = current
                explain(symbol, timeframe)
                previous = current

            time.sleep(2)

    except KeyboardInterrupt:
        print("CHART_LISTENER_STATUS=STOPPED")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
