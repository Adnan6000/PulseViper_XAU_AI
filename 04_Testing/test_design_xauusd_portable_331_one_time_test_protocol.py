from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name(
    "design_xauusd_portable_331_one_time_test_protocol.py"
)

spec = importlib.util.spec_from_file_location(
    "one_time_test_protocol_design",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

module = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    module
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(
    path: Path,
    value: dict,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _synthetic_parent_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validation_protocol_fp = "1" * 64
    validation_result_fp = "2" * 64
    validation_freeze_fp = "3" * 64

    model_bytes = (
        b"synthetic-model-artifact"
    )

    loader_bytes = (
        b"synthetic-loader-source\n"
    )

    monkeypatch.setattr(
        module,
        "EXPECTED_VALIDATION_PROTOCOL_FINGERPRINT",
        validation_protocol_fp,
    )

    monkeypatch.setattr(
        module,
        "EXPECTED_VALIDATION_RESULT_FINGERPRINT",
        validation_result_fp,
    )

    monkeypatch.setattr(
        module,
        "EXPECTED_VALIDATION_FREEZE_FINGERPRINT",
        validation_freeze_fp,
    )

    monkeypatch.setattr(
        module,
        "EXPECTED_MODEL_ARTIFACT_SHA256",
        _sha(model_bytes),
    )

    monkeypatch.setattr(
        module,
        "EXPECTED_LOADER_SOURCE_SHA256",
        _sha(loader_bytes),
    )

    _write_json(
        tmp_path
        / module.VALIDATION_PROTOCOL_PATH,
        {
            "protocol_fingerprint": (
                validation_protocol_fp
            ),
            "valid": True,
        },
    )

    _write_json(
        tmp_path
        / module.VALIDATION_RESULT_PATH,
        {
            "result_fingerprint": (
                validation_result_fp
            ),
            "valid": True,
        },
    )

    _write_json(
        tmp_path
        / module.VALIDATION_FREEZE_PATH,
        {
            "freeze_fingerprint": (
                validation_freeze_fp
            ),
            (
                "bound_validation_result_"
                "fingerprint"
            ): validation_result_fp,
            "decision": {
                "validation_result_frozen": (
                    True
                ),
                "validation_consumed": True,
                (
                    "validation_rerun_authorized"
                ): False,
                (
                    "test_runner_implementation_"
                    "authorized_next"
                ): True,
                (
                    "test_execution_authorized"
                ): False,
            },
        },
    )

    (
        tmp_path
        / module.MODEL_ARTIFACT_PATH
    ).write_bytes(
        model_bytes
    )

    loader_path = (
        tmp_path
        / module.LOADER_SOURCE_PATH
    )

    loader_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    loader_path.write_bytes(
        loader_bytes
    )


def test_contract_reuses_train_derived_floors_not_validation_metrics() -> None:
    contract = (
        module.build_protocol_contract()
    )

    policy = contract[
        "test_acceptance_policy"
    ]

    assert (
        policy["threshold_origin"]
        == "TRAIN_ONLY_FROZEN_PRE_VALIDATION"
    )

    assert (
        policy[
            "validation_metrics_used_to_set_or_"
            "raise_test_thresholds"
        ]
        is False
    )

    assert (
        policy[
            "directional_macro_f1_short_long_min"
        ]
        == pytest.approx(
            0.25365034089349603
        )
    )

    assert (
        policy[
            "balanced_accuracy_3class_min"
        ]
        == pytest.approx(
            0.34040386328178984
        )
    )

    assert (
        policy[
            "macro_f1_3class_min"
        ]
        == pytest.approx(
            0.24533114425757888
        )
    )

    assert (
        policy[
            "predicted_trade_coverage_min"
        ]
        == pytest.approx(
            0.05
        )
    )

    assert (
        policy[
            "predicted_trade_coverage_max"
        ]
        == pytest.approx(
            0.95
        )
    )


def test_contract_binds_frozen_model_features_and_validation_freeze() -> None:
    contract = (
        module.build_protocol_contract()
    )

    assert (
        contract[
            "dataset_binding"
        ][
            "feature_count"
        ]
        == 331
    )

    assert (
        contract[
            "dataset_binding"
        ][
            "feature_columns_sha256"
        ]
        == (
            module.EXPECTED_FEATURE_COLUMNS_SHA256
        )
    )

    assert (
        contract[
            "model_binding"
        ][
            "model_artifact_sha256"
        ]
        == (
            module.EXPECTED_MODEL_ARTIFACT_SHA256
        )
    )

    assert (
        contract[
            "model_binding"
        ][
            "probability_class_order"
        ]
        == [-1, 0, 1]
    )

    assert (
        contract[
            "parent_validation_binding"
        ][
            "validation_result_fingerprint"
        ]
        == (
            module.EXPECTED_VALIDATION_RESULT_FINGERPRINT
        )
    )

    assert (
        contract[
            "parent_validation_binding"
        ][
            "validation_freeze_fingerprint"
        ]
        == (
            module.EXPECTED_VALIDATION_FREEZE_FINGERPRINT
        )
    )

    assert (
        contract[
            "parent_validation_binding"
        ][
            "validation_reread_authorized"
        ]
        is False
    )


def test_contract_forbids_tuning_and_real_test_access_before_runner() -> None:
    contract = (
        module.build_protocol_contract()
    )

    scientific = contract[
        "scientific_policy"
    ]

    one_time = contract[
        "one_time_test_semantics"
    ]

    assert (
        scientific[
            "model_refit_allowed"
        ]
        is False
    )

    assert (
        scientific[
            "candidate_change_allowed"
        ]
        is False
    )

    assert (
        scientific[
            "threshold_search_allowed"
        ]
        is False
    )

    assert (
        scientific[
            "probability_calibration_allowed"
        ]
        is False
    )

    assert (
        scientific[
            "test_peeking_before_one_shot_"
            "execution_allowed"
        ]
        is False
    )

    assert (
        scientific[
            "shadow_authorized"
        ]
        is False
    )

    assert (
        scientific[
            "live_authorized"
        ]
        is False
    )

    assert (
        one_time[
            "read_initiation_is_"
            "consumption_boundary"
        ]
        is True
    )

    assert (
        one_time[
            "second_performance_driven_"
            "test_read_authorized"
        ]
        is False
    )


def test_protocol_fingerprint_is_deterministic() -> None:
    parent = {
        "parent_evidence_verified": True,
        "example": "same",
    }

    first = (
        module.build_protocol_document(
            parent
        )
    )

    second = (
        module.build_protocol_document(
            parent
        )
    )

    assert (
        first[
            "protocol_fingerprint"
        ]
        == second[
            "protocol_fingerprint"
        ]
    )

    assert (
        len(
            first[
                "protocol_fingerprint"
            ]
        )
        == 64
    )


def test_verify_parent_evidence_accepts_frozen_synthetic_chain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _synthetic_parent_files(
        tmp_path,
        monkeypatch,
    )

    evidence = (
        module.verify_parent_evidence(
            tmp_path
        )
    )

    assert (
        evidence[
            "parent_evidence_verified"
        ]
        is True
    )

    assert (
        evidence[
            "model_artifact_sha256"
        ]
        == (
            module.EXPECTED_MODEL_ARTIFACT_SHA256
        )
    )

    assert (
        evidence[
            "loader_source_sha256"
        ]
        == (
            module.EXPECTED_LOADER_SOURCE_SHA256
        )
    )


def test_verify_parent_evidence_rejects_validation_state_that_allows_rerun(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _synthetic_parent_files(
        tmp_path,
        monkeypatch,
    )

    freeze_path = (
        tmp_path
        / module.VALIDATION_FREEZE_PATH
    )

    freeze = json.loads(
        freeze_path.read_text(
            encoding="utf-8"
        )
    )

    freeze[
        "decision"
    ][
        "validation_rerun_authorized"
    ] = True

    _write_json(
        freeze_path,
        freeze,
    )

    with pytest.raises(
        module.TestProtocolError,
        match="validation_rerun_authorized",
    ):
        module.verify_parent_evidence(
            tmp_path
        )


def test_verify_parent_evidence_rejects_model_artifact_tamper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _synthetic_parent_files(
        tmp_path,
        monkeypatch,
    )

    (
        tmp_path
        / module.MODEL_ARTIFACT_PATH
    ).write_bytes(
        b"tampered"
    )

    with pytest.raises(
        module.TestProtocolError,
        match="MODEL_ARTIFACT_SHA256_MISMATCH",
    ):
        module.verify_parent_evidence(
            tmp_path
        )


def test_frozen_protocol_write_is_idempotent_and_rejects_mutation(
    tmp_path: Path,
) -> None:
    path = (
        tmp_path
        / "protocol.json"
    )

    parent = {
        "parent_evidence_verified": True,
    }

    document = (
        module.build_protocol_document(
            parent
        )
    )

    module.write_frozen_protocol(
        path,
        document,
    )

    module.write_frozen_protocol(
        path,
        document,
    )

    mutated = json.loads(
        json.dumps(
            document
        )
    )

    mutated[
        "decision"
    ][
        "test_execution_authorized"
    ] = True

    with pytest.raises(
        module.TestProtocolError,
        match="DIFFERENT_CONTENT",
    ):
        module.write_frozen_protocol(
            path,
            mutated,
        )