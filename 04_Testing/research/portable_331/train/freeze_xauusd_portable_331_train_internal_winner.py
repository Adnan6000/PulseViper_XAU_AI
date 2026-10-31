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


ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_INTERNAL_"
    "WINNER_FREEZE_V1"
)

def _find_repo_root(start: Path) -> Path:
    resolved = start.resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "02_AI").is_dir():
            return candidate
    return resolved.parents[4]

REPO_ROOT = _find_repo_root(Path(__file__))
SCRIPT_DIR = Path(__file__).resolve().parent


EVALUATOR_PATH = (
    SCRIPT_DIR
    / "evaluate_xauusd_portable_331_train_model_candidates.py"
)

REGISTRY_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_train_model_candidate_registry_design.json"
)

EVALUATION_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_train_model_candidate_walk_forward_evaluation.json"
)

DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "04_Testing/evidence/research/portable_331/train/xauusd_portable_331_train_internal_winner_freeze.json"
)

EXPECTED_EVALUATION_ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_CANDIDATE_"
    "WALK_FORWARD_EVALUATION_V1"
)

EXPECTED_EVALUATOR_ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_MODEL_"
    "CANDIDATE_EVALUATOR_V1"
)

EXPECTED_REGISTRY_FINGERPRINT = (
    "b8088bb34ce8940f7de5946fbb9b0fd20f40d7cc93a76b76fd7975591f00066c"
)

EXPECTED_PROTOCOL_FINGERPRINT = (
    "69e51e1b249b9da68cbf6f6778a8ae10f9f33f7082a07e5073a1ba731fa1640d"
)

EXPECTED_EVALUATION_FINGERPRINT = (
    "15516174ba6f3d8932425b20dcde33db25c040e0901c86af39796f97847ac7ed"
)

