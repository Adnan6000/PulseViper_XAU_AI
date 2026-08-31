from __future__ import annotations

import hashlib
import importlib
import json

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest


loader_module: Any = importlib.import_module(
    "02_AI.Dataset.portable_331_training_input_loader"
)


Portable331TrainingInputLoader = (
    loader_module
    .Portable331TrainingInputLoader
)

Portable331TrainingInputLoaderError = (
    loader_module
    .Portable331TrainingInputLoaderError
)


def test_feature_columns_sha256_is_order_sensitive(
) -> None:

    first = [
        "feature_a",
        "feature_b",
        "feature_c",
    ]

    second = [
        "feature_b",
        "feature_a",
        "feature_c",
    ]

    first_hash = (
        Portable331TrainingInputLoader
        ._feature_columns_sha256(
            first
        )
    )

    second_hash = (
        Portable331TrainingInputLoader
        ._feature_columns_sha256(
            second
        )
    )

    expected_payload = json.dumps(
        first,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=True,
        allow_nan=False,
    ).encode(
        "utf-8"
    )

    expected_hash = hashlib.sha256(
        expected_payload
    ).hexdigest()

    assert (
        first_hash
        ==
        expected_hash
    )

    assert (
        first_hash
        !=
        second_hash
    )


def test_train_input_fingerprint_is_deterministic_and_value_sensitive(
) -> None:

    frame = pd.DataFrame(
        {
            "decision_time": [
                "2026-01-01T00:00:00+00:00",
                "2026-01-01T00:05:00+00:00",
            ],
            "feature_a": [
                1.0,
                2.0,
            ],
            "feature_b": [
                3.0,
                4.0,
            ],
        }
    )

    features = [
        "feature_a",
        "feature_b",
    ]

    first = (
        Portable331TrainingInputLoader
        ._train_input_fingerprint(
            train_frame=(
                frame
            ),
            feature_columns=(
                features
            ),
        )
    )

    second = (
        Portable331TrainingInputLoader
        ._train_input_fingerprint(
            train_frame=(
                frame.copy()
            ),
            feature_columns=(
                features
            ),
        )
    )

    changed = (
        frame.copy()
    )

    changed.loc[
        1,
        "feature_b",
    ] = (
        4.0001
    )

    third = (
        Portable331TrainingInputLoader
        ._train_input_fingerprint(
            train_frame=(
                changed
            ),
            feature_columns=(
                features
            ),
        )
    )

    assert (
        first
        ==
        second
    )

    assert (
        first
        !=
        third
    )


def test_numeric_matrix_preserves_declared_feature_order(
) -> None:

    frame = pd.DataFrame(
        {
            "feature_a": [
                1.0,
                2.0,
            ],
            "feature_b": [
                10.0,
                20.0,
            ],
        }
    )

    matrix = (
        Portable331TrainingInputLoader
        ._numeric_matrix(
            frame=(
                frame
            ),
            feature_columns=[
                "feature_b",
                "feature_a",
            ],
        )
    )

    expected = np.asarray(
        [
            [
                10.0,
                1.0,
            ],
            [
                20.0,
                2.0,
            ],
        ],
        dtype=np.float64,
    )

    assert np.array_equal(
        matrix,
        expected,
    )


def test_numeric_matrix_rejects_nonfinite_values(
) -> None:

    frame = pd.DataFrame(
        {
            "feature_a": [
                1.0,
                float(
                    "inf"
                ),
            ],
        }
    )

    with pytest.raises(
        Portable331TrainingInputLoaderError,
        match=(
            "NONFINITE_TRAIN_MODEL_INPUT_VALUES"
        ),
    ):

        (
            Portable331TrainingInputLoader
            ._numeric_matrix(
                frame=(
                    frame
                ),
                feature_columns=[
                    "feature_a"
                ],
            )
        )


def test_validate_split_series_accepts_exact_frozen_layout(
) -> None:

    split = pd.Series(
        (
            [
                "TRAIN"
            ]
            *
            Portable331TrainingInputLoader
            .EXPECTED_TRAIN_ROWS
        )
        +
        (
            [
                "VALIDATION"
            ]
            *
            Portable331TrainingInputLoader
            .EXPECTED_VALIDATION_ROWS
        )
        +
        (
            [
                "TEST"
            ]
            *
            Portable331TrainingInputLoader
            .EXPECTED_TEST_ROWS
        )
    )

    result = (
        Portable331TrainingInputLoader
        ._validate_split_series(
            split
        )
    )

    assert (
        result
        ==
        Portable331TrainingInputLoader
        .EXPECTED_SPLIT_ROWS
    )


def test_validate_split_series_rejects_noncontiguous_train_layout(
) -> None:

    values = (
        (
            [
                "TRAIN"
            ]
            *
            Portable331TrainingInputLoader
            .EXPECTED_TRAIN_ROWS
        )
        +
        (
            [
                "VALIDATION"
            ]
            *
            Portable331TrainingInputLoader
            .EXPECTED_VALIDATION_ROWS
        )
        +
        (
            [
                "TEST"
            ]
            *
            Portable331TrainingInputLoader
            .EXPECTED_TEST_ROWS
        )
    )

    values[
        Portable331TrainingInputLoader
        .EXPECTED_TRAIN_ROWS
        -
        1
    ] = (
        "VALIDATION"
    )

    values[
        Portable331TrainingInputLoader
        .EXPECTED_TRAIN_ROWS
    ] = (
        "TRAIN"
    )

    split = pd.Series(
        values
    )

    with pytest.raises(
        Portable331TrainingInputLoaderError,
        match=(
            "TRAIN_SPLIT_NOT_CONTIGUOUS_PREFIX"
        ),
    ):

        (
            Portable331TrainingInputLoader
            ._validate_split_series(
                split
            )
        )


def test_target_class_normalization_accepts_labels_and_numeric_ids(
) -> None:

    series = pd.Series(
        [
            "SHORT",
            "NO_TRADE",
            "LONG",
            -1,
            0.0,
            "1",
        ],
        dtype=object,
    )

    result = (
        Portable331TrainingInputLoader
        ._normalize_target_class_array(
            series
        )
    )

    expected = np.asarray(
        [
            -1,
            0,
            1,
            -1,
            0,
            1,
        ],
        dtype=np.int8,
    )

    assert (
        result.dtype
        ==
        np.dtype(
            np.int8
        )
    )

    assert np.array_equal(
        result,
        expected,
    )


def test_target_class_normalization_rejects_unknown_class(
) -> None:

    series = pd.Series(
        [
            "SHORT",
            "SIDEWAYS",
            "LONG",
        ],
        dtype=object,
    )

    with pytest.raises(
        Portable331TrainingInputLoaderError,
        match=(
            "TRAIN_TARGET_CLASS_INVALID"
        ),
    ):

        (
            Portable331TrainingInputLoader
            ._normalize_target_class_array(
                series
            )
        )


def test_target_tradeable_normalization_accepts_binary_forms(
) -> None:

    series = pd.Series(
        [
            0,
            1,
            False,
            True,
            "0",
            "1.0",
        ],
        dtype=object,
    )

    result = (
        Portable331TrainingInputLoader
        ._normalize_target_tradeable_array(
            series
        )
    )

    expected = np.asarray(
        [
            0,
            1,
            0,
            1,
            0,
            1,
        ],
        dtype=np.int8,
    )

    assert np.array_equal(
        result,
        expected,
    )


