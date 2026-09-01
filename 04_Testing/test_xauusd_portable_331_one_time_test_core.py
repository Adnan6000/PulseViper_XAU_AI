from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest


MODULE_PATH = Path(
    __file__
).with_name(
    "xauusd_portable_331_one_time_test_core.py"
)

spec = (
    importlib.util.spec_from_file_location(
        "one_time_test_core",
        MODULE_PATH,
    )
)

assert spec is not None
assert spec.loader is not None

module = (
    importlib.util.module_from_spec(
        spec
    )
)

sys.modules[
    spec.name
] = module

spec.loader.exec_module(
    module
)


def _protocol() -> dict:
    return {
        "protocol_fingerprint": (
            module.EXPECTED_TEST_PROTOCOL_FINGERPRINT
        ),
    }


def _batch(
    rows: int = 9,
) -> object:
    X = np.zeros(
        (
            rows,
            module.EXPECTED_FEATURE_COUNT,
        ),
        dtype=np.float64,
    )

    pattern = np.asarray(
        [
            -1,
            0,
            1,
        ],
        dtype=np.int8,
    )

    y = np.resize(
        pattern,
        rows,
    )

    return module.ProtectedTestBatch(
        X=X,
        y_true=y,
    )


def _accepted_metrics() -> dict[
    str,
    float,
]:
    return {
        "balanced_accuracy_3class": 0.36,
        "macro_f1_3class": 0.30,
        (
            "directional_macro_f1_short_long"
        ): 0.29,
        "short_precision": 0.31,
        "short_recall": 0.30,
        "short_f1": 0.305,
        "no_trade_precision": 0.40,
        "no_trade_recall": 0.30,
        "no_trade_f1": 0.34,
        "long_precision": 0.32,
        "long_recall": 0.35,
        "long_f1": 0.334,
        "log_loss_3class": 1.10,
        "multiclass_brier": 0.67,
        "predicted_trade_coverage": 0.75,
    }


def _proba(
    X: np.ndarray,
) -> tuple[
    np.ndarray,
    list[int],
]:
    probabilities = np.tile(
        np.asarray(
            [
                [
                    0.34,
                    0.32,
                    0.34,
                ]
            ],
            dtype=np.float64,
        ),
        (
            X.shape[0],
            1,
        ),
    )

    return (
        probabilities,
        [
            -1,
            0,
            1,
        ],
    )


def test_ledger_is_persisted_before_read_boundary(
    tmp_path: Path,
) -> None:
    path = (
        tmp_path
        / "ledger.json"
    )

    ledger = (
        module.TestAccessLedger(
            path
        )
    )

    reserved = (
        ledger.reserve_before_read()
    )

    assert path.is_file()

    assert (
        reserved[
            "status"
        ]
        == module.STATUS_RESERVED
    )

    assert (
        reserved[
            "test_read_attempt_count"
        ]
        == 0
    )

    assert (
        reserved[
            "holdout_consumed_for_rerun_policy"
        ]
        is False
    )

    on_disk = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        on_disk[
            "status"
        ]
        == module.STATUS_RESERVED
    )


def test_read_initiation_consumes_and_second_read_is_blocked(
    tmp_path: Path,
) -> None:
    ledger = (
        module.TestAccessLedger(
            tmp_path
            / "ledger.json"
        )
    )

    ledger.reserve_before_read()

    consumed = (
        ledger.mark_read_initiated()
    )

    assert (
        consumed[
            "status"
        ]
        == module.STATUS_READ_INITIATED
    )

    assert (
        consumed[
            "test_read_attempt_count"
        ]
        == 1
    )

    assert (
        consumed[
            "holdout_consumed_for_rerun_policy"
        ]
        is True
    )

    with pytest.raises(
        module.OneTimeTestCoreError
    ):
        ledger.mark_read_initiated()

    with pytest.raises(
        module.OneTimeTestCoreError
    ):
        ledger.reserve_before_read()


def test_pre_read_failure_is_retriable_only_with_zero_reads(
    tmp_path: Path,
) -> None:
    ledger = (
        module.TestAccessLedger(
            tmp_path
            / "ledger.json"
        )
    )

    ledger.reserve_before_read()

    failed = (
        ledger.mark_technical_failure(
            error=(
                "synthetic pre-read failure"
            ),
            before_read_boundary=True,
        )
    )

    assert (
        failed[
            "status"
        ]
        == module.STATUS_PRE_READ_FAILURE
    )

    assert (
        failed[
            "test_read_attempt_count"
        ]
        == 0
    )

    assert (
        failed[
            "holdout_consumed_for_rerun_policy"
        ]
        is False
    )

    retried = (
        ledger.reserve_before_read()
    )

    assert (
        retried[
            "status"
        ]
        == module.STATUS_RESERVED
    )

    assert (
        retried[
            "test_read_attempt_count"
        ]
        == 0
    )


def test_post_read_failure_is_permanently_consumed(
    tmp_path: Path,
) -> None:
    ledger = (
        module.TestAccessLedger(
            tmp_path
            / "ledger.json"
        )
    )

    ledger.reserve_before_read()
    ledger.mark_read_initiated()

    failed = (
        ledger.mark_technical_failure(
            error=(
                "synthetic post-read failure"
            ),
            before_read_boundary=False,
        )
    )

    assert (
        failed[
            "status"
        ]
        == module.STATUS_CONSUMED_FAILURE
    )

    assert (
        failed[
            "test_read_attempt_count"
        ]
        == 1
    )

    assert (
        failed[
            "holdout_consumed_for_rerun_policy"
        ]
        is True
    )

    with pytest.raises(
        module.OneTimeTestCoreError
    ):
        ledger.reserve_before_read()


def test_batch_validation_rejects_wrong_feature_count_and_non_finite() -> None:
    wrong = (
        module.ProtectedTestBatch(
            X=np.zeros(
                (
                    6,
                    330,
                ),
                dtype=np.float64,
            ),
            y_true=np.asarray(
                [
                    -1,
                    0,
                    1,
                    -1,
                    0,
                    1,
                ],
                dtype=np.int8,
            ),
        )
    )

    with pytest.raises(
        module.OneTimeTestCoreError,
        match=(
            "TEST_FEATURE_COUNT_MISMATCH"
        ),
    ):
        module.validate_test_batch(
            wrong
        )

    X = np.zeros(
        (
            6,
            331,
        ),
        dtype=np.float64,
    )

    X[
        0,
        0,
    ] = np.nan

    non_finite = (
        module.ProtectedTestBatch(
            X=X,
            y_true=np.asarray(
                [
                    -1,
                    0,
                    1,
                    -1,
                    0,
                    1,
                ],
                dtype=np.int8,
            ),
        )
    )

    with pytest.raises(
        module.OneTimeTestCoreError,
        match="TEST_X_NON_FINITE",
    ):
        module.validate_test_batch(
            non_finite
        )


def test_acceptance_uses_frozen_train_floors() -> None:
    metrics = (
        _accepted_metrics()
    )

    accepted = (
        module.evaluate_acceptance(
            metrics
        )
    )

    assert (
        accepted.accepted
        is True
    )

    metrics[
        "directional_macro_f1_short_long"
    ] = 0.25

    rejected = (
        module.evaluate_acceptance(
            metrics
        )
    )

    assert (
        rejected.accepted
        is False
    )

    assert (
        rejected.hard_checks[
            "directional_macro_f1_short_long_floor"
        ]
        is False
    )


def test_synthetic_one_time_execution_accepts_and_freezes_ledger(
    tmp_path: Path,
) -> None:
    ledger = (
        module.TestAccessLedger(
            tmp_path
            / "ledger.json"
        )
    )

    result = (
        module.execute_one_time_test(
            protocol=(
                _protocol()
            ),
            ledger=ledger,
            load_test_batch=(
                lambda: _batch(
                    9
                )
            ),
            predict_probabilities=(
                _proba
            ),
            metric_evaluator=(
                lambda y, p:
                _accepted_metrics()
            ),
        )
    )

    assert (
        result[
            "status"
        ]
        == "ONE_TIME_TEST_ACCEPTED"
    )

    assert (
        result[
            "decision"
        ][
            "test_accepted"
        ]
        is True
    )

    assert (
        result[
            "decision"
        ][
            "test_rerun_authorized"
        ]
        is False
    )

    assert (
        result[
            "decision"
        ][
            "live_authorized"
        ]
        is False
    )

    final_ledger = (
        ledger.read()
    )

    assert (
        final_ledger[
            "status"
        ]
        == module.STATUS_COMPLETE_ACCEPTED
    )

    assert (
        final_ledger[
            "test_read_attempt_count"
        ]
        == 1
    )

    assert (
        final_ledger[
            "holdout_consumed_for_rerun_policy"
        ]
        is True
    )

    assert (
        final_ledger[
            "test_metrics_computed"
        ]
        is True
    )

    assert (
        final_ledger[
            "test_accepted"
        ]
        is True
    )


