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
    "XAUUSD_CURRENT_BROKER_D1_AVAILABILITY_ALIGNMENT_V1"
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


D1_MINUTES = 1440

D1_SECONDS = (
    D1_MINUTES
    *
    60
)

MIN_OVERLAP_ROWS = 5000


DELTA_HOURS = tuple(
    range(
        -6,
        7,
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


CONFIRMED_ANCHOR_MEDIAN_CORRELATION = 0.90

CONFIRMED_ALL_MEDIAN_CORRELATION = 0.90

LIKELY_ANCHOR_MEDIAN_CORRELATION = 0.80

MIN_IMPROVEMENT_VS_CURRENT = 0.10


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

    result = pd.to_datetime(
        values,
        utc=True,
        errors="raise",
    ).astype(
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


def _feature_comparison(
    frozen_train: pd.DataFrame,
    current_aligned: pd.DataFrame,
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
                    current_aligned[
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


def _build_available_time(
    source_time: pd.Series,
    *,
    policy_family: str,
    delta_hours: int,
) -> pd.Series:

    source_time = (
        _canonical_time(
            source_time
        )
    )

    delta = pd.to_timedelta(
        delta_hours,
        unit="h",
    )

    if (
        policy_family
        ==
        "SEASONAL_CLOCK_PLUS_D1_CLOSE"
    ):

        offsets = pd.Series(
            [
                mapped
                ._research_clock_offset_seconds(
                    pd.Timestamp(
                        value
                    )
                )
                for value
                in source_time
            ],
            index=source_time.index,
            dtype="int64",
        )

        available_time = (
            source_time
            +
            pd.to_timedelta(
                offsets,
                unit="s",
            )
            +
            pd.to_timedelta(
                D1_SECONDS,
                unit="s",
            )
            +
            delta
        )

    elif (
        policy_family
        ==
        "RAW_SOURCE_D1_CLOSE"
    ):

        available_time = (
            source_time
            +
            pd.to_timedelta(
                D1_SECONDS,
                unit="s",
            )
            +
            delta
        )

    else:

        raise RuntimeError(
            (
                "UNKNOWN_D1_AVAILABILITY_POLICY:"
                f"{policy_family}"
            )
        )

    return (
        _canonical_time(
            available_time
        )
    )


def _align_candidate(
    *,
    frozen_train: pd.DataFrame,
    generated_d1: pd.DataFrame,
    technical_features: Sequence[
        str
    ],
    policy_family: str,
    delta_hours: int,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

    right = (
        generated_d1[
            [
                "time",
                *technical_features,
            ]
        ]
        .copy()
    )

    right[
        "available_time"
    ] = (
        _build_available_time(
            right[
                "time"
            ],
            policy_family=(
                policy_family
            ),
            delta_hours=(
                delta_hours
            ),
        )
    )

    right = (
        right.drop(
            columns=[
                "time"
            ]
        )
        .sort_values(
            "available_time"
        )
        .reset_index(
            drop=True
        )
    )

    duplicate_available_rows = int(
        right[
            "available_time"
        ]
        .duplicated(
            keep=False
        )
        .sum()
    )

    _require(
        duplicate_available_rows
        ==
        0,
        (
            "D1_AVAILABLE_TIME_DUPLICATES:"
            f"{policy_family}:"
            f"{delta_hours}:"
            f"{duplicate_available_rows}"
        ),
    )

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
            f"{policy_family}:"
            f"{delta_hours}:"
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
            "D1_NEGATIVE_AGE:"
            f"{policy_family}:"
            f"{delta_hours}:"
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

    return (
        aligned,
        {
            "policy_family": (
                policy_family
            ),
            "delta_hours": int(
                delta_hours
            ),
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
            "duplicate_available_time_rows": (
                duplicate_available_rows
            ),
            "decision_time_dtype": (
                str(
                    aligned[
                        "decision_time"
                    ].dtype
                )
            ),
            "available_time_dtype": (
                str(
                    aligned[
                        "available_time"
                    ].dtype
                )
            ),
        },
    )


def _candidate_document(
    *,
    frozen_train: pd.DataFrame,
    generated_d1: pd.DataFrame,
    technical_features: Sequence[
        str
    ],
    policy_family: str,
    delta_hours: int,
) -> dict[str, Any]:

    (
        aligned,
        alignment_meta,
    ) = (
        _align_candidate(
            frozen_train=(
                frozen_train
            ),
            generated_d1=(
                generated_d1
            ),
            technical_features=(
                technical_features
            ),
            policy_family=(
                policy_family
            ),
            delta_hours=(
                delta_hours
            ),
        )
    )

    matched_rows = int(
        alignment_meta[
            "matched_rows"
        ]
    )

    _require(
        matched_rows
        >=
        MIN_OVERLAP_ROWS,
        (
            "D1_CANDIDATE_OVERLAP_TOO_SMALL:"
            f"{policy_family}:"
            f"{delta_hours}:"
            f"{matched_rows}"
        ),
    )

    technical_correlations: dict[
        str,
        float | None,
    ] = {}

    for feature in (
        technical_features
    ):

        comparison = (
            _feature_comparison(
                frozen_train,
                aligned,
                feature,
            )
        )

        technical_correlations[
            feature
        ] = (
            _safe_float(
                comparison.get(
                    "paired_correlation"
                )
            )
        )

    anchor_correlations = {
        feature: (
            technical_correlations[
                feature
            ]
        )
        for feature
        in D1_ANCHOR_FEATURES
    }

    all_values = list(
        technical_correlations.values()
    )

    anchor_values = list(
        anchor_correlations.values()
    )

    age_comparison = (
        _feature_comparison(
            frozen_train,
            aligned,
            "d1_age_minutes",
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

    age_standardized_shift = (
        _safe_float(
            age_comparison.get(
                "standardized_mean_shift"
            )
        )
    )

    finite_age = pd.to_numeric(
        aligned[
            "d1_age_minutes"
        ],
        errors="coerce",
    )

    age_median = (
        float(
            finite_age.median()
        )
        if bool(
            finite_age.notna().any()
        )
        else None
    )

    return {
        "policy_family": (
            policy_family
        ),
        "delta_hours": int(
            delta_hours
        ),
        "effective_rule": (
            (
                "SOURCE_TIME_PLUS_SEASONAL_CLOCK_OFFSET_"
                "PLUS_24H_PLUS_DELTA"
            )
            if (
                policy_family
                ==
                "SEASONAL_CLOCK_PLUS_D1_CLOSE"
            )
            else
            (
                "SOURCE_TIME_PLUS_24H_PLUS_DELTA"
            )
        ),
        "alignment": (
            alignment_meta
        ),
        "all_technical_feature_count": int(
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
        "d1_age": {
            "current_median_minutes": (
                age_median
            ),
            "paired_correlation": (
                age_correlation
            ),
            "psi": (
                age_psi
            ),
            "standardized_mean_shift": (
                age_standardized_shift
            ),
        },
        "anchor_correlations": (
            anchor_correlations
        ),
        "technical_correlations": (
            technical_correlations
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

    all_095 = int(
        document.get(
            "all_technical_correlation_ge_0_95_count",
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
        all_095,
        age_correlation
        if age_correlation is not None
        else -2.0,
    )


def _decision(
    candidate_documents: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
) -> dict[str, Any]:

    _require(
        bool(
            candidate_documents
        ),
        "NO_D1_ALIGNMENT_CANDIDATES",
    )

    ranked = sorted(
        candidate_documents,
        key=_candidate_score,
        reverse=True,
    )

    best = (
        ranked[
            0
        ]
    )

    current_policy: (
        Mapping[
            str,
            Any,
        ]
        |
        None
    ) = next(
        (
            document
            for document
            in candidate_documents
            if (
                str(
                    document.get(
                        "policy_family",
                        "",
                    )
                )
                ==
                "SEASONAL_CLOCK_PLUS_D1_CLOSE"
                and
                int(
                    document.get(
                        "delta_hours",
                        999,
                    )
                )
                ==
                0
            )
        ),
        None,
    )

    if current_policy is None:

        raise RuntimeError(
            "CURRENT_D1_POLICY_CANDIDATE_MISSING"
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

    current_anchor = (
        _safe_float(
            current_policy.get(
                "anchor_median_correlation"
            )
        )
    )

    current_all = (
        _safe_float(
            current_policy.get(
                "all_technical_median_correlation"
            )
        )
    )

    anchor_gain: (
        float
        |
        None
    ) = None

    if (
        best_anchor is not None
        and
        current_anchor is not None
    ):

        anchor_gain = float(
            best_anchor
            -
            current_anchor
        )

    best_family = str(
        best.get(
            "policy_family",
            "",
        )
    )

    best_delta = int(
        best.get(
            "delta_hours",
            0,
        )
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
        MIN_IMPROVEMENT_VS_CURRENT
    ):

        status = (
            "D1_AVAILABILITY_ALIGNMENT_OFFSET_CONFIRMED"
        )

        reason = (
            "A_SIMPLE_D1_AVAILABILITY_TIME_POLICY_"
            "MATERIALLY_RESTORES_FAST_AND_FULL_"
            "TECHNICAL_FEATURE_CORRESPONDENCE"
        )

        next_action = (
            "TRACE_CONFIRMED_D1_AVAILABILITY_POLICY_"
            "TO_FROZEN_SOURCE_SEMANTICS_BEFORE_"
            "UPDATING_FULL_MTF_AUDIT"
        )

    elif (
        best_anchor is not None
        and
        best_anchor
        >=
        LIKELY_ANCHOR_MEDIAN_CORRELATION
        and
        anchor_gain is not None
        and
        anchor_gain
        >=
        MIN_IMPROVEMENT_VS_CURRENT
    ):

        status = (
            "D1_AVAILABILITY_ALIGNMENT_OFFSET_LIKELY"
        )

        reason = (
            "A_SIMPLE_D1_AVAILABILITY_SHIFT_IMPROVES_"
            "FAST_FEATURE_ALIGNMENT_BUT_DOES_NOT_"
            "FULLY_RESTORE_D1_PORTABILITY"
        )

        next_action = (
            "VERIFY_D1_RAW_BAR_BOUNDARY_AND_"
            "FROZEN_D1_AVAILABILITY_CONVENTION"
        )

    else:

        status = (
            "D1_NATIVE_BAR_AGGREGATION_BOUNDARY_MISMATCH_LIKELY"
        )

        reason = (
            "NO_TESTED_PLUS_OR_MINUS_SIX_HOUR_"
            "AVAILABILITY_POLICY_RESTORES_D1_FAST_"
            "FEATURE_CORRESPONDENCE"
        )

        next_action = (
            "RECONSTRUCT_CANONICAL_D1_BARS_FROM_"
            "PORTABLE_H1_DATA_AND_SCAN_DAILY_"
            "SESSION_BOUNDARY"
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "selected_policy_family": (
            best_family
        ),
        "selected_delta_hours": (
            best_delta
        ),
        "selected_anchor_median_correlation": (
            best_anchor
        ),
        "selected_all_technical_median_correlation": (
            best_all
        ),
        "current_policy_anchor_median_correlation": (
            current_anchor
        ),
        "current_policy_all_technical_median_correlation": (
            current_all
        ),
        "anchor_median_gain_vs_current": (
            anchor_gain
        ),
        "d1_native_portability_confirmed": bool(
            status
            ==
            "D1_AVAILABILITY_ALIGNMENT_OFFSET_CONFIRMED"
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
        len(
            frozen_train
        )
        ==
        base.EXPECTED_TRAIN_ROWS,
        (
            "FROZEN_TRAIN_ROW_COUNT_MISMATCH:"
            f"{len(frozen_train)}"
        ),
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
                days=(
                    full
                    .FETCH_WARMUP_DAYS[
                        "D1"
                    ]
                )
            )
            -
            pd.Timedelta(
                days=7
            )
        )

        fetch_end = (
            train_end
            +
            pd.Timedelta(
                days=7
            )
        )

        rates = (
            mt5.copy_rates_range(
                broker_symbol,
                mt5.TIMEFRAME_D1,
                fetch_start.to_pydatetime(),
                fetch_end.to_pydatetime(),
            )
        )

        raw_d1 = (
            base
            ._mt5_rates_frame(
                rates
            )
        )

        _require(
            not raw_d1.empty,
            "CURRENT_BROKER_D1_EMPTY",
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

        raw_d1 = (
            raw_d1
            .sort_values(
                "time"
            )
            .reset_index(
                drop=True
            )
        )

        _require(
            not bool(
                raw_d1[
                    "time"
                ]
                .duplicated()
                .any()
            ),
            "CURRENT_BROKER_D1_TIME_DUPLICATES",
        )

        builder = (
            TrainingMatrixBuilder(
                canonical_root=(
                    CANONICAL_ROOT
                )
            )
        )

        generated_d1 = (
            builder
            ._generate_feature_frame(
                frame=raw_d1,
                timeframe="D1",
            )
        )

        _require(
            isinstance(
                generated_d1,
                pd.DataFrame,
            ),
            "D1_FEATURE_GENERATOR_DID_NOT_RETURN_DATAFRAME",
        )

        required_generated = {
            "time",
            *technical_features,
        }

        missing_generated = sorted(
            required_generated
            -
            set(
                str(
                    column
                )
                for column
                in generated_d1.columns
            )
        )

        _require(
            not missing_generated,
            (
                "D1_GENERATED_FEATURES_MISSING:"
                f"{missing_generated}"
            ),
        )

        generated_d1[
            "time"
        ] = (
            _canonical_time(
                generated_d1[
                    "time"
                ]
            )
        )

        candidate_documents: list[
            dict[str, Any]
        ] = []

        for policy_family in (
            "SEASONAL_CLOCK_PLUS_D1_CLOSE",
            "RAW_SOURCE_D1_CLOSE",
        ):

            for delta_hours in (
                DELTA_HOURS
            ):

                candidate_documents.append(
                    _candidate_document(
                        frozen_train=(
                            frozen_train
                        ),
                        generated_d1=(
                            generated_d1
                        ),
                        technical_features=(
                            technical_features
                        ),
                        policy_family=(
                            policy_family
                        ),
                        delta_hours=(
                            delta_hours
                        ),
                    )
                )

        ranked = sorted(
            candidate_documents,
            key=_candidate_score,
            reverse=True,
        )

        decision = (
            _decision(
                candidate_documents
            )
        )

        return {
            "valid": True,
            "reason": (
                "OK_XAUUSD_CURRENT_BROKER_D1_"
                "AVAILABILITY_ALIGNMENT_DIAGNOSTIC"
            ),
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "research_scope": (
                "D1_NATIVE_BAR_FEATURE_AVAILABILITY_"
                "AND_TIME_ALIGNMENT_TRAIN_ONLY"
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
                "raw_d1_rows": int(
                    len(
                        raw_d1
                    )
                ),
                "generated_d1_rows": int(
                    len(
                        generated_d1
                    )
                ),
                "raw_d1_time_start": (
                    pd.Timestamp(
                        raw_d1[
                            "time"
                        ].min()
                    ).isoformat()
                ),
                "raw_d1_time_end": (
                    pd.Timestamp(
                        raw_d1[
                            "time"
                        ].max()
                    ).isoformat()
                ),
            },
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
                "policy_families": [
                    "SEASONAL_CLOCK_PLUS_D1_CLOSE",
                    "RAW_SOURCE_D1_CLOSE",
                ],
                "delta_hours_tested": list(
                    DELTA_HOURS
                ),
                "candidate_count": int(
                    len(
                        candidate_documents
                    )
                ),
                "selection_primary": (
                    "MAX_D1_FAST_ANCHOR_MEDIAN_CORRELATION"
                ),
                "selection_secondary": (
                    "MAX_ALL_43_D1_TECHNICAL_MEDIAN_CORRELATION"
                ),
                "selection_tertiary": (
                    "MAX_D1_AGE_CORRELATION"
                ),
                "native_d1_ohlc_reaggregation_performed": (
                    False
                ),
            },
            "thresholds": {
                "minimum_overlap_rows": (
                    MIN_OVERLAP_ROWS
                ),
                "confirmed_anchor_median_correlation": (
                    CONFIRMED_ANCHOR_MEDIAN_CORRELATION
                ),
                "confirmed_all_median_correlation": (
                    CONFIRMED_ALL_MEDIAN_CORRELATION
                ),
                "likely_anchor_median_correlation": (
                    LIKELY_ANCHOR_MEDIAN_CORRELATION
                ),
                "minimum_improvement_vs_current": (
                    MIN_IMPROVEMENT_VS_CURRENT
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
                    "policy_family": (
                        document[
                            "policy_family"
                        ]
                    ),
                    "delta_hours": (
                        document[
                            "delta_hours"
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
                    "d1_age": (
                        document[
                            "d1_age"
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
                candidate_documents
            ),
            "utc_full_audit_note": {
                "full_audit_reported_portable": (
                    False
                ),
                "scientific_interpretation": (
                    "KNOWN_PSI_FALSE_POSITIVE_ON_"
                    "DETERMINISTIC_DISCRETE_CYCLICAL_FEATURE"
                ),
                "evidence": {
                    "utc_group_median_correlation": (
                        0.9999999999999996
                    ),
                    "all_four_strong_correlation": (
                        True
                    ),
                    "utc_day_sin_paired_correlation": (
                        0.9999999999999996
                    ),
                    "utc_day_sin_paired_normalized_abs_difference": (
                        6.068713832726025e-12
                    ),
                },
                "full_runner_fix_deferred_until_d1_gate_complete": (
                    True
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
                "broker_specific_retraining_authorized": (
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
                "if_simple_availability_offset_confirmed": (
                    "TRACE_SELECTED_D1_AVAILABILITY_SEMANTICS_"
                    "BEFORE_UPDATING_FULL_MTF_AUDIT"
                ),
                "if_simple_availability_offset_not_confirmed": (
                    "RECONSTRUCT_CANONICAL_D1_FROM_PORTABLE_H1_"
                    "AND_SCAN_DAILY_SESSION_BOUNDARY"
                ),
                "utc_metric_fix_deferred": (
                    True
                ),
                "full_mtf_runner_not_committed": (
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
                        "AVAILABILITY_ALIGNMENT_DIAGNOSTIC_FAILED"
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