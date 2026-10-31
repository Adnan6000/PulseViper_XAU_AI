"""
===============================================================================
Module      : frozen_c04_forward_runtime_atomic_ledgers.py
Project     : PulseViper XAU AI
Purpose     : Gate 15D-C-B2D — Lock-Atomic Runtime Ledger Authority
===============================================================================

Provides hardened append-only runtime ledger implementations for:

1. Prospective forward outcome anchors
2. TRUE_FORWARD observations

This module intentionally REUSES the already-frozen record schemas and
semantic validators from:

- frozen_c04_forward_outcome_anchor.py
- frozen_c04_shadow_observer.py

It does NOT rewrite historical record semantics.

Critical hardening:

OLD append shape:
    in-memory duplicate/conflict check
        ->
    acquire file lock
        ->
    append

That permits a multi-process race because two processes may inspect stale
in-memory indexes before either process acquires the file lock.

HARDENED append shape:
    validate candidate
        ->
    open ledger
        ->
    acquire exclusive file lock
        ->
    rebuild authoritative index from CURRENT ON-DISK contents
        ->
    duplicate/conflict decision
        ->
    append if new
        ->
    flush
        ->
    fsync
        ->
    update in-memory index

Therefore the duplicate/conflict decision and append operation are performed
within one exclusive lock transaction.

Safety:
- append-only
- no ledger truncation
- no rewrite
- no deletion
- no MT5
- no future-market access
- no outcome maturation
- no performance evaluation
- no PnL evaluation
- live_authorized = False
- execution_authorized = False
===============================================================================
"""

from __future__ import annotations

import contextlib
import importlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Generator


_anchor_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_anchor"
)

_observer_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_shadow_observer"
)


# =============================================================================
# Authority
# =============================================================================

ATOMIC_LEDGER_AUTHORITY_VERSION: str = (
    "FROZEN_C04_FORWARD_RUNTIME_ATOMIC_LEDGERS_V1"
)

ANCHOR_RECORD_VERSION: str = (
    _anchor_mod.ANCHOR_VERSION
)

ANCHOR_LEDGER_SCHEMA_VERSION: str = (
    _anchor_mod.ANCHOR_LEDGER_VERSION
)

OBSERVATION_SCHEMA_VERSION: str = (
    _observer_mod.OBSERVER_SCHEMA_VERSION
)

LOCK_TRANSACTION_POLICY: str = (
    "LOCK_THEN_REBUILD_DISK_INDEX_THEN_DECIDE_THEN_APPEND_FSYNC"
)

APPEND_ONLY: bool = True

PERFORMANCE_EVALUATION_AUTHORIZED: bool = False
PNL_EVALUATION_AUTHORIZED: bool = False
LIVE_AUTHORIZED: bool = False
EXECUTION_AUTHORIZED: bool = False


# =============================================================================
# Reused Frozen Types
# =============================================================================

FrozenC04ForwardOutcomeAnchor: Any = (
    _anchor_mod.FrozenC04ForwardOutcomeAnchor
)

AnchorAppendResult: Any = (
    _anchor_mod.AnchorAppendResult
)

AnchorDuplicateHandling: Any = (
    _anchor_mod.AnchorDuplicateHandling
)

DuplicateAnchorError: Any = (
    _anchor_mod.DuplicateAnchorError
)

ConflictingAnchorError: Any = (
    _anchor_mod.ConflictingAnchorError
)

CorruptedAnchorLedgerError: Any = (
    _anchor_mod.CorruptedAnchorLedgerError
)

InvalidAnchorError: Any = (
    _anchor_mod.InvalidAnchorError
)

validate_anchor_document: Any = (
    _anchor_mod.validate_anchor_document
)


FrozenC04ObservationRecord: Any = (
    _observer_mod.FrozenC04ObservationRecord
)

ObservationAppendResult: Any = (
    _observer_mod.AppendResult
)

ObservationDuplicateHandling: Any = (
    _observer_mod.DuplicateHandling
)

DuplicateObservationError: Any = (
    _observer_mod.DuplicateObservationError
)

ConflictingObservationError: Any = (
    _observer_mod.ConflictingObservationError
)

CorruptedObservationLedgerError: Any = (
    _observer_mod.CorruptedLedgerError
)


