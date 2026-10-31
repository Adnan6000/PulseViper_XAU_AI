from __future__ import annotations

import importlib
import json
import math
import os
import sys

from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


def _find_repo_root(start: Path) -> Path:
    resolved = start.resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "02_AI").is_dir():
            return candidate
    return resolved.parents[4]

ROOT_DIR = _find_repo_root(Path(__file__))


if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_FLOAT_ROUNDTRIP_DIAGNOSTIC_V1"
)


PROJECTOR_MODULE = (
    "02_AI.Dataset.portable_training_feature_projector"
)


projector_module: Any = importlib.import_module(
    PROJECTOR_MODULE
)


PortableTrainingFeatureProjector = (
    projector_module
    .PortableTrainingFeatureProjector
)


SOURCE_CONTRACT = (
    "XAUUSD_MTF_TRAINING_V3"
)

PORTABLE_CONTRACT = (
    "XAUUSD_MTF_PORTABLE_FEATURE_V1"
)


EXPECTED_SOURCE_DATASET_ID = (
    "train_66ff363d25d8143d4e2c3410"
)

EXPECTED_SOURCE_DATASET_SHA256 = (
    "66ff363d25d8143d4e2c3410964ad26b5bd72f2e98806c3e0997ce420d18413d"
)

EXPECTED_SOURCE_MANIFEST_SHA256 = (
    "a205403a6cb5a2d1b17159a2296d1f4afb01ea5b9b90b2710feafa7dd9476aa3"
)


EXPECTED_PORTABLE_DATASET_ID = (
    "portable_cff75b0686383a3ab6f8352b"
)

EXPECTED_PORTABLE_DATASET_SHA256 = (
    "cff75b0686383a3ab6f8352bfcdcd55308b99b7a4c6edbf7d2e7215f6f33dd07"
)

EXPECTED_PORTABLE_MANIFEST_SHA256 = (
    "1b8e3599b227c9cbbc6b12f8ab0e275ca4deb4a65839fb626ca90720d59512dc"
)


EXPECTED_SOURCE_FEATURE_COUNT = 333

EXPECTED_PORTABLE_FEATURE_COUNT = 331

EXPECTED_TOTAL_ROWS = 99945

EXPECTED_TRAIN_ROWS = 69966


DROPPED_FEATURES = (
    "m5_spread_points",
    "m5_tick_volume_log1p",
)


FOCUS_FEATURE = (
    "utc_hour_cos"
)


FLOAT64_EPSILON = float(
    np.finfo(
        np.float64
    ).eps
)


SERIALIZATION_MAX_ABS_DIFFERENCE = (
    2.0e-15
)

SERIALIZATION_MAX_SCALED_EPSILON_UNITS = (
    8.0
)


MAX_RAW_TEXT_FEATURES_TO_INSPECT = (
    20
)


EXCLUDED_SCAN_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
}


def _require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise RuntimeError(
            reason
        )


def _string_list(
    value: Any,
    *,
    field_name: str,
) -> list[str]:

    if not isinstance(
        value,
        list,
    ):
        raise RuntimeError(
            (
                "EXPECTED_LIST_MISSING:"
                f"{field_name}"
            )
        )

    result = [
        str(
            item
        )
        for item
        in value
    ]

    if any(
        not item
        for item
        in result
    ):
        raise RuntimeError(
            (
                "EMPTY_LIST_VALUE:"
                f"{field_name}"
            )
        )

    return result


def _manifest_files(
    root: Path,
):

    for (
        current_root,
        directory_names,
        file_names,
    ) in os.walk(
        root
    ):

        directory_names[:] = [
            name
            for name
            in directory_names
            if (
                name
                not in
                EXCLUDED_SCAN_DIRECTORIES
            )
        ]

        for file_name in file_names:

            if not file_name.endswith(
                ".manifest.json"
            ):
                continue

            yield (
                Path(
                    current_root
                )
                /
                file_name
            )


def _search_roots(
) -> list[Path]:

    roots: list[Path] = []

    preferred = (
        ROOT_DIR
        /
        "03_Data"
    )

    if preferred.is_dir():
        roots.append(
            preferred
        )

    roots.append(
        ROOT_DIR
    )

    result: list[Path] = []

    seen: set[Path] = set()

    for root in roots:

        resolved = (
            root.resolve()
        )

        if resolved in seen:
            continue

        seen.add(
            resolved
        )

        result.append(
            root
        )

    return result


def _discover_artifact(
    *,
    dataset_id: str,
    dataset_sha256: str,
    manifest_sha256: str,
    training_contract: str,
) -> tuple[
    Path,
    Path,
    dict[str, Any],
]:

    candidates: list[
        tuple[
            Path,
            Path,
            dict[str, Any],
        ]
    ] = []

    seen: set[Path] = set()

    for root in (
        _search_roots()
    ):

        for manifest_path in (
            _manifest_files(
                root
            )
        ):

            resolved_manifest = (
                manifest_path.resolve()
            )

            if resolved_manifest in seen:
                continue

            seen.add(
                resolved_manifest
            )

            try:

                observed_manifest_sha256 = (
                    PortableTrainingFeatureProjector
                    ._sha256_file(
                        manifest_path
                    )
                )

            except OSError:
                continue

            if (
                observed_manifest_sha256
                !=
                manifest_sha256
            ):
                continue

            try:

                manifest = (
                    PortableTrainingFeatureProjector
                    ._load_json(
                        manifest_path
                    )
                )

            except Exception:
                continue

            if (
                str(
                    manifest.get(
                        "dataset_id",
                        "",
                    )
                )
                !=
                dataset_id
            ):
                continue

            if (
                str(
                    manifest.get(
                        "dataset_sha256",
                        "",
                    )
                )
                !=
                dataset_sha256
            ):
                continue

            if (
                str(
                    manifest.get(
                        "training_contract_version",
                        "",
                    )
                )
                !=
                training_contract
            ):
                continue

            dataset_filename = str(
                manifest.get(
                    "dataset_filename",
                    "",
                )
            ).strip()

            if not dataset_filename:
                continue

            dataset_path = (
                manifest_path.parent
                /
                dataset_filename
            )

            if not dataset_path.is_file():
                continue

            try:

                observed_dataset_sha256 = (
                    PortableTrainingFeatureProjector
                    ._sha256_file(
                        dataset_path
                    )
                )

            except OSError:
                continue

            if (
                observed_dataset_sha256
                !=
                dataset_sha256
            ):
                continue

            candidates.append(
                (
                    dataset_path,
                    manifest_path,
                    manifest,
                )
            )

    _require(
        len(
            candidates
        )
        ==
        1,
        (
            "ARTIFACT_DISCOVERY_COUNT_INVALID:"
            f"{dataset_id}:"
            f"{len(candidates)}"
        ),
    )

    return candidates[
        0
    ]


def _portable_features(
    *,
    source_manifest: Mapping[
        str,
        Any,
    ],
    portable_manifest: Mapping[
        str,
        Any,
    ],
) -> list[str]:

    source_features = (
        _string_list(
            source_manifest.get(
                "feature_columns"
            ),
            field_name=(
                "source.feature_columns"
            ),
        )
    )

    portable_features = (
        _string_list(
            portable_manifest.get(
                "feature_columns"
            ),
            field_name=(
                "portable.feature_columns"
            ),
        )
    )

    _require(
        len(
            source_features
        )
        ==
        EXPECTED_SOURCE_FEATURE_COUNT,
        (
            "SOURCE_FEATURE_COUNT_MISMATCH:"
            f"{len(source_features)}"
        ),
    )

    _require(
        len(
            portable_features
        )
        ==
        EXPECTED_PORTABLE_FEATURE_COUNT,
        (
            "PORTABLE_FEATURE_COUNT_MISMATCH:"
            f"{len(portable_features)}"
        ),
    )

    expected = [
        feature
        for feature
        in source_features
        if (
            feature
            not in
            set(
                DROPPED_FEATURES
            )
        )
    ]

    _require(
        portable_features
        ==
        expected,
        "PORTABLE_FEATURE_LIST_NOT_EXACT_PARENT_PROJECTION",
    )

    _require(
        FOCUS_FEATURE
        in
        portable_features,
        (
            "FOCUS_FEATURE_NOT_PRESENT:"
            f"{FOCUS_FEATURE}"
        ),
    )

    return portable_features


