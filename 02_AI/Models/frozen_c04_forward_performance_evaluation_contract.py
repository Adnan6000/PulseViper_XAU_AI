from __future__ import annotations

import hashlib
import json
from typing import Any


CONTRACT_ID = (
    "FROZEN_C04_FORWARD_PERFORMANCE_EVALUATION_CONTRACT_V1"
)

SCHEMA_VERSION = "1.0.0"

BASELINE_G5_AUTHORITY_COMMIT = (
    "c82abaf6008e9239cecae5fef4fde24936ad6358"
)

BASELINE_MATURED_OUTCOME_COUNT = 30

CLASS_ORDER: tuple[int, ...] = (
    -1,
    0,
    1,
)

CLASS_LABELS: dict[int, str] = {
    -1: "SHORT",
    0: "NO_TRADE",
    1: "LONG",
}


# ---------------------------------------------------------------------------
# Weekly evaluation cadence
# ---------------------------------------------------------------------------

EVALUATION_CADENCE = "WEEKLY"

WEEK_TIMEZONE = "UTC"

WEEK_START_DAY = "MONDAY"

WEEK_START_TIME_UTC = "00:00:00"

WEEK_INTERVAL_SEMANTICS = (
    "MONDAY_00_00_UTC_INCLUSIVE_TO_NEXT_MONDAY_00_00_UTC_EXCLUSIVE"
)

WEEKLY_SAMPLE_POLICY = (
    "EVALUATE_ALL_ELIGIBLE_MATURED_OUTCOMES_AVAILABLE_FOR_THE_WEEKLY_COHORT"
)

MINIMUM_NEW_WEEKLY_SAMPLE_COUNT = 0

FIXED_COUNT_WAIT_REQUIRED = False

MULTI_DAY_FIXED_SAMPLE_COLLECTION_REQUIRED = False


# ---------------------------------------------------------------------------
# Cohort authority
# ---------------------------------------------------------------------------

WEEKLY_COHORT_TIMESTAMP_FIELD = (
    "decision_time_utc"
)

CUMULATIVE_COHORT_POLICY = (
    "ALL_ELIGIBLE_MATURED_FORWARD_OUTCOMES_UP_TO_WEEKLY_CUTOFF"
)

BASELINE_POLICY = (
    "G5_FROZEN_30_MATURED_FORWARD_OUTCOMES"
)


# ---------------------------------------------------------------------------
# Frozen metrics
# ---------------------------------------------------------------------------

METRIC_EXACT_CLASS_ACCURACY = (
    "EXACT_CLASS_ACCURACY"
)

METRIC_CONFUSION_MATRIX = (
    "CONFUSION_MATRIX"
)

METRIC_PER_CLASS_PRECISION = (
    "PER_CLASS_PRECISION"
)

METRIC_PER_CLASS_RECALL = (
    "PER_CLASS_RECALL"
)

METRIC_PER_CLASS_F1 = (
    "PER_CLASS_F1"
)

METRIC_MACRO_F1 = (
    "MACRO_F1"
)

METRIC_BALANCED_ACCURACY = (
    "BALANCED_ACCURACY"
)

METRIC_PREDICTION_DISTRIBUTION = (
    "PREDICTION_DISTRIBUTION"
)

METRIC_OUTCOME_DISTRIBUTION = (
    "OUTCOME_DISTRIBUTION"
)

METRIC_MULTICLASS_BRIER_SCORE = (
    "MULTICLASS_BRIER_SCORE"
)

METRIC_MULTICLASS_LOG_LOSS = (
    "MULTICLASS_LOG_LOSS"
)

METRIC_SAMPLE_COUNT = (
    "SAMPLE_COUNT"
)

METRIC_COVERAGE_PERIOD = (
    "COVERAGE_PERIOD"
)


FROZEN_METRICS: tuple[str, ...] = (
    METRIC_EXACT_CLASS_ACCURACY,
    METRIC_CONFUSION_MATRIX,
    METRIC_PER_CLASS_PRECISION,
    METRIC_PER_CLASS_RECALL,
    METRIC_PER_CLASS_F1,
    METRIC_MACRO_F1,
    METRIC_BALANCED_ACCURACY,
    METRIC_PREDICTION_DISTRIBUTION,
    METRIC_OUTCOME_DISTRIBUTION,
    METRIC_MULTICLASS_BRIER_SCORE,
    METRIC_MULTICLASS_LOG_LOSS,
    METRIC_SAMPLE_COUNT,
    METRIC_COVERAGE_PERIOD,
)


