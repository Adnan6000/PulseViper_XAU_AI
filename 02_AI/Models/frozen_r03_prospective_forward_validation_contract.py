from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping


CONTRACT_ID = (
    "FROZEN_R03_PROSPECTIVE_FORWARD_VALIDATION_CONTRACT_V1"
)

SCHEMA_VERSION = "1.0.0"

BASE_AUTHORITY_COMMIT = (
    "a520c646aa6fb8bff139219f7101eb0d4aa07b43"
)


# =============================================================================
# Frozen upstream authorities
# =============================================================================

WINNER_CANDIDATE_ID = (
    "R03_FLAT_EXTRA_TREES_SMOOTH"
)

WINNER_CANDIDATE_FINGERPRINT_SHA256 = (
    "ae644c7272a015c26daeaaa7e655120bd7a3e4d267b2acd0d1f235e10bfa2e5f"
)

FINAL_WINNER_CONTRACT_FINGERPRINT_SHA256 = (
    "1c0a7e91b318973f319de4a01b9f850e80f236c9211b4866f52cbb330a973f91"
)

SEALED_TEST_CONFIRMATION_CONTRACT_FINGERPRINT_SHA256 = (
    "bc1633761ad6dc68923351735abd6ec940ac84871a38c2620ef668666cffe305"
)

SEALED_TEST_PUBLISHED_COMMIT = (
    "a520c646aa6fb8bff139219f7101eb0d4aa07b43"
)

SEALED_TEST_EVIDENCE_SHA256 = (
    "df6de696e413ade5a1a6cf52bd6ec4c290a46895d97c1fff2c30e9e7e6e09e0b"
)

SEALED_TEST_ACCESS_MARKER_SHA256 = (
    "d4555e29b4938ed12fe624d9e3b8853b5b59d2e8c35e494225fdd34f89f8ae72"
)

SEALED_TEST_PUBLICATION_TIME_UTC = (
    "2026-10-03T04:32:41Z"
)

FORWARD_OUTCOME_CONTRACT_FINGERPRINT_SHA256 = (
    "01fe52a2f068fcc8fb2fc5b89dd7e19dc974fc2d967cfb791e75c3415804ce87"
)


# =============================================================================
# Model and feature authority
# =============================================================================

FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

FEATURE_COUNT = 331

MODEL_ARCHITECTURE = (
    "FLAT_3CLASS"
)

MODEL_FAMILY = (
    "EXTRA_TREES"
)

PREDICTION_RULE = (
    "ARGMAX_3CLASS_PROBABILITY"
)

PROBABILITY_CLASS_ORDER = (
    -1,
    0,
    1,
)

MODEL_ARTIFACT_MUST_BE_FROZEN_BEFORE_COLLECTION = True

MODEL_ARTIFACT_TRAIN_ONLY_REQUIRED = True

TRAIN_PLUS_VALIDATION_REFIT_ALLOWED = False

POST_TEST_MODEL_CHANGE_ALLOWED = False

POST_TEST_THRESHOLD_TUNING_ALLOWED = False

POST_TEST_CALIBRATION_ALLOWED = False

POST_TEST_FEATURE_CHANGE_ALLOWED = False


# =============================================================================
# Target / prospective outcome semantics
# =============================================================================

TARGET_CONTRACT = (
    "CLEAN_DIRECTIONAL_EXCURSION_V2"
)

CANONICAL_INSTRUMENT = (
    "XAUUSD"
)

BASE_TIMEFRAME = (
    "M5"
)

HORIZON_BARS = 12

HORIZON_MINUTES = 60

REFERENCE_PRICE = (
    "DECISION_M5_CLOSE"
)

REFERENCE_VOLATILITY = (
    "DECISION_M5_ATR14"
)

PROFIT_ATR = 1.25

MAX_ADVERSE_ATR = 0.75

ONLY_COMPLETED_M5_BARS_ALLOWED = True

FORMING_CANDLE_ALLOWED = False

PROSPECTIVE_ANCHOR_REQUIRED = True

FUTURE_DATA_MAY_ONLY_BE_USED_FOR_OUTCOME = True


# =============================================================================
# Prospective start boundary
# =============================================================================

FRESH_SAMPLE_ONLY = True

