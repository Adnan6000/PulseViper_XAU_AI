from __future__ import annotations

import importlib
import inspect
from typing import Any


runner: Any = importlib.import_module(
    "04_Testing.production_portability."
    "run_xauusd_gate_15d_c_b2d_g3_forward_sample_controller"
)


def test_01_identity() -> None:

    assert (
        runner.GATE_ID
        ==
        "GATE_15D_C_B2D_G3_FORWARD_SAMPLE_CONTROLLER"
    )

    assert (
        runner.REQUIRED_FUTURE_M5_BARS
        ==
        12
    )


def test_02_no_authorized_performance_or_execution() -> None:

    assert (
        runner.PERFORMANCE_EVALUATION_AUTHORIZED
        is False
    )

    assert (
        runner.PNL_EVALUATION_AUTHORIZED
        is False
    )

    assert (
        runner.LIVE_AUTHORIZED
        is False
    )

    assert (
        runner.EXECUTION_AUTHORIZED
        is False
    )


def test_03_raw_mt5_boundary() -> None:

    assert (
        runner.RAW_MT5_CALLS
        ==
        (
            "initialize",
            "shutdown",
        )
    )


def test_04_no_execution_capabilities() -> None:

    source = inspect.getsource(
        runner
    )

    forbidden = (
        "order_send",
        "order_check",
        "order_calc_margin",
        "order_calc_profit",
        "positions_get",
        "orders_get",
        "history_deals_get",
    )

    for item in forbidden:
        assert item not in source


def test_05_controller_does_not_append_ledgers() -> None:

    source = inspect.getsource(
        runner
    )

    forbidden = (
        "ObservationLedger.append",
        "AnchorLedger.append",
        "OutcomeLedger.append",
        "observations.append(",
        "anchors.append(",
        "outcomes.append(",
        "outcome_ledger.append(",
        "observation_ledger.append(",
        "anchor_ledger.append(",
    )

    for item in forbidden:
        assert item not in source


def test_06_no_performance_metrics() -> None:

    source = inspect.getsource(
        runner
    ).lower()

    forbidden = (
        "accuracy_score",
        "win_rate",
        "profit_factor",
        "drawdown",
        "sharpe",
        "pnl =",
    )

    for item in forbidden:
        assert item not in source


def test_07_no_pending_means_g1_capture() -> None:

    source = inspect.getsource(
        runner.run_controller
    )

    assert (
        '"RUN_G1_CAPTURE"'
        in source
    )


def test_08_pending_not_ready_means_wait() -> None:

    source = inspect.getsource(
        runner.evaluate_oldest_pending
    )

    assert (
        '"WAIT_FOR_MATURATION"'
        in source
    )


def test_09_ready_pending_means_g2_append() -> None:

    source = inspect.getsource(
        runner.evaluate_oldest_pending
    )

    assert (
        '"RUN_G2_APPEND"'
        in source
    )


def test_10_matured_ids_are_excluded_from_pending() -> None:

    source = inspect.getsource(
        runner.load_runtime_state
    )

    assert (
        "pending_ids"
        in source
    )

    assert (
        "set(outcome_by_id)"
        in source
    )


def test_11_requires_true_forward_eligibility() -> None:

    source = inspect.getsource(
        runner.load_runtime_state
    )

    assert (
        "is_true_forward_eligible"
        in source
    )


def test_12_clean_repository_required() -> None:

    source = inspect.getsource(
        runner.verify_repository_authority
    )

    assert (
        '"status"'
        in source
    )

    assert (
        '"--porcelain"'
        in source
    )

    assert (
        "WORKTREE_NOT_CLEAN"
        in source
    )
