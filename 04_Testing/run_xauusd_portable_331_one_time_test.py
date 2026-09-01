from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Mapping, Sequence, cast

import joblib
import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.metrics import (
    balanced_accuracy_score,
    f1_score,
    log_loss,
    precision_recall_fscore_support,
)


ANALYSIS_VERSION = "XAUUSD_PORTABLE_331_ONE_TIME_TEST_RUNNER_V1"

REPO_ROOT = Path(__file__).resolve().parents[1]

CORE_PATH = (
    REPO_ROOT
    / "04_Testing"
    / "xauusd_portable_331_one_time_test_core.py"
)

SOURCE_PATH = (
    REPO_ROOT
    / "04_Testing"
    / "xauusd_portable_331_authorized_test_source.py"
)

LOADER_PATH = (
    REPO_ROOT
    / "02_AI"
    / "Dataset"
    / "portable_331_training_input_loader.py"
)

PROTOCOL_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_test_protocol.json"
)

CORE_ATTESTATION_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_test_core_attestation.json"
)

SOURCE_ATTESTATION_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_authorized_test_source_attestation.json"
)

VALIDATION_RESULT_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_validation_result.json"
)

VALIDATION_FREEZE_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_validation_result_freeze.json"
)

MODEL_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_c04_full_train_model.joblib"
)

DEFAULT_PREFLIGHT_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_test_preflight.json"
)

DEFAULT_LEDGER_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_test_access_ledger.json"
)

DEFAULT_RESULT_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_test_result.json"
)


EXPECTED_WINNER_ID = (
    "C04_FLAT_EXTRA_TREES_CONSTRAINED"
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

EXPECTED_MODEL_VERIFICATION_RECORD_SHA256 = (
    "a2759a429b90998a7d24c8b217e570813e36dcf43df5de6cf98daf875b8678ef"
)

EXPECTED_LOADER_SOURCE_SHA256 = (
    "49c86c269f2742fec7c6991eaf7a8a9c0466066a3db230a80375ba2e2c33680c"
)

EXPECTED_FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

EXPECTED_FEATURE_COUNT = 331

EXPECTED_CLASS_ORDER = [
    -1,
    0,
    1,
]

EXPECTED_SPLIT_COLUMN = "dataset_split"
EXPECTED_TARGET_COLUMN = "target_class"


class OneTimeTestRunnerError(RuntimeError):
    """Raised when one-shot TEST safety cannot be proven."""


def _canonical_json(
    value: Any,
) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _canonical_sha256(
    value: Any,
) -> str:
    return hashlib.sha256(
        _canonical_json(
            value
        ).encode(
            "utf-8"
        )
    ).hexdigest()


def _sha256_file(
    path: Path,
) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def _read_json_auto(
    path: Path,
) -> dict[str, Any]:
    if not path.is_file():
        raise OneTimeTestRunnerError(
            f"REQUIRED_JSON_MISSING:{path}"
        )

    raw = path.read_bytes()

    last_error: Exception | None = None

    for encoding in (
        "utf-8",
        "utf-8-sig",
        "utf-16",
    ):
        try:
            value = json.loads(
                raw.decode(
                    encoding
                )
            )

            if not isinstance(
                value,
                dict,
            ):
                raise OneTimeTestRunnerError(
                    f"JSON_ROOT_NOT_OBJECT:{path}"
                )

            return value

        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            last_error = exc

    raise OneTimeTestRunnerError(
        f"JSON_DECODE_FAILED:{path}:{last_error}"
    )


def _write_json_atomic(
    path: Path,
    document: Mapping[str, Any],
) -> None:
    path.parent.mkdir(
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

    temporary = path.with_name(
        path.name
        + ".tmp"
    )

    temporary.write_text(
        payload,
        encoding="utf-8",
    )

    os.replace(
        temporary,
        path,
    )


def _load_module(
    path: Path,
    module_name: str,
) -> ModuleType:
    if not path.is_file():
        raise OneTimeTestRunnerError(
            f"MODULE_SOURCE_MISSING:{path}"
        )

    spec = (
        importlib.util
        .spec_from_file_location(
            module_name,
            path,
        )
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise OneTimeTestRunnerError(
            f"MODULE_IMPORT_SPEC_FAILED:{path}"
        )

    module = (
        importlib.util
        .module_from_spec(
            spec
        )
    )

    sys.modules[
        spec.name
    ] = module

    spec.loader.exec_module(
        module
    )

    return module


def _required_mapping(
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
        raise OneTimeTestRunnerError(
            f"REQUIRED_MAPPING_MISSING:{key}"
        )

    return value


def _contains_scalar(
    node: Any,
    expected: Any,
) -> bool:
    if isinstance(
        node,
        Mapping,
    ):
        return any(
            _contains_scalar(
                value,
                expected,
            )
            for value
            in node.values()
        )

    if isinstance(
        node,
        list,
    ):
        return any(
            _contains_scalar(
                value,
                expected,
            )
            for value
            in node
        )

    if isinstance(
        expected,
        bool,
    ):
        return (
            isinstance(
                node,
                bool,
            )
            and node
            is expected
        )

    return node == expected


def _values_for_key(
    node: Any,
    key: str,
) -> list[Any]:
    values: list[Any] = []

    if isinstance(
        node,
        Mapping,
    ):
        for (
            child_key,
            child,
        ) in node.items():
            if child_key == key:
                values.append(
                    child
                )

            values.extend(
                _values_for_key(
                    child,
                    key,
                )
            )

    elif isinstance(
        node,
        list,
    ):
        for child in node:
            values.extend(
                _values_for_key(
                    child,
                    key,
                )
            )

    return values


def _require_key_value(
    document: Mapping[str, Any],
    key: str,
    expected: Any,
) -> None:
    values = _values_for_key(
        document,
        key,
    )

    if isinstance(
        expected,
        bool,
    ):
        matched = any(
            isinstance(
                value,
                bool,
            )
            and value
            is expected
            for value
            in values
        )

    else:
        matched = any(
            value
            == expected
            for value
            in values
        )

    if not matched:
        raise OneTimeTestRunnerError(
            "REQUIRED_STATE_MISSING:"
            f"{key}="
            f"{expected!r};"
            f"observed="
            f"{values!r}"
        )


def _require_scalar(
    document: Mapping[str, Any],
    expected: Any,
    label: str,
) -> None:
    if not _contains_scalar(
        document,
        expected,
    ):
        raise OneTimeTestRunnerError(
            "REQUIRED_IDENTITY_MISSING:"
            f"{label}:"
            f"{expected}"
        )


def _validate_ledger_state_before_execution(
    ledger_path: Path,
    result_path: Path,
) -> dict[str, Any]:
    if result_path.exists():
        return {
            "state": (
                "RESULT_ALREADY_EXISTS"
            ),
            (
                "execution_recovery_allowed"
            ): False,
            (
                "test_read_attempt_count"
            ): None,
            (
                "holdout_consumed_for_rerun_policy"
            ): None,
        }

    if not ledger_path.exists():
        return {
            "state": (
                "ABSENT"
            ),
            (
                "execution_recovery_allowed"
            ): True,
            (
                "test_read_attempt_count"
            ): 0,
            (
                "holdout_consumed_for_rerun_policy"
            ): False,
        }

    ledger = _read_json_auto(
        ledger_path
    )

    attempts = ledger.get(
        "test_read_attempt_count"
    )

    consumed = ledger.get(
        "holdout_consumed_for_rerun_policy"
    )

    status = ledger.get(
        "status"
    )

    recoverable = (
        status
        == "PRE_READ_TECHNICAL_FAILURE"
        and attempts == 0
        and consumed is False
    )

    return {
        "state": str(
            status
        ),
        (
            "execution_recovery_allowed"
        ): recoverable,
        (
            "test_read_attempt_count"
        ): attempts,
        (
            "holdout_consumed_for_rerun_policy"
        ): consumed,
    }


def _validate_attestation_chain(
    *,
    ledger_path: Path,
    result_path: Path,
) -> dict[str, Any]:
    required_files = [
        CORE_PATH,
        SOURCE_PATH,
        LOADER_PATH,
        PROTOCOL_PATH,
        CORE_ATTESTATION_PATH,
        SOURCE_ATTESTATION_PATH,
        VALIDATION_RESULT_PATH,
        VALIDATION_FREEZE_PATH,
        MODEL_PATH,
    ]

    missing = [
        str(
            path
        )
        for path
        in required_files
        if not path.is_file()
    ]

    if missing:
        raise OneTimeTestRunnerError(
            "REQUIRED_PREFLIGHT_FILE_MISSING:"
            f"{missing}"
        )

    actual_model_sha256 = (
        _sha256_file(
            MODEL_PATH
        )
    )

    if (
        actual_model_sha256
        != EXPECTED_MODEL_ARTIFACT_SHA256
    ):
        raise OneTimeTestRunnerError(
            "MODEL_ARTIFACT_SHA256_MISMATCH:"
            f"expected="
            f"{EXPECTED_MODEL_ARTIFACT_SHA256};"
            f"actual="
            f"{actual_model_sha256}"
        )

    actual_loader_sha256 = (
        _sha256_file(
            LOADER_PATH
        )
    )

    if (
        actual_loader_sha256
        != EXPECTED_LOADER_SOURCE_SHA256
    ):
        raise OneTimeTestRunnerError(
            "LOADER_SOURCE_SHA256_MISMATCH:"
            f"expected="
            f"{EXPECTED_LOADER_SOURCE_SHA256};"
            f"actual="
            f"{actual_loader_sha256}"
        )

    core_source_sha256 = (
        _sha256_file(
            CORE_PATH
        )
    )

    source_source_sha256 = (
        _sha256_file(
            SOURCE_PATH
        )
    )

    protocol = _read_json_auto(
        PROTOCOL_PATH
    )

    core_attestation = (
        _read_json_auto(
            CORE_ATTESTATION_PATH
        )
    )

    source_attestation = (
        _read_json_auto(
            SOURCE_ATTESTATION_PATH
        )
    )

    validation_result = (
        _read_json_auto(
            VALIDATION_RESULT_PATH
        )
    )

    validation_freeze = (
        _read_json_auto(
            VALIDATION_FREEZE_PATH
        )
    )

    if (
        protocol.get(
            "valid"
        )
        is not True
        or protocol.get(
            "status"
        )
        != "ONE_TIME_TEST_PROTOCOL_FROZEN"
        or protocol.get(
            "protocol_fingerprint"
        )
        != EXPECTED_TEST_PROTOCOL_FINGERPRINT
    ):
        raise OneTimeTestRunnerError(
            "FROZEN_TEST_PROTOCOL_MISMATCH"
        )

    _require_key_value(
        protocol,
        "test_execution_authorized",
        False,
    )

    _require_key_value(
        protocol,
        "validation_rerun_authorized",
        False,
    )

    if (
        core_attestation.get(
            "valid"
        )
        is not True
        or core_attestation.get(
            "status"
        )
        != (
            "ONE_TIME_TEST_CORE_"
            "IMPLEMENTED_NOT_REAL_EXECUTED"
        )
    ):
        raise OneTimeTestRunnerError(
            "TEST_CORE_ATTESTATION_INVALID"
        )

    _require_scalar(
        core_attestation,
        EXPECTED_TEST_PROTOCOL_FINGERPRINT,
        "core_test_protocol_fingerprint",
    )

    _require_scalar(
        core_attestation,
        core_source_sha256,
        "core_source_sha256",
    )

    _require_key_value(
        core_attestation,
        "test_execution_authorized",
        False,
    )

    _require_key_value(
        core_attestation,
        "test_values_accessed",
        False,
    )

    if (
        source_attestation.get(
            "valid"
        )
        is not True
        or source_attestation.get(
            "status"
        )
        != (
            "AUTHORIZED_TEST_SOURCE_"
            "IMPLEMENTED_NOT_REAL_EXECUTED"
        )
    ):
        raise OneTimeTestRunnerError(
            "TEST_SOURCE_ATTESTATION_INVALID"
        )

    _require_scalar(
        source_attestation,
        EXPECTED_TEST_PROTOCOL_FINGERPRINT,
        "source_test_protocol_fingerprint",
    )

    _require_scalar(
        source_attestation,
        core_source_sha256,
        "bound_test_core_source_sha256",
    )

    _require_scalar(
        source_attestation,
        source_source_sha256,
        "authorized_test_source_sha256",
    )

    _require_key_value(
        source_attestation,
        "real_test_values_accessed",
        False,
    )

    _require_key_value(
        source_attestation,
        "test_execution_authorized",
        False,
    )

    _require_scalar(
        validation_result,
        EXPECTED_VALIDATION_RESULT_FINGERPRINT,
        "validation_result_fingerprint",
    )

    _require_scalar(
        validation_result,
        EXPECTED_MODEL_VERIFICATION_RECORD_SHA256,
        (
            "inherited_model_verification_"
            "record_fingerprint"
        ),
    )

    _require_key_value(
        validation_result,
        "validation_accepted",
        True,
    )

    _require_key_value(
        validation_result,
        "validation_consumed",
        True,
    )

    _require_key_value(
        validation_result,
        "validation_rerun_authorized",
        False,
    )

    _require_scalar(
        validation_freeze,
        EXPECTED_VALIDATION_FREEZE_FINGERPRINT,
        "validation_freeze_fingerprint",
    )

    _require_scalar(
        validation_freeze,
        EXPECTED_VALIDATION_RESULT_FINGERPRINT,
        "bound_validation_result_fingerprint",
    )

    _require_key_value(
        validation_freeze,
        "validation_result_frozen",
        True,
    )

    _require_key_value(
        validation_freeze,
        "validation_consumed",
        True,
    )

    _require_key_value(
        validation_freeze,
        "validation_rerun_authorized",
        False,
    )

    _require_key_value(
        validation_freeze,
        (
            "test_runner_implementation_"
            "authorized_next"
        ),
        True,
    )

    _require_key_value(
        validation_freeze,
        "test_execution_authorized",
        False,
    )

    return {
        "protocol": (
            protocol
        ),
        "core_attestation": (
            core_attestation
        ),
        "source_attestation": (
            source_attestation
        ),
        "validation_result": (
            validation_result
        ),
        "validation_freeze": (
            validation_freeze
        ),
        "core_source_sha256": (
            core_source_sha256
        ),
        "source_source_sha256": (
            source_source_sha256
        ),
        "loader_source_sha256": (
            actual_loader_sha256
        ),
        "model_artifact_sha256": (
            actual_model_sha256
        ),
        "ledger_state": (
            _validate_ledger_state_before_execution(
                ledger_path,
                result_path,
            )
        ),
    }


def build_preflight(
    *,
    ledger_path: Path = DEFAULT_LEDGER_PATH,
    result_path: Path = DEFAULT_RESULT_PATH,
) -> dict[str, Any]:
    chain = (
        _validate_attestation_chain(
            ledger_path=ledger_path,
            result_path=result_path,
        )
    )

    ledger_state = chain[
        "ledger_state"
    ]

    execution_recovery_allowed = (
        ledger_state[
            "execution_recovery_allowed"
        ]
        is True
    )

    preflight_record = {
        "winner_candidate_id": (
            EXPECTED_WINNER_ID
        ),
        (
            "test_protocol_fingerprint_sha256"
        ): (
            EXPECTED_TEST_PROTOCOL_FINGERPRINT
        ),
        (
            "validation_result_fingerprint_sha256"
        ): (
            EXPECTED_VALIDATION_RESULT_FINGERPRINT
        ),
        (
            "validation_freeze_fingerprint_sha256"
        ): (
            EXPECTED_VALIDATION_FREEZE_FINGERPRINT
        ),
        "model_artifact_sha256": (
            EXPECTED_MODEL_ARTIFACT_SHA256
        ),
        (
            "model_verification_record_"
            "fingerprint_sha256"
        ): (
            EXPECTED_MODEL_VERIFICATION_RECORD_SHA256
        ),
        "portable_loader_source_sha256": (
            EXPECTED_LOADER_SOURCE_SHA256
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
        "test_core_source_sha256": (
            chain[
                "core_source_sha256"
            ]
        ),
        (
            "authorized_test_source_sha256"
        ): (
            chain[
                "source_source_sha256"
            ]
        ),
        (
            "core_attestation_canonical_sha256"
        ): (
            _canonical_sha256(
                chain[
                    "core_attestation"
                ]
            )
        ),
        (
            "source_attestation_canonical_sha256"
        ): (
            _canonical_sha256(
                chain[
                    "source_attestation"
                ]
            )
        ),
        (
            "validation_result_canonical_sha256"
        ): (
            _canonical_sha256(
                chain[
                    "validation_result"
                ]
            )
        ),
        (
            "validation_freeze_canonical_sha256"
        ): (
            _canonical_sha256(
                chain[
                    "validation_freeze"
                ]
            )
        ),
        "ledger_filename": (
            ledger_path.name
        ),
        "result_filename": (
            result_path.name
        ),
        "ledger_state": (
            ledger_state[
                "state"
            ]
        ),
        (
            "ledger_execution_recovery_allowed"
        ): (
            execution_recovery_allowed
        ),
        (
            "test_read_attempt_count_before_execution"
        ): (
            ledger_state[
                "test_read_attempt_count"
            ]
        ),
        (
            "holdout_consumed_before_execution"
        ): (
            ledger_state[
                "holdout_consumed_for_rerun_policy"
            ]
        ),
        "prediction_rule": (
            "ARGMAX_FROZEN_MODEL_PROBABILITIES"
        ),
        (
            "test_acceptance_threshold_origin"
        ): (
            "TRAIN_ONLY_FROZEN_PRE_VALIDATION"
        ),
        (
            "validation_values_reread_allowed"
        ): False,
        "model_refit_allowed": False,
        "threshold_search_allowed": False,
        (
            "probability_calibration_allowed"
        ): False,
        "candidate_change_allowed": False,
        "feature_change_allowed": False,
        "target_change_allowed": False,
    }

    preflight_fingerprint = (
        _canonical_sha256(
            preflight_record
        )
    )

    return {
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "valid": True,
        "research_scope": (
            "FINAL_DRY_PREFLIGHT_BEFORE_"
            "FIRST_AND_ONLY_REAL_PORTABLE_"
            "TEST_READ"
        ),
        "preflight_record": (
            preflight_record
        ),
        "preflight_fingerprint": {
            "canonicalization": (
                "JSON_SORT_KEYS_COMPACT_UTF8_SHA256"
            ),
            "sha256": (
                preflight_fingerprint
            ),
        },
        "decision": {
            "status": (
                "ONE_TIME_TEST_DRY_PREFLIGHT_READY"
                if execution_recovery_allowed
                else (
                    "ONE_TIME_TEST_EXECUTION_BLOCKED"
                )
            ),
            "dry_preflight_completed": True,
            "real_test_executed": False,
            "real_test_values_loaded": False,
            "real_test_metrics_computed": False,
            (
                "real_test_execution_authorized_next"
            ): (
                execution_recovery_allowed
            ),
            (
                "validation_reread_authorized"
            ): False,
            "test_consumed": False,
            "test_rerun_authorized": False,
            "shadow_authorized": False,
            "live_authorized": False,
            "next_action": (
                "FREEZE_THIS_PREFLIGHT_FINGERPRINT_"
                "THEN_EXECUTE_EXACTLY_ONE_REAL_TEST_RUN"
                if execution_recovery_allowed
                else (
                    "STOP_TEST_EXECUTION_BECAUSE_"
                    "LEDGER_OR_RESULT_STATE_IS_"
                    "NOT_PRISTINE"
                )
            ),
        },
        "scientific_policy": {
            (
                "dataset_structural_read_performed"
            ): False,
            "train_feature_values_loaded": False,
            "train_target_values_loaded": False,
            (
                "portable_validation_feature_"
                "values_loaded"
            ): False,
            (
                "portable_validation_target_"
                "values_loaded"
            ): False,
            (
                "portable_validation_metrics_"
                "computed"
            ): False,
            (
                "portable_test_feature_values_loaded"
            ): False,
            (
                "portable_test_target_values_loaded"
            ): False,
            (
                "portable_test_metrics_computed"
            ): False,
            "model_fit_performed": False,
            "model_refit_performed": False,
            "threshold_search_performed": False,
            (
                "probability_calibration_performed"
            ): False,
            "feature_selection_performed": False,
            "candidate_registry_changed": False,
            "model_artifact_modified": False,
            (
                "execution_integration_modified"
            ): False,
            "risk_engine_modified": False,
            "orders_sent": False,
            "shadow_authorized": False,
            "live_authorized": False,
        },
    }


def validate_stored_preflight(
    *,
    preflight_path: Path,
    expected_fingerprint: str,
    ledger_path: Path,
    result_path: Path,
) -> dict[str, Any]:
    stored = _read_json_auto(
        preflight_path
    )

    if (
        stored.get(
            "analysis_version"
        )
        != ANALYSIS_VERSION
    ):
        raise OneTimeTestRunnerError(
            "Stored preflight analysis "
            "version mismatch."
        )

    if (
        stored.get(
            "valid"
        )
        is not True
    ):
        raise OneTimeTestRunnerError(
            "Stored preflight must be valid=true."
        )

    fingerprint = _required_mapping(
        stored,
        "preflight_fingerprint",
    )

    if (
        fingerprint.get(
            "sha256"
        )
        != expected_fingerprint
    ):
        raise OneTimeTestRunnerError(
            "Expected preflight fingerprint "
            "does not match stored preflight."
        )

    preflight_record = (
        _required_mapping(
            stored,
            "preflight_record",
        )
    )

    if (
        _canonical_sha256(
            preflight_record
        )
        != expected_fingerprint
    ):
        raise OneTimeTestRunnerError(
            "Stored preflight content "
            "fingerprint mismatch."
        )

    decision = _required_mapping(
        stored,
        "decision",
    )

    if (
        decision.get(
            "real_test_execution_authorized_next"
        )
        is not True
    ):
        raise OneTimeTestRunnerError(
            "Stored preflight does not authorize "
            "one-time TEST execution."
        )

    current = build_preflight(
        ledger_path=ledger_path,
        result_path=result_path,
    )

    current_fingerprint = (
        current[
            "preflight_fingerprint"
        ][
            "sha256"
        ]
    )

    if (
        current_fingerprint
        != expected_fingerprint
    ):
        raise OneTimeTestRunnerError(
            "Current provenance/ledger state "
            "differs from frozen dry preflight."
        )

    if (
        current[
            "preflight_record"
        ]
        != preflight_record
    ):
        raise OneTimeTestRunnerError(
            "Current preflight record differs "
            "from frozen preflight."
        )

    return stored


def _load_loader_class() -> type:
    module = _load_module(
        LOADER_PATH,
        "xauusd_test_runner_loader",
    )

    loader_class = getattr(
        module,
        "Portable331TrainingInputLoader",
        None,
    )

    if not isinstance(
        loader_class,
        type,
    ):
        raise OneTimeTestRunnerError(
            "Portable331TrainingInputLoader "
            "class missing."
        )

    return loader_class


class ArtifactBoundedTestSource:
    def __init__(
        self,
        canonical_root: Path,
        *,
        core_module: Any,
        source_module: Any,
        loader_class: type | None = None,
        read_csv: Callable[
            ...,
            pd.DataFrame,
        ] = pd.read_csv,
    ) -> None:
        self.canonical_root = Path(
            canonical_root
        )

        self.core_module = (
            core_module
        )

        self.source_module = (
            source_module
        )

        self.loader_class = (
            loader_class
            if loader_class is not None
            else _load_loader_class()
        )

        self.read_csv = (
            read_csv
        )

        self.last_evidence: (
            dict[str, Any]
            | None
        ) = None

    def load(
        self,
    ) -> Any:
        loader = self.loader_class(
            self.canonical_root
        )

        try:
            (
                dataset_path,
                manifest_path,
                manifest,
            ) = (
                loader
                ._discover_exact_artifact()
            )

        except Exception as exc:
            raise OneTimeTestRunnerError(
                "Cannot discover exact frozen "
                "portable artifact."
            ) from exc

        try:
            (
                feature_columns,
                target_columns,
            ) = (
                loader
                ._validate_manifest(
                    manifest
                )
            )

        except Exception as exc:
            raise OneTimeTestRunnerError(
                "Frozen portable manifest "
                "validation failed."
            ) from exc

        feature_columns = [
            str(
                value
            )
            for value
            in feature_columns
        ]

        if (
            len(
                feature_columns
            )
            != EXPECTED_FEATURE_COUNT
        ):
            raise OneTimeTestRunnerError(
                "Manifest feature count "
                "must equal 331."
            )

        if (
            len(
                set(
                    feature_columns
                )
            )
            != len(
                feature_columns
            )
        ):
            raise OneTimeTestRunnerError(
                "Manifest feature columns "
                "contain duplicates."
            )

        try:
            feature_sha = (
                loader
                ._feature_columns_sha256(
                    feature_columns
                )
            )

        except Exception as exc:
            raise OneTimeTestRunnerError(
                "Cannot recompute manifest "
                "feature-column SHA256."
            ) from exc

        if (
            feature_sha
            != EXPECTED_FEATURE_COLUMNS_SHA256
        ):
            raise OneTimeTestRunnerError(
                "Manifest feature-column "
                "SHA256 mismatch."
            )

        normalized_target_columns = [
            str(
                value
            )
            for value
            in target_columns
        ]

        if (
            EXPECTED_TARGET_COLUMN
            not in normalized_target_columns
        ):
            raise OneTimeTestRunnerError(
                "Frozen manifest target_class "
                "column missing."
            )

        try:
            split_frame = self.read_csv(
                dataset_path,
                usecols=[
                    EXPECTED_SPLIT_COLUMN
                ],
                low_memory=False,
            )

        except Exception as exc:
            raise OneTimeTestRunnerError(
                "Cannot perform structural "
                "dataset_split read."
            ) from exc

        if (
            list(
                split_frame.columns
            )
            != [
                EXPECTED_SPLIT_COLUMN
            ]
        ):
            raise OneTimeTestRunnerError(
                "Structural split read loaded "
                "unexpected columns."
            )

        try:
            loader._validate_split_series(
                split_frame[
                    EXPECTED_SPLIT_COLUMN
                ]
            )

        except Exception as exc:
            raise OneTimeTestRunnerError(
                "Existing loader split "
                "validation failed."
            ) from exc

        split_labels = (
            split_frame[
                EXPECTED_SPLIT_COLUMN
            ]
            .astype(
                "string"
            )
            .str.strip()
            .str.upper()
            .tolist()
        )

        read_evidence: dict[
            str,
            int,
        ] = {}

        def read_bounded_rows(
            start: int,
            stop: int,
            columns: Sequence[str],
        ) -> pd.DataFrame:
            if stop <= start:
                raise OneTimeTestRunnerError(
                    "Invalid bounded TEST "
                    "row range."
                )

            try:
                frame = self.read_csv(
                    dataset_path,
                    usecols=list(
                        columns
                    ),
                    skiprows=range(
                        1,
                        start + 1,
                    ),
                    nrows=(
                        stop
                        - start
                    ),
                    low_memory=False,
                )

            except Exception as exc:
                raise OneTimeTestRunnerError(
                    "Cannot load bounded "
                    "TEST block."
                ) from exc

            try:
                normalized_target = (
                    loader
                    ._normalize_target_class_array(
                        frame[
                            EXPECTED_TARGET_COLUMN
                        ]
                    )
                )

            except Exception as exc:
                raise OneTimeTestRunnerError(
                    "Cannot normalize bounded "
                    "TEST target_class."
                ) from exc

            frame = frame.copy()

            frame[
                EXPECTED_TARGET_COLUMN
            ] = normalized_target

            read_evidence.update(
                {
                    "start": int(
                        start
                    ),
                    "stop": int(
                        stop
                    ),
                    "rows": int(
                        stop
                        - start
                    ),
                }
            )

            return frame

        adapter = (
            self.source_module
            .AuthorizedBoundedTestSource(
                split_labels=(
                    split_labels
                ),
                feature_columns=(
                    feature_columns
                ),
                feature_columns_sha256=(
                    feature_sha
                ),
                read_bounded_rows=(
                    read_bounded_rows
                ),
                target_column=(
                    EXPECTED_TARGET_COLUMN
                ),
                split_column=(
                    EXPECTED_SPLIT_COLUMN
                ),
                test_core_module=(
                    self.core_module
                ),
            )
        )

        batch = (
            adapter
            .load_protected_test_batch()
        )

        if not read_evidence:
            raise OneTimeTestRunnerError(
                "Bounded TEST reader "
                "evidence missing."
            )

        self.last_evidence = {
            "dataset_path_name": (
                Path(
                    dataset_path
                ).name
            ),
            "manifest_path_name": (
                Path(
                    manifest_path
                ).name
            ),
            "feature_count": (
                len(
                    feature_columns
                )
            ),
            "feature_columns_sha256": (
                feature_sha
            ),
            "target_column": (
                EXPECTED_TARGET_COLUMN
            ),
            "split_window": {
                "test_start": (
                    read_evidence[
                        "start"
                    ]
                ),
                "test_stop_exclusive": (
                    read_evidence[
                        "stop"
                    ]
                ),
                "test_rows": (
                    read_evidence[
                        "rows"
                    ]
                ),
            },
            "read_policy": {
                (
                    "structural_read_columns"
                ): [
                    EXPECTED_SPLIT_COLUMN
                ],
                "value_read_split": (
                    "TEST"
                ),
                (
                    "value_read_start_data_row"
                ): (
                    read_evidence[
                        "start"
                    ]
                ),
                "value_read_rows": (
                    read_evidence[
                        "rows"
                    ]
                ),
                (
                    "value_read_stop_exclusive"
                ): (
                    read_evidence[
                        "stop"
                    ]
                ),
                (
                    "parser_reads_final_test_"
                    "block_only"
                ): True,
                (
                    "validation_feature_"
                    "values_loaded"
                ): False,
                (
                    "validation_target_"
                    "values_loaded"
                ): False,
                (
                    "train_feature_values_loaded"
                ): False,
                (
                    "train_target_values_loaded"
                ): False,
            },
        }

        return batch


def _predict_probabilities(
    model: Any,
    X: np.ndarray,
) -> tuple[
    np.ndarray,
    Sequence[int],
]:
    classes = getattr(
        model,
        "classes_",
        None,
    )

    if classes is None:
        raise OneTimeTestRunnerError(
            "Frozen model classes_ missing."
        )

    class_order = [
        int(
            value
        )
        for value
        in np.asarray(
            classes
        ).tolist()
    ]

    if (
        class_order
        != EXPECTED_CLASS_ORDER
    ):
        raise OneTimeTestRunnerError(
            "Frozen model class order mismatch:"
            f"{class_order}"
        )

    n_features = getattr(
        model,
        "n_features_in_",
        None,
    )

    if (
        n_features is not None
        and int(
            n_features
        )
        != EXPECTED_FEATURE_COUNT
    ):
        raise OneTimeTestRunnerError(
            "Frozen model feature-count mismatch:"
            f"{n_features}"
        )

    probabilities = np.asarray(
        model.predict_proba(
            X
        ),
        dtype=np.float64,
    )

    return (
        probabilities,
        class_order,
    )


def evaluate_test_metrics(
    y_true: np.ndarray,
    probabilities: np.ndarray,
) -> dict[str, float]:
    y = np.asarray(
        y_true,
        dtype=np.int8,
    )

    proba = np.asarray(
        probabilities,
        dtype=np.float64,
    )

    if (
        proba.ndim
        != 2
        or proba.shape[
            0
        ]
        != y.shape[
            0
        ]
        or proba.shape[
            1
        ]
        != len(
            EXPECTED_CLASS_ORDER
        )
    ):
        raise OneTimeTestRunnerError(
            "Metric evaluator "
            "probability shape mismatch."
        )

    predictions = (
        np.asarray(
            EXPECTED_CLASS_ORDER,
            dtype=np.int8,
        )[
            np.argmax(
                proba,
                axis=1,
            )
        ]
    )

    (
        precision_raw,
        recall_raw,
        f1_raw,
        _,
    ) = (
        precision_recall_fscore_support(
            y,
            predictions,
            labels=(
                EXPECTED_CLASS_ORDER
            ),
            average=None,
            zero_division=0,
        )
    )

    precision: NDArray[
        np.float64
    ] = np.asarray(
        cast(
            Any,
            precision_raw,
        ),
        dtype=np.float64,
    )

    recall: NDArray[
        np.float64
    ] = np.asarray(
        cast(
            Any,
            recall_raw,
        ),
        dtype=np.float64,
    )

    f1_values: NDArray[
        np.float64
    ] = np.asarray(
        cast(
            Any,
            f1_raw,
        ),
        dtype=np.float64,
    )

    if (
        precision.shape
        != (
            3,
        )
        or recall.shape
        != (
            3,
        )
        or f1_values.shape
        != (
            3,
        )
    ):
        raise OneTimeTestRunnerError(
            "Per-class metric vector "
            "shape mismatch."
        )

    one_hot = np.zeros_like(
        proba,
        dtype=np.float64,
    )

    class_to_index = {
        value: index
        for (
            index,
            value,
        )
        in enumerate(
            EXPECTED_CLASS_ORDER
        )
    }

    for (
        row_index,
        value,
    ) in enumerate(
        y.tolist()
    ):
        target_value = int(
            value
        )

        if (
            target_value
            not in class_to_index
        ):
            raise OneTimeTestRunnerError(
                "Metric evaluator target class "
                "outside frozen domain."
            )

        one_hot[
            row_index,
            class_to_index[
                target_value
            ],
        ] = 1.0

    brier = float(
        np.mean(
            np.sum(
                (
                    proba
                    - one_hot
                )
                ** 2,
                axis=1,
            )
        )
    )

    return {
        "balanced_accuracy_3class": float(
            balanced_accuracy_score(
                y,
                predictions,
            )
        ),
        "macro_f1_3class": float(
            f1_score(
                y,
                predictions,
                labels=(
                    EXPECTED_CLASS_ORDER
                ),
                average="macro",
                zero_division=0,
            )
        ),
        (
            "directional_macro_f1_"
            "short_long"
        ): float(
            f1_score(
                y,
                predictions,
                labels=[
                    -1,
                    1,
                ],
                average="macro",
                zero_division=0,
            )
        ),
        "short_precision": float(
            precision[
                0
            ]
        ),
        "short_recall": float(
            recall[
                0
            ]
        ),
        "short_f1": float(
            f1_values[
                0
            ]
        ),
        "no_trade_precision": float(
            precision[
                1
            ]
        ),
        "no_trade_recall": float(
            recall[
                1
            ]
        ),
        "no_trade_f1": float(
            f1_values[
                1
            ]
        ),
        "long_precision": float(
            precision[
                2
            ]
        ),
        "long_recall": float(
            recall[
                2
            ]
        ),
        "long_f1": float(
            f1_values[
                2
            ]
        ),
        "log_loss_3class": float(
            log_loss(
                y,
                proba,
                labels=(
                    EXPECTED_CLASS_ORDER
                ),
            )
        ),
        "multiclass_brier": (
            brier
        ),
        "predicted_trade_coverage": float(
            np.mean(
                predictions
                != 0
            )
        ),
    }


def execute_one_time_test(
    *,
    expected_preflight_fingerprint: str,
    canonical_root: Path = REPO_ROOT,
    preflight_path: Path = (
        DEFAULT_PREFLIGHT_PATH
    ),
    ledger_path: Path = (
        DEFAULT_LEDGER_PATH
    ),
    result_path: Path = (
        DEFAULT_RESULT_PATH
    ),
) -> dict[str, Any]:
    validate_stored_preflight(
        preflight_path=(
            preflight_path
        ),
        expected_fingerprint=(
            expected_preflight_fingerprint
        ),
        ledger_path=(
            ledger_path
        ),
        result_path=(
            result_path
        ),
    )

    core = _load_module(
        CORE_PATH,
        "xauusd_test_execution_core",
    )

    source_module = _load_module(
        SOURCE_PATH,
        "xauusd_test_execution_source",
    )

    protocol = _read_json_auto(
        PROTOCOL_PATH
    )

    model = joblib.load(
        MODEL_PATH
    )

    adapter = (
        ArtifactBoundedTestSource(
            canonical_root,
            core_module=(
                core
            ),
            source_module=(
                source_module
            ),
        )
    )

    ledger = (
        core.TestAccessLedger(
            path=(
                ledger_path
            ),
            protocol_fingerprint=(
                EXPECTED_TEST_PROTOCOL_FINGERPRINT
            ),
        )
    )

    core_result = (
        core.execute_one_time_test(
            protocol=(
                protocol
            ),
            ledger=(
                ledger
            ),
            load_test_batch=(
                adapter.load
            ),
            predict_probabilities=(
                lambda X:
                _predict_probabilities(
                    model,
                    X,
                )
            ),
            metric_evaluator=(
                evaluate_test_metrics
            ),
        )
    )

    source_evidence = (
        adapter.last_evidence
    )

    if not isinstance(
        source_evidence,
        Mapping,
    ):
        raise OneTimeTestRunnerError(
            "TEST source evidence missing "
            "after one-time execution."
        )

    decision = _required_mapping(
        core_result,
        "decision",
    )

    accepted = (
        decision.get(
            "test_accepted"
        )
        is True
    )

    ledger_final = (
        ledger.read()
    )

    result_record = {
        (
            "preflight_fingerprint_sha256"
        ): (
            expected_preflight_fingerprint
        ),
        "winner_candidate_id": (
            EXPECTED_WINNER_ID
        ),
        (
            "test_protocol_fingerprint_sha256"
        ): (
            EXPECTED_TEST_PROTOCOL_FINGERPRINT
        ),
        (
            "validation_result_fingerprint_sha256"
        ): (
            EXPECTED_VALIDATION_RESULT_FINGERPRINT
        ),
        (
            "validation_freeze_fingerprint_sha256"
        ): (
            EXPECTED_VALIDATION_FREEZE_FINGERPRINT
        ),
        "model_artifact_sha256": (
            EXPECTED_MODEL_ARTIFACT_SHA256
        ),
        (
            "model_verification_record_"
            "fingerprint_sha256"
        ): (
            EXPECTED_MODEL_VERIFICATION_RECORD_SHA256
        ),
        "portable_loader_source_sha256": (
            EXPECTED_LOADER_SOURCE_SHA256
        ),
        "feature_columns_sha256": (
            EXPECTED_FEATURE_COLUMNS_SHA256
        ),
        "test_row_count": (
            core_result.get(
                "test_row_count"
            )
        ),
        "test_feature_count": (
            EXPECTED_FEATURE_COUNT
        ),
        "test_metrics": (
            core_result.get(
                "metrics"
            )
        ),
        "test_hard_checks": (
            core_result.get(
                "hard_checks"
            )
        ),
        (
            "core_test_result_fingerprint"
        ): (
            core_result.get(
                "result_fingerprint"
            )
        ),
        "source_evidence": dict(
            source_evidence
        ),
        "ledger_final_status": (
            ledger_final.get(
                "status"
            )
        ),
        "test_accepted": (
            accepted
        ),
    }

    result_fingerprint = (
        _canonical_sha256(
            result_record
        )
    )

    report = {
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "valid": True,
        "research_scope": (
            "FIRST_AND_ONLY_REAL_UNTOUCHED_"
            "PORTABLE_TEST_EVALUATION_OF_"
            "VERIFIED_FROZEN_C04"
        ),
        "result_record": (
            result_record
        ),
        "result_fingerprint": {
            "canonicalization": (
                "JSON_SORT_KEYS_COMPACT_UTF8_SHA256"
            ),
            "sha256": (
                result_fingerprint
            ),
        },
        "core_result": (
            core_result
        ),
        "decision": {
            "status": (
                "ONE_TIME_TEST_ACCEPTED"
                if accepted
                else (
                    "ONE_TIME_TEST_REJECTED"
                )
            ),
            "test_consumed": True,
            "test_accepted": (
                accepted
            ),
            "test_rerun_authorized": False,
            (
                "validation_reread_authorized"
            ): False,
            (
                "current_frozen_lineage_"
                "may_be_tuned_from_test"
            ): False,
            "model_refit_authorized": False,
            "threshold_change_authorized": False,
            (
                "probability_calibration_authorized"
            ): False,
            "candidate_change_authorized": False,
            "shadow_authorized": False,
            "live_authorized": False,
            "next_action": (
                "FREEZE_TEST_RESULT_AND_BUILD_"
                "FINAL_HISTORICAL_RESEARCH_VERDICT"
                if accepted
                else (
                    "FREEZE_TEST_REJECTION_AND_CLOSE_"
                    "CURRENT_RESEARCH_LINEAGE_"
                    "NO_SHADOW_NO_LIVE"
                )
            ),
        },
        "scientific_policy": {
            (
                "portable_validation_"
                "reread_performed"
            ): False,
            (
                "portable_test_consumed"
            ): True,
            (
                "portable_test_rerun_allowed"
            ): False,
            "model_refit_performed": False,
            "threshold_search_performed": False,
            (
                "probability_calibration_performed"
            ): False,
            "feature_selection_performed": False,
            "candidate_changed": False,
            "model_artifact_modified": False,
            (
                "execution_integration_modified"
            ): False,
            "risk_engine_modified": False,
            "orders_sent": False,
            "shadow_authorized": False,
            "live_authorized": False,
        },
    }

    _write_json_atomic(
        result_path,
        report,
    )

    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-preflight or explicitly execute "
            "the first and only real portable "
            "TEST evaluation."
        )
    )

    parser.add_argument(
        "--execute-one-time-test",
        action="store_true",
    )

    parser.add_argument(
        "--expected-preflight-fingerprint",
        type=str,
        default=None,
    )

    parser.add_argument(
        "--canonical-root",
        type=Path,
        default=REPO_ROOT,
    )

    parser.add_argument(
        "--preflight-output",
        type=Path,
        default=(
            DEFAULT_PREFLIGHT_PATH
        ),
    )

    parser.add_argument(
        "--ledger",
        type=Path,
        default=(
            DEFAULT_LEDGER_PATH
        ),
    )

    parser.add_argument(
        "--result-output",
        type=Path,
        default=(
            DEFAULT_RESULT_PATH
        ),
    )

    args = parser.parse_args()

    if not (
        args.execute_one_time_test
    ):
        try:
            report = build_preflight(
                ledger_path=(
                    args.ledger
                ),
                result_path=(
                    args.result_output
                ),
            )

            _write_json_atomic(
                args.preflight_output,
                report,
            )

        except Exception as exc:
            failure = {
                "analysis_version": (
                    ANALYSIS_VERSION
                ),
                "valid": False,
                "reason": (
                    "ONE_TIME_TEST_DRY_"
                    "PREFLIGHT_FAILED"
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
                    (
                        "portable_validation_"
                        "feature_values_loaded"
                    ): False,
                    (
                        "portable_validation_"
                        "target_values_loaded"
                    ): False,
                    (
                        "portable_test_feature_"
                        "values_loaded"
                    ): False,
                    (
                        "portable_test_target_"
                        "values_loaded"
                    ): False,
                    "test_consumed": False,
                    "live_authorized": False,
                },
            }

            _write_json_atomic(
                args.preflight_output,
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
                    (
                        "preflight_fingerprint_sha256"
                    ): (
                        report[
                            "preflight_fingerprint"
                        ][
                            "sha256"
                        ]
                    ),
                    "preflight_record": (
                        report[
                            "preflight_record"
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

    if not (
        args.expected_preflight_fingerprint
    ):
        print(
            json.dumps(
                {
                    "analysis_version": (
                        ANALYSIS_VERSION
                    ),
                    "valid": False,
                    "reason": (
                        "EXPECTED_PREFLIGHT_"
                        "FINGERPRINT_REQUIRED"
                    ),
                    "test_executed": False,
                    (
                        "validation_reread_authorized"
                    ): False,
                    "live_authorized": False,
                },
                indent=2,
                sort_keys=True,
            )
        )

        return 2

    try:
        report = execute_one_time_test(
            expected_preflight_fingerprint=(
                args
                .expected_preflight_fingerprint
            ),
            canonical_root=(
                args.canonical_root
            ),
            preflight_path=(
                args.preflight_output
            ),
            ledger_path=(
                args.ledger
            ),
            result_path=(
                args.result_output
            ),
        )

    except Exception as exc:
        ledger_state: Any = None

        if args.ledger.exists():
            try:
                ledger_state = (
                    _read_json_auto(
                        args.ledger
                    )
                )

            except Exception:
                ledger_state = {
                    "unreadable": True,
                }

        failure = {
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "valid": False,
            "reason": (
                "ONE_TIME_REAL_TEST_"
                "EXECUTION_FAILED"
            ),
            "error_type": (
                type(
                    exc
                ).__name__
            ),
            "error": str(
                exc
            ),
            "ledger_state": (
                ledger_state
            ),
            "scientific_policy": {
                (
                    "validation_reread_authorized"
                ): False,
                "test_rerun_authorized": False,
                "shadow_authorized": False,
                "live_authorized": False,
            },
        }

        _write_json_atomic(
            args.result_output,
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
                (
                    "result_fingerprint_sha256"
                ): (
                    report[
                        "result_fingerprint"
                    ][
                        "sha256"
                    ]
                ),
                "test_metrics": (
                    report[
                        "result_record"
                    ][
                        "test_metrics"
                    ]
                ),
                "test_hard_checks": (
                    report[
                        "result_record"
                    ][
                        "test_hard_checks"
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