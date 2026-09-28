"""
===============================================================================
Module      : mt5_read_only_forward_acquisition_adapter.py
Project     : PulseViper XAU AI
Purpose     : Read-Only Forward Market Data Acquisition Authority (Gate 15B-A)
===============================================================================

Production-safe, provably isolated, read-only MetaTrader 5 market-data acquisition
adapter. Captures completed multi-timeframe OHLCV snapshots, normalizes the broker
clock to true UTC through an explicit fail-closed time-basis authority, computes a
deterministic source snapshot fingerprint, and generates tamper-evident acquisition
attestations for Gate 13 feature generation and Gate 15A shadow observation.

Safety guarantees (NON-NEGOTIABLE):
- ZERO broker write methods and ZERO execution/risk dependencies.
- Capability facade exposes only approved read-only market-data methods.
- start_pos >= 1 is enforced; forming/incomplete candles are never ingested.
- Genuine acquisition must prove exactly one supported MT5 timestamp basis:
    * UNIX_UTC
    * NY_CLOSE_SERVER_WALL_CLOCK (UTC+2/UTC+3, DST-aware per historical row)
- No fixed current broker offset is applied to historical data.
- Ambiguous or unprovable timestamp semantics fail closed.
- Gate 13 D1 reconstruction remains canonical from intraday data.
- Supports only frozen supported symbols XAUUSD and XAUUSDm.
- Synthetic/mock data cannot escalate to TRUE_FORWARD authority.
- live_authorized = False; execution_authorized = False.
"""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import hashlib
import importlib
import json
from pathlib import Path
import sys
import time
from typing import Any, Callable, Mapping, Protocol, cast
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

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
TrueForwardAcquisitionNotAuthorizedError: Any = (
    _observer.TrueForwardAcquisitionNotAuthorizedError
)

CanonicalGoldResolver: Any = _adapter_mod.CanonicalGoldResolver

ACQUISITION_SCHEMA_VERSION: str = "2.1.0"
ACQUISITION_AUTHORITY_ID: str = "MT5ReadOnlyForwardAcquisitionAdapter:2.1.0"

_PRIVATE_FORWARD_AUTHORITY_TOKEN: object = object()

TIMEFRAME_MINUTES: dict[str, int] = {
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}

DEFAULT_TIMEFRAME_ENUMS: dict[str, int] = {
    "TIMEFRAME_M5": 5,
    "TIMEFRAME_M15": 15,
    "TIMEFRAME_M30": 30,
    "TIMEFRAME_H1": 16385,
    "TIMEFRAME_H4": 16388,
    "TIMEFRAME_D1": 16408,
}

TIME_BASIS_AUTO: str = "AUTO"
TIME_BASIS_UNIX_UTC: str = "UNIX_UTC"
TIME_BASIS_NY_CLOSE_SERVER: str = "NY_CLOSE_SERVER_WALL_CLOCK"

SUPPORTED_TIME_BASIS_MODES: frozenset[str] = frozenset(
    {
        TIME_BASIS_AUTO,
        TIME_BASIS_UNIX_UTC,
        TIME_BASIS_NY_CLOSE_SERVER,
    }
)

DEFAULT_MAX_TICK_AGE_SECONDS: int = 180
DEFAULT_MAX_FUTURE_TICK_SKEW_SECONDS: int = 5

NEW_YORK_CLOSE_DISTANCE_SECONDS: int = 7 * 60 * 60
NY_CLOSE_STANDARD_OFFSET_SECONDS: int = 2 * 60 * 60
NY_CLOSE_DST_OFFSET_SECONDS: int = 3 * 60 * 60

_NEW_YORK: ZoneInfo = ZoneInfo("America/New_York")


# =============================================================================
# Fail-Closed Exception Taxonomy
# =============================================================================

class ForwardAcquisitionError(Exception):
    """Base exception for all forward acquisition errors (fail closed)."""


class MT5ConnectionUnavailableError(ForwardAcquisitionError):
    """Raised when MT5 API/session market data is unavailable."""


class IncompleteCandleAccessAttemptError(ForwardAcquisitionError):
    """Raised when start_pos < 1 would permit forming-candle access."""


class SymbolResolutionError(ForwardAcquisitionError):
    """Raised when no frozen supported broker symbol can be resolved."""


class UnsupportedSymbolError(ForwardAcquisitionError):
    """Raised when resolved symbol violates the Gate 13 symbol contract."""


class InsufficientForwardHistoryError(ForwardAcquisitionError):
    """Raised when broker returns insufficient completed history."""


class HistoricalFreezeBoundaryViolationError(ForwardAcquisitionError):
    """Raised when decision time does not exceed research freeze boundary."""


class PreActivationForwardError(ForwardAcquisitionError):
    """Raised when true-forward timestamp precedes Gate 15A activation."""


class MalformedBarDataError(ForwardAcquisitionError):
    """Raised when acquired bar data violates schema/geometry/time causality."""


class AttestationIntegrityError(ForwardAcquisitionError):
    """Raised when attestation integrity cannot be established."""


class TimestampBasisResolutionError(ForwardAcquisitionError):
    """Raised when raw MT5 timestamp semantics are ambiguous or unprovable."""


# =============================================================================
# Read-Only Capability Boundary
# =============================================================================

class ReadOnlyMT5Protocol(Protocol):
    def symbols_get(self) -> Any: ...
    def symbol_info(self, symbol: str) -> Any: ...
    def symbol_info_tick(self, symbol: str) -> Any: ...
    def copy_rates_from_pos(
        self,
        symbol: str,
        timeframe: int,
        start_pos: int,
        count: int,
    ) -> np.ndarray | None: ...


class MT5ReadOnlyCapabilityFacade:
    """Capability-restricting facade for Gate 15B read-only broker access."""

    ALLOWED_METHODS: frozenset[str] = frozenset(
        {
            "symbols_get",
            "symbol_info",
            "symbol_info_tick",
            "copy_rates_from_pos",
        }
    )

    ALLOWED_TIMEFRAME_ATTRS: frozenset[str] = frozenset(
        {
            "TIMEFRAME_M5",
            "TIMEFRAME_M15",
            "TIMEFRAME_M30",
            "TIMEFRAME_H1",
            "TIMEFRAME_H4",
            "TIMEFRAME_D1",
        }
    )

    FORBIDDEN_MUTATING_METHODS: frozenset[str] = frozenset(
        {
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
        }
    )

    def __init__(self, api: Any) -> None:
        if api is None:
            raise MT5ConnectionUnavailableError(
                "MT5 API instance must not be None"
            )

        self._api = api

    def symbols_get(self) -> Any:
        return self._api.symbols_get()

    def symbol_info(self, symbol: str) -> Any:
        return self._api.symbol_info(symbol)

    def symbol_info_tick(self, symbol: str) -> Any:
        return self._api.symbol_info_tick(symbol)

    def copy_rates_from_pos(
        self,
        symbol: str,
        timeframe: int,
        start_pos: int,
        count: int,
    ) -> np.ndarray | None:
        if start_pos < 1:
            raise IncompleteCandleAccessAttemptError(
                f"Gate 15B forbids start_pos < 1 (requested: {start_pos}). "
                "Position 0 is the incomplete/forming bar."
            )

        return self._api.copy_rates_from_pos(
            symbol,
            timeframe,
            start_pos,
            count,
        )

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
            f"Method or attribute {name!r} is not permitted on "
            "MT5ReadOnlyCapabilityFacade."
        )


# =============================================================================
# Time-Basis Authority
# =============================================================================

@dataclass(frozen=True)
class TimeBasisResolution:
    policy: str
    reference_tick_raw: int | None
    reference_tick_utc: str | None
    reference_offset_seconds: int | None
    reference_tick_age_seconds: float | None


def _timestamp_from_epoch_seconds(
    epoch_seconds: int | float,
) -> pd.Timestamp:
    py_dt = dt.datetime.fromtimestamp(
        float(epoch_seconds),
        tz=dt.timezone.utc,
    )

    ts = pd.Timestamp(py_dt)

    if ts is pd.NaT:
        raise MalformedBarDataError(
            "Encountered NaT while converting epoch seconds"
        )

    return cast(pd.Timestamp, ts)


def _to_utc_iso(
    ts_input: Any,
) -> str:
    ts = pd.Timestamp(ts_input)

    if ts is pd.NaT:
        raise MalformedBarDataError(
            "Encountered NaT or invalid timestamp"
        )

    utc_ts = (
        ts.tz_convert("UTC")
        if ts.tz is not None
        else ts.tz_localize("UTC")
    )

    utc_ts = cast(pd.Timestamp, utc_ts)

    value = utc_ts.isoformat()

    if value.endswith("+00:00"):
        return value[:-6] + "Z"

    return value


def _to_utc_timestamp(
    ts_input: Any,
) -> pd.Timestamp:
    ts = pd.Timestamp(ts_input)

    if ts is pd.NaT:
        raise MalformedBarDataError(
            "Encountered NaT or invalid timestamp"
        )

    utc_ts = (
        ts.tz_convert("UTC")
        if ts.tz is not None
        else ts.tz_localize("UTC")
    )

    if utc_ts is pd.NaT:
        raise MalformedBarDataError(
            "Encountered NaT after UTC normalization"
        )

    return cast(pd.Timestamp, utc_ts)


def _new_york_utc_offset_seconds(
    true_utc: pd.Timestamp,
) -> int:
    utc_py = true_utc.to_pydatetime()

    if utc_py.tzinfo is None:
        utc_py = utc_py.replace(
            tzinfo=dt.timezone.utc
        )

    ny_time = utc_py.astimezone(
        _NEW_YORK
    )

    offset = ny_time.utcoffset()

    if offset is None:
        raise TimestampBasisResolutionError(
            "NEW_YORK_UTC_OFFSET_UNAVAILABLE"
        )

    return int(
        offset.total_seconds()
    )


def _expected_ny_close_server_offset_seconds(
    true_utc: pd.Timestamp,
) -> int:
    ny_offset_seconds = (
        _new_york_utc_offset_seconds(
            true_utc
        )
    )

    server_offset_seconds = (
        ny_offset_seconds
        + NEW_YORK_CLOSE_DISTANCE_SECONDS
    )

    if server_offset_seconds not in {
        NY_CLOSE_STANDARD_OFFSET_SECONDS,
        NY_CLOSE_DST_OFFSET_SECONDS,
    }:
        raise TimestampBasisResolutionError(
            "UNEXPECTED_NY_CLOSE_SERVER_OFFSET:"
            f"{server_offset_seconds}"
        )

    return server_offset_seconds


def normalize_ny_close_server_epoch(
    raw_server_epoch: int,
) -> tuple[pd.Timestamp, int]:
    """
    Convert a broker-server wall-clock timestamp encoded as epoch-like seconds
    into true UTC.

    Both supported server offsets are evaluated independently for each row.
    Exactly one candidate must satisfy the New-York-close convention.
    """

    valid_candidates: list[
        tuple[pd.Timestamp, int]
    ] = []

    for candidate_offset in (
        NY_CLOSE_STANDARD_OFFSET_SECONDS,
        NY_CLOSE_DST_OFFSET_SECONDS,
    ):
        candidate_utc = (
            _timestamp_from_epoch_seconds(
                int(raw_server_epoch)
                - candidate_offset
            )
        )

        expected_offset = (
            _expected_ny_close_server_offset_seconds(
                candidate_utc
            )
        )

        if expected_offset == candidate_offset:
            valid_candidates.append(
                (
                    candidate_utc,
                    candidate_offset,
                )
            )

    if len(valid_candidates) != 1:
        raise TimestampBasisResolutionError(
            "NY_CLOSE_SERVER_TIMESTAMP_"
            "AMBIGUOUS_OR_INVALID:"
            f"raw={raw_server_epoch}:"
            f"valid_candidates={len(valid_candidates)}"
        )

    return valid_candidates[0]


