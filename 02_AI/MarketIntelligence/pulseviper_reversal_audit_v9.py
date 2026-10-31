
"""
PulseViper V9 - Historical Reversal Audit

Compares screenshot event times with V8 saved predictions.

READ ONLY:
- No model training
- No champion changes
- No trades
- No future information used to create predictions

Chart timezone offset defaults to UTC+3.
Verify this against MT5 broker server time.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

V8_ROOT = (
    ROOT
    / "01_Data"
    / "VolumeMemory"
    / "StableMemoryV2"
    / "DecisionDiagnosticsV8"
)

DEFAULT_RUN = "7a09b7e54f8ef686"

EVENTS = [
    {
        "name": "BOTTOM_REVERSAL",
        "time": "2026-10-30 04:53:00",
        "expected": "BUY",
    },
    {
        "name": "TOP_REVERSAL",
        "time": "2026-10-30 05:17:00",
        "expected": "SELL",
    },
]


def load_predictions(path: Path) -> list[dict]:
    rows = []

    with path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        for row in csv.DictReader(handle):
            try:
                # Use the exact V7-style scenario.
                if abs(float(row["cost"])) > 1e-9:
                    continue

                if abs(
                    float(row["risk_multiplier"]) - 0.5
                ) > 1e-9:
                    continue

                rows.append({
                    "time": int(row["timestamp_msc"]),
                    "symbol": row["symbol"],
                    "action": row["action"],
                    "reason": row["reason"],
                    "pred_buy": float(
                        row["predicted_buy"]
                    ),
                    "pred_sell": float(
                        row["predicted_sell"]
                    ),
                    "adjusted_buy": float(
                        row["adjusted_buy"]
                    ),
                    "adjusted_sell": float(
                        row["adjusted_sell"]
                    ),
                    "actual_buy": float(
                        row["actual_buy_net"]
                    ),
                    "actual_sell": float(
                        row["actual_sell_net"]
                    ),
                    "realized": float(
                        row["realized_net"]
                    ),
                })

            except (KeyError, ValueError, TypeError):
                continue

    rows.sort(key=lambda r: r["time"])
    return rows


def audit_event(
    event: dict,
    rows: list[dict],
    offset_hours: float,
    window_minutes: float,
) -> None:
    chart_time = datetime.strptime(
        event["time"], "%Y-%m-%d %H:%M:%S"
    )

    chart_zone = timezone(
        timedelta(hours=offset_hours)
    )

    utc_time = chart_time.replace(
        tzinfo=chart_zone
    ).astimezone(timezone.utc)

    event_ms = int(utc_time.timestamp() * 1000)
    window_ms = window_minutes * 60_000

    matches = [
        row for row in rows
        if abs(row["time"] - event_ms) <= window_ms
    ]

    matches.sort(
        key=lambda row: abs(row["time"] - event_ms)
    )

    print("\n" + "=" * 66)
    print(f"EVENT={event['name']}")
    print(f"CHART_TIME={event['time']}")
    print(
        "EXPECTED_REVERSAL_DIRECTION="
        f"{event['expected']} (HINDSIGHT)"
    )
    print(f"ASSUMED_CHART_UTC_OFFSET={offset_hours:+g}")
    print(
        "MATCHING_UTC_TIME="
        f"{utc_time.isoformat()}"
    )
    print(f"MATCH_WINDOW_MINUTES={window_minutes}")

    if not matches:
        print("STATUS=NO_SAVED_V8_DECISION_IN_WINDOW")
        print(
            "CONCLUSION=Cannot determine historical "
            "AI behavior for this event"
        )
        return

    print(f"STATUS=MATCHED_{len(matches)}_SAVED_DECISIONS")

    for row in matches[:12]:
        observed_utc = datetime.fromtimestamp(
            row["time"] / 1000,
            tz=timezone.utc,
        )

        gap = (
            row["time"] - event_ms
        ) / 60_000

        print("\n--- HISTORICAL DECISION ---")
        print(f"UTC={observed_utc.isoformat()}")
        print(f"OFFSET_FROM_EVENT_MIN={gap:+.2f}")
        print(f"SYMBOL={row['symbol']}")
        print(f"AI_ACTION={row['action']}")
        print(f"AI_REASON={row['reason']}")
        print(f"PREDICTED_BUY={row['pred_buy']:+.5f}")
        print(f"PREDICTED_SELL={row['pred_sell']:+.5f}")
        print(
            f"ADJUSTED_BUY={row['adjusted_buy']:+.5f}"
        )
        print(
            f"ADJUSTED_SELL={row['adjusted_sell']:+.5f}"
        )
        print(f"ACTUAL_60S_BUY={row['actual_buy']:+.5f}")
        print(f"ACTUAL_60S_SELL={row['actual_sell']:+.5f}")
        print(
            f"ACTUAL_AI_ACTION_NET={row['realized']:+.5f}"
        )

        expected_net = (
            row["actual_buy"]
            if event["expected"] == "BUY"
            else row["actual_sell"]
        )

        print(
            f"HINDSIGHT_EXPECTED_SIDE_60S="
            f"{expected_net:+.5f}"
        )

        if row["action"] == event["expected"]:
            print("DECISION_MATCH=YES")
        elif row["action"] == "WAIT":
            print("DECISION_MATCH=WAIT")
        else:
            print("DECISION_MATCH=OPPOSITE")

        if expected_net <= 0:
            print(
                "NOTE=The chart reversal direction "
                "was not profitable over this exact "
                "60-second observation"
            )

    if len(matches) > 12:
        print(
            f"\nOTHER_MATCHES_NOT_PRINTED="
            f"{len(matches) - 12}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--run-id",
        default=DEFAULT_RUN,
    )

    parser.add_argument(
        "--chart-utc-offset",
        type=float,
        default=3.0,
    )

    parser.add_argument(
        "--window-minutes",
        type=float,
        default=4.0,
    )

    args = parser.parse_args()

    if not -12 <= args.chart_utc_offset <= 14:
        parser.error("Invalid UTC offset")

    if not 0 <= args.window_minutes <= 30:
        parser.error("Invalid time window")

    path = (
        V8_ROOT
        / args.run_id
        / "decision_diagnostics.csv"
    )

    if not path.is_file():
        raise FileNotFoundError(
            f"V8 decision CSV not found: {path}"
        )

    rows = load_predictions(path)

    print("PV_REVERSAL_AUDIT=V9")
    print(f"V8_RUN={args.run_id}")
    print(f"SAVED_DEFAULT_SCENARIO_DECISIONS={len(rows)}")
    print("MODEL_RETRAINED=NO")
    print("TRADING_ENABLED=NO")

    if not rows:
        print("STATUS=NO_MATCHING_V8_SCENARIO")
        return

    print(
        "EARLIEST_SAVED_UTC="
        + datetime.fromtimestamp(
            rows[0]["time"] / 1000,
            timezone.utc,
        ).isoformat()
    )

    print(
        "LATEST_SAVED_UTC="
        + datetime.fromtimestamp(
            rows[-1]["time"] / 1000,
            timezone.utc,
        ).isoformat()
    )

    for event in EVENTS:
        audit_event(
            event,
            rows,
            args.chart_utc_offset,
            args.window_minutes,
        )

    print("\nPV_REVERSAL_AUDIT_STATUS=COMPLETE")
    print("HISTORICAL_PREDICTIONS_ONLY=YES")
    print("TRADING_ENABLED=NO")


if __name__ == "__main__":
    main()
