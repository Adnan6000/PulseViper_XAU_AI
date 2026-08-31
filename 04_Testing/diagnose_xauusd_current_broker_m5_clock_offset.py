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
    "XAUUSD_CURRENT_BROKER_M5_CLOCK_OFFSET_V1"
)

RAW_DIAGNOSTIC_MODULE = (
    "04_Testing."
    "diagnose_xauusd_current_broker_m5_raw_ohlc_alignment"
)

M5_SECONDS = 300

COARSE_MAX_ABS_LAG_SECONDS = (
    8 * 60 * 60
)

COARSE_STEP_SECONDS = (
    30 * 60
)

REFINE_RADIUS_SECONDS = (
    30 * 60
)

REFINE_STEP_SECONDS = (
    M5_SECONDS
)

MIN_OVERLAP_ROWS = 5000

STRONG_BODY_CORRELATION = 0.80

STRONG_CLOSE_DELTA_CORRELATION = 0.80

STRONG_DIRECTION_AGREEMENT = 0.80

STRONG_RANGE_CORRELATION = 0.70

LIKELY_ALIGNMENT_SCORE = 0.50

LIKELY_SCORE_GAIN_VS_ZERO = 0.20


raw_module: Any = importlib.import_module(
    RAW_DIAGNOSTIC_MODULE
)

audit: Any = raw_module.audit


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


def _metric(
    document: Mapping[
        str,
        Any,
    ],
    key: str,
) -> float | None:

    return _safe_float(
        document.get(
            key
        )
    )


def _direction_edge(
    agreement: float | None,
) -> float | None:

    if agreement is None:
        return None

    return float(
        max(
            -1.0,
            min(
                1.0,
                (
                    2.0
                    *
                    agreement
                    -
                    1.0
                ),
            ),
        )
    )


def _alignment_score(
    document: Mapping[
        str,
        Any,
    ],
) -> float | None:

    body = (
        _metric(
            document,
            "body_correlation",
        )
    )

    close_delta = (
        _metric(
            document,
            "close_delta_correlation",
        )
    )

    direction = (
        _direction_edge(
            _metric(
                document,
                "candle_direction_agreement",
            )
        )
    )

    range_correlation = (
        _metric(
            document,
            "range_correlation",
        )
    )

    values = [
        value
        for value
        in (
            body,
            close_delta,
            direction,
            range_correlation,
        )
        if value is not None
    ]

    if len(
        values
    ) < 3:

        return None

    return float(
        np.mean(
            np.asarray(
                values,
                dtype=np.float64,
            )
        )
    )


def _strong_alignment(
    document: Mapping[
        str,
        Any,
    ],
) -> bool:

    overlap = int(
        document.get(
            "overlap_rows",
            0,
        )
    )

    body = (
        _metric(
            document,
            "body_correlation",
        )
    )

    close_delta = (
        _metric(
            document,
            "close_delta_correlation",
        )
    )

    direction = (
        _metric(
            document,
            "candle_direction_agreement",
        )
    )

    range_correlation = (
        _metric(
            document,
            "range_correlation",
        )
    )

    return bool(
        overlap
        >=
        MIN_OVERLAP_ROWS
        and
        body
        is not None
        and
        body
        >=
        STRONG_BODY_CORRELATION
        and
        close_delta
        is not None
        and
        close_delta
        >=
        STRONG_CLOSE_DELTA_CORRELATION
        and
        direction
        is not None
        and
        direction
        >=
        STRONG_DIRECTION_AGREEMENT
        and
        range_correlation
        is not None
        and
        range_correlation
        >=
        STRONG_RANGE_CORRELATION
    )


def _scan_document(
    frozen_raw: pd.DataFrame,
    current_raw: pd.DataFrame,
    *,
    lag_seconds: int,
) -> dict[str, Any]:

    full = (
        raw_module
        ._raw_lag_document(
            frozen_raw,
            current_raw,
            lag_seconds=(
                lag_seconds
            ),
        )
    )

    score = (
        _alignment_score(
            full
        )
    )

    return {
        "lag_seconds": int(
            lag_seconds
        ),
        "lag_minutes": float(
            lag_seconds
            /
            60.0
        ),
        "lag_hours": float(
            lag_seconds
            /
            3600.0
        ),
        "lag_bars_m5": float(
            lag_seconds
            /
            M5_SECONDS
        ),
        "overlap_rows": int(
            full.get(
                "overlap_rows",
                0,
            )
        ),
        "body_correlation": (
            full.get(
                "body_correlation"
            )
        ),
        "close_delta_correlation": (
            full.get(
                "close_delta_correlation"
            )
        ),
        "candle_direction_agreement": (
            full.get(
                "candle_direction_agreement"
            )
        ),
        "range_correlation": (
            full.get(
                "range_correlation"
            )
        ),
        "alignment_score": (
            score
        ),
        "strong_alignment": (
            _strong_alignment(
                full
            )
        ),
    }


