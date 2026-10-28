
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from typing import Any, Mapping

VERSION = "R03_V2_AUTHORITY_GUARD_V1"

EXPECTED_ID = (
    "febaf847ef5cd078cfc0e8223eb2120c81969a91645998968e9a1083caa1c1f8"
)

ROOT = Path(__file__).resolve().parents[2]


class AuthorityError(RuntimeError):
    pass


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise AuthorityError(reason)


def validate_recovery(
    *,
    original: Mapping[str, Any],
    candidate: Mapping[str, Any],
    terminal: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Evaluate authority without granting it.

    Diagnostic evidence is never promotion authority.
    """

    require(
        original["observation_count"] == candidate["observations"],
        "OBSERVATION_COUNT_CHANGED",
    )

    require(
        original["anchor_count"] == candidate["anchors"],
        "ANCHOR_COUNT_CHANGED",
    )

    require(
        original["matured_outcome_count"]
        == candidate["matured_outcomes"],
        "MATURED_COUNT_CHANGED",
    )

    require(
        original["pending_count"] == 1,
        "ORIGINAL_PENDING_NOT_ONE",
    )

    require(
        original["pending_logical_observation_id"] == EXPECTED_ID,
        "PENDING_ID_MISMATCH",
    )

    require(
        candidate["terminal_exclusions"] == 1,
        "TERMINAL_RECORD_NOT_ONE",
    )

    require(
        candidate["unresolved_pending"] == 0,
        "CANDIDATE_PENDING_NOT_ZERO",
    )

    require(
        terminal["logical_observation_id"] == EXPECTED_ID,
        "TERMINAL_ID_MISMATCH",
    )

    require(
        terminal["counts_as_matured_outcome"] is False,
        "TERMINAL_COUNTS_AS_MATURED",
    )

    require(
        evidence["logical_observation_id"] == EXPECTED_ID,
        "EVIDENCE_ID_MISMATCH",
    )

    require(
        evidence["terminal_exclusion_authorized"] is False,
        "EVIDENCE_AUTHORITY_UNEXPECTED",
    )

    require(
        evidence["controller_promotion_authorized"] is False,
        "EVIDENCE_PROMOTION_UNEXPECTED",
    )

    require(
        terminal["source_event_fingerprint_sha256"]
        == evidence["event_fingerprint_sha256"],
        "EVENT_FINGERPRINT_MISMATCH",
    )

    return {
        "version": VERSION,
        "status": "PASS_DIAGNOSTIC_RECONCILIATION_ONLY",
        "observation_count": original["observation_count"],
        "anchor_count": original["anchor_count"],
        "matured_outcome_count": original["matured_outcome_count"],
        "v1_pending_count": 1,
        "v2_candidate_pending_count": 0,
        "terminal_evidence_count": 1,
        "terminal_disposition_authorized": False,
        "effective_unresolved_pending_count": 1,
        "next_action": (
            "BLOCKED_AWAITING_INDEPENDENT_V2_PROTOCOL_AUTHORITY"
        ),
        "capture_authorized": False,
        "ledger_writes_authorized": False,
        "live_authorized": False,
        "execution_authorized": False,
    }


def audit() -> dict[str, Any]:
    controller = importlib.import_module(
        "02_AI.Models.r03_prospective_collection_controller"
    )

    recovery = importlib.import_module(
        "04_Testing.production_portability.r03_collection_v2_recovery"
    )

    events_module = importlib.import_module(
        "04_Testing.production_portability."
        "r03_session_gap_evidence_ledger_r4"
    )

    original = controller.inspect_state(repo_root=ROOT)

    candidate = recovery.inspect_v2(repo_root=ROOT)

    terminals = recovery.read_terminal_ledger()

    events = events_module.read_events(
        events_module.DEFAULT_LEDGER
    )

    require(
        len(terminals) == 1 and EXPECTED_ID in terminals,
        "TERMINAL_LEDGER_INVALID",
    )

    require(
        len(events) == 1,
        "DIAGNOSTIC_EVENT_COUNT_INVALID",
    )

    event = events[0]

    events_module.validate_document(event)

    recovery.validate_terminal_document(
        terminals[EXPECTED_ID]
    )

    result = validate_recovery(
        original=original.to_dict(),
        candidate=candidate.to_dict(),
        terminal=terminals[EXPECTED_ID],
        evidence=event,
    )

    require(
        controller.inspect_state(repo_root=ROOT).to_dict()
        == original.to_dict(),
        "V1_STATE_CHANGED_DURING_AUDIT",
    )

    return result


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--json",
        action="store_true",
    )

    parser.parse_args()

    try:
        result = audit()

    except Exception as exc:
        print("R03_V2_AUTHORITY_STATUS=BLOCKED")
        print(f"ERROR_TYPE={type(exc).__name__}")
        print(f"ERROR={exc}")
        print("CAPTURE_AUTHORIZED=false")
        return 2

    print("R03_V2_AUTHORITY_STATUS=PASS_DIAGNOSTIC_ONLY")

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
