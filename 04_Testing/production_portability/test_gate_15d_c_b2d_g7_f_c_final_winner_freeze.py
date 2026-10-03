from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any


REPO_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

RUNNER_PATH = (
    Path(__file__)
    .resolve()
    .parent
    /
    "run_xauusd_gate_15d_c_b2d_g7_f_c_final_winner_freeze.py"
)


spec = importlib.util.spec_from_file_location(
    "g7fc",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g7fc: Any = (
    importlib.util.module_from_spec(
        spec
    )
)

spec.loader.exec_module(
    g7fc
)


contract: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_final_winner_contract"
)

registry: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_candidate_registry"
)

access: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_train_validation_access_contract"
)


def test_01_base_authority_exact() -> None:

    assert (
        g7fc.BASE_AUTHORITY_COMMIT
        ==
        "74ba1f9bc074de6bb8e6081758b9f31efa32b066"
    )


def test_02_winner_id_exact() -> None:

    assert (
        contract.WINNER_CANDIDATE_ID
        ==
        "R03_FLAT_EXTRA_TREES_SMOOTH"
    )


def test_03_winner_fingerprint_exact() -> None:

    assert (
        contract.WINNER_CANDIDATE_FINGERPRINT_SHA256
        ==
        "ae644c7272a015c26daeaaa7e655120bd7a3e4d267b2acd0d1f235e10bfa2e5f"
    )


def test_04_g7fb_evidence_hash_exact() -> None:

    assert (
        contract.G7FB_EVIDENCE_SHA256
        ==
        "34a90921c81fdc1f482330b6cc91e7b34a54339295f4d6e272838057078727b4"
    )


def test_05_registry_fingerprint_exact() -> None:

    assert (
        registry.REGISTRY_FINGERPRINT_SHA256
        ==
        "4556eb982086da0ea19ab910a30b5ab58788c7e5b7488ef8e3453e46289c0deb"
    )


def test_06_access_fingerprint_exact() -> None:

    assert (
        access.CONTRACT_FINGERPRINT_SHA256
        ==
        "bfd0cfee283dcb29cff79feff6a5366772a596c9635e470e06d56e70ead74b3e"
    )


def test_07_winner_exists_once() -> None:

    matches = [
        candidate
        for candidate
        in registry.CANDIDATES
        if candidate[
            "candidate_id"
        ]
        ==
        contract.WINNER_CANDIDATE_ID
    ]

    assert len(
        matches
    ) == 1


def test_08_winner_registry_fingerprint_matches() -> None:

    winner = next(
        candidate
        for candidate
        in registry.CANDIDATES
        if candidate[
            "candidate_id"
        ]
        ==
        contract.WINNER_CANDIDATE_ID
    )

    assert (
        registry.candidate_fingerprint_sha256(
            winner
        )
        ==
        contract.WINNER_CANDIDATE_FINGERPRINT_SHA256
    )


def test_09_winner_estimator_exact() -> None:

    assert (
        contract.WINNER_ESTIMATOR_CONFIG
        ==
        {
            "implementation": (
                "sklearn.ensemble.ExtraTreesClassifier"
            ),
            "bootstrap": False,
            "class_weight": "balanced",
            "max_depth": 8,
            "max_features": 0.50,
            "min_samples_leaf": 50,
            "n_estimators": 750,
            "n_jobs": -1,
            "random_state": 271828,
        }
    )


def test_10_winner_no_scaler() -> None:

    assert (
        contract.WINNER_PREPROCESSING
        ==
        {
            "standard_scaler": False,
        }
    )


def test_11_no_probability_calibration() -> None:

    assert (
        contract.PROBABILITY_CALIBRATION_ENABLED
        is False
    )


def test_12_no_threshold_tuning() -> None:

    assert (
        contract.THRESHOLD_TUNING_ENABLED
        is False
    )


def test_13_validation_macro_f1_exact() -> None:

    assert (
        contract.VALIDATION_MACRO_F1
        ==
        0.3601580118907661
    )


def test_14_validation_balanced_accuracy_exact() -> None:

    assert (
        contract.VALIDATION_BALANCED_ACCURACY
        ==
        0.377760637941734
    )


def test_15_validation_min_recall_exact() -> None:

    assert (
        contract.VALIDATION_MINIMUM_PER_CLASS_RECALL
        ==
        0.32515085024684587
    )


def test_16_validation_brier_exact() -> None:

    assert (
        contract.VALIDATION_MULTICLASS_BRIER
        ==
        0.6648217771177802
    )


def test_17_validation_logloss_exact() -> None:

    assert (
        contract.VALIDATION_MULTICLASS_LOG_LOSS
        ==
        1.0958580283040205
    )


def test_18_prediction_counts_exact() -> None:

    assert (
        contract.VALIDATION_PREDICTION_COUNTS
        ==
        {
            "SHORT": 4452,
            "NO_TRADE": 4283,
            "LONG": 6248,
        }
    )


def test_19_test_values_still_blocked() -> None:

    assert (
        contract.TEST_VALUES_AUTHORIZED_IN_THIS_GATE
        is False
    )

    assert (
        access.TEST_FEATURE_ACCESS_AUTHORIZED
        is False
    )

    assert (
        access.TEST_TARGET_ACCESS_AUTHORIZED
        is False
    )


def test_20_test_evaluation_still_blocked() -> None:

    assert (
        contract.TEST_EVALUATION_AUTHORIZED_IN_THIS_GATE
        is False
    )


def test_21_no_same_test_tuning_after_failure() -> None:

    assert (
        contract.TEST_FAILURE_MAY_TRIGGER_SAME_TEST_TUNING
        is False
    )


def test_22_winner_config_frozen_before_test() -> None:

    assert (
        contract.WINNER_CONFIG_MAY_CHANGE_BEFORE_TEST
        is False
    )

    assert (
        contract.WINNER_FEATURES_MAY_CHANGE_BEFORE_TEST
        is False
    )


def test_23_validation_not_reused_for_selection() -> None:

    assert (
        contract.VALIDATION_MAY_BE_REUSED_FOR_FURTHER_SELECTION
        is False
    )


def test_24_forward30_not_tuning_surface() -> None:

    assert (
        contract.OLD_FORWARD_30_MAY_BE_USED_FOR_TUNING
        is False
    )


def test_25_runner_does_not_load_training_data() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "load_train_supervised("
        not in text
    )

    assert (
        "load_validation_supervised("
        not in text
    )


def test_26_runner_does_not_load_test() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "load_test_features(" not in text
    assert "load_test_targets(" not in text
    assert "load_test_supervised(" not in text


def test_27_runner_does_not_fit_model() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert ".fit(" not in text
    assert "fit_predict_candidate(" not in text


def test_28_runner_does_not_access_mt5() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text
    assert "copy_ticks" not in text
    assert "copy_rates" not in text
    assert "order_send(" not in text


def test_29_runner_protects_ledgers() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "PROTECTED_LEDGER_CHANGED_DURING_G7FC"
        in text
    )


def test_30_contract_fingerprint_self_consistent() -> None:

    assert (
        contract.CONTRACT_FINGERPRINT_SHA256
        ==
        contract.contract_fingerprint_sha256()
    )


def test_31_live_execution_blocked() -> None:

    assert (
        contract.LIVE_AUTHORIZED
        is False
    )

    assert (
        contract.EXECUTION_AUTHORIZED
        is False
    )