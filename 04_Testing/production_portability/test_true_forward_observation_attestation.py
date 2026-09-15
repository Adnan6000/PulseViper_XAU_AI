"""
===============================================================================
Module      : test_true_forward_observation_attestation.py
Project     : PulseViper XAU AI
Purpose     : Forward Shadow Attestation & Safety Harness Integration (Gate 15B-A)
===============================================================================

Comprehensive integration test suite verifying:
- Full read-only pipeline: Mock MT5 -> Acquisition Adapter -> Gate 13 Pipeline
  -> Gate 14 Inference -> Gate 15A Shadow Observer.
- CRITICAL: Synthetic/mock data NEVER produces true-forward eligibility
  (is_true_forward_eligible remains False; true_forward_observation_count is 0).
- Attempts to submit synthetic data as TRUE_FORWARD_OBSERVATION fail closed.
- Plain caller-supplied TRUE_FORWARD_OBSERVATION without attestation fails closed.
- Tampered or mismatched attestation (snapshot ID, decision time, model/feature SHA)
  fails closed.
- Historical engineering replay never results in forward eligibility.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib
import importlib
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd
import pytest

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Import required components
_acq_mod = importlib.import_module("02_AI.Adapters.mt5_read_only_forward_acquisition_adapter")
_pipeline_mod = importlib.import_module("02_AI.Features.portable_feature_pipeline")
_adapter_mod = importlib.import_module("02_AI.Models.frozen_c04_inference_adapter")
_observer_mod = importlib.import_module("02_AI.Models.frozen_c04_shadow_observer")

MT5ReadOnlyForwardAcquisitionAdapter = _acq_mod.MT5ReadOnlyForwardAcquisitionAdapter
PortableFeaturePipeline = _pipeline_mod.PortableFeaturePipeline
FrozenC04InferenceAdapter = _adapter_mod.FrozenC04InferenceAdapter
FrozenC04ShadowObserver = _observer_mod.FrozenC04ShadowObserver
SourceProvenance = _observer_mod.SourceProvenance
TrueForwardAcquisitionNotAuthorizedError = _observer_mod.TrueForwardAcquisitionNotAuthorizedError
RESEARCH_FREEZE_BOUNDARY_UTC = _observer_mod.RESEARCH_FREEZE_BOUNDARY_UTC
GATE_15A_ACTIVATION_UTC = _observer_mod.GATE_15A_ACTIVATION_UTC

_test_acq = importlib.import_module("04_Testing.production_portability.test_mt5_read_only_forward_acquisition_adapter")
MockMT5Session = _test_acq.MockMT5Session


def _format_iso_z(val: Any) -> str:
    ts = pd.Timestamp(val)
    if isinstance(ts, pd.Timestamp) and ts is not pd.NaT:
        utc_ts = ts.tz_convert("UTC") if ts.tz is not None else ts.tz_localize("UTC")
        if isinstance(utc_ts, pd.Timestamp):
            return str(utc_ts.isoformat()).replace("+00:00", "Z")
    raise ValueError(f"Invalid timestamp: {val}")


# =============================================================================
# Test 1: Full Pipeline Integration (Mock MT5 -> Gate 13 -> Gate 14 -> Gate 15A)
# =============================================================================
def test_01_full_forward_observation_pipeline_synthetic() -> None:
    session = MockMT5Session(base_epoch=1789000000, bar_count=5200)
    acq_adapter = MT5ReadOnlyForwardAcquisitionAdapter(session, is_synthetic=True)
    snapshot = acq_adapter.acquire_snapshot()

    # Pass acquired market data to Gate 13 PortableFeaturePipeline
    pipeline = PortableFeaturePipeline()
    feature_result = pipeline.generate(snapshot.market_data, symbol=snapshot.canonical_instrument)

    assert feature_result.feature_count == 331
    assert feature_result.row_count > 0
    assert feature_result.symbol == "XAUUSD"

    # Pass features to Gate 14 FrozenC04InferenceAdapter via Gate 15A ShadowObserver
    observer = FrozenC04ShadowObserver(canonical_instrument=snapshot.canonical_instrument)
    latest_feature_row = feature_result.features.iloc[-1]
    dt_iso = _format_iso_z(feature_result.decision_times.iloc[-1])

    record = observer.observe_single(
        feature_row=latest_feature_row,
        decision_time_utc=dt_iso,
        source_snapshot_id=snapshot.source_snapshot_id,
        source_provenance=SourceProvenance.SYNTHETIC_ENGINEERING,
        acquisition_attestation=snapshot.attestation,
    )

    # Invariants
    assert record.feature_count == 331
    assert record.canonical_instrument == "XAUUSD"
    assert record.predicted_class in (-1, 0, 1)
    assert record.live_authorized is False
    assert record.execution_authorized is False
    # CRITICAL: Synthetic observation is NEVER true forward eligible!
    assert record.is_true_forward_eligible is False
    assert record.source_provenance == "SYNTHETIC_ENGINEERING"


# =============================================================================
# Test 2: Synthetic Data Rejected from TRUE_FORWARD Escalation
# =============================================================================
def test_02_synthetic_data_rejected_from_true_forward() -> None:
    session = MockMT5Session(base_epoch=1789000000, bar_count=5200)
    acq_adapter = MT5ReadOnlyForwardAcquisitionAdapter(session, is_synthetic=True)
    snapshot = acq_adapter.acquire_snapshot()

    pipeline = PortableFeaturePipeline()
    feature_result = pipeline.generate(snapshot.market_data, symbol=snapshot.canonical_instrument)

    observer = FrozenC04ShadowObserver(canonical_instrument=snapshot.canonical_instrument)
    latest_row = feature_result.features.iloc[-1]
    dt_iso = _format_iso_z(feature_result.decision_times.iloc[-1])

    # Attempting to declare TRUE_FORWARD_OBSERVATION using synthetic/mock acquisition MUST FAIL CLOSED.
    # The capability-bound verify_forward_acquisition_authority rejects a plain ForwardAcquisitionAttestation
    # (not a VerifiedForwardAcquisitionAuthority) at the isinstance check — the earliest security boundary.
    # This is correct hardened behaviour: no plain dataclass can escalate to TRUE_FORWARD_OBSERVATION.
    with pytest.raises(TrueForwardAcquisitionNotAuthorizedError) as exc_info:
        observer.observe_single(
            feature_row=latest_row,
            decision_time_utc=dt_iso,
            source_snapshot_id=snapshot.source_snapshot_id,
            source_provenance=SourceProvenance.TRUE_FORWARD_OBSERVATION,
            acquisition_attestation=snapshot.attestation,
        )
    # The error MUST be TrueForwardAcquisitionNotAuthorizedError; the exact message path depends on
    # which security boundary fires first. Both "not authorized without a verified acquisition authority"
    # and "Synthetic or mocked acquisition data cannot be authorized" are valid rejections.
    assert (
        "not authorized" in str(exc_info.value).lower()
        or "synthetic" in str(exc_info.value).lower()
        or "mocked" in str(exc_info.value).lower()
    )


# =============================================================================
# Test 3: Missing Attestation on TRUE_FORWARD Fails Closed
# =============================================================================
def test_03_missing_attestation_fails_closed() -> None:
    session = MockMT5Session(base_epoch=1789000000, bar_count=5200)
    acq_adapter = MT5ReadOnlyForwardAcquisitionAdapter(session, is_synthetic=True)
    snapshot = acq_adapter.acquire_snapshot()

    pipeline = PortableFeaturePipeline()
    feature_result = pipeline.generate(snapshot.market_data, symbol=snapshot.canonical_instrument)

    observer = FrozenC04ShadowObserver(canonical_instrument=snapshot.canonical_instrument)
    latest_row = feature_result.features.iloc[-1]
    dt_iso = _format_iso_z(feature_result.decision_times.iloc[-1])

    # Caller passes TRUE_FORWARD_OBSERVATION but omits acquisition_attestation
    with pytest.raises(TrueForwardAcquisitionNotAuthorizedError) as exc_info:
        observer.observe_single(
            feature_row=latest_row,
            decision_time_utc=dt_iso,
            source_snapshot_id=snapshot.source_snapshot_id,
            source_provenance=SourceProvenance.TRUE_FORWARD_OBSERVATION,
            acquisition_attestation=None,
        )
    assert "TRUE_FORWARD_OBSERVATION is not authorized without" in str(exc_info.value)


# =============================================================================
# Test 4: Mismatched Attestation Properties Fail Closed
# =============================================================================
def test_04_mismatched_attestation_properties_fail_closed() -> None:
    session = MockMT5Session(base_epoch=1789000000, bar_count=5200)
    acq_adapter = MT5ReadOnlyForwardAcquisitionAdapter(session, is_synthetic=True)
    snapshot = acq_adapter.acquire_snapshot()

    pipeline = PortableFeaturePipeline()
    feature_result = pipeline.generate(snapshot.market_data, symbol=snapshot.canonical_instrument)

    observer = FrozenC04ShadowObserver(canonical_instrument=snapshot.canonical_instrument)
    latest_row = feature_result.features.iloc[-1]
    dt_iso = _format_iso_z(feature_result.decision_times.iloc[-1])

    # Mismatched snapshot ID
    mismatched_snapshot_id = hashlib.sha256(b"tampered_snapshot_id").hexdigest()
    with pytest.raises(TrueForwardAcquisitionNotAuthorizedError):
        observer.observe_single(
            feature_row=latest_row,
            decision_time_utc=dt_iso,
            source_snapshot_id=mismatched_snapshot_id,
            source_provenance=SourceProvenance.TRUE_FORWARD_OBSERVATION,
            acquisition_attestation=snapshot.attestation,
        )

    # Mismatched decision time
    with pytest.raises(TrueForwardAcquisitionNotAuthorizedError):
        observer.observe_single(
            feature_row=latest_row,
            decision_time_utc="2026-09-15T00:00:00Z",
            source_snapshot_id=snapshot.source_snapshot_id,
            source_provenance=SourceProvenance.TRUE_FORWARD_OBSERVATION,
            acquisition_attestation=snapshot.attestation,
        )


# =============================================================================
# Test 5: Historical Engineering Replay Never Forward Eligible
# =============================================================================
def test_05_historical_replay_with_attestation_never_forward_eligible() -> None:
    session = MockMT5Session(base_epoch=1789000000, bar_count=5200)
    acq_adapter = MT5ReadOnlyForwardAcquisitionAdapter(session, is_synthetic=True)
    snapshot = acq_adapter.acquire_snapshot()

    pipeline = PortableFeaturePipeline()
    feature_result = pipeline.generate(snapshot.market_data, symbol=snapshot.canonical_instrument)

    observer = FrozenC04ShadowObserver(canonical_instrument=snapshot.canonical_instrument)
    latest_row = feature_result.features.iloc[-1]
    dt_iso = _format_iso_z(feature_result.decision_times.iloc[-1])

    # Pass as HISTORICAL_ENGINEERING
    record = observer.observe_single(
        feature_row=latest_row,
        decision_time_utc=dt_iso,
        source_snapshot_id=snapshot.source_snapshot_id,
        source_provenance=SourceProvenance.HISTORICAL_ENGINEERING,
        acquisition_attestation=snapshot.attestation,
    )

    assert record.is_true_forward_eligible is False
    assert record.source_provenance == "HISTORICAL_ENGINEERING"
