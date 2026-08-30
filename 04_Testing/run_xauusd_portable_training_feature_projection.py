from __future__ import annotations

import importlib
import json
import os
import sys

from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_TRAINING_FEATURE_PROJECTION_INTEGRATION_V1"
)

PROJECTOR_MODULE = (
    "02_AI.Dataset.portable_training_feature_projector"
)


projector_module: Any = importlib.import_module(
    PROJECTOR_MODULE
)


PortableTrainingFeatureProjector = (
    projector_module
    .PortableTrainingFeatureProjector
)

PortableTrainingFeatureProjectionError = (
    projector_module
    .PortableTrainingFeatureProjectionError
)


EXPECTED_SOURCE_CONTRACT = (
    "XAUUSD_MTF_TRAINING_V3"
)

EXPECTED_OUTPUT_CONTRACT = (
    "XAUUSD_MTF_PORTABLE_FEATURE_V1"
)

EXPECTED_SOURCE_FEATURE_COUNT = 333

EXPECTED_OUTPUT_FEATURE_COUNT = 331

EXPECTED_TOTAL_ROWS = 99945


EXPECTED_SPLIT_ROWS = {
    "TRAIN": 69966,
    "VALIDATION": 14983,
    "TEST": 14996,
}


EXPECTED_DROPPED_FEATURES = (
    "m5_spread_points",
    "m5_tick_volume_log1p",
)

EXPECTED_RETAINED_FEATURE = (
    "m5_tick_volume_ratio20"
)


EXPECTED_SOURCE_DATASET_ID = (
    "train_66ff363d25d8143d4e2c3410"
)

EXPECTED_SOURCE_DATASET_SHA256 = (
    "66ff363d25d8143d4e2c3410964ad26b5bd72f2e98806c3e0997ce420d18413d"
)

EXPECTED_SOURCE_MANIFEST_SHA256 = (
    "a205403a6cb5a2d1b17159a2296d1f4afb01ea5b9b90b2710feafa7dd9476aa3"
)


EXPECTED_CONTRACT_DESIGN_FINGERPRINT = (
    "de389b1daa02b2d864490aa41776494baea4f9e42dbf2146c2c44b9c2660ff40"
)


PRESERVED_PARENT_FIELDS = (
    "dataset_kind",
    "target_columns",
    "target_classes",
    "target_class_mapping",
    "target_label_contract",
    "base_timeframe",
    "context_timeframes",
    "target_horizon_bars",
    "train_fraction",
    "validation_fraction",
    "test_fraction",
    "split_purge_bars",
    "class_distribution",
    "split_class_distribution",
    "learning_scope",
    "learning_scope_fingerprint",
    "source_execution_context_fingerprint",
    "source_historical_snapshots",
    "domain_feature_contract",
    "causality_rule",
    "feature_availability_rule",
    "target_future_data_rule",
)


EXCLUDED_SCAN_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
}


def _require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise RuntimeError(
            reason
        )


def _mapping(
    document: Mapping[
        str,
        Any,
    ],
    key: str,
) -> Mapping[
    str,
    Any,
]:

    value = document.get(
        key
    )

    if not isinstance(
        value,
        Mapping,
    ):
        raise RuntimeError(
            (
                "EXPECTED_MAPPING_MISSING:"
                f"{key}"
            )
        )

    return value


def _string_list(
    value: Any,
    *,
    field_name: str,
) -> list[str]:

    if not isinstance(
        value,
        list,
    ):
        raise RuntimeError(
            (
                "EXPECTED_LIST_MISSING:"
                f"{field_name}"
            )
        )

    return [
        str(
            item
        )
        for item
        in value
    ]


def _candidate_search_roots(
) -> list[Path]:

    preferred = (
        ROOT_DIR
        /
        "03_Data"
    )

    if preferred.is_dir():

        return [
            preferred
        ]

    return [
        ROOT_DIR
    ]


def _manifest_files(
    root: Path,
):

    for (
        current_root,
        directory_names,
        file_names,
    ) in os.walk(
        root
    ):

        directory_names[:] = [
            name
            for name
            in directory_names
            if (
                name
                not in
                EXCLUDED_SCAN_DIRECTORIES
            )
        ]

        for file_name in file_names:

            if not file_name.endswith(
                ".manifest.json"
            ):
                continue

            yield (
                Path(
                    current_root
                )
                /
                file_name
            )


