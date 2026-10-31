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
    "run_xauusd_gate_15d_c_b2d_g7_h_a_r03_prospective_forward_contract_freeze.py"
)


spec = importlib.util.spec_from_file_location(
    "g7ha",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g7ha: Any = (
    importlib.util.module_from_spec(
        spec
    )
)

spec.loader.exec_module(
    g7ha
)


contract: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_r03_prospective_forward_validation_contract"
)

winner: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_final_winner_contract"
)

test_contract: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_test_confirmation_contract"
)


def passing_metrics() -> dict[str, Any]:

    return {
        "macro_f1": (
            contract.PROSPECTIVE_MACRO_F1_MINIMUM
        ),
        "balanced_accuracy": (
            contract.PROSPECTIVE_BALANCED_ACCURACY_MINIMUM
        ),
        "minimum_per_class_recall": (
            contract.PROSPECTIVE_MINIMUM_PER_CLASS_RECALL_MINIMUM
        ),
        "short_recall": 0.25,
        "no_trade_recall": 0.25,
        "long_recall": 0.25,
        "multiclass_brier": (
            contract.PROSPECTIVE_MULTICLASS_BRIER_MAXIMUM
        ),
        "multiclass_log_loss": (
            contract.PROSPECTIVE_MULTICLASS_LOG_LOSS_MAXIMUM
        ),
        "prediction_counts": {
            "SHORT": 18,
            "NO_TRADE": 18,
            "LONG": 24,
        },
        "prediction_shares": {
            "SHORT": 0.30,
            "NO_TRADE": 0.30,
            "LONG": 0.40,
        },
    }


def test_01_base_authority_exact() -> None:

    assert (
        contract.BASE_AUTHORITY_COMMIT
        ==
        "a520c646aa6fb8bff139219f7101eb0d4aa07b43"
    )


def test_02_winner_fingerprint_exact() -> None:

    assert (
        contract.WINNER_CANDIDATE_FINGERPRINT_SHA256
        ==
        "ae644c7272a015c26daeaaa7e655120bd7a3e4d267b2acd0d1f235e10bfa2e5f"
    )


def test_03_winner_contract_linkage() -> None:

    assert (
        winner.CONTRACT_FINGERPRINT_SHA256
        ==
        contract.FINAL_WINNER_CONTRACT_FINGERPRINT_SHA256
    )


def test_04_test_contract_linkage() -> None:

    assert (
        test_contract.CONTRACT_FINGERPRINT_SHA256
        ==
        contract.SEALED_TEST_CONFIRMATION_CONTRACT_FINGERPRINT_SHA256
    )


def test_05_forward_contract_hash_exact() -> None:

    assert (
        contract.FORWARD_OUTCOME_CONTRACT_FINGERPRINT_SHA256
        ==
        "01fe52a2f068fcc8fb2fc5b89dd7e19dc974fc2d967cfb791e75c3415804ce87"
    )


def test_06_model_artifact_required_before_collection() -> None:

    assert (
        contract.MODEL_ARTIFACT_MUST_BE_FROZEN_BEFORE_COLLECTION
        is True
    )


def test_07_train_only_model_required() -> None:

    assert (
        contract.MODEL_ARTIFACT_TRAIN_ONLY_REQUIRED
        is True
    )

    assert (
        contract.TRAIN_PLUS_VALIDATION_REFIT_ALLOWED
        is False
    )


def test_08_fresh_samples_only() -> None:

    assert (
        contract.FRESH_SAMPLE_ONLY
        is True
    )

    assert (
        contract.DECISION_TIME_MUST_BE_AFTER_SEALED_TEST_PUBLICATION
        is True
    )


def test_09_old_forward30_excluded() -> None:

    assert (
        contract.OLD_FORWARD_30_ELIGIBLE_FOR_ACCEPTANCE
        is False
    )

    assert (
        contract.OLD_FORWARD_30_ELIGIBLE_FOR_TUNING
        is False
    )


def test_10_sealed_test_not_tuning_surface() -> None:

    assert (
        contract.SEALED_TEST_ELIGIBLE_FOR_FURTHER_TUNING
        is False
    )


