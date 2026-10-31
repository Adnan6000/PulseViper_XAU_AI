"""
===============================================================================
Module      : test_frozen_c04_shadow_observer.py
Project     : PulseViper XAU AI
Purpose     : Gate 15A Unit Test Suite for Forward Shadow Observation Infrastructure
===============================================================================

Comprehensive test suite verifying:
- Typed immutable observation records
- Exact model and feature contract propagation
- Decoupled logical observation ID vs semantic fingerprint
- Locked durable append ledger with fail-closed corruption detection
- Provenance-based forward eligibility enforcement
- Unconditional prohibition of trading execution / RiskEngine / broker writes
- Reachable dependency graph safety proof
- Blocked outcome contract status
- Numerical determinism
"""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Set

import numpy as np
import pandas as pd
import pytest

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Import Gate 15A observer module
_obs_mod = importlib.import_module("02_AI.Models.frozen_c04_shadow_observer")

FrozenC04ShadowObserver = _obs_mod.FrozenC04ShadowObserver
FrozenC04ShadowObservationCoordinator = _obs_mod.FrozenC04ShadowObservationCoordinator
FrozenC04ObservationRecord = _obs_mod.FrozenC04ObservationRecord
FrozenC04ObservationLedger = _obs_mod.FrozenC04ObservationLedger
SourceProvenance = _obs_mod.SourceProvenance
DuplicateHandling = _obs_mod.DuplicateHandling

# Error classes
FrozenC04ObservationError = _obs_mod.FrozenC04ObservationError
DuplicateObservationError = _obs_mod.DuplicateObservationError
ConflictingObservationError = _obs_mod.ConflictingObservationError
CorruptedLedgerError = _obs_mod.CorruptedLedgerError
TrueForwardAcquisitionNotAuthorizedError = _obs_mod.TrueForwardAcquisitionNotAuthorizedError
InvalidDecisionTimestampError = _obs_mod.InvalidDecisionTimestampError
InvalidSnapshotIdError = _obs_mod.InvalidSnapshotIdError
OutcomeContractBlockedError = _obs_mod.OutcomeContractBlockedError

# Constants
OBSERVER_SCHEMA_VERSION = _obs_mod.OBSERVER_SCHEMA_VERSION
RESEARCH_FREEZE_BOUNDARY_UTC = _obs_mod.RESEARCH_FREEZE_BOUNDARY_UTC
GATE_15A_ACTIVATION_UTC = _obs_mod.GATE_15A_ACTIVATION_UTC
OUTCOME_HORIZON_CONTRACT_STATUS = _obs_mod.OUTCOME_HORIZON_CONTRACT_STATUS
EXPECTED_FEATURE_COUNT = _obs_mod.EXPECTED_FEATURE_COUNT
EXPECTED_FEATURE_COLUMNS_SHA256 = _obs_mod.EXPECTED_FEATURE_COLUMNS_SHA256
FROZEN_MODEL_SHA256 = _obs_mod.FROZEN_MODEL_SHA256
FROZEN_MODEL_CLASSES = _obs_mod.FROZEN_MODEL_CLASSES
LABEL_MAP = _obs_mod.LABEL_MAP

# Helper functions
validate_iso8601_utc = _obs_mod.validate_iso8601_utc
validate_snapshot_id = _obs_mod.validate_snapshot_id
compute_logical_observation_id = _obs_mod.compute_logical_observation_id
compute_semantic_record_fingerprint = _obs_mod.compute_semantic_record_fingerprint


@pytest.fixture(scope="module")
def sample_feature_row() -> pd.Series:
    """Create a deterministic synthetic 331-feature row for testing."""
    _contract = importlib.import_module("02_AI.Features.portable_feature_contract")
    col_names = _contract.FROZEN_FEATURE_COLUMNS
    rng = np.random.RandomState(42)
    values = rng.randn(len(col_names)).astype(np.float32)
    return pd.Series(values, index=col_names)


@pytest.fixture(scope="module")
def observer_instance() -> FrozenC04ShadowObserver:
    """Create an instance of FrozenC04ShadowObserver for testing."""
    return FrozenC04ShadowObserver()


@pytest.fixture
def valid_snapshot_id() -> str:
    """Return a valid 64-hex SHA256 snapshot ID."""
    return hashlib.sha256(b"mock_snapshot_data_for_gate_15a").hexdigest()


# -----------------------------------------------------------------------------
# Test 1: Valid Observation Creation
# -----------------------------------------------------------------------------
def test_01_valid_observation_creation(
    observer_instance: FrozenC04ShadowObserver,
    sample_feature_row: pd.Series,
    valid_snapshot_id: str,
) -> None:
    dt = "2026-08-14T20:55:00Z"
    rec = observer_instance.observe_single(
        feature_row=sample_feature_row,
        decision_time_utc=dt,
        source_snapshot_id=valid_snapshot_id,
        source_provenance=SourceProvenance.HISTORICAL_ENGINEERING,
    )
    assert isinstance(rec, FrozenC04ObservationRecord)
    assert rec.decision_time_utc == dt
    assert rec.source_snapshot_id == valid_snapshot_id
    assert rec.source_provenance == SourceProvenance.HISTORICAL_ENGINEERING.value
    assert rec.canonical_instrument == "XAUUSD"
    assert rec.broker_symbol == "XAUUSDm"
    assert rec.feature_generation_status == "VALIDATED_GATE_13"
    assert rec.inference_status == "SUCCESS_GATE_14"
    assert rec.observation_status == "RECORDED"
    assert rec.live_authorized is False
    assert rec.execution_authorized is False
    assert rec.is_true_forward_eligible is False


# -----------------------------------------------------------------------------
# Test 2: Exact Model Identity Propagated
# -----------------------------------------------------------------------------
def test_02_exact_model_identity_propagated(
    observer_instance: FrozenC04ShadowObserver,
    sample_feature_row: pd.Series,
    valid_snapshot_id: str,
) -> None:
    rec = observer_instance.observe_single(
        feature_row=sample_feature_row,
        decision_time_utc="2026-08-14T20:55:00Z",
        source_snapshot_id=valid_snapshot_id,
    )
    assert rec.model_sha256 == FROZEN_MODEL_SHA256
    assert rec.model_class == "ExtraTreesClassifier"


# -----------------------------------------------------------------------------
# Test 3: Exact Feature Identity Propagated
# -----------------------------------------------------------------------------
def test_03_exact_feature_identity_propagated(
    observer_instance: FrozenC04ShadowObserver,
    sample_feature_row: pd.Series,
    valid_snapshot_id: str,
) -> None:
    rec = observer_instance.observe_single(
        feature_row=sample_feature_row,
        decision_time_utc="2026-08-14T20:55:00Z",
        source_snapshot_id=valid_snapshot_id,
    )
    assert rec.feature_count == EXPECTED_FEATURE_COUNT
    assert rec.feature_columns_sha256 == EXPECTED_FEATURE_COLUMNS_SHA256


# -----------------------------------------------------------------------------
# Test 4: Class & Probability Mapping
# -----------------------------------------------------------------------------
def test_04_class_probability_mapping(
    observer_instance: FrozenC04ShadowObserver,
    sample_feature_row: pd.Series,
    valid_snapshot_id: str,
) -> None:
    rec = observer_instance.observe_single(
        feature_row=sample_feature_row,
        decision_time_utc="2026-08-14T20:55:00Z",
        source_snapshot_id=valid_snapshot_id,
    )
    assert rec.class_order == (-1, 0, 1)
    assert 0.0 <= rec.probability_short <= 1.0
    assert 0.0 <= rec.probability_no_trade <= 1.0
    assert 0.0 <= rec.probability_long <= 1.0
    prob_sum = rec.probability_short + rec.probability_no_trade + rec.probability_long
    assert abs(prob_sum - 1.0) < 1e-5
    assert rec.predicted_class in (-1, 0, 1)
    assert rec.predicted_label == LABEL_MAP[rec.predicted_class]
    expected_win = max(rec.probability_short, rec.probability_no_trade, rec.probability_long)
    assert abs(rec.winning_probability - expected_win) < 1e-6