EXPECTED_WINNER_CANDIDATE_ID = (
    "C04_FLAT_EXTRA_TREES_CONSTRAINED"
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

EXPECTED_TRAIN_INPUT_FINGERPRINT = (
    "9ffb72759499cfc202e88cfdbd61b42cee5b5c7cbb7db5870470453caa5ed2c5"
)

EXPECTED_TRAIN_TARGET_FINGERPRINT = (
    "bc063a790e70cdbc931b2170ccfef883634b40ee7336a529a32bda0eaf0babe3"
)

EXPECTED_CANDIDATE_IDS = (
    "C01_FLAT_LOGREG_BALANCED_C005",
    "C02_FLAT_LOGREG_BALANCED_C020",
    "C03_FLAT_HGB_SHALLOW",
    "C04_FLAT_EXTRA_TREES_CONSTRAINED",
    "C05_HIER_LOGREG_REGULARIZED",
    "C06_HIER_HGB_LOGREG_CONSTRAINED",
)


class WinnerFreezeError(
    RuntimeError
):
    pass


def _canonical_json_sha256(
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


def _read_text_auto(
    path: Path,
) -> str:
    raw = path.read_bytes()

    if raw.startswith(
        b"\xff\xfe"
    ):
        return raw.decode(
            "utf-16"
        )

    if raw.startswith(
        b"\xfe\xff"
    ):
        return raw.decode(
            "utf-16"
        )

    if raw.startswith(
        b"\xef\xbb\xbf"
    ):
        return raw.decode(
            "utf-8-sig"
        )

    return raw.decode(
        "utf-8"
    )


def _load_json_auto(
    path: Path,
) -> dict[str, Any]:
    if not path.is_file():
        raise WinnerFreezeError(
            f"Required JSON file missing: {path}"
        )

    try:
        payload = json.loads(
            _read_text_auto(
                path
            )
        )

    except Exception as exc:
        raise WinnerFreezeError(
            f"Cannot load JSON file: {path}"
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        raise WinnerFreezeError(
            f"Expected JSON object: {path}"
        )

    return payload


def _load_evaluator() -> ModuleType:
    if not EVALUATOR_PATH.is_file():
        raise WinnerFreezeError(
            f"Evaluator missing: {EVALUATOR_PATH}"
        )

    spec = importlib.util.spec_from_file_location(
        "xauusd_candidate_evaluator_for_winner_freeze",
        EVALUATOR_PATH,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise WinnerFreezeError(
            "Cannot create evaluator import spec."
        )

    module = importlib.util.module_from_spec(
        spec
    )

    sys.modules[
        spec.name
    ] = module

    spec.loader.exec_module(
        module
    )

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
        raise WinnerFreezeError(
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
        raise WinnerFreezeError(
            f"Required list missing: {key}"
        )

    return value


def _validate_artifact_identity(
    payload: Mapping[str, Any],
) -> None:
    identity = _required_mapping(
        payload,
        "artifact_identity",
    )

    expected = {
        "candidate_registry_fingerprint_sha256": (
            EXPECTED_REGISTRY_FINGERPRINT
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
        "research_protocol_fingerprint_sha256": (
            EXPECTED_PROTOCOL_FINGERPRINT
        ),
        "train_input_fingerprint_sha256": (
            EXPECTED_TRAIN_INPUT_FINGERPRINT
        ),
        "train_target_fingerprint_sha256": (
            EXPECTED_TRAIN_TARGET_FINGERPRINT
        ),
    }

    for key, expected_value in expected.items():
        if (
            identity.get(
                key
            )
            != expected_value
        ):
            raise WinnerFreezeError(
                "Evaluation artifact identity mismatch: "
                f"{key}"
            )


def _validate_outer_scientific_boundary(
    payload: Mapping[str, Any],
) -> None:
    policy = _required_mapping(
        payload,
        "scientific_policy",
    )

    required_false = (
        "candidate_added_after_results",
        "candidate_registry_changed",
        "execution_integration_modified",
        "feature_selection_performed",
        "final_full_train_fit_performed",
        "hyperparameters_changed_after_results",
        "live_authorized",
        "model_artifacts_written",
        "orders_sent",
        "portable_test_feature_values_loaded",
        "portable_test_target_values_loaded",
        "portable_validation_feature_values_loaded",
        "portable_validation_target_values_loaded",
        "probability_calibration_performed",
        "risk_engine_modified",
        "threshold_search_performed",
    )

    for key in required_false:
        if (
            policy.get(
                key
            )
            is not False
        ):
            raise WinnerFreezeError(
                "Scientific boundary mismatch: "
                f"{key}"
            )

    if (
        policy.get(
            "real_candidate_fit_performed"
        )
        is not True
    ):
        raise WinnerFreezeError(
            "Real candidate fit must be recorded as performed."
        )

    if (
        policy.get(
            "fit_scope"
        )
        != "FOUR_FROZEN_TRAIN_INTERNAL_FOLDS_ONLY"
    ):
        raise WinnerFreezeError(
            "Unexpected candidate fit scope."
        )


def _validate_outer_decision(
    payload: Mapping[str, Any],
) -> None:
    decision = _required_mapping(
        payload,
        "decision",
    )

    if (
        decision.get(
            "candidate_walk_forward_evaluation_completed"
        )
        is not True
    ):
        raise WinnerFreezeError(
            "Walk-forward evaluation is not complete."
        )

    if (
        decision.get(
            "selection_status"
        )
        != "WINNER_SELECTED_TRAIN_INTERNAL_ONLY"
    ):
        raise WinnerFreezeError(
            "Expected a TRAIN-internal winner."
        )

    if (
        decision.get(
            "train_internal_winner_candidate_id"
        )
        != EXPECTED_WINNER_CANDIDATE_ID
    ):
        raise WinnerFreezeError(
            "Unexpected TRAIN-internal winner."
        )

    required_false = (
        "final_full_train_fit_authorized",
        "live_authorized",
        "test_access_authorized",
        "validation_access_authorized",
        "winner_frozen_for_full_train_fit",
    )

    for key in required_false:
        if (
            decision.get(
                key
            )
            is not False
        ):
            raise WinnerFreezeError(
                "Pre-freeze decision boundary mismatch: "
                f"{key}"
            )


def _validate_execution_contract(
    payload: Mapping[str, Any],
    evaluator: ModuleType,
) -> None:
    contract = _required_mapping(
        payload,
        "execution_contract",
    )

    if (
        contract.get(
            "candidate_count"
        )
        != 6
    ):
        raise WinnerFreezeError(
            "Expected exactly six frozen candidates."
        )

    if (
        tuple(
            contract.get(
                "candidate_ids",
                (),
            )
        )
        != EXPECTED_CANDIDATE_IDS
    ):
        raise WinnerFreezeError(
            "Frozen candidate IDs mismatch."
        )

    if (
        contract.get(
            "feature_count"
        )
        != 331
    ):
        raise WinnerFreezeError(
            "Feature count mismatch."
        )

    if (
        contract.get(
            "fold_count"
        )
        != 4
    ):
        raise WinnerFreezeError(
            "Fold count mismatch."
        )

    if (
        contract.get(
            "purge_rows"
        )
        != 12
    ):
        raise WinnerFreezeError(
            "Purge rows mismatch."
        )

    if (
        contract.get(
            "train_rows"
        )
        != 69966
    ):
        raise WinnerFreezeError(
            "TRAIN row count mismatch."
        )

    if (
        tuple(
            contract.get(
                "required_fold_metrics",
                (),
            )
        )
        != tuple(
            evaluator.REQUIRED_FOLD_METRICS
        )
    ):
        raise WinnerFreezeError(
            "Frozen fold metric contract mismatch."
        )

    required_true = (
        "registry_frozen_before_fit",
    )

    for key in required_true:
        if (
            contract.get(
                key
            )
            is not True
        ):
            raise WinnerFreezeError(
                f"Execution contract mismatch: {key}"
            )

    required_false = (
        "feature_selection_performed",
        "portable_test_accessed",
        "portable_validation_accessed",
        "probability_calibration_performed",
        "threshold_tuning_performed",
    )

    for key in required_false:
        if (
            contract.get(
                key
            )
            is not False
        ):
            raise WinnerFreezeError(
                f"Execution contract mismatch: {key}"
            )


def _validate_evaluation_fingerprint(
    payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    evaluation = _required_mapping(
        payload,
        "evaluation",
    )

    fingerprint = _required_mapping(
        payload,
        "evaluation_fingerprint",
    )

    if (
        fingerprint.get(
            "canonicalization"
        )
        != "JSON_SORT_KEYS_COMPACT_UTF8_SHA256"
    ):
        raise WinnerFreezeError(
            "Unexpected evaluation fingerprint canonicalization."
        )

    declared_sha = fingerprint.get(
        "sha256"
    )

    if (
        declared_sha
        != EXPECTED_EVALUATION_FINGERPRINT
    ):
        raise WinnerFreezeError(
            "Evaluation fingerprint does not match "
            "the reviewed frozen result."
        )

    computed_sha = _canonical_json_sha256(
        evaluation
    )

    if (
        computed_sha
        != declared_sha
    ):
        raise WinnerFreezeError(
            "Evaluation content does not match "
            "declared fingerprint."
        )

    return evaluation


def _validate_nested_evaluation(
    evaluation: Mapping[str, Any],
    registry: Mapping[str, Any],
    evaluator: ModuleType,
) -> tuple[
    Mapping[str, Any],
    Mapping[str, Any],
]:
    if (
        evaluation.get(
            "analysis_version"
        )
        != EXPECTED_EVALUATOR_ANALYSIS_VERSION
    ):
        raise WinnerFreezeError(
            "Unexpected evaluator analysis version."
        )

    if (
        evaluation.get(
            "registry_fingerprint_sha256"
        )
        != EXPECTED_REGISTRY_FINGERPRINT
    ):
        raise WinnerFreezeError(
            "Nested evaluation registry fingerprint mismatch."
        )

    if (
        evaluation.get(
            "fold_count"
        )
        != 4
    ):
        raise WinnerFreezeError(
            "Nested evaluation fold count mismatch."
        )

    if (
        tuple(
            evaluation.get(
                "required_fold_metrics",
                (),
            )
        )
        != tuple(
            evaluator.REQUIRED_FOLD_METRICS
        )
    ):
        raise WinnerFreezeError(
            "Nested evaluator metric contract mismatch."
        )

    nested_policy = _required_mapping(
        evaluation,
        "scientific_policy",
    )

    required_false = (
        "feature_selection_performed",
        "live_authorized",
        "model_artifacts_written",
        "portable_test_accessed",
        "portable_validation_accessed",
        "probability_calibration_performed",
        "registry_changed",
        "threshold_search_performed",
    )

    for key in required_false:
        if (
            nested_policy.get(
                key
            )
            is not False
        ):
            raise WinnerFreezeError(
                "Nested scientific policy mismatch: "
                f"{key}"
            )

    reports = _required_list(
        evaluation,
        "candidate_reports",
    )

    if (
        len(
            reports
        )
        != 6
    ):
        raise WinnerFreezeError(
            "Expected six candidate reports."
        )

    candidate_ids = tuple(
        report.get(
            "candidate_id"
        )
        for report in reports
        if isinstance(
            report,
            Mapping,
        )
    )

    if (
        candidate_ids
        != EXPECTED_CANDIDATE_IDS
    ):
        raise WinnerFreezeError(
            "Candidate report identity/order mismatch."
        )

    registry_contract = _required_mapping(
        registry,
        "contract",
    )

    selection_policy = _required_mapping(
        registry_contract,
        "selection_policy",
    )

    recomputed_selection = (
        evaluator.select_winner(
            reports,
            selection_policy,
        )
    )

    recorded_selection = _required_mapping(
        evaluation,
        "selection",
    )

    if (
        recomputed_selection.get(
            "status"
        )
        != recorded_selection.get(
            "status"
        )
    ):
        raise WinnerFreezeError(
            "Recomputed selection status mismatch."
        )

    if (
        recomputed_selection.get(
            "winner_candidate_id"
        )
        != recorded_selection.get(
            "winner_candidate_id"
        )
    ):
        raise WinnerFreezeError(
            "Recomputed winner mismatch."
        )

    if (
        recorded_selection.get(
            "winner_candidate_id"
        )
        != EXPECTED_WINNER_CANDIDATE_ID
    ):
        raise WinnerFreezeError(
            "Frozen selection did not choose expected winner."
        )

    winner_report = None

    for report in reports:
        if (
            report.get(
                "candidate_id"
            )
            == EXPECTED_WINNER_CANDIDATE_ID
        ):
            winner_report = report
            break

    if not isinstance(
        winner_report,
        Mapping,
    ):
        raise WinnerFreezeError(
            "Winner report missing."
        )

    if (
        winner_report.get(
            "eligible"
        )
        is not True
    ):
        raise WinnerFreezeError(
            "Selected winner is not eligible."
        )

    if (
        winner_report.get(
            "status"
        )
        != "ELIGIBLE"
    ):
        raise WinnerFreezeError(
            "Selected winner status is not ELIGIBLE."
        )

    return (
        winner_report,
        recorded_selection,
    )


def _winner_candidate_config(
    registry: Mapping[str, Any],
) -> Mapping[str, Any]:
    contract = _required_mapping(
        registry,
        "contract",
    )

    candidates = _required_list(
        contract,
        "candidates",
    )

    for candidate in candidates:
        if (
            isinstance(
                candidate,
                Mapping,
            )
            and candidate.get(
                "candidate_id"
            )
            == EXPECTED_WINNER_CANDIDATE_ID
        ):
            return candidate

    raise WinnerFreezeError(
        "Winner candidate configuration missing "
        "from frozen registry."
    )


def validate_reviewed_evaluation(
    payload: Mapping[str, Any],
    registry: Mapping[str, Any],
    evaluator: ModuleType,
) -> tuple[
    Mapping[str, Any],
    Mapping[str, Any],
    Mapping[str, Any],
]:
    if (
        payload.get(
            "analysis_version"
        )
        != EXPECTED_EVALUATION_ANALYSIS_VERSION
    ):
        raise WinnerFreezeError(
            "Unexpected walk-forward evaluation version."
        )

    if (
        payload.get(
            "valid"
        )
        is not True
    ):
        raise WinnerFreezeError(
            "Walk-forward evaluation must be valid=true."
        )

    _validate_artifact_identity(
        payload
    )

    _validate_outer_scientific_boundary(
        payload
    )

    _validate_outer_decision(
        payload
    )

    _validate_execution_contract(
        payload,
        evaluator,
    )

    evaluation = (
        _validate_evaluation_fingerprint(
            payload
        )
    )

    (
        winner_report,
        recorded_selection,
    ) = _validate_nested_evaluation(
        evaluation,
        registry,
        evaluator,
    )

    candidate_config = (
        _winner_candidate_config(
            registry
        )
    )

    return (
        winner_report,
        recorded_selection,
        candidate_config,
    )


def build_winner_freeze() -> dict[str, Any]:
    evaluator = _load_evaluator()

    registry = (
        evaluator.load_frozen_candidate_registry(
            REGISTRY_PATH
        )
    )

    if (
        registry[
            "registry_fingerprint"
        ][
            "sha256"
        ]
        != EXPECTED_REGISTRY_FINGERPRINT
    ):
        raise WinnerFreezeError(
            "Frozen registry fingerprint mismatch."
        )

    evaluation_payload = (
        _load_json_auto(
            EVALUATION_PATH
        )
    )

    (
        winner_report,
        recorded_selection,
        candidate_config,
    ) = validate_reviewed_evaluation(
        evaluation_payload,
        registry,
        evaluator,
    )

    summary = _required_mapping(
        winner_report,
        "summary",
    )

    candidate_config_sha = (
        _canonical_json_sha256(
            candidate_config
        )
    )

    eligible_count = sum(
        1
        for report in evaluation_payload[
            "evaluation"
        ][
            "candidate_reports"
        ]
        if (
            isinstance(
                report,
                Mapping,
            )
            and report.get(
                "eligible"
            )
            is True
        )
    )

    failed_closed_count = sum(
        1
        for report in evaluation_payload[
            "evaluation"
        ][
            "candidate_reports"
        ]
        if (
            isinstance(
                report,
                Mapping,
            )
            and report.get(
                "status"
            )
            == "FAILED_CLOSED"
        )
    )

    return {
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "valid": True,
        "research_scope": (
            "FREEZE_PREDECLARED_TRAIN_INTERNAL_"
            "WINNER_AFTER_FIXED_SIX_PURGED_"
            "WALK_FORWARD_WITHOUT_NEW_MODEL_FIT"
        ),
        "artifact_identity": {
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
                EXPECTED_TRAIN_INPUT_FINGERPRINT
            ),
            "train_target_fingerprint_sha256": (
                EXPECTED_TRAIN_TARGET_FINGERPRINT
            ),
            "candidate_registry_fingerprint_sha256": (
                EXPECTED_REGISTRY_FINGERPRINT
            ),
            "research_protocol_fingerprint_sha256": (
                EXPECTED_PROTOCOL_FINGERPRINT
            ),
            "walk_forward_evaluation_fingerprint_sha256": (
                EXPECTED_EVALUATION_FINGERPRINT
            ),
        },
        "winner": {
            "candidate_id": (
                EXPECTED_WINNER_CANDIDATE_ID
            ),
            "candidate_config": dict(
                candidate_config
            ),
            "candidate_config_fingerprint": {
                "canonicalization": (
                    "JSON_SORT_KEYS_COMPACT_UTF8_SHA256"
                ),
                "sha256": (
                    candidate_config_sha
                ),
            },
            "selection_status": (
                recorded_selection.get(
                    "status"
                )
            ),
            "selection_reason": (
                recorded_selection.get(
                    "reason"
                )
            ),
            "selection_key": (
                recorded_selection.get(
                    "selection_key"
                )
            ),
            "eligible": True,
            "summary": dict(
                summary
            ),
        },
        "review": {
            "candidate_count": 6,
            "eligible_candidate_count": int(
                eligible_count
            ),
            "failed_closed_candidate_count": int(
                failed_closed_count
            ),
            "winner_selected_by_predeclared_policy": True,
            "results_driven_candidate_change_performed": False,
            "results_driven_hyperparameter_change_performed": False,
            "post_hoc_selection_threshold_added": False,
            "train_internal_winner_is_not_validation_proof": True,
            "train_internal_winner_is_not_test_proof": True,
            "train_internal_winner_is_not_live_proof": True,
        },
        "decision": {
            "status": (
                "TRAIN_INTERNAL_WINNER_FROZEN"
            ),
            "winner_candidate_id": (
                EXPECTED_WINNER_CANDIDATE_ID
            ),
            "winner_frozen_for_full_train_fit": True,
            "full_train_fit_authorized_next": True,
            "full_train_fit_performed": False,
            "validation_access_authorized": False,
            "test_access_authorized": False,
            "shadow_authorized": False,
            "live_authorized": False,
            "next_action": (
                "FIT_EXACT_FROZEN_C04_ON_FULL_"
                "69966_ROW_TRAIN_ONLY_AND_FREEZE_"
                "MODEL_ARTIFACT_BEFORE_ONE_TIME_"
                "UNTOUCHED_VALIDATION"
            ),
        },
        "scientific_policy": {
            "model_fit_performed_in_this_gate": False,
            "scaler_fit_performed_in_this_gate": False,
            "candidate_registry_changed": False,
            "candidate_added_after_results": False,
            "hyperparameters_changed_after_results": False,
            "threshold_search_performed": False,
            "probability_calibration_performed": False,
            "feature_selection_performed": False,
            "portable_validation_feature_values_loaded": False,
            "portable_validation_target_values_loaded": False,
            "portable_test_feature_values_loaded": False,
            "portable_test_target_values_loaded": False,
            "model_artifacts_written_in_this_gate": False,
            "execution_integration_modified": False,
            "risk_engine_modified": False,
            "orders_sent": False,
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
            "Freeze the predeclared TRAIN-internal "
            "winner from the reviewed fixed-six "
            "walk-forward evaluation."
        )
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )

    args = parser.parse_args()

    try:
        report = build_winner_freeze()

    except Exception as exc:
        failure = {
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "valid": False,
            "reason": (
                "TRAIN_INTERNAL_WINNER_FREEZE_FAILED"
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
                "model_fit_performed_in_this_gate": False,
                "validation_access_authorized": False,
                "test_access_authorized": False,
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

    _write_json_utf8_atomic(
        args.output,
        report,
    )

    print(
        json.dumps(
            {
                "analysis_version": (
                    report[
                        "analysis_version"
                    ]
                ),
                "valid": True,
                "output": str(
                    args.output
                ),
                "winner": {
                    "candidate_id": (
                        report[
                            "winner"
                        ][
                            "candidate_id"
                        ]
                    ),
                    "candidate_config_fingerprint_sha256": (
                        report[
                            "winner"
                        ][
                            "candidate_config_fingerprint"
                        ][
                            "sha256"
                        ]
                    ),
                },
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