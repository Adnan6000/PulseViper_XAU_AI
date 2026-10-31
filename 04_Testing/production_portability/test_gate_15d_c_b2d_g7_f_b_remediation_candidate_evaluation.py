from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any

import numpy as np


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
    "run_xauusd_gate_15d_c_b2d_g7_f_b_remediation_candidate_evaluation.py"
)


spec = importlib.util.spec_from_file_location(
    "g7fb",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g7fb: Any = (
    importlib.util.module_from_spec(
        spec
    )
)

spec.loader.exec_module(
    g7fb
)


registry: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_candidate_registry"
)

access: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_train_validation_access_contract"
)

evaluator: Any = importlib.import_module(
    "02_AI.Models."
    "remediation_candidate_evaluator"
)


def synthetic_data(
    rows: int = 360,
    features: int = 6,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:

    rng = np.random.default_rng(
        271828
    )

    X = rng.normal(
        size=(
            rows,
            features,
        )
    )

    signal = (
        X[
            :,
            0
        ]
        +
        0.5
        *
        X[
            :,
            1
        ]
    )

    y = np.zeros(
        rows,
        dtype=np.int8,
    )

    y[
        signal
        <
        -0.40
    ] = -1

    y[
        signal
        >
        0.40
    ] = 1

    tradeable = (
        y != 0
    ).astype(
        np.int8
    )

    return (
        X,
        y,
        tradeable,
    )


def lightweight_flat_candidate() -> dict[str, Any]:

    return {
        "candidate_id": "SYNTH_FLAT",
        "role": "TEST",
        "architecture": "FLAT_3CLASS",
        "family": "LOGISTIC_REGRESSION",
        "estimator": {
            "implementation": (
                "sklearn.linear_model."
                "LogisticRegression"
            ),
            "C": 0.1,
            "class_weight": "balanced",
            "max_iter": 500,
            "solver": "lbfgs",
        },
        "preprocessing": {
            "standard_scaler": True,
        },
        "probability_class_order": [
            -1,
            0,
            1,
        ],
    }


def lightweight_hier_candidate() -> dict[str, Any]:

    return {
        "candidate_id": "SYNTH_HIER",
        "role": "TEST",
        "architecture": (
            "HIERARCHICAL_TRADEABILITY_DIRECTION"
        ),
        "family": "TEST_HIER",
        "stage_a": {
            "estimator": {
                "implementation": (
                    "sklearn.linear_model."
                    "LogisticRegression"
                ),
                "C": 0.1,
                "class_weight": "balanced",
                "max_iter": 500,
                "solver": "lbfgs",
            },
            "preprocessing": {
                "standard_scaler": True,
            },
        },
        "stage_b": {
            "estimator": {
                "implementation": (
                    "sklearn.linear_model."
                    "LogisticRegression"
                ),
                "C": 0.1,
                "class_weight": "balanced",
                "max_iter": 500,
                "solver": "lbfgs",
            },
            "preprocessing": {
                "standard_scaler": True,
            },
        },
        "probability_class_order": [
            -1,
            0,
            1,
        ],
    }


def test_01_current_base_authority() -> None:

    assert (
        g7fb.BASE_AUTHORITY_COMMIT
        ==
        "4870dcfd432ff0fa2dd242a5e2bd2d2845fbd806"
    )


def test_02_registry_fingerprint_bound() -> None:

    assert (
        registry.REGISTRY_FINGERPRINT_SHA256
        ==
        "4556eb982086da0ea19ab910a30b5ab58788c7e5b7488ef8e3453e46289c0deb"
    )


def test_03_access_fingerprint_bound() -> None:

    assert (
        access.CONTRACT_FINGERPRINT_SHA256
        ==
        "bfd0cfee283dcb29cff79feff6a5366772a596c9635e470e06d56e70ead74b3e"
    )


def test_04_candidate_count_exact() -> None:

    assert (
        len(
            registry.CANDIDATES
        )
        ==
        6
    )


def test_05_test_access_remains_blocked() -> None:

    assert (
        access.TEST_FEATURE_ACCESS_AUTHORIZED
        is False
    )

    assert (
        access.TEST_TARGET_ACCESS_AUTHORIZED
        is False
    )


def test_06_flat_candidate_fit_predict() -> None:

    X, y, tradeable = synthetic_data()

    train_stop = 250

    probabilities = (
        evaluator.fit_predict_candidate(
            lightweight_flat_candidate(),
            X[
                :train_stop
            ],
            y[
                :train_stop
            ],
            tradeable[
                :train_stop
            ],
            X[
                train_stop:
            ],
        )
    )

    assert probabilities.shape == (
        110,
        3,
    )

    assert np.allclose(
        probabilities.sum(
            axis=1
        ),
        1.0,
    )


def test_07_hier_candidate_fit_predict() -> None:

    X, y, tradeable = synthetic_data()

    train_stop = 250

    probabilities = (
        evaluator.fit_predict_candidate(
            lightweight_hier_candidate(),
            X[
                :train_stop
            ],
            y[
                :train_stop
            ],
            tradeable[
                :train_stop
            ],
            X[
                train_stop:
            ],
        )
    )

    assert probabilities.shape == (
        110,
        3,
    )

    assert np.allclose(
        probabilities.sum(
            axis=1
        ),
        1.0,
    )


def test_08_metric_contract() -> None:

    X, y, tradeable = synthetic_data()

    train_stop = 250

    probabilities = (
        evaluator.fit_predict_candidate(
            lightweight_flat_candidate(),
            X[
                :train_stop
            ],
            y[
                :train_stop
            ],
            tradeable[
                :train_stop
            ],
            X[
                train_stop:
            ],
        )
    )

    metrics = (
        evaluator.compute_validation_metrics(
            y[
                train_stop:
            ],
            probabilities,
        )
    )

    required = {
        "exact_class_accuracy",
        "macro_f1",
        "balanced_accuracy",
        "minimum_per_class_recall",
        "short_precision",
        "short_recall",
        "short_f1",
        "no_trade_precision",
        "no_trade_recall",
        "no_trade_f1",
        "long_precision",
        "long_recall",
        "long_f1",
        "multiclass_brier",
        "multiclass_log_loss",
        "prediction_counts",
        "prediction_shares",
        "outcome_counts",
        "outcome_shares",
        "mean_probability_by_class",
        "mean_correct_confidence",
        "mean_incorrect_confidence",
    }

    assert required.issubset(
        metrics.keys()
    )


def test_09_selection_uses_macro_f1_first() -> None:

    assert (
        registry.SELECTION_POLICY[
            0
        ][
            "metric"
        ]
        ==
        "macro_f1"
    )

    assert (
        registry.SELECTION_POLICY[
            0
        ][
            "direction"
        ]
        ==
        "MAXIMIZE"
    )


def test_10_selection_lexicographic() -> None:

    reports = [
        {
            "candidate_id": "A",
            "eligible": True,
            "validation_metrics": {
                "macro_f1": 0.40,
                "balanced_accuracy": 0.90,
                "minimum_per_class_recall": 0.30,
                "multiclass_brier": 0.70,
                "multiclass_log_loss": 1.0,
                "exact_class_accuracy": 0.50,
            },
        },
        {
            "candidate_id": "B",
            "eligible": True,
            "validation_metrics": {
                "macro_f1": 0.41,
                "balanced_accuracy": 0.40,
                "minimum_per_class_recall": 0.20,
                "multiclass_brier": 0.90,
                "multiclass_log_loss": 1.2,
                "exact_class_accuracy": 0.40,
            },
        },
    ]

    selection = evaluator.select_winner(
        reports,
        registry.SELECTION_POLICY,
        "NO_WINNER",
    )

    assert (
        selection[
            "winner_candidate_id"
        ]
        ==
        "B"
    )


def test_11_no_winner_when_all_ineligible() -> None:

    reports = [
        {
            "candidate_id": "A",
            "eligible": False,
        },
        {
            "candidate_id": "B",
            "eligible": False,
        },
    ]

    selection = evaluator.select_winner(
        reports,
        registry.SELECTION_POLICY,
        "NO_WINNER",
    )

    assert (
        selection[
            "status"
        ]
        ==
        "NO_WINNER"
    )

    assert (
        selection[
            "winner_candidate_id"
        ]
        is None
    )


def test_12_registry_has_c04_control() -> None:

    assert (
        registry.CANDIDATES[
            0
        ][
            "candidate_id"
        ]
        ==
        "R00_CONTROL_C04_EXACT"
    )


def test_13_no_candidate_calibration() -> None:

    for candidate in (
        registry.CANDIDATES
    ):

        assert (
            candidate[
                "probability_calibration"
            ][
                "enabled"
            ]
            is False
        )


def test_14_no_threshold_tuning() -> None:

    for candidate in (
        registry.CANDIDATES
    ):

        assert (
            candidate[
                "threshold_policy"
            ][
                "tuning_enabled"
            ]
            is False
        )


def test_15_runner_protects_test_boundary() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "TEST_VALUES_LOADED=false"
        in text
    )

    assert (
        "TEST_EVALUATION_PERFORMED=false"
        in text
    )


