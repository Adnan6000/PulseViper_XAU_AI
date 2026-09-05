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


ANALYSIS_VERSION = "XAUUSD_CURRENT_BROKER_M5_DOMAIN_SHIFT_V3"

EXPECTED_DATASET_ID = "train_66ff363d25d8143d4e2c3410"

EXPECTED_DATASET_SHA256 = (
    "66ff363d25d8143d4e2c3410964ad26b"
    "5bd72f2e98806c3e0997ce420d18413d"
)

EXPECTED_TRAINING_MANIFEST_SHA256 = (
    "a205403a6cb5a2d1b17159a2296d1f4a"
    "fb01ea5b9b90b2710feafa7dd9476aa3"
)

EXPECTED_TRAIN_ROWS = 69966

EXPECTED_TRAINING_CONTRACT = "XAUUSD_MTF_TRAINING_V3"

EXPECTED_FEATURE_COUNT = 333

EXPECTED_BASE_FEATURE_COUNT = 43

CANONICAL_SYMBOL = "XAUUSD"

M5_SECONDS = 300

HISTORY_WARMUP_DAYS = 14

MIN_REQUIRED_OVERLAP_ROWS = 5000

MIN_REQUIRED_PRICE_FEATURES = 35

PSI_WARNING_THRESHOLD = 0.10

PSI_MATERIAL_THRESHOLD = 0.25

STANDARDIZED_MEAN_SHIFT_THRESHOLD = 0.50

PRICE_CORRELATION_WARNING_THRESHOLD = 0.95

PRICE_CORRELATION_STRONG_THRESHOLD = 0.98


BROKER_SENSITIVE_FEATURES = (
    "m5_spread_points",
    "m5_tick_volume_log1p",
    "m5_tick_volume_ratio20",
)


trainer_module: Any = importlib.import_module(
    "02_AI.Models.xauusd_hierarchical_model_v4_trainer"
)

sweep_module: Any = importlib.import_module(
    "04_Testing.tune_xauusd_hierarchical_model_v4_stage_b"
)

builder_module: Any = importlib.import_module(
    "02_AI.Dataset.training_matrix_builder"
)

feature_list_module: Any = importlib.import_module(
    "02_AI.Features.feature_list"
)

broker_adapter_module: Any = importlib.import_module(
    "02_AI.Adapters.xauusd_broker_adapter"
)


XAUUSDHierarchicalModelV4Trainer: Any = (
    trainer_module.XAUUSDHierarchicalModelV4Trainer
)

TrainingMatrixBuilder: Any = (
    builder_module.TrainingMatrixBuilder
)

BrokerCostAdapter: Any = (
    broker_adapter_module.BrokerCostAdapter
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
    except (TypeError, ValueError):
        return None

    if not math.isfinite(result):
        return None

    return result


def _sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open("rb") as handle:

        while True:

            block = handle.read(1024 * 1024)

            if not block:
                break

            digest.update(block)

    return digest.hexdigest()


def _snapshot_dataset_path(
    snapshot: Any,
) -> Path:

    value = getattr(
        snapshot,
        "dataset_path",
        None,
    )

    if value is None:
        raise RuntimeError(
            "FROZEN_SNAPSHOT_DATASET_PATH_MISSING"
        )

    path = Path(value)

    if not path.exists():
        raise RuntimeError(
            f"FROZEN_DATASET_PATH_NOT_FOUND:{path}"
        )

    return path


def _snapshot_manifest_path(
    snapshot: Any,
    dataset_path: Path,
) -> Path:

    value = getattr(
        snapshot,
        "manifest_path",
        None,
    )

    if value is None:
        path = dataset_path.with_suffix(
            ".manifest.json"
        )
    else:
        path = Path(value)

    if not path.exists():
        raise RuntimeError(
            f"FROZEN_MANIFEST_PATH_NOT_FOUND:{path}"
        )

    return path


def _validate_snapshot(
    snapshot: Any,
    dataset_path: Path,
    manifest_path: Path,
) -> None:

    dataset_id = str(
        getattr(
            snapshot,
            "dataset_id",
            "",
        )
    )

    dataset_sha256 = str(
        getattr(
            snapshot,
            "dataset_sha256",
            "",
        )
    )

    manifest_sha256 = str(
        getattr(
            snapshot,
            "manifest_sha256",
            "",
        )
    )

    _require(
        dataset_id == EXPECTED_DATASET_ID,
        f"UNEXPECTED_FROZEN_DATASET_ID:{dataset_id}",
    )

    _require(
        dataset_sha256
        == EXPECTED_DATASET_SHA256,
        (
            "UNEXPECTED_FROZEN_DATASET_SHA256:"
            f"{dataset_sha256}"
        ),
    )

    _require(
        manifest_sha256
        == EXPECTED_TRAINING_MANIFEST_SHA256,
        (
            "UNEXPECTED_FROZEN_MANIFEST_SHA256:"
            f"{manifest_sha256}"
        ),
    )

    actual_dataset_sha256 = (
        _sha256_file(dataset_path)
    )

    _require(
        actual_dataset_sha256
        == EXPECTED_DATASET_SHA256,
        (
            "FROZEN_DATASET_FILE_SHA256_MISMATCH:"
            f"{actual_dataset_sha256}"
        ),
    )

    actual_manifest_sha256 = (
        _sha256_file(manifest_path)
    )

    _require(
        actual_manifest_sha256
        == EXPECTED_TRAINING_MANIFEST_SHA256,
        (
            "FROZEN_MANIFEST_FILE_SHA256_MISMATCH:"
            f"{actual_manifest_sha256}"
        ),
    )


def _load_manifest(
    manifest_path: Path,
) -> dict[str, Any]:

    payload = json.loads(
        manifest_path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(payload, dict):
        raise RuntimeError(
            "TRAINING_MANIFEST_NOT_OBJECT"
        )

    _require(
        str(
            payload.get(
                "dataset_id",
                "",
            )
        )
        == EXPECTED_DATASET_ID,
        "TRAINING_MANIFEST_DATASET_ID_MISMATCH",
    )

    _require(
        str(
            payload.get(
                "dataset_sha256",
                "",
            )
        )
        == EXPECTED_DATASET_SHA256,
        "TRAINING_MANIFEST_DATASET_SHA256_MISMATCH",
    )

    _require(
        str(
            payload.get(
                "training_contract_version",
                "",
            )
        )
        == EXPECTED_TRAINING_CONTRACT,
        "TRAINING_CONTRACT_VERSION_MISMATCH",
    )

    feature_columns = payload.get(
        "feature_columns"
    )

    if not isinstance(
        feature_columns,
        list,
    ):
        raise RuntimeError(
            "TRAINING_MANIFEST_FEATURE_COLUMNS_MISSING"
        )

    _require(
        len(feature_columns)
        == EXPECTED_FEATURE_COUNT,
        (
            "TRAINING_MANIFEST_FEATURE_COUNT_MISMATCH:"
            f"{len(feature_columns)}"
        ),
    )

    return payload


def _safe_frozen_identity(
    manifest: Mapping[str, Any],
) -> dict[str, Any]:

    raw_scope = manifest.get(
        "learning_scope",
        {},
    )

    if isinstance(
        raw_scope,
        Mapping,
    ):
        learning_scope: Mapping[
            str,
            Any,
        ] = raw_scope
    else:
        learning_scope = {}

    safe_keys = (
        "canonical_symbol",
        "broker_id",
        "broker_symbol",
        "contract_spec_id",
        "asset_class",
        "execution_environment",
        "data_schema_version",
        "feature_contract_version",
    )

    return {
        key: learning_scope.get(key)
        for key in safe_keys
    }


def _base_feature_names() -> list[str]:

    raw = getattr(
        feature_list_module,
        "FEATURE_COLUMNS",
        None,
    )

    if not isinstance(
        raw,
        (list, tuple),
    ):
        raise RuntimeError(
            "FEATURE_COLUMNS_CONTRACT_MISSING"
        )

    features = [
        str(value)
        for value in raw
    ]

    _require(
        len(features)
        == EXPECTED_BASE_FEATURE_COUNT,
        (
            "UNEXPECTED_BASE_FEATURE_COUNT:"
            f"{len(features)}"
        ),
    )

    _require(
        len(set(features))
        == len(features),
        "DUPLICATE_BASE_FEATURE_NAMES",
    )

    return features


def _comparison_feature_names(
    base_features: Sequence[str],
) -> list[str]:

    result = [
        f"m5_{feature}"
        for feature in base_features
    ]

    result.extend(
        BROKER_SENSITIVE_FEATURES
    )

    expected_count = (
        EXPECTED_BASE_FEATURE_COUNT
        +
        len(BROKER_SENSITIVE_FEATURES)
    )

    _require(
        len(result)
        == expected_count,
        (
            "UNEXPECTED_M5_COMPARISON_FEATURE_COUNT:"
            f"{len(result)}"
        ),
    )

    return result


def _load_frozen_train_only(
    dataset_path: Path,
    feature_names: Sequence[str],
) -> pd.DataFrame:

    use_columns = [
        "decision_time",
        "dataset_split",
        *feature_names,
    ]

    frame = pd.read_csv(
        dataset_path,
        usecols=use_columns,
        nrows=EXPECTED_TRAIN_ROWS,
    )

    _require(
        len(frame)
        == EXPECTED_TRAIN_ROWS,
        (
            "FROZEN_TRAIN_ROW_COUNT_MISMATCH:"
            f"{len(frame)}"
        ),
    )

    split_values = {
        str(value).strip().upper()
        for value
        in frame[
            "dataset_split"
        ].dropna().unique()
    }

    _require(
        split_values == {"TRAIN"},
        (
            "NON_TRAIN_ROWS_TOUCHED:"
            f"{sorted(split_values)}"
        ),
    )

    frame[
        "decision_time"
    ] = pd.to_datetime(
        frame[
            "decision_time"
        ],
        utc=True,
        errors="raise",
    )

    _require(
        not bool(
            frame[
                "decision_time"
            ].duplicated().any()
        ),
        "DUPLICATE_FROZEN_TRAIN_DECISION_TIME",
    )

    _require(
        bool(
            frame[
                "decision_time"
            ].is_monotonic_increasing
        ),
        "FROZEN_TRAIN_DECISION_TIME_NOT_SORTED",
    )

    return (
        frame
        .sort_values(
            "decision_time"
        )
        .reset_index(
            drop=True
        )
    )


def _mt5_rates_frame(
    rates: Any,
) -> pd.DataFrame:

    _require(
        rates is not None,
        (
            "MT5_COPY_RATES_RANGE_RETURNED_NONE:"
            f"{mt5.last_error()}"
        ),
    )

    frame = pd.DataFrame(rates)

    _require(
        not frame.empty,
        "MT5_M5_HISTORY_EMPTY",
    )

    required_columns = {
        "time",
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
        "spread",
    }

    missing = sorted(
        required_columns
        -
        set(frame.columns)
    )

    _require(
        not missing,
        (
            "MT5_M5_REQUIRED_COLUMNS_MISSING:"
            f"{missing}"
        ),
    )

    frame[
        "time"
    ] = pd.to_datetime(
        frame[
            "time"
        ],
        unit="s",
        utc=True,
        errors="raise",
    )

    numeric_columns = (
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
        "spread",
        "real_volume",
    )

    for column in numeric_columns:

        if column not in frame.columns:
            continue

        frame[
            column
        ] = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

    frame = (
        frame
        .sort_values("time")
        .drop_duplicates(
            subset=["time"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    _require(
        len(frame) >= 250,
        (
            "CURRENT_BROKER_M5_HISTORY_TOO_SMALL:"
            f"{len(frame)}"
        ),
    )

    return frame


def _generate_current_base_features(
    raw_m5: pd.DataFrame,
    base_feature_names: Sequence[str],
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

    canonical_root = (
        ROOT_DIR
        /
        "01_Data"
        /
        "Canonical"
    )

    # IMPORTANT:
    # canonical_root is keyword-only in the actual
    # TrainingMatrixBuilder constructor.
    builder = TrainingMatrixBuilder(
        canonical_root=canonical_root
    )

    generated = (
        builder
        ._generate_feature_frame(
            frame=raw_m5.copy(),
            timeframe="M5",
        )
    )

    _require(
        isinstance(
            generated,
            pd.DataFrame,
        ),
        "GENERATED_M5_FEATURES_NOT_DATAFRAME",
    )

    _require(
        not generated.empty,
        "GENERATED_M5_FEATURES_EMPTY",
    )

    generated = generated.copy()

    time_column: str | None = None

    for candidate in (
        "feature_availability_time",
        "decision_time",
        "time",
        "timestamp",
        "bar_time",
    ):

        if candidate in generated.columns:

            time_column = candidate
            break

    if time_column is None:

        if isinstance(
            generated.index,
            pd.DatetimeIndex,
        ):

            generated = (
                generated
                .reset_index()
            )

            time_column = str(
                generated.columns[0]
            )

        else:

            raise RuntimeError(
                (
                    "GENERATED_M5_FEATURE_TIME_COLUMN_NOT_FOUND:"
                    f"{list(generated.columns)[:20]}"
                )
            )

    generated[
        "decision_time"
    ] = pd.to_datetime(
        generated[
            time_column
        ],
        utc=True,
        errors="raise",
    )

    output = pd.DataFrame(
        {
            "decision_time": (
                generated[
                    "decision_time"
                ]
            )
        }
    )

    mapping: dict[str, str] = {}

    missing: list[str] = []

    for base_name in base_feature_names:

        expected = (
            "m5_"
            +
            base_name
        )

        source_name: str | None = None

        for candidate in (
            expected,
            base_name,
        ):

            if candidate in generated.columns:

                source_name = candidate
                break

        if source_name is None:

            missing.append(expected)
            continue

        output[
            expected
        ] = pd.to_numeric(
            generated[
                source_name
            ],
            errors="coerce",
        )

        mapping[
            expected
        ] = source_name

    _require(
        not missing,
        (
            "GENERATED_M5_BASE_FEATURES_MISSING:"
            f"{missing}"
        ),
    )

    output = (
        output
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
        .drop_duplicates(
            subset=[
                "decision_time"
            ],
            keep="last",
        )
        .sort_values(
            "decision_time"
        )
        .reset_index(
            drop=True
        )
    )

    return (
        output,
        {
            "generated_rows": int(
                len(generated)
            ),
            "usable_generated_rows": int(
                len(output)
            ),
            "generated_time_column": (
                time_column
            ),
            "feature_mapping": mapping,
        },
    )


def _auxiliary_candidate(
    raw_m5: pd.DataFrame,
    *,
    shift_seconds: int,
) -> pd.DataFrame:

    volume = pd.to_numeric(
        raw_m5[
            "tick_volume"
        ],
        errors="coerce",
    ).astype(
        np.float64
    )

    spread = pd.to_numeric(
        raw_m5[
            "spread"
        ],
        errors="coerce",
    ).astype(
        np.float64
    )

    volume = volume.clip(
        lower=0.0
    )

    spread = spread.clip(
        lower=0.0
    )

    rolling_volume = (
        volume
        .rolling(
            window=20
        )
        .mean()
        .replace(
            0.0,
            np.nan,
        )
    )

    ratio = (
        volume
        /
        rolling_volume
    )

    decision_time = (
        raw_m5[
            "time"
        ]
        +
        pd.to_timedelta(
            shift_seconds,
            unit="s",
        )
    )

    return pd.DataFrame(
        {
            "decision_time": (
                decision_time
            ),
            "m5_spread_points": (
                spread
            ),
            "m5_tick_volume_log1p": (
                np.log1p(volume)
            ),
            "m5_tick_volume_ratio20": (
                ratio
            ),
        }
    )


def _timestamp_ns_set(
    values: Any,
) -> set[int]:

    timestamps = pd.to_datetime(
        pd.Series(values),
        utc=True,
        errors="raise",
    )

    nanoseconds = (
        timestamps
        .astype("int64")
        .to_numpy(
            dtype=np.int64
        )
    )

    return {
        int(value)
        for value
        in nanoseconds.tolist()
    }


def _select_auxiliary_alignment(
    raw_m5: pd.DataFrame,
    generated_times: pd.Series,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

    generated_ns = (
        _timestamp_ns_set(
            generated_times
        )
    )

    candidates: list[
        tuple[
            int,
            int,
            pd.DataFrame,
        ]
    ] = []

    for shift_seconds in (
        0,
        M5_SECONDS,
    ):

        candidate = (
            _auxiliary_candidate(
                raw_m5,
                shift_seconds=shift_seconds,
            )
        )

        candidate_ns = (
            _timestamp_ns_set(
                candidate[
                    "decision_time"
                ]
            )
        )

        overlap = len(
            candidate_ns
            &
            generated_ns
        )

        candidates.append(
            (
                int(overlap),
                shift_seconds,
                candidate,
            )
        )

    candidates.sort(
        key=lambda item: (
            item[0],
            (
                1
                if item[1]
                == M5_SECONDS
                else
                0
            ),
        ),
        reverse=True,
    )

    best_overlap = candidates[0][0]
    best_shift = candidates[0][1]
    best_frame = candidates[0][2]

    _require(
        best_overlap > 0,
        "AUXILIARY_FEATURE_ALIGNMENT_FAILED",
    )

    overlap_document = {
        str(shift): int(overlap)
        for (
            overlap,
            shift,
            _,
        )
        in candidates
    }

    return (
        best_frame,
        {
            "selected_shift_seconds": int(
                best_shift
            ),
            "selected_overlap_rows": int(
                best_overlap
            ),
            "candidate_overlap_rows": (
                overlap_document
            ),
        },
    )


def _build_current_m5_comparison_frame(
    raw_m5: pd.DataFrame,
    base_feature_names: Sequence[str],
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:

    (
        generated,
        generated_meta,
    ) = (
        _generate_current_base_features(
            raw_m5,
            base_feature_names,
        )
    )

    (
        auxiliary,
        auxiliary_meta,
    ) = (
        _select_auxiliary_alignment(
            raw_m5,
            generated[
                "decision_time"
            ],
        )
    )

    current = (
        generated
        .merge(
            auxiliary,
            on="decision_time",
            how="left",
            validate="one_to_one",
        )
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
        .sort_values(
            "decision_time"
        )
        .reset_index(
            drop=True
        )
    )

    return (
        current,
        {
            "base_generation": (
                generated_meta
            ),
            "auxiliary_alignment": (
                auxiliary_meta
            ),
            "comparison_rows": int(
                len(current)
            ),
        },
    )


def _finite_array(
    values: Any,
) -> np.ndarray:

    numeric = pd.to_numeric(
        pd.Series(values),
        errors="coerce",
    ).to_numpy(
        dtype=np.float64
    )

    return numeric[
        np.isfinite(numeric)
    ]


def _distribution_summary(
    values: Any,
) -> dict[str, Any]:

    array = (
        _finite_array(values)
    )

    if array.size == 0:

        return {
            "rows": 0,
            "mean": None,
            "std": None,
            "p05": None,
            "p25": None,
            "median": None,
            "p75": None,
            "p95": None,
        }

    return {
        "rows": int(
            array.size
        ),
        "mean": float(
            np.mean(array)
        ),
        "std": float(
            np.std(array)
        ),
        "p05": float(
            np.percentile(
                array,
                5,
            )
        ),
        "p25": float(
            np.percentile(
                array,
                25,
            )
        ),
        "median": float(
            np.percentile(
                array,
                50,
            )
        ),
        "p75": float(
            np.percentile(
                array,
                75,
            )
        ),
        "p95": float(
            np.percentile(
                array,
                95,
            )
        ),
    }


def _population_stability_index(
    reference: np.ndarray,
    current: np.ndarray,
) -> float | None:

    if (
        reference.size < 100
        or
        current.size < 100
    ):
        return None

    quantiles = np.linspace(
        0.0,
        1.0,
        11,
    )

    edges = np.quantile(
        reference,
        quantiles,
    )

    edges = np.unique(edges)

    if edges.size < 3:
        return None

    edges[0] = -np.inf
    edges[-1] = np.inf

    reference_counts, _ = np.histogram(
        reference,
        bins=edges,
    )

    current_counts, _ = np.histogram(
        current,
        bins=edges,
    )

    reference_pct = (
        reference_counts.astype(
            np.float64
        )
        /
        max(
            1,
            int(
                reference_counts.sum()
            ),
        )
    )

    current_pct = (
        current_counts.astype(
            np.float64
        )
        /
        max(
            1,
            int(
                current_counts.sum()
            ),
        )
    )

    epsilon = 1e-6

    reference_pct = np.clip(
        reference_pct,
        epsilon,
        None,
    )

    current_pct = np.clip(
        current_pct,
        epsilon,
        None,
    )

    psi = np.sum(
        (
            current_pct
            -
            reference_pct
        )
        *
        np.log(
            current_pct
            /
            reference_pct
        )
    )

    return float(psi)


def _paired_correlation(
    reference: np.ndarray,
    current: np.ndarray,
) -> float | None:

    if (
        reference.size < 3
        or
        current.size
        !=
        reference.size
    ):
        return None

    reference_std = float(
        np.std(reference)
    )

    current_std = float(
        np.std(current)
    )

    if (
        reference_std <= 1e-12
        or
        current_std <= 1e-12
    ):
        return None

    value = float(
        np.corrcoef(
            reference,
            current,
        )[0, 1]
    )

    if not math.isfinite(value):
        return None

    return value


def _feature_comparison(
    paired: pd.DataFrame,
    feature: str,
) -> dict[str, Any]:

    reference_column = (
        f"{feature}_frozen"
    )

    current_column = (
        f"{feature}_current"
    )

    reference_values = pd.to_numeric(
        paired[
            reference_column
        ],
        errors="coerce",
    ).to_numpy(
        dtype=np.float64
    )

    current_values = pd.to_numeric(
        paired[
            current_column
        ],
        errors="coerce",
    ).to_numpy(
        dtype=np.float64
    )

    valid_mask = (
        np.isfinite(
            reference_values
        )
        &
        np.isfinite(
            current_values
        )
    )

    reference = (
        reference_values[
            valid_mask
        ]
    )

    current = (
        current_values[
            valid_mask
        ]
    )

    reference_summary = (
        _distribution_summary(
            reference
        )
    )

    current_summary = (
        _distribution_summary(
            current
        )
    )

    reference_std = (
        _safe_float(
            reference_summary.get(
                "std"
            )
        )
    )

    standardized_mean_shift: (
        float
        |
        None
    ) = None

    median_shift_reference_std: (
        float
        |
        None
    ) = None

    paired_median_abs_diff_reference_std: (
        float
        |
        None
    ) = None

    if (
        reference_std is not None
        and
        reference_std > 1e-12
        and
        reference.size > 0
    ):

        standardized_mean_shift = float(
            abs(
                float(
                    np.mean(current)
                )
                -
                float(
                    np.mean(reference)
                )
            )
            /
            reference_std
        )

        median_shift_reference_std = float(
            abs(
                float(
                    np.median(current)
                )
                -
                float(
                    np.median(reference)
                )
            )
            /
            reference_std
        )

        paired_median_abs_diff_reference_std = float(
            np.median(
                np.abs(
                    current
                    -
                    reference
                )
            )
            /
            reference_std
        )

    psi = (
        _population_stability_index(
            reference,
            current,
        )
    )

    correlation = (
        _paired_correlation(
            reference,
            current,
        )
    )

    material_shift = bool(
        (
            psi is not None
            and
            psi
            >=
            PSI_MATERIAL_THRESHOLD
        )
        or
        (
            standardized_mean_shift
            is not None
            and
            standardized_mean_shift
            >=
            STANDARDIZED_MEAN_SHIFT_THRESHOLD
        )
    )

    return {
        "feature": feature,
        "category": (
            "BROKER_SENSITIVE"
            if feature
            in BROKER_SENSITIVE_FEATURES
            else
            "PRICE_CANDLE"
        ),
        "paired_rows": int(
            reference.size
        ),
        "frozen_train": (
            reference_summary
        ),
        "current_broker": (
            current_summary
        ),
        "psi": psi,
        "psi_warning": bool(
            psi is not None
            and
            psi
            >=
            PSI_WARNING_THRESHOLD
        ),
        "standardized_mean_shift": (
            standardized_mean_shift
        ),
        "median_shift_reference_std": (
            median_shift_reference_std
        ),
        "paired_correlation": (
            correlation
        ),
        "paired_median_abs_diff_reference_std": (
            paired_median_abs_diff_reference_std
        ),
        "material_distribution_shift": (
            material_shift
        ),
    }


def _median_finite(
    values: Sequence[
        float
        |
        None
    ],
) -> float | None:

    finite = np.asarray(
        [
            float(value)
            for value in values
            if (
                value is not None
                and
                math.isfinite(
                    float(value)
                )
            )
        ],
        dtype=np.float64,
    )

    if finite.size == 0:
        return None

    return float(
        np.median(finite)
    )


def _summarize_comparisons(
    comparisons: Sequence[
        Mapping[str, Any]
    ],
) -> dict[str, Any]:

    price = [
        item
        for item in comparisons
        if item.get("category")
        == "PRICE_CANDLE"
    ]

    sensitive = [
        item
        for item in comparisons
        if item.get("category")
        == "BROKER_SENSITIVE"
    ]

    price_correlations = [
        _safe_float(
            item.get(
                "paired_correlation"
            )
        )
        for item in price
    ]

    price_psis = [
        _safe_float(
            item.get("psi")
        )
        for item in price
    ]

    price_mean_shifts = [
        _safe_float(
            item.get(
                "standardized_mean_shift"
            )
        )
        for item in price
    ]

    correlation_values = [
        value
        for value
        in price_correlations
        if value is not None
    ]

    strong_correlation_count = sum(
        1
        for value
        in correlation_values
        if value
        >=
        PRICE_CORRELATION_STRONG_THRESHOLD
    )

    weak_correlation_count = sum(
        1
        for value
        in correlation_values
        if value
        <
        PRICE_CORRELATION_WARNING_THRESHOLD
    )

    sensitive_shifted = [
        str(
            item.get(
                "feature"
            )
        )
        for item in sensitive
        if bool(
            item.get(
                "material_distribution_shift",
                False,
            )
        )
    ]

    return {
        "price_candle_feature_count": int(
            len(price)
        ),
        "price_candle_features_with_correlation": int(
            len(
                correlation_values
            )
        ),
        "price_candle_median_paired_correlation": (
            _median_finite(
                price_correlations
            )
        ),
        "price_candle_median_psi": (
            _median_finite(
                price_psis
            )
        ),
        "price_candle_median_standardized_mean_shift": (
            _median_finite(
                price_mean_shifts
            )
        ),
        "price_candle_strong_correlation_count": int(
            strong_correlation_count
        ),
        "price_candle_weak_correlation_count": int(
            weak_correlation_count
        ),
        "broker_sensitive_feature_count": int(
            len(sensitive)
        ),
        "broker_sensitive_materially_shifted": (
            sensitive_shifted
        ),
    }


def _classification(
    *,
    overlap_rows: int,
    summary: Mapping[str, Any],
) -> dict[str, Any]:

    if (
        overlap_rows
        <
        MIN_REQUIRED_OVERLAP_ROWS
    ):

        return {
            "classification": (
                "INSUFFICIENT_CURRENT_BROKER_HISTORY_OVERLAP"
            ),
            "scope": (
                "M5_PRELIMINARY"
            ),
            "reason": (
                "NOT_ENOUGH_SAME_TIMESTAMP_ROWS"
            ),
            "full_333_portability_claimed": (
                False
            ),
        }

    price_feature_count = int(
        summary.get(
            "price_candle_feature_count",
            0,
        )
    )

    correlation_count = int(
        summary.get(
            "price_candle_features_with_correlation",
            0,
        )
    )

    median_correlation = (
        _safe_float(
            summary.get(
                "price_candle_median_paired_correlation"
            )
        )
    )

    median_psi = (
        _safe_float(
            summary.get(
                "price_candle_median_psi"
            )
        )
    )

    weak_count = int(
        summary.get(
            "price_candle_weak_correlation_count",
            0,
        )
    )

    raw_sensitive_shifted = (
        summary.get(
            "broker_sensitive_materially_shifted",
            [],
        )
    )

    if isinstance(
        raw_sensitive_shifted,
        list,
    ):
        sensitive_shifted = (
            raw_sensitive_shifted
        )
    else:
        sensitive_shifted = []

    if (
        price_feature_count
        <
        MIN_REQUIRED_PRICE_FEATURES
        or
        correlation_count
        <
        MIN_REQUIRED_PRICE_FEATURES
    ):

        return {
            "classification": (
                "M5_FEATURE_COMPARISON_INCOMPLETE"
            ),
            "scope": (
                "M5_PRELIMINARY"
            ),
            "reason": (
                "TOO_FEW_PRICE_FEATURES_COMPARABLE"
            ),
            "full_333_portability_claimed": (
                False
            ),
        }

    broad_price_shift = bool(
        (
            median_correlation
            is not None
            and
            median_correlation
            <
            PRICE_CORRELATION_WARNING_THRESHOLD
        )
        or
        (
            median_psi
            is not None
            and
            median_psi
            >=
            PSI_MATERIAL_THRESHOLD
        )
        or
        (
            weak_count
            >
            max(
                3,
                int(
                    0.25
                    *
                    correlation_count
                ),
            )
        )
    )

    if broad_price_shift:

        return {
            "classification": (
                "RETRAIN_OR_RECALIBRATE_REQUIRED"
            ),
            "scope": (
                "M5_PRELIMINARY"
            ),
            "reason": (
                "BROAD_SAME_TIMESTAMP_PRICE_FEATURE_DOMAIN_SHIFT"
            ),
            "full_333_portability_claimed": (
                False
            ),
        }

    if sensitive_shifted:

        return {
            "classification": (
                "NORMALIZATION_REQUIRED"
            ),
            "scope": (
                "M5_PRELIMINARY"
            ),
            "reason": (
                "PRICE_FEATURES_RELATIVELY_STABLE_BUT_"
                "BROKER_SENSITIVE_FEATURES_SHIFTED"
            ),
            "full_333_portability_claimed": (
                False
            ),
        }

    return {
        "classification": (
            "M5_PRELIMINARY_PORTABLE"
        ),
        "scope": (
            "M5_PRELIMINARY"
        ),
        "reason": (
            "NO_MATERIAL_M5_SHIFT_DETECTED_UNDER_CURRENT_THRESHOLDS"
        ),
        "full_333_portability_claimed": (
            False
        ),
    }


def run_analysis() -> dict[str, Any]:

    trainer = (
        XAUUSDHierarchicalModelV4Trainer()
    )

    snapshot = (
        sweep_module
        ._discover_frozen_training_snapshot(
            trainer=trainer
        )
    )

    dataset_path = (
        _snapshot_dataset_path(
            snapshot
        )
    )

    manifest_path = (
        _snapshot_manifest_path(
            snapshot,
            dataset_path,
        )
    )

    _validate_snapshot(
        snapshot,
        dataset_path,
        manifest_path,
    )

    manifest = (
        _load_manifest(
            manifest_path
        )
    )

    base_features = (
        _base_feature_names()
    )

    comparison_features = (
        _comparison_feature_names(
            base_features
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

    missing_contract_features = sorted(
        set(comparison_features)
        -
        manifest_feature_columns
    )

    _require(
        not missing_contract_features,
        (
            "M5_COMPARISON_FEATURES_NOT_IN_FROZEN_CONTRACT:"
            f"{missing_contract_features}"
        ),
    )

    frozen_train = (
        _load_frozen_train_only(
            dataset_path,
            comparison_features,
        )
    )

    train_start_raw = (
        frozen_train[
            "decision_time"
        ].min()
    )

    train_end_raw = (
        frozen_train[
            "decision_time"
        ].max()
    )

    train_start = pd.Timestamp(
        train_start_raw
    )

    train_end = pd.Timestamp(
        train_end_raw
    )

    _require(
        not pd.isna(train_start),
        "FROZEN_TRAIN_START_TIMESTAMP_INVALID",
    )

    _require(
        not pd.isna(train_end),
        "FROZEN_TRAIN_END_TIMESTAMP_INVALID",
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
            BrokerCostAdapter(
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

        symbol_info = (
            mt5.symbol_info(
                broker_symbol
            )
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

            selected = (
                mt5.symbol_select(
                    broker_symbol,
                    True,
                )
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
                days=HISTORY_WARMUP_DAYS
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
            _mt5_rates_frame(
                rates
            )
        )

        (
            current_frame,
            generation_meta,
        ) = (
            _build_current_m5_comparison_frame(
                raw_m5,
                base_features,
            )
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
            current_frame[
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
            _feature_comparison(
                paired,
                feature,
            )
            for feature
            in comparison_features
        ]

        summary = (
            _summarize_comparisons(
                comparisons
            )
        )

        classification = (
            _classification(
                overlap_rows=overlap_rows,
                summary=summary,
            )
        )

        history_start = pd.Timestamp(
            raw_m5[
                "time"
            ].min()
        )

        history_end = pd.Timestamp(
            raw_m5[
                "time"
            ].max()
        )

        return {
            "valid": True,
            "reason": (
                "OK_XAUUSD_CURRENT_BROKER_M5_DOMAIN_SHIFT"
            ),
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "research_scope": (
                "M5_SAME_TIMESTAMP_DOMAIN_SHIFT_PRELIMINARY"
            ),
            "frozen_reference": {
                "dataset_id": (
                    EXPECTED_DATASET_ID
                ),
                "dataset_sha256": (
                    EXPECTED_DATASET_SHA256
                ),
                "training_manifest_sha256": (
                    EXPECTED_TRAINING_MANIFEST_SHA256
                ),
                "training_contract": (
                    EXPECTED_TRAINING_CONTRACT
                ),
                "identity": (
                    _safe_frozen_identity(
                        manifest
                    )
                ),
                "rows_loaded": int(
                    len(frozen_train)
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
                    CANONICAL_SYMBOL
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
                "historical_m5_rows_fetched": int(
                    len(raw_m5)
                ),
                "history_time_start": (
                    history_start.isoformat()
                ),
                "history_time_end": (
                    history_end.isoformat()
                ),
            },
            "feature_contract": {
                "exact_existing_base_generator_used": (
                    True
                ),
                "training_matrix_builder_constructor_call": (
                    "TrainingMatrixBuilder(canonical_root=...)"
                ),
                "base_feature_count": int(
                    len(base_features)
                ),
                "broker_sensitive_feature_count": int(
                    len(
                        BROKER_SENSITIVE_FEATURES
                    )
                ),
                "comparison_feature_count": int(
                    len(
                        comparison_features
                    )
                ),
                "broker_sensitive_features": list(
                    BROKER_SENSITIVE_FEATURES
                ),
                "feature_generation": (
                    generation_meta
                ),
            },
            "same_timestamp_overlap": {
                "rows": (
                    overlap_rows
                ),
                "frozen_train_rows": int(
                    len(frozen_train)
                ),
                "fraction_of_frozen_train": (
                    overlap_fraction
                ),
                "minimum_required_rows": (
                    MIN_REQUIRED_OVERLAP_ROWS
                ),
            },
            "summary": (
                summary
            ),
            "classification": (
                classification
            ),
            "feature_comparisons": (
                comparisons
            ),
            "thresholds": {
                "psi_warning": (
                    PSI_WARNING_THRESHOLD
                ),
                "psi_material": (
                    PSI_MATERIAL_THRESHOLD
                ),
                "standardized_mean_shift_material": (
                    STANDARDIZED_MEAN_SHIFT_THRESHOLD
                ),
                "price_correlation_warning": (
                    PRICE_CORRELATION_WARNING_THRESHOLD
                ),
                "price_correlation_strong": (
                    PRICE_CORRELATION_STRONG_THRESHOLD
                ),
            },
            "scientific_policy": {
                "frozen_dataset_mutated": (
                    False
                ),
                "frozen_manifest_mutated": (
                    False
                ),
                "train_loaded": (
                    True
                ),
                "train_rows_expected": (
                    EXPECTED_TRAIN_ROWS
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
            },
            "decision_contract": {
                "if_normalization_required": (
                    "CREATE_NEW_CROSS_BROKER_NORMALIZED_"
                    "FEATURE_CONTRACT_BEFORE_RETRAINING"
                ),
                "if_retrain_or_recalibrate_required": (
                    "EXPAND_AUDIT_TO_FULL_MTF_AND_DOMAIN_FEATURES_"
                    "BEFORE_MODEL_DECISION"
                ),
                "if_m5_preliminary_portable": (
                    "EXPAND_TO_FULL_MTF_PLUS_63_DOMAIN_FEATURE_AUDIT"
                ),
                "if_insufficient_history_overlap": (
                    "FIX_OR_EXTEND_CURRENT_BROKER_HISTORY_AVAILABILITY"
                ),
                "full_333_feature_portability_not_decided_here": (
                    True
                ),
                "test_holdout_remains_untouched": (
                    True
                ),
            },
            "live_authorized": False,
        }

    finally:
        mt5.shutdown()


def main() -> int:

    try:

        result = (
            run_analysis()
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
                        "XAUUSD_CURRENT_BROKER_M5_DOMAIN_SHIFT_FAILED"
                    ),
                    "analysis_version": (
                        ANALYSIS_VERSION
                    ),
                    "error_type": (
                        type(exc).__name__
                    ),
                    "error": (
                        str(exc)
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