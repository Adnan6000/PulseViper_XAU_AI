
from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

VERSION = "R03_V2_TERMINAL_RESOLUTION_V1"

LANE: Any = importlib.import_module(
    "04_Testing.production_portability.r03_v2_collection_lane"
)

GAP: Any = importlib.import_module(
    "04_Testing.production_portability.r03_v2_session_gap_terminal"
)

POLICY_PATH = (
    LANE.LANE_ROOT / "terminal_resolution_policy.json"
)

# No approved terminal-resolution authority exists yet.
# Never insert a locally invented hash to unlock collection.
APPROVED_TERMINAL_POLICY_SHA256: str | None = None

POLICY_SCOPE = "V2_STRICT_M5_GAP_TERMINAL_RESOLUTION"


class TerminalResolutionError(RuntimeError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise TerminalResolutionError(reason)


def file_sha256(path: Path) -> str:
    require(path.is_file(), f"MISSING_FILE:{path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_sha256(value: Any, name: str) -> str:
    require(
        isinstance(value, str)
        and len(value) == 64
        and all(c in "0123456789abcdef" for c in value),
        f"INVALID_SHA256:{name}",
    )
    return value


def verify_policy(
    *,
    policy_path: Path = POLICY_PATH,
    pinned_sha256: str | None = (
        APPROVED_TERMINAL_POLICY_SHA256
    ),
) -> bool:
    """
    Fail-closed authorization check.

    A hash verifies integrity, not reviewer identity.
    Real independent review must happen outside this code.
    """

    if pinned_sha256 is None:
        return False

    validate_sha256(pinned_sha256, "POLICY_PIN")

    require(
        file_sha256(policy_path) == pinned_sha256,
        "TERMINAL_POLICY_SHA256_MISMATCH",
    )

    def reject_duplicates(
        pairs: list[tuple[str, Any]],
    ) -> dict[str, Any]:
        output: dict[str, Any] = {}

        for key, value in pairs:
            require(
                key not in output,
                f"DUPLICATE_POLICY_FIELD:{key}",
            )
            output[key] = value

        return output

    try:
        document = json.loads(
            policy_path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicates,
        )
    except (ValueError, UnicodeError) as exc:
        raise TerminalResolutionError(
            "TERMINAL_POLICY_JSON_INVALID"
        ) from exc

    require(
        isinstance(document, dict),
        "TERMINAL_POLICY_NOT_OBJECT",
    )

    expected_keys = {
        "version",
        "scope",
        "cohort_policy",
        "decision",
        "reviewer",
        "independent_review_attested",
        "allow_gap_slot_release",
        "count_exclusions_as_matured",
        "allow_v1_ledger_mutation",
        "live_authorized",
        "execution_authorized",
    }

    require(
        set(document) == expected_keys,
        "TERMINAL_POLICY_SCHEMA_MISMATCH",
    )

    require(
        document["version"] == VERSION,
        "TERMINAL_POLICY_VERSION_MISMATCH",
    )

    require(
        document["scope"] == POLICY_SCOPE,
        "TERMINAL_POLICY_SCOPE_MISMATCH",
    )

    require(
        document["cohort_policy"] == LANE.COHORT_POLICY,
        "TERMINAL_POLICY_COHORT_MISMATCH",
    )

    require(
        document["decision"] == "APPROVED",
        "TERMINAL_POLICY_NOT_APPROVED",
    )

    require(
        document["independent_review_attested"] is True,
        "INDEPENDENT_TERMINAL_REVIEW_MISSING",
    )

    require(
        isinstance(document["reviewer"], str)
        and bool(document["reviewer"].strip())
        and document["reviewer"] != "PENDING",
        "TERMINAL_REVIEWER_INVALID",
    )

    require(
        document["allow_gap_slot_release"] is True,
        "TERMINAL_SLOT_RELEASE_NOT_ALLOWED",
    )

    for field in (
        "count_exclusions_as_matured",
        "allow_v1_ledger_mutation",
        "live_authorized",
        "execution_authorized",
    ):
        require(
            document[field] is False,
            f"FORBIDDEN_POLICY_AUTHORITY:{field}",
        )

    return True


def validate_terminal_linkage(
    *,
    terminal: Mapping[str, Any],
    observation: Any,
    anchor: Any,
    outcome_exists: bool,
) -> str:
    """
    Validate one V2 terminal record against its original
    observation and anchor.

    Do not convert evidence into an outcome.
    """

    GAP.validate_document(terminal)

    logical_id = terminal["logical_observation_id"]

    require(
        logical_id == observation.logical_observation_id,
        "TERMINAL_OBSERVATION_ID_MISMATCH",
    )

    require(
        logical_id == anchor.logical_observation_id,
        "TERMINAL_ANCHOR_ID_MISMATCH",
    )

    require(
        observation.semantic_record_fingerprint
        == anchor.semantic_observation_fingerprint,
        "OBSERVATION_ANCHOR_FINGERPRINT_MISMATCH",
    )

    require(
        terminal["observation_fingerprint"]
        == observation.semantic_record_fingerprint,
        "TERMINAL_OBSERVATION_FINGERPRINT_MISMATCH",
    )

    require(
        terminal["anchor_fingerprint"]
        == anchor.anchor_semantic_fingerprint,
        "TERMINAL_ANCHOR_FINGERPRINT_MISMATCH",
    )

    require(
        not outcome_exists,
        "TERMINAL_OUTCOME_CONFLICT",
    )

    require(
        terminal["counts_as_matured_outcome"] is False,
        "TERMINAL_COUNTS_AS_OUTCOME",
    )

    require(
        terminal["capture_slot_release_authorized"] is False,
        "DIAGNOSTIC_RECORD_MUST_NOT_GRANT_AUTHORITY",
    )

    require(
        terminal["terminal_resolution_authorized"] is False,
        "DIAGNOSTIC_RECORD_MUST_NOT_APPROVE_RESOLUTION",
    )

    return logical_id


@dataclass(frozen=True)
class Resolution:
    evidence_count: int
    authorized_resolution_count: int
    unresolved_pending_count: int
    authorized_resolved_ids: frozenset[str]
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": VERSION,
            "terminal_evidence_count": self.evidence_count,
            "authorized_terminal_resolutions": (
                self.authorized_resolution_count
            ),
            "effective_unresolved_pending_count": (
                self.unresolved_pending_count
            ),
            "authorized_resolved_ids": sorted(
                self.authorized_resolved_ids
            ),
            "next_action": self.next_action,
            "matured_outcome_increment": 0,
            "live_authorized": False,
            "execution_authorized": False,
        }


def derive_resolution(
    *,
    observations: Mapping[str, Any],
    anchors: Mapping[str, Any],
    outcomes: Mapping[str, Any],
    terminals: Mapping[str, Mapping[str, Any]],
    protocol_approved: bool,
    terminal_policy_approved: bool,
) -> Resolution:
    """
    Deterministic controller reconciliation.

    Both approvals must be true before a terminal
    observation can release the pending slot.

    Production callers must obtain those approvals
    from independently validated authority checks.
    """

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
        terminal_ids <= anchor_ids,
        "TERMINAL_WITHOUT_ANCHOR",
    )

    require(
        not (terminal_ids & outcome_ids),
        "TERMINAL_OUTCOME_CONFLICT",
    )

    for logical_id in sorted(terminal_ids):
        validate_terminal_linkage(
            terminal=terminals[logical_id],
            observation=observations[logical_id],
            anchor=anchors[logical_id],
            outcome_exists=logical_id in outcome_ids,
        )

    authorized = (
        frozenset(terminal_ids)
        if protocol_approved and terminal_policy_approved
        else frozenset()
    )

    unresolved = (
        observation_ids
        - outcome_ids
        - authorized
    )

    require(
        len(unresolved) <= 1,
        "MULTIPLE_EFFECTIVE_PENDING_OBSERVATIONS",
    )

    orphan_ids = anchor_ids - observation_ids

    if orphan_ids:
        action = "BLOCKED_ORPHAN_ANCHOR"

    elif not protocol_approved:
        action = "BLOCKED_PROTOCOL_AUTHORITY"

    elif unresolved:
        action = "MATURE_PENDING"

    elif terminal_ids and not terminal_policy_approved:
        action = "BLOCKED_TERMINAL_POLICY_AUTHORITY"

    else:
        action = "CAPTURE_CANDIDATE"

    return Resolution(
        evidence_count=len(terminal_ids),
        authorized_resolution_count=len(authorized),
        unresolved_pending_count=len(unresolved),
        authorized_resolved_ids=authorized,
        next_action=action,
    )


def inspect_resolution() -> Resolution:
    """
    Read-only integrated authority inspection.

    Does not mutate any ledger or authorize execution.
    """

    controller, runtime, maturer = LANE.modules()

    observations, anchors, outcomes = (
        LANE.read_v2_records(
            controller,
            runtime,
            maturer,
        )
    )

    terminals = GAP.read_terminal_records()

    return derive_resolution(
        observations=observations,
        anchors=anchors,
        outcomes=outcomes,
        terminals=terminals,
        protocol_approved=LANE.authority_valid(),
        terminal_policy_approved=verify_policy(),
    )


if __name__ == "__main__":
    try:
        result = inspect_resolution()

        print(
            "R03_V2_TERMINAL_RESOLUTION="
            + result.next_action
        )

        print(
            json.dumps(
                result.to_dict(),
                indent=2,
                sort_keys=True,
            )
        )

    except Exception as exc:
        print("R03_V2_TERMINAL_RESOLUTION=BLOCKED")
        print(f"ERROR_TYPE={type(exc).__name__}")
        print(f"ERROR={exc}")
        raise SystemExit(2) from exc
