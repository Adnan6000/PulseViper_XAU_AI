
from __future__ import annotations

import argparse
import importlib
import json
import msvcrt
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, cast

import pandas as pd


VERSION = "R03_COLLECTION_LANE_V2_3"

ROOT = Path(__file__).resolve().parents[2]

LANE_ROOT = Path(
    "D:/PulseViper_R03_Recovery_Backup/r03_v2_collection"
)

AUTHORITY_PATH = LANE_ROOT / "approved_protocol.json"
APPROVED_PROTOCOL_SHA256: str | None = None

OBS_PATH = LANE_ROOT / "observations.jsonl"
ANCH_PATH = LANE_ROOT / "anchors.jsonl"
OUT_PATH = LANE_ROOT / "outcomes.jsonl"
LOCK_PATH = LANE_ROOT / "collection.lock"

EXPECTED_TERMINAL_ID = (
    "febaf847ef5cd078cfc0e8223eb2120c81969a91645998968e9a1083caa1c1f8"
)

COHORT_POLICY = "V2_INDEPENDENT_PROSPECTIVE_COHORT"
MINIMUM_MATURED_OUTCOMES = 60
MINIMUM_DISTINCT_DATES = 5

CAPTURE = "CAPTURE"
MATURE = "MATURE_PENDING"
TARGET = "TARGET_REACHED"
BLOCKED = "BLOCKED_PROTOCOL_AUTHORITY"
ORPHAN = "BLOCKED_ORPHAN_ANCHOR"
TERMINAL_BLOCKED = "BLOCKED_TERMINAL_POLICY_AUTHORITY"

LIVE_AUTHORIZED = False
EXECUTION_AUTHORIZED = False


class LaneError(RuntimeError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise LaneError(reason)


def authority_valid(
    *,
    path: Path = AUTHORITY_PATH,
    pinned_sha: str | None = APPROVED_PROTOCOL_SHA256,
) -> bool:
    module = importlib.import_module(
        "04_Testing.production_portability."
        "r03_v2_protocol_authority"
    )

    return bool(
        module.verify_review(
            protocol_path=module.PROTOCOL_PATH,
            review_path=path,
            pinned_review_sha256=pinned_sha,
        )
    )


@contextmanager
def collector_lock(
    path: Path = LOCK_PATH,
) -> Iterator[None]:
    require(path.parent.is_dir(), "LOCK_PARENT_MISSING")

    handle = path.open("a+b")
    locked = False

    try:
        handle.seek(0)

        try:
            msvcrt.locking(
                handle.fileno(),
                msvcrt.LK_NBLCK,
                1,
            )
        except OSError as exc:
            raise LaneError(
                "COLLECTOR_ALREADY_RUNNING"
            ) from exc

        locked = True
        yield

    finally:
        try:
            if locked:
                handle.seek(0)
                msvcrt.locking(
                    handle.fileno(),
                    msvcrt.LK_UNLCK,
                    1,
                )
        finally:
            handle.close()


def decision_date(record: Any) -> str:
    parsed = pd.Timestamp(record.decision_time_utc)

    if pd.isna(parsed):
        raise LaneError("INVALID_DECISION_TIME")

    stamp = cast(pd.Timestamp, parsed)

    if stamp.tzinfo is None:
        raise LaneError("NAIVE_DECISION_TIME")

    return cast(
        pd.Timestamp,
        stamp.tz_convert("UTC"),
    ).date().isoformat()


@dataclass(frozen=True)
class LaneState:
    original_observations: int
    original_matured: int
    original_pending: int

    v2_observations: int
    v2_matured: int
    v2_pending: int
    v2_orphan_anchors: int

    v2_terminal_evidence: int
    v2_authorized_terminal_resolutions: int
    v2_effective_pending: int

    distinct_matured_dates: int
    protocol_authorized: bool
    terminal_policy_authorized: bool
    collection_target_reached: bool
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)

        result.update({
            "version": VERSION,
            "cohort_policy": COHORT_POLICY,
            "minimum_matured_outcomes": (
                MINIMUM_MATURED_OUTCOMES
            ),
            "minimum_distinct_utc_dates": (
                MINIMUM_DISTINCT_DATES
            ),
            "capture_authorized": (
                self.protocol_authorized
                and self.next_action == CAPTURE
            ),
            "performance_evaluated": False,
            "pnl_evaluated": False,
            "live_authorized": False,
            "execution_authorized": False,
        })

        return result