def _discover_exact_frozen_v3(
) -> tuple[
    Path,
    Path,
    dict[str, Any],
]:

    candidates: list[
        tuple[
            Path,
            Path,
            dict[str, Any],
        ]
    ] = []

    seen_manifest_paths: set[
        Path
    ] = set()

    for search_root in (
        _candidate_search_roots()
    ):

        for manifest_path in (
            _manifest_files(
                search_root
            )
        ):

            resolved_manifest_path = (
                manifest_path.resolve()
            )

            if (
                resolved_manifest_path
                in
                seen_manifest_paths
            ):
                continue

            seen_manifest_paths.add(
                resolved_manifest_path
            )

            try:

                manifest_sha256 = (
                    PortableTrainingFeatureProjector
                    ._sha256_file(
                        manifest_path
                    )
                )

            except OSError:
                continue

            if (
                manifest_sha256
                !=
                EXPECTED_SOURCE_MANIFEST_SHA256
            ):
                continue

            try:

                manifest = (
                    PortableTrainingFeatureProjector
                    ._load_json(
                        manifest_path
                    )
                )

            except Exception:
                continue

            if (
                str(
                    manifest.get(
                        "dataset_id",
                        "",
                    )
                )
                !=
                EXPECTED_SOURCE_DATASET_ID
            ):
                continue

            if (
                str(
                    manifest.get(
                        "dataset_sha256",
                        "",
                    )
                )
                !=
                EXPECTED_SOURCE_DATASET_SHA256
            ):
                continue

            if (
                str(
                    manifest.get(
                        "training_contract_version",
                        "",
                    )
                )
                !=
                EXPECTED_SOURCE_CONTRACT
            ):
                continue

            dataset_filename = str(
                manifest.get(
                    "dataset_filename",
                    "",
                )
            ).strip()

            if not dataset_filename:
                continue

            dataset_path = (
                manifest_path.parent
                /
                dataset_filename
            )

            if not dataset_path.is_file():
                continue

            try:

                dataset_sha256 = (
                    PortableTrainingFeatureProjector
                    ._sha256_file(
                        dataset_path
                    )
                )

            except OSError:
                continue

            if (
                dataset_sha256
                !=
                EXPECTED_SOURCE_DATASET_SHA256
            ):
                continue

            candidates.append(
                (
                    dataset_path,
                    manifest_path,
                    manifest,
                )
            )

    _require(
        len(
            candidates
        )
        ==
        1,
        (
            "EXACT_FROZEN_V3_SOURCE_DISCOVERY_COUNT_INVALID:"
            f"{len(candidates)}"
        ),
    )

    return candidates[
        0
    ]


def _validate_source_manifest(
    source_manifest: Mapping[
        str,
        Any,
    ],
) -> tuple[
    list[str],
    list[str],
]:

    _require(
        str(
            source_manifest.get(
                "dataset_id",
                "",
            )
        )
        ==
        EXPECTED_SOURCE_DATASET_ID,
        "SOURCE_DATASET_ID_MISMATCH",
    )

    _require(
        str(
            source_manifest.get(
                "dataset_sha256",
                "",
            )
        )
        ==
        EXPECTED_SOURCE_DATASET_SHA256,
        "SOURCE_DATASET_SHA256_MISMATCH",
    )

    _require(
        str(
            source_manifest.get(
                "training_contract_version",
                "",
            )
        )
        ==
        EXPECTED_SOURCE_CONTRACT,
        "SOURCE_CONTRACT_MISMATCH",
    )

    _require(
        int(
            source_manifest.get(
                "feature_count",
                -1,
            )
        )
        ==
        EXPECTED_SOURCE_FEATURE_COUNT,
        "SOURCE_FEATURE_COUNT_MISMATCH",
    )

    _require(
        int(
            source_manifest.get(
                "row_count",
                -1,
            )
        )
        ==
        EXPECTED_TOTAL_ROWS,
        "SOURCE_ROW_COUNT_MISMATCH",
    )

    _require(
        not bool(
            source_manifest.get(
                "live_authorized",
                False,
            )
        ),
        "SOURCE_UNEXPECTEDLY_LIVE_AUTHORIZED",
    )

    feature_columns = (
        _string_list(
            source_manifest.get(
                "feature_columns"
            ),
            field_name=(
                "feature_columns"
            ),
        )
    )

    target_columns = (
        _string_list(
            source_manifest.get(
                "target_columns"
            ),
            field_name=(
                "target_columns"
            ),
        )
    )

    _require(
        len(
            feature_columns
        )
        ==
        EXPECTED_SOURCE_FEATURE_COUNT,
        "SOURCE_FEATURE_LIST_COUNT_MISMATCH",
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
        "SOURCE_FEATURE_COLUMNS_NOT_UNIQUE",
    )

    for feature in (
        EXPECTED_DROPPED_FEATURES
    ):

        _require(
            feature
            in
            feature_columns,
            (
                "EXPECTED_DROP_FEATURE_MISSING:"
                f"{feature}"
            ),
        )

    _require(
        EXPECTED_RETAINED_FEATURE
        in
        feature_columns,
        "EXPECTED_RETAINED_FEATURE_MISSING",
    )

    return (
        feature_columns,
        target_columns,
    )


