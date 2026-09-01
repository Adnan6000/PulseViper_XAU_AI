#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping, Sequence

import joblib
import numpy as np
import sklearn


ANALYSIS_VERSION = "XAUUSD_PORTABLE_331_C04_FULL_TRAIN_MODEL_FIT_V1"

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTING_DIR = REPO_ROOT / "04_Testing"

EVALUATOR_PATH = (
    TESTING_DIR
    / "evaluate_xauusd_portable_331_train_model_candidates.py"
)

INTEGRATION_RUNNER_PATH = (
    TESTING_DIR
    / "run_xauusd_portable_331_candidate_evaluator_integration.py"
)

WINNER_FREEZE_RUNNER_PATH = (
    TESTING_DIR
    / "freeze_xauusd_portable_331_train_internal_winner.py"
)

WINNER_FREEZE_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_train_internal_winner_freeze.json"
)

DEFAULT_MODEL_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_c04_full_train_model.joblib"
)

DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_c04_full_train_model_fit.json"
)

EXPECTED_WINNER_ID = (
    "C04_FLAT_EXTRA_TREES_CONSTRAINED"
)

EXPECTED_WINNER_CONFIG_SHA256 = (
    "f1b11c6f91561f2eba1bd56195e2239e9598b1906c88f11ada67eac6cdeb09e3"
)

EXPECTED_DATASET_ID = (
    "portable_cff75b0686383a3ab6f8352b"
)

EXPECTED_DATASET_SHA256 = (
    "cff75b0686383a3ab6f8352bfcdcd55308b99b7a4c6edbf7d2e7215f6f33dd07"
)

EXPECTED_MANIFEST_SHA256 = (
    "1b8e3599b227c9cbbc6b12f8ab0e275ca4deb4a65839fb626ca90720d59512dc"
)

EXPECTED_TRAIN_INPUT_SHA256 = (
    "9ffb72759499cfc202e88cfdbd61b42cee5b5c7cbb7db5870470453caa5ed2c5"
)

EXPECTED_TRAIN_TARGET_SHA256 = (
    "bc063a790e70cdbc931b2170ccfef883634b40ee7336a529a32bda0eaf0babe3"
)

EXPECTED_FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

EXPECTED_REGISTRY_SHA256 = (
    "b8088bb34ce8940f7de5946fbb9b0fd20f40d7cc93a76b76fd7975591f00066c"
)

EXPECTED_PROTOCOL_SHA256 = (
    "69e51e1b249b9da68cbf6f6778a8ae10f9f33f7082a07e5073a1ba731fa1640d"
)

EXPECTED_WALK_FORWARD_SHA256 = (
    "15516174ba6f3d8932425b20dcde33db25c040e0901c86af39796f97847ac7ed"
)

EXPECTED_ROWS = 69966
EXPECTED_FEATURES = 331
EXPECTED_CLASS_ORDER = (-1, 0, 1)

EXPECTED_ESTIMATOR = {
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
}


class FullTrainFitError(
    RuntimeError
):
    pass


def _canonical_sha256(
    value: Any,
) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        raw
    ).hexdigest()


def _sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as handle:
        for chunk in iter(
            lambda: handle.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(
                chunk
            )

    return digest.hexdigest()


def _read_json(
    path: Path,
) -> dict[str, Any]:
    raw = path.read_bytes()

    if raw.startswith(
        (
            b"\xff\xfe",
            b"\xfe\xff",
        )
    ):
        text = raw.decode(
            "utf-16"
        )

    elif raw.startswith(
        b"\xef\xbb\xbf"
    ):
        text = raw.decode(
            "utf-8-sig"
        )

    else:
        text = raw.decode(
            "utf-8"
        )

    payload = json.loads(
        text
    )

    if not isinstance(
        payload,
        dict,
    ):
        raise FullTrainFitError(
            f"Expected JSON object: {path}"
        )

    return payload


def _load_module(
    path: Path,
    name: str,
) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        name,
        path,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise FullTrainFitError(
            f"Cannot import module: {path}"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    sys.modules[
        name
    ] = module

    try:
        spec.loader.exec_module(
            module
        )

    except Exception:
        sys.modules.pop(
            name,
            None,
        )
        raise

    return module


def _mapping(
    value: Any,
    name: str,
) -> Mapping[str, Any]:
    if not isinstance(
        value,
        Mapping,
    ):
        raise FullTrainFitError(
            f"Expected mapping: {name}"
        )

    return value


def _load_and_validate_winner_freeze(
    freeze_module: ModuleType,
) -> tuple[
    dict[str, Any],
    Mapping[str, Any],
]:
    stored = _read_json(
        WINNER_FREEZE_PATH
    )

    rebuilt = (
        freeze_module
        .build_winner_freeze()
    )

    if stored != rebuilt:
        raise FullTrainFitError(
            "Stored winner-freeze evidence does not "
            "match a fresh reconstruction from the "
            "frozen evaluation."
        )

    if (
        stored.get(
            "valid"
        )
        is not True
    ):
        raise FullTrainFitError(
            "Winner-freeze evidence must be valid=true."
        )

    decision = _mapping(
        stored.get(
            "decision"
        ),
        "winner-freeze decision",
    )

    required_decision = {
        "status": (
            "TRAIN_INTERNAL_WINNER_FROZEN"
        ),
        "winner_candidate_id": (
            EXPECTED_WINNER_ID
        ),
        "winner_frozen_for_full_train_fit": True,
        "full_train_fit_authorized_next": True,
        "full_train_fit_performed": False,
        "validation_access_authorized": False,
        "test_access_authorized": False,
        "shadow_authorized": False,
        "live_authorized": False,
    }

    for (
        key,
        expected,
    ) in required_decision.items():
        if (
            decision.get(
                key
            )
            != expected
        ):
            raise FullTrainFitError(
                "Winner-freeze decision mismatch: "
                f"{key}"
            )

    identity = _mapping(
        stored.get(
            "artifact_identity"
        ),
        "winner-freeze identity",
    )

    expected_identity = {
        "dataset_id": (
            EXPECTED_DATASET_ID
        ),
        "dataset_sha256": (
            EXPECTED_DATASET_SHA256
        ),
        "manifest_sha256": (
            EXPECTED_MANIFEST_SHA256
        ),
        "train_input_fingerprint_sha256": (
            EXPECTED_TRAIN_INPUT_SHA256
        ),
        "train_target_fingerprint_sha256": (
            EXPECTED_TRAIN_TARGET_SHA256
        ),
        "candidate_registry_fingerprint_sha256": (
            EXPECTED_REGISTRY_SHA256
        ),
        "research_protocol_fingerprint_sha256": (
            EXPECTED_PROTOCOL_SHA256
        ),
        "walk_forward_evaluation_fingerprint_sha256": (
            EXPECTED_WALK_FORWARD_SHA256
        ),
    }

    for (
        key,
        expected,
    ) in expected_identity.items():
        if (
            identity.get(
                key
            )
            != expected
        ):
            raise FullTrainFitError(
                "Winner-freeze identity mismatch: "
                f"{key}"
            )

    winner = _mapping(
        stored.get(
            "winner"
        ),
        "winner",
    )

    if (
        winner.get(
            "candidate_id"
        )
        != EXPECTED_WINNER_ID
    ):
        raise FullTrainFitError(
            "Frozen winner ID mismatch."
        )

    if (
        winner.get(
            "eligible"
        )
        is not True
    ):
        raise FullTrainFitError(
            "Frozen winner must remain eligible."
        )

    config = _mapping(
        winner.get(
            "candidate_config"
        ),
        "winner candidate_config",
    )

    fingerprint = _mapping(
        winner.get(
            "candidate_config_fingerprint"
        ),
        "winner candidate_config_fingerprint",
    )

    if (
        fingerprint.get(
            "sha256"
        )
        != EXPECTED_WINNER_CONFIG_SHA256
    ):
        raise FullTrainFitError(
            "Winner config fingerprint mismatch."
        )

    if (
        _canonical_sha256(
            config
        )
        != EXPECTED_WINNER_CONFIG_SHA256
    ):
        raise FullTrainFitError(
            "Winner config content fingerprint mismatch."
        )

    if (
        config.get(
            "candidate_id"
        )
        != EXPECTED_WINNER_ID
    ):
        raise FullTrainFitError(
            "Winner config candidate ID mismatch."
        )

    if (
        config.get(
            "architecture"
        )
        != "FLAT_3CLASS"
    ):
        raise FullTrainFitError(
            "C04 architecture mismatch."
        )

    if (
        config.get(
            "family"
        )
        != "EXTRA_TREES"
    ):
        raise FullTrainFitError(
            "C04 family mismatch."
        )

    if (
        config.get(
            "probability_class_order"
        )
        != list(
            EXPECTED_CLASS_ORDER
        )
    ):
        raise FullTrainFitError(
            "C04 probability class order mismatch."
        )

    preprocessing = _mapping(
        config.get(
            "preprocessing"
        ),
        "preprocessing",
    )

    if (
        preprocessing.get(
            "standard_scaler"
        )
        is not False
    ):
        raise FullTrainFitError(
            "C04 must not use StandardScaler."
        )

    estimator = _mapping(
        config.get(
            "estimator"
        ),
        "estimator",
    )

    if (
        dict(
            estimator
        )
        != EXPECTED_ESTIMATOR
    ):
        raise FullTrainFitError(
            "C04 estimator configuration mismatch."
        )

    return (
        stored,
        config,
    )


def _validate_batch(
    batch: Any,
) -> None:
    expected = {
        "dataset_id": (
            EXPECTED_DATASET_ID
        ),
        "dataset_sha256": (
            EXPECTED_DATASET_SHA256
        ),
        "manifest_sha256": (
            EXPECTED_MANIFEST_SHA256
        ),
        "train_input_fingerprint_sha256": (
            EXPECTED_TRAIN_INPUT_SHA256
        ),
        "train_target_fingerprint_sha256": (
            EXPECTED_TRAIN_TARGET_SHA256
        ),
        "feature_columns_sha256": (
            EXPECTED_FEATURE_COLUMNS_SHA256
        ),
        "row_count": (
            EXPECTED_ROWS
        ),
    }

    for (
        key,
        expected_value,
    ) in expected.items():
        if (
            getattr(
                batch,
                key,
                None,
            )
            != expected_value
        ):
            raise FullTrainFitError(
                "TRAIN batch identity mismatch: "
                f"{key}"
            )

    if (
        len(
            batch.feature_columns
        )
        != EXPECTED_FEATURES
    ):
        raise FullTrainFitError(
            "TRAIN feature column count mismatch."
        )

    X = np.asarray(
        batch.X
    )

    y = np.asarray(
        batch.target_class
    )

    tradeable = np.asarray(
        batch.target_tradeable
    )

    decision_time = np.asarray(
        batch.decision_time
    )

    if (
        X.shape
        != (
            EXPECTED_ROWS,
            EXPECTED_FEATURES,
        )
    ):
        raise FullTrainFitError(
            "TRAIN X shape mismatch."
        )

    if (
        y.shape
        != (
            EXPECTED_ROWS,
        )
    ):
        raise FullTrainFitError(
            "target_class shape mismatch."
        )

    if (
        tradeable.shape
        != (
            EXPECTED_ROWS,
        )
    ):
        raise FullTrainFitError(
            "target_tradeable shape mismatch."
        )

    if (
        decision_time.shape
        != (
            EXPECTED_ROWS,
        )
    ):
        raise FullTrainFitError(
            "decision_time shape mismatch."
        )

    if not np.isfinite(
        X
    ).all():
        raise FullTrainFitError(
            "TRAIN X contains non-finite values."
        )

    if not np.isin(
        y,
        EXPECTED_CLASS_ORDER,
    ).all():
        raise FullTrainFitError(
            "target_class contains unexpected labels."
        )

    if not np.array_equal(
        (
            y
            != 0
        ).astype(
            np.int8
        ),
        tradeable.astype(
            np.int8,
            copy=False,
        ),
    ):
        raise FullTrainFitError(
            "target_tradeable linkage mismatch."
        )

    if not bool(
        np.all(
            decision_time[
                1:
            ]
            > decision_time[
                :-1
            ]
        )
    ):
        raise FullTrainFitError(
            "decision_time is not strictly increasing."
        )


def _build_model(
    evaluator: ModuleType,
    candidate_config: Mapping[str, Any],
) -> Any:
    estimator_config = _mapping(
        candidate_config.get(
            "estimator"
        ),
        "estimator",
    )

    builder = getattr(
        evaluator,
        "_build_estimator",
        None,
    )

    if builder is None:
        raise FullTrainFitError(
            "Evaluator estimator builder unavailable."
        )

    model = builder(
        estimator_config
    )

    if (
        model.__class__.__name__
        != "ExtraTreesClassifier"
    ):
        raise FullTrainFitError(
            "Frozen C04 did not build "
            "ExtraTreesClassifier."
        )

    params = model.get_params(
        deep=False
    )

    for (
        key,
        expected,
    ) in EXPECTED_ESTIMATOR.items():
        if (
            key
            == "implementation"
        ):
            continue

        if (
            params.get(
                key
            )
            != expected
        ):
            raise FullTrainFitError(
                "Built estimator parameter mismatch: "
                f"{key}"
            )

    return model


def _validate_model_structure(
    model: Any,
    X: np.ndarray,
) -> dict[str, Any]:
    classes = tuple(
        int(
            value
        )
        for value
        in np.asarray(
            model.classes_
        ).tolist()
    )

    if (
        classes
        != EXPECTED_CLASS_ORDER
    ):
        raise FullTrainFitError(
            "Fitted model class order mismatch."
        )

    if (
        int(
            model.n_features_in_
        )
        != EXPECTED_FEATURES
    ):
        raise FullTrainFitError(
            "Fitted model feature count mismatch."
        )

    trees = getattr(
        model,
        "estimators_",
        None,
    )

    if (
        not isinstance(
            trees,
            list,
        )
        or len(
            trees
        )
        != EXPECTED_ESTIMATOR[
            "n_estimators"
        ]
    ):
        raise FullTrainFitError(
            "Fitted model tree count mismatch."
        )

    row_count = min(
        64,
        X.shape[
            0
        ],
    )

    sanity_X = np.concatenate(
        (
            X[
                :row_count
            ],
            X[
                -row_count:
            ],
        ),
        axis=0,
    )

    probabilities = np.asarray(
        model.predict_proba(
            sanity_X
        ),
        dtype=np.float64,
    )

    if (
        probabilities.shape
        != (
            sanity_X.shape[
                0
            ],
            3,
        )
    ):
        raise FullTrainFitError(
            "predict_proba shape mismatch."
        )

    if not np.isfinite(
        probabilities
    ).all():
        raise FullTrainFitError(
            "predict_proba contains non-finite values."
        )

    if (
        np.any(
            probabilities
            < 0.0
        )
        or np.any(
            probabilities
            > 1.0
        )
    ):
        raise FullTrainFitError(
            "predict_proba outside [0,1]."
        )

    if not np.allclose(
        probabilities.sum(
            axis=1
        ),
        1.0,
        rtol=1e-9,
        atol=1e-9,
    ):
        raise FullTrainFitError(
            "predict_proba rows do not sum to one."
        )

    return {
        "class_order": list(
            classes
        ),
        "n_features_in": int(
            model.n_features_in_
        ),
        "tree_count": len(
            trees
        ),
        "structural_probability_sanity_rows": int(
            sanity_X.shape[
                0
            ]
        ),
        "structural_probability_shape": [
            int(
                value
            )
            for value
            in probabilities.shape
        ],
        "structural_probability_rows_sum_to_one": True,
        "structural_probability_values_finite": True,
    }


def _warning_records(
    records: Sequence[Any],
) -> list[dict[str, Any]]:
    return [
        {
            "category": (
                record.category.__name__
            ),
            "message": str(
                record.message
            ),
            "filename": str(
                record.filename
            ),
            "lineno": int(
                record.lineno
            ),
        }
        for record
        in records
    ]


def _dump_joblib_atomic(
    model: Any,
    path: Path,
) -> str:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(
        path.suffix
        + ".tmp"
    )

    temporary_path.unlink(
        missing_ok=True
    )

    joblib.dump(
        model,
        temporary_path,
        compress=3,
        protocol=5,
    )

    try:
        joblib.load(
            temporary_path
        )

    except Exception as exc:
        temporary_path.unlink(
            missing_ok=True
        )

        raise FullTrainFitError(
            "Staged joblib artifact cannot be reloaded."
        ) from exc

    staged_sha = _sha256_file(
        temporary_path
    )

    if path.exists():
        existing_sha = _sha256_file(
            path
        )

        temporary_path.unlink(
            missing_ok=True
        )

        if (
            existing_sha
            != staged_sha
        ):
            raise FullTrainFitError(
                "Immutable model path already exists "
                "with a different SHA256."
            )

        return existing_sha

    temporary_path.replace(
        path
    )

    final_sha = _sha256_file(
        path
    )

    if (
        final_sha
        != staged_sha
    ):
        raise FullTrainFitError(
            "Final model SHA256 differs "
            "from staged SHA256."
        )

    return final_sha


def _write_json_atomic(
    path: Path,
    payload: Mapping[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(
        path.suffix
        + ".tmp"
    )

    temporary_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary_path.replace(
        path
    )


def build_full_train_fit(
    canonical_root: str | Path = REPO_ROOT,
    model_path: Path = DEFAULT_MODEL_PATH,
) -> dict[str, Any]:
    evaluator = _load_module(
        EVALUATOR_PATH,
        "xauusd_candidate_evaluator_for_c04_full_fit",
    )

    integration = _load_module(
        INTEGRATION_RUNNER_PATH,
        "xauusd_candidate_integration_for_c04_full_fit",
    )

    freeze_module = _load_module(
        WINNER_FREEZE_RUNNER_PATH,
        "xauusd_winner_freeze_for_c04_full_fit",
    )

    (
        freeze_payload,
        candidate_config,
    ) = _load_and_validate_winner_freeze(
        freeze_module
    )

    registry = (
        evaluator
        .load_frozen_candidate_registry(
            freeze_module.REGISTRY_PATH
        )
    )

    if (
        registry[
            "registry_fingerprint"
        ][
            "sha256"
        ]
        != EXPECTED_REGISTRY_SHA256
    ):
        raise FullTrainFitError(
            "Registry fingerprint mismatch."
        )

    loader_module = (
        integration
        ._load_loader_module()
    )

    loader_class = getattr(
        loader_module,
        "Portable331TrainingInputLoader",
        None,
    )

    if loader_class is None:
        raise FullTrainFitError(
            "Portable331TrainingInputLoader unavailable."
        )

    batch = (
        loader_class(
            canonical_root
        )
        .load_train_supervised()
    )

    integration._validate_supervised_batch(
        batch,
        registry,
    )

    _validate_batch(
        batch
    )

    (
        X,
        y_class,
        y_tradeable,
    ) = evaluator.validate_train_only_inputs(
        batch.X,
        batch.target_class,
        batch.target_tradeable,
        expected_feature_count=(
            EXPECTED_FEATURES
        ),
    )

    if (
        y_tradeable.shape
        != (
            EXPECTED_ROWS,
        )
    ):
        raise FullTrainFitError(
            "Validated target_tradeable shape mismatch."
        )

    model = _build_model(
        evaluator,
        candidate_config,
    )

    started_utc = datetime.now(
        timezone.utc
    ).isoformat()

    with warnings.catch_warnings(
        record=True
    ) as caught:
        warnings.simplefilter(
            "always"
        )

        model.fit(
            X,
            y_class,
        )

    completed_utc = datetime.now(
        timezone.utc
    ).isoformat()

    structure_before_save = (
        _validate_model_structure(
            model,
            X,
        )
    )

    model_sha256 = (
        _dump_joblib_atomic(
            model,
            model_path,
        )
    )

    reloaded_model = joblib.load(
        model_path
    )

    structure_after_reload = (
        _validate_model_structure(
            reloaded_model,
            X,
        )
    )

    if (
        structure_before_save
        != structure_after_reload
    ):
        raise FullTrainFitError(
            "Reloaded model structure differs "
            "from fitted model."
        )

    model_record = {
        "candidate_id": (
            EXPECTED_WINNER_ID
        ),
        "candidate_config_fingerprint_sha256": (
            EXPECTED_WINNER_CONFIG_SHA256
        ),
        "model_artifact_filename": (
            model_path.name
        ),
        "model_artifact_sha256": (
            model_sha256
        ),
        "serialization": "joblib",
        "dataset_id": (
            EXPECTED_DATASET_ID
        ),
        "dataset_sha256": (
            EXPECTED_DATASET_SHA256
        ),
        "manifest_sha256": (
            EXPECTED_MANIFEST_SHA256
        ),
        "train_input_fingerprint_sha256": (
            EXPECTED_TRAIN_INPUT_SHA256
        ),
        "train_target_fingerprint_sha256": (
            EXPECTED_TRAIN_TARGET_SHA256
        ),
        "feature_columns_sha256": (
            EXPECTED_FEATURE_COLUMNS_SHA256
        ),
        "train_rows": (
            EXPECTED_ROWS
        ),
        "feature_count": (
            EXPECTED_FEATURES
        ),
        "probability_class_order": list(
            EXPECTED_CLASS_ORDER
        ),
    }

    return {
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "valid": True,
        "research_scope": (
            "FIT_EXACT_FROZEN_C04_ON_FULL_"
            "69966_ROW_TRAIN_ONLY_AND_FREEZE_"
            "MODEL_ARTIFACT_WITHOUT_HOLDOUT_ACCESS"
        ),
        "runtime": {
            "started_utc": (
                started_utc
            ),
            "completed_utc": (
                completed_utc
            ),
            "python_version": (
                platform.python_version()
            ),
            "numpy_version": (
                np.__version__
            ),
            "sklearn_version": (
                sklearn.__version__
            ),
            "joblib_version": (
                joblib.__version__
            ),
            "platform": (
                platform.platform()
            ),
        },
        "artifact_identity": {
            "dataset_id": (
                EXPECTED_DATASET_ID
            ),
            "dataset_sha256": (
                EXPECTED_DATASET_SHA256
            ),
            "manifest_sha256": (
                EXPECTED_MANIFEST_SHA256
            ),
            "train_input_fingerprint_sha256": (
                EXPECTED_TRAIN_INPUT_SHA256
            ),
            "train_target_fingerprint_sha256": (
                EXPECTED_TRAIN_TARGET_SHA256
            ),
            "feature_columns_sha256": (
                EXPECTED_FEATURE_COLUMNS_SHA256
            ),
            "candidate_registry_fingerprint_sha256": (
                EXPECTED_REGISTRY_SHA256
            ),
            "research_protocol_fingerprint_sha256": (
                EXPECTED_PROTOCOL_SHA256
            ),
            "walk_forward_evaluation_fingerprint_sha256": (
                EXPECTED_WALK_FORWARD_SHA256
            ),
            "winner_config_fingerprint_sha256": (
                EXPECTED_WINNER_CONFIG_SHA256
            ),
            "winner_freeze_canonical_sha256": (
                _canonical_sha256(
                    freeze_payload
                )
            ),
        },
        "model_record": (
            model_record
        ),
        "model_record_fingerprint": {
            "canonicalization": (
                "JSON_SORT_KEYS_COMPACT_UTF8_SHA256"
            ),
            "sha256": (
                _canonical_sha256(
                    model_record
                )
            ),
        },
        "fit": {
            "candidate_id": (
                EXPECTED_WINNER_ID
            ),
            "candidate_config": dict(
                candidate_config
            ),
            "fit_rows": (
                EXPECTED_ROWS
            ),
            "fit_feature_count": (
                EXPECTED_FEATURES
            ),
            "fit_target": (
                "target_class"
            ),
            "scaler_fit_performed": False,
            "sample_weight_supplied": False,
            "training_metrics_computed": False,
            "structural_validation": (
                structure_before_save
            ),
            "artifact_reload_validation": (
                structure_after_reload
            ),
        },
        "warnings": (
            _warning_records(
                caught
            )
        ),
        "decision": {
            "status": (
                "FROZEN_C04_FULL_TRAIN_MODEL_"
                "ARTIFACT_CREATED"
            ),
            "full_train_fit_completed": True,
            "model_artifact_frozen": True,
            "winner_candidate_id": (
                EXPECTED_WINNER_ID
            ),
            "validation_accessed_in_this_gate": False,
            "validation_access_authorized_next": True,
            "test_accessed_in_this_gate": False,
            "test_access_authorized": False,
            "shadow_authorized": False,
            "live_authorized": False,
            "next_action": (
                "RUN_ONE_TIME_UNTOUCHED_PORTABLE_"
                "VALIDATION_USING_ONLY_THE_FROZEN_"
                "MODEL_ARTIFACT_WITHOUT_REFIT_OR_TUNING"
            ),
        },
        "scientific_policy": {
            "model_fit_performed_in_this_gate": True,
            "fit_scope": (
                "FULL_FROZEN_TRAIN_ONLY"
            ),
            "candidate_registry_changed": False,
            "candidate_added_after_results": False,
            "hyperparameters_changed_after_results": False,
            "winner_changed_after_freeze": False,
            "scaler_fit_performed": False,
            "threshold_search_performed": False,
            "probability_calibration_performed": False,
            "feature_selection_performed": False,
            "training_metrics_computed": False,
            "portable_validation_feature_values_loaded": False,
            "portable_validation_target_values_loaded": False,
            "portable_test_feature_values_loaded": False,
            "portable_test_target_values_loaded": False,
            "execution_integration_modified": False,
            "risk_engine_modified": False,
            "orders_sent": False,
            "shadow_authorized": False,
            "live_authorized": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--execute-full-train-fit",
        action="store_true",
    )

    parser.add_argument(
        "--canonical-root",
        type=Path,
        default=REPO_ROOT,
    )

    parser.add_argument(
        "--model-output",
        type=Path,
        default=DEFAULT_MODEL_PATH,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )

    args = parser.parse_args()

    if not args.execute_full_train_fit:
        print(
            json.dumps(
                {
                    "analysis_version": (
                        ANALYSIS_VERSION
                    ),
                    "valid": False,
                    "reason": (
                        "EXPLICIT_FULL_TRAIN_FIT_"
                        "FLAG_REQUIRED"
                    ),
                    "model_fit_performed": False,
                    "validation_accessed": False,
                    "test_accessed": False,
                    "live_authorized": False,
                },
                indent=2,
                sort_keys=True,
            )
        )

        return 2

    try:
        report = build_full_train_fit(
            args.canonical_root,
            args.model_output,
        )

        _write_json_atomic(
            args.output,
            report,
        )

    except Exception as exc:
        failure = {
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "valid": False,
            "reason": (
                "XAUUSD_PORTABLE_331_C04_"
                "FULL_TRAIN_MODEL_FIT_FAILED"
            ),
            "error_type": (
                type(
                    exc
                ).__name__
            ),
            "error": str(
                exc
            ),
            "scientific_policy": {
                "validation_access_authorized": False,
                "test_access_authorized": False,
                "shadow_authorized": False,
                "live_authorized": False,
            },
        }

        _write_json_atomic(
            args.output,
            failure,
        )

        print(
            json.dumps(
                failure,
                indent=2,
                sort_keys=True,
            )
        )

        return 1

    print(
        json.dumps(
            {
                "analysis_version": (
                    report[
                        "analysis_version"
                    ]
                ),
                "valid": True,
                "model_artifact": (
                    report[
                        "model_record"
                    ][
                        "model_artifact_filename"
                    ]
                ),
                "model_artifact_sha256": (
                    report[
                        "model_record"
                    ][
                        "model_artifact_sha256"
                    ]
                ),
                "model_record_fingerprint_sha256": (
                    report[
                        "model_record_fingerprint"
                    ][
                        "sha256"
                    ]
                ),
                "warnings": (
                    report[
                        "warnings"
                    ]
                ),
                "decision": (
                    report[
                        "decision"
                    ]
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )