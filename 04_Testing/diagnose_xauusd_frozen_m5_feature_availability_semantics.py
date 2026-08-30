from __future__ import annotations

import importlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


ANALYSIS_VERSION = (
    "XAUUSD_FROZEN_M5_FEATURE_AVAILABILITY_SEMANTICS_V1"
)

BASE_AUDIT_MODULE = (
    "04_Testing."
    "analyze_xauusd_current_broker_m5_domain_shift"
)

RAW_DIAGNOSTIC_MODULE = (
    "04_Testing."
    "diagnose_xauusd_current_broker_m5_raw_ohlc_alignment"
)


M5_SECONDS = 300

LAG_CANDIDATES_SECONDS = (
    -600,
    -300,
    0,
    300,
    600,
)


EXPECTED_PRICE_FEATURE_COUNT = 43

MIN_OVERLAP_ROWS = 5000

CONFIRMED_ANCHOR_MEDIAN_CORRELATION = 0.99

CONFIRMED_PRICE_MEDIAN_CORRELATION = 0.99

CONFIRMED_GAIN_VS_ZERO = 0.25

CONFIRMED_ANCHOR_SHARE_GE_095 = 0.90


AVAILABILITY_ANCHOR_FEATURES = (
    "m5_rsi_slope",
    "m5_roc10",
    "m5_momentum10",
    "m5_true_range",
    "m5_candle_range",
    "m5_body",
    "m5_range",
    "m5_upper_wick",
    "m5_lower_wick",
    "m5_body_ratio",
    "m5_upper_wick_ratio",
    "m5_lower_wick_ratio",
)


base: Any = importlib.import_module(
    BASE_AUDIT_MODULE
)

