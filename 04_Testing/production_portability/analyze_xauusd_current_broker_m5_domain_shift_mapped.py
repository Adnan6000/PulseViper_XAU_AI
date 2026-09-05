from __future__ import annotations

import importlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping

import MetaTrader5 as mt5
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


ANALYSIS_VERSION = (
    "XAUUSD_CURRENT_BROKER_M5_DOMAIN_SHIFT_MAPPED_V4"
)

BASE_AUDIT_MODULE = (
    "04_Testing."
    "analyze_xauusd_current_broker_m5_domain_shift"
)


M5_SECONDS = 300

OFFSET_MINUS_3H_SECONDS = -3 * 60 * 60
OFFSET_MINUS_2H_SECONDS = -2 * 60 * 60

FEATURE_AVAILABILITY_SHIFT_SECONDS = M5_SECONDS


FALL_2025_SOURCE_BOUNDARY = pd.Timestamp(
    "2025-11-03T01:05:00Z"
)

SPRING_2026_SOURCE_BOUNDARY = pd.Timestamp(
    "2026-03-09T01:00:00Z"
)


MIN_MAPPING_PRICE_MEDIAN_CORRELATION = 0.80
MIN_MAPPING_PRICE_STRONG_CORRELATION_SHARE = 0.60
MIN_MAPPING_OVERLAP_ROWS = 5000


base: Any = importlib.import_module(
    BASE_AUDIT_MODULE
)


def _require(
    condition: bool,
    reason: str,
) -> None:
    if not condition:
        raise RuntimeError(reason)


def _safe_float(
    value: Any,
) -> float | None:
    try:
        result = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return None

    if not math.isfinite(result):
        return None

    return result


def _coerce_int(
    value: Any,
) -> int:
    try:
        return int(value)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise RuntimeError(
            f"INTEGER_COERCION_FAILED:{value!r}"
        ) from exc


def _validate_mapping_contract() -> None:
    _require(
        FALL_2025_SOURCE_BOUNDARY
        <
        SPRING_2026_SOURCE_BOUNDARY,
        "INVALID_INTRADAY_BOUNDARY_ORDER",
    )

    _require(
        FALL_2025_SOURCE_BOUNDARY
        ==
        pd.Timestamp(
            "2025-11-03T01:05:00Z"
        ),
        (
            "FALL_2025_SOURCE_BOUNDARY_CHANGED:"
            f"{FALL_2025_SOURCE_BOUNDARY}"
        ),
    )

    _require(
        SPRING_2026_SOURCE_BOUNDARY
        ==
        pd.Timestamp(
            "2026-03-09T01:00:00Z"
        ),
        (
            "SPRING_2026_SOURCE_BOUNDARY_CHANGED:"
            f"{SPRING_2026_SOURCE_BOUNDARY}"
        ),
    )

    _require(
        FEATURE_AVAILABILITY_SHIFT_SECONDS
        ==
        M5_SECONDS,
        (
            "FEATURE_AVAILABILITY_SHIFT_CHANGED:"
            f"{FEATURE_AVAILABILITY_SHIFT_SECONDS}"
        ),
    )


