from __future__ import annotations

import hashlib
import json
from typing import Any


CONTRACT_ID = (
    "FROZEN_C04_MODEL_REMEDIATION_PROTOCOL_CONTRACT_V1"
)

SCHEMA_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Authority
# ---------------------------------------------------------------------------

BASE_AUTHORITY_COMMIT = (
    "ad5ec6d9addc9353b655efdb3089896a35676098"
)

SOURCE_MODEL_ID = (
    "C04_FLAT_EXTRA_TREES_CONSTRAINED"
)

SOURCE_MODEL_SHA256 = (
    "48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769"
)

SOURCE_FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

SOURCE_FEATURE_COUNT = 331


# ---------------------------------------------------------------------------
# Existing frozen forward holdout
# ---------------------------------------------------------------------------

FORWARD_HOLDOUT_NAME = (
    "G5_FROZEN_30_MATURED_FORWARD_OUTCOMES"
)

FORWARD_HOLDOUT_SAMPLE_COUNT = 30

FORWARD_HOLDOUT_FIRST_DECISION_TIME_UTC = (
    "2026-09-30T01:55:00Z"
)

FORWARD_HOLDOUT_LAST_DECISION_TIME_UTC = (
    "2026-10-02T05:50:00Z"
)

FORWARD_HOLDOUT_OBSERVATION_LEDGER_SHA256 = (
    "3a3421d3f29cd31cf0b9a2cfec1619cc7df9a3d95df6b30645b3600e3e09c3d3"
)

FORWARD_HOLDOUT_ANCHOR_LEDGER_SHA256 = (
    "1828ba8f1b6a1cfabe20c0ba402bb26f3db1d6e2aabc454055566b2a7ef08bcc"
)

FORWARD_HOLDOUT_OUTCOME_LEDGER_SHA256 = (
    "24fe13c091ac91a134b55d1bcda83b8f9b05e7c13b5c276bfb8649ac4dce84f7"
)

FORWARD_HOLDOUT_ROLE = (
    "EVALUATION_ONLY_IMMUTABLE_HOLDOUT"
)

FORWARD_HOLDOUT_CAN_BE_USED_FOR_TRAINING = False

FORWARD_HOLDOUT_CAN_BE_USED_FOR_REFITTING = False

FORWARD_HOLDOUT_CAN_BE_USED_FOR_CALIBRATION = False

FORWARD_HOLDOUT_CAN_BE_USED_FOR_THRESHOLD_SELECTION = False

FORWARD_HOLDOUT_CAN_BE_USED_FOR_FEATURE_SELECTION = False

FORWARD_HOLDOUT_CAN_BE_USED_FOR_HYPERPARAMETER_SELECTION = False

FORWARD_HOLDOUT_CAN_BE_USED_FOR_MODEL_SELECTION = False

FORWARD_HOLDOUT_CAN_BE_REMOVED_POST_HOC = False

FORWARD_HOLDOUT_CAN_BE_RELABELLED_POST_HOC = False

FORWARD_HOLDOUT_CAN_BE_REWRITTEN = False


# ---------------------------------------------------------------------------
# Diagnostic evidence usage
# ---------------------------------------------------------------------------

DIAGNOSTIC_EVIDENCE_MAY_TRIGGER_REMEDIATION = True

DIAGNOSTIC_EVIDENCE_MAY_DEFINE_BROAD_FAILURE_MODES = True

DIAGNOSTIC_EVIDENCE_MAY_BE_USED_FOR_SAMPLE_SPECIFIC_TUNING = False

DIAGNOSTIC_EVIDENCE_MAY_BE_USED_TO_OPTIMIZE_HOLDOUT_METRICS = False

DIAGNOSTIC_EVIDENCE_MAY_BE_USED_TO_PICK_BEST_HOLDOUT_MODEL = False

KNOWN_BASELINE_DIAGNOSTIC_FINDINGS: tuple[str, ...] = (
    "FORWARD_EXACT_CLASS_ACCURACY_0_30",
    "FORWARD_MACRO_F1_0_219845513963",
    "FORWARD_BALANCED_ACCURACY_0_288888888889",
    "LONG_ARGMAX_DOMINANCE_23_OF_30",
    "NEAR_UNIFORM_FORWARD_PROBABILITY_GEOMETRY",
    "MACRO_PAIRWISE_AUC_0_481203703704",
)


# ---------------------------------------------------------------------------
# Remediation development data isolation
# ---------------------------------------------------------------------------

REMEDIATION_DEVELOPMENT_SCOPE = (
    "PRE_FORWARD_RESEARCH_AND_TRAINING_DATA_ONLY"
)

CURRENT_FORWARD_HOLDOUT_EXCLUDED_FROM_DEVELOPMENT = True

ORIGINAL_VALIDATION_HOLDOUT_CONTAMINATION_ALLOWED = False

ORIGINAL_TEST_HOLDOUT_CONTAMINATION_ALLOWED = False

FUTURE_PROSPECTIVE_FORWARD_DATA_CONTAMINATION_ALLOWED = False

DATA_LEAKAGE_ACROSS_TEMPORAL_BOUNDARIES_ALLOWED = False

FUTURE_DATA_IN_INFERENCE_ALLOWED = False

FORMING_CANDLE_ALLOWED = False


# ---------------------------------------------------------------------------
# Candidate research permissions
# ---------------------------------------------------------------------------

REMEDIATION_RESEARCH_MAY_REOPEN = True

CANDIDATE_RETRAINING_MAY_OCCUR_AFTER_THIS_FREEZE = True

CANDIDATE_REFITTING_MAY_OCCUR_AFTER_THIS_FREEZE = True

CANDIDATE_FEATURE_RESEARCH_MAY_OCCUR_AFTER_THIS_FREEZE = True

CANDIDATE_HYPERPARAMETER_RESEARCH_MAY_OCCUR_AFTER_THIS_FREEZE = True

CANDIDATE_MODEL_RESELECTION_MAY_OCCUR_AFTER_THIS_FREEZE = True

CANDIDATE_PROBABILITY_CALIBRATION_MAY_OCCUR_AFTER_THIS_FREEZE = True

CANDIDATE_THRESHOLD_RESEARCH_MAY_OCCUR_AFTER_THIS_FREEZE = True

OUTCOME_CONTRACT_MODIFICATION_ALLOWED = False

TARGET_SEMANTICS_MODIFICATION_ALLOWED = False


# ---------------------------------------------------------------------------
# Candidate development requirements
# ---------------------------------------------------------------------------

CANDIDATE_DEVELOPMENT_MUST_BE_OFFLINE = True

CANDIDATE_MUST_HAVE_REPRODUCIBLE_ARTIFACT_HASH = True

CANDIDATE_MUST_HAVE_REPRODUCIBLE_FEATURE_CONTRACT = True

CANDIDATE_MUST_HAVE_EXPLICIT_TRAINING_DATA_AUTHORITY = True

CANDIDATE_MUST_HAVE_EXPLICIT_VALIDATION_DATA_AUTHORITY = True

CANDIDATE_MUST_HAVE_EXPLICIT_TEST_DATA_AUTHORITY = True

CANDIDATE_MUST_PASS_OFFLINE_VALIDATION_BEFORE_FORWARD = True

CANDIDATE_MUST_BE_FROZEN_BEFORE_FORWARD = True

CANDIDATE_PARAMETERS_MUST_NOT_CHANGE_DURING_FORWARD = True

CANDIDATE_FEATURES_MUST_NOT_CHANGE_DURING_FORWARD = True

CANDIDATE_THRESHOLDS_MUST_NOT_CHANGE_DURING_FORWARD = True

CANDIDATE_CALIBRATION_MUST_NOT_CHANGE_DURING_FORWARD = True


# ---------------------------------------------------------------------------
# Prospective validation requirements
# ---------------------------------------------------------------------------

PROSPECTIVE_VALIDATION_REQUIRED = True

PROSPECTIVE_DATA_MUST_OCCUR_AFTER_CANDIDATE_FREEZE = True

PROSPECTIVE_EVALUATION_CADENCE = (
    "WEEKLY"
)

PROSPECTIVE_WEEK_TIMEZONE = (
    "UTC"
)

PROSPECTIVE_WEEK_START_DAY = (
    "MONDAY"
)

PROSPECTIVE_WEEK_START_TIME_UTC = (
    "00:00:00"
)

PROSPECTIVE_WEEK_INTERVAL_SEMANTICS = (
    "MONDAY_00_00_UTC_INCLUSIVE_TO_NEXT_MONDAY_00_00_UTC_EXCLUSIVE"
)

PROSPECTIVE_MINIMUM_NEW_WEEKLY_SAMPLE_COUNT = 0

PROSPECTIVE_FIXED_COUNT_WAIT_REQUIRED = False

PROSPECTIVE_MULTI_DAY_FIXED_SAMPLE_COLLECTION_REQUIRED = False

OLD_30_FORWARD_HOLDOUT_MAY_BE_REPORTED_AS_HISTORICAL_BASELINE = True

OLD_30_FORWARD_HOLDOUT_MAY_SELECT_NEW_CANDIDATE = False

NEW_PROSPECTIVE_COHORT_MUST_BE_DISTINCT_FROM_OLD_30 = True


# ---------------------------------------------------------------------------
# Promotion boundary
# ---------------------------------------------------------------------------

PROMOTION_CRITERIA_DEFINED = False

PRODUCTION_PROMOTION_AUTHORIZED = False

PNL_EVALUATION_AUTHORIZED = False

BROKER_EXECUTION_VALIDATION_AUTHORIZED = False

LIVE_AUTHORIZED = False

EXECUTION_AUTHORIZED = False


# ---------------------------------------------------------------------------
# Current gate behavior
# ---------------------------------------------------------------------------

THIS_GATE_PERFORMS_RETRAINING = False

THIS_GATE_PERFORMS_REFITTING = False

THIS_GATE_PERFORMS_CALIBRATION = False

THIS_GATE_PERFORMS_MODEL_RESELECTION = False

THIS_GATE_PERFORMS_FEATURE_RESELECTION = False

THIS_GATE_PERFORMS_HYPERPARAMETER_TUNING = False

THIS_GATE_PERFORMS_THRESHOLD_TUNING = False

THIS_GATE_PERFORMS_PNL_EVALUATION = False

THIS_GATE_ACQUIRES_MARKET_DATA = False

THIS_GATE_WRITES_RUNTIME_LEDGERS = False


