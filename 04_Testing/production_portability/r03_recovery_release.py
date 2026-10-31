from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any, Mapping

VERSION = "R03_RECOVERY_RELEASE_V1"

REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_PENDING_ID = (
    "febaf847ef5cd078cfc0e8223eb2120c81969a91645998968e9a1083caa1c1f8"
)

EXPECTED_EVIDENCE_SHA256 = (
    "0a38f50d02c1844218be6f7863c12d0e2c4b132572f24e780d528534703f8ca5"
)

EXPECTED_DECISION = "2026-10-05T20:35:00+00:00"
EXPECTED_LAST = "2026-10-05T21:30:00+00:00"
ACTUAL_LAST = "2026-10-05T22:30:00+00:00"


class RecoveryBlocked(RuntimeError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RecoveryBlocked(reason)


def sha256_file(path: Path) -> str:
    require(path.is_file(), f"MISSING_FILE:{path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_document(
    event: Mapping[str, Any],
) -> dict[str, Any]:
    evidence = importlib.import_module(
        "04_Testing.production_portability."
        "r03_session_gap_evidence_ledger_r4"
    )

    evidence.validate_document(event)

    source = event["source_document"]

    require(
        event["logical_observation_id"] == EXPECTED_PENDING_ID,
        "ID_MISMATCH",
    )
    require(
        source["decision_time_utc"] == EXPECTED_DECISION,
        "DECISION_TIME_MISMATCH",
    )
    require(
        source["expected_last_future_bar_utc"] == EXPECTED_LAST,
        "EXPECTED_HORIZON_MISMATCH",
    )
    require(
        source["actual_last_future_bar_utc"] == ACTUAL_LAST,
        "ACTUAL_HORIZON_MISMATCH",
    )
    require(
        len(source["missing_m5_timestamps_utc"]) == 7,
        "SESSION_GAP_EVIDENCE_MISMATCH",
    )

    for key in (
        "counts_as_matured_outcome",
        "terminal_exclusion_authorized",
        "controller_promotion_authorized",
        "live_authorized",
        "execution_authorized",
    ):
        require(
            event[key] is False,
            f"UNEXPECTED_AUTHORIZATION:{key}",
        )

    return dict(source)


def audit(
    *,
    evidence_path: Path,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:

    controller = importlib.import_module(
        "02_AI.Models.r03_prospective_collection_controller"
    )
    maturer = importlib.import_module(
        "02_AI.Models.frozen_r03_prospective_outcome_maturer"
    )
    contract = importlib.import_module(
        "02_AI.Models."
        "frozen_r03_prospective_forward_validation_contract"
    )
    evidence = importlib.import_module(
        "04_Testing.production_portability."
        "r03_session_gap_evidence_ledger_r4"
    )

    before_hash = sha256_file(evidence_path)

    require(
        before_hash == EXPECTED_EVIDENCE_SHA256,
        "EVIDENCE_FILE_SHA256_MISMATCH",
    )

    events = evidence.read_events(evidence_path)

    require(
        len(events) == 1,
        "EVIDENCE_EVENT_COUNT_NOT_ONE",
    )

    source = check_document(events[0])

    require(
        maturer.EXPECTED_HORIZON_BARS == 12,
        "MATURER_HORIZON_MISMATCH",
    )
    require(
        contract.HORIZON_BARS == 12
        and contract.HORIZON_MINUTES == 60,
        "CONTRACT_HORIZON_MISMATCH",
    )
    require(
        maturer.HORIZON_SEMANTICS
        == "NEXT_12_COMPLETED_M5_ROWS_AFTER_DECISION_BAR",
        "ROW_SEMANTICS_MISMATCH",
    )

    state = controller.inspect_state(repo_root=repo_root)

    require(
        state.pending_count == 1,
        "EXPECTED_EXACTLY_ONE_PENDING",
    )
    require(
        state.pending_logical_observation_id
        == EXPECTED_PENDING_ID,
        "PENDING_ID_MISMATCH",
    )
    require(
        state.next_action
        == controller.ACTION_CHECK_PENDING_MATURITY,
        "NEXT_ACTION_MISMATCH",
    )

    observations = controller.read_observations(
        repo_root=repo_root
    )
    anchors = controller.read_anchors(
        repo_root=repo_root
    )
    outcomes = controller.read_outcomes(
        repo_root=repo_root
    )

    require(
        EXPECTED_PENDING_ID in observations,
        "OBSERVATION_MISSING",
    )
    require(
        EXPECTED_PENDING_ID in anchors,
        "ANCHOR_MISSING",
    )
    require(
        EXPECTED_PENDING_ID not in outcomes,
        "OUTCOME_ALREADY_MATURED",
    )

    observation = observations[EXPECTED_PENDING_ID]
    anchor = anchors[EXPECTED_PENDING_ID]

    require(
        observation.logical_observation_id
        == anchor.logical_observation_id,
        "OBSERVATION_ANCHOR_ID_MISMATCH",
    )
    require(
        observation.semantic_record_fingerprint
        == anchor.semantic_observation_fingerprint,
        "OBSERVATION_ANCHOR_FINGERPRINT_MISMATCH",
    )
    require(
        observation.source_snapshot_id
        == anchor.source_snapshot_id,
        "OBSERVATION_ANCHOR_SOURCE_MISMATCH",
    )
    require(
        str(observation.decision_time_utc).replace(
            "Z", "+00:00"
        ) == EXPECTED_DECISION,
        "OBSERVATION_TIME_MISMATCH",
    )
    require(
        state.orphan_anchor_count == 0,
        "ORPHAN_ANCHOR_BLOCK",
    )

    require(
        sha256_file(evidence_path) == before_hash,
        "EVIDENCE_CHANGED_DURING_AUDIT",
    )

    after = controller.inspect_state(repo_root=repo_root)

    require(
        state.to_dict() == after.to_dict(),
        "STATE_CHANGED_DURING_AUDIT",
    )

    return {
        "version": VERSION,
        "status": "PASS_FAIL_CLOSED_GAP_RECORDED",
        "gap_disposition": (
            "REQUIRES_VERSIONED_SCIENTIFIC_AUTHORITY"
        ),
        "pending_id": EXPECTED_PENDING_ID,
        "evidence_file_sha256": before_hash,
        "missing_m5_timestamps_utc": source[
            "missing_m5_timestamps_utc"
        ],
        "matured_outcome_count": state.matured_outcome_count,
        "unresolved_pending_count": state.pending_count,
        "next_action": state.next_action,
        "terminal_disposition_authorized": False,
        "new_capture_authorized": False,
        "live_authorized": False,
        "execution_authorized": False,
        "ledger_writes": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--evidence",
        type=Path,
        default=Path(
            "D:/PulseViper_R03_Recovery_Backup/"
            "r03_session_gap_evidence.jsonl"
        ),
    )

    args = parser.parse_args()

    try:
        result = audit(evidence_path=args.evidence)

    except Exception as exc:
        print("R03_RECOVERY_RELEASE_STATUS=BLOCKED")
        print("ERROR_TYPE=" + type(exc).__name__)
        print("ERROR=" + str(exc))
        print("LEDGER_WRITES=false")
        print("LIVE_AUTHORIZED=false")
        print("EXECUTION_AUTHORIZED=false")
        return 2

    print("R03_RECOVERY_RELEASE_STATUS=PASS_FAIL_CLOSED")

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