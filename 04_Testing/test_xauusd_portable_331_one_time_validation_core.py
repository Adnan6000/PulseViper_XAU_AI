from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest


MODULE_PATH = Path(__file__).with_name(
    "xauusd_portable_331_one_time_validation_core.py"
)

spec = importlib.util.spec_from_file_location(
    "xauusd_one_time_validation_core_test_target",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

core = importlib.util.module_from_spec(
    spec
)

sys.modules[
    spec.name
] = core

spec.loader.exec_module(
    core
)


class SyntheticPerfectModel:
    def __init__(
        self,
    ) -> None:
        self.classes_ = np.asarray(
            [
                -1,
                0,
                1,
            ],
            dtype=np.int8,
        )

        self.n_features_in_ = 331

    def predict_proba(
        self,
        X: np.ndarray,
    ) -> np.ndarray:
        probabilities = np.full(
            (
                X.shape[
                    0
                ],
                3,
            ),
            0.05,
            dtype=np.float64,
        )

        labels = np.asarray(
            np.rint(
                X[
                    :,
                    0
                ]
            ),
            dtype=np.int8,
        )

        mapping = {
            -1: 0,
            0: 1,
            1: 2,
        }

        for (
            row_index,
            label,
        ) in enumerate(
            labels
        ):
            probabilities[
                row_index,
                mapping[
                    int(
                        label
                    )
                ],
            ] = 0.90

        return probabilities


class SyntheticRejectModel:
    def __init__(
        self,
    ) -> None:
        self.classes_ = np.asarray(
            [
                -1,
                0,
                1,
            ],
            dtype=np.int8,
        )

        self.n_features_in_ = 331

    def predict_proba(
        self,
        X: np.ndarray,
    ) -> np.ndarray:
        probabilities = np.empty(
            (
                X.shape[
                    0
                ],
                3,
            ),
            dtype=np.float64,
        )

        probabilities[
            :,
            0
        ] = 0.05

        probabilities[
            :,
            1
        ] = 0.90

        probabilities[
            :,
            2
        ] = 0.05

        return probabilities


class InvalidSyntheticModel:
    def __init__(
        self,
    ) -> None:
        self.classes_ = np.asarray(
            [
                0,
                1,
            ],
            dtype=np.int8,
        )

        self.n_features_in_ = 331

    def predict_proba(
        self,
        X: np.ndarray,
    ) -> np.ndarray:
        return np.full(
            (
                X.shape[
                    0
                ],
                2,
            ),
            0.5,
            dtype=np.float64,
        )


def _protocol():
    return core._read_json_auto(
        core.PROTOCOL_PATH
    )


def _batch(
    n_rows: int = 90,
):
    y_class = np.resize(
        np.asarray(
            [
                -1,
                0,
                1,
            ],
            dtype=np.int8,
        ),
        n_rows,
    )

    X = np.zeros(
        (
            n_rows,
            331,
        ),
        dtype=np.float64,
    )

    X[
        :,
        0
    ] = y_class.astype(
        np.float64
    )

    target_tradeable = (
        y_class
        != 0
    ).astype(
        np.int8
    )

    decision_time = np.arange(
        n_rows,
        dtype=np.int64,
    )

    feature_columns = tuple(
        f"synthetic_feature_{index:03d}"
        for index in range(
            331
        )
    )

    return core.ValidationBatch(
        X=X,
        target_class=y_class,
        target_tradeable=target_tradeable,
        decision_time=decision_time,
        feature_columns=feature_columns,
        split_name="VALIDATION",
    )


def _ledger(
    tmp_path: Path,
):
    return core.ValidationAccessLedger(
        path=(
            tmp_path
            / "validation_access_ledger.json"
        ),
        protocol_fingerprint_sha256=(
            core.EXPECTED_PROTOCOL_FINGERPRINT
        ),
        model_artifact_sha256=(
            core.EXPECTED_MODEL_ARTIFACT_SHA256
        ),
    )


def test_frozen_protocol_validates_exact_fingerprint():
    contract = (
        core.validate_frozen_validation_protocol(
            _protocol()
        )
    )

    assert (
        contract[
            "contract_version"
        ]
        == core.EXPECTED_PROTOCOL_CONTRACT_VERSION
    )


def test_protocol_tamper_fails_closed():
    payload = _protocol()

    payload[
        "contract"
    ][
        "acceptance_gate"
    ][
        "minimum_directional_macro_f1_short_long"
    ] = 0.20

    with pytest.raises(
        core.ValidationCoreError
    ):
        core.validate_frozen_validation_protocol(
            payload
        )


def test_implementation_attestation_has_no_real_value_access():
    report = (
        core.build_implementation_attestation()
    )

    assert (
        report[
            "valid"
        ]
        is True
    )

    assert (
        report[
            "implementation"
        ][
            "real_validation_data_source_wired"
        ]
        is False
    )

    assert (
        report[
            "decision"
        ][
            "real_validation_execution_authorized"
        ]
        is False
    )

    assert (
        report[
            "scientific_policy"
        ][
            "portable_validation_feature_values_loaded"
        ]
        is False
    )

    assert (
        report[
            "scientific_policy"
        ][
            "portable_test_feature_values_loaded"
        ]
        is False
    )


def test_synthetic_perfect_validation_passes_and_consumes_once(
    tmp_path: Path,
):
    ledger = _ledger(
        tmp_path
    )

    source_called = {
        "value": False,
    }

    def source():
        current = ledger.load()

        assert (
            current[
                "status"
            ]
            == "READ_INITIATED_CONSUMED_BOUNDARY"
        )

        assert (
            current[
                "validation_read_attempt_count"
            ]
            == 1
        )

        assert (
            current[
                "holdout_consumed_for_rerun_policy"
            ]
            is True
        )

        source_called[
            "value"
        ] = True

        return _batch()

    report = (
        core.run_one_time_validation_from_source(
            protocol_payload=_protocol(),
            model=SyntheticPerfectModel(),
            source=source,
            ledger=ledger,
        )
    )

    assert (
        source_called[
            "value"
        ]
        is True
    )

    assert (
        report[
            "validation_result"
        ][
            "gate_result"
        ][
            "accepted"
        ]
        is True
    )

    assert (
        report[
            "decision"
        ][
            "test_access_authorized_next"
        ]
        is True
    )

    final_ledger = ledger.load()

    assert (
        final_ledger[
            "status"
        ]
        == "VALIDATION_COMPLETE_ACCEPTED"
    )

    assert (
        final_ledger[
            "validation_read_attempt_count"
        ]
        == 1
    )

    assert (
        final_ledger[
            "validation_metrics_computed"
        ]
        is True
    )


def test_synthetic_rejected_validation_does_not_authorize_test(
    tmp_path: Path,
):
    ledger = _ledger(
        tmp_path
    )

    report = (
        core.run_one_time_validation_from_source(
            protocol_payload=_protocol(),
            model=SyntheticRejectModel(),
            source=_batch,
            ledger=ledger,
        )
    )

    assert (
        report[
            "validation_result"
        ][
            "gate_result"
        ][
            "accepted"
        ]
        is False
    )

    assert (
        report[
            "decision"
        ][
            "test_access_authorized_next"
        ]
        is False
    )

    final_ledger = ledger.load()

    assert (
        final_ledger[
            "status"
        ]
        == "VALIDATION_COMPLETE_REJECTED"
    )


def test_pre_read_model_failure_is_not_holdout_consumption(
    tmp_path: Path,
):
    ledger = _ledger(
        tmp_path
    )

    source_called = {
        "value": False,
    }

    def source():
        source_called[
            "value"
        ] = True

        return _batch()

    with pytest.raises(
        core.ValidationCoreError
    ):
        core.run_one_time_validation_from_source(
            protocol_payload=_protocol(),
            model=InvalidSyntheticModel(),
            source=source,
            ledger=ledger,
        )

    assert (
        source_called[
            "value"
        ]
        is False
    )

    state = ledger.load()

    assert (
        state[
            "status"
        ]
        == "PRE_READ_TECHNICAL_FAILURE"
    )

    assert (
        state[
            "validation_read_attempt_count"
        ]
        == 0
    )

    assert (
        state[
            "holdout_consumed_for_rerun_policy"
        ]
        is False
    )

    recovered = (
        ledger.reserve_before_read()
    )

    assert (
        recovered[
            "status"
        ]
        == "RESERVED_BEFORE_READ"
    )


def test_post_read_failure_marks_consumed_and_blocks_rerun(
    tmp_path: Path,
):
    ledger = _ledger(
        tmp_path
    )

    def failing_source():
        state = ledger.load()

        assert (
            state[
                "status"
            ]
            == "READ_INITIATED_CONSUMED_BOUNDARY"
        )

        raise RuntimeError(
            "synthetic post-read technical failure"
        )

    with pytest.raises(
        RuntimeError
    ):
        core.run_one_time_validation_from_source(
            protocol_payload=_protocol(),
            model=SyntheticPerfectModel(),
            source=failing_source,
            ledger=ledger,
        )

    state = ledger.load()

    assert (
        state[
            "status"
        ]
        == "CONSUMED_TECHNICAL_FAILURE"
    )

    assert (
        state[
            "validation_read_attempt_count"
        ]
        == 1
    )

    assert (
        state[
            "holdout_consumed_for_rerun_policy"
        ]
        is True
    )

    with pytest.raises(
        core.ValidationLedgerError
    ):
        ledger.reserve_before_read()


def test_completed_validation_cannot_be_run_twice(
    tmp_path: Path,
):
    ledger = _ledger(
        tmp_path
    )

    core.run_one_time_validation_from_source(
        protocol_payload=_protocol(),
        model=SyntheticPerfectModel(),
        source=_batch,
        ledger=ledger,
    )

    with pytest.raises(
        core.ValidationLedgerError
    ):
        core.run_one_time_validation_from_source(
            protocol_payload=_protocol(),
            model=SyntheticPerfectModel(),
            source=_batch,
            ledger=ledger,
        )