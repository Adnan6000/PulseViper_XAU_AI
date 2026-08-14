"""
===============================================================================
Module      : account_protected_compounding_admission.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Shadow Account-Protection Pre-Gate for Compounding Admission
===============================================================================

Status
------
SHADOW / RESEARCH / DEMO ONLY.

Flow
----
    BrokerRiskPlan
        -> AccountProtectionGuard
        -> ExecutionAwareCompoundingAdmissionEngine
            -> ExecutionFrictionModel
            -> BasketLegCandidate
            -> CompoundingAccountStateAdapter

Purpose
-------
Fail closed before execution-friction and compounding-admission work whenever
account protection says NEW exposure is not allowed.

Important semantics
-------------------
1. Protection uses risk_plan.equity as the current account-equity observation.
2. Protection watermark state is returned even when exposure is blocked.
3. A protection block never invokes downstream admission.
4. A downstream rejection does not roll back the already-observed protection
   watermark state.
5. This layer does not record basket-close P&L. Basket-close state changes stay
   in AccountProtectionGuard.record_basket_close().
6. live_authorized is always False.

This module does NOT:
- connect to MT5
- send orders
- open positions
- modify SL/TP
- modify production trade_ready
- modify production RiskEngine
"""

from __future__ import annotations

import importlib
import math
from dataclasses import dataclass
from typing import Any


protection_module: Any = importlib.import_module(
    "02_AI.Shadow.account_protection_guard"
)

admission_module: Any = importlib.import_module(
    "02_AI.Shadow.execution_aware_compounding_admission"
)


AccountProtectionGuard: Any = (
    protection_module.AccountProtectionGuard
)

ExecutionAwareCompoundingAdmissionEngine: Any = (
    admission_module.ExecutionAwareCompoundingAdmissionEngine
)


@dataclass(
    frozen=True,
)
class AccountProtectedCompoundingAdmission:
    valid: bool

    admitted: bool

    reason: str

    protection_reason: str

    admission_reason: str

    mode: str

    version: str

    live_authorized: bool

    downstream_invoked: bool

    protection_state_before: Any

    protection_state_after: Any

    protection_assessment: Any

    admission_result: Any


