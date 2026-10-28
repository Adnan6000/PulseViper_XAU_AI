
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

VERSION = "R03_V2_PROTOCOL_AUTHORITY_V1"

REPO_ROOT = Path(__file__).resolve().parents[2]

PROTOCOL_PATH = (
    REPO_ROOT
    / "04_Testing"
    / "production_portability"
    / "R03_V2_SCIENTIFIC_PROTOCOL.md"
)

REVIEW_PATH = Path(
    "D:/PulseViper_R03_Recovery_Backup/"
    "r03_v2_collection/approved_protocol.json"
)

COHORT = "V2_INDEPENDENT_PROSPECTIVE_COHORT"
LANE_VERSION = "R03_COLLECTION_LANE_V2_1"

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ProtocolAuthorityError(RuntimeError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ProtocolAuthorityError(reason)


def sha256_file(path: Path) -> str:
    require(path.is_file(), f"FILE_MISSING:{path}")

    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for chunk in iter(
            lambda: stream.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def read_json_object(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"REVIEW_MISSING:{path}")

    def no_duplicate_keys(
        pairs: list[tuple[str, Any]],
    ) -> dict[str, Any]:
        document: dict[str, Any] = {}

        for key, value in pairs:
            require(
                key not in document,
                f"DUPLICATE_REVIEW_FIELD:{key}",
            )
            document[key] = value

        return document

    try:
        document = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=no_duplicate_keys,
        )
    except (UnicodeError, ValueError) as exc:
        raise ProtocolAuthorityError(
            "REVIEW_JSON_INVALID"
        ) from exc

    require(
        isinstance(document, dict),
        "REVIEW_NOT_OBJECT",
    )

    return document


def verify_review(
    *,
    protocol_path: Path = PROTOCOL_PATH,
    review_path: Path = REVIEW_PATH,
    pinned_review_sha256: str | None = None,
) -> bool:
    """
    Research-only permission check.

    No pin means no authorization.

    This verifies recorded review claims and file
    integrity. It does NOT authenticate a reviewer's
    real-world identity or independence.
    """

    if pinned_review_sha256 is None:
        return False

    require(
        bool(SHA256_PATTERN.fullmatch(pinned_review_sha256)),
        "REVIEW_PIN_INVALID",
    )

    require(
        sha256_file(review_path) == pinned_review_sha256,
        "REVIEW_SHA256_MISMATCH",
    )

    document = read_json_object(review_path)

    expected_fields = {
        "authority_version",
        "protocol_version",
        "protocol_sha256",
        "cohort_policy",
        "review_decision",
        "reviewer",
        "reviewed_at_utc",
        "reviewer_independent_attestation",
        "scope",
        "v1_ledger_mutation_authorized",
        "v1_terminal_disposition_authorized",
        "live_authorized",
        "execution_authorized",
        "retraining_authorized",
    }

    require(
        set(document) == expected_fields,
        "REVIEW_SCHEMA_MISMATCH",
    )

    require(
        document["authority_version"] == VERSION,
        "AUTHORITY_VERSION_MISMATCH",
    )

    require(
        document["protocol_version"] == LANE_VERSION,
        "LANE_VERSION_MISMATCH",
    )

    require(
        document["cohort_policy"] == COHORT,
        "COHORT_MISMATCH",
    )

    require(
        document["review_decision"] == "APPROVED",
        "REVIEW_NOT_APPROVED",
    )

    require(
        document["reviewer_independent_attestation"] is True,
        "INDEPENDENT_ATTESTATION_MISSING",
    )

    reviewer = document["reviewer"]

    require(
        isinstance(reviewer, str)
        and bool(reviewer.strip())
        and reviewer != "PENDING",
        "REVIEWER_INVALID",
    )

    reviewed_at = document["reviewed_at_utc"]

    require(
        isinstance(reviewed_at, str),
        "REVIEW_TIME_INVALID",
    )

    try:
        timestamp = datetime.fromisoformat(
            reviewed_at.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ProtocolAuthorityError(
            "REVIEW_TIME_INVALID"
        ) from exc

    require(
        timestamp.tzinfo is not None,
        "REVIEW_TIME_NOT_TIMEZONE_AWARE",
    )

    require(
        timestamp.astimezone(timezone.utc)
        <= datetime.now(timezone.utc),
        "REVIEW_TIME_IN_FUTURE",
    )

    require(
        document["scope"] == [
            "V2_RESEARCH_CAPTURE",
            "V2_STRICT_M5_MATURATION",
        ],
        "REVIEW_SCOPE_INVALID",
    )

    for field in (
        "v1_ledger_mutation_authorized",
        "v1_terminal_disposition_authorized",
        "live_authorized",
        "execution_authorized",
        "retraining_authorized",
    ):
        require(
            document[field] is False,
            f"FORBIDDEN_AUTHORIZATION:{field}",
        )

    expected_protocol_hash = document["protocol_sha256"]

    require(
        isinstance(expected_protocol_hash, str)
        and bool(
            SHA256_PATTERN.fullmatch(
                expected_protocol_hash
            )
        ),
        "PROTOCOL_HASH_INVALID",
    )

    require(
        sha256_file(protocol_path)
        == expected_protocol_hash,
        "PROTOCOL_DOCUMENT_CHANGED",
    )

    protocol_text = protocol_path.read_text(
        encoding="utf-8"
    )

    require(
        "R03_COLLECTION_LANE_V2_1" in protocol_text,
        "PROTOCOL_ID_MISSING",
    )

    require(
        "V2_INDEPENDENT_PROSPECTIVE_COHORT"
        in protocol_text,
        "COHORT_NOT_IN_PROTOCOL",
    )

    require(
        "12 consecutive completed M5 future bars"
        in protocol_text,
        "HORIZON_NOT_IN_PROTOCOL",
    )

    return True


def review_template(
    *,
    protocol_path: Path = PROTOCOL_PATH,
) -> dict[str, Any]:
    """
    Unapproved review template only.
    Does not write any files.
    """

    return {
        "authority_version": VERSION,
        "protocol_version": LANE_VERSION,
        "protocol_sha256": sha256_file(protocol_path),
        "cohort_policy": COHORT,
        "review_decision": "PENDING",
        "reviewer": "PENDING",
        "reviewed_at_utc": "PENDING",
        "reviewer_independent_attestation": False,
        "scope": [
            "V2_RESEARCH_CAPTURE",
            "V2_STRICT_M5_MATURATION",
        ],
        "v1_ledger_mutation_authorized": False,
        "v1_terminal_disposition_authorized": False,
        "live_authorized": False,
        "execution_authorized": False,
        "retraining_authorized": False,
    }


if __name__ == "__main__":
    try:
        print(
            json.dumps(
                review_template(),
                indent=2,
                sort_keys=True,
            )
        )
    except ProtocolAuthorityError as exc:
        print(f"R03_V2_PROTOCOL_STATUS=BLOCKED:{exc}")
        raise SystemExit(2) from exc