def _validate_headers(
    *,
    source_dataset_path: Path,
    output_dataset_path: Path,
    source_feature_columns: Sequence[
        str
    ],
) -> dict[str, Any]:

    source_header = pd.read_csv(
        source_dataset_path,
        nrows=0,
    )

    output_header = pd.read_csv(
        output_dataset_path,
        nrows=0,
    )

    source_columns = [
        str(
            column
        )
        for column
        in source_header.columns
    ]

    output_columns = [
        str(
            column
        )
        for column
        in output_header.columns
    ]

    expected_output_columns = [
        column
        for column
        in source_columns
        if (
            column
            not in
            set(
                EXPECTED_DROPPED_FEATURES
            )
        )
    ]

    _require(
        output_columns
        ==
        expected_output_columns,
        "OUTPUT_DATASET_COLUMN_ORDER_OR_CONTENT_MISMATCH",
    )

    expected_portable_features = [
        str(
            feature
        )
        for feature
        in source_feature_columns
        if (
            str(
                feature
            )
            not in
            set(
                EXPECTED_DROPPED_FEATURES
            )
        )
    ]

    output_feature_columns = [
        feature
        for feature
        in expected_portable_features
        if (
            feature
            in
            output_columns
        )
    ]

    _require(
        output_feature_columns
        ==
        expected_portable_features,
        "OUTPUT_FEATURE_ORDER_MISMATCH",
    )

    _require(
        len(
            output_feature_columns
        )
        ==
        EXPECTED_OUTPUT_FEATURE_COUNT,
        "OUTPUT_FEATURE_HEADER_COUNT_MISMATCH",
    )

    for feature in (
        EXPECTED_DROPPED_FEATURES
    ):

        _require(
            feature
            not in
            output_columns,
            (
                "DROPPED_FEATURE_PRESENT_IN_OUTPUT:"
                f"{feature}"
            ),
        )

    _require(
        EXPECTED_RETAINED_FEATURE
        in
        output_columns,
        "RETAINED_FEATURE_MISSING_FROM_OUTPUT",
    )

    return {
        "source_total_column_count": int(
            len(
                source_columns
            )
        ),
        "output_total_column_count": int(
            len(
                output_columns
            )
        ),
        "source_feature_count": (
            EXPECTED_SOURCE_FEATURE_COUNT
        ),
        "output_feature_count": (
            EXPECTED_OUTPUT_FEATURE_COUNT
        ),
        "column_order_preserved": (
            True
        ),
        "dropped_features_absent": (
            True
        ),
        "retained_relative_volume_feature_present": (
            True
        ),
    }