def test_11_completed_m5_only() -> None:

    assert (
        contract.ONLY_COMPLETED_M5_BARS_ALLOWED
        is True
    )

    assert (
        contract.FORMING_CANDLE_ALLOWED
        is False
    )


def test_12_target_semantics_exact() -> None:

    assert (
        contract.HORIZON_BARS
        ==
        12
    )

    assert (
        contract.HORIZON_MINUTES
        ==
        60
    )

    assert (
        contract.PROFIT_ATR
        ==
        1.25
    )

    assert (
        contract.MAX_ADVERSE_ATR
        ==
        0.75
    )


def test_13_dedicated_r03_ledgers() -> None:

    assert (
        "r03_prospective"
        in
        contract.OBSERVATION_LEDGER_RELATIVE_PATH
    )

    assert (
        "r03_prospective"
        in
        contract.ANCHOR_LEDGER_RELATIVE_PATH
    )

    assert (
        "r03_prospective"
        in
        contract.OUTCOME_LEDGER_RELATIVE_PATH
    )


def test_14_ledgers_append_only() -> None:

    assert (
        contract.LEDGERS_APPEND_ONLY
        is True
    )

    assert (
        contract.LEDGERS_MAY_BE_DELETED
        is False
    )

    assert (
        contract.LEDGERS_MAY_BE_RESET
        is False
    )

    assert (
        contract.LEDGERS_MAY_BE_TRUNCATED
        is False
    )

    assert (
        contract.LEDGERS_MAY_BE_OVERWRITTEN
        is False
    )


def test_15_minimum_matured_outcomes_exact() -> None:

    assert (
        contract.MINIMUM_MATURED_OUTCOMES
        ==
        60
    )


def test_16_minimum_distinct_dates_exact() -> None:

    assert (
        contract.MINIMUM_DISTINCT_OBSERVATION_UTC_DATES
        ==
        5
    )


def test_17_weekly_reports_descriptive_only() -> None:

    assert (
        contract.WEEKLY_REPORTING_ENABLED
        is True
    )

    assert (
        contract.WEEKLY_REPORTS_ARE_DESCRIPTIVE_ONLY
        is True
    )

    assert (
        contract.WEEKLY_REPORTS_MAY_TRIGGER_PASS_FAIL
        is False
    )


def test_18_no_early_decision() -> None:

    assert (
        contract.EARLY_PASS_ALLOWED
        is False
    )

    assert (
        contract.EARLY_FAIL_ALLOWED
        is False
    )


def test_19_macro_threshold_exact() -> None:

    assert (
        contract.PROSPECTIVE_MACRO_F1_MINIMUM
        ==
        contract.SEALED_TEST_MACRO_F1
        *
        0.85
    )


def test_20_balanced_threshold_exact() -> None:

    assert (
        contract.PROSPECTIVE_BALANCED_ACCURACY_MINIMUM
        ==
        contract.SEALED_TEST_BALANCED_ACCURACY
        *
        0.85
    )


def test_21_min_recall_threshold_exact() -> None:

    assert (
        contract.PROSPECTIVE_MINIMUM_PER_CLASS_RECALL_MINIMUM
        ==
        contract.SEALED_TEST_MINIMUM_PER_CLASS_RECALL
        *
        0.70
    )


def test_22_brier_threshold_exact() -> None:

    assert (
        contract.PROSPECTIVE_MULTICLASS_BRIER_MAXIMUM
        ==
        contract.SEALED_TEST_MULTICLASS_BRIER
        +
        0.05
    )


def test_23_logloss_threshold_exact() -> None:

    assert (
        contract.PROSPECTIVE_MULTICLASS_LOG_LOSS_MAXIMUM
        ==
        contract.SEALED_TEST_MULTICLASS_LOG_LOSS
        +
        0.10
    )


def test_24_prediction_share_bounds() -> None:

    assert (
        contract.MINIMUM_PREDICTED_CLASS_SHARE
        ==
        0.05
    )

    assert (
        contract.MAXIMUM_PREDICTED_CLASS_SHARE
        ==
        0.80
    )


def test_25_immature_sample_blocked() -> None:

    result = (
        contract.evaluate_prospective_confirmation(
            passing_metrics(),
            matured_outcomes=59,
            distinct_observation_utc_dates=5,
        )
    )

    assert (
        result[
            "mature"
        ]
        is False
    )

    assert (
        result[
            "status"
        ]
        ==
        contract.NOT_MATURE_STATUS
    )


