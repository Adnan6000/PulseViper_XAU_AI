
from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest


r = importlib.import_module(
    "04_Testing.production_portability."
    "r03_v2_terminal_resolution"
)


@dataclass(frozen=True)
class Observation:
    logical_observation_id: str = "new-id"
    semantic_record_fingerprint: str = "a" * 64


@dataclass(frozen=True)
class Anchor:
    logical_observation_id: str = "new-id"
    semantic_observation_fingerprint: str = "a" * 64
    anchor_semantic_fingerprint: str = "b" * 64


def terminal() -> dict[str, Any]:
    first = "2026-10-05T20:35:00+00:00"
    last = "2026-10-05T21:30:00+00:00"

    missing = [
        f"2026-10-05T21:{minute:02d}:00+00:00"
        for minute in range(0, 35, 5)
    ]

    core = {
        "schema_version": r.GAP.VERSION,
        "logical_observation_id": "new-id",
        "disposition": "UNSCORABLE_STRICT_M5_SESSION_GAP",
        "observation_fingerprint": "a" * 64,
        "anchor_fingerprint": "b" * 64,
        "evidence_snapshot_id": "c" * 64,
        "missing_m5_timestamps_utc": missing,
        "expected_first_utc": first,
        "expected_last_utc": last,
        "counts_as_matured_outcome": False,
        "terminal_resolution_authorized": False,
        "capture_slot_release_authorized": False,
        "live_authorized": False,
        "execution_authorized": False,
    }

    return {
        **core,
        "semantic_fingerprint_sha256": (
            r.GAP.fingerprint(core)
        ),
    }


def derive(
    *,
    protocol: bool = False,
    policy: bool = False,
    with_terminal: bool = True,
    with_outcome: bool = False,
) -> Any:
    observations = {"new-id": Observation()}
    anchors = {"new-id": Anchor()}

    outcomes = (
        {"new-id": object()}
        if with_outcome
        else {}
    )

    terminals = (
        {"new-id": terminal()}
        if with_terminal
        else {}
    )

    return r.derive_resolution(
        observations=observations,
        anchors=anchors,
        outcomes=outcomes,
        terminals=terminals,
        protocol_approved=protocol,
        terminal_policy_approved=policy,
    )


def test_diagnostic_evidence_does_not_release_slot():
    state = derive()

    assert state.unresolved_pending_count == 1
    assert state.authorized_resolution_count == 0


def test_protocol_alone_does_not_release_slot():
    state = derive(protocol=True)

    assert state.unresolved_pending_count == 1
    assert state.authorized_resolution_count == 0


def test_terminal_policy_alone_does_not_release_slot():
    state = derive(policy=True)

    assert state.unresolved_pending_count == 1


def test_both_authorities_resolve_terminal():
    state = derive(protocol=True, policy=True)

    assert state.unresolved_pending_count == 0
    assert state.authorized_resolution_count == 1
    assert state.next_action == "CAPTURE_CANDIDATE"


def test_resolution_never_increases_matured_count():
    state = derive(protocol=True, policy=True)

    assert state.to_dict()["matured_outcome_increment"] == 0


def test_outcome_terminal_conflict_rejected():
    with pytest.raises(
        r.TerminalResolutionError,
        match="TERMINAL_OUTCOME_CONFLICT",
    ):
        derive(
            protocol=True,
            policy=True,
            with_outcome=True,
        )


def test_no_terminal_remains_pending():
    state = derive(
        protocol=True,
        policy=True,
        with_terminal=False,
    )

    assert state.unresolved_pending_count == 1


def test_unpinned_policy_rejected(tmp_path: Path):
    assert r.verify_policy(
        policy_path=tmp_path / "missing.json",
        pinned_sha256=None,
    ) is False


def test_missing_pinned_policy_rejected(tmp_path: Path):
    with pytest.raises(
        r.TerminalResolutionError,
        match="MISSING_FILE",
    ):
        r.verify_policy(
            policy_path=tmp_path / "missing.json",
            pinned_sha256="a" * 64,
        )


def test_terminal_fingerprint_tampering_rejected():
    document = terminal()
    document["observation_fingerprint"] = "d" * 64

    with pytest.raises(Exception):
        r.derive_resolution(
            observations={"new-id": Observation()},
            anchors={"new-id": Anchor()},
            outcomes={},
            terminals={"new-id": document},
            protocol_approved=True,
            terminal_policy_approved=True,
        )


def test_unknown_terminal_id_rejected():
    with pytest.raises(
        r.TerminalResolutionError,
        match="TERMINAL_WITHOUT_OBSERVATION",
    ):
        r.derive_resolution(
            observations={"new-id": Observation()},
            anchors={"new-id": Anchor()},
            outcomes={},
            terminals={"unknown": terminal()},
            protocol_approved=True,
            terminal_policy_approved=True,
        )