def _validate_structural_rows(
    *,
    source_dataset_path: Path,
    output_dataset_path: Path,
) -> dict[str, Any]:

    columns = [
        "decision_time",
        "dataset_split",
    ]

    source = pd.read_csv(
        source_dataset_path,
        usecols=(
            columns
        ),
    )

    output = pd.read_csv(
        output_dataset_path,
        usecols=(
            columns
        ),
    )

    _require(
        len(
            source
        )
        ==
        EXPECTED_TOTAL_ROWS,
        (
            "SOURCE_STRUCTURAL_ROW_COUNT_MISMATCH:"
            f"{len(source)}"
        ),
    )

    _require(
        len(
            output
        )
        ==
        EXPECTED_TOTAL_ROWS,
        (
            "OUTPUT_STRUCTURAL_ROW_COUNT_MISMATCH:"
            f"{len(output)}"
        ),
    )

    _require(
        source[
            "decision_time"
        ].equals(
            output[
                "decision_time"
            ]
        ),
        "DECISION_TIME_SEQUENCE_CHANGED",
    )

    _require(
        source[
            "dataset_split"
        ].equals(
            output[
                "dataset_split"
            ]
        ),
        "DATASET_SPLIT_SEQUENCE_CHANGED",
    )

    _require(
        not bool(
            output[
                "decision_time"
            ]
            .duplicated()
            .any()
        ),
        "OUTPUT_DUPLICATE_DECISION_TIME",
    )

    observed_split_rows = {
        str(
            key
        ): int(
            value
        )
        for (
            key,
            value,
        )
        in (
            output[
                "dataset_split"
            ]
            .value_counts()
            .to_dict()
            .items()
        )
    }

    _require(
        observed_split_rows
        ==
        EXPECTED_SPLIT_ROWS,
        (
            "OUTPUT_SPLIT_ROW_COUNTS_MISMATCH:"
            f"{observed_split_rows}"
        ),
    )

    return {
        "row_count": (
            EXPECTED_TOTAL_ROWS
        ),
        "decision_time_sequence_preserved": (
            True
        ),
        "dataset_split_sequence_preserved": (
            True
        ),
        "duplicate_decision_time_rows": (
            0
        ),
        "split_rows": (
            observed_split_rows
        ),
    }


def _validate_preserved_manifest_fields(
    *,
    source_manifest: Mapping[
        str,
        Any,
    ],
    output_manifest: Mapping[
        str,
        Any,
    ],
) -> list[str]:

    validated: list[str] = []

    for field in (
        PRESERVED_PARENT_FIELDS
    ):

        if (
            field
            not in
            source_manifest
        ):
            continue

        _require(
            field
            in
            output_manifest,
            (
                "PRESERVED_MANIFEST_FIELD_MISSING:"
                f"{field}"
            ),
        )

        _require(
            output_manifest[
                field
            ]
            ==
            source_manifest[
                field
            ],
            (
                "PRESERVED_MANIFEST_FIELD_CHANGED:"
                f"{field}"
            ),
        )

        validated.append(
            field
        )

    return validated


