from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any


RUNNER_PATH = (
    Path(__file__).resolve().parent
    / "run_xauusd_gate_15d_c_b2d_g7_a_model_remediation_protocol_freeze.py"
)


spec = importlib.util.spec_from_file_location(
    "g7a",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g7a: Any = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    g7a
)


contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_model_remediation_protocol_contract"
)


def test_01_base_authority_is_g6e_publication() -> None:

    assert (
        g7a.BASE_AUTHORITY_COMMIT
        ==
        "ad5ec6d9addc9353b655efdb3089896a35676098"
    )


def test_02_contract_authority_matches() -> None:

    assert (
        contract.BASE_AUTHORITY_COMMIT
        ==
        g7a.BASE_AUTHORITY_COMMIT
    )


def test_03_holdout_count_is_30() -> None:

    assert (
        contract.FORWARD_HOLDOUT_SAMPLE_COUNT
        ==
        30
    )


def test_04_holdout_is_evaluation_only() -> None:

    assert (
        contract.FORWARD_HOLDOUT_ROLE
        ==
        "EVALUATION_ONLY_IMMUTABLE_HOLDOUT"
    )


def test_05_holdout_cannot_train() -> None:

    assert (
        contract.FORWARD_HOLDOUT_CAN_BE_USED_FOR_TRAINING
        is False
    )

    assert (
        contract.FORWARD_HOLDOUT_CAN_BE_USED_FOR_REFITTING
        is False
    )


def test_06_holdout_cannot_calibrate_or_threshold_select() -> None:

    assert (
        contract.FORWARD_HOLDOUT_CAN_BE_USED_FOR_CALIBRATION
        is False
    )

    assert (
        contract.FORWARD_HOLDOUT_CAN_BE_USED_FOR_THRESHOLD_SELECTION
        is False
    )


def test_07_holdout_cannot_select_features_hyperparameters_or_model() -> None:

    assert (
        contract.FORWARD_HOLDOUT_CAN_BE_USED_FOR_FEATURE_SELECTION
        is False
    )

    assert (
        contract.FORWARD_HOLDOUT_CAN_BE_USED_FOR_HYPERPARAMETER_SELECTION
        is False
    )

    assert (
        contract.FORWARD_HOLDOUT_CAN_BE_USED_FOR_MODEL_SELECTION
        is False
    )


def test_08_holdout_is_immutable() -> None:

    assert (
        contract.FORWARD_HOLDOUT_CAN_BE_REMOVED_POST_HOC
        is False
    )

    assert (
        contract.FORWARD_HOLDOUT_CAN_BE_RELABELLED_POST_HOC
        is False
    )

    assert (
        contract.FORWARD_HOLDOUT_CAN_BE_REWRITTEN
        is False
    )


def test_09_diagnostics_can_trigger_but_not_tune() -> None:

    assert (
        contract.DIAGNOSTIC_EVIDENCE_MAY_TRIGGER_REMEDIATION
        is True
    )

    assert (
        contract.DIAGNOSTIC_EVIDENCE_MAY_DEFINE_BROAD_FAILURE_MODES
        is True
    )

    assert (
        contract.DIAGNOSTIC_EVIDENCE_MAY_BE_USED_FOR_SAMPLE_SPECIFIC_TUNING
        is False
    )

    assert (
        contract.DIAGNOSTIC_EVIDENCE_MAY_BE_USED_TO_OPTIMIZE_HOLDOUT_METRICS
        is False
    )


def test_10_research_may_reopen_after_protocol_freeze() -> None:

    assert (
        contract.REMEDIATION_RESEARCH_MAY_REOPEN
        is True
    )

    assert (
        contract.CANDIDATE_RETRAINING_MAY_OCCUR_AFTER_THIS_FREEZE
        is True
    )

    assert (
        contract.CANDIDATE_MODEL_RESELECTION_MAY_OCCUR_AFTER_THIS_FREEZE
        is True
    )


def test_11_candidate_development_is_offline() -> None:

    assert (
        contract.CANDIDATE_DEVELOPMENT_MUST_BE_OFFLINE
        is True
    )


def test_12_candidate_requires_explicit_data_authority() -> None:

    assert (
        contract.CANDIDATE_MUST_HAVE_EXPLICIT_TRAINING_DATA_AUTHORITY
        is True
    )

    assert (
        contract.CANDIDATE_MUST_HAVE_EXPLICIT_VALIDATION_DATA_AUTHORITY
        is True
    )

    assert (
        contract.CANDIDATE_MUST_HAVE_EXPLICIT_TEST_DATA_AUTHORITY
        is True
    )