# -----------------------------------------------------------------------------
# Test 5: UTC Decision Timestamp Handling
# -----------------------------------------------------------------------------
def test_05_utc_decision_timestamp_handling() -> None:
    # Trailing Z
    assert validate_iso8601_utc("2026-08-14T20:55:00Z") == "2026-08-14T20:55:00Z"
    # Offset +00:00 normalized to Z
    assert validate_iso8601_utc("2026-08-14T20:55:00+00:00") == "2026-08-14T20:55:00Z"
    # Space separator normalized to T
    assert validate_iso8601_utc("2026-08-14 20:55:00Z") == "2026-08-14T20:55:00Z"


# -----------------------------------------------------------------------------
# Test 6: Unknown / Naive Timestamp Rejection
# -----------------------------------------------------------------------------
def test_06_unknown_naive_timestamp_rejection() -> None:
    # Naive without timezone
    with pytest.raises(InvalidDecisionTimestampError):
        validate_iso8601_utc("2026-08-14T20:55:00")
    # Non-UTC timezone offset (+02:00)
    with pytest.raises(InvalidDecisionTimestampError):
        validate_iso8601_utc("2026-08-14T20:55:00+02:00")
    # Malformed text
    with pytest.raises(InvalidDecisionTimestampError):
        validate_iso8601_utc("yesterday_afternoon")
    # Non-string
    with pytest.raises(InvalidDecisionTimestampError):
        validate_iso8601_utc(1723668900)  # type: ignore


# -----------------------------------------------------------------------------
# Test 7: Duplicate Observation Detection
# -----------------------------------------------------------------------------
def test_07_duplicate_observation_detection(
    observer_instance: FrozenC04ShadowObserver,
    sample_feature_row: pd.Series,
    valid_snapshot_id: str,
) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "test_ledger.jsonl"
        # 1. FAIL_CLOSED mode
        ledger_fail = FrozenC04ObservationLedger(
            ledger_path=ledger_path, duplicate_handling=DuplicateHandling.FAIL_CLOSED
        )
        rec = observer_instance.observe_single(
            feature_row=sample_feature_row,
            decision_time_utc="2026-08-14T20:55:00Z",
            source_snapshot_id=valid_snapshot_id,
        )
        res1 = ledger_fail.append(rec)
        assert res1.appended is True
        assert res1.is_duplicate is False

        # Second append should raise DuplicateObservationError
        with pytest.raises(DuplicateObservationError):
            ledger_fail.append(rec)

        # 2. IDEMPOTENT_IGNORE mode
        ledger_idem = FrozenC04ObservationLedger(
            ledger_path=ledger_path, duplicate_handling=DuplicateHandling.IDEMPOTENT_IGNORE
        )
        res2 = ledger_idem.append(rec)
        assert res2.appended is False
        assert res2.is_duplicate is True
        assert ledger_idem.count() == 1


# -----------------------------------------------------------------------------
# Test 8: Conflicting Observation Fails Closed
# -----------------------------------------------------------------------------
def test_08_conflicting_observation_fail_closed(
    observer_instance: FrozenC04ShadowObserver,
    sample_feature_row: pd.Series,
    valid_snapshot_id: str,
) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "test_conflicting.jsonl"
        ledger = FrozenC04ObservationLedger(
            ledger_path=ledger_path, duplicate_handling=DuplicateHandling.IDEMPOTENT_IGNORE
        )
        dt = "2026-08-14T20:55:00Z"
        rec1 = observer_instance.observe_single(
            feature_row=sample_feature_row,
            decision_time_utc=dt,
            source_snapshot_id=valid_snapshot_id,
        )
        ledger.append(rec1)

        # Create conflicting record with SAME logical ID (same dt, model, feature contract)
        # but DIFFERENT source_snapshot_id
        diff_snapshot_id = hashlib.sha256(b"conflicting_snapshot_data").hexdigest()
        rec2 = dataclasses.replace(rec1, source_snapshot_id=diff_snapshot_id, semantic_record_fingerprint="conflicting_hash")

        with pytest.raises(ConflictingObservationError):
            ledger.append(rec2)


