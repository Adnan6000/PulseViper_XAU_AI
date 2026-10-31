from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping


CONTRACT_ID = (
    "FROZEN_C04_REMEDIATION_TEST_CONFIRMATION_CONTRACT_V1"
)

SCHEMA_VERSION = "1.0.0"

BASE_AUTHORITY_COMMIT = (
    "648939914f74ae993829105274e10146c137414e"
)


# =============================================================================
# Frozen upstream winner authority
# =============================================================================

FINAL_WINNER_CONTRACT_ID = (
    "FROZEN_C04_REMEDIATION_FINAL_WINNER_CONTRACT_V1"
)

FINAL_WINNER_CONTRACT_FINGERPRINT_SHA256 = (
    "1c0a7e91b318973f319de4a01b9f850e80f236c9211b4866f52cbb330a973f91"
)

FINAL_WINNER_PUBLISHED_COMMIT = (
    "648939914f74ae993829105274e10146c137414e"
)

WINNER_CANDIDATE_ID = (
    "R03_FLAT_EXTRA_TREES_SMOOTH"
)

WINNER_CANDIDATE_FINGERPRINT_SHA256 = (
    "ae644c7272a015c26daeaaa7e655120bd7a3e4d267b2acd0d1f235e10bfa2e5f"
)


# =============================================================================
# Frozen dataset / target authority
# =============================================================================

DATASET_ID = (
    "portable_cff75b0686383a3ab6f8352b"
)

DATASET_SHA256 = (
    "cff75b0686383a3ab6f8352bfcdcd55308b99b7a4c6edbf7d2e7215f6f33dd07"
)

FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

FEATURE_COUNT = 331

TRAIN_ROWS = 69966

VALIDATION_ROWS = 14983

TEST_ROWS = 14996

TARGET_CONTRACT = (
    "CLEAN_DIRECTIONAL_EXCURSION_V2"
)

CLASS_ORDER = (
    -1,
    0,
    1,
)


# =============================================================================
# Frozen validation reference
# =============================================================================

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


# =============================================================================
# Predeclared TEST confirmation policy
# =============================================================================

TEST_ROLE = (
    "SEALED_ONE_SHOT_FINAL_OFFLINE_CONFIRMATION"
)

TEST_ACCESS_COUNT_MAXIMUM = 1

TEST_RESULT_MAY_NOT_BE_USED_FOR_SAME_TEST_TUNING = True

TEST_RESULT_MAY_NOT_TRIGGER_THRESHOLD_TUNING = True

TEST_RESULT_MAY_NOT_TRIGGER_CALIBRATION = True

TEST_RESULT_MAY_NOT_TRIGGER_FEATURE_SELECTION = True

TEST_RESULT_MAY_NOT_TRIGGER_HYPERPARAMETER_CHANGE = True

TEST_RESULT_MAY_NOT_TRIGGER_CANDIDATE_REPLACEMENT = True

TRAIN_ONLY_MODEL_FIT_REQUIRED = True

TRAIN_PLUS_VALIDATION_REFIT_ALLOWED = False

VALIDATION_REEVALUATION_ALLOWED_DURING_TEST = False

OLD_FORWARD_30_USE_ALLOWED_DURING_TEST = False


# =============================================================================
# Structural eligibility requirements
# =============================================================================

ALL_METRICS_MUST_BE_FINITE = True

ALL_THREE_CLASSES_MUST_BE_PREDICTED = True

SHORT_RECALL_MUST_BE_POSITIVE = True

NO_TRADE_RECALL_MUST_BE_POSITIVE = True

LONG_RECALL_MUST_BE_POSITIVE = True

MINIMUM_PREDICTED_CLASS_SHARE = (
    0.01
)

MAXIMUM_PREDICTED_CLASS_SHARE = (
    0.90
)


# =============================================================================
# Generalization thresholds
# =============================================================================

MACRO_F1_VALIDATION_RETENTION_RATIO = (
    0.90
)

BALANCED_ACCURACY_VALIDATION_RETENTION_RATIO = (
    0.90
)

MINIMUM_PER_CLASS_RECALL_RETENTION_RATIO = (
    0.80
)

MAXIMUM_BRIER_DEGRADATION = (
    0.05
)

MAXIMUM_LOG_LOSS_DEGRADATION = (
    0.10
)


TEST_MACRO_F1_MINIMUM = (
    VALIDATION_MACRO_F1
    *
    MACRO_F1_VALIDATION_RETENTION_RATIO
)

TEST_BALANCED_ACCURACY_MINIMUM = (
    VALIDATION_BALANCED_ACCURACY
    *
    BALANCED_ACCURACY_VALIDATION_RETENTION_RATIO
)

TEST_MINIMUM_PER_CLASS_RECALL_MINIMUM = (
    VALIDATION_MINIMUM_PER_CLASS_RECALL
    *
    MINIMUM_PER_CLASS_RECALL_RETENTION_RATIO
)

TEST_MULTICLASS_BRIER_MAXIMUM = (
    VALIDATION_MULTICLASS_BRIER
    +
    MAXIMUM_BRIER_DEGRADATION
)

