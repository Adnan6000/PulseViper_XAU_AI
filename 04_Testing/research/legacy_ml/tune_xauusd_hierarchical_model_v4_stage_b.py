from __future__ import annotations

import hashlib
import importlib
import json
import math
import sys

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler


# =============================================================================
# Repository bootstrap
# =============================================================================

ROOT_DIR = (
    Path(__file__)
    .resolve()
    .parents[3]
)

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


# =============================================================================
# Project modules
# =============================================================================

trainer_module: Any = importlib.import_module(
    "02_AI.Models.xauusd_hierarchical_model_v4_trainer"
)

XAUUSDHierarchicalModelV4Trainer: Any = (
    trainer_module.XAUUSDHierarchicalModelV4Trainer
)

TrainingSnapshot: Any = (
    trainer_module.TrainingSnapshot
)

STAGE_A_CLASS_IDS = (
    trainer_module.STAGE_A_CLASS_IDS
)

STAGE_A_CLASS_NAMES = (
    trainer_module.STAGE_A_CLASS_NAMES
)

STAGE_B_CLASS_IDS = (
    trainer_module.STAGE_B_CLASS_IDS
)

STAGE_B_CLASS_NAMES = (
    trainer_module.STAGE_B_CLASS_NAMES
)

STAGE_A_METRICS_KEY = (
    trainer_module.STAGE_A_METRICS_KEY
)

STAGE_B_METRICS_KEY = (
    trainer_module.STAGE_B_METRICS_KEY
)

COMBINED_METRICS_KEY = (
    trainer_module.COMBINED_METRICS_KEY
)


# =============================================================================
# Frozen scientific gate
# =============================================================================

SWEEP_VERSION = (
    "XAUUSD_V4_STAGE_B_VALIDATION_SWEEP_V2"
)

TRAINING_CONTRACT_VERSION = (
    "XAUUSD_MTF_TRAINING_V3"
)

EXPECTED_DATASET_ID = (
    "train_66ff363d25d8143d4e2c3410"
)

EXPECTED_DATASET_SHA256 = (
    "66ff363d25d8143d4e2c3410964ad26b"
    "5bd72f2e98806c3e0997ce420d18413d"
)

EXPECTED_TRAINING_MANIFEST_SHA256 = (
    "a205403a6cb5a2d1b17159a2296d1f4"
    "afb01ea5b9b90b2710feafa7dd9476aa3"
)

EXPECTED_FEATURE_COUNT = 333

EXPECTED_TRAIN_ROWS = 69_966
EXPECTED_VALIDATION_ROWS = 14_983

EXPECTED_TRAIN_TRADEABLE_ROWS = 35_896
EXPECTED_VALIDATION_TRADEABLE_ROWS = 7_691

RANDOM_STATE = 42

STAGE_A_CLASS_BALANCE_POWER = 0.20
STAGE_B_CLASS_BALANCE_POWER = 0.20


# =============================================================================
# Fixed Stage A baseline
# =============================================================================

STAGE_A_PARAMETERS = {
    "max_iter": 300,
    "learning_rate": 0.04,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 50,
    "l2_regularization": 1.5,
}


# =============================================================================
# Stage B candidates
# =============================================================================

@dataclass(frozen=True)
class StageBCandidate:
    name: str
    max_iter: int
    learning_rate: float
    max_leaf_nodes: int
    min_samples_leaf: int
    l2_regularization: float

    def parameter_document(
        self,
    ) -> dict[str, Any]:
        return {
            "max_iter": int(
                self.max_iter
            ),
            "learning_rate": float(
                self.learning_rate
            ),
            "max_leaf_nodes": int(
                self.max_leaf_nodes
            ),
            "min_samples_leaf": int(
                self.min_samples_leaf
            ),
            "l2_regularization": float(
                self.l2_regularization
            ),
        }

    def model_parameters(
        self,
    ) -> dict[str, Any]:
        return {
            **self.parameter_document(),
            "early_stopping": False,
            "random_state": (
                RANDOM_STATE + 1
            ),
        }


CANDIDATES: tuple[
    StageBCandidate,
    ...,
] = (
    StageBCandidate(
        name="baseline_v4",
        max_iter=300,
        learning_rate=0.04,
        max_leaf_nodes=31,
        min_samples_leaf=50,
        l2_regularization=1.5,
    ),
    StageBCandidate(
        name="reg_180_15_100",
        max_iter=180,
        learning_rate=0.03,
        max_leaf_nodes=15,
        min_samples_leaf=100,
        l2_regularization=3.0,
    ),
    StageBCandidate(
        name="reg_140_15_150",
        max_iter=140,
        learning_rate=0.025,
        max_leaf_nodes=15,
        min_samples_leaf=150,
        l2_regularization=5.0,
    ),
    StageBCandidate(
        name="reg_120_15_200",
        max_iter=120,
        learning_rate=0.02,
        max_leaf_nodes=15,
        min_samples_leaf=200,
        l2_regularization=7.5,
    ),
    StageBCandidate(
        name="reg_140_7_150",
        max_iter=140,
        learning_rate=0.02,
        max_leaf_nodes=7,
        min_samples_leaf=150,
        l2_regularization=5.0,
    ),
    StageBCandidate(
        name="reg_120_7_250",
        max_iter=120,
        learning_rate=0.015,
        max_leaf_nodes=7,
        min_samples_leaf=250,
        l2_regularization=10.0,
    ),
    StageBCandidate(
        name="reg_80_7_300",
        max_iter=80,
        learning_rate=0.025,
        max_leaf_nodes=7,
        min_samples_leaf=300,
        l2_regularization=12.5,
    ),
    StageBCandidate(
        name="reg_100_7_400",
        max_iter=100,
        learning_rate=0.02,
        max_leaf_nodes=7,
        min_samples_leaf=400,
        l2_regularization=15.0,
    ),
)


