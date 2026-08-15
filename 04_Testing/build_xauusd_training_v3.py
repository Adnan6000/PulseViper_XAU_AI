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

enricher_module: Any = importlib.import_module(
    "02_AI.Dataset."
    "training_feature_enricher"
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
            enricher_module
            .TrainingFeatureEnricher()
            .enrich(
                context=(
                    attestation.context
                )
            )
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_TRAINING_V3_BUILD_FAILED"
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
                    "OK_XAUUSD_MTF_TRAINING_V3_BUILT"
                ),
                "dataset_id": (
                    result.dataset_id
                ),
                "dataset_path": str(
                    result.dataset_path
                ),
                "manifest_path": str(
                    result.manifest_path
                ),
                "row_count": (
                    result.row_count
                ),
                "feature_count": (
                    result.feature_count
                ),
                "added_feature_count": (
                    result.added_feature_count
                ),
                "class_distribution": (
                    result.class_distribution
                ),
                "training_contract_version": (
                    result.training_contract_version
                ),
                "live_authorized": False,
            },
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )