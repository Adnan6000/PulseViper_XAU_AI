"""
===============================================================================
Module      : mt5_read_only_forward_acquisition_adapter.py
Project     : PulseViper XAU AI
Purpose     : Read-Only Forward Market Data Acquisition Authority (Gate 15B-A)
===============================================================================

Production-safe, provably isolated, read-only MetaTrader 5 market data acquisition
adapter. Captures completed multi-timeframe OHLCV snapshots, computes deterministic
source snapshot fingerprints, and generates tamper-evident acquisition attestations
for Gate 13 feature generation and Gate 15A shadow observation.

Safety Guarantees (NON-NEGOTIABLE):
- ZERO broker write methods: order_send, order_modify, order_close, positions_get,
  and RiskEngine imports are strictly forbidden.
- Capability facade exposes ONLY whitelisted read-only market data methods.
- Enforces start_pos >= 1 to strictly exclude forming/incomplete candles.
- Normalizes integer Unix timestamps to UTC (pd.to_datetime(..., unit='s', utc=True)).
- Computes deterministic lowercase 64-hex SHA256 snapshot fingerprint using exact
  numeric representation (float.hex() and integer tick_volume), removing decimal rounding.
- Preserves Gate 13 authoritative D1 reconstruction: acquires authoritative intraday
  histories (M5, M15, M30, H1, H4). Native D1 is excluded from market_data by default.
- Capability/authority-bound result pattern: VerifiedForwardAcquisitionAuthority
  prevents provenance escalation from arbitrary or forged plain dataclass attestations.
- Supports only frozen supported symbols: XAUUSD and XAUUSDm.
- Strictly marks synthetic/mock data to prevent unauthorized true-forward escalation.
- live_authorized = False, execution_authorized = False.
"""

from __future__ import annotations

import collections.abc
from dataclasses import dataclass
import hashlib
import importlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Protocol, Sequence

import numpy as np
import pandas as pd

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Authorities & Contracts from Gate 13, 14, 15A
_contract = importlib.import_module("02_AI.Features.portable_feature_contract")
_observer = importlib.import_module("02_AI.Models.frozen_c04_shadow_observer")
_adapter_mod = importlib.import_module("02_AI.Adapters.xauusd_broker_adapter")

CANONICAL_SYMBOL: str = str(_contract.CANONICAL_SYMBOL)
SUPPORTED_SYMBOLS: tuple[str, ...] = tuple(_contract.SUPPORTED_SYMBOLS)
EXPECTED_FEATURE_COLUMNS_SHA256: str = str(_contract.EXPECTED_FEATURE_COLUMNS_SHA256)
FROZEN_MODEL_SHA256: str = str(_contract.FROZEN_MODEL_SHA256)
normalize_supported_symbol: Any = _contract.normalize_supported_symbol

RESEARCH_FREEZE_BOUNDARY_UTC: str = str(_observer.RESEARCH_FREEZE_BOUNDARY_UTC)
GATE_15A_ACTIVATION_UTC: str = str(_observer.GATE_15A_ACTIVATION_UTC)
validate_iso8601_utc: Any = _observer.validate_iso8601_utc
validate_snapshot_id: Any = _observer.validate_snapshot_id
TrueForwardAcquisitionNotAuthorizedError: Any = _observer.TrueForwardAcquisitionNotAuthorizedError

CanonicalGoldResolver: Any = _adapter_mod.CanonicalGoldResolver

ACQUISITION_SCHEMA_VERSION: str = "2.0.0"
ACQUISITION_AUTHORITY_ID: str = "MT5ReadOnlyForwardAcquisitionAdapter:2.0.0"

# Module-owned private authority token for capability-bound provenance enforcement
_PRIVATE_FORWARD_AUTHORITY_TOKEN: object = object()

# Timeframe durations in minutes
TIMEFRAME_MINUTES: dict[str, int] = {
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}

# Default MT5 timeframe enum values if MetaTrader5 module is absent
DEFAULT_TIMEFRAME_ENUMS: dict[str, int] = {
    "TIMEFRAME_M5": 5,
    "TIMEFRAME_M15": 15,
    "TIMEFRAME_M30": 30,
    "TIMEFRAME_H1": 16385,
    "TIMEFRAME_H4": 16388,
    "TIMEFRAME_D1": 16408,
}


# =============================================================================
# Fail-Closed Exception Taxonomy
# =============================================================================

class ForwardAcquisitionError(Exception):
    """Base exception for all forward acquisition errors (fail-closed)."""
    pass


class MT5ConnectionUnavailableError(ForwardAcquisitionError):
    """Raised when MT5 API or terminal connection is unavailable."""
    pass


class IncompleteCandleAccessAttemptError(ForwardAcquisitionError):
    """Raised when an attempt is made to access forming/incomplete candles (start_pos < 1)."""
    pass


class SymbolResolutionError(ForwardAcquisitionError):
    """Raised when canonical gold symbol cannot be resolved."""
    pass


class UnsupportedSymbolError(ForwardAcquisitionError):
    """Raised when resolved symbol does not conform to Gate 13 contract."""
    pass


class InsufficientForwardHistoryError(ForwardAcquisitionError):
    """Raised when broker returns fewer closed bars than required for warmup."""
    pass


class HistoricalFreezeBoundaryViolationError(ForwardAcquisitionError):
    """Raised when decision time does not exceed the frozen research boundary."""
    pass


class PreActivationForwardError(ForwardAcquisitionError):
    """Raised when true forward observation timestamp precedes Gate 15A activation."""
    pass


class MalformedBarDataError(ForwardAcquisitionError):
    """Raised when acquired bar data violates schema, monotonicity, or finite rules."""
    pass


class AttestationIntegrityError(ForwardAcquisitionError):
    """Raised when acquisition attestation fingerprint or integrity verification fails."""
    pass


# =============================================================================
# Read-Only Capability Protocol & Facade
# =============================================================================

class ReadOnlyMT5Protocol(Protocol):
    """Structural protocol defining the exact allowed read-only MT5 interface."""
    def symbols_get(self) -> Any: ...
    def symbol_info(self, symbol: str) -> Any: ...
    def symbol_info_tick(self, symbol: str) -> Any: ...
    def copy_rates_from_pos(
        self, symbol: str, timeframe: int, start_pos: int, count: int
    ) -> np.ndarray | None: ...


class MT5ReadOnlyCapabilityFacade:
    """
    Capability-restricting facade wrapping an underlying MT5 session.
    
    Guarantees:
    - Exposes ONLY whitelisted read-only methods.
    - Explicitly blocks and raises PermissionError on any mutating/trading methods.
    - Strictly forbids start_pos < 1 in copy_rates_from_pos to prevent forming bar ingestion.
    """
    ALLOWED_METHODS: frozenset[str] = frozenset({
        "symbols_get",
        "symbol_info",
        "symbol_info_tick",
        "copy_rates_from_pos",
    })

    ALLOWED_TIMEFRAME_ATTRS: frozenset[str] = frozenset({
        "TIMEFRAME_M5",
        "TIMEFRAME_M15",
        "TIMEFRAME_M30",
        "TIMEFRAME_H1",
        "TIMEFRAME_H4",
        "TIMEFRAME_D1",
    })

    FORBIDDEN_MUTATING_METHODS: frozenset[str] = frozenset({
        "order_send",
        "order_check",
        "order_calc_margin",
        "order_calc_profit",
        "positions_get",
        "positions_total",
        "orders_get",
        "orders_total",
        "history_orders_get",
        "history_deals_get",
    })

    def __init__(self, api: Any) -> None:
        if api is None:
            raise MT5ConnectionUnavailableError("MT5 API instance must not be None")
        self._api = api

    def symbols_get(self) -> Any:
        return self._api.symbols_get()

    def symbol_info(self, symbol: str) -> Any:
        return self._api.symbol_info(symbol)

    def symbol_info_tick(self, symbol: str) -> Any:
        return self._api.symbol_info_tick(symbol)

    def copy_rates_from_pos(
        self, symbol: str, timeframe: int, start_pos: int, count: int
    ) -> np.ndarray | None:
        if start_pos < 1:
            raise IncompleteCandleAccessAttemptError(
                f"Gate 15B forbids start_pos < 1 (requested: {start_pos}). "
                "Position 0 is the incomplete/forming bar."
            )
        return self._api.copy_rates_from_pos(symbol, timeframe, start_pos, count)

    def __getattr__(self, name: str) -> Any:
        if name in self.FORBIDDEN_MUTATING_METHODS:
            raise PermissionError(
                f"Access to broker mutating/trading method {name!r} is strictly forbidden."
            )
        if name in self.ALLOWED_TIMEFRAME_ATTRS:
            if hasattr(self._api, name):
                return getattr(self._api, name)
            return DEFAULT_TIMEFRAME_ENUMS.get(name)
        if name in self.ALLOWED_METHODS:
            return getattr(self._api, name)
        raise AttributeError(
            f"Method or attribute {name!r} is not permitted on MT5ReadOnlyCapabilityFacade."
        )


