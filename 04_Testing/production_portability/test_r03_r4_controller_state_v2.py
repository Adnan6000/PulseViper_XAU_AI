from __future__ import annotations

import importlib

import pytest


r4 = importlib.import_module(
    "04_Testing.production_portability."
    "r03_r4_controller_state_v2"
)


def fixture_records():
    observations = {
        f"id-{i}": "2026-10-05"
        for i in range(14)
    }

    anchors = set(observations)

    outcomes = {
        f"id-{i}"
        for i in range(13)
    }

    return observations, anchors, outcomes


def test_existing_pending_remains_pending():
    observations, anchors, outcomes = fixture_records()

    state = r4.derive_r4_state(
        observations=observations,
        anchors=anchors,
        outcomes=outcomes,
        authorized_terminal_ids=set(),
    )

    assert state.matured_count == 13
    assert state.terminal_count == 0
    assert state.pending_count == 1
    assert state.proposed_next_action == r4.ACTION_MATURE


def test_authorized_terminal_changes_only_pending_count():
    observations, anchors, outcomes = fixture_records()

    state = r4.derive_r4_state(
        observations=observations,
        anchors=anchors,
        outcomes=outcomes,
        authorized_terminal_ids={"id-13"},
    )

    assert state.observation_count == 14
    assert state.anchor_count == 14
    assert state.matured_count == 13
    assert state.terminal_count == 1
    assert state.pending_count == 0
    assert state.proposed_next_action == r4.ACTION_CAPTURE

    assert state.to_dict()["capture_authorized"] is False


def test_terminal_cannot_overlap_matured_outcome():
    observations, anchors, outcomes = fixture_records()

    with pytest.raises(
        r4.R4ControllerError,
        match="OUTCOME_TERMINAL_CONFLICT",
    ):
        r4.derive_r4_state(
            observations=observations,
            anchors=anchors,
            outcomes=outcomes,
            authorized_terminal_ids={"id-0"},
        )


def test_unknown_terminal_id_rejected():
    observations, anchors, outcomes = fixture_records()

    with pytest.raises(
        r4.R4ControllerError,
        match="TERMINAL_WITHOUT_OBSERVATION",
    ):
        r4.derive_r4_state(
            observations=observations,
            anchors=anchors,
            outcomes=outcomes,
            authorized_terminal_ids={"unknown"},
        )


def test_missing_anchor_rejected():
    observations, anchors, outcomes = fixture_records()

    anchors.remove("id-13")

    with pytest.raises(
        r4.R4ControllerError,
        match="OBSERVATION_WITHOUT_ANCHOR",
    ):
        r4.derive_r4_state(
            observations=observations,
            anchors=anchors,
            outcomes=outcomes,
            authorized_terminal_ids=set(),
        )


def test_target_cannot_be_reached_by_exclusions():
    observations, anchors, outcomes = fixture_records()

    state = r4.derive_r4_state(
        observations=observations,
        anchors=anchors,
        outcomes=outcomes,
        authorized_terminal_ids={"id-13"},
    )

    assert state.target_reached is False
    assert state.matured_count == 13


def test_multiple_pending_fail_closed():
    observations, anchors, outcomes = fixture_records()

    outcomes.remove("id-12")

    state = r4.derive_r4_state(
        observations=observations,
        anchors=anchors,
        outcomes=outcomes,
        authorized_terminal_ids=set(),
    )

    assert state.pending_count == 2
    assert state.proposed_next_action == r4.ACTION_BLOCKED


def test_no_trading_or_capture_authority():
    observations, anchors, outcomes = fixture_records()

    state = r4.derive_r4_state(
        observations=observations,
        anchors=anchors,
        outcomes=outcomes,
        authorized_terminal_ids={"id-13"},
    )

    document = state.to_dict()

    assert document["capture_authorized"] is False
    assert document["live_authorized"] is False
    assert document["execution_authorized"] is False
    assert document["terminal_disposition_authorized"] is False