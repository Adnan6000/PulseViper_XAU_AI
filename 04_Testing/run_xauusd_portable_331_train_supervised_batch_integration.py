from __future__ import annotations

import importlib
import json
import sys

from pathlib import Path
from typing import Any, Callable, Sequence, cast

import numpy as np


ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_SUPERVISED_BATCH_INTEGRATION_V1"
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


EXPECTED_SUPERVISED_BATCH_CONTRACT = (
    "XAUUSD_PORTABLE_331_TRAIN_SUPERVISED_BATCH_V1"
)

EXPECTED_SUPERVISED_BATCH_CONTRACT_FINGERPRINT_SHA256 = (
    "1e7bd0751234282d4081ef87783de8633aac815a2f6aa13010fbb5a06156aec4"
)


EXPECTED_FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
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


def _audit_supervised_loader(
    loader: Any,
) -> tuple[
    dict[str, Any],
    Any,
    Any,
    Any,
]:

    original_read_csv: Callable[..., Any] = (
        loader_module
        .pd
        .read_csv
    )

    original_feature_loader_raw = getattr(
        loader,
        "load_train_features",
        None,
    )

    original_target_loader_raw = getattr(
        loader,
        "load_train_targets",
        None,
    )

    if not callable(
        original_feature_loader_raw
    ):
        raise RuntimeError(
            "LOAD_TRAIN_FEATURES_NOT_CALLABLE"
        )

    if not callable(
        original_target_loader_raw
    ):
        raise RuntimeError(
            "LOAD_TRAIN_TARGETS_NOT_CALLABLE"
        )

    feature_loader = cast(
        Callable[
            [],
            Any,
        ],
        original_feature_loader_raw,
    )

    target_loader = cast(
        Callable[
            [],
            Any,
        ],
        original_target_loader_raw,
    )

    read_calls: list[
        dict[str, Any]
    ] = []

    feature_batches: list[
        Any
    ] = []

    target_batches: list[
        Any
    ] = []

    feature_loader_call_count = 0
    target_loader_call_count = 0

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

    def audited_feature_loader(
    ) -> Any:

        nonlocal feature_loader_call_count

        feature_loader_call_count += 1

        batch = (
            feature_loader()
        )

        feature_batches.append(
            batch
        )

        return batch

    def audited_target_loader(
    ) -> Any:

        nonlocal target_loader_call_count

        target_loader_call_count += 1

        batch = (
            target_loader()
        )

        target_batches.append(
            batch
        )

        return batch

    loader_module.pd.read_csv = (
        audited_read_csv
    )

    setattr(
        loader,
        "load_train_features",
        audited_feature_loader,
    )

    setattr(
        loader,
        "load_train_targets",
        audited_target_loader,
    )

    try:

        supervised_batch = (
            loader.load_train_supervised()
        )

    finally:

        loader_module.pd.read_csv = (
            original_read_csv
        )

        setattr(
            loader,
            "load_train_features",
            original_feature_loader_raw,
        )

        setattr(
            loader,
            "load_train_targets",
            original_target_loader_raw,
        )

    _require(
        feature_loader_call_count
        ==
        1,
        (
            "FEATURE_LOADER_CALL_COUNT_INVALID:"
            f"{feature_loader_call_count}"
        ),
    )

    _require(
        target_loader_call_count
        ==
        1,
        (
            "TARGET_LOADER_CALL_COUNT_INVALID:"
            f"{target_loader_call_count}"
        ),
    )

    _require(
        len(
            feature_batches
        )
        ==
        1,
        (
            "CAPTURED_FEATURE_BATCH_COUNT_INVALID:"
            f"{len(feature_batches)}"
        ),
    )

    _require(
        len(
            target_batches
        )
        ==
        1,
        (
            "CAPTURED_TARGET_BATCH_COUNT_INVALID:"
            f"{len(target_batches)}"
        ),
    )

    _require(
        len(
            read_calls
        )
        ==
        4,
        (
            "SUPERVISED_READ_CALL_COUNT_INVALID:"
            f"{len(read_calls)}"
        ),
    )

    structural_calls: list[
        dict[str, Any]
    ] = []

    feature_reads: list[
        dict[str, Any]
    ] = []

    target_reads: list[
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
                "SUPERVISED_READ_USECOLS_NOT_LIST"
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
                "SUPERVISED_READ_NROWS_NOT_INTEGER"
            )

        _require(
            nrows_raw
            ==
            EXPECTED_TRAIN_ROWS,
            (
                "NON_TRAIN_PREFIX_READ_DETECTED:"
                f"{nrows_raw}"
            ),
        )

        if (
            usecols
            ==
            [
                "decision_time",
                "target_class",
                "target_tradeable",
            ]
        ):

            target_reads.append(
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

            feature_reads.append(
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
            "SUPERVISED_STRUCTURAL_READ_COUNT_INVALID:"
            f"{len(structural_calls)}"
        ),
    )

    for call in (
        structural_calls
    ):

        usecols_raw = (
            call.get(
                "usecols"
            )
        )

        if not isinstance(
            usecols_raw,
            list,
        ):
            raise RuntimeError(
                "SUPERVISED_STRUCTURAL_USECOLS_NOT_LIST"
            )

        usecols = [
            str(
                item
            )
            for item
            in usecols_raw
        ]

        _require(
            usecols
            ==
            [
                "dataset_split"
            ],
            (
                "SUPERVISED_STRUCTURAL_SCOPE_EXCEEDED:"
                f"{usecols}"
            ),
        )

    _require(
        len(
            feature_reads
        )
        ==
        1,
        (
            "SUPERVISED_FEATURE_READ_COUNT_INVALID:"
            f"{len(feature_reads)}"
        ),
    )

    _require(
        len(
            target_reads
        )
        ==
        1,
        (
            "SUPERVISED_TARGET_READ_COUNT_INVALID:"
            f"{len(target_reads)}"
        ),
    )

    feature_read = (
        feature_reads[
            0
        ]
    )

    feature_usecols_raw = (
        feature_read.get(
            "usecols"
        )
    )

    if not isinstance(
        feature_usecols_raw,
        list,
    ):
        raise RuntimeError(
            "SUPERVISED_FEATURE_USECOLS_NOT_LIST"
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
            "SUPERVISED_FEATURE_READ_COLUMN_COUNT_INVALID:"
            f"{len(feature_usecols)}"
        ),
    )

    _require(
        feature_usecols[
            0
        ]
        ==
        "decision_time",
        "SUPERVISED_FEATURE_READ_DECISION_TIME_NOT_FIRST",
    )

    forbidden_target_columns = sorted(
        set(
            EXPECTED_TARGET_COLUMNS
        )
        &
        set(
            feature_usecols
        )
    )

    _require(
        not forbidden_target_columns,
        (
            "SUPERVISED_FEATURE_READ_INCLUDED_TARGETS:"
            f"{forbidden_target_columns}"
        ),
    )

    target_read = (
        target_reads[
            0
        ]
    )

    target_usecols_raw = (
        target_read.get(
            "usecols"
        )
    )

    if not isinstance(
        target_usecols_raw,
        list,
    ):
        raise RuntimeError(
            "SUPERVISED_TARGET_USECOLS_NOT_LIST"
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
            "SUPERVISED_TARGET_READ_SCOPE_MISMATCH:"
            f"{target_usecols}"
        ),
    )

    return (
        {
            "feature_loader_call_count": (
                feature_loader_call_count
            ),
            "target_loader_call_count": (
                target_loader_call_count
            ),
            "total_csv_read_count": (
                len(
                    read_calls
                )
            ),
            "structural_read_count": (
                len(
                    structural_calls
                )
            ),
            "train_feature_read_count": (
                len(
                    feature_reads
                )
            ),
            "train_target_read_count": (
                len(
                    target_reads
                )
            ),
            "additional_dataset_read_count": (
                0
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
        supervised_batch,
        feature_batches[
            0
        ],
        target_batches[
            0
        ],
    )


def _validate_supervised_batch(
    *,
    supervised_batch: Any,
    feature_batch: Any,
    target_batch: Any,
) -> dict[str, Any]:

    _require(
        type(
            supervised_batch
        ).__name__
        ==
        "Portable331TrainSupervisedBatch",
        (
            "SUPERVISED_BATCH_TYPE_INVALID:"
            f"{type(supervised_batch).__name__}"
        ),
    )

    _require(
        str(
            supervised_batch.dataset_id
        )
        ==
        EXPECTED_DATASET_ID,
        "SUPERVISED_DATASET_ID_MISMATCH",
    )

    _require(
        str(
            supervised_batch.dataset_sha256
        )
        ==
        EXPECTED_DATASET_SHA256,
        "SUPERVISED_DATASET_SHA256_MISMATCH",
    )

    _require(
        str(
            supervised_batch.manifest_sha256
        )
        ==
        EXPECTED_MANIFEST_SHA256,
        "SUPERVISED_MANIFEST_SHA256_MISMATCH",
    )

    _require(
        str(
            supervised_batch.training_contract_version
        )
        ==
        EXPECTED_FEATURE_CONTRACT,
        "SUPERVISED_FEATURE_CONTRACT_MISMATCH",
    )

    _require(
        str(
            supervised_batch.trainer_input_contract_version
        )
        ==
        EXPECTED_TRAINER_INPUT_CONTRACT,
        "SUPERVISED_TRAINER_INPUT_CONTRACT_MISMATCH",
    )

    _require(
        str(
            supervised_batch.trainer_input_contract_fingerprint_sha256
        )
        ==
        EXPECTED_TRAINER_INPUT_CONTRACT_FINGERPRINT_SHA256,
        "SUPERVISED_TRAINER_INPUT_FINGERPRINT_MISMATCH",
    )

    _require(
        str(
            supervised_batch.target_access_contract_version
        )
        ==
        EXPECTED_TARGET_ACCESS_CONTRACT,
        "SUPERVISED_TARGET_ACCESS_CONTRACT_MISMATCH",
    )

    _require(
        str(
            supervised_batch.target_access_contract_fingerprint_sha256
        )
        ==
        EXPECTED_TARGET_ACCESS_CONTRACT_FINGERPRINT_SHA256,
        "SUPERVISED_TARGET_ACCESS_FINGERPRINT_MISMATCH",
    )

    _require(
        str(
            supervised_batch.supervised_batch_contract_version
        )
        ==
        EXPECTED_SUPERVISED_BATCH_CONTRACT,
        "SUPERVISED_BATCH_CONTRACT_MISMATCH",
    )

    _require(
        str(
            supervised_batch.supervised_batch_contract_fingerprint_sha256
        )
        ==
        EXPECTED_SUPERVISED_BATCH_CONTRACT_FINGERPRINT_SHA256,
        "SUPERVISED_BATCH_CONTRACT_FINGERPRINT_MISMATCH",
    )

    _require(
        int(
            supervised_batch.row_count
        )
        ==
        EXPECTED_TRAIN_ROWS,
        "SUPERVISED_ROW_COUNT_MISMATCH",
    )

    feature_columns = tuple(
        str(
            feature
        )
        for feature
        in supervised_batch.feature_columns
    )

    _require(
        len(
            feature_columns
        )
        ==
        EXPECTED_FEATURE_COUNT,
        "SUPERVISED_FEATURE_COUNT_MISMATCH",
    )

    _require(
        str(
            supervised_batch.feature_columns_sha256
        )
        ==
        EXPECTED_FEATURE_COLUMNS_SHA256,
        "SUPERVISED_FEATURE_COLUMNS_SHA256_MISMATCH",
    )

    _require(
        str(
            supervised_batch.train_input_fingerprint_sha256
        )
        ==
        EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256,
        "SUPERVISED_TRAIN_INPUT_FINGERPRINT_MISMATCH",
    )

    target_columns = tuple(
        str(
            target
        )
        for target
        in supervised_batch.target_columns
    )

    _require(
        target_columns
        ==
        EXPECTED_TARGET_COLUMNS,
        (
            "SUPERVISED_TARGET_COLUMNS_MISMATCH:"
            f"{target_columns}"
        ),
    )

    _require(
        str(
            supervised_batch.train_target_fingerprint_sha256
        )
        ==
        EXPECTED_TRAIN_TARGET_FINGERPRINT_SHA256,
        "SUPERVISED_TRAIN_TARGET_FINGERPRINT_MISMATCH",
    )

    decision_time_raw = (
        supervised_batch.decision_time
    )

    X_raw = (
        supervised_batch.X
    )

    target_class_raw = (
        supervised_batch.target_class
    )

    target_tradeable_raw = (
        supervised_batch.target_tradeable
    )

    if not isinstance(
        decision_time_raw,
        np.ndarray,
    ):
        raise RuntimeError(
            "SUPERVISED_DECISION_TIME_NOT_ARRAY"
        )

    if not isinstance(
        X_raw,
        np.ndarray,
    ):
        raise RuntimeError(
            "SUPERVISED_X_NOT_ARRAY"
        )

    if not isinstance(
        target_class_raw,
        np.ndarray,
    ):
        raise RuntimeError(
            "SUPERVISED_TARGET_CLASS_NOT_ARRAY"
        )

    if not isinstance(
        target_tradeable_raw,
        np.ndarray,
    ):
        raise RuntimeError(
            "SUPERVISED_TARGET_TRADEABLE_NOT_ARRAY"
        )

    decision_time: np.ndarray = (
        decision_time_raw
    )

    X: np.ndarray = (
        X_raw
    )

    target_class: np.ndarray = (
        target_class_raw
    )

    target_tradeable: np.ndarray = (
        target_tradeable_raw
    )

    _require(
        decision_time.shape
        ==
        (
            EXPECTED_TRAIN_ROWS,
        ),
        (
            "SUPERVISED_DECISION_TIME_SHAPE_INVALID:"
            f"{decision_time.shape}"
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
            "SUPERVISED_X_SHAPE_INVALID:"
            f"{X.shape}"
        ),
    )

    _require(
        target_class.shape
        ==
        (
            EXPECTED_TRAIN_ROWS,
        ),
        (
            "SUPERVISED_TARGET_CLASS_SHAPE_INVALID:"
            f"{target_class.shape}"
        ),
    )

    _require(
        target_tradeable.shape
        ==
        (
            EXPECTED_TRAIN_ROWS,
        ),
        (
            "SUPERVISED_TARGET_TRADEABLE_SHAPE_INVALID:"
            f"{target_tradeable.shape}"
        ),
    )

    _require(
        X.dtype
        ==
        np.dtype(
            np.float64
        ),
        (
            "SUPERVISED_X_DTYPE_INVALID:"
            f"{X.dtype}"
        ),
    )

    _require(
        target_class.dtype
        ==
        np.dtype(
            np.int8
        ),
        (
            "SUPERVISED_TARGET_CLASS_DTYPE_INVALID:"
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
            "SUPERVISED_TARGET_TRADEABLE_DTYPE_INVALID:"
            f"{target_tradeable.dtype}"
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
            "SUPERVISED_X_NONFINITE_COUNT:"
            f"{nonfinite_count}"
        ),
    )

    _require(
        not bool(
            decision_time.flags.writeable
        ),
        "SUPERVISED_DECISION_TIME_NOT_READ_ONLY",
    )

    _require(
        not bool(
            X.flags.writeable
        ),
        "SUPERVISED_X_NOT_READ_ONLY",
    )

    _require(
        not bool(
            target_class.flags.writeable
        ),
        "SUPERVISED_TARGET_CLASS_NOT_READ_ONLY",
    )

    _require(
        not bool(
            target_tradeable.flags.writeable
        ),
        "SUPERVISED_TARGET_TRADEABLE_NOT_READ_ONLY",
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
            "SUPERVISED_DECISION_TIME_NOT_UNIQUE:"
            f"{unique_decision_time_count}"
        ),
    )

    _require(
        bool(
            np.isin(
                target_class,
                np.asarray(
                    sorted(
                        EXPECTED_TARGET_CLASS_VALUES
                    ),
                    dtype=np.int8,
                ),
            ).all()
        ),
        "SUPERVISED_TARGET_CLASS_DOMAIN_INVALID",
    )

    _require(
        bool(
            np.isin(
                target_tradeable,
                np.asarray(
                    sorted(
                        EXPECTED_TARGET_TRADEABLE_VALUES
                    ),
                    dtype=np.int8,
                ),
            ).all()
        ),
        "SUPERVISED_TARGET_TRADEABLE_DOMAIN_INVALID",
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
            "SUPERVISED_TARGET_LINKAGE_MISMATCH:"
            f"{linkage_mismatch_count}"
        ),
    )

    feature_decision_time_raw = (
        feature_batch.decision_time
    )

    target_decision_time_raw = (
        target_batch.decision_time
    )

    if not isinstance(
        feature_decision_time_raw,
        np.ndarray,
    ):
        raise RuntimeError(
            "CAPTURED_FEATURE_DECISION_TIME_NOT_ARRAY"
        )

    if not isinstance(
        target_decision_time_raw,
        np.ndarray,
    ):
        raise RuntimeError(
            "CAPTURED_TARGET_DECISION_TIME_NOT_ARRAY"
        )

    _require(
        bool(
            np.array_equal(
                decision_time.astype(
                    str
                ),
                feature_decision_time_raw.astype(
                    str
                ),
            )
        ),
        "SUPERVISED_FEATURE_DECISION_TIME_ALIGNMENT_FAILED",
    )

    _require(
        bool(
            np.array_equal(
                decision_time.astype(
                    str
                ),
                target_decision_time_raw.astype(
                    str
                ),
            )
        ),
        "SUPERVISED_TARGET_DECISION_TIME_ALIGNMENT_FAILED",
    )

    _require(
        supervised_batch.X
        is
        feature_batch.X,
        "SUPERVISED_X_NOT_REUSED_FROM_FEATURE_BATCH",
    )

    _require(
        supervised_batch.decision_time
        is
        feature_batch.decision_time,
        "SUPERVISED_DECISION_TIME_NOT_REUSED_FROM_FEATURE_BATCH",
    )

    _require(
        supervised_batch.target_class
        is
        target_batch.target_class,
        "SUPERVISED_TARGET_CLASS_NOT_REUSED_FROM_TARGET_BATCH",
    )

    _require(
        supervised_batch.target_tradeable
        is
        target_batch.target_tradeable,
        "SUPERVISED_TARGET_TRADEABLE_NOT_REUSED_FROM_TARGET_BATCH",
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

    _require(
        observed_target_fingerprint
        ==
        EXPECTED_TRAIN_TARGET_FINGERPRINT_SHA256,
        "SUPERVISED_RECOMPUTED_TARGET_FINGERPRINT_MISMATCH",
    )

    return {
        "row_count": (
            EXPECTED_TRAIN_ROWS
        ),
        "feature_count": (
            EXPECTED_FEATURE_COUNT
        ),
        "X_shape": [
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
        "X_dtype": (
            str(
                X.dtype
            )
        ),
        "X_nonfinite_count": (
            nonfinite_count
        ),
        "target_class_shape": [
            int(
                target_class.shape[
                    0
                ]
            )
        ],
        "target_class_dtype": (
            str(
                target_class.dtype
            )
        ),
        "target_tradeable_shape": [
            int(
                target_tradeable.shape[
                    0
                ]
            )
        ],
        "target_tradeable_dtype": (
            str(
                target_tradeable.dtype
            )
        ),
        "decision_time_unique_count": (
            unique_decision_time_count
        ),
        "feature_target_decision_time_alignment": (
            True
        ),
        "target_tradeable_linkage_mismatch_count": (
            linkage_mismatch_count
        ),
        "target_tradeable_linkage_confirmed": (
            True
        ),
        "arrays_read_only": (
            True
        ),
        "arrays_reused_without_copy": (
            True
        ),
        "feature_columns_sha256": (
            EXPECTED_FEATURE_COLUMNS_SHA256
        ),
        "train_input_fingerprint_sha256": (
            EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256
        ),
        "train_target_fingerprint_sha256": (
            observed_target_fingerprint
        ),
        "target_distribution_computed": (
            False
        ),
        "metrics_computed": (
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
                    "FAIL_CLOSED_MESSAGE_MISMATCH:"
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
                    "FAIL_CLOSED_ACCESSOR_DID_NOT_BLOCK:"
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


def _validate_artifact_immutability(
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
        "DATASET_HASH_BEFORE_MISMATCH",
    )

    _require(
        manifest_sha256_before
        ==
        EXPECTED_MANIFEST_SHA256,
        "MANIFEST_HASH_BEFORE_MISMATCH",
    )

    _require(
        dataset_sha256_after
        ==
        EXPECTED_DATASET_SHA256,
        "DATASET_HASH_AFTER_MISMATCH",
    )

    _require(
        manifest_sha256_after
        ==
        EXPECTED_MANIFEST_SHA256,
        "MANIFEST_HASH_AFTER_MISMATCH",
    )

    _require(
        dataset_sha256_before
        ==
        dataset_sha256_after,
        "DATASET_CHANGED_DURING_SUPERVISED_INTEGRATION",
    )

    _require(
        manifest_sha256_before
        ==
        manifest_sha256_after,
        "MANIFEST_CHANGED_DURING_SUPERVISED_INTEGRATION",
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
        read_policy,
        supervised_batch,
        feature_batch,
        target_batch,
    ) = (
        _audit_supervised_loader(
            loader
        )
    )

    batch_validation = (
        _validate_supervised_batch(
            supervised_batch=(
                supervised_batch
            ),
            feature_batch=(
                feature_batch
            ),
            target_batch=(
                target_batch
            ),
        )
    )

    fail_closed_validation = (
        _validate_fail_closed_accessors(
            loader
        )
    )

    artifact_immutability = (
        _validate_artifact_immutability(
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

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_PORTABLE_331_TRAIN_SUPERVISED_BATCH_INTEGRATION"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "research_scope": (
            "REAL_TRAIN_ONLY_SUPERVISED_BATCH_ALIGNMENT_USING_"
            "EXISTING_FEATURE_AND_TARGET_LOADERS_WITHOUT_ADDITIONAL_"
            "DATA_READ_MODEL_FIT_METRICS_OR_HOLDOUT_ACCESS"
        ),
        "decision": {
            "status": (
                "XAUUSD_PORTABLE_331_TRAIN_SUPERVISED_BATCH_INTEGRATION_CONFIRMED"
            ),
            "reason": (
                "THE_SUPERVISED_BATCH_WAS_CONSTRUCTED_ONLY_FROM_"
                "THE_FROZEN_AUTHORIZED_TRAIN_FEATURE_AND_TARGET_"
                "BATCHES_WITH_EXACT_IDENTITY_TIME_FINGERPRINT_"
                "DOMAIN_AND_LINKAGE_ALIGNMENT"
            ),
            "supervised_batch_contract_version": (
                EXPECTED_SUPERVISED_BATCH_CONTRACT
            ),
            "supervised_batch_contract_fingerprint_sha256": (
                EXPECTED_SUPERVISED_BATCH_CONTRACT_FINGERPRINT_SHA256
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
            "train_supervised_batch_confirmed": (
                True
            ),
            "additional_dataset_read_confirmed": (
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
            "validation_access_authorized": (
                False
            ),
            "test_access_authorized": (
                False
            ),
            "target_contract_change_authorized": (
                False
            ),
            "feature_contract_change_authorized": (
                False
            ),
            "live_authorized": (
                False
            ),
            "next_action": (
                "DESIGN_TRAIN_ONLY_MODEL_RESEARCH_PROTOCOL_"
                "WITH_WALK_FORWARD_SELECTION_AND_NO_HOLDOUT_ACCESS"
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
            "supervised_batch_contract_version": (
                EXPECTED_SUPERVISED_BATCH_CONTRACT
            ),
            "supervised_batch_contract_fingerprint_sha256": (
                EXPECTED_SUPERVISED_BATCH_CONTRACT_FINGERPRINT_SHA256
            ),
            "train_input_fingerprint_sha256": (
                EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256
            ),
            "train_target_fingerprint_sha256": (
                EXPECTED_TRAIN_TARGET_FINGERPRINT_SHA256
            ),
            "filesystem_path_emitted": (
                False
            ),
        },
        "read_policy_validation": (
            read_policy
        ),
        "train_supervised_batch_validation": (
            batch_validation
        ),
        "fail_closed_validation": (
            fail_closed_validation
        ),
        "artifact_immutability": (
            artifact_immutability
        ),
        "scientific_policy": {
            "train_feature_values_loaded": (
                True
            ),
            "train_target_values_loaded": (
                True
            ),
            "train_supervised_values_combined": (
                True
            ),
            "additional_dataset_read_performed": (
                False
            ),
            "target_values_recomputed": (
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
            "model_architecture_selected": (
                False
            ),
            "scaler_fit": (
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
            "feature_contract_changed": (
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
                "DESIGN_TRAIN_ONLY_MODEL_RESEARCH_PROTOCOL_"
                "WITH_WALK_FORWARD_SELECTION_AND_NO_HOLDOUT_ACCESS"
            ),
            "supervised_batch_loader_reimplementation_required": (
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
            "validation_access_currently_authorized": (
                False
            ),
            "test_access_currently_authorized": (
                False
            ),
            "model_training_currently_authorized": (
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
                        "XAUUSD_PORTABLE_331_TRAIN_SUPERVISED_"
                        "BATCH_INTEGRATION_FAILED"
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