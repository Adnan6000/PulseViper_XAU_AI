from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any


RUNNER_PATH = (
    Path(__file__).resolve().parent
    / "run_xauusd_gate_15d_c_b2d_g7_b_remediation_data_authority_freeze.py"
)


spec = importlib.util.spec_from_file_location(
    "g7b",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g7b: Any = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    g7b
)


contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_remediation_data_authority_contract"
)


def test_01_base_authority_is_g7a_publication() -> None:

    assert (
        g7b.BASE_AUTHORITY_COMMIT
        ==
        "144d4359eae9835563f1bf8d01a4dee35ef8c4c2"
    )


def test_02_g7a_fingerprint_is_frozen() -> None:

    assert (
        contract.G7A_CONTRACT_FINGERPRINT_SHA256
        ==
        "3af5ccd2d84950dd37c3dda5f9d5872af5a303e9b8fdf5515c52dc5b92ad6f6c"
    )


def test_03_research_cutoff_is_frozen() -> None:

    assert (
        contract.RESEARCH_DATA_CUTOFF_UTC
        ==
        "2026-08-14T20:55:00Z"
    )


def test_04_forward_data_is_excluded() -> None:

    assert (
        contract.CURRENT_FORWARD_30_ALLOWED
        is False
    )

    assert (
        contract.FUTURE_PROSPECTIVE_FORWARD_ROWS_ALLOWED
        is False
    )

    assert (
        contract.RUNTIME_SHADOW_LEDGERS_ALLOWED_AS_DEVELOPMENT_DATA
        is False
    )


def test_05_dataset_identity_is_required() -> None:

    assert (
        contract.DATASET_MUST_BE_CONTENT_ADDRESSED
        is True
    )

    assert (
        contract.DATASET_MANIFEST_HASH_REQUIRED
        is True
    )

    assert (
        contract.DATASET_FILE_HASH_REQUIRED
        is True
    )


def test_06_split_is_chronological_and_purged() -> None:

    assert (
        contract.SPLIT_POLICY
        ==
        "PURGED_CHRONOLOGICAL_TRAIN_VALIDATION_TEST"
    )

    assert (
        contract.SPLIT_PURGE_REQUIRED
        is True
    )

    assert (
        contract.RANDOM_SHUFFLE_SPLIT_ALLOWED
        is False
    )


def test_07_split_fractions() -> None:

    assert (
        contract.TRAIN_FRACTION
        ==
        0.70
    )

    assert (
        contract.VALIDATION_FRACTION
        ==
        0.15
    )

    assert (
        contract.TEST_FRACTION
        ==
        0.15
    )


def test_08_model_and_preprocessor_fit_train_only() -> None:

    assert (
        contract.MODEL_FIT_ALLOWED_SPLITS
        ==
        ("TRAIN",)
    )

    assert (
        contract.PREPROCESSOR_FIT_ALLOWED_SPLITS
        ==
        ("TRAIN",)
    )


def test_09_validation_can_drive_research() -> None:

    assert (
        contract.MODEL_SELECTION_ALLOWED_SPLITS
        ==
        (
            "TRAIN",
            "VALIDATION",
        )
    )

    assert (
        contract.HYPERPARAMETER_SELECTION_ALLOWED_SPLITS
        ==
        (
            "TRAIN",
            "VALIDATION",
        )
    )


def test_10_test_cannot_select_model() -> None:

    assert (
        contract.TEST_MAY_SELECT_MODEL
        is False
    )

    assert (
        contract.CANDIDATE_COMPARISON_MAY_USE_TEST_METRICS
        is False
    )


def test_11_test_cannot_tune_features_or_hyperparameters() -> None:

    assert (
        contract.TEST_MAY_SELECT_FEATURES
        is False
    )

    assert (
        contract.TEST_MAY_SELECT_HYPERPARAMETERS
        is False
    )


def test_12_test_cannot_tune_calibration_or_thresholds() -> None:

    assert (
        contract.TEST_MAY_SELECT_CALIBRATION
        is False
    )

    assert (
        contract.TEST_MAY_SELECT_THRESHOLDS
        is False
    )


def test_13_test_is_one_shot_confirmation() -> None:

    assert (
        contract.SELECTED_CANDIDATE_MUST_BE_FROZEN_BEFORE_TEST
        is True
    )

    assert (
        contract.SELECTED_CANDIDATE_MUST_PASS_ONE_SHOT_TEST
        is True
    )

    assert (
        contract.TEST_MAY_TRIGGER_ITERATIVE_TUNING
        is False
    )


