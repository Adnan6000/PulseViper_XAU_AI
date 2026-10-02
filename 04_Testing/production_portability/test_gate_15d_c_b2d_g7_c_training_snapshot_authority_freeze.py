from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any


RUNNER_PATH = (
    Path(__file__).resolve().parent
    / "run_xauusd_gate_15d_c_b2d_g7_c_training_snapshot_authority_freeze.py"
)


spec = importlib.util.spec_from_file_location(
    "g7c",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g7c: Any = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(g7c)


contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_remediation_training_snapshot_authority"
)


def test_01_base_authority_is_g7b() -> None:

    assert (
        g7c.BASE_AUTHORITY_COMMIT
        ==
        "5ab1fdbe822e0e1f723f2a6a5f75da3544233f09"
    )


def test_02_g7b_fingerprint_is_frozen() -> None:

    assert (
        contract.G7B_CONTRACT_FINGERPRINT_SHA256
        ==
        "5e1d643c9a65d5709593bf7e3163895cc087ffb18eb0330ae0e80886d4fae0f3"
    )


def test_03_dataset_identity() -> None:

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


def test_04_manifest_identity() -> None:

    assert (
        contract.MANIFEST_SHA256
        ==
        "1b8e3599b227c9cbbc6b12f8ab0e275ca4deb4a65839fb626ca90720d59512dc"
    )


def test_05_feature_identity() -> None:

    assert (
        contract.FEATURE_COUNT
        ==
        331
    )

    assert (
        contract.FEATURE_COLUMNS_SHA256
        ==
        "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
    )


def test_06_total_rows() -> None:

    assert (
        contract.TOTAL_ROWS
        ==
        99945
    )


def test_07_train_rows() -> None:

    assert (
        contract.TRAIN_ROWS
        ==
        69966
    )


def test_08_validation_rows() -> None:

    assert (
        contract.VALIDATION_ROWS
        ==
        14983
    )


def test_09_test_rows() -> None:

    assert (
        contract.TEST_ROWS
        ==
        14996
    )


def test_10_split_sum() -> None:

    assert (
        contract.TRAIN_ROWS
        +
        contract.VALIDATION_ROWS
        +
        contract.TEST_ROWS
        ==
        contract.TOTAL_ROWS
    )


def test_11_portable_contract() -> None:

    assert (
        contract.TRAINING_CONTRACT_VERSION
        ==
        "XAUUSD_MTF_PORTABLE_FEATURE_V1"
    )


def test_12_source_v3_is_bound() -> None:

    assert (
        contract.SOURCE_TRAINING_CONTRACT_VERSION
        ==
        "XAUUSD_MTF_TRAINING_V3"
    )


def test_13_target_contract_stays_frozen() -> None:

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


def test_14_train_can_fit() -> None:

    assert (
        contract.TRAIN_MAY_BE_USED_FOR_FITTING
        is True
    )


def test_15_validation_can_research_select() -> None:

    assert (
        contract.VALIDATION_MAY_BE_USED_FOR_RESEARCH_SELECTION
        is True
    )


def test_16_test_stays_closed_before_candidate_freeze() -> None:

    assert (
        contract.TEST_MAY_BE_USED_BEFORE_CANDIDATE_FREEZE
        is False
    )


def test_17_test_cannot_select() -> None:

    assert (
        contract.TEST_MAY_SELECT_MODEL
        is False
    )

    assert (
        contract.TEST_MAY_SELECT_FEATURES
        is False
    )

    assert (
        contract.TEST_MAY_SELECT_HYPERPARAMETERS
        is False
    )


def test_18_forward_data_excluded() -> None:

    assert (
        contract.FORWARD_30_MAY_BE_JOINED_TO_DATASET
        is False
    )

    assert (
        contract.FORWARD_30_MAY_BE_USED_FOR_TRAINING
        is False
    )

    assert (
        contract.FORWARD_30_MAY_BE_USED_FOR_SELECTION
        is False
    )


def test_19_current_gate_only_reads_metadata_columns() -> None:

    assert (
        contract.THIS_GATE_READS_ONLY_SPLIT_AND_DECISION_TIME_COLUMNS
        is True
    )

    assert (
        contract.THIS_GATE_READS_MODEL_FEATURE_VALUES
        is False
    )

    assert (
        contract.THIS_GATE_READS_TARGET_VALUES
        is False
    )


def test_20_current_gate_does_not_train() -> None:

    assert (
        contract.THIS_GATE_TRAINS_MODEL
        is False
    )

    assert (
        contract.THIS_GATE_FITS_PREPROCESSOR
        is False
    )


def test_21_current_gate_does_not_tune() -> None:

    assert (
        contract.THIS_GATE_TUNES_HYPERPARAMETERS
        is False
    )

    assert (
        contract.THIS_GATE_TUNES_THRESHOLDS
        is False
    )

    assert (
        contract.THIS_GATE_CALIBRATES_PROBABILITIES
        is False
    )


def test_22_current_gate_does_not_evaluate_holdouts() -> None:

    assert (
        contract.THIS_GATE_EVALUATES_VALIDATION
        is False
    )

    assert (
        contract.THIS_GATE_EVALUATES_TEST
        is False
    )


def test_23_no_live_or_execution() -> None:

    assert (
        contract.LIVE_AUTHORIZED
        is False
    )

    assert (
        contract.EXECUTION_AUTHORIZED
        is False
    )


def test_24_runner_has_no_mt5() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text
    assert "order_send(" not in text
    assert "order_check(" not in text


def test_25_runtime_ledgers_are_protected() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "RUNTIME_LEDGER_CHANGED_DURING_G7C_FREEZE"
        in text
    )


def test_26_only_two_dataset_columns_are_loaded() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        '"decision_time"'
        in text
    )

    assert (
        '"dataset_split"'
        in text
    )


def test_27_contract_fingerprint_self_consistent() -> None:

    assert (
        contract.contract_fingerprint_sha256()
        ==
        contract.CONTRACT_FINGERPRINT_SHA256
    )