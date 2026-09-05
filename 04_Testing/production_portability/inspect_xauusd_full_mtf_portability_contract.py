from __future__ import annotations

import importlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


ANALYSIS_VERSION = (
    "XAUUSD_FULL_MTF_PORTABILITY_CONTRACT_INSPECTION_V1"
)

BASE_AUDIT_MODULE = (
    "04_Testing."
    "analyze_xauusd_current_broker_m5_domain_shift"
)


EXPECTED_TOTAL_FEATURE_COUNT = 333

EXPECTED_DOMAIN_FEATURE_COUNT = 63

EXPECTED_TECHNICAL_FEATURE_COUNT_PER_TIMEFRAME = 43

TIMEFRAMES = (
    "M5",
    "M15",
    "M30",
    "H1",
    "H4",
    "D1",
)


base: Any = importlib.import_module(
    BASE_AUDIT_MODULE
)


def _require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise RuntimeError(
            reason
        )


def _safe_optional_int(
    value: Any,
) -> int | None:

    if value is None:
        return None

    try:
        return int(
            value
        )

    except (
        TypeError,
        ValueError,
    ):
        return None


def _ordered_subset(
    source: Sequence[str],
    membership: set[str],
) -> list[str]:

    return [
        value
        for value
        in source
        if value
        in membership
    ]


