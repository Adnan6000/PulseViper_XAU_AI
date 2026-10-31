from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from typing import Any


VERSION = "R03_SCIENTIFIC_DISPOSITION_R4_V1"

DECISION = "EXCLUDE_FROM_STRICT_CONTIGUOUS_V1_MATURATION"

STATUS = "PROPOSED_NOT_AUTHORIZED"

REPO_ROOT = Path(__file__).resolve().parents[2]

resolution: Any = importlib.import_module(
    "04_Testing.production_portability.r03_terminal_resolution_r4"
)

evidence: Any = importlib.import_module(
    "04_Testing.production_portability.r03_session_gap_evidence_ledger_r4"
)

controller: Any = importlib.import_module(
    "02_AI.Models.r03_prospective_collection_controller"
)

maturer: Any = importlib.import_module(
    "02_AI.Models.frozen_r03_prospective_outcome_maturer"
)

contract: Any = importlib.import_module(
    "02_AI.Models.frozen_r03_prospective_forward_validation_contract"
)


class R03DispositionError(RuntimeError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise R03DispositionError(reason)


def canonical_bytes(document: dict[str, Any]) -> bytes:
    return json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def build_decision(
    *,
    evidence_path: Path = evidence.DEFAULT_LEDGER,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:

    events = evidence.read_events(evidence_path)

    require(
        len(events) == 1,
        "EXPECTED_ONE_VERIFIED_GAP_EVENT",
    )

    event = events[0]
    evidence.validate_document(event)

    state = controller.inspect_state(repo_root=repo_root)

    require(
        state.pending_count == 1,
        "EXPECTED_ONE_PENDING",
    )

    require(
        state.pending_logical_observation_id
        == resolution.PENDING_ID,
        "PENDING_ID_MISMATCH",
    )

    require(
        resolution.PENDING_ID
        not in controller.read_outcomes(repo_root=repo_root),
        "PENDING_ALREADY_MATURED",
    )

    require(
        maturer.EXPECTED_HORIZON_BARS == 12,
        "MATURER_HORIZON_CHANGED",
    )

    require(
        contract.HORIZON_BARS == 12,
        "CONTRACT_HORIZON_CHANGED",
    )

    require(
        contract.HORIZON_MINUTES == 60,
        "CONTRACT_DURATION_CHANGED",
    )

    require(
        maturer.HORIZON_SEMANTICS
        == "NEXT_12_COMPLETED_M5_ROWS_AFTER_DECISION_BAR",
        "HORIZON_SEMANTICS_CHANGED",
    )

    source = event["source_document"]

    require(
        source["logical_observation_id"]
        == resolution.PENDING_ID,
        "GAP_EVIDENCE_ID_MISMATCH",
    )

    require(
        len(source["missing_m5_timestamps_utc"]) == 7,
        "GAP_EVIDENCE_TIMESTAMP_COUNT_CHANGED",
    )

    core = {
        "schema_version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "logical_observation_id": resolution.PENDING_ID,
        "reason": "STRICT_M5_CONTINUITY_NOT_SATISFIED",
        "horizon_bars": 12,
        "horizon_minutes": 60,
        "published_maturation_version": (
            maturer.MATURATION_VERSION
        ),
        "evidence_fingerprint_sha256": event[
            "event_fingerprint_sha256"
        ],
        "original_matured_outcome_count": (
            state.matured_outcome_count
        ),
        "counts_as_matured_outcome": False,
        "terminal_disposition_authorized": False,
        "controller_promotion_authorized": False,
        "new_capture_authorized": False,
        "live_authorized": False,
        "execution_authorized": False,
    }

    return {
        **core,
        "decision_fingerprint_sha256": hashlib.sha256(
            canonical_bytes(core)
        ).hexdigest(),
    }


def main() -> int:
    print("R03_SCIENTIFIC_DISPOSITION_VERSION=" + VERSION)

    try:
        decision = build_decision()

    except Exception as exc:
        print("R03_SCIENTIFIC_DISPOSITION_STATUS=BLOCKED")
        print("ERROR_TYPE=" + type(exc).__name__)
        print("ERROR=" + str(exc))
        return 2

    print("R03_SCIENTIFIC_DISPOSITION_STATUS=PROPOSED")
    print(
        json.dumps(
            decision,
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())