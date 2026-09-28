"""
===============================================================================
Module      : test_mt5_read_only_forward_acquisition_adapter.py
Project     : PulseViper XAU AI
Purpose     : Gate 15B-A Unit Tests — Reopened Timestamp-Semantics Authority
===============================================================================
"""

from __future__ import annotations

import ast
import datetime as dt
from dataclasses import replace
import importlib
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any, Sequence, cast
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_acq_mod = importlib.import_module(
    "02_AI.Adapters.mt5_read_only_forward_acquisition_adapter"
)

MT5ReadOnlyCapabilityFacade = _acq_mod.MT5ReadOnlyCapabilityFacade
MT5ReadOnlyForwardAcquisitionAdapter = (
    _acq_mod.MT5ReadOnlyForwardAcquisitionAdapter
)

VerifiedForwardAcquisitionAuthority = (
    _acq_mod.VerifiedForwardAcquisitionAuthority
)

verify_forward_acquisition_authority = (
    _acq_mod.verify_forward_acquisition_authority
)

compute_canonical_snapshot_id = (
    _acq_mod.compute_canonical_snapshot_id
)

normalize_ny_close_server_epoch = (
    _acq_mod.normalize_ny_close_server_epoch
)

detect_timestamp_basis_from_tick = (
    _acq_mod.detect_timestamp_basis_from_tick
)

IncompleteCandleAccessAttemptError = (
    _acq_mod.IncompleteCandleAccessAttemptError
)

MT5ConnectionUnavailableError = (
    _acq_mod.MT5ConnectionUnavailableError
)

MalformedBarDataError = (
    _acq_mod.MalformedBarDataError
)

HistoricalFreezeBoundaryViolationError = (
    _acq_mod.HistoricalFreezeBoundaryViolationError
)

PreActivationForwardError = (
    _acq_mod.PreActivationForwardError
)

SymbolResolutionError = (
    _acq_mod.SymbolResolutionError
)

TimestampBasisResolutionError = (
    _acq_mod.TimestampBasisResolutionError
)

TIME_BASIS_UNIX_UTC = (
    _acq_mod.TIME_BASIS_UNIX_UTC
)

TIME_BASIS_NY_CLOSE_SERVER = (
    _acq_mod.TIME_BASIS_NY_CLOSE_SERVER
)

_NEW_YORK = ZoneInfo(
    "America/New_York"
)


def _epoch(
    value: str,
) -> int:
    ts = pd.Timestamp(
        value
    )

    if ts is pd.NaT:
        raise RuntimeError(
            "TEST_TIMESTAMP_IS_NAT"
        )

    return int(
        cast(
            pd.Timestamp,
            ts,
        ).timestamp()
    )


class MockSymbolInfo:
    def __init__(
        self,
        name: str,
    ) -> None:
        self.name = name
        self.visible = True
        self.selected = True
        self.digits = 2
        self.point = 0.01
        self.trade_contract_size = 100.0


class MockMT5Session:
    TIMEFRAME_M5 = 5
    TIMEFRAME_M15 = 15
    TIMEFRAME_M30 = 30
    TIMEFRAME_H1 = 16385
    TIMEFRAME_H4 = 16388
    TIMEFRAME_D1 = 16408

    def __init__(
        self,
        *,
        base_epoch: int = 1789000000,
        bar_count: int = 5200,
        symbols: Sequence[str] = (
            "XAUUSD",
            "XAUUSDm",
        ),
        raw_tick_epoch: int | None = None,
        server_wall_clock: bool = False,
    ) -> None:
        self.base_epoch = int(
            base_epoch
        )

        self.bar_count = int(
            bar_count
        )

        self.symbols = list(
            symbols
        )

        self.raw_tick_epoch = (
            int(raw_tick_epoch)
            if raw_tick_epoch is not None
            else int(base_epoch)
        )

        self.server_wall_clock = bool(
            server_wall_clock
        )

        self.copy_rates_calls: list[
            dict[str, Any]
        ] = []

    def symbols_get(
        self,
    ) -> list[MockSymbolInfo]:
        return [
            MockSymbolInfo(
                symbol
            )
            for symbol
            in self.symbols
        ]

    def symbol_info(
        self,
        symbol: str,
    ) -> MockSymbolInfo | None:
        if symbol in self.symbols:
            return MockSymbolInfo(
                symbol
            )

        return None

    def symbol_info_tick(
        self,
        symbol: str,
    ) -> Any:
        if symbol not in self.symbols:
            return None

        return SimpleNamespace(
            bid=2500.00,
            ask=2500.25,
            time=self.raw_tick_epoch,
            time_msc=(
                self.raw_tick_epoch
                * 1000
            ),
        )

    @staticmethod
    def _server_offset_for_true_utc(
        true_epoch: int,
    ) -> int:
        true_utc = dt.datetime.fromtimestamp(
            true_epoch,
            tz=dt.timezone.utc,
        )

        ny = true_utc.astimezone(
            _NEW_YORK
        )

        ny_offset = ny.utcoffset()

        if ny_offset is None:
            raise RuntimeError(
                "NY_OFFSET_UNAVAILABLE"
            )

        return int(
            ny_offset.total_seconds()
            + (7 * 60 * 60)
        )

    def _encode_time(
        self,
        true_epoch: int,
    ) -> int:
        if not self.server_wall_clock:
            return int(
                true_epoch
            )

        return int(
            true_epoch
            + self._server_offset_for_true_utc(
                true_epoch
            )
        )

    def copy_rates_from_pos(
        self,
        symbol: str,
        timeframe: int,
        start_pos: int,
        count: int,
    ) -> np.ndarray | None:

        self.copy_rates_calls.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "start_pos": start_pos,
                "count": count,
            }
        )

        if symbol not in self.symbols:
            return None

        timeframe_minutes = {
            self.TIMEFRAME_M5: 5,
            self.TIMEFRAME_M15: 15,
            self.TIMEFRAME_M30: 30,
            self.TIMEFRAME_H1: 60,
            self.TIMEFRAME_H4: 240,
            self.TIMEFRAME_D1: 1440,
        }.get(
            timeframe,
            5,
        )

        step_seconds = (
            timeframe_minutes
            * 60
        )

        actual_count = min(
            int(count),
            self.bar_count,
        )

        end_time = (
            self.base_epoch
            - (
                int(start_pos)
                * step_seconds
            )
        )

        start_time = (
            end_time
            - (
                actual_count
                * step_seconds
            )
        )

        true_times = np.arange(
            start_time,
            end_time,
            step_seconds,
            dtype=np.int64,
        )[:actual_count]

        encoded_times = np.asarray(
            [
                self._encode_time(
                    int(value)
                )
                for value
                in true_times
            ],
            dtype=np.int64,
        )

        dtype = np.dtype(
            [
                ("time", "<i8"),
                ("open", "<f8"),
                ("high", "<f8"),
                ("low", "<f8"),
                ("close", "<f8"),
                ("tick_volume", "<i8"),
                ("spread", "<i4"),
                ("real_volume", "<i8"),
            ]
        )

        rates = np.zeros(
            actual_count,
            dtype=dtype,
        )

        rates["time"] = (
            encoded_times
        )

        indexes = np.arange(
            actual_count,
            dtype=np.float64,
        )

        base_price = (
            2500.0
            + np.sin(
                indexes * 0.1
            )
            * 5.0
        )

        rates["open"] = (
            base_price
        )

        rates["high"] = (
            base_price
            + 1.5
        )

        rates["low"] = (
            base_price
            - 1.5
        )

        rates["close"] = (
            base_price
            + 0.5
        )

        rates["tick_volume"] = (
            100
            + (
                indexes.astype(
                    np.int64
                )
                % 50
            )
        )

        return rates


def test_01_capability_facade_whitelist_and_blocking() -> None:
    session = MockMT5Session()
    facade = MT5ReadOnlyCapabilityFacade(
        session
    )

    assert facade.symbols_get()
    assert facade.symbol_info(
        "XAUUSD"
    ) is not None

    rates = facade.copy_rates_from_pos(
        "XAUUSD",
        session.TIMEFRAME_M5,
        1,
        10,
    )

    assert rates is not None
    assert len(rates) == 10

    with pytest.raises(
        PermissionError
    ):
        facade.order_send()

    with pytest.raises(
        PermissionError
    ):
        facade.positions_get()

    with pytest.raises(
        PermissionError
    ):
        facade.history_deals_get()


def test_02_forming_candle_exclusion() -> None:
    session = MockMT5Session()
    facade = MT5ReadOnlyCapabilityFacade(
        session
    )

    with pytest.raises(
        IncompleteCandleAccessAttemptError
    ):
        facade.copy_rates_from_pos(
            "XAUUSD",
            session.TIMEFRAME_M5,
            0,
            10,
        )

    with pytest.raises(
        IncompleteCandleAccessAttemptError
    ):
        facade.copy_rates_from_pos(
            "XAUUSD",
            session.TIMEFRAME_M5,
            -1,
            10,
        )


def test_03_unix_utc_synthetic_acquisition() -> None:
    session = MockMT5Session(
        base_epoch=1789000000,
    )

    adapter = MT5ReadOnlyForwardAcquisitionAdapter(
        session,
        is_synthetic=True,
    )

    snapshot = adapter.acquire_snapshot()

    assert (
        snapshot.attestation.time_basis_policy
        == TIME_BASIS_UNIX_UTC
    )

    assert (
        snapshot.authority
        is None
    )

    for timeframe in (
        "M5",
        "M15",
        "M30",
        "H1",
        "H4",
    ):
        frame = snapshot.market_data[
            timeframe
        ]

        assert (
            str(
                frame["time"].dt.tz
            )
            == "UTC"
        )


def test_04_insufficient_bars_rejected() -> None:
    session = MockMT5Session(
        bar_count=30,
    )

    adapter = MT5ReadOnlyForwardAcquisitionAdapter(
        session,
        is_synthetic=True,
    )

    with pytest.raises(
        _acq_mod.InsufficientForwardHistoryError
    ):
        adapter.acquire_snapshot()


def test_05_none_rates_rejected() -> None:
    session = MockMT5Session()

    session.copy_rates_from_pos = (  # type: ignore[method-assign]
        lambda *args, **kwargs: None
    )

    adapter = MT5ReadOnlyForwardAcquisitionAdapter(
        session,
        is_synthetic=True,
    )

    with pytest.raises(
        MT5ConnectionUnavailableError
    ):
        adapter.acquire_snapshot()


def test_06_bad_ohlc_rejected() -> None:
    session = MockMT5Session()

    original = (
        session.copy_rates_from_pos
    )

    def corrupt(
        symbol: str,
        timeframe: int,
        start_pos: int,
        count: int,
    ) -> np.ndarray | None:

        rates = original(
            symbol,
            timeframe,
            start_pos,
            count,
        )

        if (
            rates is not None
            and timeframe
            == session.TIMEFRAME_M5
        ):
            rates["low"][10] = (
                rates["high"][10]
                + 5.0
            )

        return rates

    session.copy_rates_from_pos = corrupt  # type: ignore[method-assign]

    adapter = MT5ReadOnlyForwardAcquisitionAdapter(
        session,
        is_synthetic=True,
    )

    with pytest.raises(
        MalformedBarDataError
    ):
        adapter.acquire_snapshot()


