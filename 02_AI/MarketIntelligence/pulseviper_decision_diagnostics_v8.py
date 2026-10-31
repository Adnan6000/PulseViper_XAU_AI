
"""
PulseViper Quantum Brain V8
Frozen Cost Sensitivity & Explainable WAIT Diagnostics

Reuses the existing V7 data preparation module.

One frozen source snapshot.
One trained regression model.
One fixed chronological test set.
Multiple cost/risk scenarios on identical observations.

No trading, promotion, or champion checkpoint changes.
"""

from __future__ import annotations

import csv
import hashlib
import json
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from sklearn.ensemble import RandomForestRegressor

import pulseviper_decision_intelligence_v7 as v7


OUTPUT = v7.MEMORY / "DecisionDiagnosticsV8"

COSTS = (0.00, 0.05, 0.10, 0.20)
RISKS = (0.00, 0.25, 0.50, 1.00)


def classify_decision(
    predicted_buy: float,
    predicted_sell: float,
    buy_error: float,
    sell_error: float,
    cost: float,
    risk: float,
) -> tuple[str, str]:
    raw_best = max(predicted_buy, predicted_sell)

    if raw_best <= 0:
        return "WAIT", "NEGATIVE_EXPECTED_PAYOFF"

    adjusted_buy = (
        predicted_buy - risk * buy_error
    )
    adjusted_sell = (
        predicted_sell - risk * sell_error
    )

    if max(adjusted_buy, adjusted_sell) <= 0:
        return "WAIT", "UNCERTAINTY_PENALTY"

    final_buy = adjusted_buy - cost
    final_sell = adjusted_sell - cost

    if max(final_buy, final_sell) <= 0:
        return "WAIT", "EXECUTION_COST"

    if final_buy >= final_sell:
        return "BUY", "POSITIVE_ADJUSTED_BUY"

    return "SELL", "POSITIVE_ADJUSTED_SELL"


