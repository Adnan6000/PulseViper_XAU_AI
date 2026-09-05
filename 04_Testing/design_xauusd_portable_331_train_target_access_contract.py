from __future__ import annotations

import ast
import hashlib
import importlib
import json
import math
import sys

from pathlib import Path
from typing import Any, Mapping


ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_TARGET_ACCESS_CONTRACT_DESIGN_V1"
)

TARGET_ACCESS_CONTRACT_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_TARGET_ACCESS_V1"
)


LOADER_MODULE = (
    "02_AI.Dataset.portable_331_training_input_loader"
)

loader_module: Any = importlib.import_module(
    LOADER_MODULE
)

Portable331TrainingInputLoader = (
    loader_module
    .Portable331TrainingInputLoader
)


LOADER_INTEGRATION_JSON = (
    ROOT_DIR
    /
    "04_Testing/evidence/research/portable_331/train/xauusd_portable_331_training_input_loader_integration.json"
)

LOADER_SOURCE = (
    ROOT_DIR
    /
    "02_AI"
    /
    "Dataset"
    /
    "portable_331_training_input_loader.py"
)


EXPECTED_LOADER_INTEGRATION_VERSION = (
    "XAUUSD_PORTABLE_331_TRAINING_INPUT_LOADER_INTEGRATION_V1"
)

EXPECTED_LOADER_INTEGRATION_STATUS = (
    "XAUUSD_PORTABLE_331_TRAIN_FEATURE_LOADER_INTEGRATION_CONFIRMED"
)


EXPECTED_DATASET_ID = (
    "portable_cff75b0686383a3ab6f8352b"
)

EXPECTED_DATASET_SHA256 = (
    "cff75b0686383a3ab6f8352bfcdcd55308b99b7a4c6edbf7d2e7215f6f33dd07"
)

EXPECTED_MANIFEST_SHA256 = (
    "1b8e3599b227c9cbbc6b12f8ab0e275ca4deb4a65839fb626ca90720d59512dc"
)


EXPECTED_FEATURE_CONTRACT = (
    "XAUUSD_MTF_PORTABLE_FEATURE_V1"
)

EXPECTED_TRAINER_INPUT_CONTRACT = (
    "XAUUSD_PORTABLE_331_RESEARCH_TRAINER_INPUT_V1"
)

EXPECTED_TRAINER_INPUT_CONTRACT_FINGERPRINT_SHA256 = (
    "b192ce16291fe9ddca9ead9561224fb942c331d1f30fc1b53cee396efa5accdf"
)


EXPECTED_FEATURE_COUNT = (
    331
)

EXPECTED_TRAIN_ROWS = (
    69966
)

EXPECTED_VALIDATION_ROWS = (
    14983
)

EXPECTED_TEST_ROWS = (
    14996
)


EXPECTED_TARGET_LABEL_CONTRACT = (
    "CLEAN_DIRECTIONAL_EXCURSION_V2"
)

EXPECTED_TARGET_PROFIT_ATR = (
    1.25
)

EXPECTED_TARGET_MAX_ADVERSE_ATR = (
    0.75
)


EXPECTED_TARGET_CLASS_MAPPING = {
    "SHORT": -1,
    "NO_TRADE": 0,
    "LONG": 1,
}


TRAIN_TARGET_COLUMNS = (
    "target_class",
    "target_tradeable",
)


CURRENT_BLOCKED_ACCESSORS = {
    "load_train_targets": (
        "TRAIN_TARGET_ACCESS_NOT_AUTHORIZED"
    ),
    "load_train_supervised": (
        "SUPERVISED_TRAIN_INPUT_ACCESS_NOT_AUTHORIZED"
    ),
    "load_validation_features": (
        "VALIDATION_FEATURE_ACCESS_NOT_AUTHORIZED"
    ),
    "load_validation_targets": (
        "VALIDATION_TARGET_ACCESS_NOT_AUTHORIZED"
    ),
    "load_test_features": (
        "TEST_FEATURE_ACCESS_NOT_AUTHORIZED"
    ),
    "load_test_targets": (
        "TEST_TARGET_ACCESS_NOT_AUTHORIZED"
    ),
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
    document: Mapping[str, Any],
    key: str,
) -> Mapping[str, Any]:

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

    result = [
        str(
            item
        )
        for item
        in value
    ]

    if any(
        not item
        for item
        in result
    ):
        raise RuntimeError(
            (
                "EMPTY_LIST_VALUE:"
                f"{field_name}"
            )
        )

    return result