# ---------------------------------------------------------------------------
# Metric semantics
# ---------------------------------------------------------------------------

CONFUSION_MATRIX_ROW_SEMANTICS = (
    "TRUE_OUTCOME_CLASS"
)

CONFUSION_MATRIX_COLUMN_SEMANTICS = (
    "PREDICTED_CLASS"
)

ZERO_DIVISION_POLICY = 0.0

EXACT_CLASS_ACCURACY_FORMULA = (
    "MEAN(PREDICTED_CLASS_EQUALS_OUTCOME_CLASS)"
)

PER_CLASS_PRECISION_FORMULA = (
    "TP_DIVIDED_BY_TP_PLUS_FP"
)

PER_CLASS_RECALL_FORMULA = (
    "TP_DIVIDED_BY_TP_PLUS_FN"
)

PER_CLASS_F1_FORMULA = (
    "2_TIMES_PRECISION_TIMES_RECALL_DIVIDED_BY_PRECISION_PLUS_RECALL"
)

MACRO_F1_FORMULA = (
    "ARITHMETIC_MEAN_OF_F1_OVER_FROZEN_CLASS_ORDER"
)

BALANCED_ACCURACY_FORMULA = (
    "ARITHMETIC_MEAN_OF_RECALL_OVER_FROZEN_CLASS_ORDER"
)

DISTRIBUTION_SEMANTICS = (
    "REPORT_COUNTS_AND_PROPORTIONS_FOR_EACH_FROZEN_CLASS"
)


# ---------------------------------------------------------------------------
# Probability metric semantics
# ---------------------------------------------------------------------------

PROBABILITY_COLUMN_ORDER: tuple[str, ...] = (
    "probability_short",
    "probability_no_trade",
    "probability_long",
)

PROBABILITY_SUM_TOLERANCE = 1e-9

BRIER_SCORE_FORMULA = (
    "MEAN_OVER_SAMPLES_OF_SUM_OVER_CLASSES_OF_"
    "SQUARED_PREDICTED_PROBABILITY_MINUS_ONE_HOT_OUTCOME"
)

LOG_LOSS_EPSILON = 1e-15

LOG_LOSS_NUMERICAL_POLICY = (
    "CLIP_EACH_CLASS_PROBABILITY_TO_EPSILON_AND_ONE_MINUS_EPSILON_"
    "THEN_RENORMALIZE_ROW_TO_SUM_ONE"
)

LOG_LOSS_FORMULA = (
    "NEGATIVE_MEAN_LOG_PROBABILITY_ASSIGNED_TO_TRUE_OUTCOME_CLASS"
)

PROBABILITY_CALIBRATION_ALLOWED = False


# ---------------------------------------------------------------------------
# Scientific isolation
# ---------------------------------------------------------------------------

RETRAINING_ALLOWED = False

REFITTING_ALLOWED = False

MODEL_RESELECTION_ALLOWED = False

THRESHOLD_TUNING_ALLOWED = False

FEATURE_RESELECTION_ALLOWED = False

HYPERPARAMETER_TUNING_ALLOWED = False

OUTCOME_CONTRACT_MODIFICATION_ALLOWED = False

PERFORMANCE_BASED_DATA_EXCLUSION_ALLOWED = False

POST_HOC_SAMPLE_REMOVAL_ALLOWED = False


# ---------------------------------------------------------------------------
# Promotion / execution boundary
# ---------------------------------------------------------------------------

PASS_FAIL_THRESHOLD_DEFINED = False

PRODUCTION_PROMOTION_DECISION_AUTHORIZED = False

PNL_EVALUATION_AUTHORIZED = False

LIVE_AUTHORIZED = False

EXECUTION_AUTHORIZED = False


