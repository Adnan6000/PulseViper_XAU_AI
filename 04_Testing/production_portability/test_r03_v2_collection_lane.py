
from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path

import pytest


lane = importlib.import_module(
    "04_Testing.production_portability."
    "r03_v2_collection_lane"
)

resolution = importlib.import_module(
    "04_Testing.production_portability."
    "r03_v2_terminal_resolution"
)

protocol = importlib.import_module(
    "04_Testing.production_portability."
    "r03_v2_protocol_authority"
)


@dataclass(frozen=True)
class Record:
    decision_time_utc: str = "2026-10-05T20:35:00Z"


def records():
    observations = {
        f"old-{i}": Record()
        for i in range(13)
    }

    observations[lane.EXPECTED_TERMINAL_ID] = Record()

    outcomes = {
        key: value
        for key, value in observations.items()
        if key != lane.EXPECTED_TERMINAL_ID
    }

    return observations, dict(observations), outcomes


def derive(
    *,
    approved=False,
    v2_observations=None,
    v2_anchors=None,
    v2_outcomes=None,
):
    old_obs, old_anchors, old_outcomes = records()

    new_obs = (
        {} if v2_observations is None
        else v2_observations
    )

    new_anchors = (
        dict(new_obs)
        if v2_anchors is None
        else v2_anchors
    )

    new_out = (
        {} if v2_outcomes is None
        else v2_outcomes
    )

    return lane.derive_state(
        original_observations=old_obs,
        original_anchors=old_anchors,
        original_outcomes=old_outcomes,
        v2_observations=new_obs,
        v2_anchors=new_anchors,
        v2_outcomes=new_out,
        approved=approved,
    )


def test_unapproved_state_is_blocked():
    state = derive()

    assert state.next_action == lane.BLOCKED
    assert state.original_matured == 13
    assert state.original_pending == 1
    assert state.v2_matured == 0
    assert state.to_dict()["capture_authorized"] is False


def test_approved_empty_lane_candidate_capture():
    state = derive(approved=True)

    assert state.next_action == lane.CAPTURE
    assert state.to_dict()["live_authorized"] is False
    assert state.to_dict()["execution_authorized"] is False


def test_pending_requires_maturation():
    state = derive(
        approved=True,
        v2_observations={"new": Record()},
    )

    assert state.next_action == lane.MATURE
    assert state.v2_pending == 1
    assert state.v2_effective_pending == 1


def test_genuine_v2_outcome_count_only():
    new = {"new": Record()}

    state = derive(
        approved=True,
        v2_observations=new,
        v2_outcomes=new,
    )

    assert state.original_matured == 13
    assert state.v2_matured == 1
    assert state.distinct_matured_dates == 1
    assert state.collection_target_reached is False


def test_original_outcomes_not_pooled_into_v2_target():
    new = {"new": Record()}

    state = derive(
        approved=True,
        v2_observations=new,
        v2_outcomes=new,
    )

    assert state.v2_matured == 1
    assert state.next_action == lane.CAPTURE
    assert state.to_dict()["cohort_policy"] == (
        "V2_INDEPENDENT_PROSPECTIVE_COHORT"
    )


def test_orphan_anchor_blocks_capture():
    state = derive(
        approved=True,
        v2_observations={},
        v2_anchors={"orphan": Record()},
    )

    assert state.v2_orphan_anchors == 1
    assert state.next_action == lane.ORPHAN


def test_orphan_anchor_cannot_be_silently_discarded():
    state = derive(
        approved=True,
        v2_observations={"new": Record()},
        v2_anchors={
            "new": Record(),
            "orphan": Record(),
        },
    )

    assert state.next_action == lane.ORPHAN


def test_observation_without_anchor_rejected():
    with pytest.raises(
        lane.LaneError,
        match="V2_OBSERVATION_WITHOUT_ANCHOR",
    ):
        derive(
            approved=True,
            v2_observations={"new": Record()},
            v2_anchors={},
        )


def test_duplicate_original_id_rejected():
    with pytest.raises(
        lane.LaneError,
        match="V1_V2_OBSERVATION_ID_COLLISION",
    ):
        derive(
            approved=True,
            v2_observations={
                lane.EXPECTED_TERMINAL_ID: Record()
            },
        )


def test_outcome_without_observation_rejected():
    with pytest.raises(
        lane.LaneError,
        match="V2_OUTCOME_WITHOUT_OBSERVATION",
    ):
        derive(
            approved=True,
            v2_outcomes={"unknown": Record()},
        )


def test_multiple_pending_rejected():
    # V2.3 delegates this invariant to the terminal
    # reconciliation engine; do not weaken it.
    with pytest.raises(
        resolution.TerminalResolutionError,
        match="MULTIPLE_EFFECTIVE_PENDING_OBSERVATIONS",
    ):
        derive(
            approved=True,
            v2_observations={
                "new-1": Record(),
                "new-2": Record(),
            },
        )


def test_unpinned_protocol_rejected(tmp_path: Path):
    assert (
        lane.authority_valid(
            path=tmp_path / "missing.json",
            pinned_sha=None,
        )
        is False
    )


def test_missing_pinned_protocol_rejected(tmp_path: Path):
    with pytest.raises(
        protocol.ProtocolAuthorityError,
        match="FILE_MISSING",
    ):
        lane.authority_valid(
            path=tmp_path / "missing.json",
            pinned_sha="a" * 64,
        )


def test_invalid_authority_pin_rejected(tmp_path: Path):
    with pytest.raises(
        protocol.ProtocolAuthorityError,
        match="REVIEW_PIN_INVALID",
    ):
        lane.authority_valid(
            path=tmp_path / "missing.json",
            pinned_sha="bad",
        )


def test_process_lock_is_exclusive(tmp_path: Path):
    lock = tmp_path / "collector.lock"

    with lane.collector_lock(lock):
        with pytest.raises(
            lane.LaneError,
            match="COLLECTOR_ALREADY_RUNNING",
        ):
            with lane.collector_lock(lock):
                pass


def test_lock_released_after_exception(tmp_path: Path):
    lock = tmp_path / "collector.lock"

    with pytest.raises(
        ValueError,
        match="simulated crash",
    ):
        with lane.collector_lock(lock):
            raise ValueError("simulated crash")

    with lane.collector_lock(lock):
        assert lock.exists()


def test_lock_released_after_success(tmp_path: Path):
    lock = tmp_path / "collector.lock"

    with lane.collector_lock(lock):
        assert lock.exists()

    with lane.collector_lock(lock):
        assert lock.exists()


def test_target_requires_60_v2_outcomes():
    new = {
        f"new-{i}": Record(
            decision_time_utc=(
                f"2026-10-{10 + i % 5:02d}T12:00:00Z"
            )
        )
        for i in range(60)
    }

    state = derive(
        approved=True,
        v2_observations=new,
        v2_outcomes=new,
    )

    assert state.v2_matured == 60
    assert state.distinct_matured_dates == 5
    assert state.collection_target_reached is True
    assert state.next_action == lane.TARGET


def test_60_same_day_cannot_reach_target():
    new = {
        f"new-{i}": Record()
        for i in range(60)
    }

    state = derive(
        approved=True,
        v2_observations=new,
        v2_outcomes=new,
    )

    assert state.v2_matured == 60
    assert state.distinct_matured_dates == 1
    assert state.collection_target_reached is False
    assert state.next_action == lane.CAPTURE


def test_all_execution_authorities_false():
    state = derive(approved=True)

    data = state.to_dict()

    assert data["live_authorized"] is False
    assert data["execution_authorized"] is False
    assert data["performance_evaluated"] is False
    assert data["pnl_evaluated"] is False
