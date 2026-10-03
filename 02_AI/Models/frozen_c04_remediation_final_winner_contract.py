from __future__ import annotations

import hashlib
import json
from typing import Any


CONTRACT_ID = (
    "FROZEN_C04_REMEDIATION_FINAL_WINNER_CONTRACT_V1"
)

SCHEMA_VERSION = "1.0.0"

BASE_AUTHORITY_COMMIT = (
    "74ba1f9bc074de6bb8e6081758b9f31efa32b066"
)


# =============================================================================
# Upstream authorities
# =============================================================================

G7E_REGISTRY_FINGERPRINT_SHA256 = (
    "4556eb982086da0ea19ab910a30b5ab58788c7e5b7488ef8e3453e46289c0deb"
)

G7FA_ACCESS_CONTRACT_FINGERPRINT_SHA256 = (
    "bfd0cfee283dcb29cff79feff6a5366772a596c9635e470e06d56e70ead74b3e"
)

G7FB_PUBLISHED_COMMIT = (
    "74ba1f9bc074de6bb8e6081758b9f31efa32b066"
)

G7FB_EVIDENCE_RELATIVE_PATH = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_f_b_"
    "remediation_candidate_evaluation.json"
)

G7FB_EVIDENCE_SHA256 = (
    "34a90921c81fdc1f482330b6cc91e7b34a54339295f4d6e272838057078727b4"
)


# =============================================================================
# Frozen data authority
# =============================================================================

DATASET_ID = (
    "portable_cff75b0686383a3ab6f8352b"
)

DATASET_SHA256 = (
    "cff75b0686383a3ab6f8352bfcdcd55308b99b7a4c6edbf7d2e7215f6f33dd07"
)

MANIFEST_SHA256 = (
    "1b8e3599b227c9cbbc6b12f8ab0e275ca4deb4a65839fb626ca90720d59512dc"
)

FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

FEATURE_COUNT = 331

TRAIN_ROWS = 69966

VALIDATION_ROWS = 14983

TEST_ROWS = 14996


# =============================================================================
# Target authority
# =============================================================================

TARGET_CONTRACT = (
    "CLEAN_DIRECTIONAL_EXCURSION_V2"
)

TARGET_PROFIT_ATR = 1.25

TARGET_MAX_ADVERSE_ATR = 0.75

CLASS_ORDER = (
    -1,
    0,
    1,
)


# =============================================================================
# Winner selection authority
# =============================================================================

WINNER_CANDIDATE_ID = (
    "R03_FLAT_EXTRA_TREES_SMOOTH"
)

WINNER_CANDIDATE_FINGERPRINT_SHA256 = (
    "ae644c7272a015c26daeaaa7e655120bd7a3e4d267b2acd0d1f235e10bfa2e5f"
)

WINNER_ROLE = (
    "REMEDIATION_CANDIDATE"
)

WINNER_ARCHITECTURE = (
    "FLAT_3CLASS"
)

WINNER_FAMILY = (
    "EXTRA_TREES"
)

WINNER_FEATURE_SCOPE = (
    "EXACT_331_FROZEN_FEATURES"
)

WINNER_PREDICTION_RULE = (
    "ARGMAX_3CLASS_PROBABILITY"
)

WINNER_PROBABILITY_CLASS_ORDER = (
    -1,
    0,
    1,
)

WINNER_ESTIMATOR_CONFIG: dict[str, Any] = {
    "implementation": (
        "sklearn.ensemble.ExtraTreesClassifier"
    ),
    "bootstrap": False,
    "class_weight": "balanced",
    "max_depth": 8,
    "max_features": 0.50,
    "min_samples_leaf": 50,
    "n_estimators": 750,
    "n_jobs": -1,
    "random_state": 271828,
}

WINNER_PREPROCESSING: dict[str, Any] = {
    "standard_scaler": False,
}

PROBABILITY_CALIBRATION_ENABLED = False

THRESHOLD_TUNING_ENABLED = False

POST_HOC_CLASS_BIAS_ALLOWED = False

RESULTS_DRIVEN_CONFIG_CHANGE_ALLOWED = False

RESULTS_DRIVEN_FEATURE_CHANGE_ALLOWED = False

RESULTS_DRIVEN_CANDIDATE_REPLACEMENT_ALLOWED = False


# =============================================================================
# Frozen validation result
# =============================================================================

VALIDATION_EXACT_CLASS_ACCURACY = (
    0.3640125475538944
)

VALIDATION_MACRO_F1 = (
    0.3601580118907661
)

VALIDATION_BALANCED_ACCURACY = (
    0.377760637941734
)

VALIDATION_MINIMUM_PER_CLASS_RECALL = (
    0.32515085024684587
)

VALIDATION_MULTICLASS_BRIER = (
    0.6648217771177802
)

VALIDATION_MULTICLASS_LOG_LOSS = (
    1.0958580283040205
)

VALIDATION_SHORT_RECALL = (
    0.35235063663075417
)

VALIDATION_NO_TRADE_RECALL = (
    0.32515085024684587
)

VALIDATION_LONG_RECALL = (
    0.4557804269476019
)

VALIDATION_PREDICTION_COUNTS = {
    "SHORT": 4452,
    "NO_TRADE": 4283,
    "LONG": 6248,
}

VALIDATION_OUTCOME_COUNTS = {
    "SHORT": 4084,
    "NO_TRADE": 7292,
    "LONG": 3607,
}

FROZEN_SELECTION_KEY = (
    0.3601580118907661,
    0.377760637941734,
    0.32515085024684587,
    -0.6648217771177802,
    -1.0958580283040205,
    0.3640125475538944,
)

SELECTION_STATUS = (
    "VALIDATION_WINNER_SELECTED"
)

SELECTION_REASON = (
    "FROZEN_G7E_LEXICOGRAPHIC_SELECTION_POLICY"
)


# =============================================================================
# Final winner semantics
# =============================================================================

WINNER_IS_FINAL_FOR_SEALED_TEST = True

WINNER_CONFIG_MAY_CHANGE_BEFORE_TEST = False

WINNER_FEATURES_MAY_CHANGE_BEFORE_TEST = False

WINNER_PREDICTION_RULE_MAY_CHANGE_BEFORE_TEST = False

WINNER_CALIBRATION_MAY_CHANGE_BEFORE_TEST = False

WINNER_THRESHOLDS_MAY_CHANGE_BEFORE_TEST = False

VALIDATION_MAY_BE_REUSED_FOR_FURTHER_SELECTION = False

OLD_FORWARD_30_MAY_BE_USED_FOR_TUNING = False

TEST_ROLE = (
    "SEALED_ONE_SHOT_FINAL_OFFLINE_CONFIRMATION"
)

TEST_VALUES_AUTHORIZED_IN_THIS_GATE = False

TEST_EVALUATION_AUTHORIZED_IN_THIS_GATE = False

TEST_ACCESS_MAY_OCCUR_ONLY_AFTER_THIS_FREEZE_IS_PUBLISHED = True

TEST_FAILURE_MAY_TRIGGER_SAME_TEST_TUNING = False

TEST_FAILURE_MAY_TRIGGER_THRESHOLD_TUNING = False

TEST_FAILURE_MAY_TRIGGER_CALIBRATION = False

TEST_FAILURE_MAY_TRIGGER_FEATURE_SELECTION = False

TEST_FAILURE_MAY_TRIGGER_CANDIDATE_REPLACEMENT = False


# =============================================================================
# Current G7-F-C gate safety
# =============================================================================

THIS_GATE_FREEZES_WINNER_ONLY = True

THIS_GATE_LOADS_TRAIN_VALUES = False

THIS_GATE_LOADS_VALIDATION_VALUES = False

THIS_GATE_LOADS_TEST_VALUES = False

THIS_GATE_TRAINS_MODEL = False

THIS_GATE_FITS_PREPROCESSOR = False

THIS_GATE_REEVALUATES_VALIDATION = False

THIS_GATE_EVALUATES_TEST = False

THIS_GATE_USES_FORWARD_30 = False

THIS_GATE_CALIBRATES_PROBABILITIES = False

THIS_GATE_TUNES_THRESHOLDS = False

THIS_GATE_EVALUATES_PNL = False

THIS_GATE_ACQUIRES_MARKET_DATA = False

THIS_GATE_WRITES_RUNTIME_LEDGERS = False

LIVE_AUTHORIZED = False

EXECUTION_AUTHORIZED = False


def canonical_contract_dict() -> dict[str, Any]:

    return {
        "contract_id": CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),
        "upstream_authorities": {
            "g7e_registry_fingerprint_sha256": (
                G7E_REGISTRY_FINGERPRINT_SHA256
            ),
            "g7fa_access_contract_fingerprint_sha256": (
                G7FA_ACCESS_CONTRACT_FINGERPRINT_SHA256
            ),
            "g7fb_published_commit": (
                G7FB_PUBLISHED_COMMIT
            ),
            "g7fb_evidence_relative_path": (
                G7FB_EVIDENCE_RELATIVE_PATH
            ),
            "g7fb_evidence_sha256": (
                G7FB_EVIDENCE_SHA256
            ),
        },
        "data_authority": {
            "dataset_id": DATASET_ID,
            "dataset_sha256": DATASET_SHA256,
            "manifest_sha256": (
                MANIFEST_SHA256
            ),
            "feature_columns_sha256": (
                FEATURE_COLUMNS_SHA256
            ),
            "feature_count": FEATURE_COUNT,
            "train_rows": TRAIN_ROWS,
            "validation_rows": (
                VALIDATION_ROWS
            ),
            "test_rows": TEST_ROWS,
        },
        "target_authority": {
            "target_contract": (
                TARGET_CONTRACT
            ),
            "profit_atr": TARGET_PROFIT_ATR,
            "max_adverse_atr": (
                TARGET_MAX_ADVERSE_ATR
            ),
            "class_order": list(
                CLASS_ORDER
            ),
        },
        "winner": {
            "candidate_id": (
                WINNER_CANDIDATE_ID
            ),
            "candidate_fingerprint_sha256": (
                WINNER_CANDIDATE_FINGERPRINT_SHA256
            ),
            "role": WINNER_ROLE,
            "architecture": (
                WINNER_ARCHITECTURE
            ),
            "family": WINNER_FAMILY,
            "feature_scope": (
                WINNER_FEATURE_SCOPE
            ),
            "prediction_rule": (
                WINNER_PREDICTION_RULE
            ),
            "probability_class_order": list(
                WINNER_PROBABILITY_CLASS_ORDER
            ),
            "estimator": (
                WINNER_ESTIMATOR_CONFIG
            ),
            "preprocessing": (
                WINNER_PREPROCESSING
            ),
            "probability_calibration_enabled": (
                PROBABILITY_CALIBRATION_ENABLED
            ),
            "threshold_tuning_enabled": (
                THRESHOLD_TUNING_ENABLED
            ),
            "post_hoc_class_bias_allowed": (
                POST_HOC_CLASS_BIAS_ALLOWED
            ),
        },
        "validation_result": {
            "exact_class_accuracy": (
                VALIDATION_EXACT_CLASS_ACCURACY
            ),
            "macro_f1": (
                VALIDATION_MACRO_F1
            ),
            "balanced_accuracy": (
                VALIDATION_BALANCED_ACCURACY
            ),
            "minimum_per_class_recall": (
                VALIDATION_MINIMUM_PER_CLASS_RECALL
            ),
            "multiclass_brier": (
                VALIDATION_MULTICLASS_BRIER
            ),
            "multiclass_log_loss": (
                VALIDATION_MULTICLASS_LOG_LOSS
            ),
            "short_recall": (
                VALIDATION_SHORT_RECALL
            ),
            "no_trade_recall": (
                VALIDATION_NO_TRADE_RECALL
            ),
            "long_recall": (
                VALIDATION_LONG_RECALL
            ),
            "prediction_counts": (
                VALIDATION_PREDICTION_COUNTS
            ),
            "outcome_counts": (
                VALIDATION_OUTCOME_COUNTS
            ),
            "selection_key": list(
                FROZEN_SELECTION_KEY
            ),
            "selection_status": (
                SELECTION_STATUS
            ),
            "selection_reason": (
                SELECTION_REASON
            ),
        },
        "immutability_policy": {
            "final_for_sealed_test": (
                WINNER_IS_FINAL_FOR_SEALED_TEST
            ),
            "config_change_before_test": (
                WINNER_CONFIG_MAY_CHANGE_BEFORE_TEST
            ),
            "feature_change_before_test": (
                WINNER_FEATURES_MAY_CHANGE_BEFORE_TEST
            ),
            "prediction_rule_change_before_test": (
                WINNER_PREDICTION_RULE_MAY_CHANGE_BEFORE_TEST
            ),
            "calibration_change_before_test": (
                WINNER_CALIBRATION_MAY_CHANGE_BEFORE_TEST
            ),
            "threshold_change_before_test": (
                WINNER_THRESHOLDS_MAY_CHANGE_BEFORE_TEST
            ),
            "validation_reuse_for_selection": (
                VALIDATION_MAY_BE_REUSED_FOR_FURTHER_SELECTION
            ),
            "old_forward_30_tuning": (
                OLD_FORWARD_30_MAY_BE_USED_FOR_TUNING
            ),
        },
        "test_policy": {
            "role": TEST_ROLE,
            "values_authorized_in_this_gate": (
                TEST_VALUES_AUTHORIZED_IN_THIS_GATE
            ),
            "evaluation_authorized_in_this_gate": (
                TEST_EVALUATION_AUTHORIZED_IN_THIS_GATE
            ),
            "access_only_after_freeze_published": (
                TEST_ACCESS_MAY_OCCUR_ONLY_AFTER_THIS_FREEZE_IS_PUBLISHED
            ),
            "same_test_tuning_after_failure": (
                TEST_FAILURE_MAY_TRIGGER_SAME_TEST_TUNING
            ),
            "threshold_tuning_after_failure": (
                TEST_FAILURE_MAY_TRIGGER_THRESHOLD_TUNING
            ),
            "calibration_after_failure": (
                TEST_FAILURE_MAY_TRIGGER_CALIBRATION
            ),
            "feature_selection_after_failure": (
                TEST_FAILURE_MAY_TRIGGER_FEATURE_SELECTION
            ),
            "candidate_replacement_after_failure": (
                TEST_FAILURE_MAY_TRIGGER_CANDIDATE_REPLACEMENT
            ),
        },
        "current_gate": {
            "winner_freeze_only": (
                THIS_GATE_FREEZES_WINNER_ONLY
            ),
            "train_values_loaded": (
                THIS_GATE_LOADS_TRAIN_VALUES
            ),
            "validation_values_loaded": (
                THIS_GATE_LOADS_VALIDATION_VALUES
            ),
            "test_values_loaded": (
                THIS_GATE_LOADS_TEST_VALUES
            ),
            "model_training": (
                THIS_GATE_TRAINS_MODEL
            ),
            "preprocessor_fit": (
                THIS_GATE_FITS_PREPROCESSOR
            ),
            "validation_reevaluation": (
                THIS_GATE_REEVALUATES_VALIDATION
            ),
            "test_evaluation": (
                THIS_GATE_EVALUATES_TEST
            ),
            "forward_30_used": (
                THIS_GATE_USES_FORWARD_30
            ),
            "calibration": (
                THIS_GATE_CALIBRATES_PROBABILITIES
            ),
            "threshold_tuning": (
                THIS_GATE_TUNES_THRESHOLDS
            ),
            "pnl_evaluation": (
                THIS_GATE_EVALUATES_PNL
            ),
            "market_data_acquisition": (
                THIS_GATE_ACQUIRES_MARKET_DATA
            ),
            "runtime_ledger_write": (
                THIS_GATE_WRITES_RUNTIME_LEDGERS
            ),
            "live_authorized": (
                LIVE_AUTHORIZED
            ),
            "execution_authorized": (
                EXECUTION_AUTHORIZED
            ),
        },
    }


def contract_fingerprint_sha256() -> str:

    encoded = json.dumps(
        canonical_contract_dict(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        encoded
    ).hexdigest()


CONTRACT_FINGERPRINT_SHA256 = (
    contract_fingerprint_sha256()
)