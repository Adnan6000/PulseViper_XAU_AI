from __future__ import annotations

import hashlib
import importlib
from pathlib import Path
from typing import Any, Mapping, cast

import joblib
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier


_registry: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_remediation_candidate_registry"
)


WINNER_CANDIDATE_ID = (
    "R03_FLAT_EXTRA_TREES_SMOOTH"
)

WINNER_CANDIDATE_FINGERPRINT_SHA256 = (
    "ae644c7272a015c26daeaaa7e655120bd7a3e4d267b2acd0d1f235e10bfa2e5f"
)

FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

PROBABILITY_CLASS_ORDER = (
    -1,
    0,
    1,
)

PREDICTION_RULE = (
    "ARGMAX_3CLASS_PROBABILITY"
)

ARTIFACT_SCHEMA_VERSION = (
    "R03_TRAIN_ONLY_FROZEN_ARTIFACT_V1"
)

PROBE_ROWS = 256

PARITY_RTOL = 1e-12

PARITY_ATOL = 1e-12


class R03ArtifactBuilderError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise R03ArtifactBuilderError(
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
        raise R03ArtifactBuilderError(
            reason
        )

    return value


def winner_candidate() -> Mapping[str, Any]:

    matches = [
        candidate
        for candidate
        in _registry.CANDIDATES
        if candidate.get(
            "candidate_id"
        )
        ==
        WINNER_CANDIDATE_ID
    ]

    require(
        len(
            matches
        )
        ==
        1,
        "WINNER_CANDIDATE_NOT_UNIQUE",
    )

    candidate = require_mapping(
        matches[0],
        "WINNER_CANDIDATE_INVALID",
    )

    fingerprint = (
        _registry.candidate_fingerprint_sha256(
            candidate
        )
    )

    require(
        fingerprint
        ==
        WINNER_CANDIDATE_FINGERPRINT_SHA256,
        "WINNER_CANDIDATE_FINGERPRINT_MISMATCH",
    )

    return candidate


def build_estimator(
    candidate: Mapping[str, Any],
) -> ExtraTreesClassifier:

    require(
        candidate.get(
            "architecture"
        )
        ==
        "FLAT_3CLASS",
        "UNEXPECTED_ARCHITECTURE",
    )

    require(
        candidate.get(
            "family"
        )
        ==
        "EXTRA_TREES",
        "UNEXPECTED_FAMILY",
    )

    preprocessing = require_mapping(
        candidate.get(
            "preprocessing"
        ),
        "PREPROCESSING_CONFIG_INVALID",
    )

    require(
        preprocessing.get(
            "standard_scaler"
        )
        is False,
        "STANDARD_SCALER_MUST_BE_DISABLED",
    )

    estimator_config = require_mapping(
        candidate.get(
            "estimator"
        ),
        "ESTIMATOR_CONFIG_INVALID",
    )

    require(
        estimator_config.get(
            "implementation"
        )
        ==
        "sklearn.ensemble.ExtraTreesClassifier",
        "ESTIMATOR_IMPLEMENTATION_MISMATCH",
    )

    expected: dict[str, Any] = {
        "bootstrap": False,
        "class_weight": "balanced",
        "max_depth": 8,
        "max_features": 0.50,
        "min_samples_leaf": 50,
        "n_estimators": 750,
        "n_jobs": -1,
        "random_state": 271828,
    }

    for key, expected_value in expected.items():

        require(
            estimator_config.get(
                key
            )
            ==
            expected_value,
            (
                "ESTIMATOR_PARAMETER_MISMATCH:"
                f"{key}"
            ),
        )

    constructor = cast(
        Any,
        ExtraTreesClassifier,
    )

    estimator_raw: Any = constructor(
        bootstrap=False,
        class_weight="balanced",
        max_depth=8,
        max_features=0.50,
        min_samples_leaf=50,
        n_estimators=750,
        n_jobs=-1,
        random_state=271828,
    )

    if not isinstance(
        estimator_raw,
        ExtraTreesClassifier,
    ):
        raise R03ArtifactBuilderError(
            "ESTIMATOR_CONSTRUCTION_TYPE_MISMATCH"
        )

    return estimator_raw


def reorder_probabilities(
    estimator: ExtraTreesClassifier,
    X: np.ndarray,
) -> np.ndarray:

    raw = np.asarray(
        estimator.predict_proba(
            X
        ),
        dtype=np.float64,
    )

    classes = tuple(
        int(
            value
        )
        for value
        in estimator.classes_
    )

    for label in PROBABILITY_CLASS_ORDER:

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
        in PROBABILITY_CLASS_ORDER
    ]

    probabilities = np.asarray(
        raw[
            :,
            columns,
        ],
        dtype=np.float64,
    )

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
        "PROBABILITY_SUM_MISMATCH",
    )

    return probabilities


def probability_sha256(
    probabilities: np.ndarray,
) -> str:

    normalized = np.ascontiguousarray(
        probabilities,
        dtype="<f8",
    )

    return hashlib.sha256(
        normalized.tobytes(
            order="C"
        )
    ).hexdigest()


def argmax_predictions(
    probabilities: np.ndarray,
) -> np.ndarray:

    order = np.asarray(
        PROBABILITY_CLASS_ORDER,
        dtype=np.int8,
    )

    return order[
        np.argmax(
            probabilities,
            axis=1,
        )
    ]


def build_artifact_bundle(
    *,
    train_batch: Any,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
]:

    candidate = (
        winner_candidate()
    )

    require(
        train_batch.row_count
        ==
        69966,
        "TRAIN_ROW_COUNT_MISMATCH",
    )

    require(
        train_batch.X.shape
        ==
        (
            69966,
            331,
        ),
        "TRAIN_MATRIX_SHAPE_MISMATCH",
    )

    require(
        train_batch.feature_columns_sha256
        ==
        FEATURE_COLUMNS_SHA256,
        "TRAIN_FEATURE_HASH_MISMATCH",
    )

    estimator = build_estimator(
        candidate
    )

    estimator.fit(
        train_batch.X,
        train_batch.target_class,
    )

    classes = tuple(
        int(
            value
        )
        for value
        in estimator.classes_
    )

    require(
        classes
        ==
        PROBABILITY_CLASS_ORDER,
        (
            "FITTED_CLASS_ORDER_MISMATCH:"
            f"{classes}"
        ),
    )

    probe_count = min(
        PROBE_ROWS,
        int(
            train_batch.row_count
        ),
    )

    probe_probabilities = (
        reorder_probabilities(
            estimator,
            train_batch.X[
                :probe_count
            ],
        )
    )

    bundle: dict[str, Any] = {
        "artifact_schema_version": (
            ARTIFACT_SCHEMA_VERSION
        ),
        "candidate_id": (
            WINNER_CANDIDATE_ID
        ),
        "candidate_fingerprint_sha256": (
            WINNER_CANDIDATE_FINGERPRINT_SHA256
        ),
        "dataset_id": (
            train_batch.dataset_id
        ),
        "dataset_sha256": (
            train_batch.dataset_sha256
        ),
        "manifest_sha256": (
            train_batch.manifest_sha256
        ),
        "feature_columns": tuple(
            train_batch.feature_columns
        ),
        "feature_columns_sha256": (
            train_batch.feature_columns_sha256
        ),
        "feature_count": 331,
        "train_rows": (
            train_batch.row_count
        ),
        "probability_class_order": (
            PROBABILITY_CLASS_ORDER
        ),
        "prediction_rule": (
            PREDICTION_RULE
        ),
        "preprocessing": {
            "standard_scaler": False,
        },
        "estimator_config": dict(
            require_mapping(
                candidate.get(
                    "estimator"
                ),
                "ESTIMATOR_CONFIG_INVALID",
            )
        ),
        "estimator": estimator,
    }

    runtime_metadata: dict[str, Any] = {
        "probe_rows": (
            probe_count
        ),
        "reference_probe_probabilities": (
            probe_probabilities
        ),
        "reference_probe_probability_sha256": (
            probability_sha256(
                probe_probabilities
            )
        ),
        "estimator_classes": list(
            classes
        ),
    }

    return (
        bundle,
        runtime_metadata,
    )


def save_bundle_create_only(
    *,
    bundle: Mapping[str, Any],
    artifact_path: Path,
) -> None:

    require(
        not artifact_path.exists(),
        "ARTIFACT_ALREADY_EXISTS",
    )

    artifact_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_path = artifact_path.with_suffix(
        artifact_path.suffix
        +
        ".tmp"
    )

    require(
        not temp_path.exists(),
        "ARTIFACT_TEMP_ALREADY_EXISTS",
    )

    try:

        joblib.dump(
            dict(
                bundle
            ),
            temp_path,
            compress=0,
            protocol=5,
        )

        require(
            temp_path.is_file(),
            "ARTIFACT_TEMP_NOT_CREATED",
        )

        temp_path.replace(
            artifact_path
        )

    finally:

        if temp_path.exists():

            temp_path.unlink()


