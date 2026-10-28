
from __future__ import annotations

import importlib
from dataclasses import dataclass

import pandas as pd
import pytest


m = importlib.import_module(
    "04_Testing.production_portability."
    "r03_v2_session_gap_terminal"
)


@dataclass(frozen=True)
class Record:
    logical_observation_id: str = "sample"
    semantic_record_fingerprint: str = "a" * 64
    semantic_observation_fingerprint: str = "a" * 64
    anchor_semantic_fingerprint: str = "b" * 64
    source_snapshot_id: str = "c" * 64


def bars(times: list[str]) -> pd.DataFrame:
    return pd.DataFrame({"time": times})


def full_times() -> list[str]:
    return [
        (
            pd.Timestamp("2026-10-05T20:35:00Z")
            + pd.Timedelta(minutes=5 * index)
        ).isoformat()
        for index in range(12)
    ]


def test_contiguous_horizon():
    result = m.assess_gap(
        decision_time_utc="2026-10-05T20:35:00Z",
        completed_m5=bars(full_times()),
    )

    assert result["status"] == (
        "STRICT_M5_HORIZON_COMPLETE"
    )


def test_realistic_session_gap():
    times = full_times()[:5] + [
        "2026-10-05T22:00:00Z",
        "2026-10-05T22:05:00Z",
    ]

    result = m.assess_gap(
        decision_time_utc="2026-10-05T20:35:00Z",
        completed_m5=bars(times),
    )

    assert result["status"] == (
        "STRICT_M5_GAP_CONFIRMED"
    )

    assert len(
        result["missing_m5_timestamps_utc"]
    ) == 7


def test_incomplete_horizon_waits():
    result = m.assess_gap(
        decision_time_utc="2026-10-05T20:35:00Z",
        completed_m5=bars(full_times()[:3]),
    )

    assert result["status"] == (
        "WAIT_HORIZON_NOT_ELAPSED"
    )


def test_document_cannot_authorize_capture():
    assessment = m.assess_gap(
        decision_time_utc="2026-10-05T20:35:00Z",
        completed_m5=bars(
            full_times()[:5]
            + ["2026-10-05T22:00:00Z"]
        ),
    )

    observation = Record()

    anchor = type(
        "Anchor",
        (),
        {
            "logical_observation_id": "sample",
            "semantic_observation_fingerprint": "a" * 64,
            "anchor_semantic_fingerprint": "b" * 64,
            "source_snapshot_id": "c" * 64,
        },
    )()

    document = m.terminal_document(
        observation=observation,
        anchor=anchor,
        snapshot_id="d" * 64,
        assessment=assessment,
    )

    m.validate_document(document)

    assert document["capture_slot_release_authorized"] is False
    assert document["counts_as_matured_outcome"] is False


def test_tampering_rejected():
    assessment = m.assess_gap(
        decision_time_utc="2026-10-05T20:35:00Z",
        completed_m5=bars(
            full_times()[:5]
            + ["2026-10-05T22:00:00Z"]
        ),
    )

    observation = Record()

    anchor = type(
        "Anchor",
        (),
        {
            "logical_observation_id": "sample",
            "semantic_observation_fingerprint": "a" * 64,
            "anchor_semantic_fingerprint": "b" * 64,
            "source_snapshot_id": "c" * 64,
        },
    )()

    document = m.terminal_document(
        observation=observation,
        anchor=anchor,
        snapshot_id="d" * 64,
        assessment=assessment,
    )

    document["live_authorized"] = True

    with pytest.raises(
        m.TerminalGapError,
        match="UNEXPECTED_TERMINAL_AUTHORITY",
    ):
        m.validate_document(document)


def test_duplicate_times_rejected():
    times = full_times()
    times.append(times[0])

    with pytest.raises(
        m.TerminalGapError,
        match="DUPLICATE_M5_TIMESTAMPS",
    ):
        m.assess_gap(
            decision_time_utc="2026-10-05T20:35:00Z",
            completed_m5=bars(times),
        )


def test_no_future_rewriting():
    result = m.assess_gap(
        decision_time_utc="2026-10-05T20:35:00Z",
        completed_m5=bars(
            full_times()[:5]
            + ["2026-10-05T22:00:00Z"]
        ),
    )

    assert result["missing_m5_timestamps_utc"][0] == (
        "2026-10-05T21:00:00+00:00"
    )
