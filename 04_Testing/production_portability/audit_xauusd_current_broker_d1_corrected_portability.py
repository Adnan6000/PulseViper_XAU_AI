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
    "XAUUSD_CURRENT_BROKER_D1_CORRECTED_PORTABILITY_V1"
)

FULL_AUDIT_MODULE = (
    "04_Testing."
    "analyze_xauusd_current_broker_full_mtf_portability"
)

FULL_STATE_RECOVERY_MODULE = (
    "04_Testing."
    "diagnose_xauusd_current_broker_d1_full_state_recovery"
)


full: Any = importlib.import_module(
    FULL_AUDIT_MODULE
)

recovery: Any = importlib.import_module(
    FULL_STATE_RECOVERY_MODULE
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


H1_REQUEST_START = pd.Timestamp(
    "2010-01-01T00:00:00Z"
)


CORRECTED_MINIMUM_H1_BARS = 1

EXPECTED_D1_STATE_COUNT = 309

EXPECTED_TRAIN_ROWS = 69966


CORRELATION_STRONG = 0.98

CORRELATION_WARNING = 0.95

MINIMUM_GROUP_MEDIAN_CORRELATION = 0.80

MINIMUM_FEATURE_FINITE_PAIR_FRACTION = 0.90

MAXIMUM_GROUP_MATERIAL_SHIFT_SHARE = 0.20

PSI_WARNING = 0.10

PSI_MATERIAL = 0.25

STANDARDIZED_MEAN_SHIFT_MATERIAL = 0.50


PSI_BIN_COUNT = 10

PSI_EPSILON = 1e-6

MINIMUM_PSI_UNIQUE_REFERENCE_VALUES = 10


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

    return (
        result
    )


def _finite_array(
    values: Any,
) -> np.ndarray:

    numeric = np.asarray(
        pd.to_numeric(
            values,
            errors="coerce",
        ),
        dtype=np.float64,
    )

    return (
        numeric[
            np.isfinite(
                numeric
            )
        ]
    )


def _distribution_summary(
    values: Any,
) -> dict[str, Any]:

    finite = (
        _finite_array(
            values
        )
    )

    if (
        finite.size
        ==
        0
    ):

        return {
            "rows": 0,
            "mean": None,
            "median": None,
            "std": None,
            "p05": None,
            "p25": None,
            "p75": None,
            "p95": None,
        }

    return {
        "rows": int(
            finite.size
        ),
        "mean": float(
            np.mean(
                finite
            )
        ),
        "median": float(
            np.median(
                finite
            )
        ),
        "std": float(
            np.std(
                finite
            )
        ),
        "p05": float(
            np.quantile(
                finite,
                0.05,
            )
        ),
        "p25": float(
            np.quantile(
                finite,
                0.25,
            )
        ),
        "p75": float(
            np.quantile(
                finite,
                0.75,
            )
        ),
        "p95": float(
            np.quantile(
                finite,
                0.95,
            )
        ),
    }


def _paired_arrays(
    reference: Any,
    current: Any,
) -> tuple[
    np.ndarray,
    np.ndarray,
    int,
    int,
]:

    reference_values = np.asarray(
        pd.to_numeric(
            reference,
            errors="coerce",
        ),
        dtype=np.float64,
    )

    current_values = np.asarray(
        pd.to_numeric(
            current,
            errors="coerce",
        ),
        dtype=np.float64,
    )

    _require(
        reference_values.shape
        ==
        current_values.shape,
        (
            "PAIRED_ARRAY_SHAPE_MISMATCH:"
            f"{reference_values.shape}:"
            f"{current_values.shape}"
        ),
    )

    finite = (
        np.isfinite(
            reference_values
        )
        &
        np.isfinite(
            current_values
        )
    )

    paired_rows = int(
        finite.sum()
    )

    total_rows = int(
        reference_values.size
    )

    return (
        reference_values[
            finite
        ],
        current_values[
            finite
        ],
        paired_rows,
        total_rows,
    )


def _paired_correlation(
    reference: Any,
    current: Any,
) -> float | None:

    (
        reference_values,
        current_values,
        paired_rows,
        _,
    ) = (
        _paired_arrays(
            reference,
            current,
        )
    )

    if (
        paired_rows
        <
        3
    ):

        return None

    reference_std = float(
        np.std(
            reference_values
        )
    )

    current_std = float(
        np.std(
            current_values
        )
    )

    if (
        reference_std
        <=
        1e-15
        or
        current_std
        <=
        1e-15
    ):

        return None

    value = float(
        np.corrcoef(
            reference_values,
            current_values,
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


def _population_stability_index(
    reference: Any,
    current: Any,
) -> float | None:

    reference_values = (
        _finite_array(
            reference
        )
    )

    current_values = (
        _finite_array(
            current
        )
    )

    if (
        reference_values.size
        <
        20
        or
        current_values.size
        <
        20
    ):

        return None

    unique_reference = np.unique(
        reference_values
    )

    if (
        unique_reference.size
        <
        MINIMUM_PSI_UNIQUE_REFERENCE_VALUES
    ):

        return None

    quantiles = np.linspace(
        0.0,
        1.0,
        PSI_BIN_COUNT
        +
        1,
    )

    edges = np.quantile(
        reference_values,
        quantiles,
    )

    edges = np.unique(
        edges
    )

    if (
        edges.size
        <
        3
    ):

        return None

    edges = edges.astype(
        np.float64
    )

    edges[
        0
    ] = (
        -np.inf
    )

    edges[
        -1
    ] = (
        np.inf
    )

    reference_counts, _ = np.histogram(
        reference_values,
        bins=edges,
    )

    current_counts, _ = np.histogram(
        current_values,
        bins=edges,
    )

    reference_share = (
        reference_counts.astype(
            np.float64
        )
        /
        float(
            reference_values.size
        )
    )

    current_share = (
        current_counts.astype(
            np.float64
        )
        /
        float(
            current_values.size
        )
    )

    reference_share = np.maximum(
        reference_share,
        PSI_EPSILON,
    )

    current_share = np.maximum(
        current_share,
        PSI_EPSILON,
    )

    psi = float(
        np.sum(
            (
                current_share
                -
                reference_share
            )
            *
            np.log(
                current_share
                /
                reference_share
            )
        )
    )

    if not math.isfinite(
        psi
    ):

        return None

    return (
        psi
    )


def _feature_comparison(
    *,
    feature: str,
    reference: pd.Series,
    current: pd.Series,
    category: str,
) -> dict[str, Any]:

    (
        reference_pair,
        current_pair,
        paired_rows,
        total_rows,
    ) = (
        _paired_arrays(
            reference,
            current,
        )
    )

    finite_pair_fraction = (
        float(
            paired_rows
            /
            total_rows
        )
        if (
            total_rows
            >
            0
        )
        else 0.0
    )

    correlation = (
        _paired_correlation(
            reference,
            current,
        )
    )

    reference_summary = (
        _distribution_summary(
            reference
        )
    )

    current_summary = (
        _distribution_summary(
            current
        )
    )

    reference_std = (
        _safe_float(
            reference_summary[
                "std"
            ]
        )
    )

    reference_mean = (
        _safe_float(
            reference_summary[
                "mean"
            ]
        )
    )

    current_mean = (
        _safe_float(
            current_summary[
                "mean"
            ]
        )
    )

    reference_median = (
        _safe_float(
            reference_summary[
                "median"
            ]
        )
    )

    current_median = (
        _safe_float(
            current_summary[
                "median"
            ]
        )
    )

    standardized_mean_shift: (
        float
        |
        None
    ) = None

    median_shift_reference_std: (
        float
        |
        None
    ) = None

    paired_median_abs_diff_reference_std: (
        float
        |
        None
    ) = None

    if (
        reference_std
        is not None
        and
        reference_std
        >
        1e-15
    ):

        if (
            reference_mean
            is not None
            and
            current_mean
            is not None
        ):

            standardized_mean_shift = float(
                abs(
                    current_mean
                    -
                    reference_mean
                )
                /
                reference_std
            )

        if (
            reference_median
            is not None
            and
            current_median
            is not None
        ):

            median_shift_reference_std = float(
                abs(
                    current_median
                    -
                    reference_median
                )
                /
                reference_std
            )

        if (
            paired_rows
            >
            0
        ):

            paired_median_abs_diff_reference_std = float(
                np.median(
                    np.abs(
                        current_pair
                        -
                        reference_pair
                    )
                )
                /
                reference_std
            )

    else:

        if (
            reference_median
            is not None
            and
            current_median
            is not None
            and
            abs(
                current_median
                -
                reference_median
            )
            <=
            1e-15
        ):

            median_shift_reference_std = 0.0

        if (
            paired_rows
            >
            0
            and
            bool(
                np.allclose(
                    current_pair,
                    reference_pair,
                    rtol=0.0,
                    atol=1e-12,
                    equal_nan=False,
                )
            )
        ):

            paired_median_abs_diff_reference_std = 0.0

    psi = (
        _population_stability_index(
            reference,
            current,
        )
    )

    psi_warning = bool(
        psi is not None
        and
        psi
        >=
        PSI_WARNING
    )

    psi_material = bool(
        psi is not None
        and
        psi
        >=
        PSI_MATERIAL
    )

    standardized_mean_shift_material = bool(
        standardized_mean_shift
        is not None
        and
        standardized_mean_shift
        >=
        STANDARDIZED_MEAN_SHIFT_MATERIAL
    )

    material_distribution_shift = bool(
        psi_material
        or
        standardized_mean_shift_material
    )

    correlation_warning = bool(
        correlation
        is not None
        and
        correlation
        <
        CORRELATION_WARNING
    )

    strong_correlation = bool(
        correlation
        is not None
        and
        correlation
        >=
        CORRELATION_STRONG
    )

    low_coverage = bool(
        finite_pair_fraction
        <
        MINIMUM_FEATURE_FINITE_PAIR_FRACTION
    )

    return {
        "feature": (
            feature
        ),
        "category": (
            category
        ),
        "frozen_train": (
            reference_summary
        ),
        "current_broker": (
            current_summary
        ),
        "paired_rows": (
            paired_rows
        ),
        "finite_pair_rows": (
            paired_rows
        ),
        "finite_pair_fraction": (
            finite_pair_fraction
        ),
        "paired_correlation": (
            correlation
        ),
        "correlation_warning": (
            correlation_warning
        ),
        "strong_correlation": (
            strong_correlation
        ),
        "psi": (
            psi
        ),
        "psi_warning": (
            psi_warning
        ),
        "psi_material": (
            psi_material
        ),
        "standardized_mean_shift": (
            standardized_mean_shift
        ),
        "standardized_mean_shift_material": (
            standardized_mean_shift_material
        ),
        "median_shift_reference_std": (
            median_shift_reference_std
        ),
        "paired_median_abs_diff_reference_std": (
            paired_median_abs_diff_reference_std
        ),
        "material_distribution_shift": (
            material_distribution_shift
        ),
        "low_coverage": (
            low_coverage
        ),
    }


def _median_metric(
    comparisons: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
    field: str,
) -> float | None:

    values: list[
        float
    ] = []

    for document in (
        comparisons
    ):

        value = (
            _safe_float(
                document.get(
                    field
                )
            )
        )

        if (
            value
            is not None
        ):

            values.append(
                value
            )

    if not values:
        return None

    return float(
        np.median(
            np.asarray(
                values,
                dtype=np.float64,
            )
        )
    )


def _max_abs_metric(
    comparisons: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
    field: str,
) -> float | None:

    values: list[
        float
    ] = []

    for document in (
        comparisons
    ):

        value = (
            _safe_float(
                document.get(
                    field
                )
            )
        )

        if (
            value
            is not None
        ):

            values.append(
                abs(
                    value
                )
            )

    if not values:
        return None

    return float(
        max(
            values
        )
    )


def _group_summary(
    *,
    comparisons: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
    group: str,
) -> dict[str, Any]:

    correlation_documents = [
        document
        for document
        in comparisons
        if (
            _safe_float(
                document.get(
                    "paired_correlation"
                )
            )
            is not None
        )
    ]

    correlation_warning_features = [
        str(
            document[
                "feature"
            ]
        )
        for document
        in comparisons
        if bool(
            document.get(
                "correlation_warning",
                False,
            )
        )
    ]

    strong_correlation_features = [
        str(
            document[
                "feature"
            ]
        )
        for document
        in comparisons
        if bool(
            document.get(
                "strong_correlation",
                False,
            )
        )
    ]

    low_coverage_features = [
        str(
            document[
                "feature"
            ]
        )
        for document
        in comparisons
        if bool(
            document.get(
                "low_coverage",
                False,
            )
        )
    ]

    material_shift_features = [
        str(
            document[
                "feature"
            ]
        )
        for document
        in comparisons
        if bool(
            document.get(
                "material_distribution_shift",
                False,
            )
        )
    ]

    psi_material_features = [
        str(
            document[
                "feature"
            ]
        )
        for document
        in comparisons
        if bool(
            document.get(
                "psi_material",
                False,
            )
        )
    ]

    mean_shift_material_features = [
        str(
            document[
                "feature"
            ]
        )
        for document
        in comparisons
        if bool(
            document.get(
                "standardized_mean_shift_material",
                False,
            )
        )
    ]

    feature_count = int(
        len(
            comparisons
        )
    )

    features_with_correlation = int(
        len(
            correlation_documents
        )
    )

    material_share = (
        float(
            len(
                material_shift_features
            )
            /
            feature_count
        )
        if (
            feature_count
            >
            0
        )
        else 1.0
    )

    strong_share = (
        float(
            len(
                strong_correlation_features
            )
            /
            features_with_correlation
        )
        if (
            features_with_correlation
            >
            0
        )
        else 0.0
    )

    return {
        "group": (
            group
        ),
        "feature_count": (
            feature_count
        ),
        "features_with_correlation": (
            features_with_correlation
        ),
        "median_paired_correlation": (
            _median_metric(
                comparisons,
                "paired_correlation",
            )
        ),
        "median_finite_pair_fraction": (
            _median_metric(
                comparisons,
                "finite_pair_fraction",
            )
        ),
        "minimum_finite_pair_fraction": (
            min(
                (
                    _safe_float(
                        document.get(
                            "finite_pair_fraction"
                        )
                    )
                    or
                    0.0
                )
                for document
                in comparisons
            )
            if comparisons
            else None
        ),
        "median_psi": (
            _median_metric(
                comparisons,
                "psi",
            )
        ),
        "median_abs_standardized_mean_shift": (
            _median_metric(
                [
                    {
                        "value": (
                            abs(
                                value
                            )
                            if (
                                value
                                is not None
                            )
                            else None
                        )
                    }
                    for value
                    in [
                        _safe_float(
                            document.get(
                                "standardized_mean_shift"
                            )
                        )
                        for document
                        in comparisons
                    ]
                ],
                "value",
            )
        ),
        "max_abs_standardized_mean_shift": (
            _max_abs_metric(
                comparisons,
                "standardized_mean_shift",
            )
        ),
        "correlation_warning_feature_count": int(
            len(
                correlation_warning_features
            )
        ),
        "correlation_warning_features": (
            correlation_warning_features
        ),
        "strong_correlation_feature_count": int(
            len(
                strong_correlation_features
            )
        ),
        "strong_correlation_features": (
            strong_correlation_features
        ),
        "strong_correlation_share_of_correlated": (
            strong_share
        ),
        "low_coverage_feature_count": int(
            len(
                low_coverage_features
            )
        ),
        "low_coverage_features": (
            low_coverage_features
        ),
        "material_distribution_shift_feature_count": int(
            len(
                material_shift_features
            )
        ),
        "material_distribution_shift_features": (
            material_shift_features
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
    }


def _group_status(
    summary: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    median_correlation = (
        _safe_float(
            summary.get(
                "median_paired_correlation"
            )
        )
    )

    minimum_coverage = (
        _safe_float(
            summary.get(
                "minimum_finite_pair_fraction"
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

    if (
        median_correlation
        is None
        or
        median_correlation
        <
        MINIMUM_GROUP_MEDIAN_CORRELATION
    ):

        return {
            "portable": False,
            "status": (
                "PORTABILITY_NOT_CONFIRMED"
            ),
            "reason": (
                "GROUP_MEDIAN_SAME_DECISION_TIME_"
                "CORRELATION_BELOW_THRESHOLD"
            ),
        }

    if (
        minimum_coverage
        is None
        or
        minimum_coverage
        <
        MINIMUM_FEATURE_FINITE_PAIR_FRACTION
    ):

        return {
            "portable": False,
            "status": (
                "PORTABILITY_NOT_CONFIRMED"
            ),
            "reason": (
                "ONE_OR_MORE_FEATURES_HAVE_"
                "INSUFFICIENT_FINITE_PAIR_COVERAGE"
            ),
        }

    if (
        material_share
        is None
        or
        material_share
        >
        MAXIMUM_GROUP_MATERIAL_SHIFT_SHARE
    ):

        return {
            "portable": False,
            "status": (
                "PORTABILITY_NOT_CONFIRMED"
            ),
            "reason": (
                "GROUP_MATERIAL_DISTRIBUTION_"
                "SHIFT_SHARE_ABOVE_THRESHOLD"
            ),
        }

    return {
        "portable": True,
        "status": (
            "TRAIN_ONLY_PRELIMINARY_PORTABLE"
        ),
        "reason": (
            "GROUP_MEETS_PREDECLARED_CORRELATION_"
            "DISTRIBUTION_AND_COVERAGE_THRESHOLDS"
        ),
    }


def _align_to_train(
    *,
    frozen_train: pd.DataFrame,
    generated: pd.DataFrame,
    technical_features: Sequence[
        str
    ],
) -> pd.DataFrame:

    left = (
        frozen_train[
            [
                "decision_time",
                "d1_age_minutes",
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
        generated[
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
        ==
        EXPECTED_TRAIN_ROWS,
        (
            "CORRECTED_D1_TRAIN_ALIGNMENT_ROW_MISMATCH:"
            f"{matched_rows}:"
            f"{EXPECTED_TRAIN_ROWS}"
        ),
    )

    aligned[
        "d1_age_minutes_current"
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
    )

    negative_age_rows = int(
        (
            aligned[
                "d1_age_minutes_current"
            ]
            <
            0.0
        )
        .sum()
    )

    _require(
        negative_age_rows
        ==
        0,
        (
            "CORRECTED_D1_NEGATIVE_AGE_ROWS:"
            f"{negative_age_rows}"
        ),
    )

    return (
        aligned
    )


def _decision(
    *,
    technical_status: Mapping[
        str,
        Any,
    ],
    age_status: Mapping[
        str,
        Any,
    ],
    generated_state_count: int,
    aligned_rows: int,
) -> dict[str, Any]:

    technical_portable = bool(
        technical_status.get(
            "portable",
            False,
        )
    )

    age_portable = bool(
        age_status.get(
            "portable",
            False,
        )
    )

    if (
        generated_state_count
        <
        EXPECTED_D1_STATE_COUNT
    ):

        status = (
            "D1_CORRECTED_PORTABILITY_STATE_COVERAGE_FAILED"
        )

        reason = (
            "CORRECTED_GE1_RECONSTRUCTION_DOES_NOT_"
            "PROVIDE_THE_CONFIRMED_309_STATE_SEQUENCE"
        )

        next_action = (
            "RESOLVE_D1_STATE_SEQUENCE_BEFORE_FULL_MTF_ADJUDICATION"
        )

    elif (
        aligned_rows
        !=
        EXPECTED_TRAIN_ROWS
    ):

        status = (
            "D1_CORRECTED_PORTABILITY_DECISION_ROW_ALIGNMENT_FAILED"
        )

        reason = (
            "CORRECTED_D1_FEATURE_STATES_DO_NOT_"
            "ALIGN_TO_ALL_FROZEN_TRAIN_DECISION_ROWS"
        )

        next_action = (
            "RESOLVE_D1_ASOF_ALIGNMENT_BEFORE_FULL_MTF_ADJUDICATION"
        )

    elif (
        technical_portable
        and
        age_portable
    ):

        status = (
            "D1_CORRECTED_TRAIN_ROW_PORTABILITY_CONFIRMED"
        )

        reason = (
            "CORRECTED_00UTC_GE1_D1_RECONSTRUCTION_MEETS_"
            "ORIGINAL_FULL_MTF_CORRELATION_DISTRIBUTION_"
            "AND_COVERAGE_THRESHOLDS_ON_ALL_TRAIN_ROWS"
        )

        next_action = (
            "RUN_FINAL_FULL_333_EVIDENCE_ADJUDICATION_WITH_"
            "CORRECTED_D1_AND_DETERMINISTIC_UTC_POLICY"
        )

    elif (
        not technical_portable
    ):

        status = (
            "D1_CORRECTED_TECHNICAL_PORTABILITY_NOT_CONFIRMED"
        )

        reason = (
            "CORRECTED_D1_TECHNICAL_GROUP_STILL_FAILS_"
            "ONE_OR_MORE_ORIGINAL_FULL_MTF_THRESHOLDS"
        )

        next_action = (
            "ISOLATE_ONLY_REMAINING_D1_TECHNICAL_"
            "DISTRIBUTION_OR_COVERAGE_FAILURES"
        )

    else:

        status = (
            "D1_CORRECTED_AGE_PORTABILITY_NOT_CONFIRMED"
        )

        reason = (
            "CORRECTED_D1_TECHNICAL_GROUP_PASSES_BUT_"
            "D1_AGE_METADATA_REMAINS_NONPORTABLE"
        )

        next_action = (
            "ISOLATE_D1_AGE_SEMANTICS_BEFORE_FULL_MTF_ADJUDICATION"
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "technical_portable": (
            technical_portable
        ),
        "d1_age_portable": (
            age_portable
        ),
        "generated_state_count": (
            generated_state_count
        ),
        "aligned_train_rows": (
            aligned_rows
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
        recovery
        ._technical_features(
            manifest
        )
    )

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
            recovery
            ._clock_map_current_h1(
                raw_h1
            )
        )

        (
            corrected_raw_d1,
            aggregation_meta,
        ) = (
            recovery
            ._build_synthetic_d1(
                canonical_h1,
                minimum_h1_bars=(
                    CORRECTED_MINIMUM_H1_BARS
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
            generated,
            generation_meta,
        ) = (
            recovery
            ._generate_d1_features(
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

        aligned = (
            _align_to_train(
                frozen_train=(
                    frozen_train
                ),
                generated=(
                    generated
                ),
                technical_features=(
                    technical_features
                ),
            )
        )

        technical_comparisons: list[
            dict[str, Any]
        ] = []

        for feature in (
            technical_features
        ):

            comparison = (
                _feature_comparison(
                    feature=(
                        feature
                    ),
                    reference=(
                        aligned[
                            (
                                feature
                                +
                                "_frozen"
                            )
                        ]
                    ),
                    current=(
                        aligned[
                            (
                                feature
                                +
                                "_current"
                            )
                        ]
                    ),
                    category=(
                        "PRICE_CANDLE"
                    ),
                )
            )

            technical_comparisons.append(
                comparison
            )

        d1_age_comparison = (
            _feature_comparison(
                feature=(
                    "d1_age_minutes"
                ),
                reference=(
                    aligned[
                        "d1_age_minutes"
                    ]
                ),
                current=(
                    aligned[
                        "d1_age_minutes_current"
                    ]
                ),
                category=(
                    "HTF_AGE"
                ),
            )
        )

        technical_summary = (
            _group_summary(
                comparisons=(
                    technical_comparisons
                ),
                group=(
                    "TECHNICAL_D1_CORRECTED"
                ),
            )
        )

        age_summary = (
            _group_summary(
                comparisons=[
                    d1_age_comparison
                ],
                group=(
                    "D1_AGE_CORRECTED"
                ),
            )
        )

        technical_status = (
            _group_status(
                technical_summary
            )
        )

        age_status = (
            _group_status(
                age_summary
            )
        )

        unique_train_state_count = int(
            aligned[
                "available_time"
            ]
            .nunique(
                dropna=True
            )
        )

        _require(
            unique_train_state_count
            ==
            EXPECTED_D1_STATE_COUNT,
            (
                "CORRECTED_D1_UNIQUE_TRAIN_STATE_COUNT_MISMATCH:"
                f"{unique_train_state_count}:"
                f"{EXPECTED_D1_STATE_COUNT}"
            ),
        )

        decision = (
            _decision(
                technical_status=(
                    technical_status
                ),
                age_status=(
                    age_status
                ),
                generated_state_count=(
                    unique_train_state_count
                ),
                aligned_rows=(
                    len(
                        aligned
                    )
                ),
            )
        )

        return {
            "valid": True,
            "reason": (
                "OK_XAUUSD_CURRENT_BROKER_D1_"
                "CORRECTED_PORTABILITY_AUDIT"
            ),
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "research_scope": (
                "CORRECTED_00UTC_GE1_D1_TECHNICAL_AND_AGE_"
                "PORTABILITY_ON_ALL_FROZEN_TRAIN_DECISION_ROWS"
            ),
            "prerequisite_contract": {
                "d1_full_state_recovery_status": (
                    "D1_FULL_309_STATE_FEATURE_ALIGNMENT_CONFIRMED"
                ),
                "confirmed_session_boundary_utc": (
                    "00:00"
                ),
                "confirmed_minimum_h1_bars": (
                    CORRECTED_MINIMUM_H1_BARS
                ),
                "confirmed_d1_state_count": (
                    EXPECTED_D1_STATE_COUNT
                ),
                "confirmed_d1_availability_lag_minutes": (
                    1440
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
                "train_start": (
                    train_start.isoformat()
                ),
                "train_end": (
                    train_end.isoformat()
                ),
                "technical_feature_count": int(
                    len(
                        technical_features
                    )
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
            },
            "confirmed_clock_mapping": (
                clock_meta
            ),
            "corrected_d1_aggregation": (
                aggregation_meta
            ),
            "corrected_d1_feature_generation": (
                generation_meta
            ),
            "alignment": {
                "train_rows": int(
                    len(
                        aligned
                    )
                ),
                "matched_train_rows": int(
                    aligned[
                        "available_time"
                    ]
                    .notna()
                    .sum()
                ),
                "unique_d1_states_on_train_grid": (
                    unique_train_state_count
                ),
                "negative_d1_age_rows": int(
                    (
                        aligned[
                            "d1_age_minutes_current"
                        ]
                        <
                        0.0
                    )
                    .sum()
                ),
            },
            "technical_d1": {
                "status": (
                    technical_status
                ),
                "summary": (
                    technical_summary
                ),
                "feature_comparisons": (
                    technical_comparisons
                ),
            },
            "d1_age": {
                "status": (
                    age_status
                ),
                "summary": (
                    age_summary
                ),
                "feature_comparison": (
                    d1_age_comparison
                ),
            },
            "thresholds": {
                "correlation_strong": (
                    CORRELATION_STRONG
                ),
                "correlation_warning": (
                    CORRELATION_WARNING
                ),
                "minimum_group_median_correlation": (
                    MINIMUM_GROUP_MEDIAN_CORRELATION
                ),
                "minimum_feature_finite_pair_fraction": (
                    MINIMUM_FEATURE_FINITE_PAIR_FRACTION
                ),
                "maximum_group_material_shift_share": (
                    MAXIMUM_GROUP_MATERIAL_SHIFT_SHARE
                ),
                "psi_warning": (
                    PSI_WARNING
                ),
                "psi_material": (
                    PSI_MATERIAL
                ),
                "standardized_mean_shift_material": (
                    STANDARDIZED_MEAN_SHIFT_MATERIAL
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
                "native_current_broker_d1_used": (
                    False
                ),
                "current_broker_h1_used": (
                    True
                ),
                "current_d1_reconstructed_from_h1": (
                    True
                ),
                "corrected_minimum_h1_bars": (
                    CORRECTED_MINIMUM_H1_BARS
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
                "if_corrected_d1_confirmed": (
                    "RUN_FINAL_FULL_333_EVIDENCE_ADJUDICATION_"
                    "WITH_CORRECTED_D1_AND_DETERMINISTIC_UTC_POLICY"
                ),
                "if_corrected_technical_fails": (
                    "ISOLATE_ONLY_REMAINING_D1_TECHNICAL_"
                    "DISTRIBUTION_OR_COVERAGE_FAILURES"
                ),
                "if_corrected_age_fails": (
                    "ISOLATE_D1_AGE_SEMANTICS"
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
                        "CORRECTED_PORTABILITY_AUDIT_FAILED"
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