DECISION_TIME_MUST_BE_AFTER_SEALED_TEST_PUBLICATION = True

EARLIEST_PROSPECTIVE_AUTHORITY_TIME_UTC = (
    SEALED_TEST_PUBLICATION_TIME_UTC
)

OLD_FORWARD_30_ELIGIBLE_FOR_ACCEPTANCE = False

OLD_FORWARD_30_ELIGIBLE_FOR_TUNING = False

SEALED_TEST_ELIGIBLE_FOR_FURTHER_TUNING = False


# =============================================================================
# Dedicated R03 prospective ledgers
# =============================================================================

OBSERVATION_LEDGER_RELATIVE_PATH = (
    "01_Data/Shadow/"
    "xauusd_r03_prospective_observations.jsonl"
)

ANCHOR_LEDGER_RELATIVE_PATH = (
    "01_Data/Shadow/"
    "xauusd_r03_prospective_forward_outcome_anchors.jsonl"
)

OUTCOME_LEDGER_RELATIVE_PATH = (
    "01_Data/Shadow/"
    "xauusd_r03_prospective_forward_outcomes.jsonl"
)

LEDGERS_APPEND_ONLY = True

LEDGERS_MAY_BE_DELETED = False

LEDGERS_MAY_BE_RESET = False

LEDGERS_MAY_BE_TRUNCATED = False

LEDGERS_MAY_BE_OVERWRITTEN = False


# =============================================================================
# Frozen sealed TEST reference metrics
# =============================================================================

SEALED_TEST_EXACT_CLASS_ACCURACY = (
    0.3560949586556415
)

SEALED_TEST_MACRO_F1 = (
    0.3490621418247086
)

SEALED_TEST_BALANCED_ACCURACY = (
    0.36362456717804426
)

SEALED_TEST_MINIMUM_PER_CLASS_RECALL = (
    0.29837117472852914
)

SEALED_TEST_MULTICLASS_BRIER = (
    0.6647780979670608
)

SEALED_TEST_MULTICLASS_LOG_LOSS = (
    1.095870026564396
)


# =============================================================================
# Prospective maturity requirements
# =============================================================================

MINIMUM_MATURED_OUTCOMES = 60

MINIMUM_DISTINCT_OBSERVATION_UTC_DATES = 5

WEEKLY_REPORTING_ENABLED = True

WEEKLY_REPORTS_ARE_DESCRIPTIVE_ONLY = True

WEEKLY_REPORTS_MAY_TRIGGER_PASS_FAIL = False

CUMULATIVE_REPORT_IS_DECISION_AUTHORITY = True

EARLY_PASS_ALLOWED = False

EARLY_FAIL_ALLOWED = False


# =============================================================================
# Structural acceptance rules
# =============================================================================

ALL_METRICS_MUST_BE_FINITE = True

ALL_THREE_PREDICTION_CLASSES_REQUIRED = True

SHORT_RECALL_MUST_BE_POSITIVE = True

NO_TRADE_RECALL_MUST_BE_POSITIVE = True

LONG_RECALL_MUST_BE_POSITIVE = True

MINIMUM_PREDICTED_CLASS_SHARE = (
    0.05
)

MAXIMUM_PREDICTED_CLASS_SHARE = (
    0.80
)


# =============================================================================
# Prospective generalization thresholds
# =============================================================================

MACRO_F1_TEST_RETENTION_RATIO = (
    0.85
)

BALANCED_ACCURACY_TEST_RETENTION_RATIO = (
    0.85
)

MINIMUM_PER_CLASS_RECALL_TEST_RETENTION_RATIO = (
    0.70
)

MAXIMUM_BRIER_DEGRADATION_FROM_TEST = (
    0.05
)

MAXIMUM_LOG_LOSS_DEGRADATION_FROM_TEST = (
    0.10
)


PROSPECTIVE_MACRO_F1_MINIMUM = (
    SEALED_TEST_MACRO_F1
    *
    MACRO_F1_TEST_RETENTION_RATIO
)

PROSPECTIVE_BALANCED_ACCURACY_MINIMUM = (
    SEALED_TEST_BALANCED_ACCURACY
    *
    BALANCED_ACCURACY_TEST_RETENTION_RATIO
)

PROSPECTIVE_MINIMUM_PER_CLASS_RECALL_MINIMUM = (
    SEALED_TEST_MINIMUM_PER_CLASS_RECALL
    *
    MINIMUM_PER_CLASS_RECALL_TEST_RETENTION_RATIO
)

PROSPECTIVE_MULTICLASS_BRIER_MAXIMUM = (
    SEALED_TEST_MULTICLASS_BRIER
    +
    MAXIMUM_BRIER_DEGRADATION_FROM_TEST
)

PROSPECTIVE_MULTICLASS_LOG_LOSS_MAXIMUM = (
    SEALED_TEST_MULTICLASS_LOG_LOSS
    +
    MAXIMUM_LOG_LOSS_DEGRADATION_FROM_TEST
)


# =============================================================================
# Monitoring-only diagnostics
# =============================================================================

TRACK_EXACT_CLASS_ACCURACY = True

TRACK_PER_CLASS_PRECISION_RECALL_F1 = True

TRACK_PREDICTION_DISTRIBUTION = True

TRACK_OUTCOME_DISTRIBUTION = True

TRACK_MEAN_PROBABILITY_BY_CLASS = True

TRACK_CORRECT_INCORRECT_CONFIDENCE = True

CONFIDENCE_SEPARATION_IS_PASS_FAIL_CRITERION = False


# =============================================================================
# Decision policy
# =============================================================================

PASS_STATUS = (
    "R03_PROSPECTIVE_FORWARD_CONFIRMED"
)

FAIL_STATUS = (
    "R03_PROSPECTIVE_FORWARD_NOT_CONFIRMED"
)

NOT_MATURE_STATUS = (
    "R03_PROSPECTIVE_FORWARD_NOT_YET_MATURE"
)

ALL_ACCEPTANCE_CRITERIA_MUST_PASS = True

POST_HOC_EXCEPTION_ALLOWED = False

MANUAL_OVERRIDE_TO_PASS_ALLOWED = False

PNL_IS_ACCEPTANCE_CRITERION = False

TRANSACTION_COSTS_ARE_ACCEPTANCE_CRITERION = False

PROSPECTIVE_PASS_AUTHORIZES_LIVE = False

PROSPECTIVE_PASS_AUTHORIZES_EXECUTION = False

REAL_TICK_VALIDATION_REQUIRED_AFTER_PROSPECTIVE_PASS = True

BROKER_EXECUTION_VALIDATION_REQUIRED_AFTER_PROSPECTIVE_PASS = True


# =============================================================================
# Current G7-H-A gate boundaries
# =============================================================================

THIS_GATE_FREEZES_CONTRACT_ONLY = True

THIS_GATE_LOADS_MARKET_DATA = False

THIS_GATE_LOADS_OLD_FORWARD_OUTCOMES = False

THIS_GATE_LOADS_TEST_VALUES = False

THIS_GATE_TRAINS_MODEL = False

THIS_GATE_SERIALIZES_MODEL = False

THIS_GATE_WRITES_PROSPECTIVE_LEDGERS = False

THIS_GATE_EVALUATES_PROSPECTIVE_RESULTS = False

THIS_GATE_EVALUATES_PNL = False

LIVE_AUTHORIZED = False

EXECUTION_AUTHORIZED = False


def acceptance_thresholds_dict() -> dict[str, float]:

    return {
        "macro_f1_minimum": (
            PROSPECTIVE_MACRO_F1_MINIMUM
        ),
        "balanced_accuracy_minimum": (
            PROSPECTIVE_BALANCED_ACCURACY_MINIMUM
        ),
        "minimum_per_class_recall_minimum": (
            PROSPECTIVE_MINIMUM_PER_CLASS_RECALL_MINIMUM
        ),
        "multiclass_brier_maximum": (
            PROSPECTIVE_MULTICLASS_BRIER_MAXIMUM
        ),
        "multiclass_log_loss_maximum": (
            PROSPECTIVE_MULTICLASS_LOG_LOSS_MAXIMUM
        ),
    }


