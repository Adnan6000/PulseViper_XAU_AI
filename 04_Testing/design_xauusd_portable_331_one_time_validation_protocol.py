#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_ONE_TIME_"
    "VALIDATION_PROTOCOL_DESIGN_V1"
)

CONTRACT_VERSION = (
    "XAUUSD_PORTABLE_331_ONE_TIME_"
    "VALIDATION_PROTOCOL_V1"
)

REPO_ROOT = Path(__file__).resolve().parents[1]

REGISTRY_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_train_model_candidate_registry_design.json"
)

WALK_FORWARD_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_train_model_candidate_walk_forward_evaluation.json"
)

MODEL_VERIFICATION_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_c04_full_train_model_artifact_verification.json"
)

DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_validation_protocol.json"
)


EXPECTED_WINNER_ID = (
    "C04_FLAT_EXTRA_TREES_CONSTRAINED"
)

EXPECTED_REGISTRY_SHA256 = (
    "b8088bb34ce8940f7de5946fbb9b0fd20f40d7cc93a76b76fd7975591f00066c"
)

EXPECTED_RESEARCH_PROTOCOL_SHA256 = (
    "69e51e1b249b9da68cbf6f6778a8ae10f9f33f7082a07e5073a1ba731fa1640d"
)

EXPECTED_WALK_FORWARD_SHA256 = (
    "15516174ba6f3d8932425b20dcde33db25c040e0901c86af39796f97847ac7ed"
)

EXPECTED_MODEL_ARTIFACT_SHA256 = (
    "48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769"
)

EXPECTED_MODEL_RECORD_SHA256 = (
    "bd6d76f92d3c6274bed756683f4263b9cce9a3f0e5ffbb8bd4ba3fcbe6f6ff74"
)

EXPECTED_MODEL_VERIFICATION_RECORD_SHA256 = (
    "a2759a429b90998a7d24c8b217e570813e36dcf43df5de6cf98daf875b8678ef"
)

EXPECTED_WINNER_CONFIG_SHA256 = (
    "f1b11c6f91561f2eba1bd56195e2239e9598b1906c88f11ada67eac6cdeb09e3"
)

EXPECTED_DATASET_ID = (
    "portable_cff75b0686383a3ab6f8352b"
)

EXPECTED_FEATURE_COUNT = 331

EXPECTED_CLASS_ORDER = (
    -1,
    0,
    1,
)

EXPECTED_REQUIRED_METRICS = (
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


class ValidationProtocolDesignError(
    RuntimeError
):
    pass


def _canonical_sha256(
    value: Any,
) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        encoded
    ).hexdigest()


