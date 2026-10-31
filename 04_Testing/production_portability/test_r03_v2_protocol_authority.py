
from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


a = importlib.import_module(
    "04_Testing.production_portability."
    "r03_v2_protocol_authority"
)


PROTOCOL = """
# R03_COLLECTION_LANE_V2_1

V2_INDEPENDENT_PROSPECTIVE_COHORT

12 consecutive completed M5 future bars
"""


def setup_review(
    tmp_path: Path,
) -> tuple[Path, Path, str]:
    protocol = tmp_path / "protocol.md"
    protocol.write_text(PROTOCOL, encoding="utf-8")

    review = a.review_template(
        protocol_path=protocol
    )

    review["review_decision"] = "APPROVED"
    review["reviewer"] = "Independent Reviewer"
    review["reviewed_at_utc"] = (
        "2026-10-01T12:00:00Z"
    )
    review["reviewer_independent_attestation"] = True

    path = tmp_path / "review.json"

    path.write_text(
        json.dumps(review, sort_keys=True),
        encoding="utf-8",
    )

    return protocol, path, a.sha256_file(path)


def test_missing_pin_blocks(tmp_path: Path) -> None:
    protocol, review, _ = setup_review(tmp_path)

    assert a.verify_review(
        protocol_path=protocol,
        review_path=review,
        pinned_review_sha256=None,
    ) is False


def test_review_claim_verification(tmp_path: Path) -> None:
    protocol, review, sha = setup_review(tmp_path)

    assert a.verify_review(
        protocol_path=protocol,
        review_path=review,
        pinned_review_sha256=sha,
    ) is True


def test_protocol_tampering_blocks(tmp_path: Path) -> None:
    protocol, review, sha = setup_review(tmp_path)

    protocol.write_text(
        PROTOCOL + "\nmodified",
        encoding="utf-8",
    )

    with pytest.raises(
        a.ProtocolAuthorityError,
        match="PROTOCOL_DOCUMENT_CHANGED",
    ):
        a.verify_review(
            protocol_path=protocol,
            review_path=review,
            pinned_review_sha256=sha,
        )


def test_review_tampering_blocks(tmp_path: Path) -> None:
    protocol, review, sha = setup_review(tmp_path)

    review.write_text("{}", encoding="utf-8")

    with pytest.raises(
        a.ProtocolAuthorityError,
        match="REVIEW_SHA256_MISMATCH",
    ):
        a.verify_review(
            protocol_path=protocol,
            review_path=review,
            pinned_review_sha256=sha,
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("review_decision", "PENDING"),
        ("reviewer_independent_attestation", False),
        ("live_authorized", True),
        ("execution_authorized", True),
        ("retraining_authorized", True),
        ("v1_ledger_mutation_authorized", True),
        ("v1_terminal_disposition_authorized", True),
        ("scope", ["LIVE_TRADING"]),
    ],
)
def test_forbidden_review_states(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    protocol, review, _ = setup_review(tmp_path)

    document = json.loads(
        review.read_text(encoding="utf-8")
    )

    document[field] = value

    review.write_text(
        json.dumps(document),
        encoding="utf-8",
    )

    with pytest.raises(a.ProtocolAuthorityError):
        a.verify_review(
            protocol_path=protocol,
            review_path=review,
            pinned_review_sha256=a.sha256_file(review),
        )


def test_unapproved_template(tmp_path: Path) -> None:
    protocol = tmp_path / "protocol.md"
    protocol.write_text(PROTOCOL, encoding="utf-8")

    result = a.review_template(
        protocol_path=protocol
    )

    assert result["review_decision"] == "PENDING"
    assert result["live_authorized"] is False
    assert result["reviewer_independent_attestation"] is False
