from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


VERSION = "R03_COLLECTION_V2_RECOVERY_V1"

REPO_ROOT = Path(__file__).resolve().parents[2]

TERMINAL_LEDGER = Path(
    "D:/PulseViper_R03_Recovery_Backup/"
    "r03_v2_terminal_dispositions.jsonl"
)

PROTOCOL = "STRICT_CONTIGUOUS_M5_SESSION_GAP_EXCLUSION_V1"

controller: Any = importlib.import_module(
    "02_AI.Models.r03_prospective_collection_controller"
)

evidence: Any = importlib.import_module(
    "04_Testing.production_portability."
    "r03_session_gap_evidence_ledger_r4"
)

preflight: Any = importlib.import_module(
    "04_Testing.production_portability."
    "run_r03_r4_authority_preflight"
)


class V2RecoveryError(RuntimeError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise V2RecoveryError(reason)


def canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def fingerprint(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        canonical_bytes(value)
    ).hexdigest()


def terminal_document(
    *,
    observation_id: str,
    source_event_fingerprint: str,
    source_file_sha256: str,
    observation_fingerprint: str,
    anchor_fingerprint: str,
) -> dict[str, Any]:

    core = {
        "schema_version": VERSION,
        "protocol": PROTOCOL,
        "disposition": "UNSCORABLE_SESSION_GAP",
        "logical_observation_id": observation_id,
        "source_event_fingerprint_sha256": (
            source_event_fingerprint
        ),
        "source_evidence_file_sha256": (
            source_file_sha256
        ),
        "observation_fingerprint": observation_fingerprint,
        "anchor_fingerprint": anchor_fingerprint,
        "counts_as_matured_outcome": False,
        "performance_evaluated": False,
        "pnl_evaluated": False,
        "live_authorized": False,
        "execution_authorized": False,
    }

    return {
        **core,
        "semantic_fingerprint_sha256": fingerprint(core),
    }


def validate_terminal_document(
    document: Mapping[str, Any],
) -> None:

    require(
        document.get("schema_version") == VERSION,
        "TERMINAL_SCHEMA_MISMATCH",
    )

    require(
        document.get("protocol") == PROTOCOL,
        "TERMINAL_PROTOCOL_MISMATCH",
    )

    require(
        document.get("disposition")
        == "UNSCORABLE_SESSION_GAP",
        "TERMINAL_DISPOSITION_MISMATCH",
    )

    for name in (
        "counts_as_matured_outcome",
        "performance_evaluated",
        "pnl_evaluated",
        "live_authorized",
        "execution_authorized",
    ):
        require(
            document.get(name) is False,
            f"UNAUTHORIZED_FLAG:{name}",
        )

    for name in (
        "source_event_fingerprint_sha256",
        "source_evidence_file_sha256",
        "observation_fingerprint",
        "anchor_fingerprint",
    ):
        value = document.get(name)

        require(
            isinstance(value, str)
            and len(value) == 64
            and all(c in "0123456789abcdef" for c in value),
            f"INVALID_FINGERPRINT:{name}",
        )

    core = dict(document)
    supplied = core.pop("semantic_fingerprint_sha256", None)

    require(
        set(core) == {
            "schema_version",
            "protocol",
            "disposition",
            "logical_observation_id",
            "source_event_fingerprint_sha256",
            "source_evidence_file_sha256",
            "observation_fingerprint",
            "anchor_fingerprint",
            "counts_as_matured_outcome",
            "performance_evaluated",
            "pnl_evaluated",
            "live_authorized",
            "execution_authorized",
        },
        "UNEXPECTED_TERMINAL_FIELDS",
    )

    require(
        supplied == fingerprint(core),
        "TERMINAL_FINGERPRINT_MISMATCH",
    )


def read_terminal_ledger(
    path: Path = TERMINAL_LEDGER,
) -> dict[str, dict[str, Any]]:

    if not path.exists():
        return {}

    require(path.is_file(), "TERMINAL_PATH_NOT_FILE")

    data = path.read_bytes()

    require(
        not data or data.endswith(b"\n"),
        "TERMINAL_LEDGER_PARTIAL_RECORD",
    )

    records: dict[str, dict[str, Any]] = {}

    for number, line in enumerate(data.splitlines(), start=1):
        require(bool(line.strip()), f"EMPTY_RECORD:{number}")

        try:
            document = json.loads(line.decode("utf-8"))
        except (ValueError, UnicodeError) as exc:
            raise V2RecoveryError(
                f"INVALID_JSON:{number}"
            ) from exc

        require(
            isinstance(document, dict),
            f"NON_OBJECT_RECORD:{number}",
        )

        validate_terminal_document(document)

        logical_id = document["logical_observation_id"]

        require(
            logical_id not in records,
            f"DUPLICATE_TERMINAL_RECORD:{logical_id}",
        )

        records[logical_id] = document

    return records


def verify_source_authority(
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:

    result = preflight.run_preflight(
        repo_root=repo_root,
        evidence_path=evidence.DEFAULT_LEDGER,
    )

    require(
        result["status"] == "PASS_DIAGNOSTIC_AUTHORITY_ONLY",
        "R4_PREFLIGHT_NOT_PASS",
    )

    events = evidence.read_events(evidence.DEFAULT_LEDGER)

    require(len(events) == 1, "EXPECTED_ONE_GAP_EVENT")

    event = events[0]
    evidence.validate_document(event)

    logical_id = event["logical_observation_id"]

    observations = controller.read_observations(
        repo_root=repo_root
    )
    anchors = controller.read_anchors(
        repo_root=repo_root
    )
    outcomes = controller.read_outcomes(
        repo_root=repo_root
    )

    require(logical_id in observations, "OBSERVATION_MISSING")
    require(logical_id in anchors, "ANCHOR_MISSING")
    require(logical_id not in outcomes, "ALREADY_MATURED")

    observation = observations[logical_id]
    anchor = anchors[logical_id]

    require(
        observation.semantic_record_fingerprint
        == anchor.semantic_observation_fingerprint,
        "OBSERVATION_ANCHOR_MISMATCH",
    )

    return terminal_document(
        observation_id=logical_id,
        source_event_fingerprint=event[
            "event_fingerprint_sha256"
        ],
        source_file_sha256=result["evidence_sha256"],
        observation_fingerprint=(
            observation.semantic_record_fingerprint
        ),
        anchor_fingerprint=anchor.anchor_semantic_fingerprint,
    )


def append_terminal_once(
    *,
    path: Path = TERMINAL_LEDGER,
    repo_root: Path = REPO_ROOT,
) -> str:

    document = verify_source_authority(repo_root=repo_root)

    require(
        path.parent.is_dir(),
        "TERMINAL_PARENT_DIRECTORY_MISSING",
    )

    lock = path.with_name(path.name + ".lock")
    owned = False

    try:
        try:
            fd = os.open(
                str(lock),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
        except FileExistsError as exc:
            raise V2RecoveryError(
                "TERMINAL_LEDGER_LOCKED"
            ) from exc

        owned = True
        os.close(fd)

        existing = read_terminal_ledger(path)

        logical_id = document["logical_observation_id"]

        if logical_id in existing:
            require(
                existing[logical_id] == document,
                "TERMINAL_RECORD_CONFLICT",
            )
            return "IDEMPOTENT_ALREADY_PRESENT"

        require(
            not existing,
            "UNEXPECTED_OTHER_TERMINAL_RECORDS",
        )

        payload = canonical_bytes(document) + b"\n"

        with path.open("ab") as handle:
            require(
                handle.write(payload) == len(payload),
                "SHORT_TERMINAL_WRITE",
            )
            handle.flush()
            os.fsync(handle.fileno())

        verified = read_terminal_ledger(path)

        require(
            verified.get(logical_id) == document,
            "POST_APPEND_TERMINAL_INTEGRITY_FAILURE",
        )

        return "TERMINAL_EVIDENCE_APPENDED"

    finally:
        if owned:
            lock.unlink()


@dataclass(frozen=True)
class RecoveryState:
    observations: int
    anchors: int
    matured: int
    terminal: int
    pending: int
    next_action_candidate: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": VERSION,
            "observations": self.observations,
            "anchors": self.anchors,
            "matured_outcomes": self.matured,
            "terminal_exclusions": self.terminal,
            "unresolved_pending": self.pending,
            "next_action_candidate": self.next_action_candidate,
            "capture_authorized": False,
            "performance_evaluated": False,
            "pnl_evaluated": False,
            "live_authorized": False,
            "execution_authorized": False,
        }


def inspect_v2(
    *,
    repo_root: Path = REPO_ROOT,
    terminal_path: Path = TERMINAL_LEDGER,
) -> RecoveryState:

    observations = controller.read_observations(
        repo_root=repo_root
    )
    anchors = controller.read_anchors(
        repo_root=repo_root
    )
    outcomes = controller.read_outcomes(
        repo_root=repo_root
    )
    terminals = read_terminal_ledger(terminal_path)

    observation_ids = set(observations)
    anchor_ids = set(anchors)
    outcome_ids = set(outcomes)
    terminal_ids = set(terminals)

    require(
        observation_ids <= anchor_ids,
        "OBSERVATION_WITHOUT_ANCHOR",
    )
    require(
        outcome_ids <= observation_ids,
        "OUTCOME_WITHOUT_OBSERVATION",
    )
    require(
        terminal_ids <= observation_ids,
        "TERMINAL_WITHOUT_OBSERVATION",
    )
    require(
        not (outcome_ids & terminal_ids),
        "TERMINAL_OUTCOME_CONFLICT",
    )

    require(
        anchor_ids <= observation_ids,
        "ORPHAN_ANCHOR_BLOCK",
    )

    if terminal_ids:
        expected = verify_source_authority(repo_root=repo_root)
        require(
            terminals.get(expected["logical_observation_id"])
            == expected,
            "TERMINAL_SOURCE_AUTHORITY_MISMATCH",
        )

    pending_ids = (
        observation_ids - outcome_ids - terminal_ids
    )

    require(
        len(pending_ids) <= 1,
        "MULTIPLE_UNRESOLVED_PENDING",
    )

    action = (
        "CANDIDATE_CHECK_MATURITY"
        if pending_ids
        else "CANDIDATE_CAPTURE_NEW_OBSERVATION"
    )

    return RecoveryState(
        observations=len(observation_ids),
        anchors=len(anchor_ids),
        matured=len(outcome_ids),
        terminal=len(terminal_ids),
        pending=len(pending_ids),
        next_action_candidate=action,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--record-terminal",
        action="store_true",
    )
    args = parser.parse_args()

    try:
        if args.record_terminal:
            print(
                "R03_V2_TERMINAL_STATUS="
                + append_terminal_once()
            )

        state = inspect_v2()

        print("R03_V2_STATUS=PASS_RECONCILED")
        print(json.dumps(state.to_dict(), indent=2))
        return 0

    except Exception as exc:
        print("R03_V2_STATUS=BLOCKED")
        print("ERROR_TYPE=" + type(exc).__name__)
        print("ERROR=" + str(exc))
        print("CAPTURE_AUTHORIZED=false")
        print("LIVE_AUTHORIZED=false")
        print("EXECUTION_AUTHORIZED=false")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())