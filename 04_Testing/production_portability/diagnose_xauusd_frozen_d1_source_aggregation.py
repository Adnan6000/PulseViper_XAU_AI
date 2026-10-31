from __future__ import annotations

import hashlib
import importlib
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


ANALYSIS_VERSION = (
    "XAUUSD_FROZEN_D1_SOURCE_AGGREGATION_V2"
)

BASE_AUDIT_MODULE = (
    "04_Testing."
    "analyze_xauusd_current_broker_m5_domain_shift"
)


base: Any = importlib.import_module(
    BASE_AUDIT_MODULE
)


CANONICAL_ROOT = (
    ROOT_DIR
    /
    "01_Data"
    /
    "Canonical"
)

XAUUSD_CANONICAL_ROOT = (
    CANONICAL_ROOT
    /
    "Instruments"
    /
    "XAUUSD"
)


TIMEFRAME_H1 = "H1"
TIMEFRAME_D1 = "D1"


SESSION_CLOSE_HOURS = tuple(
    range(
        24
    )
)

LABEL_DAY_SHIFTS = (
    -1,
    0,
    1,
)


MIN_H1_BARS_PER_SYNTHETIC_D1 = 6

MIN_GLOBAL_PAIRED_D1_ROWS = 150

MIN_MONTHLY_PAIRED_D1_ROWS = 15

MIN_ELIGIBLE_MONTHS = 8


FIXED_CONFIRMED_BODY_CORRELATION = 0.98
FIXED_CONFIRMED_CLOSE_DELTA_CORRELATION = 0.98
FIXED_CONFIRMED_RANGE_CORRELATION = 0.98
FIXED_CONFIRMED_DIRECTION_AGREEMENT = 0.95

FIXED_LIKELY_BODY_CORRELATION = 0.90
FIXED_LIKELY_CLOSE_DELTA_CORRELATION = 0.90
FIXED_LIKELY_RANGE_CORRELATION = 0.90
FIXED_LIKELY_DIRECTION_AGREEMENT = 0.90


MONTHLY_STRONG_BODY_CORRELATION = 0.95
MONTHLY_STRONG_CLOSE_DELTA_CORRELATION = 0.95
MONTHLY_STRONG_RANGE_CORRELATION = 0.95
MONTHLY_STRONG_DIRECTION_AGREEMENT = 0.90

MIN_MONTHLY_STRONG_SHARE = 0.75

MIN_TOP_TWO_BOUNDARY_SHARE = 0.80


RAW_PRICE_COLUMNS = (
    "open",
    "high",
    "low",
    "close",
)


CANONICAL_DATETIME_DTYPE = (
    "datetime64[ns, UTC]"
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


def _required_int(
    value: object,
    *,
    reason: str,
) -> int:

    if value is None:
        raise RuntimeError(
            reason
        )

    text = str(
        value
    ).strip()

    if not text:
        raise RuntimeError(
            reason
        )

    try:
        result = int(
            text
        )

    except ValueError as exc:
        raise RuntimeError(
            reason
        ) from exc

    return (
        result
    )


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


def _numeric_array(
    values: Any,
) -> np.ndarray:

    numeric = pd.to_numeric(
        values,
        errors="coerce",
    )

    return np.asarray(
        numeric,
        dtype=np.float64,
    )


def _sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as handle:

        while True:

            chunk = handle.read(
                1024
                *
                1024
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


def _snapshot_document(
    manifest: Mapping[
        str,
        Any,
    ],
    timeframe: str,
) -> dict[str, Any]:

    snapshots = (
        manifest.get(
            "source_historical_snapshots"
        )
    )

    if not isinstance(
        snapshots,
        Mapping,
    ):

        raise RuntimeError(
            "SOURCE_HISTORICAL_SNAPSHOTS_MISSING"
        )

    raw_document = (
        snapshots.get(
            timeframe
        )
    )

    if not isinstance(
        raw_document,
        Mapping,
    ):

        raise RuntimeError(
            (
                "SOURCE_HISTORICAL_SNAPSHOT_MISSING:"
                f"{timeframe}"
            )
        )

    dataset_id = str(
        raw_document.get(
            "dataset_id",
            "",
        )
    ).strip()

    dataset_sha256 = str(
        raw_document.get(
            "dataset_sha256",
            "",
        )
    ).strip()

    row_count = (
        _required_int(
            raw_document.get(
                "row_count"
            ),
            reason=(
                "SOURCE_HISTORICAL_ROW_COUNT_INVALID:"
                f"{timeframe}"
            ),
        )
    )

    _require(
        bool(
            dataset_id
        ),
        (
            "SOURCE_HISTORICAL_DATASET_ID_MISSING:"
            f"{timeframe}"
        ),
    )

    _require(
        len(
            dataset_sha256
        )
        ==
        64,
        (
            "SOURCE_HISTORICAL_SHA256_INVALID:"
            f"{timeframe}"
        ),
    )

    _require(
        row_count
        >
        0,
        (
            "SOURCE_HISTORICAL_ROW_COUNT_NONPOSITIVE:"
            f"{timeframe}"
        ),
    )

    return {
        "timeframe": (
            timeframe
        ),
        "dataset_id": (
            dataset_id
        ),
        "dataset_sha256": (
            dataset_sha256
        ),
        "row_count": (
            row_count
        ),
    }


def _snapshot_search_tokens(
    snapshot: Mapping[
        str,
        Any,
    ],
) -> tuple[str, ...]:

    dataset_id = str(
        snapshot[
            "dataset_id"
        ]
    )

    dataset_sha256 = str(
        snapshot[
            "dataset_sha256"
        ]
    )

    if dataset_id.startswith(
        "hist_"
    ):

        dataset_token = (
            dataset_id[
                len(
                    "hist_"
                ):
            ]
        )

    else:

        dataset_token = (
            dataset_id
        )

    return (
        dataset_id.lower(),
        dataset_token.lower(),
        dataset_sha256.lower(),
        dataset_sha256[
            :24
        ].lower(),
        dataset_sha256[
            :16
        ].lower(),
    )


def _candidate_snapshot_files(
    snapshot: Mapping[
        str,
        Any,
    ],
) -> list[Path]:

    _require(
        XAUUSD_CANONICAL_ROOT.is_dir(),
        "XAUUSD_CANONICAL_ROOT_NOT_FOUND",
    )

    timeframe = str(
        snapshot[
            "timeframe"
        ]
    ).lower()

    tokens = (
        _snapshot_search_tokens(
            snapshot
        )
    )

    supported_suffixes = {
        ".parquet",
        ".csv",
    }

    direct_candidates: list[
        Path
    ] = []

    fallback_candidates: list[
        Path
    ] = []

    for path in (
        XAUUSD_CANONICAL_ROOT.rglob(
            "*"
        )
    ):

        if not path.is_file():
            continue

        suffix = (
            path.suffix.lower()
        )

        if (
            suffix
            not in
            supported_suffixes
        ):
            continue

        name = (
            path.name.lower()
        )

        if (
            timeframe
            not in
            name
        ):
            continue

        fallback_candidates.append(
            path
        )

        if any(
            token
            in
            name
            for token
            in tokens
        ):

            direct_candidates.append(
                path
            )

    ordered: list[
        Path
    ] = []

    seen: set[
        Path
    ] = set()

    for path in (
        direct_candidates
        +
        fallback_candidates
    ):

        resolved = (
            path.resolve()
        )

        if (
            resolved
            in
            seen
        ):
            continue

        seen.add(
            resolved
        )

        ordered.append(
            resolved
        )

    return (
        ordered
    )


def _resolve_snapshot_file(
    snapshot: Mapping[
        str,
        Any,
    ],
) -> tuple[
    Path,
    dict[str, Any],
]:

    expected_sha256 = str(
        snapshot[
            "dataset_sha256"
        ]
    )

    candidates = (
        _candidate_snapshot_files(
            snapshot
        )
    )

    _require(
        bool(
            candidates
        ),
        (
            "SOURCE_HISTORICAL_CANDIDATE_FILES_NOT_FOUND:"
            f"{snapshot['timeframe']}"
        ),
    )

    matching: list[
        Path
    ] = []

    hashed_candidate_count = 0

    for path in candidates:

        actual_sha256 = (
            _sha256_file(
                path
            )
        )

        hashed_candidate_count += 1

        if (
            actual_sha256
            ==
            expected_sha256
        ):

            matching.append(
                path
            )

    _require(
        len(
            matching
        )
        ==
        1,
        (
            "SOURCE_HISTORICAL_DATA_FILE_MATCH_COUNT:"
            f"{snapshot['timeframe']}:"
            f"{len(matching)}"
        ),
    )

    return (
        matching[
            0
        ],
        {
            "candidate_file_count": int(
                len(
                    candidates
                )
            ),
            "hashed_candidate_count": int(
                hashed_candidate_count
            ),
            "exact_sha256_match_count": int(
                len(
                    matching
                )
            ),
            "filesystem_path_emitted": (
                False
            ),
        },
    )


def _read_snapshot_frame(
    path: Path,
    snapshot: Mapping[
        str,
        Any,
    ],
) -> pd.DataFrame:

    suffix = (
        path.suffix.lower()
    )

    if (
        suffix
        ==
        ".parquet"
    ):

        frame = pd.read_parquet(
            path
        )

    elif (
        suffix
        ==
        ".csv"
    ):

        frame = pd.read_csv(
            path
        )

    else:

        raise RuntimeError(
            (
                "UNSUPPORTED_HISTORICAL_SNAPSHOT_FORMAT:"
                f"{suffix}"
            )
        )

    _require(
        isinstance(
            frame,
            pd.DataFrame,
        ),
        (
            "HISTORICAL_SNAPSHOT_NOT_DATAFRAME:"
            f"{snapshot['timeframe']}"
        ),
    )

    expected_rows = (
        _required_int(
            snapshot.get(
                "row_count"
            ),
            reason=(
                "HISTORICAL_SNAPSHOT_EXPECTED_ROWS_INVALID:"
                f"{snapshot['timeframe']}"
            ),
        )
    )

    _require(
        len(
            frame
        )
        ==
        expected_rows,
        (
            "HISTORICAL_SNAPSHOT_ROW_COUNT_MISMATCH:"
            f"{snapshot['timeframe']}:"
            f"{len(frame)}:"
            f"{expected_rows}"
        ),
    )

    required_columns = {
        "time",
        *RAW_PRICE_COLUMNS,
    }

    actual_columns = {
        str(
            column
        )
        for column
        in frame.columns
    }

    missing = sorted(
        required_columns
        -
        actual_columns
    )

    _require(
        not missing,
        (
            "HISTORICAL_SNAPSHOT_COLUMNS_MISSING:"
            f"{snapshot['timeframe']}:"
            f"{missing}"
        ),
    )

    result = (
        frame.copy()
    )

    result[
        "time"
    ] = (
        _canonical_time(
            result[
                "time"
            ]
        )
    )

    for column in (
        RAW_PRICE_COLUMNS
    ):

        result[
            column
        ] = pd.to_numeric(
            result[
                column
            ],
            errors="raise",
        ).astype(
            "float64"
        )

    result = (
        result
        .sort_values(
            "time"
        )
        .reset_index(
            drop=True
        )
    )

    duplicate_count = int(
        result[
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
            "HISTORICAL_SNAPSHOT_TIME_DUPLICATES:"
            f"{snapshot['timeframe']}:"
            f"{duplicate_count}"
        ),
    )

    return (
        result
    )


def _correlation(
    left: Any,
    right: Any,
) -> float | None:

    left_values = (
        _numeric_array(
            left
        )
    )

    right_values = (
        _numeric_array(
            right
        )
    )

    _require(
        left_values.shape
        ==
        right_values.shape,
        (
            "CORRELATION_ARRAY_SHAPE_MISMATCH:"
            f"{left_values.shape}:"
            f"{right_values.shape}"
        ),
    )

    finite = (
        np.isfinite(
            left_values
        )
        &
        np.isfinite(
            right_values
        )
    )

    if (
        int(
            finite.sum()
        )
        <
        3
    ):

        return None

    x = (
        left_values[
            finite
        ]
    )

    y = (
        right_values[
            finite
        ]
    )

    x_std = float(
        np.std(
            x
        )
    )

    y_std = float(
        np.std(
            y
        )
    )

    if (
        x_std
        ==
        0.0
        or
        y_std
        ==
        0.0
    ):

        return None

    value = float(
        np.corrcoef(
            x,
            y,
        )[
            0,
            1
        ]
    )

    if not math.isfinite(
        value
    ):

        return None

    return (
        value
    )


def _direction_agreement(
    frozen_body: Any,
    synthetic_body: Any,
) -> float | None:

    frozen = (
        _numeric_array(
            frozen_body
        )
    )

    synthetic = (
        _numeric_array(
            synthetic_body
        )
    )

    _require(
        frozen.shape
        ==
        synthetic.shape,
        (
            "DIRECTION_ARRAY_SHAPE_MISMATCH:"
            f"{frozen.shape}:"
            f"{synthetic.shape}"
        ),
    )

    finite = (
        np.isfinite(
            frozen
        )
        &
        np.isfinite(
            synthetic
        )
    )

    if not bool(
        finite.any()
    ):

        return None

    frozen_sign = np.sign(
        frozen[
            finite
        ]
    )

    synthetic_sign = np.sign(
        synthetic[
            finite
        ]
    )

    return float(
        np.mean(
            frozen_sign
            ==
            synthetic_sign
        )
    )


def _synthetic_d1(
    h1: pd.DataFrame,
    *,
    close_hour: int,
    label_day_shift: int,
) -> pd.DataFrame:

    _require(
        0
        <=
        close_hour
        <=
        23,
        (
            "INVALID_CLOSE_HOUR:"
            f"{close_hour}"
        ),
    )

    _require(
        label_day_shift
        in
        LABEL_DAY_SHIFTS,
        (
            "INVALID_LABEL_DAY_SHIFT:"
            f"{label_day_shift}"
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

    close_offset = pd.Timedelta(
        hours=(
            close_hour
        )
    )

    shifted = (
        working[
            "time"
        ]
        -
        close_offset
    )

    working[
        "session_close"
    ] = (
        shifted.dt.floor(
            "D"
        )
        +
        pd.Timedelta(
            days=1
        )
        +
        close_offset
    )

    grouped = (
        working
        .groupby(
            "session_close",
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
        )
        .reset_index()
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

    grouped = (
        grouped.loc[
            grouped[
                "h1_bar_count"
            ]
            >=
            MIN_H1_BARS_PER_SYNTHETIC_D1
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    grouped[
        "synthetic_bar_time"
    ] = (
        grouped[
            "session_close"
        ]
        -
        pd.Timedelta(
            days=1
        )
    )

    grouped[
        "synthetic_bar_time"
    ] = (
        _canonical_time(
            grouped[
                "synthetic_bar_time"
            ]
        )
    )

    grouped[
        "comparison_date"
    ] = (
        grouped[
            "synthetic_bar_time"
        ]
        .dt
        .floor(
            "D"
        )
        +
        pd.Timedelta(
            days=(
                label_day_shift
            )
        )
    )

    grouped[
        "comparison_date"
    ] = (
        _canonical_time(
            grouped[
                "comparison_date"
            ]
        )
    )

    duplicate_dates = int(
        grouped[
            "comparison_date"
        ]
        .duplicated(
            keep=False
        )
        .sum()
    )

    _require(
        duplicate_dates
        ==
        0,
        (
            "SYNTHETIC_D1_COMPARISON_DATE_DUPLICATES:"
            f"{close_hour}:"
            f"{label_day_shift}:"
            f"{duplicate_dates}"
        ),
    )

    return (
        grouped
    )


def _frozen_d1_for_comparison(
    d1: pd.DataFrame,
) -> pd.DataFrame:

    result = (
        d1[
            [
                "time",
                *RAW_PRICE_COLUMNS,
            ]
        ]
        .copy()
    )

    result[
        "comparison_date"
    ] = (
        result[
            "time"
        ]
        .dt
        .floor(
            "D"
        )
    )

    result[
        "comparison_date"
    ] = (
        _canonical_time(
            result[
                "comparison_date"
            ]
        )
    )

    duplicate_dates = int(
        result[
            "comparison_date"
        ]
        .duplicated(
            keep=False
        )
        .sum()
    )

    _require(
        duplicate_dates
        ==
        0,
        (
            "FROZEN_D1_COMPARISON_DATE_DUPLICATES:"
            f"{duplicate_dates}"
        ),
    )

    return (
        result
    )


def _pair_candidate(
    frozen_d1: pd.DataFrame,
    synthetic: pd.DataFrame,
) -> pd.DataFrame:

    frozen = (
        frozen_d1[
            [
                "comparison_date",
                "time",
                *RAW_PRICE_COLUMNS,
            ]
        ]
        .rename(
            columns={
                "time": (
                    "frozen_time"
                ),
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
    )

    current = (
        synthetic[
            [
                "comparison_date",
                "synthetic_bar_time",
                "session_close",
                "h1_bar_count",
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
    )

    paired = (
        frozen
        .merge(
            current,
            on="comparison_date",
            how="inner",
            validate="one_to_one",
        )
        .sort_values(
            "comparison_date"
        )
        .reset_index(
            drop=True
        )
    )

    return (
        paired
    )


def _alignment_metrics(
    paired: pd.DataFrame,
) -> dict[str, Any]:

    if (
        len(
            paired
        )
        <
        3
    ):

        return {
            "paired_rows": int(
                len(
                    paired
                )
            ),
            "body_correlation": None,
            "close_delta_correlation": None,
            "range_correlation": None,
            "upper_wick_correlation": None,
            "lower_wick_correlation": None,
            "direction_agreement": None,
            "median_price_level_offset": None,
            "alignment_score": None,
        }

    frozen_open = pd.to_numeric(
        paired[
            "open_frozen"
        ],
        errors="coerce",
    )

    frozen_high = pd.to_numeric(
        paired[
            "high_frozen"
        ],
        errors="coerce",
    )

    frozen_low = pd.to_numeric(
        paired[
            "low_frozen"
        ],
        errors="coerce",
    )

    frozen_close = pd.to_numeric(
        paired[
            "close_frozen"
        ],
        errors="coerce",
    )

    synthetic_open = pd.to_numeric(
        paired[
            "open_synthetic"
        ],
        errors="coerce",
    )

    synthetic_high = pd.to_numeric(
        paired[
            "high_synthetic"
        ],
        errors="coerce",
    )

    synthetic_low = pd.to_numeric(
        paired[
            "low_synthetic"
        ],
        errors="coerce",
    )

    synthetic_close = pd.to_numeric(
        paired[
            "close_synthetic"
        ],
        errors="coerce",
    )

    frozen_body = (
        frozen_close
        -
        frozen_open
    )

    synthetic_body = (
        synthetic_close
        -
        synthetic_open
    )

    frozen_range = (
        frozen_high
        -
        frozen_low
    )

    synthetic_range = (
        synthetic_high
        -
        synthetic_low
    )

    frozen_upper_wick = pd.Series(
        frozen_high.to_numpy(
            dtype=np.float64
        )
        -
        np.maximum(
            frozen_open.to_numpy(
                dtype=np.float64
            ),
            frozen_close.to_numpy(
                dtype=np.float64
            ),
        ),
        index=paired.index,
        dtype="float64",
    )

    synthetic_upper_wick = pd.Series(
        synthetic_high.to_numpy(
            dtype=np.float64
        )
        -
        np.maximum(
            synthetic_open.to_numpy(
                dtype=np.float64
            ),
            synthetic_close.to_numpy(
                dtype=np.float64
            ),
        ),
        index=paired.index,
        dtype="float64",
    )

    frozen_lower_wick = pd.Series(
        np.minimum(
            frozen_open.to_numpy(
                dtype=np.float64
            ),
            frozen_close.to_numpy(
                dtype=np.float64
            ),
        )
        -
        frozen_low.to_numpy(
            dtype=np.float64
        ),
        index=paired.index,
        dtype="float64",
    )

    synthetic_lower_wick = pd.Series(
        np.minimum(
            synthetic_open.to_numpy(
                dtype=np.float64
            ),
            synthetic_close.to_numpy(
                dtype=np.float64
            ),
        )
        -
        synthetic_low.to_numpy(
            dtype=np.float64
        ),
        index=paired.index,
        dtype="float64",
    )

    frozen_close_delta = (
        frozen_close.diff()
    )

    synthetic_close_delta = (
        synthetic_close.diff()
    )

    body_correlation = (
        _correlation(
            frozen_body,
            synthetic_body,
        )
    )

    close_delta_correlation = (
        _correlation(
            frozen_close_delta,
            synthetic_close_delta,
        )
    )

    range_correlation = (
        _correlation(
            frozen_range,
            synthetic_range,
        )
    )

    upper_wick_correlation = (
        _correlation(
            frozen_upper_wick,
            synthetic_upper_wick,
        )
    )

    lower_wick_correlation = (
        _correlation(
            frozen_lower_wick,
            synthetic_lower_wick,
        )
    )

    direction_agreement = (
        _direction_agreement(
            frozen_body,
            synthetic_body,
        )
    )

    level_offset = (
        frozen_close
        -
        synthetic_close
    )

    median_level_offset = (
        float(
            level_offset.median()
        )
        if bool(
            level_offset.notna().any()
        )
        else None
    )

    score_components: tuple[
        tuple[
            float | None,
            float,
        ],
        ...,
    ] = (
        (
            body_correlation,
            0.30,
        ),
        (
            close_delta_correlation,
            0.30,
        ),
        (
            range_correlation,
            0.20,
        ),
        (
            upper_wick_correlation,
            0.075,
        ),
        (
            lower_wick_correlation,
            0.075,
        ),
        (
            (
                (
                    2.0
                    *
                    direction_agreement
                )
                -
                1.0
            )
            if (
                direction_agreement
                is not None
            )
            else None,
            0.05,
        ),
    )

    weighted_sum = 0.0
    weight_sum = 0.0

    for (
        value,
        weight,
    ) in score_components:

        if (
            value
            is None
        ):
            continue

        weighted_sum += (
            float(
                value
            )
            *
            weight
        )

        weight_sum += (
            weight
        )

    alignment_score = (
        float(
            weighted_sum
            /
            weight_sum
        )
        if (
            weight_sum
            >
            0.0
        )
        else None
    )

    return {
        "paired_rows": int(
            len(
                paired
            )
        ),
        "body_correlation": (
            body_correlation
        ),
        "close_delta_correlation": (
            close_delta_correlation
        ),
        "range_correlation": (
            range_correlation
        ),
        "upper_wick_correlation": (
            upper_wick_correlation
        ),
        "lower_wick_correlation": (
            lower_wick_correlation
        ),
        "direction_agreement": (
            direction_agreement
        ),
        "median_price_level_offset": (
            median_level_offset
        ),
        "alignment_score": (
            alignment_score
        ),
    }


def _candidate_document(
    *,
    frozen_d1: pd.DataFrame,
    h1: pd.DataFrame,
    close_hour: int,
    label_day_shift: int,
) -> tuple[
    dict[str, Any],
    pd.DataFrame,
]:

    synthetic = (
        _synthetic_d1(
            h1,
            close_hour=(
                close_hour
            ),
            label_day_shift=(
                label_day_shift
            ),
        )
    )

    paired = (
        _pair_candidate(
            frozen_d1,
            synthetic,
        )
    )

    metrics = (
        _alignment_metrics(
            paired
        )
    )

    median_h1_bars: (
        float
        |
        None
    )

    if (
        synthetic.empty
    ):

        median_h1_bars = (
            None
        )

    else:

        median_h1_bars = float(
            synthetic[
                "h1_bar_count"
            ].median()
        )

    return (
        {
            "session_close_hour": int(
                close_hour
            ),
            "label_day_shift": int(
                label_day_shift
            ),
            "synthetic_session_count": int(
                len(
                    synthetic
                )
            ),
            "median_h1_bars_per_session": (
                median_h1_bars
            ),
            **metrics,
        },
        paired,
    )


def _candidate_rank_key(
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
]:

    alignment_score = (
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

    candle_range = (
        _safe_float(
            document.get(
                "range_correlation"
            )
        )
    )

    direction = (
        _safe_float(
            document.get(
                "direction_agreement"
            )
        )
    )

    return (
        (
            alignment_score
            if alignment_score
            is not None
            else -2.0
        ),
        (
            body
            if body
            is not None
            else -2.0
        ),
        (
            close_delta
            if close_delta
            is not None
            else -2.0
        ),
        (
            candle_range
            if candle_range
            is not None
            else -2.0
        ),
        (
            direction
            if direction
            is not None
            else -2.0
        ),
    )


def _fixed_confirmed(
    document: Mapping[
        str,
        Any,
    ],
) -> bool:

    body = (
        _safe_float(
            document.get(
                "body_correlation"
            )
        )
    )

    delta = (
        _safe_float(
            document.get(
                "close_delta_correlation"
            )
        )
    )

    candle_range = (
        _safe_float(
            document.get(
                "range_correlation"
            )
        )
    )

    direction = (
        _safe_float(
            document.get(
                "direction_agreement"
            )
        )
    )

    return bool(
        body
        is not None
        and
        body
        >=
        FIXED_CONFIRMED_BODY_CORRELATION
        and
        delta
        is not None
        and
        delta
        >=
        FIXED_CONFIRMED_CLOSE_DELTA_CORRELATION
        and
        candle_range
        is not None
        and
        candle_range
        >=
        FIXED_CONFIRMED_RANGE_CORRELATION
        and
        direction
        is not None
        and
        direction
        >=
        FIXED_CONFIRMED_DIRECTION_AGREEMENT
    )


def _fixed_likely(
    document: Mapping[
        str,
        Any,
    ],
) -> bool:

    body = (
        _safe_float(
            document.get(
                "body_correlation"
            )
        )
    )

    delta = (
        _safe_float(
            document.get(
                "close_delta_correlation"
            )
        )
    )

    candle_range = (
        _safe_float(
            document.get(
                "range_correlation"
            )
        )
    )

    direction = (
        _safe_float(
            document.get(
                "direction_agreement"
            )
        )
    )

    return bool(
        body
        is not None
        and
        body
        >=
        FIXED_LIKELY_BODY_CORRELATION
        and
        delta
        is not None
        and
        delta
        >=
        FIXED_LIKELY_CLOSE_DELTA_CORRELATION
        and
        candle_range
        is not None
        and
        candle_range
        >=
        FIXED_LIKELY_RANGE_CORRELATION
        and
        direction
        is not None
        and
        direction
        >=
        FIXED_LIKELY_DIRECTION_AGREEMENT
    )


def _monthly_strong(
    document: Mapping[
        str,
        Any,
    ],
) -> bool:

    body = (
        _safe_float(
            document.get(
                "body_correlation"
            )
        )
    )

    delta = (
        _safe_float(
            document.get(
                "close_delta_correlation"
            )
        )
    )

    candle_range = (
        _safe_float(
            document.get(
                "range_correlation"
            )
        )
    )

    direction = (
        _safe_float(
            document.get(
                "direction_agreement"
            )
        )
    )

    return bool(
        body
        is not None
        and
        body
        >=
        MONTHLY_STRONG_BODY_CORRELATION
        and
        delta
        is not None
        and
        delta
        >=
        MONTHLY_STRONG_CLOSE_DELTA_CORRELATION
        and
        candle_range
        is not None
        and
        candle_range
        >=
        MONTHLY_STRONG_RANGE_CORRELATION
        and
        direction
        is not None
        and
        direction
        >=
        MONTHLY_STRONG_DIRECTION_AGREEMENT
    )


def _month_key(
    values: pd.Series,
) -> pd.Series:

    canonical = (
        _canonical_time(
            values
        )
    )

    return canonical.dt.strftime(
        "%Y-%m"
    )


def _monthly_documents(
    pair_cache: Mapping[
        tuple[int, int],
        pd.DataFrame,
    ],
) -> list[dict[str, Any]]:

    all_months: set[
        str
    ] = set()

    for paired in (
        pair_cache.values()
    ):

        if paired.empty:
            continue

        months = (
            _month_key(
                paired[
                    "comparison_date"
                ]
            )
            .tolist()
        )

        all_months.update(
            str(
                month
            )
            for month
            in months
        )

    monthly_results: list[
        dict[str, Any]
    ] = []

    for month in sorted(
        all_months
    ):

        candidates: list[
            dict[str, Any]
        ] = []

        for (
            close_hour,
            label_shift,
        ), paired in (
            pair_cache.items()
        ):

            if paired.empty:
                continue

            month_values = (
                _month_key(
                    paired[
                        "comparison_date"
                    ]
                )
            )

            month_mask = (
                month_values
                ==
                month
            )

            month_pair = (
                paired.loc[
                    month_mask
                ]
                .copy()
                .reset_index(
                    drop=True
                )
            )

            if (
                len(
                    month_pair
                )
                <
                MIN_MONTHLY_PAIRED_D1_ROWS
            ):

                continue

            metrics = (
                _alignment_metrics(
                    month_pair
                )
            )

            candidates.append(
                {
                    "session_close_hour": int(
                        close_hour
                    ),
                    "label_day_shift": int(
                        label_shift
                    ),
                    **metrics,
                }
            )

        if not candidates:
            continue

        ranked = sorted(
            candidates,
            key=_candidate_rank_key,
            reverse=True,
        )

        selected = (
            ranked[
                0
            ]
        )

        monthly_results.append(
            {
                "month": (
                    month
                ),
                "selected_session_close_hour": int(
                    selected[
                        "session_close_hour"
                    ]
                ),
                "selected_label_day_shift": int(
                    selected[
                        "label_day_shift"
                    ]
                ),
                "paired_rows": int(
                    selected[
                        "paired_rows"
                    ]
                ),
                "alignment_score": (
                    selected[
                        "alignment_score"
                    ]
                ),
                "body_correlation": (
                    selected[
                        "body_correlation"
                    ]
                ),
                "close_delta_correlation": (
                    selected[
                        "close_delta_correlation"
                    ]
                ),
                "range_correlation": (
                    selected[
                        "range_correlation"
                    ]
                ),
                "direction_agreement": (
                    selected[
                        "direction_agreement"
                    ]
                ),
                "strong_alignment": (
                    _monthly_strong(
                        selected
                    )
                ),
            }
        )

    return (
        monthly_results
    )


def _decision(
    *,
    fixed_candidates: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
    monthly_results: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
) -> dict[str, Any]:

    _require(
        bool(
            fixed_candidates
        ),
        "NO_FIXED_D1_AGGREGATION_CANDIDATES",
    )

    ranked = sorted(
        fixed_candidates,
        key=_candidate_rank_key,
        reverse=True,
    )

    best = (
        ranked[
            0
        ]
    )

    eligible_month_count = int(
        len(
            monthly_results
        )
    )

    strong_month_count = int(
        sum(
            1
            for document
            in monthly_results
            if bool(
                document.get(
                    "strong_alignment",
                    False,
                )
            )
        )
    )

    strong_month_share = (
        float(
            strong_month_count
            /
            eligible_month_count
        )
        if (
            eligible_month_count
            >
            0
        )
        else None
    )

    selected_boundaries = [
        (
            int(
                document[
                    "selected_session_close_hour"
                ]
            ),
            int(
                document[
                    "selected_label_day_shift"
                ]
            ),
        )
        for document
        in monthly_results
    ]

    boundary_counts = Counter(
        selected_boundaries
    )

    ranked_boundaries = (
        boundary_counts
        .most_common()
    )

    top_two_count = int(
        sum(
            int(
                count
            )
            for (
                _,
                count,
            )
            in ranked_boundaries[
                :2
            ]
        )
    )

    top_two_share = (
        float(
            top_two_count
            /
            eligible_month_count
        )
        if (
            eligible_month_count
            >
            0
        )
        else None
    )

    paired_rows = int(
        best[
            "paired_rows"
        ]
    )

    if (
        paired_rows
        <
        MIN_GLOBAL_PAIRED_D1_ROWS
    ):

        status = (
            "FROZEN_D1_SOURCE_AGGREGATION_INSUFFICIENT_OVERLAP"
        )

        reason = (
            "TOO_FEW_FROZEN_H1_TO_D1_PAIRED_BARS_"
            "FOR_SOURCE_AGGREGATION_PROVENANCE"
        )

        next_action = (
            "RESOLVE_FROZEN_H1_D1_RAW_HISTORY_OVERLAP"
        )

    elif (
        _fixed_confirmed(
            best
        )
    ):

        status = (
            "FROZEN_D1_FIXED_SESSION_BOUNDARY_CONFIRMED"
        )

        reason = (
            "FROZEN_H1_REAGGREGATION_STRONGLY_REPRODUCES_"
            "FROZEN_D1_RAW_CANDLES_AT_ONE_FIXED_BOUNDARY"
        )

        next_action = (
            "APPLY_CONFIRMED_FROZEN_D1_BOUNDARY_TO_"
            "CURRENT_BROKER_H1_AND_AUDIT_RESIDUAL_"
            "SESSION_HOUR_DIFFERENCES"
        )

    elif (
        eligible_month_count
        >=
        MIN_ELIGIBLE_MONTHS
        and
        strong_month_share
        is not None
        and
        strong_month_share
        >=
        MIN_MONTHLY_STRONG_SHARE
        and
        top_two_share
        is not None
        and
        top_two_share
        >=
        MIN_TOP_TWO_BOUNDARY_SHARE
    ):

        status = (
            "FROZEN_D1_SEASONAL_SESSION_BOUNDARY_PATTERN_CONFIRMED"
        )

        reason = (
            "MONTHLY_FROZEN_H1_TO_D1_ALIGNMENT_IS_STRONG_"
            "AND_DOMINATED_BY_AT_MOST_TWO_SESSION_BOUNDARIES"
        )

        next_action = (
            "TRACE_MONTHLY_BOUNDARY_TRANSITION_DATES_"
            "THEN_APPLY_CAUSAL_SEASONAL_D1_MAPPING_"
            "TO_CURRENT_BROKER_H1"
        )

    elif (
        _fixed_likely(
            best
        )
    ):

        status = (
            "FROZEN_D1_FIXED_SESSION_BOUNDARY_LIKELY"
        )

        reason = (
            "ONE_FIXED_BOUNDARY_SUBSTANTIALLY_MATCHES_"
            "FROZEN_D1_BUT_DOES_NOT_MEET_STRONG_"
            "RAW_ALIGNMENT_THRESHOLDS"
        )

        next_action = (
            "INSPECT_FROZEN_H1_SESSION_GAPS_AROUND_"
            "THE_SELECTED_D1_BOUNDARY"
        )

    else:

        status = (
            "FROZEN_D1_SOURCE_AGGREGATION_UNRESOLVED"
        )

        reason = (
            "NEITHER_FIXED_NOR_SEASONAL_H1_REAGGREGATION_"
            "SUFFICIENTLY_REPRODUCES_FROZEN_D1_RAW_CANDLES"
        )

        next_action = (
            "AUDIT_FROZEN_D1_NATIVE_SOURCE_PROVENANCE_"
            "IN_HISTORICAL_INGEST_PIPELINE"
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "selected_fixed_session_close_hour": int(
            best[
                "session_close_hour"
            ]
        ),
        "selected_fixed_label_day_shift": int(
            best[
                "label_day_shift"
            ]
        ),
        "selected_fixed_alignment_score": (
            best[
                "alignment_score"
            ]
        ),
        "selected_fixed_body_correlation": (
            best[
                "body_correlation"
            ]
        ),
        "selected_fixed_close_delta_correlation": (
            best[
                "close_delta_correlation"
            ]
        ),
        "selected_fixed_range_correlation": (
            best[
                "range_correlation"
            ]
        ),
        "selected_fixed_direction_agreement": (
            best[
                "direction_agreement"
            ]
        ),
        "eligible_month_count": (
            eligible_month_count
        ),
        "strong_month_count": (
            strong_month_count
        ),
        "strong_month_share": (
            strong_month_share
        ),
        "monthly_selected_boundary_counts": [
            {
                "session_close_hour": int(
                    boundary[
                        0
                    ]
                ),
                "label_day_shift": int(
                    boundary[
                        1
                    ]
                ),
                "month_count": int(
                    count
                ),
            }
            for (
                boundary,
                count,
            )
            in ranked_boundaries
        ],
        "top_two_monthly_boundary_share": (
            top_two_share
        ),
        "current_broker_used": (
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
        _snapshot_document(
            training_manifest,
            TIMEFRAME_H1,
        )
    )

    d1_snapshot = (
        _snapshot_document(
            training_manifest,
            TIMEFRAME_D1,
        )
    )

    (
        h1_path,
        h1_resolution,
    ) = (
        _resolve_snapshot_file(
            h1_snapshot
        )
    )

    (
        d1_path,
        d1_resolution,
    ) = (
        _resolve_snapshot_file(
            d1_snapshot
        )
    )

    h1 = (
        _read_snapshot_frame(
            h1_path,
            h1_snapshot,
        )
    )

    d1 = (
        _read_snapshot_frame(
            d1_path,
            d1_snapshot,
        )
    )

    frozen_train = (
        base
        ._load_frozen_train_only(
            training_dataset_path,
            [
                "d1_ema20"
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

    _require(
        len(
            frozen_train
        )
        ==
        base.EXPECTED_TRAIN_ROWS,
        (
            "FROZEN_TRAIN_ROW_COUNT_MISMATCH:"
            f"{len(frozen_train)}:"
            f"{base.EXPECTED_TRAIN_ROWS}"
        ),
    )

    comparison_start = (
        train_start
        -
        pd.Timedelta(
            days=3
        )
    )

    comparison_end = (
        train_end
        +
        pd.Timedelta(
            days=3
        )
    )

    h1_window = (
        h1.loc[
            (
                h1[
                    "time"
                ]
                >=
                comparison_start
            )
            &
            (
                h1[
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

    d1_window = (
        d1.loc[
            (
                d1[
                    "time"
                ]
                >=
                comparison_start.floor(
                    "D"
                )
            )
            &
            (
                d1[
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
        not h1_window.empty,
        "FROZEN_H1_TRAIN_WINDOW_EMPTY",
    )

    _require(
        not d1_window.empty,
        "FROZEN_D1_TRAIN_WINDOW_EMPTY",
    )

    frozen_d1 = (
        _frozen_d1_for_comparison(
            d1_window
        )
    )

    fixed_candidates: list[
        dict[str, Any]
    ] = []

    pair_cache: dict[
        tuple[int, int],
        pd.DataFrame,
    ] = {}

    for close_hour in (
        SESSION_CLOSE_HOURS
    ):

        for label_shift in (
            LABEL_DAY_SHIFTS
        ):

            (
                document,
                paired,
            ) = (
                _candidate_document(
                    frozen_d1=(
                        frozen_d1
                    ),
                    h1=(
                        h1_window
                    ),
                    close_hour=(
                        close_hour
                    ),
                    label_day_shift=(
                        label_shift
                    ),
                )
            )

            fixed_candidates.append(
                document
            )

            pair_cache[
                (
                    close_hour,
                    label_shift,
                )
            ] = (
                paired
            )

    ranked_candidates = sorted(
        fixed_candidates,
        key=_candidate_rank_key,
        reverse=True,
    )

    monthly_results = (
        _monthly_documents(
            pair_cache
        )
    )

    decision = (
        _decision(
            fixed_candidates=(
                fixed_candidates
            ),
            monthly_results=(
                monthly_results
            ),
        )
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_FROZEN_D1_"
            "SOURCE_AGGREGATION_DIAGNOSTIC"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "research_scope": (
            "IMMUTABLE_FROZEN_H1_TO_D1_RAW_"
            "AGGREGATION_PROVENANCE_TRAIN_WINDOW_ONLY"
        ),
        "frozen_training_reference": {
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
            "split_used_for_time_boundary": (
                "TRAIN_ONLY"
            ),
            "rows_loaded_for_time_boundary": int(
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
        "frozen_raw_sources": {
            "H1": {
                "dataset_id": (
                    h1_snapshot[
                        "dataset_id"
                    ]
                ),
                "dataset_sha256": (
                    h1_snapshot[
                        "dataset_sha256"
                    ]
                ),
                "expected_full_rows": int(
                    h1_snapshot[
                        "row_count"
                    ]
                ),
                "loaded_full_rows": int(
                    len(
                        h1
                    )
                ),
                "train_window_rows": int(
                    len(
                        h1_window
                    )
                ),
                "data_file_sha256_validated": (
                    True
                ),
                "resolution": (
                    h1_resolution
                ),
                "filesystem_path_emitted": (
                    False
                ),
            },
            "D1": {
                "dataset_id": (
                    d1_snapshot[
                        "dataset_id"
                    ]
                ),
                "dataset_sha256": (
                    d1_snapshot[
                        "dataset_sha256"
                    ]
                ),
                "expected_full_rows": int(
                    d1_snapshot[
                        "row_count"
                    ]
                ),
                "loaded_full_rows": int(
                    len(
                        d1
                    )
                ),
                "train_window_rows": int(
                    len(
                        d1_window
                    )
                ),
                "data_file_sha256_validated": (
                    True
                ),
                "resolution": (
                    d1_resolution
                ),
                "filesystem_path_emitted": (
                    False
                ),
            },
        },
        "diagnostic_contract": {
            "current_broker_used": (
                False
            ),
            "source_broker_comparison": (
                "FROZEN_EXNESS_H1_TO_FROZEN_EXNESS_D1"
            ),
            "session_close_hours_tested": list(
                SESSION_CLOSE_HOURS
            ),
            "label_day_shifts_tested": list(
                LABEL_DAY_SHIFTS
            ),
            "fixed_candidate_count": int(
                len(
                    fixed_candidates
                )
            ),
            "minimum_h1_bars_per_synthetic_d1": (
                MIN_H1_BARS_PER_SYNTHETIC_D1
            ),
            "minimum_global_paired_d1_rows": (
                MIN_GLOBAL_PAIRED_D1_ROWS
            ),
            "minimum_monthly_paired_d1_rows": (
                MIN_MONTHLY_PAIRED_D1_ROWS
            ),
            "primary_metric": (
                "CANDLE_BODY_CORRELATION"
            ),
            "secondary_metric": (
                "CONSECUTIVE_CLOSE_DELTA_CORRELATION"
            ),
            "tertiary_metric": (
                "CANDLE_RANGE_CORRELATION"
            ),
            "direction_metric": (
                "CANDLE_DIRECTION_AGREEMENT"
            ),
            "price_level_offset_allowed": (
                True
            ),
            "reason_price_level_offset_allowed": (
                "RAW_AGGREGATION_PROVENANCE_USES_"
                "CANDLE_STRUCTURE_NOT_ABSOLUTE_PRICE_LEVEL"
            ),
        },
        "thresholds": {
            "fixed_confirmed_body_correlation": (
                FIXED_CONFIRMED_BODY_CORRELATION
            ),
            "fixed_confirmed_close_delta_correlation": (
                FIXED_CONFIRMED_CLOSE_DELTA_CORRELATION
            ),
            "fixed_confirmed_range_correlation": (
                FIXED_CONFIRMED_RANGE_CORRELATION
            ),
            "fixed_confirmed_direction_agreement": (
                FIXED_CONFIRMED_DIRECTION_AGREEMENT
            ),
            "fixed_likely_body_correlation": (
                FIXED_LIKELY_BODY_CORRELATION
            ),
            "fixed_likely_close_delta_correlation": (
                FIXED_LIKELY_CLOSE_DELTA_CORRELATION
            ),
            "fixed_likely_range_correlation": (
                FIXED_LIKELY_RANGE_CORRELATION
            ),
            "fixed_likely_direction_agreement": (
                FIXED_LIKELY_DIRECTION_AGREEMENT
            ),
            "monthly_strong_share_minimum": (
                MIN_MONTHLY_STRONG_SHARE
            ),
            "top_two_monthly_boundary_share_minimum": (
                MIN_TOP_TWO_BOUNDARY_SHARE
            ),
        },
        "decision": (
            decision
        ),
        "fixed_candidate_ranking": [
            {
                "rank": int(
                    index
                ),
                **document,
            }
            for (
                index,
                document,
            )
            in enumerate(
                ranked_candidates,
                start=1,
            )
        ],
        "monthly_best_boundaries": (
            monthly_results
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
            "broker_specific_retraining_authorized": (
                False
            ),
            "live_authorized": (
                False
            ),
            "filesystem_paths_emitted": (
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
            "if_fixed_boundary_confirmed": (
                "APPLY_CONFIRMED_FROZEN_D1_BOUNDARY_"
                "TO_CURRENT_BROKER_H1_AND_AUDIT_"
                "RESIDUAL_SESSION_HOUR_DIFFERENCES"
            ),
            "if_seasonal_pattern_confirmed": (
                "TRACE_FROZEN_D1_BOUNDARY_TRANSITION_DATES_"
                "THEN_APPLY_CAUSAL_SEASONAL_D1_MAPPING"
            ),
            "if_source_aggregation_unresolved": (
                "AUDIT_FROZEN_D1_HISTORICAL_INGEST_PROVENANCE"
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
                        "XAUUSD_FROZEN_D1_"
                        "SOURCE_AGGREGATION_DIAGNOSTIC_FAILED"
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
                    "mt5_used": (
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