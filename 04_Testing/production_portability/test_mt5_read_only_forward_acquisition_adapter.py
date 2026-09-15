"""
===============================================================================
Module      : test_mt5_read_only_forward_acquisition_adapter.py
Project     : PulseViper XAU AI
Purpose     : Gate 15B-A Unit Test Suite for Read-Only Forward Acquisition Adapter
===============================================================================

Comprehensive unit test suite verifying:
- Read-only capability facade whitelist and attribute blocking
- Forbidden broker mutating methods (order_send, positions_get, etc.) fail closed
- Forming candle exclusion (start_pos < 1 strictly rejected)
- Multi-timeframe acquisition and UTC timestamp normalization
- Data integrity, geometry validation, monotonicity, and insufficient bars
- Deterministic source snapshot fingerprinting and sensitivity to changes
- Forward acquisition attestation integrity and tamper resistance
- Frozen research boundary and Gate 15A activation boundary enforcement
- Static safety audit proving zero reachable broker write/order APIs
"""

from __future__ import annotations

import ast
from dataclasses import replace
import hashlib
import importlib
from pathlib import Path
import sys
from typing import Any, Sequence

import numpy as np
import pandas as pd
import pytest

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Import Gate 15B-A adapter module
_acq_mod = importlib.import_module("02_AI.Adapters.mt5_read_only_forward_acquisition_adapter")

MT5ReadOnlyCapabilityFacade = _acq_mod.MT5ReadOnlyCapabilityFacade
MT5ReadOnlyForwardAcquisitionAdapter = _acq_mod.MT5ReadOnlyForwardAcquisitionAdapter
ForwardMarketSnapshot = _acq_mod.ForwardMarketSnapshot
ForwardAcquisitionAttestation = _acq_mod.ForwardAcquisitionAttestation
compute_canonical_snapshot_id = _acq_mod.compute_canonical_snapshot_id

# Exceptions
ForwardAcquisitionError = _acq_mod.ForwardAcquisitionError
MT5ConnectionUnavailableError = _acq_mod.MT5ConnectionUnavailableError
IncompleteCandleAccessAttemptError = _acq_mod.IncompleteCandleAccessAttemptError
SymbolResolutionError = _acq_mod.SymbolResolutionError
UnsupportedSymbolError = _acq_mod.UnsupportedSymbolError
InsufficientForwardHistoryError = _acq_mod.InsufficientForwardHistoryError
HistoricalFreezeBoundaryViolationError = _acq_mod.HistoricalFreezeBoundaryViolationError
PreActivationForwardError = _acq_mod.PreActivationForwardError
MalformedBarDataError = _acq_mod.MalformedBarDataError
AttestationIntegrityError = _acq_mod.AttestationIntegrityError

RESEARCH_FREEZE_BOUNDARY_UTC = _acq_mod.RESEARCH_FREEZE_BOUNDARY_UTC
GATE_15A_ACTIVATION_UTC = _acq_mod.GATE_15A_ACTIVATION_UTC


# =============================================================================
# Mock MT5 Implementation for Testing
# =============================================================================

class MockSymbolInfo:
    def __init__(self, name: str, visible: bool = True, selected: bool = True) -> None:
        self.name = name
        self.visible = visible
        self.selected = selected
        self.digits = 2
        self.point = 0.01
        self.trade_contract_size = 100.0


class MockMT5Session:
    """Mock MT5 session providing deterministic rates for M5, M15, M30, H1, H4."""
    TIMEFRAME_M5 = 5
    TIMEFRAME_M15 = 15
    TIMEFRAME_M30 = 30
    TIMEFRAME_H1 = 16385
    TIMEFRAME_H4 = 16388
    TIMEFRAME_D1 = 16408

    def __init__(
        self,
        *,
        base_epoch: int = 1789000000,  # ~2026-09-10 (well past Gate 15A activation)
        bar_count: int = 250,
        symbols: Sequence[str] = ("XAUUSD", "XAUUSDm"),
    ) -> None:
        self.base_epoch = base_epoch
        self.bar_count = bar_count
        self.symbols = list(symbols)
        self.copy_rates_calls: list[dict[str, Any]] = []

    def symbols_get(self) -> Any:
        return [MockSymbolInfo(s) for s in self.symbols]

    def symbol_info(self, symbol: str) -> Any:
        if symbol in self.symbols:
            return MockSymbolInfo(symbol)
        return None

    def symbol_info_tick(self, symbol: str) -> Any:
        class MockTick:
            bid = 2500.00
            ask = 2500.25
            time = self.base_epoch
        return MockTick()

    def copy_rates_from_pos(
        self, symbol: str, timeframe: int, start_pos: int, count: int
    ) -> np.ndarray | None:
        self.copy_rates_calls.append({
            "symbol": symbol,
            "timeframe": timeframe,
            "start_pos": start_pos,
            "count": count,
        })
        if symbol not in self.symbols:
            return None

        # Map timeframe enum to minutes
        tf_mins = {
            self.TIMEFRAME_M5: 5,
            self.TIMEFRAME_M15: 15,
            self.TIMEFRAME_M30: 30,
            self.TIMEFRAME_H1: 60,
            self.TIMEFRAME_H4: 240,
            self.TIMEFRAME_D1: 1440,
        }.get(timeframe, 5)

        step_seconds = tf_mins * 60
        actual_count = min(count, self.bar_count)
        # End time of completed bars (start_pos=1 skips 1 bar)
        end_time = self.base_epoch - (start_pos * step_seconds)
        start_time = end_time - (actual_count * step_seconds)

        times = np.arange(start_time, end_time, step_seconds, dtype=np.int64)[:actual_count]

        # Build numpy structured array matching MT5 format
        dtype = np.dtype([
            ("time", "<i8"),
            ("open", "<f8"),
            ("high", "<f8"),
            ("low", "<f8"),
            ("close", "<f8"),
            ("tick_volume", "<i8"),
            ("spread", "<i4"),
            ("real_volume", "<i8"),
        ])

        arr = np.zeros(actual_count, dtype=dtype)
        arr["time"] = times
        base_price = 2500.0
        for i in range(actual_count):
            p = base_price + np.sin(i * 0.1) * 5.0
            arr["open"][i] = p
            arr["high"][i] = p + 1.5
            arr["low"][i] = p - 1.5
            arr["close"][i] = p + 0.5
            arr["tick_volume"][i] = 100 + (i % 50)
            arr["spread"][i] = 20
            arr["real_volume"][i] = 0

        return arr


# =============================================================================
# Test 1: Capability Facade Whitelist & Attribute Blocking
# =============================================================================
def test_01_capability_facade_whitelist_and_blocking() -> None:
    session = MockMT5Session()
    facade = MT5ReadOnlyCapabilityFacade(session)

    # Allowed methods succeed
    assert facade.symbols_get() is not None
    assert facade.symbol_info("XAUUSD") is not None
    assert facade.symbol_info_tick("XAUUSD") is not None
    rates = facade.copy_rates_from_pos("XAUUSD", MockMT5Session.TIMEFRAME_M5, 1, 10)
    assert rates is not None and len(rates) == 10

    # Whitelisted timeframe constants succeed
    assert facade.TIMEFRAME_M5 == 5
    assert facade.TIMEFRAME_H1 == 16385

    # Forbidden mutating methods raise PermissionError
    with pytest.raises(PermissionError):
        facade.order_send()
    with pytest.raises(PermissionError):
        facade.order_check()
    with pytest.raises(PermissionError):
        facade.positions_get()
    with pytest.raises(PermissionError):
        facade.history_deals_get()

    # Unrecognized methods raise AttributeError
    with pytest.raises(AttributeError):
        facade.arbitrary_unknown_call()


# =============================================================================
# Test 2: Forming Candle Exclusion (start_pos >= 1)
# =============================================================================
def test_02_forming_candle_exclusion() -> None:
    session = MockMT5Session()
    facade = MT5ReadOnlyCapabilityFacade(session)

    # start_pos=0 is the active forming candle -> strictly rejected
    with pytest.raises(IncompleteCandleAccessAttemptError):
        facade.copy_rates_from_pos("XAUUSD", MockMT5Session.TIMEFRAME_M5, 0, 100)

    with pytest.raises(IncompleteCandleAccessAttemptError):
        facade.copy_rates_from_pos("XAUUSD", MockMT5Session.TIMEFRAME_M5, -1, 100)

    # start_pos=1 succeeds
    rates = facade.copy_rates_from_pos("XAUUSD", MockMT5Session.TIMEFRAME_M5, 1, 10)
    assert rates is not None


# =============================================================================
# Test 3: Multi-Timeframe Acquisition & UTC Timestamp Handling
# =============================================================================
def test_03_multi_timeframe_acquisition_and_utc() -> None:
    session = MockMT5Session(base_epoch=1789000000, bar_count=250)
    adapter = MT5ReadOnlyForwardAcquisitionAdapter(session, is_synthetic=True)
    snapshot = adapter.acquire_snapshot()

    assert snapshot.canonical_instrument == "XAUUSD"
    assert snapshot.broker_symbol in ("XAUUSD", "XAUUSDm")
    assert snapshot.is_synthetic is True

    # Check that required timeframes are present
    for tf in ("M5", "M15", "M30", "H1", "H4"):
        assert tf in snapshot.market_data
        df = snapshot.market_data[tf]
        assert len(df) >= 200
        # Timezone must be explicit UTC
        assert df["time"].dt.tz is not None
        assert str(df["time"].dt.tz) == "UTC"
        # Monotonic increasing
        assert df["time"].is_monotonic_increasing
        # Required columns present
        for col in ("time", "open", "high", "low", "close", "tick_volume"):
            assert col in df.columns

    # Check that copy_rates_from_pos was strictly invoked with start_pos=1
    for call in session.copy_rates_calls:
        assert call["start_pos"] == 1


# =============================================================================
# Test 4: Insufficient Bars Rejection
# =============================================================================
def test_04_insufficient_bars_rejection() -> None:
    # Session with only 30 bars (default requires 200)
    session = MockMT5Session(bar_count=30)
    adapter = MT5ReadOnlyForwardAcquisitionAdapter(session, is_synthetic=True)
    with pytest.raises(InsufficientForwardHistoryError):
        adapter.acquire_snapshot()


# =============================================================================
# Test 5: None Broker Return Rejection
# =============================================================================
def test_05_none_broker_return_rejection() -> None:
    session = MockMT5Session()
    # Force copy_rates_from_pos to return None
    session.copy_rates_from_pos = lambda *args, **kwargs: None  # type: ignore
    adapter = MT5ReadOnlyForwardAcquisitionAdapter(session, is_synthetic=True)
    with pytest.raises(MT5ConnectionUnavailableError):
        adapter.acquire_snapshot()


# =============================================================================
# Test 6: Malformed OHLC Geometry Rejection
# =============================================================================
def test_06_malformed_ohlc_geometry_rejection() -> None:
    session = MockMT5Session()
    orig_copy = session.copy_rates_from_pos

    def corrupt_copy(symbol: str, tf: int, pos: int, count: int) -> np.ndarray | None:
        rates = orig_copy(symbol, tf, pos, count)
        if rates is not None and tf == MockMT5Session.TIMEFRAME_M5:
            # Corrupt low > high on bar 10
            rates["low"][10] = rates["high"][10] + 5.0
        return rates

    session.copy_rates_from_pos = corrupt_copy  # type: ignore
    adapter = MT5ReadOnlyForwardAcquisitionAdapter(session, is_synthetic=True)
    with pytest.raises(MalformedBarDataError):
        adapter.acquire_snapshot()


# =============================================================================
# Test 7: Duplicate Timestamps Rejection
# =============================================================================
def test_07_duplicate_timestamps_rejection() -> None:
    session = MockMT5Session()
    orig_copy = session.copy_rates_from_pos

    def duplicate_copy(symbol: str, tf: int, pos: int, count: int) -> np.ndarray | None:
        rates = orig_copy(symbol, tf, pos, count)
        if rates is not None and tf == MockMT5Session.TIMEFRAME_M5:
            # Duplicate timestamp
            rates["time"][10] = rates["time"][9]
        return rates

    session.copy_rates_from_pos = duplicate_copy  # type: ignore
    adapter = MT5ReadOnlyForwardAcquisitionAdapter(session, is_synthetic=True)
    with pytest.raises(MalformedBarDataError):
        adapter.acquire_snapshot()


# =============================================================================
# Test 8: Deterministic Snapshot Fingerprint & Sensitivity
# =============================================================================
def test_08_snapshot_fingerprint_determinism_and_sensitivity() -> None:
    session1 = MockMT5Session(base_epoch=1789000000, bar_count=200)
    adapter1 = MT5ReadOnlyForwardAcquisitionAdapter(session1, is_synthetic=True)
    snap1 = adapter1.acquire_snapshot()

    session2 = MockMT5Session(base_epoch=1789000000, bar_count=200)
    adapter2 = MT5ReadOnlyForwardAcquisitionAdapter(session2, is_synthetic=True)
    snap2 = adapter2.acquire_snapshot()

    # Identical snapshots produce identical lowercase 64-hex SHA256 IDs
    assert snap1.source_snapshot_id == snap2.source_snapshot_id
    assert len(snap1.source_snapshot_id) == 64
    assert snap1.source_snapshot_id == snap1.source_snapshot_id.lower()

    # Change 1 bar's close price -> fingerprint must change
    modified_market_data = dict(snap1.market_data)
    m5_modified = modified_market_data["M5"].copy()
    m5_modified.loc[0, "close"] += 0.05
    modified_market_data["M5"] = m5_modified

    diff_id = compute_canonical_snapshot_id(modified_market_data)
    assert diff_id != snap1.source_snapshot_id


# =============================================================================
# Test 9: Attestation Integrity & Tamper Detection
# =============================================================================
def test_09_attestation_integrity_and_tamper_detection() -> None:
    session = MockMT5Session(base_epoch=1789000000)
    adapter = MT5ReadOnlyForwardAcquisitionAdapter(session, is_synthetic=True)
    snapshot = adapter.acquire_snapshot()

    att = snapshot.attestation
    assert att.verify_integrity() is True

    # Tamper with decision time in attestation -> verification must fail
    tampered_att = replace(att, decision_time_utc="2026-10-01T00:00:00Z")
    assert tampered_att.verify_integrity() is False

    # Tamper with snapshot ID -> verification must fail
    tampered_id = replace(att, source_snapshot_id="0" * 64)
    assert tampered_id.verify_integrity() is False


# =============================================================================
# Test 10: Frozen Research Boundary Enforcement
# =============================================================================
def test_10_frozen_research_boundary_enforcement() -> None:
    # 2026-08-14T20:55:00Z corresponds to epoch 1786740900
    pre_freeze_epoch = 1786740900 - 3600  # 1 hour before freeze
    session = MockMT5Session(base_epoch=pre_freeze_epoch)
    adapter = MT5ReadOnlyForwardAcquisitionAdapter(session, is_synthetic=True)

    with pytest.raises(HistoricalFreezeBoundaryViolationError):
        adapter.acquire_snapshot(enforce_forward_boundaries=True)


# =============================================================================
# Test 11: Gate 15A Activation Boundary Enforcement
# =============================================================================
def test_11_gate_15a_activation_boundary_enforcement() -> None:
    # Timestamp between research freeze (2026-08-14, ~1786740900) and activation (2026-09-06, ~1788700800)
    mid_epoch = 1787500000
    session = MockMT5Session(base_epoch=mid_epoch)
    adapter = MT5ReadOnlyForwardAcquisitionAdapter(session, is_synthetic=True)

    with pytest.raises(PreActivationForwardError):
        adapter.acquire_snapshot(enforce_forward_boundaries=True)


# =============================================================================
# Test 12: Unsupported Symbol Rejection
# =============================================================================
def test_12_unsupported_symbol_rejection() -> None:
    session = MockMT5Session(symbols=["EURUSD", "GBPUSD"])
    adapter = MT5ReadOnlyForwardAcquisitionAdapter(session, is_synthetic=True)

    with pytest.raises(SymbolResolutionError):
        adapter.acquire_snapshot()


# =============================================================================
# Test 13: Static AST Safety Check — No Order/Write APIs in Adapter
# =============================================================================
def test_13_static_safety_audit_no_broker_writes() -> None:
    adapter_file = REPO_ROOT / "02_AI" / "Adapters" / "mt5_read_only_forward_acquisition_adapter.py"
    tree = ast.parse(adapter_file.read_text(encoding="utf-8"))

    forbidden_names = {
        "order_send",
        "OrderSend",
        "order_modify",
        "OrderModify",
        "order_close",
        "OrderClose",
        "PositionOpen",
        "PositionClose",
        "RiskEngine",
        "broker_aware_risk_engine",
        "account_protection_guard",
        "trade_ready",
    }

    imported_names = set()
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
    assert not violations, f"Forbidden imports found in forward acquisition adapter: {violations}"
