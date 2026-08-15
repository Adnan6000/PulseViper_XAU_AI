"""
===============================================================================
Module      : risk_mode_basket_reconciliation.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Shadow Broker Risk-Mode -> Basket-Policy Reconciliation
===============================================================================

Status
------
SHADOW / RESEARCH / DEMO ONLY.

Purpose
-------
Reconcile an already-approved ExecutionAwareCompoundingAdmission with the
basket-risk regime implied by the upstream BrokerRiskPlan.risk_mode.

Why this exists
---------------
BrokerAwareRiskEngine selects:

    STANDARD_COMPOUND

first whenever broker minimum volume fits standard hard limits. MICRO_BOOTSTRAP
is only a fallback.

BootstrapCompoundingPlanner, however, selects its basket regime from account
risk-base alone:

    risk_base <= bootstrap_balance_max
        -> MICRO_BOOTSTRAP_BASKET

That means a small account can theoretically produce a STANDARD_COMPOUND
single-leg plan while the basket planner evaluates the combined basket under
bootstrap limits.

This module does NOT change either engine. It applies the effective basket
limits implied by the upstream risk mode before lifecycle exposure is allowed.

Important semantics
-------------------
STANDARD_COMPOUND:
- combined basket loss uses standard_basket_hard_loss_percent
- combined basket margin uses standard_margin_cap_percent
- basket spread uses max_total_spread_to_basket_loss_ratio

MICRO_BOOTSTRAP:
- combined basket loss uses bootstrap floor / percent / ceiling
- combined basket margin uses bootstrap_margin_cap_percent
- basket spread uses max_total_spread_to_basket_loss_ratio
- risk base must remain inside bootstrap_balance_max

A planner basket-mode label mismatch is not automatically rejected. The
effective upstream risk-mode limits are recomputed and enforced. This allows
safe reconciliation without redesigning the existing planner.

Safety
------
This module:
- does not connect to MT5
- does not send orders
- does not modify positions
- does not modify SL/TP
- does not authorize live execution
- does not modify production trade_ready
- does not modify production RiskEngine

Every result:
    live_authorized = False
"""

from __future__ import annotations

import importlib
import math
from dataclasses import dataclass
from typing import Any


planner_module: Any = importlib.import_module(
    "02_AI.Shadow.bootstrap_compounding_planner"
)

BootstrapCompoundingPolicy: Any = (
    planner_module.BootstrapCompoundingPolicy
)


@dataclass(
    frozen=True,
)
class RiskModeBasketReconciliation:
    valid: bool

    reconciled: bool

    reason: str

    mode: str

    version: str

    live_authorized: bool

    risk_mode: str

    planner_basket_mode: str

    effective_basket_mode: str

    regime_override_required: bool

    risk_base: float

    account_equity: float

    effective_loss_cap: float

    effective_loss_cap_percent: float

    effective_margin_cap_amount: float

    effective_margin_cap_percent: float

    total_projected_loss: float

    total_projected_loss_percent: float

    total_margin: float

    total_margin_percent_of_equity: float

    total_spread_cost: float

    spread_to_effective_loss_cap_ratio: float

    admission_result: Any


