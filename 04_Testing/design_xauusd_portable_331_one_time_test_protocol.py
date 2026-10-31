from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


ANALYSIS_VERSION = "XAUUSD_PORTABLE_331_ONE_TIME_TEST_PROTOCOL_DESIGN_V1"
STATUS = "ONE_TIME_TEST_PROTOCOL_FROZEN"

OUTPUT_PATH = Path("xauusd_portable_331_one_time_test_protocol.json")
VALIDATION_PROTOCOL_PATH = Path("xauusd_portable_331_one_time_validation_protocol.json")
VALIDATION_RESULT_PATH = Path("xauusd_portable_331_one_time_validation_result.json")
VALIDATION_FREEZE_PATH = Path(
    "xauusd_portable_331_one_time_validation_result_freeze.json"
)
MODEL_ARTIFACT_PATH = Path(
    "xauusd_portable_331_c04_full_train_model.joblib"
)
LOADER_SOURCE_PATH = Path(
    "02_AI/Dataset/portable_331_training_input_loader.py"
)

EXPECTED_DATASET_ID = "portable_cff75b0686383a3ab6f8352b"
EXPECTED_DATASET_SHA256 = (
    "cff75b0686383a3ab6f8352bfcdcd55308b99b7a4c6edbf7d2e7215f6f33dd07"
)
EXPECTED_MANIFEST_SHA256 = (
    "1b8e3599b227c9cbbc6b12f8ab0e275ca4deb4a65839fb626ca90720d59512dc"
)
EXPECTED_FEATURE_COUNT = 331
EXPECTED_FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)
EXPECTED_MODEL_ARTIFACT_SHA256 = (
    "48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769"
)
EXPECTED_LOADER_SOURCE_SHA256 = (
    "49c86c269f2742fec7c6991eaf7a8a9c0466066a3db230a80375ba2e2c33680c"
)
EXPECTED_VALIDATION_PROTOCOL_FINGERPRINT = (
    "ce78180a5f2472c36c74cea2c447307641aa3d5fedfb7a01d9b65260b5a6fcea"
)
EXPECTED_VALIDATION_RESULT_FINGERPRINT = (
    "ea8b482e60f854f58e27f3be387b7bb82f0c16a6cf1a99555b12643aeeca5fa1"
)
EXPECTED_VALIDATION_FREEZE_FINGERPRINT = (
    "521a97b41a86231b049cc65aebfd85ffc7c83ae7141134d6ae1158d112b1468c"
)
EXPECTED_CLASS_ORDER = [-1, 0, 1]

REQUIRED_METRICS = [
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
]

TRAIN_DERIVED_HARD_FLOORS = {
    "directional_macro_f1_short_long": 0.25365034089349603,
    "balanced_accuracy_3class": 0.34040386328178984,
    "macro_f1_3class": 0.24533114425757888,
    "predicted_trade_coverage_min": 0.05,
    "predicted_trade_coverage_max": 0.95,
}


class TestProtocolError(RuntimeError):
    """Raised when the frozen one-time TEST protocol cannot be established safely."""


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(
        _canonical_json(value).encode("utf-8")
    )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise TestProtocolError(
            f"JSON_NOT_UTF8:{path}"
        ) from exc

    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TestProtocolError(
            f"JSON_INVALID:{path}"
        ) from exc

    if not isinstance(value, dict):
        raise TestProtocolError(
            f"JSON_ROOT_NOT_OBJECT:{path}"
        )

    return value


def _contains_scalar(node: Any, expected: Any) -> bool:
    if isinstance(node, Mapping):
        return any(
            _contains_scalar(value, expected)
            for value in node.values()
        )

    if isinstance(node, list):
        return any(
            _contains_scalar(value, expected)
            for value in node
        )

    if isinstance(expected, bool):
        return (
            isinstance(node, bool)
            and node is expected
        )

    return node == expected


def _values_for_key(
    node: Any,
    wanted_key: str,
) -> list[Any]:
    found: list[Any] = []

    if isinstance(node, Mapping):
        for key, value in node.items():
            if key == wanted_key:
                found.append(value)

            found.extend(
                _values_for_key(
                    value,
                    wanted_key,
                )
            )

    elif isinstance(node, list):
        for value in node:
            found.extend(
                _values_for_key(
                    value,
                    wanted_key,
                )
            )

    return found


def _require_key_value(
    document: Mapping[str, Any],
    key: str,
    expected: Any,
) -> None:
    values = _values_for_key(
        document,
        key,
    )

    if isinstance(expected, bool):
        matched = any(
            isinstance(value, bool)
            and value is expected
            for value in values
        )
    else:
        matched = any(
            value == expected
            for value in values
        )

    if not matched:
        raise TestProtocolError(
            "REQUIRED_PARENT_STATE_MISSING:"
            f"{key}={expected!r};"
            f"observed={values!r}"
        )


def _require_scalar(
    document: Mapping[str, Any],
    expected: Any,
    label: str,
) -> None:
    if not _contains_scalar(
        document,
        expected,
    ):
        raise TestProtocolError(
            "REQUIRED_PARENT_IDENTITY_MISSING:"
            f"{label}:{expected}"
        )


def verify_parent_evidence(
    root: Path = Path("."),
) -> dict[str, Any]:
    root = root.resolve()

    validation_protocol_path = (
        root / VALIDATION_PROTOCOL_PATH
    )
    validation_result_path = (
        root / VALIDATION_RESULT_PATH
    )
    validation_freeze_path = (
        root / VALIDATION_FREEZE_PATH
    )
    model_path = (
        root / MODEL_ARTIFACT_PATH
    )
    loader_path = (
        root / LOADER_SOURCE_PATH
    )

    required_paths = [
        validation_protocol_path,
        validation_result_path,
        validation_freeze_path,
        model_path,
        loader_path,
    ]

    missing = [
        str(path)
        for path in required_paths
        if not path.is_file()
    ]

    if missing:
        raise TestProtocolError(
            f"REQUIRED_PARENT_FILE_MISSING:{missing}"
        )

    validation_protocol = _load_json(
        validation_protocol_path
    )
    validation_result = _load_json(
        validation_result_path
    )
    validation_freeze = _load_json(
        validation_freeze_path
    )

    _require_scalar(
        validation_protocol,
        EXPECTED_VALIDATION_PROTOCOL_FINGERPRINT,
        "validation_protocol_fingerprint",
    )

    _require_scalar(
        validation_result,
        EXPECTED_VALIDATION_RESULT_FINGERPRINT,
        "validation_result_fingerprint",
    )

    _require_scalar(
        validation_freeze,
        EXPECTED_VALIDATION_FREEZE_FINGERPRINT,
        "validation_freeze_fingerprint",
    )

    _require_scalar(
        validation_freeze,
        EXPECTED_VALIDATION_RESULT_FINGERPRINT,
        "bound_validation_result_fingerprint",
    )

    _require_key_value(
        validation_freeze,
        "validation_result_frozen",
        True,
    )

    _require_key_value(
        validation_freeze,
        "validation_consumed",
        True,
    )

    _require_key_value(
        validation_freeze,
        "validation_rerun_authorized",
        False,
    )

    _require_key_value(
        validation_freeze,
        "test_runner_implementation_authorized_next",
        True,
    )

    _require_key_value(
        validation_freeze,
        "test_execution_authorized",
        False,
    )

    actual_model_sha256 = _sha256_file(
        model_path
    )

    if (
        actual_model_sha256
        != EXPECTED_MODEL_ARTIFACT_SHA256
    ):
        raise TestProtocolError(
            "MODEL_ARTIFACT_SHA256_MISMATCH:"
            f"expected={EXPECTED_MODEL_ARTIFACT_SHA256};"
            f"actual={actual_model_sha256}"
        )

    actual_loader_sha256 = _sha256_file(
        loader_path
    )

    if (
        actual_loader_sha256
        != EXPECTED_LOADER_SOURCE_SHA256
    ):
        raise TestProtocolError(
            "LOADER_SOURCE_SHA256_MISMATCH:"
            f"expected={EXPECTED_LOADER_SOURCE_SHA256};"
            f"actual={actual_loader_sha256}"
        )

    return {
        "parent_evidence_verified": True,
        "validation_protocol_path": (
            VALIDATION_PROTOCOL_PATH.as_posix()
        ),
        "validation_protocol_fingerprint": (
            EXPECTED_VALIDATION_PROTOCOL_FINGERPRINT
        ),
        "validation_result_path": (
            VALIDATION_RESULT_PATH.as_posix()
        ),
        "validation_result_fingerprint": (
            EXPECTED_VALIDATION_RESULT_FINGERPRINT
        ),
        "validation_freeze_path": (
            VALIDATION_FREEZE_PATH.as_posix()
        ),
        "validation_freeze_fingerprint": (
            EXPECTED_VALIDATION_FREEZE_FINGERPRINT
        ),
        "model_artifact_path": (
            MODEL_ARTIFACT_PATH.as_posix()
        ),
        "model_artifact_sha256": (
            actual_model_sha256
        ),
        "loader_source_path": (
            LOADER_SOURCE_PATH.as_posix()
        ),
        "loader_source_sha256": (
            actual_loader_sha256
        ),
    }


