from __future__ import annotations

import importlib
from dataclasses import replace
from typing import Any

import pytest


r4: Any = importlib.import_module(
    "04_Testing.production_portability.r03_terminal_resolution_r4"
)


def test_exact_disposition():
    assert r4.DISPOSITION == (
        "EXCLUDED_STRICT_M5_SESSION_GAP"
    )


def test_exact_gap_evidence():
    document = r4.expected_exclusion_document()

    assert len(document["missing_m5_timestamps_utc"]) == 7
    assert document["actual_last_future_bar_utc"] == (
        "2026-10-05T22:30:00+00:00"
    )

    assert r4.validate_exclusion_document(document)


def test_evidence_tampering_fails():
    document = r4.expected_exclusion_document()
    document["actual_last_future_bar_utc"] = (
        "2026-10-05T21:30:00+00:00"
    )

    with pytest.raises(
        r4.R03TerminalResolutionError,
        match="EXCLUSION_EVIDENCE_AUTHORITY_MISMATCH",
    ):
        r4.validate_exclusion_document(document)


def test_fingerprint_tampering_fails():
    document = r4.expected_exclusion_document()
    document["semantic_fingerprint_sha256"] = "0" * 64

    with pytest.raises(
        r4.R03TerminalResolutionError,
        match="EXCLUSION_EVIDENCE_AUTHORITY_MISMATCH",
    ):
        r4.validate_exclusion_document(document)


def test_no_authorized_outcome_or_execution():
    document = r4.expected_exclusion_document()

    assert document["counts_as_matured_outcome"] is False
    assert document["live_authorized"] is False
    assert document["execution_authorized"] is False


def test_reconciled_state_is_non_mutating():
    original = r4.R4ReconciledState(
        observation_count=14,
        anchor_count=14,
        matured_outcome_count=13,
        excluded_count=1,
        unresolved_pending_count=0,
        original_pending_count=1,
        original_next_action="CHECK_PENDING_MATURITY",
        proposed_next_action=(
            "CANDIDATE_CAPTURE_NEW_OBSERVATION"
        ),
        collection_target_reached=False,
    )

    document = original.to_dict()

    assert document["matured_outcome_count"] == 13
    assert document["excluded_count"] == 1
    assert document["unresolved_pending_count"] == 0
    assert document["controller_promotion_authorized"] is False
    assert document["ledger_writes_authorized"] is False

    changed = replace(
        original,
        excluded_count=0,
    )

    assert original.excluded_count == 1
    assert changed.excluded_count == 0