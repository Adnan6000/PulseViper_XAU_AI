from __future__ import annotations

import dataclasses
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


pytestmark = pytest.mark.offline


ledger_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_ledger"
)

maturer_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_maturer"
)


def _outcome() -> Any:

    return maturer_mod.FrozenC04ForwardOutcome(
        logical_observation_id=(
            "a"
            *
            64
        ),

        decision_time_utc=(
            "2026-09-28T11:45:00Z"
        ),

        decision_bar_open_time_utc=(
            "2026-09-28T11:40:00Z"
        ),

        outcome_class=1,

        outcome_label="LONG",

        entry_close=4000.0,

        decision_atr14=10.0,

        horizon_bars=12,

        horizon_semantics=(
            "NEXT_12_COMPLETED_M5_ROWS_AFTER_DECISION_BAR"
        ),

        decision_bar_semantics=(
            "M5_BAR_OPEN_EQUALS_DECISION_TIME_MINUS_5_MINUTES"
        ),

        first_future_bar_time_utc=(
            "2026-09-28T11:45:00Z"
        ),

        last_future_bar_time_utc=(
            "2026-09-28T12:40:00Z"
        ),

        max_future_high=4015.0,

        min_future_low=3995.0,

        up_excursion_atr=1.5,

        down_excursion_atr=0.5,

        source_observation_fingerprint=(
            "b"
            *
            64
        ),
    )


def test_01_authorities_pass() -> None:

    assert (
        ledger_mod.verify_authorities()
        is True
    )


def test_02_versions_are_v1_1() -> None:

    assert (
        ledger_mod.OUTCOME_LEDGER_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_LEDGER_V1_1"
    )

    assert (
        ledger_mod.EXPECTED_MATURATION_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_MATURER_V1_1"
    )


def test_03_corrected_semantics_are_frozen() -> None:

    assert (
        ledger_mod.EXPECTED_DECISION_BAR_SEMANTICS
        ==
        "M5_BAR_OPEN_EQUALS_DECISION_TIME_MINUS_5_MINUTES"
    )

    assert (
        ledger_mod.EXPECTED_ENTRY_REFERENCE
        ==
        "DECISION_M5_COMPLETED_BAR_CLOSE"
    )

    assert (
        ledger_mod.EXPECTED_ATR_REFERENCE
        ==
        "DECISION_M5_COMPLETED_BAR_ATR14"
    )

    assert (
        ledger_mod.EXPECTED_HORIZON_SEMANTICS
        ==
        "NEXT_12_COMPLETED_M5_ROWS_AFTER_DECISION_BAR"
    )


def test_04_empty_ledger_count_zero(
    tmp_path: Path,
) -> None:

    path = (
        tmp_path
        /
        "outcomes.jsonl"
    )

    ledger = (
        ledger_mod.FrozenC04ForwardOutcomeLedger(
            path
        )
    )

    assert ledger.count() == 0

    assert (
        ledger.validate_integrity()
        is True
    )


def test_05_append_one_outcome(
    tmp_path: Path,
) -> None:

    path = (
        tmp_path
        /
        "outcomes.jsonl"
    )

    ledger = (
        ledger_mod.FrozenC04ForwardOutcomeLedger(
            path
        )
    )

    result = ledger.append(
        _outcome()
    )

    assert (
        result.appended
        is True
    )

    assert (
        result.is_duplicate
        is False
    )

    assert (
        ledger.count()
        ==
        1
    )

    assert (
        ledger.validate_integrity()
        is True
    )


