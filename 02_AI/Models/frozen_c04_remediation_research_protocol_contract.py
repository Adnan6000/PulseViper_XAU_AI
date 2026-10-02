from __future__ import annotations

import hashlib
import json
from typing import Any


CONTRACT_ID = (
    "FROZEN_C04_REMEDIATION_RESEARCH_PROTOCOL_CONTRACT_V1"
)

SCHEMA_VERSION = "1.0.0"

BASE_AUTHORITY_COMMIT = (
    "03dfb354bdb99a8a334aa6408b9edfd4d21bc096"
)

G7C_CONTRACT_ID = (
    "FROZEN_C04_REMEDIATION_TRAINING_SNAPSHOT_AUTHORITY_V1"
)

G7C_CONTRACT_FINGERPRINT_SHA256 = (
    "11302c424f05aab2fbd640d644b30d3df0b013d3b9e1b559b29e325ee2f99b50"
)


# =============================================================================
# Frozen development data authority
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

TOTAL_ROWS = 99945

TRAIN_ROWS = 69966

VALIDATION_ROWS = 14983

TEST_ROWS = 14996


# =============================================================================
# Frozen target authority
# =============================================================================

TARGET_CONTRACT = (
    "CLEAN_DIRECTIONAL_EXCURSION_V2"
)

TARGET_PROFIT_ATR = 1.25

TARGET_MAX_ADVERSE_ATR = 0.75

TARGET_CLASS_ORDER = (
    -1,
    0,
    1,
)

TARGET_CHANGE_ALLOWED = False

FORWARD_FAILURE_RELABELING_ALLOWED = False


# =============================================================================
# Historical research lineage
# =============================================================================

HISTORICAL_RESEARCH_PROTOCOL_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_MODEL_RESEARCH_PROTOCOL_V1"
)

HISTORICAL_RESEARCH_PROTOCOL_FINGERPRINT_SHA256 = (
    "69e51e1b249b9da68cbf6f6778a8ae10f9f33f7082a07e5073a1ba731fa1640d"
)

HISTORICAL_CANDIDATE_REGISTRY_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_MODEL_CANDIDATE_REGISTRY_V1"
)

HISTORICAL_CANDIDATE_REGISTRY_FINGERPRINT_SHA256 = (
    "b8088bb34ce8940f7de5946fbb9b0fd20f40d7cc93a76b76fd7975591f00066c"
)

HISTORICAL_CANDIDATE_IDS = (
    "C01_FLAT_LOGREG_BALANCED_C005",
    "C02_FLAT_LOGREG_BALANCED_C020",
    "C03_FLAT_HGB_SHALLOW",
    "C04_FLAT_EXTRA_TREES_CONSTRAINED",
    "C05_HIER_LOGREG_REGULARIZED",
    "C06_HIER_HGB_LOGREG_CONSTRAINED",
)

HISTORICAL_WINNER_CANDIDATE_ID = (
    "C04_FLAT_EXTRA_TREES_CONSTRAINED"
)

HISTORICAL_WINNER_IS_REMEDIATION_CONTROL_ONLY = True

HISTORICAL_REGISTRY_AUTOMATICALLY_REUSED_AS_REMEDIATION_REGISTRY = False


# =============================================================================
# Broad forward failure modes
#
# These are descriptive research questions only.
# No individual holdout sample may be inspected or optimized against.
# =============================================================================

BROAD_REMEDIATION_FAILURE_MODES = (
    "WEAK_MULTICLASS_DISCRIMINATION",
    "NEAR_UNIFORM_PROBABILITY_GEOMETRY",
    "SYSTEMATIC_LONG_ARGMAX_UPLIFT",
    "WEAK_CONFIDENCE_ERROR_SEPARATION",
)

FORWARD_DIAGNOSTICS_MAY_DEFINE_BROAD_FAILURE_MODES = True

FORWARD_DIAGNOSTICS_MAY_SELECT_SAMPLE_SPECIFIC_RULES = False

FORWARD_DIAGNOSTICS_MAY_OPTIMIZE_HOLDOUT_METRICS = False


# =============================================================================
# Development split authority
# =============================================================================

TRAIN_ROLE = (
    "MODEL_FITTING_AND_TRAIN_ONLY_PREPROCESSOR_FITTING"
)

VALIDATION_ROLE = (
    "REMEDIATION_RESEARCH_SELECTION_AND_CONFIGURATION"
)

TEST_ROLE = (
    "ONE_SHOT_FINAL_OFFLINE_CONFIRMATION_AFTER_FINAL_CANDIDATE_FREEZE"
)

TRAIN_MAY_BE_USED_FOR_REMEDIATION_RESEARCH = True

VALIDATION_MAY_BE_USED_FOR_REMEDIATION_RESEARCH = True

TEST_MAY_BE_USED_FOR_REMEDIATION_RESEARCH = False

TEST_MAY_BE_USED_BEFORE_FINAL_CANDIDATE_FREEZE = False

TEST_MAY_SELECT_MODEL = False

TEST_MAY_SELECT_FEATURES = False

TEST_MAY_SELECT_HYPERPARAMETERS = False

TEST_MAY_SELECT_CALIBRATION = False

TEST_MAY_SELECT_THRESHOLDS = False

TEST_MAY_TRIGGER_ITERATIVE_TUNING = False


# =============================================================================
# Old forward holdout isolation
# =============================================================================

FORWARD_30_ROLE = (
    "IMMUTABLE_HISTORICAL_EVALUATION_BASELINE_ONLY"
)

FORWARD_30_MAY_BE_USED_FOR_TRAINING = False

FORWARD_30_MAY_BE_USED_FOR_MODEL_SELECTION = False

FORWARD_30_MAY_BE_USED_FOR_FEATURE_SELECTION = False

FORWARD_30_MAY_BE_USED_FOR_HYPERPARAMETER_SELECTION = False

FORWARD_30_MAY_BE_USED_FOR_CALIBRATION = False

FORWARD_30_MAY_BE_USED_FOR_THRESHOLD_SELECTION = False

FORWARD_30_MAY_BE_JOINED_TO_REMEDIATION_DATASET = False


# =============================================================================
# G7-E future remediation registry rules
# =============================================================================

NEW_REMEDIATION_REGISTRY_REQUIRED = True

NEW_REMEDIATION_REGISTRY_GATE = "G7-E"

NEW_REMEDIATION_REGISTRY_MUST_BE_FINITE = True

NEW_REMEDIATION_REGISTRY_MUST_BE_FROZEN_BEFORE_FIRST_FIT = True

NEW_REMEDIATION_REGISTRY_MUST_BE_FINGERPRINTED = True

NEW_REMEDIATION_REGISTRY_MIN_CANDIDATES = 4

NEW_REMEDIATION_REGISTRY_MAX_CANDIDATES = 12

NEW_REMEDIATION_REGISTRY_MUST_INCLUDE_C04_CONTROL = True

RESULTS_DRIVEN_CANDIDATE_ADDITION_AFTER_FIRST_FIT_ALLOWED = False

RESULTS_DRIVEN_HYPERPARAMETER_CHANGE_AFTER_FIRST_FIT_ALLOWED = False

UNBOUNDED_GRID_SEARCH_ALLOWED = False

BAYESIAN_OPTIMIZATION_ALLOWED = False

AUTOML_SEARCH_ALLOWED = False

RANDOM_UNBOUNDED_SEARCH_ALLOWED = False


# =============================================================================
# Remediation research dimensions
#
# These are permissions for later gates, not actions performed in G7-D.
# Exact choices must be frozen in G7-E before fitting.
# =============================================================================

MODEL_ARCHITECTURE_RESEARCH_ALLOWED = True

FEATURE_RESEARCH_ALLOWED = True

HYPERPARAMETER_RESEARCH_ALLOWED = True

PROBABILITY_CALIBRATION_RESEARCH_ALLOWED = True

DECISION_THRESHOLD_RESEARCH_ALLOWED = True

CLASS_BALANCE_RESEARCH_ALLOWED = True

PREPROCESSING_RESEARCH_ALLOWED = True

ALL_RESEARCH_MUST_USE_ONLY_TRAIN_AND_VALIDATION = True

ALL_RESEARCH_CONFIGURATION_MUST_BE_FROZEN_BEFORE_TEST = True