def test_07_duplicate_times_rejected() -> None:
    session = MockMT5Session()

    original = (
        session.copy_rates_from_pos
    )

    def duplicate(
        symbol: str,
        timeframe: int,
        start_pos: int,
        count: int,
    ) -> np.ndarray | None:

        rates = original(
            symbol,
            timeframe,
            start_pos,
            count,
        )

        if (
            rates is not None
            and timeframe
            == session.TIMEFRAME_M5
        ):
            rates["time"][10] = (
                rates["time"][9]
            )

        return rates

    session.copy_rates_from_pos = duplicate  # type: ignore[method-assign]

    adapter = MT5ReadOnlyForwardAcquisitionAdapter(
        session,
        is_synthetic=True,
    )

    with pytest.raises(
        MalformedBarDataError
    ):
        adapter.acquire_snapshot()


def test_08_snapshot_hash_is_deterministic_and_sensitive() -> None:
    session_a = MockMT5Session()
    session_b = MockMT5Session()

    adapter_a = MT5ReadOnlyForwardAcquisitionAdapter(
        session_a,
        is_synthetic=True,
    )

    adapter_b = MT5ReadOnlyForwardAcquisitionAdapter(
        session_b,
        is_synthetic=True,
    )

    snapshot_a = adapter_a.acquire_snapshot()
    snapshot_b = adapter_b.acquire_snapshot()

    assert (
        snapshot_a.source_snapshot_id
        == snapshot_b.source_snapshot_id
    )

    modified = dict(
        snapshot_a.market_data
    )

    m5 = modified[
        "M5"
    ].copy()

    m5.loc[
        0,
        "close",
    ] += 0.00000001

    modified[
        "M5"
    ] = m5

    assert (
        compute_canonical_snapshot_id(
            modified
        )
        != snapshot_a.source_snapshot_id
    )


def test_09_attestation_tamper_detection() -> None:
    session = MockMT5Session()

    adapter = MT5ReadOnlyForwardAcquisitionAdapter(
        session,
        is_synthetic=True,
    )

    snapshot = adapter.acquire_snapshot()

    assert (
        snapshot.attestation.verify_integrity()
        is True
    )

    tampered = replace(
        snapshot.attestation,
        time_basis_policy=(
            TIME_BASIS_NY_CLOSE_SERVER
        ),
    )

    assert (
        tampered.verify_integrity()
        is False
    )


def test_10_research_freeze_boundary() -> None:
    pre_freeze = (
        _epoch(
            "2026-08-14T19:00:00Z"
        )
    )

    session = MockMT5Session(
        base_epoch=pre_freeze,
    )

    adapter = MT5ReadOnlyForwardAcquisitionAdapter(
        session,
        is_synthetic=True,
    )

    with pytest.raises(
        HistoricalFreezeBoundaryViolationError
    ):
        adapter.acquire_snapshot(
            enforce_forward_boundaries=True
        )


def test_11_gate15a_activation_boundary() -> None:
    before_activation = (
        _epoch(
            "2026-09-01T12:00:00Z"
        )
    )

    session = MockMT5Session(
        base_epoch=before_activation,
    )

    adapter = MT5ReadOnlyForwardAcquisitionAdapter(
        session,
        is_synthetic=True,
    )

    with pytest.raises(
        PreActivationForwardError
    ):
        adapter.acquire_snapshot(
            enforce_forward_boundaries=True
        )


def test_12_unsupported_symbol_rejected() -> None:
    session = MockMT5Session(
        symbols=(
            "EURUSD",
            "GBPUSD",
        ),
    )

    adapter = MT5ReadOnlyForwardAcquisitionAdapter(
        session,
        is_synthetic=True,
    )

    with pytest.raises(
        SymbolResolutionError
    ):
        adapter.acquire_snapshot()


