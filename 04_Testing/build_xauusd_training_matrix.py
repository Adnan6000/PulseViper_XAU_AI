"""Build the first causal multi-timeframe XAUUSD training matrix.

This operation:
- attests the current Exness DEMO XAUUSD context
- uses already materialized canonical historical datasets
- performs no historical downloading
- performs no trading
- produces LONG / SHORT / NO_TRADE supervised training data
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys

from pathlib import Path
from typing import Any


PROJECT_ROOT = (
    Path(
        __file__
    )
    .resolve()
    .parents[
        1
    ]
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

builder_module: Any = (
    importlib.import_module(
        "02_AI.Dataset."
        "training_matrix_builder"
    )
)


TrainingMatrixBuilder: Any = (
    builder_module.TrainingMatrixBuilder
)


def parse_timeframes(
    value: str,
) -> tuple[
    str,
    ...
]:

    result: list[
        str
    ] = []

    seen: set[
        str
    ] = set()

    for raw in str(
        value
    ).split(
        ","
    ):

        timeframe = raw.strip().upper()

        if not timeframe:
            continue

        if timeframe in seen:
            continue

        result.append(
            timeframe
        )

        seen.add(
            timeframe
        )

    if not result:

        raise ValueError(
            "No context timeframes supplied"
        )

    return tuple(
        result
    )


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Build PulseViper causal "
            "multi-timeframe XAUUSD training matrix."
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
        "--base-timeframe",
        default="M5",
    )

    parser.add_argument(
        "--context-timeframes",
        default="M15,M30,H1,H4,D1",
    )

    parser.add_argument(
        "--horizon-bars",
        type=int,
        default=12,
        help=(
            "Future base-timeframe bars used "
            "only for target generation."
        ),
    )

    parser.add_argument(
        "--barrier-atr",
        type=float,
        default=1.0,
        help=(
            "Symmetric target barrier in ATR units."
        ),
    )

    parser.add_argument(
        "--train-fraction",
        type=float,
        default=0.70,
    )

    parser.add_argument(
        "--validation-fraction",
        type=float,
        default=0.15,
    )

    parser.add_argument(
        "--resolver-attempts",
        type=int,
        default=3,
    )

    args = parser.parse_args()

    try:

        context_timeframes = (
            parse_timeframes(
                args.context_timeframes
            )
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "INVALID_CONTEXT_TIMEFRAMES"
                    ),
                    "error": str(
                        exc
                    ),
                    "live_authorized": False,
                },
                indent=2,
            )
        )

        return 2

    # ========================================================================
    # Verify current broker/account/contract identity
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
            "BUILD_XAUUSD_TRAINING_MATRIX"
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
    # Build training matrix
    # ========================================================================

    try:

        result = (
            TrainingMatrixBuilder()
            .build(
                context=context,
                base_timeframe=(
                    args.base_timeframe
                ),
                context_timeframes=(
                    context_timeframes
                ),
                horizon_bars=(
                    args.horizon_bars
                ),
                barrier_atr=(
                    args.barrier_atr
                ),
                train_fraction=(
                    args.train_fraction
                ),
                validation_fraction=(
                    args.validation_fraction
                ),
            )
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "TRAINING_MATRIX_BUILD_FAILED"
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
                    "context_identity_fingerprint": (
                        context.identity_fingerprint
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
            "OK_XAUUSD_TRAINING_MATRIX_BUILT"
        ),
        "action": (
            "READY_FOR_MODEL_TRAINING_PIPELINE"
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
        "dataset_sha256": (
            result.dataset_sha256
        ),
        "manifest_sha256": (
            result.manifest_sha256
        ),
        "row_count": (
            result.row_count
        ),
        "feature_count": (
            result.feature_count
        ),
        "base_timeframe": (
            result.base_timeframe
        ),
        "class_distribution": (
            result.class_distribution
        ),
        "split_distribution": (
            result.split_distribution
        ),
        "learning_scope_fingerprint": (
            result.learning_scope_fingerprint
        ),
        "training_contract_version": (
            result.training_contract_version
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
        "reused_existing_dataset": (
            result.reused_existing_dataset
        ),
        "reused_existing_manifest": (
            result.reused_existing_manifest
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