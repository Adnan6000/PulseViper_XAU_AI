from __future__ import annotations

import importlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler


ROOT_DIR = Path(__file__).resolve().parents[3]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


sweep_module: Any = importlib.import_module(
    "04_Testing.research.legacy_ml.tune_xauusd_hierarchical_model_v4_stage_b"
)

trainer_module: Any = importlib.import_module(
    "02_AI.Models.xauusd_hierarchical_model_v4_trainer"
)


XAUUSDHierarchicalModelV4Trainer: Any = (
    trainer_module.XAUUSDHierarchicalModelV4Trainer
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

STAGE_B_METRICS_KEY = (
    trainer_module.STAGE_B_METRICS_KEY
)

COMBINED_METRICS_KEY = (
    trainer_module.COMBINED_METRICS_KEY
)


ANALYSIS_VERSION = (
    "XAUUSD_V4_STAGE_B_TEMPORAL_ROBUSTNESS_V1"
)

REFERENCE_CANDIDATE_NAMES = (
    "baseline_v4",
    "reg_180_15_100",
)

WALK_FORWARD_EVALUATION_FOLDS = 4

VALIDATION_BLOCKS = 4

DEFAULT_TARGET_HORIZON_BARS = 12


RANDOM_STATE = int(
    sweep_module.RANDOM_STATE
)

STAGE_A_PARAMETERS = dict(
    sweep_module.STAGE_A_PARAMETERS
)

STAGE_A_CLASS_BALANCE_POWER = float(
    sweep_module.STAGE_A_CLASS_BALANCE_POWER
)

STAGE_B_CLASS_BALANCE_POWER = float(
    sweep_module.STAGE_B_CLASS_BALANCE_POWER
)


def _finite_float(
    value: Any,
    *,
    name: str,
) -> float:

    result = float(
        value
    )

    if not math.isfinite(
        result
    ):
        raise RuntimeError(
            f"NONFINITE_TEMPORAL_METRIC: {name}"
        )

    return result


def _require_finite_matrix(
    values: np.ndarray,
    *,
    name: str,
) -> None:

    if not np.isfinite(
        values
    ).all():
        raise RuntimeError(
            f"NONFINITE_TEMPORAL_MATRIX: {name}"
        )


def _unique_string(
    frame: pd.DataFrame,
    column: str,
    *,
    required: bool = True,
) -> str | None:

    if column not in frame.columns:

        if required:
            raise RuntimeError(
                f"DATASET_IDENTITY_COLUMN_MISSING: {column}"
            )

        return None

    values = sorted(
        {
            str(
                value
            ).strip()
            for value
            in frame[
                column
            ]
            .dropna()
            .tolist()
            if str(
                value
            ).strip()
        }
    )

    if len(
        values
    ) != 1:
        raise RuntimeError(
            (
                f"DATASET_IDENTITY_NOT_UNIQUE: "
                f"{column}: "
                f"{values}"
            )
        )

    return values[
        0
    ]


def _dataset_identity(
    frame: pd.DataFrame,
) -> dict[str, Any]:

    return {
        "canonical_symbol": (
            _unique_string(
                frame,
                "pv_canonical_symbol",
            )
        ),
        "asset_class": (
            _unique_string(
                frame,
                "pv_asset_class",
            )
        ),
        "broker_id": (
            _unique_string(
                frame,
                "pv_broker_id",
            )
        ),
        "broker_symbol": (
            _unique_string(
                frame,
                "pv_broker_symbol",
            )
        ),
        "account_scope_id": (
            _unique_string(
                frame,
                "pv_account_scope_id",
                required=False,
            )
        ),
        "execution_environment": (
            _unique_string(
                frame,
                "pv_execution_environment",
                required=False,
            )
        ),
        "contract_spec_id": (
            _unique_string(
                frame,
                "pv_contract_spec_id",
            )
        ),
        "data_schema_version": (
            _unique_string(
                frame,
                "pv_data_schema_version",
            )
        ),
        "feature_contract_version": (
            _unique_string(
                frame,
                "pv_feature_contract_version",
            )
        ),
    }


def _decision_time_series(
    frame: pd.DataFrame,
) -> pd.Series | None:

    if (
        "decision_time"
        not in frame.columns
    ):
        return None

    result = pd.to_datetime(
        frame[
            "decision_time"
        ],
        utc=True,
        errors="raise",
    )

    if not result.is_monotonic_increasing:
        raise RuntimeError(
            "DECISION_TIME_NOT_MONOTONIC"
        )

    return result


def _time_range_document(
    frame: pd.DataFrame,
) -> dict[str, Any]:

    series = (
        _decision_time_series(
            frame
        )
    )

    if (
        series is None
        or
        frame.empty
    ):
        return {
            "time_column": None,
            "start": None,
            "end": None,
            "ordering_basis": (
                "FROZEN_MATRIX_ROW_ORDER_"
                "CHRONOLOGICAL_BY_BUILDER_CONTRACT"
            ),
        }

    return {
        "time_column": (
            "decision_time"
        ),
        "start": (
            series.iloc[
                0
            ].isoformat()
        ),
        "end": (
            series.iloc[
                -1
            ].isoformat()
        ),
        "ordering_basis": (
            "DECISION_TIME"
        ),
    }


def _collect_horizon_values(
    value: Any,
) -> list[int]:

    found: list[
        int
    ] = []

    if isinstance(
        value,
        dict,
    ):

        for (
            key,
            child,
        ) in value.items():

            if (
                str(
                    key
                )
                .strip()
                .lower()
                in {
                    "horizon_bars",
                    "target_horizon_bars",
                    "forward_horizon_bars",
                }
            ):

                try:
                    candidate = int(
                        child
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    candidate = 0

                if candidate > 0:
                    found.append(
                        candidate
                    )

            found.extend(
                _collect_horizon_values(
                    child
                )
            )

    elif isinstance(
        value,
        list,
    ):

        for child in value:

            found.extend(
                _collect_horizon_values(
                    child
                )
            )

    return found


def _resolve_internal_purge_rows(
    *,
    snapshot: Any,
    research_frame: pd.DataFrame,
) -> dict[str, Any]:

    manifest = json.loads(
        snapshot
        .manifest_path
        .read_text(
            encoding="utf-8"
        )
    )

    manifest_candidates = sorted(
        set(
            _collect_horizon_values(
                manifest
            )
        )
    )

    resolution_max: int | None = None

    if (
        "target_resolution_bars"
        in research_frame.columns
    ):

        resolution = pd.to_numeric(
            research_frame[
                "target_resolution_bars"
            ],
            errors="coerce",
        )

        finite = resolution[
            np.isfinite(
                resolution
            )
        ]

        if not finite.empty:

            candidate = int(
                finite.max()
            )

            if candidate > 0:
                resolution_max = (
                    candidate
                )

    candidates = [
        DEFAULT_TARGET_HORIZON_BARS,
        *manifest_candidates,
    ]

    if resolution_max is not None:
        candidates.append(
            resolution_max
        )

    return {
        "purge_rows": int(
            max(
                candidates
            )
        ),
        "default_target_horizon_bars": (
            DEFAULT_TARGET_HORIZON_BARS
        ),
        "manifest_horizon_candidates": (
            manifest_candidates
        ),
        "max_target_resolution_bars_observed": (
            resolution_max
        ),
        "policy": (
            "USE_MAX_AVAILABLE_HORIZON_EVIDENCE_"
            "FOR_CONSERVATIVE_INTERNAL_PURGE"
        ),
    }


def _reference_candidates(
) -> dict[str, Any]:

    by_name = {
        candidate.name: (
            candidate
        )
        for candidate
        in sweep_module.CANDIDATES
    }

    missing = [
        name
        for name
        in REFERENCE_CANDIDATE_NAMES
        if name
        not in by_name
    ]

    if missing:
        raise RuntimeError(
            (
                "REFERENCE_STAGE_B_CANDIDATES_MISSING: "
                +
                ", ".join(
                    missing
                )
            )
        )

    return {
        name: (
            by_name[
                name
            ]
        )
        for name
        in REFERENCE_CANDIDATE_NAMES
    }


def _validate_class_contract(
    y_final: np.ndarray,
    *,
    name: str,
) -> None:

    actual = {
        int(
            value
        )
        for value
        in np.unique(
            y_final
        )
    }

    if actual != {
        -1,
        0,
        1,
    }:
        raise RuntimeError(
            (
                f"{name}_FINAL_CLASS_CONTRACT_MISMATCH: "
                f"{sorted(actual)}"
            )
        )


def _fit_stage_a_and_scalers(
    *,
    trainer: Any,
    x_fit_raw: np.ndarray,
    y_fit: np.ndarray,
) -> dict[str, Any]:

    _require_finite_matrix(
        x_fit_raw,
        name="FIT_RAW",
    )

    _validate_class_contract(
        y_fit,
        name="FIT",
    )

    y_stage_a = (
        y_fit
        !=
        0
    ).astype(
        np.int8
    )

    tradeable_mask = (
        y_fit
        !=
        0
    )

    y_stage_b = (
        y_fit[
            tradeable_mask
        ]
    )

    if {
        int(
            value
        )
        for value
        in np.unique(
            y_stage_a
        )
    } != set(
        STAGE_A_CLASS_IDS
    ):
        raise RuntimeError(
            "TEMPORAL_STAGE_A_FIT_CLASS_CONTRACT_MISMATCH"
        )

    if {
        int(
            value
        )
        for value
        in np.unique(
            y_stage_b
        )
    } != set(
        STAGE_B_CLASS_IDS
    ):
        raise RuntimeError(
            "TEMPORAL_STAGE_B_FIT_CLASS_CONTRACT_MISMATCH"
        )

    stage_a_scaler = (
        StandardScaler(
            copy=True,
            with_mean=True,
            with_std=True,
        )
    )

    x_stage_a_fit = (
        stage_a_scaler
        .fit_transform(
            x_fit_raw
        )
    )

    stage_b_scaler = (
        StandardScaler(
            copy=True,
            with_mean=True,
            with_std=True,
        )
    )

    x_stage_b_tradeable_fit = (
        stage_b_scaler
        .fit_transform(
            x_fit_raw[
                tradeable_mask
            ]
        )
    )

    _require_finite_matrix(
        x_stage_a_fit,
        name="STAGE_A_FIT",
    )

    _require_finite_matrix(
        x_stage_b_tradeable_fit,
        name="STAGE_B_TRADEABLE_FIT",
    )

    (
        stage_a_sample_weights,
        stage_a_class_weights,
    ) = (
        trainer
        ._binary_sample_weights(
            y_stage_a,
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

    (
        stage_b_sample_weights,
        stage_b_class_weights,
    ) = (
        trainer
        ._binary_sample_weights(
            y_stage_b,
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

    trainer._validate_hyperparameters(
        max_iter=int(
            STAGE_A_PARAMETERS[
                "max_iter"
            ]
        ),
        learning_rate=float(
            STAGE_A_PARAMETERS[
                "learning_rate"
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
        x_stage_a_fit,
        y_stage_a,
        sample_weight=(
            stage_a_sample_weights
        ),
    )

    trainer._require_model_classes(
        stage_a_model,
        STAGE_A_CLASS_IDS,
        "TEMPORAL_STAGE_A_MODEL_CLASS_ORDER_MISMATCH",
    )

    return {
        "stage_a_model": (
            stage_a_model
        ),
        "stage_a_scaler": (
            stage_a_scaler
        ),
        "stage_b_scaler": (
            stage_b_scaler
        ),
        "x_stage_b_tradeable_fit": (
            x_stage_b_tradeable_fit
        ),
        "y_stage_b_fit": (
            y_stage_b
        ),
        "stage_b_sample_weights": (
            stage_b_sample_weights
        ),
        "stage_a_class_weights": (
            stage_a_class_weights
        ),
        "stage_b_class_weights": (
            stage_b_class_weights
        ),
        "fit_rows": int(
            len(
                y_fit
            )
        ),
        "fit_tradeable_rows": int(
            np.sum(
                tradeable_mask
            )
        ),
    }


def _fit_stage_b_model(
    *,
    trainer: Any,
    candidate: Any,
    fit_bundle: dict[str, Any],
) -> Any:

    trainer._validate_hyperparameters(
        max_iter=int(
            candidate.max_iter
        ),
        learning_rate=float(
            candidate.learning_rate
        ),
        max_leaf_nodes=int(
            candidate.max_leaf_nodes
        ),
        min_samples_leaf=int(
            candidate.min_samples_leaf
        ),
        l2_regularization=float(
            candidate.l2_regularization
        ),
    )

    model = (
        HistGradientBoostingClassifier(
            **candidate
            .model_parameters()
        )
    )

    model.fit(
        fit_bundle[
            "x_stage_b_tradeable_fit"
        ],
        fit_bundle[
            "y_stage_b_fit"
        ],
        sample_weight=(
            fit_bundle[
                "stage_b_sample_weights"
            ]
        ),
    )

    trainer._require_model_classes(
        model,
        STAGE_B_CLASS_IDS,
        "TEMPORAL_STAGE_B_MODEL_CLASS_ORDER_MISMATCH",
    )

    return model


def _evaluate_frame(
    *,
    trainer: Any,
    fit_bundle: dict[str, Any],
    stage_b_model: Any,
    features: list[str],
    frame: pd.DataFrame,
) -> dict[str, Any]:

    if frame.empty:
        raise RuntimeError(
            "TEMPORAL_EVALUATION_FRAME_EMPTY"
        )

    x_raw = (
        frame[
            features
        ]
        .to_numpy(
            dtype=np.float64
        )
    )

    y_final = (
        frame[
            "target_class_id"
        ]
        .to_numpy(
            dtype=np.int8
        )
    )

    _require_finite_matrix(
        x_raw,
        name="EVALUATION_RAW",
    )

    x_stage_a = (
        fit_bundle[
            "stage_a_scaler"
        ]
        .transform(
            x_raw
        )
    )

    x_stage_b = (
        fit_bundle[
            "stage_b_scaler"
        ]
        .transform(
            x_raw
        )
    )

    _require_finite_matrix(
        x_stage_a,
        name="STAGE_A_EVALUATION",
    )

    _require_finite_matrix(
        x_stage_b,
        name="STAGE_B_EVALUATION",
    )

    return (
        trainer
        ._evaluate_split(
            stage_a_model=(
                fit_bundle[
                    "stage_a_model"
                ]
            ),
            stage_b_model=(
                stage_b_model
            ),
            x_stage_a=(
                x_stage_a
            ),
            x_stage_b=(
                x_stage_b
            ),
            y_final=(
                y_final
            ),
        )
    )


def _class_projection(
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
        "precision": (
            _finite_float(
                values[
                    "precision"
                ],
                name=(
                    f"{class_name}_precision"
                ),
            )
        ),
        "recall": (
            _finite_float(
                values[
                    "recall"
                ],
                name=(
                    f"{class_name}_recall"
                ),
            )
        ),
        "f1": (
            _finite_float(
                values[
                    "f1"
                ],
                name=(
                    f"{class_name}_f1"
                ),
            )
        ),
        "support": int(
            values[
                "support"
            ]
        ),
    }


def _metrics_projection(
    metrics: dict[str, Any],
) -> dict[str, Any]:

    stage_b = (
        metrics[
            STAGE_B_METRICS_KEY
        ]
    )

    combined = (
        metrics[
            COMBINED_METRICS_KEY
        ]
    )

    trade_selection = (
        combined[
            "trade_selection"
        ]
    )

    direction_accuracy = (
        trade_selection[
            "direction_accuracy_when_predicted_trade_is_tradeable"
        ]
    )

    tradeability_precision = (
        trade_selection[
            "tradeability_precision"
        ]
    )

    return {
        "stage_b": {
            "accuracy": (
                _finite_float(
                    stage_b[
                        "accuracy"
                    ],
                    name=(
                        "stage_b_accuracy"
                    ),
                )
            ),
            "balanced_accuracy": (
                _finite_float(
                    stage_b[
                        "balanced_accuracy"
                    ],
                    name=(
                        "stage_b_balanced_accuracy"
                    ),
                )
            ),
            "macro_f1": (
                _finite_float(
                    stage_b[
                        "macro_f1"
                    ],
                    name=(
                        "stage_b_macro_f1"
                    ),
                )
            ),
            "binary_brier": (
                _finite_float(
                    stage_b[
                        "binary_brier"
                    ],
                    name=(
                        "stage_b_binary_brier"
                    ),
                )
            ),
            "binary_ece": (
                _finite_float(
                    stage_b[
                        "binary_probability_ece"
                    ],
                    name=(
                        "stage_b_binary_ece"
                    ),
                )
            ),
            "short": (
                _class_projection(
                    stage_b,
                    "SHORT",
                )
            ),
            "long": (
                _class_projection(
                    stage_b,
                    "LONG",
                )
            ),
        },
        "combined": {
            "accuracy": (
                _finite_float(
                    combined[
                        "accuracy"
                    ],
                    name=(
                        "combined_accuracy"
                    ),
                )
            ),
            "balanced_accuracy": (
                _finite_float(
                    combined[
                        "balanced_accuracy"
                    ],
                    name=(
                        "combined_balanced_accuracy"
                    ),
                )
            ),
            "macro_f1": (
                _finite_float(
                    combined[
                        "macro_f1"
                    ],
                    name=(
                        "combined_macro_f1"
                    ),
                )
            ),
            "log_loss": (
                _finite_float(
                    combined[
                        "log_loss"
                    ],
                    name=(
                        "combined_log_loss"
                    ),
                )
            ),
            "multiclass_brier": (
                _finite_float(
                    combined[
                        "multiclass_brier"
                    ],
                    name=(
                        "combined_multiclass_brier"
                    ),
                )
            ),
            "ece": (
                _finite_float(
                    combined[
                        "expected_calibration_error"
                    ],
                    name=(
                        "combined_ece"
                    ),
                )
            ),
            "short": (
                _class_projection(
                    combined,
                    "SHORT",
                )
            ),
            "no_trade": (
                _class_projection(
                    combined,
                    "NO_TRADE",
                )
            ),
            "long": (
                _class_projection(
                    combined,
                    "LONG",
                )
            ),
            "prediction_distribution": dict(
                combined[
                    "prediction_distribution"
                ]
            ),
            "predicted_trade_coverage": (
                _finite_float(
                    trade_selection[
                        "predicted_trade_coverage"
                    ],
                    name=(
                        "predicted_trade_coverage"
                    ),
                )
            ),
            "tradeability_precision": (
                _finite_float(
                    tradeability_precision,
                    name=(
                        "tradeability_precision"
                    ),
                )
                if (
                    tradeability_precision
                    is not None
                )
                else None
            ),
            "direction_accuracy_when_predicted_trade_is_tradeable": (
                _finite_float(
                    direction_accuracy,
                    name=(
                        "direction_accuracy"
                    ),
                )
                if (
                    direction_accuracy
                    is not None
                )
                else None
            ),
        },
    }


def _path_value(
    document: dict[str, Any],
    path: tuple[str, ...],
) -> float:

    value: Any = (
        document
    )

    for key in path:
        value = (
            value[
                key
            ]
        )

    return (
        _finite_float(
            value,
            name=(
                ".".join(
                    path
                )
            ),
        )
    )


def _distribution(
    values: Iterable[float],
) -> dict[str, Any]:

    array = np.asarray(
        list(
            values
        ),
        dtype=np.float64,
    )

    if array.size == 0:
        raise RuntimeError(
            "EMPTY_TEMPORAL_METRIC_DISTRIBUTION"
        )

    _require_finite_matrix(
        array,
        name=(
            "TEMPORAL_METRIC_DISTRIBUTION"
        ),
    )

    return {
        "count": int(
            array.size
        ),
        "mean": float(
            np.mean(
                array
            )
        ),
        "std": float(
            np.std(
                array
            )
        ),
        "min": float(
            np.min(
                array
            )
        ),
        "max": float(
            np.max(
                array
            )
        ),
        "range": float(
            np.max(
                array
            )
            -
            np.min(
                array
            )
        ),
    }


def _temporal_summary(
    records: list[dict[str, Any]],
) -> dict[str, Any]:

    paths: dict[
        str,
        tuple[str, ...],
    ] = {
        "stage_b_balanced_accuracy": (
            "stage_b",
            "balanced_accuracy",
        ),
        "stage_b_macro_f1": (
            "stage_b",
            "macro_f1",
        ),
        "stage_b_binary_ece": (
            "stage_b",
            "binary_ece",
        ),
        "stage_b_short_f1": (
            "stage_b",
            "short",
            "f1",
        ),
        "stage_b_short_recall": (
            "stage_b",
            "short",
            "recall",
        ),
        "stage_b_long_f1": (
            "stage_b",
            "long",
            "f1",
        ),
        "stage_b_long_recall": (
            "stage_b",
            "long",
            "recall",
        ),
        "combined_macro_f1": (
            "combined",
            "macro_f1",
        ),
        "combined_balanced_accuracy": (
            "combined",
            "balanced_accuracy",
        ),
        "combined_predicted_trade_coverage": (
            "combined",
            "predicted_trade_coverage",
        ),
    }

    result: dict[
        str,
        Any,
    ] = {
        name: (
            _distribution(
                _path_value(
                    record[
                        "metrics"
                    ],
                    path,
                )
                for record
                in records
            )
        )
        for (
            name,
            path,
        )
        in paths.items()
    }

    stage_b_ba = [
        _path_value(
            record[
                "metrics"
            ],
            (
                "stage_b",
                "balanced_accuracy",
            ),
        )
        for record
        in records
    ]

    recall_imbalance = [
        abs(
            _path_value(
                record[
                    "metrics"
                ],
                (
                    "stage_b",
                    "short",
                    "recall",
                ),
            )
            -
            _path_value(
                record[
                    "metrics"
                ],
                (
                    "stage_b",
                    "long",
                    "recall",
                ),
            )
        )
        for record
        in records
    ]

    result[
        "stage_b_balanced_accuracy_above_0_50_blocks"
    ] = int(
        sum(
            value > 0.50
            for value
            in stage_b_ba
        )
    )

    result[
        "stage_b_balanced_accuracy_at_or_below_0_50_blocks"
    ] = int(
        sum(
            value <= 0.50
            for value
            in stage_b_ba
        )
    )

    result[
        "stage_b_short_long_recall_absolute_gap"
    ] = (
        _distribution(
            recall_imbalance
        )
    )

    return result


def _walk_forward_plan(
    *,
    rows: int,
    purge_rows: int,
) -> list[dict[str, int]]:

    if rows < 1000:
        raise RuntimeError(
            "INSUFFICIENT_TRAIN_ROWS_FOR_TEMPORAL_ANALYSIS"
        )

    segments = (
        WALK_FORWARD_EVALUATION_FOLDS
        +
        1
    )

    boundaries = np.linspace(
        0,
        rows,
        segments + 1,
        dtype=int,
    )

    plan: list[
        dict[str, int]
    ] = []

    for fold_index in range(
        1,
        segments,
    ):

        evaluation_start = int(
            boundaries[
                fold_index
            ]
        )

        evaluation_end = int(
            boundaries[
                fold_index
                +
                1
            ]
        )

        fit_end = (
            evaluation_start
            -
            purge_rows
        )

        if fit_end <= 0:
            raise RuntimeError(
                "TEMPORAL_PURGE_REMOVES_INITIAL_FIT_WINDOW"
            )

        if (
            evaluation_end
            <=
            evaluation_start
        ):
            raise RuntimeError(
                "INVALID_TEMPORAL_EVALUATION_WINDOW"
            )

        plan.append(
            {
                "fold": int(
                    fold_index
                ),
                "fit_start": 0,
                "fit_end_exclusive": int(
                    fit_end
                ),
                "purge_start": int(
                    fit_end
                ),
                "purge_end_exclusive": int(
                    evaluation_start
                ),
                "evaluation_start": int(
                    evaluation_start
                ),
                "evaluation_end_exclusive": int(
                    evaluation_end
                ),
            }
        )

    if (
        len(
            plan
        )
        !=
        WALK_FORWARD_EVALUATION_FOLDS
    ):
        raise RuntimeError(
            "WALK_FORWARD_FOLD_COUNT_MISMATCH"
        )

    return plan


def _validation_block_plan(
    *,
    rows: int,
) -> list[dict[str, int]]:

    boundaries = np.linspace(
        0,
        rows,
        VALIDATION_BLOCKS + 1,
        dtype=int,
    )

    result: list[
        dict[str, int]
    ] = []

    for block_index in range(
        VALIDATION_BLOCKS
    ):

        start = int(
            boundaries[
                block_index
            ]
        )

        end = int(
            boundaries[
                block_index
                +
                1
            ]
        )

        if end <= start:
            raise RuntimeError(
                "INVALID_VALIDATION_TEMPORAL_BLOCK"
            )

        result.append(
            {
                "block": int(
                    block_index
                    +
                    1
                ),
                "start": (
                    start
                ),
                "end_exclusive": (
                    end
                ),
            }
        )

    return result


def run_analysis(
) -> dict[str, Any]:

    trainer = (
        XAUUSDHierarchicalModelV4Trainer()
    )

    snapshot = (
        sweep_module
        ._discover_frozen_training_snapshot(
            trainer=trainer
        )
    )

    trainer._load_and_validate_v3_manifest(
        snapshot=snapshot
    )

    research_frame = (
        sweep_module
        ._load_train_validation_frame(
            trainer=trainer,
            snapshot=snapshot,
        )
    )

    identity = (
        _dataset_identity(
            research_frame
        )
    )

    purge_policy = (
        _resolve_internal_purge_rows(
            snapshot=snapshot,
            research_frame=research_frame,
        )
    )

    purge_rows = int(
        purge_policy[
            "purge_rows"
        ]
    )

    features = list(
        snapshot.feature_columns
    )

    train = (
        research_frame.loc[
            research_frame[
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
        research_frame.loc[
            research_frame[
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
            "TEMPORAL_REQUIRED_SPLIT_EMPTY"
        )

    if (
        len(
            train
        )
        !=
        int(
            sweep_module
            .EXPECTED_TRAIN_ROWS
        )
    ):
        raise RuntimeError(
            (
                "TEMPORAL_TRAIN_ROW_COUNT_MISMATCH: "
                f"{len(train)}"
            )
        )

    if (
        len(
            validation
        )
        !=
        int(
            sweep_module
            .EXPECTED_VALIDATION_ROWS
        )
    ):
        raise RuntimeError(
            (
                "TEMPORAL_VALIDATION_ROW_COUNT_MISMATCH: "
                f"{len(validation)}"
            )
        )

    train_time = (
        _decision_time_series(
            train
        )
    )

    validation_time = (
        _decision_time_series(
            validation
        )
    )

    if (
        train_time
        is not None
        and
        validation_time
        is not None
        and
        train_time.iloc[
            -1
        ]
        >=
        validation_time.iloc[
            0
        ]
    ):
        raise RuntimeError(
            "TRAIN_VALIDATION_TIME_ORDER_MISMATCH"
        )

    reference_candidates = (
        _reference_candidates()
    )

    x_train_all = (
        train[
            features
        ]
        .to_numpy(
            dtype=np.float64
        )
    )

    y_train_all = (
        train[
            "target_class_id"
        ]
        .to_numpy(
            dtype=np.int8
        )
    )

    _require_finite_matrix(
        x_train_all,
        name="FULL_TRAIN_RAW",
    )

    walk_forward_records: dict[
        str,
        list[dict[str, Any]],
    ] = {
        name: []
        for name
        in REFERENCE_CANDIDATE_NAMES
    }

    walk_plan = (
        _walk_forward_plan(
            rows=len(
                train
            ),
            purge_rows=(
                purge_rows
            ),
        )
    )

    fold_plan_output: list[
        dict[str, Any]
    ] = []

    for fold in walk_plan:

        fit_frame = (
            train.iloc[
                fold[
                    "fit_start"
                ]
                :
                fold[
                    "fit_end_exclusive"
                ]
            ]
            .reset_index(
                drop=True
            )
        )

        evaluation_frame = (
            train.iloc[
                fold[
                    "evaluation_start"
                ]
                :
                fold[
                    "evaluation_end_exclusive"
                ]
            ]
            .reset_index(
                drop=True
            )
        )

        x_fit_raw = (
            fit_frame[
                features
            ]
            .to_numpy(
                dtype=np.float64
            )
        )

        y_fit = (
            fit_frame[
                "target_class_id"
            ]
            .to_numpy(
                dtype=np.int8
            )
        )

        fit_bundle = (
            _fit_stage_a_and_scalers(
                trainer=trainer,
                x_fit_raw=(
                    x_fit_raw
                ),
                y_fit=(
                    y_fit
                ),
            )
        )

        fold_plan_output.append(
            {
                **fold,
                "fit_rows": int(
                    len(
                        fit_frame
                    )
                ),
                "fit_tradeable_rows": int(
                    np.sum(
                        y_fit
                        !=
                        0
                    )
                ),
                "purged_rows": int(
                    fold[
                        "purge_end_exclusive"
                    ]
                    -
                    fold[
                        "purge_start"
                    ]
                ),
                "evaluation_rows": int(
                    len(
                        evaluation_frame
                    )
                ),
                "evaluation_tradeable_rows": int(
                    np.sum(
                        evaluation_frame[
                            "target_class_id"
                        ]
                        .to_numpy(
                            dtype=np.int8
                        )
                        !=
                        0
                    )
                ),
                "fit_time_range": (
                    _time_range_document(
                        fit_frame
                    )
                ),
                "evaluation_time_range": (
                    _time_range_document(
                        evaluation_frame
                    )
                ),
            }
        )

        for (
            name,
            candidate,
        ) in (
            reference_candidates
            .items()
        ):

            stage_b_model = (
                _fit_stage_b_model(
                    trainer=trainer,
                    candidate=candidate,
                    fit_bundle=(
                        fit_bundle
                    ),
                )
            )

            raw_metrics = (
                _evaluate_frame(
                    trainer=trainer,
                    fit_bundle=(
                        fit_bundle
                    ),
                    stage_b_model=(
                        stage_b_model
                    ),
                    features=features,
                    frame=(
                        evaluation_frame
                    ),
                )
            )

            walk_forward_records[
                name
            ].append(
                {
                    "fold": int(
                        fold[
                            "fold"
                        ]
                    ),
                    "fit_rows": int(
                        len(
                            fit_frame
                        )
                    ),
                    "evaluation_rows": int(
                        len(
                            evaluation_frame
                        )
                    ),
                    "evaluation_time_range": (
                        _time_range_document(
                            evaluation_frame
                        )
                    ),
                    "metrics": (
                        _metrics_projection(
                            raw_metrics
                        )
                    ),
                }
            )

    full_fit_bundle = (
        _fit_stage_a_and_scalers(
            trainer=trainer,
            x_fit_raw=(
                x_train_all
            ),
            y_fit=(
                y_train_all
            ),
        )
    )

    validation_plan = (
        _validation_block_plan(
            rows=len(
                validation
            )
        )
    )

    validation_results: dict[
        str,
        Any,
    ] = {}

    for (
        name,
        candidate,
    ) in (
        reference_candidates
        .items()
    ):

        stage_b_model = (
            _fit_stage_b_model(
                trainer=trainer,
                candidate=candidate,
                fit_bundle=(
                    full_fit_bundle
                ),
            )
        )

        whole_validation_raw = (
            _evaluate_frame(
                trainer=trainer,
                fit_bundle=(
                    full_fit_bundle
                ),
                stage_b_model=(
                    stage_b_model
                ),
                features=features,
                frame=(
                    validation
                ),
            )
        )

        block_records: list[
            dict[str, Any]
        ] = []

        for block in validation_plan:

            block_frame = (
                validation.iloc[
                    block[
                        "start"
                    ]
                    :
                    block[
                        "end_exclusive"
                    ]
                ]
                .reset_index(
                    drop=True
                )
            )

            block_raw = (
                _evaluate_frame(
                    trainer=trainer,
                    fit_bundle=(
                        full_fit_bundle
                    ),
                    stage_b_model=(
                        stage_b_model
                    ),
                    features=features,
                    frame=(
                        block_frame
                    ),
                )
            )

            block_records.append(
                {
                    "block": int(
                        block[
                            "block"
                        ]
                    ),
                    "rows": int(
                        len(
                            block_frame
                        )
                    ),
                    "tradeable_rows": int(
                        np.sum(
                            block_frame[
                                "target_class_id"
                            ]
                            .to_numpy(
                                dtype=np.int8
                            )
                            !=
                            0
                        )
                    ),
                    "time_range": (
                        _time_range_document(
                            block_frame
                        )
                    ),
                    "metrics": (
                        _metrics_projection(
                            block_raw
                        )
                    ),
                }
            )

        validation_results[
            name
        ] = {
            "stage_b_parameters": (
                candidate
                .parameter_document()
            ),
            "whole_validation": (
                _metrics_projection(
                    whole_validation_raw
                )
            ),
            "temporal_blocks": (
                block_records
            ),
            "temporal_summary": (
                _temporal_summary(
                    block_records
                )
            ),
        }

    walk_forward_output = {
        name: {
            "stage_b_parameters": (
                reference_candidates[
                    name
                ]
                .parameter_document()
            ),
            "folds": (
                walk_forward_records[
                    name
                ]
            ),
            "temporal_summary": (
                _temporal_summary(
                    walk_forward_records[
                        name
                    ]
                )
            ),
        }
        for name
        in REFERENCE_CANDIDATE_NAMES
    }

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_V4_STAGE_B_"
            "TEMPORAL_ROBUSTNESS_ANALYSIS"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "research_lane": (
            "RESEARCH_LANE_2_XAUUSD_ML"
        ),
        "model_id": (
            "XAUUSD_MODEL_v4_HIERARCHICAL"
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
            "feature_count": int(
                len(
                    features
                )
            ),
            "dataset_path": str(
                snapshot.dataset_path
            ),
            "manifest_path": str(
                snapshot.manifest_path
            ),
        },
        "dataset_identity": (
            identity
        ),
        "active_mt5_runtime_identity": {
            "queried": False,
            "reason": (
                "TEMPORAL_RESEARCH_RUNNER_USES_"
                "FROZEN_DATASET_IDENTITY_ONLY"
            ),
        },
        "rows_used": {
            "TRAIN": int(
                len(
                    train
                )
            ),
            "VALIDATION": int(
                len(
                    validation
                )
            ),
            "TRAIN_TRADEABLE": int(
                np.sum(
                    y_train_all
                    !=
                    0
                )
            ),
            "VALIDATION_TRADEABLE": int(
                np.sum(
                    validation[
                        "target_class_id"
                    ]
                    .to_numpy(
                        dtype=np.int8
                    )
                    !=
                    0
                )
            ),
        },
        "time_ranges": {
            "TRAIN": (
                _time_range_document(
                    train
                )
            ),
            "VALIDATION": (
                _time_range_document(
                    validation
                )
            ),
        },
        "internal_purge_policy": (
            purge_policy
        ),
        "reference_candidates": list(
            REFERENCE_CANDIDATE_NAMES
        ),
        "scientific_policy": {
            "purpose": (
                "DIAGNOSTIC_TEMPORAL_ROBUSTNESS_ONLY"
            ),
            "new_hyperparameter_selection": False,
            "candidate_promotion": False,
            "stage_a_parameters_fixed": True,
            "stage_a_fit_scope": (
                "EACH_WALK_FORWARD_PREFIX_OR_FULL_TRAIN_ONLY"
            ),
            "stage_b_fit_scope": (
                "TRUE_TRADEABLE_ROWS_WITHIN_FIT_WINDOW_ONLY"
            ),
            "walk_forward_source": (
                "TRAIN_ONLY"
            ),
            "walk_forward_internal_boundary_purge": True,
            "external_evaluation_split": (
                "VALIDATION"
            ),
            "validation_used_for_new_tuning": False,
            "test_selected": False,
            "test_evaluated": False,
            "test_used_for_selection": False,
            "artifact_writes": False,
            "mt5_used": False,
            "live_authorized": False,
        },
        "walk_forward_train": {
            "evaluation_fold_count": int(
                WALK_FORWARD_EVALUATION_FOLDS
            ),
            "fold_plan": (
                fold_plan_output
            ),
            "candidates": (
                walk_forward_output
            ),
        },
        "external_validation": {
            "fit_scope": (
                "FULL_TRAIN"
            ),
            "temporal_block_count": int(
                VALIDATION_BLOCKS
            ),
            "candidates": (
                validation_results
            ),
        },
        "next_decision_contract": {
            "do_not_choose_a_new_model_from_this_analysis": True,
            "inspect": [
                "stage_b_balanced_accuracy_by_time",
                "stage_b_macro_f1_by_time",
                "SHORT_recall_and_f1_by_time",
                "LONG_recall_and_f1_by_time",
                "SHORT_LONG_recall_imbalance",
                "combined_macro_f1_by_time",
                "predicted_trade_coverage_by_time",
                "calibration_by_time",
            ],
            "if_directional_performance_is_near_random_or_unstable": (
                "NEXT_GATE_STAGE_B_FEATURE_STABILITY_AND_REDUCTION"
            ),
            "if_a_repeatable_temporal_edge_is_visible": (
                "NEXT_GATE_LOCALIZE_STABLE_FEATURE_FAMILIES_OR_REGIMES"
            ),
        },
        "live_authorized": False,
    }


def main() -> int:

    try:

        result = (
            run_analysis()
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_V4_STAGE_B_"
                        "TEMPORAL_ROBUSTNESS_ANALYSIS_FAILED"
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