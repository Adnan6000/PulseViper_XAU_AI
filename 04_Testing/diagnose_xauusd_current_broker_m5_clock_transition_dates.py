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
    "XAUUSD_CURRENT_BROKER_M5_CLOCK_TRANSITION_DATES_V1"
)

TEMPORAL_MODULE_NAME = (
    "04_Testing."
    "diagnose_xauusd_current_broker_m5_clock_offset_temporal"
)

M5_SECONDS = 300

OFFSET_MINUS_3H = -3 * 60 * 60

OFFSET_MINUS_2H = -2 * 60 * 60

CANDIDATE_LAGS_SECONDS = (
    OFFSET_MINUS_3H,
    OFFSET_MINUS_2H,
)

CURRENT_HISTORY_BUFFER_SECONDS = (
    4 * 60 * 60
)

MIN_DAILY_OVERLAP_ROWS = 120

MIN_DAILY_ALIGNMENT_SCORE = 0.70

MIN_DAILY_SCORE_GAP = 0.20

MIN_CONFIDENT_DAY_SHARE = 0.70

MAX_TRADING_DAY_TRANSITION_GAP_DAYS = 5

MIN_CONFIRMED_TRANSITIONS = 2


temporal_module: Any = importlib.import_module(
    TEMPORAL_MODULE_NAME
)

clock_module: Any = (
    temporal_module.clock_module
)

raw_module: Any = (
    temporal_module.raw_module
)

audit: Any = (
    temporal_module.audit
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


def _compact_lag_document(
    document: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    lag_seconds = int(
        document.get(
            "lag_seconds",
            0,
        )
    )

    score = (
        clock_module
        ._alignment_score(
            document
        )
    )

    return {
        "lag_seconds": (
            lag_seconds
        ),
        "lag_hours": float(
            lag_seconds
            /
            3600.0
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
        "strong_alignment": bool(
            clock_module
            ._strong_alignment(
                document
            )
        ),
    }


def _candidate_sort_key(
    document: Mapping[
        str,
        Any,
    ],
) -> tuple[
    float,
    float,
    float,
    float,
    int,
]:

    score = (
        _safe_float(
            document.get(
                "alignment_score"
            )
        )
    )

    body = (
        _safe_float(
            document.get(
                "body_correlation"
            )
        )
    )

    close_delta = (
        _safe_float(
            document.get(
                "close_delta_correlation"
            )
        )
    )

    direction = (
        _safe_float(
            document.get(
                "candle_direction_agreement"
            )
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
        int(
            document.get(
                "overlap_rows",
                0,
            )
        ),
    )


def _daily_diagnostic(
    frozen_day: pd.DataFrame,
    current_raw: pd.DataFrame,
    *,
    date_key: str,
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
                frozen_day,
                current_raw,
                lag_seconds=(
                    lag_seconds
                ),
            )
        )

        candidate_documents.append(
            _compact_lag_document(
                full
            )
        )

    ranked = sorted(
        candidate_documents,
        key=_candidate_sort_key,
        reverse=True,
    )

    _require(
        len(
            ranked
        )
        ==
        2,
        (
            "UNEXPECTED_DAILY_CANDIDATE_COUNT:"
            f"{date_key}:"
            f"{len(ranked)}"
        ),
    )

    best = (
        ranked[
            0
        ]
    )

    second = (
        ranked[
            1
        ]
    )

    best_score = (
        _safe_float(
            best.get(
                "alignment_score"
            )
        )
    )

    second_score = (
        _safe_float(
            second.get(
                "alignment_score"
            )
        )
    )

    score_gap: (
        float
        |
        None
    ) = None

    if (
        best_score is not None
        and
        second_score is not None
    ):

        score_gap = float(
            best_score
            -
            second_score
        )

    best_overlap = int(
        best.get(
            "overlap_rows",
            0,
        )
    )

    confident = bool(
        best_overlap
        >=
        MIN_DAILY_OVERLAP_ROWS
        and
        best_score
        is not None
        and
        best_score
        >=
        MIN_DAILY_ALIGNMENT_SCORE
        and
        score_gap
        is not None
        and
        score_gap
        >=
        MIN_DAILY_SCORE_GAP
    )

    day_start = pd.Timestamp(
        frozen_day[
            "time"
        ].min()
    )

    day_end = pd.Timestamp(
        frozen_day[
            "time"
        ].max()
    )

    return {
        "date": (
            date_key
        ),
        "frozen_rows": int(
            len(
                frozen_day
            )
        ),
        "time_start": (
            day_start.isoformat()
        ),
        "time_end": (
            day_end.isoformat()
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
        "alternative_lag_seconds": int(
            second.get(
                "lag_seconds",
                0,
            )
        ),
        "alternative_lag_hours": float(
            int(
                second.get(
                    "lag_seconds",
                    0,
                )
            )
            /
            3600.0
        ),
        "alternative_alignment_score": (
            second_score
        ),
        "alignment_score_gap": (
            score_gap
        ),
        "selected_overlap_rows": (
            best_overlap
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
        "selected_strong_alignment": bool(
            best.get(
                "strong_alignment",
                False,
            )
        ),
        "confident": (
            confident
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


def _confident_days(
    daily_documents: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
) -> list[
    Mapping[
        str,
        Any,
    ]
]:

    return [
        document
        for document
        in daily_documents
        if bool(
            document.get(
                "confident",
                False,
            )
        )
    ]


def _detect_transitions(
    daily_documents: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
) -> list[dict[str, Any]]:

    confident = (
        _confident_days(
            daily_documents
        )
    )

    transitions: list[
        dict[str, Any]
    ] = []

    if len(
        confident
    ) < 2:

        return transitions

    for index in range(
        1,
        len(
            confident
        ),
    ):

        previous = (
            confident[
                index
                -
                1
            ]
        )

        current = (
            confident[
                index
            ]
        )

        previous_lag = int(
            previous.get(
                "selected_lag_seconds",
                0,
            )
        )

        current_lag = int(
            current.get(
                "selected_lag_seconds",
                0,
            )
        )

        if (
            previous_lag
            ==
            current_lag
        ):

            continue

        previous_date = pd.Timestamp(
            str(
                previous[
                    "date"
                ]
            )
        )

        current_date = pd.Timestamp(
            str(
                current[
                    "date"
                ]
            )
        )

        calendar_gap_days = int(
            (
                current_date
                -
                previous_date
            ).days
        )

        transitions.append(
            {
                "from_lag_seconds": (
                    previous_lag
                ),
                "from_lag_hours": float(
                    previous_lag
                    /
                    3600.0
                ),
                "to_lag_seconds": (
                    current_lag
                ),
                "to_lag_hours": float(
                    current_lag
                    /
                    3600.0
                ),
                "last_confident_date_old_regime": (
                    str(
                        previous[
                            "date"
                        ]
                    )
                ),
                "first_confident_date_new_regime": (
                    str(
                        current[
                            "date"
                        ]
                    )
                ),
                "calendar_gap_days": (
                    calendar_gap_days
                ),
                "transition_bracket_is_tight": bool(
                    calendar_gap_days
                    <=
                    MAX_TRADING_DAY_TRANSITION_GAP_DAYS
                ),
                "old_regime_alignment_score": (
                    previous.get(
                        "selected_alignment_score"
                    )
                ),
                "new_regime_alignment_score": (
                    current.get(
                        "selected_alignment_score"
                    )
                ),
                "old_regime_score_gap": (
                    previous.get(
                        "alignment_score_gap"
                    )
                ),
                "new_regime_score_gap": (
                    current.get(
                        "alignment_score_gap"
                    )
                ),
            }
        )

    return transitions


def _build_regimes(
    daily_documents: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
) -> list[dict[str, Any]]:

    confident = (
        _confident_days(
            daily_documents
        )
    )

    if not confident:

        return []

    regimes: list[
        dict[str, Any]
    ] = []

    current_lag = int(
        confident[
            0
        ].get(
            "selected_lag_seconds",
            0,
        )
    )

    current_documents: list[
        Mapping[
            str,
            Any,
        ]
    ] = [
        confident[
            0
        ]
    ]

    for document in (
        confident[
            1:
        ]
    ):

        lag = int(
            document.get(
                "selected_lag_seconds",
                0,
            )
        )

        if lag == current_lag:

            current_documents.append(
                document
            )

            continue

        regimes.append(
            _regime_document(
                current_lag,
                current_documents,
            )
        )

        current_lag = lag

        current_documents = [
            document
        ]

    regimes.append(
        _regime_document(
            current_lag,
            current_documents,
        )
    )

    return regimes


def _regime_document(
    lag_seconds: int,
    documents: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
) -> dict[str, Any]:

    _require(
        bool(
            documents
        ),
        "EMPTY_REGIME_DOCUMENTS",
    )

    scores = [
        _safe_float(
            document.get(
                "selected_alignment_score"
            )
        )
        for document
        in documents
    ]

    body = [
        _safe_float(
            document.get(
                "selected_body_correlation"
            )
        )
        for document
        in documents
    ]

    close_delta = [
        _safe_float(
            document.get(
                "selected_close_delta_correlation"
            )
        )
        for document
        in documents
    ]

    direction = [
        _safe_float(
            document.get(
                "selected_candle_direction_agreement"
            )
        )
        for document
        in documents
    ]

    range_values = [
        _safe_float(
            document.get(
                "selected_range_correlation"
            )
        )
        for document
        in documents
    ]

    return {
        "lag_seconds": (
            lag_seconds
        ),
        "lag_hours": float(
            lag_seconds
            /
            3600.0
        ),
        "first_confident_date": str(
            documents[
                0
            ][
                "date"
            ]
        ),
        "last_confident_date": str(
            documents[
                -1
            ][
                "date"
            ]
        ),
        "confident_trading_day_count": int(
            len(
                documents
            )
        ),
        "median_alignment_score": (
            _median_finite(
                scores
            )
        ),
        "median_body_correlation": (
            _median_finite(
                body
            )
        ),
        "median_close_delta_correlation": (
            _median_finite(
                close_delta
            )
        ),
        "median_direction_agreement": (
            _median_finite(
                direction
            )
        ),
        "median_range_correlation": (
            _median_finite(
                range_values
            )
        ),
    }


def _decision(
    daily_documents: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
    transitions: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
    regimes: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
) -> dict[str, Any]:

    total_days = int(
        len(
            daily_documents
        )
    )

    confident = (
        _confident_days(
            daily_documents
        )
    )

    confident_count = int(
        len(
            confident
        )
    )

    confident_share = (
        float(
            confident_count
            /
            total_days
        )
        if total_days
        >
        0
        else
        None
    )

    lag_counts = Counter(
        int(
            document.get(
                "selected_lag_seconds",
                0,
            )
        )
        for document
        in confident
    )

    only_expected_offsets = bool(
        confident
        and
        set(
            lag_counts.keys()
        )
        .issubset(
            set(
                CANDIDATE_LAGS_SECONDS
            )
        )
    )

    alternates_cleanly = bool(
        len(
            transitions
        )
        >=
        1
        and
        all(
            (
                int(
                    transition.get(
                        "from_lag_seconds",
                        0,
                    )
                ),
                int(
                    transition.get(
                        "to_lag_seconds",
                        0,
                    )
                ),
            )
            in {
                (
                    OFFSET_MINUS_3H,
                    OFFSET_MINUS_2H,
                ),
                (
                    OFFSET_MINUS_2H,
                    OFFSET_MINUS_3H,
                ),
            }
            for transition
            in transitions
        )
    )

    tight_transition_count = sum(
        1
        for transition
        in transitions
        if bool(
            transition.get(
                "transition_bracket_is_tight",
                False,
            )
        )
    )

    has_both_offsets = bool(
        lag_counts.get(
            OFFSET_MINUS_3H,
            0,
        )
        >
        0
        and
        lag_counts.get(
            OFFSET_MINUS_2H,
            0,
        )
        >
        0
    )

    if (
        confident_share
        is None
        or
        confident_share
        <
        MIN_CONFIDENT_DAY_SHARE
    ):

        status = (
            "INSUFFICIENT_DAILY_CLOCK_CONFIDENCE"
        )

        reason = (
            "TOO_FEW_TRADING_DAYS_HAVE_DECISIVE_"
            "MINUS_2H_OR_MINUS_3H_ALIGNMENT"
        )

        next_action = (
            "REVIEW_LOW_CONFIDENCE_DAYS_BEFORE_TIME_MAPPING"
        )

    elif (
        len(
            transitions
        )
        >=
        MIN_CONFIRMED_TRANSITIONS
        and
        has_both_offsets
        and
        only_expected_offsets
        and
        alternates_cleanly
        and
        tight_transition_count
        ==
        len(
            transitions
        )
    ):

        status = (
            "SEASONAL_CLOCK_TRANSITION_DATES_CONFIRMED"
        )

        reason = (
            "DAILY_ALIGNMENT_IDENTIFIES_REPEATED_"
            "MINUS_3H_TO_MINUS_2H_AND_MINUS_2H_TO_MINUS_3H_"
            "TRANSITIONS"
        )

        next_action = (
            "BUILD_CAUSAL_DATE_AWARE_RESEARCH_TIME_MAPPING_"
            "FROM_CONFIRMED_TRANSITION_BRACKETS"
        )

    elif (
        len(
            transitions
        )
        >=
        1
        and
        has_both_offsets
        and
        only_expected_offsets
        and
        alternates_cleanly
    ):

        status = (
            "SEASONAL_CLOCK_TRANSITIONS_PARTIALLY_CONFIRMED"
        )

        reason = (
            "EXPECTED_MINUS_2H_MINUS_3H_SWITCHING_EXISTS_"
            "BUT_AVAILABLE_WINDOW_DOES_NOT_LOCK_TWO_TIGHT_TRANSITIONS"
        )

        next_action = (
            "USE_OBSERVED_TRANSITION_BRACKETS_FOR_RESEARCH_MAPPING_"
            "AND_REQUIRE_FORWARD_CONFIRMATION"
        )

    else:

        status = (
            "DAILY_CLOCK_TRANSITION_PATTERN_UNRESOLVED"
        )

        reason = (
            "DAILY_SELECTED_OFFSETS_DO_NOT_FORM_A_"
            "CLEAN_SEASONAL_SEQUENCE"
        )

        next_action = (
            "AUDIT_BROKER_BAR_TIMESTAMP_PROVENANCE"
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "trading_day_count": (
            total_days
        ),
        "confident_trading_day_count": (
            confident_count
        ),
        "confident_trading_day_share": (
            confident_share
        ),
        "selected_lag_counts_confident_days": {
            str(
                key
            ): int(
                value
            )
            for key, value
            in sorted(
                lag_counts.items()
            )
        },
        "minus_3h_confident_day_count": int(
            lag_counts.get(
                OFFSET_MINUS_3H,
                0,
            )
        ),
        "minus_2h_confident_day_count": int(
            lag_counts.get(
                OFFSET_MINUS_2H,
                0,
            )
        ),
        "transition_count": int(
            len(
                transitions
            )
        ),
        "tight_transition_count": int(
            tight_transition_count
        ),
        "regime_count": int(
            len(
                regimes
            )
        ),
        "has_both_expected_offsets": (
            has_both_offsets
        ),
        "only_expected_offsets_selected": (
            only_expected_offsets
        ),
        "transitions_alternate_cleanly": (
            alternates_cleanly
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
        "FROZEN_RAW_TRANSITION_WINDOW_EMPTY",
    )

    frozen_raw[
        "date_key"
    ] = (
        frozen_raw[
            "time"
        ]
        .dt
        .strftime(
            "%Y-%m-%d"
        )
    )

    date_keys = sorted(
        str(
            value
        )
        for value
        in frozen_raw[
            "date_key"
        ].dropna().unique()
    )

    _require(
        bool(
            date_keys
        ),
        "NO_FROZEN_TRADING_DATES",
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
            symbol_info is not None,
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

        daily_documents: list[
            dict[str, Any]
        ] = []

        for date_key in (
            date_keys
        ):

            frozen_day = (
                frozen_raw.loc[
                    frozen_raw[
                        "date_key"
                    ]
                    ==
                    date_key
                ]
                .drop(
                    columns=[
                        "date_key"
                    ]
                )
                .copy()
                .reset_index(
                    drop=True
                )
            )

            if frozen_day.empty:
                continue

            daily_documents.append(
                _daily_diagnostic(
                    frozen_day,
                    current_raw,
                    date_key=(
                        date_key
                    ),
                )
            )

        transitions = (
            _detect_transitions(
                daily_documents
            )
        )

        regimes = (
            _build_regimes(
                daily_documents
            )
        )

        decision = (
            _decision(
                daily_documents,
                transitions,
                regimes,
            )
        )

        transition_neighborhood_dates: set[
            str
        ] = set()

        for transition in (
            transitions
        ):

            old_date = pd.Timestamp(
                str(
                    transition[
                        "last_confident_date_old_regime"
                    ]
                )
            )

            new_date = pd.Timestamp(
                str(
                    transition[
                        "first_confident_date_new_regime"
                    ]
                )
            )

            for center in (
                old_date,
                new_date,
            ):

                for offset_days in range(
                    -3,
                    4,
                ):

                    transition_neighborhood_dates.add(
                        (
                            center
                            +
                            pd.Timedelta(
                                days=offset_days
                            )
                        )
                        .strftime(
                            "%Y-%m-%d"
                        )
                    )

        transition_neighborhood = [
            document
            for document
            in daily_documents
            if str(
                document.get(
                    "date",
                    "",
                )
            )
            in
            transition_neighborhood_dates
        ]

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
                "CLOCK_TRANSITION_DATES_DIAGNOSTIC"
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
            "transition_policy": {
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
                "grouping": (
                    "UTC_CALENDAR_DATE_AS_STORED"
                ),
                "minimum_daily_overlap_rows": (
                    MIN_DAILY_OVERLAP_ROWS
                ),
                "minimum_daily_alignment_score": (
                    MIN_DAILY_ALIGNMENT_SCORE
                ),
                "minimum_daily_score_gap": (
                    MIN_DAILY_SCORE_GAP
                ),
                "minimum_confident_day_share": (
                    MIN_CONFIDENT_DAY_SHARE
                ),
                "maximum_transition_gap_calendar_days": (
                    MAX_TRADING_DAY_TRANSITION_GAP_DAYS
                ),
                "minimum_confirmed_transitions": (
                    MIN_CONFIRMED_TRANSITIONS
                ),
                "month_names_hardcoded": (
                    False
                ),
                "transition_dates_hardcoded": (
                    False
                ),
                "offsets_discovered_from_prior_train_only_diagnostic": (
                    True
                ),
            },
            "decision": (
                decision
            ),
            "regimes": (
                regimes
            ),
            "transitions": (
                transitions
            ),
            "transition_neighborhood_daily_diagnostics": (
                transition_neighborhood
            ),
            "daily_summary": {
                "trading_day_count": int(
                    len(
                        daily_documents
                    )
                ),
                "confident_day_count": int(
                    sum(
                        1
                        for document
                        in daily_documents
                        if bool(
                            document.get(
                                "confident",
                                False,
                            )
                        )
                    )
                ),
            },
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
                "if_seasonal_transition_dates_confirmed": (
                    "BUILD_CAUSAL_DATE_AWARE_RESEARCH_TIME_MAPPING_"
                    "AND_RERUN_M5_DOMAIN_SHIFT"
                ),
                "if_partially_confirmed": (
                    "FREEZE_OBSERVED_TRANSITIONS_FOR_RESEARCH_ONLY_"
                    "AND_REQUIRE_FORWARD_CONFIRMATION"
                ),
                "if_unresolved": (
                    "AUDIT_BROKER_BAR_TIMESTAMP_PROVENANCE"
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
                        "CLOCK_TRANSITION_DATES_DIAGNOSTIC_FAILED"
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