def _validate_output_manifest(
    *,
    source_manifest: Mapping[
        str,
        Any,
    ],
    output_manifest: Mapping[
        str,
        Any,
    ],
    output_dataset_sha256: str,
    output_manifest_sha256: str,
    result: Any,
) -> dict[str, Any]:

    _require(
        str(
            output_manifest.get(
                "manifest_version",
                "",
            )
        )
        ==
        PortableTrainingFeatureProjector.MANIFEST_VERSION,
        "OUTPUT_MANIFEST_VERSION_MISMATCH",
    )

    _require(
        str(
            output_manifest.get(
                "training_contract_version",
                "",
            )
        )
        ==
        EXPECTED_OUTPUT_CONTRACT,
        "OUTPUT_TRAINING_CONTRACT_MISMATCH",
    )

    _require(
        str(
            output_manifest.get(
                "dataset_id",
                "",
            )
        )
        ==
        str(
            result.dataset_id
        ),
        "OUTPUT_DATASET_ID_RESULT_MISMATCH",
    )

    _require(
        str(
            output_manifest.get(
                "dataset_sha256",
                "",
            )
        )
        ==
        output_dataset_sha256,
        "OUTPUT_MANIFEST_DATASET_SHA256_MISMATCH",
    )

    _require(
        output_dataset_sha256
        ==
        str(
            result.dataset_sha256
        ),
        "OUTPUT_DATASET_SHA256_RESULT_MISMATCH",
    )

    _require(
        output_manifest_sha256
        ==
        str(
            result.manifest_sha256
        ),
        "OUTPUT_MANIFEST_SHA256_RESULT_MISMATCH",
    )

    _require(
        int(
            output_manifest.get(
                "row_count",
                -1,
            )
        )
        ==
        EXPECTED_TOTAL_ROWS,
        "OUTPUT_MANIFEST_ROW_COUNT_MISMATCH",
    )

    _require(
        int(
            output_manifest.get(
                "feature_count",
                -1,
            )
        )
        ==
        EXPECTED_OUTPUT_FEATURE_COUNT,
        "OUTPUT_MANIFEST_FEATURE_COUNT_MISMATCH",
    )

    output_features = (
        _string_list(
            output_manifest.get(
                "feature_columns"
            ),
            field_name=(
                "feature_columns"
            ),
        )
    )

    _require(
        len(
            output_features
        )
        ==
        EXPECTED_OUTPUT_FEATURE_COUNT,
        "OUTPUT_MANIFEST_FEATURE_LIST_COUNT_MISMATCH",
    )

    for feature in (
        EXPECTED_DROPPED_FEATURES
    ):

        _require(
            feature
            not in
            output_features,
            (
                "DROPPED_FEATURE_PRESENT_IN_OUTPUT_MANIFEST:"
                f"{feature}"
            ),
        )

    _require(
        EXPECTED_RETAINED_FEATURE
        in
        output_features,
        "RETAINED_FEATURE_MISSING_FROM_OUTPUT_MANIFEST",
    )

    source_training_matrix = (
        _mapping(
            output_manifest,
            "source_training_matrix",
        )
    )

    _require(
        str(
            source_training_matrix.get(
                "dataset_id",
                "",
            )
        )
        ==
        EXPECTED_SOURCE_DATASET_ID,
        "OUTPUT_PARENT_DATASET_ID_MISMATCH",
    )

    _require(
        str(
            source_training_matrix.get(
                "dataset_sha256",
                "",
            )
        )
        ==
        EXPECTED_SOURCE_DATASET_SHA256,
        "OUTPUT_PARENT_DATASET_SHA256_MISMATCH",
    )

    _require(
        str(
            source_training_matrix.get(
                "manifest_sha256",
                "",
            )
        )
        ==
        EXPECTED_SOURCE_MANIFEST_SHA256,
        "OUTPUT_PARENT_MANIFEST_SHA256_MISMATCH",
    )

    _require(
        str(
            source_training_matrix.get(
                "training_contract_version",
                "",
            )
        )
        ==
        EXPECTED_SOURCE_CONTRACT,
        "OUTPUT_PARENT_CONTRACT_MISMATCH",
    )

    portable_contract = (
        _mapping(
            output_manifest,
            "portable_feature_contract",
        )
    )

    _require(
        str(
            portable_contract.get(
                "version",
                "",
            )
        )
        ==
        EXPECTED_OUTPUT_CONTRACT,
        "PORTABLE_FEATURE_CONTRACT_VERSION_MISMATCH",
    )

    _require(
        int(
            portable_contract.get(
                "parent_feature_count",
                -1,
            )
        )
        ==
        EXPECTED_SOURCE_FEATURE_COUNT,
        "PORTABLE_PARENT_FEATURE_COUNT_MISMATCH",
    )

    _require(
        int(
            portable_contract.get(
                "portable_feature_count",
                -1,
            )
        )
        ==
        EXPECTED_OUTPUT_FEATURE_COUNT,
        "PORTABLE_OUTPUT_FEATURE_COUNT_MISMATCH",
    )

    dropped = (
        _string_list(
            portable_contract.get(
                "dropped_features"
            ),
            field_name=(
                "portable_feature_contract.dropped_features"
            ),
        )
    )

    _require(
        dropped
        ==
        list(
            EXPECTED_DROPPED_FEATURES
        ),
        (
            "PORTABLE_DROPPED_FEATURE_POLICY_MISMATCH:"
            f"{dropped}"
        ),
    )

    added = (
        _string_list(
            portable_contract.get(
                "added_features"
            ),
            field_name=(
                "portable_feature_contract.added_features"
            ),
        )
    )

    _require(
        added
        ==
        [],
        "PORTABLE_ADDED_FEATURE_POLICY_MISMATCH",
    )

    _require(
        str(
            portable_contract.get(
                "retained_existing_broker_sensitive_feature",
                "",
            )
        )
        ==
        EXPECTED_RETAINED_FEATURE,
        "PORTABLE_RETAINED_FEATURE_POLICY_MISMATCH",
    )

    fingerprint = (
        _mapping(
            portable_contract,
            "contract_design_fingerprint",
        )
    )

    _require(
        str(
            fingerprint.get(
                "sha256",
                "",
            )
        )
        ==
        EXPECTED_CONTRACT_DESIGN_FINGERPRINT,
        "PORTABLE_CONTRACT_DESIGN_FINGERPRINT_MISMATCH",
    )

    _require(
        not bool(
            output_manifest.get(
                "live_authorized",
                True,
            )
        ),
        "OUTPUT_UNEXPECTEDLY_LIVE_AUTHORIZED",
    )

    preserved_fields = (
        _validate_preserved_manifest_fields(
            source_manifest=(
                source_manifest
            ),
            output_manifest=(
                output_manifest
            ),
        )
    )

    return {
        "manifest_version": (
            str(
                output_manifest.get(
                    "manifest_version",
                    "",
                )
            )
        ),
        "training_contract_version": (
            EXPECTED_OUTPUT_CONTRACT
        ),
        "feature_count": (
            EXPECTED_OUTPUT_FEATURE_COUNT
        ),
        "row_count": (
            EXPECTED_TOTAL_ROWS
        ),
        "parent_lineage_confirmed": (
            True
        ),
        "contract_design_fingerprint_confirmed": (
            True
        ),
        "dropped_features": list(
            EXPECTED_DROPPED_FEATURES
        ),
        "added_features": [],
        "retained_relative_volume_feature": (
            EXPECTED_RETAINED_FEATURE
        ),
        "preserved_parent_manifest_fields": (
            preserved_fields
        ),
        "live_authorized": (
            False
        ),
    }


