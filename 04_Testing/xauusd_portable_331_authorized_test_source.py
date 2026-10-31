from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np


ANALYSIS_VERSION = "XAUUSD_PORTABLE_331_AUTHORIZED_TEST_SOURCE_IMPLEMENTATION_V1"
STATUS = "AUTHORIZED_TEST_SOURCE_IMPLEMENTED_NOT_REAL_EXECUTED"

ATTESTATION_PATH = Path(
    "xauusd_portable_331_authorized_test_source_attestation.json"
)
TEST_PROTOCOL_PATH = Path(
    "xauusd_portable_331_one_time_test_protocol.json"
)
TEST_CORE_SOURCE_PATH = Path(
    "04_Testing/xauusd_portable_331_one_time_test_core.py"
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
EXPECTED_FEATURE_COUNT = 331
EXPECTED_FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)
EXPECTED_LOADER_SOURCE_SHA256 = (
    "49c86c269f2742fec7c6991eaf7a8a9c0466066a3db230a80375ba2e2c33680c"
)
EXPECTED_CLASS_ORDER = [-1, 0, 1]

TRAIN_LABEL = "TRAIN"
VALIDATION_LABEL = "VALIDATION"
TEST_LABEL = "TEST"


class AuthorizedTestSourceError(RuntimeError):
    """Raised when bounded TEST-source guarantees cannot be proven."""


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(
        _canonical_json(value).encode("utf-8")
    )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise AuthorizedTestSourceError(
            f"JSON_NOT_UTF8:{path}"
        ) from exc

    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AuthorizedTestSourceError(
            f"JSON_INVALID:{path}"
        ) from exc

    if not isinstance(value, dict):
        raise AuthorizedTestSourceError(
            f"JSON_ROOT_NOT_OBJECT:{path}"
        )

    return value


def _load_test_core_module(path: Path) -> Any:
    if not path.is_file():
        raise AuthorizedTestSourceError(
            f"TEST_CORE_SOURCE_MISSING:{path}"
        )

    spec = importlib.util.spec_from_file_location(
        "pulseviper_one_time_test_core_for_source",
        path,
    )

    if spec is None or spec.loader is None:
        raise AuthorizedTestSourceError(
            f"TEST_CORE_IMPORT_SPEC_FAILED:{path}"
        )

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class TestBlockPlan:
    start_row: int
    stop_row_exclusive: int
    row_count: int
    split_label: str = TEST_LABEL


def locate_final_test_block(
    split_labels: Sequence[Any],
) -> TestBlockPlan:
    labels = [
        str(value).strip().upper()
        for value in split_labels
    ]

    if not labels:
        raise AuthorizedTestSourceError(
            "SPLIT_STRUCTURE_EMPTY"
        )

    allowed = {
        TRAIN_LABEL,
        VALIDATION_LABEL,
        TEST_LABEL,
    }

    unexpected = sorted(
        set(labels) - allowed
    )

    if unexpected:
        raise AuthorizedTestSourceError(
            "UNEXPECTED_SPLIT_LABELS:"
            f"{unexpected}"
        )

    if TRAIN_LABEL not in labels:
        raise AuthorizedTestSourceError(
            "TRAIN_BLOCK_MISSING"
        )

    if VALIDATION_LABEL not in labels:
        raise AuthorizedTestSourceError(
            "VALIDATION_BLOCK_MISSING"
        )

    if TEST_LABEL not in labels:
        raise AuthorizedTestSourceError(
            "TEST_BLOCK_MISSING"
        )

    first_validation = labels.index(
        VALIDATION_LABEL
    )
    first_test = labels.index(
        TEST_LABEL
    )

    if first_validation <= 0:
        raise AuthorizedTestSourceError(
            "VALIDATION_MUST_FOLLOW_TRAIN"
        )

    if first_test <= first_validation:
        raise AuthorizedTestSourceError(
            "TEST_MUST_FOLLOW_VALIDATION"
        )

    if any(
        label != TRAIN_LABEL
        for label in labels[:first_validation]
    ):
        raise AuthorizedTestSourceError(
            "TRAIN_BLOCK_NOT_CONTIGUOUS"
        )

    if any(
        label != VALIDATION_LABEL
        for label in labels[
            first_validation:first_test
        ]
    ):
        raise AuthorizedTestSourceError(
            "VALIDATION_BLOCK_NOT_CONTIGUOUS"
        )

    if any(
        label != TEST_LABEL
        for label in labels[first_test:]
    ):
        raise AuthorizedTestSourceError(
            "TEST_BLOCK_NOT_FINAL_CONTIGUOUS"
        )

    return TestBlockPlan(
        start_row=first_test,
        stop_row_exclusive=len(labels),
        row_count=len(labels) - first_test,
    )


