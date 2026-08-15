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

if str(
    ROOT_DIR
) not in sys.path:

    sys.path.insert(
        0,
        str(
            ROOT_DIR
        ),
    )


attestation_module: Any = importlib.import_module(
    "04_Testing."
    "exness_demo_xauusd_context_"
    "attestation_operation"
)

trainer_module: Any = importlib.import_module(
    "02_AI.Models."
    "xauusd_hierarchical_model_v4_trainer"
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
                sort_keys=True,
            )
        )

        return 2

    try:

        result = (
            trainer_module
            .XAUUSDHierarchicalModelV4Trainer()
            .train(
                context=(
                    attestation.context
                ),
                training_contract_version=(
                    "XAUUSD_MTF_TRAINING_V3"
                ),
                random_state=42,
                max_iter=300,
                learning_rate=0.04,
                max_leaf_nodes=31,
                min_samples_leaf=50,
                l2_regularization=1.5,
                stage_a_class_balance_power=(
                    0.20
                ),
                stage_b_class_balance_power=(
                    0.20
                ),
            )
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_HIERARCHICAL_MODEL_V4_"
                        "TRAINING_FAILED"
                    ),
                    "error_type": (
                        type(
                            exc
                        ).__name__
                    ),
                    "error": str(
                        exc
                    ),
                    "live_authorized": False,
                },
                indent=2,
                sort_keys=True,
            )
        )

        return 2

    print(
        json.dumps(
            {
                "valid": True,
                "reason": (
                    "OK_XAUUSD_HIERARCHICAL_MODEL_V4_"
                    "TRAINED"
                ),
                "model_id": (
                    result.model_id
                ),
                "output_directory": str(
                    result.output_directory
                ),
                "stage_a_model_path": str(
                    result.stage_a_model_path
                ),
                "stage_a_scaler_path": str(
                    result.stage_a_scaler_path
                ),
                "stage_b_model_path": str(
                    result.stage_b_model_path
                ),
                "stage_b_scaler_path": str(
                    result.stage_b_scaler_path
                ),
                "manifest_path": str(
                    result.manifest_path
                ),
                "training_dataset_id": (
                    result.training_dataset_id
                ),
                "training_dataset_sha256": (
                    result.training_dataset_sha256
                ),
                "training_manifest_sha256": (
                    result.training_manifest_sha256
                ),
                "feature_count": (
                    result.feature_count
                ),
                "rows": {
                    "TRAIN": (
                        result.train_rows
                    ),
                    "VALIDATION": (
                        result.validation_rows
                    ),
                    "TEST": (
                        result.test_rows
                    ),
                },
                "tradeable_rows": {
                    "TRAIN": (
                        result.train_tradeable_rows
                    ),
                    "VALIDATION": (
                        result.validation_tradeable_rows
                    ),
                    "TEST": (
                        result.test_tradeable_rows
                    ),
                },
                "metrics": (
                    result.split_metrics
                ),
                "learning_scope_fingerprint": (
                    result.learning_scope_fingerprint
                ),
                "model_training_contract_fingerprint": (
                    result
                    .model_training_contract_fingerprint
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