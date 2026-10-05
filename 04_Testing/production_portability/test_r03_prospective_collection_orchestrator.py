from __future__ import annotations

from pathlib import Path


RUNNER = (
    Path(__file__)
    .resolve()
    .parent
    /
    "run_xauusd_r03_prospective_collection_orchestrator.py"
)


def text() -> str:

    return RUNNER.read_text(
        encoding="utf-8"
    )


def test_01_runner_exists() -> None:
    assert RUNNER.is_file()


def test_02_uses_precheck() -> None:
    assert (
        "run_xauusd_r03_market_freshness_precheck.py"
        in
        text()
    )


def test_03_uses_frozen_capture_runner() -> None:
    assert (
        "run_xauusd_gate_15d_c_b2d_g7_h_e_d_"
        in
        text()
    )


def test_04_uses_frozen_maturity_runner() -> None:
    assert (
        "run_xauusd_gate_15d_c_b2d_g7_h_e_c_r1_"
        in
        text()
    )


def test_05_controller_state_dispatch() -> None:
    assert (
        "ACTION_CAPTURE_NEW_OBSERVATION"
        in
        text()
    )

    assert (
        "ACTION_CHECK_PENDING_MATURITY"
        in
        text()
    )


def test_06_target_stop() -> None:
    assert (
        "ACTION_COLLECTION_TARGET_REACHED"
        in
        text()
    )


def test_07_orphan_fail_closed() -> None:
    assert (
        "ACTION_REVIEW_ORPHAN_ANCHOR"
        in
        text()
    )


def test_08_external_process_lock() -> None:
    assert (
        "LOCALAPPDATA"
        in
        text()
    )

    assert (
        "ORCHESTRATOR_ALREADY_RUNNING"
        in
        text()
    )


def test_09_no_direct_capture_logic() -> None:
    assert (
        "capture_new_observation_from_snapshot("
        not in
        text()
    )


def test_10_no_direct_maturation_logic() -> None:
    assert (
        "mature_pending_from_snapshot("
        not in
        text()
    )


def test_11_no_order_send() -> None:
    assert "order_send(" not in text()


def test_12_no_order_check() -> None:
    assert "order_check(" not in text()


def test_13_no_model_fit() -> None:
    assert ".fit(" not in text()


def test_14_no_performance_evaluation() -> None:
    assert (
        "evaluate_prospective_confirmation("
        not in
        text()
    )


def test_15_live_false() -> None:
    assert (
        "LIVE_AUTHORIZED = False"
        in
        text()
    )


def test_16_execution_false() -> None:
    assert (
        "EXECUTION_AUTHORIZED = False"
        in
        text()
    )


def test_17_pnl_false() -> None:
    assert (
        "PNL_EVALUATION_AUTHORIZED = False"
        in
        text()
    )


def test_18_performance_false() -> None:
    assert (
        "PERFORMANCE_EVALUATION_AUTHORIZED = False"
        in
        text()
    )


def test_19_wait_supported() -> None:
    assert (
        "R03_ORCHESTRATOR_STATUS=WAIT"
        in
        text()
    )


def test_20_mature_then_capture_supported() -> None:
    assert (
        "MATURED_AND_CAPTURED_NEXT"
        in
        text()
    )