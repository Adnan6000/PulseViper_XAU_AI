from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
from typing import Any, Mapping


VERSION = "R03_SESSION_GAP_EVIDENCE_LEDGER_R4_V1"

resolution: Any = importlib.import_module(
    "04_Testing.production_portability.r03_terminal_resolution_r4"
)

DEFAULT_LEDGER = (
    Path("D:/PulseViper_R03_Recovery_Backup")
    / "r03_session_gap_evidence.jsonl"
)


class R03EvidenceLedgerError(RuntimeError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise R03EvidenceLedgerError(reason)


def canonical_bytes(document: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(document),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        ensure_ascii=True,
    ).encode("utf-8")


def evidence_document() -> dict[str, Any]:
    """
    Deterministic diagnostic evidence only.

    This event does not authorize terminal exclusion,
    controller promotion, model evaluation or trading.
    """
    source = resolution.expected_exclusion_document()

    require(
        resolution.validate_exclusion_document(source),
        "SOURCE_EVIDENCE_INVALID",
    )

    core = {
        "schema_version": VERSION,
        "event_type": "R03_SESSION_GAP_DIAGNOSTIC",
        "logical_observation_id": source[
            "logical_observation_id"
        ],
        "source_document": source,
        "counts_as_matured_outcome": False,
        "terminal_exclusion_authorized": False,
        "controller_promotion_authorized": False,
        "performance_evaluated": False,
        "pnl_evaluated": False,
        "live_authorized": False,
        "execution_authorized": False,
    }

    return {
        **core,
        "event_fingerprint_sha256": hashlib.sha256(
            canonical_bytes(core)
        ).hexdigest(),
    }


def validate_document(document: Mapping[str, Any]) -> None:
    require(
        dict(document) == evidence_document(),
        "EVIDENCE_DOCUMENT_MISMATCH",
    )


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    require(
        path.is_file(),
        "LEDGER_PATH_NOT_FILE",
    )

    data = path.read_bytes()

    require(
        not data or data.endswith(b"\n"),
        "LEDGER_PARTIAL_FINAL_RECORD",
    )

    events: list[dict[str, Any]] = []

    for line_number, raw in enumerate(
        data.splitlines(),
        start=1,
    ):
        require(
            bool(raw.strip()),
            f"EMPTY_LEDGER_RECORD:{line_number}",
        )

        try:
            record = json.loads(
                raw.decode("utf-8")
            )
        except (ValueError, UnicodeError) as exc:
            raise R03EvidenceLedgerError(
                f"INVALID_LEDGER_JSON:{line_number}"
            ) from exc

        require(
            isinstance(record, dict),
            f"LEDGER_RECORD_NOT_OBJECT:{line_number}",
        )

        validate_document(record)

        require(
            not events,
            "DUPLICATE_LEDGER_EVENT",
        )

        events.append(record)

    return events


def append_once(
    *,
    path: Path = DEFAULT_LEDGER,
) -> str:
    """
    Append exactly one diagnostic event.

    Guarantees:
    - Exclusive lock creation.
    - Existing evidence bytes are never rewritten.
    - Repeated valid append is idempotent.
    - Conflicting or partial ledger data fails closed.
    - Only this invocation's acquired lock is released.
    """
    document = evidence_document()
    validate_document(document)

    require(
        path.parent.is_dir(),
        "EVIDENCE_PARENT_DIRECTORY_MISSING",
    )

    lock_path = path.with_name(
        path.name + ".lock"
    )

    lock_fd: int | None = None
    owned_lock = False

    try:
        try:
            lock_fd = os.open(
                str(lock_path),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
            owned_lock = True

        except FileExistsError as exc:
            raise R03EvidenceLedgerError(
                "EVIDENCE_LEDGER_LOCKED"
            ) from exc

        finally:
            if lock_fd is not None:
                os.close(lock_fd)
                lock_fd = None

        existing = read_events(path)

        if existing:
            require(
                len(existing) == 1,
                "INVALID_EXISTING_EVIDENCE_COUNT",
            )
            return "IDEMPOTENT_ALREADY_RECORDED"

        payload = canonical_bytes(document) + b"\n"

        with path.open("ab") as handle:
            written = handle.write(payload)

            require(
                written == len(payload),
                "SHORT_LEDGER_WRITE",
            )

            handle.flush()
            os.fsync(handle.fileno())

        verified = read_events(path)

        require(
            len(verified) == 1,
            "POST_APPEND_INTEGRITY_FAILED",
        )

        require(
            verified[0] == document,
            "POST_APPEND_DOCUMENT_MISMATCH",
        )

        return "DIAGNOSTIC_EVIDENCE_APPENDED"

    finally:
        if lock_fd is not None:
            os.close(lock_fd)

        if owned_lock:
            lock_path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
    )

    parser.add_argument(
        "--record",
        action="store_true",
    )

    args = parser.parse_args()

    try:
        if args.record:
            result = append_once(
                path=args.ledger
            )
        else:
            events = read_events(
                args.ledger
            )

            result = (
                "EVIDENCE_PRESENT"
                if events
                else "EVIDENCE_ABSENT"
            )

        print(
            "R03_R4_EVIDENCE_STATUS=" + result
        )
        print(
            "LEDGER=" + str(args.ledger)
        )
        print(
            "TERMINAL_EXCLUSION_AUTHORIZED=false"
        )
        print(
            "CONTROLLER_PROMOTION_AUTHORIZED=false"
        )
        print("LIVE_AUTHORIZED=false")
        print("EXECUTION_AUTHORIZED=false")

        return 0

    except Exception as exc:
        print("R03_R4_EVIDENCE_STATUS=BLOCKED")
        print(
            "ERROR_TYPE=" + type(exc).__name__
        )
        print(
            "ERROR=" + str(exc)
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())