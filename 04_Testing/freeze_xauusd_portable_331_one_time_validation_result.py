#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping


ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_ONE_TIME_"
    "VALIDATION_RESULT_FREEZE_V1"
)

REPO_ROOT = Path(__file__).resolve().parents[1]

RESULT_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_validation_result.json"
)

LEDGER_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_validation_access_ledger.json"
)

PREFLIGHT_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_validation_preflight.json"
)

DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_validation_result_freeze.json"
)

EXPECTED_RUNNER_ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_ONE_TIME_VALIDATION_RUNNER_V1"
)

EXPECTED_PREFLIGHT_FINGERPRINT = (
    "5ee6d0948d93f83f7969662e103066f1a09d7b081883290aba104b52f0038f41"
)

EXPECTED_RESULT_FINGERPRINT = (
    "ea8b482e60f854f58e27f3be387b7bb82f0c16a6cf1a99555b12643aeeca5fa1"
)

EXPECTED_PROTOCOL_FINGERPRINT = (
    "ce78180a5f2472c36c74cea2c447307641aa3d5fedfb7a01d9b65260b5a6fcea"
)

EXPECTED_MODEL_ARTIFACT_SHA256 = (
    "48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769"
)

EXPECTED_MODEL_VERIFICATION_RECORD_SHA256 = (
    "a2759a429b90998a7d24c8b217e570813e36dcf43df5de6cf98daf875b8678ef"
)

EXPECTED_LOADER_SOURCE_SHA256 = (
    "49c86c269f2742fec7c6991eaf7a8a9c0466066a3db230a80375ba2e2c33680c"
)

EXPECTED_FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

EXPECTED_WINNER_ID = (
    "C04_FLAT_EXTRA_TREES_CONSTRAINED"
)

EXPECTED_FEATURE_COUNT = 331

EXPECTED_REQUIRED_METRICS = {
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
}

EXPECTED_HARD_CHECKS = {
    "all_required_metrics_finite",
    "required_target_classes_present",
    "directional_macro_f1_floor_pass",
    "balanced_accuracy_floor_pass",
    "macro_f1_floor_pass",
    "short_recall_positive",
    "long_recall_positive",
    "minimum_trade_coverage_pass",
    "maximum_trade_coverage_pass",
}


