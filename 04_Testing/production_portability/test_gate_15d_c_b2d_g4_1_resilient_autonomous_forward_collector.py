from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


MODULE_PATH = (
    Path(__file__).resolve().parent
    / "run_xauusd_gate_15d_c_b2d_g4_1_resilient_autonomous_forward_collector.py"
)

spec = importlib.util.spec_from_file_location(
    "g4_1_collector",
    MODULE_PATH,
)

assert spec
assert spec.loader

g4: Any = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    g4
)


def source() -> str:
    return MODULE_PATH.read_text(
        encoding="utf-8"
    )


def test_01_defaults_are_safe() -> None:

    assert g4.DEFAULT_TARGET_MATURED == 30
    assert g4.DEFAULT_POLL_SECONDS >= 10
    assert g4.DEFAULT_RETRY_SECONDS >= 10

    assert (
        g4.PERFORMANCE_EVALUATION_AUTHORIZED
        is False
    )

    assert (
        g4.PNL_EVALUATION_AUTHORIZED
        is False
    )

    assert g4.LIVE_AUTHORIZED is False
    assert g4.EXECUTION_AUTHORIZED is False


def test_02_log_is_local_shadow_runtime() -> None:

    path = str(
        g4.LOG_PATH
    ).replace(
        "\\",
        "/",
    )

    assert "/01_Data/Shadow/" in path
    assert path.endswith(".log")


def test_03_parse_kv() -> None:

    assert g4.parse_kv(
        "A=1\n"
        "B=true\n"
        "X\n"
        "C=hello=world\n"
    ) == {
        "A": "1",
        "B": "true",
        "C": "hello=world",
    }


def test_04_common_safety_accepts_false() -> None:

    g4.verify_common_safety(
        {
            "LIVE_AUTHORIZED": "false",
            "EXECUTION_AUTHORIZED": "false",
            "PERFORMANCE_EVALUATED": "false",
            "PNL_EVALUATED": "false",
        }
    )


def test_05_common_safety_rejects_live_true() -> None:

    try:
        g4.verify_common_safety(
            {
                "LIVE_AUTHORIZED": "true",
                "EXECUTION_AUTHORIZED": "false",
            }
        )

    except g4.G41CollectorError:
        return

    raise AssertionError(
        "Expected fail-closed rejection"
    )


def test_06_positive_int_parser() -> None:

    assert (
        g4.parse_positive_int(
            {"X": "0"},
            "X",
        )
        ==
        0
    )

    assert (
        g4.parse_positive_int(
            {"X": "30"},
            "X",
        )
        ==
        30
    )


def test_07_negative_integer_rejected() -> None:

    try:
        g4.parse_positive_int(
            {"X": "-1"},
            "X",
        )

    except g4.G41CollectorError:
        return

    raise AssertionError(
        "Expected negative integer rejection"
    )


def test_08_evidence_paths_are_narrow() -> None:

    assert g4.G1_EVIDENCE_REL.endswith(
        "g1_genuine_anchored_forward_capture_evidence.json"
    )

    assert g4.G2_EVIDENCE_REL.endswith(
        "g2_genuine_outcome_maturation_evidence.json"
    )


def test_09_no_force_or_destructive_git() -> None:

    text = source()

    forbidden = (
        "--force",
        "--force-with-lease",
        'git("reset"',
        'git("restore"',
        'git("checkout"',
        'git("clean"',
    )

    for token in forbidden:
        assert token not in text


def test_10_no_order_api_literals() -> None:

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


def test_11_thin_orchestrator() -> None:

    text = source()

    assert "G1_RUNNER" in text
    assert "G2_RUNNER" in text
    assert "G3_RUNNER" in text
    assert "MetaTrader5" not in text


def test_12_wait_requires_single_pending() -> None:

    text = source()

    assert (
        '"WAIT_WITH_UNEXPECTED_PENDING_COUNT"'
        in text
    )


def test_13_g2_sequence_is_preserved() -> None:

    text = source()

    dry = text.index(
        "dry = run_g2_dry"
    )

    first = text.index(
        "first = run_g2_first_append"
    )

    duplicate = text.index(
        "duplicate = run_g2_idempotency"
    )

    assert dry < first < duplicate


def test_14_target_stops_before_next_capture() -> None:

    text = source()

    target = text.index(
        "if matured >= target_matured"
    )

    capture = text.index(
        'if action == "RUN_G1_CAPTURE"'
    )

    assert target < capture


def test_15_remote_movement_stays_fail_closed() -> None:

    text = source()

    assert (
        "REMOTE_MOVED_BEFORE_EVIDENCE_COMMIT"
        in text
    )

    assert (
        "REMOTE_MOVED_AFTER_LOCAL_COMMIT"
        in text
    )

    assert (
        "REMOTE_MOVED_DURING_PUSH_RETRY"
        in text
    )


def test_16_fetch_has_retry_loop() -> None:

    text = source()

    assert (
        "def resilient_fetch_origin"
        in text
    )

    assert (
        "TRANSIENT_WAIT"
        in text
    )

    assert (
        'git(\n            "fetch",\n            "origin"'
        in text
    )


def test_17_g3_transient_fetch_is_retryable() -> None:

    text = source()

    assert (
        "def run_g3_resilient"
        in text
    )

    assert (
        "is_transient_git_fetch_failure"
        in text
    )

    assert (
        "G3_TRANSIENT_WAIT"
        in text
    )


def test_18_g1_is_not_automatically_retried() -> None:

    text = source()

    assert "def run_g1()" in text

    section = text[
        text.index("def run_g1()"):
        text.index("def run_g2_dry")
    ]

    assert "while True" not in section


def test_19_push_has_retry_but_divergence_guard() -> None:

    text = source()

    assert (
        "PUSH_TRANSIENT_WAIT"
        in text
    )

    assert (
        "push_retry_guard"
        in text
    )

    assert (
        "REMOTE_MOVED_DURING_PUSH_RETRY"
        in text
    )


def test_20_retry_is_interruptible() -> None:

    text = source()

    assert "KeyboardInterrupt" in text

    assert (
        "G4_1_AUTONOMOUS_COLLECTOR_STATUS="
        in text
    )


def test_21_no_performance_or_pnl_enablement() -> None:

    text = source()

    assert (
        "PERFORMANCE_EVALUATION_AUTHORIZED = False"
        in text
    )

    assert (
        "PNL_EVALUATION_AUTHORIZED = False"
        in text
    )

    assert (
        "LIVE_AUTHORIZED = False"
        in text
    )

    assert (
        "EXECUTION_AUTHORIZED = False"
        in text
    )


def test_22_retry_default_is_one_minute() -> None:

    assert (
        g4.DEFAULT_RETRY_SECONDS
        ==
        60
    )