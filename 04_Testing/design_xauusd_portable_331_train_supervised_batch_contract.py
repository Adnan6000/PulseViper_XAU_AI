from __future__ import annotations

import ast
import hashlib
import json
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
    "XAUUSD_PORTABLE_331_TRAIN_SUPERVISED_BATCH_CONTRACT_DESIGN_V1"
)

SUPERVISED_BATCH_CONTRACT_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_SUPERVISED_BATCH_V1"
)


TARGET_INTEGRATION_JSON = (
    ROOT_DIR
    /
    "xauusd_portable_331_train_target_loader_integration.json"
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


EXPECTED_TARGET_INTEGRATION_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_TARGET_LOADER_INTEGRATION_V1"
)

EXPECTED_TARGET_INTEGRATION_STATUS = (
    "XAUUSD_PORTABLE_331_TRAIN_TARGET_LOADER_INTEGRATION_CONFIRMED"
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


EXPECTED_TARGET_ACCESS_CONTRACT = (
    "XAUUSD_PORTABLE_331_TRAIN_TARGET_ACCESS_V1"
)

EXPECTED_TARGET_ACCESS_CONTRACT_FINGERPRINT_SHA256 = (
    "a640b9cda2522b734515a2cdf05259abbf77e4c6488afd635aedc21f62458266"
)


EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256 = (
    "9ffb72759499cfc202e88cfdbd61b42cee5b5c7cbb7db5870470453caa5ed2c5"
)

EXPECTED_TRAIN_TARGET_FINGERPRINT_SHA256 = (
    "bc063a790e70cdbc931b2170ccfef883634b40ee7336a529a32bda0eaf0babe3"
)


EXPECTED_FEATURE_COUNT = (
    331
)

EXPECTED_TRAIN_ROWS = (
    69966
)


EXPECTED_TARGET_COLUMNS = (
    "target_class",
    "target_tradeable",
)


EXPECTED_TARGET_CLASS_VALUES = (
    -1,
    0,
    1,
)

EXPECTED_TARGET_TRADEABLE_VALUES = (
    0,
    1,
)


EXPECTED_BLOCKED_ACCESSORS = {
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

        result = int(
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


def _decode_text_bytes(
    raw: bytes,
    *,
    source_name: str,
) -> str:
    """
    Decode text files produced either by Python/modern PowerShell as UTF-8
    or Windows PowerShell redirection as UTF-16.

    Supported BOM-aware forms:
    - UTF-8 BOM
    - UTF-16 LE BOM
    - UTF-16 BE BOM
    - plain UTF-8
    """

    if raw.startswith(
        b"\xef\xbb\xbf"
    ):
        try:

            return raw.decode(
                "utf-8-sig"
            )

        except UnicodeDecodeError as exc:

            raise RuntimeError(
                (
                    "UTF8_BOM_TEXT_DECODE_FAILED:"
                    f"{source_name}"
                )
            ) from exc

    if (
        raw.startswith(
            b"\xff\xfe"
        )
        or
        raw.startswith(
            b"\xfe\xff"
        )
    ):
        try:

            return raw.decode(
                "utf-16"
            )

        except UnicodeDecodeError as exc:

            raise RuntimeError(
                (
                    "UTF16_TEXT_DECODE_FAILED:"
                    f"{source_name}"
                )
            ) from exc

    try:

        return raw.decode(
            "utf-8"
        )

    except UnicodeDecodeError as exc:

        raise RuntimeError(
            (
                "TEXT_ENCODING_NOT_SUPPORTED:"
                f"{source_name}"
            )
        ) from exc


def _read_text_auto(
    path: Path,
) -> str:

    _require(
        path.is_file(),
        (
            "TEXT_FILE_NOT_FOUND:"
            f"{path.name}"
        ),
    )

    try:

        raw = path.read_bytes()

    except OSError as exc:

        raise RuntimeError(
            (
                "TEXT_FILE_READ_FAILED:"
                f"{path.name}"
            )
        ) from exc

    return _decode_text_bytes(
        raw,
        source_name=(
            path.name
        ),
    )


def _load_json_object(
    path: Path,
) -> dict[str, Any]:

    text = (
        _read_text_auto(
            path
        )
    )

    try:

        document_raw: Any = (
            json.loads(
                text
            )
        )

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            (
                "JSON_PARSE_FAILED:"
                f"{path.name}:"
                f"line={exc.lineno}:"
                f"column={exc.colno}"
            )
        ) from exc

    if not isinstance(
        document_raw,
        dict,
    ):
        raise RuntimeError(
            (
                "JSON_ROOT_NOT_OBJECT:"
                f"{path.name}"
            )
        )

    return document_raw


def _validate_target_integration(
) -> Mapping[str, Any]:

    document = (
        _load_json_object(
            TARGET_INTEGRATION_JSON
        )
    )

    _require(
        bool(
            document.get(
                "valid",
                False,
            )
        ),
        "TARGET_LOADER_INTEGRATION_INVALID",
    )

    _require(
        str(
            document.get(
                "analysis_version",
                "",
            )
        )
        ==
        EXPECTED_TARGET_INTEGRATION_VERSION,
        "TARGET_LOADER_INTEGRATION_VERSION_MISMATCH",
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
        EXPECTED_TARGET_INTEGRATION_STATUS,
        "TARGET_LOADER_INTEGRATION_STATUS_MISMATCH",
    )

    _require(
        _required_int(
            decision,
            "train_rows",
        )
        ==
        EXPECTED_TRAIN_ROWS,
        "TARGET_LOADER_TRAIN_ROW_COUNT_MISMATCH",
    )

    _require(
        bool(
            decision.get(
                "train_target_loading_confirmed",
                False,
            )
        ),
        "TRAIN_TARGET_LOADING_NOT_CONFIRMED",
    )

    _require(
        bool(
            decision.get(
                "train_feature_target_time_alignment_confirmed",
                False,
            )
        ),
        "TRAIN_FEATURE_TARGET_ALIGNMENT_NOT_CONFIRMED",
    )

    _require(
        not bool(
            decision.get(
                "train_supervised_combination_authorized",
                True,
            )
        ),
        "SUPERVISED_COMBINATION_ALREADY_AUTHORIZED",
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

    _require(
        not bool(
            decision.get(
                "validation_feature_access_authorized",
                True,
            )
        ),
        "VALIDATION_FEATURE_ACCESS_UNEXPECTEDLY_AUTHORIZED",
    )

    _require(
        not bool(
            decision.get(
                "validation_target_access_authorized",
                True,
            )
        ),
        "VALIDATION_TARGET_ACCESS_UNEXPECTEDLY_AUTHORIZED",
    )

    _require(
        not bool(
            decision.get(
                "test_feature_access_authorized",
                True,
            )
        ),
        "TEST_FEATURE_ACCESS_UNEXPECTEDLY_AUTHORIZED",
    )

    _require(
        not bool(
            decision.get(
                "test_target_access_authorized",
                True,
            )
        ),
        "TEST_TARGET_ACCESS_UNEXPECTEDLY_AUTHORIZED",
    )

    _require(
        str(
            decision.get(
                "train_target_fingerprint_sha256",
                "",
            )
        )
        ==
        EXPECTED_TRAIN_TARGET_FINGERPRINT_SHA256,
        "TRAIN_TARGET_FINGERPRINT_MISMATCH",
    )

    artifact = (
        _mapping(
            document,
            "artifact_identity",
        )
    )

    _require(
        str(
            artifact.get(
                "dataset_id",
                "",
            )
        )
        ==
        EXPECTED_DATASET_ID,
        "ARTIFACT_DATASET_ID_MISMATCH",
    )

    _require(
        str(
            artifact.get(
                "dataset_sha256",
                "",
            )
        )
        ==
        EXPECTED_DATASET_SHA256,
        "ARTIFACT_DATASET_SHA256_MISMATCH",
    )

    _require(
        str(
            artifact.get(
                "manifest_sha256",
                "",
            )
        )
        ==
        EXPECTED_MANIFEST_SHA256,
        "ARTIFACT_MANIFEST_SHA256_MISMATCH",
    )

    _require(
        str(
            artifact.get(
                "feature_contract_version",
                "",
            )
        )
        ==
        EXPECTED_FEATURE_CONTRACT,
        "FEATURE_CONTRACT_MISMATCH",
    )

    _require(
        str(
            artifact.get(
                "trainer_input_contract_version",
                "",
            )
        )
        ==
        EXPECTED_TRAINER_INPUT_CONTRACT,
        "TRAINER_INPUT_CONTRACT_MISMATCH",
    )

    _require(
        str(
            artifact.get(
                "trainer_input_contract_fingerprint_sha256",
                "",
            )
        )
        ==
        EXPECTED_TRAINER_INPUT_CONTRACT_FINGERPRINT_SHA256,
        "TRAINER_INPUT_CONTRACT_FINGERPRINT_MISMATCH",
    )

    _require(
        str(
            artifact.get(
                "target_access_contract_version",
                "",
            )
        )
        ==
        EXPECTED_TARGET_ACCESS_CONTRACT,
        "TARGET_ACCESS_CONTRACT_MISMATCH",
    )

    _require(
        str(
            artifact.get(
                "target_access_contract_fingerprint_sha256",
                "",
            )
        )
        ==
        EXPECTED_TARGET_ACCESS_CONTRACT_FINGERPRINT_SHA256,
        "TARGET_ACCESS_CONTRACT_FINGERPRINT_MISMATCH",
    )

    _require(
        str(
            artifact.get(
                "train_input_fingerprint_sha256",
                "",
            )
        )
        ==
        EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256,
        "TRAIN_INPUT_FINGERPRINT_MISMATCH",
    )

    _require(
        str(
            artifact.get(
                "train_target_fingerprint_sha256",
                "",
            )
        )
        ==
        EXPECTED_TRAIN_TARGET_FINGERPRINT_SHA256,
        "ARTIFACT_TRAIN_TARGET_FINGERPRINT_MISMATCH",
    )

    target_validation = (
        _mapping(
            document,
            "train_target_batch_validation",
        )
    )

    target_columns = (
        _string_list(
            target_validation.get(
                "target_columns"
            ),
            field_name=(
                "train_target_batch_validation.target_columns"
            ),
        )
    )

    _require(
        tuple(
            target_columns
        )
        ==
        EXPECTED_TARGET_COLUMNS,
        "TRAIN_TARGET_COLUMNS_MISMATCH",
    )

    _require(
        bool(
            target_validation.get(
                "target_class_domain_confirmed",
                False,
            )
        ),
        "TARGET_CLASS_DOMAIN_NOT_CONFIRMED",
    )

    _require(
        bool(
            target_validation.get(
                "target_tradeable_domain_confirmed",
                False,
            )
        ),
        "TARGET_TRADEABLE_DOMAIN_NOT_CONFIRMED",
    )

    _require(
        bool(
            target_validation.get(
                "target_tradeable_linkage_confirmed",
                False,
            )
        ),
        "TARGET_TRADEABLE_LINKAGE_NOT_CONFIRMED",
    )

    _require(
        _required_int(
            target_validation,
            "target_tradeable_linkage_mismatch_count",
        )
        ==
        0,
        "TARGET_TRADEABLE_LINKAGE_HAS_MISMATCHES",
    )

    scientific_policy = (
        _mapping(
            document,
            "scientific_policy",
        )
    )

    _require(
        bool(
            scientific_policy.get(
                "train_feature_values_loaded",
                False,
            )
        ),
        "PRIOR_INTEGRATION_DID_NOT_LOAD_TRAIN_FEATURES",
    )

    _require(
        bool(
            scientific_policy.get(
                "train_target_values_loaded",
                False,
            )
        ),
        "PRIOR_INTEGRATION_DID_NOT_LOAD_TRAIN_TARGETS",
    )

    _require(
        not bool(
            scientific_policy.get(
                "train_feature_target_values_combined",
                True,
            )
        ),
        "PRIOR_INTEGRATION_ALREADY_COMBINED_SUPERVISED_VALUES",
    )

    _require(
        not bool(
            scientific_policy.get(
                "validation_feature_values_loaded",
                True,
            )
        ),
        "VALIDATION_FEATURE_VALUES_ALREADY_LOADED",
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
                "test_feature_values_loaded",
                True,
            )
        ),
        "TEST_FEATURE_VALUES_ALREADY_LOADED",
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
            "DESIGN_TRAIN_ONLY_SUPERVISED_BATCH_CONTRACT_"
            "WITHOUT_MODEL_FIT_OR_HOLDOUT_ACCESS"
        ),
        "TARGET_INTEGRATION_NEXT_ACTION_MISMATCH",
    )

    return document


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