def test_13_candidate_must_freeze_before_forward() -> None:

    assert (
        contract.CANDIDATE_MUST_PASS_OFFLINE_VALIDATION_BEFORE_FORWARD
        is True
    )

    assert (
        contract.CANDIDATE_MUST_BE_FROZEN_BEFORE_FORWARD
        is True
    )

    assert (
        contract.CANDIDATE_PARAMETERS_MUST_NOT_CHANGE_DURING_FORWARD
        is True
    )


def test_14_future_forward_must_be_prospective() -> None:

    assert (
        contract.PROSPECTIVE_VALIDATION_REQUIRED
        is True
    )

    assert (
        contract.PROSPECTIVE_DATA_MUST_OCCUR_AFTER_CANDIDATE_FREEZE
        is True
    )

    assert (
        contract.NEW_PROSPECTIVE_COHORT_MUST_BE_DISTINCT_FROM_OLD_30
        is True
    )


def test_15_weekly_cadence_has_no_fixed_sample_wait() -> None:

    assert (
        contract.PROSPECTIVE_EVALUATION_CADENCE
        ==
        "WEEKLY"
    )

    assert (
        contract.PROSPECTIVE_MINIMUM_NEW_WEEKLY_SAMPLE_COUNT
        ==
        0
    )

    assert (
        contract.PROSPECTIVE_FIXED_COUNT_WAIT_REQUIRED
        is False
    )

    assert (
        contract.PROSPECTIVE_MULTI_DAY_FIXED_SAMPLE_COLLECTION_REQUIRED
        is False
    )


def test_16_target_and_outcome_contract_stay_frozen() -> None:

    assert (
        contract.OUTCOME_CONTRACT_MODIFICATION_ALLOWED
        is False
    )

    assert (
        contract.TARGET_SEMANTICS_MODIFICATION_ALLOWED
        is False
    )


def test_17_current_gate_does_not_train_or_tune() -> None:

    assert (
        contract.THIS_GATE_PERFORMS_RETRAINING
        is False
    )

    assert (
        contract.THIS_GATE_PERFORMS_REFITTING
        is False
    )

    assert (
        contract.THIS_GATE_PERFORMS_CALIBRATION
        is False
    )

    assert (
        contract.THIS_GATE_PERFORMS_MODEL_RESELECTION
        is False
    )

    assert (
        contract.THIS_GATE_PERFORMS_FEATURE_RESELECTION
        is False
    )

    assert (
        contract.THIS_GATE_PERFORMS_HYPERPARAMETER_TUNING
        is False
    )

    assert (
        contract.THIS_GATE_PERFORMS_THRESHOLD_TUNING
        is False
    )


def test_18_no_promotion_pnl_live_execution() -> None:

    assert (
        contract.PROMOTION_CRITERIA_DEFINED
        is False
    )

    assert (
        contract.PRODUCTION_PROMOTION_AUTHORIZED
        is False
    )

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


def test_19_runner_has_no_mt5_or_execution_api() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text
    assert "order_send(" not in text
    assert "order_check(" not in text
    assert "positions_get(" not in text
    assert "orders_get(" not in text


def test_20_runner_protects_runtime_ledgers() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "RUNTIME_LEDGER_CHANGED_DURING_G7A_FREEZE"
        in text
    )

    assert (
        '"ledger_write_performed": False'
        in text
    )


def test_21_contract_fingerprint_is_self_consistent() -> None:

    assert (
        contract.contract_fingerprint_sha256()
        ==
        contract.CONTRACT_FINGERPRINT_SHA256
    )


def test_22_known_holdout_hashes_are_frozen() -> None:

    assert (
        contract.FORWARD_HOLDOUT_OBSERVATION_LEDGER_SHA256
        ==
        "3a3421d3f29cd31cf0b9a2cfec1619cc7df9a3d95df6b30645b3600e3e09c3d3"
    )

    assert (
        contract.FORWARD_HOLDOUT_ANCHOR_LEDGER_SHA256
        ==
        "1828ba8f1b6a1cfabe20c0ba402bb26f3db1d6e2aabc454055566b2a7ef08bcc"
    )

    assert (
        contract.FORWARD_HOLDOUT_OUTCOME_LEDGER_SHA256
        ==
        "24fe13c091ac91a134b55d1bcda83b8f9b05e7c13b5c276bfb8649ac4dce84f7"
    )