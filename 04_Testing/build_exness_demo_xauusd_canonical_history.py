"""Build canonical instrument-isolated XAUUSD historical datasets from Exness DEMO.

Flow:
1. Attest active Exness DEMO account and exact Gold contract.
2. Obtain verified InstrumentContext.
3. Fetch selected historical timeframes.
4. Reject broker-symbol drift.
5. Validate/stamp every row with instrument identity.
6. Persist immutable canonical CSV + lineage manifest.

No order submission, no live authorization.
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


attestation_module: Any = importlib.import_module(
    "04_Testing."
    "exness_demo_xauusd_context_"
    "attestation_operation"
)

history_module: Any = importlib.import_module(
    "02_AI.Dataset.history_manager"
)


HistoryManager: Any = (
    history_module.HistoryManager
)


def parse_timeframes(
    raw: str,
) -> tuple[str, ...]:

    supported = set(
        HistoryManager.TIMEFRAMES.keys()
    )

    result: list[str] = []

    seen: set[str] = set()

    for value in str(
        raw
    ).split(
        ","
    ):

        timeframe = (
            value
            .strip()
            .upper()
        )

        if not timeframe:

            continue

        if timeframe not in supported:

            raise ValueError(
                (
                    "Unsupported timeframe: "
                    f"{timeframe}. Supported: "
                    +
                    ", ".join(
                        HistoryManager
                        .TIMEFRAMES
                        .keys()
                    )
                )
            )

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
            "At least one timeframe is required"
        )

    return tuple(
        result
    )


def materialization_document(
    result: Any,
) -> dict[str, Any]:

    return {
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
        "timeframe": (
            result.timeframe
        ),
        "canonical_symbol": (
            result.canonical_symbol
        ),
        "broker_symbol": (
            result.broker_symbol
        ),
        "context_identity_fingerprint": (
            result.context_identity_fingerprint
        ),
        "reused_existing_dataset": (
            result.reused_existing_dataset
        ),
        "reused_existing_manifest": (
            result.reused_existing_manifest
        ),
        "live_authorized": False,
    }


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Build canonical Exness DEMO "
            "XAUUSD historical datasets."
        )
    )

    parser.add_argument(
        "--symbol",
        default="XAUUSDm",
    )

    parser.add_argument(
        "--bars",
        type=int,
        default=100000,
    )

    parser.add_argument(
        "--timeframes",
        default=(
            "M1,M5,M15,M30,H1,H4,D1"
        ),
    )

    parser.add_argument(
        "--account-scope-id",
        default="PRIMARY_DEMO",
    )

    parser.add_argument(
        "--resolver-attempts",
        type=int,
        default=3,
    )

    parser.add_argument(
        "--data-schema-version",
        default="MARKET_V1",
    )

    parser.add_argument(
        "--feature-contract-version",
        default="FEATURES_V1",
    )

    args = parser.parse_args()

    if (
        isinstance(
            args.bars,
            bool,
        )
        or
        args.bars
        <=
        0
    ):

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "INVALID_BAR_COUNT"
                    ),
                    "live_authorized": False,
                },
                indent=2,
            )
        )

        return 2

    try:

        timeframes = (
            parse_timeframes(
                args.timeframes
            )
        )

    except ValueError as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "INVALID_TIMEFRAME_SELECTION"
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
    # Step 1: broker/account/contract attestation
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
                args.data_schema_version
            ),
            feature_contract_version=(
                args.feature_contract_version
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
            "CANONICAL_HISTORY_BUILD"
        )

        document[
            "history_build_started"
        ] = False

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
                    "history_build_started": False,
                    "live_authorized": False,
                },
                indent=2,
            )
        )

        return 2

    # ========================================================================
    # Step 2: canonical materialization
    # ========================================================================

    manager = (
        HistoryManager()
    )

    try:

        results = (
            manager.build_dataset(
                context=context,
                bars=(
                    args.bars
                ),
                timeframes=(
                    timeframes
                ),
            )
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "CANONICAL_HISTORY_BUILD_FAILED"
                    ),
                    "error_type": (
                        type(
                            exc
                        ).__name__
                    ),
                    "error": str(
                        exc
                    ),
                    "requested_bars": (
                        args.bars
                    ),
                    "timeframes": list(
                        timeframes
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

    # ========================================================================
    # Step 3: final build summary
    # ========================================================================

    output = {
        "valid": True,
        "reason": (
            "OK_CANONICAL_XAUUSD_HISTORY_BUILT"
        ),
        "action": (
            "USE_CANONICAL_HISTORY_FOR_RESEARCH_AND_TRAINING"
        ),
        "live_authorized": False,
        "canonical_symbol": (
            context.canonical_symbol
        ),
        "asset_class": (
            context.asset_class
        ),
        "broker_id": (
            context.broker_id
        ),
        "broker_symbol": (
            context.broker_symbol
        ),
        "execution_environment": (
            context.execution_environment
        ),
        "account_scope_id": (
            context.account_scope_id
        ),
        "contract_spec_id": (
            context.contract_spec_id
        ),
        "data_schema_version": (
            context.data_schema_version
        ),
        "feature_contract_version": (
            context.feature_contract_version
        ),
        "context_identity_fingerprint": (
            context.identity_fingerprint
        ),
        "requested_bars_per_timeframe": (
            args.bars
        ),
        "timeframes": list(
            timeframes
        ),
        "dataset_count": len(
            results
        ),
        "datasets": [
            materialization_document(
                item
            )
            for item
            in results
        ],
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