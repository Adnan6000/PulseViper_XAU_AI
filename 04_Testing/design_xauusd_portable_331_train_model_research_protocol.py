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
    "XAUUSD_PORTABLE_331_TRAIN_MODEL_RESEARCH_PROTOCOL_DESIGN_V1"
)

RESEARCH_PROTOCOL_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_MODEL_RESEARCH_PROTOCOL_V1"
)


SUPERVISED_INTEGRATION_JSON = (
    ROOT_DIR
    /
    "04_Testing/evidence/research/portable_331/train/xauusd_portable_331_train_supervised_batch_integration.json"
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


EXPECTED_SUPERVISED_INTEGRATION_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_SUPERVISED_BATCH_INTEGRATION_V1"
)

EXPECTED_SUPERVISED_INTEGRATION_STATUS = (
    "XAUUSD_PORTABLE_331_TRAIN_SUPERVISED_BATCH_INTEGRATION_CONFIRMED"
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


EXPECTED_SUPERVISED_BATCH_CONTRACT = (
    "XAUUSD_PORTABLE_331_TRAIN_SUPERVISED_BATCH_V1"
)

EXPECTED_SUPERVISED_BATCH_CONTRACT_FINGERPRINT_SHA256 = (
    "1e7bd0751234282d4081ef87783de8633aac815a2f6aa13010fbb5a06156aec4"
)


EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256 = (
    "9ffb72759499cfc202e88cfdbd61b42cee5b5c7cbb7db5870470453caa5ed2c5"
)

EXPECTED_TRAIN_TARGET_FINGERPRINT_SHA256 = (
    "bc063a790e70cdbc931b2170ccfef883634b40ee7336a529a32bda0eaf0babe3"
)


EXPECTED_TRAIN_ROWS = 69966
EXPECTED_FEATURE_COUNT = 331

TARGET_HORIZON_BARS = 12

WALK_FORWARD_FOLD_COUNT = 4
INITIAL_TRAIN_FRACTION = 0.40


EXPECTED_TARGET_CLASS_VALUES = (
    -1,
    0,
    1,
)

EXPECTED_TARGET_TRADEABLE_VALUES = (
    0,
    1,
)


EXPECTED_HOLDOUT_BLOCKED_ACCESSORS = {
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
        document_raw: Any = json.loads(
            text
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


def _validate_supervised_integration(
) -> Mapping[str, Any]:

    document = (
        _load_json_object(
            SUPERVISED_INTEGRATION_JSON
        )
    )

    _require(
        bool(
            document.get(
                "valid",
                False,
            )
        ),
        "SUPERVISED_INTEGRATION_INVALID",
    )

    _require(
        str(
            document.get(
                "analysis_version",
                "",
            )
        )
        ==
        EXPECTED_SUPERVISED_INTEGRATION_VERSION,
        "SUPERVISED_INTEGRATION_VERSION_MISMATCH",
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
        EXPECTED_SUPERVISED_INTEGRATION_STATUS,
        "SUPERVISED_INTEGRATION_STATUS_MISMATCH",
    )

    _require(
        _required_int(
            decision,
            "train_rows",
        )
        ==
        EXPECTED_TRAIN_ROWS,
        "SUPERVISED_TRAIN_ROWS_MISMATCH",
    )

    _require(
        _required_int(
            decision,
            "feature_count",
        )
        ==
        EXPECTED_FEATURE_COUNT,
        "SUPERVISED_FEATURE_COUNT_MISMATCH",
    )

    _require(
        bool(
            decision.get(
                "train_supervised_batch_confirmed",
                False,
            )
        ),
        "TRAIN_SUPERVISED_BATCH_NOT_CONFIRMED",
    )

    _require(
        not bool(
            decision.get(
                "additional_dataset_read_confirmed",
                True,
            )
        ),
        "UNEXPECTED_ADDITIONAL_DATASET_READ",
    )

    _require(
        not bool(
            decision.get(
                "model_training_authorized",
                True,
            )
        ),
        "MODEL_TRAINING_ALREADY_AUTHORIZED",
    )

    _require(
        not bool(
            decision.get(
                "validation_access_authorized",
                True,
            )
        ),
        "VALIDATION_ACCESS_ALREADY_AUTHORIZED",
    )

    _require(
        not bool(
            decision.get(
                "test_access_authorized",
                True,
            )
        ),
        "TEST_ACCESS_ALREADY_AUTHORIZED",
    )

    _require(
        str(
            decision.get(
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
        "DATASET_ID_MISMATCH",
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
        "DATASET_SHA256_MISMATCH",
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
        "MANIFEST_SHA256_MISMATCH",
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
                "supervised_batch_contract_version",
                "",
            )
        )
        ==
        EXPECTED_SUPERVISED_BATCH_CONTRACT,
        "SUPERVISED_BATCH_CONTRACT_MISMATCH",
    )

    _require(
        str(
            artifact.get(
                "supervised_batch_contract_fingerprint_sha256",
                "",
            )
        )
        ==
        EXPECTED_SUPERVISED_BATCH_CONTRACT_FINGERPRINT_SHA256,
        "SUPERVISED_BATCH_CONTRACT_FINGERPRINT_MISMATCH",
    )

    batch_validation = (
        _mapping(
            document,
            "train_supervised_batch_validation",
        )
    )

    _require(
        _required_int(
            batch_validation,
            "row_count",
        )
        ==
        EXPECTED_TRAIN_ROWS,
        "SUPERVISED_BATCH_ROW_COUNT_MISMATCH",
    )

    _require(
        _required_int(
            batch_validation,
            "feature_count",
        )
        ==
        EXPECTED_FEATURE_COUNT,
        "SUPERVISED_BATCH_FEATURE_COUNT_MISMATCH",
    )

    _require(
        _required_int(
            batch_validation,
            "X_nonfinite_count",
        )
        ==
        0,
        "SUPERVISED_BATCH_HAS_NONFINITE_FEATURES",
    )

    _require(
        bool(
            batch_validation.get(
                "feature_target_decision_time_alignment",
                False,
            )
        ),
        "SUPERVISED_DECISION_TIME_ALIGNMENT_NOT_CONFIRMED",
    )

    _require(
        bool(
            batch_validation.get(
                "target_tradeable_linkage_confirmed",
                False,
            )
        ),
        "SUPERVISED_TARGET_LINKAGE_NOT_CONFIRMED",
    )

    _require(
        _required_int(
            batch_validation,
            "target_tradeable_linkage_mismatch_count",
        )
        ==
        0,
        "SUPERVISED_TARGET_LINKAGE_HAS_MISMATCHES",
    )

    _require(
        bool(
            batch_validation.get(
                "arrays_read_only",
                False,
            )
        ),
        "SUPERVISED_ARRAYS_NOT_READ_ONLY",
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
                "validation_feature_values_loaded",
                True,
            )
        ),
        "VALIDATION_FEATURES_ALREADY_LOADED",
    )

    _require(
        not bool(
            scientific_policy.get(
                "validation_target_values_loaded",
                True,
            )
        ),
        "VALIDATION_TARGETS_ALREADY_LOADED",
    )

    _require(
        not bool(
            scientific_policy.get(
                "test_feature_values_loaded",
                True,
            )
        ),
        "TEST_FEATURES_ALREADY_LOADED",
    )

    _require(
        not bool(
            scientific_policy.get(
                "test_target_values_loaded",
                True,
            )
        ),
        "TEST_TARGETS_ALREADY_LOADED",
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

    _require(
        not bool(
            scientific_policy.get(
                "scaler_fit",
                True,
            )
        ),
        "SCALER_ALREADY_FIT",
    )

    _require(
        str(
            decision.get(
                "next_action",
                "",
            )
        )
        ==
        (
            "DESIGN_TRAIN_ONLY_MODEL_RESEARCH_PROTOCOL_"
            "WITH_WALK_FORWARD_SELECTION_AND_NO_HOLDOUT_ACCESS"
        ),
        "SUPERVISED_INTEGRATION_NEXT_ACTION_MISMATCH",
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


def _inspect_loader_boundary(
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
                "LOADER_AST_PARSE_FAILED:"
                f"{exc}"
            )
        ) from exc

    loader_class: ast.ClassDef | None = None

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
            loader_class = node
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
            ] = node

    supervised_method = methods.get(
        "load_train_supervised"
    )

    if supervised_method is None:
        raise RuntimeError(
            "LOAD_TRAIN_SUPERVISED_METHOD_MISSING"
        )

    holdout_state: dict[str, str] = {}

    for (
        method_name,
        expected_literal,
    ) in EXPECTED_HOLDOUT_BLOCKED_ACCESSORS.items():

        method = methods.get(
            method_name
        )

        if method is None:
            raise RuntimeError(
                (
                    "HOLDOUT_ACCESSOR_MISSING:"
                    f"{method_name}"
                )
            )

        literals = (
            _method_string_literals(
                method
            )
        )

        _require(
            expected_literal
            in
            literals,
            (
                "HOLDOUT_FAIL_CLOSED_LITERAL_MISSING:"
                f"{method_name}:"
                f"{expected_literal}"
            ),
        )

        holdout_state[
            method_name
        ] = (
            expected_literal
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
        "loader_source_sha256": (
            source_sha256
        ),
        "load_train_supervised_present": (
            True
        ),
        "holdout_access_currently_blocked": (
            True
        ),
        "confirmed_holdout_accessors": (
            holdout_state
        ),
    }


def _build_walk_forward_folds(
) -> list[dict[str, int]]:

    initial_validation_start = int(
        EXPECTED_TRAIN_ROWS
        *
        INITIAL_TRAIN_FRACTION
    )

    remaining_rows = (
        EXPECTED_TRAIN_ROWS
        -
        initial_validation_start
    )

    _require(
        remaining_rows
        %
        WALK_FORWARD_FOLD_COUNT
        ==
        0,
        (
            "WALK_FORWARD_REMAINDER_NOT_ZERO:"
            f"{remaining_rows}"
        ),
    )

    validation_rows = (
        remaining_rows
        //
        WALK_FORWARD_FOLD_COUNT
    )

    _require(
        validation_rows
        >
        TARGET_HORIZON_BARS,
        "WALK_FORWARD_VALIDATION_BLOCK_TOO_SMALL",
    )

    folds: list[
        dict[str, int]
    ] = []

    for fold_index in range(
        WALK_FORWARD_FOLD_COUNT
    ):

        validation_start = (
            initial_validation_start
            +
            (
                fold_index
                *
                validation_rows
            )
        )

        validation_end = (
            validation_start
            +
            validation_rows
        )

        train_start = 0

        train_end = (
            validation_start
            -
            TARGET_HORIZON_BARS
        )

        purge_start = train_end
        purge_end = validation_start

        _require(
            train_end
            >
            train_start,
            (
                "WALK_FORWARD_TRAIN_BLOCK_EMPTY:"
                f"{fold_index + 1}"
            ),
        )

        _require(
            (
                purge_end
                -
                purge_start
            )
            ==
            TARGET_HORIZON_BARS,
            (
                "WALK_FORWARD_PURGE_LENGTH_INVALID:"
                f"{fold_index + 1}"
            ),
        )

        _require(
            (
                validation_end
                -
                validation_start
            )
            ==
            validation_rows,
            (
                "WALK_FORWARD_VALIDATION_LENGTH_INVALID:"
                f"{fold_index + 1}"
            ),
        )

        folds.append(
            {
                "fold": (
                    fold_index
                    +
                    1
                ),
                "train_start_inclusive": (
                    train_start
                ),
                "train_end_exclusive": (
                    train_end
                ),
                "train_rows": (
                    train_end
                    -
                    train_start
                ),
                "purge_start_inclusive": (
                    purge_start
                ),
                "purge_end_exclusive": (
                    purge_end
                ),
                "purge_rows": (
                    TARGET_HORIZON_BARS
                ),
                "validation_start_inclusive": (
                    validation_start
                ),
                "validation_end_exclusive": (
                    validation_end
                ),
                "validation_rows": (
                    validation_rows
                ),
            }
        )

    final_fold = folds[
        -1
    ]

    _require(
        final_fold[
            "validation_end_exclusive"
        ]
        ==
        EXPECTED_TRAIN_ROWS,
        "FINAL_WALK_FORWARD_FOLD_DOES_NOT_END_AT_TRAIN_BOUNDARY",
    )

    validation_starts = [
        fold[
            "validation_start_inclusive"
        ]
        for fold
        in folds
    ]

    validation_ends = [
        fold[
            "validation_end_exclusive"
        ]
        for fold
        in folds
    ]

    for index in range(
        1,
        len(
            folds
        ),
    ):

        _require(
            validation_starts[
                index
            ]
            ==
            validation_ends[
                index
                -
                1
            ],
            (
                "WALK_FORWARD_VALIDATION_BLOCK_GAP_OR_OVERLAP:"
                f"{index + 1}"
            ),
        )

    return folds


def _build_contract(
    *,
    loader_boundary: Mapping[str, Any],
    folds: list[dict[str, int]],
) -> dict[str, Any]:

    return {
        "contract_version": (
            RESEARCH_PROTOCOL_VERSION
        ),
        "contract_status": (
            "DESIGN_ONLY_NO_MODEL_FIT"
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
            "supervised_batch_contract": (
                EXPECTED_SUPERVISED_BATCH_CONTRACT
            ),
            "supervised_batch_contract_fingerprint_sha256": (
                EXPECTED_SUPERVISED_BATCH_CONTRACT_FINGERPRINT_SHA256
            ),
        },
        "frozen_train_data": {
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
            "target_class_allowed_values": list(
                EXPECTED_TARGET_CLASS_VALUES
            ),
            "target_tradeable_allowed_values": list(
                EXPECTED_TARGET_TRADEABLE_VALUES
            ),
        },
        "walk_forward_protocol": {
            "method": (
                "EXPANDING_WINDOW_PURGED_TRAIN_ONLY"
            ),
            "fold_count": (
                WALK_FORWARD_FOLD_COUNT
            ),
            "initial_train_fraction_before_purge": (
                INITIAL_TRAIN_FRACTION
            ),
            "target_horizon_bars": (
                TARGET_HORIZON_BARS
            ),
            "purge_rows_before_each_validation": (
                TARGET_HORIZON_BARS
            ),
            "validation_block_rows": (
                folds[
                    0
                ][
                    "validation_rows"
                ]
            ),
            "folds": (
                folds
            ),
            "chronological_order_required": (
                True
            ),
            "shuffle_allowed": (
                False
            ),
            "validation_rows_are_inside_frozen_train_only": (
                True
            ),
            "portable_validation_split_access_allowed": (
                False
            ),
            "portable_test_split_access_allowed": (
                False
            ),
        },
        "candidate_selection_protocol": {
            "candidate_registry_required_before_any_fit": (
                True
            ),
            "candidate_registry_must_be_finite": (
                True
            ),
            "candidate_registry_must_be_fingerprinted": (
                True
            ),
            "candidate_registry_may_not_be_changed_after_first_fit": (
                True
            ),
            "candidate_architecture_selected_in_this_gate": (
                False
            ),
            "hyperparameters_selected_in_this_gate": (
                False
            ),
            "selection_data_scope": (
                "TRAIN_WALK_FORWARD_FOLDS_ONLY"
            ),
            "test_may_not_be_used_for_candidate_selection": (
                True
            ),
            "portable_validation_split_may_not_be_used_for_candidate_selection": (
                True
            ),
        },
        "required_fold_metrics": [
            "balanced_accuracy_3class",
            "macro_f1_3class",
            "directional_macro_f1_short_long",
            "short_precision",
            "short_recall",
            "short_f1",
            "no_trade_precision",
            "no_trade_recall",
            "no_trade_f1",
            "long_precision",
            "long_recall",
            "long_f1",
            "log_loss_3class",
            "multiclass_brier",
            "predicted_trade_coverage",
        ],
        "selection_policy": {
            "directional_robustness_priority": (
                True
            ),
            "ranking": [
                {
                    "priority": 1,
                    "metric": (
                        "worst_fold_directional_macro_f1_short_long"
                    ),
                    "direction": (
                        "MAXIMIZE"
                    ),
                },
                {
                    "priority": 2,
                    "metric": (
                        "mean_directional_macro_f1_short_long"
                    ),
                    "direction": (
                        "MAXIMIZE"
                    ),
                },
                {
                    "priority": 3,
                    "metric": (
                        "worst_fold_balanced_accuracy_3class"
                    ),
                    "direction": (
                        "MAXIMIZE"
                    ),
                },
                {
                    "priority": 4,
                    "metric": (
                        "mean_macro_f1_3class"
                    ),
                    "direction": (
                        "MAXIMIZE"
                    ),
                },
                {
                    "priority": 5,
                    "metric": (
                        "std_directional_macro_f1_short_long"
                    ),
                    "direction": (
                        "MINIMIZE"
                    ),
                },
                {
                    "priority": 6,
                    "metric": (
                        "mean_log_loss_3class"
                    ),
                    "direction": (
                        "MINIMIZE"
                    ),
                },
            ],
            "tie_breaking_is_lexicographic_in_declared_order": (
                True
            ),
            "single_pooled_metric_selection_allowed": (
                False
            ),
            "fold_metrics_must_remain_visible": (
                True
            ),
        },
        "fit_boundary": {
            "model_fit_performed_in_this_gate": (
                False
            ),
            "scaler_fit_performed_in_this_gate": (
                False
            ),
            "candidate_training_authorized_in_this_gate": (
                False
            ),
            "candidate_registry_design_authorized_next": (
                True
            ),
            "final_full_train_fit_authorized": (
                False
            ),
            "model_artifact_write_authorized": (
                False
            ),
            "calibration_fit_authorized": (
                False
            ),
            "threshold_tuning_authorized": (
                False
            ),
        },
        "holdout_boundary": {
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
            "validation_metrics_authorized": (
                False
            ),
            "test_metrics_authorized": (
                False
            ),
            "test_remains_final_holdout": (
                True
            ),
        },
        "current_loader_boundary": (
            dict(
                loader_boundary
            )
        ),
        "live_authorized": (
            False
        ),
    }


def run_design(
) -> dict[str, Any]:

    _validate_supervised_integration()

    loader_boundary = (
        _inspect_loader_boundary()
    )

    folds = (
        _build_walk_forward_folds()
    )

    contract = (
        _build_contract(
            loader_boundary=(
                loader_boundary
            ),
            folds=(
                folds
            ),
        )
    )

    contract_fingerprint = (
        _canonical_json_sha256(
            contract
        )
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_PORTABLE_331_TRAIN_MODEL_RESEARCH_PROTOCOL_DESIGN"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "research_scope": (
            "DESIGN_ONLY_TRAIN_WALK_FORWARD_MODEL_RESEARCH_"
            "PROTOCOL_WITHOUT_MODEL_FIT_OR_HOLDOUT_ACCESS"
        ),
        "contract": (
            contract
        ),
        "contract_fingerprint": {
            "version": (
                "XAUUSD_PORTABLE_331_TRAIN_MODEL_RESEARCH_"
                "PROTOCOL_FINGERPRINT_V1"
            ),
            "canonicalization": (
                "JSON_SORT_KEYS_COMPACT_UTF8_SHA256"
            ),
            "sha256": (
                contract_fingerprint
            ),
        },
        "decision": {
            "status": (
                "XAUUSD_PORTABLE_331_TRAIN_MODEL_RESEARCH_PROTOCOL_DESIGN_CONFIRMED"
            ),
            "reason": (
                "MODEL_RESEARCH_IS_RESTRICTED_TO_FOUR_PURGED_"
                "EXPANDING_WALK_FORWARD_FOLDS_INSIDE_THE_FROZEN_"
                "TRAIN_PREFIX_WITH_DIRECTIONAL_ROBUSTNESS_FIRST_"
                "SELECTION_AND_NO_PORTABLE_VALIDATION_OR_TEST_ACCESS"
            ),
            "research_protocol_version": (
                RESEARCH_PROTOCOL_VERSION
            ),
            "research_protocol_fingerprint_sha256": (
                contract_fingerprint
            ),
            "train_rows": (
                EXPECTED_TRAIN_ROWS
            ),
            "feature_count": (
                EXPECTED_FEATURE_COUNT
            ),
            "walk_forward_fold_count": (
                WALK_FORWARD_FOLD_COUNT
            ),
            "purge_rows": (
                TARGET_HORIZON_BARS
            ),
            "candidate_registry_design_authorized_next": (
                True
            ),
            "candidate_training_authorized": (
                False
            ),
            "model_architecture_selected": (
                False
            ),
            "model_training_authorized": (
                False
            ),
            "scaler_fit_authorized": (
                False
            ),
            "validation_access_authorized": (
                False
            ),
            "test_access_authorized": (
                False
            ),
            "live_authorized": (
                False
            ),
            "next_action": (
                "DESIGN_FIXED_FINITE_TRAIN_ONLY_MODEL_CANDIDATE_"
                "REGISTRY_BEFORE_ANY_MODEL_FIT"
            ),
        },
        "scientific_policy": {
            "supervised_integration_evidence_loaded": (
                True
            ),
            "loader_source_read_only": (
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
            "metrics_computed": (
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
                "DESIGN_FIXED_FINITE_TRAIN_ONLY_MODEL_CANDIDATE_"
                "REGISTRY_BEFORE_ANY_MODEL_FIT"
            ),
            "candidate_registry_must_be_frozen_before_fit": (
                True
            ),
            "candidate_training_not_authorized_yet": (
                True
            ),
            "portable_validation_access_remains_blocked": (
                True
            ),
            "portable_test_access_remains_blocked": (
                True
            ),
            "final_model_fit_not_authorized": (
                True
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
                        "XAUUSD_PORTABLE_331_TRAIN_MODEL_"
                        "RESEARCH_PROTOCOL_DESIGN_FAILED"
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