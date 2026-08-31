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

CANONICAL_ROOT = (
    ROOT_DIR
    /
    "01_Data"
    /
    "Canonical"
)

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


ANALYSIS_VERSION = (
    "XAUUSD_CURRENT_BROKER_FULL_MTF_PORTABILITY_V2"
)

MAPPED_M5_AUDIT_MODULE = (
    "04_Testing."
    "analyze_xauusd_current_broker_m5_domain_shift_mapped"
)

TRAINING_MATRIX_MODULE = (
    "02_AI.Dataset.training_matrix_builder"
)

TRAINING_FEATURE_ENRICHER_MODULE = (
    "02_AI.Dataset.training_feature_enricher"
)


TIMEFRAMES = (
    "M5",
    "M15",
    "M30",
    "H1",
    "H4",
    "D1",
)

CONTEXT_TIMEFRAMES = (
    "M15",
    "M30",
    "H1",
    "H4",
    "D1",
)


TIMEFRAME_MINUTES = {
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}


FETCH_WARMUP_DAYS = {
    "M5": 90,
    "M15": 120,
    "M30": 180,
    "H1": 365,
    "H4": 730,
    "D1": 1500,
}


AGE_FEATURES = (
    "m15_age_minutes",
    "m30_age_minutes",
    "h1_age_minutes",
    "h4_age_minutes",
    "d1_age_minutes",
)

UTC_FEATURES = (
    "utc_hour_sin",
    "utc_hour_cos",
    "utc_day_sin",
    "utc_day_cos",
)


EXPECTED_TOTAL_FEATURE_COUNT = 333
EXPECTED_TECHNICAL_COUNT_PER_TIMEFRAME = 43
EXPECTED_DOMAIN_FEATURE_COUNT = 63
EXPECTED_BROKER_SENSITIVE_COUNT = 3
EXPECTED_AGE_FEATURE_COUNT = 5
EXPECTED_UTC_FEATURE_COUNT = 4


MIN_FEATURE_FINITE_PAIR_FRACTION = 0.90

MIN_GROUP_MEDIAN_CORRELATION = 0.80

MAX_GROUP_MATERIAL_SHIFT_SHARE = 0.20

MIN_UTC_MEDIAN_CORRELATION = 0.999999


CANONICAL_DATETIME_DTYPE = (
    "datetime64[ns, UTC]"
)


mapped: Any = importlib.import_module(
    MAPPED_M5_AUDIT_MODULE
)

base: Any = (
    mapped.base
)

training_matrix_module: Any = importlib.import_module(
    TRAINING_MATRIX_MODULE
)

training_enricher_module: Any = importlib.import_module(
    TRAINING_FEATURE_ENRICHER_MODULE
)


TrainingMatrixBuilder: Any = getattr(
    training_matrix_module,
    "TrainingMatrixBuilder",
)

TrainingFeatureEnricher: Any = getattr(
    training_enricher_module,
    "TrainingFeatureEnricher",
)


MT5_TIMEFRAMES = {
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}


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


def _coerce_int(
    value: Any,
) -> int:

    try:
        return int(
            value
        )

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise RuntimeError(
            (
                "INTEGER_COERCION_FAILED:"
                f"{value!r}"
            )
        ) from exc


def _utc_ns_series(
    values: pd.Series,
) -> pd.Series:

    converted = pd.to_datetime(
        values,
        utc=True,
        errors="raise",
    )

    normalized = converted.astype(
        CANONICAL_DATETIME_DTYPE
    )

    return (
        normalized
    )


def _normalize_time_column(
    frame: pd.DataFrame,
    column: str,
) -> pd.DataFrame:

    _require(
        column
        in frame.columns,
        (
            "TIME_COLUMN_MISSING:"
            f"{column}"
        ),
    )

    result = (
        frame.copy()
    )

    result[
        column
    ] = (
        _utc_ns_series(
            result[
                column
            ]
        )
    )

    _require(
        str(
            result[
                column
            ].dtype
        )
        ==
        CANONICAL_DATETIME_DTYPE,
        (
            "TIME_COLUMN_DTYPE_NOT_CANONICAL:"
            f"{column}:"
            f"{result[column].dtype}"
        ),
    )

    return (
        result
    )


def _assert_same_time_dtype(
    left: pd.Series,
    right: pd.Series,
    *,
    context: str,
) -> None:

    left_dtype = str(
        left.dtype
    )

    right_dtype = str(
        right.dtype
    )

    _require(
        left_dtype
        ==
        CANONICAL_DATETIME_DTYPE,
        (
            "LEFT_TIME_DTYPE_NOT_CANONICAL:"
            f"{context}:"
            f"{left_dtype}"
        ),
    )

    _require(
        right_dtype
        ==
        CANONICAL_DATETIME_DTYPE,
        (
            "RIGHT_TIME_DTYPE_NOT_CANONICAL:"
            f"{context}:"
            f"{right_dtype}"
        ),
    )

    _require(
        left_dtype
        ==
        right_dtype,
        (
            "TIME_DTYPE_MISMATCH:"
            f"{context}:"
            f"{left_dtype}:"
            f"{right_dtype}"
        ),
    )


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


def _maximum_finite(
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
        max(
            finite
        )
    )


def _minimum_finite(
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
        min(
            finite
        )
    )


def _feature_groups(
    manifest: Mapping[
        str,
        Any,
    ],
    base_feature_names: Sequence[
        str
    ],
) -> dict[str, Any]:

    feature_columns_raw = (
        manifest.get(
            "feature_columns"
        )
    )

    if not isinstance(
        feature_columns_raw,
        list,
    ):

        raise RuntimeError(
            "FROZEN_FEATURE_COLUMNS_MISSING"
        )

    frozen_features = [
        str(
            value
        )
        for value
        in feature_columns_raw
    ]

    _require(
        len(
            frozen_features
        )
        ==
        EXPECTED_TOTAL_FEATURE_COUNT,
        (
            "FROZEN_FEATURE_COUNT_MISMATCH:"
            f"{len(frozen_features)}"
        ),
    )

    _require(
        len(
            set(
                frozen_features
            )
        )
        ==
        len(
            frozen_features
        ),
        "FROZEN_FEATURE_COLUMNS_NOT_UNIQUE",
    )

    _require(
        len(
            base_feature_names
        )
        ==
        EXPECTED_TECHNICAL_COUNT_PER_TIMEFRAME,
        (
            "BASE_FEATURE_COUNT_MISMATCH:"
            f"{len(base_feature_names)}"
        ),
    )

    technical: dict[
        str,
        list[str],
    ] = {}

    for timeframe in (
        TIMEFRAMES
    ):

        prefix = (
            timeframe.lower()
        )

        features = [
            (
                prefix
                +
                "_"
                +
                str(
                    feature
                )
            )
            for feature
            in base_feature_names
        ]

        _require(
            len(
                features
            )
            ==
            EXPECTED_TECHNICAL_COUNT_PER_TIMEFRAME,
            (
                "TECHNICAL_GROUP_COUNT_MISMATCH:"
                f"{timeframe}:"
                f"{len(features)}"
            ),
        )

        technical[
            timeframe
        ] = (
            features
        )

    domain_contract = (
        manifest.get(
            "domain_feature_contract"
        )
    )

    if not isinstance(
        domain_contract,
        Mapping,
    ):

        raise RuntimeError(
            "DOMAIN_FEATURE_CONTRACT_MISSING"
        )

    domain_features_raw = (
        domain_contract.get(
            "feature_columns"
        )
    )

    if not isinstance(
        domain_features_raw,
        list,
    ):

        raise RuntimeError(
            "DOMAIN_FEATURE_COLUMNS_MISSING"
        )

    domain_features = [
        str(
            value
        )
        for value
        in domain_features_raw
    ]

    _require(
        len(
            domain_features
        )
        ==
        EXPECTED_DOMAIN_FEATURE_COUNT,
        (
            "DOMAIN_FEATURE_COUNT_MISMATCH:"
            f"{len(domain_features)}"
        ),
    )

    broker_sensitive_features = [
        str(
            value
        )
        for value
        in base.BROKER_SENSITIVE_FEATURES
    ]

    _require(
        len(
            broker_sensitive_features
        )
        ==
        EXPECTED_BROKER_SENSITIVE_COUNT,
        (
            "BROKER_SENSITIVE_COUNT_MISMATCH:"
            f"{len(broker_sensitive_features)}"
        ),
    )

    age_features = list(
        AGE_FEATURES
    )

    utc_features = list(
        UTC_FEATURES
    )

    _require(
        len(
            age_features
        )
        ==
        EXPECTED_AGE_FEATURE_COUNT,
        "AGE_FEATURE_COUNT_MISMATCH",
    )

    _require(
        len(
            utc_features
        )
        ==
        EXPECTED_UTC_FEATURE_COUNT,
        "UTC_FEATURE_COUNT_MISMATCH",
    )

    technical_union: set[
        str
    ] = set()

    for features in (
        technical.values()
    ):

        technical_union.update(
            features
        )

    group_sets = {
        "technical": (
            technical_union
        ),
        "domain": set(
            domain_features
        ),
        "broker_sensitive": set(
            broker_sensitive_features
        ),
        "age": set(
            age_features
        ),
        "utc": set(
            utc_features
        ),
    }

    group_names = list(
        group_sets.keys()
    )

    for left_index in range(
        len(
            group_names
        )
    ):

        for right_index in range(
            left_index + 1,
            len(
                group_names
            ),
        ):

            left_name = (
                group_names[
                    left_index
                ]
            )

            right_name = (
                group_names[
                    right_index
                ]
            )

            overlap = sorted(
                group_sets[
                    left_name
                ]
                &
                group_sets[
                    right_name
                ]
            )

            _require(
                not overlap,
                (
                    "FEATURE_GROUP_OVERLAP:"
                    f"{left_name}:"
                    f"{right_name}:"
                    f"{overlap}"
                ),
            )

    classified: set[
        str
    ] = set()

    for group_set in (
        group_sets.values()
    ):

        classified.update(
            group_set
        )

    frozen_set = set(
        frozen_features
    )

    missing = sorted(
        frozen_set
        -
        classified
    )

    extra = sorted(
        classified
        -
        frozen_set
    )

    _require(
        not missing,
        (
            "UNCLASSIFIED_FROZEN_FEATURES:"
            f"{missing}"
        ),
    )

    _require(
        not extra,
        (
            "CLASSIFIED_FEATURES_NOT_IN_FROZEN_CONTRACT:"
            f"{extra}"
        ),
    )

    _require(
        len(
            classified
        )
        ==
        EXPECTED_TOTAL_FEATURE_COUNT,
        (
            "CLASSIFIED_FEATURE_COUNT_MISMATCH:"
            f"{len(classified)}"
        ),
    )

    return {
        "frozen_features": (
            frozen_features
        ),
        "technical": (
            technical
        ),
        "domain": (
            domain_features
        ),
        "broker_sensitive": (
            broker_sensitive_features
        ),
        "age": (
            age_features
        ),
        "utc": (
            utc_features
        ),
    }


def _clock_map_times(
    source_times: pd.Series,
) -> tuple[
    pd.Series,
    dict[str, Any],
]:

    normalized = (
        _utc_ns_series(
            source_times
        )
    )

    offsets = [
        mapped
        ._research_clock_offset_seconds(
            pd.Timestamp(
                value
            )
        )
        for value
        in normalized
    ]

    offset_series = pd.Series(
        offsets,
        index=normalized.index,
        dtype="int64",
    )

    market_times = (
        normalized
        +
        pd.to_timedelta(
            offset_series,
            unit="s",
        )
    )

    market_times = (
        _utc_ns_series(
            market_times
        )
    )

    duplicate_count = int(
        market_times
        .duplicated(
            keep=False
        )
        .sum()
    )

    offset_counts_raw = (
        offset_series
        .value_counts()
        .sort_index()
    )

    offset_counts: dict[
        str,
        int,
    ] = {}

    for (
        offset,
        count,
    ) in offset_counts_raw.items():

        offset_counts[
            str(
                _coerce_int(
                    offset
                )
            )
        ] = (
            _coerce_int(
                count
            )
        )

    return (
        market_times,
        {
            "rows": int(
                len(
                    market_times
                )
            ),
            "datetime_dtype": (
                str(
                    market_times.dtype
                )
            ),
            "duplicate_market_bar_time_rows": (
                duplicate_count
            ),
            "clock_offset_row_counts": (
                offset_counts
            ),
            "market_bar_time_start": (
                pd.Timestamp(
                    market_times.min()
                ).isoformat()
                if len(
                    market_times
                )
                else None
            ),
            "market_bar_time_end": (
                pd.Timestamp(
                    market_times.max()
                ).isoformat()
                if len(
                    market_times
                )
                else None
            ),
        },
    )


def _fetch_current_timeframes(
    *,
    broker_symbol: str,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
) -> tuple[
    dict[str, pd.DataFrame],
    dict[str, Any],
]:

    frames: dict[
        str,
        pd.DataFrame,
    ] = {}

    metadata: dict[
        str,
        Any,
    ] = {}

    for timeframe in (
        TIMEFRAMES
    ):

        warmup_days = int(
            FETCH_WARMUP_DAYS[
                timeframe
            ]
        )

        fetch_start = (
            train_start
            -
            pd.Timedelta(
                days=warmup_days
            )
            -
            pd.Timedelta(
                hours=6
            )
        )

        fetch_end = (
            train_end
            +
            pd.Timedelta(
                days=2
            )
            +
            pd.Timedelta(
                hours=6
            )
        )

        rates = mt5.copy_rates_range(
            broker_symbol,
            MT5_TIMEFRAMES[
                timeframe
            ],
            fetch_start.to_pydatetime(),
            fetch_end.to_pydatetime(),
        )

        frame = (
            base
            ._mt5_rates_frame(
                rates
            )
        )

        _require(
            not frame.empty,
            (
                "CURRENT_BROKER_TIMEFRAME_EMPTY:"
                f"{timeframe}"
            ),
        )

        frame = (
            _normalize_time_column(
                frame,
                "time",
            )
        )

        frame = (
            frame
            .sort_values(
                "time"
            )
            .reset_index(
                drop=True
            )
        )

        _require(
            not bool(
                frame[
                    "time"
                ]
                .duplicated()
                .any()
            ),
            (
                "CURRENT_BROKER_RAW_TIME_DUPLICATES:"
                f"{timeframe}"
            ),
        )

        frames[
            timeframe
        ] = (
            frame
        )

        metadata[
            timeframe
        ] = {
            "rows": int(
                len(
                    frame
                )
            ),
            "requested_warmup_days": (
                warmup_days
            ),
            "datetime_dtype": (
                str(
                    frame[
                        "time"
                    ].dtype
                )
            ),
            "time_start": (
                pd.Timestamp(
                    frame[
                        "time"
                    ].min()
                ).isoformat()
            ),
            "time_end": (
                pd.Timestamp(
                    frame[
                        "time"
                    ].max()
                ).isoformat()
            ),
        }

    return (
        frames,
        metadata,
    )


def _build_m5_features(
    raw_m5: pd.DataFrame,
    *,
    base_feature_names: Sequence[
        str
    ],
    required_features: Sequence[
        str
    ],
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

    (
        generated,
        generation_meta,
    ) = (
        base
        ._build_current_m5_comparison_frame(
            raw_m5,
            base_feature_names,
        )
    )

    generated = (
        _normalize_time_column(
            generated,
            "decision_time",
        )
    )

    (
        clock_mapped,
        clock_meta,
    ) = (
        mapped
        ._apply_research_clock_mapping(
            generated
        )
    )

    clock_mapped = (
        _normalize_time_column(
            clock_mapped,
            "market_bar_time",
        )
    )

    (
        availability_mapped,
        availability_meta,
    ) = (
        mapped
        ._apply_feature_availability_semantics(
            clock_mapped
        )
    )

    availability_mapped = (
        _normalize_time_column(
            availability_mapped,
            "decision_time",
        )
    )

    missing = sorted(
        set(
            required_features
        )
        -
        set(
            str(
                column
            )
            for column
            in availability_mapped.columns
        )
    )

    _require(
        not missing,
        (
            "M5_REQUIRED_FEATURES_MISSING:"
            f"{missing}"
        ),
    )

    result = (
        availability_mapped[
            [
                "decision_time",
                *required_features,
            ]
        ]
        .copy()
        .sort_values(
            "decision_time"
        )
        .reset_index(
            drop=True
        )
    )

    result = (
        _normalize_time_column(
            result,
            "decision_time",
        )
    )

    _require(
        not bool(
            result[
                "decision_time"
            ]
            .duplicated()
            .any()
        ),
        "M5_CANONICAL_DECISION_TIME_DUPLICATES",
    )

    return (
        result,
        {
            "feature_generation": (
                generation_meta
            ),
            "clock_mapping": (
                clock_meta
            ),
            "feature_availability": (
                availability_meta
            ),
            "decision_time_dtype": (
                str(
                    result[
                        "decision_time"
                    ].dtype
                )
            ),
            "rows": int(
                len(
                    result
                )
            ),
        },
    )


def _build_context_features(
    *,
    builder: Any,
    raw_frame: pd.DataFrame,
    timeframe: str,
    decision_grid: pd.DataFrame,
    technical_features: Sequence[
        str
    ],
    age_feature: str,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

    generated = (
        builder
        ._generate_feature_frame(
            frame=raw_frame,
            timeframe=timeframe,
        )
    )

    _require(
        "time"
        in generated.columns,
        (
            "CONTEXT_GENERATED_TIME_MISSING:"
            f"{timeframe}"
        ),
    )

    expected_generated = {
        *technical_features,
        "time",
        "available_time",
    }

    missing = sorted(
        expected_generated
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
            "CONTEXT_GENERATED_COLUMNS_MISSING:"
            f"{timeframe}:"
            f"{missing}"
        ),
    )

    generated = (
        _normalize_time_column(
            generated,
            "time",
        )
    )

    (
        market_bar_time,
        clock_meta,
    ) = (
        _clock_map_times(
            generated[
                "time"
            ]
        )
    )

    _require(
        int(
            clock_meta[
                "duplicate_market_bar_time_rows"
            ]
        )
        ==
        0,
        (
            "CONTEXT_MAPPED_MARKET_TIME_DUPLICATES:"
            f"{timeframe}:"
            f"{clock_meta['duplicate_market_bar_time_rows']}"
        ),
    )

    canonical_available_time = (
        market_bar_time
        +
        pd.to_timedelta(
            TIMEFRAME_MINUTES[
                timeframe
            ],
            unit="m",
        )
    )

    canonical_available_time = (
        _utc_ns_series(
            canonical_available_time
        )
    )

    right = (
        generated[
            list(
                technical_features
            )
        ]
        .copy()
    )

    available_column = (
        f"__{timeframe.lower()}_available_time"
    )

    right[
        available_column
    ] = (
        canonical_available_time
    )

    right = (
        _normalize_time_column(
            right,
            available_column,
        )
    )

    right = (
        right
        .sort_values(
            available_column
        )
        .reset_index(
            drop=True
        )
    )

    duplicate_available_count = int(
        right[
            available_column
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
            "CONTEXT_AVAILABLE_TIME_DUPLICATES:"
            f"{timeframe}:"
            f"{duplicate_available_count}"
        ),
    )

    left = (
        decision_grid[
            [
                "decision_time"
            ]
        ]
        .copy()
    )

    left = (
        _normalize_time_column(
            left,
            "decision_time",
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

    _assert_same_time_dtype(
        left[
            "decision_time"
        ],
        right[
            available_column
        ],
        context=(
            f"CONTEXT_ASOF_{timeframe}"
        ),
    )

    merged = pd.merge_asof(
        left,
        right,
        left_on="decision_time",
        right_on=available_column,
        direction="backward",
        allow_exact_matches=True,
    )

    merged = (
        _normalize_time_column(
            merged,
            "decision_time",
        )
    )

    merged = (
        _normalize_time_column(
            merged,
            available_column,
        )
    )

    merged[
        age_feature
    ] = (
        (
            merged[
                "decision_time"
            ]
            -
            merged[
                available_column
            ]
        )
        .dt
        .total_seconds()
        /
        60.0
    ).astype(
        "float32"
    )

    negative_age_count = int(
        (
            merged[
                age_feature
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
            "CURRENT_CONTEXT_FUTURE_LEAKAGE:"
            f"{timeframe}:"
            f"{negative_age_count}"
        ),
    )

    matched_rows = int(
        merged[
            available_column
        ]
        .notna()
        .sum()
    )

    result = (
        merged[
            [
                "decision_time",
                *technical_features,
                age_feature,
            ]
        ]
        .copy()
    )

    result = (
        _normalize_time_column(
            result,
            "decision_time",
        )
    )

    return (
        result,
        {
            "timeframe": (
                timeframe
            ),
            "generated_rows": int(
                len(
                    generated
                )
            ),
            "decision_grid_rows": int(
                len(
                    decision_grid
                )
            ),
            "matched_rows": (
                matched_rows
            ),
            "matched_fraction": float(
                matched_rows
                /
                len(
                    decision_grid
                )
            ),
            "negative_age_rows": (
                negative_age_count
            ),
            "duplicate_available_time_rows": (
                duplicate_available_count
            ),
            "left_decision_time_dtype": (
                str(
                    left[
                        "decision_time"
                    ].dtype
                )
            ),
            "right_available_time_dtype": (
                str(
                    right[
                        available_column
                    ].dtype
                )
            ),
            "clock_mapping": (
                clock_meta
            ),
        },
    )


def _add_utc_features(
    frame: pd.DataFrame,
) -> pd.DataFrame:

    result = (
        _normalize_time_column(
            frame,
            "decision_time",
        )
    )

    decision_time = (
        result[
            "decision_time"
        ]
    )

    hour_value = (
        decision_time.dt.hour
        +
        (
            decision_time.dt.minute
            /
            60.0
        )
    )

    day_value = (
        decision_time
        .dt
        .dayofweek
        .astype(
            float
        )
    )

    result[
        "utc_hour_sin"
    ] = np.sin(
        2.0
        *
        np.pi
        *
        hour_value
        /
        24.0
    ).astype(
        "float32"
    )

    result[
        "utc_hour_cos"
    ] = np.cos(
        2.0
        *
        np.pi
        *
        hour_value
        /
        24.0
    ).astype(
        "float32"
    )

    result[
        "utc_day_sin"
    ] = np.sin(
        2.0
        *
        np.pi
        *
        day_value
        /
        7.0
    ).astype(
        "float32"
    )

    result[
        "utc_day_cos"
    ] = np.cos(
        2.0
        *
        np.pi
        *
        day_value
        /
        7.0
    ).astype(
        "float32"
    )

    return (
        result
    )


def _build_domain_features(
    *,
    enricher: Any,
    raw_m5: pd.DataFrame,
    domain_features: Sequence[
        str
    ],
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

    domain = (
        enricher
        ._domain_features(
            raw=raw_m5,
            base_timeframe="M5",
        )
    )

    _require(
        isinstance(
            domain,
            pd.DataFrame,
        ),
        "DOMAIN_GENERATOR_DID_NOT_RETURN_DATAFRAME",
    )

    _require(
        "time"
        in domain.columns,
        "DOMAIN_GENERATED_TIME_MISSING",
    )

    missing = sorted(
        set(
            domain_features
        )
        -
        set(
            str(
                column
            )
            for column
            in domain.columns
        )
    )

    _require(
        not missing,
        (
            "DOMAIN_FEATURES_MISSING:"
            f"{missing}"
        ),
    )

    domain = (
        _normalize_time_column(
            domain,
            "time",
        )
    )

    (
        market_bar_time,
        clock_meta,
    ) = (
        _clock_map_times(
            domain[
                "time"
            ]
        )
    )

    _require(
        int(
            clock_meta[
                "duplicate_market_bar_time_rows"
            ]
        )
        ==
        0,
        (
            "DOMAIN_MAPPED_MARKET_TIME_DUPLICATES:"
            f"{clock_meta['duplicate_market_bar_time_rows']}"
        ),
    )

    domain = (
        domain.copy()
    )

    domain[
        "decision_time"
    ] = (
        market_bar_time
        +
        pd.to_timedelta(
            5,
            unit="m",
        )
    )

    domain = (
        _normalize_time_column(
            domain,
            "decision_time",
        )
    )

    duplicate_count = int(
        domain[
            "decision_time"
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
            "DOMAIN_DECISION_TIME_DUPLICATES:"
            f"{duplicate_count}"
        ),
    )

    result = (
        domain[
            [
                "decision_time",
                *domain_features,
            ]
        ]
        .copy()
        .sort_values(
            "decision_time"
        )
        .reset_index(
            drop=True
        )
    )

    result = (
        _normalize_time_column(
            result,
            "decision_time",
        )
    )

    return (
        result,
        {
            "rows": int(
                len(
                    result
                )
            ),
            "feature_count": int(
                len(
                    domain_features
                )
            ),
            "decision_time_duplicate_rows": (
                duplicate_count
            ),
            "decision_time_dtype": (
                str(
                    result[
                        "decision_time"
                    ].dtype
                )
            ),
            "clock_mapping": (
                clock_meta
            ),
            "availability_semantics": (
                "BASE_M5_BAR_TIME_PLUS_5_MINUTES"
            ),
        },
    )


def _merge_exact_group(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    group_name: str,
) -> pd.DataFrame:

    _require(
        "decision_time"
        in left.columns,
        (
            "LEFT_DECISION_TIME_MISSING:"
            f"{group_name}"
        ),
    )

    _require(
        "decision_time"
        in right.columns,
        (
            "RIGHT_DECISION_TIME_MISSING:"
            f"{group_name}"
        ),
    )

    left_normalized = (
        _normalize_time_column(
            left,
            "decision_time",
        )
    )

    right_normalized = (
        _normalize_time_column(
            right,
            "decision_time",
        )
    )

    _assert_same_time_dtype(
        left_normalized[
            "decision_time"
        ],
        right_normalized[
            "decision_time"
        ],
        context=(
            f"EXACT_MERGE_{group_name}"
        ),
    )

    _require(
        not bool(
            right_normalized[
                "decision_time"
            ]
            .duplicated()
            .any()
        ),
        (
            "RIGHT_DECISION_TIME_DUPLICATES:"
            f"{group_name}"
        ),
    )

    before_rows = int(
        len(
            left_normalized
        )
    )

    result = (
        left_normalized
        .merge(
            right_normalized,
            on="decision_time",
            how="left",
            validate="one_to_one",
        )
    )

    _require(
        len(
            result
        )
        ==
        before_rows,
        (
            "EXACT_GROUP_MERGE_ROW_COUNT_CHANGED:"
            f"{group_name}:"
            f"{before_rows}:"
            f"{len(result)}"
        ),
    )

    result = (
        _normalize_time_column(
            result,
            "decision_time",
        )
    )

    return (
        result
    )


def _build_current_feature_matrix(
    *,
    frozen_train: pd.DataFrame,
    groups: Mapping[
        str,
        Any,
    ],
    raw_frames: Mapping[
        str,
        pd.DataFrame,
    ],
    base_feature_names: Sequence[
        str
    ],
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

    builder = TrainingMatrixBuilder(
        canonical_root=CANONICAL_ROOT
    )

    enricher = TrainingFeatureEnricher(
        canonical_root=CANONICAL_ROOT
    )

    matrix = (
        frozen_train[
            [
                "decision_time"
            ]
        ]
        .copy()
    )

    matrix = (
        _normalize_time_column(
            matrix,
            "decision_time",
        )
    )

    matrix = (
        matrix
        .sort_values(
            "decision_time"
        )
        .reset_index(
            drop=True
        )
    )

    _require(
        not bool(
            matrix[
                "decision_time"
            ]
            .duplicated()
            .any()
        ),
        "FROZEN_TRAIN_DECISION_TIME_DUPLICATES",
    )

    m5_required = [
        *groups[
            "technical"
        ][
            "M5"
        ],
        *groups[
            "broker_sensitive"
        ],
    ]

    (
        m5_features,
        m5_meta,
    ) = (
        _build_m5_features(
            raw_frames[
                "M5"
            ],
            base_feature_names=(
                base_feature_names
            ),
            required_features=(
                m5_required
            ),
        )
    )

    matrix = (
        _merge_exact_group(
            matrix,
            m5_features,
            group_name="M5",
        )
    )

    context_metadata: dict[
        str,
        Any,
    ] = {}

    for timeframe in (
        CONTEXT_TIMEFRAMES
    ):

        age_feature = (
            timeframe.lower()
            +
            "_age_minutes"
        )

        (
            context_features,
            context_meta,
        ) = (
            _build_context_features(
                builder=builder,
                raw_frame=(
                    raw_frames[
                        timeframe
                    ]
                ),
                timeframe=(
                    timeframe
                ),
                decision_grid=(
                    matrix[
                        [
                            "decision_time"
                        ]
                    ]
                ),
                technical_features=(
                    groups[
                        "technical"
                    ][
                        timeframe
                    ]
                ),
                age_feature=(
                    age_feature
                ),
            )
        )

        _assert_same_time_dtype(
            matrix[
                "decision_time"
            ],
            context_features[
                "decision_time"
            ],
            context=(
                f"CONTEXT_GRID_{timeframe}"
            ),
        )

        _require(
            len(
                context_features
            )
            ==
            len(
                matrix
            ),
            (
                "CONTEXT_FEATURE_ROW_COUNT_MISMATCH:"
                f"{timeframe}:"
                f"{len(context_features)}:"
                f"{len(matrix)}"
            ),
        )

        _require(
            bool(
                (
                    matrix[
                        "decision_time"
                    ]
                    ==
                    context_features[
                        "decision_time"
                    ]
                )
                .all()
            ),
            (
                "CONTEXT_DECISION_GRID_MISMATCH:"
                f"{timeframe}"
            ),
        )

        context_payload = (
            context_features.drop(
                columns=[
                    "decision_time"
                ]
            )
        )

        for column in (
            context_payload.columns
        ):

            matrix[
                str(
                    column
                )
            ] = (
                context_payload[
                    column
                ]
                .to_numpy()
            )

        context_metadata[
            timeframe
        ] = (
            context_meta
        )

    matrix = (
        _add_utc_features(
            matrix
        )
    )

    (
        domain_features,
        domain_meta,
    ) = (
        _build_domain_features(
            enricher=enricher,
            raw_m5=(
                raw_frames[
                    "M5"
                ]
            ),
            domain_features=(
                groups[
                    "domain"
                ]
            ),
        )
    )

    matrix = (
        _merge_exact_group(
            matrix,
            domain_features,
            group_name="DOMAIN",
        )
    )

    frozen_features = [
        str(
            value
        )
        for value
        in groups[
            "frozen_features"
        ]
    ]

    missing_columns = sorted(
        set(
            frozen_features
        )
        -
        set(
            str(
                column
            )
            for column
            in matrix.columns
        )
    )

    _require(
        not missing_columns,
        (
            "CURRENT_FULL_FEATURE_MATRIX_MISSING_COLUMNS:"
            f"{missing_columns}"
        ),
    )

    matrix = (
        matrix[
            [
                "decision_time",
                *frozen_features,
            ]
        ]
        .copy()
    )

    matrix = (
        _normalize_time_column(
            matrix,
            "decision_time",
        )
    )

    _require(
        len(
            matrix.columns
        )
        ==
        (
            EXPECTED_TOTAL_FEATURE_COUNT
            +
            1
        ),
        (
            "CURRENT_FULL_MATRIX_COLUMN_COUNT_MISMATCH:"
            f"{len(matrix.columns)}"
        ),
    )

    _require(
        len(
            matrix
        )
        ==
        len(
            frozen_train
        ),
        (
            "CURRENT_FULL_MATRIX_ROW_COUNT_MISMATCH:"
            f"{len(matrix)}:"
            f"{len(frozen_train)}"
        ),
    )

    frozen_decision_time = (
        _utc_ns_series(
            frozen_train[
                "decision_time"
            ]
        )
    )

    _assert_same_time_dtype(
        matrix[
            "decision_time"
        ],
        frozen_decision_time,
        context="FINAL_DECISION_GRID",
    )

    _require(
        bool(
            (
                matrix[
                    "decision_time"
                ]
                ==
                frozen_decision_time
            )
            .all()
        ),
        "CURRENT_AND_FROZEN_DECISION_GRIDS_DIFFER",
    )

    return (
        matrix,
        {
            "datetime_join_contract": {
                "canonical_dtype": (
                    CANONICAL_DATETIME_DTYPE
                ),
                "frozen_decision_time_dtype": (
                    str(
                        frozen_decision_time.dtype
                    )
                ),
                "current_decision_time_dtype": (
                    str(
                        matrix[
                            "decision_time"
                        ].dtype
                    )
                ),
                "all_join_keys_normalized_before_merge": (
                    True
                ),
            },
            "m5": (
                m5_meta
            ),
            "context_timeframes": (
                context_metadata
            ),
            "domain": (
                domain_meta
            ),
            "utc_features": {
                "feature_count": int(
                    len(
                        UTC_FEATURES
                    )
                ),
                "formula_source": (
                    "CANONICAL_DECISION_TIME"
                ),
            },
            "row_count": int(
                len(
                    matrix
                )
            ),
            "feature_count": (
                EXPECTED_TOTAL_FEATURE_COUNT
            ),
        },
    )


def _compare_feature(
    *,
    frozen_train: pd.DataFrame,
    current_matrix: pd.DataFrame,
    feature: str,
) -> dict[str, Any]:

    frozen_values = pd.to_numeric(
        frozen_train[
            feature
        ],
        errors="coerce",
    )

    current_values = pd.to_numeric(
        current_matrix[
            feature
        ],
        errors="coerce",
    )

    frozen_array = frozen_values.to_numpy(
        dtype=np.float64
    )

    current_array = current_values.to_numpy(
        dtype=np.float64
    )

    finite = (
        np.isfinite(
            frozen_array
        )
        &
        np.isfinite(
            current_array
        )
    )

    finite_pair_rows = int(
        np.sum(
            finite
        )
    )

    finite_pair_fraction = float(
        finite_pair_rows
        /
        len(
            frozen_train
        )
    )

    paired = pd.DataFrame(
        {
            "decision_time": (
                _utc_ns_series(
                    frozen_train[
                        "decision_time"
                    ]
                )
                .to_numpy()
            ),
            f"{feature}_frozen": (
                frozen_values.to_numpy()
            ),
            f"{feature}_current": (
                current_values.to_numpy()
            ),
        }
    )

    document = (
        base
        ._feature_comparison(
            paired,
            feature,
        )
    )

    psi = (
        _safe_float(
            document.get(
                "psi"
            )
        )
    )

    standardized_shift = (
        _safe_float(
            document.get(
                "standardized_mean_shift"
            )
        )
    )

    correlation = (
        _safe_float(
            document.get(
                "paired_correlation"
            )
        )
    )

    psi_material = bool(
        psi is not None
        and
        psi
        >=
        float(
            base.PSI_MATERIAL_THRESHOLD
        )
    )

    standardized_shift_material = bool(
        standardized_shift
        is not None
        and
        abs(
            standardized_shift
        )
        >=
        float(
            base.STANDARDIZED_MEAN_SHIFT_THRESHOLD
        )
    )

    material_distribution_shift = bool(
        psi_material
        or
        standardized_shift_material
    )

    correlation_warning = bool(
        correlation is not None
        and
        correlation
        <
        float(
            base.PRICE_CORRELATION_WARNING_THRESHOLD
        )
    )

    strong_correlation = bool(
        correlation is not None
        and
        correlation
        >=
        float(
            base.PRICE_CORRELATION_STRONG_THRESHOLD
        )
    )

    return {
        **document,
        "finite_pair_rows": (
            finite_pair_rows
        ),
        "finite_pair_fraction": (
            finite_pair_fraction
        ),
        "psi_material": (
            psi_material
        ),
        "standardized_mean_shift_material": (
            standardized_shift_material
        ),
        "material_distribution_shift": (
            material_distribution_shift
        ),
        "correlation_warning": (
            correlation_warning
        ),
        "strong_correlation": (
            strong_correlation
        ),
    }


def _group_summary(
    *,
    group_name: str,
    features: Sequence[
        str
    ],
    comparisons_by_feature: Mapping[
        str,
        Mapping[
            str,
            Any,
        ]
    ],
) -> dict[str, Any]:

    documents = [
        comparisons_by_feature[
            feature
        ]
        for feature
        in features
    ]

    correlations = [
        _safe_float(
            document.get(
                "paired_correlation"
            )
        )
        for document
        in documents
    ]

    psis = [
        _safe_float(
            document.get(
                "psi"
            )
        )
        for document
        in documents
    ]

    standardized_shifts = [
        _safe_float(
            document.get(
                "standardized_mean_shift"
            )
        )
        for document
        in documents
    ]

    finite_fractions = [
        _safe_float(
            document.get(
                "finite_pair_fraction"
            )
        )
        for document
        in documents
    ]

    correlated_feature_count = int(
        sum(
            1
            for value
            in correlations
            if value is not None
        )
    )

    strong_features = [
        feature
        for feature, document
        in zip(
            features,
            documents,
            strict=True,
        )
        if bool(
            document.get(
                "strong_correlation",
                False,
            )
        )
    ]

    correlation_warning_features = [
        feature
        for feature, document
        in zip(
            features,
            documents,
            strict=True,
        )
        if bool(
            document.get(
                "correlation_warning",
                False,
            )
        )
    ]

    material_shift_features = [
        feature
        for feature, document
        in zip(
            features,
            documents,
            strict=True,
        )
        if bool(
            document.get(
                "material_distribution_shift",
                False,
            )
        )
    ]

    psi_material_features = [
        feature
        for feature, document
        in zip(
            features,
            documents,
            strict=True,
        )
        if bool(
            document.get(
                "psi_material",
                False,
            )
        )
    ]

    mean_shift_material_features = [
        feature
        for feature, document
        in zip(
            features,
            documents,
            strict=True,
        )
        if bool(
            document.get(
                "standardized_mean_shift_material",
                False,
            )
        )
    ]

    low_coverage_features: list[
        str
    ] = []

    for (
        feature,
        document,
    ) in zip(
        features,
        documents,
        strict=True,
    ):

        finite_fraction = (
            _safe_float(
                document.get(
                    "finite_pair_fraction"
                )
            )
        )

        if (
            finite_fraction
            is None
            or
            finite_fraction
            <
            MIN_FEATURE_FINITE_PAIR_FRACTION
        ):

            low_coverage_features.append(
                feature
            )

    material_share = float(
        len(
            material_shift_features
        )
        /
        len(
            features
        )
    )

    strong_share = (
        float(
            len(
                strong_features
            )
            /
            correlated_feature_count
        )
        if correlated_feature_count
        >
        0
        else
        None
    )

    return {
        "group": (
            group_name
        ),
        "feature_count": int(
            len(
                features
            )
        ),
        "features_with_correlation": (
            correlated_feature_count
        ),
        "median_paired_correlation": (
            _median_finite(
                correlations
            )
        ),
        "strong_correlation_feature_count": int(
            len(
                strong_features
            )
        ),
        "strong_correlation_share_of_correlated": (
            strong_share
        ),
        "correlation_warning_feature_count": int(
            len(
                correlation_warning_features
            )
        ),
        "median_psi": (
            _median_finite(
                psis
            )
        ),
        "median_abs_standardized_mean_shift": (
            _median_finite(
                [
                    abs(
                        value
                    )
                    if value
                    is not None
                    else None
                    for value
                    in standardized_shifts
                ]
            )
        ),
        "max_abs_standardized_mean_shift": (
            _maximum_finite(
                [
                    abs(
                        value
                    )
                    if value
                    is not None
                    else None
                    for value
                    in standardized_shifts
                ]
            )
        ),
        "material_distribution_shift_feature_count": int(
            len(
                material_shift_features
            )
        ),
        "material_distribution_shift_share": (
            material_share
        ),
        "psi_material_feature_count": int(
            len(
                psi_material_features
            )
        ),
        "standardized_mean_shift_material_feature_count": int(
            len(
                mean_shift_material_features
            )
        ),
        "median_finite_pair_fraction": (
            _median_finite(
                finite_fractions
            )
        ),
        "minimum_finite_pair_fraction": (
            _minimum_finite(
                finite_fractions
            )
        ),
        "low_coverage_feature_count": int(
            len(
                low_coverage_features
            )
        ),
        "strong_correlation_features": (
            strong_features
        ),
        "correlation_warning_features": (
            correlation_warning_features
        ),
        "material_distribution_shift_features": (
            material_shift_features
        ),
        "low_coverage_features": (
            low_coverage_features
        ),
    }


def _group_status(
    summary: Mapping[
        str,
        Any,
    ],
    *,
    group_kind: str,
) -> dict[str, Any]:

    minimum_coverage = (
        _safe_float(
            summary.get(
                "minimum_finite_pair_fraction"
            )
        )
    )

    median_correlation = (
        _safe_float(
            summary.get(
                "median_paired_correlation"
            )
        )
    )

    material_share = (
        _safe_float(
            summary.get(
                "material_distribution_shift_share"
            )
        )
    )

    low_coverage_count = (
        _coerce_int(
            summary.get(
                "low_coverage_feature_count",
                0,
            )
        )
    )

    if (
        minimum_coverage
        is None
        or
        minimum_coverage
        <
        MIN_FEATURE_FINITE_PAIR_FRACTION
        or
        low_coverage_count
        >
        0
    ):

        return {
            "status": (
                "INSUFFICIENT_CURRENT_BROKER_COVERAGE"
            ),
            "portable": False,
            "reason": (
                "ONE_OR_MORE_FEATURES_HAVE_INSUFFICIENT_"
                "FINITE_SAME_DECISION_TIME_PAIRS"
            ),
        }

    if (
        group_kind
        ==
        "BROKER_SENSITIVE"
    ):

        material_count = (
            _coerce_int(
                summary.get(
                    "material_distribution_shift_feature_count",
                    0,
                )
            )
        )

        if material_count > 0:

            return {
                "status": (
                    "NORMALIZATION_REQUIRED"
                ),
                "portable": False,
                "reason": (
                    "BROKER_SENSITIVE_FEATURES_HAVE_"
                    "MATERIAL_DISTRIBUTION_SHIFT"
                ),
            }

        return {
            "status": (
                "BROKER_SENSITIVE_PRELIMINARY_PORTABLE"
            ),
            "portable": True,
            "reason": (
                "NO_MATERIAL_BROKER_SENSITIVE_SHIFT_DETECTED"
            ),
        }

    if (
        group_kind
        ==
        "UTC"
    ):

        if (
            median_correlation
            is not None
            and
            median_correlation
            >=
            MIN_UTC_MEDIAN_CORRELATION
            and
            material_share
            is not None
            and
            material_share
            ==
            0.0
        ):

            return {
                "status": (
                    "UTC_DECISION_TIME_ENCODING_REPRODUCED"
                ),
                "portable": True,
                "reason": (
                    "UTC_CYCLICAL_FEATURES_MATCH_CANONICAL_"
                    "DECISION_TIME_SEMANTICS"
                ),
            }

        return {
            "status": (
                "UTC_DECISION_TIME_ENCODING_NOT_REPRODUCED"
            ),
            "portable": False,
            "reason": (
                "UTC_CYCLICAL_FEATURES_DO_NOT_MATCH_"
                "FROZEN_DECISION_TIME_CONTRACT"
            ),
        }

    if (
        median_correlation
        is None
        or
        median_correlation
        <
        MIN_GROUP_MEDIAN_CORRELATION
    ):

        return {
            "status": (
                "PORTABILITY_NOT_CONFIRMED"
            ),
            "portable": False,
            "reason": (
                "GROUP_MEDIAN_SAME_DECISION_TIME_CORRELATION_"
                "BELOW_THRESHOLD"
            ),
        }

    if (
        material_share
        is None
        or
        material_share
        >
        MAX_GROUP_MATERIAL_SHIFT_SHARE
    ):

        return {
            "status": (
                "PORTABILITY_NOT_CONFIRMED"
            ),
            "portable": False,
            "reason": (
                "TOO_MANY_FEATURES_HAVE_MATERIAL_"
                "DISTRIBUTION_SHIFT"
            ),
        }

    return {
        "status": (
            "TRAIN_ONLY_PRELIMINARY_PORTABLE"
        ),
        "portable": True,
        "reason": (
            "GROUP_MEETS_PREDECLARED_CORRELATION_"
            "DISTRIBUTION_AND_COVERAGE_THRESHOLDS"
        ),
    }


def _overall_decision(
    *,
    technical_statuses: Mapping[
        str,
        Mapping[
            str,
            Any,
        ]
    ],
    age_status: Mapping[
        str,
        Any,
    ],
    utc_status: Mapping[
        str,
        Any,
    ],
    domain_status: Mapping[
        str,
        Any,
    ],
    broker_status: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    failed_technical_timeframes = [
        timeframe
        for timeframe, document
        in technical_statuses.items()
        if not bool(
            document.get(
                "portable",
                False,
            )
        )
    ]

    if failed_technical_timeframes:

        classification = (
            "FULL_MTF_TECHNICAL_PORTABILITY_NOT_CONFIRMED"
        )

        reason = (
            "ONE_OR_MORE_TIMEFRAME_TECHNICAL_GROUPS_"
            "FAIL_TRAIN_ONLY_PORTABILITY_THRESHOLDS"
        )

        next_action = (
            "ISOLATE_FAILED_TIMEFRAMES_AND_AUDIT_"
            "BROKER_BAR_AGGREGATION_BOUNDARIES"
        )

    elif not bool(
        utc_status.get(
            "portable",
            False,
        )
    ):

        classification = (
            "CANONICAL_DECISION_TIME_CONTRACT_NOT_REPRODUCED"
        )

        reason = (
            "UTC_CALENDAR_FEATURES_DO_NOT_MATCH_"
            "FROZEN_CANONICAL_DECISION_TIME"
        )

        next_action = (
            "STOP_AND_AUDIT_DECISION_TIME_CANONICALIZATION"
        )

    elif not bool(
        age_status.get(
            "portable",
            False,
        )
    ):

        classification = (
            "HTF_ALIGNMENT_METADATA_PORTABILITY_NOT_CONFIRMED"
        )

        reason = (
            "HIGHER_TIMEFRAME_AGE_FEATURES_DO_NOT_"
            "MATCH_FROZEN_CAUSAL_ALIGNMENT_SEMANTICS"
        )

        next_action = (
            "AUDIT_FAILED_HTF_AVAILABILITY_AND_BAR_CLOSE_MAPPING"
        )

    elif not bool(
        domain_status.get(
            "portable",
            False,
        )
    ):

        classification = (
            "DOMAIN_FEATURE_PORTABILITY_NOT_CONFIRMED"
        )

        reason = (
            "CAUSAL_M5_DOMAIN_FEATURES_DO_NOT_MEET_"
            "TRAIN_ONLY_CROSS_BROKER_PORTABILITY_THRESHOLDS"
        )

        next_action = (
            "ISOLATE_UNSTABLE_DOMAIN_FEATURE_FAMILIES_"
            "BEFORE_ANY_NEW_PORTABLE_FEATURE_CONTRACT"
        )

    elif not bool(
        broker_status.get(
            "portable",
            False,
        )
    ):

        classification = (
            "NORMALIZATION_REQUIRED"
        )

        reason = (
            "PRICE_MTF_DOMAIN_AND_ALIGNMENT_GROUPS_PASS_"
            "BUT_BROKER_SENSITIVE_FEATURES_REQUIRE_NORMALIZATION"
        )

        next_action = (
            "DESIGN_NEW_XAUUSD_PORTABLE_FEATURE_CONTRACT_"
            "FOR_BROKER_SENSITIVE_FIELDS_WITHOUT_MUTATING_V3"
        )

    else:

        classification = (
            "FULL_333_TRAIN_ONLY_PRELIMINARY_PORTABLE"
        )

        reason = (
            "ALL_FEATURE_GROUPS_MEET_TRAIN_ONLY_"
            "CROSS_BROKER_PORTABILITY_THRESHOLDS"
        )

        next_action = (
            "FREEZE_RESEARCH_PORTABILITY_CONTRACT_"
            "BEFORE_ANY_FORWARD_OR_MODEL_EVALUATION"
        )

    return {
        "classification": (
            classification
        ),
        "reason": (
            reason
        ),
        "failed_technical_timeframes": (
            failed_technical_timeframes
        ),
        "technical_all_portable": (
            not failed_technical_timeframes
        ),
        "age_group_portable": bool(
            age_status.get(
                "portable",
                False,
            )
        ),
        "utc_group_portable": bool(
            utc_status.get(
                "portable",
                False,
            )
        ),
        "domain_group_portable": bool(
            domain_status.get(
                "portable",
                False,
            )
        ),
        "broker_sensitive_group_portable": bool(
            broker_status.get(
                "portable",
                False,
            )
        ),
        "broker_specific_retraining_authorized": (
            False
        ),
        "test_evaluation_authorized": (
            False
        ),
        "full_333_live_portability_claimed": (
            False
        ),
        "next_action": (
            next_action
        ),
    }


def run_analysis(
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

    base_feature_names = (
        base
        ._base_feature_names()
    )

    groups = (
        _feature_groups(
            manifest,
            base_feature_names,
        )
    )

    frozen_train = (
        base
        ._load_frozen_train_only(
            dataset_path,
            groups[
                "frozen_features"
            ],
        )
    )

    frozen_train = (
        _normalize_time_column(
            frozen_train,
            "decision_time",
        )
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

    _require(
        not pd.isna(
            train_start
        ),
        "TRAIN_START_INVALID",
    )

    _require(
        not pd.isna(
            train_end
        ),
        "TRAIN_END_INVALID",
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

    initialized = mt5.initialize()

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

        (
            raw_frames,
            raw_history_meta,
        ) = (
            _fetch_current_timeframes(
                broker_symbol=(
                    broker_symbol
                ),
                train_start=(
                    train_start
                ),
                train_end=(
                    train_end
                ),
            )
        )

        (
            current_matrix,
            generation_meta,
        ) = (
            _build_current_feature_matrix(
                frozen_train=(
                    frozen_train
                ),
                groups=(
                    groups
                ),
                raw_frames=(
                    raw_frames
                ),
                base_feature_names=(
                    base_feature_names
                ),
            )
        )

        comparison_documents = [
            _compare_feature(
                frozen_train=(
                    frozen_train
                ),
                current_matrix=(
                    current_matrix
                ),
                feature=(
                    feature
                ),
            )
            for feature
            in groups[
                "frozen_features"
            ]
        ]

        comparisons_by_feature = {
            str(
                document[
                    "feature"
                ]
            ): document
            for document
            in comparison_documents
        }

        technical_summaries: dict[
            str,
            Any,
        ] = {}

        technical_statuses: dict[
            str,
            Any,
        ] = {}

        for timeframe in (
            TIMEFRAMES
        ):

            summary = (
                _group_summary(
                    group_name=(
                        f"TECHNICAL_{timeframe}"
                    ),
                    features=(
                        groups[
                            "technical"
                        ][
                            timeframe
                        ]
                    ),
                    comparisons_by_feature=(
                        comparisons_by_feature
                    ),
                )
            )

            status = (
                _group_status(
                    summary,
                    group_kind="TECHNICAL",
                )
            )

            technical_summaries[
                timeframe
            ] = (
                summary
            )

            technical_statuses[
                timeframe
            ] = (
                status
            )

        age_summary = (
            _group_summary(
                group_name="HTF_AGE",
                features=(
                    groups[
                        "age"
                    ]
                ),
                comparisons_by_feature=(
                    comparisons_by_feature
                ),
            )
        )

        age_status = (
            _group_status(
                age_summary,
                group_kind="AGE",
            )
        )

        utc_summary = (
            _group_summary(
                group_name="UTC_CALENDAR",
                features=(
                    groups[
                        "utc"
                    ]
                ),
                comparisons_by_feature=(
                    comparisons_by_feature
                ),
            )
        )

        utc_status = (
            _group_status(
                utc_summary,
                group_kind="UTC",
            )
        )

        domain_summary = (
            _group_summary(
                group_name="M5_DOMAIN",
                features=(
                    groups[
                        "domain"
                    ]
                ),
                comparisons_by_feature=(
                    comparisons_by_feature
                ),
            )
        )

        domain_status = (
            _group_status(
                domain_summary,
                group_kind="DOMAIN",
            )
        )

        broker_summary = (
            _group_summary(
                group_name="BROKER_SENSITIVE",
                features=(
                    groups[
                        "broker_sensitive"
                    ]
                ),
                comparisons_by_feature=(
                    comparisons_by_feature
                ),
            )
        )

        broker_status = (
            _group_status(
                broker_summary,
                group_kind="BROKER_SENSITIVE",
            )
        )

        decision = (
            _overall_decision(
                technical_statuses=(
                    technical_statuses
                ),
                age_status=(
                    age_status
                ),
                utc_status=(
                    utc_status
                ),
                domain_status=(
                    domain_status
                ),
                broker_status=(
                    broker_status
                ),
            )
        )

        return {
            "valid": True,
            "reason": (
                "OK_XAUUSD_CURRENT_BROKER_"
                "FULL_MTF_PORTABILITY_AUDIT"
            ),
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "research_scope": (
                "FULL_333_FEATURE_TRAIN_ONLY_"
                "CROSS_BROKER_PORTABILITY"
            ),
            "datetime_join_contract": {
                "canonical_dtype": (
                    CANONICAL_DATETIME_DTYPE
                ),
                "normalization_applied_before_all_asof_joins": (
                    True
                ),
                "normalization_applied_before_all_exact_joins": (
                    True
                ),
                "timezone": (
                    "UTC"
                ),
                "resolution": (
                    "NANOSECONDS"
                ),
            },
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
                "identity": (
                    base
                    ._safe_frozen_identity(
                        manifest
                    )
                ),
                "split_loaded": (
                    "TRAIN_ONLY"
                ),
                "rows_loaded": int(
                    len(
                        frozen_train
                    )
                ),
                "feature_count": int(
                    len(
                        groups[
                            "frozen_features"
                        ]
                    )
                ),
                "decision_time_dtype": (
                    str(
                        frozen_train[
                            "decision_time"
                        ].dtype
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
                "historical_timeframes": (
                    raw_history_meta
                ),
            },
            "confirmed_time_semantics": {
                "broker_clock_mapping": (
                    mapped
                    ._mapping_contract()
                ),
                "m5_feature_availability_shift_seconds": (
                    mapped
                    .FEATURE_AVAILABILITY_SHIFT_SECONDS
                ),
                "m5_feature_availability_shift_m5_bars": (
                    1.0
                ),
                "context_feature_availability_rule": (
                    "BAR_FEATURES_AVAILABLE_ONLY_AFTER_BAR_CLOSE"
                ),
                "context_alignment_rule": (
                    "BACKWARD_MERGE_ASOF_ALLOW_EXACT_MATCHES"
                ),
                "age_feature_rule": (
                    "DECISION_TIME_MINUS_CONTEXT_AVAILABLE_TIME_MINUTES"
                ),
                "utc_feature_rule": (
                    "SINE_COSINE_FROM_CANONICAL_DECISION_TIME"
                ),
                "domain_feature_rule": (
                    "BASE_M5_DOMAIN_FEATURES_AVAILABLE_AFTER_M5_CLOSE"
                ),
            },
            "feature_contract": {
                "total_feature_count": (
                    EXPECTED_TOTAL_FEATURE_COUNT
                ),
                "technical_feature_count": int(
                    len(
                        TIMEFRAMES
                    )
                    *
                    EXPECTED_TECHNICAL_COUNT_PER_TIMEFRAME
                ),
                "technical_feature_count_per_timeframe": (
                    EXPECTED_TECHNICAL_COUNT_PER_TIMEFRAME
                ),
                "domain_feature_count": int(
                    len(
                        groups[
                            "domain"
                        ]
                    )
                ),
                "broker_sensitive_feature_count": int(
                    len(
                        groups[
                            "broker_sensitive"
                        ]
                    )
                ),
                "age_feature_count": int(
                    len(
                        groups[
                            "age"
                        ]
                    )
                ),
                "utc_feature_count": int(
                    len(
                        groups[
                            "utc"
                        ]
                    )
                ),
                "timeframes": list(
                    TIMEFRAMES
                ),
                "broker_sensitive_features": (
                    groups[
                        "broker_sensitive"
                    ]
                ),
                "age_features": (
                    groups[
                        "age"
                    ]
                ),
                "utc_features": (
                    groups[
                        "utc"
                    ]
                ),
            },
            "current_feature_generation": (
                generation_meta
            ),
            "thresholds": {
                "minimum_feature_finite_pair_fraction": (
                    MIN_FEATURE_FINITE_PAIR_FRACTION
                ),
                "minimum_group_median_correlation": (
                    MIN_GROUP_MEDIAN_CORRELATION
                ),
                "maximum_group_material_shift_share": (
                    MAX_GROUP_MATERIAL_SHIFT_SHARE
                ),
                "minimum_utc_median_correlation": (
                    MIN_UTC_MEDIAN_CORRELATION
                ),
                "psi_warning": (
                    base.PSI_WARNING_THRESHOLD
                ),
                "psi_material": (
                    base.PSI_MATERIAL_THRESHOLD
                ),
                "standardized_mean_shift_material": (
                    base
                    .STANDARDIZED_MEAN_SHIFT_THRESHOLD
                ),
                "correlation_warning": (
                    base
                    .PRICE_CORRELATION_WARNING_THRESHOLD
                ),
                "correlation_strong": (
                    base
                    .PRICE_CORRELATION_STRONG_THRESHOLD
                ),
            },
            "group_summaries": {
                "technical_by_timeframe": (
                    technical_summaries
                ),
                "age": (
                    age_summary
                ),
                "utc": (
                    utc_summary
                ),
                "domain": (
                    domain_summary
                ),
                "broker_sensitive": (
                    broker_summary
                ),
            },
            "group_statuses": {
                "technical_by_timeframe": (
                    technical_statuses
                ),
                "age": (
                    age_status
                ),
                "utc": (
                    utc_status
                ),
                "domain": (
                    domain_status
                ),
                "broker_sensitive": (
                    broker_status
                ),
            },
            "classification": (
                decision
            ),
            "feature_comparisons": (
                comparison_documents
            ),
            "scientific_policy": {
                "frozen_dataset_mutated": (
                    False
                ),
                "frozen_manifest_mutated": (
                    False
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
                "if_full_mtf_technical_not_confirmed": (
                    "ISOLATE_FAILED_TIMEFRAME_BAR_AGGREGATION_"
                    "AND_CLOCK_BOUNDARY_SEMANTICS"
                ),
                "if_age_not_confirmed": (
                    "AUDIT_ONLY_FAILED_HTF_AVAILABILITY_ALIGNMENT"
                ),
                "if_domain_not_confirmed": (
                    "ISOLATE_UNSTABLE_DOMAIN_FEATURE_FAMILIES_"
                    "BEFORE_PORTABLE_CONTRACT_DESIGN"
                ),
                "if_only_broker_sensitive_normalization_required": (
                    "DESIGN_NEW_XAUUSD_PORTABLE_FEATURE_CONTRACT_"
                    "WITHOUT_MUTATING_FROZEN_V3"
                ),
                "if_full_333_preliminary_portable": (
                    "FREEZE_RESEARCH_PORTABILITY_CONTRACT_"
                    "BEFORE_FORWARD_OR_MODEL_EVALUATION"
                ),
                "broker_specific_retraining_not_authorized": (
                    True
                ),
                "test_holdout_remains_untouched": (
                    True
                ),
                "v3_contract_not_mutated": (
                    True
                ),
            },
            "live_authorized": False,
        }

    finally:

        mt5.shutdown()


def main() -> int:

    try:

        result = (
            run_analysis()
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
                        "XAUUSD_CURRENT_BROKER_"
                        "FULL_MTF_PORTABILITY_AUDIT_FAILED"
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