# =============================================================================
# Attestation & Snapshot Dataclasses
# =============================================================================

@dataclass(frozen=True)
class ForwardAcquisitionAttestation:
    """
    Immutable attestation record establishing provenance, parameters,
    and integrity of an acquired forward market data snapshot.
    """
    schema_version: str
    acquisition_authority: str
    canonical_instrument: str
    resolved_broker_symbol: str
    acquisition_time_utc: str
    decision_time_utc: str
    timeframe_bar_counts: dict[str, int]
    earliest_bar_open_utc: dict[str, str]
    latest_bar_open_utc: dict[str, str]
    latest_bar_available_utc: dict[str, str]
    research_freeze_boundary_utc: str
    gate_15a_activation_utc: str
    source_snapshot_id: str
    feature_columns_sha256: str
    model_sha256: str
    capability_manifest: tuple[str, ...]
    is_synthetic: bool
    attestation_sha256: str

    def to_canonical_dict(self) -> dict[str, Any]:
        """Convert to canonical dictionary excluding the attestation_sha256 itself."""
        return {
            "schema_version": self.schema_version,
            "acquisition_authority": self.acquisition_authority,
            "canonical_instrument": self.canonical_instrument,
            "resolved_broker_symbol": self.resolved_broker_symbol,
            "acquisition_time_utc": self.acquisition_time_utc,
            "decision_time_utc": self.decision_time_utc,
            "timeframe_bar_counts": self.timeframe_bar_counts,
            "earliest_bar_open_utc": self.earliest_bar_open_utc,
            "latest_bar_open_utc": self.latest_bar_open_utc,
            "latest_bar_available_utc": self.latest_bar_available_utc,
            "research_freeze_boundary_utc": self.research_freeze_boundary_utc,
            "gate_15a_activation_utc": self.gate_15a_activation_utc,
            "source_snapshot_id": self.source_snapshot_id,
            "feature_columns_sha256": self.feature_columns_sha256,
            "model_sha256": self.model_sha256,
            "capability_manifest": list(self.capability_manifest),
            "is_synthetic": self.is_synthetic,
        }

    def verify_integrity(self) -> bool:
        """Verify that attestation_sha256 matches the hash of canonical dict."""
        payload = json.dumps(
            self.to_canonical_dict(), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        computed = hashlib.sha256(payload).hexdigest()
        return computed == self.attestation_sha256


class VerifiedForwardAcquisitionAuthority:
    """
    Capability-bound acquisition authority marker produced exclusively by
    MT5ReadOnlyForwardAcquisitionAdapter's genuine, non-synthetic forward acquisition path.
    
    Enforces repository architectural boundaries: prevents ordinary provenance
    escalation through public constructors, arbitrary mappings, or plain dataclass construction.
    """
    def __init__(
        self,
        token: object,
        attestation: ForwardAcquisitionAttestation,
        is_synthetic: bool,
    ) -> None:
        if token is not _PRIVATE_FORWARD_AUTHORITY_TOKEN:
            raise PermissionError(
                "VerifiedForwardAcquisitionAuthority cannot be instantiated outside "
                "the genuine MT5ReadOnlyForwardAcquisitionAdapter acquisition path."
            )
        self._token = token
        self._attestation = attestation
        self._is_synthetic = bool(is_synthetic)

    @property
    def attestation(self) -> ForwardAcquisitionAttestation:
        return self._attestation

    @property
    def is_synthetic(self) -> bool:
        return self._is_synthetic

    def is_valid_authority(self) -> bool:
        """Check object identity of internal authority token and synthetic flag."""
        return (
            (self._token is _PRIVATE_FORWARD_AUTHORITY_TOKEN)
            and (not self._is_synthetic)
            and (not self._attestation.is_synthetic)
            and self._attestation.verify_integrity()
        )


def verify_forward_acquisition_authority(
    authority: Any,
    *,
    expected_decision_time_utc: str,
    expected_source_snapshot_id: str,
    expected_canonical_instrument: str,
    expected_feature_columns_sha256: str,
    expected_model_sha256: str,
) -> ForwardAcquisitionAttestation:
    """
    Dedicated public verification function enforcing acquisition capability authority.
    
    Validates that:
    1. The authority object is a genuine VerifiedForwardAcquisitionAuthority instance.
    2. The authority possesses object identity to the private module token.
    3. The authority and underlying attestation are non-synthetic.
    4. Attestation payload integrity (attestation_sha256) is mathematically verified.
    5. Parameters match the expected decision_time, snapshot ID, instrument, and SHAs.
    6. Timestamps strictly exceed research freeze and Gate 15A activation boundaries.
    
    Raises:
        TrueForwardAcquisitionNotAuthorizedError: If any verification check fails.
    """
    if not isinstance(authority, VerifiedForwardAcquisitionAuthority):
        raise TrueForwardAcquisitionNotAuthorizedError(
            "TRUE_FORWARD_OBSERVATION is not authorized without a verified acquisition authority "
            "generated by MT5ReadOnlyForwardAcquisitionAdapter genuine acquisition path. "
            "Manual attestation construction or field reproduction is rejected."
        )

    if getattr(authority, "_token", None) is not _PRIVATE_FORWARD_AUTHORITY_TOKEN:
        raise TrueForwardAcquisitionNotAuthorizedError(
            "Verified acquisition authority does not possess the valid internal module authority token."
        )

    if authority.is_synthetic or authority.attestation.is_synthetic:
        raise TrueForwardAcquisitionNotAuthorizedError(
            "Synthetic or mocked acquisition data cannot be authorized as TRUE_FORWARD_OBSERVATION."
        )

    att = authority.attestation
    if not att.verify_integrity():
        raise TrueForwardAcquisitionNotAuthorizedError(
            "Forward acquisition attestation failed cryptographic/structural integrity verification."
        )

    if att.source_snapshot_id != expected_source_snapshot_id:
        raise TrueForwardAcquisitionNotAuthorizedError(
            f"Attestation snapshot ID mismatch: {att.source_snapshot_id} != {expected_source_snapshot_id}"
        )

    if att.decision_time_utc != expected_decision_time_utc:
        raise TrueForwardAcquisitionNotAuthorizedError(
            f"Attestation decision time mismatch: {att.decision_time_utc} != {expected_decision_time_utc}"
        )

    if att.canonical_instrument != expected_canonical_instrument:
        raise TrueForwardAcquisitionNotAuthorizedError(
            f"Attestation instrument mismatch: {att.canonical_instrument} != {expected_canonical_instrument}"
        )

    if att.feature_columns_sha256 != expected_feature_columns_sha256:
        raise TrueForwardAcquisitionNotAuthorizedError(
            "Attestation feature columns SHA256 mismatch with frozen authority."
        )

    if att.model_sha256 != expected_model_sha256:
        raise TrueForwardAcquisitionNotAuthorizedError(
            "Attestation model SHA256 mismatch with frozen authority."
        )

    if expected_decision_time_utc <= RESEARCH_FREEZE_BOUNDARY_UTC:
        raise TrueForwardAcquisitionNotAuthorizedError(
            f"Decision time {expected_decision_time_utc} does not exceed research freeze boundary {RESEARCH_FREEZE_BOUNDARY_UTC}"
        )

    if expected_decision_time_utc < GATE_15A_ACTIVATION_UTC:
        raise TrueForwardAcquisitionNotAuthorizedError(
            f"Decision time {expected_decision_time_utc} precedes Gate 15A activation {GATE_15A_ACTIVATION_UTC}"
        )

    return att


@dataclass(frozen=True)
class ForwardMarketSnapshot:
    """
    Immutable container packaging acquired multi-timeframe DataFrames
    along with canonical snapshot ID, attestation, decision timestamp,
    verified authority object, and optional diagnostic D1 frame.
    """
    canonical_instrument: str
    broker_symbol: str
    market_data: Mapping[str, pd.DataFrame]
    decision_time_utc: str
    source_snapshot_id: str
    attestation: ForwardAcquisitionAttestation
    is_synthetic: bool = False
    authority: VerifiedForwardAcquisitionAuthority | None = None
    native_d1_diagnostic: pd.DataFrame | None = None


def _to_utc_iso(ts_input: Any) -> str:
    ts = pd.Timestamp(ts_input)
    if isinstance(ts, pd.Timestamp) and ts is not pd.NaT:
        utc_ts = ts.tz_convert("UTC") if ts.tz is not None else ts.tz_localize("UTC")
        if isinstance(utc_ts, pd.Timestamp):
            s = str(utc_ts.isoformat())
            if s.endswith("+00:00"):
                s = s[:-6] + "Z"
            return s
    raise MalformedBarDataError("Encountered NaT or invalid timestamp in bar data")


def _to_utc_timestamp(ts_input: Any) -> pd.Timestamp:
    ts = pd.Timestamp(ts_input)
    if isinstance(ts, pd.Timestamp) and ts is not pd.NaT:
        utc_ts = ts.tz_convert("UTC") if ts.tz is not None else ts.tz_localize("UTC")
        if isinstance(utc_ts, pd.Timestamp):
            return utc_ts
    raise MalformedBarDataError("Encountered NaT or invalid timestamp in bar data")


# =============================================================================
# Canonical Snapshot Fingerprint Computation
# =============================================================================

def compute_canonical_snapshot_id(market_data: Mapping[str, pd.DataFrame]) -> str:
    """
    Compute a deterministic 64-character lowercase hex SHA256 digest
    representing the exact normalized finite numeric values in market_data.
    
    Eliminates arbitrary decimal rounding by using IEEE-754 exact float.hex()
    and integer tick_volume representation.
    
    Ordered deterministically by:
    - schema_version header: [version:2.0.0]
    - sorted timeframe keys
    - sorted columns: ("time", "open", "high", "low", "close", "tick_volume")
    - chronological row order with canonical ISO-8601 UTC timestamp
    """
    blocks: list[str] = ["[version:2.0.0]"]
    for tf in sorted(market_data.keys()):
        df = market_data[tf]
        rows: list[str] = []
        for _, row in df.iterrows():
            ts_str = _to_utc_iso(row["time"])
            o = float(row["open"]).hex()
            h = float(row["high"]).hex()
            l = float(row["low"]).hex()
            c = float(row["close"]).hex()
            vol = int(round(float(row["tick_volume"])))
            rows.append(f"{ts_str}:{o}:{h}:{l}:{c}:{vol}")
        blocks.append(f"[{tf}]\n" + "\n".join(rows))
    
    full_content = "\n---\n".join(blocks)
    return hashlib.sha256(full_content.encode("utf-8")).hexdigest()


# =============================================================================
# Forward Acquisition Adapter
# =============================================================================

class MT5ReadOnlyForwardAcquisitionAdapter:
    """
    Production-safe forward acquisition authority.
    
    Responsibilities:
    - Resolves and validates broker symbol against Gate 13 contract.
    - Acquires completed closed intraday bars (start_pos >= 1) for M5, M15, M30, H1, H4.
    - Preserves Gate 13 authoritative D1 reconstruction: native broker D1 is NOT
      part of the authoritative source snapshot by default.
    - Enforces UTC timestamp conversion.
    - Verifies temporal causality and no-lookahead invariants.
    - Generates deterministic source snapshot fingerprint using exact numeric representation.
    - Produces ForwardAcquisitionAttestation, VerifiedForwardAcquisitionAuthority,
      and ForwardMarketSnapshot.
    """

    REQUIRED_TIMEFRAMES: tuple[str, ...] = ("M5", "M15", "M30", "H1", "H4")
    DEFAULT_MIN_BARS: dict[str, int] = {
        "M5": 200,
        "M15": 200,
        "M30": 200,
        "H1": 5000,
        "H4": 200,
        "D1": 200,
    }

    def __init__(
        self,
        api: Any,
        *,
        canonical_symbol: str = CANONICAL_SYMBOL,
        min_history_bars: dict[str, int] | None = None,
        is_synthetic: bool = False,
        include_native_d1: bool = False,
    ) -> None:
        self._facade = MT5ReadOnlyCapabilityFacade(api)
        self._canonical_symbol = str(normalize_supported_symbol(canonical_symbol))
        self._min_history_bars = dict(self.DEFAULT_MIN_BARS)
        if min_history_bars is not None:
            self._min_history_bars.update(min_history_bars)
        self._is_synthetic = bool(is_synthetic)
        self._include_native_d1 = bool(include_native_d1)

    @property
    def is_synthetic(self) -> bool:
        return self._is_synthetic

    @property
    def facade(self) -> MT5ReadOnlyCapabilityFacade:
        return self._facade

    def resolve_broker_symbol(self) -> str:
        """Resolve broker symbol using CanonicalGoldResolver or explicit match."""
        try:
            resolver = CanonicalGoldResolver(self._facade)
            resolution = resolver.resolve()
            raw_symbol = resolution.broker_symbol
        except Exception:
            # Fallback to direct symbol probe if resolver fails or in test environments
            info = self._facade.symbol_info(self._canonical_symbol)
            if info is not None:
                raw_symbol = self._canonical_symbol
            else:
                info_m = self._facade.symbol_info("XAUUSDm")
                if info_m is not None:
                    raw_symbol = "XAUUSDm"
                else:
                    raise SymbolResolutionError(
                        f"Could not resolve supported broker symbol for {self._canonical_symbol}"
                    )

        norm = str(normalize_supported_symbol(raw_symbol))
        if norm not in SUPPORTED_SYMBOLS:
            raise UnsupportedSymbolError(
                f"Resolved symbol {norm!r} is not in Gate 13 supported symbols: {SUPPORTED_SYMBOLS}"
            )
        return raw_symbol

    def _tf_enum(self, tf_str: str) -> int:
        attr_name = f"TIMEFRAME_{tf_str}"
        return int(getattr(self._facade, attr_name))

    def _convert_rates_to_frame(
        self, rates: np.ndarray, timeframe: str
    ) -> pd.DataFrame:
        """Convert MT5 numpy structured array to validated UTC DataFrame."""
        if rates is None or len(rates) == 0:
            raise InsufficientForwardHistoryError(f"No rates returned for timeframe {timeframe}")

        # Extract columns
        data: dict[str, Any] = {}
        for col in ("time", "open", "high", "low", "close", "tick_volume"):
            if col in rates.dtype.names:  # type: ignore
                data[col] = rates[col]
            else:
                raise MalformedBarDataError(f"Missing required field {col!r} in rates for {timeframe}")

        df = pd.DataFrame(data)

        # Critical: integer timestamps are Unix UTC seconds
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)

        # Validate numeric OHLCV
        for col in ("open", "high", "low", "close", "tick_volume"):
            df[col] = pd.to_numeric(df[col], errors="coerce")

        if bool(df[["open", "high", "low", "close", "tick_volume"]].isna().to_numpy().any()):
            raise MalformedBarDataError(f"Non-numeric or NaN values in OHLCV for {timeframe}")

        # Check geometry
        lows = df["low"].to_numpy()
        highs = df["high"].to_numpy()
        opens = df["open"].to_numpy()
        closes = df["close"].to_numpy()

        if (lows <= 0).any() or (highs < lows).any():
            raise MalformedBarDataError(f"Invalid OHLC geometry in {timeframe}: low <= 0 or high < low")
        if (highs < opens).any() or (highs < closes).any():
            raise MalformedBarDataError(f"Invalid OHLC geometry in {timeframe}: high < open or high < close")
        if (lows > opens).any() or (lows > closes).any():
            raise MalformedBarDataError(f"Invalid OHLC geometry in {timeframe}: low > open or low > close")

        # Chronological sort and monotonicity check
        df = df.sort_values(by="time").reset_index(drop=True)
        if not df["time"].is_monotonic_increasing:
            raise MalformedBarDataError(f"Timestamps are not strictly monotonic in {timeframe}")
        if df["time"].duplicated().any():
            raise MalformedBarDataError(f"Duplicate timestamps detected in {timeframe}")

        min_bars = self._min_history_bars.get(timeframe, 50)
        if len(df) < min_bars:
            raise InsufficientForwardHistoryError(
                f"Insufficient bars for {timeframe}: {len(df)} < {min_bars}"
            )

        return df

    def acquire_snapshot(
        self,
        *,
        acquisition_time_utc: str | None = None,
        enforce_forward_boundaries: bool = True,
    ) -> ForwardMarketSnapshot:
        """
        Acquire completed multi-timeframe market snapshot from MT5.
        
        Preserves Gate 13 D1 authority: acquires authoritative intraday histories
        (M5, M15, M30, H1, H4) so PortableFeaturePipeline performs canonical 00:00 UTC
        reconstruction. Native D1 is excluded from market_data by default.
        
        Args:
            acquisition_time_utc: Optional ISO-8601 UTC timestamp override for testing.
            enforce_forward_boundaries: If True, validates decision_time against
                                        frozen research freeze and activation boundaries.
        """
        broker_symbol = self.resolve_broker_symbol()

        if acquisition_time_utc is not None:
            norm_acq_time = validate_iso8601_utc(acquisition_time_utc)
        else:
            now = pd.Timestamp.now(tz="UTC").isoformat()
            norm_acq_time = validate_iso8601_utc(now)

        # Gate 15B authoritative acquisition spans intraday timeframes
        timeframes_to_fetch = list(self.REQUIRED_TIMEFRAMES)

        market_data: dict[str, pd.DataFrame] = {}
        bar_counts: dict[str, int] = {}
        earliest_opens: dict[str, str] = {}
        latest_opens: dict[str, str] = {}
        latest_availables: dict[str, str] = {}

        for tf in timeframes_to_fetch:
            tf_enum = self._tf_enum(tf)
            req_bars = self._min_history_bars.get(tf, 200)
            # Fetch strictly starting at position 1 (excluding forming candle)
            raw_rates = self._facade.copy_rates_from_pos(broker_symbol, tf_enum, 1, req_bars)
            if raw_rates is None:
                raise MT5ConnectionUnavailableError(f"Failed to fetch rates for {broker_symbol} on {tf}")

            df = self._convert_rates_to_frame(raw_rates, tf)
            market_data[tf] = df
            bar_counts[tf] = len(df)

            first_open = _to_utc_iso(df["time"].iloc[0])
            last_open_ts = _to_utc_timestamp(df["time"].iloc[-1])
            last_open = _to_utc_iso(last_open_ts)
            last_avail_ts = last_open_ts + pd.Timedelta(minutes=TIMEFRAME_MINUTES[tf])
            last_avail = _to_utc_iso(last_avail_ts)

            earliest_opens[tf] = first_open
            latest_opens[tf] = last_open
            latest_availables[tf] = last_avail

        # Acquire native D1 strictly as optional diagnostic metadata if requested
        native_d1_diagnostic: pd.DataFrame | None = None
        if self._include_native_d1:
            raw_d1 = self._facade.copy_rates_from_pos(
                broker_symbol, self._tf_enum("D1"), 1, self._min_history_bars.get("D1", 200)
            )
            if raw_d1 is not None:
                native_d1_diagnostic = self._convert_rates_to_frame(raw_d1, "D1")

        # The authoritative decision time is governed by the latest completed M5 candle close
        latest_m5_open = _to_utc_timestamp(market_data["M5"]["time"].iloc[-1])
        decision_time_ts = latest_m5_open + pd.Timedelta(minutes=5)
        decision_time_utc = validate_iso8601_utc(_to_utc_iso(decision_time_ts))

        # Verify temporal causality: no higher timeframe bar may have available_time > decision_time
        for tf in timeframes_to_fetch:
            tf_avail_ts = _to_utc_timestamp(latest_availables[tf])
            if tf_avail_ts > decision_time_ts:
                raise MalformedBarDataError(
                    f"Higher timeframe {tf} available_time ({latest_availables[tf]}) "
                    f"exceeds decision_time ({decision_time_utc}). Lookahead detected!"
                )

        # Enforce frozen boundaries if requested
        if enforce_forward_boundaries:
            if decision_time_utc <= RESEARCH_FREEZE_BOUNDARY_UTC:
                raise HistoricalFreezeBoundaryViolationError(
                    f"Decision time {decision_time_utc} is within historical research freeze "
                    f"boundary ({RESEARCH_FREEZE_BOUNDARY_UTC})."
                )
            if decision_time_utc < GATE_15A_ACTIVATION_UTC:
                raise PreActivationForwardError(
                    f"Decision time {decision_time_utc} precedes Gate 15A activation "
                    f"authority ({GATE_15A_ACTIVATION_UTC})."
                )

        # Compute deterministic snapshot fingerprint using exact numeric representation
        snapshot_id = compute_canonical_snapshot_id(market_data)

        # Build attestation
        attestation_payload = {
            "schema_version": ACQUISITION_SCHEMA_VERSION,
            "acquisition_authority": ACQUISITION_AUTHORITY_ID,
            "canonical_instrument": self._canonical_symbol,
            "resolved_broker_symbol": broker_symbol,
            "acquisition_time_utc": norm_acq_time,
            "decision_time_utc": decision_time_utc,
            "timeframe_bar_counts": bar_counts,
            "earliest_bar_open_utc": earliest_opens,
            "latest_bar_open_utc": latest_opens,
            "latest_bar_available_utc": latest_availables,
            "research_freeze_boundary_utc": RESEARCH_FREEZE_BOUNDARY_UTC,
            "gate_15a_activation_utc": GATE_15A_ACTIVATION_UTC,
            "source_snapshot_id": snapshot_id,
            "feature_columns_sha256": EXPECTED_FEATURE_COLUMNS_SHA256,
            "model_sha256": FROZEN_MODEL_SHA256,
            "capability_manifest": list(sorted(MT5ReadOnlyCapabilityFacade.ALLOWED_METHODS)),
            "is_synthetic": self._is_synthetic,
        }
        encoded_att = json.dumps(attestation_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        attestation_sha256 = hashlib.sha256(encoded_att).hexdigest()

        attestation = ForwardAcquisitionAttestation(
            schema_version=ACQUISITION_SCHEMA_VERSION,
            acquisition_authority=ACQUISITION_AUTHORITY_ID,
            canonical_instrument=self._canonical_symbol,
            resolved_broker_symbol=broker_symbol,
            acquisition_time_utc=norm_acq_time,
            decision_time_utc=decision_time_utc,
            timeframe_bar_counts=bar_counts,
            earliest_bar_open_utc=earliest_opens,
            latest_bar_open_utc=latest_opens,
            latest_bar_available_utc=latest_availables,
            research_freeze_boundary_utc=RESEARCH_FREEZE_BOUNDARY_UTC,
            gate_15a_activation_utc=GATE_15A_ACTIVATION_UTC,
            source_snapshot_id=snapshot_id,
            feature_columns_sha256=EXPECTED_FEATURE_COLUMNS_SHA256,
            model_sha256=FROZEN_MODEL_SHA256,
            capability_manifest=tuple(sorted(MT5ReadOnlyCapabilityFacade.ALLOWED_METHODS)),
            is_synthetic=self._is_synthetic,
            attestation_sha256=attestation_sha256,
        )

        # Issue verified acquisition authority ONLY for genuine, non-synthetic acquisition
        authority: VerifiedForwardAcquisitionAuthority | None = None
        if not self._is_synthetic:
            authority = VerifiedForwardAcquisitionAuthority(
                _PRIVATE_FORWARD_AUTHORITY_TOKEN,
                attestation,
                is_synthetic=False,
            )

        return ForwardMarketSnapshot(
            canonical_instrument=self._canonical_symbol,
            broker_symbol=broker_symbol,
            market_data=market_data,
            decision_time_utc=decision_time_utc,
            source_snapshot_id=snapshot_id,
            attestation=attestation,
            is_synthetic=self._is_synthetic,
            authority=authority,
            native_d1_diagnostic=native_d1_diagnostic,
        )
