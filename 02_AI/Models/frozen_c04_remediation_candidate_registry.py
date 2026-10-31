from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


CONTRACT_ID = (
    "FROZEN_C04_REMEDIATION_CANDIDATE_REGISTRY_V1"
)

SCHEMA_VERSION = "1.0.0"

REPOSITORY_BASE_COMMIT = (
    "63b2ea84a74c7a4a5e3ad355b6e0c2ec4e702893"
)

SCIENTIFIC_PARENT_AUTHORITY_COMMIT = (
    "86271e347939c18a45c03629efdfeab1035da75a"
)

G7D_CONTRACT_ID = (
    "FROZEN_C04_REMEDIATION_RESEARCH_PROTOCOL_CONTRACT_V1"
)

G7D_CONTRACT_FINGERPRINT_SHA256 = (
    "c6270f03fed45ba749d40ea4c556b95e683ad934575c9dc958664bef83f86638"
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

TARGET_CHANGE_ALLOWED = False


# =============================================================================
# Historical control authority
# =============================================================================

HISTORICAL_C04_CANDIDATE_ID = (
    "C04_FLAT_EXTRA_TREES_CONSTRAINED"
)

HISTORICAL_C04_CONFIG_FINGERPRINT_SHA256 = (
    "f1b11c6f91561f2eba1bd56195e2239e9598b1906c88f11ada67eac6cdeb09e3"
)

HISTORICAL_REGISTRY_FINGERPRINT_SHA256 = (
    "b8088bb34ce8940f7de5946fbb9b0fd20f40d7cc93a76b76fd7975591f00066c"
)


# =============================================================================
# Broad frozen remediation hypotheses
# =============================================================================

BROAD_FAILURE_MODES = (
    "WEAK_MULTICLASS_DISCRIMINATION",
    "NEAR_UNIFORM_PROBABILITY_GEOMETRY",
    "SYSTEMATIC_LONG_ARGMAX_UPLIFT",
    "WEAK_CONFIDENCE_ERROR_SEPARATION",
)

SAMPLE_SPECIFIC_FORWARD_TUNING_ALLOWED = False

FORWARD_30_DEVELOPMENT_USE_ALLOWED = False


# =============================================================================
# Registry policy
# =============================================================================

REGISTRY_VERSION = (
    "XAUUSD_REMEDIATION_CANDIDATE_REGISTRY_V1"
)

REGISTRY_STATUS = (
    "FROZEN_BEFORE_FIRST_REMEDIATION_FIT"
)

CANDIDATE_COUNT = 6

MIN_ALLOWED_CANDIDATES = 4

MAX_ALLOWED_CANDIDATES = 12

REGISTRY_FINITE = True

REGISTRY_FROZEN_BEFORE_FIRST_FIT = True

REGISTRY_CHANGE_AFTER_FIRST_FIT_ALLOWED = False

RESULTS_DRIVEN_CANDIDATE_ADDITION_ALLOWED = False

RESULTS_DRIVEN_HYPERPARAMETER_CHANGE_ALLOWED = False

UNBOUNDED_GRID_SEARCH_ALLOWED = False

BAYESIAN_OPTIMIZATION_ALLOWED = False

AUTOML_ALLOWED = False

UNBOUNDED_RANDOM_SEARCH_ALLOWED = False

ALL_CANDIDATES_USE_EXACT_331_FEATURES = True

FEATURE_SUBSET_SEARCH_ALLOWED = False

RANDOM_SEED = 271828


# =============================================================================
# Prediction / calibration policy
# =============================================================================

PREDICTION_RULE = "ARGMAX_3CLASS_PROBABILITY"

POST_HOC_CLASS_BIAS_ALLOWED = False

PROBABILITY_CALIBRATION_IN_THIS_REGISTRY = False

DECISION_THRESHOLD_TUNING_IN_THIS_REGISTRY = False

TRADE_THRESHOLD_TUNING_IN_THIS_REGISTRY = False


# =============================================================================
# Development / selection authority
# =============================================================================

TRAIN_ROLE = (
    "FIT_MODEL_AND_TRAIN_ONLY_PREPROCESSING"
)

VALIDATION_ROLE = (
    "ONE_PREDECLARED_REMEDIATION_SELECTION_SURFACE"
)

TEST_ROLE = (
    "SEALED_ONE_SHOT_FINAL_OFFLINE_CONFIRMATION_AFTER_FINAL_CANDIDATE_FREEZE"
)

TRAIN_ACCESS_ALLOWED_IN_G7E = False

VALIDATION_ACCESS_ALLOWED_IN_G7E = False

TEST_ACCESS_ALLOWED_IN_G7E = False

TEST_ACCESS_ALLOWED_DURING_REMEDIATION_SELECTION = False

OLD_FORWARD_30_ACCESS_ALLOWED_DURING_REMEDIATION_SELECTION = False


# =============================================================================
# Eligibility / selection policy for future G7-F evaluation
# =============================================================================

ELIGIBILITY_POLICY: dict[str, Any] = {
    "all_metrics_must_be_finite": True,
    "all_three_classes_must_be_predicted": True,
    "short_recall_must_be_positive": True,
    "no_trade_recall_must_be_positive": True,
    "long_recall_must_be_positive": True,
    "maximum_single_predicted_class_share": 0.90,
    "minimum_single_predicted_class_share": 0.01,
    "if_all_candidates_fail": "NO_WINNER",
    "eligibility_rules_may_not_change_after_results": True,
}

SELECTION_POLICY: tuple[dict[str, Any], ...] = (
    {
        "priority": 1,
        "metric": "macro_f1",
        "direction": "MAXIMIZE",
    },
    {
        "priority": 2,
        "metric": "balanced_accuracy",
        "direction": "MAXIMIZE",
    },
    {
        "priority": 3,
        "metric": "minimum_per_class_recall",
        "direction": "MAXIMIZE",
    },
    {
        "priority": 4,
        "metric": "multiclass_brier",
        "direction": "MINIMIZE",
    },
    {
        "priority": 5,
        "metric": "multiclass_log_loss",
        "direction": "MINIMIZE",
    },
    {
        "priority": 6,
        "metric": "exact_class_accuracy",
        "direction": "MAXIMIZE",
    },
)

SELECTION_TIE_BREAKING = (
    "LEXICOGRAPHIC_DECLARED_PRIORITY_ORDER"
)

SINGLE_METRIC_ONLY_SELECTION_ALLOWED = False


# =============================================================================
# Candidate definitions
# =============================================================================

CANDIDATES: tuple[dict[str, Any], ...] = (

    # -------------------------------------------------------------------------
    # R00 — exact historical C04 control
    # -------------------------------------------------------------------------
    {
        "candidate_id": "R00_CONTROL_C04_EXACT",
        "role": "HISTORICAL_CONTROL",
        "hypothesis": (
            "UNCHANGED_C04_CONTROL_FOR_DIRECT_REMEDIATION_COMPARISON"
        ),
        "addresses_failure_modes": [],
        "architecture": "FLAT_3CLASS",
        "family": "EXTRA_TREES",
        "feature_scope": "EXACT_331_FROZEN_FEATURES",
        "estimator": {
            "implementation": (
                "sklearn.ensemble.ExtraTreesClassifier"
            ),
            "bootstrap": False,
            "class_weight": "balanced",
            "max_depth": 10,
            "max_features": 0.35,
            "min_samples_leaf": 25,
            "n_estimators": 500,
            "n_jobs": -1,
            "random_state": 271828,
        },
        "preprocessing": {
            "standard_scaler": False,
        },
        "probability_class_order": [-1, 0, 1],
        "prediction_rule": "ARGMAX_3CLASS_PROBABILITY",
        "probability_calibration": {
            "enabled": False,
        },
        "threshold_policy": {
            "tuning_enabled": False,
        },
    },

    # -------------------------------------------------------------------------
    # R01 — strongly regularized linear reference
    # -------------------------------------------------------------------------
    {
        "candidate_id": "R01_FLAT_LOGREG_STRONG_REG",
        "role": "REMEDIATION_CANDIDATE",
        "hypothesis": (
            "STRONGER_LINEAR_REGULARIZATION_MAY_REDUCE_NOISE_AND_CLASS_BIAS"
        ),
        "addresses_failure_modes": [
            "WEAK_MULTICLASS_DISCRIMINATION",
            "SYSTEMATIC_LONG_ARGMAX_UPLIFT",
        ],
        "architecture": "FLAT_3CLASS",
        "family": "LOGISTIC_REGRESSION",
        "feature_scope": "EXACT_331_FROZEN_FEATURES",
        "estimator": {
            "implementation": (
                "sklearn.linear_model.LogisticRegression"
            ),
            "C": 0.01,
            "class_weight": "balanced",
            "max_iter": 2500,
            "solver": "lbfgs",
            "tol": 0.0001,
        },
        "preprocessing": {
            "standard_scaler": True,
            "scaler_fit_scope": "TRAIN_ONLY",
        },
        "probability_class_order": [-1, 0, 1],
        "prediction_rule": "ARGMAX_3CLASS_PROBABILITY",
        "probability_calibration": {
            "enabled": False,
        },
        "threshold_policy": {
            "tuning_enabled": False,
        },
    },

    # -------------------------------------------------------------------------
    # R02 — balanced HGB nonlinear model
    # -------------------------------------------------------------------------
    {
        "candidate_id": "R02_FLAT_HGB_BALANCED_MEDIUM",
        "role": "REMEDIATION_CANDIDATE",
        "hypothesis": (
            "CONTROLLED_NONLINEAR_INTERACTIONS_MAY_IMPROVE_CLASS_DISCRIMINATION"
        ),
        "addresses_failure_modes": [
            "WEAK_MULTICLASS_DISCRIMINATION",
            "NEAR_UNIFORM_PROBABILITY_GEOMETRY",
        ],
        "architecture": "FLAT_3CLASS",
        "family": "HIST_GRADIENT_BOOSTING",
        "feature_scope": "EXACT_331_FROZEN_FEATURES",
        "estimator": {
            "implementation": (
                "sklearn.ensemble.HistGradientBoostingClassifier"
            ),
            "early_stopping": False,
            "l2_regularization": 2.0,
            "learning_rate": 0.025,
            "loss": "log_loss",
            "max_iter": 260,
            "max_leaf_nodes": 15,
            "min_samples_leaf": 100,
            "random_state": 271828,
        },
        "fold_local_class_balance": (
            "INVERSE_FREQUENCY_SAMPLE_WEIGHT"
        ),
        "preprocessing": {
            "standard_scaler": False,
        },
        "probability_class_order": [-1, 0, 1],
        "prediction_rule": "ARGMAX_3CLASS_PROBABILITY",
        "probability_calibration": {
            "enabled": False,
        },
        "threshold_policy": {
            "tuning_enabled": False,
        },
    },

    # -------------------------------------------------------------------------
    # R03 — smoother ExtraTrees remediation variant
    # -------------------------------------------------------------------------
    {
        "candidate_id": "R03_FLAT_EXTRA_TREES_SMOOTH",
        "role": "REMEDIATION_CANDIDATE",
        "hypothesis": (
            "SHALLOWER_TREES_AND_LARGER_LEAVES_MAY_REDUCE_ARGMAX_CLASS_BIAS_"
            "AND_PRODUCE_MORE_STABLE_PROBABILITY_GEOMETRY"
        ),
        "addresses_failure_modes": [
            "NEAR_UNIFORM_PROBABILITY_GEOMETRY",
            "SYSTEMATIC_LONG_ARGMAX_UPLIFT",
            "WEAK_CONFIDENCE_ERROR_SEPARATION",
        ],
        "architecture": "FLAT_3CLASS",
        "family": "EXTRA_TREES",
        "feature_scope": "EXACT_331_FROZEN_FEATURES",
        "estimator": {
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
        },
        "preprocessing": {
            "standard_scaler": False,
        },
        "probability_class_order": [-1, 0, 1],
        "prediction_rule": "ARGMAX_3CLASS_PROBABILITY",
        "probability_calibration": {
            "enabled": False,
        },
        "threshold_policy": {
            "tuning_enabled": False,
        },
    },

    # -------------------------------------------------------------------------
    # R04 — HGB tradeability + logistic direction
    # -------------------------------------------------------------------------
    {
        "candidate_id": "R04_HIER_HGB_LOGREG_REBALANCED",
        "role": "REMEDIATION_CANDIDATE",
        "hypothesis": (
            "SEPARATING_TRADEABILITY_FROM_DIRECTION_MAY_IMPROVE_NO_TRADE_"
            "REPRESENTATION_AND_REDUCE_DIRECTIONAL_CLASS_COLLAPSE"
        ),
        "addresses_failure_modes": [
            "WEAK_MULTICLASS_DISCRIMINATION",
            "SYSTEMATIC_LONG_ARGMAX_UPLIFT",
        ],
        "architecture": (
            "HIERARCHICAL_TRADEABILITY_DIRECTION"
        ),
        "family": (
            "HGB_STAGE_A_LOGREG_STAGE_B"
        ),
        "feature_scope": "EXACT_331_FROZEN_FEATURES",
        "probability_class_order": [-1, 0, 1],
        "probability_combination": {
            "SHORT": (
                "P_TRADEABLE * P_SHORT_GIVEN_TRADEABLE"
            ),
            "NO_TRADE": (
                "1 - P_TRADEABLE"
            ),
            "LONG": (
                "P_TRADEABLE * P_LONG_GIVEN_TRADEABLE"
            ),
        },
        "stage_a": {
            "target": "target_tradeable",
            "estimator": {
                "implementation": (
                    "sklearn.ensemble.HistGradientBoostingClassifier"
                ),
                "early_stopping": False,
                "l2_regularization": 3.0,
                "learning_rate": 0.025,
                "loss": "log_loss",
                "max_iter": 220,
                "max_leaf_nodes": 7,
                "min_samples_leaf": 120,
                "random_state": 271828,
            },
            "fold_local_class_balance": (
                "INVERSE_FREQUENCY_SAMPLE_WEIGHT"
            ),
            "preprocessing": {
                "standard_scaler": False,
            },
        },
        "stage_b": {
            "target": "SHORT_VS_LONG_FROM_TARGET_CLASS",
            "fit_scope": (
                "TRUE_TRADEABLE_TRAIN_ROWS_ONLY"
            ),
            "estimator": {
                "implementation": (
                    "sklearn.linear_model.LogisticRegression"
                ),
                "C": 0.02,
                "class_weight": "balanced",
                "max_iter": 2500,
                "solver": "lbfgs",
                "tol": 0.0001,
            },
            "preprocessing": {
                "standard_scaler": True,
                "scaler_fit_scope": (
                    "STAGE_B_TRAIN_ONLY"
                ),
            },
        },
        "prediction_rule": (
            "ARGMAX_COMBINED_3CLASS_PROBABILITY"
        ),
        "probability_calibration": {
            "enabled": False,
        },
        "threshold_policy": {
            "tuning_enabled": False,
        },
    },

    # -------------------------------------------------------------------------
    # R05 — logistic tradeability + nonlinear directional stage
    # -------------------------------------------------------------------------
    {
        "candidate_id": "R05_HIER_LOGREG_HGB_DIRECTION",
        "role": "REMEDIATION_CANDIDATE",
        "hypothesis": (
            "LINEAR_TRADEABILITY_WITH_NONLINEAR_DIRECTION_STAGE_MAY_IMPROVE_"
            "SHORT_LONG_SEPARATION_WITHOUT_OVERCOMPLICATING_NO_TRADE"
        ),
        "addresses_failure_modes": [
            "WEAK_MULTICLASS_DISCRIMINATION",
            "SYSTEMATIC_LONG_ARGMAX_UPLIFT",
            "WEAK_CONFIDENCE_ERROR_SEPARATION",
        ],
        "architecture": (
            "HIERARCHICAL_TRADEABILITY_DIRECTION"
        ),
        "family": (
            "LOGREG_STAGE_A_HGB_STAGE_B"
        ),
        "feature_scope": "EXACT_331_FROZEN_FEATURES",
        "probability_class_order": [-1, 0, 1],
        "probability_combination": {
            "SHORT": (
                "P_TRADEABLE * P_SHORT_GIVEN_TRADEABLE"
            ),
            "NO_TRADE": (
                "1 - P_TRADEABLE"
            ),
            "LONG": (
                "P_TRADEABLE * P_LONG_GIVEN_TRADEABLE"
            ),
        },
        "stage_a": {
            "target": "target_tradeable",
            "estimator": {
                "implementation": (
                    "sklearn.linear_model.LogisticRegression"
                ),
                "C": 0.03,
                "class_weight": "balanced",
                "max_iter": 2500,
                "solver": "lbfgs",
                "tol": 0.0001,
            },
            "preprocessing": {
                "standard_scaler": True,
                "scaler_fit_scope": (
                    "TRAIN_ONLY"
                ),
            },
        },
        "stage_b": {
            "target": "SHORT_VS_LONG_FROM_TARGET_CLASS",
            "fit_scope": (
                "TRUE_TRADEABLE_TRAIN_ROWS_ONLY"
            ),
            "estimator": {
                "implementation": (
                    "sklearn.ensemble.HistGradientBoostingClassifier"
                ),
                "early_stopping": False,
                "l2_regularization": 2.0,
                "learning_rate": 0.025,
                "loss": "log_loss",
                "max_iter": 220,
                "max_leaf_nodes": 7,
                "min_samples_leaf": 80,
                "random_state": 271828,
            },
            "fold_local_class_balance": (
                "INVERSE_FREQUENCY_SAMPLE_WEIGHT"
            ),
            "preprocessing": {
                "standard_scaler": False,
            },
        },
        "prediction_rule": (
            "ARGMAX_COMBINED_3CLASS_PROBABILITY"
        ),
        "probability_calibration": {
            "enabled": False,
        },
        "threshold_policy": {
            "tuning_enabled": False,
        },
    },
)


# =============================================================================
# Current G7-E gate safety
# =============================================================================

THIS_GATE_LOADS_TRAIN_VALUES = False

THIS_GATE_LOADS_VALIDATION_VALUES = False

THIS_GATE_LOADS_TEST_VALUES = False

THIS_GATE_TRAINS_MODELS = False

THIS_GATE_FITS_PREPROCESSORS = False

THIS_GATE_EVALUATES_CANDIDATES = False

THIS_GATE_SELECTS_WINNER = False

THIS_GATE_CALIBRATES_PROBABILITIES = False

THIS_GATE_TUNES_THRESHOLDS = False

THIS_GATE_EVALUATES_PNL = False

THIS_GATE_ACQUIRES_MARKET_DATA = False

THIS_GATE_WRITES_RUNTIME_LEDGERS = False

LIVE_AUTHORIZED = False

EXECUTION_AUTHORIZED = False


def canonical_json_sha256(
    value: Any,
) -> str:

    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")

    return hashlib.sha256(
        encoded
    ).hexdigest()


def candidate_fingerprint_sha256(
    candidate: Mapping[str, Any],
) -> str:

    return canonical_json_sha256(
        dict(candidate)
    )


def candidate_fingerprints() -> dict[str, str]:

    return {
        str(
            candidate[
                "candidate_id"
            ]
        ): candidate_fingerprint_sha256(
            candidate
        )
        for candidate
        in CANDIDATES
    }


def registry_core_dict() -> dict[str, Any]:

    return {
        "contract_id": CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "repository_base_commit": (
            REPOSITORY_BASE_COMMIT
        ),
        "scientific_parent_authority_commit": (
            SCIENTIFIC_PARENT_AUTHORITY_COMMIT
        ),
        "g7d_contract_id": G7D_CONTRACT_ID,
        "g7d_contract_fingerprint_sha256": (
            G7D_CONTRACT_FINGERPRINT_SHA256
        ),
        "registry_version": REGISTRY_VERSION,
        "registry_status": REGISTRY_STATUS,
        "data_authority": {
            "dataset_id": DATASET_ID,
            "dataset_sha256": DATASET_SHA256,
            "manifest_sha256": MANIFEST_SHA256,
            "feature_columns_sha256": (
                FEATURE_COLUMNS_SHA256
            ),
            "feature_count": FEATURE_COUNT,
            "train_rows": TRAIN_ROWS,
            "validation_rows": VALIDATION_ROWS,
            "test_rows": TEST_ROWS,
        },
        "target_authority": {
            "target_contract": TARGET_CONTRACT,
            "profit_atr": TARGET_PROFIT_ATR,
            "max_adverse_atr": (
                TARGET_MAX_ADVERSE_ATR
            ),
            "class_order": list(
                CLASS_ORDER
            ),
            "target_change_allowed": (
                TARGET_CHANGE_ALLOWED
            ),
        },
        "historical_control": {
            "historical_candidate_id": (
                HISTORICAL_C04_CANDIDATE_ID
            ),
            "historical_candidate_config_fingerprint_sha256": (
                HISTORICAL_C04_CONFIG_FINGERPRINT_SHA256
            ),
            "historical_registry_fingerprint_sha256": (
                HISTORICAL_REGISTRY_FINGERPRINT_SHA256
            ),
        },
        "broad_failure_modes": list(
            BROAD_FAILURE_MODES
        ),
        "forward_holdout_policy": {
            "sample_specific_forward_tuning_allowed": (
                SAMPLE_SPECIFIC_FORWARD_TUNING_ALLOWED
            ),
            "forward_30_development_use_allowed": (
                FORWARD_30_DEVELOPMENT_USE_ALLOWED
            ),
        },
        "registry_policy": {
            "candidate_count": CANDIDATE_COUNT,
            "minimum_allowed_candidates": (
                MIN_ALLOWED_CANDIDATES
            ),
            "maximum_allowed_candidates": (
                MAX_ALLOWED_CANDIDATES
            ),
            "finite": REGISTRY_FINITE,
            "frozen_before_first_fit": (
                REGISTRY_FROZEN_BEFORE_FIRST_FIT
            ),
            "change_after_first_fit_allowed": (
                REGISTRY_CHANGE_AFTER_FIRST_FIT_ALLOWED
            ),
            "results_driven_candidate_addition_allowed": (
                RESULTS_DRIVEN_CANDIDATE_ADDITION_ALLOWED
            ),
            "results_driven_hyperparameter_change_allowed": (
                RESULTS_DRIVEN_HYPERPARAMETER_CHANGE_ALLOWED
            ),
            "unbounded_grid_search_allowed": (
                UNBOUNDED_GRID_SEARCH_ALLOWED
            ),
            "bayesian_optimization_allowed": (
                BAYESIAN_OPTIMIZATION_ALLOWED
            ),
            "automl_allowed": AUTOML_ALLOWED,
            "unbounded_random_search_allowed": (
                UNBOUNDED_RANDOM_SEARCH_ALLOWED
            ),
            "all_candidates_exact_331_features": (
                ALL_CANDIDATES_USE_EXACT_331_FEATURES
            ),
            "feature_subset_search_allowed": (
                FEATURE_SUBSET_SEARCH_ALLOWED
            ),
            "random_seed": RANDOM_SEED,
        },
        "prediction_policy": {
            "prediction_rule": PREDICTION_RULE,
            "class_order": list(
                CLASS_ORDER
            ),
            "post_hoc_class_bias_allowed": (
                POST_HOC_CLASS_BIAS_ALLOWED
            ),
            "probability_calibration_enabled": (
                PROBABILITY_CALIBRATION_IN_THIS_REGISTRY
            ),
            "decision_threshold_tuning_enabled": (
                DECISION_THRESHOLD_TUNING_IN_THIS_REGISTRY
            ),
            "trade_threshold_tuning_enabled": (
                TRADE_THRESHOLD_TUNING_IN_THIS_REGISTRY
            ),
        },
        "development_authority": {
            "train_role": TRAIN_ROLE,
            "validation_role": VALIDATION_ROLE,
            "test_role": TEST_ROLE,
            "train_access_in_g7e": (
                TRAIN_ACCESS_ALLOWED_IN_G7E
            ),
            "validation_access_in_g7e": (
                VALIDATION_ACCESS_ALLOWED_IN_G7E
            ),
            "test_access_in_g7e": (
                TEST_ACCESS_ALLOWED_IN_G7E
            ),
            "test_access_during_selection": (
                TEST_ACCESS_ALLOWED_DURING_REMEDIATION_SELECTION
            ),
            "forward_30_access_during_selection": (
                OLD_FORWARD_30_ACCESS_ALLOWED_DURING_REMEDIATION_SELECTION
            ),
        },
        "eligibility_policy": (
            ELIGIBILITY_POLICY
        ),
        "selection_policy": list(
            SELECTION_POLICY
        ),
        "selection_tie_breaking": (
            SELECTION_TIE_BREAKING
        ),
        "single_metric_only_selection_allowed": (
            SINGLE_METRIC_ONLY_SELECTION_ALLOWED
        ),
        "candidates": [
            dict(candidate)
            for candidate
            in CANDIDATES
        ],
        "candidate_fingerprints": (
            candidate_fingerprints()
        ),
        "current_gate": {
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
                THIS_GATE_TRAINS_MODELS
            ),
            "preprocessor_fit": (
                THIS_GATE_FITS_PREPROCESSORS
            ),
            "candidate_evaluation": (
                THIS_GATE_EVALUATES_CANDIDATES
            ),
            "winner_selection": (
                THIS_GATE_SELECTS_WINNER
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
            "live_authorized": LIVE_AUTHORIZED,
            "execution_authorized": (
                EXECUTION_AUTHORIZED
            ),
        },
    }


def registry_fingerprint_sha256() -> str:

    return canonical_json_sha256(
        registry_core_dict()
    )


REGISTRY_FINGERPRINT_SHA256 = (
    registry_fingerprint_sha256()
)