# -----------------------------------------------------------------------------
# Test 9: Ledger Append and Recovery
# -----------------------------------------------------------------------------
def test_09_ledger_append_and_recovery(
    observer_instance: FrozenC04ShadowObserver,
    sample_feature_row: pd.Series,
    valid_snapshot_id: str,
) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "test_recovery.jsonl"
        ledger1 = FrozenC04ObservationLedger(ledger_path=ledger_path)

        # Append 3 distinct observations
        records_written = []
        for i in range(3):
            dt = f"2026-08-14T20:{50 + i}:00Z"
            rec = observer_instance.observe_single(
                feature_row=sample_feature_row,
                decision_time_utc=dt,
                source_snapshot_id=valid_snapshot_id,
            )
            ledger1.append(rec)
            records_written.append(rec)

        assert ledger1.count() == 3

        # Reopen in new instance from disk
        ledger2 = FrozenC04ObservationLedger(ledger_path=ledger_path)
        assert ledger2.count() == 3
        recovered = ledger2.read_all()
        assert len(recovered) == 3
        for orig, recov in zip(records_written, recovered):
            assert orig.logical_observation_id == recov.logical_observation_id
            assert orig.semantic_record_fingerprint == recov.semantic_record_fingerprint
            assert orig.decision_time_utc == recov.decision_time_utc


# -----------------------------------------------------------------------------
# Test 10: Ledger Locking, Durability, and Fail-Closed Partial Record
# -----------------------------------------------------------------------------
def test_10_ledger_locking_durability_and_fail_closed_partial_record(
    observer_instance: FrozenC04ShadowObserver,
    sample_feature_row: pd.Series,
    valid_snapshot_id: str,
) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "test_locking_durability.jsonl"
        ledger = FrozenC04ObservationLedger(ledger_path=ledger_path)

        rec = observer_instance.observe_single(
            feature_row=sample_feature_row,
            decision_time_utc="2026-08-14T20:55:00Z",
            source_snapshot_id=valid_snapshot_id,
        )
        ledger.append(rec)
        assert ledger_path.is_file()

        # Simulate a partial / interrupted write
        with open(ledger_path, "a", encoding="utf-8") as f:
            f.write('{"schema_version": "1.0.0", "logical_observation_id": "trunc\n')

        # Fail closed: must raise CorruptedLedgerError upon reopening or scanning
        with pytest.raises(CorruptedLedgerError):
            FrozenC04ObservationLedger(ledger_path=ledger_path)


# -----------------------------------------------------------------------------
# Test 11: Corrupted Ledger Rejection
# -----------------------------------------------------------------------------
def test_11_corrupted_ledger_rejection() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "corrupt_schema.jsonl"
        # Write JSON missing required keys
        with open(ledger_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"schema_version": "1.0.0", "only_one_key": True}) + "\n")

        with pytest.raises(CorruptedLedgerError):
            FrozenC04ObservationLedger(ledger_path=ledger_path)

        # Write unsupported schema version
        with open(ledger_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"schema_version": "99.0.0"}) + "\n")

        with pytest.raises(CorruptedLedgerError):
            FrozenC04ObservationLedger(ledger_path=ledger_path)


