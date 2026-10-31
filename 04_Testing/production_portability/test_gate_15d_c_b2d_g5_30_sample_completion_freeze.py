from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


MODULE_PATH = (
    Path(__file__).resolve().parent
    / "run_xauusd_gate_15d_c_b2d_g5_30_sample_completion_freeze.py"
)

spec = importlib.util.spec_from_file_location(
    "g5_freeze",
    MODULE_PATH,
)

assert spec
assert spec.loader

g5: Any = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    g5
)


def source() -> str:

    return MODULE_PATH.read_text(
        encoding="utf-8"
    )


def test_01_target_is_exactly_30() -> None:

    assert (
        g5.EXPECTED_MATURED_COUNT
        ==
        30
    )

    assert (
        g5.EXPECTED_PENDING_COUNT
        ==
        0
    )


def test_02_expected_counts_are_frozen() -> None:

    assert (
        g5.EXPECTED_OBSERVATION_COUNT
        ==
        32
    )

    assert (
        g5.EXPECTED_ANCHOR_COUNT
        ==
        30
    )

    assert (
        g5.EXPECTED_OUTCOME_COUNT
        ==
        30
    )

    assert (
        g5.EXPECTED_UNANCHORED_COUNT
        ==
        2
    )


def test_03_base_authority_is_current_completion_commit() -> None:

    assert (
        g5.BASE_AUTHORITY_COMMIT
        ==
        "679cab31cdaef786e7059f545133a0bf660fed7f"
    )


def test_04_runtime_ledgers_are_hash_only() -> None:

    text = source()

    assert (
        "raw_sha256"
        in text
    )

    assert (
        "RUNTIME_LEDGER_CHANGED_DURING_FREEZE"
        in text
    )


def test_05_g3_is_read_only_verification_authority() -> None:

    text = source()

    assert (
        "run_g3_read_only_verification"
        in text
    )

    assert (
        "G3_RUNNER_REL"
        in text
    )


def test_06_no_g1_or_g2_execution() -> None:

    text = source()

    assert (
        "run_g1("
        not in text
    )

    assert (
        "run_g2_dry("
        not in text
    )

    assert (
        "run_g2_first_append("
        not in text
    )


def test_07_no_order_api_capabilities() -> None:

    text = source()

    forbidden = (
        "order_send(",
        "order_check(",
        "order_calc_margin(",
        "order_calc_profit(",
        "positions_get(",
        "orders_get(",
        "history_orders_get(",
        "history_deals_get(",
    )

    for token in forbidden:
        assert token not in text


def test_08_no_destructive_git() -> None:

    text = source()

    forbidden = (
        "--force",
        "--force-with-lease",
        'git_output("reset"',
        'git_output("restore"',
        'git_output("checkout"',
        'git_output("clean"',
    )

    for token in forbidden:
        assert token not in text


def test_09_no_performance_evaluation() -> None:

    text = source()

    assert (
        '"performance_evaluated": False'
        in text
    )

    assert (
        '"pnl_evaluated": False'
        in text
    )


def test_10_live_and_execution_remain_false() -> None:

    text = source()

    assert (
        '"live_authorized": False'
        in text
    )

    assert (
        '"execution_authorized": False'
        in text
    )


def test_11_completion_requires_pending_zero() -> None:

    text = source()

    assert (
        "EXPECTED_PENDING_COUNT"
        in text
    )

    assert (
        "PENDING_COUNT_MISMATCH"
        in text
    )


def test_12_completion_requires_30_outcomes() -> None:

    text = source()

    assert (
        "OUTCOME_COUNT_MISMATCH"
        in text
    )

    assert (
        "MATURED_COUNT_MISMATCH"
        in text
    )


def test_13_historical_unanchored_count_is_explicit() -> None:

    text = source()

    assert (
        "UNANCHORED_COUNT_MISMATCH"
        in text
    )


def test_14_freeze_does_not_initialize_mt5() -> None:

    text = source()

    assert "MetaTrader5" not in text

    assert (
        '"mt5_initialized": False'
        in text
    )


def test_15_freeze_declares_no_market_acquisition() -> None:

    text = source()

    assert (
        '"market_data_acquired": False'
        in text
    )


def test_16_hash_semantics_are_canonical_lf() -> None:

    text = source()

    assert (
        "GIT_TEXT_CANONICAL_LF_SHA256"
        in text
    )


def test_17_target_reached_is_frozen() -> None:

    text = source()

    assert (
        '"target_reached": True'
        in text
    )


def test_18_next_action_must_be_run_g1_capture() -> None:

    text = source()

    assert (
        '"RUN_G1_CAPTURE"'
        in text
    )

    assert (
        "UNEXPECTED_G3_NEXT_ACTION"
        in text
    )