from __future__ import annotations

import ast
import hashlib
import importlib
import json
import math
import os
import sys

from pathlib import Path
from typing import Any, Mapping, Sequence


def _find_repo_root(start: Path) -> Path:
    resolved = start.resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "02_AI").is_dir():
            return candidate
    return resolved.parents[4]

ROOT_DIR = _find_repo_root(Path(__file__))


if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_TRAINER_INPUT_CONTRACT_DESIGN_V1"
)

TRAINER_INPUT_CONTRACT_VERSION = (
    "XAUUSD_PORTABLE_331_RESEARCH_TRAINER_INPUT_V1"
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


READINESS_JSON = (
    ROOT_DIR
    /
    "04_Testing/evidence/research/portable_331/train/xauusd_portable_331_train_input_readiness.json"
)

V4_TRAINER_SOURCE = (
    ROOT_DIR
    /
    "02_AI"
    /
    "Models"
    /
    "xauusd_hierarchical_model_v4_trainer.py"
)


EXPECTED_READINESS_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_INPUT_READINESS_AUDIT_V2"
)

EXPECTED_READINESS_STATUS = (
    "XAUUSD_PORTABLE_331_TRAIN_MODEL_INPUT_READINESS_CONFIRMED"
)


SOURCE_CONTRACT = (
    "XAUUSD_MTF_TRAINING_V3"
)

PORTABLE_FEATURE_CONTRACT = (
    "XAUUSD_MTF_PORTABLE_FEATURE_V1"
)


EXPECTED_PORTABLE_DATASET_ID = (
    "portable_cff75b0686383a3ab6f8352b"
)

EXPECTED_PORTABLE_DATASET_SHA256 = (
    "cff75b0686383a3ab6f8352bfcdcd55308b99b7a4c6edbf7d2e7215f6f33dd07"
)

EXPECTED_PORTABLE_MANIFEST_SHA256 = (
    "1b8e3599b227c9cbbc6b12f8ab0e275ca4deb4a65839fb626ca90720d59512dc"
)


EXPECTED_PORTABLE_FEATURE_COUNT = 331

EXPECTED_TOTAL_ROWS = 99945

EXPECTED_TRAIN_ROWS = 69966

EXPECTED_VALIDATION_ROWS = 14983

EXPECTED_TEST_ROWS = 14996


EXPECTED_FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256 = (
    "9ffb72759499cfc202e88cfdbd61b42cee5b5c7cbb7db5870470453caa5ed2c5"
)

