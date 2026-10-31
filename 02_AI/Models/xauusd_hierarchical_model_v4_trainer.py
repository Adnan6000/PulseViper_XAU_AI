"""
===============================================================================
PulseViper XAU AI
XAUUSD Hierarchical Model V4 Trainer
===============================================================================

Research architecture
---------------------
Stage A:
    NO_TRADE (0) vs TRADEABLE (1)

Stage B:
    SHORT (-1) vs LONG (1)

Stage B scaler and model are fitted only on true-tradeable TRAIN rows.

Final probability contract
--------------------------
P(SHORT)    = P(TRADEABLE) * P(SHORT | TRADEABLE)
P(NO_TRADE) = 1 - P(TRADEABLE)
P(LONG)     = P(TRADEABLE) * P(LONG | TRADEABLE)

Safety
------
Research-only.
No MT5 execution.
No RiskEngine modification.
No trade_ready modification.
No live authorization.
"""

from __future__ import annotations

import importlib
import json
import math
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
import sklearn

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler


# =============================================================================
# Base contracts
# =============================================================================

base_module: Any = importlib.import_module(
    "02_AI.Models.xauusd_model_trainer"
)

training_matrix_module: Any = importlib.import_module(
    "02_AI.Dataset.training_matrix_builder"
)

XAUUSDModelTrainer: Any = (
    base_module.XAUUSDModelTrainer
)

XAUUSDModelTrainingError: Any = (
    base_module.XAUUSDModelTrainingError
)

TrainingSnapshot: Any = (
    base_module.TrainingSnapshot
)

TrainingMatrixBuilder: Any = (
    training_matrix_module.TrainingMatrixBuilder
)

XAUUSDHierarchicalModelV4TrainingError: Any = (
    XAUUSDModelTrainingError
)


# =============================================================================
# Class contracts
# =============================================================================

FINAL_CLASS_IDS: tuple[int, int, int] = (
    -1,
    0,
    1,
)

FINAL_CLASS_NAMES: dict[int, str] = {
    -1: "SHORT",
    0: "NO_TRADE",
    1: "LONG",
}

STAGE_A_CLASS_IDS: tuple[int, int] = (
    0,
    1,
)

STAGE_A_CLASS_NAMES: dict[int, str] = {
    0: "NO_TRADE",
    1: "TRADEABLE",
}

STAGE_B_CLASS_IDS: tuple[int, int] = (
    -1,
    1,
)

STAGE_B_CLASS_NAMES: dict[int, str] = {
    -1: "SHORT",
    1: "LONG",
}

STAGE_A_METRICS_KEY = (
    "stage_a_tradeability"
)

STAGE_B_METRICS_KEY = (
    "stage_b_direction"
)

COMBINED_METRICS_KEY = (
    "combined"
)


# =============================================================================
# Result
# =============================================================================

@dataclass(frozen=True)
class XAUUSDHierarchicalModelV4TrainingResult:

    model_id: str

    stage_a_model_path: Path
    stage_a_scaler_path: Path

    stage_b_model_path: Path
    stage_b_scaler_path: Path

    manifest_path: Path

    output_directory: Path

    stage_a_model_sha256: str
    stage_a_scaler_sha256: str

    stage_b_model_sha256: str
    stage_b_scaler_sha256: str

    manifest_sha256: str

    training_dataset_id: str
    training_dataset_sha256: str
    training_manifest_sha256: str

    feature_count: int

    train_rows: int
    validation_rows: int
    test_rows: int

    train_tradeable_rows: int
    validation_tradeable_rows: int
    test_tradeable_rows: int

    train_metrics: dict[str, Any]
    validation_metrics: dict[str, Any]
    test_metrics: dict[str, Any]

    learning_scope_fingerprint: str

    model_training_contract_fingerprint: str

    live_authorized: bool = False

    @property
    def model_path(
        self,
    ) -> Path:

        return (
            self.stage_a_model_path
        )

    @property
    def scaler_path(
        self,
    ) -> Path:

        return (
            self.stage_a_scaler_path
        )

    @property
    def model_sha256(
        self,
    ) -> str:

        return (
            self.stage_a_model_sha256
        )

    @property
    def scaler_sha256(
        self,
    ) -> str:

        return (
            self.stage_a_scaler_sha256
        )

    @property
    def stage_b_train_rows(
        self,
    ) -> int:

        return (
            self.train_tradeable_rows
        )

    @property
    def stage_b_fit_rows(
        self,
    ) -> int:

        return (
            self.train_tradeable_rows
        )

    @property
    def tradeable_rows(
        self,
    ) -> dict[str, int]:

        return {
            "TRAIN": (
                self.train_tradeable_rows
            ),
            "VALIDATION": (
                self.validation_tradeable_rows
            ),
            "TEST": (
                self.test_tradeable_rows
            ),
        }

    @property
    def split_metrics(
        self,
    ) -> dict[
        str,
        dict[str, Any],
    ]:

        return {
            "TRAIN": (
                self.train_metrics
            ),
            "VALIDATION": (
                self.validation_metrics
            ),
            "TEST": (
                self.test_metrics
            ),
        }

    @property
    def metrics(
        self,
    ) -> dict[
        str,
        dict[str, Any],
    ]:

        return (
            self.split_metrics
        )


# =============================================================================
# Trainer
# =============================================================================

class XAUUSDHierarchicalModelV4Trainer(
    XAUUSDModelTrainer
):

    VERSION = "4.0"

    MODEL_ID = (
        "XAUUSD_MODEL_v4_HIERARCHICAL"
    )

    ALGORITHM = (
        "SKLEARN_HIST_GRADIENT_BOOSTING_HIERARCHICAL"
    )

    MANIFEST_VERSION = (
        "PULSEVIPER_HIERARCHICAL_MODEL_MANIFEST_V1"
    )

    TRAINING_CONTRACT_VERSION = (
        "XAUUSD_MTF_TRAINING_V3"
    )

    SOURCE_TARGET_TRAINING_CONTRACT = (
        "XAUUSD_MTF_TRAINING_V2"
    )

    TARGET_LABEL_CONTRACT = (
        "CLEAN_DIRECTIONAL_EXCURSION_V2"
    )

    TARGET_PROFIT_ATR = 1.25

    TARGET_MAX_ADVERSE_ATR = 0.75

    STORAGE_SLUG = "v4h"

    STAGE_A_SCALER_STEM = "sa_s"
    STAGE_A_MODEL_STEM = "sa_m"

    STAGE_B_SCALER_STEM = "sb_s"
    STAGE_B_MODEL_STEM = "sb_m"

    # =========================================================================
    # Validation helpers
    # =========================================================================

    @staticmethod
    def _require_mapping(
        value: Any,
        error_code: str,
    ) -> Mapping[str, Any]:

        if not isinstance(
            value,
            Mapping,
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    error_code
                )
            )

        return value

    @staticmethod
    def _require_finite_number(
        value: Any,
        error_code: str,
    ) -> float:

        try:

            result = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    error_code
                )
            ) from exc

        if not math.isfinite(
            result
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    error_code
                )
            )

        return result

    @classmethod
    def _require_exact_float(
        cls,
        value: Any,
        expected: float,
        error_code: str,
    ) -> None:

        actual = (
            cls._require_finite_number(
                value,
                error_code,
            )
        )

        if not math.isclose(
            actual,
            expected,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    error_code
                )
            )

    @staticmethod
    def _validate_hyperparameters(
        *,
        max_iter: int,
        learning_rate: float,
        max_leaf_nodes: int,
        min_samples_leaf: int,
        l2_regularization: float,
    ) -> None:

        if int(
            max_iter
        ) <= 0:

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "INVALID_MAX_ITER"
                )
            )

        if (
            not math.isfinite(
                float(
                    learning_rate
                )
            )
            or
            float(
                learning_rate
            )
            <=
            0.0
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "INVALID_LEARNING_RATE"
                )
            )

        if int(
            max_leaf_nodes
        ) < 2:

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "INVALID_MAX_LEAF_NODES"
                )
            )

        if int(
            min_samples_leaf
        ) <= 0:

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "INVALID_MIN_SAMPLES_LEAF"
                )
            )

        if (
            not math.isfinite(
                float(
                    l2_regularization
                )
            )
            or
            float(
                l2_regularization
            )
            <
            0.0
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "INVALID_L2_REGULARIZATION"
                )
            )

    # =========================================================================
    # Frozen V3 -> V2 target lineage
    # =========================================================================

    def _load_and_validate_v3_manifest(
        self,
        *,
        snapshot: TrainingSnapshot,
    ) -> dict[str, Any]:

        try:

            manifest = json.loads(
                snapshot.manifest_path.read_text(
                    encoding="utf-8"
                )
            )

        except Exception as exc:

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "INVALID_V3_TRAINING_MANIFEST"
                )
            ) from exc

        if not isinstance(
            manifest,
            dict,
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "INVALID_V3_TRAINING_MANIFEST"
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
            self.TRAINING_CONTRACT_VERSION
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "V4_TRAINING_CONTRACT_MISMATCH"
                )
            )

        if bool(
            manifest.get(
                "live_authorized",
                False,
            )
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "LIVE_AUTHORIZED_V3_MANIFEST_REJECTED"
                )
            )

        source = (
            self._require_mapping(
                manifest.get(
                    "source_training_matrix"
                ),
                "V3_SOURCE_TRAINING_MATRIX_MISSING",
            )
        )

        if (
            str(
                source.get(
                    "training_contract_version",
                    "",
                )
            )
            !=
            self.SOURCE_TARGET_TRAINING_CONTRACT
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "V3_SOURCE_TARGET_CONTRACT_MISMATCH"
                )
            )

        target_contract = (
            self._require_mapping(
                manifest.get(
                    "target_label_contract"
                ),
                "V3_TARGET_LABEL_CONTRACT_MISSING",
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
            self.TARGET_LABEL_CONTRACT
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "V3_TARGET_LABEL_CONTRACT_MISMATCH"
                )
            )

        self._require_exact_float(
            target_contract.get(
                "profit_atr"
            ),
            self.TARGET_PROFIT_ATR,
            "V3_TARGET_PROFIT_ATR_MISMATCH",
        )

        self._require_exact_float(
            target_contract.get(
                "max_adverse_atr"
            ),
            self.TARGET_MAX_ADVERSE_ATR,
            "V3_TARGET_MAX_ADVERSE_ATR_MISMATCH",
        )

        class_mapping = (
            self._require_mapping(
                manifest.get(
                    "target_class_mapping"
                ),
                "V3_TARGET_CLASS_MAPPING_MISSING",
            )
        )

        try:

            normalized_mapping = {
                str(
                    key
                ): int(
                    value
                )
                for (
                    key,
                    value,
                )
                in class_mapping.items()
            }

        except Exception as exc:

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "V3_TARGET_CLASS_MAPPING_MISMATCH"
                )
            ) from exc

        if normalized_mapping != {
            "SHORT": -1,
            "NO_TRADE": 0,
            "LONG": 1,
        }:

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "V3_TARGET_CLASS_MAPPING_MISMATCH"
                )
            )

        target_columns = (
            manifest.get(
                "target_columns",
                [],
            )
        )

        if not isinstance(
            target_columns,
            list,
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "V3_TARGET_COLUMNS_INVALID"
                )
            )

        required_target_columns = {
            "target_class",
            "target_class_id",
            "target_tradeable",
            "target_profit_atr",
            "target_max_adverse_atr",
        }

        if not (
            required_target_columns
            .issubset(
                {
                    str(
                        value
                    )
                    for value
                    in target_columns
                }
            )
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "V3_REQUIRED_TARGET_COLUMNS_MISSING"
                )
            )

        return manifest

    def _validate_frozen_target_frame(
        self,
        frame: pd.DataFrame,
    ) -> None:

        required = {
            "target_class_id",
            "target_tradeable",
            "target_profit_atr",
            "target_max_adverse_atr",
        }

        missing = sorted(
            required
            -
            set(
                frame.columns
            )
        )

        if missing:

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    (
                        "V4_REQUIRED_TARGET_COLUMNS_MISSING: "
                        +
                        ", ".join(
                            missing
                        )
                    )
                )
            )

        target_ids = pd.to_numeric(
            frame[
                "target_class_id"
            ],
            errors="coerce",
        ).to_numpy(
            dtype=np.float64
        )

        tradeable = pd.to_numeric(
            frame[
                "target_tradeable"
            ],
            errors="coerce",
        ).to_numpy(
            dtype=np.float64
        )

        profit = pd.to_numeric(
            frame[
                "target_profit_atr"
            ],
            errors="coerce",
        ).to_numpy(
            dtype=np.float64
        )

        adverse = pd.to_numeric(
            frame[
                "target_max_adverse_atr"
            ],
            errors="coerce",
        ).to_numpy(
            dtype=np.float64
        )

        if not np.isfinite(
            target_ids
        ).all():

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "NONFINITE_TARGET_CLASS_ID"
                )
            )

        if not np.isfinite(
            tradeable
        ).all():

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "NONFINITE_TARGET_TRADEABLE"
                )
            )

        if not np.isfinite(
            profit
        ).all():

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "NONFINITE_TARGET_PROFIT_ATR"
                )
            )

        if not np.isfinite(
            adverse
        ).all():

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "NONFINITE_TARGET_MAX_ADVERSE_ATR"
                )
            )

        if not np.isin(
            target_ids,
            np.asarray(
                FINAL_CLASS_IDS,
                dtype=np.float64,
            ),
        ).all():

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "INVALID_TARGET_CLASS_ID"
                )
            )

        if not np.isin(
            tradeable,
            np.asarray(
                (
                    0.0,
                    1.0,
                ),
                dtype=np.float64,
            ),
        ).all():

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "INVALID_TARGET_TRADEABLE"
                )
            )

        expected_tradeable = (
            (
                target_ids
                !=
                0.0
            )
            .astype(
                np.float64
            )
        )

        if not np.array_equal(
            expected_tradeable,
            tradeable,
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "TARGET_TRADEABLE_LINKAGE_MISMATCH"
                )
            )

        if not np.allclose(
            profit,
            self.TARGET_PROFIT_ATR,
            rtol=0.0,
            atol=1e-12,
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "TARGET_PROFIT_ATR_MISMATCH"
                )
            )

        if not np.allclose(
            adverse,
            self.TARGET_MAX_ADVERSE_ATR,
            rtol=0.0,
            atol=1e-12,
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "TARGET_MAX_ADVERSE_ATR_MISMATCH"
                )
            )

    # =========================================================================
    # Class balancing
    # =========================================================================

    @staticmethod
    def _binary_sample_weights(
        y: np.ndarray,
        *,
        class_ids: Sequence[int],
        class_names: Mapping[int, str],
        balance_power: float,
    ) -> tuple[
        np.ndarray,
        dict[str, float],
    ]:

        power = float(
            balance_power
        )

        if (
            not math.isfinite(
                power
            )
            or
            power
            <
            0.0
            or
            power
            >
            1.0
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "INVALID_CLASS_BALANCE_POWER"
                )
            )

        ids = tuple(
            int(
                value
            )
            for value
            in class_ids
        )

        if (
            len(
                ids
            )
            !=
            2
            or
            len(
                set(
                    ids
                )
            )
            !=
            2
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "INVALID_BINARY_CLASS_CONTRACT"
                )
            )

        counts = {
            class_id: int(
                np.sum(
                    y
                    ==
                    class_id
                )
            )
            for class_id
            in ids
        }

        if any(
            value
            <=
            0
            for value
            in counts.values()
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    (
                        "TRAIN_SPLIT_MISSING_BINARY_CLASS: "
                        f"{counts}"
                    )
                )
            )

        total = int(
            len(
                y
            )
        )

        raw = {
            class_id: (
                total
                /
                (
                    2.0
                    *
                    count
                )
            )
            **
            power
            for (
                class_id,
                count,
            )
            in counts.items()
        }

        weights = np.asarray(
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
                weights
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

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "INVALID_SAMPLE_WEIGHTS"
                )
            )

        weights = (
            weights
            /
            mean_weight
        )

        normalized = {
            str(
                class_names[
                    class_id
                ]
            ): float(
                raw[
                    class_id
                ]
                /
                mean_weight
            )
            for class_id
            in ids
        }

        return (
            weights,
            normalized,
        )

    # =========================================================================
    # Probability contract
    # =========================================================================

    @staticmethod
    def _validate_probability_matrix(
        probabilities: np.ndarray,
        *,
        columns: int,
        error_prefix: str,
    ) -> np.ndarray:

        matrix = np.asarray(
            probabilities,
            dtype=np.float64,
        )

        if (
            matrix.ndim
            !=
            2
            or
            matrix.shape[
                1
            ]
            !=
            columns
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    (
                        f"{error_prefix}"
                        "_SHAPE_MISMATCH"
                    )
                )
            )

        if not np.isfinite(
            matrix
        ).all():

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    (
                        f"{error_prefix}"
                        "_NONFINITE"
                    )
                )
            )

        if (
            bool(
                np.any(
                    matrix
                    <
                    -1e-12
                )
            )
            or
            bool(
                np.any(
                    matrix
                    >
                    1.0
                    +
                    1e-12
                )
            )
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    (
                        f"{error_prefix}"
                        "_OUT_OF_RANGE"
                    )
                )
            )

        if not np.allclose(
            np.sum(
                matrix,
                axis=1,
            ),
            1.0,
            rtol=0.0,
            atol=1e-9,
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    (
                        f"{error_prefix}"
                        "_ROW_SUM_MISMATCH"
                    )
                )
            )

        return np.clip(
            matrix,
            0.0,
            1.0,
        )

    @classmethod
    def combine_probabilities(
        cls,
        *,
        stage_a_probabilities: np.ndarray,
        stage_b_probabilities: np.ndarray,
    ) -> np.ndarray:

        stage_a = (
            cls._validate_probability_matrix(
                stage_a_probabilities,
                columns=2,
                error_prefix=(
                    "STAGE_A_PROBABILITIES"
                ),
            )
        )

        stage_b = (
            cls._validate_probability_matrix(
                stage_b_probabilities,
                columns=2,
                error_prefix=(
                    "STAGE_B_PROBABILITIES"
                ),
            )
        )

        if (
            stage_a.shape[
                0
            ]
            !=
            stage_b.shape[
                0
            ]
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "HIERARCHICAL_PROBABILITY_ROW_MISMATCH"
                )
            )

        p_tradeable = (
            stage_a[
                :,
                1,
            ]
        )

        p_short = (
            p_tradeable
            *
            stage_b[
                :,
                0,
            ]
        )

        p_no_trade = (
            1.0
            -
            p_tradeable
        )

        p_long = (
            p_tradeable
            *
            stage_b[
                :,
                1,
            ]
        )

        combined = (
            np.column_stack(
                (
                    p_short,
                    p_no_trade,
                    p_long,
                )
            )
        )

        return (
            cls._validate_probability_matrix(
                combined,
                columns=3,
                error_prefix=(
                    "COMBINED_PROBABILITIES"
                ),
            )
        )

    @classmethod
    def _combine_probabilities(
        cls,
        *,
        stage_a_probabilities: np.ndarray,
        stage_b_probabilities: np.ndarray,
    ) -> np.ndarray:

        return (
            cls.combine_probabilities(
                stage_a_probabilities=(
                    stage_a_probabilities
                ),
                stage_b_probabilities=(
                    stage_b_probabilities
                ),
            )
        )

    # =========================================================================
    # Metrics
    # =========================================================================

    @staticmethod
    def _predict_from_probabilities(
        probabilities: np.ndarray,
        class_ids: Sequence[int],
    ) -> np.ndarray:

        ids = np.asarray(
            tuple(
                int(
                    value
                )
                for value
                in class_ids
            ),
            dtype=np.int8,
        )

        return ids[
            np.argmax(
                probabilities,
                axis=1,
            )
        ]

    @staticmethod
    def _safe_auc(
        *,
        binary_truth: np.ndarray,
        probability: np.ndarray,
    ) -> tuple[
        float | None,
        float | None,
    ]:

        if (
            len(
                np.unique(
                    binary_truth
                )
            )
            !=
            2
        ):

            return (
                None,
                None,
            )

        return (
            float(
                roc_auc_score(
                    binary_truth,
                    probability,
                )
            ),
            float(
                average_precision_score(
                    binary_truth,
                    probability,
                )
            ),
        )

    @staticmethod
    def _binary_probability_ece(
        *,
        y_true: np.ndarray,
        positive_probability: np.ndarray,
        positive_class: int,
        bins: int = 10,
    ) -> float:

        y = np.asarray(
            y_true
        )

        probability = np.asarray(
            positive_probability,
            dtype=np.float64,
        )

        truth = (
            (
                y
                ==
                int(
                    positive_class
                )
            )
            .astype(
                np.float64
            )
        )

        edges = np.linspace(
            0.0,
            1.0,
            int(
                bins
            )
            +
            1,
        )

        ece = 0.0

        for index in range(
            int(
                bins
            )
        ):

            low = (
                edges[
                    index
                ]
            )

            high = (
                edges[
                    index
                    +
                    1
                ]
            )

            if (
                index
                ==
                int(
                    bins
                )
                -
                1
            ):

                mask = (
                    (
                        probability
                        >=
                        low
                    )
                    &
                    (
                        probability
                        <=
                        high
                    )
                )

            else:

                mask = (
                    (
                        probability
                        >=
                        low
                    )
                    &
                    (
                        probability
                        <
                        high
                    )
                )

            rows = int(
                np.sum(
                    mask
                )
            )

            if rows == 0:
                continue

            observed_rate = float(
                np.mean(
                    truth[
                        mask
                    ]
                )
            )

            probability_mean = float(
                np.mean(
                    probability[
                        mask
                    ]
                )
            )

            ece += (
                rows
                /
                len(
                    y
                )
            ) * abs(
                observed_rate
                -
                probability_mean
            )

        return float(
            ece
        )

    @staticmethod
    def _selective_confidence(
        *,
        y_true: np.ndarray,
        predicted: np.ndarray,
        confidence: np.ndarray,
    ) -> dict[str, Any]:

        result: dict[
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

            rows = int(
                np.sum(
                    mask
                )
            )

            result[
                f"{threshold:.2f}"
            ] = {
                "coverage": (
                    float(
                        np.mean(
                            mask
                        )
                    )
                    if len(
                        mask
                    )
                    else
                    0.0
                ),
                "rows": (
                    rows
                ),
                "accuracy": (
                    float(
                        np.mean(
                            predicted[
                                mask
                            ]
                            ==
                            y_true[
                                mask
                            ]
                        )
                    )
                    if rows
                    else
                    None
                ),
            }

        return result

    @classmethod
    def _base_metrics(
        cls,
        *,
        y_true: np.ndarray,
        probabilities: np.ndarray,
        class_ids: Sequence[int],
        class_names: Mapping[int, str],
    ) -> tuple[
        dict[str, Any],
        np.ndarray,
    ]:

        ids = tuple(
            int(
                value
            )
            for value
            in class_ids
        )

        y = np.asarray(
            y_true,
            dtype=np.int8,
        )

        predicted = (
            cls._predict_from_probabilities(
                probabilities,
                ids,
            )
        )

        (
            precision,
            recall,
            f1,
            support,
        ) = (
            precision_recall_fscore_support(
                y,
                predicted,
                labels=list(
                    ids
                ),
                zero_division=0,
            )
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

        top_class_ece = (
            cls._expected_calibration_error(
                y_true=y,
                y_pred=predicted,
                confidence=confidence,
            )
        )

        per_class: dict[
            str,
            Any,
        ] = {}

        for (
            index,
            class_id,
        ) in enumerate(
            ids
        ):

            binary_truth = (
                (
                    y
                    ==
                    class_id
                )
                .astype(
                    np.int8
                )
            )

            (
                roc_auc,
                pr_auc,
            ) = (
                cls._safe_auc(
                    binary_truth=(
                        binary_truth
                    ),
                    probability=(
                        probabilities[
                            :,
                            index,
                        ]
                    ),
                )
            )

            per_class[
                str(
                    class_names[
                        class_id
                    ]
                )
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
                            index,
                        ]
                    )
                ),
                "one_vs_rest_brier": float(
                    np.mean(
                        (
                            probabilities[
                                :,
                                index,
                            ]
                            -
                            binary_truth.astype(
                                np.float64
                            )
                        )
                        **
                        2
                    )
                ),
                "roc_auc": (
                    roc_auc
                ),
                "pr_auc": (
                    pr_auc
                ),
            }

        (
            values,
            counts,
        ) = np.unique(
            y,
            return_counts=True,
        )

        majority_class = int(
            values[
                int(
                    np.argmax(
                        counts
                    )
                )
            ]
        )

        selective = (
            cls._selective_confidence(
                y_true=y,
                predicted=predicted,
                confidence=confidence,
            )
        )

        metrics = {
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
                    labels=list(
                        ids
                    ),
                    average="macro",
                    zero_division=0,
                )
            ),
            "log_loss": float(
                log_loss(
                    y,
                    probabilities,
                    labels=list(
                        ids
                    ),
                )
            ),
            "top_class_ece": (
                top_class_ece
            ),
            "expected_calibration_error": (
                top_class_ece
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
            "prediction_distribution": {
                str(
                    class_names[
                        class_id
                    ]
                ): int(
                    np.sum(
                        predicted
                        ==
                        class_id
                    )
                )
                for class_id
                in ids
            },
            "per_class": (
                per_class
            ),
            "confusion_matrix": {
                "labels": [
                    str(
                        class_names[
                            class_id
                        ]
                    )
                    for class_id
                    in ids
                ],
                "rows": (
                    confusion_matrix(
                        y,
                        predicted,
                        labels=list(
                            ids
                        ),
                    )
                    .astype(
                        int
                    )
                    .tolist()
                ),
            },
            "selective_confidence": (
                selective
            ),
            "majority_baseline": {
                "class_id": (
                    majority_class
                ),
                "class_name": str(
                    class_names[
                        majority_class
                    ]
                ),
                "accuracy": float(
                    np.max(
                        counts
                    )
                    /
                    len(
                        y
                    )
                ),
            },
        }

        return (
            metrics,
            predicted,
        )

    @classmethod
    def _binary_metrics(
        cls,
        *,
        y_true: np.ndarray,
        probabilities: np.ndarray,
        class_ids: Sequence[int],
        class_names: Mapping[int, str],
        positive_class: int,
    ) -> dict[str, Any]:

        ids = tuple(
            int(
                value
            )
            for value
            in class_ids
        )

        matrix = (
            cls._validate_probability_matrix(
                probabilities,
                columns=2,
                error_prefix=(
                    "BINARY_EVALUATION_PROBABILITIES"
                ),
            )
        )

        y = np.asarray(
            y_true,
            dtype=np.int8,
        )

        (
            metrics,
            _,
        ) = cls._base_metrics(
            y_true=y,
            probabilities=matrix,
            class_ids=ids,
            class_names=class_names,
        )

        positive_index = (
            ids.index(
                int(
                    positive_class
                )
            )
        )

        positive_probability = (
            matrix[
                :,
                positive_index,
            ]
        )

        positive_truth = (
            (
                y
                ==
                int(
                    positive_class
                )
            )
            .astype(
                np.float64
            )
        )

        binary_brier = float(
            np.mean(
                (
                    positive_probability
                    -
                    positive_truth
                )
                **
                2
            )
        )

        binary_probability_ece = (
            cls._binary_probability_ece(
                y_true=y,
                positive_probability=(
                    positive_probability
                ),
                positive_class=(
                    positive_class
                ),
            )
        )

        metrics[
            "binary_brier"
        ] = (
            binary_brier
        )

        metrics[
            "brier_score"
        ] = (
            binary_brier
        )

        metrics[
            "binary_probability_ece"
        ] = (
            binary_probability_ece
        )

        metrics[
            "binary_expected_calibration_error"
        ] = (
            binary_probability_ece
        )

        return metrics

    @classmethod
    def _combined_metrics(
        cls,
        *,
        y_true: np.ndarray,
        probabilities: np.ndarray,
    ) -> dict[str, Any]:

        matrix = (
            cls._validate_probability_matrix(
                probabilities,
                columns=3,
                error_prefix=(
                    "COMBINED_EVALUATION_PROBABILITIES"
                ),
            )
        )

        y = np.asarray(
            y_true,
            dtype=np.int8,
        )

        (
            metrics,
            predicted,
        ) = cls._base_metrics(
            y_true=y,
            probabilities=matrix,
            class_ids=FINAL_CLASS_IDS,
            class_names=FINAL_CLASS_NAMES,
        )

        one_hot = np.column_stack(
            [
                (
                    y
                    ==
                    class_id
                )
                .astype(
                    np.float64
                )
                for class_id
                in FINAL_CLASS_IDS
            ]
        )

        multiclass_brier = float(
            np.mean(
                np.sum(
                    (
                        matrix
                        -
                        one_hot
                    )
                    **
                    2,
                    axis=1,
                )
            )
        )

        predicted_trade = (
            predicted
            !=
            0
        )

        true_tradeable = (
            y
            !=
            0
        )

        direction_mask = (
            predicted_trade
            &
            true_tradeable
        )

        predicted_trade_rows = int(
            np.sum(
                predicted_trade
            )
        )

        direction_rows = int(
            np.sum(
                direction_mask
            )
        )

        metrics[
            "multiclass_brier"
        ] = (
            multiclass_brier
        )

        metrics[
            "trade_selection"
        ] = {
            "predicted_trade_rows": (
                predicted_trade_rows
            ),
            "predicted_trade_coverage": float(
                np.mean(
                    predicted_trade
                )
            ),
            "true_tradeable_rows": int(
                np.sum(
                    true_tradeable
                )
            ),
            "true_tradeable_rate": float(
                np.mean(
                    true_tradeable
                )
            ),
            "tradeability_precision": (
                float(
                    np.mean(
                        true_tradeable[
                            predicted_trade
                        ]
                    )
                )
                if predicted_trade_rows
                else
                None
            ),
            "direction_evaluable_rows": (
                direction_rows
            ),
            "direction_accuracy_when_predicted_trade_is_tradeable": (
                float(
                    np.mean(
                        predicted[
                            direction_mask
                        ]
                        ==
                        y[
                            direction_mask
                        ]
                    )
                )
                if direction_rows
                else
                None
            ),
        }

        return metrics

    # =========================================================================
    # Model/split evaluation
    # =========================================================================

    @staticmethod
    def _require_model_classes(
        model: Any,
        expected: Sequence[int],
        error_code: str,
    ) -> None:

        actual = tuple(
            int(
                value
            )
            for value
            in model.classes_
        )

        expected_tuple = tuple(
            int(
                value
            )
            for value
            in expected
        )

        if (
            actual
            !=
            expected_tuple
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    (
                        f"{error_code}: "
                        f"{actual}"
                    )
                )
            )

    @classmethod
    def _evaluate_split(
        cls,
        *,
        stage_a_model: Any,
        stage_b_model: Any,
        x_stage_a: np.ndarray,
        x_stage_b: np.ndarray,
        y_final: np.ndarray,
    ) -> dict[str, Any]:

        y_final_array = np.asarray(
            y_final,
            dtype=np.int8,
        )

        tradeable_mask = (
            y_final_array
            !=
            0
        )

        if not bool(
            np.any(
                tradeable_mask
            )
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "SPLIT_HAS_NO_TRADEABLE_ROWS"
                )
            )

        stage_a_probabilities = np.asarray(
            stage_a_model.predict_proba(
                x_stage_a
            ),
            dtype=np.float64,
        )

        stage_b_probabilities = np.asarray(
            stage_b_model.predict_proba(
                x_stage_b
            ),
            dtype=np.float64,
        )

        combined_probabilities = (
            cls.combine_probabilities(
                stage_a_probabilities=(
                    stage_a_probabilities
                ),
                stage_b_probabilities=(
                    stage_b_probabilities
                ),
            )
        )

        return {
            STAGE_A_METRICS_KEY: (
                cls._binary_metrics(
                    y_true=(
                        (
                            y_final_array
                            !=
                            0
                        )
                        .astype(
                            np.int8
                        )
                    ),
                    probabilities=(
                        stage_a_probabilities
                    ),
                    class_ids=(
                        STAGE_A_CLASS_IDS
                    ),
                    class_names=(
                        STAGE_A_CLASS_NAMES
                    ),
                    positive_class=1,
                )
            ),
            STAGE_B_METRICS_KEY: (
                cls._binary_metrics(
                    y_true=(
                        y_final_array[
                            tradeable_mask
                        ]
                    ),
                    probabilities=(
                        stage_b_probabilities[
                            tradeable_mask
                        ]
                    ),
                    class_ids=(
                        STAGE_B_CLASS_IDS
                    ),
                    class_names=(
                        STAGE_B_CLASS_NAMES
                    ),
                    positive_class=1,
                )
            ),
            COMBINED_METRICS_KEY: (
                cls._combined_metrics(
                    y_true=(
                        y_final_array
                    ),
                    probabilities=(
                        combined_probabilities
                    ),
                )
            ),
        }

    # =========================================================================
    # Training
    # =========================================================================

    def train(
        self,
        *,
        context: Any,
        training_contract_version: str = (
            TRAINING_CONTRACT_VERSION
        ),
        random_state: int = 42,
        max_iter: int = 300,
        learning_rate: float = 0.04,
        max_leaf_nodes: int = 31,
        min_samples_leaf: int = 50,
        l2_regularization: float = 1.5,
        stage_a_class_balance_power: float = 0.20,
        stage_b_class_balance_power: float = 0.20,
    ) -> XAUUSDHierarchicalModelV4TrainingResult:

        self._validate_context(
            context
        )

        if (
            str(
                training_contract_version
            )
            !=
            self.TRAINING_CONTRACT_VERSION
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "V4_REQUIRES_XAUUSD_MTF_TRAINING_V3"
                )
            )

        self._validate_hyperparameters(
            max_iter=(
                max_iter
            ),
            learning_rate=(
                learning_rate
            ),
            max_leaf_nodes=(
                max_leaf_nodes
            ),
            min_samples_leaf=(
                min_samples_leaf
            ),
            l2_regularization=(
                l2_regularization
            ),
        )

        snapshot = (
            self.discover_training_snapshot(
                context=context,
                training_contract_version=(
                    self.TRAINING_CONTRACT_VERSION
                ),
            )
        )

        source_manifest = (
            self._load_and_validate_v3_manifest(
                snapshot=(
                    snapshot
                )
            )
        )

        frame = (
            self.load_training_frame(
                context=context,
                snapshot=(
                    snapshot
                ),
            )
        )

        self._validate_frozen_target_frame(
            frame
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
                frame.loc[
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

        train = (
            split_frames[
                "TRAIN"
            ]
        )

        validation = (
            split_frames[
                "VALIDATION"
            ]
        )

        test = (
            split_frames[
                "TEST"
            ]
        )

        if (
            train.empty
            or
            validation.empty
            or
            test.empty
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "EMPTY_REQUIRED_MODEL_SPLIT"
                )
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

        for (
            split_name,
            target_values,
        ) in (
            (
                "TRAIN",
                y_train,
            ),
            (
                "VALIDATION",
                y_validation,
            ),
            (
                "TEST",
                y_test,
            ),
        ):

            if set(
                int(
                    value
                )
                for value
                in np.unique(
                    target_values
                )
            ) != set(
                FINAL_CLASS_IDS
            ):

                raise (
                    XAUUSDHierarchicalModelV4TrainingError(
                        (
                            f"{split_name}_"
                            "SPLIT_DOES_NOT_CONTAIN_ALL_CLASSES"
                        )
                    )
                )

        y_stage_a_train = (
            (
                y_train
                !=
                0
            )
            .astype(
                np.int8
            )
        )

        tradeable_train_mask = (
            y_train
            !=
            0
        )

        y_stage_b_train = (
            y_train[
                tradeable_train_mask
            ]
        )

        if set(
            int(
                value
            )
            for value
            in np.unique(
                y_stage_a_train
            )
        ) != set(
            STAGE_A_CLASS_IDS
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "STAGE_A_TRAIN_CLASS_CONTRACT_MISMATCH"
                )
            )

        if set(
            int(
                value
            )
            for value
            in np.unique(
                y_stage_b_train
            )
        ) != set(
            STAGE_B_CLASS_IDS
        ):

            raise (
                XAUUSDHierarchicalModelV4TrainingError(
                    "STAGE_B_TRAIN_CLASS_CONTRACT_MISMATCH"
                )
            )

        # ---------------------------------------------------------------------
        # Stage A scaler: ALL TRAIN rows only
        # ---------------------------------------------------------------------

        stage_a_scaler = (
            StandardScaler(
                copy=True,
                with_mean=True,
                with_std=True,
            )
        )

        x_stage_a_train = (
            stage_a_scaler.fit_transform(
                x_train_raw
            )
        )

        x_stage_a_validation = (
            stage_a_scaler.transform(
                x_validation_raw
            )
        )

        x_stage_a_test = (
            stage_a_scaler.transform(
                x_test_raw
            )
        )

        # ---------------------------------------------------------------------
        # Stage B scaler: true-tradeable TRAIN rows only
        # ---------------------------------------------------------------------

        stage_b_scaler = (
            StandardScaler(
                copy=True,
                with_mean=True,
                with_std=True,
            )
        )

        x_stage_b_tradeable_train = (
            stage_b_scaler.fit_transform(
                x_train_raw[
                    tradeable_train_mask
                ]
            )
        )

        x_stage_b_train_all = (
            stage_b_scaler.transform(
                x_train_raw
            )
        )

        x_stage_b_validation = (
            stage_b_scaler.transform(
                x_validation_raw
            )
        )

        x_stage_b_test = (
            stage_b_scaler.transform(
                x_test_raw
            )
        )

        for (
            name,
            values,
        ) in (
            (
                "STAGE_A_TRAIN",
                x_stage_a_train,
            ),
            (
                "STAGE_A_VALIDATION",
                x_stage_a_validation,
            ),
            (
                "STAGE_A_TEST",
                x_stage_a_test,
            ),
            (
                "STAGE_B_TRADEABLE_TRAIN",
                x_stage_b_tradeable_train,
            ),
            (
                "STAGE_B_TRAIN_ALL",
                x_stage_b_train_all,
            ),
            (
                "STAGE_B_VALIDATION",
                x_stage_b_validation,
            ),
            (
                "STAGE_B_TEST",
                x_stage_b_test,
            ),
        ):

            if not np.isfinite(
                values
            ).all():

                raise (
                    XAUUSDHierarchicalModelV4TrainingError(
                        (
                            "NONFINITE_SCALED_DATA: "
                            f"{name}"
                        )
                    )
                )

        (
            stage_a_sample_weights,
            stage_a_class_weights,
        ) = (
            self._binary_sample_weights(
                y_stage_a_train,
                class_ids=(
                    STAGE_A_CLASS_IDS
                ),
                class_names=(
                    STAGE_A_CLASS_NAMES
                ),
                balance_power=(
                    stage_a_class_balance_power
                ),
            )
        )

        (
            stage_b_sample_weights,
            stage_b_class_weights,
        ) = (
            self._binary_sample_weights(
                y_stage_b_train,
                class_ids=(
                    STAGE_B_CLASS_IDS
                ),
                class_names=(
                    STAGE_B_CLASS_NAMES
                ),
                balance_power=(
                    stage_b_class_balance_power
                ),
            )
        )

        common_model_parameters = {
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
        }

        stage_a_model_parameters = {
            **common_model_parameters,
            "random_state": int(
                random_state
            ),
        }

        stage_b_model_parameters = {
            **common_model_parameters,
            "random_state": (
                int(
                    random_state
                )
                +
                1
            ),
        }

        stage_a_model = (
            HistGradientBoostingClassifier(
                **stage_a_model_parameters
            )
        )

        stage_a_model.fit(
            x_stage_a_train,
            y_stage_a_train,
            sample_weight=(
                stage_a_sample_weights
            ),
        )

        self._require_model_classes(
            stage_a_model,
            STAGE_A_CLASS_IDS,
            "STAGE_A_MODEL_CLASS_ORDER_MISMATCH",
        )

        stage_b_model = (
            HistGradientBoostingClassifier(
                **stage_b_model_parameters
            )
        )

        stage_b_model.fit(
            x_stage_b_tradeable_train,
            y_stage_b_train,
            sample_weight=(
                stage_b_sample_weights
            ),
        )

        self._require_model_classes(
            stage_b_model,
            STAGE_B_CLASS_IDS,
            "STAGE_B_MODEL_CLASS_ORDER_MISMATCH",
        )

        # =====================================================================
        # NO FITTING BELOW THIS LINE
        # =====================================================================

        train_metrics = (
            self._evaluate_split(
                stage_a_model=(
                    stage_a_model
                ),
                stage_b_model=(
                    stage_b_model
                ),
                x_stage_a=(
                    x_stage_a_train
                ),
                x_stage_b=(
                    x_stage_b_train_all
                ),
                y_final=(
                    y_train
                ),
            )
        )

        validation_metrics = (
            self._evaluate_split(
                stage_a_model=(
                    stage_a_model
                ),
                stage_b_model=(
                    stage_b_model
                ),
                x_stage_a=(
                    x_stage_a_validation
                ),
                x_stage_b=(
                    x_stage_b_validation
                ),
                y_final=(
                    y_validation
                ),
            )
        )

        test_metrics = (
            self._evaluate_split(
                stage_a_model=(
                    stage_a_model
                ),
                stage_b_model=(
                    stage_b_model
                ),
                x_stage_a=(
                    x_stage_a_test
                ),
                x_stage_b=(
                    x_stage_b_test
                ),
                y_final=(
                    y_test
                ),
            )
        )

        split_metrics = {
            "TRAIN": (
                train_metrics
            ),
            "VALIDATION": (
                validation_metrics
            ),
            "TEST": (
                test_metrics
            ),
        }

        train_tradeable_rows = int(
            np.sum(
                y_train
                !=
                0
            )
        )

        validation_tradeable_rows = int(
            np.sum(
                y_validation
                !=
                0
            )
        )

        test_tradeable_rows = int(
            np.sum(
                y_test
                !=
                0
            )
        )

        learning_fingerprint = (
            TrainingMatrixBuilder
            .learning_scope_fingerprint(
                context
            )
        )

        frozen_target_label_contract = {
            "name": (
                self.TARGET_LABEL_CONTRACT
            ),
            "profit_atr": (
                self.TARGET_PROFIT_ATR
            ),
            "max_adverse_atr": (
                self.TARGET_MAX_ADVERSE_ATR
            ),
        }

        target_contract = {
            **frozen_target_label_contract,
            "class_mapping": {
                "SHORT": -1,
                "NO_TRADE": 0,
                "LONG": 1,
            },
            "source_training_contract_version": (
                self.SOURCE_TARGET_TRAINING_CONTRACT
            ),
            "feature_training_contract_version": (
                self.TRAINING_CONTRACT_VERSION
            ),
        }

        final_probability_contract = {
            "probability_order": [
                "SHORT",
                "NO_TRADE",
                "LONG",
            ],
            "prob_short": (
                "P(TRADEABLE)*P(SHORT|TRADEABLE)"
            ),
            "prob_no_trade": (
                "1-P(TRADEABLE)"
            ),
            "prob_long": (
                "P(TRADEABLE)*P(LONG|TRADEABLE)"
            ),
        }

        research_policy = {
            "train_usage": (
                "FIT_ONLY"
            ),
            "validation_usage": (
                "EVALUATION_ONLY"
            ),
            "test_usage": (
                "FINAL_HOLDOUT_EVALUATION_ONLY"
            ),
            "threshold_selection": (
                "NONE_IN_THIS_TRAINER"
            ),
            "calibration_fit": (
                "NONE_IN_THIS_TRAINER"
            ),
            "calibration_metrics": (
                "DIAGNOSTIC_ONLY"
            ),
            "test_used_for_hyperparameter_tuning": False,
            "test_used_for_threshold_selection": False,
            "model_promotion_authorized": False,
            "execution_authorized": False,
        }

        model_training_contract = {
            "trainer_version": (
                self.VERSION
            ),
            "model_id": (
                self.MODEL_ID
            ),
            "algorithm": (
                self.ALGORITHM
            ),
            "architecture": (
                "HIERARCHICAL_TRADEABILITY_THEN_DIRECTION"
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
            "source_target_contract": (
                self.SOURCE_TARGET_TRAINING_CONTRACT
            ),
            "target_label_contract": (
                frozen_target_label_contract
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
            "target_contract": (
                target_contract
            ),
            "stage_a": {
                "task": (
                    "NO_TRADE_VS_TRADEABLE"
                ),
                "metric_key": (
                    STAGE_A_METRICS_KEY
                ),
                "class_ids": [
                    0,
                    1,
                ],
                "probability_order": [
                    "NO_TRADE",
                    "TRADEABLE",
                ],
                "fit_scope": (
                    "TRAIN_ONLY_ALL_ROWS"
                ),
                "scaler_fit_scope": (
                    "TRAIN_ONLY_ALL_ROWS"
                ),
                "class_balance_power": float(
                    stage_a_class_balance_power
                ),
                "class_weights": (
                    stage_a_class_weights
                ),
                "model_parameters": (
                    stage_a_model_parameters
                ),
            },
            "stage_b": {
                "task": (
                    "SHORT_VS_LONG_GIVEN_TRADEABLE"
                ),
                "metric_key": (
                    STAGE_B_METRICS_KEY
                ),
                "class_ids": [
                    -1,
                    1,
                ],
                "probability_order": [
                    "SHORT",
                    "LONG",
                ],
                "fit_scope": (
                    "TRAIN_ONLY_TRUE_TRADEABLE_ROWS"
                ),
                "scaler_fit_scope": (
                    "TRAIN_ONLY_TRUE_TRADEABLE_ROWS"
                ),
                "class_balance_power": float(
                    stage_b_class_balance_power
                ),
                "class_weights": (
                    stage_b_class_weights
                ),
                "model_parameters": (
                    stage_b_model_parameters
                ),
            },
            "final_probability_contract": (
                final_probability_contract
            ),
            "research_policy": (
                research_policy
            ),
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

        model_training_contract_fingerprint = (
            self._canonical_hash(
                model_training_contract
            )
        )

        canonical_symbol = (
            self._safe_token(
                context.canonical_symbol,
                "canonical_symbol",
            )
        )

        self._safe_token(
            self.MODEL_ID,
            "model_id",
        )

        storage_slug = (
            self._safe_token(
                self.STORAGE_SLUG,
                "model_storage_slug",
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
            storage_slug
            /
            (
                "b_"
                +
                model_training_contract_fingerprint[
                    :12
                ]
            )
        )

        (
            stage_a_scaler_path,
            stage_a_scaler_hash,
        ) = (
            self._dump_joblib_content_addressed(
                value=(
                    stage_a_scaler
                ),
                directory=(
                    output_directory
                ),
                stem=(
                    self.STAGE_A_SCALER_STEM
                ),
            )
        )

        (
            stage_a_model_path,
            stage_a_model_hash,
        ) = (
            self._dump_joblib_content_addressed(
                value=(
                    stage_a_model
                ),
                directory=(
                    output_directory
                ),
                stem=(
                    self.STAGE_A_MODEL_STEM
                ),
            )
        )

        (
            stage_b_scaler_path,
            stage_b_scaler_hash,
        ) = (
            self._dump_joblib_content_addressed(
                value=(
                    stage_b_scaler
                ),
                directory=(
                    output_directory
                ),
                stem=(
                    self.STAGE_B_SCALER_STEM
                ),
            )
        )

        (
            stage_b_model_path,
            stage_b_model_hash,
        ) = (
            self._dump_joblib_content_addressed(
                value=(
                    stage_b_model
                ),
                directory=(
                    output_directory
                ),
                stem=(
                    self.STAGE_B_MODEL_STEM
                ),
            )
        )

        artifacts = {
            "stage_a_scaler": {
                "type": (
                    "StandardScaler"
                ),
                "fit_scope": (
                    "TRAIN_ONLY_ALL_ROWS"
                ),
                "filename": (
                    stage_a_scaler_path.name
                ),
                "sha256": (
                    stage_a_scaler_hash
                ),
            },
            "stage_a_model": {
                "type": (
                    "HistGradientBoostingClassifier"
                ),
                "fit_scope": (
                    "TRAIN_ONLY_ALL_ROWS"
                ),
                "filename": (
                    stage_a_model_path.name
                ),
                "sha256": (
                    stage_a_model_hash
                ),
            },
            "stage_b_scaler": {
                "type": (
                    "StandardScaler"
                ),
                "fit_scope": (
                    "TRAIN_ONLY_TRUE_TRADEABLE_ROWS"
                ),
                "filename": (
                    stage_b_scaler_path.name
                ),
                "sha256": (
                    stage_b_scaler_hash
                ),
            },
            "stage_b_model": {
                "type": (
                    "HistGradientBoostingClassifier"
                ),
                "fit_scope": (
                    "TRAIN_ONLY_TRUE_TRADEABLE_ROWS"
                ),
                "filename": (
                    stage_b_model_path.name
                ),
                "sha256": (
                    stage_b_model_hash
                ),
            },
        }

        manifest = {
            "manifest_version": (
                self.MANIFEST_VERSION
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
                model_training_contract
            ),
            "model_training_contract_fingerprint": (
                model_training_contract_fingerprint
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
                "source_target_contract": (
                    self.SOURCE_TARGET_TRAINING_CONTRACT
                ),
                "target_label_contract": (
                    frozen_target_label_contract
                ),
                "base_timeframe": (
                    snapshot.base_timeframe
                ),
                "source_training_matrix": (
                    source_manifest.get(
                        "source_training_matrix"
                    )
                ),
            },
            "target_label_contract": (
                frozen_target_label_contract
            ),
            "target_contract": (
                target_contract
            ),
            "feature_columns": (
                features
            ),
            "feature_columns_sha256": (
                feature_hash
            ),
            "architecture": {
                "name": (
                    "HIERARCHICAL_TRADEABILITY_THEN_DIRECTION"
                ),
                "stage_a": {
                    "task": (
                        "NO_TRADE_VS_TRADEABLE"
                    ),
                    "metric_key": (
                        STAGE_A_METRICS_KEY
                    ),
                    "class_ids": [
                        0,
                        1,
                    ],
                    "class_names": [
                        "NO_TRADE",
                        "TRADEABLE",
                    ],
                    "probability_order": [
                        "NO_TRADE",
                        "TRADEABLE",
                    ],
                    "fit_scope": (
                        "TRAIN_ONLY_ALL_ROWS"
                    ),
                },
                "stage_b": {
                    "task": (
                        "SHORT_VS_LONG_GIVEN_TRADEABLE"
                    ),
                    "metric_key": (
                        STAGE_B_METRICS_KEY
                    ),
                    "class_ids": [
                        -1,
                        1,
                    ],
                    "class_names": [
                        "SHORT",
                        "LONG",
                    ],
                    "probability_order": [
                        "SHORT",
                        "LONG",
                    ],
                    "fit_scope": (
                        "TRAIN_ONLY_TRUE_TRADEABLE_ROWS"
                    ),
                },
                "final_class_ids": [
                    -1,
                    0,
                    1,
                ],
                "final_class_names": [
                    "SHORT",
                    "NO_TRADE",
                    "LONG",
                ],
                "final_probability_order": [
                    "SHORT",
                    "NO_TRADE",
                    "LONG",
                ],
            },
            "final_probability_contract": (
                final_probability_contract
            ),
            "artifacts": (
                artifacts
            ),
            "stage_a_scaler": (
                artifacts[
                    "stage_a_scaler"
                ]
            ),
            "stage_a_model": (
                artifacts[
                    "stage_a_model"
                ]
            ),
            "stage_b_scaler": (
                artifacts[
                    "stage_b_scaler"
                ]
            ),
            "stage_b_model": (
                artifacts[
                    "stage_b_model"
                ]
            ),
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
            "tradeable_rows": {
                "TRAIN": (
                    train_tradeable_rows
                ),
                "VALIDATION": (
                    validation_tradeable_rows
                ),
                "TEST": (
                    test_tradeable_rows
                ),
            },
            "train_tradeable_rows": (
                train_tradeable_rows
            ),
            "validation_tradeable_rows": (
                validation_tradeable_rows
            ),
            "test_tradeable_rows": (
                test_tradeable_rows
            ),
            "stage_b_fit_rows": (
                train_tradeable_rows
            ),
            "metrics": (
                split_metrics
            ),
            "split_metrics": (
                split_metrics
            ),
            "research_policy": (
                research_policy
            ),
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
                "m_"
                +
                model_training_contract_fingerprint[
                    :8
                ]
                +
                "_"
                +
                stage_a_model_hash[
                    :4
                ]
                +
                "_"
                +
                stage_b_model_hash[
                    :4
                ]
                +
                ".manifest.json"
            )
        )

        self._write_immutable(
            path=(
                manifest_path
            ),
            payload=(
                manifest_bytes
            ),
        )

        return (
            XAUUSDHierarchicalModelV4TrainingResult(
                model_id=(
                    self.MODEL_ID
                ),
                stage_a_model_path=(
                    stage_a_model_path
                ),
                stage_a_scaler_path=(
                    stage_a_scaler_path
                ),
                stage_b_model_path=(
                    stage_b_model_path
                ),
                stage_b_scaler_path=(
                    stage_b_scaler_path
                ),
                manifest_path=(
                    manifest_path
                ),
                output_directory=(
                    output_directory
                ),
                stage_a_model_sha256=(
                    stage_a_model_hash
                ),
                stage_a_scaler_sha256=(
                    stage_a_scaler_hash
                ),
                stage_b_model_sha256=(
                    stage_b_model_hash
                ),
                stage_b_scaler_sha256=(
                    stage_b_scaler_hash
                ),
                manifest_sha256=(
                    manifest_hash
                ),
                training_dataset_id=(
                    snapshot.dataset_id
                ),
                training_dataset_sha256=(
                    snapshot.dataset_sha256
                ),
                training_manifest_sha256=(
                    snapshot.manifest_sha256
                ),
                feature_count=(
                    len(
                        features
                    )
                ),
                train_rows=(
                    len(
                        train
                    )
                ),
                validation_rows=(
                    len(
                        validation
                    )
                ),
                test_rows=(
                    len(
                        test
                    )
                ),
                train_tradeable_rows=(
                    train_tradeable_rows
                ),
                validation_tradeable_rows=(
                    validation_tradeable_rows
                ),
                test_tradeable_rows=(
                    test_tradeable_rows
                ),
                train_metrics=(
                    train_metrics
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
                    model_training_contract_fingerprint
                ),
                live_authorized=False,
            )
        )


Trainer = (
    XAUUSDHierarchicalModelV4Trainer
)