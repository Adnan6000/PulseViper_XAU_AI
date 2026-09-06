"""
===============================================================================
Module      : frozen_c04_shadow_observer.py
Project     : PulseViper XAU AI
Purpose     : Forward Shadow Observation Infrastructure & Safety Harness (Gate 15A)
===============================================================================

Production-safe observation infrastructure required for future unseen-regime
forward shadow validation.

Establishes the safe, read-only data path:
  broker-derived market snapshot
    -> Gate 13 PortableFeaturePipeline
    -> validated frozen 331 matrix
    -> Gate 14 FrozenC04InferenceAdapter
    -> READ-ONLY shadow observation record

Gate 15A Safety Constraints (NON-NEGOTIABLE):
- Zero trading execution: no RiskEngine, execution readiness checks, order routing, SL/TP, or broker writes.
- live_authorized = False, execution_authorized = False.
- forward_performance_evaluated = False.
- No live-feed overclaim: TRUE_FORWARD_OBSERVATION is NOT authorized in Gate 15A (count = 0).
- Outcome horizon contract is strictly marked BLOCKED_NOT_PREDEFINED (no fabricated horizons).
- Append-only ledger with locked durable append and fail-closed corruption detection.
"""

from __future__ import annotations

import contextlib
import dataclasses
import datetime
from enum import Enum
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Generator, Sequence

import numpy as np
import pandas as pd

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Safe lazy import of Gate 13 and Gate 14 modules
_contract = importlib.import_module("02_AI.Features.portable_feature_contract")
_adapter = importlib.import_module("02_AI.Models.frozen_c04_inference_adapter")

EXPECTED_FEATURE_COUNT: int = int(_contract.EXPECTED_FEATURE_COUNT)
EXPECTED_FEATURE_COLUMNS_SHA256: str = str(_contract.EXPECTED_FEATURE_COLUMNS_SHA256)
FROZEN_MODEL_SHA256: str = str(_contract.FROZEN_MODEL_SHA256)
FROZEN_MODEL_CLASSES: tuple[int, ...] = tuple(_contract.FROZEN_MODEL_CLASSES)
LABEL_MAP: dict[int, str] = dict(_adapter.LABEL_MAP)
EXPECTED_MODEL_CLASS_NAME: str = str(_adapter.EXPECTED_MODEL_CLASS_NAME)
FrozenC04InferenceAdapter = _adapter.FrozenC04InferenceAdapter
FrozenC04InferenceRow = _adapter.FrozenC04InferenceRow

# -----------------------------------------------------------------------------
# Immutable Authorities & Constants
# -----------------------------------------------------------------------------

OBSERVER_SCHEMA_VERSION: str = "1.0.0"

# Proven maximum historical source timestamp across all historical timeframes
# (D1, H1, H4, M15, M30, M5) from authoritative frozen manifest:
RESEARCH_FREEZE_BOUNDARY_UTC: str = "2026-08-14T20:55:00Z"
RESEARCH_FREEZE_BOUNDARY_SOURCE: str = (
    "01_Data/Canonical/Instruments/XAUUSD/learning/scope_c8705b79f4cb595c4a2dec477d76a64956ae63133a2f91426f1647a3c5f5cfef/"
    "training/XAUUSD_MTF_TRAINING_V3/portable_v1/pv_portable_xauusd_cff75b0686383a3ab6f8352b.manifest.json"
)
RESEARCH_FREEZE_BOUNDARY_KEY: str = "source_historical_snapshots.M5.end_time"

# Gate 15A activation authority timestamp (frozen once, persisted)
GATE_15A_ACTIVATION_UTC: str = "2026-09-06T13:20:00Z"

# Outcome evaluation contract status: strictly BLOCKED_NOT_PREDEFINED in Gate 15A
OUTCOME_HORIZON_CONTRACT_STATUS: str = "BLOCKED_NOT_PREDEFINED"


# -----------------------------------------------------------------------------
# Provenance & Error Classes
# -----------------------------------------------------------------------------

