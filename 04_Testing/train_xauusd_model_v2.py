from __future__ import annotations

import importlib
import json
import sys

from pathlib import Path
from typing import Any


ROOT_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(ROOT_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


attestation_module: Any = importlib.import_module(
    "04_Testing."
    "exness_demo_xauusd_context_"
    "attestation_operation"
)

trainer_module: Any = importlib.import_module(
    "02_AI.Models."
    "xauusd_model_v2_trainer"
)


def main() -> int:

    attestation = (
        attestation_module
        .run_attestation(
            requested_symbol="XAUUSDm",
            probe_bars=32,
            broker_id="EXNESS",
            account_scope_id=(
                "PRIMARY_DEMO"
            ),
            data_schema_version=(
                "MARKET_V1"
            ),
            feature_contract_version=(
                "FEATURES_V1"
            ),
            resolver_attempts=3,
        )
    )

    if not attestation.valid:

        print(
            json.dumps(
                attestation.to_document(),
                indent=2,
            )
        )

        return 2

    try:

        result = (
            trainer_module
            .XAUUSDModelV2Trainer()
            .train(
                context=(
                    attestation.context
                ),
                training_contract_version=(
                    "XAUUSD_MTF_TRAINING_V2"
                ),
                random_state=42,
                max_iter=250,
                learning_rate=0.05,
                max_leaf_nodes=31,
                min_samples_leaf=40,
                l2_regularization=1.0,

                # V2 classes are already much healthier.
                # Only very mild balancing is needed.
                class_balance_power=0.25,
            )
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_MODEL_V2_TRAINING_FAILED"
                    ),
                    "error_type": (
                        type(exc).__name__
                    ),
                    "error": str(exc),
                    "live_authorized": False,
                },
                indent=2,
            )
        )

        return 2

    print(
        json.dumps(
            {
                "valid": True,
                "reason": (
                    "OK_XAUUSD_MODEL_V2_TRAINED"
                ),
                "model_id": (
                    result.model_id
                ),
                "model_path": str(
                    result.model_path
                ),
                "scaler_path": str(
                    result.scaler_path
                ),
                "manifest_path": str(
                    result.manifest_path
                ),
                "feature_count": (
                    result.feature_count
                ),
                "validation_metrics": (
                    result.validation_metrics
                ),
                "test_metrics": (
                    result.test_metrics
                ),
                "live_authorized": False,
            },
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    )

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )