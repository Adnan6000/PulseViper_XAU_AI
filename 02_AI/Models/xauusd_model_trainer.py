"""
===============================================================================
Module      : xauusd_model_trainer.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Symbol-Isolated XAUUSD Multiclass Model Trainer
===============================================================================

Model:
    XAUUSD_MODEL_v1

Classes:
    SHORT    = -1
    NO_TRADE =  0
    LONG     =  1

Guarantees:
- Loads only the exact learning-scope training matrix.
- Verifies dataset SHA256.
- Uses feature columns declared by the training manifest.
- StandardScaler is fitted ONLY on TRAIN.
- Model is fitted ONLY on TRAIN.
- VALIDATION and TEST are never used for fitting.
- Produces LONG / SHORT / NO_TRADE probabilities.
- Reports confidence and normalized entropy uncertainty.
- Persists model/scaler/manifest under exact XAUUSD learning scope.
- No MT5 calls.
- No execution authority.
- No live authorization.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import os
import platform
import tempfile

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import joblib
import numpy as np
import pandas as pd
import sklearn

from sklearn.ensemble import (
    HistGradientBoostingClassifier,
)
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_fscore_support,
)
from sklearn.preprocessing import (
    StandardScaler,
)


ROOT_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
)

CANONICAL_ROOT = (
    ROOT_DIR
    /
    "01_Data"
    /
    "Canonical"
)


training_matrix_module: Any = (
    importlib.import_module(
        "02_AI.Dataset.training_matrix_builder"
    )
)

TrainingMatrixBuilder: Any = (
    training_matrix_module.TrainingMatrixBuilder
)


CLASS_IDS = (
    -1,
    0,
    1,
)

CLASS_NAMES = {
    -1: "SHORT",
    0: "NO_TRADE",
    1: "LONG",
}


class XAUUSDModelTrainingError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class TrainingSnapshot:

    dataset_id: str

    dataset_path: Path

    manifest_path: Path

    dataset_sha256: str

    manifest_sha256: str

    feature_columns: tuple[
        str,
        ...
    ]

    row_count: int

    training_contract_version: str

    base_timeframe: str


@dataclass(frozen=True)
class XAUUSDModelTrainingResult:

    model_id: str

    model_path: Path

    scaler_path: Path

    manifest_path: Path

    model_sha256: str

    scaler_sha256: str

    manifest_sha256: str

    training_dataset_id: str

    training_dataset_sha256: str

    feature_count: int

    train_rows: int

    validation_rows: int

    test_rows: int

    validation_metrics: dict[
        str,
        Any,
    ]

    test_metrics: dict[
        str,
        Any,
    ]

    learning_scope_fingerprint: str

    model_training_contract_fingerprint: str

    live_authorized: bool = False


class XAUUSDModelTrainer:

    VERSION = "1.0"

    MODEL_ID = (
        "XAUUSD_MODEL_v1"
    )

    ALGORITHM = (
        "SKLEARN_HIST_GRADIENT_BOOSTING_MULTICLASS"
    )

    def __init__(
        self,
        *,
        canonical_root: Path | None = None,
    ) -> None:

        self.canonical_root = (
            Path(
                canonical_root
            )
            if canonical_root is not None
            else
            CANONICAL_ROOT
        )

    # =========================================================================
    # Hash / serialization
    # =========================================================================

    @staticmethod
    def _sha256_bytes(
        payload: bytes,
    ) -> str:

        return hashlib.sha256(
            payload
        ).hexdigest()

    @staticmethod
    def _sha256_file(
        path: Path,
    ) -> str:

        digest = hashlib.sha256()

        with path.open(
            "rb"
        ) as handle:

            while True:

                chunk = handle.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                digest.update(
                    chunk
                )

        return digest.hexdigest()

    @staticmethod
    def _canonical_json_bytes(
        document: Any,
    ) -> bytes:

        return (
            json.dumps(
                document,
                sort_keys=True,
                separators=(
                    ",",
                    ":",
                ),
                ensure_ascii=False,
                allow_nan=False,
            )
            +
            "\n"
        ).encode(
            "utf-8"
        )

    @classmethod
    def _canonical_hash(
        cls,
        document: Any,
    ) -> str:

        return cls._sha256_bytes(
            cls._canonical_json_bytes(
                document
            )
        )

    # =========================================================================
    # Context / learning scope
    # =========================================================================

    @staticmethod
    def _validate_context(
        context: Any,
    ) -> None:

        if context is None:

            raise XAUUSDModelTrainingError(
                "INSTRUMENT_CONTEXT_REQUIRED"
            )

        if bool(
            getattr(
                context,
                "live_authorized",
                False,
            )
        ):

            raise XAUUSDModelTrainingError(
                "LIVE_AUTHORIZED_CONTEXT_REJECTED"
            )

        if (
            str(
                getattr(
                    context,
                    "canonical_symbol",
                    "",
                )
            )
            !=
            "XAUUSD"
        ):

            raise XAUUSDModelTrainingError(
                "MODEL_CANONICAL_SYMBOL_MISMATCH"
            )

        if (
            str(
                getattr(
                    context,
                    "asset_class",
                    "",
                )
            )
            !=
            "METAL"
        ):

            raise XAUUSDModelTrainingError(
                "MODEL_ASSET_CLASS_MISMATCH"
            )

        if not str(
            getattr(
                context,
                "broker_symbol",
                "",
            )
        ).strip():

            raise XAUUSDModelTrainingError(
                "BROKER_SYMBOL_MISSING"
            )

    @staticmethod
    def _safe_token(
        value: Any,
        name: str,
    ) -> str:

        raw = str(
            value
        ).strip()

        if (
            not raw
            or
            raw in {
                ".",
                "..",
            }
            or
            "/"
            in raw
            or
            "\\"
            in raw
            or
            "\x00"
            in raw
        ):

            raise XAUUSDModelTrainingError(
                f"INVALID_{name.upper()}"
            )

        cleaned = "".join(
            character
            for character in raw
            if (
                character.isalnum()
                or
                character in {
                    "_",
                    "-",
                    ".",
                }
            )
        )

        if not cleaned:

            raise XAUUSDModelTrainingError(
                f"INVALID_{name.upper()}"
            )

        return cleaned

    # =========================================================================
    # Training matrix discovery
    # =========================================================================

    def _training_directory(
        self,
        *,
        context: Any,
        training_contract_version: str,
    ) -> tuple[
        Path,
        str,
    ]:

        learning_fingerprint = (
            TrainingMatrixBuilder
            .learning_scope_fingerprint(
                context
            )
        )

        canonical_symbol = (
            self._safe_token(
                context.canonical_symbol,
                "canonical_symbol",
            )
        )

        safe_contract = (
            self._safe_token(
                training_contract_version,
                "training_contract_version",
            )
        )

        path = (
            self.canonical_root
            /
            "Instruments"
            /
            canonical_symbol
            /
            "learning"
            /
            (
                "scope_"
                +
                learning_fingerprint
            )
            /
            "training"
            /
            safe_contract
        )

        return (
            path,
            learning_fingerprint,
        )

    def discover_training_snapshot(
        self,
        *,
        context: Any,
        training_contract_version: str = (
            "XAUUSD_MTF_TRAINING_V1"
        ),
    ) -> TrainingSnapshot:

        self._validate_context(
            context
        )

        (
            directory,
            learning_fingerprint,
        ) = self._training_directory(
            context=context,
            training_contract_version=(
                training_contract_version
            ),
        )

        if not directory.is_dir():

            raise XAUUSDModelTrainingError(
                (
                    "TRAINING_DIRECTORY_MISSING: "
                    f"{directory}"
                )
            )

        manifests = sorted(
            directory.glob(
                "*.manifest.json"
            )
        )

        if not manifests:

            raise XAUUSDModelTrainingError(
                "TRAINING_MANIFEST_MISSING"
            )

        candidates: list[
            tuple[
                pd.Timestamp,
                str,
                Path,
                dict[
                    str,
                    Any,
                ],
            ]
        ] = []

        for manifest_path in manifests:

            try:

                manifest = json.loads(
                    manifest_path.read_text(
                        encoding="utf-8"
                    )
                )

            except Exception as exc:

                raise XAUUSDModelTrainingError(
                    (
                        "INVALID_TRAINING_MANIFEST: "
                        f"{manifest_path}"
                    )
                ) from exc

            if (
                str(
                    manifest.get(
                        "training_contract_version",
                        "",
                    )
                )
                !=
                training_contract_version
            ):

                continue

            if (
                str(
                    manifest.get(
                        "learning_scope_fingerprint",
                        "",
                    )
                )
                !=
                learning_fingerprint
            ):

                continue

            if (
                bool(
                    manifest.get(
                        "live_authorized",
                        False,
                    )
                )
            ):

                raise XAUUSDModelTrainingError(
                    "LIVE_AUTHORIZED_TRAINING_MANIFEST_REJECTED"
                )

            base_timeframe = str(
                manifest.get(
                    "base_timeframe",
                    "",
                )
            ).strip().upper()

            snapshots = manifest.get(
                "source_historical_snapshots",
                {},
            )

            base_snapshot = (
                snapshots.get(
                    base_timeframe,
                    {}
                )
                if isinstance(
                    snapshots,
                    Mapping,
                )
                else
                {}
            )

            end_time_raw = (
                base_snapshot.get(
                    "end_time",
                    "",
                )
                if isinstance(
                    base_snapshot,
                    Mapping,
                )
                else
                ""
            )

            try:

                end_time = pd.to_datetime(
                    end_time_raw,
                    utc=True,
                    errors="raise",
                )

            except Exception:

                end_time = pd.Timestamp(
                    "1970-01-01",
                    tz="UTC",
                )

            dataset_id = str(
                manifest.get(
                    "dataset_id",
                    "",
                )
            )

            candidates.append(
                (
                    end_time,
                    dataset_id,
                    manifest_path,
                    manifest,
                )
            )

        if not candidates:

            raise XAUUSDModelTrainingError(
                "NO_MATCHING_TRAINING_MANIFEST"
            )

        candidates.sort(
            key=lambda value: (
                value[0],
                value[1],
            )
        )

        (
            _end_time,
            dataset_id,
            manifest_path,
            manifest,
        ) = candidates[-1]

        dataset_filename = str(
            manifest.get(
                "dataset_filename",
                "",
            )
        ).strip()

        if not dataset_filename:

            raise XAUUSDModelTrainingError(
                "TRAINING_DATASET_FILENAME_MISSING"
            )

        dataset_path = (
            manifest_path.parent
            /
            dataset_filename
        )

        if not dataset_path.is_file():

            raise XAUUSDModelTrainingError(
                (
                    "TRAINING_DATASET_MISSING: "
                    f"{dataset_path}"
                )
            )

        expected_hash = str(
            manifest.get(
                "dataset_sha256",
                "",
            )
        ).strip()

        actual_hash = (
            self._sha256_file(
                dataset_path
            )
        )

        if (
            not expected_hash
            or
            actual_hash
            !=
            expected_hash
        ):

            raise XAUUSDModelTrainingError(
                "TRAINING_DATASET_HASH_MISMATCH"
            )

        feature_columns_raw = (
            manifest.get(
                "feature_columns",
                []
            )
        )

        if not isinstance(
            feature_columns_raw,
            list,
        ):

            raise XAUUSDModelTrainingError(
                "INVALID_FEATURE_COLUMN_MANIFEST"
            )

        feature_columns = tuple(
            str(
                value
            )
            for value
            in feature_columns_raw
        )

        if (
            not feature_columns
            or
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

            raise XAUUSDModelTrainingError(
                "INVALID_FEATURE_COLUMNS"
            )

        return TrainingSnapshot(
            dataset_id=dataset_id,
            dataset_path=dataset_path,
            manifest_path=manifest_path,
            dataset_sha256=actual_hash,
            manifest_sha256=(
                self._sha256_file(
                    manifest_path
                )
            ),
            feature_columns=(
                feature_columns
            ),
            row_count=int(
                manifest.get(
                    "row_count",
                    0,
                )
            ),
            training_contract_version=(
                training_contract_version
            ),
            base_timeframe=str(
                manifest.get(
                    "base_timeframe",
                    "",
                )
            ).strip().upper(),
        )

    # =========================================================================
    # Training frame validation
    # =========================================================================

    def load_training_frame(
        self,
        *,
        context: Any,
        snapshot: TrainingSnapshot,
    ) -> pd.DataFrame:

        frame = pd.read_csv(
            snapshot.dataset_path
        )

        if frame.empty:

            raise XAUUSDModelTrainingError(
                "TRAINING_DATASET_EMPTY"
            )

        if (
            snapshot.row_count
            > 0
            and
            len(
                frame
            )
            !=
            snapshot.row_count
        ):

            raise XAUUSDModelTrainingError(
                "TRAINING_ROW_COUNT_MISMATCH"
            )

        required = {
            "target_class",
            "target_class_id",
            "dataset_split",
            "pv_canonical_symbol",
            "pv_asset_class",
            "pv_broker_id",
            "pv_broker_symbol",
            "pv_contract_spec_id",
            "pv_data_schema_version",
            "pv_feature_contract_version",
        }

        required.update(
            snapshot.feature_columns
        )

        missing = (
            required
            -
            set(
                frame.columns
            )
        )

        if missing:

            raise XAUUSDModelTrainingError(
                (
                    "TRAINING_COLUMNS_MISSING: "
                    +
                    ", ".join(
                        sorted(
                            missing
                        )
                    )
                )
            )

        identity_expectations = {
            "pv_canonical_symbol": str(
                context.canonical_symbol
            ),
            "pv_asset_class": str(
                context.asset_class
            ),
            "pv_broker_id": str(
                context.broker_id
            ),
            "pv_broker_symbol": str(
                context.broker_symbol
            ),
            "pv_contract_spec_id": str(
                context.contract_spec_id
            ),
            "pv_data_schema_version": str(
                context.data_schema_version
            ),
            "pv_feature_contract_version": str(
                context.feature_contract_version
            ),
        }

        for (
            column,
            expected,
        ) in identity_expectations.items():

            values = (
                frame[
                    column
                ]
                .astype(
                    str
                )
                .drop_duplicates()
            )

            if (
                len(
                    values
                )
                !=
                1
                or
                str(
                    values.iloc[
                        0
                    ]
                )
                !=
                expected
            ):

                raise XAUUSDModelTrainingError(
                    (
                        "TRAINING_IDENTITY_MISMATCH: "
                        f"{column}"
                    )
                )

        expected_target_ids = (
            frame[
                "target_class"
            ]
            .map(
                {
                    "SHORT": -1,
                    "NO_TRADE": 0,
                    "LONG": 1,
                }
            )
        )

        target_ids = pd.to_numeric(
            frame[
                "target_class_id"
            ],
            errors="coerce",
        )

        if bool(
            expected_target_ids.isna().any()
        ):

            raise XAUUSDModelTrainingError(
                "UNKNOWN_TARGET_CLASS"
            )

        if not np.array_equal(
            expected_target_ids.to_numpy(
                dtype=np.int8
            ),
            target_ids.to_numpy(
                dtype=np.int8
            ),
        ):

            raise XAUUSDModelTrainingError(
                "TARGET_CLASS_ID_MISMATCH"
            )

        split_values = set(
            frame[
                "dataset_split"
            ]
            .astype(
                str
            )
            .unique()
        )

        if split_values != {
            "TRAIN",
            "VALIDATION",
            "TEST",
        }:

            raise XAUUSDModelTrainingError(
                (
                    "INVALID_DATASET_SPLITS: "
                    f"{sorted(split_values)}"
                )
            )

        feature_frame = (
            frame[
                list(
                    snapshot.feature_columns
                )
            ]
            .apply(
                pd.to_numeric,
                errors="coerce",
            )
        )

        values = feature_frame.to_numpy(
            dtype=np.float64,
            copy=False,
        )

        if not np.isfinite(
            values
        ).all():

            raise XAUUSDModelTrainingError(
                "NONFINITE_MODEL_FEATURES"
            )

        for column in snapshot.feature_columns:

            if str(
                column
            ).startswith(
                "target_"
            ):

                raise XAUUSDModelTrainingError(
                    (
                        "TARGET_COLUMN_IN_FEATURE_SET: "
                        f"{column}"
                    )
                )

        return frame

    # =========================================================================
    # Class weighting
    # =========================================================================

    @staticmethod
    def _sample_weights(
        y: np.ndarray,
        *,
        balance_power: float,
    ) -> tuple[
        np.ndarray,
        dict[
            str,
            float,
        ],
    ]:

        if (
            not math.isfinite(
                float(
                    balance_power
                )
            )
            or
            balance_power
            <
            0.0
            or
            balance_power
            >
            1.0
        ):

            raise XAUUSDModelTrainingError(
                "INVALID_CLASS_BALANCE_POWER"
            )

        counts = {
            int(
                class_id
            ): int(
                np.sum(
                    y
                    ==
                    class_id
                )
            )
            for class_id
            in CLASS_IDS
        }

        if any(
            count
            <=
            0
            for count
            in counts.values()
        ):

            raise XAUUSDModelTrainingError(
                (
                    "TRAIN_SPLIT_MISSING_CLASS: "
                    f"{counts}"
                )
            )

        total = len(
            y
        )

        class_count = len(
            CLASS_IDS
        )

        raw = {
            class_id: (
                total
                /
                (
                    class_count
                    *
                    count
                )
            )
            **
            balance_power
            for (
                class_id,
                count,
            )
            in counts.items()
        }

        sample_weights = np.asarray(
            [
                raw[
                    int(
                        value
                    )
                ]
                for value
                in y
            ],
            dtype=np.float64,
        )

        mean_weight = float(
            np.mean(
                sample_weights
            )
        )

        if (
            not math.isfinite(
                mean_weight
            )
            or
            mean_weight
            <=
            0.0
        ):

            raise XAUUSDModelTrainingError(
                "INVALID_SAMPLE_WEIGHTS"
            )

        sample_weights = (
            sample_weights
            /
            mean_weight
        )

        normalized_class_weights = {
            CLASS_NAMES[
                class_id
            ]: float(
                raw[
                    class_id
                ]
                /
                mean_weight
            )
            for class_id
            in CLASS_IDS
        }

        return (
            sample_weights,
            normalized_class_weights,
        )

    # =========================================================================
    # Evaluation
    # =========================================================================

    @staticmethod
    def _normalized_entropy(
        probabilities: np.ndarray,
    ) -> np.ndarray:

        clipped = np.clip(
            probabilities,
            1e-12,
            1.0,
        )

        entropy = -np.sum(
            clipped
            *
            np.log(
                clipped
            ),
            axis=1,
        )

        return (
            entropy
            /
            math.log(
                probabilities.shape[
                    1
                ]
            )
        )

    @staticmethod
    def _expected_calibration_error(
        *,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        confidence: np.ndarray,
        bins: int = 10,
    ) -> float:

        edges = np.linspace(
            0.0,
            1.0,
            bins
            +
            1,
        )

        total = len(
            y_true
        )

        if total == 0:
            return 0.0

        ece = 0.0

        for index in range(
            bins
        ):

            low = edges[
                index
            ]

            high = edges[
                index
                +
                1
            ]

            if index == (
                bins
                -
                1
            ):

                mask = (
                    confidence
                    >=
                    low
                ) & (
                    confidence
                    <=
                    high
                )

            else:

                mask = (
                    confidence
                    >=
                    low
                ) & (
                    confidence
                    <
                    high
                )

            count = int(
                np.sum(
                    mask
                )
            )

            if count == 0:
                continue

            bin_accuracy = float(
                np.mean(
                    y_true[
                        mask
                    ]
                    ==
                    y_pred[
                        mask
                    ]
                )
            )

            bin_confidence = float(
                np.mean(
                    confidence[
                        mask
                    ]
                )
            )

            ece += (
                count
                /
                total
            ) * abs(
                bin_accuracy
                -
                bin_confidence
            )

        return float(
            ece
        )

    @classmethod
    def _evaluate(
        cls,
        *,
        model: Any,
        x: np.ndarray,
        y: np.ndarray,
    ) -> dict[
        str,
        Any,
    ]:

        predicted = model.predict(
            x
        ).astype(
            np.int8
        )

        probabilities = (
            model.predict_proba(
                x
            )
        )

        model_classes = tuple(
            int(
                value
            )
            for value
            in model.classes_
        )

        if model_classes != CLASS_IDS:

            raise XAUUSDModelTrainingError(
                (
                    "MODEL_CLASS_ORDER_MISMATCH: "
                    f"{model_classes}"
                )
            )

        precision, recall, f1, support = (
            precision_recall_fscore_support(
                y,
                predicted,
                labels=list(
                    CLASS_IDS
                ),
                zero_division=0,
            )
        )

        confusion = confusion_matrix(
            y,
            predicted,
            labels=list(
                CLASS_IDS
            ),
        )

        confidence = np.max(
            probabilities,
            axis=1,
        )

        uncertainty = (
            cls._normalized_entropy(
                probabilities
            )
        )

        one_hot = np.zeros_like(
            probabilities,
            dtype=np.float64,
        )

        for (
            column_index,
            class_id,
        ) in enumerate(
            CLASS_IDS
        ):

            one_hot[
                :,
                column_index
            ] = (
                y
                ==
                class_id
            ).astype(
                np.float64
            )

        multiclass_brier = float(
            np.mean(
                np.sum(
                    (
                        probabilities
                        -
                        one_hot
                    )
                    **
                    2,
                    axis=1,
                )
            )
        )

        selective: dict[
            str,
            Any,
        ] = {}

        for threshold in (
            0.50,
            0.60,
            0.70,
            0.80,
        ):

            mask = (
                confidence
                >=
                threshold
            )

            count = int(
                np.sum(
                    mask
                )
            )

            selective[
                f"{threshold:.2f}"
            ] = {
                "coverage": float(
                    np.mean(
                        mask
                    )
                ),
                "rows": count,
                "accuracy": (
                    float(
                        np.mean(
                            predicted[
                                mask
                            ]
                            ==
                            y[
                                mask
                            ]
                        )
                    )
                    if count
                    else
                    None
                ),
            }

        per_class = {}

        for (
            index,
            class_id,
        ) in enumerate(
            CLASS_IDS
        ):

            name = (
                CLASS_NAMES[
                    class_id
                ]
            )

            per_class[
                name
            ] = {
                "precision": float(
                    precision[
                        index
                    ]
                ),
                "recall": float(
                    recall[
                        index
                    ]
                ),
                "f1": float(
                    f1[
                        index
                    ]
                ),
                "support": int(
                    support[
                        index
                    ]
                ),
                "mean_probability": float(
                    np.mean(
                        probabilities[
                            :,
                            index
                        ]
                    )
                ),
            }

        prediction_distribution = {
            CLASS_NAMES[
                class_id
            ]: int(
                np.sum(
                    predicted
                    ==
                    class_id
                )
            )
            for class_id
            in CLASS_IDS
        }

        return {
            "rows": int(
                len(
                    y
                )
            ),
            "accuracy": float(
                accuracy_score(
                    y,
                    predicted,
                )
            ),
            "balanced_accuracy": float(
                balanced_accuracy_score(
                    y,
                    predicted,
                )
            ),
            "macro_f1": float(
                f1_score(
                    y,
                    predicted,
                    average="macro",
                    labels=list(
                        CLASS_IDS
                    ),
                    zero_division=0,
                )
            ),
            "log_loss": float(
                log_loss(
                    y,
                    probabilities,
                    labels=list(
                        CLASS_IDS
                    ),
                )
            ),
            "multiclass_brier": (
                multiclass_brier
            ),
            "expected_calibration_error": (
                cls._expected_calibration_error(
                    y_true=y,
                    y_pred=predicted,
                    confidence=confidence,
                )
            ),
            "mean_confidence": float(
                np.mean(
                    confidence
                )
            ),
            "median_confidence": float(
                np.median(
                    confidence
                )
            ),
            "mean_uncertainty": float(
                np.mean(
                    uncertainty
                )
            ),
            "median_uncertainty": float(
                np.median(
                    uncertainty
                )
            ),
            "prediction_distribution": (
                prediction_distribution
            ),
            "per_class": (
                per_class
            ),
            "confusion_matrix": {
                "labels": [
                    "SHORT",
                    "NO_TRADE",
                    "LONG",
                ],
                "rows": (
                    confusion
                    .astype(
                        int
                    )
                    .tolist()
                ),
            },
            "selective_confidence": (
                selective
            ),
        }

    # =========================================================================
    # Artifact writing
    # =========================================================================

    def _dump_joblib_content_addressed(
        self,
        *,
        value: Any,
        directory: Path,
        stem: str,
    ) -> tuple[
        Path,
        str,
    ]:

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_path: Path | None = None

        try:

            with tempfile.NamedTemporaryFile(
                suffix=".joblib",
                prefix="pv_model_",
                dir=directory,
                delete=False,
            ) as handle:

                temp_path = Path(
                    handle.name
                )

            joblib.dump(
                value,
                temp_path,
                compress=3,
            )

            artifact_hash = (
                self._sha256_file(
                    temp_path
                )
            )

            final_path = (
                directory
                /
                (
                    stem
                    +
                    "_"
                    +
                    artifact_hash[
                        :16
                    ]
                    +
                    ".joblib"
                )
            )

            if final_path.exists():

                existing_hash = (
                    self._sha256_file(
                        final_path
                    )
                )

                if (
                    existing_hash
                    !=
                    artifact_hash
                ):

                    raise XAUUSDModelTrainingError(
                        "MODEL_ARTIFACT_COLLISION"
                    )

                temp_path.unlink(
                    missing_ok=True
                )

                temp_path = None

                return (
                    final_path,
                    artifact_hash,
                )

            os.replace(
                temp_path,
                final_path,
            )

            temp_path = None

            return (
                final_path,
                artifact_hash,
            )

        finally:

            if (
                temp_path
                is not None
            ):

                try:

                    temp_path.unlink(
                        missing_ok=True
                    )

                except Exception:

                    pass

    @staticmethod
    def _write_immutable(
        *,
        path: Path,
        payload: bytes,
    ) -> None:

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if path.exists():

            if (
                path.read_bytes()
                !=
                payload
            ):

                raise XAUUSDModelTrainingError(
                    "MODEL_MANIFEST_COLLISION"
                )

            return

        try:

            with path.open(
                "xb"
            ) as handle:

                handle.write(
                    payload
                )

                handle.flush()

                os.fsync(
                    handle.fileno()
                )

        except FileExistsError:

            if (
                path.read_bytes()
                !=
                payload
            ):

                raise XAUUSDModelTrainingError(
                    "MODEL_MANIFEST_COLLISION"
                )

    # =========================================================================
    # Train
    # =========================================================================

    def train(
        self,
        *,
        context: Any,
        training_contract_version: str = (
            "XAUUSD_MTF_TRAINING_V1"
        ),
        random_state: int = 42,
        max_iter: int = 250,
        learning_rate: float = 0.05,
        max_leaf_nodes: int = 31,
        min_samples_leaf: int = 40,
        l2_regularization: float = 1.0,
        class_balance_power: float = 0.50,
    ) -> XAUUSDModelTrainingResult:

        self._validate_context(
            context
        )

        snapshot = (
            self.discover_training_snapshot(
                context=context,
                training_contract_version=(
                    training_contract_version
                ),
            )
        )

        frame = (
            self.load_training_frame(
                context=context,
                snapshot=snapshot,
            )
        )

        features = list(
            snapshot.feature_columns
        )

        feature_hash = (
            self._canonical_hash(
                features
            )
        )

        split_frames = {
            split: (
                frame[
                    frame[
                        "dataset_split"
                    ]
                    ==
                    split
                ]
                .reset_index(
                    drop=True
                )
            )
            for split
            in (
                "TRAIN",
                "VALIDATION",
                "TEST",
            )
        }

        train = split_frames[
            "TRAIN"
        ]

        validation = split_frames[
            "VALIDATION"
        ]

        test = split_frames[
            "TEST"
        ]

        if (
            train.empty
            or
            validation.empty
            or
            test.empty
        ):

            raise XAUUSDModelTrainingError(
                "EMPTY_REQUIRED_MODEL_SPLIT"
            )

        x_train_raw = (
            train[
                features
            ]
            .to_numpy(
                dtype=np.float64
            )
        )

        x_validation_raw = (
            validation[
                features
            ]
            .to_numpy(
                dtype=np.float64
            )
        )

        x_test_raw = (
            test[
                features
            ]
            .to_numpy(
                dtype=np.float64
            )
        )

        y_train = (
            train[
                "target_class_id"
            ]
            .to_numpy(
                dtype=np.int8
            )
        )

        y_validation = (
            validation[
                "target_class_id"
            ]
            .to_numpy(
                dtype=np.int8
            )
        )

        y_test = (
            test[
                "target_class_id"
            ]
            .to_numpy(
                dtype=np.int8
            )
        )

        if set(
            int(
                value
            )
            for value
            in np.unique(
                y_train
            )
        ) != set(
            CLASS_IDS
        ):

            raise XAUUSDModelTrainingError(
                "TRAIN_SPLIT_DOES_NOT_CONTAIN_ALL_CLASSES"
            )

        # =====================================================================
        # TRAIN-only scaler fit
        # =====================================================================

        scaler = StandardScaler(
            copy=True,
            with_mean=True,
            with_std=True,
        )

        x_train = (
            scaler.fit_transform(
                x_train_raw
            )
        )

        x_validation = (
            scaler.transform(
                x_validation_raw
            )
        )

        x_test = (
            scaler.transform(
                x_test_raw
            )
        )

        if not np.isfinite(
            x_train
        ).all():

            raise XAUUSDModelTrainingError(
                "NONFINITE_SCALED_TRAIN_DATA"
            )

        # =====================================================================
        # Mild class balancing
        # =====================================================================

        (
            sample_weights,
            class_weights,
        ) = self._sample_weights(
            y_train,
            balance_power=(
                class_balance_power
            ),
        )

        # =====================================================================
        # Model fit — TRAIN only
        # =====================================================================

        model_parameters = {
            "learning_rate": float(
                learning_rate
            ),
            "max_iter": int(
                max_iter
            ),
            "max_leaf_nodes": int(
                max_leaf_nodes
            ),
            "min_samples_leaf": int(
                min_samples_leaf
            ),
            "l2_regularization": float(
                l2_regularization
            ),
            "early_stopping": False,
            "random_state": int(
                random_state
            ),
        }

        model = (
            HistGradientBoostingClassifier(
                **model_parameters
            )
        )

        model.fit(
            x_train,
            y_train,
            sample_weight=(
                sample_weights
            ),
        )

        if tuple(
            int(
                value
            )
            for value
            in model.classes_
        ) != CLASS_IDS:

            raise XAUUSDModelTrainingError(
                "TRAINED_MODEL_CLASS_CONTRACT_MISMATCH"
            )

        # =====================================================================
        # Evaluation
        # =====================================================================

        train_metrics = (
            self._evaluate(
                model=model,
                x=x_train,
                y=y_train,
            )
        )

        validation_metrics = (
            self._evaluate(
                model=model,
                x=x_validation,
                y=y_validation,
            )
        )

        test_metrics = (
            self._evaluate(
                model=model,
                x=x_test,
                y=y_test,
            )
        )

        learning_fingerprint = (
            TrainingMatrixBuilder
            .learning_scope_fingerprint(
                context
            )
        )

        training_contract = {
            "trainer_version": (
                self.VERSION
            ),
            "model_id": (
                self.MODEL_ID
            ),
            "algorithm": (
                self.ALGORITHM
            ),
            "training_dataset_id": (
                snapshot.dataset_id
            ),
            "training_dataset_sha256": (
                snapshot.dataset_sha256
            ),
            "training_manifest_sha256": (
                snapshot.manifest_sha256
            ),
            "training_contract_version": (
                snapshot.training_contract_version
            ),
            "base_timeframe": (
                snapshot.base_timeframe
            ),
            "feature_count": (
                len(
                    features
                )
            ),
            "feature_columns_sha256": (
                feature_hash
            ),
            "model_parameters": (
                model_parameters
            ),
            "class_balance_power": float(
                class_balance_power
            ),
            "class_weights": (
                class_weights
            ),
            "class_mapping": {
                "SHORT": -1,
                "NO_TRADE": 0,
                "LONG": 1,
            },
            "learning_scope_fingerprint": (
                learning_fingerprint
            ),
            "python_version": (
                platform.python_version()
            ),
            "numpy_version": (
                np.__version__
            ),
            "pandas_version": (
                pd.__version__
            ),
            "sklearn_version": (
                sklearn.__version__
            ),
        }

        training_contract_fingerprint = (
            self._canonical_hash(
                training_contract
            )
        )

        canonical_symbol = (
            self._safe_token(
                context.canonical_symbol,
                "canonical_symbol",
            )
        )

        model_id_safe = (
            self._safe_token(
                self.MODEL_ID,
                "model_id",
            )
        )

        output_directory = (
            self.canonical_root
            /
            "Instruments"
            /
            canonical_symbol
            /
            "learning"
            /
            (
                "scope_"
                +
                learning_fingerprint
            )
            /
            "models"
            /
            model_id_safe
            /
            (
                "build_"
                +
                training_contract_fingerprint[
                    :16
                ]
            )
        )

        # =====================================================================
        # Persist scaler + model
        # =====================================================================

        (
            scaler_path,
            scaler_hash,
        ) = self._dump_joblib_content_addressed(
            value=scaler,
            directory=output_directory,
            stem=(
                model_id_safe
                +
                "_scaler"
            ),
        )

        (
            model_path,
            model_hash,
        ) = self._dump_joblib_content_addressed(
            value=model,
            directory=output_directory,
            stem=model_id_safe,
        )

        # =====================================================================
        # Bundle manifest
        # =====================================================================

        manifest = {
            "manifest_version": (
                "PULSEVIPER_MODEL_MANIFEST_V1"
            ),
            "model_id": (
                self.MODEL_ID
            ),
            "trainer_version": (
                self.VERSION
            ),
            "algorithm": (
                self.ALGORITHM
            ),
            "canonical_symbol": (
                context.canonical_symbol
            ),
            "asset_class": (
                context.asset_class
            ),
            "broker_id": (
                context.broker_id
            ),
            "broker_symbol": (
                context.broker_symbol
            ),
            "contract_spec_id": (
                context.contract_spec_id
            ),
            "data_schema_version": (
                context.data_schema_version
            ),
            "feature_contract_version": (
                context.feature_contract_version
            ),
            "learning_scope_fingerprint": (
                learning_fingerprint
            ),
            "model_training_contract": (
                training_contract
            ),
            "model_training_contract_fingerprint": (
                training_contract_fingerprint
            ),
            "training_dataset": {
                "dataset_id": (
                    snapshot.dataset_id
                ),
                "dataset_sha256": (
                    snapshot.dataset_sha256
                ),
                "manifest_sha256": (
                    snapshot.manifest_sha256
                ),
                "training_contract_version": (
                    snapshot.training_contract_version
                ),
                "base_timeframe": (
                    snapshot.base_timeframe
                ),
            },
            "feature_columns": (
                features
            ),
            "feature_columns_sha256": (
                feature_hash
            ),
            "class_ids": [
                -1,
                0,
                1,
            ],
            "class_names": [
                "SHORT",
                "NO_TRADE",
                "LONG",
            ],
            "probability_order": [
                "SHORT",
                "NO_TRADE",
                "LONG",
            ],
            "scaler": {
                "type": (
                    "StandardScaler"
                ),
                "fit_scope": (
                    "TRAIN_ONLY"
                ),
                "filename": (
                    scaler_path.name
                ),
                "sha256": (
                    scaler_hash
                ),
            },
            "model": {
                "filename": (
                    model_path.name
                ),
                "sha256": (
                    model_hash
                ),
            },
            "split_rows": {
                "TRAIN": int(
                    len(
                        train
                    )
                ),
                "VALIDATION": int(
                    len(
                        validation
                    )
                ),
                "TEST": int(
                    len(
                        test
                    )
                ),
            },
            "metrics": {
                "TRAIN": (
                    train_metrics
                ),
                "VALIDATION": (
                    validation_metrics
                ),
                "TEST": (
                    test_metrics
                ),
            },
            "prediction_contract": {
                "outputs": [
                    "prob_short",
                    "prob_no_trade",
                    "prob_long",
                    "predicted_class",
                    "confidence",
                    "uncertainty",
                ],
                "confidence": (
                    "MAX_CLASS_PROBABILITY"
                ),
                "uncertainty": (
                    "NORMALIZED_PREDICTIVE_ENTROPY_0_TO_1"
                ),
                "low_confidence_policy": (
                    "DOWNSTREAM_DECISION_LAYER_MAY_FORCE_NO_TRADE"
                ),
            },
            "live_authorized": False,
        }

        manifest_bytes = (
            self._canonical_json_bytes(
                manifest
            )
        )

        manifest_hash = (
            self._sha256_bytes(
                manifest_bytes
            )
        )

        manifest_path = (
            output_directory
            /
            (
                model_id_safe
                +
                "_"
                +
                training_contract_fingerprint[
                    :12
                ]
                +
                "_"
                +
                model_hash[
                    :12
                ]
                +
                ".manifest.json"
            )
        )

        self._write_immutable(
            path=manifest_path,
            payload=manifest_bytes,
        )

        return XAUUSDModelTrainingResult(
            model_id=self.MODEL_ID,
            model_path=model_path,
            scaler_path=scaler_path,
            manifest_path=manifest_path,
            model_sha256=model_hash,
            scaler_sha256=scaler_hash,
            manifest_sha256=(
                manifest_hash
            ),
            training_dataset_id=(
                snapshot.dataset_id
            ),
            training_dataset_sha256=(
                snapshot.dataset_sha256
            ),
            feature_count=len(
                features
            ),
            train_rows=len(
                train
            ),
            validation_rows=len(
                validation
            ),
            test_rows=len(
                test
            ),
            validation_metrics=(
                validation_metrics
            ),
            test_metrics=(
                test_metrics
            ),
            learning_scope_fingerprint=(
                learning_fingerprint
            ),
            model_training_contract_fingerprint=(
                training_contract_fingerprint
            ),
            live_authorized=False,
        )