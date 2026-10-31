"""
Offline tests for CompoundingPnLLedger v1.0.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_pnl_ledger"
)


Ledger: Any = (
    module.CompoundingPnLLedger
)


def ledger() -> Any:

    return Ledger()


def test_initial_state() -> None:

    state = ledger().initial_state(
        balance=10.0
    )

    assert state.balance_start == pytest.approx(
        10.0
    )

    assert state.realized_profit == pytest.approx(
        0.0
    )

    assert state.floating_profit == pytest.approx(
        0.0
    )

    assert state.lifecycle_profit == pytest.approx(
        0.0
    )

    assert state.equity == pytest.approx(
        10.0
    )

    assert state.live_authorized is False


def test_first_leg_immediately_pays_spread() -> None:

    engine = ledger()

    state = engine.initial_state(
        balance=10.0
    )

    transition = engine.add_exposure(
        state=state,
        added_volume=0.01,
        added_margin=2.19,
        added_spread_cost=0.26,
        new_projected_basket_risk=0.50,
    )

    assert transition.valid is True

    result = transition.state_after

    assert result.active_volume == pytest.approx(
        0.01
    )

    assert result.margin_used == pytest.approx(
        2.19
    )

    assert result.floating_profit == pytest.approx(
        -0.26
    )

    assert result.lifecycle_profit == pytest.approx(
        -0.26
    )

    assert result.equity == pytest.approx(
        9.74
    )

    assert result.free_margin == pytest.approx(
        7.55
    )

    assert result.cumulative_spread_cost == pytest.approx(
        0.26
    )


def test_mark_to_market_replaces_current_floating_profit() -> None:

    engine = ledger()

    state = engine.initial_state(
        balance=10.0
    )

    state = engine.add_exposure(
        state=state,
        added_volume=0.01,
        added_margin=2.19,
        added_spread_cost=0.26,
        new_projected_basket_risk=0.50,
    ).state_after

    marked = engine.mark_to_market(
        state=state,
        floating_profit=0.175,
    )

    assert marked.valid is True

    assert marked.state_after.floating_profit == pytest.approx(
        0.175
    )

    assert marked.state_after.lifecycle_profit == pytest.approx(
        0.175
    )

    assert marked.state_after.equity == pytest.approx(
        10.175
    )


def test_new_compounding_leg_has_immediate_spread_drag() -> None:

    engine = ledger()

    state = engine.initial_state(
        balance=10.0
    )

    state = engine.add_exposure(
        state=state,
        added_volume=0.01,
        added_margin=2.19,
        added_spread_cost=0.26,
        new_projected_basket_risk=0.50,
    ).state_after

    state = engine.mark_to_market(
        state=state,
        floating_profit=0.175,
    ).state_after

    add = engine.add_exposure(
        state=state,
        added_volume=0.01,
        added_margin=2.19,
        added_spread_cost=0.26,
        new_projected_basket_risk=1.00,
    )

    assert add.valid is True

    result = add.state_after

    # +0.175 existing net floating
    # -0.260 immediate spread on new leg
    assert result.floating_profit == pytest.approx(
        -0.085
    )

    assert result.lifecycle_profit == pytest.approx(
        -0.085
    )

    assert result.active_volume == pytest.approx(
        0.02
    )

    assert result.margin_used == pytest.approx(
        4.38
    )

    assert result.cumulative_spread_cost == pytest.approx(
        0.52
    )

    assert result.lifecycle_risk_watermark == pytest.approx(
        1.00
    )


def test_risk_watermark_never_decreases_on_add() -> None:

    engine = ledger()

    state = engine.initial_state(
        balance=10.0
    )

    first = engine.add_exposure(
        state=state,
        added_volume=0.01,
        added_margin=2.19,
        added_spread_cost=0.26,
        new_projected_basket_risk=0.50,
    ).state_after

    assert first.lifecycle_risk_watermark == pytest.approx(
        0.50
    )

    second = engine.add_exposure(
        state=first,
        added_volume=0.01,
        added_margin=2.19,
        added_spread_cost=0.26,
        new_projected_basket_risk=1.00,
    ).state_after

    assert second.lifecycle_risk_watermark == pytest.approx(
        1.00
    )


def test_partial_booking_preserves_total_lifecycle_profit() -> None:

    engine = ledger()

    state = engine.initial_state(
        balance=10.0
    )

    state = engine.add_exposure(
        state=state,
        added_volume=0.02,
        added_margin=4.38,
        added_spread_cost=0.52,
        new_projected_basket_risk=1.00,
    ).state_after

    state = engine.mark_to_market(
        state=state,
        floating_profit=0.85,
    ).state_after

    partial = engine.partial_close(
        state=state,
        close_volume=0.01,
        remaining_margin=2.19,
    )

    assert partial.valid is True

    result = partial.state_after

    assert partial.realized_delta == pytest.approx(
        0.425
    )

    assert result.realized_profit == pytest.approx(
        0.425
    )

    assert result.floating_profit == pytest.approx(
        0.425
    )

    # Critical invariant.
    assert result.lifecycle_profit == pytest.approx(
        0.85
    )

    assert result.lifecycle_r == pytest.approx(
        0.85
    )

    assert result.lifecycle_risk_watermark == pytest.approx(
        1.00
    )


def test_partial_booking_keeps_equity_constant_before_commission() -> None:

    engine = ledger()

    state = engine.initial_state(
        balance=10.0
    )

    state = engine.add_exposure(
        state=state,
        added_volume=0.02,
        added_margin=4.38,
        added_spread_cost=0.52,
        new_projected_basket_risk=1.00,
    ).state_after

    state = engine.mark_to_market(
        state=state,
        floating_profit=0.85,
    ).state_after

    equity_before = (
        state.equity
    )

    result = engine.partial_close(
        state=state,
        close_volume=0.01,
        remaining_margin=2.19,
    ).state_after

    assert result.equity == pytest.approx(
        equity_before
    )

    # Margin release increases free margin.
    assert result.free_margin > (
        state.free_margin
    )


def test_realized_plus_floating_drives_runner_r() -> None:

    engine = ledger()

    state = engine.initial_state(
        balance=10.0
    )

    state = engine.add_exposure(
        state=state,
        added_volume=0.02,
        added_margin=4.38,
        added_spread_cost=0.52,
        new_projected_basket_risk=1.00,
    ).state_after

    state = engine.mark_to_market(
        state=state,
        floating_profit=0.85,
    ).state_after

    state = engine.partial_close(
        state=state,
        close_volume=0.01,
        remaining_margin=2.19,
    ).state_after

    # Already realized:
    #     +0.425
    #
    # To reach lifecycle +1.50:
    # remaining floating only needs:
    #     1.50 - 0.425 = 1.075
    marked = engine.mark_to_market(
        state=state,
        floating_profit=1.075,
    )

    assert marked.state_after.realized_profit == pytest.approx(
        0.425
    )

    assert marked.state_after.floating_profit == pytest.approx(
        1.075
    )

    assert marked.state_after.lifecycle_profit == pytest.approx(
        1.50
    )

    assert marked.state_after.lifecycle_r == pytest.approx(
        1.50
    )


def test_close_all_moves_floating_into_realized_without_changing_lifecycle_profit() -> None:

    engine = ledger()

    state = engine.initial_state(
        balance=10.0
    )

    state = engine.add_exposure(
        state=state,
        added_volume=0.01,
        added_margin=2.19,
        added_spread_cost=0.26,
        new_projected_basket_risk=0.50,
    ).state_after

    state = engine.mark_to_market(
        state=state,
        floating_profit=0.75,
    ).state_after

    lifecycle_before = (
        state.lifecycle_profit
    )

    closed = engine.close_all(
        state=state
    )

    assert closed.valid is True

    result = closed.state_after

    assert result.active_volume == pytest.approx(
        0.0
    )

    assert result.margin_used == pytest.approx(
        0.0
    )

    assert result.floating_profit == pytest.approx(
        0.0
    )

    assert result.realized_profit == pytest.approx(
        0.75
    )

    assert result.lifecycle_profit == pytest.approx(
        lifecycle_before
    )


def test_invalid_partial_close_fails_closed() -> None:

    engine = ledger()

    state = engine.initial_state(
        balance=10.0
    )

    result = engine.partial_close(
        state=state,
        close_volume=0.01,
        remaining_margin=0.0,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_PARTIAL_CLOSE"
    )

    assert result.state_after == state


def test_ledger_never_authorizes_live_execution() -> None:

    engine = ledger()

    state = engine.initial_state(
        balance=10.0
    )

    result = engine.add_exposure(
        state=state,
        added_volume=0.01,
        added_margin=2.19,
        added_spread_cost=0.26,
        new_projected_basket_risk=0.50,
    )

    assert result.live_authorized is False

    assert result.state_after.live_authorized is False

    assert result.mode == (
        "SHADOW_COMPOUNDING_PNL_ACCOUNTING_ONLY"
    )