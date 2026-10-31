#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import pandas as pd


ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_AUTHORIZED_"
    "VALIDATION_SOURCE_IMPLEMENTATION_V1"
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

CORE_PATH = (
    REPO_ROOT
    / "04_Testing"
    / "xauusd_portable_331_one_time_validation_core.py"
)

INTEGRATION_RUNNER_PATH = (
    REPO_ROOT
    / "04_Testing"
    / "run_xauusd_portable_331_candidate_evaluator_integration.py"
)

DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_authorized_validation_source_attestation.json"
)

EXPECTED_LOADER_SOURCE_SHA256 = (
    "49c86c269f2742fec7c6991eaf7a8a9c0466066a3db230a80375ba2e2c33680c"
)

EXPECTED_PROTOCOL_FINGERPRINT = (
    "ce78180a5f2472c36c74cea2c447307641aa3d5fedfb7a01d9b65260b5a6fcea"
)

EXPECTED_MODEL_ARTIFACT_SHA256 = (
    "48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769"
)

EXPECTED_FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

EXPECTED_FEATURE_COUNT = 331

EXPECTED_SPLIT_COLUMN = (
    "dataset_split"
)

EXPECTED_DECISION_TIME_COLUMN = (
    "decision_time"
)

EXPECTED_TARGET_COLUMNS = (
    "target_class",
    "target_tradeable",
)

EXPECTED_SPLIT_ORDER = (
    "TRAIN",
    "VALIDATION",
    "TEST",
)

