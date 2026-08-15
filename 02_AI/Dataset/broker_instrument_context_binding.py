"""Broker-resolved XAUUSD -> canonical InstrumentContext binding.

Pure identity layer: no MT5 import, no broker calls, no order execution and no
live authorization. It consumes already-resolved history evidence plus a
symbol-info snapshot supplied by the caller.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


_context = importlib.import_module(
    "02_AI.Common.instrument_context"
)

InstrumentDefinition: Any = (
    _context.InstrumentDefinition
)

InstrumentContext: Any = (
    _context.InstrumentContext
)

InstrumentIsolationError: Any = (
    _context.InstrumentIsolationError
)


@dataclass(frozen=True)
class BrokerResolvedInstrumentEvidence:
    requested_symbol: str
    resolved_symbol: str
    symbol_info_name: str
    currency_base: str
    currency_profit: str
    description: str
    history_bar_count: int
    source: str
    live_authorized: bool = False

    def to_document(
        self,
    ) -> dict[str, Any]:

        return {
            "requested_symbol": self.requested_symbol,
            "resolved_symbol": self.resolved_symbol,
            "symbol_info_name": self.symbol_info_name,
            "currency_base": self.currency_base,
            "currency_profit": self.currency_profit,
            "description": self.description,
            "history_bar_count": self.history_bar_count,
            "source": self.source,
            "live_authorized": False,
        }

    @property
    def fingerprint(
        self,
    ) -> str:

        payload = json.dumps(
            self.to_document(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode(
            "utf-8"
        )

        return hashlib.sha256(
            payload
        ).hexdigest()


@dataclass(frozen=True)
class BrokerInstrumentContextBindingResult:
    valid: bool
    bound: bool
    reason: str
    action: str
    mode: str
    version: str
    live_authorized: bool

    canonical_symbol: str
    asset_class: str

    requested_symbol: str
    resolved_symbol: str

    definition_fingerprint: str
    evidence_fingerprint: str
    context_identity_fingerprint: str

    evidence: BrokerResolvedInstrumentEvidence | None
    context: Any | None


class XAUUSDBrokerInstrumentContextBinder:

    VERSION = "1.0"

    MODE = (
        "XAUUSD_BROKER_RESOLUTION_TO_"
        "INSTRUMENT_CONTEXT_BINDING_ONLY"
    )

    CANONICAL_SYMBOL = "XAUUSD"

    ASSET_CLASS = "METAL"

    DEFINITION_VERSION = (
        "XAUUSD_BROKER_ALIASES_V1"
    )

    DEFAULT_ALLOWED_BROKER_SYMBOLS = (
        "XAUUSD",
        "XAUUSDm",
        "XAUUSD.a",
        "XAUUSD.pro",
        "GOLD",
        "GOLDm",
    )

    _FETCHER_FIELDS = (
        "last_requested_symbol",
        "last_resolved_symbol",
        "last_bar_count",
    )

    _SYMBOL_INFO_FIELDS = (
        "name",
        "currency_base",
        "currency_profit",
    )

    def __init__(
        self,
        *,
        allowed_broker_symbols: Sequence[str] | None = None,
    ) -> None:

        aliases = tuple(
            allowed_broker_symbols
            if allowed_broker_symbols is not None
            else self.DEFAULT_ALLOWED_BROKER_SYMBOLS
        )

        self.definition = InstrumentDefinition(
            canonical_symbol=(
                self.CANONICAL_SYMBOL
            ),
            asset_class=(
                self.ASSET_CLASS
            ),
            broker_symbols=aliases,
            definition_version=(
                self.DEFINITION_VERSION
            ),
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

    @staticmethod
    def _normalized_symbol(
        value: Any,
    ) -> str:

        return "".join(
            character
            for character
            in str(
                value
            ).upper()
            if character.isalnum()
        )

    @classmethod
    def _gold_request(
        cls,
        requested_symbol: str,
    ) -> bool:

        normalized = cls._normalized_symbol(
            requested_symbol
        )

        return (
            normalized
            in {
                "",
                "AUTO",
            }
            or
            normalized.startswith(
                "XAUUSD"
            )
            or
            normalized.startswith(
                "GOLD"
            )
        )

    @staticmethod
    def _positive_history_count(
        value: Any,
    ) -> int:

        if isinstance(
            value,
            bool,
        ):

            raise ValueError(
                "INVALID_HISTORY_BAR_COUNT"
            )

        try:

            number = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "INVALID_HISTORY_BAR_COUNT"
            ) from exc

        if (
            not math.isfinite(
                number
            )
            or
            number <= 0
            or
            not number.is_integer()
        ):

            raise ValueError(
                "INVALID_HISTORY_BAR_COUNT"
            )

        return int(
            number
        )

    def _make_evidence(
        self,
        *,
        requested_symbol: Any,
        resolved_symbol: Any,
        history_bar_count: Any,
        symbol_info: Any,
        source: str,
    ) -> BrokerResolvedInstrumentEvidence:

        requested = str(
            requested_symbol
        ).strip()

        resolved = str(
            resolved_symbol
        ).strip()

        if not resolved:

            raise ValueError(
                "RESOLVED_SYMBOL_MISSING"
            )

        if not self._has_fields(
            symbol_info,
            self._SYMBOL_INFO_FIELDS,
        ):

            raise ValueError(
                "INVALID_SYMBOL_INFO_SHAPE"
            )

        info_name = str(
            symbol_info.name
        ).strip()

        base = str(
            symbol_info.currency_base
        ).strip().upper()

        profit = str(
            symbol_info.currency_profit
        ).strip().upper()

        description = str(
            getattr(
                symbol_info,
                "description",
                "",
            )
            or
            ""
        ).strip()

        if not info_name:

            raise ValueError(
                "SYMBOL_INFO_NAME_MISSING"
            )

        if info_name != resolved:

            raise ValueError(
                "RESOLVED_SYMBOL_INFO_NAME_MISMATCH"
            )

        if not self._gold_request(
            requested
        ):

            raise ValueError(
                "REQUESTED_SYMBOL_NOT_XAUUSD_FAMILY"
            )

        if not self.definition.accepts_broker_symbol(
            resolved
        ):

            raise ValueError(
                "RESOLVED_SYMBOL_NOT_IN_XAUUSD_ALLOWLIST"
            )

        if base != "XAU":

            raise ValueError(
                "RESOLVED_SYMBOL_BASE_NOT_XAU"
            )

        if profit != "USD":

            raise ValueError(
                "RESOLVED_SYMBOL_PROFIT_NOT_USD"
            )

        return BrokerResolvedInstrumentEvidence(
            requested_symbol=requested,
            resolved_symbol=resolved,
            symbol_info_name=info_name,
            currency_base=base,
            currency_profit=profit,
            description=description,
            history_bar_count=(
                self._positive_history_count(
                    history_bar_count
                )
            ),
            source=str(
                source
            ).strip().upper(),
            live_authorized=False,
        )

    def _invalid(
        self,
        reason: str,
        *,
        requested_symbol: str = "",
        resolved_symbol: str = "",
        evidence: BrokerResolvedInstrumentEvidence | None = None,
    ) -> BrokerInstrumentContextBindingResult:

        return BrokerInstrumentContextBindingResult(
            valid=False,
            bound=False,
            reason=reason,
            action="NO_ACTION",
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            canonical_symbol=(
                self.CANONICAL_SYMBOL
            ),
            asset_class=(
                self.ASSET_CLASS
            ),
            requested_symbol=(
                requested_symbol
            ),
            resolved_symbol=(
                resolved_symbol
            ),
            definition_fingerprint=(
                self.definition.fingerprint
            ),
            evidence_fingerprint=(
                evidence.fingerprint
                if evidence is not None
                else ""
            ),
            context_identity_fingerprint="",
            evidence=evidence,
            context=None,
        )

    def _bind(
        self,
        *,
        evidence: BrokerResolvedInstrumentEvidence,
        broker_id: str,
        account_scope_id: str,
        execution_environment: str,
        contract_spec_id: str,
        data_schema_version: str,
        feature_contract_version: str,
    ) -> BrokerInstrumentContextBindingResult:

        try:

            context = InstrumentContext(
                definition=(
                    self.definition
                ),
                broker_id=broker_id,
                broker_symbol=(
                    evidence.resolved_symbol
                ),
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

        except InstrumentIsolationError as exc:

            return self._invalid(
                str(
                    exc
                ),
                requested_symbol=(
                    evidence.requested_symbol
                ),
                resolved_symbol=(
                    evidence.resolved_symbol
                ),
                evidence=evidence,
            )

        if bool(
            context.live_authorized
        ):

            return self._invalid(
                (
                    "INSTRUMENT_CONTEXT_"
                    "LIVE_AUTHORIZATION_NOT_ALLOWED"
                ),
                requested_symbol=(
                    evidence.requested_symbol
                ),
                resolved_symbol=(
                    evidence.resolved_symbol
                ),
                evidence=evidence,
            )

        return BrokerInstrumentContextBindingResult(
            valid=True,
            bound=True,
            reason=(
                "OK_XAUUSD_INSTRUMENT_CONTEXT_BOUND"
            ),
            action=(
                "USE_CANONICAL_XAUUSD_"
                "INSTRUMENT_CONTEXT"
            ),
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            canonical_symbol=(
                self.CANONICAL_SYMBOL
            ),
            asset_class=(
                self.ASSET_CLASS
            ),
            requested_symbol=(
                evidence.requested_symbol
            ),
            resolved_symbol=(
                evidence.resolved_symbol
            ),
            definition_fingerprint=(
                self.definition.fingerprint
            ),
            evidence_fingerprint=(
                evidence.fingerprint
            ),
            context_identity_fingerprint=(
                context.identity_fingerprint
            ),
            evidence=evidence,
            context=context,
        )

    def bind_fetcher_resolution(
        self,
        *,
        fetcher_state: Any,
        symbol_info: Any,
        broker_id: str,
        account_scope_id: str,
        execution_environment: str,
        contract_spec_id: str,
        data_schema_version: str,
        feature_contract_version: str,
    ) -> BrokerInstrumentContextBindingResult:

        if not self._has_fields(
            fetcher_state,
            self._FETCHER_FIELDS,
        ):

            return self._invalid(
                "INVALID_FETCHER_RESOLUTION_STATE"
            )

        requested = str(
            fetcher_state.last_requested_symbol
        ).strip()

        resolved = str(
            fetcher_state.last_resolved_symbol
        ).strip()

        try:

            evidence = self._make_evidence(
                requested_symbol=(
                    requested
                ),
                resolved_symbol=(
                    resolved
                ),
                history_bar_count=(
                    fetcher_state.last_bar_count
                ),
                symbol_info=(
                    symbol_info
                ),
                source=(
                    "MT5_DATA_FETCHER"
                ),
            )

        except ValueError as exc:

            return self._invalid(
                str(
                    exc
                ),
                requested_symbol=(
                    requested
                ),
                resolved_symbol=(
                    resolved
                ),
            )

        return self._bind(
            evidence=evidence,
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

    def bind_history_export(
        self,
        *,
        export_metadata: Mapping[str, Any],
        symbol_info: Any,
        broker_id: str,
        account_scope_id: str,
        execution_environment: str,
        contract_spec_id: str,
        data_schema_version: str,
        feature_contract_version: str,
    ) -> BrokerInstrumentContextBindingResult:

        required = (
            "requested_symbol",
            "resolved_symbol",
            "bars",
        )

        if (
            not isinstance(
                export_metadata,
                Mapping,
            )
            or
            not all(
                key
                in export_metadata
                for key
                in required
            )
        ):

            return self._invalid(
                "INVALID_HISTORY_EXPORT_METADATA"
            )

        requested = str(
            export_metadata[
                "requested_symbol"
            ]
        ).strip()

        resolved = str(
            export_metadata[
                "resolved_symbol"
            ]
        ).strip()

        try:

            evidence = self._make_evidence(
                requested_symbol=(
                    requested
                ),
                resolved_symbol=(
                    resolved
                ),
                history_bar_count=(
                    export_metadata[
                        "bars"
                    ]
                ),
                symbol_info=(
                    symbol_info
                ),
                source=(
                    "HISTORY_DOWNLOADER_EXPORT"
                ),
            )

        except ValueError as exc:

            return self._invalid(
                str(
                    exc
                ),
                requested_symbol=(
                    requested
                ),
                resolved_symbol=(
                    resolved
                ),
            )

        return self._bind(
            evidence=evidence,
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