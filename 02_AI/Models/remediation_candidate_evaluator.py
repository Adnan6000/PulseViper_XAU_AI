from __future__ import annotations

import math
from typing import Any, Mapping, Sequence, cast

import numpy as np
from sklearn.ensemble import (
    ExtraTreesClassifier,
    HistGradientBoostingClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    log_loss,
    precision_recall_fscore_support,
)
from sklearn.preprocessing import StandardScaler


CLASS_ORDER = (-1, 0, 1)
TRADEABLE_CLASS_ORDER = (0, 1)
DIRECTION_CLASS_ORDER = (-1, 1)


class RemediationEvaluationError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:
    if not condition:
        raise RemediationEvaluationError(
            reason
        )


def require_mapping(
    value: Any,
    reason: str,
) -> Mapping[str, Any]:
    if not isinstance(
        value,
        Mapping,
    ):
        raise RemediationEvaluationError(
            reason
        )

    return value


def require_sequence(
    value: Any,
    reason: str,
) -> Sequence[Mapping[str, Any]]:
    if not isinstance(
        value,
        Sequence,
    ):
        raise RemediationEvaluationError(
            reason
        )

    result: list[Mapping[str, Any]] = []

    for item in value:
        result.append(
            require_mapping(
                item,
                reason,
            )
        )

    return result


def _as_feature_matrix(
    value: Any,
    *,
    expected_feature_count: int,
    label: str,
) -> np.ndarray:
    array = np.asarray(
        value,
        dtype=np.float64,
    )

    require(
        array.ndim == 2,
        f"{label}_NOT_2D",
    )

    require(
        array.shape[0] > 0,
        f"{label}_EMPTY",
    )

    require(
        array.shape[1]
        ==
        expected_feature_count,
        (
            f"{label}_FEATURE_COUNT_MISMATCH:"
            f"{array.shape[1]}:"
            f"{expected_feature_count}"
        ),
    )

    require(
        bool(
            np.isfinite(
                array
            ).all()
        ),
        f"{label}_NON_FINITE",
    )

    return array


def _as_class_vector(
    value: Any,
    *,
    expected_rows: int,
    label: str,
) -> np.ndarray:
    array = np.asarray(
        value
    )

    require(
        array.ndim == 1,
        f"{label}_NOT_1D",
    )

    require(
        array.shape[0]
        ==
        expected_rows,
        (
            f"{label}_ROW_COUNT_MISMATCH:"
            f"{array.shape[0]}:"
            f"{expected_rows}"
        ),
    )

    require(
        bool(
            np.isin(
                array,
                CLASS_ORDER,
            ).all()
        ),
        f"{label}_INVALID_CLASS",
    )

    return np.asarray(
        array,
        dtype=np.int8,
    )


def _as_tradeable_vector(
    value: Any,
    *,
    expected_rows: int,
    label: str,
) -> np.ndarray:
    array = np.asarray(
        value
    )

    require(
        array.ndim == 1,
        f"{label}_NOT_1D",
    )

    require(
        array.shape[0]
        ==
        expected_rows,
        (
            f"{label}_ROW_COUNT_MISMATCH:"
            f"{array.shape[0]}:"
            f"{expected_rows}"
        ),
    )

    require(
        bool(
            np.isin(
                array,
                TRADEABLE_CLASS_ORDER,
            ).all()
        ),
        f"{label}_INVALID_CLASS",
    )

    return np.asarray(
        array,
        dtype=np.int8,
    )


