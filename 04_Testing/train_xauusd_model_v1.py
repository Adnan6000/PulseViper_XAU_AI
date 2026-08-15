"""Train XAUUSD_MODEL_v1 from the canonical PulseViper training matrix."""

from __future__ import annotations

import argparse
import importlib
import json
import sys

from pathlib import Path
from typing import Any


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(
    PROJECT_ROOT
) not in sys.path:

    sys.path.insert(
        0,
        str(
            PROJECT_ROOT
        ),
    )


attestation_module: Any = (
    importlib.import_module(
        "04_Testing."
        "exness_demo_xauusd_context_"
        "attestation_operation"
    )
)

trainer_module: Any = (
    importlib.import_module(
        "02_AI.Models."
        "xauusd_model_trainer"
    )
)


XAUUSDModelTrainer: Any = (
    trainer_module.XAUUSDModelTrainer
)


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Train PulseViper XAUUSD_MODEL_v1."
        )
    )

    parser.add_argument(
        "--symbol",
        default="XAUUSDm",
    )

    parser.add_argument(
        "--account-scope-id",
        default="PRIMARY_DEMO",
    )

    parser.add_argument(
        "--training-contract",
        default=(
            "XAUUSD_MTF_TRAINING_V1"
        ),
    )

    parser.add_argument(
        "--max-iter",
        type=int,
        default=250,
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.05,
    )

    parser.add_argument(
        "--max-leaf-nodes",
        type=int,
        default=31,
    )

    parser.add_argument(
        "--min-samples-leaf",
        type=int,
        default=40,
    )

    parser.add_argument(
        "--l2",
        type=float,
        default=1.0,
    )

    parser.add_argument(
        "--class-balance-power",
        type=float,
        default=0.50,
    )

    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--resolver-attempts",
        type=int,
        default=3,
    )

    args = parser.parse_args()

    # ========================================================================
    # Re-attest exact current XAUUSD broker contract.
    # ========================================================================

    attestation = (
        attestation_module
        .run_attestation(
            requested_symbol=(
                args.symbol
            ),
            probe_bars=32,
            broker_id="EXNESS",
            account_scope_id=(
                args.account_scope_id
            ),
            data_schema_version=(
                "MARKET_V1"
            ),
            feature_contract_version=(
                "FEATURES_V1"
            ),
            resolver_attempts=(
                args.resolver_attempts
            ),
        )
    )

    if not bool(
        attestation.valid
    ):

        document = (
            attestation.to_document()
        )

        document[
            "operation"
        ] = (
            "TRAIN_XAUUSD_MODEL_V1"
        )

        print(
            json.dumps(
                document,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            )
        )

        return 2

    context = (
        attestation.context
    )

    if (
        context is None
        or
        bool(
            context.live_authorized
        )
    ):

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "INVALID_ATTESTED_CONTEXT"
                    ),
                    "live_authorized": False,
                },
                indent=2,
            )
        )

        return 2

    # ========================================================================
    # Actual model training.
    # ========================================================================

    try:

        result = (
            XAUUSDModelTrainer()
            .train(
                context=context,
                training_contract_version=(
                    args.training_contract
                ),
                random_state=(
                    args.random_state
                ),
                max_iter=(
                    args.max_iter
                ),
                learning_rate=(
                    args.learning_rate
                ),
                max_leaf_nodes=(
                    args.max_leaf_nodes
                ),
                min_samples_leaf=(
                    args.min_samples_leaf
                ),
                l2_regularization=(
                    args.l2
                ),
                class_balance_power=(
                    args.class_balance_power
                ),
            )
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_MODEL_V1_TRAINING_FAILED"
                    ),
                    "error_type": (
                        type(
                            exc
                        ).__name__
                    ),
                    "error": str(
                        exc
                    ),
                    "canonical_symbol": (
                        context.canonical_symbol
                    ),
                    "broker_symbol": (
                        context.broker_symbol
                    ),
                    "contract_spec_id": (
                        context.contract_spec_id
                    ),
                    "live_authorized": False,
                },
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            )
        )

        return 2

    output = {
        "valid": True,
        "reason": (
            "OK_XAUUSD_MODEL_V1_TRAINED"
        ),
        "action": (
            "MODEL_READY_FOR_OFFLINE_EVALUATION_AND_SHADOW_INFERENCE"
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
        "model_sha256": (
            result.model_sha256
        ),
        "scaler_sha256": (
            result.scaler_sha256
        ),
        "manifest_sha256": (
            result.manifest_sha256
        ),
        "training_dataset_id": (
            result.training_dataset_id
        ),
        "training_dataset_sha256": (
            result.training_dataset_sha256
        ),
        "feature_count": (
            result.feature_count
        ),
        "split_rows": {
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
        "validation_metrics": (
            result.validation_metrics
        ),
        "test_metrics": (
            result.test_metrics
        ),
        "learning_scope_fingerprint": (
            result.learning_scope_fingerprint
        ),
        "model_training_contract_fingerprint": (
            result.model_training_contract_fingerprint
        ),
        "canonical_symbol": (
            context.canonical_symbol
        ),
        "broker_symbol": (
            context.broker_symbol
        ),
        "contract_spec_id": (
            context.contract_spec_id
        ),
        "live_authorized": False,
    }

    print(
        json.dumps(
            output,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
    )

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )