from __future__ import annotations

import hashlib
import json
from typing import Any


CONTRACT_ID = (
    "FROZEN_C04_REMEDIATION_DATA_AUTHORITY_CONTRACT_V1"
)

SCHEMA_VERSION = "1.0.0"

BASE_AUTHORITY_COMMIT = (
    "144d4359eae9835563f1bf8d01a4dee35ef8c4c2"
)

G7A_CONTRACT_ID = (
    "FROZEN_C04_MODEL_REMEDIATION_PROTOCOL_CONTRACT_V1"
)

G7A_CONTRACT_FINGERPRINT_SHA256 = (
    "3af5ccd2d84950dd37c3dda5f9d5872af5a303e9b8fdf5515c52dc5b92ad6f6c"
)


# ---------------------------------------------------------------------------
# Historical research boundary
# ---------------------------------------------------------------------------

RESEARCH_DATA_CUTOFF_UTC = (
    "2026-08-14T20:55:00Z"
)

DEVELOPMENT_DATA_SCOPE = (
    "IMMUTABLE_PRE_FORWARD_HISTORICAL_RESEARCH_DATA_ONLY"
)

DATASET_DISCOVERY_POLICY = (
    "CONTENT_ADDRESSED_CAUSAL_TRAINING_SNAPSHOT_"
    "AT_OR_BEFORE_RESEARCH_DATA_CUTOFF"
)

POST_RESEARCH_CUTOFF_ROWS_ALLOWED = False

CURRENT_FORWARD_30_ALLOWED = False

FUTURE_PROSPECTIVE_FORWARD_ROWS_ALLOWED = False

RUNTIME_SHADOW_LEDGERS_ALLOWED_AS_DEVELOPMENT_DATA = False


# ---------------------------------------------------------------------------
# Dataset identity requirements
# ---------------------------------------------------------------------------

DATASET_MUST_BE_CONTENT_ADDRESSED = True

DATASET_MUST_HAVE_MANIFEST = True

DATASET_MANIFEST_HASH_REQUIRED = True

DATASET_FILE_HASH_REQUIRED = True

DATASET_ID_REQUIRED = True

DATASET_ROW_COUNT_REQUIRED = True

DATASET_FEATURE_COLUMNS_HASH_REQUIRED = True

DATASET_TARGET_CONTRACT_REQUIRED = True

DATASET_TEMPORAL_COVERAGE_REQUIRED = True

DATASET_SPLIT_DISTRIBUTION_REQUIRED = True

DATASET_IMMUTABILITY_REQUIRED = True


# ---------------------------------------------------------------------------
# Temporal split authority
# ---------------------------------------------------------------------------

SPLIT_POLICY = (
    "PURGED_CHRONOLOGICAL_TRAIN_VALIDATION_TEST"
)

TRAIN_FRACTION = 0.70

VALIDATION_FRACTION = 0.15

TEST_FRACTION = 0.15

SPLIT_PURGE_REQUIRED = True

RANDOM_SHUFFLE_SPLIT_ALLOWED = False

TEMPORAL_ORDER_MUST_BE_MONOTONIC = True

DUPLICATE_DECISION_TIMES_ALLOWED = False

FUTURE_OVERLAP_ACROSS_SPLITS_ALLOWED = False


# ---------------------------------------------------------------------------
# Split roles
# ---------------------------------------------------------------------------

TRAIN_ROLE = (
    "MODEL_FITTING_AND_TRAIN_ONLY_PREPROCESSOR_FITTING"
)

VALIDATION_ROLE = (
    "CANDIDATE_RESEARCH_SELECTION_HYPERPARAMETER_FEATURE_"
    "CALIBRATION_AND_THRESHOLD_RESEARCH"
)

TEST_ROLE = (
    "ONE_SHOT_FINAL_OFFLINE_CONFIRMATION_AFTER_CANDIDATE_SELECTION"
)

MODEL_FIT_ALLOWED_SPLITS: tuple[str, ...] = (
    "TRAIN",
)

PREPROCESSOR_FIT_ALLOWED_SPLITS: tuple[str, ...] = (
    "TRAIN",
)

FEATURE_SELECTION_ALLOWED_SPLITS: tuple[str, ...] = (
    "TRAIN",
    "VALIDATION",
)

