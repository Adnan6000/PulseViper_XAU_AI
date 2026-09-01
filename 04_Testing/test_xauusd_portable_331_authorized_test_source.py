from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest


MODULE_PATH = Path(
    __file__
).with_name(
    "xauusd_portable_331_authorized_test_source.py"
)

spec = importlib.util.spec_from_file_location(
    "authorized_test_source",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

module = importlib.util.module_from_spec(
    spec
)

sys.modules[
    spec.name
] = module

spec.loader.exec_module(
    module
)


class SyntheticCore:
    class ProtectedTestBatch:
        def __init__(
            self,
            *,
            X: np.ndarray,
            y_true: np.ndarray,
        ) -> None:
            self.X = np.asarray(X)
            self.y_true = np.asarray(y_true)

    @staticmethod
    def validate_test_batch(
        batch: object,
    ) -> object:
        X = np.asarray(
            batch.X
        )
        y_true = np.asarray(
            batch.y_true
        )

        if X.shape[1] != 331:
            raise RuntimeError(
                "wrong feature count"
            )

        if X.shape[0] != y_true.shape[0]:
            raise RuntimeError(
                "row mismatch"
            )

        return batch


def _feature_columns() -> list[str]:
    return [
        f"f_{index:03d}"
        for index in range(
            module.EXPECTED_FEATURE_COUNT
        )
    ]


def _split_labels() -> list[str]:
    return [
        "TRAIN",
        "TRAIN",
        "TRAIN",
        "VALIDATION",
        "VALIDATION",
        "TEST",
        "TEST",
        "TEST",
    ]


def _test_mapping(
    *,
    split_values: list[str] | None = None,
) -> dict[str, np.ndarray]:
    features = {
        column: np.asarray(
            [
                1.0,
                2.0,
                3.0,
            ],
            dtype=np.float64,
        )
        for column in _feature_columns()
    }

    return {
        "dataset_split": np.asarray(
            split_values
            if split_values is not None
            else [
                "TEST",
                "TEST",
                "TEST",
            ],
            dtype=object,
        ),
        **features,
        "target_class": np.asarray(
            [
                -1,
                0,
                1,
            ],
            dtype=np.int8,
        ),
    }


def test_locates_final_contiguous_test_block() -> None:
    plan = (
        module.locate_final_test_block(
            _split_labels()
        )
    )

    assert plan.start_row == 5
    assert plan.stop_row_exclusive == 8
    assert plan.row_count == 3
    assert plan.split_label == "TEST"


def test_rejects_test_before_validation_finishes() -> None:
    labels = [
        "TRAIN",
        "VALIDATION",
        "TEST",
        "VALIDATION",
        "TEST",
    ]

    with pytest.raises(
        module.AuthorizedTestSourceError,
        match=(
            "VALIDATION_BLOCK_NOT_CONTIGUOUS|"
            "TEST_BLOCK_NOT_FINAL_CONTIGUOUS"
        ),
    ):
        module.locate_final_test_block(
            labels
        )


def test_rejects_missing_validation_block() -> None:
    with pytest.raises(
        module.AuthorizedTestSourceError,
        match="VALIDATION_BLOCK_MISSING",
    ):
        module.locate_final_test_block(
            [
                "TRAIN",
                "TRAIN",
                "TEST",
                "TEST",
            ]
        )


def test_bounded_reader_receives_only_exact_test_range() -> None:
    calls: list[
        tuple[
            int,
            int,
            tuple[str, ...],
        ]
    ] = []

    def reader(
        start: int,
        stop: int,
        columns: tuple[str, ...],
    ) -> dict[str, np.ndarray]:
        calls.append(
            (
                start,
                stop,
                columns,
            )
        )

        return _test_mapping()

    source = (
        module.AuthorizedBoundedTestSource(
            split_labels=(
                _split_labels()
            ),
            feature_columns=(
                _feature_columns()
            ),
            feature_columns_sha256=(
                module.EXPECTED_FEATURE_COLUMNS_SHA256
            ),
            read_bounded_rows=reader,
            test_core_module=(
                SyntheticCore
            ),
        )
    )

    batch = (
        source.load_protected_test_batch()
    )

    assert len(calls) == 1
    assert calls[0][0] == 5
    assert calls[0][1] == 8

    requested_columns = (
        calls[0][2]
    )

    assert (
        requested_columns[0]
        == "dataset_split"
    )

    assert (
        requested_columns[-1]
        == "target_class"
    )

    assert (
        list(
            requested_columns[
                1:-1
            ]
        )
        == _feature_columns()
    )

    assert batch.X.shape == (
        3,
        331,
    )

    assert batch.y_true.tolist() == [
        -1,
        0,
        1,
    ]


def test_rejects_reader_that_returns_validation_row() -> None:
    def reader(
        start: int,
        stop: int,
        columns: tuple[str, ...],
    ) -> dict[str, np.ndarray]:
        del start
        del stop
        del columns

        return _test_mapping(
            split_values=[
                "VALIDATION",
                "TEST",
                "TEST",
            ]
        )

    source = (
        module.AuthorizedBoundedTestSource(
            split_labels=(
                _split_labels()
            ),
            feature_columns=(
                _feature_columns()
            ),
            feature_columns_sha256=(
                module.EXPECTED_FEATURE_COLUMNS_SHA256
            ),
            read_bounded_rows=reader,
            test_core_module=(
                SyntheticCore
            ),
        )
    )

    with pytest.raises(
        module.AuthorizedTestSourceError,
        match="RETURNED_NON_TEST_ROWS",
    ):
        source.load_protected_test_batch()


def test_rejects_wrong_feature_fingerprint_before_read() -> None:
    read_called = False

    def reader(
        start: int,
        stop: int,
        columns: tuple[str, ...],
    ) -> dict[str, np.ndarray]:
        nonlocal read_called
        del start
        del stop
        del columns

        read_called = True
        return _test_mapping()

    with pytest.raises(
        module.AuthorizedTestSourceError,
        match="FEATURE_COLUMNS_SHA256_MISMATCH",
    ):
        module.AuthorizedBoundedTestSource(
            split_labels=(
                _split_labels()
            ),
            feature_columns=(
                _feature_columns()
            ),
            feature_columns_sha256=(
                "0" * 64
            ),
            read_bounded_rows=reader,
            test_core_module=(
                SyntheticCore
            ),
        )

    assert read_called is False


def test_rejects_wrong_bounded_row_count() -> None:
    mapping = _test_mapping()

    shortened = {
        key: value[:2]
        for key, value in mapping.items()
    }

    source = (
        module.AuthorizedBoundedTestSource(
            split_labels=(
                _split_labels()
            ),
            feature_columns=(
                _feature_columns()
            ),
            feature_columns_sha256=(
                module.EXPECTED_FEATURE_COLUMNS_SHA256
            ),
            read_bounded_rows=(
                lambda start, stop, columns:
                shortened
            ),
            test_core_module=(
                SyntheticCore
            ),
        )
    )

    with pytest.raises(
        module.AuthorizedTestSourceError,
        match="BOUNDED_TEST_ROW_COUNT_MISMATCH",
    ):
        source.load_protected_test_batch()


def test_source_module_does_not_call_public_holdout_accessors() -> None:
    text = MODULE_PATH.read_text(
        encoding="utf-8"
    )

    forbidden_calls = [
        "load_test_features(",
        "load_test_targets(",
        "load_validation_features(",
        "load_validation_targets(",
    ]

    for forbidden in forbidden_calls:
        assert forbidden not in text


def test_attestation_keeps_real_test_execution_unauthorized() -> None:
    attestation = (
        module.build_source_attestation(
            test_core_source_sha256=(
                "a" * 64
            ),
            source_sha256=(
                "b" * 64
            ),
        )
    )

    assert (
        attestation[
            "valid"
        ]
        is True
    )

    assert (
        attestation[
            "status"
        ]
        == module.STATUS
    )

    assert (
        attestation[
            "verified_properties"
        ][
            "validation_value_reread_performed"
        ]
        is False
    )

    assert (
        attestation[
            "verified_properties"
        ][
            "real_test_values_accessed"
        ]
        is False
    )

    assert (
        attestation[
            "decision"
        ][
            "one_shot_test_runner_implementation_authorized_next"
        ]
        is True
    )

    assert (
        attestation[
            "decision"
        ][
            "test_execution_authorized"
        ]
        is False
    )

    assert (
        attestation[
            "decision"
        ][
            "live_authorized"
        ]
        is False
    )