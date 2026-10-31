"""
===============================================================================
Module      : risk_policy_scenario_matrix.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Shadow Cross-Policy Risk Scenario Matrix
===============================================================================

Status
------
SHADOW / RESEARCH / DEMO ONLY.

Purpose
-------
Make the current provisional risk-policy boundaries explicit across account
sizes without changing any existing broker, basket, reconciliation, lifecycle,
or production policy.

This module compares:

    BrokerRiskPolicy
    BootstrapCompoundingPolicy

and exposes the monetary capacity implied by both policies.

Important
---------
This module does NOT decide whether a setup is executable.

BrokerAwareRiskEngine remains STANDARD-first. Therefore a small account can
still use STANDARD_COMPOUND when broker minimum volume satisfies standard hard
limits.

The matrix only reports:

- policy ranges
- risk amounts
- margin capacities
- basket capacities
- spread capacities
- planner label expected from risk base
- whether reconciliation override would be required for each upstream mode

It does NOT replace RiskModeBasketReconciliationEngine.

Safety
------
This module:

- does not connect to MT5
- does not send orders
- does not change structural stops
- does not modify trade_ready
- does not modify production RiskEngine
- does not authorize live execution

Every row/result:

    live_authorized = False
"""

from __future__ import annotations

import importlib
import math
from dataclasses import dataclass
from typing import Any, Iterable


broker_module: Any = importlib.import_module(
    "02_AI.Shadow.broker_aware_risk_engine"
)

planner_module: Any = importlib.import_module(
    "02_AI.Shadow.bootstrap_compounding_planner"
)


BrokerRiskPolicy: Any = (
    broker_module.BrokerRiskPolicy
)

BootstrapCompoundingPolicy: Any = (
    planner_module.BootstrapCompoundingPolicy
)


@dataclass(
    frozen=True,
)
class RiskPolicyScenarioRow:
    valid: bool

    reason: str

    mode: str

    version: str

    live_authorized: bool

    balance: float

    equity: float

    free_margin: float

    risk_base: float

    broker_micro_eligible: bool

    planner_bootstrap_range: bool

    planner_basket_mode_by_risk_base: str

    standard_override_required_if_selected: bool

    micro_override_required_if_selected: bool

    standard_target_risk_percent: float

    standard_hard_single_leg_percent: float

    standard_target_risk_amount: float

    standard_hard_single_leg_amount: float

    standard_broker_margin_cap_percent: float

    standard_broker_margin_cap_amount: float

    standard_broker_spread_hard_cap: float

    standard_basket_hard_loss_percent: float

    standard_basket_loss_cap: float

    standard_basket_margin_cap_percent: float

    standard_basket_margin_cap_amount: float

    standard_basket_spread_cap: float

    micro_hard_single_leg_percent: float

    micro_hard_single_leg_amount: float

    micro_broker_margin_cap_percent: float

    micro_broker_margin_cap_amount: float

    micro_min_balance: float

    micro_max_balance: float

    bootstrap_balance_max: float

    micro_basket_loss_cap: float

    micro_basket_loss_cap_percent_of_risk_base: float

    micro_basket_margin_cap_percent: float

    micro_basket_margin_cap_amount: float

    micro_basket_spread_cap: float

    max_simultaneous_legs: int

    max_total_volume: float

    add_only_after_profit: bool

    minimum_profit_r_before_add: float


@dataclass(
    frozen=True,
)
class RiskPolicyScenarioMatrixResult:
    valid: bool

    reason: str

    mode: str

    version: str

    live_authorized: bool

    policy_alignment_valid: bool

    alignment_violations: tuple[
        str,
        ...,
    ]

    rows: tuple[
        RiskPolicyScenarioRow,
        ...,
    ]


class RiskPolicyScenarioMatrix:
    VERSION = "1.0"

    MODE = (
        "SHADOW_RISK_POLICY_SCENARIO_MATRIX_ONLY"
    )

    MICRO_BASKET_MODE = (
        "MICRO_BOOTSTRAP_BASKET"
    )

    STANDARD_BASKET_MODE = (
        "STANDARD_COMPOUND_BASKET"
    )

    DEFAULT_BALANCES = (
        3.0,
        5.0,
        10.0,
        20.0,
        21.0,
        50.0,
        63.35,
        100.0,
    )

    _EPSILON = 1e-9

    def __init__(
        self,
        *,
        broker_policy: Any | None = None,
        basket_policy: Any | None = None,
    ) -> None:

        self.broker_policy = (
            broker_policy
            if broker_policy is not None
            else BrokerRiskPolicy()
        )

        self.basket_policy = (
            basket_policy
            if basket_policy is not None
            else BootstrapCompoundingPolicy(
                compounding_enabled=True,
                allow_initial_multi_leg=False,
            )
        )

    # =========================================================================
    # Numeric helpers
    # =========================================================================

    @staticmethod
    def _number(
        value: float | int | None,
    ) -> float:

        try:

            result = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return math.nan

        if not math.isfinite(
            result
        ):

            return math.nan

        return result

    @staticmethod
    def _percent(
        numerator: float,
        denominator: float,
    ) -> float:

        if denominator <= 0.0:

            return 0.0

        return (
            numerator
            /
            denominator
            *
            100.0
        )

    @staticmethod
    def _amount(
        base: float,
        percent: float,
    ) -> float:

        return (
            base
            *
            percent
            /
            100.0
        )

    # =========================================================================
    # Policy calculations
    # =========================================================================

    def _bootstrap_loss_cap(
        self,
        risk_base: float,
    ) -> float:

        percentage_amount = (
            risk_base
            *
            self.basket_policy.bootstrap_loss_budget_percent
            /
            100.0
        )

        cap = max(
            self.basket_policy.bootstrap_loss_budget_floor_usd,
            percentage_amount,
        )

        return min(
            cap,
            self.basket_policy.bootstrap_loss_budget_ceiling_usd,
        )

    def alignment_violations(
        self,
    ) -> tuple[
        str,
        ...,
    ]:

        violations: list[
            str
        ] = []

        if (
            abs(
                float(
                    self.broker_policy.micro_max_balance
                )
                -
                float(
                    self.basket_policy.bootstrap_balance_max
                )
            )
            >
            self._EPSILON
        ):

            violations.append(
                "MICRO_BOOTSTRAP_MAX_RANGE_MISMATCH"
            )

        if (
            self.broker_policy.hard_max_risk_percent
            >
            self.basket_policy.standard_basket_hard_loss_percent
            +
            self._EPSILON
        ):

            violations.append(
                "STANDARD_SINGLE_LEG_EXCEEDS_BASKET_CAP"
            )

        if (
            self.broker_policy.target_risk_percent
            >
            self.broker_policy.hard_max_risk_percent
            +
            self._EPSILON
        ):

            violations.append(
                "STANDARD_TARGET_EXCEEDS_HARD_SINGLE_LEG"
            )

        if (
            self.broker_policy.micro_min_balance
            >
            self.broker_policy.micro_max_balance
            +
            self._EPSILON
        ):

            violations.append(
                "MICRO_MIN_EXCEEDS_MICRO_MAX"
            )

        if (
            self.basket_policy.bootstrap_loss_budget_floor_usd
            >
            self.basket_policy.bootstrap_loss_budget_ceiling_usd
            +
            self._EPSILON
        ):

            violations.append(
                "BOOTSTRAP_FLOOR_EXCEEDS_CEILING"
            )

        return tuple(
            violations
        )

    # =========================================================================
    # Invalid row
    # =========================================================================

    def _invalid_row(
        self,
        *,
        reason: str,
        balance: float = 0.0,
        equity: float = 0.0,
        free_margin: float = 0.0,
    ) -> RiskPolicyScenarioRow:

        return RiskPolicyScenarioRow(
            valid=False,
            reason=reason,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            balance=balance,
            equity=equity,
            free_margin=free_margin,
            risk_base=0.0,
            broker_micro_eligible=False,
            planner_bootstrap_range=False,
            planner_basket_mode_by_risk_base="",
            standard_override_required_if_selected=False,
            micro_override_required_if_selected=False,
            standard_target_risk_percent=0.0,
            standard_hard_single_leg_percent=0.0,
            standard_target_risk_amount=0.0,
            standard_hard_single_leg_amount=0.0,
            standard_broker_margin_cap_percent=0.0,
            standard_broker_margin_cap_amount=0.0,
            standard_broker_spread_hard_cap=0.0,
            standard_basket_hard_loss_percent=0.0,
            standard_basket_loss_cap=0.0,
            standard_basket_margin_cap_percent=0.0,
            standard_basket_margin_cap_amount=0.0,
            standard_basket_spread_cap=0.0,
            micro_hard_single_leg_percent=0.0,
            micro_hard_single_leg_amount=0.0,
            micro_broker_margin_cap_percent=0.0,
            micro_broker_margin_cap_amount=0.0,
            micro_min_balance=0.0,
            micro_max_balance=0.0,
            bootstrap_balance_max=0.0,
            micro_basket_loss_cap=0.0,
            micro_basket_loss_cap_percent_of_risk_base=0.0,
            micro_basket_margin_cap_percent=0.0,
            micro_basket_margin_cap_amount=0.0,
            micro_basket_spread_cap=0.0,
            max_simultaneous_legs=0,
            max_total_volume=0.0,
            add_only_after_profit=False,
            minimum_profit_r_before_add=0.0,
        )

    # =========================================================================
    # Single account scenario
    # =========================================================================

    def evaluate_account(
        self,
        *,
        balance: float,
        equity: float | None = None,
        free_margin: float | None = None,
    ) -> RiskPolicyScenarioRow:

        resolved_balance = self._number(
            balance
        )

        resolved_equity = self._number(
            (
                balance
                if equity is None
                else equity
            )
        )

        resolved_free_margin = self._number(
            (
                resolved_equity
                if free_margin is None
                else free_margin
            )
        )

        if (
            not math.isfinite(
                resolved_balance
            )
            or
            resolved_balance <= 0.0
        ):

            return self._invalid_row(
                reason="INVALID_BALANCE",
            )

        if (
            not math.isfinite(
                resolved_equity
            )
            or
            resolved_equity <= 0.0
        ):

            return self._invalid_row(
                reason="INVALID_EQUITY",
                balance=resolved_balance,
            )

        if (
            not math.isfinite(
                resolved_free_margin
            )
            or
            resolved_free_margin < 0.0
        ):

            return self._invalid_row(
                reason="INVALID_FREE_MARGIN",
                balance=resolved_balance,
                equity=resolved_equity,
            )

        risk_base = min(
            resolved_balance,
            resolved_equity,
        )

        planner_bootstrap_range = (
            risk_base
            <=
            self.basket_policy.bootstrap_balance_max
            +
            self._EPSILON
        )

        planner_basket_mode = (
            self.MICRO_BASKET_MODE
            if planner_bootstrap_range
            else
            self.STANDARD_BASKET_MODE
        )

        broker_micro_eligible = (
            bool(
                self.broker_policy.micro_enabled
            )
            and
            risk_base
            >=
            self.broker_policy.micro_min_balance
            -
            self._EPSILON
            and
            risk_base
            <=
            self.broker_policy.micro_max_balance
            +
            self._EPSILON
        )

        standard_target_amount = self._amount(
            risk_base,
            self.broker_policy.target_risk_percent,
        )

        standard_hard_amount = self._amount(
            risk_base,
            self.broker_policy.hard_max_risk_percent,
        )

        standard_broker_margin_cap = self._amount(
            resolved_free_margin,
            self.broker_policy.max_margin_percent_of_free,
        )

        standard_broker_spread_cap = (
            standard_hard_amount
            *
            self.broker_policy
            .max_spread_cost_to_hard_risk_ratio
        )

        standard_basket_loss_cap = self._amount(
            risk_base,
            self.basket_policy.standard_basket_hard_loss_percent,
        )

        standard_basket_margin_cap = self._amount(
            resolved_equity,
            self.basket_policy.standard_margin_cap_percent,
        )

        standard_basket_spread_cap = (
            standard_basket_loss_cap
            *
            self.basket_policy
            .max_total_spread_to_basket_loss_ratio
        )

        micro_hard_amount = self._amount(
            risk_base,
            self.broker_policy.micro_hard_max_risk_percent,
        )

        micro_broker_margin_cap = self._amount(
            resolved_free_margin,
            self.broker_policy.micro_max_margin_percent_of_free,
        )

        micro_basket_loss_cap = (
            self._bootstrap_loss_cap(
                risk_base
            )
            if broker_micro_eligible
            and planner_bootstrap_range
            else
            0.0
        )

        micro_basket_loss_cap_percent = (
            self._percent(
                micro_basket_loss_cap,
                risk_base,
            )
            if micro_basket_loss_cap > 0.0
            else
            0.0
        )

        micro_basket_margin_cap = (
            self._amount(
                resolved_equity,
                self.basket_policy.bootstrap_margin_cap_percent,
            )
            if broker_micro_eligible
            and planner_bootstrap_range
            else
            0.0
        )

        micro_basket_spread_cap = (
            micro_basket_loss_cap
            *
            self.basket_policy
            .max_total_spread_to_basket_loss_ratio
        )

        return RiskPolicyScenarioRow(
            valid=True,
            reason="OK_RISK_POLICY_SCENARIO",
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            balance=round(
                resolved_balance,
                8,
            ),
            equity=round(
                resolved_equity,
                8,
            ),
            free_margin=round(
                resolved_free_margin,
                8,
            ),
            risk_base=round(
                risk_base,
                8,
            ),
            broker_micro_eligible=(
                broker_micro_eligible
            ),
            planner_bootstrap_range=(
                planner_bootstrap_range
            ),
            planner_basket_mode_by_risk_base=(
                planner_basket_mode
            ),
            standard_override_required_if_selected=(
                planner_basket_mode
                !=
                self.STANDARD_BASKET_MODE
            ),
            micro_override_required_if_selected=(
                planner_basket_mode
                !=
                self.MICRO_BASKET_MODE
            ),
            standard_target_risk_percent=round(
                self.broker_policy.target_risk_percent,
                8,
            ),
            standard_hard_single_leg_percent=round(
                self.broker_policy.hard_max_risk_percent,
                8,
            ),
            standard_target_risk_amount=round(
                standard_target_amount,
                8,
            ),
            standard_hard_single_leg_amount=round(
                standard_hard_amount,
                8,
            ),
            standard_broker_margin_cap_percent=round(
                self.broker_policy.max_margin_percent_of_free,
                8,
            ),
            standard_broker_margin_cap_amount=round(
                standard_broker_margin_cap,
                8,
            ),
            standard_broker_spread_hard_cap=round(
                standard_broker_spread_cap,
                8,
            ),
            standard_basket_hard_loss_percent=round(
                self.basket_policy.standard_basket_hard_loss_percent,
                8,
            ),
            standard_basket_loss_cap=round(
                standard_basket_loss_cap,
                8,
            ),
            standard_basket_margin_cap_percent=round(
                self.basket_policy.standard_margin_cap_percent,
                8,
            ),
            standard_basket_margin_cap_amount=round(
                standard_basket_margin_cap,
                8,
            ),
            standard_basket_spread_cap=round(
                standard_basket_spread_cap,
                8,
            ),
            micro_hard_single_leg_percent=round(
                self.broker_policy.micro_hard_max_risk_percent,
                8,
            ),
            micro_hard_single_leg_amount=round(
                micro_hard_amount,
                8,
            ),
            micro_broker_margin_cap_percent=round(
                self.broker_policy.micro_max_margin_percent_of_free,
                8,
            ),
            micro_broker_margin_cap_amount=round(
                micro_broker_margin_cap,
                8,
            ),
            micro_min_balance=round(
                self.broker_policy.micro_min_balance,
                8,
            ),
            micro_max_balance=round(
                self.broker_policy.micro_max_balance,
                8,
            ),
            bootstrap_balance_max=round(
                self.basket_policy.bootstrap_balance_max,
                8,
            ),
            micro_basket_loss_cap=round(
                micro_basket_loss_cap,
                8,
            ),
            micro_basket_loss_cap_percent_of_risk_base=round(
                micro_basket_loss_cap_percent,
                8,
            ),
            micro_basket_margin_cap_percent=round(
                self.basket_policy.bootstrap_margin_cap_percent,
                8,
            ),
            micro_basket_margin_cap_amount=round(
                micro_basket_margin_cap,
                8,
            ),
            micro_basket_spread_cap=round(
                micro_basket_spread_cap,
                8,
            ),
            max_simultaneous_legs=int(
                self.basket_policy.max_simultaneous_legs
            ),
            max_total_volume=round(
                self.basket_policy.max_total_volume,
                8,
            ),
            add_only_after_profit=bool(
                self.basket_policy.add_only_after_profit
            ),
            minimum_profit_r_before_add=round(
                self.basket_policy.minimum_profit_r_before_add,
                8,
            ),
        )

    # =========================================================================
    # Matrix
    # =========================================================================

    def evaluate(
        self,
        balances: Iterable[
            float
        ] | None = None,
    ) -> RiskPolicyScenarioMatrixResult:

        resolved_balances = tuple(
            self.DEFAULT_BALANCES
            if balances is None
            else balances
        )

        if not resolved_balances:

            return RiskPolicyScenarioMatrixResult(
                valid=False,
                reason="EMPTY_SCENARIO_MATRIX",
                mode=self.MODE,
                version=self.VERSION,
                live_authorized=False,
                policy_alignment_valid=False,
                alignment_violations=(),
                rows=(),
            )

        rows = tuple(
            self.evaluate_account(
                balance=balance,
            )
            for balance
            in resolved_balances
        )

        if any(
            not row.valid
            for row
            in rows
        ):

            return RiskPolicyScenarioMatrixResult(
                valid=False,
                reason="INVALID_SCENARIO_ROW",
                mode=self.MODE,
                version=self.VERSION,
                live_authorized=False,
                policy_alignment_valid=False,
                alignment_violations=(),
                rows=rows,
            )

        violations = (
            self.alignment_violations()
        )

        return RiskPolicyScenarioMatrixResult(
            valid=True,
            reason="OK_RISK_POLICY_SCENARIO_MATRIX",
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            policy_alignment_valid=(
                not violations
            ),
            alignment_violations=violations,
            rows=rows,
        )


risk_policy_scenario_matrix = (
    RiskPolicyScenarioMatrix()
)