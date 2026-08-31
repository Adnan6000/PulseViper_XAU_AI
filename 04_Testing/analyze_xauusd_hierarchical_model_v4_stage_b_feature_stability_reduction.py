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


ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


sweep_module: Any = importlib.import_module(
    "04_Testing.tune_xauusd_hierarchical_model_v4_stage_b"
)

temporal_module: Any = importlib.import_module(
    "04_Testing.analyze_xauusd_hierarchical_model_v4_stage_b_temporal_robustness"
)

trainer_module: Any = importlib.import_module(
    "02_AI.Models.xauusd_hierarchical_model_v4_trainer"
)


XAUUSDHierarchicalModelV4Trainer: Any = (
    trainer_module.XAUUSDHierarchicalModelV4Trainer
)

STAGE_B_CLASS_IDS = (
    trainer_module.STAGE_B_CLASS_IDS
)

STAGE_B_CLASS_NAMES = (
    trainer_module.STAGE_B_CLASS_NAMES
)


ANALYSIS_VERSION = (
    "XAUUSD_V4_STAGE_B_FEATURE_STABILITY_REDUCTION_V1"
)

REFERENCE_STAGE_B_CANDIDATE_NAME = (
    "baseline_v4"
)

FEATURE_STABILITY_BLOCKS = 3

FEATURE_COUNTS = (
    32,
    64,
    128,
    192,
    333,
)

TOP_FEATURES_TO_REPORT = 50

RANDOM_STATE = int(
    sweep_module.RANDOM_STATE
)

STAGE_B_CLASS_BALANCE_POWER = float(
    sweep_module.STAGE_B_CLASS_BALANCE_POWER
)


@dataclass(frozen=True)
class FeatureStabilityRecord:

    feature: str

    stability_score: float

    mean_signed_correlation: float

    mean_absolute_correlation: float

    min_absolute_correlation: float

    std_signed_correlation: float

    sign_consistency: float

    positive_blocks: int

    negative_blocks: int

    zero_blocks: int

    polarity_flips: int

    block_correlations: tuple[
        float,
        ...,
    ]

    def document(
        self,
    ) -> dict[str, Any]:

        return {
            "feature": (
                self.feature
            ),
            "stability_score": (
                self.stability_score
            ),
            "mean_signed_correlation": (
                self.mean_signed_correlation
            ),
            "mean_absolute_correlation": (
                self.mean_absolute_correlation
            ),
            "min_absolute_correlation": (
                self.min_absolute_correlation
            ),
            "std_signed_correlation": (
                self.std_signed_correlation
            ),
            "sign_consistency": (
                self.sign_consistency
            ),
            "positive_blocks": (
                self.positive_blocks
            ),
            "negative_blocks": (
                self.negative_blocks
            ),
            "zero_blocks": (
                self.zero_blocks
            ),
            "polarity_flips": (
                self.polarity_flips
            ),
            "block_correlations": list(
                self.block_correlations
            ),
        }


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
            (
                "NONFINITE_FEATURE_STABILITY_VALUE: "
                f"{name}"
            )
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
            (
                "NONFINITE_FEATURE_STABILITY_MATRIX: "
                f"{name}"
            )
        )


def _sha256_strings(
    values: list[str],
) -> str:

    payload = (
        "\n"
        .join(
            values
        )
        .encode(
            "utf-8"
        )
    )

    return (
        hashlib
        .sha256(
            payload
        )
        .hexdigest()
    )


def _reference_candidate(
) -> Any:

    for candidate in (
        sweep_module.CANDIDATES
    ):

        if (
            candidate.name
            ==
            REFERENCE_STAGE_B_CANDIDATE_NAME
        ):
            return candidate

    raise RuntimeError(
        "REFERENCE_STAGE_B_CANDIDATE_MISSING"
    )


def _tradeable_frame(
    frame: pd.DataFrame,
) -> pd.DataFrame:

    result = (
        frame.loc[
            frame[
                "target_class_id"
            ]
            !=
            0
        ]
        .reset_index(
            drop=True
        )
    )

    if result.empty:
        raise RuntimeError(
            "TRADEABLE_FRAME_EMPTY"
        )

    classes = {
        int(
            value
        )
        for value
        in result[
            "target_class_id"
        ].unique()
    }

    if classes != {
        -1,
        1,
    }:

        raise RuntimeError(
            (
                "TRADEABLE_DIRECTION_CLASS_CONTRACT_MISMATCH: "
                f"{sorted(classes)}"
            )
        )

    return result


def _chronological_blocks(
    frame: pd.DataFrame,
    block_count: int,
) -> list[pd.DataFrame]:

    if block_count < 2:
        raise RuntimeError(
            "FEATURE_STABILITY_BLOCK_COUNT_TOO_SMALL"
        )

    if (
        len(
            frame
        )
        <
        block_count
        *
        100
    ):
        raise RuntimeError(
            "INSUFFICIENT_ROWS_FOR_FEATURE_STABILITY_BLOCKS"
        )

    boundaries = np.linspace(
        0,
        len(
            frame
        ),
        block_count
        +
        1,
        dtype=int,
    )

    blocks: list[
        pd.DataFrame
    ] = []

    for index in range(
        block_count
    ):

        start = int(
            boundaries[
                index
            ]
        )

        end = int(
            boundaries[
                index
                +
                1
            ]
        )

        block = (
            frame.iloc[
                start:end
            ]
            .reset_index(
                drop=True
            )
        )

        if block.empty:
            raise RuntimeError(
                "EMPTY_FEATURE_STABILITY_BLOCK"
            )

        blocks.append(
            block
        )

    return blocks


def _signed_point_biserial_correlations(
    block: pd.DataFrame,
    features: list[str],
) -> np.ndarray:

    x = (
        block[
            features
        ]
        .to_numpy(
            dtype=np.float64
        )
    )

    y = (
        block[
            "target_class_id"
        ]
        .to_numpy(
            dtype=np.float64
        )
    )

    _require_finite_matrix(
        x,
        name=(
            "FEATURE_STABILITY_BLOCK_X"
        ),
    )

    _require_finite_matrix(
        y,
        name=(
            "FEATURE_STABILITY_BLOCK_Y"
        ),
    )

    x_centered = (
        x
        -
        np.mean(
            x,
            axis=0,
            keepdims=True,
        )
    )

    y_centered = (
        y
        -
        np.mean(
            y
        )
    )

    numerator = np.sum(
        x_centered
        *
        y_centered[
            :,
            None,
        ],
        axis=0,
    )

    denominator = np.sqrt(
        np.sum(
            x_centered
            *
            x_centered,
            axis=0,
        )
        *
        np.sum(
            y_centered
            *
            y_centered
        )
    )

    correlations = np.zeros(
        len(
            features
        ),
        dtype=np.float64,
    )

    valid = (
        denominator
        >
        0.0
    )

    correlations[
        valid
    ] = (
        numerator[
            valid
        ]
        /
        denominator[
            valid
        ]
    )

    correlations = np.clip(
        correlations,
        -1.0,
        1.0,
    )

    _require_finite_matrix(
        correlations,
        name=(
            "FEATURE_STABILITY_CORRELATIONS"
        ),
    )

    return correlations


def _polarity_flips(
    values: np.ndarray,
) -> int:

    signs = np.sign(
        values
    )

    nonzero = signs[
        signs
        !=
        0.0
    ]

    if (
        nonzero.size
        <=
        1
    ):
        return 0

    return int(
        np.sum(
            nonzero[
                1:
            ]
            !=
            nonzero[
                :-1
            ]
        )
    )


def _feature_stability_ranking(
    frame: pd.DataFrame,
    features: list[str],
) -> list[
    FeatureStabilityRecord
]:

    tradeable = (
        _tradeable_frame(
            frame
        )
    )

    blocks = (
        _chronological_blocks(
            tradeable,
            FEATURE_STABILITY_BLOCKS,
        )
    )

    block_values = np.vstack(
        [
            _signed_point_biserial_correlations(
                block,
                features,
            )
            for block
            in blocks
        ]
    )

    records: list[
        FeatureStabilityRecord
    ] = []

    for (
        feature_index,
        feature,
    ) in enumerate(
        features
    ):

        values = (
            block_values[
                :,
                feature_index,
            ]
        )

        positive = int(
            np.sum(
                values
                >
                0.0
            )
        )

        negative = int(
            np.sum(
                values
                <
                0.0
            )
        )

        zero = int(
            np.sum(
                values
                ==
                0.0
            )
        )

        sign_consistency = float(
            max(
                positive,
                negative,
            )
            /
            FEATURE_STABILITY_BLOCKS
        )

        mean_signed = float(
            np.mean(
                values
            )
        )

        mean_abs = float(
            np.mean(
                np.abs(
                    values
                )
            )
        )

        min_abs = float(
            np.min(
                np.abs(
                    values
                )
            )
        )

        std_signed = float(
            np.std(
                values
            )
        )

        stability_score = float(
            abs(
                mean_signed
            )
            *
            sign_consistency
            /
            (
                1.0
                +
                (
                    5.0
                    *
                    std_signed
                )
            )
        )

        records.append(
            FeatureStabilityRecord(
                feature=(
                    feature
                ),
                stability_score=(
                    stability_score
                ),
                mean_signed_correlation=(
                    mean_signed
                ),
                mean_absolute_correlation=(
                    mean_abs
                ),
                min_absolute_correlation=(
                    min_abs
                ),
                std_signed_correlation=(
                    std_signed
                ),
                sign_consistency=(
                    sign_consistency
                ),
                positive_blocks=(
                    positive
                ),
                negative_blocks=(
                    negative
                ),
                zero_blocks=(
                    zero
                ),
                polarity_flips=(
                    _polarity_flips(
                        values
                    )
                ),
                block_correlations=tuple(
                    float(
                        value
                    )
                    for value
                    in values
                ),
            )
        )

    records.sort(
        key=lambda record: (
            record.stability_score,
            record.sign_consistency,
            abs(
                record.mean_signed_correlation
            ),
            record.min_absolute_correlation,
            record.mean_absolute_correlation,
            -record.std_signed_correlation,
            record.feature,
        ),
        reverse=True,
    )

    return records


def _selected_features(
    ranking: list[
        FeatureStabilityRecord
    ],
    all_features: list[str],
    feature_count: int,
) -> list[str]:

    if (
        feature_count
        >=
        len(
            all_features
        )
    ):
        return list(
            all_features
        )

    selected = [
        record.feature
        for record
        in ranking[
            :feature_count
        ]
    ]

    if (
        len(
            selected
        )
        !=
        feature_count
        or
        len(
            set(
                selected
            )
        )
        !=
        feature_count
    ):

        raise RuntimeError(
            "INVALID_SELECTED_FEATURE_SUBSET"
        )

    return selected


def _fit_stage_b(
    *,
    trainer: Any,
    candidate: Any,
    fit_frame: pd.DataFrame,
    selected_features: list[str],
) -> tuple[
    Any,
    StandardScaler,
]:

    tradeable = (
        _tradeable_frame(
            fit_frame
        )
    )

    x = (
        tradeable[
            selected_features
        ]
        .to_numpy(
            dtype=np.float64
        )
    )

    y = (
        tradeable[
            "target_class_id"
        ]
        .to_numpy(
            dtype=np.int8
        )
    )

    _require_finite_matrix(
        x,
        name=(
            "STAGE_B_SUBSET_FIT_X"
        ),
    )

    scaler = StandardScaler(
        copy=True,
        with_mean=True,
        with_std=True,
    )

    x_scaled = (
        scaler
        .fit_transform(
            x
        )
    )

    _require_finite_matrix(
        x_scaled,
        name=(
            "STAGE_B_SUBSET_FIT_SCALED"
        ),
    )

    (
        sample_weights,
        _class_weights,
    ) = (
        trainer
        ._binary_sample_weights(
            y,
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
        x_scaled,
        y,
        sample_weight=(
            sample_weights
        ),
    )

    trainer._require_model_classes(
        model,
        STAGE_B_CLASS_IDS,
        (
            "FEATURE_REDUCTION_STAGE_B_"
            "MODEL_CLASS_ORDER_MISMATCH"
        ),
    )

    return (
        model,
        scaler,
    )


def _evaluate_subset(
    *,
    trainer: Any,
    stage_a_bundle: dict[str, Any],
    stage_b_model: Any,
    stage_b_scaler: StandardScaler,
    all_features: list[str],
    selected_features: list[str],
    frame: pd.DataFrame,
) -> dict[str, Any]:

    x_stage_a_raw = (
        frame[
            all_features
        ]
        .to_numpy(
            dtype=np.float64
        )
    )

    x_stage_b_raw = (
        frame[
            selected_features
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
        x_stage_a_raw,
        name=(
            "STAGE_A_SUBSET_EVAL_RAW"
        ),
    )

    _require_finite_matrix(
        x_stage_b_raw,
        name=(
            "STAGE_B_SUBSET_EVAL_RAW"
        ),
    )

    x_stage_a = (
        stage_a_bundle[
            "stage_a_scaler"
        ]
        .transform(
            x_stage_a_raw
        )
    )

    x_stage_b = (
        stage_b_scaler
        .transform(
            x_stage_b_raw
        )
    )

    _require_finite_matrix(
        x_stage_a,
        name=(
            "STAGE_A_SUBSET_EVAL"
        ),
    )

    _require_finite_matrix(
        x_stage_b,
        name=(
            "STAGE_B_SUBSET_EVAL"
        ),
    )

    raw_metrics = (
        trainer
        ._evaluate_split(
            stage_a_model=(
                stage_a_bundle[
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

    return (
        temporal_module
        ._metrics_projection(
            raw_metrics
        )
    )


def _metric(
    records: list[
        dict[str, Any]
    ],
    path: tuple[
        str,
        ...,
    ],
) -> np.ndarray:

    values: list[
        float
    ] = []

    for record in records:

        value: Any = (
            record[
                "metrics"
            ]
        )

        for key in path:
            value = (
                value[
                    key
                ]
            )

        values.append(
            _finite_float(
                value,
                name=(
                    ".".join(
                        path
                    )
                ),
            )
        )

    return np.asarray(
        values,
        dtype=np.float64,
    )


def _summary(
    records: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:

    stage_b_ba = (
        _metric(
            records,
            (
                "stage_b",
                "balanced_accuracy",
            ),
        )
    )

    stage_b_macro = (
        _metric(
            records,
            (
                "stage_b",
                "macro_f1",
            ),
        )
    )

    short_recall = (
        _metric(
            records,
            (
                "stage_b",
                "short",
                "recall",
            ),
        )
    )

    long_recall = (
        _metric(
            records,
            (
                "stage_b",
                "long",
                "recall",
            ),
        )
    )

    combined_macro = (
        _metric(
            records,
            (
                "combined",
                "macro_f1",
            ),
        )
    )

    coverage = (
        _metric(
            records,
            (
                "combined",
                "predicted_trade_coverage",
            ),
        )
    )

    recall_gap = np.abs(
        short_recall
        -
        long_recall
    )

    return {
        "fold_count": int(
            len(
                records
            )
        ),
        "stage_b_balanced_accuracy": {
            "mean": float(
                np.mean(
                    stage_b_ba
                )
            ),
            "std": float(
                np.std(
                    stage_b_ba
                )
            ),
            "min": float(
                np.min(
                    stage_b_ba
                )
            ),
            "max": float(
                np.max(
                    stage_b_ba
                )
            ),
            "above_0_50_folds": int(
                np.sum(
                    stage_b_ba
                    >
                    0.50
                )
            ),
            "at_or_below_0_50_folds": int(
                np.sum(
                    stage_b_ba
                    <=
                    0.50
                )
            ),
        },
        "stage_b_macro_f1_mean": float(
            np.mean(
                stage_b_macro
            )
        ),
        "stage_b_short_recall_mean": float(
            np.mean(
                short_recall
            )
        ),
        "stage_b_long_recall_mean": float(
            np.mean(
                long_recall
            )
        ),
        "stage_b_short_long_recall_gap_mean": float(
            np.mean(
                recall_gap
            )
        ),
        "stage_b_short_long_recall_gap_max": float(
            np.max(
                recall_gap
            )
        ),
        "combined_macro_f1_mean": float(
            np.mean(
                combined_macro
            )
        ),
        "combined_predicted_trade_coverage_mean": float(
            np.mean(
                coverage
            )
        ),
    }


def _selection_key(
    summary: dict[str, Any],
) -> tuple[
    float,
    float,
    float,
    float,
    float,
]:

    ba = (
        summary[
            "stage_b_balanced_accuracy"
        ]
    )

    return (
        float(
            ba[
                "mean"
            ]
        ),
        float(
            ba[
                "min"
            ]
        ),
        float(
            summary[
                "stage_b_macro_f1_mean"
            ]
        ),
        -float(
            summary[
                "stage_b_short_long_recall_gap_mean"
            ]
        ),
        float(
            summary[
                "combined_macro_f1_mean"
            ]
        ),
    )


def _candidate_key(
    feature_count: int,
) -> str:

    if feature_count < 333:
        return (
            f"top_{feature_count}"
        )

    return "full_333"


def _validation_delta(
    selected: dict[str, Any],
    baseline: dict[str, Any],
) -> dict[str, Any]:

    return {
        "stage_b_balanced_accuracy": (
            float(
                selected[
                    "stage_b"
                ][
                    "balanced_accuracy"
                ]
            )
            -
            float(
                baseline[
                    "stage_b"
                ][
                    "balanced_accuracy"
                ]
            )
        ),
        "stage_b_macro_f1": (
            float(
                selected[
                    "stage_b"
                ][
                    "macro_f1"
                ]
            )
            -
            float(
                baseline[
                    "stage_b"
                ][
                    "macro_f1"
                ]
            )
        ),
        "stage_b_short_recall": (
            float(
                selected[
                    "stage_b"
                ][
                    "short"
                ][
                    "recall"
                ]
            )
            -
            float(
                baseline[
                    "stage_b"
                ][
                    "short"
                ][
                    "recall"
                ]
            )
        ),
        "stage_b_long_recall": (
            float(
                selected[
                    "stage_b"
                ][
                    "long"
                ][
                    "recall"
                ]
            )
            -
            float(
                baseline[
                    "stage_b"
                ][
                    "long"
                ][
                    "recall"
                ]
            )
        ),
        "combined_macro_f1": (
            float(
                selected[
                    "combined"
                ][
                    "macro_f1"
                ]
            )
            -
            float(
                baseline[
                    "combined"
                ][
                    "macro_f1"
                ]
            )
        ),
        "combined_balanced_accuracy": (
            float(
                selected[
                    "combined"
                ][
                    "balanced_accuracy"
                ]
            )
            -
            float(
                baseline[
                    "combined"
                ][
                    "balanced_accuracy"
                ]
            )
        ),
        "combined_predicted_trade_coverage": (
            float(
                selected[
                    "combined"
                ][
                    "predicted_trade_coverage"
                ]
            )
            -
            float(
                baseline[
                    "combined"
                ][
                    "predicted_trade_coverage"
                ]
            )
        ),
    }


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

    all_features = list(
        snapshot.feature_columns
    )

    if (
        len(
            all_features
        )
        !=
        333
    ):
        raise RuntimeError(
            (
                "FEATURE_COUNT_MISMATCH: "
                f"{len(all_features)}"
            )
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
                "TRAIN_ROW_COUNT_MISMATCH: "
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
                "VALIDATION_ROW_COUNT_MISMATCH: "
                f"{len(validation)}"
            )
        )

    identity = (
        temporal_module
        ._dataset_identity(
            research_frame
        )
    )

    purge_policy = (
        temporal_module
        ._resolve_internal_purge_rows(
            snapshot=snapshot,
            research_frame=(
                research_frame
            ),
        )
    )

    purge_rows = int(
        purge_policy[
            "purge_rows"
        ]
    )

    walk_plan = (
        temporal_module
        ._walk_forward_plan(
            rows=len(
                train
            ),
            purge_rows=(
                purge_rows
            ),
        )
    )

    candidate = (
        _reference_candidate()
    )

    walk_records: dict[
        str,
        list[
            dict[str, Any]
        ],
    ] = {
        _candidate_key(
            count
        ): []
        for count
        in FEATURE_COUNTS
    }

    fold_feature_diagnostics: list[
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

        ranking = (
            _feature_stability_ranking(
                fit_frame,
                all_features,
            )
        )

        x_fit_raw = (
            fit_frame[
                all_features
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

        stage_a_bundle = (
            temporal_module
            ._fit_stage_a_and_scalers(
                trainer=trainer,
                x_fit_raw=(
                    x_fit_raw
                ),
                y_fit=(
                    y_fit
                ),
            )
        )

        fold_feature_diagnostics.append(
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
                "top_20_stable_features": [
                    record.document()
                    for record
                    in ranking[
                        :20
                    ]
                ],
            }
        )

        for feature_count in (
            FEATURE_COUNTS
        ):

            key = (
                _candidate_key(
                    feature_count
                )
            )

            selected = (
                _selected_features(
                    ranking,
                    all_features,
                    feature_count,
                )
            )

            (
                stage_b_model,
                stage_b_scaler,
            ) = (
                _fit_stage_b(
                    trainer=trainer,
                    candidate=candidate,
                    fit_frame=(
                        fit_frame
                    ),
                    selected_features=(
                        selected
                    ),
                )
            )

            metrics = (
                _evaluate_subset(
                    trainer=trainer,
                    stage_a_bundle=(
                        stage_a_bundle
                    ),
                    stage_b_model=(
                        stage_b_model
                    ),
                    stage_b_scaler=(
                        stage_b_scaler
                    ),
                    all_features=(
                        all_features
                    ),
                    selected_features=(
                        selected
                    ),
                    frame=(
                        evaluation_frame
                    ),
                )
            )

            walk_records[
                key
            ].append(
                {
                    "fold": int(
                        fold[
                            "fold"
                        ]
                    ),
                    "feature_count": int(
                        len(
                            selected
                        )
                    ),
                    "selected_features_sha256": (
                        _sha256_strings(
                            selected
                        )
                    ),
                    "top_20_selected_features": (
                        selected[
                            :20
                        ]
                    ),
                    "metrics": (
                        metrics
                    ),
                }
            )

    train_summaries: dict[
        str,
        dict[str, Any],
    ] = {
        key: (
            _summary(
                records
            )
        )
        for (
            key,
            records,
        )
        in walk_records.items()
    }

    ranked_keys = sorted(
        train_summaries,
        key=lambda key: (
            _selection_key(
                train_summaries[
                    key
                ]
            )
        ),
        reverse=True,
    )

    best_key = (
        ranked_keys[
            0
        ]
    )

    if (
        best_key
        ==
        "full_333"
    ):
        best_feature_count = 333

    else:
        best_feature_count = int(
            best_key.split(
                "_"
            )[
                1
            ]
        )

    full_train_ranking = (
        _feature_stability_ranking(
            train,
            all_features,
        )
    )

    final_selected_features = (
        _selected_features(
            full_train_ranking,
            all_features,
            best_feature_count,
        )
    )

    full_train_x = (
        train[
            all_features
        ]
        .to_numpy(
            dtype=np.float64
        )
    )

    full_train_y = (
        train[
            "target_class_id"
        ]
        .to_numpy(
            dtype=np.int8
        )
    )

    full_stage_a_bundle = (
        temporal_module
        ._fit_stage_a_and_scalers(
            trainer=trainer,
            x_fit_raw=(
                full_train_x
            ),
            y_fit=(
                full_train_y
            ),
        )
    )

    (
        selected_stage_b_model,
        selected_stage_b_scaler,
    ) = (
        _fit_stage_b(
            trainer=trainer,
            candidate=candidate,
            fit_frame=train,
            selected_features=(
                final_selected_features
            ),
        )
    )

    selected_validation = (
        _evaluate_subset(
            trainer=trainer,
            stage_a_bundle=(
                full_stage_a_bundle
            ),
            stage_b_model=(
                selected_stage_b_model
            ),
            stage_b_scaler=(
                selected_stage_b_scaler
            ),
            all_features=(
                all_features
            ),
            selected_features=(
                final_selected_features
            ),
            frame=validation,
        )
    )

    (
        baseline_stage_b_model,
        baseline_stage_b_scaler,
    ) = (
        _fit_stage_b(
            trainer=trainer,
            candidate=candidate,
            fit_frame=train,
            selected_features=(
                all_features
            ),
        )
    )

    baseline_validation = (
        _evaluate_subset(
            trainer=trainer,
            stage_a_bundle=(
                full_stage_a_bundle
            ),
            stage_b_model=(
                baseline_stage_b_model
            ),
            stage_b_scaler=(
                baseline_stage_b_scaler
            ),
            all_features=(
                all_features
            ),
            selected_features=(
                all_features
            ),
            frame=validation,
        )
    )

    baseline_summary = (
        train_summaries[
            "full_333"
        ]
    )

    selected_summary = (
        train_summaries[
            best_key
        ]
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_V4_STAGE_B_"
            "FEATURE_STABILITY_REDUCTION_ANALYSIS"
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
            "feature_count": (
                len(
                    all_features
                )
            ),
        },
        "dataset_identity": (
            identity
        ),
        "active_mt5_runtime_identity": {
            "queried": False,
            "reason": (
                "FEATURE_RESEARCH_USES_"
                "FROZEN_DATASET_IDENTITY_ONLY"
            ),
        },
        "scientific_policy": {
            "purpose": (
                "STAGE_B_FEATURE_STABILITY_AND_REDUCTION"
            ),
            "feature_ranking_source": (
                "FIT_PREFIX_TRAIN_ONLY_PER_WALK_FORWARD_FOLD"
            ),
            "feature_count_selection_source": (
                "TRAIN_WALK_FORWARD_ONLY"
            ),
            "external_confirmation_split": (
                "VALIDATION"
            ),
            "validation_used_for_feature_count_selection": (
                False
            ),
            "test_evaluated": False,
            "test_selected": False,
            "artifact_writes": False,
            "mt5_used": False,
            "stage_a_feature_count": 333,
            "stage_a_parameters_fixed": True,
            "stage_b_hyperparameters_fixed": (
                REFERENCE_STAGE_B_CANDIDATE_NAME
            ),
            "live_authorized": False,
        },
        "feature_stability_method": {
            "method": (
                "CHRONOLOGICAL_BLOCK_"
                "SIGNED_POINT_BISERIAL_CORRELATION"
            ),
            "blocks_within_each_fit_prefix": (
                FEATURE_STABILITY_BLOCKS
            ),
            "ranking_score": (
                "abs(mean_signed_correlation) * "
                "sign_consistency / "
                "(1 + 5 * std_signed_correlation)"
            ),
            "interpretation": (
                "Higher score favors directional features "
                "with stronger, same-sign, lower-dispersion "
                "relationships across time."
            ),
        },
        "fixed_stage_b_parameters": (
            candidate
            .parameter_document()
        ),
        "candidate_feature_counts": list(
            FEATURE_COUNTS
        ),
        "train_walk_forward": {
            "candidate_ranking": (
                ranked_keys
            ),
            "best_feature_count_by_train_policy": (
                best_feature_count
            ),
            "selection_policy": [
                (
                    "stage_b_balanced_accuracy_mean_max"
                ),
                (
                    "stage_b_balanced_accuracy_min_max"
                ),
                (
                    "stage_b_macro_f1_mean_max"
                ),
                (
                    "stage_b_short_long_recall_gap_mean_min"
                ),
                (
                    "combined_macro_f1_mean_max"
                ),
            ],
            "candidates": {
                key: {
                    "summary": (
                        train_summaries[
                            key
                        ]
                    ),
                    "folds": (
                        walk_records[
                            key
                        ]
                    ),
                }
                for key
                in ranked_keys
            },
            "selected_vs_full_333_train_summary_delta": {
                "stage_b_balanced_accuracy_mean": (
                    float(
                        selected_summary[
                            "stage_b_balanced_accuracy"
                        ][
                            "mean"
                        ]
                    )
                    -
                    float(
                        baseline_summary[
                            "stage_b_balanced_accuracy"
                        ][
                            "mean"
                        ]
                    )
                ),
                "stage_b_balanced_accuracy_min": (
                    float(
                        selected_summary[
                            "stage_b_balanced_accuracy"
                        ][
                            "min"
                        ]
                    )
                    -
                    float(
                        baseline_summary[
                            "stage_b_balanced_accuracy"
                        ][
                            "min"
                        ]
                    )
                ),
                "stage_b_macro_f1_mean": (
                    float(
                        selected_summary[
                            "stage_b_macro_f1_mean"
                        ]
                    )
                    -
                    float(
                        baseline_summary[
                            "stage_b_macro_f1_mean"
                        ]
                    )
                ),
                "stage_b_short_long_recall_gap_mean": (
                    float(
                        selected_summary[
                            "stage_b_short_long_recall_gap_mean"
                        ]
                    )
                    -
                    float(
                        baseline_summary[
                            "stage_b_short_long_recall_gap_mean"
                        ]
                    )
                ),
                "combined_macro_f1_mean": (
                    float(
                        selected_summary[
                            "combined_macro_f1_mean"
                        ]
                    )
                    -
                    float(
                        baseline_summary[
                            "combined_macro_f1_mean"
                        ]
                    )
                ),
            },
            "fold_feature_diagnostics": (
                fold_feature_diagnostics
            ),
        },
        "full_train_feature_stability": {
            "selected_feature_count": (
                len(
                    final_selected_features
                )
            ),
            "selected_features_sha256": (
                _sha256_strings(
                    final_selected_features
                )
            ),
            "selected_features": (
                final_selected_features
            ),
            "top_stable_features": [
                record.document()
                for record
                in full_train_ranking[
                    :TOP_FEATURES_TO_REPORT
                ]
            ],
        },
        "external_validation_confirmation": {
            "baseline_full_333": (
                baseline_validation
            ),
            "selected_train_only_feature_subset": (
                selected_validation
            ),
            "selected_minus_baseline_delta": (
                _validation_delta(
                    selected_validation,
                    baseline_validation,
                )
            ),
            "validation_used_for_selection": False,
        },
        "next_decision_contract": {
            "do_not_run_test_from_this_script": True,
            "clear_feature_reduction_candidate_requires": [
                (
                    "TRAIN walk-forward Stage-B "
                    "balanced accuracy improvement"
                ),
                (
                    "no material deterioration "
                    "in worst TRAIN fold"
                ),
                (
                    "smaller or non-worse "
                    "SHORT/LONG recall imbalance"
                ),
                (
                    "external VALIDATION directional metrics "
                    "confirm rather than reverse the improvement"
                ),
                (
                    "combined validation macro-F1 "
                    "does not materially deteriorate"
                ),
            ],
            "if_clear_reduced_subset_wins": (
                "FREEZE_FEATURE_SUBSET_BEFORE_"
                "ONE_FINAL_TEST_EVALUATION"
            ),
            "if_no_clear_reduced_subset_wins": (
                "STOP_V4_CAPACITY_FEATURE_TUNING_"
                "AND_REVISIT_DIRECTION_TARGET_OR_REGIME_DESIGN"
            ),
        },
        "internal_purge_policy": (
            purge_policy
        ),
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
                        "FEATURE_STABILITY_REDUCTION_FAILED"
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