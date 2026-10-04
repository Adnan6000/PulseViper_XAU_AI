from __future__ import annotations

from pathlib import Path


SCRIPT = (
    Path(__file__)
    .resolve()
    .parent
    /
    "run_xauusd_r03_market_freshness_precheck.py"
)


def source() -> str:

    return SCRIPT.read_text(
        encoding="utf-8"
    )


def test_01_script_exists() -> None:
    assert SCRIPT.is_file()


def test_02_read_only_facade() -> None:
    assert (
        "MT5ReadOnlyCapabilityFacade"
        in source()
    )


def test_03_read_only_adapter() -> None:
    assert (
        "MT5ReadOnlyForwardAcquisitionAdapter"
        in source()
    )


def test_04_auto_timestamp_basis() -> None:
    assert (
        'timestamp_basis="AUTO"'
        in source()
    )


def test_05_timestamp_detection() -> None:
    assert (
        "detect_timestamp_basis_from_tick"
        in source()
    )


def test_06_timestamp_failure_caught() -> None:
    assert (
        "TimestampBasisResolutionError"
        in source()
    )


def test_07_ready_status() -> None:
    assert (
        "R03_MARKET_PRECHECK_STATUS=READY"
        in source()
    )


def test_08_not_ready_status() -> None:
    assert (
        "R03_MARKET_PRECHECK_STATUS=MARKET_NOT_READY"
        in source()
    )


def test_09_no_capture() -> None:
    assert (
        "capture_new_observation_from_snapshot"
        not in source()
    )


def test_10_no_maturation() -> None:
    assert (
        "mature_pending_from_snapshot"
        not in source()
    )


def test_11_no_order_send() -> None:
    assert "order_send(" not in source()


def test_12_no_order_check() -> None:
    assert "order_check(" not in source()


def test_13_no_model_fit() -> None:
    assert ".fit(" not in source()


def test_14_no_test_access() -> None:
    assert "load_test(" not in source()


def test_15_no_validation_access() -> None:
    assert "load_validation(" not in source()


def test_16_ledgers_not_written() -> None:
    assert (
        "LEDGERS_WRITTEN=false"
        in source()
    )


def test_17_live_blocked() -> None:
    assert (
        "LIVE_AUTHORIZED=false"
        in source()
    )


def test_18_execution_blocked() -> None:
    assert (
        "EXECUTION_AUTHORIZED=false"
        in source()
    )