class RiskModeBasketReconciliationEngine:
    VERSION = "1.0"

    MODE = "SHADOW_RISK_MODE_BASKET_RECONCILIATION_ONLY"

    STANDARD_RISK_MODE = "STANDARD_COMPOUND"

    MICRO_RISK_MODE = "MICRO_BOOTSTRAP"

    STANDARD_BASKET_MODE = "STANDARD_COMPOUND_BASKET"

    MICRO_BASKET_MODE = "MICRO_BOOTSTRAP_BASKET"

    _EPSILON = 1e-9

    _REQUIRED_ADMISSION_FIELDS = (
        "valid",
        "admitted",
        "reason",
        "live_authorized",
        "risk_plan",
        "account_plan",
    )

    _REQUIRED_RISK_FIELDS = (
        "valid",
        "risk_mode",
        "risk_base",
        "equity",
        "live_authorized",
    )

    _REQUIRED_ACCOUNT_FIELDS = (
        "valid",
        "live_authorized",
        "basket_plan",
    )

    _REQUIRED_BASKET_FIELDS = (
        "valid",
        "basket_mode",
        "total_projected_loss",
        "total_margin",
        "total_spread_cost",
        "live_authorized",
    )

    def __init__(
        self,
        policy: Any | None = None,
    ) -> None:

        self.policy = (
            policy
            if policy is not None
            else BootstrapCompoundingPolicy()
        )

    # =========================================================================
    # Helpers
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
    def _has_fields(
        value: Any,
        fields: tuple[
            str,
            ...,
        ],
    ) -> bool:

        if value is None:

            return False

        return all(
            hasattr(
                value,
                field,
            )
            for field
            in fields
        )

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

    def _result(
        self,
        *,
        valid: bool,
        reconciled: bool,
        reason: str,
        admission_result: Any,
        risk_mode: str = "",
        planner_basket_mode: str = "",
        effective_basket_mode: str = "",
        regime_override_required: bool = False,
        risk_base: float = 0.0,
        account_equity: float = 0.0,
        effective_loss_cap: float = 0.0,
        effective_loss_cap_percent: float = 0.0,
        effective_margin_cap_amount: float = 0.0,
        effective_margin_cap_percent: float = 0.0,
        total_projected_loss: float = 0.0,
        total_margin: float = 0.0,
        total_spread_cost: float = 0.0,
    ) -> RiskModeBasketReconciliation:

        total_projected_loss_percent = (
            self._percent(
                total_projected_loss,
                risk_base,
            )
        )

        total_margin_percent_of_equity = (
            self._percent(
                total_margin,
                account_equity,
            )
        )

        spread_ratio = (
            (
                total_spread_cost
                /
                effective_loss_cap
            )
            if effective_loss_cap > 0.0
            else
            0.0
        )

        return RiskModeBasketReconciliation(
            valid=valid,
            reconciled=reconciled,
            reason=reason,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            risk_mode=risk_mode,
            planner_basket_mode=planner_basket_mode,
            effective_basket_mode=effective_basket_mode,
            regime_override_required=regime_override_required,
            risk_base=round(
                risk_base,
                8,
            ),
            account_equity=round(
                account_equity,
                8,
            ),
            effective_loss_cap=round(
                effective_loss_cap,
                8,
            ),
            effective_loss_cap_percent=round(
                effective_loss_cap_percent,
                8,
            ),
            effective_margin_cap_amount=round(
                effective_margin_cap_amount,
                8,
            ),
            effective_margin_cap_percent=round(
                effective_margin_cap_percent,
                8,
            ),
            total_projected_loss=round(
                total_projected_loss,
                8,
            ),
            total_projected_loss_percent=round(
                total_projected_loss_percent,
                8,
            ),
            total_margin=round(
                total_margin,
                8,
            ),
            total_margin_percent_of_equity=round(
                total_margin_percent_of_equity,
                8,
            ),
            total_spread_cost=round(
                total_spread_cost,
                8,
            ),
            spread_to_effective_loss_cap_ratio=round(
                spread_ratio,
                8,
            ),
            admission_result=admission_result,
        )

    def _bootstrap_loss_cap(
        self,
        risk_base: float,
    ) -> float:

        percentage_amount = (
            risk_base
            *
            self.policy.bootstrap_loss_budget_percent
            /
            100.0
        )

        cap = max(
            self.policy.bootstrap_loss_budget_floor_usd,
            percentage_amount,
        )

        return min(
            cap,
            self.policy.bootstrap_loss_budget_ceiling_usd,
        )

    # =========================================================================
    # Main reconciliation
    # =========================================================================

    def evaluate(
        self,
        *,
        admission_result: Any,
    ) -> RiskModeBasketReconciliation:

        if not self._has_fields(
            admission_result,
            self._REQUIRED_ADMISSION_FIELDS,
        ):

            return self._result(
                valid=False,
                reconciled=False,
                reason="INVALID_EXECUTION_ADMISSION_SHAPE",
                admission_result=admission_result,
            )

        if bool(
            admission_result.live_authorized
        ):

            return self._result(
                valid=False,
                reconciled=False,
                reason="LIVE_AUTHORIZATION_NOT_ALLOWED",
                admission_result=admission_result,
            )

        if (
            not bool(
                admission_result.valid
            )
            or
            not bool(
                admission_result.admitted
            )
        ):

            return self._result(
                valid=False,
                reconciled=False,
                reason="EXECUTION_ADMISSION_REJECTED",
                admission_result=admission_result,
            )

        risk_plan = (
            admission_result.risk_plan
        )

        account_plan = (
            admission_result.account_plan
        )

        if not self._has_fields(
            risk_plan,
            self._REQUIRED_RISK_FIELDS,
        ):

            return self._result(
                valid=False,
                reconciled=False,
                reason="INVALID_BROKER_RISK_PLAN_SHAPE",
                admission_result=admission_result,
            )

        if not self._has_fields(
            account_plan,
            self._REQUIRED_ACCOUNT_FIELDS,
        ):

            return self._result(
                valid=False,
                reconciled=False,
                reason="INVALID_ACCOUNT_PLAN_SHAPE",
                admission_result=admission_result,
            )

        basket_plan = (
            account_plan.basket_plan
        )

        if not self._has_fields(
            basket_plan,
            self._REQUIRED_BASKET_FIELDS,
        ):

            return self._result(
                valid=False,
                reconciled=False,
                reason="INVALID_BASKET_PLAN_SHAPE",
                admission_result=admission_result,
            )

        if (
            bool(
                risk_plan.live_authorized
            )
            or
            bool(
                account_plan.live_authorized
            )
            or
            bool(
                basket_plan.live_authorized
            )
        ):

            return self._result(
                valid=False,
                reconciled=False,
                reason="NESTED_LIVE_AUTHORIZATION_NOT_ALLOWED",
                admission_result=admission_result,
            )

        if (
            not bool(
                risk_plan.valid
            )
            or
            not bool(
                account_plan.valid
            )
            or
            not bool(
                basket_plan.valid
            )
        ):

            return self._result(
                valid=False,
                reconciled=False,
                reason="NESTED_PLAN_REJECTED",
                admission_result=admission_result,
            )

        risk_mode = str(
            risk_plan.risk_mode
        ).strip().upper()

        planner_basket_mode = str(
            basket_plan.basket_mode
        ).strip().upper()

        risk_base = self._number(
            risk_plan.risk_base
        )

        account_equity = self._number(
            risk_plan.equity
        )

        total_projected_loss = self._number(
            basket_plan.total_projected_loss
        )

        total_margin = self._number(
            basket_plan.total_margin
        )

        total_spread_cost = self._number(
            basket_plan.total_spread_cost
        )

        if (
            not math.isfinite(
                risk_base
            )
            or
            not math.isfinite(
                account_equity
            )
            or
            not math.isfinite(
                total_projected_loss
            )
            or
            not math.isfinite(
                total_margin
            )
            or
            not math.isfinite(
                total_spread_cost
            )
            or
            risk_base <= 0.0
            or
            account_equity <= 0.0
            or
            total_projected_loss < 0.0
            or
            total_margin < 0.0
            or
            total_spread_cost < 0.0
        ):

            return self._result(
                valid=False,
                reconciled=False,
                reason="INVALID_RECONCILIATION_NUMERIC_STATE",
                admission_result=admission_result,
                risk_mode=risk_mode,
                planner_basket_mode=planner_basket_mode,
            )

        if risk_mode == self.STANDARD_RISK_MODE:

            effective_basket_mode = (
                self.STANDARD_BASKET_MODE
            )

            effective_loss_cap_percent = (
                self.policy.standard_basket_hard_loss_percent
            )

            effective_loss_cap = (
                risk_base
                *
                effective_loss_cap_percent
                /
                100.0
            )

            effective_margin_cap_percent = (
                self.policy.standard_margin_cap_percent
            )

        elif risk_mode == self.MICRO_RISK_MODE:

            if (
                risk_base
                >
                self.policy.bootstrap_balance_max
                +
                self._EPSILON
            ):

                return self._result(
                    valid=False,
                    reconciled=False,
                    reason="MICRO_RISK_MODE_OUTSIDE_BOOTSTRAP_RANGE",
                    admission_result=admission_result,
                    risk_mode=risk_mode,
                    planner_basket_mode=planner_basket_mode,
                    risk_base=risk_base,
                    account_equity=account_equity,
                    total_projected_loss=total_projected_loss,
                    total_margin=total_margin,
                    total_spread_cost=total_spread_cost,
                )

            effective_basket_mode = (
                self.MICRO_BASKET_MODE
            )

            effective_loss_cap = (
                self._bootstrap_loss_cap(
                    risk_base
                )
            )

            effective_loss_cap_percent = (
                self._percent(
                    effective_loss_cap,
                    risk_base,
                )
            )

            effective_margin_cap_percent = (
                self.policy.bootstrap_margin_cap_percent
            )

        else:

            return self._result(
                valid=False,
                reconciled=False,
                reason="UNKNOWN_RISK_MODE",
                admission_result=admission_result,
                risk_mode=risk_mode,
                planner_basket_mode=planner_basket_mode,
                risk_base=risk_base,
                account_equity=account_equity,
                total_projected_loss=total_projected_loss,
                total_margin=total_margin,
                total_spread_cost=total_spread_cost,
            )

        effective_margin_cap_amount = (
            account_equity
            *
            effective_margin_cap_percent
            /
            100.0
        )

        regime_override_required = (
            planner_basket_mode
            !=
            effective_basket_mode
        )

        common = {
            "admission_result": admission_result,
            "risk_mode": risk_mode,
            "planner_basket_mode": planner_basket_mode,
            "effective_basket_mode": effective_basket_mode,
            "regime_override_required": regime_override_required,
            "risk_base": risk_base,
            "account_equity": account_equity,
            "effective_loss_cap": effective_loss_cap,
            "effective_loss_cap_percent": (
                effective_loss_cap_percent
            ),
            "effective_margin_cap_amount": (
                effective_margin_cap_amount
            ),
            "effective_margin_cap_percent": (
                effective_margin_cap_percent
            ),
            "total_projected_loss": total_projected_loss,
            "total_margin": total_margin,
            "total_spread_cost": total_spread_cost,
        }

        if (
            total_projected_loss
            >
            effective_loss_cap
            +
            self._EPSILON
        ):

            return self._result(
                valid=True,
                reconciled=False,
                reason="BASKET_LOSS_EXCEEDS_RISK_MODE_CAP",
                **common,
            )

        if (
            total_margin
            >
            effective_margin_cap_amount
            +
            self._EPSILON
        ):

            return self._result(
                valid=True,
                reconciled=False,
                reason="BASKET_MARGIN_EXCEEDS_RISK_MODE_CAP",
                **common,
            )

        spread_ratio = (
            (
                total_spread_cost
                /
                effective_loss_cap
            )
            if effective_loss_cap > 0.0
            else
            math.inf
        )

        if (
            spread_ratio
            >
            self.policy.max_total_spread_to_basket_loss_ratio
            +
            self._EPSILON
        ):

            return self._result(
                valid=True,
                reconciled=False,
                reason="BASKET_SPREAD_EXCEEDS_RISK_MODE_CAP",
                **common,
            )

        reason = (
            "OK_RISK_MODE_BASKET_RECONCILIATION_OVERRIDE"
            if regime_override_required
            else
            "OK_RISK_MODE_BASKET_RECONCILIATION"
        )

        return self._result(
            valid=True,
            reconciled=True,
            reason=reason,
            **common,
        )


risk_mode_basket_reconciliation_engine = (
    RiskModeBasketReconciliationEngine()
)