def _required_int(
    mapping: Mapping[str, Any],
    key: str,
) -> int:

    if key not in mapping:
        raise RuntimeError(
            (
                "REQUIRED_INTEGER_MISSING:"
                f"{key}"
            )
        )

    value = mapping[
        key
    ]

    if value is None:
        raise RuntimeError(
            (
                "REQUIRED_INTEGER_NONE:"
                f"{key}"
            )
        )

    if isinstance(
        value,
        bool,
    ):
        raise RuntimeError(
            (
                "REQUIRED_INTEGER_BOOLEAN:"
                f"{key}"
            )
        )

    try:

        return int(
            value
        )

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise RuntimeError(
            (
                "REQUIRED_INTEGER_INVALID:"
                f"{key}:"
                f"{value}"
            )
        ) from exc


def _required_float(
    mapping: Mapping[str, Any],
    key: str,
) -> float:

    if key not in mapping:
        raise RuntimeError(
            (
                "REQUIRED_FLOAT_MISSING:"
                f"{key}"
            )
        )

    value = mapping[
        key
    ]

    if value is None:
        raise RuntimeError(
            (
                "REQUIRED_FLOAT_NONE:"
                f"{key}"
            )
        )

    if isinstance(
        value,
        bool,
    ):
        raise RuntimeError(
            (
                "REQUIRED_FLOAT_BOOLEAN:"
                f"{key}"
            )
        )

    try:

        result = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise RuntimeError(
            (
                "REQUIRED_FLOAT_INVALID:"
                f"{key}:"
                f"{value}"
            )
        ) from exc

    if not math.isfinite(
        result
    ):
        raise RuntimeError(
            (
                "REQUIRED_FLOAT_NONFINITE:"
                f"{key}"
            )
        )

    return result


def _canonical_json_sha256(
    value: Any,
) -> str:

    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=True,
        allow_nan=False,
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        payload
    ).hexdigest()


