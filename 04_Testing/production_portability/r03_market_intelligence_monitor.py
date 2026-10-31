from __future__ import annotations

import importlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


VERSION = "R03_MARKET_INTELLIGENCE_MONITOR_V1"

REPO_ROOT = Path(__file__).resolve().parents[2]

controller: Any = importlib.import_module(
    "02_AI.Models.r03_prospective_collection_controller"
)

LABELS = ("SHORT", "NO_TRADE", "LONG")


class MarketIntelligenceError(RuntimeError):
    pass


def analyze_probabilities(
    probabilities: list[tuple[float, float, float]],
) -> dict[str, Any]:

    if not probabilities:
        raise MarketIntelligenceError(
            "NO_PROSPECTIVE_OBSERVATIONS"
        )

    predictions: list[str] = []
    confidences: list[float] = []
    entropies: list[float] = []

    for values in probabilities:
        if len(values) != 3:
            raise MarketIntelligenceError(
                "INVALID_PROBABILITY_VECTOR"
            )

        if not all(
            math.isfinite(value) and 0 <= value <= 1
            for value in values
        ):
            raise MarketIntelligenceError(
                "INVALID_PROBABILITY_VALUE"
            )

        if abs(sum(values) - 1.0) > 1e-5:
            raise MarketIntelligenceError(
                "PROBABILITIES_NOT_NORMALIZED"
            )

        index = max(
            range(3),
            key=lambda i: values[i],
        )

        predictions.append(LABELS[index])
        confidences.append(max(values))

        entropy = -sum(
            value * math.log(value)
            for value in values
            if value > 0
        ) / math.log(3)

        entropies.append(entropy)

    count = len(predictions)
    distribution = Counter(predictions)

    return {
        "version": VERSION,
        "observation_count": count,
        "predicted_class_distribution": {
            label: distribution[label]
            for label in LABELS
        },
        "predicted_class_share": {
            label: round(
                distribution[label] / count,
                6,
            )
            for label in LABELS
        },
        "mean_top_class_confidence": round(
            sum(confidences) / count,
            6,
        ),
        "mean_normalized_entropy": round(
            sum(entropies) / count,
            6,
        ),
        "unique_predicted_classes": len(distribution),
        "market_regime_identified": False,
        "predictive_edge_established": False,
        "drift_established": False,
        "model_retraining_authorized": False,
        "performance_evaluated": False,
        "pnl_evaluated": False,
        "live_authorized": False,
        "execution_authorized": False,
    }


def run_monitor(
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:

    state = controller.inspect_state(
        repo_root=repo_root
    )

    observations = controller.read_observations(
        repo_root=repo_root
    )

    if len(observations) != state.observation_count:
        raise MarketIntelligenceError(
            "OBSERVATION_COUNT_MISMATCH"
        )

    probabilities = [
        (
            float(record.probability_short),
            float(record.probability_no_trade),
            float(record.probability_long),
        )
        for _, record in sorted(observations.items())
    ]

    report = analyze_probabilities(probabilities)

    report["matured_outcome_count"] = (
        state.matured_outcome_count
    )
    report["pending_count"] = state.pending_count
    report["collection_target_reached"] = (
        state.collection_target_reached
    )

    return report


def main() -> int:
    try:
        report = run_monitor()
    except Exception as exc:
        print("R03_INTELLIGENCE_STATUS=BLOCKED")
        print("ERROR_TYPE=" + type(exc).__name__)
        print("ERROR=" + str(exc))
        return 2

    print("R03_INTELLIGENCE_STATUS=PASS_READ_ONLY")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())