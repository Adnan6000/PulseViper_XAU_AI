from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest


MODULE_PATH = Path(__file__).with_name(
    "evaluate_xauusd_portable_331_train_model_candidates.py"
)

REGISTRY_PATH = (
    Path(__file__).resolve().parents[1]
    / "xauusd_portable_331_train_model_candidate_registry_design.json"
)

EXPECTED_FOLD_METRICS = (
    "balanced_accuracy_3class",
    "macro_f1_3class",
    "directional_macro_f1_short_long",
    "short_precision",
    "short_recall",
    "short_f1",
    "no_trade_precision",
    "no_trade_recall",
    "no_trade_f1",
    "long_precision",
    "long_recall",
    "long_f1",
    "log_loss_3class",
    "multiclass_brier",
    "predicted_trade_coverage",
)

spec = importlib.util.spec_from_file_location(
    "xauusd_portable_candidate_evaluator",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

candidate_evaluator = (
    importlib.util.module_from_spec(
        spec
    )
)

sys.modules[
    spec.name
] = candidate_evaluator

spec.loader.exec_module(
    candidate_evaluator
)


def _load_registry():
    return (
        candidate_evaluator
        .load_frozen_candidate_registry(
            REGISTRY_PATH
        )
    )


def _synthetic_train_matrix(
    n_rows: int = 360,
    n_features: int = 331,
):
    rng = np.random.default_rng(
        271828
    )

    y_class = np.resize(
        np.asarray(
            [-1, 0, 1],
            dtype=np.int8,
        ),
        n_rows,
    )

    X = rng.normal(
        0.0,
        0.35,
        size=(
            n_rows,
            n_features,
        ),
    )

    X[:, 0] = (
        4.0 * y_class
        + rng.normal(
            0.0,
            0.1,
            size=n_rows,
        )
    )

    X[:, 1] = (
        3.0
        * (
            y_class != 0
        ).astype(float)
        + rng.normal(
            0.0,
            0.1,
            size=n_rows,
        )
    )

    X[:, 2] = (
        2.5
        * (
            y_class == 1
        ).astype(float)
        - 2.5
        * (
            y_class == -1
        ).astype(float)
        + rng.normal(
            0.0,
            0.1,
            size=n_rows,
        )
    )

    y_tradeable = (
        y_class != 0
    ).astype(
        np.int8
    )

    folds = [
        candidate_evaluator.FoldSpec(
            "F1",
            0,
            90,
            102,
            150,
            12,
        ),
        candidate_evaluator.FoldSpec(
            "F2",
            0,
            150,
            162,
            210,
            12,
        ),
        candidate_evaluator.FoldSpec(
            "F3",
            0,
            210,
            222,
            270,
            12,
        ),
        candidate_evaluator.FoldSpec(
            "F4",
            0,
            270,
            282,
            360,
            12,
        ),
    ]

    return (
        X,
        y_class,
        y_tradeable,
        folds,
    )


def test_frozen_registry_fingerprint_and_contract_validate():
    registry = _load_registry()

    assert (
        registry[
            "registry_fingerprint"
        ][
            "sha256"
        ]
        == candidate_evaluator
        .EXPECTED_REGISTRY_FINGERPRINT_SHA256
    )


def test_registry_tamper_is_fail_closed():
    registry = _load_registry()

    tampered = copy.deepcopy(
        registry
    )

    tampered[
        "contract"
    ][
        "candidates"
    ][
        0
    ][
        "estimator"
    ][
        "C"
    ] = 0.051

    with pytest.raises(
        candidate_evaluator
        .EvaluatorContractError
    ):
        candidate_evaluator.validate_frozen_candidate_registry(
            tampered
        )


def test_fold_validation_enforces_frozen_purge():
    bad_folds = [
        candidate_evaluator.FoldSpec(
            "F1",
            0,
            90,
            101,
            150,
            12,
        ),
        candidate_evaluator.FoldSpec(
            "F2",
            0,
            150,
            162,
            210,
            12,
        ),
        candidate_evaluator.FoldSpec(
            "F3",
            0,
            210,
            222,
            270,
            12,
        ),
        candidate_evaluator.FoldSpec(
            "F4",
            0,
            270,
            282,
            360,
            12,
        ),
    ]

    with pytest.raises(
        candidate_evaluator
        .EvaluatorContractError
    ):
        candidate_evaluator.validate_fold_specs(
            bad_folds,
            360,
            4,
            12,
        )


def test_target_tradeable_linkage_is_fail_closed():
    (
        X,
        y_class,
        y_tradeable,
        _,
    ) = _synthetic_train_matrix()

    broken = y_tradeable.copy()

    broken[0] = (
        0
        if broken[0] == 1
        else 1
    )

    with pytest.raises(
        candidate_evaluator
        .EvaluatorContractError
    ):
        candidate_evaluator.validate_train_only_inputs(
            X,
            y_class,
            broken,
            331,
        )


def test_flat_and_hierarchical_candidates_pass_synthetic_walk_forward():
    registry = _load_registry()

    (
        X,
        y_class,
        y_tradeable,
        folds,
    ) = _synthetic_train_matrix()

    gate = registry[
        "contract"
    ][
        "eligibility_gate"
    ]

    candidates = registry[
        "contract"
    ][
        "candidates"
    ]

    for candidate in (
        candidates[0],
        candidates[4],
    ):
        report = (
            candidate_evaluator
            .evaluate_candidate_train_only(
                candidate,
                X,
                y_class,
                y_tradeable,
                folds,
                gate,
            )
        )

        assert (
            report[
                "status"
            ]
            == "ELIGIBLE"
        )

        assert (
            report[
                "eligible"
            ]
            is True
        )

        assert len(
            report[
                "fold_reports"
            ]
        ) == 4

        for fold_report in report[
            "fold_reports"
        ]:
            assert tuple(
                fold_report[
                    "metrics"
                ].keys()
            ) == EXPECTED_FOLD_METRICS

        assert (
            report[
                "summary"
            ][
                "worst_fold_directional_macro_f1_short_long"
            ]
            > 0.0
        )

        assert (
            report[
                "summary"
            ][
                "worst_fold_short_recall"
            ]
            > 0.0
        )

        assert (
            report[
                "summary"
            ][
                "worst_fold_long_recall"
            ]
            > 0.0
        )


def test_hierarchical_probability_contract_sums_to_one():
    registry = _load_registry()

    (
        X,
        y_class,
        y_tradeable,
        folds,
    ) = _synthetic_train_matrix()

    candidate = registry[
        "contract"
    ][
        "candidates"
    ][
        4
    ]

    fold = folds[0]

    probabilities = (
        candidate_evaluator
        .fit_predict_candidate_fold(
            candidate,
            X[
                fold.train_slice()
            ],
            y_class[
                fold.train_slice()
            ],
            y_tradeable[
                fold.train_slice()
            ],
            X[
                fold.validation_slice()
            ],
        )
    )

    assert (
        probabilities.shape
        == (
            (
                fold.validation_stop
                - fold.validation_start
            ),
            3,
        )
    )

    assert np.all(
        probabilities >= 0.0
    )

    assert np.all(
        probabilities <= 1.0
    )

    assert np.allclose(
        probabilities.sum(
            axis=1
        ),
        1.0,
        atol=1e-9,
        rtol=1e-9,
    )


def test_fold_metric_contract_is_exact_and_brier_semantics_are_correct():
    y_true = np.asarray(
        [-1, 0, 1, -1, 0, 1],
        dtype=np.int8,
    )

    probabilities = np.zeros(
        (
            y_true.shape[0],
            3,
        ),
        dtype=np.float64,
    )

    class_to_column = {
        -1: 0,
        0: 1,
        1: 2,
    }

    for row_index, label in enumerate(
        y_true
    ):
        probabilities[
            row_index,
            class_to_column[
                int(label)
            ],
        ] = 1.0

    metrics = (
        candidate_evaluator
        .compute_fold_metrics(
            y_true,
            probabilities,
        )
    )

    assert tuple(
        metrics.keys()
    ) == EXPECTED_FOLD_METRICS

    assert (
        tuple(
            candidate_evaluator
            .REQUIRED_FOLD_METRICS
        )
        == EXPECTED_FOLD_METRICS
    )

    assert (
        metrics[
            "balanced_accuracy_3class"
        ]
        == pytest.approx(
            1.0
        )
    )

    assert (
        metrics[
            "macro_f1_3class"
        ]
        == pytest.approx(
            1.0
        )
    )

    assert (
        metrics[
            "directional_macro_f1_short_long"
        ]
        == pytest.approx(
            1.0
        )
    )

    assert (
        metrics[
            "short_precision"
        ]
        == pytest.approx(
            1.0
        )
    )

    assert (
        metrics[
            "short_recall"
        ]
        == pytest.approx(
            1.0
        )
    )

    assert (
        metrics[
            "short_f1"
        ]
        == pytest.approx(
            1.0
        )
    )

    assert (
        metrics[
            "no_trade_precision"
        ]
        == pytest.approx(
            1.0
        )
    )

    assert (
        metrics[
            "no_trade_recall"
        ]
        == pytest.approx(
            1.0
        )
    )

    assert (
        metrics[
            "no_trade_f1"
        ]
        == pytest.approx(
            1.0
        )
    )

    assert (
        metrics[
            "long_precision"
        ]
        == pytest.approx(
            1.0
        )
    )

    assert (
        metrics[
            "long_recall"
        ]
        == pytest.approx(
            1.0
        )
    )

    assert (
        metrics[
            "long_f1"
        ]
        == pytest.approx(
            1.0
        )
    )

    assert (
        metrics[
            "log_loss_3class"
        ]
        == pytest.approx(
            0.0,
            abs=1e-12,
        )
    )

    assert (
        metrics[
            "multiclass_brier"
        ]
        == pytest.approx(
            0.0,
            abs=1e-12,
        )
    )

    assert (
        metrics[
            "predicted_trade_coverage"
        ]
        == pytest.approx(
            4.0 / 6.0
        )
    )


def test_selection_uses_declared_lexicographic_priority():
    registry = _load_registry()

    selection_policy = registry[
        "contract"
    ][
        "selection_policy"
    ]

    common = {
        "mean_directional_macro_f1_short_long": 0.60,
        "worst_fold_balanced_accuracy_3class": 0.50,
        "mean_macro_f1_3class": 0.50,
        "std_directional_macro_f1_short_long": 0.03,
        "mean_log_loss_3class": 1.0,
    }

    reports = [
        {
            "candidate_id": "A",
            "eligible": True,
            "summary": {
                **common,
                "worst_fold_directional_macro_f1_short_long": 0.40,
            },
        },
        {
            "candidate_id": "B",
            "eligible": True,
            "summary": {
                **common,
                "worst_fold_directional_macro_f1_short_long": 0.41,
            },
        },
    ]

    selection = (
        candidate_evaluator
        .select_winner(
            reports,
            selection_policy,
        )
    )

    assert (
        selection[
            "winner_candidate_id"
        ]
        == "B"
    )

    assert (
        selection[
            "status"
        ]
        == "WINNER_SELECTED_TRAIN_INTERNAL_ONLY"
    )