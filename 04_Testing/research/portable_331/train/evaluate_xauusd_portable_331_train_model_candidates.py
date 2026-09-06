#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    balanced_accuracy_score,
    f1_score,
    log_loss,
    precision_recall_fscore_support,
)
from sklearn.preprocessing import StandardScaler


REGISTRY_ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_MODEL_CANDIDATE_REGISTRY_DESIGN_V1"
)

REGISTRY_CONTRACT_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_MODEL_CANDIDATE_REGISTRY_V1"
)

EXPECTED_REGISTRY_FINGERPRINT_SHA256 = (
    "b8088bb34ce8940f7de5946fbb9b0fd20f40d7cc93a76b76fd7975591f00066c"
)

EXPECTED_CANDIDATE_IDS = (
    "C01_FLAT_LOGREG_BALANCED_C005",
    "C02_FLAT_LOGREG_BALANCED_C020",
    "C03_FLAT_HGB_SHALLOW",
    "C04_FLAT_EXTRA_TREES_CONSTRAINED",
    "C05_HIER_LOGREG_REGULARIZED",
    "C06_HIER_HGB_LOGREG_CONSTRAINED",
)

CLASS_ORDER = (-1, 0, 1)
DIRECTION_CLASS_ORDER = (-1, 1)
TRADEABLE_CLASS_ORDER = (0, 1)

REQUIRED_FOLD_METRICS = (
    "balanced_accuracy_3class",
    "macro_f1_3class",
    "directional_macro_f1_short_long",
    "short_precision",
    "short_recall",
    "short_f1",
    "no_trade_precision",
    "no_trade_recall",
    "no_trade_f1",
    "long_precision",
    "long_recall",
    "long_f1",
    "log_loss_3class",
    "multiclass_brier",
    "predicted_trade_coverage",
)


class EvaluatorContractError(ValueError):
    """Raised when the frozen evaluator contract is violated."""


class CandidateFoldFailure(RuntimeError):
    """Raised when one candidate cannot be evaluated safely on one fold."""


@dataclass(frozen=True)
class FoldSpec:
    fold_id: str
    train_start: int
    train_stop: int
    validation_start: int
    validation_stop: int
    purge_rows: int = 12

    def validate(self, n_rows: int) -> None:
        values = (
            self.train_start,
            self.train_stop,
            self.validation_start,
            self.validation_stop,
            self.purge_rows,
        )

        if any(not isinstance(value, int) for value in values):
            raise EvaluatorContractError(
                "Fold boundaries and purge_rows must be integers."
            )

        if not self.fold_id:
            raise EvaluatorContractError("fold_id must be non-empty.")

        if self.purge_rows < 0:
            raise EvaluatorContractError("purge_rows must be >= 0.")

        if not (0 <= self.train_start < self.train_stop <= n_rows):
            raise EvaluatorContractError(
                f"Invalid train range for {self.fold_id}."
            )

        if not (
            0
            <= self.validation_start
            < self.validation_stop
            <= n_rows
        ):
            raise EvaluatorContractError(
                f"Invalid validation range for {self.fold_id}."
            )

        if self.train_stop > self.validation_start:
            raise EvaluatorContractError(
                f"Train/validation overlap in {self.fold_id}."
            )

        actual_gap = self.validation_start - self.train_stop

        if actual_gap < self.purge_rows:
            raise EvaluatorContractError(
                f"Insufficient purge gap in {self.fold_id}: "
                f"required={self.purge_rows}, actual={actual_gap}."
            )

    def train_slice(self) -> slice:
        return slice(self.train_start, self.train_stop)

    def validation_slice(self) -> slice:
        return slice(self.validation_start, self.validation_stop)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _canonical_json_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def load_frozen_candidate_registry(path: str | Path) -> dict[str, Any]:
    registry_path = Path(path)

    with registry_path.open(
        "r",
        encoding="utf-8-sig",
    ) as handle:
        payload = json.load(handle)

    validate_frozen_candidate_registry(payload)

    return payload