def load_bundle(
    artifact_path: Path,
) -> Mapping[str, Any]:

    value: Any = joblib.load(
        artifact_path
    )

    return require_mapping(
        value,
        "LOADED_ARTIFACT_NOT_MAPPING",
    )


def verify_loaded_bundle(
    *,
    bundle: Mapping[str, Any],
    train_batch: Any,
    reference_probe_probabilities: np.ndarray,
) -> dict[str, Any]:

    require(
        bundle.get(
            "artifact_schema_version"
        )
        ==
        ARTIFACT_SCHEMA_VERSION,
        "LOADED_ARTIFACT_SCHEMA_MISMATCH",
    )

    require(
        bundle.get(
            "candidate_id"
        )
        ==
        WINNER_CANDIDATE_ID,
        "LOADED_CANDIDATE_ID_MISMATCH",
    )

    require(
        bundle.get(
            "candidate_fingerprint_sha256"
        )
        ==
        WINNER_CANDIDATE_FINGERPRINT_SHA256,
        "LOADED_CANDIDATE_FINGERPRINT_MISMATCH",
    )

    require(
        bundle.get(
            "feature_columns_sha256"
        )
        ==
        FEATURE_COLUMNS_SHA256,
        "LOADED_FEATURE_HASH_MISMATCH",
    )

    loaded_columns_raw: Any = bundle.get(
        "feature_columns"
    )

    if not isinstance(
        loaded_columns_raw,
        (
            list,
            tuple,
        ),
    ):
        raise R03ArtifactBuilderError(
            "LOADED_FEATURE_COLUMNS_INVALID"
        )

    loaded_columns = tuple(
        str(
            value
        )
        for value
        in loaded_columns_raw
    )

    require(
        loaded_columns
        ==
        tuple(
            train_batch.feature_columns
        ),
        "LOADED_FEATURE_ORDER_MISMATCH",
    )

    estimator_raw: Any = bundle.get(
        "estimator"
    )

    if not isinstance(
        estimator_raw,
        ExtraTreesClassifier,
    ):
        raise R03ArtifactBuilderError(
            "LOADED_ESTIMATOR_TYPE_MISMATCH"
        )

    estimator: ExtraTreesClassifier = (
        estimator_raw
    )

    probe_count = min(
        PROBE_ROWS,
        int(
            train_batch.row_count
        ),
    )

    loaded_probabilities = (
        reorder_probabilities(
            estimator,
            train_batch.X[
                :probe_count
            ],
        )
    )

    reference = np.asarray(
        reference_probe_probabilities,
        dtype=np.float64,
    )

    require(
        reference.shape
        ==
        loaded_probabilities.shape,
        "ARTIFACT_RELOAD_PROBABILITY_SHAPE_MISMATCH",
    )

    absolute_difference = np.abs(
        reference
        -
        loaded_probabilities
    )

    max_abs_difference = float(
        np.max(
            absolute_difference
        )
    )

    mean_abs_difference = float(
        np.mean(
            absolute_difference
        )
    )

    numeric_parity = bool(
        np.allclose(
            reference,
            loaded_probabilities,
            rtol=PARITY_RTOL,
            atol=PARITY_ATOL,
        )
    )

    require(
        numeric_parity,
        (
            "ARTIFACT_RELOAD_NUMERIC_PARITY_MISMATCH:"
            f"{max_abs_difference}"
        ),
    )

    reference_predictions = (
        argmax_predictions(
            reference
        )
    )

    loaded_predictions = (
        argmax_predictions(
            loaded_probabilities
        )
    )

    prediction_parity = bool(
        np.array_equal(
            reference_predictions,
            loaded_predictions,
        )
    )

    require(
        prediction_parity,
        "ARTIFACT_RELOAD_ARGMAX_PARITY_MISMATCH",
    )

    estimator_classes = [
        int(
            value
        )
        for value
        in estimator.classes_
    ]

    return {
        "status": "PASS",
        "probe_rows": (
            probe_count
        ),
        "reference_probe_probability_sha256": (
            probability_sha256(
                reference
            )
        ),
        "loaded_probe_probability_sha256": (
            probability_sha256(
                loaded_probabilities
            )
        ),
        "max_absolute_probability_difference": (
            max_abs_difference
        ),
        "mean_absolute_probability_difference": (
            mean_abs_difference
        ),
        "parity_rtol": (
            PARITY_RTOL
        ),
        "parity_atol": (
            PARITY_ATOL
        ),
        "numeric_probability_parity": True,
        "argmax_prediction_parity": True,
        "estimator_classes": (
            estimator_classes
        ),
    }