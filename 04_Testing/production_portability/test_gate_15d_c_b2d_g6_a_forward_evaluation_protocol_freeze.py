from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

CONTRACT_PATH = (
    ROOT
    / "02_AI/Models/"
    "frozen_c04_forward_performance_evaluation_contract.py"
)

RUNNER_PATH = (
    Path(__file__).resolve().parent
    / "run_xauusd_gate_15d_c_b2d_g6_a_forward_evaluation_protocol_freeze.py"
)


contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_performance_evaluation_contract"
)


spec = importlib.util.spec_from_file_location(
    "g6a_freeze",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g6a: Any = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    g6a
)


def test_01_baseline_is_g5_30() -> None:

    assert (
        contract.BASELINE_G5_AUTHORITY_COMMIT
        ==
        "c82abaf6008e9239cecae5fef4fde24936ad6358"
    )

    assert (
        contract.BASELINE_MATURED_OUTCOME_COUNT
        ==
        30
    )


def test_02_weekly_cadence_is_frozen() -> None:

    assert (
        contract.EVALUATION_CADENCE
        ==
        "WEEKLY"
    )

    assert (
        contract.WEEK_TIMEZONE
        ==
        "UTC"
    )

    assert (
        contract.WEEK_START_DAY
        ==
        "MONDAY"
    )


def test_03_no_fixed_count_wait() -> None:

    assert (
        contract.MINIMUM_NEW_WEEKLY_SAMPLE_COUNT
        ==
        0
    )

    assert (
        contract.FIXED_COUNT_WAIT_REQUIRED
        is False
    )

    assert (
        contract.MULTI_DAY_FIXED_SAMPLE_COLLECTION_REQUIRED
        is False
    )


def test_04_class_order_is_frozen() -> None:

    assert (
        contract.CLASS_ORDER
        ==
        (
            -1,
            0,
            1,
        )
    )


def test_05_metrics_are_predeclared() -> None:

    expected = {
        "EXACT_CLASS_ACCURACY",
        "CONFUSION_MATRIX",
        "PER_CLASS_PRECISION",
        "PER_CLASS_RECALL",
        "PER_CLASS_F1",
        "MACRO_F1",
        "BALANCED_ACCURACY",
        "PREDICTION_DISTRIBUTION",
        "OUTCOME_DISTRIBUTION",
        "MULTICLASS_BRIER_SCORE",
        "MULTICLASS_LOG_LOSS",
        "SAMPLE_COUNT",
        "COVERAGE_PERIOD",
    }

    assert set(
        contract.FROZEN_METRICS
    ) == expected


def test_06_confusion_matrix_semantics() -> None:

    assert (
        contract.CONFUSION_MATRIX_ROW_SEMANTICS
        ==
        "TRUE_OUTCOME_CLASS"
    )

    assert (
        contract.CONFUSION_MATRIX_COLUMN_SEMANTICS
        ==
        "PREDICTED_CLASS"
    )


def test_07_probability_order_matches_classes() -> None:

    assert (
        contract.PROBABILITY_COLUMN_ORDER
        ==
        (
            "probability_short",
            "probability_no_trade",
            "probability_long",
        )
    )


def test_08_no_calibration_or_tuning() -> None:

    assert (
        contract.PROBABILITY_CALIBRATION_ALLOWED
        is False
    )

    assert (
        contract.RETRAINING_ALLOWED
        is False
    )

    assert (
        contract.REFITTING_ALLOWED
        is False
    )

    assert (
        contract.MODEL_RESELECTION_ALLOWED
        is False
    )

    assert (
        contract.THRESHOLD_TUNING_ALLOWED
        is False
    )

    assert (
        contract.HYPERPARAMETER_TUNING_ALLOWED
        is False
    )


def test_09_no_post_hoc_sample_manipulation() -> None:

    assert (
        contract.PERFORMANCE_BASED_DATA_EXCLUSION_ALLOWED
        is False
    )

    assert (
        contract.POST_HOC_SAMPLE_REMOVAL_ALLOWED
        is False
    )


def test_10_no_premature_pass_fail_threshold() -> None:

    assert (
        contract.PASS_FAIL_THRESHOLD_DEFINED
        is False
    )

    assert (
        contract.PRODUCTION_PROMOTION_DECISION_AUTHORIZED
        is False
    )


def test_11_execution_boundaries_remain_closed() -> None:

    assert (
        contract.PNL_EVALUATION_AUTHORIZED
        is False
    )

    assert (
        contract.LIVE_AUTHORIZED
        is False
    )

    assert (
        contract.EXECUTION_AUTHORIZED
        is False
    )


def test_12_contract_fingerprint_is_deterministic() -> None:

    assert (
        contract.contract_fingerprint_sha256()
        ==
        contract.CONTRACT_FINGERPRINT_SHA256
    )

    assert len(
        contract.CONTRACT_FINGERPRINT_SHA256
    ) == 64


def test_13_runner_does_not_calculate_performance() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        '"performance_calculated": False'
        in text
    )

    assert "accuracy_score(" not in text
    assert "f1_score(" not in text
    assert "log_loss(" not in text


def test_14_runner_does_not_touch_mt5() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text
    assert "order_send(" not in text
    assert "order_check(" not in text


def test_15_g5_baseline_is_required() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "verify_g5_baseline" in text
    assert "G5_MATURED_COUNT_NOT_30" in text
    assert "G5_PENDING_COUNT_NOT_ZERO" in text


def test_16_weekly_rule_is_checked_by_freeze() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "WEEKLY_CADENCE_NOT_FROZEN" in text
    assert "FIXED_COUNT_WAIT_PRESENT" in text