EXPECTED_BLOCKED_ACCESSOR_TOKENS = {
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


class AuthorizedValidationSourceError(
    RuntimeError
):
    pass


@dataclass(
    frozen=True
)
class ValidationWindow:
    total_rows: int
    train_rows: int
    validation_rows: int
    test_rows: int
    validation_start: int
    validation_stop: int

    def to_dict(
        self,
    ) -> dict[str, int]:
        return asdict(
            self
        )


def _sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as handle:
        for chunk in iter(
            lambda: handle.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(
                chunk
            )

    return digest.hexdigest()


def _load_module_from_path(
    path: Path,
    module_name: str,
) -> ModuleType:
    if not path.is_file():
        raise AuthorizedValidationSourceError(
            f"Required Python module missing: {path}"
        )

    spec = importlib.util.spec_from_file_location(
        module_name,
        path,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise AuthorizedValidationSourceError(
            f"Cannot create module spec: {path}"
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


def _load_core_module() -> ModuleType:
    return _load_module_from_path(
        CORE_PATH,
        "xauusd_authorized_validation_source_core",
    )


def _load_loader_class() -> type:
    integration = _load_module_from_path(
        INTEGRATION_RUNNER_PATH,
        "xauusd_validation_source_integration_loader",
    )

    loader_module = (
        integration._load_loader_module()
    )

    loader_class = getattr(
        loader_module,
        "Portable331TrainingInputLoader",
        None,
    )

    if loader_class is None:
        raise AuthorizedValidationSourceError(
            "Portable331TrainingInputLoader unavailable."
        )

    return loader_class


def inspect_loader_source_contract() -> dict[str, Any]:
    if not LOADER_PATH.is_file():
        raise AuthorizedValidationSourceError(
            f"Training loader missing: {LOADER_PATH}"
        )

    source_sha256 = _sha256_file(
        LOADER_PATH
    )

    if (
        source_sha256
        != EXPECTED_LOADER_SOURCE_SHA256
    ):
        raise AuthorizedValidationSourceError(
            "Portable 331 loader source SHA256 mismatch."
        )

    source = LOADER_PATH.read_text(
        encoding="utf-8"
    )

    try:
        tree = ast.parse(
            source,
            filename=str(
                LOADER_PATH
            ),
        )

    except SyntaxError as exc:
        raise AuthorizedValidationSourceError(
            "Portable 331 loader source cannot be parsed."
        ) from exc

    loader_class_node = None

    for node in tree.body:
        if (
            isinstance(
                node,
                ast.ClassDef,
            )
            and node.name
            == "Portable331TrainingInputLoader"
        ):
            loader_class_node = node
            break

    if loader_class_node is None:
        raise AuthorizedValidationSourceError(
            "Portable331TrainingInputLoader class missing."
        )

    methods = {
        node.name: node
        for node in loader_class_node.body
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
    }

    required_internal_methods = (
        "_discover_exact_artifact",
        "_validate_manifest",
        "_validate_split_series",
        "_validate_split_structure",
        "_feature_columns_sha256",
        "_numeric_matrix",
        "_normalize_target_class_array",
        "_normalize_target_tradeable_array",
    )

    for method_name in required_internal_methods:
        if method_name not in methods:
            raise AuthorizedValidationSourceError(
                "Required loader helper missing: "
                f"{method_name}"
            )

    blocked_accessors: dict[
        str,
        dict[str, Any],
    ] = {}

    for (
        method_name,
        expected_token,
    ) in EXPECTED_BLOCKED_ACCESSOR_TOKENS.items():
        method = methods.get(
            method_name
        )

        if method is None:
            raise AuthorizedValidationSourceError(
                "Required blocked accessor missing: "
                f"{method_name}"
            )

        string_constants = {
            node.value
            for node in ast.walk(
                method
            )
            if (
                isinstance(
                    node,
                    ast.Constant,
                )
                and isinstance(
                    node.value,
                    str,
                )
            )
        }

        if expected_token not in string_constants:
            raise AuthorizedValidationSourceError(
                "Blocked holdout accessor token mismatch: "
                f"{method_name}"
            )

        blocked_accessors[
            method_name
        ] = {
            "expected_token": (
                expected_token
            ),
            "confirmed": True,
        }

    return {
        "loader_path": str(
            LOADER_PATH.relative_to(
                REPO_ROOT
            )
        ),
        "loader_source_sha256": (
            source_sha256
        ),
        "loader_class": (
            "Portable331TrainingInputLoader"
        ),
        "required_internal_methods": list(
            required_internal_methods
        ),
        "blocked_accessors": (
            blocked_accessors
        ),
        "public_holdout_accessors_remain_modified": False,
    }


def _normalize_split_series(
    split: pd.Series,
) -> pd.Series:
    if not isinstance(
        split,
        pd.Series,
    ):
        raise AuthorizedValidationSourceError(
            "dataset_split must be a pandas Series."
        )

    if split.empty:
        raise AuthorizedValidationSourceError(
            "dataset_split cannot be empty."
        )

    normalized = (
        split.astype(
            "string"
        )
        .str.strip()
        .str.upper()
    )

    if normalized.isna().any():
        raise AuthorizedValidationSourceError(
            "dataset_split contains null values."
        )

    return normalized


def locate_validation_window(
    split: pd.Series,
) -> ValidationWindow:
    normalized = _normalize_split_series(
        split
    )

    actual_labels = tuple(
        dict.fromkeys(
            str(
                value
            )
            for value
            in normalized.tolist()
        )
    )

    if (
        actual_labels
        != EXPECTED_SPLIT_ORDER
    ):
        raise AuthorizedValidationSourceError(
            "Portable split order must be exactly "
            "TRAIN -> VALIDATION -> TEST."
        )

    values = normalized.to_numpy(
        dtype=str
    )

    train_positions = np.flatnonzero(
        values
        == "TRAIN"
    )

    validation_positions = np.flatnonzero(
        values
        == "VALIDATION"
    )

    test_positions = np.flatnonzero(
        values
        == "TEST"
    )

    if (
        train_positions.size
        == 0
        or validation_positions.size
        == 0
        or test_positions.size
        == 0
    ):
        raise AuthorizedValidationSourceError(
            "TRAIN, VALIDATION and TEST must all be present."
        )

    validation_start = int(
        validation_positions[
            0
        ]
    )

    validation_stop = int(
        validation_positions[
            -1
        ]
        + 1
    )

    expected_validation_positions = np.arange(
        validation_start,
        validation_stop,
        dtype=np.int64,
    )

    if not np.array_equal(
        validation_positions,
        expected_validation_positions,
    ):
        raise AuthorizedValidationSourceError(
            "VALIDATION rows must form one contiguous block."
        )

    if (
        validation_start
        != train_positions.size
    ):
        raise AuthorizedValidationSourceError(
            "VALIDATION must begin immediately "
            "after the TRAIN block."
        )

    if not np.all(
        values[
            :validation_start
        ]
        == "TRAIN"
    ):
        raise AuthorizedValidationSourceError(
            "Rows before VALIDATION must all be TRAIN."
        )

    if not np.all(
        values[
            validation_stop:
        ]
        == "TEST"
    ):
        raise AuthorizedValidationSourceError(
            "Rows after VALIDATION must all be TEST."
        )

    if (
        test_positions[
            0
        ]
        != validation_stop
    ):
        raise AuthorizedValidationSourceError(
            "TEST must begin immediately "
            "after VALIDATION."
        )

    return ValidationWindow(
        total_rows=int(
            values.shape[
                0
            ]
        ),
        train_rows=int(
            train_positions.size
        ),
        validation_rows=int(
            validation_positions.size
        ),
        test_rows=int(
            test_positions.size
        ),
        validation_start=(
            validation_start
        ),
        validation_stop=(
            validation_stop
        ),
    )


def _unique_columns(
    columns: Sequence[str],
) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in columns:
        name = str(
            value
        )

        if name not in seen:
            seen.add(
                name
            )

            result.append(
                name
            )

    return result


def _validate_feature_columns(
    *,
    loader_class: type,
    feature_columns: Sequence[str],
) -> tuple[str, ...]:
    normalized = tuple(
        str(
            value
        )
        for value
        in feature_columns
    )

    if (
        len(
            normalized
        )
        != EXPECTED_FEATURE_COUNT
    ):
        raise AuthorizedValidationSourceError(
            "Manifest feature count must equal 331."
        )

    if (
        len(
            set(
                normalized
            )
        )
        != EXPECTED_FEATURE_COUNT
    ):
        raise AuthorizedValidationSourceError(
            "Manifest feature columns contain duplicates."
        )

    feature_hash = (
        loader_class
        ._feature_columns_sha256(
            normalized
        )
    )

    if (
        feature_hash
        != EXPECTED_FEATURE_COLUMNS_SHA256
    ):
        raise AuthorizedValidationSourceError(
            "Manifest feature-column SHA256 mismatch."
        )

    return normalized


def _validate_target_columns(
    target_columns: Sequence[str],
) -> tuple[str, ...]:
    normalized = tuple(
        str(
            value
        )
        for value
        in target_columns
    )

    missing = [
        target
        for target
        in EXPECTED_TARGET_COLUMNS
        if target not in normalized
    ]

    if missing:
        raise AuthorizedValidationSourceError(
            "Required target columns missing: "
            f"{missing}"
        )

    return normalized


def _normalize_decision_time(
    series: pd.Series,
) -> np.ndarray:
    try:
        parsed = pd.to_datetime(
            series,
            errors="raise",
            utc=True,
        )

    except Exception as exc:
        raise AuthorizedValidationSourceError(
            "Cannot parse validation decision_time."
        ) from exc

    if parsed.isna().any():
        raise AuthorizedValidationSourceError(
            "Validation decision_time contains null values."
        )

    naive_utc = (
        parsed
        .dt.tz_convert(
            "UTC"
        )
        .dt.tz_localize(
            None
        )
    )

    result = naive_utc.to_numpy(
        dtype="datetime64[ns]"
    )

    result.setflags(
        write=False
    )

    return result


def build_validation_batch_from_frame(
    *,
    frame: pd.DataFrame,
    feature_columns: Sequence[str],
    loader_class: type,
    core_module: ModuleType,
) -> Any:
    if not isinstance(
        frame,
        pd.DataFrame,
    ):
        raise AuthorizedValidationSourceError(
            "Validation frame must be a pandas DataFrame."
        )

    required_columns = {
        EXPECTED_SPLIT_COLUMN,
        EXPECTED_DECISION_TIME_COLUMN,
        *EXPECTED_TARGET_COLUMNS,
        *feature_columns,
    }

    missing = sorted(
        required_columns
        - set(
            frame.columns
        )
    )

    if missing:
        raise AuthorizedValidationSourceError(
            "Validation frame missing columns: "
            f"{missing}"
        )

    split = _normalize_split_series(
        frame[
            EXPECTED_SPLIT_COLUMN
        ]
    )

    if not bool(
        (
            split
            == "VALIDATION"
        ).all()
    ):
        raise AuthorizedValidationSourceError(
            "Value-bearing frame contains "
            "non-VALIDATION rows."
        )

    X = (
        loader_class
        ._numeric_matrix(
            frame=frame,
            feature_columns=feature_columns,
        )
    )

    X = np.asarray(
        X,
        dtype=np.float64,
    )

    target_class = np.asarray(
        loader_class
        ._normalize_target_class_array(
            frame[
                "target_class"
            ]
        ),
        dtype=np.int8,
    )

    target_tradeable = np.asarray(
        loader_class
        ._normalize_target_tradeable_array(
            frame[
                "target_tradeable"
            ]
        ),
        dtype=np.int8,
    )

    decision_time = (
        _normalize_decision_time(
            frame[
                EXPECTED_DECISION_TIME_COLUMN
            ]
        )
    )

    for array in (
        X,
        target_class,
        target_tradeable,
    ):
        array.setflags(
            write=False
        )

    batch = core_module.ValidationBatch(
        X=X,
        target_class=target_class,
        target_tradeable=target_tradeable,
        decision_time=decision_time,
        feature_columns=tuple(
            feature_columns
        ),
        split_name="VALIDATION",
    )

    core_module.validate_validation_batch(
        batch
    )

    return batch


class AuthorizedPortableValidationSource:
    def __init__(
        self,
        canonical_root: str | Path,
        *,
        loader_class: type | None = None,
        read_csv: Callable[..., pd.DataFrame] = (
            pd.read_csv
        ),
        core_module: ModuleType | None = None,
    ) -> None:
        self.canonical_root = Path(
            canonical_root
        )

        self.loader_class = (
            loader_class
            if loader_class is not None
            else _load_loader_class()
        )

        self.read_csv = (
            read_csv
        )

        self.core_module = (
            core_module
            if core_module is not None
            else _load_core_module()
        )

        self.last_evidence: (
            dict[str, Any]
            | None
        ) = None

    def load(
        self,
    ) -> Any:
        loader = self.loader_class(
            self.canonical_root
        )

        try:
            (
                dataset_path,
                manifest_path,
                manifest,
            ) = loader._discover_exact_artifact()

        except Exception as exc:
            raise AuthorizedValidationSourceError(
                "Cannot discover exact frozen portable artifact."
            ) from exc

        try:
            (
                feature_columns,
                target_columns,
            ) = loader._validate_manifest(
                manifest
            )

        except Exception as exc:
            raise AuthorizedValidationSourceError(
                "Frozen portable manifest validation failed."
            ) from exc

        feature_columns = (
            _validate_feature_columns(
                loader_class=(
                    self.loader_class
                ),
                feature_columns=(
                    feature_columns
                ),
            )
        )

        target_columns = (
            _validate_target_columns(
                target_columns
            )
        )

        try:
            split_frame = self.read_csv(
                dataset_path,
                usecols=[
                    EXPECTED_SPLIT_COLUMN
                ],
                low_memory=False,
            )

        except Exception as exc:
            raise AuthorizedValidationSourceError(
                "Cannot perform structural dataset_split read."
            ) from exc

        if (
            list(
                split_frame.columns
            )
            != [
                EXPECTED_SPLIT_COLUMN
            ]
        ):
            raise AuthorizedValidationSourceError(
                "Structural read loaded unexpected columns."
            )

        try:
            loader._validate_split_series(
                split_frame[
                    EXPECTED_SPLIT_COLUMN
                ]
            )

        except Exception as exc:
            raise AuthorizedValidationSourceError(
                "Existing loader split validation failed."
            ) from exc

        window = locate_validation_window(
            split_frame[
                EXPECTED_SPLIT_COLUMN
            ]
        )

        read_columns = _unique_columns(
            (
                EXPECTED_SPLIT_COLUMN,
                EXPECTED_DECISION_TIME_COLUMN,
                *feature_columns,
                *target_columns,
            )
        )

        skiprows = range(
            1,
            window.validation_start
            + 1,
        )

        try:
            validation_frame = self.read_csv(
                dataset_path,
                usecols=read_columns,
                skiprows=skiprows,
                nrows=(
                    window.validation_rows
                ),
                low_memory=False,
            )

        except Exception as exc:
            raise AuthorizedValidationSourceError(
                "Cannot load bounded VALIDATION block."
            ) from exc

        if (
            validation_frame.shape[
                0
            ]
            != window.validation_rows
        ):
            raise AuthorizedValidationSourceError(
                "VALIDATION bounded read row count mismatch."
            )

        batch = build_validation_batch_from_frame(
            frame=validation_frame,
            feature_columns=feature_columns,
            loader_class=(
                self.loader_class
            ),
            core_module=(
                self.core_module
            ),
        )

        self.last_evidence = {
            "dataset_path_name": (
                Path(
                    dataset_path
                ).name
            ),
            "manifest_path_name": (
                Path(
                    manifest_path
                ).name
            ),
            "feature_count": (
                len(
                    feature_columns
                )
            ),
            "feature_columns_sha256": (
                EXPECTED_FEATURE_COLUMNS_SHA256
            ),
            "target_columns": list(
                target_columns
            ),
            "split_window": (
                window.to_dict()
            ),
            "read_policy": {
                "structural_read_columns": [
                    EXPECTED_SPLIT_COLUMN
                ],
                "value_read_split": (
                    "VALIDATION"
                ),
                "value_read_start_data_row": (
                    window.validation_start
                ),
                "value_read_rows": (
                    window.validation_rows
                ),
                "value_read_stop_exclusive": (
                    window.validation_stop
                ),
                "parser_stops_before_test_value_rows": True,
                "test_feature_values_loaded": False,
                "test_target_values_loaded": False,
                "train_feature_values_loaded": False,
                "train_target_values_loaded": False,
            },
        }

        return batch


def build_source_attestation() -> dict[str, Any]:
    loader_contract = (
        inspect_loader_source_contract()
    )

    core = _load_core_module()

    core_attestation = (
        core.build_implementation_attestation()
    )

    if (
        core_attestation.get(
            "valid"
        )
        is not True
    ):
        raise AuthorizedValidationSourceError(
            "One-time validation core attestation is invalid."
        )

    if (
        core_attestation[
            "protocol"
        ][
            "contract_fingerprint_sha256"
        ]
        != EXPECTED_PROTOCOL_FINGERPRINT
    ):
        raise AuthorizedValidationSourceError(
            "Validation core protocol fingerprint mismatch."
        )

    if (
        core_attestation[
            "decision"
        ][
            "real_validation_execution_authorized"
        ]
        is not False
    ):
        raise AuthorizedValidationSourceError(
            "Real validation execution must still "
            "be unauthorized."
        )

    return {
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "valid": True,
        "research_scope": (
            "IMPLEMENT_AUTHORIZED_REAL_VALIDATION_"
            "SOURCE_ADAPTER_WITHOUT_EXECUTING_ANY_"
            "REAL_VALIDATION_OR_TEST_VALUE_READ"
        ),
        "loader_contract": (
            loader_contract
        ),
        "source_contract": {
            "split_order_required": list(
                EXPECTED_SPLIT_ORDER
            ),
            "structural_read_only_before_value_block": True,
            "structural_read_columns": [
                EXPECTED_SPLIT_COLUMN
            ],
            "validation_block_must_be_contiguous": True,
            "validation_must_follow_train": True,
            "test_must_follow_validation": True,
            "value_read_uses_skiprows": True,
            "value_read_uses_nrows": True,
            "value_parser_stops_at_validation_end": True,
            "feature_order_from_frozen_manifest": True,
            "feature_columns_sha256": (
                EXPECTED_FEATURE_COLUMNS_SHA256
            ),
            "feature_count": (
                EXPECTED_FEATURE_COUNT
            ),
            "existing_loader_numeric_matrix_reused": True,
            "existing_loader_target_normalizers_reused": True,
            "public_loader_holdout_accessors_modified": False,
            "test_value_access_path_present": False,
        },
        "core_contract": {
            "protocol_fingerprint_sha256": (
                EXPECTED_PROTOCOL_FINGERPRINT
            ),
            "model_artifact_sha256": (
                EXPECTED_MODEL_ARTIFACT_SHA256
            ),
            "one_time_ledger_present": True,
            "post_read_rerun_blocked": True,
        },
        "decision": {
            "status": (
                "AUTHORIZED_VALIDATION_SOURCE_"
                "IMPLEMENTED_NOT_REAL_EXECUTED"
            ),
            "validation_source_implementation_confirmed": True,
            "validation_source_synthetic_testing_authorized": True,
            "real_validation_source_executed": False,
            "real_validation_values_loaded": False,
            "real_validation_metrics_computed": False,
            "real_validation_execution_authorized": False,
            "test_access_authorized": False,
            "shadow_authorized": False,
            "live_authorized": False,
            "next_action": (
                "SYNTHETICALLY_TEST_BOUNDED_"
                "VALIDATION_SOURCE_THEN_BUILD_"
                "FINAL_ONE_SHOT_REAL_VALIDATION_RUNNER"
            ),
        },
        "scientific_policy": {
            "dataset_structural_read_performed_in_this_attestation": False,
            "train_feature_values_loaded": False,
            "train_target_values_loaded": False,
            "portable_validation_feature_values_loaded": False,
            "portable_validation_target_values_loaded": False,
            "portable_validation_metrics_computed": False,
            "portable_test_feature_values_loaded": False,
            "portable_test_target_values_loaded": False,
            "portable_test_metrics_computed": False,
            "model_fit_performed": False,
            "model_refit_performed": False,
            "threshold_search_performed": False,
            "probability_calibration_performed": False,
            "feature_selection_performed": False,
            "candidate_registry_changed": False,
            "model_artifact_modified": False,
            "loader_source_modified": False,
            "execution_integration_modified": False,
            "risk_engine_modified": False,
            "orders_sent": False,
            "shadow_authorized": False,
            "live_authorized": False,
        },
    }


def _write_json_atomic(
    path: Path,
    payload: Mapping[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix
        + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary.replace(
        path
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Attest the authorized portable 331 "
            "VALIDATION source adapter without "
            "executing any real holdout value read."
        )
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )

    args = parser.parse_args()

    try:
        report = build_source_attestation()

        _write_json_atomic(
            args.output,
            report,
        )

    except Exception as exc:
        failure = {
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "valid": False,
            "reason": (
                "AUTHORIZED_VALIDATION_SOURCE_"
                "ATTESTATION_FAILED"
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
                "portable_validation_feature_values_loaded": False,
                "portable_validation_target_values_loaded": False,
                "portable_test_feature_values_loaded": False,
                "portable_test_target_values_loaded": False,
                "real_validation_execution_authorized": False,
                "live_authorized": False,
            },
        }

        _write_json_atomic(
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

    print(
        json.dumps(
            {
                "analysis_version": (
                    report[
                        "analysis_version"
                    ]
                ),
                "valid": True,
                "loader_source_sha256": (
                    report[
                        "loader_contract"
                    ][
                        "loader_source_sha256"
                    ]
                ),
                "source_contract": (
                    report[
                        "source_contract"
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