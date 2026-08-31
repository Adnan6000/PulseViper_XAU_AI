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
    "XAUUSD_CURRENT_BROKER_M5_CLOCK_OFFSET_TEMPORAL_V1"
)

CLOCK_MODULE_NAME = (
    "04_Testing."
    "diagnose_xauusd_current_broker_m5_clock_offset"
)

M5_SECONDS = 300

CANDIDATE_LAGS_SECONDS = (
    -4 * 60 * 60,
    -3 * 60 * 60,
    -2 * 60 * 60,
    -1 * 60 * 60,
    0,
)

CURRENT_HISTORY_BUFFER_SECONDS = (
    5 * 60 * 60
)

MIN_MONTH_OVERLAP_ROWS = 1500

MIN_ELIGIBLE_MONTHS = 6

CONFIRMED_DOMINANCE_SHARE = 0.80

LIKELY_NONZERO_SHARE = 0.80

MIN_CONFIRMED_MEDIAN_ALIGNMENT_SCORE = 0.70

MIN_LIKELY_MEDIAN_ALIGNMENT_SCORE = 0.50

MIN_DST_REGIME_MONTHS_EACH = 2


clock_module: Any = importlib.import_module(
    CLOCK_MODULE_NAME
)

raw_module: Any = (
    clock_module.raw_module
)

audit: Any = (
    clock_module.audit
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


def _compact_candidate(
    document: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    score = (
        clock_module
        ._alignment_score(
            document
        )
    )

    return {
        "lag_seconds": int(
            document.get(
                "lag_seconds",
                0,
            )
        ),
        "lag_hours": float(
            int(
                document.get(
                    "lag_seconds",
                    0,
                )
            )
            /
            3600.0
        ),
        "lag_bars_m5": float(
            int(
                document.get(
                    "lag_seconds",
                    0,
                )
            )
            /
            M5_SECONDS
        ),
        "overlap_rows": int(
            document.get(
                "overlap_rows",
                0,
            )
        ),
        "alignment_score": (
            score
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
            clock_module
            ._strong_alignment(
                document
            )
        ),
    }


def _candidate_score_key(
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

    return (
        clock_module
        ._score_key(
            document
        )
    )


def _month_diagnostic(
    frozen_month: pd.DataFrame,
    current_raw: pd.DataFrame,
    *,
    month_key: str,
) -> dict[str, Any]:

    candidate_documents: list[
        dict[str, Any]
    ] = []

    for lag_seconds in (
        CANDIDATE_LAGS_SECONDS
    ):

        full = (
            raw_module
            ._raw_lag_document(
                frozen_month,
                current_raw,
                lag_seconds=(
                    lag_seconds
                ),
            )
        )

        candidate_documents.append(
            _compact_candidate(
                full
            )
        )

    ranked = sorted(
        candidate_documents,
        key=_candidate_score_key,
        reverse=True,
    )

    _require(
        bool(
            ranked
        ),
        (
            "MONTH_CLOCK_CANDIDATES_EMPTY:"
            f"{month_key}"
        ),
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
            in candidate_documents
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
            (
                "MONTH_ZERO_LAG_MISSING:"
                f"{month_key}"
            )
        )

    best_score = (
        _safe_float(
            best.get(
                "alignment_score"
            )
        )
    )

    zero_score = (
        _safe_float(
            zero.get(
                "alignment_score"
            )
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

    month_start = pd.Timestamp(
        frozen_month[
            "time"
        ].min()
    )

    month_end = pd.Timestamp(
        frozen_month[
            "time"
        ].max()
    )

    eligible = bool(
        int(
            best.get(
                "overlap_rows",
                0,
            )
        )
        >=
        MIN_MONTH_OVERLAP_ROWS
    )

    return {
        "month": (
            month_key
        ),
        "frozen_rows": int(
            len(
                frozen_month
            )
        ),
        "time_start": (
            month_start.isoformat()
        ),
        "time_end": (
            month_end.isoformat()
        ),
        "eligible": (
            eligible
        ),
        "selected_lag_seconds": int(
            best.get(
                "lag_seconds",
                0,
            )
        ),
        "selected_lag_hours": float(
            int(
                best.get(
                    "lag_seconds",
                    0,
                )
            )
            /
            3600.0
        ),
        "selected_alignment_score": (
            best_score
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
        "selected_overlap_rows": int(
            best.get(
                "overlap_rows",
                0,
            )
        ),
        "selected_strong_alignment": bool(
            best.get(
                "strong_alignment",
                False,
            )
        ),
        "zero_lag_alignment_score": (
            zero_score
        ),
        "alignment_score_gain_vs_zero": (
            score_gain
        ),
        "candidate_ranking": [
            {
                "rank": int(
                    index
                ),
                **document,
            }
            for index, document
            in enumerate(
                ranked,
                start=1,
            )
        ],
    }


def _aggregate_decision(
    month_documents: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
) -> dict[str, Any]:

    eligible = [
        document
        for document
        in month_documents
        if bool(
            document.get(
                "eligible",
                False,
            )
        )
    ]

    eligible_count = int(
        len(
            eligible
        )
    )

    selected_lags = [
        int(
            document.get(
                "selected_lag_seconds",
                0,
            )
        )
        for document
        in eligible
    ]

    counts = Counter(
        selected_lags
    )

    lag_counts = {
        str(
            lag
        ): int(
            counts.get(
                lag,
                0,
            )
        )
        for lag
        in CANDIDATE_LAGS_SECONDS
    }

    if eligible_count == 0:

        dominant_lag = None

        dominant_count = 0

    else:

        (
            dominant_lag,
            dominant_count,
        ) = (
            counts.most_common(
                1
            )[
                0
            ]
        )

    dominant_share = (
        float(
            dominant_count
            /
            eligible_count
        )
        if eligible_count
        >
        0
        else
        None
    )

    minus_2_count = int(
        counts.get(
            -2
            *
            60
            *
            60,
            0,
        )
    )

    minus_3_count = int(
        counts.get(
            -3
            *
            60
            *
            60,
            0,
        )
    )

    minus_2_minus_3_count = (
        minus_2_count
        +
        minus_3_count
    )

    minus_2_minus_3_share = (
        float(
            minus_2_minus_3_count
            /
            eligible_count
        )
        if eligible_count
        >
        0
        else
        None
    )

    nonzero_count = sum(
        1
        for lag
        in selected_lags
        if lag
        !=
        0
    )

    nonzero_share = (
        float(
            nonzero_count
            /
            eligible_count
        )
        if eligible_count
        >
        0
        else
        None
    )

    selected_scores = [
        _safe_float(
            document.get(
                "selected_alignment_score"
            )
        )
        for document
        in eligible
    ]

    selected_body = [
        _safe_float(
            document.get(
                "selected_body_correlation"
            )
        )
        for document
        in eligible
    ]

    selected_delta = [
        _safe_float(
            document.get(
                "selected_close_delta_correlation"
            )
        )
        for document
        in eligible
    ]

    selected_direction = [
        _safe_float(
            document.get(
                "selected_candle_direction_agreement"
            )
        )
        for document
        in eligible
    ]

    selected_range = [
        _safe_float(
            document.get(
                "selected_range_correlation"
            )
        )
        for document
        in eligible
    ]

    median_score = (
        _median_finite(
            selected_scores
        )
    )

    median_body = (
        _median_finite(
            selected_body
        )
    )

    median_delta = (
        _median_finite(
            selected_delta
        )
    )

    median_direction = (
        _median_finite(
            selected_direction
        )
    )

    median_range = (
        _median_finite(
            selected_range
        )
    )

    strong_month_count = sum(
        1
        for document
        in eligible
        if bool(
            document.get(
                "selected_strong_alignment",
                False,
            )
        )
    )

    if (
        eligible_count
        <
        MIN_ELIGIBLE_MONTHS
    ):

        status = (
            "INSUFFICIENT_TEMPORAL_MONTHS"
        )

        reason = (
            "TOO_FEW_MONTHS_HAVE_REQUIRED_OVERLAP"
        )

        next_action = (
            "EXTEND_OR_REPAIR_CURRENT_BROKER_HISTORY"
        )

    elif (
        minus_2_minus_3_share
        is not None
        and
        minus_2_minus_3_share
        >=
        CONFIRMED_DOMINANCE_SHARE
        and
        minus_2_count
        >=
        MIN_DST_REGIME_MONTHS_EACH
        and
        minus_3_count
        >=
        MIN_DST_REGIME_MONTHS_EACH
        and
        median_score
        is not None
        and
        median_score
        >=
        MIN_CONFIRMED_MEDIAN_ALIGNMENT_SCORE
    ):

        status = (
            "DST_OR_SERVER_CLOCK_REGIME_PATTERN_CONFIRMED"
        )

        reason = (
            "MINUS_2H_AND_MINUS_3H_OFFSETS_DOMINATE_"
            "ACROSS_CHRONOLOGICAL_MONTHS"
        )

        next_action = (
            "BUILD_CAUSAL_DATE_AWARE_BROKER_TIME_MAPPING_"
            "FOR_RESEARCH_DOMAIN_AUDIT"
        )

    elif (
        dominant_lag
        is not None
        and
        dominant_lag
        !=
        0
        and
        dominant_share
        is not None
        and
        dominant_share
        >=
        CONFIRMED_DOMINANCE_SHARE
        and
        median_score
        is not None
        and
        median_score
        >=
        MIN_CONFIRMED_MEDIAN_ALIGNMENT_SCORE
    ):

        status = (
            "FIXED_CLOCK_OFFSET_TEMPORALLY_CONFIRMED"
        )

        reason = (
            "ONE_NONZERO_CLOCK_OFFSET_DOMINATES_"
            "ACROSS_CHRONOLOGICAL_MONTHS"
        )

        next_action = (
            "RERUN_M5_DOMAIN_SHIFT_WITH_CONFIRMED_"
            "FIXED_TIME_MAPPING"
        )

    elif (
        nonzero_share
        is not None
        and
        nonzero_share
        >=
        LIKELY_NONZERO_SHARE
        and
        median_score
        is not None
        and
        median_score
        >=
        MIN_LIKELY_MEDIAN_ALIGNMENT_SCORE
    ):

        status = (
            "NONZERO_CLOCK_OFFSET_TEMPORALLY_LIKELY"
        )

        reason = (
            "NONZERO_OFFSETS_DOMINATE_BUT_PATTERN_"
            "DOES_NOT_MEET_CONFIRMATION_CONTRACT"
        )

        next_action = (
            "INSPECT_MONTHLY_OFFSET_TRANSITIONS_BEFORE_"
            "APPLYING_TIME_MAPPING"
        )

    else:

        status = (
            "CLOCK_OFFSET_TEMPORALLY_UNSTABLE"
        )

        reason = (
            "MONTHLY_BEST_OFFSETS_DO_NOT_FORM_A_"
            "STABLE_FIXED_OR_DST_LIKE_PATTERN"
        )

        next_action = (
            "AUDIT_RAW_TIMESTAMP_PROVENANCE_AND_"
            "BROKER_BAR_TIME_SEMANTICS"
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "eligible_month_count": (
            eligible_count
        ),
        "lag_selection_counts": (
            lag_counts
        ),
        "dominant_lag_seconds": (
            int(
                dominant_lag
            )
            if dominant_lag
            is not None
            else None
        ),
        "dominant_lag_hours": (
            float(
                dominant_lag
                /
                3600.0
            )
            if dominant_lag
            is not None
            else None
        ),
        "dominant_lag_share": (
            dominant_share
        ),
        "minus_2h_month_count": (
            minus_2_count
        ),
        "minus_3h_month_count": (
            minus_3_count
        ),
        "minus_2h_minus_3h_share": (
            minus_2_minus_3_share
        ),
        "nonzero_month_count": (
            nonzero_count
        ),
        "nonzero_month_share": (
            nonzero_share
        ),
        "strong_alignment_month_count": int(
            strong_month_count
        ),
        "median_selected_alignment_score": (
            median_score
        ),
        "median_selected_body_correlation": (
            median_body
        ),
        "median_selected_close_delta_correlation": (
            median_delta
        ),
        "median_selected_direction_agreement": (
            median_direction
        ),
        "median_selected_range_correlation": (
            median_range
        ),
        "feature_domain_shift_verdict_allowed": (
            False
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
        "SOURCE_M5_DATASET_ID_MISMATCH",
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
        "SOURCE_M5_DATASET_SHA256_MISMATCH",
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
        "HISTORICAL_MANIFEST_ID_MISMATCH",
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
        "HISTORICAL_MANIFEST_SHA_MISMATCH",
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

    frozen_raw = (
        frozen_raw.loc[
            (
                frozen_raw[
                    "time"
                ]
                >=
                train_start
            )
            &
            (
                frozen_raw[
                    "time"
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
        not frozen_raw.empty,
        "FROZEN_RAW_TEMPORAL_WINDOW_EMPTY",
    )

    frozen_raw[
        "month_key"
    ] = (
        frozen_raw[
            "time"
        ]
        .dt
        .strftime(
            "%Y-%m"
        )
    )

    month_keys = sorted(
        str(
            value
        )
        for value
        in frozen_raw[
            "month_key"
        ].dropna().unique()
    )

    _require(
        bool(
            month_keys
        ),
        "NO_TEMPORAL_MONTHS_FOUND",
    )

    current_fetch_start = (
        train_start
        -
        pd.Timedelta(
            seconds=(
                CURRENT_HISTORY_BUFFER_SECONDS
            )
        )
    )

    current_fetch_end = (
        train_end
        +
        pd.Timedelta(
            seconds=(
                CURRENT_HISTORY_BUFFER_SECONDS
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

        month_documents: list[
            dict[str, Any]
        ] = []

        for month_key in (
            month_keys
        ):

            frozen_month = (
                frozen_raw.loc[
                    frozen_raw[
                        "month_key"
                    ]
                    ==
                    month_key
                ]
                .drop(
                    columns=[
                        "month_key"
                    ]
                )
                .copy()
                .reset_index(
                    drop=True
                )
            )

            if frozen_month.empty:
                continue

            month_documents.append(
                _month_diagnostic(
                    frozen_month,
                    current_raw,
                    month_key=(
                        month_key
                    ),
                )
            )

        decision = (
            _aggregate_decision(
                month_documents
            )
        )

        current_start = pd.Timestamp(
            current_raw[
                "time"
            ].min()
        )

        current_end = pd.Timestamp(
            current_raw[
                "time"
            ].max()
        )

        return {
            "valid": True,
            "reason": (
                "OK_XAUUSD_CURRENT_BROKER_M5_"
                "CLOCK_OFFSET_TEMPORAL_DIAGNOSTIC"
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
                    "TRAIN_ONLY_FOR_TEMPORAL_BOUNDARY"
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
                "m5_rows_loaded": int(
                    len(
                        current_raw
                    )
                ),
                "time_start": (
                    current_start.isoformat()
                ),
                "time_end": (
                    current_end.isoformat()
                ),
            },
            "temporal_policy": {
                "grouping": (
                    "CALENDAR_MONTH_UTC_AS_STORED"
                ),
                "candidate_lags_seconds": list(
                    CANDIDATE_LAGS_SECONDS
                ),
                "candidate_lags_hours": [
                    float(
                        value
                        /
                        3600.0
                    )
                    for value
                    in CANDIDATE_LAGS_SECONDS
                ],
                "minimum_month_overlap_rows": (
                    MIN_MONTH_OVERLAP_ROWS
                ),
                "minimum_eligible_months": (
                    MIN_ELIGIBLE_MONTHS
                ),
                "confirmed_dominance_share": (
                    CONFIRMED_DOMINANCE_SHARE
                ),
                "minimum_confirmed_median_alignment_score": (
                    MIN_CONFIRMED_MEDIAN_ALIGNMENT_SCORE
                ),
                "minimum_likely_median_alignment_score": (
                    MIN_LIKELY_MEDIAN_ALIGNMENT_SCORE
                ),
                "dst_candidate_offsets": [
                    -3.0,
                    -2.0,
                ],
                "selection_metrics": [
                    "body_correlation",
                    "close_delta_correlation",
                    "candle_direction_agreement",
                    "range_correlation",
                ],
            },
            "decision": (
                decision
            ),
            "monthly_diagnostics": (
                month_documents
            ),
            "scientific_policy": {
                "train_loaded": (
                    True
                ),
                "train_used_only_for_temporal_boundary": (
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
                "if_dst_or_server_clock_regime_confirmed": (
                    "BUILD_DATE_AWARE_RESEARCH_TIME_MAPPING_"
                    "THEN_RERUN_M5_DOMAIN_SHIFT"
                ),
                "if_fixed_clock_offset_confirmed": (
                    "RERUN_M5_DOMAIN_SHIFT_WITH_FIXED_TIME_MAPPING"
                ),
                "if_nonzero_offset_temporally_likely": (
                    "INSPECT_MONTHLY_OFFSET_TRANSITIONS"
                ),
                "if_temporally_unstable": (
                    "AUDIT_RAW_TIMESTAMP_PROVENANCE_AND_"
                    "BROKER_BAR_TIME_SEMANTICS"
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
                        "CLOCK_OFFSET_TEMPORAL_DIAGNOSTIC_FAILED"
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