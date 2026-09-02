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


ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_ONE_TIME_TEST_PRE_READ_RECOVERY_RUNNER_V1"
)

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTING_DIR = REPO_ROOT / "04_Testing"

CORE_PATH = (
    TESTING_DIR
    / "xauusd_portable_331_one_time_test_core.py"
)

SOURCE_PATH = (
    TESTING_DIR
    / "xauusd_portable_331_authorized_test_source.py"
)

VALIDATION_SOURCE_PATH = (
    TESTING_DIR
    / "xauusd_portable_331_authorized_validation_source.py"
)

INTEGRATION_RUNNER_PATH = (
    TESTING_DIR
    / "run_xauusd_portable_331_candidate_evaluator_integration.py"
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

ORIGINAL_PREFLIGHT_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_test_preflight.json"
)

ORIGINAL_FAILED_RESULT_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_test_result.json"
)

DEFAULT_RECOVERY_PREFLIGHT_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_test_recovery_preflight.json"
)

DEFAULT_LEDGER_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_test_access_ledger.json"
)

DEFAULT_RECOVERY_RESULT_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_one_time_test_recovery_result.json"
)


EXPECTED_WINNER_ID = (
    "C04_FLAT_EXTRA_TREES_CONSTRAINED"
)

EXPECTED_ORIGINAL_PREFLIGHT_FINGERPRINT = (
    "0050ce2bea50ddafa4e9a698fff3affa7ac24fc0f1a0185871ac86cfca127057"
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

EXPECTED_SPLIT_COLUMN = (
    "dataset_split"
)

EXPECTED_TARGET_COLUMN = (
    "target_class"
)

EXPECTED_PRE_READ_ERROR_TYPE = (
    "ImportError"
)

EXPECTED_PRE_READ_ERROR_TEXT = (
    "attempted relative import with no known parent package"
)


class OneTimeTestRecoveryRunnerError(
    RuntimeError
):
    """Raised when safe TEST recovery cannot be proven."""


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


def _json_safe(
    value: Any,
) -> Any:
    if isinstance(
        value,
        np.ndarray,
    ):
        return [
            _json_safe(
                item
            )
            for item
            in value.tolist()
        ]

    if isinstance(
        value,
        np.generic,
    ):
        return value.item()

    if isinstance(
        value,
        Mapping,
    ):
        return {
            str(
                key
            ): _json_safe(
                child
            )
            for (
                key,
                child,
            )
            in value.items()
        }

    if isinstance(
        value,
        (
            list,
            tuple,
        ),
    ):
        return [
            _json_safe(
                child
            )
            for child
            in value
        ]

    return value


def _read_json_auto(
    path: Path,
) -> dict[str, Any]:
    if not path.is_file():
        raise OneTimeTestRecoveryRunnerError(
            f"REQUIRED_JSON_MISSING:{path}"
        )

    raw = path.read_bytes()

    last_error: (
        Exception
        | None
    ) = None

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
                raise OneTimeTestRecoveryRunnerError(
                    f"JSON_ROOT_NOT_OBJECT:{path}"
                )

            return value

        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            last_error = exc

    raise OneTimeTestRecoveryRunnerError(
        "JSON_DECODE_FAILED:"
        f"{path}:"
        f"{last_error}"
    )


def _write_json_atomic(
    path: Path,
    document: Mapping[
        str,
        Any,
    ],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = (
        json.dumps(
            _json_safe(
                document
            ),
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
        raise OneTimeTestRecoveryRunnerError(
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
        raise OneTimeTestRecoveryRunnerError(
            f"MODULE_IMPORT_SPEC_FAILED:{path}"
        )

    module = (
        importlib.util
        .module_from_spec(
            spec
        )
    )

    sys.modules[
        module_name
    ] = module

    try:
        spec.loader.exec_module(
            module
        )

    except Exception:
        sys.modules.pop(
            module_name,
            None,
        )

        raise

    return module


def _required_mapping(
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
        raise OneTimeTestRecoveryRunnerError(
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

    return (
        node
        == expected
    )


def _values_for_key(
    node: Any,
    key: str,
) -> list[Any]:
    values: list[
        Any
    ] = []

    if isinstance(
        node,
        Mapping,
    ):
        for (
            child_key,
            child,
        ) in node.items():
            if (
                child_key
                == key
            ):
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
    document: Mapping[
        str,
        Any,
    ],
    key: str,
    expected: Any,
) -> None:
    values = (
        _values_for_key(
            document,
            key,
        )
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
        raise OneTimeTestRecoveryRunnerError(
            "REQUIRED_STATE_MISSING:"
            f"{key}="
            f"{expected!r};"
            f"observed="
            f"{values!r}"
        )


def _require_scalar(
    document: Mapping[
        str,
        Any,
    ],
    expected: Any,
    label: str,
) -> None:
    if not _contains_scalar(
        document,
        expected,
    ):
        raise OneTimeTestRecoveryRunnerError(
            "REQUIRED_IDENTITY_MISSING:"
            f"{label}:"
            f"{expected}"
        )


def _validate_model_contract(
    model: Any,
) -> None:
    classes = getattr(
        model,
        "classes_",
        None,
    )

    if classes is None:
        raise OneTimeTestRecoveryRunnerError(
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
        raise OneTimeTestRecoveryRunnerError(
            "Frozen model class "
            "order mismatch:"
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
        raise OneTimeTestRecoveryRunnerError(
            "Frozen model feature-count "
            "mismatch:"
            f"{n_features}"
        )


def _validate_original_pre_read_failure(
    *,
    original_preflight_path: Path = (
        ORIGINAL_PREFLIGHT_PATH
    ),
    original_failure_path: Path = (
        ORIGINAL_FAILED_RESULT_PATH
    ),
    ledger_path: Path = (
        DEFAULT_LEDGER_PATH
    ),
) -> dict[str, Any]:
    if ledger_path.exists():
        raise OneTimeTestRecoveryRunnerError(
            "RECOVERY_FORBIDDEN_TEST_"
            "LEDGER_ALREADY_EXISTS"
        )

    original_preflight = (
        _read_json_auto(
            original_preflight_path
        )
    )

    if (
        original_preflight.get(
            "valid"
        )
        is not True
    ):
        raise OneTimeTestRecoveryRunnerError(
            "ORIGINAL_PREFLIGHT_NOT_VALID"
        )

    fingerprint = (
        _required_mapping(
            original_preflight,
            "preflight_fingerprint",
        )
    )

    if (
        fingerprint.get(
            "sha256"
        )
        != (
            EXPECTED_ORIGINAL_PREFLIGHT_FINGERPRINT
        )
    ):
        raise OneTimeTestRecoveryRunnerError(
            "ORIGINAL_PREFLIGHT_"
            "FINGERPRINT_MISMATCH"
        )

    if (
        _canonical_sha256(
            _required_mapping(
                original_preflight,
                "preflight_record",
            )
        )
        != (
            EXPECTED_ORIGINAL_PREFLIGHT_FINGERPRINT
        )
    ):
        raise OneTimeTestRecoveryRunnerError(
            "ORIGINAL_PREFLIGHT_CONTENT_"
            "FINGERPRINT_MISMATCH"
        )

    failure = (
        _read_json_auto(
            original_failure_path
        )
    )

    if (
        failure.get(
            "valid"
        )
        is not False
    ):
        raise OneTimeTestRecoveryRunnerError(
            "ORIGINAL_FAILURE_MUST_BE_"
            "VALID_FALSE"
        )

    if (
        failure.get(
            "reason"
        )
        != (
            "ONE_TIME_REAL_TEST_EXECUTION_FAILED"
        )
    ):
        raise OneTimeTestRecoveryRunnerError(
            "ORIGINAL_FAILURE_REASON_MISMATCH"
        )

    if (
        failure.get(
            "error_type"
        )
        != EXPECTED_PRE_READ_ERROR_TYPE
    ):
        raise OneTimeTestRecoveryRunnerError(
            "ORIGINAL_FAILURE_ERROR_"
            "TYPE_MISMATCH"
        )

    if (
        EXPECTED_PRE_READ_ERROR_TEXT
        not in str(
            failure.get(
                "error",
                "",
            )
        )
    ):
        raise OneTimeTestRecoveryRunnerError(
            "ORIGINAL_FAILURE_ERROR_"
            "TEXT_MISMATCH"
        )

    if (
        failure.get(
            "ledger_state"
        )
        is not None
    ):
        raise OneTimeTestRecoveryRunnerError(
            "ORIGINAL_FAILURE_LEDGER_"
            "STATE_NOT_NULL"
        )

    _require_key_value(
        failure,
        "validation_reread_authorized",
        False,
    )

    _require_key_value(
        failure,
        "test_rerun_authorized",
        False,
    )

    _require_key_value(
        failure,
        "shadow_authorized",
        False,
    )

    _require_key_value(
        failure,
        "live_authorized",
        False,
    )

    return {
        "original_preflight_sha256": (
            _sha256_file(
                original_preflight_path
            )
        ),
        "original_failure_sha256": (
            _sha256_file(
                original_failure_path
            )
        ),
        (
            "original_failure_"
            "canonical_sha256"
        ): (
            _canonical_sha256(
                failure
            )
        ),
        "original_failure_error_type": (
            failure.get(
                "error_type"
            )
        ),
        "original_failure_error": (
            failure.get(
                "error"
            )
        ),
        (
            "ledger_absent_after_"
            "original_failure"
        ): True,
    }


def _validate_ledger_state_for_recovery(
    ledger_path: Path,
    recovery_result_path: Path,
) -> dict[str, Any]:
    if recovery_result_path.exists():
        return {
            "state": (
                "RECOVERY_RESULT_ALREADY_EXISTS"
            ),
            (
                "recovery_execution_allowed"
            ): False,
            "test_read_attempt_count": None,
            (
                "holdout_consumed_for_"
                "rerun_policy"
            ): None,
        }

    if not ledger_path.exists():
        return {
            "state": (
                "ABSENT"
            ),
            (
                "recovery_execution_allowed"
            ): True,
            "test_read_attempt_count": 0,
            (
                "holdout_consumed_for_"
                "rerun_policy"
            ): False,
        }

    ledger = (
        _read_json_auto(
            ledger_path
        )
    )

    return {
        "state": str(
            ledger.get(
                "status"
            )
        ),
        (
            "recovery_execution_allowed"
        ): False,
        "test_read_attempt_count": (
            ledger.get(
                "test_read_attempt_count"
            )
        ),
        (
            "holdout_consumed_for_"
            "rerun_policy"
        ): (
            ledger.get(
                "holdout_consumed_for_rerun_policy"
            )
        ),
    }


def _validate_attestation_chain(
    *,
    ledger_path: Path,
    recovery_result_path: Path,
) -> dict[str, Any]:
    required_files = [
        CORE_PATH,
        SOURCE_PATH,
        VALIDATION_SOURCE_PATH,
        INTEGRATION_RUNNER_PATH,
        LOADER_PATH,
        PROTOCOL_PATH,
        CORE_ATTESTATION_PATH,
        SOURCE_ATTESTATION_PATH,
        VALIDATION_RESULT_PATH,
        VALIDATION_FREEZE_PATH,
        MODEL_PATH,
        ORIGINAL_PREFLIGHT_PATH,
        ORIGINAL_FAILED_RESULT_PATH,
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
        raise OneTimeTestRecoveryRunnerError(
            "REQUIRED_RECOVERY_FILE_MISSING:"
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
        raise OneTimeTestRecoveryRunnerError(
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
        raise OneTimeTestRecoveryRunnerError(
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

    validation_source_sha256 = (
        _sha256_file(
            VALIDATION_SOURCE_PATH
        )
    )

    integration_runner_sha256 = (
        _sha256_file(
            INTEGRATION_RUNNER_PATH
        )
    )

    protocol = (
        _read_json_auto(
            PROTOCOL_PATH
        )
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
        != (
            "ONE_TIME_TEST_PROTOCOL_FROZEN"
        )
        or protocol.get(
            "protocol_fingerprint"
        )
        != (
            EXPECTED_TEST_PROTOCOL_FINGERPRINT
        )
    ):
        raise OneTimeTestRecoveryRunnerError(
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
        raise OneTimeTestRecoveryRunnerError(
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
        raise OneTimeTestRecoveryRunnerError(
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
            "inherited_model_"
            "verification_record_fingerprint"
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
        (
            "bound_validation_result_"
            "fingerprint"
        ),
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
        (
            "validation_source_sha256"
        ): (
            validation_source_sha256
        ),
        (
            "integration_runner_sha256"
        ): (
            integration_runner_sha256
        ),
        "loader_source_sha256": (
            actual_loader_sha256
        ),
        "model_artifact_sha256": (
            actual_model_sha256
        ),
        "ledger_state": (
            _validate_ledger_state_for_recovery(
                ledger_path,
                recovery_result_path,
            )
        ),
    }


def _load_loader_class_via_proven_path() -> type:
    validation_source = (
        _load_module(
            VALIDATION_SOURCE_PATH,
            (
                "xauusd_test_recovery_"
                "validation_source"
            ),
        )
    )

    helper = getattr(
        validation_source,
        "_load_loader_class",
        None,
    )

    if not callable(
        helper
    ):
        raise OneTimeTestRecoveryRunnerError(
            "VALIDATION_SOURCE_LOADER_"
            "HELPER_MISSING"
        )

    loader_class = (
        helper()
    )

    if not isinstance(
        loader_class,
        type,
    ):
        raise OneTimeTestRecoveryRunnerError(
            "LOADER_HELPER_DID_NOT_"
            "RETURN_CLASS"
        )

    if (
        loader_class.__name__
        != (
            "Portable331TrainingInputLoader"
        )
    ):
        raise OneTimeTestRecoveryRunnerError(
            "UNEXPECTED_LOADER_CLASS:"
            f"{loader_class.__name__}"
        )

    return loader_class


def _probe_pre_read_dependencies() -> dict[str, Any]:
    core = (
        _load_module(
            CORE_PATH,
            (
                "xauusd_test_recovery_"
                "probe_core"
            ),
        )
    )

    source_module = (
        _load_module(
            SOURCE_PATH,
            (
                "xauusd_test_recovery_"
                "probe_source"
            ),
        )
    )

    if not callable(
        getattr(
            core,
            "execute_one_time_test",
            None,
        )
    ):
        raise OneTimeTestRecoveryRunnerError(
            "TEST_CORE_EXECUTION_"
            "FUNCTION_MISSING"
        )

    if not isinstance(
        getattr(
            core,
            "TestAccessLedger",
            None,
        ),
        type,
    ):
        raise OneTimeTestRecoveryRunnerError(
            "TEST_CORE_LEDGER_CLASS_MISSING"
        )

    if not isinstance(
        getattr(
            source_module,
            "AuthorizedBoundedTestSource",
            None,
        ),
        type,
    ):
        raise OneTimeTestRecoveryRunnerError(
            "AUTHORIZED_BOUNDED_TEST_"
            "SOURCE_CLASS_MISSING"
        )

    loader_class = (
        _load_loader_class_via_proven_path()
    )

    model = (
        joblib.load(
            MODEL_PATH
        )
    )

    _validate_model_contract(
        model
    )

    return {
        "core_import_probe": True,
        "test_source_import_probe": True,
        "proven_loader_import_probe": True,
        "loader_class_name": (
            loader_class.__name__
        ),
        "model_deserialization_probe": True,
        "model_class_name": (
            type(
                model
            ).__name__
        ),
        "model_class_order": (
            EXPECTED_CLASS_ORDER
        ),
        "model_feature_count": (
            EXPECTED_FEATURE_COUNT
        ),
        (
            "dataset_structural_read_"
            "performed"
        ): False,
        "test_values_loaded": False,
    }


def build_recovery_preflight(
    *,
    ledger_path: Path = (
        DEFAULT_LEDGER_PATH
    ),
    recovery_result_path: Path = (
        DEFAULT_RECOVERY_RESULT_PATH
    ),
) -> dict[str, Any]:
    chain = (
        _validate_attestation_chain(
            ledger_path=(
                ledger_path
            ),
            recovery_result_path=(
                recovery_result_path
            ),
        )
    )

    failure_evidence = (
        _validate_original_pre_read_failure(
            ledger_path=(
                ledger_path
            )
        )
    )

    probe = (
        _probe_pre_read_dependencies()
    )

    ledger_state = cast(
        Mapping[
            str,
            Any,
        ],
        chain[
            "ledger_state"
        ],
    )

    recovery_allowed = (
        ledger_state.get(
            "recovery_execution_allowed"
        )
        is True
    )

    preflight_record = {
        "winner_candidate_id": (
            EXPECTED_WINNER_ID
        ),
        (
            "original_preflight_"
            "fingerprint_sha256"
        ): (
            EXPECTED_ORIGINAL_PREFLIGHT_FINGERPRINT
        ),
        (
            "test_protocol_"
            "fingerprint_sha256"
        ): (
            EXPECTED_TEST_PROTOCOL_FINGERPRINT
        ),
        (
            "validation_result_"
            "fingerprint_sha256"
        ): (
            EXPECTED_VALIDATION_RESULT_FINGERPRINT
        ),
        (
            "validation_freeze_"
            "fingerprint_sha256"
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
        (
            "portable_loader_source_sha256"
        ): (
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
            "proven_validation_source_sha256"
        ): (
            chain[
                "validation_source_sha256"
            ]
        ),
        (
            "proven_integration_runner_sha256"
        ): (
            chain[
                "integration_runner_sha256"
            ]
        ),
        (
            "recovery_runner_source_sha256"
        ): (
            _sha256_file(
                Path(
                    __file__
                ).resolve()
            )
        ),
        (
            "core_attestation_"
            "canonical_sha256"
        ): (
            _canonical_sha256(
                chain[
                    "core_attestation"
                ]
            )
        ),
        (
            "source_attestation_"
            "canonical_sha256"
        ): (
            _canonical_sha256(
                chain[
                    "source_attestation"
                ]
            )
        ),
        (
            "validation_result_"
            "canonical_sha256"
        ): (
            _canonical_sha256(
                chain[
                    "validation_result"
                ]
            )
        ),
        (
            "validation_freeze_"
            "canonical_sha256"
        ): (
            _canonical_sha256(
                chain[
                    "validation_freeze"
                ]
            )
        ),
        **failure_evidence,
        "ledger_filename": (
            ledger_path.name
        ),
        "recovery_result_filename": (
            recovery_result_path.name
        ),
        "ledger_state": (
            ledger_state.get(
                "state"
            )
        ),
        (
            "recovery_execution_allowed"
        ): (
            recovery_allowed
        ),
        (
            "test_read_attempt_count_"
            "before_recovery"
        ): (
            ledger_state.get(
                "test_read_attempt_count"
            )
        ),
        (
            "holdout_consumed_"
            "before_recovery"
        ): (
            ledger_state.get(
                "holdout_consumed_for_rerun_policy"
            )
        ),
        "loader_resolution_policy": (
            "PROVEN_VALIDATION_SOURCE_"
            "LOAD_LOADER_CLASS_HELPER"
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
        "pre_read_dependency_probe": (
            probe
        ),
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
            "PRE_READ_TECHNICAL_RECOVERY_"
            "WITHOUT_TEST_VALUE_ACCESS"
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
                "ONE_TIME_TEST_PRE_READ_"
                "RECOVERY_PREFLIGHT_READY"
                if recovery_allowed
                else (
                    "ONE_TIME_TEST_PRE_READ_"
                    "RECOVERY_BLOCKED"
                )
            ),
            (
                "original_test_attempt_"
                "failed_pre_read"
            ): True,
            (
                "original_failure_preserved"
            ): True,
            (
                "test_consumption_boundary_"
                "crossed"
            ): False,
            (
                "dry_recovery_preflight_"
                "completed"
            ): True,
            (
                "real_test_executed_in_"
                "recovery"
            ): False,
            (
                "real_test_values_loaded_in_"
                "recovery"
            ): False,
            (
                "real_test_metrics_computed_in_"
                "recovery"
            ): False,
            (
                "recovery_execution_"
                "authorized_next"
            ): (
                recovery_allowed
            ),
            "test_rerun_authorized": False,
            (
                "validation_reread_authorized"
            ): False,
            "shadow_authorized": False,
            "live_authorized": False,
            "next_action": (
                "FREEZE_RECOVERY_PREFLIGHT_"
                "THEN_CONSIDER_SINGLE_RECOVERED_"
                "TEST_EXECUTION"
                if recovery_allowed
                else (
                    "STOP_RECOVERY_EXECUTION"
                )
            ),
        },
        "scientific_policy": {
            (
                "dataset_structural_read_"
                "performed"
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
                "portable_test_feature_"
                "values_loaded"
            ): False,
            (
                "portable_test_target_"
                "values_loaded"
            ): False,
            (
                "portable_test_metrics_"
                "computed"
            ): False,
            "model_fit_performed": False,
            "model_refit_performed": False,
            "threshold_search_performed": False,
            (
                "probability_calibration_"
                "performed"
            ): False,
            "feature_selection_performed": False,
            "candidate_registry_changed": False,
            "model_artifact_modified": False,
            (
                "execution_integration_"
                "modified"
            ): False,
            "risk_engine_modified": False,
            "orders_sent": False,
            "shadow_authorized": False,
            "live_authorized": False,
        },
    }


def validate_stored_recovery_preflight(
    *,
    preflight_path: Path,
    expected_fingerprint: str,
    ledger_path: Path,
    recovery_result_path: Path,
) -> dict[str, Any]:
    stored = (
        _read_json_auto(
            preflight_path
        )
    )

    if (
        stored.get(
            "analysis_version"
        )
        != ANALYSIS_VERSION
    ):
        raise OneTimeTestRecoveryRunnerError(
            "Stored recovery preflight "
            "analysis version mismatch."
        )

    if (
        stored.get(
            "valid"
        )
        is not True
    ):
        raise OneTimeTestRecoveryRunnerError(
            "Stored recovery preflight "
            "must be valid=true."
        )

    fingerprint = (
        _required_mapping(
            stored,
            "preflight_fingerprint",
        )
    )

    if (
        fingerprint.get(
            "sha256"
        )
        != expected_fingerprint
    ):
        raise OneTimeTestRecoveryRunnerError(
            "Expected recovery preflight "
            "fingerprint does not match "
            "stored preflight."
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
        raise OneTimeTestRecoveryRunnerError(
            "Stored recovery preflight "
            "content fingerprint mismatch."
        )

    decision = (
        _required_mapping(
            stored,
            "decision",
        )
    )

    if (
        decision.get(
            "recovery_execution_authorized_next"
        )
        is not True
    ):
        raise OneTimeTestRecoveryRunnerError(
            "Stored recovery preflight "
            "does not authorize recovered "
            "TEST execution."
        )

    current = (
        build_recovery_preflight(
            ledger_path=(
                ledger_path
            ),
            recovery_result_path=(
                recovery_result_path
            ),
        )
    )

    if (
        current[
            "preflight_fingerprint"
        ][
            "sha256"
        ]
        != expected_fingerprint
    ):
        raise OneTimeTestRecoveryRunnerError(
            "Current provenance/ledger "
            "state differs from frozen "
            "recovery preflight."
        )

    if (
        current[
            "preflight_record"
        ]
        != preflight_record
    ):
        raise OneTimeTestRecoveryRunnerError(
            "Current recovery preflight "
            "record differs from frozen "
            "preflight."
        )

    return stored


class ArtifactBoundedTestSource:
    def __init__(
        self,
        canonical_root: Path,
        *,
        core_module: Any,
        source_module: Any,
        loader_class: type,
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
        )

        self.read_csv = (
            read_csv
        )

        self.last_evidence: (
            dict[
                str,
                Any,
            ]
            | None
        ) = None

    def load(
        self,
    ) -> Any:
        loader = (
            self.loader_class(
                self.canonical_root
            )
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
            raise OneTimeTestRecoveryRunnerError(
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
            raise OneTimeTestRecoveryRunnerError(
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
            raise OneTimeTestRecoveryRunnerError(
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
            raise OneTimeTestRecoveryRunnerError(
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
            raise OneTimeTestRecoveryRunnerError(
                "Cannot recompute manifest "
                "feature-column SHA256."
            ) from exc

        if (
            feature_sha
            != EXPECTED_FEATURE_COLUMNS_SHA256
        ):
            raise OneTimeTestRecoveryRunnerError(
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
            raise OneTimeTestRecoveryRunnerError(
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
            raise OneTimeTestRecoveryRunnerError(
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
            raise OneTimeTestRecoveryRunnerError(
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
            raise OneTimeTestRecoveryRunnerError(
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
            if (
                stop
                <= start
            ):
                raise OneTimeTestRecoveryRunnerError(
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
                        start
                        + 1,
                    ),
                    nrows=(
                        stop
                        - start
                    ),
                    low_memory=False,
                )

            except Exception as exc:
                raise OneTimeTestRecoveryRunnerError(
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
                raise OneTimeTestRecoveryRunnerError(
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
            raise OneTimeTestRecoveryRunnerError(
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
                    "parser_reads_final_"
                    "test_block_only"
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
    _validate_model_contract(
        model
    )

    probabilities = np.asarray(
        model.predict_proba(
            X
        ),
        dtype=np.float64,
    )

    return (
        probabilities,
        EXPECTED_CLASS_ORDER,
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
        raise OneTimeTestRecoveryRunnerError(
            "Metric evaluator probability "
            "shape mismatch."
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
        raise OneTimeTestRecoveryRunnerError(
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
            raise OneTimeTestRecoveryRunnerError(
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
        (
            "predicted_trade_coverage"
        ): float(
            np.mean(
                predictions
                != 0
            )
        ),
    }


def _prepare_execution_dependencies() -> dict[str, Any]:
    core = (
        _load_module(
            CORE_PATH,
            (
                "xauusd_test_recovery_"
                "execution_core"
            ),
        )
    )

    source_module = (
        _load_module(
            SOURCE_PATH,
            (
                "xauusd_test_recovery_"
                "execution_source"
            ),
        )
    )

    if not callable(
        getattr(
            core,
            "execute_one_time_test",
            None,
        )
    ):
        raise OneTimeTestRecoveryRunnerError(
            "TEST_CORE_EXECUTION_"
            "FUNCTION_MISSING"
        )

    if not isinstance(
        getattr(
            core,
            "TestAccessLedger",
            None,
        ),
        type,
    ):
        raise OneTimeTestRecoveryRunnerError(
            "TEST_CORE_LEDGER_CLASS_MISSING"
        )

    if not isinstance(
        getattr(
            source_module,
            "AuthorizedBoundedTestSource",
            None,
        ),
        type,
    ):
        raise OneTimeTestRecoveryRunnerError(
            "AUTHORIZED_BOUNDED_TEST_"
            "SOURCE_CLASS_MISSING"
        )

    loader_class = (
        _load_loader_class_via_proven_path()
    )

    protocol = (
        _read_json_auto(
            PROTOCOL_PATH
        )
    )

    model = (
        joblib.load(
            MODEL_PATH
        )
    )

    _validate_model_contract(
        model
    )

    return {
        "core": (
            core
        ),
        "source_module": (
            source_module
        ),
        "loader_class": (
            loader_class
        ),
        "protocol": (
            protocol
        ),
        "model": (
            model
        ),
    }


def execute_recovered_one_time_test(
    *,
    expected_recovery_preflight_fingerprint: str,
    canonical_root: Path = (
        REPO_ROOT
    ),
    preflight_path: Path = (
        DEFAULT_RECOVERY_PREFLIGHT_PATH
    ),
    ledger_path: Path = (
        DEFAULT_LEDGER_PATH
    ),
    recovery_result_path: Path = (
        DEFAULT_RECOVERY_RESULT_PATH
    ),
) -> dict[str, Any]:
    validate_stored_recovery_preflight(
        preflight_path=(
            preflight_path
        ),
        expected_fingerprint=(
            expected_recovery_preflight_fingerprint
        ),
        ledger_path=(
            ledger_path
        ),
        recovery_result_path=(
            recovery_result_path
        ),
    )

    # All dependency import/deserialization
    # checks happen before ledger creation.
    dependencies = (
        _prepare_execution_dependencies()
    )

    core = (
        dependencies[
            "core"
        ]
    )

    source_module = (
        dependencies[
            "source_module"
        ]
    )

    loader_class = (
        dependencies[
            "loader_class"
        ]
    )

    protocol = (
        dependencies[
            "protocol"
        ]
    )

    model = (
        dependencies[
            "model"
        ]
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
            loader_class=(
                loader_class
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

    ledger_final = (
        ledger.read()
    )

    source_evidence = (
        adapter.last_evidence
    )

    if not isinstance(
        source_evidence,
        Mapping,
    ):
        source_evidence = {
            "available": False,
        }

    ledger_status = str(
        ledger_final.get(
            "status"
        )
    )

    accepted: (
        bool
        | None
    )

    if (
        ledger_status
        == "TEST_COMPLETE_ACCEPTED"
    ):
        accepted = True

    elif (
        ledger_status
        == "TEST_COMPLETE_REJECTED"
    ):
        accepted = False

    else:
        accepted = None

    safe_core_result = (
        _json_safe(
            core_result
        )
    )

    safe_ledger = (
        _json_safe(
            ledger_final
        )
    )

    safe_source_evidence = (
        _json_safe(
            dict(
                source_evidence
            )
        )
    )

    result_record = {
        (
            "recovery_preflight_"
            "fingerprint_sha256"
        ): (
            expected_recovery_preflight_fingerprint
        ),
        (
            "original_preflight_"
            "fingerprint_sha256"
        ): (
            EXPECTED_ORIGINAL_PREFLIGHT_FINGERPRINT
        ),
        (
            "original_failed_result_sha256"
        ): (
            _sha256_file(
                ORIGINAL_FAILED_RESULT_PATH
            )
        ),
        "winner_candidate_id": (
            EXPECTED_WINNER_ID
        ),
        (
            "test_protocol_"
            "fingerprint_sha256"
        ): (
            EXPECTED_TEST_PROTOCOL_FINGERPRINT
        ),
        (
            "validation_result_"
            "fingerprint_sha256"
        ): (
            EXPECTED_VALIDATION_RESULT_FINGERPRINT
        ),
        (
            "validation_freeze_"
            "fingerprint_sha256"
        ): (
            EXPECTED_VALIDATION_FREEZE_FINGERPRINT
        ),
        "model_artifact_sha256": (
            EXPECTED_MODEL_ARTIFACT_SHA256
        ),
        (
            "portable_loader_source_sha256"
        ): (
            EXPECTED_LOADER_SOURCE_SHA256
        ),
        "feature_columns_sha256": (
            EXPECTED_FEATURE_COLUMNS_SHA256
        ),
        "ledger_final": (
            safe_ledger
        ),
        "ledger_final_status": (
            ledger_status
        ),
        "source_evidence": (
            safe_source_evidence
        ),
        "core_result": (
            safe_core_result
        ),
        (
            "core_result_canonical_sha256"
        ): (
            _canonical_sha256(
                safe_core_result
            )
        ),
        (
            "test_accepted_from_"
            "ledger_status"
        ): (
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
            "RECOVERED_FIRST_AND_ONLY_REAL_"
            "PORTABLE_TEST_EVALUATION_AFTER_"
            "PRE_READ_TECHNICAL_FAILURE"
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
        "decision": {
            "status": (
                "ONE_TIME_TEST_ACCEPTED"
                if accepted is True
                else (
                    "ONE_TIME_TEST_REJECTED"
                    if accepted is False
                    else (
                        "ONE_TIME_TEST_CONSUMED_"
                        "WITH_NONFINAL_LEDGER_STATUS"
                    )
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
                "probability_calibration_"
                "authorized"
            ): False,
            "candidate_change_authorized": False,
            "shadow_authorized": False,
            "live_authorized": False,
            "next_action": (
                "FREEZE_RECOVERED_TEST_RESULT_"
                "AND_BUILD_FINAL_HISTORICAL_"
                "RESEARCH_VERDICT"
            ),
        },
        "scientific_policy": {
            (
                "original_pre_read_failure_"
                "preserved"
            ): True,
            (
                "portable_validation_"
                "reread_performed"
            ): False,
            "portable_test_consumed": True,
            (
                "portable_test_rerun_allowed"
            ): False,
            "model_refit_performed": False,
            "threshold_search_performed": False,
            (
                "probability_calibration_"
                "performed"
            ): False,
            "feature_selection_performed": False,
            "candidate_changed": False,
            "model_artifact_modified": False,
            (
                "execution_integration_"
                "modified"
            ): False,
            "risk_engine_modified": False,
            "orders_sent": False,
            "shadow_authorized": False,
            "live_authorized": False,
        },
    }

    _write_json_atomic(
        recovery_result_path,
        report,
    )

    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Freeze a pre-read TEST recovery "
            "preflight, or explicitly perform "
            "the single recovered TEST execution."
        )
    )

    parser.add_argument(
        "--execute-one-time-test-recovery",
        action="store_true",
    )

    parser.add_argument(
        (
            "--expected-recovery-"
            "preflight-fingerprint"
        ),
        type=str,
        default=None,
    )

    parser.add_argument(
        "--canonical-root",
        type=Path,
        default=(
            REPO_ROOT
        ),
    )

    parser.add_argument(
        "--recovery-preflight-output",
        type=Path,
        default=(
            DEFAULT_RECOVERY_PREFLIGHT_PATH
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
        "--recovery-result-output",
        type=Path,
        default=(
            DEFAULT_RECOVERY_RESULT_PATH
        ),
    )

    args = (
        parser.parse_args()
    )

    if not (
        args.execute_one_time_test_recovery
    ):
        try:
            report = (
                build_recovery_preflight(
                    ledger_path=(
                        args.ledger
                    ),
                    recovery_result_path=(
                        args.recovery_result_output
                    ),
                )
            )

            _write_json_atomic(
                args.recovery_preflight_output,
                report,
            )

        except Exception as exc:
            failure = {
                "analysis_version": (
                    ANALYSIS_VERSION
                ),
                "valid": False,
                "reason": (
                    "ONE_TIME_TEST_PRE_READ_"
                    "RECOVERY_PREFLIGHT_FAILED"
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
                args.recovery_preflight_output,
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
                        "recovery_preflight_"
                        "fingerprint_sha256"
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
        args.expected_recovery_preflight_fingerprint
    ):
        print(
            json.dumps(
                {
                    "analysis_version": (
                        ANALYSIS_VERSION
                    ),
                    "valid": False,
                    "reason": (
                        "EXPECTED_RECOVERY_PREFLIGHT_"
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
        report = (
            execute_recovered_one_time_test(
                expected_recovery_preflight_fingerprint=(
                    args
                    .expected_recovery_preflight_fingerprint
                ),
                canonical_root=(
                    args.canonical_root
                ),
                preflight_path=(
                    args.recovery_preflight_output
                ),
                ledger_path=(
                    args.ledger
                ),
                recovery_result_path=(
                    args.recovery_result_output
                ),
            )
        )

    except Exception as exc:
        ledger_state: Any = (
            None
        )

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
                "ONE_TIME_RECOVERED_REAL_"
                "TEST_EXECUTION_FAILED"
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
            (
                "original_failure_preserved"
            ): (
                ORIGINAL_FAILED_RESULT_PATH
                .is_file()
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
            args.recovery_result_output,
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
                "ledger_final_status": (
                    report[
                        "result_record"
                    ][
                        "ledger_final_status"
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