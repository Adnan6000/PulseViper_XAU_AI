"""Durable exactly-once realized-fill observation coordinator.

SHADOW / RESEARCH / DEMO ONLY.

This module coordinates finalized forward telemetry with the existing
RealizedFillTelemetryBridge, then persists the resulting observational cost
state in a hash-chained JSONL journal with an atomic head anchor.

It never connects to a broker, submits or modifies orders/positions, changes
stops, mutates production risk, books execution costs into lifecycle P&L, or
authorizes live trading.

Each instance is bound to exactly one canonical symbol. Different symbols must
use different coordinator instances/journals, so learned/observed execution
state cannot silently cross-contaminate instruments.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import os
import re
import time
import uuid
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Callable

bridge_module: Any = importlib.import_module(
    "02_AI.Shadow.realized_fill_telemetry_bridge"
)
accounting_module: Any = importlib.import_module(
    "02_AI.Shadow.realized_execution_cost_accounting"
)

RealizedFillTelemetryBridge: Any = bridge_module.RealizedFillTelemetryBridge
RealizedExecutionCostState: Any = accounting_module.RealizedExecutionCostState


class RealizedFillObservationJournalError(RuntimeError):
    """Raised when durable observation state cannot be trusted."""


@dataclass(frozen=True)
class RealizedFillObservationCommit:
    valid: bool
    committed: bool
    already_committed: bool
    reason: str
    action: str
    mode: str
    version: str
    live_authorized: bool
    canonical_symbol: str
    request_id: str
    execution_id: str
    telemetry_fingerprint: str
    lifecycle_fingerprint: str
    event_sequence: int | None
    event_hash: str | None
    cost_state_before: Any
    cost_state_after: Any
    observation: Any
    observation_summary: dict[str, Any] | None


@dataclass(frozen=True)
class RealizedFillObservationSnapshot:
    canonical_symbol: str
    observation_count: int
    complete_observation_count: int
    committed_request_count: int
    committed_execution_count: int
    last_event_sequence: int
    last_event_hash: str
    live_authorized: bool


@dataclass(frozen=True)
class _CommittedObservation:
    request_id: str
    execution_id: str
    telemetry_fingerprint: str
    lifecycle_fingerprint: str
    event_sequence: int
    event_hash: str
    observation_summary: dict[str, Any]


class RealizedFillObservationCoordinator:
    VERSION = "1.0"
    MODE = "SHADOW_DURABLE_REALIZED_FILL_OBSERVATION_COORDINATOR_ONLY"

    _EVENT_TYPE = "REALIZED_FILL_OBSERVATION_COMMITTED"
    _GENESIS_HASH = "GENESIS"
    _SYMBOL_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9._-]{0,63}$")
    _STATE_FIELDS = tuple(field.name for field in fields(RealizedExecutionCostState))
    _REQUIRED_OBSERVATION_FIELDS = (
        "valid",
        "observed",
        "reason",
        "cost_reason",
        "live_authorized",
        "lifecycle_pnl_delta",
        "execution_id",
        "cost_state_before",
        "cost_state_after",
        "realized_spread_available",
        "realized_spread_cost",
        "realized_slippage_available",
        "realized_slippage_cost",
        "realized_commission_available",
        "realized_commission_cost",
    )

    def __init__(
        self,
        *,
        forward_journal: Any,
        canonical_symbol: str,
        journal_path: str | Path | None = None,
        bridge: Any | None = None,
        clock_msc: Callable[[], int] | None = None,
    ) -> None:
        if forward_journal is None:
            raise ValueError("forward_journal is required")
        if not hasattr(forward_journal, "telemetry_for"):
            raise TypeError("forward_journal must expose telemetry_for(request_id)")

        self.forward_journal = forward_journal
        self.canonical_symbol = self._canonical_symbol(canonical_symbol)
        self.bridge = bridge if bridge is not None else RealizedFillTelemetryBridge()
        if not hasattr(self.bridge, "initial_cost_state") or not hasattr(
            self.bridge, "observe_fill"
        ):
            raise TypeError(
                "bridge must expose initial_cost_state() and observe_fill(...)"
            )

        self._clock_msc = clock_msc if clock_msc is not None else self._system_clock_msc
        if journal_path is None:
            name = f"{self.canonical_symbol.lower()}.realized_fill_observation.journal.jsonl"
            self.path = Path("01_Data/Processed") / name
        else:
            self.path = Path(journal_path)

        self.anchor_path = self.path.with_name(self.path.name + ".anchor.json")
        self.lock_path = self.path.with_name(self.path.name + ".lock")

        self._lock_file: Any = None
        self._closed = False
        self._poisoned = False
        self._cost_state = self.bridge.initial_cost_state()
        self._committed_by_request: dict[str, _CommittedObservation] = {}
        self._request_by_execution: dict[str, str] = {}
        self._last_event_sequence = 0
        self._last_event_hash = self._GENESIS_HASH
        self._last_committed_at_msc = 0

        self._implementation_document = self._build_implementation_document()
        self._implementation_fingerprint = self._hash_document(
            self._implementation_document
        )

        self._acquire_writer_lock()
        try:
            self._recover()
        except Exception:
            self.close()
            raise

    # ------------------------------------------------------------------
    # Lifetime / writer ownership
    # ------------------------------------------------------------------

    def __enter__(self) -> "RealizedFillObservationCoordinator":
        return self

    def __exit__(self, _exc_type: Any, _exc: Any, _tb: Any) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        handle = self._lock_file
        self._lock_file = None
        if handle is None:
            return

        try:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()

    def _acquire_writer_lock(self) -> None:
        self._ensure_safe_runtime_path(self.lock_path)
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.lock_path.open("a+b")
        try:
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
                os.fsync(handle.fileno())
            handle.seek(0)

            if os.name == "nt":
                import msvcrt

                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError as exc:
                    raise RealizedFillObservationJournalError(
                        "REALIZED_FILL_OBSERVATION_WRITER_ALREADY_ACTIVE"
                    ) from exc
            else:
                import fcntl

                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError as exc:
                    raise RealizedFillObservationJournalError(
                        "REALIZED_FILL_OBSERVATION_WRITER_ALREADY_ACTIVE"
                    ) from exc
        except Exception:
            handle.close()
            raise
        self._lock_file = handle

    # ------------------------------------------------------------------
    # Public state
    # ------------------------------------------------------------------

    @property
    def cost_state(self) -> Any:
        return self._cost_state

    def snapshot(self) -> RealizedFillObservationSnapshot:
        return RealizedFillObservationSnapshot(
            canonical_symbol=self.canonical_symbol,
            observation_count=int(self._cost_state.observation_count),
            complete_observation_count=int(self._cost_state.complete_observation_count),
            committed_request_count=len(self._committed_by_request),
            committed_execution_count=len(self._request_by_execution),
            last_event_sequence=self._last_event_sequence,
            last_event_hash=self._last_event_hash,
            live_authorized=False,
        )

    # ------------------------------------------------------------------
    # Main exactly-once operation
    # ------------------------------------------------------------------

    def observe_finalized(
        self,
        *,
        request_id: str,
        canonical_symbol: str,
        lifecycle_transition: Any,
        live_authorized: bool = False,
    ) -> RealizedFillObservationCommit:
        self._assert_usable()
        before = self._cost_state
        resolved_request_id = str(request_id).strip()

        if not resolved_request_id:
            return self._invalid("INVALID_REQUEST_ID", "", before)
        if bool(live_authorized):
            return self._invalid(
                "LIVE_AUTHORIZATION_NOT_ALLOWED", resolved_request_id, before
            )

        try:
            supplied_symbol = self._canonical_symbol(canonical_symbol)
        except ValueError:
            return self._invalid(
                "INVALID_CANONICAL_SYMBOL", resolved_request_id, before
            )
        if supplied_symbol != self.canonical_symbol:
            return self._invalid(
                "CANONICAL_SYMBOL_SCOPE_MISMATCH", resolved_request_id, before
            )

        try:
            telemetry = self.forward_journal.telemetry_for(resolved_request_id)
        except Exception:
            return self._invalid(
                "FORWARD_TELEMETRY_READ_EXCEPTION", resolved_request_id, before
            )
        if telemetry is None:
            return self._invalid(
                "FORWARD_TELEMETRY_NOT_FINALIZED", resolved_request_id, before
            )

        try:
            telemetry_document = self._telemetry_document(telemetry)
            lifecycle_document = self._lifecycle_document(lifecycle_transition)
        except (TypeError, ValueError) as exc:
            return self._invalid(str(exc), resolved_request_id, before)

        if bool(telemetry_document["live_authorized"]):
            return self._invalid(
                "FILL_TELEMETRY_LIVE_AUTHORIZATION_NOT_ALLOWED",
                resolved_request_id,
                before,
            )

        execution_id = str(telemetry_document["execution_id"]).strip()
        if not execution_id:
            return self._invalid("INVALID_EXECUTION_ID", resolved_request_id, before)

        telemetry_fingerprint = self._hash_document(telemetry_document)
        lifecycle_fingerprint = self._hash_document(lifecycle_document)

        existing = self._committed_by_request.get(resolved_request_id)
        if existing is not None:
            if (
                existing.execution_id == execution_id
                and existing.telemetry_fingerprint == telemetry_fingerprint
                and existing.lifecycle_fingerprint == lifecycle_fingerprint
            ):
                return RealizedFillObservationCommit(
                    valid=True,
                    committed=False,
                    already_committed=True,
                    reason="OK_ALREADY_COMMITTED",
                    action="NO_NEW_OBSERVATION",
                    mode=self.MODE,
                    version=self.VERSION,
                    live_authorized=False,
                    canonical_symbol=self.canonical_symbol,
                    request_id=resolved_request_id,
                    execution_id=execution_id,
                    telemetry_fingerprint=telemetry_fingerprint,
                    lifecycle_fingerprint=lifecycle_fingerprint,
                    event_sequence=existing.event_sequence,
                    event_hash=existing.event_hash,
                    cost_state_before=self._cost_state,
                    cost_state_after=self._cost_state,
                    observation=None,
                    observation_summary=dict(existing.observation_summary),
                )
            return self._invalid(
                "REQUEST_EVIDENCE_MISMATCH",
                resolved_request_id,
                before,
                execution_id,
                telemetry_fingerprint,
                lifecycle_fingerprint,
            )

        if execution_id in self._request_by_execution:
            return self._invalid(
                "DUPLICATE_EXECUTION_ID",
                resolved_request_id,
                before,
                execution_id,
                telemetry_fingerprint,
                lifecycle_fingerprint,
            )

        try:
            observation = self.bridge.observe_fill(
                cost_state=before,
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
            )
        except Exception:
            return self._invalid(
                "REALIZED_FILL_BRIDGE_EXCEPTION",
                resolved_request_id,
                before,
                execution_id,
                telemetry_fingerprint,
                lifecycle_fingerprint,
            )

        if not self._has_fields(observation, self._REQUIRED_OBSERVATION_FIELDS):
            return self._invalid(
                "INVALID_REALIZED_FILL_BRIDGE_RESULT",
                resolved_request_id,
                before,
                execution_id,
                telemetry_fingerprint,
                lifecycle_fingerprint,
                observation=observation,
            )

        try:
            summary = self._observation_summary(observation)
        except ValueError as exc:
            return self._invalid(
                str(exc),
                resolved_request_id,
                before,
                execution_id,
                telemetry_fingerprint,
                lifecycle_fingerprint,
                observation=observation,
            )

        if not bool(observation.valid) or not bool(observation.observed):
            return self._invalid(
                "REALIZED_FILL_BRIDGE_REJECTED",
                resolved_request_id,
                before,
                execution_id,
                telemetry_fingerprint,
                lifecycle_fingerprint,
                observation,
                summary,
            )

        if str(observation.execution_id).strip() != execution_id:
            return self._invalid(
                "BRIDGE_EXECUTION_ID_MISMATCH",
                resolved_request_id,
                before,
                execution_id,
                telemetry_fingerprint,
                lifecycle_fingerprint,
                observation,
                summary,
            )

        if bool(observation.live_authorized) or abs(summary["lifecycle_pnl_delta"]) > 1e-8:
            return self._invalid(
                "REALIZED_FILL_BRIDGE_BOUNDARY_VIOLATION",
                resolved_request_id,
                before,
                execution_id,
                telemetry_fingerprint,
                lifecycle_fingerprint,
                observation,
                summary,
            )

        try:
            before_document = self._state_document(before)
            observation_before = self._state_document(observation.cost_state_before)
            after_document = self._state_document(observation.cost_state_after)
        except ValueError as exc:
            return self._invalid(
                str(exc),
                resolved_request_id,
                before,
                execution_id,
                telemetry_fingerprint,
                lifecycle_fingerprint,
                observation,
                summary,
            )

        if observation_before != before_document:
            return self._invalid(
                "BRIDGE_COST_STATE_BEFORE_MISMATCH",
                resolved_request_id,
                before,
                execution_id,
                telemetry_fingerprint,
                lifecycle_fingerprint,
                observation,
                summary,
            )

        try:
            self._validate_state_transition(
                before_document, after_document, execution_id
            )
        except RealizedFillObservationJournalError as exc:
            return self._invalid(
                str(exc),
                resolved_request_id,
                before,
                execution_id,
                telemetry_fingerprint,
                lifecycle_fingerprint,
                observation,
                summary,
            )

        payload = {
            "request_id": resolved_request_id,
            "execution_id": execution_id,
            "telemetry_fingerprint": telemetry_fingerprint,
            "lifecycle_fingerprint": lifecycle_fingerprint,
            "telemetry": telemetry_document,
            "lifecycle": lifecycle_document,
            "cost_state_before": before_document,
            "cost_state_after": after_document,
            "observation": summary,
        }

        sequence, event_hash = self._append_event(payload)

        committed = _CommittedObservation(
            request_id=resolved_request_id,
            execution_id=execution_id,
            telemetry_fingerprint=telemetry_fingerprint,
            lifecycle_fingerprint=lifecycle_fingerprint,
            event_sequence=sequence,
            event_hash=event_hash,
            observation_summary=summary,
        )
        self._cost_state = observation.cost_state_after
        self._committed_by_request[resolved_request_id] = committed
        self._request_by_execution[execution_id] = resolved_request_id

        return RealizedFillObservationCommit(
            valid=True,
            committed=True,
            already_committed=False,
            reason="OK_REALIZED_FILL_OBSERVATION_COMMITTED",
            action="COMMIT_REALIZED_FILL_OBSERVATION",
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            canonical_symbol=self.canonical_symbol,
            request_id=resolved_request_id,
            execution_id=execution_id,
            telemetry_fingerprint=telemetry_fingerprint,
            lifecycle_fingerprint=lifecycle_fingerprint,
            event_sequence=sequence,
            event_hash=event_hash,
            cost_state_before=before,
            cost_state_after=self._cost_state,
            observation=observation,
            observation_summary=summary,
        )

    # ------------------------------------------------------------------
    # Evidence normalization
    # ------------------------------------------------------------------

    def _telemetry_document(self, telemetry: Any) -> dict[str, Any]:
        required = (
            "execution_id",
            "filled_volume",
            "fill_price",
            "quote_bid",
            "quote_ask",
            "commission_cost",
            "live_authorized",
        )
        if not self._has_fields(telemetry, required):
            raise ValueError("INVALID_FILL_TELEMETRY_SHAPE")
        return {
            "execution_id": str(telemetry.execution_id).strip(),
            "filled_volume": self._finite_number(
                telemetry.filled_volume, "INVALID_FILLED_VOLUME"
            ),
            "fill_price": self._optional_finite_number(
                telemetry.fill_price, "INVALID_FILL_PRICE"
            ),
            "quote_bid": self._optional_finite_number(
                telemetry.quote_bid, "INVALID_QUOTE_BID"
            ),
            "quote_ask": self._optional_finite_number(
                telemetry.quote_ask, "INVALID_QUOTE_ASK"
            ),
            "commission_cost": self._optional_finite_number(
                telemetry.commission_cost, "INVALID_COMMISSION_COST"
            ),
            "live_authorized": bool(telemetry.live_authorized),
        }

    def _lifecycle_document(self, transition: Any) -> dict[str, Any]:
        try:
            protected = transition.protected_admission_result
            admission = protected.admission_result
            risk = admission.risk_plan
            friction = admission.friction_assessment
            candidate = admission.candidate
            pnl_before = transition.lifecycle_state_before.pnl_state
            pnl_after = transition.lifecycle_state_after.pnl_state
        except AttributeError as exc:
            raise ValueError("INVALID_LIFECYCLE_TRANSITION_SHAPE") from exc

        n = self._finite_number
        return {
            "valid": bool(transition.valid),
            "exposure_applied": bool(transition.exposure_applied),
            "live_authorized": bool(transition.live_authorized),
            "lifecycle_invoked": bool(transition.lifecycle_invoked),
            "lifecycle_spread_before": n(
                pnl_before.cumulative_spread_cost, "INVALID_LIFECYCLE_SPREAD_BEFORE"
            ),
            "lifecycle_spread_after": n(
                pnl_after.cumulative_spread_cost, "INVALID_LIFECYCLE_SPREAD_AFTER"
            ),
            "protected": {"live_authorized": bool(protected.live_authorized)},
            "admission": {
                "valid": bool(admission.valid),
                "admitted": bool(admission.admitted),
                "live_authorized": bool(admission.live_authorized),
            },
            "risk": {
                "valid": bool(risk.valid),
                "live_authorized": bool(risk.live_authorized),
                "direction": str(risk.direction),
                "selected_volume": n(
                    risk.selected_volume, "INVALID_RISK_SELECTED_VOLUME"
                ),
                "entry_price": n(risk.entry_price, "INVALID_RISK_ENTRY_PRICE"),
                "stop_distance_price": n(
                    risk.stop_distance_price, "INVALID_RISK_STOP_DISTANCE_PRICE"
                ),
                "stop_distance_points": n(
                    risk.stop_distance_points, "INVALID_RISK_STOP_DISTANCE_POINTS"
                ),
                "estimated_stop_loss_amount": n(
                    risk.estimated_stop_loss_amount,
                    "INVALID_RISK_ESTIMATED_STOP_LOSS",
                ),
                "spread_price": n(risk.spread_price, "INVALID_RISK_SPREAD_PRICE"),
                "spread_points": n(risk.spread_points, "INVALID_RISK_SPREAD_POINTS"),
                "spread_cost": n(risk.spread_cost, "INVALID_RISK_SPREAD_COST"),
            },
            "friction": {
                "valid": bool(friction.valid),
                "execution_feasible": bool(friction.execution_feasible),
                "live_authorized": bool(friction.live_authorized),
                "direction": str(friction.direction),
                "volume": n(friction.volume, "INVALID_FRICTION_VOLUME"),
                "entry_price": n(
                    friction.entry_price, "INVALID_FRICTION_ENTRY_PRICE"
                ),
                "stop_distance_price": n(
                    friction.stop_distance_price,
                    "INVALID_FRICTION_STOP_DISTANCE_PRICE",
                ),
                "projected_stop_loss": n(
                    friction.projected_stop_loss,
                    "INVALID_FRICTION_PROJECTED_STOP_LOSS",
                ),
                "spread_price": n(
                    friction.spread_price, "INVALID_FRICTION_SPREAD_PRICE"
                ),
                "spread_cost": n(
                    friction.spread_cost, "INVALID_FRICTION_SPREAD_COST"
                ),
                "estimated_slippage_cost": n(
                    friction.estimated_slippage_cost,
                    "INVALID_FRICTION_ESTIMATED_SLIPPAGE_COST",
                ),
                "estimated_commission_cost": n(
                    friction.estimated_commission_cost,
                    "INVALID_FRICTION_ESTIMATED_COMMISSION_COST",
                ),
                "total_friction_cost": n(
                    friction.total_friction_cost, "INVALID_FRICTION_TOTAL_COST"
                ),
            },
            "candidate": {
                "direction": str(candidate.direction),
                "volume": n(candidate.volume, "INVALID_CANDIDATE_VOLUME"),
                "projected_stop_loss": n(
                    candidate.projected_stop_loss,
                    "INVALID_CANDIDATE_PROJECTED_STOP_LOSS",
                ),
                "spread_cost": n(
                    candidate.spread_cost, "INVALID_CANDIDATE_SPREAD_COST"
                ),
                "structural_stop_distance": n(
                    candidate.structural_stop_distance,
                    "INVALID_CANDIDATE_STOP_DISTANCE",
                ),
            },
        }

    # ------------------------------------------------------------------
    # Cost-state persistence
    # ------------------------------------------------------------------

    def _state_document(self, state: Any) -> dict[str, Any]:
        if state is None or not all(hasattr(state, name) for name in self._STATE_FIELDS):
            raise ValueError("INVALID_REALIZED_COST_STATE_SHAPE")

        document: dict[str, Any] = {}
        for name in self._STATE_FIELDS:
            value = getattr(state, name)
            if name == "execution_ids":
                document[name] = [str(item) for item in value]
            elif isinstance(value, bool):
                document[name] = value
            elif isinstance(value, int):
                document[name] = value
            elif isinstance(value, float):
                document[name] = self._finite_number(
                    value, "INVALID_REALIZED_COST_STATE_NUMBER"
                )
            else:
                raise ValueError("INVALID_REALIZED_COST_STATE_VALUE")

        if bool(document.get("live_authorized", True)):
            raise ValueError("REALIZED_COST_STATE_LIVE_AUTHORIZATION_NOT_ALLOWED")
        return document

    def _state_from_document(self, document: dict[str, Any]) -> Any:
        if not isinstance(document, dict):
            raise RealizedFillObservationJournalError("INVALID_PERSISTED_COST_STATE")
        if set(document) != set(self._STATE_FIELDS):
            raise RealizedFillObservationJournalError(
                "PERSISTED_COST_STATE_SCHEMA_MISMATCH"
            )

        values = dict(document)
        execution_ids = values.get("execution_ids")
        if not isinstance(execution_ids, list) or not all(
            isinstance(item, str) and bool(item.strip()) for item in execution_ids
        ):
            raise RealizedFillObservationJournalError(
                "INVALID_PERSISTED_EXECUTION_IDS"
            )
        values["execution_ids"] = tuple(execution_ids)

        try:
            state = RealizedExecutionCostState(**values)
            normalized = self._state_document(state)
        except Exception as exc:
            raise RealizedFillObservationJournalError(
                "INVALID_PERSISTED_COST_STATE"
            ) from exc
        if normalized != document:
            raise RealizedFillObservationJournalError(
                "PERSISTED_COST_STATE_NORMALIZATION_MISMATCH"
            )
        return state

    def _validate_state_transition(
        self,
        before_document: dict[str, Any],
        after_document: dict[str, Any],
        execution_id: str,
    ) -> None:
        before_ids = list(before_document["execution_ids"])
        after_ids = list(after_document["execution_ids"])
        if after_ids != before_ids + [execution_id]:
            raise RealizedFillObservationJournalError(
                "REALIZED_COST_EXECUTION_ID_TRANSITION_MISMATCH"
            )
        if int(after_document["observation_count"]) != int(
            before_document["observation_count"]
        ) + 1:
            raise RealizedFillObservationJournalError(
                "REALIZED_COST_OBSERVATION_COUNT_TRANSITION_MISMATCH"
            )

        count_fields = (
            "complete_observation_count",
            "realized_spread_observation_count",
            "realized_slippage_observation_count",
            "realized_commission_observation_count",
        )
        for name in count_fields:
            before_value = int(before_document[name])
            after_value = int(after_document[name])
            if after_value not in {before_value, before_value + 1}:
                raise RealizedFillObservationJournalError(
                    "REALIZED_COST_COMPONENT_COUNT_TRANSITION_MISMATCH"
                )
        if bool(after_document["live_authorized"]):
            raise RealizedFillObservationJournalError(
                "REALIZED_COST_STATE_LIVE_AUTHORIZATION_NOT_ALLOWED"
            )

    # ------------------------------------------------------------------
    # Durable journal
    # ------------------------------------------------------------------

    def _append_event(self, payload: dict[str, Any]) -> tuple[int, str]:
        self._assert_usable()
        self._verify_disk_matches_memory()

        now = int(self._clock_msc())
        if now < 0:
            raise RealizedFillObservationJournalError("INVALID_COMMIT_TIMESTAMP")
        if now < self._last_committed_at_msc:
            raise RealizedFillObservationJournalError("PERSISTENCE_CLOCK_ROLLBACK")

        sequence = self._last_event_sequence + 1
        body = {
            "version": self.VERSION,
            "mode": self.MODE,
            "event_type": self._EVENT_TYPE,
            "canonical_symbol": self.canonical_symbol,
            "implementation_fingerprint": self._implementation_fingerprint,
            "sequence": sequence,
            "previous_event_hash": self._last_event_hash,
            "committed_at_msc": now,
            "payload": payload,
        }
        event_hash = self._hash_document(body)
        event = {**body, "event_hash": event_hash}
        encoded = self._canonical_json(event).encode("utf-8") + b"\n"

        self._ensure_safe_runtime_path(self.path)
        self._ensure_safe_runtime_path(self.anchor_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with self.path.open("ab") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())

            anchor = {
                "version": self.VERSION,
                "mode": self.MODE,
                "canonical_symbol": self.canonical_symbol,
                "implementation_fingerprint": self._implementation_fingerprint,
                "last_event_sequence": sequence,
                "last_event_hash": event_hash,
                "last_committed_at_msc": now,
                "journal_size_bytes": self.path.stat().st_size,
            }
            self._atomic_write_anchor(anchor)
        except Exception as exc:
            self._poisoned = True
            raise RealizedFillObservationJournalError(
                "REALIZED_FILL_OBSERVATION_HALF_COMMIT_OR_IO_FAILURE"
            ) from exc

        self._last_event_sequence = sequence
        self._last_event_hash = event_hash
        self._last_committed_at_msc = now
        return sequence, event_hash

    def _atomic_write_anchor(self, anchor: dict[str, Any]) -> None:
        token = uuid.uuid4().hex
        temp_path = self.anchor_path.with_name(
            f".{self.anchor_path.name}.{token}.anchor.json"
        )
        self._ensure_safe_runtime_path(temp_path)
        data = self._canonical_json(anchor).encode("utf-8") + b"\n"
        descriptor: int | None = None
        try:
            descriptor = os.open(
                temp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
            )
            with os.fdopen(descriptor, "wb", closefd=True) as handle:
                descriptor = None
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.anchor_path)
            self._fsync_parent_best_effort(self.anchor_path.parent)
        finally:
            if descriptor is not None:
                os.close(descriptor)
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    # ------------------------------------------------------------------
    # Recovery / integrity verification
    # ------------------------------------------------------------------

    def _recover(self) -> None:
        events, anchor = self._load_verified_events()
        if not events:
            return

        state = self.bridge.initial_cost_state()
        committed_by_request: dict[str, _CommittedObservation] = {}
        request_by_execution: dict[str, str] = {}

        for event in events:
            payload = event["payload"]
            request_id = str(payload.get("request_id", "")).strip()
            execution_id = str(payload.get("execution_id", "")).strip()
            telemetry_fp = str(payload.get("telemetry_fingerprint", "")).strip()
            lifecycle_fp = str(payload.get("lifecycle_fingerprint", "")).strip()
            if not request_id or not execution_id or not telemetry_fp or not lifecycle_fp:
                raise RealizedFillObservationJournalError(
                    "INVALID_PERSISTED_OBSERVATION_IDENTITY"
                )
            if request_id in committed_by_request:
                raise RealizedFillObservationJournalError(
                    "DUPLICATE_PERSISTED_REQUEST_ID"
                )
            if execution_id in request_by_execution:
                raise RealizedFillObservationJournalError(
                    "DUPLICATE_PERSISTED_EXECUTION_ID"
                )

            telemetry_document = payload.get("telemetry")
            lifecycle_document = payload.get("lifecycle")
            if self._hash_document(telemetry_document) != telemetry_fp:
                raise RealizedFillObservationJournalError(
                    "PERSISTED_TELEMETRY_FINGERPRINT_MISMATCH"
                )
            if self._hash_document(lifecycle_document) != lifecycle_fp:
                raise RealizedFillObservationJournalError(
                    "PERSISTED_LIFECYCLE_FINGERPRINT_MISMATCH"
                )

            current_document = self._state_document(state)
            before_document = payload.get("cost_state_before")
            after_document = payload.get("cost_state_after")
            if before_document != current_document:
                raise RealizedFillObservationJournalError(
                    "PERSISTED_COST_STATE_CHAIN_MISMATCH"
                )
            self._validate_state_transition(
                before_document, after_document, execution_id
            )
            state = self._state_from_document(after_document)

            summary = payload.get("observation")
            if not isinstance(summary, dict):
                raise RealizedFillObservationJournalError(
                    "INVALID_PERSISTED_OBSERVATION_SUMMARY"
                )

            committed = _CommittedObservation(
                request_id=request_id,
                execution_id=execution_id,
                telemetry_fingerprint=telemetry_fp,
                lifecycle_fingerprint=lifecycle_fp,
                event_sequence=int(event["sequence"]),
                event_hash=str(event["event_hash"]),
                observation_summary=dict(summary),
            )
            committed_by_request[request_id] = committed
            request_by_execution[execution_id] = request_id

        self._cost_state = state
        self._committed_by_request = committed_by_request
        self._request_by_execution = request_by_execution
        assert anchor is not None
        self._last_event_sequence = int(anchor["last_event_sequence"])
        self._last_event_hash = str(anchor["last_event_hash"])
        self._last_committed_at_msc = int(anchor["last_committed_at_msc"])

    def _verify_disk_matches_memory(self) -> None:
        events, anchor = self._load_verified_events()
        if not events:
            if self._last_event_sequence != 0:
                raise RealizedFillObservationJournalError(
                    "IN_MEMORY_DURABLE_STATE_DIVERGENCE"
                )
            return
        assert anchor is not None
        if int(anchor["last_event_sequence"]) != self._last_event_sequence or str(
            anchor["last_event_hash"]
        ) != self._last_event_hash:
            raise RealizedFillObservationJournalError(
                "STALE_WRITER_OR_EXTERNAL_JOURNAL_MUTATION"
            )

    def _load_verified_events(
        self,
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        self._ensure_safe_runtime_path(self.path)
        self._ensure_safe_runtime_path(self.anchor_path)
        journal_exists = self.path.exists()
        anchor_exists = self.anchor_path.exists()
        if not journal_exists and not anchor_exists:
            return [], None
        if journal_exists != anchor_exists:
            raise RealizedFillObservationJournalError(
                "JOURNAL_ANCHOR_PRESENCE_MISMATCH"
            )

        try:
            anchor = json.loads(self.anchor_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RealizedFillObservationJournalError(
                "INVALID_OBSERVATION_ANCHOR"
            ) from exc
        self._validate_anchor_shape(anchor)

        if self.path.stat().st_size != int(anchor["journal_size_bytes"]):
            raise RealizedFillObservationJournalError(
                "JOURNAL_SIZE_ANCHOR_MISMATCH"
            )

        try:
            raw_lines = self.path.read_text(encoding="utf-8").splitlines()
        except Exception as exc:
            raise RealizedFillObservationJournalError(
                "OBSERVATION_JOURNAL_READ_FAILED"
            ) from exc
        if not raw_lines:
            raise RealizedFillObservationJournalError("EMPTY_JOURNAL_WITH_ANCHOR")

        events: list[dict[str, Any]] = []
        previous_hash = self._GENESIS_HASH
        previous_timestamp = 0
        for expected_sequence, line in enumerate(raw_lines, start=1):
            if not line.strip():
                raise RealizedFillObservationJournalError(
                    "BLANK_OBSERVATION_JOURNAL_EVENT"
                )
            try:
                event = json.loads(line)
            except Exception as exc:
                raise RealizedFillObservationJournalError(
                    "INVALID_OBSERVATION_JOURNAL_JSON"
                ) from exc
            self._validate_event_shape(event)

            if int(event["sequence"]) != expected_sequence:
                raise RealizedFillObservationJournalError(
                    "OBSERVATION_JOURNAL_SEQUENCE_MISMATCH"
                )
            if str(event["previous_event_hash"]) != previous_hash:
                raise RealizedFillObservationJournalError(
                    "OBSERVATION_JOURNAL_PREDECESSOR_MISMATCH"
                )

            committed_at = int(event["committed_at_msc"])
            if committed_at < previous_timestamp:
                raise RealizedFillObservationJournalError(
                    "OBSERVATION_JOURNAL_CLOCK_ROLLBACK"
                )

            supplied_hash = str(event["event_hash"])
            body = dict(event)
            del body["event_hash"]
            if supplied_hash != self._hash_document(body):
                raise RealizedFillObservationJournalError(
                    "OBSERVATION_JOURNAL_HASH_MISMATCH"
                )

            previous_hash = supplied_hash
            previous_timestamp = committed_at
            events.append(event)

        if int(anchor["last_event_sequence"]) != len(events):
            raise RealizedFillObservationJournalError(
                "OBSERVATION_ANCHOR_SEQUENCE_MISMATCH"
            )
        if str(anchor["last_event_hash"]) != previous_hash:
            raise RealizedFillObservationJournalError(
                "OBSERVATION_ANCHOR_HASH_MISMATCH"
            )
        if int(anchor["last_committed_at_msc"]) != previous_timestamp:
            raise RealizedFillObservationJournalError(
                "OBSERVATION_ANCHOR_TIMESTAMP_MISMATCH"
            )
        return events, anchor

    def _validate_event_shape(self, event: Any) -> None:
        required = {
            "version",
            "mode",
            "event_type",
            "canonical_symbol",
            "implementation_fingerprint",
            "sequence",
            "previous_event_hash",
            "committed_at_msc",
            "payload",
            "event_hash",
        }
        if not isinstance(event, dict) or set(event) != required:
            raise RealizedFillObservationJournalError(
                "INVALID_OBSERVATION_JOURNAL_EVENT_SHAPE"
            )
        if (
            event["version"] != self.VERSION
            or event["mode"] != self.MODE
            or event["event_type"] != self._EVENT_TYPE
        ):
            raise RealizedFillObservationJournalError(
                "OBSERVATION_JOURNAL_VERSION_OR_MODE_MISMATCH"
            )
        if event["canonical_symbol"] != self.canonical_symbol:
            raise RealizedFillObservationJournalError(
                "OBSERVATION_JOURNAL_SYMBOL_SCOPE_MISMATCH"
            )
        if event["implementation_fingerprint"] != self._implementation_fingerprint:
            raise RealizedFillObservationJournalError(
                "OBSERVATION_IMPLEMENTATION_FINGERPRINT_MISMATCH"
            )
        if not isinstance(event["payload"], dict):
            raise RealizedFillObservationJournalError(
                "INVALID_OBSERVATION_JOURNAL_PAYLOAD"
            )

    def _validate_anchor_shape(self, anchor: Any) -> None:
        required = {
            "version",
            "mode",
            "canonical_symbol",
            "implementation_fingerprint",
            "last_event_sequence",
            "last_event_hash",
            "last_committed_at_msc",
            "journal_size_bytes",
        }
        if not isinstance(anchor, dict) or set(anchor) != required:
            raise RealizedFillObservationJournalError(
                "INVALID_OBSERVATION_ANCHOR_SHAPE"
            )
        if anchor["version"] != self.VERSION or anchor["mode"] != self.MODE:
            raise RealizedFillObservationJournalError(
                "OBSERVATION_ANCHOR_VERSION_OR_MODE_MISMATCH"
            )
        if anchor["canonical_symbol"] != self.canonical_symbol:
            raise RealizedFillObservationJournalError(
                "OBSERVATION_ANCHOR_SYMBOL_SCOPE_MISMATCH"
            )
        if anchor["implementation_fingerprint"] != self._implementation_fingerprint:
            raise RealizedFillObservationJournalError(
                "OBSERVATION_IMPLEMENTATION_FINGERPRINT_MISMATCH"
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _invalid(
        self,
        reason: str,
        request_id: str,
        cost_state: Any,
        execution_id: str = "",
        telemetry_fingerprint: str = "",
        lifecycle_fingerprint: str = "",
        observation: Any = None,
        observation_summary: dict[str, Any] | None = None,
    ) -> RealizedFillObservationCommit:
        return RealizedFillObservationCommit(
            valid=False,
            committed=False,
            already_committed=False,
            reason=reason,
            action="NO_ACTION",
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            canonical_symbol=self.canonical_symbol,
            request_id=request_id,
            execution_id=execution_id,
            telemetry_fingerprint=telemetry_fingerprint,
            lifecycle_fingerprint=lifecycle_fingerprint,
            event_sequence=None,
            event_hash=None,
            cost_state_before=cost_state,
            cost_state_after=cost_state,
            observation=observation,
            observation_summary=observation_summary,
        )

    def _observation_summary(self, observation: Any) -> dict[str, Any]:
        return {
            "reason": str(getattr(observation, "reason", "")),
            "cost_reason": str(getattr(observation, "cost_reason", "")),
            "realized_spread_available": bool(
                getattr(observation, "realized_spread_available", False)
            ),
            "realized_spread_cost": self._optional_finite_number(
                getattr(observation, "realized_spread_cost", None),
                "INVALID_REALIZED_SPREAD_COST",
            ),
            "realized_slippage_available": bool(
                getattr(observation, "realized_slippage_available", False)
            ),
            "realized_slippage_cost": self._optional_finite_number(
                getattr(observation, "realized_slippage_cost", None),
                "INVALID_REALIZED_SLIPPAGE_COST",
            ),
            "realized_commission_available": bool(
                getattr(observation, "realized_commission_available", False)
            ),
            "realized_commission_cost": self._optional_finite_number(
                getattr(observation, "realized_commission_cost", None),
                "INVALID_REALIZED_COMMISSION_COST",
            ),
            "lifecycle_pnl_delta": self._finite_number(
                getattr(observation, "lifecycle_pnl_delta", math.nan),
                "INVALID_BRIDGE_LIFECYCLE_PNL_DELTA",
            ),
        }

    def _build_implementation_document(self) -> dict[str, Any]:
        observer = getattr(self.bridge, "observer", None)
        accounting = getattr(observer, "accounting", None)
        return {
            "coordinator_version": self.VERSION,
            "coordinator_mode": self.MODE,
            "bridge_version": str(getattr(self.bridge, "VERSION", "")),
            "bridge_mode": str(getattr(self.bridge, "MODE", "")),
            "observer_version": str(getattr(observer, "VERSION", "")),
            "observer_mode": str(getattr(observer, "MODE", "")),
            "accounting_version": str(getattr(accounting, "VERSION", "")),
            "accounting_mode": str(getattr(accounting, "MODE", "")),
            "cost_state_fields": list(self._STATE_FIELDS),
        }

    @classmethod
    def _canonical_symbol(cls, value: str) -> str:
        resolved = str(value).strip().upper()
        if not cls._SYMBOL_PATTERN.fullmatch(resolved):
            raise ValueError("INVALID_CANONICAL_SYMBOL")
        return resolved

    @staticmethod
    def _system_clock_msc() -> int:
        return time.time_ns() // 1_000_000

    @staticmethod
    def _has_fields(value: Any, names: tuple[str, ...]) -> bool:
        return value is not None and all(hasattr(value, name) for name in names)

    @staticmethod
    def _finite_number(value: Any, reason: str) -> float:
        try:
            resolved = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(reason) from exc
        if not math.isfinite(resolved):
            raise ValueError(reason)
        return resolved

    @classmethod
    def _optional_finite_number(
        cls, value: Any, reason: str
    ) -> float | None:
        if value is None:
            return None
        return cls._finite_number(value, reason)

    @staticmethod
    def _canonical_json(document: Any) -> str:
        try:
            return json.dumps(
                document,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise RealizedFillObservationJournalError(
                "NON_CANONICAL_OBSERVATION_DOCUMENT"
            ) from exc

    @classmethod
    def _hash_document(cls, document: Any) -> str:
        return hashlib.sha256(cls._canonical_json(document).encode("utf-8")).hexdigest()

    @staticmethod
    def _ensure_safe_runtime_path(path: Path) -> None:
        if path.exists() and path.is_symlink():
            raise RealizedFillObservationJournalError(
                "SYMLINK_RUNTIME_PATH_NOT_ALLOWED"
            )

    @staticmethod
    def _fsync_parent_best_effort(parent: Path) -> None:
        if os.name == "nt":
            return
        try:
            descriptor = os.open(parent, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(descriptor)
        except OSError:
            pass
        finally:
            os.close(descriptor)

    def _assert_usable(self) -> None:
        if self._closed:
            raise RealizedFillObservationJournalError(
                "REALIZED_FILL_OBSERVATION_COORDINATOR_CLOSED"
            )
        if self._poisoned:
            raise RealizedFillObservationJournalError(
                "REALIZED_FILL_OBSERVATION_COORDINATOR_POISONED"
            )