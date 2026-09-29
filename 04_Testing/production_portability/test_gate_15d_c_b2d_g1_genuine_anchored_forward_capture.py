from __future__ import annotations

import ast
import importlib
import inspect
import textwrap
from pathlib import Path
from typing import Any

import pytest


pytestmark = pytest.mark.offline


runner: Any = importlib.import_module(
    "04_Testing.production_portability."
    "run_xauusd_gate_15d_c_b2d_g1_genuine_anchored_forward_capture"
)

coordinator_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_anchor_first_coordinator"
)

atomic_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_runtime_atomic_ledgers"
)


def _run_gate_tree() -> ast.FunctionDef:

    source = textwrap.dedent(
        inspect.getsource(
            runner.run_gate
        )
    )

    tree = ast.parse(
        source
    )

    functions = [
        node
        for node in tree.body
        if isinstance(
            node,
            ast.FunctionDef,
        )
    ]

    assert len(functions) == 1

    return functions[0]


def _attribute_calls(
    node: ast.AST,
) -> list[str]:

    calls: list[str] = []

    for candidate in ast.walk(
        node
    ):

        if not isinstance(
            candidate,
            ast.Call,
        ):
            continue

        target = candidate.func

        if isinstance(
            target,
            ast.Attribute,
        ):
            calls.append(
                target.attr
            )

        elif isinstance(
            target,
            ast.Name,
        ):
            calls.append(
                target.id
            )

    return calls


def test_01_runner_identity_is_frozen() -> None:

    assert (
        runner.GATE_ID
        ==
        "GATE_15D_C_B2D_G1_GENUINE_ANCHORED_FORWARD_CAPTURE"
    )

    assert (
        runner.SCHEMA_VERSION
        ==
        "1.0.0"
    )


def test_02_b2d_published_authority_commit_is_frozen() -> None:

    assert (
        runner.B2D_AUTHORITY_COMMIT
        ==
        "03c7a5e74b57b3f670521e29d0b55086027ca4da"
    )


def test_03_b2d_runtime_authorities_match() -> None:

    assert (
        atomic_mod.ATOMIC_LEDGER_AUTHORITY_VERSION
        ==
        "FROZEN_C04_FORWARD_RUNTIME_ATOMIC_LEDGERS_V1"
    )

    assert (
        coordinator_mod.COORDINATOR_VERSION
        ==
        "FROZEN_C04_FORWARD_ANCHOR_FIRST_COORDINATOR_V1"
    )

    assert (
        coordinator_mod.PERSISTENCE_ORDER
        ==
        "ANCHOR_FIRST_THEN_OBSERVATION"
    )


def test_04_authorization_boundaries_remain_closed() -> None:

    assert (
        runner.OUTCOME_MATURATION_AUTHORIZED
        is False
    )

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


def test_05_run_gate_uses_anchor_first_coordinator() -> None:

    tree = _run_gate_tree()

    calls = _attribute_calls(
        tree
    )

    assert (
        "persist"
        in calls
    )


def test_06_run_gate_does_not_directly_append_observation() -> None:

    source = inspect.getsource(
        runner.run_gate
    )

    assert (
        "observation_ledger.append("
        not in source
    )

    assert (
        "anchor_ledger.append("
        not in source
    )


def test_07_run_gate_has_no_outcome_maturation_call() -> None:

    tree = _run_gate_tree()

    calls = set(
        _attribute_calls(
            tree
        )
    )

    forbidden = {
        "mature_observation",
        "evaluate_outcome",
        "calculate_performance",
        "calculate_pnl",
        "score",
    }

    assert (
        calls.isdisjoint(
            forbidden
        )
    )


def test_08_run_gate_has_no_outcome_ledger_append() -> None:

    source = inspect.getsource(
        runner.run_gate
    )

    assert (
        "outcome_ledger.append("
        not in source
    )

    assert (
        "OUTCOME_LEDGER_PATH"
        not in source
    )