def modules() -> tuple[Any, Any, Any]:
    return (
        importlib.import_module(
            "02_AI.Models.r03_prospective_collection_controller"
        ),
        importlib.import_module(
            "02_AI.Models.frozen_r03_prospective_runtime"
        ),
        importlib.import_module(
            "02_AI.Models.frozen_r03_prospective_outcome_maturer"
        ),
    )


def terminal_modules() -> tuple[Any, Any]:
    # Late imports prevent the lane/terminal circular-import
    # relationship from becoming an import-time dependency.
    gap = importlib.import_module(
        "04_Testing.production_portability."
        "r03_v2_session_gap_terminal"
    )

    resolution = importlib.import_module(
        "04_Testing.production_portability."
        "r03_v2_terminal_resolution"
    )

    return gap, resolution


def read_v2_records(
    controller: Any,
    runtime: Any,
    maturer: Any,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    observations = controller._read_jsonl_records(
        path=OBS_PATH,
        validator=runtime.validate_observation_document,
        fingerprint_field="semantic_record_fingerprint",
    )

    anchors = controller._read_jsonl_records(
        path=ANCH_PATH,
        validator=runtime.validate_anchor_document,
        fingerprint_field="anchor_semantic_fingerprint",
    )

    outcomes = controller._read_jsonl_records(
        path=OUT_PATH,
        validator=maturer.validate_outcome_document,
        fingerprint_field="semantic_outcome_fingerprint",
    )

    return observations, anchors, outcomes


def reconcile_v2_resolution(
    *,
    observations: Mapping[str, Any],
    anchors: Mapping[str, Any],
    outcomes: Mapping[str, Any],
    terminals: Mapping[str, Mapping[str, Any]],
    protocol_approved: bool,
    terminal_policy_approved: bool,
) -> Any:
    _, resolution_module = terminal_modules()

    resolution = resolution_module.derive_resolution(
        observations=observations,
        anchors=anchors,
        outcomes=outcomes,
        terminals=terminals,
        protocol_approved=protocol_approved,
        terminal_policy_approved=terminal_policy_approved,
    )

    raw_pending = set(observations) - set(outcomes)
    resolved = set(resolution.authorized_resolved_ids)

    require(
        resolved <= raw_pending,
        "TERMINAL_RESOLVED_ID_NOT_PENDING",
    )

    require(
        resolution.unresolved_pending_count
        == len(raw_pending - resolved),
        "TERMINAL_PENDING_RECONCILIATION_MISMATCH",
    )

    return resolution


def effective_pending_ids(
    *,
    observations: Mapping[str, Any],
    outcomes: Mapping[str, Any],
    authorized_resolved_ids: frozenset[str],
) -> set[str]:
    """
    Only unresolved samples are eligible for maturation.

    Terminal-resolved samples remain in observations,
    but they are NEVER matured and NEVER recaptured.
    """
    observation_ids = set(observations)
    outcome_ids = set(outcomes)
    resolved = set(authorized_resolved_ids)

    require(
        outcome_ids <= observation_ids,
        "OUTCOME_WITHOUT_OBSERVATION",
    )

    require(
        resolved <= observation_ids,
        "RESOLVED_ID_WITHOUT_OBSERVATION",
    )

    require(
        not (outcome_ids & resolved),
        "OUTCOME_TERMINAL_CONFLICT",
    )

    return observation_ids - outcome_ids - resolved


def derive_state(
    *,
    original_observations: Mapping[str, Any],
    original_anchors: Mapping[str, Any],
    original_outcomes: Mapping[str, Any],
    v2_observations: Mapping[str, Any],
    v2_anchors: Mapping[str, Any],
    v2_outcomes: Mapping[str, Any],
    approved: bool,
    terminal_records: Mapping[
        str, Mapping[str, Any]
    ] | None = None,
    terminal_policy_approved: bool = False,
) -> LaneState:
    old_ids = set(original_observations)
    old_anchors = set(original_anchors)
    old_outcomes = set(original_outcomes)

    new_ids = set(v2_observations)
    new_anchors = set(v2_anchors)
    new_outcomes = set(v2_outcomes)

    require(
        old_ids == old_anchors,
        "ORIGINAL_ANCHOR_SET_MISMATCH",
    )

    require(
        old_outcomes <= old_ids,
        "ORIGINAL_OUTCOME_WITHOUT_OBSERVATION",
    )

    require(
        old_ids - old_outcomes == {EXPECTED_TERMINAL_ID},
        "ORIGINAL_PENDING_ID_CHANGED",
    )

    require(
        new_ids <= new_anchors,
        "V2_OBSERVATION_WITHOUT_ANCHOR",
    )

    require(
        new_outcomes <= new_ids,
        "V2_OUTCOME_WITHOUT_OBSERVATION",
    )

    require(
        not (old_ids & new_ids),
        "V1_V2_OBSERVATION_ID_COLLISION",
    )

    require(
        not (old_outcomes & new_outcomes),
        "V1_V2_OUTCOME_ID_COLLISION",
    )

    orphan_ids = new_anchors - new_ids

    require(
        len(orphan_ids) <= 1,
        "MULTIPLE_V2_ORPHAN_ANCHORS",
    )

    terminals = (
        {} if terminal_records is None
        else terminal_records
    )

    resolution = reconcile_v2_resolution(
        observations=v2_observations,
        anchors=v2_anchors,
        outcomes=v2_outcomes,
        terminals=terminals,
        protocol_approved=approved,
        terminal_policy_approved=terminal_policy_approved,
    )

    raw_pending = new_ids - new_outcomes

    pending = effective_pending_ids(
        observations=v2_observations,
        outcomes=v2_outcomes,
        authorized_resolved_ids=(
            resolution.authorized_resolved_ids
        ),
    )

    require(
        len(pending) == resolution.unresolved_pending_count,
        "PENDING_RESOLUTION_COUNT_MISMATCH",
    )

    require(
        len(pending) <= 1,
        "MULTIPLE_EFFECTIVE_PENDING",
    )

    dates = {
        decision_date(v2_observations[logical_id])
        for logical_id in new_outcomes
    }

    target_reached = (
        len(new_outcomes) >= MINIMUM_MATURED_OUTCOMES
        and len(dates) >= MINIMUM_DISTINCT_DATES
    )

    if not approved:
        action = BLOCKED

    elif orphan_ids:
        action = ORPHAN

    elif pending:
        if set(terminals) & pending:
            action = TERMINAL_BLOCKED
        else:
            action = MATURE

    elif target_reached:
        action = TARGET

    else:
        action = CAPTURE

    return LaneState(
        original_observations=len(old_ids),
        original_matured=len(old_outcomes),
        original_pending=len(old_ids - old_outcomes),
        v2_observations=len(new_ids),
        v2_matured=len(new_outcomes),
        v2_pending=len(raw_pending),
        v2_orphan_anchors=len(orphan_ids),
        v2_terminal_evidence=len(terminals),
        v2_authorized_terminal_resolutions=(
            resolution.authorized_resolution_count
        ),
        v2_effective_pending=len(pending),
        distinct_matured_dates=len(dates),
        protocol_authorized=approved,
        terminal_policy_authorized=(
            terminal_policy_approved
        ),
        collection_target_reached=target_reached,
        next_action=action,
    )


def inspect() -> LaneState:
    controller, runtime, maturer = modules()

    old_observations = controller.read_observations(
        repo_root=ROOT
    )

    old_anchors = controller.read_anchors(
        repo_root=ROOT
    )

    old_outcomes = controller.read_outcomes(
        repo_root=ROOT
    )

    observations, anchors, outcomes = read_v2_records(
        controller,
        runtime,
        maturer,
    )

    gap_module, resolution_module = terminal_modules()

    terminals = gap_module.read_terminal_records()

    protocol_ok = authority_valid()
    terminal_policy_ok = resolution_module.verify_policy()

    return derive_state(
        original_observations=old_observations,
        original_anchors=old_anchors,
        original_outcomes=old_outcomes,
        v2_observations=observations,
        v2_anchors=anchors,
        v2_outcomes=outcomes,
        approved=protocol_ok,
        terminal_records=terminals,
        terminal_policy_approved=terminal_policy_ok,
    )


def require_write_authority(action: str) -> LaneState:
    require(
        authority_valid(),
        "INDEPENDENT_PROTOCOL_APPROVAL_MISSING",
    )

    require(
        LANE_ROOT.is_dir(),
        "V2_LANE_DIRECTORY_MISSING",
    )

    before = inspect()

    require(
        before.next_action == action,
        f"INVALID_STATE_FOR_WRITE:{before.next_action}",
    )

    require(
        before.v2_orphan_anchors == 0,
        "ORPHAN_ANCHOR_REQUIRES_REVIEW",
    )

    return before


def capture_from_snapshot(
    *,
    snapshot: Any,
    feature_result: Any,
) -> dict[str, Any]:
    with collector_lock():
        before = require_write_authority(CAPTURE)

        controller, runtime, maturer = modules()

        binder = runtime.R03ProspectiveRuntimeBinder(
            inference_adapter=(
                runtime.R03FrozenArtifactInferenceAdapter(
                    repo_root=ROOT
                )
            )
        )

        binder.verify_genuine_snapshot_authority(snapshot)

        observation = binder.create_observation(
            snapshot=snapshot,
            feature_result=feature_result,
        )

        anchor = binder.create_anchor(
            observation=observation,
            market_data=snapshot.market_data,
        )

        old = controller.read_observations(
            repo_root=ROOT
        )

        existing, existing_anchors, _ = read_v2_records(
            controller,
            runtime,
            maturer,
        )

        logical_id = observation.logical_observation_id

        require(
            logical_id not in old,
            "DUPLICATES_ORIGINAL_OBSERVATION",
        )

        require(
            logical_id not in existing,
            "DUPLICATES_V2_OBSERVATION",
        )

        require(
            logical_id not in existing_anchors,
            "DUPLICATES_V2_ANCHOR",
        )

        persistence = binder.persist_anchor_first(
            observation=observation,
            anchor=anchor,
            observation_ledger=(
                runtime.R03ProspectiveObservationLedger(
                    OBS_PATH
                )
            ),
            anchor_ledger=(
                runtime.R03ProspectiveAnchorLedger(
                    ANCH_PATH
                )
            ),
        )

        after = inspect()

        require(
            after.v2_observations
            == before.v2_observations + 1,
            "POST_CAPTURE_COUNT_MISMATCH",
        )

        require(
            after.v2_effective_pending == 1,
            "POST_CAPTURE_PENDING_NOT_ONE",
        )

        require(
            after.v2_orphan_anchors == 0,
            "POST_CAPTURE_ORPHAN_CREATED",
        )

        return {
            "version": VERSION,
            "action": "CAPTURED_RESEARCH_ONLY",
            "logical_observation_id": logical_id,
            "anchor_appended": bool(
                persistence["anchor_appended"]
            ),
            "observation_appended": bool(
                persistence["observation_appended"]
            ),
            "state": after.to_dict(),
            "live_authorized": False,
            "execution_authorized": False,
        }


def select_pending_for_maturation(
    *,
    observations: Mapping[str, Any],
    anchors: Mapping[str, Any],
    outcomes: Mapping[str, Any],
    terminals: Mapping[str, Mapping[str, Any]],
    protocol_approved: bool,
    terminal_policy_approved: bool,
) -> str:
    """
    Select only the genuinely unresolved observation.

    This is the critical V2 lifecycle fix.
    """
    resolution = reconcile_v2_resolution(
        observations=observations,
        anchors=anchors,
        outcomes=outcomes,
        terminals=terminals,
        protocol_approved=protocol_approved,
        terminal_policy_approved=terminal_policy_approved,
    )

    pending = effective_pending_ids(
        observations=observations,
        outcomes=outcomes,
        authorized_resolved_ids=(
            resolution.authorized_resolved_ids
        ),
    )

    require(
        len(pending) == 1,
        f"UNIQUE_EFFECTIVE_PENDING_REQUIRED:{len(pending)}",
    )

    logical_id = next(iter(pending))

    require(
        logical_id in anchors,
        "PENDING_ANCHOR_MISSING",
    )

    return logical_id


def mature_from_snapshot(
    *,
    snapshot: Any,
) -> dict[str, Any]:
    with collector_lock():
        before = require_write_authority(MATURE)

        controller, runtime, maturer = modules()

        observations, anchors, outcomes = read_v2_records(
            controller,
            runtime,
            maturer,
        )

        gap_module, resolution_module = terminal_modules()

        terminals = gap_module.read_terminal_records()

        logical_id = select_pending_for_maturation(
            observations=observations,
            anchors=anchors,
            outcomes=outcomes,
            terminals=terminals,
            protocol_approved=authority_valid(),
            terminal_policy_approved=(
                resolution_module.verify_policy()
            ),
        )

        binder = runtime.R03ProspectiveRuntimeBinder(
            inference_adapter=(
                runtime.R03FrozenArtifactInferenceAdapter(
                    repo_root=ROOT
                )
            )
        )

        binder.verify_genuine_snapshot_authority(snapshot)

        market = getattr(snapshot, "market_data", None)

        if not isinstance(market, Mapping):
            raise LaneError(
                "SNAPSHOT_MARKET_DATA_INVALID"
            )

        m5 = market.get("M5")

        if not isinstance(m5, pd.DataFrame):
            raise LaneError("SNAPSHOT_M5_INVALID")

        try:
            outcome = maturer.mature_observation(
                observation=observations[logical_id],
                anchor=anchors[logical_id],
                completed_m5_bars=m5,
            )
        except maturer.InsufficientFutureBarsError as exc:
            return {
                "version": VERSION,
                "action": "WAIT",
                "reason": str(exc),
                "state": before.to_dict(),
                "live_authorized": False,
                "execution_authorized": False,
            }

        ledger = maturer.R03ProspectiveOutcomeLedger(
            OUT_PATH
        )

        result = ledger.append(outcome)

        require(
            ledger.validate_integrity() is True,
            "OUTCOME_LEDGER_INTEGRITY_FAILED",
        )

        after = inspect()

        require(
            after.v2_matured == before.v2_matured + 1,
            "POST_MATURATION_COUNT_MISMATCH",
        )

        require(
            after.v2_effective_pending == 0,
            "POST_MATURATION_PENDING_NOT_ZERO",
        )

        return {
            "version": VERSION,
            "action": "MATURED_RESEARCH_ONLY",
            "logical_observation_id": logical_id,
            "outcome_appended": bool(result.appended),
            "state": after.to_dict(),
            "live_authorized": False,
            "execution_authorized": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true")
    parser.parse_args()

    try:
        result = inspect().to_dict()
    except Exception as exc:
        print("R03_V2_LANE_STATUS=BLOCKED")
        print(f"ERROR_TYPE={type(exc).__name__}")
        print(f"ERROR={exc}")
        print("CAPTURE_AUTHORIZED=false")
        print("LIVE_AUTHORIZED=false")
        print("EXECUTION_AUTHORIZED=false")
        return 2

    print("R03_V2_LANE_STATUS=INSPECTED")
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
