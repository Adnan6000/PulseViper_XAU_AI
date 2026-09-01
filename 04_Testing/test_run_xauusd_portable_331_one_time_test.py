from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Sequence, cast

import numpy as np
import pandas as pd
import pytest


MODULE_PATH = (
    Path(
        __file__
    ).with_name(
        "run_xauusd_portable_331_one_time_test.py"
    )
)

spec = (
    importlib.util
    .spec_from_file_location(
        "one_time_test_runner",
        MODULE_PATH,
    )
)

assert spec is not None
assert spec.loader is not None

module = (
    importlib.util
    .module_from_spec(
        spec
    )
)

sys.modules[
    spec.name
] = module

spec.loader.exec_module(
    module
)


def _perfect_case() -> tuple[
    np.ndarray,
    np.ndarray,
]:
    y = np.asarray(
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

    p = np.asarray(
        [
            [
                0.80,
                0.10,
                0.10,
            ],
            [
                0.10,
                0.80,
                0.10,
            ],
            [
                0.10,
                0.10,
                0.80,
            ],
            [
                0.70,
                0.20,
                0.10,
            ],
            [
                0.20,
                0.70,
                0.10,
            ],
            [
                0.10,
                0.20,
                0.70,
            ],
        ],
        dtype=np.float64,
    )

    return (
        y,
        p,
    )


def test_metric_contract_exact_for_perfect_predictions() -> None:
    (
        y,
        p,
    ) = _perfect_case()

    metrics = (
        module
        .evaluate_test_metrics(
            y,
            p,
        )
    )

    assert (
        metrics[
            "balanced_accuracy_3class"
        ]
        == pytest.approx(
            1.0
        )
    )

    assert (
        metrics[
            "macro_f1_3class"
        ]
        == pytest.approx(
            1.0
        )
    )

    assert (
        metrics[
            "directional_macro_f1_short_long"
        ]
        == pytest.approx(
            1.0
        )
    )

    assert (
        metrics[
            "short_recall"
        ]
        == pytest.approx(
            1.0
        )
    )

    assert (
        metrics[
            "long_recall"
        ]
        == pytest.approx(
            1.0
        )
    )

    assert (
        metrics[
            "predicted_trade_coverage"
        ]
        == pytest.approx(
            4.0
            / 6.0
        )
    )

    assert (
        len(
            metrics
        )
        == 15
    )


def test_multiclass_brier_matches_manual_definition() -> None:
    (
        y,
        p,
    ) = _perfect_case()

    metrics = (
        module
        .evaluate_test_metrics(
            y,
            p,
        )
    )

    one_hot = (
        np.zeros_like(
            p
        )
    )

    mapping = {
        -1: 0,
        0: 1,
        1: 2,
    }

    for (
        index,
        value,
    ) in enumerate(
        y.tolist()
    ):
        one_hot[
            index,
            mapping[
                int(
                    value
                )
            ],
        ] = 1.0

    expected = float(
        np.mean(
            np.sum(
                (
                    p
                    - one_hot
                )
                ** 2,
                axis=1,
            )
        )
    )

    assert (
        metrics[
            "multiclass_brier"
        ]
        == pytest.approx(
            expected
        )
    )


def test_metric_evaluator_rejects_wrong_probability_shape() -> None:
    y = np.asarray(
        [
            -1,
            0,
            1,
        ],
        dtype=np.int8,
    )

    bad = np.asarray(
        [
            [
                0.5,
                0.5,
            ],
            [
                0.5,
                0.5,
            ],
            [
                0.5,
                0.5,
            ],
        ],
        dtype=np.float64,
    )

    with pytest.raises(
        module.OneTimeTestRunnerError,
        match=(
            "probability shape mismatch"
        ),
    ):
        module.evaluate_test_metrics(
            y,
            bad,
        )


def test_absent_ledger_is_pristine(
    tmp_path: Path,
) -> None:
    state = (
        module
        ._validate_ledger_state_before_execution(
            tmp_path
            / "ledger.json",
            tmp_path
            / "result.json",
        )
    )

    assert state == {
        "state": (
            "ABSENT"
        ),
        (
            "execution_recovery_allowed"
        ): True,
        (
            "test_read_attempt_count"
        ): 0,
        (
            "holdout_consumed_for_rerun_policy"
        ): False,
    }


def test_consumed_ledger_blocks_execution(
    tmp_path: Path,
) -> None:
    ledger_path = (
        tmp_path
        / "ledger.json"
    )

    ledger_path.write_text(
        json.dumps(
            {
                "status": (
                    "TEST_READ_INITIATED_"
                    "CONSUMED_BOUNDARY"
                ),
                (
                    "test_read_attempt_count"
                ): 1,
                (
                    "holdout_consumed_for_"
                    "rerun_policy"
                ): True,
            }
        ),
        encoding="utf-8",
    )

    state = (
        module
        ._validate_ledger_state_before_execution(
            ledger_path,
            tmp_path
            / "result.json",
        )
    )

    assert (
        state[
            "execution_recovery_allowed"
        ]
        is False
    )

    assert (
        state[
            "test_read_attempt_count"
        ]
        == 1
    )

    assert (
        state[
            "holdout_consumed_for_rerun_policy"
        ]
        is True
    )


def test_pre_read_failure_with_zero_reads_is_recoverable(
    tmp_path: Path,
) -> None:
    ledger_path = (
        tmp_path
        / "ledger.json"
    )

    ledger_path.write_text(
        json.dumps(
            {
                "status": (
                    "PRE_READ_TECHNICAL_FAILURE"
                ),
                (
                    "test_read_attempt_count"
                ): 0,
                (
                    "holdout_consumed_for_"
                    "rerun_policy"
                ): False,
            }
        ),
        encoding="utf-8",
    )

    state = (
        module
        ._validate_ledger_state_before_execution(
            ledger_path,
            tmp_path
            / "result.json",
        )
    )

    assert (
        state[
            "execution_recovery_allowed"
        ]
        is True
    )


def test_existing_result_blocks_execution(
    tmp_path: Path,
) -> None:
    result_path = (
        tmp_path
        / "result.json"
    )

    result_path.write_text(
        "{}",
        encoding="utf-8",
    )

    state = (
        module
        ._validate_ledger_state_before_execution(
            tmp_path
            / "ledger.json",
            result_path,
        )
    )

    assert (
        state[
            "state"
        ]
        == (
            "RESULT_ALREADY_EXISTS"
        )
    )

    assert (
        state[
            "execution_recovery_allowed"
        ]
        is False
    )


def test_build_preflight_reads_no_dataset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chain = {
        "core_attestation": {
            "a": 1,
        },
        "source_attestation": {
            "b": 2,
        },
        "validation_result": {
            "c": 3,
        },
        "validation_freeze": {
            "d": 4,
        },
        "core_source_sha256": (
            "1"
            * 64
        ),
        "source_source_sha256": (
            "2"
            * 64
        ),
        "ledger_state": {
            "state": (
                "ABSENT"
            ),
            (
                "execution_recovery_allowed"
            ): True,
            (
                "test_read_attempt_count"
            ): 0,
            (
                "holdout_consumed_for_"
                "rerun_policy"
            ): False,
        },
    }

    monkeypatch.setattr(
        module,
        "_validate_attestation_chain",
        lambda **kwargs: (
            chain
        ),
    )

    def forbidden_read_csv(
        *args: object,
        **kwargs: object,
    ) -> object:
        raise AssertionError(
            "dry preflight must "
            "not read dataset"
        )

    monkeypatch.setattr(
        module.pd,
        "read_csv",
        forbidden_read_csv,
    )

    report = (
        module
        .build_preflight(
            ledger_path=(
                tmp_path
                / "ledger.json"
            ),
            result_path=(
                tmp_path
                / "result.json"
            ),
        )
    )

    assert (
        report[
            "decision"
        ][
            "status"
        ]
        == (
            "ONE_TIME_TEST_"
            "DRY_PREFLIGHT_READY"
        )
    )

    assert (
        report[
            "decision"
        ][
            "real_test_execution_authorized_next"
        ]
        is True
    )

    assert (
        report[
            "decision"
        ][
            "real_test_values_loaded"
        ]
        is False
    )

    assert (
        report[
            "decision"
        ][
            "test_consumed"
        ]
        is False
    )

    assert (
        report[
            "decision"
        ][
            "live_authorized"
        ]
        is False
    )

    assert (
        report[
            "scientific_policy"
        ][
            "dataset_structural_read_performed"
        ]
        is False
    )


def test_stored_preflight_rejects_tampered_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = {
        "a": 1,
        "b": 2,
    }

    fingerprint = (
        module
        ._canonical_sha256(
            record
        )
    )

    stored = {
        "analysis_version": (
            module
            .ANALYSIS_VERSION
        ),
        "valid": True,
        "preflight_record": (
            record
        ),
        "preflight_fingerprint": {
            "sha256": (
                fingerprint
            ),
        },
        "decision": {
            (
                "real_test_execution_"
                "authorized_next"
            ): True,
        },
    }

    preflight_path = (
        tmp_path
        / "preflight.json"
    )

    preflight_path.write_text(
        json.dumps(
            stored
        ),
        encoding="utf-8",
    )

    current = json.loads(
        json.dumps(
            stored
        )
    )

    monkeypatch.setattr(
        module,
        "build_preflight",
        lambda **kwargs: (
            current
        ),
    )

    validated = (
        module
        .validate_stored_preflight(
            preflight_path=(
                preflight_path
            ),
            expected_fingerprint=(
                fingerprint
            ),
            ledger_path=(
                tmp_path
                / "ledger.json"
            ),
            result_path=(
                tmp_path
                / "result.json"
            ),
        )
    )

    assert (
        validated[
            "preflight_record"
        ]
        == record
    )

    tampered = json.loads(
        json.dumps(
            stored
        )
    )

    tampered[
        "preflight_record"
    ][
        "a"
    ] = 99

    preflight_path.write_text(
        json.dumps(
            tampered
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        module.OneTimeTestRunnerError,
        match=(
            "content fingerprint mismatch"
        ),
    ):
        module.validate_stored_preflight(
            preflight_path=(
                preflight_path
            ),
            expected_fingerprint=(
                fingerprint
            ),
            ledger_path=(
                tmp_path
                / "ledger.json"
            ),
            result_path=(
                tmp_path
                / "result.json"
            ),
        )


def test_artifact_source_reads_only_final_test_block(
    tmp_path: Path,
) -> None:
    feature_columns = [
        f"f_{index:03d}"
        for index
        in range(
            module
            .EXPECTED_FEATURE_COUNT
        )
    ]

    dataset_path = (
        tmp_path
        / "dataset.csv"
    )

    manifest_path = (
        tmp_path
        / "manifest.json"
    )

    class FakeLoader:
        def __init__(
            self,
            root: Path,
        ) -> None:
            self.root = (
                root
            )

        def _discover_exact_artifact(
            self,
        ) -> tuple[
            Path,
            Path,
            dict[str, Any],
        ]:
            return (
                dataset_path,
                manifest_path,
                {},
            )

        def _validate_manifest(
            self,
            manifest: dict[str, Any],
        ) -> tuple[
            list[str],
            list[str],
        ]:
            del manifest

            return (
                feature_columns,
                [
                    "target_class",
                    "target_tradeable",
                ],
            )

        def _feature_columns_sha256(
            self,
            columns: Sequence[str],
        ) -> str:
            assert (
                list(
                    columns
                )
                == feature_columns
            )

            return (
                module
                .EXPECTED_FEATURE_COLUMNS_SHA256
            )

        def _validate_split_series(
            self,
            split: pd.Series,
        ) -> None:
            assert (
                split.tolist()
                == [
                    "TRAIN",
                    "TRAIN",
                    "VALIDATION",
                    "VALIDATION",
                    "TEST",
                    "TEST",
                    "TEST",
                ]
            )

        def _normalize_target_class_array(
            self,
            values: pd.Series,
        ) -> np.ndarray:
            mapping = {
                "SHORT": -1,
                "NO_TRADE": 0,
                "LONG": 1,
            }

            return np.asarray(
                [
                    mapping[
                        str(
                            value
                        )
                    ]
                    for value
                    in values.tolist()
                ],
                dtype=np.int8,
            )

    calls: list[
        dict[
            str,
            object,
        ]
    ] = []

    def fake_read_csv(
        path: Path,
        **kwargs: object,
    ) -> pd.DataFrame:
        assert (
            path
            == dataset_path
        )

        calls.append(
            dict(
                kwargs
            )
        )

        usecols = list(
            cast(
                Sequence[str],
                kwargs[
                    "usecols"
                ],
            )
        )

        if (
            usecols
            == [
                "dataset_split"
            ]
        ):
            return pd.DataFrame(
                {
                    "dataset_split": [
                        "TRAIN",
                        "TRAIN",
                        "VALIDATION",
                        "VALIDATION",
                        "TEST",
                        "TEST",
                        "TEST",
                    ]
                }
            )

        assert (
            cast(
                int,
                kwargs[
                    "nrows"
                ],
            )
            == 3
        )

        skiprows = list(
            cast(
                Sequence[int],
                kwargs[
                    "skiprows"
                ],
            )
        )

        assert (
            skiprows
            == [
                1,
                2,
                3,
                4,
            ]
        )

        data: dict[
            str,
            object,
        ] = {
            "dataset_split": [
                "TEST",
                "TEST",
                "TEST",
            ],
            "target_class": [
                "SHORT",
                "NO_TRADE",
                "LONG",
            ],
        }

        for (
            index,
            column,
        ) in enumerate(
            feature_columns
        ):
            data[
                column
            ] = [
                float(
                    index
                ),
                float(
                    index
                    + 1
                ),
                float(
                    index
                    + 2
                ),
            ]

        return (
            pd.DataFrame(
                data
            )[
                usecols
            ]
        )

    class FakeCore:
        class ProtectedTestBatch:
            def __init__(
                self,
                *,
                X: np.ndarray,
                y_true: np.ndarray,
            ) -> None:
                self.X = np.asarray(
                    X
                )

                self.y_true = np.asarray(
                    y_true
                )

        @staticmethod
        def validate_test_batch(
            batch: Any,
        ) -> Any:
            assert (
                batch.X.shape
                == (
                    3,
                    331,
                )
            )

            assert (
                batch.y_true.tolist()
                == [
                    -1,
                    0,
                    1,
                ]
            )

            return batch

    class FakeBounded:
        def __init__(
            self,
            *,
            split_labels: Sequence[str],
            feature_columns: Sequence[str],
            feature_columns_sha256: str,
            read_bounded_rows: Callable[
                [
                    int,
                    int,
                    Sequence[str],
                ],
                pd.DataFrame,
            ],
            target_column: str,
            split_column: str,
            test_core_module: Any,
        ) -> None:
            assert (
                list(
                    split_labels[
                        -3:
                    ]
                )
                == [
                    "TEST",
                    "TEST",
                    "TEST",
                ]
            )

            assert (
                feature_columns_sha256
                == (
                    module
                    .EXPECTED_FEATURE_COLUMNS_SHA256
                )
            )

            self.feature_columns = list(
                feature_columns
            )

            self.read_bounded_rows = (
                read_bounded_rows
            )

            self.target_column = (
                target_column
            )

            self.split_column = (
                split_column
            )

            self.core = (
                test_core_module
            )

        def load_protected_test_batch(
            self,
        ) -> Any:
            columns = [
                self.split_column,
                *self.feature_columns,
                self.target_column,
            ]

            frame = (
                self.read_bounded_rows(
                    4,
                    7,
                    columns,
                )
            )

            assert (
                frame[
                    "dataset_split"
                ].tolist()
                == [
                    "TEST",
                    "TEST",
                    "TEST",
                ]
            )

            return (
                self.core
                .validate_test_batch(
                    self.core
                    .ProtectedTestBatch(
                        X=(
                            frame[
                                self.feature_columns
                            ].to_numpy()
                        ),
                        y_true=(
                            frame[
                                self.target_column
                            ].to_numpy()
                        ),
                    )
                )
            )

    source = (
        module
        .ArtifactBoundedTestSource(
            tmp_path,
            core_module=(
                FakeCore
            ),
            source_module=(
                SimpleNamespace(
                    AuthorizedBoundedTestSource=(
                        FakeBounded
                    )
                )
            ),
            loader_class=(
                FakeLoader
            ),
            read_csv=(
                fake_read_csv
            ),
        )
    )

    batch = source.load()

    assert (
        batch.X.shape
        == (
            3,
            331,
        )
    )

    assert (
        batch.y_true.tolist()
        == [
            -1,
            0,
            1,
        ]
    )

    assert (
        len(
            calls
        )
        == 2
    )

    assert (
        source.last_evidence
        is not None
    )

    assert (
        source.last_evidence[
            "read_policy"
        ][
            "value_read_split"
        ]
        == "TEST"
    )

    assert (
        source.last_evidence[
            "read_policy"
        ][
            "validation_feature_values_loaded"
        ]
        is False
    )


def test_prediction_requires_frozen_class_order() -> None:
    class BadModel:
        classes_ = np.asarray(
            [
                0,
                -1,
                1,
            ]
        )

        n_features_in_ = 331

        def predict_proba(
            self,
            X: np.ndarray,
        ) -> np.ndarray:
            return np.tile(
                [
                    [
                        0.2,
                        0.3,
                        0.5,
                    ]
                ],
                (
                    X.shape[
                        0
                    ],
                    1,
                ),
            )

    with pytest.raises(
        module.OneTimeTestRunnerError,
        match=(
            "class order mismatch"
        ),
    ):
        module._predict_probabilities(
            BadModel(),
            np.zeros(
                (
                    2,
                    331,
                )
            ),
        )


def test_execute_flag_without_fingerprint_never_executes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(
                MODULE_PATH
            ),
            "--execute-one-time-test",
        ],
    )

    called = False

    def forbidden_execute(
        **kwargs: object,
    ) -> object:
        nonlocal called

        called = True

        raise AssertionError(
            "must not execute"
        )

    monkeypatch.setattr(
        module,
        "execute_one_time_test",
        forbidden_execute,
    )

    result = (
        module.main()
    )

    assert (
        result
        == 2
    )

    assert (
        called
        is False
    )

    assert (
        "EXPECTED_PREFLIGHT_FINGERPRINT_REQUIRED"
        in (
            capsys
            .readouterr()
            .out
        )
    )