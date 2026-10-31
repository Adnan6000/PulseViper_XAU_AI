"""
Forward/demo operational execution evidence journal.

This module makes the existing forward execution evidence path durable and
operational without owning broker execution.

SHADOW / RESEARCH / DEMO ONLY.

Allowed broker reads:
- symbol_info_tick(symbol) for the contemporaneous executable Bid/Ask
- last_error() for diagnostics
- completed-fill history through MT5ReadOnlyCompletedFillAdapter

Explicitly out of scope:
- order_send or any broker write
- order/position modification or cancellation
- implicit MT5 initialize/shutdown ownership
- historical quote reconstruction in the authoritative forward path
- lifecycle/accounting mutation
- trade_ready mutation
- production RiskEngine mutation
- live authorization

Durability model:
- PREPARED is fsync'd before a submission handoff is returned.
- ORDER_BOUND accepts only an externally returned order ticket and the exact
  PREPARED event hash.
- FINALIZED reads already-completed deals and reconciles them against the
  ORIGINAL PREPARED quote through ForwardExecutionEvidenceCapture.
- Events are append-only canonical JSONL with a SHA-256 predecessor chain.
- An atomic head anchor must exactly match the journal tail.
- Any malformed chain, journal/anchor mismatch, stale writer lock, policy drift,
  or half-commit fails closed.

Runtime journal/anchor/lock/temp artifacts are local evidence artifacts and must
never be committed.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import os
import time
import uuid

from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Iterator


_forward_module: Any = importlib.import_module(
    "02_AI.Shadow.forward_execution_evidence_capture"
)
_completed_module: Any = importlib.import_module(
    "02_AI.Shadow.mt5_read_only_completed_fill_adapter"
)

ForwardExecutionEvidenceCapture: Any = (
    _forward_module.ForwardExecutionEvidenceCapture
)
CompletedExecutionFill: Any = _forward_module.CompletedExecutionFill
MT5ReadOnlyCompletedFillAdapter: Any = (
    _completed_module.MT5ReadOnlyCompletedFillAdapter
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FORWARD_DEMO_EVIDENCE_JOURNAL_PATH = (
    PROJECT_ROOT
    / "01_Data"
    / "Processed"
    / "forward_demo_execution_evidence.journal.jsonl"
)


class ForwardDemoEvidenceJournalError(RuntimeError):
    """Base error for the operational forward evidence journal."""


class ForwardDemoEvidenceJournalIntegrityError(
    ForwardDemoEvidenceJournalError
):
    """Persisted evidence cannot be trusted or replayed safely."""


class ForwardDemoEvidenceJournalPersistenceError(
    ForwardDemoEvidenceJournalError
):
    """A durable persistence operation failed or is unsafe to continue."""


@dataclass(frozen=True)
class ForwardDemoEvidenceJournalPolicy:
    max_quote_age_ms: int = 500
    max_quote_future_skew_ms: int = 250
    max_submission_future_skew_ms: int = 250
    numeric_tolerance: float = 1e-10


@dataclass(frozen=True)
class ForwardDemoSubmissionHandoff:
    request_id: str
    symbol: str
    direction: str
    requested_volume: float
    quote_bid: float
    quote_ask: float
    quote_time_msc: int
    captured_at_msc: int
    quote_age_ms: int
    executable_quote_side: float
    request_price: float | None
    requested_deviation_points: int | None
    max_capture_to_submission_ms: int
    journal_sequence: int
    journal_event_hash: str
    live_authorized: bool = False


@dataclass(frozen=True)
class ForwardDemoEvidenceJournalSnapshot:
    journal_id: str
    journal_sequence: int
    journal_event_hash: str
    total_request_count: int
    prepared_only_count: int
    bound_count: int
    finalized_count: int
    evidence_state: Any
    mode: str
    version: str
    live_authorized: bool = False


@dataclass(frozen=True)
class ForwardDemoEvidenceJournalResult:
    valid: bool
    applied: bool
    reason: str
    action: str
    stage: str
    mode: str
    version: str
    live_authorized: bool
    request_id: str
    order_ticket: int
    execution_id: str
    journal_sequence: int
    journal_event_hash: str
    handoff: Any
    forward_transition: Any
    completed_fill_result: Any
    telemetry: Any
    evidence_state: Any
    mt5_error: str


@dataclass(frozen=True)
class _PreparedEvidence:
    request_id: str
    symbol: str
    direction: str
    requested_volume: float
    quote_bid: float
    quote_ask: float
    quote_time_msc: int
    captured_at_msc: int
    quote_age_ms: int
    request_price: float | None
    requested_deviation_points: int | None
    max_quote_age_ms: int
    max_quote_future_skew_ms: int
    max_capture_to_submission_ms: int
    capture_volume_tolerance: float
    capture_numeric_tolerance: float
    prepared_event_hash: str


class ForwardDemoExecutionEvidenceJournal:
    VERSION = "1.0"
    MODE = "SHADOW_FORWARD_DEMO_EXECUTION_EVIDENCE_JOURNAL_ONLY"
    SCHEMA_VERSION = 1
    GENESIS_HASH = "0" * 64

    _EVENT_PREPARED = "PREPARED"
    _EVENT_ORDER_BOUND = "ORDER_BOUND"
    _EVENT_FINALIZED = "FINALIZED"
    _HEX = frozenset("0123456789abcdef")

    def __init__(
        self,
        *,
        journal_path: str | Path | None = None,
        mt5_api: Any | None = None,
        clock_msc: Callable[[], int] | None = None,
        policy: ForwardDemoEvidenceJournalPolicy | None = None,
        evidence_capture: Any | None = None,
        completed_fill_adapter: Any | None = None,
    ) -> None:
        self.path = Path(
            journal_path
            if journal_path is not None
            else DEFAULT_FORWARD_DEMO_EVIDENCE_JOURNAL_PATH
        )
        self.anchor_path = self.path.with_suffix(
            self.path.suffix + ".anchor.json"
        )
        self.lock_path = self.path.with_suffix(
            self.path.suffix + ".lock"
        )
        self.policy = (
            policy
            if policy is not None
            else ForwardDemoEvidenceJournalPolicy()
        )
        self._validate_policy()
        self._mt5_api = mt5_api
        self._clock_msc = (
            clock_msc
            if clock_msc is not None
            else lambda: time.time_ns() // 1_000_000
        )
        self.evidence_capture = (
            evidence_capture
            if evidence_capture is not None
            else ForwardExecutionEvidenceCapture()
        )
        self.completed_fill_adapter = (
            completed_fill_adapter
            if completed_fill_adapter is not None
            else MT5ReadOnlyCompletedFillAdapter(mt5_api=mt5_api)
        )
        (
            self._capture_limit_ms,
            self._capture_volume_tolerance,
            self._capture_numeric_tolerance,
        ) = self._resolve_capture_policy()
        self._journal_id = uuid.uuid4().hex
        self._sequence = 0
        self._head_hash = self.GENESIS_HASH
        self._last_recorded_at_msc = 0
        self._prepared: dict[str, _PreparedEvidence] = {}
        self._finalized_telemetry: dict[str, Any] = {}
        self._state = self.evidence_capture.initial_state()
        self._poisoned = False
        self._assert_safe_runtime_paths()
        if self.lock_path.exists():
            raise ForwardDemoEvidenceJournalPersistenceError(
                f"journal writer lock already exists: {self.lock_path}"
            )
        self._load_and_replay()

    # ---------------------------------------------------------------------
    # Public state
    # ---------------------------------------------------------------------

    @property
    def evidence_state(self) -> Any:
        return self._state

    def telemetry_for(self, request_id: str) -> Any:
        return self._finalized_telemetry.get(str(request_id).strip())

    def snapshot(self) -> ForwardDemoEvidenceJournalSnapshot:
        bound = sum(1 for r in self._state.records if r.status == "BOUND")
        finalized = sum(
            1 for r in self._state.records if r.status == "FINALIZED"
        )
        prepared_only = len(self._prepared) - len(self._state.records)
        if prepared_only < 0:
            raise ForwardDemoEvidenceJournalIntegrityError(
                "evidence state contains a request without PREPARED evidence"
            )
        return ForwardDemoEvidenceJournalSnapshot(
            journal_id=self._journal_id,
            journal_sequence=self._sequence,
            journal_event_hash=self._head_hash,
            total_request_count=len(self._prepared),
            prepared_only_count=prepared_only,
            bound_count=bound,
            finalized_count=finalized,
            evidence_state=self._state,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
        )

    # ---------------------------------------------------------------------
    # Validation helpers
    # ---------------------------------------------------------------------

    def _validate_policy(self) -> None:
        for name in (
            "max_quote_age_ms",
            "max_quote_future_skew_ms",
            "max_submission_future_skew_ms",
        ):
            value = getattr(self.policy, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 0
            ):
                raise ValueError(f"{name} must be a non-negative integer")
        tolerance = self._number(self.policy.numeric_tolerance)
        if not math.isfinite(tolerance) or tolerance <= 0.0:
            raise ValueError("numeric_tolerance must be positive")

    def _resolve_capture_policy(self) -> tuple[int, float, float]:
        policy = getattr(self.evidence_capture, "policy", None)
        max_delay = self._integer(
            getattr(policy, "max_capture_to_submission_ms", None)
        )
        volume_tolerance = self._number(
            getattr(policy, "volume_tolerance", None)
        )
        numeric_tolerance = self._number(
            getattr(policy, "numeric_tolerance", None)
        )
        if max_delay is None or max_delay < 0:
            raise ValueError(
                "evidence_capture must expose a non-negative "
                "policy.max_capture_to_submission_ms"
            )
        if not math.isfinite(volume_tolerance) or volume_tolerance <= 0.0:
            raise ValueError(
                "evidence_capture must expose positive policy.volume_tolerance"
            )
        if not math.isfinite(numeric_tolerance) or numeric_tolerance <= 0.0:
            raise ValueError(
                "evidence_capture must expose positive policy.numeric_tolerance"
            )
        return max_delay, volume_tolerance, numeric_tolerance

    @staticmethod
    def _number(value: Any) -> float:
        try:
            result = float(value)
        except (TypeError, ValueError):
            return math.nan
        return result if math.isfinite(result) else math.nan

    @staticmethod
    def _integer(value: Any) -> int | None:
        if isinstance(value, bool):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _field(value: Any, name: str, default: Any = None) -> Any:
        if value is None:
            return default
        if isinstance(value, dict):
            return value.get(name, default)
        if hasattr(value, name):
            return getattr(value, name)
        dtype = getattr(value, "dtype", None)
        names = getattr(dtype, "names", None)
        if names is not None and name in names:
            try:
                return value[name]
            except Exception:
                return default
        return default

    @staticmethod
    def _direction(value: Any) -> str:
        text = str(value).strip().upper()
        if text in {"LONG", "BUY", "BULLISH"}:
            return "LONG"
        if text in {"SHORT", "SELL", "BEARISH"}:
            return "SHORT"
        return "INVALID"

    @classmethod
    def _valid_hash(cls, value: Any) -> bool:
        text = str(value).strip().lower()
        return len(text) == 64 and all(char in cls._HEX for char in text)

    @staticmethod
    def _canonical_json(value: Any) -> str:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

    @classmethod
    def _event_digest(cls, core: dict[str, Any]) -> str:
        return hashlib.sha256(
            cls._canonical_json(core).encode("utf-8")
        ).hexdigest()

    def _now_msc(self) -> int | None:
        try:
            resolved = self._integer(self._clock_msc())
        except Exception:
            return None
        if resolved is None or resolved <= 0:
            return None
        return resolved

    def _api(self) -> Any:
        if self._mt5_api is not None:
            return self._mt5_api
        return importlib.import_module("MetaTrader5")

    @staticmethod
    def _last_error(api: Any) -> str:
        method = getattr(api, "last_error", None)
        if not callable(method):
            return ""
        try:
            return str(method())
        except Exception as exc:
            return f"last_error_exception={exc}"

    def _record_for_request(self, request_id: str) -> Any:
        for record in self._state.records:
            if record.request_id == request_id:
                return record
        return None

    def _record_for_order(self, order_ticket: int) -> Any:
        for record in self._state.records:
            if record.order_ticket == order_ticket:
                return record
        return None

    def _assert_safe_runtime_paths(self) -> None:
        if len({self.path, self.anchor_path, self.lock_path}) != 3:
            raise ForwardDemoEvidenceJournalIntegrityError(
                "journal, anchor, and lock paths must be distinct"
            )
        for label, path in (
            ("journal", self.path),
            ("anchor", self.anchor_path),
            ("lock", self.lock_path),
        ):
            if path.is_symlink():
                raise ForwardDemoEvidenceJournalIntegrityError(
                    f"{label} path must not be a symbolic link"
                )
            if path.exists() and label != "lock" and not path.is_file():
                raise ForwardDemoEvidenceJournalIntegrityError(
                    f"{label} path exists but is not a regular file"
                )
        parent = self.path.parent
        if parent.exists() and not parent.is_dir():
            raise ForwardDemoEvidenceJournalIntegrityError(
                "journal parent exists but is not a directory"
            )

    def _assert_operational(self) -> None:
        if self._poisoned:
            raise ForwardDemoEvidenceJournalPersistenceError(
                "journal instance is poisoned after a persistence failure; "
                "restart and verify local evidence before continuing"
            )

    # ---------------------------------------------------------------------
    # Results
    # ---------------------------------------------------------------------

    def _result(
        self,
        *,
        valid: bool,
        applied: bool,
        reason: str,
        action: str = "NO_ACTION",
        stage: str = "",
        request_id: str = "",
        order_ticket: int = 0,
        execution_id: str = "",
        handoff: Any = None,
        forward_transition: Any = None,
        completed_fill_result: Any = None,
        telemetry: Any = None,
        mt5_error: str = "",
    ) -> ForwardDemoEvidenceJournalResult:
        return ForwardDemoEvidenceJournalResult(
            valid=valid,
            applied=applied,
            reason=reason,
            action=action,
            stage=stage,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            request_id=request_id,
            order_ticket=order_ticket,
            execution_id=execution_id,
            journal_sequence=self._sequence,
            journal_event_hash=self._head_hash,
            handoff=handoff,
            forward_transition=forward_transition,
            completed_fill_result=completed_fill_result,
            telemetry=telemetry,
            evidence_state=self._state,
            mt5_error=mt5_error,
        )

    def _invalid(self, *, reason: str, **kwargs: Any) -> Any:
        return self._result(valid=False, applied=False, reason=reason, **kwargs)

    # ---------------------------------------------------------------------
    # Durable storage
    # ---------------------------------------------------------------------

    @contextmanager
    def _writer_lock(self) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(
                self.lock_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except FileExistsError as exc:
            raise ForwardDemoEvidenceJournalPersistenceError(
                f"journal writer lock exists: {self.lock_path}"
            ) from exc
        except OSError as exc:
            raise ForwardDemoEvidenceJournalPersistenceError(
                f"cannot create journal writer lock: {exc}"
            ) from exc
        try:
            lock_body = (
                self._canonical_json(
                    {"pid": os.getpid(), "created_at_msc": self._now_msc()}
                )
                + "\n"
            ).encode("utf-8")
            self._write_all(fd, lock_body)
            os.fsync(fd)
            os.close(fd)
            fd = -1
            yield
        finally:
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass
            try:
                self.lock_path.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass

    @staticmethod
    def _write_all(fd: int, data: bytes) -> None:
        offset = 0
        while offset < len(data):
            written = os.write(fd, data[offset:])
            if written <= 0:
                raise OSError("short write while persisting evidence")
            offset += written

    @staticmethod
    def _fsync_parent(path: Path) -> None:
        flags = getattr(os, "O_DIRECTORY", 0)
        try:
            fd = os.open(path.parent, os.O_RDONLY | flags)
        except OSError:
            return
        try:
            os.fsync(fd)
        except OSError:
            pass
        finally:
            try:
                os.close(fd)
            except OSError:
                pass

    def _anchor_document(
        self, *, journal_id: str, sequence: int, event_hash: str
    ) -> dict[str, Any]:
        return {
            "schema_version": self.SCHEMA_VERSION,
            "mode": self.MODE,
            "journal_id": journal_id,
            "sequence": sequence,
            "event_hash": event_hash,
        }

    def _write_anchor_atomic(
        self, *, journal_id: str, sequence: int, event_hash: str
    ) -> None:
        self.anchor_path.parent.mkdir(parents=True, exist_ok=True)
        body = (
            self._canonical_json(
                self._anchor_document(
                    journal_id=journal_id,
                    sequence=sequence,
                    event_hash=event_hash,
                )
            )
            + "\n"
        ).encode("utf-8")
        temp = self.anchor_path.parent / (
            f".{self.anchor_path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
        )
        fd: int | None = None
        try:
            fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            self._write_all(fd, body)
            os.fsync(fd)
            os.close(fd)
            fd = None
            os.replace(temp, self.anchor_path)
            self._fsync_parent(self.anchor_path)
        except Exception:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            try:
                temp.unlink()
            except OSError:
                pass
            raise

    def _read_anchor(self) -> dict[str, Any]:
        try:
            value = json.loads(self.anchor_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ForwardDemoEvidenceJournalIntegrityError(
                "journal anchor is unreadable or invalid JSON"
            ) from exc
        expected = {
            "schema_version",
            "mode",
            "journal_id",
            "sequence",
            "event_hash",
        }
        if not isinstance(value, dict) or set(value) != expected:
            raise ForwardDemoEvidenceJournalIntegrityError(
                "journal anchor schema mismatch"
            )
        sequence = self._integer(value["sequence"])
        journal_id = str(value["journal_id"]).strip()
        event_hash = str(value["event_hash"]).strip().lower()
        if (
            value["schema_version"] != self.SCHEMA_VERSION
            or value["mode"] != self.MODE
            or not journal_id
            or sequence is None
            or sequence <= 0
            or not self._valid_hash(event_hash)
        ):
            raise ForwardDemoEvidenceJournalIntegrityError(
                "journal anchor fields are invalid"
            )
        return {
            "schema_version": self.SCHEMA_VERSION,
            "mode": self.MODE,
            "journal_id": journal_id,
            "sequence": sequence,
            "event_hash": event_hash,
        }

    def _read_validated_events(
        self,
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        journal_exists = self.path.exists()
        anchor_exists = self.anchor_path.exists()
        if not journal_exists and not anchor_exists:
            return [], None
        if journal_exists != anchor_exists:
            raise ForwardDemoEvidenceJournalIntegrityError(
                "journal/anchor presence mismatch; possible half commit"
            )
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise ForwardDemoEvidenceJournalIntegrityError(
                f"cannot read evidence journal: {exc}"
            ) from exc
        if not lines:
            raise ForwardDemoEvidenceJournalIntegrityError(
                "journal exists but contains no events"
            )
        expected_keys = {
            "schema_version",
            "mode",
            "journal_id",
            "sequence",
            "event_type",
            "recorded_at_msc",
            "prev_hash",
            "payload",
            "event_hash",
        }
        events: list[dict[str, Any]] = []
        previous_hash = self.GENESIS_HASH
        previous_recorded_at_msc = 0
        expected_sequence = 1
        journal_id = ""
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                raise ForwardDemoEvidenceJournalIntegrityError(
                    f"blank journal line at {line_number}"
                )
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ForwardDemoEvidenceJournalIntegrityError(
                    f"invalid JSON on journal line {line_number}"
                ) from exc
            if not isinstance(event, dict) or set(event) != expected_keys:
                raise ForwardDemoEvidenceJournalIntegrityError(
                    f"journal schema mismatch on line {line_number}"
                )
            sequence = self._integer(event["sequence"])
            recorded = self._integer(event["recorded_at_msc"])
            current_id = str(event["journal_id"]).strip()
            event_type = str(event["event_type"]).strip()
            prev_hash = str(event["prev_hash"]).strip().lower()
            event_hash = str(event["event_hash"]).strip().lower()
            if (
                event["schema_version"] != self.SCHEMA_VERSION
                or event["mode"] != self.MODE
                or sequence != expected_sequence
                or recorded is None
                or recorded <= 0
                or not current_id
                or event_type
                not in {
                    self._EVENT_PREPARED,
                    self._EVENT_ORDER_BOUND,
                    self._EVENT_FINALIZED,
                }
                or not isinstance(event["payload"], dict)
                or not self._valid_hash(prev_hash)
                or not self._valid_hash(event_hash)
            ):
                raise ForwardDemoEvidenceJournalIntegrityError(
                    f"invalid journal fields on line {line_number}"
                )
            if recorded < previous_recorded_at_msc:
                raise ForwardDemoEvidenceJournalIntegrityError(
                    f"journal timestamp moved backward on line {line_number}"
                )
            if not journal_id:
                journal_id = current_id
            elif current_id != journal_id:
                raise ForwardDemoEvidenceJournalIntegrityError(
                    f"journal id changed on line {line_number}"
                )
            if prev_hash != previous_hash:
                raise ForwardDemoEvidenceJournalIntegrityError(
                    f"hash predecessor mismatch on line {line_number}"
                )
            core = {key: event[key] for key in event if key != "event_hash"}
            if self._event_digest(core) != event_hash:
                raise ForwardDemoEvidenceJournalIntegrityError(
                    f"event hash mismatch on line {line_number}"
                )
            events.append(event)
            previous_hash = event_hash
            previous_recorded_at_msc = recorded
            expected_sequence += 1
        anchor = self._read_anchor()
        tail = events[-1]
        if (
            anchor["journal_id"] != journal_id
            or anchor["sequence"] != tail["sequence"]
            or anchor["event_hash"] != tail["event_hash"]
        ):
            raise ForwardDemoEvidenceJournalIntegrityError(
                "journal tail does not match atomic head anchor"
            )
        return events, anchor

    def _assert_disk_head_matches_memory(self) -> None:
        events, anchor = self._read_validated_events()
        if not events:
            if self._sequence != 0 or self._head_hash != self.GENESIS_HASH:
                raise ForwardDemoEvidenceJournalPersistenceError(
                    "in-memory journal head is stale"
                )
            return
        assert anchor is not None
        if (
            anchor["journal_id"] != self._journal_id
            or anchor["sequence"] != self._sequence
            or anchor["event_hash"] != self._head_hash
        ):
            raise ForwardDemoEvidenceJournalPersistenceError(
                "persisted journal head changed; concurrent/stale writer fails closed"
            )

    def _append_event(self, event_type: str, payload: dict[str, Any]) -> tuple[int, str]:
        self._assert_operational()
        recorded = self._now_msc()
        if recorded is None:
            raise ForwardDemoEvidenceJournalPersistenceError(
                "cannot obtain a valid persistence timestamp"
            )
        if recorded < self._last_recorded_at_msc:
            raise ForwardDemoEvidenceJournalPersistenceError(
                "persistence clock moved backward; append fails closed"
            )
        try:
            self._canonical_json(payload)
        except (TypeError, ValueError) as exc:
            raise ForwardDemoEvidenceJournalPersistenceError(
                "event payload is not canonical JSON serializable"
            ) from exc
        with self._writer_lock():
            self._assert_disk_head_matches_memory()
            sequence = self._sequence + 1
            core = {
                "schema_version": self.SCHEMA_VERSION,
                "mode": self.MODE,
                "journal_id": self._journal_id,
                "sequence": sequence,
                "event_type": event_type,
                "recorded_at_msc": recorded,
                "prev_hash": self._head_hash,
                "payload": payload,
            }
            event_hash = self._event_digest(core)
            event = dict(core)
            event["event_hash"] = event_hash
            line = (self._canonical_json(event) + "\n").encode("utf-8")
            try:
                fd = os.open(
                    self.path,
                    os.O_WRONLY | os.O_CREAT | os.O_APPEND,
                    0o600,
                )
                try:
                    self._write_all(fd, line)
                    os.fsync(fd)
                finally:
                    os.close(fd)
                self._fsync_parent(self.path)
                self._write_anchor_atomic(
                    journal_id=self._journal_id,
                    sequence=sequence,
                    event_hash=event_hash,
                )
            except Exception as exc:
                self._poisoned = True
                raise ForwardDemoEvidenceJournalPersistenceError(
                    "durable evidence append failed; persisted state may be a "
                    "half commit and this instance is now poisoned"
                ) from exc
        self._sequence = sequence
        self._head_hash = event_hash
        self._last_recorded_at_msc = recorded
        return sequence, event_hash

    # ---------------------------------------------------------------------
    # Replay payload parsing
    # ---------------------------------------------------------------------

    def _prepared_from_payload(
        self, payload: dict[str, Any], event_hash: str
    ) -> _PreparedEvidence:
        expected = {
            "request_id",
            "symbol",
            "direction",
            "requested_volume",
            "quote_bid",
            "quote_ask",
            "quote_time_msc",
            "captured_at_msc",
            "quote_age_ms",
            "request_price",
            "requested_deviation_points",
            "max_quote_age_ms",
            "max_quote_future_skew_ms",
            "max_capture_to_submission_ms",
            "capture_volume_tolerance",
            "capture_numeric_tolerance",
            "live_authorized",
        }
        if set(payload) != expected or payload["live_authorized"] is not False:
            raise ForwardDemoEvidenceJournalIntegrityError(
                "PREPARED payload schema/live boundary mismatch"
            )
        request_id = str(payload["request_id"]).strip()
        symbol = str(payload["symbol"]).strip()
        direction = self._direction(payload["direction"])
        volume = self._number(payload["requested_volume"])
        bid = self._number(payload["quote_bid"])
        ask = self._number(payload["quote_ask"])
        quote_time = self._integer(payload["quote_time_msc"])
        captured = self._integer(payload["captured_at_msc"])
        quote_age = self._integer(payload["quote_age_ms"])
        max_age = self._integer(payload["max_quote_age_ms"])
        max_future = self._integer(payload["max_quote_future_skew_ms"])
        max_capture = self._integer(payload["max_capture_to_submission_ms"])
        capture_volume_tolerance = self._number(
            payload["capture_volume_tolerance"]
        )
        capture_numeric_tolerance = self._number(
            payload["capture_numeric_tolerance"]
        )
        if (
            not request_id
            or not symbol
            or direction == "INVALID"
            or not math.isfinite(volume)
            or volume <= 0.0
            or not math.isfinite(bid)
            or not math.isfinite(ask)
            or bid <= 0.0
            or ask <= 0.0
            or ask < bid
            or quote_time is None
            or quote_time <= 0
            or captured is None
            or captured <= 0
            or quote_age is None
            or max_age is None
            or max_age < 0
            or max_future is None
            or max_future < 0
            or max_capture is None
            or max_capture < 0
            or not math.isfinite(capture_volume_tolerance)
            or capture_volume_tolerance <= 0.0
            or not math.isfinite(capture_numeric_tolerance)
            or capture_numeric_tolerance <= 0.0
            or quote_age != captured - quote_time
            or quote_age > max_age
            or quote_age < -max_future
        ):
            raise ForwardDemoEvidenceJournalIntegrityError(
                "PREPARED evidence values are invalid"
            )
        if (
            max_capture != self._capture_limit_ms
            or not math.isclose(
                capture_volume_tolerance,
                self._capture_volume_tolerance,
                rel_tol=0.0,
                abs_tol=0.0,
            )
            or not math.isclose(
                capture_numeric_tolerance,
                self._capture_numeric_tolerance,
                rel_tol=0.0,
                abs_tol=0.0,
            )
        ):
            raise ForwardDemoEvidenceJournalIntegrityError(
                "forward capture policy drift detected during recovery"
            )
        request_price: float | None = None
        if payload["request_price"] is not None:
            request_price = self._number(payload["request_price"])
            if not math.isfinite(request_price) or request_price <= 0.0:
                raise ForwardDemoEvidenceJournalIntegrityError(
                    "PREPARED request_price is invalid"
                )
        deviation: int | None = None
        if payload["requested_deviation_points"] is not None:
            deviation = self._integer(payload["requested_deviation_points"])
            if deviation is None or deviation < 0:
                raise ForwardDemoEvidenceJournalIntegrityError(
                    "PREPARED requested_deviation_points is invalid"
                )
        return _PreparedEvidence(
            request_id=request_id,
            symbol=symbol,
            direction=direction,
            requested_volume=volume,
            quote_bid=bid,
            quote_ask=ask,
            quote_time_msc=quote_time,
            captured_at_msc=captured,
            quote_age_ms=quote_age,
            request_price=request_price,
            requested_deviation_points=deviation,
            max_quote_age_ms=max_age,
            max_quote_future_skew_ms=max_future,
            max_capture_to_submission_ms=max_capture,
            capture_volume_tolerance=capture_volume_tolerance,
            capture_numeric_tolerance=capture_numeric_tolerance,
            prepared_event_hash=event_hash,
        )

    def _bound_payload_values(
        self, payload: dict[str, Any]
    ) -> tuple[str, str, int, int]:
        expected = {
            "request_id",
            "prepared_event_hash",
            "submitted_at_msc",
            "order_ticket",
            "submission_latency_ms",
            "live_authorized",
        }
        if set(payload) != expected or payload["live_authorized"] is not False:
            raise ForwardDemoEvidenceJournalIntegrityError(
                "ORDER_BOUND payload schema/live boundary mismatch"
            )
        request_id = str(payload["request_id"]).strip()
        prepared_hash = str(payload["prepared_event_hash"]).strip().lower()
        submitted = self._integer(payload["submitted_at_msc"])
        order = self._integer(payload["order_ticket"])
        latency = self._integer(payload["submission_latency_ms"])
        if (
            not request_id
            or not self._valid_hash(prepared_hash)
            or submitted is None
            or submitted <= 0
            or order is None
            or order <= 0
            or latency is None
            or latency < 0
        ):
            raise ForwardDemoEvidenceJournalIntegrityError(
                "ORDER_BOUND values are invalid"
            )
        return request_id, prepared_hash, submitted, order

    def _fill_from_finalized_payload(
        self, payload: dict[str, Any]
    ) -> tuple[str, Any, dict[str, Any], dict[str, Any]]:
        expected = {
            "request_id",
            "completed_fill",
            "fill_audit",
            "telemetry",
            "live_authorized",
        }
        if set(payload) != expected or payload["live_authorized"] is not False:
            raise ForwardDemoEvidenceJournalIntegrityError(
                "FINALIZED payload schema/live boundary mismatch"
            )
        request_id = str(payload["request_id"]).strip()
        fill_doc = payload["completed_fill"]
        audit = payload["fill_audit"]
        telemetry_doc = payload["telemetry"]
        if (
            not request_id
            or not isinstance(fill_doc, dict)
            or not isinstance(audit, dict)
            or not isinstance(telemetry_doc, dict)
        ):
            raise ForwardDemoEvidenceJournalIntegrityError(
                "FINALIZED nested documents are invalid"
            )
        fill_expected = {
            "order_ticket",
            "execution_id",
            "symbol",
            "direction",
            "filled_volume",
            "fill_price",
            "commission_cost",
            "live_authorized",
        }
        if set(fill_doc) != fill_expected or fill_doc["live_authorized"] is not False:
            raise ForwardDemoEvidenceJournalIntegrityError(
                "FINALIZED completed_fill schema/live boundary mismatch"
            )
        order = self._integer(fill_doc["order_ticket"])
        execution_id = str(fill_doc["execution_id"]).strip()
        symbol = str(fill_doc["symbol"]).strip()
        direction = self._direction(fill_doc["direction"])
        volume = self._number(fill_doc["filled_volume"])
        price = self._number(fill_doc["fill_price"])
        commission = self._number(fill_doc["commission_cost"])
        if (
            order is None
            or order <= 0
            or not execution_id
            or not symbol
            or direction == "INVALID"
            or not math.isfinite(volume)
            or volume <= 0.0
            or not math.isfinite(price)
            or price <= 0.0
            or not math.isfinite(commission)
            or commission < 0.0
        ):
            raise ForwardDemoEvidenceJournalIntegrityError(
                "FINALIZED completed_fill values are invalid"
            )
        fill = CompletedExecutionFill(
            order_ticket=order,
            execution_id=execution_id,
            symbol=symbol,
            direction=direction,
            filled_volume=volume,
            fill_price=price,
            commission_cost=commission,
            live_authorized=False,
        )
        self._validate_fill_audit(audit, fill)
        return request_id, fill, audit, telemetry_doc

    def _validate_fill_audit(self, audit: dict[str, Any], fill: Any) -> None:
        expected = {
            "raw_deal_count",
            "selected_deal_count",
            "deal_tickets",
            "first_deal_time_msc",
            "last_deal_time_msc",
            "raw_commission_sum",
            "raw_fee_sum",
            "normalized_commission_cost",
            "history_invoked",
            "adapter_reason",
            "adapter_mode",
            "adapter_version",
        }
        if set(audit) != expected or audit["history_invoked"] is not True:
            raise ForwardDemoEvidenceJournalIntegrityError(
                "FINALIZED fill_audit schema/history boundary mismatch"
            )
        raw_count = self._integer(audit["raw_deal_count"])
        selected_count = self._integer(audit["selected_deal_count"])
        first_time = self._integer(audit["first_deal_time_msc"])
        last_time = self._integer(audit["last_deal_time_msc"])
        deal_tickets = audit["deal_tickets"]
        raw_commission = self._number(audit["raw_commission_sum"])
        raw_fee = self._number(audit["raw_fee_sum"])
        normalized = self._number(audit["normalized_commission_cost"])
        reason = str(audit["adapter_reason"]).strip()
        mode = str(audit["adapter_mode"]).strip()
        version = str(audit["adapter_version"]).strip()
        if (
            raw_count is None
            or selected_count is None
            or raw_count < selected_count
            or selected_count <= 0
            or not isinstance(deal_tickets, list)
            or len(deal_tickets) != selected_count
            or first_time is None
            or first_time <= 0
            or last_time is None
            or last_time < first_time
            or not math.isfinite(raw_commission)
            or not math.isfinite(raw_fee)
            or not math.isfinite(normalized)
            or normalized < 0.0
            or not reason
            or not mode
            or not version
        ):
            raise ForwardDemoEvidenceJournalIntegrityError(
                "FINALIZED fill_audit values are invalid"
            )
        resolved_tickets: list[int] = []
        for value in deal_tickets:
            ticket = self._integer(value)
            if ticket is None or ticket <= 0:
                raise ForwardDemoEvidenceJournalIntegrityError(
                    "FINALIZED deal ticket is invalid"
                )
            resolved_tickets.append(ticket)
        if len(set(resolved_tickets)) != len(resolved_tickets):
            raise ForwardDemoEvidenceJournalIntegrityError(
                "FINALIZED deal tickets are duplicated"
            )
        if not math.isclose(
            normalized,
            float(fill.commission_cost),
            rel_tol=0.0,
            abs_tol=self.policy.numeric_tolerance,
        ):
            raise ForwardDemoEvidenceJournalIntegrityError(
                "FINALIZED normalized commission does not match completed fill"
            )

    def _telemetry_document(
        self,
        telemetry: Any,
        signed_slippage: float,
    ) -> dict[str, Any]:
        return {
            "execution_id": str(telemetry.execution_id),
            "filled_volume": float(telemetry.filled_volume),
            "fill_price": float(telemetry.fill_price),
            "quote_bid": float(telemetry.quote_bid),
            "quote_ask": float(telemetry.quote_ask),
            "commission_cost": float(telemetry.commission_cost),
            "signed_slippage_price": float(signed_slippage),
            "live_authorized": False,
        }

    def _validate_telemetry_document(
        self,
        persisted: dict[str, Any],
        telemetry: Any,
        signed_slippage: float,
    ) -> None:
        expected = {
            "execution_id",
            "filled_volume",
            "fill_price",
            "quote_bid",
            "quote_ask",
            "commission_cost",
            "signed_slippage_price",
            "live_authorized",
        }
        if set(persisted) != expected or persisted["live_authorized"] is not False:
            raise ForwardDemoEvidenceJournalIntegrityError(
                "FINALIZED telemetry schema/live boundary mismatch"
            )
        computed = self._telemetry_document(
            telemetry,
            signed_slippage,
        )
        if str(persisted["execution_id"]) != computed["execution_id"]:
            raise ForwardDemoEvidenceJournalIntegrityError(
                "FINALIZED telemetry execution id mismatch"
            )
        for name in (
            "filled_volume",
            "fill_price",
            "quote_bid",
            "quote_ask",
            "commission_cost",
            "signed_slippage_price",
        ):
            value = self._number(persisted[name])
            if not math.isfinite(value) or not math.isclose(
                value,
                computed[name],
                rel_tol=0.0,
                abs_tol=self.policy.numeric_tolerance,
            ):
                raise ForwardDemoEvidenceJournalIntegrityError(
                    f"FINALIZED telemetry {name} mismatch"
                )

    # ---------------------------------------------------------------------
    # Replay
    # ---------------------------------------------------------------------

    def _load_and_replay(self) -> None:
        events, anchor = self._read_validated_events()
        if not events:
            return
        assert anchor is not None
        self._journal_id = anchor["journal_id"]
        self._sequence = anchor["sequence"]
        self._head_hash = anchor["event_hash"]
        self._last_recorded_at_msc = int(events[-1]["recorded_at_msc"])
        state = self.evidence_capture.initial_state()
        prepared: dict[str, _PreparedEvidence] = {}
        telemetry_by_request: dict[str, Any] = {}
        bound_orders: set[int] = set()
        execution_ids: set[str] = set()
        for event in events:
            event_type = event["event_type"]
            payload = event["payload"]
            if event_type == self._EVENT_PREPARED:
                item = self._prepared_from_payload(
                    payload,
                    event["event_hash"],
                )
                if item.request_id in prepared:
                    raise ForwardDemoEvidenceJournalIntegrityError(
                        "duplicate PREPARED request id"
                    )
                prepared[item.request_id] = item
                continue

            if event_type == self._EVENT_ORDER_BOUND:
                request_id, prepared_hash, submitted, order = (
                    self._bound_payload_values(payload)
                )
                item = prepared.get(request_id)
                if item is None or item.prepared_event_hash != prepared_hash:
                    raise ForwardDemoEvidenceJournalIntegrityError(
                        "ORDER_BOUND does not link to its PREPARED evidence"
                    )
                if self._record_in_state(state, request_id) is not None:
                    raise ForwardDemoEvidenceJournalIntegrityError(
                        "request was bound more than once"
                    )
                if order in bound_orders:
                    raise ForwardDemoEvidenceJournalIntegrityError(
                        "order ticket was bound more than once"
                    )

                capture = self.evidence_capture.capture_submission(
                    state=state,
                    request_id=item.request_id,
                    symbol=item.symbol,
                    direction=item.direction,
                    requested_volume=item.requested_volume,
                    quote_bid=item.quote_bid,
                    quote_ask=item.quote_ask,
                    quote_time_msc=item.quote_time_msc,
                    captured_at_msc=item.captured_at_msc,
                    submitted_at_msc=submitted,
                    request_price=item.request_price,
                    requested_deviation_points=(
                        item.requested_deviation_points
                    ),
                    live_authorized=False,
                )
                if not capture.valid or not capture.applied:
                    raise ForwardDemoEvidenceJournalIntegrityError(
                        f"cannot replay capture: {capture.reason}"
                    )

                expected_latency = submitted - item.captured_at_msc
                persisted_latency = self._integer(
                    payload["submission_latency_ms"]
                )
                if persisted_latency != expected_latency:
                    raise ForwardDemoEvidenceJournalIntegrityError(
                        "ORDER_BOUND submission latency mismatch"
                    )

                bound = self.evidence_capture.bind_order(
                    state=capture.state_after,
                    request_id=request_id,
                    order_ticket=order,
                    live_authorized=False,
                )
                if not bound.valid or not bound.applied:
                    raise ForwardDemoEvidenceJournalIntegrityError(
                        f"cannot replay order binding: {bound.reason}"
                    )

                state = bound.state_after
                bound_orders.add(order)
                continue

            request_id, fill, _audit, telemetry_doc = (
                self._fill_from_finalized_payload(payload)
            )
            record = self._record_in_state(state, request_id)
            if record is None or record.status != "BOUND":
                raise ForwardDemoEvidenceJournalIntegrityError(
                    "FINALIZED request is not uniquely BOUND"
                )
            if fill.order_ticket != record.order_ticket:
                raise ForwardDemoEvidenceJournalIntegrityError(
                    "FINALIZED fill order does not match bound order"
                )
            if fill.execution_id in execution_ids:
                raise ForwardDemoEvidenceJournalIntegrityError(
                    "FINALIZED execution id is duplicated"
                )

            reconciled = self.evidence_capture.reconcile_completed_fill(
                state=state,
                completed_fill=fill,
            )
            if not reconciled.valid or not reconciled.applied:
                raise ForwardDemoEvidenceJournalIntegrityError(
                    f"cannot replay completed fill: {reconciled.reason}"
                )
            if (
                reconciled.telemetry is None
                or reconciled.signed_slippage_price is None
            ):
                raise ForwardDemoEvidenceJournalIntegrityError(
                    "replayed FINALIZED event produced no telemetry"
                )

            self._validate_telemetry_document(
                telemetry_doc,
                reconciled.telemetry,
                reconciled.signed_slippage_price,
            )
            state = reconciled.state_after
            telemetry_by_request[request_id] = reconciled.telemetry
            execution_ids.add(fill.execution_id)

        self._state = state
        self._prepared = prepared
        self._finalized_telemetry = telemetry_by_request

    @staticmethod
    def _record_in_state(state: Any, request_id: str) -> Any:
        for record in state.records:
            if record.request_id == request_id:
                return record
        return None

    # ---------------------------------------------------------------------
    # Stage 1: capture current executable quote, persist, return handoff
    # ---------------------------------------------------------------------

    def capture_pre_submit(
        self,
        *,
        request_id: str,
        symbol: str,
        direction: str,
        requested_volume: float,
        request_price: float | None = None,
        requested_deviation_points: int | None = None,
        live_authorized: bool = False,
    ) -> ForwardDemoEvidenceJournalResult:
        self._assert_operational()

        request = str(request_id).strip()
        resolved_symbol = str(symbol).strip()
        resolved_direction = self._direction(direction)
        volume = self._number(requested_volume)

        if live_authorized:
            return self._invalid(
                reason="LIVE_AUTHORIZATION_NOT_ALLOWED",
                stage=self._EVENT_PREPARED,
                request_id=request,
            )

        if not request:
            return self._invalid(
                reason="INVALID_REQUEST_ID",
                stage=self._EVENT_PREPARED,
            )

        if request in self._prepared:
            return self._invalid(
                reason="DUPLICATE_REQUEST_ID",
                stage=self._EVENT_PREPARED,
                request_id=request,
            )

        if not resolved_symbol:
            return self._invalid(
                reason="INVALID_SYMBOL",
                stage=self._EVENT_PREPARED,
                request_id=request,
            )

        if resolved_direction == "INVALID":
            return self._invalid(
                reason="INVALID_DIRECTION",
                stage=self._EVENT_PREPARED,
                request_id=request,
            )

        if not math.isfinite(volume) or volume <= 0.0:
            return self._invalid(
                reason="INVALID_REQUESTED_VOLUME",
                stage=self._EVENT_PREPARED,
                request_id=request,
            )

        normalized_request_price: float | None = None

        if request_price is not None:
            normalized_request_price = self._number(request_price)

            if (
                not math.isfinite(normalized_request_price)
                or normalized_request_price <= 0.0
            ):
                return self._invalid(
                    reason="INVALID_REQUEST_PRICE",
                    stage=self._EVENT_PREPARED,
                    request_id=request,
                )

        deviation: int | None = None

        if requested_deviation_points is not None:
            deviation = self._integer(requested_deviation_points)

            if deviation is None or deviation < 0:
                return self._invalid(
                    reason="INVALID_REQUESTED_DEVIATION",
                    stage=self._EVENT_PREPARED,
                    request_id=request,
                )

        try:
            api = self._api()
        except Exception as exc:
            return self._invalid(
                reason="MT5_API_IMPORT_FAILED",
                stage=self._EVENT_PREPARED,
                request_id=request,
                mt5_error=str(exc),
            )

        method = getattr(api, "symbol_info_tick", None)

        if not callable(method):
            return self._invalid(
                reason="MT5_SYMBOL_INFO_TICK_UNAVAILABLE",
                stage=self._EVENT_PREPARED,
                request_id=request,
            )

        try:
            tick = api.symbol_info_tick(resolved_symbol)
        except Exception as exc:
            return self._invalid(
                reason="MT5_CURRENT_QUOTE_READ_EXCEPTION",
                stage=self._EVENT_PREPARED,
                request_id=request,
                mt5_error=str(exc),
            )

        if tick is None:
            return self._invalid(
                reason="MT5_CURRENT_QUOTE_READ_FAILED",
                stage=self._EVENT_PREPARED,
                request_id=request,
                mt5_error=self._last_error(api),
            )

        captured_at = self._now_msc()

        if captured_at is None:
            return self._invalid(
                reason="INVALID_CAPTURE_CLOCK",
                stage=self._EVENT_PREPARED,
                request_id=request,
            )

        bid = self._number(self._field(tick, "bid"))
        ask = self._number(self._field(tick, "ask"))
        quote_time = self._integer(self._field(tick, "time_msc"))

        if (
            not math.isfinite(bid)
            or not math.isfinite(ask)
            or bid <= 0.0
            or ask <= 0.0
            or quote_time is None
            or quote_time <= 0
        ):
            return self._invalid(
                reason="INVALID_CURRENT_EXECUTABLE_QUOTE",
                stage=self._EVENT_PREPARED,
                request_id=request,
            )

        if ask < bid:
            return self._invalid(
                reason="CURRENT_EXECUTABLE_QUOTE_INVERTED",
                stage=self._EVENT_PREPARED,
                request_id=request,
            )

        quote_age = captured_at - quote_time

        if quote_age > self.policy.max_quote_age_ms:
            return self._invalid(
                reason="CURRENT_EXECUTABLE_QUOTE_STALE",
                stage=self._EVENT_PREPARED,
                request_id=request,
            )

        if quote_age < -self.policy.max_quote_future_skew_ms:
            return self._invalid(
                reason="CURRENT_EXECUTABLE_QUOTE_TIME_IN_FUTURE",
                stage=self._EVENT_PREPARED,
                request_id=request,
            )

        payload = {
            "request_id": request,
            "symbol": resolved_symbol,
            "direction": resolved_direction,
            "requested_volume": volume,
            "quote_bid": bid,
            "quote_ask": ask,
            "quote_time_msc": quote_time,
            "captured_at_msc": captured_at,
            "quote_age_ms": quote_age,
            "request_price": normalized_request_price,
            "requested_deviation_points": deviation,
            "max_quote_age_ms": self.policy.max_quote_age_ms,
            "max_quote_future_skew_ms": (
                self.policy.max_quote_future_skew_ms
            ),
            "max_capture_to_submission_ms": self._capture_limit_ms,
            "capture_volume_tolerance": (
                self._capture_volume_tolerance
            ),
            "capture_numeric_tolerance": (
                self._capture_numeric_tolerance
            ),
            "live_authorized": False,
        }

        sequence, event_hash = self._append_event(
            self._EVENT_PREPARED,
            payload,
        )

        prepared = self._prepared_from_payload(
            payload,
            event_hash,
        )
        self._prepared[request] = prepared

        executable = ask if resolved_direction == "LONG" else bid

        handoff = ForwardDemoSubmissionHandoff(
            request_id=request,
            symbol=resolved_symbol,
            direction=resolved_direction,
            requested_volume=volume,
            quote_bid=bid,
            quote_ask=ask,
            quote_time_msc=quote_time,
            captured_at_msc=captured_at,
            quote_age_ms=quote_age,
            executable_quote_side=executable,
            request_price=normalized_request_price,
            requested_deviation_points=deviation,
            max_capture_to_submission_ms=self._capture_limit_ms,
            journal_sequence=sequence,
            journal_event_hash=event_hash,
            live_authorized=False,
        )

        return self._result(
            valid=True,
            applied=True,
            reason="OK_FORWARD_DEMO_PRE_SUBMIT_EVIDENCE_DURABLE",
            action="HANDOFF_TO_EXTERNAL_DEMO_EXECUTION_OWNER",
            stage=self._EVENT_PREPARED,
            request_id=request,
            handoff=handoff,
        )

    # ---------------------------------------------------------------------
    # Stage 2: accept external submission timestamp + returned order ticket
    # ---------------------------------------------------------------------

    def bind_external_order(
        self,
        *,
        request_id: str,
        handoff_event_hash: str,
        submitted_at_msc: int,
        order_ticket: int,
        live_authorized: bool = False,
    ) -> ForwardDemoEvidenceJournalResult:
        self._assert_operational()

        request = str(request_id).strip()

        if live_authorized:
            return self._invalid(
                reason="LIVE_AUTHORIZATION_NOT_ALLOWED",
                stage=self._EVENT_ORDER_BOUND,
                request_id=request,
            )

        prepared = self._prepared.get(request)

        if prepared is None:
            return self._invalid(
                reason="PREPARED_EVIDENCE_NOT_FOUND",
                stage=self._EVENT_ORDER_BOUND,
                request_id=request,
            )

        if self._record_for_request(request) is not None:
            return self._invalid(
                reason="REQUEST_ALREADY_BOUND_OR_FINALIZED",
                stage=self._EVENT_ORDER_BOUND,
                request_id=request,
            )

        supplied_hash = str(handoff_event_hash).strip().lower()

        if (
            not self._valid_hash(supplied_hash)
            or supplied_hash != prepared.prepared_event_hash
        ):
            return self._invalid(
                reason="PREPARED_HANDOFF_HASH_MISMATCH",
                stage=self._EVENT_ORDER_BOUND,
                request_id=request,
            )

        submitted = self._integer(submitted_at_msc)
        order = self._integer(order_ticket)

        if submitted is None or submitted <= 0:
            return self._invalid(
                reason="INVALID_EXTERNAL_SUBMISSION_TIMESTAMP",
                stage=self._EVENT_ORDER_BOUND,
                request_id=request,
            )

        if order is None or order <= 0:
            return self._invalid(
                reason="INVALID_EXTERNAL_ORDER_TICKET",
                stage=self._EVENT_ORDER_BOUND,
                request_id=request,
            )

        if self._record_for_order(order) is not None:
            return self._invalid(
                reason="DUPLICATE_EXTERNAL_ORDER_TICKET",
                stage=self._EVENT_ORDER_BOUND,
                request_id=request,
                order_ticket=order,
            )

        now = self._now_msc()

        if now is None:
            return self._invalid(
                reason="INVALID_BIND_CLOCK",
                stage=self._EVENT_ORDER_BOUND,
                request_id=request,
                order_ticket=order,
            )

        if submitted > now + self.policy.max_submission_future_skew_ms:
            return self._invalid(
                reason="EXTERNAL_SUBMISSION_TIMESTAMP_IN_FUTURE",
                stage=self._EVENT_ORDER_BOUND,
                request_id=request,
                order_ticket=order,
            )

        capture = self.evidence_capture.capture_submission(
            state=self._state,
            request_id=prepared.request_id,
            symbol=prepared.symbol,
            direction=prepared.direction,
            requested_volume=prepared.requested_volume,
            quote_bid=prepared.quote_bid,
            quote_ask=prepared.quote_ask,
            quote_time_msc=prepared.quote_time_msc,
            captured_at_msc=prepared.captured_at_msc,
            submitted_at_msc=submitted,
            request_price=prepared.request_price,
            requested_deviation_points=(
                prepared.requested_deviation_points
            ),
            live_authorized=False,
        )

        if not capture.valid or not capture.applied:
            return self._invalid(
                reason=f"FORWARD_CAPTURE_REJECTED:{capture.reason}",
                stage=self._EVENT_ORDER_BOUND,
                request_id=request,
                order_ticket=order,
                forward_transition=capture,
            )

        bound = self.evidence_capture.bind_order(
            state=capture.state_after,
            request_id=request,
            order_ticket=order,
            live_authorized=False,
        )

        if not bound.valid or not bound.applied:
            return self._invalid(
                reason=f"FORWARD_BIND_REJECTED:{bound.reason}",
                stage=self._EVENT_ORDER_BOUND,
                request_id=request,
                order_ticket=order,
                forward_transition=bound,
            )

        payload = {
            "request_id": request,
            "prepared_event_hash": prepared.prepared_event_hash,
            "submitted_at_msc": submitted,
            "order_ticket": order,
            "submission_latency_ms": (
                submitted - prepared.captured_at_msc
            ),
            "live_authorized": False,
        }

        self._append_event(
            self._EVENT_ORDER_BOUND,
            payload,
        )

        self._state = bound.state_after

        return self._result(
            valid=True,
            applied=True,
            reason="OK_EXTERNAL_DEMO_ORDER_BOUND_TO_DURABLE_EVIDENCE",
            action="WAIT_FOR_COMPLETED_FILL_READ_ONLY",
            stage=self._EVENT_ORDER_BOUND,
            request_id=request,
            order_ticket=order,
            forward_transition=bound,
        )

    # ---------------------------------------------------------------------
    # Stage 3: read completed deals and reconcile to original quote
    # ---------------------------------------------------------------------

    def reconcile_completed_order(
        self,
        *,
        request_id: str,
        execution_id: str | None = None,
        live_authorized: bool = False,
    ) -> ForwardDemoEvidenceJournalResult:
        self._assert_operational()

        request = str(request_id).strip()

        if live_authorized:
            return self._invalid(
                reason="LIVE_AUTHORIZATION_NOT_ALLOWED",
                stage=self._EVENT_FINALIZED,
                request_id=request,
            )

        prepared = self._prepared.get(request)
        record = self._record_for_request(request)

        if prepared is None or record is None:
            return self._invalid(
                reason="BOUND_EVIDENCE_NOT_FOUND",
                stage=self._EVENT_FINALIZED,
                request_id=request,
            )

        if record.status == "FINALIZED":
            return self._invalid(
                reason="ORDER_EVIDENCE_ALREADY_FINALIZED",
                stage=self._EVENT_FINALIZED,
                request_id=request,
                order_ticket=int(record.order_ticket or 0),
            )

        if record.status != "BOUND" or record.order_ticket is None:
            return self._invalid(
                reason="ORDER_EVIDENCE_NOT_BOUND",
                stage=self._EVENT_FINALIZED,
                request_id=request,
            )

        order = int(record.order_ticket)

        result = self.completed_fill_adapter.read_order_fill(
            order_ticket=order,
            expected_symbol=prepared.symbol,
            expected_direction=prepared.direction,
            expected_volume=prepared.requested_volume,
        )

        if (
            not getattr(result, "valid", False)
            or not getattr(result, "normalized", False)
        ):
            return self._invalid(
                reason=(
                    "COMPLETED_FILL_READ_REJECTED:"
                    f"{getattr(result, 'reason', 'UNKNOWN')}"
                ),
                stage=self._EVENT_FINALIZED,
                request_id=request,
                order_ticket=order,
                completed_fill_result=result,
                mt5_error=str(
                    getattr(result, "mt5_error", "")
                ),
            )

        fill = getattr(result, "completed_fill", None)

        if fill is None:
            return self._invalid(
                reason="COMPLETED_FILL_ADAPTER_RETURNED_NO_FILL",
                stage=self._EVENT_FINALIZED,
                request_id=request,
                order_ticket=order,
                completed_fill_result=result,
            )

        if execution_id is not None:
            resolved_execution_id = str(execution_id).strip()

            if not resolved_execution_id:
                return self._invalid(
                    reason="INVALID_EXECUTION_ID_OVERRIDE",
                    stage=self._EVENT_FINALIZED,
                    request_id=request,
                    order_ticket=order,
                    completed_fill_result=result,
                )

            fill = replace(
                fill,
                execution_id=resolved_execution_id,
            )

        reconciled = self.evidence_capture.reconcile_completed_fill(
            state=self._state,
            completed_fill=fill,
        )

        if (
            not reconciled.valid
            or not reconciled.applied
            or reconciled.telemetry is None
        ):
            return self._invalid(
                reason=(
                    "FORWARD_FILL_RECONCILIATION_REJECTED:"
                    f"{reconciled.reason}"
                ),
                stage=self._EVENT_FINALIZED,
                request_id=request,
                order_ticket=order,
                execution_id=str(
                    getattr(fill, "execution_id", "")
                ),
                forward_transition=reconciled,
                completed_fill_result=result,
            )

        first_deal_time = self._integer(
            result.first_deal_time_msc
        )
        last_deal_time = self._integer(
            result.last_deal_time_msc
        )
        finalize_clock = self._now_msc()

        if (
            first_deal_time is None
            or last_deal_time is None
            or finalize_clock is None
        ):
            return self._invalid(
                reason="INVALID_COMPLETED_FILL_TIMESTAMPS",
                stage=self._EVENT_FINALIZED,
                request_id=request,
                order_ticket=order,
                completed_fill_result=result,
            )

        if first_deal_time < (
            int(record.submitted_at_msc)
            - self.policy.max_submission_future_skew_ms
        ):
            return self._invalid(
                reason="COMPLETED_FILL_PRECEDES_SUBMISSION",
                stage=self._EVENT_FINALIZED,
                request_id=request,
                order_ticket=order,
                completed_fill_result=result,
            )

        if last_deal_time > (
            finalize_clock
            + self.policy.max_submission_future_skew_ms
        ):
            return self._invalid(
                reason="COMPLETED_FILL_TIMESTAMP_IN_FUTURE",
                stage=self._EVENT_FINALIZED,
                request_id=request,
                order_ticket=order,
                completed_fill_result=result,
            )

        audit = {
            "raw_deal_count": int(result.raw_deal_count),
            "selected_deal_count": int(
                result.selected_deal_count
            ),
            "deal_tickets": [
                int(value)
                for value in result.deal_tickets
            ],
            "first_deal_time_msc": int(
                result.first_deal_time_msc
            ),
            "last_deal_time_msc": int(
                result.last_deal_time_msc
            ),
            "raw_commission_sum": float(
                result.raw_commission_sum
            ),
            "raw_fee_sum": float(
                result.raw_fee_sum
            ),
            "normalized_commission_cost": float(
                result.normalized_commission_cost
            ),
            "history_invoked": bool(
                result.history_invoked
            ),
            "adapter_reason": str(
                result.reason
            ),
            "adapter_mode": str(
                result.mode
            ),
            "adapter_version": str(
                result.version
            ),
        }

        self._validate_fill_audit(
            audit,
            fill,
        )

        if reconciled.signed_slippage_price is None:
            return self._invalid(
                reason=(
                    "FORWARD_RECONCILIATION_MISSING_SIGNED_SLIPPAGE"
                ),
                stage=self._EVENT_FINALIZED,
                request_id=request,
                order_ticket=order,
                execution_id=str(fill.execution_id),
                forward_transition=reconciled,
                completed_fill_result=result,
            )

        telemetry_doc = self._telemetry_document(
            reconciled.telemetry,
            reconciled.signed_slippage_price,
        )

        payload = {
            "request_id": request,
            "completed_fill": {
                "order_ticket": int(fill.order_ticket),
                "execution_id": str(fill.execution_id),
                "symbol": str(fill.symbol),
                "direction": str(fill.direction),
                "filled_volume": float(fill.filled_volume),
                "fill_price": float(fill.fill_price),
                "commission_cost": float(
                    fill.commission_cost
                ),
                "live_authorized": False,
            },
            "fill_audit": audit,
            "telemetry": telemetry_doc,
            "live_authorized": False,
        }

        self._append_event(
            self._EVENT_FINALIZED,
            payload,
        )

        self._state = reconciled.state_after
        self._finalized_telemetry[
            request
        ] = reconciled.telemetry

        return self._result(
            valid=True,
            applied=True,
            reason=(
                "OK_FORWARD_DEMO_AUTHORITATIVE_FILL_EVIDENCE_FINALIZED"
            ),
            action=(
                "FORWARD_NORMALIZED_TELEMETRY_READY_FOR_EXISTING_BRIDGE"
            ),
            stage=self._EVENT_FINALIZED,
            request_id=request,
            order_ticket=order,
            execution_id=str(fill.execution_id),
            forward_transition=reconciled,
            completed_fill_result=result,
            telemetry=reconciled.telemetry,
        )