from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pytest
from sklearn.ensemble import ExtraTreesClassifier


MODULE_PATH = Path(__file__).with_name(
    "fit_xauusd_portable_331_c04_full_train_model.py"
)

spec = importlib.util.spec_from_file_location(
    "xauusd_c04_full_train_fit_test_target",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

fit = importlib.util.module_from_spec(
    spec
)

sys.modules[
    spec.name
] = fit

spec.loader.exec_module(
    fit
)


def _freeze_module():
    return fit._load_module(
        fit.WINNER_FREEZE_RUNNER_PATH,
        "xauusd_winner_freeze_for_full_fit_tests",
    )


def test_frozen_winner_rebuild_matches_and_authorizes_exact_c04():
    freeze_module = _freeze_module()

    (
        stored,
        config,
    ) = fit._load_and_validate_winner_freeze(
        freeze_module
    )

    assert (
        stored[
            "valid"
        ]
        is True
    )

    assert (
        config[
            "candidate_id"
        ]
        == fit.EXPECTED_WINNER_ID
    )

    assert (
        fit._canonical_sha256(
            config
        )
        == fit.EXPECTED_WINNER_CONFIG_SHA256
    )

    assert (
        config[
            "estimator"
        ]
        == fit.EXPECTED_ESTIMATOR
    )


def test_tampered_stored_winner_freeze_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    freeze_module = _freeze_module()

    stored = fit._read_json(
        fit.WINNER_FREEZE_PATH
    )

    tampered = copy.deepcopy(
        stored
    )

    tampered[
        "decision"
    ][
        "winner_candidate_id"
    ] = "C03_FLAT_HGB_SHALLOW"

    path = (
        tmp_path
        / "winner_freeze.json"
    )

    path.write_text(
        json.dumps(
            tampered
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        fit,
        "WINNER_FREEZE_PATH",
        path,
    )

    with pytest.raises(
        fit.FullTrainFitError
    ):
        fit._load_and_validate_winner_freeze(
            freeze_module
        )


def test_build_model_uses_exact_frozen_extra_trees_config():
    evaluator = fit._load_module(
        fit.EVALUATOR_PATH,
        "xauusd_evaluator_for_full_fit_tests",
    )

    freeze_module = _freeze_module()

    (
        _,
        config,
    ) = fit._load_and_validate_winner_freeze(
        freeze_module
    )

    model = fit._build_model(
        evaluator,
        config,
    )

    assert (
        model.__class__.__name__
        == "ExtraTreesClassifier"
    )

    params = model.get_params(
        deep=False
    )

    for (
        key,
        expected,
    ) in fit.EXPECTED_ESTIMATOR.items():
        if (
            key
            == "implementation"
        ):
            continue

        assert (
            params[
                key
            ]
            == expected
        )


def test_model_structure_validation_checks_class_order_and_probabilities(
    monkeypatch: pytest.MonkeyPatch,
):
    X = np.asarray(
        [
            [-2.0, 0.0],
            [-1.0, 0.2],
            [0.0, 1.0],
            [0.2, 0.8],
            [1.0, 0.2],
            [2.0, 0.0],
        ],
        dtype=np.float64,
    )

    y = np.asarray(
        [
            -1,
            -1,
            0,
            0,
            1,
            1,
        ],
        dtype=np.int8,
    )

    model = ExtraTreesClassifier(
        n_estimators=3,
        random_state=271828,
    )

    model.fit(
        X,
        y,
    )

    monkeypatch.setattr(
        fit,
        "EXPECTED_FEATURES",
        2,
    )

    monkeypatch.setitem(
        fit.EXPECTED_ESTIMATOR,
        "n_estimators",
        3,
    )

    report = (
        fit._validate_model_structure(
            model,
            X,
        )
    )

    assert (
        report[
            "class_order"
        ]
        == [
            -1,
            0,
            1,
        ]
    )

    assert (
        report[
            "tree_count"
        ]
        == 3
    )

    assert (
        report[
            "structural_probability_rows_sum_to_one"
        ]
        is True
    )


def test_joblib_atomic_artifact_is_reloadable_and_hash_pinned(
    tmp_path: Path,
):
    model = ExtraTreesClassifier(
        n_estimators=2,
        random_state=271828,
    )

    X = np.asarray(
        [
            [-1.0],
            [0.0],
            [1.0],
            [-0.5],
            [0.5],
            [1.5],
        ],
        dtype=np.float64,
    )

    y = np.asarray(
        [
            -1,
            0,
            1,
            -1,
            0,
            1,
        ],
        dtype=np.int8,
    )

    model.fit(
        X,
        y,
    )

    path = (
        tmp_path
        / "model.joblib"
    )

    sha256 = (
        fit._dump_joblib_atomic(
            model,
            path,
        )
    )

    assert path.is_file()

    assert (
        fit._sha256_file(
            path
        )
        == sha256
    )

    loaded = joblib.load(
        path
    )

    assert (
        loaded.__class__.__name__
        == "ExtraTreesClassifier"
    )

    assert (
        tuple(
            int(
                value
            )
            for value
            in loaded.classes_
        )
        == (
            -1,
            0,
            1,
        )
    )