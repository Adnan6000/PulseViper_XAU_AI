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

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


ANALYSIS_VERSION = (
    "XAUUSD_CURRENT_BROKER_M5_FEATURE_ALIGNMENT_V2"
)

SOURCE_AUDIT_MODULE = (
    "04_Testing.analyze_xauusd_current_broker_m5_domain_shift"
)

LAG_CANDIDATES_SECONDS = (
    -900,
    -600,
    -300,
    0,
    300,
    600,
    900,
)

MIN_OVERLAP_ROWS = 5000

STRONG_MEDIAN_CORRELATION = 0.80

CLEAR_GAIN_THRESHOLD = 0.25

LIKELY_GAIN_THRESHOLD = 0.10

LIKELY_CORRELATION_THRESHOLD = 0.50


ALIGNMENT_ANCHOR_FEATURES = (
    "m5_dist_ema20",
    "m5_ema20_slope",
    "m5_rsi14",
    "m5_rsi_slope",
    "m5_macd",
    "m5_macd_hist",
    "m5_roc10",
    "m5_momentum10",
    "m5_true_range",
    "m5_atr14",
    "m5_candle_range",
    "m5_avg_range20",
    "m5_rolling_std20",
    "m5_body",
    "m5_range",
    "m5_upper_wick",
    "m5_lower_wick",
    "m5_body_ratio",
    "m5_upper_wick_ratio",
    "m5_lower_wick_ratio",
)