# =============================================================================
# Candidate evaluation requirements
# =============================================================================

REQUIRED_RESEARCH_METRICS = (
    "exact_class_accuracy",
    "macro_f1",
    "balanced_accuracy",
    "per_class_precision",
    "per_class_recall",
    "per_class_f1",
    "prediction_distribution",
    "outcome_distribution",
    "multiclass_brier",
    "multiclass_log_loss",
)

CLASS_SPECIFIC_RECALLS_MUST_REMAIN_VISIBLE = True

PROBABILITY_METRICS_MUST_REMAIN_VISIBLE = True

PREDICTION_DISTRIBUTION_MUST_REMAIN_VISIBLE = True

SINGLE_METRIC_OPTIMIZATION_ONLY_ALLOWED = False

SELECTION_POLICY_MUST_BE_PREDECLARED_BEFORE_FIRST_FIT = True


# =============================================================================
# Offline freeze / test boundary
# =============================================================================

FINAL_OFFLINE_CANDIDATE_MUST_BE_FROZEN_BEFORE_TEST = True

FINAL_MODEL_ARTIFACT_HASH_REQUIRED_BEFORE_TEST = True

FINAL_FEATURE_CONTRACT_HASH_REQUIRED_BEFORE_TEST = True

FINAL_CONFIGURATION_HASH_REQUIRED_BEFORE_TEST = True

FINAL_DATA_AUTHORITY_HASH_REQUIRED_BEFORE_TEST = True

TEST_ACCESS_IS_ONE_SHOT = True

FAILED_TEST_MAY_NOT_BE_TUNED_AGAINST_SAME_TEST = True

FAILED_TEST_REQUIRES_NEW_RESEARCH_AUTHORITY_DECISION = True


# =============================================================================
# Prospective validation boundary
# =============================================================================

NEW_PROSPECTIVE_FORWARD_VALIDATION_REQUIRED = True

NEW_FORWARD_DATA_MUST_POSTDATE_FINAL_CANDIDATE_FREEZE = True

FORWARD_EVALUATION_CADENCE = "WEEKLY"

FORWARD_WEEK_START = "MONDAY_00_00_UTC"

FORWARD_MINIMUM_NEW_WEEKLY_SAMPLE_COUNT = 0

FIXED_COUNT_FORWARD_WAIT_REQUIRED = False

MULTI_DAY_FIXED_SAMPLE_COLLECTION_REQUIRED = False


# =============================================================================
# G7-D current gate behavior
# =============================================================================

THIS_GATE_IS_PROTOCOL_FREEZE_ONLY = True

THIS_GATE_LOADS_TRAIN_FEATURE_VALUES = False

THIS_GATE_LOADS_TRAIN_TARGET_VALUES = False

THIS_GATE_LOADS_VALIDATION_FEATURE_VALUES = False

THIS_GATE_LOADS_VALIDATION_TARGET_VALUES = False

THIS_GATE_LOADS_TEST_FEATURE_VALUES = False

THIS_GATE_LOADS_TEST_TARGET_VALUES = False

THIS_GATE_TRAINS_MODEL = False

THIS_GATE_FITS_PREPROCESSOR = False

THIS_GATE_SELECTS_MODEL = False

THIS_GATE_SELECTS_FEATURES = False

THIS_GATE_TUNES_HYPERPARAMETERS = False

THIS_GATE_CALIBRATES_PROBABILITIES = False

THIS_GATE_TUNES_THRESHOLDS = False

THIS_GATE_WRITES_MODEL_ARTIFACTS = False

THIS_GATE_ACQUIRES_MARKET_DATA = False

THIS_GATE_WRITES_RUNTIME_LEDGERS = False

THIS_GATE_EVALUATES_PNL = False

LIVE_AUTHORIZED = False

EXECUTION_AUTHORIZED = False


