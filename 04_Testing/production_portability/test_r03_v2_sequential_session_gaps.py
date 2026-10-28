
from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

import pandas as pd
import pytest


gap = importlib.import_module(
    "04_Testing.production_portability."
    "r03_v2_session_gap_terminal"
)

lane = importlib.import_module(
    "04_Testing.production_portability."
    "r03_v2_collection_lane"
)

resolution = importlib.import_module(
    "04_Testing.production_portability."
    "r03_v2_terminal_resolution"
)


@dataclass(frozen=True)
class Observation:
    logical_observation_id: str
    decision_time_utc: str = (
        "2026-10-10T12:00:00Z"
    )
    semantic_record_fingerprint: str = "a" * 64


@dataclass(frozen=True)
class Anchor:
    logical_observation_id: str
    decision_time_utc: str = (
        "2026-10-10T12:00:00Z"
    )
    semantic_observation_fingerprint: str = (
        "a" * 64
    )
    anchor_semantic_fingerprint: str = (
        "b" * 64
    )


def terminal(logical_id: str) -> dict[str, Any]:
    core = {
        "schema_version": gap.VERSION,
        "logical_observation_id": logical_id,
        "disposition": (
            "UNSCORABLE_STRICT_M5_SESSION_GAP"
        ),
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
        "semantic_fingerprint_sha256": (
            gap.fingerprint(core)
        ),
    }


def cohort(
    terminal_ids: list[str],
    pending_id: str,
) -> tuple[
    dict[str, Observation],
    dict[str, Anchor],
    dict[str, Any],
    dict[str, dict[str, Any]],
]:
    ids = terminal_ids + [pending_id]

    observations = {
        logical_id: Observation(logical_id)
        for logical_id in ids
    }

    anchors = {
        logical_id: Anchor(logical_id)
        for logical_id in ids
    }

    terminals = {
        logical_id: terminal(logical_id)
        for logical_id in terminal_ids
    }

    return observations, anchors, {}, terminals


def select(
    terminal_ids: list[str],
    pending_id: str,
    *,
    policy: bool,
) -> str:
    observations, anchors, outcomes, terminals = (
        cohort(terminal_ids, pending_id)
    )

    return gap.select_pending_for_gap(
        observations=observations,
        anchors=anchors,
        outcomes=outcomes,
        terminals=terminals,
        protocol_approved=True,
        terminal_policy_approved=policy,
    )


def test_first_gap_selects_first_pending():
    assert select([], "gap-1", policy=False) == (
        "gap-1"
    )


def test_second_gap_excludes_first_terminal():
    assert select(
        ["gap-1"],
        "gap-2",
        policy=True,
    ) == "gap-2"


def test_third_gap_excludes_two_terminals():
    assert select(
        ["gap-1", "gap-2"],
        "gap-3",
        policy=True,
    ) == "gap-3"


def test_fourth_gap_excludes_three_terminals():
    assert select(
        ["gap-1", "gap-2", "gap-3"],
        "gap-4",
        policy=True,
    ) == "gap-4"


def test_no_terminal_policy_fails_closed():
    with pytest.raises(
        resolution.TerminalResolutionError,
        match="MULTIPLE_EFFECTIVE_PENDING_OBSERVATIONS",
    ):
        select(
            ["gap-1"],
            "gap-2",
            policy=False,
        )


def test_no_protocol_authority_fails_closed():
    observations, anchors, outcomes, terminals = (
        cohort(["gap-1"], "gap-2")
    )

    with pytest.raises(
        resolution.TerminalResolutionError,
        match="MULTIPLE_EFFECTIVE_PENDING_OBSERVATIONS",
    ):
        gap.select_pending_for_gap(
            observations=observations,
            anchors=anchors,
            outcomes=outcomes,
            terminals=terminals,
            protocol_approved=False,
            terminal_policy_approved=True,
        )


def test_untracked_terminal_id_rejected():
    observations, anchors, outcomes, terminals = (
        cohort([], "gap-2")
    )

    terminals["unknown"] = terminal("unknown")

    with pytest.raises(
        resolution.TerminalResolutionError,
        match="TERMINAL_WITHOUT_OBSERVATION",
    ):
        gap.select_pending_for_gap(
            observations=observations,
            anchors=anchors,
            outcomes=outcomes,
            terminals=terminals,
            protocol_approved=True,
            terminal_policy_approved=True,
        )


def test_truncated_snapshot_not_called_gap():
    frame = pd.DataFrame({
        "time": pd.date_range(
            start="2026-10-10T13:00:00Z",
            periods=12,
            freq="5min",
        )
    })

    result = gap.assess_gap(
        decision_time_utc=(
            "2026-10-10T12:00:00Z"
        ),
        completed_m5=frame,
    )

    assert result["status"] == (
        "INSUFFICIENT_HISTORICAL_COVERAGE"
    )
    assert result[
        "missing_m5_timestamps_utc"
    ] == []


def test_real_gap_with_historical_coverage():
    times = list(
        pd.date_range(
            start="2026-10-10T11:55:00Z",
            periods=7,
            freq="5min",
        )
    )

    times.extend(
        list(
            pd.date_range(
                start="2026-10-10T13:00:00Z",
                periods=12,
                freq="5min",
            )
        )
    )

    frame = pd.DataFrame({"time": times})

    result = gap.assess_gap(
        decision_time_utc=(
            "2026-10-10T12:00:00Z"
        ),
        completed_m5=frame,
    )

    assert result["status"] == (
        "STRICT_M5_GAP_CONFIRMED"
    )
    assert result["horizon_elapsed"] is True
    assert len(
        result["missing_m5_timestamps_utc"]
    ) > 0


def test_contiguous_horizon_is_not_gap():
    frame = pd.DataFrame({
        "time": pd.date_range(
            start="2026-10-10T12:00:00Z",
            periods=12,
            freq="5min",
        )
    })

    result = gap.assess_gap(
        decision_time_utc=(
            "2026-10-10T12:00:00Z"
        ),
        completed_m5=frame,
    )

    assert result["status"] == (
        "STRICT_M5_HORIZON_COMPLETE"
    )


def test_duplicate_terminal_snapshot_id_is_idempotent():
    previous = terminal("gap-1")

    updated = dict(previous)
    updated["evidence_snapshot_id"] = (
        "d" * 64
    )

    core = dict(updated)
    core.pop("semantic_fingerprint_sha256")

    updated["semantic_fingerprint_sha256"] = (
        gap.fingerprint(core)
    )

    assert gap.same_terminal_evidence(
        existing=previous,
        candidate=updated,
    )


def test_changed_missing_bars_is_conflict():
    previous = terminal("gap-1")

    updated = dict(previous)
    updated["missing_m5_timestamps_utc"] = [
        "2026-10-10T12:55:00+00:00"
    ]

    core = dict(updated)
    core.pop("semantic_fingerprint_sha256")

    updated["semantic_fingerprint_sha256"] = (
        gap.fingerprint(core)
    )

    assert not gap.same_terminal_evidence(
        existing=previous,
        candidate=updated,
    )
