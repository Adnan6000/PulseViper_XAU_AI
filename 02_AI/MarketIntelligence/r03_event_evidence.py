
from __future__ import annotations

import importlib
import json
from typing import Any

import numpy as np
import pandas as pd

VERSION = "PULSEVIPER_EVENT_EVIDENCE_V2_2"
LOOKBACK = 60
HORIZON = 12
MIN_PAIRS = 30

brain: Any = importlib.import_module(
    "02_AI.MarketIntelligence.r03_market_discovery_brain"
)
validator: Any = importlib.import_module(
    "02_AI.MarketIntelligence.r03_market_discovery_validation"
)


def summary(values: list[float]) -> dict[str, Any]:
    if not values:
        return {
            "count": 0,
            "mean_atr_return": None,
            "positive_share": None,
        }

    array = np.asarray(values, dtype=np.float64)

    return {
        "count": len(values),
        "mean_atr_return": round(
            float(array.mean()), 6
        ),
        "positive_share": round(
            float((array > 0).mean()), 6
        ),
    }


def directions(report: dict[str, Any]) -> dict[str, int]:
    result: dict[str, int] = {}

    for item in report["candidate_hypotheses"]:
        name = str(item["id"])

        if name == "UPPER_ZONE_REJECTION":
            result[name] = -1
        elif name == "LOWER_ZONE_DEFENSE":
            result[name] = 1
        elif name == "FAILED_BREAK_CONTINUATION":
            if report["failed_break_above"]:
                result[name] = -1
            elif report["failed_break_below"]:
                result[name] = 1

    return result


def separated(
    index: int,
    other_indices: list[int],
) -> bool:
    # Decisions at least 12 completed bars apart
    # have disjoint future windows [i+1, i+12].
    return all(
        abs(index - other) >= HORIZON
        for other in other_indices
    )


def build_decision_rows(
    frame: pd.DataFrame,
) -> tuple[list[dict[str, Any]], int, int]:
    data = validator.prepare_history(frame)
    rows: list[dict[str, Any]] = []
    skipped = 0

    for i in range(LOOKBACK - 1, len(data) - HORIZON):
        window = data.iloc[
            i - LOOKBACK + 1 : i + HORIZON + 1
        ]

        if not validator.consecutive_m5(window):
            skipped += 1
            continue

        past = data.iloc[i - LOOKBACK + 1 : i + 1]
        report = brain.analyze_m5(past)

        atr = float(report["atr14_price_units"])
        if not np.isfinite(atr) or atr <= 0:
            raise ValueError("INVALID_DECISION_ATR")

        start = float(data["close"].iloc[i])
        end = float(data["close"].iloc[i + HORIZON])

        timestamp = pd.Timestamp(
            data["time"].iloc[i]
        )
        if not isinstance(timestamp, pd.Timestamp):
            raise ValueError("INVALID_DECISION_TIME")

        rows.append({
            "index": i,
            "decision_time_utc": (
                timestamp + pd.Timedelta(minutes=5)
            ).isoformat(),
            "session": timestamp.hour // 6,
            "atr_pct": atr / start,
            "forward": (end - start) / atr,
            "directions": directions(report),
        })

    return rows, skipped, len(data)