def _extract_column(
    table: Any,
    column: str,
) -> np.ndarray:
    if isinstance(table, Mapping):
        if column not in table:
            raise AuthorizedTestSourceError(
                f"REQUIRED_COLUMN_MISSING:{column}"
            )

        return np.asarray(
            table[column]
        )

    columns = getattr(
        table,
        "columns",
        None,
    )

    if columns is not None:
        if column not in list(columns):
            raise AuthorizedTestSourceError(
                f"REQUIRED_COLUMN_MISSING:{column}"
            )

        return np.asarray(
            table[column]
        )

    raise AuthorizedTestSourceError(
        "BOUNDED_READER_RESULT_UNSUPPORTED"
    )


def _row_count_from_table(
    table: Any,
) -> int:
    if isinstance(table, Mapping):
        lengths: set[int] = set()

        for value in table.values():
            array = np.asarray(value)

            if array.ndim == 0:
                raise AuthorizedTestSourceError(
                    "BOUNDED_READER_SCALAR_COLUMN"
                )

            lengths.add(
                int(array.shape[0])
            )

        if not lengths:
            raise AuthorizedTestSourceError(
                "BOUNDED_READER_RESULT_EMPTY"
            )

        if len(lengths) != 1:
            raise AuthorizedTestSourceError(
                "BOUNDED_READER_COLUMN_LENGTH_MISMATCH"
            )

        return next(iter(lengths))

    try:
        return int(len(table))
    except TypeError as exc:
        raise AuthorizedTestSourceError(
            "BOUNDED_READER_RESULT_HAS_NO_ROW_COUNT"
        ) from exc


class AuthorizedBoundedTestSource:
    def __init__(
        self,
        *,
        split_labels: Sequence[Any],
        feature_columns: Sequence[str],
        feature_columns_sha256: str,
        read_bounded_rows: Callable[
            [int, int, Sequence[str]],
            Any,
        ],
        target_column: str = "target_class",
        split_column: str = "dataset_split",
        test_core_module: Any,
    ) -> None:
        self.plan = locate_final_test_block(
            split_labels
        )

        self.feature_columns = [
            str(value)
            for value in feature_columns
        ]

        if (
            len(self.feature_columns)
            != EXPECTED_FEATURE_COUNT
        ):
            raise AuthorizedTestSourceError(
                "FEATURE_COLUMN_COUNT_MISMATCH:"
                f"expected={EXPECTED_FEATURE_COUNT};"
                f"actual={len(self.feature_columns)}"
            )

        if len(set(self.feature_columns)) != len(
            self.feature_columns
        ):
            raise AuthorizedTestSourceError(
                "FEATURE_COLUMNS_NOT_UNIQUE"
            )

        if (
            feature_columns_sha256
            != EXPECTED_FEATURE_COLUMNS_SHA256
        ):
            raise AuthorizedTestSourceError(
                "FEATURE_COLUMNS_SHA256_MISMATCH:"
                f"expected={EXPECTED_FEATURE_COLUMNS_SHA256};"
                f"actual={feature_columns_sha256}"
            )

        self.read_bounded_rows = (
            read_bounded_rows
        )
        self.target_column = str(
            target_column
        )
        self.split_column = str(
            split_column
        )
        self.test_core_module = (
            test_core_module
        )

    @property
    def required_columns(
        self,
    ) -> list[str]:
        return [
            self.split_column,
            *self.feature_columns,
            self.target_column,
        ]

    def load_protected_test_batch(
        self,
    ) -> Any:
        table = self.read_bounded_rows(
            self.plan.start_row,
            self.plan.stop_row_exclusive,
            tuple(
                self.required_columns
            ),
        )

        actual_rows = (
            _row_count_from_table(
                table
            )
        )

        if (
            actual_rows
            != self.plan.row_count
        ):
            raise AuthorizedTestSourceError(
                "BOUNDED_TEST_ROW_COUNT_MISMATCH:"
                f"expected={self.plan.row_count};"
                f"actual={actual_rows}"
            )

        returned_splits = [
            str(value).strip().upper()
            for value in _extract_column(
                table,
                self.split_column,
            ).tolist()
        ]

        if (
            len(returned_splits)
            != self.plan.row_count
        ):
            raise AuthorizedTestSourceError(
                "RETURNED_SPLIT_ROW_COUNT_MISMATCH"
            )

        if any(
            value != TEST_LABEL
            for value in returned_splits
        ):
            raise AuthorizedTestSourceError(
                "BOUNDED_READER_RETURNED_NON_TEST_ROWS"
            )

        feature_arrays = []

        for column in self.feature_columns:
            values = _extract_column(
                table,
                column,
            )

            if values.ndim != 1:
                raise AuthorizedTestSourceError(
                    "FEATURE_COLUMN_NOT_1D:"
                    f"{column}"
                )

            feature_arrays.append(
                values
            )

        X = np.column_stack(
            feature_arrays
        )

        y_true = _extract_column(
            table,
            self.target_column,
        )

        batch = (
            self.test_core_module.ProtectedTestBatch(
                X=X,
                y_true=y_true,
            )
        )

        return (
            self.test_core_module.validate_test_batch(
                batch
            )
        )


def build_source_attestation(
    *,
    test_core_source_sha256: str,
    source_sha256: str,
) -> dict[str, Any]:
    document = {
        "analysis_version": ANALYSIS_VERSION,
        "valid": True,
        "status": STATUS,
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
            "feature_count": (
                EXPECTED_FEATURE_COUNT
            ),
            "feature_columns_sha256": (
                EXPECTED_FEATURE_COLUMNS_SHA256
            ),
            "loader_source_sha256": (
                EXPECTED_LOADER_SOURCE_SHA256
            ),
            "test_core_source_sha256": (
                test_core_source_sha256
            ),
            "authorized_test_source_sha256": (
                source_sha256
            ),
        },
        "verified_properties": {
            "split_structure_only_before_read": True,
            "test_is_final_contiguous_block": True,
            "bounded_row_range_required": True,
            "bounded_reader_receives_test_range_only": True,
            "returned_rows_must_all_be_test": True,
            "exact_331_feature_order_required": True,
            "frozen_feature_sha_required": True,
            "target_class_only": True,
            "validation_value_reread_performed": False,
            "real_test_values_accessed": False,
            "original_public_holdout_accessors_modified": False,
        },
        "decision": {
            "authorized_test_source_implemented": True,
            "one_shot_test_runner_implementation_authorized_next": True,
            "test_execution_authorized": False,
            "test_values_accessed": False,
            "validation_rerun_authorized": False,
            "model_refit_authorized": False,
            "candidate_change_authorized": False,
            "threshold_change_authorized": False,
            "probability_calibration_authorized": False,
            "shadow_authorized": False,
            "live_authorized": False,
            "next_action": (
                "IMPLEMENT_ONE_SHOT_TEST_RUNNER_AND_DRY_"
                "PREFLIGHT_WITHOUT_READING_TEST_VALUES"
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
    document: Mapping[str, Any],
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
            _canonical_json(existing)
            != _canonical_json(document)
        ):
            raise AuthorizedTestSourceError(
                "FROZEN_ATTESTATION_ALREADY_EXISTS_"
                f"WITH_DIFFERENT_CONTENT:{path}"
            )

        return

    path.write_text(
        payload,
        encoding="utf-8",
    )


def main() -> int:
    core = _load_test_core_module(
        TEST_CORE_SOURCE_PATH
    )

    protocol = (
        core.load_and_verify_frozen_test_protocol(
            TEST_PROTOCOL_PATH
        )
    )

    if (
        protocol.get(
            "protocol_fingerprint"
        )
        != EXPECTED_TEST_PROTOCOL_FINGERPRINT
    ):
        raise AuthorizedTestSourceError(
            "TEST_PROTOCOL_FINGERPRINT_MISMATCH"
        )

    core_source_sha256 = (
        _sha256_file(
            TEST_CORE_SOURCE_PATH
        )
    )

    source_sha256 = _sha256_file(
        Path(__file__).resolve()
    )

    attestation = (
        build_source_attestation(
            test_core_source_sha256=(
                core_source_sha256
            ),
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
        f"{source_sha256}"
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