def test_13_static_ast_safety() -> None:
    adapter_file = (
        REPO_ROOT
        / "02_AI"
        / "Adapters"
        / "mt5_read_only_forward_acquisition_adapter.py"
    )

    tree = ast.parse(
        adapter_file.read_text(
            encoding="utf-8"
        )
    )

    forbidden = {
        "RiskEngine",
        "trade_ready",
        "broker_aware_risk_engine",
        "account_protection_guard",
        "order_send",
        "positions_get",
        "orders_get",
        "history_deals_get",
    }

    imported: set[str] = set()

    for node in ast.walk(
        tree
    ):
        if isinstance(
            node,
            ast.Import,
        ):
            for alias in node.names:
                imported.add(
                    alias.name
                )

        elif isinstance(
            node,
            ast.ImportFrom,
        ):
            if node.module:
                imported.add(
                    node.module
                )

            for alias in node.names:
                imported.add(
                    alias.name
                )

    assert not (
        forbidden
        & imported
    )


def test_14_gate13_d1_reconstruction_preserved() -> None:
    session = MockMT5Session()

    adapter = MT5ReadOnlyForwardAcquisitionAdapter(
        session,
        is_synthetic=True,
    )

    snapshot = adapter.acquire_snapshot()

    assert (
        "D1"
        not in snapshot.market_data
    )

    pipeline_mod = importlib.import_module(
        "02_AI.Features.portable_feature_pipeline"
    )

    pipeline = (
        pipeline_mod.PortableFeaturePipeline()
    )

    result = pipeline.generate(
        snapshot.market_data,
        symbol=snapshot.canonical_instrument,
    )

    assert (
        result.feature_count
        == 331
    )

    assert (
        result.feature_columns_sha256
        == _acq_mod.EXPECTED_FEATURE_COLUMNS_SHA256
    )


def test_15_authority_token_isolation() -> None:
    base_epoch = _epoch(
        "2026-09-20T12:00:00Z"
    )

    session = MockMT5Session(
        base_epoch=base_epoch,
        raw_tick_epoch=base_epoch,
    )

    adapter = MT5ReadOnlyForwardAcquisitionAdapter(
        session,
        is_synthetic=False,
        timestamp_basis=(
            TIME_BASIS_UNIX_UTC
        ),
        now_provider=(
            lambda: float(
                base_epoch
            )
        ),
    )

    snapshot = adapter.acquire_snapshot()

    assert (
        snapshot.authority
        is not None
    )

    assert (
        snapshot.authority.is_valid_authority()
        is True
    )

    with pytest.raises(
        PermissionError
    ):
        VerifiedForwardAcquisitionAuthority(
            token=object(),
            attestation=snapshot.attestation,
            is_synthetic=False,
        )

    verified = verify_forward_acquisition_authority(
        snapshot.authority,
        expected_decision_time_utc=(
            snapshot.decision_time_utc
        ),
        expected_source_snapshot_id=(
            snapshot.source_snapshot_id
        ),
        expected_canonical_instrument=(
            snapshot.canonical_instrument
        ),
        expected_feature_columns_sha256=(
            _acq_mod.EXPECTED_FEATURE_COLUMNS_SHA256
        ),
        expected_model_sha256=(
            _acq_mod.FROZEN_MODEL_SHA256
        ),
    )

    assert (
        verified.attestation_sha256
        == snapshot.attestation.attestation_sha256
    )


def test_16_auto_detects_unix_utc() -> None:
    now_epoch = _epoch(
        "2026-09-20T12:00:10Z"
    )

    raw_tick = _epoch(
        "2026-09-20T12:00:08Z"
    )

    resolution = (
        detect_timestamp_basis_from_tick(
            raw_tick_epoch=(
                raw_tick
            ),
            now_epoch=(
                float(
                    now_epoch
                )
            ),
        )
    )

    assert (
        resolution.policy
        == TIME_BASIS_UNIX_UTC
    )

    assert (
        resolution.reference_offset_seconds
        == 0
    )