EXPECTED_FEATURE_CONTRACT_DESIGN_FINGERPRINT_SHA256 = (
    "de389b1daa02b2d864490aa41776494baea4f9e42dbf2146c2c44b9c2660ff40"
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


REQUIRED_MODEL_TARGET_COLUMNS = (
    "target_class",
    "target_tradeable",
)


DROPPED_MODEL_FEATURES = (
    "m5_spread_points",
    "m5_tick_volume_log1p",
)

RETAINED_RELATIVE_VOLUME_FEATURE = (
    "m5_tick_volume_ratio20"
)


FLOAT64_SERIALIZATION_MAX_ABS_DIFFERENCE = (
    2.0e-15
)

FLOAT64_SERIALIZATION_MAX_SCALED_EPSILON_UNITS = (
    8.0
)


V4_REQUIRED_TRAIN_CALLS = {
    "self._load_and_validate_v3_manifest",
    "self.load_training_frame",
    "self._validate_frozen_target_frame",
    "stage_a_scaler.fit_transform",
    "stage_b_scaler.fit_transform",
    "stage_a_model.fit",
    "stage_b_model.fit",
    "self._evaluate_split",
    "self._write_immutable",
}


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


def _required_int_mapping_value(
    mapping: Mapping[str, Any],
    key: str,
) -> int:

    if key not in mapping:
        raise RuntimeError(
            (
                "REQUIRED_INTEGER_MAPPING_VALUE_MISSING:"
                f"{key}"
            )
        )

    value = mapping[
        key
    ]

    if value is None:
        raise RuntimeError(
            (
                "REQUIRED_INTEGER_MAPPING_VALUE_NONE:"
                f"{key}"
            )
        )

    if isinstance(
        value,
        bool,
    ):
        raise RuntimeError(
            (
                "REQUIRED_INTEGER_MAPPING_VALUE_BOOLEAN:"
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
                "REQUIRED_INTEGER_MAPPING_VALUE_INVALID:"
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


def _feature_columns_sha256(
    feature_columns: Sequence[str],
) -> str:

    payload = json.dumps(
        [
            str(
                feature
            )
            for feature
            in feature_columns
        ],
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


def _search_roots(
) -> list[Path]:

    roots: list[Path] = []

    preferred = (
        ROOT_DIR
        /
        "03_Data"
    )

    if preferred.is_dir():
        roots.append(
            preferred
        )

    roots.append(
        ROOT_DIR
    )

    result: list[Path] = []

    seen: set[Path] = set()

    for root in roots:

        resolved = (
            root.resolve()
        )

        if resolved in seen:
            continue

        seen.add(
            resolved
        )

        result.append(
            root
        )

    return result


def _discover_portable_artifact(
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

    seen: set[Path] = set()

    for root in (
        _search_roots()
    ):

        for manifest_path in (
            _manifest_files(
                root
            )
        ):

            resolved_manifest = (
                manifest_path.resolve()
            )

            if resolved_manifest in seen:
                continue

            seen.add(
                resolved_manifest
            )

            try:

                observed_manifest_sha256 = (
                    PortableTrainingFeatureProjector
                    ._sha256_file(
                        manifest_path
                    )
                )

            except OSError:
                continue

            if (
                observed_manifest_sha256
                !=
                EXPECTED_PORTABLE_MANIFEST_SHA256
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
                EXPECTED_PORTABLE_DATASET_ID
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
                EXPECTED_PORTABLE_DATASET_SHA256
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
                PORTABLE_FEATURE_CONTRACT
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

                observed_dataset_sha256 = (
                    PortableTrainingFeatureProjector
                    ._sha256_file(
                        dataset_path
                    )
                )

            except OSError:
                continue

            if (
                observed_dataset_sha256
                !=
                EXPECTED_PORTABLE_DATASET_SHA256
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
            "PORTABLE_ARTIFACT_DISCOVERY_COUNT_INVALID:"
            f"{len(candidates)}"
        ),
    )

    return candidates[
        0
    ]


def _validate_readiness(
) -> Mapping[str, Any]:

    document = (
        PortableTrainingFeatureProjector
        ._load_json(
            READINESS_JSON
        )
    )

    _require(
        bool(
            document.get(
                "valid",
                False,
            )
        ),
        "READINESS_AUDIT_INVALID",
    )

    _require(
        str(
            document.get(
                "analysis_version",
                "",
            )
        )
        ==
        EXPECTED_READINESS_VERSION,
        "READINESS_AUDIT_VERSION_MISMATCH",
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
        EXPECTED_READINESS_STATUS,
        "READINESS_STATUS_MISMATCH",
    )

    _require(
        int(
            decision.get(
                "portable_feature_count",
                -1,
            )
        )
        ==
        EXPECTED_PORTABLE_FEATURE_COUNT,
        "READINESS_FEATURE_COUNT_MISMATCH",
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
        "READINESS_TRAIN_ROW_COUNT_MISMATCH",
    )

    _require(
        bool(
            decision.get(
                "train_prefix_only_feature_loading_confirmed",
                False,
            )
        ),
        "TRAIN_PREFIX_ONLY_LOADING_NOT_CONFIRMED",
    )

    _require(
        bool(
            decision.get(
                "float64_serialization_equivalence_confirmed",
                False,
            )
        ),
        "FLOAT64_SERIALIZATION_EQUIVALENCE_NOT_CONFIRMED",
    )

    _require(
        bool(
            decision.get(
                "train_inputs_all_finite",
                False,
            )
        ),
        "TRAIN_INPUTS_NOT_ALL_FINITE",
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
                "validation_evaluation_authorized",
                True,
            )
        ),
        "VALIDATION_UNEXPECTEDLY_AUTHORIZED",
    )

    _require(
        not bool(
            decision.get(
                "test_evaluation_authorized",
                True,
            )
        ),
        "TEST_UNEXPECTEDLY_AUTHORIZED",
    )

    portable_artifact = (
        _mapping(
            document,
            "portable_artifact",
        )
    )

    _require(
        str(
            portable_artifact.get(
                "dataset_id",
                "",
            )
        )
        ==
        EXPECTED_PORTABLE_DATASET_ID,
        "READINESS_DATASET_ID_MISMATCH",
    )

    _require(
        str(
            portable_artifact.get(
                "dataset_sha256",
                "",
            )
        )
        ==
        EXPECTED_PORTABLE_DATASET_SHA256,
        "READINESS_DATASET_SHA256_MISMATCH",
    )

    _require(
        str(
            portable_artifact.get(
                "manifest_sha256",
                "",
            )
        )
        ==
        EXPECTED_PORTABLE_MANIFEST_SHA256,
        "READINESS_MANIFEST_SHA256_MISMATCH",
    )

    _require(
        str(
            portable_artifact.get(
                "feature_columns_sha256",
                "",
            )
        )
        ==
        EXPECTED_FEATURE_COLUMNS_SHA256,
        "READINESS_FEATURE_COLUMNS_SHA256_MISMATCH",
    )

    _require(
        str(
            portable_artifact.get(
                "contract_design_fingerprint_sha256",
                "",
            )
        )
        ==
        EXPECTED_FEATURE_CONTRACT_DESIGN_FINGERPRINT_SHA256,
        "READINESS_FEATURE_CONTRACT_FINGERPRINT_MISMATCH",
    )

    train_validation = (
        _mapping(
            document,
            "train_model_input_validation",
        )
    )

    _require(
        int(
            train_validation.get(
                "outside_serialization_envelope_feature_count",
                -1,
            )
        )
        ==
        0,
        "READINESS_SERIALIZATION_ENVELOPE_FAILURE",
    )

    _require(
        int(
            train_validation.get(
                "source_nonfinite_feature_value_count",
                -1,
            )
        )
        ==
        0,
        "READINESS_SOURCE_NONFINITE_VALUES",
    )

    _require(
        int(
            train_validation.get(
                "portable_nonfinite_feature_value_count",
                -1,
            )
        )
        ==
        0,
        "READINESS_PORTABLE_NONFINITE_VALUES",
    )

    _require(
        str(
            train_validation.get(
                "portable_train_input_fingerprint_sha256",
                "",
            )
        )
        ==
        EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256,
        "READINESS_TRAIN_INPUT_FINGERPRINT_MISMATCH",
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
        "READINESS_VALIDATION_FEATURE_VALUES_WERE_LOADED",
    )

    _require(
        not bool(
            scientific_policy.get(
                "test_feature_values_loaded",
                True,
            )
        ),
        "READINESS_TEST_FEATURE_VALUES_WERE_LOADED",
    )

    _require(
        not bool(
            scientific_policy.get(
                "target_columns_loaded",
                True,
            )
        ),
        "READINESS_TARGET_COLUMNS_WERE_LOADED",
    )

    _require(
        not bool(
            scientific_policy.get(
                "model_trained",
                True,
            )
        ),
        "READINESS_MODEL_WAS_TRAINED",
    )

    return document


def _validate_portable_manifest(
    manifest: Mapping[str, Any],
) -> dict[str, Any]:

    _require(
        str(
            manifest.get(
                "manifest_version",
                "",
            )
        )
        ==
        PortableTrainingFeatureProjector.MANIFEST_VERSION,
        "PORTABLE_MANIFEST_VERSION_MISMATCH",
    )

    _require(
        str(
            manifest.get(
                "dataset_id",
                "",
            )
        )
        ==
        EXPECTED_PORTABLE_DATASET_ID,
        "PORTABLE_MANIFEST_DATASET_ID_MISMATCH",
    )

    _require(
        str(
            manifest.get(
                "dataset_sha256",
                "",
            )
        )
        ==
        EXPECTED_PORTABLE_DATASET_SHA256,
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
        PORTABLE_FEATURE_CONTRACT,
        "PORTABLE_MANIFEST_CONTRACT_MISMATCH",
    )

    _require(
        int(
            manifest.get(
                "row_count",
                -1,
            )
        )
        ==
        EXPECTED_TOTAL_ROWS,
        "PORTABLE_MANIFEST_ROW_COUNT_MISMATCH",
    )

    _require(
        int(
            manifest.get(
                "feature_count",
                -1,
            )
        )
        ==
        EXPECTED_PORTABLE_FEATURE_COUNT,
        "PORTABLE_MANIFEST_FEATURE_COUNT_MISMATCH",
    )

    _require(
        not bool(
            manifest.get(
                "live_authorized",
                True,
            )
        ),
        "PORTABLE_MANIFEST_UNEXPECTEDLY_LIVE_AUTHORIZED",
    )

    feature_columns = (
        _string_list(
            manifest.get(
                "feature_columns"
            ),
            field_name=(
                "feature_columns"
            ),
        )
    )

    _require(
        len(
            feature_columns
        )
        ==
        EXPECTED_PORTABLE_FEATURE_COUNT,
        "PORTABLE_FEATURE_LIST_COUNT_MISMATCH",
    )

    _require(
        _feature_columns_sha256(
            feature_columns
        )
        ==
        EXPECTED_FEATURE_COLUMNS_SHA256,
        "PORTABLE_FEATURE_LIST_SHA256_MISMATCH",
    )

    for feature in (
        DROPPED_MODEL_FEATURES
    ):

        _require(
            feature
            not in
            feature_columns,
            (
                "DROPPED_MODEL_FEATURE_PRESENT:"
                f"{feature}"
            ),
        )

    _require(
        RETAINED_RELATIVE_VOLUME_FEATURE
        in
        feature_columns,
        "RETAINED_RELATIVE_VOLUME_FEATURE_MISSING",
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
        REQUIRED_MODEL_TARGET_COLUMNS
    ):

        _require(
            target_column
            in
            target_columns,
            (
                "REQUIRED_MODEL_TARGET_COLUMN_MISSING:"
                f"{target_column}"
            ),
        )

    target_class_mapping = (
        _mapping(
            manifest,
            "target_class_mapping",
        )
    )

    normalized_mapping: dict[str, int] = {}

    for name in (
        EXPECTED_TARGET_CLASS_MAPPING
    ):

        normalized_mapping[
            name
        ] = (
            _required_int_mapping_value(
                target_class_mapping,
                name,
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

    target_label_contract = (
        _mapping(
            manifest,
            "target_label_contract",
        )
    )

    target_name = str(
        target_label_contract.get(
            "name",
            "",
        )
    )

    _require(
        target_name
        ==
        EXPECTED_TARGET_LABEL_CONTRACT,
        (
            "TARGET_LABEL_CONTRACT_MISMATCH:"
            f"{target_name}"
        ),
    )

    profit_atr = float(
        target_label_contract.get(
            "profit_atr",
            float(
                "nan"
            ),
        )
    )

    max_adverse_atr = float(
        target_label_contract.get(
            "max_adverse_atr",
            float(
                "nan"
            ),
        )
    )

    _require(
        math.isfinite(
            profit_atr
        )
        and
        profit_atr
        ==
        EXPECTED_TARGET_PROFIT_ATR,
        (
            "TARGET_PROFIT_ATR_MISMATCH:"
            f"{profit_atr}"
        ),
    )

    _require(
        math.isfinite(
            max_adverse_atr
        )
        and
        max_adverse_atr
        ==
        EXPECTED_TARGET_MAX_ADVERSE_ATR,
        (
            "TARGET_MAX_ADVERSE_ATR_MISMATCH:"
            f"{max_adverse_atr}"
        ),
    )

    portable_contract = (
        _mapping(
            manifest,
            "portable_feature_contract",
        )
    )

    design_fingerprint = (
        _mapping(
            portable_contract,
            "contract_design_fingerprint",
        )
    )

    _require(
        str(
            design_fingerprint.get(
                "sha256",
                "",
            )
        )
        ==
        EXPECTED_FEATURE_CONTRACT_DESIGN_FINGERPRINT_SHA256,
        "PORTABLE_FEATURE_DESIGN_FINGERPRINT_MISMATCH",
    )

    target_metadata = {
        "target_columns": (
            target_columns
        ),
        "target_class_mapping": (
            normalized_mapping
        ),
        "target_label_contract": {
            "name": (
                target_name
            ),
            "profit_atr": (
                profit_atr
            ),
            "max_adverse_atr": (
                max_adverse_atr
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

    return {
        "feature_columns": (
            feature_columns
        ),
        "target_columns": (
            target_columns
        ),
        "target_class_mapping": (
            normalized_mapping
        ),
        "target_label_contract": {
            "name": (
                target_name
            ),
            "profit_atr": (
                profit_atr
            ),
            "max_adverse_atr": (
                max_adverse_atr
            ),
        },
        "target_metadata_sha256": (
            _canonical_json_sha256(
                target_metadata
            )
        ),
    }


def _call_name(
    node: ast.Call,
) -> str:

    function = node.func

    if isinstance(
        function,
        ast.Name,
    ):
        return function.id

    if isinstance(
        function,
        ast.Attribute,
    ):

        parts = [
            function.attr
        ]

        current = (
            function.value
        )

        while isinstance(
            current,
            ast.Attribute,
        ):

            parts.append(
                current.attr
            )

            current = (
                current.value
            )

        if isinstance(
            current,
            ast.Name,
        ):
            parts.append(
                current.id
            )

        parts.reverse()

        return ".".join(
            parts
        )

    return type(
        function
    ).__name__


def _inspect_current_v4_trainer(
) -> dict[str, Any]:

    _require(
        V4_TRAINER_SOURCE.is_file(),
        "CURRENT_V4_TRAINER_SOURCE_NOT_FOUND",
    )

    try:

        source_text = (
            V4_TRAINER_SOURCE.read_text(
                encoding="utf-8"
            )
        )

    except UnicodeDecodeError:

        source_text = (
            V4_TRAINER_SOURCE.read_text(
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
                "CURRENT_V4_TRAINER_AST_PARSE_FAILED:"
                f"{exc}"
            )
        ) from exc

    trainer_class: (
        ast.ClassDef
        |
        None
    ) = None

    for node in (
        tree.body
    ):

        if (
            isinstance(
                node,
                ast.ClassDef,
            )
            and
            node.name
            ==
            "XAUUSDHierarchicalModelV4Trainer"
        ):

            trainer_class = (
                node
            )

            break

    if trainer_class is None:
        raise RuntimeError(
            "CURRENT_V4_TRAINER_CLASS_NOT_FOUND"
        )

    train_method: (
        ast.FunctionDef
        |
        ast.AsyncFunctionDef
        |
        None
    ) = None

    for node in (
        trainer_class.body
    ):

        if (
            isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
            and
            node.name
            ==
            "train"
        ):

            train_method = (
                node
            )

            break

    if train_method is None:
        raise RuntimeError(
            "CURRENT_V4_TRAIN_METHOD_NOT_FOUND"
        )

    arguments = [
        argument.arg
        for argument
        in train_method.args.args
    ]

    arguments.extend(
        argument.arg
        for argument
        in train_method.args.kwonlyargs
    )

    _require(
        "training_contract_version"
        in
        arguments,
        "V4_TRAIN_METHOD_CONTRACT_ARGUMENT_MISSING",
    )

    calls = {
        _call_name(
            node
        )
        for node
        in ast.walk(
            train_method
        )
        if isinstance(
            node,
            ast.Call,
        )
    }

    missing_required_calls = sorted(
        V4_REQUIRED_TRAIN_CALLS
        -
        calls
    )

    _require(
        not missing_required_calls,
        (
            "V4_EXPECTED_TRAIN_FLOW_CALLS_MISSING:"
            f"{missing_required_calls}"
        ),
    )

    v3_requirement_literal_found = bool(
        "V4_REQUIRES_XAUUSD_MTF_TRAINING_V3"
        in
        source_text
    )

    _require(
        v3_requirement_literal_found,
        "V4_EXPLICIT_V3_REQUIREMENT_NOT_FOUND",
    )

    source_sha256 = hashlib.sha256(
        source_text.encode(
            "utf-8"
        )
    ).hexdigest()

    return {
        "trainer_class": (
            "XAUUSDHierarchicalModelV4Trainer"
        ),
        "train_method_contract_argument_present": (
            True
        ),
        "explicit_v3_requirement_present": (
            True
        ),
        "observed_required_train_calls": sorted(
            V4_REQUIRED_TRAIN_CALLS
        ),
        "source_sha256": (
            source_sha256
        ),
        "direct_reuse_for_portable_contract_authorized": (
            False
        ),
        "reason": (
            "CURRENT_V4_TRAIN_PATH_IS_V3_SPECIFIC_AND_COMBINES_"
            "INPUT_LOADING_WITH_SCALER_FIT_MODEL_FIT_SPLIT_"
            "EVALUATION_AND_ARTIFACT_WRITES"
        ),
    }


def _contract_core(
    *,
    manifest_validation: Mapping[str, Any],
    trainer_inspection: Mapping[str, Any],
) -> dict[str, Any]:

    feature_columns = (
        manifest_validation.get(
            "feature_columns"
        )
    )

    if not isinstance(
        feature_columns,
        list,
    ):
        raise RuntimeError(
            "VALIDATED_FEATURE_COLUMNS_MISSING"
        )

    target_columns = (
        manifest_validation.get(
            "target_columns"
        )
    )

    if not isinstance(
        target_columns,
        list,
    ):
        raise RuntimeError(
            "VALIDATED_TARGET_COLUMNS_MISSING"
        )

    target_class_mapping = (
        manifest_validation.get(
            "target_class_mapping"
        )
    )

    if not isinstance(
        target_class_mapping,
        Mapping,
    ):
        raise RuntimeError(
            "VALIDATED_TARGET_CLASS_MAPPING_MISSING"
        )

    target_label_contract = (
        manifest_validation.get(
            "target_label_contract"
        )
    )

    if not isinstance(
        target_label_contract,
        Mapping,
    ):
        raise RuntimeError(
            "VALIDATED_TARGET_LABEL_CONTRACT_MISSING"
        )

    target_metadata_sha256 = str(
        manifest_validation.get(
            "target_metadata_sha256",
            "",
        )
    )

    _require(
        len(
            target_metadata_sha256
        )
        ==
        64,
        "TARGET_METADATA_FINGERPRINT_INVALID",
    )

    return {
        "contract_version": (
            TRAINER_INPUT_CONTRACT_VERSION
        ),
        "contract_status": (
            "DESIGN_ONLY_NOT_IMPLEMENTED"
        ),
        "asset": (
            "XAUUSD"
        ),
        "artifact_identity": {
            "dataset_id": (
                EXPECTED_PORTABLE_DATASET_ID
            ),
            "dataset_sha256": (
                EXPECTED_PORTABLE_DATASET_SHA256
            ),
            "manifest_sha256": (
                EXPECTED_PORTABLE_MANIFEST_SHA256
            ),
            "training_contract_version": (
                PORTABLE_FEATURE_CONTRACT
            ),
            "total_rows": (
                EXPECTED_TOTAL_ROWS
            ),
        },
        "feature_input_contract": {
            "feature_contract_version": (
                PORTABLE_FEATURE_CONTRACT
            ),
            "feature_count": (
                EXPECTED_PORTABLE_FEATURE_COUNT
            ),
            "feature_columns_sha256": (
                EXPECTED_FEATURE_COLUMNS_SHA256
            ),
            "train_input_fingerprint_sha256": (
                EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256
            ),
            "feature_contract_design_fingerprint_sha256": (
                EXPECTED_FEATURE_CONTRACT_DESIGN_FINGERPRINT_SHA256
            ),
            "feature_columns": (
                feature_columns
            ),
            "dropped_parent_features": list(
                DROPPED_MODEL_FEATURES
            ),
            "added_features": [],
            "retained_relative_volume_feature": (
                RETAINED_RELATIVE_VOLUME_FEATURE
            ),
            "nonfinite_values_allowed": (
                False
            ),
            "serialization_equivalence": {
                "bit_exact_required": (
                    False
                ),
                "maximum_absolute_difference": (
                    FLOAT64_SERIALIZATION_MAX_ABS_DIFFERENCE
                ),
                "maximum_scaled_epsilon_units": (
                    FLOAT64_SERIALIZATION_MAX_SCALED_EPSILON_UNITS
                ),
                "special_value_layout_must_match": (
                    True
                ),
            },
        },
        "target_input_contract": {
            "target_contract_changed": (
                False
            ),
            "target_columns": (
                target_columns
            ),
            "model_required_target_columns": list(
                REQUIRED_MODEL_TARGET_COLUMNS
            ),
            "target_class_mapping": dict(
                target_class_mapping
            ),
            "target_label_contract": dict(
                target_label_contract
            ),
            "target_metadata_sha256": (
                target_metadata_sha256
            ),
            "target_tradeable_linkage_required": (
                True
            ),
            "expected_target_tradeable_rule": (
                "TARGET_TRADEABLE_EQUALS_TARGET_CLASS_NOT_NO_TRADE"
            ),
        },
        "split_access_contract": {
            "TRAIN": {
                "row_count": (
                    EXPECTED_TRAIN_ROWS
                ),
                "role": (
                    "MODEL_FIT_ONLY_WHEN_SEPARATELY_AUTHORIZED"
                ),
                "feature_access": (
                    "EXPLICIT_TRAIN_ROWS_ONLY"
                ),
                "target_access": (
                    "EXPLICIT_TRAIN_ROWS_ONLY_WHEN_MODEL_FIT_AUTHORIZED"
                ),
            },
            "VALIDATION": {
                "row_count": (
                    EXPECTED_VALIDATION_ROWS
                ),
                "role": (
                    "MODEL_SELECTION_AND_EVALUATION_ONLY"
                ),
                "feature_access_currently_authorized": (
                    False
                ),
                "target_access_currently_authorized": (
                    False
                ),
                "must_not_be_used_for_scaler_fit": (
                    True
                ),
            },
            "TEST": {
                "row_count": (
                    EXPECTED_TEST_ROWS
                ),
                "role": (
                    "FINAL_HOLDOUT_ONLY_AFTER_CANDIDATE_FREEZE"
                ),
                "feature_access_currently_authorized": (
                    False
                ),
                "target_access_currently_authorized": (
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
                "maximum_final_evaluations_after_candidate_freeze": (
                    1
                ),
            },
        },
        "loader_contract": {
            "recommended_module": (
                "02_AI.Dataset.portable_331_training_input_loader"
            ),
            "recommended_class": (
                "Portable331TrainingInputLoader"
            ),
            "artifact_discovery": (
                "EXACT_DATASET_ID_DATASET_SHA256_AND_MANIFEST_SHA256_ONLY"
            ),
            "manifest_first_validation": (
                True
            ),
            "feature_order_from_manifest_only": (
                True
            ),
            "full_dataset_feature_loading_allowed": (
                False
            ),
            "full_dataset_target_loading_allowed": (
                False
            ),
            "full_dataset_structural_columns_allowed": [
                "dataset_split"
            ],
            "split_rows_must_be_contiguous_and_exact": (
                True
            ),
            "implicit_test_access_allowed": (
                False
            ),
            "implicit_validation_access_allowed": (
                False
            ),
            "model_architecture_selected_by_loader": (
                False
            ),
            "scaler_fit_performed_by_loader": (
                False
            ),
            "model_fit_performed_by_loader": (
                False
            ),
            "metrics_computed_by_loader": (
                False
            ),
            "model_artifacts_written_by_loader": (
                False
            ),
        },
        "model_architecture_policy": {
            "architecture_selected": (
                False
            ),
            "current_v4_trainer_direct_reuse_authorized": (
                False
            ),
            "current_v4_trainer_observation": (
                dict(
                    trainer_inspection
                )
            ),
            "reason": (
                "FEATURE_PORTABILITY_AND_INPUT_LOADING_MUST_BE_"
                "DECOUPLED_FROM_MODEL_ARCHITECTURE_SELECTION"
            ),
        },
        "authorization": {
            "trainer_input_contract_design_frozen": (
                True
            ),
            "portable_input_loader_implementation_authorized": (
                False
            ),
            "model_training_authorized": (
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
        },
    }


def run_design(
) -> dict[str, Any]:

    readiness = (
        _validate_readiness()
    )

    (
        portable_dataset_path,
        portable_manifest_path,
        portable_manifest,
    ) = (
        _discover_portable_artifact()
    )

    _require(
        (
            PortableTrainingFeatureProjector
            ._sha256_file(
                portable_dataset_path
            )
        )
        ==
        EXPECTED_PORTABLE_DATASET_SHA256,
        "PORTABLE_DATASET_HASH_CHANGED",
    )

    _require(
        (
            PortableTrainingFeatureProjector
            ._sha256_file(
                portable_manifest_path
            )
        )
        ==
        EXPECTED_PORTABLE_MANIFEST_SHA256,
        "PORTABLE_MANIFEST_HASH_CHANGED",
    )

    manifest_validation = (
        _validate_portable_manifest(
            portable_manifest
        )
    )

    trainer_inspection = (
        _inspect_current_v4_trainer()
    )

    contract_core = (
        _contract_core(
            manifest_validation=(
                manifest_validation
            ),
            trainer_inspection=(
                trainer_inspection
            ),
        )
    )

    contract_fingerprint = (
        _canonical_json_sha256(
            contract_core
        )
    )

    readiness_decision = (
        _mapping(
            readiness,
            "decision",
        )
    )

    _require(
        bool(
            readiness_decision.get(
                "trainer_input_contract_design_authorized_next",
                False,
            )
        ),
        "READINESS_DID_NOT_AUTHORIZE_TRAINER_INPUT_DESIGN",
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_PORTABLE_331_TRAINER_INPUT_CONTRACT_DESIGN"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "research_scope": (
            "DESIGN_ONLY_ARCHITECTURE_NEUTRAL_INPUT_CONTRACT_"
            "FOR_THE_FROZEN_331_FEATURE_PORTABLE_XAUUSD_ARTIFACT"
        ),
        "evidence": {
            "readiness_version": (
                EXPECTED_READINESS_VERSION
            ),
            "readiness_status": (
                EXPECTED_READINESS_STATUS
            ),
            "portable_dataset_id": (
                EXPECTED_PORTABLE_DATASET_ID
            ),
            "portable_dataset_sha256": (
                EXPECTED_PORTABLE_DATASET_SHA256
            ),
            "portable_manifest_sha256": (
                EXPECTED_PORTABLE_MANIFEST_SHA256
            ),
            "feature_columns_sha256": (
                EXPECTED_FEATURE_COLUMNS_SHA256
            ),
            "train_input_fingerprint_sha256": (
                EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256
            ),
            "feature_contract_design_fingerprint_sha256": (
                EXPECTED_FEATURE_CONTRACT_DESIGN_FINGERPRINT_SHA256
            ),
            "all_prerequisites_validated": (
                True
            ),
        },
        "contract": (
            contract_core
        ),
        "contract_fingerprint": {
            "version": (
                "XAUUSD_PORTABLE_331_TRAINER_INPUT_CONTRACT_FINGERPRINT_V1"
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
                "XAUUSD_PORTABLE_331_RESEARCH_TRAINER_INPUT_CONTRACT_DESIGN_CONFIRMED"
            ),
            "reason": (
                "PORTABLE_ARTIFACT_FEATURE_ORDER_TARGET_METADATA_"
                "SPLIT_ACCESS_AND_HOLDOUT_RULES_ARE_NOW_PINNED_"
                "IN_AN_ARCHITECTURE_NEUTRAL_INPUT_CONTRACT"
            ),
            "trainer_input_contract_version": (
                TRAINER_INPUT_CONTRACT_VERSION
            ),
            "trainer_input_contract_fingerprint_sha256": (
                contract_fingerprint
            ),
            "portable_feature_count": (
                EXPECTED_PORTABLE_FEATURE_COUNT
            ),
            "train_rows": (
                EXPECTED_TRAIN_ROWS
            ),
            "validation_rows": (
                EXPECTED_VALIDATION_ROWS
            ),
            "test_rows": (
                EXPECTED_TEST_ROWS
            ),
            "current_v4_trainer_direct_reuse_authorized": (
                False
            ),
            "portable_input_loader_implementation_authorized_next": (
                True
            ),
            "model_architecture_selected": (
                False
            ),
            "model_training_authorized": (
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
                "IMPLEMENT_PORTABLE_331_TRAINING_INPUT_LOADER_"
                "WITHOUT_MODEL_FIT_OR_HOLDOUT_FEATURE_ACCESS"
            ),
        },
        "scientific_policy": {
            "readiness_evidence_loaded": (
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
            "target_values_loaded": (
                False
            ),
            "train_feature_values_loaded": (
                False
            ),
            "validation_feature_values_loaded": (
                False
            ),
            "test_feature_values_loaded": (
                False
            ),
            "validation_metrics_computed": (
                False
            ),
            "test_metrics_computed": (
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
            "model_artifacts_written": (
                False
            ),
            "dataset_written": (
                False
            ),
            "manifest_written": (
                False
            ),
            "current_v4_trainer_source_read_only": (
                True
            ),
            "current_v4_trainer_imported": (
                False
            ),
            "current_v4_trainer_modified": (
                False
            ),
            "feature_pipeline_modified": (
                False
            ),
            "portable_contract_mutated": (
                False
            ),
            "frozen_v3_contract_mutated": (
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
        "next_decision_contract": {
            "if_design_confirmed": (
                "IMPLEMENT_PORTABLE_331_TRAINING_INPUT_LOADER_"
                "WITHOUT_MODEL_FIT_OR_HOLDOUT_FEATURE_ACCESS"
            ),
            "recommended_loader_module": (
                "02_AI.Dataset.portable_331_training_input_loader"
            ),
            "recommended_loader_class": (
                "Portable331TrainingInputLoader"
            ),
            "model_architecture_selection_deferred": (
                True
            ),
            "model_training_not_authorized": (
                True
            ),
            "validation_feature_access_not_authorized": (
                True
            ),
            "test_feature_access_not_authorized": (
                True
            ),
            "test_final_holdout_policy": (
                "ONE_FINAL_EVALUATION_ONLY_AFTER_CANDIDATE_FREEZE"
            ),
            "portable_dataset_rebuild_required": (
                False
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
                        "XAUUSD_PORTABLE_331_TRAINER_INPUT_"
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
                    "target_values_loaded": (
                        False
                    ),
                    "validation_feature_values_loaded": (
                        False
                    ),
                    "test_feature_values_loaded": (
                        False
                    ),
                    "model_loaded": (
                        False
                    ),
                    "model_trained": (
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