def test_validate_train_target_frame_confirms_linkage_and_fingerprint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    monkeypatch.setattr(
        Portable331TrainingInputLoader,
        "EXPECTED_TRAIN_ROWS",
        3,
    )

    frame = pd.DataFrame(
        {
            "decision_time": [
                "2026-01-01T00:00:00+00:00",
                "2026-01-01T00:05:00+00:00",
                "2026-01-01T00:10:00+00:00",
            ],
            "target_class": [
                "SHORT",
                "NO_TRADE",
                "LONG",
            ],
            "target_tradeable": [
                1,
                0,
                1,
            ],
        }
    )

    (
        decision_time,
        target_class,
        target_tradeable,
        fingerprint,
    ) = (
        Portable331TrainingInputLoader
        ._validate_train_target_frame(
            frame
        )
    )

    assert np.array_equal(
        target_class,
        np.asarray(
            [
                -1,
                0,
                1,
            ],
            dtype=np.int8,
        ),
    )

    assert np.array_equal(
        target_tradeable,
        np.asarray(
            [
                1,
                0,
                1,
            ],
            dtype=np.int8,
        ),
    )

    assert (
        decision_time.shape
        ==
        (
            3,
        )
    )

    assert (
        len(
            fingerprint
        )
        ==
        64
    )

    repeated = (
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

    assert (
        fingerprint
        ==
        repeated
    )


def test_validate_train_target_frame_rejects_tradeable_linkage_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    monkeypatch.setattr(
        Portable331TrainingInputLoader,
        "EXPECTED_TRAIN_ROWS",
        3,
    )

    frame = pd.DataFrame(
        {
            "decision_time": [
                "2026-01-01T00:00:00+00:00",
                "2026-01-01T00:05:00+00:00",
                "2026-01-01T00:10:00+00:00",
            ],
            "target_class": [
                -1,
                0,
                1,
            ],
            "target_tradeable": [
                1,
                1,
                1,
            ],
        }
    )

    with pytest.raises(
        Portable331TrainingInputLoaderError,
        match=(
            "TRAIN_TARGET_TRADEABLE_LINKAGE_MISMATCH"
        ),
    ):

        (
            Portable331TrainingInputLoader
            ._validate_train_target_frame(
                frame
            )
        )


def test_validate_train_target_frame_rejects_duplicate_decision_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    monkeypatch.setattr(
        Portable331TrainingInputLoader,
        "EXPECTED_TRAIN_ROWS",
        3,
    )

    frame = pd.DataFrame(
        {
            "decision_time": [
                "2026-01-01T00:00:00+00:00",
                "2026-01-01T00:00:00+00:00",
                "2026-01-01T00:10:00+00:00",
            ],
            "target_class": [
                -1,
                0,
                1,
            ],
            "target_tradeable": [
                1,
                0,
                1,
            ],
        }
    )

    with pytest.raises(
        Portable331TrainingInputLoaderError,
        match=(
            "TRAIN_TARGET_DUPLICATE_DECISION_TIME"
        ),
    ):

        (
            Portable331TrainingInputLoader
            ._validate_train_target_frame(
                frame
            )
        )


def test_currently_unauthorized_accessors_remain_fail_closed(
    tmp_path: Path,
) -> None:

    loader = (
        Portable331TrainingInputLoader(
            canonical_root=(
                tmp_path
            )
        )
    )

    unauthorized = [
        (
            loader.load_train_supervised,
            "SUPERVISED_TRAIN_INPUT_ACCESS_NOT_AUTHORIZED",
        ),
        (
            loader.load_validation_features,
            "VALIDATION_FEATURE_ACCESS_NOT_AUTHORIZED",
        ),
        (
            loader.load_validation_targets,
            "VALIDATION_TARGET_ACCESS_NOT_AUTHORIZED",
        ),
        (
            loader.load_test_features,
            "TEST_FEATURE_ACCESS_NOT_AUTHORIZED",
        ),
        (
            loader.load_test_targets,
            "TEST_TARGET_ACCESS_NOT_AUTHORIZED",
        ),
    ]

    for (
        method,
        expected_message,
    ) in unauthorized:

        with pytest.raises(
            Portable331TrainingInputLoaderError,
            match=(
                expected_message
            ),
        ):

            method()