def validate_frozen_candidate_registry(
    payload: Mapping[str, Any],
) -> None:
    try:
        contract = payload["contract"]
        decision = payload["decision"]
        next_contract = payload["next_decision_contract"]
        fingerprint = payload["registry_fingerprint"]

    except KeyError as exc:
        raise EvaluatorContractError(
            f"Missing registry key: {exc.args[0]}"
        ) from exc

    if payload.get("valid") is not True:
        raise EvaluatorContractError(
            "Registry design must be valid=true."
        )

    if payload.get("analysis_version") != REGISTRY_ANALYSIS_VERSION:
        raise EvaluatorContractError(
            "Unexpected registry analysis_version."
        )

    if contract.get("contract_version") != REGISTRY_CONTRACT_VERSION:
        raise EvaluatorContractError(
            "Unexpected registry contract_version."
        )

    policy = contract.get(
        "candidate_registry_policy",
        {},
    )

    if policy.get("finite_registry") is not True:
        raise EvaluatorContractError(
            "Candidate registry must be finite."
        )

    if (
        policy.get("registry_frozen_before_first_model_fit")
        is not True
    ):
        raise EvaluatorContractError(
            "Registry must be frozen before first fit."
        )

    if (
        policy.get("registry_change_after_first_fit_allowed")
        is not False
    ):
        raise EvaluatorContractError(
            "Registry changes after first fit must be blocked."
        )

    if (
        policy.get("results_driven_candidate_addition_allowed")
        is not False
    ):
        raise EvaluatorContractError(
            "Results-driven candidate addition must be blocked."
        )

    if (
        policy.get("results_driven_hyperparameter_change_allowed")
        is not False
    ):
        raise EvaluatorContractError(
            "Results-driven hyperparameter changes must be blocked."
        )

    if (
        policy.get("all_candidates_use_exact_331_features")
        is not True
    ):
        raise EvaluatorContractError(
            "All candidates must use the exact 331-feature contract."
        )

    anti_overfit = contract.get(
        "anti_overfit_policy",
        {},
    )

    blocked_flags = (
        "bayesian_optimization_allowed",
        "candidate_addition_after_results_allowed",
        "feature_selection_during_candidate_search_allowed",
        "hyperparameter_grid_search_allowed",
        "test_peeking_allowed",
        "threshold_search_during_candidate_search_allowed",
        "validation_split_peeking_allowed",
    )

    for key in blocked_flags:
        if anti_overfit.get(key) is not False:
            raise EvaluatorContractError(
                f"Anti-overfit flag must be false: {key}"
            )

    candidates = contract.get("candidates")

    if not isinstance(candidates, list):
        raise EvaluatorContractError(
            "contract.candidates must be a list."
        )

    candidate_ids = tuple(
        candidate.get("candidate_id")
        for candidate in candidates
    )

    if candidate_ids != EXPECTED_CANDIDATE_IDS:
        raise EvaluatorContractError(
            "Frozen six-candidate registry does not match V1."
        )

    if policy.get("candidate_count") != len(EXPECTED_CANDIDATE_IDS):
        raise EvaluatorContractError(
            "candidate_count does not match frozen V1 registry."
        )

    frozen_train = contract.get(
        "frozen_train_identity",
        {},
    )

    if frozen_train.get("feature_count") != 331:
        raise EvaluatorContractError(
            "Frozen TRAIN feature_count must be 331."
        )

    fold_policy = contract.get(
        "fold_training_policy",
        {},
    )

    if fold_policy.get("walk_forward_fold_count") != 4:
        raise EvaluatorContractError(
            "Frozen walk-forward fold count must be 4."
        )

    if fold_policy.get("purge_rows") != 12:
        raise EvaluatorContractError(
            "Frozen purge_rows must be 12."
        )

    if fold_policy.get("chronological_only") is not True:
        raise EvaluatorContractError(
            "Walk-forward evaluation must be chronological only."
        )

    if fold_policy.get("shuffle_allowed") is not False:
        raise EvaluatorContractError(
            "Shuffle must remain disabled."
        )

    if (
        fold_policy.get("portable_validation_access_allowed")
        is not False
    ):
        raise EvaluatorContractError(
            "Portable VALIDATION access must remain blocked."
        )

    if (
        fold_policy.get("portable_test_access_allowed")
        is not False
    ):
        raise EvaluatorContractError(
            "Portable TEST access must remain blocked."
        )

    prediction_policy = contract.get(
        "prediction_policy",
        {},
    )

    if prediction_policy.get("class_order") != list(CLASS_ORDER):
        raise EvaluatorContractError(
            "Prediction class order must be [-1, 0, 1]."
        )

    prediction_blocked_flags = (
        "decision_threshold_tuning_allowed",
        "post_hoc_class_bias_allowed",
        "probability_calibration_allowed",
        "trade_threshold_tuning_allowed",
    )

    for key in prediction_blocked_flags:
        if prediction_policy.get(key) is not False:
            raise EvaluatorContractError(
                f"Prediction tuning flag must be false: {key}"
            )

    boundary = contract.get(
        "current_gate_boundary",
        {},
    )

    boundary_false_flags = (
        "model_artifacts_written",
        "model_fit_performed",
        "scaler_fit_performed",
        "test_values_loaded",
        "train_values_loaded",
        "validation_values_loaded",
        "live_authorized",
    )

    for key in boundary_false_flags:
        if boundary.get(key) is not False:
            raise EvaluatorContractError(
                f"Current gate boundary must remain false: {key}"
            )

    if (
        decision.get("candidate_real_fit_authorized_next")
        is not False
    ):
        raise EvaluatorContractError(
            "Real candidate fit must not yet be authorized."
        )

    if (
        decision.get(
            "candidate_training_implementation_authorized_next"
        )
        is not True
    ):
        raise EvaluatorContractError(
            "Evaluator implementation must be authorized next."
        )

    if decision.get("validation_access_authorized") is not False:
        raise EvaluatorContractError(
            "VALIDATION access must remain blocked."
        )

    if decision.get("test_access_authorized") is not False:
        raise EvaluatorContractError(
            "TEST access must remain blocked."
        )

    if (
        next_contract.get(
            "real_candidate_fit_not_authorized_until_evaluator_tests_pass"
        )
        is not True
    ):
        raise EvaluatorContractError(
            "Synthetic evaluator tests must gate real candidate fit."
        )

    registry_sha = fingerprint.get("sha256")
    decision_sha = decision.get(
        "candidate_registry_fingerprint_sha256"
    )

    if not registry_sha or registry_sha != decision_sha:
        raise EvaluatorContractError(
            "Registry fingerprint fields are inconsistent."
        )

    if registry_sha != EXPECTED_REGISTRY_FINGERPRINT_SHA256:
        raise EvaluatorContractError(
            "Registry fingerprint does not match frozen V1."
        )

    computed_sha = _canonical_json_sha256(contract)

    if computed_sha != registry_sha:
        raise EvaluatorContractError(
            "Registry contract content does not match "
            "its canonical SHA256 fingerprint."
        )