class ValidationResultFreezeError(
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
        raise ValidationResultFreezeError(
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
        raise ValidationResultFreezeError(
            f"Invalid JSON: {path}"
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        raise ValidationResultFreezeError(
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
        raise ValidationResultFreezeError(
            f"Required mapping missing: {key}"
        )

    return value


def _validate_preflight(
    payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    if (
        payload.get(
            "analysis_version"
        )
        != EXPECTED_RUNNER_ANALYSIS_VERSION
    ):
        raise ValidationResultFreezeError(
            "Preflight analysis version mismatch."
        )

    if (
        payload.get(
            "valid"
        )
        is not True
    ):
        raise ValidationResultFreezeError(
            "Preflight must be valid=true."
        )

    fingerprint = _required_mapping(
        payload,
        "preflight_fingerprint",
    )

    if (
        fingerprint.get(
            "sha256"
        )
        != EXPECTED_PREFLIGHT_FINGERPRINT
    ):
        raise ValidationResultFreezeError(
            "Preflight fingerprint mismatch."
        )

    record = _required_mapping(
        payload,
        "preflight_record",
    )

    if (
        _canonical_sha256(
            record
        )
        != EXPECTED_PREFLIGHT_FINGERPRINT
    ):
        raise ValidationResultFreezeError(
            "Preflight content fingerprint mismatch."
        )

    expected_record = {
        "winner_candidate_id": (
            EXPECTED_WINNER_ID
        ),
        "validation_protocol_fingerprint_sha256": (
            EXPECTED_PROTOCOL_FINGERPRINT
        ),
        "model_artifact_sha256": (
            EXPECTED_MODEL_ARTIFACT_SHA256
        ),
        "model_verification_record_fingerprint_sha256": (
            EXPECTED_MODEL_VERIFICATION_RECORD_SHA256
        ),
        "portable_loader_source_sha256": (
            EXPECTED_LOADER_SOURCE_SHA256
        ),
        "feature_columns_sha256": (
            EXPECTED_FEATURE_COLUMNS_SHA256
        ),
        "ledger_state": "ABSENT",
        "ledger_execution_recovery_allowed": True,
        "validation_read_attempt_count_before_execution": 0,
        "holdout_consumed_before_execution": False,
        "prediction_rule": (
            "ARGMAX_FROZEN_MODEL_PROBABILITIES"
        ),
        "model_refit_allowed": False,
        "threshold_search_allowed": False,
        "probability_calibration_allowed": False,
        "candidate_change_allowed": False,
        "test_access_during_validation_allowed": False,
    }

    for (
        key,
        expected,
    ) in expected_record.items():
        if (
            record.get(
                key
            )
            != expected
        ):
            raise ValidationResultFreezeError(
                "Preflight record mismatch: "
                f"{key}"
            )

    decision = _required_mapping(
        payload,
        "decision",
    )

    if (
        decision.get(
            "dry_preflight_completed"
        )
        is not True
    ):
        raise ValidationResultFreezeError(
            "Dry preflight was not completed."
        )

    if (
        decision.get(
            "real_validation_execution_authorized_next"
        )
        is not True
    ):
        raise ValidationResultFreezeError(
            "Dry preflight did not authorize validation."
        )

    if (
        decision.get(
            "real_validation_executed"
        )
        is not False
    ):
        raise ValidationResultFreezeError(
            "Preflight must precede real validation."
        )

    if (
        decision.get(
            "test_access_authorized"
        )
        is not False
    ):
        raise ValidationResultFreezeError(
            "TEST must have remained blocked at preflight."
        )

    return record


def _validate_result(
    payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    if (
        payload.get(
            "analysis_version"
        )
        != EXPECTED_RUNNER_ANALYSIS_VERSION
    ):
        raise ValidationResultFreezeError(
            "Validation result analysis version mismatch."
        )

    if (
        payload.get(
            "valid"
        )
        is not True
    ):
        raise ValidationResultFreezeError(
            "Validation result must be valid=true."
        )

    fingerprint = _required_mapping(
        payload,
        "result_fingerprint",
    )

    if (
        fingerprint.get(
            "canonicalization"
        )
        != "JSON_SORT_KEYS_COMPACT_UTF8_SHA256"
    ):
        raise ValidationResultFreezeError(
            "Result fingerprint canonicalization mismatch."
        )

    if (
        fingerprint.get(
            "sha256"
        )
        != EXPECTED_RESULT_FINGERPRINT
    ):
        raise ValidationResultFreezeError(
            "Validation result fingerprint mismatch."
        )

    record = _required_mapping(
        payload,
        "result_record",
    )

    if (
        _canonical_sha256(
            record
        )
        != EXPECTED_RESULT_FINGERPRINT
    ):
        raise ValidationResultFreezeError(
            "Validation result content fingerprint mismatch."
        )

    expected_identity = {
        "preflight_fingerprint_sha256": (
            EXPECTED_PREFLIGHT_FINGERPRINT
        ),
        "winner_candidate_id": (
            EXPECTED_WINNER_ID
        ),
        "validation_protocol_fingerprint_sha256": (
            EXPECTED_PROTOCOL_FINGERPRINT
        ),
        "model_artifact_sha256": (
            EXPECTED_MODEL_ARTIFACT_SHA256
        ),
        "model_verification_record_fingerprint_sha256": (
            EXPECTED_MODEL_VERIFICATION_RECORD_SHA256
        ),
        "portable_loader_source_sha256": (
            EXPECTED_LOADER_SOURCE_SHA256
        ),
        "feature_columns_sha256": (
            EXPECTED_FEATURE_COLUMNS_SHA256
        ),
        "validation_feature_count": (
            EXPECTED_FEATURE_COUNT
        ),
        "ledger_final_status": (
            "VALIDATION_COMPLETE_ACCEPTED"
        ),
        "validation_accepted": True,
    }

    for (
        key,
        expected,
    ) in expected_identity.items():
        if (
            record.get(
                key
            )
            != expected
        ):
            raise ValidationResultFreezeError(
                "Validation result identity mismatch: "
                f"{key}"
            )

    row_count = record.get(
        "validation_row_count"
    )

    if (
        not isinstance(
            row_count,
            int,
        )
        or row_count
        <= 0
    ):
        raise ValidationResultFreezeError(
            "Validation row count is invalid."
        )

    metrics = _required_mapping(
        record,
        "validation_metrics",
    )

    if (
        set(
            metrics.keys()
        )
        != EXPECTED_REQUIRED_METRICS
    ):
        raise ValidationResultFreezeError(
            "Validation metric contract mismatch."
        )

    for (
        key,
        value,
    ) in metrics.items():
        try:
            numeric = float(
                value
            )

        except Exception as exc:
            raise ValidationResultFreezeError(
                f"Validation metric is not numeric: {key}"
            ) from exc

        if not math.isfinite(
            numeric
        ):
            raise ValidationResultFreezeError(
                f"Validation metric is not finite: {key}"
            )

    gate = _required_mapping(
        record,
        "validation_gate_result",
    )

    if (
        gate.get(
            "accepted"
        )
        is not True
    ):
        raise ValidationResultFreezeError(
            "Frozen validation gate did not accept result."
        )

    hard_checks = _required_mapping(
        gate,
        "hard_checks",
    )

    if (
        set(
            hard_checks.keys()
        )
        != EXPECTED_HARD_CHECKS
    ):
        raise ValidationResultFreezeError(
            "Validation hard-check contract mismatch."
        )

    for (
        key,
        value,
    ) in hard_checks.items():
        if (
            value
            is not True
        ):
            raise ValidationResultFreezeError(
                "Validation hard check failed: "
                f"{key}"
            )

    probability_metrics = _required_mapping(
        gate,
        "probability_metrics",
    )

    if (
        probability_metrics.get(
            "hard_gate"
        )
        is not False
    ):
        raise ValidationResultFreezeError(
            "Probability metrics must remain report-only."
        )

    if (
        probability_metrics.get(
            "role"
        )
        != "REPORT_ONLY_NO_POST_HOC_CALIBRATION"
    ):
        raise ValidationResultFreezeError(
            "Probability metric role mismatch."
        )

    source_evidence = _required_mapping(
        record,
        "source_evidence",
    )

    read_policy = _required_mapping(
        source_evidence,
        "read_policy",
    )

    required_read_policy = {
        "value_read_split": (
            "VALIDATION"
        ),
        "parser_stops_before_test_value_rows": True,
        "test_feature_values_loaded": False,
        "test_target_values_loaded": False,
        "train_feature_values_loaded": False,
        "train_target_values_loaded": False,
    }

    for (
        key,
        expected,
    ) in required_read_policy.items():
        if (
            read_policy.get(
                key
            )
            != expected
        ):
            raise ValidationResultFreezeError(
                "Validation source read-policy mismatch: "
                f"{key}"
            )

    decision = _required_mapping(
        payload,
        "decision",
    )

    expected_decision = {
        "status": (
            "ONE_TIME_VALIDATION_ACCEPTED"
        ),
        "validation_consumed": True,
        "validation_accepted": True,
        "validation_rerun_authorized": False,
        "test_access_authorized_next": True,
        "test_access_performed": False,
        "model_refit_authorized": False,
        "threshold_change_authorized": False,
        "probability_calibration_authorized": False,
        "candidate_change_authorized": False,
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
            raise ValidationResultFreezeError(
                "Validation decision mismatch: "
                f"{key}"
            )

    policy = _required_mapping(
        payload,
        "scientific_policy",
    )

    expected_policy = {
        "portable_validation_consumed": True,
        "portable_validation_rerun_allowed": False,
        "portable_test_feature_values_loaded": False,
        "portable_test_target_values_loaded": False,
        "portable_test_metrics_computed": False,
        "model_refit_performed": False,
        "threshold_search_performed": False,
        "probability_calibration_performed": False,
        "feature_selection_performed": False,
        "candidate_changed": False,
        "model_artifact_modified": False,
        "execution_integration_modified": False,
        "risk_engine_modified": False,
        "orders_sent": False,
        "shadow_authorized": False,
        "live_authorized": False,
    }

    for (
        key,
        expected,
    ) in expected_policy.items():
        if (
            policy.get(
                key
            )
            != expected
        ):
            raise ValidationResultFreezeError(
                "Validation scientific-policy mismatch: "
                f"{key}"
            )

    core_result = _required_mapping(
        payload,
        "core_result",
    )

    core_validation_result = _required_mapping(
        core_result,
        "validation_result",
    )

    if (
        core_validation_result.get(
            "metrics"
        )
        != metrics
    ):
        raise ValidationResultFreezeError(
            "Core validation metrics differ "
            "from result record."
        )

    if (
        core_validation_result.get(
            "gate_result"
        )
        != gate
    ):
        raise ValidationResultFreezeError(
            "Core gate result differs "
            "from result record."
        )

    return record


def _validate_ledger(
    payload: Mapping[str, Any],
    result_payload: Mapping[str, Any],
) -> None:
    expected = {
        "protocol_fingerprint_sha256": (
            EXPECTED_PROTOCOL_FINGERPRINT
        ),
        "model_artifact_sha256": (
            EXPECTED_MODEL_ARTIFACT_SHA256
        ),
        "validation_read_attempt_count": 1,
        "holdout_consumed_for_rerun_policy": True,
        "validation_values_loaded": True,
        "validation_metrics_computed": True,
        "test_values_accessed": False,
        "validation_accepted": True,
        "test_access_authorized_next": True,
        "status": (
            "VALIDATION_COMPLETE_ACCEPTED"
        ),
    }

    for (
        key,
        expected_value,
    ) in expected.items():
        if (
            payload.get(
                key
            )
            != expected_value
        ):
            raise ValidationResultFreezeError(
                "Validation ledger mismatch: "
                f"{key}"
            )

    result_record = _required_mapping(
        result_payload,
        "result_record",
    )

    if (
        payload.get(
            "validation_row_count"
        )
        != result_record.get(
            "validation_row_count"
        )
    ):
        raise ValidationResultFreezeError(
            "Ledger/result validation row-count mismatch."
        )

    if (
        payload.get(
            "validation_feature_count"
        )
        != EXPECTED_FEATURE_COUNT
    ):
        raise ValidationResultFreezeError(
            "Ledger validation feature-count mismatch."
        )

    core_result = _required_mapping(
        result_payload,
        "core_result",
    )

    embedded_ledger = _required_mapping(
        core_result,
        "ledger",
    )

    if (
        dict(
            embedded_ledger
        )
        != dict(
            payload
        )
    ):
        raise ValidationResultFreezeError(
            "External ledger differs from "
            "ledger embedded in validation result."
        )


def build_validation_result_freeze() -> dict[str, Any]:
    preflight = _read_json_auto(
        PREFLIGHT_PATH
    )

    _validate_preflight(
        preflight
    )

    result = _read_json_auto(
        RESULT_PATH
    )

    result_record = _validate_result(
        result
    )

    ledger = _read_json_auto(
        LEDGER_PATH
    )

    _validate_ledger(
        ledger,
        result,
    )

    metrics = _required_mapping(
        result_record,
        "validation_metrics",
    )

    gate = _required_mapping(
        result_record,
        "validation_gate_result",
    )

    freeze_record = {
        "winner_candidate_id": (
            EXPECTED_WINNER_ID
        ),
        "preflight_fingerprint_sha256": (
            EXPECTED_PREFLIGHT_FINGERPRINT
        ),
        "validation_result_fingerprint_sha256": (
            EXPECTED_RESULT_FINGERPRINT
        ),
        "validation_protocol_fingerprint_sha256": (
            EXPECTED_PROTOCOL_FINGERPRINT
        ),
        "model_artifact_sha256": (
            EXPECTED_MODEL_ARTIFACT_SHA256
        ),
        "model_verification_record_fingerprint_sha256": (
            EXPECTED_MODEL_VERIFICATION_RECORD_SHA256
        ),
        "portable_loader_source_sha256": (
            EXPECTED_LOADER_SOURCE_SHA256
        ),
        "feature_columns_sha256": (
            EXPECTED_FEATURE_COLUMNS_SHA256
        ),
        "ledger_canonical_sha256": (
            _canonical_sha256(
                ledger
            )
        ),
        "validation_row_count": (
            result_record[
                "validation_row_count"
            ]
        ),
        "validation_feature_count": (
            result_record[
                "validation_feature_count"
            ]
        ),
        "validation_metrics": dict(
            metrics
        ),
        "validation_gate_result": dict(
            gate
        ),
        "validation_consumed": True,
        "validation_rerun_authorized": False,
        "test_access_authorized_next": True,
        "test_access_performed": False,
    }

    freeze_fingerprint = (
        _canonical_sha256(
            freeze_record
        )
    )

    return {
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "valid": True,
        "research_scope": (
            "FREEZE_CONSUMED_ONE_TIME_"
            "VALIDATION_RESULT_AND_LEDGER_"
            "BEFORE_ANY_PORTABLE_TEST_READ"
        ),
        "freeze_record": (
            freeze_record
        ),
        "freeze_fingerprint": {
            "canonicalization": (
                "JSON_SORT_KEYS_COMPACT_UTF8_SHA256"
            ),
            "sha256": (
                freeze_fingerprint
            ),
        },
        "decision": {
            "status": (
                "ONE_TIME_VALIDATION_RESULT_FROZEN_ACCEPTED"
            ),
            "winner_candidate_id": (
                EXPECTED_WINNER_ID
            ),
            "validation_result_frozen": True,
            "validation_accepted": True,
            "validation_consumed": True,
            "validation_rerun_authorized": False,
            "test_runner_implementation_authorized_next": True,
            "test_execution_authorized": False,
            "test_access_performed": False,
            "model_refit_authorized": False,
            "threshold_change_authorized": False,
            "probability_calibration_authorized": False,
            "candidate_change_authorized": False,
            "shadow_authorized": False,
            "live_authorized": False,
            "next_action": (
                "IMPLEMENT_AND_SYNTHETICALLY_TEST_"
                "ONE_SHOT_PORTABLE_TEST_RUNNER_"
                "BEFORE_FIRST_AND_ONLY_TEST_READ"
            ),
        },
        "scientific_policy": {
            "dataset_rows_loaded_in_this_gate": False,
            "portable_validation_feature_values_loaded_in_this_gate": False,
            "portable_validation_target_values_loaded_in_this_gate": False,
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


def _write_json_atomic(
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
        report = (
            build_validation_result_freeze()
        )

        _write_json_atomic(
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
                "ONE_TIME_VALIDATION_RESULT_FREEZE_FAILED"
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
                "portable_test_feature_values_loaded": False,
                "portable_test_target_values_loaded": False,
                "test_execution_authorized": False,
                "shadow_authorized": False,
                "live_authorized": False,
            },
        }

        _write_json_atomic(
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
                "freeze_fingerprint_sha256": (
                    report[
                        "freeze_fingerprint"
                    ][
                        "sha256"
                    ]
                ),
                "validation_metrics": (
                    report[
                        "freeze_record"
                    ][
                        "validation_metrics"
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