def test_14_target_contract_remains_frozen() -> None:

    assert (
        contract.TARGET_CONTRACT
        ==
        "CLEAN_DIRECTIONAL_EXCURSION_V2"
    )

    assert (
        contract.TARGET_PROFIT_ATR
        ==
        1.25
    )

    assert (
        contract.TARGET_MAX_ADVERSE_ATR
        ==
        0.75
    )


def test_15_no_causal_leakage() -> None:

    assert (
        contract.FORMING_CANDLE_ALLOWED
        is False
    )

    assert (
        contract.FUTURE_FEATURE_DATA_ALLOWED
        is False
    )

    assert (
        contract.POST_DECISION_INFORMATION_ALLOWED
        is False
    )

    assert (
        contract.LEAKAGE_ACROSS_SPLITS_ALLOWED
        is False
    )


def test_16_forward_30_cannot_select_candidate() -> None:

    assert (
        contract.FORWARD_30_MAY_SELECT_CANDIDATE
        is False
    )

    assert (
        contract.FORWARD_DIAGNOSTICS_MAY_SELECT_CANDIDATE
        is False
    )


def test_17_candidate_hashes_required() -> None:

    assert (
        contract.SELECTED_CANDIDATE_ARTIFACT_HASH_REQUIRED
        is True
    )

    assert (
        contract.SELECTED_CANDIDATE_FEATURE_HASH_REQUIRED
        is True
    )

    assert (
        contract.SELECTED_CANDIDATE_CONFIGURATION_HASH_REQUIRED
        is True
    )

    assert (
        contract.SELECTED_CANDIDATE_DATA_AUTHORITY_HASH_REQUIRED
        is True
    )


def test_18_failed_test_cannot_be_optimized_against() -> None:

    assert (
        contract.FAILED_TEST_MAY_NOT_BE_TUNED_AGAINST_SAME_TEST
        is True
    )

    assert (
        contract.TEST_REUSE_AFTER_INSPECTION_FOR_OPTIMIZATION_ALLOWED
        is False
    )


def test_19_future_forward_is_prospective_weekly() -> None:

    assert (
        contract.PROSPECTIVE_FORWARD_REQUIRED_AFTER_OFFLINE_FREEZE
        is True
    )

    assert (
        contract.NEW_FORWARD_DATA_MUST_POSTDATE_CANDIDATE_FREEZE
        is True
    )

    assert (
        contract.WEEKLY_FORWARD_EVALUATION
        is True
    )


def test_20_no_fixed_forward_sample_wait() -> None:

    assert (
        contract.MINIMUM_NEW_WEEKLY_SAMPLE_COUNT
        ==
        0
    )

    assert (
        contract.FIXED_COUNT_FORWARD_WAIT_REQUIRED
        is False
    )


def test_21_current_gate_does_not_train() -> None:

    assert (
        contract.THIS_GATE_DISCOVERS_DATASET
        is False
    )

    assert (
        contract.THIS_GATE_LOADS_TRAINING_ROWS
        is False
    )

    assert (
        contract.THIS_GATE_TRAINS_MODEL
        is False
    )

    assert (
        contract.THIS_GATE_FITS_PREPROCESSOR
        is False
    )


def test_22_current_gate_does_not_select_or_tune() -> None:

    assert (
        contract.THIS_GATE_SELECTS_FEATURES
        is False
    )

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

    assert (
        contract.THIS_GATE_SELECTS_MODEL
        is False
    )


def test_23_current_gate_does_not_touch_test_pnl_live() -> None:

    assert (
        contract.THIS_GATE_EVALUATES_TEST
        is False
    )

    assert (
        contract.THIS_GATE_EVALUATES_PNL
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


def test_24_runner_has_no_mt5_execution_api() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text
    assert "order_send(" not in text
    assert "order_check(" not in text
    assert "positions_get(" not in text


def test_25_runner_protects_ledgers() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "RUNTIME_LEDGER_CHANGED_DURING_G7B_FREEZE"
        in text
    )

    assert (
        '"ledger_write_performed": False'
        in text
    )


def test_26_contract_fingerprint_self_consistent() -> None:

    assert (
        contract.contract_fingerprint_sha256()
        ==
        contract.CONTRACT_FINGERPRINT_SHA256
    )