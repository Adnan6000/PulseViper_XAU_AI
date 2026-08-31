from __future__ import annotations

import importlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import MetaTrader5 as mt5
import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


ANALYSIS_VERSION = (
    "XAUUSD_CURRENT_BROKER_D1_FEATURE_STATE_WARMUP_V1"
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

mapped: Any = (
    full.mapped
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


CONFIRMED_D1_SESSION_CLOSE_HOUR_UTC = 0

CONFIRMED_D1_LABEL_DAY_SHIFT = 0


H1_REQUEST_START = pd.Timestamp(
    "2010-01-01T00:00:00Z"
)


MIN_H1_BARS_PER_SYNTHETIC_D1 = 6

MIN_DAILY_STATE_ROWS = 30


WARMUP_CUTOFF_DAYS = (
    0,
    30,
    60,
    90,
    120,
    150,
    180,
    240,
    300,
)


D1_ANCHOR_FEATURES = (
    "d1_rsi_slope",
    "d1_roc10",
    "d1_momentum10",
    "d1_true_range",
    "d1_candle_range",
    "d1_body",
    "d1_range",
    "d1_upper_wick",
    "d1_lower_wick",
    "d1_body_ratio",
    "d1_upper_wick_ratio",
    "d1_lower_wick_ratio",
)


CONFIRMED_ANCHOR_MEDIAN_CORRELATION = 0.95

CONFIRMED_ALL_MEDIAN_CORRELATION = 0.95

CONFIRMED_MINIMUM_ANCHOR_GAIN = 0.10

CONFIRMED_MINIMUM_ALL_GAIN = 0.10


MATERIAL_ANCHOR_MEDIAN_CORRELATION = 0.90

MATERIAL_ALL_MEDIAN_CORRELATION = 0.90

MATERIAL_MINIMUM_ANCHOR_GAIN = 0.05

MATERIAL_MINIMUM_ALL_GAIN = 0.05


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


def _count_at_least(
    values: Sequence[
        float | None
    ],
    threshold: float,
) -> int:

    return int(
        sum(
            1
            for value
            in values
            if (
                value is not None
                and
                value
                >=
                threshold
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


def _clock_map_current_h1(
    raw_h1: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

    required_columns = {
        "time",
        "open",
        "high",
        "low",
        "close",
    }

    missing = sorted(
        required_columns
        -
        set(
            str(
                column
            )
            for column
            in raw_h1.columns
        )
    )

    _require(
        not missing,
        (
            "CURRENT_H1_REQUIRED_COLUMNS_MISSING:"
            f"{missing}"
        ),
    )

    current = (
        raw_h1.copy()
    )

    current[
        "source_broker_time"
    ] = (
        _canonical_time(
            current[
                "time"
            ]
        )
    )

    (
        market_time,
        mapping_meta,
    ) = (
        full
        ._clock_map_times(
            current[
                "source_broker_time"
            ]
        )
    )

    current[
        "time"
    ] = (
        _canonical_time(
            market_time
        )
    )

    current = (
        current
        .sort_values(
            "time"
        )
        .reset_index(
            drop=True
        )
    )

    duplicate_count = int(
        current[
            "time"
        ]
        .duplicated(
            keep=False
        )
        .sum()
    )

    _require(
        duplicate_count
        ==
        0,
        (
            "CURRENT_CANONICAL_H1_TIME_DUPLICATES:"
            f"{duplicate_count}"
        ),
    )

    return (
        current,
        {
            **mapping_meta,
            "duplicate_canonical_h1_time_rows": (
                duplicate_count
            ),
            "canonical_time_dtype": (
                str(
                    current[
                        "time"
                    ].dtype
                )
            ),
        },
    )


def _build_synthetic_d1_raw(
    canonical_h1: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

    required_columns = {
        "time",
        "open",
        "high",
        "low",
        "close",
    }

    missing = sorted(
        required_columns
        -
        set(
            str(
                column
            )
            for column
            in canonical_h1.columns
        )
    )

    _require(
        not missing,
        (
            "CANONICAL_H1_REQUIRED_COLUMNS_MISSING:"
            f"{missing}"
        ),
    )

    working = (
        canonical_h1.copy()
    )

    working[
        "session_close"
    ] = (
        working[
            "time"
        ]
        .dt
        .floor(
            "D"
        )
        +
        pd.Timedelta(
            days=1
        )
    )

    aggregation: dict[
        str,
        str
    ] = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "time": "count",
    }

    if (
        "tick_volume"
        in working.columns
    ):

        aggregation[
            "tick_volume"
        ] = "sum"

    if (
        "spread"
        in working.columns
    ):

        aggregation[
            "spread"
        ] = "median"

    if (
        "real_volume"
        in working.columns
    ):

        aggregation[
            "real_volume"
        ] = "sum"

    grouped = (
        working
        .groupby(
            "session_close",
            sort=True,
            observed=True,
        )
        .agg(
            aggregation
        )
        .reset_index()
        .rename(
            columns={
                "time": (
                    "h1_bar_count"
                )
            }
        )
    )

    grouped[
        "h1_bar_count"
    ] = pd.to_numeric(
        grouped[
            "h1_bar_count"
        ],
        errors="raise",
    ).astype(
        "int64"
    )

    sessions_before_filter = int(
        len(
            grouped
        )
    )

    grouped = (
        grouped.loc[
            grouped[
                "h1_bar_count"
            ]
            >=
            MIN_H1_BARS_PER_SYNTHETIC_D1
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    _require(
        not grouped.empty,
        "NO_SYNTHETIC_D1_SESSIONS",
    )

    grouped[
        "session_close"
    ] = (
        _canonical_time(
            grouped[
                "session_close"
            ]
        )
    )

    grouped[
        "time"
    ] = (
        grouped[
            "session_close"
        ]
        -
        pd.Timedelta(
            days=1
        )
    )

    grouped[
        "time"
    ] = (
        _canonical_time(
            grouped[
                "time"
            ]
        )
    )

    output_columns = [
        "time",
        "open",
        "high",
        "low",
        "close",
    ]

    for optional_column in (
        "tick_volume",
        "spread",
        "real_volume",
    ):

        if (
            optional_column
            in grouped.columns
        ):

            output_columns.append(
                optional_column
            )

    raw_d1 = (
        grouped[
            output_columns
        ]
        .copy()
        .sort_values(
            "time"
        )
        .reset_index(
            drop=True
        )
    )

    duplicate_count = int(
        raw_d1[
            "time"
        ]
        .duplicated(
            keep=False
        )
        .sum()
    )

    _require(
        duplicate_count
        ==
        0,
        (
            "SYNTHETIC_D1_TIME_DUPLICATES:"
            f"{duplicate_count}"
        ),
    )

    bar_counts = (
        grouped[
            "h1_bar_count"
        ]
        .to_numpy(
            dtype=np.float64
        )
    )

    return (
        raw_d1,
        {
            "session_close_hour_utc": (
                CONFIRMED_D1_SESSION_CLOSE_HOUR_UTC
            ),
            "label_day_shift": (
                CONFIRMED_D1_LABEL_DAY_SHIFT
            ),
            "sessions_before_minimum_bar_filter": (
                sessions_before_filter
            ),
            "sessions_after_minimum_bar_filter": int(
                len(
                    raw_d1
                )
            ),
            "minimum_h1_bars_per_synthetic_d1": (
                MIN_H1_BARS_PER_SYNTHETIC_D1
            ),
            "minimum_observed_h1_bars": int(
                np.min(
                    bar_counts
                )
            ),
            "median_observed_h1_bars": float(
                np.median(
                    bar_counts
                )
            ),
            "maximum_observed_h1_bars": int(
                np.max(
                    bar_counts
                )
            ),
            "time_start": (
                pd.Timestamp(
                    raw_d1[
                        "time"
                    ].min()
                ).isoformat()
            ),
            "time_end": (
                pd.Timestamp(
                    raw_d1[
                        "time"
                    ].max()
                ).isoformat()
            ),
        },
    )


def _generate_d1_features(
    *,
    builder: Any,
    synthetic_raw_d1: pd.DataFrame,
    technical_features: Sequence[
        str
    ],
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

    generated = (
        builder
        ._generate_feature_frame(
            frame=(
                synthetic_raw_d1
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
            "GENERATED_D1_FEATURES_MISSING:"
            f"{missing}"
        ),
    )

    generated = (
        generated.copy()
    )

    generated[
        "time"
    ] = (
        _canonical_time(
            generated[
                "time"
            ]
        )
    )

    generated[
        "available_time"
    ] = (
        generated[
            "time"
        ]
        +
        pd.Timedelta(
            days=1
        )
    )

    generated[
        "available_time"
    ] = (
        _canonical_time(
            generated[
                "available_time"
            ]
        )
    )

    duplicate_count = int(
        generated[
            "available_time"
        ]
        .duplicated(
            keep=False
        )
        .sum()
    )

    _require(
        duplicate_count
        ==
        0,
        (
            "GENERATED_D1_AVAILABLE_TIME_DUPLICATES:"
            f"{duplicate_count}"
        ),
    )

    output = (
        generated[
            [
                "available_time",
                *technical_features,
            ]
        ]
        .copy()
        .sort_values(
            "available_time"
        )
        .reset_index(
            drop=True
        )
    )

    return (
        output,
        {
            "generated_rows": int(
                len(
                    generated
                )
            ),
            "available_time_start": (
                pd.Timestamp(
                    output[
                        "available_time"
                    ].min()
                ).isoformat()
            ),
            "available_time_end": (
                pd.Timestamp(
                    output[
                        "available_time"
                    ].max()
                ).isoformat()
            ),
            "available_time_duplicate_rows": (
                duplicate_count
            ),
        },
    )


def _align_to_frozen_train(
    *,
    frozen_train: pd.DataFrame,
    generated_d1: pd.DataFrame,
    technical_features: Sequence[
        str
    ],
) -> pd.DataFrame:

    left = (
        frozen_train[
            [
                "decision_time",
                *technical_features,
            ]
        ]
        .copy()
    )

    left[
        "decision_time"
    ] = (
        _canonical_time(
            left[
                "decision_time"
            ]
        )
    )

    left = (
        left
        .sort_values(
            "decision_time"
        )
        .reset_index(
            drop=True
        )
    )

    right = (
        generated_d1[
            [
                "available_time",
                *technical_features,
            ]
        ]
        .copy()
    )

    right[
        "available_time"
    ] = (
        _canonical_time(
            right[
                "available_time"
            ]
        )
    )

    right = (
        right
        .sort_values(
            "available_time"
        )
        .reset_index(
            drop=True
        )
    )

    _require(
        str(
            left[
                "decision_time"
            ].dtype
        )
        ==
        str(
            right[
                "available_time"
            ].dtype
        ),
        (
            "D1_ASOF_DTYPE_MISMATCH:"
            f"{left['decision_time'].dtype}:"
            f"{right['available_time'].dtype}"
        ),
    )

    aligned = pd.merge_asof(
        left,
        right,
        left_on="decision_time",
        right_on="available_time",
        direction="backward",
        allow_exact_matches=True,
        suffixes=(
            "_frozen",
            "_current",
        ),
    )

    matched_rows = int(
        aligned[
            "available_time"
        ]
        .notna()
        .sum()
    )

    _require(
        matched_rows
        >
        0,
        "NO_D1_FEATURE_STATES_ALIGNED_TO_TRAIN",
    )

    return (
        aligned
    )


def _daily_state_frame(
    aligned: pd.DataFrame,
) -> pd.DataFrame:

    matched = (
        aligned.loc[
            aligned[
                "available_time"
            ]
            .notna()
        ]
        .copy()
    )

    matched[
        "available_time"
    ] = (
        _canonical_time(
            matched[
                "available_time"
            ]
        )
    )

    daily = (
        matched
        .sort_values(
            "decision_time"
        )
        .drop_duplicates(
            subset=[
                "available_time"
            ],
            keep="last",
        )
        .reset_index(
            drop=True
        )
    )

    _require(
        not daily.empty,
        "NO_UNIQUE_D1_FEATURE_STATES",
    )

    return (
        daily
    )


def _correlation(
    left: Any,
    right: Any,
) -> float | None:

    left_values = np.asarray(
        pd.to_numeric(
            left,
            errors="coerce",
        ),
        dtype=np.float64,
    )

    right_values = np.asarray(
        pd.to_numeric(
            right,
            errors="coerce",
        ),
        dtype=np.float64,
    )

    _require(
        left_values.shape
        ==
        right_values.shape,
        (
            "CORRELATION_SHAPE_MISMATCH:"
            f"{left_values.shape}:"
            f"{right_values.shape}"
        ),
    )

    finite = (
        np.isfinite(
            left_values
        )
        &
        np.isfinite(
            right_values
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
        left_values[
            finite
        ]
    )

    y = (
        right_values[
            finite
        ]
    )

    if (
        float(
            np.std(
                x
            )
        )
        ==
        0.0
        or
        float(
            np.std(
                y
            )
        )
        ==
        0.0
    ):

        return None

    value = float(
        np.corrcoef(
            x,
            y,
        )[
            0,
            1
        ]
    )

    if not math.isfinite(
        value
    ):

        return None

    return (
        value
    )


def _cutoff_document(
    *,
    daily_states: pd.DataFrame,
    technical_features: Sequence[
        str
    ],
    first_available_time: pd.Timestamp,
    cutoff_days: int,
) -> dict[str, Any]:

    cutoff_time = (
        first_available_time
        +
        pd.Timedelta(
            days=(
                cutoff_days
            )
        )
    )

    window = (
        daily_states.loc[
            daily_states[
                "available_time"
            ]
            >=
            cutoff_time
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    daily_state_rows = int(
        len(
            window
        )
    )

    correlations: dict[
        str,
        float | None,
    ] = {}

    if (
        daily_state_rows
        >=
        MIN_DAILY_STATE_ROWS
    ):

        for feature in (
            technical_features
        ):

            correlations[
                feature
            ] = (
                _correlation(
                    window[
                        (
                            feature
                            +
                            "_frozen"
                        )
                    ],
                    window[
                        (
                            feature
                            +
                            "_current"
                        )
                    ],
                )
            )

    else:

        correlations = {
            feature: None
            for feature
            in technical_features
        }

    all_values = list(
        correlations.values()
    )

    anchor_values = [
        correlations[
            feature
        ]
        for feature
        in D1_ANCHOR_FEATURES
    ]

    return {
        "cutoff_days_from_first_current_d1_state": int(
            cutoff_days
        ),
        "cutoff_time": (
            cutoff_time.isoformat()
        ),
        "daily_state_rows": (
            daily_state_rows
        ),
        "sufficient_daily_state_rows": bool(
            daily_state_rows
            >=
            MIN_DAILY_STATE_ROWS
        ),
        "all_technical_median_correlation": (
            _median_finite(
                all_values
            )
        ),
        "all_technical_correlation_ge_0_80_count": (
            _count_at_least(
                all_values,
                0.80,
            )
        ),
        "all_technical_correlation_ge_0_90_count": (
            _count_at_least(
                all_values,
                0.90,
            )
        ),
        "all_technical_correlation_ge_0_95_count": (
            _count_at_least(
                all_values,
                0.95,
            )
        ),
        "all_technical_correlation_ge_0_98_count": (
            _count_at_least(
                all_values,
                0.98,
            )
        ),
        "anchor_median_correlation": (
            _median_finite(
                anchor_values
            )
        ),
        "anchor_correlation_ge_0_80_count": (
            _count_at_least(
                anchor_values,
                0.80,
            )
        ),
        "anchor_correlation_ge_0_90_count": (
            _count_at_least(
                anchor_values,
                0.90,
            )
        ),
        "anchor_correlation_ge_0_95_count": (
            _count_at_least(
                anchor_values,
                0.95,
            )
        ),
        "feature_correlations": (
            correlations
        ),
    }


def _candidate_score(
    document: Mapping[
        str,
        Any,
    ],
) -> tuple[
    float,
    float,
    int,
    int,
]:

    anchor = (
        _safe_float(
            document.get(
                "anchor_median_correlation"
            )
        )
    )

    all_median = (
        _safe_float(
            document.get(
                "all_technical_median_correlation"
            )
        )
    )

    all_095 = int(
        document.get(
            "all_technical_correlation_ge_0_95_count",
            0,
        )
    )

    rows = int(
        document.get(
            "daily_state_rows",
            0,
        )
    )

    return (
        (
            anchor
            if anchor
            is not None
            else -2.0
        ),
        (
            all_median
            if all_median
            is not None
            else -2.0
        ),
        all_095,
        rows,
    )


def _decision(
    cutoff_documents: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
) -> dict[str, Any]:

    _require(
        bool(
            cutoff_documents
        ),
        "NO_D1_WARMUP_CUTOFF_DOCUMENTS",
    )

    baseline_candidate = next(
        (
            document
            for document
            in cutoff_documents
            if int(
                document[
                    "cutoff_days_from_first_current_d1_state"
                ]
            )
            ==
            0
        ),
        None,
    )

    if baseline_candidate is None:
        raise RuntimeError(
            "D1_WARMUP_BASELINE_MISSING"
        )

    baseline: Mapping[
        str,
        Any,
    ] = baseline_candidate

    eligible = [
        document
        for document
        in cutoff_documents
        if bool(
            document.get(
                "sufficient_daily_state_rows",
                False,
            )
        )
    ]

    _require(
        bool(
            eligible
        ),
        "NO_ELIGIBLE_D1_WARMUP_CUTOFFS",
    )

    ranked = sorted(
        eligible,
        key=_candidate_score,
        reverse=True,
    )

    best = (
        ranked[
            0
        ]
    )

    baseline_anchor = (
        _safe_float(
            baseline.get(
                "anchor_median_correlation"
            )
        )
    )

    baseline_all = (
        _safe_float(
            baseline.get(
                "all_technical_median_correlation"
            )
        )
    )

    best_anchor = (
        _safe_float(
            best.get(
                "anchor_median_correlation"
            )
        )
    )

    best_all = (
        _safe_float(
            best.get(
                "all_technical_median_correlation"
            )
        )
    )

    anchor_gain: (
        float
        |
        None
    ) = None

    all_gain: (
        float
        |
        None
    ) = None

    if (
        baseline_anchor
        is not None
        and
        best_anchor
        is not None
    ):

        anchor_gain = float(
            best_anchor
            -
            baseline_anchor
        )

    if (
        baseline_all
        is not None
        and
        best_all
        is not None
    ):

        all_gain = float(
            best_all
            -
            baseline_all
        )

    best_cutoff_days = int(
        best[
            "cutoff_days_from_first_current_d1_state"
        ]
    )

    if (
        best_cutoff_days
        >
        0
        and
        best_anchor
        is not None
        and
        best_anchor
        >=
        CONFIRMED_ANCHOR_MEDIAN_CORRELATION
        and
        best_all
        is not None
        and
        best_all
        >=
        CONFIRMED_ALL_MEDIAN_CORRELATION
        and
        anchor_gain
        is not None
        and
        anchor_gain
        >=
        CONFIRMED_MINIMUM_ANCHOR_GAIN
        and
        all_gain
        is not None
        and
        all_gain
        >=
        CONFIRMED_MINIMUM_ALL_GAIN
    ):

        status = (
            "D1_FEATURE_WARMUP_STATE_CONTAMINATION_CONFIRMED"
        )

        reason = (
            "D1_TECHNICAL_FEATURE_ALIGNMENT_STRONGLY_"
            "RECOVERS_AFTER_EXCLUDING_EARLY_CURRENT_"
            "BROKER_HISTORY_STATE"
        )

        next_action = (
            "DESIGN_CAUSAL_D1_WARMUP_REQUIREMENT_OR_"
            "PORTABLE_STATE_BOOTSTRAP_BEFORE_FULL_MTF_UPDATE"
        )

    elif (
        best_cutoff_days
        >
        0
        and
        best_anchor
        is not None
        and
        best_anchor
        >=
        MATERIAL_ANCHOR_MEDIAN_CORRELATION
        and
        best_all
        is not None
        and
        best_all
        >=
        MATERIAL_ALL_MEDIAN_CORRELATION
        and
        anchor_gain
        is not None
        and
        anchor_gain
        >=
        MATERIAL_MINIMUM_ANCHOR_GAIN
        and
        all_gain
        is not None
        and
        all_gain
        >=
        MATERIAL_MINIMUM_ALL_GAIN
    ):

        status = (
            "D1_FEATURE_WARMUP_STATE_CONTAMINATION_MATERIAL"
        )

        reason = (
            "D1_FEATURE_ALIGNMENT_MATERIALLY_IMPROVES_"
            "WITH_HISTORY_AGE_BUT_DOES_NOT_REACH_"
            "NEAR_PORTABLE_LEVELS"
        )

        next_action = (
            "ISOLATE_NONCONVERGING_D1_FEATURES_AFTER_"
            "ADEQUATE_WARMUP_BEFORE_CONTRACT_DESIGN"
        )

    else:

        status = (
            "D1_FEATURE_WARMUP_STATE_NOT_SUFFICIENT"
        )

        reason = (
            "EXCLUDING_EARLY_HISTORY_DOES_NOT_"
            "SUFFICIENTLY_RESTORE_D1_TECHNICAL_"
            "FEATURE_CORRESPONDENCE"
        )

        next_action = (
            "ISOLATE_D1_FEATURE_FORMULA_OR_INPUT_FIELDS_"
            "THAT_REMAIN_NONPORTABLE_DESPITE_RAW_D1_ALIGNMENT"
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "baseline_cutoff_days": (
            0
        ),
        "baseline_anchor_median_correlation": (
            baseline_anchor
        ),
        "baseline_all_technical_median_correlation": (
            baseline_all
        ),
        "selected_cutoff_days": (
            best_cutoff_days
        ),
        "selected_daily_state_rows": int(
            best[
                "daily_state_rows"
            ]
        ),
        "selected_anchor_median_correlation": (
            best_anchor
        ),
        "selected_all_technical_median_correlation": (
            best_all
        ),
        "anchor_gain_vs_baseline": (
            anchor_gain
        ),
        "all_technical_gain_vs_baseline": (
            all_gain
        ),
        "warmup_state_contamination_confirmed": bool(
            status
            ==
            "D1_FEATURE_WARMUP_STATE_CONTAMINATION_CONFIRMED"
        ),
        "broker_specific_retraining_authorized": (
            False
        ),
        "full_mtf_portability_verdict_allowed": (
            False
        ),
        "test_evaluation_authorized": (
            False
        ),
        "next_action": (
            next_action
        ),
    }


def run_diagnostic(
) -> dict[str, Any]:

    mapped._validate_mapping_contract()

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

    technical_features = [
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
            technical_features
        )
        ==
        full.EXPECTED_TECHNICAL_COUNT_PER_TIMEFRAME,
        (
            "D1_TECHNICAL_FEATURE_COUNT_MISMATCH:"
            f"{len(technical_features)}"
        ),
    )

    for feature in (
        D1_ANCHOR_FEATURES
    ):

        _require(
            feature
            in
            technical_features,
            (
                "D1_ANCHOR_NOT_IN_TECHNICAL_CONTRACT:"
                f"{feature}"
            ),
        )

    frozen_train = (
        base
        ._load_frozen_train_only(
            training_dataset_path,
            technical_features,
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

    train_start = pd.Timestamp(
        frozen_train[
            "decision_time"
        ].min()
    )

    train_end = pd.Timestamp(
        frozen_train[
            "decision_time"
        ].max()
    )

    initialized = (
        mt5.initialize()
    )

    if not initialized:

        raise RuntimeError(
            (
                "MT5_INITIALIZE_FAILED:"
                f"{mt5.last_error()}"
            )
        )

    try:

        adapter = (
            base
            .BrokerCostAdapter(
                mt5
            )
        )

        broker_snapshot = (
            adapter.snapshot(
                include_m5_atr=False
            )
        )

        broker_symbol = str(
            broker_snapshot[
                "resolution"
            ][
                "broker_symbol"
            ]
        )

        broker_server = str(
            broker_snapshot[
                "broker_identity"
            ].get(
                "server",
                "",
            )
        )

        symbol_info = (
            mt5.symbol_info(
                broker_symbol
            )
        )

        _require(
            symbol_info
            is not None,
            (
                "MT5_SYMBOL_INFO_UNAVAILABLE:"
                f"{broker_symbol}"
            ),
        )

        if not bool(
            getattr(
                symbol_info,
                "visible",
                False,
            )
        ):

            selected = (
                mt5.symbol_select(
                    broker_symbol,
                    True,
                )
            )

            _require(
                bool(
                    selected
                ),
                (
                    "MT5_SYMBOL_SELECT_FAILED:"
                    f"{broker_symbol}:"
                    f"{mt5.last_error()}"
                ),
            )

        fetch_end = (
            train_end
            +
            pd.Timedelta(
                days=7
            )
        )

        rates = mt5.copy_rates_range(
            broker_symbol,
            mt5.TIMEFRAME_H1,
            H1_REQUEST_START.to_pydatetime(),
            fetch_end.to_pydatetime(),
        )

        raw_h1 = (
            base
            ._mt5_rates_frame(
                rates
            )
        )

        _require(
            not raw_h1.empty,
            "CURRENT_BROKER_H1_EMPTY",
        )

        raw_h1[
            "time"
        ] = (
            _canonical_time(
                raw_h1[
                    "time"
                ]
            )
        )

        raw_h1 = (
            raw_h1
            .sort_values(
                "time"
            )
            .reset_index(
                drop=True
            )
        )

        (
            canonical_h1,
            clock_meta,
        ) = (
            _clock_map_current_h1(
                raw_h1
            )
        )

        (
            synthetic_raw_d1,
            aggregation_meta,
        ) = (
            _build_synthetic_d1_raw(
                canonical_h1
            )
        )

        builder = (
            TrainingMatrixBuilder(
                canonical_root=(
                    CANONICAL_ROOT
                )
            )
        )

        (
            generated_d1,
            generation_meta,
        ) = (
            _generate_d1_features(
                builder=(
                    builder
                ),
                synthetic_raw_d1=(
                    synthetic_raw_d1
                ),
                technical_features=(
                    technical_features
                ),
            )
        )

        aligned = (
            _align_to_frozen_train(
                frozen_train=(
                    frozen_train
                ),
                generated_d1=(
                    generated_d1
                ),
                technical_features=(
                    technical_features
                ),
            )
        )

        daily_states = (
            _daily_state_frame(
                aligned
            )
        )

        first_available_time = pd.Timestamp(
            generated_d1[
                "available_time"
            ].min()
        )

        current_history_days_before_train = float(
            (
                train_start
                -
                first_available_time
            )
            .total_seconds()
            /
            86400.0
        )

        cutoff_documents = [
            _cutoff_document(
                daily_states=(
                    daily_states
                ),
                technical_features=(
                    technical_features
                ),
                first_available_time=(
                    first_available_time
                ),
                cutoff_days=(
                    cutoff_days
                ),
            )
            for cutoff_days
            in WARMUP_CUTOFF_DAYS
        ]

        decision = (
            _decision(
                cutoff_documents
            )
        )

        ranked = sorted(
            [
                document
                for document
                in cutoff_documents
                if bool(
                    document.get(
                        "sufficient_daily_state_rows",
                        False,
                    )
                )
            ],
            key=_candidate_score,
            reverse=True,
        )

        return {
            "valid": True,
            "reason": (
                "OK_XAUUSD_CURRENT_BROKER_D1_"
                "FEATURE_STATE_WARMUP_DIAGNOSTIC"
            ),
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "research_scope": (
                "D1_TECHNICAL_FEATURE_STATE_CONVERGENCE_"
                "USING_CONFIRMED_00UTC_H1_REAGGREGATION_"
                "TRAIN_ONLY_NO_LABELS"
            ),
            "prerequisite_contract": {
                "frozen_d1_session_close_hour_utc": (
                    CONFIRMED_D1_SESSION_CLOSE_HOUR_UTC
                ),
                "frozen_d1_label_day_shift": (
                    CONFIRMED_D1_LABEL_DAY_SHIFT
                ),
                "frozen_d1_boundary_status": (
                    "FROZEN_D1_FIXED_SESSION_BOUNDARY_CONFIRMED"
                ),
                "current_raw_d1_alignment_status": (
                    "CURRENT_H1_REAGGREGATED_D1_RAW_ALIGNMENT_CONFIRMED"
                ),
                "raw_d1_alignment_required_before_this_gate": (
                    True
                ),
            },
            "frozen_reference": {
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
                "train_start": (
                    train_start.isoformat()
                ),
                "train_end": (
                    train_end.isoformat()
                ),
            },
            "current_broker": {
                "canonical_symbol": (
                    "XAUUSD"
                ),
                "broker_symbol": (
                    broker_symbol
                ),
                "broker_server": (
                    broker_server
                ),
                "contract_fingerprint": (
                    broker_snapshot[
                        "contract_fingerprint"
                    ]
                ),
                "h1_requested_start": (
                    H1_REQUEST_START.isoformat()
                ),
                "raw_h1_rows_returned": int(
                    len(
                        raw_h1
                    )
                ),
                "canonical_h1_rows": int(
                    len(
                        canonical_h1
                    )
                ),
                "actual_canonical_h1_start": (
                    pd.Timestamp(
                        canonical_h1[
                            "time"
                        ].min()
                    ).isoformat()
                ),
                "actual_canonical_h1_end": (
                    pd.Timestamp(
                        canonical_h1[
                            "time"
                        ].max()
                    ).isoformat()
                ),
            },
            "history_depth": {
                "first_synthetic_d1_bar_time": (
                    pd.Timestamp(
                        synthetic_raw_d1[
                            "time"
                        ].min()
                    ).isoformat()
                ),
                "first_synthetic_d1_available_time": (
                    first_available_time.isoformat()
                ),
                "train_start": (
                    train_start.isoformat()
                ),
                "calendar_days_of_current_d1_history_before_train_start": (
                    current_history_days_before_train
                ),
                "unique_aligned_daily_state_rows": int(
                    len(
                        daily_states
                    )
                ),
            },
            "confirmed_clock_mapping": (
                clock_meta
            ),
            "synthetic_d1_aggregation": (
                aggregation_meta
            ),
            "d1_feature_generation": (
                generation_meta
            ),
            "diagnostic_contract": {
                "technical_feature_count": int(
                    len(
                        technical_features
                    )
                ),
                "anchor_feature_count": int(
                    len(
                        D1_ANCHOR_FEATURES
                    )
                ),
                "anchor_features": list(
                    D1_ANCHOR_FEATURES
                ),
                "warmup_cutoff_days": list(
                    WARMUP_CUTOFF_DAYS
                ),
                "minimum_daily_state_rows": (
                    MIN_DAILY_STATE_ROWS
                ),
                "comparison_unit": (
                    "UNIQUE_D1_AVAILABLE_STATE"
                ),
                "reason_for_daily_state_comparison": (
                    "AVOIDS_REPEATED_M5_DECISION_ROWS_"
                    "OVERWEIGHTING_THE_SAME_D1_STATE"
                ),
            },
            "thresholds": {
                "confirmed_anchor_median_correlation": (
                    CONFIRMED_ANCHOR_MEDIAN_CORRELATION
                ),
                "confirmed_all_median_correlation": (
                    CONFIRMED_ALL_MEDIAN_CORRELATION
                ),
                "confirmed_minimum_anchor_gain": (
                    CONFIRMED_MINIMUM_ANCHOR_GAIN
                ),
                "confirmed_minimum_all_gain": (
                    CONFIRMED_MINIMUM_ALL_GAIN
                ),
                "material_anchor_median_correlation": (
                    MATERIAL_ANCHOR_MEDIAN_CORRELATION
                ),
                "material_all_median_correlation": (
                    MATERIAL_ALL_MEDIAN_CORRELATION
                ),
                "material_minimum_anchor_gain": (
                    MATERIAL_MINIMUM_ANCHOR_GAIN
                ),
                "material_minimum_all_gain": (
                    MATERIAL_MINIMUM_ALL_GAIN
                ),
            },
            "decision": (
                decision
            ),
            "cutoff_results_chronological": (
                cutoff_documents
            ),
            "cutoff_ranking": [
                {
                    "rank": int(
                        index
                    ),
                    "cutoff_days_from_first_current_d1_state": (
                        document[
                            "cutoff_days_from_first_current_d1_state"
                        ]
                    ),
                    "cutoff_time": (
                        document[
                            "cutoff_time"
                        ]
                    ),
                    "daily_state_rows": (
                        document[
                            "daily_state_rows"
                        ]
                    ),
                    "anchor_median_correlation": (
                        document[
                            "anchor_median_correlation"
                        ]
                    ),
                    "all_technical_median_correlation": (
                        document[
                            "all_technical_median_correlation"
                        ]
                    ),
                    "anchor_correlation_ge_0_95_count": (
                        document[
                            "anchor_correlation_ge_0_95_count"
                        ]
                    ),
                    "all_technical_correlation_ge_0_95_count": (
                        document[
                            "all_technical_correlation_ge_0_95_count"
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
            "scientific_policy": {
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
                "native_current_broker_d1_used": (
                    False
                ),
                "current_broker_h1_used": (
                    True
                ),
                "current_d1_reconstructed_from_h1": (
                    True
                ),
                "confirmed_00utc_boundary_used": (
                    True
                ),
                "mt5_used": (
                    True
                ),
                "mt5_history_read_only": (
                    True
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
                "full_mtf_portability_verdict_allowed": (
                    False
                ),
                "test_evaluation_authorized": (
                    False
                ),
                "live_authorized": (
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
                "filesystem_paths_emitted": (
                    False
                ),
            },
            "next_decision_contract": {
                "if_warmup_state_contamination_confirmed": (
                    "DESIGN_CAUSAL_D1_WARMUP_REQUIREMENT_"
                    "OR_PORTABLE_STATE_BOOTSTRAP"
                ),
                "if_warmup_state_contamination_material": (
                    "ISOLATE_NONCONVERGING_D1_FEATURES_"
                    "AFTER_ADEQUATE_WARMUP"
                ),
                "if_warmup_not_sufficient": (
                    "ISOLATE_D1_FEATURE_FORMULAS_OR_INPUTS_"
                    "THAT_REMAIN_NONPORTABLE"
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

    finally:

        mt5.shutdown()


def main() -> int:

    try:

        result = (
            run_diagnostic()
        )

    except Exception as exc:

        try:
            mt5.shutdown()

        except Exception:
            pass

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_CURRENT_BROKER_D1_"
                        "FEATURE_STATE_WARMUP_DIAGNOSTIC_FAILED"
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