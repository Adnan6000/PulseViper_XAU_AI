from __future__ import annotations

import hashlib
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
    "XAUUSD_PORTABLE_331_TRAIN_INPUT_READINESS_AUDIT_V2"
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


EXPECTED_CONTRACT_DESIGN_FINGERPRINT_SHA256 = (
    "de389b1daa02b2d864490aa41776494baea4f9e42dbf2146c2c44b9c2660ff40"
)


EXPECTED_SOURCE_FEATURE_COUNT = 333

EXPECTED_PORTABLE_FEATURE_COUNT = 331

EXPECTED_TOTAL_ROWS = 99945

EXPECTED_TRAIN_ROWS = 69966


EXPECTED_SPLIT_ROWS = {
    "TRAIN": 69966,
    "VALIDATION": 14983,
    "TEST": 14996,
}


DROPPED_FEATURES = (
    "m5_spread_points",
    "m5_tick_volume_log1p",
)


RETAINED_RELATIVE_VOLUME_FEATURE = (
    "m5_tick_volume_ratio20"
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


def _mapping(
    document: Mapping[str, Any],
    key: str,
) -> Mapping[str, Any]:

    value = document.get(
        key
    )

    if not isinstance(
        value,
        Mapping,
    ):
        raise RuntimeError(
            (
                "EXPECTED_MAPPING_MISSING:"
                f"{key}"
            )
        )

    return value


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


def _feature_columns(
    manifest: Mapping[str, Any],
    *,
    expected_count: int,
    field_prefix: str,
) -> list[str]:

    features = (
        _string_list(
            manifest.get(
                "feature_columns"
            ),
            field_name=(
                field_prefix
                +
                ".feature_columns"
            ),
        )
    )

    _require(
        len(
            features
        )
        ==
        expected_count,
        (
            "FEATURE_COUNT_MISMATCH:"
            f"{field_prefix}:"
            f"{len(features)}:"
            f"{expected_count}"
        ),
    )

    _require(
        len(
            set(
                features
            )
        )
        ==
        len(
            features
        ),
        (
            "FEATURE_COLUMNS_NOT_UNIQUE:"
            f"{field_prefix}"
        ),
    )

    return features


def _validate_manifests(
    *,
    source_manifest: Mapping[str, Any],
    portable_manifest: Mapping[str, Any],
) -> tuple[
    list[str],
    list[str],
]:

    _require(
        str(
            source_manifest.get(
                "dataset_id",
                "",
            )
        )
        ==
        EXPECTED_SOURCE_DATASET_ID,
        "SOURCE_DATASET_ID_MISMATCH",
    )

    _require(
        str(
            source_manifest.get(
                "dataset_sha256",
                "",
            )
        )
        ==
        EXPECTED_SOURCE_DATASET_SHA256,
        "SOURCE_DATASET_SHA256_MISMATCH",
    )

    _require(
        str(
            source_manifest.get(
                "training_contract_version",
                "",
            )
        )
        ==
        SOURCE_CONTRACT,
        "SOURCE_CONTRACT_MISMATCH",
    )

    _require(
        int(
            source_manifest.get(
                "row_count",
                -1,
            )
        )
        ==
        EXPECTED_TOTAL_ROWS,
        "SOURCE_ROW_COUNT_MISMATCH",
    )

    source_features = (
        _feature_columns(
            source_manifest,
            expected_count=(
                EXPECTED_SOURCE_FEATURE_COUNT
            ),
            field_prefix=(
                "source"
            ),
        )
    )

    _require(
        str(
            portable_manifest.get(
                "dataset_id",
                "",
            )
        )
        ==
        EXPECTED_PORTABLE_DATASET_ID,
        "PORTABLE_DATASET_ID_MISMATCH",
    )

    _require(
        str(
            portable_manifest.get(
                "dataset_sha256",
                "",
            )
        )
        ==
        EXPECTED_PORTABLE_DATASET_SHA256,
        "PORTABLE_DATASET_SHA256_MISMATCH",
    )

    _require(
        str(
            portable_manifest.get(
                "training_contract_version",
                "",
            )
        )
        ==
        PORTABLE_CONTRACT,
        "PORTABLE_CONTRACT_MISMATCH",
    )

    _require(
        int(
            portable_manifest.get(
                "row_count",
                -1,
            )
        )
        ==
        EXPECTED_TOTAL_ROWS,
        "PORTABLE_ROW_COUNT_MISMATCH",
    )

    portable_features = (
        _feature_columns(
            portable_manifest,
            expected_count=(
                EXPECTED_PORTABLE_FEATURE_COUNT
            ),
            field_prefix=(
                "portable"
            ),
        )
    )

    expected_portable_features = [
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
        expected_portable_features,
        "PORTABLE_FEATURE_LIST_NOT_EXACT_PARENT_PROJECTION",
    )

    for feature in (
        DROPPED_FEATURES
    ):

        _require(
            feature
            not in
            portable_features,
            (
                "DROPPED_FEATURE_STILL_PRESENT:"
                f"{feature}"
            ),
        )

    _require(
        RETAINED_RELATIVE_VOLUME_FEATURE
        in
        portable_features,
        "RETAINED_RELATIVE_VOLUME_FEATURE_MISSING",
    )

    source_lineage = (
        _mapping(
            portable_manifest,
            "source_training_matrix",
        )
    )

    _require(
        str(
            source_lineage.get(
                "dataset_id",
                "",
            )
        )
        ==
        EXPECTED_SOURCE_DATASET_ID,
        "PORTABLE_SOURCE_DATASET_ID_MISMATCH",
    )

    _require(
        str(
            source_lineage.get(
                "dataset_sha256",
                "",
            )
        )
        ==
        EXPECTED_SOURCE_DATASET_SHA256,
        "PORTABLE_SOURCE_DATASET_SHA256_MISMATCH",
    )

    _require(
        str(
            source_lineage.get(
                "manifest_sha256",
                "",
            )
        )
        ==
        EXPECTED_SOURCE_MANIFEST_SHA256,
        "PORTABLE_SOURCE_MANIFEST_SHA256_MISMATCH",
    )

    _require(
        str(
            source_lineage.get(
                "training_contract_version",
                "",
            )
        )
        ==
        SOURCE_CONTRACT,
        "PORTABLE_SOURCE_CONTRACT_MISMATCH",
    )

    portable_contract = (
        _mapping(
            portable_manifest,
            "portable_feature_contract",
        )
    )

    _require(
        str(
            portable_contract.get(
                "version",
                "",
            )
        )
        ==
        PORTABLE_CONTRACT,
        "PORTABLE_FEATURE_CONTRACT_VERSION_MISMATCH",
    )

    _require(
        int(
            portable_contract.get(
                "parent_feature_count",
                -1,
            )
        )
        ==
        EXPECTED_SOURCE_FEATURE_COUNT,
        "PORTABLE_PARENT_FEATURE_COUNT_MISMATCH",
    )

    _require(
        int(
            portable_contract.get(
                "portable_feature_count",
                -1,
            )
        )
        ==
        EXPECTED_PORTABLE_FEATURE_COUNT,
        "PORTABLE_OUTPUT_FEATURE_COUNT_MISMATCH",
    )

    dropped = (
        _string_list(
            portable_contract.get(
                "dropped_features"
            ),
            field_name=(
                "portable_feature_contract.dropped_features"
            ),
        )
    )

    _require(
        dropped
        ==
        list(
            DROPPED_FEATURES
        ),
        (
            "PORTABLE_DROP_POLICY_MISMATCH:"
            f"{dropped}"
        ),
    )

    added = (
        portable_contract.get(
            "added_features"
        )
    )

    if not isinstance(
        added,
        list,
    ):
        raise RuntimeError(
            "PORTABLE_ADDED_FEATURES_NOT_LIST"
        )

    _require(
        len(
            added
        )
        ==
        0,
        "PORTABLE_ADDED_FEATURES_NOT_EMPTY",
    )

    _require(
        str(
            portable_contract.get(
                "retained_existing_broker_sensitive_feature",
                "",
            )
        )
        ==
        RETAINED_RELATIVE_VOLUME_FEATURE,
        "PORTABLE_RETAINED_FEATURE_MISMATCH",
    )

    design_fingerprint = (
        _mapping(
            portable_contract,
            "contract_design_fingerprint",
        )
    )

    _require(
        str(
            design_fingerprint.get(
                "sha256",
                "",
            )
        )
        ==
        EXPECTED_CONTRACT_DESIGN_FINGERPRINT_SHA256,
        "PORTABLE_DESIGN_FINGERPRINT_MISMATCH",
    )

    _require(
        not bool(
            portable_manifest.get(
                "live_authorized",
                True,
            )
        ),
        "PORTABLE_ARTIFACT_UNEXPECTEDLY_LIVE_AUTHORIZED",
    )

    return (
        source_features,
        portable_features,
    )


def _validate_train_prefix(
    *,
    dataset_path: Path,
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

    train_prefix = (
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
            train_prefix.eq(
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

    split_rows = {
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

    _require(
        split_rows
        ==
        EXPECTED_SPLIT_ROWS,
        (
            "SPLIT_ROW_COUNTS_MISMATCH:"
            f"{artifact_name}:"
            f"{split_rows}"
        ),
    )

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
            split_rows
        ),
        "full_file_columns_loaded": [
            "dataset_split"
        ],
        "validation_feature_values_loaded": (
            False
        ),
        "test_feature_values_loaded": (
            False
        ),
        "target_columns_loaded": (
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
            "TRAIN_ROW_COUNT_MISMATCH:"
            f"{len(frame)}:"
            f"{EXPECTED_TRAIN_ROWS}"
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
        "TRAIN_DUPLICATE_DECISION_TIME",
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

    original_missing = (
        series.isna()
    )

    numeric_missing = (
        numeric.isna()
    )

    introduced_missing = int(
        (
            numeric_missing
            &
            ~original_missing
        )
        .sum()
    )

    _require(
        introduced_missing
        ==
        0,
        (
            "NON_NUMERIC_FEATURE_VALUES:"
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


def _compare_feature(
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
            "TRAIN_FEATURE_SHAPE_MISMATCH:"
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

    special_layout_equal = bool(
        np.array_equal(
            source_nan,
            portable_nan,
        )
        and
        np.array_equal(
            source_pos_inf,
            portable_pos_inf,
        )
        and
        np.array_equal(
            source_neg_inf,
            portable_neg_inf,
        )
    )

    source_nonfinite_count = int(
        (
            ~np.isfinite(
                source
            )
        )
        .sum()
    )

    portable_nonfinite_count = int(
        (
            ~np.isfinite(
                portable
            )
        )
        .sum()
    )

    finite_pair_mask = (
        np.isfinite(
            source
        )
        &
        np.isfinite(
            portable
        )
    )

    source_finite = (
        source[
            finite_pair_mask
        ]
    )

    portable_finite = (
        portable[
            finite_pair_mask
        ]
    )

    exact_equal_mask = (
        source_finite
        ==
        portable_finite
    )

    non_bit_exact_count = int(
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
        source_finite.size
        >
        0
    ):

        absolute_difference = np.abs(
            source_finite
            -
            portable_finite
        )

        scaled_units = (
            _scaled_epsilon_units(
                source_finite,
                portable_finite,
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
        "source_nonfinite_value_count": (
            source_nonfinite_count
        ),
        "portable_nonfinite_value_count": (
            portable_nonfinite_count
        ),
        "special_value_layout_equal": (
            special_layout_equal
        ),
        "bit_exact_finite_value_count": int(
            exact_equal_mask.sum()
        ),
        "non_bit_exact_finite_value_count": (
            non_bit_exact_count
        ),
        "all_finite_values_bit_exact": bool(
            non_bit_exact_count
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
        "within_float64_serialization_envelope": (
            within_serialization_envelope
        ),
    }


def _feature_columns_sha256(
    feature_columns: Sequence[str],
) -> str:

    payload = json.dumps(
        [
            str(
                feature
            )
            for feature
            in feature_columns
        ],
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=True,
        allow_nan=False,
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        payload
    ).hexdigest()


def _portable_train_input_fingerprint(
    *,
    train_frame: pd.DataFrame,
    feature_columns: Sequence[str],
) -> str:

    digest = hashlib.sha256()

    digest.update(
        b"XAUUSD_PORTABLE_331_TRAIN_INPUT_FINGERPRINT_V1\0"
    )

    digest.update(
        json.dumps(
            [
                str(
                    feature
                )
                for feature
                in feature_columns
            ],
            separators=(
                ",",
                ":",
            ),
            ensure_ascii=True,
            allow_nan=False,
        ).encode(
            "utf-8"
        )
    )

    digest.update(
        b"\0"
    )

    for decision_time in (
        train_frame[
            "decision_time"
        ]
        .astype(
            str
        )
        .tolist()
    ):

        digest.update(
            decision_time.encode(
                "utf-8"
            )
        )

        digest.update(
            b"\n"
        )

    for feature in (
        feature_columns
    ):

        feature_name = str(
            feature
        )

        values = (
            _numeric_array(
                train_frame[
                    feature_name
                ],
                feature=(
                    feature_name
                ),
            )
        )

        values_little_endian = np.asarray(
            values,
            dtype="<f8",
        )

        digest.update(
            feature_name.encode(
                "utf-8"
            )
        )

        digest.update(
            b"\0"
        )

        digest.update(
            values_little_endian.tobytes(
                order="C"
            )
        )

    return digest.hexdigest()


def _validate_train_inputs(
    *,
    source_train: pd.DataFrame,
    portable_train: pd.DataFrame,
    portable_feature_columns: Sequence[str],
) -> dict[str, Any]:

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

    non_bit_exact_features: list[str] = []

    outside_envelope_features: list[str] = []

    total_non_bit_exact_values = 0

    source_nonfinite_value_count = 0

    portable_nonfinite_value_count = 0

    constant_feature_count = 0

    global_max_abs_difference = (
        0.0
    )

    global_max_scaled_epsilon_units = (
        0.0
    )

    changed_feature_comparisons: list[
        dict[str, Any]
    ] = []

    for feature in (
        portable_feature_columns
    ):

        feature_name = str(
            feature
        )

        comparison = (
            _compare_feature(
                feature=(
                    feature_name
                ),
                source_series=(
                    source_train[
                        feature_name
                    ]
                ),
                portable_series=(
                    portable_train[
                        feature_name
                    ]
                ),
            )
        )

        source_nonfinite_value_count += int(
            comparison[
                "source_nonfinite_value_count"
            ]
        )

        portable_nonfinite_value_count += int(
            comparison[
                "portable_nonfinite_value_count"
            ]
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
                feature_name
            )

            changed_feature_comparisons.append(
                comparison
            )

        if not bool(
            comparison[
                "within_float64_serialization_envelope"
            ]
        ):

            outside_envelope_features.append(
                feature_name
            )

        global_max_abs_difference = max(
            global_max_abs_difference,
            float(
                comparison[
                    "maximum_absolute_difference"
                ]
            ),
        )

        global_max_scaled_epsilon_units = max(
            global_max_scaled_epsilon_units,
            float(
                comparison[
                    "maximum_scaled_epsilon_units"
                ]
            ),
        )

        portable_values = (
            _numeric_array(
                portable_train[
                    feature_name
                ],
                feature=(
                    feature_name
                ),
            )
        )

        finite_values = (
            portable_values[
                np.isfinite(
                    portable_values
                )
            ]
        )

        if (
            finite_values.size
            >
            0
        ):

            minimum = float(
                np.min(
                    finite_values
                )
            )

            maximum = float(
                np.max(
                    finite_values
                )
            )

            if math.isclose(
                minimum,
                maximum,
                rel_tol=0.0,
                abs_tol=0.0,
            ):

                constant_feature_count += (
                    1
                )

    _require(
        not outside_envelope_features,
        (
            "TRAIN_FEATURE_SERIALIZATION_ENVELOPE_FAILED:"
            f"{outside_envelope_features[:10]}"
        ),
    )

    _require(
        source_nonfinite_value_count
        ==
        0,
        (
            "SOURCE_TRAIN_NONFINITE_INPUT_VALUES:"
            f"{source_nonfinite_value_count}"
        ),
    )

    _require(
        portable_nonfinite_value_count
        ==
        0,
        (
            "PORTABLE_TRAIN_NONFINITE_INPUT_VALUES:"
            f"{portable_nonfinite_value_count}"
        ),
    )

    portable_input_fingerprint = (
        _portable_train_input_fingerprint(
            train_frame=(
                portable_train
            ),
            feature_columns=(
                portable_feature_columns
            ),
        )
    )

    return {
        "train_rows": (
            EXPECTED_TRAIN_ROWS
        ),
        "feature_count": (
            EXPECTED_PORTABLE_FEATURE_COUNT
        ),
        "serialization_equivalence_confirmed": (
            True
        ),
        "non_bit_exact_feature_count": int(
            len(
                non_bit_exact_features
            )
        ),
        "non_bit_exact_features": (
            non_bit_exact_features
        ),
        "total_non_bit_exact_finite_values": (
            total_non_bit_exact_values
        ),
        "outside_serialization_envelope_feature_count": (
            0
        ),
        "outside_serialization_envelope_features": [],
        "global_maximum_absolute_difference": (
            global_max_abs_difference
        ),
        "global_maximum_scaled_epsilon_units": (
            global_max_scaled_epsilon_units
        ),
        "source_nonfinite_feature_value_count": (
            source_nonfinite_value_count
        ),
        "portable_nonfinite_feature_value_count": (
            portable_nonfinite_value_count
        ),
        "constant_feature_count": (
            constant_feature_count
        ),
        "decision_time_sequence_preserved": (
            True
        ),
        "changed_feature_comparisons": (
            changed_feature_comparisons
        ),
        "portable_train_input_fingerprint_sha256": (
            portable_input_fingerprint
        ),
        "target_columns_loaded": (
            False
        ),
        "validation_feature_values_loaded": (
            False
        ),
        "test_feature_values_loaded": (
            False
        ),
    }


def run_audit(
) -> dict[str, Any]:

    (
        source_dataset_path,
        source_manifest_path,
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
        portable_manifest_path,
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

    _require(
        (
            PortableTrainingFeatureProjector
            ._sha256_file(
                source_dataset_path
            )
        )
        ==
        EXPECTED_SOURCE_DATASET_SHA256,
        "SOURCE_DATASET_HASH_CHANGED",
    )

    _require(
        (
            PortableTrainingFeatureProjector
            ._sha256_file(
                source_manifest_path
            )
        )
        ==
        EXPECTED_SOURCE_MANIFEST_SHA256,
        "SOURCE_MANIFEST_HASH_CHANGED",
    )

    _require(
        (
            PortableTrainingFeatureProjector
            ._sha256_file(
                portable_dataset_path
            )
        )
        ==
        EXPECTED_PORTABLE_DATASET_SHA256,
        "PORTABLE_DATASET_HASH_CHANGED",
    )

    _require(
        (
            PortableTrainingFeatureProjector
            ._sha256_file(
                portable_manifest_path
            )
        )
        ==
        EXPECTED_PORTABLE_MANIFEST_SHA256,
        "PORTABLE_MANIFEST_HASH_CHANGED",
    )

    (
        _source_feature_columns,
        portable_feature_columns,
    ) = (
        _validate_manifests(
            source_manifest=(
                source_manifest
            ),
            portable_manifest=(
                portable_manifest
            ),
        )
    )

    source_split_validation = (
        _validate_train_prefix(
            dataset_path=(
                source_dataset_path
            ),
            artifact_name=(
                "FROZEN_V3"
            ),
        )
    )

    portable_split_validation = (
        _validate_train_prefix(
            dataset_path=(
                portable_dataset_path
            ),
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
                portable_feature_columns
            ),
        )
    )

    portable_train = (
        _load_train_features_only(
            dataset_path=(
                portable_dataset_path
            ),
            feature_columns=(
                portable_feature_columns
            ),
        )
    )

    train_input_validation = (
        _validate_train_inputs(
            source_train=(
                source_train
            ),
            portable_train=(
                portable_train
            ),
            portable_feature_columns=(
                portable_feature_columns
            ),
        )
    )

    feature_columns_sha256 = (
        _feature_columns_sha256(
            portable_feature_columns
        )
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_PORTABLE_331_TRAIN_INPUT_READINESS_AUDIT"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "research_scope": (
            "STRICT_TRAIN_PREFIX_ONLY_MODEL_INPUT_READINESS_WITH_"
            "FLOAT64_SERIALIZATION_EQUIVALENCE"
        ),
        "decision": {
            "status": (
                "XAUUSD_PORTABLE_331_TRAIN_MODEL_INPUT_READINESS_CONFIRMED"
            ),
            "reason": (
                "ALL_331_PORTABLE_TRAIN_INPUTS_ARE_FINITE_AND_"
                "PRESERVED_FROM_THE_FROZEN_V3_PARENT_EITHER_"
                "BIT_EXACTLY_OR_WITHIN_THE_PREDECLARED_FLOAT64_"
                "CSV_SERIALIZATION_ENVELOPE"
            ),
            "source_contract": (
                SOURCE_CONTRACT
            ),
            "portable_contract": (
                PORTABLE_CONTRACT
            ),
            "portable_feature_count": (
                EXPECTED_PORTABLE_FEATURE_COUNT
            ),
            "train_rows": (
                EXPECTED_TRAIN_ROWS
            ),
            "dropped_features": list(
                DROPPED_FEATURES
            ),
            "added_features": [],
            "retained_relative_volume_feature": (
                RETAINED_RELATIVE_VOLUME_FEATURE
            ),
            "train_prefix_only_feature_loading_confirmed": (
                True
            ),
            "float64_serialization_equivalence_confirmed": (
                True
            ),
            "train_inputs_all_finite": (
                True
            ),
            "portable_artifact_identity_confirmed": (
                True
            ),
            "trainer_input_contract_design_authorized_next": (
                True
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
                "DESIGN_PORTABLE_331_RESEARCH_TRAINER_INPUT_"
                "CONTRACT_WITHOUT_MODEL_FIT"
            ),
        },
        "source_artifact": {
            "dataset_id": (
                EXPECTED_SOURCE_DATASET_ID
            ),
            "dataset_sha256": (
                EXPECTED_SOURCE_DATASET_SHA256
            ),
            "manifest_sha256": (
                EXPECTED_SOURCE_MANIFEST_SHA256
            ),
            "training_contract_version": (
                SOURCE_CONTRACT
            ),
            "feature_count": (
                EXPECTED_SOURCE_FEATURE_COUNT
            ),
            "filesystem_path_emitted": (
                False
            ),
        },
        "portable_artifact": {
            "dataset_id": (
                EXPECTED_PORTABLE_DATASET_ID
            ),
            "dataset_sha256": (
                EXPECTED_PORTABLE_DATASET_SHA256
            ),
            "manifest_sha256": (
                EXPECTED_PORTABLE_MANIFEST_SHA256
            ),
            "training_contract_version": (
                PORTABLE_CONTRACT
            ),
            "feature_count": (
                EXPECTED_PORTABLE_FEATURE_COUNT
            ),
            "feature_columns_sha256": (
                feature_columns_sha256
            ),
            "contract_design_fingerprint_sha256": (
                EXPECTED_CONTRACT_DESIGN_FINGERPRINT_SHA256
            ),
            "filesystem_path_emitted": (
                False
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
        "serialization_policy": {
            "float64_epsilon": (
                FLOAT64_EPSILON
            ),
            "maximum_absolute_difference": (
                SERIALIZATION_MAX_ABS_DIFFERENCE
            ),
            "maximum_scaled_epsilon_units": (
                SERIALIZATION_MAX_SCALED_EPSILON_UNITS
            ),
            "bit_exact_equality_required": (
                False
            ),
            "special_value_layout_must_match": (
                True
            ),
            "nonfinite_model_inputs_allowed": (
                False
            ),
        },
        "train_model_input_validation": (
            train_input_validation
        ),
        "scientific_policy": {
            "source_dataset_read": (
                True
            ),
            "portable_dataset_read": (
                True
            ),
            "full_dataset_columns_loaded": [
                "dataset_split"
            ],
            "source_train_feature_values_loaded": (
                True
            ),
            "portable_train_feature_values_loaded": (
                True
            ),
            "train_feature_rows_loaded": (
                EXPECTED_TRAIN_ROWS
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
            "validation_used_for_selection": (
                False
            ),
            "test_used_for_selection": (
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
            "target_contract_changed": (
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
            "if_readiness_confirmed": (
                "DESIGN_PORTABLE_331_RESEARCH_TRAINER_INPUT_"
                "CONTRACT_WITHOUT_MODEL_FIT"
            ),
            "portable_dataset_rebuild_required": (
                False
            ),
            "feature_contract_change_required": (
                False
            ),
            "target_contract_change_required": (
                False
            ),
            "model_training_authorized": (
                False
            ),
            "validation_feature_values_remain_unread": (
                True
            ),
            "test_feature_values_remain_unread": (
                True
            ),
            "test_holdout_remains_untouched": (
                True
            ),
            "live_authorization_not_changed": (
                True
            ),
        },
    }


def main() -> int:

    try:

        result = (
            run_audit()
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_PORTABLE_331_TRAIN_INPUT_"
                        "READINESS_AUDIT_FAILED"
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
                    "mt5_used": (
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