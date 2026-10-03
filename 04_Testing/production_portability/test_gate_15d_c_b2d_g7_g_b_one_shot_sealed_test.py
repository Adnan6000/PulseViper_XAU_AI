from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any

import numpy as np


RUNNER_PATH = (
    Path(__file__)
    .resolve()
    .parent
    /
    "run_xauusd_gate_15d_c_b2d_g7_g_b_one_shot_sealed_test.py"
)


spec = importlib.util.spec_from_file_location(
    "g7gb",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g7gb: Any = (
    importlib.util.module_from_spec(
        spec
    )
)

spec.loader.exec_module(
    g7gb
)


contract: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_test_confirmation_contract"
)

winner_contract: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_final_winner_contract"
)

registry: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_candidate_registry"
)

evaluator: Any = importlib.import_module(
    "02_AI.Models."
    "remediation_candidate_evaluator"
)

loader_module: Any = importlib.import_module(
    "02_AI.Dataset."
    "portable_331_remediation_sealed_test_loader"
)


def winner_candidate() -> dict[str, Any]:

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

    return dict(
        matches[0]
    )


def synthetic_training_data() -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:

    rng = np.random.default_rng(
        271828
    )

    rows_per_class = 60
    feature_count = 8

    short = rng.normal(
        loc=-1.0,
        scale=0.7,
        size=(
            rows_per_class,
            feature_count,
        ),
    )

    no_trade = rng.normal(
        loc=0.0,
        scale=0.7,
        size=(
            rows_per_class,
            feature_count,
        ),
    )

    long = rng.normal(
        loc=1.0,
        scale=0.7,
        size=(
            rows_per_class,
            feature_count,
        ),
    )

    X_train = np.vstack(
        (
            short,
            no_trade,
            long,
        )
    )

    y_train = np.asarray(
        (
            [-1]
            *
            rows_per_class
            +
            [0]
            *
            rows_per_class
            +
            [1]
            *
            rows_per_class
        ),
        dtype=np.int8,
    )

    y_tradeable = (
        y_train
        !=
        0
    ).astype(
        np.int8
    )

    X_eval = rng.normal(
        loc=0.0,
        scale=1.0,
        size=(
            30,
            feature_count,
        ),
    )

    return (
        X_train,
        y_train,
        y_tradeable,
        X_eval,
    )


def test_01_base_authority_exact() -> None:

    assert (
        g7gb.BASE_AUTHORITY_COMMIT
        ==
        "fcc2f282e9c617708ca75b599e337dbeb879283e"
    )


def test_02_test_contract_fingerprint_exact() -> None:

    assert (
        contract.CONTRACT_FINGERPRINT_SHA256
        ==
        "bc1633761ad6dc68923351735abd6ec940ac84871a38c2620ef668666cffe305"
    )


def test_03_winner_contract_fingerprint_exact() -> None:

    assert (
        winner_contract.CONTRACT_FINGERPRINT_SHA256
        ==
        "1c0a7e91b318973f319de4a01b9f850e80f236c9211b4866f52cbb330a973f91"
    )


def test_04_registry_fingerprint_exact() -> None:

    assert (
        registry.REGISTRY_FINGERPRINT_SHA256
        ==
        "4556eb982086da0ea19ab910a30b5ab58788c7e5b7488ef8e3453e46289c0deb"
    )


def test_05_winner_id_exact() -> None:

    assert (
        contract.WINNER_CANDIDATE_ID
        ==
        "R03_FLAT_EXTRA_TREES_SMOOTH"
    )


def test_06_winner_candidate_fingerprint_exact() -> None:

    candidate = (
        winner_candidate()
    )

    assert (
        registry.candidate_fingerprint_sha256(
            candidate
        )
        ==
        "ae644c7272a015c26daeaaa7e655120bd7a3e4d267b2acd0d1f235e10bfa2e5f"
    )


def test_07_test_rows_exact() -> None:

    loader_cls = (
        loader_module
        .Portable331RemediationSealedTestLoader
    )

    assert (
        loader_cls.EXPECTED_TEST_ROWS
        ==
        14996
    )


def test_08_test_start_after_train_validation() -> None:

    loader_cls = (
        loader_module
        .Portable331RemediationSealedTestLoader
    )

    assert (
        loader_cls.TEST_START_ROW
        ==
        69966
        +
        14983
    )


def test_09_validation_access_blocked_in_loader() -> None:

    text = Path(
        loader_module.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "VALIDATION_ACCESS_FORBIDDEN_DURING_SEALED_TEST"
        in text
    )


def test_10_test_read_is_bounded() -> None:

    text = Path(
        loader_module.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "nrows=self.EXPECTED_TEST_ROWS"
        in text
    )

    assert (
        "skiprows=skiprows"
        in text
    )


def test_11_test_window_requires_test_split() -> None:

    text = Path(
        loader_module.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "NON_TEST_ROW_ENTERED_SEALED_TEST_WINDOW"
        in text
    )