raw_module: Any = importlib.import_module(
    RAW_DIAGNOSTIC_MODULE
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


def _price_feature_names(
    generator_base_features: Sequence[
        str
    ],
) -> list[str]:

    comparison_features = (
        base
        ._comparison_feature_names(
            generator_base_features
        )
    )

    broker_sensitive = {
        str(
            feature
        )
        for feature
        in base.BROKER_SENSITIVE_FEATURES
    }

    price_features = [
        str(
            feature
        )
        for feature
        in comparison_features
        if str(
            feature
        )
        not in broker_sensitive
    ]

    _require(
        len(
            price_features
        )
        ==
        EXPECTED_PRICE_FEATURE_COUNT,
        (
            "PRICE_FEATURE_COUNT_MISMATCH:"
            f"{len(price_features)}"
        ),
    )

    _require(
        len(
            set(
                price_features
            )
        )
        ==
        len(
            price_features
        ),
        "PRICE_FEATURE_NAMES_NOT_UNIQUE",
    )

    return (
        price_features
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


def _lag_document(
    frozen_train: pd.DataFrame,
    replayed_features: pd.DataFrame,
    *,
    price_features: Sequence[
        str
    ],
    lag_seconds: int,
) -> dict[str, Any]:

    frozen_projection = (
        frozen_train[
            [
                "decision_time",
                *price_features,
            ]
        ]
        .rename(
            columns={
                feature: (
                    f"{feature}_frozen"
                )
                for feature
                in price_features
            }
        )
        .copy()
    )

    replay_projection = (
        replayed_features[
            [
                "decision_time",
                *price_features,
            ]
        ]
        .rename(
            columns={
                feature: (
                    f"{feature}_current"
                )
                for feature
                in price_features
            }
        )
        .copy()
    )

    replay_projection[
        "decision_time"
    ] = (
        pd.to_datetime(
            replay_projection[
                "decision_time"
            ],
            utc=True,
            errors="raise",
        )
        +
        pd.to_timedelta(
            lag_seconds,
            unit="s",
        )
    )

    _require(
        not bool(
            replay_projection[
                "decision_time"
            ].duplicated().any()
        ),
        (
            "REPLAY_SHIFTED_TIME_DUPLICATES:"
            f"{lag_seconds}"
        ),
    )

    paired = (
        frozen_projection
        .merge(
            replay_projection,
            on="decision_time",
            how="inner",
            validate="one_to_one",
        )
        .sort_values(
            "decision_time"
        )
        .reset_index(
            drop=True
        )
    )

    feature_documents: list[
        dict[str, Any]
    ] = []

    correlations: dict[
        str,
        float | None,
    ] = {}

    normalized_abs_differences: dict[
        str,
        float | None,
    ] = {}

    for feature in price_features:

        comparison = (
            base
            ._feature_comparison(
                paired,
                feature,
            )
        )

        correlation = (
            _safe_float(
                comparison.get(
                    "paired_correlation"
                )
            )
        )

        normalized_abs_difference = (
            _safe_float(
                comparison.get(
                    "paired_median_abs_diff_reference_std"
                )
            )
        )

        correlations[
            feature
        ] = (
            correlation
        )

        normalized_abs_differences[
            feature
        ] = (
            normalized_abs_difference
        )

        feature_documents.append(
            {
                "feature": (
                    feature
                ),
                "paired_correlation": (
                    correlation
                ),
                "paired_median_abs_diff_reference_std": (
                    normalized_abs_difference
                ),
            }
        )

    all_values = list(
        correlations.values()
    )

    anchor_correlations = {
        feature: (
            correlations[
                feature
            ]
        )
        for feature
        in AVAILABILITY_ANCHOR_FEATURES
    }

    anchor_values = list(
        anchor_correlations.values()
    )

    anchor_ge_095 = (
        _count_at_least(
            anchor_values,
            0.95,
        )
    )

    anchor_finite_count = int(
        sum(
            1
            for value
            in anchor_values
            if value is not None
        )
    )

    anchor_share_ge_095 = (
        float(
            anchor_ge_095
            /
            anchor_finite_count
        )
        if anchor_finite_count
        >
        0
        else
        None
    )

    normalized_diff_values = list(
        normalized_abs_differences.values()
    )

    return {
        "lag_seconds": int(
            lag_seconds
        ),
        "lag_bars_m5": float(
            lag_seconds
            /
            M5_SECONDS
        ),
        "interpretation": (
            "REPLAYED_GENERATOR_FEATURE_TIME_SHIFT_"
            "BEFORE_JOIN_TO_FROZEN_TRAIN_DECISION_TIME"
        ),
        "overlap_rows": int(
            len(
                paired
            )
        ),
        "price_feature_count": int(
            len(
                price_features
            )
        ),
        "price_median_correlation": (
            _median_finite(
                all_values
            )
        ),
        "price_correlation_ge_0_95_count": (
            _count_at_least(
                all_values,
                0.95,
            )
        ),
        "price_correlation_ge_0_99_count": (
            _count_at_least(
                all_values,
                0.99,
            )
        ),
        "price_median_normalized_abs_difference": (
            _median_finite(
                normalized_diff_values
            )
        ),
        "anchor_feature_count": int(
            len(
                AVAILABILITY_ANCHOR_FEATURES
            )
        ),
        "anchor_median_correlation": (
            _median_finite(
                anchor_values
            )
        ),
        "anchor_correlation_ge_0_95_count": (
            anchor_ge_095
        ),
        "anchor_correlation_ge_0_95_share": (
            anchor_share_ge_095
        ),
        "anchor_correlations": (
            anchor_correlations
        ),
        "feature_metrics": (
            feature_documents
        ),
    }


def _lag_score(
    document: Mapping[
        str,
        Any,
    ],
) -> tuple[
    float,
    float,
    float,
    int,
    int,
    int,
]:

    anchor_median = (
        _safe_float(
            document.get(
                "anchor_median_correlation"
            )
        )
    )

    price_median = (
        _safe_float(
            document.get(
                "price_median_correlation"
            )
        )
    )

    anchor_share = (
        _safe_float(
            document.get(
                "anchor_correlation_ge_0_95_share"
            )
        )
    )

    price_099 = int(
        document.get(
            "price_correlation_ge_0_99_count",
            0,
        )
    )

    price_095 = int(
        document.get(
            "price_correlation_ge_0_95_count",
            0,
        )
    )

    overlap = int(
        document.get(
            "overlap_rows",
            0,
        )
    )

    return (
        anchor_median
        if anchor_median is not None
        else -2.0,
        price_median
        if price_median is not None
        else -2.0,
        anchor_share
        if anchor_share is not None
        else -2.0,
        price_099,
        price_095,
        overlap,
    )


def _decision(
    lag_documents: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
) -> dict[str, Any]:

    _require(
        bool(
            lag_documents
        ),
        "NO_FROZEN_REPLAY_LAG_DOCUMENTS",
    )

    ranked = sorted(
        lag_documents,
        key=_lag_score,
        reverse=True,
    )

    best = (
        ranked[
            0
        ]
    )

    zero: (
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
            in lag_documents
            if int(
                document.get(
                    "lag_seconds",
                    999999,
                )
            )
            ==
            0
        ),
        None,
    )

    if zero is None:
        raise RuntimeError(
            "ZERO_LAG_FROZEN_REPLAY_DOCUMENT_MISSING"
        )

    best_lag = int(
        best.get(
            "lag_seconds",
            0,
        )
    )

    best_overlap = int(
        best.get(
            "overlap_rows",
            0,
        )
    )

    best_anchor_median = (
        _safe_float(
            best.get(
                "anchor_median_correlation"
            )
        )
    )

    zero_anchor_median = (
        _safe_float(
            zero.get(
                "anchor_median_correlation"
            )
        )
    )

    best_price_median = (
        _safe_float(
            best.get(
                "price_median_correlation"
            )
        )
    )

    zero_price_median = (
        _safe_float(
            zero.get(
                "price_median_correlation"
            )
        )
    )

    best_anchor_share = (
        _safe_float(
            best.get(
                "anchor_correlation_ge_0_95_share"
            )
        )
    )

    anchor_gain: (
        float
        |
        None
    ) = None

    if (
        best_anchor_median
        is not None
        and
        zero_anchor_median
        is not None
    ):

        anchor_gain = float(
            best_anchor_median
            -
            zero_anchor_median
        )

    if (
        best_overlap
        <
        MIN_OVERLAP_ROWS
    ):

        status = (
            "INSUFFICIENT_FROZEN_REPLAY_OVERLAP"
        )

        reason = (
            "BEST_REPLAY_LAG_HAS_TOO_FEW_TRAIN_ROWS"
        )

        next_action = (
            "AUDIT_FROZEN_HISTORICAL_SOURCE_COVERAGE"
        )

    elif (
        best_lag
        ==
        M5_SECONDS
        and
        best_anchor_median
        is not None
        and
        best_anchor_median
        >=
        CONFIRMED_ANCHOR_MEDIAN_CORRELATION
        and
        best_price_median
        is not None
        and
        best_price_median
        >=
        CONFIRMED_PRICE_MEDIAN_CORRELATION
        and
        best_anchor_share
        is not None
        and
        best_anchor_share
        >=
        CONFIRMED_ANCHOR_SHARE_GE_095
        and
        anchor_gain
        is not None
        and
        anchor_gain
        >=
        CONFIRMED_GAIN_VS_ZERO
    ):

        status = (
            "FROZEN_M5_FEATURE_AVAILABILITY_PLUS_ONE_BAR_CONFIRMED"
        )

        reason = (
            "EXACT_FROZEN_EXNESS_RAW_SOURCE_REPLAY_SHOWS_"
            "TRAIN_DECISION_TIME_IS_GENERATOR_BAR_TIME_PLUS_300_SECONDS"
        )

        next_action = (
            "RERUN_MAPPED_CURRENT_BROKER_M5_DOMAIN_SHIFT_"
            "WITH_PLUS_300_SECOND_PRICE_FEATURE_AVAILABILITY_SHIFT"
        )

    elif (
        best_lag
        ==
        0
        and
        best_anchor_median
        is not None
        and
        best_anchor_median
        >=
        CONFIRMED_ANCHOR_MEDIAN_CORRELATION
        and
        best_price_median
        is not None
        and
        best_price_median
        >=
        CONFIRMED_PRICE_MEDIAN_CORRELATION
    ):

        status = (
            "FROZEN_M5_ZERO_LAG_AVAILABILITY_CONFIRMED"
        )

        reason = (
            "FROZEN_SOURCE_REPLAY_ALIGNS_AT_GENERATOR_BAR_TIME"
        )

        next_action = (
            "DO_NOT_APPLY_PLUS_300_SECOND_FEATURE_SHIFT;"
            "AUDIT_CURRENT_BROKER_PIPELINE_PROVENANCE"
        )

    else:

        status = (
            "FROZEN_M5_FEATURE_AVAILABILITY_SEMANTICS_UNRESOLVED"
        )

        reason = (
            "FROZEN_EXNESS_SOURCE_REPLAY_DOES_NOT_CONFIRM_"
            "A_CLEAN_PLUS_ONE_BAR_OR_ZERO_LAG_SEMANTIC"
        )

        next_action = (
            "AUDIT_TRAINING_MATRIX_TIME_ASSIGNMENT_SOURCE"
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "selected_replay_feature_shift_seconds": (
            best_lag
        ),
        "selected_replay_feature_shift_m5_bars": float(
            best_lag
            /
            M5_SECONDS
        ),
        "selected_overlap_rows": (
            best_overlap
        ),
        "selected_anchor_median_correlation": (
            best_anchor_median
        ),
        "zero_lag_anchor_median_correlation": (
            zero_anchor_median
        ),
        "anchor_median_correlation_gain_vs_zero": (
            anchor_gain
        ),
        "selected_price_median_correlation": (
            best_price_median
        ),
        "zero_lag_price_median_correlation": (
            zero_price_median
        ),
        "selected_anchor_share_ge_0_95": (
            best_anchor_share
        ),
        "current_broker_mapped_domain_rerun_allowed": bool(
            status
            ==
            "FROZEN_M5_FEATURE_AVAILABILITY_PLUS_ONE_BAR_CONFIRMED"
        ),
        "full_333_portability_claimed": (
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

    historical_sources = (
        manifest.get(
            "source_historical_snapshots"
        )
    )

    if not isinstance(
        historical_sources,
        Mapping,
    ):
        raise RuntimeError(
            "SOURCE_HISTORICAL_SNAPSHOTS_MISSING"
        )

    m5_source = (
        historical_sources.get(
            "M5"
        )
    )

    if not isinstance(
        m5_source,
        Mapping,
    ):
        raise RuntimeError(
            "SOURCE_HISTORICAL_M5_MISSING"
        )

    _require(
        str(
            m5_source.get(
                "dataset_id",
                "",
            )
        )
        ==
        raw_module
        .EXPECTED_HISTORICAL_M5_DATASET_ID,
        "FROZEN_M5_SOURCE_DATASET_ID_MISMATCH",
    )

    _require(
        str(
            m5_source.get(
                "dataset_sha256",
                "",
            )
        )
        ==
        raw_module
        .EXPECTED_HISTORICAL_M5_DATASET_SHA256,
        "FROZEN_M5_SOURCE_DATASET_SHA256_MISMATCH",
    )

    (
        historical_dataset_path,
        _historical_manifest_path,
        historical_manifest,
    ) = (
        raw_module
        ._discover_exact_historical_m5()
    )

    _require(
        str(
            historical_manifest.get(
                "dataset_id",
                "",
            )
        )
        ==
        raw_module
        .EXPECTED_HISTORICAL_M5_DATASET_ID,
        "HISTORICAL_M5_MANIFEST_ID_MISMATCH",
    )

    _require(
        str(
            historical_manifest.get(
                "dataset_sha256",
                "",
            )
        )
        ==
        raw_module
        .EXPECTED_HISTORICAL_M5_DATASET_SHA256,
        "HISTORICAL_M5_MANIFEST_SHA_MISMATCH",
    )

    generator_base_features = (
        base
        ._base_feature_names()
    )

    _require(
        len(
            generator_base_features
        )
        ==
        base.EXPECTED_BASE_FEATURE_COUNT,
        (
            "GENERATOR_BASE_FEATURE_COUNT_MISMATCH:"
            f"{len(generator_base_features)}"
        ),
    )

    price_features = (
        _price_feature_names(
            generator_base_features
        )
    )

    for feature in (
        AVAILABILITY_ANCHOR_FEATURES
    ):

        _require(
            feature
            in
            price_features,
            (
                "AVAILABILITY_ANCHOR_NOT_IN_PRICE_CONTRACT:"
                f"{feature}"
            ),
        )

    frozen_train = (
        base
        ._load_frozen_train_only(
            dataset_path,
            price_features,
        )
    )

    frozen_raw_m5 = (
        raw_module
        ._load_frozen_raw_m5(
            historical_dataset_path
        )
    )

    (
        replayed_features,
        generation_meta,
    ) = (
        base
        ._build_current_m5_comparison_frame(
            frozen_raw_m5,
            generator_base_features,
        )
    )

    missing_replayed = sorted(
        set(
            price_features
        )
        -
        set(
            str(
                column
            )
            for column
            in replayed_features.columns
        )
    )

    _require(
        not missing_replayed,
        (
            "REPLAYED_PRICE_FEATURES_MISSING:"
            f"{missing_replayed}"
        ),
    )

    _require(
        not bool(
            replayed_features[
                "decision_time"
            ].duplicated().any()
        ),
        "REPLAYED_GENERATOR_TIME_DUPLICATES",
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

    lag_buffer = max(
        abs(
            lag
        )
        for lag
        in LAG_CANDIDATES_SECONDS
    )

    replayed_features = (
        replayed_features.loc[
            (
                replayed_features[
                    "decision_time"
                ]
                >=
                (
                    train_start
                    -
                    pd.Timedelta(
                        seconds=lag_buffer
                    )
                )
            )
            &
            (
                replayed_features[
                    "decision_time"
                ]
                <=
                (
                    train_end
                    +
                    pd.Timedelta(
                        seconds=lag_buffer
                    )
                )
            )
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    _require(
        not replayed_features.empty,
        "REPLAYED_FROZEN_M5_WINDOW_EMPTY",
    )

    lag_documents = [
        _lag_document(
            frozen_train,
            replayed_features,
            price_features=(
                price_features
            ),
            lag_seconds=(
                lag_seconds
            ),
        )
        for lag_seconds
        in LAG_CANDIDATES_SECONDS
    ]

    ranked = sorted(
        lag_documents,
        key=_lag_score,
        reverse=True,
    )

    decision = (
        _decision(
            lag_documents
        )
    )

    raw_start = pd.Timestamp(
        frozen_raw_m5[
            "time"
        ].min()
    )

    raw_end = pd.Timestamp(
        frozen_raw_m5[
            "time"
        ].max()
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_FROZEN_M5_"
            "FEATURE_AVAILABILITY_SEMANTICS_DIAGNOSTIC"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "frozen_training_reference": {
            "dataset_id": (
                base.EXPECTED_DATASET_ID
            ),
            "dataset_sha256": (
                base.EXPECTED_DATASET_SHA256
            ),
            "training_manifest_sha256": (
                base.EXPECTED_TRAINING_MANIFEST_SHA256
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
            "time_start": (
                train_start.isoformat()
            ),
            "time_end": (
                train_end.isoformat()
            ),
        },
        "frozen_raw_m5_reference": {
            "dataset_id": (
                raw_module
                .EXPECTED_HISTORICAL_M5_DATASET_ID
            ),
            "dataset_sha256": (
                raw_module
                .EXPECTED_HISTORICAL_M5_DATASET_SHA256
            ),
            "hash_validated": (
                True
            ),
            "full_raw_rows": int(
                len(
                    frozen_raw_m5
                )
            ),
            "time_start": (
                raw_start.isoformat()
            ),
            "time_end": (
                raw_end.isoformat()
            ),
            "filesystem_path_emitted": (
                False
            ),
        },
        "feature_contract": {
            "generator_base_feature_count": int(
                len(
                    generator_base_features
                )
            ),
            "price_comparison_feature_count": int(
                len(
                    price_features
                )
            ),
            "broker_sensitive_features_excluded": list(
                base.BROKER_SENSITIVE_FEATURES
            ),
            "price_comparison_features": (
                price_features
            ),
            "exact_existing_generator_used": (
                True
            ),
            "feature_generation": (
                generation_meta
            ),
        },
        "availability_policy": {
            "candidate_replay_feature_shifts_seconds": list(
                LAG_CANDIDATES_SECONDS
            ),
            "candidate_replay_feature_shifts_m5_bars": [
                float(
                    value
                    /
                    M5_SECONDS
                )
                for value
                in LAG_CANDIDATES_SECONDS
            ],
            "anchor_features": list(
                AVAILABILITY_ANCHOR_FEATURES
            ),
            "selection_primary": (
                "MAX_ANCHOR_MEDIAN_CORRELATION"
            ),
            "selection_secondary": (
                "MAX_PRICE_MEDIAN_CORRELATION"
            ),
            "selection_tertiary": (
                "MAX_ANCHOR_SHARE_CORRELATION_GE_0_95"
            ),
            "broker_sensitive_features_used_for_selection": (
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
            "confirmed_price_median_correlation": (
                CONFIRMED_PRICE_MEDIAN_CORRELATION
            ),
            "confirmed_gain_vs_zero": (
                CONFIRMED_GAIN_VS_ZERO
            ),
            "confirmed_anchor_share_ge_0_95": (
                CONFIRMED_ANCHOR_SHARE_GE_095
            ),
        },
        "decision": (
            decision
        ),
        "lag_ranking": [
            {
                "rank": int(
                    index
                ),
                "lag_seconds": (
                    document[
                        "lag_seconds"
                    ]
                ),
                "lag_bars_m5": (
                    document[
                        "lag_bars_m5"
                    ]
                ),
                "overlap_rows": (
                    document[
                        "overlap_rows"
                    ]
                ),
                "anchor_median_correlation": (
                    document[
                        "anchor_median_correlation"
                    ]
                ),
                "anchor_correlation_ge_0_95_share": (
                    document[
                        "anchor_correlation_ge_0_95_share"
                    ]
                ),
                "price_median_correlation": (
                    document[
                        "price_median_correlation"
                    ]
                ),
                "price_correlation_ge_0_95_count": (
                    document[
                        "price_correlation_ge_0_95_count"
                    ]
                ),
                "price_correlation_ge_0_99_count": (
                    document[
                        "price_correlation_ge_0_99_count"
                    ]
                ),
                "price_median_normalized_abs_difference": (
                    document[
                        "price_median_normalized_abs_difference"
                    ]
                ),
            }
            for index, document
            in enumerate(
                ranked,
                start=1,
            )
        ],
        "lag_diagnostics": (
            lag_documents
        ),
        "scientific_policy": {
            "frozen_training_train_only_loaded": (
                True
            ),
            "frozen_raw_m5_loaded": (
                True
            ),
            "frozen_raw_m5_hash_verified": (
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
            "live_authorized": (
                False
            ),
            "account_scope_identifier_emitted": (
                False
            ),
        },
        "next_decision_contract": {
            "if_plus_one_bar_confirmed": (
                "UPDATE_MAPPED_CURRENT_BROKER_M5_DOMAIN_AUDIT_"
                "WITH_PLUS_300_SECOND_PRICE_FEATURE_AVAILABILITY_SHIFT"
            ),
            "if_zero_lag_confirmed": (
                "REJECT_PLUS_300_SECOND_CURRENT_BROKER_SHIFT_"
                "AND_AUDIT_CURRENT_PIPELINE_PROVENANCE"
            ),
            "if_unresolved": (
                "AUDIT_TRAINING_MATRIX_TIME_ASSIGNMENT_SOURCE"
            ),
            "broker_sensitive_features_remain_separate": (
                True
            ),
            "test_holdout_remains_untouched": (
                True
            ),
            "full_333_portability_not_decided": (
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
                        "XAUUSD_FROZEN_M5_"
                        "FEATURE_AVAILABILITY_SEMANTICS_DIAGNOSTIC_FAILED"
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
                    "validation_loaded": False,
                    "test_loaded": False,
                    "test_evaluated": False,
                    "mt5_used": False,
                    "current_broker_used": False,
                    "model_trained": False,
                    "model_artifacts_written": False,
                    "orders_sent": False,
                    "positions_modified": False,
                    "risk_engine_modified": False,
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