def _mapping_contract() -> dict[str, Any]:
    return {
        "version": (
            "XAUUSD_RESEARCH_BROKER_TIME_MAPPING_V2"
        ),
        "scope": "RESEARCH_ONLY",
        "canonical_symbol": "XAUUSD",
        "basis": (
            "TRAIN_ONLY_RAW_M5_CROSS_BROKER_ALIGNMENT_"
            "PLUS_FROZEN_EXNESS_FEATURE_REPLAY"
        ),
        "source_time_semantics": (
            "CURRENT_BROKER_MT5_BAR_TIME"
        ),
        "market_bar_time_semantics": (
            "FROZEN_REFERENCE_MARKET_BAR_TIME"
        ),
        "decision_time_semantics": (
            "FROZEN_REFERENCE_MARKET_BAR_TIME_PLUS_300_SECONDS"
        ),
        "feature_availability_shift_seconds": (
            FEATURE_AVAILABILITY_SHIFT_SECONDS
        ),
        "feature_availability_shift_m5_bars": 1.0,
        "clock_regimes": [
            {
                "source_time_before": (
                    FALL_2025_SOURCE_BOUNDARY.isoformat()
                ),
                "clock_offset_seconds": (
                    OFFSET_MINUS_3H_SECONDS
                ),
                "clock_offset_hours": -3.0,
            },
            {
                "source_time_from": (
                    FALL_2025_SOURCE_BOUNDARY.isoformat()
                ),
                "source_time_before": (
                    SPRING_2026_SOURCE_BOUNDARY.isoformat()
                ),
                "clock_offset_seconds": (
                    OFFSET_MINUS_2H_SECONDS
                ),
                "clock_offset_hours": -2.0,
            },
            {
                "source_time_from": (
                    SPRING_2026_SOURCE_BOUNDARY.isoformat()
                ),
                "clock_offset_seconds": (
                    OFFSET_MINUS_3H_SECONDS
                ),
                "clock_offset_hours": -3.0,
            },
        ],
        "clock_transition_provenance": [
            {
                "transition_id": "FALL_2025",
                "source_boundary": (
                    FALL_2025_SOURCE_BOUNDARY.isoformat()
                ),
                "old_offset_seconds": (
                    OFFSET_MINUS_3H_SECONDS
                ),
                "new_offset_seconds": (
                    OFFSET_MINUS_2H_SECONDS
                ),
                "intraday_alignment_score": (
                    0.9837686343525152
                ),
                "intraday_body_correlation": (
                    0.9980837201030263
                ),
                "intraday_close_delta_correlation": (
                    0.9986452115213432
                ),
                "intraday_direction_agreement": (
                    0.9805097451274363
                ),
                "intraday_range_correlation": (
                    0.9773261155308184
                ),
                "intraday_duplicate_mapped_rows": 0,
            },
            {
                "transition_id": "SPRING_2026",
                "source_boundary": (
                    SPRING_2026_SOURCE_BOUNDARY.isoformat()
                ),
                "old_offset_seconds": (
                    OFFSET_MINUS_2H_SECONDS
                ),
                "new_offset_seconds": (
                    OFFSET_MINUS_3H_SECONDS
                ),
                "intraday_alignment_score": (
                    0.9892223243803562
                ),
                "intraday_body_correlation": (
                    0.9975438141590512
                ),
                "intraday_close_delta_correlation": (
                    0.9990767651051665
                ),
                "intraday_direction_agreement": (
                    0.9855907780979827
                ),
                "intraday_range_correlation": (
                    0.9890871620612414
                ),
                "intraday_duplicate_mapped_rows": 0,
            },
        ],
        "feature_availability_provenance": {
            "diagnostic_version": (
                "XAUUSD_FROZEN_M5_"
                "FEATURE_AVAILABILITY_SEMANTICS_V1"
            ),
            "source": (
                "EXACT_IMMUTABLE_FROZEN_EXNESS_M5_REPLAY"
            ),
            "selected_shift_seconds": 300,
            "selected_shift_m5_bars": 1.0,
            "selected_overlap_rows": 69966,
            "selected_anchor_median_correlation": 1.0,
            "selected_price_median_correlation": 1.0,
            "selected_anchor_share_ge_0_95": 1.0,
            "zero_lag_anchor_median_correlation": (
                0.41338668873017803
            ),
            "zero_lag_price_median_correlation": (
                0.7662438491488106
            ),
            "derived_from_validation": False,
            "derived_from_test": False,
        },
        "source_boundaries_frozen_from_train_only_diagnostic": (
            True
        ),
        "feature_availability_frozen_from_train_only_replay": (
            True
        ),
        "mapped_rows_deduplicated": False,
        "duplicate_mapped_times_allowed": False,
        "broker_sensitive_features_normalized": False,
        "live_runtime_mapping_authorized": False,
    }


def _research_clock_offset_seconds(
    source_broker_time: pd.Timestamp,
) -> int:
    timestamp = pd.Timestamp(
        source_broker_time
    )

    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize(
            "UTC"
        )
    else:
        timestamp = timestamp.tz_convert(
            "UTC"
        )

    if (
        timestamp
        <
        FALL_2025_SOURCE_BOUNDARY
    ):
        return OFFSET_MINUS_3H_SECONDS

    if (
        timestamp
        <
        SPRING_2026_SOURCE_BOUNDARY
    ):
        return OFFSET_MINUS_2H_SECONDS

    return OFFSET_MINUS_3H_SECONDS


