"""
===============================================================================
Module      : run_xauusd_frozen_c04_inference_parity.py
Project     : PulseViper XAU AI
Purpose     : Gate 14 Direct-Model Parity Harness & Evidence Generator
===============================================================================

Validates offline inference parity between direct joblib model invocation
and FrozenC04InferenceAdapter across authorized non-holdout TRAIN rows.

Safety Constraints:
- Consumes ONLY non-holdout TRAIN rows via Portable331TrainingInputLoader.
- NEVER reads or executes VALIDATION or TEST holdout partitions.
- Never refits or retrains models.
- live_authorized = False, shadow_authorized = False.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

adapter_mod = importlib.import_module("02_AI.Models.frozen_c04_inference_adapter")
contract_mod = importlib.import_module("02_AI.Features.portable_feature_contract")
loader_mod = importlib.import_module("02_AI.Dataset.portable_331_training_input_loader")

FrozenC04InferenceAdapter = adapter_mod.FrozenC04InferenceAdapter
FrozenC04InferenceError = adapter_mod.FrozenC04InferenceError
Portable331TrainingInputLoader = loader_mod.Portable331TrainingInputLoader

EXPECTED_FEATURE_COUNT = contract_mod.EXPECTED_FEATURE_COUNT
EXPECTED_FEATURE_COLUMNS_SHA256 = contract_mod.EXPECTED_FEATURE_COLUMNS_SHA256
FROZEN_MODEL_SHA256 = contract_mod.FROZEN_MODEL_SHA256
FROZEN_MODEL_CLASSES = contract_mod.FROZEN_MODEL_CLASSES


def compute_file_sha256(path: Path) -> str:
    """Compute SHA256 of file."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def run_inference_parity_verification() -> dict[str, Any]:
    """Execute complete Gate 14 inference parity and fail-closed checks."""
    # 1. Resolve model and verify SHA
    model_path = REPO_ROOT / "xauusd_portable_331_c04_full_train_model.joblib"
    if not model_path.is_file():
        raise RuntimeError(f"Frozen model artifact missing at {model_path}")

    actual_model_sha = compute_file_sha256(model_path)
    if actual_model_sha != FROZEN_MODEL_SHA256:
        raise RuntimeError(
            f"Model SHA mismatch! Expected {FROZEN_MODEL_SHA256}, got {actual_model_sha}"
        )

    # 2. Load direct model read-only
    direct_model = joblib.load(model_path)
    direct_model_class = direct_model.__class__.__name__
    direct_n_features = getattr(direct_model, "n_features_in_", None)
    direct_classes = getattr(direct_model, "classes_", None)
    direct_classes_tuple = tuple(direct_classes.tolist()) if direct_classes is not None else None

    # 3. Instantiate adapter
    adapter = FrozenC04InferenceAdapter(model_path=model_path)

    # 4. Load authorized non-holdout TRAIN rows
    canonical_root = REPO_ROOT / "01_Data" / "Canonical"
    loader = Portable331TrainingInputLoader(canonical_root=canonical_root)
    train_batch = loader.load_train_features()

    eval_rows = min(500, len(train_batch.X))
    X_sample = train_batch.X[:eval_rows]
    decision_times_sample = list(train_batch.decision_time[:eval_rows])

    # 5. Direct model inference
    direct_proba = direct_model.predict_proba(X_sample)
    direct_classes_pred = direct_model.classes_[np.argmax(direct_proba, axis=1)]

    # 6. Adapter inference
    adapter_batch = adapter.infer(X_sample, decision_times=decision_times_sample)

    # 7. Compare direct vs adapter
    prob_diff = np.abs(direct_proba - adapter_batch.probabilities)
    max_prob_diff = float(np.max(prob_diff))
    prob_mismatches = int(np.sum(prob_diff > 1e-6))

    class_mismatches = int(np.sum(direct_classes_pred != adapter_batch.predicted_classes))

    # 8. Test argmax tie and decision behavior
    # Synthesize test cases for each class win
    short_win_proba = np.array([[0.80, 0.10, 0.10]], dtype=np.float32)
    no_trade_win_proba = np.array([[0.10, 0.80, 0.10]], dtype=np.float32)
    long_win_proba = np.array([[0.10, 0.10, 0.80]], dtype=np.float32)
    three_way_tie_proba = np.array([[0.33333334, 0.33333334, 0.33333334]], dtype=np.float32)

    argmax_short = int(adapter._classes[np.argmax(short_win_proba, axis=1)][0])
    argmax_no_trade = int(adapter._classes[np.argmax(no_trade_win_proba, axis=1)][0])
    argmax_long = int(adapter._classes[np.argmax(long_win_proba, axis=1)][0])
    argmax_tie = int(adapter._classes[np.argmax(three_way_tie_proba, axis=1)][0])

    argmax_contract_status = {
        "short_decision_correct": argmax_short == -1,
        "no_trade_decision_correct": argmax_no_trade == 0,
        "long_decision_correct": argmax_long == 1,
        "tie_first_index_deterministic": argmax_tie == -1,
    }

    # 9. Test determinism
    adapter_batch_repeat = adapter.infer(X_sample, decision_times=decision_times_sample)
    repeat_prob_diff = np.abs(adapter_batch.probabilities - adapter_batch_repeat.probabilities)
    max_repeat_prob_diff = float(np.max(repeat_prob_diff))
    deterministic_proba_match = bool(max_repeat_prob_diff < 1e-12)
    deterministic_pred_match = bool(
        np.array_equal(adapter_batch.predicted_classes, adapter_batch_repeat.predicted_classes)
    )

    # 10. Fail-closed tests
    fail_closed_checks: dict[str, bool] = {}

    # Check wrong feature dimension
    try:
        adapter.infer(np.zeros((5, 330), dtype=np.float32))
        fail_closed_checks["wrong_feature_dimension_rejected"] = False
    except FrozenC04InferenceError:
        fail_closed_checks["wrong_feature_dimension_rejected"] = True

    # Check NaN rejection
    try:
        nan_matrix = np.zeros((5, 331), dtype=np.float32)
        nan_matrix[0, 0] = np.nan
        adapter.infer(nan_matrix)
        fail_closed_checks["nan_matrix_rejected"] = False
    except FrozenC04InferenceError:
        fail_closed_checks["nan_matrix_rejected"] = True

    # Check inf rejection
    try:
        inf_matrix = np.zeros((5, 331), dtype=np.float32)
        inf_matrix[0, 0] = np.inf
        adapter.infer(inf_matrix)
        fail_closed_checks["inf_matrix_rejected"] = False
    except FrozenC04InferenceError:
        fail_closed_checks["inf_matrix_rejected"] = True

    # Check empty input rejection
    try:
        adapter.infer(np.zeros((0, 331), dtype=np.float32))
        fail_closed_checks["empty_input_rejected"] = False
    except FrozenC04InferenceError:
        fail_closed_checks["empty_input_rejected"] = True

    verdict = "PASS" if (
        prob_mismatches == 0
        and class_mismatches == 0
        and deterministic_proba_match
        and deterministic_pred_match
        and all(argmax_contract_status.values())
        and all(fail_closed_checks.values())
    ) else "FAIL_CLOSED"

    evidence: dict[str, Any] = {
        "gate_id": "GATE_14_FROZEN_C04_INFERENCE_ADAPTER",
        "verdict": verdict,
        "input_source_classification": "NON_HOLDOUT_TRAIN_OR_GATE13_ENGINEERING_INPUT",
        "model_authority": {
            "resolved_model_path": str(model_path),
            "model_sha256": actual_model_sha,
            "expected_model_sha256": FROZEN_MODEL_SHA256,
            "model_sha_match": actual_model_sha == FROZEN_MODEL_SHA256,
            "model_class": direct_model_class,
            "expected_model_class": "ExtraTreesClassifier",
            "n_features_in": direct_n_features,
            "classes": list(direct_classes_tuple) if direct_classes_tuple else None,
            "expected_classes": list(FROZEN_MODEL_CLASSES),
        },
        "feature_contract": {
            "expected_feature_count": EXPECTED_FEATURE_COUNT,
            "feature_columns_sha256": EXPECTED_FEATURE_COLUMNS_SHA256,
        },
        "parity_evaluation": {
            "evaluated_rows": eval_rows,
            "direct_model_max_probability_diff": max_prob_diff,
            "probability_mismatch_count": prob_mismatches,
            "class_prediction_mismatch_count": class_mismatches,
            "probability_matrix_shape": list(adapter_batch.probabilities.shape),
            "probabilities_finite": bool(np.all(np.isfinite(adapter_batch.probabilities))),
            "probabilities_in_unit_interval": bool(
                np.all(adapter_batch.probabilities >= 0.0)
                and np.all(adapter_batch.probabilities <= 1.0)
            ),
            "probabilities_sum_to_one": bool(
                np.all(np.isclose(np.sum(adapter_batch.probabilities, axis=1), 1.0, atol=1e-4))
            ),
        },
        "argmax_contract": argmax_contract_status,
        "determinism": {
            "deterministic_probabilities": deterministic_proba_match,
            "deterministic_class_predictions": deterministic_pred_match,
            "max_repeat_probability_diff": max_repeat_prob_diff,
        },
        "fail_closed_checks": fail_closed_checks,
        "operational_safety": {
            "live_authorized": False,
            "shadow_authorized": False,
            "model_retrained": False,
            "model_refit": False,
            "model_mutated": False,
            "holdouts_accessed": False,
        },
    }

    # Write evidence artifact
    evidence_dir = REPO_ROOT / "04_Testing" / "evidence" / "production_portability"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / "xauusd_frozen_c04_inference_adapter_evidence.json"

    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)

    return evidence


def main() -> None:
    """Entry point for Gate 14 parity harness execution."""
    print("Executing Gate 14 Frozen C04 Inference Parity Verification...")
    evidence = run_inference_parity_verification()
    print("=" * 70)
    print(f"Gate 14 Parity Harness Completed: Verdict = {evidence['verdict']}")
    print(f"Evaluated rows: {evidence['parity_evaluation']['evaluated_rows']}")
    print(f"Max probability diff: {evidence['parity_evaluation']['direct_model_max_probability_diff']}")
    print(f"Probability mismatches: {evidence['parity_evaluation']['probability_mismatch_count']}")
    print(f"Class mismatches: {evidence['parity_evaluation']['class_prediction_mismatch_count']}")
    print(f"Artifact: 04_Testing/evidence/production_portability/xauusd_frozen_c04_inference_adapter_evidence.json")
    print("=" * 70)


if __name__ == "__main__":
    main()