def test_06_idempotent_duplicate(
    tmp_path: Path,
) -> None:

    path = (
        tmp_path
        /
        "outcomes.jsonl"
    )

    ledger = (
        ledger_mod.FrozenC04ForwardOutcomeLedger(
            path,
            duplicate_handling=(
                ledger_mod
                .OutcomeDuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )
    )

    first = ledger.append(
        _outcome()
    )

    second = ledger.append(
        _outcome()
    )

    assert (
        first.appended
        is True
    )

    assert (
        second.appended
        is False
    )

    assert (
        second.is_duplicate
        is True
    )

    assert (
        ledger.count()
        ==
        1
    )


def test_07_duplicate_fail_closed(
    tmp_path: Path,
) -> None:

    path = (
        tmp_path
        /
        "outcomes.jsonl"
    )

    ledger = (
        ledger_mod.FrozenC04ForwardOutcomeLedger(
            path
        )
    )

    ledger.append(
        _outcome()
    )

    with pytest.raises(
        ledger_mod.DuplicateOutcomeError
    ):

        ledger.append(
            _outcome()
        )


def test_08_conflicting_outcome_rejected(
    tmp_path: Path,
) -> None:

    path = (
        tmp_path
        /
        "outcomes.jsonl"
    )

    ledger = (
        ledger_mod.FrozenC04ForwardOutcomeLedger(
            path,
            duplicate_handling=(
                ledger_mod
                .OutcomeDuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )
    )

    original = (
        _outcome()
    )

    ledger.append(
        original
    )

    conflicting = (
        dataclasses.replace(
            original,
            up_excursion_atr=1.6,
        )
    )

    with pytest.raises(
        ledger_mod.ConflictingOutcomeError
    ):

        ledger.append(
            conflicting
        )


def test_09_read_all_roundtrip(
    tmp_path: Path,
) -> None:

    path = (
        tmp_path
        /
        "outcomes.jsonl"
    )

    ledger = (
        ledger_mod.FrozenC04ForwardOutcomeLedger(
            path
        )
    )

    expected = (
        _outcome()
    )

    ledger.append(
        expected
    )

    records = (
        ledger.read_all()
    )

    assert len(
        records
    ) == 1

    assert (
        records[
            0
        ].semantic_fingerprint()
        ==
        expected.semantic_fingerprint()
    )


def test_10_corrupted_json_fails_closed(
    tmp_path: Path,
) -> None:

    path = (
        tmp_path
        /
        "outcomes.jsonl"
    )

    path.write_text(
        "{not-json\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ledger_mod.CorruptedOutcomeLedgerError
    ):

        ledger_mod.FrozenC04ForwardOutcomeLedger(
            path
        )


def test_11_tampered_fingerprint_fails_closed(
    tmp_path: Path,
) -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "semantic_outcome_fingerprint"
    ] = (
        "c"
        *
        64
    )

    path = (
        tmp_path
        /
        "outcomes.jsonl"
    )

    path.write_text(
        json.dumps(
            document
        )
        +
        "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ledger_mod.CorruptedOutcomeLedgerError
    ):

        ledger_mod.FrozenC04ForwardOutcomeLedger(
            path
        )


def test_12_class_label_mismatch_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "outcome_label"
    ] = "SHORT"

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="OUTCOME_CLASS_LABEL_MISMATCH",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_13_horizon_mismatch_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "horizon_bars"
    ] = 13

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="OUTCOME_HORIZON_BARS_MISMATCH",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_14_old_horizon_semantics_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "horizon_semantics"
    ] = (
        "NEXT_12_COMPLETED_M5_ROWS_AFTER_DECISION_ROW"
    )

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="OUTCOME_HORIZON_SEMANTICS_MISMATCH",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_15_wrong_decision_bar_semantics_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "decision_bar_semantics"
    ] = "WRONG"

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="OUTCOME_DECISION_BAR_SEMANTICS_MISMATCH",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_16_wrong_decision_bar_time_mapping_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "decision_bar_open_time_utc"
    ] = (
        "2026-09-28T11:35:00Z"
    )

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="DECISION_BAR_TIME_MAPPING_MISMATCH",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_17_decision_bar_time_mapping_passes() -> None:

    validated = (
        ledger_mod.validate_outcome_document(
            _outcome().to_dict()
        )
    )

    assert (
        validated.decision_time_utc
        ==
        "2026-09-28T11:45:00Z"
    )

    assert (
        validated.decision_bar_open_time_utc
        ==
        "2026-09-28T11:40:00Z"
    )


def test_18_future_bars_follow_decision_bar() -> None:

    validated = (
        ledger_mod.validate_outcome_document(
            _outcome().to_dict()
        )
    )

    assert (
        validated.first_future_bar_time_utc
        ==
        "2026-09-28T11:45:00Z"
    )

    assert (
        validated.last_future_bar_time_utc
        ==
        "2026-09-28T12:40:00Z"
    )


def test_19_performance_authority_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "performance_evaluation_authorized"
    ] = True

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="PERFORMANCE_AUTHORIZATION_VIOLATION",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_20_live_authority_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "live_authorized"
    ] = True

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="LIVE_AUTHORIZATION_VIOLATION",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_21_execution_authority_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "execution_authorized"
    ] = True

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="EXECUTION_AUTHORIZATION_VIOLATION",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_22_old_maturation_version_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "maturation_version"
    ] = (
        "FROZEN_C04_FORWARD_OUTCOME_MATURER_V1"
    )

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="OUTCOME_MATURATION_VERSION_MISMATCH",
    ):

        ledger_mod.validate_outcome_document(
            document
        )