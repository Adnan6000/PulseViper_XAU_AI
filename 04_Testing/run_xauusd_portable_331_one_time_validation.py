#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

import joblib


ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_ONE_TIME_"
    "VALIDATION_RUNNER_V1"
)

REPO_ROOT = Path(__file__).resolve().parents[1]

CORE_PATH = (
    REPO_ROOT
    / "04_Testing"
    / "xauusd_portable_331_one_time_validation_core.py"
)

SOURCE_PATH = (
    REPO_ROOT
    / "04_Testing"
    / "xauusd_portable_331_authorized_validation_source.py"
)

MODEL_VERIFIER_PATH = (
    REPO_ROOT
    / "04_Testing"
    / "verify_xauusd_portable_331_c04_full_train_model_artifact.py"
)

PROTOCOL_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_validation_protocol.json"
)

CORE_ATTESTATION_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_validation_core_attestation.json"
)

SOURCE_ATTESTATION_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_authorized_validation_source_attestation.json"
)

MODEL_VERIFICATION_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_c04_full_train_model_artifact_verification.json"
)

MODEL_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_c04_full_train_model.joblib"
)

DEFAULT_PREFLIGHT_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_validation_preflight.json"
)

DEFAULT_LEDGER_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_validation_access_ledger.json"
)

DEFAULT_RESULT_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_validation_result.json"
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


class OneTimeValidationRunnerError(
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
        raise OneTimeValidationRunnerError(
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
        raise OneTimeValidationRunnerError(
            f"Invalid JSON: {path}"
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        raise OneTimeValidationRunnerError(
            f"Expected JSON object: {path}"
        )

    return payload


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


def _load_module(
    path: Path,
    name: str,
) -> ModuleType:
    if not path.is_file():
        raise OneTimeValidationRunnerError(
            f"Required Python module missing: {path}"
        )

    spec = importlib.util.spec_from_file_location(
        name,
        path,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise OneTimeValidationRunnerError(
            f"Cannot create import spec: {path}"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    sys.modules[
        name
    ] = module

    try:
        spec.loader.exec_module(
            module
        )

    except Exception:
        sys.modules.pop(
            name,
            None,
        )
        raise

    return module


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
        raise OneTimeValidationRunnerError(
            f"Required mapping missing: {key}"
        )

    return value


def _validate_ledger_state_before_execution(
    *,
    core: ModuleType,
    ledger_path: Path,
) -> dict[str, Any]:
    if not ledger_path.exists():
        return {
            "state": "ABSENT",
            "execution_recovery_allowed": True,
            "holdout_consumed_for_rerun_policy": False,
            "validation_read_attempt_count": 0,
        }

    ledger = core.ValidationAccessLedger(
        path=ledger_path,
        protocol_fingerprint_sha256=(
            EXPECTED_PROTOCOL_FINGERPRINT
        ),
        model_artifact_sha256=(
            EXPECTED_MODEL_ARTIFACT_SHA256
        ),
    )

    payload = ledger.load()

    status = payload.get(
        "status"
    )

    read_attempt_count = int(
        payload.get(
            "validation_read_attempt_count",
            0,
        )
    )

    consumed = bool(
        payload.get(
            "holdout_consumed_for_rerun_policy",
            False,
        )
    )

    if (
        status
        == "PRE_READ_TECHNICAL_FAILURE"
        and read_attempt_count
        == 0
        and consumed
        is False
    ):
        return {
            "state": (
                "PRE_READ_TECHNICAL_FAILURE_RECOVERABLE"
            ),
            "execution_recovery_allowed": True,
            "holdout_consumed_for_rerun_policy": False,
            "validation_read_attempt_count": 0,
        }

    return {
        "state": str(
            status
        ),
        "execution_recovery_allowed": False,
        "holdout_consumed_for_rerun_policy": (
            consumed
        ),
        "validation_read_attempt_count": (
            read_attempt_count
        ),
    }


def _validate_attestation_chain(
    *,
    ledger_path: Path,
) -> dict[str, Any]:
    core = _load_module(
        CORE_PATH,
        "xauusd_validation_runner_core",
    )

    source = _load_module(
        SOURCE_PATH,
        "xauusd_validation_runner_source",
    )

    verifier = _load_module(
        MODEL_VERIFIER_PATH,
        "xauusd_validation_runner_model_verifier",
    )

    protocol = _read_json_auto(
        PROTOCOL_PATH
    )

    core.validate_frozen_validation_protocol(
        protocol
    )

    stored_core = _read_json_auto(
        CORE_ATTESTATION_PATH
    )

    rebuilt_core = (
        core.build_implementation_attestation()
    )

    if (
        stored_core
        != rebuilt_core
    ):
        raise OneTimeValidationRunnerError(
            "Stored validation-core attestation "
            "does not match current implementation."
        )

    if (
        stored_core.get(
            "valid"
        )
        is not True
    ):
        raise OneTimeValidationRunnerError(
            "Validation-core attestation is invalid."
        )

    core_decision = _required_mapping(
        stored_core,
        "decision",
    )

    if (
        core_decision.get(
            "real_validation_execution_authorized"
        )
        is not False
    ):
        raise OneTimeValidationRunnerError(
            "Core implementation artifact must not "
            "already authorize real validation."
        )

    if (
        core_decision.get(
            "test_access_authorized"
        )
        is not False
    ):
        raise OneTimeValidationRunnerError(
            "Core implementation must keep TEST blocked."
        )

    stored_source = _read_json_auto(
        SOURCE_ATTESTATION_PATH
    )

    rebuilt_source = (
        source.build_source_attestation()
    )

    if (
        stored_source
        != rebuilt_source
    ):
        raise OneTimeValidationRunnerError(
            "Stored validation-source attestation "
            "does not match current implementation."
        )

    if (
        stored_source.get(
            "valid"
        )
        is not True
    ):
        raise OneTimeValidationRunnerError(
            "Validation-source attestation is invalid."
        )

    source_decision = _required_mapping(
        stored_source,
        "decision",
    )

    required_source_decision = {
        "validation_source_implementation_confirmed": True,
        "real_validation_source_executed": False,
        "real_validation_values_loaded": False,
        "real_validation_metrics_computed": False,
        "real_validation_execution_authorized": False,
        "test_access_authorized": False,
        "shadow_authorized": False,
        "live_authorized": False,
    }

    for (
        key,
        expected,
    ) in required_source_decision.items():
        if (
            source_decision.get(
                key
            )
            != expected
        ):
            raise OneTimeValidationRunnerError(
                "Validation-source decision mismatch: "
                f"{key}"
            )

    loader_contract = _required_mapping(
        stored_source,
        "loader_contract",
    )

    if (
        loader_contract.get(
            "loader_source_sha256"
        )
        != EXPECTED_LOADER_SOURCE_SHA256
    ):
        raise OneTimeValidationRunnerError(
            "Frozen portable loader SHA256 mismatch."
        )

    source_contract = _required_mapping(
        stored_source,
        "source_contract",
    )

    required_source_contract = {
        "value_parser_stops_at_validation_end": True,
        "feature_order_from_frozen_manifest": True,
        "feature_columns_sha256": (
            EXPECTED_FEATURE_COLUMNS_SHA256
        ),
        "public_loader_holdout_accessors_modified": False,
        "test_value_access_path_present": False,
    }

    for (
        key,
        expected,
    ) in required_source_contract.items():
        if (
            source_contract.get(
                key
            )
            != expected
        ):
            raise OneTimeValidationRunnerError(
                "Validation-source contract mismatch: "
                f"{key}"
            )

    stored_model_verification = (
        _read_json_auto(
            MODEL_VERIFICATION_PATH
        )
    )

    rebuilt_model_verification = (
        verifier.build_verification()
    )

    if (
        stored_model_verification
        != rebuilt_model_verification
    ):
        raise OneTimeValidationRunnerError(
            "Stored model verification does not "
            "match current frozen artifact."
        )

    if (
        stored_model_verification.get(
            "valid"
        )
        is not True
    ):
        raise OneTimeValidationRunnerError(
            "Model verification is invalid."
        )

    model_decision = _required_mapping(
        stored_model_verification,
        "decision",
    )

    required_model_decision = {
        "model_artifact_verified": True,
        "model_artifact_cryptographically_frozen": True,
        "full_train_fit_verified": True,
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
    ) in required_model_decision.items():
        if (
            model_decision.get(
                key
            )
            != expected
        ):
            raise OneTimeValidationRunnerError(
                "Model-verification decision mismatch: "
                f"{key}"
            )

    verification_record_fingerprint = (
        _required_mapping(
            stored_model_verification,
            "verification_record_fingerprint",
        )
    )

    if (
        verification_record_fingerprint.get(
            "sha256"
        )
        != EXPECTED_MODEL_VERIFICATION_RECORD_SHA256
    ):
        raise OneTimeValidationRunnerError(
            "Model verification record fingerprint mismatch."
        )

    artifact_validation = _required_mapping(
        stored_model_verification,
        "artifact_validation",
    )

    if (
        artifact_validation.get(
            "model_artifact_sha256"
        )
        != EXPECTED_MODEL_ARTIFACT_SHA256
    ):
        raise OneTimeValidationRunnerError(
            "Frozen model artifact SHA256 mismatch."
        )

    ledger_state = (
        _validate_ledger_state_before_execution(
            core=core,
            ledger_path=ledger_path,
        )
    )

    return {
        "core_module": core,
        "source_module": source,
        "model_verifier_module": verifier,
        "protocol": protocol,
        "core_attestation": stored_core,
        "source_attestation": stored_source,
        "model_verification": (
            stored_model_verification
        ),
        "ledger_state": (
            ledger_state
        ),
    }


def build_preflight(
    *,
    ledger_path: Path = DEFAULT_LEDGER_PATH,
    result_path: Path = DEFAULT_RESULT_PATH,
) -> dict[str, Any]:
    chain = _validate_attestation_chain(
        ledger_path=ledger_path
    )

    ledger_state = chain[
        "ledger_state"
    ]

    execution_recovery_allowed = (
        ledger_state[
            "execution_recovery_allowed"
        ]
        is True
    )

    preflight_record = {
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
        "core_attestation_canonical_sha256": (
            _canonical_sha256(
                chain[
                    "core_attestation"
                ]
            )
        ),
        "source_attestation_canonical_sha256": (
            _canonical_sha256(
                chain[
                    "source_attestation"
                ]
            )
        ),
        "model_verification_canonical_sha256": (
            _canonical_sha256(
                chain[
                    "model_verification"
                ]
            )
        ),
        "ledger_filename": (
            ledger_path.name
        ),
        "result_filename": (
            result_path.name
        ),
        "ledger_state": (
            ledger_state[
                "state"
            ]
        ),
        "ledger_execution_recovery_allowed": (
            execution_recovery_allowed
        ),
        "validation_read_attempt_count_before_execution": (
            ledger_state[
                "validation_read_attempt_count"
            ]
        ),
        "holdout_consumed_before_execution": (
            ledger_state[
                "holdout_consumed_for_rerun_policy"
            ]
        ),
        "prediction_rule": (
            "ARGMAX_FROZEN_MODEL_PROBABILITIES"
        ),
        "model_refit_allowed": False,
        "threshold_search_allowed": False,
        "probability_calibration_allowed": False,
        "candidate_change_allowed": False,
        "test_access_during_validation_allowed": False,
    }

    preflight_fingerprint = (
        _canonical_sha256(
            preflight_record
        )
    )

    return {
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "valid": True,
        "research_scope": (
            "FINAL_DRY_PREFLIGHT_BEFORE_FIRST_"
            "AND_ONLY_REAL_PORTABLE_VALIDATION_READ"
        ),
        "preflight_record": (
            preflight_record
        ),
        "preflight_fingerprint": {
            "canonicalization": (
                "JSON_SORT_KEYS_COMPACT_UTF8_SHA256"
            ),
            "sha256": (
                preflight_fingerprint
            ),
        },
        "decision": {
            "status": (
                "ONE_TIME_VALIDATION_DRY_PREFLIGHT_READY"
                if execution_recovery_allowed
                else "ONE_TIME_VALIDATION_EXECUTION_BLOCKED"
            ),
            "dry_preflight_completed": True,
            "real_validation_executed": False,
            "real_validation_values_loaded": False,
            "real_validation_metrics_computed": False,
            "real_validation_execution_authorized_next": (
                execution_recovery_allowed
            ),
            "test_access_authorized": False,
            "shadow_authorized": False,
            "live_authorized": False,
            "next_action": (
                "FREEZE_THIS_PREFLIGHT_FINGERPRINT_"
                "THEN_EXECUTE_EXACTLY_ONE_REAL_"
                "VALIDATION_RUN"
                if execution_recovery_allowed
                else "STOP_VALIDATION_EXECUTION_"
                "BECAUSE_LEDGER_IS_ALREADY_CONSUMED"
            ),
        },
        "scientific_policy": {
            "dataset_structural_read_performed": False,
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
            "model_artifact_modified": False,
            "execution_integration_modified": False,
            "risk_engine_modified": False,
            "orders_sent": False,
            "shadow_authorized": False,
            "live_authorized": False,
        },
    }


def validate_stored_preflight(
    *,
    preflight_path: Path,
    expected_fingerprint: str,
    ledger_path: Path,
    result_path: Path,
) -> dict[str, Any]:
    stored = _read_json_auto(
        preflight_path
    )

    if (
        stored.get(
            "analysis_version"
        )
        != ANALYSIS_VERSION
    ):
        raise OneTimeValidationRunnerError(
            "Stored preflight analysis version mismatch."
        )

    if (
        stored.get(
            "valid"
        )
        is not True
    ):
        raise OneTimeValidationRunnerError(
            "Stored preflight must be valid=true."
        )

    fingerprint = _required_mapping(
        stored,
        "preflight_fingerprint",
    )

    declared = fingerprint.get(
        "sha256"
    )

    if (
        declared
        != expected_fingerprint
    ):
        raise OneTimeValidationRunnerError(
            "Expected preflight fingerprint does not "
            "match stored preflight."
        )

    preflight_record = _required_mapping(
        stored,
        "preflight_record",
    )

    if (
        _canonical_sha256(
            preflight_record
        )
        != expected_fingerprint
    ):
        raise OneTimeValidationRunnerError(
            "Stored preflight content fingerprint mismatch."
        )

    decision = _required_mapping(
        stored,
        "decision",
    )

    if (
        decision.get(
            "real_validation_execution_authorized_next"
        )
        is not True
    ):
        raise OneTimeValidationRunnerError(
            "Stored preflight does not authorize "
            "one-time validation execution."
        )

    current = build_preflight(
        ledger_path=ledger_path,
        result_path=result_path,
    )

    current_fingerprint = (
        current[
            "preflight_fingerprint"
        ][
            "sha256"
        ]
    )

    if (
        current_fingerprint
        != expected_fingerprint
    ):
        raise OneTimeValidationRunnerError(
            "Current provenance/ledger state differs "
            "from frozen dry preflight."
        )

    if (
        current[
            "preflight_record"
        ]
        != preflight_record
    ):
        raise OneTimeValidationRunnerError(
            "Current preflight record differs "
            "from frozen preflight."
        )

    return stored


def execute_one_time_validation(
    *,
    expected_preflight_fingerprint: str,
    canonical_root: Path = REPO_ROOT,
    preflight_path: Path = DEFAULT_PREFLIGHT_PATH,
    ledger_path: Path = DEFAULT_LEDGER_PATH,
    result_path: Path = DEFAULT_RESULT_PATH,
) -> dict[str, Any]:
    validate_stored_preflight(
        preflight_path=preflight_path,
        expected_fingerprint=(
            expected_preflight_fingerprint
        ),
        ledger_path=ledger_path,
        result_path=result_path,
    )

    core = _load_module(
        CORE_PATH,
        "xauusd_validation_execution_core",
    )

    source_module = _load_module(
        SOURCE_PATH,
        "xauusd_validation_execution_source",
    )

    protocol = _read_json_auto(
        PROTOCOL_PATH
    )

    model = joblib.load(
        MODEL_PATH
    )

    adapter = (
        source_module
        .AuthorizedPortableValidationSource(
            canonical_root,
            core_module=core,
        )
    )

    ledger = core.ValidationAccessLedger(
        path=ledger_path,
        protocol_fingerprint_sha256=(
            EXPECTED_PROTOCOL_FINGERPRINT
        ),
        model_artifact_sha256=(
            EXPECTED_MODEL_ARTIFACT_SHA256
        ),
    )

    core_result = (
        core.run_one_time_validation_from_source(
            protocol_payload=protocol,
            model=model,
            source=adapter.load,
            ledger=ledger,
        )
    )

    source_evidence = (
        adapter.last_evidence
    )

    if not isinstance(
        source_evidence,
        Mapping,
    ):
        raise OneTimeValidationRunnerError(
            "Validation source evidence missing "
            "after one-time execution."
        )

    validation_result = _required_mapping(
        core_result,
        "validation_result",
    )

    gate_result = _required_mapping(
        validation_result,
        "gate_result",
    )

    accepted = (
        gate_result.get(
            "accepted"
        )
        is True
    )

    result_record = {
        "preflight_fingerprint_sha256": (
            expected_preflight_fingerprint
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
        "validation_row_count": (
            validation_result.get(
                "row_count"
            )
        ),
        "validation_feature_count": (
            validation_result.get(
                "feature_count"
            )
        ),
        "validation_metrics": (
            validation_result.get(
                "metrics"
            )
        ),
        "validation_gate_result": (
            gate_result
        ),
        "source_evidence": dict(
            source_evidence
        ),
        "ledger_final_status": (
            core_result[
                "ledger"
            ].get(
                "status"
            )
        ),
        "validation_accepted": (
            accepted
        ),
    }

    result_fingerprint = (
        _canonical_sha256(
            result_record
        )
    )

    report = {
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "valid": True,
        "research_scope": (
            "FIRST_AND_ONLY_REAL_UNTOUCHED_"
            "PORTABLE_VALIDATION_EVALUATION_"
            "OF_VERIFIED_FROZEN_C04"
        ),
        "result_record": (
            result_record
        ),
        "result_fingerprint": {
            "canonicalization": (
                "JSON_SORT_KEYS_COMPACT_UTF8_SHA256"
            ),
            "sha256": (
                result_fingerprint
            ),
        },
        "core_result": (
            core_result
        ),
        "decision": {
            "status": (
                "ONE_TIME_VALIDATION_ACCEPTED"
                if accepted
                else "ONE_TIME_VALIDATION_REJECTED"
            ),
            "validation_consumed": True,
            "validation_accepted": (
                accepted
            ),
            "validation_rerun_authorized": False,
            "test_access_authorized_next": (
                accepted
            ),
            "test_access_performed": False,
            "model_refit_authorized": False,
            "threshold_change_authorized": False,
            "probability_calibration_authorized": False,
            "candidate_change_authorized": False,
            "shadow_authorized": False,
            "live_authorized": False,
            "next_action": (
                "FREEZE_VALIDATION_RESULT_AND_"
                "IMPLEMENT_ONE_SHOT_TEST_RUNNER_"
                "BEFORE_ANY_TEST_READ"
                if accepted
                else "STOP_MODEL_RESEARCH_FOR_THIS_"
                "FROZEN_CANDIDATE_NO_TEST_NO_"
                "SHADOW_NO_LIVE"
            ),
        },
        "scientific_policy": {
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
        },
    }

    _write_json_atomic(
        result_path,
        report,
    )

    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-preflight or explicitly execute "
            "the first and only real portable "
            "VALIDATION evaluation."
        )
    )

    parser.add_argument(
        "--execute-one-time-validation",
        action="store_true",
    )

    parser.add_argument(
        "--expected-preflight-fingerprint",
        type=str,
        default=None,
    )

    parser.add_argument(
        "--canonical-root",
        type=Path,
        default=REPO_ROOT,
    )

    parser.add_argument(
        "--preflight-output",
        type=Path,
        default=DEFAULT_PREFLIGHT_PATH,
    )

    parser.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER_PATH,
    )

    parser.add_argument(
        "--result-output",
        type=Path,
        default=DEFAULT_RESULT_PATH,
    )

    args = parser.parse_args()

    if not args.execute_one_time_validation:
        try:
            report = build_preflight(
                ledger_path=args.ledger,
                result_path=args.result_output,
            )

            _write_json_atomic(
                args.preflight_output,
                report,
            )

        except Exception as exc:
            failure = {
                "analysis_version": (
                    ANALYSIS_VERSION
                ),
                "valid": False,
                "reason": (
                    "ONE_TIME_VALIDATION_DRY_"
                    "PREFLIGHT_FAILED"
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
                    "live_authorized": False,
                },
            }

            _write_json_atomic(
                args.preflight_output,
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
                    "preflight_fingerprint_sha256": (
                        report[
                            "preflight_fingerprint"
                        ][
                            "sha256"
                        ]
                    ),
                    "preflight_record": (
                        report[
                            "preflight_record"
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

    if not args.expected_preflight_fingerprint:
        print(
            json.dumps(
                {
                    "analysis_version": (
                        ANALYSIS_VERSION
                    ),
                    "valid": False,
                    "reason": (
                        "EXPECTED_PREFLIGHT_FINGERPRINT_REQUIRED"
                    ),
                    "validation_executed": False,
                    "test_access_authorized": False,
                    "live_authorized": False,
                },
                indent=2,
                sort_keys=True,
            )
        )

        return 2

    try:
        report = execute_one_time_validation(
            expected_preflight_fingerprint=(
                args.expected_preflight_fingerprint
            ),
            canonical_root=(
                args.canonical_root
            ),
            preflight_path=(
                args.preflight_output
            ),
            ledger_path=(
                args.ledger
            ),
            result_path=(
                args.result_output
            ),
        )

    except Exception as exc:
        ledger_state = None

        if args.ledger.exists():
            try:
                ledger_state = (
                    _read_json_auto(
                        args.ledger
                    )
                )

            except Exception:
                ledger_state = {
                    "unreadable": True,
                }

        failure = {
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "valid": False,
            "reason": (
                "ONE_TIME_REAL_VALIDATION_EXECUTION_FAILED"
            ),
            "error_type": (
                type(
                    exc
                ).__name__
            ),
            "error": str(
                exc
            ),
            "ledger_state": (
                ledger_state
            ),
            "scientific_policy": {
                "test_access_authorized": False,
                "shadow_authorized": False,
                "live_authorized": False,
            },
        }

        _write_json_atomic(
            args.result_output,
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
                "result_fingerprint_sha256": (
                    report[
                        "result_fingerprint"
                    ][
                        "sha256"
                    ]
                ),
                "validation_metrics": (
                    report[
                        "result_record"
                    ][
                        "validation_metrics"
                    ]
                ),
                "validation_gate_result": (
                    report[
                        "result_record"
                    ][
                        "validation_gate_result"
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