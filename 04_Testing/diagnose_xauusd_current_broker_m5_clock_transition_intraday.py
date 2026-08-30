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
    "XAUUSD_CURRENT_BROKER_M5_CLOCK_TRANSITION_INTRADAY_V1"
)

TRANSITION_MODULE_NAME = (
    "04_Testing."
    "diagnose_xauusd_current_broker_m5_clock_transition_dates"
)


M5_SECONDS = 300

OFFSET_MINUS_3H = -3 * 60 * 60
OFFSET_MINUS_2H = -2 * 60 * 60

LOCAL_WINDOW_BUFFER_HOURS = 6

MIN_TRANSITION_OVERLAP_ROWS = 300

MIN_TRANSITION_ALIGNMENT_SCORE = 0.95

MIN_TRANSITION_BODY_CORRELATION = 0.95

MIN_TRANSITION_CLOSE_DELTA_CORRELATION = 0.95

MIN_TRANSITION_DIRECTION_AGREEMENT = 0.90

MIN_TRANSITION_RANGE_CORRELATION = 0.90


transition_module: Any = importlib.import_module(
    TRANSITION_MODULE_NAME
)

temporal_module: Any = (
    transition_module.temporal_module
)

clock_module: Any = (
    transition_module.clock_module
)

raw_module: Any = (
    transition_module.raw_module
)

audit: Any = (
    transition_module.audit
)


TRANSITION_SPECS: tuple[
    dict[str, Any],
    ...,
] = (
    {
        "transition_id": "FALL_2025",
        "last_old_regime_date": "2025-10-31",
        "first_new_regime_date": "2025-11-03",
        "old_offset_seconds": OFFSET_MINUS_3H,
        "new_offset_seconds": OFFSET_MINUS_2H,
    },
    {
        "transition_id": "SPRING_2026",
        "last_old_regime_date": "2026-03-06",
        "first_new_regime_date": "2026-03-09",
        "old_offset_seconds": OFFSET_MINUS_2H,
        "new_offset_seconds": OFFSET_MINUS_3H,
    },
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


def _correlation(
    left: np.ndarray,
    right: np.ndarray,
) -> float | None:

    if (
        left.size < 3
        or
        right.size != left.size
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
        left_std <= 1e-12
        or
        right_std <= 1e-12
    ):
        return None

    result = float(
        np.corrcoef(
            left,
            right,
        )[0, 1]
    )

    if not math.isfinite(
        result
    ):
        return None

    return result


def _alignment_score(
    *,
    body_correlation: float | None,
    close_delta_correlation: float | None,
    direction_agreement: float | None,
    range_correlation: float | None,
) -> float | None:

    direction_edge: float | None

    if direction_agreement is None:
        direction_edge = None

    else:
        direction_edge = float(
            max(
                -1.0,
                min(
                    1.0,
                    (
                        2.0
                        *
                        direction_agreement
                        -
                        1.0
                    ),
                ),
            )
        )

    values = [
        value
        for value
        in (
            body_correlation,
            close_delta_correlation,
            direction_edge,
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


def _transition_reference_bounds(
    spec: Mapping[
        str,
        Any,
    ],
) -> dict[str, pd.Timestamp]:

    old_date = str(
        spec[
            "last_old_regime_date"
        ]
    )

    new_date = str(
        spec[
            "first_new_regime_date"
        ]
    )

    old_offset = int(
        spec[
            "old_offset_seconds"
        ]
    )

    new_offset = int(
        spec[
            "new_offset_seconds"
        ]
    )

    old_reference_start = pd.Timestamp(
        f"{old_date}T00:00:00Z"
    )

    old_reference_end = pd.Timestamp(
        f"{old_date}T23:55:00Z"
    )

    new_reference_start = pd.Timestamp(
        f"{new_date}T00:00:00Z"
    )

    new_reference_end = pd.Timestamp(
        f"{new_date}T23:55:00Z"
    )

    candidate_source_lower = (
        old_reference_end
        -
        pd.Timedelta(
            seconds=old_offset
        )
        +
        pd.Timedelta(
            seconds=M5_SECONDS
        )
    )

    candidate_source_upper = (
        new_reference_start
        -
        pd.Timedelta(
            seconds=new_offset
        )
    )

    reference_window_start = (
        old_reference_start
        -
        pd.Timedelta(
            hours=LOCAL_WINDOW_BUFFER_HOURS
        )
    )

    reference_window_end = (
        new_reference_end
        +
        pd.Timedelta(
            hours=LOCAL_WINDOW_BUFFER_HOURS
        )
    )

    source_window_start = (
        reference_window_start
        +
        pd.Timedelta(
            hours=1
        )
    )

    source_window_end = (
        reference_window_end
        +
        pd.Timedelta(
            hours=4
        )
    )

    _require(
        candidate_source_lower
        <=
        candidate_source_upper,
        (
            "INVALID_TRANSITION_CANDIDATE_INTERVAL:"
            f"{spec['transition_id']}"
        ),
    )

    return {
        "old_reference_start": (
            old_reference_start
        ),
        "old_reference_end": (
            old_reference_end
        ),
        "new_reference_start": (
            new_reference_start
        ),
        "new_reference_end": (
            new_reference_end
        ),
        "candidate_source_lower": (
            candidate_source_lower
        ),
        "candidate_source_upper": (
            candidate_source_upper
        ),
        "reference_window_start": (
            reference_window_start
        ),
        "reference_window_end": (
            reference_window_end
        ),
        "source_window_start": (
            source_window_start
        ),
        "source_window_end": (
            source_window_end
        ),
    }


def _candidate_boundaries(
    current_raw: pd.DataFrame,
    *,
    lower: pd.Timestamp,
    upper: pd.Timestamp,
) -> list[pd.Timestamp]:

    mask = (
        (
            current_raw[
                "time"
            ]
            >=
            lower
        )
        &
        (
            current_raw[
                "time"
            ]
            <=
            upper
        )
    )

    values = (
        current_raw.loc[
            mask,
            "time",
        ]
        .dropna()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    candidates = [
        pd.Timestamp(
            value
        )
        for value
        in values
    ]

    _require(
        bool(
            candidates
        ),
        (
            "NO_INTRADAY_BOUNDARY_CANDIDATES:"
            f"{lower.isoformat()}:"
            f"{upper.isoformat()}"
        ),
    )

    return candidates


def _map_current_raw(
    current_raw: pd.DataFrame,
    *,
    boundary: pd.Timestamp,
    old_offset_seconds: int,
    new_offset_seconds: int,
) -> tuple[
    pd.DataFrame,
    int,
]:

    mapped = (
        current_raw[
            [
                "time",
                "open",
                "high",
                "low",
                "close",
            ]
        ]
        .copy()
    )

    mapped[
        "source_time"
    ] = pd.to_datetime(
        mapped[
            "time"
        ],
        utc=True,
        errors="raise",
    )

    use_new_regime = (
        mapped[
            "source_time"
        ]
        >=
        boundary
    )

    offsets = np.where(
        use_new_regime.to_numpy(
            dtype=bool
        ),
        new_offset_seconds,
        old_offset_seconds,
    )

    mapped[
        "offset_seconds"
    ] = offsets.astype(
        np.int64
    )

    mapped[
        "time"
    ] = (
        mapped[
            "source_time"
        ]
        +
        pd.to_timedelta(
            mapped[
                "offset_seconds"
            ],
            unit="s",
        )
    )

    duplicate_count = int(
        mapped[
            "time"
        ].duplicated(
            keep=False
        ).sum()
    )

    return (
        mapped,
        duplicate_count,
    )


def _paired_metrics(
    frozen_raw: pd.DataFrame,
    mapped_current: pd.DataFrame,
    *,
    reference_start: pd.Timestamp,
    reference_end: pd.Timestamp,
) -> dict[str, Any]:

    frozen = (
        frozen_raw.loc[
            (
                frozen_raw[
                    "time"
                ]
                >=
                reference_start
            )
            &
            (
                frozen_raw[
                    "time"
                ]
                <=
                reference_end
            ),
            [
                "time",
                "open",
                "high",
                "low",
                "close",
            ],
        ]
        .rename(
            columns={
                "open": "open_frozen",
                "high": "high_frozen",
                "low": "low_frozen",
                "close": "close_frozen",
            }
        )
        .copy()
    )

    current = (
        mapped_current.loc[
            (
                mapped_current[
                    "time"
                ]
                >=
                reference_start
            )
            &
            (
                mapped_current[
                    "time"
                ]
                <=
                reference_end
            ),
            [
                "time",
                "open",
                "high",
                "low",
                "close",
            ],
        ]
        .rename(
            columns={
                "open": "open_current",
                "high": "high_current",
                "low": "low_current",
                "close": "close_current",
            }
        )
        .copy()
    )

    if bool(
        current[
            "time"
        ].duplicated().any()
    ):

        return {
            "paired_rows": 0,
            "body_correlation": None,
            "close_delta_correlation": None,
            "candle_direction_agreement": None,
            "range_correlation": None,
            "alignment_score": None,
        }

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

    if paired.empty:

        return {
            "paired_rows": 0,
            "body_correlation": None,
            "close_delta_correlation": None,
            "candle_direction_agreement": None,
            "range_correlation": None,
            "alignment_score": None,
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

    finite = (
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
            finite
        ]
    )

    high_frozen = (
        high_frozen[
            finite
        ]
    )

    low_frozen = (
        low_frozen[
            finite
        ]
    )

    close_frozen = (
        close_frozen[
            finite
        ]
    )

    open_current = (
        open_current[
            finite
        ]
    )

    high_current = (
        high_current[
            finite
        ]
    )

    low_current = (
        low_current[
            finite
        ]
    )

    close_current = (
        close_current[
            finite
        ]
    )

    finite_times = pd.to_datetime(
        paired.loc[
            finite,
            "time",
        ],
        utc=True,
        errors="raise",
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

    body_correlation = (
        _correlation(
            body_frozen,
            body_current,
        )
    )

    range_correlation = (
        _correlation(
            range_frozen,
            range_current,
        )
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
        (
            direction_frozen
            !=
            0.0
        )
        &
        (
            direction_current
            !=
            0.0
        )
    )

    direction_agreement: (
        float
        |
        None
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

    else:

        direction_agreement = None

    close_delta_correlation: (
        float
        |
        None
    ) = None

    if close_frozen.size >= 2:

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

        consecutive = (
            finite_times.diff()
            ==
            pd.Timedelta(
                seconds=M5_SECONDS
            )
        ).to_numpy(
            dtype=bool
        )

        delta_mask = (
            consecutive[
                1:
            ]
        )

        if (
            delta_mask.size
            ==
            frozen_delta.size
        ):

            frozen_delta = (
                frozen_delta[
                    delta_mask
                ]
            )

            current_delta = (
                current_delta[
                    delta_mask
                ]
            )

        close_delta_correlation = (
            _correlation(
                frozen_delta,
                current_delta,
            )
        )

    score = (
        _alignment_score(
            body_correlation=(
                body_correlation
            ),
            close_delta_correlation=(
                close_delta_correlation
            ),
            direction_agreement=(
                direction_agreement
            ),
            range_correlation=(
                range_correlation
            ),
        )
    )

    return {
        "paired_rows": int(
            open_frozen.size
        ),
        "body_correlation": (
            body_correlation
        ),
        "close_delta_correlation": (
            close_delta_correlation
        ),
        "candle_direction_agreement": (
            direction_agreement
        ),
        "range_correlation": (
            range_correlation
        ),
        "alignment_score": (
            score
        ),
    }


def _candidate_document(
    frozen_raw: pd.DataFrame,
    current_raw: pd.DataFrame,
    *,
    boundary: pd.Timestamp,
    old_offset_seconds: int,
    new_offset_seconds: int,
    reference_start: pd.Timestamp,
    reference_end: pd.Timestamp,
) -> dict[str, Any]:

    (
        mapped_current,
        duplicate_count,
    ) = (
        _map_current_raw(
            current_raw,
            boundary=boundary,
            old_offset_seconds=(
                old_offset_seconds
            ),
            new_offset_seconds=(
                new_offset_seconds
            ),
        )
    )

    metrics = (
        _paired_metrics(
            frozen_raw,
            mapped_current,
            reference_start=(
                reference_start
            ),
            reference_end=(
                reference_end
            ),
        )
    )

    collision_free = bool(
        duplicate_count == 0
    )

    alignment_score = (
        _safe_float(
            metrics.get(
                "alignment_score"
            )
        )
    )

    valid_candidate = bool(
        collision_free
        and
        int(
            metrics.get(
                "paired_rows",
                0,
            )
        )
        >=
        MIN_TRANSITION_OVERLAP_ROWS
        and
        alignment_score
        is not None
    )

    return {
        "boundary_source_time": (
            boundary.isoformat()
        ),
        "old_offset_seconds": (
            old_offset_seconds
        ),
        "old_offset_hours": float(
            old_offset_seconds
            /
            3600.0
        ),
        "new_offset_seconds": (
            new_offset_seconds
        ),
        "new_offset_hours": float(
            new_offset_seconds
            /
            3600.0
        ),
        "duplicate_mapped_time_rows": (
            duplicate_count
        ),
        "collision_free": (
            collision_free
        ),
        "valid_candidate": (
            valid_candidate
        ),
        **metrics,
    }


def _candidate_sort_key(
    document: Mapping[
        str,
        Any,
    ],
) -> tuple[
    int,
    float,
    float,
    float,
    float,
    int,
]:

    collision_free = int(
        bool(
            document.get(
                "collision_free",
                False,
            )
        )
    )

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
        collision_free,
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
                "paired_rows",
                0,
            )
        ),
    )


def _transition_confirmed(
    document: Mapping[
        str,
        Any,
    ],
) -> bool:

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

    range_correlation = (
        _safe_float(
            document.get(
                "range_correlation"
            )
        )
    )

    return bool(
        bool(
            document.get(
                "collision_free",
                False,
            )
        )
        and
        int(
            document.get(
                "paired_rows",
                0,
            )
        )
        >=
        MIN_TRANSITION_OVERLAP_ROWS
        and
        score
        is not None
        and
        score
        >=
        MIN_TRANSITION_ALIGNMENT_SCORE
        and
        body
        is not None
        and
        body
        >=
        MIN_TRANSITION_BODY_CORRELATION
        and
        close_delta
        is not None
        and
        close_delta
        >=
        MIN_TRANSITION_CLOSE_DELTA_CORRELATION
        and
        direction
        is not None
        and
        direction
        >=
        MIN_TRANSITION_DIRECTION_AGREEMENT
        and
        range_correlation
        is not None
        and
        range_correlation
        >=
        MIN_TRANSITION_RANGE_CORRELATION
    )


def _transition_diagnostic(
    frozen_raw: pd.DataFrame,
    current_raw: pd.DataFrame,
    *,
    spec: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    bounds = (
        _transition_reference_bounds(
            spec
        )
    )

    frozen_local = (
        frozen_raw.loc[
            (
                frozen_raw[
                    "time"
                ]
                >=
                bounds[
                    "reference_window_start"
                ]
            )
            &
            (
                frozen_raw[
                    "time"
                ]
                <=
                bounds[
                    "reference_window_end"
                ]
            )
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    current_local = (
        current_raw.loc[
            (
                current_raw[
                    "time"
                ]
                >=
                bounds[
                    "source_window_start"
                ]
            )
            &
            (
                current_raw[
                    "time"
                ]
                <=
                bounds[
                    "source_window_end"
                ]
            )
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    _require(
        not frozen_local.empty,
        (
            "FROZEN_TRANSITION_WINDOW_EMPTY:"
            f"{spec['transition_id']}"
        ),
    )

    _require(
        not current_local.empty,
        (
            "CURRENT_TRANSITION_WINDOW_EMPTY:"
            f"{spec['transition_id']}"
        ),
    )

    boundaries = (
        _candidate_boundaries(
            current_local,
            lower=(
                bounds[
                    "candidate_source_lower"
                ]
            ),
            upper=(
                bounds[
                    "candidate_source_upper"
                ]
            ),
        )
    )

    old_offset = int(
        spec[
            "old_offset_seconds"
        ]
    )

    new_offset = int(
        spec[
            "new_offset_seconds"
        ]
    )

    documents = [
        _candidate_document(
            frozen_local,
            current_local,
            boundary=boundary,
            old_offset_seconds=(
                old_offset
            ),
            new_offset_seconds=(
                new_offset
            ),
            reference_start=(
                bounds[
                    "reference_window_start"
                ]
            ),
            reference_end=(
                bounds[
                    "reference_window_end"
                ]
            ),
        )
        for boundary
        in boundaries
    ]

    ranked = sorted(
        documents,
        key=_candidate_sort_key,
        reverse=True,
    )

    _require(
        bool(
            ranked
        ),
        (
            "TRANSITION_RANKING_EMPTY:"
            f"{spec['transition_id']}"
        ),
    )

    best = (
        ranked[
            0
        ]
    )

    confirmed = (
        _transition_confirmed(
            best
        )
    )

    collision_free_candidates = sum(
        1
        for document
        in documents
        if bool(
            document.get(
                "collision_free",
                False,
            )
        )
    )

    valid_candidates = sum(
        1
        for document
        in documents
        if bool(
            document.get(
                "valid_candidate",
                False,
            )
        )
    )

    return {
        "transition_id": (
            str(
                spec[
                    "transition_id"
                ]
            )
        ),
        "last_old_regime_date": (
            str(
                spec[
                    "last_old_regime_date"
                ]
            )
        ),
        "first_new_regime_date": (
            str(
                spec[
                    "first_new_regime_date"
                ]
            )
        ),
        "old_offset_seconds": (
            old_offset
        ),
        "old_offset_hours": float(
            old_offset
            /
            3600.0
        ),
        "new_offset_seconds": (
            new_offset
        ),
        "new_offset_hours": float(
            new_offset
            /
            3600.0
        ),
        "candidate_source_lower": (
            bounds[
                "candidate_source_lower"
            ].isoformat()
        ),
        "candidate_source_upper": (
            bounds[
                "candidate_source_upper"
            ].isoformat()
        ),
        "candidate_count": int(
            len(
                documents
            )
        ),
        "collision_free_candidate_count": int(
            collision_free_candidates
        ),
        "valid_candidate_count": int(
            valid_candidates
        ),
        "confirmed": (
            confirmed
        ),
        "selected_boundary_source_time": (
            best.get(
                "boundary_source_time"
            )
        ),
        "selected_duplicate_mapped_time_rows": (
            best.get(
                "duplicate_mapped_time_rows"
            )
        ),
        "selected_paired_rows": (
            best.get(
                "paired_rows"
            )
        ),
        "selected_alignment_score": (
            best.get(
                "alignment_score"
            )
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
        "top_candidates": [
            {
                "rank": int(
                    index
                ),
                **document,
            }
            for index, document
            in enumerate(
                ranked[
                    :10
                ],
                start=1,
            )
        ],
    }


def _overall_decision(
    transition_documents: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
) -> dict[str, Any]:

    _require(
        len(
            transition_documents
        )
        ==
        len(
            TRANSITION_SPECS
        ),
        (
            "UNEXPECTED_TRANSITION_DOCUMENT_COUNT:"
            f"{len(transition_documents)}"
        ),
    )

    confirmed_count = sum(
        1
        for document
        in transition_documents
        if bool(
            document.get(
                "confirmed",
                False,
            )
        )
    )

    collision_free_all = all(
        int(
            document.get(
                "selected_duplicate_mapped_time_rows",
                -1,
            )
        )
        ==
        0
        for document
        in transition_documents
    )

    if (
        confirmed_count
        ==
        len(
            transition_documents
        )
        and
        collision_free_all
    ):

        status = (
            "COLLISION_FREE_INTRADAY_TRANSITION_BOUNDARIES_CONFIRMED"
        )

        reason = (
            "BOTH_SEASONAL_SWITCHES_HAVE_COLLISION_FREE_"
            "SOURCE_TIME_BOUNDARIES_WITH_STRONG_RAW_OHLC_ALIGNMENT"
        )

        next_action = (
            "UPDATE_MAPPED_M5_DOMAIN_SHIFT_RUNNER_WITH_"
            "DISCOVERED_INTRADAY_BOUNDARIES_AND_RERUN"
        )

    elif confirmed_count > 0:

        status = (
            "INTRADAY_TRANSITION_BOUNDARIES_PARTIALLY_CONFIRMED"
        )

        reason = (
            "ONLY_ONE_SEASONAL_TRANSITION_MEETS_"
            "COLLISION_FREE_ALIGNMENT_CONTRACT"
        )

        next_action = (
            "INSPECT_UNRESOLVED_TRANSITION_BEFORE_MAPPED_DOMAIN_AUDIT"
        )

    else:

        status = (
            "INTRADAY_TRANSITION_BOUNDARIES_UNRESOLVED"
        )

        reason = (
            "NO_COLLISION_FREE_BOUNDARY_MEETS_RAW_ALIGNMENT_THRESHOLDS"
        )

        next_action = (
            "AUDIT_BROKER_MARKET_REOPEN_AND_TIMESTAMP_PROVENANCE"
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "transition_count": int(
            len(
                transition_documents
            )
        ),
        "confirmed_transition_count": int(
            confirmed_count
        ),
        "all_selected_boundaries_collision_free": (
            collision_free_all
        ),
        "mapped_feature_domain_audit_allowed": bool(
            status
            ==
            "COLLISION_FREE_INTRADAY_TRANSITION_BOUNDARIES_CONFIRMED"
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

    current_fetch_start = (
        train_start
        -
        pd.Timedelta(
            hours=6
        )
    )

    current_fetch_end = (
        train_end
        +
        pd.Timedelta(
            days=1
        )
        +
        pd.Timedelta(
            hours=6
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

        transition_documents = [
            _transition_diagnostic(
                frozen_raw,
                current_raw,
                spec=(
                    spec
                ),
            )
            for spec
            in TRANSITION_SPECS
        ]

        decision = (
            _overall_decision(
                transition_documents
            )
        )

        return {
            "valid": True,
            "reason": (
                "OK_XAUUSD_CURRENT_BROKER_M5_"
                "CLOCK_TRANSITION_INTRADAY_DIAGNOSTIC"
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
            "boundary_policy": {
                "source": (
                    "CONFIRMED_TRAIN_ONLY_DAILY_TRANSITION_BRACKETS"
                ),
                "candidate_boundary_granularity": (
                    "ACTUAL_CURRENT_BROKER_M5_BAR_TIMES"
                ),
                "old_and_new_offsets": [
                    -3.0,
                    -2.0,
                ],
                "duplicate_mapped_times_allowed": (
                    False
                ),
                "mapped_rows_deduplicated": (
                    False
                ),
                "collision_candidates_rejected": (
                    True
                ),
                "minimum_transition_overlap_rows": (
                    MIN_TRANSITION_OVERLAP_ROWS
                ),
                "minimum_alignment_score": (
                    MIN_TRANSITION_ALIGNMENT_SCORE
                ),
                "minimum_body_correlation": (
                    MIN_TRANSITION_BODY_CORRELATION
                ),
                "minimum_close_delta_correlation": (
                    MIN_TRANSITION_CLOSE_DELTA_CORRELATION
                ),
                "minimum_direction_agreement": (
                    MIN_TRANSITION_DIRECTION_AGREEMENT
                ),
                "minimum_range_correlation": (
                    MIN_TRANSITION_RANGE_CORRELATION
                ),
                "month_names_hardcoded": (
                    False
                ),
                "live_runtime_mapping_authorized": (
                    False
                ),
            },
            "decision": (
                decision
            ),
            "transitions": (
                transition_documents
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
                "if_collision_free_boundaries_confirmed": (
                    "UPDATE_MAPPED_M5_DOMAIN_SHIFT_RUNNER_"
                    "WITH_DISCOVERED_SOURCE_TIME_BOUNDARIES"
                ),
                "if_partial": (
                    "INSPECT_ONLY_UNRESOLVED_SEASONAL_TRANSITION"
                ),
                "if_unresolved": (
                    "AUDIT_MARKET_REOPEN_AND_TIMESTAMP_PROVENANCE"
                ),
                "mapped_rows_must_never_be_silently_deduplicated": (
                    True
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
                        "CLOCK_TRANSITION_INTRADAY_DIAGNOSTIC_FAILED"
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