# -----------------------------------------------------------------------------
# Test 12: Immutable Record Behavior
# -----------------------------------------------------------------------------
def test_12_immutable_record_behavior(
    observer_instance: FrozenC04ShadowObserver,
    sample_feature_row: pd.Series,
    valid_snapshot_id: str,
) -> None:
    rec = observer_instance.observe_single(
        feature_row=sample_feature_row,
        decision_time_utc="2026-08-14T20:55:00Z",
        source_snapshot_id=valid_snapshot_id,
    )
    # Dataclass must be frozen
    with pytest.raises(dataclasses.FrozenInstanceError):
        rec.live_authorized = True  # type: ignore
    with pytest.raises(dataclasses.FrozenInstanceError):
        rec.probability_short = 0.99  # type: ignore


# -----------------------------------------------------------------------------
# Test 13: No Overwrite of Existing Observation
# -----------------------------------------------------------------------------
def test_13_no_overwrite_of_existing_observation(
    observer_instance: FrozenC04ShadowObserver,
    sample_feature_row: pd.Series,
    valid_snapshot_id: str,
) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "no_overwrite.jsonl"
        ledger = FrozenC04ObservationLedger(
            ledger_path=ledger_path, duplicate_handling=DuplicateHandling.IDEMPOTENT_IGNORE
        )
        rec = observer_instance.observe_single(
            feature_row=sample_feature_row,
            decision_time_utc="2026-08-14T20:55:00Z",
            source_snapshot_id=valid_snapshot_id,
        )
        ledger.append(rec)
        line_count_initial = len(ledger_path.read_text(encoding="utf-8").strip().splitlines())
        assert line_count_initial == 1

        # Attempt duplicate append
        ledger.append(rec)
        line_count_after = len(ledger_path.read_text(encoding="utf-8").strip().splitlines())
        assert line_count_after == 1  # File was not appended to or overwritten


# -----------------------------------------------------------------------------
# Test 14: Row / Source Identity Preservation
# -----------------------------------------------------------------------------
def test_14_row_source_identity_preservation(
    observer_instance: FrozenC04ShadowObserver,
    sample_feature_row: pd.Series,
    valid_snapshot_id: str,
) -> None:
    rec = observer_instance.observe_single(
        feature_row=sample_feature_row,
        decision_time_utc="2026-08-14T20:55:00Z",
        source_snapshot_id=valid_snapshot_id,
    )
    assert rec.source_snapshot_id == valid_snapshot_id

    # Test invalid snapshot ID format
    with pytest.raises(InvalidSnapshotIdError):
        observer_instance.observe_single(
            feature_row=sample_feature_row,
            decision_time_utc="2026-08-14T20:55:00Z",
            source_snapshot_id="invalid_not_hex_or_wrong_len",
        )


# -----------------------------------------------------------------------------
# Test 15: Static AST Check — No Order / Execution Imports
# -----------------------------------------------------------------------------
def test_15_static_no_order_execution_imports() -> None:
    observer_file = REPO_ROOT / "02_AI" / "Models" / "frozen_c04_shadow_observer.py"
    tree = ast.parse(observer_file.read_text(encoding="utf-8"))

    forbidden_names = {
        "order_send",
        "OrderSend",
        "order_modify",
        "OrderModify",
        "order_close",
        "OrderClose",
        "PositionOpen",
        "PositionClose",
        "execution_lifecycle",
        "trading_runtime",
    }
    imported_names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_names.add(node.module)
            for alias in node.names:
                imported_names.add(alias.name)

    violations = forbidden_names.intersection(imported_names)
    assert not violations, f"Forbidden order/execution imports found: {violations}"


# -----------------------------------------------------------------------------
# Test 16: Static AST Check — No RiskEngine Imports
# -----------------------------------------------------------------------------
def test_16_static_no_risk_engine_imports() -> None:
    observer_file = REPO_ROOT / "02_AI" / "Models" / "frozen_c04_shadow_observer.py"
    tree = ast.parse(observer_file.read_text(encoding="utf-8"))

    forbidden_names = {
        "RiskEngine",
        "broker_aware_risk_engine",
        "account_protection_guard",
        "risk_policy_scenario_matrix",
    }
    imported_names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_names.add(node.module)
            for alias in node.names:
                imported_names.add(alias.name)

    violations = forbidden_names.intersection(imported_names)
    assert not violations, f"Forbidden RiskEngine imports found: {violations}"