def _validate_train_is_contiguous_prefix(
    dataset_path: Path,
    *,
    artifact_name: str,
) -> dict[str, Any]:

    split = pd.read_csv(
        dataset_path,
        usecols=[
            "dataset_split"
        ],
    )[
        "dataset_split"
    ].astype(
        str
    )

    _require(
        len(
            split
        )
        ==
        EXPECTED_TOTAL_ROWS,
        (
            "TOTAL_ROW_COUNT_MISMATCH:"
            f"{artifact_name}:"
            f"{len(split)}"
        ),
    )

    first_train = (
        split.iloc[
            :EXPECTED_TRAIN_ROWS
        ]
    )

    remaining = (
        split.iloc[
            EXPECTED_TRAIN_ROWS:
        ]
    )

    _require(
        bool(
            first_train.eq(
                "TRAIN"
            ).all()
        ),
        (
            "TRAIN_NOT_CONTIGUOUS_PREFIX:"
            f"{artifact_name}"
        ),
    )

    _require(
        not bool(
            remaining.eq(
                "TRAIN"
            ).any()
        ),
        (
            "TRAIN_ROWS_FOUND_AFTER_PREFIX:"
            f"{artifact_name}"
        ),
    )

    counts = {
        str(
            key
        ): int(
            value
        )
        for (
            key,
            value,
        )
        in (
            split.value_counts()
            .to_dict()
            .items()
        )
    }

    return {
        "artifact": (
            artifact_name
        ),
        "total_rows": (
            EXPECTED_TOTAL_ROWS
        ),
        "train_rows": (
            EXPECTED_TRAIN_ROWS
        ),
        "train_is_contiguous_prefix": (
            True
        ),
        "split_rows": (
            counts
        ),
        "feature_values_loaded_during_split_check": (
            False
        ),
    }


def _load_train_features_only(
    *,
    dataset_path: Path,
    feature_columns: Sequence[str],
) -> pd.DataFrame:

    usecols = [
        "decision_time",
        *[
            str(
                feature
            )
            for feature
            in feature_columns
        ],
    ]

    frame = pd.read_csv(
        dataset_path,
        usecols=(
            usecols
        ),
        nrows=(
            EXPECTED_TRAIN_ROWS
        ),
    )

    _require(
        len(
            frame
        )
        ==
        EXPECTED_TRAIN_ROWS,
        (
            "TRAIN_FEATURE_ROW_COUNT_MISMATCH:"
            f"{len(frame)}"
        ),
    )

    _require(
        not bool(
            frame[
                "decision_time"
            ]
            .duplicated()
            .any()
        ),
        "DUPLICATE_TRAIN_DECISION_TIME",
    )

    return frame


def _numeric_array(
    series: pd.Series,
    *,
    feature: str,
) -> np.ndarray:

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    source_missing = (
        series.isna()
    )

    numeric_missing = (
        numeric.isna()
    )

    introduced_missing = int(
        (
            numeric_missing
            &
            ~source_missing
        )
        .sum()
    )

    _require(
        introduced_missing
        ==
        0,
        (
            "NON_NUMERIC_VALUES:"
            f"{feature}:"
            f"{introduced_missing}"
        ),
    )

    return np.asarray(
        numeric,
        dtype=np.float64,
    )


def _scaled_epsilon_units(
    source: np.ndarray,
    portable: np.ndarray,
) -> np.ndarray:

    absolute_difference = np.abs(
        source
        -
        portable
    )

    scale = np.maximum(
        1.0,
        np.maximum(
            np.abs(
                source
            ),
            np.abs(
                portable
            ),
        ),
    )

    denominator = (
        FLOAT64_EPSILON
        *
        scale
    )

    return (
        absolute_difference
        /
        denominator
    )