def _validate_tick_age(
    normalized_tick_utc: pd.Timestamp,
    *,
    now_epoch: float,
    max_tick_age_seconds: int,
    max_future_tick_skew_seconds: int,
) -> float:
    tick_epoch = normalized_tick_utc.timestamp()

    age_seconds = (
        float(now_epoch)
        - float(tick_epoch)
    )

    if age_seconds > float(
        max_tick_age_seconds
    ):
        raise TimestampBasisResolutionError(
            "NORMALIZED_TICK_IS_STALE:"
            f"{age_seconds:.6f}"
        )

    if age_seconds < -float(
        max_future_tick_skew_seconds
    ):
        raise TimestampBasisResolutionError(
            "NORMALIZED_TICK_IS_FUTURE:"
            f"{age_seconds:.6f}"
        )

    return age_seconds


def detect_timestamp_basis_from_tick(
    *,
    raw_tick_epoch: int,
    now_epoch: float,
    max_tick_age_seconds: int = (
        DEFAULT_MAX_TICK_AGE_SECONDS
    ),
    max_future_tick_skew_seconds: int = (
        DEFAULT_MAX_FUTURE_TICK_SKEW_SECONDS
    ),
) -> TimeBasisResolution:
    """
    Detect the genuine MT5 timestamp basis from one current tick.

    Exactly one supported policy must produce a fresh, non-future true-UTC tick.
    """

    candidates: list[
        TimeBasisResolution
    ] = []

    unix_utc = (
        _timestamp_from_epoch_seconds(
            raw_tick_epoch
        )
    )

    try:
        unix_age = _validate_tick_age(
            unix_utc,
            now_epoch=now_epoch,
            max_tick_age_seconds=(
                max_tick_age_seconds
            ),
            max_future_tick_skew_seconds=(
                max_future_tick_skew_seconds
            ),
        )

        candidates.append(
            TimeBasisResolution(
                policy=TIME_BASIS_UNIX_UTC,
                reference_tick_raw=(
                    raw_tick_epoch
                ),
                reference_tick_utc=(
                    _to_utc_iso(
                        unix_utc
                    )
                ),
                reference_offset_seconds=0,
                reference_tick_age_seconds=(
                    float(unix_age)
                ),
            )
        )

    except TimestampBasisResolutionError:
        pass

    try:
        (
            ny_close_utc,
            ny_offset_seconds,
        ) = normalize_ny_close_server_epoch(
            raw_tick_epoch
        )

        ny_age = _validate_tick_age(
            ny_close_utc,
            now_epoch=now_epoch,
            max_tick_age_seconds=(
                max_tick_age_seconds
            ),
            max_future_tick_skew_seconds=(
                max_future_tick_skew_seconds
            ),
        )

        candidates.append(
            TimeBasisResolution(
                policy=(
                    TIME_BASIS_NY_CLOSE_SERVER
                ),
                reference_tick_raw=(
                    raw_tick_epoch
                ),
                reference_tick_utc=(
                    _to_utc_iso(
                        ny_close_utc
                    )
                ),
                reference_offset_seconds=(
                    ny_offset_seconds
                ),
                reference_tick_age_seconds=(
                    float(ny_age)
                ),
            )
        )

    except TimestampBasisResolutionError:
        pass

    if len(candidates) != 1:
        raise TimestampBasisResolutionError(
            "TIMESTAMP_BASIS_NOT_UNIQUELY_PROVEN:"
            f"raw_tick={raw_tick_epoch}:"
            f"candidate_count={len(candidates)}"
        )

    return candidates[0]


# =============================================================================
# Attestation / Snapshot Models
# =============================================================================

@dataclass(frozen=True)
class ForwardAcquisitionAttestation:
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
    time_basis_policy: str
    time_basis_reference_tick_raw: int | None
    time_basis_reference_tick_utc: str | None
    time_basis_reference_offset_seconds: int | None
    time_basis_reference_tick_age_seconds: float | None

    def to_canonical_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "schema_version": (
                self.schema_version
            ),
            "acquisition_authority": (
                self.acquisition_authority
            ),
            "canonical_instrument": (
                self.canonical_instrument
            ),
            "resolved_broker_symbol": (
                self.resolved_broker_symbol
            ),
            "acquisition_time_utc": (
                self.acquisition_time_utc
            ),
            "decision_time_utc": (
                self.decision_time_utc
            ),
            "timeframe_bar_counts": (
                self.timeframe_bar_counts
            ),
            "earliest_bar_open_utc": (
                self.earliest_bar_open_utc
            ),
            "latest_bar_open_utc": (
                self.latest_bar_open_utc
            ),
            "latest_bar_available_utc": (
                self.latest_bar_available_utc
            ),
            "research_freeze_boundary_utc": (
                self.research_freeze_boundary_utc
            ),
            "gate_15a_activation_utc": (
                self.gate_15a_activation_utc
            ),
            "source_snapshot_id": (
                self.source_snapshot_id
            ),
            "feature_columns_sha256": (
                self.feature_columns_sha256
            ),
            "model_sha256": (
                self.model_sha256
            ),
            "capability_manifest": list(
                self.capability_manifest
            ),
            "is_synthetic": (
                self.is_synthetic
            ),
            "time_basis_policy": (
                self.time_basis_policy
            ),
            "time_basis_reference_tick_raw": (
                self.time_basis_reference_tick_raw
            ),
            "time_basis_reference_tick_utc": (
                self.time_basis_reference_tick_utc
            ),
            "time_basis_reference_offset_seconds": (
                self.time_basis_reference_offset_seconds
            ),
            "time_basis_reference_tick_age_seconds": (
                self.time_basis_reference_tick_age_seconds
            ),
        }

    def verify_integrity(
        self,
    ) -> bool:
        payload = json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        computed = hashlib.sha256(
            payload
        ).hexdigest()

        return (
            computed
            == self.attestation_sha256
        )


class VerifiedForwardAcquisitionAuthority:
    def __init__(
        self,
        token: object,
        attestation: ForwardAcquisitionAttestation,
        is_synthetic: bool,
    ) -> None:
        if (
            token
            is not
            _PRIVATE_FORWARD_AUTHORITY_TOKEN
        ):
            raise PermissionError(
                "VerifiedForwardAcquisitionAuthority cannot be instantiated "
                "outside the genuine MT5ReadOnlyForwardAcquisitionAdapter path."
            )

        self._token = token
        self._attestation = attestation
        self._is_synthetic = bool(
            is_synthetic
        )

    @property
    def attestation(
        self,
    ) -> ForwardAcquisitionAttestation:
        return self._attestation

    @property
    def is_synthetic(
        self,
    ) -> bool:
        return self._is_synthetic

    def is_valid_authority(
        self,
    ) -> bool:
        return bool(
            self._token
            is _PRIVATE_FORWARD_AUTHORITY_TOKEN
            and not self._is_synthetic
            and not self._attestation.is_synthetic
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

    if not isinstance(
        authority,
        VerifiedForwardAcquisitionAuthority,
    ):
        raise TrueForwardAcquisitionNotAuthorizedError(
            "TRUE_FORWARD_OBSERVATION requires genuine verified "
            "forward acquisition authority."
        )

    if (
        getattr(
            authority,
            "_token",
            None,
        )
        is not
        _PRIVATE_FORWARD_AUTHORITY_TOKEN
    ):
        raise TrueForwardAcquisitionNotAuthorizedError(
            "Invalid forward acquisition authority token."
        )

    if (
        authority.is_synthetic
        or authority.attestation.is_synthetic
    ):
        raise TrueForwardAcquisitionNotAuthorizedError(
            "Synthetic acquisition cannot authorize TRUE_FORWARD provenance."
        )

    attestation = (
        authority.attestation
    )

    if not attestation.verify_integrity():
        raise TrueForwardAcquisitionNotAuthorizedError(
            "Forward acquisition attestation integrity verification failed."
        )

    if (
        attestation.source_snapshot_id
        != expected_source_snapshot_id
    ):
        raise TrueForwardAcquisitionNotAuthorizedError(
            "Attestation source snapshot ID mismatch."
        )

    if (
        attestation.decision_time_utc
        != expected_decision_time_utc
    ):
        raise TrueForwardAcquisitionNotAuthorizedError(
            "Attestation decision time mismatch."
        )

    if (
        attestation.canonical_instrument
        != expected_canonical_instrument
    ):
        raise TrueForwardAcquisitionNotAuthorizedError(
            "Attestation canonical instrument mismatch."
        )

    if (
        attestation.feature_columns_sha256
        != expected_feature_columns_sha256
    ):
        raise TrueForwardAcquisitionNotAuthorizedError(
            "Attestation feature-column SHA mismatch."
        )

    if (
        attestation.model_sha256
        != expected_model_sha256
    ):
        raise TrueForwardAcquisitionNotAuthorizedError(
            "Attestation frozen-model SHA mismatch."
        )

    if (
        expected_decision_time_utc
        <= RESEARCH_FREEZE_BOUNDARY_UTC
    ):
        raise TrueForwardAcquisitionNotAuthorizedError(
            "Decision time does not exceed the frozen research boundary."
        )

    if (
        expected_decision_time_utc
        < GATE_15A_ACTIVATION_UTC
    ):
        raise TrueForwardAcquisitionNotAuthorizedError(
            "Decision time precedes Gate 15A activation."
        )

    if (
        attestation.time_basis_policy
        not in {
            TIME_BASIS_UNIX_UTC,
            TIME_BASIS_NY_CLOSE_SERVER,
        }
    ):
        raise TrueForwardAcquisitionNotAuthorizedError(
            "Attestation does not contain an approved resolved timestamp basis."
        )

    return attestation


@dataclass(frozen=True)
class ForwardMarketSnapshot:
    canonical_instrument: str
    broker_symbol: str
    market_data: Mapping[
        str,
        pd.DataFrame,
    ]
    decision_time_utc: str
    source_snapshot_id: str
    attestation: ForwardAcquisitionAttestation
    is_synthetic: bool = False
    authority: (
        VerifiedForwardAcquisitionAuthority
        | None
    ) = None
    native_d1_diagnostic: (
        pd.DataFrame
        | None
    ) = None


# =============================================================================
# Deterministic Snapshot Fingerprint
# =============================================================================

def compute_canonical_snapshot_id(
    market_data: Mapping[
        str,
        pd.DataFrame,
    ],
) -> str:
    blocks: list[str] = [
        "[version:2.1.0]"
    ]

    for timeframe in sorted(
        market_data.keys()
    ):
        frame = market_data[
            timeframe
        ]

        rows: list[str] = []

        for _, row in frame.iterrows():
            timestamp = _to_utc_iso(
                row["time"]
            )

            row_text = (
                f"{timestamp}:"
                f"{float(row['open']).hex()}:"
                f"{float(row['high']).hex()}:"
                f"{float(row['low']).hex()}:"
                f"{float(row['close']).hex()}:"
                f"{int(round(float(row['tick_volume'])))}"
            )

            rows.append(
                row_text
            )

        blocks.append(
            f"[{timeframe}]\n"
            + "\n".join(
                rows
            )
        )

    full_content = "\n---\n".join(
        blocks
    )

    return hashlib.sha256(
        full_content.encode(
            "utf-8"
        )
    ).hexdigest()


# =============================================================================
# Forward Acquisition Adapter
# =============================================================================

class MT5ReadOnlyForwardAcquisitionAdapter:
    REQUIRED_TIMEFRAMES: tuple[
        str,
        ...,
    ] = (
        "M5",
        "M15",
        "M30",
        "H1",
        "H4",
    )

    DEFAULT_MIN_BARS: dict[
        str,
        int,
    ] = {
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
        canonical_symbol: str = (
            CANONICAL_SYMBOL
        ),
        min_history_bars: (
            dict[str, int]
            | None
        ) = None,
        is_synthetic: bool = False,
        include_native_d1: bool = False,
        timestamp_basis: str = (
            TIME_BASIS_AUTO
        ),
        now_provider: Callable[
            [],
            float,
        ] = time.time,
        max_tick_age_seconds: int = (
            DEFAULT_MAX_TICK_AGE_SECONDS
        ),
        max_future_tick_skew_seconds: int = (
            DEFAULT_MAX_FUTURE_TICK_SKEW_SECONDS
        ),
    ) -> None:

        self._facade = (
            api
            if isinstance(
                api,
                MT5ReadOnlyCapabilityFacade,
            )
            else MT5ReadOnlyCapabilityFacade(
                api
            )
        )

        self._canonical_symbol = str(
            normalize_supported_symbol(
                canonical_symbol
            )
        )

        self._min_history_bars = dict(
            self.DEFAULT_MIN_BARS
        )

        if min_history_bars is not None:
            self._min_history_bars.update(
                min_history_bars
            )

        self._is_synthetic = bool(
            is_synthetic
        )

        self._include_native_d1 = bool(
            include_native_d1
        )

        timestamp_basis = str(
            timestamp_basis
        ).upper()

        if (
            timestamp_basis
            not in
            SUPPORTED_TIME_BASIS_MODES
        ):
            raise ValueError(
                "UNSUPPORTED_TIMESTAMP_BASIS:"
                f"{timestamp_basis}"
            )

        self._timestamp_basis = (
            timestamp_basis
        )

        self._now_provider = (
            now_provider
        )

        if (
            max_tick_age_seconds
            <= 0
        ):
            raise ValueError(
                "MAX_TICK_AGE_SECONDS_MUST_BE_POSITIVE"
            )

        if (
            max_future_tick_skew_seconds
            < 0
        ):
            raise ValueError(
                "MAX_FUTURE_TICK_SKEW_SECONDS_MUST_BE_NON_NEGATIVE"
            )

        self._max_tick_age_seconds = int(
            max_tick_age_seconds
        )

        self._max_future_tick_skew_seconds = int(
            max_future_tick_skew_seconds
        )

    @property
    def is_synthetic(
        self,
    ) -> bool:
        return self._is_synthetic

    @property
    def facade(
        self,
    ) -> MT5ReadOnlyCapabilityFacade:
        return self._facade

    @property
    def timestamp_basis(
        self,
    ) -> str:
        return self._timestamp_basis

    def resolve_broker_symbol(
        self,
    ) -> str:
        try:
            resolver = CanonicalGoldResolver(
                self._facade
            )

            resolution = (
                resolver.resolve()
            )

            raw_symbol = (
                resolution.broker_symbol
            )

        except Exception:
            symbol_info = (
                self._facade.symbol_info(
                    self._canonical_symbol
                )
            )

            if symbol_info is not None:
                raw_symbol = (
                    self._canonical_symbol
                )

            else:
                symbol_info_m = (
                    self._facade.symbol_info(
                        "XAUUSDm"
                    )
                )

                if symbol_info_m is not None:
                    raw_symbol = (
                        "XAUUSDm"
                    )

                else:
                    raise SymbolResolutionError(
                        "Could not resolve supported broker symbol "
                        f"for {self._canonical_symbol}"
                    )

        normalized_symbol = str(
            normalize_supported_symbol(
                raw_symbol
            )
        )

        if (
            normalized_symbol
            not in
            SUPPORTED_SYMBOLS
        ):
            raise UnsupportedSymbolError(
                f"Resolved symbol {normalized_symbol!r} "
                "is outside frozen supported symbols."
            )

        return raw_symbol

    def _tf_enum(
        self,
        timeframe: str,
    ) -> int:
        return int(
            getattr(
                self._facade,
                f"TIMEFRAME_{timeframe}",
            )
        )

    def _resolve_time_basis(
        self,
        broker_symbol: str,
    ) -> TimeBasisResolution:

        if self._is_synthetic:
            if (
                self._timestamp_basis
                == TIME_BASIS_AUTO
            ):
                policy = (
                    TIME_BASIS_UNIX_UTC
                )
            else:
                policy = (
                    self._timestamp_basis
                )

            return TimeBasisResolution(
                policy=policy,
                reference_tick_raw=None,
                reference_tick_utc=None,
                reference_offset_seconds=None,
                reference_tick_age_seconds=None,
            )

        tick = (
            self._facade.symbol_info_tick(
                broker_symbol
            )
        )

        if tick is None:
            raise TimestampBasisResolutionError(
                "CURRENT_TICK_UNAVAILABLE"
            )

        raw_tick = getattr(
            tick,
            "time",
            None,
        )

        if raw_tick is None:
            raise TimestampBasisResolutionError(
                "CURRENT_TICK_TIME_MISSING"
            )

        raw_tick_epoch = int(
            raw_tick
        )

        now_epoch = float(
            self._now_provider()
        )

        if (
            self._timestamp_basis
            == TIME_BASIS_AUTO
        ):
            return detect_timestamp_basis_from_tick(
                raw_tick_epoch=(
                    raw_tick_epoch
                ),
                now_epoch=(
                    now_epoch
                ),
                max_tick_age_seconds=(
                    self._max_tick_age_seconds
                ),
                max_future_tick_skew_seconds=(
                    self._max_future_tick_skew_seconds
                ),
            )

        if (
            self._timestamp_basis
            == TIME_BASIS_UNIX_UTC
        ):
            normalized_tick = (
                _timestamp_from_epoch_seconds(
                    raw_tick_epoch
                )
            )

            age_seconds = (
                _validate_tick_age(
                    normalized_tick,
                    now_epoch=now_epoch,
                    max_tick_age_seconds=(
                        self._max_tick_age_seconds
                    ),
                    max_future_tick_skew_seconds=(
                        self._max_future_tick_skew_seconds
                    ),
                )
            )

            return TimeBasisResolution(
                policy=(
                    TIME_BASIS_UNIX_UTC
                ),
                reference_tick_raw=(
                    raw_tick_epoch
                ),
                reference_tick_utc=(
                    _to_utc_iso(
                        normalized_tick
                    )
                ),
                reference_offset_seconds=0,
                reference_tick_age_seconds=(
                    age_seconds
                ),
            )

        if (
            self._timestamp_basis
            == TIME_BASIS_NY_CLOSE_SERVER
        ):
            (
                normalized_tick,
                offset_seconds,
            ) = normalize_ny_close_server_epoch(
                raw_tick_epoch
            )

            age_seconds = (
                _validate_tick_age(
                    normalized_tick,
                    now_epoch=now_epoch,
                    max_tick_age_seconds=(
                        self._max_tick_age_seconds
                    ),
                    max_future_tick_skew_seconds=(
                        self._max_future_tick_skew_seconds
                    ),
                )
            )

            return TimeBasisResolution(
                policy=(
                    TIME_BASIS_NY_CLOSE_SERVER
                ),
                reference_tick_raw=(
                    raw_tick_epoch
                ),
                reference_tick_utc=(
                    _to_utc_iso(
                        normalized_tick
                    )
                ),
                reference_offset_seconds=(
                    offset_seconds
                ),
                reference_tick_age_seconds=(
                    age_seconds
                ),
            )

        raise TimestampBasisResolutionError(
            "TIMESTAMP_BASIS_RESOLUTION_FAILED"
        )

    @staticmethod
    def _normalize_raw_epoch(
        raw_epoch: int,
        policy: str,
    ) -> tuple[
        pd.Timestamp,
        int,
    ]:
        if (
            policy
            == TIME_BASIS_UNIX_UTC
        ):
            return (
                _timestamp_from_epoch_seconds(
                    raw_epoch
                ),
                0,
            )

        if (
            policy
            == TIME_BASIS_NY_CLOSE_SERVER
        ):
            return (
                normalize_ny_close_server_epoch(
                    raw_epoch
                )
            )

        raise TimestampBasisResolutionError(
            "UNRESOLVED_OR_UNSUPPORTED_TIMESTAMP_POLICY:"
            f"{policy}"
        )

    def _convert_rates_to_frame(
        self,
        rates: np.ndarray,
        timeframe: str,
        *,
        time_basis_policy: str,
    ) -> pd.DataFrame:

        if (
            rates is None
            or len(rates) == 0
        ):
            raise InsufficientForwardHistoryError(
                f"No rates returned for timeframe {timeframe}"
            )

        dtype_names = (
            rates.dtype.names
        )

        if dtype_names is None:
            raise MalformedBarDataError(
                f"Rates dtype has no named fields for {timeframe}"
            )

        data: dict[
            str,
            Any,
        ] = {}

        for column in (
            "time",
            "open",
            "high",
            "low",
            "close",
            "tick_volume",
        ):
            if column not in dtype_names:
                raise MalformedBarDataError(
                    f"Missing required field {column!r} "
                    f"in rates for {timeframe}"
                )

            data[column] = (
                rates[column]
            )

        raw_times = [
            int(value)
            for value
            in data["time"]
        ]

        normalized_times: list[
            pd.Timestamp
        ] = []

        for raw_epoch in raw_times:
            (
                normalized_time,
                _,
            ) = self._normalize_raw_epoch(
                raw_epoch,
                time_basis_policy,
            )

            normalized_times.append(
                normalized_time
            )

        frame = pd.DataFrame(
            data
        )

        frame["time"] = pd.DatetimeIndex(
            normalized_times
        )

        for column in (
            "open",
            "high",
            "low",
            "close",
            "tick_volume",
        ):
            frame[column] = (
                pd.to_numeric(
                    frame[column],
                    errors="coerce",
                )
            )

        if bool(
            frame[
                [
                    "open",
                    "high",
                    "low",
                    "close",
                    "tick_volume",
                ]
            ]
            .isna()
            .to_numpy()
            .any()
        ):
            raise MalformedBarDataError(
                f"Non-numeric or NaN values in OHLCV for {timeframe}"
            )

        lows = frame[
            "low"
        ].to_numpy()

        highs = frame[
            "high"
        ].to_numpy()

        opens = frame[
            "open"
        ].to_numpy()

        closes = frame[
            "close"
        ].to_numpy()

        if (
            (lows <= 0).any()
            or (highs < lows).any()
        ):
            raise MalformedBarDataError(
                f"Invalid OHLC geometry in {timeframe}: "
                "low <= 0 or high < low"
            )

        if (
            (highs < opens).any()
            or (highs < closes).any()
        ):
            raise MalformedBarDataError(
                f"Invalid OHLC geometry in {timeframe}: "
                "high < open or high < close"
            )

        if (
            (lows > opens).any()
            or (lows > closes).any()
        ):
            raise MalformedBarDataError(
                f"Invalid OHLC geometry in {timeframe}: "
                "low > open or low > close"
            )

        frame = (
            frame
            .sort_values(
                by="time"
            )
            .reset_index(
                drop=True
            )
        )

        if not frame[
            "time"
        ].is_monotonic_increasing:
            raise MalformedBarDataError(
                f"Timestamps are not strictly monotonic in {timeframe}"
            )

        if frame[
            "time"
        ].duplicated().any():
            raise MalformedBarDataError(
                f"Duplicate timestamps detected in {timeframe}"
            )

        min_bars = (
            self._min_history_bars.get(
                timeframe,
                50,
            )
        )

        if len(frame) < min_bars:
            raise InsufficientForwardHistoryError(
                f"Insufficient bars for {timeframe}: "
                f"{len(frame)} < {min_bars}"
            )

        return frame

    def acquire_snapshot(
        self,
        *,
        acquisition_time_utc: str | None = None,
        enforce_forward_boundaries: bool = True,
    ) -> ForwardMarketSnapshot:

        broker_symbol = (
            self.resolve_broker_symbol()
        )

        time_basis = (
            self._resolve_time_basis(
                broker_symbol
            )
        )

        if acquisition_time_utc is not None:
            norm_acq_time = (
                validate_iso8601_utc(
                    acquisition_time_utc
                )
            )

        else:
            norm_acq_time = (
                validate_iso8601_utc(
                    pd.Timestamp.now(
                        tz="UTC"
                    ).isoformat()
                )
            )

        market_data: dict[
            str,
            pd.DataFrame,
        ] = {}

        bar_counts: dict[
            str,
            int,
        ] = {}

        earliest_opens: dict[
            str,
            str,
        ] = {}

        latest_opens: dict[
            str,
            str,
        ] = {}

        latest_availables: dict[
            str,
            str,
        ] = {}

        for timeframe in (
            self.REQUIRED_TIMEFRAMES
        ):
            raw_rates = (
                self._facade
                .copy_rates_from_pos(
                    broker_symbol,
                    self._tf_enum(
                        timeframe
                    ),
                    1,
                    self._min_history_bars.get(
                        timeframe,
                        200,
                    ),
                )
            )

            if raw_rates is None:
                raise MT5ConnectionUnavailableError(
                    "Failed to fetch rates for "
                    f"{broker_symbol} on {timeframe}"
                )

            frame = (
                self._convert_rates_to_frame(
                    raw_rates,
                    timeframe,
                    time_basis_policy=(
                        time_basis.policy
                    ),
                )
            )

            market_data[
                timeframe
            ] = frame

            bar_counts[
                timeframe
            ] = len(
                frame
            )

            first_open = (
                _to_utc_iso(
                    frame[
                        "time"
                    ].iloc[0]
                )
            )

            last_open_ts = (
                _to_utc_timestamp(
                    frame[
                        "time"
                    ].iloc[-1]
                )
            )

            last_open = (
                _to_utc_iso(
                    last_open_ts
                )
            )

            last_available_ts = (
                last_open_ts
                + pd.Timedelta(
                    minutes=(
                        TIMEFRAME_MINUTES[
                            timeframe
                        ]
                    )
                )
            )

            last_available = (
                _to_utc_iso(
                    last_available_ts
                )
            )

            earliest_opens[
                timeframe
            ] = first_open

            latest_opens[
                timeframe
            ] = last_open

            latest_availables[
                timeframe
            ] = last_available

        native_d1_diagnostic: (
            pd.DataFrame
            | None
        ) = None

        if self._include_native_d1:
            raw_d1 = (
                self._facade
                .copy_rates_from_pos(
                    broker_symbol,
                    self._tf_enum(
                        "D1"
                    ),
                    1,
                    self._min_history_bars.get(
                        "D1",
                        200,
                    ),
                )
            )

            if raw_d1 is not None:
                native_d1_diagnostic = (
                    self._convert_rates_to_frame(
                        raw_d1,
                        "D1",
                        time_basis_policy=(
                            time_basis.policy
                        ),
                    )
                )

        latest_m5_open = (
            _to_utc_timestamp(
                market_data[
                    "M5"
                ][
                    "time"
                ].iloc[-1]
            )
        )

        decision_time_ts = (
            latest_m5_open
            + pd.Timedelta(
                minutes=5
            )
        )

        decision_time_utc = (
            validate_iso8601_utc(
                _to_utc_iso(
                    decision_time_ts
                )
            )
        )

        for timeframe in (
            self.REQUIRED_TIMEFRAMES
        ):
            timeframe_available = (
                _to_utc_timestamp(
                    latest_availables[
                        timeframe
                    ]
                )
            )

            if (
                timeframe_available
                > decision_time_ts
            ):
                raise MalformedBarDataError(
                    "Higher timeframe "
                    f"{timeframe} available_time "
                    f"({latest_availables[timeframe]}) "
                    "exceeds decision_time "
                    f"({decision_time_utc}). "
                    "Lookahead detected."
                )

        if (
            time_basis.reference_tick_utc
            is not None
        ):
            reference_tick_ts = (
                _to_utc_timestamp(
                    time_basis.reference_tick_utc
                )
            )

            if (
                decision_time_ts
                > reference_tick_ts
            ):
                raise MalformedBarDataError(
                    f"Decision time {decision_time_utc} exceeds "
                    "normalized reference tick "
                    f"{time_basis.reference_tick_utc}."
                )

        if enforce_forward_boundaries:
            if (
                decision_time_utc
                <= RESEARCH_FREEZE_BOUNDARY_UTC
            ):
                raise HistoricalFreezeBoundaryViolationError(
                    f"Decision time {decision_time_utc} is within "
                    "historical research freeze boundary "
                    f"({RESEARCH_FREEZE_BOUNDARY_UTC})."
                )

            if (
                decision_time_utc
                < GATE_15A_ACTIVATION_UTC
            ):
                raise PreActivationForwardError(
                    f"Decision time {decision_time_utc} precedes "
                    "Gate 15A activation authority "
                    f"({GATE_15A_ACTIVATION_UTC})."
                )

        snapshot_id = (
            compute_canonical_snapshot_id(
                market_data
            )
        )

        attestation_payload = {
            "schema_version": (
                ACQUISITION_SCHEMA_VERSION
            ),
            "acquisition_authority": (
                ACQUISITION_AUTHORITY_ID
            ),
            "canonical_instrument": (
                self._canonical_symbol
            ),
            "resolved_broker_symbol": (
                broker_symbol
            ),
            "acquisition_time_utc": (
                norm_acq_time
            ),
            "decision_time_utc": (
                decision_time_utc
            ),
            "timeframe_bar_counts": (
                bar_counts
            ),
            "earliest_bar_open_utc": (
                earliest_opens
            ),
            "latest_bar_open_utc": (
                latest_opens
            ),
            "latest_bar_available_utc": (
                latest_availables
            ),
            "research_freeze_boundary_utc": (
                RESEARCH_FREEZE_BOUNDARY_UTC
            ),
            "gate_15a_activation_utc": (
                GATE_15A_ACTIVATION_UTC
            ),
            "source_snapshot_id": (
                snapshot_id
            ),
            "feature_columns_sha256": (
                EXPECTED_FEATURE_COLUMNS_SHA256
            ),
            "model_sha256": (
                FROZEN_MODEL_SHA256
            ),
            "capability_manifest": list(
                sorted(
                    MT5ReadOnlyCapabilityFacade.ALLOWED_METHODS
                )
            ),
            "is_synthetic": (
                self._is_synthetic
            ),
            "time_basis_policy": (
                time_basis.policy
            ),
            "time_basis_reference_tick_raw": (
                time_basis.reference_tick_raw
            ),
            "time_basis_reference_tick_utc": (
                time_basis.reference_tick_utc
            ),
            "time_basis_reference_offset_seconds": (
                time_basis.reference_offset_seconds
            ),
            "time_basis_reference_tick_age_seconds": (
                time_basis.reference_tick_age_seconds
            ),
        }

        encoded_attestation = (
            json.dumps(
                attestation_payload,
                sort_keys=True,
                separators=(",", ":"),
            )
            .encode(
                "utf-8"
            )
        )

        attestation_sha256 = (
            hashlib.sha256(
                encoded_attestation
            )
            .hexdigest()
        )

        attestation = (
            ForwardAcquisitionAttestation(
                schema_version=(
                    ACQUISITION_SCHEMA_VERSION
                ),
                acquisition_authority=(
                    ACQUISITION_AUTHORITY_ID
                ),
                canonical_instrument=(
                    self._canonical_symbol
                ),
                resolved_broker_symbol=(
                    broker_symbol
                ),
                acquisition_time_utc=(
                    norm_acq_time
                ),
                decision_time_utc=(
                    decision_time_utc
                ),
                timeframe_bar_counts=(
                    bar_counts
                ),
                earliest_bar_open_utc=(
                    earliest_opens
                ),
                latest_bar_open_utc=(
                    latest_opens
                ),
                latest_bar_available_utc=(
                    latest_availables
                ),
                research_freeze_boundary_utc=(
                    RESEARCH_FREEZE_BOUNDARY_UTC
                ),
                gate_15a_activation_utc=(
                    GATE_15A_ACTIVATION_UTC
                ),
                source_snapshot_id=(
                    snapshot_id
                ),
                feature_columns_sha256=(
                    EXPECTED_FEATURE_COLUMNS_SHA256
                ),
                model_sha256=(
                    FROZEN_MODEL_SHA256
                ),
                capability_manifest=tuple(
                    sorted(
                        MT5ReadOnlyCapabilityFacade.ALLOWED_METHODS
                    )
                ),
                is_synthetic=(
                    self._is_synthetic
                ),
                attestation_sha256=(
                    attestation_sha256
                ),
                time_basis_policy=(
                    time_basis.policy
                ),
                time_basis_reference_tick_raw=(
                    time_basis.reference_tick_raw
                ),
                time_basis_reference_tick_utc=(
                    time_basis.reference_tick_utc
                ),
                time_basis_reference_offset_seconds=(
                    time_basis.reference_offset_seconds
                ),
                time_basis_reference_tick_age_seconds=(
                    time_basis.reference_tick_age_seconds
                ),
            )
        )

        authority: (
            VerifiedForwardAcquisitionAuthority
            | None
        ) = None

        if not self._is_synthetic:
            authority = (
                VerifiedForwardAcquisitionAuthority(
                    _PRIVATE_FORWARD_AUTHORITY_TOKEN,
                    attestation,
                    is_synthetic=False,
                )
            )

        return ForwardMarketSnapshot(
            canonical_instrument=(
                self._canonical_symbol
            ),
            broker_symbol=(
                broker_symbol
            ),
            market_data=(
                market_data
            ),
            decision_time_utc=(
                decision_time_utc
            ),
            source_snapshot_id=(
                snapshot_id
            ),
            attestation=(
                attestation
            ),
            is_synthetic=(
                self._is_synthetic
            ),
            authority=(
                authority
            ),
            native_d1_diagnostic=(
                native_d1_diagnostic
            ),
        )