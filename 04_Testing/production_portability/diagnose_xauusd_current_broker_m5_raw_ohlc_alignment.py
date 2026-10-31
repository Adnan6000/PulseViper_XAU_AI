from __future__ import annotations

import hashlib
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
    sys.path.insert(0, str(ROOT_DIR))


ANALYSIS_VERSION = (
    "XAUUSD_CURRENT_BROKER_M5_RAW_OHLC_ALIGNMENT_V1"
)

SOURCE_AUDIT_MODULE = (
    "04_Testing.analyze_xauusd_current_broker_m5_domain_shift"
)

EXPECTED_HISTORICAL_M5_DATASET_ID = (
    "hist_699191ac65db605731559dda"
)

EXPECTED_HISTORICAL_M5_DATASET_SHA256 = (
    "699191ac65db605731559dda"
    "1b7a1f35e696ab7e6df100caa8291f6648bc5dfa"
)

EXPECTED_HISTORICAL_M5_ROWS = 100000

M5_SECONDS = 300

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

STRONG_BODY_CORRELATION = 0.80

STRONG_CLOSE_DELTA_CORRELATION = 0.80

STRONG_DIRECTION_AGREEMENT = 0.80

STRONG_RANGE_CORRELATION = 0.70

NONZERO_GAIN_REQUIRED = 0.15


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


def _sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as handle:

        while True:

            block = handle.read(
                1024 * 1024
            )

            if not block:
                break

            digest.update(
                block
            )

    return digest.hexdigest()


def _json_object(
    path: Path,
) -> dict[str, Any] | None:

    try:

        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
    ):

        return None

    if not isinstance(
        payload,
        dict,
    ):

        return None

    return payload


def _manifest_candidate_paths(
    value: Any,
    *,
    manifest_path: Path,
) -> list[Path]:

    candidates: list[Path] = []

    def visit(
        item: Any,
    ) -> None:

        if isinstance(
            item,
            Mapping,
        ):

            for child in item.values():
                visit(
                    child
                )

            return

        if isinstance(
            item,
            list,
        ):

            for child in item:
                visit(
                    child
                )

            return

        if not isinstance(
            item,
            str,
        ):

            return

        lowered = (
            item.lower()
        )

        if not (
            lowered.endswith(
                ".csv"
            )
            or
            lowered.endswith(
                ".parquet"
            )
        ):

            return

        raw_path = Path(
            item
        )

        if raw_path.is_absolute():

            candidates.append(
                raw_path
            )

        else:

            candidates.append(
                manifest_path.parent
                /
                raw_path
            )

    visit(
        value
    )

    return candidates


def _candidate_data_files(
    manifest_path: Path,
    payload: Mapping[
        str,
        Any,
    ],
) -> list[Path]:

    candidates: list[Path] = []

    candidates.extend(
        _manifest_candidate_paths(
            payload,
            manifest_path=(
                manifest_path
            ),
        )
    )

    for pattern in (
        "*.csv",
        "*.parquet",
    ):

        candidates.extend(
            manifest_path.parent.glob(
                pattern
            )
        )

    seen: set[Path] = set()

    unique: list[Path] = []

    for candidate in candidates:

        try:

            resolved = (
                candidate.resolve()
            )

        except OSError:

            resolved = (
                candidate
            )

        if resolved in seen:
            continue

        seen.add(
            resolved
        )

        if resolved.exists():
            unique.append(
                resolved
            )

    return unique


