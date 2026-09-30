from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import Any


runner: Any = importlib.import_module(
    "04_Testing.production_portability."
    "run_xauusd_gate_15d_c_b2d_g2_genuine_outcome_maturation"
)


def test_01_gate_identity() -> None:

    assert (
        runner.GATE_ID
        ==
        "GATE_15D_C_B2D_G2_GENUINE_OUTCOME_MATURATION"
    )

    assert (
        runner.BASE_AUTHORITY_COMMIT
        ==
        "a1b692acd6b71b8fa32e59cb78f2da313388977f"
    )


def test_02_authorization_boundaries_remain_false() -> None:

    assert runner.PERFORMANCE_EVALUATION_AUTHORIZED is False
    assert runner.PNL_EVALUATION_AUTHORIZED is False
    assert runner.LIVE_AUTHORIZED is False
    assert runner.EXECUTION_AUTHORIZED is False


def test_03_only_read_only_mt5_runtime_boundary() -> None:

    source = Path(
        runner.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "order_send" not in source
    assert "order_check" not in source
    assert "positions_get" not in source
    assert "orders_get" not in source
    assert "history_deals_get" not in source

    assert (
        runner.RAW_MT5_CALLS
        ==
        (
            "initialize",
            "shutdown",
        )
    )


def test_04_maturation_requires_frozen_v2_authority() -> None:

    source = inspect.getsource(
        runner.verify_runtime_authorities
    )

    assert (
        "FROZEN_C04_FORWARD_OUTCOME_MATURER_V2"
        in source
    )

    assert (
        "FROZEN_C04_FORWARD_OUTCOME_LEDGER_V2"
        in source
    )

    assert (
        "EXPECTED_HORIZON_BARS"
        in source
    )


def test_05_runner_uses_prospective_observation_and_anchor() -> None:

    source = inspect.getsource(
        runner.run_gate
    )

    assert (
        "ObservationLedger"
        in source
    )

    assert (
        "AnchorLedger"
        in source
    )

    assert (
        "_maturer.mature_observation"
        in source
    )

    assert (
        "observation.to_dict()"
        in source
    )

    assert (
        "anchor=anchor"
        in source
    )


def test_06_append_is_explicitly_guarded() -> None:

    source = inspect.getsource(
        runner.run_gate
    )

    assert (
        "if append_outcome:"
        in source
    )

    assert (
        "IDEMPOTENT_IGNORE"
        in source
    )

    assert (
        "outcome_ledger.append"
        in source
    )


def test_07_default_cli_does_not_append() -> None:

    source = inspect.getsource(
        runner.parse_args
    )

    assert (
        '"--append-outcome"'
        in source
    )

    assert (
        "default=False"
        in source
    )


def test_08_observation_and_anchor_ledgers_are_immutable() -> None:

    source = inspect.getsource(
        runner.run_gate
    )

    assert (
        "OBSERVATION_LEDGER_CHANGED"
        in source
    )

    assert (
        "ANCHOR_LEDGER_CHANGED"
        in source
    )

    assert (
        ".append(\n                observation"
        not in source
    )

    assert (
        ".append(\n                anchor"
        not in source
    )


def test_09_dry_run_requires_outcome_ledger_unchanged() -> None:

    source = inspect.getsource(
        runner.run_gate
    )

    assert (
        "OUTCOME_LEDGER_CHANGED_DURING_DRY_RUN"
        in source
    )


def test_10_repository_authority_is_non_self_referential() -> None:

    source = inspect.getsource(
        runner.verify_repository_authority
    )

    assert (
        "merge-base"
        in source
    )

    assert (
        "--is-ancestor"
        in source
    )

    assert (
        "head == origin_main"
        in source
    )


def test_11_dynamic_broker_symbol_is_preserved() -> None:

    source = inspect.getsource(
        runner.run_gate
    )

    assert (
        "acquisition.resolve_broker_symbol"
        in source
    )

    assert (
        "observation.broker_symbol"
        in source
    )

    assert (
        "SUPPORTED_SYMBOLS"
        not in source
    )


def test_12_no_performance_or_pnl_computation() -> None:

    source = inspect.getsource(
        runner.run_gate
    ).lower()

    assert "accuracy_score" not in source
    assert "win_rate" not in source
    assert "drawdown" not in source
    assert "profit_loss" not in source