def test_12_loader_has_no_model_fit() -> None:

    text = Path(
        loader_module.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert ".fit(" not in text


def test_13_loader_has_no_metrics() -> None:

    text = Path(
        loader_module.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "accuracy_score" not in text
    assert "log_loss(" not in text


def test_14_one_shot_policy_exact() -> None:

    assert (
        contract.TEST_ACCESS_COUNT_MAXIMUM
        ==
        1
    )


def test_15_runner_has_create_only_marker() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        'path.open(\n            "x",'
        in text
    )


def test_16_marker_before_test_read() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    marker_position = text.index(
        "create_access_marker("
    )

    test_read_position = text.index(
        "loader.load_test_supervised()"
    )

    assert (
        marker_position
        <
        test_read_position
    )


def test_17_runner_blocks_existing_marker() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "SEALED_TEST_ALREADY_CONSUMED"
        in text
    )


def test_18_runner_never_loads_validation() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "load_validation_supervised("
        not in text
    )

    assert (
        "load_validation_features("
        not in text
    )

    assert (
        "load_validation_targets("
        not in text
    )


def test_19_train_only_refit_policy() -> None:

    assert (
        contract.TRAIN_ONLY_MODEL_FIT_REQUIRED
        is True
    )

    assert (
        contract.TRAIN_PLUS_VALIDATION_REFIT_ALLOWED
        is False
    )


def test_20_runner_no_train_validation_concat() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "np.concatenate" not in text
    assert "np.vstack" not in text


def test_21_synthetic_winner_fit_predict() -> None:

    (
        X_train,
        y_train,
        y_tradeable,
        X_eval,
    ) = synthetic_training_data()

    probabilities = (
        evaluator.fit_predict_candidate(
            winner_candidate(),
            X_train,
            y_train,
            y_tradeable,
            X_eval,
        )
    )

    assert (
        probabilities.shape
        ==
        (
            30,
            3,
        )
    )

    assert bool(
        np.isfinite(
            probabilities
        ).all()
    )

    assert bool(
        np.allclose(
            probabilities.sum(
                axis=1
            ),
            1.0,
        )
    )


def test_22_synthetic_metrics_work() -> None:

    (
        X_train,
        y_train,
        y_tradeable,
        X_eval,
    ) = synthetic_training_data()

    probabilities = (
        evaluator.fit_predict_candidate(
            winner_candidate(),
            X_train,
            y_train,
            y_tradeable,
            X_eval,
        )
    )

    y_eval = np.asarray(
        (
            [-1]
            *
            10
            +
            [0]
            *
            10
            +
            [1]
            *
            10
        ),
        dtype=np.int8,
    )

    metrics = (
        evaluator.compute_validation_metrics(
            y_eval,
            probabilities,
        )
    )

    for key in (
        "exact_class_accuracy",
        "macro_f1",
        "balanced_accuracy",
        "minimum_per_class_recall",
        "multiclass_brier",
        "multiclass_log_loss",
    ):

        assert key in metrics


def test_23_confirmation_function_accepts_mapping() -> None:

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

    assert (
        result[
            "passed"
        ]
        is True
    )


def test_24_same_test_tuning_blocked() -> None:

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


def test_25_feature_hyperparameter_tuning_blocked() -> None:

    assert (
        contract.TEST_RESULT_MAY_NOT_TRIGGER_FEATURE_SELECTION
        is True
    )

    assert (
        contract.TEST_RESULT_MAY_NOT_TRIGGER_HYPERPARAMETER_CHANGE
        is True
    )

    assert (
        contract.TEST_RESULT_MAY_NOT_TRIGGER_CANDIDATE_REPLACEMENT
        is True
    )


def test_26_runner_has_no_threshold_tuning() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "GridSearchCV" not in text
    assert "RandomizedSearchCV" not in text
    assert "CalibratedClassifierCV" not in text


def test_27_runner_has_no_forward30_access() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "forward_outcomes.jsonl"
        in text
    )

    assert (
        "forward_30_used"
        in text
    )

    assert (
        '"forward_30_used": False'
        in text
    )


def test_28_runner_has_no_market_acquisition() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text
    assert "copy_ticks" not in text
    assert "copy_rates" not in text
    assert "order_send(" not in text


def test_29_protected_ledgers_guarded() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "PROTECTED_LEDGER_CHANGED_DURING_G7GB"
        in text
    )


def test_30_live_execution_blocked() -> None:

    assert (
        contract.TEST_PASS_DOES_NOT_AUTHORIZE_LIVE_TRADING
        is True
    )

    assert (
        contract.TEST_PASS_DOES_NOT_AUTHORIZE_EXECUTION
        is True
    )


def test_31_runner_reports_test_state_on_failure() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        '"test_values_loaded"'
        in text
    )

    assert (
        "SAME_TEST_RERUN_AUTHORIZED=false"
        in text
    )


def test_32_evidence_is_create_only() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "write_json_new(\n        EVIDENCE_PATH,"
        in text
    )


def test_33_no_pnl_evaluation() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        '"pnl_evaluated": False'
        in text
    )


def test_34_test_confirmation_thresholds_still_exact() -> None:

    assert (
        contract.TEST_MACRO_F1_MINIMUM
        ==
        0.3241422107016895
    )

    assert (
        contract.TEST_BALANCED_ACCURACY_MINIMUM
        ==
        0.3399845741475606
    )

    assert (
        contract.TEST_MINIMUM_PER_CLASS_RECALL_MINIMUM
        ==
        0.2601206801974767
    )

    assert (
        contract.TEST_MULTICLASS_BRIER_MAXIMUM
        ==
        0.7148217771177803
    )

    assert (
        contract.TEST_MULTICLASS_LOG_LOSS_MAXIMUM
        ==
        1.1958580283040205
    )