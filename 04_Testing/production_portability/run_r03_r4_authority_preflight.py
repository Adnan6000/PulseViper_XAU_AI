from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from typing import Any


VERSION = "R03_R4_AUTHORITY_PREFLIGHT_V1"

REPO_ROOT = Path(__file__).resolve().parents[2]

ledger = importlib.import_module(
    "04_Testing.production_portability."
    "r03_session_gap_evidence_ledger_r4"
)

resolution = importlib.import_module(
    "04_Testing.production_portability."
    "r03_terminal_resolution_r4"
)

controller = importlib.import_module(
    "02_AI.Models.r03_prospective_collection_controller"
)


class R4AuthorityError(RuntimeError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise R4AuthorityError(reason)


def file_hash(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def run_preflight(
    *,
    repo_root: Path = REPO_ROOT,
    evidence_path: Path = ledger.DEFAULT_LEDGER,
) -> dict[str, Any]:

    require(
        evidence_path.is_file(),
        "R4_EVIDENCE_FILE_MISSING",
    )

    evidence_hash_before = file_hash(evidence_path)

    events = ledger.read_events(evidence_path)

    require(
        len(events) == 1,
        "EXPECTED_EXACTLY_ONE_EVIDENCE_EVENT",
    )

    event = events[0]

    ledger.validate_document(event)

    require(
        event["event_type"]
        == "R03_SESSION_GAP_DIAGNOSTIC",
        "UNEXPECTED_EVENT_TYPE",
    )

    require(
        event["terminal_exclusion_authorized"] is False,
        "UNAUTHORIZED_TERMINAL_EXCLUSION",
    )

    require(
        event["controller_promotion_authorized"] is False,
        "UNAUTHORIZED_CONTROLLER_PROMOTION",
    )

    require(
        event["counts_as_matured_outcome"] is False,
        "DIAGNOSTIC_COUNTED_AS_OUTCOME",
    )

    source = event["source_document"]

    resolution.validate_exclusion_document(source)

    require(
        event["logical_observation_id"]
        == source["logical_observation_id"],
        "EVIDENCE_OBSERVATION_ID_MISMATCH",
    )

    before = controller.inspect_state(
        repo_root=repo_root
    )

    require(
        before.pending_count == 1,
        "EXPECTED_EXACTLY_ONE_PENDING",
    )

    require(
        before.pending_logical_observation_id
        == event["logical_observation_id"],
        "PENDING_ID_EVIDENCE_MISMATCH",
    )

    require(
        before.next_action
        == controller.ACTION_CHECK_PENDING_MATURITY,
        "PENDING_ACTION_MISMATCH",
    )

    reconciled = resolution.reconcile(
        repo_root=repo_root,
        exclusion_document=source,
    )

    require(
        reconciled.matured_outcome_count
        == before.matured_outcome_count,
        "MATURED_COUNT_CHANGED",
    )

    require(
        reconciled.excluded_count == 1,
        "EXCLUSION_CLASSIFICATION_MISSING",
    )

    require(
        reconciled.unresolved_pending_count == 0,
        "RECONCILIATION_PENDING_MISMATCH",
    )

    require(
        reconciled.original_pending_count == 1,
        "ORIGINAL_PENDING_NOT_PRESERVED",
    )

    after = controller.inspect_state(
        repo_root=repo_root
    )

    require(
        after.to_dict() == before.to_dict(),
        "CONTROLLER_STATE_CHANGED",
    )

    require(
        file_hash(evidence_path)
        == evidence_hash_before,
        "EVIDENCE_CHANGED_DURING_PREFLIGHT",
    )

    return {
        "version": VERSION,
        "status": "PASS_DIAGNOSTIC_AUTHORITY_ONLY",
        "pending_logical_observation_id": (
            event["logical_observation_id"]
        ),
        "evidence_sha256": evidence_hash_before,
        "evidence_event_count": len(events),
        "original_state": before.to_dict(),
        "reconciled_candidate_state": (
            reconciled.to_dict()
        ),
        "ledgers_written": False,
        "terminal_exclusion_authorized": False,
        "controller_promotion_authorized": False,
        "new_capture_authorized": False,
        "performance_evaluated": False,
        "pnl_evaluated": False,
        "live_authorized": False,
        "execution_authorized": False,
    }


def main() -> int:
    print("R03_R4_PREFLIGHT_VERSION=" + VERSION)

    try:
        result = run_preflight()

    except Exception as exc:
        print("R03_R4_PREFLIGHT_STATUS=BLOCKED")
        print("ERROR_TYPE=" + type(exc).__name__)
        print("ERROR=" + str(exc))
        print("LEDGERS_WRITTEN=false")
        print("CONTROLLER_PROMOTION_AUTHORIZED=false")
        print("LIVE_AUTHORIZED=false")
        print("EXECUTION_AUTHORIZED=false")
        return 2

    print("R03_R4_PREFLIGHT_STATUS=PASS")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())