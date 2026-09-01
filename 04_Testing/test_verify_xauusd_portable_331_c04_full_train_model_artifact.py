from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name(
    "verify_xauusd_portable_331_c04_full_train_model_artifact.py"
)

spec = importlib.util.spec_from_file_location(
    "xauusd_c04_model_artifact_verifier_test_target",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

verify = importlib.util.module_from_spec(
    spec
)

sys.modules[
    spec.name
] = verify

spec.loader.exec_module(
    verify
)


def _real_payloads():
    winner_freeze = (
        verify._read_json_auto(
            verify.WINNER_FREEZE_PATH
        )
    )

    fit_payload = (
        verify._read_json_auto(
            verify.FULL_TRAIN_FIT_PATH
        )
    )

    return (
        winner_freeze,
        fit_payload,
    )


def test_real_frozen_c04_artifact_and_provenance_verify():
    report = (
        verify.build_verification()
    )

    assert (
        report[
            "valid"
        ]
        is True
    )

    assert (
        report[
            "artifact_validation"
        ][
            "model_artifact_sha256"
        ]
        == verify.EXPECTED_MODEL_ARTIFACT_SHA256
    )

    assert (
        report[
            "artifact_validation"
        ][
            "tree_count"
        ]
        == 500
    )

    assert (
        report[
            "artifact_validation"
        ][
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
            "decision"
        ][
            "validation_access_authorized_next"
        ]
        is True
    )

    assert (
        report[
            "decision"
        ][
            "test_access_authorized"
        ]
        is False
    )


def test_winner_freeze_config_tamper_fails_closed():
    (
        winner_freeze,
        _,
    ) = _real_payloads()

    tampered = copy.deepcopy(
        winner_freeze
    )

    tampered[
        "winner"
    ][
        "candidate_config"
    ][
        "estimator"
    ][
        "max_depth"
    ] = 11

    with pytest.raises(
        verify.ModelArtifactVerificationError
    ):
        verify.validate_winner_freeze(
            tampered
        )


def test_full_train_holdout_boundary_tamper_fails_closed():
    (
        winner_freeze,
        fit_payload,
    ) = _real_payloads()

    tampered = copy.deepcopy(
        fit_payload
    )

    tampered[
        "scientific_policy"
    ][
        "portable_validation_feature_values_loaded"
    ] = True

    with pytest.raises(
        verify.ModelArtifactVerificationError
    ):
        verify.validate_full_train_fit_report(
            tampered,
            winner_freeze,
        )


def test_model_record_sha_tamper_fails_closed():
    (
        winner_freeze,
        fit_payload,
    ) = _real_payloads()

    tampered = copy.deepcopy(
        fit_payload
    )

    tampered[
        "model_record"
    ][
        "model_artifact_sha256"
    ] = (
        "0"
        * 64
    )

    with pytest.raises(
        verify.ModelArtifactVerificationError
    ):
        verify.validate_full_train_fit_report(
            tampered,
            winner_freeze,
        )


def test_missing_model_artifact_fails_closed(
    tmp_path: Path,
):
    (
        winner_freeze,
        fit_payload,
    ) = _real_payloads()

    model_record = (
        verify.validate_full_train_fit_report(
            fit_payload,
            winner_freeze,
        )
    )

    missing = (
        tmp_path
        / "xauusd_portable_331_c04_full_train_model.joblib"
    )

    with pytest.raises(
        verify.ModelArtifactVerificationError
    ):
        verify.validate_model_artifact(
            model_record,
            missing,
        )