def _read_json_auto(
    path: Path,
) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationProtocolDesignError(
            f"Required JSON missing: {path}"
        )

    raw = path.read_bytes()

    if raw.startswith(
        (
            b"\xff\xfe",
            b"\xfe\xff",
        )
    ):
        text = raw.decode(
            "utf-16"
        )

    elif raw.startswith(
        b"\xef\xbb\xbf"
    ):
        text = raw.decode(
            "utf-8-sig"
        )

    else:
        text = raw.decode(
            "utf-8"
        )

    try:
        payload = json.loads(
            text
        )

    except json.JSONDecodeError as exc:
        raise ValidationProtocolDesignError(
            f"Invalid JSON: {path}"
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        raise ValidationProtocolDesignError(
            f"Expected JSON object: {path}"
        )

    return payload


def _required_mapping(
    mapping: Mapping[str, Any],
    key: str,
) -> Mapping[str, Any]:
    value = mapping.get(
        key
    )

    if not isinstance(
        value,
        Mapping,
    ):
        raise ValidationProtocolDesignError(
            f"Required mapping missing: {key}"
        )

    return value


def _required_list(
    mapping: Mapping[str, Any],
    key: str,
) -> list[Any]:
    value = mapping.get(
        key
    )

    if not isinstance(
        value,
        list,
    ):
        raise ValidationProtocolDesignError(
            f"Required list missing: {key}"
        )

    return value


def _validate_model_verification(
    payload: Mapping[str, Any],
) -> None:
    if (
        payload.get(
            "analysis_version"
        )
        != (
            "XAUUSD_PORTABLE_331_C04_FULL_TRAIN_"
            "MODEL_ARTIFACT_VERIFICATION_V1"
        )
    ):
        raise ValidationProtocolDesignError(
            "Unexpected model verification version."
        )

    if (
        payload.get(
            "valid"
        )
        is not True
    ):
        raise ValidationProtocolDesignError(
            "Model verification must be valid=true."
        )

    artifact_validation = (
        _required_mapping(
            payload,
            "artifact_validation",
        )
    )

    if (
        artifact_validation.get(
            "model_artifact_sha256"
        )
        != EXPECTED_MODEL_ARTIFACT_SHA256
    ):
        raise ValidationProtocolDesignError(
            "Frozen model SHA256 mismatch."
        )

    if (
        artifact_validation.get(
            "artifact_reload_confirmed"
        )
        is not True
    ):
        raise ValidationProtocolDesignError(
            "Frozen model reload was not confirmed."
        )

    if (
        artifact_validation.get(
            "class_order"
        )
        != list(
            EXPECTED_CLASS_ORDER
        )
    ):
        raise ValidationProtocolDesignError(
            "Frozen model class order mismatch."
        )

    if (
        artifact_validation.get(
            "n_features_in"
        )
        != EXPECTED_FEATURE_COUNT
    ):
        raise ValidationProtocolDesignError(
            "Frozen model feature count mismatch."
        )

    verification_fingerprint = (
        _required_mapping(
            payload,
            "verification_record_fingerprint",
        )
    )

    if (
        verification_fingerprint.get(
            "sha256"
        )
        != EXPECTED_MODEL_VERIFICATION_RECORD_SHA256
    ):
        raise ValidationProtocolDesignError(
            "Model verification fingerprint mismatch."
        )

    verification_record = (
        _required_mapping(
            payload,
            "verification_record",
        )
    )

    if (
        _canonical_sha256(
            verification_record
        )
        != EXPECTED_MODEL_VERIFICATION_RECORD_SHA256
    ):
        raise ValidationProtocolDesignError(
            "Model verification record content mismatch."
        )

    expected_record = {
        "candidate_id": (
            EXPECTED_WINNER_ID
        ),
        "winner_config_fingerprint_sha256": (
            EXPECTED_WINNER_CONFIG_SHA256
        ),
        "model_record_fingerprint_sha256": (
            EXPECTED_MODEL_RECORD_SHA256
        ),
        "model_artifact_sha256": (
            EXPECTED_MODEL_ARTIFACT_SHA256
        ),
        "candidate_registry_fingerprint_sha256": (
            EXPECTED_REGISTRY_SHA256
        ),
        "research_protocol_fingerprint_sha256": (
            EXPECTED_RESEARCH_PROTOCOL_SHA256
        ),
        "walk_forward_evaluation_fingerprint_sha256": (
            EXPECTED_WALK_FORWARD_SHA256
        ),
    }

    for (
        key,
        expected,
    ) in expected_record.items():
        if (
            verification_record.get(
                key
            )
            != expected
        ):
            raise ValidationProtocolDesignError(
                "Model verification provenance mismatch: "
                f"{key}"
            )

    decision = _required_mapping(
        payload,
        "decision",
    )

    expected_decision = {
        "full_train_fit_verified": True,
        "model_artifact_verified": True,
        "model_artifact_cryptographically_frozen": True,
        "winner_candidate_id": (
            EXPECTED_WINNER_ID
        ),
        "validation_accessed_in_this_gate": False,
        "validation_access_authorized_next": True,
        "test_accessed_in_this_gate": False,
        "test_access_authorized": False,
        "shadow_authorized": False,
        "live_authorized": False,
    }

    for (
        key,
        expected,
    ) in expected_decision.items():
        if (
            decision.get(
                key
            )
            != expected
        ):
            raise ValidationProtocolDesignError(
                "Model verification decision mismatch: "
                f"{key}"
            )


def _validate_registry(
    payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    if (
        payload.get(
            "valid"
        )
        is not True
    ):
        raise ValidationProtocolDesignError(
            "Candidate registry must be valid=true."
        )

    fingerprint = _required_mapping(
        payload,
        "registry_fingerprint",
    )

    if (
        fingerprint.get(
            "sha256"
        )
        != EXPECTED_REGISTRY_SHA256
    ):
        raise ValidationProtocolDesignError(
            "Candidate registry fingerprint mismatch."
        )

    contract = _required_mapping(
        payload,
        "contract",
    )

    if (
        _canonical_sha256(
            contract
        )
        != EXPECTED_REGISTRY_SHA256
    ):
        raise ValidationProtocolDesignError(
            "Candidate registry content mismatch."
        )

    eligibility = _required_mapping(
        contract,
        "eligibility_gate",
    )

    if (
        eligibility.get(
            "minimum_predicted_trade_coverage_each_fold"
        )
        != 0.05
    ):
        raise ValidationProtocolDesignError(
            "Frozen minimum trade coverage mismatch."
        )

    if (
        eligibility.get(
            "maximum_predicted_trade_coverage_each_fold"
        )
        != 0.95
    ):
        raise ValidationProtocolDesignError(
            "Frozen maximum trade coverage mismatch."
        )

    if (
        eligibility.get(
            "short_recall_must_be_positive_every_fold"
        )
        is not True
    ):
        raise ValidationProtocolDesignError(
            "Frozen SHORT recall rule mismatch."
        )

    if (
        eligibility.get(
            "long_recall_must_be_positive_every_fold"
        )
        is not True
    ):
        raise ValidationProtocolDesignError(
            "Frozen LONG recall rule mismatch."
        )

    return eligibility


def _validate_walk_forward(
    payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    if (
        payload.get(
            "valid"
        )
        is not True
    ):
        raise ValidationProtocolDesignError(
            "Walk-forward result must be valid=true."
        )

    if (
        payload.get(
            "analysis_version"
        )
        != (
            "XAUUSD_PORTABLE_331_TRAIN_CANDIDATE_"
            "WALK_FORWARD_EVALUATION_V1"
        )
    ):
        raise ValidationProtocolDesignError(
            "Unexpected walk-forward version."
        )

    artifact_identity = _required_mapping(
        payload,
        "artifact_identity",
    )

    if (
        artifact_identity.get(
            "dataset_id"
        )
        != EXPECTED_DATASET_ID
    ):
        raise ValidationProtocolDesignError(
            "Walk-forward dataset identity mismatch."
        )

    if (
        artifact_identity.get(
            "candidate_registry_fingerprint_sha256"
        )
        != EXPECTED_REGISTRY_SHA256
    ):
        raise ValidationProtocolDesignError(
            "Walk-forward registry fingerprint mismatch."
        )

    if (
        artifact_identity.get(
            "research_protocol_fingerprint_sha256"
        )
        != EXPECTED_RESEARCH_PROTOCOL_SHA256
    ):
        raise ValidationProtocolDesignError(
            "Walk-forward research protocol mismatch."
        )

    fingerprint = _required_mapping(
        payload,
        "evaluation_fingerprint",
    )

    if (
        fingerprint.get(
            "sha256"
        )
        != EXPECTED_WALK_FORWARD_SHA256
    ):
        raise ValidationProtocolDesignError(
            "Walk-forward evaluation fingerprint mismatch."
        )

    evaluation = _required_mapping(
        payload,
        "evaluation",
    )

    if (
        _canonical_sha256(
            evaluation
        )
        != EXPECTED_WALK_FORWARD_SHA256
    ):
        raise ValidationProtocolDesignError(
            "Walk-forward evaluation content mismatch."
        )

    if (
        tuple(
            evaluation.get(
                "required_fold_metrics",
                (),
            )
        )
        != EXPECTED_REQUIRED_METRICS
    ):
        raise ValidationProtocolDesignError(
            "Required metric contract mismatch."
        )

    selection = _required_mapping(
        evaluation,
        "selection",
    )

    if (
        selection.get(
            "status"
        )
        != "WINNER_SELECTED_TRAIN_INTERNAL_ONLY"
    ):
        raise ValidationProtocolDesignError(
            "TRAIN-internal winner missing."
        )

    if (
        selection.get(
            "winner_candidate_id"
        )
        != EXPECTED_WINNER_ID
    ):
        raise ValidationProtocolDesignError(
            "Unexpected TRAIN-internal winner."
        )

    reports = _required_list(
        evaluation,
        "candidate_reports",
    )

    winner_report = None

    for report in reports:
        if (
            isinstance(
                report,
                Mapping,
            )
            and report.get(
                "candidate_id"
            )
            == EXPECTED_WINNER_ID
        ):
            winner_report = report
            break

    if not isinstance(
        winner_report,
        Mapping,
    ):
        raise ValidationProtocolDesignError(
            "C04 winner report missing."
        )

    if (
        winner_report.get(
            "eligible"
        )
        is not True
    ):
        raise ValidationProtocolDesignError(
            "C04 winner is not eligible."
        )

    if (
        winner_report.get(
            "status"
        )
        != "ELIGIBLE"
    ):
        raise ValidationProtocolDesignError(
            "C04 winner status mismatch."
        )

    return winner_report


def _derive_acceptance_gate(
    winner_report: Mapping[str, Any],
    eligibility: Mapping[str, Any],
) -> dict[str, Any]:
    summary = _required_mapping(
        winner_report,
        "summary",
    )

    fold_reports = _required_list(
        winner_report,
        "fold_reports",
    )

    if len(
        fold_reports
    ) != 4:
        raise ValidationProtocolDesignError(
            "Winner must have exactly four TRAIN folds."
        )

    directional_floor = float(
        summary[
            "worst_fold_directional_macro_f1_short_long"
        ]
    )

    balanced_floor = float(
        summary[
            "worst_fold_balanced_accuracy_3class"
        ]
    )

    macro_f1_values: list[float] = []

    for fold_report in fold_reports:
        if not isinstance(
            fold_report,
            Mapping,
        ):
            raise ValidationProtocolDesignError(
                "Invalid winner fold report."
            )

        metrics = _required_mapping(
            fold_report,
            "metrics",
        )

        macro_f1_values.append(
            float(
                metrics[
                    "macro_f1_3class"
                ]
            )
        )

    macro_f1_floor = min(
        macro_f1_values
    )

    return {
        "gate_semantics": (
            "ALL_HARD_REQUIREMENTS_MUST_PASS"
        ),
        "all_required_metrics_must_be_finite": True,
        "required_target_classes_present": list(
            EXPECTED_CLASS_ORDER
        ),
        "minimum_directional_macro_f1_short_long": (
            directional_floor
        ),
        "directional_floor_source": (
            "C04_WORST_FROZEN_TRAIN_WALK_FORWARD_FOLD"
        ),
        "minimum_balanced_accuracy_3class": (
            balanced_floor
        ),
        "balanced_accuracy_floor_source": (
            "C04_WORST_FROZEN_TRAIN_WALK_FORWARD_FOLD"
        ),
        "minimum_macro_f1_3class": (
            macro_f1_floor
        ),
        "macro_f1_floor_source": (
            "C04_WORST_FROZEN_TRAIN_WALK_FORWARD_FOLD"
        ),
        "short_recall_must_be_positive": True,
        "long_recall_must_be_positive": True,
        "minimum_predicted_trade_coverage": float(
            eligibility[
                "minimum_predicted_trade_coverage_each_fold"
            ]
        ),
        "maximum_predicted_trade_coverage": float(
            eligibility[
                "maximum_predicted_trade_coverage_each_fold"
            ]
        ),
        "log_loss_3class_is_hard_gate": False,
        "multiclass_brier_is_hard_gate": False,
        "probability_metrics_role": (
            "REPORT_ONLY_NO_POST_HOC_CALIBRATION"
        ),
    }


def build_protocol() -> dict[str, Any]:
    model_verification = (
        _read_json_auto(
            MODEL_VERIFICATION_PATH
        )
    )

    _validate_model_verification(
        model_verification
    )

    registry = _read_json_auto(
        REGISTRY_PATH
    )

    eligibility = _validate_registry(
        registry
    )

    walk_forward = _read_json_auto(
        WALK_FORWARD_PATH
    )

    winner_report = (
        _validate_walk_forward(
            walk_forward
        )
    )

    acceptance_gate = (
        _derive_acceptance_gate(
            winner_report,
            eligibility,
        )
    )

    contract = {
        "contract_version": (
            CONTRACT_VERSION
        ),
        "research_scope": (
            "PREDECLARE_ONE_TIME_UNTOUCHED_"
            "VALIDATION_ACCEPT_REJECT_RULES_"
            "BEFORE_ANY_VALIDATION_VALUE_ACCESS"
        ),
        "frozen_model": {
            "candidate_id": (
                EXPECTED_WINNER_ID
            ),
            "winner_config_fingerprint_sha256": (
                EXPECTED_WINNER_CONFIG_SHA256
            ),
            "model_artifact_sha256": (
                EXPECTED_MODEL_ARTIFACT_SHA256
            ),
            "model_record_fingerprint_sha256": (
                EXPECTED_MODEL_RECORD_SHA256
            ),
            "model_verification_record_fingerprint_sha256": (
                EXPECTED_MODEL_VERIFICATION_RECORD_SHA256
            ),
            "feature_count": (
                EXPECTED_FEATURE_COUNT
            ),
            "probability_class_order": list(
                EXPECTED_CLASS_ORDER
            ),
        },
        "required_validation_metrics": list(
            EXPECTED_REQUIRED_METRICS
        ),
        "acceptance_gate": (
            acceptance_gate
        ),
        "prediction_policy": {
            "prediction_rule": (
                "ARGMAX_FROZEN_MODEL_PROBABILITIES"
            ),
            "class_order": list(
                EXPECTED_CLASS_ORDER
            ),
            "threshold_search_allowed": False,
            "threshold_change_allowed": False,
            "probability_calibration_allowed": False,
            "post_hoc_class_bias_allowed": False,
            "candidate_change_allowed": False,
            "hyperparameter_change_allowed": False,
            "model_refit_allowed": False,
            "feature_selection_allowed": False,
        },
        "one_time_access_protocol": {
            "validation_feature_access_authorized": True,
            "validation_target_access_authorized": True,
            "validation_access_attempt_limit": 1,
            "access_ledger_must_be_created_before_first_validation_value_read": True,
            "validation_metrics_may_be_computed_once": True,
            "performance_driven_validation_rerun_allowed": False,
            "technical_failure_before_any_validation_value_read": (
                "SAFE_TO_FIX_INFRASTRUCTURE_BEFORE_CONSUMPTION"
            ),
            "technical_failure_after_any_validation_value_read": (
                "MARK_VALIDATION_CONSUMED_AND_FAIL_CLOSED"
            ),
            "test_access_during_validation_run_allowed": False,
        },
        "decision_protocol": {
            "all_hard_acceptance_requirements_pass": (
                "VALIDATION_ACCEPTED_AUTHORIZE_ONE_SHOT_TEST_NEXT"
            ),
            "any_hard_acceptance_requirement_fails": (
                "VALIDATION_REJECTED_STOP_NO_TEST"
            ),
            "soft_pass_allowed": False,
            "manual_override_allowed": False,
            "results_driven_gate_change_allowed": False,
            "validation_pass_does_not_authorize_shadow": True,
            "validation_pass_does_not_authorize_live": True,
        },
        "holdout_boundary": {
            "portable_validation_is_current_holdout": True,
            "portable_test_remains_untouched_final_holdout": True,
            "portable_test_feature_access_authorized": False,
            "portable_test_target_access_authorized": False,
            "portable_test_metrics_authorized": False,
            "shadow_authorized": False,
            "live_authorized": False,
        },
        "parent_fingerprints": {
            "candidate_registry_fingerprint_sha256": (
                EXPECTED_REGISTRY_SHA256
            ),
            "research_protocol_fingerprint_sha256": (
                EXPECTED_RESEARCH_PROTOCOL_SHA256
            ),
            "walk_forward_evaluation_fingerprint_sha256": (
                EXPECTED_WALK_FORWARD_SHA256
            ),
            "model_artifact_sha256": (
                EXPECTED_MODEL_ARTIFACT_SHA256
            ),
            "model_verification_record_fingerprint_sha256": (
                EXPECTED_MODEL_VERIFICATION_RECORD_SHA256
            ),
        },
    }

    contract_sha256 = (
        _canonical_sha256(
            contract
        )
    )

    return {
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "valid": True,
        "research_scope": (
            "DESIGN_ONLY_ONE_TIME_UNTOUCHED_"
            "VALIDATION_PROTOCOL_WITHOUT_"
            "VALIDATION_OR_TEST_VALUE_ACCESS"
        ),
        "contract": (
            contract
        ),
        "contract_fingerprint": {
            "canonicalization": (
                "JSON_SORT_KEYS_COMPACT_UTF8_SHA256"
            ),
            "version": (
                "XAUUSD_PORTABLE_331_ONE_TIME_"
                "VALIDATION_PROTOCOL_FINGERPRINT_V1"
            ),
            "sha256": (
                contract_sha256
            ),
        },
        "decision": {
            "status": (
                "ONE_TIME_VALIDATION_PROTOCOL_FROZEN"
            ),
            "winner_candidate_id": (
                EXPECTED_WINNER_ID
            ),
            "validation_protocol_frozen": True,
            "validation_values_loaded": False,
            "validation_metrics_computed": False,
            "validation_execution_implementation_authorized_next": True,
            "validation_execution_authorized": False,
            "test_access_authorized": False,
            "shadow_authorized": False,
            "live_authorized": False,
            "next_action": (
                "IMPLEMENT_AND_SYNTHETICALLY_TEST_"
                "ONE_TIME_VALIDATION_ACCESS_LEDGER_"
                "AND_FROZEN_MODEL_EVALUATION_RUNNER_"
                "BEFORE_FIRST_REAL_VALIDATION_READ"
            ),
        },
        "scientific_policy": {
            "train_feature_values_loaded": False,
            "train_target_values_loaded": False,
            "portable_validation_feature_values_loaded": False,
            "portable_validation_target_values_loaded": False,
            "portable_validation_metrics_computed": False,
            "portable_test_feature_values_loaded": False,
            "portable_test_target_values_loaded": False,
            "portable_test_metrics_computed": False,
            "model_fit_performed": False,
            "model_refit_performed": False,
            "threshold_search_performed": False,
            "probability_calibration_performed": False,
            "feature_selection_performed": False,
            "candidate_registry_changed": False,
            "winner_changed": False,
            "model_artifact_modified": False,
            "execution_integration_modified": False,
            "risk_engine_modified": False,
            "orders_sent": False,
            "shadow_authorized": False,
            "live_authorized": False,
        },
    }


def _write_json_utf8_atomic(
    path: Path,
    payload: Mapping[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix
        + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary.replace(
        path
    )


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )

    args = parser.parse_args()

    try:
        report = build_protocol()

        _write_json_utf8_atomic(
            args.output,
            report,
        )

    except Exception as exc:
        failure = {
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "valid": False,
            "reason": (
                "ONE_TIME_VALIDATION_PROTOCOL_DESIGN_FAILED"
            ),
            "error_type": (
                type(
                    exc
                ).__name__
            ),
            "error": str(
                exc
            ),
            "scientific_policy": {
                "portable_validation_feature_values_loaded": False,
                "portable_validation_target_values_loaded": False,
                "portable_test_feature_values_loaded": False,
                "portable_test_target_values_loaded": False,
                "model_fit_performed": False,
                "live_authorized": False,
            },
        }

        _write_json_utf8_atomic(
            args.output,
            failure,
        )

        print(
            json.dumps(
                failure,
                indent=2,
                sort_keys=True,
            )
        )

        return 1

    print(
        json.dumps(
            {
                "analysis_version": (
                    report[
                        "analysis_version"
                    ]
                ),
                "valid": True,
                "contract_fingerprint_sha256": (
                    report[
                        "contract_fingerprint"
                    ][
                        "sha256"
                    ]
                ),
                "acceptance_gate": (
                    report[
                        "contract"
                    ][
                        "acceptance_gate"
                    ]
                ),
                "decision": (
                    report[
                        "decision"
                    ]
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )