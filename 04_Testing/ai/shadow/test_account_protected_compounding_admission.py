"""
Offline tests for AccountProtectedCompoundingAdmissionEngine v1.0.
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from typing import Any

import pytest


pytestmark = pytest.mark.offline


protection_module: Any = importlib.import_module(
    "02_AI.Shadow.account_protection_guard"
)

module: Any = importlib.import_module(
    "02_AI.Shadow.account_protected_compounding_admission"
)


Policy: Any = (
    protection_module.AccountProtectionPolicy
)

Guard: Any = (
    protection_module.AccountProtectionGuard
)

Engine: Any = (
    module.AccountProtectedCompoundingAdmissionEngine
)


def guard(
    **overrides: Any,
) -> Any:

    values = {
        "max_peak_drawdown_percent": 10.0,
        "cooldown_bars_after_loss": 5,
        "loss_streak_threshold": 3,
        "cooldown_bars_after_loss_streak": 30,
        "flat_pnl_epsilon": 1e-9,
    }

    values.update(
        overrides
    )

    return Guard(
        Policy(
            **values
        )
    )


def risk_plan(
    *,
    equity: float = 100.0,
) -> Any:

    return SimpleNamespace(
        equity=equity
    )


def downstream_result(
    *,
    valid: bool = True,
    admitted: bool = True,
    reason: str = "OK_EXECUTION_AWARE_COMPOUNDING_ADMISSION",
    live_authorized: bool = False,
) -> Any:

    return SimpleNamespace(
        valid=valid,
        admitted=admitted,
        reason=reason,
        live_authorized=live_authorized,
    )


class CaptureAdmission:
    def __init__(
        self,
        result: Any | None = None,
    ) -> None:

        self.calls: list[
            dict[
                str,
                Any,
            ]
        ] = []

        self.result = (
            downstream_result()
            if result is None
            else result
        )

    def admit(
        self,
        **kwargs: Any,
    ) -> Any:

        self.calls.append(
            dict(
                kwargs
            )
        )

        return self.result


class ExplodingAdmission:
    def admit(
        self,
        **_: Any,
    ) -> Any:

        raise AssertionError(
            "downstream admission must not be invoked"
        )


def engine(
    admission_engine: Any | None = None,
    **policy_overrides: Any,
) -> Any:

    return Engine(
        protection_guard=guard(
            **policy_overrides
        ),
        admission_engine=(
            CaptureAdmission()
            if admission_engine is None
            else admission_engine
        ),
    )


def test_engine_is_shadow_only_and_allows_protected_admission() -> None:

    downstream = CaptureAdmission()

    protected = engine(
        admission_engine=downstream
    )

    state = protected.protection_guard.initial_state(
        equity=100.0,
        current_bar=0,
    )

    result = protected.admit(
        protection_state=state,
        current_bar=1,
        risk_plan=risk_plan(
            equity=100.0
        ),
        leg_id="L1",
        account_margin_used=0.0,
    )

    assert protected.VERSION == "1.0"

    assert protected.MODE == (
        "SHADOW_ACCOUNT_PROTECTED_COMPOUNDING_ADMISSION_ONLY"
    )

    assert result.valid is True

    assert result.admitted is True

    assert result.live_authorized is False

    assert result.downstream_invoked is True

    assert len(
        downstream.calls
    ) == 1


def test_loss_cooldown_blocks_before_downstream() -> None:

    protected = engine(
        admission_engine=ExplodingAdmission()
    )

    state = protected.protection_guard.initial_state(
        equity=100.0,
        current_bar=10,
    )

    state = (
        protected
        .protection_guard
        .record_basket_close(
            state=state,
            realized_pnl=-1.0,
            equity_after_close=99.0,
            current_bar=10,
        )
        .state_after
    )

    result = protected.admit(
        protection_state=state,
        current_bar=11,
        risk_plan=risk_plan(
            equity=99.0
        ),
        leg_id="L2",
        account_margin_used=0.0,
    )

    assert result.valid is False

    assert result.admitted is False

    assert result.reason == (
        "ACCOUNT_PROTECTION_BLOCKED"
    )

    assert result.protection_reason == (
        "LOSS_COOLDOWN_ACTIVE"
    )

    assert result.downstream_invoked is False

    assert result.protection_state_after.last_observed_bar == (
        11
    )


def test_hard_drawdown_lock_blocks_before_downstream() -> None:

    protected = engine(
        admission_engine=ExplodingAdmission(),
        max_peak_drawdown_percent=10.0,
    )

    state = protected.protection_guard.initial_state(
        equity=100.0,
        current_bar=0,
    )

    result = protected.admit(
        protection_state=state,
        current_bar=1,
        risk_plan=risk_plan(
            equity=90.0
        ),
        leg_id="L1",
        account_margin_used=0.0,
    )

    assert result.valid is False

    assert result.reason == (
        "ACCOUNT_PROTECTION_BLOCKED"
    )

    assert result.protection_reason == (
        "HARD_DRAWDOWN_LOCK"
    )

    assert result.protection_state_after.hard_locked is True

    assert result.downstream_invoked is False


def test_non_monotonic_bar_fails_before_downstream_and_preserves_state() -> None:

    protected = engine(
        admission_engine=ExplodingAdmission()
    )

    state = protected.protection_guard.initial_state(
        equity=100.0,
        current_bar=10,
    )

    result = protected.admit(
        protection_state=state,
        current_bar=9,
        risk_plan=risk_plan(
            equity=100.0
        ),
        leg_id="L1",
        account_margin_used=0.0,
    )

    assert result.valid is False

    assert result.reason == (
        "ACCOUNT_PROTECTION_ASSESSMENT_INVALID"
    )

    assert result.protection_reason == (
        "NON_MONOTONIC_BAR"
    )

    assert result.downstream_invoked is False

    assert result.protection_state_after == (
        state
    )


def test_allowed_path_forwards_exact_downstream_inputs() -> None:

    downstream = CaptureAdmission()

    protected = engine(
        admission_engine=downstream
    )

    state = protected.protection_guard.initial_state(
        equity=100.0
    )

    upstream = risk_plan(
        equity=100.0
    )

    result = protected.admit(
        protection_state=state,
        current_bar=1,
        risk_plan=upstream,
        leg_id="L2",
        account_margin_used=2.16,
        estimated_slippage_price=0.03,
        estimated_slippage_cost=0.04,
        estimated_commission_cost=0.05,
        existing_legs=1,
        existing_direction="LONG",
        existing_volume=0.01,
        existing_projected_loss=0.50,
        existing_basket_margin=2.16,
        existing_spread_cost=0.26,
        existing_floating_profit=0.30,
        first_leg_initial_risk=0.50,
    )

    assert result.valid is True

    assert len(
        downstream.calls
    ) == 1

    call = downstream.calls[0]

    assert call["risk_plan"] is (
        upstream
    )

    assert call["leg_id"] == (
        "L2"
    )

    assert call["account_margin_used"] == pytest.approx(
        2.16
    )

    assert call["estimated_slippage_price"] == pytest.approx(
        0.03
    )

    assert call["estimated_slippage_cost"] == pytest.approx(
        0.04
    )

    assert call["estimated_commission_cost"] == pytest.approx(
        0.05
    )

    assert call["existing_legs"] == (
        1
    )

    assert call["existing_direction"] == (
        "LONG"
    )

    assert call["existing_volume"] == pytest.approx(
        0.01
    )

    assert call["existing_projected_loss"] == pytest.approx(
        0.50
    )

    assert call["existing_basket_margin"] == pytest.approx(
        2.16
    )

    assert call["existing_spread_cost"] == pytest.approx(
        0.26
    )

    assert call["existing_floating_profit"] == pytest.approx(
        0.30
    )

    assert call["first_leg_initial_risk"] == pytest.approx(
        0.50
    )


def test_downstream_rejection_is_preserved_after_protection_pass() -> None:

    downstream = CaptureAdmission(
        downstream_result(
            valid=False,
            admitted=False,
            reason="EXECUTION_FRICTION_BLOCKED",
        )
    )

    protected = engine(
        admission_engine=downstream
    )

    state = protected.protection_guard.initial_state(
        equity=100.0
    )

    result = protected.admit(
        protection_state=state,
        current_bar=1,
        risk_plan=risk_plan(
            equity=100.0
        ),
        leg_id="L1",
        account_margin_used=0.0,
    )

    assert result.valid is False

    assert result.admitted is False

    assert result.reason == (
        "DOWNSTREAM_ADMISSION_REJECTED"
    )

    assert result.admission_reason == (
        "EXECUTION_FRICTION_BLOCKED"
    )

    assert result.protection_reason == (
        "OK_ACCOUNT_PROTECTION"
    )

    assert result.downstream_invoked is True


def test_new_equity_peak_is_retained_even_when_downstream_rejects() -> None:

    downstream = CaptureAdmission(
        downstream_result(
            valid=False,
            admitted=False,
            reason="ACCOUNT_COMPOUNDING_ADMISSION_REJECTED",
        )
    )

    protected = engine(
        admission_engine=downstream
    )

    state = protected.protection_guard.initial_state(
        equity=100.0
    )

    result = protected.admit(
        protection_state=state,
        current_bar=1,
        risk_plan=risk_plan(
            equity=110.0
        ),
        leg_id="L1",
        account_margin_used=0.0,
    )

    assert result.valid is False

    assert result.protection_state_after.peak_equity == pytest.approx(
        110.0
    )

    assert result.protection_state_after.current_equity == pytest.approx(
        110.0
    )


def test_cooldown_expiry_allows_downstream_again() -> None:

    downstream = CaptureAdmission()

    protected = engine(
        admission_engine=downstream
    )

    state = protected.protection_guard.initial_state(
        equity=100.0,
        current_bar=10,
    )

    state = (
        protected
        .protection_guard
        .record_basket_close(
            state=state,
            realized_pnl=-1.0,
            equity_after_close=99.0,
            current_bar=10,
        )
        .state_after
    )

    result = protected.admit(
        protection_state=state,
        current_bar=15,
        risk_plan=risk_plan(
            equity=99.0
        ),
        leg_id="L2",
        account_margin_used=0.0,
    )

    assert result.valid is True

    assert result.admitted is True

    assert result.protection_reason == (
        "OK_ACCOUNT_PROTECTION"
    )

    assert result.downstream_invoked is True

    assert len(
        downstream.calls
    ) == 1


def test_missing_risk_plan_equity_fails_before_protection_and_downstream() -> None:

    protected = engine(
        admission_engine=ExplodingAdmission()
    )

    state = protected.protection_guard.initial_state(
        equity=100.0
    )

    result = protected.admit(
        protection_state=state,
        current_bar=1,
        risk_plan=SimpleNamespace(),
        leg_id="L1",
        account_margin_used=0.0,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_RISK_PLAN_EQUITY"
    )

    assert result.downstream_invoked is False

    assert result.protection_assessment is None

    assert result.protection_state_after == (
        state
    )


def test_non_finite_risk_plan_equity_fails_closed() -> None:

    protected = engine(
        admission_engine=ExplodingAdmission()
    )

    state = protected.protection_guard.initial_state(
        equity=100.0
    )

    result = protected.admit(
        protection_state=state,
        current_bar=1,
        risk_plan=risk_plan(
            equity=float("nan")
        ),
        leg_id="L1",
        account_margin_used=0.0,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_RISK_PLAN_EQUITY"
    )

    assert result.downstream_invoked is False


def test_malformed_downstream_result_fails_closed() -> None:

    downstream = CaptureAdmission(
        SimpleNamespace(
            reason="MALFORMED"
        )
    )

    protected = engine(
        admission_engine=downstream
    )

    state = protected.protection_guard.initial_state(
        equity=100.0
    )

    result = protected.admit(
        protection_state=state,
        current_bar=1,
        risk_plan=risk_plan(),
        leg_id="L1",
        account_margin_used=0.0,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_DOWNSTREAM_ADMISSION_RESULT"
    )

    assert result.downstream_invoked is True


def test_downstream_live_authorization_is_refused() -> None:

    downstream = CaptureAdmission(
        downstream_result(
            valid=True,
            admitted=True,
            live_authorized=True,
        )
    )

    protected = engine(
        admission_engine=downstream
    )

    state = protected.protection_guard.initial_state(
        equity=100.0
    )

    result = protected.admit(
        protection_state=state,
        current_bar=1,
        risk_plan=risk_plan(),
        leg_id="L1",
        account_margin_used=0.0,
    )

    assert result.valid is False

    assert result.admitted is False

    assert result.reason == (
        "LIVE_AUTHORIZATION_NOT_ALLOWED"
    )

    assert result.live_authorized is False