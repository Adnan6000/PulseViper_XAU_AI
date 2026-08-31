#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

import numpy as np


ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_CANDIDATE_"
    "EVALUATOR_INTEGRATION_V1"
)

REPO_ROOT = Path(__file__).resolve().parents[1]

DATASET_DIR = (
    REPO_ROOT
    / "02_AI"
    / "Dataset"
)

LOADER_PATH = (
    DATASET_DIR
    / "portable_331_training_input_loader.py"
)

EVALUATOR_PATH = (
    REPO_ROOT
    / "04_Testing"
    / "evaluate_xauusd_portable_331_train_model_candidates.py"
)

PROTOCOL_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_train_model_research_protocol_design.json"
)

REGISTRY_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_train_model_candidate_registry_design.json"
)

DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_candidate_evaluator_integration.json"
)

DATASET_PACKAGE = (
    "02_AI.Dataset"
)

LOADER_MODULE_BASENAME = (
    "portable_331_training_input_loader"
)

EXPECTED_PROTOCOL_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_MODEL_RESEARCH_PROTOCOL_V1"
)

EXPECTED_PROTOCOL_FINGERPRINT = (
    "69e51e1b249b9da68cbf6f6778a8ae10f9f33f7082a07e5073a1ba731fa1640d"
)

EXPECTED_REGISTRY_FINGERPRINT = (
    "b8088bb34ce8940f7de5946fbb9b0fd20f40d7cc93a76b76fd7975591f00066c"
)

EXPECTED_SUPERVISED_BATCH_CONTRACT = (
    "XAUUSD_PORTABLE_331_TRAIN_SUPERVISED_BATCH_V1"
)

EXPECTED_SUPERVISED_BATCH_FINGERPRINT = (
    "1e7bd0751234282d4081ef87783de8633aac815a2f6aa13010fbb5a06156aec4"
)

EXPECTED_TRAINER_INPUT_CONTRACT = (
    "XAUUSD_PORTABLE_331_RESEARCH_TRAINER_INPUT_V1"
)

EXPECTED_TRAINER_INPUT_FINGERPRINT = (
    "b192ce16291fe9ddca9ead9561224fb942c331d1f30fc1b53cee396efa5accdf"
)

EXPECTED_TARGET_ACCESS_CONTRACT = (
    "XAUUSD_PORTABLE_331_TRAIN_TARGET_ACCESS_V1"
)

EXPECTED_TARGET_ACCESS_FINGERPRINT = (
    "a640b9cda2522b734515a2cdf05259abbf77e4c6488afd635aedc21f62458266"
)

EXPECTED_FEATURE_COUNT = 331
EXPECTED_TRAIN_ROWS = 69966
EXPECTED_PURGE_ROWS = 12
EXPECTED_FOLD_COUNT = 4


class IntegrationContractError(
    RuntimeError
):
    pass


def _canonical_json_sha256(
    value: Any,
) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=False,
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        encoded
    ).hexdigest()


def _read_text_auto(
    path: Path,
) -> str:
    raw = path.read_bytes()

    if raw.startswith(
        b"\xff\xfe"
    ):
        return raw.decode(
            "utf-16"
        )

    if raw.startswith(
        b"\xfe\xff"
    ):
        return raw.decode(
            "utf-16"
        )

    if raw.startswith(
        b"\xef\xbb\xbf"
    ):
        return raw.decode(
            "utf-8-sig"
        )

    return raw.decode(
        "utf-8"
    )