def _score_key(
    document: Mapping[
        str,
        Any,
    ],
) -> tuple[
    float,
    float,
    float,
    float,
    float,
    int,
]:

    score = (
        _metric(
            document,
            "alignment_score",
        )
    )

    body = (
        _metric(
            document,
            "body_correlation",
        )
    )

    close_delta = (
        _metric(
            document,
            "close_delta_correlation",
        )
    )

    direction = (
        _metric(
            document,
            "candle_direction_agreement",
        )
    )

    range_correlation = (
        _metric(
            document,
            "range_correlation",
        )
    )

    return (
        score
        if score is not None
        else -2.0,
        body
        if body is not None
        else -2.0,
        close_delta
        if close_delta is not None
        else -2.0,
        direction
        if direction is not None
        else -2.0,
        range_correlation
        if range_correlation is not None
        else -2.0,
        int(
            document.get(
                "overlap_rows",
                0,
            )
        ),
    )


def _coarse_lags(
) -> tuple[int, ...]:

    return tuple(
        range(
            -COARSE_MAX_ABS_LAG_SECONDS,
            COARSE_MAX_ABS_LAG_SECONDS
            +
            COARSE_STEP_SECONDS,
            COARSE_STEP_SECONDS,
        )
    )


def _refined_lags(
    best_coarse_lag: int,
) -> tuple[int, ...]:

    lower = max(
        -COARSE_MAX_ABS_LAG_SECONDS,
        (
            best_coarse_lag
            -
            REFINE_RADIUS_SECONDS
        ),
    )

    upper = min(
        COARSE_MAX_ABS_LAG_SECONDS,
        (
            best_coarse_lag
            +
            REFINE_RADIUS_SECONDS
        ),
    )

    values = set(
        range(
            lower,
            upper
            +
            REFINE_STEP_SECONDS,
            REFINE_STEP_SECONDS,
        )
    )

    values.add(
        best_coarse_lag
    )

    values.add(
        0
    )

    return tuple(
        sorted(
            values
        )
    )


def _ranked_summary(
    documents: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
    *,
    limit: int,
) -> list[dict[str, Any]]:

    ranked = sorted(
        documents,
        key=_score_key,
        reverse=True,
    )

    return [
        {
            "rank": int(
                index
            ),
            "lag_seconds": (
                document.get(
                    "lag_seconds"
                )
            ),
            "lag_minutes": (
                document.get(
                    "lag_minutes"
                )
            ),
            "lag_hours": (
                document.get(
                    "lag_hours"
                )
            ),
            "lag_bars_m5": (
                document.get(
                    "lag_bars_m5"
                )
            ),
            "overlap_rows": (
                document.get(
                    "overlap_rows"
                )
            ),
            "alignment_score": (
                document.get(
                    "alignment_score"
                )
            ),
            "body_correlation": (
                document.get(
                    "body_correlation"
                )
            ),
            "close_delta_correlation": (
                document.get(
                    "close_delta_correlation"
                )
            ),
            "candle_direction_agreement": (
                document.get(
                    "candle_direction_agreement"
                )
            ),
            "range_correlation": (
                document.get(
                    "range_correlation"
                )
            ),
            "strong_alignment": (
                document.get(
                    "strong_alignment"
                )
            ),
        }
        for index, document
        in enumerate(
            ranked[
                :limit
            ],
            start=1,
        )
    ]


def _decision(
    refined_documents: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
) -> dict[str, Any]:

    _require(
        bool(
            refined_documents
        ),
        "NO_REFINED_CLOCK_SCAN_DOCUMENTS",
    )

    ranked = sorted(
        refined_documents,
        key=_score_key,
        reverse=True,
    )

    best = ranked[
        0
    ]

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
            in refined_documents
            if int(
                document.get(
                    "lag_seconds",
                    999999999,
                )
            )
            ==
            0
        ),
        None,
    )

    if zero is None:

        raise RuntimeError(
            "ZERO_LAG_CLOCK_SCAN_DOCUMENT_MISSING"
        )

    best_lag = int(
        best.get(
            "lag_seconds",
            0,
        )
    )

    best_score = (
        _metric(
            best,
            "alignment_score",
        )
    )

    zero_score = (
        _metric(
            zero,
            "alignment_score",
        )
    )

    score_gain: (
        float
        |
        None
    ) = None

    if (
        best_score is not None
        and
        zero_score is not None
    ):

        score_gain = float(
            best_score
            -
            zero_score
        )

    best_strong = bool(
        best.get(
            "strong_alignment",
            False,
        )
    )

    boundary_hit = bool(
        abs(
            best_lag
        )
        >=
        COARSE_MAX_ABS_LAG_SECONDS
    )

    if (
        best_strong
        and
        abs(
            best_lag
        )
        <=
        M5_SECONDS
    ):

        status = (
            "NEAR_ZERO_RAW_ALIGNMENT_CONFIRMED"
        )

        reason = (
            "RAW_CANDLES_ALIGN_WITHOUT_MATERIAL_CLOCK_OFFSET"
        )

        next_action = (
            "AUDIT_FROZEN_FEATURE_AVAILABILITY_TIME_AND_"
            "FEATURE_PROVENANCE"
        )

    elif best_strong:

        status = (
            "CLOCK_OFFSET_CONFIRMED"
        )

        reason = (
            "RAW_CANDLE_CORRESPONDENCE_RESTORED_BY_"
            "NONZERO_CLOCK_SHIFT"
        )

        next_action = (
            "APPLY_CONFIRMED_TIME_MAPPING_IN_RESEARCH_"
            "DOMAIN_AUDIT_AND_RERUN_M5_FEATURE_COMPARISON"
        )

    elif (
        best_score is not None
        and
        best_score
        >=
        LIKELY_ALIGNMENT_SCORE
        and
        score_gain is not None
        and
        score_gain
        >=
        LIKELY_SCORE_GAIN_VS_ZERO
    ):

        status = (
            "CLOCK_OFFSET_LIKELY"
        )

        reason = (
            "WIDE_CLOCK_SCAN_SUBSTANTIALLY_IMPROVES_"
            "RAW_CANDLE_CORRESPONDENCE"
        )

        next_action = (
            "VERIFY_SELECTED_CLOCK_OFFSET_WITH_"
            "RAW_CANDLE_SAMPLES_BEFORE_FEATURE_AUDIT"
        )

    elif boundary_hit:

        status = (
            "CLOCK_SCAN_BOUNDARY_HIT"
        )

        reason = (
            "BEST_CANDIDATE_IS_AT_PLUS_OR_MINUS_8_HOUR_BOUNDARY"
        )

        next_action = (
            "EXPAND_CLOCK_SCAN_BEFORE_TRUE_FEED_SHIFT_CONCLUSION"
        )

    else:

        status = (
            "WIDE_CLOCK_OFFSET_NOT_FOUND"
        )

        reason = (
            "NO_PLUS_OR_MINUS_8_HOUR_SHIFT_RESTORED_"
            "STRONG_RAW_CANDLE_CORRESPONDENCE"
        )

        next_action = (
            "AUDIT_FROZEN_RAW_SOURCE_PROVENANCE_PRICE_BASIS_"
            "AND_BAR_TIMESTAMP_SEMANTICS"
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "selected_lag_seconds": (
            best_lag
        ),
        "selected_lag_minutes": float(
            best_lag
            /
            60.0
        ),
        "selected_lag_hours": float(
            best_lag
            /
            3600.0
        ),
        "selected_lag_bars_m5": float(
            best_lag
            /
            M5_SECONDS
        ),
        "selected_alignment_score": (
            best_score
        ),
        "zero_lag_alignment_score": (
            zero_score
        ),
        "alignment_score_gain_vs_zero": (
            score_gain
        ),
        "selected_body_correlation": (
            best.get(
                "body_correlation"
            )
        ),
        "selected_close_delta_correlation": (
            best.get(
                "close_delta_correlation"
            )
        ),
        "selected_candle_direction_agreement": (
            best.get(
                "candle_direction_agreement"
            )
        ),
        "selected_range_correlation": (
            best.get(
                "range_correlation"
            )
        ),
        "selected_overlap_rows": (
            best.get(
                "overlap_rows"
            )
        ),
        "selected_strong_alignment": (
            best_strong
        ),
        "scan_boundary_hit": (
            boundary_hit
        ),
        "feature_domain_shift_verdict_allowed": (
            status
            in {
                "NEAR_ZERO_RAW_ALIGNMENT_CONFIRMED",
                "CLOCK_OFFSET_CONFIRMED",
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

    trainer = (
        audit
        .XAUUSDHierarchicalModelV4Trainer()
    )

    training_snapshot = (
        audit
        .sweep_module
        ._discover_frozen_training_snapshot(
            trainer=trainer
        )
    )

    training_dataset_path = (
        audit
        ._snapshot_dataset_path(
            training_snapshot
        )
    )

    training_manifest_path = (
        audit
        ._snapshot_manifest_path(
            training_snapshot,
            training_dataset_path,
        )
    )

    audit._validate_snapshot(
        training_snapshot,
        training_dataset_path,
        training_manifest_path,
    )

    training_manifest = (
        audit
        ._load_manifest(
            training_manifest_path
        )
    )

    historical_sources = (
        training_manifest.get(
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
        "SOURCE_HISTORICAL_M5_DATASET_ID_MISMATCH",
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
        "SOURCE_HISTORICAL_M5_DATASET_SHA256_MISMATCH",
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

    frozen_raw = (
        raw_module
        ._load_frozen_raw_m5(
            historical_dataset_path
        )
    )

    frozen_train = (
        audit
        ._load_frozen_train_only(
            training_dataset_path,
            [
                "m5_ema20"
            ],
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

    frozen_window_start = (
        train_start
        -
        pd.Timedelta(
            days=1
        )
    )

    frozen_window_end = (
        train_end
        +
        pd.Timedelta(
            days=1
        )
    )

    frozen_raw = (
        frozen_raw.loc[
            (
                frozen_raw[
                    "time"
                ]
                >=
                frozen_window_start
            )
            &
            (
                frozen_raw[
                    "time"
                ]
                <=
                frozen_window_end
            )
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    _require(
        not frozen_raw.empty,
        "FROZEN_RAW_CLOCK_SCAN_WINDOW_EMPTY",
    )

    current_fetch_start = (
        frozen_window_start
        -
        pd.Timedelta(
            seconds=(
                COARSE_MAX_ABS_LAG_SECONDS
                +
                REFINE_RADIUS_SECONDS
            )
        )
    )

    current_fetch_end = (
        frozen_window_end
        +
        pd.Timedelta(
            seconds=(
                COARSE_MAX_ABS_LAG_SECONDS
                +
                REFINE_RADIUS_SECONDS
            )
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
                "CURRENT_BROKER_SYMBOL_INFO_UNAVAILABLE:"
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
                    "CURRENT_BROKER_SYMBOL_SELECT_FAILED:"
                    f"{mt5.last_error()}"
                ),
            )

        rates = (
            mt5.copy_rates_range(
                broker_symbol,
                mt5.TIMEFRAME_M5,
                current_fetch_start.to_pydatetime(),
                current_fetch_end.to_pydatetime(),
            )
        )

        current_raw = (
            audit
            ._mt5_rates_frame(
                rates
            )
        )

        coarse_lags = (
            _coarse_lags()
        )

        coarse_documents = [
            _scan_document(
                frozen_raw,
                current_raw,
                lag_seconds=(
                    lag_seconds
                ),
            )
            for lag_seconds
            in coarse_lags
        ]

        coarse_ranked = sorted(
            coarse_documents,
            key=_score_key,
            reverse=True,
        )

        _require(
            bool(
                coarse_ranked
            ),
            "COARSE_CLOCK_SCAN_EMPTY",
        )

        best_coarse_lag = int(
            coarse_ranked[
                0
            ].get(
                "lag_seconds",
                0,
            )
        )

        refine_lags = (
            _refined_lags(
                best_coarse_lag
            )
        )

        refined_documents = [
            _scan_document(
                frozen_raw,
                current_raw,
                lag_seconds=(
                    lag_seconds
                ),
            )
            for lag_seconds
            in refine_lags
        ]

        decision = (
            _decision(
                refined_documents
            )
        )

        selected_lag = int(
            decision[
                "selected_lag_seconds"
            ]
        )

        selected_full = (
            raw_module
            ._raw_lag_document(
                frozen_raw,
                current_raw,
                lag_seconds=(
                    selected_lag
                ),
            )
        )

        zero_full = (
            raw_module
            ._raw_lag_document(
                frozen_raw,
                current_raw,
                lag_seconds=0,
            )
        )

        return {
            "valid": True,
            "reason": (
                "OK_XAUUSD_CURRENT_BROKER_M5_CLOCK_OFFSET_DIAGNOSTIC"
            ),
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "frozen_reference": {
                "training_dataset_id": (
                    audit
                    .EXPECTED_DATASET_ID
                ),
                "training_dataset_sha256": (
                    audit
                    .EXPECTED_DATASET_SHA256
                ),
                "training_contract": (
                    audit
                    .EXPECTED_TRAINING_CONTRACT
                ),
                "split_loaded": (
                    "TRAIN_ONLY_FOR_TIME_BOUNDARY"
                ),
                "identity": (
                    audit
                    ._safe_frozen_identity(
                        training_manifest
                    )
                ),
                "raw_m5_dataset_id": (
                    raw_module
                    .EXPECTED_HISTORICAL_M5_DATASET_ID
                ),
                "raw_m5_dataset_sha256": (
                    raw_module
                    .EXPECTED_HISTORICAL_M5_DATASET_SHA256
                ),
                "raw_m5_hash_verified": (
                    True
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
                "m5_rows_loaded": int(
                    len(
                        current_raw
                    )
                ),
            },
            "scan_policy": {
                "coarse_min_lag_hours": float(
                    -COARSE_MAX_ABS_LAG_SECONDS
                    /
                    3600.0
                ),
                "coarse_max_lag_hours": float(
                    COARSE_MAX_ABS_LAG_SECONDS
                    /
                    3600.0
                ),
                "coarse_step_minutes": float(
                    COARSE_STEP_SECONDS
                    /
                    60.0
                ),
                "coarse_candidate_count": int(
                    len(
                        coarse_lags
                    )
                ),
                "best_coarse_lag_seconds": (
                    best_coarse_lag
                ),
                "best_coarse_lag_hours": float(
                    best_coarse_lag
                    /
                    3600.0
                ),
                "refine_radius_minutes": float(
                    REFINE_RADIUS_SECONDS
                    /
                    60.0
                ),
                "refine_step_minutes": float(
                    REFINE_STEP_SECONDS
                    /
                    60.0
                ),
                "refined_candidate_count": int(
                    len(
                        refine_lags
                    )
                ),
                "price_level_correlation_not_used_for_selection": (
                    True
                ),
                "selection_metrics": [
                    "body_correlation",
                    "close_delta_correlation",
                    "candle_direction_agreement",
                    "range_correlation",
                ],
            },
            "thresholds": {
                "minimum_overlap_rows": (
                    MIN_OVERLAP_ROWS
                ),
                "strong_body_correlation": (
                    STRONG_BODY_CORRELATION
                ),
                "strong_close_delta_correlation": (
                    STRONG_CLOSE_DELTA_CORRELATION
                ),
                "strong_direction_agreement": (
                    STRONG_DIRECTION_AGREEMENT
                ),
                "strong_range_correlation": (
                    STRONG_RANGE_CORRELATION
                ),
                "likely_alignment_score": (
                    LIKELY_ALIGNMENT_SCORE
                ),
                "likely_score_gain_vs_zero": (
                    LIKELY_SCORE_GAIN_VS_ZERO
                ),
            },
            "decision": (
                decision
            ),
            "coarse_top_10": (
                _ranked_summary(
                    coarse_documents,
                    limit=10,
                )
            ),
            "refined_ranking": (
                _ranked_summary(
                    refined_documents,
                    limit=(
                        len(
                            refined_documents
                        )
                    ),
                )
            ),
            "selected_full_diagnostic": (
                selected_full
            ),
            "zero_lag_full_diagnostic": (
                zero_full
            ),
            "scientific_policy": {
                "train_loaded": (
                    True
                ),
                "train_used_only_for_time_boundary": (
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
                "frozen_raw_snapshot_hash_verified": (
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
                "if_clock_offset_confirmed": (
                    "RERUN_M5_DOMAIN_SHIFT_WITH_CONFIRMED_TIME_MAPPING"
                ),
                "if_near_zero_alignment_confirmed": (
                    "AUDIT_FEATURE_AVAILABILITY_TIME_AND_FEATURE_PROVENANCE"
                ),
                "if_wide_clock_offset_not_found": (
                    "AUDIT_FROZEN_RAW_SOURCE_PROVENANCE_PRICE_BASIS_"
                    "AND_TIMESTAMP_SEMANTICS"
                ),
                "if_scan_boundary_hit": (
                    "EXPAND_CLOCK_SCAN_BEFORE_FEED_SHIFT_CONCLUSION"
                ),
                "broker_sensitive_spread_and_tick_volume_issue": (
                    "REMAINS_SEPARATE_AND_UNRESOLVED"
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
                        "CLOCK_OFFSET_DIAGNOSTIC_FAILED"
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