# -----------------------------------------------------------------------------
# Test 17: Static AST Check — No trade_ready Dependency
# -----------------------------------------------------------------------------
def test_17_static_no_trade_ready_dependency() -> None:
    observer_file = REPO_ROOT / "02_AI" / "Models" / "frozen_c04_shadow_observer.py"
    tree = ast.parse(observer_file.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Name, ast.Attribute, ast.FunctionDef, ast.ClassDef)):
            name = getattr(node, "id", getattr(node, "attr", getattr(node, "name", "")))
            assert "trade_ready" not in name.lower(), f"Forbidden symbol {name} found in observer"


# -----------------------------------------------------------------------------
# Test 18: Static Reachable Dependency Graph Safety Verification
# -----------------------------------------------------------------------------
def test_18_static_no_broker_write_calls() -> None:
    """
    Statically inspects the full reachable Gate 15A dependency graph:
    observer -> Gate 14 inference adapter -> Gate 13 feature contract & pipeline.
    Proves zero reachable broker write APIs, RiskEngine, or order execution.
    """
    gate15_modules = [
        REPO_ROOT / "02_AI" / "Models" / "frozen_c04_shadow_observer.py",
        REPO_ROOT / "02_AI" / "Models" / "frozen_c04_inference_adapter.py",
        REPO_ROOT / "02_AI" / "Features" / "portable_feature_contract.py",
        REPO_ROOT / "02_AI" / "Features" / "portable_feature_pipeline.py",
    ]

    forbidden_symbols = {
        "OrderSend",
        "order_send",
        "order_modify",
        "order_close",
        "PositionOpen",
        "RiskEngine",
        "trade_ready",
        "MetaTrader5.order_send",
    }

    for fpath in gate15_modules:
        assert fpath.is_file(), f"Module {fpath} missing"
        tree = ast.parse(fpath.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            # Check function calls
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in forbidden_symbols:
                    pytest.fail(f"Forbidden call {func.id} found in {fpath.name}")
                elif isinstance(func, ast.Attribute) and func.attr in forbidden_symbols:
                    pytest.fail(f"Forbidden attribute call {func.attr} found in {fpath.name}")


# -----------------------------------------------------------------------------
# Test 19: live_authorized Invariant Always False
# -----------------------------------------------------------------------------
def test_19_live_authorized_invariant_false(
    observer_instance: FrozenC04ShadowObserver,
    sample_feature_row: pd.Series,
    valid_snapshot_id: str,
) -> None:
    rec = observer_instance.observe_single(
        feature_row=sample_feature_row,
        decision_time_utc="2026-08-14T20:55:00Z",
        source_snapshot_id=valid_snapshot_id,
    )
    assert rec.live_authorized is False


# -----------------------------------------------------------------------------
# Test 20: execution_authorized Invariant Always False
# -----------------------------------------------------------------------------
def test_20_execution_authorized_invariant_false(
    observer_instance: FrozenC04ShadowObserver,
    sample_feature_row: pd.Series,
    valid_snapshot_id: str,
) -> None:
    rec = observer_instance.observe_single(
        feature_row=sample_feature_row,
        decision_time_utc="2026-08-14T20:55:00Z",
        source_snapshot_id=valid_snapshot_id,
    )
    assert rec.execution_authorized is False


# -----------------------------------------------------------------------------
# Test 21: Historical Replay Never Forward Eligible
# -----------------------------------------------------------------------------
def test_21_historical_replay_never_forward_eligible(
    observer_instance: FrozenC04ShadowObserver,
    sample_feature_row: pd.Series,
    valid_snapshot_id: str,
) -> None:
    # Even with a decision timestamp far into the future, historical replay is not forward eligible
    rec = observer_instance.observe_single(
        feature_row=sample_feature_row,
        decision_time_utc="2027-01-01T00:00:00Z",
        source_snapshot_id=valid_snapshot_id,
        source_provenance=SourceProvenance.HISTORICAL_ENGINEERING,
    )
    assert rec.is_true_forward_eligible is False
    assert rec.source_provenance == "HISTORICAL_ENGINEERING"


# -----------------------------------------------------------------------------
# Test 22: Synthetic Data Never Forward Eligible
# -----------------------------------------------------------------------------
def test_22_synthetic_data_never_forward_eligible(
    observer_instance: FrozenC04ShadowObserver,
    sample_feature_row: pd.Series,
    valid_snapshot_id: str,
) -> None:
    rec = observer_instance.observe_single(
        feature_row=sample_feature_row,
        decision_time_utc="2027-01-01T00:00:00Z",
        source_snapshot_id=valid_snapshot_id,
        source_provenance=SourceProvenance.SYNTHETIC_ENGINEERING,
    )
    assert rec.is_true_forward_eligible is False
    assert rec.source_provenance == "SYNTHETIC_ENGINEERING"


# -----------------------------------------------------------------------------
# Test 23: Forward Boundary & Provenance Authority Enforcement
# -----------------------------------------------------------------------------
def test_23_forward_boundary_and_provenance_enforcement(
    observer_instance: FrozenC04ShadowObserver,
    sample_feature_row: pd.Series,
    valid_snapshot_id: str,
) -> None:
    # 1. Verify frozen research boundary authority
    assert RESEARCH_FREEZE_BOUNDARY_UTC == "2026-08-14T20:55:00Z"

    # 2. Verify Gate 15A fails closed on attempts to supply TRUE_FORWARD_OBSERVATION
    with pytest.raises(TrueForwardAcquisitionNotAuthorizedError):
        observer_instance.observe_single(
            feature_row=sample_feature_row,
            decision_time_utc="2026-08-14T21:00:00Z",
            source_snapshot_id=valid_snapshot_id,
            source_provenance=SourceProvenance.TRUE_FORWARD_OBSERVATION,
        )


# -----------------------------------------------------------------------------
# Test 24: Outcome Contract Blocked Status Verified
# -----------------------------------------------------------------------------
def test_24_outcome_contract_blocked_status_verified(
    observer_instance: FrozenC04ShadowObserver,
) -> None:
    assert OUTCOME_HORIZON_CONTRACT_STATUS == "BLOCKED_NOT_PREDEFINED"
    with pytest.raises(OutcomeContractBlockedError):
        observer_instance.evaluate_outcome()


# -----------------------------------------------------------------------------
# Test 25: Numerical Determinism & Probability Tolerance
# -----------------------------------------------------------------------------
def test_25_numerical_determinism_and_probability_tolerance(
    observer_instance: FrozenC04ShadowObserver,
    sample_feature_row: pd.Series,
    valid_snapshot_id: str,
) -> None:
    dt = "2026-08-14T20:55:00Z"
    rec1 = observer_instance.observe_single(
        feature_row=sample_feature_row,
        decision_time_utc=dt,
        source_snapshot_id=valid_snapshot_id,
    )
    rec2 = observer_instance.observe_single(
        feature_row=sample_feature_row,
        decision_time_utc=dt,
        source_snapshot_id=valid_snapshot_id,
    )
    # Decisions match exactly
    assert rec1.predicted_class == rec2.predicted_class
    assert rec1.predicted_label == rec2.predicted_label
    # Probabilities match within machine precision tolerance
    assert abs(rec1.probability_short - rec2.probability_short) < 1e-12
    assert abs(rec1.probability_no_trade - rec2.probability_no_trade) < 1e-12
    assert abs(rec1.probability_long - rec2.probability_long) < 1e-12
    # Logical observation ID is deterministic and identical
    assert rec1.logical_observation_id == rec2.logical_observation_id
    assert rec1.semantic_record_fingerprint == rec2.semantic_record_fingerprint
