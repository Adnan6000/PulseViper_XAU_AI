"""
===============================================================================
Module      : frozen_c04_inference_adapter.py
Project     : PulseViper XAU AI
Purpose     : Offline Inference Adapter for Frozen C04 ExtraTrees Model (Gate 14)
===============================================================================

Production-quality offline inference adapter wrapping the immutable frozen C04
ExtraTrees model (winner of historical walk-forward research).

Safety Constraints (NON-NEGOTIABLE):
- Read-only model loading: model artifact is NEVER mutated, refit, or retrained.
- Consumes the authoritative Gate 13 331-feature contract.
- Pure ML inference: no trading authorization, no order routing, no risk controls calls.
- live_authorized = False, shadow_authorized = False.
- Strictly fail-closed on any validation or schema discrepancy.
"""

from __future__ import annotations

import hashlib
import importlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import joblib
import numpy as np
import pandas as pd

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_contract: Any = importlib.import_module("02_AI.Features.portable_feature_contract")

EXPECTED_FEATURE_COUNT: int = int(_contract.EXPECTED_FEATURE_COUNT)
EXPECTED_FEATURE_COLUMNS_SHA256: str = str(_contract.EXPECTED_FEATURE_COLUMNS_SHA256)
FROZEN_MODEL_SHA256: str = str(_contract.FROZEN_MODEL_SHA256)
FROZEN_MODEL_CLASSES: tuple[int, ...] = tuple(_contract.FROZEN_MODEL_CLASSES)
FROZEN_FEATURE_COLUMNS: tuple[str, ...] = tuple(_contract.FROZEN_FEATURE_COLUMNS)
verify_feature_columns = _contract.verify_feature_columns

LABEL_MAP: dict[int, str] = {
    -1: "SHORT",
    0: "NO_TRADE",
    1: "LONG",
}

EXPECTED_MODEL_CLASS_NAME: str = "ExtraTreesClassifier"


class FrozenC04InferenceError(Exception):
    """Base exception for all Gate 14 frozen inference contract violations (fail-closed)."""
    pass


@dataclass(frozen=True)
class FrozenC04InferenceRow:
    """
    Typed, immutable result for a single inference decision.
    """
    decision_time: str | None
    probability_short: float
    probability_no_trade: float
    probability_long: float
    predicted_class: int
    predicted_label: str
    winning_probability: float
    class_order: tuple[int, ...] = FROZEN_MODEL_CLASSES
    feature_count: int = EXPECTED_FEATURE_COUNT
    feature_columns_sha256: str = EXPECTED_FEATURE_COLUMNS_SHA256
    model_sha256: str = FROZEN_MODEL_SHA256
    model_class: str = EXPECTED_MODEL_CLASS_NAME
    model_identity_verified: bool = True
    live_authorized: bool = False
    shadow_authorized: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert row to serializable dictionary."""
        return {
            "decision_time": self.decision_time,
            "probability_short": self.probability_short,
            "probability_no_trade": self.probability_no_trade,
            "probability_long": self.probability_long,
            "predicted_class": self.predicted_class,
            "predicted_label": self.predicted_label,
            "winning_probability": self.winning_probability,
            "class_order": list(self.class_order),
            "feature_count": self.feature_count,
            "feature_columns_sha256": self.feature_columns_sha256,
            "model_sha256": self.model_sha256,
            "model_class": self.model_class,
            "model_identity_verified": self.model_identity_verified,
            "live_authorized": self.live_authorized,
            "shadow_authorized": self.shadow_authorized,
        }


@dataclass(frozen=True)
class FrozenC04InferenceBatch:
    """
    Typed, immutable container for batch inference results.
    """
    rows: tuple[FrozenC04InferenceRow, ...]
    probabilities: np.ndarray
    predicted_classes: np.ndarray
    predicted_labels: tuple[str, ...]
    model_sha256: str = FROZEN_MODEL_SHA256
    feature_columns_sha256: str = EXPECTED_FEATURE_COLUMNS_SHA256
    feature_count: int = EXPECTED_FEATURE_COUNT
    live_authorized: bool = False
    shadow_authorized: bool = False

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> FrozenC04InferenceRow:
        return self.rows[index]

    def to_dataframe(self) -> pd.DataFrame:
        """Convert batch results to pandas DataFrame."""
        return pd.DataFrame([row.to_dict() for row in self.rows])


class FrozenC04InferenceAdapter:
    """
    Production offline inference adapter wrapping the immutable frozen C04 model.
    """

    def __init__(self, model_path: Path | str | None = None) -> None:
        """
        Initialize and verify the frozen model artifact.

        Args:
            model_path: Optional explicit path to frozen model. If None, resolves
                        to 'xauusd_portable_331_c04_full_train_model.joblib' at repository root.
        """
        resolved_path = self._resolve_model_path(model_path)
        self._model_path = resolved_path

        # 1. Verify model file exists
        if not resolved_path.is_file():
            raise FrozenC04InferenceError(
                f"Frozen model artifact missing at resolved path: {resolved_path}"
            )

        # 2. Verify SHA256 before loading
        actual_sha = self._compute_sha256(resolved_path)
        if actual_sha != FROZEN_MODEL_SHA256:
            raise FrozenC04InferenceError(
                f"Frozen model SHA256 mismatch! Expected {FROZEN_MODEL_SHA256}, got {actual_sha}"
            )

        # 3. Load model read-only
        try:
            self._model = joblib.load(resolved_path)
        except Exception as exc:
            raise FrozenC04InferenceError(
                f"Failed to load frozen model artifact: {exc}"
            ) from exc

        # 4. Verify model class
        actual_class = self._model.__class__.__name__
        if actual_class != EXPECTED_MODEL_CLASS_NAME:
            raise FrozenC04InferenceError(
                f"Frozen model class mismatch! Expected {EXPECTED_MODEL_CLASS_NAME}, got {actual_class}"
            )

        # 5. Verify n_features_in_
        n_features = getattr(self._model, "n_features_in_", None)
        if n_features != EXPECTED_FEATURE_COUNT:
            raise FrozenC04InferenceError(
                f"Frozen model n_features_in_ mismatch! Expected {EXPECTED_FEATURE_COUNT}, got {n_features}"
            )

        # 6. Verify classes_
        classes = getattr(self._model, "classes_", None)
        if classes is None or tuple(classes.tolist()) != FROZEN_MODEL_CLASSES:
            raise FrozenC04InferenceError(
                f"Frozen model classes_ mismatch! Expected {FROZEN_MODEL_CLASSES}, got {classes}"
            )

        self._classes = np.array(FROZEN_MODEL_CLASSES, dtype=int)
        self._model_sha256 = actual_sha
        self._model_class_name = actual_class

    @property
    def model_path(self) -> Path:
        """Resolved path to frozen model artifact."""
        return self._model_path

    @property
    def model_sha256(self) -> str:
        """Verified SHA256 of the model artifact."""
        return self._model_sha256

    @property
    def model_class(self) -> str:
        """Verified model class name."""
        return self._model_class_name

    @property
    def n_features_in(self) -> int:
        """Verified input feature dimension."""
        return EXPECTED_FEATURE_COUNT

    @property
    def classes(self) -> tuple[int, ...]:
        """Verified target classes in model order."""
        return FROZEN_MODEL_CLASSES

    def infer(
        self,
        features: pd.DataFrame | np.ndarray,
        decision_times: Sequence[Any] | None = None,
    ) -> FrozenC04InferenceBatch:
        """
        Execute offline inference on a validated Gate 13 feature matrix.

        Args:
            features: pandas DataFrame or 2D numpy array with shape (N, 331).
                      If DataFrame, column names and ordering must exactly match
                      the frozen 331-feature schema.
            decision_times: Optional sequence of timestamp strings or identifiers
                            corresponding 1:1 with input rows.

        Returns:
            FrozenC04InferenceBatch containing immutable inference rows and arrays.

        Raises:
            FrozenC04InferenceError: on any validation failure, malformed input,
                                     non-finite values, or probability inconsistency.
        """
        # 1. Validate input structure and extract matrix + timestamps
        matrix, extracted_times = self._validate_and_extract_inputs(features, decision_times)

        # 2. Execute read-only predict_proba
        try:
            raw_proba = self._model.predict_proba(matrix)
        except Exception as exc:
            raise FrozenC04InferenceError(
                f"Model predict_proba execution failed: {exc}"
            ) from exc

        # 3. Validate probability matrix
        proba = self._validate_probabilities(raw_proba, expected_rows=len(matrix))

        # 4. Derive predictions via exact frozen argmax rule: classes_[argmax(proba)]
        argmax_indices = np.argmax(proba, axis=1)
        predicted_classes = self._classes[argmax_indices]
        predicted_labels = tuple(LABEL_MAP[int(cls)] for cls in predicted_classes)
        winning_probabilities = proba[np.arange(len(proba)), argmax_indices]

        # 5. Construct immutable row records
        rows: list[FrozenC04InferenceRow] = []
        for i in range(len(matrix)):
            dt = extracted_times[i] if extracted_times is not None else None
            p_short = float(proba[i, 0])
            p_no_trade = float(proba[i, 1])
            p_long = float(proba[i, 2])
            pred_cls = int(predicted_classes[i])
            pred_lbl = predicted_labels[i]
            win_p = float(winning_probabilities[i])

            rows.append(
                FrozenC04InferenceRow(
                    decision_time=dt,
                    probability_short=p_short,
                    probability_no_trade=p_no_trade,
                    probability_long=p_long,
                    predicted_class=pred_cls,
                    predicted_label=pred_lbl,
                    winning_probability=win_p,
                )
            )

        return FrozenC04InferenceBatch(
            rows=tuple(rows),
            probabilities=proba,
            predicted_classes=predicted_classes,
            predicted_labels=predicted_labels,
        )

    def infer_single(
        self,
        feature_row: pd.Series | pd.DataFrame | np.ndarray,
        decision_time: Any | None = None,
    ) -> FrozenC04InferenceRow:
        """
        Convenience method to execute offline inference on a single feature row.
        """
        if isinstance(feature_row, pd.Series):
            df = feature_row.to_frame().T
            d_times = [decision_time] if decision_time is not None else None
            batch = self.infer(df, decision_times=d_times)
            return batch[0]

        if isinstance(feature_row, np.ndarray) and feature_row.ndim == 1:
            arr2d = feature_row.reshape(1, -1)
            d_times = [decision_time] if decision_time is not None else None
            batch = self.infer(arr2d, decision_times=d_times)
            return batch[0]

        if isinstance(feature_row, (pd.DataFrame, np.ndarray)):
            if len(feature_row) != 1:
                raise FrozenC04InferenceError(
                    f"infer_single expects exactly 1 row, got {len(feature_row)}"
                )
            d_times = [decision_time] if decision_time is not None else None
            batch = self.infer(feature_row, decision_times=d_times)
            return batch[0]

        raise FrozenC04InferenceError(
            f"Unsupported input type for infer_single: {type(feature_row)}"
        )

    # -------------------------------------------------------------------------
    # Internal Validation Helpers
    # -------------------------------------------------------------------------

    def _resolve_model_path(self, custom_path: Path | str | None) -> Path:
        """Resolve model path against repository root."""
        if custom_path is not None:
            return Path(custom_path).resolve()

        # By default, look for the authoritative artifact at repository root
        repo_root = Path(__file__).resolve().parents[2]
        candidate = repo_root / "xauusd_portable_331_c04_full_train_model.joblib"
        return candidate.resolve()

    @staticmethod
    def _compute_sha256(file_path: Path) -> str:
        """Compute SHA256 digest of a file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _validate_and_extract_inputs(
        self,
        features: pd.DataFrame | np.ndarray,
        decision_times: Sequence[Any] | None,
    ) -> tuple[np.ndarray, list[str] | None]:
        """Validate feature input types, shapes, columns, and finite values."""
        if features is None:
            raise FrozenC04InferenceError("Input features cannot be None")

        extracted_times: list[str] | None = None
        if decision_times is not None:
            extracted_times = [str(t) for t in decision_times]

        if isinstance(features, pd.DataFrame):
            if len(features) == 0:
                raise FrozenC04InferenceError("Empty feature DataFrame provided")

            if len(features.columns) != EXPECTED_FEATURE_COUNT:
                raise FrozenC04InferenceError(
                    f"Feature column count mismatch: expected {EXPECTED_FEATURE_COUNT}, "
                    f"got {len(features.columns)}"
                )

            # Strict column verification against Gate 13 contract
            if not verify_feature_columns(list(features.columns)):
                raise FrozenC04InferenceError(
                    "Feature columns contract failed: column names, count, or ordering mismatch"
                )

            # Check dtypes: reject non-numeric columns
            for col, dtype in features.dtypes.items():
                if not pd.api.types.is_numeric_dtype(dtype):
                    raise FrozenC04InferenceError(
                        f"Non-numeric dtype '{dtype}' in feature column '{col}'"
                    )

            # Check for non-finite values
            arr = features.to_numpy(dtype=np.float32)
            if not np.all(np.isfinite(arr)):
                raise FrozenC04InferenceError(
                    "Features contain NaN, +inf, or -inf values"
                )

            if extracted_times is None:
                # If index is DatetimeIndex or named 'time', extract decision times
                if isinstance(features.index, pd.DatetimeIndex):
                    extracted_times = [ts.isoformat() for ts in features.index]
                elif "time" in features.index.names:
                    extracted_times = [str(ts) for ts in features.index]

            if extracted_times is not None and len(extracted_times) != len(features):
                raise FrozenC04InferenceError(
                    f"decision_times length ({len(extracted_times)}) does not match "
                    f"features row count ({len(features)})"
                )

            return arr, extracted_times

        if isinstance(features, np.ndarray):
            if features.ndim != 2:
                raise FrozenC04InferenceError(
                    f"Expected 2D numpy array, got {features.ndim}D"
                )

            if len(features) == 0:
                raise FrozenC04InferenceError("Empty feature array provided")

            if features.shape[1] != EXPECTED_FEATURE_COUNT:
                raise FrozenC04InferenceError(
                    f"Feature dimension mismatch: expected {EXPECTED_FEATURE_COUNT}, "
                    f"got {features.shape[1]}"
                )

            if not np.issubdtype(features.dtype, np.number):
                raise FrozenC04InferenceError(
                    f"Non-numeric numpy dtype '{features.dtype}' provided"
                )

            if not np.all(np.isfinite(features)):
                raise FrozenC04InferenceError(
                    "Features contain NaN, +inf, or -inf values"
                )

            if extracted_times is not None and len(extracted_times) != len(features):
                raise FrozenC04InferenceError(
                    f"decision_times length ({len(extracted_times)}) does not match "
                    f"features row count ({len(features)})"
                )

            arr = features.astype(np.float32)
            return arr, extracted_times

        raise FrozenC04InferenceError(
            f"Unsupported feature type: {type(features)}. Expected pd.DataFrame or np.ndarray."
        )

    def _validate_probabilities(
        self,
        proba: np.ndarray,
        expected_rows: int,
    ) -> np.ndarray:
        """Validate output probability array shape, finiteness, range, and row sums."""
        if not isinstance(proba, np.ndarray):
            raise FrozenC04InferenceError(
                f"Model output is not a numpy array: {type(proba)}"
            )

        if proba.shape != (expected_rows, 3):
            raise FrozenC04InferenceError(
                f"Expected probability shape ({expected_rows}, 3), got {proba.shape}"
            )

        if not np.all(np.isfinite(proba)):
            raise FrozenC04InferenceError(
                "Model returned non-finite probabilities (NaN, +inf, -inf)"
            )

        # Allow slight floating point tolerance around [0.0, 1.0]
        if np.any(proba < -1e-6) or np.any(proba > 1.0 + 1e-6):
            raise FrozenC04InferenceError(
                f"Model probabilities out of [0, 1] bounds: min={np.min(proba)}, max={np.max(proba)}"
            )

        # Clip tiny numerical artifacts within [0.0, 1.0]
        clipped = np.clip(proba, 0.0, 1.0)

        # Check row sums approximately equal 1.0
        row_sums = np.sum(clipped, axis=1)
        if not np.all(np.isclose(row_sums, 1.0, atol=1e-4)):
            raise FrozenC04InferenceError(
                f"Probability row sums deviate from 1.0: min_sum={np.min(row_sums)}, max_sum={np.max(row_sums)}"
            )

        return clipped
