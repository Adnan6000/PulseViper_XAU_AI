from __future__ import annotations

import hashlib
import json
import math
import os

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from .portable_training_feature_projector import (
    PortableTrainingFeatureProjector,
)


class Portable331TrainingInputLoaderError(
    RuntimeError
):
    pass


@dataclass(
    frozen=True
)
class Portable331TrainFeatureBatch:
    dataset_id: str
    dataset_sha256: str
    manifest_sha256: str
    training_contract_version: str
    trainer_input_contract_version: str
    trainer_input_contract_fingerprint_sha256: str
    feature_columns: tuple[str, ...]
    feature_columns_sha256: str
    train_input_fingerprint_sha256: str
    row_count: int
    decision_time: np.ndarray
    X: np.ndarray


@dataclass(
    frozen=True
)
class Portable331TrainTargetBatch:
    dataset_id: str
    dataset_sha256: str
    manifest_sha256: str
    training_contract_version: str
    trainer_input_contract_version: str
    trainer_input_contract_fingerprint_sha256: str
    target_access_contract_version: str
    target_access_contract_fingerprint_sha256: str
    target_columns: tuple[str, ...]
    train_target_fingerprint_sha256: str
    row_count: int
    decision_time: np.ndarray
    target_class: np.ndarray
    target_tradeable: np.ndarray


@dataclass(
    frozen=True
)
class Portable331TrainSupervisedBatch:
    dataset_id: str
    dataset_sha256: str
    manifest_sha256: str
    training_contract_version: str

    trainer_input_contract_version: str
    trainer_input_contract_fingerprint_sha256: str

    target_access_contract_version: str
    target_access_contract_fingerprint_sha256: str

    supervised_batch_contract_version: str
    supervised_batch_contract_fingerprint_sha256: str

    feature_columns: tuple[str, ...]
    feature_columns_sha256: str
    train_input_fingerprint_sha256: str

    target_columns: tuple[str, ...]
    train_target_fingerprint_sha256: str

    row_count: int

    decision_time: np.ndarray
    X: np.ndarray
    target_class: np.ndarray
    target_tradeable: np.ndarray


class Portable331TrainingInputLoader:
    """
    Architecture-neutral loader for the frozen portable XAUUSD 331-feature
    research artifact.

    Current authorization boundary:

    - exact immutable portable artifact only
    - manifest-first validation
    - full-file structural access limited to dataset_split
    - TRAIN feature values only
    - TRAIN target_class and target_tradeable values only
    - TRAIN supervised alignment-only batch authorized
    - no additional dataset read inside supervised combination
    - no VALIDATION feature/target values
    - no TEST feature/target values
    - no scaler fit
    - no model fit
    - no metrics
    - no model artifacts
    """

    VERSION = (
        "1.2"
    )

    TRAINER_INPUT_CONTRACT_VERSION = (
        "XAUUSD_PORTABLE_331_RESEARCH_TRAINER_INPUT_V1"
    )

    TRAINER_INPUT_CONTRACT_FINGERPRINT_SHA256 = (
        "b192ce16291fe9ddca9ead9561224fb942c331d1f30fc1b53cee396efa5accdf"
    )

    TARGET_ACCESS_CONTRACT_VERSION = (
        "XAUUSD_PORTABLE_331_TRAIN_TARGET_ACCESS_V1"
    )

    TARGET_ACCESS_CONTRACT_FINGERPRINT_SHA256 = (
        "a640b9cda2522b734515a2cdf05259abbf77e4c6488afd635aedc21f62458266"
    )

    SUPERVISED_BATCH_CONTRACT_VERSION = (
        "XAUUSD_PORTABLE_331_TRAIN_SUPERVISED_BATCH_V1"
    )

    SUPERVISED_BATCH_CONTRACT_FINGERPRINT_SHA256 = (
        "1e7bd0751234282d4081ef87783de8633aac815a2f6aa13010fbb5a06156aec4"
    )

    PORTABLE_FEATURE_CONTRACT = (
        "XAUUSD_MTF_PORTABLE_FEATURE_V1"
    )

    SOURCE_FEATURE_CONTRACT = (
        "XAUUSD_MTF_TRAINING_V3"
    )

    EXPECTED_DATASET_ID = (
        "portable_cff75b0686383a3ab6f8352b"
    )

    EXPECTED_DATASET_SHA256 = (
        "cff75b0686383a3ab6f8352bfcdcd55308b99b7a4c6edbf7d2e7215f6f33dd07"
    )

    EXPECTED_MANIFEST_SHA256 = (
        "1b8e3599b227c9cbbc6b12f8ab0e275ca4deb4a65839fb626ca90720d59512dc"
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

    EXPECTED_FEATURE_COUNT = (
        331
    )

    EXPECTED_TOTAL_ROWS = (
        99945
    )

    EXPECTED_TRAIN_ROWS = (
        69966
    )

    EXPECTED_VALIDATION_ROWS = (
        14983
    )

    EXPECTED_TEST_ROWS = (
        14996
    )

    EXPECTED_SPLIT_ROWS = {
        "TRAIN": (
            EXPECTED_TRAIN_ROWS
        ),
        "VALIDATION": (
            EXPECTED_VALIDATION_ROWS
        ),
        "TEST": (
            EXPECTED_TEST_ROWS
        ),
    }

    EXPECTED_FEATURE_COLUMNS_SHA256 = (
        "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
    )

    EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256 = (
        "9ffb72759499cfc202e88cfdbd61b42cee5b5c7cbb7db5870470453caa5ed2c5"
    )

    EXPECTED_TRAIN_TARGET_FINGERPRINT_SHA256 = (
        "bc063a790e70cdbc931b2170ccfef883634b40ee7336a529a32bda0eaf0babe3"
    )

    EXPECTED_FEATURE_CONTRACT_DESIGN_FINGERPRINT_SHA256 = (
        "de389b1daa02b2d864490aa41776494baea4f9e42dbf2146c2c44b9c2660ff40"
    )

    EXPECTED_TARGET_LABEL_CONTRACT = (
        "CLEAN_DIRECTIONAL_EXCURSION_V2"
    )

    EXPECTED_TARGET_PROFIT_ATR = (
        1.25
    )

    EXPECTED_TARGET_MAX_ADVERSE_ATR = (
        0.75
    )

    EXPECTED_TARGET_CLASS_MAPPING = {
        "SHORT": -1,
        "NO_TRADE": 0,
        "LONG": 1,
    }

    TARGET_CLASS_ALLOWED_VALUES = {
        -1,
        0,
        1,
    }

    TARGET_TRADEABLE_ALLOWED_VALUES = {
        0,
        1,
    }

    REQUIRED_MODEL_TARGET_COLUMNS = (
        "target_class",
        "target_tradeable",
    )

    TRAIN_TARGET_COLUMNS = (
        "target_class",
        "target_tradeable",
    )

    DROPPED_PARENT_FEATURES = (
        "m5_spread_points",
        "m5_tick_volume_log1p",
    )

    RETAINED_RELATIVE_VOLUME_FEATURE = (
        "m5_tick_volume_ratio20"
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

    def __init__(
        self,
        canonical_root: str | Path,
    ) -> None:

        self.canonical_root = Path(
            canonical_root
        )

    @staticmethod
    def _mapping(
        document: Mapping[
            str,
            Any,
        ],
        key: str,
    ) -> Mapping[
        str,
        Any,
    ]:

        value = document.get(
            key
        )

        if not isinstance(
            value,
            Mapping,
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "EXPECTED_MAPPING_MISSING:"
                        f"{key}"
                    )
                )
            )

        return value

    @staticmethod
    def _string_list(
        value: Any,
        *,
        field_name: str,
    ) -> list[str]:

        if not isinstance(
            value,
            list,
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "EXPECTED_LIST_MISSING:"
                        f"{field_name}"
                    )
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
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "EMPTY_LIST_VALUE:"
                        f"{field_name}"
                    )
                )
            )

        return result

    @staticmethod
    def _required_int(
        mapping: Mapping[
            str,
            Any,
        ],
        key: str,
    ) -> int:

        if key not in mapping:
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "REQUIRED_INTEGER_MISSING:"
                        f"{key}"
                    )
                )
            )

        value = mapping[
            key
        ]

        if value is None:
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "REQUIRED_INTEGER_NONE:"
                        f"{key}"
                    )
                )
            )

        if isinstance(
            value,
            bool,
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "REQUIRED_INTEGER_BOOLEAN:"
                        f"{key}"
                    )
                )
            )

        try:

            result = int(
                value
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "REQUIRED_INTEGER_INVALID:"
                        f"{key}:"
                        f"{value}"
                    )
                )
            ) from exc

        return result

    @staticmethod
    def _feature_columns_sha256(
        feature_columns: Sequence[
            str
        ],
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

    @staticmethod
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

        if (
            introduced_missing
            !=
            0
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "NON_NUMERIC_TRAIN_FEATURE_VALUES:"
                        f"{feature}:"
                        f"{introduced_missing}"
                    )
                )
            )

        return np.asarray(
            numeric,
            dtype=np.float64,
        )

    @classmethod
    def _normalize_target_class_array(
        cls,
        series: pd.Series,
    ) -> np.ndarray:

        values: list[
            int
        ] = []

        raw_values = (
            series.tolist()
        )

        for (
            row_index,
            raw_value,
        ) in enumerate(
            raw_values
        ):

            if raw_value is None:
                raise (
                    Portable331TrainingInputLoaderError(
                        (
                            "TRAIN_TARGET_CLASS_MISSING:"
                            f"{row_index}"
                        )
                    )
                )

            normalized: int

            if isinstance(
                raw_value,
                str,
            ):

                token = (
                    raw_value
                    .strip()
                    .upper()
                )

                if not token:
                    raise (
                        Portable331TrainingInputLoaderError(
                            (
                                "TRAIN_TARGET_CLASS_EMPTY:"
                                f"{row_index}"
                            )
                        )
                    )

                if (
                    token
                    in
                    cls.EXPECTED_TARGET_CLASS_MAPPING
                ):

                    normalized = (
                        cls.EXPECTED_TARGET_CLASS_MAPPING[
                            token
                        ]
                    )

                else:

                    try:

                        numeric = float(
                            token
                        )

                    except ValueError as exc:

                        raise (
                            Portable331TrainingInputLoaderError(
                                (
                                    "TRAIN_TARGET_CLASS_INVALID:"
                                    f"{row_index}:"
                                    f"{raw_value}"
                                )
                            )
                        ) from exc

                    if (
                        not math.isfinite(
                            numeric
                        )
                        or
                        not numeric.is_integer()
                    ):
                        raise (
                            Portable331TrainingInputLoaderError(
                                (
                                    "TRAIN_TARGET_CLASS_INVALID:"
                                    f"{row_index}:"
                                    f"{raw_value}"
                                )
                            )
                        )

                    normalized = int(
                        numeric
                    )

            elif isinstance(
                raw_value,
                (
                    bool,
                    np.bool_,
                ),
            ):

                raise (
                    Portable331TrainingInputLoaderError(
                        (
                            "TRAIN_TARGET_CLASS_BOOLEAN:"
                            f"{row_index}"
                        )
                    )
                )

            elif isinstance(
                raw_value,
                (
                    int,
                    np.integer,
                ),
            ):

                normalized = int(
                    raw_value
                )

            elif isinstance(
                raw_value,
                (
                    float,
                    np.floating,
                ),
            ):

                numeric = float(
                    raw_value
                )

                if not math.isfinite(
                    numeric
                ):
                    raise (
                        Portable331TrainingInputLoaderError(
                            (
                                "TRAIN_TARGET_CLASS_NONFINITE:"
                                f"{row_index}"
                            )
                        )
                    )

                if not numeric.is_integer():
                    raise (
                        Portable331TrainingInputLoaderError(
                            (
                                "TRAIN_TARGET_CLASS_NONINTEGER:"
                                f"{row_index}:"
                                f"{numeric}"
                            )
                        )
                    )

                normalized = int(
                    numeric
                )

            else:

                raise (
                    Portable331TrainingInputLoaderError(
                        (
                            "TRAIN_TARGET_CLASS_TYPE_INVALID:"
                            f"{row_index}:"
                            f"{type(raw_value).__name__}"
                        )
                    )
                )

            if (
                normalized
                not in
                cls.TARGET_CLASS_ALLOWED_VALUES
            ):
                raise (
                    Portable331TrainingInputLoaderError(
                        (
                            "TRAIN_TARGET_CLASS_DOMAIN_INVALID:"
                            f"{row_index}:"
                            f"{normalized}"
                        )
                    )
                )

            values.append(
                normalized
            )

        return np.asarray(
            values,
            dtype=np.int8,
        )

    @classmethod
    def _normalize_target_tradeable_array(
        cls,
        series: pd.Series,
    ) -> np.ndarray:

        values: list[
            int
        ] = []

        raw_values = (
            series.tolist()
        )

        for (
            row_index,
            raw_value,
        ) in enumerate(
            raw_values
        ):

            if raw_value is None:
                raise (
                    Portable331TrainingInputLoaderError(
                        (
                            "TRAIN_TARGET_TRADEABLE_MISSING:"
                            f"{row_index}"
                        )
                    )
                )

            normalized: int

            if isinstance(
                raw_value,
                str,
            ):

                token = (
                    raw_value
                    .strip()
                )

                if not token:
                    raise (
                        Portable331TrainingInputLoaderError(
                            (
                                "TRAIN_TARGET_TRADEABLE_EMPTY:"
                                f"{row_index}"
                            )
                        )
                    )

                try:

                    numeric = float(
                        token
                    )

                except ValueError as exc:

                    raise (
                        Portable331TrainingInputLoaderError(
                            (
                                "TRAIN_TARGET_TRADEABLE_INVALID:"
                                f"{row_index}:"
                                f"{raw_value}"
                            )
                        )
                    ) from exc

                if (
                    not math.isfinite(
                        numeric
                    )
                    or
                    not numeric.is_integer()
                ):
                    raise (
                        Portable331TrainingInputLoaderError(
                            (
                                "TRAIN_TARGET_TRADEABLE_INVALID:"
                                f"{row_index}:"
                                f"{raw_value}"
                            )
                        )
                    )

                normalized = int(
                    numeric
                )

            elif isinstance(
                raw_value,
                (
                    bool,
                    np.bool_,
                ),
            ):

                normalized = int(
                    bool(
                        raw_value
                    )
                )

            elif isinstance(
                raw_value,
                (
                    int,
                    np.integer,
                ),
            ):

                normalized = int(
                    raw_value
                )

            elif isinstance(
                raw_value,
                (
                    float,
                    np.floating,
                ),
            ):

                numeric = float(
                    raw_value
                )

                if not math.isfinite(
                    numeric
                ):
                    raise (
                        Portable331TrainingInputLoaderError(
                            (
                                "TRAIN_TARGET_TRADEABLE_NONFINITE:"
                                f"{row_index}"
                            )
                        )
                    )

                if not numeric.is_integer():
                    raise (
                        Portable331TrainingInputLoaderError(
                            (
                                "TRAIN_TARGET_TRADEABLE_NONINTEGER:"
                                f"{row_index}:"
                                f"{numeric}"
                            )
                        )
                    )

                normalized = int(
                    numeric
                )

            else:

                raise (
                    Portable331TrainingInputLoaderError(
                        (
                            "TRAIN_TARGET_TRADEABLE_TYPE_INVALID:"
                            f"{row_index}:"
                            f"{type(raw_value).__name__}"
                        )
                    )
                )

            if (
                normalized
                not in
                cls.TARGET_TRADEABLE_ALLOWED_VALUES
            ):
                raise (
                    Portable331TrainingInputLoaderError(
                        (
                            "TRAIN_TARGET_TRADEABLE_DOMAIN_INVALID:"
                            f"{row_index}:"
                            f"{normalized}"
                        )
                    )
                )

            values.append(
                normalized
            )

        return np.asarray(
            values,
            dtype=np.int8,
        )

    @classmethod
    def _train_input_fingerprint(
        cls,
        *,
        train_frame: pd.DataFrame,
        feature_columns: Sequence[
            str
        ],
    ) -> str:

        if (
            "decision_time"
            not in
            train_frame.columns
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "TRAIN_DECISION_TIME_COLUMN_MISSING"
                )
            )

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

        decision_times = (
            train_frame[
                "decision_time"
            ]
            .astype(
                str
            )
            .tolist()
        )

        for decision_time in (
            decision_times
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

            if (
                feature_name
                not in
                train_frame.columns
            ):
                raise (
                    Portable331TrainingInputLoaderError(
                        (
                            "TRAIN_FEATURE_COLUMN_MISSING:"
                            f"{feature_name}"
                        )
                    )
                )

            values = (
                cls._numeric_array(
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

    @classmethod
    def _train_target_fingerprint(
        cls,
        *,
        decision_time: np.ndarray,
        target_class: np.ndarray,
        target_tradeable: np.ndarray,
    ) -> str:

        if (
            decision_time.shape
            !=
            target_class.shape
            or
            decision_time.shape
            !=
            target_tradeable.shape
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "TRAIN_TARGET_FINGERPRINT_SHAPE_MISMATCH"
                )
            )

        digest = hashlib.sha256()

        digest.update(
            b"XAUUSD_PORTABLE_331_TRAIN_TARGET_FINGERPRINT_V1\0"
        )

        normalized_decision_time = (
            decision_time
            .astype(
                str
            )
            .tolist()
        )

        for value in (
            normalized_decision_time
        ):

            digest.update(
                str(
                    value
                ).encode(
                    "utf-8"
                )
            )

            digest.update(
                b"\n"
            )

        digest.update(
            b"target_class\0"
        )

        digest.update(
            np.asarray(
                target_class,
                dtype=np.int8,
            ).tobytes(
                order="C"
            )
        )

        digest.update(
            b"target_tradeable\0"
        )

        digest.update(
            np.asarray(
                target_tradeable,
                dtype=np.int8,
            ).tobytes(
                order="C"
            )
        )

        return digest.hexdigest()

    @classmethod
    def _validate_train_target_frame(
        cls,
        frame: pd.DataFrame,
    ) -> tuple[
        np.ndarray,
        np.ndarray,
        np.ndarray,
        str,
    ]:

        required_columns = [
            "decision_time",
            *cls.TRAIN_TARGET_COLUMNS,
        ]

        missing_columns = [
            column
            for column
            in required_columns
            if (
                column
                not in
                frame.columns
            )
        ]

        if missing_columns:
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "TRAIN_TARGET_COLUMNS_MISSING:"
                        f"{missing_columns}"
                    )
                )
            )

        if (
            len(
                frame
            )
            !=
            cls.EXPECTED_TRAIN_ROWS
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "TRAIN_TARGET_ROW_COUNT_MISMATCH:"
                        f"{len(frame)}:"
                        f"{cls.EXPECTED_TRAIN_ROWS}"
                    )
                )
            )

        if bool(
            frame[
                "decision_time"
            ]
            .duplicated()
            .any()
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "TRAIN_TARGET_DUPLICATE_DECISION_TIME"
                )
            )

        target_class = (
            cls._normalize_target_class_array(
                frame[
                    "target_class"
                ]
            )
        )

        target_tradeable = (
            cls._normalize_target_tradeable_array(
                frame[
                    "target_tradeable"
                ]
            )
        )

        expected_tradeable = (
            (
                target_class
                !=
                0
            )
            .astype(
                np.int8,
                copy=False,
            )
        )

        linkage_mismatch_count = int(
            np.count_nonzero(
                target_tradeable
                !=
                expected_tradeable
            )
        )

        if (
            linkage_mismatch_count
            !=
            0
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "TRAIN_TARGET_TRADEABLE_LINKAGE_MISMATCH:"
                        f"{linkage_mismatch_count}"
                    )
                )
            )

        decision_time = (
            frame[
                "decision_time"
            ]
            .astype(
                str
            )
            .to_numpy(
                copy=True
            )
        )

        target_fingerprint = (
            cls._train_target_fingerprint(
                decision_time=(
                    decision_time
                ),
                target_class=(
                    target_class
                ),
                target_tradeable=(
                    target_tradeable
                ),
            )
        )

        return (
            decision_time,
            target_class,
            target_tradeable,
            target_fingerprint,
        )

    @classmethod
    def _numeric_matrix(
        cls,
        *,
        frame: pd.DataFrame,
        feature_columns: Sequence[
            str
        ],
    ) -> np.ndarray:

        columns: list[
            np.ndarray
        ] = []

        for feature in (
            feature_columns
        ):

            feature_name = str(
                feature
            )

            if (
                feature_name
                not in
                frame.columns
            ):
                raise (
                    Portable331TrainingInputLoaderError(
                        (
                            "TRAIN_FEATURE_COLUMN_MISSING:"
                            f"{feature_name}"
                        )
                    )
                )

            values = (
                cls._numeric_array(
                    frame[
                        feature_name
                    ],
                    feature=(
                        feature_name
                    ),
                )
            )

            columns.append(
                values
            )

        if not columns:
            raise (
                Portable331TrainingInputLoaderError(
                    "NO_TRAIN_FEATURE_COLUMNS"
                )
            )

        matrix = np.column_stack(
            columns
        ).astype(
            np.float64,
            copy=False,
        )

        nonfinite_count = int(
            (
                ~np.isfinite(
                    matrix
                )
            )
            .sum()
        )

        if (
            nonfinite_count
            !=
            0
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "NONFINITE_TRAIN_MODEL_INPUT_VALUES:"
                        f"{nonfinite_count}"
                    )
                )
            )

        return matrix

    @classmethod
    def _validate_split_series(
        cls,
        split: pd.Series,
    ) -> dict[str, int]:

        normalized = (
            split.astype(
                str
            )
            .reset_index(
                drop=True
            )
        )

        if (
            len(
                normalized
            )
            !=
            cls.EXPECTED_TOTAL_ROWS
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "TOTAL_ROW_COUNT_MISMATCH:"
                        f"{len(normalized)}:"
                        f"{cls.EXPECTED_TOTAL_ROWS}"
                    )
                )
            )

        train_prefix = (
            normalized.iloc[
                :cls.EXPECTED_TRAIN_ROWS
            ]
        )

        validation_block = (
            normalized.iloc[
                cls.EXPECTED_TRAIN_ROWS:
                (
                    cls.EXPECTED_TRAIN_ROWS
                    +
                    cls.EXPECTED_VALIDATION_ROWS
                )
            ]
        )

        test_block = (
            normalized.iloc[
                (
                    cls.EXPECTED_TRAIN_ROWS
                    +
                    cls.EXPECTED_VALIDATION_ROWS
                ):
            ]
        )

        if not bool(
            train_prefix.eq(
                "TRAIN"
            ).all()
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "TRAIN_SPLIT_NOT_CONTIGUOUS_PREFIX"
                )
            )

        if not bool(
            validation_block.eq(
                "VALIDATION"
            ).all()
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "VALIDATION_SPLIT_BLOCK_INVALID"
                )
            )

        if not bool(
            test_block.eq(
                "TEST"
            ).all()
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "TEST_SPLIT_BLOCK_INVALID"
                )
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
                normalized
                .value_counts()
                .to_dict()
                .items()
            )
        }

        if (
            split_rows
            !=
            cls.EXPECTED_SPLIT_ROWS
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "SPLIT_ROW_COUNTS_MISMATCH:"
                        f"{split_rows}"
                    )
                )
            )

        return split_rows

    @classmethod
    def _combine_train_batches(
        cls,
        *,
        feature_batch: Portable331TrainFeatureBatch,
        target_batch: Portable331TrainTargetBatch,
    ) -> Portable331TrainSupervisedBatch:

        if (
            feature_batch.dataset_id
            !=
            cls.EXPECTED_DATASET_ID
            or
            target_batch.dataset_id
            !=
            cls.EXPECTED_DATASET_ID
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_DATASET_ID_MISMATCH"
                )
            )

        if (
            feature_batch.dataset_sha256
            !=
            cls.EXPECTED_DATASET_SHA256
            or
            target_batch.dataset_sha256
            !=
            cls.EXPECTED_DATASET_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_DATASET_SHA256_MISMATCH"
                )
            )

        if (
            feature_batch.manifest_sha256
            !=
            cls.EXPECTED_MANIFEST_SHA256
            or
            target_batch.manifest_sha256
            !=
            cls.EXPECTED_MANIFEST_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_MANIFEST_SHA256_MISMATCH"
                )
            )

        if (
            feature_batch.training_contract_version
            !=
            cls.PORTABLE_FEATURE_CONTRACT
            or
            target_batch.training_contract_version
            !=
            cls.PORTABLE_FEATURE_CONTRACT
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_FEATURE_CONTRACT_MISMATCH"
                )
            )

        if (
            feature_batch.trainer_input_contract_version
            !=
            cls.TRAINER_INPUT_CONTRACT_VERSION
            or
            target_batch.trainer_input_contract_version
            !=
            cls.TRAINER_INPUT_CONTRACT_VERSION
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_TRAINER_INPUT_CONTRACT_MISMATCH"
                )
            )

        if (
            feature_batch.trainer_input_contract_fingerprint_sha256
            !=
            cls.TRAINER_INPUT_CONTRACT_FINGERPRINT_SHA256
            or
            target_batch.trainer_input_contract_fingerprint_sha256
            !=
            cls.TRAINER_INPUT_CONTRACT_FINGERPRINT_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_TRAINER_INPUT_FINGERPRINT_MISMATCH"
                )
            )

        if (
            target_batch.target_access_contract_version
            !=
            cls.TARGET_ACCESS_CONTRACT_VERSION
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_TARGET_ACCESS_CONTRACT_MISMATCH"
                )
            )

        if (
            target_batch.target_access_contract_fingerprint_sha256
            !=
            cls.TARGET_ACCESS_CONTRACT_FINGERPRINT_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_TARGET_ACCESS_FINGERPRINT_MISMATCH"
                )
            )

        if (
            feature_batch.row_count
            !=
            cls.EXPECTED_TRAIN_ROWS
            or
            target_batch.row_count
            !=
            cls.EXPECTED_TRAIN_ROWS
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_ROW_COUNT_MISMATCH"
                )
            )

        if (
            feature_batch.row_count
            !=
            target_batch.row_count
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_COMPONENT_ROW_COUNT_MISMATCH"
                )
            )

        if (
            len(
                feature_batch.feature_columns
            )
            !=
            cls.EXPECTED_FEATURE_COUNT
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_FEATURE_COUNT_MISMATCH"
                )
            )

        if (
            feature_batch.feature_columns_sha256
            !=
            cls.EXPECTED_FEATURE_COLUMNS_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_FEATURE_COLUMNS_SHA256_MISMATCH"
                )
            )

        recomputed_feature_columns_sha256 = (
            cls._feature_columns_sha256(
                feature_batch.feature_columns
            )
        )

        if (
            recomputed_feature_columns_sha256
            !=
            cls.EXPECTED_FEATURE_COLUMNS_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_RECOMPUTED_FEATURE_COLUMNS_SHA256_MISMATCH"
                )
            )

        if (
            feature_batch.train_input_fingerprint_sha256
            !=
            cls.EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_TRAIN_INPUT_FINGERPRINT_MISMATCH"
                )
            )

        if (
            target_batch.target_columns
            !=
            cls.TRAIN_TARGET_COLUMNS
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_TARGET_COLUMNS_MISMATCH"
                )
            )

        if (
            target_batch.train_target_fingerprint_sha256
            !=
            cls.EXPECTED_TRAIN_TARGET_FINGERPRINT_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_TRAIN_TARGET_FINGERPRINT_MISMATCH"
                )
            )

        feature_decision_time = (
            feature_batch.decision_time
        )

        target_decision_time = (
            target_batch.decision_time
        )

        X = (
            feature_batch.X
        )

        target_class = (
            target_batch.target_class
        )

        target_tradeable = (
            target_batch.target_tradeable
        )

        if not isinstance(
            feature_decision_time,
            np.ndarray,
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_FEATURE_DECISION_TIME_NOT_ARRAY"
                )
            )

        if not isinstance(
            target_decision_time,
            np.ndarray,
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_TARGET_DECISION_TIME_NOT_ARRAY"
                )
            )

        if not isinstance(
            X,
            np.ndarray,
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_X_NOT_ARRAY"
                )
            )

        if not isinstance(
            target_class,
            np.ndarray,
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_TARGET_CLASS_NOT_ARRAY"
                )
            )

        if not isinstance(
            target_tradeable,
            np.ndarray,
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_TARGET_TRADEABLE_NOT_ARRAY"
                )
            )

        expected_vector_shape = (
            cls.EXPECTED_TRAIN_ROWS,
        )

        expected_matrix_shape = (
            cls.EXPECTED_TRAIN_ROWS,
            cls.EXPECTED_FEATURE_COUNT,
        )

        if (
            feature_decision_time.shape
            !=
            expected_vector_shape
            or
            target_decision_time.shape
            !=
            expected_vector_shape
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_DECISION_TIME_SHAPE_MISMATCH"
                )
            )

        if (
            X.shape
            !=
            expected_matrix_shape
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "SUPERVISED_X_SHAPE_MISMATCH:"
                        f"{X.shape}"
                    )
                )
            )

        if (
            target_class.shape
            !=
            expected_vector_shape
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "SUPERVISED_TARGET_CLASS_SHAPE_MISMATCH:"
                        f"{target_class.shape}"
                    )
                )
            )

        if (
            target_tradeable.shape
            !=
            expected_vector_shape
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "SUPERVISED_TARGET_TRADEABLE_SHAPE_MISMATCH:"
                        f"{target_tradeable.shape}"
                    )
                )
            )

        if (
            X.dtype
            !=
            np.dtype(
                np.float64
            )
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "SUPERVISED_X_DTYPE_MISMATCH:"
                        f"{X.dtype}"
                    )
                )
            )

        if (
            target_class.dtype
            !=
            np.dtype(
                np.int8
            )
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "SUPERVISED_TARGET_CLASS_DTYPE_MISMATCH:"
                        f"{target_class.dtype}"
                    )
                )
            )

        if (
            target_tradeable.dtype
            !=
            np.dtype(
                np.int8
            )
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "SUPERVISED_TARGET_TRADEABLE_DTYPE_MISMATCH:"
                        f"{target_tradeable.dtype}"
                    )
                )
            )

        if (
            bool(
                feature_decision_time.flags.writeable
            )
            or
            bool(
                target_decision_time.flags.writeable
            )
            or
            bool(
                X.flags.writeable
            )
            or
            bool(
                target_class.flags.writeable
            )
            or
            bool(
                target_tradeable.flags.writeable
            )
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_ARRAY_NOT_READ_ONLY"
                )
            )

        feature_decision_time_string = (
            feature_decision_time.astype(
                str
            )
        )

        target_decision_time_string = (
            target_decision_time.astype(
                str
            )
        )

        if not bool(
            np.array_equal(
                feature_decision_time_string,
                target_decision_time_string,
            )
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_DECISION_TIME_ALIGNMENT_MISMATCH"
                )
            )

        if (
            int(
                np.unique(
                    feature_decision_time_string
                ).size
            )
            !=
            cls.EXPECTED_TRAIN_ROWS
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_DECISION_TIME_NOT_UNIQUE"
                )
            )

        if not bool(
            np.isfinite(
                X
            ).all()
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_X_NONFINITE"
                )
            )

        if not bool(
            np.isin(
                target_class,
                np.asarray(
                    sorted(
                        cls.TARGET_CLASS_ALLOWED_VALUES
                    ),
                    dtype=np.int8,
                ),
            ).all()
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_TARGET_CLASS_DOMAIN_INVALID"
                )
            )

        if not bool(
            np.isin(
                target_tradeable,
                np.asarray(
                    sorted(
                        cls.TARGET_TRADEABLE_ALLOWED_VALUES
                    ),
                    dtype=np.int8,
                ),
            ).all()
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_TARGET_TRADEABLE_DOMAIN_INVALID"
                )
            )

        expected_tradeable = (
            (
                target_class
                !=
                0
            )
            .astype(
                np.int8,
                copy=False,
            )
        )

        linkage_mismatch_count = int(
            np.count_nonzero(
                target_tradeable
                !=
                expected_tradeable
            )
        )

        if (
            linkage_mismatch_count
            !=
            0
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "SUPERVISED_TARGET_TRADEABLE_LINKAGE_MISMATCH:"
                        f"{linkage_mismatch_count}"
                    )
                )
            )

        recomputed_target_fingerprint = (
            cls._train_target_fingerprint(
                decision_time=(
                    target_decision_time
                ),
                target_class=(
                    target_class
                ),
                target_tradeable=(
                    target_tradeable
                ),
            )
        )

        if (
            recomputed_target_fingerprint
            !=
            cls.EXPECTED_TRAIN_TARGET_FINGERPRINT_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SUPERVISED_RECOMPUTED_TARGET_FINGERPRINT_MISMATCH"
                )
            )

        return (
            Portable331TrainSupervisedBatch(
                dataset_id=(
                    cls.EXPECTED_DATASET_ID
                ),
                dataset_sha256=(
                    cls.EXPECTED_DATASET_SHA256
                ),
                manifest_sha256=(
                    cls.EXPECTED_MANIFEST_SHA256
                ),
                training_contract_version=(
                    cls.PORTABLE_FEATURE_CONTRACT
                ),
                trainer_input_contract_version=(
                    cls.TRAINER_INPUT_CONTRACT_VERSION
                ),
                trainer_input_contract_fingerprint_sha256=(
                    cls.TRAINER_INPUT_CONTRACT_FINGERPRINT_SHA256
                ),
                target_access_contract_version=(
                    cls.TARGET_ACCESS_CONTRACT_VERSION
                ),
                target_access_contract_fingerprint_sha256=(
                    cls.TARGET_ACCESS_CONTRACT_FINGERPRINT_SHA256
                ),
                supervised_batch_contract_version=(
                    cls.SUPERVISED_BATCH_CONTRACT_VERSION
                ),
                supervised_batch_contract_fingerprint_sha256=(
                    cls.SUPERVISED_BATCH_CONTRACT_FINGERPRINT_SHA256
                ),
                feature_columns=(
                    feature_batch.feature_columns
                ),
                feature_columns_sha256=(
                    feature_batch.feature_columns_sha256
                ),
                train_input_fingerprint_sha256=(
                    feature_batch.train_input_fingerprint_sha256
                ),
                target_columns=(
                    target_batch.target_columns
                ),
                train_target_fingerprint_sha256=(
                    target_batch.train_target_fingerprint_sha256
                ),
                row_count=(
                    cls.EXPECTED_TRAIN_ROWS
                ),
                decision_time=(
                    feature_decision_time
                ),
                X=(
                    X
                ),
                target_class=(
                    target_class
                ),
                target_tradeable=(
                    target_tradeable
                ),
            )
        )

    def _search_roots(
        self,
    ) -> list[Path]:

        roots: list[
            Path
        ] = []

        preferred = (
            self.canonical_root
            /
            "03_Data"
        )

        if preferred.is_dir():
            roots.append(
                preferred
            )

        roots.append(
            self.canonical_root
        )

        result: list[
            Path
        ] = []

        seen: set[
            Path
        ] = set()

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

    @classmethod
    def _manifest_files(
        cls,
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
                    cls.EXCLUDED_SCAN_DIRECTORIES
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

    def _discover_exact_artifact(
        self,
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

        seen_manifests: set[
            Path
        ] = set()

        for search_root in (
            self._search_roots()
        ):

            for manifest_path in (
                self._manifest_files(
                    search_root
                )
            ):

                resolved_manifest = (
                    manifest_path.resolve()
                )

                if (
                    resolved_manifest
                    in
                    seen_manifests
                ):
                    continue

                seen_manifests.add(
                    resolved_manifest
                )

                try:

                    manifest_sha256 = (
                        PortableTrainingFeatureProjector
                        ._sha256_file(
                            manifest_path
                        )
                    )

                except OSError:
                    continue

                if (
                    manifest_sha256
                    !=
                    self.EXPECTED_MANIFEST_SHA256
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
                    self.EXPECTED_DATASET_ID
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
                    self.EXPECTED_DATASET_SHA256
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
                    self.PORTABLE_FEATURE_CONTRACT
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

                    dataset_sha256 = (
                        PortableTrainingFeatureProjector
                        ._sha256_file(
                            dataset_path
                        )
                    )

                except OSError:
                    continue

                if (
                    dataset_sha256
                    !=
                    self.EXPECTED_DATASET_SHA256
                ):
                    continue

                candidates.append(
                    (
                        dataset_path,
                        manifest_path,
                        manifest,
                    )
                )

        if (
            len(
                candidates
            )
            !=
            1
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "PORTABLE_ARTIFACT_DISCOVERY_COUNT_INVALID:"
                        f"{len(candidates)}"
                    )
                )
            )

        return candidates[
            0
        ]

    @classmethod
    def _validate_manifest(
        cls,
        manifest: Mapping[
            str,
            Any,
        ],
    ) -> tuple[
        tuple[str, ...],
        tuple[str, ...],
    ]:

        if (
            str(
                manifest.get(
                    "manifest_version",
                    "",
                )
            )
            !=
            PortableTrainingFeatureProjector
            .MANIFEST_VERSION
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_MANIFEST_VERSION_MISMATCH"
                )
            )

        if (
            str(
                manifest.get(
                    "dataset_id",
                    "",
                )
            )
            !=
            cls.EXPECTED_DATASET_ID
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_DATASET_ID_MISMATCH"
                )
            )

        if (
            str(
                manifest.get(
                    "dataset_sha256",
                    "",
                )
            )
            !=
            cls.EXPECTED_DATASET_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_DATASET_SHA256_MISMATCH"
                )
            )

        if (
            str(
                manifest.get(
                    "training_contract_version",
                    "",
                )
            )
            !=
            cls.PORTABLE_FEATURE_CONTRACT
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_FEATURE_CONTRACT_MISMATCH"
                )
            )

        if (
            cls._required_int(
                manifest,
                "row_count",
            )
            !=
            cls.EXPECTED_TOTAL_ROWS
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_ROW_COUNT_MISMATCH"
                )
            )

        if (
            cls._required_int(
                manifest,
                "feature_count",
            )
            !=
            cls.EXPECTED_FEATURE_COUNT
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_FEATURE_COUNT_MISMATCH"
                )
            )

        if bool(
            manifest.get(
                "live_authorized",
                True,
            )
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_ARTIFACT_UNEXPECTEDLY_LIVE_AUTHORIZED"
                )
            )

        feature_columns = (
            cls._string_list(
                manifest.get(
                    "feature_columns"
                ),
                field_name=(
                    "feature_columns"
                ),
            )
        )

        if (
            len(
                feature_columns
            )
            !=
            cls.EXPECTED_FEATURE_COUNT
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_FEATURE_LIST_COUNT_MISMATCH"
                )
            )

        if (
            len(
                set(
                    feature_columns
                )
            )
            !=
            len(
                feature_columns
            )
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_FEATURE_COLUMNS_NOT_UNIQUE"
                )
            )

        if (
            cls._feature_columns_sha256(
                feature_columns
            )
            !=
            cls.EXPECTED_FEATURE_COLUMNS_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_FEATURE_COLUMNS_SHA256_MISMATCH"
                )
            )

        for feature in (
            cls.DROPPED_PARENT_FEATURES
        ):

            if (
                feature
                in
                feature_columns
            ):
                raise (
                    Portable331TrainingInputLoaderError(
                        (
                            "DROPPED_PARENT_FEATURE_PRESENT:"
                            f"{feature}"
                        )
                    )
                )

        if (
            cls.RETAINED_RELATIVE_VOLUME_FEATURE
            not in
            feature_columns
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "RETAINED_RELATIVE_VOLUME_FEATURE_MISSING"
                )
            )

        portable_contract = (
            cls._mapping(
                manifest,
                "portable_feature_contract",
            )
        )

        if (
            str(
                portable_contract.get(
                    "version",
                    "",
                )
            )
            !=
            cls.PORTABLE_FEATURE_CONTRACT
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_CONTRACT_VERSION_MISMATCH"
                )
            )

        dropped_features = (
            cls._string_list(
                portable_contract.get(
                    "dropped_features"
                ),
                field_name=(
                    "portable_feature_contract.dropped_features"
                ),
            )
        )

        if (
            dropped_features
            !=
            list(
                cls.DROPPED_PARENT_FEATURES
            )
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_DROP_POLICY_MISMATCH"
                )
            )

        added_features = (
            portable_contract.get(
                "added_features"
            )
        )

        if not isinstance(
            added_features,
            list,
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_ADDED_FEATURES_NOT_LIST"
                )
            )

        if added_features:
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_ADDED_FEATURES_NOT_EMPTY"
                )
            )

        if (
            str(
                portable_contract.get(
                    "retained_existing_broker_sensitive_feature",
                    "",
                )
            )
            !=
            cls.RETAINED_RELATIVE_VOLUME_FEATURE
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_RETAINED_FEATURE_MISMATCH"
                )
            )

        design_fingerprint = (
            cls._mapping(
                portable_contract,
                "contract_design_fingerprint",
            )
        )

        if (
            str(
                design_fingerprint.get(
                    "sha256",
                    "",
                )
            )
            !=
            cls.EXPECTED_FEATURE_CONTRACT_DESIGN_FINGERPRINT_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_DESIGN_FINGERPRINT_MISMATCH"
                )
            )

        source_lineage = (
            cls._mapping(
                manifest,
                "source_training_matrix",
            )
        )

        if (
            str(
                source_lineage.get(
                    "dataset_id",
                    "",
                )
            )
            !=
            cls.EXPECTED_SOURCE_DATASET_ID
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SOURCE_LINEAGE_DATASET_ID_MISMATCH"
                )
            )

        if (
            str(
                source_lineage.get(
                    "dataset_sha256",
                    "",
                )
            )
            !=
            cls.EXPECTED_SOURCE_DATASET_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SOURCE_LINEAGE_DATASET_SHA256_MISMATCH"
                )
            )

        if (
            str(
                source_lineage.get(
                    "manifest_sha256",
                    "",
                )
            )
            !=
            cls.EXPECTED_SOURCE_MANIFEST_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SOURCE_LINEAGE_MANIFEST_SHA256_MISMATCH"
                )
            )

        if (
            str(
                source_lineage.get(
                    "training_contract_version",
                    "",
                )
            )
            !=
            cls.SOURCE_FEATURE_CONTRACT
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "SOURCE_LINEAGE_CONTRACT_MISMATCH"
                )
            )

        target_columns = (
            cls._string_list(
                manifest.get(
                    "target_columns"
                ),
                field_name=(
                    "target_columns"
                ),
            )
        )

        for target_column in (
            cls.REQUIRED_MODEL_TARGET_COLUMNS
        ):

            if (
                target_column
                not in
                target_columns
            ):
                raise (
                    Portable331TrainingInputLoaderError(
                        (
                            "REQUIRED_MODEL_TARGET_COLUMN_MISSING:"
                            f"{target_column}"
                        )
                    )
                )

        target_mapping = (
            cls._mapping(
                manifest,
                "target_class_mapping",
            )
        )

        normalized_target_mapping: dict[
            str,
            int
        ] = {}

        for class_name in (
            cls.EXPECTED_TARGET_CLASS_MAPPING
        ):

            normalized_target_mapping[
                class_name
            ] = (
                cls._required_int(
                    target_mapping,
                    class_name,
                )
            )

        if (
            normalized_target_mapping
            !=
            cls.EXPECTED_TARGET_CLASS_MAPPING
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "TARGET_CLASS_MAPPING_MISMATCH"
                )
            )

        target_contract = (
            cls._mapping(
                manifest,
                "target_label_contract",
            )
        )

        if (
            str(
                target_contract.get(
                    "name",
                    "",
                )
            )
            !=
            cls.EXPECTED_TARGET_LABEL_CONTRACT
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "TARGET_LABEL_CONTRACT_MISMATCH"
                )
            )

        try:

            profit_atr = float(
                target_contract[
                    "profit_atr"
                ]
            )

            max_adverse_atr = float(
                target_contract[
                    "max_adverse_atr"
                ]
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:

            raise (
                Portable331TrainingInputLoaderError(
                    "TARGET_THRESHOLD_METADATA_INVALID"
                )
            ) from exc

        if (
            profit_atr
            !=
            cls.EXPECTED_TARGET_PROFIT_ATR
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "TARGET_PROFIT_ATR_MISMATCH"
                )
            )

        if (
            max_adverse_atr
            !=
            cls.EXPECTED_TARGET_MAX_ADVERSE_ATR
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "TARGET_MAX_ADVERSE_ATR_MISMATCH"
                )
            )

        return (
            tuple(
                feature_columns
            ),
            tuple(
                target_columns
            ),
        )

    def _validate_split_structure(
        self,
        dataset_path: Path,
    ) -> dict[str, int]:

        try:

            split_frame = pd.read_csv(
                dataset_path,
                usecols=[
                    "dataset_split"
                ],
            )

        except Exception as exc:

            raise (
                Portable331TrainingInputLoaderError(
                    "STRUCTURAL_SPLIT_READ_FAILED"
                )
            ) from exc

        return (
            self._validate_split_series(
                split_frame[
                    "dataset_split"
                ]
            )
        )

    def inspect_contract(
        self,
    ) -> dict[str, Any]:

        (
            dataset_path,
            manifest_path,
            manifest,
        ) = (
            self._discover_exact_artifact()
        )

        if (
            PortableTrainingFeatureProjector
            ._sha256_file(
                dataset_path
            )
            !=
            self.EXPECTED_DATASET_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_DATASET_HASH_CHANGED"
                )
            )

        if (
            PortableTrainingFeatureProjector
            ._sha256_file(
                manifest_path
            )
            !=
            self.EXPECTED_MANIFEST_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_MANIFEST_HASH_CHANGED"
                )
            )

        (
            feature_columns,
            target_columns,
        ) = (
            self._validate_manifest(
                manifest
            )
        )

        split_rows = (
            self._validate_split_structure(
                dataset_path
            )
        )

        return {
            "dataset_id": (
                self.EXPECTED_DATASET_ID
            ),
            "dataset_sha256": (
                self.EXPECTED_DATASET_SHA256
            ),
            "manifest_sha256": (
                self.EXPECTED_MANIFEST_SHA256
            ),
            "training_contract_version": (
                self.PORTABLE_FEATURE_CONTRACT
            ),
            "trainer_input_contract_version": (
                self.TRAINER_INPUT_CONTRACT_VERSION
            ),
            "trainer_input_contract_fingerprint_sha256": (
                self.TRAINER_INPUT_CONTRACT_FINGERPRINT_SHA256
            ),
            "target_access_contract_version": (
                self.TARGET_ACCESS_CONTRACT_VERSION
            ),
            "target_access_contract_fingerprint_sha256": (
                self.TARGET_ACCESS_CONTRACT_FINGERPRINT_SHA256
            ),
            "supervised_batch_contract_version": (
                self.SUPERVISED_BATCH_CONTRACT_VERSION
            ),
            "supervised_batch_contract_fingerprint_sha256": (
                self.SUPERVISED_BATCH_CONTRACT_FINGERPRINT_SHA256
            ),
            "feature_count": (
                len(
                    feature_columns
                )
            ),
            "feature_columns_sha256": (
                self.EXPECTED_FEATURE_COLUMNS_SHA256
            ),
            "train_input_fingerprint_sha256": (
                self.EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256
            ),
            "train_target_fingerprint_sha256": (
                self.EXPECTED_TRAIN_TARGET_FINGERPRINT_SHA256
            ),
            "target_columns_present_in_manifest": (
                list(
                    target_columns
                )
            ),
            "target_values_loaded": (
                False
            ),
            "split_rows": (
                split_rows
            ),
            "validation_feature_values_loaded": (
                False
            ),
            "test_feature_values_loaded": (
                False
            ),
            "live_authorized": (
                False
            ),
        }

    def load_train_features(
        self,
    ) -> Portable331TrainFeatureBatch:

        (
            dataset_path,
            manifest_path,
            manifest,
        ) = (
            self._discover_exact_artifact()
        )

        dataset_sha256 = (
            PortableTrainingFeatureProjector
            ._sha256_file(
                dataset_path
            )
        )

        manifest_sha256 = (
            PortableTrainingFeatureProjector
            ._sha256_file(
                manifest_path
            )
        )

        if (
            dataset_sha256
            !=
            self.EXPECTED_DATASET_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_DATASET_HASH_CHANGED"
                )
            )

        if (
            manifest_sha256
            !=
            self.EXPECTED_MANIFEST_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_MANIFEST_HASH_CHANGED"
                )
            )

        (
            feature_columns,
            _target_columns,
        ) = (
            self._validate_manifest(
                manifest
            )
        )

        self._validate_split_structure(
            dataset_path
        )

        usecols = [
            "decision_time",
            *feature_columns,
        ]

        try:

            frame = pd.read_csv(
                dataset_path,
                usecols=(
                    usecols
                ),
                nrows=(
                    self.EXPECTED_TRAIN_ROWS
                ),
            )

        except Exception as exc:

            raise (
                Portable331TrainingInputLoaderError(
                    "TRAIN_FEATURE_READ_FAILED"
                )
            ) from exc

        frame = frame[
            usecols
        ].copy()

        if (
            len(
                frame
            )
            !=
            self.EXPECTED_TRAIN_ROWS
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "TRAIN_FEATURE_ROW_COUNT_MISMATCH:"
                        f"{len(frame)}:"
                        f"{self.EXPECTED_TRAIN_ROWS}"
                    )
                )
            )

        if bool(
            frame[
                "decision_time"
            ]
            .duplicated()
            .any()
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "TRAIN_DUPLICATE_DECISION_TIME"
                )
            )

        input_fingerprint = (
            self._train_input_fingerprint(
                train_frame=(
                    frame
                ),
                feature_columns=(
                    feature_columns
                ),
            )
        )

        if (
            input_fingerprint
            !=
            self.EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "TRAIN_INPUT_FINGERPRINT_MISMATCH"
                )
            )

        X = (
            self._numeric_matrix(
                frame=(
                    frame
                ),
                feature_columns=(
                    feature_columns
                ),
            )
        )

        if (
            X.shape
            !=
            (
                self.EXPECTED_TRAIN_ROWS,
                self.EXPECTED_FEATURE_COUNT,
            )
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    (
                        "TRAIN_INPUT_MATRIX_SHAPE_MISMATCH:"
                        f"{X.shape}"
                    )
                )
            )

        decision_time = (
            frame[
                "decision_time"
            ]
            .astype(
                str
            )
            .to_numpy(
                copy=True
            )
        )

        X = np.asarray(
            X,
            dtype=np.float64,
        )

        X.setflags(
            write=False
        )

        decision_time.setflags(
            write=False
        )

        return (
            Portable331TrainFeatureBatch(
                dataset_id=(
                    self.EXPECTED_DATASET_ID
                ),
                dataset_sha256=(
                    dataset_sha256
                ),
                manifest_sha256=(
                    manifest_sha256
                ),
                training_contract_version=(
                    self.PORTABLE_FEATURE_CONTRACT
                ),
                trainer_input_contract_version=(
                    self.TRAINER_INPUT_CONTRACT_VERSION
                ),
                trainer_input_contract_fingerprint_sha256=(
                    self.TRAINER_INPUT_CONTRACT_FINGERPRINT_SHA256
                ),
                feature_columns=(
                    feature_columns
                ),
                feature_columns_sha256=(
                    self.EXPECTED_FEATURE_COLUMNS_SHA256
                ),
                train_input_fingerprint_sha256=(
                    input_fingerprint
                ),
                row_count=(
                    self.EXPECTED_TRAIN_ROWS
                ),
                decision_time=(
                    decision_time
                ),
                X=(
                    X
                ),
            )
        )

    def load_train_targets(
        self,
    ) -> Portable331TrainTargetBatch:

        (
            dataset_path,
            manifest_path,
            manifest,
        ) = (
            self._discover_exact_artifact()
        )

        dataset_sha256 = (
            PortableTrainingFeatureProjector
            ._sha256_file(
                dataset_path
            )
        )

        manifest_sha256 = (
            PortableTrainingFeatureProjector
            ._sha256_file(
                manifest_path
            )
        )

        if (
            dataset_sha256
            !=
            self.EXPECTED_DATASET_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_DATASET_HASH_CHANGED"
                )
            )

        if (
            manifest_sha256
            !=
            self.EXPECTED_MANIFEST_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "PORTABLE_MANIFEST_HASH_CHANGED"
                )
            )

        (
            _feature_columns,
            target_columns,
        ) = (
            self._validate_manifest(
                manifest
            )
        )

        self._validate_split_structure(
            dataset_path
        )

        for target_column in (
            self.TRAIN_TARGET_COLUMNS
        ):

            if (
                target_column
                not in
                target_columns
            ):
                raise (
                    Portable331TrainingInputLoaderError(
                        (
                            "TRAIN_TARGET_COLUMN_NOT_DECLARED:"
                            f"{target_column}"
                        )
                    )
                )

        usecols = [
            "decision_time",
            *self.TRAIN_TARGET_COLUMNS,
        ]

        try:

            frame = pd.read_csv(
                dataset_path,
                usecols=(
                    usecols
                ),
                nrows=(
                    self.EXPECTED_TRAIN_ROWS
                ),
            )

        except Exception as exc:

            raise (
                Portable331TrainingInputLoaderError(
                    "TRAIN_TARGET_READ_FAILED"
                )
            ) from exc

        frame = frame[
            usecols
        ].copy()

        (
            decision_time,
            target_class,
            target_tradeable,
            target_fingerprint,
        ) = (
            self._validate_train_target_frame(
                frame
            )
        )

        if (
            target_fingerprint
            !=
            self.EXPECTED_TRAIN_TARGET_FINGERPRINT_SHA256
        ):
            raise (
                Portable331TrainingInputLoaderError(
                    "TRAIN_TARGET_FINGERPRINT_MISMATCH"
                )
            )

        decision_time.setflags(
            write=False
        )

        target_class.setflags(
            write=False
        )

        target_tradeable.setflags(
            write=False
        )

        return (
            Portable331TrainTargetBatch(
                dataset_id=(
                    self.EXPECTED_DATASET_ID
                ),
                dataset_sha256=(
                    dataset_sha256
                ),
                manifest_sha256=(
                    manifest_sha256
                ),
                training_contract_version=(
                    self.PORTABLE_FEATURE_CONTRACT
                ),
                trainer_input_contract_version=(
                    self.TRAINER_INPUT_CONTRACT_VERSION
                ),
                trainer_input_contract_fingerprint_sha256=(
                    self.TRAINER_INPUT_CONTRACT_FINGERPRINT_SHA256
                ),
                target_access_contract_version=(
                    self.TARGET_ACCESS_CONTRACT_VERSION
                ),
                target_access_contract_fingerprint_sha256=(
                    self.TARGET_ACCESS_CONTRACT_FINGERPRINT_SHA256
                ),
                target_columns=(
                    self.TRAIN_TARGET_COLUMNS
                ),
                train_target_fingerprint_sha256=(
                    target_fingerprint
                ),
                row_count=(
                    self.EXPECTED_TRAIN_ROWS
                ),
                decision_time=(
                    decision_time
                ),
                target_class=(
                    target_class
                ),
                target_tradeable=(
                    target_tradeable
                ),
            )
        )

    def load_train_supervised(
        self,
    ) -> Portable331TrainSupervisedBatch:

        feature_batch = (
            self.load_train_features()
        )

        target_batch = (
            self.load_train_targets()
        )

        return (
            self._combine_train_batches(
                feature_batch=(
                    feature_batch
                ),
                target_batch=(
                    target_batch
                ),
            )
        )

    def load_validation_features(
        self,
    ) -> None:

        raise (
            Portable331TrainingInputLoaderError(
                "VALIDATION_FEATURE_ACCESS_NOT_AUTHORIZED"
            )
        )

    def load_validation_targets(
        self,
    ) -> None:

        raise (
            Portable331TrainingInputLoaderError(
                "VALIDATION_TARGET_ACCESS_NOT_AUTHORIZED"
            )
        )

    def load_test_features(
        self,
    ) -> None:

        raise (
            Portable331TrainingInputLoaderError(
                "TEST_FEATURE_ACCESS_NOT_AUTHORIZED"
            )
        )

    def load_test_targets(
        self,
    ) -> None:

        raise (
            Portable331TrainingInputLoaderError(
                "TEST_TARGET_ACCESS_NOT_AUTHORIZED"
            )
        )