def run_integration(
) -> dict[str, Any]:

    (
        source_dataset_path,
        source_manifest_path,
        source_manifest,
    ) = (
        _discover_exact_frozen_v3()
    )

    (
        source_feature_columns,
        target_columns,
    ) = (
        _validate_source_manifest(
            source_manifest
        )
    )

    source_dataset_sha256_before = (
        PortableTrainingFeatureProjector
        ._sha256_file(
            source_dataset_path
        )
    )

    source_manifest_sha256_before = (
        PortableTrainingFeatureProjector
        ._sha256_file(
            source_manifest_path
        )
    )

    _require(
        source_dataset_sha256_before
        ==
        EXPECTED_SOURCE_DATASET_SHA256,
        "SOURCE_DATASET_HASH_INVALID_BEFORE_PROJECTION",
    )

    _require(
        source_manifest_sha256_before
        ==
        EXPECTED_SOURCE_MANIFEST_SHA256,
        "SOURCE_MANIFEST_HASH_INVALID_BEFORE_PROJECTION",
    )

    projector = (
        PortableTrainingFeatureProjector(
            canonical_root=(
                ROOT_DIR
            )
        )
    )

    result = (
        projector.project(
            source_dataset_path=(
                source_dataset_path
            ),
            source_manifest_path=(
                source_manifest_path
            ),
        )
    )

    source_dataset_sha256_after = (
        PortableTrainingFeatureProjector
        ._sha256_file(
            source_dataset_path
        )
    )

    source_manifest_sha256_after = (
        PortableTrainingFeatureProjector
        ._sha256_file(
            source_manifest_path
        )
    )

    _require(
        source_dataset_sha256_after
        ==
        source_dataset_sha256_before,
        "SOURCE_DATASET_MUTATED_BY_PROJECTION",
    )

    _require(
        source_manifest_sha256_after
        ==
        source_manifest_sha256_before,
        "SOURCE_MANIFEST_MUTATED_BY_PROJECTION",
    )

    _require(
        result.dataset_path.is_file(),
        "PORTABLE_DATASET_FILE_NOT_FOUND",
    )

    _require(
        result.manifest_path.is_file(),
        "PORTABLE_MANIFEST_FILE_NOT_FOUND",
    )

    output_dataset_sha256 = (
        PortableTrainingFeatureProjector
        ._sha256_file(
            result.dataset_path
        )
    )

    output_manifest_sha256 = (
        PortableTrainingFeatureProjector
        ._sha256_file(
            result.manifest_path
        )
    )

    output_manifest = (
        PortableTrainingFeatureProjector
        ._load_json(
            result.manifest_path
        )
    )

    header_validation = (
        _validate_headers(
            source_dataset_path=(
                source_dataset_path
            ),
            output_dataset_path=(
                result.dataset_path
            ),
            source_feature_columns=(
                source_feature_columns
            ),
        )
    )

    structural_rows = (
        _validate_structural_rows(
            source_dataset_path=(
                source_dataset_path
            ),
            output_dataset_path=(
                result.dataset_path
            ),
        )
    )

    manifest_validation = (
        _validate_output_manifest(
            source_manifest=(
                source_manifest
            ),
            output_manifest=(
                output_manifest
            ),
            output_dataset_sha256=(
                output_dataset_sha256
            ),
            output_manifest_sha256=(
                output_manifest_sha256
            ),
            result=(
                result
            ),
        )
    )

    _require(
        int(
            result.row_count
        )
        ==
        EXPECTED_TOTAL_ROWS,
        "RESULT_ROW_COUNT_MISMATCH",
    )

    _require(
        int(
            result.feature_count
        )
        ==
        EXPECTED_OUTPUT_FEATURE_COUNT,
        "RESULT_FEATURE_COUNT_MISMATCH",
    )

    _require(
        int(
            result.dropped_feature_count
        )
        ==
        len(
            EXPECTED_DROPPED_FEATURES
        ),
        "RESULT_DROPPED_FEATURE_COUNT_MISMATCH",
    )

    _require(
        str(
            result.training_contract_version
        )
        ==
        EXPECTED_OUTPUT_CONTRACT,
        "RESULT_TRAINING_CONTRACT_MISMATCH",
    )

    _require(
        not bool(
            result.live_authorized
        ),
        "RESULT_UNEXPECTEDLY_LIVE_AUTHORIZED",
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_PORTABLE_TRAINING_FEATURE_PROJECTION_INTEGRATION"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "decision": {
            "status": (
                "XAUUSD_PORTABLE_331_FEATURE_DATASET_PROJECTION_CONFIRMED"
            ),
            "reason": (
                "IMMUTABLE_FROZEN_V3_MATRIX_WAS_PROJECTED_TO_THE_"
                "FROZEN_331_FEATURE_PORTABLE_CONTRACT_BY_REMOVING_"
                "EXACTLY_TWO_BROKER_SENSITIVE_MODEL_FEATURES"
            ),
            "source_contract": (
                EXPECTED_SOURCE_CONTRACT
            ),
            "output_contract": (
                EXPECTED_OUTPUT_CONTRACT
            ),
            "source_feature_count": (
                EXPECTED_SOURCE_FEATURE_COUNT
            ),
            "output_feature_count": (
                EXPECTED_OUTPUT_FEATURE_COUNT
            ),
            "dropped_features": list(
                EXPECTED_DROPPED_FEATURES
            ),
            "added_features": [],
            "retained_relative_volume_feature": (
                EXPECTED_RETAINED_FEATURE
            ),
            "source_artifacts_unchanged": (
                True
            ),
            "portable_dataset_written": (
                True
            ),
            "portable_manifest_written": (
                True
            ),
            "model_retraining_authorized": (
                False
            ),
            "validation_evaluation_authorized": (
                False
            ),
            "test_evaluation_authorized": (
                False
            ),
            "target_contract_change_authorized": (
                False
            ),
            "live_authorized": (
                False
            ),
            "next_action": (
                "AUDIT_PORTABLE_331_DATASET_EXACT_PROJECTION_"
                "AND_TRAIN_ONLY_MODEL_INPUT_READINESS"
            ),
        },
        "source_reference": {
            "dataset_id": (
                EXPECTED_SOURCE_DATASET_ID
            ),
            "dataset_sha256": (
                EXPECTED_SOURCE_DATASET_SHA256
            ),
            "manifest_sha256": (
                EXPECTED_SOURCE_MANIFEST_SHA256
            ),
            "training_contract_version": (
                EXPECTED_SOURCE_CONTRACT
            ),
            "row_count": (
                EXPECTED_TOTAL_ROWS
            ),
            "feature_count": (
                EXPECTED_SOURCE_FEATURE_COUNT
            ),
            "source_dataset_immutable_before_after": (
                True
            ),
            "source_manifest_immutable_before_after": (
                True
            ),
            "filesystem_path_emitted": (
                False
            ),
        },
        "portable_artifact": {
            "dataset_id": (
                str(
                    result.dataset_id
                )
            ),
            "dataset_sha256": (
                output_dataset_sha256
            ),
            "manifest_sha256": (
                output_manifest_sha256
            ),
            "training_contract_version": (
                EXPECTED_OUTPUT_CONTRACT
            ),
            "row_count": (
                EXPECTED_TOTAL_ROWS
            ),
            "feature_count": (
                EXPECTED_OUTPUT_FEATURE_COUNT
            ),
            "dropped_feature_count": (
                len(
                    EXPECTED_DROPPED_FEATURES
                )
            ),
            "contract_design_fingerprint_sha256": (
                EXPECTED_CONTRACT_DESIGN_FINGERPRINT
            ),
            "filesystem_path_emitted": (
                False
            ),
        },
        "header_validation": (
            header_validation
        ),
        "structural_row_validation": (
            structural_rows
        ),
        "manifest_validation": (
            manifest_validation
        ),
        "target_preservation": {
            "target_columns": (
                target_columns
            ),
            "target_columns_changed": (
                False
            ),
            "target_contract_changed": (
                False
            ),
            "target_values_used_for_selection": (
                False
            ),
            "target_metrics_computed": (
                False
            ),
        },
        "scientific_policy": {
            "frozen_v3_source_read": (
                True
            ),
            "portable_dataset_written": (
                True
            ),
            "portable_manifest_written": (
                True
            ),
            "existing_v3_dataset_modified": (
                False
            ),
            "existing_v3_manifest_modified": (
                False
            ),
            "existing_training_feature_enricher_modified": (
                False
            ),
            "existing_training_matrix_builder_modified": (
                False
            ),
            "existing_training_target_relabeler_modified": (
                False
            ),
            "existing_model_trainer_modified": (
                False
            ),
            "mt5_used": (
                False
            ),
            "new_market_data_loaded": (
                False
            ),
            "target_columns_copied_unchanged": (
                True
            ),
            "target_values_used_for_feature_selection": (
                False
            ),
            "target_metrics_computed": (
                False
            ),
            "validation_metrics_computed": (
                False
            ),
            "test_metrics_computed": (
                False
            ),
            "validation_used_for_selection": (
                False
            ),
            "test_used_for_selection": (
                False
            ),
            "model_loaded": (
                False
            ),
            "model_trained": (
                False
            ),
            "model_artifacts_written": (
                False
            ),
            "target_contract_changed": (
                False
            ),
            "orders_sent": (
                False
            ),
            "positions_modified": (
                False
            ),
            "risk_engine_modified": (
                False
            ),
            "sizing_modified": (
                False
            ),
            "execution_integration_modified": (
                False
            ),
            "live_authorized": (
                False
            ),
            "account_login_emitted": (
                False
            ),
            "account_holder_name_emitted": (
                False
            ),
            "account_scope_identifier_emitted": (
                False
            ),
            "filesystem_paths_emitted": (
                False
            ),
        },
    }


def main() -> int:

    try:

        result = (
            run_integration()
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_PORTABLE_TRAINING_FEATURE_"
                        "PROJECTION_INTEGRATION_FAILED"
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
                    "mt5_used": (
                        False
                    ),
                    "model_loaded": (
                        False
                    ),
                    "model_trained": (
                        False
                    ),
                    "validation_metrics_computed": (
                        False
                    ),
                    "test_metrics_computed": (
                        False
                    ),
                    "target_contract_changed": (
                        False
                    ),
                    "orders_sent": (
                        False
                    ),
                    "positions_modified": (
                        False
                    ),
                    "risk_engine_modified": (
                        False
                    ),
                    "live_authorized": (
                        False
                    ),
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