def test_26_insufficient_dates_blocked() -> None:

    result = (
        contract.evaluate_prospective_confirmation(
            passing_metrics(),
            matured_outcomes=60,
            distinct_observation_utc_dates=4,
        )
    )

    assert (
        result[
            "mature"
        ]
        is False
    )


def test_27_boundary_pass() -> None:

    result = (
        contract.evaluate_prospective_confirmation(
            passing_metrics(),
            matured_outcomes=60,
            distinct_observation_utc_dates=5,
        )
    )

    assert (
        result[
            "mature"
        ]
        is True
    )

    assert (
        result[
            "passed"
        ]
        is True
    )


def test_28_macro_failure_detected() -> None:

    metrics = passing_metrics()

    metrics[
        "macro_f1"
    ] = (
        contract.PROSPECTIVE_MACRO_F1_MINIMUM
        -
        0.000001
    )

    result = (
        contract.evaluate_prospective_confirmation(
            metrics,
            matured_outcomes=60,
            distinct_observation_utc_dates=5,
        )
    )

    assert (
        result[
            "passed"
        ]
        is False
    )

    assert (
        "MACRO_F1_BELOW_MINIMUM"
        in
        result[
            "failures"
        ]
    )


def test_29_class_collapse_detected() -> None:

    metrics = passing_metrics()

    metrics[
        "prediction_counts"
    ] = {
        "SHORT": 0,
        "NO_TRADE": 30,
        "LONG": 30,
    }

    metrics[
        "prediction_shares"
    ] = {
        "SHORT": 0.0,
        "NO_TRADE": 0.50,
        "LONG": 0.50,
    }

    result = (
        contract.evaluate_prospective_confirmation(
            metrics,
            matured_outcomes=60,
            distinct_observation_utc_dates=5,
        )
    )

    assert (
        result[
            "passed"
        ]
        is False
    )

    assert (
        "CLASS_NOT_PREDICTED:SHORT"
        in
        result[
            "failures"
        ]
    )


def test_30_pnl_not_acceptance_criterion() -> None:

    assert (
        contract.PNL_IS_ACCEPTANCE_CRITERION
        is False
    )


def test_31_forward_pass_not_live_authorization() -> None:

    assert (
        contract.PROSPECTIVE_PASS_AUTHORIZES_LIVE
        is False
    )

    assert (
        contract.PROSPECTIVE_PASS_AUTHORIZES_EXECUTION
        is False
    )


def test_32_real_tick_and_broker_validation_required() -> None:

    assert (
        contract.REAL_TICK_VALIDATION_REQUIRED_AFTER_PROSPECTIVE_PASS
        is True
    )

    assert (
        contract.BROKER_EXECUTION_VALIDATION_REQUIRED_AFTER_PROSPECTIVE_PASS
        is True
    )


def test_33_current_gate_no_data_or_training() -> None:

    assert (
        contract.THIS_GATE_LOADS_MARKET_DATA
        is False
    )

    assert (
        contract.THIS_GATE_LOADS_OLD_FORWARD_OUTCOMES
        is False
    )

    assert (
        contract.THIS_GATE_LOADS_TEST_VALUES
        is False
    )

    assert (
        contract.THIS_GATE_TRAINS_MODEL
        is False
    )


def test_34_current_gate_no_ledger_write() -> None:

    assert (
        contract.THIS_GATE_WRITES_PROSPECTIVE_LEDGERS
        is False
    )


def test_35_runner_has_no_market_access() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text
    assert "copy_ticks" not in text
    assert "copy_rates" not in text
    assert "order_send(" not in text


def test_36_runner_has_no_model_fit() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert ".fit(" not in text


def test_37_contract_fingerprint_consistent() -> None:

    assert (
        contract.CONTRACT_FINGERPRINT_SHA256
        ==
        contract.contract_fingerprint_sha256()
    )


def test_38_live_execution_blocked() -> None:

    assert (
        contract.LIVE_AUTHORIZED
        is False
    )

    assert (
        contract.EXECUTION_AUTHORIZED
        is False
    )