def test_09_only_raw_mt5_lifecycle_calls_are_initialize_shutdown() -> None:

    tree = _run_gate_tree()

    mt5_calls: list[str] = []

    for candidate in ast.walk(
        tree
    ):

        if not isinstance(
            candidate,
            ast.Call,
        ):
            continue

        target = candidate.func

        if not isinstance(
            target,
            ast.Attribute,
        ):
            continue

        owner = target.value

        if (
            isinstance(
                owner,
                ast.Name,
            )
            and
            owner.id
            ==
            "mt5"
        ):
            mt5_calls.append(
                target.attr
            )

    assert set(
        mt5_calls
    ) <= {
        "initialize",
        "shutdown",
    }

    assert (
        "initialize"
        in mt5_calls
    )

    assert (
        "shutdown"
        in mt5_calls
    )


def test_10_forbidden_trading_calls_absent_from_run_gate() -> None:

    calls = set(
        _attribute_calls(
            _run_gate_tree()
        )
    )

    forbidden = {
        "order_send",
        "order_check",
        "order_calc_margin",
        "order_calc_profit",
        "positions_get",
        "positions_total",
        "orders_get",
        "orders_total",
        "history_orders_get",
        "history_orders_total",
        "history_deals_get",
        "history_deals_total",
    }

    assert (
        calls.isdisjoint(
            forbidden
        )
    )


def test_11_runtime_ledgers_stay_under_shadow() -> None:

    for path in (
        runner.OBSERVATION_LEDGER_PATH,
        runner.ANCHOR_LEDGER_PATH,
        runner.OUTCOME_LEDGER_PATH,
    ):

        relative = Path(
            path
        ).resolve().relative_to(
            runner.REPO_ROOT
        )

        assert (
            relative.parts[
                0
            ]
            ==
            "01_Data"
        )

        assert (
            relative.parts[
                1
            ]
            ==
            "Shadow"
        )


def test_12_runner_requires_same_snapshot_hash_after_normalization() -> None:

    source = inspect.getsource(
        runner.run_gate
    )

    assert (
        "compute_canonical_snapshot_id"
        in source
    )

    assert (
        "TIMESTAMP_NORMALIZATION_CHANGED_SOURCE_SNAPSHOT_ID"
        in source
    )


def test_13_runner_requires_prospective_eligibility_before_persistence() -> None:

    source = inspect.getsource(
        runner.run_gate
    )

    eligibility_position = source.index(
        "assess_observation"
    )

    persistence_position = source.index(
        "coordinator.persist"
    )

    assert (
        eligibility_position
        <
        persistence_position
    )


def test_14_runner_requires_gate13_before_gate14_observation() -> None:

    source = inspect.getsource(
        runner.run_gate
    )

    feature_position = source.index(
        "PortableFeaturePipeline"
    )

    observer_position = source.index(
        "observer.observe_single"
    )

    assert (
        feature_position
        <
        observer_position
    )


def test_15_outcome_ledger_is_required_unchanged() -> None:

    source = inspect.getsource(
        runner.run_gate
    )

    assert (
        "OUTCOME_LEDGER_CHANGED_DURING_G1"
        in source
    )

    assert (
        'runtime_after[\n                "outcome"\n            ]'
        in source
        or
        'runtime_after["outcome"]'
        in source
    )


def test_16_orphan_anchor_policy_matches_b2d() -> None:

    assert (
        coordinator_mod.ORPHAN_ANCHOR_POLICY
        ==
        "PRESERVE_IMMUTABLE_ANCHOR_IF_OBSERVATION_APPEND_FAILS"
    )


def test_17_b2d_authority_verification_is_offline_safe() -> None:

    result = (
        runner.verify_b2d_authority()
    )

    assert (
        result[
            "status"
        ]
        ==
        "PASS"
    )

    assert (
        result[
            "authority_commit"
        ]
        ==
        runner.B2D_AUTHORITY_COMMIT
    )


def test_18_runtime_authority_verification_is_offline_safe() -> None:

    result = (
        runner.verify_runtime_authorities()
    )

    assert (
        result[
            "status"
        ]
        ==
        "PASS"
    )

    assert (
        result[
            "outcome_maturation_authorized"
        ]
        is False
    )

    assert (
        result[
            "performance_evaluation_authorized"
        ]
        is False
    )

    assert (
        result[
            "live_authorized"
        ]
        is False
    )

    assert (
        result[
            "execution_authorized"
        ]
        is False
    )