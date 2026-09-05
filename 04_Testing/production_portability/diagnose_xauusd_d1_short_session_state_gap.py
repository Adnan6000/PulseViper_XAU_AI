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


ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


ANALYSIS_VERSION = (
    "XAUUSD_D1_SHORT_SESSION_STATE_GAP_V1"
)

FULL_AUDIT_MODULE = (
    "04_Testing."
    "analyze_xauusd_current_broker_full_mtf_portability"
)

FROZEN_D1_SOURCE_MODULE = (
    "04_Testing."
    "diagnose_xauusd_frozen_d1_source_aggregation"
)

FROZEN_D1_REPLAY_MODULE = (
    "04_Testing."
    "diagnose_xauusd_frozen_d1_feature_state_replay"
)


full: Any = importlib.import_module(
    FULL_AUDIT_MODULE
)

source: Any = importlib.import_module(
    FROZEN_D1_SOURCE_MODULE
)

replay: Any = importlib.import_module(
    FROZEN_D1_REPLAY_MODULE
)

base: Any = (
    full.base
)

mapped: Any = (
    full.mapped
)


CANONICAL_DATETIME_DTYPE = (
    full.CANONICAL_DATETIME_DTYPE
)


CONFIRMED_D1_CLOSE_HOUR_UTC = 0

CONFIRMED_D1_AVAILABLE_LAG_DAYS = 1


SHORT_SESSION_MAX_H1_BARS = 5

PREVIOUS_RECONSTRUCTION_MIN_H1_BARS = 6


MIN_REQUIRED_D1_STATES = 200

MIN_SHORT_STATE_COUNT_FOR_MATERIAL_GAP = 20

MIN_SHORT_SOURCE_RECONSTRUCTION_MATCH_FRACTION = 0.90


RAW_PRICE_COLUMNS = (
    "open",
    "high",
    "low",
    "close",
)


PRICE_ABSOLUTE_TOLERANCE = 1e-6


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


def _technical_features(
    manifest: Mapping[
        str,
        Any,
    ],
) -> list[str]:

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

    features = [
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
            features
        )
        ==
        full.EXPECTED_TECHNICAL_COUNT_PER_TIMEFRAME,
        (
            "D1_TECHNICAL_FEATURE_COUNT_MISMATCH:"
            f"{len(features)}"
        ),
    )

    return (
        features
    )


def _session_census(
    h1: pd.DataFrame,
) -> pd.DataFrame:

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
            in h1.columns
        )
    )

    _require(
        not missing,
        (
            "H1_SESSION_CENSUS_COLUMNS_MISSING:"
            f"{missing}"
        ),
    )

    working = (
        h1[
            [
                "time",
                *RAW_PRICE_COLUMNS,
            ]
        ]
        .copy()
    )

    working[
        "time"
    ] = (
        _canonical_time(
            working[
                "time"
            ]
        )
    )

    working[
        "session_bar_time"
    ] = (
        working[
            "time"
        ]
        .dt
        .floor(
            "D"
        )
    )

    grouped = (
        working
        .groupby(
            "session_bar_time",
            sort=True,
            observed=True,
        )
        .agg(
            open=(
                "open",
                "first",
            ),
            high=(
                "high",
                "max",
            ),
            low=(
                "low",
                "min",
            ),
            close=(
                "close",
                "last",
            ),
            h1_bar_count=(
                "time",
                "count",
            ),
            first_h1_time=(
                "time",
                "min",
            ),
            last_h1_time=(
                "time",
                "max",
            ),
        )
        .reset_index()
    )

    grouped[
        "session_bar_time"
    ] = (
        _canonical_time(
            grouped[
                "session_bar_time"
            ]
        )
    )

    grouped[
        "first_h1_time"
    ] = (
        _canonical_time(
            grouped[
                "first_h1_time"
            ]
        )
    )

    grouped[
        "last_h1_time"
    ] = (
        _canonical_time(
            grouped[
                "last_h1_time"
            ]
        )
    )

    grouped[
        "h1_bar_count"
    ] = pd.to_numeric(
        grouped[
            "h1_bar_count"
        ],
        errors="raise",
    ).astype(
        "int64"
    )

    duplicate_sessions = int(
        grouped[
            "session_bar_time"
        ]
        .duplicated(
            keep=False
        )
        .sum()
    )

    _require(
        duplicate_sessions
        ==
        0,
        (
            "H1_SESSION_CENSUS_DUPLICATES:"
            f"{duplicate_sessions}"
        ),
    )

    return (
        grouped
        .sort_values(
            "session_bar_time"
        )
        .reset_index(
            drop=True
        )
    )