def _safe_source_snapshot_document(
    timeframe: str,
    document: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    dataset_id = str(
        document.get(
            "dataset_id",
            "",
        )
    )

    dataset_sha256 = str(
        document.get(
            "dataset_sha256",
            "",
        )
    )

    row_count = (
        _safe_optional_int(
            document.get(
                "row_count"
            )
        )
    )

    return {
        "timeframe": (
            timeframe
        ),
        "dataset_id": (
            dataset_id
        ),
        "dataset_sha256_present": bool(
            dataset_sha256
        ),
        "dataset_sha256_length": int(
            len(
                dataset_sha256
            )
        ),
        "row_count": (
            row_count
        ),
    }


def _availability_metadata(
    manifest: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    keys = (
        "feature_availability_rule",
        "feature_availability",
        "causality",
        "causal_contract",
    )

    result: dict[
        str,
        Any,
    ] = {}

    for key in keys:

        if key in manifest:

            value = (
                manifest[
                    key
                ]
            )

            if isinstance(
                value,
                (
                    str,
                    int,
                    float,
                    bool,
                    type(None),
                ),
            ):

                result[
                    key
                ] = (
                    value
                )

            elif isinstance(
                value,
                Mapping,
            ):

                safe_mapping: dict[
                    str,
                    Any,
                ] = {}

                for (
                    child_key,
                    child_value,
                ) in value.items():

                    if isinstance(
                        child_value,
                        (
                            str,
                            int,
                            float,
                            bool,
                            type(None),
                        ),
                    ):

                        safe_mapping[
                            str(
                                child_key
                            )
                        ] = (
                            child_value
                        )

                result[
                    key
                ] = (
                    safe_mapping
                )

    domain_contract = (
        manifest.get(
            "domain_feature_contract"
        )
    )

    if isinstance(
        domain_contract,
        Mapping,
    ):

        safe_domain: dict[
            str,
            Any,
        ] = {}

        for key in (
            "version",
            "feature_count",
            "feature_availability_rule",
            "causality_rule",
        ):

            if key in domain_contract:

                value = (
                    domain_contract[
                        key
                    ]
                )

                if isinstance(
                    value,
                    (
                        str,
                        int,
                        float,
                        bool,
                        type(None),
                    ),
                ):

                    safe_domain[
                        key
                    ] = (
                        value
                    )

        result[
            "domain_feature_contract"
        ] = (
            safe_domain
        )

    return (
        result
    )


def _candidate_alignment_metadata(
    features: Sequence[str],
) -> list[str]:

    tokens = (
        "age",
        "availability",
        "stale",
        "staleness",
        "lag",
        "delay",
        "elapsed",
        "seconds",
        "bars_since",
        "source_time",
        "bar_time",
        "feature_time",
    )

    return [
        feature
        for feature
        in features
        if any(
            token
            in
            feature.lower()
            for token
            in tokens
        )
    ]


def _feature_prefix_counts(
    feature_columns: Sequence[str],
) -> dict[str, int]:

    counts: Counter[str] = Counter()

    for feature in feature_columns:

        lowered = (
            feature.lower()
        )

        matched = False

        for timeframe in (
            TIMEFRAMES
        ):

            prefix = (
                timeframe.lower()
                +
                "_"
            )

            if lowered.startswith(
                prefix
            ):

                counts[
                    timeframe
                ] += 1

                matched = True

                break

        if not matched:

            counts[
                "NO_KNOWN_TIMEFRAME_PREFIX"
            ] += 1

    return {
        key: int(
            value
        )
        for (
            key,
            value,
        ) in sorted(
            counts.items()
        )
    }


def run_inspection(
) -> dict[str, Any]:

    trainer = (
        base
        .XAUUSDHierarchicalModelV4Trainer()
    )

    snapshot = (
        base
        .sweep_module
        ._discover_frozen_training_snapshot(
            trainer=trainer
        )
    )

    dataset_path = (
        base
        ._snapshot_dataset_path(
            snapshot
        )
    )

    manifest_path = (
        base
        ._snapshot_manifest_path(
            snapshot,
            dataset_path,
        )
    )

    base._validate_snapshot(
        snapshot,
        dataset_path,
        manifest_path,
    )

    manifest = (
        base
        ._load_manifest(
            manifest_path
        )
    )

    feature_columns_raw = (
        manifest.get(
            "feature_columns"
        )
    )

    if not isinstance(
        feature_columns_raw,
        list,
    ):

        raise RuntimeError(
            "FROZEN_FEATURE_COLUMNS_MISSING"
        )

    feature_columns = [
        str(
            value
        )
        for value
        in feature_columns_raw
    ]

    _require(
        len(
            feature_columns
        )
        ==
        EXPECTED_TOTAL_FEATURE_COUNT,
        (
            "FROZEN_FEATURE_COUNT_MISMATCH:"
            f"{len(feature_columns)}"
        ),
    )

    _require(
        len(
            set(
                feature_columns
            )
        )
        ==
        len(
            feature_columns
        ),
        "FROZEN_FEATURE_COLUMNS_NOT_UNIQUE",
    )

    base_feature_names = (
        base
        ._base_feature_names()
    )

    _require(
        len(
            base_feature_names
        )
        ==
        EXPECTED_TECHNICAL_FEATURE_COUNT_PER_TIMEFRAME,
        (
            "BASE_TECHNICAL_FEATURE_COUNT_MISMATCH:"
            f"{len(base_feature_names)}"
        ),
    )

    domain_contract = (
        manifest.get(
            "domain_feature_contract"
        )
    )

    if not isinstance(
        domain_contract,
        Mapping,
    ):

        raise RuntimeError(
            "DOMAIN_FEATURE_CONTRACT_MISSING"
        )

    domain_columns_raw = (
        domain_contract.get(
            "feature_columns"
        )
    )

    if not isinstance(
        domain_columns_raw,
        list,
    ):

        raise RuntimeError(
            "DOMAIN_FEATURE_COLUMNS_MISSING"
        )

    domain_features = [
        str(
            value
        )
        for value
        in domain_columns_raw
    ]

    _require(
        len(
            domain_features
        )
        ==
        EXPECTED_DOMAIN_FEATURE_COUNT,
        (
            "DOMAIN_FEATURE_COUNT_MISMATCH:"
            f"{len(domain_features)}"
        ),
    )

    broker_sensitive_features = [
        str(
            value
        )
        for value
        in base.BROKER_SENSITIVE_FEATURES
    ]

    feature_set = set(
        feature_columns
    )

    domain_set = set(
        domain_features
    )

    broker_sensitive_set = set(
        broker_sensitive_features
    )

    _require(
        domain_set.issubset(
            feature_set
        ),
        "DOMAIN_FEATURES_NOT_SUBSET_OF_FROZEN_FEATURES",
    )

    _require(
        broker_sensitive_set.issubset(
            feature_set
        ),
        "BROKER_SENSITIVE_FEATURES_NOT_SUBSET_OF_FROZEN_FEATURES",
    )

    technical_groups: dict[
        str,
        list[str],
    ] = {}

    missing_technical_by_timeframe: dict[
        str,
        list[str],
    ] = {}

    expected_technical_union: set[
        str
    ] = set()

    for timeframe in (
        TIMEFRAMES
    ):

        prefix = (
            timeframe.lower()
        )

        expected = {
            (
                prefix
                +
                "_"
                +
                feature
            )
            for feature
            in base_feature_names
        }

        expected_technical_union.update(
            expected
        )

        present = (
            expected
            &
            feature_set
        )

        missing = (
            expected
            -
            feature_set
        )

        technical_groups[
            timeframe
        ] = (
            _ordered_subset(
                feature_columns,
                present,
            )
        )

        missing_technical_by_timeframe[
            timeframe
        ] = sorted(
            missing
        )

    technical_present_union = (
        expected_technical_union
        &
        feature_set
    )

    overlap_technical_domain = sorted(
        technical_present_union
        &
        domain_set
    )

    overlap_technical_broker = sorted(
        technical_present_union
        &
        broker_sensitive_set
    )

    overlap_domain_broker = sorted(
        domain_set
        &
        broker_sensitive_set
    )

    _require(
        not overlap_technical_domain,
        (
            "TECHNICAL_DOMAIN_FEATURE_OVERLAP:"
            f"{overlap_technical_domain}"
        ),
    )

    _require(
        not overlap_technical_broker,
        (
            "TECHNICAL_BROKER_FEATURE_OVERLAP:"
            f"{overlap_technical_broker}"
        ),
    )

    _require(
        not overlap_domain_broker,
        (
            "DOMAIN_BROKER_FEATURE_OVERLAP:"
            f"{overlap_domain_broker}"
        ),
    )

    classified_set = (
        technical_present_union
        |
        domain_set
        |
        broker_sensitive_set
    )

    unclassified_set = (
        feature_set
        -
        classified_set
    )

    unclassified_features = (
        _ordered_subset(
            feature_columns,
            unclassified_set,
        )
    )

    alignment_metadata_candidates = (
        _candidate_alignment_metadata(
            unclassified_features
        )
    )

    source_snapshots_raw = (
        manifest.get(
            "source_historical_snapshots"
        )
    )

    if not isinstance(
        source_snapshots_raw,
        Mapping,
    ):

        raise RuntimeError(
            "SOURCE_HISTORICAL_SNAPSHOTS_MISSING"
        )

    source_snapshot_documents: list[
        dict[str, Any]
    ] = []

    missing_source_timeframes: list[
        str
    ] = []

    for timeframe in (
        TIMEFRAMES
    ):

        raw_document = (
            source_snapshots_raw.get(
                timeframe
            )
        )

        if not isinstance(
            raw_document,
            Mapping,
        ):

            missing_source_timeframes.append(
                timeframe
            )

            continue

        source_snapshot_documents.append(
            _safe_source_snapshot_document(
                timeframe,
                raw_document,
            )
        )

    technical_counts = {
        timeframe: int(
            len(
                technical_groups[
                    timeframe
                ]
            )
        )
        for timeframe
        in TIMEFRAMES
    }

    technical_missing_counts = {
        timeframe: int(
            len(
                missing_technical_by_timeframe[
                    timeframe
                ]
            )
        )
        for timeframe
        in TIMEFRAMES
    }

    all_expected_technical_present = all(
        count
        ==
        EXPECTED_TECHNICAL_FEATURE_COUNT_PER_TIMEFRAME
        for count
        in technical_counts.values()
    )

    if missing_source_timeframes:

        status = (
            "FULL_MTF_SOURCE_CONTRACT_INCOMPLETE"
        )

        reason = (
            "ONE_OR_MORE_EXPECTED_HISTORICAL_TIMEFRAME_"
            "SNAPSHOTS_ARE_MISSING"
        )

        next_action = (
            "RESOLVE_SOURCE_TIMEFRAME_CONTRACT_BEFORE_"
            "CURRENT_BROKER_FULL_MTF_AUDIT"
        )

    elif not all_expected_technical_present:

        status = (
            "FULL_MTF_TECHNICAL_CONTRACT_MISMATCH"
        )

        reason = (
            "FROZEN_FEATURE_LIST_DOES_NOT_CONTAIN_"
            "EXPECTED_43_FEATURE_TECHNICAL_SET_FOR_EVERY_TIMEFRAME"
        )

        next_action = (
            "TRACE_MISSING_TECHNICAL_FEATURES_BEFORE_"
            "CURRENT_BROKER_FULL_MTF_AUDIT"
        )

    elif unclassified_features:

        status = (
            "FULL_333_CONTRACT_HAS_UNCLASSIFIED_FEATURES"
        )

        reason = (
            "FROZEN_333_FEATURE_LIST_CONTAINS_FEATURES_OUTSIDE_"
            "KNOWN_TECHNICAL_DOMAIN_AND_BROKER_SENSITIVE_GROUPS"
        )

        next_action = (
            "TRACE_UNCLASSIFIED_FEATURE_PROVENANCE_"
            "BEFORE_CURRENT_BROKER_FULL_MTF_AUDIT"
        )

    else:

        status = (
            "FULL_333_PORTABILITY_CONTRACT_DECOMPOSED"
        )

        reason = (
            "ALL_FROZEN_FEATURES_ACCOUNTED_FOR_BY_"
            "TECHNICAL_DOMAIN_OR_BROKER_SENSITIVE_CONTRACTS"
        )

        next_action = (
            "RUN_CURRENT_BROKER_FULL_MTF_PLUS_DOMAIN_"
            "TRAIN_ONLY_PORTABILITY_AUDIT"
        )

    accounted_count = int(
        len(
            classified_set
        )
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_FULL_MTF_"
            "PORTABILITY_CONTRACT_INSPECTION"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "frozen_reference": {
            "dataset_id": (
                base.EXPECTED_DATASET_ID
            ),
            "dataset_sha256": (
                base.EXPECTED_DATASET_SHA256
            ),
            "training_manifest_sha256": (
                base.EXPECTED_TRAINING_MANIFEST_SHA256
            ),
            "training_contract": (
                base.EXPECTED_TRAINING_CONTRACT
            ),
            "identity": (
                base
                ._safe_frozen_identity(
                    manifest
                )
            ),
            "feature_count": int(
                len(
                    feature_columns
                )
            ),
        },
        "decision": {
            "status": (
                status
            ),
            "reason": (
                reason
            ),
            "full_333_feature_count": int(
                len(
                    feature_columns
                )
            ),
            "classified_feature_count": (
                accounted_count
            ),
            "unclassified_feature_count": int(
                len(
                    unclassified_features
                )
            ),
            "full_333_portability_audit_allowed": bool(
                status
                ==
                "FULL_333_PORTABILITY_CONTRACT_DECOMPOSED"
            ),
            "next_action": (
                next_action
            ),
        },
        "technical_contract": {
            "timeframes": list(
                TIMEFRAMES
            ),
            "base_feature_count_per_timeframe": int(
                len(
                    base_feature_names
                )
            ),
            "expected_technical_total": int(
                len(
                    TIMEFRAMES
                )
                *
                len(
                    base_feature_names
                )
            ),
            "present_technical_total": int(
                len(
                    technical_present_union
                )
            ),
            "present_counts_by_timeframe": (
                technical_counts
            ),
            "missing_counts_by_timeframe": (
                technical_missing_counts
            ),
            "missing_features_by_timeframe": (
                missing_technical_by_timeframe
            ),
            "features_by_timeframe": (
                technical_groups
            ),
        },
        "domain_contract": {
            "feature_count": int(
                len(
                    domain_features
                )
            ),
            "feature_columns": (
                domain_features
            ),
        },
        "broker_sensitive_contract": {
            "feature_count": int(
                len(
                    broker_sensitive_features
                )
            ),
            "feature_columns": (
                broker_sensitive_features
            ),
        },
        "unclassified_contract": {
            "feature_count": int(
                len(
                    unclassified_features
                )
            ),
            "feature_columns": (
                unclassified_features
            ),
            "alignment_metadata_candidates": (
                alignment_metadata_candidates
            ),
        },
        "prefix_diagnostics": {
            "all_frozen_feature_prefix_counts": (
                _feature_prefix_counts(
                    feature_columns
                )
            ),
        },
        "source_historical_contract": {
            "expected_timeframes": list(
                TIMEFRAMES
            ),
            "missing_timeframes": (
                missing_source_timeframes
            ),
            "snapshots": (
                source_snapshot_documents
            ),
        },
        "availability_metadata": (
            _availability_metadata(
                manifest
            )
        ),
        "scientific_policy": {
            "frozen_manifest_loaded": True,
            "frozen_training_rows_loaded": False,
            "validation_loaded": False,
            "validation_evaluated": False,
            "test_loaded": False,
            "test_evaluated": False,
            "labels_used": False,
            "model_loaded": False,
            "model_trained": False,
            "model_artifacts_written": False,
            "mt5_used": False,
            "current_broker_used": False,
            "orders_sent": False,
            "positions_modified": False,
            "risk_engine_modified": False,
            "sizing_modified": False,
            "execution_integration_modified": False,
            "live_authorized": False,
            "account_login_emitted": False,
            "account_holder_name_emitted": False,
            "account_scope_identifier_emitted": False,
            "filesystem_paths_emitted": False,
        },
        "next_decision_contract": {
            "if_fully_decomposed": (
                "RUN_CURRENT_BROKER_FULL_MTF_PLUS_DOMAIN_"
                "TRAIN_ONLY_PORTABILITY_AUDIT"
            ),
            "if_unclassified_features_found": (
                "TRACE_ONLY_UNCLASSIFIED_FEATURES_TO_"
                "TRAINING_MATRIX_BUILDER_PROVENANCE"
            ),
            "if_technical_contract_mismatch": (
                "STOP_AND_TRACE_FROZEN_MTF_FEATURE_CONSTRUCTION"
            ),
            "test_holdout_remains_untouched": True,
            "v3_contract_not_mutated": True,
        },
    }


def main() -> int:

    try:

        result = (
            run_inspection()
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_FULL_MTF_"
                        "PORTABILITY_CONTRACT_INSPECTION_FAILED"
                    ),
                    "analysis_version": (
                        ANALYSIS_VERSION
                    ),
                    "error_type": (
                        type(
                            exc
                        ).__name__
                    ),
                    "error": (
                        str(
                            exc
                        )
                    ),
                    "validation_loaded": False,
                    "test_loaded": False,
                    "test_evaluated": False,
                    "mt5_used": False,
                    "model_trained": False,
                    "model_artifacts_written": False,
                    "orders_sent": False,
                    "positions_modified": False,
                    "risk_engine_modified": False,
                    "live_authorized": False,
                },
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
        )

        return 2

    print(
        json.dumps(
            result,
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