HYPERPARAMETER_SELECTION_ALLOWED_SPLITS: tuple[str, ...] = (
    "TRAIN",
    "VALIDATION",
)

MODEL_SELECTION_ALLOWED_SPLITS: tuple[str, ...] = (
    "TRAIN",
    "VALIDATION",
)

CALIBRATION_RESEARCH_ALLOWED_SPLITS: tuple[str, ...] = (
    "TRAIN",
    "VALIDATION",
)

THRESHOLD_RESEARCH_ALLOWED_SPLITS: tuple[str, ...] = (
    "TRAIN",
    "VALIDATION",
)

TEST_MAY_SELECT_MODEL = False

TEST_MAY_SELECT_FEATURES = False

TEST_MAY_SELECT_HYPERPARAMETERS = False

TEST_MAY_SELECT_CALIBRATION = False

TEST_MAY_SELECT_THRESHOLDS = False

TEST_MAY_TRIGGER_ITERATIVE_TUNING = False

TEST_REUSE_AFTER_INSPECTION_FOR_OPTIMIZATION_ALLOWED = False


# ---------------------------------------------------------------------------
# Target authority
# ---------------------------------------------------------------------------

TARGET_CONTRACT = (
    "CLEAN_DIRECTIONAL_EXCURSION_V2"
)

TARGET_PROFIT_ATR = 1.25

TARGET_MAX_ADVERSE_ATR = 0.75

TARGET_CLASS_ORDER: tuple[int, ...] = (
    -1,
    0,
    1,
)

TARGET_CLASS_LABELS: dict[int, str] = {
    -1: "SHORT",
    0: "NO_TRADE",
    1: "LONG",
}

TARGET_CONTRACT_MODIFICATION_ALLOWED = False

TARGET_RELABELING_FOR_FORWARD_FAILURES_ALLOWED = False


# ---------------------------------------------------------------------------
# Causal feature authority
# ---------------------------------------------------------------------------

FORMING_CANDLE_ALLOWED = False

FUTURE_FEATURE_DATA_ALLOWED = False

FUTURE_TARGET_INFORMATION_IN_FEATURES_ALLOWED = False

POST_DECISION_INFORMATION_ALLOWED = False

LEAKAGE_ACROSS_SPLITS_ALLOWED = False

FEATURE_RESEARCH_MUST_REMAIN_CAUSAL = True

FEATURE_CONTRACT_MUST_BE_FROZEN_BEFORE_FORWARD = True


# ---------------------------------------------------------------------------
# Candidate comparison authority
# ---------------------------------------------------------------------------

CANDIDATE_COMPARISON_MUST_USE_SAME_AUTHORIZED_DATA = True

CANDIDATE_COMPARISON_MUST_USE_SAME_TARGET_CONTRACT = True

CANDIDATE_COMPARISON_MUST_USE_SAME_SPLIT_AUTHORITY = True

CANDIDATE_COMPARISON_MAY_USE_VALIDATION_METRICS = True

CANDIDATE_COMPARISON_MAY_USE_TEST_METRICS = False

FORWARD_30_MAY_SELECT_CANDIDATE = False

FORWARD_DIAGNOSTICS_MAY_SELECT_CANDIDATE = False

FORWARD_DIAGNOSTICS_MAY_DEFINE_BROAD_RESEARCH_PROBLEM = True


# ---------------------------------------------------------------------------
# Candidate offline freeze requirements
# ---------------------------------------------------------------------------

SELECTED_CANDIDATE_MUST_BE_FROZEN_BEFORE_TEST = True

SELECTED_CANDIDATE_ARTIFACT_HASH_REQUIRED = True

SELECTED_CANDIDATE_FEATURE_HASH_REQUIRED = True

SELECTED_CANDIDATE_CONFIGURATION_HASH_REQUIRED = True

SELECTED_CANDIDATE_DATA_AUTHORITY_HASH_REQUIRED = True

SELECTED_CANDIDATE_MUST_PASS_ONE_SHOT_TEST = True

FAILED_TEST_MAY_NOT_BE_TUNED_AGAINST_SAME_TEST = True

NEW_RESEARCH_CYCLE_AFTER_TEST_FAILURE_REQUIRES_NEW_AUTHORITY_DECISION = True


# ---------------------------------------------------------------------------
# Forward boundary
# ---------------------------------------------------------------------------

PROSPECTIVE_FORWARD_REQUIRED_AFTER_OFFLINE_FREEZE = True

NEW_FORWARD_DATA_MUST_POSTDATE_CANDIDATE_FREEZE = True

OLD_FORWARD_30_REMAINS_HISTORICAL_BASELINE_ONLY = True

WEEKLY_FORWARD_EVALUATION = True

MINIMUM_NEW_WEEKLY_SAMPLE_COUNT = 0

FIXED_COUNT_FORWARD_WAIT_REQUIRED = False


# ---------------------------------------------------------------------------
# Current gate actions
# ---------------------------------------------------------------------------

THIS_GATE_DISCOVERS_DATASET = False

THIS_GATE_LOADS_TRAINING_ROWS = False

THIS_GATE_TRAINS_MODEL = False

THIS_GATE_FITS_PREPROCESSOR = False

THIS_GATE_SELECTS_FEATURES = False

THIS_GATE_TUNES_HYPERPARAMETERS = False

THIS_GATE_CALIBRATES_PROBABILITIES = False

THIS_GATE_TUNES_THRESHOLDS = False

THIS_GATE_SELECTS_MODEL = False

THIS_GATE_EVALUATES_TEST = False

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
        "g7a_contract_id": G7A_CONTRACT_ID,
        "g7a_contract_fingerprint_sha256": (
            G7A_CONTRACT_FINGERPRINT_SHA256
        ),
        "research_data_cutoff_utc": RESEARCH_DATA_CUTOFF_UTC,
        "development_data_scope": DEVELOPMENT_DATA_SCOPE,
        "dataset_discovery_policy": DATASET_DISCOVERY_POLICY,
        "post_research_cutoff_rows_allowed": (
            POST_RESEARCH_CUTOFF_ROWS_ALLOWED
        ),
        "current_forward_30_allowed": CURRENT_FORWARD_30_ALLOWED,
        "future_prospective_forward_rows_allowed": (
            FUTURE_PROSPECTIVE_FORWARD_ROWS_ALLOWED
        ),
        "runtime_shadow_ledgers_allowed_as_development_data": (
            RUNTIME_SHADOW_LEDGERS_ALLOWED_AS_DEVELOPMENT_DATA
        ),
        "dataset_must_be_content_addressed": (
            DATASET_MUST_BE_CONTENT_ADDRESSED
        ),
        "dataset_must_have_manifest": DATASET_MUST_HAVE_MANIFEST,
        "dataset_manifest_hash_required": (
            DATASET_MANIFEST_HASH_REQUIRED
        ),
        "dataset_file_hash_required": DATASET_FILE_HASH_REQUIRED,
        "dataset_id_required": DATASET_ID_REQUIRED,
        "dataset_row_count_required": DATASET_ROW_COUNT_REQUIRED,
        "dataset_feature_columns_hash_required": (
            DATASET_FEATURE_COLUMNS_HASH_REQUIRED
        ),
        "dataset_target_contract_required": (
            DATASET_TARGET_CONTRACT_REQUIRED
        ),
        "dataset_temporal_coverage_required": (
            DATASET_TEMPORAL_COVERAGE_REQUIRED
        ),
        "dataset_split_distribution_required": (
            DATASET_SPLIT_DISTRIBUTION_REQUIRED
        ),
        "dataset_immutability_required": DATASET_IMMUTABILITY_REQUIRED,
        "split_policy": SPLIT_POLICY,
        "train_fraction": TRAIN_FRACTION,
        "validation_fraction": VALIDATION_FRACTION,
        "test_fraction": TEST_FRACTION,
        "split_purge_required": SPLIT_PURGE_REQUIRED,
        "random_shuffle_split_allowed": RANDOM_SHUFFLE_SPLIT_ALLOWED,
        "temporal_order_must_be_monotonic": (
            TEMPORAL_ORDER_MUST_BE_MONOTONIC
        ),
        "duplicate_decision_times_allowed": (
            DUPLICATE_DECISION_TIMES_ALLOWED
        ),
        "future_overlap_across_splits_allowed": (
            FUTURE_OVERLAP_ACROSS_SPLITS_ALLOWED
        ),
        "train_role": TRAIN_ROLE,
        "validation_role": VALIDATION_ROLE,
        "test_role": TEST_ROLE,
        "model_fit_allowed_splits": list(
            MODEL_FIT_ALLOWED_SPLITS
        ),
        "preprocessor_fit_allowed_splits": list(
            PREPROCESSOR_FIT_ALLOWED_SPLITS
        ),
        "feature_selection_allowed_splits": list(
            FEATURE_SELECTION_ALLOWED_SPLITS
        ),
        "hyperparameter_selection_allowed_splits": list(
            HYPERPARAMETER_SELECTION_ALLOWED_SPLITS
        ),
        "model_selection_allowed_splits": list(
            MODEL_SELECTION_ALLOWED_SPLITS
        ),
        "calibration_research_allowed_splits": list(
            CALIBRATION_RESEARCH_ALLOWED_SPLITS
        ),
        "threshold_research_allowed_splits": list(
            THRESHOLD_RESEARCH_ALLOWED_SPLITS
        ),
        "test_may_select_model": TEST_MAY_SELECT_MODEL,
        "test_may_select_features": TEST_MAY_SELECT_FEATURES,
        "test_may_select_hyperparameters": (
            TEST_MAY_SELECT_HYPERPARAMETERS
        ),
        "test_may_select_calibration": TEST_MAY_SELECT_CALIBRATION,
        "test_may_select_thresholds": TEST_MAY_SELECT_THRESHOLDS,
        "test_may_trigger_iterative_tuning": (
            TEST_MAY_TRIGGER_ITERATIVE_TUNING
        ),
        "test_reuse_after_inspection_for_optimization_allowed": (
            TEST_REUSE_AFTER_INSPECTION_FOR_OPTIMIZATION_ALLOWED
        ),
        "target_contract": TARGET_CONTRACT,
        "target_profit_atr": TARGET_PROFIT_ATR,
        "target_max_adverse_atr": TARGET_MAX_ADVERSE_ATR,
        "target_class_order": list(
            TARGET_CLASS_ORDER
        ),
        "target_class_labels": {
            str(key): value
            for key, value in TARGET_CLASS_LABELS.items()
        },
        "target_contract_modification_allowed": (
            TARGET_CONTRACT_MODIFICATION_ALLOWED
        ),
        "target_relabeling_for_forward_failures_allowed": (
            TARGET_RELABELING_FOR_FORWARD_FAILURES_ALLOWED
        ),
        "forming_candle_allowed": FORMING_CANDLE_ALLOWED,
        "future_feature_data_allowed": FUTURE_FEATURE_DATA_ALLOWED,
        "future_target_information_in_features_allowed": (
            FUTURE_TARGET_INFORMATION_IN_FEATURES_ALLOWED
        ),
        "post_decision_information_allowed": (
            POST_DECISION_INFORMATION_ALLOWED
        ),
        "leakage_across_splits_allowed": LEAKAGE_ACROSS_SPLITS_ALLOWED,
        "feature_research_must_remain_causal": (
            FEATURE_RESEARCH_MUST_REMAIN_CAUSAL
        ),
        "feature_contract_must_be_frozen_before_forward": (
            FEATURE_CONTRACT_MUST_BE_FROZEN_BEFORE_FORWARD
        ),
        "candidate_comparison_must_use_same_authorized_data": (
            CANDIDATE_COMPARISON_MUST_USE_SAME_AUTHORIZED_DATA
        ),
        "candidate_comparison_must_use_same_target_contract": (
            CANDIDATE_COMPARISON_MUST_USE_SAME_TARGET_CONTRACT
        ),
        "candidate_comparison_must_use_same_split_authority": (
            CANDIDATE_COMPARISON_MUST_USE_SAME_SPLIT_AUTHORITY
        ),
        "candidate_comparison_may_use_validation_metrics": (
            CANDIDATE_COMPARISON_MAY_USE_VALIDATION_METRICS
        ),
        "candidate_comparison_may_use_test_metrics": (
            CANDIDATE_COMPARISON_MAY_USE_TEST_METRICS
        ),
        "forward_30_may_select_candidate": (
            FORWARD_30_MAY_SELECT_CANDIDATE
        ),
        "forward_diagnostics_may_select_candidate": (
            FORWARD_DIAGNOSTICS_MAY_SELECT_CANDIDATE
        ),
        "forward_diagnostics_may_define_broad_research_problem": (
            FORWARD_DIAGNOSTICS_MAY_DEFINE_BROAD_RESEARCH_PROBLEM
        ),
        "selected_candidate_must_be_frozen_before_test": (
            SELECTED_CANDIDATE_MUST_BE_FROZEN_BEFORE_TEST
        ),
        "selected_candidate_artifact_hash_required": (
            SELECTED_CANDIDATE_ARTIFACT_HASH_REQUIRED
        ),
        "selected_candidate_feature_hash_required": (
            SELECTED_CANDIDATE_FEATURE_HASH_REQUIRED
        ),
        "selected_candidate_configuration_hash_required": (
            SELECTED_CANDIDATE_CONFIGURATION_HASH_REQUIRED
        ),
        "selected_candidate_data_authority_hash_required": (
            SELECTED_CANDIDATE_DATA_AUTHORITY_HASH_REQUIRED
        ),
        "selected_candidate_must_pass_one_shot_test": (
            SELECTED_CANDIDATE_MUST_PASS_ONE_SHOT_TEST
        ),
        "failed_test_may_not_be_tuned_against_same_test": (
            FAILED_TEST_MAY_NOT_BE_TUNED_AGAINST_SAME_TEST
        ),
        "new_research_cycle_after_test_failure_requires_new_authority_decision": (
            NEW_RESEARCH_CYCLE_AFTER_TEST_FAILURE_REQUIRES_NEW_AUTHORITY_DECISION
        ),
        "prospective_forward_required_after_offline_freeze": (
            PROSPECTIVE_FORWARD_REQUIRED_AFTER_OFFLINE_FREEZE
        ),
        "new_forward_data_must_postdate_candidate_freeze": (
            NEW_FORWARD_DATA_MUST_POSTDATE_CANDIDATE_FREEZE
        ),
        "old_forward_30_remains_historical_baseline_only": (
            OLD_FORWARD_30_REMAINS_HISTORICAL_BASELINE_ONLY
        ),
        "weekly_forward_evaluation": WEEKLY_FORWARD_EVALUATION,
        "minimum_new_weekly_sample_count": (
            MINIMUM_NEW_WEEKLY_SAMPLE_COUNT
        ),
        "fixed_count_forward_wait_required": (
            FIXED_COUNT_FORWARD_WAIT_REQUIRED
        ),
        "this_gate_discovers_dataset": THIS_GATE_DISCOVERS_DATASET,
        "this_gate_loads_training_rows": THIS_GATE_LOADS_TRAINING_ROWS,
        "this_gate_trains_model": THIS_GATE_TRAINS_MODEL,
        "this_gate_fits_preprocessor": THIS_GATE_FITS_PREPROCESSOR,
        "this_gate_selects_features": THIS_GATE_SELECTS_FEATURES,
        "this_gate_tunes_hyperparameters": (
            THIS_GATE_TUNES_HYPERPARAMETERS
        ),
        "this_gate_calibrates_probabilities": (
            THIS_GATE_CALIBRATES_PROBABILITIES
        ),
        "this_gate_tunes_thresholds": THIS_GATE_TUNES_THRESHOLDS,
        "this_gate_selects_model": THIS_GATE_SELECTS_MODEL,
        "this_gate_evaluates_test": THIS_GATE_EVALUATES_TEST,
        "this_gate_acquires_market_data": THIS_GATE_ACQUIRES_MARKET_DATA,
        "this_gate_writes_runtime_ledgers": (
            THIS_GATE_WRITES_RUNTIME_LEDGERS
        ),
        "this_gate_evaluates_pnl": THIS_GATE_EVALUATES_PNL,
        "live_authorized": LIVE_AUTHORIZED,
        "execution_authorized": EXECUTION_AUTHORIZED,
    }


def contract_fingerprint_sha256() -> str:

    payload = json.dumps(
        canonical_contract_dict(),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


CONTRACT_FINGERPRINT_SHA256 = (
    contract_fingerprint_sha256()
)