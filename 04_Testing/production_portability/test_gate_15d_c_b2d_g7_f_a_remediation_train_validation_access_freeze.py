from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any


RUNNER_PATH = (
    Path(__file__).resolve().parent
    / "run_xauusd_gate_15d_c_b2d_g7_f_a_remediation_train_validation_access_freeze.py"
)

LOADER_PATH = (
    Path(__file__).resolve().parents[2]
    / "02_AI/Dataset/"
    "portable_331_remediation_train_validation_loader.py"
)


spec = importlib.util.spec_from_file_location(
    "g7fa",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g7fa: Any = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    g7fa
)


contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_remediation_train_validation_access_contract"
)

loader_module: Any = importlib.import_module(
    "02_AI.Dataset.portable_331_remediation_train_validation_loader"
)


def test_01_base_authority() -> None:

    assert (
        contract.BASE_AUTHORITY_COMMIT
        ==
        "b650eff40e191b154c3055caadd9159e0eb0812a"
    )


def test_02_g7e_registry_bound() -> None:

    assert (
        contract.G7E_REGISTRY_FINGERPRINT_SHA256
        ==
        "4556eb982086da0ea19ab910a30b5ab58788c7e5b7488ef8e3453e46289c0deb"
    )


def test_03_dataset_identity() -> None:

    assert (
        contract.DATASET_ID
        ==
        "portable_cff75b0686383a3ab6f8352b"
    )


def test_04_feature_count() -> None:

    assert contract.FEATURE_COUNT == 331


def test_05_split_counts() -> None:

    assert contract.TRAIN_ROWS == 69966
    assert contract.VALIDATION_ROWS == 14983
    assert contract.TEST_ROWS == 14996


def test_06_train_access_authorized() -> None:

    assert (
        contract.TRAIN_FEATURE_ACCESS_AUTHORIZED
        is True
    )

    assert (
        contract.TRAIN_TARGET_ACCESS_AUTHORIZED
        is True
    )


def test_07_validation_access_authorized() -> None:

    assert (
        contract.VALIDATION_FEATURE_ACCESS_AUTHORIZED
        is True
    )

    assert (
        contract.VALIDATION_TARGET_ACCESS_AUTHORIZED
        is True
    )


def test_08_test_access_blocked() -> None:

    assert (
        contract.TEST_FEATURE_ACCESS_AUTHORIZED
        is False
    )

    assert (
        contract.TEST_TARGET_ACCESS_AUTHORIZED
        is False
    )


def test_09_old_validation_ledger_not_rewritten() -> None:

    assert (
        contract.HISTORICAL_VALIDATION_LEDGER_MAY_BE_REWRITTEN
        is False
    )

    assert (
        contract.HISTORICAL_VALIDATION_LEDGER_MAY_BE_RESET
        is False
    )


def test_10_old_validation_ledger_not_remediation_authority() -> None:

    assert (
        contract.HISTORICAL_VALIDATION_LEDGER_GOVERNS_REMEDIATION_ACCESS
        is False
    )


def test_11_loader_uses_composition() -> None:

    text = LOADER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        'importlib.import_module('
        in text
    )

    assert (
        '"02_AI.Dataset.portable_331_training_input_loader"'
        in text
    )

    assert (
        "self._base"
        in text
    )


def test_12_loader_version() -> None:

    cls = (
        loader_module
        .Portable331RemediationTrainValidationLoader
    )

    assert cls.VERSION == "1.0"


def test_13_validation_start_equals_train_rows() -> None:

    cls = (
        loader_module
        .Portable331RemediationTrainValidationLoader
    )

    assert (
        cls.VALIDATION_START_ROW
        ==
        69966
    )


def test_14_test_start_boundary() -> None:

    cls = (
        loader_module
        .Portable331RemediationTrainValidationLoader
    )

    assert (
        cls.TEST_START_ROW
        ==
        69966 + 14983
    )


def test_15_validation_batch_dataclass_exists() -> None:

    assert hasattr(
        loader_module,
        "Portable331RemediationValidationBatch",
    )


def test_16_validation_loader_method_exists() -> None:

    cls = (
        loader_module
        .Portable331RemediationTrainValidationLoader
    )

    assert hasattr(
        cls,
        "load_validation_supervised",
    )


def test_17_test_feature_method_exists() -> None:

    cls = (
        loader_module
        .Portable331RemediationTrainValidationLoader
    )

    assert hasattr(
        cls,
        "load_test_features",
    )


def test_18_test_target_method_exists() -> None:

    cls = (
        loader_module
        .Portable331RemediationTrainValidationLoader
    )

    assert hasattr(
        cls,
        "load_test_targets",
    )


def test_19_test_supervised_method_exists() -> None:

    cls = (
        loader_module
        .Portable331RemediationTrainValidationLoader
    )

    assert hasattr(
        cls,
        "load_test_supervised",
    )


def test_20_current_gate_no_values_loaded() -> None:

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


def test_21_current_gate_no_training() -> None:

    assert (
        contract.THIS_GATE_TRAINS_MODELS
        is False
    )

    assert (
        contract.THIS_GATE_FITS_PREPROCESSORS
        is False
    )


def test_22_current_gate_no_evaluation() -> None:

    assert (
        contract.THIS_GATE_EVALUATES_CANDIDATES
        is False
    )

    assert (
        contract.THIS_GATE_SELECTS_WINNER
        is False
    )


def test_23_no_test_evaluation() -> None:

    assert (
        contract.THIS_GATE_EVALUATES_TEST
        is False
    )


def test_24_no_pnl() -> None:

    assert (
        contract.THIS_GATE_EVALUATES_PNL
        is False
    )


def test_25_no_live() -> None:

    assert contract.LIVE_AUTHORIZED is False


def test_26_no_execution() -> None:

    assert (
        contract.EXECUTION_AUTHORIZED
        is False
    )


def test_27_contract_fingerprint_consistent() -> None:

    assert (
        contract.contract_fingerprint_sha256()
        ==
        contract.CONTRACT_FINGERPRINT_SHA256
    )


def test_28_runner_protects_ledgers() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "PROTECTED_LEDGER_CHANGED_DURING_G7FA"
        in text
    )


def test_29_runner_no_mt5() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text
    assert "order_send(" not in text
    assert "order_check(" not in text


def test_30_loader_has_no_model_fit() -> None:

    text = LOADER_PATH.read_text(
        encoding="utf-8"
    )

    assert ".fit(" not in text


def test_31_loader_hard_blocks_test() -> None:

    text = LOADER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "TEST_FEATURE_ACCESS_NOT_AUTHORIZED_FOR_REMEDIATION"
        in text
    )

    assert (
        "TEST_TARGET_ACCESS_NOT_AUTHORIZED_FOR_REMEDIATION"
        in text
    )