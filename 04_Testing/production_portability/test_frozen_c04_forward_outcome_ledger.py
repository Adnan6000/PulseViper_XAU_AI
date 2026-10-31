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

anchor_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_anchor"
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

        outcome_label=(
            "LONG"
        ),

        entry_close=(
            4000.0
        ),

        decision_atr14=(
            10.0
        ),

        horizon_bars=(
            12
        ),

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

        max_future_high=(
            4015.0
        ),

        min_future_low=(
            3995.0
        ),

        up_excursion_atr=(
            1.5
        ),

        down_excursion_atr=(
            0.5
        ),

        source_observation_fingerprint=(
            "b"
            *
            64
        ),

        source_anchor_fingerprint=(
            "c"
            *
            64
        ),

        source_anchor_version=(
            anchor_mod.ANCHOR_VERSION
        ),
    )


def test_01_authorities_pass() -> None:

    assert (
        ledger_mod.verify_authorities()
        is True
    )


def test_02_versions_are_v2() -> None:

    assert (
        ledger_mod.OUTCOME_LEDGER_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_LEDGER_V2"
    )

    assert (
        ledger_mod.SUPERSEDES_OUTCOME_LEDGER_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_LEDGER_V1_1"
    )

    assert (
        ledger_mod.EXPECTED_MATURATION_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_MATURER_V2"
    )


def test_03_anchor_requirements_are_frozen() -> None:

    assert (
        ledger_mod.EXPECTED_ANCHOR_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_ANCHOR_V1"
    )

    assert (
        ledger_mod.EXPECTED_ENTRY_REFERENCE
        ==
        "PROSPECTIVE_ANCHOR_DECISION_M5_CLOSE"
    )

    assert (
        ledger_mod.EXPECTED_ATR_REFERENCE
        ==
        "PROSPECTIVE_ANCHOR_DECISION_M5_ATR14"
    )

    assert (
        ledger_mod.EXPECTED_ANCHOR_REQUIREMENT
        ==
        "VALIDATED_PROSPECTIVE_ANCHOR_REQUIRED"
    )

    assert (
        ledger_mod.EXPECTED_REFERENCE_RECONSTRUCTION_POLICY
        ==
        "POST_HOC_ENTRY_AND_ATR_RECONSTRUCTION_FORBIDDEN"
    )


def test_04_empty_ledger_count_zero(
    tmp_path: Path,
) -> None:

    ledger = (
        ledger_mod.FrozenC04ForwardOutcomeLedger(
            tmp_path
            /
            "outcomes.jsonl"
        )
    )

    assert (
        ledger.count()
        ==
        0
    )

    assert (
        ledger.validate_integrity()
        is True
    )


def test_05_append_one_outcome(
    tmp_path: Path,
) -> None:

    ledger = (
        ledger_mod.FrozenC04ForwardOutcomeLedger(
            tmp_path
            /
            "outcomes.jsonl"
        )
    )

    result = (
        ledger.append(
            _outcome()
        )
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


def test_06_idempotent_duplicate(
    tmp_path: Path,
) -> None:

    ledger = (
        ledger_mod.FrozenC04ForwardOutcomeLedger(
            tmp_path
            /
            "outcomes.jsonl",

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

    ledger = (
        ledger_mod.FrozenC04ForwardOutcomeLedger(
            tmp_path
            /
            "outcomes.jsonl"
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

    ledger = (
        ledger_mod.FrozenC04ForwardOutcomeLedger(
            tmp_path
            /
            "outcomes.jsonl",

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

    conflicting = dataclasses.replace(
        original,
        up_excursion_atr=(
            1.6
        ),
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

    ledger = (
        ledger_mod.FrozenC04ForwardOutcomeLedger(
            tmp_path
            /
            "outcomes.jsonl"
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

    assert (
        len(
            records
        )
        ==
        1
    )

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
        "d"
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


def test_12_source_anchor_fingerprint_required() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document.pop(
        "source_anchor_fingerprint"
    )

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="SOURCE_ANCHOR_FINGERPRINT",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_13_source_anchor_version_required() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document.pop(
        "source_anchor_version"
    )

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="SOURCE_ANCHOR_VERSION",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_14_wrong_anchor_version_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "source_anchor_version"
    ] = (
        "WRONG_ANCHOR_VERSION"
    )

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="SOURCE_ANCHOR_VERSION_MISMATCH",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_15_wrong_entry_reference_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "entry_reference"
    ] = (
        "DECISION_M5_COMPLETED_BAR_CLOSE"
    )

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="OUTCOME_ENTRY_REFERENCE_MISMATCH",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_16_wrong_atr_reference_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "atr_reference"
    ] = (
        "DECISION_M5_COMPLETED_BAR_ATR14"
    )

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="OUTCOME_ATR_REFERENCE_MISMATCH",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_17_missing_anchor_requirement_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "anchor_requirement"
    ] = (
        "NONE"
    )

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="OUTCOME_ANCHOR_REQUIREMENT_MISMATCH",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_18_reconstruction_policy_violation_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "reference_reconstruction_policy"
    ] = (
        "POST_HOC_ALLOWED"
    )

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="OUTCOME_REFERENCE_RECONSTRUCTION_POLICY_MISMATCH",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_19_class_label_mismatch_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "outcome_label"
    ] = (
        "SHORT"
    )

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="OUTCOME_CLASS_LABEL_MISMATCH",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_20_horizon_mismatch_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "horizon_bars"
    ] = (
        13
    )

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="OUTCOME_HORIZON_BARS_MISMATCH",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_21_wrong_horizon_semantics_rejected() -> None:

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


def test_22_wrong_decision_bar_semantics_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "decision_bar_semantics"
    ] = (
        "WRONG"
    )

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="OUTCOME_DECISION_BAR_SEMANTICS_MISMATCH",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_23_wrong_decision_bar_time_mapping_rejected() -> None:

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


def test_24_old_maturer_v1_1_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "maturation_version"
    ] = (
        "FROZEN_C04_FORWARD_OUTCOME_MATURER_V1_1"
    )

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="OUTCOME_MATURATION_VERSION_MISMATCH",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_25_performance_authority_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "performance_evaluation_authorized"
    ] = (
        True
    )

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="PERFORMANCE_AUTHORIZATION_VIOLATION",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_26_live_authority_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "live_authorized"
    ] = (
        True
    )

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="LIVE_AUTHORIZATION_VIOLATION",
    ):

        ledger_mod.validate_outcome_document(
            document
        )


def test_27_execution_authority_rejected() -> None:

    document = (
        _outcome()
        .to_dict()
    )

    document[
        "execution_authorized"
    ] = (
        True
    )

    with pytest.raises(
        ledger_mod.InvalidOutcomeRecordError,
        match="EXECUTION_AUTHORIZATION_VIOLATION",
    ):

        ledger_mod.validate_outcome_document(
            document
        )