def evaluate_events(frame: pd.DataFrame) -> dict[str, Any]:
    rows, skipped, history_bars = (
        build_decision_rows(frame)
    )

    results: dict[str, Any] = {}

    for name in validator.HYPOTHESES:
        candidates = [
            row for row in rows
            if name in row["directions"]
        ]

        # One selected event per non-overlapping
        # future horizon, in chronological order.
        events: list[dict[str, Any]] = []
        event_indices: list[int] = []

        for row in candidates:
            idx = int(row["index"])
            if separated(idx, event_indices):
                events.append(row)
                event_indices.append(idx)

        all_event_returns = [
            int(row["directions"][name])
            * float(row["forward"])
            for row in events
        ]

        control_pool = [
            row for row in rows
            if name not in row["directions"]
        ]

        used_control_indices: list[int] = []
        paired_event_returns: list[float] = []
        paired_control_returns: list[float] = []
        pairs: list[dict[str, Any]] = []

        for event in events:
            direction = int(
                event["directions"][name]
            )
            event_idx = int(event["index"])
            event_atr = float(event["atr_pct"])

            eligible: list[dict[str, Any]] = []

            for control in control_pool:
                idx = int(control["index"])

                if control["session"] != event["session"]:
                    continue

                ratio = (
                    float(control["atr_pct"])
                    / event_atr
                )
                if not 0.75 <= ratio <= 1.25:
                    continue

                # Control cannot overlap any
                # selected event horizon.
                if not separated(idx, event_indices):
                    continue

                # Controls also cannot overlap
                # one another.
                if not separated(
                    idx, used_control_indices
                ):
                    continue

                eligible.append(control)

            if not eligible:
                continue

            # Deterministic nearest-time match.
            # This is retrospective matching, not
            # a causal or randomized experiment.
            selected = min(
                eligible,
                key=lambda row: (
                    abs(
                        int(row["index"])
                        - event_idx
                    ),
                    abs(
                        float(row["atr_pct"])
                        / event_atr - 1.0
                    ),
                    int(row["index"]),
                ),
            )

            control_idx = int(selected["index"])
            used_control_indices.append(control_idx)

            event_return = (
                direction * float(event["forward"])
            )
            control_return = (
                direction * float(selected["forward"])
            )

            paired_event_returns.append(event_return)
            paired_control_returns.append(
                control_return
            )

            pairs.append({
                "event_decision_utc": (
                    event["decision_time_utc"]
                ),
                "control_decision_utc": (
                    selected["decision_time_utc"]
                ),
                "direction": (
                    "LONG" if direction > 0
                    else "SHORT"
                ),
                "event_index": event_idx,
                "control_index": control_idx,
                "event_atr_return": round(
                    event_return, 6
                ),
                "control_atr_return": round(
                    control_return, 6
                ),
                "difference_atr": round(
                    event_return - control_return,
                    6,
                ),
            })

        differences = [
            event - control
            for event, control in zip(
                paired_event_returns,
                paired_control_returns,
            )
        ]

        enough = len(pairs) >= MIN_PAIRS

        results[name] = {
            "raw_candidate_decisions": len(candidates),
            "non_overlapping_events": summary(
                all_event_returns
            ),
            "unmatched_event_count": (
                len(events) - len(pairs)
            ),
            "paired_event_statistics": summary(
                paired_event_returns
            ),
            "paired_control_statistics": summary(
                paired_control_returns
            ),
            "paired_difference_statistics": summary(
                differences
            ),
            "matched_pair_count": len(pairs),
            "example_pairs": pairs[:5],
            "enough_evidence_for_further_research": enough,
            "verdict": (
                "EXPLORATORY_ONLY" if enough
                else "INSUFFICIENT_EVIDENCE"
            ),
            "independently_validated": False,
            "predictive_edge_established": False,
        }

    return {
        "version": VERSION,
        "status": "EXPLORATORY_READ_ONLY",
        "history_bars": history_bars,
        "eligible_decisions": len(rows),
        "skipped_gap_decisions": skipped,
        "horizon_bars": HORIZON,
        "hypotheses": results,
        "limitations": [
            "Matched pairs are retrospective, not randomized",
            "Matching uses UTC time block and ATR ratio",
            "Control matching is greedy and order-dependent",
            "Different hypothesis families can share horizons",
            "Multiple-testing adjustment is not implemented",
            "Independent out-of-sample validation is pending",
            "No costs, spread, slippage or cash-flow inference",
            "No autonomous production code modification",
        ],
        "ledger_written": False,
        "model_retrained": False,
        "orders_sent": False,
        "execution_authorized": False,
    }


def main() -> int:
    try:
        orchestrator: Any = importlib.import_module(
            "04_Testing.production_portability."
            "run_xauusd_r03_v2_orchestrator"
        )

        snapshot = (
            orchestrator.acquire_genuine_snapshot()
        )
        orchestrator.verify_snapshot_authority(
            snapshot
        )

        if snapshot.is_synthetic is not False:
            raise ValueError(
                "SYNTHETIC_SNAPSHOT_FORBIDDEN"
            )

        if snapshot.canonical_instrument != "XAUUSD":
            raise ValueError("INSTRUMENT_MISMATCH")

        market = snapshot.market_data

        if (
            not isinstance(market, dict)
            or "M5" not in market
        ):
            raise ValueError("M5_HISTORY_MISSING")

        result = evaluate_events(market["M5"])
        result["source_snapshot_id"] = (
            snapshot.source_snapshot_id
        )
        result["decision_time_utc"] = (
            snapshot.decision_time_utc
        )

    except Exception as exc:
        print("EVENT_EVIDENCE_STATUS=BLOCKED")
        print("ERROR_TYPE=" + type(exc).__name__)
        print("ERROR=" + str(exc))
        return 2

    print("EVENT_EVIDENCE_STATUS=PASS_READ_ONLY")
    print(json.dumps(
        result, indent=2, sort_keys=True
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
