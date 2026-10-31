#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Mapping

import numpy as np


ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_ONE_TIME_"
    "VALIDATION_CORE_IMPLEMENTATION_V1"
)

REPO_ROOT = Path(__file__).resolve().parents[1]

PROTOCOL_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_validation_protocol.json"
)

EVALUATOR_PATH = (
    REPO_ROOT
    / "04_Testing"
    / "evaluate_xauusd_portable_331_train_model_candidates.py"
)

DEFAULT_ATTESTATION_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_validation_core_attestation.json"
)

EXPECTED_PROTOCOL_ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_ONE_TIME_"
    "VALIDATION_PROTOCOL_DESIGN_V1"
)

EXPECTED_PROTOCOL_CONTRACT_VERSION = (
    "XAUUSD_PORTABLE_331_ONE_TIME_"
    "VALIDATION_PROTOCOL_V1"
)

EXPECTED_PROTOCOL_FINGERPRINT = (
    "ce78180a5f2472c36c74cea2c447307641aa3d5fedfb7a01d9b65260b5a6fcea"
)

EXPECTED_WINNER_ID = (
    "C04_FLAT_EXTRA_TREES_CONSTRAINED"
)

EXPECTED_WINNER_CONFIG_SHA256 = (
    "f1b11c6f91561f2eba1bd56195e2239e9598b1906c88f11ada67eac6cdeb09e3"
)

EXPECTED_MODEL_ARTIFACT_SHA256 = (
    "48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769"
)

EXPECTED_MODEL_RECORD_SHA256 = (
    "bd6d76f92d3c6274bed756683f4263b9cce9a3f0e5ffbb8bd4ba3fcbe6f6ff74"
)

EXPECTED_MODEL_VERIFICATION_RECORD_SHA256 = (
    "a2759a429b90998a7d24c8b217e570813e36dcf43df5de6cf98daf875b8678ef"
)

EXPECTED_FEATURE_COUNT = 331

EXPECTED_CLASS_ORDER = (
    -1,
    0,
    1,
)

EXPECTED_REQUIRED_METRICS = (
    "balanced_accuracy_3class",
    "macro_f1_3class",
    "directional_macro_f1_short_long",
    "short_precision",
    "short_recall",
    "short_f1",
    "no_trade_precision",
    "no_trade_recall",
    "no_trade_f1",
    "long_precision",
    "long_recall",
    "long_f1",
    "log_loss_3class",
    "multiclass_brier",
    "predicted_trade_coverage",
)

EXPECTED_DIRECTIONAL_FLOOR = (
    0.25365034089349603
)

EXPECTED_BALANCED_ACCURACY_FLOOR = (
    0.34040386328178984
)

EXPECTED_MACRO_F1_FLOOR = (
    0.24533114425757888
)

EXPECTED_MIN_TRADE_COVERAGE = 0.05
EXPECTED_MAX_TRADE_COVERAGE = 0.95


class ValidationCoreError(
    RuntimeError
):
    pass


class ValidationLedgerError(
    ValidationCoreError
):
    pass


@dataclass(
    frozen=True
)
class ValidationBatch:
    X: np.ndarray
    target_class: np.ndarray
    target_tradeable: np.ndarray
    decision_time: np.ndarray
    feature_columns: tuple[str, ...]
    split_name: str = "VALIDATION"


def _utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def _canonical_sha256(
    value: Any,
) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        encoded
    ).hexdigest()


def _read_json_auto(
    path: Path,
) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationCoreError(
            f"Required JSON missing: {path}"
        )

    raw = path.read_bytes()

    if raw.startswith(
        (
            b"\xff\xfe",
            b"\xfe\xff",
        )
    ):
        text = raw.decode(
            "utf-16"
        )

    elif raw.startswith(
        b"\xef\xbb\xbf"
    ):
        text = raw.decode(
            "utf-8-sig"
        )

    else:
        text = raw.decode(
            "utf-8"
        )

    try:
        payload = json.loads(
            text
        )

    except json.JSONDecodeError as exc:
        raise ValidationCoreError(
            f"Invalid JSON: {path}"
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        raise ValidationCoreError(
            f"Expected JSON object: {path}"
        )

    return payload


def _required_mapping(
    mapping: Mapping[str, Any],
    key: str,
) -> Mapping[str, Any]:
    value = mapping.get(
        key
    )

    if not isinstance(
        value,
        Mapping,
    ):
        raise ValidationCoreError(
            f"Required mapping missing: {key}"
        )

    return value


def _load_evaluator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "xauusd_validation_core_evaluator",
        EVALUATOR_PATH,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise ValidationCoreError(
            "Cannot import candidate evaluator."
        )

    module = importlib.util.module_from_spec(
        spec
    )

    sys.modules[
        spec.name
    ] = module

    spec.loader.exec_module(
        module
    )

    return module


def validate_frozen_validation_protocol(
    payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    if (
        payload.get(
            "analysis_version"
        )
        != EXPECTED_PROTOCOL_ANALYSIS_VERSION
    ):
        raise ValidationCoreError(
            "Validation protocol analysis version mismatch."
        )

    if (
        payload.get(
            "valid"
        )
        is not True
    ):
        raise ValidationCoreError(
            "Validation protocol must be valid=true."
        )

    contract = _required_mapping(
        payload,
        "contract",
    )

    if (
        contract.get(
            "contract_version"
        )
        != EXPECTED_PROTOCOL_CONTRACT_VERSION
    ):
        raise ValidationCoreError(
            "Validation protocol contract version mismatch."
        )

    fingerprint = _required_mapping(
        payload,
        "contract_fingerprint",
    )

    if (
        fingerprint.get(
            "canonicalization"
        )
        != "JSON_SORT_KEYS_COMPACT_UTF8_SHA256"
    ):
        raise ValidationCoreError(
            "Validation protocol canonicalization mismatch."
        )

    if (
        fingerprint.get(
            "sha256"
        )
        != EXPECTED_PROTOCOL_FINGERPRINT
    ):
        raise ValidationCoreError(
            "Validation protocol fingerprint mismatch."
        )

    if (
        _canonical_sha256(
            contract
        )
        != EXPECTED_PROTOCOL_FINGERPRINT
    ):
        raise ValidationCoreError(
            "Validation protocol content fingerprint mismatch."
        )

    frozen_model = _required_mapping(
        contract,
        "frozen_model",
    )

    expected_model = {
        "candidate_id": (
            EXPECTED_WINNER_ID
        ),
        "winner_config_fingerprint_sha256": (
            EXPECTED_WINNER_CONFIG_SHA256
        ),
        "model_artifact_sha256": (
            EXPECTED_MODEL_ARTIFACT_SHA256
        ),
        "model_record_fingerprint_sha256": (
            EXPECTED_MODEL_RECORD_SHA256
        ),
        "model_verification_record_fingerprint_sha256": (
            EXPECTED_MODEL_VERIFICATION_RECORD_SHA256
        ),
        "feature_count": (
            EXPECTED_FEATURE_COUNT
        ),
        "probability_class_order": list(
            EXPECTED_CLASS_ORDER
        ),
    }

    for (
        key,
        expected,
    ) in expected_model.items():
        if (
            frozen_model.get(
                key
            )
            != expected
        ):
            raise ValidationCoreError(
                "Frozen model protocol mismatch: "
                f"{key}"
            )

    required_metrics = tuple(
        contract.get(
            "required_validation_metrics",
            (),
        )
    )

    if (
        required_metrics
        != EXPECTED_REQUIRED_METRICS
    ):
        raise ValidationCoreError(
            "Required validation metric contract mismatch."
        )

    gate = _required_mapping(
        contract,
        "acceptance_gate",
    )

    expected_gate_values = {
        "gate_semantics": (
            "ALL_HARD_REQUIREMENTS_MUST_PASS"
        ),
        "all_required_metrics_must_be_finite": True,
        "required_target_classes_present": list(
            EXPECTED_CLASS_ORDER
        ),
        "minimum_directional_macro_f1_short_long": (
            EXPECTED_DIRECTIONAL_FLOOR
        ),
        "minimum_balanced_accuracy_3class": (
            EXPECTED_BALANCED_ACCURACY_FLOOR
        ),
        "minimum_macro_f1_3class": (
            EXPECTED_MACRO_F1_FLOOR
        ),
        "short_recall_must_be_positive": True,
        "long_recall_must_be_positive": True,
        "minimum_predicted_trade_coverage": (
            EXPECTED_MIN_TRADE_COVERAGE
        ),
        "maximum_predicted_trade_coverage": (
            EXPECTED_MAX_TRADE_COVERAGE
        ),
        "log_loss_3class_is_hard_gate": False,
        "multiclass_brier_is_hard_gate": False,
    }

    for (
        key,
        expected,
    ) in expected_gate_values.items():
        if (
            gate.get(
                key
            )
            != expected
        ):
            raise ValidationCoreError(
                "Frozen validation gate mismatch: "
                f"{key}"
            )

    prediction_policy = _required_mapping(
        contract,
        "prediction_policy",
    )

    if (
        prediction_policy.get(
            "prediction_rule"
        )
        != "ARGMAX_FROZEN_MODEL_PROBABILITIES"
    ):
        raise ValidationCoreError(
            "Frozen prediction rule mismatch."
        )

    blocked_prediction_flags = (
        "threshold_search_allowed",
        "threshold_change_allowed",
        "probability_calibration_allowed",
        "post_hoc_class_bias_allowed",
        "candidate_change_allowed",
        "hyperparameter_change_allowed",
        "model_refit_allowed",
        "feature_selection_allowed",
    )

    for key in blocked_prediction_flags:
        if (
            prediction_policy.get(
                key
            )
            is not False
        ):
            raise ValidationCoreError(
                "Prediction-policy boundary mismatch: "
                f"{key}"
            )

    access_protocol = _required_mapping(
        contract,
        "one_time_access_protocol",
    )

    expected_access = {
        "validation_feature_access_authorized": True,
        "validation_target_access_authorized": True,
        "validation_access_attempt_limit": 1,
        "access_ledger_must_be_created_before_first_validation_value_read": True,
        "validation_metrics_may_be_computed_once": True,
        "performance_driven_validation_rerun_allowed": False,
        "test_access_during_validation_run_allowed": False,
    }

    for (
        key,
        expected,
    ) in expected_access.items():
        if (
            access_protocol.get(
                key
            )
            != expected
        ):
            raise ValidationCoreError(
                "One-time access protocol mismatch: "
                f"{key}"
            )

    decision_protocol = _required_mapping(
        contract,
        "decision_protocol",
    )

    if (
        decision_protocol.get(
            "soft_pass_allowed"
        )
        is not False
    ):
        raise ValidationCoreError(
            "Soft validation pass must remain blocked."
        )

    if (
        decision_protocol.get(
            "manual_override_allowed"
        )
        is not False
    ):
        raise ValidationCoreError(
            "Manual validation override must remain blocked."
        )

    if (
        decision_protocol.get(
            "results_driven_gate_change_allowed"
        )
        is not False
    ):
        raise ValidationCoreError(
            "Results-driven validation gate changes "
            "must remain blocked."
        )

    decision = _required_mapping(
        payload,
        "decision",
    )

    if (
        decision.get(
            "validation_protocol_frozen"
        )
        is not True
    ):
        raise ValidationCoreError(
            "Validation protocol is not frozen."
        )

    if (
        decision.get(
            "validation_values_loaded"
        )
        is not False
    ):
        raise ValidationCoreError(
            "Validation values were already recorded as loaded."
        )

    if (
        decision.get(
            "validation_metrics_computed"
        )
        is not False
    ):
        raise ValidationCoreError(
            "Validation metrics were already recorded."
        )

    if (
        decision.get(
            "validation_execution_implementation_authorized_next"
        )
        is not True
    ):
        raise ValidationCoreError(
            "Validation implementation is not authorized."
        )

    if (
        decision.get(
            "validation_execution_authorized"
        )
        is not False
    ):
        raise ValidationCoreError(
            "Real validation execution must remain "
            "unauthorized in this implementation gate."
        )

    if (
        decision.get(
            "test_access_authorized"
        )
        is not False
    ):
        raise ValidationCoreError(
            "TEST access must remain blocked."
        )

    if (
        decision.get(
            "shadow_authorized"
        )
        is not False
    ):
        raise ValidationCoreError(
            "Shadow must remain unauthorized."
        )

    if (
        decision.get(
            "live_authorized"
        )
        is not False
    ):
        raise ValidationCoreError(
            "Live must remain unauthorized."
        )

    return contract


def _validate_model_for_inference(
    model: Any,
) -> None:
    if not hasattr(
        model,
        "predict_proba",
    ):
        raise ValidationCoreError(
            "Frozen inference object lacks predict_proba."
        )

    if not hasattr(
        model,
        "classes_",
    ):
        raise ValidationCoreError(
            "Frozen inference object lacks classes_."
        )

    if not hasattr(
        model,
        "n_features_in_",
    ):
        raise ValidationCoreError(
            "Frozen inference object lacks n_features_in_."
        )

    classes = tuple(
        int(
            value
        )
        for value in np.asarray(
            model.classes_
        ).tolist()
    )

    if (
        classes
        != EXPECTED_CLASS_ORDER
    ):
        raise ValidationCoreError(
            "Inference model class order mismatch."
        )

    if (
        int(
            model.n_features_in_
        )
        != EXPECTED_FEATURE_COUNT
    ):
        raise ValidationCoreError(
            "Inference model feature count mismatch."
        )


def validate_validation_batch(
    batch: ValidationBatch,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    if (
        batch.split_name
        != "VALIDATION"
    ):
        raise ValidationCoreError(
            "Validation batch split_name must be VALIDATION."
        )

    if (
        len(
            batch.feature_columns
        )
        != EXPECTED_FEATURE_COUNT
    ):
        raise ValidationCoreError(
            "Validation feature-column count mismatch."
        )

    if (
        len(
            set(
                batch.feature_columns
            )
        )
        != EXPECTED_FEATURE_COUNT
    ):
        raise ValidationCoreError(
            "Validation feature columns contain duplicates."
        )

    X = np.asarray(
        batch.X,
        dtype=np.float64,
    )

    y_class = np.asarray(
        batch.target_class
    )

    y_tradeable = np.asarray(
        batch.target_tradeable
    )

    decision_time = np.asarray(
        batch.decision_time
    )

    if (
        X.ndim
        != 2
    ):
        raise ValidationCoreError(
            "Validation X must be two-dimensional."
        )

    if (
        X.shape[
            1
        ]
        != EXPECTED_FEATURE_COUNT
    ):
        raise ValidationCoreError(
            "Validation X feature count mismatch."
        )

    if (
        X.shape[
            0
        ]
        <= 0
    ):
        raise ValidationCoreError(
            "Validation batch must contain rows."
        )

    row_count = X.shape[
        0
    ]

    expected_vector_shape = (
        row_count,
    )

    for (
        name,
        array,
    ) in (
        (
            "target_class",
            y_class,
        ),
        (
            "target_tradeable",
            y_tradeable,
        ),
        (
            "decision_time",
            decision_time,
        ),
    ):
        if (
            array.shape
            != expected_vector_shape
        ):
            raise ValidationCoreError(
                f"{name} is not aligned to validation X."
            )

    if not np.isfinite(
        X
    ).all():
        raise ValidationCoreError(
            "Validation X contains non-finite values."
        )

    if not np.isin(
        y_class,
        EXPECTED_CLASS_ORDER,
    ).all():
        raise ValidationCoreError(
            "Validation target_class contains "
            "unexpected values."
        )

    present_classes = tuple(
        sorted(
            int(
                value
            )
            for value in np.unique(
                y_class
            )
        )
    )

    if (
        present_classes
        != EXPECTED_CLASS_ORDER
    ):
        raise ValidationCoreError(
            "Validation must contain all three "
            "required target classes."
        )

    if not np.isin(
        y_tradeable,
        (
            0,
            1,
        ),
    ).all():
        raise ValidationCoreError(
            "Validation target_tradeable contains "
            "unexpected values."
        )

    if not np.array_equal(
        (
            y_class
            != 0
        ).astype(
            np.int8
        ),
        y_tradeable.astype(
            np.int8,
            copy=False,
        ),
    ):
        raise ValidationCoreError(
            "Validation target_tradeable linkage mismatch."
        )

    if (
        decision_time.shape[
            0
        ]
        > 1
    ):
        try:
            chronological = bool(
                np.all(
                    decision_time[
                        1:
                    ]
                    > decision_time[
                        :-1
                    ]
                )
            )

        except Exception as exc:
            raise ValidationCoreError(
                "Cannot validate validation chronology."
            ) from exc

        if not chronological:
            raise ValidationCoreError(
                "Validation decision_time must "
                "be strictly increasing."
            )

    return (
        X,
        y_class.astype(
            np.int8,
            copy=False,
        ),
        y_tradeable.astype(
            np.int8,
            copy=False,
        ),
        decision_time,
    )


def _predict_probabilities(
    model: Any,
    X: np.ndarray,
) -> np.ndarray:
    probabilities = np.asarray(
        model.predict_proba(
            X
        ),
        dtype=np.float64,
    )

    if (
        probabilities.shape
        != (
            X.shape[
                0
            ],
            len(
                EXPECTED_CLASS_ORDER
            ),
        )
    ):
        raise ValidationCoreError(
            "Validation predict_proba shape mismatch."
        )

    if not np.isfinite(
        probabilities
    ).all():
        raise ValidationCoreError(
            "Validation probabilities contain "
            "non-finite values."
        )

    if (
        np.any(
            probabilities
            < 0.0
        )
        or np.any(
            probabilities
            > 1.0
        )
    ):
        raise ValidationCoreError(
            "Validation probabilities outside [0,1]."
        )

    if not np.allclose(
        probabilities.sum(
            axis=1
        ),
        1.0,
        rtol=1e-9,
        atol=1e-9,
    ):
        raise ValidationCoreError(
            "Validation probability rows do not sum to one."
        )

    return probabilities


def evaluate_acceptance_gate(
    metrics: Mapping[str, float],
    target_class: np.ndarray,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    gate = _required_mapping(
        contract,
        "acceptance_gate",
    )

    metric_keys = tuple(
        metrics.keys()
    )

    if (
        metric_keys
        != EXPECTED_REQUIRED_METRICS
    ):
        raise ValidationCoreError(
            "Validation metric output does not "
            "match frozen protocol."
        )

    finite = all(
        math.isfinite(
            float(
                value
            )
        )
        for value in metrics.values()
    )

    present_classes = tuple(
        sorted(
            int(
                value
            )
            for value in np.unique(
                target_class
            )
        )
    )

    checks = {
        "all_required_metrics_finite": (
            finite
        ),
        "required_target_classes_present": (
            present_classes
            == EXPECTED_CLASS_ORDER
        ),
        "directional_macro_f1_floor_pass": (
            float(
                metrics[
                    "directional_macro_f1_short_long"
                ]
            )
            >= float(
                gate[
                    "minimum_directional_macro_f1_short_long"
                ]
            )
        ),
        "balanced_accuracy_floor_pass": (
            float(
                metrics[
                    "balanced_accuracy_3class"
                ]
            )
            >= float(
                gate[
                    "minimum_balanced_accuracy_3class"
                ]
            )
        ),
        "macro_f1_floor_pass": (
            float(
                metrics[
                    "macro_f1_3class"
                ]
            )
            >= float(
                gate[
                    "minimum_macro_f1_3class"
                ]
            )
        ),
        "short_recall_positive": (
            float(
                metrics[
                    "short_recall"
                ]
            )
            > 0.0
        ),
        "long_recall_positive": (
            float(
                metrics[
                    "long_recall"
                ]
            )
            > 0.0
        ),
        "minimum_trade_coverage_pass": (
            float(
                metrics[
                    "predicted_trade_coverage"
                ]
            )
            >= float(
                gate[
                    "minimum_predicted_trade_coverage"
                ]
            )
        ),
        "maximum_trade_coverage_pass": (
            float(
                metrics[
                    "predicted_trade_coverage"
                ]
            )
            <= float(
                gate[
                    "maximum_predicted_trade_coverage"
                ]
            )
        ),
    }

    accepted = all(
        checks.values()
    )

    return {
        "accepted": (
            accepted
        ),
        "hard_checks": (
            checks
        ),
        "probability_metrics": {
            "log_loss_3class": (
                float(
                    metrics[
                        "log_loss_3class"
                    ]
                )
            ),
            "multiclass_brier": (
                float(
                    metrics[
                        "multiclass_brier"
                    ]
                )
            ),
            "hard_gate": False,
            "role": (
                "REPORT_ONLY_NO_POST_HOC_CALIBRATION"
            ),
        },
    }


def evaluate_loaded_validation_batch(
    *,
    model: Any,
    batch: ValidationBatch,
    protocol_contract: Mapping[str, Any],
) -> dict[str, Any]:
    _validate_model_for_inference(
        model
    )

    (
        X,
        y_class,
        _,
        _,
    ) = validate_validation_batch(
        batch
    )

    probabilities = (
        _predict_probabilities(
            model,
            X,
        )
    )

    evaluator = _load_evaluator()

    metrics = (
        evaluator.compute_fold_metrics(
            y_class,
            probabilities,
        )
    )

    if (
        tuple(
            metrics.keys()
        )
        != EXPECTED_REQUIRED_METRICS
    ):
        raise ValidationCoreError(
            "Evaluator metric contract mismatch."
        )

    gate_result = (
        evaluate_acceptance_gate(
            metrics,
            y_class,
            protocol_contract,
        )
    )

    return {
        "row_count": int(
            X.shape[
                0
            ]
        ),
        "feature_count": int(
            X.shape[
                1
            ]
        ),
        "target_classes_present": [
            int(
                value
            )
            for value in np.unique(
                y_class
            )
        ],
        "metrics": {
            key: float(
                value
            )
            for (
                key,
                value,
            ) in metrics.items()
        },
        "gate_result": (
            gate_result
        ),
        "prediction_policy": {
            "rule": (
                "ARGMAX_FROZEN_MODEL_PROBABILITIES"
            ),
            "threshold_search_performed": False,
            "probability_calibration_performed": False,
            "post_hoc_class_bias_performed": False,
        },
    }


class ValidationAccessLedger:
    def __init__(
        self,
        *,
        path: Path,
        protocol_fingerprint_sha256: str,
        model_artifact_sha256: str,
    ) -> None:
        self.path = Path(
            path
        )

        self.protocol_fingerprint_sha256 = (
            protocol_fingerprint_sha256
        )

        self.model_artifact_sha256 = (
            model_artifact_sha256
        )

    def _base_payload(
        self,
    ) -> dict[str, Any]:
        return {
            "ledger_version": (
                "XAUUSD_PORTABLE_331_ONE_TIME_"
                "VALIDATION_ACCESS_LEDGER_V1"
            ),
            "protocol_fingerprint_sha256": (
                self.protocol_fingerprint_sha256
            ),
            "model_artifact_sha256": (
                self.model_artifact_sha256
            ),
            "validation_read_attempt_count": 0,
            "holdout_consumed_for_rerun_policy": False,
            "validation_values_loaded": False,
            "validation_metrics_computed": False,
            "test_values_accessed": False,
            "status": (
                "RESERVED_BEFORE_READ"
            ),
            "created_utc": (
                _utc_now()
            ),
            "updated_utc": (
                _utc_now()
            ),
        }

    def load(
        self,
    ) -> dict[str, Any]:
        payload = _read_json_auto(
            self.path
        )

        if (
            payload.get(
                "protocol_fingerprint_sha256"
            )
            != self.protocol_fingerprint_sha256
        ):
            raise ValidationLedgerError(
                "Ledger protocol fingerprint mismatch."
            )

        if (
            payload.get(
                "model_artifact_sha256"
            )
            != self.model_artifact_sha256
        ):
            raise ValidationLedgerError(
                "Ledger model artifact fingerprint mismatch."
            )

        return payload

    def _write_atomic(
        self,
        payload: Mapping[str, Any],
    ) -> None:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = (
            self.path.with_suffix(
                self.path.suffix
                + ".tmp"
            )
        )

        temporary.write_text(
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        temporary.replace(
            self.path
        )

    def reserve_before_read(
        self,
    ) -> dict[str, Any]:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if self.path.exists():
            existing = self.load()

            if (
                existing.get(
                    "status"
                )
                == "PRE_READ_TECHNICAL_FAILURE"
                and existing.get(
                    "validation_read_attempt_count"
                )
                == 0
                and existing.get(
                    "holdout_consumed_for_rerun_policy"
                )
                is False
            ):
                retry = self._base_payload()

                retry[
                    "created_utc"
                ] = existing.get(
                    "created_utc"
                )

                retry[
                    "pre_read_recovery_count"
                ] = int(
                    existing.get(
                        "pre_read_recovery_count",
                        0,
                    )
                ) + 1

                self._write_atomic(
                    retry
                )

                return retry

            raise ValidationLedgerError(
                "Validation access ledger already exists "
                "and cannot be reserved again."
            )

        payload = self._base_payload()

        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
        )

        try:
            descriptor = os.open(
                self.path,
                flags,
            )

        except FileExistsError as exc:
            raise ValidationLedgerError(
                "Validation access ledger already exists."
            ) from exc

        try:
            with os.fdopen(
                descriptor,
                "w",
                encoding="utf-8",
                newline="\n",
            ) as handle:
                json.dump(
                    payload,
                    handle,
                    indent=2,
                    sort_keys=True,
                    ensure_ascii=False,
                )

                handle.write(
                    "\n"
                )

        except Exception:
            self.path.unlink(
                missing_ok=True
            )
            raise

        return payload

    def mark_read_initiated(
        self,
    ) -> dict[str, Any]:
        payload = self.load()

        if (
            payload.get(
                "status"
            )
            != "RESERVED_BEFORE_READ"
        ):
            raise ValidationLedgerError(
                "Ledger is not reserved for first read."
            )

        if (
            payload.get(
                "validation_read_attempt_count"
            )
            != 0
        ):
            raise ValidationLedgerError(
                "Validation read attempt limit exceeded."
            )

        payload[
            "validation_read_attempt_count"
        ] = 1

        payload[
            "holdout_consumed_for_rerun_policy"
        ] = True

        payload[
            "read_initiated_utc"
        ] = _utc_now()

        payload[
            "updated_utc"
        ] = _utc_now()

        payload[
            "status"
        ] = (
            "READ_INITIATED_CONSUMED_BOUNDARY"
        )

        self._write_atomic(
            payload
        )

        return payload

    def mark_values_loaded(
        self,
        batch: ValidationBatch,
    ) -> dict[str, Any]:
        payload = self.load()

        if (
            payload.get(
                "status"
            )
            != "READ_INITIATED_CONSUMED_BOUNDARY"
        ):
            raise ValidationLedgerError(
                "Validation values cannot be marked "
                "loaded before read initiation."
            )

        X = np.asarray(
            batch.X
        )

        payload[
            "validation_values_loaded"
        ] = True

        payload[
            "validation_row_count"
        ] = int(
            X.shape[
                0
            ]
        )

        payload[
            "validation_feature_count"
        ] = int(
            X.shape[
                1
            ]
        )

        payload[
            "values_loaded_utc"
        ] = _utc_now()

        payload[
            "updated_utc"
        ] = _utc_now()

        payload[
            "status"
        ] = (
            "VALIDATION_VALUES_LOADED"
        )

        self._write_atomic(
            payload
        )

        return payload

    def mark_metrics_computed(
        self,
        result: Mapping[str, Any],
    ) -> dict[str, Any]:
        payload = self.load()

        if (
            payload.get(
                "status"
            )
            != "VALIDATION_VALUES_LOADED"
        ):
            raise ValidationLedgerError(
                "Validation metrics cannot be completed "
                "before values are loaded."
            )

        gate_result = _required_mapping(
            result,
            "gate_result",
        )

        accepted = (
            gate_result.get(
                "accepted"
            )
            is True
        )

        payload[
            "validation_metrics_computed"
        ] = True

        payload[
            "validation_accepted"
        ] = accepted

        payload[
            "test_access_authorized_next"
        ] = accepted

        payload[
            "metrics_computed_utc"
        ] = _utc_now()

        payload[
            "updated_utc"
        ] = _utc_now()

        payload[
            "status"
        ] = (
            "VALIDATION_COMPLETE_ACCEPTED"
            if accepted
            else "VALIDATION_COMPLETE_REJECTED"
        )

        self._write_atomic(
            payload
        )

        return payload

    def mark_failure(
        self,
        exc: BaseException,
    ) -> dict[str, Any]:
        if not self.path.exists():
            raise ValidationLedgerError(
                "Cannot record failure without ledger."
            )

        payload = self.load()

        read_attempt_count = int(
            payload.get(
                "validation_read_attempt_count",
                0,
            )
        )

        consumed = bool(
            payload.get(
                "holdout_consumed_for_rerun_policy",
                False,
            )
        )

        payload[
            "failure_type"
        ] = type(
            exc
        ).__name__

        payload[
            "failure_reason"
        ] = str(
            exc
        )

        payload[
            "failure_utc"
        ] = _utc_now()

        payload[
            "updated_utc"
        ] = _utc_now()

        if (
            read_attempt_count
            == 0
            and not consumed
        ):
            payload[
                "status"
            ] = (
                "PRE_READ_TECHNICAL_FAILURE"
            )

        else:
            payload[
                "holdout_consumed_for_rerun_policy"
            ] = True

            payload[
                "status"
            ] = (
                "CONSUMED_TECHNICAL_FAILURE"
            )

        self._write_atomic(
            payload
        )

        return payload


def run_one_time_validation_from_source(
    *,
    protocol_payload: Mapping[str, Any],
    model: Any,
    source: Callable[
        [],
        ValidationBatch,
    ],
    ledger: ValidationAccessLedger,
) -> dict[str, Any]:
    contract = (
        validate_frozen_validation_protocol(
            protocol_payload
        )
    )

    ledger.reserve_before_read()

    try:
        _validate_model_for_inference(
            model
        )

    except Exception as exc:
        ledger.mark_failure(
            exc
        )
        raise

    ledger.mark_read_initiated()

    try:
        batch = source()

        if not isinstance(
            batch,
            ValidationBatch,
        ):
            raise ValidationCoreError(
                "Validation source must return ValidationBatch."
            )

        ledger.mark_values_loaded(
            batch
        )

        result = (
            evaluate_loaded_validation_batch(
                model=model,
                batch=batch,
                protocol_contract=contract,
            )
        )

        final_ledger = (
            ledger.mark_metrics_computed(
                result
            )
        )

    except Exception as exc:
        try:
            current = ledger.load()

            if (
                current.get(
                    "status"
                )
                not in (
                    "VALIDATION_COMPLETE_ACCEPTED",
                    "VALIDATION_COMPLETE_REJECTED",
                )
            ):
                ledger.mark_failure(
                    exc
                )

        except Exception:
            pass

        raise

    accepted = (
        result[
            "gate_result"
        ][
            "accepted"
        ]
        is True
    )

    return {
        "analysis_version": (
            "XAUUSD_PORTABLE_331_ONE_TIME_"
            "VALIDATION_CORE_RESULT_V1"
        ),
        "valid": True,
        "research_scope": (
            "ONE_TIME_VALIDATION_CORE_EXECUTION_"
            "AGAINST_CALLER_SUPPLIED_VALIDATION_BATCH"
        ),
        "protocol_fingerprint_sha256": (
            EXPECTED_PROTOCOL_FINGERPRINT
        ),
        "model_artifact_sha256": (
            EXPECTED_MODEL_ARTIFACT_SHA256
        ),
        "validation_result": (
            result
        ),
        "ledger": (
            final_ledger
        ),
        "decision": {
            "validation_accepted": (
                accepted
            ),
            "test_access_authorized_next": (
                accepted
            ),
            "test_access_performed": False,
            "model_refit_performed": False,
            "threshold_search_performed": False,
            "probability_calibration_performed": False,
            "candidate_change_performed": False,
            "shadow_authorized": False,
            "live_authorized": False,
        },
    }


def build_implementation_attestation() -> dict[str, Any]:
    protocol = _read_json_auto(
        PROTOCOL_PATH
    )

    contract = (
        validate_frozen_validation_protocol(
            protocol
        )
    )

    return {
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "valid": True,
        "research_scope": (
            "IMPLEMENTATION_ATTESTATION_ONLY_"
            "WITHOUT_VALIDATION_OR_TEST_VALUE_ACCESS"
        ),
        "protocol": {
            "analysis_version": (
                protocol[
                    "analysis_version"
                ]
            ),
            "contract_version": (
                contract[
                    "contract_version"
                ]
            ),
            "contract_fingerprint_sha256": (
                EXPECTED_PROTOCOL_FINGERPRINT
            ),
        },
        "implementation": {
            "validation_batch_contract_present": True,
            "one_time_access_ledger_present": True,
            "ledger_created_before_read_boundary": True,
            "conservative_consumption_boundary_present": True,
            "pre_read_failure_recovery_supported": True,
            "post_read_rerun_blocked": True,
            "frozen_model_inference_validation_present": True,
            "frozen_metric_contract_present": True,
            "frozen_acceptance_gate_present": True,
            "test_access_path_present": False,
            "real_validation_data_source_wired": False,
        },
        "decision": {
            "status": (
                "ONE_TIME_VALIDATION_CORE_"
                "IMPLEMENTED_NOT_REAL_EXECUTED"
            ),
            "real_validation_execution_authorized": False,
            "real_validation_values_loaded": False,
            "real_validation_metrics_computed": False,
            "synthetic_testing_authorized": True,
            "test_access_authorized": False,
            "shadow_authorized": False,
            "live_authorized": False,
            "next_action": (
                "SYNTHETICALLY_VALIDATE_LEDGER_"
                "CONSUMPTION_METRICS_AND_GATE_"
                "BEFORE_WIRING_REAL_VALIDATION_SOURCE"
            ),
        },
        "scientific_policy": {
            "train_feature_values_loaded": False,
            "train_target_values_loaded": False,
            "portable_validation_feature_values_loaded": False,
            "portable_validation_target_values_loaded": False,
            "portable_validation_metrics_computed": False,
            "portable_test_feature_values_loaded": False,
            "portable_test_target_values_loaded": False,
            "portable_test_metrics_computed": False,
            "model_fit_performed": False,
            "model_refit_performed": False,
            "threshold_search_performed": False,
            "probability_calibration_performed": False,
            "feature_selection_performed": False,
            "candidate_registry_changed": False,
            "model_artifact_modified": False,
            "execution_integration_modified": False,
            "risk_engine_modified": False,
            "orders_sent": False,
            "shadow_authorized": False,
            "live_authorized": False,
        },
    }


def _write_json_atomic(
    path: Path,
    payload: Mapping[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix
        + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary.replace(
        path
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Attest the one-time validation core "
            "implementation without reading real "
            "VALIDATION or TEST values."
        )
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_ATTESTATION_PATH,
    )

    args = parser.parse_args()

    try:
        report = (
            build_implementation_attestation()
        )

        _write_json_atomic(
            args.output,
            report,
        )

    except Exception as exc:
        failure = {
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "valid": False,
            "reason": (
                "ONE_TIME_VALIDATION_CORE_"
                "IMPLEMENTATION_ATTESTATION_FAILED"
            ),
            "error_type": (
                type(
                    exc
                ).__name__
            ),
            "error": str(
                exc
            ),
            "scientific_policy": {
                "portable_validation_feature_values_loaded": False,
                "portable_validation_target_values_loaded": False,
                "portable_test_feature_values_loaded": False,
                "portable_test_target_values_loaded": False,
                "model_fit_performed": False,
                "live_authorized": False,
            },
        }

        _write_json_atomic(
            args.output,
            failure,
        )

        print(
            json.dumps(
                failure,
                indent=2,
                sort_keys=True,
            )
        )

        return 1

    print(
        json.dumps(
            {
                "analysis_version": (
                    report[
                        "analysis_version"
                    ]
                ),
                "valid": True,
                "protocol_fingerprint_sha256": (
                    report[
                        "protocol"
                    ][
                        "contract_fingerprint_sha256"
                    ]
                ),
                "implementation": (
                    report[
                        "implementation"
                    ]
                ),
                "decision": (
                    report[
                        "decision"
                    ]
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )