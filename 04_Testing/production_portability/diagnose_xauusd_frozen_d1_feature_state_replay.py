from __future__ import annotations

import importlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


ANALYSIS_VERSION = (
    "XAUUSD_FROZEN_D1_FEATURE_STATE_REPLAY_V1"
)

FULL_AUDIT_MODULE = (
    "04_Testing."
    "analyze_xauusd_current_broker_full_mtf_portability"
)

FROZEN_D1_SOURCE_MODULE = (
    "04_Testing."
    "diagnose_xauusd_frozen_d1_source_aggregation"
)


full: Any = importlib.import_module(
    FULL_AUDIT_MODULE
)

source: Any = importlib.import_module(
    FROZEN_D1_SOURCE_MODULE
)

base: Any = (
    full.base
)

TrainingMatrixBuilder: Any = (
    full.TrainingMatrixBuilder
)


CANONICAL_ROOT = (
    full.CANONICAL_ROOT
)

CANONICAL_DATETIME_DTYPE = (
    full.CANONICAL_DATETIME_DTYPE
)


CANDIDATE_AVAILABILITY_SHIFT_DAYS = (
    -2,
    -1,
    0,
    1,
    2,
)


MIN_PAIRED_D1_STATES = 200

EXACT_ABSOLUTE_TOLERANCE = 1e-6

CONFIRMED_MIN_EXACT_FEATURE_COUNT = 40

CONFIRMED_MIN_MEDIAN_EXACT_MATCH_FRACTION = 0.999

CONFIRMED_MAX_MEDIAN_NORMALIZED_MAE = 1e-6


LIKELY_MIN_EXACT_FEATURE_COUNT = 35

LIKELY_MIN_MEDIAN_EXACT_MATCH_FRACTION = 0.99

LIKELY_MAX_MEDIAN_NORMALIZED_MAE = 1e-3


def _require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise RuntimeError(
            reason
        )


def _safe_float(
    value: Any,
) -> float | None:

    try:
        result = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):
        return None

    if not math.isfinite(
        result
    ):
        return None

    return result


def _median_finite(
    values: Sequence[
        float | None
    ],
) -> float | None:

    finite = [
        float(
            value
        )
        for value
        in values
        if (
            value is not None
            and
            math.isfinite(
                float(
                    value
                )
            )
        )
    ]

    if not finite:
        return None

    return float(
        np.median(
            np.asarray(
                finite,
                dtype=np.float64,
            )
        )
    )


def _canonical_time(
    values: pd.Series,
) -> pd.Series:

    converted = pd.to_datetime(
        values,
        utc=True,
        errors="raise",
    )

    result = converted.astype(
        CANONICAL_DATETIME_DTYPE
    )

    _require(
        str(
            result.dtype
        )
        ==
        CANONICAL_DATETIME_DTYPE,
        (
            "DATETIME_DTYPE_NOT_CANONICAL:"
            f"{result.dtype}"
        ),
    )

    return (
        result
    )


def _correlation(
    left: np.ndarray,
    right: np.ndarray,
) -> float | None:

    _require(
        left.shape
        ==
        right.shape,
        (
            "CORRELATION_SHAPE_MISMATCH:"
            f"{left.shape}:"
            f"{right.shape}"
        ),
    )

    finite = (
        np.isfinite(
            left
        )
        &
        np.isfinite(
            right
        )
    )

    if (
        int(
            finite.sum()
        )
        <
        3
    ):

        return None

    x = (
        left[
            finite
        ]
    )

    y = (
        right[
            finite
        ]
    )

    x_std = float(
        np.std(
            x
        )
    )

    y_std = float(
        np.std(
            y
        )
    )

    if (
        x_std
        <=
        1e-15
        or
        y_std
        <=
        1e-15
    ):

        return None

    result = float(
        np.corrcoef(
            x,
            y,
        )[
            0,
            1
        ]
    )

    if not math.isfinite(
        result
    ):

        return None

    return (
        result
    )


def _technical_features(
    manifest: Mapping[
        str,
        Any,
    ],
) -> list[str]:

    base_feature_names = (
        base
        ._base_feature_names()
    )

    groups = (
        full
        ._feature_groups(
            manifest,
            base_feature_names,
        )
    )

    features = [
        str(
            feature
        )
        for feature
        in groups[
            "technical"
        ][
            "D1"
        ]
    ]

    _require(
        len(
            features
        )
        ==
        full.EXPECTED_TECHNICAL_COUNT_PER_TIMEFRAME,
        (
            "D1_TECHNICAL_FEATURE_COUNT_MISMATCH:"
            f"{len(features)}"
        ),
    )

    return (
        features
    )


def _frozen_d1_states(
    *,
    frozen_train: pd.DataFrame,
    technical_features: Sequence[
        str
    ],
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

    required_columns = {
        "decision_time",
        "d1_age_minutes",
        *technical_features,
    }

    missing = sorted(
        required_columns
        -
        set(
            str(
                column
            )
            for column
            in frozen_train.columns
        )
    )

    _require(
        not missing,
        (
            "FROZEN_TRAIN_D1_COLUMNS_MISSING:"
            f"{missing}"
        ),
    )

    working = (
        frozen_train.copy()
    )

    working[
        "decision_time"
    ] = (
        _canonical_time(
            working[
                "decision_time"
            ]
        )
    )

    age_minutes = pd.to_numeric(
        working[
            "d1_age_minutes"
        ],
        errors="coerce",
    )

    finite_age = np.isfinite(
        age_minutes.to_numpy(
            dtype=np.float64
        )
    )

    _require(
        bool(
            finite_age.all()
        ),
        "FROZEN_D1_AGE_HAS_NONFINITE_VALUES",
    )

    negative_age_rows = int(
        (
            age_minutes
            <
            0
        )
        .sum()
    )

    _require(
        negative_age_rows
        ==
        0,
        (
            "FROZEN_D1_AGE_NEGATIVE_ROWS:"
            f"{negative_age_rows}"
        ),
    )

    working[
        "frozen_available_time"
    ] = (
        working[
            "decision_time"
        ]
        -
        pd.to_timedelta(
            age_minutes,
            unit="m",
        )
    )

    working[
        "frozen_available_time"
    ] = (
        _canonical_time(
            working[
                "frozen_available_time"
            ]
        )
    )

    inconsistent_features: list[
        str
    ] = []

    grouped = working.groupby(
        "frozen_available_time",
        sort=True,
        observed=True,
    )

    for feature in (
        technical_features
    ):

        maximum_unique = int(
            grouped[
                feature
            ]
            .nunique(
                dropna=False
            )
            .max()
        )

        if (
            maximum_unique
            >
            1
        ):

            inconsistent_features.append(
                feature
            )

    _require(
        not inconsistent_features,
        (
            "FROZEN_D1_STATE_FEATURE_INCONSISTENCY:"
            f"{inconsistent_features}"
        ),
    )

    states = (
        working
        .sort_values(
            "decision_time"
        )
        .drop_duplicates(
            subset=[
                "frozen_available_time"
            ],
            keep="first",
        )
        [
            [
                "frozen_available_time",
                *technical_features,
            ]
        ]
        .copy()
        .sort_values(
            "frozen_available_time"
        )
        .reset_index(
            drop=True
        )
    )

    _require(
        not states.empty,
        "FROZEN_D1_STATE_TABLE_EMPTY",
    )

    duplicate_state_times = int(
        states[
            "frozen_available_time"
        ]
        .duplicated(
            keep=False
        )
        .sum()
    )

    _require(
        duplicate_state_times
        ==
        0,
        (
            "FROZEN_D1_STATE_TIME_DUPLICATES:"
            f"{duplicate_state_times}"
        ),
    )

    return (
        states,
        {
            "train_rows": int(
                len(
                    frozen_train
                )
            ),
            "unique_d1_state_rows": int(
                len(
                    states
                )
            ),
            "negative_age_rows": (
                negative_age_rows
            ),
            "inconsistent_feature_count": int(
                len(
                    inconsistent_features
                )
            ),
            "state_time_start": (
                pd.Timestamp(
                    states[
                        "frozen_available_time"
                    ].min()
                ).isoformat()
            ),
            "state_time_end": (
                pd.Timestamp(
                    states[
                        "frozen_available_time"
                    ].max()
                ).isoformat()
            ),
        },
    )


def _generate_from_frozen_raw_d1(
    *,
    frozen_raw_d1: pd.DataFrame,
    technical_features: Sequence[
        str
    ],
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

    builder = TrainingMatrixBuilder(
        canonical_root=(
            CANONICAL_ROOT
        )
    )

    generated = (
        builder
        ._generate_feature_frame(
            frame=(
                frozen_raw_d1
            ),
            timeframe="D1",
        )
    )

    _require(
        isinstance(
            generated,
            pd.DataFrame,
        ),
        "D1_FEATURE_GENERATOR_NOT_DATAFRAME",
    )

    required_columns = {
        "time",
        "available_time",
        *technical_features,
    }

    missing = sorted(
        required_columns
        -
        set(
            str(
                column
            )
            for column
            in generated.columns
        )
    )

    _require(
        not missing,
        (
            "GENERATED_D1_COLUMNS_MISSING:"
            f"{missing}"
        ),
    )

    result = (
        generated[
            [
                "time",
                "available_time",
                *technical_features,
            ]
        ]
        .copy()
    )

    result[
        "time"
    ] = (
        _canonical_time(
            result[
                "time"
            ]
        )
    )

    result[
        "available_time"
    ] = (
        _canonical_time(
            result[
                "available_time"
            ]
        )
    )

    result = (
        result
        .sort_values(
            "available_time"
        )
        .reset_index(
            drop=True
        )
    )

    duplicate_available_times = int(
        result[
            "available_time"
        ]
        .duplicated(
            keep=False
        )
        .sum()
    )

    _require(
        duplicate_available_times
        ==
        0,
        (
            "GENERATED_D1_AVAILABLE_TIME_DUPLICATES:"
            f"{duplicate_available_times}"
        ),
    )

    availability_delta_minutes = (
        (
            result[
                "available_time"
            ]
            -
            result[
                "time"
            ]
        )
        .dt
        .total_seconds()
        /
        60.0
    )

    unique_availability_deltas = sorted(
        {
            float(
                value
            )
            for value
            in availability_delta_minutes
            .dropna()
            .tolist()
        }
    )

    return (
        result,
        {
            "raw_d1_rows": int(
                len(
                    frozen_raw_d1
                )
            ),
            "generated_rows": int(
                len(
                    result
                )
            ),
            "duplicate_available_time_rows": (
                duplicate_available_times
            ),
            "unique_available_minus_bar_time_minutes": (
                unique_availability_deltas
            ),
            "generated_time_start": (
                pd.Timestamp(
                    result[
                        "time"
                    ].min()
                ).isoformat()
            ),
            "generated_time_end": (
                pd.Timestamp(
                    result[
                        "time"
                    ].max()
                ).isoformat()
            ),
            "available_time_start": (
                pd.Timestamp(
                    result[
                        "available_time"
                    ].min()
                ).isoformat()
            ),
            "available_time_end": (
                pd.Timestamp(
                    result[
                        "available_time"
                    ].max()
                ).isoformat()
            ),
        },
    )


def _feature_replay_metrics(
    frozen_values: pd.Series,
    generated_values: pd.Series,
) -> dict[str, Any]:

    frozen = np.asarray(
        pd.to_numeric(
            frozen_values,
            errors="coerce",
        ),
        dtype=np.float64,
    )

    generated = np.asarray(
        pd.to_numeric(
            generated_values,
            errors="coerce",
        ),
        dtype=np.float64,
    )

    _require(
        frozen.shape
        ==
        generated.shape,
        (
            "FEATURE_REPLAY_SHAPE_MISMATCH:"
            f"{frozen.shape}:"
            f"{generated.shape}"
        ),
    )

    both_nan = (
        np.isnan(
            frozen
        )
        &
        np.isnan(
            generated
        )
    )

    finite = (
        np.isfinite(
            frozen
        )
        &
        np.isfinite(
            generated
        )
    )

    comparable = (
        both_nan
        |
        finite
    )

    comparable_rows = int(
        comparable.sum()
    )

    exact_mask = np.zeros(
        frozen.shape,
        dtype=bool,
    )

    exact_mask[
        both_nan
    ] = True

    if bool(
        finite.any()
    ):

        exact_mask[
            finite
        ] = np.isclose(
            frozen[
                finite
            ],
            generated[
                finite
            ],
            rtol=0.0,
            atol=(
                EXACT_ABSOLUTE_TOLERANCE
            ),
            equal_nan=False,
        )

    exact_match_rows = int(
        (
            exact_mask
            &
            comparable
        )
        .sum()
    )

    exact_match_fraction = (
        float(
            exact_match_rows
            /
            comparable_rows
        )
        if (
            comparable_rows
            >
            0
        )
        else None
    )

    finite_rows = int(
        finite.sum()
    )

    mae: (
        float
        |
        None
    ) = None

    normalized_mae: (
        float
        |
        None
    ) = None

    maximum_absolute_difference: (
        float
        |
        None
    ) = None

    if (
        finite_rows
        >
        0
    ):

        absolute_difference = np.abs(
            frozen[
                finite
            ]
            -
            generated[
                finite
            ]
        )

        mae = float(
            np.mean(
                absolute_difference
            )
        )

        maximum_absolute_difference = float(
            np.max(
                absolute_difference
            )
        )

        frozen_scale = float(
            np.std(
                frozen[
                    finite
                ]
            )
        )

        denominator = max(
            frozen_scale,
            1e-12,
        )

        normalized_mae = float(
            mae
            /
            denominator
        )

    correlation = (
        _correlation(
            frozen,
            generated,
        )
    )

    exact_feature = bool(
        exact_match_fraction
        is not None
        and
        exact_match_fraction
        >=
        0.999
        and
        normalized_mae
        is not None
        and
        normalized_mae
        <=
        1e-6
    )

    return {
        "comparable_rows": (
            comparable_rows
        ),
        "finite_rows": (
            finite_rows
        ),
        "exact_match_rows": (
            exact_match_rows
        ),
        "exact_match_fraction": (
            exact_match_fraction
        ),
        "mean_absolute_difference": (
            mae
        ),
        "maximum_absolute_difference": (
            maximum_absolute_difference
        ),
        "normalized_mae": (
            normalized_mae
        ),
        "paired_correlation": (
            correlation
        ),
        "exact_feature_replay": (
            exact_feature
        ),
    }


def _candidate_document(
    *,
    frozen_states: pd.DataFrame,
    generated: pd.DataFrame,
    technical_features: Sequence[
        str
    ],
    shift_days: int,
) -> dict[str, Any]:

    right = (
        generated[
            [
                "available_time",
                *technical_features,
            ]
        ]
        .copy()
    )

    right[
        "candidate_available_time"
    ] = (
        right[
            "available_time"
        ]
        +
        pd.Timedelta(
            days=(
                shift_days
            )
        )
    )

    right[
        "candidate_available_time"
    ] = (
        _canonical_time(
            right[
                "candidate_available_time"
            ]
        )
    )

    right = (
        right.drop(
            columns=[
                "available_time"
            ]
        )
    )

    paired = (
        frozen_states
        .merge(
            right,
            left_on="frozen_available_time",
            right_on="candidate_available_time",
            how="inner",
            suffixes=(
                "_frozen",
                "_generated",
            ),
            validate="one_to_one",
        )
        .sort_values(
            "frozen_available_time"
        )
        .reset_index(
            drop=True
        )
    )

    paired_states = int(
        len(
            paired
        )
    )

    feature_metrics: dict[
        str,
        dict[str, Any],
    ] = {}

    exact_feature_count = 0

    exact_fractions: list[
        float | None
    ] = []

    normalized_maes: list[
        float | None
    ] = []

    correlations: list[
        float | None
    ] = []

    if (
        paired_states
        >
        0
    ):

        for feature in (
            technical_features
        ):

            metrics = (
                _feature_replay_metrics(
                    paired[
                        (
                            feature
                            +
                            "_frozen"
                        )
                    ],
                    paired[
                        (
                            feature
                            +
                            "_generated"
                        )
                    ],
                )
            )

            feature_metrics[
                feature
            ] = (
                metrics
            )

            if bool(
                metrics[
                    "exact_feature_replay"
                ]
            ):

                exact_feature_count += 1

            exact_fractions.append(
                _safe_float(
                    metrics[
                        "exact_match_fraction"
                    ]
                )
            )

            normalized_maes.append(
                _safe_float(
                    metrics[
                        "normalized_mae"
                    ]
                )
            )

            correlations.append(
                _safe_float(
                    metrics[
                        "paired_correlation"
                    ]
                )
            )

    return {
        "shift_days": int(
            shift_days
        ),
        "paired_state_rows": (
            paired_states
        ),
        "paired_state_fraction_vs_frozen": float(
            paired_states
            /
            len(
                frozen_states
            )
        ),
        "technical_feature_count": int(
            len(
                technical_features
            )
        ),
        "exact_feature_replay_count": int(
            exact_feature_count
        ),
        "median_exact_match_fraction": (
            _median_finite(
                exact_fractions
            )
        ),
        "median_normalized_mae": (
            _median_finite(
                normalized_maes
            )
        ),
        "median_paired_correlation": (
            _median_finite(
                correlations
            )
        ),
        "feature_metrics": (
            feature_metrics
        ),
    }


def _candidate_score(
    document: Mapping[
        str,
        Any,
    ],
) -> tuple[
    int,
    float,
    float,
    float,
    int,
]:

    exact_feature_count = int(
        document.get(
            "exact_feature_replay_count",
            0,
        )
    )

    exact_fraction = (
        _safe_float(
            document.get(
                "median_exact_match_fraction"
            )
        )
    )

    normalized_mae = (
        _safe_float(
            document.get(
                "median_normalized_mae"
            )
        )
    )

    correlation = (
        _safe_float(
            document.get(
                "median_paired_correlation"
            )
        )
    )

    paired_states = int(
        document.get(
            "paired_state_rows",
            0,
        )
    )

    return (
        exact_feature_count,
        (
            exact_fraction
            if exact_fraction
            is not None
            else -1.0
        ),
        (
            -normalized_mae
            if normalized_mae
            is not None
            else -1e12
        ),
        (
            correlation
            if correlation
            is not None
            else -2.0
        ),
        paired_states,
    )


def _decision(
    candidates: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
) -> dict[str, Any]:

    _require(
        bool(
            candidates
        ),
        "NO_D1_REPLAY_CANDIDATES",
    )

    ranked = sorted(
        candidates,
        key=_candidate_score,
        reverse=True,
    )

    best = (
        ranked[
            0
        ]
    )

    selected_shift = int(
        best[
            "shift_days"
        ]
    )

    paired_states = int(
        best[
            "paired_state_rows"
        ]
    )

    exact_feature_count = int(
        best[
            "exact_feature_replay_count"
        ]
    )

    median_exact_fraction = (
        _safe_float(
            best.get(
                "median_exact_match_fraction"
            )
        )
    )

    median_normalized_mae = (
        _safe_float(
            best.get(
                "median_normalized_mae"
            )
        )
    )

    median_correlation = (
        _safe_float(
            best.get(
                "median_paired_correlation"
            )
        )
    )

    if (
        paired_states
        >=
        MIN_PAIRED_D1_STATES
        and
        exact_feature_count
        >=
        CONFIRMED_MIN_EXACT_FEATURE_COUNT
        and
        median_exact_fraction
        is not None
        and
        median_exact_fraction
        >=
        CONFIRMED_MIN_MEDIAN_EXACT_MATCH_FRACTION
        and
        median_normalized_mae
        is not None
        and
        median_normalized_mae
        <=
        CONFIRMED_MAX_MEDIAN_NORMALIZED_MAE
    ):

        status = (
            "FROZEN_D1_FEATURE_STATE_REPLAY_CONFIRMED"
        )

        reason = (
            "IMMUTABLE_FROZEN_D1_RAW_SOURCE_AND_EXACT_"
            "FEATURE_GENERATOR_REPRODUCE_FROZEN_TRAIN_"
            "D1_FEATURE_STATES_AT_ONE_AVAILABILITY_SHIFT"
        )

        next_action = (
            "APPLY_CONFIRMED_D1_FEATURE_STATE_ALIGNMENT_"
            "TO_CURRENT_00UTC_RECONSTRUCTED_D1_AND_"
            "ISOLATE_TRUE_CROSS_BROKER_FEATURE_RESIDUALS"
        )

    elif (
        paired_states
        >=
        MIN_PAIRED_D1_STATES
        and
        exact_feature_count
        >=
        LIKELY_MIN_EXACT_FEATURE_COUNT
        and
        median_exact_fraction
        is not None
        and
        median_exact_fraction
        >=
        LIKELY_MIN_MEDIAN_EXACT_MATCH_FRACTION
        and
        median_normalized_mae
        is not None
        and
        median_normalized_mae
        <=
        LIKELY_MAX_MEDIAN_NORMALIZED_MAE
    ):

        status = (
            "FROZEN_D1_FEATURE_STATE_REPLAY_LIKELY"
        )

        reason = (
            "FROZEN_D1_REPLAY_IS_HIGHLY_CONSISTENT_"
            "BUT_NOT_EXACT_ENOUGH_FOR_CONTRACT_CONFIRMATION"
        )

        next_action = (
            "ISOLATE_NONEXACT_FROZEN_D1_FEATURES_"
            "BEFORE_CURRENT_BROKER_COMPARISON"
        )

    else:

        status = (
            "FROZEN_D1_FEATURE_STATE_REPLAY_UNRESOLVED"
        )

        reason = (
            "EXACT_FROZEN_D1_RAW_REPLAY_DOES_NOT_"
            "SUFFICIENTLY_REPRODUCE_FROZEN_TRAIN_D1_FEATURE_STATES"
        )

        next_action = (
            "TRACE_D1_FEATURE_AVAILABILITY_AND_MATRIX_"
            "MERGE_PROVENANCE_IN_TRAINING_MATRIX_BUILDER"
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "selected_availability_shift_days": (
            selected_shift
        ),
        "selected_paired_state_rows": (
            paired_states
        ),
        "selected_exact_feature_replay_count": (
            exact_feature_count
        ),
        "selected_median_exact_match_fraction": (
            median_exact_fraction
        ),
        "selected_median_normalized_mae": (
            median_normalized_mae
        ),
        "selected_median_paired_correlation": (
            median_correlation
        ),
        "frozen_d1_feature_state_contract_confirmed": bool(
            status
            ==
            "FROZEN_D1_FEATURE_STATE_REPLAY_CONFIRMED"
        ),
        "current_broker_used": (
            False
        ),
        "broker_specific_retraining_authorized": (
            False
        ),
        "test_evaluation_authorized": (
            False
        ),
        "full_mtf_portability_verdict_allowed": (
            False
        ),
        "next_action": (
            next_action
        ),
    }


def run_diagnostic(
) -> dict[str, Any]:

    trainer = (
        base
        .XAUUSDHierarchicalModelV4Trainer()
    )

    training_snapshot = (
        base
        .sweep_module
        ._discover_frozen_training_snapshot(
            trainer=trainer
        )
    )

    training_dataset_path = (
        base
        ._snapshot_dataset_path(
            training_snapshot
        )
    )

    training_manifest_path = (
        base
        ._snapshot_manifest_path(
            training_snapshot,
            training_dataset_path,
        )
    )

    base._validate_snapshot(
        training_snapshot,
        training_dataset_path,
        training_manifest_path,
    )

    manifest = (
        base
        ._load_manifest(
            training_manifest_path
        )
    )

    technical_features = (
        _technical_features(
            manifest
        )
    )

    frozen_train = (
        base
        ._load_frozen_train_only(
            training_dataset_path,
            [
                *technical_features,
                "d1_age_minutes",
            ],
        )
    )

    frozen_train[
        "decision_time"
    ] = (
        _canonical_time(
            frozen_train[
                "decision_time"
            ]
        )
    )

    _require(
        len(
            frozen_train
        )
        ==
        base.EXPECTED_TRAIN_ROWS,
        (
            "FROZEN_TRAIN_ROW_COUNT_MISMATCH:"
            f"{len(frozen_train)}:"
            f"{base.EXPECTED_TRAIN_ROWS}"
        ),
    )

    (
        frozen_states,
        frozen_state_meta,
    ) = (
        _frozen_d1_states(
            frozen_train=(
                frozen_train
            ),
            technical_features=(
                technical_features
            ),
        )
    )

    d1_snapshot = (
        source
        ._snapshot_document(
            manifest,
            "D1",
        )
    )

    (
        d1_path,
        d1_resolution,
    ) = (
        source
        ._resolve_snapshot_file(
            d1_snapshot
        )
    )

    frozen_raw_d1 = (
        source
        ._read_snapshot_frame(
            d1_path,
            d1_snapshot,
        )
    )

    (
        generated,
        generation_meta,
    ) = (
        _generate_from_frozen_raw_d1(
            frozen_raw_d1=(
                frozen_raw_d1
            ),
            technical_features=(
                technical_features
            ),
        )
    )

    candidates = [
        _candidate_document(
            frozen_states=(
                frozen_states
            ),
            generated=(
                generated
            ),
            technical_features=(
                technical_features
            ),
            shift_days=(
                shift_days
            ),
        )
        for shift_days
        in CANDIDATE_AVAILABILITY_SHIFT_DAYS
    ]

    ranked = sorted(
        candidates,
        key=_candidate_score,
        reverse=True,
    )

    decision = (
        _decision(
            candidates
        )
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_FROZEN_D1_FEATURE_STATE_REPLAY"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "research_scope": (
            "IMMUTABLE_FROZEN_D1_RAW_TO_FROZEN_TRAIN_"
            "FEATURE_STATE_REPLAY_NO_CURRENT_BROKER"
        ),
        "frozen_training_reference": {
            "training_dataset_id": (
                base.EXPECTED_DATASET_ID
            ),
            "training_dataset_sha256": (
                base.EXPECTED_DATASET_SHA256
            ),
            "training_manifest_sha256": (
                base
                .EXPECTED_TRAINING_MANIFEST_SHA256
            ),
            "training_contract": (
                base.EXPECTED_TRAINING_CONTRACT
            ),
            "split_loaded": (
                "TRAIN_ONLY"
            ),
            "train_rows": int(
                len(
                    frozen_train
                )
            ),
            "technical_feature_count": int(
                len(
                    technical_features
                )
            ),
        },
        "frozen_raw_d1": {
            "dataset_id": (
                d1_snapshot[
                    "dataset_id"
                ]
            ),
            "dataset_sha256": (
                d1_snapshot[
                    "dataset_sha256"
                ]
            ),
            "expected_rows": int(
                d1_snapshot[
                    "row_count"
                ]
            ),
            "loaded_rows": int(
                len(
                    frozen_raw_d1
                )
            ),
            "data_file_sha256_validated": (
                True
            ),
            "resolution": (
                d1_resolution
            ),
            "filesystem_path_emitted": (
                False
            ),
        },
        "frozen_state_derivation": (
            frozen_state_meta
        ),
        "exact_feature_generation": (
            generation_meta
        ),
        "diagnostic_contract": {
            "candidate_availability_shift_days": list(
                CANDIDATE_AVAILABILITY_SHIFT_DAYS
            ),
            "candidate_count": int(
                len(
                    candidates
                )
            ),
            "feature_count": int(
                len(
                    technical_features
                )
            ),
            "frozen_state_available_time_formula": (
                "DECISION_TIME_MINUS_D1_AGE_MINUTES"
            ),
            "generated_availability_source": (
                "TRAINING_MATRIX_BUILDER_GENERATED_AVAILABLE_TIME"
            ),
            "comparison_unit": (
                "UNIQUE_FROZEN_D1_AVAILABLE_STATE"
            ),
            "exact_absolute_tolerance": (
                EXACT_ABSOLUTE_TOLERANCE
            ),
        },
        "thresholds": {
            "minimum_paired_d1_states": (
                MIN_PAIRED_D1_STATES
            ),
            "confirmed_min_exact_feature_count": (
                CONFIRMED_MIN_EXACT_FEATURE_COUNT
            ),
            "confirmed_min_median_exact_match_fraction": (
                CONFIRMED_MIN_MEDIAN_EXACT_MATCH_FRACTION
            ),
            "confirmed_max_median_normalized_mae": (
                CONFIRMED_MAX_MEDIAN_NORMALIZED_MAE
            ),
            "likely_min_exact_feature_count": (
                LIKELY_MIN_EXACT_FEATURE_COUNT
            ),
            "likely_min_median_exact_match_fraction": (
                LIKELY_MIN_MEDIAN_EXACT_MATCH_FRACTION
            ),
            "likely_max_median_normalized_mae": (
                LIKELY_MAX_MEDIAN_NORMALIZED_MAE
            ),
        },
        "decision": (
            decision
        ),
        "candidate_ranking": [
            {
                "rank": int(
                    index
                ),
                "shift_days": (
                    document[
                        "shift_days"
                    ]
                ),
                "paired_state_rows": (
                    document[
                        "paired_state_rows"
                    ]
                ),
                "paired_state_fraction_vs_frozen": (
                    document[
                        "paired_state_fraction_vs_frozen"
                    ]
                ),
                "exact_feature_replay_count": (
                    document[
                        "exact_feature_replay_count"
                    ]
                ),
                "median_exact_match_fraction": (
                    document[
                        "median_exact_match_fraction"
                    ]
                ),
                "median_normalized_mae": (
                    document[
                        "median_normalized_mae"
                    ]
                ),
                "median_paired_correlation": (
                    document[
                        "median_paired_correlation"
                    ]
                ),
            }
            for (
                index,
                document,
            )
            in enumerate(
                ranked,
                start=1,
            )
        ],
        "candidate_diagnostics": (
            candidates
        ),
        "warmup_diagnostic_note": {
            "previous_warmup_status": (
                "D1_FEATURE_WARMUP_STATE_NOT_SUFFICIENT"
            ),
            "previous_warmup_verdict_scientifically_accepted": (
                False
            ),
            "reason": (
                "ALL_TESTED_CUTOFF_TIMES_PRECEDED_"
                "THE_FROZEN_TRAIN_WINDOW_SO_ALL_CUTOFFS_"
                "COMPARED_THE_SAME_256_D1_STATES"
            ),
            "current_history_days_before_train_start": (
                699.3645833333334
            ),
        },
        "scientific_policy": {
            "immutable_frozen_d1_loaded": (
                True
            ),
            "raw_snapshot_hash_validated": (
                True
            ),
            "train_loaded": (
                True
            ),
            "validation_loaded": (
                False
            ),
            "validation_evaluated": (
                False
            ),
            "test_loaded": (
                False
            ),
            "test_evaluated": (
                False
            ),
            "labels_used": (
                False
            ),
            "target_columns_loaded": (
                False
            ),
            "model_loaded": (
                False
            ),
            "model_trained": (
                False
            ),
            "model_artifacts_written": (
                False
            ),
            "mt5_used": (
                False
            ),
            "current_broker_used": (
                False
            ),
            "orders_sent": (
                False
            ),
            "positions_modified": (
                False
            ),
            "risk_engine_modified": (
                False
            ),
            "sizing_modified": (
                False
            ),
            "execution_integration_modified": (
                False
            ),
            "broker_specific_retraining_authorized": (
                False
            ),
            "test_evaluation_authorized": (
                False
            ),
            "full_mtf_portability_verdict_allowed": (
                False
            ),
            "live_authorized": (
                False
            ),
            "filesystem_paths_emitted": (
                False
            ),
            "account_login_emitted": (
                False
            ),
            "account_holder_name_emitted": (
                False
            ),
            "account_scope_identifier_emitted": (
                False
            ),
        },
        "next_decision_contract": {
            "if_replay_confirmed": (
                "APPLY_EXACT_D1_STATE_ALIGNMENT_TO_CURRENT_"
                "00UTC_RECONSTRUCTED_D1_AND_ISOLATE_TRUE_"
                "CROSS_BROKER_FEATURE_RESIDUALS"
            ),
            "if_replay_likely": (
                "ISOLATE_NONEXACT_FROZEN_D1_FEATURES"
            ),
            "if_replay_unresolved": (
                "TRACE_D1_FEATURE_AVAILABILITY_AND_MATRIX_"
                "MERGE_PROVENANCE"
            ),
            "previous_warmup_file_not_committed": (
                True
            ),
            "full_mtf_runner_remains_uncommitted": (
                True
            ),
            "utc_false_positive_fix_remains_deferred": (
                True
            ),
            "test_holdout_remains_untouched": (
                True
            ),
            "v3_contract_not_mutated": (
                True
            ),
        },
    }


def main() -> int:

    try:

        result = (
            run_diagnostic()
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_FROZEN_D1_FEATURE_STATE_REPLAY_FAILED"
                    ),
                    "analysis_version": (
                        ANALYSIS_VERSION
                    ),
                    "error_type": (
                        type(
                            exc
                        ).__name__
                    ),
                    "error": (
                        str(
                            exc
                        )
                    ),
                    "validation_loaded": (
                        False
                    ),
                    "test_loaded": (
                        False
                    ),
                    "test_evaluated": (
                        False
                    ),
                    "mt5_used": (
                        False
                    ),
                    "current_broker_used": (
                        False
                    ),
                    "model_loaded": (
                        False
                    ),
                    "model_trained": (
                        False
                    ),
                    "model_artifacts_written": (
                        False
                    ),
                    "orders_sent": (
                        False
                    ),
                    "positions_modified": (
                        False
                    ),
                    "risk_engine_modified": (
                        False
                    ),
                    "live_authorized": (
                        False
                    ),
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