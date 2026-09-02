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
        "one_time_test_recovery_runner",
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

    probabilities = np.asarray(
        [
            [
                0.8,
                0.1,
                0.1,
            ],
            [
                0.1,
                0.8,
                0.1,
            ],
            [
                0.1,
                0.1,
                0.8,
            ],
            [
                0.7,
                0.2,
                0.1,
            ],
            [
                0.2,
                0.7,
                0.1,
            ],
            [
                0.1,
                0.2,
                0.7,
            ],
        ],
        dtype=np.float64,
    )

    return (
        y,
        probabilities,
    )


def test_metric_contract_contains_exact_15_metrics() -> None:
    (
        y,
        probabilities,
    ) = _perfect_case()

    metrics = (
        module
        .evaluate_test_metrics(
            y,
            probabilities,
        )
    )

    assert (
        len(
            metrics
        )
        == 15
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
            "directional_macro_f1_short_long"
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


def test_multiclass_brier_matches_manual_definition() -> None:
    (
        y,
        probabilities,
    ) = _perfect_case()

    metrics = (
        module
        .evaluate_test_metrics(
            y,
            probabilities,
        )
    )

    one_hot = (
        np.zeros_like(
            probabilities
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
                    probabilities
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

    probabilities = np.zeros(
        (
            3,
            2,
        ),
        dtype=np.float64,
    )

    with pytest.raises(
        module.OneTimeTestRecoveryRunnerError,
        match=(
            "probability shape mismatch"
        ),
    ):
        module.evaluate_test_metrics(
            y,
            probabilities,
        )


def test_json_safe_normalizes_numpy_values() -> None:
    value = {
        "array": np.asarray(
            [
                1,
                2,
            ]
        ),
        "scalar": np.float64(
            1.25
        ),
    }

    normalized = (
        module
        ._json_safe(
            value
        )
    )

    assert normalized == {
        "array": [
            1,
            2,
        ],
        "scalar": 1.25,
    }


def test_absent_ledger_allows_recovery(
    tmp_path: Path,
) -> None:
    state = (
        module
        ._validate_ledger_state_for_recovery(
            tmp_path
            / "ledger.json",
            tmp_path
            / "recovery_result.json",
        )
    )

    assert (
        state[
            "state"
        ]
        == "ABSENT"
    )

    assert (
        state[
            "recovery_execution_allowed"
        ]
        is True
    )

    assert (
        state[
            "test_read_attempt_count"
        ]
        == 0
    )

    assert (
        state[
            "holdout_consumed_for_rerun_policy"
        ]
        is False
    )


def test_existing_recovery_result_blocks_recovery(
    tmp_path: Path,
) -> None:
    recovery_result = (
        tmp_path
        / "recovery_result.json"
    )

    recovery_result.write_text(
        "{}",
        encoding="utf-8",
    )

    state = (
        module
        ._validate_ledger_state_for_recovery(
            tmp_path
            / "ledger.json",
            recovery_result,
        )
    )

    assert (
        state[
            "recovery_execution_allowed"
        ]
        is False
    )


def test_original_pre_read_failure_evidence_is_accepted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preflight_record = {
        "x": 1,
    }

    fingerprint = (
        module
        ._canonical_sha256(
            preflight_record
        )
    )

    monkeypatch.setattr(
        module,
        (
            "EXPECTED_ORIGINAL_"
            "PREFLIGHT_FINGERPRINT"
        ),
        fingerprint,
    )

    original_preflight = {
        "valid": True,
        "preflight_record": (
            preflight_record
        ),
        "preflight_fingerprint": {
            "sha256": (
                fingerprint
            ),
        },
    }

    original_failure = {
        "valid": False,
        "reason": (
            "ONE_TIME_REAL_TEST_"
            "EXECUTION_FAILED"
        ),
        "error_type": (
            "ImportError"
        ),
        "error": (
            "attempted relative import "
            "with no known parent package"
        ),
        "ledger_state": None,
        "scientific_policy": {
            (
                "validation_reread_authorized"
            ): False,
            "test_rerun_authorized": False,
            "shadow_authorized": False,
            "live_authorized": False,
        },
    }

    preflight_path = (
        tmp_path
        / "original_preflight.json"
    )

    failure_path = (
        tmp_path
        / "original_failure.json"
    )

    ledger_path = (
        tmp_path
        / "ledger.json"
    )

    preflight_path.write_text(
        json.dumps(
            original_preflight
        ),
        encoding="utf-8",
    )

    failure_path.write_text(
        json.dumps(
            original_failure
        ),
        encoding="utf-8",
    )

    evidence = (
        module
        ._validate_original_pre_read_failure(
            original_preflight_path=(
                preflight_path
            ),
            original_failure_path=(
                failure_path
            ),
            ledger_path=(
                ledger_path
            ),
        )
    )

    assert (
        evidence[
            "ledger_absent_after_original_failure"
        ]
        is True
    )


def test_loader_class_uses_proven_validation_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeLoader:
        pass

    FakeLoader.__name__ = (
        "Portable331TrainingInputLoader"
    )

    fake_validation_source = (
        SimpleNamespace(
            _load_loader_class=(
                lambda: FakeLoader
            )
        )
    )

    monkeypatch.setattr(
        module,
        "_load_module",
        lambda *args, **kwargs: (
            fake_validation_source
        ),
    )

    loader_class = (
        module
        ._load_loader_class_via_proven_path()
    )

    assert (
        loader_class
        is FakeLoader
    )


def test_build_recovery_preflight_reads_no_dataset(
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
        "validation_source_sha256": (
            "3"
            * 64
        ),
        "integration_runner_sha256": (
            "4"
            * 64
        ),
        "ledger_state": {
            "state": (
                "ABSENT"
            ),
            (
                "recovery_execution_allowed"
            ): True,
            (
                "test_read_attempt_count"
            ): 0,
            (
                "holdout_consumed_for_rerun_policy"
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

    monkeypatch.setattr(
        module,
        (
            "_validate_original_"
            "pre_read_failure"
        ),
        lambda **kwargs: {
            (
                "original_preflight_sha256"
            ): (
                "5"
                * 64
            ),
            (
                "original_failure_sha256"
            ): (
                "6"
                * 64
            ),
            (
                "original_failure_canonical_sha256"
            ): (
                "7"
                * 64
            ),
            "original_failure_error_type": (
                "ImportError"
            ),
            "original_failure_error": (
                module
                .EXPECTED_PRE_READ_ERROR_TEXT
            ),
            (
                "ledger_absent_after_original_failure"
            ): True,
        },
    )

    monkeypatch.setattr(
        module,
        "_probe_pre_read_dependencies",
        lambda: {
            (
                "proven_loader_import_probe"
            ): True,
            (
                "dataset_structural_read_performed"
            ): False,
            "test_values_loaded": False,
        },
    )

    monkeypatch.setattr(
        module,
        "_sha256_file",
        lambda path: (
            "8"
            * 64
        ),
    )

    def forbidden_read_csv(
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        raise AssertionError(
            "dataset read forbidden"
        )

    monkeypatch.setattr(
        module.pd,
        "read_csv",
        forbidden_read_csv,
    )

    report = (
        module
        .build_recovery_preflight()
    )

    assert (
        report[
            "decision"
        ][
            "status"
        ]
        == (
            "ONE_TIME_TEST_PRE_READ_"
            "RECOVERY_PREFLIGHT_READY"
        )
    )

    assert (
        report[
            "decision"
        ][
            "test_consumption_boundary_crossed"
        ]
        is False
    )

    assert (
        report[
            "decision"
        ][
            "real_test_values_loaded_in_recovery"
        ]
        is False
    )


def test_stored_recovery_preflight_rejects_tamper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = {
        "a": 1,
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
                "recovery_execution_"
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

    monkeypatch.setattr(
        module,
        "build_recovery_preflight",
        lambda **kwargs: (
            stored
        ),
    )

    validated = (
        module
        .validate_stored_recovery_preflight(
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
            recovery_result_path=(
                tmp_path
                / "result.json"
            ),
        )
    )

    assert (
        validated[
            "valid"
        ]
        is True
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
    ] = 2

    preflight_path.write_text(
        json.dumps(
            tampered
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        module.OneTimeTestRecoveryRunnerError,
        match=(
            "content fingerprint mismatch"
        ),
    ):
        module.validate_stored_recovery_preflight(
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
            recovery_result_path=(
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
                    "VALIDATION",
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
                        "VALIDATION",
                        "TEST",
                        "TEST",
                    ]
                }
            )

        assert (
            list(
                cast(
                    Sequence[int],
                    kwargs[
                        "skiprows"
                    ],
                )
            )
            == [
                1,
                2,
            ]
        )

        assert (
            cast(
                int,
                kwargs[
                    "nrows"
                ],
            )
            == 2
        )

        data: dict[
            str,
            object,
        ] = {
            "dataset_split": [
                "TEST",
                "TEST",
            ],
            "target_class": [
                "SHORT",
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
                self.X = (
                    np.asarray(
                        X
                    )
                )

                self.y_true = (
                    np.asarray(
                        y_true
                    )
                )

        @staticmethod
        def validate_test_batch(
            batch: Any,
        ) -> Any:
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
            del split_labels

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
            frame = (
                self.read_bounded_rows(
                    2,
                    4,
                    [
                        self.split_column,
                        *self.feature_columns,
                        self.target_column,
                    ],
                )
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

    batch = (
        source.load()
    )

    assert (
        batch.X.shape
        == (
            2,
            331,
        )
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
        module.OneTimeTestRecoveryRunnerError,
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


def test_execute_preserves_opaque_core_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        module,
        (
            "validate_stored_"
            "recovery_preflight"
        ),
        lambda **kwargs: {
            "valid": True,
        },
    )

    class FakeLedger:
        def __init__(
            self,
            *,
            path: Path,
            protocol_fingerprint: str,
        ) -> None:
            self.path = (
                path
            )

            self.protocol_fingerprint = (
                protocol_fingerprint
            )

        def read(
            self,
        ) -> dict[str, Any]:
            return {
                "status": (
                    "TEST_COMPLETE_ACCEPTED"
                ),
                (
                    "test_read_attempt_count"
                ): 1,
                (
                    "holdout_consumed_for_"
                    "rerun_policy"
                ): True,
            }

    class FakeCore:
        TestAccessLedger = (
            FakeLedger
        )

        @staticmethod
        def execute_one_time_test(
            **kwargs: Any,
        ) -> dict[str, Any]:
            del kwargs

            return {
                "strange_schema": {
                    "numpy_value": (
                        np.float64(
                            2.5
                        )
                    )
                }
            }

    class FakeAdapter:
        def __init__(
            self,
            *args: Any,
            **kwargs: Any,
        ) -> None:
            del args
            del kwargs

            self.last_evidence = {
                "ok": True,
            }

        def load(
            self,
        ) -> Any:
            raise AssertionError(
                "fake core does not "
                "call datasource"
            )

    class Model:
        classes_ = np.asarray(
            [
                -1,
                0,
                1,
            ]
        )

        n_features_in_ = 331

    dependencies = {
        "core": (
            FakeCore
        ),
        "source_module": (
            SimpleNamespace()
        ),
        "loader_class": (
            type(
                "Portable331TrainingInputLoader",
                (),
                {},
            )
        ),
        "protocol": {},
        "model": (
            Model()
        ),
    }

    monkeypatch.setattr(
        module,
        "_prepare_execution_dependencies",
        lambda: (
            dependencies
        ),
    )

    monkeypatch.setattr(
        module,
        "ArtifactBoundedTestSource",
        FakeAdapter,
    )

    original_failure = (
        tmp_path
        / "old_failure.json"
    )

    original_failure.write_text(
        "{}",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module,
        "ORIGINAL_FAILED_RESULT_PATH",
        original_failure,
    )

    report = (
        module
        .execute_recovered_one_time_test(
            expected_recovery_preflight_fingerprint=(
                "a"
                * 64
            ),
            canonical_root=(
                tmp_path
            ),
            preflight_path=(
                tmp_path
                / "preflight.json"
            ),
            ledger_path=(
                tmp_path
                / "ledger.json"
            ),
            recovery_result_path=(
                tmp_path
                / "recovery_result.json"
            ),
        )
    )

    assert (
        report[
            "decision"
        ][
            "test_accepted"
        ]
        is True
    )

    assert (
        report[
            "result_record"
        ][
            "core_result"
        ][
            "strange_schema"
        ][
            "numpy_value"
        ]
        == 2.5
    )


def test_recovery_execution_flag_requires_fingerprint(
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
            (
                "--execute-one-time-"
                "test-recovery"
            ),
        ],
    )

    called = False

    def forbidden_execute(
        **kwargs: Any,
    ) -> Any:
        nonlocal called

        called = True

        raise AssertionError(
            "must not execute"
        )

    monkeypatch.setattr(
        module,
        (
            "execute_recovered_"
            "one_time_test"
        ),
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

    output = (
        capsys
        .readouterr()
        .out
    )

    assert (
        "EXPECTED_RECOVERY_PREFLIGHT_"
        "FINGERPRINT_REQUIRED"
        in output
    )