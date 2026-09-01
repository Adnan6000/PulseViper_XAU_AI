from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest


MODULE_PATH = Path(__file__).with_name(
    "xauusd_portable_331_authorized_validation_source.py"
)

spec = importlib.util.spec_from_file_location(
    "xauusd_authorized_validation_source_test_target",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

source_module = (
    importlib.util.module_from_spec(
        spec
    )
)

sys.modules[
    spec.name
] = source_module

spec.loader.exec_module(
    source_module
)

core = (
    source_module
    ._load_core_module()
)


def _feature_columns() -> tuple[str, ...]:
    return tuple(
        f"feature_{index:03d}"
        for index in range(
            331
        )
    )


class FakePortableLoader:
    def __init__(
        self,
        canonical_root: str | Path,
    ) -> None:
        self.canonical_root = Path(
            canonical_root
        )

    def _discover_exact_artifact(
        self,
    ):
        return (
            Path(
                "synthetic_portable.csv"
            ),
            Path(
                "synthetic_manifest.json"
            ),
            {
                "synthetic": True,
            },
        )

    @classmethod
    def _validate_manifest(
        cls,
        manifest: Any,
    ):
        return (
            _feature_columns(),
            (
                "target_class",
                "target_tradeable",
            ),
        )

    @classmethod
    def _feature_columns_sha256(
        cls,
        feature_columns,
    ):
        assert tuple(
            feature_columns
        ) == _feature_columns()

        return (
            source_module
            .EXPECTED_FEATURE_COLUMNS_SHA256
        )

    @classmethod
    def _validate_split_series(
        cls,
        split: pd.Series,
    ):
        normalized = (
            split.astype(
                "string"
            )
            .str.strip()
            .str.upper()
        )

        return {
            "TRAIN": int(
                (
                    normalized
                    == "TRAIN"
                ).sum()
            ),
            "VALIDATION": int(
                (
                    normalized
                    == "VALIDATION"
                ).sum()
            ),
            "TEST": int(
                (
                    normalized
                    == "TEST"
                ).sum()
            ),
        }

    @classmethod
    def _numeric_matrix(
        cls,
        *,
        frame: pd.DataFrame,
        feature_columns,
    ):
        return (
            frame.loc[
                :,
                list(
                    feature_columns
                ),
            ]
            .apply(
                pd.to_numeric,
                errors="raise",
            )
            .to_numpy(
                dtype=np.float64
            )
        )

    @classmethod
    def _normalize_target_class_array(
        cls,
        series: pd.Series,
    ):
        return (
            pd.to_numeric(
                series,
                errors="raise",
            )
            .to_numpy(
                dtype=np.int8
            )
        )

    @classmethod
    def _normalize_target_tradeable_array(
        cls,
        series: pd.Series,
    ):
        return (
            pd.to_numeric(
                series,
                errors="raise",
            )
            .to_numpy(
                dtype=np.int8
            )
        )


def _synthetic_full_dataset() -> pd.DataFrame:
    split = (
        [
            "TRAIN"
        ]
        * 5
        + [
            "VALIDATION"
        ]
        * 3
        + [
            "TEST"
        ]
        * 4
    )

    row_count = len(
        split
    )

    target_class = np.resize(
        np.asarray(
            [
                -1,
                0,
                1,
            ],
            dtype=np.int8,
        ),
        row_count,
    )

    frame = pd.DataFrame(
        {
            "dataset_split": (
                split
            ),
            "decision_time": (
                pd.date_range(
                    "2026-01-01",
                    periods=row_count,
                    freq="h",
                    tz="UTC",
                )
            ),
            "target_class": (
                target_class
            ),
            "target_tradeable": (
                target_class
                != 0
            ).astype(
                np.int8
            ),
        }
    )

    for (
        index,
        feature,
    ) in enumerate(
        _feature_columns()
    ):
        frame[
            feature
        ] = (
            np.arange(
                row_count,
                dtype=np.float64,
            )
            + (
                index
                / 1000.0
            )
        )

    return frame


class FakeReadCsv:
    def __init__(
        self,
        frame: pd.DataFrame,
    ) -> None:
        self.frame = frame
        self.calls: list[
            dict[str, Any]
        ] = []

    def __call__(
        self,
        path,
        **kwargs,
    ) -> pd.DataFrame:
        self.calls.append(
            {
                "path": str(
                    path
                ),
                **kwargs,
            }
        )

        usecols = list(
            kwargs[
                "usecols"
            ]
        )

        if (
            usecols
            == [
                "dataset_split"
            ]
            and "nrows"
            not in kwargs
        ):
            return (
                self.frame.loc[
                    :,
                    usecols,
                ]
                .copy()
            )

        skiprows = kwargs.get(
            "skiprows"
        )

        nrows = kwargs.get(
            "nrows"
        )

        assert skiprows is not None
        assert nrows is not None

        skipped_data_rows = len(
            list(
                skiprows
            )
        )

        start = (
            skipped_data_rows
        )

        stop = (
            start
            + int(
                nrows
            )
        )

        return (
            self.frame.iloc[
                start:stop
            ]
            .loc[
                :,
                usecols,
            ]
            .copy()
        )


def test_real_loader_source_contract_is_exact_and_holdouts_stay_blocked():
    report = (
        source_module
        .inspect_loader_source_contract()
    )

    assert (
        report[
            "loader_source_sha256"
        ]
        == source_module
        .EXPECTED_LOADER_SOURCE_SHA256
    )

    for accessor in (
        "load_validation_features",
        "load_validation_targets",
        "load_test_features",
        "load_test_targets",
    ):
        assert (
            report[
                "blocked_accessors"
            ][
                accessor
            ][
                "confirmed"
            ]
            is True
        )

    assert (
        report[
            "public_holdout_accessors_remain_modified"
        ]
        is False
    )


def test_validation_window_exact_train_validation_test_order():
    split = pd.Series(
        (
            [
                "TRAIN"
            ]
            * 5
            + [
                "VALIDATION"
            ]
            * 3
            + [
                "TEST"
            ]
            * 4
        )
    )

    window = (
        source_module
        .locate_validation_window(
            split
        )
    )

    assert (
        window.train_rows
        == 5
    )

    assert (
        window.validation_rows
        == 3
    )

    assert (
        window.test_rows
        == 4
    )

    assert (
        window.validation_start
        == 5
    )

    assert (
        window.validation_stop
        == 8
    )


def test_non_contiguous_validation_fails_closed():
    split = pd.Series(
        [
            "TRAIN",
            "TRAIN",
            "VALIDATION",
            "TEST",
            "VALIDATION",
            "TEST",
        ]
    )

    with pytest.raises(
        source_module
        .AuthorizedValidationSourceError
    ):
        source_module.locate_validation_window(
            split
        )


def test_wrong_split_order_fails_closed():
    split = pd.Series(
        [
            "TRAIN",
            "VALIDATION",
            "VALIDATION",
            "TRAIN",
            "TEST",
        ]
    )

    with pytest.raises(
        source_module
        .AuthorizedValidationSourceError
    ):
        source_module.locate_validation_window(
            split
        )


def test_synthetic_authorized_source_reads_only_validation_value_block():
    frame = (
        _synthetic_full_dataset()
    )

    fake_reader = FakeReadCsv(
        frame
    )

    adapter = (
        source_module
        .AuthorizedPortableValidationSource(
            ".",
            loader_class=(
                FakePortableLoader
            ),
            read_csv=(
                fake_reader
            ),
            core_module=(
                core
            ),
        )
    )

    batch = adapter.load()

    assert (
        batch.X.shape
        == (
            3,
            331,
        )
    )

    assert (
        batch.target_class.shape
        == (
            3,
        )
    )

    assert (
        batch.target_tradeable.shape
        == (
            3,
        )
    )

    assert (
        batch.split_name
        == "VALIDATION"
    )

    assert (
        len(
            fake_reader.calls
        )
        == 2
    )

    structural_call = (
        fake_reader.calls[
            0
        ]
    )

    assert (
        structural_call[
            "usecols"
        ]
        == [
            "dataset_split"
        ]
    )

    assert (
        "nrows"
        not in structural_call
    )

    value_call = (
        fake_reader.calls[
            1
        ]
    )

    assert (
        value_call[
            "nrows"
        ]
        == 3
    )

    assert (
        len(
            list(
                value_call[
                    "skiprows"
                ]
            )
        )
        == 5
    )

    assert (
        adapter.last_evidence
        is not None
    )

    assert (
        adapter.last_evidence[
            "read_policy"
        ][
            "value_read_start_data_row"
        ]
        == 5
    )

    assert (
        adapter.last_evidence[
            "read_policy"
        ][
            "value_read_stop_exclusive"
        ]
        == 8
    )

    assert (
        adapter.last_evidence[
            "read_policy"
        ][
            "parser_stops_before_test_value_rows"
        ]
        is True
    )

    assert (
        adapter.last_evidence[
            "read_policy"
        ][
            "test_feature_values_loaded"
        ]
        is False
    )

    assert (
        adapter.last_evidence[
            "read_policy"
        ][
            "test_target_values_loaded"
        ]
        is False
    )


def test_validation_batch_preserves_manifest_feature_order():
    frame = (
        _synthetic_full_dataset()
        .iloc[
            5:8
        ]
        .copy()
    )

    batch = (
        source_module
        .build_validation_batch_from_frame(
            frame=frame,
            feature_columns=(
                _feature_columns()
            ),
            loader_class=(
                FakePortableLoader
            ),
            core_module=(
                core
            ),
        )
    )

    assert (
        batch.feature_columns
        == _feature_columns()
    )

    expected_first_feature = (
        frame[
            "feature_000"
        ]
        .to_numpy(
            dtype=np.float64
        )
    )

    assert np.array_equal(
        batch.X[
            :,
            0
        ],
        expected_first_feature,
    )

    expected_last_feature = (
        frame[
            "feature_330"
        ]
        .to_numpy(
            dtype=np.float64
        )
    )

    assert np.array_equal(
        batch.X[
            :,
            330
        ],
        expected_last_feature,
    )


def test_value_frame_containing_test_row_fails_closed():
    frame = (
        _synthetic_full_dataset()
        .iloc[
            6:9
        ]
        .copy()
    )

    assert (
        "TEST"
        in set(
            frame[
                "dataset_split"
            ]
        )
    )

    with pytest.raises(
        source_module
        .AuthorizedValidationSourceError
    ):
        source_module.build_validation_batch_from_frame(
            frame=frame,
            feature_columns=(
                _feature_columns()
            ),
            loader_class=(
                FakePortableLoader
            ),
            core_module=(
                core
            ),
        )


def test_source_attestation_does_not_execute_real_validation():
    report = (
        source_module
        .build_source_attestation()
    )

    assert (
        report[
            "valid"
        ]
        is True
    )

    assert (
        report[
            "decision"
        ][
            "validation_source_implementation_confirmed"
        ]
        is True
    )

    assert (
        report[
            "decision"
        ][
            "real_validation_source_executed"
        ]
        is False
    )

    assert (
        report[
            "decision"
        ][
            "real_validation_values_loaded"
        ]
        is False
    )

    assert (
        report[
            "decision"
        ][
            "real_validation_execution_authorized"
        ]
        is False
    )

    assert (
        report[
            "decision"
        ][
            "test_access_authorized"
        ]
        is False
    )

    assert (
        report[
            "scientific_policy"
        ][
            "portable_test_feature_values_loaded"
        ]
        is False
    )