from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest


ledger: Any = importlib.import_module(
    "04_Testing.production_portability."
    "r03_session_gap_evidence_ledger_r4"
)


def test_evidence_is_deterministic():
    first = ledger.evidence_document()
    second = ledger.evidence_document()

    assert first == second
    ledger.validate_document(first)


def test_evidence_never_authorizes_promotion():
    event = ledger.evidence_document()

    assert event["counts_as_matured_outcome"] is False
    assert event["terminal_exclusion_authorized"] is False
    assert event["controller_promotion_authorized"] is False
    assert event["live_authorized"] is False
    assert event["execution_authorized"] is False


def test_tampering_blocked():
    event = ledger.evidence_document()
    event["terminal_exclusion_authorized"] = True

    with pytest.raises(
        ledger.R03EvidenceLedgerError,
        match="EVIDENCE_DOCUMENT_MISMATCH",
    ):
        ledger.validate_document(event)


def test_append_once_and_idempotency(tmp_path: Path):
    path = tmp_path / "evidence.jsonl"

    assert ledger.append_once(path=path) == (
        "DIAGNOSTIC_EVIDENCE_APPENDED"
    )

    original = path.read_bytes()

    assert ledger.append_once(path=path) == (
        "IDEMPOTENT_ALREADY_RECORDED"
    )

    assert path.read_bytes() == original
    assert len(ledger.read_events(path)) == 1


def test_corrupt_ledger_fails_closed(tmp_path: Path):
    path = tmp_path / "evidence.jsonl"
    path.write_bytes(b'{"invalid":true}\n')

    with pytest.raises(
        ledger.R03EvidenceLedgerError,
        match="EVIDENCE_DOCUMENT_MISMATCH",
    ):
        ledger.append_once(path=path)


def test_partial_record_fails_closed(tmp_path: Path):
    path = tmp_path / "evidence.jsonl"
    path.write_bytes(b'{"partial":true}')

    with pytest.raises(
        ledger.R03EvidenceLedgerError,
        match="LEDGER_PARTIAL_FINAL_RECORD",
    ):
        ledger.read_events(path)


def test_existing_lock_blocks(tmp_path: Path):
    path = tmp_path / "evidence.jsonl"
    lock = tmp_path / "evidence.jsonl.lock"
    lock.write_text("owned-by-another-process")

    with pytest.raises(
        ledger.R03EvidenceLedgerError,
        match="EVIDENCE_LEDGER_LOCKED",
    ):
        ledger.append_once(path=path)


def test_successful_append_releases_lock(tmp_path: Path):
    path = tmp_path / "evidence.jsonl"

    ledger.append_once(path=path)

    assert not (
        tmp_path / "evidence.jsonl.lock"
    ).exists()