def _as_2d_float_array(X: Any) -> np.ndarray:
    array = np.asarray(
        X,
        dtype=np.float64,
    )

    if array.ndim != 2:
        raise EvaluatorContractError(
            "X must be a two-dimensional feature matrix."
        )

    if array.shape[0] == 0 or array.shape[1] == 0:
        raise EvaluatorContractError(
            "X must be non-empty."
        )

    if not np.isfinite(array).all():
        raise EvaluatorContractError(
            "X contains non-finite values."
        )

    return array


def _as_class_vector(
    y: Any,
    n_rows: int,
) -> np.ndarray:
    array = np.asarray(y)

    if array.ndim != 1 or array.shape[0] != n_rows:
        raise EvaluatorContractError(
            "target_class must be a one-dimensional "
            "vector aligned to X."
        )

    if not np.isin(array, CLASS_ORDER).all():
        raise EvaluatorContractError(
            "target_class contains values outside {-1, 0, 1}."
        )

    return array.astype(
        np.int8,
        copy=False,
    )


def _as_tradeable_vector(
    y: Any,
    n_rows: int,
) -> np.ndarray:
    array = np.asarray(y)

    if array.ndim != 1 or array.shape[0] != n_rows:
        raise EvaluatorContractError(
            "target_tradeable must be a one-dimensional "
            "vector aligned to X."
        )

    if not np.isin(array, TRADEABLE_CLASS_ORDER).all():
        raise EvaluatorContractError(
            "target_tradeable contains values outside {0, 1}."
        )

    return array.astype(
        np.int8,
        copy=False,
    )