def validate_supervised_inputs(
    X_train: Any,
    y_class_train: Any,
    y_tradeable_train: Any,
    X_validation: Any,
    y_class_validation: Any,
    y_tradeable_validation: Any,
    *,
    expected_feature_count: int,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    train_matrix = _as_feature_matrix(
        X_train,
        expected_feature_count=(
            expected_feature_count
        ),
        label="TRAIN_X",
    )

    validation_matrix = _as_feature_matrix(
        X_validation,
        expected_feature_count=(
            expected_feature_count
        ),
        label="VALIDATION_X",
    )

    train_class = _as_class_vector(
        y_class_train,
        expected_rows=(
            train_matrix.shape[0]
        ),
        label="TRAIN_TARGET_CLASS",
    )

    train_tradeable = _as_tradeable_vector(
        y_tradeable_train,
        expected_rows=(
            train_matrix.shape[0]
        ),
        label="TRAIN_TARGET_TRADEABLE",
    )

    validation_class = _as_class_vector(
        y_class_validation,
        expected_rows=(
            validation_matrix.shape[0]
        ),
        label="VALIDATION_TARGET_CLASS",
    )

    validation_tradeable = (
        _as_tradeable_vector(
            y_tradeable_validation,
            expected_rows=(
                validation_matrix.shape[0]
            ),
            label=(
                "VALIDATION_TARGET_TRADEABLE"
            ),
        )
    )

    expected_train_tradeable = (
        train_class != 0
    ).astype(
        np.int8
    )

    expected_validation_tradeable = (
        validation_class != 0
    ).astype(
        np.int8
    )

    require(
        bool(
            np.array_equal(
                train_tradeable,
                expected_train_tradeable,
            )
        ),
        "TRAIN_TRADEABLE_CLASS_INCONSISTENCY",
    )

    require(
        bool(
            np.array_equal(
                validation_tradeable,
                expected_validation_tradeable,
            )
        ),
        (
            "VALIDATION_TRADEABLE_CLASS_"
            "INCONSISTENCY"
        ),
    )

    for label in CLASS_ORDER:
        require(
            bool(
                np.any(
                    train_class
                    ==
                    label
                )
            ),
            (
                "TRAIN_CLASS_MISSING:"
                f"{label}"
            ),
        )

        require(
            bool(
                np.any(
                    validation_class
                    ==
                    label
                )
            ),
            (
                "VALIDATION_CLASS_MISSING:"
                f"{label}"
            ),
        )

    return (
        train_matrix,
        train_class,
        train_tradeable,
        validation_matrix,
        validation_class,
        validation_tradeable,
    )


def _inverse_frequency_sample_weight(
    y: np.ndarray,
) -> np.ndarray:
    unique, counts = np.unique(
        y,
        return_counts=True,
    )

    require(
        unique.shape[0] >= 2,
        "SAMPLE_WEIGHT_SINGLE_CLASS",
    )

    total = float(
        y.shape[0]
    )

    class_count = float(
        unique.shape[0]
    )

    weight_map = {
        int(label): (
            total
            /
            (
                class_count
                *
                float(count)
            )
        )
        for label, count
        in zip(
            unique,
            counts,
        )
    }

    weights = np.asarray(
        [
            weight_map[
                int(label)
            ]
            for label in y
        ],
        dtype=np.float64,
    )

    require(
        bool(
            np.isfinite(
                weights
            ).all()
        ),
        "SAMPLE_WEIGHT_NON_FINITE",
    )

    return weights


def _build_estimator(
    config: Mapping[str, Any],
) -> Any:
    implementation = str(
        config.get(
            "implementation",
            "",
        )
    )

    kwargs = {
        key: value
        for key, value
        in config.items()
        if key
        !=
        "implementation"
    }

    if (
        implementation
        ==
        "sklearn.linear_model.LogisticRegression"
    ):
        return LogisticRegression(
            **kwargs
        )

    if (
        implementation
        ==
        "sklearn.ensemble.HistGradientBoostingClassifier"
    ):
        return HistGradientBoostingClassifier(
            **kwargs
        )

    if (
        implementation
        ==
        "sklearn.ensemble.ExtraTreesClassifier"
    ):
        return ExtraTreesClassifier(
            **kwargs
        )

    raise RemediationEvaluationError(
        (
            "UNSUPPORTED_ESTIMATOR:"
            f"{implementation}"
        )
    )


def _fit_estimator(
    estimator_config: Mapping[str, Any],
    preprocessing: Mapping[str, Any],
    X_train: np.ndarray,
    y_train: np.ndarray,
    fold_local_class_balance: Any = None,
) -> tuple[Any, Any]:
    transformed = X_train

    scaler: Any = None

    standard_scaler = preprocessing.get(
        "standard_scaler",
        False,
    )

    if standard_scaler is True:
        scaler = StandardScaler()

        transformed = (
            scaler.fit_transform(
                X_train
            )
        )

    elif standard_scaler is not False:
        raise RemediationEvaluationError(
            "UNSUPPORTED_STANDARD_SCALER_POLICY"
        )

    estimator = _build_estimator(
        estimator_config
    )

    fit_kwargs: dict[str, Any] = {}

    if (
        fold_local_class_balance
        is not None
    ):
        require(
            fold_local_class_balance
            ==
            "INVERSE_FREQUENCY_SAMPLE_WEIGHT",
            (
                "UNSUPPORTED_CLASS_BALANCE:"
                f"{fold_local_class_balance}"
            ),
        )

        fit_kwargs[
            "sample_weight"
        ] = (
            _inverse_frequency_sample_weight(
                y_train
            )
        )

    estimator.fit(
        transformed,
        y_train,
        **fit_kwargs,
    )

    return (
        estimator,
        scaler,
    )


def _transform(
    scaler: Any,
    X: np.ndarray,
) -> np.ndarray:
    if scaler is None:
        return X

    transformed = scaler.transform(
        X
    )

    return np.asarray(
        transformed,
        dtype=np.float64,
    )


def _predict_proba_reordered(
    estimator: Any,
    X: np.ndarray,
    class_order: Sequence[int],
) -> np.ndarray:
    raw = np.asarray(
        estimator.predict_proba(
            X
        ),
        dtype=np.float64,
    )

    classes = tuple(
        int(value)
        for value
        in estimator.classes_
    )

    for label in class_order:
        require(
            label in classes,
            (
                "ESTIMATOR_CLASS_MISSING:"
                f"{label}"
            ),
        )

    columns = [
        classes.index(
            label
        )
        for label
        in class_order
    ]

    probabilities = raw[
        :,
        columns,
    ]

    require(
        bool(
            np.isfinite(
                probabilities
            ).all()
        ),
        "PROBABILITY_NON_FINITE",
    )

    require(
        bool(
            (
                probabilities
                >=
                0.0
            ).all()
        ),
        "PROBABILITY_BELOW_ZERO",
    )

    require(
        bool(
            (
                probabilities
                <=
                1.0
            ).all()
        ),
        "PROBABILITY_ABOVE_ONE",
    )

    require(
        bool(
            np.allclose(
                probabilities.sum(
                    axis=1
                ),
                1.0,
                rtol=1e-9,
                atol=1e-9,
            )
        ),
        "PROBABILITY_ROW_SUM_MISMATCH",
    )

    return probabilities


def fit_predict_candidate(
    candidate: Mapping[str, Any],
    X_train: np.ndarray,
    y_class_train: np.ndarray,
    y_tradeable_train: np.ndarray,
    X_validation: np.ndarray,
) -> np.ndarray:
    architecture = str(
        candidate.get(
            "architecture",
            "",
        )
    )

    if (
        architecture
        ==
        "FLAT_3CLASS"
    ):
        estimator_config = require_mapping(
            candidate.get(
                "estimator"
            ),
            "FLAT_ESTIMATOR_CONFIG_MISSING",
        )

        preprocessing = require_mapping(
            candidate.get(
                "preprocessing",
                {},
            ),
            (
                "FLAT_PREPROCESSING_"
                "CONFIG_INVALID"
            ),
        )

        estimator, scaler = (
            _fit_estimator(
                estimator_config,
                preprocessing,
                X_train,
                y_class_train,
                candidate.get(
                    "fold_local_class_balance"
                ),
            )
        )

        X_eval = _transform(
            scaler,
            X_validation,
        )

        return _predict_proba_reordered(
            estimator,
            X_eval,
            CLASS_ORDER,
        )

    if (
        architecture
        ==
        "HIERARCHICAL_TRADEABILITY_DIRECTION"
    ):
        stage_a = require_mapping(
            candidate.get(
                "stage_a"
            ),
            "STAGE_A_CONFIG_MISSING",
        )

        stage_b = require_mapping(
            candidate.get(
                "stage_b"
            ),
            "STAGE_B_CONFIG_MISSING",
        )

        stage_a_estimator_config = (
            require_mapping(
                stage_a.get(
                    "estimator"
                ),
                "STAGE_A_ESTIMATOR_MISSING",
            )
        )

        stage_a_preprocessing = (
            require_mapping(
                stage_a.get(
                    "preprocessing",
                    {},
                ),
                (
                    "STAGE_A_PREPROCESSING_"
                    "INVALID"
                ),
            )
        )

        (
            stage_a_estimator,
            stage_a_scaler,
        ) = _fit_estimator(
            stage_a_estimator_config,
            stage_a_preprocessing,
            X_train,
            y_tradeable_train,
            stage_a.get(
                "fold_local_class_balance"
            ),
        )

        tradeability_probabilities = (
            _predict_proba_reordered(
                stage_a_estimator,
                _transform(
                    stage_a_scaler,
                    X_validation,
                ),
                TRADEABLE_CLASS_ORDER,
            )
        )

        p_tradeable = (
            tradeability_probabilities[
                :,
                1,
            ]
        )

        stage_b_mask = (
            y_tradeable_train
            ==
            1
        )

        require(
            bool(
                np.any(
                    stage_b_mask
                )
            ),
            "STAGE_B_NO_TRADEABLE_ROWS",
        )

        stage_b_y = (
            y_class_train[
                stage_b_mask
            ]
        )

        for label in (
            DIRECTION_CLASS_ORDER
        ):
            require(
                bool(
                    np.any(
                        stage_b_y
                        ==
                        label
                    )
                ),
                (
                    "STAGE_B_CLASS_MISSING:"
                    f"{label}"
                ),
            )

        stage_b_estimator_config = (
            require_mapping(
                stage_b.get(
                    "estimator"
                ),
                "STAGE_B_ESTIMATOR_MISSING",
            )
        )

        stage_b_preprocessing = (
            require_mapping(
                stage_b.get(
                    "preprocessing",
                    {},
                ),
                (
                    "STAGE_B_PREPROCESSING_"
                    "INVALID"
                ),
            )
        )

        (
            stage_b_estimator,
            stage_b_scaler,
        ) = _fit_estimator(
            stage_b_estimator_config,
            stage_b_preprocessing,
            X_train[
                stage_b_mask
            ],
            stage_b_y,
            stage_b.get(
                "fold_local_class_balance"
            ),
        )

        direction_probabilities = (
            _predict_proba_reordered(
                stage_b_estimator,
                _transform(
                    stage_b_scaler,
                    X_validation,
                ),
                DIRECTION_CLASS_ORDER,
            )
        )

        probabilities = np.column_stack(
            (
                p_tradeable
                *
                direction_probabilities[
                    :,
                    0,
                ],
                1.0
                -
                p_tradeable,
                p_tradeable
                *
                direction_probabilities[
                    :,
                    1,
                ],
            )
        )

        require(
            bool(
                np.allclose(
                    probabilities.sum(
                        axis=1
                    ),
                    1.0,
                    rtol=1e-9,
                    atol=1e-9,
                )
            ),
            (
                "HIERARCHICAL_PROBABILITY_"
                "SUM_MISMATCH"
            ),
        )

        return np.asarray(
            probabilities,
            dtype=np.float64,
        )

    raise RemediationEvaluationError(
        (
            "UNSUPPORTED_ARCHITECTURE:"
            f"{architecture}"
        )
    )


def _argmax_predictions(
    probabilities: np.ndarray,
) -> np.ndarray:
    order = np.asarray(
        CLASS_ORDER,
        dtype=np.int8,
    )

    return order[
        np.argmax(
            probabilities,
            axis=1,
        )
    ]


def _multiclass_brier(
    y_true: np.ndarray,
    probabilities: np.ndarray,
) -> float:
    one_hot = np.zeros_like(
        probabilities,
        dtype=np.float64,
    )

    for index, label in enumerate(
        CLASS_ORDER
    ):
        one_hot[
            :,
            index,
        ] = (
            y_true
            ==
            label
        ).astype(
            np.float64
        )

    value = float(
        np.mean(
            np.sum(
                (
                    probabilities
                    -
                    one_hot
                )
                ** 2,
                axis=1,
            )
        )
    )

    require(
        math.isfinite(
            value
        ),
        "BRIER_NON_FINITE",
    )

    return value


def compute_validation_metrics(
    y_true: np.ndarray,
    probabilities: np.ndarray,
) -> dict[str, Any]:
    require(
        probabilities.shape
        ==
        (
            y_true.shape[0],
            3,
        ),
        "PROBABILITY_SHAPE_MISMATCH",
    )

    predictions = (
        _argmax_predictions(
            probabilities
        )
    )

    metric_result = (
        precision_recall_fscore_support(
            y_true,
            predictions,
            labels=list(
                CLASS_ORDER
            ),
            average=None,
            zero_division=cast(
                Any,
                0,
            ),
        )
    )

    precision = np.asarray(
        metric_result[0],
        dtype=np.float64,
    )

    recall = np.asarray(
        metric_result[1],
        dtype=np.float64,
    )

    f1 = np.asarray(
        metric_result[2],
        dtype=np.float64,
    )

    prediction_counts = {
        "SHORT": int(
            np.sum(
                predictions == -1
            )
        ),
        "NO_TRADE": int(
            np.sum(
                predictions == 0
            )
        ),
        "LONG": int(
            np.sum(
                predictions == 1
            )
        ),
    }

    outcome_counts = {
        "SHORT": int(
            np.sum(
                y_true == -1
            )
        ),
        "NO_TRADE": int(
            np.sum(
                y_true == 0
            )
        ),
        "LONG": int(
            np.sum(
                y_true == 1
            )
        ),
    }

    n_rows = float(
        y_true.shape[0]
    )

    prediction_shares = {
        key: (
            float(value)
            /
            n_rows
        )
        for key, value
        in prediction_counts.items()
    }

    outcome_shares = {
        key: (
            float(value)
            /
            n_rows
        )
        for key, value
        in outcome_counts.items()
    }

    probability_means = {
        "SHORT": float(
            np.mean(
                probabilities[
                    :,
                    0,
                ]
            )
        ),
        "NO_TRADE": float(
            np.mean(
                probabilities[
                    :,
                    1,
                ]
            )
        ),
        "LONG": float(
            np.mean(
                probabilities[
                    :,
                    2,
                ]
            )
        ),
    }

    confidence = np.max(
        probabilities,
        axis=1,
    )

    correct_mask = (
        predictions
        ==
        y_true
    )

    incorrect_mask = (
        ~correct_mask
    )

    mean_correct_confidence = (
        float(
            np.mean(
                confidence[
                    correct_mask
                ]
            )
        )
        if bool(
            np.any(
                correct_mask
            )
        )
        else 0.0
    )

    mean_incorrect_confidence = (
        float(
            np.mean(
                confidence[
                    incorrect_mask
                ]
            )
        )
        if bool(
            np.any(
                incorrect_mask
            )
        )
        else 0.0
    )

    macro_f1 = float(
        np.mean(
            f1
        )
    )

    balanced_accuracy = float(
        balanced_accuracy_score(
            y_true,
            predictions,
        )
    )

    accuracy = float(
        accuracy_score(
            y_true,
            predictions,
        )
    )

    brier = _multiclass_brier(
        y_true,
        probabilities,
    )

    loss = float(
        log_loss(
            y_true,
            probabilities,
            labels=list(
                CLASS_ORDER
            ),
        )
    )

    metrics: dict[str, Any] = {
        "exact_class_accuracy": accuracy,
        "macro_f1": macro_f1,
        "balanced_accuracy": (
            balanced_accuracy
        ),
        "minimum_per_class_recall": float(
            np.min(
                recall
            )
        ),
        "short_precision": float(
            precision[0]
        ),
        "short_recall": float(
            recall[0]
        ),
        "short_f1": float(
            f1[0]
        ),
        "no_trade_precision": float(
            precision[1]
        ),
        "no_trade_recall": float(
            recall[1]
        ),
        "no_trade_f1": float(
            f1[1]
        ),
        "long_precision": float(
            precision[2]
        ),
        "long_recall": float(
            recall[2]
        ),
        "long_f1": float(
            f1[2]
        ),
        "multiclass_brier": brier,
        "multiclass_log_loss": loss,
        "prediction_counts": (
            prediction_counts
        ),
        "prediction_shares": (
            prediction_shares
        ),
        "outcome_counts": (
            outcome_counts
        ),
        "outcome_shares": (
            outcome_shares
        ),
        "mean_probability_by_class": (
            probability_means
        ),
        "mean_correct_confidence": (
            mean_correct_confidence
        ),
        "mean_incorrect_confidence": (
            mean_incorrect_confidence
        ),
    }

    scalar_metrics = (
        "exact_class_accuracy",
        "macro_f1",
        "balanced_accuracy",
        "minimum_per_class_recall",
        "short_precision",
        "short_recall",
        "short_f1",
        "no_trade_precision",
        "no_trade_recall",
        "no_trade_f1",
        "long_precision",
        "long_recall",
        "long_f1",
        "multiclass_brier",
        "multiclass_log_loss",
        "mean_correct_confidence",
        "mean_incorrect_confidence",
    )

    require(
        all(
            math.isfinite(
                float(
                    metrics[
                        key
                    ]
                )
            )
            for key
            in scalar_metrics
        ),
        "NON_FINITE_VALIDATION_METRIC",
    )

    return metrics


def evaluate_eligibility(
    metrics: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> tuple[bool, list[str]]:
    failures: list[str] = []

    if (
        policy.get(
            "all_metrics_must_be_finite"
        )
        is True
    ):
        scalar_keys = (
            "exact_class_accuracy",
            "macro_f1",
            "balanced_accuracy",
            "minimum_per_class_recall",
            "short_recall",
            "no_trade_recall",
            "long_recall",
            "multiclass_brier",
            "multiclass_log_loss",
        )

        if not all(
            math.isfinite(
                float(
                    metrics[
                        key
                    ]
                )
            )
            for key
            in scalar_keys
        ):
            failures.append(
                "NON_FINITE_METRIC"
            )

    counts_raw = require_mapping(
        metrics.get(
            "prediction_counts"
        ),
        "PREDICTION_COUNTS_MISSING",
    )

    shares_raw = require_mapping(
        metrics.get(
            "prediction_shares"
        ),
        "PREDICTION_SHARES_MISSING",
    )

    if (
        policy.get(
            "all_three_classes_must_be_predicted"
        )
        is True
    ):
        if any(
            int(
                counts_raw.get(
                    label,
                    0,
                )
            )
            <=
            0
            for label
            in (
                "SHORT",
                "NO_TRADE",
                "LONG",
            )
        ):
            failures.append(
                "NOT_ALL_CLASSES_PREDICTED"
            )

    recall_rules = (
        (
            "short_recall_must_be_positive",
            "short_recall",
            "SHORT_RECALL_NOT_POSITIVE",
        ),
        (
            "no_trade_recall_must_be_positive",
            "no_trade_recall",
            "NO_TRADE_RECALL_NOT_POSITIVE",
        ),
        (
            "long_recall_must_be_positive",
            "long_recall",
            "LONG_RECALL_NOT_POSITIVE",
        ),
    )

    for (
        policy_key,
        metric_key,
        failure,
    ) in recall_rules:
        if (
            policy.get(
                policy_key
            )
            is True
            and
            float(
                metrics[
                    metric_key
                ]
            )
            <=
            0.0
        ):
            failures.append(
                failure
            )

    maximum_share = float(
        policy.get(
            "maximum_single_predicted_class_share",
            1.0,
        )
    )

    minimum_share = float(
        policy.get(
            "minimum_single_predicted_class_share",
            0.0,
        )
    )

    for label in (
        "SHORT",
        "NO_TRADE",
        "LONG",
    ):
        share = float(
            shares_raw[
                label
            ]
        )

        if (
            share
            >
            maximum_share
        ):
            failures.append(
                (
                    "PREDICTED_CLASS_SHARE_"
                    f"ABOVE_MAX:{label}"
                )
            )

        if (
            share
            <
            minimum_share
        ):
            failures.append(
                (
                    "PREDICTED_CLASS_SHARE_"
                    f"BELOW_MIN:{label}"
                )
            )

    return (
        len(
            failures
        )
        ==
        0,
        failures,
    )


def evaluate_candidate(
    candidate: Mapping[str, Any],
    X_train: np.ndarray,
    y_class_train: np.ndarray,
    y_tradeable_train: np.ndarray,
    X_validation: np.ndarray,
    y_class_validation: np.ndarray,
    eligibility_policy: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_id = str(
        candidate.get(
            "candidate_id",
            "",
        )
    )

    require(
        bool(
            candidate_id
        ),
        "CANDIDATE_ID_MISSING",
    )

    probabilities = (
        fit_predict_candidate(
            candidate,
            X_train,
            y_class_train,
            y_tradeable_train,
            X_validation,
        )
    )

    metrics = (
        compute_validation_metrics(
            y_class_validation,
            probabilities,
        )
    )

    eligible, failures = (
        evaluate_eligibility(
            metrics,
            eligibility_policy,
        )
    )

    return {
        "candidate_id": candidate_id,
        "role": candidate.get(
            "role"
        ),
        "architecture": candidate.get(
            "architecture"
        ),
        "family": candidate.get(
            "family"
        ),
        "eligible": eligible,
        "eligibility_failures": failures,
        "validation_metrics": metrics,
    }


def _selection_key(
    report: Mapping[str, Any],
    selection_policy: Sequence[
        Mapping[str, Any]
    ],
) -> tuple[float, ...]:
    metrics_raw = require_mapping(
        report.get(
            "validation_metrics"
        ),
        (
            "SELECTION_METRICS_MISSING:"
            +
            str(
                report.get(
                    "candidate_id"
                )
            )
        ),
    )

    result: list[float] = []

    expected_priority = 1

    for rule in selection_policy:
        priority = int(
            rule.get(
                "priority",
                -1,
            )
        )

        require(
            priority
            ==
            expected_priority,
            "SELECTION_PRIORITY_NOT_CONTIGUOUS",
        )

        expected_priority += 1

        metric = str(
            rule.get(
                "metric",
                "",
            )
        )

        direction = str(
            rule.get(
                "direction",
                "",
            )
        )

        require(
            metric
            in
            metrics_raw,
            (
                "SELECTION_METRIC_MISSING:"
                f"{metric}"
            ),
        )

        value = float(
            metrics_raw[
                metric
            ]
        )

        require(
            math.isfinite(
                value
            ),
            (
                "SELECTION_METRIC_NON_FINITE:"
                f"{metric}"
            ),
        )

        if (
            direction
            ==
            "MAXIMIZE"
        ):
            result.append(
                value
            )

        elif (
            direction
            ==
            "MINIMIZE"
        ):
            result.append(
                -value
            )

        else:
            raise RemediationEvaluationError(
                (
                    "UNKNOWN_SELECTION_DIRECTION:"
                    f"{direction}"
                )
            )

    return tuple(
        result
    )


def select_winner(
    reports: Sequence[
        Mapping[str, Any]
    ],
    selection_policy: Sequence[
        Mapping[str, Any]
    ],
    if_all_fail: str,
) -> dict[str, Any]:
    eligible: list[
        Mapping[str, Any]
    ] = [
        report
        for report
        in reports
        if report.get(
            "eligible"
        )
        is True
    ]

    if not eligible:
        require(
            if_all_fail
            ==
            "NO_WINNER",
            "INVALID_ALL_FAIL_POLICY",
        )

        return {
            "status": "NO_WINNER",
            "winner_candidate_id": None,
            "reason": (
                "NO_CANDIDATE_PASSED_"
                "FROZEN_ELIGIBILITY_POLICY"
            ),
        }

    winner = max(
        eligible,
        key=lambda report: (
            _selection_key(
                report,
                selection_policy,
            )
        ),
    )

    winner_id = winner[
        "candidate_id"
    ]

    return {
        "status": (
            "VALIDATION_WINNER_SELECTED"
        ),
        "winner_candidate_id": (
            winner_id
        ),
        "selection_key": list(
            _selection_key(
                winner,
                selection_policy,
            )
        ),
        "reason": (
            "FROZEN_G7E_LEXICOGRAPHIC_"
            "SELECTION_POLICY"
        ),
    }


def evaluate_frozen_registry(
    candidates: Sequence[
        Mapping[str, Any]
    ],
    eligibility_policy: Mapping[str, Any],
    selection_policy: Sequence[
        Mapping[str, Any]
    ],
    X_train: Any,
    y_class_train: Any,
    y_tradeable_train: Any,
    X_validation: Any,
    y_class_validation: Any,
    y_tradeable_validation: Any,
    *,
    expected_feature_count: int,
) -> dict[str, Any]:
    require(
        4
        <=
        len(
            candidates
        )
        <=
        12,
        "CANDIDATE_COUNT_OUT_OF_BOUNDS",
    )

    (
        train_matrix,
        train_class,
        train_tradeable,
        validation_matrix,
        validation_class,
        _validation_tradeable,
    ) = validate_supervised_inputs(
        X_train,
        y_class_train,
        y_tradeable_train,
        X_validation,
        y_class_validation,
        y_tradeable_validation,
        expected_feature_count=(
            expected_feature_count
        ),
    )

    reports: list[
        dict[str, Any]
    ] = []

    for candidate in candidates:
        reports.append(
            evaluate_candidate(
                candidate,
                train_matrix,
                train_class,
                train_tradeable,
                validation_matrix,
                validation_class,
                eligibility_policy,
            )
        )

    selection = select_winner(
        reports,
        selection_policy,
        str(
            eligibility_policy.get(
                "if_all_candidates_fail",
                "",
            )
        ),
    )

    return {
        "research_scope": (
            "FROZEN_REMEDIATION_TRAIN_FIT_"
            "VALIDATION_SELECTION_ONLY"
        ),
        "candidate_count": len(
            reports
        ),
        "candidate_reports": reports,
        "selection": selection,
        "test_values_loaded": False,
        "forward_30_used": False,
        "pnl_evaluated": False,
    }