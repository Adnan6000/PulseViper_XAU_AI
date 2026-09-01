from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np


ANALYSIS_VERSION = "XAUUSD_PORTABLE_331_ONE_TIME_TEST_CORE_IMPLEMENTATION_V1"
ATTESTATION_STATUS = "ONE_TIME_TEST_CORE_IMPLEMENTED_NOT_REAL_EXECUTED"
LEDGER_VERSION = "XAUUSD_PORTABLE_331_ONE_TIME_TEST_ACCESS_LEDGER_V1"
RESULT_ANALYSIS_VERSION = "XAUUSD_PORTABLE_331_ONE_TIME_TEST_RESULT_V1"

PROTOCOL_PATH = Path("xauusd_portable_331_one_time_test_protocol.json")
ATTESTATION_PATH = Path(
    "xauusd_portable_331_one_time_test_core_attestation.json"
)
DEFAULT_LEDGER_PATH = Path(
    "xauusd_portable_331_one_time_test_access_ledger.json"
)

EXPECTED_TEST_PROTOCOL_FINGERPRINT = (
    "f8acc2665e9e5bbd3c3ad4bdf34d4a1ff9bfb8b715acf24f6669530eaa5aab3e"
)
EXPECTED_VALIDATION_RESULT_FINGERPRINT = (
    "ea8b482e60f854f58e27f3be387b7bb82f0c16a6cf1a99555b12643aeeca5fa1"
)
EXPECTED_VALIDATION_FREEZE_FINGERPRINT = (
    "521a97b41a86231b049cc65aebfd85ffc7c83ae7141134d6ae1158d112b1468c"
)
EXPECTED_MODEL_ARTIFACT_SHA256 = (
    "48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769"
)
EXPECTED_FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

EXPECTED_FEATURE_COUNT = 331
EXPECTED_CLASS_ORDER = [-1, 0, 1]

REQUIRED_METRICS = [
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
]

TRAIN_DERIVED_HARD_FLOORS = {
    "directional_macro_f1_short_long": 0.25365034089349603,
    "balanced_accuracy_3class": 0.34040386328178984,
    "macro_f1_3class": 0.24533114425757888,
    "predicted_trade_coverage_min": 0.05,
    "predicted_trade_coverage_max": 0.95,
}

STATUS_RESERVED = "RESERVED_BEFORE_READ"
STATUS_READ_INITIATED = "TEST_READ_INITIATED_CONSUMED_BOUNDARY"
STATUS_VALUES_LOADED = "TEST_VALUES_LOADED"
STATUS_COMPLETE_ACCEPTED = "TEST_COMPLETE_ACCEPTED"
STATUS_COMPLETE_REJECTED = "TEST_COMPLETE_REJECTED"
STATUS_PRE_READ_FAILURE = "PRE_READ_TECHNICAL_FAILURE"
STATUS_CONSUMED_FAILURE = "CONSUMED_TECHNICAL_FAILURE"


class OneTimeTestCoreError(RuntimeError):
    """Raised when the frozen one-time TEST contract is violated."""


@dataclass(frozen=True)
class ProtectedTestBatch:
    X: np.ndarray
    y_true: np.ndarray


@dataclass(frozen=True)
class TestAcceptanceDecision:
    accepted: bool
    hard_checks: dict[str, bool]


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(
        _canonical_json(value).encode("utf-8")
    )


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(
            encoding="utf-8"
        )
    except UnicodeDecodeError as exc:
        raise OneTimeTestCoreError(
            f"JSON_NOT_UTF8:{path}"
        ) from exc

    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise OneTimeTestCoreError(
            f"JSON_INVALID:{path}"
        ) from exc

    if not isinstance(value, dict):
        raise OneTimeTestCoreError(
            f"JSON_ROOT_NOT_OBJECT:{path}"
        )

    return value


def load_and_verify_frozen_test_protocol(
    path: Path = PROTOCOL_PATH,
) -> dict[str, Any]:
    protocol = _load_json(path)

    if protocol.get("valid") is not True:
        raise OneTimeTestCoreError(
            "TEST_PROTOCOL_NOT_VALID"
        )

    if (
        protocol.get("status")
        != "ONE_TIME_TEST_PROTOCOL_FROZEN"
    ):
        raise OneTimeTestCoreError(
            "TEST_PROTOCOL_NOT_FROZEN"
        )

    if (
        protocol.get("protocol_fingerprint")
        != EXPECTED_TEST_PROTOCOL_FINGERPRINT
    ):
        raise OneTimeTestCoreError(
            "TEST_PROTOCOL_FINGERPRINT_MISMATCH:"
            f"expected={EXPECTED_TEST_PROTOCOL_FINGERPRINT};"
            f"actual={protocol.get('protocol_fingerprint')!r}"
        )

    contract = protocol.get("contract")

    if not isinstance(
        contract,
        dict,
    ):
        raise OneTimeTestCoreError(
            "TEST_PROTOCOL_CONTRACT_MISSING"
        )

    parent = contract.get(
        "parent_validation_binding"
    )

    if not isinstance(
        parent,
        dict,
    ):
        raise OneTimeTestCoreError(
            "PARENT_VALIDATION_BINDING_MISSING"
        )

    if (
        parent.get(
            "validation_result_fingerprint"
        )
        != EXPECTED_VALIDATION_RESULT_FINGERPRINT
    ):
        raise OneTimeTestCoreError(
            "VALIDATION_RESULT_FINGERPRINT_MISMATCH"
        )

    if (
        parent.get(
            "validation_freeze_fingerprint"
        )
        != EXPECTED_VALIDATION_FREEZE_FINGERPRINT
    ):
        raise OneTimeTestCoreError(
            "VALIDATION_FREEZE_FINGERPRINT_MISMATCH"
        )

    if (
        parent.get(
            "validation_consumed"
        )
        is not True
    ):
        raise OneTimeTestCoreError(
            "VALIDATION_MUST_ALREADY_BE_CONSUMED"
        )

    if (
        parent.get(
            "validation_reread_authorized"
        )
        is not False
    ):
        raise OneTimeTestCoreError(
            "VALIDATION_REREAD_MUST_BE_FORBIDDEN"
        )

    dataset = contract.get(
        "dataset_binding"
    )

    if not isinstance(
        dataset,
        dict,
    ):
        raise OneTimeTestCoreError(
            "DATASET_BINDING_MISSING"
        )

    if (
        dataset.get(
            "feature_count"
        )
        != EXPECTED_FEATURE_COUNT
    ):
        raise OneTimeTestCoreError(
            "FEATURE_COUNT_BINDING_MISMATCH"
        )

    if (
        dataset.get(
            "feature_columns_sha256"
        )
        != EXPECTED_FEATURE_COLUMNS_SHA256
    ):
        raise OneTimeTestCoreError(
            "FEATURE_COLUMNS_BINDING_MISMATCH"
        )

    model = contract.get(
        "model_binding"
    )

    if not isinstance(
        model,
        dict,
    ):
        raise OneTimeTestCoreError(
            "MODEL_BINDING_MISSING"
        )

    if (
        model.get(
            "model_artifact_sha256"
        )
        != EXPECTED_MODEL_ARTIFACT_SHA256
    ):
        raise OneTimeTestCoreError(
            "MODEL_ARTIFACT_BINDING_MISMATCH"
        )

    if (
        model.get(
            "probability_class_order"
        )
        != EXPECTED_CLASS_ORDER
    ):
        raise OneTimeTestCoreError(
            "MODEL_CLASS_ORDER_BINDING_MISMATCH"
        )

    scientific = contract.get(
        "scientific_policy"
    )

    if not isinstance(
        scientific,
        dict,
    ):
        raise OneTimeTestCoreError(
            "SCIENTIFIC_POLICY_MISSING"
        )

    forbidden_false_keys = [
        "model_refit_allowed",
        "candidate_change_allowed",
        "feature_change_allowed",
        "target_change_allowed",
        "threshold_search_allowed",
        "probability_calibration_allowed",
        "validation_peeking_allowed",
        (
            "test_peeking_before_one_shot_"
            "execution_allowed"
        ),
        (
            "test_result_may_tune_current_"
            "frozen_lineage"
        ),
        "shadow_authorized",
        "live_authorized",
    ]

    for key in forbidden_false_keys:
        if scientific.get(key) is not False:
            raise OneTimeTestCoreError(
                "SCIENTIFIC_POLICY_NOT_FAIL_CLOSED:"
                f"{key}"
            )

    return protocol


