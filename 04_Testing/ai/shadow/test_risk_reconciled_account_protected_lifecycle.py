"""
Offline tests for
RiskReconciledAccountProtectedLifecycleCoordinator v1.0.
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from typing import Any

import pytest


pytestmark = pytest.mark.offline


risk_module: Any = importlib.import_module(
    "02_AI.Shadow.broker_aware_risk_engine"
)

friction_module: Any = importlib.import_module(
    "02_AI.Shadow.execution_friction_model"
)

basket_module: Any = importlib.import_module(
    "02_AI.Shadow.bootstrap_compounding_planner"
)

adapter_module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_account_state_adapter"
)

trade_module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_trade_state_machine"
)

pnl_module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_pnl_ledger"
)

lifecycle_module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_lifecycle_accounting"
)

admission_module: Any = importlib.import_module(
    "02_AI.Shadow.execution_aware_compounding_admission"
)

lifecycle_gate_module: Any = importlib.import_module(
    "02_AI.Shadow.execution_aware_lifecycle_gate"
)

protection_module: Any = importlib.import_module(
    "02_AI.Shadow.account_protection_guard"
)

protected_module: Any = importlib.import_module(
    "02_AI.Shadow.account_protected_compounding_admission"
)

reconciliation_module: Any = importlib.import_module(
    "02_AI.Shadow.risk_mode_basket_reconciliation"
)

module: Any = importlib.import_module(
    "02_AI.Shadow.risk_reconciled_account_protected_lifecycle"
)


RiskEngine: Any = (
    risk_module.BrokerAwareRiskEngine
)

RiskPolicy: Any = (
    risk_module.BrokerRiskPolicy
)

FrictionModel: Any = (
    friction_module.ExecutionFrictionModel
)

Planner: Any = (
    basket_module.BootstrapCompoundingPlanner
)

PlannerPolicy: Any = (
    basket_module.BootstrapCompoundingPolicy
)

Adapter: Any = (
    adapter_module.CompoundingAccountStateAdapter
)

Machine: Any = (
    trade_module.CompoundingTradeStateMachine
)

Ledger: Any = (
    pnl_module.CompoundingPnLLedger
)

Lifecycle: Any = (
    lifecycle_module.CompoundingLifecycleAccounting
)

AdmissionEngine: Any = (
    admission_module.ExecutionAwareCompoundingAdmissionEngine
)

LifecycleGate: Any = (
    lifecycle_gate_module.ExecutionAwareLifecycleGate
)

ProtectionPolicy: Any = (
    protection_module.AccountProtectionPolicy
)

ProtectionGuard: Any = (
    protection_module.AccountProtectionGuard
)

ProtectedAdmissionEngine: Any = (
    protected_module.AccountProtectedCompoundingAdmissionEngine
)

ReconciliationEngine: Any = (
    reconciliation_module.RiskModeBasketReconciliationEngine
)

Coordinator: Any = (
    module.RiskReconciledAccountProtectedLifecycleCoordinator
)


BID = 4318.705

ASK = 4318.965

POINT = 0.001

TICK_SIZE = 0.001

VOLUME_MIN = 0.01

VOLUME_MAX = 200.0

VOLUME_STEP = 0.01

SPREAD = 0.260


def risk_engine() -> Any:

    return RiskEngine(
        RiskPolicy(
            target_risk_percent=0.75,
            hard_max_risk_percent=1.00,
            max_margin_percent_of_free=25.0,
            max_spread_cost_to_hard_risk_ratio=1.0,
            micro_enabled=True,
            micro_min_balance=3.0,
            micro_max_balance=20.0,
            micro_hard_max_risk_percent=12.0,
            micro_max_margin_percent_of_free=80.0,
            micro_max_spread_cost_to_stop_risk_ratio=1.0,
            micro_max_stop_to_spread_risk_ratio=4.0,
        )
    )


def loss_estimator(
    stop_distance: float,
):

    def estimate(
        volume: float,
    ) -> float:

        return (
            stop_distance
            *
            (
                volume
                /
                0.01
            )
        )

    return estimate


def margin_estimator(
    volume: float,
) -> float:

    return (
        2.16
        *
        (
            volume
            /
            0.01
        )
    )


def spread_estimator(
    volume: float,
) -> float:

    return (
        SPREAD
        *
        (
            volume
            /
            0.01
        )
    )


def risk_plan(
    *,
    balance: float = 100.0,
    equity: float | None = None,
    free_margin: float | None = None,
    stop_distance: float = 0.50,
    direction: str = "LONG",
) -> Any:

    resolved_equity = (
        balance
        if equity is None
        else equity
    )

    resolved_free_margin = (
        resolved_equity
        if free_margin is None
        else free_margin
    )

    if direction == "LONG":

        stop_loss = (
            ASK
            -
            stop_distance
        )

    else:

        stop_loss = (
            BID
            +
            stop_distance
        )

    return risk_engine().plan(
        direction=direction,
        account_balance=balance,
        account_equity=resolved_equity,
        free_margin=resolved_free_margin,
        bid=BID,
        ask=ASK,
        stop_loss=stop_loss,
        point=POINT,
        tick_size=TICK_SIZE,
        volume_min=VOLUME_MIN,
        volume_max=VOLUME_MAX,
        volume_step=VOLUME_STEP,
        stops_level_points=0.0,
        loss_estimator=loss_estimator(
            stop_distance
        ),
        margin_estimator=margin_estimator,
        spread_cost_estimator=spread_estimator,
    )


def planner_policy() -> Any:

    return PlannerPolicy(
        compounding_enabled=True,
        allow_initial_multi_leg=False,
        max_simultaneous_legs=3,
        max_total_volume=0.03,
        bootstrap_balance_max=20.0,
        bootstrap_loss_budget_floor_usd=0.50,
        bootstrap_loss_budget_percent=16.67,
        bootstrap_loss_budget_ceiling_usd=2.00,
        bootstrap_margin_cap_percent=85.0,
        standard_basket_hard_loss_percent=2.0,
        standard_margin_cap_percent=35.0,
        max_total_spread_to_basket_loss_ratio=1.0,
        add_only_after_profit=True,
        minimum_profit_r_before_add=0.25,
        partial_booking_enabled=True,
        partial_booking_r=0.75,
        partial_booking_fraction=0.50,
        trail_enabled=True,
        trail_start_r=0.50,
        runner_r=1.25,
    )


def protection_guard() -> Any:

    return ProtectionGuard(
        ProtectionPolicy(
            max_peak_drawdown_percent=10.0,
            cooldown_bars_after_loss=5,
            loss_streak_threshold=3,
            cooldown_bars_after_loss_streak=30,
            flat_pnl_epsilon=1e-9,
        )
    )


def real_system() -> tuple[
    Any,
    Any,
    Any,
]:

    shared_policy = planner_policy()

    shared_planner = Planner(
        shared_policy
    )

    adapter = Adapter(
        planner=shared_planner
    )

    machine = Machine(
        planner=shared_planner,
        adapter=adapter,
    )

    lifecycle = Lifecycle(
        machine=machine,
        ledger=Ledger(),
    )

    admission = AdmissionEngine(
        friction_model=FrictionModel(),
        adapter=adapter,
    )

    guard = protection_guard()

    protected = ProtectedAdmissionEngine(
        protection_guard=guard,
        admission_engine=admission,
    )

    reconciliation = ReconciliationEngine(
        policy=shared_policy
    )

    lifecycle_gate = LifecycleGate(
        lifecycle=lifecycle
    )

    coordinator = Coordinator(
        protected_admission_engine=protected,
        reconciliation_engine=reconciliation,
        lifecycle_gate=lifecycle_gate,
    )

    return (
        coordinator,
        guard,
        lifecycle,
    )


def synthetic_execution_admission(
    *,
    risk_mode: str,
    risk_base: float,
    equity: float,
    basket_mode: str,
    total_loss: float,
    total_margin: float,
    total_spread: float,
) -> Any:

    basket_plan = SimpleNamespace(
        valid=True,
        basket_mode=basket_mode,
        total_projected_loss=total_loss,
        total_margin=total_margin,
        total_spread_cost=total_spread,
        live_authorized=False,
    )

    account_plan = SimpleNamespace(
        valid=True,
        live_authorized=False,
        basket_plan=basket_plan,
    )

    nested_risk_plan = SimpleNamespace(
        valid=True,
        risk_mode=risk_mode,
        risk_base=risk_base,
        equity=equity,
        live_authorized=False,
    )

    return SimpleNamespace(
        valid=True,
        admitted=True,
        reason="OK_EXECUTION_AWARE_COMPOUNDING_ADMISSION",
        live_authorized=False,
        risk_plan=nested_risk_plan,
        account_plan=account_plan,
    )


def protected_result(
    *,
    valid: bool = True,
    admitted: bool = True,
    reason: str = "OK_ACCOUNT_PROTECTED_COMPOUNDING_ADMISSION",
    downstream_invoked: bool = True,
    admission_result: Any = None,
    protection_state_after: Any = None,
) -> Any:

    return SimpleNamespace(
        valid=valid,
        admitted=admitted,
        reason=reason,
        live_authorized=False,
        downstream_invoked=downstream_invoked,
        protection_state_after=protection_state_after,
        admission_result=admission_result,
    )


class StaticProtectedAdmission:
    def __init__(
        self,
        result: Any,
    ) -> None:

        self.result = result

        self.calls = 0

    def admit(
        self,
        **_: Any,
    ) -> Any:

        self.calls += 1

        return self.result


class ExplodingReconciliation:
    def evaluate(
        self,
        **_: Any,
    ) -> Any:

        raise AssertionError(
            "reconciliation must not be invoked"
        )


class ExplodingLifecycleGate:
    def apply_start_admission(
        self,
        **_: Any,
    ) -> Any:

        raise AssertionError(
            "lifecycle gate must not be invoked"
        )

    def apply_addon_admission(
        self,
        **_: Any,
    ) -> Any:

        raise AssertionError(
            "lifecycle gate must not be invoked"
        )


class CaptureLifecycleGate:
    def __init__(
        self,
    ) -> None:

        self.start_calls = 0

    def apply_start_admission(
        self,
        *,
        state: Any,
        **_: Any,
    ) -> Any:

        self.start_calls += 1

        return SimpleNamespace(
            valid=True,
            reason="OK_FAKE_LIFECYCLE",
            action="START_BASKET",
            live_authorized=False,
            lifecycle_invoked=True,
            state_after=state,
        )


class MalformedReconciliation:
    def evaluate(
        self,
        **_: Any,
    ) -> Any:

        return SimpleNamespace(
            reason="MALFORMED"
        )


class LiveReconciliation:
    def evaluate(
        self,
        **_: Any,
    ) -> Any:

        return SimpleNamespace(
            valid=True,
            reconciled=True,
            reason="OK",
            live_authorized=True,
        )


def test_coordinator_is_shadow_only() -> None:

    coordinator, guard, lifecycle = (
        real_system()
    )

    result = coordinator.start(
        protection_state=guard.initial_state(
            equity=100.0
        ),
        lifecycle_state=lifecycle.initial_state(
            balance=100.0
        ),
        current_bar=1,
        risk_plan=risk_plan(),
        leg_id="L1",
        account_margin_used=0.0,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert coordinator.VERSION == "1.0"

    assert coordinator.MODE == (
        "SHADOW_RISK_RECONCILED_ACCOUNT_PROTECTED_LIFECYCLE_ONLY"
    )

    assert result.valid is True

    assert result.live_authorized is False


def test_real_standard_start_runs_all_four_boundaries() -> None:

    coordinator, guard, lifecycle = (
        real_system()
    )

    result = coordinator.start(
        protection_state=guard.initial_state(
            equity=100.0
        ),
        lifecycle_state=lifecycle.initial_state(
            balance=100.0
        ),
        current_bar=1,
        risk_plan=risk_plan(
            balance=100.0
        ),
        leg_id="L1",
        account_margin_used=0.0,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is True

    assert result.exposure_applied is True

    assert result.downstream_admission_invoked is True

    assert result.reconciliation_invoked is True

    assert result.lifecycle_gate_invoked is True

    assert result.lifecycle_invoked is True

    assert (
        result
        .reconciliation_result
        .risk_mode
        ==
        "STANDARD_COMPOUND"
    )

    assert (
        result
        .reconciliation_result
        .effective_basket_mode
        ==
        "STANDARD_COMPOUND_BASKET"
    )


def test_real_micro_start_runs_bootstrap_reconciliation() -> None:

    coordinator, guard, lifecycle = (
        real_system()
    )

    plan = risk_plan(
        balance=10.0,
        equity=10.0,
        free_margin=10.0,
        stop_distance=0.50,
    )

    assert plan.valid is True

    assert plan.risk_mode == (
        "MICRO_BOOTSTRAP"
    )

    result = coordinator.start(
        protection_state=guard.initial_state(
            equity=10.0
        ),
        lifecycle_state=lifecycle.initial_state(
            balance=10.0
        ),
        current_bar=1,
        risk_plan=plan,
        leg_id="L1",
        account_margin_used=0.0,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is True

    assert result.exposure_applied is True

    assert result.reconciliation_result.reconciled is True

    assert (
        result
        .reconciliation_result
        .effective_basket_mode
        ==
        "MICRO_BOOTSTRAP_BASKET"
    )


def test_real_start_books_raw_spread_once() -> None:

    coordinator, guard, lifecycle = (
        real_system()
    )

    result = coordinator.start(
        protection_state=guard.initial_state(
            equity=100.0
        ),
        lifecycle_state=lifecycle.initial_state(
            balance=100.0
        ),
        current_bar=1,
        risk_plan=risk_plan(),
        leg_id="L1",
        account_margin_used=0.0,
        volume_min=0.01,
        volume_step=0.01,
    )

    pnl = (
        result
        .lifecycle_state_after
        .pnl_state
    )

    assert pnl.floating_profit == pytest.approx(
        -0.26
    )

    assert pnl.cumulative_spread_cost == pytest.approx(
        0.26
    )


def test_protection_rejection_skips_reconciliation_and_lifecycle() -> None:

    protection_after = object()

    static_protected = StaticProtectedAdmission(
        protected_result(
            valid=False,
            admitted=False,
            reason="ACCOUNT_PROTECTION_BLOCKED",
            downstream_invoked=False,
            admission_result=None,
            protection_state_after=protection_after,
        )
    )

    coordinator = Coordinator(
        protected_admission_engine=static_protected,
        reconciliation_engine=ExplodingReconciliation(),
        lifecycle_gate=ExplodingLifecycleGate(),
    )

    lifecycle_state = object()

    result = coordinator.start(
        protection_state=object(),
        lifecycle_state=lifecycle_state,
        current_bar=1,
        risk_plan=object(),
        leg_id="L1",
        account_margin_used=0.0,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "PROTECTED_ADMISSION_REJECTED"
    )

    assert result.downstream_admission_invoked is False

    assert result.reconciliation_invoked is False

    assert result.lifecycle_gate_invoked is False

    assert result.lifecycle_invoked is False

    assert result.protection_state_after is (
        protection_after
    )

    assert result.lifecycle_state_after is (
        lifecycle_state
    )


def test_downstream_rejection_skips_reconciliation_and_lifecycle() -> None:

    static_protected = StaticProtectedAdmission(
        protected_result(
            valid=False,
            admitted=False,
            reason="DOWNSTREAM_ADMISSION_REJECTED",
            downstream_invoked=True,
            admission_result=SimpleNamespace(
                valid=False
            ),
            protection_state_after=object(),
        )
    )

    coordinator = Coordinator(
        protected_admission_engine=static_protected,
        reconciliation_engine=ExplodingReconciliation(),
        lifecycle_gate=ExplodingLifecycleGate(),
    )

    result = coordinator.start(
        protection_state=object(),
        lifecycle_state=object(),
        current_bar=1,
        risk_plan=object(),
        leg_id="L1",
        account_margin_used=0.0,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is False

    assert result.downstream_admission_invoked is True

    assert result.reconciliation_invoked is False

    assert result.lifecycle_invoked is False


def test_standard_bootstrap_label_override_can_continue_when_within_standard_caps() -> None:

    execution = synthetic_execution_admission(
        risk_mode="STANDARD_COMPOUND",
        risk_base=20.0,
        equity=20.0,
        basket_mode="MICRO_BOOTSTRAP_BASKET",
        total_loss=0.30,
        total_margin=3.00,
        total_spread=0.10,
    )

    protected = protected_result(
        admission_result=execution,
        protection_state_after=object(),
    )

    lifecycle_gate = CaptureLifecycleGate()

    coordinator = Coordinator(
        protected_admission_engine=(
            StaticProtectedAdmission(
                protected
            )
        ),
        reconciliation_engine=(
            ReconciliationEngine(
                policy=planner_policy()
            )
        ),
        lifecycle_gate=lifecycle_gate,
    )

    lifecycle_state = object()

    result = coordinator.start(
        protection_state=object(),
        lifecycle_state=lifecycle_state,
        current_bar=1,
        risk_plan=object(),
        leg_id="L1",
        account_margin_used=0.0,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is True

    assert result.reconciliation_result.reconciled is True

    assert (
        result
        .reconciliation_result
        .regime_override_required
        is True
    )

    assert lifecycle_gate.start_calls == (
        1
    )


def test_standard_override_policy_violation_never_reaches_lifecycle() -> None:

    execution = synthetic_execution_admission(
        risk_mode="STANDARD_COMPOUND",
        risk_base=20.0,
        equity=20.0,
        basket_mode="MICRO_BOOTSTRAP_BASKET",
        total_loss=0.50,
        total_margin=3.00,
        total_spread=0.10,
    )

    lifecycle_state = object()

    coordinator = Coordinator(
        protected_admission_engine=(
            StaticProtectedAdmission(
                protected_result(
                    admission_result=execution,
                    protection_state_after=object(),
                )
            )
        ),
        reconciliation_engine=(
            ReconciliationEngine(
                policy=planner_policy()
            )
        ),
        lifecycle_gate=ExplodingLifecycleGate(),
    )

    result = coordinator.start(
        protection_state=object(),
        lifecycle_state=lifecycle_state,
        current_bar=1,
        risk_plan=object(),
        leg_id="L1",
        account_margin_used=0.0,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is False

    assert result.exposure_applied is False

    assert result.reason == (
        "RISK_MODE_BASKET_RECONCILIATION_REJECTED"
    )

    assert result.reconciliation_reason == (
        "BASKET_LOSS_EXCEEDS_RISK_MODE_CAP"
    )

    assert result.reconciliation_invoked is True

    assert result.lifecycle_gate_invoked is False

    assert result.lifecycle_invoked is False

    assert result.lifecycle_state_after is (
        lifecycle_state
    )


def test_real_addon_reconciles_before_lifecycle_and_books_second_spread_once() -> None:

    coordinator, guard, lifecycle = (
        real_system()
    )

    started = coordinator.start(
        protection_state=guard.initial_state(
            equity=100.0
        ),
        lifecycle_state=lifecycle.initial_state(
            balance=100.0
        ),
        current_bar=1,
        risk_plan=risk_plan(),
        leg_id="L1",
        account_margin_used=0.0,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert started.valid is True

    addon_plan = risk_plan(
        balance=100.0,
        equity=100.30,
        free_margin=98.14,
        stop_distance=0.50,
    )

    added = coordinator.add(
        protection_state=(
            started.protection_state_after
        ),
        lifecycle_state=(
            started.lifecycle_state_after
        ),
        current_bar=2,
        risk_plan=addon_plan,
        leg_id="L2",
        account_margin_used=2.16,
        current_market_floating_profit=0.30,
        volume_min=0.01,
        volume_step=0.01,
        existing_legs=1,
        existing_direction="LONG",
        existing_volume=0.01,
        existing_projected_loss=0.50,
        existing_basket_margin=2.16,
        existing_spread_cost=0.26,
        existing_floating_profit=0.30,
        first_leg_initial_risk=0.50,
    )

    assert added.valid is True

    assert added.exposure_applied is True

    assert added.reconciliation_invoked is True

    assert added.lifecycle_invoked is True

    assert (
        added
        .lifecycle_state_after
        .trade_state
        .active_volume
        ==
        pytest.approx(
            0.02
        )
    )

    assert (
        added
        .lifecycle_state_after
        .pnl_state
        .cumulative_spread_cost
        ==
        pytest.approx(
            0.52
        )
    )


def test_malformed_reconciliation_fails_closed_before_lifecycle() -> None:

    execution = synthetic_execution_admission(
        risk_mode="STANDARD_COMPOUND",
        risk_base=100.0,
        equity=100.0,
        basket_mode="STANDARD_COMPOUND_BASKET",
        total_loss=1.00,
        total_margin=10.0,
        total_spread=0.50,
    )

    coordinator = Coordinator(
        protected_admission_engine=(
            StaticProtectedAdmission(
                protected_result(
                    admission_result=execution,
                    protection_state_after=object(),
                )
            )
        ),
        reconciliation_engine=MalformedReconciliation(),
        lifecycle_gate=ExplodingLifecycleGate(),
    )

    result = coordinator.start(
        protection_state=object(),
        lifecycle_state=object(),
        current_bar=1,
        risk_plan=object(),
        leg_id="L1",
        account_margin_used=0.0,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_RECONCILIATION_RESULT"
    )

    assert result.reconciliation_invoked is True

    assert result.lifecycle_gate_invoked is False


def test_reconciliation_live_authorization_is_refused() -> None:

    execution = synthetic_execution_admission(
        risk_mode="STANDARD_COMPOUND",
        risk_base=100.0,
        equity=100.0,
        basket_mode="STANDARD_COMPOUND_BASKET",
        total_loss=1.00,
        total_margin=10.0,
        total_spread=0.50,
    )

    coordinator = Coordinator(
        protected_admission_engine=(
            StaticProtectedAdmission(
                protected_result(
                    admission_result=execution,
                    protection_state_after=object(),
                )
            )
        ),
        reconciliation_engine=LiveReconciliation(),
        lifecycle_gate=ExplodingLifecycleGate(),
    )

    result = coordinator.start(
        protection_state=object(),
        lifecycle_state=object(),
        current_bar=1,
        risk_plan=object(),
        leg_id="L1",
        account_margin_used=0.0,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "RECONCILIATION_LIVE_AUTHORIZATION_NOT_ALLOWED"
    )

    assert result.live_authorized is False

    assert result.lifecycle_gate_invoked is False

    assert result.lifecycle_invoked is False