def evaluate_prospective_confirmation(
    metrics: Mapping[str, Any],
    *,
    matured_outcomes: int,
    distinct_observation_utc_dates: int,
) -> dict[str, Any]:

    if (
        matured_outcomes
        <
        MINIMUM_MATURED_OUTCOMES
        or
        distinct_observation_utc_dates
        <
        MINIMUM_DISTINCT_OBSERVATION_UTC_DATES
    ):
        return {
            "mature": False,
            "passed": False,
            "status": (
                NOT_MATURE_STATUS
            ),
            "failures": [],
            "maturity": {
                "matured_outcomes": (
                    matured_outcomes
                ),
                "minimum_matured_outcomes": (
                    MINIMUM_MATURED_OUTCOMES
                ),
                "distinct_observation_utc_dates": (
                    distinct_observation_utc_dates
                ),
                "minimum_distinct_observation_utc_dates": (
                    MINIMUM_DISTINCT_OBSERVATION_UTC_DATES
                ),
            },
            "thresholds": (
                acceptance_thresholds_dict()
            ),
        }

    required_scalar_metrics = (
        "macro_f1",
        "balanced_accuracy",
        "minimum_per_class_recall",
        "short_recall",
        "no_trade_recall",
        "long_recall",
        "multiclass_brier",
        "multiclass_log_loss",
    )

    failures: list[str] = []

    values: dict[str, float] = {}

    for key in required_scalar_metrics:

        if key not in metrics:
            failures.append(
                f"MISSING_METRIC:{key}"
            )
            continue

        try:
            value = float(
                metrics[
                    key
                ]
            )
        except (
            TypeError,
            ValueError,
        ):
            failures.append(
                f"INVALID_METRIC:{key}"
            )
            continue

        values[
            key
        ] = value

        if (
            ALL_METRICS_MUST_BE_FINITE
            and
            not math.isfinite(
                value
            )
        ):
            failures.append(
                f"NON_FINITE_METRIC:{key}"
            )

    counts_raw = metrics.get(
        "prediction_counts"
    )

    shares_raw = metrics.get(
        "prediction_shares"
    )

    if not isinstance(
        counts_raw,
        Mapping,
    ):
        counts: Mapping[str, Any] = {}

        failures.append(
            "PREDICTION_COUNTS_MISSING"
        )

    else:
        counts = counts_raw

    if not isinstance(
        shares_raw,
        Mapping,
    ):
        shares: Mapping[str, Any] = {}

        failures.append(
            "PREDICTION_SHARES_MISSING"
        )

    else:
        shares = shares_raw

    labels = (
        "SHORT",
        "NO_TRADE",
        "LONG",
    )

    if (
        ALL_THREE_PREDICTION_CLASSES_REQUIRED
    ):

        for label in labels:

            try:
                count = int(
                    counts.get(
                        label,
                        0,
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                count = 0

            if count <= 0:
                failures.append(
                    f"CLASS_NOT_PREDICTED:{label}"
                )

    for label in labels:

        try:
            share = float(
                shares.get(
                    label,
                    0.0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            share = 0.0

        if (
            share
            <
            MINIMUM_PREDICTED_CLASS_SHARE
        ):
            failures.append(
                (
                    "PREDICTED_CLASS_SHARE_BELOW_MIN:"
                    f"{label}"
                )
            )

        if (
            share
            >
            MAXIMUM_PREDICTED_CLASS_SHARE
        ):
            failures.append(
                (
                    "PREDICTED_CLASS_SHARE_ABOVE_MAX:"
                    f"{label}"
                )
            )

    if (
        SHORT_RECALL_MUST_BE_POSITIVE
        and
        values.get(
            "short_recall",
            0.0,
        )
        <=
        0.0
    ):
        failures.append(
            "SHORT_RECALL_NOT_POSITIVE"
        )

    if (
        NO_TRADE_RECALL_MUST_BE_POSITIVE
        and
        values.get(
            "no_trade_recall",
            0.0,
        )
        <=
        0.0
    ):
        failures.append(
            "NO_TRADE_RECALL_NOT_POSITIVE"
        )

    if (
        LONG_RECALL_MUST_BE_POSITIVE
        and
        values.get(
            "long_recall",
            0.0,
        )
        <=
        0.0
    ):
        failures.append(
            "LONG_RECALL_NOT_POSITIVE"
        )

    if (
        values.get(
            "macro_f1",
            float("-inf"),
        )
        <
        PROSPECTIVE_MACRO_F1_MINIMUM
    ):
        failures.append(
            "MACRO_F1_BELOW_MINIMUM"
        )

    if (
        values.get(
            "balanced_accuracy",
            float("-inf"),
        )
        <
        PROSPECTIVE_BALANCED_ACCURACY_MINIMUM
    ):
        failures.append(
            "BALANCED_ACCURACY_BELOW_MINIMUM"
        )

    if (
        values.get(
            "minimum_per_class_recall",
            float("-inf"),
        )
        <
        PROSPECTIVE_MINIMUM_PER_CLASS_RECALL_MINIMUM
    ):
        failures.append(
            "MINIMUM_PER_CLASS_RECALL_BELOW_MINIMUM"
        )

    if (
        values.get(
            "multiclass_brier",
            float("inf"),
        )
        >
        PROSPECTIVE_MULTICLASS_BRIER_MAXIMUM
    ):
        failures.append(
            "MULTICLASS_BRIER_ABOVE_MAXIMUM"
        )

    if (
        values.get(
            "multiclass_log_loss",
            float("inf"),
        )
        >
        PROSPECTIVE_MULTICLASS_LOG_LOSS_MAXIMUM
    ):
        failures.append(
            "MULTICLASS_LOG_LOSS_ABOVE_MAXIMUM"
        )

    failures = list(
        dict.fromkeys(
            failures
        )
    )

    passed = (
        len(
            failures
        )
        ==
        0
    )

    return {
        "mature": True,
        "passed": passed,
        "status": (
            PASS_STATUS
            if passed
            else FAIL_STATUS
        ),
        "failures": failures,
        "maturity": {
            "matured_outcomes": (
                matured_outcomes
            ),
            "minimum_matured_outcomes": (
                MINIMUM_MATURED_OUTCOMES
            ),
            "distinct_observation_utc_dates": (
                distinct_observation_utc_dates
            ),
            "minimum_distinct_observation_utc_dates": (
                MINIMUM_DISTINCT_OBSERVATION_UTC_DATES
            ),
        },
        "thresholds": (
            acceptance_thresholds_dict()
        ),
    }


def canonical_contract_dict() -> dict[str, Any]:

    return {
        "contract_id": CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),
        "upstream": {
            "winner_candidate_id": (
                WINNER_CANDIDATE_ID
            ),
            "winner_candidate_fingerprint_sha256": (
                WINNER_CANDIDATE_FINGERPRINT_SHA256
            ),
            "final_winner_contract_fingerprint_sha256": (
                FINAL_WINNER_CONTRACT_FINGERPRINT_SHA256
            ),
            "sealed_test_confirmation_contract_fingerprint_sha256": (
                SEALED_TEST_CONFIRMATION_CONTRACT_FINGERPRINT_SHA256
            ),
            "sealed_test_published_commit": (
                SEALED_TEST_PUBLISHED_COMMIT
            ),
            "sealed_test_evidence_sha256": (
                SEALED_TEST_EVIDENCE_SHA256
            ),
            "sealed_test_access_marker_sha256": (
                SEALED_TEST_ACCESS_MARKER_SHA256
            ),
            "sealed_test_publication_time_utc": (
                SEALED_TEST_PUBLICATION_TIME_UTC
            ),
            "forward_outcome_contract_fingerprint_sha256": (
                FORWARD_OUTCOME_CONTRACT_FINGERPRINT_SHA256
            ),
        },
        "model": {
            "feature_columns_sha256": (
                FEATURE_COLUMNS_SHA256
            ),
            "feature_count": (
                FEATURE_COUNT
            ),
            "architecture": (
                MODEL_ARCHITECTURE
            ),
            "family": (
                MODEL_FAMILY
            ),
            "prediction_rule": (
                PREDICTION_RULE
            ),
            "probability_class_order": list(
                PROBABILITY_CLASS_ORDER
            ),
            "artifact_must_be_frozen_before_collection": (
                MODEL_ARTIFACT_MUST_BE_FROZEN_BEFORE_COLLECTION
            ),
            "artifact_train_only_required": (
                MODEL_ARTIFACT_TRAIN_ONLY_REQUIRED
            ),
            "train_plus_validation_refit_allowed": (
                TRAIN_PLUS_VALIDATION_REFIT_ALLOWED
            ),
            "post_test_model_change_allowed": (
                POST_TEST_MODEL_CHANGE_ALLOWED
            ),
            "post_test_threshold_tuning_allowed": (
                POST_TEST_THRESHOLD_TUNING_ALLOWED
            ),
            "post_test_calibration_allowed": (
                POST_TEST_CALIBRATION_ALLOWED
            ),
            "post_test_feature_change_allowed": (
                POST_TEST_FEATURE_CHANGE_ALLOWED
            ),
        },
        "target": {
            "contract": TARGET_CONTRACT,
            "canonical_instrument": (
                CANONICAL_INSTRUMENT
            ),
            "base_timeframe": (
                BASE_TIMEFRAME
            ),
            "horizon_bars": (
                HORIZON_BARS
            ),
            "horizon_minutes": (
                HORIZON_MINUTES
            ),
            "reference_price": (
                REFERENCE_PRICE
            ),
            "reference_volatility": (
                REFERENCE_VOLATILITY
            ),
            "profit_atr": PROFIT_ATR,
            "max_adverse_atr": (
                MAX_ADVERSE_ATR
            ),
            "completed_m5_only": (
                ONLY_COMPLETED_M5_BARS_ALLOWED
            ),
            "forming_candle_allowed": (
                FORMING_CANDLE_ALLOWED
            ),
            "prospective_anchor_required": (
                PROSPECTIVE_ANCHOR_REQUIRED
            ),
            "future_data_outcome_only": (
                FUTURE_DATA_MAY_ONLY_BE_USED_FOR_OUTCOME
            ),
        },
        "freshness": {
            "fresh_sample_only": (
                FRESH_SAMPLE_ONLY
            ),
            "decision_time_after_test_publication": (
                DECISION_TIME_MUST_BE_AFTER_SEALED_TEST_PUBLICATION
            ),
            "earliest_authority_time_utc": (
                EARLIEST_PROSPECTIVE_AUTHORITY_TIME_UTC
            ),
            "old_forward_30_acceptance": (
                OLD_FORWARD_30_ELIGIBLE_FOR_ACCEPTANCE
            ),
            "old_forward_30_tuning": (
                OLD_FORWARD_30_ELIGIBLE_FOR_TUNING
            ),
            "sealed_test_further_tuning": (
                SEALED_TEST_ELIGIBLE_FOR_FURTHER_TUNING
            ),
        },
        "ledgers": {
            "observation": (
                OBSERVATION_LEDGER_RELATIVE_PATH
            ),
            "anchor": (
                ANCHOR_LEDGER_RELATIVE_PATH
            ),
            "outcome": (
                OUTCOME_LEDGER_RELATIVE_PATH
            ),
            "append_only": (
                LEDGERS_APPEND_ONLY
            ),
            "delete_allowed": (
                LEDGERS_MAY_BE_DELETED
            ),
            "reset_allowed": (
                LEDGERS_MAY_BE_RESET
            ),
            "truncate_allowed": (
                LEDGERS_MAY_BE_TRUNCATED
            ),
            "overwrite_allowed": (
                LEDGERS_MAY_BE_OVERWRITTEN
            ),
        },
        "sealed_test_reference": {
            "exact_class_accuracy": (
                SEALED_TEST_EXACT_CLASS_ACCURACY
            ),
            "macro_f1": (
                SEALED_TEST_MACRO_F1
            ),
            "balanced_accuracy": (
                SEALED_TEST_BALANCED_ACCURACY
            ),
            "minimum_per_class_recall": (
                SEALED_TEST_MINIMUM_PER_CLASS_RECALL
            ),
            "multiclass_brier": (
                SEALED_TEST_MULTICLASS_BRIER
            ),
            "multiclass_log_loss": (
                SEALED_TEST_MULTICLASS_LOG_LOSS
            ),
        },
        "maturity": {
            "minimum_matured_outcomes": (
                MINIMUM_MATURED_OUTCOMES
            ),
            "minimum_distinct_observation_utc_dates": (
                MINIMUM_DISTINCT_OBSERVATION_UTC_DATES
            ),
            "weekly_reporting": (
                WEEKLY_REPORTING_ENABLED
            ),
            "weekly_descriptive_only": (
                WEEKLY_REPORTS_ARE_DESCRIPTIVE_ONLY
            ),
            "weekly_may_trigger_pass_fail": (
                WEEKLY_REPORTS_MAY_TRIGGER_PASS_FAIL
            ),
            "cumulative_decision_authority": (
                CUMULATIVE_REPORT_IS_DECISION_AUTHORITY
            ),
            "early_pass_allowed": (
                EARLY_PASS_ALLOWED
            ),
            "early_fail_allowed": (
                EARLY_FAIL_ALLOWED
            ),
        },
        "acceptance": {
            "all_metrics_finite": (
                ALL_METRICS_MUST_BE_FINITE
            ),
            "all_three_prediction_classes": (
                ALL_THREE_PREDICTION_CLASSES_REQUIRED
            ),
            "short_recall_positive": (
                SHORT_RECALL_MUST_BE_POSITIVE
            ),
            "no_trade_recall_positive": (
                NO_TRADE_RECALL_MUST_BE_POSITIVE
            ),
            "long_recall_positive": (
                LONG_RECALL_MUST_BE_POSITIVE
            ),
            "minimum_predicted_class_share": (
                MINIMUM_PREDICTED_CLASS_SHARE
            ),
            "maximum_predicted_class_share": (
                MAXIMUM_PREDICTED_CLASS_SHARE
            ),
            "macro_f1_test_retention_ratio": (
                MACRO_F1_TEST_RETENTION_RATIO
            ),
            "balanced_accuracy_test_retention_ratio": (
                BALANCED_ACCURACY_TEST_RETENTION_RATIO
            ),
            "minimum_recall_test_retention_ratio": (
                MINIMUM_PER_CLASS_RECALL_TEST_RETENTION_RATIO
            ),
            "maximum_brier_degradation_from_test": (
                MAXIMUM_BRIER_DEGRADATION_FROM_TEST
            ),
            "maximum_log_loss_degradation_from_test": (
                MAXIMUM_LOG_LOSS_DEGRADATION_FROM_TEST
            ),
            "thresholds": (
                acceptance_thresholds_dict()
            ),
            "all_criteria_must_pass": (
                ALL_ACCEPTANCE_CRITERIA_MUST_PASS
            ),
            "post_hoc_exception_allowed": (
                POST_HOC_EXCEPTION_ALLOWED
            ),
            "manual_override_to_pass_allowed": (
                MANUAL_OVERRIDE_TO_PASS_ALLOWED
            ),
            "pnl_is_acceptance_criterion": (
                PNL_IS_ACCEPTANCE_CRITERION
            ),
        },
        "downstream": {
            "prospective_pass_authorizes_live": (
                PROSPECTIVE_PASS_AUTHORIZES_LIVE
            ),
            "prospective_pass_authorizes_execution": (
                PROSPECTIVE_PASS_AUTHORIZES_EXECUTION
            ),
            "real_tick_validation_required": (
                REAL_TICK_VALIDATION_REQUIRED_AFTER_PROSPECTIVE_PASS
            ),
            "broker_execution_validation_required": (
                BROKER_EXECUTION_VALIDATION_REQUIRED_AFTER_PROSPECTIVE_PASS
            ),
        },
        "current_gate": {
            "contract_freeze_only": (
                THIS_GATE_FREEZES_CONTRACT_ONLY
            ),
            "market_data_loaded": (
                THIS_GATE_LOADS_MARKET_DATA
            ),
            "old_forward_outcomes_loaded": (
                THIS_GATE_LOADS_OLD_FORWARD_OUTCOMES
            ),
            "test_values_loaded": (
                THIS_GATE_LOADS_TEST_VALUES
            ),
            "model_training": (
                THIS_GATE_TRAINS_MODEL
            ),
            "model_serialization": (
                THIS_GATE_SERIALIZES_MODEL
            ),
            "prospective_ledger_write": (
                THIS_GATE_WRITES_PROSPECTIVE_LEDGERS
            ),
            "prospective_evaluation": (
                THIS_GATE_EVALUATES_PROSPECTIVE_RESULTS
            ),
            "pnl_evaluation": (
                THIS_GATE_EVALUATES_PNL
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