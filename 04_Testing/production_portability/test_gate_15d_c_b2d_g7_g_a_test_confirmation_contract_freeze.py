from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any


RUNNER_PATH = (
    Path(__file__)
    .resolve()
    .parent
    /
    "run_xauusd_gate_15d_c_b2d_g7_g_a_test_confirmation_contract_freeze.py"
)


spec = importlib.util.spec_from_file_location(
    "g7ga",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g7ga: Any = (
    importlib.util.module_from_spec(
        spec
    )
)

spec.loader.exec_module(
    g7ga
)


contract: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_test_confirmation_contract"
)

winner: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_final_winner_contract"
)


def test_01_base_authority_exact() -> None:

    assert (
        contract.BASE_AUTHORITY_COMMIT
        ==
        "648939914f74ae993829105274e10146c137414e"
    )


def test_02_winner_contract_fingerprint_exact() -> None:

    assert (
        contract.FINAL_WINNER_CONTRACT_FINGERPRINT_SHA256
        ==
        "1c0a7e91b318973f319de4a01b9f850e80f236c9211b4866f52cbb330a973f91"
    )


def test_03_upstream_winner_contract_matches() -> None:

    assert (
        winner.CONTRACT_FINGERPRINT_SHA256
        ==
        contract.FINAL_WINNER_CONTRACT_FINGERPRINT_SHA256
    )


def test_04_winner_id_exact() -> None:

    assert (
        contract.WINNER_CANDIDATE_ID
        ==
        "R03_FLAT_EXTRA_TREES_SMOOTH"
    )


def test_05_test_one_shot() -> None:

    assert (
        contract.TEST_ACCESS_COUNT_MAXIMUM
        ==
        1
    )


def test_06_train_only_fit_required() -> None:

    assert (
        contract.TRAIN_ONLY_MODEL_FIT_REQUIRED
        is True
    )


def test_07_no_train_validation_refit() -> None:

    assert (
        contract.TRAIN_PLUS_VALIDATION_REFIT_ALLOWED
        is False
    )


def test_08_no_validation_reevaluation() -> None:

    assert (
        contract.VALIDATION_REEVALUATION_ALLOWED_DURING_TEST
        is False
    )


def test_09_no_forward30_use() -> None:

    assert (
        contract.OLD_FORWARD_30_USE_ALLOWED_DURING_TEST
        is False
    )


def test_10_macro_f1_threshold_exact() -> None:

    assert (
        contract.TEST_MACRO_F1_MINIMUM
        ==
        contract.VALIDATION_MACRO_F1
        *
        0.90
    )


def test_11_balanced_accuracy_threshold_exact() -> None:

    assert (
        contract.TEST_BALANCED_ACCURACY_MINIMUM
        ==
        contract.VALIDATION_BALANCED_ACCURACY
        *
        0.90
    )


def test_12_min_recall_threshold_exact() -> None:

    assert (
        contract.TEST_MINIMUM_PER_CLASS_RECALL_MINIMUM
        ==
        contract.VALIDATION_MINIMUM_PER_CLASS_RECALL
        *
        0.80
    )


def test_13_brier_threshold_exact() -> None:

    assert (
        contract.TEST_MULTICLASS_BRIER_MAXIMUM
        ==
        contract.VALIDATION_MULTICLASS_BRIER
        +
        0.05
    )


def test_14_logloss_threshold_exact() -> None:

    assert (
        contract.TEST_MULTICLASS_LOG_LOSS_MAXIMUM
        ==
        contract.VALIDATION_MULTICLASS_LOG_LOSS
        +
        0.10
    )


def test_15_all_classes_required() -> None:

    assert (
        contract.ALL_THREE_CLASSES_MUST_BE_PREDICTED
        is True
    )


def test_16_class_share_bounds() -> None:

    assert (
        contract.MINIMUM_PREDICTED_CLASS_SHARE
        ==
        0.01
    )

    assert (
        contract.MAXIMUM_PREDICTED_CLASS_SHARE
        ==
        0.90
    )


def test_17_all_criteria_required() -> None:

    assert (
        contract.ALL_CONFIRMATION_CRITERIA_MUST_PASS
        is True
    )


def test_18_no_manual_pass_override() -> None:

    assert (
        contract.NO_MANUAL_OVERRIDE_TO_PASS_ALLOWED
        is True
    )


def test_19_no_posthoc_exception() -> None:

    assert (
        contract.NO_POST_HOC_EXCEPTION_ALLOWED
        is True
    )


def test_20_test_result_cannot_tune_same_test() -> None:

    assert (
        contract.TEST_RESULT_MAY_NOT_BE_USED_FOR_SAME_TEST_TUNING
        is True
    )

    assert (
        contract.TEST_RESULT_MAY_NOT_TRIGGER_THRESHOLD_TUNING
        is True
    )

    assert (
        contract.TEST_RESULT_MAY_NOT_TRIGGER_CALIBRATION
        is True
    )


