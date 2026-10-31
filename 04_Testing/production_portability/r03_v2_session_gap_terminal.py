
from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
from typing import Any, Mapping, cast

import pandas as pd


VERSION = "R03_V2_SESSION_GAP_TERMINAL_V1"

LANE: Any = importlib.import_module(
    "04_Testing.production_portability.r03_v2_collection_lane"
)

TERMINAL_PATH = LANE.LANE_ROOT / "terminal_gaps.jsonl"

HORIZON_BARS = 12
BAR_MINUTES = 5


class TerminalGapError(RuntimeError):
    pass


def require(value: bool, reason: str) -> None:
    if not value:
        raise TerminalGapError(reason)


def utc(value: Any) -> pd.Timestamp:
    parsed = pd.Timestamp(value)

    if pd.isna(parsed):
        raise TerminalGapError("INVALID_TIMESTAMP")

    stamp = cast(pd.Timestamp, parsed)

    if stamp.tzinfo is None:
        raise TerminalGapError("TIMESTAMP_NOT_UTC_AWARE")

    return cast(
        pd.Timestamp,
        stamp.tz_convert("UTC"),
    )


def fingerprint(document: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        dict(document),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def expected_horizon(
    decision_time_utc: str,
) -> list[pd.Timestamp]:
    """
    Return exactly 12 expected M5 open timestamps.

    Explicit cast prevents Pyright from inferring
    Timestamp | NaTType for Timestamp arithmetic.
    """
    decision_time = utc(decision_time_utc)

    horizon: list[pd.Timestamp] = []

    for index in range(HORIZON_BARS):
        timestamp = cast(
            pd.Timestamp,
            decision_time
            + pd.Timedelta(
                minutes=BAR_MINUTES * (index + 1)
            ),
        )
        horizon.append(timestamp)

    return horizon


def assess_gap(
    *,
    decision_time_utc: str,
    completed_m5: pd.DataFrame,
) -> dict[str, Any]:
    """
    Assess the existing strict 12-M5-bar horizon.

    Missing timestamps are not enough to prove
    a session gap if the snapshot has truncated
    historical coverage.

    This function never interpolates or creates bars.
    """

    require(
        "time" in completed_m5.columns,
        "M5_TIME_MISSING",
    )

    require(
        not completed_m5.empty,
        "M5_FRAME_EMPTY",
    )

    raw_times = pd.to_datetime(
        completed_m5["time"],
        utc=True,
        errors="raise",
    )

    require(
        not bool(raw_times.isna().any()),
        "INVALID_M5_TIMESTAMP",
    )

    require(
        not bool(raw_times.duplicated().any()),
        "DUPLICATE_M5_TIMESTAMPS",
    )

    observed = pd.DatetimeIndex(
        raw_times
    ).sort_values()

    expected = expected_horizon(
        decision_time_utc
    )

    earliest = cast(pd.Timestamp, observed[0])
    latest = cast(pd.Timestamp, observed[-1])

    first_expected = expected[0]
    last_expected = expected[-1]

    # A recent MT5 snapshot can drop old bars.
    # Truncated history is not session-gap evidence.
    if earliest > utc(decision_time_utc):
        return {
            "status": "INSUFFICIENT_HISTORICAL_COVERAGE",
            "missing_m5_timestamps_utc": [],
            "horizon_elapsed": (
                latest >= last_expected
            ),
            "expected_first_utc": (
                first_expected.isoformat()
            ),
            "expected_last_utc": (
                last_expected.isoformat()
            ),
        }

    if latest < last_expected:
        return {
            "status": "WAIT_HORIZON_NOT_ELAPSED",
            "missing_m5_timestamps_utc": [],
            "horizon_elapsed": False,
            "expected_first_utc": (
                first_expected.isoformat()
            ),
            "expected_last_utc": (
                last_expected.isoformat()
            ),
        }

    present = set(observed)

    missing = [
        timestamp.isoformat()
        for timestamp in expected
        if timestamp not in present
    ]

    return {
        "status": (
            "STRICT_M5_GAP_CONFIRMED"
            if missing
            else "STRICT_M5_HORIZON_COMPLETE"
        ),
        "missing_m5_timestamps_utc": missing,
        "expected_first_utc": (
            first_expected.isoformat()
        ),
        "expected_last_utc": (
            last_expected.isoformat()
        ),
        "horizon_elapsed": True,
    }


def terminal_document(
    *,
    observation: Any,
    anchor: Any,
    snapshot_id: str,
    assessment: Mapping[str, Any],
) -> dict[str, Any]:
    logical_id = observation.logical_observation_id

    require(
        logical_id == anchor.logical_observation_id,
        "OBSERVATION_ANCHOR_ID_MISMATCH",
    )

    require(
        observation.semantic_record_fingerprint
        == anchor.semantic_observation_fingerprint,
        "OBSERVATION_ANCHOR_FINGERPRINT_MISMATCH",
    )

    require(
        observation.source_snapshot_id
        == anchor.source_snapshot_id,
        "OBSERVATION_ANCHOR_SOURCE_MISMATCH",
    )

    require(
        assessment["status"]
        == "STRICT_M5_GAP_CONFIRMED",
        "NO_CONFIRMED_TERMINAL_GAP",
    )

    missing = list(
        assessment["missing_m5_timestamps_utc"]
    )

    require(
        bool(missing),
        "MISSING_TIMESTAMP_EVIDENCE_EMPTY",
    )

    core = {
        "schema_version": VERSION,
        "logical_observation_id": logical_id,
        "disposition": (
            "UNSCORABLE_STRICT_M5_SESSION_GAP"
        ),
        "observation_fingerprint": (
            observation.semantic_record_fingerprint
        ),
        "anchor_fingerprint": (
            anchor.anchor_semantic_fingerprint
        ),
        "evidence_snapshot_id": snapshot_id,
        "missing_m5_timestamps_utc": missing,
        "expected_first_utc": (
            assessment["expected_first_utc"]
        ),
        "expected_last_utc": (
            assessment["expected_last_utc"]
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
            fingerprint(core)
        ),
    }


def validate_document(
    document: Mapping[str, Any],
) -> None:
    required = {
        "schema_version",
        "logical_observation_id",
        "disposition",
        "observation_fingerprint",
        "anchor_fingerprint",
        "evidence_snapshot_id",
        "missing_m5_timestamps_utc",
        "expected_first_utc",
        "expected_last_utc",
        "counts_as_matured_outcome",
        "terminal_resolution_authorized",
        "capture_slot_release_authorized",
        "live_authorized",
        "execution_authorized",
        "semantic_fingerprint_sha256",
    }

    require(
        set(document) == required,
        "TERMINAL_SCHEMA_MISMATCH",
    )

    require(
        document["schema_version"] == VERSION,
        "TERMINAL_VERSION_MISMATCH",
    )

    require(
        document["disposition"]
        == "UNSCORABLE_STRICT_M5_SESSION_GAP",
        "TERMINAL_DISPOSITION_MISMATCH",
    )

    logical_id = document["logical_observation_id"]

    require(
        isinstance(logical_id, str)
        and bool(logical_id.strip()),
        "TERMINAL_LOGICAL_ID_INVALID",
    )

    for key in (
        "counts_as_matured_outcome",
        "terminal_resolution_authorized",
        "capture_slot_release_authorized",
        "live_authorized",
        "execution_authorized",
    ):
        require(
            document[key] is False,
            f"UNEXPECTED_TERMINAL_AUTHORITY:{key}",
        )

    for key in (
        "observation_fingerprint",
        "anchor_fingerprint",
        "evidence_snapshot_id",
    ):
        value = document[key]

        require(
            isinstance(value, str)
            and len(value) == 64
            and all(
                char in "0123456789abcdef"
                for char in value
            ),
            f"INVALID_SOURCE_FINGERPRINT:{key}",
        )

    missing = document[
        "missing_m5_timestamps_utc"
    ]

    require(
        isinstance(missing, list)
        and 0 < len(missing) <= HORIZON_BARS,
        "INVALID_MISSING_TIMESTAMPS",
    )

    first = utc(
        document["expected_first_utc"]
    )

    last = utc(
        document["expected_last_utc"]
    )

    expected = [
        cast(
            pd.Timestamp,
            first
            + pd.Timedelta(
                minutes=BAR_MINUTES * index
            ),
        )
        for index in range(HORIZON_BARS)
    ]

    require(
        last == expected[-1],
        "TERMINAL_HORIZON_INVALID",
    )

    normalized = [
        utc(value)
        for value in missing
    ]

    require(
        len(normalized) == len(set(normalized)),
        "DUPLICATE_MISSING_TIMESTAMPS",
    )

    require(
        normalized == sorted(normalized),
        "UNSORTED_MISSING_TIMESTAMPS",
    )

    require(
        all(value in expected for value in normalized),
        "MISSING_TIMESTAMP_OUTSIDE_HORIZON",
    )

    core = dict(document)

    supplied = core.pop(
        "semantic_fingerprint_sha256"
    )

    require(
        supplied == fingerprint(core),
        "TERMINAL_FINGERPRINT_MISMATCH",
    )


def read_terminal_records(
    path: Path = TERMINAL_PATH,
) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}

    require(
        path.is_file(),
        "TERMINAL_LEDGER_NOT_FILE",
    )

    content = path.read_bytes()

    require(
        not content
        or content.endswith(b"\n"),
        "TERMINAL_LEDGER_PARTIAL_LINE",
    )

    records: dict[str, dict[str, Any]] = {}

    for line_number, raw_line in enumerate(
        content.splitlines(),
        start=1,
    ):
        require(
            bool(raw_line.strip()),
            f"EMPTY_TERMINAL_LINE:{line_number}",
        )

        try:
            document = json.loads(
                raw_line.decode("utf-8")
            )

        except (
            ValueError,
            UnicodeError,
        ) as exc:
            raise TerminalGapError(
                f"INVALID_TERMINAL_JSON:{line_number}"
            ) from exc

        require(
            isinstance(document, dict),
            "TERMINAL_RECORD_NOT_OBJECT",
        )

        validate_document(document)

        logical_id = document[
            "logical_observation_id"
        ]

        require(
            logical_id not in records,
            f"DUPLICATE_TERMINAL_ID:{logical_id}",
        )

        records[logical_id] = document

    return records


