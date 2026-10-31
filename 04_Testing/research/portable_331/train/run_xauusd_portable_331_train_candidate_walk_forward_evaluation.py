#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping, Sequence

import numpy as np
import sklearn


ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_CANDIDATE_"
    "WALK_FORWARD_EVALUATION_V1"
)

def _find_repo_root(start: Path) -> Path:
    resolved = start.resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "02_AI").is_dir():
            return candidate
    return resolved.parents[4]

REPO_ROOT = _find_repo_root(Path(__file__))
SCRIPT_DIR = Path(__file__).resolve().parent


INTEGRATION_RUNNER_PATH = (
    SCRIPT_DIR
    / "run_xauusd_portable_331_candidate_evaluator_integration.py"
)

EVALUATOR_PATH = (
    SCRIPT_DIR
    / "evaluate_xauusd_portable_331_train_model_candidates.py"
)

REGISTRY_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_train_model_candidate_registry_design.json"
)

PROTOCOL_PATH = (
    REPO_ROOT
    / "04_Testing/evidence/research/portable_331/train/xauusd_portable_331_train_model_research_protocol_design.json"
)

INTEGRATION_ATTESTATION_PATH = (
    REPO_ROOT
    / "04_Testing/evidence/research/portable_331/train/xauusd_portable_331_candidate_evaluator_integration.json"
)

DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_train_model_candidate_walk_forward_evaluation.json"
)

EXPECTED_INTEGRATION_ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_CANDIDATE_"
    "EVALUATOR_INTEGRATION_V1"
)

EXPECTED_REGISTRY_FINGERPRINT = (
    "b8088bb34ce8940f7de5946fbb9b0fd20f40d7cc93a76b76fd7975591f00066c"
)