def test_21_test_pass_does_not_authorize_live() -> None:

    assert (
        contract.TEST_PASS_DOES_NOT_AUTHORIZE_LIVE_TRADING
        is True
    )

    assert (
        contract.TEST_PASS_DOES_NOT_AUTHORIZE_EXECUTION
        is True
    )


def test_22_boundary_metrics_pass() -> None:

    metrics = {
        "macro_f1": (
            contract.TEST_MACRO_F1_MINIMUM
        ),
        "balanced_accuracy": (
            contract.TEST_BALANCED_ACCURACY_MINIMUM
        ),
        "minimum_per_class_recall": (
            contract.TEST_MINIMUM_PER_CLASS_RECALL_MINIMUM
        ),
        "short_recall": 0.30,
        "no_trade_recall": 0.30,
        "long_recall": 0.30,
        "multiclass_brier": (
            contract.TEST_MULTICLASS_BRIER_MAXIMUM
        ),
        "multiclass_log_loss": (
            contract.TEST_MULTICLASS_LOG_LOSS_MAXIMUM
        ),
        "prediction_counts": {
            "SHORT": 4500,
            "NO_TRADE": 5000,
            "LONG": 5496,
        },
        "prediction_shares": {
            "SHORT": 4500 / 14996,
            "NO_TRADE": 5000 / 14996,
            "LONG": 5496 / 14996,
        },
    }

    result = (
        contract.evaluate_test_confirmation(
            metrics
        )
    )

    assert result[
        "passed"
    ] is True

    assert result[
        "status"
    ] == contract.PASS_STATUS


def test_23_macro_failure_detected() -> None:

    metrics = {
        "macro_f1": (
            contract.TEST_MACRO_F1_MINIMUM
            -
            0.000001
        ),
        "balanced_accuracy": 0.40,
        "minimum_per_class_recall": 0.30,
        "short_recall": 0.30,
        "no_trade_recall": 0.30,
        "long_recall": 0.30,
        "multiclass_brier": 0.66,
        "multiclass_log_loss": 1.09,
        "prediction_counts": {
            "SHORT": 4500,
            "NO_TRADE": 5000,
            "LONG": 5496,
        },
        "prediction_shares": {
            "SHORT": 4500 / 14996,
            "NO_TRADE": 5000 / 14996,
            "LONG": 5496 / 14996,
        },
    }

    result = (
        contract.evaluate_test_confirmation(
            metrics
        )
    )

    assert result[
        "passed"
    ] is False

    assert (
        "MACRO_F1_BELOW_MINIMUM"
        in
        result[
            "failures"
        ]
    )


def test_24_class_collapse_detected() -> None:

    metrics = {
        "macro_f1": 0.40,
        "balanced_accuracy": 0.40,
        "minimum_per_class_recall": 0.30,
        "short_recall": 0.30,
        "no_trade_recall": 0.30,
        "long_recall": 0.30,
        "multiclass_brier": 0.66,
        "multiclass_log_loss": 1.09,
        "prediction_counts": {
            "SHORT": 0,
            "NO_TRADE": 7000,
            "LONG": 7996,
        },
        "prediction_shares": {
            "SHORT": 0.0,
            "NO_TRADE": 7000 / 14996,
            "LONG": 7996 / 14996,
        },
    }

    result = (
        contract.evaluate_test_confirmation(
            metrics
        )
    )

    assert result[
        "passed"
    ] is False

    assert (
        "CLASS_NOT_PREDICTED:SHORT"
        in
        result[
            "failures"
        ]
    )


def test_25_contract_fingerprint_consistent() -> None:

    assert (
        contract.CONTRACT_FINGERPRINT_SHA256
        ==
        contract.contract_fingerprint_sha256()
    )


def test_26_freeze_gate_has_no_data_access() -> None:

    assert (
        contract.THIS_GATE_LOADS_TRAIN_VALUES
        is False
    )

    assert (
        contract.THIS_GATE_LOADS_VALIDATION_VALUES
        is False
    )

    assert (
        contract.THIS_GATE_LOADS_TEST_VALUES
        is False
    )


def test_27_freeze_gate_has_no_evaluation() -> None:

    assert (
        contract.THIS_GATE_TRAINS_MODEL
        is False
    )

    assert (
        contract.THIS_GATE_EVALUATES_TEST
        is False
    )


def test_28_runner_has_no_test_loader_call() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "load_test_features(" not in text
    assert "load_test_targets(" not in text
    assert "load_test_supervised(" not in text


def test_29_runner_has_no_model_fit() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert ".fit(" not in text


def test_30_runner_has_no_mt5() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text
    assert "copy_ticks" not in text
    assert "copy_rates" not in text
    assert "order_send(" not in text


def test_31_runtime_ledgers_protected() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "PROTECTED_LEDGER_CHANGED_DURING_G7GA"
        in text
    )


def test_32_live_execution_blocked() -> None:

    assert (
        contract.LIVE_AUTHORIZED
        is False
    )

    assert (
        contract.EXECUTION_AUTHORIZED
        is False
    )