from __future__ import annotations

import ast
import dataclasses
import importlib
import inspect
import json
import textwrap
from pathlib import Path
from typing import Any

import pytest


pytestmark = pytest.mark.offline


atomic_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_runtime_atomic_ledgers"
)

anchor_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_anchor"
)

observer_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_shadow_observer"
)


def _function_tree(
    cls: type[Any],
    method_name: str,
) -> ast.FunctionDef:

    method = getattr(
        cls,
        method_name,
    )

    source = textwrap.dedent(
        inspect.getsource(
            method
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

    assert (
        len(
            functions
        )
        ==
        1
    )

    return functions[
        0
    ]


def _lock_with_node(
    function: ast.FunctionDef,
) -> ast.With:

    for node in ast.walk(
        function
    ):

        if not isinstance(
            node,
            ast.With,
        ):

            continue

        for item in node.items:

            expression = (
                item.context_expr
            )

            if not isinstance(
                expression,
                ast.Call,
            ):

                continue

            target = (
                expression.func
            )

            if (
                isinstance(
                    target,
                    ast.Name,
                )
                and
                target.id
                ==
                "_file_lock"
            ):

                return node

    raise AssertionError(
        "APPEND_FILE_LOCK_CONTEXT_NOT_FOUND"
    )


def _membership_checks(
    node: ast.AST,
    variable_name: str,
) -> list[ast.Compare]:

    matches: list[
        ast.Compare
    ] = []

    for candidate in ast.walk(
        node
    ):

        if not isinstance(
            candidate,
            ast.Compare,
        ):

            continue

        if (
            len(
                candidate.ops
            )
            !=
            1
        ):

            continue

        if not isinstance(
            candidate.ops[
                0
            ],
            ast.In,
        ):

            continue

        if (
            len(
                candidate.comparators
            )
            !=
            1
        ):

            continue

        comparator = (
            candidate.comparators[
                0
            ]
        )

        if not isinstance(
            comparator,
            ast.Name,
        ):

            continue

        if (
            comparator.id
            !=
            variable_name
        ):

            continue

        matches.append(
            candidate
        )

    return matches


def _calls_self_method(
    node: ast.AST,
    method_name: str,
) -> bool:

    for candidate in ast.walk(
        node
    ):

        if not isinstance(
            candidate,
            ast.Call,
        ):

            continue

        target = (
            candidate.func
        )

        if not isinstance(
            target,
            ast.Attribute,
        ):

            continue

        if (
            not isinstance(
                target.value,
                ast.Name,
            )
        ):

            continue

        if (
            target.value.id
            !=
            "self"
        ):

            continue

        if (
            target.attr
            ==
            method_name
        ):

            return True

    return False


def _assert_atomic_shape(
    cls: type[Any],
) -> None:

    function = (
        _function_tree(
            cls,
            "append",
        )
    )

    lock_node = (
        _lock_with_node(
            function
        )
    )

    checks = (
        _membership_checks(
            lock_node,
            "disk_index",
        )
    )

    assert (
        len(
            checks
        )
        >=
        1
    ), (
        "DUPLICATE_CONFLICT_DECISION_MUST_USE_LOCKED_DISK_INDEX"
    )

    assert (
        _calls_self_method(
            lock_node,
            "_scan_locked_handle",
        )
        is True
    ), (
        "CURRENT_ON_DISK_LEDGER_MUST_BE_SCANNED_INSIDE_LOCK"
    )


def _anchor() -> Any:

    return (
        anchor_mod
        .FrozenC04ForwardOutcomeAnchor(
            logical_observation_id=(
                "a"
                *
                64
            ),

            semantic_observation_fingerprint=(
                "b"
                *
                64
            ),

            source_snapshot_id=(
                "c"
                *
                64
            ),

            canonical_instrument=(
                "XAUUSD"
            ),

            decision_time_utc=(
                "2026-09-29T08:05:00Z"
            ),

            decision_bar_open_time_utc=(
                "2026-09-29T08:00:00Z"
            ),

            decision_m5_close=(
                3800.0
            ),

            decision_m5_atr14=(
                10.0
            ),

            feature_columns_sha256=(
                anchor_mod
                .EXPECTED_FEATURE_COLUMNS_SHA256
            ),

            model_sha256=(
                anchor_mod
                .EXPECTED_MODEL_SHA256
            ),

            acquisition_authority=(
                anchor_mod
                .EXPECTED_ACQUISITION_AUTHORITY
            ),

            source_provenance=(
                anchor_mod
                .EXPECTED_SOURCE_PROVENANCE
            ),
        )
    )


def _observation() -> Any:

    logical_id = (
        "d"
        *
        64
    )

    snapshot_id = (
        "e"
        *
        64
    )

    probability_short = (
        0.1
    )

    probability_no_trade = (
        0.2
    )

    probability_long = (
        0.7
    )

    predicted_class = (
        1
    )

    winning_probability = (
        0.7
    )

    semantic_fp = (
        observer_mod
        .compute_semantic_record_fingerprint(
            logical_observation_id=(
                logical_id
            ),

            source_snapshot_id=(
                snapshot_id
            ),

            source_provenance=(
                "TRUE_FORWARD_OBSERVATION"
            ),

            probability_short=(
                probability_short
            ),

            probability_no_trade=(
                probability_no_trade
            ),

            probability_long=(
                probability_long
            ),

            predicted_class=(
                predicted_class
            ),

            winning_probability=(
                winning_probability
            ),

            feature_count=(
                observer_mod
                .EXPECTED_FEATURE_COUNT
            ),

            feature_columns_sha256=(
                observer_mod
                .EXPECTED_FEATURE_COLUMNS_SHA256
            ),

            model_sha256=(
                observer_mod
                .FROZEN_MODEL_SHA256
            ),
        )
    )

    return (
        observer_mod
        .FrozenC04ObservationRecord(
            logical_observation_id=(
                logical_id
            ),

            semantic_record_fingerprint=(
                semantic_fp
            ),

            observed_at_utc=(
                "2026-09-29T08:05:30Z"
            ),

            decision_time_utc=(
                "2026-09-29T08:05:00Z"
            ),

            canonical_instrument=(
                "XAUUSD"
            ),

            broker_symbol=(
                "XAUUSDm"
            ),

            feature_count=(
                observer_mod
                .EXPECTED_FEATURE_COUNT
            ),

            feature_columns_sha256=(
                observer_mod
                .EXPECTED_FEATURE_COLUMNS_SHA256
            ),

            model_sha256=(
                observer_mod
                .FROZEN_MODEL_SHA256
            ),

            model_class=(
                observer_mod
                .EXPECTED_MODEL_CLASS_NAME
            ),

            class_order=(
                observer_mod
                .FROZEN_MODEL_CLASSES
            ),

            probability_short=(
                probability_short
            ),

            probability_no_trade=(
                probability_no_trade
            ),

            probability_long=(
                probability_long
            ),

            predicted_class=(
                predicted_class
            ),

            predicted_label=(
                "LONG"
            ),

            winning_probability=(
                winning_probability
            ),

            source_snapshot_id=(
                snapshot_id
            ),

            source_provenance=(
                "TRUE_FORWARD_OBSERVATION"
            ),

            feature_generation_status=(
                "PASS"
            ),

            inference_status=(
                "PASS"
            ),

            observation_status=(
                "PASS"
            ),

            is_true_forward_eligible=True,

            live_authorized=False,

            execution_authorized=False,
        )
    )


def test_01_atomic_authority_passes() -> None:

    assert (
        atomic_mod.verify_authorities()
        is True
    )


def test_02_anchor_append_is_lock_atomic() -> None:

    _assert_atomic_shape(
        atomic_mod
        .AtomicFrozenC04ForwardOutcomeAnchorLedger
    )


def test_03_observation_append_is_lock_atomic() -> None:

    _assert_atomic_shape(
        atomic_mod
        .AtomicFrozenC04ObservationLedger
    )


def test_04_anchor_idempotent_retry(
    tmp_path: Path,
) -> None:

    path = (
        tmp_path
        /
        "anchors.jsonl"
    )

    first_ledger = (
        atomic_mod
        .AtomicFrozenC04ForwardOutcomeAnchorLedger(
            path,
            duplicate_handling=(
                anchor_mod
                .AnchorDuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )
    )

    second_ledger = (
        atomic_mod
        .AtomicFrozenC04ForwardOutcomeAnchorLedger(
            path,
            duplicate_handling=(
                anchor_mod
                .AnchorDuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )
    )

    first = (
        first_ledger.append(
            _anchor()
        )
    )

    second = (
        second_ledger.append(
            _anchor()
        )
    )

    assert first.appended is True

    assert second.appended is False

    assert second.is_duplicate is True

    assert (
        second_ledger.count()
        ==
        1
    )


def test_05_anchor_conflict_detected_from_fresh_disk_state(
    tmp_path: Path,
) -> None:

    path = (
        tmp_path
        /
        "anchors.jsonl"
    )

    first_ledger = (
        atomic_mod
        .AtomicFrozenC04ForwardOutcomeAnchorLedger(
            path,
            duplicate_handling=(
                anchor_mod
                .AnchorDuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )
    )

    stale_ledger = (
        atomic_mod
        .AtomicFrozenC04ForwardOutcomeAnchorLedger(
            path,
            duplicate_handling=(
                anchor_mod
                .AnchorDuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )
    )

    original = (
        _anchor()
    )

    first_ledger.append(
        original
    )

    conflicting = dataclasses.replace(
        original,
        decision_m5_close=(
            3801.0
        ),
    )

    with pytest.raises(
        anchor_mod.ConflictingAnchorError
    ):

        stale_ledger.append(
            conflicting
        )


def test_06_observation_idempotent_retry(
    tmp_path: Path,
) -> None:

    path = (
        tmp_path
        /
        "observations.jsonl"
    )

    first_ledger = (
        atomic_mod
        .AtomicFrozenC04ObservationLedger(
            path,
            duplicate_handling=(
                observer_mod
                .DuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )
    )

    second_ledger = (
        atomic_mod
        .AtomicFrozenC04ObservationLedger(
            path,
            duplicate_handling=(
                observer_mod
                .DuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )
    )

    first = (
        first_ledger.append(
            _observation()
        )
    )

    second = (
        second_ledger.append(
            _observation()
        )
    )

    assert first.appended is True

    assert second.appended is False

    assert second.is_duplicate is True

    assert (
        second_ledger.count()
        ==
        1
    )


def test_07_observation_conflict_detected_from_fresh_disk_state(
    tmp_path: Path,
) -> None:

    path = (
        tmp_path
        /
        "observations.jsonl"
    )

    first_ledger = (
        atomic_mod
        .AtomicFrozenC04ObservationLedger(
            path,
            duplicate_handling=(
                observer_mod
                .DuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )
    )

    stale_ledger = (
        atomic_mod
        .AtomicFrozenC04ObservationLedger(
            path,
            duplicate_handling=(
                observer_mod
                .DuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )
    )

    original = (
        _observation()
    )

    first_ledger.append(
        original
    )

    conflicting = dataclasses.replace(
        original,
        semantic_record_fingerprint=(
            "f"
            *
            64
        ),
    )

    with pytest.raises(
        observer_mod.ConflictingObservationError
    ):

        stale_ledger.append(
            conflicting
        )


def test_08_anchor_disk_record_is_single_line(
    tmp_path: Path,
) -> None:

    path = (
        tmp_path
        /
        "anchors.jsonl"
    )

    ledger = (
        atomic_mod
        .AtomicFrozenC04ForwardOutcomeAnchorLedger(
            path
        )
    )

    ledger.append(
        _anchor()
    )

    lines = [
        line
        for line in path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    assert (
        len(
            lines
        )
        ==
        1
    )

    parsed = json.loads(
        lines[
            0
        ]
    )

    assert (
        parsed[
            "logical_observation_id"
        ]
        ==
        (
            "a"
            *
            64
        )
    )


def test_09_observation_disk_record_is_single_line(
    tmp_path: Path,
) -> None:

    path = (
        tmp_path
        /
        "observations.jsonl"
    )

    ledger = (
        atomic_mod
        .AtomicFrozenC04ObservationLedger(
            path
        )
    )

    ledger.append(
        _observation()
    )

    lines = [
        line
        for line in path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    assert (
        len(
            lines
        )
        ==
        1
    )


def test_10_authorization_boundaries_remain_closed() -> None:

    assert (
        atomic_mod.PERFORMANCE_EVALUATION_AUTHORIZED
        is False
    )

    assert (
        atomic_mod.PNL_EVALUATION_AUTHORIZED
        is False
    )

    assert (
        atomic_mod.LIVE_AUTHORIZED
        is False
    )

    assert (
        atomic_mod.EXECUTION_AUTHORIZED
        is False
    )


def test_11_lock_transaction_policy_is_frozen() -> None:

    assert (
        atomic_mod.LOCK_TRANSACTION_POLICY
        ==
        "LOCK_THEN_REBUILD_DISK_INDEX_THEN_DECIDE_THEN_APPEND_FSYNC"
    )


def test_12_append_only_is_frozen() -> None:

    assert (
        atomic_mod.APPEND_ONLY
        is True
    )