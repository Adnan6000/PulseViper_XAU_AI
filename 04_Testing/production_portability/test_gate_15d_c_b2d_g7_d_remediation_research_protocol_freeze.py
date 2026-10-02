from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any


RUNNER_PATH = (
    Path(__file__).resolve().parent
    / "run_xauusd_gate_15d_c_b2d_g7_d_remediation_research_protocol_freeze.py"
)


spec = importlib.util.spec_from_file_location(
    "g7d",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g7d: Any = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    g7d
)


contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_remediation_research_protocol_contract"
)


def test_01_base_authority_is_g7c() -> None:

    assert (
        contract.BASE_AUTHORITY_COMMIT
        ==
        "03dfb354bdb99a8a334aa6408b9edfd4d21bc096"
    )


def test_02_g7c_fingerprint_is_bound() -> None:

    assert (
        contract.G7C_CONTRACT_FINGERPRINT_SHA256
        ==
        "11302c424f05aab2fbd640d644b30d3df0b013d3b9e1b559b29e325ee2f99b50"
    )


def test_03_dataset_identity_is_frozen() -> None:

    assert (
        contract.DATASET_ID
        ==
        "portable_cff75b0686383a3ab6f8352b"
    )

    assert (
        contract.DATASET_SHA256
        ==
        "cff75b0686383a3ab6f8352bfcdcd55308b99b7a4c6edbf7d2e7215f6f33dd07"
    )


def test_04_feature_identity_is_frozen() -> None:

    assert contract.FEATURE_COUNT == 331

    assert (
        contract.FEATURE_COLUMNS_SHA256
        ==
        "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
    )


def test_05_target_contract_unchanged() -> None:

    assert (
        contract.TARGET_CONTRACT
        ==
        "CLEAN_DIRECTIONAL_EXCURSION_V2"
    )

    assert contract.TARGET_CHANGE_ALLOWED is False

    assert (
        contract.FORWARD_FAILURE_RELABELING_ALLOWED
        is False
    )


def test_06_historical_registry_is_bound() -> None:

    assert (
        contract.HISTORICAL_CANDIDATE_REGISTRY_FINGERPRINT_SHA256
        ==
        "b8088bb34ce8940f7de5946fbb9b0fd20f40d7cc93a76b76fd7975591f00066c"
    )

    assert len(
        contract.HISTORICAL_CANDIDATE_IDS
    ) == 6


def test_07_c04_is_control_only() -> None:

    assert (
        contract.HISTORICAL_WINNER_CANDIDATE_ID
        ==
        "C04_FLAT_EXTRA_TREES_CONSTRAINED"
    )

    assert (
        contract.HISTORICAL_WINNER_IS_REMEDIATION_CONTROL_ONLY
        is True
    )


def test_08_old_registry_not_automatically_reused() -> None:

    assert (
        contract.HISTORICAL_REGISTRY_AUTOMATICALLY_REUSED_AS_REMEDIATION_REGISTRY
        is False
    )


def test_09_broad_failure_modes_only() -> None:

    assert (
        contract.FORWARD_DIAGNOSTICS_MAY_DEFINE_BROAD_FAILURE_MODES
        is True
    )

    assert (
        contract.FORWARD_DIAGNOSTICS_MAY_SELECT_SAMPLE_SPECIFIC_RULES
        is False
    )

    assert (
        contract.FORWARD_DIAGNOSTICS_MAY_OPTIMIZE_HOLDOUT_METRICS
        is False
    )


def test_10_train_and_validation_research_allowed() -> None:

    assert (
        contract.TRAIN_MAY_BE_USED_FOR_REMEDIATION_RESEARCH
        is True
    )

    assert (
        contract.VALIDATION_MAY_BE_USED_FOR_REMEDIATION_RESEARCH
        is True
    )


def test_11_test_closed_for_research() -> None:

    assert (
        contract.TEST_MAY_BE_USED_FOR_REMEDIATION_RESEARCH
        is False
    )

    assert (
        contract.TEST_MAY_BE_USED_BEFORE_FINAL_CANDIDATE_FREEZE
        is False
    )


def test_12_test_cannot_select_or_tune() -> None:

    assert contract.TEST_MAY_SELECT_MODEL is False
    assert contract.TEST_MAY_SELECT_FEATURES is False
    assert (
        contract.TEST_MAY_SELECT_HYPERPARAMETERS
        is False
    )
    assert (
        contract.TEST_MAY_SELECT_CALIBRATION
        is False
    )
    assert (
        contract.TEST_MAY_SELECT_THRESHOLDS
        is False
    )


def test_13_forward_30_isolation() -> None:

    assert (
        contract.FORWARD_30_MAY_BE_USED_FOR_TRAINING
        is False
    )

    assert (
        contract.FORWARD_30_MAY_BE_USED_FOR_MODEL_SELECTION
        is False
    )

    assert (
        contract.FORWARD_30_MAY_BE_JOINED_TO_REMEDIATION_DATASET
        is False
    )


def test_14_new_registry_required() -> None:

    assert (
        contract.NEW_REMEDIATION_REGISTRY_REQUIRED
        is True
    )

    assert (
        contract.NEW_REMEDIATION_REGISTRY_GATE
        ==
        "G7-E"
    )


def test_15_registry_is_bounded() -> None:

    assert (
        contract.NEW_REMEDIATION_REGISTRY_MIN_CANDIDATES
        ==
        4
    )

    assert (
        contract.NEW_REMEDIATION_REGISTRY_MAX_CANDIDATES
        ==
        12
    )


def test_16_registry_frozen_before_fit() -> None:

    assert (
        contract.NEW_REMEDIATION_REGISTRY_MUST_BE_FINITE
        is True
    )

    assert (
        contract.NEW_REMEDIATION_REGISTRY_MUST_BE_FROZEN_BEFORE_FIRST_FIT
        is True
    )

    assert (
        contract.NEW_REMEDIATION_REGISTRY_MUST_BE_FINGERPRINTED
        is True
    )


def test_17_c04_control_required_in_future_registry() -> None:

    assert (
        contract.NEW_REMEDIATION_REGISTRY_MUST_INCLUDE_C04_CONTROL
        is True
    )


def test_18_no_unbounded_search() -> None:

    assert (
        contract.UNBOUNDED_GRID_SEARCH_ALLOWED
        is False
    )

    assert (
        contract.BAYESIAN_OPTIMIZATION_ALLOWED
        is False
    )

    assert (
        contract.AUTOML_SEARCH_ALLOWED
        is False
    )

    assert (
        contract.RANDOM_UNBOUNDED_SEARCH_ALLOWED
        is False
    )


def test_19_no_results_driven_candidate_changes() -> None:

    assert (
        contract.RESULTS_DRIVEN_CANDIDATE_ADDITION_AFTER_FIRST_FIT_ALLOWED
        is False
    )

    assert (
        contract.RESULTS_DRIVEN_HYPERPARAMETER_CHANGE_AFTER_FIRST_FIT_ALLOWED
        is False
    )


def test_20_test_is_one_shot() -> None:

    assert contract.TEST_ACCESS_IS_ONE_SHOT is True

    assert (
        contract.FAILED_TEST_MAY_NOT_BE_TUNED_AGAINST_SAME_TEST
        is True
    )


def test_21_prospective_forward_required() -> None:

    assert (
        contract.NEW_PROSPECTIVE_FORWARD_VALIDATION_REQUIRED
        is True
    )

    assert (
        contract.NEW_FORWARD_DATA_MUST_POSTDATE_FINAL_CANDIDATE_FREEZE
        is True
    )


def test_22_weekly_no_fixed_wait() -> None:

    assert (
        contract.FORWARD_EVALUATION_CADENCE
        ==
        "WEEKLY"
    )

    assert (
        contract.FORWARD_MINIMUM_NEW_WEEKLY_SAMPLE_COUNT
        ==
        0
    )

    assert (
        contract.FIXED_COUNT_FORWARD_WAIT_REQUIRED
        is False
    )


def test_23_current_gate_does_not_load_data_values() -> None:

    assert (
        contract.THIS_GATE_LOADS_TRAIN_FEATURE_VALUES
        is False
    )

    assert (
        contract.THIS_GATE_LOADS_VALIDATION_FEATURE_VALUES
        is False
    )

    assert (
        contract.THIS_GATE_LOADS_TEST_FEATURE_VALUES
        is False
    )

    assert (
        contract.THIS_GATE_LOADS_TEST_TARGET_VALUES
        is False
    )


def test_24_current_gate_does_not_train_or_tune() -> None:

    assert contract.THIS_GATE_TRAINS_MODEL is False
    assert contract.THIS_GATE_SELECTS_MODEL is False
    assert contract.THIS_GATE_SELECTS_FEATURES is False
    assert (
        contract.THIS_GATE_TUNES_HYPERPARAMETERS
        is False
    )
    assert (
        contract.THIS_GATE_CALIBRATES_PROBABILITIES
        is False
    )
    assert (
        contract.THIS_GATE_TUNES_THRESHOLDS
        is False
    )


def test_25_no_live_or_execution() -> None:

    assert contract.LIVE_AUTHORIZED is False
    assert contract.EXECUTION_AUTHORIZED is False


def test_26_runner_has_no_mt5_or_execution_calls() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text
    assert "order_send(" not in text
    assert "order_check(" not in text
    assert "positions_get(" not in text


def test_27_runtime_ledgers_are_protected() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "RUNTIME_LEDGER_CHANGED_DURING_G7D_FREEZE"
        in text
    )


def test_28_contract_fingerprint_consistent() -> None:

    assert (
        contract.contract_fingerprint_sha256()
        ==
        contract.CONTRACT_FINGERPRINT_SHA256
    )