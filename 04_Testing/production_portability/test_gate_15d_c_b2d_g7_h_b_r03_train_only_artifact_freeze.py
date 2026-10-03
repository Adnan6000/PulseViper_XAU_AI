from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import ExtraTreesClassifier


RUNNER_PATH = (
    Path(__file__)
    .resolve()
    .parent
    /
    "run_xauusd_gate_15d_c_b2d_g7_h_b_r03_train_only_artifact_freeze.py"
)


spec = importlib.util.spec_from_file_location(
    "g7hb",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g7hb: Any = (
    importlib.util.module_from_spec(
        spec
    )
)

spec.loader.exec_module(
    g7hb
)


builder: Any = importlib.import_module(
    "02_AI.Models."
    "r03_train_only_frozen_artifact_builder"
)

contract: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_r03_prospective_forward_validation_contract"
)


def test_01_base_authority_exact() -> None:

    assert (
        g7hb.BASE_AUTHORITY_COMMIT
        ==
        "439f8409efbc15a571180100533808042291b4ed"
    )


def test_02_prospective_contract_exact() -> None:

    assert (
        contract.CONTRACT_FINGERPRINT_SHA256
        ==
        "e70d8e26c8f4734c456022689d47de406fe3f8daf1827d01b7f0f0d7fe752b9e"
    )


def test_03_candidate_id_exact() -> None:

    assert (
        builder.WINNER_CANDIDATE_ID
        ==
        "R03_FLAT_EXTRA_TREES_SMOOTH"
    )


def test_04_candidate_fingerprint_exact() -> None:

    assert (
        builder.WINNER_CANDIDATE_FINGERPRINT_SHA256
        ==
        "ae644c7272a015c26daeaaa7e655120bd7a3e4d267b2acd0d1f235e10bfa2e5f"
    )


def test_05_feature_hash_exact() -> None:

    assert (
        builder.FEATURE_COLUMNS_SHA256
        ==
        "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
    )


def test_06_exact_estimator_type() -> None:

    estimator = builder.build_estimator(
        builder.winner_candidate()
    )

    assert isinstance(
        estimator,
        ExtraTreesClassifier,
    )


def test_07_exact_n_estimators() -> None:

    estimator = builder.build_estimator(
        builder.winner_candidate()
    )

    assert estimator.n_estimators == 750


def test_08_exact_max_depth() -> None:

    estimator = builder.build_estimator(
        builder.winner_candidate()
    )

    assert estimator.max_depth == 8


def test_09_exact_max_features() -> None:

    estimator = builder.build_estimator(
        builder.winner_candidate()
    )

    assert estimator.max_features == 0.50


def test_10_exact_min_samples_leaf() -> None:

    estimator = builder.build_estimator(
        builder.winner_candidate()
    )

    assert estimator.min_samples_leaf == 50


def test_11_class_weight_balanced() -> None:

    estimator = builder.build_estimator(
        builder.winner_candidate()
    )

    assert estimator.class_weight == "balanced"


def test_12_bootstrap_false() -> None:

    estimator = builder.build_estimator(
        builder.winner_candidate()
    )

    assert estimator.bootstrap is False


def test_13_random_state_exact() -> None:

    estimator = builder.build_estimator(
        builder.winner_candidate()
    )

    assert estimator.random_state == 271828


def test_14_no_scaler() -> None:

    candidate = builder.winner_candidate()

    assert (
        candidate[
            "preprocessing"
        ][
            "standard_scaler"
        ]
        is False
    )


def test_15_prediction_rule_exact() -> None:

    assert (
        builder.PREDICTION_RULE
        ==
        "ARGMAX_3CLASS_PROBABILITY"
    )


def test_16_probability_order_exact() -> None:

    assert (
        builder.PROBABILITY_CLASS_ORDER
        ==
        (
            -1,
            0,
            1,
        )
    )


def test_17_synthetic_deterministic_semantics() -> None:

    rng = np.random.default_rng(
        271828
    )

    X = rng.normal(
        size=(
            180,
            8,
        )
    )

    y = np.asarray(
        [-1] * 60
        +
        [0] * 60
        +
        [1] * 60,
        dtype=np.int8,
    )

    first = builder.build_estimator(
        builder.winner_candidate()
    )

    second = builder.build_estimator(
        builder.winner_candidate()
    )

    first.fit(
        X,
        y,
    )

    second.fit(
        X,
        y,
    )

    p1 = builder.reorder_probabilities(
        first,
        X[
            :32
        ],
    )

    p2 = builder.reorder_probabilities(
        second,
        X[
            :32
        ],
    )

    assert np.allclose(
        p1,
        p2,
        rtol=builder.PARITY_RTOL,
        atol=builder.PARITY_ATOL,
    )

    assert np.array_equal(
        builder.argmax_predictions(
            p1
        ),
        builder.argmax_predictions(
            p2
        ),
    )


def test_18_probability_hash_deterministic_for_same_bytes() -> None:

    value = np.asarray(
        [
            [0.2, 0.3, 0.5],
            [0.4, 0.4, 0.2],
        ],
        dtype=np.float64,
    )

    assert (
        builder.probability_sha256(
            value
        )
        ==
        builder.probability_sha256(
            value.copy()
        )
    )


def test_19_parity_tolerance_tight() -> None:

    assert (
        builder.PARITY_RTOL
        ==
        1e-12
    )

    assert (
        builder.PARITY_ATOL
        ==
        1e-12
    )


def test_20_existing_orphan_artifact_recovery_supported() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "artifact_recovery_mode"
        in text
    )

    assert (
        "ARTIFACT_PATH.exists()"
        in text
    )


def test_21_existing_artifact_not_overwritten() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        '"artifact_overwritten": False'
        in text
    )


def test_22_manifest_create_only() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "FROZEN_ARTIFACT_MANIFEST_ALREADY_EXISTS"
        in text
    )


def test_23_evidence_create_only() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "FROZEN_ARTIFACT_EVIDENCE_ALREADY_EXISTS"
        in text
    )


def test_24_training_loader_only() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "load_train_supervised()"
        in text
    )

    assert (
        "load_validation"
        not in text
    )

    assert (
        "load_test"
        not in text
    )


def test_25_no_train_validation_refit() -> None:

    assert (
        contract.TRAIN_PLUS_VALIDATION_REFIT_ALLOWED
        is False
    )


def test_26_no_old_forward30() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        '"old_forward_30_used": False'
        in text
    )


def test_27_no_market_data() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text
    assert "copy_ticks" not in text
    assert "copy_rates" not in text
    assert "order_send(" not in text


def test_28_no_prospective_ledger_write() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        '"prospective_ledgers_written": False'
        in text
    )


def test_29_numeric_parity_required() -> None:

    text = Path(
        builder.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "ARTIFACT_RELOAD_NUMERIC_PARITY_MISMATCH"
        in text
    )


def test_30_argmax_parity_required() -> None:

    text = Path(
        builder.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "ARTIFACT_RELOAD_ARGMAX_PARITY_MISMATCH"
        in text
    )


def test_31_probe_rows_exact() -> None:

    assert (
        builder.PROBE_ROWS
        ==
        256
    )


def test_32_artifact_schema_exact() -> None:

    assert (
        builder.ARTIFACT_SCHEMA_VERSION
        ==
        "R03_TRAIN_ONLY_FROZEN_ARTIFACT_V1"
    )


def test_33_protected_ledger_guard() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "PROTECTED_LEDGER_CHANGED_DURING_G7HB"
        in text
    )


def test_34_artifact_before_collection_requirement() -> None:

    assert (
        contract.MODEL_ARTIFACT_MUST_BE_FROZEN_BEFORE_COLLECTION
        is True
    )


def test_35_live_execution_still_blocked() -> None:

    assert (
        contract.PROSPECTIVE_PASS_AUTHORIZES_LIVE
        is False
    )

    assert (
        contract.PROSPECTIVE_PASS_AUTHORIZES_EXECUTION
        is False
    )


def test_36_artifact_path_is_joblib() -> None:

    assert (
        g7hb.ARTIFACT_PATH.suffix
        ==
        ".joblib"
    )