def test_16_runner_does_not_call_test_loader() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        ".load_test_features("
        not in text
    )

    assert (
        ".load_test_targets("
        not in text
    )

    assert (
        ".load_test_supervised("
        not in text
    )


def test_17_runner_excludes_forward30() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "FORWARD_30_USED=false"
        in text
    )


def test_18_runner_no_mt5() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text
    assert "order_send(" not in text
    assert "order_check(" not in text


def test_19_runner_protects_ledgers() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "PROTECTED_LEDGER_CHANGED_DURING_G7FB"
        in text
    )


def test_20_evaluator_has_no_test_access() -> None:

    evaluator_path = (
        REPO_ROOT
        /
        "02_AI/Models/"
        "remediation_candidate_evaluator.py"
    )

    text = evaluator_path.read_text(
        encoding="utf-8"
    )

    assert "load_test" not in text
    assert "TEST_ROWS" not in text


def test_21_evaluator_has_no_forward_ledger_access() -> None:

    evaluator_path = (
        REPO_ROOT
        /
        "02_AI/Models/"
        "remediation_candidate_evaluator.py"
    )

    text = evaluator_path.read_text(
        encoding="utf-8"
    )

    assert (
        "shadow_observations"
        not in text
    )

    assert (
        "forward_outcomes"
        not in text
    )


def test_22_evaluator_has_no_pnl() -> None:

    evaluator_path = (
        REPO_ROOT
        /
        "02_AI/Models/"
        "remediation_candidate_evaluator.py"
    )

    text = evaluator_path.read_text(
        encoding="utf-8"
    ).lower()

    assert "profit_factor" not in text
    assert "sharpe" not in text
    assert "drawdown" not in text


def test_23_target_tradeable_consistency_checked() -> None:

    X, y, tradeable = synthetic_data(
        rows=120,
    )

    bad_tradeable = tradeable.copy()

    bad_tradeable[
        0
    ] = (
        1
        -
        bad_tradeable[
            0
        ]
    )

    raised = False

    try:

        evaluator.validate_supervised_inputs(
            X[
                :80
            ],
            y[
                :80
            ],
            bad_tradeable[
                :80
            ],
            X[
                80:
            ],
            y[
                80:
            ],
            tradeable[
                80:
            ],
            expected_feature_count=6,
        )

    except (
        evaluator.RemediationEvaluationError
    ):

        raised = True

    assert raised is True