from __future__ import annotations

import importlib
import json
import math
import sys
from functools import reduce
from math import gcd
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
    "XAUUSD_PORTABLE_BROKER_SENSITIVE_REPLACEMENT_AUDIT_V1"
)

FULL_AUDIT_MODULE = (
    "04_Testing."
    "analyze_xauusd_current_broker_full_mtf_portability"
)

SOURCE_MODULE = (
    "04_Testing."
    "diagnose_xauusd_frozen_d1_source_aggregation"
)

METRICS_MODULE = (
    "04_Testing."
    "audit_xauusd_current_broker_d1_corrected_portability"
)

FINAL_ADJUDICATOR_MODULE = (
    "04_Testing."
    "adjudicate_xauusd_current_broker_full_333_portability"
)


full: Any = importlib.import_module(
    FULL_AUDIT_MODULE
)

source: Any = importlib.import_module(
    SOURCE_MODULE
)

metrics: Any = importlib.import_module(
    METRICS_MODULE
)

adjudicator: Any = importlib.import_module(
    FINAL_ADJUDICATOR_MODULE
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


FINAL_ADJUDICATION_JSON = (
    ROOT_DIR
    /
    "04_Testing/evidence/production_portability/xauusd_current_broker_full_333_evidence_adjudication.json"
)


EXPECTED_FINAL_CLASSIFICATION = (
    "XAUUSD_330_NON_BROKER_SENSITIVE_FEATURES_"
    "TRAIN_PORTABILITY_CONFIRMED"
)

EXPECTED_TRAIN_ROWS = 69966

EXPECTED_RETAINED_BASE_FEATURE_COUNT = 331


M5_AVAILABILITY_MINUTES = 5

CURRENT_HISTORY_WARMUP_DAYS = 30


MINIMUM_FINITE_PAIR_FRACTION = 0.90

MINIMUM_PAIRED_CORRELATION = 0.80

PSI_MATERIAL = 0.25

STANDARDIZED_MEAN_SHIFT_MATERIAL = 0.50


SOURCE_VALIDATION_MINIMUM_CORRELATION = 0.999

SOURCE_VALIDATION_MAXIMUM_STANDARDIZED_SHIFT = 1e-5


SPREAD_CANDIDATES = (
    "spread_atr",
    "spread_bps",
    "spread_ratio100",
    "spread_ratio20",
    "spread_ticks",
)


SPREAD_SELECTION_PREFERENCE = (
    "spread_atr",
    "spread_bps",
    "spread_ratio100",
    "spread_ratio20",
    "spread_ticks",
)


TICK_VOLUME_CANDIDATES = (
    "tick_volume_ratio100",
    "tick_volume_ratio288",
    "tick_volume_zscore100",
    "tick_volume_zscore288",
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

    return result


def _validate_final_prerequisite(
) -> Mapping[str, Any]:

    document = (
        adjudicator
        ._load_json(
            FINAL_ADJUDICATION_JSON
        )
    )

    _require(
        bool(
            document.get(
                "valid",
                False,
            )
        ),
        "FINAL_333_ADJUDICATION_INVALID",
    )

    classification = (
        adjudicator
        ._mapping(
            document,
            "classification",
        )
    )

    observed = str(
        classification.get(
            "classification",
            "",
        )
    )

    _require(
        observed
        ==
        EXPECTED_FINAL_CLASSIFICATION,
        (
            "FINAL_CLASSIFICATION_MISMATCH:"
            f"{observed}"
        ),
    )

    _require(
        bool(
            classification.get(
                "non_broker_sensitive_330_portable",
                False,
            )
        ),
        "NON_BROKER_SENSITIVE_330_NOT_CONFIRMED",
    )

    _require(
        not bool(
            classification.get(
                "full_333_portable_as_is",
                True,
            )
        ),
        "FULL_333_UNEXPECTEDLY_PORTABLE_AS_IS",
    )

    _require(
        bool(
            classification.get(
                "broker_sensitive_normalization_required",
                False,
            )
        ),
        "BROKER_SENSITIVE_NORMALIZATION_NOT_REQUIRED",
    )

    _require(
        not bool(
            classification.get(
                "test_evaluation_authorized",
                True,
            )
        ),
        "TEST_UNEXPECTEDLY_AUTHORIZED",
    )

    return document


def _technical_features(
    manifest: Mapping[
        str,
        Any,
    ],
) -> list[str]:

    base_names = (
        base
        ._base_feature_names()
    )

    groups = (
        full
        ._feature_groups(
            manifest,
            base_names,
        )
    )

    features = [
        str(
            value
        )
        for value
        in groups[
            "technical"
        ][
            "M5"
        ]
    ]

    _require(
        "m5_atr14"
        in
        features,
        "M5_ATR14_NOT_IN_TECHNICAL_CONTRACT",
    )

    return features


def _clock_map_current_m5(
    raw_m5: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

    required = {
        "time",
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
        "spread",
    }

    missing = sorted(
        required
        -
        set(
            str(
                column
            )
            for column
            in raw_m5.columns
        )
    )

    _require(
        not missing,
        (
            "CURRENT_M5_REQUIRED_COLUMNS_MISSING:"
            f"{missing}"
        ),
    )

    frame = (
        raw_m5.copy()
    )

    frame[
        "source_broker_time"
    ] = (
        _canonical_time(
            frame[
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
            frame[
                "source_broker_time"
            ]
        )
    )

    frame[
        "time"
    ] = (
        _canonical_time(
            canonical_time
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

    duplicate_rows = int(
        frame[
            "time"
        ]
        .duplicated(
            keep=False
        )
        .sum()
    )

    _require(
        duplicate_rows
        ==
        0,
        (
            "CURRENT_CANONICAL_M5_DUPLICATE_ROWS:"
            f"{duplicate_rows}"
        ),
    )

    return (
        frame,
        {
            **mapping_meta,
            "duplicate_canonical_m5_rows": (
                duplicate_rows
            ),
        },
    )


def _infer_quote_point(
    frame: pd.DataFrame,
) -> tuple[
    float,
    dict[str, Any],
]:

    values: list[
        np.ndarray
    ] = []

    for column in (
        "open",
        "high",
        "low",
        "close",
    ):

        numeric = np.asarray(
            pd.to_numeric(
                frame[
                    column
                ],
                errors="coerce",
            ),
            dtype=np.float64,
        )

        numeric = (
            numeric[
                np.isfinite(
                    numeric
                )
            ]
        )

        if (
            numeric.size
            >
            0
        ):

            values.append(
                numeric
            )

    _require(
        bool(
            values
        ),
        "NO_PRICE_VALUES_FOR_POINT_INFERENCE",
    )

    sample = np.concatenate(
        values
    )

    if (
        sample.size
        >
        50000
    ):

        indexes = np.linspace(
            0,
            sample.size - 1,
            50000,
            dtype=np.int64,
        )

        sample = (
            sample[
                indexes
            ]
        )

    selected_digits: (
        int
        |
        None
    ) = None

    selected_quantile: (
        float
        |
        None
    ) = None

    for digits in range(
        0,
        7,
    ):

        scale = float(
            10 ** digits
        )

        scaled = (
            sample
            *
            scale
        )

        residual = np.abs(
            scaled
            -
            np.rint(
                scaled
            )
        )

        q999 = float(
            np.quantile(
                residual,
                0.999,
            )
        )

        if (
            q999
            <=
            1e-6
        ):

            selected_digits = (
                digits
            )

            selected_quantile = (
                q999
            )

            break

    if selected_digits is None:
        raise RuntimeError(
            "FROZEN_QUOTE_POINT_INFERENCE_FAILED"
        )

    selected_digits_value: int = (
        selected_digits
    )

    point = float(
        10
        **
        (
            -selected_digits_value
        )
    )

    return (
        point,
        {
            "source": (
                "RAW_PRICE_DECIMAL_LATTICE_INFERENCE"
            ),
            "digits": (
                selected_digits_value
            ),
            "point": (
                point
            ),
            "residual_q999": (
                selected_quantile
            ),
        },
    )


def _infer_tick_size(
    frame: pd.DataFrame,
    *,
    point: float,
) -> tuple[
    float,
    dict[str, Any],
]:

    _require(
        point
        >
        0.0,
        "INVALID_POINT_FOR_TICK_SIZE_INFERENCE",
    )

    close = np.asarray(
        pd.to_numeric(
            frame[
                "close"
            ],
            errors="coerce",
        ),
        dtype=np.float64,
    )

    finite = (
        np.isfinite(
            close
        )
    )

    close = (
        close[
            finite
        ]
    )

    _require(
        close.size
        >=
        100,
        "INSUFFICIENT_CLOSE_VALUES_FOR_TICK_INFERENCE",
    )

    units = np.rint(
        close
        /
        point
    ).astype(
        np.int64
    )

    differences = np.abs(
        np.diff(
            units
        )
    )

    differences = (
        differences[
            differences
            >
            0
        ]
    )

    _require(
        differences.size
        >
        0,
        "NO_POSITIVE_PRICE_DIFFERENCES_FOR_TICK_INFERENCE",
    )

    if (
        differences.size
        >
        20000
    ):

        differences = (
            differences[
                :20000
            ]
        )

    integer_gcd = int(
        reduce(
            gcd,
            (
                int(
                    value
                )
                for value
                in differences
            ),
        )
    )

    _require(
        integer_gcd
        >=
        1,
        (
            "INVALID_INFERRED_TICK_GCD:"
            f"{integer_gcd}"
        ),
    )

    tick_size = float(
        integer_gcd
        *
        point
    )

    return (
        tick_size,
        {
            "source": (
                "RAW_CLOSE_PRICE_LATTICE_GCD_INFERENCE"
            ),
            "point_units_per_tick": (
                integer_gcd
            ),
            "tick_size": (
                tick_size
            ),
        },
    )


def _generate_m5_atr(
    *,
    builder: Any,
    raw_m5: pd.DataFrame,
) -> pd.DataFrame:

    generated = (
        builder
        ._generate_feature_frame(
            frame=(
                raw_m5
            ),
            timeframe="M5",
        )
    )

    _require(
        isinstance(
            generated,
            pd.DataFrame,
        ),
        "M5_FEATURE_GENERATOR_NOT_DATAFRAME",
    )

    required = {
        "time",
        "available_time",
        "m5_atr14",
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
            "GENERATED_M5_COLUMNS_MISSING:"
            f"{missing}"
        ),
    )

    result = (
        generated[
            [
                "time",
                "available_time",
                "m5_atr14",
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

    duplicate_rows = int(
        result[
            "available_time"
        ]
        .duplicated(
            keep=False
        )
        .sum()
    )

    _require(
        duplicate_rows
        ==
        0,
        (
            "GENERATED_M5_AVAILABLE_TIME_DUPLICATES:"
            f"{duplicate_rows}"
        ),
    )

    return (
        result
        .sort_values(
            "available_time"
        )
        .reset_index(
            drop=True
        )
    )


def _safe_ratio(
    numerator: pd.Series,
    denominator: pd.Series,
) -> pd.Series:

    numerator_numeric = pd.to_numeric(
        numerator,
        errors="coerce",
    )

    denominator_numeric = pd.to_numeric(
        denominator,
        errors="coerce",
    )

    result = (
        numerator_numeric
        /
        denominator_numeric.where(
            denominator_numeric.abs()
            >
            1e-15
        )
    )

    return (
        result.astype(
            np.float64
        )
    )


def _candidate_frame(
    *,
    raw_m5: pd.DataFrame,
    generated_atr: pd.DataFrame,
    point: float,
    tick_size: float,
) -> pd.DataFrame:

    _require(
        point
        >
        0.0,
        "INVALID_POINT",
    )

    _require(
        tick_size
        >
        0.0,
        "INVALID_TICK_SIZE",
    )

    frame = (
        raw_m5[
            [
                "time",
                "close",
                "tick_volume",
                "spread",
            ]
        ]
        .copy()
    )

    frame[
        "time"
    ] = (
        _canonical_time(
            frame[
                "time"
            ]
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

    frame[
        "available_time"
    ] = (
        frame[
            "time"
        ]
        +
        pd.Timedelta(
            minutes=(
                M5_AVAILABILITY_MINUTES
            )
        )
    )

    frame[
        "available_time"
    ] = (
        _canonical_time(
            frame[
                "available_time"
            ]
        )
    )

    frame[
        "source_spread_points"
    ] = pd.to_numeric(
        frame[
            "spread"
        ],
        errors="coerce",
    )

    frame[
        "source_tick_volume"
    ] = pd.to_numeric(
        frame[
            "tick_volume"
        ],
        errors="coerce",
    )

    frame[
        "source_tick_volume_log1p"
    ] = np.log1p(
        frame[
            "source_tick_volume"
        ]
    )

    frame[
        "spread_price"
    ] = (
        frame[
            "source_spread_points"
        ]
        *
        point
    )

    frame[
        "spread_ticks"
    ] = (
        frame[
            "spread_price"
        ]
        /
        tick_size
    )

    frame[
        "spread_bps"
    ] = (
        _safe_ratio(
            frame[
                "spread_price"
            ],
            pd.to_numeric(
                frame[
                    "close"
                ],
                errors="coerce",
            ),
        )
        *
        10000.0
    )

    spread_median20 = (
        frame[
            "source_spread_points"
        ]
        .rolling(
            window=20,
            min_periods=20,
        )
        .median()
    )

    spread_median100 = (
        frame[
            "source_spread_points"
        ]
        .rolling(
            window=100,
            min_periods=100,
        )
        .median()
    )

    frame[
        "spread_ratio20"
    ] = (
        _safe_ratio(
            frame[
                "source_spread_points"
            ],
            spread_median20,
        )
    )

    frame[
        "spread_ratio100"
    ] = (
        _safe_ratio(
            frame[
                "source_spread_points"
            ],
            spread_median100,
        )
    )

    tick_mean20 = (
        frame[
            "source_tick_volume"
        ]
        .rolling(
            window=20,
            min_periods=20,
        )
        .mean()
    )

    tick_mean100 = (
        frame[
            "source_tick_volume"
        ]
        .rolling(
            window=100,
            min_periods=100,
        )
        .mean()
    )

    tick_mean288 = (
        frame[
            "source_tick_volume"
        ]
        .rolling(
            window=288,
            min_periods=288,
        )
        .mean()
    )

    frame[
        "tick_volume_ratio20_recomputed"
    ] = (
        _safe_ratio(
            frame[
                "source_tick_volume"
            ],
            tick_mean20,
        )
    )

    frame[
        "tick_volume_ratio100"
    ] = (
        _safe_ratio(
            frame[
                "source_tick_volume"
            ],
            tick_mean100,
        )
    )

    frame[
        "tick_volume_ratio288"
    ] = (
        _safe_ratio(
            frame[
                "source_tick_volume"
            ],
            tick_mean288,
        )
    )

    log_volume = (
        frame[
            "source_tick_volume_log1p"
        ]
    )

    log_mean100 = (
        log_volume
        .rolling(
            window=100,
            min_periods=100,
        )
        .mean()
    )

    log_std100 = (
        log_volume
        .rolling(
            window=100,
            min_periods=100,
        )
        .std(
            ddof=0
        )
    )

    log_mean288 = (
        log_volume
        .rolling(
            window=288,
            min_periods=288,
        )
        .mean()
    )

    log_std288 = (
        log_volume
        .rolling(
            window=288,
            min_periods=288,
        )
        .std(
            ddof=0
        )
    )

    frame[
        "tick_volume_zscore100"
    ] = (
        _safe_ratio(
            (
                log_volume
                -
                log_mean100
            ),
            log_std100,
        )
    )

    frame[
        "tick_volume_zscore288"
    ] = (
        _safe_ratio(
            (
                log_volume
                -
                log_mean288
            ),
            log_std288,
        )
    )

    atr = (
        generated_atr[
            [
                "available_time",
                "m5_atr14",
            ]
        ]
        .copy()
    )

    atr[
        "available_time"
    ] = (
        _canonical_time(
            atr[
                "available_time"
            ]
        )
    )

    frame = (
        frame
        .merge(
            atr,
            on="available_time",
            how="left",
            validate="one_to_one",
        )
    )

    frame[
        "spread_atr"
    ] = (
        _safe_ratio(
            frame[
                "spread_price"
            ],
            frame[
                "m5_atr14"
            ],
        )
    )

    output_columns = [
        "available_time",
        "source_spread_points",
        "source_tick_volume",
        "source_tick_volume_log1p",
        "m5_atr14",
        "spread_ticks",
        "spread_atr",
        "spread_bps",
        "spread_ratio20",
        "spread_ratio100",
        "tick_volume_ratio20_recomputed",
        "tick_volume_ratio100",
        "tick_volume_ratio288",
        "tick_volume_zscore100",
        "tick_volume_zscore288",
    ]

    return (
        frame[
            output_columns
        ]
        .copy()
        .sort_values(
            "available_time"
        )
        .reset_index(
            drop=True
        )
    )


def _align_candidate_frame(
    *,
    train_grid: pd.DataFrame,
    candidate_frame: pd.DataFrame,
    suffix: str,
) -> pd.DataFrame:

    left = (
        train_grid[
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
        candidate_frame.copy()
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

    rename_map = {
        column: (
            column
            +
            "_"
            +
            suffix
        )
        for column
        in right.columns
        if (
            column
            !=
            "available_time"
        )
    }

    right = (
        right.rename(
            columns=(
                rename_map
            )
        )
    )

    right = (
        right.rename(
            columns={
                "available_time": (
                    "available_time_"
                    +
                    suffix
                )
            }
        )
    )

    aligned = pd.merge_asof(
        left,
        right,
        left_on="decision_time",
        right_on=(
            "available_time_"
            +
            suffix
        ),
        direction="backward",
        allow_exact_matches=True,
    )

    return aligned


def _comparison(
    *,
    feature: str,
    frozen: pd.Series,
    current: pd.Series,
) -> dict[str, Any]:

    return (
        metrics
        ._feature_comparison(
            feature=(
                feature
            ),
            reference=(
                frozen
            ),
            current=(
                current
            ),
            category=(
                "BROKER_PORTABLE_CANDIDATE"
            ),
        )
    )


def _portable_candidate(
    comparison: Mapping[
        str,
        Any,
    ],
) -> bool:

    coverage = (
        _safe_float(
            comparison.get(
                "finite_pair_fraction"
            )
        )
    )

    correlation = (
        _safe_float(
            comparison.get(
                "paired_correlation"
            )
        )
    )

    standardized_shift = (
        _safe_float(
            comparison.get(
                "standardized_mean_shift"
            )
        )
    )

    psi = (
        _safe_float(
            comparison.get(
                "psi"
            )
        )
    )

    material_shift = bool(
        comparison.get(
            "material_distribution_shift",
            False,
        )
    )

    return bool(
        coverage
        is not None
        and
        coverage
        >=
        MINIMUM_FINITE_PAIR_FRACTION
        and
        correlation
        is not None
        and
        correlation
        >=
        MINIMUM_PAIRED_CORRELATION
        and
        not material_shift
        and
        (
            psi is None
            or
            psi
            <
            PSI_MATERIAL
        )
        and
        (
            standardized_shift is None
            or
            abs(
                standardized_shift
            )
            <
            STANDARDIZED_MEAN_SHIFT_MATERIAL
        )
    )


def _validate_frozen_source_replay(
    *,
    frozen_train: pd.DataFrame,
    frozen_aligned: pd.DataFrame,
) -> dict[str, Any]:

    spread = (
        _comparison(
            feature=(
                "frozen_source_spread_points_replay"
            ),
            frozen=(
                frozen_train[
                    "m5_spread_points"
                ]
            ),
            current=(
                frozen_aligned[
                    "source_spread_points_frozen"
                ]
            ),
        )
    )

    tick_log = (
        _comparison(
            feature=(
                "frozen_source_tick_volume_log1p_replay"
            ),
            frozen=(
                frozen_train[
                    "m5_tick_volume_log1p"
                ]
            ),
            current=(
                frozen_aligned[
                    "source_tick_volume_log1p_frozen"
                ]
            ),
        )
    )

    atr = (
        _comparison(
            feature=(
                "frozen_source_m5_atr14_replay"
            ),
            frozen=(
                frozen_train[
                    "m5_atr14"
                ]
            ),
            current=(
                frozen_aligned[
                    "m5_atr14_frozen"
                ]
            ),
        )
    )

    ratio20 = (
        _comparison(
            feature=(
                "frozen_tick_volume_ratio20_formula_check"
            ),
            frozen=(
                frozen_train[
                    "m5_tick_volume_ratio20"
                ]
            ),
            current=(
                frozen_aligned[
                    "tick_volume_ratio20_recomputed_frozen"
                ]
            ),
        )
    )

    for name, document in (
        (
            "SPREAD_POINTS",
            spread,
        ),
        (
            "TICK_VOLUME_LOG1P",
            tick_log,
        ),
        (
            "M5_ATR14",
            atr,
        ),
    ):

        correlation = (
            _safe_float(
                document.get(
                    "paired_correlation"
                )
            )
        )

        shift = (
            _safe_float(
                document.get(
                    "standardized_mean_shift"
                )
            )
        )

        _require(
            correlation
            is not None
            and
            correlation
            >=
            SOURCE_VALIDATION_MINIMUM_CORRELATION,
            (
                "FROZEN_SOURCE_REPLAY_CORRELATION_FAILED:"
                f"{name}:"
                f"{correlation}"
            ),
        )

        _require(
            shift is None
            or
            abs(
                shift
            )
            <=
            SOURCE_VALIDATION_MAXIMUM_STANDARDIZED_SHIFT,
            (
                "FROZEN_SOURCE_REPLAY_SHIFT_FAILED:"
                f"{name}:"
                f"{shift}"
            ),
        )

    return {
        "spread_points": (
            spread
        ),
        "tick_volume_log1p": (
            tick_log
        ),
        "m5_atr14": (
            atr
        ),
        "tick_volume_ratio20_formula_check": (
            ratio20
        ),
        "required_replays_confirmed": (
            True
        ),
    }


def _candidate_documents(
    *,
    frozen_aligned: pd.DataFrame,
    current_aligned: pd.DataFrame,
    candidates: Sequence[
        str
    ],
) -> dict[
    str,
    dict[str, Any],
]:

    documents: dict[
        str,
        dict[str, Any],
    ] = {}

    for feature in candidates:

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

        _require(
            frozen_column
            in
            frozen_aligned.columns,
            (
                "FROZEN_CANDIDATE_COLUMN_MISSING:"
                f"{frozen_column}"
            ),
        )

        _require(
            current_column
            in
            current_aligned.columns,
            (
                "CURRENT_CANDIDATE_COLUMN_MISSING:"
                f"{current_column}"
            ),
        )

        comparison = (
            _comparison(
                feature=(
                    feature
                ),
                frozen=(
                    frozen_aligned[
                        frozen_column
                    ]
                ),
                current=(
                    current_aligned[
                        current_column
                    ]
                ),
            )
        )

        documents[
            feature
        ] = {
            "portable": (
                _portable_candidate(
                    comparison
                )
            ),
            "comparison": (
                comparison
            ),
        }

    return documents


def _select_spread_candidate(
    documents: Mapping[
        str,
        Mapping[
            str,
            Any,
        ],
    ],
) -> str | None:

    for feature in (
        SPREAD_SELECTION_PREFERENCE
    ):

        document = (
            documents.get(
                feature
            )
        )

        if (
            isinstance(
                document,
                Mapping,
            )
            and
            bool(
                document.get(
                    "portable",
                    False,
                )
            )
        ):

            return feature

    return None


def _portable_feature_names(
    documents: Mapping[
        str,
        Mapping[
            str,
            Any,
        ],
    ],
) -> list[str]:

    return [
        feature
        for (
            feature,
            document,
        )
        in documents.items()
        if bool(
            document.get(
                "portable",
                False,
            )
        )
    ]


def _decision(
    *,
    spread_documents: Mapping[
        str,
        Mapping[
            str,
            Any,
        ],
    ],
    tick_documents: Mapping[
        str,
        Mapping[
            str,
            Any,
        ],
    ],
) -> dict[str, Any]:

    portable_spread = (
        _portable_feature_names(
            spread_documents
        )
    )

    portable_tick = (
        _portable_feature_names(
            tick_documents
        )
    )

    selected_spread = (
        _select_spread_candidate(
            spread_documents
        )
    )

    if (
        selected_spread
        is not None
    ):

        status = (
            "PORTABLE_SPREAD_CANDIDATE_IDENTIFIED"
        )

        reason = (
            "AT_LEAST_ONE_PREDECLARED_NORMALIZED_SPREAD_"
            "CANDIDATE_MEETS_TRAIN_ONLY_CROSS_BROKER_"
            "PORTABILITY_THRESHOLDS"
        )

        next_action = (
            "DESIGN_XAUUSD_PORTABLE_FEATURE_CONTRACT_"
            "WITH_331_UNCHANGED_FEATURES_AND_FROZEN_"
            "SPREAD_CANDIDATE_POLICY"
        )

    else:

        status = (
            "NO_PORTABLE_MODEL_SPREAD_CANDIDATE_IDENTIFIED"
        )

        reason = (
            "NONE_OF_THE_PREDECLARED_NORMALIZED_SPREAD_"
            "CANDIDATES_MEET_TRAIN_ONLY_CROSS_BROKER_"
            "PORTABILITY_THRESHOLDS"
        )

        next_action = (
            "DESIGN_XAUUSD_PORTABLE_FEATURE_CONTRACT_WITH_"
            "SPREAD_REMOVED_FROM_MODEL_INPUTS_AND_BROKER_COST_"
            "METRICS_RETAINED_ONLY_FOR_EXECUTION_OR_TRADE_READY_GATING"
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "portable_spread_candidates": (
            portable_spread
        ),
        "selected_spread_candidate_for_contract_design": (
            selected_spread
        ),
        "portable_tick_volume_candidates": (
            portable_tick
        ),
        "absolute_tick_volume_default_action": (
            "DROP_WITHOUT_REPLACEMENT_FOR_FIRST_PORTABLE_CONTRACT"
        ),
        "absolute_tick_volume_default_action_reason": (
            "M5_TICK_VOLUME_RATIO20_IS_ALREADY_RETAINED_AS_A_"
            "PORTABLE_RELATIVE_VOLUME_FEATURE_AND_THIS_GATE_"
            "DOES_NOT_USE_LABELS_TO_JUSTIFY_ADDITIONAL_REDUNDANT_FEATURES"
        ),
        "retained_existing_relative_volume_feature": (
            "m5_tick_volume_ratio20"
        ),
        "unchanged_portable_feature_base": (
            EXPECTED_RETAINED_BASE_FEATURE_COUNT
        ),
        "new_feature_contract_implementation_authorized": (
            False
        ),
        "model_retraining_authorized": (
            False
        ),
        "test_evaluation_authorized": (
            False
        ),
        "target_contract_change_authorized": (
            False
        ),
        "live_authorized": (
            False
        ),
        "next_action": (
            next_action
        ),
    }


def run_audit(
) -> dict[str, Any]:

    mapped._validate_mapping_contract()

    final_document = (
        _validate_final_prerequisite()
    )

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

    _technical_features(
        manifest
    )

    required_train_columns = [
        "m5_spread_points",
        "m5_tick_volume_log1p",
        "m5_tick_volume_ratio20",
        "m5_atr14",
    ]

    frozen_train = (
        base
        ._load_frozen_train_only(
            training_dataset_path,
            required_train_columns,
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
            f"{len(frozen_train)}:"
            f"{EXPECTED_TRAIN_ROWS}"
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

    m5_snapshot = (
        source
        ._snapshot_document(
            manifest,
            "M5",
        )
    )

    (
        frozen_m5_path,
        frozen_m5_resolution,
    ) = (
        source
        ._resolve_snapshot_file(
            m5_snapshot
        )
    )

    frozen_raw_m5 = (
        source
        ._read_snapshot_frame(
            frozen_m5_path,
            m5_snapshot,
        )
    )

    required_raw_columns = {
        "time",
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
        "spread",
    }

    frozen_missing = sorted(
        required_raw_columns
        -
        set(
            str(
                column
            )
            for column
            in frozen_raw_m5.columns
        )
    )

    _require(
        not frozen_missing,
        (
            "FROZEN_M5_REQUIRED_COLUMNS_MISSING:"
            f"{frozen_missing}"
        ),
    )

    frozen_raw_m5[
        "time"
    ] = (
        _canonical_time(
            frozen_raw_m5[
                "time"
            ]
        )
    )

    frozen_raw_m5 = (
        frozen_raw_m5
        .sort_values(
            "time"
        )
        .reset_index(
            drop=True
        )
    )

    (
        frozen_point,
        frozen_point_meta,
    ) = (
        _infer_quote_point(
            frozen_raw_m5
        )
    )

    (
        frozen_tick_size,
        frozen_tick_meta,
    ) = (
        _infer_tick_size(
            frozen_raw_m5,
            point=(
                frozen_point
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

    frozen_generated_atr = (
        _generate_m5_atr(
            builder=(
                builder
            ),
            raw_m5=(
                frozen_raw_m5
            ),
        )
    )

    frozen_candidate_frame = (
        _candidate_frame(
            raw_m5=(
                frozen_raw_m5
            ),
            generated_atr=(
                frozen_generated_atr
            ),
            point=(
                frozen_point
            ),
            tick_size=(
                frozen_tick_size
            ),
        )
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

        current_point = float(
            getattr(
                symbol_info,
                "point",
                0.0,
            )
        )

        current_tick_size = float(
            getattr(
                symbol_info,
                "trade_tick_size",
                0.0,
            )
        )

        _require(
            current_point
            >
            0.0,
            (
                "CURRENT_POINT_INVALID:"
                f"{current_point}"
            ),
        )

        _require(
            current_tick_size
            >
            0.0,
            (
                "CURRENT_TICK_SIZE_INVALID:"
                f"{current_tick_size}"
            ),
        )

        fetch_start = (
            train_start
            -
            pd.Timedelta(
                days=(
                    CURRENT_HISTORY_WARMUP_DAYS
                )
            )
        )

        fetch_end = (
            train_end
            +
            pd.Timedelta(
                days=1
            )
        )

        rates = mt5.copy_rates_range(
            broker_symbol,
            mt5.TIMEFRAME_M5,
            fetch_start.to_pydatetime(),
            fetch_end.to_pydatetime(),
        )

        raw_current_m5 = (
            base
            ._mt5_rates_frame(
                rates
            )
        )

        _require(
            not raw_current_m5.empty,
            "CURRENT_BROKER_M5_EMPTY",
        )

        raw_current_m5[
            "time"
        ] = (
            _canonical_time(
                raw_current_m5[
                    "time"
                ]
            )
        )

        (
            current_raw_m5,
            clock_meta,
        ) = (
            _clock_map_current_m5(
                raw_current_m5
            )
        )

        current_generated_atr = (
            _generate_m5_atr(
                builder=(
                    builder
                ),
                raw_m5=(
                    current_raw_m5
                ),
            )
        )

        current_candidate_frame = (
            _candidate_frame(
                raw_m5=(
                    current_raw_m5
                ),
                generated_atr=(
                    current_generated_atr
                ),
                point=(
                    current_point
                ),
                tick_size=(
                    current_tick_size
                ),
            )
        )

        train_grid = (
            frozen_train[
                [
                    "decision_time"
                ]
            ]
            .copy()
        )

        frozen_aligned = (
            _align_candidate_frame(
                train_grid=(
                    train_grid
                ),
                candidate_frame=(
                    frozen_candidate_frame
                ),
                suffix=(
                    "frozen"
                ),
            )
        )

        current_aligned = (
            _align_candidate_frame(
                train_grid=(
                    train_grid
                ),
                candidate_frame=(
                    current_candidate_frame
                ),
                suffix=(
                    "current"
                ),
            )
        )

        source_validation = (
            _validate_frozen_source_replay(
                frozen_train=(
                    frozen_train
                ),
                frozen_aligned=(
                    frozen_aligned
                ),
            )
        )

        spread_documents = (
            _candidate_documents(
                frozen_aligned=(
                    frozen_aligned
                ),
                current_aligned=(
                    current_aligned
                ),
                candidates=(
                    SPREAD_CANDIDATES
                ),
            )
        )

        tick_documents = (
            _candidate_documents(
                frozen_aligned=(
                    frozen_aligned
                ),
                current_aligned=(
                    current_aligned
                ),
                candidates=(
                    TICK_VOLUME_CANDIDATES
                ),
            )
        )

        existing_ratio20_cross_broker = (
            _comparison(
                feature=(
                    "m5_tick_volume_ratio20_existing"
                ),
                frozen=(
                    frozen_train[
                        "m5_tick_volume_ratio20"
                    ]
                ),
                current=(
                    current_aligned[
                        "tick_volume_ratio20_recomputed_current"
                    ]
                ),
            )
        )

        decision = (
            _decision(
                spread_documents=(
                    spread_documents
                ),
                tick_documents=(
                    tick_documents
                ),
            )
        )

        return {
            "valid": True,
            "reason": (
                "OK_XAUUSD_PORTABLE_BROKER_SENSITIVE_"
                "REPLACEMENT_AUDIT"
            ),
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "research_scope": (
                "TRAIN_ONLY_PORTABILITY_AUDIT_FOR_NORMALIZED_"
                "SPREAD_AND_RELATIVE_TICK_VOLUME_CANDIDATES"
            ),
            "prerequisite": {
                "final_adjudication_valid": (
                    True
                ),
                "final_classification": (
                    EXPECTED_FINAL_CLASSIFICATION
                ),
                "unchanged_portable_feature_base": (
                    EXPECTED_RETAINED_BASE_FEATURE_COUNT
                ),
                "m5_tick_volume_ratio20_policy": (
                    "KEEP_AS_IS"
                ),
                "m5_spread_points_policy": (
                    "REPLACE"
                ),
                "m5_tick_volume_log1p_policy": (
                    "REMOVE_OR_REPLACE"
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
                "m5_snapshot_hash_validated": (
                    True
                ),
                "m5_snapshot_resolution": (
                    frozen_m5_resolution
                ),
                "filesystem_path_emitted": (
                    False
                ),
            },
            "frozen_contract_inference": {
                "point": (
                    frozen_point_meta
                ),
                "tick_size": (
                    frozen_tick_meta
                ),
                "important_limitation": (
                    "FROZEN_POINT_AND_TICK_SIZE_ARE_INFERRED_FROM_"
                    "THE_IMMUTABLE_PRICE_LATTICE_UNLESS_ARCHIVED_"
                    "BROKER_CONTRACT_METADATA_IS_AVAILABLE"
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
                "point": (
                    current_point
                ),
                "tick_size": (
                    current_tick_size
                ),
                "raw_m5_rows": int(
                    len(
                        raw_current_m5
                    )
                ),
                "canonical_m5_rows": int(
                    len(
                        current_raw_m5
                    )
                ),
            },
            "confirmed_clock_mapping": (
                clock_meta
            ),
            "frozen_source_replay_validation": (
                source_validation
            ),
            "existing_relative_volume_sanity_check": {
                "feature": (
                    "m5_tick_volume_ratio20"
                ),
                "comparison_against_recomputed_current_ratio20": (
                    existing_ratio20_cross_broker
                ),
            },
            "spread_candidates": (
                spread_documents
            ),
            "tick_volume_candidates": (
                tick_documents
            ),
            "thresholds": {
                "minimum_finite_pair_fraction": (
                    MINIMUM_FINITE_PAIR_FRACTION
                ),
                "minimum_paired_correlation": (
                    MINIMUM_PAIRED_CORRELATION
                ),
                "psi_material": (
                    PSI_MATERIAL
                ),
                "standardized_mean_shift_material": (
                    STANDARDIZED_MEAN_SHIFT_MATERIAL
                ),
                "source_validation_minimum_correlation": (
                    SOURCE_VALIDATION_MINIMUM_CORRELATION
                ),
                "source_validation_maximum_standardized_shift": (
                    SOURCE_VALIDATION_MAXIMUM_STANDARDIZED_SHIFT
                ),
            },
            "decision": (
                decision
            ),
            "candidate_semantics": {
                "spread_ticks": (
                    "SPREAD_PRICE_DIVIDED_BY_TICK_SIZE"
                ),
                "spread_atr": (
                    "SPREAD_PRICE_DIVIDED_BY_M5_ATR14"
                ),
                "spread_bps": (
                    "SPREAD_PRICE_DIVIDED_BY_CLOSE_TIMES_10000"
                ),
                "spread_ratio20": (
                    "RAW_SPREAD_POINTS_DIVIDED_BY_CAUSAL_"
                    "ROLLING_MEDIAN_20"
                ),
                "spread_ratio100": (
                    "RAW_SPREAD_POINTS_DIVIDED_BY_CAUSAL_"
                    "ROLLING_MEDIAN_100"
                ),
                "tick_volume_ratio100": (
                    "TICK_VOLUME_DIVIDED_BY_CAUSAL_ROLLING_MEAN_100"
                ),
                "tick_volume_ratio288": (
                    "TICK_VOLUME_DIVIDED_BY_CAUSAL_ROLLING_MEAN_288"
                ),
                "tick_volume_zscore100": (
                    "CAUSAL_ZSCORE_OF_LOG1P_TICK_VOLUME_OVER_100_BARS"
                ),
                "tick_volume_zscore288": (
                    "CAUSAL_ZSCORE_OF_LOG1P_TICK_VOLUME_OVER_288_BARS"
                ),
            },
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
                "candidate_features_written_to_training_contract": (
                    False
                ),
                "feature_pipeline_modified": (
                    False
                ),
                "frozen_v3_contract_mutated": (
                    False
                ),
                "target_contract_changed": (
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
                "model_retraining_authorized": (
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
                "if_portable_spread_candidate_identified": (
                    "DESIGN_NEW_PORTABLE_XAUUSD_FEATURE_CONTRACT_"
                    "WITHOUT_MUTATING_FROZEN_V3"
                ),
                "if_no_portable_spread_candidate": (
                    "REMOVE_SPREAD_FROM_MODEL_FEATURES_AND_KEEP_"
                    "BROKER_NORMALIZED_COST_METRICS_IN_EXECUTION_GATING"
                ),
                "absolute_tick_volume_default": (
                    "DROP_WITHOUT_REPLACEMENT_UNLESS_LATER_MODEL_"
                    "EVIDENCE_JUSTIFIES_A_SECOND_RELATIVE_VOLUME_FEATURE"
                ),
                "existing_m5_tick_volume_ratio20_retained": (
                    True
                ),
                "target_contract_change_required": (
                    False
                ),
                "target_contract_change_authorized": (
                    False
                ),
                "model_retraining_authorized": (
                    False
                ),
                "test_holdout_remains_untouched": (
                    True
                ),
                "live_authorization_not_changed": (
                    True
                ),
            },
        }

    finally:

        mt5.shutdown()


def main() -> int:

    try:

        result = (
            run_audit()
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
                        "XAUUSD_PORTABLE_BROKER_SENSITIVE_"
                        "REPLACEMENT_AUDIT_FAILED"
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