
from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

import pytest


lane = importlib.import_module(
    "04_Testing.production_portability.r03_v2_collection_lane"
)

gap = importlib.import_module(
    "04_Testing.production_portability.r03_v2_session_gap_terminal"
)


@dataclass(frozen=True)
class Observation:
    logical_observation_id: str
    decision_time_utc: str = "2026-10-10T12:00:00Z"
    semantic_record_fingerprint: str = "a" * 64


@dataclass(frozen=True)
class Anchor:
    logical_observation_id: str
    semantic_observation_fingerprint: str = "a" * 64
    anchor_semantic_fingerprint: str = "b" * 64


def original() -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    observations = {
        f"old-{number}": Observation(f"old-{number}")
        for number in range(13)
    }

    observations[lane.EXPECTED_TERMINAL_ID] = (
        Observation(lane.EXPECTED_TERMINAL_ID)
    )

    outcomes = {
        key: value
        for key, value in observations.items()
        if key != lane.EXPECTED_TERMINAL_ID
    }

    return observations, dict(observations), outcomes


def terminal(logical_id: str) -> dict[str, Any]:
    core = {
        "schema_version": gap.VERSION,
        "logical_observation_id": logical_id,
        "disposition": "UNSCORABLE_STRICT_M5_SESSION_GAP",
        "observation_fingerprint": "a" * 64,
        "anchor_fingerprint": "b" * 64,
        "evidence_snapshot_id": "c" * 64,
        "missing_m5_timestamps_utc": [
            f"2026-10-10T12:{minute:02d}:00+00:00"
            for minute in range(30, 60, 5)
        ],
        "expected_first_utc": "2026-10-10T12:00:00+00:00",
        "expected_last_utc": "2026-10-10T12:55:00+00:00",
        "counts_as_matured_outcome": False,
        "terminal_resolution_authorized": False,
        "capture_slot_release_authorized": False,
        "live_authorized": False,
        "execution_authorized": False,
    }

    return {
        **core,
        "semantic_fingerprint_sha256": gap.fingerprint(core),
    }


def derive(
    *,
    approved: bool = True,
    policy: bool = False,
    with_terminal: bool = True,
) -> Any:
    old_obs, old_anchors, old_outcomes = original()

    new_obs = {"new-1": Observation("new-1")}
    new_anchors = {"new-1": Anchor("new-1")}

    terminals = (
        {"new-1": terminal("new-1")}
        if with_terminal else {}
    )

    return lane.derive_state(
        original_observations=old_obs,
        original_anchors=old_anchors,
        original_outcomes=old_outcomes,
        v2_observations=new_obs,
        v2_anchors=new_anchors,
        v2_outcomes={},
        approved=approved,
        terminal_records=terminals,
        terminal_policy_approved=policy,
    )


def test_diagnostic_record_does_not_release():
    result = derive(policy=False)

    assert result.v2_terminal_evidence == 1
    assert result.v2_authorized_terminal_resolutions == 0
    assert result.v2_effective_pending == 1
    assert result.next_action == lane.TERMINAL_BLOCKED


def test_both_authorities_release_terminal():
    result = derive(policy=True)

    assert result.v2_terminal_evidence == 1
    assert result.v2_authorized_terminal_resolutions == 1
    assert result.v2_effective_pending == 0
    assert result.next_action == lane.CAPTURE
    assert result.v2_matured == 0


def test_protocol_only_cannot_release():
    result = derive(approved=True, policy=False)

    assert result.v2_effective_pending == 1


def test_terminal_policy_only_cannot_release():
    result = derive(approved=False, policy=True)

    assert result.v2_effective_pending == 1
    assert result.next_action == lane.BLOCKED


def test_no_terminal_stays_pending():
    result = derive(with_terminal=False, policy=True)

    assert result.next_action == lane.MATURE
    assert result.v2_effective_pending == 1


def test_terminal_never_counts_as_outcome():
    result = derive(policy=True)

    assert result.v2_observations == 1
    assert result.v2_matured == 0
    assert result.collection_target_reached is False


def test_bad_terminal_fingerprint_blocks():
    old_obs, old_anchors, old_outcomes = original()
    record = terminal("new-1")
    record["observation_fingerprint"] = "d" * 64

    with pytest.raises(Exception):
        lane.derive_state(
            original_observations=old_obs,
            original_anchors=old_anchors,
            original_outcomes=old_outcomes,
            v2_observations={
                "new-1": Observation("new-1")
            },
            v2_anchors={
                "new-1": Anchor("new-1")
            },
            v2_outcomes={},
            approved=True,
            terminal_records={"new-1": record},
            terminal_policy_approved=True,
        )
