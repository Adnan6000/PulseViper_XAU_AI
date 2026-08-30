from __future__ import annotations

import importlib
import json
import math
import sys
from collections import Counter
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
    "XAUUSD_CURRENT_BROKER_H1_SESSION_HOUR_RESIDUAL_V1"
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


TIMEFRAME_H1 = "H1"
TIMEFRAME_D1 = "D1"


CONFIRMED_D1_CLOSE_HOUR_UTC = 0
CONFIRMED_D1_LABEL_DAY_SHIFT = 0


MIN_GLOBAL_H1_PAIRED_ROWS = 3000

MIN_HOUR_PAIRED_ROWS = 100

MIN_HOUR_COVERAGE = 0.90


H1_STRONG_BODY_CORRELATION = 0.95

H1_STRONG_CLOSE_DELTA_CORRELATION = 0.95

H1_STRONG_RANGE_CORRELATION = 0.95

H1_STRONG_DIRECTION_AGREEMENT = 0.90


D1_RAW_CONFIRMED_BODY_CORRELATION = 0.95

D1_RAW_CONFIRMED_CLOSE_DELTA_CORRELATION = 0.95

D1_RAW_CONFIRMED_RANGE_CORRELATION = 0.95

D1_RAW_CONFIRMED_DIRECTION_AGREEMENT = 0.90


MAX_LOCALIZED_WEAK_HOURS = 4


CANONICAL_DATETIME_DTYPE = (
    "datetime64[ns, UTC]"
)