class SourceProvenance(str, Enum):
    """Explicit source classification governing forward eligibility."""
    HISTORICAL_ENGINEERING = "HISTORICAL_ENGINEERING"
    SYNTHETIC_ENGINEERING = "SYNTHETIC_ENGINEERING"
    TRUE_FORWARD_OBSERVATION = "TRUE_FORWARD_OBSERVATION"


class DuplicateHandling(str, Enum):
    """Ledger behavior when encountering an existing logical observation ID."""
    FAIL_CLOSED = "FAIL_CLOSED"
    IDEMPOTENT_IGNORE = "IDEMPOTENT_IGNORE"


class FrozenC04ObservationError(Exception):
    """Base exception for all Gate 15A observation errors (fail-closed)."""
    pass


class DuplicateObservationError(FrozenC04ObservationError):
    """Raised when an exact duplicate observation is rejected under FAIL_CLOSED."""
    pass


class ConflictingObservationError(FrozenC04ObservationError):
    """Raised when the same logical observation ID is submitted with conflicting content."""
    pass


class CorruptedLedgerError(FrozenC04ObservationError):
    """Raised when a ledger file contains malformed, corrupted, or truncated records."""
    pass


class TrueForwardAcquisitionNotAuthorizedError(FrozenC04ObservationError):
    """Raised when caller attempts to create a TRUE_FORWARD_OBSERVATION without approved live acquisition."""
    pass


class InvalidDecisionTimestampError(FrozenC04ObservationError):
    """Raised when a decision timestamp is invalid, naive, or lacks explicit UTC offset."""
    pass


class InvalidSnapshotIdError(FrozenC04ObservationError):
    """Raised when a source snapshot ID is not a valid 64-character lowercase hex SHA256."""
    pass


class OutcomeContractBlockedError(FrozenC04ObservationError):
    """Raised when attempting to evaluate future outcomes while the horizon contract is BLOCKED."""
    pass


# -----------------------------------------------------------------------------
# Validation & Identification Helpers
# -----------------------------------------------------------------------------

_ISO8601_UTC_PATTERN: re.Pattern[str] = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)$"
)
_SHA256_HEX_PATTERN: re.Pattern[str] = re.compile(r"^[a-f0-9]{64}$")


def validate_iso8601_utc(timestamp_str: Any) -> str:
    """
    Validate that timestamp is a valid ISO-8601 string with explicit UTC timezone (Z or +00:00).
    Fails closed on naive timestamps or non-UTC timezones.
    """
    if not isinstance(timestamp_str, str):
        raise InvalidDecisionTimestampError(
            f"Decision timestamp must be a string, got {type(timestamp_str).__name__}: {timestamp_str!r}"
        )
    ts = timestamp_str.strip()
    if not _ISO8601_UTC_PATTERN.match(ts):
        raise InvalidDecisionTimestampError(
            f"Decision timestamp must be an explicit UTC ISO-8601 string (e.g. '2026-08-14T20:55:00Z'), got: {ts!r}"
        )
    # Canonicalize "+00:00" to "Z" and space separator to "T"
    normalized = ts.replace(" ", "T")
    if normalized.endswith("+00:00"):
        normalized = normalized[:-6] + "Z"
    return normalized


def validate_snapshot_id(snapshot_id: Any) -> str:
    """
    Validate that snapshot_id is a canonical 64-character lowercase hex SHA256 digest.
    """
    if not isinstance(snapshot_id, str):
        raise InvalidSnapshotIdError(
            f"source_snapshot_id must be a string, got {type(snapshot_id).__name__}: {snapshot_id!r}"
        )
    sid = snapshot_id.strip().lower()
    if not _SHA256_HEX_PATTERN.match(sid):
        raise InvalidSnapshotIdError(
            f"source_snapshot_id must be a 64-character lowercase hex SHA256 string, got: {sid!r}"
        )
    return sid


