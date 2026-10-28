from __future__ import annotations

import importlib
import json
from typing import Any

brain: Any = importlib.import_module(
    "02_AI.MarketIntelligence.r03_market_discovery_brain"
)
validator: Any = importlib.import_module(
    "02_AI.MarketIntelligence.r03_market_discovery_validation"
)
orchestrator: Any = importlib.import_module(
    "04_Testing.production_portability.run_xauusd_r03_v2_orchestrator"
)

VERSION = "PULSEVIPER_AUTONOMOUS_RESEARCH_V1"


def evaluate_hypothesis(
    name: str,
    result: dict[str, Any],
    active: bool,
) -> dict[str, Any]:
    count = int(result["count"])
    mean = result["mean_atr_normalized_return"]
    baseline = result["baseline"]

    if count < 30:
        verdict = "INSUFFICIENT_EVIDENCE"
        experiment = "Collect more distinct events across multiple sessions"
    elif baseline is None:
        verdict = "NO_MATCHED_DIRECTIONAL_BASELINE"
        experiment = "Create direction-matched controls"
    elif mean is None:
        verdict = "INSUFFICIENT_EVIDENCE"
        experiment = "Collect valid forward outcomes"
    else:
        excess = mean - baseline["mean_atr_normalized_return"]
        if excess <= 0:
            verdict = "CHALLENGED_BY_HISTORY"
            experiment = "Test whether regime conditioning explains failure"
        else:
            verdict = "EXPLORATORY_CANDIDATE"
            experiment = "Test on untouched, non-overlapping forward events"

    return {
        "hypothesis_id": name,
        "active_in_latest_market": active,
        "historical_decision_count": count,
        "historical_mean_atr_return": mean,
        "verdict": verdict,
        "next_experiment": experiment,
        "independently_validated": False,
        "trading_signal": False,
    }


def research_cycle() -> dict[str, Any]:
    snapshot = orchestrator.acquire_genuine_snapshot()
    orchestrator.verify_snapshot_authority(snapshot)

    if snapshot.is_synthetic is not False:
        raise RuntimeError("SYNTHETIC_DATA_FORBIDDEN")
    if snapshot.canonical_instrument != "XAUUSD":
        raise RuntimeError("INSTRUMENT_MISMATCH")

    market = snapshot.market_data
    if not isinstance(market, dict) or "M5" not in market:
        raise RuntimeError("M5_HISTORY_MISSING")

    m5 = market["M5"]

    current = brain.analyze_m5(m5)
    history = validator.validate_history(m5)

    active_ids = {
        item["id"]
        for item in current["candidate_hypotheses"]
    }

    reviews = [
        evaluate_hypothesis(
            name=name,
            result=result,
            active=(name in active_ids),
        )
        for name, result in history["hypotheses"].items()
    ]

    return {
        "version": VERSION,
        "status": "RESEARCH_ONLY",
        "instrument": snapshot.canonical_instrument,
        "broker_symbol": snapshot.broker_symbol,
        "source_snapshot_id": snapshot.source_snapshot_id,
        "decision_time_utc": snapshot.decision_time_utc,
        "current_evidence": current["evidence"],
        "current_contradictions": current["contradictions"],
        "current_resistance": current["resistance_zone_center"],
        "current_support": current["support_zone_center"],
        "historical_decisions_evaluated": history["evaluated_decisions"],
        "historical_gaps_skipped": history["skipped_due_to_m5_gaps"],
        "research_reviews": reviews,
        "limitations": [
            "Historical horizons may overlap",
            "Research hypothesis families are currently predefined",
            "No independent predictive edge validation",
            "No real cash-flow or hidden-order visibility",
        ],
        "autonomous_code_changes": False,
        "model_retrained": False,
        "ledger_written": False,
        "orders_sent": False,
        "execution_authorized": False,
    }


def main() -> int:
    try:
        report = research_cycle()
    except Exception as exc:
        print("AUTONOMOUS_RESEARCH_STATUS=BLOCKED")
        print("ERROR_TYPE=" + type(exc).__name__)
        print("ERROR=" + str(exc))
        return 2

    print("AUTONOMOUS_RESEARCH_STATUS=PASS_READ_ONLY")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