def canonical_contract_dict() -> dict[str, Any]:

    return {
        "contract_id": CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "base_authority_commit": BASE_AUTHORITY_COMMIT,
        "source_model_id": SOURCE_MODEL_ID,
        "source_model_sha256": SOURCE_MODEL_SHA256,
        "source_feature_columns_sha256": (
            SOURCE_FEATURE_COLUMNS_SHA256
        ),
        "source_feature_count": (
            SOURCE_FEATURE_COUNT
        ),
        "forward_holdout_name": (
            FORWARD_HOLDOUT_NAME
        ),
        "forward_holdout_sample_count": (
            FORWARD_HOLDOUT_SAMPLE_COUNT
        ),
        "forward_holdout_first_decision_time_utc": (
            FORWARD_HOLDOUT_FIRST_DECISION_TIME_UTC
        ),
        "forward_holdout_last_decision_time_utc": (
            FORWARD_HOLDOUT_LAST_DECISION_TIME_UTC
        ),
        "forward_holdout_observation_ledger_sha256": (
            FORWARD_HOLDOUT_OBSERVATION_LEDGER_SHA256
        ),
        "forward_holdout_anchor_ledger_sha256": (
            FORWARD_HOLDOUT_ANCHOR_LEDGER_SHA256
        ),
        "forward_holdout_outcome_ledger_sha256": (
            FORWARD_HOLDOUT_OUTCOME_LEDGER_SHA256
        ),
        "forward_holdout_role": (
            FORWARD_HOLDOUT_ROLE
        ),
        "forward_holdout_can_be_used_for_training": (
            FORWARD_HOLDOUT_CAN_BE_USED_FOR_TRAINING
        ),
        "forward_holdout_can_be_used_for_refitting": (
            FORWARD_HOLDOUT_CAN_BE_USED_FOR_REFITTING
        ),
        "forward_holdout_can_be_used_for_calibration": (
            FORWARD_HOLDOUT_CAN_BE_USED_FOR_CALIBRATION
        ),
        "forward_holdout_can_be_used_for_threshold_selection": (
            FORWARD_HOLDOUT_CAN_BE_USED_FOR_THRESHOLD_SELECTION
        ),
        "forward_holdout_can_be_used_for_feature_selection": (
            FORWARD_HOLDOUT_CAN_BE_USED_FOR_FEATURE_SELECTION
        ),
        "forward_holdout_can_be_used_for_hyperparameter_selection": (
            FORWARD_HOLDOUT_CAN_BE_USED_FOR_HYPERPARAMETER_SELECTION
        ),
        "forward_holdout_can_be_used_for_model_selection": (
            FORWARD_HOLDOUT_CAN_BE_USED_FOR_MODEL_SELECTION
        ),
        "forward_holdout_can_be_removed_post_hoc": (
            FORWARD_HOLDOUT_CAN_BE_REMOVED_POST_HOC
        ),
        "forward_holdout_can_be_relabelled_post_hoc": (
            FORWARD_HOLDOUT_CAN_BE_RELABELLED_POST_HOC
        ),
        "forward_holdout_can_be_rewritten": (
            FORWARD_HOLDOUT_CAN_BE_REWRITTEN
        ),
        "diagnostic_evidence_may_trigger_remediation": (
            DIAGNOSTIC_EVIDENCE_MAY_TRIGGER_REMEDIATION
        ),
        "diagnostic_evidence_may_define_broad_failure_modes": (
            DIAGNOSTIC_EVIDENCE_MAY_DEFINE_BROAD_FAILURE_MODES
        ),
        "diagnostic_evidence_may_be_used_for_sample_specific_tuning": (
            DIAGNOSTIC_EVIDENCE_MAY_BE_USED_FOR_SAMPLE_SPECIFIC_TUNING
        ),
        "diagnostic_evidence_may_be_used_to_optimize_holdout_metrics": (
            DIAGNOSTIC_EVIDENCE_MAY_BE_USED_TO_OPTIMIZE_HOLDOUT_METRICS
        ),
        "diagnostic_evidence_may_be_used_to_pick_best_holdout_model": (
            DIAGNOSTIC_EVIDENCE_MAY_BE_USED_TO_PICK_BEST_HOLDOUT_MODEL
        ),
        "known_baseline_diagnostic_findings": list(
            KNOWN_BASELINE_DIAGNOSTIC_FINDINGS
        ),
        "remediation_development_scope": (
            REMEDIATION_DEVELOPMENT_SCOPE
        ),
        "current_forward_holdout_excluded_from_development": (
            CURRENT_FORWARD_HOLDOUT_EXCLUDED_FROM_DEVELOPMENT
        ),
        "original_validation_holdout_contamination_allowed": (
            ORIGINAL_VALIDATION_HOLDOUT_CONTAMINATION_ALLOWED
        ),
        "original_test_holdout_contamination_allowed": (
            ORIGINAL_TEST_HOLDOUT_CONTAMINATION_ALLOWED
        ),
        "future_prospective_forward_data_contamination_allowed": (
            FUTURE_PROSPECTIVE_FORWARD_DATA_CONTAMINATION_ALLOWED
        ),
        "data_leakage_across_temporal_boundaries_allowed": (
            DATA_LEAKAGE_ACROSS_TEMPORAL_BOUNDARIES_ALLOWED
        ),
        "future_data_in_inference_allowed": (
            FUTURE_DATA_IN_INFERENCE_ALLOWED
        ),
        "forming_candle_allowed": (
            FORMING_CANDLE_ALLOWED
        ),
        "remediation_research_may_reopen": (
            REMEDIATION_RESEARCH_MAY_REOPEN
        ),
        "candidate_retraining_may_occur_after_this_freeze": (
            CANDIDATE_RETRAINING_MAY_OCCUR_AFTER_THIS_FREEZE
        ),
        "candidate_refitting_may_occur_after_this_freeze": (
            CANDIDATE_REFITTING_MAY_OCCUR_AFTER_THIS_FREEZE
        ),
        "candidate_feature_research_may_occur_after_this_freeze": (
            CANDIDATE_FEATURE_RESEARCH_MAY_OCCUR_AFTER_THIS_FREEZE
        ),
        "candidate_hyperparameter_research_may_occur_after_this_freeze": (
            CANDIDATE_HYPERPARAMETER_RESEARCH_MAY_OCCUR_AFTER_THIS_FREEZE
        ),
        "candidate_model_reselection_may_occur_after_this_freeze": (
            CANDIDATE_MODEL_RESELECTION_MAY_OCCUR_AFTER_THIS_FREEZE
        ),
        "candidate_probability_calibration_may_occur_after_this_freeze": (
            CANDIDATE_PROBABILITY_CALIBRATION_MAY_OCCUR_AFTER_THIS_FREEZE
        ),
        "candidate_threshold_research_may_occur_after_this_freeze": (
            CANDIDATE_THRESHOLD_RESEARCH_MAY_OCCUR_AFTER_THIS_FREEZE
        ),
        "outcome_contract_modification_allowed": (
            OUTCOME_CONTRACT_MODIFICATION_ALLOWED
        ),
        "target_semantics_modification_allowed": (
            TARGET_SEMANTICS_MODIFICATION_ALLOWED
        ),
        "candidate_development_must_be_offline": (
            CANDIDATE_DEVELOPMENT_MUST_BE_OFFLINE
        ),
        "candidate_must_have_reproducible_artifact_hash": (
            CANDIDATE_MUST_HAVE_REPRODUCIBLE_ARTIFACT_HASH
        ),
        "candidate_must_have_reproducible_feature_contract": (
            CANDIDATE_MUST_HAVE_REPRODUCIBLE_FEATURE_CONTRACT
        ),
        "candidate_must_have_explicit_training_data_authority": (
            CANDIDATE_MUST_HAVE_EXPLICIT_TRAINING_DATA_AUTHORITY
        ),
        "candidate_must_have_explicit_validation_data_authority": (
            CANDIDATE_MUST_HAVE_EXPLICIT_VALIDATION_DATA_AUTHORITY
        ),
        "candidate_must_have_explicit_test_data_authority": (
            CANDIDATE_MUST_HAVE_EXPLICIT_TEST_DATA_AUTHORITY
        ),
        "candidate_must_pass_offline_validation_before_forward": (
            CANDIDATE_MUST_PASS_OFFLINE_VALIDATION_BEFORE_FORWARD
        ),
        "candidate_must_be_frozen_before_forward": (
            CANDIDATE_MUST_BE_FROZEN_BEFORE_FORWARD
        ),
        "candidate_parameters_must_not_change_during_forward": (
            CANDIDATE_PARAMETERS_MUST_NOT_CHANGE_DURING_FORWARD
        ),
        "candidate_features_must_not_change_during_forward": (
            CANDIDATE_FEATURES_MUST_NOT_CHANGE_DURING_FORWARD
        ),
        "candidate_thresholds_must_not_change_during_forward": (
            CANDIDATE_THRESHOLDS_MUST_NOT_CHANGE_DURING_FORWARD
        ),
        "candidate_calibration_must_not_change_during_forward": (
            CANDIDATE_CALIBRATION_MUST_NOT_CHANGE_DURING_FORWARD
        ),
        "prospective_validation_required": (
            PROSPECTIVE_VALIDATION_REQUIRED
        ),
        "prospective_data_must_occur_after_candidate_freeze": (
            PROSPECTIVE_DATA_MUST_OCCUR_AFTER_CANDIDATE_FREEZE
        ),
        "prospective_evaluation_cadence": (
            PROSPECTIVE_EVALUATION_CADENCE
        ),
        "prospective_week_timezone": (
            PROSPECTIVE_WEEK_TIMEZONE
        ),
        "prospective_week_start_day": (
            PROSPECTIVE_WEEK_START_DAY
        ),
        "prospective_week_start_time_utc": (
            PROSPECTIVE_WEEK_START_TIME_UTC
        ),
        "prospective_week_interval_semantics": (
            PROSPECTIVE_WEEK_INTERVAL_SEMANTICS
        ),
        "prospective_minimum_new_weekly_sample_count": (
            PROSPECTIVE_MINIMUM_NEW_WEEKLY_SAMPLE_COUNT
        ),
        "prospective_fixed_count_wait_required": (
            PROSPECTIVE_FIXED_COUNT_WAIT_REQUIRED
        ),
        "prospective_multi_day_fixed_sample_collection_required": (
            PROSPECTIVE_MULTI_DAY_FIXED_SAMPLE_COLLECTION_REQUIRED
        ),
        "old_30_forward_holdout_may_be_reported_as_historical_baseline": (
            OLD_30_FORWARD_HOLDOUT_MAY_BE_REPORTED_AS_HISTORICAL_BASELINE
        ),
        "old_30_forward_holdout_may_select_new_candidate": (
            OLD_30_FORWARD_HOLDOUT_MAY_SELECT_NEW_CANDIDATE
        ),
        "new_prospective_cohort_must_be_distinct_from_old_30": (
            NEW_PROSPECTIVE_COHORT_MUST_BE_DISTINCT_FROM_OLD_30
        ),
        "promotion_criteria_defined": (
            PROMOTION_CRITERIA_DEFINED
        ),
        "production_promotion_authorized": (
            PRODUCTION_PROMOTION_AUTHORIZED
        ),
        "pnl_evaluation_authorized": (
            PNL_EVALUATION_AUTHORIZED
        ),
        "broker_execution_validation_authorized": (
            BROKER_EXECUTION_VALIDATION_AUTHORIZED
        ),
        "live_authorized": (
            LIVE_AUTHORIZED
        ),
        "execution_authorized": (
            EXECUTION_AUTHORIZED
        ),
        "this_gate_performs_retraining": (
            THIS_GATE_PERFORMS_RETRAINING
        ),
        "this_gate_performs_refitting": (
            THIS_GATE_PERFORMS_REFITTING
        ),
        "this_gate_performs_calibration": (
            THIS_GATE_PERFORMS_CALIBRATION
        ),
        "this_gate_performs_model_reselection": (
            THIS_GATE_PERFORMS_MODEL_RESELECTION
        ),
        "this_gate_performs_feature_reselection": (
            THIS_GATE_PERFORMS_FEATURE_RESELECTION
        ),
        "this_gate_performs_hyperparameter_tuning": (
            THIS_GATE_PERFORMS_HYPERPARAMETER_TUNING
        ),
        "this_gate_performs_threshold_tuning": (
            THIS_GATE_PERFORMS_THRESHOLD_TUNING
        ),
        "this_gate_performs_pnl_evaluation": (
            THIS_GATE_PERFORMS_PNL_EVALUATION
        ),
        "this_gate_acquires_market_data": (
            THIS_GATE_ACQUIRES_MARKET_DATA
        ),
        "this_gate_writes_runtime_ledgers": (
            THIS_GATE_WRITES_RUNTIME_LEDGERS
        ),
    }


def contract_fingerprint_sha256() -> str:

    payload = json.dumps(
        canonical_contract_dict(),
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        allow_nan=False,
    )

    return hashlib.sha256(
        payload.encode(
            "utf-8"
        )
    ).hexdigest()


CONTRACT_FINGERPRINT_SHA256 = (
    contract_fingerprint_sha256()
)