def _validate_loader_integration(
) -> Mapping[str, Any]:

    document = (
        loader_module
        .PortableTrainingFeatureProjector
        ._load_json(
            LOADER_INTEGRATION_JSON
        )
        if hasattr(
            loader_module,
            "PortableTrainingFeatureProjector",
        )
        else
        json.loads(
            LOADER_INTEGRATION_JSON.read_text(
                encoding="utf-8-sig"
            )
        )
    )

    if not isinstance(
        document,
        Mapping,
    ):
        raise RuntimeError(
            "LOADER_INTEGRATION_JSON_ROOT_NOT_OBJECT"
        )

    _require(
        bool(
            document.get(
                "valid",
                False,
            )
        ),
        "LOADER_INTEGRATION_INVALID",
    )

    _require(
        str(
            document.get(
                "analysis_version",
                "",
            )
        )
        ==
        EXPECTED_LOADER_INTEGRATION_VERSION,
        "LOADER_INTEGRATION_VERSION_MISMATCH",
    )

    decision = (
        _mapping(
            document,
            "decision",
        )
    )

    _require(
        str(
            decision.get(
                "status",
                "",
            )
        )
        ==
        EXPECTED_LOADER_INTEGRATION_STATUS,
        "LOADER_INTEGRATION_STATUS_MISMATCH",
    )

    _require(
        int(
            decision.get(
                "train_rows",
                -1,
            )
        )
        ==
        EXPECTED_TRAIN_ROWS,
        "LOADER_INTEGRATION_TRAIN_ROWS_MISMATCH",
    )

    _require(
        int(
            decision.get(
                "feature_count",
                -1,
            )
        )
        ==
        EXPECTED_FEATURE_COUNT,
        "LOADER_INTEGRATION_FEATURE_COUNT_MISMATCH",
    )

    _require(
        bool(
            decision.get(
                "train_feature_loading_confirmed",
                False,
            )
        ),
        "TRAIN_FEATURE_LOADING_NOT_CONFIRMED",
    )

    _require(
        not bool(
            decision.get(
                "train_target_access_confirmed",
                True,
            )
        ),
        "TRAIN_TARGET_ACCESS_ALREADY_CONFIRMED",
    )

    _require(
        not bool(
            decision.get(
                "validation_feature_access_confirmed",
                True,
            )
        ),
        "VALIDATION_FEATURE_ACCESS_ALREADY_CONFIRMED",
    )

    _require(
        not bool(
            decision.get(
                "test_feature_access_confirmed",
                True,
            )
        ),
        "TEST_FEATURE_ACCESS_ALREADY_CONFIRMED",
    )

    _require(
        not bool(
            decision.get(
                "model_training_authorized",
                True,
            )
        ),
        "MODEL_TRAINING_UNEXPECTEDLY_AUTHORIZED",
    )

    next_contract = (
        _mapping(
            document,
            "next_decision_contract",
        )
    )

    _require(
        str(
            next_contract.get(
                "if_integration_confirmed",
                "",
            )
        )
        ==
        (
            "DESIGN_TRAIN_ONLY_SUPERVISED_TARGET_ACCESS_"
            "CONTRACT_WITHOUT_MODEL_FIT"
        ),
        "LOADER_INTEGRATION_NEXT_ACTION_MISMATCH",
    )

    scientific_policy = (
        _mapping(
            document,
            "scientific_policy",
        )
    )

    _require(
        not bool(
            scientific_policy.get(
                "train_target_values_loaded",
                True,
            )
        ),
        "TRAIN_TARGET_VALUES_ALREADY_LOADED",
    )

    _require(
        not bool(
            scientific_policy.get(
                "validation_target_values_loaded",
                True,
            )
        ),
        "VALIDATION_TARGET_VALUES_ALREADY_LOADED",
    )

    _require(
        not bool(
            scientific_policy.get(
                "test_target_values_loaded",
                True,
            )
        ),
        "TEST_TARGET_VALUES_ALREADY_LOADED",
    )

    _require(
        not bool(
            scientific_policy.get(
                "model_trained",
                True,
            )
        ),
        "MODEL_ALREADY_TRAINED",
    )

    return document


def _discover_and_validate_manifest(
) -> tuple[
    Path,
    Path,
    dict[str, Any],
]:

    loader = (
        Portable331TrainingInputLoader(
            canonical_root=(
                ROOT_DIR
            )
        )
    )

    (
        dataset_path,
        manifest_path,
        manifest,
    ) = (
        loader._discover_exact_artifact()
    )

    dataset_sha256 = (
        loader_module
        .PortableTrainingFeatureProjector
        ._sha256_file(
            dataset_path
        )
    )

    manifest_sha256 = (
        loader_module
        .PortableTrainingFeatureProjector
        ._sha256_file(
            manifest_path
        )
    )

    _require(
        dataset_sha256
        ==
        EXPECTED_DATASET_SHA256,
        "PORTABLE_DATASET_HASH_MISMATCH",
    )

    _require(
        manifest_sha256
        ==
        EXPECTED_MANIFEST_SHA256,
        "PORTABLE_MANIFEST_HASH_MISMATCH",
    )

    _require(
        str(
            manifest.get(
                "dataset_id",
                "",
            )
        )
        ==
        EXPECTED_DATASET_ID,
        "PORTABLE_DATASET_ID_MISMATCH",
    )

    _require(
        str(
            manifest.get(
                "dataset_sha256",
                "",
            )
        )
        ==
        EXPECTED_DATASET_SHA256,
        "PORTABLE_MANIFEST_DATASET_SHA256_MISMATCH",
    )

    _require(
        str(
            manifest.get(
                "training_contract_version",
                "",
            )
        )
        ==
        EXPECTED_FEATURE_CONTRACT,
        "PORTABLE_FEATURE_CONTRACT_MISMATCH",
    )

    target_columns = (
        _string_list(
            manifest.get(
                "target_columns"
            ),
            field_name=(
                "target_columns"
            ),
        )
    )

    for target_column in (
        TRAIN_TARGET_COLUMNS
    ):

        _require(
            target_column
            in
            target_columns,
            (
                "REQUIRED_TRAIN_TARGET_COLUMN_MISSING:"
                f"{target_column}"
            ),
        )

    mapping = (
        _mapping(
            manifest,
            "target_class_mapping",
        )
    )

    normalized_mapping: dict[
        str,
        int
    ] = {}

    for class_name in (
        EXPECTED_TARGET_CLASS_MAPPING
    ):

        normalized_mapping[
            class_name
        ] = (
            _required_int(
                mapping,
                class_name,
            )
        )

    _require(
        normalized_mapping
        ==
        EXPECTED_TARGET_CLASS_MAPPING,
        (
            "TARGET_CLASS_MAPPING_MISMATCH:"
            f"{normalized_mapping}"
        ),
    )

    target_contract = (
        _mapping(
            manifest,
            "target_label_contract",
        )
    )

    _require(
        str(
            target_contract.get(
                "name",
                "",
            )
        )
        ==
        EXPECTED_TARGET_LABEL_CONTRACT,
        "TARGET_LABEL_CONTRACT_MISMATCH",
    )

    profit_atr = (
        _required_float(
            target_contract,
            "profit_atr",
        )
    )

    max_adverse_atr = (
        _required_float(
            target_contract,
            "max_adverse_atr",
        )
    )

    _require(
        profit_atr
        ==
        EXPECTED_TARGET_PROFIT_ATR,
        "TARGET_PROFIT_ATR_MISMATCH",
    )

    _require(
        max_adverse_atr
        ==
        EXPECTED_TARGET_MAX_ADVERSE_ATR,
        "TARGET_MAX_ADVERSE_ATR_MISMATCH",
    )

    return (
        dataset_path,
        manifest_path,
        manifest,
    )


def _method_string_literals(
    method: ast.FunctionDef | ast.AsyncFunctionDef,
) -> set[str]:

    result: set[str] = set()

    for node in ast.walk(
        method
    ):

        if (
            isinstance(
                node,
                ast.Constant,
            )
            and
            isinstance(
                node.value,
                str,
            )
        ):

            result.add(
                node.value
            )

    return result


def _inspect_loader_fail_closed_state(
) -> dict[str, Any]:

    _require(
        LOADER_SOURCE.is_file(),
        "LOADER_SOURCE_NOT_FOUND",
    )

    try:

        source_text = (
            LOADER_SOURCE.read_text(
                encoding="utf-8"
            )
        )

    except UnicodeDecodeError:

        source_text = (
            LOADER_SOURCE.read_text(
                encoding="utf-8-sig"
            )
        )

    try:

        tree = ast.parse(
            source_text
        )

    except SyntaxError as exc:

        raise RuntimeError(
            (
                "LOADER_SOURCE_AST_PARSE_FAILED:"
                f"{exc}"
            )
        ) from exc

    loader_class: ast.ClassDef | None = (
        None
    )

    for node in tree.body:

        if (
            isinstance(
                node,
                ast.ClassDef,
            )
            and
            node.name
            ==
            "Portable331TrainingInputLoader"
        ):

            loader_class = (
                node
            )

            break

    if loader_class is None:
        raise RuntimeError(
            "PORTABLE_331_LOADER_CLASS_NOT_FOUND"
        )

    methods: dict[
        str,
        ast.FunctionDef | ast.AsyncFunctionDef
    ] = {}

    for node in loader_class.body:

        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):

            methods[
                node.name
            ] = (
                node
            )

    confirmed: dict[
        str,
        str
    ] = {}

    for (
        method_name,
        expected_error,
    ) in CURRENT_BLOCKED_ACCESSORS.items():

        method = methods.get(
            method_name
        )

        if method is None:
            raise RuntimeError(
                (
                    "EXPECTED_FAIL_CLOSED_METHOD_MISSING:"
                    f"{method_name}"
                )
            )

        literals = (
            _method_string_literals(
                method
            )
        )

        _require(
            expected_error
            in
            literals,
            (
                "FAIL_CLOSED_ERROR_LITERAL_MISSING:"
                f"{method_name}:"
                f"{expected_error}"
            ),
        )

        confirmed[
            method_name
        ] = (
            expected_error
        )

    source_sha256 = hashlib.sha256(
        source_text.encode(
            "utf-8"
        )
    ).hexdigest()

    return {
        "loader_class": (
            "Portable331TrainingInputLoader"
        ),
        "source_sha256": (
            source_sha256
        ),
        "current_fail_closed_accessors": (
            confirmed
        ),
        "train_target_accessor_currently_blocked": (
            True
        ),
        "supervised_train_accessor_currently_blocked": (
            True
        ),
        "validation_access_currently_blocked": (
            True
        ),
        "test_access_currently_blocked": (
            True
        ),
    }