EXPECTED_PROTOCOL_FINGERPRINT = (
    "69e51e1b249b9da68cbf6f6778a8ae10f9f33f7082a07e5073a1ba731fa1640d"
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

EXPECTED_FEATURE_COUNT = 331
EXPECTED_TRAIN_ROWS = 69966
EXPECTED_FOLD_COUNT = 4
EXPECTED_PURGE_ROWS = 12

EXPECTED_CANDIDATE_IDS = (
    "C01_FLAT_LOGREG_BALANCED_C005",
    "C02_FLAT_LOGREG_BALANCED_C020",
    "C03_FLAT_HGB_SHALLOW",
    "C04_FLAT_EXTRA_TREES_CONSTRAINED",
    "C05_HIER_LOGREG_REGULARIZED",
    "C06_HIER_HGB_LOGREG_CONSTRAINED",
)


class CandidateEvaluationRunError(
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
    ).encode("utf-8")

    return hashlib.sha256(
        encoded
    ).hexdigest()


def _read_text_auto(
    path: Path,
) -> str:
    raw = path.read_bytes()

    if raw.startswith(b"\xff\xfe"):
        return raw.decode("utf-16")

    if raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")

    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")

    return raw.decode("utf-8")


def _load_json_auto(
    path: Path,
) -> dict[str, Any]:
    if not path.is_file():
        raise CandidateEvaluationRunError(
            f"Required JSON file missing: {path}"
        )

    try:
        payload = json.loads(
            _read_text_auto(
                path
            )
        )

    except Exception as exc:
        raise CandidateEvaluationRunError(
            f"Cannot load JSON file: {path}"
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        raise CandidateEvaluationRunError(
            f"Expected JSON object: {path}"
        )

    return payload


def _load_module_from_path(
    path: Path,
    module_name: str,
) -> ModuleType:
    if not path.is_file():
        raise CandidateEvaluationRunError(
            f"Required Python file missing: {path}"
        )

    spec = importlib.util.spec_from_file_location(
        module_name,
        path,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise CandidateEvaluationRunError(
            f"Cannot create module spec: {path}"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    sys.modules[
        module_name
    ] = module

    try:
        spec.loader.exec_module(
            module
        )

    except Exception:
        sys.modules.pop(
            module_name,
            None,
        )
        raise

    return module


def _load_integration_runner() -> ModuleType:
    return _load_module_from_path(
        INTEGRATION_RUNNER_PATH,
        "xauusd_portable_candidate_integration_runtime_for_fit",
    )


def _load_evaluator() -> ModuleType:
    return _load_module_from_path(
        EVALUATOR_PATH,
        "xauusd_portable_candidate_evaluator_runtime_for_fit",
    )


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
        raise CandidateEvaluationRunError(
            f"Required mapping missing: {key}"
        )

    return value


def _validate_integration_attestation(
    attestation: Mapping[str, Any],
) -> None:
    if (
        attestation.get(
            "analysis_version"
        )
        != EXPECTED_INTEGRATION_ANALYSIS_VERSION
    ):
        raise CandidateEvaluationRunError(
            "Unexpected integration attestation version."
        )

    if (
        attestation.get(
            "valid"
        )
        is not True
    ):
        raise CandidateEvaluationRunError(
            "Integration attestation must be valid=true."
        )

    decision = _required_mapping(
        attestation,
        "decision",
    )

    required_decision_values = {
        "integration_confirmed": True,
        "candidate_fit_authorized_in_this_gate": False,
        "candidate_fit_performed": False,
        "candidate_evaluation_metrics_computed": False,
        "winner_selected": False,
        "final_full_train_fit_authorized": False,
        "validation_access_authorized": False,
        "test_access_authorized": False,
        "live_authorized": False,
    }

    for key, expected in required_decision_values.items():
        if decision.get(key) is not expected:
            raise CandidateEvaluationRunError(
                "Integration attestation decision mismatch: "
                f"{key}"
            )

    runtime_import = _required_mapping(
        attestation,
        "runtime_import",
    )

    if (
        runtime_import.get(
            "package_context_confirmed"
        )
        is not True
    ):
        raise CandidateEvaluationRunError(
            "Package-aware loader import was not confirmed."
        )

    artifact_identity = _required_mapping(
        attestation,
        "artifact_identity",
    )

    expected_identity = {
        "dataset_id": EXPECTED_DATASET_ID,
        "dataset_sha256": EXPECTED_DATASET_SHA256,
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "train_input_fingerprint_sha256": (
            EXPECTED_TRAIN_INPUT_FINGERPRINT
        ),
        "train_target_fingerprint_sha256": (
            EXPECTED_TRAIN_TARGET_FINGERPRINT
        ),
        "research_protocol_fingerprint_sha256": (
            EXPECTED_PROTOCOL_FINGERPRINT
        ),
        "candidate_registry_fingerprint_sha256": (
            EXPECTED_REGISTRY_FINGERPRINT
        ),
    }

    for key, expected in expected_identity.items():
        if artifact_identity.get(key) != expected:
            raise CandidateEvaluationRunError(
                "Integration attestation identity mismatch: "
                f"{key}"
            )


def _validate_required_metric_contract(
    protocol: Mapping[str, Any],
    evaluator: ModuleType,
) -> tuple[str, ...]:
    contract = _required_mapping(
        protocol,
        "contract",
    )

    required_metrics = contract.get(
        "required_fold_metrics"
    )

    if not isinstance(
        required_metrics,
        list,
    ):
        raise CandidateEvaluationRunError(
            "Protocol required_fold_metrics missing."
        )

    protocol_metrics = tuple(
        str(value)
        for value in required_metrics
    )

    evaluator_metrics = tuple(
        evaluator.REQUIRED_FOLD_METRICS
    )

    if protocol_metrics != evaluator_metrics:
        raise CandidateEvaluationRunError(
            "Evaluator fold metric contract does not "
            "exactly match frozen research protocol."
        )

    return protocol_metrics


def _validate_runtime_batch(
    batch: Any,
) -> None:
    expected_values = {
        "dataset_id": EXPECTED_DATASET_ID,
        "dataset_sha256": EXPECTED_DATASET_SHA256,
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "train_input_fingerprint_sha256": (
            EXPECTED_TRAIN_INPUT_FINGERPRINT
        ),
        "train_target_fingerprint_sha256": (
            EXPECTED_TRAIN_TARGET_FINGERPRINT
        ),
        "row_count": EXPECTED_TRAIN_ROWS,
    }

    for key, expected in expected_values.items():
        actual = getattr(
            batch,
            key,
            None,
        )

        if actual != expected:
            raise CandidateEvaluationRunError(
                f"Runtime TRAIN batch mismatch: {key}"
            )

    X = np.asarray(
        batch.X
    )

    target_class = np.asarray(
        batch.target_class
    )

    target_tradeable = np.asarray(
        batch.target_tradeable
    )

    if (
        X.shape
        != (
            EXPECTED_TRAIN_ROWS,
            EXPECTED_FEATURE_COUNT,
        )
    ):
        raise CandidateEvaluationRunError(
            "Runtime X shape mismatch."
        )

    if (
        target_class.shape
        != (
            EXPECTED_TRAIN_ROWS,
        )
    ):
        raise CandidateEvaluationRunError(
            "Runtime target_class shape mismatch."
        )

    if (
        target_tradeable.shape
        != (
            EXPECTED_TRAIN_ROWS,
        )
    ):
        raise CandidateEvaluationRunError(
            "Runtime target_tradeable shape mismatch."
        )

    if not np.isfinite(
        X
    ).all():
        raise CandidateEvaluationRunError(
            "Runtime TRAIN matrix contains non-finite values."
        )

    expected_tradeable = (
        target_class != 0
    ).astype(
        np.int8
    )

    if not np.array_equal(
        expected_tradeable,
        target_tradeable.astype(
            np.int8,
            copy=False,
        ),
    ):
        raise CandidateEvaluationRunError(
            "Runtime target linkage mismatch."
        )


def _validate_candidate_reports(
    evaluation: Mapping[str, Any],
    required_metrics: Sequence[str],
) -> None:
    if (
        evaluation.get(
            "registry_fingerprint_sha256"
        )
        != EXPECTED_REGISTRY_FINGERPRINT
    ):
        raise CandidateEvaluationRunError(
            "Evaluation registry fingerprint mismatch."
        )

    if (
        evaluation.get(
            "fold_count"
        )
        != EXPECTED_FOLD_COUNT
    ):
        raise CandidateEvaluationRunError(
            "Evaluation fold_count mismatch."
        )

    reports = evaluation.get(
        "candidate_reports"
    )

    if not isinstance(
        reports,
        list,
    ):
        raise CandidateEvaluationRunError(
            "candidate_reports missing."
        )

    if (
        len(
            reports
        )
        != len(
            EXPECTED_CANDIDATE_IDS
        )
    ):
        raise CandidateEvaluationRunError(
            "Candidate report count mismatch."
        )

    actual_candidate_ids = tuple(
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
        actual_candidate_ids
        != EXPECTED_CANDIDATE_IDS
    ):
        raise CandidateEvaluationRunError(
            "Candidate report order/identity mismatch."
        )

    required_metric_tuple = tuple(
        required_metrics
    )

    for report in reports:
        if not isinstance(
            report,
            Mapping,
        ):
            raise CandidateEvaluationRunError(
                "Candidate report must be a mapping."
            )

        status = report.get(
            "status"
        )

        if status not in (
            "ELIGIBLE",
            "INELIGIBLE",
            "FAILED_CLOSED",
        ):
            raise CandidateEvaluationRunError(
                "Unexpected candidate status: "
                f"{status}"
            )

        fold_reports = report.get(
            "fold_reports"
        )

        if not isinstance(
            fold_reports,
            list,
        ):
            raise CandidateEvaluationRunError(
                "Candidate fold_reports missing."
            )

        if status in (
            "ELIGIBLE",
            "INELIGIBLE",
        ):
            if (
                len(
                    fold_reports
                )
                != EXPECTED_FOLD_COUNT
            ):
                raise CandidateEvaluationRunError(
                    "Completed candidate must have "
                    "exactly four fold reports."
                )

            if not isinstance(
                report.get(
                    "summary"
                ),
                Mapping,
            ):
                raise CandidateEvaluationRunError(
                    "Completed candidate is missing summary."
                )

        if status == "FAILED_CLOSED":
            if report.get(
                "eligible"
            ) is not False:
                raise CandidateEvaluationRunError(
                    "FAILED_CLOSED candidate cannot be eligible."
                )

        for fold_report in fold_reports:
            if not isinstance(
                fold_report,
                Mapping,
            ):
                raise CandidateEvaluationRunError(
                    "Fold report must be a mapping."
                )

            metrics = fold_report.get(
                "metrics"
            )

            if metrics is None:
                continue

            if not isinstance(
                metrics,
                Mapping,
            ):
                raise CandidateEvaluationRunError(
                    "Fold metrics must be a mapping."
                )

            if (
                tuple(
                    metrics.keys()
                )
                != required_metric_tuple
            ):
                raise CandidateEvaluationRunError(
                    "Fold metrics do not exactly match "
                    "frozen protocol metric contract."
                )

            for metric_name, metric_value in metrics.items():
                try:
                    finite = bool(
                        np.isfinite(
                            float(
                                metric_value
                            )
                        )
                    )

                except Exception as exc:
                    raise CandidateEvaluationRunError(
                        "Non-numeric fold metric: "
                        f"{metric_name}"
                    ) from exc

                if not finite:
                    raise CandidateEvaluationRunError(
                        "Non-finite fold metric: "
                        f"{metric_name}"
                    )

    selection = evaluation.get(
        "selection"
    )

    if not isinstance(
        selection,
        Mapping,
    ):
        raise CandidateEvaluationRunError(
            "Evaluation selection missing."
        )

    selection_status = selection.get(
        "status"
    )

    if selection_status not in (
        "NO_WINNER",
        "WINNER_SELECTED_TRAIN_INTERNAL_ONLY",
    ):
        raise CandidateEvaluationRunError(
            "Unexpected selection status."
        )

    winner_candidate_id = selection.get(
        "winner_candidate_id"
    )

    if (
        selection_status
        == "WINNER_SELECTED_TRAIN_INTERNAL_ONLY"
    ):
        eligible_ids = {
            report[
                "candidate_id"
            ]
            for report in reports
            if (
                report.get(
                    "eligible"
                )
                is True
            )
        }

        if (
            winner_candidate_id
            not in eligible_ids
        ):
            raise CandidateEvaluationRunError(
                "Selected winner is not an eligible candidate."
            )

    elif winner_candidate_id is not None:
        raise CandidateEvaluationRunError(
            "NO_WINNER must have winner_candidate_id=None."
        )

    baseline = evaluation.get(
        "diagnostic_baseline"
    )

    if not isinstance(
        baseline,
        Mapping,
    ):
        raise CandidateEvaluationRunError(
            "Diagnostic baseline missing."
        )

    if (
        baseline.get(
            "selectable_as_winner"
        )
        is not False
    ):
        raise CandidateEvaluationRunError(
            "Diagnostic baseline must not be selectable."
        )

    scientific_policy = evaluation.get(
        "scientific_policy"
    )

    if not isinstance(
        scientific_policy,
        Mapping,
    ):
        raise CandidateEvaluationRunError(
            "Evaluation scientific_policy missing."
        )

    if (
        scientific_policy.get(
            "portable_validation_accessed"
        )
        is not False
    ):
        raise CandidateEvaluationRunError(
            "VALIDATION access detected."
        )

    if (
        scientific_policy.get(
            "portable_test_accessed"
        )
        is not False
    ):
        raise CandidateEvaluationRunError(
            "TEST access detected."
        )

    if (
        scientific_policy.get(
            "model_artifacts_written"
        )
        is not False
    ):
        raise CandidateEvaluationRunError(
            "Candidate evaluator must not write model artifacts."
        )


def _candidate_summary(
    evaluation: Mapping[str, Any],
) -> list[dict[str, Any]]:
    reports = evaluation[
        "candidate_reports"
    ]

    result: list[
        dict[str, Any]
    ] = []

    for report in reports:
        summary = report.get(
            "summary"
        )

        row: dict[str, Any] = {
            "candidate_id": report.get(
                "candidate_id"
            ),
            "status": report.get(
                "status"
            ),
            "eligible": report.get(
                "eligible"
            ),
            "failure_type": report.get(
                "failure_type"
            ),
            "failure_reason": report.get(
                "failure_reason"
            ),
        }

        if isinstance(
            summary,
            Mapping,
        ):
            row.update(
                {
                    "worst_fold_directional_macro_f1_short_long": (
                        summary.get(
                            "worst_fold_directional_macro_f1_short_long"
                        )
                    ),
                    "mean_directional_macro_f1_short_long": (
                        summary.get(
                            "mean_directional_macro_f1_short_long"
                        )
                    ),
                    "worst_fold_balanced_accuracy_3class": (
                        summary.get(
                            "worst_fold_balanced_accuracy_3class"
                        )
                    ),
                    "mean_macro_f1_3class": (
                        summary.get(
                            "mean_macro_f1_3class"
                        )
                    ),
                    "std_directional_macro_f1_short_long": (
                        summary.get(
                            "std_directional_macro_f1_short_long"
                        )
                    ),
                    "mean_log_loss_3class": (
                        summary.get(
                            "mean_log_loss_3class"
                        )
                    ),
                    "mean_multiclass_brier": (
                        summary.get(
                            "mean_multiclass_brier"
                        )
                    ),
                    "mean_predicted_trade_coverage": (
                        summary.get(
                            "mean_predicted_trade_coverage"
                        )
                    ),
                    "worst_fold_short_recall": (
                        summary.get(
                            "worst_fold_short_recall"
                        )
                    ),
                    "worst_fold_long_recall": (
                        summary.get(
                            "worst_fold_long_recall"
                        )
                    ),
                }
            )

        result.append(
            row
        )

    return result


def _warning_records(
    caught_warnings: Sequence[Any],
) -> list[dict[str, str]]:
    records: list[
        dict[str, str]
    ] = []

    for warning_record in caught_warnings:
        records.append(
            {
                "category": (
                    warning_record.category.__name__
                ),
                "message": str(
                    warning_record.message
                ),
                "filename": str(
                    warning_record.filename
                ),
                "lineno": str(
                    warning_record.lineno
                ),
            }
        )

    return records


def build_real_candidate_evaluation(
    canonical_root: str | Path = REPO_ROOT,
) -> dict[str, Any]:
    integration_attestation = (
        _load_json_auto(
            INTEGRATION_ATTESTATION_PATH
        )
    )

    _validate_integration_attestation(
        integration_attestation
    )

    integration_runner = (
        _load_integration_runner()
    )

    evaluator = (
        _load_evaluator()
    )

    registry = (
        evaluator.load_frozen_candidate_registry(
            REGISTRY_PATH
        )
    )

    registry_fingerprint = (
        registry[
            "registry_fingerprint"
        ][
            "sha256"
        ]
    )

    if (
        registry_fingerprint
        != EXPECTED_REGISTRY_FINGERPRINT
    ):
        raise CandidateEvaluationRunError(
            "Frozen registry fingerprint mismatch."
        )

    protocol = (
        _load_json_auto(
            PROTOCOL_PATH
        )
    )

    required_metrics = (
        _validate_required_metric_contract(
            protocol,
            evaluator,
        )
    )

    protocol_contract = (
        integration_runner._validate_protocol(
            protocol,
            registry,
        )
    )

    folds = (
        integration_runner._build_folds(
            protocol_contract,
            evaluator,
        )
    )

    if (
        len(
            folds
        )
        != EXPECTED_FOLD_COUNT
    ):
        raise CandidateEvaluationRunError(
            "Frozen fold count mismatch."
        )

    loader_module = (
        integration_runner._load_loader_module()
    )

    loader_class = getattr(
        loader_module,
        "Portable331TrainingInputLoader",
        None,
    )

    if loader_class is None:
        raise CandidateEvaluationRunError(
            "Portable331TrainingInputLoader unavailable."
        )

    loader = loader_class(
        canonical_root
    )

    batch = (
        loader.load_train_supervised()
    )

    integration_runner._validate_supervised_batch(
        batch,
        registry,
    )

    _validate_runtime_batch(
        batch
    )

    evaluator.validate_train_only_inputs(
        batch.X,
        batch.target_class,
        batch.target_tradeable,
        expected_feature_count=EXPECTED_FEATURE_COUNT,
    )

    evaluator.validate_fold_specs(
        folds,
        n_rows=EXPECTED_TRAIN_ROWS,
        required_fold_count=EXPECTED_FOLD_COUNT,
        required_purge_rows=EXPECTED_PURGE_ROWS,
    )

    started_utc = datetime.now(
        timezone.utc
    ).isoformat()

    with warnings.catch_warnings(
        record=True
    ) as caught:
        warnings.simplefilter(
            "always"
        )

        evaluation = (
            evaluator.evaluate_registry_train_only(
                registry,
                batch.X,
                batch.target_class,
                batch.target_tradeable,
                folds,
                include_dummy_baseline=True,
            )
        )

    completed_utc = datetime.now(
        timezone.utc
    ).isoformat()

    _validate_candidate_reports(
        evaluation,
        required_metrics,
    )

    evaluation_fingerprint = (
        _canonical_json_sha256(
            evaluation
        )
    )

    candidate_summary = (
        _candidate_summary(
            evaluation
        )
    )

    selection = evaluation[
        "selection"
    ]

    eligible_count = sum(
        1
        for report in evaluation[
            "candidate_reports"
        ]
        if report.get(
            "eligible"
        )
        is True
    )

    failed_closed_count = sum(
        1
        for report in evaluation[
            "candidate_reports"
        ]
        if report.get(
            "status"
        )
        == "FAILED_CLOSED"
    )

    return {
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "valid": True,
        "research_scope": (
            "FIRST_REAL_FIXED_SIX_CANDIDATE_"
            "FOUR_FOLD_PURGED_WALK_FORWARD_"
            "EVALUATION_INSIDE_FROZEN_TRAIN_ONLY"
        ),
        "runtime": {
            "started_utc": (
                started_utc
            ),
            "completed_utc": (
                completed_utc
            ),
            "python_version": (
                platform.python_version()
            ),
            "numpy_version": (
                np.__version__
            ),
            "sklearn_version": (
                sklearn.__version__
            ),
            "platform": (
                platform.platform()
            ),
        },
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
        },
        "execution_contract": {
            "candidate_count": (
                len(
                    EXPECTED_CANDIDATE_IDS
                )
            ),
            "candidate_ids": list(
                EXPECTED_CANDIDATE_IDS
            ),
            "fold_count": (
                EXPECTED_FOLD_COUNT
            ),
            "purge_rows": (
                EXPECTED_PURGE_ROWS
            ),
            "feature_count": (
                EXPECTED_FEATURE_COUNT
            ),
            "train_rows": (
                EXPECTED_TRAIN_ROWS
            ),
            "required_fold_metrics": list(
                required_metrics
            ),
            "registry_frozen_before_fit": True,
            "threshold_tuning_performed": False,
            "probability_calibration_performed": False,
            "feature_selection_performed": False,
            "portable_validation_accessed": False,
            "portable_test_accessed": False,
        },
        "warnings": (
            _warning_records(
                caught
            )
        ),
        "candidate_summary": (
            candidate_summary
        ),
        "evaluation": (
            evaluation
        ),
        "evaluation_fingerprint": {
            "canonicalization": (
                "JSON_SORT_KEYS_COMPACT_UTF8_SHA256"
            ),
            "sha256": (
                evaluation_fingerprint
            ),
        },
        "decision": {
            "candidate_walk_forward_evaluation_completed": True,
            "eligible_candidate_count": int(
                eligible_count
            ),
            "failed_closed_candidate_count": int(
                failed_closed_count
            ),
            "selection_status": (
                selection.get(
                    "status"
                )
            ),
            "train_internal_winner_candidate_id": (
                selection.get(
                    "winner_candidate_id"
                )
            ),
            "winner_frozen_for_full_train_fit": False,
            "final_full_train_fit_authorized": False,
            "validation_access_authorized": False,
            "test_access_authorized": False,
            "live_authorized": False,
            "next_action": (
                "REVIEW_FIXED_SIX_TRAIN_ONLY_"
                "WALK_FORWARD_RESULTS_AND_FREEZE_"
                "OR_REJECT_TRAIN_INTERNAL_WINNER_"
                "WITHOUT_CHANGING_REGISTRY"
            ),
        },
        "scientific_policy": {
            "real_candidate_fit_performed": True,
            "fit_scope": (
                "FOUR_FROZEN_TRAIN_INTERNAL_FOLDS_ONLY"
            ),
            "candidate_registry_changed": False,
            "hyperparameters_changed_after_results": False,
            "candidate_added_after_results": False,
            "threshold_search_performed": False,
            "probability_calibration_performed": False,
            "feature_selection_performed": False,
            "portable_validation_feature_values_loaded": False,
            "portable_validation_target_values_loaded": False,
            "portable_test_feature_values_loaded": False,
            "portable_test_target_values_loaded": False,
            "final_full_train_fit_performed": False,
            "model_artifacts_written": False,
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

    text = (
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    )

    temporary_path.write_text(
        text,
        encoding="utf-8",
    )

    temporary_path.replace(
        path
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the first real fixed six-candidate "
            "four-fold purged walk-forward evaluation "
            "inside frozen portable TRAIN only."
        )
    )

    parser.add_argument(
        "--execute-frozen-six",
        action="store_true",
        help=(
            "Explicitly authorize the frozen six-candidate "
            "TRAIN-only walk-forward fits."
        ),
    )

    parser.add_argument(
        "--canonical-root",
        type=Path,
        default=REPO_ROOT,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )

    args = parser.parse_args()

    if not args.execute_frozen_six:
        refusal = {
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "valid": False,
            "reason": (
                "EXPLICIT_FROZEN_SIX_EXECUTION_FLAG_REQUIRED"
            ),
            "candidate_fit_performed": False,
            "validation_access_authorized": False,
            "test_access_authorized": False,
            "live_authorized": False,
        }

        print(
            json.dumps(
                refusal,
                indent=2,
                sort_keys=True,
            )
        )

        return 2

    try:
        report = (
            build_real_candidate_evaluation(
                args.canonical_root
            )
        )

    except Exception as exc:
        failure = {
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "valid": False,
            "reason": (
                "XAUUSD_PORTABLE_331_TRAIN_"
                "CANDIDATE_WALK_FORWARD_EVALUATION_FAILED"
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
                "validation_access_authorized": False,
                "test_access_authorized": False,
                "final_full_train_fit_authorized": False,
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

    console_summary = {
        "analysis_version": (
            report[
                "analysis_version"
            ]
        ),
        "valid": True,
        "output": str(
            args.output
        ),
        "candidate_summary": (
            report[
                "candidate_summary"
            ]
        ),
        "evaluation_fingerprint_sha256": (
            report[
                "evaluation_fingerprint"
            ][
                "sha256"
            ]
        ),
        "decision": (
            report[
                "decision"
            ]
        ),
    }

    print(
        json.dumps(
            console_summary,
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )