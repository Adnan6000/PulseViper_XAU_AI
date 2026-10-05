from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

RUNNER = (
    Path(__file__)
    .resolve()
    .parent
    /
    "run_xauusd_gate_15d_c_b2d_g7_h_e_d_r03_reusable_capture.py"
)

FREEZE = (
    Path(__file__)
    .resolve()
    .parent
    /
    "run_xauusd_gate_15d_c_b2d_g7_h_e_d_r03_reusable_capture_freeze.py"
)


spec = importlib.util.spec_from_file_location(
    "g7hedfreeze",
    FREEZE,
)

assert spec is not None
assert spec.loader is not None

freeze: Any = (
    importlib.util.module_from_spec(
        spec
    )
)

spec.loader.exec_module(
    freeze
)


def runner_text() -> str:

    return RUNNER.read_text(
        encoding="utf-8"
    )


def freeze_text() -> str:

    return FREEZE.read_text(
        encoding="utf-8"
    )


def test_01_runner_exists() -> None:
    assert RUNNER.is_file()


def test_02_freeze_exists() -> None:
    assert FREEZE.is_file()


def test_03_base_commit_exact() -> None:
    assert (
        freeze.BASE_AUTHORITY_COMMIT
        ==
        "80c05a1270081cafd136cac40309f27302796d15"
    )


def test_04_read_only_facade() -> None:
    assert (
        "MT5ReadOnlyCapabilityFacade"
        in
        runner_text()
    )


def test_05_read_only_adapter() -> None:
    assert (
        "MT5ReadOnlyForwardAcquisitionAdapter"
        in
        runner_text()
    )


def test_06_auto_timestamp_basis() -> None:
    assert (
        'timestamp_basis="AUTO"'
        in
        runner_text()
    )


def test_07_forward_boundaries() -> None:
    assert (
        "enforce_forward_boundaries=True"
        in
        runner_text()
    )


def test_08_feature_pipeline_used() -> None:
    assert (
        "PortableFeaturePipeline"
        in
        runner_text()
    )


def test_09_controller_capture_used() -> None:
    assert (
        "capture_new_observation_from_snapshot"
        in
        runner_text()
    )


def test_10_anchor_first() -> None:
    assert (
        "ANCHOR_FIRST_THEN_OBSERVATION=true"
        in
        runner_text()
    )


def test_11_zero_pending_required() -> None:
    assert (
        "CAPTURE_REQUIRES_ZERO_PENDING"
        in
        runner_text()
    )


def test_12_target_not_reached_required() -> None:
    assert (
        "COLLECTION_TARGET_ALREADY_REACHED"
        in
        runner_text()
    )


def test_13_generic_observation_increment() -> None:
    assert (
        "POST_CAPTURE_OBSERVATION_COUNT_NOT_INCREMENTED"
        in
        runner_text()
    )


def test_14_generic_anchor_increment() -> None:
    assert (
        "POST_CAPTURE_ANCHOR_COUNT_NOT_INCREMENTED"
        in
        runner_text()
    )


def test_15_outcomes_unchanged() -> None:
    assert (
        "OUTCOME_COUNT_CHANGED_DURING_CAPTURE"
        in
        runner_text()
    )


def test_16_dates_unchanged() -> None:
    assert (
        "MATURED_DATE_COUNT_CHANGED_DURING_CAPTURE"
        in
        runner_text()
    )


def test_17_pending_becomes_one() -> None:
    assert (
        "POST_CAPTURE_PENDING_COUNT_NOT_ONE"
        in
        runner_text()
    )


def test_18_next_action_maturity() -> None:
    assert (
        "POST_CAPTURE_NEXT_ACTION_MISMATCH"
        in
        runner_text()
    )


def test_19_no_maturation_call() -> None:
    assert (
        "mature_pending_from_snapshot("
        not in
        runner_text()
    )


def test_20_no_performance_eval() -> None:
    assert (
        "evaluate_prospective_confirmation("
        not in
        runner_text()
    )


def test_21_no_order_send() -> None:
    assert "order_send(" not in runner_text()


def test_22_no_order_check() -> None:
    assert "order_check(" not in runner_text()


def test_23_no_risk_engine() -> None:
    assert "RiskEngine(" not in runner_text()


def test_24_no_trade_ready() -> None:
    assert "trade_ready" not in runner_text()


def test_25_no_fit() -> None:
    assert ".fit(" not in runner_text()


def test_26_no_test_access() -> None:
    assert "load_test(" not in runner_text()


def test_27_no_validation_access() -> None:
    assert "load_validation(" not in runner_text()


def test_28_freeze_requires_one_observation() -> None:
    assert (
        "EXPECTED_ONE_OBSERVATION"
        in
        freeze_text()
    )


def test_29_freeze_requires_one_anchor() -> None:
    assert (
        "EXPECTED_ONE_ANCHOR"
        in
        freeze_text()
    )


def test_30_freeze_requires_one_matured() -> None:
    assert (
        "EXPECTED_ONE_MATURED_OUTCOME"
        in
        freeze_text()
    )


def test_31_freeze_requires_zero_pending() -> None:
    assert (
        "EXPECTED_ZERO_PENDING"
        in
        freeze_text()
    )


def test_32_freeze_capture_action() -> None:
    assert (
        "CAPTURE_ACTION_NOT_AUTHORIZED"
        in
        freeze_text()
    )


def test_33_freeze_no_mt5_initialize() -> None:
    assert (
        "mt5.initialize("
        not in
        freeze_text()
    )


def test_34_freeze_no_capture_call() -> None:
    assert (
        "capture_new_observation_from_snapshot("
        not in
        freeze_text()
    )


def test_35_freeze_protects_state() -> None:
    assert (
        "FREEZE_CHANGED_COLLECTION_STATE"
        in
        freeze_text()
    )


def test_36_freeze_protects_ledgers() -> None:
    assert (
        "FREEZE_MUTATED_RUNTIME_LEDGER"
        in
        freeze_text()
    )


def test_37_freeze_evidence_create_only() -> None:
    assert (
        'open(\n        "x"'
        in
        freeze_text()
    )


def test_38_runner_verifies_hashes() -> None:
    assert (
        "CAPTURE_ARTIFACT_CHANGED"
        in
        runner_text()
    )


def test_39_performance_false() -> None:
    assert (
        "PERFORMANCE_EVALUATED=false"
        in
        runner_text()
    )


def test_40_pnl_false() -> None:
    assert (
        "PNL_EVALUATED=false"
        in
        runner_text()
    )


def test_41_live_false() -> None:
    assert (
        "LIVE_AUTHORIZED=false"
        in
        runner_text()
    )


def test_42_execution_false() -> None:
    assert (
        "EXECUTION_AUTHORIZED=false"
        in
        runner_text()
    )