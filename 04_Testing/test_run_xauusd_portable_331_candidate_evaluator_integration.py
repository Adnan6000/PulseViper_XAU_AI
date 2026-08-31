from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


MODULE_PATH = Path(__file__).with_name(
    "run_xauusd_portable_331_candidate_evaluator_integration.py"
)

EVALUATOR_PATH = Path(__file__).with_name(
    "evaluate_xauusd_portable_331_train_model_candidates.py"
)

spec = importlib.util.spec_from_file_location(
    "xauusd_candidate_integration_runner_test_target",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

runner = importlib.util.module_from_spec(
    spec
)

sys.modules[
    spec.name
] = runner

spec.loader.exec_module(
    runner
)

evaluator_spec = importlib.util.spec_from_file_location(
    "xauusd_candidate_evaluator_for_integration_tests",
    EVALUATOR_PATH,
)

assert evaluator_spec is not None
assert evaluator_spec.loader is not None

evaluator = importlib.util.module_from_spec(
    evaluator_spec
)

sys.modules[
    evaluator_spec.name
] = evaluator

evaluator_spec.loader.exec_module(
    evaluator
)


def _protocol_contract():
    return {
        "walk_forward_protocol": {
            "method": "EXPANDING_WINDOW_PURGED_TRAIN_ONLY",
            "chronological_order_required": True,
            "shuffle_allowed": False,
            "validation_rows_are_inside_frozen_train_only": True,
            "portable_validation_split_access_allowed": False,
            "portable_test_split_access_allowed": False,
            "fold_count": 4,
            "purge_rows_before_each_validation": 12,
            "folds": [
                {
                    "fold": 1,
                    "train_start_inclusive": 0,
                    "train_end_exclusive": 27974,
                    "train_rows": 27974,
                    "purge_start_inclusive": 27974,
                    "purge_end_exclusive": 27986,
                    "purge_rows": 12,
                    "validation_start_inclusive": 27986,
                    "validation_end_exclusive": 38481,
                    "validation_rows": 10495,
                },
                {
                    "fold": 2,
                    "train_start_inclusive": 0,
                    "train_end_exclusive": 38469,
                    "train_rows": 38469,
                    "purge_start_inclusive": 38469,
                    "purge_end_exclusive": 38481,
                    "purge_rows": 12,
                    "validation_start_inclusive": 38481,
                    "validation_end_exclusive": 48976,
                    "validation_rows": 10495,
                },
                {
                    "fold": 3,
                    "train_start_inclusive": 0,
                    "train_end_exclusive": 48964,
                    "train_rows": 48964,
                    "purge_start_inclusive": 48964,
                    "purge_end_exclusive": 48976,
                    "purge_rows": 12,
                    "validation_start_inclusive": 48976,
                    "validation_end_exclusive": 59471,
                    "validation_rows": 10495,
                },
                {
                    "fold": 4,
                    "train_start_inclusive": 0,
                    "train_end_exclusive": 59459,
                    "train_rows": 59459,
                    "purge_start_inclusive": 59459,
                    "purge_end_exclusive": 59471,
                    "purge_rows": 12,
                    "validation_start_inclusive": 59471,
                    "validation_end_exclusive": 69966,
                    "validation_rows": 10495,
                },
            ],
        }
    }


def _registry():
    return {
        "contract": {
            "frozen_train_identity": {
                "dataset_id": "dataset",
                "dataset_sha256": "dataset_sha",
                "manifest_sha256": "manifest_sha",
                "train_input_fingerprint_sha256": "input_sha",
                "train_target_fingerprint_sha256": "target_sha",
                "row_count": 69966,
            }
        }
    }


def _batch():
    rows = 69966

    X = np.zeros(
        (
            rows,
            331,
        ),
        dtype=np.float64,
    )

    target_class = np.resize(
        np.asarray(
            [-1, 0, 1],
            dtype=np.int8,
        ),
        rows,
    )

    target_tradeable = (
        target_class != 0
    ).astype(
        np.int8
    )

    decision_time = np.arange(
        rows,
        dtype=np.int64,
    )

    return SimpleNamespace(
        dataset_id="dataset",
        dataset_sha256="dataset_sha",
        manifest_sha256="manifest_sha",
        trainer_input_contract_version=(
            runner.EXPECTED_TRAINER_INPUT_CONTRACT
        ),
        trainer_input_contract_fingerprint_sha256=(
            runner.EXPECTED_TRAINER_INPUT_FINGERPRINT
        ),
        target_access_contract_version=(
            runner.EXPECTED_TARGET_ACCESS_CONTRACT
        ),
        target_access_contract_fingerprint_sha256=(
            runner.EXPECTED_TARGET_ACCESS_FINGERPRINT
        ),
        supervised_batch_contract_version=(
            runner.EXPECTED_SUPERVISED_BATCH_CONTRACT
        ),
        supervised_batch_contract_fingerprint_sha256=(
            runner.EXPECTED_SUPERVISED_BATCH_FINGERPRINT
        ),
        feature_columns=tuple(
            f"f_{index}"
            for index in range(
                331
            )
        ),
        feature_columns_sha256="feature_sha",
        train_input_fingerprint_sha256="input_sha",
        target_columns=(
            "target_class",
            "target_tradeable",
        ),
        train_target_fingerprint_sha256="target_sha",
        row_count=rows,
        decision_time=decision_time,
        X=X,
        target_class=target_class,
        target_tradeable=target_tradeable,
    )


def test_exact_frozen_fold_boundaries_build():
    folds = runner._build_folds(
        _protocol_contract(),
        evaluator,
    )

    assert len(
        folds
    ) == 4

    assert (
        folds[0].train_start,
        folds[0].train_stop,
        folds[0].validation_start,
        folds[0].validation_stop,
        folds[0].purge_rows,
    ) == (
        0,
        27974,
        27986,
        38481,
        12,
    )

    assert (
        folds[3].train_start,
        folds[3].train_stop,
        folds[3].validation_start,
        folds[3].validation_stop,
        folds[3].purge_rows,
    ) == (
        0,
        59459,
        59471,
        69966,
        12,
    )

    evaluator.validate_fold_specs(
        folds,
        n_rows=69966,
        required_fold_count=4,
        required_purge_rows=12,
    )


def test_fold_purge_tamper_fails_closed():
    contract = _protocol_contract()

    contract[
        "walk_forward_protocol"
    ][
        "folds"
    ][
        0
    ][
        "purge_end_exclusive"
    ] = 27985

    with pytest.raises(
        runner.IntegrationContractError
    ):
        runner._build_folds(
            contract,
            evaluator,
        )


def test_supervised_batch_identity_and_shape_validate():
    summary = runner._validate_supervised_batch(
        _batch(),
        _registry(),
    )

    assert (
        summary[
            "row_count"
        ]
        == 69966
    )

    assert (
        summary[
            "feature_count"
        ]
        == 331
    )

    assert (
        summary[
            "X_shape"
        ]
        == [
            69966,
            331,
        ]
    )

    assert (
        summary[
            "target_tradeable_linkage_confirmed"
        ]
        is True
    )

    assert (
        summary[
            "decision_time_strictly_increasing"
        ]
        is True
    )


def test_supervised_batch_identity_tamper_fails_closed():
    batch = _batch()

    batch.dataset_sha256 = "tampered"

    with pytest.raises(
        runner.IntegrationContractError
    ):
        runner._validate_supervised_batch(
            batch,
            _registry(),
        )


def test_target_linkage_tamper_fails_closed():
    batch = _batch()

    batch.target_tradeable = (
        batch.target_tradeable.copy()
    )

    batch.target_tradeable[
        0
    ] = (
        0
        if batch.target_tradeable[
            0
        ]
        == 1
        else 1
    )

    with pytest.raises(
        runner.IntegrationContractError
    ):
        runner._validate_supervised_batch(
            batch,
            _registry(),
        )


def test_non_chronological_decision_time_fails_closed():
    batch = _batch()

    batch.decision_time = (
        batch.decision_time.copy()
    )

    batch.decision_time[
        100
    ] = batch.decision_time[
        99
    ]

    with pytest.raises(
        runner.IntegrationContractError
    ):
        runner._validate_supervised_batch(
            batch,
            _registry(),
        )