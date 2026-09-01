#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import joblib
import numpy as np


ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_C04_FULL_TRAIN_"
    "MODEL_ARTIFACT_VERIFICATION_V1"
)

REPO_ROOT = Path(__file__).resolve().parents[1]

FULL_TRAIN_FIT_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_c04_full_train_model_fit.json"
)

WINNER_FREEZE_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_train_internal_winner_freeze.json"
)

DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_c04_full_train_model_artifact_verification.json"
)

EXPECTED_FIT_ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_C04_FULL_TRAIN_MODEL_FIT_V1"
)

EXPECTED_WINNER_FREEZE_ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_INTERNAL_WINNER_FREEZE_V1"
)

EXPECTED_WINNER_ID = (
    "C04_FLAT_EXTRA_TREES_CONSTRAINED"
)

EXPECTED_WINNER_CONFIG_SHA256 = (
    "f1b11c6f91561f2eba1bd56195e2239e9598b1906c88f11ada67eac6cdeb09e3"
)

EXPECTED_MODEL_ARTIFACT_SHA256 = (
    "48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769"
)

EXPECTED_MODEL_RECORD_SHA256 = (
    "bd6d76f92d3c6274bed756683f4263b9cce9a3f0e5ffbb8bd4ba3fcbe6f6ff74"
)

EXPECTED_DATASET_ID = (
    "portable_cff75b0686383a3ab6f8352b"
)

EXPECTED_DATASET_SHA256 = (
    "cff75b0686383a3ab6f8352bfcdcd55308b99b7a4c6edbf7d2e7215f6f33dd07"
)

EXPECTED_MANIFEST_SHA256 = (
    "1b8e3599b227c9cbbc6b12f8ab0e275ca4deb4a65839fb626ca90720d59512dc"
)

EXPECTED_TRAIN_INPUT_SHA256 = (
    "9ffb72759499cfc202e88cfdbd61b42cee5b5c7cbb7db5870470453caa5ed2c5"
)

EXPECTED_TRAIN_TARGET_SHA256 = (
    "bc063a790e70cdbc931b2170ccfef883634b40ee7336a529a32bda0eaf0babe3"
)

EXPECTED_FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

EXPECTED_REGISTRY_SHA256 = (
    "b8088bb34ce8940f7de5946fbb9b0fd20f40d7cc93a76b76fd7975591f00066c"
)

EXPECTED_PROTOCOL_SHA256 = (
    "69e51e1b249b9da68cbf6f6778a8ae10f9f33f7082a07e5073a1ba731fa1640d"
)

EXPECTED_WALK_FORWARD_SHA256 = (
    "15516174ba6f3d8932425b20dcde33db25c040e0901c86af39796f97847ac7ed"
)

EXPECTED_ROWS = 69966
EXPECTED_FEATURES = 331
EXPECTED_CLASS_ORDER = (-1, 0, 1)

EXPECTED_ESTIMATOR_PARAMS = {
    "bootstrap": False,
    "class_weight": "balanced",
    "max_depth": 10,
    "max_features": 0.35,
    "min_samples_leaf": 25,
    "n_estimators": 500,
    "n_jobs": -1,
    "random_state": 271828,
}


class ModelArtifactVerificationError(
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
    ).encode("utf-8")

    return hashlib.sha256(
        encoded
    ).hexdigest()


def _sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as handle:
        for chunk in iter(
            lambda: handle.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(
                chunk
            )

    return digest.hexdigest()


def _read_json_auto(
    path: Path,
) -> dict[str, Any]:
    if not path.is_file():
        raise ModelArtifactVerificationError(
            f"Required JSON file missing: {path}"
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
        raise ModelArtifactVerificationError(
            f"Invalid JSON: {path}"
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        raise ModelArtifactVerificationError(
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
        raise ModelArtifactVerificationError(
            f"Required mapping missing: {key}"
        )

    return value


def validate_winner_freeze(
    freeze_payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    if (
        freeze_payload.get(
            "analysis_version"
        )
        != EXPECTED_WINNER_FREEZE_ANALYSIS_VERSION
    ):
        raise ModelArtifactVerificationError(
            "Winner-freeze analysis version mismatch."
        )

    if (
        freeze_payload.get(
            "valid"
        )
        is not True
    ):
        raise ModelArtifactVerificationError(
            "Winner-freeze evidence must be valid=true."
        )

    decision = _required_mapping(
        freeze_payload,
        "decision",
    )

    expected_decision = {
        "status": (
            "TRAIN_INTERNAL_WINNER_FROZEN"
        ),
        "winner_candidate_id": (
            EXPECTED_WINNER_ID
        ),
        "winner_frozen_for_full_train_fit": True,
        "full_train_fit_authorized_next": True,
        "full_train_fit_performed": False,
        "validation_access_authorized": False,
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
            raise ModelArtifactVerificationError(
                "Winner-freeze decision mismatch: "
                f"{key}"
            )

    winner = _required_mapping(
        freeze_payload,
        "winner",
    )

    if (
        winner.get(
            "candidate_id"
        )
        != EXPECTED_WINNER_ID
    ):
        raise ModelArtifactVerificationError(
            "Winner candidate mismatch."
        )

    if (
        winner.get(
            "eligible"
        )
        is not True
    ):
        raise ModelArtifactVerificationError(
            "Winner must remain eligible."
        )

    config = _required_mapping(
        winner,
        "candidate_config",
    )

    config_fingerprint = _required_mapping(
        winner,
        "candidate_config_fingerprint",
    )

    if (
        config_fingerprint.get(
            "sha256"
        )
        != EXPECTED_WINNER_CONFIG_SHA256
    ):
        raise ModelArtifactVerificationError(
            "Winner config fingerprint mismatch."
        )

    if (
        _canonical_sha256(
            config
        )
        != EXPECTED_WINNER_CONFIG_SHA256
    ):
        raise ModelArtifactVerificationError(
            "Winner config content mismatch."
        )

    return config


def validate_full_train_fit_report(
    fit_payload: Mapping[str, Any],
    winner_freeze_payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    if (
        fit_payload.get(
            "analysis_version"
        )
        != EXPECTED_FIT_ANALYSIS_VERSION
    ):
        raise ModelArtifactVerificationError(
            "Full-TRAIN fit analysis version mismatch."
        )

    if (
        fit_payload.get(
            "valid"
        )
        is not True
    ):
        raise ModelArtifactVerificationError(
            "Full-TRAIN fit must be valid=true."
        )

    identity = _required_mapping(
        fit_payload,
        "artifact_identity",
    )

    expected_identity = {
        "dataset_id": (
            EXPECTED_DATASET_ID
        ),
        "dataset_sha256": (
            EXPECTED_DATASET_SHA256
        ),
        "manifest_sha256": (
            EXPECTED_MANIFEST_SHA256
        ),
        "train_input_fingerprint_sha256": (
            EXPECTED_TRAIN_INPUT_SHA256
        ),
        "train_target_fingerprint_sha256": (
            EXPECTED_TRAIN_TARGET_SHA256
        ),
        "feature_columns_sha256": (
            EXPECTED_FEATURE_COLUMNS_SHA256
        ),
        "candidate_registry_fingerprint_sha256": (
            EXPECTED_REGISTRY_SHA256
        ),
        "research_protocol_fingerprint_sha256": (
            EXPECTED_PROTOCOL_SHA256
        ),
        "walk_forward_evaluation_fingerprint_sha256": (
            EXPECTED_WALK_FORWARD_SHA256
        ),
        "winner_config_fingerprint_sha256": (
            EXPECTED_WINNER_CONFIG_SHA256
        ),
    }

    for (
        key,
        expected,
    ) in expected_identity.items():
        if (
            identity.get(
                key
            )
            != expected
        ):
            raise ModelArtifactVerificationError(
                "Full-TRAIN artifact identity mismatch: "
                f"{key}"
            )

    expected_winner_freeze_sha = (
        _canonical_sha256(
            winner_freeze_payload
        )
    )

    if (
        identity.get(
            "winner_freeze_canonical_sha256"
        )
        != expected_winner_freeze_sha
    ):
        raise ModelArtifactVerificationError(
            "Full-TRAIN fit does not reference "
            "the exact frozen winner evidence."
        )

    fit = _required_mapping(
        fit_payload,
        "fit",
    )

    if (
        fit.get(
            "candidate_id"
        )
        != EXPECTED_WINNER_ID
    ):
        raise ModelArtifactVerificationError(
            "Fitted candidate ID mismatch."
        )

    candidate_config = _required_mapping(
        fit,
        "candidate_config",
    )

    if (
        _canonical_sha256(
            candidate_config
        )
        != EXPECTED_WINNER_CONFIG_SHA256
    ):
        raise ModelArtifactVerificationError(
            "Fitted candidate config differs "
            "from frozen C04 config."
        )

    if (
        fit.get(
            "fit_rows"
        )
        != EXPECTED_ROWS
    ):
        raise ModelArtifactVerificationError(
            "Full-TRAIN fit row count mismatch."
        )

    if (
        fit.get(
            "fit_feature_count"
        )
        != EXPECTED_FEATURES
    ):
        raise ModelArtifactVerificationError(
            "Full-TRAIN feature count mismatch."
        )

    if (
        fit.get(
            "fit_target"
        )
        != "target_class"
    ):
        raise ModelArtifactVerificationError(
            "Unexpected fit target."
        )

    if (
        fit.get(
            "scaler_fit_performed"
        )
        is not False
    ):
        raise ModelArtifactVerificationError(
            "C04 must not fit a scaler."
        )

    if (
        fit.get(
            "sample_weight_supplied"
        )
        is not False
    ):
        raise ModelArtifactVerificationError(
            "Unexpected sample weighting in C04 full fit."
        )

    if (
        fit.get(
            "training_metrics_computed"
        )
        is not False
    ):
        raise ModelArtifactVerificationError(
            "Training metrics must not be computed."
        )

    decision = _required_mapping(
        fit_payload,
        "decision",
    )

    expected_decision = {
        "status": (
            "FROZEN_C04_FULL_TRAIN_MODEL_ARTIFACT_CREATED"
        ),
        "full_train_fit_completed": True,
        "model_artifact_frozen": True,
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
            raise ModelArtifactVerificationError(
                "Full-TRAIN decision mismatch: "
                f"{key}"
            )

    policy = _required_mapping(
        fit_payload,
        "scientific_policy",
    )

    required_false = (
        "candidate_registry_changed",
        "candidate_added_after_results",
        "hyperparameters_changed_after_results",
        "winner_changed_after_freeze",
        "scaler_fit_performed",
        "threshold_search_performed",
        "probability_calibration_performed",
        "feature_selection_performed",
        "training_metrics_computed",
        "portable_validation_feature_values_loaded",
        "portable_validation_target_values_loaded",
        "portable_test_feature_values_loaded",
        "portable_test_target_values_loaded",
        "execution_integration_modified",
        "risk_engine_modified",
        "orders_sent",
        "shadow_authorized",
        "live_authorized",
    )

    for key in required_false:
        if (
            policy.get(
                key
            )
            is not False
        ):
            raise ModelArtifactVerificationError(
                "Full-TRAIN scientific boundary mismatch: "
                f"{key}"
            )

    if (
        policy.get(
            "model_fit_performed_in_this_gate"
        )
        is not True
    ):
        raise ModelArtifactVerificationError(
            "Full-TRAIN fit is not recorded as performed."
        )

    if (
        policy.get(
            "fit_scope"
        )
        != "FULL_FROZEN_TRAIN_ONLY"
    ):
        raise ModelArtifactVerificationError(
            "Full-TRAIN fit scope mismatch."
        )

    model_record = _required_mapping(
        fit_payload,
        "model_record",
    )

    model_record_fingerprint = _required_mapping(
        fit_payload,
        "model_record_fingerprint",
    )

    if (
        model_record_fingerprint.get(
            "canonicalization"
        )
        != "JSON_SORT_KEYS_COMPACT_UTF8_SHA256"
    ):
        raise ModelArtifactVerificationError(
            "Unexpected model-record canonicalization."
        )

    if (
        model_record_fingerprint.get(
            "sha256"
        )
        != EXPECTED_MODEL_RECORD_SHA256
    ):
        raise ModelArtifactVerificationError(
            "Model-record fingerprint mismatch."
        )

    if (
        _canonical_sha256(
            model_record
        )
        != EXPECTED_MODEL_RECORD_SHA256
    ):
        raise ModelArtifactVerificationError(
            "Model-record content fingerprint mismatch."
        )

    expected_model_record = {
        "candidate_id": (
            EXPECTED_WINNER_ID
        ),
        "candidate_config_fingerprint_sha256": (
            EXPECTED_WINNER_CONFIG_SHA256
        ),
        "model_artifact_filename": (
            "xauusd_portable_331_c04_full_train_model.joblib"
        ),
        "model_artifact_sha256": (
            EXPECTED_MODEL_ARTIFACT_SHA256
        ),
        "serialization": "joblib",
        "dataset_id": (
            EXPECTED_DATASET_ID
        ),
        "dataset_sha256": (
            EXPECTED_DATASET_SHA256
        ),
        "manifest_sha256": (
            EXPECTED_MANIFEST_SHA256
        ),
        "train_input_fingerprint_sha256": (
            EXPECTED_TRAIN_INPUT_SHA256
        ),
        "train_target_fingerprint_sha256": (
            EXPECTED_TRAIN_TARGET_SHA256
        ),
        "feature_columns_sha256": (
            EXPECTED_FEATURE_COLUMNS_SHA256
        ),
        "train_rows": (
            EXPECTED_ROWS
        ),
        "feature_count": (
            EXPECTED_FEATURES
        ),
        "probability_class_order": list(
            EXPECTED_CLASS_ORDER
        ),
    }

    if (
        dict(
            model_record
        )
        != expected_model_record
    ):
        raise ModelArtifactVerificationError(
            "Model record differs from frozen "
            "reviewed artifact identity."
        )

    return model_record


def validate_model_artifact(
    model_record: Mapping[str, Any],
    model_path: Path,
) -> dict[str, Any]:
    if (
        model_path.name
        != model_record.get(
            "model_artifact_filename"
        )
    ):
        raise ModelArtifactVerificationError(
            "Model artifact filename mismatch."
        )

    if not model_path.is_file():
        raise ModelArtifactVerificationError(
            f"Frozen model artifact missing: {model_path}"
        )

    actual_sha256 = _sha256_file(
        model_path
    )

    if (
        actual_sha256
        != EXPECTED_MODEL_ARTIFACT_SHA256
    ):
        raise ModelArtifactVerificationError(
            "Frozen model artifact SHA256 mismatch."
        )

    if (
        actual_sha256
        != model_record.get(
            "model_artifact_sha256"
        )
    ):
        raise ModelArtifactVerificationError(
            "Model artifact SHA256 differs "
            "from model record."
        )

    try:
        model = joblib.load(
            model_path
        )

    except Exception as exc:
        raise ModelArtifactVerificationError(
            "Frozen model artifact cannot be reloaded."
        ) from exc

    if (
        model.__class__.__name__
        != "ExtraTreesClassifier"
    ):
        raise ModelArtifactVerificationError(
            "Frozen model class mismatch."
        )

    classes = tuple(
        int(
            value
        )
        for value
        in np.asarray(
            model.classes_
        ).tolist()
    )

    if (
        classes
        != EXPECTED_CLASS_ORDER
    ):
        raise ModelArtifactVerificationError(
            "Frozen model class order mismatch."
        )

    if (
        int(
            model.n_features_in_
        )
        != EXPECTED_FEATURES
    ):
        raise ModelArtifactVerificationError(
            "Frozen model n_features_in_ mismatch."
        )

    estimators = getattr(
        model,
        "estimators_",
        None,
    )

    if (
        not isinstance(
            estimators,
            list,
        )
        or len(
            estimators
        )
        != 500
    ):
        raise ModelArtifactVerificationError(
            "Frozen model tree count mismatch."
        )

    params = model.get_params(
        deep=False
    )

    for (
        key,
        expected,
    ) in EXPECTED_ESTIMATOR_PARAMS.items():
        if (
            params.get(
                key
            )
            != expected
        ):
            raise ModelArtifactVerificationError(
                "Frozen model parameter mismatch: "
                f"{key}"
            )

    return {
        "model_artifact_filename": (
            model_path.name
        ),
        "model_artifact_sha256": (
            actual_sha256
        ),
        "model_class": (
            model.__class__.__name__
        ),
        "class_order": list(
            classes
        ),
        "n_features_in": int(
            model.n_features_in_
        ),
        "tree_count": len(
            estimators
        ),
        "estimator_params_confirmed": True,
        "artifact_reload_confirmed": True,
    }


def build_verification(
    model_path: Path | None = None,
) -> dict[str, Any]:
    winner_freeze = _read_json_auto(
        WINNER_FREEZE_PATH
    )

    validate_winner_freeze(
        winner_freeze
    )

    fit_payload = _read_json_auto(
        FULL_TRAIN_FIT_PATH
    )

    model_record = (
        validate_full_train_fit_report(
            fit_payload,
            winner_freeze,
        )
    )

    if model_path is None:
        model_path = (
            REPO_ROOT
            / str(
                model_record[
                    "model_artifact_filename"
                ]
            )
        )

    artifact_validation = (
        validate_model_artifact(
            model_record,
            model_path,
        )
    )

    verification_record = {
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
        "dataset_id": (
            EXPECTED_DATASET_ID
        ),
        "dataset_sha256": (
            EXPECTED_DATASET_SHA256
        ),
        "manifest_sha256": (
            EXPECTED_MANIFEST_SHA256
        ),
        "train_input_fingerprint_sha256": (
            EXPECTED_TRAIN_INPUT_SHA256
        ),
        "train_target_fingerprint_sha256": (
            EXPECTED_TRAIN_TARGET_SHA256
        ),
        "feature_columns_sha256": (
            EXPECTED_FEATURE_COLUMNS_SHA256
        ),
        "candidate_registry_fingerprint_sha256": (
            EXPECTED_REGISTRY_SHA256
        ),
        "research_protocol_fingerprint_sha256": (
            EXPECTED_PROTOCOL_SHA256
        ),
        "walk_forward_evaluation_fingerprint_sha256": (
            EXPECTED_WALK_FORWARD_SHA256
        ),
    }

    return {
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "valid": True,
        "research_scope": (
            "VERIFY_FROZEN_C04_FULL_TRAIN_MODEL_"
            "ARTIFACT_AND_PROVENANCE_WITHOUT_DATASET_"
            "OR_HOLDOUT_VALUE_ACCESS"
        ),
        "verification_record": (
            verification_record
        ),
        "verification_record_fingerprint": {
            "canonicalization": (
                "JSON_SORT_KEYS_COMPACT_UTF8_SHA256"
            ),
            "sha256": (
                _canonical_sha256(
                    verification_record
                )
            ),
        },
        "artifact_validation": (
            artifact_validation
        ),
        "decision": {
            "status": (
                "FROZEN_C04_MODEL_ARTIFACT_"
                "PROVENANCE_VERIFIED"
            ),
            "winner_candidate_id": (
                EXPECTED_WINNER_ID
            ),
            "model_artifact_verified": True,
            "model_artifact_cryptographically_frozen": True,
            "full_train_fit_verified": True,
            "validation_accessed_in_this_gate": False,
            "validation_access_authorized_next": True,
            "test_accessed_in_this_gate": False,
            "test_access_authorized": False,
            "shadow_authorized": False,
            "live_authorized": False,
            "next_action": (
                "IMPLEMENT_ONE_TIME_UNTOUCHED_PORTABLE_"
                "VALIDATION_RUNNER_USING_ONLY_THE_VERIFIED_"
                "FROZEN_C04_MODEL_WITHOUT_REFIT_TUNING_"
                "CALIBRATION_OR_THRESHOLD_SEARCH"
            ),
        },
        "scientific_policy": {
            "dataset_rows_loaded": False,
            "train_feature_values_loaded": False,
            "train_target_values_loaded": False,
            "portable_validation_feature_values_loaded": False,
            "portable_validation_target_values_loaded": False,
            "portable_test_feature_values_loaded": False,
            "portable_test_target_values_loaded": False,
            "model_fit_performed_in_this_gate": False,
            "model_refit_performed": False,
            "model_artifact_modified": False,
            "candidate_registry_changed": False,
            "winner_changed": False,
            "hyperparameters_changed": False,
            "threshold_search_performed": False,
            "probability_calibration_performed": False,
            "feature_selection_performed": False,
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

    temporary_path = path.with_suffix(
        path.suffix
        + ".tmp"
    )

    temporary_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary_path.replace(
        path
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify the frozen C04 full-TRAIN model "
            "artifact and provenance before one-time "
            "untouched VALIDATION."
        )
    )

    parser.add_argument(
        "--model",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )

    args = parser.parse_args()

    try:
        report = build_verification(
            args.model
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
                "FROZEN_C04_MODEL_ARTIFACT_"
                "PROVENANCE_VERIFICATION_FAILED"
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
                "dataset_rows_loaded": False,
                "model_fit_performed_in_this_gate": False,
                "validation_access_authorized": False,
                "test_access_authorized": False,
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
                "model_artifact_sha256": (
                    report[
                        "artifact_validation"
                    ][
                        "model_artifact_sha256"
                    ]
                ),
                "verification_record_fingerprint_sha256": (
                    report[
                        "verification_record_fingerprint"
                    ][
                        "sha256"
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