def build_protocol_contract() -> dict[str, Any]:
    return {
        "asset": "XAUUSD",
        "research_lane": (
            "PORTABLE_331_FINAL_HISTORICAL_TEST"
        ),
        "dataset_binding": {
            "dataset_id": (
                EXPECTED_DATASET_ID
            ),
            "dataset_sha256": (
                EXPECTED_DATASET_SHA256
            ),
            "manifest_sha256": (
                EXPECTED_MANIFEST_SHA256
            ),
            "feature_count": (
                EXPECTED_FEATURE_COUNT
            ),
            "feature_columns_sha256": (
                EXPECTED_FEATURE_COLUMNS_SHA256
            ),
        },
        "model_binding": {
            "candidate_id": (
                "C04_FLAT_EXTRA_TREES_CONSTRAINED"
            ),
            "model_artifact_path": (
                MODEL_ARTIFACT_PATH.as_posix()
            ),
            "model_artifact_sha256": (
                EXPECTED_MODEL_ARTIFACT_SHA256
            ),
            "probability_class_order": (
                EXPECTED_CLASS_ORDER
            ),
            "prediction_rule": (
                "ARGMAX_OVER_MODEL_CLASSES_"
                "NO_THRESHOLD_TUNING"
            ),
        },
        "parent_validation_binding": {
            "validation_protocol_fingerprint": (
                EXPECTED_VALIDATION_PROTOCOL_FINGERPRINT
            ),
            "validation_result_fingerprint": (
                EXPECTED_VALIDATION_RESULT_FINGERPRINT
            ),
            "validation_freeze_fingerprint": (
                EXPECTED_VALIDATION_FREEZE_FINGERPRINT
            ),
            "validation_consumed": True,
            "validation_reread_authorized": False,
        },
        "loader_binding": {
            "source_path": (
                LOADER_SOURCE_PATH.as_posix()
            ),
            "source_sha256": (
                EXPECTED_LOADER_SOURCE_SHA256
            ),
            (
                "original_public_test_accessors_"
                "must_remain_fail_closed"
            ): True,
        },
        "test_acceptance_policy": {
            "threshold_origin": (
                "TRAIN_ONLY_FROZEN_PRE_VALIDATION"
            ),
            (
                "validation_metrics_used_to_set_or_"
                "raise_test_thresholds"
            ): False,
            "required_metrics": (
                REQUIRED_METRICS
            ),
            "all_required_metrics_must_be_finite": (
                True
            ),
            "required_target_classes_exact": (
                EXPECTED_CLASS_ORDER
            ),
            (
                "directional_macro_f1_short_long_min"
            ): TRAIN_DERIVED_HARD_FLOORS[
                "directional_macro_f1_short_long"
            ],
            "balanced_accuracy_3class_min": (
                TRAIN_DERIVED_HARD_FLOORS[
                    "balanced_accuracy_3class"
                ]
            ),
            "macro_f1_3class_min": (
                TRAIN_DERIVED_HARD_FLOORS[
                    "macro_f1_3class"
                ]
            ),
            "short_recall_must_be_positive": True,
            "long_recall_must_be_positive": True,
            "predicted_trade_coverage_min": (
                TRAIN_DERIVED_HARD_FLOORS[
                    "predicted_trade_coverage_min"
                ]
            ),
            "predicted_trade_coverage_max": (
                TRAIN_DERIVED_HARD_FLOORS[
                    "predicted_trade_coverage_max"
                ]
            ),
            "report_only_metrics": [
                "log_loss_3class",
                "multiclass_brier",
            ],
            (
                "no_acceptance_relaxation_after_"
                "test_read"
            ): True,
        },
        "one_time_test_semantics": {
            (
                "dedicated_persistent_test_ledger_"
                "required_before_first_test_value_read"
            ): True,
            "read_initiation_is_consumption_boundary": (
                True
            ),
            (
                "pre_read_technical_failure_retriable_"
                "only_if_zero_test_values_were_read"
            ): True,
            "post_read_technical_failure_consumes_test": (
                True
            ),
            (
                "second_performance_driven_test_read_"
                "authorized"
            ): False,
            "test_source_must_be_bounded_to_test_rows_only": (
                True
            ),
            "validation_value_reread_authorized": (
                False
            ),
        },
        "scientific_policy": {
            "model_refit_allowed": False,
            "candidate_change_allowed": False,
            "feature_change_allowed": False,
            "target_change_allowed": False,
            "threshold_search_allowed": False,
            "probability_calibration_allowed": False,
            "validation_peeking_allowed": False,
            (
                "test_peeking_before_one_shot_"
                "execution_allowed"
            ): False,
            (
                "test_result_may_tune_current_"
                "frozen_lineage"
            ): False,
            "shadow_authorized": False,
            "live_authorized": False,
        },
        "required_next_implementation": {
            "test_core_and_ledger": True,
            "bounded_test_source": True,
            "one_shot_test_runner": True,
            "synthetic_tests_before_real_test_read": (
                True
            ),
            "dry_preflight_before_real_test_read": (
                True
            ),
            (
                "preflight_fingerprint_must_be_"
                "frozen_before_real_test_read"
            ): True,
        },
    }