audit: Any = importlib.import_module(
    SOURCE_AUDIT_MODULE
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


def _paired_correlation(
    left: pd.Series,
    right: pd.Series,
) -> tuple[
    float | None,
    int,
]:

    left_values = pd.to_numeric(
        left,
        errors="coerce",
    ).to_numpy(
        dtype=np.float64
    )

    right_values = pd.to_numeric(
        right,
        errors="coerce",
    ).to_numpy(
        dtype=np.float64
    )

    valid = (
        np.isfinite(
            left_values
        )
        &
        np.isfinite(
            right_values
        )
    )

    left_valid = (
        left_values[
            valid
        ]
    )

    right_valid = (
        right_values[
            valid
        ]
    )

    rows = int(
        left_valid.size
    )

    if rows < 3:

        return (
            None,
            rows,
        )

    left_std = float(
        np.std(
            left_valid
        )
    )

    right_std = float(
        np.std(
            right_valid
        )
    )

    if (
        left_std
        <=
        1e-12
        or
        right_std
        <=
        1e-12
    ):

        return (
            None,
            rows,
        )

    correlation = float(
        np.corrcoef(
            left_valid,
            right_valid,
        )[
            0,
            1
        ]
    )

    if not math.isfinite(
        correlation
    ):

        return (
            None,
            rows,
        )

    return (
        correlation,
        rows,
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


def _median_absolute_correlation(
    values: Sequence[
        float | None
    ],
) -> float | None:

    finite = [
        abs(
            float(
                value
            )
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


def _lag_document(
    frozen_train: pd.DataFrame,
    current_frame: pd.DataFrame,
    *,
    lag_seconds: int,
) -> dict[str, Any]:

    current = (
        current_frame[
            [
                "decision_time",
                *ALIGNMENT_ANCHOR_FEATURES,
            ]
        ]
        .copy()
    )

    current[
        "decision_time"
    ] = (
        pd.to_datetime(
            current[
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

    frozen = (
        frozen_train[
            [
                "decision_time",
                *ALIGNMENT_ANCHOR_FEATURES,
            ]
        ]
        .copy()
    )

    paired = (
        frozen
        .merge(
            current,
            on="decision_time",
            how="inner",
            suffixes=(
                "_frozen",
                "_current",
            ),
            validate="one_to_one",
        )
        .sort_values(
            "decision_time"
        )
        .reset_index(
            drop=True
        )
    )

    feature_metrics: list[
        dict[str, Any]
    ] = []

    correlations: list[
        float | None
    ] = []

    for feature in (
        ALIGNMENT_ANCHOR_FEATURES
    ):

        (
            correlation,
            paired_rows,
        ) = (
            _paired_correlation(
                paired[
                    f"{feature}_frozen"
                ],
                paired[
                    f"{feature}_current"
                ],
            )
        )

        correlations.append(
            correlation
        )

        feature_metrics.append(
            {
                "feature": (
                    feature
                ),
                "paired_rows": (
                    paired_rows
                ),
                "correlation": (
                    correlation
                ),
                "absolute_correlation": (
                    abs(
                        correlation
                    )
                    if correlation
                    is not None
                    else None
                ),
            }
        )

    signed_median = (
        _median_finite(
            correlations
        )
    )

    absolute_median = (
        _median_absolute_correlation(
            correlations
        )
    )

    positive_080_count = sum(
        1
        for value
        in correlations
        if (
            value is not None
            and
            value
            >=
            0.80
        )
    )

    positive_095_count = sum(
        1
        for value
        in correlations
        if (
            value is not None
            and
            value
            >=
            0.95
        )
    )

    negative_count = sum(
        1
        for value
        in correlations
        if (
            value is not None
            and
            value
            <
            0.0
        )
    )

    return {
        "lag_seconds": int(
            lag_seconds
        ),
        "lag_bars_m5": float(
            lag_seconds
            /
            300.0
        ),
        "interpretation": (
            "CURRENT_FEATURE_TIME_SHIFT_APPLIED_BEFORE_JOIN"
        ),
        "overlap_rows": int(
            len(
                paired
            )
        ),
        "anchor_feature_count": int(
            len(
                ALIGNMENT_ANCHOR_FEATURES
            )
        ),
        "finite_correlation_count": int(
            sum(
                1
                for value
                in correlations
                if value
                is not None
            )
        ),
        "median_signed_correlation": (
            signed_median
        ),
        "median_absolute_correlation": (
            absolute_median
        ),
        "positive_correlation_ge_0_80_count": int(
            positive_080_count
        ),
        "positive_correlation_ge_0_95_count": int(
            positive_095_count
        ),
        "negative_correlation_count": int(
            negative_count
        ),
        "feature_correlations": (
            feature_metrics
        ),
    }


def _lag_score(
    document: Mapping[
        str,
        Any,
    ],
) -> tuple[
    float,
    int,
    int,
    int,
]:

    median_signed = (
        _safe_float(
            document.get(
                "median_signed_correlation"
            )
        )
    )

    if median_signed is None:

        median_signed = -2.0

    positive_095_count = int(
        document.get(
            "positive_correlation_ge_0_95_count",
            0,
        )
    )

    positive_080_count = int(
        document.get(
            "positive_correlation_ge_0_80_count",
            0,
        )
    )

    overlap_rows = int(
        document.get(
            "overlap_rows",
            0,
        )
    )

    return (
        median_signed,
        positive_095_count,
        positive_080_count,
        overlap_rows,
    )


def _alignment_decision(
    lag_documents: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
) -> dict[str, Any]:

    if not lag_documents:

        raise RuntimeError(
            "NO_LAG_DOCUMENTS"
        )

    ranked = sorted(
        lag_documents,
        key=_lag_score,
        reverse=True,
    )

    best: Mapping[
        str,
        Any,
    ] = ranked[
        0
    ]

    zero: Mapping[
        str,
        Any,
    ] | None = next(
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
            "ZERO_LAG_DOCUMENT_MISSING"
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
                "median_signed_correlation"
            )
        )
    )

    zero_median = (
        _safe_float(
            zero.get(
                "median_signed_correlation"
            )
        )
    )

    gain: float | None = None

    if (
        best_median
        is not None
        and
        zero_median
        is not None
    ):

        gain = (
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
            "INSUFFICIENT_ALIGNMENT_OVERLAP"
        )

        reason = (
            "BEST_LAG_HAS_TOO_FEW_OVERLAPPING_ROWS"
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
        STRONG_MEDIAN_CORRELATION
    ):

        status = (
            "ZERO_LAG_ALIGNMENT_CONFIRMED"
        )

        reason = (
            "CURRENT_FEATURE_TIMESTAMPS_ALREADY_ALIGNED"
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
        STRONG_MEDIAN_CORRELATION
        and
        gain
        is not None
        and
        gain
        >=
        CLEAR_GAIN_THRESHOLD
    ):

        status = (
            "NONZERO_FEATURE_TIME_OFFSET_CONFIRMED"
        )

        reason = (
            "NONZERO_LAG_MATERIALLY_RESTORES_"
            "FAST_FEATURE_CORRELATION"
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
        LIKELY_CORRELATION_THRESHOLD
        and
        gain
        is not None
        and
        gain
        >=
        LIKELY_GAIN_THRESHOLD
    ):

        status = (
            "NONZERO_FEATURE_TIME_OFFSET_LIKELY"
        )

        reason = (
            "NONZERO_LAG_SUBSTANTIALLY_IMPROVES_"
            "FEATURE_CORRELATION"
        )

    else:

        status = (
            "ALIGNMENT_NOT_RESOLVED"
        )

        reason = (
            "NO_TESTED_LAG_PRODUCED_CONCLUSIVE_ALIGNMENT"
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "selected_current_time_shift_seconds": (
            best_lag
        ),
        "selected_current_time_shift_m5_bars": float(
            best_lag
            /
            300.0
        ),
        "selected_overlap_rows": (
            best_overlap
        ),
        "selected_median_signed_correlation": (
            best_median
        ),
        "zero_lag_median_signed_correlation": (
            zero_median
        ),
        "median_correlation_gain_vs_zero": (
            gain
        ),
        "domain_shift_verdict_allowed": (
            status
            in {
                "ZERO_LAG_ALIGNMENT_CONFIRMED",
                "NONZERO_FEATURE_TIME_OFFSET_CONFIRMED",
            }
        ),
        "full_333_portability_claimed": (
            False
        ),
    }


def run_diagnostic() -> dict[str, Any]:

    trainer = (
        audit
        .XAUUSDHierarchicalModelV4Trainer()
    )

    snapshot = (
        audit
        .sweep_module
        ._discover_frozen_training_snapshot(
            trainer=trainer
        )
    )

    dataset_path = (
        audit
        ._snapshot_dataset_path(
            snapshot
        )
    )

    manifest_path = (
        audit
        ._snapshot_manifest_path(
            snapshot,
            dataset_path,
        )
    )

    audit._validate_snapshot(
        snapshot,
        dataset_path,
        manifest_path,
    )

    manifest = (
        audit
        ._load_manifest(
            manifest_path
        )
    )

    base_features = (
        audit
        ._base_feature_names()
    )

    comparison_features = (
        audit
        ._comparison_feature_names(
            base_features
        )
    )

    for feature in (
        ALIGNMENT_ANCHOR_FEATURES
    ):

        _require(
            feature
            in
            comparison_features,
            (
                "ALIGNMENT_ANCHOR_NOT_IN_M5_CONTRACT:"
                f"{feature}"
            ),
        )

    frozen_train = (
        audit
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
            audit
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
                "SYMBOL_INFO_UNAVAILABLE:"
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
                    "SYMBOL_SELECT_FAILED:"
                    f"{broker_symbol}:"
                    f"{mt5.last_error()}"
                ),
            )

        fetch_start = (
            train_start
            -
            pd.Timedelta(
                days=(
                    audit
                    .HISTORY_WARMUP_DAYS
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

        rates = (
            mt5.copy_rates_range(
                broker_symbol,
                mt5.TIMEFRAME_M5,
                fetch_start.to_pydatetime(),
                fetch_end.to_pydatetime(),
            )
        )

        raw_m5 = (
            audit
            ._mt5_rates_frame(
                rates
            )
        )

        (
            current_frame,
            generation_meta,
        ) = (
            audit
            ._build_current_m5_comparison_frame(
                raw_m5,
                base_features,
            )
        )

        lag_documents: list[
            dict[str, Any]
        ] = [
            _lag_document(
                frozen_train,
                current_frame,
                lag_seconds=(
                    lag_seconds
                ),
            )
            for lag_seconds
            in LAG_CANDIDATES_SECONDS
        ]

        decision = (
            _alignment_decision(
                lag_documents
            )
        )

        ranked_lags = sorted(
            lag_documents,
            key=_lag_score,
            reverse=True,
        )

        return {
            "valid": True,
            "reason": (
                "OK_XAUUSD_CURRENT_BROKER_M5_"
                "FEATURE_ALIGNMENT_DIAGNOSTIC"
            ),
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "source_audit_module": (
                SOURCE_AUDIT_MODULE
            ),
            "frozen_reference": {
                "dataset_id": (
                    audit
                    .EXPECTED_DATASET_ID
                ),
                "dataset_sha256": (
                    audit
                    .EXPECTED_DATASET_SHA256
                ),
                "training_manifest_sha256": (
                    audit
                    .EXPECTED_TRAINING_MANIFEST_SHA256
                ),
                "training_contract": (
                    audit
                    .EXPECTED_TRAINING_CONTRACT
                ),
                "identity": (
                    audit
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
                "m5_history_rows": int(
                    len(
                        raw_m5
                    )
                ),
            },
            "feature_generation": (
                generation_meta
            ),
            "alignment_policy": {
                "candidate_current_time_shifts_seconds": list(
                    LAG_CANDIDATES_SECONDS
                ),
                "candidate_current_time_shifts_m5_bars": [
                    float(
                        value
                        /
                        300.0
                    )
                    for value
                    in LAG_CANDIDATES_SECONDS
                ],
                "selection_primary": (
                    "MAX_MEDIAN_SIGNED_CORRELATION_"
                    "ACROSS_FAST_M5_FEATURES"
                ),
                "selection_secondary": (
                    "MAX_COUNT_CORRELATION_GE_0_95"
                ),
                "selection_tertiary": (
                    "MAX_COUNT_CORRELATION_GE_0_80"
                ),
                "selection_final": (
                    "MAX_OVERLAP_ROWS"
                ),
                "anchor_features": list(
                    ALIGNMENT_ANCHOR_FEATURES
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
                    "median_signed_correlation": (
                        document[
                            "median_signed_correlation"
                        ]
                    ),
                    "median_absolute_correlation": (
                        document[
                            "median_absolute_correlation"
                        ]
                    ),
                    "positive_correlation_ge_0_80_count": (
                        document[
                            "positive_correlation_ge_0_80_count"
                        ]
                    ),
                    "positive_correlation_ge_0_95_count": (
                        document[
                            "positive_correlation_ge_0_95_count"
                        ]
                    ),
                }
                for index, document
                in enumerate(
                    ranked_lags,
                    start=1,
                )
            ],
            "lag_diagnostics": (
                lag_documents
            ),
            "scientific_policy": {
                "train_loaded": True,
                "validation_loaded": False,
                "validation_evaluated": False,
                "test_loaded": False,
                "test_evaluated": False,
                "labels_used": False,
                "model_loaded": False,
                "model_trained": False,
                "model_artifacts_written": False,
                "frozen_dataset_mutated": False,
                "frozen_manifest_mutated": False,
                "mt5_used": True,
                "mt5_history_read_only": True,
                "orders_sent": False,
                "positions_modified": False,
                "risk_engine_modified": False,
                "sizing_modified": False,
                "execution_integration_modified": False,
                "live_authorized": False,
            },
            "next_decision_contract": {
                "if_nonzero_offset_confirmed": (
                    "CORRECT_M5_DOMAIN_SHIFT_AUDIT_"
                    "ALIGNMENT_AND_RERUN"
                ),
                "if_zero_lag_confirmed": (
                    "ACCEPT_ZERO_LAG_AND_REVIEW_"
                    "TRUE_PRICE_DOMAIN_SHIFT"
                ),
                "if_alignment_not_resolved": (
                    "COMPARE_RAW_OHLC_SAME_TIMESTAMP_"
                    "BEFORE_ANY_MODEL_DECISION"
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
                        "FEATURE_ALIGNMENT_DIAGNOSTIC_FAILED"
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