TEST_MULTICLASS_LOG_LOSS_MAXIMUM = (
    VALIDATION_MULTICLASS_LOG_LOSS
    +
    MAXIMUM_LOG_LOSS_DEGRADATION
)


# =============================================================================
# Overall decision policy
# =============================================================================

ALL_CONFIRMATION_CRITERIA_MUST_PASS = True

PASS_STATUS = (
    "SEALED_TEST_CONFIRMED"
)

FAIL_STATUS = (
    "SEALED_TEST_NOT_CONFIRMED"
)

NO_METRIC_WEIGHTING_ALLOWED = True

NO_POST_HOC_EXCEPTION_ALLOWED = True

NO_MANUAL_OVERRIDE_TO_PASS_ALLOWED = True

TEST_PASS_DOES_NOT_AUTHORIZE_LIVE_TRADING = True

TEST_PASS_DOES_NOT_AUTHORIZE_EXECUTION = True


# =============================================================================
# Current G7-G-A gate safety
# =============================================================================

THIS_GATE_FREEZES_TEST_CRITERIA_ONLY = True

THIS_GATE_LOADS_TRAIN_VALUES = False

THIS_GATE_LOADS_VALIDATION_VALUES = False

THIS_GATE_LOADS_TEST_VALUES = False

THIS_GATE_TRAINS_MODEL = False

THIS_GATE_EVALUATES_VALIDATION = False

THIS_GATE_EVALUATES_TEST = False

THIS_GATE_USES_FORWARD_30 = False

THIS_GATE_EVALUATES_PNL = False

THIS_GATE_ACQUIRES_MARKET_DATA = False

THIS_GATE_WRITES_RUNTIME_LEDGERS = False

LIVE_AUTHORIZED = False

EXECUTION_AUTHORIZED = False


def test_thresholds_dict() -> dict[str, float]:

    return {
        "macro_f1_minimum": (
            TEST_MACRO_F1_MINIMUM
        ),
        "balanced_accuracy_minimum": (
            TEST_BALANCED_ACCURACY_MINIMUM
        ),
        "minimum_per_class_recall_minimum": (
            TEST_MINIMUM_PER_CLASS_RECALL_MINIMUM
        ),
        "multiclass_brier_maximum": (
            TEST_MULTICLASS_BRIER_MAXIMUM
        ),
        "multiclass_log_loss_maximum": (
            TEST_MULTICLASS_LOG_LOSS_MAXIMUM
        ),
    }


def evaluate_test_confirmation(
    metrics: Mapping[str, Any],
) -> dict[str, Any]:

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

    scalar_values: dict[str, float] = {}

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

        scalar_values[
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
        failures.append(
            "PREDICTION_COUNTS_MISSING"
        )
        counts: Mapping[str, Any] = {}
    else:
        counts = counts_raw

    if not isinstance(
        shares_raw,
        Mapping,
    ):
        failures.append(
            "PREDICTION_SHARES_MISSING"
        )
        shares: Mapping[str, Any] = {}
    else:
        shares = shares_raw

    labels = (
        "SHORT",
        "NO_TRADE",
        "LONG",
    )

    if (
        ALL_THREE_CLASSES_MUST_BE_PREDICTED
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

    if (
        SHORT_RECALL_MUST_BE_POSITIVE
        and
        scalar_values.get(
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
        scalar_values.get(
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
        scalar_values.get(
            "long_recall",
            0.0,
        )
        <=
        0.0
    ):
        failures.append(
            "LONG_RECALL_NOT_POSITIVE"
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
        scalar_values.get(
            "macro_f1",
            float("-inf"),
        )
        <
        TEST_MACRO_F1_MINIMUM
    ):
        failures.append(
            "MACRO_F1_BELOW_MINIMUM"
        )

    if (
        scalar_values.get(
            "balanced_accuracy",
            float("-inf"),
        )
        <
        TEST_BALANCED_ACCURACY_MINIMUM
    ):
        failures.append(
            "BALANCED_ACCURACY_BELOW_MINIMUM"
        )

    if (
        scalar_values.get(
            "minimum_per_class_recall",
            float("-inf"),
        )
        <
        TEST_MINIMUM_PER_CLASS_RECALL_MINIMUM
    ):
        failures.append(
            "MINIMUM_PER_CLASS_RECALL_BELOW_MINIMUM"
        )

    if (
        scalar_values.get(
            "multiclass_brier",
            float("inf"),
        )
        >
        TEST_MULTICLASS_BRIER_MAXIMUM
    ):
        failures.append(
            "MULTICLASS_BRIER_ABOVE_MAXIMUM"
        )

    if (
        scalar_values.get(
            "multiclass_log_loss",
            float("inf"),
        )
        >
        TEST_MULTICLASS_LOG_LOSS_MAXIMUM
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
        "passed": passed,
        "status": (
            PASS_STATUS
            if passed
            else FAIL_STATUS
        ),
        "failures": failures,
        "thresholds": (
            test_thresholds_dict()
        ),
    }


def canonical_contract_dict() -> dict[str, Any]:

    return {
        "contract_id": CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),
        "winner_authority": {
            "contract_id": (
                FINAL_WINNER_CONTRACT_ID
            ),
            "contract_fingerprint_sha256": (
                FINAL_WINNER_CONTRACT_FINGERPRINT_SHA256
            ),
            "published_commit": (
                FINAL_WINNER_PUBLISHED_COMMIT
            ),
            "candidate_id": (
                WINNER_CANDIDATE_ID
            ),
            "candidate_fingerprint_sha256": (
                WINNER_CANDIDATE_FINGERPRINT_SHA256
            ),
        },
        "data_authority": {
            "dataset_id": DATASET_ID,
            "dataset_sha256": (
                DATASET_SHA256
            ),
            "feature_columns_sha256": (
                FEATURE_COLUMNS_SHA256
            ),
            "feature_count": (
                FEATURE_COUNT
            ),
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
            "class_order": list(
                CLASS_ORDER
            ),
        },
        "validation_reference": {
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
        },
        "test_policy": {
            "role": TEST_ROLE,
            "maximum_access_count": (
                TEST_ACCESS_COUNT_MAXIMUM
            ),
            "train_only_fit_required": (
                TRAIN_ONLY_MODEL_FIT_REQUIRED
            ),
            "train_plus_validation_refit_allowed": (
                TRAIN_PLUS_VALIDATION_REFIT_ALLOWED
            ),
            "validation_reevaluation_during_test": (
                VALIDATION_REEVALUATION_ALLOWED_DURING_TEST
            ),
            "forward_30_use_during_test": (
                OLD_FORWARD_30_USE_ALLOWED_DURING_TEST
            ),
            "same_test_tuning_allowed": (
                not TEST_RESULT_MAY_NOT_BE_USED_FOR_SAME_TEST_TUNING
            ),
            "threshold_tuning_after_test_allowed": (
                not TEST_RESULT_MAY_NOT_TRIGGER_THRESHOLD_TUNING
            ),
            "calibration_after_test_allowed": (
                not TEST_RESULT_MAY_NOT_TRIGGER_CALIBRATION
            ),
            "feature_selection_after_test_allowed": (
                not TEST_RESULT_MAY_NOT_TRIGGER_FEATURE_SELECTION
            ),
            "hyperparameter_change_after_test_allowed": (
                not TEST_RESULT_MAY_NOT_TRIGGER_HYPERPARAMETER_CHANGE
            ),
            "candidate_replacement_after_test_allowed": (
                not TEST_RESULT_MAY_NOT_TRIGGER_CANDIDATE_REPLACEMENT
            ),
        },
        "structural_requirements": {
            "all_metrics_finite": (
                ALL_METRICS_MUST_BE_FINITE
            ),
            "all_three_classes_predicted": (
                ALL_THREE_CLASSES_MUST_BE_PREDICTED
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
        },
        "generalization_policy": {
            "macro_f1_validation_retention_ratio": (
                MACRO_F1_VALIDATION_RETENTION_RATIO
            ),
            "balanced_accuracy_validation_retention_ratio": (
                BALANCED_ACCURACY_VALIDATION_RETENTION_RATIO
            ),
            "minimum_per_class_recall_retention_ratio": (
                MINIMUM_PER_CLASS_RECALL_RETENTION_RATIO
            ),
            "maximum_brier_degradation": (
                MAXIMUM_BRIER_DEGRADATION
            ),
            "maximum_log_loss_degradation": (
                MAXIMUM_LOG_LOSS_DEGRADATION
            ),
            "test_thresholds": (
                test_thresholds_dict()
            ),
        },
        "decision_policy": {
            "all_criteria_must_pass": (
                ALL_CONFIRMATION_CRITERIA_MUST_PASS
            ),
            "pass_status": PASS_STATUS,
            "fail_status": FAIL_STATUS,
            "metric_weighting_allowed": (
                not NO_METRIC_WEIGHTING_ALLOWED
            ),
            "post_hoc_exception_allowed": (
                not NO_POST_HOC_EXCEPTION_ALLOWED
            ),
            "manual_override_to_pass_allowed": (
                not NO_MANUAL_OVERRIDE_TO_PASS_ALLOWED
            ),
            "test_pass_authorizes_live": (
                not TEST_PASS_DOES_NOT_AUTHORIZE_LIVE_TRADING
            ),
            "test_pass_authorizes_execution": (
                not TEST_PASS_DOES_NOT_AUTHORIZE_EXECUTION
            ),
        },
        "current_gate": {
            "criteria_freeze_only": (
                THIS_GATE_FREEZES_TEST_CRITERIA_ONLY
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
            "validation_evaluation": (
                THIS_GATE_EVALUATES_VALIDATION
            ),
            "test_evaluation": (
                THIS_GATE_EVALUATES_TEST
            ),
            "forward_30_used": (
                THIS_GATE_USES_FORWARD_30
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