def canonical_contract_dict() -> dict[str, Any]:

    return {
        "contract_id": CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "base_authority_commit": BASE_AUTHORITY_COMMIT,
        "g7c_contract_id": G7C_CONTRACT_ID,
        "g7c_contract_fingerprint_sha256": (
            G7C_CONTRACT_FINGERPRINT_SHA256
        ),
        "dataset": {
            "dataset_id": DATASET_ID,
            "dataset_sha256": DATASET_SHA256,
            "manifest_sha256": MANIFEST_SHA256,
            "feature_columns_sha256": FEATURE_COLUMNS_SHA256,
            "feature_count": FEATURE_COUNT,
            "total_rows": TOTAL_ROWS,
            "train_rows": TRAIN_ROWS,
            "validation_rows": VALIDATION_ROWS,
            "test_rows": TEST_ROWS,
        },
        "target": {
            "target_contract": TARGET_CONTRACT,
            "profit_atr": TARGET_PROFIT_ATR,
            "max_adverse_atr": TARGET_MAX_ADVERSE_ATR,
            "class_order": list(TARGET_CLASS_ORDER),
            "target_change_allowed": TARGET_CHANGE_ALLOWED,
            "forward_failure_relabeling_allowed": (
                FORWARD_FAILURE_RELABELING_ALLOWED
            ),
        },
        "historical_lineage": {
            "research_protocol_version": (
                HISTORICAL_RESEARCH_PROTOCOL_VERSION
            ),
            "research_protocol_fingerprint_sha256": (
                HISTORICAL_RESEARCH_PROTOCOL_FINGERPRINT_SHA256
            ),
            "candidate_registry_version": (
                HISTORICAL_CANDIDATE_REGISTRY_VERSION
            ),
            "candidate_registry_fingerprint_sha256": (
                HISTORICAL_CANDIDATE_REGISTRY_FINGERPRINT_SHA256
            ),
            "candidate_ids": list(
                HISTORICAL_CANDIDATE_IDS
            ),
            "historical_winner": (
                HISTORICAL_WINNER_CANDIDATE_ID
            ),
            "historical_winner_is_control_only": (
                HISTORICAL_WINNER_IS_REMEDIATION_CONTROL_ONLY
            ),
            "historical_registry_automatically_reused": (
                HISTORICAL_REGISTRY_AUTOMATICALLY_REUSED_AS_REMEDIATION_REGISTRY
            ),
        },
        "broad_failure_modes": list(
            BROAD_REMEDIATION_FAILURE_MODES
        ),
        "forward_diagnostics_policy": {
            "broad_failure_modes_allowed": (
                FORWARD_DIAGNOSTICS_MAY_DEFINE_BROAD_FAILURE_MODES
            ),
            "sample_specific_rules_allowed": (
                FORWARD_DIAGNOSTICS_MAY_SELECT_SAMPLE_SPECIFIC_RULES
            ),
            "holdout_metric_optimization_allowed": (
                FORWARD_DIAGNOSTICS_MAY_OPTIMIZE_HOLDOUT_METRICS
            ),
        },
        "development_split_authority": {
            "train_role": TRAIN_ROLE,
            "validation_role": VALIDATION_ROLE,
            "test_role": TEST_ROLE,
            "train_research_allowed": (
                TRAIN_MAY_BE_USED_FOR_REMEDIATION_RESEARCH
            ),
            "validation_research_allowed": (
                VALIDATION_MAY_BE_USED_FOR_REMEDIATION_RESEARCH
            ),
            "test_research_allowed": (
                TEST_MAY_BE_USED_FOR_REMEDIATION_RESEARCH
            ),
            "test_before_final_candidate_freeze": (
                TEST_MAY_BE_USED_BEFORE_FINAL_CANDIDATE_FREEZE
            ),
            "test_may_select_model": TEST_MAY_SELECT_MODEL,
            "test_may_select_features": TEST_MAY_SELECT_FEATURES,
            "test_may_select_hyperparameters": (
                TEST_MAY_SELECT_HYPERPARAMETERS
            ),
            "test_may_select_calibration": (
                TEST_MAY_SELECT_CALIBRATION
            ),
            "test_may_select_thresholds": (
                TEST_MAY_SELECT_THRESHOLDS
            ),
            "test_may_trigger_iterative_tuning": (
                TEST_MAY_TRIGGER_ITERATIVE_TUNING
            ),
        },
        "forward_30_isolation": {
            "role": FORWARD_30_ROLE,
            "training": FORWARD_30_MAY_BE_USED_FOR_TRAINING,
            "model_selection": (
                FORWARD_30_MAY_BE_USED_FOR_MODEL_SELECTION
            ),
            "feature_selection": (
                FORWARD_30_MAY_BE_USED_FOR_FEATURE_SELECTION
            ),
            "hyperparameter_selection": (
                FORWARD_30_MAY_BE_USED_FOR_HYPERPARAMETER_SELECTION
            ),
            "calibration": (
                FORWARD_30_MAY_BE_USED_FOR_CALIBRATION
            ),
            "threshold_selection": (
                FORWARD_30_MAY_BE_USED_FOR_THRESHOLD_SELECTION
            ),
            "dataset_join": (
                FORWARD_30_MAY_BE_JOINED_TO_REMEDIATION_DATASET
            ),
        },
        "future_registry": {
            "required": NEW_REMEDIATION_REGISTRY_REQUIRED,
            "gate": NEW_REMEDIATION_REGISTRY_GATE,
            "finite": NEW_REMEDIATION_REGISTRY_MUST_BE_FINITE,
            "freeze_before_fit": (
                NEW_REMEDIATION_REGISTRY_MUST_BE_FROZEN_BEFORE_FIRST_FIT
            ),
            "fingerprint_required": (
                NEW_REMEDIATION_REGISTRY_MUST_BE_FINGERPRINTED
            ),
            "minimum_candidates": (
                NEW_REMEDIATION_REGISTRY_MIN_CANDIDATES
            ),
            "maximum_candidates": (
                NEW_REMEDIATION_REGISTRY_MAX_CANDIDATES
            ),
            "c04_control_required": (
                NEW_REMEDIATION_REGISTRY_MUST_INCLUDE_C04_CONTROL
            ),
            "results_driven_candidate_addition": (
                RESULTS_DRIVEN_CANDIDATE_ADDITION_AFTER_FIRST_FIT_ALLOWED
            ),
            "results_driven_hyperparameter_change": (
                RESULTS_DRIVEN_HYPERPARAMETER_CHANGE_AFTER_FIRST_FIT_ALLOWED
            ),
            "unbounded_grid_search": (
                UNBOUNDED_GRID_SEARCH_ALLOWED
            ),
            "bayesian_optimization": (
                BAYESIAN_OPTIMIZATION_ALLOWED
            ),
            "automl_search": AUTOML_SEARCH_ALLOWED,
            "random_unbounded_search": (
                RANDOM_UNBOUNDED_SEARCH_ALLOWED
            ),
        },
        "research_dimensions": {
            "architecture": MODEL_ARCHITECTURE_RESEARCH_ALLOWED,
            "feature": FEATURE_RESEARCH_ALLOWED,
            "hyperparameter": HYPERPARAMETER_RESEARCH_ALLOWED,
            "calibration": (
                PROBABILITY_CALIBRATION_RESEARCH_ALLOWED
            ),
            "decision_threshold": (
                DECISION_THRESHOLD_RESEARCH_ALLOWED
            ),
            "class_balance": CLASS_BALANCE_RESEARCH_ALLOWED,
            "preprocessing": PREPROCESSING_RESEARCH_ALLOWED,
            "train_validation_only": (
                ALL_RESEARCH_MUST_USE_ONLY_TRAIN_AND_VALIDATION
            ),
            "freeze_before_test": (
                ALL_RESEARCH_CONFIGURATION_MUST_BE_FROZEN_BEFORE_TEST
            ),
        },
        "required_research_metrics": list(
            REQUIRED_RESEARCH_METRICS
        ),
        "metric_policy": {
            "class_specific_recalls_visible": (
                CLASS_SPECIFIC_RECALLS_MUST_REMAIN_VISIBLE
            ),
            "probability_metrics_visible": (
                PROBABILITY_METRICS_MUST_REMAIN_VISIBLE
            ),
            "prediction_distribution_visible": (
                PREDICTION_DISTRIBUTION_MUST_REMAIN_VISIBLE
            ),
            "single_metric_only_allowed": (
                SINGLE_METRIC_OPTIMIZATION_ONLY_ALLOWED
            ),
            "selection_policy_predeclared": (
                SELECTION_POLICY_MUST_BE_PREDECLARED_BEFORE_FIRST_FIT
            ),
        },
        "offline_test_boundary": {
            "candidate_frozen_before_test": (
                FINAL_OFFLINE_CANDIDATE_MUST_BE_FROZEN_BEFORE_TEST
            ),
            "model_hash_required": (
                FINAL_MODEL_ARTIFACT_HASH_REQUIRED_BEFORE_TEST
            ),
            "feature_hash_required": (
                FINAL_FEATURE_CONTRACT_HASH_REQUIRED_BEFORE_TEST
            ),
            "configuration_hash_required": (
                FINAL_CONFIGURATION_HASH_REQUIRED_BEFORE_TEST
            ),
            "data_authority_hash_required": (
                FINAL_DATA_AUTHORITY_HASH_REQUIRED_BEFORE_TEST
            ),
            "one_shot": TEST_ACCESS_IS_ONE_SHOT,
            "failed_test_no_same_test_tuning": (
                FAILED_TEST_MAY_NOT_BE_TUNED_AGAINST_SAME_TEST
            ),
            "failed_test_requires_new_authority": (
                FAILED_TEST_REQUIRES_NEW_RESEARCH_AUTHORITY_DECISION
            ),
        },
        "prospective_boundary": {
            "required": NEW_PROSPECTIVE_FORWARD_VALIDATION_REQUIRED,
            "postdates_candidate_freeze": (
                NEW_FORWARD_DATA_MUST_POSTDATE_FINAL_CANDIDATE_FREEZE
            ),
            "cadence": FORWARD_EVALUATION_CADENCE,
            "week_start": FORWARD_WEEK_START,
            "minimum_new_weekly_sample_count": (
                FORWARD_MINIMUM_NEW_WEEKLY_SAMPLE_COUNT
            ),
            "fixed_count_wait": FIXED_COUNT_FORWARD_WAIT_REQUIRED,
            "multi_day_fixed_collection": (
                MULTI_DAY_FIXED_SAMPLE_COLLECTION_REQUIRED
            ),
        },
        "current_gate": {
            "protocol_freeze_only": (
                THIS_GATE_IS_PROTOCOL_FREEZE_ONLY
            ),
            "train_features_loaded": (
                THIS_GATE_LOADS_TRAIN_FEATURE_VALUES
            ),
            "train_targets_loaded": (
                THIS_GATE_LOADS_TRAIN_TARGET_VALUES
            ),
            "validation_features_loaded": (
                THIS_GATE_LOADS_VALIDATION_FEATURE_VALUES
            ),
            "validation_targets_loaded": (
                THIS_GATE_LOADS_VALIDATION_TARGET_VALUES
            ),
            "test_features_loaded": (
                THIS_GATE_LOADS_TEST_FEATURE_VALUES
            ),
            "test_targets_loaded": (
                THIS_GATE_LOADS_TEST_TARGET_VALUES
            ),
            "model_training": THIS_GATE_TRAINS_MODEL,
            "preprocessor_fit": THIS_GATE_FITS_PREPROCESSOR,
            "model_selection": THIS_GATE_SELECTS_MODEL,
            "feature_selection": THIS_GATE_SELECTS_FEATURES,
            "hyperparameter_tuning": (
                THIS_GATE_TUNES_HYPERPARAMETERS
            ),
            "probability_calibration": (
                THIS_GATE_CALIBRATES_PROBABILITIES
            ),
            "threshold_tuning": THIS_GATE_TUNES_THRESHOLDS,
            "model_artifact_write": (
                THIS_GATE_WRITES_MODEL_ARTIFACTS
            ),
            "market_data_acquisition": (
                THIS_GATE_ACQUIRES_MARKET_DATA
            ),
            "runtime_ledger_write": (
                THIS_GATE_WRITES_RUNTIME_LEDGERS
            ),
            "pnl_evaluation": THIS_GATE_EVALUATES_PNL,
            "live_authorized": LIVE_AUTHORIZED,
            "execution_authorized": EXECUTION_AUTHORIZED,
        },
    }


def contract_fingerprint_sha256() -> str:

    payload = json.dumps(
        canonical_contract_dict(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")

    return hashlib.sha256(
        payload
    ).hexdigest()


CONTRACT_FINGERPRINT_SHA256 = (
    contract_fingerprint_sha256()
)