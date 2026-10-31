from __future__ import annotations

import hashlib
import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


_training_loader_module: Any = importlib.import_module(
    "02_AI.Dataset.portable_331_training_input_loader"
)

_BaseTrainingLoader: Any = getattr(
    _training_loader_module,
    "Portable331TrainingInputLoader",
)

Portable331TrainingInputLoaderError: Any = getattr(
    _training_loader_module,
    "Portable331TrainingInputLoaderError",
)


@dataclass(frozen=True)
class Portable331RemediationSealedTestBatch:
    dataset_id: str
    dataset_sha256: str
    manifest_sha256: str
    feature_columns: tuple[str, ...]
    feature_columns_sha256: str
    target_columns: tuple[str, ...]
    row_count: int
    decision_time: np.ndarray
    X: np.ndarray
    target_class: np.ndarray
    target_tradeable: np.ndarray


class Portable331RemediationSealedTestLoader:
    """
    Dedicated one-shot remediation TEST loader.

    Authorized only after:
    - final remediation winner freeze is published
    - sealed TEST confirmation criteria are published
    - caller has independently enforced the one-shot consumption marker

    Authorized:
    - exact immutable TRAIN supervised values through frozen base loader
    - exact immutable TEST feature/target values for one-shot confirmation

    Not authorized:
    - VALIDATION feature/target access
    - TRAIN + VALIDATION refit
    - model fitting inside loader
    - preprocessing fitting
    - metrics
    - candidate selection
    - threshold tuning
    - calibration
    - artifact writes
    """

    VERSION = "1.0"

    EXPECTED_DATASET_ID: str = (
        _BaseTrainingLoader.EXPECTED_DATASET_ID
    )

    EXPECTED_DATASET_SHA256: str = (
        _BaseTrainingLoader.EXPECTED_DATASET_SHA256
    )

    EXPECTED_MANIFEST_SHA256: str = (
        _BaseTrainingLoader.EXPECTED_MANIFEST_SHA256
    )

    EXPECTED_FEATURE_COLUMNS_SHA256: str = (
        _BaseTrainingLoader.EXPECTED_FEATURE_COLUMNS_SHA256
    )

    EXPECTED_FEATURE_COUNT: int = (
        _BaseTrainingLoader.EXPECTED_FEATURE_COUNT
    )

    EXPECTED_TOTAL_ROWS: int = (
        _BaseTrainingLoader.EXPECTED_TOTAL_ROWS
    )

    EXPECTED_TRAIN_ROWS: int = (
        _BaseTrainingLoader.EXPECTED_TRAIN_ROWS
    )

    EXPECTED_VALIDATION_ROWS: int = (
        _BaseTrainingLoader.EXPECTED_VALIDATION_ROWS
    )

    EXPECTED_TEST_ROWS: int = (
        _BaseTrainingLoader.EXPECTED_TEST_ROWS
    )

    TARGET_COLUMNS: tuple[str, ...] = tuple(
        _BaseTrainingLoader.TRAIN_TARGET_COLUMNS
    )

    TEST_START_ROW = (
        EXPECTED_TRAIN_ROWS
        +
        EXPECTED_VALIDATION_ROWS
    )

    def __init__(
        self,
        canonical_root: str | Path,
    ) -> None:

        self.canonical_root = Path(
            canonical_root
        )

        self._base: Any = _BaseTrainingLoader(
            self.canonical_root
        )

    @staticmethod
    def _freeze_array(
        value: np.ndarray,
    ) -> np.ndarray:

        value.setflags(
            write=False
        )

        return value

    @staticmethod
    def _require_dataframe(
        value: Any,
        reason: str,
    ) -> pd.DataFrame:

        if not isinstance(
            value,
            pd.DataFrame,
        ):
            raise Portable331TrainingInputLoaderError(
                reason
            )

        return value

    @staticmethod
    def _require_series(
        value: Any,
        reason: str,
    ) -> pd.Series:

        if not isinstance(
            value,
            pd.Series,
        ):
            raise Portable331TrainingInputLoaderError(
                reason
            )

        return value

    @staticmethod
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

    def load_train_supervised(
        self,
    ) -> Any:

        return self._base.load_train_supervised()

    def _test_frame(
        self,
        *,
        usecols: list[str],
    ) -> pd.DataFrame:

        (
            dataset_path,
            manifest_path,
            manifest,
        ) = self._base._discover_exact_artifact()

        dataset_sha = self._sha256_file(
            dataset_path
        )

        manifest_sha = self._sha256_file(
            manifest_path
        )

        if (
            dataset_sha
            !=
            self.EXPECTED_DATASET_SHA256
        ):
            raise Portable331TrainingInputLoaderError(
                "SEALED_TEST_DATASET_HASH_CHANGED"
            )

        if (
            manifest_sha
            !=
            self.EXPECTED_MANIFEST_SHA256
        ):
            raise Portable331TrainingInputLoaderError(
                "SEALED_TEST_MANIFEST_HASH_CHANGED"
            )

        (
            _feature_columns,
            _target_columns,
        ) = self._base._validate_manifest(
            manifest
        )

        split_rows: dict[str, int] = (
            self._base._validate_split_structure(
                dataset_path
            )
        )

        if (
            split_rows.get(
                "TRAIN"
            )
            !=
            self.EXPECTED_TRAIN_ROWS
        ):
            raise Portable331TrainingInputLoaderError(
                "SEALED_TEST_TRAIN_ROW_COUNT_MISMATCH"
            )

        if (
            split_rows.get(
                "VALIDATION"
            )
            !=
            self.EXPECTED_VALIDATION_ROWS
        ):
            raise Portable331TrainingInputLoaderError(
                "SEALED_TEST_VALIDATION_ROW_COUNT_MISMATCH"
            )

        if (
            split_rows.get(
                "TEST"
            )
            !=
            self.EXPECTED_TEST_ROWS
        ):
            raise Portable331TrainingInputLoaderError(
                "SEALED_TEST_ROW_COUNT_MISMATCH"
            )

        columns = [
            "decision_time",
            "dataset_split",
            *usecols,
        ]

        skiprows: list[int] = list(
            range(
                1,
                self.TEST_START_ROW + 1,
            )
        )

        try:

            raw_frame = pd.read_csv(
                dataset_path,
                usecols=columns,
                skiprows=skiprows,
                nrows=self.EXPECTED_TEST_ROWS,
            )

        except Exception as exc:

            raise Portable331TrainingInputLoaderError(
                "SEALED_TEST_READ_FAILED"
            ) from exc

        frame = self._require_dataframe(
            raw_frame,
            "SEALED_TEST_READ_NOT_DATAFRAME",
        )

        selected = frame.loc[
            :,
            columns,
        ].copy()

        frame = self._require_dataframe(
            selected,
            "SEALED_TEST_SELECTION_NOT_DATAFRAME",
        )

        if (
            len(
                frame
            )
            !=
            self.EXPECTED_TEST_ROWS
        ):
            raise Portable331TrainingInputLoaderError(
                (
                    "SEALED_TEST_ROW_COUNT_MISMATCH:"
                    f"{len(frame)}:"
                    f"{self.EXPECTED_TEST_ROWS}"
                )
            )

        split_series = self._require_series(
            frame.loc[
                :,
                "dataset_split",
            ],
            "SEALED_TEST_DATASET_SPLIT_NOT_SERIES",
        )

        split_values = (
            split_series
            .astype(
                str
            )
            .tolist()
        )

        if any(
            value
            !=
            "TEST"
            for value
            in split_values
        ):
            raise Portable331TrainingInputLoaderError(
                "NON_TEST_ROW_ENTERED_SEALED_TEST_WINDOW"
            )

        decision_time_series = self._require_series(
            frame.loc[
                :,
                "decision_time",
            ],
            "SEALED_TEST_DECISION_TIME_NOT_SERIES",
        )

        if bool(
            decision_time_series
            .duplicated()
            .any()
        ):
            raise Portable331TrainingInputLoaderError(
                "SEALED_TEST_DUPLICATE_DECISION_TIME"
            )

        return frame

    def load_test_supervised(
        self,
    ) -> Portable331RemediationSealedTestBatch:

        (
            _dataset_path,
            _manifest_path,
            manifest,
        ) = self._base._discover_exact_artifact()

        (
            feature_columns_raw,
            target_columns_raw,
        ) = self._base._validate_manifest(
            manifest
        )

        feature_columns = tuple(
            feature_columns_raw
        )

        target_columns = tuple(
            target_columns_raw
        )

        for target_column in (
            self.TARGET_COLUMNS
        ):

            if (
                target_column
                not in
                target_columns
            ):
                raise Portable331TrainingInputLoaderError(
                    (
                        "SEALED_TEST_TARGET_NOT_DECLARED:"
                        f"{target_column}"
                    )
                )

        frame = self._test_frame(
            usecols=[
                *feature_columns,
                *self.TARGET_COLUMNS,
            ]
        )

        X: np.ndarray = (
            self._base._numeric_matrix(
                frame=frame,
                feature_columns=feature_columns,
            )
        )

        if (
            X.shape
            !=
            (
                self.EXPECTED_TEST_ROWS,
                self.EXPECTED_FEATURE_COUNT,
            )
        ):
            raise Portable331TrainingInputLoaderError(
                (
                    "SEALED_TEST_MATRIX_SHAPE_MISMATCH:"
                    f"{X.shape}"
                )
            )

        decision_time_series = self._require_series(
            frame.loc[
                :,
                "decision_time",
            ],
            "SEALED_TEST_DECISION_TIME_NOT_SERIES",
        )

        target_class_series = self._require_series(
            frame.loc[
                :,
                "target_class",
            ],
            "SEALED_TEST_TARGET_CLASS_NOT_SERIES",
        )

        target_tradeable_series = self._require_series(
            frame.loc[
                :,
                "target_tradeable",
            ],
            "SEALED_TEST_TARGET_TRADEABLE_NOT_SERIES",
        )

        decision_time = (
            decision_time_series
            .astype(
                str
            )
            .to_numpy(
                copy=True
            )
        )

        target_class: np.ndarray = (
            self._base._normalize_target_class_array(
                target_class_series
            )
        )

        target_tradeable: np.ndarray = (
            self._base._normalize_target_tradeable_array(
                target_tradeable_series
            )
        )

        if (
            target_class.shape[0]
            !=
            self.EXPECTED_TEST_ROWS
        ):
            raise Portable331TrainingInputLoaderError(
                "SEALED_TEST_TARGET_CLASS_COUNT_MISMATCH"
            )

        if (
            target_tradeable.shape[0]
            !=
            self.EXPECTED_TEST_ROWS
        ):
            raise Portable331TrainingInputLoaderError(
                "SEALED_TEST_TARGET_TRADEABLE_COUNT_MISMATCH"
            )

        expected_tradeable = (
            target_class
            !=
            0
        ).astype(
            np.int8
        )

        if not bool(
            np.array_equal(
                expected_tradeable,
                target_tradeable,
            )
        ):
            raise Portable331TrainingInputLoaderError(
                "SEALED_TEST_TARGET_TRADEABLE_INCONSISTENT"
            )

        X = np.asarray(
            X,
            dtype=np.float64,
        )

        decision_time = np.asarray(
            decision_time
        )

        target_class = np.asarray(
            target_class,
            dtype=np.int8,
        )

        target_tradeable = np.asarray(
            target_tradeable,
            dtype=np.int8,
        )

        if not bool(
            np.isfinite(
                X
            ).all()
        ):
            raise Portable331TrainingInputLoaderError(
                "SEALED_TEST_FEATURE_MATRIX_NON_FINITE"
            )

        self._freeze_array(
            X
        )

        self._freeze_array(
            decision_time
        )

        self._freeze_array(
            target_class
        )

        self._freeze_array(
            target_tradeable
        )

        return Portable331RemediationSealedTestBatch(
            dataset_id=(
                self.EXPECTED_DATASET_ID
            ),
            dataset_sha256=(
                self.EXPECTED_DATASET_SHA256
            ),
            manifest_sha256=(
                self.EXPECTED_MANIFEST_SHA256
            ),
            feature_columns=(
                feature_columns
            ),
            feature_columns_sha256=(
                self.EXPECTED_FEATURE_COLUMNS_SHA256
            ),
            target_columns=(
                self.TARGET_COLUMNS
            ),
            row_count=(
                self.EXPECTED_TEST_ROWS
            ),
            decision_time=(
                decision_time
            ),
            X=X,
            target_class=(
                target_class
            ),
            target_tradeable=(
                target_tradeable
            ),
        )

    def load_validation_features(
        self,
    ) -> None:

        raise Portable331TrainingInputLoaderError(
            "VALIDATION_ACCESS_FORBIDDEN_DURING_SEALED_TEST"
        )

    def load_validation_targets(
        self,
    ) -> None:

        raise Portable331TrainingInputLoaderError(
            "VALIDATION_ACCESS_FORBIDDEN_DURING_SEALED_TEST"
        )

    def load_validation_supervised(
        self,
    ) -> None:

        raise Portable331TrainingInputLoaderError(
            "VALIDATION_ACCESS_FORBIDDEN_DURING_SEALED_TEST"
        )