def _feature_difference(
    *,
    feature: str,
    source_series: pd.Series,
    portable_series: pd.Series,
) -> dict[str, Any]:

    source = (
        _numeric_array(
            source_series,
            feature=(
                feature
            ),
        )
    )

    portable = (
        _numeric_array(
            portable_series,
            feature=(
                feature
            ),
        )
    )

    _require(
        source.shape
        ==
        portable.shape,
        (
            "FEATURE_SHAPE_MISMATCH:"
            f"{feature}"
        ),
    )

    source_nan = np.isnan(
        source
    )

    portable_nan = np.isnan(
        portable
    )

    source_pos_inf = np.isposinf(
        source
    )

    portable_pos_inf = np.isposinf(
        portable
    )

    source_neg_inf = np.isneginf(
        source
    )

    portable_neg_inf = np.isneginf(
        portable
    )

    nan_layout_equal = bool(
        np.array_equal(
            source_nan,
            portable_nan,
        )
    )

    positive_inf_layout_equal = bool(
        np.array_equal(
            source_pos_inf,
            portable_pos_inf,
        )
    )

    negative_inf_layout_equal = bool(
        np.array_equal(
            source_neg_inf,
            portable_neg_inf,
        )
    )

    special_layout_equal = bool(
        nan_layout_equal
        and
        positive_inf_layout_equal
        and
        negative_inf_layout_equal
    )

    finite_mask = (
        np.isfinite(
            source
        )
        &
        np.isfinite(
            portable
        )
    )

    finite_source = (
        source[
            finite_mask
        ]
    )

    finite_portable = (
        portable[
            finite_mask
        ]
    )

    exact_equal_mask = (
        finite_source
        ==
        finite_portable
    )

    exact_mismatch_count = int(
        (
            ~exact_equal_mask
        )
        .sum()
    )

    max_abs_difference = (
        0.0
    )

    median_abs_difference = (
        0.0
    )

    max_scaled_epsilon_units = (
        0.0
    )

    p99_scaled_epsilon_units = (
        0.0
    )

    if (
        finite_source.size
        >
        0
    ):

        absolute_difference = np.abs(
            finite_source
            -
            finite_portable
        )

        scaled_units = (
            _scaled_epsilon_units(
                finite_source,
                finite_portable,
            )
        )

        max_abs_difference = float(
            np.max(
                absolute_difference
            )
        )

        median_abs_difference = float(
            np.median(
                absolute_difference
            )
        )

        max_scaled_epsilon_units = float(
            np.max(
                scaled_units
            )
        )

        p99_scaled_epsilon_units = float(
            np.quantile(
                scaled_units,
                0.99,
            )
        )

    within_serialization_envelope = bool(
        special_layout_equal
        and
        max_abs_difference
        <=
        SERIALIZATION_MAX_ABS_DIFFERENCE
        and
        max_scaled_epsilon_units
        <=
        SERIALIZATION_MAX_SCALED_EPSILON_UNITS
    )

    return {
        "feature": (
            feature
        ),
        "row_count": int(
            source.shape[
                0
            ]
        ),
        "finite_pair_count": int(
            finite_mask.sum()
        ),
        "nan_layout_equal": (
            nan_layout_equal
        ),
        "positive_inf_layout_equal": (
            positive_inf_layout_equal
        ),
        "negative_inf_layout_equal": (
            negative_inf_layout_equal
        ),
        "special_value_layout_equal": (
            special_layout_equal
        ),
        "bit_exact_finite_value_count": int(
            exact_equal_mask.sum()
        ),
        "non_bit_exact_finite_value_count": (
            exact_mismatch_count
        ),
        "all_finite_values_bit_exact": bool(
            exact_mismatch_count
            ==
            0
        ),
        "maximum_absolute_difference": (
            max_abs_difference
        ),
        "median_absolute_difference": (
            median_abs_difference
        ),
        "maximum_scaled_epsilon_units": (
            max_scaled_epsilon_units
        ),
        "p99_scaled_epsilon_units": (
            p99_scaled_epsilon_units
        ),
        "within_declared_float64_serialization_envelope": (
            within_serialization_envelope
        ),
    }


def _raw_text_difference(
    *,
    source_dataset_path: Path,
    portable_dataset_path: Path,
    feature: str,
) -> dict[str, Any]:

    source = pd.read_csv(
        source_dataset_path,
        usecols=[
            feature
        ],
        dtype=str,
        keep_default_na=False,
        nrows=(
            EXPECTED_TRAIN_ROWS
        ),
    )[
        feature
    ]

    portable = pd.read_csv(
        portable_dataset_path,
        usecols=[
            feature
        ],
        dtype=str,
        keep_default_na=False,
        nrows=(
            EXPECTED_TRAIN_ROWS
        ),
    )[
        feature
    ]

    _require(
        len(
            source
        )
        ==
        EXPECTED_TRAIN_ROWS,
        (
            "SOURCE_RAW_TEXT_ROW_COUNT_MISMATCH:"
            f"{feature}"
        ),
    )

    _require(
        len(
            portable
        )
        ==
        EXPECTED_TRAIN_ROWS,
        (
            "PORTABLE_RAW_TEXT_ROW_COUNT_MISMATCH:"
            f"{feature}"
        ),
    )

    mismatch_mask = (
        source
        !=
        portable
    )

    mismatch_count = int(
        mismatch_mask.sum()
    )

    examples: list[
        dict[str, Any]
    ] = []

    mismatch_indexes = (
        np.flatnonzero(
            mismatch_mask.to_numpy()
        )
    )

    for index in (
        mismatch_indexes[
            :5
        ]
    ):

        row_index = int(
            index
        )

        examples.append(
            {
                "train_row_index": (
                    row_index
                ),
                "source_text": str(
                    source.iloc[
                        row_index
                    ]
                ),
                "portable_text": str(
                    portable.iloc[
                        row_index
                    ]
                ),
            }
        )

    return {
        "feature": (
            feature
        ),
        "raw_text_mismatch_count": (
            mismatch_count
        ),
        "raw_text_exact_match_count": int(
            EXPECTED_TRAIN_ROWS
            -
            mismatch_count
        ),
        "examples": (
            examples
        ),
    }


def run_diagnostic(
) -> dict[str, Any]:

    (
        source_dataset_path,
        _source_manifest_path,
        source_manifest,
    ) = (
        _discover_artifact(
            dataset_id=(
                EXPECTED_SOURCE_DATASET_ID
            ),
            dataset_sha256=(
                EXPECTED_SOURCE_DATASET_SHA256
            ),
            manifest_sha256=(
                EXPECTED_SOURCE_MANIFEST_SHA256
            ),
            training_contract=(
                SOURCE_CONTRACT
            ),
        )
    )

    (
        portable_dataset_path,
        _portable_manifest_path,
        portable_manifest,
    ) = (
        _discover_artifact(
            dataset_id=(
                EXPECTED_PORTABLE_DATASET_ID
            ),
            dataset_sha256=(
                EXPECTED_PORTABLE_DATASET_SHA256
            ),
            manifest_sha256=(
                EXPECTED_PORTABLE_MANIFEST_SHA256
            ),
            training_contract=(
                PORTABLE_CONTRACT
            ),
        )
    )

    portable_features = (
        _portable_features(
            source_manifest=(
                source_manifest
            ),
            portable_manifest=(
                portable_manifest
            ),
        )
    )

    source_split_validation = (
        _validate_train_is_contiguous_prefix(
            source_dataset_path,
            artifact_name=(
                "FROZEN_V3"
            ),
        )
    )

    portable_split_validation = (
        _validate_train_is_contiguous_prefix(
            portable_dataset_path,
            artifact_name=(
                "PORTABLE_V1"
            ),
        )
    )

    source_train = (
        _load_train_features_only(
            dataset_path=(
                source_dataset_path
            ),
            feature_columns=(
                portable_features
            ),
        )
    )

    portable_train = (
        _load_train_features_only(
            dataset_path=(
                portable_dataset_path
            ),
            feature_columns=(
                portable_features
            ),
        )
    )

    _require(
        source_train[
            "decision_time"
        ].equals(
            portable_train[
                "decision_time"
            ]
        ),
        "TRAIN_DECISION_TIME_SEQUENCE_CHANGED",
    )

    feature_differences: list[
        dict[str, Any]
    ] = []

    non_bit_exact_features: list[
        str
    ] = []

    outside_envelope_features: list[
        str
    ] = []

    global_max_abs_difference = (
        0.0
    )

    global_max_scaled_epsilon_units = (
        0.0
    )

    total_non_bit_exact_values = (
        0
    )

    for feature in (
        portable_features
    ):

        comparison = (
            _feature_difference(
                feature=(
                    feature
                ),
                source_series=(
                    source_train[
                        feature
                    ]
                ),
                portable_series=(
                    portable_train[
                        feature
                    ]
                ),
            )
        )

        feature_differences.append(
            comparison
        )

        mismatch_count = int(
            comparison[
                "non_bit_exact_finite_value_count"
            ]
        )

        total_non_bit_exact_values += (
            mismatch_count
        )

        if mismatch_count > 0:

            non_bit_exact_features.append(
                feature
            )

        if not bool(
            comparison[
                "within_declared_float64_serialization_envelope"
            ]
        ):

            outside_envelope_features.append(
                feature
            )

        feature_max_abs = float(
            comparison[
                "maximum_absolute_difference"
            ]
        )

        feature_max_scaled = float(
            comparison[
                "maximum_scaled_epsilon_units"
            ]
        )

        global_max_abs_difference = max(
            global_max_abs_difference,
            feature_max_abs,
        )

        global_max_scaled_epsilon_units = max(
            global_max_scaled_epsilon_units,
            feature_max_scaled,
        )

    changed_feature_documents = [
        document
        for document
        in feature_differences
        if (
            int(
                document[
                    "non_bit_exact_finite_value_count"
                ]
            )
            >
            0
        )
    ]

    focus_document: (
        dict[str, Any]
        |
        None
    ) = next(
        (
            document
            for document
            in feature_differences
            if (
                str(
                    document[
                        "feature"
                    ]
                )
                ==
                FOCUS_FEATURE
            )
        ),
        None,
    )

    if focus_document is None:
        raise RuntimeError(
            (
                "FOCUS_FEATURE_COMPARISON_MISSING:"
                f"{FOCUS_FEATURE}"
            )
        )

    focus_feature_within_serialization_envelope = bool(
        focus_document[
            "within_declared_float64_serialization_envelope"
        ]
    )

    raw_text_features = (
        non_bit_exact_features[
            :MAX_RAW_TEXT_FEATURES_TO_INSPECT
        ]
    )

    if (
        FOCUS_FEATURE
        not in
        raw_text_features
    ):

        raw_text_features.append(
            FOCUS_FEATURE
        )

    raw_text_differences = [
        _raw_text_difference(
            source_dataset_path=(
                source_dataset_path
            ),
            portable_dataset_path=(
                portable_dataset_path
            ),
            feature=(
                feature
            ),
        )
        for feature
        in raw_text_features
    ]

    serialization_roundtrip_confirmed = bool(
        non_bit_exact_features
        and
        not outside_envelope_features
    )

    if (
        serialization_roundtrip_confirmed
    ):

        status = (
            "FLOAT64_CSV_SERIALIZATION_ROUNDTRIP_CONFIRMED"
        )

        reason = (
            "NON_BIT_EXACT_VALUES_ARE_CONFINED_TO_THE_"
            "PREDECLARED_MACHINE_PRECISION_SERIALIZATION_ENVELOPE_"
            "WITH_IDENTICAL_SPECIAL_VALUE_LAYOUTS"
        )

        next_action = (
            "REPLACE_READINESS_AUDIT_EXACT_BINARY_EQUALITY_WITH_"
            "STRICT_FLOAT64_SERIALIZATION_EQUIVALENCE_AND_TRUE_"
            "TRAIN_PREFIX_ONLY_FEATURE_LOADING"
        )

    elif (
        not non_bit_exact_features
    ):

        status = (
            "ALL_331_TRAIN_FEATURES_BIT_EXACT"
        )

        reason = (
            "NO_NUMERIC_ROUNDTRIP_DIFFERENCE_DETECTED"
        )

        next_action = (
            "REVIEW_ORIGINAL_READINESS_FAILURE_REPRODUCIBILITY"
        )

    else:

        status = (
            "PORTABLE_PROJECTION_NUMERIC_MUTATION_NOT_EXPLAINED_"
            "BY_FLOAT64_SERIALIZATION"
        )

        reason = (
            "ONE_OR_MORE_RETAINED_FEATURES_EXCEED_THE_"
            "PREDECLARED_MACHINE_PRECISION_SERIALIZATION_ENVELOPE"
        )

        next_action = (
            "REBUILD_PORTABLE_PROJECTOR_WITH_TEXT_PRESERVING_"
            "COLUMN_PROJECTION_BEFORE_ANY_TRAINER_READINESS_GATE"
        )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_PORTABLE_331_FLOAT_ROUNDTRIP_DIAGNOSTIC"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "research_scope": (
            "TRAIN_PREFIX_ONLY_NUMERICAL_AND_RAW_TEXT_"
            "ROUNDTRIP_DIAGNOSTIC_FOR_331_RETAINED_FEATURES"
        ),
        "decision": {
            "status": (
                status
            ),
            "reason": (
                reason
            ),
            "serialization_roundtrip_confirmed": (
                serialization_roundtrip_confirmed
            ),
            "non_bit_exact_feature_count": int(
                len(
                    non_bit_exact_features
                )
            ),
            "non_bit_exact_features": (
                non_bit_exact_features
            ),
            "outside_serialization_envelope_feature_count": int(
                len(
                    outside_envelope_features
                )
            ),
            "outside_serialization_envelope_features": (
                outside_envelope_features
            ),
            "total_non_bit_exact_finite_values": (
                total_non_bit_exact_values
            ),
            "global_maximum_absolute_difference": (
                global_max_abs_difference
            ),
            "global_maximum_scaled_epsilon_units": (
                global_max_scaled_epsilon_units
            ),
            "focus_feature": (
                FOCUS_FEATURE
            ),
            "focus_feature_within_serialization_envelope": (
                focus_feature_within_serialization_envelope
            ),
            "portable_dataset_rebuild_authorized": (
                False
            ),
            "model_training_authorized": (
                False
            ),
            "validation_evaluation_authorized": (
                False
            ),
            "test_evaluation_authorized": (
                False
            ),
            "target_contract_change_authorized": (
                False
            ),
            "live_authorized": (
                False
            ),
            "next_action": (
                next_action
            ),
        },
        "thresholds": {
            "float64_epsilon": (
                FLOAT64_EPSILON
            ),
            "serialization_max_absolute_difference": (
                SERIALIZATION_MAX_ABS_DIFFERENCE
            ),
            "serialization_max_scaled_epsilon_units": (
                SERIALIZATION_MAX_SCALED_EPSILON_UNITS
            ),
        },
        "split_validation": {
            "source": (
                source_split_validation
            ),
            "portable": (
                portable_split_validation
            ),
        },
        "focus_feature_comparison": (
            focus_document
        ),
        "changed_feature_comparisons": (
            changed_feature_documents
        ),
        "raw_text_differences": (
            raw_text_differences
        ),
        "scientific_policy": {
            "source_train_feature_values_loaded": (
                True
            ),
            "portable_train_feature_values_loaded": (
                True
            ),
            "validation_feature_values_loaded": (
                False
            ),
            "test_feature_values_loaded": (
                False
            ),
            "split_column_loaded_for_all_rows": (
                True
            ),
            "target_columns_loaded": (
                False
            ),
            "target_values_loaded": (
                False
            ),
            "target_metrics_computed": (
                False
            ),
            "validation_metrics_computed": (
                False
            ),
            "test_metrics_computed": (
                False
            ),
            "model_loaded": (
                False
            ),
            "model_trained": (
                False
            ),
            "dataset_written": (
                False
            ),
            "manifest_written": (
                False
            ),
            "feature_pipeline_modified": (
                False
            ),
            "frozen_v3_contract_mutated": (
                False
            ),
            "portable_contract_mutated": (
                False
            ),
            "mt5_used": (
                False
            ),
            "new_market_data_loaded": (
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
            "live_authorized": (
                False
            ),
            "filesystem_paths_emitted": (
                False
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
                        "XAUUSD_PORTABLE_331_FLOAT_ROUNDTRIP_"
                        "DIAGNOSTIC_FAILED"
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
                    "validation_feature_values_loaded": (
                        False
                    ),
                    "test_feature_values_loaded": (
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
                    "dataset_written": (
                        False
                    ),
                    "mt5_used": (
                        False
                    ),
                    "orders_sent": (
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