def _load_json_auto(
    path: Path,
) -> dict[str, Any]:
    try:
        payload = json.loads(
            _read_text_auto(
                path
            )
        )

    except Exception as exc:
        raise IntegrationContractError(
            f"Cannot load JSON contract: {path}"
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        raise IntegrationContractError(
            f"Expected JSON object: {path}"
        )

    return payload


def _prepend_sys_path(
    path: Path,
) -> None:
    path_text = str(
        path
    )

    if path_text in sys.path:
        sys.path.remove(
            path_text
        )

    sys.path.insert(
        0,
        path_text,
    )


def _load_module_from_path(
    path: Path,
    module_name: str,
) -> ModuleType:
    if not path.is_file():
        raise IntegrationContractError(
            f"Missing Python module: {path}"
        )

    spec = importlib.util.spec_from_file_location(
        module_name,
        path,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise IntegrationContractError(
            f"Cannot create import spec: {path}"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    sys.modules[
        module_name
    ] = module

    try:
        spec.loader.exec_module(
            module
        )

    except Exception:
        sys.modules.pop(
            module_name,
            None,
        )

        raise

    return module


def _local_dataset_dependencies(
    module_path: Path,
) -> tuple[str, ...]:
    try:
        source = module_path.read_text(
            encoding="utf-8"
        )

        tree = ast.parse(
            source,
            filename=str(
                module_path
            ),
        )

    except Exception as exc:
        raise IntegrationContractError(
            "Cannot inspect local Dataset module "
            f"dependencies: {module_path}"
        ) from exc

    dependencies: set[str] = set()

    for node in ast.walk(
        tree
    ):
        if isinstance(
            node,
            ast.Import,
        ):
            for alias in node.names:
                module_name = (
                    alias.name.split(
                        ".",
                        1,
                    )[0]
                )

                candidate = (
                    DATASET_DIR
                    / f"{module_name}.py"
                )

                if candidate.is_file():
                    dependencies.add(
                        module_name
                    )

        elif isinstance(
            node,
            ast.ImportFrom,
        ):
            if (
                node.level
                != 0
                or not node.module
            ):
                continue

            module_name = (
                node.module.split(
                    ".",
                    1,
                )[0]
            )

            candidate = (
                DATASET_DIR
                / f"{module_name}.py"
            )

            if candidate.is_file():
                dependencies.add(
                    module_name
                )

    return tuple(
        sorted(
            dependencies
        )
    )


def _import_dataset_package_module(
    module_basename: str,
    visiting: set[str] | None = None,
) -> ModuleType:
    if visiting is None:
        visiting = set()

    qualified_name = (
        f"{DATASET_PACKAGE}.{module_basename}"
    )

    existing = sys.modules.get(
        qualified_name
    )

    if isinstance(
        existing,
        ModuleType,
    ):
        sys.modules[
            module_basename
        ] = existing

        return existing

    if module_basename in visiting:
        existing_top_level = (
            sys.modules.get(
                module_basename
            )
        )

        if isinstance(
            existing_top_level,
            ModuleType,
        ):
            return existing_top_level

        raise IntegrationContractError(
            "Circular Dataset import could not "
            f"be resolved: {module_basename}"
        )

    module_path = (
        DATASET_DIR
        / f"{module_basename}.py"
    )

    if not module_path.is_file():
        raise IntegrationContractError(
            "Local Dataset dependency does not exist: "
            f"{module_basename}"
        )

    visiting.add(
        module_basename
    )

    try:
        dependencies = (
            _local_dataset_dependencies(
                module_path
            )
        )

        for dependency in dependencies:
            if (
                dependency
                == module_basename
            ):
                continue

            _import_dataset_package_module(
                dependency,
                visiting,
            )

        try:
            module = importlib.import_module(
                qualified_name
            )

        except Exception as exc:
            raise IntegrationContractError(
                "Package-aware Dataset import failed: "
                f"{qualified_name}: {exc}"
            ) from exc

        sys.modules[
            module_basename
        ] = module

        return module

    finally:
        visiting.discard(
            module_basename
        )


def _load_loader_module() -> ModuleType:
    if not LOADER_PATH.is_file():
        raise IntegrationContractError(
            f"Missing training loader: {LOADER_PATH}"
        )

    _prepend_sys_path(
        REPO_ROOT
    )

    try:
        importlib.import_module(
            DATASET_PACKAGE
        )

    except Exception as exc:
        raise IntegrationContractError(
            "Cannot import Dataset package context "
            f"{DATASET_PACKAGE}: {exc}"
        ) from exc

    return _import_dataset_package_module(
        LOADER_MODULE_BASENAME
    )


def _load_evaluator_module() -> ModuleType:
    return _load_module_from_path(
        EVALUATOR_PATH,
        "xauusd_portable_331_candidate_evaluator_runtime",
    )


def _required_mapping(
    mapping: Mapping[str, Any],
    key: str,
) -> Mapping[str, Any]:
    value = mapping.get(
        key
    )

    if not isinstance(
        value,
        Mapping,
    ):
        raise IntegrationContractError(
            f"Required mapping missing: {key}"
        )

    return value


def _required_list(
    mapping: Mapping[str, Any],
    key: str,
) -> list[Any]:
    value = mapping.get(
        key
    )

    if not isinstance(
        value,
        list,
    ):
        raise IntegrationContractError(
            f"Required list missing: {key}"
        )

    return value


def _required_int(
    mapping: Mapping[str, Any],
    key: str,
) -> int:
    value = mapping.get(
        key
    )

    if (
        isinstance(
            value,
            bool,
        )
        or not isinstance(
            value,
            int,
        )
    ):
        raise IntegrationContractError(
            f"Required integer missing: {key}"
        )

    return value


def _validate_protocol(
    protocol: Mapping[str, Any],
    registry: Mapping[str, Any],
) -> Mapping[str, Any]:
    if (
        protocol.get(
            "valid"
        )
        is not True
    ):
        raise IntegrationContractError(
            "Research protocol must be valid=true."
        )

    contract = _required_mapping(
        protocol,
        "contract",
    )

    contract_fingerprint = (
        _required_mapping(
            protocol,
            "contract_fingerprint",
        )
    )

    fingerprint = (
        contract_fingerprint.get(
            "sha256"
        )
    )

    if (
        fingerprint
        != EXPECTED_PROTOCOL_FINGERPRINT
    ):
        raise IntegrationContractError(
            "Research protocol fingerprint mismatch."
        )

    computed = (
        _canonical_json_sha256(
            contract
        )
    )

    if (
        computed
        != fingerprint
    ):
        raise IntegrationContractError(
            "Research protocol contract content "
            "does not match its SHA256 fingerprint."
        )

    decision = _required_mapping(
        protocol,
        "decision",
    )

    if (
        decision.get(
            "research_protocol_version"
        )
        != EXPECTED_PROTOCOL_VERSION
    ):
        raise IntegrationContractError(
            "Research protocol version mismatch."
        )

    if (
        decision.get(
            "research_protocol_fingerprint_sha256"
        )
        != EXPECTED_PROTOCOL_FINGERPRINT
    ):
        raise IntegrationContractError(
            "Protocol decision fingerprint mismatch."
        )

    if (
        decision.get(
            "candidate_training_authorized"
        )
        is not False
    ):
        raise IntegrationContractError(
            "Protocol must not authorize candidate "
            "training in this gate."
        )

    if (
        decision.get(
            "model_training_authorized"
        )
        is not False
    ):
        raise IntegrationContractError(
            "Protocol must not authorize model training."
        )

    if (
        decision.get(
            "validation_access_authorized"
        )
        is not False
    ):
        raise IntegrationContractError(
            "VALIDATION must remain blocked."
        )

    if (
        decision.get(
            "test_access_authorized"
        )
        is not False
    ):
        raise IntegrationContractError(
            "TEST must remain blocked."
        )

    registry_contract = (
        _required_mapping(
            registry,
            "contract",
        )
    )

    parent_protocol = (
        _required_mapping(
            registry_contract,
            "parent_research_protocol",
        )
    )

    if (
        parent_protocol.get(
            "fingerprint_sha256"
        )
        != EXPECTED_PROTOCOL_FINGERPRINT
    ):
        raise IntegrationContractError(
            "Registry does not reference the "
            "frozen research protocol."
        )

    return contract


def _build_folds(
    protocol_contract: Mapping[str, Any],
    evaluator_module: ModuleType,
) -> list[Any]:
    walk_forward = (
        _required_mapping(
            protocol_contract,
            "walk_forward_protocol",
        )
    )

    if (
        walk_forward.get(
            "method"
        )
        != "EXPANDING_WINDOW_PURGED_TRAIN_ONLY"
    ):
        raise IntegrationContractError(
            "Unexpected walk-forward method."
        )

    if (
        walk_forward.get(
            "chronological_order_required"
        )
        is not True
    ):
        raise IntegrationContractError(
            "Chronological order must be required."
        )

    if (
        walk_forward.get(
            "shuffle_allowed"
        )
        is not False
    ):
        raise IntegrationContractError(
            "Shuffle must remain disabled."
        )

    if (
        walk_forward.get(
            "validation_rows_are_inside_frozen_train_only"
        )
        is not True
    ):
        raise IntegrationContractError(
            "Fold validation rows must remain "
            "inside frozen TRAIN only."
        )

    if (
        walk_forward.get(
            "portable_validation_split_access_allowed"
        )
        is not False
    ):
        raise IntegrationContractError(
            "Portable VALIDATION access must remain blocked."
        )

    if (
        walk_forward.get(
            "portable_test_split_access_allowed"
        )
        is not False
    ):
        raise IntegrationContractError(
            "Portable TEST access must remain blocked."
        )

    if (
        _required_int(
            walk_forward,
            "fold_count",
        )
        != EXPECTED_FOLD_COUNT
    ):
        raise IntegrationContractError(
            "Unexpected fold count."
        )

    if (
        _required_int(
            walk_forward,
            "purge_rows_before_each_validation",
        )
        != EXPECTED_PURGE_ROWS
    ):
        raise IntegrationContractError(
            "Unexpected protocol purge rows."
        )

    raw_folds = _required_list(
        walk_forward,
        "folds",
    )

    if (
        len(
            raw_folds
        )
        != EXPECTED_FOLD_COUNT
    ):
        raise IntegrationContractError(
            "Frozen fold list length mismatch."
        )

    folds: list[Any] = []

    for expected_fold, raw_fold in enumerate(
        raw_folds,
        start=1,
    ):
        if not isinstance(
            raw_fold,
            Mapping,
        ):
            raise IntegrationContractError(
                "Fold entry must be a mapping."
            )

        fold_number = _required_int(
            raw_fold,
            "fold",
        )

        if (
            fold_number
            != expected_fold
        ):
            raise IntegrationContractError(
                "Fold numbering is not contiguous."
            )

        train_start = _required_int(
            raw_fold,
            "train_start_inclusive",
        )

        train_stop = _required_int(
            raw_fold,
            "train_end_exclusive",
        )

        purge_start = _required_int(
            raw_fold,
            "purge_start_inclusive",
        )

        purge_end = _required_int(
            raw_fold,
            "purge_end_exclusive",
        )

        validation_start = _required_int(
            raw_fold,
            "validation_start_inclusive",
        )

        validation_stop = _required_int(
            raw_fold,
            "validation_end_exclusive",
        )

        purge_rows = _required_int(
            raw_fold,
            "purge_rows",
        )

        train_rows = _required_int(
            raw_fold,
            "train_rows",
        )

        validation_rows = _required_int(
            raw_fold,
            "validation_rows",
        )

        if (
            train_stop
            - train_start
            != train_rows
        ):
            raise IntegrationContractError(
                f"Fold {fold_number} train row count mismatch."
            )

        if (
            purge_start
            != train_stop
        ):
            raise IntegrationContractError(
                f"Fold {fold_number} purge must start "
                "at train end."
            )

        if (
            purge_end
            != validation_start
        ):
            raise IntegrationContractError(
                f"Fold {fold_number} validation must start "
                "at purge end."
            )

        if (
            purge_end
            - purge_start
            != purge_rows
        ):
            raise IntegrationContractError(
                f"Fold {fold_number} purge size mismatch."
            )

        if (
            purge_rows
            != EXPECTED_PURGE_ROWS
        ):
            raise IntegrationContractError(
                f"Fold {fold_number} purge contract mismatch."
            )

        if (
            validation_stop
            - validation_start
            != validation_rows
        ):
            raise IntegrationContractError(
                f"Fold {fold_number} validation row "
                "count mismatch."
            )

        folds.append(
            evaluator_module.FoldSpec(
                fold_id=f"F{fold_number}",
                train_start=train_start,
                train_stop=train_stop,
                validation_start=validation_start,
                validation_stop=validation_stop,
                purge_rows=purge_rows,
            )
        )

    return folds


def _validate_supervised_batch(
    batch: Any,
    registry: Mapping[str, Any],
) -> dict[str, Any]:
    registry_contract = (
        _required_mapping(
            registry,
            "contract",
        )
    )

    frozen_identity = (
        _required_mapping(
            registry_contract,
            "frozen_train_identity",
        )
    )

    expected_pairs = (
        (
            "dataset_id",
            batch.dataset_id,
        ),
        (
            "dataset_sha256",
            batch.dataset_sha256,
        ),
        (
            "manifest_sha256",
            batch.manifest_sha256,
        ),
        (
            "train_input_fingerprint_sha256",
            batch.train_input_fingerprint_sha256,
        ),
        (
            "train_target_fingerprint_sha256",
            batch.train_target_fingerprint_sha256,
        ),
        (
            "row_count",
            batch.row_count,
        ),
    )

    for key, actual in expected_pairs:
        expected = (
            frozen_identity.get(
                key
            )
        )

        if actual != expected:
            raise IntegrationContractError(
                "Supervised TRAIN identity mismatch: "
                f"{key}"
            )

    if (
        batch.row_count
        != EXPECTED_TRAIN_ROWS
    ):
        raise IntegrationContractError(
            "Unexpected supervised TRAIN row count."
        )

    if (
        batch.supervised_batch_contract_version
        != EXPECTED_SUPERVISED_BATCH_CONTRACT
    ):
        raise IntegrationContractError(
            "Supervised batch contract version mismatch."
        )

    if (
        batch.supervised_batch_contract_fingerprint_sha256
        != EXPECTED_SUPERVISED_BATCH_FINGERPRINT
    ):
        raise IntegrationContractError(
            "Supervised batch contract fingerprint mismatch."
        )

    if (
        batch.trainer_input_contract_version
        != EXPECTED_TRAINER_INPUT_CONTRACT
    ):
        raise IntegrationContractError(
            "Trainer input contract version mismatch."
        )

    if (
        batch.trainer_input_contract_fingerprint_sha256
        != EXPECTED_TRAINER_INPUT_FINGERPRINT
    ):
        raise IntegrationContractError(
            "Trainer input contract fingerprint mismatch."
        )

    if (
        batch.target_access_contract_version
        != EXPECTED_TARGET_ACCESS_CONTRACT
    ):
        raise IntegrationContractError(
            "Target access contract version mismatch."
        )

    if (
        batch.target_access_contract_fingerprint_sha256
        != EXPECTED_TARGET_ACCESS_FINGERPRINT
    ):
        raise IntegrationContractError(
            "Target access contract fingerprint mismatch."
        )

    feature_count = len(
        batch.feature_columns
    )

    if (
        feature_count
        != EXPECTED_FEATURE_COUNT
    ):
        raise IntegrationContractError(
            "Supervised batch feature count mismatch."
        )

    X = np.asarray(
        batch.X
    )

    target_class = np.asarray(
        batch.target_class
    )

    target_tradeable = np.asarray(
        batch.target_tradeable
    )

    decision_time = np.asarray(
        batch.decision_time
    )

    if (
        X.shape
        != (
            EXPECTED_TRAIN_ROWS,
            EXPECTED_FEATURE_COUNT,
        )
    ):
        raise IntegrationContractError(
            "Supervised TRAIN X shape mismatch."
        )

    expected_vector_shape = (
        EXPECTED_TRAIN_ROWS,
    )

    for name, array in (
        (
            "target_class",
            target_class,
        ),
        (
            "target_tradeable",
            target_tradeable,
        ),
        (
            "decision_time",
            decision_time,
        ),
    ):
        if (
            array.shape
            != expected_vector_shape
        ):
            raise IntegrationContractError(
                f"{name} shape mismatch."
            )

    if not np.isfinite(
        X
    ).all():
        raise IntegrationContractError(
            "Supervised TRAIN X contains non-finite values."
        )

    if not np.array_equal(
        (
            target_class
            != 0
        ).astype(
            np.int8
        ),
        target_tradeable.astype(
            np.int8,
            copy=False,
        ),
    ):
        raise IntegrationContractError(
            "target_tradeable linkage mismatch."
        )

    if (
        decision_time.shape[0]
        > 1
    ):
        try:
            strictly_increasing = bool(
                np.all(
                    decision_time[
                        1:
                    ]
                    > decision_time[
                        :-1
                    ]
                )
            )

        except Exception as exc:
            raise IntegrationContractError(
                "Cannot verify decision_time chronology."
            ) from exc

        if not strictly_increasing:
            raise IntegrationContractError(
                "TRAIN decision_time must be "
                "strictly increasing."
            )

    return {
        "dataset_id": (
            batch.dataset_id
        ),
        "dataset_sha256": (
            batch.dataset_sha256
        ),
        "manifest_sha256": (
            batch.manifest_sha256
        ),
        "row_count": int(
            batch.row_count
        ),
        "feature_count": int(
            feature_count
        ),
        "feature_columns_sha256": (
            batch.feature_columns_sha256
        ),
        "train_input_fingerprint_sha256": (
            batch.train_input_fingerprint_sha256
        ),
        "train_target_fingerprint_sha256": (
            batch.train_target_fingerprint_sha256
        ),
        "X_shape": [
            int(
                value
            )
            for value in X.shape
        ],
        "X_dtype": str(
            X.dtype
        ),
        "X_nonfinite_count": int(
            np.size(
                X
            )
            - np.count_nonzero(
                np.isfinite(
                    X
                )
            )
        ),
        "target_class_shape": [
            int(
                value
            )
            for value in target_class.shape
        ],
        "target_class_dtype": str(
            target_class.dtype
        ),
        "target_tradeable_shape": [
            int(
                value
            )
            for value in target_tradeable.shape
        ],
        "target_tradeable_dtype": str(
            target_tradeable.dtype
        ),
        "target_tradeable_linkage_confirmed": True,
        "decision_time_shape": [
            int(
                value
            )
            for value in decision_time.shape
        ],
        "decision_time_strictly_increasing": True,
        "supervised_batch_contract_version": (
            batch.supervised_batch_contract_version
        ),
        "supervised_batch_contract_fingerprint_sha256": (
            batch.supervised_batch_contract_fingerprint_sha256
        ),
    }


def build_integration_attestation(
    canonical_root: str | Path = REPO_ROOT,
) -> dict[str, Any]:
    evaluator = (
        _load_evaluator_module()
    )

    loader_module = (
        _load_loader_module()
    )

    registry = (
        evaluator.load_frozen_candidate_registry(
            REGISTRY_PATH
        )
    )

    registry_fingerprint = (
        registry[
            "registry_fingerprint"
        ][
            "sha256"
        ]
    )

    if (
        registry_fingerprint
        != EXPECTED_REGISTRY_FINGERPRINT
    ):
        raise IntegrationContractError(
            "Frozen registry fingerprint mismatch."
        )

    protocol = _load_json_auto(
        PROTOCOL_PATH
    )

    protocol_contract = (
        _validate_protocol(
            protocol,
            registry,
        )
    )

    folds = _build_folds(
        protocol_contract,
        evaluator,
    )

    loader_class = getattr(
        loader_module,
        "Portable331TrainingInputLoader",
        None,
    )

    if loader_class is None:
        raise IntegrationContractError(
            "Portable331TrainingInputLoader "
            "class is unavailable."
        )

    loader = loader_class(
        canonical_root
    )

    batch = (
        loader.load_train_supervised()
    )

    batch_summary = (
        _validate_supervised_batch(
            batch,
            registry,
        )
    )

    (
        X_validated,
        target_class_validated,
        target_tradeable_validated,
    ) = evaluator.validate_train_only_inputs(
        batch.X,
        batch.target_class,
        batch.target_tradeable,
        expected_feature_count=(
            EXPECTED_FEATURE_COUNT
        ),
    )

    evaluator.validate_fold_specs(
        folds,
        n_rows=(
            X_validated.shape[
                0
            ]
        ),
        required_fold_count=(
            EXPECTED_FOLD_COUNT
        ),
        required_purge_rows=(
            EXPECTED_PURGE_ROWS
        ),
    )

    if (
        X_validated.shape[0]
        != EXPECTED_TRAIN_ROWS
        or target_class_validated.shape[0]
        != EXPECTED_TRAIN_ROWS
        or target_tradeable_validated.shape[0]
        != EXPECTED_TRAIN_ROWS
    ):
        raise IntegrationContractError(
            "Evaluator-normalized TRAIN arrays "
            "have unexpected row counts."
        )

    fold_report = [
        {
            "fold_id": (
                fold.fold_id
            ),
            "train_start": int(
                fold.train_start
            ),
            "train_stop": int(
                fold.train_stop
            ),
            "train_rows": int(
                fold.train_stop
                - fold.train_start
            ),
            "purge_rows": int(
                fold.purge_rows
            ),
            "validation_start": int(
                fold.validation_start
            ),
            "validation_stop": int(
                fold.validation_stop
            ),
            "validation_rows": int(
                fold.validation_stop
                - fold.validation_start
            ),
        }
        for fold in folds
    ]

    return {
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "valid": True,
        "research_scope": (
            "REAL_FROZEN_TRAIN_SUPERVISED_BATCH_"
            "TO_CANDIDATE_EVALUATOR_INTEGRATION_"
            "ATTESTATION_WITHOUT_MODEL_FIT"
        ),
        "runtime_import": {
            "loader_module_name": (
                loader_module.__name__
            ),
            "loader_module_package": (
                loader_module.__package__
            ),
            "package_context_confirmed": (
                loader_module.__package__
                == DATASET_PACKAGE
            ),
        },
        "artifact_identity": {
            "dataset_id": (
                batch.dataset_id
            ),
            "dataset_sha256": (
                batch.dataset_sha256
            ),
            "manifest_sha256": (
                batch.manifest_sha256
            ),
            "train_input_fingerprint_sha256": (
                batch.train_input_fingerprint_sha256
            ),
            "train_target_fingerprint_sha256": (
                batch.train_target_fingerprint_sha256
            ),
            "research_protocol_fingerprint_sha256": (
                EXPECTED_PROTOCOL_FINGERPRINT
            ),
            "candidate_registry_fingerprint_sha256": (
                EXPECTED_REGISTRY_FINGERPRINT
            ),
        },
        "train_supervised_batch": (
            batch_summary
        ),
        "walk_forward_folds": (
            fold_report
        ),
        "evaluator_validation": {
            "feature_count": int(
                X_validated.shape[
                    1
                ]
            ),
            "row_count": int(
                X_validated.shape[
                    0
                ]
            ),
            "fold_count": int(
                len(
                    folds
                )
            ),
            "purge_rows": (
                EXPECTED_PURGE_ROWS
            ),
            "target_linkage_validated": True,
            "candidate_fit_performed": False,
        },
        "decision": {
            "integration_confirmed": True,
            "candidate_fit_authorized_in_this_gate": False,
            "candidate_fit_performed": False,
            "candidate_evaluation_metrics_computed": False,
            "winner_selected": False,
            "final_full_train_fit_authorized": False,
            "validation_access_authorized": False,
            "test_access_authorized": False,
            "live_authorized": False,
            "next_action": (
                "AUTHORIZE_FIRST_REAL_FIXED_SIX_"
                "CANDIDATE_TRAIN_ONLY_WALK_FORWARD_"
                "EVALUATION_IF_THIS_INTEGRATION_"
                "ATTESTATION_IS_REVIEWED_AND_ACCEPTED"
            ),
        },
        "scientific_policy": {
            "train_feature_values_loaded": True,
            "train_target_values_loaded": True,
            "portable_validation_feature_values_loaded": False,
            "portable_validation_target_values_loaded": False,
            "portable_test_feature_values_loaded": False,
            "portable_test_target_values_loaded": False,
            "model_fit_performed": False,
            "scaler_fit_performed": False,
            "candidate_metrics_computed": False,
            "threshold_search_performed": False,
            "probability_calibration_performed": False,
            "feature_selection_performed": False,
            "registry_changed": False,
            "model_artifacts_written": False,
            "dataset_written": False,
            "manifest_written": False,
            "execution_integration_modified": False,
            "risk_engine_modified": False,
            "orders_sent": False,
            "live_authorized": False,
        },
    }


def _write_json_utf8(
    path: Path,
    payload: Mapping[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate real portable 331 TRAIN supervised "
            "batch integration with the frozen walk-forward "
            "candidate evaluator without fitting any model."
        )
    )

    parser.add_argument(
        "--canonical-root",
        type=Path,
        default=REPO_ROOT,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )

    args = parser.parse_args()

    try:
        report = (
            build_integration_attestation(
                args.canonical_root
            )
        )

    except Exception as exc:
        failure = {
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "valid": False,
            "reason": (
                "XAUUSD_PORTABLE_331_CANDIDATE_"
                "EVALUATOR_INTEGRATION_FAILED"
            ),
            "error_type": (
                type(
                    exc
                ).__name__
            ),
            "error": str(
                exc
            ),
            "scientific_policy": {
                "candidate_fit_performed": False,
                "validation_access_authorized": False,
                "test_access_authorized": False,
                "live_authorized": False,
            },
        }

        _write_json_utf8(
            args.output,
            failure,
        )

        print(
            json.dumps(
                failure,
                indent=2,
                sort_keys=True,
            )
        )

        return 1

    _write_json_utf8(
        args.output,
        report,
    )

    print(
        json.dumps(
            {
                "analysis_version": (
                    report[
                        "analysis_version"
                    ]
                ),
                "valid": True,
                "output": str(
                    args.output
                ),
                "runtime_import": (
                    report[
                        "runtime_import"
                    ]
                ),
                "decision": (
                    report[
                        "decision"
                    ]
                ),
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