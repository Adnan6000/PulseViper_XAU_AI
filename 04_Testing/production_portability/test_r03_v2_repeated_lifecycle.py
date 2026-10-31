
from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

import pytest


lane = importlib.import_module(
    "04_Testing.production_portability."
    "r03_v2_collection_lane"
)

gap = importlib.import_module(
    "04_Testing.production_portability."
    "r03_v2_session_gap_terminal"
)

resolution = importlib.import_module(
    "04_Testing.production_portability."
    "r03_v2_terminal_resolution"
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
        "expected_first_utc": (
            "2026-10-10T12:00:00+00:00"
        ),
        "expected_last_utc": (
            "2026-10-10T12:55:00+00:00"
        ),
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


def records() -> tuple[
    dict[str, Observation],
    dict[str, Anchor],
    dict[str, Any],
    dict[str, dict[str, Any]],
]:
    observations = {
        "gap-old": Observation("gap-old"),
        "new-pending": Observation("new-pending"),
    }

    anchors = {
        key: Anchor(key)
        for key in observations
    }

    return (
        observations,
        anchors,
        {},
        {"gap-old": terminal("gap-old")},
    )


def original() -> tuple[
    dict[str, Observation],
    dict[str, Observation],
    dict[str, Observation],
]:
    observations = {
        f"old-{index}": Observation(f"old-{index}")
        for index in range(13)
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


def derive(
    *,
    approved: bool = True,
    terminal_policy: bool = True,
    observations: dict[str, Observation] | None = None,
    anchors: dict[str, Anchor] | None = None,
    outcomes: dict[str, Any] | None = None,
    terminals: dict[str, dict[str, Any]] | None = None,
) -> Any:
    old_obs, old_anchors, old_outcomes = original()

    if observations is None:
        observations = {}

    if anchors is None:
        anchors = {
            key: Anchor(key)
            for key in observations
        }

    if outcomes is None:
        outcomes = {}

    if terminals is None:
        terminals = {}

    return lane.derive_state(
        original_observations=old_obs,
        original_anchors=old_anchors,
        original_outcomes=old_outcomes,
        v2_observations=observations,
        v2_anchors=anchors,
        v2_outcomes=outcomes,
        approved=approved,
        terminal_records=terminals,
        terminal_policy_approved=terminal_policy,
    )


def test_resolved_then_new_pending() -> None:
    observations, anchors, outcomes, terminals = records()

    state = derive(
        observations=observations,
        anchors=anchors,
        outcomes=outcomes,
        terminals=terminals,
    )

    assert state.v2_observations == 2
    assert state.v2_matured == 0
    assert state.v2_pending == 2
    assert state.v2_effective_pending == 1
    assert state.next_action == lane.MATURE


def test_maturer_selects_new_not_resolved() -> None:
    observations, anchors, outcomes, terminals = records()

    selected = lane.select_pending_for_maturation(
        observations=observations,
        anchors=anchors,
        outcomes=outcomes,
        terminals=terminals,
        protocol_approved=True,
        terminal_policy_approved=True,
    )

    assert selected == "new-pending"


def test_unapproved_terminal_does_not_disappear() -> None:
    observations, anchors, outcomes, terminals = records()

    # Without terminal-policy authority there are TWO
    # effective pending observations. This invalid state
    # must fail closed before any maturation attempt.
    with pytest.raises(
        resolution.TerminalResolutionError,
        match="MULTIPLE_EFFECTIVE_PENDING_OBSERVATIONS",
    ):
        lane.select_pending_for_maturation(
            observations=observations,
            anchors=anchors,
            outcomes=outcomes,
            terminals=terminals,
            protocol_approved=True,
            terminal_policy_approved=False,
        )


def test_resolved_then_new_matured_then_capture() -> None:
    observations, anchors, _, terminals = records()

    outcomes = {"new-pending": object()}

    state = derive(
        observations=observations,
        anchors=anchors,
        outcomes=outcomes,
        terminals=terminals,
    )

    assert state.v2_matured == 1
    assert state.v2_authorized_terminal_resolutions == 1
    assert state.v2_effective_pending == 0
    assert state.next_action == lane.CAPTURE


def test_terminal_outcome_overlap_rejected() -> None:
    observations, anchors, _, terminals = records()

    with pytest.raises(
        resolution.TerminalResolutionError,
        match="TERMINAL_OUTCOME_CONFLICT",
    ):
        derive(
            observations=observations,
            anchors=anchors,
            outcomes={"gap-old": object()},
            terminals=terminals,
        )


def test_diagnostic_only_blocks_next_capture() -> None:
    observations, anchors, outcomes, terminals = records()

    # A synthetic state with old unresolved gap plus
    # a new pending sample cannot be legitimized by
    # diagnostic evidence alone.
    with pytest.raises(
        resolution.TerminalResolutionError,
        match="MULTIPLE_EFFECTIVE_PENDING_OBSERVATIONS",
    ):
        derive(
            observations=observations,
            anchors=anchors,
            outcomes=outcomes,
            terminals=terminals,
            terminal_policy=False,
        )


def test_no_terminal_new_pending_selected() -> None:
    observations = {
        "new-pending": Observation("new-pending")
    }

    anchors = {
        "new-pending": Anchor("new-pending")
    }

    selected = lane.select_pending_for_maturation(
        observations=observations,
        anchors=anchors,
        outcomes={},
        terminals={},
        protocol_approved=True,
        terminal_policy_approved=False,
    )

    assert selected == "new-pending"


def test_terminal_does_not_count_for_target() -> None:
    observations = {
        "gap-old": Observation("gap-old")
    }

    state = derive(
        observations=observations,
        terminals={"gap-old": terminal("gap-old")},
    )

    assert state.v2_matured == 0
    assert state.distinct_matured_dates == 0
    assert state.collection_target_reached is False


def test_effective_pending_rejects_conflict() -> None:
    with pytest.raises(
        lane.LaneError,
        match="OUTCOME_TERMINAL_CONFLICT",
    ):
        lane.effective_pending_ids(
            observations={"id": object()},
            outcomes={"id": object()},
            authorized_resolved_ids=frozenset({"id"}),
        )