def validate_test_batch(
    batch: ProtectedTestBatch,
) -> ProtectedTestBatch:
    X = np.asarray(
        batch.X
    )

    y_true = np.asarray(
        batch.y_true
    )

    if X.ndim != 2:
        raise OneTimeTestCoreError(
            f"TEST_X_NOT_2D:shape={X.shape}"
        )

    if X.shape[0] <= 0:
        raise OneTimeTestCoreError(
            "TEST_BATCH_EMPTY"
        )

    if (
        X.shape[1]
        != EXPECTED_FEATURE_COUNT
    ):
        raise OneTimeTestCoreError(
            "TEST_FEATURE_COUNT_MISMATCH:"
            f"expected={EXPECTED_FEATURE_COUNT};"
            f"actual={X.shape[1]}"
        )

    if not np.issubdtype(
        X.dtype,
        np.number,
    ):
        raise OneTimeTestCoreError(
            f"TEST_X_NOT_NUMERIC:dtype={X.dtype}"
        )

    if not np.isfinite(
        X
    ).all():
        raise OneTimeTestCoreError(
            "TEST_X_NON_FINITE"
        )

    if y_true.ndim != 1:
        raise OneTimeTestCoreError(
            f"TEST_Y_NOT_1D:shape={y_true.shape}"
        )

    if (
        y_true.shape[0]
        != X.shape[0]
    ):
        raise OneTimeTestCoreError(
            "TEST_ROW_COUNT_MISMATCH:"
            f"X={X.shape[0]};"
            f"y={y_true.shape[0]}"
        )

    if not np.issubdtype(
        y_true.dtype,
        np.number,
    ):
        raise OneTimeTestCoreError(
            f"TEST_Y_NOT_NUMERIC:dtype={y_true.dtype}"
        )

    if not np.isfinite(
        y_true.astype(
            np.float64,
            copy=False,
        )
    ).all():
        raise OneTimeTestCoreError(
            "TEST_Y_NON_FINITE"
        )

    try:
        normalized_y = y_true.astype(
            np.int8,
            copy=False,
        )
    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as exc:
        raise OneTimeTestCoreError(
            "TEST_Y_NOT_INTEGER_COMPATIBLE"
        ) from exc

    if not np.array_equal(
        normalized_y.astype(
            y_true.dtype,
            copy=False,
        ),
        y_true,
    ):
        raise OneTimeTestCoreError(
            "TEST_Y_NOT_EXACT_INTEGER_CLASSES"
        )

    observed = sorted(
        int(value)
        for value in np.unique(
            normalized_y
        )
    )

    if (
        observed
        != EXPECTED_CLASS_ORDER
    ):
        raise OneTimeTestCoreError(
            "TEST_TARGET_CLASSES_MISMATCH:"
            f"expected={EXPECTED_CLASS_ORDER};"
            f"actual={observed}"
        )

    return ProtectedTestBatch(
        X=np.asarray(
            X,
            dtype=np.float64,
        ),
        y_true=np.asarray(
            normalized_y,
            dtype=np.int8,
        ),
    )


def validate_probability_output(
    probabilities: np.ndarray,
    *,
    expected_rows: int,
    model_class_order: Sequence[int],
) -> np.ndarray:
    observed_order = [
        int(value)
        for value in model_class_order
    ]

    if (
        observed_order
        != EXPECTED_CLASS_ORDER
    ):
        raise OneTimeTestCoreError(
            "PREDICTION_CLASS_ORDER_MISMATCH:"
            f"expected={EXPECTED_CLASS_ORDER};"
            f"actual={observed_order}"
        )

    proba = np.asarray(
        probabilities,
        dtype=np.float64,
    )

    expected_shape = (
        expected_rows,
        len(
            EXPECTED_CLASS_ORDER
        ),
    )

    if proba.shape != expected_shape:
        raise OneTimeTestCoreError(
            "PREDICTION_PROBABILITY_SHAPE_MISMATCH:"
            f"expected={expected_shape};"
            f"actual={proba.shape}"
        )

    if not np.isfinite(
        proba
    ).all():
        raise OneTimeTestCoreError(
            "PREDICTION_PROBABILITIES_NON_FINITE"
        )

    if (
        np.any(
            proba < 0.0
        )
        or np.any(
            proba > 1.0
        )
    ):
        raise OneTimeTestCoreError(
            "PREDICTION_PROBABILITIES_OUT_OF_RANGE"
        )

    row_sums = proba.sum(
        axis=1
    )

    if not np.allclose(
        row_sums,
        1.0,
        rtol=0.0,
        atol=1e-8,
    ):
        raise OneTimeTestCoreError(
            "PREDICTION_PROBABILITIES_DO_NOT_SUM_TO_ONE"
        )

    return proba


def evaluate_acceptance(
    metrics: Mapping[str, Any],
) -> TestAcceptanceDecision:
    missing = [
        name
        for name in REQUIRED_METRICS
        if name not in metrics
    ]

    if missing:
        raise OneTimeTestCoreError(
            "REQUIRED_TEST_METRICS_MISSING:"
            f"{missing}"
        )

    numeric: dict[
        str,
        float,
    ] = {}

    for name in REQUIRED_METRICS:
        value = metrics[
            name
        ]

        if isinstance(
            value,
            bool,
        ):
            raise OneTimeTestCoreError(
                "TEST_METRIC_NOT_NUMERIC:"
                f"{name}"
            )

        try:
            number = float(
                value
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise OneTimeTestCoreError(
                "TEST_METRIC_NOT_NUMERIC:"
                f"{name}"
            ) from exc

        if not math.isfinite(
            number
        ):
            raise OneTimeTestCoreError(
                "TEST_METRIC_NON_FINITE:"
                f"{name}"
            )

        numeric[
            name
        ] = number

    hard_checks = {
        "all_required_metrics_finite": True,
        (
            "directional_macro_f1_short_long_floor"
        ): (
            numeric[
                "directional_macro_f1_short_long"
            ]
            >= TRAIN_DERIVED_HARD_FLOORS[
                "directional_macro_f1_short_long"
            ]
        ),
        "balanced_accuracy_3class_floor": (
            numeric[
                "balanced_accuracy_3class"
            ]
            >= TRAIN_DERIVED_HARD_FLOORS[
                "balanced_accuracy_3class"
            ]
        ),
        "macro_f1_3class_floor": (
            numeric[
                "macro_f1_3class"
            ]
            >= TRAIN_DERIVED_HARD_FLOORS[
                "macro_f1_3class"
            ]
        ),
        "short_recall_positive": (
            numeric[
                "short_recall"
            ]
            > 0.0
        ),
        "long_recall_positive": (
            numeric[
                "long_recall"
            ]
            > 0.0
        ),
        (
            "predicted_trade_coverage_min"
        ): (
            numeric[
                "predicted_trade_coverage"
            ]
            >= TRAIN_DERIVED_HARD_FLOORS[
                "predicted_trade_coverage_min"
            ]
        ),
        (
            "predicted_trade_coverage_max"
        ): (
            numeric[
                "predicted_trade_coverage"
            ]
            <= TRAIN_DERIVED_HARD_FLOORS[
                "predicted_trade_coverage_max"
            ]
        ),
    }

    return TestAcceptanceDecision(
        accepted=all(
            hard_checks.values()
        ),
        hard_checks=hard_checks,
    )


class TestAccessLedger:
    def __init__(
        self,
        path: Path = DEFAULT_LEDGER_PATH,
        *,
        protocol_fingerprint: str = (
            EXPECTED_TEST_PROTOCOL_FINGERPRINT
        ),
    ) -> None:
        self.path = Path(
            path
        )

        self.protocol_fingerprint = (
            protocol_fingerprint
        )

    def exists(
        self,
    ) -> bool:
        return self.path.is_file()

    def read(
        self,
    ) -> dict[str, Any]:
        if not self.path.is_file():
            raise OneTimeTestCoreError(
                "TEST_LEDGER_MISSING:"
                f"{self.path}"
            )

        document = _load_json(
            self.path
        )

        self._validate_identity(
            document
        )

        return document

    def _validate_identity(
        self,
        document: Mapping[
            str,
            Any,
        ],
    ) -> None:
        if (
            document.get(
                "ledger_version"
            )
            != LEDGER_VERSION
        ):
            raise OneTimeTestCoreError(
                "TEST_LEDGER_VERSION_MISMATCH"
            )

        if (
            document.get(
                "test_protocol_fingerprint"
            )
            != self.protocol_fingerprint
        ):
            raise OneTimeTestCoreError(
                "TEST_LEDGER_PROTOCOL_FINGERPRINT_MISMATCH"
            )

        if (
            document.get(
                "validation_result_fingerprint"
            )
            != EXPECTED_VALIDATION_RESULT_FINGERPRINT
        ):
            raise OneTimeTestCoreError(
                "TEST_LEDGER_VALIDATION_RESULT_MISMATCH"
            )

        if (
            document.get(
                "validation_freeze_fingerprint"
            )
            != EXPECTED_VALIDATION_FREEZE_FINGERPRINT
        ):
            raise OneTimeTestCoreError(
                "TEST_LEDGER_VALIDATION_FREEZE_MISMATCH"
            )

        if (
            document.get(
                "model_artifact_sha256"
            )
            != EXPECTED_MODEL_ARTIFACT_SHA256
        ):
            raise OneTimeTestCoreError(
                "TEST_LEDGER_MODEL_SHA_MISMATCH"
            )

        if (
            document.get(
                "feature_columns_sha256"
            )
            != EXPECTED_FEATURE_COLUMNS_SHA256
        ):
            raise OneTimeTestCoreError(
                "TEST_LEDGER_FEATURE_SHA_MISMATCH"
            )

    def _write(
        self,
        document: Mapping[
            str,
            Any,
        ],
    ) -> None:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = (
            json.dumps(
                document,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n"
        )

        temporary = (
            self.path.with_name(
                self.path.name
                + ".tmp"
            )
        )

        temporary.write_text(
            payload,
            encoding="utf-8",
        )

        os.replace(
            temporary,
            self.path,
        )

    def _new_document(
        self,
    ) -> dict[str, Any]:
        return {
            "ledger_version": (
                LEDGER_VERSION
            ),
            "valid": True,
            "status": (
                STATUS_RESERVED
            ),
            (
                "test_protocol_fingerprint"
            ): (
                self.protocol_fingerprint
            ),
            (
                "validation_result_fingerprint"
            ): (
                EXPECTED_VALIDATION_RESULT_FINGERPRINT
            ),
            (
                "validation_freeze_fingerprint"
            ): (
                EXPECTED_VALIDATION_FREEZE_FINGERPRINT
            ),
            "model_artifact_sha256": (
                EXPECTED_MODEL_ARTIFACT_SHA256
            ),
            "feature_columns_sha256": (
                EXPECTED_FEATURE_COLUMNS_SHA256
            ),
            "test_read_attempt_count": 0,
            (
                "holdout_consumed_for_rerun_policy"
            ): False,
            "test_values_loaded": False,
            "test_metrics_computed": False,
            "test_accepted": None,
            "validation_values_reread": False,
            "technical_failure": None,
            "events": [
                {
                    "event": (
                        STATUS_RESERVED
                    ),
                    (
                        "test_read_attempt_count"
                    ): 0,
                    (
                        "holdout_consumed_for_rerun_policy"
                    ): False,
                }
            ],
        }

    def reserve_before_read(
        self,
    ) -> dict[str, Any]:
        if not self.exists():
            document = (
                self._new_document()
            )

            self._write(
                document
            )

            return document

        document = self.read()

        status = document.get(
            "status"
        )

        attempts = document.get(
            "test_read_attempt_count"
        )

        consumed = document.get(
            "holdout_consumed_for_rerun_policy"
        )

        if (
            status
            == STATUS_PRE_READ_FAILURE
            and attempts == 0
            and consumed is False
        ):
            document[
                "status"
            ] = STATUS_RESERVED

            document[
                "technical_failure"
            ] = None

            document[
                "events"
            ].append(
                {
                    "event": (
                        STATUS_RESERVED
                    ),
                    "reason": (
                        "AUTHORIZED_PRE_READ_"
                        "TECHNICAL_RETRY"
                    ),
                    (
                        "test_read_attempt_count"
                    ): 0,
                    (
                        "holdout_consumed_for_rerun_policy"
                    ): False,
                }
            )

            self._write(
                document
            )

            return document

        raise OneTimeTestCoreError(
            "TEST_LEDGER_ALREADY_EXISTS_NOT_SAFE_TO_RESERVE:"
            f"status={status};"
            f"attempts={attempts};"
            f"consumed={consumed}"
        )

    def mark_read_initiated(
        self,
    ) -> dict[str, Any]:
        document = self.read()

        if (
            document.get(
                "status"
            )
            != STATUS_RESERVED
        ):
            raise OneTimeTestCoreError(
                "TEST_READ_REQUIRES_RESERVED_LEDGER"
            )

        if (
            document.get(
                "test_read_attempt_count"
            )
            != 0
        ):
            raise OneTimeTestCoreError(
                "TEST_READ_ATTEMPT_ALREADY_RECORDED"
            )

        if (
            document.get(
                "holdout_consumed_for_rerun_policy"
            )
            is not False
        ):
            raise OneTimeTestCoreError(
                "TEST_HOLDOUT_ALREADY_CONSUMED"
            )

        document[
            "status"
        ] = STATUS_READ_INITIATED

        document[
            "test_read_attempt_count"
        ] = 1

        document[
            "holdout_consumed_for_rerun_policy"
        ] = True

        document[
            "events"
        ].append(
            {
                "event": (
                    STATUS_READ_INITIATED
                ),
                (
                    "test_read_attempt_count"
                ): 1,
                (
                    "holdout_consumed_for_rerun_policy"
                ): True,
            }
        )

        self._write(
            document
        )

        return document

    def mark_values_loaded(
        self,
        *,
        row_count: int,
    ) -> dict[str, Any]:
        document = self.read()

        if (
            document.get(
                "status"
            )
            != STATUS_READ_INITIATED
        ):
            raise OneTimeTestCoreError(
                "TEST_VALUES_LOADED_REQUIRES_READ_BOUNDARY"
            )

        if (
            document.get(
                "test_read_attempt_count"
            )
            != 1
        ):
            raise OneTimeTestCoreError(
                "TEST_VALUES_LOADED_INVALID_READ_COUNT"
            )

        if (
            document.get(
                "holdout_consumed_for_rerun_policy"
            )
            is not True
        ):
            raise OneTimeTestCoreError(
                "TEST_VALUES_LOADED_WITHOUT_CONSUMPTION"
            )

        if row_count <= 0:
            raise OneTimeTestCoreError(
                "TEST_VALUES_LOADED_INVALID_ROW_COUNT"
            )

        document[
            "status"
        ] = STATUS_VALUES_LOADED

        document[
            "test_values_loaded"
        ] = True

        document[
            "test_row_count"
        ] = int(
            row_count
        )

        document[
            "events"
        ].append(
            {
                "event": (
                    STATUS_VALUES_LOADED
                ),
                "row_count": int(
                    row_count
                ),
            }
        )

        self._write(
            document
        )

        return document

    def mark_complete(
        self,
        *,
        accepted: bool,
        result_fingerprint: str,
    ) -> dict[str, Any]:
        document = self.read()

        if (
            document.get(
                "status"
            )
            != STATUS_VALUES_LOADED
        ):
            raise OneTimeTestCoreError(
                "TEST_COMPLETE_REQUIRES_VALUES_LOADED"
            )

        if (
            document.get(
                "test_values_loaded"
            )
            is not True
        ):
            raise OneTimeTestCoreError(
                "TEST_COMPLETE_WITHOUT_VALUES_LOADED"
            )

        document[
            "status"
        ] = (
            STATUS_COMPLETE_ACCEPTED
            if accepted
            else STATUS_COMPLETE_REJECTED
        )

        document[
            "test_metrics_computed"
        ] = True

        document[
            "test_accepted"
        ] = bool(
            accepted
        )

        document[
            "result_fingerprint"
        ] = result_fingerprint

        document[
            "events"
        ].append(
            {
                "event": (
                    document[
                        "status"
                    ]
                ),
                "test_accepted": (
                    bool(
                        accepted
                    )
                ),
                "result_fingerprint": (
                    result_fingerprint
                ),
            }
        )

        self._write(
            document
        )

        return document

    def mark_technical_failure(
        self,
        *,
        error: str,
        before_read_boundary: bool,
    ) -> dict[str, Any]:
        if not self.exists():
            if not before_read_boundary:
                raise OneTimeTestCoreError(
                    "CONSUMED_FAILURE_REQUIRES_EXISTING_LEDGER"
                )

            document = (
                self._new_document()
            )

        else:
            document = self.read()

        if before_read_boundary:
            if (
                document.get(
                    "test_read_attempt_count"
                )
                != 0
            ):
                raise OneTimeTestCoreError(
                    "PRE_READ_FAILURE_AFTER_READ_ATTEMPT"
                )

            if (
                document.get(
                    "holdout_consumed_for_rerun_policy"
                )
                is not False
            ):
                raise OneTimeTestCoreError(
                    "PRE_READ_FAILURE_AFTER_CONSUMPTION"
                )

            document[
                "status"
            ] = STATUS_PRE_READ_FAILURE

        else:
            if (
                document.get(
                    "test_read_attempt_count"
                )
                != 1
            ):
                raise OneTimeTestCoreError(
                    "CONSUMED_FAILURE_WITHOUT_SINGLE_READ_ATTEMPT"
                )

            if (
                document.get(
                    "holdout_consumed_for_rerun_policy"
                )
                is not True
            ):
                raise OneTimeTestCoreError(
                    "CONSUMED_FAILURE_WITHOUT_CONSUMPTION"
                )

            document[
                "status"
            ] = STATUS_CONSUMED_FAILURE

        document[
            "technical_failure"
        ] = str(
            error
        )

        document[
            "events"
        ].append(
            {
                "event": (
                    document[
                        "status"
                    ]
                ),
                "error": str(
                    error
                ),
            }
        )

        self._write(
            document
        )

        return document


def build_test_result(
    *,
    metrics: Mapping[
        str,
        Any,
    ],
    acceptance: TestAcceptanceDecision,
    row_count: int,
) -> dict[str, Any]:
    normalized_metrics = {
        name: float(
            metrics[
                name
            ]
        )
        for name in REQUIRED_METRICS
    }

    body = {
        "analysis_version": (
            RESULT_ANALYSIS_VERSION
        ),
        "valid": True,
        "status": (
            "ONE_TIME_TEST_ACCEPTED"
            if acceptance.accepted
            else "ONE_TIME_TEST_REJECTED"
        ),
        "bindings": {
            "test_protocol_fingerprint": (
                EXPECTED_TEST_PROTOCOL_FINGERPRINT
            ),
            "validation_result_fingerprint": (
                EXPECTED_VALIDATION_RESULT_FINGERPRINT
            ),
            "validation_freeze_fingerprint": (
                EXPECTED_VALIDATION_FREEZE_FINGERPRINT
            ),
            "model_artifact_sha256": (
                EXPECTED_MODEL_ARTIFACT_SHA256
            ),
            "feature_columns_sha256": (
                EXPECTED_FEATURE_COLUMNS_SHA256
            ),
            "feature_count": (
                EXPECTED_FEATURE_COUNT
            ),
            "probability_class_order": (
                EXPECTED_CLASS_ORDER
            ),
        },
        "test_row_count": int(
            row_count
        ),
        "metrics": (
            normalized_metrics
        ),
        "hard_checks": dict(
            acceptance.hard_checks
        ),
        "scientific_policy": {
            "validation_values_reread": False,
            "model_refit_performed": False,
            "candidate_change_performed": False,
            "feature_change_performed": False,
            "target_change_performed": False,
            "threshold_change_performed": False,
            (
                "probability_calibration_performed"
            ): False,
            "test_consumed": True,
            "test_rerun_authorized": False,
            "shadow_authorized": False,
            "live_authorized": False,
        },
        "decision": {
            "test_accepted": bool(
                acceptance.accepted
            ),
            "test_consumed": True,
            "test_rerun_authorized": False,
            (
                "current_frozen_lineage_"
                "may_be_tuned_from_test"
            ): False,
            "shadow_authorized": False,
            "live_authorized": False,
            "next_action": (
                "FREEZE_ONE_TIME_TEST_RESULT_AND_BUILD_"
                "FINAL_RESEARCH_VERDICT"
                if acceptance.accepted
                else
                "FREEZE_ONE_TIME_TEST_REJECTION_AND_CLOSE_"
                "CURRENT_RESEARCH_LINEAGE"
            ),
        },
    }

    body[
        "result_fingerprint"
    ] = _sha256_json(
        body
    )

    return body


def execute_one_time_test(
    *,
    protocol: Mapping[
        str,
        Any,
    ],
    ledger: TestAccessLedger,
    load_test_batch: Callable[
        [],
        ProtectedTestBatch,
    ],
    predict_probabilities: Callable[
        [np.ndarray],
        tuple[
            np.ndarray,
            Sequence[int],
        ],
    ],
    metric_evaluator: Callable[
        [
            np.ndarray,
            np.ndarray,
        ],
        Mapping[
            str,
            Any,
        ],
    ],
) -> dict[str, Any]:
    if (
        protocol.get(
            "protocol_fingerprint"
        )
        != EXPECTED_TEST_PROTOCOL_FINGERPRINT
    ):
        raise OneTimeTestCoreError(
            "EXECUTION_PROTOCOL_FINGERPRINT_MISMATCH"
        )

    ledger.reserve_before_read()

    # This durable disk transition is the scientific
    # one-time TEST consumption boundary.
    #
    # It is intentionally persisted BEFORE calling the
    # datasource callback.
    ledger.mark_read_initiated()

    try:
        batch = validate_test_batch(
            load_test_batch()
        )

        ledger.mark_values_loaded(
            row_count=batch.X.shape[0]
        )

        (
            probabilities,
            class_order,
        ) = predict_probabilities(
            batch.X
        )

        proba = (
            validate_probability_output(
                probabilities,
                expected_rows=(
                    batch.X.shape[0]
                ),
                model_class_order=(
                    class_order
                ),
            )
        )

        metrics = metric_evaluator(
            batch.y_true,
            proba,
        )

        acceptance = (
            evaluate_acceptance(
                metrics
            )
        )

        result = build_test_result(
            metrics=metrics,
            acceptance=acceptance,
            row_count=batch.X.shape[0],
        )

        ledger.mark_complete(
            accepted=(
                acceptance.accepted
            ),
            result_fingerprint=(
                result[
                    "result_fingerprint"
                ]
            ),
        )

        return result

    except Exception as exc:
        try:
            current = ledger.read()

            if (
                current.get(
                    "status"
                )
                not in {
                    STATUS_COMPLETE_ACCEPTED,
                    STATUS_COMPLETE_REJECTED,
                    STATUS_CONSUMED_FAILURE,
                }
            ):
                ledger.mark_technical_failure(
                    error=(
                        f"{type(exc).__name__}:"
                        f"{exc}"
                    ),
                    before_read_boundary=False,
                )

        except Exception as ledger_exc:
            raise OneTimeTestCoreError(
                "TEST_EXECUTION_FAILED_AND_LEDGER_FAILURE:"
                f"execution={type(exc).__name__}:{exc};"
                f"ledger={type(ledger_exc).__name__}:"
                f"{ledger_exc}"
            ) from exc

        raise


def build_core_attestation(
    protocol: Mapping[
        str,
        Any,
    ],
    *,
    source_sha256: str,
) -> dict[str, Any]:
    if (
        protocol.get(
            "protocol_fingerprint"
        )
        != EXPECTED_TEST_PROTOCOL_FINGERPRINT
    ):
        raise OneTimeTestCoreError(
            "ATTESTATION_PROTOCOL_FINGERPRINT_MISMATCH"
        )

    document = {
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "valid": True,
        "status": (
            ATTESTATION_STATUS
        ),
        "test_protocol_fingerprint": (
            EXPECTED_TEST_PROTOCOL_FINGERPRINT
        ),
        "validation_result_fingerprint": (
            EXPECTED_VALIDATION_RESULT_FINGERPRINT
        ),
        "validation_freeze_fingerprint": (
            EXPECTED_VALIDATION_FREEZE_FINGERPRINT
        ),
        "model_artifact_sha256": (
            EXPECTED_MODEL_ARTIFACT_SHA256
        ),
        "feature_columns_sha256": (
            EXPECTED_FEATURE_COLUMNS_SHA256
        ),
        "source_sha256": (
            source_sha256
        ),
        "verified_properties": {
            (
                "persistent_ledger_implemented"
            ): True,
            (
                "ledger_written_before_"
                "test_read_callback"
            ): True,
            (
                "read_initiation_is_"
                "consumption_boundary"
            ): True,
            (
                "pre_read_failure_retriable_"
                "only_before_consumption"
            ): True,
            (
                "post_read_failure_consumes_test"
            ): True,
            (
                "second_performance_driven_"
                "read_blocked"
            ): True,
            (
                "test_acceptance_uses_"
                "train_derived_floors"
            ): True,
            (
                "validation_metrics_do_not_"
                "raise_test_floors"
            ): True,
            (
                "validation_reread_forbidden"
            ): True,
            "real_test_values_accessed": False,
        },
        "decision": {
            (
                "test_core_and_ledger_implemented"
            ): True,
            (
                "bounded_test_source_"
                "implementation_authorized_next"
            ): True,
            "test_execution_authorized": False,
            "test_values_accessed": False,
            "validation_rerun_authorized": False,
            "shadow_authorized": False,
            "live_authorized": False,
            "next_action": (
                "IMPLEMENT_AND_SYNTHETICALLY_TEST_"
                "DEDICATED_BOUNDED_REAL_TEST_SOURCE"
            ),
        },
    }

    document[
        "attestation_fingerprint"
    ] = _sha256_json(
        document
    )

    return document


def write_json_once(
    path: Path,
    document: Mapping[
        str,
        Any,
    ],
) -> None:
    payload = (
        json.dumps(
            document,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    )

    if path.exists():
        existing = _load_json(
            path
        )

        if (
            _canonical_json(
                existing
            )
            != _canonical_json(
                document
            )
        ):
            raise OneTimeTestCoreError(
                "FROZEN_JSON_ALREADY_EXISTS_"
                "WITH_DIFFERENT_CONTENT:"
                f"{path}"
            )

        return

    path.write_text(
        payload,
        encoding="utf-8",
    )


def main() -> int:
    protocol = (
        load_and_verify_frozen_test_protocol(
            PROTOCOL_PATH
        )
    )

    source_sha256 = (
        _sha256_file(
            Path(
                __file__
            ).resolve()
        )
    )

    attestation = (
        build_core_attestation(
            protocol,
            source_sha256=(
                source_sha256
            ),
        )
    )

    write_json_once(
        ATTESTATION_PATH,
        attestation,
    )

    print(
        f"status={attestation['status']}"
    )

    print(
        "source_sha256="
        f"{attestation['source_sha256']}"
    )

    print(
        "attestation_fingerprint="
        f"{attestation['attestation_fingerprint']}"
    )

    print(
        f"output={ATTESTATION_PATH}"
    )

    print(
        "test_execution_authorized=false"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )