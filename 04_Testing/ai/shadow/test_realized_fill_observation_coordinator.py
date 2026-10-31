"""Offline tests for durable realized-fill observation coordination."""

from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

pytestmark = pytest.mark.offline

coordinator_module: Any = importlib.import_module(
    "02_AI.Shadow.realized_fill_observation_coordinator"
)
bridge_module: Any = importlib.import_module(
    "02_AI.Shadow.realized_fill_telemetry_bridge"
)
friction_module: Any = importlib.import_module(
    "02_AI.Shadow.execution_friction_model"
)

Coordinator: Any = coordinator_module.RealizedFillObservationCoordinator
JournalError: Any = coordinator_module.RealizedFillObservationJournalError
Bridge: Any = bridge_module.RealizedFillTelemetryBridge
Telemetry: Any = bridge_module.NormalizedActualFillTelemetry
FrictionModel: Any = friction_module.ExecutionFrictionModel


class MutableClock:
    def __init__(self, value: int = 1_800_000_000_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


class FakeForwardJournal:
    def __init__(self, telemetry_by_request: dict[str, Any] | None = None) -> None:
        self.telemetry_by_request = dict(telemetry_by_request or {})
        self.calls: list[str] = []

    def telemetry_for(self, request_id: str) -> Any:
        self.calls.append(request_id)
        return self.telemetry_by_request.get(request_id)


class CountingBridge:
    VERSION = Bridge.VERSION
    MODE = Bridge.MODE

    def __init__(self) -> None:
        self.inner = Bridge()
        self.observer = self.inner.observer
        self.calls = 0

    def initial_cost_state(self) -> Any:
        return self.inner.initial_cost_state()

    def observe_fill(self, **kwargs: Any) -> Any:
        self.calls += 1
        return self.inner.observe_fill(**kwargs)


def lifecycle_state(spread: float) -> Any:
    return SimpleNamespace(
        pnl_state=SimpleNamespace(cumulative_spread_cost=spread)
    )


def successful_transition(
    *,
    direction: str = "LONG",
    spread_before: float = 0.0,
    spread_after: float = 0.26,
    admission_valid: bool = True,
    candidate_spread: float = 0.26,
) -> Any:
    direction = direction.upper()
    entry = 4316.760 if direction == "LONG" else 4316.500
    stop = entry - 0.50 if direction == "LONG" else entry + 0.50

    friction = FrictionModel().evaluate(
        direction=direction,
        volume=0.01,
        balance=63.35,
        equity=63.35,
        hard_loss_budget=1.00,
        entry_price=entry,
        stop_loss=stop,
        point=0.001,
        spread_price=0.26,
        spread_cost=0.26,
        projected_stop_loss=0.50,
        estimated_slippage_price=0.02,
        estimated_slippage_cost=0.02,
        estimated_commission_cost=0.04,
    )
    assert friction.valid is True

    risk_plan = SimpleNamespace(
        valid=True,
        live_authorized=False,
        direction=direction,
        selected_volume=0.01,
        entry_price=entry,
        stop_distance_price=0.50,
        stop_distance_points=500.0,
        estimated_stop_loss_amount=0.50,
        spread_price=0.26,
        spread_points=260.0,
        spread_cost=0.26,
    )
    candidate = SimpleNamespace(
        direction=direction,
        volume=0.01,
        projected_stop_loss=0.50,
        spread_cost=candidate_spread,
        structural_stop_distance=0.50,
    )
    admission = SimpleNamespace(
        valid=admission_valid,
        admitted=admission_valid,
        live_authorized=False,
        risk_plan=risk_plan,
        friction_assessment=friction,
        candidate=candidate,
    )
    protected = SimpleNamespace(
        live_authorized=False,
        admission_result=admission,
    )
    return SimpleNamespace(
        valid=True,
        exposure_applied=True,
        live_authorized=False,
        lifecycle_invoked=True,
        lifecycle_state_before=lifecycle_state(spread_before),
        lifecycle_state_after=lifecycle_state(spread_after),
        protected_admission_result=protected,
    )


def telemetry(
    *,
    execution_id: str = "MT5_ORDER_9001",
    direction: str = "LONG",
    live_authorized: bool = False,
) -> Any:
    direction = direction.upper()
    return Telemetry(
        execution_id=execution_id,
        filled_volume=0.01,
        fill_price=4316.800 if direction == "LONG" else 4316.450,
        quote_bid=4316.500,
        quote_ask=4316.760,
        commission_cost=0.04,
        live_authorized=live_authorized,
    )


def journal_path(tmp_path: Path, name: str = "xau") -> Path:
    return tmp_path / f"{name}.realized_fill_observation.journal.jsonl"


def coordinator(
    tmp_path: Path,
    *,
    forward: FakeForwardJournal | None = None,
    bridge: Any | None = None,
    clock: MutableClock | None = None,
    symbol: str = "XAUUSD",
    path: Path | None = None,
) -> Any:
    return Coordinator(
        forward_journal=forward or FakeForwardJournal({"req-1": telemetry()}),
        canonical_symbol=symbol,
        journal_path=path or journal_path(tmp_path, symbol.lower()),
        bridge=bridge,
        clock_msc=clock or MutableClock(),
    )


def observe(
    engine: Any,
    *,
    request_id: str = "req-1",
    symbol: str = "XAUUSD",
    transition: Any | None = None,
    live_authorized: bool = False,
) -> Any:
    return engine.observe_finalized(
        request_id=request_id,
        canonical_symbol=symbol,
        lifecycle_transition=transition or successful_transition(),
        live_authorized=live_authorized,
    )


def test_first_observation_commits_durable_state(tmp_path: Path) -> None:
    engine = coordinator(tmp_path)
    result = observe(engine)

    assert result.valid is True
    assert result.committed is True
    assert result.already_committed is False
    assert result.reason == "OK_REALIZED_FILL_OBSERVATION_COMMITTED"
    assert result.live_authorized is False
    assert result.observation.lifecycle_pnl_delta == pytest.approx(0.0)
    assert result.cost_state_after.observation_count == 1
    assert result.cost_state_after.complete_observation_count == 1
    assert engine.path.exists()
    assert engine.anchor_path.exists()
    engine.close()


def test_exact_retry_is_idempotent_and_does_not_reinvoke_bridge(tmp_path: Path) -> None:
    counting = CountingBridge()
    engine = coordinator(tmp_path, bridge=counting)

    first = observe(engine)
    assert first.valid is True
    assert counting.calls == 1

    second = observe(engine)
    assert second.valid is True
    assert second.committed is False
    assert second.already_committed is True
    assert second.reason == "OK_ALREADY_COMMITTED"
    assert second.event_hash == first.event_hash
    assert counting.calls == 1
    assert engine.cost_state.observation_count == 1
    engine.close()


def test_same_request_with_changed_lifecycle_evidence_fails_closed(tmp_path: Path) -> None:
    counting = CountingBridge()
    engine = coordinator(tmp_path, bridge=counting)
    assert observe(engine).valid is True

    changed = successful_transition(candidate_spread=0.27)
    result = observe(engine, transition=changed)

    assert result.valid is False
    assert result.reason == "REQUEST_EVIDENCE_MISMATCH"
    assert counting.calls == 1
    assert engine.cost_state.observation_count == 1
    engine.close()


def test_duplicate_execution_id_under_new_request_fails_closed(tmp_path: Path) -> None:
    forward = FakeForwardJournal(
        {
            "req-1": telemetry(execution_id="EXEC-1"),
            "req-2": telemetry(execution_id="EXEC-1"),
        }
    )
    counting = CountingBridge()
    engine = coordinator(tmp_path, forward=forward, bridge=counting)

    assert observe(engine, request_id="req-1").valid is True
    second = observe(engine, request_id="req-2")

    assert second.valid is False
    assert second.reason == "DUPLICATE_EXECUTION_ID"
    assert counting.calls == 1
    assert engine.cost_state.observation_count == 1
    engine.close()


def test_restart_restores_cost_state_without_reinvoking_bridge(tmp_path: Path) -> None:
    path = journal_path(tmp_path)
    forward = FakeForwardJournal({"req-1": telemetry()})
    first_bridge = CountingBridge()
    first = coordinator(
        tmp_path,
        forward=forward,
        bridge=first_bridge,
        path=path,
    )
    committed = observe(first)
    assert committed.valid is True
    assert first_bridge.calls == 1
    expected_state = first.cost_state
    first.close()

    second_bridge = CountingBridge()
    recovered = coordinator(
        tmp_path,
        forward=forward,
        bridge=second_bridge,
        path=path,
    )
    assert recovered.cost_state == expected_state
    assert recovered.snapshot().committed_request_count == 1
    assert second_bridge.calls == 0

    retry = observe(recovered)
    assert retry.valid is True
    assert retry.already_committed is True
    assert second_bridge.calls == 0
    assert recovered.cost_state == expected_state
    recovered.close()


def test_restart_then_new_execution_advances_from_recovered_state(tmp_path: Path) -> None:
    path = journal_path(tmp_path)
    forward = FakeForwardJournal(
        {
            "req-1": telemetry(execution_id="EXEC-1"),
            "req-2": telemetry(execution_id="EXEC-2"),
        }
    )
    first = coordinator(tmp_path, forward=forward, path=path)
    assert observe(first, request_id="req-1").valid is True
    first.close()

    recovered = coordinator(tmp_path, forward=forward, path=path)
    second = observe(recovered, request_id="req-2")

    assert second.valid is True
    assert second.committed is True
    assert recovered.cost_state.observation_count == 2
    assert recovered.cost_state.complete_observation_count == 2
    assert recovered.cost_state.execution_ids == ("EXEC-1", "EXEC-2")
    assert recovered.snapshot().last_event_sequence == 2
    recovered.close()


def test_symbol_scope_mismatch_rejected_before_forward_read(tmp_path: Path) -> None:
    forward = FakeForwardJournal({"req-1": telemetry()})
    counting = CountingBridge()
    engine = coordinator(tmp_path, forward=forward, bridge=counting)

    result = observe(engine, symbol="BTCUSD")

    assert result.valid is False
    assert result.reason == "CANONICAL_SYMBOL_SCOPE_MISMATCH"
    assert forward.calls == []
    assert counting.calls == 0
    assert engine.cost_state.observation_count == 0
    engine.close()


def test_different_symbols_use_separate_durable_state(tmp_path: Path) -> None:
    xau_forward = FakeForwardJournal({"req-1": telemetry(execution_id="EXEC-1")})
    btc_forward = FakeForwardJournal({"req-1": telemetry(execution_id="EXEC-1")})

    xau = coordinator(
        tmp_path,
        forward=xau_forward,
        symbol="XAUUSD",
        path=journal_path(tmp_path, "xauusd"),
    )
    btc = coordinator(
        tmp_path,
        forward=btc_forward,
        symbol="BTCUSD",
        path=journal_path(tmp_path, "btcusd"),
    )

    assert observe(xau, symbol="XAUUSD").valid is True
    assert observe(btc, symbol="BTCUSD").valid is True
    assert xau.cost_state.execution_ids == ("EXEC-1",)
    assert btc.cost_state.execution_ids == ("EXEC-1",)
    assert xau.path != btc.path
    assert xau.snapshot().canonical_symbol == "XAUUSD"
    assert btc.snapshot().canonical_symbol == "BTCUSD"
    xau.close()
    btc.close()


def test_existing_xau_journal_cannot_be_recovered_as_btc(tmp_path: Path) -> None:
    path = journal_path(tmp_path, "shared")
    first = coordinator(tmp_path, symbol="XAUUSD", path=path)
    assert observe(first, symbol="XAUUSD").valid is True
    first.close()

    with pytest.raises(JournalError, match="SYMBOL_SCOPE_MISMATCH"):
        coordinator(tmp_path, symbol="BTCUSD", path=path)


def test_live_authorization_is_rejected_before_forward_read(tmp_path: Path) -> None:
    forward = FakeForwardJournal({"req-1": telemetry()})
    engine = coordinator(tmp_path, forward=forward)

    result = observe(engine, live_authorized=True)

    assert result.valid is False
    assert result.reason == "LIVE_AUTHORIZATION_NOT_ALLOWED"
    assert result.live_authorized is False
    assert forward.calls == []
    assert engine.cost_state.observation_count == 0
    engine.close()


def test_live_fill_telemetry_is_rejected(tmp_path: Path) -> None:
    forward = FakeForwardJournal(
        {"req-1": telemetry(live_authorized=True)}
    )
    counting = CountingBridge()
    engine = coordinator(tmp_path, forward=forward, bridge=counting)

    result = observe(engine)

    assert result.valid is False
    assert result.reason == "FILL_TELEMETRY_LIVE_AUTHORIZATION_NOT_ALLOWED"
    assert counting.calls == 0
    assert engine.cost_state.observation_count == 0
    engine.close()


def test_missing_finalized_telemetry_fails_closed(tmp_path: Path) -> None:
    engine = coordinator(tmp_path, forward=FakeForwardJournal())
    result = observe(engine)

    assert result.valid is False
    assert result.reason == "FORWARD_TELEMETRY_NOT_FINALIZED"
    assert engine.cost_state.observation_count == 0
    engine.close()


def test_bridge_rejection_is_not_durably_committed(tmp_path: Path) -> None:
    engine = coordinator(tmp_path)
    rejected = successful_transition(admission_valid=False)

    result = observe(engine, transition=rejected)

    assert result.valid is False
    assert result.reason == "REALIZED_FILL_BRIDGE_REJECTED"
    assert engine.cost_state.observation_count == 0
    assert engine.path.exists() is False
    assert engine.anchor_path.exists() is False
    engine.close()


def test_journal_hash_tamper_is_detected_on_restart(tmp_path: Path) -> None:
    path = journal_path(tmp_path)
    engine = coordinator(tmp_path, path=path)
    assert observe(engine).valid is True
    anchor_path = engine.anchor_path
    engine.close()

    event = json.loads(path.read_text(encoding="utf-8").strip())
    event["payload"]["request_id"] = "req-X"
    path.write_text(
        json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    anchor = json.loads(anchor_path.read_text(encoding="utf-8"))
    anchor["journal_size_bytes"] = path.stat().st_size
    anchor_path.write_text(
        json.dumps(anchor, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(JournalError, match="HASH_MISMATCH"):
        coordinator(tmp_path, path=path)


def test_anchor_hash_tamper_is_detected_on_restart(tmp_path: Path) -> None:
    path = journal_path(tmp_path)
    engine = coordinator(tmp_path, path=path)
    assert observe(engine).valid is True
    anchor_path = engine.anchor_path
    engine.close()

    anchor = json.loads(anchor_path.read_text(encoding="utf-8"))
    anchor["last_event_hash"] = "0" * 64
    anchor_path.write_text(
        json.dumps(anchor, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(JournalError, match="ANCHOR_HASH_MISMATCH"):
        coordinator(tmp_path, path=path)


def test_unanchored_extra_tail_is_detected(tmp_path: Path) -> None:
    path = journal_path(tmp_path)
    engine = coordinator(tmp_path, path=path)
    assert observe(engine).valid is True
    engine.close()

    with path.open("ab") as handle:
        handle.write(b"{}\n")

    with pytest.raises(JournalError, match="JOURNAL_SIZE_ANCHOR_MISMATCH"):
        coordinator(tmp_path, path=path)


def test_journal_without_anchor_is_fail_closed(tmp_path: Path) -> None:
    path = journal_path(tmp_path)
    engine = coordinator(tmp_path, path=path)
    assert observe(engine).valid is True
    anchor_path = engine.anchor_path
    engine.close()
    anchor_path.unlink()

    with pytest.raises(JournalError, match="JOURNAL_ANCHOR_PRESENCE_MISMATCH"):
        coordinator(tmp_path, path=path)


def test_single_writer_lock_is_enforced(tmp_path: Path) -> None:
    path = journal_path(tmp_path)
    first = coordinator(tmp_path, path=path)
    try:
        with pytest.raises(JournalError, match="WRITER_ALREADY_ACTIVE"):
            coordinator(tmp_path, path=path)
    finally:
        first.close()


def test_persistence_clock_rollback_is_fail_closed(tmp_path: Path) -> None:
    clock = MutableClock(1000)
    forward = FakeForwardJournal(
        {
            "req-1": telemetry(execution_id="EXEC-1"),
            "req-2": telemetry(execution_id="EXEC-2"),
        }
    )
    engine = coordinator(tmp_path, forward=forward, clock=clock)
    assert observe(engine, request_id="req-1").valid is True

    clock.value = 999
    with pytest.raises(JournalError, match="PERSISTENCE_CLOCK_ROLLBACK"):
        observe(engine, request_id="req-2")

    assert engine.cost_state.observation_count == 1
    engine.close()


def test_snapshot_is_lifecycle_neutral_and_auditable(tmp_path: Path) -> None:
    engine = coordinator(tmp_path)
    initial = engine.snapshot()
    assert initial.observation_count == 0
    assert initial.committed_request_count == 0
    assert initial.live_authorized is False

    assert observe(engine).valid is True
    after = engine.snapshot()
    assert after.observation_count == 1
    assert after.complete_observation_count == 1
    assert after.committed_request_count == 1
    assert after.committed_execution_count == 1
    assert after.last_event_sequence == 1
    assert after.last_event_hash != "GENESIS"
    assert after.live_authorized is False
    engine.close()


def test_coordinator_contains_no_broker_execution_calls() -> None:
    source = Path(coordinator_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {
        "order_send",
        "copy_ticks_range",
        "copy_ticks_from",
        "initialize",
        "shutdown",
    }
    called: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
            elif isinstance(node.func, ast.Name):
                called.add(node.func.id)
    assert called.isdisjoint(forbidden)