RAW_PRICE_COLUMNS = (
    "open",
    "high",
    "low",
    "close",
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

    return (
        result
    )


def _clock_map_current_h1(
    raw_h1: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

    required = {
        "time",
        *RAW_PRICE_COLUMNS,
    }

    missing = sorted(
        required
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
        clock_meta,
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
            **clock_meta,
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


def _pair_h1(
    frozen_h1: pd.DataFrame,
    current_h1: pd.DataFrame,
) -> pd.DataFrame:

    frozen = (
        frozen_h1[
            [
                "time",
                *RAW_PRICE_COLUMNS,
            ]
        ]
        .rename(
            columns={
                "open": (
                    "open_frozen"
                ),
                "high": (
                    "high_frozen"
                ),
                "low": (
                    "low_frozen"
                ),
                "close": (
                    "close_frozen"
                ),
            }
        )
        .copy()
    )

    current = (
        current_h1[
            [
                "time",
                *RAW_PRICE_COLUMNS,
            ]
        ]
        .rename(
            columns={
                "open": (
                    "open_synthetic"
                ),
                "high": (
                    "high_synthetic"
                ),
                "low": (
                    "low_synthetic"
                ),
                "close": (
                    "close_synthetic"
                ),
            }
        )
        .copy()
    )

    frozen[
        "time"
    ] = (
        _canonical_time(
            frozen[
                "time"
            ]
        )
    )

    current[
        "time"
    ] = (
        _canonical_time(
            current[
                "time"
            ]
        )
    )

    paired = (
        frozen
        .merge(
            current,
            on="time",
            how="inner",
            validate="one_to_one",
        )
        .sort_values(
            "time"
        )
        .reset_index(
            drop=True
        )
    )

    return (
        paired
    )


def _metrics_from_h1_pair(
    paired: pd.DataFrame,
) -> dict[str, Any]:

    proxy = (
        paired.rename(
            columns={
                "time": (
                    "comparison_date"
                ),
            }
        )
        .copy()
    )

    proxy[
        "frozen_time"
    ] = (
        proxy[
            "comparison_date"
        ]
    )

    proxy[
        "synthetic_bar_time"
    ] = (
        proxy[
            "comparison_date"
        ]
    )

    proxy[
        "session_close"
    ] = (
        proxy[
            "comparison_date"
        ]
        +
        pd.Timedelta(
            hours=1
        )
    )

    proxy[
        "h1_bar_count"
    ] = 1

    return (
        source
        ._alignment_metrics(
            proxy
        )
    )


def _hour_document(
    *,
    hour: int,
    frozen_h1_window: pd.DataFrame,
    current_h1_window: pd.DataFrame,
    paired_h1: pd.DataFrame,
) -> dict[str, Any]:

    frozen_hour = (
        frozen_h1_window.loc[
            frozen_h1_window[
                "time"
            ]
            .dt
            .hour
            ==
            hour
        ]
        .copy()
    )

    current_hour = (
        current_h1_window.loc[
            current_h1_window[
                "time"
            ]
            .dt
            .hour
            ==
            hour
        ]
        .copy()
    )

    paired_hour = (
        paired_h1.loc[
            paired_h1[
                "time"
            ]
            .dt
            .hour
            ==
            hour
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    frozen_rows = int(
        len(
            frozen_hour
        )
    )

    current_rows = int(
        len(
            current_hour
        )
    )

    paired_rows = int(
        len(
            paired_hour
        )
    )

    coverage_vs_frozen = (
        float(
            paired_rows
            /
            frozen_rows
        )
        if (
            frozen_rows
            >
            0
        )
        else None
    )

    metrics = (
        _metrics_from_h1_pair(
            paired_hour
        )
    )

    body_correlation = (
        _safe_float(
            metrics.get(
                "body_correlation"
            )
        )
    )

    close_delta_correlation = (
        _safe_float(
            metrics.get(
                "close_delta_correlation"
            )
        )
    )

    range_correlation = (
        _safe_float(
            metrics.get(
                "range_correlation"
            )
        )
    )

    direction_agreement = (
        _safe_float(
            metrics.get(
                "direction_agreement"
            )
        )
    )

    sufficient_rows = bool(
        paired_rows
        >=
        MIN_HOUR_PAIRED_ROWS
    )

    coverage_ok = bool(
        coverage_vs_frozen
        is not None
        and
        coverage_vs_frozen
        >=
        MIN_HOUR_COVERAGE
    )

    strong_structure = bool(
        sufficient_rows
        and
        coverage_ok
        and
        body_correlation
        is not None
        and
        body_correlation
        >=
        H1_STRONG_BODY_CORRELATION
        and
        close_delta_correlation
        is not None
        and
        close_delta_correlation
        >=
        H1_STRONG_CLOSE_DELTA_CORRELATION
        and
        range_correlation
        is not None
        and
        range_correlation
        >=
        H1_STRONG_RANGE_CORRELATION
        and
        direction_agreement
        is not None
        and
        direction_agreement
        >=
        H1_STRONG_DIRECTION_AGREEMENT
    )

    return {
        "canonical_hour_utc": int(
            hour
        ),
        "frozen_rows": (
            frozen_rows
        ),
        "current_rows": (
            current_rows
        ),
        "paired_rows": (
            paired_rows
        ),
        "coverage_vs_frozen": (
            coverage_vs_frozen
        ),
        "sufficient_rows": (
            sufficient_rows
        ),
        "coverage_ok": (
            coverage_ok
        ),
        "strong_structure": (
            strong_structure
        ),
        **metrics,
    }


def _session_bar_count_document(
    frozen_h1: pd.DataFrame,
    current_h1: pd.DataFrame,
) -> dict[str, Any]:

    frozen_synthetic = (
        source
        ._synthetic_d1(
            frozen_h1,
            close_hour=(
                CONFIRMED_D1_CLOSE_HOUR_UTC
            ),
            label_day_shift=(
                CONFIRMED_D1_LABEL_DAY_SHIFT
            ),
        )
    )

    current_synthetic = (
        source
        ._synthetic_d1(
            current_h1,
            close_hour=(
                CONFIRMED_D1_CLOSE_HOUR_UTC
            ),
            label_day_shift=(
                CONFIRMED_D1_LABEL_DAY_SHIFT
            ),
        )
    )

    counts = (
        frozen_synthetic[
            [
                "comparison_date",
                "h1_bar_count",
            ]
        ]
        .rename(
            columns={
                "h1_bar_count": (
                    "frozen_h1_bar_count"
                )
            }
        )
        .merge(
            current_synthetic[
                [
                    "comparison_date",
                    "h1_bar_count",
                ]
            ]
            .rename(
                columns={
                    "h1_bar_count": (
                        "current_h1_bar_count"
                    )
                }
            ),
            on="comparison_date",
            how="inner",
            validate="one_to_one",
        )
    )

    _require(
        not counts.empty,
        "NO_PAIRED_D1_SESSION_BAR_COUNTS",
    )

    equal_mask = (
        counts[
            "frozen_h1_bar_count"
        ]
        ==
        counts[
            "current_h1_bar_count"
        ]
    )

    mismatch = (
        counts.loc[
            ~equal_mask
        ]
        .copy()
    )

    frozen_distribution = (
        Counter(
            int(
                value
            )
            for value
            in frozen_synthetic[
                "h1_bar_count"
            ]
            .tolist()
        )
    )

    current_distribution = (
        Counter(
            int(
                value
            )
            for value
            in current_synthetic[
                "h1_bar_count"
            ]
            .tolist()
        )
    )

    return {
        "paired_session_count": int(
            len(
                counts
            )
        ),
        "equal_bar_count_session_count": int(
            equal_mask.sum()
        ),
        "equal_bar_count_share": float(
            equal_mask.mean()
        ),
        "mismatched_bar_count_session_count": int(
            len(
                mismatch
            )
        ),
        "frozen_bar_count_distribution": {
            str(
                key
            ): int(
                value
            )
            for (
                key,
                value,
            )
            in sorted(
                frozen_distribution.items()
            )
        },
        "current_bar_count_distribution": {
            str(
                key
            ): int(
                value
            )
            for (
                key,
                value,
            )
            in sorted(
                current_distribution.items()
            )
        },
    }


def _current_d1_raw_alignment(
    *,
    frozen_d1: pd.DataFrame,
    current_h1: pd.DataFrame,
) -> dict[str, Any]:

    frozen_d1_for_comparison = (
        source
        ._frozen_d1_for_comparison(
            frozen_d1
        )
    )

    current_synthetic = (
        source
        ._synthetic_d1(
            current_h1,
            close_hour=(
                CONFIRMED_D1_CLOSE_HOUR_UTC
            ),
            label_day_shift=(
                CONFIRMED_D1_LABEL_DAY_SHIFT
            ),
        )
    )

    paired = (
        source
        ._pair_candidate(
            frozen_d1_for_comparison,
            current_synthetic,
        )
    )

    metrics = (
        source
        ._alignment_metrics(
            paired
        )
    )

    body = (
        _safe_float(
            metrics.get(
                "body_correlation"
            )
        )
    )

    close_delta = (
        _safe_float(
            metrics.get(
                "close_delta_correlation"
            )
        )
    )

    candle_range = (
        _safe_float(
            metrics.get(
                "range_correlation"
            )
        )
    )

    direction = (
        _safe_float(
            metrics.get(
                "direction_agreement"
            )
        )
    )

    confirmed = bool(
        body
        is not None
        and
        body
        >=
        D1_RAW_CONFIRMED_BODY_CORRELATION
        and
        close_delta
        is not None
        and
        close_delta
        >=
        D1_RAW_CONFIRMED_CLOSE_DELTA_CORRELATION
        and
        candle_range
        is not None
        and
        candle_range
        >=
        D1_RAW_CONFIRMED_RANGE_CORRELATION
        and
        direction
        is not None
        and
        direction
        >=
        D1_RAW_CONFIRMED_DIRECTION_AGREEMENT
    )

    return {
        **metrics,
        "raw_d1_alignment_confirmed": (
            confirmed
        ),
        "session_close_hour_utc": (
            CONFIRMED_D1_CLOSE_HOUR_UTC
        ),
        "label_day_shift": (
            CONFIRMED_D1_LABEL_DAY_SHIFT
        ),
    }


def _decision(
    *,
    global_h1_metrics: Mapping[
        str,
        Any,
    ],
    hour_documents: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
    d1_raw_alignment: Mapping[
        str,
        Any,
    ],
    session_bar_counts: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    global_paired_rows = int(
        global_h1_metrics.get(
            "paired_rows",
            0,
        )
    )

    weak_hours = [
        int(
            document[
                "canonical_hour_utc"
            ]
        )
        for document
        in hour_documents
        if not bool(
            document.get(
                "strong_structure",
                False,
            )
        )
    ]

    strong_hours = [
        int(
            document[
                "canonical_hour_utc"
            ]
        )
        for document
        in hour_documents
        if bool(
            document.get(
                "strong_structure",
                False,
            )
        )
    ]

    raw_d1_confirmed = bool(
        d1_raw_alignment.get(
            "raw_d1_alignment_confirmed",
            False,
        )
    )

    equal_session_share = (
        _safe_float(
            session_bar_counts.get(
                "equal_bar_count_share"
            )
        )
    )

    if (
        global_paired_rows
        <
        MIN_GLOBAL_H1_PAIRED_ROWS
    ):

        status = (
            "CURRENT_H1_RESIDUAL_INSUFFICIENT_OVERLAP"
        )

        reason = (
            "TOO_FEW_SAME_CANONICAL_H1_ROWS_FOR_"
            "RELIABLE_SESSION_HOUR_DIAGNOSIS"
        )

        next_action = (
            "RESOLVE_CURRENT_BROKER_H1_HISTORY_COVERAGE"
        )

    elif (
        raw_d1_confirmed
    ):

        status = (
            "CURRENT_H1_REAGGREGATED_D1_RAW_ALIGNMENT_CONFIRMED"
        )

        reason = (
            "CONFIRMED_00UTC_H1_REAGGREGATION_RESTORES_"
            "RAW_D1_CANDLE_STRUCTURE_ACROSS_BROKERS"
        )

        next_action = (
            "AUDIT_D1_FEATURE_GENERATION_WARMUP_AND_"
            "LONG_MEMORY_STATE_USING_CONFIRMED_00UTC_RAW_D1"
        )

    elif (
        equal_session_share
        is not None
        and
        equal_session_share
        <
        0.90
    ):

        status = (
            "CURRENT_H1_DAILY_SESSION_COVERAGE_MISMATCH"
        )

        reason = (
            "CURRENT_AND_FROZEN_00UTC_DAILY_SESSIONS_"
            "FREQUENTLY_CONTAIN_DIFFERENT_H1_BAR_COUNTS"
        )

        next_action = (
            "ISOLATE_MISSING_OR_EXTRA_CANONICAL_H1_"
            "SESSION_HOURS_BY_DATE"
        )

    elif (
        len(
            weak_hours
        )
        <=
        MAX_LOCALIZED_WEAK_HOURS
        and
        len(
            strong_hours
        )
        >
        0
    ):

        status = (
            "CURRENT_H1_SESSION_HOUR_RESIDUAL_LOCALIZED"
        )

        reason = (
            "CROSS_BROKER_H1_RAW_MISMATCH_IS_CONCENTRATED_"
            "IN_A_SMALL_NUMBER_OF_CANONICAL_UTC_HOURS"
        )

        next_action = (
            "TRACE_WEAK_HOURS_TO_BROKER_ROLLOVER_"
            "AND_SESSION_GAP_BEHAVIOR"
        )

    else:

        status = (
            "CURRENT_H1_CROSS_BROKER_RAW_RESIDUAL_BROAD"
        )

        reason = (
            "H1_RAW_CANDLE_STRUCTURE_DIFFERS_ACROSS_"
            "MANY_CANONICAL_SESSION_HOURS"
        )

        next_action = (
            "QUANTIFY_H1_RAW_MICROSTRUCTURE_EFFECT_ON_"
            "D1_LONG_MEMORY_FEATURES_BEFORE_PORTABLE_CONTRACT_DESIGN"
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "weak_canonical_hours_utc": (
            weak_hours
        ),
        "weak_hour_count": int(
            len(
                weak_hours
            )
        ),
        "strong_canonical_hours_utc": (
            strong_hours
        ),
        "strong_hour_count": int(
            len(
                strong_hours
            )
        ),
        "raw_d1_alignment_confirmed": (
            raw_d1_confirmed
        ),
        "equal_daily_session_bar_count_share": (
            equal_session_share
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

    training_manifest = (
        base
        ._load_manifest(
            training_manifest_path
        )
    )

    h1_snapshot = (
        source
        ._snapshot_document(
            training_manifest,
            TIMEFRAME_H1,
        )
    )

    d1_snapshot = (
        source
        ._snapshot_document(
            training_manifest,
            TIMEFRAME_D1,
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

    (
        frozen_d1_path,
        frozen_d1_resolution,
    ) = (
        source
        ._resolve_snapshot_file(
            d1_snapshot
        )
    )

    frozen_h1 = (
        source
        ._read_snapshot_frame(
            frozen_h1_path,
            h1_snapshot,
        )
    )

    frozen_d1 = (
        source
        ._read_snapshot_frame(
            frozen_d1_path,
            d1_snapshot,
        )
    )

    frozen_train = (
        base
        ._load_frozen_train_only(
            training_dataset_path,
            [
                "h1_ema20",
                "d1_ema20",
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

    comparison_start = (
        train_start
        .floor(
            "D"
        )
        -
        pd.Timedelta(
            days=3
        )
    )

    comparison_end = (
        train_end
        .ceil(
            "D"
        )
        +
        pd.Timedelta(
            days=3
        )
    )

    frozen_h1_window = (
        frozen_h1.loc[
            (
                frozen_h1[
                    "time"
                ]
                >=
                comparison_start
            )
            &
            (
                frozen_h1[
                    "time"
                ]
                <=
                comparison_end
            )
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    frozen_d1_window = (
        frozen_d1.loc[
            (
                frozen_d1[
                    "time"
                ]
                >=
                comparison_start.floor(
                    "D"
                )
            )
            &
            (
                frozen_d1[
                    "time"
                ]
                <=
                comparison_end.ceil(
                    "D"
                )
            )
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    _require(
        not frozen_h1_window.empty,
        "FROZEN_H1_COMPARISON_WINDOW_EMPTY",
    )

    _require(
        not frozen_d1_window.empty,
        "FROZEN_D1_COMPARISON_WINDOW_EMPTY",
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
            comparison_start
            -
            pd.Timedelta(
                days=7
            )
        )

        fetch_end = (
            comparison_end
            +
            pd.Timedelta(
                days=2
            )
        )

        rates = mt5.copy_rates_range(
            broker_symbol,
            mt5.TIMEFRAME_H1,
            fetch_start.to_pydatetime(),
            fetch_end.to_pydatetime(),
        )

        raw_current_h1 = (
            base
            ._mt5_rates_frame(
                rates
            )
        )

        _require(
            not raw_current_h1.empty,
            "CURRENT_BROKER_H1_EMPTY",
        )

        (
            current_h1,
            current_clock_meta,
        ) = (
            _clock_map_current_h1(
                raw_current_h1
            )
        )

        current_h1_window = (
            current_h1.loc[
                (
                    current_h1[
                        "time"
                    ]
                    >=
                    comparison_start
                )
                &
                (
                    current_h1[
                        "time"
                    ]
                    <=
                    comparison_end
                )
            ]
            .copy()
            .reset_index(
                drop=True
            )
        )

        _require(
            not current_h1_window.empty,
            "CURRENT_CANONICAL_H1_COMPARISON_WINDOW_EMPTY",
        )

        paired_h1 = (
            _pair_h1(
                frozen_h1_window,
                current_h1_window,
            )
        )

        _require(
            len(
                paired_h1
            )
            >=
            MIN_GLOBAL_H1_PAIRED_ROWS,
            (
                "CURRENT_H1_GLOBAL_OVERLAP_TOO_SMALL:"
                f"{len(paired_h1)}"
            ),
        )

        global_h1_metrics = (
            _metrics_from_h1_pair(
                paired_h1
            )
        )

        hour_documents = [
            _hour_document(
                hour=(
                    hour
                ),
                frozen_h1_window=(
                    frozen_h1_window
                ),
                current_h1_window=(
                    current_h1_window
                ),
                paired_h1=(
                    paired_h1
                ),
            )
            for hour
            in range(
                24
            )
        ]

        session_bar_counts = (
            _session_bar_count_document(
                frozen_h1_window,
                current_h1_window,
            )
        )

        d1_raw_alignment = (
            _current_d1_raw_alignment(
                frozen_d1=(
                    frozen_d1_window
                ),
                current_h1=(
                    current_h1_window
                ),
            )
        )

        decision = (
            _decision(
                global_h1_metrics=(
                    global_h1_metrics
                ),
                hour_documents=(
                    hour_documents
                ),
                d1_raw_alignment=(
                    d1_raw_alignment
                ),
                session_bar_counts=(
                    session_bar_counts
                ),
            )
        )

        return {
            "valid": True,
            "reason": (
                "OK_XAUUSD_CURRENT_BROKER_H1_"
                "SESSION_HOUR_RESIDUAL_DIAGNOSTIC"
            ),
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "research_scope": (
                "CURRENT_BROKER_VS_FROZEN_H1_"
                "SAME_CANONICAL_HOUR_RAW_RESIDUAL_"
                "AND_CONFIRMED_00UTC_D1_REAGGREGATION"
            ),
            "confirmed_frozen_d1_contract": {
                "session_close_hour_utc": (
                    CONFIRMED_D1_CLOSE_HOUR_UTC
                ),
                "label_day_shift": (
                    CONFIRMED_D1_LABEL_DAY_SHIFT
                ),
                "source_provenance_status": (
                    "FROZEN_D1_FIXED_SESSION_BOUNDARY_CONFIRMED"
                ),
                "source_alignment_score": (
                    0.9993282836210587
                ),
                "source_body_correlation": (
                    0.9997335945860204
                ),
                "source_close_delta_correlation": (
                    0.9997641690038179
                ),
                "source_range_correlation": (
                    0.9999999999999998
                ),
                "source_direction_agreement": (
                    0.9961240310077519
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
                "split_used": (
                    "TRAIN_ONLY_TIME_WINDOW"
                ),
                "train_rows": int(
                    len(
                        frozen_train
                    )
                ),
                "comparison_time_start": (
                    comparison_start.isoformat()
                ),
                "comparison_time_end": (
                    comparison_end.isoformat()
                ),
                "frozen_h1_full_rows": int(
                    len(
                        frozen_h1
                    )
                ),
                "frozen_h1_window_rows": int(
                    len(
                        frozen_h1_window
                    )
                ),
                "frozen_d1_full_rows": int(
                    len(
                        frozen_d1
                    )
                ),
                "frozen_d1_window_rows": int(
                    len(
                        frozen_d1_window
                    )
                ),
                "frozen_h1_hash_validated": (
                    True
                ),
                "frozen_d1_hash_validated": (
                    True
                ),
                "frozen_h1_resolution": (
                    frozen_h1_resolution
                ),
                "frozen_d1_resolution": (
                    frozen_d1_resolution
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
                "raw_h1_rows": int(
                    len(
                        raw_current_h1
                    )
                ),
                "canonical_h1_window_rows": int(
                    len(
                        current_h1_window
                    )
                ),
            },
            "confirmed_clock_mapping": (
                current_clock_meta
            ),
            "global_h1_same_time_alignment": (
                global_h1_metrics
            ),
            "session_bar_count_comparison": (
                session_bar_counts
            ),
            "confirmed_00utc_d1_raw_alignment": (
                d1_raw_alignment
            ),
            "hourly_h1_residuals": (
                hour_documents
            ),
            "thresholds": {
                "minimum_global_h1_paired_rows": (
                    MIN_GLOBAL_H1_PAIRED_ROWS
                ),
                "minimum_hour_paired_rows": (
                    MIN_HOUR_PAIRED_ROWS
                ),
                "minimum_hour_coverage": (
                    MIN_HOUR_COVERAGE
                ),
                "h1_strong_body_correlation": (
                    H1_STRONG_BODY_CORRELATION
                ),
                "h1_strong_close_delta_correlation": (
                    H1_STRONG_CLOSE_DELTA_CORRELATION
                ),
                "h1_strong_range_correlation": (
                    H1_STRONG_RANGE_CORRELATION
                ),
                "h1_strong_direction_agreement": (
                    H1_STRONG_DIRECTION_AGREEMENT
                ),
                "d1_raw_confirmed_body_correlation": (
                    D1_RAW_CONFIRMED_BODY_CORRELATION
                ),
                "d1_raw_confirmed_close_delta_correlation": (
                    D1_RAW_CONFIRMED_CLOSE_DELTA_CORRELATION
                ),
                "d1_raw_confirmed_range_correlation": (
                    D1_RAW_CONFIRMED_RANGE_CORRELATION
                ),
                "d1_raw_confirmed_direction_agreement": (
                    D1_RAW_CONFIRMED_DIRECTION_AGREEMENT
                ),
                "maximum_localized_weak_hours": (
                    MAX_LOCALIZED_WEAK_HOURS
                ),
            },
            "decision": (
                decision
            ),
            "scientific_policy": {
                "immutable_frozen_h1_loaded": (
                    True
                ),
                "immutable_frozen_d1_loaded": (
                    True
                ),
                "raw_snapshot_hashes_validated": (
                    True
                ),
                "train_used_only_for_time_window": (
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
                "if_d1_raw_alignment_confirmed": (
                    "AUDIT_D1_FEATURE_GENERATION_WARMUP_"
                    "AND_LONG_MEMORY_STATE_USING_CONFIRMED_00UTC_D1"
                ),
                "if_session_coverage_mismatch": (
                    "ISOLATE_MISSING_OR_EXTRA_CANONICAL_"
                    "H1_SESSION_HOURS_BY_DATE"
                ),
                "if_hour_residual_localized": (
                    "TRACE_WEAK_HOURS_TO_BROKER_"
                    "ROLLOVER_AND_SESSION_GAP_BEHAVIOR"
                ),
                "if_hour_residual_broad": (
                    "QUANTIFY_H1_RAW_MICROSTRUCTURE_EFFECT_"
                    "ON_D1_LONG_MEMORY_FEATURES"
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
                        "XAUUSD_CURRENT_BROKER_H1_"
                        "SESSION_HOUR_RESIDUAL_DIAGNOSTIC_FAILED"
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