def _discover_exact_historical_m5(
) -> tuple[
    Path,
    Path,
    dict[str, Any],
]:

    search_root = (
        ROOT_DIR
        /
        "01_Data"
        /
        "Canonical"
        /
        "Instruments"
        /
        "XAUUSD"
    )

    _require(
        search_root.exists(),
        "XAUUSD_CANONICAL_ROOT_NOT_FOUND",
    )

    matching_manifests: list[
        tuple[
            Path,
            dict[str, Any],
        ]
    ] = []

    for manifest_path in (
        search_root.rglob(
            "*.manifest.json"
        )
    ):

        payload = (
            _json_object(
                manifest_path
            )
        )

        if payload is None:
            continue

        dataset_id = str(
            payload.get(
                "dataset_id",
                "",
            )
        )

        dataset_sha256 = str(
            payload.get(
                "dataset_sha256",
                "",
            )
        )

        if (
            dataset_id
            ==
            EXPECTED_HISTORICAL_M5_DATASET_ID
            and
            dataset_sha256
            ==
            EXPECTED_HISTORICAL_M5_DATASET_SHA256
        ):

            matching_manifests.append(
                (
                    manifest_path,
                    payload,
                )
            )

    _require(
        len(
            matching_manifests
        )
        ==
        1,
        (
            "EXACT_HISTORICAL_M5_MANIFEST_COUNT:"
            f"{len(matching_manifests)}"
        ),
    )

    (
        manifest_path,
        manifest,
    ) = matching_manifests[
        0
    ]

    matching_data_files: list[
        Path
    ] = []

    for candidate in (
        _candidate_data_files(
            manifest_path,
            manifest,
        )
    ):

        if candidate.suffix.lower() != ".csv":
            continue

        try:

            digest = (
                _sha256_file(
                    candidate
                )
            )

        except OSError:
            continue

        if (
            digest
            ==
            EXPECTED_HISTORICAL_M5_DATASET_SHA256
        ):

            matching_data_files.append(
                candidate
            )

    _require(
        len(
            matching_data_files
        )
        ==
        1,
        (
            "EXACT_HISTORICAL_M5_DATA_FILE_COUNT:"
            f"{len(matching_data_files)}"
        ),
    )

    return (
        matching_data_files[
            0
        ],
        manifest_path,
        manifest,
    )


def _resolve_time_column(
    columns: Sequence[
        str
    ],
) -> str:

    available = {
        str(
            column
        )
        for column in columns
    }

    for candidate in (
        "time",
        "timestamp",
        "datetime",
        "bar_time",
        "open_time",
    ):

        if candidate in available:
            return candidate

    raise RuntimeError(
        (
            "HISTORICAL_M5_TIME_COLUMN_NOT_FOUND:"
            f"{sorted(available)}"
        )
    )


def _to_utc_datetime(
    values: pd.Series,
) -> pd.Series:

    numeric = pd.to_numeric(
        values,
        errors="coerce",
    )

    numeric_fraction = float(
        numeric.notna().mean()
    )

    if (
        numeric_fraction
        >=
        0.95
    ):

        finite = numeric[
            numeric.notna()
        ]

        _require(
            not finite.empty,
            "NUMERIC_TIMESTAMP_VALUES_EMPTY",
        )

        magnitude = float(
            finite.abs().median()
        )

        if magnitude >= 1.0e17:

            unit = "ns"

        elif magnitude >= 1.0e14:

            unit = "us"

        elif magnitude >= 1.0e11:

            unit = "ms"

        else:

            unit = "s"

        return pd.to_datetime(
            numeric,
            unit=unit,
            utc=True,
            errors="raise",
        )

    return pd.to_datetime(
        values,
        utc=True,
        errors="raise",
    )


def _load_frozen_raw_m5(
    dataset_path: Path,
) -> pd.DataFrame:

    header = pd.read_csv(
        dataset_path,
        nrows=0,
    )

    time_column = (
        _resolve_time_column(
            [
                str(
                    column
                )
                for column
                in header.columns
            ]
        )
    )

    required = (
        time_column,
        "open",
        "high",
        "low",
        "close",
    )

    missing = [
        column
        for column
        in required
        if column
        not in header.columns
    ]

    _require(
        not missing,
        (
            "FROZEN_HISTORICAL_OHLC_COLUMNS_MISSING:"
            f"{missing}"
        ),
    )

    optional_columns = [
        column
        for column
        in (
            "tick_volume",
            "spread",
            "real_volume",
        )
        if column
        in header.columns
    ]

    use_columns = [
        *required,
        *optional_columns,
    ]

    frame = pd.read_csv(
        dataset_path,
        usecols=use_columns,
    )

    _require(
        len(
            frame
        )
        ==
        EXPECTED_HISTORICAL_M5_ROWS,
        (
            "FROZEN_HISTORICAL_M5_ROW_COUNT_MISMATCH:"
            f"{len(frame)}"
        ),
    )

    frame[
        "time"
    ] = (
        _to_utc_datetime(
            frame[
                time_column
            ]
        )
    )

    for column in (
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
        "spread",
        "real_volume",
    ):

        if column not in frame.columns:
            continue

        frame[
            column
        ] = pd.to_numeric(
            frame[
                column
            ],
            errors="coerce",
        )

    frame = (
        frame
        .sort_values(
            "time"
        )
        .drop_duplicates(
            subset=[
                "time"
            ],
            keep="last",
        )
        .reset_index(
            drop=True
        )
    )

    _require(
        not frame.empty,
        "FROZEN_HISTORICAL_M5_EMPTY",
    )

    return frame


def _correlation(
    left: np.ndarray,
    right: np.ndarray,
) -> float | None:

    if (
        left.size
        <
        3
        or
        right.size
        !=
        left.size
    ):

        return None

    left_std = float(
        np.std(
            left
        )
    )

    right_std = float(
        np.std(
            right
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

        return None

    value = float(
        np.corrcoef(
            left,
            right,
        )[
            0,
            1
        ]
    )

    if not math.isfinite(
        value
    ):

        return None

    return value


def _paired_numeric(
    left: pd.Series,
    right: pd.Series,
) -> tuple[
    np.ndarray,
    np.ndarray,
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

    return (
        left_values[
            valid
        ],
        right_values[
            valid
        ],
    )


def _distribution(
    values: np.ndarray,
) -> dict[str, Any]:

    if values.size == 0:

        return {
            "rows": 0,
            "mean": None,
            "std": None,
            "median": None,
            "p05": None,
            "p95": None,
        }

    return {
        "rows": int(
            values.size
        ),
        "mean": float(
            np.mean(
                values
            )
        ),
        "std": float(
            np.std(
                values
            )
        ),
        "median": float(
            np.median(
                values
            )
        ),
        "p05": float(
            np.percentile(
                values,
                5,
            )
        ),
        "p95": float(
            np.percentile(
                values,
                95,
            )
        ),
    }


def _raw_lag_document(
    frozen_raw: pd.DataFrame,
    current_raw: pd.DataFrame,
    *,
    lag_seconds: int,
) -> dict[str, Any]:

    frozen = (
        frozen_raw[
            [
                "time",
                "open",
                "high",
                "low",
                "close",
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
        current_raw[
            [
                "time",
                "open",
                "high",
                "low",
                "close",
            ]
        ]
        .rename(
            columns={
                "open": (
                    "open_current"
                ),
                "high": (
                    "high_current"
                ),
                "low": (
                    "low_current"
                ),
                "close": (
                    "close_current"
                ),
            }
        )
        .copy()
    )

    current[
        "time"
    ] = (
        current[
            "time"
        ]
        +
        pd.to_timedelta(
            lag_seconds,
            unit="s",
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

    overlap_rows = int(
        len(
            paired
        )
    )

    if overlap_rows == 0:

        return {
            "lag_seconds": int(
                lag_seconds
            ),
            "lag_bars_m5": float(
                lag_seconds
                /
                M5_SECONDS
            ),
            "overlap_rows": 0,
        }

    open_frozen = pd.to_numeric(
        paired[
            "open_frozen"
        ],
        errors="coerce",
    ).to_numpy(
        dtype=np.float64
    )

    high_frozen = pd.to_numeric(
        paired[
            "high_frozen"
        ],
        errors="coerce",
    ).to_numpy(
        dtype=np.float64
    )

    low_frozen = pd.to_numeric(
        paired[
            "low_frozen"
        ],
        errors="coerce",
    ).to_numpy(
        dtype=np.float64
    )

    close_frozen = pd.to_numeric(
        paired[
            "close_frozen"
        ],
        errors="coerce",
    ).to_numpy(
        dtype=np.float64
    )

    open_current = pd.to_numeric(
        paired[
            "open_current"
        ],
        errors="coerce",
    ).to_numpy(
        dtype=np.float64
    )

    high_current = pd.to_numeric(
        paired[
            "high_current"
        ],
        errors="coerce",
    ).to_numpy(
        dtype=np.float64
    )

    low_current = pd.to_numeric(
        paired[
            "low_current"
        ],
        errors="coerce",
    ).to_numpy(
        dtype=np.float64
    )

    close_current = pd.to_numeric(
        paired[
            "close_current"
        ],
        errors="coerce",
    ).to_numpy(
        dtype=np.float64
    )

    finite_mask = (
        np.isfinite(
            open_frozen
        )
        &
        np.isfinite(
            high_frozen
        )
        &
        np.isfinite(
            low_frozen
        )
        &
        np.isfinite(
            close_frozen
        )
        &
        np.isfinite(
            open_current
        )
        &
        np.isfinite(
            high_current
        )
        &
        np.isfinite(
            low_current
        )
        &
        np.isfinite(
            close_current
        )
    )

    open_frozen = (
        open_frozen[
            finite_mask
        ]
    )

    high_frozen = (
        high_frozen[
            finite_mask
        ]
    )

    low_frozen = (
        low_frozen[
            finite_mask
        ]
    )

    close_frozen = (
        close_frozen[
            finite_mask
        ]
    )

    open_current = (
        open_current[
            finite_mask
        ]
    )

    high_current = (
        high_current[
            finite_mask
        ]
    )

    low_current = (
        low_current[
            finite_mask
        ]
    )

    close_current = (
        close_current[
            finite_mask
        ]
    )

    body_frozen = (
        close_frozen
        -
        open_frozen
    )

    body_current = (
        close_current
        -
        open_current
    )

    range_frozen = (
        high_frozen
        -
        low_frozen
    )

    range_current = (
        high_current
        -
        low_current
    )

    direction_frozen = (
        np.sign(
            body_frozen
        )
    )

    direction_current = (
        np.sign(
            body_current
        )
    )

    direction_valid = (
        direction_frozen
        !=
        0.0
    ) & (
        direction_current
        !=
        0.0
    )

    if bool(
        np.any(
            direction_valid
        )
    ):

        direction_agreement = float(
            np.mean(
                direction_frozen[
                    direction_valid
                ]
                ==
                direction_current[
                    direction_valid
                ]
            )
        )

        direction_rows = int(
            np.sum(
                direction_valid
            )
        )

    else:

        direction_agreement = None

        direction_rows = 0

    close_offset = (
        close_current
        -
        close_frozen
    )

    open_offset = (
        open_current
        -
        open_frozen
    )

    level_correlations = {
        "open": (
            _correlation(
                open_frozen,
                open_current,
            )
        ),
        "high": (
            _correlation(
                high_frozen,
                high_current,
            )
        ),
        "low": (
            _correlation(
                low_frozen,
                low_current,
            )
        ),
        "close": (
            _correlation(
                close_frozen,
                close_current,
            )
        ),
    }

    time_values = pd.to_datetime(
        paired.loc[
            finite_mask,
            "time",
        ],
        utc=True,
        errors="raise",
    )

    consecutive = (
        time_values.diff()
        ==
        pd.Timedelta(
            seconds=M5_SECONDS
        )
    ).to_numpy(
        dtype=bool
    )

    close_delta_correlation: (
        float
        |
        None
    ) = None

    close_delta_rows = 0

    if (
        close_frozen.size
        >=
        2
    ):

        frozen_delta = (
            np.diff(
                close_frozen
            )
        )

        current_delta = (
            np.diff(
                close_current
            )
        )

        consecutive_delta_mask = (
            consecutive[
                1:
            ]
        )

        if (
            consecutive_delta_mask.size
            ==
            frozen_delta.size
        ):

            frozen_delta = (
                frozen_delta[
                    consecutive_delta_mask
                ]
            )

            current_delta = (
                current_delta[
                    consecutive_delta_mask
                ]
            )

        close_delta_rows = int(
            frozen_delta.size
        )

        close_delta_correlation = (
            _correlation(
                frozen_delta,
                current_delta,
            )
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
        "overlap_rows": (
            overlap_rows
        ),
        "finite_ohlc_rows": int(
            open_frozen.size
        ),
        "level_correlations": (
            level_correlations
        ),
        "body_correlation": (
            _correlation(
                body_frozen,
                body_current,
            )
        ),
        "range_correlation": (
            _correlation(
                range_frozen,
                range_current,
            )
        ),
        "close_delta_correlation": (
            close_delta_correlation
        ),
        "close_delta_rows": (
            close_delta_rows
        ),
        "candle_direction_agreement": (
            direction_agreement
        ),
        "candle_direction_rows": (
            direction_rows
        ),
        "close_price_offset": (
            _distribution(
                close_offset
            )
        ),
        "open_price_offset": (
            _distribution(
                open_offset
            )
        ),
        "body_absolute_difference": (
            _distribution(
                np.abs(
                    body_current
                    -
                    body_frozen
                )
            )
        ),
        "range_absolute_difference": (
            _distribution(
                np.abs(
                    range_current
                    -
                    range_frozen
                )
            )
        ),
    }


def _metric_or_floor(
    document: Mapping[
        str,
        Any,
    ],
    key: str,
) -> float:

    value = (
        _safe_float(
            document.get(
                key
            )
        )
    )

    if value is None:
        return -2.0

    return value


def _lag_score(
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

    return (
        _metric_or_floor(
            document,
            "body_correlation",
        ),
        _metric_or_floor(
            document,
            "close_delta_correlation",
        ),
        _metric_or_floor(
            document,
            "candle_direction_agreement",
        ),
        _metric_or_floor(
            document,
            "range_correlation",
        ),
        int(
            document.get(
                "overlap_rows",
                0,
            )
        ),
    )


def _raw_alignment_strong(
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

    range_correlation = (
        _safe_float(
            document.get(
                "range_correlation"
            )
        )
    )

    overlap = int(
        document.get(
            "overlap_rows",
            0,
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


def _decision(
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
        "NO_RAW_ALIGNMENT_DOCUMENTS",
    )

    ranked = sorted(
        documents,
        key=_lag_score,
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
            in documents
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
            "ZERO_LAG_RAW_DOCUMENT_MISSING"
        )

    best_lag = int(
        best.get(
            "lag_seconds",
            0,
        )
    )

    best_body = (
        _safe_float(
            best.get(
                "body_correlation"
            )
        )
    )

    zero_body = (
        _safe_float(
            zero.get(
                "body_correlation"
            )
        )
    )

    best_delta = (
        _safe_float(
            best.get(
                "close_delta_correlation"
            )
        )
    )

    zero_delta = (
        _safe_float(
            zero.get(
                "close_delta_correlation"
            )
        )
    )

    body_gain: (
        float
        |
        None
    ) = None

    delta_gain: (
        float
        |
        None
    ) = None

    if (
        best_body
        is not None
        and
        zero_body
        is not None
    ):

        body_gain = (
            best_body
            -
            zero_body
        )

    if (
        best_delta
        is not None
        and
        zero_delta
        is not None
    ):

        delta_gain = (
            best_delta
            -
            zero_delta
        )

    zero_strong = (
        _raw_alignment_strong(
            zero
        )
    )

    best_strong = (
        _raw_alignment_strong(
            best
        )
    )

    if zero_strong:

        status = (
            "ZERO_LAG_RAW_OHLC_ALIGNMENT_CONFIRMED"
        )

        reason = (
            "EXNESS_AND_CURRENT_BROKER_M5_RAW_CANDLES_"
            "ALIGN_AT_SAME_BAR_TIMESTAMP"
        )

        selected_lag = 0

        downstream = (
            "RAW_FEED_ALIGNMENT_CONFIRMED;"
            "FEATURE_TIME_SEMANTICS_OR_FEATURE_PROVENANCE_"
            "MUST_BE_AUDITED_BEFORE_DOMAIN_SHIFT_VERDICT"
        )

    elif (
        best_lag
        !=
        0
        and
        best_strong
        and
        body_gain
        is not None
        and
        body_gain
        >=
        NONZERO_GAIN_REQUIRED
        and
        delta_gain
        is not None
        and
        delta_gain
        >=
        NONZERO_GAIN_REQUIRED
    ):

        status = (
            "NONZERO_RAW_OHLC_TIME_OFFSET_CONFIRMED"
        )

        reason = (
            "RAW_CANDLE_ALIGNMENT_REQUIRES_NONZERO_"
            "CURRENT_BROKER_TIME_SHIFT"
        )

        selected_lag = (
            best_lag
        )

        downstream = (
            "CORRECT_RAW_TIME_ALIGNMENT_BEFORE_"
            "ANY_FEATURE_DOMAIN_COMPARISON"
        )

    else:

        status = (
            "RAW_OHLC_ALIGNMENT_NOT_CONFIRMED"
        )

        reason = (
            "NO_TESTED_M5_LAG_PRODUCED_STRONG_RAW_"
            "CANDLE_CORRESPONDENCE"
        )

        selected_lag = (
            best_lag
        )

        downstream = (
            "INVESTIGATE_RAW_SOURCE_PROVENANCE_OR_"
            "TRUE_BROKER_FEED_DIFFERENCE"
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "selected_lag_seconds": int(
            selected_lag
        ),
        "selected_lag_bars_m5": float(
            selected_lag
            /
            M5_SECONDS
        ),
        "best_ranked_lag_seconds": (
            best_lag
        ),
        "best_body_correlation": (
            best_body
        ),
        "zero_lag_body_correlation": (
            zero_body
        ),
        "body_correlation_gain_best_vs_zero": (
            body_gain
        ),
        "best_close_delta_correlation": (
            best_delta
        ),
        "zero_lag_close_delta_correlation": (
            zero_delta
        ),
        "close_delta_correlation_gain_best_vs_zero": (
            delta_gain
        ),
        "zero_lag_raw_alignment_strong": (
            zero_strong
        ),
        "best_raw_alignment_strong": (
            best_strong
        ),
        "downstream_action": (
            downstream
        ),
        "feature_domain_shift_verdict_allowed": (
            False
        ),
        "full_333_portability_claimed": (
            False
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

    source_dataset_id = str(
        m5_source.get(
            "dataset_id",
            "",
        )
    )

    source_dataset_sha256 = str(
        m5_source.get(
            "dataset_sha256",
            "",
        )
    )

    source_row_count = int(
        m5_source.get(
            "row_count",
            0,
        )
    )

    _require(
        source_dataset_id
        ==
        EXPECTED_HISTORICAL_M5_DATASET_ID,
        (
            "SOURCE_M5_DATASET_ID_MISMATCH:"
            f"{source_dataset_id}"
        ),
    )

    _require(
        source_dataset_sha256
        ==
        EXPECTED_HISTORICAL_M5_DATASET_SHA256,
        (
            "SOURCE_M5_DATASET_SHA256_MISMATCH:"
            f"{source_dataset_sha256}"
        ),
    )

    _require(
        source_row_count
        ==
        EXPECTED_HISTORICAL_M5_ROWS,
        (
            "SOURCE_M5_ROW_COUNT_MISMATCH:"
            f"{source_row_count}"
        ),
    )

    (
        historical_dataset_path,
        historical_manifest_path,
        historical_manifest,
    ) = (
        _discover_exact_historical_m5()
    )

    actual_historical_sha256 = (
        _sha256_file(
            historical_dataset_path
        )
    )

    _require(
        actual_historical_sha256
        ==
        EXPECTED_HISTORICAL_M5_DATASET_SHA256,
        "HISTORICAL_M5_FILE_SHA256_MISMATCH",
    )

    historical_manifest_id = str(
        historical_manifest.get(
            "dataset_id",
            "",
        )
    )

    historical_manifest_sha = str(
        historical_manifest.get(
            "dataset_sha256",
            "",
        )
    )

    _require(
        historical_manifest_id
        ==
        EXPECTED_HISTORICAL_M5_DATASET_ID,
        "HISTORICAL_MANIFEST_ID_MISMATCH",
    )

    _require(
        historical_manifest_sha
        ==
        EXPECTED_HISTORICAL_M5_DATASET_SHA256,
        "HISTORICAL_MANIFEST_SHA_MISMATCH",
    )

    frozen_raw = (
        _load_frozen_raw_m5(
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

    raw_window_start = (
        train_start
        -
        pd.Timedelta(
            days=1
        )
    )

    raw_window_end = (
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
                raw_window_start
            )
            &
            (
                frozen_raw[
                    "time"
                ]
                <=
                raw_window_end
            )
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    _require(
        not frozen_raw.empty,
        "FROZEN_RAW_TRAIN_WINDOW_EMPTY",
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
                raw_window_start.to_pydatetime(),
                raw_window_end.to_pydatetime(),
            )
        )

        current_raw = (
            audit
            ._mt5_rates_frame(
                rates
            )
        )

        lag_documents = [
            _raw_lag_document(
                frozen_raw,
                current_raw,
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

        frozen_start = pd.Timestamp(
            frozen_raw[
                "time"
            ].min()
        )

        frozen_end = pd.Timestamp(
            frozen_raw[
                "time"
            ].max()
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
                "RAW_OHLC_ALIGNMENT_DIAGNOSTIC"
            ),
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "frozen_training_reference": {
                "dataset_id": (
                    audit
                    .EXPECTED_DATASET_ID
                ),
                "dataset_sha256": (
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
                "time_start": (
                    train_start.isoformat()
                ),
                "time_end": (
                    train_end.isoformat()
                ),
            },
            "frozen_raw_m5_source": {
                "dataset_id": (
                    EXPECTED_HISTORICAL_M5_DATASET_ID
                ),
                "dataset_sha256": (
                    EXPECTED_HISTORICAL_M5_DATASET_SHA256
                ),
                "expected_full_rows": (
                    EXPECTED_HISTORICAL_M5_ROWS
                ),
                "loaded_window_rows": int(
                    len(
                        frozen_raw
                    )
                ),
                "window_time_start": (
                    frozen_start.isoformat()
                ),
                "window_time_end": (
                    frozen_end.isoformat()
                ),
                "manifest_validated": (
                    True
                ),
                "data_file_sha256_validated": (
                    True
                ),
                "filesystem_path_emitted": (
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
            "alignment_policy": {
                "raw_fields": [
                    "open",
                    "high",
                    "low",
                    "close",
                ],
                "candidate_current_time_shifts_seconds": list(
                    LAG_CANDIDATES_SECONDS
                ),
                "candidate_current_time_shifts_m5_bars": [
                    float(
                        value
                        /
                        M5_SECONDS
                    )
                    for value
                    in LAG_CANDIDATES_SECONDS
                ],
                "primary_metric": (
                    "CANDLE_BODY_CORRELATION"
                ),
                "secondary_metric": (
                    "CONSECUTIVE_CLOSE_DELTA_CORRELATION"
                ),
                "tertiary_metric": (
                    "CANDLE_DIRECTION_AGREEMENT"
                ),
                "range_metric": (
                    "CANDLE_RANGE_CORRELATION"
                ),
                "price_level_offset_allowed": (
                    True
                ),
                "reason_price_offset_allowed": (
                    "BROKERS_MAY_HAVE_SMALL_LEVEL_OFFSETS_"
                    "WHILE_PRESERVING_DIRECTIONAL_CANDLE_STRUCTURE"
                ),
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
                "nonzero_gain_required": (
                    NONZERO_GAIN_REQUIRED
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
                        document.get(
                            "lag_seconds"
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
                "frozen_training_train_only_used_for_time_boundary": (
                    True
                ),
                "frozen_raw_historical_snapshot_used": (
                    True
                ),
                "frozen_raw_snapshot_hash_verified": (
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
                "if_zero_lag_raw_alignment_confirmed": (
                    "AUDIT_FEATURE_AVAILABILITY_TIME_AND_"
                    "FROZEN_FEATURE_PROVENANCE"
                ),
                "if_nonzero_raw_offset_confirmed": (
                    "CORRECT_RAW_TIME_MAPPING_AND_RERUN_"
                    "M5_FEATURE_DOMAIN_SHIFT"
                ),
                "if_raw_alignment_not_confirmed": (
                    "INVESTIGATE_TRUE_RAW_BROKER_FEED_DOMAIN_SHIFT"
                ),
                "broker_sensitive_spread_and_tick_volume_shift": (
                    "REMAINS_SEPARATE_KNOWN_PORTABILITY_CONCERN"
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
                        "RAW_OHLC_ALIGNMENT_DIAGNOSTIC_FAILED"
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