def compute_logical_observation_id(
    schema_version: str,
    canonical_instrument: str,
    decision_time_utc: str,
    feature_columns_sha256: str,
    model_sha256: str,
) -> str:
    """
    Compute deterministic logical observation identity.
    Represents the exact logical market decision point and model/feature authorities.
    """
    content = f"{schema_version}:{canonical_instrument}:{decision_time_utc}:{feature_columns_sha256}:{model_sha256}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def compute_semantic_record_fingerprint(
    logical_observation_id: str,
    source_snapshot_id: str,
    source_provenance: str,
    probability_short: float,
    probability_no_trade: float,
    probability_long: float,
    predicted_class: int,
    winning_probability: float,
    feature_count: int,
    feature_columns_sha256: str,
    model_sha256: str,
) -> str:
    """
    Compute canonical fingerprint of immutable observation content.
    Excludes observed_at_utc so an exact retry remains idempotent.
    """
    payload = {
        "logical_observation_id": logical_observation_id,
        "source_snapshot_id": source_snapshot_id,
        "source_provenance": source_provenance,
        "probability_short": f"{probability_short:.12f}",
        "probability_no_trade": f"{probability_no_trade:.12f}",
        "probability_long": f"{probability_long:.12f}",
        "predicted_class": int(predicted_class),
        "winning_probability": f"{winning_probability:.12f}",
        "feature_count": int(feature_count),
        "feature_columns_sha256": feature_columns_sha256,
        "model_sha256": model_sha256,
    }
    dumped = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


# -----------------------------------------------------------------------------
# Observation Record Dataclass
# -----------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class FrozenC04ObservationRecord:
    """
    Typed, immutable record for a single read-only forward shadow observation.
    """
    logical_observation_id: str
    semantic_record_fingerprint: str
    observed_at_utc: str
    decision_time_utc: str
    canonical_instrument: str
    broker_symbol: str
    feature_count: int
    feature_columns_sha256: str
    model_sha256: str
    model_class: str
    class_order: tuple[int, ...]
    probability_short: float
    probability_no_trade: float
    probability_long: float
    predicted_class: int
    predicted_label: str
    winning_probability: float
    source_snapshot_id: str
    source_provenance: str
    feature_generation_status: str
    inference_status: str
    observation_status: str
    is_true_forward_eligible: bool
    live_authorized: bool = False
    execution_authorized: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert record to JSON-serializable dictionary."""
        return {
            "schema_version": OBSERVER_SCHEMA_VERSION,
            "logical_observation_id": self.logical_observation_id,
            "semantic_record_fingerprint": self.semantic_record_fingerprint,
            "observed_at_utc": self.observed_at_utc,
            "decision_time_utc": self.decision_time_utc,
            "canonical_instrument": self.canonical_instrument,
            "broker_symbol": self.broker_symbol,
            "feature_count": self.feature_count,
            "feature_columns_sha256": self.feature_columns_sha256,
            "model_sha256": self.model_sha256,
            "model_class": self.model_class,
            "class_order": list(self.class_order),
            "probability_short": self.probability_short,
            "probability_no_trade": self.probability_no_trade,
            "probability_long": self.probability_long,
            "predicted_class": self.predicted_class,
            "predicted_label": self.predicted_label,
            "winning_probability": self.winning_probability,
            "source_snapshot_id": self.source_snapshot_id,
            "source_provenance": self.source_provenance,
            "feature_generation_status": self.feature_generation_status,
            "inference_status": self.inference_status,
            "observation_status": self.observation_status,
            "is_true_forward_eligible": self.is_true_forward_eligible,
            "live_authorized": self.live_authorized,
            "execution_authorized": self.execution_authorized,
        }

    def to_json(self) -> str:
        """Serialize record to compact JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> FrozenC04ObservationRecord:
        """Construct immutable record from dictionary with fail-closed validation."""
        required_keys = {
            "schema_version",
            "logical_observation_id",
            "semantic_record_fingerprint",
            "observed_at_utc",
            "decision_time_utc",
            "canonical_instrument",
            "broker_symbol",
            "feature_count",
            "feature_columns_sha256",
            "model_sha256",
            "model_class",
            "class_order",
            "probability_short",
            "probability_no_trade",
            "probability_long",
            "predicted_class",
            "predicted_label",
            "winning_probability",
            "source_snapshot_id",
            "source_provenance",
            "feature_generation_status",
            "inference_status",
            "observation_status",
            "is_true_forward_eligible",
            "live_authorized",
            "execution_authorized",
        }
        missing = required_keys - set(d.keys())
        if missing:
            raise CorruptedLedgerError(f"Observation record missing required keys: {sorted(missing)}")

        if d.get("schema_version") != OBSERVER_SCHEMA_VERSION:
            raise CorruptedLedgerError(
                f"Unsupported schema version: {d.get('schema_version')} (expected {OBSERVER_SCHEMA_VERSION})"
            )

        # Invariant checks: execution is NEVER authorized
        if d.get("live_authorized") is not False:
            raise FrozenC04ObservationError("Corrupted record violation: live_authorized must be False")
        if d.get("execution_authorized") is not False:
            raise FrozenC04ObservationError("Corrupted record violation: execution_authorized must be False")

        return cls(
            logical_observation_id=str(d["logical_observation_id"]),
            semantic_record_fingerprint=str(d["semantic_record_fingerprint"]),
            observed_at_utc=str(d["observed_at_utc"]),
            decision_time_utc=str(d["decision_time_utc"]),
            canonical_instrument=str(d["canonical_instrument"]),
            broker_symbol=str(d["broker_symbol"]),
            feature_count=int(d["feature_count"]),
            feature_columns_sha256=str(d["feature_columns_sha256"]),
            model_sha256=str(d["model_sha256"]),
            model_class=str(d["model_class"]),
            class_order=tuple(int(x) for x in d["class_order"]),
            probability_short=float(d["probability_short"]),
            probability_no_trade=float(d["probability_no_trade"]),
            probability_long=float(d["probability_long"]),
            predicted_class=int(d["predicted_class"]),
            predicted_label=str(d["predicted_label"]),
            winning_probability=float(d["winning_probability"]),
            source_snapshot_id=str(d["source_snapshot_id"]),
            source_provenance=str(d["source_provenance"]),
            feature_generation_status=str(d["feature_generation_status"]),
            inference_status=str(d["inference_status"]),
            observation_status=str(d["observation_status"]),
            is_true_forward_eligible=bool(d["is_true_forward_eligible"]),
            live_authorized=False,
            execution_authorized=False,
        )


@dataclasses.dataclass(frozen=True)
class AppendResult:
    """Result of attempting to append an observation to the ledger."""
    record: FrozenC04ObservationRecord
    is_duplicate: bool
    appended: bool
    message: str


# -----------------------------------------------------------------------------
# Locked Append-Only Ledger with Fail-Closed Corruption Detection
# -----------------------------------------------------------------------------

@contextlib.contextmanager
def _file_lock(fd: Any) -> Generator[None, None, None]:
    """Platform-appropriate file locking context manager."""
    if sys.platform == "win32":
        import msvcrt
        # Lock 1 byte at position 0
        fd.seek(0, os.SEEK_SET)
        msvcrt.locking(fd.fileno(), msvcrt.LK_LOCK, 1)
        try:
            yield
        finally:
            fd.seek(0, os.SEEK_SET)
            msvcrt.locking(fd.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(fd.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fd.fileno(), fcntl.LOCK_UN)


class FrozenC04ObservationLedger:
    """
    Append-only observation ledger using locked durable append with fail-closed corruption detection.
    
    Guarantees:
    - Writes records one JSON per line to a JSONL file.
    - File locking during append to prevent multi-process interleaving.
    - Immediate flush and fsync after append.
    - Deterministic deduplication:
        - Same logical_observation_id + same semantic_record_fingerprint = duplicate / idempotent.
        - Same logical_observation_id + different semantic_record_fingerprint = ConflictingObservationError.
    - Fail-closed corruption detection: any unparseable or truncated line raises CorruptedLedgerError.
    """

    def __init__(
        self,
        ledger_path: Path | str,
        duplicate_handling: DuplicateHandling = DuplicateHandling.FAIL_CLOSED,
    ) -> None:
        self._path = Path(ledger_path).resolve()
        self._duplicate_handling = duplicate_handling
        self._index: dict[str, str] = {}  # logical_observation_id -> semantic_record_fingerprint

        # Initialize or index existing ledger
        if self._path.exists():
            self._rebuild_index_and_verify()
        else:
            self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    def _rebuild_index_and_verify(self) -> None:
        """Scan existing ledger, index all records, and fail-closed on any corruption."""
        self._index.clear()
        if not self._path.is_file():
            return

        with open(self._path, "r", encoding="utf-8") as f:
            for line_no, raw_line in enumerate(f, start=1):
                line = raw_line.strip()
                if not line:
                    continue  # Ignore empty lines
                try:
                    data = json.loads(line)
                    record = FrozenC04ObservationRecord.from_dict(data)
                except Exception as exc:
                    raise CorruptedLedgerError(
                        f"Ledger file {self._path} is corrupted at line {line_no}: {exc}"
                    ) from exc

                logical_id = record.logical_observation_id
                semantic_fp = record.semantic_record_fingerprint

                if logical_id in self._index:
                    existing_fp = self._index[logical_id]
                    if existing_fp != semantic_fp:
                        raise ConflictingObservationError(
                            f"Ledger file {self._path} contains conflicting records for logical ID {logical_id}"
                        )
                self._index[logical_id] = semantic_fp

    def count(self) -> int:
        """Return total number of unique logical observations in the ledger."""
        return len(self._index)

    def append(self, record: FrozenC04ObservationRecord) -> AppendResult:
        """
        Append a single observation record to the ledger.
        
        Args:
            record: FrozenC04ObservationRecord to append.
            
        Returns:
            AppendResult indicating whether appended or duplicate.
            
        Raises:
            ConflictingObservationError: If logical ID exists with different semantic content.
            DuplicateObservationError: If exact duplicate exists and FAIL_CLOSED is set.
            CorruptedLedgerError: On write failure or file inconsistency.
        """
        logical_id = record.logical_observation_id
        semantic_fp = record.semantic_record_fingerprint

        # Check existing index
        if logical_id in self._index:
            existing_fp = self._index[logical_id]
            if existing_fp != semantic_fp:
                raise ConflictingObservationError(
                    f"Conflicting observation for logical ID {logical_id}! "
                    f"Existing semantic fingerprint {existing_fp}, new {semantic_fp}"
                )
            if self._duplicate_handling == DuplicateHandling.FAIL_CLOSED:
                raise DuplicateObservationError(
                    f"Duplicate observation rejected (logical ID: {logical_id})"
                )
            return AppendResult(
                record=record,
                is_duplicate=True,
                appended=False,
                message=f"Idempotent duplicate ignored: {logical_id}",
            )

        # Locked append
        line_to_write = record.to_json() + "\n"
        try:
            with open(self._path, "a+", encoding="utf-8") as f:
                with _file_lock(f):
                    f.seek(0, os.SEEK_END)
                    f.write(line_to_write)
                    f.flush()
                    os.fsync(f.fileno())
        except Exception as exc:
            raise CorruptedLedgerError(f"Failed to append record to ledger {self._path}: {exc}") from exc

        # Update in-memory index
        self._index[logical_id] = semantic_fp

        return AppendResult(
            record=record,
            is_duplicate=False,
            appended=True,
            message=f"Observation recorded: {logical_id}",
        )

    def read_all(self) -> list[FrozenC04ObservationRecord]:
        """Read all observations from ledger in order of storage."""
        records: list[FrozenC04ObservationRecord] = []
        if not self._path.exists():
            return records

        with open(self._path, "r", encoding="utf-8") as f:
            for line_no, raw_line in enumerate(f, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    record = FrozenC04ObservationRecord.from_dict(data)
                    records.append(record)
                except Exception as exc:
                    raise CorruptedLedgerError(
                        f"Ledger {self._path} corrupted at line {line_no}: {exc}"
                    ) from exc
        return records

    def validate_integrity(self) -> bool:
        """Verify entire ledger consistency, record schemas, and conflict absence."""
        self._rebuild_index_and_verify()
        return True


# -----------------------------------------------------------------------------
# Core Shadow Observer
# -----------------------------------------------------------------------------

class FrozenC04ShadowObserver:
    """
    Pure shadow observation consumer (Gate 15A).
    
    Responsibilities:
    - Consumes validated Gate 13 features (Series or DataFrame).
    - Executes offline inference via Gate 14 FrozenC04InferenceAdapter.
    - Validates provenance, snapshot ID, and decision timestamp.
    - Constructs immutable FrozenC04ObservationRecord.
    - Enforces fail-closed safety invariants:
        - TRUE_FORWARD_OBSERVATION fails closed (no live read authority in Gate 15A).
        - live_authorized = False, execution_authorized = False.
        - Outcome horizon contract is strictly marked BLOCKED_NOT_PREDEFINED.
    """

    def __init__(
        self,
        inference_adapter: FrozenC04InferenceAdapter | None = None,
        canonical_instrument: str = "XAUUSD",
        broker_symbol: str = "XAUUSDm",
    ) -> None:
        self._adapter = inference_adapter or FrozenC04InferenceAdapter()
        self._canonical_instrument = canonical_instrument
        self._broker_symbol = broker_symbol

    @property
    def inference_adapter(self) -> FrozenC04InferenceAdapter:
        return self._adapter

    @property
    def canonical_instrument(self) -> str:
        return self._canonical_instrument

    @property
    def broker_symbol(self) -> str:
        return self._broker_symbol

    def observe_single(
        self,
        feature_row: pd.Series | pd.DataFrame | np.ndarray,
        decision_time_utc: str,
        source_snapshot_id: str,
        source_provenance: SourceProvenance = SourceProvenance.HISTORICAL_ENGINEERING,
        observed_at_utc: str | None = None,
    ) -> FrozenC04ObservationRecord:
        """
        Create a single typed immutable observation record.
        
        Args:
            feature_row: Series, 1-row DataFrame, or (331,) array of validated Gate 13 features.
            decision_time_utc: ISO-8601 UTC decision timestamp (e.g. '2026-08-14T20:55:00Z').
            source_snapshot_id: 64-character hex SHA256 of the market snapshot source.
            source_provenance: SourceProvenance enum value.
            observed_at_utc: Optional override for recorded timestamp (for testing).
        """
        # 1. Enforce provenance authority: Gate 15A has NO live acquisition authority
        if source_provenance == SourceProvenance.TRUE_FORWARD_OBSERVATION:
            raise TrueForwardAcquisitionNotAuthorizedError(
                "Gate 15A has no approved live-read acquisition authority; "
                "TRUE_FORWARD_OBSERVATION is strictly not authorized in Gate 15A."
            )

        # 2. Validate timestamps and snapshot ID
        norm_decision_time = validate_iso8601_utc(decision_time_utc)
        norm_snapshot_id = validate_snapshot_id(source_snapshot_id)

        if observed_at_utc is not None:
            norm_observed_at = validate_iso8601_utc(observed_at_utc)
        else:
            now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
            norm_observed_at = validate_iso8601_utc(now_utc)

        # 3. Execute Gate 14 inference
        inf_row = self._adapter.infer_single(feature_row, decision_time=norm_decision_time)

        # 4. Compute deterministic identities
        logical_id = compute_logical_observation_id(
            schema_version=OBSERVER_SCHEMA_VERSION,
            canonical_instrument=self._canonical_instrument,
            decision_time_utc=norm_decision_time,
            feature_columns_sha256=EXPECTED_FEATURE_COLUMNS_SHA256,
            model_sha256=FROZEN_MODEL_SHA256,
        )

        semantic_fp = compute_semantic_record_fingerprint(
            logical_observation_id=logical_id,
            source_snapshot_id=norm_snapshot_id,
            source_provenance=source_provenance.value,
            probability_short=inf_row.probability_short,
            probability_no_trade=inf_row.probability_no_trade,
            probability_long=inf_row.probability_long,
            predicted_class=inf_row.predicted_class,
            winning_probability=inf_row.winning_probability,
            feature_count=EXPECTED_FEATURE_COUNT,
            feature_columns_sha256=EXPECTED_FEATURE_COLUMNS_SHA256,
            model_sha256=FROZEN_MODEL_SHA256,
        )

        # 5. Determine true forward eligibility (strictly False in Gate 15A)
        is_true_forward = False

        # 6. Construct immutable record
        return FrozenC04ObservationRecord(
            logical_observation_id=logical_id,
            semantic_record_fingerprint=semantic_fp,
            observed_at_utc=norm_observed_at,
            decision_time_utc=norm_decision_time,
            canonical_instrument=self._canonical_instrument,
            broker_symbol=self._broker_symbol,
            feature_count=EXPECTED_FEATURE_COUNT,
            feature_columns_sha256=EXPECTED_FEATURE_COLUMNS_SHA256,
            model_sha256=FROZEN_MODEL_SHA256,
            model_class=EXPECTED_MODEL_CLASS_NAME,
            class_order=FROZEN_MODEL_CLASSES,
            probability_short=inf_row.probability_short,
            probability_no_trade=inf_row.probability_no_trade,
            probability_long=inf_row.probability_long,
            predicted_class=inf_row.predicted_class,
            predicted_label=inf_row.predicted_label,
            winning_probability=inf_row.winning_probability,
            source_snapshot_id=norm_snapshot_id,
            source_provenance=source_provenance.value,
            feature_generation_status="VALIDATED_GATE_13",
            inference_status="SUCCESS_GATE_14",
            observation_status="RECORDED",
            is_true_forward_eligible=is_true_forward,
            live_authorized=False,
            execution_authorized=False,
        )

    def evaluate_outcome(self, *args: Any, **kwargs: Any) -> Any:
        """
        Outcome evaluation hook. In Gate 15A, this is strictly BLOCKED_NOT_PREDEFINED.
        """
        raise OutcomeContractBlockedError(
            "Gate 15A outcome evaluation contract is BLOCKED_NOT_PREDEFINED. "
            "Forward outcome evaluation must not be fabricated post-hoc."
        )


# -----------------------------------------------------------------------------
# Optional Observation Coordinator (Decoupled Snapshot -> Feature -> Observer)
# -----------------------------------------------------------------------------

class FrozenC04ShadowObservationCoordinator:
    """
    Read-only coordination pipeline chaining:
      Raw Multi-Timeframe Snapshot
        -> Gate 13 PortableFeaturePipeline
        -> Gate 14 FrozenC04InferenceAdapter
        -> FrozenC04ShadowObserver
        -> FrozenC04ObservationLedger
    """

    def __init__(
        self,
        observer: FrozenC04ShadowObserver | None = None,
        ledger: FrozenC04ObservationLedger | None = None,
    ) -> None:
        self._observer = observer or FrozenC04ShadowObserver()
        self._ledger = ledger
        # Lazy import of pipeline to maintain loose coupling
        pipeline_mod = importlib.import_module("02_AI.Features.portable_feature_pipeline")
        self._pipeline_cls = pipeline_mod.PortableFeaturePipeline

    @property
    def observer(self) -> FrozenC04ShadowObserver:
        return self._observer

    @property
    def ledger(self) -> FrozenC04ObservationLedger | None:
        return self._ledger

    def process_features_and_record(
        self,
        features: pd.DataFrame | pd.Series,
        decision_times: Sequence[str] | str,
        source_snapshot_id: str,
        source_provenance: SourceProvenance = SourceProvenance.HISTORICAL_ENGINEERING,
    ) -> list[FrozenC04ObservationRecord]:
        """
        Record observations directly from validated Gate 13 features.
        """
        if isinstance(features, pd.Series):
            dt = decision_times if isinstance(decision_times, str) else decision_times[0]
            rec = self._observer.observe_single(
                feature_row=features,
                decision_time_utc=dt,
                source_snapshot_id=source_snapshot_id,
                source_provenance=source_provenance,
            )
            if self._ledger is not None:
                self._ledger.append(rec)
            return [rec]

        # Multi-row DataFrame
        d_times = [decision_times] if isinstance(decision_times, str) else list(decision_times)
        if len(d_times) != len(features):
            raise FrozenC04ObservationError(
                f"Mismatch between feature rows ({len(features)}) and decision times ({len(d_times)})"
            )

        records: list[FrozenC04ObservationRecord] = []
        for idx in range(len(features)):
            row = features.iloc[idx] if hasattr(features, "iloc") else features[idx]
            dt = d_times[idx]
            rec = self._observer.observe_single(
                feature_row=row,
                decision_time_utc=dt,
                source_snapshot_id=source_snapshot_id,
                source_provenance=source_provenance,
            )
            if self._ledger is not None:
                self._ledger.append(rec)
            records.append(rec)
        return records