def test_17_auto_detects_ny_close_server_wall_clock() -> None:
    true_tick = _epoch(
        "2026-09-20T12:00:08Z"
    )

    raw_server_tick = (
        true_tick
        + (3 * 60 * 60)
    )

    now_epoch = _epoch(
        "2026-09-20T12:00:10Z"
    )

    resolution = (
        detect_timestamp_basis_from_tick(
            raw_tick_epoch=(
                raw_server_tick
            ),
            now_epoch=(
                float(
                    now_epoch
                )
            ),
        )
    )

    assert (
        resolution.policy
        == TIME_BASIS_NY_CLOSE_SERVER
    )

    assert (
        resolution.reference_offset_seconds
        == 10800
    )


def test_18_ny_close_historical_rows_are_dst_aware() -> None:
    winter_true = _epoch(
        "2026-03-08T06:00:00Z"
    )

    summer_true = _epoch(
        "2026-03-09T06:00:00Z"
    )

    winter_raw = (
        winter_true
        + (2 * 60 * 60)
    )

    summer_raw = (
        summer_true
        + (3 * 60 * 60)
    )

    winter_utc, winter_offset = (
        normalize_ny_close_server_epoch(
            winter_raw
        )
    )

    summer_utc, summer_offset = (
        normalize_ny_close_server_epoch(
            summer_raw
        )
    )

    assert (
        int(
            winter_utc.timestamp()
        )
        == winter_true
    )

    assert (
        int(
            summer_utc.timestamp()
        )
        == summer_true
    )

    assert (
        winter_offset
        == 7200
    )

    assert (
        summer_offset
        == 10800
    )


def test_19_stale_or_unprovable_time_basis_fails_closed() -> None:
    old_tick = _epoch(
        "2026-09-20T09:00:00Z"
    )

    now_epoch = _epoch(
        "2026-09-20T12:00:00Z"
    )

    with pytest.raises(
        TimestampBasisResolutionError
    ):
        detect_timestamp_basis_from_tick(
            raw_tick_epoch=(
                old_tick
            ),
            now_epoch=(
                float(
                    now_epoch
                )
            ),
            max_tick_age_seconds=180,
        )


def test_20_exact_331_feature_contract_under_ny_close_policy() -> None:
    true_now = _epoch(
        "2026-09-20T12:00:00Z"
    )

    raw_server_now = (
        true_now
        + (3 * 60 * 60)
    )

    session = MockMT5Session(
        base_epoch=true_now,
        raw_tick_epoch=(
            raw_server_now
        ),
        server_wall_clock=True,
    )

    adapter = MT5ReadOnlyForwardAcquisitionAdapter(
        session,
        is_synthetic=False,
        timestamp_basis=(
            TIME_BASIS_NY_CLOSE_SERVER
        ),
        now_provider=(
            lambda: float(
                true_now
            )
        ),
    )

    snapshot = (
        adapter.acquire_snapshot()
    )

    assert (
        snapshot.attestation.time_basis_policy
        == TIME_BASIS_NY_CLOSE_SERVER
    )

    pipeline_mod = importlib.import_module(
        "02_AI.Features.portable_feature_pipeline"
    )

    pipeline = (
        pipeline_mod.PortableFeaturePipeline()
    )

    result = pipeline.generate(
        snapshot.market_data,
        symbol=snapshot.canonical_instrument,
    )

    assert (
        result.feature_count
        == 331
    )

    assert (
        result.feature_columns_sha256
        == _acq_mod.EXPECTED_FEATURE_COLUMNS_SHA256
    )

    decision_ts = pd.Timestamp(
        snapshot.decision_time_utc
    )

    tick_ts = pd.Timestamp(
        snapshot.attestation.time_basis_reference_tick_utc
    )

    if (
        decision_ts is pd.NaT
        or tick_ts is pd.NaT
    ):
        raise AssertionError(
            "Unexpected NaT in causal test"
        )

    assert (
        cast(
            pd.Timestamp,
            decision_ts,
        )
        <= cast(
            pd.Timestamp,
            tick_ts,
        )
    )