def _target_metadata(
    manifest: Mapping[str, Any],
) -> dict[str, Any]:

    target_columns = (
        _string_list(
            manifest.get(
                "target_columns"
            ),
            field_name=(
                "target_columns"
            ),
        )
    )

    mapping = (
        _mapping(
            manifest,
            "target_class_mapping",
        )
    )

    normalized_mapping: dict[
        str,
        int
    ] = {}

    for class_name in (
        EXPECTED_TARGET_CLASS_MAPPING
    ):

        normalized_mapping[
            class_name
        ] = (
            _required_int(
                mapping,
                class_name,
            )
        )

    target_contract = (
        _mapping(
            manifest,
            "target_label_contract",
        )
    )

    return {
        "target_columns": (
            target_columns
        ),
        "target_class_mapping": (
            normalized_mapping
        ),
        "target_label_contract": {
            "name": str(
                target_contract.get(
                    "name",
                    "",
                )
            ),
            "profit_atr": (
                _required_float(
                    target_contract,
                    "profit_atr",
                )
            ),
            "max_adverse_atr": (
                _required_float(
                    target_contract,
                    "max_adverse_atr",
                )
            ),
        },
        "target_horizon_bars": (
            manifest.get(
                "target_horizon_bars"
            )
        ),
        "target_future_data_rule": (
            manifest.get(
                "target_future_data_rule"
            )
        ),
    }


def _contract_core(
    *,
    manifest: Mapping[str, Any],
    loader_inspection: Mapping[str, Any],
) -> dict[str, Any]:

    metadata = (
        _target_metadata(
            manifest
        )
    )

    metadata_sha256 = (
        _canonical_json_sha256(
            metadata
        )
    )

    return {
        "contract_version": (
            TARGET_ACCESS_CONTRACT_VERSION
        ),
        "contract_status": (
            "DESIGN_ONLY_NOT_IMPLEMENTED"
        ),
        "asset": (
            "XAUUSD"
        ),
        "parent_contracts": {
            "portable_feature_contract": (
                EXPECTED_FEATURE_CONTRACT
            ),
            "trainer_input_contract": (
                EXPECTED_TRAINER_INPUT_CONTRACT
            ),
            "trainer_input_contract_fingerprint_sha256": (
                EXPECTED_TRAINER_INPUT_CONTRACT_FINGERPRINT_SHA256
            ),
        },
        "artifact_identity": {
            "dataset_id": (
                EXPECTED_DATASET_ID
            ),
            "dataset_sha256": (
                EXPECTED_DATASET_SHA256
            ),
            "manifest_sha256": (
                EXPECTED_MANIFEST_SHA256
            ),
        },
        "target_contract": {
            "target_contract_changed": (
                False
            ),
            "target_metadata": (
                metadata
            ),
            "target_metadata_sha256": (
                metadata_sha256
            ),
            "train_target_columns": list(
                TRAIN_TARGET_COLUMNS
            ),
            "target_class_allowed_values": [
                -1,
                0,
                1,
            ],
            "target_tradeable_allowed_values": [
                0,
                1,
            ],
            "target_tradeable_linkage_rule": (
                "target_tradeable == int(target_class != 0)"
            ),
            "target_values_must_not_be_recomputed": (
                True
            ),
            "target_values_must_be_loaded_from_frozen_portable_artifact": (
                True
            ),
            "missing_target_values_allowed": (
                False
            ),
            "nonfinite_target_values_allowed": (
                False
            ),
        },
        "train_access_contract": {
            "row_count": (
                EXPECTED_TRAIN_ROWS
            ),
            "read_scope": (
                "FIRST_EXACT_69966_TRAIN_ROWS_ONLY"
            ),
            "required_read_columns": [
                "decision_time",
                "target_class",
                "target_tradeable",
            ],
            "full_dataset_target_column_read_allowed": (
                False
            ),
            "validation_target_rows_allowed": (
                False
            ),
            "test_target_rows_allowed": (
                False
            ),
            "decision_time_unique_required": (
                True
            ),
            "decision_time_alignment_with_train_feature_batch_required": (
                True
            ),
            "target_class_integer_semantics_required": (
                True
            ),
            "target_tradeable_binary_integer_semantics_required": (
                True
            ),
            "target_tradeable_linkage_validation_required": (
                True
            ),
            "target_class_distribution_may_be_reported": (
                False
            ),
            "target_metrics_may_be_computed": (
                False
            ),
        },
        "loader_implementation_contract": {
            "module": (
                "02_AI.Dataset.portable_331_training_input_loader"
            ),
            "class": (
                "Portable331TrainingInputLoader"
            ),
            "new_result_dataclass": (
                "Portable331TrainTargetBatch"
            ),
            "method_to_implement": (
                "load_train_targets"
            ),
            "load_train_supervised_remains_blocked": (
                True
            ),
            "validation_feature_access_remains_blocked": (
                True
            ),
            "validation_target_access_remains_blocked": (
                True
            ),
            "test_feature_access_remains_blocked": (
                True
            ),
            "test_target_access_remains_blocked": (
                True
            ),
            "scaler_fit_performed": (
                False
            ),
            "model_fit_performed": (
                False
            ),
            "metrics_computed": (
                False
            ),
            "model_artifacts_written": (
                False
            ),
        },
        "current_loader_state": (
            dict(
                loader_inspection
            )
        ),
        "authorization": {
            "train_target_loader_implementation_authorized": (
                False
            ),
            "train_supervised_combination_authorized": (
                False
            ),
            "model_architecture_selection_authorized": (
                False
            ),
            "scaler_fit_authorized": (
                False
            ),
            "model_training_authorized": (
                False
            ),
            "validation_feature_access_authorized": (
                False
            ),
            "validation_target_access_authorized": (
                False
            ),
            "test_feature_access_authorized": (
                False
            ),
            "test_target_access_authorized": (
                False
            ),
            "target_contract_change_authorized": (
                False
            ),
            "live_authorized": (
                False
            ),
        },
    }