# =============================================================================
# Error
# =============================================================================

class AtomicRuntimeLedgerError(
    RuntimeError
):
    pass


# =============================================================================
# Authority Verification
# =============================================================================

def verify_authorities() -> bool:

    if (
        ANCHOR_RECORD_VERSION
        !=
        "FROZEN_C04_FORWARD_OUTCOME_ANCHOR_V1"
    ):
        raise AtomicRuntimeLedgerError(
            "ANCHOR_RECORD_VERSION_AUTHORITY_MISMATCH"
        )

    if (
        ANCHOR_LEDGER_SCHEMA_VERSION
        !=
        "FROZEN_C04_FORWARD_OUTCOME_ANCHOR_LEDGER_V1"
    ):
        raise AtomicRuntimeLedgerError(
            "ANCHOR_LEDGER_SCHEMA_AUTHORITY_MISMATCH"
        )

    if (
        PERFORMANCE_EVALUATION_AUTHORIZED
        or
        PNL_EVALUATION_AUTHORIZED
        or
        LIVE_AUTHORIZED
        or
        EXECUTION_AUTHORIZED
    ):
        raise AtomicRuntimeLedgerError(
            "ATOMIC_RUNTIME_LEDGER_AUTHORIZATION_BOUNDARY_VIOLATION"
        )

    return True


# =============================================================================
# Cross-Platform Exclusive File Lock
# =============================================================================

@contextlib.contextmanager
def _file_lock(
    fd: Any,
) -> Generator[
    None,
    None,
    None,
]:

    if sys.platform == "win32":

        import msvcrt

        fd.seek(
            0,
            os.SEEK_SET,
        )

        msvcrt.locking(
            fd.fileno(),
            msvcrt.LK_LOCK,
            1,
        )

        try:

            yield

        finally:

            fd.seek(
                0,
                os.SEEK_SET,
            )

            msvcrt.locking(
                fd.fileno(),
                msvcrt.LK_UNLCK,
                1,
            )

    else:

        import fcntl

        fcntl.flock(
            fd.fileno(),
            fcntl.LOCK_EX,
        )

        try:

            yield

        finally:

            fcntl.flock(
                fd.fileno(),
                fcntl.LOCK_UN,
            )


# =============================================================================
# Anchor Ledger
# =============================================================================

