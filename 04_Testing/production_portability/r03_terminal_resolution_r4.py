from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


VERSION = "R03_TERMINAL_RESOLUTION_R4_V1"

DISPOSITION = "EXCLUDED_STRICT_M5_SESSION_GAP"

PENDING_ID = (
    "febaf847ef5cd078cfc0e8223eb2120c81969a91645998968e9a1083caa1c1f8"
)

EXPECTED_DECISION_UTC = "2026-10-05T20:35:00+00:00"

EXPECTED_LAST_UTC = "2026-10-05T21:30:00+00:00"

ACTUAL_LAST_UTC = "2026-10-05T22:30:00+00:00"

EXPECTED_MISSING = tuple(
    f"2026-10-05T21:{minute:02d}:00+00:00"
    for minute in range(0, 35, 5)
)

controller: Any = importlib.import_module(
    "02_AI.Models.r03_prospective_collection_controller"
)

policy: Any = importlib.import_module(
    "04_Testing.production_portability.r03_session_gap_policy_r3"
)


class R03TerminalResolutionError(RuntimeError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise R03TerminalResolutionError(reason)


def canonical_bytes(document: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(document),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def expected_exclusion_document() -> dict[str, Any]:
    """
    Deterministic research evidence for one observed gap.

    This document does NOT independently authorize
    the published controller to resume collection.
    """
    core = {
        "schema_version": VERSION,
        "disposition": DISPOSITION,
        "logical_observation_id": PENDING_ID,
        "decision_time_utc": EXPECTED_DECISION_UTC,
        "expected_last_future_bar_utc": EXPECTED_LAST_UTC,
        "actual_last_future_bar_utc": ACTUAL_LAST_UTC,
        "missing_m5_timestamps_utc": list(EXPECTED_MISSING),
        "counts_as_matured_outcome": False,
        "performance_evaluated": False,
        "pnl_evaluated": False,
        "live_authorized": False,
        "execution_authorized": False,
    }

    fingerprint = hashlib.sha256(
        canonical_bytes(core)
    ).hexdigest()

    return {
        **core,
        "semantic_fingerprint_sha256": fingerprint,
    }


def validate_exclusion_document(
    document: Mapping[str, Any],
) -> bool:
    require(
        dict(document) == expected_exclusion_document(),
        "EXCLUSION_EVIDENCE_AUTHORITY_MISMATCH",
    )
    return True


@dataclass(frozen=True)
class R4ReconciledState:
    observation_count: int
    anchor_count: int
    matured_outcome_count: int
    excluded_count: int
    unresolved_pending_count: int
    original_pending_count: int
    original_next_action: str
    proposed_next_action: str
    collection_target_reached: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": VERSION,
            "observation_count": self.observation_count,
            "anchor_count": self.anchor_count,
            "matured_outcome_count": self.matured_outcome_count,
            "excluded_count": self.excluded_count,
            "unresolved_pending_count": self.unresolved_pending_count,
            "original_pending_count": self.original_pending_count,
            "original_next_action": self.original_next_action,
            "proposed_next_action": self.proposed_next_action,
            "collection_target_reached": (
                self.collection_target_reached
            ),
            "controller_promotion_authorized": False,
            "ledger_writes_authorized": False,
            "live_authorized": False,
            "execution_authorized": False,
        }


def reconcile(
    *,
    repo_root: Path,
    exclusion_document: Mapping[str, Any],
) -> R4ReconciledState:

    validate_exclusion_document(exclusion_document)

    before = controller.inspect_state(
        repo_root=repo_root
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
        before.pending_count == 1,
        "EXPECTED_ONE_ORIGINAL_PENDING",
    )

    require(
        before.pending_logical_observation_id == PENDING_ID,
        "PENDING_ID_AUTHORITY_MISMATCH",
    )

    require(
        PENDING_ID in observations,
        "EXCLUDED_OBSERVATION_MISSING",
    )

    require(
        PENDING_ID in anchors,
        "EXCLUDED_ANCHOR_MISSING",
    )

    require(
        PENDING_ID not in outcomes,
        "CANNOT_EXCLUDE_MATURED_OUTCOME",
    )

    observation = observations[PENDING_ID]
    anchor = anchors[PENDING_ID]

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
        "OBSERVATION_ANCHOR_SNAPSHOT_MISMATCH",
    )

    require(
        str(observation.decision_time_utc).replace(
            "Z", "+00:00"
        )
        == EXPECTED_DECISION_UTC,
        "DECISION_TIME_AUTHORITY_MISMATCH",
    )

    require(
        before.orphan_anchor_count == 0,
        "ORPHAN_ANCHOR_BLOCK",
    )

    proposed_action = (
        "CANDIDATE_CAPTURE_NEW_OBSERVATION"
        if not before.collection_target_reached
        else "COLLECTION_TARGET_REACHED"
    )

    after = controller.inspect_state(
        repo_root=repo_root
    )

    require(
        after.to_dict() == before.to_dict(),
        "CONTROLLER_STATE_CHANGED_DURING_RECONCILIATION",
    )

    return R4ReconciledState(
        observation_count=before.observation_count,
        anchor_count=before.anchor_count,
        matured_outcome_count=before.matured_outcome_count,
        excluded_count=1,
        unresolved_pending_count=0,
        original_pending_count=before.pending_count,
        original_next_action=before.next_action,
        proposed_next_action=proposed_action,
        collection_target_reached=before.collection_target_reached,
    )