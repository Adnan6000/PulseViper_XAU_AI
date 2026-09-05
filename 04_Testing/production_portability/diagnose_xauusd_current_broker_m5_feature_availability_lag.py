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
    "XAUUSD_CURRENT_BROKER_M5_FEATURE_AVAILABILITY_LAG_V2"
)

MAPPED_AUDIT_MODULE = (
    "04_Testing."
    "analyze_xauusd_current_broker_m5_domain_shift_mapped"
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

CONFIRMED_MEDIAN_CORRELATION = 0.80

CONFIRMED_GAIN_VS_ZERO = 0.25

CONFIRMED_STRONG_SHARE = 0.60

LIKELY_MEDIAN_CORRELATION = 0.65

LIKELY_GAIN_VS_ZERO = 0.15

LIKELY_STRONG_SHARE = 0.40


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


mapped: Any = importlib.import_module(
    MAPPED_AUDIT_MODULE
)

base: Any = (
    mapped.base
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
    base_features: Sequence[
        str
    ],
) -> list[str]:

    comparison_features = (
        base
        ._comparison_feature_names(
            base_features
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

    overlap_with_broker_sensitive = sorted(
        set(
            price_features
        )
        &
        broker_sensitive
    )

    _require(
        not overlap_with_broker_sensitive,
        (
            "BROKER_SENSITIVE_FEATURES_LEAKED_INTO_"
            "PRICE_LAG_SELECTION:"
            f"{overlap_with_broker_sensitive}"
        ),
    )

    return (
        price_features
    )


def _feature_correlation(
    paired: pd.DataFrame,
    feature: str,
) -> float | None:

    comparison = (
        base
        ._feature_comparison(
            paired,
            feature,
        )
    )

    return (
        _safe_float(
            comparison.get(
                "paired_correlation"
            )
        )
    )


def _feature_correlations(
    paired: pd.DataFrame,
    features: Sequence[
        str
    ],
) -> dict[str, float | None]:

    result: dict[
        str,
        float | None,
    ] = {}

    for feature in features:

        result[
            feature
        ] = (
            _feature_correlation(
                paired,
                feature,
            )
        )

    return (
        result
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
    current_mapped: pd.DataFrame,
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

    current_projection = (
        current_mapped[
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

    current_projection[
        "decision_time"
    ] = (
        pd.to_datetime(
            current_projection[
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
            current_projection[
                "decision_time"
            ].duplicated().any()
        ),
        (
            "SHIFTED_CURRENT_DECISION_TIME_DUPLICATES:"
            f"{lag_seconds}"
        ),
    )

    paired = (
        frozen_projection
        .merge(
            current_projection,
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

    overlap_rows = int(
        len(
            paired
        )
    )

    all_correlations = (
        _feature_correlations(
            paired,
            price_features,
        )
    )

    anchor_correlations = {
        feature: (
            all_correlations[
                feature
            ]
        )
        for feature
        in AVAILABILITY_ANCHOR_FEATURES
    }

    all_values = list(
        all_correlations.values()
    )

    anchor_values = list(
        anchor_correlations.values()
    )

    finite_all_count = int(
        sum(
            1
            for value
            in all_values
            if value
            is not None
        )
    )

    finite_anchor_count = int(
        sum(
            1
            for value
            in anchor_values
            if value
            is not None
        )
    )

    anchor_ge_080 = (
        _count_at_least(
            anchor_values,
            0.80,
        )
    )

    anchor_ge_095 = (
        _count_at_least(
            anchor_values,
            0.95,
        )
    )

    all_ge_080 = (
        _count_at_least(
            all_values,
            0.80,
        )
    )

    all_ge_095 = (
        _count_at_least(
            all_values,
            0.95,
        )
    )

    anchor_strong_share = (
        float(
            anchor_ge_080
            /
            finite_anchor_count
        )
        if finite_anchor_count
        >
        0
        else
        None
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
            "CURRENT_GENERATED_PRICE_FEATURE_TIME_SHIFT_"
            "APPLIED_AFTER_BROKER_CLOCK_MAPPING"
        ),
        "overlap_rows": (
            overlap_rows
        ),
        "price_feature_count": int(
            len(
                price_features
            )
        ),
        "price_features_with_correlation": (
            finite_all_count
        ),
        "price_median_correlation": (
            _median_finite(
                all_values
            )
        ),
        "price_correlation_ge_0_80_count": (
            all_ge_080
        ),
        "price_correlation_ge_0_95_count": (
            all_ge_095
        ),
        "anchor_feature_count": int(
            len(
                AVAILABILITY_ANCHOR_FEATURES
            )
        ),
        "anchor_features_with_correlation": (
            finite_anchor_count
        ),
        "anchor_median_correlation": (
            _median_finite(
                anchor_values
            )
        ),
        "anchor_correlation_ge_0_80_count": (
            anchor_ge_080
        ),
        "anchor_correlation_ge_0_95_count": (
            anchor_ge_095
        ),
        "anchor_correlation_ge_0_80_share": (
            anchor_strong_share
        ),
        "anchor_correlations": (
            anchor_correlations
        ),
        "price_correlations": (
            all_correlations
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
    int,
    int,
    float,
    int,
]:

    anchor_median = (
        _safe_float(
            document.get(
                "anchor_median_correlation"
            )
        )
    )

    anchor_share = (
        _safe_float(
            document.get(
                "anchor_correlation_ge_0_80_share"
            )
        )
    )

    anchor_095 = int(
        document.get(
            "anchor_correlation_ge_0_95_count",
            0,
        )
    )

    anchor_080 = int(
        document.get(
            "anchor_correlation_ge_0_80_count",
            0,
        )
    )

    price_median = (
        _safe_float(
            document.get(
                "price_median_correlation"
            )
        )
    )

    overlap_rows = int(
        document.get(
            "overlap_rows",
            0,
        )
    )

    return (
        anchor_median
        if anchor_median is not None
        else -2.0,
        anchor_share
        if anchor_share is not None
        else -2.0,
        anchor_095,
        anchor_080,
        price_median
        if price_median is not None
        else -2.0,
        overlap_rows,
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
        "NO_FEATURE_AVAILABILITY_LAG_DOCUMENTS",
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
            "ZERO_LAG_FEATURE_DOCUMENT_MISSING"
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

    best_median = (
        _safe_float(
            best.get(
                "anchor_median_correlation"
            )
        )
    )

    zero_median = (
        _safe_float(
            zero.get(
                "anchor_median_correlation"
            )
        )
    )

    best_share = (
        _safe_float(
            best.get(
                "anchor_correlation_ge_0_80_share"
            )
        )
    )

    zero_share = (
        _safe_float(
            zero.get(
                "anchor_correlation_ge_0_80_share"
            )
        )
    )

    correlation_gain: (
        float
        |
        None
    ) = None

    if (
        best_median
        is not None
        and
        zero_median
        is not None
    ):

        correlation_gain = float(
            best_median
            -
            zero_median
        )

    if (
        best_overlap
        <
        MIN_OVERLAP_ROWS
    ):

        status = (
            "INSUFFICIENT_FEATURE_LAG_OVERLAP"
        )

        reason = (
            "BEST_FEATURE_LAG_HAS_TOO_FEW_OVERLAPPING_ROWS"
        )

        next_action = (
            "REVIEW_CURRENT_BROKER_HISTORY_AVAILABILITY"
        )

    elif (
        best_lag
        ==
        0
        and
        best_median
        is not None
        and
        best_median
        >=
        CONFIRMED_MEDIAN_CORRELATION
        and
        best_share
        is not None
        and
        best_share
        >=
        CONFIRMED_STRONG_SHARE
    ):

        status = (
            "ZERO_LAG_FEATURE_AVAILABILITY_CONFIRMED"
        )

        reason = (
            "FAST_M5_PRICE_FEATURES_ALIGN_WITHOUT_"
            "AN_ADDITIONAL_FEATURE_TIME_SHIFT"
        )

        next_action = (
            "AUDIT_EXACT_FEATURE_FORMULAS_AND_"
            "RAW_INPUT_PRICE_BASIS"
        )

    elif (
        best_lag
        !=
        0
        and
        best_median
        is not None
        and
        best_median
        >=
        CONFIRMED_MEDIAN_CORRELATION
        and
        best_share
        is not None
        and
        best_share
        >=
        CONFIRMED_STRONG_SHARE
        and
        correlation_gain
        is not None
        and
        correlation_gain
        >=
        CONFIRMED_GAIN_VS_ZERO
    ):

        status = (
            "NONZERO_FEATURE_AVAILABILITY_OFFSET_CONFIRMED"
        )

        reason = (
            "NONZERO_M5_BAR_SHIFT_MATERIALLY_RESTORES_"
            "FAST_PRICE_FEATURE_CORRESPONDENCE"
        )

        next_action = (
            "AUDIT_FROZEN_FEATURE_AVAILABILITY_SEMANTICS_"
            "AND_APPLY_CONFIRMED_SHIFT_IN_RESEARCH_AUDIT"
        )

    elif (
        best_lag
        !=
        0
        and
        best_median
        is not None
        and
        best_median
        >=
        LIKELY_MEDIAN_CORRELATION
        and
        best_share
        is not None
        and
        best_share
        >=
        LIKELY_STRONG_SHARE
        and
        correlation_gain
        is not None
        and
        correlation_gain
        >=
        LIKELY_GAIN_VS_ZERO
    ):

        status = (
            "NONZERO_FEATURE_AVAILABILITY_OFFSET_LIKELY"
        )

        reason = (
            "NONZERO_M5_BAR_SHIFT_SUBSTANTIALLY_IMPROVES_"
            "FAST_PRICE_FEATURE_CORRESPONDENCE"
        )

        next_action = (
            "INSPECT_FROZEN_FEATURE_BUILD_TIME_SEMANTICS_"
            "BEFORE_DOMAIN_SHIFT_CLASSIFICATION"
        )

    else:

        status = (
            "FEATURE_AVAILABILITY_LAG_NOT_RESOLVED"
        )

        reason = (
            "PLUS_OR_MINUS_TWO_M5_BARS_DO_NOT_RESTORE_"
            "SUFFICIENT_FAST_PRICE_FEATURE_CORRESPONDENCE"
        )

        next_action = (
            "AUDIT_FEATURE_FORMULA_PROVENANCE_AND_"
            "RAW_INPUT_COLUMN_SEMANTICS"
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "selected_current_feature_shift_seconds": (
            best_lag
        ),
        "selected_current_feature_shift_m5_bars": float(
            best_lag
            /
            M5_SECONDS
        ),
        "selected_overlap_rows": (
            best_overlap
        ),
        "selected_anchor_median_correlation": (
            best_median
        ),
        "zero_lag_anchor_median_correlation": (
            zero_median
        ),
        "anchor_median_correlation_gain_vs_zero": (
            correlation_gain
        ),
        "selected_anchor_strong_share": (
            best_share
        ),
        "zero_lag_anchor_strong_share": (
            zero_share
        ),
        "selected_price_median_correlation": (
            best.get(
                "price_median_correlation"
            )
        ),
        "zero_lag_price_median_correlation": (
            zero.get(
                "price_median_correlation"
            )
        ),
        "mapped_domain_shift_classification_allowed": (
            status
            in {
                "ZERO_LAG_FEATURE_AVAILABILITY_CONFIRMED",
                "NONZERO_FEATURE_AVAILABILITY_OFFSET_CONFIRMED",
            }
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
                    base.HISTORY_WARMUP_DAYS
                )
            )
            -
            pd.Timedelta(
                hours=4
            )
        )

        fetch_end = (
            train_end
            +
            pd.Timedelta(
                days=1
            )
            +
            pd.Timedelta(
                hours=4
            )
        )

        rates = (
            mt5.copy_rates_range(
                broker_symbol,
                mt5.TIMEFRAME_M5,
                fetch_start.to_pydatetime(),
                fetch_end.to_pydatetime(),
            )
        )

        raw_m5 = (
            base
            ._mt5_rates_frame(
                rates
            )
        )

        (
            current_unmapped,
            generation_meta,
        ) = (
            base
            ._build_current_m5_comparison_frame(
                raw_m5,
                generator_base_features,
            )
        )

        missing_current_features = sorted(
            set(
                price_features
            )
            -
            set(
                str(
                    column
                )
                for column
                in current_unmapped.columns
            )
        )

        _require(
            not missing_current_features,
            (
                "GENERATED_PRICE_FEATURES_MISSING:"
                f"{missing_current_features}"
            ),
        )

        (
            current_mapped,
            mapping_meta,
        ) = (
            mapped
            ._apply_research_time_mapping(
                current_unmapped
            )
        )

        lag_buffer = max(
            abs(
                lag
            )
            for lag
            in LAG_CANDIDATES_SECONDS
        )

        current_mapped = (
            current_mapped.loc[
                (
                    current_mapped[
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
                    current_mapped[
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
            not current_mapped.empty,
            "CURRENT_MAPPED_FEATURE_LAG_WINDOW_EMPTY",
        )

        _require(
            not bool(
                current_mapped[
                    "decision_time"
                ].duplicated().any()
            ),
            "CURRENT_MAPPED_FEATURE_LAG_WINDOW_DUPLICATES",
        )

        lag_documents = [
            _lag_document(
                frozen_train,
                current_mapped,
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

        decision = (
            _decision(
                lag_documents
            )
        )

        ranked = sorted(
            lag_documents,
            key=_lag_score,
            reverse=True,
        )

        current_history_start = pd.Timestamp(
            raw_m5[
                "time"
            ].min()
        )

        current_history_end = pd.Timestamp(
            raw_m5[
                "time"
            ].max()
        )

        return {
            "valid": True,
            "reason": (
                "OK_XAUUSD_CURRENT_BROKER_M5_"
                "FEATURE_AVAILABILITY_LAG_DIAGNOSTIC"
            ),
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "frozen_reference": {
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
                "rows_loaded": int(
                    len(
                        frozen_train
                    )
                ),
                "split_loaded": (
                    "TRAIN_ONLY"
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
                "historical_m5_rows_fetched": int(
                    len(
                        raw_m5
                    )
                ),
                "history_time_start": (
                    current_history_start.isoformat()
                ),
                "history_time_end": (
                    current_history_end.isoformat()
                ),
            },
            "confirmed_broker_clock_mapping": {
                "contract": (
                    mapped
                    ._mapping_contract()
                ),
                "application": (
                    mapping_meta
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
                "feature_generation": (
                    generation_meta
                ),
            },
            "availability_policy": {
                "candidate_feature_time_shifts_seconds": list(
                    LAG_CANDIDATES_SECONDS
                ),
                "candidate_feature_time_shifts_m5_bars": [
                    float(
                        value
                        /
                        M5_SECONDS
                    )
                    for value
                    in LAG_CANDIDATES_SECONDS
                ],
                "shift_interpretation": (
                    "CURRENT_GENERATED_PRICE_FEATURE_TIME_SHIFT_"
                    "AFTER_CONFIRMED_BROKER_CLOCK_MAPPING"
                ),
                "anchor_features": list(
                    AVAILABILITY_ANCHOR_FEATURES
                ),
                "selection_primary": (
                    "MAX_ANCHOR_MEDIAN_PAIRED_CORRELATION"
                ),
                "selection_secondary": (
                    "MAX_ANCHOR_SHARE_CORRELATION_GE_0_80"
                ),
                "selection_tertiary": (
                    "MAX_ANCHOR_COUNT_CORRELATION_GE_0_95"
                ),
                "maximum_absolute_shift_m5_bars": (
                    2
                ),
                "broker_sensitive_features_used_for_selection": (
                    False
                ),
            },
            "thresholds": {
                "minimum_overlap_rows": (
                    MIN_OVERLAP_ROWS
                ),
                "confirmed_median_correlation": (
                    CONFIRMED_MEDIAN_CORRELATION
                ),
                "confirmed_gain_vs_zero": (
                    CONFIRMED_GAIN_VS_ZERO
                ),
                "confirmed_strong_share": (
                    CONFIRMED_STRONG_SHARE
                ),
                "likely_median_correlation": (
                    LIKELY_MEDIAN_CORRELATION
                ),
                "likely_gain_vs_zero": (
                    LIKELY_GAIN_VS_ZERO
                ),
                "likely_strong_share": (
                    LIKELY_STRONG_SHARE
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
                    "anchor_correlation_ge_0_80_share": (
                        document[
                            "anchor_correlation_ge_0_80_share"
                        ]
                    ),
                    "anchor_correlation_ge_0_95_count": (
                        document[
                            "anchor_correlation_ge_0_95_count"
                        ]
                    ),
                    "price_median_correlation": (
                        document[
                            "price_median_correlation"
                        ]
                    ),
                    "price_correlation_ge_0_80_count": (
                        document[
                            "price_correlation_ge_0_80_count"
                        ]
                    ),
                    "price_correlation_ge_0_95_count": (
                        document[
                            "price_correlation_ge_0_95_count"
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
                "model_loaded": (
                    False
                ),
                "model_trained": (
                    False
                ),
                "model_artifacts_written": (
                    False
                ),
                "frozen_dataset_mutated": (
                    False
                ),
                "frozen_manifest_mutated": (
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
                "mapped_rows_deduplicated": (
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
                "if_nonzero_feature_offset_confirmed": (
                    "AUDIT_FROZEN_FEATURE_AVAILABILITY_SEMANTICS_"
                    "THEN_RERUN_MAPPED_DOMAIN_SHIFT_WITH_CONFIRMED_SHIFT"
                ),
                "if_zero_lag_confirmed": (
                    "AUDIT_FEATURE_FORMULA_AND_RAW_INPUT_PROVENANCE"
                ),
                "if_feature_lag_unresolved": (
                    "AUDIT_FEATURE_FORMULA_AND_RAW_INPUT_PROVENANCE"
                ),
                "broker_sensitive_features_excluded_from_lag_selection": (
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
                        "XAUUSD_CURRENT_BROKER_M5_"
                        "FEATURE_AVAILABILITY_LAG_DIAGNOSTIC_FAILED"
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