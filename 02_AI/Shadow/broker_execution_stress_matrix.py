"""
===============================================================================
Module      : broker_execution_stress_matrix.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Shadow Broker / Execution / Compounding Stress Evidence Matrix
===============================================================================

Status
------
SHADOW / RESEARCH / DEMO ONLY.

Purpose
-------
Exercise the existing broker-risk, execution-friction, basket-admission,
risk-mode reconciliation, and account-protection layers under deterministic
XAUUSDm stress scenarios without changing any production or research policy.

Coverage
--------
- spread spikes: 200 / 260 / 350 / 500 points
- structural stops: 0.30 / 0.40 / 0.50 / 0.60 / 1.00
- low free margin
- balance/equity divergence
- broker minimum-lot pressure
- MICRO -> STANDARD transition behavior
- STANDARD risk mode at <= $20
- planner/effective-regime reconciliation overrides
- add-on profit, leg-count, volume, loss, margin, spread and direction caps
- peak-drawdown hard lock
- loss cooldown and losing-streak cooldown
- estimator fail-closed behavior

Safety boundary
---------------
This module does NOT:
- connect to MT5
- send orders
- modify positions
- modify SL/TP
- alter structural stops
- modify trade_ready
- modify production RiskEngine
- authorize live execution

Every row/result has live_authorized = False.
"""

from __future__ import annotations

import importlib
import math
from dataclasses import dataclass
from typing import Any, Iterable


broker_module: Any = importlib.import_module(
    "02_AI.Shadow.broker_aware_risk_engine"
)
friction_module: Any = importlib.import_module(
    "02_AI.Shadow.execution_friction_model"
)
planner_module: Any = importlib.import_module(
    "02_AI.Shadow.bootstrap_compounding_planner"
)
adapter_module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_account_state_adapter"
)
admission_module: Any = importlib.import_module(
    "02_AI.Shadow.execution_aware_compounding_admission"
)
reconciliation_module: Any = importlib.import_module(
    "02_AI.Shadow.risk_mode_basket_reconciliation"
)
protection_module: Any = importlib.import_module(
    "02_AI.Shadow.account_protection_guard"
)


BrokerAwareRiskEngine: Any = broker_module.BrokerAwareRiskEngine
BrokerRiskPolicy: Any = broker_module.BrokerRiskPolicy
ExecutionFrictionModel: Any = friction_module.ExecutionFrictionModel
ExecutionFrictionPolicy: Any = friction_module.ExecutionFrictionPolicy
BootstrapCompoundingPlanner: Any = planner_module.BootstrapCompoundingPlanner
BootstrapCompoundingPolicy: Any = planner_module.BootstrapCompoundingPolicy
CompoundingAccountStateAdapter: Any = adapter_module.CompoundingAccountStateAdapter
ExecutionAwareCompoundingAdmissionEngine: Any = (
    admission_module.ExecutionAwareCompoundingAdmissionEngine
)
RiskModeBasketReconciliationEngine: Any = (
    reconciliation_module.RiskModeBasketReconciliationEngine
)
AccountProtectionGuard: Any = protection_module.AccountProtectionGuard
AccountProtectionPolicy: Any = protection_module.AccountProtectionPolicy


@dataclass(frozen=True)
class BrokerExecutionStressCalibration:
    bid_price: float = 4318.705
    point: float = 0.001
    tick_size: float = 0.001
    volume_min: float = 0.01
    volume_max: float = 200.0
    volume_step: float = 0.01
    stops_level_points: float = 0.0
    margin_per_min_volume: float = 2.16


@dataclass(frozen=True)
class BrokerExecutionStressScenario:
    scenario_id: str
    balance: float
    equity: float
    free_margin: float
    spread_points: float
    stop_distance_price: float
    direction: str = "LONG"
    account_margin_used: float = 0.0
    requested_risk_percent: float | None = None
    estimated_slippage_price: float = 0.0
    estimated_slippage_cost: float = 0.0
    estimated_commission_cost: float = 0.0
    margin_per_min_volume: float = 2.16
    loss_estimator_behavior: str = "NORMAL"
    margin_estimator_behavior: str = "NORMAL"
    spread_estimator_behavior: str = "NORMAL"


@dataclass(frozen=True)
class BrokerExecutionStressRow:
    valid: bool
    reason: str
    mode: str
    version: str
    live_authorized: bool

    scenario_id: str
    balance: float
    equity: float
    free_margin: float
    spread_points: float
    spread_price: float
    stop_distance_price: float
    direction: str

    expected_stop_loss: float
    structural_stop_observable: bool
    structural_stop_preserved: bool

    risk_valid: bool
    risk_reason: str
    risk_mode: str
    selected_volume: float
    minimum_volume_loss: float
    estimated_stop_loss_amount: float
    actual_risk_percent: float
    margin_required: float
    margin_percent_of_free: float
    raw_spread_cost: float

    friction_invoked: bool
    friction_valid: bool
    execution_feasible: bool
    friction_reason: str
    friction_violations: tuple[str, ...]
    total_friction_cost: float
    all_in_adverse_loss: float
    spread_to_stop_distance_ratio: float
    total_friction_to_stop_risk_ratio: float
    all_in_loss_to_budget_ratio: float

    admission_invoked: bool
    admission_valid: bool
    admitted: bool
    admission_reason: str
    account_reason: str
    planner_basket_mode: str

    reconciliation_invoked: bool
    reconciliation_valid: bool
    reconciled: bool
    reconciliation_reason: str
    effective_basket_mode: str
    regime_override_required: bool

    final_new_exposure_feasible: bool
    shadow_boundary_intact: bool

    risk_plan: Any
    admission_result: Any
    reconciliation_result: Any


@dataclass(frozen=True)
class AddonStressScenario:
    scenario_id: str
    balance: float = 100.0
    equity: float = 100.0
    free_margin: float = 100.0
    spread_points: float = 50.0
    stop_distance_price: float = 0.50
    direction: str = "LONG"
    account_margin_used: float = 2.16
    existing_legs: int = 1
    existing_direction: str = "LONG"
    existing_volume: float = 0.01
    existing_projected_loss: float = 0.50
    existing_basket_margin: float = 2.16
    existing_spread_cost: float = 0.05
    existing_floating_profit: float = 0.125
    first_leg_initial_risk: float = 0.50


@dataclass(frozen=True)
class AddonStressRow:
    valid: bool
    reason: str
    mode: str
    version: str
    live_authorized: bool

    scenario_id: str
    risk_valid: bool
    risk_reason: str
    risk_mode: str
    selected_volume: float

    admission_invoked: bool
    admission_valid: bool
    admitted: bool
    admission_reason: str
    account_reason: str
    planner_basket_mode: str
    planner_total_legs: int
    planner_total_volume: float
    planner_total_projected_loss: float
    planner_total_margin: float
    planner_total_spread_cost: float

    reconciliation_invoked: bool
    reconciliation_valid: bool
    reconciled: bool
    reconciliation_reason: str
    effective_basket_mode: str
    effective_loss_cap: float
    effective_margin_cap_amount: float
    regime_override_required: bool

    final_addon_feasible: bool
    shadow_boundary_intact: bool

    risk_plan: Any
    admission_result: Any
    reconciliation_result: Any


@dataclass(frozen=True)
class ProtectionCloseEvent:
    realized_pnl: float
    equity_after_close: float
    bar: int


@dataclass(frozen=True)
class ProtectionStressScenario:
    scenario_id: str
    starting_equity: float
    assessment_equity: float
    assessment_bar: int
    peak_equity: float | None = None
    peak_bar: int = 1
    close_events: tuple[ProtectionCloseEvent, ...] = ()
    recovery_equity: float | None = None
    recovery_bar: int | None = None


@dataclass(frozen=True)
class ProtectionStressRow:
    valid: bool
    reason: str
    mode: str
    version: str
    live_authorized: bool

    scenario_id: str
    assessment_valid: bool
    exposure_allowed: bool
    assessment_reason: str
    peak_equity: float
    current_equity: float
    current_drawdown_percent: float
    max_observed_drawdown_percent: float
    consecutive_losses: int
    cooldown_until_bar: int
    cooldown_remaining_bars: int
    hard_locked: bool
    hard_lock_reason: str

    recovery_invoked: bool
    recovery_valid: bool
    recovery_exposure_allowed: bool
    recovery_reason: str
    recovery_hard_locked: bool

    shadow_boundary_intact: bool
    assessment: Any
    recovery_assessment: Any


@dataclass(frozen=True)
class BrokerExecutionStressSuiteResult:
    valid: bool
    reason: str
    mode: str
    version: str
    live_authorized: bool

    market_grid: tuple[BrokerExecutionStressRow, ...]
    transition_matrix: tuple[BrokerExecutionStressRow, ...]
    account_matrix: tuple[BrokerExecutionStressRow, ...]
    fail_closed_matrix: tuple[BrokerExecutionStressRow, ...]
    addon_matrix: tuple[AddonStressRow, ...]
    protection_matrix: tuple[ProtectionStressRow, ...]

    total_rows: int
    final_single_leg_pass_count: int
    final_addon_pass_count: int
    protection_allowed_count: int
    shadow_boundary_intact: bool


class BrokerExecutionStressMatrix:
    VERSION = "1.0"
    MODE = "SHADOW_BROKER_EXECUTION_STRESS_MATRIX_ONLY"

    DEFAULT_SPREAD_POINTS = (200.0, 260.0, 350.0, 500.0)
    DEFAULT_STOP_DISTANCES = (0.30, 0.40, 0.50, 0.60, 1.00)

    _EPSILON = 1e-8

    def __init__(
        self,
        *,
        calibration: BrokerExecutionStressCalibration | None = None,
        broker_policy: Any | None = None,
        friction_policy: Any | None = None,
        basket_policy: Any | None = None,
        protection_policy: Any | None = None,
    ) -> None:
        self.calibration = (
            calibration
            if calibration is not None
            else BrokerExecutionStressCalibration()
        )
        self.broker_policy = (
            broker_policy
            if broker_policy is not None
            else BrokerRiskPolicy()
        )
        self.friction_policy = (
            friction_policy
            if friction_policy is not None
            else ExecutionFrictionPolicy()
        )
        self.basket_policy = (
            basket_policy
            if basket_policy is not None
            else BootstrapCompoundingPolicy(
                compounding_enabled=True,
                allow_initial_multi_leg=False,
            )
        )
        self.protection_policy = (
            protection_policy
            if protection_policy is not None
            else AccountProtectionPolicy()
        )

        self.risk_engine = BrokerAwareRiskEngine(
            self.broker_policy
        )
        self.friction_model = ExecutionFrictionModel(
            self.friction_policy
        )
        self.basket_planner = BootstrapCompoundingPlanner(
            self.basket_policy
        )
        self.account_adapter = CompoundingAccountStateAdapter(
            planner=self.basket_planner
        )
        self.admission_engine = ExecutionAwareCompoundingAdmissionEngine(
            friction_model=self.friction_model,
            adapter=self.account_adapter,
        )
        self.reconciliation_engine = RiskModeBasketReconciliationEngine(
            policy=self.basket_policy
        )
        self.protection_guard = AccountProtectionGuard(
            self.protection_policy
        )

    @staticmethod
    def _number(value: float | int | None) -> float:
        try:
            resolved = float(value)
        except (TypeError, ValueError):
            return math.nan
        return resolved if math.isfinite(resolved) else math.nan

    @staticmethod
    def _behavior(value: str) -> str:
        return str(value).strip().upper()

    @staticmethod
    def _live(value: Any) -> bool:
        return bool(
            getattr(
                value,
                "live_authorized",
                False,
            )
        )

    def _estimator(
        self,
        *,
        behavior: str,
        normal_value: Any,
    ) -> Any:
        resolved = self._behavior(behavior)

        if resolved == "NORMAL":
            return normal_value

        if resolved == "NONE":
            return lambda volume: None

        if resolved == "NAN":
            return lambda volume: math.nan

        if resolved == "RAISE":
            def raise_estimator(volume: float) -> float:
                raise RuntimeError("stress estimator failure")
            return raise_estimator

        return lambda volume: None

    def _market_prices(
        self,
        *,
        spread_points: float,
        stop_distance_price: float,
        direction: str,
    ) -> tuple[float, float, float]:
        spread_price = (
            spread_points
            *
            self.calibration.point
        )
        bid = self.calibration.bid_price
        ask = bid + spread_price

        normalized_direction = str(direction).strip().upper()
        if normalized_direction in {"SHORT", "SELL", "BEARISH"}:
            stop_loss = bid + stop_distance_price
        else:
            stop_loss = ask - stop_distance_price

        return bid, ask, stop_loss

    def _risk_plan(
        self,
        scenario: BrokerExecutionStressScenario | AddonStressScenario,
    ) -> Any:
        spread_points = self._number(scenario.spread_points)
        stop_distance = self._number(scenario.stop_distance_price)
        margin_per_min = self._number(
            getattr(
                scenario,
                "margin_per_min_volume",
                self.calibration.margin_per_min_volume,
            )
        )

        bid, ask, stop_loss = self._market_prices(
            spread_points=spread_points,
            stop_distance_price=stop_distance,
            direction=scenario.direction,
        )

        spread_price = (
            spread_points
            *
            self.calibration.point
        )

        def normal_loss(volume: float) -> float:
            return (
                stop_distance
                *
                (
                    volume
                    /
                    self.calibration.volume_min
                )
            )

        def normal_margin(volume: float) -> float:
            return (
                margin_per_min
                *
                (
                    volume
                    /
                    self.calibration.volume_min
                )
            )

        def normal_spread(volume: float) -> float:
            return (
                spread_price
                *
                (
                    volume
                    /
                    self.calibration.volume_min
                )
            )

        loss_estimator = self._estimator(
            behavior=getattr(
                scenario,
                "loss_estimator_behavior",
                "NORMAL",
            ),
            normal_value=normal_loss,
        )
        margin_estimator = self._estimator(
            behavior=getattr(
                scenario,
                "margin_estimator_behavior",
                "NORMAL",
            ),
            normal_value=normal_margin,
        )
        spread_estimator = self._estimator(
            behavior=getattr(
                scenario,
                "spread_estimator_behavior",
                "NORMAL",
            ),
            normal_value=normal_spread,
        )

        return self.risk_engine.plan(
            direction=scenario.direction,
            account_balance=scenario.balance,
            account_equity=scenario.equity,
            free_margin=scenario.free_margin,
            bid=bid,
            ask=ask,
            stop_loss=stop_loss,
            point=self.calibration.point,
            tick_size=self.calibration.tick_size,
            volume_min=self.calibration.volume_min,
            volume_max=self.calibration.volume_max,
            volume_step=self.calibration.volume_step,
            stops_level_points=self.calibration.stops_level_points,
            loss_estimator=loss_estimator,
            margin_estimator=margin_estimator,
            spread_cost_estimator=spread_estimator,
            requested_risk_percent=getattr(
                scenario,
                "requested_risk_percent",
                None,
            ),
        )

    def _single_row(
        self,
        *,
        scenario: BrokerExecutionStressScenario,
        risk_plan: Any,
        admission_result: Any = None,
        reconciliation_result: Any = None,
    ) -> BrokerExecutionStressRow:
        spread_price = (
            float(scenario.spread_points)
            *
            self.calibration.point
        )
        bid, ask, expected_stop = self._market_prices(
            spread_points=float(scenario.spread_points),
            stop_distance_price=float(scenario.stop_distance_price),
            direction=scenario.direction,
        )
        del bid, ask

        risk_valid = bool(getattr(risk_plan, "valid", False))
        risk_stop = self._number(getattr(risk_plan, "stop_loss", 0.0))
        structural_stop_observable = (
            math.isfinite(risk_stop)
            and
            risk_stop > 0.0
        )
        structural_stop_preserved = (
            structural_stop_observable
            and
            abs(risk_stop - expected_stop) <= self._EPSILON
        )

        friction = getattr(
            admission_result,
            "friction_assessment",
            None,
        )
        account_plan = getattr(
            admission_result,
            "account_plan",
            None,
        )
        basket_plan = getattr(
            account_plan,
            "basket_plan",
            None,
        )

        admission_invoked = admission_result is not None
        reconciliation_invoked = reconciliation_result is not None

        admitted = bool(getattr(admission_result, "admitted", False))
        reconciled = bool(getattr(reconciliation_result, "reconciled", False))

        final_feasible = (
            risk_valid
            and
            admitted
            and
            reconciled
        )

        shadow_boundary_intact = not any(
            (
                self._live(risk_plan),
                self._live(friction),
                self._live(admission_result),
                self._live(account_plan),
                self._live(basket_plan),
                self._live(reconciliation_result),
            )
        )

        if final_feasible:
            reason = "PASS_FINAL_NEW_EXPOSURE_STRESS"
        elif not risk_valid:
            reason = "RISK_PLAN_REJECTED"
        elif not admitted:
            reason = "ADMISSION_REJECTED"
        elif not reconciled:
            reason = "RECONCILIATION_REJECTED"
        else:
            reason = "STRESS_REJECTED"

        return BrokerExecutionStressRow(
            valid=True,
            reason=reason,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            scenario_id=str(scenario.scenario_id),
            balance=float(scenario.balance),
            equity=float(scenario.equity),
            free_margin=float(scenario.free_margin),
            spread_points=float(scenario.spread_points),
            spread_price=round(spread_price, 8),
            stop_distance_price=float(scenario.stop_distance_price),
            direction=str(scenario.direction).strip().upper(),
            expected_stop_loss=round(expected_stop, 8),
            structural_stop_observable=structural_stop_observable,
            structural_stop_preserved=structural_stop_preserved,
            risk_valid=risk_valid,
            risk_reason=str(getattr(risk_plan, "reason", "")),
            risk_mode=str(getattr(risk_plan, "risk_mode", "")),
            selected_volume=float(getattr(risk_plan, "selected_volume", 0.0)),
            minimum_volume_loss=float(getattr(risk_plan, "minimum_volume_loss", 0.0)),
            estimated_stop_loss_amount=float(
                getattr(risk_plan, "estimated_stop_loss_amount", 0.0)
            ),
            actual_risk_percent=float(getattr(risk_plan, "actual_risk_percent", 0.0)),
            margin_required=float(getattr(risk_plan, "margin_required", 0.0)),
            margin_percent_of_free=float(
                getattr(risk_plan, "margin_percent_of_free", 0.0)
            ),
            raw_spread_cost=float(getattr(risk_plan, "spread_cost", 0.0)),
            friction_invoked=friction is not None,
            friction_valid=bool(getattr(friction, "valid", False)),
            execution_feasible=bool(
                getattr(friction, "execution_feasible", False)
            ),
            friction_reason=str(getattr(friction, "reason", "")),
            friction_violations=tuple(getattr(friction, "violations", ())),
            total_friction_cost=float(getattr(friction, "total_friction_cost", 0.0)),
            all_in_adverse_loss=float(getattr(friction, "all_in_adverse_loss", 0.0)),
            spread_to_stop_distance_ratio=float(
                getattr(friction, "spread_to_stop_distance_ratio", 0.0)
            ),
            total_friction_to_stop_risk_ratio=float(
                getattr(friction, "total_friction_to_stop_risk_ratio", 0.0)
            ),
            all_in_loss_to_budget_ratio=float(
                getattr(friction, "all_in_loss_to_budget_ratio", 0.0)
            ),
            admission_invoked=admission_invoked,
            admission_valid=bool(getattr(admission_result, "valid", False)),
            admitted=admitted,
            admission_reason=str(getattr(admission_result, "reason", "")),
            account_reason=str(getattr(admission_result, "account_reason", "")),
            planner_basket_mode=str(getattr(basket_plan, "basket_mode", "")),
            reconciliation_invoked=reconciliation_invoked,
            reconciliation_valid=bool(
                getattr(reconciliation_result, "valid", False)
            ),
            reconciled=reconciled,
            reconciliation_reason=str(
                getattr(reconciliation_result, "reason", "")
            ),
            effective_basket_mode=str(
                getattr(reconciliation_result, "effective_basket_mode", "")
            ),
            regime_override_required=bool(
                getattr(reconciliation_result, "regime_override_required", False)
            ),
            final_new_exposure_feasible=final_feasible,
            shadow_boundary_intact=shadow_boundary_intact,
            risk_plan=risk_plan,
            admission_result=admission_result,
            reconciliation_result=reconciliation_result,
        )

    def evaluate_single(
        self,
        scenario: BrokerExecutionStressScenario,
    ) -> BrokerExecutionStressRow:
        risk_plan = self._risk_plan(scenario)

        if not bool(getattr(risk_plan, "valid", False)):
            return self._single_row(
                scenario=scenario,
                risk_plan=risk_plan,
            )

        admission = self.admission_engine.admit(
            risk_plan=risk_plan,
            leg_id=str(scenario.scenario_id),
            account_margin_used=scenario.account_margin_used,
            estimated_slippage_price=scenario.estimated_slippage_price,
            estimated_slippage_cost=scenario.estimated_slippage_cost,
            estimated_commission_cost=scenario.estimated_commission_cost,
            existing_legs=0,
            existing_direction="",
            existing_volume=0.0,
            existing_projected_loss=0.0,
            existing_basket_margin=0.0,
            existing_spread_cost=0.0,
            existing_floating_profit=0.0,
            first_leg_initial_risk=0.0,
        )

        if not bool(getattr(admission, "admitted", False)):
            return self._single_row(
                scenario=scenario,
                risk_plan=risk_plan,
                admission_result=admission,
            )

        reconciliation = self.reconciliation_engine.evaluate(
            admission_result=admission
        )

        return self._single_row(
            scenario=scenario,
            risk_plan=risk_plan,
            admission_result=admission,
            reconciliation_result=reconciliation,
        )

    def spread_stop_grid(
        self,
        *,
        balance: float = 63.35,
        equity: float | None = None,
        free_margin: float | None = None,
        spread_points: Iterable[float] | None = None,
        stop_distances: Iterable[float] | None = None,
    ) -> tuple[BrokerExecutionStressRow, ...]:
        resolved_equity = balance if equity is None else equity
        resolved_free_margin = (
            resolved_equity
            if free_margin is None
            else free_margin
        )
        spreads = tuple(
            self.DEFAULT_SPREAD_POINTS
            if spread_points is None
            else spread_points
        )
        stops = tuple(
            self.DEFAULT_STOP_DISTANCES
            if stop_distances is None
            else stop_distances
        )

        rows: list[BrokerExecutionStressRow] = []
        for spread in spreads:
            for stop in stops:
                rows.append(
                    self.evaluate_single(
                        BrokerExecutionStressScenario(
                            scenario_id=(
                                f"GRID_B{balance:g}_S{spread:g}_D{stop:g}"
                            ),
                            balance=balance,
                            equity=resolved_equity,
                            free_margin=resolved_free_margin,
                            spread_points=spread,
                            stop_distance_price=stop,
                        )
                    )
                )
        return tuple(rows)

    def default_transition_matrix(self) -> tuple[BrokerExecutionStressRow, ...]:
        scenarios = (
            BrokerExecutionStressScenario(
                scenario_id="MICRO_3_STOP_030",
                balance=3.0,
                equity=3.0,
                free_margin=3.0,
                spread_points=100.0,
                stop_distance_price=0.30,
            ),
            BrokerExecutionStressScenario(
                scenario_id="MICRO_20_STOP_030",
                balance=20.0,
                equity=20.0,
                free_margin=20.0,
                spread_points=100.0,
                stop_distance_price=0.30,
            ),
            BrokerExecutionStressScenario(
                scenario_id="STANDARD_10_STOP_010_FRICTION_BLOCK",
                balance=10.0,
                equity=10.0,
                free_margin=10.0,
                spread_points=50.0,
                stop_distance_price=0.10,
            ),
            BrokerExecutionStressScenario(
                scenario_id="STANDARD_20_STOP_010_OVERRIDE_PASS",
                balance=20.0,
                equity=20.0,
                free_margin=20.0,
                spread_points=50.0,
                stop_distance_price=0.10,
            ),
            BrokerExecutionStressScenario(
                scenario_id="TRANSITION_GAP_21_STOP_030",
                balance=21.0,
                equity=21.0,
                free_margin=21.0,
                spread_points=50.0,
                stop_distance_price=0.30,
            ),
            BrokerExecutionStressScenario(
                scenario_id="STANDARD_RISK_30_EXECUTION_BLOCK",
                balance=30.0,
                equity=30.0,
                free_margin=30.0,
                spread_points=50.0,
                stop_distance_price=0.30,
            ),
            BrokerExecutionStressScenario(
                scenario_id="STANDARD_EXECUTION_35_PASS",
                balance=35.0,
                equity=35.0,
                free_margin=35.0,
                spread_points=50.0,
                stop_distance_price=0.30,
            ),
        )
        return tuple(
            self.evaluate_single(scenario)
            for scenario in scenarios
        )

    def default_account_matrix(self) -> tuple[BrokerExecutionStressRow, ...]:
        scenarios = (
            BrokerExecutionStressScenario(
                scenario_id="EQUITY_DIVERGENCE",
                balance=100.0,
                equity=80.0,
                free_margin=80.0,
                spread_points=50.0,
                stop_distance_price=0.50,
            ),
            BrokerExecutionStressScenario(
                scenario_id="LOW_MARGIN_STANDARD_BLOCK",
                balance=63.35,
                equity=63.35,
                free_margin=8.0,
                spread_points=50.0,
                stop_distance_price=0.50,
            ),
            BrokerExecutionStressScenario(
                scenario_id="LOW_MARGIN_MICRO_BLOCK",
                balance=3.0,
                equity=3.0,
                free_margin=2.0,
                spread_points=50.0,
                stop_distance_price=0.30,
            ),
            BrokerExecutionStressScenario(
                scenario_id="CURRENT_BROKER_STYLE_63_SPREAD260_STOP050",
                balance=63.35,
                equity=63.35,
                free_margin=63.35,
                spread_points=260.0,
                stop_distance_price=0.50,
            ),
            BrokerExecutionStressScenario(
                scenario_id="STANDARD_VOLUME_GROWTH_BASKET_CAP",
                balance=1000.0,
                equity=1000.0,
                free_margin=1000.0,
                spread_points=50.0,
                stop_distance_price=0.30,
            ),
        )
        return tuple(
            self.evaluate_single(scenario)
            for scenario in scenarios
        )

    def default_fail_closed_matrix(self) -> tuple[BrokerExecutionStressRow, ...]:
        base = dict(
            balance=20.0,
            equity=20.0,
            free_margin=20.0,
            spread_points=50.0,
            stop_distance_price=0.30,
        )
        scenarios = (
            BrokerExecutionStressScenario(
                scenario_id="FAIL_INVALID_DIRECTION",
                direction="SIDEWAYS",
                **base,
            ),
            BrokerExecutionStressScenario(
                scenario_id="FAIL_LOSS_ESTIMATOR",
                loss_estimator_behavior="NONE",
                **base,
            ),
            BrokerExecutionStressScenario(
                scenario_id="FAIL_MARGIN_ESTIMATOR",
                margin_estimator_behavior="RAISE",
                **base,
            ),
            BrokerExecutionStressScenario(
                scenario_id="FAIL_SPREAD_ESTIMATOR",
                spread_estimator_behavior="NAN",
                **base,
            ),
            BrokerExecutionStressScenario(
                scenario_id="FAIL_ZERO_EQUITY",
                balance=20.0,
                equity=0.0,
                free_margin=20.0,
                spread_points=50.0,
                stop_distance_price=0.30,
            ),
            BrokerExecutionStressScenario(
                scenario_id="FAIL_ZERO_FREE_MARGIN",
                balance=20.0,
                equity=20.0,
                free_margin=0.0,
                spread_points=50.0,
                stop_distance_price=0.30,
            ),
            BrokerExecutionStressScenario(
                scenario_id="FAIL_NEGATIVE_REQUESTED_RISK",
                requested_risk_percent=-1.0,
                **base,
            ),
            BrokerExecutionStressScenario(
                scenario_id="FAIL_NEGATIVE_SPREAD",
                balance=20.0,
                equity=20.0,
                free_margin=20.0,
                spread_points=-50.0,
                stop_distance_price=0.30,
            ),
        )
        return tuple(
            self.evaluate_single(scenario)
            for scenario in scenarios
        )

    def _addon_row(
        self,
        *,
        scenario: AddonStressScenario,
        risk_plan: Any,
        admission_result: Any = None,
        reconciliation_result: Any = None,
    ) -> AddonStressRow:
        account_plan = getattr(admission_result, "account_plan", None)
        basket_plan = getattr(account_plan, "basket_plan", None)

        risk_valid = bool(getattr(risk_plan, "valid", False))
        admitted = bool(getattr(admission_result, "admitted", False))
        reconciled = bool(getattr(reconciliation_result, "reconciled", False))
        final_feasible = risk_valid and admitted and reconciled

        shadow_boundary_intact = not any(
            (
                self._live(risk_plan),
                self._live(admission_result),
                self._live(account_plan),
                self._live(basket_plan),
                self._live(reconciliation_result),
            )
        )

        if final_feasible:
            reason = "PASS_FINAL_ADDON_STRESS"
        elif not risk_valid:
            reason = "RISK_PLAN_REJECTED"
        elif not admitted:
            reason = "ADMISSION_REJECTED"
        elif not reconciled:
            reason = "RECONCILIATION_REJECTED"
        else:
            reason = "ADDON_STRESS_REJECTED"

        return AddonStressRow(
            valid=True,
            reason=reason,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            scenario_id=scenario.scenario_id,
            risk_valid=risk_valid,
            risk_reason=str(getattr(risk_plan, "reason", "")),
            risk_mode=str(getattr(risk_plan, "risk_mode", "")),
            selected_volume=float(getattr(risk_plan, "selected_volume", 0.0)),
            admission_invoked=admission_result is not None,
            admission_valid=bool(getattr(admission_result, "valid", False)),
            admitted=admitted,
            admission_reason=str(getattr(admission_result, "reason", "")),
            account_reason=str(getattr(admission_result, "account_reason", "")),
            planner_basket_mode=str(getattr(basket_plan, "basket_mode", "")),
            planner_total_legs=int(getattr(basket_plan, "total_legs", 0)),
            planner_total_volume=float(getattr(basket_plan, "total_volume", 0.0)),
            planner_total_projected_loss=float(
                getattr(basket_plan, "total_projected_loss", 0.0)
            ),
            planner_total_margin=float(getattr(basket_plan, "total_margin", 0.0)),
            planner_total_spread_cost=float(
                getattr(basket_plan, "total_spread_cost", 0.0)
            ),
            reconciliation_invoked=reconciliation_result is not None,
            reconciliation_valid=bool(
                getattr(reconciliation_result, "valid", False)
            ),
            reconciled=reconciled,
            reconciliation_reason=str(
                getattr(reconciliation_result, "reason", "")
            ),
            effective_basket_mode=str(
                getattr(reconciliation_result, "effective_basket_mode", "")
            ),
            effective_loss_cap=float(
                getattr(reconciliation_result, "effective_loss_cap", 0.0)
            ),
            effective_margin_cap_amount=float(
                getattr(reconciliation_result, "effective_margin_cap_amount", 0.0)
            ),
            regime_override_required=bool(
                getattr(reconciliation_result, "regime_override_required", False)
            ),
            final_addon_feasible=final_feasible,
            shadow_boundary_intact=shadow_boundary_intact,
            risk_plan=risk_plan,
            admission_result=admission_result,
            reconciliation_result=reconciliation_result,
        )

    def evaluate_addon(
        self,
        scenario: AddonStressScenario,
    ) -> AddonStressRow:
        risk_plan = self._risk_plan(scenario)

        if not bool(getattr(risk_plan, "valid", False)):
            return self._addon_row(
                scenario=scenario,
                risk_plan=risk_plan,
            )

        admission = self.admission_engine.admit(
            risk_plan=risk_plan,
            leg_id=scenario.scenario_id,
            account_margin_used=scenario.account_margin_used,
            existing_legs=scenario.existing_legs,
            existing_direction=scenario.existing_direction,
            existing_volume=scenario.existing_volume,
            existing_projected_loss=scenario.existing_projected_loss,
            existing_basket_margin=scenario.existing_basket_margin,
            existing_spread_cost=scenario.existing_spread_cost,
            existing_floating_profit=scenario.existing_floating_profit,
            first_leg_initial_risk=scenario.first_leg_initial_risk,
        )

        if not bool(getattr(admission, "admitted", False)):
            return self._addon_row(
                scenario=scenario,
                risk_plan=risk_plan,
                admission_result=admission,
            )

        reconciliation = self.reconciliation_engine.evaluate(
            admission_result=admission
        )

        return self._addon_row(
            scenario=scenario,
            risk_plan=risk_plan,
            admission_result=admission,
            reconciliation_result=reconciliation,
        )

    def default_addon_matrix(self) -> tuple[AddonStressRow, ...]:
        scenarios = (
            AddonStressScenario(
                scenario_id="ADD_PASS_AT_025R",
            ),
            AddonStressScenario(
                scenario_id="ADD_BLOCK_BELOW_025R",
                existing_floating_profit=0.124,
            ),
            AddonStressScenario(
                scenario_id="ADD_BLOCK_MAX_LEGS",
                existing_legs=3,
                existing_volume=0.03,
                existing_projected_loss=1.50,
                existing_basket_margin=6.48,
                existing_spread_cost=0.15,
                account_margin_used=6.48,
                existing_floating_profit=0.50,
            ),
            AddonStressScenario(
                scenario_id="ADD_BLOCK_MAX_VOLUME",
                existing_legs=2,
                existing_volume=0.03,
                existing_projected_loss=1.00,
                existing_basket_margin=4.32,
                existing_spread_cost=0.10,
                account_margin_used=4.32,
                existing_floating_profit=0.50,
            ),
            AddonStressScenario(
                scenario_id="ADD_BLOCK_STANDARD_BASKET_LOSS",
                existing_projected_loss=1.60,
                existing_floating_profit=0.50,
            ),
            AddonStressScenario(
                scenario_id="ADD_BLOCK_STANDARD_BASKET_MARGIN",
                free_margin=60.0,
                account_margin_used=34.0,
                existing_basket_margin=34.0,
                existing_floating_profit=0.50,
            ),
            AddonStressScenario(
                scenario_id="ADD_BLOCK_STANDARD_BASKET_SPREAD",
                existing_spread_cost=1.98,
                existing_floating_profit=0.50,
            ),
            AddonStressScenario(
                scenario_id="ADD_BLOCK_DIRECTION_MISMATCH",
                existing_direction="SHORT",
                existing_floating_profit=0.50,
            ),
            AddonStressScenario(
                scenario_id="ADD_SMALL_STANDARD_OVERRIDE_PASS",
                balance=20.0,
                equity=20.0,
                free_margin=20.0,
                spread_points=50.0,
                stop_distance_price=0.10,
                account_margin_used=2.16,
                existing_projected_loss=0.10,
                existing_spread_cost=0.05,
                existing_floating_profit=0.025,
                first_leg_initial_risk=0.10,
            ),
            AddonStressScenario(
                scenario_id="ADD_SMALL_STANDARD_RECONCILIATION_BLOCK",
                balance=20.0,
                equity=20.0,
                free_margin=20.0,
                spread_points=50.0,
                stop_distance_price=0.10,
                account_margin_used=2.16,
                existing_projected_loss=0.35,
                existing_spread_cost=0.05,
                existing_floating_profit=0.025,
                first_leg_initial_risk=0.10,
            ),
            AddonStressScenario(
                scenario_id="ADD_SMALL_STANDARD_RECONCILIATION_MARGIN_BLOCK",
                balance=20.0,
                equity=20.0,
                free_margin=20.0,
                spread_points=50.0,
                stop_distance_price=0.10,
                account_margin_used=6.0,
                existing_projected_loss=0.10,
                existing_basket_margin=6.0,
                existing_spread_cost=0.05,
                existing_floating_profit=0.025,
                first_leg_initial_risk=0.10,
            ),
            AddonStressScenario(
                scenario_id="ADD_SMALL_STANDARD_RECONCILIATION_SPREAD_BLOCK",
                balance=20.0,
                equity=20.0,
                free_margin=20.0,
                spread_points=50.0,
                stop_distance_price=0.10,
                account_margin_used=2.16,
                existing_projected_loss=0.10,
                existing_spread_cost=0.39,
                existing_floating_profit=0.025,
                first_leg_initial_risk=0.10,
            ),
        )
        return tuple(
            self.evaluate_addon(scenario)
            for scenario in scenarios
        )

    def evaluate_protection(
        self,
        scenario: ProtectionStressScenario,
    ) -> ProtectionStressRow:
        try:
            state = self.protection_guard.initial_state(
                equity=scenario.starting_equity,
                current_bar=0,
            )
        except ValueError:
            return ProtectionStressRow(
                valid=False,
                reason="INVALID_PROTECTION_INITIAL_STATE",
                mode=self.MODE,
                version=self.VERSION,
                live_authorized=False,
                scenario_id=scenario.scenario_id,
                assessment_valid=False,
                exposure_allowed=False,
                assessment_reason="",
                peak_equity=0.0,
                current_equity=0.0,
                current_drawdown_percent=0.0,
                max_observed_drawdown_percent=0.0,
                consecutive_losses=0,
                cooldown_until_bar=0,
                cooldown_remaining_bars=0,
                hard_locked=False,
                hard_lock_reason="",
                recovery_invoked=False,
                recovery_valid=False,
                recovery_exposure_allowed=False,
                recovery_reason="",
                recovery_hard_locked=False,
                shadow_boundary_intact=True,
                assessment=None,
                recovery_assessment=None,
            )

        if scenario.peak_equity is not None:
            peak_transition = self.protection_guard.observe_equity(
                state=state,
                current_equity=scenario.peak_equity,
                current_bar=scenario.peak_bar,
            )
            if not peak_transition.valid:
                return ProtectionStressRow(
                    valid=False,
                    reason="PEAK_OBSERVATION_REJECTED",
                    mode=self.MODE,
                    version=self.VERSION,
                    live_authorized=False,
                    scenario_id=scenario.scenario_id,
                    assessment_valid=False,
                    exposure_allowed=False,
                    assessment_reason=peak_transition.reason,
                    peak_equity=state.peak_equity,
                    current_equity=state.current_equity,
                    current_drawdown_percent=state.current_drawdown_percent,
                    max_observed_drawdown_percent=state.max_observed_drawdown_percent,
                    consecutive_losses=state.consecutive_losses,
                    cooldown_until_bar=state.cooldown_until_bar,
                    cooldown_remaining_bars=0,
                    hard_locked=state.hard_locked,
                    hard_lock_reason=state.hard_lock_reason,
                    recovery_invoked=False,
                    recovery_valid=False,
                    recovery_exposure_allowed=False,
                    recovery_reason="",
                    recovery_hard_locked=False,
                    shadow_boundary_intact=not self._live(peak_transition),
                    assessment=None,
                    recovery_assessment=None,
                )
            state = peak_transition.state_after

        for event in scenario.close_events:
            transition = self.protection_guard.record_basket_close(
                state=state,
                realized_pnl=event.realized_pnl,
                equity_after_close=event.equity_after_close,
                current_bar=event.bar,
            )
            if not transition.valid:
                return ProtectionStressRow(
                    valid=False,
                    reason="PROTECTION_CLOSE_EVENT_REJECTED",
                    mode=self.MODE,
                    version=self.VERSION,
                    live_authorized=False,
                    scenario_id=scenario.scenario_id,
                    assessment_valid=False,
                    exposure_allowed=False,
                    assessment_reason=transition.reason,
                    peak_equity=state.peak_equity,
                    current_equity=state.current_equity,
                    current_drawdown_percent=state.current_drawdown_percent,
                    max_observed_drawdown_percent=state.max_observed_drawdown_percent,
                    consecutive_losses=state.consecutive_losses,
                    cooldown_until_bar=state.cooldown_until_bar,
                    cooldown_remaining_bars=0,
                    hard_locked=state.hard_locked,
                    hard_lock_reason=state.hard_lock_reason,
                    recovery_invoked=False,
                    recovery_valid=False,
                    recovery_exposure_allowed=False,
                    recovery_reason="",
                    recovery_hard_locked=False,
                    shadow_boundary_intact=not self._live(transition),
                    assessment=None,
                    recovery_assessment=None,
                )
            state = transition.state_after

        assessment = self.protection_guard.assess_new_exposure(
            state=state,
            current_equity=scenario.assessment_equity,
            current_bar=scenario.assessment_bar,
        )

        recovery = None
        if scenario.recovery_equity is not None:
            recovery_bar = (
                scenario.recovery_bar
                if scenario.recovery_bar is not None
                else scenario.assessment_bar + 1
            )
            recovery = self.protection_guard.assess_new_exposure(
                state=assessment.state_after,
                current_equity=scenario.recovery_equity,
                current_bar=recovery_bar,
            )

        shadow_boundary_intact = not any(
            (
                self._live(state),
                self._live(assessment),
                self._live(recovery),
            )
        )

        return ProtectionStressRow(
            valid=True,
            reason=(
                "PASS_PROTECTION_STRESS_EVALUATED"
                if assessment.valid
                else
                "PROTECTION_ASSESSMENT_REJECTED"
            ),
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            scenario_id=scenario.scenario_id,
            assessment_valid=bool(assessment.valid),
            exposure_allowed=bool(assessment.exposure_allowed),
            assessment_reason=str(assessment.reason),
            peak_equity=float(assessment.state_after.peak_equity),
            current_equity=float(assessment.state_after.current_equity),
            current_drawdown_percent=float(assessment.current_drawdown_percent),
            max_observed_drawdown_percent=float(
                assessment.max_observed_drawdown_percent
            ),
            consecutive_losses=int(assessment.consecutive_losses),
            cooldown_until_bar=int(assessment.cooldown_until_bar),
            cooldown_remaining_bars=int(assessment.cooldown_remaining_bars),
            hard_locked=bool(assessment.hard_locked),
            hard_lock_reason=str(assessment.hard_lock_reason),
            recovery_invoked=recovery is not None,
            recovery_valid=bool(getattr(recovery, "valid", False)),
            recovery_exposure_allowed=bool(
                getattr(recovery, "exposure_allowed", False)
            ),
            recovery_reason=str(getattr(recovery, "reason", "")),
            recovery_hard_locked=bool(getattr(recovery, "hard_locked", False)),
            shadow_boundary_intact=shadow_boundary_intact,
            assessment=assessment,
            recovery_assessment=recovery,
        )

    def default_protection_matrix(self) -> tuple[ProtectionStressRow, ...]:
        scenarios = (
            ProtectionStressScenario(
                scenario_id="DD_BELOW_LOCK",
                starting_equity=100.0,
                assessment_equity=90.01,
                assessment_bar=1,
            ),
            ProtectionStressScenario(
                scenario_id="DD_AT_LOCK",
                starting_equity=100.0,
                assessment_equity=90.0,
                assessment_bar=1,
            ),
            ProtectionStressScenario(
                scenario_id="PEAK_BASED_DD_LOCK",
                starting_equity=100.0,
                peak_equity=120.0,
                peak_bar=1,
                assessment_equity=108.0,
                assessment_bar=2,
            ),
            ProtectionStressScenario(
                scenario_id="HARD_LOCK_STICKY_RECOVERY",
                starting_equity=100.0,
                assessment_equity=90.0,
                assessment_bar=1,
                recovery_equity=100.0,
                recovery_bar=2,
            ),
            ProtectionStressScenario(
                scenario_id="LOSS_COOLDOWN_BLOCKED",
                starting_equity=100.0,
                close_events=(
                    ProtectionCloseEvent(-1.0, 99.0, 10),
                ),
                assessment_equity=99.0,
                assessment_bar=14,
            ),
            ProtectionStressScenario(
                scenario_id="LOSS_COOLDOWN_RELEASE",
                starting_equity=100.0,
                close_events=(
                    ProtectionCloseEvent(-1.0, 99.0, 10),
                ),
                assessment_equity=99.0,
                assessment_bar=15,
            ),
            ProtectionStressScenario(
                scenario_id="LOSS_STREAK_COOLDOWN_BLOCKED",
                starting_equity=100.0,
                close_events=(
                    ProtectionCloseEvent(-1.0, 99.0, 10),
                    ProtectionCloseEvent(-1.0, 98.0, 20),
                    ProtectionCloseEvent(-1.0, 97.0, 30),
                ),
                assessment_equity=97.0,
                assessment_bar=59,
            ),
            ProtectionStressScenario(
                scenario_id="LOSS_STREAK_COOLDOWN_RELEASE",
                starting_equity=100.0,
                close_events=(
                    ProtectionCloseEvent(-1.0, 99.0, 10),
                    ProtectionCloseEvent(-1.0, 98.0, 20),
                    ProtectionCloseEvent(-1.0, 97.0, 30),
                ),
                assessment_equity=97.0,
                assessment_bar=60,
            ),
        )
        return tuple(
            self.evaluate_protection(scenario)
            for scenario in scenarios
        )

    def evaluate_default_suite(self) -> BrokerExecutionStressSuiteResult:
        market_grid = self.spread_stop_grid()
        transition_matrix = self.default_transition_matrix()
        account_matrix = self.default_account_matrix()
        fail_closed_matrix = self.default_fail_closed_matrix()
        addon_matrix = self.default_addon_matrix()
        protection_matrix = self.default_protection_matrix()

        single_rows = (
            market_grid
            + transition_matrix
            + account_matrix
            + fail_closed_matrix
        )
        all_rows_valid = all(
            row.valid
            for row in single_rows
        ) and all(
            row.valid
            for row in addon_matrix
        ) and all(
            row.valid
            for row in protection_matrix
        )

        shadow_boundary_intact = all(
            row.live_authorized is False
            and row.shadow_boundary_intact
            for row in single_rows
        ) and all(
            row.live_authorized is False
            and row.shadow_boundary_intact
            for row in addon_matrix
        ) and all(
            row.live_authorized is False
            and row.shadow_boundary_intact
            for row in protection_matrix
        )

        total_rows = (
            len(single_rows)
            + len(addon_matrix)
            + len(protection_matrix)
        )

        return BrokerExecutionStressSuiteResult(
            valid=all_rows_valid and shadow_boundary_intact,
            reason=(
                "OK_BROKER_EXECUTION_STRESS_SUITE"
                if all_rows_valid and shadow_boundary_intact
                else
                "BROKER_EXECUTION_STRESS_SUITE_FAILED"
            ),
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            market_grid=market_grid,
            transition_matrix=transition_matrix,
            account_matrix=account_matrix,
            fail_closed_matrix=fail_closed_matrix,
            addon_matrix=addon_matrix,
            protection_matrix=protection_matrix,
            total_rows=total_rows,
            final_single_leg_pass_count=sum(
                1
                for row in single_rows
                if row.final_new_exposure_feasible
            ),
            final_addon_pass_count=sum(
                1
                for row in addon_matrix
                if row.final_addon_feasible
            ),
            protection_allowed_count=sum(
                1
                for row in protection_matrix
                if row.exposure_allowed
            ),
            shadow_boundary_intact=shadow_boundary_intact,
        )


broker_execution_stress_matrix = BrokerExecutionStressMatrix()