from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest


runner: Any = importlib.import_module(
    "04_Testing.production_portability."
    "run_r03_r4_authority_preflight"
)


def test_version():
    assert runner.VERSION == (
        "R03_R4_AUTHORITY_PREFLIGHT_V1"
    )


def test_missing_evidence_fails_closed(tmp_path: Path):
    with pytest.raises(
        runner.R4AuthorityError,
        match="R4_EVIDENCE_FILE_MISSING",
    ):
        runner.run_preflight(
            repo_root=tmp_path,
            evidence_path=tmp_path / "missing.jsonl",
        )


def test_valid_evidence_rejects_wrong_pending_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence_path = tmp_path / "evidence.jsonl"

    runner.ledger.append_once(
        path=evidence_path
    )

    class FakeState:
        pending_count = 1
        next_action = "CHECK_PENDING_MATURITY"
        pending_logical_observation_id = "wrong-id"

    monkeypatch.setattr(
        runner.controller,
        "inspect_state",
        lambda **kwargs: FakeState(),
    )

    with pytest.raises(
        runner.R4AuthorityError,
        match="PENDING_ID_EVIDENCE_MISMATCH",
    ):
        runner.run_preflight(
            repo_root=tmp_path,
            evidence_path=evidence_path,
        )


def test_corrupt_evidence_fails_closed(tmp_path: Path):
    evidence_path = tmp_path / "evidence.jsonl"

    evidence_path.write_text(
        '{"invalid":true}\n',
        encoding="utf-8",
    )

    with pytest.raises(
        runner.ledger.R03EvidenceLedgerError,
        match="EVIDENCE_DOCUMENT_MISMATCH",
    ):
        runner.run_preflight(
            repo_root=tmp_path,
            evidence_path=evidence_path,
        )


def test_existing_evidence_not_rewritten(tmp_path: Path):
    evidence_path = tmp_path / "evidence.jsonl"

    runner.ledger.append_once(
        path=evidence_path
    )

    before = runner.file_hash(evidence_path)

    assert len(
        runner.ledger.read_events(evidence_path)
    ) == 1

    after = runner.file_hash(evidence_path)

    assert before == after


def test_no_runtime_mutation_calls():
    source = Path(
        runner.__file__
    ).read_text(encoding="utf-8")

    forbidden = (
        ".mature_pending_from_snapshot(",
        ".capture_new_observation_from_snapshot(",
        ".append_once(",
        ".order_send(",
        ".order_check(",
    )

    for call in forbidden:
        assert call not in source