def _clock_map_current_h1(
    raw_h1: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

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
        canonical_time,
        mapping_meta,
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
            canonical_time
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

    duplicate_rows = int(
        current[
            "time"
        ]
        .duplicated(
            keep=False
        )
        .sum()
    )

    _require(
        duplicate_rows
        ==
        0,
        (
            "CURRENT_CANONICAL_H1_DUPLICATES:"
            f"{duplicate_rows}"
        ),
    )

    return (
        current,
        {
            **mapping_meta,
            "duplicate_canonical_h1_rows": (
                duplicate_rows
            ),
        },
    )


def _required_state_table(
    *,
    frozen_states: pd.DataFrame,
) -> pd.DataFrame:

    required = (
        frozen_states[
            [
                "frozen_available_time"
            ]
        ]
        .copy()
    )

    required[
        "required_d1_bar_time"
    ] = (
        required[
            "frozen_available_time"
        ]
        -
        pd.Timedelta(
            days=(
                CONFIRMED_D1_AVAILABLE_LAG_DAYS
            )
        )
    )

    required[
        "required_d1_bar_time"
    ] = (
        _canonical_time(
            required[
                "required_d1_bar_time"
            ]
        )
    )

    required = (
        required
        .sort_values(
            "required_d1_bar_time"
        )
        .reset_index(
            drop=True
        )
    )

    duplicate_rows = int(
        required[
            "required_d1_bar_time"
        ]
        .duplicated(
            keep=False
        )
        .sum()
    )

    _require(
        duplicate_rows
        ==
        0,
        (
            "REQUIRED_D1_BAR_TIME_DUPLICATES:"
            f"{duplicate_rows}"
        ),
    )

    return (
        required
    )


def _frozen_d1_table(
    frozen_d1: pd.DataFrame,
) -> pd.DataFrame:

    result = (
        frozen_d1[
            [
                "time",
                *RAW_PRICE_COLUMNS,
            ]
        ]
        .copy()
        .rename(
            columns={
                "time": (
                    "required_d1_bar_time"
                ),
                "open": (
                    "frozen_d1_open"
                ),
                "high": (
                    "frozen_d1_high"
                ),
                "low": (
                    "frozen_d1_low"
                ),
                "close": (
                    "frozen_d1_close"
                ),
            }
        )
    )

    result[
        "required_d1_bar_time"
    ] = (
        _canonical_time(
            result[
                "required_d1_bar_time"
            ]
        )
    )

    return (
        result
    )


def _rename_census(
    census: pd.DataFrame,
    *,
    prefix: str,
) -> pd.DataFrame:

    return (
        census.rename(
            columns={
                "session_bar_time": (
                    "required_d1_bar_time"
                ),
                "open": (
                    f"{prefix}_open"
                ),
                "high": (
                    f"{prefix}_high"
                ),
                "low": (
                    f"{prefix}_low"
                ),
                "close": (
                    f"{prefix}_close"
                ),
                "h1_bar_count": (
                    f"{prefix}_h1_bar_count"
                ),
                "first_h1_time": (
                    f"{prefix}_first_h1_time"
                ),
                "last_h1_time": (
                    f"{prefix}_last_h1_time"
                ),
            }
        )
    )


def _price_match_fraction(
    frame: pd.DataFrame,
    *,
    left_prefix: str,
    right_prefix: str,
    mask: pd.Series,
) -> dict[str, Any]:

    working = (
        frame.loc[
            mask
        ]
        .copy()
    )

    row_count = int(
        len(
            working
        )
    )

    if (
        row_count
        ==
        0
    ):

        return {
            "rows": 0,
            "all_ohlc_match_rows": 0,
            "all_ohlc_match_fraction": None,
            "median_absolute_close_difference": None,
            "median_absolute_body_difference": None,
        }

    row_match = np.ones(
        row_count,
        dtype=bool,
    )

    for column in (
        RAW_PRICE_COLUMNS
    ):

        left = pd.to_numeric(
            working[
                (
                    left_prefix
                    +
                    "_"
                    +
                    column
                )
            ],
            errors="coerce",
        ).to_numpy(
            dtype=np.float64
        )

        right = pd.to_numeric(
            working[
                (
                    right_prefix
                    +
                    "_"
                    +
                    column
                )
            ],
            errors="coerce",
        ).to_numpy(
            dtype=np.float64
        )

        finite = (
            np.isfinite(
                left
            )
            &
            np.isfinite(
                right
            )
        )

        matched = (
            finite
            &
            np.isclose(
                left,
                right,
                rtol=0.0,
                atol=(
                    PRICE_ABSOLUTE_TOLERANCE
                ),
            )
        )

        row_match &= (
            matched
        )

    close_left = pd.to_numeric(
        working[
            (
                left_prefix
                +
                "_close"
            )
        ],
        errors="coerce",
    ).to_numpy(
        dtype=np.float64
    )

    close_right = pd.to_numeric(
        working[
            (
                right_prefix
                +
                "_close"
            )
        ],
        errors="coerce",
    ).to_numpy(
        dtype=np.float64
    )

    open_left = pd.to_numeric(
        working[
            (
                left_prefix
                +
                "_open"
            )
        ],
        errors="coerce",
    ).to_numpy(
        dtype=np.float64
    )

    open_right = pd.to_numeric(
        working[
            (
                right_prefix
                +
                "_open"
            )
        ],
        errors="coerce",
    ).to_numpy(
        dtype=np.float64
    )

    finite_close = (
        np.isfinite(
            close_left
        )
        &
        np.isfinite(
            close_right
        )
    )

    finite_body = (
        finite_close
        &
        np.isfinite(
            open_left
        )
        &
        np.isfinite(
            open_right
        )
    )

    median_close_difference: (
        float
        |
        None
    ) = None

    median_body_difference: (
        float
        |
        None
    ) = None

    if bool(
        finite_close.any()
    ):

        median_close_difference = float(
            np.median(
                np.abs(
                    close_left[
                        finite_close
                    ]
                    -
                    close_right[
                        finite_close
                    ]
                )
            )
        )

    if bool(
        finite_body.any()
    ):

        left_body = (
            close_left[
                finite_body
            ]
            -
            open_left[
                finite_body
            ]
        )

        right_body = (
            close_right[
                finite_body
            ]
            -
            open_right[
                finite_body
            ]
        )

        median_body_difference = float(
            np.median(
                np.abs(
                    left_body
                    -
                    right_body
                )
            )
        )

    matched_rows = int(
        row_match.sum()
    )

    return {
        "rows": (
            row_count
        ),
        "all_ohlc_match_rows": (
            matched_rows
        ),
        "all_ohlc_match_fraction": float(
            matched_rows
            /
            row_count
        ),
        "median_absolute_close_difference": (
            median_close_difference
        ),
        "median_absolute_body_difference": (
            median_body_difference
        ),
    }


def _count_distribution(
    values: pd.Series,
) -> dict[str, int]:

    numeric = pd.to_numeric(
        values,
        errors="coerce",
    )

    finite_values = [
        int(
            value
        )
        for value
        in numeric.dropna().tolist()
    ]

    counts = Counter(
        finite_values
    )

    return {
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
            counts.items()
        )
    }


def _decision(
    *,
    state_count: int,
    frozen_short_count: int,
    frozen_ge6_count: int,
    current_short_count: int,
    current_ge6_count: int,
    current_missing_count: int,
    frozen_short_reconstruction: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    short_match_fraction = (
        _safe_float(
            frozen_short_reconstruction.get(
                "all_ohlc_match_fraction"
            )
        )
    )

    previous_filter_removed_count = (
        state_count
        -
        current_ge6_count
    )

    if (
        state_count
        <
        MIN_REQUIRED_D1_STATES
    ):

        status = (
            "D1_SHORT_SESSION_DIAGNOSTIC_INSUFFICIENT_STATES"
        )

        reason = (
            "TOO_FEW_REQUIRED_FROZEN_D1_STATES_FOR_"
            "SHORT_SESSION_PROVENANCE"
        )

        next_action = (
            "RESOLVE_FROZEN_D1_STATE_WINDOW"
        )

    elif (
        frozen_short_count
        >=
        MIN_SHORT_STATE_COUNT_FOR_MATERIAL_GAP
        and
        short_match_fraction
        is not None
        and
        short_match_fraction
        >=
        MIN_SHORT_SOURCE_RECONSTRUCTION_MATCH_FRACTION
    ):

        status = (
            "D1_SHORT_SESSION_STATE_GAP_CONFIRMED"
        )

        reason = (
            "FROZEN_TRAIN_D1_STATE_SEQUENCE_CONTAINS_"
            "MATERIAL_1_TO_5_H1_BAR_SESSIONS_THAT_THE_"
            "PREVIOUS_CURRENT_RECONSTRUCTION_FILTER_EXCLUDES"
        )

        next_action = (
            "REBUILD_CURRENT_00UTC_D1_WITHOUT_THE_"
            "SIX_H1_BAR_MINIMUM_AND_COMPARE_THE_FULL_"
            "309_STATE_SEQUENCE"
        )

    elif (
        frozen_short_count
        >=
        MIN_SHORT_STATE_COUNT_FOR_MATERIAL_GAP
    ):

        status = (
            "D1_SHORT_SESSIONS_PRESENT_BUT_SOURCE_RECONSTRUCTION_UNRESOLVED"
        )

        reason = (
            "FROZEN_D1_HAS_MANY_SHORT_SESSIONS_BUT_"
            "FROZEN_H1_AGGREGATION_DOES_NOT_EXACTLY_"
            "REPRODUCE_THEM"
        )

        next_action = (
            "INSPECT_FROZEN_NATIVE_D1_SHORT_SESSION_"
            "INGEST_PROVENANCE"
        )

    else:

        status = (
            "D1_SHORT_SESSION_STATE_GAP_NOT_SUFFICIENT"
        )

        reason = (
            "TOO_FEW_FROZEN_SHORT_D1_SESSIONS_TO_"
            "EXPLAIN_THE_D1_STATE_COUNT_AND_FEATURE_GAP"
        )

        next_action = (
            "ISOLATE_OTHER_D1_STATE_SEQUENCE_DIFFERENCES"
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "required_frozen_d1_state_count": (
            state_count
        ),
        "frozen_short_session_state_count": (
            frozen_short_count
        ),
        "frozen_ge6_session_state_count": (
            frozen_ge6_count
        ),
        "current_short_session_state_count": (
            current_short_count
        ),
        "current_ge6_session_state_count": (
            current_ge6_count
        ),
        "current_missing_required_session_count": (
            current_missing_count
        ),
        "states_removed_by_previous_current_ge6_filter": (
            previous_filter_removed_count
        ),
        "frozen_short_session_ohlc_match_fraction": (
            short_match_fraction
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
        _technical_features(
            manifest
        )
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

    (
        frozen_states,
        frozen_state_meta,
    ) = (
        replay
        ._frozen_d1_states(
            frozen_train=(
                frozen_train
            ),
            technical_features=(
                technical_features
            ),
        )
    )

    required_states = (
        _required_state_table(
            frozen_states=(
                frozen_states
            )
        )
    )

    state_count = int(
        len(
            required_states
        )
    )

    _require(
        state_count
        >=
        MIN_REQUIRED_D1_STATES,
        (
            "REQUIRED_D1_STATE_COUNT_TOO_SMALL:"
            f"{state_count}"
        ),
    )

    required_start = pd.Timestamp(
        required_states[
            "required_d1_bar_time"
        ].min()
    )

    required_end = pd.Timestamp(
        required_states[
            "required_d1_bar_time"
        ].max()
    )

    h1_snapshot = (
        source
        ._snapshot_document(
            manifest,
            "H1",
        )
    )

    d1_snapshot = (
        source
        ._snapshot_document(
            manifest,
            "D1",
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

    frozen_h1_window = (
        frozen_h1.loc[
            (
                frozen_h1[
                    "time"
                ]
                >=
                (
                    required_start
                    -
                    pd.Timedelta(
                        days=1
                    )
                )
            )
            &
            (
                frozen_h1[
                    "time"
                ]
                <
                (
                    required_end
                    +
                    pd.Timedelta(
                        days=2
                    )
                )
            )
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    frozen_h1_census = (
        _session_census(
            frozen_h1_window
        )
    )

    frozen_d1_table = (
        _frozen_d1_table(
            frozen_d1
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
            required_start
            -
            pd.Timedelta(
                days=3
            )
        )

        fetch_end = (
            required_end
            +
            pd.Timedelta(
                days=3
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

        raw_current_h1[
            "time"
        ] = (
            _canonical_time(
                raw_current_h1[
                    "time"
                ]
            )
        )

        (
            current_h1,
            clock_meta,
        ) = (
            _clock_map_current_h1(
                raw_current_h1
            )
        )

        current_h1_census = (
            _session_census(
                current_h1
            )
        )

        state_table = (
            required_states
            .merge(
                frozen_d1_table,
                on="required_d1_bar_time",
                how="left",
                validate="one_to_one",
            )
            .merge(
                _rename_census(
                    frozen_h1_census,
                    prefix="frozen_h1",
                ),
                on="required_d1_bar_time",
                how="left",
                validate="one_to_one",
            )
            .merge(
                _rename_census(
                    current_h1_census,
                    prefix="current_h1",
                ),
                on="required_d1_bar_time",
                how="left",
                validate="one_to_one",
            )
            .sort_values(
                "required_d1_bar_time"
            )
            .reset_index(
                drop=True
            )
        )

        frozen_d1_present = (
            state_table[
                "frozen_d1_close"
            ]
            .notna()
        )

        _require(
            bool(
                frozen_d1_present.all()
            ),
            (
                "FROZEN_D1_REQUIRED_STATE_BARS_MISSING:"
                f"{int((~frozen_d1_present).sum())}"
            ),
        )

        frozen_count = pd.to_numeric(
            state_table[
                "frozen_h1_h1_bar_count"
            ],
            errors="coerce",
        )

        current_count = pd.to_numeric(
            state_table[
                "current_h1_h1_bar_count"
            ],
            errors="coerce",
        )

        frozen_missing_mask = (
            frozen_count.isna()
        )

        current_missing_mask = (
            current_count.isna()
        )

        frozen_short_mask = (
            frozen_count.notna()
            &
            (
                frozen_count
                >=
                1
            )
            &
            (
                frozen_count
                <=
                SHORT_SESSION_MAX_H1_BARS
            )
        )

        frozen_ge6_mask = (
            frozen_count
            >=
            PREVIOUS_RECONSTRUCTION_MIN_H1_BARS
        )

        current_short_mask = (
            current_count.notna()
            &
            (
                current_count
                >=
                1
            )
            &
            (
                current_count
                <=
                SHORT_SESSION_MAX_H1_BARS
            )
        )

        current_ge6_mask = (
            current_count
            >=
            PREVIOUS_RECONSTRUCTION_MIN_H1_BARS
        )

        frozen_short_count = int(
            frozen_short_mask.sum()
        )

        frozen_ge6_count = int(
            frozen_ge6_mask.sum()
        )

        current_short_count = int(
            current_short_mask.sum()
        )

        current_ge6_count = int(
            current_ge6_mask.sum()
        )

        frozen_missing_count = int(
            frozen_missing_mask.sum()
        )

        current_missing_count = int(
            current_missing_mask.sum()
        )

        frozen_short_reconstruction = (
            _price_match_fraction(
                state_table,
                left_prefix="frozen_d1",
                right_prefix="frozen_h1",
                mask=(
                    frozen_short_mask
                ),
            )
        )

        frozen_ge6_reconstruction = (
            _price_match_fraction(
                state_table,
                left_prefix="frozen_d1",
                right_prefix="frozen_h1",
                mask=(
                    frozen_ge6_mask
                ),
            )
        )

        current_all_present_reconstruction = (
            _price_match_fraction(
                state_table,
                left_prefix="frozen_d1",
                right_prefix="current_h1",
                mask=(
                    current_count.notna()
                ),
            )
        )

        current_short_reconstruction = (
            _price_match_fraction(
                state_table,
                left_prefix="frozen_d1",
                right_prefix="current_h1",
                mask=(
                    current_short_mask
                ),
            )
        )

        current_ge6_reconstruction = (
            _price_match_fraction(
                state_table,
                left_prefix="frozen_d1",
                right_prefix="current_h1",
                mask=(
                    current_ge6_mask
                ),
            )
        )

        decision = (
            _decision(
                state_count=(
                    state_count
                ),
                frozen_short_count=(
                    frozen_short_count
                ),
                frozen_ge6_count=(
                    frozen_ge6_count
                ),
                current_short_count=(
                    current_short_count
                ),
                current_ge6_count=(
                    current_ge6_count
                ),
                current_missing_count=(
                    current_missing_count
                ),
                frozen_short_reconstruction=(
                    frozen_short_reconstruction
                ),
            )
        )

        short_state_dates = [
            pd.Timestamp(
                value
            ).isoformat()
            for value
            in state_table.loc[
                frozen_short_mask,
                "required_d1_bar_time",
            ].tolist()
        ]

        current_missing_dates = [
            pd.Timestamp(
                value
            ).isoformat()
            for value
            in state_table.loc[
                current_missing_mask,
                "required_d1_bar_time",
            ].tolist()
        ]

        return {
            "valid": True,
            "reason": (
                "OK_XAUUSD_D1_SHORT_SESSION_STATE_GAP_DIAGNOSTIC"
            ),
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "research_scope": (
                "FROZEN_309_D1_STATE_SEQUENCE_VS_"
                "FROZEN_AND_CURRENT_00UTC_H1_SESSION_CENSUS_"
                "TRAIN_ONLY_NO_LABELS"
            ),
            "prerequisite_contract": {
                "frozen_d1_feature_state_replay_status": (
                    "FROZEN_D1_FEATURE_STATE_REPLAY_CONFIRMED"
                ),
                "confirmed_availability_shift_days": (
                    0
                ),
                "confirmed_generated_available_lag_minutes": (
                    1440
                ),
                "confirmed_d1_close_hour_utc": (
                    CONFIRMED_D1_CLOSE_HOUR_UTC
                ),
                "frozen_d1_exact_feature_replay_count": (
                    43
                ),
                "frozen_d1_exact_state_count": (
                    309
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
                "required_d1_state_count": (
                    state_count
                ),
                "state_time_start": (
                    pd.Timestamp(
                        required_states[
                            "required_d1_bar_time"
                        ].min()
                    ).isoformat()
                ),
                "state_time_end": (
                    pd.Timestamp(
                        required_states[
                            "required_d1_bar_time"
                        ].max()
                    ).isoformat()
                ),
                "frozen_state_meta": (
                    frozen_state_meta
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
                "canonical_h1_rows": int(
                    len(
                        current_h1
                    )
                ),
            },
            "confirmed_clock_mapping": (
                clock_meta
            ),
            "session_state_census": {
                "required_d1_state_count": (
                    state_count
                ),
                "previous_reconstruction_minimum_h1_bars": (
                    PREVIOUS_RECONSTRUCTION_MIN_H1_BARS
                ),
                "frozen_h1_missing_required_sessions": (
                    frozen_missing_count
                ),
                "frozen_h1_short_1_to_5_bar_sessions": (
                    frozen_short_count
                ),
                "frozen_h1_ge6_bar_sessions": (
                    frozen_ge6_count
                ),
                "current_h1_missing_required_sessions": (
                    current_missing_count
                ),
                "current_h1_short_1_to_5_bar_sessions": (
                    current_short_count
                ),
                "current_h1_ge6_bar_sessions": (
                    current_ge6_count
                ),
                "frozen_h1_bar_count_distribution": (
                    _count_distribution(
                        frozen_count
                    )
                ),
                "current_h1_bar_count_distribution": (
                    _count_distribution(
                        current_count
                    )
                ),
                "states_previous_current_ge6_filter_would_keep": (
                    current_ge6_count
                ),
                "states_previous_current_ge6_filter_would_remove": int(
                    state_count
                    -
                    current_ge6_count
                ),
            },
            "raw_reconstruction_checks": {
                "frozen_short_sessions_vs_native_frozen_d1": (
                    frozen_short_reconstruction
                ),
                "frozen_ge6_sessions_vs_native_frozen_d1": (
                    frozen_ge6_reconstruction
                ),
                "current_all_present_sessions_vs_frozen_d1": (
                    current_all_present_reconstruction
                ),
                "current_short_sessions_vs_frozen_d1": (
                    current_short_reconstruction
                ),
                "current_ge6_sessions_vs_frozen_d1": (
                    current_ge6_reconstruction
                ),
            },
            "short_frozen_state_dates": (
                short_state_dates
            ),
            "current_missing_required_state_dates": (
                current_missing_dates
            ),
            "thresholds": {
                "short_session_max_h1_bars": (
                    SHORT_SESSION_MAX_H1_BARS
                ),
                "previous_reconstruction_min_h1_bars": (
                    PREVIOUS_RECONSTRUCTION_MIN_H1_BARS
                ),
                "minimum_required_d1_states": (
                    MIN_REQUIRED_D1_STATES
                ),
                "minimum_short_state_count_for_material_gap": (
                    MIN_SHORT_STATE_COUNT_FOR_MATERIAL_GAP
                ),
                "minimum_short_source_reconstruction_match_fraction": (
                    MIN_SHORT_SOURCE_RECONSTRUCTION_MATCH_FRACTION
                ),
                "price_absolute_tolerance": (
                    PRICE_ABSOLUTE_TOLERANCE
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
                "immutable_frozen_h1_loaded": (
                    True
                ),
                "immutable_frozen_d1_loaded": (
                    True
                ),
                "frozen_raw_snapshot_hashes_validated": (
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
                "if_short_session_gap_confirmed": (
                    "REBUILD_CURRENT_00UTC_D1_WITHOUT_"
                    "THE_SIX_H1_BAR_MINIMUM_AND_COMPARE_"
                    "THE_FULL_309_STATE_SEQUENCE"
                ),
                "if_short_sessions_present_but_unresolved": (
                    "INSPECT_FROZEN_NATIVE_D1_SHORT_SESSION_"
                    "INGEST_PROVENANCE"
                ),
                "if_short_session_gap_not_sufficient": (
                    "ISOLATE_OTHER_D1_STATE_SEQUENCE_DIFFERENCES"
                ),
                "previous_warmup_file_remains_uncommitted": (
                    True
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
                        "XAUUSD_D1_SHORT_SESSION_STATE_GAP_DIAGNOSTIC_FAILED"
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