def run_design(
) -> dict[str, Any]:

    integration = (
        _validate_loader_integration()
    )

    (
        _dataset_path,
        _manifest_path,
        manifest,
    ) = (
        _discover_and_validate_manifest()
    )

    loader_inspection = (
        _inspect_loader_fail_closed_state()
    )

    contract_core = (
        _contract_core(
            manifest=(
                manifest
            ),
            loader_inspection=(
                loader_inspection
            ),
        )
    )

    contract_fingerprint = (
        _canonical_json_sha256(
            contract_core
        )
    )

    integration_decision = (
        _mapping(
            integration,
            "decision",
        )
    )

    _require(
        str(
            integration_decision.get(
                "next_action",
                "",
            )
        )
        ==
        (
            "DESIGN_TRAIN_ONLY_SUPERVISED_TARGET_ACCESS_"
            "CONTRACT_WITHOUT_MODEL_FIT"
        ),
        "INTEGRATION_DID_NOT_AUTHORIZE_TARGET_ACCESS_DESIGN",
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_PORTABLE_331_TRAIN_TARGET_ACCESS_CONTRACT_DESIGN"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "research_scope": (
            "DESIGN_ONLY_TRAIN_PREFIX_TARGET_ACCESS_WITHOUT_"
            "TARGET_VALUE_LOADING_MODEL_FIT_OR_HOLDOUT_ACCESS"
        ),
        "contract": (
            contract_core
        ),
        "contract_fingerprint": {
            "version": (
                "XAUUSD_PORTABLE_331_TRAIN_TARGET_ACCESS_"
                "CONTRACT_FINGERPRINT_V1"
            ),
            "sha256": (
                contract_fingerprint
            ),
            "canonicalization": (
                "JSON_SORT_KEYS_COMPACT_UTF8_SHA256"
            ),
        },
        "decision": {
            "status": (
                "XAUUSD_PORTABLE_331_TRAIN_TARGET_ACCESS_CONTRACT_DESIGN_CONFIRMED"
            ),
            "reason": (
                "TRAIN_ONLY_TARGET_ACCESS_IS_PINNED_TO_THE_"
                "FROZEN_PORTABLE_ARTIFACT_WITH_EXACT_TARGET_COLUMNS_"
                "CLASS_DOMAIN_TRADEABLE_LINKAGE_AND_HOLDOUT_BLOCKING"
            ),
            "target_access_contract_version": (
                TARGET_ACCESS_CONTRACT_VERSION
            ),
            "target_access_contract_fingerprint_sha256": (
                contract_fingerprint
            ),
            "train_rows": (
                EXPECTED_TRAIN_ROWS
            ),
            "train_target_columns": list(
                TRAIN_TARGET_COLUMNS
            ),
            "train_target_loader_implementation_authorized_next": (
                True
            ),
            "load_train_supervised_authorized": (
                False
            ),
            "model_architecture_selected": (
                False
            ),
            "scaler_fit_authorized": (
                False
            ),
            "model_training_authorized": (
                False
            ),
            "validation_feature_access_authorized": (
                False
            ),
            "validation_target_access_authorized": (
                False
            ),
            "test_feature_access_authorized": (
                False
            ),
            "test_target_access_authorized": (
                False
            ),
            "target_contract_change_authorized": (
                False
            ),
            "live_authorized": (
                False
            ),
            "next_action": (
                "IMPLEMENT_TRAIN_ONLY_TARGET_LOADER_WITHOUT_"
                "SUPERVISED_COMBINATION_OR_MODEL_FIT"
            ),
        },
        "scientific_policy": {
            "loader_integration_evidence_loaded": (
                True
            ),
            "portable_manifest_loaded": (
                True
            ),
            "portable_dataset_bytes_hashed": (
                True
            ),
            "portable_dataset_rows_loaded": (
                False
            ),
            "train_feature_values_loaded": (
                False
            ),
            "train_target_values_loaded": (
                False
            ),
            "validation_feature_values_loaded": (
                False
            ),
            "validation_target_values_loaded": (
                False
            ),
            "test_feature_values_loaded": (
                False
            ),
            "test_target_values_loaded": (
                False
            ),
            "target_distribution_computed": (
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
            "scaler_fit": (
                False
            ),
            "model_architecture_selected": (
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
            "dataset_written": (
                False
            ),
            "manifest_written": (
                False
            ),
            "loader_source_read_only": (
                True
            ),
            "loader_modified": (
                False
            ),
            "portable_dataset_modified": (
                False
            ),
            "portable_manifest_modified": (
                False
            ),
            "target_contract_changed": (
                False
            ),
            "mt5_used": (
                False
            ),
            "new_market_data_loaded": (
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
            "filesystem_paths_emitted": (
                False
            ),
        },
        "next_decision_contract": {
            "if_design_confirmed": (
                "IMPLEMENT_TRAIN_ONLY_TARGET_LOADER_WITHOUT_"
                "SUPERVISED_COMBINATION_OR_MODEL_FIT"
            ),
            "method_to_change": (
                "Portable331TrainingInputLoader.load_train_targets"
            ),
            "new_result_dataclass": (
                "Portable331TrainTargetBatch"
            ),
            "load_train_supervised_remains_blocked": (
                True
            ),
            "validation_access_remains_blocked": (
                True
            ),
            "test_access_remains_blocked": (
                True
            ),
            "model_training_not_authorized": (
                True
            ),
            "target_contract_change_required": (
                False
            ),
            "live_authorization_not_changed": (
                True
            ),
        },
    }


def main() -> int:

    try:

        result = (
            run_design()
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_PORTABLE_331_TRAIN_TARGET_ACCESS_"
                        "CONTRACT_DESIGN_FAILED"
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
                    "portable_dataset_rows_loaded": (
                        False
                    ),
                    "train_target_values_loaded": (
                        False
                    ),
                    "validation_target_values_loaded": (
                        False
                    ),
                    "test_target_values_loaded": (
                        False
                    ),
                    "model_loaded": (
                        False
                    ),
                    "model_trained": (
                        False
                    ),
                    "scaler_fit": (
                        False
                    ),
                    "dataset_written": (
                        False
                    ),
                    "mt5_used": (
                        False
                    ),
                    "orders_sent": (
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