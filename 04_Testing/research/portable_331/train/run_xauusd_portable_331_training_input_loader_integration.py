from __future__ import annotations

import importlib
import json
import sys

from pathlib import Path
from typing import Any, Callable, Sequence, cast

import numpy as np


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
    "XAUUSD_PORTABLE_331_TRAINING_INPUT_LOADER_INTEGRATION_V1"
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

Portable331TrainingInputLoaderError = (
    loader_module
    .Portable331TrainingInputLoaderError
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


EXPECTED_SPLIT_ROWS = {
    "TRAIN": (
        EXPECTED_TRAIN_ROWS
    ),
    "VALIDATION": (
        EXPECTED_VALIDATION_ROWS
    ),
    "TEST": (
        EXPECTED_TEST_ROWS
    ),
}


EXPECTED_FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256 = (
    "9ffb72759499cfc202e88cfdbd61b42cee5b5c7cbb7db5870470453caa5ed2c5"
)


EXPECTED_RETAINED_FEATURE = (
    "m5_tick_volume_ratio20"
)

FORBIDDEN_DROPPED_FEATURES = {
    "m5_spread_points",
    "m5_tick_volume_log1p",
}


UNAUTHORIZED_ACCESSORS = (
    (
        "load_train_targets",
        "TRAIN_TARGET_ACCESS_NOT_AUTHORIZED",
    ),
    (
        "load_train_supervised",
        "SUPERVISED_TRAIN_INPUT_ACCESS_NOT_AUTHORIZED",
    ),
    (
        "load_validation_features",
        "VALIDATION_FEATURE_ACCESS_NOT_AUTHORIZED",
    ),
    (
        "load_validation_targets",
        "VALIDATION_TARGET_ACCESS_NOT_AUTHORIZED",
    ),
    (
        "load_test_features",
        "TEST_FEATURE_ACCESS_NOT_AUTHORIZED",
    ),
    (
        "load_test_targets",
        "TEST_TARGET_ACCESS_NOT_AUTHORIZED",
    ),
)


def _require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise RuntimeError(
            reason
        )


def _normalize_usecols(
    value: Any,
) -> list[str] | None:

    if value is None:
        return None

    if isinstance(
        value,
        str,
    ):
        return [
            value
        ]

    if isinstance(
        value,
        Sequence,
    ):
        return [
            str(
                item
            )
            for item
            in value
        ]

    return None


def _audit_real_loader_reads(
    loader: Any,
) -> tuple[
    dict[str, Any],
    tuple[
        dict[str, Any],
        Any,
    ],
]:

    original_read_csv: Callable[..., Any] = (
        loader_module
        .pd
        .read_csv
    )

    read_calls: list[
        dict[str, Any]
    ] = []

    def audited_read_csv(
        *args: Any,
        **kwargs: Any,
    ) -> Any:

        usecols = (
            _normalize_usecols(
                kwargs.get(
                    "usecols"
                )
            )
        )

        nrows_raw = kwargs.get(
            "nrows"
        )

        if nrows_raw is None:
            nrows: int | None = (
                None
            )

        else:
            nrows = int(
                nrows_raw
            )

        read_calls.append(
            {
                "usecols": (
                    usecols
                ),
                "nrows": (
                    nrows
                ),
            }
        )

        return original_read_csv(
            *args,
            **kwargs,
        )

    loader_module.pd.read_csv = (
        audited_read_csv
    )

    try:

        contract_inspection_raw = (
            loader.inspect_contract()
        )

        if not isinstance(
            contract_inspection_raw,
            dict,
        ):
            raise RuntimeError(
                "LOADER_CONTRACT_INSPECTION_NOT_DICT"
            )

        contract_inspection: dict[
            str,
            Any
        ] = (
            contract_inspection_raw
        )

        batch = (
            loader.load_train_features()
        )

    finally:

        loader_module.pd.read_csv = (
            original_read_csv
        )

    _require(
        len(
            read_calls
        )
        ==
        3,
        (
            "UNEXPECTED_PANDAS_READ_CALL_COUNT:"
            f"{len(read_calls)}"
        ),
    )

    structural_calls = [
        call
        for call
        in read_calls
        if (
            call.get(
                "nrows"
            )
            is None
        )
    ]

    train_feature_calls = [
        call
        for call
        in read_calls
        if (
            call.get(
                "nrows"
            )
            ==
            EXPECTED_TRAIN_ROWS
        )
    ]

    _require(
        len(
            structural_calls
        )
        ==
        2,
        (
            "STRUCTURAL_READ_CALL_COUNT_INVALID:"
            f"{len(structural_calls)}"
        ),
    )

    _require(
        len(
            train_feature_calls
        )
        ==
        1,
        (
            "TRAIN_FEATURE_READ_CALL_COUNT_INVALID:"
            f"{len(train_feature_calls)}"
        ),
    )

    for call in (
        structural_calls
    ):

        structural_usecols = (
            call.get(
                "usecols"
            )
        )

        if not isinstance(
            structural_usecols,
            list,
        ):
            raise RuntimeError(
                "STRUCTURAL_READ_USECOLS_MISSING"
            )

        structural_usecols_list = [
            str(
                item
            )
            for item
            in structural_usecols
        ]

        _require(
            structural_usecols_list
            ==
            [
                "dataset_split"
            ],
            (
                "FULL_DATASET_READ_EXCEEDED_STRUCTURAL_POLICY:"
                f"{structural_usecols_list}"
            ),
        )

    train_feature_call = (
        train_feature_calls[
            0
        ]
    )

    train_usecols_raw = (
        train_feature_call.get(
            "usecols"
        )
    )

    if not isinstance(
        train_usecols_raw,
        list,
    ):
        raise RuntimeError(
            "TRAIN_FEATURE_READ_USECOLS_MISSING"
        )

    train_usecols_list: list[str] = [
        str(
            item
        )
        for item
        in train_usecols_raw
    ]

    _require(
        len(
            train_usecols_list
        )
        ==
        (
            EXPECTED_FEATURE_COUNT
            +
            1
        ),
        (
            "TRAIN_FEATURE_READ_COLUMN_COUNT_INVALID:"
            f"{len(train_usecols_list)}"
        ),
    )

    _require(
        train_usecols_list[
            0
        ]
        ==
        "decision_time",
        "TRAIN_FEATURE_READ_DECISION_TIME_NOT_FIRST",
    )

    batch_feature_columns = [
        str(
            feature
        )
        for feature
        in batch.feature_columns
    ]

    _require(
        train_usecols_list[
            1:
        ]
        ==
        batch_feature_columns,
        "TRAIN_FEATURE_READ_ORDER_DIFFERS_FROM_BATCH_CONTRACT",
    )

    target_columns_raw = (
        contract_inspection.get(
            "target_columns_present_in_manifest"
        )
    )

    if not isinstance(
        target_columns_raw,
        list,
    ):
        raise RuntimeError(
            "CONTRACT_INSPECTION_TARGET_COLUMNS_NOT_LIST"
        )

    target_columns = {
        str(
            column
        )
        for column
        in target_columns_raw
    }

    read_target_columns = sorted(
        target_columns
        &
        set(
            train_usecols_list
        )
    )

    _require(
        not read_target_columns,
        (
            "TARGET_COLUMNS_LOADED_DURING_TRAIN_FEATURE_ACCESS:"
            f"{read_target_columns}"
        ),
    )

    for call in (
        read_calls
    ):

        usecols_raw = (
            call.get(
                "usecols"
            )
        )

        if usecols_raw is None:
            raise RuntimeError(
                "READ_CALL_WITHOUT_EXPLICIT_USECOLS"
            )

        if not isinstance(
            usecols_raw,
            list,
        ):
            raise RuntimeError(
                "READ_CALL_USECOLS_NOT_LIST"
            )

        usecols_list = [
            str(
                item
            )
            for item
            in usecols_raw
        ]

        forbidden_in_call = sorted(
            target_columns
            &
            set(
                usecols_list
            )
        )

        _require(
            not forbidden_in_call,
            (
                "TARGET_COLUMN_READ_DETECTED:"
                f"{forbidden_in_call}"
            ),
        )

    return (
        {
            "read_call_count": (
                len(
                    read_calls
                )
            ),
            "full_dataset_structural_read_count": (
                len(
                    structural_calls
                )
            ),
            "train_feature_prefix_read_count": (
                len(
                    train_feature_calls
                )
            ),
            "full_dataset_columns_loaded": [
                "dataset_split"
            ],
            "train_feature_read_nrows": (
                EXPECTED_TRAIN_ROWS
            ),
            "train_feature_column_count_including_decision_time": (
                len(
                    train_usecols_list
                )
            ),
            "target_columns_loaded": (
                False
            ),
            "validation_feature_values_loaded": (
                False
            ),
            "test_feature_values_loaded": (
                False
            ),
            "read_policy_confirmed": (
                True
            ),
        },
        (
            contract_inspection,
            batch,
        ),
    )


def _validate_contract_inspection(
    inspection: dict[str, Any],
) -> dict[str, Any]:

    _require(
        str(
            inspection.get(
                "dataset_id",
                "",
            )
        )
        ==
        EXPECTED_DATASET_ID,
        "INSPECTION_DATASET_ID_MISMATCH",
    )

    _require(
        str(
            inspection.get(
                "dataset_sha256",
                "",
            )
        )
        ==
        EXPECTED_DATASET_SHA256,
        "INSPECTION_DATASET_SHA256_MISMATCH",
    )

    _require(
        str(
            inspection.get(
                "manifest_sha256",
                "",
            )
        )
        ==
        EXPECTED_MANIFEST_SHA256,
        "INSPECTION_MANIFEST_SHA256_MISMATCH",
    )

    _require(
        str(
            inspection.get(
                "training_contract_version",
                "",
            )
        )
        ==
        EXPECTED_FEATURE_CONTRACT,
        "INSPECTION_FEATURE_CONTRACT_MISMATCH",
    )

    _require(
        str(
            inspection.get(
                "trainer_input_contract_version",
                "",
            )
        )
        ==
        EXPECTED_TRAINER_INPUT_CONTRACT,
        "INSPECTION_TRAINER_INPUT_CONTRACT_MISMATCH",
    )

    _require(
        str(
            inspection.get(
                "trainer_input_contract_fingerprint_sha256",
                "",
            )
        )
        ==
        EXPECTED_TRAINER_INPUT_CONTRACT_FINGERPRINT_SHA256,
        "INSPECTION_TRAINER_INPUT_FINGERPRINT_MISMATCH",
    )

    _require(
        int(
            inspection.get(
                "feature_count",
                -1,
            )
        )
        ==
        EXPECTED_FEATURE_COUNT,
        "INSPECTION_FEATURE_COUNT_MISMATCH",
    )

    _require(
        str(
            inspection.get(
                "feature_columns_sha256",
                "",
            )
        )
        ==
        EXPECTED_FEATURE_COLUMNS_SHA256,
        "INSPECTION_FEATURE_COLUMNS_SHA256_MISMATCH",
    )

    split_rows_raw = inspection.get(
        "split_rows"
    )

    if not isinstance(
        split_rows_raw,
        dict,
    ):
        raise RuntimeError(
            "INSPECTION_SPLIT_ROWS_MISSING"
        )

    split_rows: dict[
        str,
        int
    ] = {}

    for (
        key,
        value,
    ) in split_rows_raw.items():

        if value is None:
            raise RuntimeError(
                (
                    "INSPECTION_SPLIT_ROW_VALUE_NONE:"
                    f"{key}"
                )
            )

        split_rows[
            str(
                key
            )
        ] = int(
            value
        )

    _require(
        split_rows
        ==
        EXPECTED_SPLIT_ROWS,
        (
            "INSPECTION_SPLIT_ROWS_MISMATCH:"
            f"{split_rows}"
        ),
    )

    _require(
        not bool(
            inspection.get(
                "target_values_loaded",
                True,
            )
        ),
        "INSPECTION_TARGET_VALUES_UNEXPECTEDLY_LOADED",
    )

    _require(
        not bool(
            inspection.get(
                "validation_feature_values_loaded",
                True,
            )
        ),
        "INSPECTION_VALIDATION_FEATURES_UNEXPECTEDLY_LOADED",
    )

    _require(
        not bool(
            inspection.get(
                "test_feature_values_loaded",
                True,
            )
        ),
        "INSPECTION_TEST_FEATURES_UNEXPECTEDLY_LOADED",
    )

    _require(
        not bool(
            inspection.get(
                "live_authorized",
                True,
            )
        ),
        "INSPECTION_UNEXPECTEDLY_LIVE_AUTHORIZED",
    )

    target_columns_raw = inspection.get(
        "target_columns_present_in_manifest"
    )

    if not isinstance(
        target_columns_raw,
        list,
    ):
        raise RuntimeError(
            "INSPECTION_TARGET_COLUMN_METADATA_MISSING"
        )

    target_columns: list[str] = [
        str(
            column
        )
        for column
        in target_columns_raw
    ]

    _require(
        "target_class"
        in
        target_columns,
        "TARGET_CLASS_METADATA_MISSING",
    )

    _require(
        "target_tradeable"
        in
        target_columns,
        "TARGET_TRADEABLE_METADATA_MISSING",
    )

    return {
        "artifact_identity_confirmed": (
            True
        ),
        "feature_contract_confirmed": (
            True
        ),
        "trainer_input_contract_confirmed": (
            True
        ),
        "feature_count": (
            EXPECTED_FEATURE_COUNT
        ),
        "split_rows": (
            split_rows
        ),
        "target_metadata_present": (
            True
        ),
        "target_values_loaded": (
            False
        ),
        "live_authorized": (
            False
        ),
    }


def _validate_train_batch(
    batch: Any,
) -> dict[str, Any]:

    _require(
        str(
            batch.dataset_id
        )
        ==
        EXPECTED_DATASET_ID,
        "BATCH_DATASET_ID_MISMATCH",
    )

    _require(
        str(
            batch.dataset_sha256
        )
        ==
        EXPECTED_DATASET_SHA256,
        "BATCH_DATASET_SHA256_MISMATCH",
    )

    _require(
        str(
            batch.manifest_sha256
        )
        ==
        EXPECTED_MANIFEST_SHA256,
        "BATCH_MANIFEST_SHA256_MISMATCH",
    )

    _require(
        str(
            batch.training_contract_version
        )
        ==
        EXPECTED_FEATURE_CONTRACT,
        "BATCH_FEATURE_CONTRACT_MISMATCH",
    )

    _require(
        str(
            batch.trainer_input_contract_version
        )
        ==
        EXPECTED_TRAINER_INPUT_CONTRACT,
        "BATCH_TRAINER_INPUT_CONTRACT_MISMATCH",
    )

    _require(
        str(
            batch.trainer_input_contract_fingerprint_sha256
        )
        ==
        EXPECTED_TRAINER_INPUT_CONTRACT_FINGERPRINT_SHA256,
        "BATCH_TRAINER_INPUT_FINGERPRINT_MISMATCH",
    )

    _require(
        int(
            batch.row_count
        )
        ==
        EXPECTED_TRAIN_ROWS,
        "BATCH_TRAIN_ROW_COUNT_MISMATCH",
    )

    feature_columns = tuple(
        str(
            feature
        )
        for feature
        in batch.feature_columns
    )

    _require(
        len(
            feature_columns
        )
        ==
        EXPECTED_FEATURE_COUNT,
        "BATCH_FEATURE_COUNT_MISMATCH",
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
        "BATCH_FEATURE_COLUMNS_NOT_UNIQUE",
    )

    _require(
        str(
            batch.feature_columns_sha256
        )
        ==
        EXPECTED_FEATURE_COLUMNS_SHA256,
        "BATCH_FEATURE_COLUMNS_SHA256_MISMATCH",
    )

    observed_feature_sha256 = (
        Portable331TrainingInputLoader
        ._feature_columns_sha256(
            feature_columns
        )
    )

    _require(
        observed_feature_sha256
        ==
        EXPECTED_FEATURE_COLUMNS_SHA256,
        "BATCH_RECOMPUTED_FEATURE_COLUMNS_SHA256_MISMATCH",
    )

    _require(
        str(
            batch.train_input_fingerprint_sha256
        )
        ==
        EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256,
        "BATCH_TRAIN_INPUT_FINGERPRINT_MISMATCH",
    )

    _require(
        EXPECTED_RETAINED_FEATURE
        in
        feature_columns,
        "BATCH_RETAINED_RELATIVE_VOLUME_FEATURE_MISSING",
    )

    unexpected_dropped = sorted(
        FORBIDDEN_DROPPED_FEATURES
        &
        set(
            feature_columns
        )
    )

    _require(
        not unexpected_dropped,
        (
            "BATCH_DROPPED_FEATURES_PRESENT:"
            f"{unexpected_dropped}"
        ),
    )

    X_raw = batch.X

    if not isinstance(
        X_raw,
        np.ndarray,
    ):
        raise RuntimeError(
            "BATCH_X_NOT_NUMPY_ARRAY"
        )

    X: np.ndarray = (
        X_raw
    )

    _require(
        X.dtype
        ==
        np.dtype(
            np.float64
        ),
        (
            "BATCH_X_DTYPE_MISMATCH:"
            f"{X.dtype}"
        ),
    )

    _require(
        X.shape
        ==
        (
            EXPECTED_TRAIN_ROWS,
            EXPECTED_FEATURE_COUNT,
        ),
        (
            "BATCH_X_SHAPE_MISMATCH:"
            f"{X.shape}"
        ),
    )

    nonfinite_count = int(
        (
            ~np.isfinite(
                X
            )
        )
        .sum()
    )

    _require(
        nonfinite_count
        ==
        0,
        (
            "BATCH_X_NONFINITE_VALUES:"
            f"{nonfinite_count}"
        ),
    )

    _require(
        not bool(
            X.flags.writeable
        ),
        "BATCH_X_NOT_READ_ONLY",
    )

    decision_time_raw = (
        batch.decision_time
    )

    if not isinstance(
        decision_time_raw,
        np.ndarray,
    ):
        raise RuntimeError(
            "BATCH_DECISION_TIME_NOT_NUMPY_ARRAY"
        )

    decision_time: np.ndarray = (
        decision_time_raw
    )

    _require(
        decision_time.shape
        ==
        (
            EXPECTED_TRAIN_ROWS,
        ),
        (
            "BATCH_DECISION_TIME_SHAPE_MISMATCH:"
            f"{decision_time.shape}"
        ),
    )

    _require(
        not bool(
            decision_time.flags.writeable
        ),
        "BATCH_DECISION_TIME_NOT_READ_ONLY",
    )

    decision_time_strings = (
        decision_time.astype(
            str
        )
    )

    unique_decision_time_count = int(
        np.unique(
            decision_time_strings
        ).size
    )

    _require(
        unique_decision_time_count
        ==
        EXPECTED_TRAIN_ROWS,
        (
            "BATCH_DUPLICATE_DECISION_TIME:"
            f"{unique_decision_time_count}"
        ),
    )

    matrix_bytes = int(
        X.nbytes
    )

    return {
        "row_count": (
            EXPECTED_TRAIN_ROWS
        ),
        "feature_count": (
            EXPECTED_FEATURE_COUNT
        ),
        "matrix_shape": [
            int(
                X.shape[
                    0
                ]
            ),
            int(
                X.shape[
                    1
                ]
            ),
        ],
        "matrix_dtype": (
            str(
                X.dtype
            )
        ),
        "matrix_nonfinite_value_count": (
            nonfinite_count
        ),
        "matrix_read_only": (
            True
        ),
        "decision_time_read_only": (
            True
        ),
        "decision_time_unique_count": (
            unique_decision_time_count
        ),
        "feature_columns_sha256": (
            observed_feature_sha256
        ),
        "train_input_fingerprint_sha256": (
            str(
                batch.train_input_fingerprint_sha256
            )
        ),
        "retained_relative_volume_feature_present": (
            True
        ),
        "dropped_parent_features_absent": (
            True
        ),
        "matrix_memory_bytes": (
            matrix_bytes
        ),
    }


def _validate_fail_closed_accessors(
    loader: Any,
) -> dict[str, Any]:

    confirmed: list[str] = []

    for (
        method_name,
        expected_message,
    ) in UNAUTHORIZED_ACCESSORS:

        method_raw = getattr(
            loader,
            method_name,
            None,
        )

        if not callable(
            method_raw
        ):
            raise RuntimeError(
                (
                    "UNAUTHORIZED_ACCESSOR_MISSING:"
                    f"{method_name}"
                )
            )

        method_callable = cast(
            Callable[
                [],
                Any,
            ],
            method_raw,
        )

        try:

            method_callable()

        except (
            Portable331TrainingInputLoaderError
        ) as exc:

            _require(
                expected_message
                in
                str(
                    exc
                ),
                (
                    "UNAUTHORIZED_ACCESSOR_ERROR_MISMATCH:"
                    f"{method_name}:"
                    f"{exc}"
                ),
            )

            confirmed.append(
                method_name
            )

        else:

            raise RuntimeError(
                (
                    "UNAUTHORIZED_ACCESSOR_DID_NOT_FAIL_CLOSED:"
                    f"{method_name}"
                )
            )

    return {
        "fail_closed_accessor_count": (
            len(
                confirmed
            )
        ),
        "confirmed_accessors": (
            confirmed
        ),
        "train_target_access_blocked": (
            True
        ),
        "supervised_train_access_blocked": (
            True
        ),
        "validation_feature_access_blocked": (
            True
        ),
        "validation_target_access_blocked": (
            True
        ),
        "test_feature_access_blocked": (
            True
        ),
        "test_target_access_blocked": (
            True
        ),
    }


def run_integration(
) -> dict[str, Any]:

    loader = (
        Portable331TrainingInputLoader(
            canonical_root=(
                ROOT_DIR
            )
        )
    )

    (
        read_policy_validation,
        loader_outputs,
    ) = (
        _audit_real_loader_reads(
            loader
        )
    )

    (
        contract_inspection,
        batch,
    ) = (
        loader_outputs
    )

    contract_validation = (
        _validate_contract_inspection(
            contract_inspection
        )
    )

    batch_validation = (
        _validate_train_batch(
            batch
        )
    )

    fail_closed_validation = (
        _validate_fail_closed_accessors(
            loader
        )
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_PORTABLE_331_TRAINING_INPUT_LOADER_INTEGRATION"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "research_scope": (
            "REAL_FROZEN_PORTABLE_ARTIFACT_TRAIN_FEATURE_LOADER_"
            "INTEGRATION_WITH_FAIL_CLOSED_HOLDOUT_AND_TARGET_ACCESS"
        ),
        "decision": {
            "status": (
                "XAUUSD_PORTABLE_331_TRAIN_FEATURE_LOADER_INTEGRATION_CONFIRMED"
            ),
            "reason": (
                "THE_ARCHITECTURE_NEUTRAL_LOADER_DISCOVERED_THE_"
                "EXACT_FROZEN_PORTABLE_ARTIFACT_VALIDATED_ITS_"
                "MANIFEST_AND_SPLIT_STRUCTURE_AND_LOADED_ONLY_THE_"
                "69966_TRAIN_ROWS_OF_THE_331_FEATURE_MODEL_MATRIX"
            ),
            "trainer_input_contract_version": (
                EXPECTED_TRAINER_INPUT_CONTRACT
            ),
            "trainer_input_contract_fingerprint_sha256": (
                EXPECTED_TRAINER_INPUT_CONTRACT_FINGERPRINT_SHA256
            ),
            "feature_contract_version": (
                EXPECTED_FEATURE_CONTRACT
            ),
            "train_rows": (
                EXPECTED_TRAIN_ROWS
            ),
            "feature_count": (
                EXPECTED_FEATURE_COUNT
            ),
            "train_feature_loading_confirmed": (
                True
            ),
            "train_target_access_confirmed": (
                False
            ),
            "validation_feature_access_confirmed": (
                False
            ),
            "test_feature_access_confirmed": (
                False
            ),
            "model_architecture_selected": (
                False
            ),
            "scaler_fit": (
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
                "DESIGN_TRAIN_ONLY_SUPERVISED_TARGET_ACCESS_"
                "CONTRACT_WITHOUT_MODEL_FIT"
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
            "feature_contract_version": (
                EXPECTED_FEATURE_CONTRACT
            ),
            "feature_columns_sha256": (
                EXPECTED_FEATURE_COLUMNS_SHA256
            ),
            "train_input_fingerprint_sha256": (
                EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256
            ),
            "filesystem_path_emitted": (
                False
            ),
        },
        "contract_validation": (
            contract_validation
        ),
        "read_policy_validation": (
            read_policy_validation
        ),
        "train_feature_batch_validation": (
            batch_validation
        ),
        "fail_closed_validation": (
            fail_closed_validation
        ),
        "scientific_policy": {
            "portable_manifest_loaded": (
                True
            ),
            "portable_dataset_bytes_hashed": (
                True
            ),
            "full_dataset_columns_loaded": [
                "dataset_split"
            ],
            "train_feature_values_loaded": (
                True
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
            "feature_pipeline_modified": (
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
            "if_integration_confirmed": (
                "DESIGN_TRAIN_ONLY_SUPERVISED_TARGET_ACCESS_"
                "CONTRACT_WITHOUT_MODEL_FIT"
            ),
            "loader_reimplementation_required": (
                False
            ),
            "portable_dataset_rebuild_required": (
                False
            ),
            "feature_contract_change_required": (
                False
            ),
            "train_target_access_currently_authorized": (
                False
            ),
            "validation_feature_access_currently_authorized": (
                False
            ),
            "test_feature_access_currently_authorized": (
                False
            ),
            "model_training_authorized": (
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
            run_integration()
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_PORTABLE_331_TRAINING_INPUT_"
                        "LOADER_INTEGRATION_FAILED"
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
                    "train_target_values_loaded": (
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