class AccountProtectedCompoundingAdmissionEngine:
    VERSION = "1.0"

    MODE = (
        "SHADOW_ACCOUNT_PROTECTED_COMPOUNDING_ADMISSION_ONLY"
    )

    _REQUIRED_DOWNSTREAM_FIELDS = (
        "valid",
        "admitted",
        "reason",
        "live_authorized",
    )

    def __init__(
        self,
        *,
        protection_guard: Any | None = None,
        admission_engine: Any | None = None,
    ) -> None:

        self.protection_guard = (
            protection_guard
            if protection_guard is not None
            else AccountProtectionGuard()
        )

        self.admission_engine = (
            admission_engine
            if admission_engine is not None
            else ExecutionAwareCompoundingAdmissionEngine()
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

    def _result(
        self,
        *,
        valid: bool,
        admitted: bool,
        reason: str,
        protection_reason: str,
        admission_reason: str,
        downstream_invoked: bool,
        protection_state_before: Any,
        protection_state_after: Any,
        protection_assessment: Any = None,
        admission_result: Any = None,
    ) -> AccountProtectedCompoundingAdmission:

        return AccountProtectedCompoundingAdmission(
            valid=valid,
            admitted=admitted,
            reason=reason,
            protection_reason=protection_reason,
            admission_reason=admission_reason,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            downstream_invoked=downstream_invoked,
            protection_state_before=protection_state_before,
            protection_state_after=protection_state_after,
            protection_assessment=protection_assessment,
            admission_result=admission_result,
        )

    # =========================================================================
    # Main protected admission
    # =========================================================================

    def admit(
        self,
        *,
        protection_state: Any,
        current_bar: int,
        risk_plan: Any,
        leg_id: str,
        account_margin_used: float,
        estimated_slippage_price: float = 0.0,
        estimated_slippage_cost: float = 0.0,
        estimated_commission_cost: float = 0.0,
        existing_legs: int = 0,
        existing_direction: str = "",
        existing_volume: float = 0.0,
        existing_projected_loss: float = 0.0,
        existing_basket_margin: float = 0.0,
        existing_spread_cost: float = 0.0,
        existing_floating_profit: float = 0.0,
        first_leg_initial_risk: float = 0.0,
    ) -> AccountProtectedCompoundingAdmission:

        # =====================================================================
        # Resolve current account equity from the already-built broker risk plan.
        #
        # We intentionally do not validate the whole BrokerRiskPlan here.
        # The downstream admission engine owns that contract.
        # =====================================================================

        if (
            risk_plan is None
            or
            not hasattr(
                risk_plan,
                "equity",
            )
        ):

            return self._result(
                valid=False,
                admitted=False,
                reason="INVALID_RISK_PLAN_EQUITY",
                protection_reason="",
                admission_reason="",
                downstream_invoked=False,
                protection_state_before=protection_state,
                protection_state_after=protection_state,
            )

        current_equity = self._number(
            risk_plan.equity
        )

        if (
            not math.isfinite(
                current_equity
            )
            or
            current_equity < 0.0
        ):

            return self._result(
                valid=False,
                admitted=False,
                reason="INVALID_RISK_PLAN_EQUITY",
                protection_reason="",
                admission_reason="",
                downstream_invoked=False,
                protection_state_before=protection_state,
                protection_state_after=protection_state,
            )

        # =====================================================================
        # Account protection is always evaluated before friction/admission.
        # =====================================================================

        protection_assessment = (
            self.protection_guard.assess_new_exposure(
                state=protection_state,
                current_equity=current_equity,
                current_bar=current_bar,
            )
        )

        protection_reason = str(
            protection_assessment.reason
        )

        protection_state_after = (
            protection_assessment.state_after
        )

        if not bool(
            protection_assessment.valid
        ):

            return self._result(
                valid=False,
                admitted=False,
                reason="ACCOUNT_PROTECTION_ASSESSMENT_INVALID",
                protection_reason=protection_reason,
                admission_reason="",
                downstream_invoked=False,
                protection_state_before=protection_state,
                protection_state_after=protection_state_after,
                protection_assessment=protection_assessment,
            )

        if not bool(
            protection_assessment.exposure_allowed
        ):

            return self._result(
                valid=False,
                admitted=False,
                reason="ACCOUNT_PROTECTION_BLOCKED",
                protection_reason=protection_reason,
                admission_reason="",
                downstream_invoked=False,
                protection_state_before=protection_state,
                protection_state_after=protection_state_after,
                protection_assessment=protection_assessment,
            )

        # =====================================================================
        # Only an account-protection-approved candidate may reach friction and
        # compounding admission.
        # =====================================================================

        admission_result = (
            self.admission_engine.admit(
                risk_plan=risk_plan,
                leg_id=leg_id,
                account_margin_used=account_margin_used,
                estimated_slippage_price=estimated_slippage_price,
                estimated_slippage_cost=estimated_slippage_cost,
                estimated_commission_cost=estimated_commission_cost,
                existing_legs=existing_legs,
                existing_direction=existing_direction,
                existing_volume=existing_volume,
                existing_projected_loss=existing_projected_loss,
                existing_basket_margin=existing_basket_margin,
                existing_spread_cost=existing_spread_cost,
                existing_floating_profit=existing_floating_profit,
                first_leg_initial_risk=first_leg_initial_risk,
            )
        )

        if not self._has_fields(
            admission_result,
            self._REQUIRED_DOWNSTREAM_FIELDS,
        ):

            return self._result(
                valid=False,
                admitted=False,
                reason="INVALID_DOWNSTREAM_ADMISSION_RESULT",
                protection_reason=protection_reason,
                admission_reason="",
                downstream_invoked=True,
                protection_state_before=protection_state,
                protection_state_after=protection_state_after,
                protection_assessment=protection_assessment,
                admission_result=admission_result,
            )

        admission_reason = str(
            admission_result.reason
        )

        if bool(
            admission_result.live_authorized
        ):

            return self._result(
                valid=False,
                admitted=False,
                reason="LIVE_AUTHORIZATION_NOT_ALLOWED",
                protection_reason=protection_reason,
                admission_reason=admission_reason,
                downstream_invoked=True,
                protection_state_before=protection_state,
                protection_state_after=protection_state_after,
                protection_assessment=protection_assessment,
                admission_result=admission_result,
            )

        if (
            bool(
                admission_result.valid
            )
            and
            bool(
                admission_result.admitted
            )
        ):

            return self._result(
                valid=True,
                admitted=True,
                reason="OK_ACCOUNT_PROTECTED_COMPOUNDING_ADMISSION",
                protection_reason=protection_reason,
                admission_reason=admission_reason,
                downstream_invoked=True,
                protection_state_before=protection_state,
                protection_state_after=protection_state_after,
                protection_assessment=protection_assessment,
                admission_result=admission_result,
            )

        return self._result(
            valid=False,
            admitted=False,
            reason="DOWNSTREAM_ADMISSION_REJECTED",
            protection_reason=protection_reason,
            admission_reason=admission_reason,
            downstream_invoked=True,
            protection_state_before=protection_state,
            protection_state_after=protection_state_after,
            protection_assessment=protection_assessment,
            admission_result=admission_result,
        )


account_protected_compounding_admission_engine = (
    AccountProtectedCompoundingAdmissionEngine()
)