def evaluate_scenario(
    samples: list[v7.Sample],
    predictions: NDArray[np.float64],
    errors: NDArray[np.float64],
    cost: float,
    risk: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    actions: list[str] = []
    reasons: Counter[str] = Counter()
    output_rows: list[dict[str, Any]] = []

    missed_profitable = 0
    missed_best_payoff = 0.0
    avoided_losses = 0

    for sample, estimate in zip(samples, predictions):
        buy_prediction = float(estimate[0])
        sell_prediction = float(estimate[1])

        action, reason = classify_decision(
            buy_prediction,
            sell_prediction,
            float(errors[0]),
            float(errors[1]),
            cost,
            risk,
        )

        actions.append(action)
        reasons[reason] += 1

        actual_buy = sample.buy_raw - cost
        actual_sell = sample.sell_raw - cost
        actual_best = max(
            0.0, actual_buy, actual_sell
        )

        if action == "WAIT":
            if actual_best > 0:
                missed_profitable += 1
                missed_best_payoff += actual_best
            else:
                avoided_losses += 1

        realized = v7.payoff(
            sample, action, cost
        )

        output_rows.append({
            "symbol": sample.symbol,
            "timestamp_msc": sample.time,
            "date_utc": datetime.fromtimestamp(
                sample.time / 1000,
                tz=timezone.utc,
            ).date().isoformat(),
            "cost": cost,
            "risk_multiplier": risk,
            "predicted_buy": round(buy_prediction, 6),
            "predicted_sell": round(sell_prediction, 6),
            "adjusted_buy": round(
                buy_prediction
                - risk * float(errors[0])
                - cost, 6
            ),
            "adjusted_sell": round(
                sell_prediction
                - risk * float(errors[1])
                - cost, 6
            ),
            "action": action,
            "reason": reason,
            "actual_buy_net": round(actual_buy, 6),
            "actual_sell_net": round(actual_sell, 6),
            "realized_net": round(realized, 6),
            "hindsight_best_net": round(
                actual_best, 6
            ),
        })

    result = v7.evaluate(
        samples, actions, cost
    )

    result["cost"] = cost
    result["risk_multiplier"] = risk
    result["wait_reasons"] = dict(reasons)
    result["missed_profitable_waits"] = (
        missed_profitable
    )
    result["missed_hindsight_payoff_sum"] = (
        missed_best_payoff
    )
    result["waits_with_no_profitable_direction"] = (
        avoided_losses
    )

    return result, output_rows


def session_utc(timestamp: int) -> str:
    hour = datetime.fromtimestamp(
        timestamp / 1000,
        tz=timezone.utc,
    ).hour

    if hour < 7:
        return "ASIA"
    if hour < 13:
        return "LONDON"
    if hour < 21:
        return "NEW_YORK"
    return "ROLLOVER"


def main() -> None:
    print("PV_DECISION_DIAGNOSTICS=V8")
    print("DATA_SNAPSHOT_POLICY=FROZEN_PER_RUN")
    print("TRADING_ENABLED=NO")
    print("CHAMPION_CHANGED=NO")

    checkpoint_id, feature_names = (
        v7.checkpoint_schema()
    )

    OUTPUT.mkdir(
        parents=True, exist_ok=True
    )

    with tempfile.TemporaryDirectory(
        prefix=".pv_v8_",
        dir=OUTPUT,
        ignore_cleanup_errors=True,
    ) as temporary:
        folder = Path(temporary)

        feature_file, label_file, recorder_file = (
            v7.stable_copies(folder)
        )

        hashes = {
            "features": v7.file_hash(feature_file),
            "labels": v7.file_hash(label_file),
            "recorder": v7.file_hash(recorder_file),
        }

        samples, skipped = v7.prepare(
            feature_file,
            label_file,
            recorder_file,
            feature_names,
        )

        samples.sort(
            key=lambda row: (row.time, row.symbol)
        )

        print(f"CHECKPOINT_ID={checkpoint_id}")
        print(f"ALIGNED_SAMPLES={len(samples)}")
        print(f"SKIPPED={dict(skipped)}")

        if len(samples) < 150:
            print("STATUS=MORE_DATA_REQUIRED")
            return

        count = len(samples)
        cal_index = int(count * 0.55)
        test_index = int(count * 0.80)

        cal_start = samples[cal_index].time
        test_start = samples[test_index].time

        train = [
            sample
            for sample in samples[:cal_index]
            if sample.time + v7.PURGE_MS < cal_start
        ]

        calibration = [
            sample
            for sample in samples[cal_index:test_index]
            if sample.time + v7.PURGE_MS < test_start
        ]

        test = samples[test_index:]

        print(f"TRAIN_SAMPLES={len(train)}")
        print(
            f"CALIBRATION_SAMPLES={len(calibration)}"
        )
        print(f"TEST_SAMPLES={len(test)}")

        if (
            len(train) < 80
            or len(calibration) < 30
            or len(test) < 20
        ):
            print("STATUS=INSUFFICIENT_SPLIT_DATA")
            return

        model = RandomForestRegressor(
            n_estimators=200,
            max_depth=5,
            min_samples_leaf=8,
            random_state=42,
            n_jobs=1,
        )

        model.fit(
            v7.matrix(train),
            v7.targets(train),
        )

        calibration_predictions = np.asarray(
            model.predict(v7.matrix(calibration)),
            dtype=np.float64,
        )

        calibration_errors = np.abs(
            calibration_predictions
            - v7.targets(calibration)
        )

        mae = np.asarray(
            np.mean(calibration_errors, axis=0),
            dtype=np.float64,
        )

        test_predictions = np.asarray(
            model.predict(v7.matrix(test)),
            dtype=np.float64,
        )

        # Non-overlap is selected once, BEFORE
        # applying any cost or risk scenario.
        indices = v7.nonoverlap_indices(test)

        test_rows = [test[i] for i in indices]
        predicted = test_predictions[indices]

        if len(test_rows) < 10:
            print(
                "STATUS=MORE_NONOVERLAP_DATA_REQUIRED"
            )
            return

        # Predictions and samples are now fixed.
        # All scenarios use exactly the same rows.
        scenario_reports: list[dict[str, Any]] = []
        detail_rows: list[dict[str, Any]] = []

        for cost in COSTS:
            for risk in RISKS:
                result, details = evaluate_scenario(
                    test_rows,
                    predicted,
                    mae,
                    cost,
                    risk,
                )

                scenario_reports.append(result)
                detail_rows.extend(details)

        baseline_reports: list[dict[str, Any]] = []

        for cost in COSTS:
            for name, action in (
                ("ALWAYS_BUY", "BUY"),
                ("ALWAYS_SELL", "SELL"),
                ("ALWAYS_WAIT", "WAIT"),
            ):
                baseline_reports.append({
                    "strategy": name,
                    "cost": cost,
                    **v7.evaluate(
                        test_rows,
                        [action] * len(test_rows),
                        cost,
                    ),
                })

        # Diagnostic quality of the regression:
        actual = v7.targets(test_rows)
        absolute_errors = np.abs(
            predicted - actual
        )

        test_mae = np.mean(
            absolute_errors, axis=0
        )

        dates = sorted({
            datetime.fromtimestamp(
                sample.time / 1000,
                tz=timezone.utc,
            ).date().isoformat()
            for sample in test_rows
        })

        session_counts = dict(Counter(
            session_utc(sample.time)
            for sample in test_rows
        ))

        run_id = hashlib.sha256(
            json.dumps({
                "checkpoint_id": checkpoint_id,
                "hashes": hashes,
                "costs": COSTS,
                "risks": RISKS,
                "version": "V8",
            }, sort_keys=True).encode()
        ).hexdigest()[:16]

        destination = OUTPUT / run_id
        destination.mkdir(
            parents=True, exist_ok=True
        )

        report: dict[str, Any] = {
            "schema": "PV_DECISION_DIAGNOSTICS_V8",
            "checkpoint_id": checkpoint_id,
            "run_id": run_id,
            "created_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "source_sha256": hashes,
            "feature_dimensions": len(feature_names),
            "train_samples": len(train),
            "calibration_samples": len(calibration),
            "test_samples": len(test),
            "nonoverlap_test_samples": len(test_rows),
            "test_dates_utc": dates,
            "session_counts": session_counts,
            "calibration_mae": {
                "buy": float(mae[0]),
                "sell": float(mae[1]),
            },
            "test_mae": {
                "buy": float(test_mae[0]),
                "sell": float(test_mae[1]),
            },
            "scenarios": scenario_reports,
            "baselines": baseline_reports,
            "limitations": [
                "Previously inspected market period",
                "Non-overlap does not prove independence",
                "Short historical test window",
                "MAE is not a prediction interval",
                "All risk scenarios are diagnostics, not new validation tests",
                "Hindsight best payoff is an unattainable oracle",
                "No TP/SL, broker execution, or position sizing",
                "No live trading or model promotion",
            ],
            "trading_enabled": False,
            "model_promoted": False,
        }

        (destination / "report.json").write_text(
            json.dumps(report, indent=2),
            encoding="utf-8",
        )

        with (
            destination / "decision_diagnostics.csv"
        ).open(
            "w",
            newline="",
            encoding="utf-8",
        ) as handle:
            fields = list(detail_rows[0].keys())
            writer = csv.DictWriter(
                handle, fieldnames=fields
            )
            writer.writeheader()
            writer.writerows(detail_rows)

        print(
            f"CALIBRATION_BUY_MAE={mae[0]:.5f}"
        )
        print(
            f"CALIBRATION_SELL_MAE={mae[1]:.5f}"
        )
        print(f"TEST_BUY_MAE={test_mae[0]:.5f}")
        print(f"TEST_SELL_MAE={test_mae[1]:.5f}")
        print(
            f"NONOVERLAP_TEST_SAMPLES="
            f"{len(test_rows)}"
        )
        print(f"TEST_DATES_UTC={dates}")
        print(f"SESSION_COUNTS={session_counts}")

        print("\n=== FROZEN COST / RISK MATRIX ===")

        for item in scenario_reports:
            print(
                f"COST={item['cost']:.2f} "
                f"RISK={item['risk_multiplier']:.2f} "
                f"TRADES={item['trades']} "
                f"WAITS={item['waits']} "
                f"NET_PER_DECISION="
                f"{item['net_price_per_decision']:.5f} "
                f"MISSED_PROFITABLE_WAITS="
                f"{item['missed_profitable_waits']}"
            )

        print("\n=== BASELINES ===")

        for item in baseline_reports:
            print(
                f"{item['strategy']} "
                f"COST={item['cost']:.2f} "
                f"NET_PER_DECISION="
                f"{item['net_price_per_decision']:.5f}"
            )

        reference = next(
            item
            for item in scenario_reports
            if (
                item["cost"] == 0.0
                and item["risk_multiplier"] == 0.5
            )
        )

        print("\n=== V7-STYLE WAIT REASONS ===")
        print(
            f"WAIT_REASONS="
            f"{reference['wait_reasons']}"
        )

        print(
            f"REPORT={destination / 'report.json'}"
        )
        print(
            f"DETAILS="
            f"{destination / 'decision_diagnostics.csv'}"
        )
        print("PV_DECISION_DIAGNOSTICS_STATUS=PASS")
        print("MODEL_PROMOTED=NO")
        print("INDEPENDENT_EDGE_PROVEN=NO")
        print("TRADING_ENABLED=NO")


if __name__ == "__main__":
    main()
