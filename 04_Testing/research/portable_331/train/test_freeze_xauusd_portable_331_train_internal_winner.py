from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name(
    "freeze_xauusd_portable_331_train_internal_winner.py"
)

spec = importlib.util.spec_from_file_location(
    "xauusd_train_internal_winner_freeze_test_target",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

freeze = importlib.util.module_from_spec(
    spec
)

sys.modules[
    spec.name
] = freeze

spec.loader.exec_module(
    freeze
)


def _runtime_objects():
    evaluator = freeze._load_evaluator()

    registry = (
        evaluator.load_frozen_candidate_registry(
            freeze.REGISTRY_PATH
        )
    )

    evaluation = (
        freeze._load_json_auto(
            freeze.EVALUATION_PATH
        )
    )

    return (
        evaluator,
        registry,
        evaluation,
    )


def test_reviewed_real_evaluation_freezes_c04():
    report = freeze.build_winner_freeze()

    assert report[
        "valid"
    ] is True

    assert (
        report[
            "winner"
        ][
            "candidate_id"
        ]
        == "C04_FLAT_EXTRA_TREES_CONSTRAINED"
    )

    assert (
        report[
            "decision"
        ][
            "winner_frozen_for_full_train_fit"
        ]
        is True
    )

    assert (
        report[
            "decision"
        ][
            "full_train_fit_authorized_next"
        ]
        is True
    )

    assert (
        report[
            "decision"
        ][
            "validation_access_authorized"
        ]
        is False
    )

    assert (
        report[
            "decision"
        ][
            "test_access_authorized"
        ]
        is False
    )


def test_nested_evaluation_tamper_fails_closed():
    (
        evaluator,
        registry,
        evaluation,
    ) = _runtime_objects()

    tampered = copy.deepcopy(
        evaluation
    )

    tampered[
        "evaluation"
    ][
        "candidate_reports"
    ][
        3
    ][
        "summary"
    ][
        "worst_fold_directional_macro_f1_short_long"
    ] += 0.01

    with pytest.raises(
        freeze.WinnerFreezeError
    ):
        freeze.validate_reviewed_evaluation(
            tampered,
            registry,
            evaluator,
        )


def test_recomputed_selection_rejects_winner_tamper():
    (
        evaluator,
        registry,
        evaluation,
    ) = _runtime_objects()

    tampered = copy.deepcopy(
        evaluation
    )

    tampered[
        "evaluation"
    ][
        "selection"
    ][
        "winner_candidate_id"
    ] = "C03_FLAT_HGB_SHALLOW"

    tampered[
        "evaluation_fingerprint"
    ][
        "sha256"
    ] = freeze._canonical_json_sha256(
        tampered[
            "evaluation"
        ]
    )

    original_expected = (
        freeze.EXPECTED_EVALUATION_FINGERPRINT
    )

    try:
        freeze.EXPECTED_EVALUATION_FINGERPRINT = (
            tampered[
                "evaluation_fingerprint"
            ][
                "sha256"
            ]
        )

        with pytest.raises(
            freeze.WinnerFreezeError
        ):
            freeze.validate_reviewed_evaluation(
                tampered,
                registry,
                evaluator,
            )

    finally:
        freeze.EXPECTED_EVALUATION_FINGERPRINT = (
            original_expected
        )


def test_holdout_boundary_tamper_fails_closed():
    (
        evaluator,
        registry,
        evaluation,
    ) = _runtime_objects()

    tampered = copy.deepcopy(
        evaluation
    )

    tampered[
        "scientific_policy"
    ][
        "portable_validation_feature_values_loaded"
    ] = True

    with pytest.raises(
        freeze.WinnerFreezeError
    ):
        freeze.validate_reviewed_evaluation(
            tampered,
            registry,
            evaluator,
        )