def validate_train_only_inputs(
    X: Any,
    target_class: Any,
    target_tradeable: Any,
    expected_feature_count: int = 331,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    X_array = _as_2d_float_array(X)

    if X_array.shape[1] != expected_feature_count:
        raise EvaluatorContractError(
            "Feature count mismatch: "
            f"expected={expected_feature_count}, "
            f"actual={X_array.shape[1]}."
        )

    y_class = _as_class_vector(
        target_class,
        X_array.shape[0],
    )

    y_tradeable = _as_tradeable_vector(
        target_tradeable,
        X_array.shape[0],
    )

    derived_tradeable = (
        y_class != 0
    ).astype(np.int8)

    if not np.array_equal(
        derived_tradeable,
        y_tradeable,
    ):
        raise EvaluatorContractError(
            "target_tradeable linkage does not match "
            "target_class != 0."
        )

    return (
        X_array,
        y_class,
        y_tradeable,
    )


def validate_fold_specs(
    folds: Sequence[FoldSpec],
    n_rows: int,
    required_fold_count: int = 4,
    required_purge_rows: int = 12,
) -> None:
    if len(folds) != required_fold_count:
        raise EvaluatorContractError(
            f"Expected {required_fold_count} folds, "
            f"received {len(folds)}."
        )

    seen_ids: set[str] = set()
    previous_validation_start = -1

    for fold in folds:
        fold.validate(n_rows)

        if fold.fold_id in seen_ids:
            raise EvaluatorContractError(
                f"Duplicate fold_id: {fold.fold_id}"
            )

        seen_ids.add(fold.fold_id)

        if fold.purge_rows != required_purge_rows:
            raise EvaluatorContractError(
                f"Fold {fold.fold_id} purge_rows must equal "
                f"frozen value {required_purge_rows}."
            )

        if fold.validation_start <= previous_validation_start:
            raise EvaluatorContractError(
                "Validation windows must progress chronologically."
            )

        previous_validation_start = fold.validation_start


def _require_classes(
    values: np.ndarray,
    required: Sequence[int],
    context: str,
) -> None:
    present = {
        int(value)
        for value in np.unique(values)
    }

    missing = [
        value
        for value in required
        if value not in present
    ]

    if missing:
        raise CandidateFoldFailure(
            f"Missing required classes in {context}: {missing}"
        )


def _inverse_frequency_sample_weight(
    y: np.ndarray,
) -> np.ndarray:
    classes, counts = np.unique(
        y,
        return_counts=True,
    )

    if classes.size < 2:
        raise CandidateFoldFailure(
            "Cannot compute class-balance weights "
            "with fewer than two classes."
        )

    total = float(y.shape[0])
    class_count = float(classes.size)

    weight_map = {
        int(label): (
            total
            / (
                class_count
                * float(count)
            )
        )
        for label, count in zip(
            classes,
            counts,
        )
    }

    return np.asarray(
        [
            weight_map[int(label)]
            for label in y
        ],
        dtype=np.float64,
    )


def _build_estimator(
    estimator_config: Mapping[str, Any],
):
    implementation = estimator_config.get("implementation")

    kwargs = {
        key: value
        for key, value in estimator_config.items()
        if key != "implementation"
    }

    if (
        implementation
        == "sklearn.linear_model.LogisticRegression"
    ):
        return LogisticRegression(**kwargs)

    if (
        implementation
        == "sklearn.ensemble.HistGradientBoostingClassifier"
    ):
        return HistGradientBoostingClassifier(**kwargs)

    if (
        implementation
        == "sklearn.ensemble.ExtraTreesClassifier"
    ):
        return ExtraTreesClassifier(**kwargs)

    raise CandidateFoldFailure(
        "Unsupported estimator implementation: "
        f"{implementation}"
    )


def _fit_estimator(
    estimator_config: Mapping[str, Any],
    preprocessing: Mapping[str, Any],
    X_train: np.ndarray,
    y_train: np.ndarray,
    fold_local_class_balance: str | None = None,
):
    scaler = None
    transformed_train = X_train

    if preprocessing.get("standard_scaler") is True:
        scaler = StandardScaler()

        transformed_train = scaler.fit_transform(
            X_train
        )

    elif preprocessing.get("standard_scaler") not in (
        False,
        None,
    ):
        raise CandidateFoldFailure(
            "Unsupported preprocessing.standard_scaler value."
        )

    estimator = _build_estimator(
        estimator_config
    )

    fit_kwargs: dict[str, Any] = {}

    if fold_local_class_balance is not None:
        if (
            fold_local_class_balance
            != "INVERSE_FREQUENCY_SAMPLE_WEIGHT"
        ):
            raise CandidateFoldFailure(
                "Unsupported fold_local_class_balance: "
                f"{fold_local_class_balance}"
            )

        fit_kwargs["sample_weight"] = (
            _inverse_frequency_sample_weight(
                y_train
            )
        )

    estimator.fit(
        transformed_train,
        y_train,
        **fit_kwargs,
    )

    return (
        estimator,
        scaler,
    )


def _transform_with_scaler(
    scaler: StandardScaler | None,
    X: np.ndarray,
) -> np.ndarray:
    if scaler is None:
        return X

    return scaler.transform(X)


def _predict_proba_reordered(
    estimator: Any,
    X: np.ndarray,
    class_order: Sequence[int],
) -> np.ndarray:
    raw = np.asarray(
        estimator.predict_proba(X),
        dtype=np.float64,
    )

    estimator_classes = tuple(
        int(value)
        for value in estimator.classes_
    )

    missing = [
        label
        for label in class_order
        if label not in estimator_classes
    ]

    if missing:
        raise CandidateFoldFailure(
            "Estimator probability output "
            f"is missing classes: {missing}"
        )

    columns = [
        estimator_classes.index(label)
        for label in class_order
    ]

    reordered = raw[:, columns]

    if not np.isfinite(reordered).all():
        raise CandidateFoldFailure(
            "Non-finite probabilities produced by estimator."
        )

    if (
        np.any(reordered < 0.0)
        or np.any(reordered > 1.0)
    ):
        raise CandidateFoldFailure(
            "Estimator produced probability outside [0, 1]."
        )

    return reordered


def fit_predict_candidate_fold(
    candidate: Mapping[str, Any],
    X_train: np.ndarray,
    y_class_train: np.ndarray,
    y_tradeable_train: np.ndarray,
    X_validation: np.ndarray,
) -> np.ndarray:
    architecture = candidate.get("architecture")

    if architecture == "FLAT_3CLASS":
        estimator, scaler = _fit_estimator(
            candidate["estimator"],
            candidate.get(
                "preprocessing",
                {},
            ),
            X_train,
            y_class_train,
            candidate.get(
                "fold_local_class_balance"
            ),
        )

        X_eval = _transform_with_scaler(
            scaler,
            X_validation,
        )

        probabilities = _predict_proba_reordered(
            estimator,
            X_eval,
            CLASS_ORDER,
        )

    elif (
        architecture
        == "HIERARCHICAL_TRADEABILITY_DIRECTION"
    ):
        stage_a = candidate["stage_a"]
        stage_b = candidate["stage_b"]

        (
            stage_a_estimator,
            stage_a_scaler,
        ) = _fit_estimator(
            stage_a["estimator"],
            stage_a.get(
                "preprocessing",
                {},
            ),
            X_train,
            y_tradeable_train,
            stage_a.get(
                "fold_local_class_balance"
            ),
        )

        X_stage_a_eval = _transform_with_scaler(
            stage_a_scaler,
            X_validation,
        )

        tradeability_proba = _predict_proba_reordered(
            stage_a_estimator,
            X_stage_a_eval,
            TRADEABLE_CLASS_ORDER,
        )

        p_tradeable = tradeability_proba[:, 1]

        stage_b_mask = y_tradeable_train == 1

        if not np.any(stage_b_mask):
            raise CandidateFoldFailure(
                "Stage B has no true tradeable TRAIN rows."
            )

        stage_b_y = y_class_train[
            stage_b_mask
        ]

        _require_classes(
            stage_b_y,
            DIRECTION_CLASS_ORDER,
            "Stage B fold TRAIN",
        )

        (
            stage_b_estimator,
            stage_b_scaler,
        ) = _fit_estimator(
            stage_b["estimator"],
            stage_b.get(
                "preprocessing",
                {},
            ),
            X_train[
                stage_b_mask
            ],
            stage_b_y,
            stage_b.get(
                "fold_local_class_balance"
            ),
        )

        X_stage_b_eval = _transform_with_scaler(
            stage_b_scaler,
            X_validation,
        )

        direction_proba = _predict_proba_reordered(
            stage_b_estimator,
            X_stage_b_eval,
            DIRECTION_CLASS_ORDER,
        )

        probabilities = np.column_stack(
            (
                p_tradeable
                * direction_proba[:, 0],
                1.0 - p_tradeable,
                p_tradeable
                * direction_proba[:, 1],
            )
        )

    else:
        raise CandidateFoldFailure(
            "Unsupported candidate architecture: "
            f"{architecture}"
        )

    row_sums = probabilities.sum(
        axis=1
    )

    if not np.isfinite(probabilities).all():
        raise CandidateFoldFailure(
            "Candidate produced non-finite "
            "combined probabilities."
        )

    if not np.allclose(
        row_sums,
        1.0,
        rtol=1e-9,
        atol=1e-9,
    ):
        raise CandidateFoldFailure(
            "Candidate probabilities do not sum to one."
        )

    return probabilities


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


def _multiclass_brier_score(
    y_true: np.ndarray,
    probabilities: np.ndarray,
) -> float:
    if (
        probabilities.ndim != 2
        or probabilities.shape[1] != len(CLASS_ORDER)
        or probabilities.shape[0] != y_true.shape[0]
    ):
        raise CandidateFoldFailure(
            "Invalid probability shape for multiclass Brier."
        )

    one_hot = np.zeros_like(
        probabilities,
        dtype=np.float64,
    )

    for column_index, label in enumerate(CLASS_ORDER):
        one_hot[:, column_index] = (
            y_true == label
        ).astype(np.float64)

    value = float(
        np.mean(
            np.sum(
                (
                    probabilities
                    - one_hot
                )
                ** 2,
                axis=1,
            )
        )
    )

    if not math.isfinite(value):
        raise CandidateFoldFailure(
            "Multiclass Brier score is non-finite."
        )

    return value


def compute_fold_metrics(
    y_true: np.ndarray,
    probabilities: np.ndarray,
) -> dict[str, float]:
    predictions = _argmax_predictions(
        probabilities
    )

    directional_f1 = float(
        f1_score(
            y_true,
            predictions,
            labels=list(
                DIRECTION_CLASS_ORDER
            ),
            average="macro",
            zero_division=0,
        )
    )

    precision_result = precision_recall_fscore_support(
        y_true,
        predictions,
        labels=list(CLASS_ORDER),
        average=None,
        zero_division=0,
    )

    precisions = np.asarray(
        precision_result[0],
        dtype=np.float64,
    )

    recalls = np.asarray(
        precision_result[1],
        dtype=np.float64,
    )

    f1_values = np.asarray(
        precision_result[2],
        dtype=np.float64,
    )

    expected_shape = (
        len(CLASS_ORDER),
    )

    if (
        precisions.shape != expected_shape
        or recalls.shape != expected_shape
        or f1_values.shape != expected_shape
    ):
        raise CandidateFoldFailure(
            "Per-class metric outputs must contain "
            "SHORT, NO_TRADE and LONG values."
        )

    metrics = {
        "balanced_accuracy_3class": float(
            balanced_accuracy_score(
                y_true,
                predictions,
            )
        ),
        "macro_f1_3class": float(
            f1_score(
                y_true,
                predictions,
                labels=list(CLASS_ORDER),
                average="macro",
                zero_division=0,
            )
        ),
        "directional_macro_f1_short_long": (
            directional_f1
        ),
        "short_precision": float(
            precisions[0]
        ),
        "short_recall": float(
            recalls[0]
        ),
        "short_f1": float(
            f1_values[0]
        ),
        "no_trade_precision": float(
            precisions[1]
        ),
        "no_trade_recall": float(
            recalls[1]
        ),
        "no_trade_f1": float(
            f1_values[1]
        ),
        "long_precision": float(
            precisions[2]
        ),
        "long_recall": float(
            recalls[2]
        ),
        "long_f1": float(
            f1_values[2]
        ),
        "log_loss_3class": float(
            log_loss(
                y_true,
                probabilities,
                labels=list(CLASS_ORDER),
            )
        ),
        "multiclass_brier": (
            _multiclass_brier_score(
                y_true,
                probabilities,
            )
        ),
        "predicted_trade_coverage": float(
            np.mean(
                predictions != 0
            )
        ),
    }

    if tuple(metrics.keys()) != REQUIRED_FOLD_METRICS:
        raise CandidateFoldFailure(
            "Fold metric contract does not match "
            "frozen required metric order."
        )

    if not all(
        math.isfinite(value)
        for value in metrics.values()
    ):
        raise CandidateFoldFailure(
            "One or more fold metrics are non-finite."
        )

    return metrics


def _fold_is_eligible(
    metrics: Mapping[str, float],
    gate: Mapping[str, Any],
) -> bool:
    if (
        gate.get(
            "all_reported_metrics_must_be_finite"
        )
        is True
    ):
        if not all(
            math.isfinite(
                float(value)
            )
            for value in metrics.values()
        ):
            return False

    if (
        gate.get(
            "directional_macro_f1_must_be_positive_every_fold"
        )
        is True
        and metrics[
            "directional_macro_f1_short_long"
        ]
        <= 0.0
    ):
        return False

    if (
        gate.get(
            "short_recall_must_be_positive_every_fold"
        )
        is True
        and metrics["short_recall"] <= 0.0
    ):
        return False

    if (
        gate.get(
            "long_recall_must_be_positive_every_fold"
        )
        is True
        and metrics["long_recall"] <= 0.0
    ):
        return False

    minimum = float(
        gate.get(
            "minimum_predicted_trade_coverage_each_fold",
            0.0,
        )
    )

    maximum = float(
        gate.get(
            "maximum_predicted_trade_coverage_each_fold",
            1.0,
        )
    )

    coverage = metrics[
        "predicted_trade_coverage"
    ]

    return minimum <= coverage <= maximum


def _aggregate_fold_metrics(
    fold_reports: Sequence[
        Mapping[str, Any]
    ],
) -> dict[str, float]:
    directional = np.asarray(
        [
            report["metrics"][
                "directional_macro_f1_short_long"
            ]
            for report in fold_reports
        ],
        dtype=np.float64,
    )

    balanced = np.asarray(
        [
            report["metrics"][
                "balanced_accuracy_3class"
            ]
            for report in fold_reports
        ],
        dtype=np.float64,
    )

    macro_f1 = np.asarray(
        [
            report["metrics"][
                "macro_f1_3class"
            ]
            for report in fold_reports
        ],
        dtype=np.float64,
    )

    losses = np.asarray(
        [
            report["metrics"][
                "log_loss_3class"
            ]
            for report in fold_reports
        ],
        dtype=np.float64,
    )

    brier = np.asarray(
        [
            report["metrics"][
                "multiclass_brier"
            ]
            for report in fold_reports
        ],
        dtype=np.float64,
    )

    coverages = np.asarray(
        [
            report["metrics"][
                "predicted_trade_coverage"
            ]
            for report in fold_reports
        ],
        dtype=np.float64,
    )

    short_recalls = np.asarray(
        [
            report["metrics"][
                "short_recall"
            ]
            for report in fold_reports
        ],
        dtype=np.float64,
    )

    long_recalls = np.asarray(
        [
            report["metrics"][
                "long_recall"
            ]
            for report in fold_reports
        ],
        dtype=np.float64,
    )

    return {
        "worst_fold_directional_macro_f1_short_long": float(
            np.min(directional)
        ),
        "mean_directional_macro_f1_short_long": float(
            np.mean(directional)
        ),
        "worst_fold_balanced_accuracy_3class": float(
            np.min(balanced)
        ),
        "mean_balanced_accuracy_3class": float(
            np.mean(balanced)
        ),
        "mean_macro_f1_3class": float(
            np.mean(macro_f1)
        ),
        "std_directional_macro_f1_short_long": float(
            np.std(
                directional,
                ddof=0,
            )
        ),
        "mean_log_loss_3class": float(
            np.mean(losses)
        ),
        "mean_multiclass_brier": float(
            np.mean(brier)
        ),
        "mean_predicted_trade_coverage": float(
            np.mean(coverages)
        ),
        "worst_fold_short_recall": float(
            np.min(short_recalls)
        ),
        "worst_fold_long_recall": float(
            np.min(long_recalls)
        ),
    }


def evaluate_candidate_train_only(
    candidate: Mapping[str, Any],
    X: np.ndarray,
    y_class: np.ndarray,
    y_tradeable: np.ndarray,
    folds: Sequence[FoldSpec],
    eligibility_gate: Mapping[str, Any],
) -> dict[str, Any]:
    fold_reports: list[
        dict[str, Any]
    ] = []

    try:
        for fold in folds:
            train_slice = fold.train_slice()
            validation_slice = fold.validation_slice()

            fold_y_train = y_class[
                train_slice
            ]

            fold_y_validation = y_class[
                validation_slice
            ]

            fold_tradeable_train = y_tradeable[
                train_slice
            ]

            _require_classes(
                fold_y_train,
                CLASS_ORDER,
                f"{fold.fold_id} fold TRAIN",
            )

            _require_classes(
                fold_y_validation,
                CLASS_ORDER,
                f"{fold.fold_id} fold validation",
            )

            _require_classes(
                fold_tradeable_train,
                TRADEABLE_CLASS_ORDER,
                (
                    f"{fold.fold_id} "
                    "tradeability fold TRAIN"
                ),
            )

            probabilities = fit_predict_candidate_fold(
                candidate,
                X[
                    train_slice
                ],
                fold_y_train,
                fold_tradeable_train,
                X[
                    validation_slice
                ],
            )

            metrics = compute_fold_metrics(
                fold_y_validation,
                probabilities,
            )

            fold_reports.append(
                {
                    "fold": fold.to_dict(),
                    "metrics": metrics,
                    "eligible": (
                        _fold_is_eligible(
                            metrics,
                            eligibility_gate,
                        )
                    ),
                }
            )

    except Exception as exc:
        return {
            "candidate_id": candidate.get(
                "candidate_id"
            ),
            "status": "FAILED_CLOSED",
            "eligible": False,
            "failure_type": type(exc).__name__,
            "failure_reason": str(exc),
            "fold_reports": fold_reports,
            "summary": None,
        }

    all_eligible = all(
        report["eligible"]
        for report in fold_reports
    )

    summary = _aggregate_fold_metrics(
        fold_reports
    )

    return {
        "candidate_id": candidate.get(
            "candidate_id"
        ),
        "status": (
            "ELIGIBLE"
            if all_eligible
            else "INELIGIBLE"
        ),
        "eligible": all_eligible,
        "failure_type": None,
        "failure_reason": None,
        "fold_reports": fold_reports,
        "summary": summary,
    }


def evaluate_dummy_baseline_train_only(
    X: np.ndarray,
    y_class: np.ndarray,
    folds: Sequence[FoldSpec],
) -> dict[str, Any]:
    fold_reports: list[
        dict[str, Any]
    ] = []

    for fold in folds:
        train_slice = fold.train_slice()
        validation_slice = fold.validation_slice()

        y_train = y_class[
            train_slice
        ]

        y_validation = y_class[
            validation_slice
        ]

        _require_classes(
            y_train,
            CLASS_ORDER,
            f"{fold.fold_id} dummy TRAIN",
        )

        _require_classes(
            y_validation,
            CLASS_ORDER,
            f"{fold.fold_id} dummy validation",
        )

        model = DummyClassifier(
            strategy="prior"
        )

        model.fit(
            X[
                train_slice
            ],
            y_train,
        )

        probabilities = _predict_proba_reordered(
            model,
            X[
                validation_slice
            ],
            CLASS_ORDER,
        )

        fold_reports.append(
            {
                "fold": fold.to_dict(),
                "metrics": compute_fold_metrics(
                    y_validation,
                    probabilities,
                ),
            }
        )

    return {
        "candidate_id": "DIAGNOSTIC_DUMMY_PRIOR",
        "selectable_as_winner": False,
        "fold_reports": fold_reports,
        "summary": _aggregate_fold_metrics(
            fold_reports
        ),
    }


def _selection_key(
    report: Mapping[str, Any],
    ranking: Sequence[
        Mapping[str, Any]
    ],
) -> tuple[float, ...]:
    summary = report.get("summary")

    if not isinstance(summary, Mapping):
        raise EvaluatorContractError(
            "Eligible candidate is missing summary metrics."
        )

    key: list[float] = []

    for rule in ranking:
        metric = rule["metric"]
        direction = rule["direction"]

        value = float(
            summary[metric]
        )

        if not math.isfinite(value):
            raise EvaluatorContractError(
                "Non-finite selection metric: "
                f"{metric}"
            )

        if direction == "MAXIMIZE":
            key.append(value)

        elif direction == "MINIMIZE":
            key.append(-value)

        else:
            raise EvaluatorContractError(
                "Unknown selection direction: "
                f"{direction}"
            )

    return tuple(key)


def select_winner(
    candidate_reports: Sequence[
        Mapping[str, Any]
    ],
    selection_policy: Mapping[str, Any],
) -> dict[str, Any]:
    eligible = [
        report
        for report in candidate_reports
        if report.get("eligible") is True
    ]

    if not eligible:
        return {
            "status": "NO_WINNER",
            "winner_candidate_id": None,
            "reason": (
                "NO_CANDIDATE_PASSED_"
                "FROZEN_ELIGIBILITY_GATE"
            ),
        }

    ranking = selection_policy.get(
        "ranking"
    )

    if (
        not isinstance(ranking, list)
        or not ranking
    ):
        raise EvaluatorContractError(
            "Selection policy ranking is missing."
        )

    priorities = [
        int(rule["priority"])
        for rule in ranking
    ]

    if priorities != list(
        range(
            1,
            len(ranking) + 1,
        )
    ):
        raise EvaluatorContractError(
            "Selection ranking priorities must "
            "be contiguous from 1."
        )

    winner = max(
        eligible,
        key=lambda report: _selection_key(
            report,
            ranking,
        ),
    )

    return {
        "status": "WINNER_SELECTED_TRAIN_INTERNAL_ONLY",
        "winner_candidate_id": winner[
            "candidate_id"
        ],
        "reason": (
            "FROZEN_LEXICOGRAPHIC_"
            "SELECTION_POLICY"
        ),
        "selection_key": list(
            _selection_key(
                winner,
                ranking,
            )
        ),
    }


def evaluate_registry_train_only(
    registry_payload: Mapping[str, Any],
    X: Any,
    target_class: Any,
    target_tradeable: Any,
    folds: Sequence[FoldSpec],
    include_dummy_baseline: bool = True,
) -> dict[str, Any]:
    validate_frozen_candidate_registry(
        registry_payload
    )

    contract = registry_payload[
        "contract"
    ]

    frozen_train = contract[
        "frozen_train_identity"
    ]

    fold_policy = contract[
        "fold_training_policy"
    ]

    (
        X_array,
        y_class,
        y_tradeable,
    ) = validate_train_only_inputs(
        X,
        target_class,
        target_tradeable,
        expected_feature_count=int(
            frozen_train[
                "feature_count"
            ]
        ),
    )

    validate_fold_specs(
        folds,
        n_rows=X_array.shape[0],
        required_fold_count=int(
            fold_policy[
                "walk_forward_fold_count"
            ]
        ),
        required_purge_rows=int(
            fold_policy[
                "purge_rows"
            ]
        ),
    )

    eligibility_gate = contract[
        "eligibility_gate"
    ]

    reports = [
        evaluate_candidate_train_only(
            candidate,
            X_array,
            y_class,
            y_tradeable,
            folds,
            eligibility_gate,
        )
        for candidate in contract[
            "candidates"
        ]
    ]

    selection = select_winner(
        reports,
        contract[
            "selection_policy"
        ],
    )

    baseline = None

    if include_dummy_baseline:
        baseline = (
            evaluate_dummy_baseline_train_only(
                X_array,
                y_class,
                folds,
            )
        )

    return {
        "analysis_version": (
            "XAUUSD_PORTABLE_331_"
            "TRAIN_MODEL_CANDIDATE_"
            "EVALUATOR_V1"
        ),
        "research_scope": (
            "TRAIN_INTERNAL_"
            "WALK_FORWARD_ONLY"
        ),
        "required_fold_metrics": list(
            REQUIRED_FOLD_METRICS
        ),
        "registry_fingerprint_sha256": (
            registry_payload[
                "registry_fingerprint"
            ][
                "sha256"
            ]
        ),
        "frozen_train_identity": dict(
            frozen_train
        ),
        "fold_count": len(folds),
        "folds": [
            fold.to_dict()
            for fold in folds
        ],
        "candidate_reports": reports,
        "diagnostic_baseline": baseline,
        "selection": selection,
        "scientific_policy": {
            "portable_validation_accessed": False,
            "portable_test_accessed": False,
            "threshold_search_performed": False,
            "probability_calibration_performed": False,
            "feature_selection_performed": False,
            "registry_changed": False,
            "model_artifacts_written": False,
            "live_authorized": False,
        },
    }