def _inspect_loader_state(
) -> dict[str, Any]:

    source_text = (
        _read_text_auto(
            LOADER_SOURCE
        )
    )

    try:

        tree = ast.parse(
            source_text
        )

    except SyntaxError as exc:

        raise RuntimeError(
            (
                "PORTABLE_LOADER_AST_PARSE_FAILED:"
                f"{exc}"
            )
        ) from exc

    loader_class: ast.ClassDef | None = (
        None
    )

    dataclasses: set[str] = set()

    for node in tree.body:

        if isinstance(
            node,
            ast.ClassDef,
        ):

            dataclasses.add(
                node.name
            )

            if (
                node.name
                ==
                "Portable331TrainingInputLoader"
            ):

                loader_class = (
                    node
                )

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

    required_existing_methods = {
        "load_train_features",
        "load_train_targets",
        "load_train_supervised",
        "load_validation_features",
        "load_validation_targets",
        "load_test_features",
        "load_test_targets",
    }

    missing_methods = sorted(
        required_existing_methods
        -
        set(
            methods
        )
    )

    _require(
        not missing_methods,
        (
            "PORTABLE_LOADER_METHODS_MISSING:"
            f"{missing_methods}"
        ),
    )

    _require(
        "Portable331TrainFeatureBatch"
        in
        dataclasses,
        "TRAIN_FEATURE_BATCH_DATACLASS_MISSING",
    )

    _require(
        "Portable331TrainTargetBatch"
        in
        dataclasses,
        "TRAIN_TARGET_BATCH_DATACLASS_MISSING",
    )

    confirmed_blocked: dict[
        str,
        str
    ] = {}

    for (
        method_name,
        expected_error,
    ) in EXPECTED_BLOCKED_ACCESSORS.items():

        method = methods.get(
            method_name
        )

        if method is None:
            raise RuntimeError(
                (
                    "EXPECTED_BLOCKED_METHOD_MISSING:"
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
                "EXPECTED_FAIL_CLOSED_LITERAL_MISSING:"
                f"{method_name}:"
                f"{expected_error}"
            ),
        )

        confirmed_blocked[
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
        "train_feature_batch_dataclass_present": (
            True
        ),
        "train_target_batch_dataclass_present": (
            True
        ),
        "load_train_features_present": (
            True
        ),
        "load_train_targets_present": (
            True
        ),
        "load_train_supervised_currently_blocked": (
            True
        ),
        "validation_access_currently_blocked": (
            True
        ),
        "test_access_currently_blocked": (
            True
        ),
        "confirmed_blocked_accessors": (
            confirmed_blocked
        ),
    }