def build_protocol_document(
    parent_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        parent_evidence.get(
            "parent_evidence_verified"
        )
        is not True
    ):
        raise TestProtocolError(
            "PARENT_EVIDENCE_NOT_VERIFIED"
        )

    contract = build_protocol_contract()
    protocol_fingerprint = _sha256_json(
        contract
    )

    return {
        "analysis_version": ANALYSIS_VERSION,
        "valid": True,
        "status": STATUS,
        "protocol_fingerprint": (
            protocol_fingerprint
        ),
        "contract": contract,
        "parent_evidence": (
            dict(parent_evidence)
        ),
        "decision": {
            "test_protocol_frozen": True,
            "validation_consumed": True,
            "validation_rerun_authorized": False,
            (
                "test_runner_implementation_"
                "authorized_next"
            ): True,
            "test_execution_authorized": False,
            "test_values_accessed": False,
            "model_refit_authorized": False,
            "candidate_change_authorized": False,
            "threshold_change_authorized": False,
            (
                "probability_calibration_"
                "authorized"
            ): False,
            "shadow_authorized": False,
            "live_authorized": False,
            "next_action": (
                "IMPLEMENT_AND_SYNTHETICALLY_TEST_"
                "ONE_SHOT_PORTABLE_TEST_CORE_"
                "LEDGER_SOURCE_AND_RUNNER_BEFORE_"
                "FIRST_AND_ONLY_TEST_READ"
            ),
        },
    }


def write_frozen_protocol(
    path: Path,
    document: Mapping[str, Any],
) -> None:
    serialized = (
        json.dumps(
            document,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    )

    if path.exists():
        existing = _load_json(path)

        if (
            _canonical_json(existing)
            != _canonical_json(document)
        ):
            raise TestProtocolError(
                "FROZEN_TEST_PROTOCOL_ALREADY_EXISTS_"
                f"WITH_DIFFERENT_CONTENT:{path}"
            )

        return

    path.write_text(
        serialized,
        encoding="utf-8",
    )


def main() -> int:
    parent_evidence = verify_parent_evidence(
        Path(".")
    )

    document = build_protocol_document(
        parent_evidence
    )

    write_frozen_protocol(
        OUTPUT_PATH,
        document,
    )

    print(
        f"status={document['status']}"
    )
    print(
        "protocol_fingerprint="
        f"{document['protocol_fingerprint']}"
    )
    print(
        f"output={OUTPUT_PATH}"
    )
    print(
        "test_execution_authorized=false"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())