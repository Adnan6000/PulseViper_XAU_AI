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
    "XAUUSD_PORTABLE_331_TRAIN_TARGET_LOADER_INTEGRATION_V1"
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

PortableTrainingFeatureProjector = (
    loader_module
    .PortableTrainingFeatureProjector
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


EXPECTED_FEATURE_COUNT = (
    331
)

EXPECTED_TRAIN_ROWS = (
    69966
)


EXPECTED_FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256 = (
    "9ffb72759499cfc202e88cfdbd61b42cee5b5c7cbb7db5870470453caa5ed2c5"
)


EXPECTED_TARGET_COLUMNS = (
    "target_class",
    "target_tradeable",
)


EXPECTED_TARGET_CLASS_VALUES = {
    -1,
    0,
    1,
}

EXPECTED_TARGET_TRADEABLE_VALUES = {
    0,
    1,
}


FAIL_CLOSED_ACCESSORS = (
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


def _validate_artifact_immutable_before_after(
    *,
    dataset_path: Path,
    manifest_path: Path,
    dataset_sha256_before: str,
    manifest_sha256_before: str,
) -> dict[str, Any]:

    dataset_sha256_after = (
        PortableTrainingFeatureProjector
        ._sha256_file(
            dataset_path
        )
    )

    manifest_sha256_after = (
        PortableTrainingFeatureProjector
        ._sha256_file(
            manifest_path
        )
    )

    _require(
        dataset_sha256_before
        ==
        EXPECTED_DATASET_SHA256,
        "PORTABLE_DATASET_HASH_BEFORE_MISMATCH",
    )

    _require(
        manifest_sha256_before
        ==
        EXPECTED_MANIFEST_SHA256,
        "PORTABLE_MANIFEST_HASH_BEFORE_MISMATCH",
    )

    _require(
        dataset_sha256_after
        ==
        EXPECTED_DATASET_SHA256,
        "PORTABLE_DATASET_HASH_AFTER_MISMATCH",
    )

    _require(
        manifest_sha256_after
        ==
        EXPECTED_MANIFEST_SHA256,
        "PORTABLE_MANIFEST_HASH_AFTER_MISMATCH",
    )

    _require(
        dataset_sha256_before
        ==
        dataset_sha256_after,
        "PORTABLE_DATASET_MODIFIED_DURING_INTEGRATION",
    )

    _require(
        manifest_sha256_before
        ==
        manifest_sha256_after,
        "PORTABLE_MANIFEST_MODIFIED_DURING_INTEGRATION",
    )

    return {
        "dataset_immutable_before_after": (
            True
        ),
        "manifest_immutable_before_after": (
            True
        ),
        "dataset_sha256": (
            dataset_sha256_after
        ),
        "manifest_sha256": (
            manifest_sha256_after
        ),
    }


def _audit_loader_reads(
    loader: Any,
) -> tuple[
    dict[str, Any],
    Any,
    Any,
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

        feature_batch = (
            loader.load_train_features()
        )

        target_batch = (
            loader.load_train_targets()
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
        4,
        (
            "UNEXPECTED_PANDAS_READ_CALL_COUNT:"
            f"{len(read_calls)}"
        ),
    )

    structural_calls: list[
        dict[str, Any]
    ] = []

    train_feature_calls: list[
        dict[str, Any]
    ] = []

    train_target_calls: list[
        dict[str, Any]
    ] = []

    for call in (
        read_calls
    ):

        usecols_raw = (
            call.get(
                "usecols"
            )
        )

        nrows_raw = (
            call.get(
                "nrows"
            )
        )

        if not isinstance(
            usecols_raw,
            list,
        ):
            raise RuntimeError(
                "READ_CALL_USECOLS_NOT_LIST"
            )

        usecols = [
            str(
                item
            )
            for item
            in usecols_raw
        ]

        if nrows_raw is None:

            structural_calls.append(
                {
                    "usecols": (
                        usecols
                    ),
                    "nrows": (
                        None
                    ),
                }
            )

            continue

        if not isinstance(
            nrows_raw,
            int,
        ):
            raise RuntimeError(
                "READ_CALL_NROWS_NOT_INTEGER"
            )

        if (
            nrows_raw
            !=
            EXPECTED_TRAIN_ROWS
        ):
            raise RuntimeError(
                (
                    "NON_TRAIN_PREFIX_ROW_READ_DETECTED:"
                    f"{nrows_raw}"
                )
            )

        if (
            usecols
            ==
            [
                "decision_time",
                *EXPECTED_TARGET_COLUMNS,
            ]
        ):

            train_target_calls.append(
                {
                    "usecols": (
                        usecols
                    ),
                    "nrows": (
                        nrows_raw
                    ),
                }
            )

        else:

            train_feature_calls.append(
                {
                    "usecols": (
                        usecols
                    ),
                    "nrows": (
                        nrows_raw
                    ),
                }
            )

    _require(
        len(
            structural_calls
        )
        ==
        2,
        (
            "STRUCTURAL_READ_COUNT_INVALID:"
            f"{len(structural_calls)}"
        ),
    )

    for call in (
        structural_calls
    ):

        structural_usecols_raw = (
            call.get(
                "usecols"
            )
        )

        if not isinstance(
            structural_usecols_raw,
            list,
        ):
            raise RuntimeError(
                "STRUCTURAL_USECOLS_NOT_LIST"
            )

        structural_usecols = [
            str(
                item
            )
            for item
            in structural_usecols_raw
        ]

        _require(
            structural_usecols
            ==
            [
                "dataset_split"
            ],
            (
                "FULL_DATASET_READ_EXCEEDED_STRUCTURAL_SCOPE:"
                f"{structural_usecols}"
            ),
        )

    _require(
        len(
            train_feature_calls
        )
        ==
        1,
        (
            "TRAIN_FEATURE_READ_COUNT_INVALID:"
            f"{len(train_feature_calls)}"
        ),
    )

    _require(
        len(
            train_target_calls
        )
        ==
        1,
        (
            "TRAIN_TARGET_READ_COUNT_INVALID:"
            f"{len(train_target_calls)}"
        ),
    )

    feature_call = (
        train_feature_calls[
            0
        ]
    )

    feature_usecols_raw = (
        feature_call.get(
            "usecols"
        )
    )

    if not isinstance(
        feature_usecols_raw,
        list,
    ):
        raise RuntimeError(
            "TRAIN_FEATURE_USECOLS_NOT_LIST"
        )

    feature_usecols = [
        str(
            item
        )
        for item
        in feature_usecols_raw
    ]

    _require(
        len(
            feature_usecols
        )
        ==
        (
            EXPECTED_FEATURE_COUNT
            +
            1
        ),
        (
            "TRAIN_FEATURE_COLUMN_COUNT_INVALID:"
            f"{len(feature_usecols)}"
        ),
    )

    _require(
        feature_usecols[
            0
        ]
        ==
        "decision_time",
        "TRAIN_FEATURE_DECISION_TIME_NOT_FIRST",
    )

    forbidden_targets_in_feature_read = sorted(
        set(
            EXPECTED_TARGET_COLUMNS
        )
        &
        set(
            feature_usecols
        )
    )

    _require(
        not forbidden_targets_in_feature_read,
        (
            "TARGET_COLUMNS_FOUND_IN_FEATURE_READ:"
            f"{forbidden_targets_in_feature_read}"
        ),
    )

    target_call = (
        train_target_calls[
            0
        ]
    )

    target_usecols_raw = (
        target_call.get(
            "usecols"
        )
    )

    if not isinstance(
        target_usecols_raw,
        list,
    ):
        raise RuntimeError(
            "TRAIN_TARGET_USECOLS_NOT_LIST"
        )

    target_usecols = [
        str(
            item
        )
        for item
        in target_usecols_raw
    ]

    _require(
        target_usecols
        ==
        [
            "decision_time",
            "target_class",
            "target_tradeable",
        ],
        (
            "TRAIN_TARGET_READ_SCOPE_MISMATCH:"
            f"{target_usecols}"
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
            "train_target_prefix_read_count": (
                len(
                    train_target_calls
                )
            ),
            "full_dataset_columns_loaded": [
                "dataset_split"
            ],
            "train_feature_read_nrows": (
                EXPECTED_TRAIN_ROWS
            ),
            "train_target_read_nrows": (
                EXPECTED_TRAIN_ROWS
            ),
            "train_target_columns_loaded": [
                "decision_time",
                "target_class",
                "target_tradeable",
            ],
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
            "read_policy_confirmed": (
                True
            ),
        },
        feature_batch,
        target_batch,
    )


def _validate_feature_batch_for_alignment(
    batch: Any,
) -> dict[str, Any]:

    _require(
        str(
            batch.dataset_id
        )
        ==
        EXPECTED_DATASET_ID,
        "FEATURE_BATCH_DATASET_ID_MISMATCH",
    )

    _require(
        str(
            batch.dataset_sha256
        )
        ==
        EXPECTED_DATASET_SHA256,
        "FEATURE_BATCH_DATASET_SHA256_MISMATCH",
    )

    _require(
        str(
            batch.manifest_sha256
        )
        ==
        EXPECTED_MANIFEST_SHA256,
        "FEATURE_BATCH_MANIFEST_SHA256_MISMATCH",
    )

    _require(
        str(
            batch.training_contract_version
        )
        ==
        EXPECTED_FEATURE_CONTRACT,
        "FEATURE_BATCH_CONTRACT_MISMATCH",
    )

    _require(
        str(
            batch.trainer_input_contract_version
        )
        ==
        EXPECTED_TRAINER_INPUT_CONTRACT,
        "FEATURE_BATCH_TRAINER_INPUT_CONTRACT_MISMATCH",
    )

    _require(
        str(
            batch.trainer_input_contract_fingerprint_sha256
        )
        ==
        EXPECTED_TRAINER_INPUT_CONTRACT_FINGERPRINT_SHA256,
        "FEATURE_BATCH_TRAINER_INPUT_FINGERPRINT_MISMATCH",
    )

    _require(
        str(
            batch.feature_columns_sha256
        )
        ==
        EXPECTED_FEATURE_COLUMNS_SHA256,
        "FEATURE_BATCH_FEATURE_COLUMNS_SHA256_MISMATCH",
    )

    _require(
        str(
            batch.train_input_fingerprint_sha256
        )
        ==
        EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256,
        "FEATURE_BATCH_TRAIN_INPUT_FINGERPRINT_MISMATCH",
    )

    _require(
        int(
            batch.row_count
        )
        ==
        EXPECTED_TRAIN_ROWS,
        "FEATURE_BATCH_ROW_COUNT_MISMATCH",
    )

    decision_time_raw = (
        batch.decision_time
    )

    if not isinstance(
        decision_time_raw,
        np.ndarray,
    ):
        raise RuntimeError(
            "FEATURE_BATCH_DECISION_TIME_NOT_ARRAY"
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
            "FEATURE_BATCH_DECISION_TIME_SHAPE_MISMATCH:"
            f"{decision_time.shape}"
        ),
    )

    _require(
        not bool(
            decision_time.flags.writeable
        ),
        "FEATURE_BATCH_DECISION_TIME_NOT_READ_ONLY",
    )

    return {
        "feature_batch_identity_confirmed": (
            True
        ),
        "train_rows": (
            EXPECTED_TRAIN_ROWS
        ),
        "decision_time_shape": [
            EXPECTED_TRAIN_ROWS
        ],
        "decision_time_read_only": (
            True
        ),
        "train_input_fingerprint_sha256": (
            EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256
        ),
    }


def _validate_target_batch(
    *,
    target_batch: Any,
    feature_batch: Any,
) -> dict[str, Any]:

    _require(
        str(
            target_batch.dataset_id
        )
        ==
        EXPECTED_DATASET_ID,
        "TARGET_BATCH_DATASET_ID_MISMATCH",
    )

    _require(
        str(
            target_batch.dataset_sha256
        )
        ==
        EXPECTED_DATASET_SHA256,
        "TARGET_BATCH_DATASET_SHA256_MISMATCH",
    )

    _require(
        str(
            target_batch.manifest_sha256
        )
        ==
        EXPECTED_MANIFEST_SHA256,
        "TARGET_BATCH_MANIFEST_SHA256_MISMATCH",
    )

    _require(
        str(
            target_batch.training_contract_version
        )
        ==
        EXPECTED_FEATURE_CONTRACT,
        "TARGET_BATCH_FEATURE_CONTRACT_MISMATCH",
    )

    _require(
        str(
            target_batch.trainer_input_contract_version
        )
        ==
        EXPECTED_TRAINER_INPUT_CONTRACT,
        "TARGET_BATCH_TRAINER_INPUT_CONTRACT_MISMATCH",
    )

    _require(
        str(
            target_batch.trainer_input_contract_fingerprint_sha256
        )
        ==
        EXPECTED_TRAINER_INPUT_CONTRACT_FINGERPRINT_SHA256,
        "TARGET_BATCH_TRAINER_INPUT_FINGERPRINT_MISMATCH",
    )

    _require(
        str(
            target_batch.target_access_contract_version
        )
        ==
        EXPECTED_TARGET_ACCESS_CONTRACT,
        "TARGET_ACCESS_CONTRACT_VERSION_MISMATCH",
    )

    _require(
        str(
            target_batch.target_access_contract_fingerprint_sha256
        )
        ==
        EXPECTED_TARGET_ACCESS_CONTRACT_FINGERPRINT_SHA256,
        "TARGET_ACCESS_CONTRACT_FINGERPRINT_MISMATCH",
    )

    target_columns = tuple(
        str(
            column
        )
        for column
        in target_batch.target_columns
    )

    _require(
        target_columns
        ==
        EXPECTED_TARGET_COLUMNS,
        (
            "TARGET_BATCH_COLUMNS_MISMATCH:"
            f"{target_columns}"
        ),
    )

    _require(
        int(
            target_batch.row_count
        )
        ==
        EXPECTED_TRAIN_ROWS,
        "TARGET_BATCH_ROW_COUNT_MISMATCH",
    )

    decision_time_raw = (
        target_batch.decision_time
    )

    target_class_raw = (
        target_batch.target_class
    )

    target_tradeable_raw = (
        target_batch.target_tradeable
    )

    if not isinstance(
        decision_time_raw,
        np.ndarray,
    ):
        raise RuntimeError(
            "TARGET_BATCH_DECISION_TIME_NOT_ARRAY"
        )

    if not isinstance(
        target_class_raw,
        np.ndarray,
    ):
        raise RuntimeError(
            "TARGET_BATCH_TARGET_CLASS_NOT_ARRAY"
        )

    if not isinstance(
        target_tradeable_raw,
        np.ndarray,
    ):
        raise RuntimeError(
            "TARGET_BATCH_TARGET_TRADEABLE_NOT_ARRAY"
        )

    decision_time: np.ndarray = (
        decision_time_raw
    )

    target_class: np.ndarray = (
        target_class_raw
    )

    target_tradeable: np.ndarray = (
        target_tradeable_raw
    )

    expected_shape = (
        EXPECTED_TRAIN_ROWS,
    )

    _require(
        decision_time.shape
        ==
        expected_shape,
        (
            "TARGET_DECISION_TIME_SHAPE_MISMATCH:"
            f"{decision_time.shape}"
        ),
    )

    _require(
        target_class.shape
        ==
        expected_shape,
        (
            "TARGET_CLASS_SHAPE_MISMATCH:"
            f"{target_class.shape}"
        ),
    )

    _require(
        target_tradeable.shape
        ==
        expected_shape,
        (
            "TARGET_TRADEABLE_SHAPE_MISMATCH:"
            f"{target_tradeable.shape}"
        ),
    )

    _require(
        target_class.dtype
        ==
        np.dtype(
            np.int8
        ),
        (
            "TARGET_CLASS_DTYPE_MISMATCH:"
            f"{target_class.dtype}"
        ),
    )

    _require(
        target_tradeable.dtype
        ==
        np.dtype(
            np.int8
        ),
        (
            "TARGET_TRADEABLE_DTYPE_MISMATCH:"
            f"{target_tradeable.dtype}"
        ),
    )

    _require(
        not bool(
            decision_time.flags.writeable
        ),
        "TARGET_DECISION_TIME_NOT_READ_ONLY",
    )

    _require(
        not bool(
            target_class.flags.writeable
        ),
        "TARGET_CLASS_NOT_READ_ONLY",
    )

    _require(
        not bool(
            target_tradeable.flags.writeable
        ),
        "TARGET_TRADEABLE_NOT_READ_ONLY",
    )

    unique_decision_time_count = int(
        np.unique(
            decision_time.astype(
                str
            )
        ).size
    )

    _require(
        unique_decision_time_count
        ==
        EXPECTED_TRAIN_ROWS,
        (
            "TARGET_DECISION_TIME_NOT_UNIQUE:"
            f"{unique_decision_time_count}"
        ),
    )

    feature_decision_time_raw = (
        feature_batch.decision_time
    )

    if not isinstance(
        feature_decision_time_raw,
        np.ndarray,
    ):
        raise RuntimeError(
            "FEATURE_DECISION_TIME_NOT_ARRAY_FOR_ALIGNMENT"
        )

    feature_decision_time: np.ndarray = (
        feature_decision_time_raw
    )

    alignment_confirmed = bool(
        np.array_equal(
            decision_time.astype(
                str
            ),
            feature_decision_time.astype(
                str
            ),
        )
    )

    _require(
        alignment_confirmed,
        "TRAIN_FEATURE_TARGET_DECISION_TIME_ALIGNMENT_FAILED",
    )

    target_class_domain_valid = bool(
        np.isin(
            target_class,
            np.asarray(
                sorted(
                    EXPECTED_TARGET_CLASS_VALUES
                ),
                dtype=np.int8,
            ),
        ).all()
    )

    _require(
        target_class_domain_valid,
        "TARGET_CLASS_DOMAIN_INVALID",
    )

    target_tradeable_domain_valid = bool(
        np.isin(
            target_tradeable,
            np.asarray(
                sorted(
                    EXPECTED_TARGET_TRADEABLE_VALUES
                ),
                dtype=np.int8,
            ),
        ).all()
    )

    _require(
        target_tradeable_domain_valid,
        "TARGET_TRADEABLE_DOMAIN_INVALID",
    )

    expected_tradeable = (
        (
            target_class
            !=
            0
        )
        .astype(
            np.int8,
            copy=False,
        )
    )

    linkage_mismatch_count = int(
        np.count_nonzero(
            target_tradeable
            !=
            expected_tradeable
        )
    )

    _require(
        linkage_mismatch_count
        ==
        0,
        (
            "TARGET_TRADEABLE_LINKAGE_MISMATCH:"
            f"{linkage_mismatch_count}"
        ),
    )

    observed_target_fingerprint = (
        Portable331TrainingInputLoader
        ._train_target_fingerprint(
            decision_time=(
                decision_time
            ),
            target_class=(
                target_class
            ),
            target_tradeable=(
                target_tradeable
            ),
        )
    )

    batch_target_fingerprint = str(
        target_batch
        .train_target_fingerprint_sha256
    )

    _require(
        len(
            batch_target_fingerprint
        )
        ==
        64,
        "TARGET_BATCH_FINGERPRINT_LENGTH_INVALID",
    )

    _require(
        observed_target_fingerprint
        ==
        batch_target_fingerprint,
        "TRAIN_TARGET_FINGERPRINT_RECOMPUTE_MISMATCH",
    )

    return {
        "row_count": (
            EXPECTED_TRAIN_ROWS
        ),
        "target_columns": list(
            EXPECTED_TARGET_COLUMNS
        ),
        "target_class_dtype": (
            str(
                target_class.dtype
            )
        ),
        "target_tradeable_dtype": (
            str(
                target_tradeable.dtype
            )
        ),
        "decision_time_unique_count": (
            unique_decision_time_count
        ),
        "decision_time_alignment_with_feature_batch": (
            True
        ),
        "target_class_domain_confirmed": (
            True
        ),
        "target_tradeable_domain_confirmed": (
            True
        ),
        "target_tradeable_linkage_mismatch_count": (
            linkage_mismatch_count
        ),
        "target_tradeable_linkage_confirmed": (
            True
        ),
        "decision_time_read_only": (
            True
        ),
        "target_class_read_only": (
            True
        ),
        "target_tradeable_read_only": (
            True
        ),
        "train_target_fingerprint_sha256": (
            observed_target_fingerprint
        ),
        "target_distribution_computed": (
            False
        ),
        "target_metrics_computed": (
            False
        ),
    }


def _validate_fail_closed_accessors(
    loader: Any,
) -> dict[str, Any]:

    confirmed: list[
        str
    ] = []

    for (
        method_name,
        expected_message,
    ) in FAIL_CLOSED_ACCESSORS:

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
                    "FAIL_CLOSED_ACCESSOR_MISSING:"
                    f"{method_name}"
                )
            )

        method = cast(
            Callable[
                [],
                Any,
            ],
            method_raw,
        )

        try:

            method()

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
                    "FAIL_CLOSED_ERROR_MISMATCH:"
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
                    "ACCESSOR_DID_NOT_FAIL_CLOSED:"
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
        "supervised_train_combination_blocked": (
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
        dataset_path,
        manifest_path,
        _manifest,
    ) = (
        loader._discover_exact_artifact()
    )

    dataset_sha256_before = (
        PortableTrainingFeatureProjector
        ._sha256_file(
            dataset_path
        )
    )

    manifest_sha256_before = (
        PortableTrainingFeatureProjector
        ._sha256_file(
            manifest_path
        )
    )

    (
        read_policy_validation,
        feature_batch,
        target_batch,
    ) = (
        _audit_loader_reads(
            loader
        )
    )

    feature_batch_validation = (
        _validate_feature_batch_for_alignment(
            feature_batch
        )
    )

    target_batch_validation = (
        _validate_target_batch(
            target_batch=(
                target_batch
            ),
            feature_batch=(
                feature_batch
            ),
        )
    )

    fail_closed_validation = (
        _validate_fail_closed_accessors(
            loader
        )
    )

    artifact_immutability = (
        _validate_artifact_immutable_before_after(
            dataset_path=(
                dataset_path
            ),
            manifest_path=(
                manifest_path
            ),
            dataset_sha256_before=(
                dataset_sha256_before
            ),
            manifest_sha256_before=(
                manifest_sha256_before
            ),
        )
    )

    target_fingerprint = str(
        target_batch_validation[
            "train_target_fingerprint_sha256"
        ]
    )

    _require(
        len(
            target_fingerprint
        )
        ==
        64,
        "FINAL_TARGET_FINGERPRINT_INVALID",
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_PORTABLE_331_TRAIN_TARGET_LOADER_INTEGRATION"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "research_scope": (
            "REAL_FROZEN_PORTABLE_ARTIFACT_TRAIN_ONLY_TARGET_"
            "LOADING_WITH_FEATURE_TIME_ALIGNMENT_AND_FAIL_CLOSED_"
            "SUPERVISED_VALIDATION_AND_TEST_ACCESS"
        ),
        "decision": {
            "status": (
                "XAUUSD_PORTABLE_331_TRAIN_TARGET_LOADER_INTEGRATION_CONFIRMED"
            ),
            "reason": (
                "THE_EXACT_FROZEN_PORTABLE_ARTIFACT_LOADED_ONLY_"
                "THE_FIRST_69966_TRAIN_TARGET_ROWS_FOR_TARGET_CLASS_"
                "AND_TARGET_TRADEABLE_WITH_CANONICAL_DOMAIN_AND_"
                "TRADEABLE_LINKAGE_VALIDATION"
            ),
            "target_access_contract_version": (
                EXPECTED_TARGET_ACCESS_CONTRACT
            ),
            "target_access_contract_fingerprint_sha256": (
                EXPECTED_TARGET_ACCESS_CONTRACT_FINGERPRINT_SHA256
            ),
            "train_target_fingerprint_sha256": (
                target_fingerprint
            ),
            "train_rows": (
                EXPECTED_TRAIN_ROWS
            ),
            "train_target_columns": list(
                EXPECTED_TARGET_COLUMNS
            ),
            "train_target_loading_confirmed": (
                True
            ),
            "train_feature_target_time_alignment_confirmed": (
                True
            ),
            "train_supervised_combination_authorized": (
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
                "DESIGN_TRAIN_ONLY_SUPERVISED_BATCH_CONTRACT_"
                "WITHOUT_MODEL_FIT_OR_HOLDOUT_ACCESS"
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
            "trainer_input_contract_version": (
                EXPECTED_TRAINER_INPUT_CONTRACT
            ),
            "trainer_input_contract_fingerprint_sha256": (
                EXPECTED_TRAINER_INPUT_CONTRACT_FINGERPRINT_SHA256
            ),
            "target_access_contract_version": (
                EXPECTED_TARGET_ACCESS_CONTRACT
            ),
            "target_access_contract_fingerprint_sha256": (
                EXPECTED_TARGET_ACCESS_CONTRACT_FINGERPRINT_SHA256
            ),
            "train_input_fingerprint_sha256": (
                EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256
            ),
            "train_target_fingerprint_sha256": (
                target_fingerprint
            ),
            "filesystem_path_emitted": (
                False
            ),
        },
        "artifact_immutability": (
            artifact_immutability
        ),
        "read_policy_validation": (
            read_policy_validation
        ),
        "feature_batch_alignment_reference": (
            feature_batch_validation
        ),
        "train_target_batch_validation": (
            target_batch_validation
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
                True
            ),
            "train_feature_target_values_combined": (
                False
            ),
            "target_distribution_computed": (
                False
            ),
            "target_metrics_computed": (
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
            "portable_dataset_modified": (
                False
            ),
            "portable_manifest_modified": (
                False
            ),
            "target_values_recomputed": (
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
                "DESIGN_TRAIN_ONLY_SUPERVISED_BATCH_CONTRACT_"
                "WITHOUT_MODEL_FIT_OR_HOLDOUT_ACCESS"
            ),
            "freeze_train_target_fingerprint": (
                target_fingerprint
            ),
            "load_train_supervised_currently_authorized": (
                False
            ),
            "validation_access_currently_authorized": (
                False
            ),
            "test_access_currently_authorized": (
                False
            ),
            "model_training_authorized": (
                False
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
            run_integration()
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_PORTABLE_331_TRAIN_TARGET_"
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