def _contract_core(
    *,
    loader_inspection: Mapping[str, Any],
) -> dict[str, Any]:

    return {
        "contract_version": (
            SUPERVISED_BATCH_CONTRACT_VERSION
        ),
        "contract_status": (
            "DESIGN_ONLY_NOT_IMPLEMENTED"
        ),
        "asset": (
            "XAUUSD"
        ),
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
            "target_access_contract": (
                EXPECTED_TARGET_ACCESS_CONTRACT
            ),
            "target_access_contract_fingerprint_sha256": (
                EXPECTED_TARGET_ACCESS_CONTRACT_FINGERPRINT_SHA256
            ),
        },
        "frozen_train_inputs": {
            "row_count": (
                EXPECTED_TRAIN_ROWS
            ),
            "feature_count": (
                EXPECTED_FEATURE_COUNT
            ),
            "train_input_fingerprint_sha256": (
                EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256
            ),
            "train_target_fingerprint_sha256": (
                EXPECTED_TRAIN_TARGET_FINGERPRINT_SHA256
            ),
            "target_columns": list(
                EXPECTED_TARGET_COLUMNS
            ),
            "target_class_allowed_values": list(
                EXPECTED_TARGET_CLASS_VALUES
            ),
            "target_tradeable_allowed_values": list(
                EXPECTED_TARGET_TRADEABLE_VALUES
            ),
        },
        "supervised_batch_contract": {
            "new_result_dataclass": (
                "Portable331TrainSupervisedBatch"
            ),
            "method_to_implement": (
                "Portable331TrainingInputLoader.load_train_supervised"
            ),
            "feature_source": (
                "load_train_features"
            ),
            "target_source": (
                "load_train_targets"
            ),
            "additional_dataset_read_allowed": (
                False
            ),
            "decision_time_alignment_required": (
                True
            ),
            "row_count_alignment_required": (
                True
            ),
            "dataset_identity_alignment_required": (
                True
            ),
            "manifest_identity_alignment_required": (
                True
            ),
            "trainer_input_contract_alignment_required": (
                True
            ),
            "feature_fingerprint_alignment_required": (
                True
            ),
            "target_fingerprint_alignment_required": (
                True
            ),
            "X_shape": [
                EXPECTED_TRAIN_ROWS,
                EXPECTED_FEATURE_COUNT,
            ],
            "X_dtype": (
                "float64"
            ),
            "target_class_shape": [
                EXPECTED_TRAIN_ROWS
            ],
            "target_class_dtype": (
                "int8"
            ),
            "target_tradeable_shape": [
                EXPECTED_TRAIN_ROWS
            ],
            "target_tradeable_dtype": (
                "int8"
            ),
            "all_arrays_read_only_required": (
                True
            ),
            "target_tradeable_linkage_revalidation_required": (
                True
            ),
            "target_recomputation_allowed": (
                False
            ),
            "target_distribution_reporting_allowed": (
                False
            ),
            "metrics_allowed": (
                False
            ),
        },
        "training_boundary": {
            "model_architecture_selected": (
                False
            ),
            "scaler_fit_allowed": (
                False
            ),
            "model_fit_allowed": (
                False
            ),
            "hyperparameter_selection_allowed": (
                False
            ),
            "threshold_selection_allowed": (
                False
            ),
            "calibration_fit_allowed": (
                False
            ),
            "model_artifact_write_allowed": (
                False
            ),
        },
        "holdout_boundary": {
            "validation_feature_access_allowed": (
                False
            ),
            "validation_target_access_allowed": (
                False
            ),
            "test_feature_access_allowed": (
                False
            ),
            "test_target_access_allowed": (
                False
            ),
            "validation_metrics_allowed": (
                False
            ),
            "test_metrics_allowed": (
                False
            ),
            "test_remains_final_holdout": (
                True
            ),
        },
        "current_loader_state": (
            dict(
                loader_inspection
            )
        ),
        "authorization": {
            "supervised_batch_loader_implementation_authorized": (
                False
            ),
            "model_training_authorized": (
                False
            ),
            "validation_access_authorized": (
                False
            ),
            "test_access_authorized": (
                False
            ),
            "feature_contract_change_authorized": (
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
        _validate_target_integration()
    )

    loader_inspection = (
        _inspect_loader_state()
    )

    contract_core = (
        _contract_core(
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
            "DESIGN_TRAIN_ONLY_SUPERVISED_BATCH_CONTRACT_"
            "WITHOUT_MODEL_FIT_OR_HOLDOUT_ACCESS"
        ),
        "TARGET_INTEGRATION_DID_NOT_AUTHORIZE_SUPERVISED_BATCH_DESIGN",
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_PORTABLE_331_TRAIN_SUPERVISED_BATCH_CONTRACT_DESIGN"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "research_scope": (
            "DESIGN_ONLY_TRAIN_SUPERVISED_BATCH_COMBINATION_"
            "WITHOUT_MODEL_FIT_METRICS_OR_HOLDOUT_ACCESS"
        ),
        "contract": (
            contract_core
        ),
        "contract_fingerprint": {
            "version": (
                "XAUUSD_PORTABLE_331_TRAIN_SUPERVISED_BATCH_"
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
                "XAUUSD_PORTABLE_331_TRAIN_SUPERVISED_BATCH_CONTRACT_DESIGN_CONFIRMED"
            ),
            "reason": (
                "THE_FROZEN_TRAIN_FEATURE_AND_TARGET_BATCHES_ARE_"
                "NOW_PINNED_FOR_ALIGNMENT_ONLY_COMBINATION_WITHOUT_"
                "ANY_ADDITIONAL_DATA_READ_MODEL_FIT_OR_HOLDOUT_ACCESS"
            ),
            "supervised_batch_contract_version": (
                SUPERVISED_BATCH_CONTRACT_VERSION
            ),
            "supervised_batch_contract_fingerprint_sha256": (
                contract_fingerprint
            ),
            "train_rows": (
                EXPECTED_TRAIN_ROWS
            ),
            "feature_count": (
                EXPECTED_FEATURE_COUNT
            ),
            "train_input_fingerprint_sha256": (
                EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256
            ),
            "train_target_fingerprint_sha256": (
                EXPECTED_TRAIN_TARGET_FINGERPRINT_SHA256
            ),
            "supervised_batch_loader_implementation_authorized_next": (
                True
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
            "validation_access_authorized": (
                False
            ),
            "test_access_authorized": (
                False
            ),
            "feature_contract_change_authorized": (
                False
            ),
            "target_contract_change_authorized": (
                False
            ),
            "live_authorized": (
                False
            ),
            "next_action": (
                "IMPLEMENT_TRAIN_SUPERVISED_BATCH_ALIGNMENT_ONLY_"
                "WITHOUT_MODEL_FIT_OR_HOLDOUT_ACCESS"
            ),
        },
        "scientific_policy": {
            "target_loader_integration_evidence_loaded": (
                True
            ),
            "loader_source_read_only": (
                True
            ),
            "portable_dataset_loaded": (
                False
            ),
            "portable_dataset_rows_loaded": (
                False
            ),
            "portable_manifest_loaded": (
                False
            ),
            "train_feature_values_loaded": (
                False
            ),
            "train_target_values_loaded": (
                False
            ),
            "train_supervised_values_combined": (
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
            "loader_modified": (
                False
            ),
            "feature_contract_changed": (
                False
            ),
            "target_contract_changed": (
                False
            ),
            "mt5_used": (
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
                "IMPLEMENT_TRAIN_SUPERVISED_BATCH_ALIGNMENT_ONLY_"
                "WITHOUT_MODEL_FIT_OR_HOLDOUT_ACCESS"
            ),
            "method_to_change": (
                "Portable331TrainingInputLoader.load_train_supervised"
            ),
            "new_result_dataclass": (
                "Portable331TrainSupervisedBatch"
            ),
            "additional_dataset_read_allowed": (
                False
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
            "feature_contract_change_required": (
                False
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
                        "XAUUSD_PORTABLE_331_TRAIN_SUPERVISED_"
                        "BATCH_CONTRACT_DESIGN_FAILED"
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