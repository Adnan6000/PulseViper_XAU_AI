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


ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


ANALYSIS_VERSION = (
    "XAUUSD_CURRENT_BROKER_D1_FULL_STATE_RECOVERY_V1"
)

FULL_AUDIT_MODULE = (
    "04_Testing."
    "analyze_xauusd_current_broker_full_mtf_portability"
)

FROZEN_D1_SOURCE_MODULE = (
    "04_Testing."
    "diagnose_xauusd_frozen_d1_source_aggregation"
)

FROZEN_D1_REPLAY_MODULE = (
    "04_Testing."
    "diagnose_xauusd_frozen_d1_feature_state_replay"
)

SHORT_SESSION_MODULE = (
    "04_Testing."
    "diagnose_xauusd_d1_short_session_state_gap"
)


full: Any = importlib.import_module(
    FULL_AUDIT_MODULE
)

source: Any = importlib.import_module(
    FROZEN_D1_SOURCE_MODULE
)

replay: Any = importlib.import_module(
    FROZEN_D1_REPLAY_MODULE
)

shortdiag: Any = importlib.import_module(
    SHORT_SESSION_MODULE
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


BASELINE_MIN_H1_BARS = 6

CORRECTED_MIN_H1_BARS = 1

SHORT_SESSION_MAX_H1_BARS = 5


H1_REQUEST_START = pd.Timestamp(
    "2010-01-01T00:00:00Z"
)


EXPECTED_D1_STATE_COUNT = 309

EXPECTED_SHORT_STATE_COUNT = 54

EXPECTED_REGULAR_STATE_COUNT = 255


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


FULL_ALIGNMENT_CONFIRMED_MEDIAN = 0.95

FULL_ALIGNMENT_MATERIAL_MEDIAN = 0.90

MIN_MATERIAL_MEDIAN_GAIN = 0.05

MIN_SHORT_RESIDUAL_GAP = 0.10

MIN_REQUIRED_FULL_STATE_FRACTION = 0.99


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
        <=
        1e-15
        or
        float(
            np.std(
                y
            )
        )
        <=
        1e-15
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


def _normalized_mae(
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
            "NORMALIZED_MAE_SHAPE_MISMATCH:"
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

    if not bool(
        finite.any()
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

    mae = float(
        np.mean(
            np.abs(
                x
                -
                y
            )
        )
    )

    scale = float(
        np.std(
            x
        )
    )

    denominator = max(
        scale,
        1e-12,
    )

    return float(
        mae
        /
        denominator
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

    for feature in (
        D1_ANCHOR_FEATURES
    ):

        _require(
            feature
            in
            features,
            (
                "D1_ANCHOR_NOT_IN_TECHNICAL_CONTRACT:"
                f"{feature}"
            ),
        )

    return (
        features
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
        canonical_time,
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
            canonical_time
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
            "duplicate_canonical_h1_rows": (
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


def _build_synthetic_d1(
    canonical_h1: pd.DataFrame,
    *,
    minimum_h1_bars: int,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

    _require(
        minimum_h1_bars
        >=
        1,
        (
            "INVALID_MINIMUM_H1_BARS:"
            f"{minimum_h1_bars}"
        ),
    )

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
        "session_bar_time"
    ] = (
        working[
            "time"
        ]
        .dt
        .floor(
            "D"
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
            "session_bar_time",
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
        "session_bar_time"
    ] = (
        _canonical_time(
            grouped[
                "session_bar_time"
            ]
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
            minimum_h1_bars
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    _require(
        not grouped.empty,
        (
            "NO_SYNTHETIC_D1_SESSIONS:"
            f"{minimum_h1_bars}"
        ),
    )

    output_columns = [
        "session_bar_time",
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
        .rename(
            columns={
                "session_bar_time": (
                    "time"
                )
            }
        )
        .sort_values(
            "time"
        )
        .reset_index(
            drop=True
        )
    )

    raw_d1[
        "time"
    ] = (
        _canonical_time(
            raw_d1[
                "time"
            ]
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
            f"{minimum_h1_bars}:"
            f"{duplicate_count}"
        ),
    )

    retained_counts = (
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
            "minimum_h1_bars": int(
                minimum_h1_bars
            ),
            "sessions_before_filter": (
                sessions_before_filter
            ),
            "sessions_after_filter": int(
                len(
                    raw_d1
                )
            ),
            "sessions_removed": int(
                sessions_before_filter
                -
                len(
                    raw_d1
                )
            ),
            "minimum_retained_h1_bar_count": int(
                np.min(
                    retained_counts
                )
            ),
            "median_retained_h1_bar_count": float(
                np.median(
                    retained_counts
                )
            ),
            "maximum_retained_h1_bar_count": int(
                np.max(
                    retained_counts
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

    duplicate_count = int(
        result[
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

    lag_minutes = (
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

    unique_lags = sorted(
        {
            float(
                value
            )
            for value
            in lag_minutes
            .dropna()
            .tolist()
        }
    )

    return (
        result,
        {
            "generated_rows": int(
                len(
                    result
                )
            ),
            "duplicate_available_time_rows": (
                duplicate_count
            ),
            "unique_available_minus_bar_time_minutes": (
                unique_lags
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


def _required_state_table(
    *,
    frozen_states: pd.DataFrame,
    frozen_h1: pd.DataFrame,
) -> pd.DataFrame:

    state_table = (
        frozen_states[
            [
                "frozen_available_time"
            ]
        ]
        .copy()
    )

    state_table[
        "d1_bar_time"
    ] = (
        state_table[
            "frozen_available_time"
        ]
        -
        pd.Timedelta(
            days=1
        )
    )

    state_table[
        "d1_bar_time"
    ] = (
        _canonical_time(
            state_table[
                "d1_bar_time"
            ]
        )
    )

    frozen_census = (
        shortdiag
        ._session_census(
            frozen_h1
        )
    )

    frozen_counts = (
        frozen_census[
            [
                "session_bar_time",
                "h1_bar_count",
            ]
        ]
        .rename(
            columns={
                "session_bar_time": (
                    "d1_bar_time"
                ),
                "h1_bar_count": (
                    "frozen_h1_bar_count"
                ),
            }
        )
        .copy()
    )

    frozen_counts[
        "d1_bar_time"
    ] = (
        _canonical_time(
            frozen_counts[
                "d1_bar_time"
            ]
        )
    )

    state_table = (
        state_table
        .merge(
            frozen_counts,
            on="d1_bar_time",
            how="left",
            validate="one_to_one",
        )
        .sort_values(
            "frozen_available_time"
        )
        .reset_index(
            drop=True
        )
    )

    missing_counts = int(
        state_table[
            "frozen_h1_bar_count"
        ]
        .isna()
        .sum()
    )

    _require(
        missing_counts
        ==
        0,
        (
            "FROZEN_H1_STATE_COUNTS_MISSING:"
            f"{missing_counts}"
        ),
    )

    state_table[
        "is_short_session"
    ] = (
        pd.to_numeric(
            state_table[
                "frozen_h1_bar_count"
            ],
            errors="raise",
        )
        <=
        SHORT_SESSION_MAX_H1_BARS
    )

    state_count = int(
        len(
            state_table
        )
    )

    short_count = int(
        state_table[
            "is_short_session"
        ]
        .sum()
    )

    regular_count = int(
        (
            ~state_table[
                "is_short_session"
            ]
        )
        .sum()
    )

    _require(
        state_count
        ==
        EXPECTED_D1_STATE_COUNT,
        (
            "D1_STATE_COUNT_MISMATCH:"
            f"{state_count}:"
            f"{EXPECTED_D1_STATE_COUNT}"
        ),
    )

    _require(
        short_count
        ==
        EXPECTED_SHORT_STATE_COUNT,
        (
            "D1_SHORT_STATE_COUNT_MISMATCH:"
            f"{short_count}:"
            f"{EXPECTED_SHORT_STATE_COUNT}"
        ),
    )

    _require(
        regular_count
        ==
        EXPECTED_REGULAR_STATE_COUNT,
        (
            "D1_REGULAR_STATE_COUNT_MISMATCH:"
            f"{regular_count}:"
            f"{EXPECTED_REGULAR_STATE_COUNT}"
        ),
    )

    return (
        state_table
    )


def _align_generated_to_frozen(
    *,
    frozen_states: pd.DataFrame,
    state_table: pd.DataFrame,
    generated: pd.DataFrame,
    technical_features: Sequence[
        str
    ],
) -> pd.DataFrame:

    frozen = (
        frozen_states[
            [
                "frozen_available_time",
                *technical_features,
            ]
        ]
        .copy()
    )

    frozen = (
        frozen
        .merge(
            state_table[
                [
                    "frozen_available_time",
                    "d1_bar_time",
                    "frozen_h1_bar_count",
                    "is_short_session",
                ]
            ],
            on="frozen_available_time",
            how="left",
            validate="one_to_one",
        )
    )

    current = (
        generated[
            [
                "available_time",
                *technical_features,
            ]
        ]
        .copy()
    )

    rename_map = {
        feature: (
            feature
            +
            "_current"
        )
        for feature
        in technical_features
    }

    current = (
        current.rename(
            columns=(
                rename_map
            )
        )
    )

    aligned = (
        frozen
        .merge(
            current,
            left_on="frozen_available_time",
            right_on="available_time",
            how="left",
            validate="one_to_one",
        )
        .sort_values(
            "frozen_available_time"
        )
        .reset_index(
            drop=True
        )
    )

    for feature in (
        technical_features
    ):

        aligned.rename(
            columns={
                feature: (
                    feature
                    +
                    "_frozen"
                )
            },
            inplace=True,
        )

    aligned[
        "state_matched"
    ] = (
        aligned[
            "available_time"
        ]
        .notna()
    )

    return (
        aligned
    )


def _feature_metrics(
    *,
    aligned: pd.DataFrame,
    technical_features: Sequence[
        str
    ],
    mask: pd.Series,
) -> dict[str, Any]:

    subset = (
        aligned.loc[
            mask
            &
            aligned[
                "state_matched"
            ]
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    rows = int(
        len(
            subset
        )
    )

    correlations: dict[
        str,
        float | None,
    ] = {}

    normalized_maes: dict[
        str,
        float | None,
    ] = {}

    for feature in (
        technical_features
    ):

        frozen_column = (
            feature
            +
            "_frozen"
        )

        current_column = (
            feature
            +
            "_current"
        )

        correlations[
            feature
        ] = (
            _correlation(
                subset[
                    frozen_column
                ],
                subset[
                    current_column
                ],
            )
        )

        normalized_maes[
            feature
        ] = (
            _normalized_mae(
                subset[
                    frozen_column
                ],
                subset[
                    current_column
                ],
            )
        )

    correlation_values = list(
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
        "rows": (
            rows
        ),
        "all_technical_median_correlation": (
            _median_finite(
                correlation_values
            )
        ),
        "anchor_median_correlation": (
            _median_finite(
                anchor_values
            )
        ),
        "all_technical_correlation_ge_0_80_count": (
            _count_at_least(
                correlation_values,
                0.80,
            )
        ),
        "all_technical_correlation_ge_0_90_count": (
            _count_at_least(
                correlation_values,
                0.90,
            )
        ),
        "all_technical_correlation_ge_0_95_count": (
            _count_at_least(
                correlation_values,
                0.95,
            )
        ),
        "all_technical_correlation_ge_0_98_count": (
            _count_at_least(
                correlation_values,
                0.98,
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
        "median_normalized_mae": (
            _median_finite(
                list(
                    normalized_maes.values()
                )
            )
        ),
        "feature_correlations": (
            correlations
        ),
        "feature_normalized_mae": (
            normalized_maes
        ),
    }


def _comparison_document(
    *,
    aligned: pd.DataFrame,
    technical_features: Sequence[
        str
    ],
) -> dict[str, Any]:

    all_mask = pd.Series(
        True,
        index=aligned.index,
        dtype=bool,
    )

    short_mask = (
        aligned[
            "is_short_session"
        ]
        .fillna(
            False
        )
        .astype(
            bool
        )
    )

    regular_mask = (
        ~short_mask
    )

    matched_state_count = int(
        aligned[
            "state_matched"
        ]
        .sum()
    )

    missing_state_count = int(
        (
            ~aligned[
                "state_matched"
            ]
        )
        .sum()
    )

    return {
        "required_state_count": int(
            len(
                aligned
            )
        ),
        "matched_state_count": (
            matched_state_count
        ),
        "missing_state_count": (
            missing_state_count
        ),
        "matched_state_fraction": float(
            matched_state_count
            /
            len(
                aligned
            )
        ),
        "all_states": (
            _feature_metrics(
                aligned=(
                    aligned
                ),
                technical_features=(
                    technical_features
                ),
                mask=(
                    all_mask
                ),
            )
        ),
        "regular_sessions": (
            _feature_metrics(
                aligned=(
                    aligned
                ),
                technical_features=(
                    technical_features
                ),
                mask=(
                    regular_mask
                ),
            )
        ),
        "short_sessions": (
            _feature_metrics(
                aligned=(
                    aligned
                ),
                technical_features=(
                    technical_features
                ),
                mask=(
                    short_mask
                ),
            )
        ),
    }


def _residual_feature_ranking(
    corrected_comparison: Mapping[
        str,
        Any,
    ],
) -> list[dict[str, Any]]:

    all_states = (
        corrected_comparison[
            "all_states"
        ]
    )

    regular = (
        corrected_comparison[
            "regular_sessions"
        ]
    )

    short = (
        corrected_comparison[
            "short_sessions"
        ]
    )

    all_correlations = (
        all_states[
            "feature_correlations"
        ]
    )

    regular_correlations = (
        regular[
            "feature_correlations"
        ]
    )

    short_correlations = (
        short[
            "feature_correlations"
        ]
    )

    documents: list[
        dict[str, Any]
    ] = []

    for feature in (
        all_correlations
    ):

        all_corr = (
            _safe_float(
                all_correlations[
                    feature
                ]
            )
        )

        regular_corr = (
            _safe_float(
                regular_correlations[
                    feature
                ]
            )
        )

        short_corr = (
            _safe_float(
                short_correlations[
                    feature
                ]
            )
        )

        short_gap: (
            float
            |
            None
        ) = None

        if (
            regular_corr
            is not None
            and
            short_corr
            is not None
        ):

            short_gap = float(
                regular_corr
                -
                short_corr
            )

        documents.append(
            {
                "feature": (
                    feature
                ),
                "all_state_correlation": (
                    all_corr
                ),
                "regular_session_correlation": (
                    regular_corr
                ),
                "short_session_correlation": (
                    short_corr
                ),
                "regular_minus_short_correlation": (
                    short_gap
                ),
            }
        )

    def rank_key(
        document: Mapping[
            str,
            Any,
        ],
    ) -> tuple[
        float,
        float,
    ]:

        all_corr = (
            _safe_float(
                document.get(
                    "all_state_correlation"
                )
            )
        )

        short_gap = (
            _safe_float(
                document.get(
                    "regular_minus_short_correlation"
                )
            )
        )

        return (
            (
                all_corr
                if all_corr
                is not None
                else -2.0
            ),
            (
                -short_gap
                if short_gap
                is not None
                else 0.0
            ),
        )

    return sorted(
        documents,
        key=rank_key,
    )


def _decision(
    *,
    baseline: Mapping[
        str,
        Any,
    ],
    corrected: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    baseline_all = (
        baseline[
            "all_states"
        ]
    )

    corrected_all = (
        corrected[
            "all_states"
        ]
    )

    corrected_regular = (
        corrected[
            "regular_sessions"
        ]
    )

    corrected_short = (
        corrected[
            "short_sessions"
        ]
    )

    baseline_all_median = (
        _safe_float(
            baseline_all.get(
                "all_technical_median_correlation"
            )
        )
    )

    baseline_anchor_median = (
        _safe_float(
            baseline_all.get(
                "anchor_median_correlation"
            )
        )
    )

    corrected_all_median = (
        _safe_float(
            corrected_all.get(
                "all_technical_median_correlation"
            )
        )
    )

    corrected_anchor_median = (
        _safe_float(
            corrected_all.get(
                "anchor_median_correlation"
            )
        )
    )

    regular_median = (
        _safe_float(
            corrected_regular.get(
                "all_technical_median_correlation"
            )
        )
    )

    regular_anchor = (
        _safe_float(
            corrected_regular.get(
                "anchor_median_correlation"
            )
        )
    )

    short_median = (
        _safe_float(
            corrected_short.get(
                "all_technical_median_correlation"
            )
        )
    )

    short_anchor = (
        _safe_float(
            corrected_short.get(
                "anchor_median_correlation"
            )
        )
    )

    all_gain: (
        float
        |
        None
    ) = None

    anchor_gain: (
        float
        |
        None
    ) = None

    if (
        baseline_all_median
        is not None
        and
        corrected_all_median
        is not None
    ):

        all_gain = float(
            corrected_all_median
            -
            baseline_all_median
        )

    if (
        baseline_anchor_median
        is not None
        and
        corrected_anchor_median
        is not None
    ):

        anchor_gain = float(
            corrected_anchor_median
            -
            baseline_anchor_median
        )

    short_residual_gap: (
        float
        |
        None
    ) = None

    if (
        regular_median
        is not None
        and
        short_median
        is not None
    ):

        short_residual_gap = float(
            regular_median
            -
            short_median
        )

    corrected_state_fraction = (
        _safe_float(
            corrected.get(
                "matched_state_fraction"
            )
        )
    )

    if (
        corrected_state_fraction
        is None
        or
        corrected_state_fraction
        <
        MIN_REQUIRED_FULL_STATE_FRACTION
    ):

        status = (
            "D1_FULL_STATE_RECOVERY_INSUFFICIENT_COVERAGE"
        )

        reason = (
            "CORRECTED_ONE_BAR_RECONSTRUCTION_DOES_NOT_"
            "RECOVER_NEARLY_ALL_REQUIRED_FROZEN_D1_STATES"
        )

        next_action = (
            "RESOLVE_REMAINING_CURRENT_D1_STATE_COVERAGE_GAPS"
        )

    elif (
        corrected_all_median
        is not None
        and
        corrected_all_median
        >=
        FULL_ALIGNMENT_CONFIRMED_MEDIAN
        and
        corrected_anchor_median
        is not None
        and
        corrected_anchor_median
        >=
        FULL_ALIGNMENT_CONFIRMED_MEDIAN
    ):

        status = (
            "D1_FULL_309_STATE_FEATURE_ALIGNMENT_CONFIRMED"
        )

        reason = (
            "RESTORING_ALL_ONE_BAR_OR_GREATER_00UTC_D1_"
            "SESSIONS_RECOVERS_NEAR_PORTABLE_D1_FEATURE_ALIGNMENT"
        )

        next_action = (
            "UPDATE_FULL_MTF_PORTABILITY_AUDIT_TO_USE_"
            "CONFIRMED_D1_RECONSTRUCTION_SEMANTICS"
        )

    elif (
        regular_median
        is not None
        and
        regular_median
        >=
        FULL_ALIGNMENT_CONFIRMED_MEDIAN
        and
        regular_anchor
        is not None
        and
        regular_anchor
        >=
        FULL_ALIGNMENT_CONFIRMED_MEDIAN
        and
        short_residual_gap
        is not None
        and
        short_residual_gap
        >=
        MIN_SHORT_RESIDUAL_GAP
    ):

        status = (
            "D1_SHORT_SESSION_MICROSTRUCTURE_RESIDUAL_CONFIRMED"
        )

        reason = (
            "FULL_STATE_SEQUENCE_IS_RESTORED_BUT_REMAINING_"
            "D1_FEATURE_ERROR_IS_CONCENTRATED_IN_SHORT_"
            "BROKER_DEPENDENT_SESSIONS"
        )

        next_action = (
            "DESIGN_PORTABLE_SHORT_SESSION_D1_POLICY_BEFORE_"
            "FULL_MTF_CONTRACT_UPDATE"
        )

    elif (
        corrected_all_median
        is not None
        and
        corrected_all_median
        >=
        FULL_ALIGNMENT_MATERIAL_MEDIAN
        and
        corrected_anchor_median
        is not None
        and
        corrected_anchor_median
        >=
        FULL_ALIGNMENT_MATERIAL_MEDIAN
        and
        all_gain
        is not None
        and
        all_gain
        >=
        MIN_MATERIAL_MEDIAN_GAIN
        and
        anchor_gain
        is not None
        and
        anchor_gain
        >=
        MIN_MATERIAL_MEDIAN_GAIN
    ):

        status = (
            "D1_FULL_STATE_SEQUENCE_MATERIAL_RECOVERY"
        )

        reason = (
            "RESTORING_SHORT_D1_STATES_MATERIALLY_IMPROVES_"
            "FEATURE_ALIGNMENT_BUT_RESIDUAL_NONPORTABILITY_REMAINS"
        )

        next_action = (
            "ISOLATE_RESIDUAL_D1_FEATURES_AND_SHORT_SESSION_"
            "SENSITIVITY_BEFORE_FULL_MTF_UPDATE"
        )

    else:

        status = (
            "D1_FEATURE_RESIDUAL_REMAINS_BROAD_AFTER_STATE_RECOVERY"
        )

        reason = (
            "RESTORING_THE_FULL_309_STATE_SEQUENCE_DOES_NOT_"
            "SUFFICIENTLY_RECOVER_D1_TECHNICAL_FEATURE_ALIGNMENT"
        )

        next_action = (
            "ISOLATE_D1_FEATURE_FAMILIES_REMAINING_NONPORTABLE_"
            "AFTER_EXACT_STATE_SEQUENCE_RESTORATION"
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "baseline_minimum_h1_bars": (
            BASELINE_MIN_H1_BARS
        ),
        "corrected_minimum_h1_bars": (
            CORRECTED_MIN_H1_BARS
        ),
        "baseline_matched_state_count": int(
            baseline[
                "matched_state_count"
            ]
        ),
        "corrected_matched_state_count": int(
            corrected[
                "matched_state_count"
            ]
        ),
        "corrected_matched_state_fraction": (
            corrected_state_fraction
        ),
        "baseline_all_technical_median_correlation": (
            baseline_all_median
        ),
        "corrected_all_technical_median_correlation": (
            corrected_all_median
        ),
        "all_technical_median_correlation_gain": (
            all_gain
        ),
        "baseline_anchor_median_correlation": (
            baseline_anchor_median
        ),
        "corrected_anchor_median_correlation": (
            corrected_anchor_median
        ),
        "anchor_median_correlation_gain": (
            anchor_gain
        ),
        "corrected_regular_session_median_correlation": (
            regular_median
        ),
        "corrected_regular_anchor_median_correlation": (
            regular_anchor
        ),
        "corrected_short_session_median_correlation": (
            short_median
        ),
        "corrected_short_anchor_median_correlation": (
            short_anchor
        ),
        "regular_minus_short_median_correlation": (
            short_residual_gap
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
        replay
        ._frozen_d1_states(
            frozen_train=(
                frozen_train
            ),
            technical_features=(
                technical_features
            ),
        )
    )

    _require(
        len(
            frozen_states
        )
        ==
        EXPECTED_D1_STATE_COUNT,
        (
            "FROZEN_D1_STATE_COUNT_MISMATCH:"
            f"{len(frozen_states)}:"
            f"{EXPECTED_D1_STATE_COUNT}"
        ),
    )

    h1_snapshot = (
        source
        ._snapshot_document(
            manifest,
            "H1",
        )
    )

    (
        frozen_h1_path,
        frozen_h1_resolution,
    ) = (
        source
        ._resolve_snapshot_file(
            h1_snapshot
        )
    )

    frozen_h1 = (
        source
        ._read_snapshot_frame(
            frozen_h1_path,
            h1_snapshot,
        )
    )

    state_table = (
        _required_state_table(
            frozen_states=(
                frozen_states
            ),
            frozen_h1=(
                frozen_h1
            ),
        )
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
            baseline_raw_d1,
            baseline_aggregation_meta,
        ) = (
            _build_synthetic_d1(
                canonical_h1,
                minimum_h1_bars=(
                    BASELINE_MIN_H1_BARS
                ),
            )
        )

        (
            corrected_raw_d1,
            corrected_aggregation_meta,
        ) = (
            _build_synthetic_d1(
                canonical_h1,
                minimum_h1_bars=(
                    CORRECTED_MIN_H1_BARS
                ),
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
            baseline_generated,
            baseline_generation_meta,
        ) = (
            _generate_d1_features(
                builder=(
                    builder
                ),
                synthetic_raw_d1=(
                    baseline_raw_d1
                ),
                technical_features=(
                    technical_features
                ),
            )
        )

        (
            corrected_generated,
            corrected_generation_meta,
        ) = (
            _generate_d1_features(
                builder=(
                    builder
                ),
                synthetic_raw_d1=(
                    corrected_raw_d1
                ),
                technical_features=(
                    technical_features
                ),
            )
        )

        baseline_aligned = (
            _align_generated_to_frozen(
                frozen_states=(
                    frozen_states
                ),
                state_table=(
                    state_table
                ),
                generated=(
                    baseline_generated
                ),
                technical_features=(
                    technical_features
                ),
            )
        )

        corrected_aligned = (
            _align_generated_to_frozen(
                frozen_states=(
                    frozen_states
                ),
                state_table=(
                    state_table
                ),
                generated=(
                    corrected_generated
                ),
                technical_features=(
                    technical_features
                ),
            )
        )

        baseline_comparison = (
            _comparison_document(
                aligned=(
                    baseline_aligned
                ),
                technical_features=(
                    technical_features
                ),
            )
        )

        corrected_comparison = (
            _comparison_document(
                aligned=(
                    corrected_aligned
                ),
                technical_features=(
                    technical_features
                ),
            )
        )

        residual_ranking = (
            _residual_feature_ranking(
                corrected_comparison
            )
        )

        decision = (
            _decision(
                baseline=(
                    baseline_comparison
                ),
                corrected=(
                    corrected_comparison
                ),
            )
        )

        return {
            "valid": True,
            "reason": (
                "OK_XAUUSD_CURRENT_BROKER_D1_"
                "FULL_STATE_RECOVERY_DIAGNOSTIC"
            ),
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "research_scope": (
                "CURRENT_BROKER_D1_BASELINE_GE6_VS_"
                "CORRECTED_GE1_SESSION_SEQUENCE_"
                "AGAINST_EXACT_FROZEN_309_D1_STATES"
            ),
            "prerequisite_contract": {
                "frozen_d1_feature_state_replay_status": (
                    "FROZEN_D1_FEATURE_STATE_REPLAY_CONFIRMED"
                ),
                "frozen_d1_exact_feature_replay_count": (
                    43
                ),
                "frozen_d1_exact_state_count": (
                    EXPECTED_D1_STATE_COUNT
                ),
                "d1_short_session_state_gap_status": (
                    "D1_SHORT_SESSION_STATE_GAP_CONFIRMED"
                ),
                "short_state_count": (
                    EXPECTED_SHORT_STATE_COUNT
                ),
                "regular_state_count": (
                    EXPECTED_REGULAR_STATE_COUNT
                ),
                "confirmed_d1_available_lag_minutes": (
                    1440
                ),
                "confirmed_d1_bar_boundary_utc": (
                    "00:00"
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
                "unique_d1_state_count": int(
                    len(
                        frozen_states
                    )
                ),
                "frozen_state_meta": (
                    frozen_state_meta
                ),
                "frozen_h1_hash_validated": (
                    True
                ),
                "frozen_h1_resolution": (
                    frozen_h1_resolution
                ),
                "filesystem_paths_emitted": (
                    False
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
                "raw_h1_rows": int(
                    len(
                        raw_h1
                    )
                ),
                "canonical_h1_rows": int(
                    len(
                        canonical_h1
                    )
                ),
                "canonical_h1_start": (
                    pd.Timestamp(
                        canonical_h1[
                            "time"
                        ].min()
                    ).isoformat()
                ),
                "canonical_h1_end": (
                    pd.Timestamp(
                        canonical_h1[
                            "time"
                        ].max()
                    ).isoformat()
                ),
            },
            "confirmed_clock_mapping": (
                clock_meta
            ),
            "baseline_ge6_reconstruction": {
                "aggregation": (
                    baseline_aggregation_meta
                ),
                "feature_generation": (
                    baseline_generation_meta
                ),
                "comparison": (
                    baseline_comparison
                ),
            },
            "corrected_ge1_reconstruction": {
                "aggregation": (
                    corrected_aggregation_meta
                ),
                "feature_generation": (
                    corrected_generation_meta
                ),
                "comparison": (
                    corrected_comparison
                ),
            },
            "residual_feature_ranking_lowest_first": (
                residual_ranking
            ),
            "thresholds": {
                "full_alignment_confirmed_median": (
                    FULL_ALIGNMENT_CONFIRMED_MEDIAN
                ),
                "full_alignment_material_median": (
                    FULL_ALIGNMENT_MATERIAL_MEDIAN
                ),
                "minimum_material_median_gain": (
                    MIN_MATERIAL_MEDIAN_GAIN
                ),
                "minimum_short_residual_gap": (
                    MIN_SHORT_RESIDUAL_GAP
                ),
                "minimum_required_full_state_fraction": (
                    MIN_REQUIRED_FULL_STATE_FRACTION
                ),
            },
            "decision": (
                decision
            ),
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
                "current_broker_h1_used": (
                    True
                ),
                "native_current_broker_d1_used": (
                    False
                ),
                "current_d1_reconstructed_from_h1": (
                    True
                ),
                "baseline_ge6_reconstruction_tested": (
                    True
                ),
                "corrected_ge1_reconstruction_tested": (
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
                "test_evaluation_authorized": (
                    False
                ),
                "full_mtf_portability_verdict_allowed": (
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
                "if_full_309_alignment_confirmed": (
                    "UPDATE_FULL_MTF_PORTABILITY_AUDIT_"
                    "TO_USE_CONFIRMED_D1_RECONSTRUCTION_SEMANTICS"
                ),
                "if_short_session_microstructure_residual_confirmed": (
                    "DESIGN_PORTABLE_SHORT_SESSION_D1_POLICY_"
                    "BEFORE_FULL_MTF_CONTRACT_UPDATE"
                ),
                "if_material_recovery_only": (
                    "ISOLATE_RESIDUAL_D1_FEATURES_AND_"
                    "SHORT_SESSION_SENSITIVITY"
                ),
                "if_broad_residual_remains": (
                    "ISOLATE_D1_FEATURE_FAMILIES_AFTER_"
                    "EXACT_STATE_SEQUENCE_RESTORATION"
                ),
                "previous_warmup_file_remains_uncommitted": (
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
                        "FULL_STATE_RECOVERY_DIAGNOSTIC_FAILED"
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