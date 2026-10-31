from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name(
    "run_xauusd_portable_331_train_candidate_walk_forward_evaluation.py"
)

spec = importlib.util.spec_from_file_location(
    "xauusd_candidate_walk_forward_runner_test_target",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

runner = importlib.util.module_from_spec(
    spec
)

sys.modules[
    spec.name
] = runner

spec.loader.exec_module(
    runner
)


def _valid_attestation():
    return {
        "analysis_version": (
            runner.EXPECTED_INTEGRATION_ANALYSIS_VERSION
        ),
        "valid": True,
        "runtime_import": {
            "package_context_confirmed": True,
        },
        "artifact_identity": {
            "dataset_id": (
                runner.EXPECTED_DATASET_ID
            ),
            "dataset_sha256": (
                runner.EXPECTED_DATASET_SHA256
            ),
            "manifest_sha256": (
                runner.EXPECTED_MANIFEST_SHA256
            ),
            "train_input_fingerprint_sha256": (
                runner.EXPECTED_TRAIN_INPUT_FINGERPRINT
            ),
            "train_target_fingerprint_sha256": (
                runner.EXPECTED_TRAIN_TARGET_FINGERPRINT
            ),
            "research_protocol_fingerprint_sha256": (
                runner.EXPECTED_PROTOCOL_FINGERPRINT
            ),
            "candidate_registry_fingerprint_sha256": (
                runner.EXPECTED_REGISTRY_FINGERPRINT
            ),
        },
        "decision": {
            "integration_confirmed": True,
            "candidate_fit_authorized_in_this_gate": False,
            "candidate_fit_performed": False,
            "candidate_evaluation_metrics_computed": False,
            "winner_selected": False,
            "final_full_train_fit_authorized": False,
            "validation_access_authorized": False,
            "test_access_authorized": False,
            "live_authorized": False,
        },
    }


def _required_metrics():
    return (
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


def _metrics():
    return {
        metric: 0.5
        for metric in _required_metrics()
    }


def _evaluation_report(
    candidate_count: int = 6,
):
    candidate_ids = (
        runner.EXPECTED_CANDIDATE_IDS[
            :candidate_count
        ]
    )

    reports = []

    for candidate_id in candidate_ids:
        reports.append(
            {
                "candidate_id": (
                    candidate_id
                ),
                "status": "ELIGIBLE",
                "eligible": True,
                "failure_type": None,
                "failure_reason": None,
                "fold_reports": [
                    {
                        "fold": {
                            "fold_id": (
                                f"F{fold_index}"
                            ),
                        },
                        "metrics": _metrics(),
                        "eligible": True,
                    }
                    for fold_index in range(
                        1,
                        5,
                    )
                ],
                "summary": {
                    "worst_fold_directional_macro_f1_short_long": 0.5,
                    "mean_directional_macro_f1_short_long": 0.5,
                    "worst_fold_balanced_accuracy_3class": 0.5,
                    "mean_balanced_accuracy_3class": 0.5,
                    "mean_macro_f1_3class": 0.5,
                    "std_directional_macro_f1_short_long": 0.0,
                    "mean_log_loss_3class": 0.5,
                    "mean_multiclass_brier": 0.5,
                    "mean_predicted_trade_coverage": 0.5,
                    "worst_fold_short_recall": 0.5,
                    "worst_fold_long_recall": 0.5,
                },
            }
        )

    return {
        "registry_fingerprint_sha256": (
            runner.EXPECTED_REGISTRY_FINGERPRINT
        ),
        "fold_count": 4,
        "candidate_reports": reports,
        "diagnostic_baseline": {
            "selectable_as_winner": False,
        },
        "selection": {
            "status": (
                "WINNER_SELECTED_TRAIN_INTERNAL_ONLY"
            ),
            "winner_candidate_id": (
                candidate_ids[0]
                if candidate_ids
                else None
            ),
        },
        "scientific_policy": {
            "portable_validation_accessed": False,
            "portable_test_accessed": False,
            "model_artifacts_written": False,
        },
    }


def test_valid_integration_attestation_is_accepted():
    runner._validate_integration_attestation(
        _valid_attestation()
    )


def test_integration_attestation_tamper_fails_closed():
    attestation = (
        _valid_attestation()
    )

    attestation[
        "artifact_identity"
    ][
        "dataset_sha256"
    ] = "tampered"

    with pytest.raises(
        runner.CandidateEvaluationRunError
    ):
        runner._validate_integration_attestation(
            attestation
        )


def test_holdout_authorization_tamper_fails_closed():
    attestation = (
        _valid_attestation()
    )

    attestation[
        "decision"
    ][
        "validation_access_authorized"
    ] = True

    with pytest.raises(
        runner.CandidateEvaluationRunError
    ):
        runner._validate_integration_attestation(
            attestation
        )


def test_complete_candidate_report_contract_is_accepted():
    runner._validate_candidate_reports(
        _evaluation_report(),
        _required_metrics(),
    )


def test_candidate_count_mismatch_fails_closed():
    evaluation = (
        _evaluation_report(
            candidate_count=5
        )
    )

    with pytest.raises(
        runner.CandidateEvaluationRunError
    ):
        runner._validate_candidate_reports(
            evaluation,
            _required_metrics(),
        )


def test_fold_metric_contract_tamper_fails_closed():
    evaluation = (
        _evaluation_report()
    )

    first_metrics = (
        evaluation[
            "candidate_reports"
        ][
            0
        ][
            "fold_reports"
        ][
            0
        ][
            "metrics"
        ]
    )

    first_metrics.pop(
        "multiclass_brier"
    )

    with pytest.raises(
        runner.CandidateEvaluationRunError
    ):
        runner._validate_candidate_reports(
            evaluation,
            _required_metrics(),
        )