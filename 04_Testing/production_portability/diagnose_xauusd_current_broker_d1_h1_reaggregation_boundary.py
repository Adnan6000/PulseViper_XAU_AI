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
    "XAUUSD_CURRENT_BROKER_D1_H1_REAGGREGATION_BOUNDARY_V1"
)

FULL_AUDIT_MODULE = (
    "04_Testing."
    "analyze_xauusd_current_broker_full_mtf_portability"
)


full: Any = importlib.import_module(
    FULL_AUDIT_MODULE
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


SESSION_CLOSE_HOURS_UTC = tuple(
    range(
        24
    )
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


EXPECTED_D1_TECHNICAL_FEATURE_COUNT = 43

EXPECTED_TRAIN_ROWS = 69966

MIN_H1_BARS_PER_SYNTHETIC_D1 = 6

MIN_MATCHED_TRAIN_ROWS = 5000


CONFIRMED_ANCHOR_MEDIAN_CORRELATION = 0.90

CONFIRMED_ALL_MEDIAN_CORRELATION = 0.90

LIKELY_ANCHOR_MEDIAN_CORRELATION = 0.85

LIKELY_ALL_MEDIAN_CORRELATION = 0.85

MIN_CONFIRMED_ANCHOR_GAIN = 0.10

MIN_LIKELY_ANCHOR_GAIN = 0.075


NATIVE_REFERENCE_DIAGNOSTIC_VERSION = (
    "XAUUSD_CURRENT_BROKER_D1_AVAILABILITY_ALIGNMENT_V1"
)

NATIVE_REFERENCE_ANCHOR_MEDIAN_CORRELATION = (
    0.7614129142011312
)

NATIVE_REFERENCE_ALL_MEDIAN_CORRELATION = (
    0.7832796548585856
)


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


def _technical_feature_names(
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
        EXPECTED_D1_TECHNICAL_FEATURE_COUNT,
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


def _map_h1_to_canonical_market_time(
    raw_h1: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

    _require(
        "time"
        in raw_h1.columns,
        "H1_TIME_MISSING",
    )

    mapped_h1 = (
        raw_h1.copy()
    )

    mapped_h1[
        "source_broker_time"
    ] = (
        _canonical_time(
            mapped_h1[
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
            mapped_h1[
                "source_broker_time"
            ]
        )
    )

    mapped_h1[
        "market_time"
    ] = (
        _canonical_time(
            market_time
        )
    )

    duplicate_count = int(
        mapped_h1[
            "market_time"
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
            "H1_CANONICAL_MARKET_TIME_DUPLICATES:"
            f"{duplicate_count}"
        ),
    )

    mapped_h1 = (
        mapped_h1
        .sort_values(
            "market_time"
        )
        .reset_index(
            drop=True
        )
    )

    return (
        mapped_h1,
        {
            **mapping_meta,
            "duplicate_market_time_rows": (
                duplicate_count
            ),
            "source_time_dtype": (
                str(
                    mapped_h1[
                        "source_broker_time"
                    ].dtype
                )
            ),
            "market_time_dtype": (
                str(
                    mapped_h1[
                        "market_time"
                    ].dtype
                )
            ),
        },
    )


def _session_close_time(
    market_time: pd.Series,
    *,
    close_hour_utc: int,
) -> pd.Series:

    _require(
        0
        <=
        close_hour_utc
        <=
        23,
        (
            "INVALID_SESSION_CLOSE_HOUR:"
            f"{close_hour_utc}"
        ),
    )

    canonical = (
        _canonical_time(
            market_time
        )
    )

    close_offset = pd.Timedelta(
        hours=close_hour_utc
    )

    shifted = (
        canonical
        -
        close_offset
    )

    session_close = (
        shifted.dt.floor(
            "D"
        )
        +
        pd.Timedelta(
            days=1
        )
        +
        close_offset
    )

    return (
        _canonical_time(
            session_close
        )
    )


def _synthetic_d1_raw(
    canonical_h1: pd.DataFrame,
    *,
    close_hour_utc: int,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

    required_columns = {
        "market_time",
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
            "H1_REQUIRED_COLUMNS_MISSING:"
            f"{missing}"
        ),
    )

    working = (
        canonical_h1.copy()
    )

    working[
        "session_close"
    ] = (
        _session_close_time(
            working[
                "market_time"
            ],
            close_hour_utc=(
                close_hour_utc
            ),
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
        "market_time": "count",
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
                "market_time": (
                    "h1_bar_count"
                ),
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

    before_minimum_filter = int(
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
        (
            "NO_SYNTHETIC_D1_SESSIONS:"
            f"{close_hour_utc}"
        ),
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

    duplicate_time_count = int(
        raw_d1[
            "time"
        ]
        .duplicated(
            keep=False
        )
        .sum()
    )

    _require(
        duplicate_time_count
        ==
        0,
        (
            "SYNTHETIC_D1_TIME_DUPLICATES:"
            f"{close_hour_utc}:"
            f"{duplicate_time_count}"
        ),
    )

    count_values = (
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
            "close_hour_utc": int(
                close_hour_utc
            ),
            "sessions_before_minimum_bar_filter": (
                before_minimum_filter
            ),
            "sessions_after_minimum_bar_filter": int(
                len(
                    raw_d1
                )
            ),
            "minimum_h1_bars_per_session": (
                MIN_H1_BARS_PER_SYNTHETIC_D1
            ),
            "median_h1_bars_per_session": float(
                np.median(
                    count_values
                )
            ),
            "minimum_observed_h1_bars_per_session": int(
                np.min(
                    count_values
                )
            ),
            "maximum_observed_h1_bars_per_session": int(
                np.max(
                    count_values
                )
            ),
            "duplicate_synthetic_d1_time_rows": (
                duplicate_time_count
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
            frame=synthetic_raw_d1,
            timeframe="D1",
        )
    )

    _require(
        isinstance(
            generated,
            pd.DataFrame,
        ),
        "SYNTHETIC_D1_GENERATOR_NOT_DATAFRAME",
    )

    required = {
        "time",
        *technical_features,
    }

    missing = sorted(
        required
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
            "SYNTHETIC_D1_GENERATED_FEATURES_MISSING:"
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

    duplicate_available_count = int(
        generated[
            "available_time"
        ]
        .duplicated(
            keep=False
        )
        .sum()
    )

    _require(
        duplicate_available_count
        ==
        0,
        (
            "SYNTHETIC_D1_AVAILABLE_TIME_DUPLICATES:"
            f"{duplicate_available_count}"
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
            "raw_synthetic_rows": int(
                len(
                    synthetic_raw_d1
                )
            ),
            "generated_rows": int(
                len(
                    generated
                )
            ),
            "usable_rows": int(
                len(
                    output
                )
            ),
            "duplicate_available_time_rows": (
                duplicate_available_count
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
        },
    )


def _align_to_frozen_train(
    *,
    frozen_train: pd.DataFrame,
    generated_features: pd.DataFrame,
    technical_features: Sequence[
        str
    ],
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

    left = (
        frozen_train[
            [
                "decision_time"
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
        generated_features[
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
            "SYNTHETIC_D1_ASOF_DTYPE_MISMATCH:"
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
    )

    aligned[
        "d1_age_minutes"
    ] = (
        (
            aligned[
                "decision_time"
            ]
            -
            aligned[
                "available_time"
            ]
        )
        .dt
        .total_seconds()
        /
        60.0
    ).astype(
        "float64"
    )

    negative_age_count = int(
        (
            aligned[
                "d1_age_minutes"
            ]
            <
            0
        )
        .fillna(
            False
        )
        .sum()
    )

    _require(
        negative_age_count
        ==
        0,
        (
            "SYNTHETIC_D1_NEGATIVE_AGE_ROWS:"
            f"{negative_age_count}"
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
        >=
        MIN_MATCHED_TRAIN_ROWS,
        (
            "SYNTHETIC_D1_MATCHED_ROWS_TOO_SMALL:"
            f"{matched_rows}"
        ),
    )

    return (
        aligned,
        {
            "matched_rows": (
                matched_rows
            ),
            "matched_fraction": float(
                matched_rows
                /
                len(
                    frozen_train
                )
            ),
            "negative_age_rows": (
                negative_age_count
            ),
        },
    )


def _feature_comparison(
    *,
    frozen_train: pd.DataFrame,
    aligned: pd.DataFrame,
    feature: str,
) -> dict[str, Any]:

    paired = pd.DataFrame(
        {
            "decision_time": (
                frozen_train[
                    "decision_time"
                ].to_numpy()
            ),
            f"{feature}_frozen": (
                pd.to_numeric(
                    frozen_train[
                        feature
                    ],
                    errors="coerce",
                )
                .to_numpy()
            ),
            f"{feature}_current": (
                pd.to_numeric(
                    aligned[
                        feature
                    ],
                    errors="coerce",
                )
                .to_numpy()
            ),
        }
    )

    return (
        base
        ._feature_comparison(
            paired,
            feature,
        )
    )


def _candidate_document(
    *,
    builder: Any,
    canonical_h1: pd.DataFrame,
    frozen_train: pd.DataFrame,
    technical_features: Sequence[
        str
    ],
    close_hour_utc: int,
) -> dict[str, Any]:

    (
        synthetic_raw,
        aggregation_meta,
    ) = (
        _synthetic_d1_raw(
            canonical_h1,
            close_hour_utc=(
                close_hour_utc
            ),
        )
    )

    (
        generated,
        generation_meta,
    ) = (
        _generate_d1_features(
            builder=builder,
            synthetic_raw_d1=(
                synthetic_raw
            ),
            technical_features=(
                technical_features
            ),
        )
    )

    (
        aligned,
        alignment_meta,
    ) = (
        _align_to_frozen_train(
            frozen_train=(
                frozen_train
            ),
            generated_features=(
                generated
            ),
            technical_features=(
                technical_features
            ),
        )
    )

    correlations: dict[
        str,
        float | None
    ] = {}

    psis: dict[
        str,
        float | None
    ] = {}

    standardized_shifts: dict[
        str,
        float | None
    ] = {}

    for feature in (
        technical_features
    ):

        comparison = (
            _feature_comparison(
                frozen_train=(
                    frozen_train
                ),
                aligned=(
                    aligned
                ),
                feature=(
                    feature
                ),
            )
        )

        correlations[
            feature
        ] = (
            _safe_float(
                comparison.get(
                    "paired_correlation"
                )
            )
        )

        psis[
            feature
        ] = (
            _safe_float(
                comparison.get(
                    "psi"
                )
            )
        )

        standardized_shifts[
            feature
        ] = (
            _safe_float(
                comparison.get(
                    "standardized_mean_shift"
                )
            )
        )

    anchor_correlations = {
        feature: (
            correlations[
                feature
            ]
        )
        for feature
        in D1_ANCHOR_FEATURES
    }

    all_values = list(
        correlations.values()
    )

    anchor_values = list(
        anchor_correlations.values()
    )

    age_comparison = (
        _feature_comparison(
            frozen_train=(
                frozen_train
            ),
            aligned=(
                aligned
            ),
            feature="d1_age_minutes",
        )
    )

    age_correlation = (
        _safe_float(
            age_comparison.get(
                "paired_correlation"
            )
        )
    )

    age_psi = (
        _safe_float(
            age_comparison.get(
                "psi"
            )
        )
    )

    age_shift = (
        _safe_float(
            age_comparison.get(
                "standardized_mean_shift"
            )
        )
    )

    material_psi_count = int(
        sum(
            1
            for value
            in psis.values()
            if (
                value is not None
                and
                value
                >=
                float(
                    base.PSI_MATERIAL_THRESHOLD
                )
            )
        )
    )

    material_mean_shift_count = int(
        sum(
            1
            for value
            in standardized_shifts.values()
            if (
                value is not None
                and
                abs(
                    value
                )
                >=
                float(
                    base
                    .STANDARDIZED_MEAN_SHIFT_THRESHOLD
                )
            )
        )
    )

    current_age = pd.to_numeric(
        aligned[
            "d1_age_minutes"
        ],
        errors="coerce",
    )

    return {
        "session_close_hour_utc": int(
            close_hour_utc
        ),
        "aggregation": (
            aggregation_meta
        ),
        "generation": (
            generation_meta
        ),
        "alignment": (
            alignment_meta
        ),
        "technical_feature_count": int(
            len(
                technical_features
            )
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
        "anchor_feature_count": int(
            len(
                D1_ANCHOR_FEATURES
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
        "anchor_correlation_ge_0_95_count": (
            _count_at_least(
                anchor_values,
                0.95,
            )
        ),
        "material_psi_feature_count": (
            material_psi_count
        ),
        "material_standardized_mean_shift_feature_count": (
            material_mean_shift_count
        ),
        "d1_age": {
            "current_median_minutes": (
                float(
                    current_age.median()
                )
                if bool(
                    current_age.notna().any()
                )
                else None
            ),
            "paired_correlation": (
                age_correlation
            ),
            "psi": (
                age_psi
            ),
            "standardized_mean_shift": (
                age_shift
            ),
        },
        "anchor_correlations": (
            anchor_correlations
        ),
        "technical_correlations": (
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
    float,
]:

    anchor_median = (
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

    anchor_095 = int(
        document.get(
            "anchor_correlation_ge_0_95_count",
            0,
        )
    )

    all_098 = int(
        document.get(
            "all_technical_correlation_ge_0_98_count",
            0,
        )
    )

    age_document = (
        document.get(
            "d1_age"
        )
    )

    age_correlation: (
        float
        |
        None
    ) = None

    if isinstance(
        age_document,
        Mapping,
    ):

        age_correlation = (
            _safe_float(
                age_document.get(
                    "paired_correlation"
                )
            )
        )

    return (
        anchor_median
        if anchor_median is not None
        else -2.0,
        all_median
        if all_median is not None
        else -2.0,
        anchor_095,
        all_098,
        age_correlation
        if age_correlation is not None
        else -2.0,
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
        "NO_H1_REAGGREGATION_CANDIDATES",
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

    best_hour = int(
        best[
            "session_close_hour_utc"
        ]
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

    age_document = (
        best.get(
            "d1_age"
        )
    )

    best_age_correlation: (
        float
        |
        None
    ) = None

    if isinstance(
        age_document,
        Mapping,
    ):

        best_age_correlation = (
            _safe_float(
                age_document.get(
                    "paired_correlation"
                )
            )
        )

    anchor_gain = (
        float(
            best_anchor
            -
            NATIVE_REFERENCE_ANCHOR_MEDIAN_CORRELATION
        )
        if best_anchor is not None
        else None
    )

    all_gain = (
        float(
            best_all
            -
            NATIVE_REFERENCE_ALL_MEDIAN_CORRELATION
        )
        if best_all is not None
        else None
    )

    if (
        best_anchor is not None
        and
        best_anchor
        >=
        CONFIRMED_ANCHOR_MEDIAN_CORRELATION
        and
        best_all is not None
        and
        best_all
        >=
        CONFIRMED_ALL_MEDIAN_CORRELATION
        and
        anchor_gain is not None
        and
        anchor_gain
        >=
        MIN_CONFIRMED_ANCHOR_GAIN
    ):

        status = (
            "H1_REAGGREGATED_D1_SESSION_BOUNDARY_CONFIRMED"
        )

        reason = (
            "PORTABLE_H1_REAGGREGATION_AT_A_SPECIFIC_"
            "UTC_SESSION_BOUNDARY_MATERIALLY_RESTORES_"
            "FROZEN_D1_TECHNICAL_FEATURE_CORRESPONDENCE"
        )

        next_action = (
            "TRACE_SELECTED_D1_SESSION_BOUNDARY_TO_"
            "FROZEN_D1_SOURCE_AND_THEN_UPDATE_FULL_MTF_AUDIT"
        )

    elif (
        best_anchor is not None
        and
        best_anchor
        >=
        LIKELY_ANCHOR_MEDIAN_CORRELATION
        and
        best_all is not None
        and
        best_all
        >=
        LIKELY_ALL_MEDIAN_CORRELATION
        and
        anchor_gain is not None
        and
        anchor_gain
        >=
        MIN_LIKELY_ANCHOR_GAIN
    ):

        status = (
            "H1_REAGGREGATED_D1_SESSION_BOUNDARY_LIKELY"
        )

        reason = (
            "FIXED_UTC_H1_REAGGREGATION_MATERIALLY_"
            "IMPROVES_D1_ALIGNMENT_BUT_DOES_NOT_"
            "FULLY_RESTORE_THE_FROZEN_D1_CONTRACT"
        )

        next_action = (
            "TEST_SEASONAL_D1_SESSION_BOUNDARY_PAIR_"
            "AROUND_THE_SELECTED_UTC_HOUR"
        )

    else:

        status = (
            "H1_REAGGREGATED_D1_FIXED_SESSION_BOUNDARY_UNRESOLVED"
        )

        reason = (
            "NO_FIXED_UTC_DAILY_BOUNDARY_RESTORES_"
            "SUFFICIENT_FROZEN_D1_FEATURE_CORRESPONDENCE"
        )

        next_action = (
            "AUDIT_FROZEN_D1_RAW_SOURCE_AGGREGATION_"
            "AND_SEASONAL_SESSION_BOUNDARY_DIRECTLY"
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "selected_session_close_hour_utc": (
            best_hour
        ),
        "selected_anchor_median_correlation": (
            best_anchor
        ),
        "selected_all_technical_median_correlation": (
            best_all
        ),
        "selected_d1_age_correlation": (
            best_age_correlation
        ),
        "native_reference_anchor_median_correlation": (
            NATIVE_REFERENCE_ANCHOR_MEDIAN_CORRELATION
        ),
        "native_reference_all_median_correlation": (
            NATIVE_REFERENCE_ALL_MEDIAN_CORRELATION
        ),
        "anchor_gain_vs_native_reference": (
            anchor_gain
        ),
        "all_technical_gain_vs_native_reference": (
            all_gain
        ),
        "d1_reaggregation_boundary_confirmed": bool(
            status
            ==
            "H1_REAGGREGATED_D1_SESSION_BOUNDARY_CONFIRMED"
        ),
        "full_mtf_portability_verdict_allowed": (
            False
        ),
        "broker_specific_retraining_authorized": (
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

    snapshot = (
        base
        .sweep_module
        ._discover_frozen_training_snapshot(
            trainer=trainer
        )
    )

    dataset_path = (
        base
        ._snapshot_dataset_path(
            snapshot
        )
    )

    manifest_path = (
        base
        ._snapshot_manifest_path(
            snapshot,
            dataset_path,
        )
    )

    base._validate_snapshot(
        snapshot,
        dataset_path,
        manifest_path,
    )

    manifest = (
        base
        ._load_manifest(
            manifest_path
        )
    )

    technical_features = (
        _technical_feature_names(
            manifest
        )
    )

    frozen_features = [
        *technical_features,
        "d1_age_minutes",
    ]

    frozen_train = (
        base
        ._load_frozen_train_only(
            dataset_path,
            frozen_features,
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
        EXPECTED_TRAIN_ROWS,
        (
            "FROZEN_TRAIN_ROW_COUNT_MISMATCH:"
            f"{len(frozen_train)}"
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

        fetch_start = (
            train_start
            -
            pd.Timedelta(
                days=450
            )
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
            fetch_start.to_pydatetime(),
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

        _require(
            not bool(
                raw_h1[
                    "time"
                ]
                .duplicated()
                .any()
            ),
            "CURRENT_BROKER_H1_TIME_DUPLICATES",
        )

        (
            canonical_h1,
            h1_mapping_meta,
        ) = (
            _map_h1_to_canonical_market_time(
                raw_h1
            )
        )

        builder = (
            TrainingMatrixBuilder(
                canonical_root=(
                    CANONICAL_ROOT
                )
            )
        )

        candidates = [
            _candidate_document(
                builder=(
                    builder
                ),
                canonical_h1=(
                    canonical_h1
                ),
                frozen_train=(
                    frozen_train
                ),
                technical_features=(
                    technical_features
                ),
                close_hour_utc=(
                    close_hour
                ),
            )
            for close_hour
            in SESSION_CLOSE_HOURS_UTC
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
                "OK_XAUUSD_CURRENT_BROKER_D1_"
                "H1_REAGGREGATION_BOUNDARY_DIAGNOSTIC"
            ),
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "research_scope": (
                "D1_RECONSTRUCTION_FROM_PORTABLE_H1_"
                "TRAIN_ONLY_SESSION_BOUNDARY_SCAN"
            ),
            "frozen_reference": {
                "dataset_id": (
                    base.EXPECTED_DATASET_ID
                ),
                "dataset_sha256": (
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
                "rows_loaded": int(
                    len(
                        frozen_train
                    )
                ),
                "time_start": (
                    train_start.isoformat()
                ),
                "time_end": (
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
                "raw_h1_time_start": (
                    pd.Timestamp(
                        raw_h1[
                            "time"
                        ].min()
                    ).isoformat()
                ),
                "raw_h1_time_end": (
                    pd.Timestamp(
                        raw_h1[
                            "time"
                        ].max()
                    ).isoformat()
                ),
            },
            "confirmed_h1_time_mapping": (
                h1_mapping_meta
            ),
            "diagnostic_contract": {
                "source_timeframe": (
                    "H1"
                ),
                "target_timeframe": (
                    "D1"
                ),
                "native_d1_used": (
                    False
                ),
                "session_close_hours_utc_tested": list(
                    SESSION_CLOSE_HOURS_UTC
                ),
                "candidate_count": int(
                    len(
                        candidates
                    )
                ),
                "minimum_h1_bars_per_synthetic_d1": (
                    MIN_H1_BARS_PER_SYNTHETIC_D1
                ),
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
                "selection_primary": (
                    "MAX_FAST_D1_ANCHOR_MEDIAN_CORRELATION"
                ),
                "selection_secondary": (
                    "MAX_ALL_43_D1_TECHNICAL_MEDIAN_CORRELATION"
                ),
                "selection_tertiary": (
                    "MAX_D1_AGE_CORRELATION"
                ),
                "frozen_labels_used_for_boundary_selection": (
                    False
                ),
                "validation_used_for_boundary_selection": (
                    False
                ),
                "test_used_for_boundary_selection": (
                    False
                ),
            },
            "native_reference": {
                "diagnostic_version": (
                    NATIVE_REFERENCE_DIAGNOSTIC_VERSION
                ),
                "anchor_median_correlation": (
                    NATIVE_REFERENCE_ANCHOR_MEDIAN_CORRELATION
                ),
                "all_technical_median_correlation": (
                    NATIVE_REFERENCE_ALL_MEDIAN_CORRELATION
                ),
                "availability_offset_scan_status": (
                    "D1_NATIVE_BAR_AGGREGATION_"
                    "BOUNDARY_MISMATCH_LIKELY"
                ),
            },
            "thresholds": {
                "confirmed_anchor_median_correlation": (
                    CONFIRMED_ANCHOR_MEDIAN_CORRELATION
                ),
                "confirmed_all_median_correlation": (
                    CONFIRMED_ALL_MEDIAN_CORRELATION
                ),
                "likely_anchor_median_correlation": (
                    LIKELY_ANCHOR_MEDIAN_CORRELATION
                ),
                "likely_all_median_correlation": (
                    LIKELY_ALL_MEDIAN_CORRELATION
                ),
                "minimum_confirmed_anchor_gain": (
                    MIN_CONFIRMED_ANCHOR_GAIN
                ),
                "minimum_likely_anchor_gain": (
                    MIN_LIKELY_ANCHOR_GAIN
                ),
                "psi_material": (
                    base.PSI_MATERIAL_THRESHOLD
                ),
                "standardized_mean_shift_material": (
                    base
                    .STANDARDIZED_MEAN_SHIFT_THRESHOLD
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
                    "session_close_hour_utc": (
                        document[
                            "session_close_hour_utc"
                        ]
                    ),
                    "matched_rows": (
                        document[
                            "alignment"
                        ][
                            "matched_rows"
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
                    "all_technical_correlation_ge_0_98_count": (
                        document[
                            "all_technical_correlation_ge_0_98_count"
                        ]
                    ),
                    "material_psi_feature_count": (
                        document[
                            "material_psi_feature_count"
                        ]
                    ),
                    "d1_age": (
                        document[
                            "d1_age"
                        ]
                    ),
                    "aggregation": (
                        document[
                            "aggregation"
                        ]
                    ),
                }
                for index, document
                in enumerate(
                    ranked,
                    start=1,
                )
            ],
            "candidate_diagnostics": (
                candidates
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
                "native_d1_used": (
                    False
                ),
                "h1_used_for_reaggregation": (
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
            },
            "next_decision_contract": {
                "if_fixed_boundary_confirmed": (
                    "TRACE_SELECTED_D1_SESSION_BOUNDARY_"
                    "TO_FROZEN_D1_SOURCE_BEFORE_FULL_MTF_UPDATE"
                ),
                "if_fixed_boundary_likely": (
                    "TEST_SEASONAL_D1_SESSION_BOUNDARY_PAIR_"
                    "AROUND_SELECTED_UTC_HOUR"
                ),
                "if_fixed_boundary_unresolved": (
                    "AUDIT_FROZEN_D1_RAW_SOURCE_AGGREGATION_"
                    "DIRECTLY"
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
                        "H1_REAGGREGATION_BOUNDARY_DIAGNOSTIC_FAILED"
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