def _apply_research_clock_mapping(
    frame: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:
    _require(
        "decision_time"
        in frame.columns,
        "CURRENT_FRAME_DECISION_TIME_MISSING",
    )

    mapped = frame.copy()

    mapped[
        "source_broker_time"
    ] = pd.to_datetime(
        mapped[
            "decision_time"
        ],
        utc=True,
        errors="raise",
    )

    mapped[
        "research_clock_offset_seconds"
    ] = [
        _research_clock_offset_seconds(
            pd.Timestamp(value)
        )
        for value
        in mapped[
            "source_broker_time"
        ]
    ]

    mapped[
        "market_bar_time"
    ] = (
        mapped[
            "source_broker_time"
        ]
        +
        pd.to_timedelta(
            mapped[
                "research_clock_offset_seconds"
            ],
            unit="s",
        )
    )

    duplicate_count = int(
        mapped[
            "market_bar_time"
        ]
        .duplicated(
            keep=False
        )
        .sum()
    )

    _require(
        duplicate_count == 0,
        (
            "MAPPED_MARKET_BAR_TIME_DUPLICATES:"
            f"{duplicate_count}"
        ),
    )

    _require(
        not bool(
            mapped[
                "market_bar_time"
            ]
            .isna()
            .any()
        ),
        "MAPPED_MARKET_BAR_TIME_NULLS",
    )

    mapped = (
        mapped
        .sort_values(
            "market_bar_time"
        )
        .reset_index(
            drop=True
        )
    )

    _require(
        bool(
            mapped[
                "market_bar_time"
            ]
            .is_monotonic_increasing
        ),
        "MAPPED_MARKET_BAR_TIME_NOT_MONOTONIC",
    )

    offset_counts = (
        mapped[
            "research_clock_offset_seconds"
        ]
        .value_counts()
        .sort_index()
    )

    regime_counts: dict[
        str,
        int,
    ] = {}

    for (
        offset_value,
        count_value,
    ) in offset_counts.items():
        regime_counts[
            str(
                _coerce_int(
                    offset_value
                )
            )
        ] = _coerce_int(
            count_value
        )

    source_start = pd.Timestamp(
        mapped[
            "source_broker_time"
        ].min()
    )

    source_end = pd.Timestamp(
        mapped[
            "source_broker_time"
        ].max()
    )

    market_start = pd.Timestamp(
        mapped[
            "market_bar_time"
        ].min()
    )

    market_end = pd.Timestamp(
        mapped[
            "market_bar_time"
        ].max()
    )

    return (
        mapped,
        {
            "mapping_applied": True,
            "mapping_scope": "RESEARCH_ONLY",
            "source_time_column": (
                "source_broker_time"
            ),
            "market_bar_time_column": (
                "market_bar_time"
            ),
            "clock_offset_column": (
                "research_clock_offset_seconds"
            ),
            "clock_offset_row_counts": (
                regime_counts
            ),
            "duplicate_market_bar_time_rows": (
                duplicate_count
            ),
            "mapped_rows_deduplicated": False,
            "source_time_start": (
                source_start.isoformat()
            ),
            "source_time_end": (
                source_end.isoformat()
            ),
            "market_bar_time_start": (
                market_start.isoformat()
            ),
            "market_bar_time_end": (
                market_end.isoformat()
            ),
            "fall_2025_source_boundary": (
                FALL_2025_SOURCE_BOUNDARY.isoformat()
            ),
            "spring_2026_source_boundary": (
                SPRING_2026_SOURCE_BOUNDARY.isoformat()
            ),
        },
    )


def _apply_feature_availability_semantics(
    frame: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:
    _require(
        "market_bar_time"
        in frame.columns,
        "MARKET_BAR_TIME_MISSING",
    )

    shifted = frame.copy()

    shifted[
        "decision_time"
    ] = (
        pd.to_datetime(
            shifted[
                "market_bar_time"
            ],
            utc=True,
            errors="raise",
        )
        +
        pd.to_timedelta(
            FEATURE_AVAILABILITY_SHIFT_SECONDS,
            unit="s",
        )
    )

    duplicate_count = int(
        shifted[
            "decision_time"
        ]
        .duplicated(
            keep=False
        )
        .sum()
    )

    _require(
        duplicate_count == 0,
        (
            "FEATURE_AVAILABILITY_DECISION_TIME_DUPLICATES:"
            f"{duplicate_count}"
        ),
    )

    _require(
        not bool(
            shifted[
                "decision_time"
            ]
            .isna()
            .any()
        ),
        "FEATURE_AVAILABILITY_DECISION_TIME_NULLS",
    )

    shifted = (
        shifted
        .sort_values(
            "decision_time"
        )
        .reset_index(
            drop=True
        )
    )

    _require(
        bool(
            shifted[
                "decision_time"
            ]
            .is_monotonic_increasing
        ),
        "FEATURE_AVAILABILITY_DECISION_TIME_NOT_MONOTONIC",
    )

    market_start = pd.Timestamp(
        shifted[
            "market_bar_time"
        ].min()
    )

    market_end = pd.Timestamp(
        shifted[
            "market_bar_time"
        ].max()
    )

    decision_start = pd.Timestamp(
        shifted[
            "decision_time"
        ].min()
    )

    decision_end = pd.Timestamp(
        shifted[
            "decision_time"
        ].max()
    )

    return (
        shifted,
        {
            "availability_shift_applied": True,
            "availability_shift_seconds": (
                FEATURE_AVAILABILITY_SHIFT_SECONDS
            ),
            "availability_shift_m5_bars": 1.0,
            "basis": (
                "EXACT_FROZEN_EXNESS_M5_FEATURE_REPLAY"
            ),
            "market_bar_time_column": (
                "market_bar_time"
            ),
            "decision_time_column": (
                "decision_time"
            ),
            "duplicate_decision_time_rows": (
                duplicate_count
            ),
            "rows_deduplicated": False,
            "market_bar_time_start": (
                market_start.isoformat()
            ),
            "market_bar_time_end": (
                market_end.isoformat()
            ),
            "decision_time_start": (
                decision_start.isoformat()
            ),
            "decision_time_end": (
                decision_end.isoformat()
            ),
            "broker_sensitive_fields_shifted_with_row": (
                True
            ),
            "broker_sensitive_fields_normalized": (
                False
            ),
        },
    )


def _price_mapping_validation(
    summary: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:
    median_correlation = _safe_float(
        summary.get(
            "price_candle_median_paired_correlation"
        )
    )

    price_feature_count = _coerce_int(
        summary.get(
            "price_candle_feature_count",
            0,
        )
    )

    correlated_feature_count = _coerce_int(
        summary.get(
            "price_candle_features_with_correlation",
            0,
        )
    )

    strong_count = _coerce_int(
        summary.get(
            "price_candle_strong_correlation_count",
            0,
        )
    )

    strong_share = (
        float(
            strong_count
            /
            correlated_feature_count
        )
        if correlated_feature_count > 0
        else None
    )

    passed = bool(
        median_correlation
        is not None
        and
        median_correlation
        >=
        MIN_MAPPING_PRICE_MEDIAN_CORRELATION
        and
        correlated_feature_count > 0
        and
        strong_share
        is not None
        and
        strong_share
        >=
        MIN_MAPPING_PRICE_STRONG_CORRELATION_SHARE
    )

    return {
        "passed": passed,
        "median_price_feature_correlation": (
            median_correlation
        ),
        "minimum_median_price_feature_correlation": (
            MIN_MAPPING_PRICE_MEDIAN_CORRELATION
        ),
        "price_feature_count": (
            price_feature_count
        ),
        "price_features_with_correlation": (
            correlated_feature_count
        ),
        "strong_price_feature_count": (
            strong_count
        ),
        "strong_price_feature_share_of_correlated_features": (
            strong_share
        ),
        "minimum_strong_price_feature_share": (
            MIN_MAPPING_PRICE_STRONG_CORRELATION_SHARE
        ),
        "feature_availability_shift_seconds": (
            FEATURE_AVAILABILITY_SHIFT_SECONDS
        ),
    }


def _mapped_decision(
    *,
    overlap_rows: int,
    summary: Mapping[
        str,
        Any,
    ],
    mapping_validation: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:
    if (
        overlap_rows
        <
        MIN_MAPPING_OVERLAP_ROWS
    ):
        return {
            "classification": (
                "INSUFFICIENT_MAPPED_OVERLAP"
            ),
            "reason": (
                "TOO_FEW_SAME_MARKET_BAR_ROWS_AFTER_"
                "CLOCK_AND_FEATURE_AVAILABILITY_MAPPING"
            ),
            "scope": "M5_PRELIMINARY",
            "portable_decision": "UNRESOLVED",
            "time_mapping_validated": False,
            "feature_availability_validated": True,
            "full_333_portability_claimed": False,
        }

    if not bool(
        mapping_validation.get(
            "passed",
            False,
        )
    ):
        return {
            "classification": (
                "MAPPED_FEATURE_ALIGNMENT_NOT_CONFIRMED"
            ),
            "reason": (
                "CONFIRMED_CLOCK_AND_PLUS_300_SECOND_"
                "FEATURE_AVAILABILITY_MAPPING_DID_NOT_RESTORE_"
                "SUFFICIENT_PRICE_FEATURE_CORRESPONDENCE"
            ),
            "scope": "M5_PRELIMINARY",
            "portable_decision": "UNRESOLVED",
            "time_mapping_validated": False,
            "feature_availability_validated": True,
            "full_333_portability_claimed": False,
        }

    base_classification = (
        base
        ._classification(
            overlap_rows=overlap_rows,
            summary=summary,
        )
    )

    original = str(
        base_classification.get(
            "classification",
            "",
        )
    )

    if (
        original
        ==
        "M5_PRELIMINARY_PORTABLE"
    ):
        portable_decision = "PORTABLE"

    elif (
        original
        ==
        "NORMALIZATION_REQUIRED"
    ):
        portable_decision = (
            "NORMALIZATION_REQUIRED"
        )

    elif (
        original
        ==
        "RETRAIN_OR_RECALIBRATE_REQUIRED"
    ):
        portable_decision = (
            "BROKER_SPECIFIC_RETRAINING_REQUIRED"
        )

    else:
        portable_decision = "UNRESOLVED"

    return {
        **base_classification,
        "portable_decision": portable_decision,
        "time_mapping_validated": True,
        "feature_availability_validated": True,
        "feature_availability_shift_seconds": (
            FEATURE_AVAILABILITY_SHIFT_SECONDS
        ),
        "full_333_portability_claimed": False,
    }


def run_analysis() -> dict[str, Any]:
    _validate_mapping_contract()

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

    comparison_features = (
        base
        ._comparison_feature_names(
            generator_base_features
        )
    )

    manifest_feature_columns_raw = (
        manifest.get(
            "feature_columns"
        )
    )

    if not isinstance(
        manifest_feature_columns_raw,
        list,
    ):
        raise RuntimeError(
            "TRAINING_MANIFEST_FEATURE_COLUMNS_MISSING"
        )

    manifest_feature_columns = {
        str(value)
        for value
        in manifest_feature_columns_raw
    }

    missing_features = sorted(
        set(comparison_features)
        -
        manifest_feature_columns
    )

    _require(
        not missing_features,
        (
            "MAPPED_M5_FEATURES_NOT_IN_FROZEN_CONTRACT:"
            f"{missing_features}"
        ),
    )

    frozen_train = (
        base
        ._load_frozen_train_only(
            dataset_path,
            comparison_features,
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

        resolution = (
            broker_snapshot[
                "resolution"
            ]
        )

        broker_symbol = str(
            resolution[
                "broker_symbol"
            ]
        )

        broker_identity = (
            broker_snapshot[
                "broker_identity"
            ]
        )

        broker_server = str(
            broker_identity.get(
                "server",
                "",
            )
        )

        symbol_info = mt5.symbol_info(
            broker_symbol
        )

        _require(
            symbol_info is not None,
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
            selected = mt5.symbol_select(
                broker_symbol,
                True,
            )

            _require(
                bool(selected),
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
                days=base.HISTORY_WARMUP_DAYS
            )
            -
            pd.Timedelta(
                hours=4
            )
            -
            pd.Timedelta(
                seconds=(
                    FEATURE_AVAILABILITY_SHIFT_SECONDS
                )
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
            +
            pd.Timedelta(
                seconds=(
                    FEATURE_AVAILABILITY_SHIFT_SECONDS
                )
            )
        )

        rates = mt5.copy_rates_range(
            broker_symbol,
            mt5.TIMEFRAME_M5,
            fetch_start.to_pydatetime(),
            fetch_end.to_pydatetime(),
        )

        raw_m5 = (
            base
            ._mt5_rates_frame(
                rates
            )
        )

        (
            current_generated,
            generation_meta,
        ) = (
            base
            ._build_current_m5_comparison_frame(
                raw_m5,
                generator_base_features,
            )
        )

        generated_columns = {
            str(column)
            for column
            in current_generated.columns
        }

        missing_generated_features = sorted(
            set(comparison_features)
            -
            generated_columns
        )

        _require(
            not missing_generated_features,
            (
                "GENERATED_COMPARISON_FEATURES_MISSING:"
                f"{missing_generated_features}"
            ),
        )

        (
            current_clock_mapped,
            clock_mapping_meta,
        ) = (
            _apply_research_clock_mapping(
                current_generated
            )
        )

        (
            current_mapped,
            availability_meta,
        ) = (
            _apply_feature_availability_semantics(
                current_clock_mapped
            )
        )

        current_mapped = (
            current_mapped.loc[
                (
                    current_mapped[
                        "decision_time"
                    ]
                    >=
                    train_start
                )
                &
                (
                    current_mapped[
                        "decision_time"
                    ]
                    <=
                    train_end
                )
            ]
            .copy()
            .reset_index(
                drop=True
            )
        )

        _require(
            not current_mapped.empty,
            "CURRENT_MAPPED_TRAIN_WINDOW_EMPTY",
        )

        _require(
            not bool(
                current_mapped[
                    "decision_time"
                ]
                .duplicated()
                .any()
            ),
            (
                "MAPPED_TRAIN_WINDOW_"
                "DECISION_TIME_DUPLICATES"
            ),
        )

        frozen_projection = (
            frozen_train[
                [
                    "decision_time",
                    *comparison_features,
                ]
            ]
            .rename(
                columns={
                    feature: (
                        f"{feature}_frozen"
                    )
                    for feature
                    in comparison_features
                }
            )
        )

        current_projection = (
            current_mapped[
                [
                    "decision_time",
                    *comparison_features,
                ]
            ]
            .rename(
                columns={
                    feature: (
                        f"{feature}_current"
                    )
                    for feature
                    in comparison_features
                }
            )
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
            len(paired)
        )

        overlap_fraction = float(
            overlap_rows
            /
            len(frozen_train)
        )

        comparisons = [
            base
            ._feature_comparison(
                paired,
                feature,
            )
            for feature
            in comparison_features
        ]

        summary = (
            base
            ._summarize_comparisons(
                comparisons
            )
        )

        mapping_validation = (
            _price_mapping_validation(
                summary
            )
        )

        decision = (
            _mapped_decision(
                overlap_rows=overlap_rows,
                summary=summary,
                mapping_validation=(
                    mapping_validation
                ),
            )
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
                "DOMAIN_SHIFT_MAPPED"
            ),
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "research_scope": (
                "M5_SAME_MARKET_BAR_DOMAIN_SHIFT_WITH_"
                "COLLISION_FREE_SEASONAL_CLOCK_MAPPING_"
                "AND_CONFIRMED_PLUS_300_SECOND_"
                "FEATURE_AVAILABILITY_SEMANTICS"
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
                "identity": (
                    base
                    ._safe_frozen_identity(
                        manifest
                    )
                ),
                "rows_loaded": int(
                    len(frozen_train)
                ),
                "split_loaded": "TRAIN_ONLY",
                "time_start": (
                    train_start.isoformat()
                ),
                "time_end": (
                    train_end.isoformat()
                ),
            },
            "current_broker": {
                "canonical_symbol": "XAUUSD",
                "broker_symbol": broker_symbol,
                "broker_server": broker_server,
                "contract_fingerprint": (
                    broker_snapshot[
                        "contract_fingerprint"
                    ]
                ),
                "historical_m5_rows_fetched": int(
                    len(raw_m5)
                ),
                "history_time_start": (
                    current_history_start
                    .isoformat()
                ),
                "history_time_end": (
                    current_history_end
                    .isoformat()
                ),
            },
            "confirmed_time_mapping": {
                "contract": (
                    _mapping_contract()
                ),
                "clock_mapping_application": (
                    clock_mapping_meta
                ),
                "feature_availability_application": (
                    availability_meta
                ),
                "provenance": {
                    "daily_transition_status": (
                        "SEASONAL_CLOCK_"
                        "TRANSITION_DATES_CONFIRMED"
                    ),
                    "intraday_transition_status": (
                        "COLLISION_FREE_INTRADAY_"
                        "TRANSITION_BOUNDARIES_CONFIRMED"
                    ),
                    "feature_availability_status": (
                        "FROZEN_M5_FEATURE_AVAILABILITY_"
                        "PLUS_ONE_BAR_CONFIRMED"
                    ),
                    "derived_from_train_only_raw_alignment": (
                        True
                    ),
                    "derived_from_frozen_train_only_replay": (
                        True
                    ),
                    "derived_from_validation": False,
                    "derived_from_test": False,
                    "mapped_rows_deduplicated": False,
                    "live_runtime_rule_claimed": False,
                },
            },
            "feature_contract": {
                "exact_existing_base_generator_used": (
                    True
                ),
                "generator_base_feature_count": int(
                    len(
                        generator_base_features
                    )
                ),
                "broker_sensitive_feature_count": int(
                    len(
                        base.BROKER_SENSITIVE_FEATURES
                    )
                ),
                "comparison_feature_count": int(
                    len(comparison_features)
                ),
                "broker_sensitive_features": list(
                    base.BROKER_SENSITIVE_FEATURES
                ),
                "feature_availability_shift_seconds": (
                    FEATURE_AVAILABILITY_SHIFT_SECONDS
                ),
                "feature_availability_shift_m5_bars": (
                    1.0
                ),
                "broker_sensitive_features_normalized": (
                    False
                ),
                "feature_generation": (
                    generation_meta
                ),
            },
            "same_market_bar_overlap": {
                "rows": overlap_rows,
                "frozen_train_rows": int(
                    len(frozen_train)
                ),
                "fraction_of_frozen_train": (
                    overlap_fraction
                ),
                "minimum_required_rows": (
                    MIN_MAPPING_OVERLAP_ROWS
                ),
            },
            "mapping_validation": (
                mapping_validation
            ),
            "summary": summary,
            "classification": decision,
            "feature_comparisons": comparisons,
            "thresholds": {
                "mapping_minimum_median_price_correlation": (
                    MIN_MAPPING_PRICE_MEDIAN_CORRELATION
                ),
                "mapping_minimum_strong_price_correlation_share": (
                    MIN_MAPPING_PRICE_STRONG_CORRELATION_SHARE
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
                "price_correlation_warning": (
                    base
                    .PRICE_CORRELATION_WARNING_THRESHOLD
                ),
                "price_correlation_strong": (
                    base
                    .PRICE_CORRELATION_STRONG_THRESHOLD
                ),
            },
            "scientific_policy": {
                "frozen_dataset_mutated": False,
                "frozen_manifest_mutated": False,
                "train_loaded": True,
                "train_rows_expected": (
                    base.EXPECTED_TRAIN_ROWS
                ),
                "validation_loaded": False,
                "validation_evaluated": False,
                "test_loaded": False,
                "test_evaluated": False,
                "labels_used": False,
                "model_loaded": False,
                "model_trained": False,
                "model_artifacts_written": False,
                "mt5_used": True,
                "mt5_history_read_only": True,
                "orders_sent": False,
                "positions_modified": False,
                "risk_engine_modified": False,
                "sizing_modified": False,
                "execution_integration_modified": False,
                "mapped_rows_deduplicated": False,
                "broker_sensitive_features_normalized": (
                    False
                ),
                "live_authorized": False,
                "account_login_emitted": False,
                "account_holder_name_emitted": False,
                "account_scope_identifier_emitted": False,
            },
            "next_decision_contract": {
                "if_portable": (
                    "EXPAND_TO_FULL_MTF_PLUS_DOMAIN_FEATURE_AUDIT"
                ),
                "if_normalization_required": (
                    "EXPAND_TO_FULL_MTF_PLUS_DOMAIN_FEATURE_AUDIT_"
                    "THEN_DESIGN_NEW_PORTABLE_FEATURE_CONTRACT_"
                    "WITHOUT_MUTATING_V3"
                ),
                "if_broker_specific_retraining_required": (
                    "EXPAND_TO_FULL_MTF_DOMAIN_AUDIT_BEFORE_"
                    "ANY_RETRAINING_DECISION"
                ),
                "if_mapping_validation_fails": (
                    "STOP_AND_AUDIT_REMAINING_FEATURE_PROVENANCE"
                ),
                "broker_sensitive_spread_and_tick_volume_issue": (
                    "MUST_BE_DECIDED_SEPARATELY_FROM_PRICE_FEATURES"
                ),
                "test_holdout_remains_untouched": True,
                "full_333_portability_not_decided": True,
            },
            "live_authorized": False,
        }

    finally:
        mt5.shutdown()


def main() -> int:
    try:
        result = run_analysis()

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
                        "DOMAIN_SHIFT_MAPPED_FAILED"
                    ),
                    "analysis_version": (
                        ANALYSIS_VERSION
                    ),
                    "error_type": (
                        type(exc).__name__
                    ),
                    "error": str(exc),
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