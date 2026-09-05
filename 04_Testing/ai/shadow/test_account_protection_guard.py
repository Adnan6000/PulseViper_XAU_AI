"""
Offline tests for AccountProtectionGuard v1.0.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Shadow.account_protection_guard"
)


Policy: Any = (
    module.AccountProtectionPolicy
)

Guard: Any = (
    module.AccountProtectionGuard
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


def test_guard_is_shadow_only() -> None:

    engine = guard()

    state = engine.initial_state(
        equity=100.0,
        current_bar=10,
    )

    result = engine.assess_new_exposure(
        state=state,
        current_equity=100.0,
        current_bar=10,
    )

    assert engine.VERSION == "1.0"

    assert engine.MODE == (
        "SHADOW_ACCOUNT_PROTECTION_RESEARCH_ONLY"
    )

    assert state.live_authorized is False

    assert result.live_authorized is False

    assert result.exposure_allowed is True


def test_initial_state_starts_at_equity_peak() -> None:

    state = guard().initial_state(
        equity=63.35,
        current_bar=100,
    )

    assert state.starting_equity == pytest.approx(
        63.35
    )

    assert state.peak_equity == pytest.approx(
        63.35
    )

    assert state.current_drawdown_percent == pytest.approx(
        0.0
    )

    assert state.cooldown_until_bar == (
        100
    )


def test_new_equity_high_ratchets_peak_watermark() -> None:

    engine = guard()

    state = engine.initial_state(
        equity=100.0
    )

    observed = engine.observe_equity(
        state=state,
        current_equity=110.0,
        current_bar=1,
    )

    assert observed.valid is True

    assert observed.state_after.peak_equity == pytest.approx(
        110.0
    )

    assert observed.state_after.current_drawdown_percent == pytest.approx(
        0.0
    )


def test_drawdown_is_measured_from_high_watermark() -> None:

    engine = guard(
        max_peak_drawdown_percent=20.0
    )

    state = engine.initial_state(
        equity=100.0
    )

    state = engine.observe_equity(
        state=state,
        current_equity=110.0,
        current_bar=1,
    ).state_after

    result = engine.assess_new_exposure(
        state=state,
        current_equity=99.0,
        current_bar=2,
    )

    assert result.valid is True

    assert result.exposure_allowed is True

    assert result.current_drawdown_percent == pytest.approx(
        10.0
    )

    assert result.max_observed_drawdown_percent == pytest.approx(
        10.0
    )


def test_drawdown_limit_hard_locks_new_exposure() -> None:

    engine = guard(
        max_peak_drawdown_percent=10.0
    )

    state = engine.initial_state(
        equity=100.0
    )

    result = engine.assess_new_exposure(
        state=state,
        current_equity=90.0,
        current_bar=1,
    )

    assert result.valid is True

    assert result.exposure_allowed is False

    assert result.reason == (
        "HARD_DRAWDOWN_LOCK"
    )

    assert result.hard_locked is True

    assert result.hard_lock_reason == (
        "PEAK_DRAWDOWN_LIMIT_REACHED"
    )


def test_hard_drawdown_lock_is_sticky_after_equity_recovery() -> None:

    engine = guard()

    state = engine.initial_state(
        equity=100.0
    )

    state = engine.assess_new_exposure(
        state=state,
        current_equity=90.0,
        current_bar=1,
    ).state_after

    recovered = engine.assess_new_exposure(
        state=state,
        current_equity=105.0,
        current_bar=2,
    )

    assert recovered.current_drawdown_percent == pytest.approx(
        0.0
    )

    assert recovered.hard_locked is True

    assert recovered.exposure_allowed is False

    assert recovered.reason == (
        "HARD_DRAWDOWN_LOCK"
    )


def test_single_loss_starts_configured_cooldown() -> None:

    engine = guard()

    state = engine.initial_state(
        equity=100.0,
        current_bar=10,
    )

    closed = engine.record_basket_close(
        state=state,
        realized_pnl=-1.0,
        equity_after_close=99.0,
        current_bar=10,
    )

    assert closed.valid is True

    assert closed.action == (
        "RECORD_LOSS"
    )

    assert closed.state_after.consecutive_losses == (
        1
    )

    assert closed.state_after.cooldown_until_bar == (
        15
    )

    blocked = engine.assess_new_exposure(
        state=closed.state_after,
        current_equity=99.0,
        current_bar=14,
    )

    assert blocked.exposure_allowed is False

    assert blocked.reason == (
        "LOSS_COOLDOWN_ACTIVE"
    )

    assert blocked.cooldown_remaining_bars == (
        1
    )


def test_cooldown_expires_exactly_on_expiry_bar() -> None:

    engine = guard()

    state = engine.initial_state(
        equity=100.0,
        current_bar=10,
    )

    state = engine.record_basket_close(
        state=state,
        realized_pnl=-1.0,
        equity_after_close=99.0,
        current_bar=10,
    ).state_after

    result = engine.assess_new_exposure(
        state=state,
        current_equity=99.0,
        current_bar=15,
    )

    assert result.valid is True

    assert result.cooldown_remaining_bars == (
        0
    )

    assert result.exposure_allowed is True

    assert result.reason == (
        "OK_ACCOUNT_PROTECTION"
    )


def test_loss_streak_extends_cooldown() -> None:

    engine = guard()

    state = engine.initial_state(
        equity=100.0
    )

    state = engine.record_basket_close(
        state=state,
        realized_pnl=-0.50,
        equity_after_close=99.50,
        current_bar=1,
    ).state_after

    state = engine.record_basket_close(
        state=state,
        realized_pnl=-0.50,
        equity_after_close=99.00,
        current_bar=6,
    ).state_after

    third = engine.record_basket_close(
        state=state,
        realized_pnl=-0.50,
        equity_after_close=98.50,
        current_bar=11,
    )

    assert third.state_after.consecutive_losses == (
        3
    )

    assert third.state_after.cooldown_until_bar == (
        41
    )

    blocked = engine.assess_new_exposure(
        state=third.state_after,
        current_equity=98.50,
        current_bar=20,
    )

    assert blocked.exposure_allowed is False

    assert blocked.cooldown_remaining_bars == (
        21
    )


def test_winning_close_resets_loss_streak_without_shortening_cooldown() -> None:

    engine = guard()

    state = engine.initial_state(
        equity=100.0
    )

    state = engine.record_basket_close(
        state=state,
        realized_pnl=-1.0,
        equity_after_close=99.0,
        current_bar=10,
    ).state_after

    won = engine.record_basket_close(
        state=state,
        realized_pnl=0.50,
        equity_after_close=99.50,
        current_bar=11,
    )

    assert won.state_after.consecutive_losses == (
        0
    )

    assert won.state_after.cooldown_until_bar == (
        15
    )


def test_flat_close_does_not_reset_existing_loss_streak() -> None:

    engine = guard()

    state = engine.initial_state(
        equity=100.0
    )

    state = engine.record_basket_close(
        state=state,
        realized_pnl=-1.0,
        equity_after_close=99.0,
        current_bar=1,
    ).state_after

    flat = engine.record_basket_close(
        state=state,
        realized_pnl=0.0,
        equity_after_close=99.0,
        current_bar=2,
    )

    assert flat.action == (
        "RECORD_FLAT"
    )

    assert flat.state_after.consecutive_losses == (
        1
    )


def test_non_monotonic_bar_fails_without_state_mutation() -> None:

    engine = guard()

    state = engine.initial_state(
        equity=100.0,
        current_bar=10,
    )

    result = engine.assess_new_exposure(
        state=state,
        current_equity=100.0,
        current_bar=9,
    )

    assert result.valid is False

    assert result.exposure_allowed is False

    assert result.reason == (
        "NON_MONOTONIC_BAR"
    )

    assert result.state_after == (
        state
    )


def test_invalid_close_pnl_fails_without_state_mutation() -> None:

    engine = guard()

    state = engine.initial_state(
        equity=100.0
    )

    result = engine.record_basket_close(
        state=state,
        realized_pnl=float("nan"),
        equity_after_close=100.0,
        current_bar=1,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_REALIZED_PNL"
    )

    assert result.state_after == (
        state
    )


def test_zero_equity_triggers_full_drawdown_lock() -> None:

    engine = guard(
        max_peak_drawdown_percent=10.0
    )

    state = engine.initial_state(
        equity=100.0
    )

    result = engine.assess_new_exposure(
        state=state,
        current_equity=0.0,
        current_bar=1,
    )

    assert result.valid is True

    assert result.current_drawdown_percent == pytest.approx(
        100.0
    )

    assert result.hard_locked is True

    assert result.exposure_allowed is False


def test_policy_rejects_streak_cooldown_shorter_than_normal_cooldown() -> None:

    with pytest.raises(
        ValueError,
        match="cannot be shorter",
    ):

        Policy(
            cooldown_bars_after_loss=10,
            cooldown_bars_after_loss_streak=5,
        )