def select_pending_for_gap(
    *,
    observations: Mapping[str, Any],
    anchors: Mapping[str, Any],
    outcomes: Mapping[str, Any],
    terminals: Mapping[
        str, Mapping[str, Any]
    ],
    protocol_approved: bool,
    terminal_policy_approved: bool,
) -> str:
    """
    Select exactly one effective pending observation.

    Exclude older terminal IDs only when BOTH
    authorities permit terminal resolution.
    """

    resolution = LANE.reconcile_v2_resolution(
        observations=observations,
        anchors=anchors,
        outcomes=outcomes,
        terminals=terminals,
        protocol_approved=protocol_approved,
        terminal_policy_approved=terminal_policy_approved,
    )

    pending = LANE.effective_pending_ids(
        observations=observations,
        outcomes=outcomes,
        authorized_resolved_ids=(
            resolution.authorized_resolved_ids
        ),
    )

    require(
        len(pending) == 1,
        f"UNIQUE_EFFECTIVE_GAP_PENDING_REQUIRED:{len(pending)}",
    )

    logical_id = next(iter(pending))

    require(
        logical_id in anchors,
        "GAP_PENDING_ANCHOR_MISSING",
    )

    require(
        logical_id not in outcomes,
        "GAP_PENDING_ALREADY_MATURED",
    )

    return logical_id


def same_terminal_evidence(
    *,
    existing: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> bool:
    """
    A newer genuine snapshot has a different ID.
    It must not create duplicate terminal rows.

    Compare scientific disposition and record
    linkage rather than the new snapshot identity.
    """

    relevant = (
        "schema_version",
        "logical_observation_id",
        "disposition",
        "observation_fingerprint",
        "anchor_fingerprint",
        "missing_m5_timestamps_utc",
        "expected_first_utc",
        "expected_last_utc",
        "counts_as_matured_outcome",
        "terminal_resolution_authorized",
        "capture_slot_release_authorized",
        "live_authorized",
        "execution_authorized",
    )

    return all(
        existing[key] == candidate[key]
        for key in relevant
    )


def record_pending_gap(
    *,
    snapshot: Any,
) -> dict[str, Any]:
    """
    Record confirmed gap evidence for the one
    effective pending V2 observation.

    - Original V1 ledgers untouched
    - No fabricated matured outcome
    - No automatic capture-slot release
    - Sequential authorized terminal exclusions
      supported by effective pending selection
    """

    with LANE.collector_lock():
        controller, runtime, maturer = LANE.modules()

        observations, anchors, outcomes = (
            LANE.read_v2_records(
                controller,
                runtime,
                maturer,
            )
        )

        terminals = read_terminal_records()

        _, resolution_module = (
            LANE.terminal_modules()
        )

        protocol_ok = LANE.authority_valid()

        terminal_policy_ok = (
            resolution_module.verify_policy()
        )

        logical_id = select_pending_for_gap(
            observations=observations,
            anchors=anchors,
            outcomes=outcomes,
            terminals=terminals,
            protocol_approved=protocol_ok,
            terminal_policy_approved=terminal_policy_ok,
        )

        observation = observations[logical_id]
        anchor = anchors[logical_id]

        binder = (
            runtime.R03ProspectiveRuntimeBinder(
                inference_adapter=(
                    runtime.R03FrozenArtifactInferenceAdapter(
                        repo_root=LANE.ROOT
                    )
                )
            )
        )

        binder.verify_genuine_snapshot_authority(
            snapshot
        )

        market = getattr(
            snapshot,
            "market_data",
            None,
        )

        if not isinstance(market, Mapping):
            raise TerminalGapError(
                "SNAPSHOT_MARKET_DATA_INVALID"
            )

        m5 = market.get("M5")

        if not isinstance(m5, pd.DataFrame):
            raise TerminalGapError(
                "SNAPSHOT_M5_INVALID"
            )

        verified_m5 = (
            maturer.validate_completed_m5(m5)
        )

        assessment = assess_gap(
            decision_time_utc=(
                anchor.decision_time_utc
            ),
            completed_m5=verified_m5,
        )

        if assessment["status"] != (
            "STRICT_M5_GAP_CONFIRMED"
        ):
            return {
                "action": assessment["status"],
                "logical_observation_id": logical_id,
                "evidence_appended": False,
                "capture_slot_released": False,
                "live_authorized": False,
                "execution_authorized": False,
            }

        document = terminal_document(
            observation=observation,
            anchor=anchor,
            snapshot_id=(
                snapshot.source_snapshot_id
            ),
            assessment=assessment,
        )

        existing = terminals.get(logical_id)

        if existing is not None:
            require(
                same_terminal_evidence(
                    existing=existing,
                    candidate=document,
                ),
                "TERMINAL_EVIDENCE_CONFLICT",
            )

            return {
                "action": (
                    "TERMINAL_EVIDENCE_ALREADY_PRESENT"
                ),
                "logical_observation_id": logical_id,
                "evidence_appended": False,
                "capture_slot_released": False,
                "live_authorized": False,
                "execution_authorized": False,
            }

        require(
            TERMINAL_PATH.parent.is_dir(),
            "TERMINAL_PARENT_MISSING",
        )

        payload = (
            json.dumps(
                document,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
            + b"\n"
        )

        with TERMINAL_PATH.open("ab") as handle:
            written = handle.write(payload)

            require(
                written == len(payload),
                "TERMINAL_WRITE_INCOMPLETE",
            )

            handle.flush()
            os.fsync(handle.fileno())

        verified = read_terminal_records()

        require(
            verified.get(logical_id) == document,
            "TERMINAL_POSTWRITE_INTEGRITY_FAILED",
        )

        return {
            "action": "TERMINAL_EVIDENCE_RECORDED",
            "logical_observation_id": logical_id,
            "missing_m5_timestamps_utc": (
                document[
                    "missing_m5_timestamps_utc"
                ]
            ),
            "evidence_appended": True,
            "capture_slot_released": False,
            "counts_as_matured_outcome": False,
            "live_authorized": False,
            "execution_authorized": False,
        }