def test_synthetic_one_time_execution_rejection_is_still_consumed(
    tmp_path: Path,
) -> None:
    ledger = (
        module.TestAccessLedger(
            tmp_path
            / "ledger.json"
        )
    )

    metrics = (
        _accepted_metrics()
    )

    metrics[
        "balanced_accuracy_3class"
    ] = 0.30

    result = (
        module.execute_one_time_test(
            protocol=(
                _protocol()
            ),
            ledger=ledger,
            load_test_batch=(
                lambda: _batch(
                    9
                )
            ),
            predict_probabilities=(
                _proba
            ),
            metric_evaluator=(
                lambda y, p:
                metrics
            ),
        )
    )

    assert (
        result[
            "status"
        ]
        == "ONE_TIME_TEST_REJECTED"
    )

    assert (
        result[
            "decision"
        ][
            "test_accepted"
        ]
        is False
    )

    assert (
        result[
            "decision"
        ][
            "test_rerun_authorized"
        ]
        is False
    )

    final_ledger = (
        ledger.read()
    )

    assert (
        final_ledger[
            "status"
        ]
        == module.STATUS_COMPLETE_REJECTED
    )

    assert (
        final_ledger[
            "holdout_consumed_for_rerun_policy"
        ]
        is True
    )


def test_exception_after_read_boundary_records_consumed_failure(
    tmp_path: Path,
) -> None:
    ledger = (
        module.TestAccessLedger(
            tmp_path
            / "ledger.json"
        )
    )

    def broken_loader() -> object:
        raise RuntimeError(
            "synthetic loader failure"
        )

    with pytest.raises(
        RuntimeError,
        match=(
            "synthetic loader failure"
        ),
    ):
        module.execute_one_time_test(
            protocol=(
                _protocol()
            ),
            ledger=ledger,
            load_test_batch=(
                broken_loader
            ),
            predict_probabilities=(
                _proba
            ),
            metric_evaluator=(
                lambda y, p:
                _accepted_metrics()
            ),
        )

    final_ledger = (
        ledger.read()
    )

    assert (
        final_ledger[
            "status"
        ]
        == module.STATUS_CONSUMED_FAILURE
    )

    assert (
        final_ledger[
            "test_read_attempt_count"
        ]
        == 1
    )

    assert (
        final_ledger[
            "holdout_consumed_for_rerun_policy"
        ]
        is True
    )


def test_probability_validation_rejects_wrong_class_order() -> None:
    probabilities = np.asarray(
        [
            [
                0.2,
                0.3,
                0.5,
            ]
        ],
        dtype=np.float64,
    )

    with pytest.raises(
        module.OneTimeTestCoreError,
        match=(
            "PREDICTION_CLASS_ORDER_MISMATCH"
        ),
    ):
        module.validate_probability_output(
            probabilities,
            expected_rows=1,
            model_class_order=[
                0,
                -1,
                1,
            ],
        )


def test_core_attestation_never_authorizes_real_test_execution() -> None:
    document = (
        module.build_core_attestation(
            _protocol(),
            source_sha256=(
                "a" * 64
            ),
        )
    )

    assert (
        document[
            "valid"
        ]
        is True
    )

    assert (
        document[
            "status"
        ]
        == module.ATTESTATION_STATUS
    )

    assert (
        document[
            "verified_properties"
        ][
            "real_test_values_accessed"
        ]
        is False
    )

    assert (
        document[
            "decision"
        ][
            "bounded_test_source_implementation_authorized_next"
        ]
        is True
    )

    assert (
        document[
            "decision"
        ][
            "test_execution_authorized"
        ]
        is False
    )

    assert (
        document[
            "decision"
        ][
            "live_authorized"
        ]
        is False
    )