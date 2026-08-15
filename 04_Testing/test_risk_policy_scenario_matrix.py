"""
Offline tests for RiskPolicyScenarioMatrix v1.0.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Shadow.risk_policy_scenario_matrix"
)

broker_module: Any = importlib.import_module(
    "02_AI.Shadow.broker_aware_risk_engine"
)

planner_module: Any = importlib.import_module(
    "02_AI.Shadow.bootstrap_compounding_planner"
)


Matrix: Any = (
    module.RiskPolicyScenarioMatrix
)

BrokerPolicy: Any = (
    broker_module.BrokerRiskPolicy
)

BasketPolicy: Any = (
    planner_module.BootstrapCompoundingPolicy
)


def test_matrix_is_shadow_only() -> None:

    result = Matrix().evaluate()

    assert result.valid is True

    assert result.live_authorized is False

    assert result.mode == (
        "SHADOW_RISK_POLICY_SCENARIO_MATRIX_ONLY"
    )

    assert all(
        row.live_authorized is False
        for row
        in result.rows
    )


def test_default_matrix_contains_required_balance_scenarios() -> None:

    result = Matrix().evaluate()

    assert tuple(
        row.balance
        for row
        in result.rows
    ) == (
        3.0,
        5.0,
        10.0,
        20.0,
        21.0,
        50.0,
        63.35,
        100.0,
    )


def test_current_default_policies_are_cross_policy_aligned() -> None:

    result = Matrix().evaluate()

    assert result.valid is True

    assert result.policy_alignment_valid is True

    assert result.alignment_violations == ()


@pytest.mark.parametrize(
    (
        "balance",
        "micro_eligible",
        "planner_mode",
        "standard_override",
        "micro_override",
    ),
    (
        (
            3.0,
            True,
            "MICRO_BOOTSTRAP_BASKET",
            True,
            False,
        ),
        (
            5.0,
            True,
            "MICRO_BOOTSTRAP_BASKET",
            True,
            False,
        ),
        (
            10.0,
            True,
            "MICRO_BOOTSTRAP_BASKET",
            True,
            False,
        ),
        (
            20.0,
            True,
            "MICRO_BOOTSTRAP_BASKET",
            True,
            False,
        ),
        (
            21.0,
            False,
            "STANDARD_COMPOUND_BASKET",
            False,
            True,
        ),
        (
            63.35,
            False,
            "STANDARD_COMPOUND_BASKET",
            False,
            True,
        ),
        (
            100.0,
            False,
            "STANDARD_COMPOUND_BASKET",
            False,
            True,
        ),
    ),
)
def test_mode_boundary_matrix(
    balance: float,
    micro_eligible: bool,
    planner_mode: str,
    standard_override: bool,
    micro_override: bool,
) -> None:

    row = Matrix().evaluate_account(
        balance=balance
    )

    assert row.valid is True

    assert (
        row.broker_micro_eligible
        is
        micro_eligible
    )

    assert (
        row.planner_basket_mode_by_risk_base
        ==
        planner_mode
    )

    assert (
        row.standard_override_required_if_selected
        is
        standard_override
    )

    assert (
        row.micro_override_required_if_selected
        is
        micro_override
    )


@pytest.mark.parametrize(
    (
        "balance",
        "expected_target",
        "expected_standard_hard",
        "expected_standard_basket",
    ),
    (
        (
            3.0,
            0.0225,
            0.03,
            0.06,
        ),
        (
            5.0,
            0.0375,
            0.05,
            0.10,
        ),
        (
            10.0,
            0.075,
            0.10,
            0.20,
        ),
        (
            20.0,
            0.15,
            0.20,
            0.40,
        ),
        (
            21.0,
            0.1575,
            0.21,
            0.42,
        ),
        (
            63.35,
            0.475125,
            0.6335,
            1.267,
        ),
        (
            100.0,
            0.75,
            1.00,
            2.00,
        ),
    ),
)
def test_standard_monetary_caps(
    balance: float,
    expected_target: float,
    expected_standard_hard: float,
    expected_standard_basket: float,
) -> None:

    row = Matrix().evaluate_account(
        balance=balance
    )

    assert (
        row.standard_target_risk_amount
        ==
        pytest.approx(
            expected_target
        )
    )

    assert (
        row.standard_hard_single_leg_amount
        ==
        pytest.approx(
            expected_standard_hard
        )
    )

    assert (
        row.standard_basket_loss_cap
        ==
        pytest.approx(
            expected_standard_basket
        )
    )


@pytest.mark.parametrize(
    (
        "balance",
        "expected_cap",
    ),
    (
        (
            3.0,
            0.5001,
        ),
        (
            5.0,
            0.8335,
        ),
        (
            10.0,
            1.667,
        ),
        (
            20.0,
            2.0,
        ),
    ),
)
def test_micro_bootstrap_floor_percent_ceiling(
    balance: float,
    expected_cap: float,
) -> None:

    row = Matrix().evaluate_account(
        balance=balance
    )

    assert row.broker_micro_eligible is True

    assert (
        row.micro_basket_loss_cap
        ==
        pytest.approx(
            expected_cap
        )
    )


def test_micro_capacity_is_not_reported_as_available_above_range() -> None:

    row = Matrix().evaluate_account(
        balance=21.0
    )

    assert row.broker_micro_eligible is False

    assert row.micro_basket_loss_cap == pytest.approx(
        0.0
    )

    assert row.micro_basket_margin_cap_amount == pytest.approx(
        0.0
    )

    assert row.micro_basket_spread_cap == pytest.approx(
        0.0
    )


def test_risk_base_uses_lower_of_balance_and_equity() -> None:

    row = Matrix().evaluate_account(
        balance=100.0,
        equity=80.0,
        free_margin=70.0,
    )

    assert row.valid is True

    assert row.risk_base == pytest.approx(
        80.0
    )

    assert row.standard_target_risk_amount == pytest.approx(
        0.60
    )

    assert row.standard_hard_single_leg_amount == pytest.approx(
        0.80
    )

    assert row.standard_basket_loss_cap == pytest.approx(
        1.60
    )


def test_broker_margin_and_basket_margin_use_distinct_bases() -> None:

    row = Matrix().evaluate_account(
        balance=100.0,
        equity=80.0,
        free_margin=20.0,
    )

    assert (
        row.standard_broker_margin_cap_amount
        ==
        pytest.approx(
            5.0
        )
    )

    assert (
        row.standard_basket_margin_cap_amount
        ==
        pytest.approx(
            28.0
        )
    )


def test_micro_margin_capacity_uses_free_margin_for_broker_gate() -> None:

    row = Matrix().evaluate_account(
        balance=10.0,
        equity=8.0,
        free_margin=5.0,
    )

    assert row.risk_base == pytest.approx(
        8.0
    )

    assert (
        row.micro_broker_margin_cap_amount
        ==
        pytest.approx(
            4.0
        )
    )

    assert (
        row.micro_basket_margin_cap_amount
        ==
        pytest.approx(
            6.8
        )
    )


def test_standard_spread_caps_are_explicit() -> None:

    row = Matrix().evaluate_account(
        balance=63.35
    )

    assert (
        row.standard_broker_spread_hard_cap
        ==
        pytest.approx(
            0.6335
        )
    )

    assert (
        row.standard_basket_spread_cap
        ==
        pytest.approx(
            1.267
        )
    )


def test_micro_basket_spread_cap_tracks_micro_loss_cap() -> None:

    row = Matrix().evaluate_account(
        balance=10.0
    )

    assert (
        row.micro_basket_spread_cap
        ==
        pytest.approx(
            row.micro_basket_loss_cap
        )
    )


def test_compounding_controls_are_exposed() -> None:

    row = Matrix().evaluate_account(
        balance=63.35
    )

    assert row.max_simultaneous_legs == 3

    assert row.max_total_volume == pytest.approx(
        0.03
    )

    assert row.add_only_after_profit is True

    assert (
        row.minimum_profit_r_before_add
        ==
        pytest.approx(
            0.25
        )
    )


def test_small_account_standard_selection_requires_reconciliation_override() -> None:

    row = Matrix().evaluate_account(
        balance=10.0
    )

    assert (
        row.planner_basket_mode_by_risk_base
        ==
        "MICRO_BOOTSTRAP_BASKET"
    )

    assert (
        row.standard_override_required_if_selected
        is True
    )


def test_balance_21_crosses_planner_bootstrap_boundary() -> None:

    row = Matrix().evaluate_account(
        balance=21.0
    )

    assert row.planner_bootstrap_range is False

    assert (
        row.planner_basket_mode_by_risk_base
        ==
        "STANDARD_COMPOUND_BASKET"
    )

    assert (
        row.standard_override_required_if_selected
        is False
    )


def test_custom_micro_max_mismatch_is_reported() -> None:

    matrix = Matrix(
        broker_policy=BrokerPolicy(
            micro_max_balance=19.0
        ),
        basket_policy=BasketPolicy(
            compounding_enabled=True,
            bootstrap_balance_max=20.0,
        ),
    )

    result = matrix.evaluate()

    assert result.valid is True

    assert result.policy_alignment_valid is False

    assert (
        "MICRO_BOOTSTRAP_MAX_RANGE_MISMATCH"
        in
        result.alignment_violations
    )


def test_standard_single_leg_basket_inversion_is_reported() -> None:

    matrix = Matrix(
        broker_policy=BrokerPolicy(
            hard_max_risk_percent=2.5,
            target_risk_percent=0.75,
        ),
        basket_policy=BasketPolicy(
            compounding_enabled=True,
            standard_basket_hard_loss_percent=2.0,
        ),
    )

    result = matrix.evaluate()

    assert result.policy_alignment_valid is False

    assert (
        "STANDARD_SINGLE_LEG_EXCEEDS_BASKET_CAP"
        in
        result.alignment_violations
    )


@pytest.mark.parametrize(
    (
        "kwargs",
        "expected_reason",
    ),
    (
        (
            {
                "balance": 0.0,
            },
            "INVALID_BALANCE",
        ),
        (
            {
                "balance": 100.0,
                "equity": 0.0,
            },
            "INVALID_EQUITY",
        ),
        (
            {
                "balance": 100.0,
                "free_margin": -1.0,
            },
            "INVALID_FREE_MARGIN",
        ),
    ),
)
def test_invalid_account_state_fails_closed(
    kwargs: dict[
        str,
        float,
    ],
    expected_reason: str,
) -> None:

    row = Matrix().evaluate_account(
        **kwargs
    )

    assert row.valid is False

    assert row.reason == expected_reason

    assert row.live_authorized is False


def test_empty_matrix_is_rejected() -> None:

    result = Matrix().evaluate(
        balances=()
    )

    assert result.valid is False

    assert result.reason == (
        "EMPTY_SCENARIO_MATRIX"
    )

    assert result.rows == ()


def test_invalid_matrix_row_rejects_whole_matrix() -> None:

    result = Matrix().evaluate(
        balances=(
            3.0,
            0.0,
            10.0,
        )
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_SCENARIO_ROW"
    )

    assert len(
        result.rows
    ) == 3