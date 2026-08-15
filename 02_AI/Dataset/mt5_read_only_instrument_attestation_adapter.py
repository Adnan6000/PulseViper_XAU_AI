"""Read-only MT5 instrument metadata attestation.

This module is intentionally execution-neutral.

It may read symbol metadata from an already-initialized MT5 API/session, but it
does not:

- initialize or shutdown MT5
- select symbols
- request historical bars or ticks
- submit orders
- modify positions
- authorize live execution
- mutate risk/lifecycle/accounting state

The low-level adapter is instrument-agnostic. XAUUSD-specific acceptance is
performed separately by XAUUSDBrokerInstrumentContextBinder.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math

from dataclasses import dataclass
from typing import Any


binding_module: Any = importlib.import_module(
    "02_AI.Dataset.broker_instrument_context_binding"
)

XAUUSDBrokerInstrumentContextBinder: Any = (
    binding_module.XAUUSDBrokerInstrumentContextBinder
)


@dataclass(frozen=True)
class MT5SymbolInfoAttestation:
    name: str

    currency_base: str
    currency_profit: str
    description: str

    digits: int
    point: float

    trade_contract_size: float

    volume_min: float
    volume_max: float
    volume_step: float

    trade_mode: int

    visible: bool
    selected: bool

    live_authorized: bool = False

    def to_document(
        self,
    ) -> dict[str, Any]:

        return {
            "name": self.name,
            "currency_base": self.currency_base,
            "currency_profit": self.currency_profit,
            "description": self.description,
            "digits": self.digits,
            "point": self.point,
            "trade_contract_size": (
                self.trade_contract_size
            ),
            "volume_min": self.volume_min,
            "volume_max": self.volume_max,
            "volume_step": self.volume_step,
            "trade_mode": self.trade_mode,
            "visible": self.visible,
            "selected": self.selected,
            "live_authorized": False,
        }

    @property
    def fingerprint(
        self,
    ) -> str:

        encoded = json.dumps(
            self.to_document(),
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
            ensure_ascii=False,
            allow_nan=False,
        ).encode(
            "utf-8"
        )

        return hashlib.sha256(
            encoded
        ).hexdigest()


@dataclass(frozen=True)
class MT5SymbolInfoAttestationResult:
    valid: bool

    attested: bool

    reason: str

    action: str

    mode: str

    version: str

    live_authorized: bool

    expected_symbol: str

    observed_symbol: str

    symbol_info_invoked: bool

    mt5_error: str

    attestation_fingerprint: str

    attestation: MT5SymbolInfoAttestation | None


@dataclass(frozen=True)
class MT5XAUUSDContextAttestationResult:
    valid: bool

    bound: bool

    reason: str

    attestation_reason: str

    binding_reason: str

    action: str

    mode: str

    version: str

    live_authorized: bool

    requested_symbol: str

    resolved_symbol: str

    canonical_symbol: str

    asset_class: str

    attestation_fingerprint: str

    context_identity_fingerprint: str

    attestation_result: Any

    binding_result: Any

    context: Any


class MT5ReadOnlyInstrumentAttestationAdapter:
    VERSION = "1.0"

    MODE = (
        "MT5_READ_ONLY_INSTRUMENT_"
        "METADATA_ATTESTATION_ONLY"
    )

    def __init__(
        self,
        *,
        mt5_api: Any | None = None,
    ) -> None:

        self._mt5_api = mt5_api

    # =========================================================================
    # MT5 API
    # =========================================================================

    def _api(
        self,
    ) -> Any:

        if self._mt5_api is not None:

            return self._mt5_api

        return importlib.import_module(
            "MetaTrader5"
        )

    # =========================================================================
    # Generic helpers
    # =========================================================================

    @staticmethod
    def _field(
        value: Any,
        name: str,
        default: Any = None,
    ) -> Any:

        if value is None:

            return default

        if isinstance(
            value,
            dict,
        ):

            return value.get(
                name,
                default,
            )

        if hasattr(
            value,
            name,
        ):

            return getattr(
                value,
                name,
            )

        dtype = getattr(
            value,
            "dtype",
            None,
        )

        names = getattr(
            dtype,
            "names",
            None,
        )

        if (
            names is not None
            and
            name in names
        ):

            try:

                result = value[
                    name
                ]

                if hasattr(
                    result,
                    "item",
                ):

                    return result.item()

                return result

            except Exception:

                return default

        try:

            return value[
                name
            ]

        except Exception:

            return default

    @staticmethod
    def _number(
        value: Any,
    ) -> float:

        try:

            resolved = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return math.nan

        if not math.isfinite(
            resolved
        ):

            return math.nan

        return resolved

    @staticmethod
    def _integer(
        value: Any,
    ) -> int | None:

        if isinstance(
            value,
            bool,
        ):

            return None

        try:

            return int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    @staticmethod
    def _last_error(
        api: Any,
    ) -> str:

        try:

            return str(
                api.last_error()
            )

        except Exception:

            return "unavailable"

    # =========================================================================
    # Result
    # =========================================================================

    def _result(
        self,
        *,
        valid: bool,
        attested: bool,
        reason: str,
        expected_symbol: str,
        observed_symbol: str = "",
        symbol_info_invoked: bool,
        mt5_error: str = "",
        attestation: MT5SymbolInfoAttestation | None = None,
    ) -> MT5SymbolInfoAttestationResult:

        return MT5SymbolInfoAttestationResult(
            valid=valid,
            attested=attested,
            reason=reason,
            action=(
                "USE_ATTESTED_MT5_SYMBOL_METADATA"
                if attested
                else
                "NO_ACTION"
            ),
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            expected_symbol=expected_symbol,
            observed_symbol=observed_symbol,
            symbol_info_invoked=symbol_info_invoked,
            mt5_error=mt5_error,
            attestation_fingerprint=(
                attestation.fingerprint
                if attestation is not None
                else
                ""
            ),
            attestation=attestation,
        )

    def _invalid(
        self,
        *,
        reason: str,
        expected_symbol: str,
        observed_symbol: str = "",
        symbol_info_invoked: bool,
        mt5_error: str = "",
    ) -> MT5SymbolInfoAttestationResult:

        return self._result(
            valid=False,
            attested=False,
            reason=reason,
            expected_symbol=expected_symbol,
            observed_symbol=observed_symbol,
            symbol_info_invoked=(
                symbol_info_invoked
            ),
            mt5_error=mt5_error,
        )

    # =========================================================================
    # Public API
    # =========================================================================

    def read_symbol(
        self,
        *,
        expected_symbol: Any,
    ) -> MT5SymbolInfoAttestationResult:

        symbol = str(
            expected_symbol
        ).strip()

        if (
            not symbol
            or
            symbol in {
                ".",
                "..",
            }
            or
            "\x00"
            in symbol
            or
            "/"
            in symbol
            or
            "\\"
            in symbol
        ):

            return self._invalid(
                reason="INVALID_EXPECTED_SYMBOL",
                expected_symbol="",
                symbol_info_invoked=False,
            )

        api = self._api()

        try:

            raw = api.symbol_info(
                symbol
            )

        except Exception:

            return self._invalid(
                reason="MT5_SYMBOL_INFO_EXCEPTION",
                expected_symbol=symbol,
                symbol_info_invoked=True,
                mt5_error=(
                    self._last_error(
                        api
                    )
                ),
            )

        if raw is None:

            return self._invalid(
                reason="MT5_SYMBOL_INFO_NOT_FOUND",
                expected_symbol=symbol,
                symbol_info_invoked=True,
                mt5_error=(
                    self._last_error(
                        api
                    )
                ),
            )

        observed_symbol = str(
            self._field(
                raw,
                "name",
                "",
            )
        ).strip()

        if not observed_symbol:

            return self._invalid(
                reason="MT5_SYMBOL_INFO_NAME_MISSING",
                expected_symbol=symbol,
                symbol_info_invoked=True,
            )

        if observed_symbol != symbol:

            return self._invalid(
                reason=(
                    "MT5_SYMBOL_INFO_EXACT_NAME_MISMATCH"
                ),
                expected_symbol=symbol,
                observed_symbol=(
                    observed_symbol
                ),
                symbol_info_invoked=True,
            )

        currency_base = str(
            self._field(
                raw,
                "currency_base",
                "",
            )
        ).strip().upper()

        currency_profit = str(
            self._field(
                raw,
                "currency_profit",
                "",
            )
        ).strip().upper()

        if not currency_base:

            return self._invalid(
                reason=(
                    "MT5_SYMBOL_INFO_BASE_CURRENCY_MISSING"
                ),
                expected_symbol=symbol,
                observed_symbol=(
                    observed_symbol
                ),
                symbol_info_invoked=True,
            )

        if not currency_profit:

            return self._invalid(
                reason=(
                    "MT5_SYMBOL_INFO_PROFIT_CURRENCY_MISSING"
                ),
                expected_symbol=symbol,
                observed_symbol=(
                    observed_symbol
                ),
                symbol_info_invoked=True,
            )

        digits = self._integer(
            self._field(
                raw,
                "digits",
                None,
            )
        )

        if (
            digits is None
            or
            digits < 0
            or
            digits > 12
        ):

            return self._invalid(
                reason="INVALID_MT5_SYMBOL_DIGITS",
                expected_symbol=symbol,
                observed_symbol=(
                    observed_symbol
                ),
                symbol_info_invoked=True,
            )

        point = self._number(
            self._field(
                raw,
                "point",
                None,
            )
        )

        if (
            not math.isfinite(
                point
            )
            or
            point <= 0.0
        ):

            return self._invalid(
                reason="INVALID_MT5_SYMBOL_POINT",
                expected_symbol=symbol,
                observed_symbol=(
                    observed_symbol
                ),
                symbol_info_invoked=True,
            )

        contract_size = self._number(
            self._field(
                raw,
                "trade_contract_size",
                None,
            )
        )

        if (
            not math.isfinite(
                contract_size
            )
            or
            contract_size <= 0.0
        ):

            return self._invalid(
                reason=(
                    "INVALID_MT5_SYMBOL_CONTRACT_SIZE"
                ),
                expected_symbol=symbol,
                observed_symbol=(
                    observed_symbol
                ),
                symbol_info_invoked=True,
            )

        volume_min = self._number(
            self._field(
                raw,
                "volume_min",
                None,
            )
        )

        volume_max = self._number(
            self._field(
                raw,
                "volume_max",
                None,
            )
        )

        volume_step = self._number(
            self._field(
                raw,
                "volume_step",
                None,
            )
        )

        if (
            not math.isfinite(
                volume_min
            )
            or
            volume_min <= 0.0
        ):

            return self._invalid(
                reason=(
                    "INVALID_MT5_SYMBOL_VOLUME_MIN"
                ),
                expected_symbol=symbol,
                observed_symbol=(
                    observed_symbol
                ),
                symbol_info_invoked=True,
            )

        if (
            not math.isfinite(
                volume_max
            )
            or
            volume_max < volume_min
        ):

            return self._invalid(
                reason=(
                    "INVALID_MT5_SYMBOL_VOLUME_MAX"
                ),
                expected_symbol=symbol,
                observed_symbol=(
                    observed_symbol
                ),
                symbol_info_invoked=True,
            )

        if (
            not math.isfinite(
                volume_step
            )
            or
            volume_step <= 0.0
        ):

            return self._invalid(
                reason=(
                    "INVALID_MT5_SYMBOL_VOLUME_STEP"
                ),
                expected_symbol=symbol,
                observed_symbol=(
                    observed_symbol
                ),
                symbol_info_invoked=True,
            )

        trade_mode = self._integer(
            self._field(
                raw,
                "trade_mode",
                0,
            )
        )

        if (
            trade_mode is None
            or
            trade_mode < 0
        ):

            return self._invalid(
                reason=(
                    "INVALID_MT5_SYMBOL_TRADE_MODE"
                ),
                expected_symbol=symbol,
                observed_symbol=(
                    observed_symbol
                ),
                symbol_info_invoked=True,
            )

        attestation = MT5SymbolInfoAttestation(
            name=observed_symbol,
            currency_base=currency_base,
            currency_profit=(
                currency_profit
            ),
            description=str(
                self._field(
                    raw,
                    "description",
                    "",
                )
                or
                ""
            ).strip(),
            digits=digits,
            point=point,
            trade_contract_size=(
                contract_size
            ),
            volume_min=volume_min,
            volume_max=volume_max,
            volume_step=volume_step,
            trade_mode=trade_mode,
            visible=bool(
                self._field(
                    raw,
                    "visible",
                    False,
                )
            ),
            selected=bool(
                self._field(
                    raw,
                    "select",
                    False,
                )
            ),
            live_authorized=False,
        )

        return self._result(
            valid=True,
            attested=True,
            reason=(
                "OK_MT5_SYMBOL_METADATA_ATTESTED"
            ),
            expected_symbol=symbol,
            observed_symbol=(
                observed_symbol
            ),
            symbol_info_invoked=True,
            attestation=attestation,
        )


class MT5ReadOnlyXAUUSDContextAttestor:
    """Read exact MT5 metadata, then invoke the strict XAUUSD binder."""

    VERSION = "1.0"

    MODE = (
        "MT5_READ_ONLY_XAUUSD_"
        "INSTRUMENT_CONTEXT_ATTESTATION_ONLY"
    )

    _FETCHER_FIELDS = (
        "last_requested_symbol",
        "last_resolved_symbol",
        "last_bar_count",
    )

    def __init__(
        self,
        *,
        adapter: Any | None = None,
        binder: Any | None = None,
        mt5_api: Any | None = None,
    ) -> None:

        self.adapter = (
            adapter
            if adapter is not None
            else
            MT5ReadOnlyInstrumentAttestationAdapter(
                mt5_api=mt5_api
            )
        )

        self.binder = (
            binder
            if binder is not None
            else
            XAUUSDBrokerInstrumentContextBinder()
        )

    @staticmethod
    def _has_fields(
        value: Any,
        fields: tuple[str, ...],
    ) -> bool:

        return (
            value is not None
            and
            all(
                hasattr(
                    value,
                    field,
                )
                for field
                in fields
            )
        )

    def _result(
        self,
        *,
        valid: bool,
        bound: bool,
        reason: str,
        requested_symbol: str,
        resolved_symbol: str,
        attestation_result: Any = None,
        binding_result: Any = None,
    ) -> MT5XAUUSDContextAttestationResult:

        context = (
            getattr(
                binding_result,
                "context",
                None,
            )
            if binding_result is not None
            else
            None
        )

        return MT5XAUUSDContextAttestationResult(
            valid=valid,
            bound=bound,
            reason=reason,
            attestation_reason=str(
                getattr(
                    attestation_result,
                    "reason",
                    "",
                )
            ),
            binding_reason=str(
                getattr(
                    binding_result,
                    "reason",
                    "",
                )
            ),
            action=(
                "USE_ATTESTED_XAUUSD_CONTEXT"
                if bound
                else
                "NO_ACTION"
            ),
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            requested_symbol=(
                requested_symbol
            ),
            resolved_symbol=(
                resolved_symbol
            ),
            canonical_symbol=str(
                getattr(
                    binding_result,
                    "canonical_symbol",
                    "",
                )
            ),
            asset_class=str(
                getattr(
                    binding_result,
                    "asset_class",
                    "",
                )
            ),
            attestation_fingerprint=str(
                getattr(
                    attestation_result,
                    "attestation_fingerprint",
                    "",
                )
            ),
            context_identity_fingerprint=str(
                getattr(
                    binding_result,
                    "context_identity_fingerprint",
                    "",
                )
            ),
            attestation_result=(
                attestation_result
            ),
            binding_result=binding_result,
            context=context,
        )

    def attest_fetcher_resolution(
        self,
        *,
        fetcher_state: Any,
        broker_id: str,
        account_scope_id: str,
        execution_environment: str,
        contract_spec_id: str,
        data_schema_version: str,
        feature_contract_version: str,
    ) -> MT5XAUUSDContextAttestationResult:

        if not self._has_fields(
            fetcher_state,
            self._FETCHER_FIELDS,
        ):

            return self._result(
                valid=False,
                bound=False,
                reason=(
                    "INVALID_FETCHER_RESOLUTION_STATE"
                ),
                requested_symbol="",
                resolved_symbol="",
            )

        requested_symbol = str(
            fetcher_state.last_requested_symbol
        ).strip()

        resolved_symbol = str(
            fetcher_state.last_resolved_symbol
        ).strip()

        if not resolved_symbol:

            return self._result(
                valid=False,
                bound=False,
                reason=(
                    "RESOLVED_SYMBOL_MISSING"
                ),
                requested_symbol=(
                    requested_symbol
                ),
                resolved_symbol="",
            )

        attestation_result = (
            self.adapter.read_symbol(
                expected_symbol=(
                    resolved_symbol
                )
            )
        )

        if (
            not bool(
                attestation_result.valid
            )
            or
            not bool(
                attestation_result.attested
            )
        ):

            return self._result(
                valid=False,
                bound=False,
                reason=(
                    "MT5_SYMBOL_ATTESTATION_REJECTED"
                ),
                requested_symbol=(
                    requested_symbol
                ),
                resolved_symbol=(
                    resolved_symbol
                ),
                attestation_result=(
                    attestation_result
                ),
            )

        if bool(
            attestation_result.live_authorized
        ):

            return self._result(
                valid=False,
                bound=False,
                reason=(
                    "MT5_ATTESTATION_LIVE_"
                    "AUTHORIZATION_NOT_ALLOWED"
                ),
                requested_symbol=(
                    requested_symbol
                ),
                resolved_symbol=(
                    resolved_symbol
                ),
                attestation_result=(
                    attestation_result
                ),
            )

        binding_result = (
            self.binder.bind_fetcher_resolution(
                fetcher_state=fetcher_state,
                symbol_info=(
                    attestation_result.attestation
                ),
                broker_id=broker_id,
                account_scope_id=(
                    account_scope_id
                ),
                execution_environment=(
                    execution_environment
                ),
                contract_spec_id=(
                    contract_spec_id
                ),
                data_schema_version=(
                    data_schema_version
                ),
                feature_contract_version=(
                    feature_contract_version
                ),
            )
        )

        if (
            not bool(
                binding_result.valid
            )
            or
            not bool(
                binding_result.bound
            )
        ):

            return self._result(
                valid=False,
                bound=False,
                reason=(
                    "XAUUSD_CONTEXT_BINDING_REJECTED"
                ),
                requested_symbol=(
                    requested_symbol
                ),
                resolved_symbol=(
                    resolved_symbol
                ),
                attestation_result=(
                    attestation_result
                ),
                binding_result=(
                    binding_result
                ),
            )

        context = (
            binding_result.context
        )

        if (
            context is None
            or
            bool(
                context.live_authorized
            )
            or
            str(
                context.canonical_symbol
            )
            !=
            "XAUUSD"
            or
            str(
                context.asset_class
            )
            !=
            "METAL"
            or
            str(
                context.broker_symbol
            )
            !=
            resolved_symbol
        ):

            return self._result(
                valid=False,
                bound=False,
                reason=(
                    "ATTESTED_CONTEXT_BOUNDARY_"
                    "VIOLATION"
                ),
                requested_symbol=(
                    requested_symbol
                ),
                resolved_symbol=(
                    resolved_symbol
                ),
                attestation_result=(
                    attestation_result
                ),
                binding_result=(
                    binding_result
                ),
            )

        return self._result(
            valid=True,
            bound=True,
            reason=(
                "OK_READ_ONLY_XAUUSD_CONTEXT_ATTESTED"
            ),
            requested_symbol=(
                requested_symbol
            ),
            resolved_symbol=(
                resolved_symbol
            ),
            attestation_result=(
                attestation_result
            ),
            binding_result=(
                binding_result
            ),
        )