class AtomicFrozenC04ForwardOutcomeAnchorLedger:
    """
    Lock-atomic append-only prospective anchor ledger.

    Frozen anchor record semantics remain owned by
    frozen_c04_forward_outcome_anchor.py.

    This class changes persistence concurrency semantics only.
    """

    def __init__(
        self,
        ledger_path: Path | str,
        duplicate_handling: Any = None,
    ) -> None:

        verify_authorities()

        self._path = Path(
            ledger_path
        ).resolve()

        if duplicate_handling is None:

            duplicate_handling = (
                AnchorDuplicateHandling.FAIL_CLOSED
            )

        self._duplicate_handling = (
            duplicate_handling
        )

        self._index: dict[
            str,
            str,
        ] = {}

        if self._path.exists():

            self._rebuild_index_and_verify()

        else:

            self._path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

    @property
    def path(
        self,
    ) -> Path:

        return self._path

    def _scan_locked_handle(
        self,
        handle: Any,
    ) -> dict[str, str]:

        index: dict[
            str,
            str,
        ] = {}

        handle.seek(
            0,
            os.SEEK_SET,
        )

        for (
            line_number,
            raw_line,
        ) in enumerate(
            handle,
            start=1,
        ):

            line = (
                raw_line.strip()
            )

            if not line:

                continue

            try:

                value = json.loads(
                    line
                )

                if not isinstance(
                    value,
                    dict,
                ):

                    raise InvalidAnchorError(
                        "ANCHOR_RECORD_NOT_OBJECT"
                    )

                anchor = (
                    validate_anchor_document(
                        value
                    )
                )

            except Exception as exc:

                raise CorruptedAnchorLedgerError(
                    (
                        "ANCHOR_LEDGER_CORRUPTED:"
                        f"line={line_number}:"
                        f"{exc}"
                    )
                ) from exc

            logical_id = (
                anchor.logical_observation_id
            )

            fingerprint = (
                anchor.semantic_fingerprint()
            )

            if logical_id in index:

                existing = (
                    index[
                        logical_id
                    ]
                )

                if (
                    existing
                    !=
                    fingerprint
                ):

                    raise ConflictingAnchorError(
                        (
                            "CONFLICTING_ANCHORS_IN_LEDGER:"
                            f"{logical_id}"
                        )
                    )

            index[
                logical_id
            ] = (
                fingerprint
            )

        return index

    def _rebuild_index_and_verify(
        self,
    ) -> None:

        if not self._path.is_file():

            self._index = {}

            return

        try:

            with self._path.open(
                "r",
                encoding="utf-8",
            ) as handle:

                self._index = (
                    self._scan_locked_handle(
                        handle
                    )
                )

        except (
            CorruptedAnchorLedgerError,
            ConflictingAnchorError,
        ):

            raise

        except Exception as exc:

            raise CorruptedAnchorLedgerError(
                (
                    "FAILED_TO_VERIFY_ANCHOR_LEDGER:"
                    f"{self._path}:"
                    f"{exc}"
                )
            ) from exc

    def validate_integrity(
        self,
    ) -> bool:

        self._rebuild_index_and_verify()

        return True

    def count(
        self,
    ) -> int:

        return len(
            self._index
        )

    def append(
        self,
        anchor: Any,
    ) -> Any:

        validated = (
            validate_anchor_document(
                anchor.to_dict()
            )
        )

        logical_id = (
            validated.logical_observation_id
        )

        fingerprint = (
            validated.semantic_fingerprint()
        )

        line = (
            json.dumps(
                validated.to_dict(),
                sort_keys=True,
                separators=(
                    ",",
                    ":",
                ),
                allow_nan=False,
            )
            +
            "\n"
        )

        try:

            with self._path.open(
                "a+",
                encoding="utf-8",
            ) as handle:

                with _file_lock(
                    handle
                ):

                    disk_index = (
                        self._scan_locked_handle(
                            handle
                        )
                    )

                    if logical_id in disk_index:

                        existing = (
                            disk_index[
                                logical_id
                            ]
                        )

                        if (
                            existing
                            !=
                            fingerprint
                        ):

                            raise ConflictingAnchorError(
                                (
                                    "CONFLICTING_ANCHOR:"
                                    f"{logical_id}:"
                                    f"{existing}!="
                                    f"{fingerprint}"
                                )
                            )

                        self._index = (
                            disk_index
                        )

                        if (
                            self._duplicate_handling
                            ==
                            AnchorDuplicateHandling.FAIL_CLOSED
                        ):

                            raise DuplicateAnchorError(
                                (
                                    "DUPLICATE_ANCHOR_REJECTED:"
                                    f"{logical_id}"
                                )
                            )

                        return AnchorAppendResult(
                            record=(
                                validated
                            ),

                            is_duplicate=True,

                            appended=False,

                            message=(
                                "IDEMPOTENT_ANCHOR_DUPLICATE_IGNORED:"
                                f"{logical_id}"
                            ),
                        )

                    handle.seek(
                        0,
                        os.SEEK_END,
                    )

                    handle.write(
                        line
                    )

                    handle.flush()

                    os.fsync(
                        handle.fileno()
                    )

                    disk_index[
                        logical_id
                    ] = (
                        fingerprint
                    )

                    self._index = (
                        disk_index
                    )

        except (
            DuplicateAnchorError,
            ConflictingAnchorError,
            CorruptedAnchorLedgerError,
        ):

            raise

        except Exception as exc:

            raise CorruptedAnchorLedgerError(
                (
                    "FAILED_TO_APPEND_ANCHOR:"
                    f"{self._path}:"
                    f"{exc}"
                )
            ) from exc

        return AnchorAppendResult(
            record=(
                validated
            ),

            is_duplicate=False,

            appended=True,

            message=(
                "ANCHOR_RECORDED:"
                f"{logical_id}"
            ),
        )

    def read_all(
        self,
    ) -> list[Any]:

        records: list[
            Any
        ] = []

        if not self._path.exists():

            return records

        try:

            with self._path.open(
                "r",
                encoding="utf-8",
            ) as handle:

                for (
                    line_number,
                    raw_line,
                ) in enumerate(
                    handle,
                    start=1,
                ):

                    line = (
                        raw_line.strip()
                    )

                    if not line:

                        continue

                    try:

                        value = json.loads(
                            line
                        )

                        if not isinstance(
                            value,
                            dict,
                        ):

                            raise InvalidAnchorError(
                                "ANCHOR_RECORD_NOT_OBJECT"
                            )

                        records.append(
                            validate_anchor_document(
                                value
                            )
                        )

                    except Exception as exc:

                        raise CorruptedAnchorLedgerError(
                            (
                                "ANCHOR_LEDGER_CORRUPTED:"
                                f"line={line_number}:"
                                f"{exc}"
                            )
                        ) from exc

        except (
            CorruptedAnchorLedgerError,
        ):

            raise

        except Exception as exc:

            raise CorruptedAnchorLedgerError(
                (
                    "FAILED_TO_READ_ANCHOR_LEDGER:"
                    f"{self._path}:"
                    f"{exc}"
                )
            ) from exc

        return records


# =============================================================================
# Observation Ledger
# =============================================================================

class AtomicFrozenC04ObservationLedger:
    """
    Lock-atomic append-only TRUE_FORWARD observation ledger.

    Observation schema and semantic fingerprint remain owned by
    frozen_c04_shadow_observer.py.

    This class changes persistence concurrency semantics only.
    """

    def __init__(
        self,
        ledger_path: Path | str,
        duplicate_handling: Any = None,
    ) -> None:

        verify_authorities()

        self._path = Path(
            ledger_path
        ).resolve()

        if duplicate_handling is None:

            duplicate_handling = (
                ObservationDuplicateHandling.FAIL_CLOSED
            )

        self._duplicate_handling = (
            duplicate_handling
        )

        self._index: dict[
            str,
            str,
        ] = {}

        if self._path.exists():

            self._rebuild_index_and_verify()

        else:

            self._path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

    @property
    def path(
        self,
    ) -> Path:

        return self._path

    def _scan_locked_handle(
        self,
        handle: Any,
    ) -> dict[str, str]:

        index: dict[
            str,
            str,
        ] = {}

        handle.seek(
            0,
            os.SEEK_SET,
        )

        for (
            line_number,
            raw_line,
        ) in enumerate(
            handle,
            start=1,
        ):

            line = (
                raw_line.strip()
            )

            if not line:

                continue

            try:

                value = json.loads(
                    line
                )

                if not isinstance(
                    value,
                    dict,
                ):

                    raise CorruptedObservationLedgerError(
                        "OBSERVATION_RECORD_NOT_OBJECT"
                    )

                record = (
                    FrozenC04ObservationRecord
                    .from_dict(
                        value
                    )
                )

            except Exception as exc:

                raise CorruptedObservationLedgerError(
                    (
                        "OBSERVATION_LEDGER_CORRUPTED:"
                        f"line={line_number}:"
                        f"{exc}"
                    )
                ) from exc

            logical_id = (
                record.logical_observation_id
            )

            semantic_fp = (
                record.semantic_record_fingerprint
            )

            if logical_id in index:

                existing = (
                    index[
                        logical_id
                    ]
                )

                if (
                    existing
                    !=
                    semantic_fp
                ):

                    raise ConflictingObservationError(
                        (
                            "CONFLICTING_OBSERVATIONS_IN_LEDGER:"
                            f"{logical_id}"
                        )
                    )

            index[
                logical_id
            ] = (
                semantic_fp
            )

        return index

    def _rebuild_index_and_verify(
        self,
    ) -> None:

        if not self._path.is_file():

            self._index = {}

            return

        try:

            with self._path.open(
                "r",
                encoding="utf-8",
            ) as handle:

                self._index = (
                    self._scan_locked_handle(
                        handle
                    )
                )

        except (
            CorruptedObservationLedgerError,
            ConflictingObservationError,
        ):

            raise

        except Exception as exc:

            raise CorruptedObservationLedgerError(
                (
                    "FAILED_TO_VERIFY_OBSERVATION_LEDGER:"
                    f"{self._path}:"
                    f"{exc}"
                )
            ) from exc

    def validate_integrity(
        self,
    ) -> bool:

        self._rebuild_index_and_verify()

        return True

    def count(
        self,
    ) -> int:

        return len(
            self._index
        )

    def append(
        self,
        record: Any,
    ) -> Any:

        if not isinstance(
            record,
            FrozenC04ObservationRecord,
        ):

            raise CorruptedObservationLedgerError(
                "OBSERVATION_RECORD_TYPE_INVALID"
            )

        logical_id = (
            record.logical_observation_id
        )

        semantic_fp = (
            record.semantic_record_fingerprint
        )

        line = (
            record.to_json()
            +
            "\n"
        )

        try:

            with self._path.open(
                "a+",
                encoding="utf-8",
            ) as handle:

                with _file_lock(
                    handle
                ):

                    disk_index = (
                        self._scan_locked_handle(
                            handle
                        )
                    )

                    if logical_id in disk_index:

                        existing = (
                            disk_index[
                                logical_id
                            ]
                        )

                        if (
                            existing
                            !=
                            semantic_fp
                        ):

                            raise ConflictingObservationError(
                                (
                                    "CONFLICTING_OBSERVATION:"
                                    f"{logical_id}:"
                                    f"{existing}!="
                                    f"{semantic_fp}"
                                )
                            )

                        self._index = (
                            disk_index
                        )

                        if (
                            self._duplicate_handling
                            ==
                            ObservationDuplicateHandling.FAIL_CLOSED
                        ):

                            raise DuplicateObservationError(
                                (
                                    "DUPLICATE_OBSERVATION_REJECTED:"
                                    f"{logical_id}"
                                )
                            )

                        return ObservationAppendResult(
                            record=(
                                record
                            ),

                            is_duplicate=True,

                            appended=False,

                            message=(
                                "IDEMPOTENT_OBSERVATION_DUPLICATE_IGNORED:"
                                f"{logical_id}"
                            ),
                        )

                    handle.seek(
                        0,
                        os.SEEK_END,
                    )

                    handle.write(
                        line
                    )

                    handle.flush()

                    os.fsync(
                        handle.fileno()
                    )

                    disk_index[
                        logical_id
                    ] = (
                        semantic_fp
                    )

                    self._index = (
                        disk_index
                    )

        except (
            DuplicateObservationError,
            ConflictingObservationError,
            CorruptedObservationLedgerError,
        ):

            raise

        except Exception as exc:

            raise CorruptedObservationLedgerError(
                (
                    "FAILED_TO_APPEND_OBSERVATION:"
                    f"{self._path}:"
                    f"{exc}"
                )
            ) from exc

        return ObservationAppendResult(
            record=(
                record
            ),

            is_duplicate=False,

            appended=True,

            message=(
                "OBSERVATION_RECORDED:"
                f"{logical_id}"
            ),
        )

    def read_all(
        self,
    ) -> list[Any]:

        records: list[
            Any
        ] = []

        if not self._path.exists():

            return records

        try:

            with self._path.open(
                "r",
                encoding="utf-8",
            ) as handle:

                for (
                    line_number,
                    raw_line,
                ) in enumerate(
                    handle,
                    start=1,
                ):

                    line = (
                        raw_line.strip()
                    )

                    if not line:

                        continue

                    try:

                        value = json.loads(
                            line
                        )

                        if not isinstance(
                            value,
                            dict,
                        ):

                            raise CorruptedObservationLedgerError(
                                "OBSERVATION_RECORD_NOT_OBJECT"
                            )

                        records.append(
                            FrozenC04ObservationRecord
                            .from_dict(
                                value
                            )
                        )

                    except Exception as exc:

                        raise CorruptedObservationLedgerError(
                            (
                                "OBSERVATION_LEDGER_CORRUPTED:"
                                f"line={line_number}:"
                                f"{exc}"
                            )
                        ) from exc

        except (
            CorruptedObservationLedgerError,
        ):

            raise

        except Exception as exc:

            raise CorruptedObservationLedgerError(
                (
                    "FAILED_TO_READ_OBSERVATION_LEDGER:"
                    f"{self._path}:"
                    f"{exc}"
                )
            ) from exc

        return records