def canonical_contract_dict() -> dict[str, Any]:

    return {
        "contract_id": CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "baseline_g5_authority_commit": (
            BASELINE_G5_AUTHORITY_COMMIT
        ),
        "baseline_matured_outcome_count": (
            BASELINE_MATURED_OUTCOME_COUNT
        ),
        "class_order": list(
            CLASS_ORDER
        ),
        "class_labels": {
            str(k): v
            for k, v in CLASS_LABELS.items()
        },
        "evaluation_cadence": (
            EVALUATION_CADENCE
        ),
        "week_timezone": (
            WEEK_TIMEZONE
        ),
        "week_start_day": (
            WEEK_START_DAY
        ),
        "week_start_time_utc": (
            WEEK_START_TIME_UTC
        ),
        "week_interval_semantics": (
            WEEK_INTERVAL_SEMANTICS
        ),
        "weekly_sample_policy": (
            WEEKLY_SAMPLE_POLICY
        ),
        "minimum_new_weekly_sample_count": (
            MINIMUM_NEW_WEEKLY_SAMPLE_COUNT
        ),
        "fixed_count_wait_required": (
            FIXED_COUNT_WAIT_REQUIRED
        ),
        "multi_day_fixed_sample_collection_required": (
            MULTI_DAY_FIXED_SAMPLE_COLLECTION_REQUIRED
        ),
        "weekly_cohort_timestamp_field": (
            WEEKLY_COHORT_TIMESTAMP_FIELD
        ),
        "cumulative_cohort_policy": (
            CUMULATIVE_COHORT_POLICY
        ),
        "baseline_policy": (
            BASELINE_POLICY
        ),
        "frozen_metrics": list(
            FROZEN_METRICS
        ),
        "confusion_matrix_row_semantics": (
            CONFUSION_MATRIX_ROW_SEMANTICS
        ),
        "confusion_matrix_column_semantics": (
            CONFUSION_MATRIX_COLUMN_SEMANTICS
        ),
        "zero_division_policy": (
            ZERO_DIVISION_POLICY
        ),
        "exact_class_accuracy_formula": (
            EXACT_CLASS_ACCURACY_FORMULA
        ),
        "per_class_precision_formula": (
            PER_CLASS_PRECISION_FORMULA
        ),
        "per_class_recall_formula": (
            PER_CLASS_RECALL_FORMULA
        ),
        "per_class_f1_formula": (
            PER_CLASS_F1_FORMULA
        ),
        "macro_f1_formula": (
            MACRO_F1_FORMULA
        ),
        "balanced_accuracy_formula": (
            BALANCED_ACCURACY_FORMULA
        ),
        "distribution_semantics": (
            DISTRIBUTION_SEMANTICS
        ),
        "probability_column_order": list(
            PROBABILITY_COLUMN_ORDER
        ),
        "probability_sum_tolerance": (
            PROBABILITY_SUM_TOLERANCE
        ),
        "brier_score_formula": (
            BRIER_SCORE_FORMULA
        ),
        "log_loss_epsilon": (
            LOG_LOSS_EPSILON
        ),
        "log_loss_numerical_policy": (
            LOG_LOSS_NUMERICAL_POLICY
        ),
        "log_loss_formula": (
            LOG_LOSS_FORMULA
        ),
        "probability_calibration_allowed": (
            PROBABILITY_CALIBRATION_ALLOWED
        ),
        "retraining_allowed": (
            RETRAINING_ALLOWED
        ),
        "refitting_allowed": (
            REFITTING_ALLOWED
        ),
        "model_reselection_allowed": (
            MODEL_RESELECTION_ALLOWED
        ),
        "threshold_tuning_allowed": (
            THRESHOLD_TUNING_ALLOWED
        ),
        "feature_reselection_allowed": (
            FEATURE_RESELECTION_ALLOWED
        ),
        "hyperparameter_tuning_allowed": (
            HYPERPARAMETER_TUNING_ALLOWED
        ),
        "outcome_contract_modification_allowed": (
            OUTCOME_CONTRACT_MODIFICATION_ALLOWED
        ),
        "performance_based_data_exclusion_allowed": (
            PERFORMANCE_BASED_DATA_EXCLUSION_ALLOWED
        ),
        "post_hoc_sample_removal_allowed": (
            POST_HOC_SAMPLE_REMOVAL_ALLOWED
        ),
        "pass_fail_threshold_defined": (
            PASS_FAIL_THRESHOLD_DEFINED
        ),
        "production_promotion_decision_authorized": (
            PRODUCTION_PROMOTION_DECISION_AUTHORIZED
        ),
        "pnl_evaluation_authorized": (
            PNL_EVALUATION_AUTHORIZED
        ),
        "live_authorized": (
            LIVE_AUTHORIZED
        ),
        "execution_authorized": (
            EXECUTION_AUTHORIZED
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