# =============================================================================
# Generic validation helpers
# =============================================================================

def _sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as handle:
        while True:
            chunk = handle.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


def _require_equal(
    *,
    actual: Any,
    expected: Any,
    reason: str,
) -> None:
    if actual != expected:
        raise RuntimeError(
            (
                f"{reason}: "
                f"actual={actual!r}, "
                f"expected={expected!r}"
            )
        )


def _require_finite_array(
    *,
    name: str,
    values: np.ndarray,
) -> None:
    if not np.isfinite(
        values
    ).all():
        raise RuntimeError(
            (
                "NONFINITE_SWEEP_MATRIX: "
                f"{name}"
            )
        )


def _require_finite_number(
    *,
    name: str,
    value: Any,
) -> float:
    result = float(
        value
    )

    if not math.isfinite(
        result
    ):
        raise RuntimeError(
            (
                "NONFINITE_SWEEP_METRIC: "
                f"{name}"
            )
        )

    return result


def _class_metrics(
    *,
    metrics: dict[str, Any],
    class_name: str,
) -> dict[str, Any]:
    values = (
        metrics[
            "per_class"
        ][
            class_name
        ]
    )

    return {
        "precision": _require_finite_number(
            name=(
                f"{class_name}_precision"
            ),
            value=(
                values[
                    "precision"
                ]
            ),
        ),
        "recall": _require_finite_number(
            name=(
                f"{class_name}_recall"
            ),
            value=(
                values[
                    "recall"
                ]
            ),
        ),
        "f1": _require_finite_number(
            name=(
                f"{class_name}_f1"
            ),
            value=(
                values[
                    "f1"
                ]
            ),
        ),
        "support": int(
            values[
                "support"
            ]
        ),
    }


# =============================================================================
# Frozen immutable training snapshot discovery
# =============================================================================

def _discover_frozen_training_snapshot(
    *,
    trainer: Any,
) -> Any:
    learning_root = (
        trainer.canonical_root
        / "Instruments"
        / "XAUUSD"
        / "learning"
    )

    if not learning_root.is_dir():
        raise RuntimeError(
            (
                "XAUUSD_LEARNING_ROOT_MISSING: "
                f"{learning_root}"
            )
        )

    matches: list[
        tuple[
            Path,
            dict[str, Any],
        ]
    ] = []

    for manifest_path in sorted(
        learning_root.rglob(
            "*.manifest.json"
        )
    ):
        if (
            _sha256_file(
                manifest_path
            )
            !=
            EXPECTED_TRAINING_MANIFEST_SHA256
        ):
            continue

        try:
            manifest = json.loads(
                manifest_path.read_text(
                    encoding="utf-8"
                )
            )
        except Exception as exc:
            raise RuntimeError(
                (
                    "INVALID_FROZEN_TRAINING_MANIFEST: "
                    f"{manifest_path}"
                )
            ) from exc

        if not isinstance(
            manifest,
            dict,
        ):
            raise RuntimeError(
                (
                    "INVALID_FROZEN_TRAINING_MANIFEST: "
                    f"{manifest_path}"
                )
            )

        if (
            str(
                manifest.get(
                    "training_contract_version",
                    "",
                )
            )
            !=
            TRAINING_CONTRACT_VERSION
        ):
            continue

        if (
            str(
                manifest.get(
                    "dataset_id",
                    "",
                )
            )
            !=
            EXPECTED_DATASET_ID
        ):
            continue

        matches.append(
            (
                manifest_path,
                manifest,
            )
        )

    if not matches:
        raise RuntimeError(
            (
                "FROZEN_V3_TRAINING_MANIFEST_NOT_FOUND: "
                f"dataset_id={EXPECTED_DATASET_ID}, "
                f"manifest_sha256="
                f"{EXPECTED_TRAINING_MANIFEST_SHA256}"
            )
        )

    if len(
        matches
    ) != 1:
        raise RuntimeError(
            (
                "FROZEN_V3_TRAINING_MANIFEST_AMBIGUOUS: "
                f"matches={len(matches)}"
            )
        )

    (
        manifest_path,
        manifest,
    ) = matches[0]

    if bool(
        manifest.get(
            "live_authorized",
            False,
        )
    ):
        raise RuntimeError(
            "LIVE_AUTHORIZED_FROZEN_TRAINING_MANIFEST_REJECTED"
        )

    _require_equal(
        actual=str(
            manifest.get(
                "dataset_id",
                "",
            )
        ),
        expected=(
            EXPECTED_DATASET_ID
        ),
        reason=(
            "SWEEP_DATASET_ID_MISMATCH"
        ),
    )

    _require_equal(
        actual=str(
            manifest.get(
                "dataset_sha256",
                "",
            )
        ),
        expected=(
            EXPECTED_DATASET_SHA256
        ),
        reason=(
            "SWEEP_DATASET_SHA256_MANIFEST_MISMATCH"
        ),
    )

    dataset_filename = str(
        manifest.get(
            "dataset_filename",
            "",
        )
    ).strip()

    if not dataset_filename:
        raise RuntimeError(
            "FROZEN_TRAINING_DATASET_FILENAME_MISSING"
        )

    dataset_path = (
        manifest_path.parent
        / dataset_filename
    )

    if not dataset_path.is_file():
        raise RuntimeError(
            (
                "FROZEN_TRAINING_DATASET_MISSING: "
                f"{dataset_path}"
            )
        )

    actual_dataset_sha256 = (
        _sha256_file(
            dataset_path
        )
    )

    _require_equal(
        actual=(
            actual_dataset_sha256
        ),
        expected=(
            EXPECTED_DATASET_SHA256
        ),
        reason=(
            "SWEEP_DATASET_FILE_SHA256_MISMATCH"
        ),
    )

    feature_columns_raw = (
        manifest.get(
            "feature_columns",
            [],
        )
    )

    if not isinstance(
        feature_columns_raw,
        list,
    ):
        raise RuntimeError(
            "FROZEN_FEATURE_COLUMNS_INVALID"
        )

    feature_columns = tuple(
        str(
            value
        )
        for value
        in feature_columns_raw
    )

    _require_equal(
        actual=len(
            feature_columns
        ),
        expected=(
            EXPECTED_FEATURE_COUNT
        ),
        reason=(
            "SWEEP_FEATURE_COUNT_MISMATCH"
        ),
    )

    if len(
        set(
            feature_columns
        )
    ) != len(
        feature_columns
    ):
        raise RuntimeError(
            "FROZEN_FEATURE_COLUMNS_NOT_UNIQUE"
        )

    return TrainingSnapshot(
        dataset_id=(
            EXPECTED_DATASET_ID
        ),
        dataset_path=(
            dataset_path
        ),
        manifest_path=(
            manifest_path
        ),
        dataset_sha256=(
            actual_dataset_sha256
        ),
        manifest_sha256=(
            EXPECTED_TRAINING_MANIFEST_SHA256
        ),
        feature_columns=(
            feature_columns
        ),
        row_count=int(
            manifest.get(
                "row_count",
                0,
            )
        ),
        training_contract_version=(
            TRAINING_CONTRACT_VERSION
        ),
        base_timeframe=str(
            manifest.get(
                "base_timeframe",
                "",
            )
        ).strip().upper(),
    )


# =============================================================================
# Research frame loading
# =============================================================================

def _load_train_validation_frame(
    *,
    trainer: Any,
    snapshot: Any,
) -> pd.DataFrame:
    frame = pd.read_csv(
        snapshot.dataset_path
    )

    if frame.empty:
        raise RuntimeError(
            "FROZEN_TRAINING_DATASET_EMPTY"
        )

    if (
        snapshot.row_count
        > 0
        and
        len(
            frame
        )
        !=
        snapshot.row_count
    ):
        raise RuntimeError(
            "FROZEN_TRAINING_ROW_COUNT_MISMATCH"
        )

    required_columns = {
        "target_class",
        "target_class_id",
        "target_tradeable",
        "target_profit_atr",
        "target_max_adverse_atr",
        "dataset_split",
    }

    required_columns.update(
        snapshot.feature_columns
    )

    missing = sorted(
        required_columns
        -
        set(
            frame.columns
        )
    )

    if missing:
        raise RuntimeError(
            (
                "FROZEN_TRAINING_COLUMNS_MISSING: "
                + ", ".join(
                    missing
                )
            )
        )

    # TEST rows are deliberately excluded immediately.
    # They are not validated, evaluated, ranked, or inspected by this sweep.
    research_frame = (
        frame.loc[
            frame[
                "dataset_split"
            ].isin(
                (
                    "TRAIN",
                    "VALIDATION",
                )
            )
        ]
        .reset_index(
            drop=True
        )
    )

    if research_frame.empty:
        raise RuntimeError(
            "TRAIN_VALIDATION_RESEARCH_FRAME_EMPTY"
        )

    trainer._validate_frozen_target_frame(
        research_frame
    )

    return research_frame


# =============================================================================
# Candidate result projection
# =============================================================================

def _project_candidate_result(
    *,
    candidate: StageBCandidate,
    train_metrics: dict[str, Any],
    validation_metrics: dict[str, Any],
) -> dict[str, Any]:
    train_stage_b = (
        train_metrics[
            STAGE_B_METRICS_KEY
        ]
    )

    validation_stage_b = (
        validation_metrics[
            STAGE_B_METRICS_KEY
        ]
    )

    train_combined = (
        train_metrics[
            COMBINED_METRICS_KEY
        ]
    )

    validation_combined = (
        validation_metrics[
            COMBINED_METRICS_KEY
        ]
    )

    train_stage_b_balanced_accuracy = (
        _require_finite_number(
            name=(
                "train_stage_b_balanced_accuracy"
            ),
            value=(
                train_stage_b[
                    "balanced_accuracy"
                ]
            ),
        )
    )

    validation_stage_b_balanced_accuracy = (
        _require_finite_number(
            name=(
                "validation_stage_b_balanced_accuracy"
            ),
            value=(
                validation_stage_b[
                    "balanced_accuracy"
                ]
            ),
        )
    )

    train_stage_b_macro_f1 = (
        _require_finite_number(
            name=(
                "train_stage_b_macro_f1"
            ),
            value=(
                train_stage_b[
                    "macro_f1"
                ]
            ),
        )
    )

    validation_stage_b_macro_f1 = (
        _require_finite_number(
            name=(
                "validation_stage_b_macro_f1"
            ),
            value=(
                validation_stage_b[
                    "macro_f1"
                ]
            ),
        )
    )

    train_combined_macro_f1 = (
        _require_finite_number(
            name=(
                "train_combined_macro_f1"
            ),
            value=(
                train_combined[
                    "macro_f1"
                ]
            ),
        )
    )

    validation_combined_macro_f1 = (
        _require_finite_number(
            name=(
                "validation_combined_macro_f1"
            ),
            value=(
                validation_combined[
                    "macro_f1"
                ]
            ),
        )
    )

    validation_combined_balanced_accuracy = (
        _require_finite_number(
            name=(
                "validation_combined_balanced_accuracy"
            ),
            value=(
                validation_combined[
                    "balanced_accuracy"
                ]
            ),
        )
    )

    validation_stage_b_binary_ece = (
        _require_finite_number(
            name=(
                "validation_stage_b_binary_ece"
            ),
            value=(
                validation_stage_b[
                    "binary_probability_ece"
                ]
            ),
        )
    )

    validation_trade_selection = (
        validation_combined[
            "trade_selection"
        ]
    )

    return {
        "name": (
            candidate.name
        ),
        "stage_b_parameters": (
            candidate.parameter_document()
        ),
        "selection_metrics": {
            "combined_validation_macro_f1": (
                validation_combined_macro_f1
            ),
            "stage_b_validation_balanced_accuracy": (
                validation_stage_b_balanced_accuracy
            ),
            "combined_validation_balanced_accuracy": (
                validation_combined_balanced_accuracy
            ),
            "stage_b_validation_binary_ece": (
                validation_stage_b_binary_ece
            ),
        },
        "train": {
            "stage_b": {
                "balanced_accuracy": (
                    train_stage_b_balanced_accuracy
                ),
                "macro_f1": (
                    train_stage_b_macro_f1
                ),
                "short": (
                    _class_metrics(
                        metrics=(
                            train_stage_b
                        ),
                        class_name="SHORT",
                    )
                ),
                "long": (
                    _class_metrics(
                        metrics=(
                            train_stage_b
                        ),
                        class_name="LONG",
                    )
                ),
            },
            "combined": {
                "balanced_accuracy": (
                    _require_finite_number(
                        name=(
                            "train_combined_balanced_accuracy"
                        ),
                        value=(
                            train_combined[
                                "balanced_accuracy"
                            ]
                        ),
                    )
                ),
                "macro_f1": (
                    train_combined_macro_f1
                ),
            },
        },
        "validation": {
            "stage_b": {
                "accuracy": (
                    _require_finite_number(
                        name=(
                            "validation_stage_b_accuracy"
                        ),
                        value=(
                            validation_stage_b[
                                "accuracy"
                            ]
                        ),
                    )
                ),
                "balanced_accuracy": (
                    validation_stage_b_balanced_accuracy
                ),
                "macro_f1": (
                    validation_stage_b_macro_f1
                ),
                "binary_brier": (
                    _require_finite_number(
                        name=(
                            "validation_stage_b_binary_brier"
                        ),
                        value=(
                            validation_stage_b[
                                "binary_brier"
                            ]
                        ),
                    )
                ),
                "binary_ece": (
                    validation_stage_b_binary_ece
                ),
                "short": (
                    _class_metrics(
                        metrics=(
                            validation_stage_b
                        ),
                        class_name="SHORT",
                    )
                ),
                "long": (
                    _class_metrics(
                        metrics=(
                            validation_stage_b
                        ),
                        class_name="LONG",
                    )
                ),
            },
            "combined": {
                "accuracy": (
                    _require_finite_number(
                        name=(
                            "validation_combined_accuracy"
                        ),
                        value=(
                            validation_combined[
                                "accuracy"
                            ]
                        ),
                    )
                ),
                "balanced_accuracy": (
                    validation_combined_balanced_accuracy
                ),
                "macro_f1": (
                    validation_combined_macro_f1
                ),
                "log_loss": (
                    _require_finite_number(
                        name=(
                            "validation_combined_log_loss"
                        ),
                        value=(
                            validation_combined[
                                "log_loss"
                            ]
                        ),
                    )
                ),
                "multiclass_brier": (
                    _require_finite_number(
                        name=(
                            "validation_combined_brier"
                        ),
                        value=(
                            validation_combined[
                                "multiclass_brier"
                            ]
                        ),
                    )
                ),
                "ece": (
                    _require_finite_number(
                        name=(
                            "validation_combined_ece"
                        ),
                        value=(
                            validation_combined[
                                "expected_calibration_error"
                            ]
                        ),
                    )
                ),
                "short": (
                    _class_metrics(
                        metrics=(
                            validation_combined
                        ),
                        class_name="SHORT",
                    )
                ),
                "no_trade": (
                    _class_metrics(
                        metrics=(
                            validation_combined
                        ),
                        class_name="NO_TRADE",
                    )
                ),
                "long": (
                    _class_metrics(
                        metrics=(
                            validation_combined
                        ),
                        class_name="LONG",
                    )
                ),
                "prediction_distribution": dict(
                    validation_combined[
                        "prediction_distribution"
                    ]
                ),
                "predicted_trade_coverage": (
                    _require_finite_number(
                        name=(
                            "validation_predicted_trade_coverage"
                        ),
                        value=(
                            validation_trade_selection[
                                "predicted_trade_coverage"
                            ]
                        ),
                    )
                ),
                "tradeability_precision": (
                    _require_finite_number(
                        name=(
                            "validation_tradeability_precision"
                        ),
                        value=(
                            validation_trade_selection[
                                "tradeability_precision"
                            ]
                        ),
                    )
                    if (
                        validation_trade_selection[
                            "tradeability_precision"
                        ]
                        is not None
                    )
                    else None
                ),
                "direction_accuracy_when_predicted_trade_is_tradeable": (
                    _require_finite_number(
                        name=(
                            "validation_direction_accuracy"
                        ),
                        value=(
                            validation_trade_selection[
                                "direction_accuracy_when_predicted_trade_is_tradeable"
                            ]
                        ),
                    )
                    if (
                        validation_trade_selection[
                            "direction_accuracy_when_predicted_trade_is_tradeable"
                        ]
                        is not None
                    )
                    else None
                ),
            },
        },
        "generalization_gap": {
            "stage_b_balanced_accuracy_train_minus_validation": (
                train_stage_b_balanced_accuracy
                -
                validation_stage_b_balanced_accuracy
            ),
            "stage_b_macro_f1_train_minus_validation": (
                train_stage_b_macro_f1
                -
                validation_stage_b_macro_f1
            ),
            "combined_macro_f1_train_minus_validation": (
                train_combined_macro_f1
                -
                validation_combined_macro_f1
            ),
        },
    }


# =============================================================================
# Validation-only ranking
# =============================================================================

def _selection_key(
    result: dict[str, Any],
) -> tuple[
    float,
    float,
    float,
    float,
]:
    metrics = (
        result[
            "selection_metrics"
        ]
    )

    return (
        float(
            metrics[
                "combined_validation_macro_f1"
            ]
        ),
        float(
            metrics[
                "stage_b_validation_balanced_accuracy"
            ]
        ),
        float(
            metrics[
                "combined_validation_balanced_accuracy"
            ]
        ),
        -float(
            metrics[
                "stage_b_validation_binary_ece"
            ]
        ),
    )


def _attach_baseline_deltas(
    *,
    results: list[
        dict[str, Any]
    ],
) -> None:
    baseline = next(
        (
            result
            for result
            in results
            if (
                result[
                    "name"
                ]
                ==
                "baseline_v4"
            )
        ),
        None,
    )

    if baseline is None:
        raise RuntimeError(
            "BASELINE_V4_RESULT_MISSING"
        )

    baseline_metrics = (
        baseline[
            "selection_metrics"
        ]
    )

    for result in results:
        metrics = (
            result[
                "selection_metrics"
            ]
        )

        result[
            "delta_vs_baseline"
        ] = {
            "combined_validation_macro_f1": (
                float(
                    metrics[
                        "combined_validation_macro_f1"
                    ]
                )
                -
                float(
                    baseline_metrics[
                        "combined_validation_macro_f1"
                    ]
                )
            ),
            "stage_b_validation_balanced_accuracy": (
                float(
                    metrics[
                        "stage_b_validation_balanced_accuracy"
                    ]
                )
                -
                float(
                    baseline_metrics[
                        "stage_b_validation_balanced_accuracy"
                    ]
                )
            ),
            "combined_validation_balanced_accuracy": (
                float(
                    metrics[
                        "combined_validation_balanced_accuracy"
                    ]
                )
                -
                float(
                    baseline_metrics[
                        "combined_validation_balanced_accuracy"
                    ]
                )
            ),
            "stage_b_validation_binary_ece": (
                float(
                    metrics[
                        "stage_b_validation_binary_ece"
                    ]
                )
                -
                float(
                    baseline_metrics[
                        "stage_b_validation_binary_ece"
                    ]
                )
            ),
        }


# =============================================================================
# Sweep
# =============================================================================

def run_sweep() -> dict[str, Any]:
    trainer = (
        XAUUSDHierarchicalModelV4Trainer()
    )

    snapshot = (
        _discover_frozen_training_snapshot(
            trainer=trainer
        )
    )

    # Validate frozen V3 -> V2 target lineage directly from the immutable
    # training manifest. No MT5 / InstrumentContext is required here.
    trainer._load_and_validate_v3_manifest(
        snapshot=snapshot
    )

    frame = (
        _load_train_validation_frame(
            trainer=trainer,
            snapshot=snapshot,
        )
    )

    features = list(
        snapshot.feature_columns
    )

    train = (
        frame.loc[
            frame[
                "dataset_split"
            ]
            ==
            "TRAIN"
        ]
        .reset_index(
            drop=True
        )
    )

    validation = (
        frame.loc[
            frame[
                "dataset_split"
            ]
            ==
            "VALIDATION"
        ]
        .reset_index(
            drop=True
        )
    )

    if (
        train.empty
        or
        validation.empty
    ):
        raise RuntimeError(
            "EMPTY_REQUIRED_SWEEP_SPLIT"
        )

    _require_equal(
        actual=len(
            train
        ),
        expected=(
            EXPECTED_TRAIN_ROWS
        ),
        reason=(
            "SWEEP_TRAIN_ROW_COUNT_MISMATCH"
        ),
    )

    _require_equal(
        actual=len(
            validation
        ),
        expected=(
            EXPECTED_VALIDATION_ROWS
        ),
        reason=(
            "SWEEP_VALIDATION_ROW_COUNT_MISMATCH"
        ),
    )

    x_train_raw = (
        train[
            features
        ]
        .to_numpy(
            dtype=np.float64
        )
    )

    x_validation_raw = (
        validation[
            features
        ]
        .to_numpy(
            dtype=np.float64
        )
    )

    y_train = (
        train[
            "target_class_id"
        ]
        .to_numpy(
            dtype=np.int8
        )
    )

    y_validation = (
        validation[
            "target_class_id"
        ]
        .to_numpy(
            dtype=np.int8
        )
    )

    _require_finite_array(
        name="RAW_TRAIN",
        values=x_train_raw,
    )

    _require_finite_array(
        name="RAW_VALIDATION",
        values=x_validation_raw,
    )

    tradeable_train_mask = (
        y_train != 0
    )

    tradeable_validation_mask = (
        y_validation != 0
    )

    train_tradeable_rows = int(
        np.sum(
            tradeable_train_mask
        )
    )

    validation_tradeable_rows = int(
        np.sum(
            tradeable_validation_mask
        )
    )

    _require_equal(
        actual=(
            train_tradeable_rows
        ),
        expected=(
            EXPECTED_TRAIN_TRADEABLE_ROWS
        ),
        reason=(
            "SWEEP_TRAIN_TRADEABLE_ROW_COUNT_MISMATCH"
        ),
    )

    _require_equal(
        actual=(
            validation_tradeable_rows
        ),
        expected=(
            EXPECTED_VALIDATION_TRADEABLE_ROWS
        ),
        reason=(
            "SWEEP_VALIDATION_TRADEABLE_ROW_COUNT_MISMATCH"
        ),
    )

    y_stage_a_train = (
        (
            y_train != 0
        )
        .astype(
            np.int8
        )
    )

    y_stage_b_train = (
        y_train[
            tradeable_train_mask
        ]
    )

    if set(
        int(
            value
        )
        for value
        in np.unique(
            y_stage_a_train
        )
    ) != set(
        STAGE_A_CLASS_IDS
    ):
        raise RuntimeError(
            "SWEEP_STAGE_A_TRAIN_CLASS_CONTRACT_MISMATCH"
        )

    if set(
        int(
            value
        )
        for value
        in np.unique(
            y_stage_b_train
        )
    ) != set(
        STAGE_B_CLASS_IDS
    ):
        raise RuntimeError(
            "SWEEP_STAGE_B_TRAIN_CLASS_CONTRACT_MISMATCH"
        )

    # =========================================================================
    # Fixed Stage A
    # =========================================================================

    stage_a_scaler = StandardScaler(
        copy=True,
        with_mean=True,
        with_std=True,
    )

    x_stage_a_train = (
        stage_a_scaler.fit_transform(
            x_train_raw
        )
    )

    x_stage_a_validation = (
        stage_a_scaler.transform(
            x_validation_raw
        )
    )

    _require_finite_array(
        name="STAGE_A_TRAIN",
        values=x_stage_a_train,
    )

    _require_finite_array(
        name="STAGE_A_VALIDATION",
        values=x_stage_a_validation,
    )

    (
        stage_a_sample_weights,
        stage_a_class_weights,
    ) = (
        trainer._binary_sample_weights(
            y_stage_a_train,
            class_ids=(
                STAGE_A_CLASS_IDS
            ),
            class_names=(
                STAGE_A_CLASS_NAMES
            ),
            balance_power=(
                STAGE_A_CLASS_BALANCE_POWER
            ),
        )
    )

    trainer._validate_hyperparameters(
        max_iter=(
            STAGE_A_PARAMETERS[
                "max_iter"
            ]
        ),
        learning_rate=(
            STAGE_A_PARAMETERS[
                "learning_rate"
            ]
        ),
        max_leaf_nodes=(
            STAGE_A_PARAMETERS[
                "max_leaf_nodes"
            ]
        ),
        min_samples_leaf=(
            STAGE_A_PARAMETERS[
                "min_samples_leaf"
            ]
        ),
        l2_regularization=(
            STAGE_A_PARAMETERS[
                "l2_regularization"
            ]
        ),
    )

    stage_a_model = (
        HistGradientBoostingClassifier(
            learning_rate=float(
                STAGE_A_PARAMETERS[
                    "learning_rate"
                ]
            ),
            max_iter=int(
                STAGE_A_PARAMETERS[
                    "max_iter"
                ]
            ),
            max_leaf_nodes=int(
                STAGE_A_PARAMETERS[
                    "max_leaf_nodes"
                ]
            ),
            min_samples_leaf=int(
                STAGE_A_PARAMETERS[
                    "min_samples_leaf"
                ]
            ),
            l2_regularization=float(
                STAGE_A_PARAMETERS[
                    "l2_regularization"
                ]
            ),
            early_stopping=False,
            random_state=(
                RANDOM_STATE
            ),
        )
    )

    stage_a_model.fit(
        x_stage_a_train,
        y_stage_a_train,
        sample_weight=(
            stage_a_sample_weights
        ),
    )

    trainer._require_model_classes(
        stage_a_model,
        STAGE_A_CLASS_IDS,
        "SWEEP_STAGE_A_MODEL_CLASS_ORDER_MISMATCH",
    )

    # =========================================================================
    # Fixed Stage B scaler
    # =========================================================================

    stage_b_scaler = StandardScaler(
        copy=True,
        with_mean=True,
        with_std=True,
    )

    x_stage_b_tradeable_train = (
        stage_b_scaler.fit_transform(
            x_train_raw[
                tradeable_train_mask
            ]
        )
    )

    x_stage_b_train_all = (
        stage_b_scaler.transform(
            x_train_raw
        )
    )

    x_stage_b_validation = (
        stage_b_scaler.transform(
            x_validation_raw
        )
    )

    _require_finite_array(
        name=(
            "STAGE_B_TRADEABLE_TRAIN"
        ),
        values=(
            x_stage_b_tradeable_train
        ),
    )

    _require_finite_array(
        name=(
            "STAGE_B_TRAIN_ALL"
        ),
        values=(
            x_stage_b_train_all
        ),
    )

    _require_finite_array(
        name=(
            "STAGE_B_VALIDATION"
        ),
        values=(
            x_stage_b_validation
        ),
    )

    (
        stage_b_sample_weights,
        stage_b_class_weights,
    ) = (
        trainer._binary_sample_weights(
            y_stage_b_train,
            class_ids=(
                STAGE_B_CLASS_IDS
            ),
            class_names=(
                STAGE_B_CLASS_NAMES
            ),
            balance_power=(
                STAGE_B_CLASS_BALANCE_POWER
            ),
        )
    )

    # =========================================================================
    # Stage B validation-only candidate sweep
    # =========================================================================

    candidate_results: list[
        dict[str, Any]
    ] = []

    for candidate in CANDIDATES:
        trainer._validate_hyperparameters(
            max_iter=(
                candidate.max_iter
            ),
            learning_rate=(
                candidate.learning_rate
            ),
            max_leaf_nodes=(
                candidate.max_leaf_nodes
            ),
            min_samples_leaf=(
                candidate.min_samples_leaf
            ),
            l2_regularization=(
                candidate.l2_regularization
            ),
        )

        stage_b_model = (
            HistGradientBoostingClassifier(
                **candidate.model_parameters()
            )
        )

        stage_b_model.fit(
            x_stage_b_tradeable_train,
            y_stage_b_train,
            sample_weight=(
                stage_b_sample_weights
            ),
        )

        trainer._require_model_classes(
            stage_b_model,
            STAGE_B_CLASS_IDS,
            "SWEEP_STAGE_B_MODEL_CLASS_ORDER_MISMATCH",
        )

        # TRAIN metrics are diagnostic only.
        train_metrics = (
            trainer._evaluate_split(
                stage_a_model=(
                    stage_a_model
                ),
                stage_b_model=(
                    stage_b_model
                ),
                x_stage_a=(
                    x_stage_a_train
                ),
                x_stage_b=(
                    x_stage_b_train_all
                ),
                y_final=(
                    y_train
                ),
            )
        )

        # VALIDATION is the only candidate-selection split.
        validation_metrics = (
            trainer._evaluate_split(
                stage_a_model=(
                    stage_a_model
                ),
                stage_b_model=(
                    stage_b_model
                ),
                x_stage_a=(
                    x_stage_a_validation
                ),
                x_stage_b=(
                    x_stage_b_validation
                ),
                y_final=(
                    y_validation
                ),
            )
        )

        candidate_results.append(
            _project_candidate_result(
                candidate=(
                    candidate
                ),
                train_metrics=(
                    train_metrics
                ),
                validation_metrics=(
                    validation_metrics
                ),
            )
        )

    _attach_baseline_deltas(
        results=(
            candidate_results
        )
    )

    ranked_results = sorted(
        candidate_results,
        key=(
            _selection_key
        ),
        reverse=True,
    )

    best_by_policy = (
        ranked_results[
            0
        ]
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_V4_STAGE_B_VALIDATION_SWEEP"
        ),
        "sweep_version": (
            SWEEP_VERSION
        ),
        "research_lane": (
            "RESEARCH_LANE_2_XAUUSD_ML"
        ),
        "model_id": (
            "XAUUSD_MODEL_v4_HIERARCHICAL"
        ),
        "training_contract_version": (
            TRAINING_CONTRACT_VERSION
        ),
        "dataset": {
            "dataset_id": (
                snapshot.dataset_id
            ),
            "dataset_sha256": (
                snapshot.dataset_sha256
            ),
            "training_manifest_sha256": (
                snapshot.manifest_sha256
            ),
            "feature_count": (
                len(
                    features
                )
            ),
            "manifest_path": str(
                snapshot.manifest_path
            ),
            "dataset_path": str(
                snapshot.dataset_path
            ),
        },
        "rows_used": {
            "TRAIN": (
                len(
                    train
                )
            ),
            "VALIDATION": (
                len(
                    validation
                )
            ),
            "TRAIN_TRADEABLE": (
                train_tradeable_rows
            ),
            "VALIDATION_TRADEABLE": (
                validation_tradeable_rows
            ),
        },
        "scientific_policy": {
            "data_source": (
                "FROZEN_IMMUTABLE_LOCAL_V3_DATASET"
            ),
            "mt5_used": False,
            "broker_attestation_used": False,
            "active_account_state_used": False,
            "stage_a_fit_scope": (
                "TRAIN_ONLY_ALL_ROWS"
            ),
            "stage_a_status": (
                "FIXED_BASELINE"
            ),
            "stage_b_fit_scope": (
                "TRAIN_ONLY_TRUE_TRADEABLE_ROWS"
            ),
            "candidate_selection_scope": (
                "VALIDATION_ONLY"
            ),
            "train_metrics_usage": (
                "GENERALIZATION_DIAGNOSTIC_ONLY"
            ),
            "validation_metrics_usage": (
                "CANDIDATE_SELECTION"
            ),
            "test_selected": False,
            "test_evaluated": False,
            "test_used_for_candidate_selection": False,
            "artifact_writes": False,
            "live_authorized": False,
        },
        "fixed_stage_a": {
            "parameters": dict(
                STAGE_A_PARAMETERS
            ),
            "class_balance_power": (
                STAGE_A_CLASS_BALANCE_POWER
            ),
            "class_weights": (
                stage_a_class_weights
            ),
            "random_state": (
                RANDOM_STATE
            ),
        },
        "fixed_stage_b_training_contract": {
            "class_balance_power": (
                STAGE_B_CLASS_BALANCE_POWER
            ),
            "class_weights": (
                stage_b_class_weights
            ),
            "random_state": (
                RANDOM_STATE + 1
            ),
            "scaler_fit_scope": (
                "TRAIN_ONLY_TRUE_TRADEABLE_ROWS"
            ),
        },
        "selection_policy": {
            "primary": (
                "combined_validation_macro_f1_max"
            ),
            "tie_breakers_in_order": [
                (
                    "stage_b_validation_balanced_accuracy_max"
                ),
                (
                    "combined_validation_balanced_accuracy_max"
                ),
                (
                    "stage_b_validation_binary_ece_min"
                ),
            ],
            "winner_requires_manual_scientific_review": True,
            "review_requirements": [
                (
                    "meaningful_validation_improvement"
                ),
                (
                    "SHORT_LONG_balance"
                ),
                (
                    "train_validation_generalization_gap"
                ),
            ],
        },
        "best_candidate_by_policy": {
            "name": (
                best_by_policy[
                    "name"
                ]
            ),
            "selection_metrics": (
                best_by_policy[
                    "selection_metrics"
                ]
            ),
            "delta_vs_baseline": (
                best_by_policy[
                    "delta_vs_baseline"
                ]
            ),
        },
        "candidate_ranking": [
            result[
                "name"
            ]
            for result
            in ranked_results
        ],
        "candidates": (
            candidate_results
        ),
        "live_authorized": False,
    }


# =============================================================================
# CLI
# =============================================================================

def main() -> int:
    try:
        result = (
            run_sweep()
        )

    except Exception as exc:
        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_V4_STAGE_B_VALIDATION_SWEEP_FAILED"
                    ),
                    "error_type": (
                        type(
                            exc
                        ).__name__
                    ),
                    "error": str(
                        exc
                    ),
                    "mt5_used": False,
                    "test_selected": False,
                    "test_evaluated": False,
                    "artifact_writes": False,
                    "live_authorized": False,
                },
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
        )

        return 2

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )