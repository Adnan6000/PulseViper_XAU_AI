"""Read-only Exness DEMO XAUUSD InstrumentContext attestation operation.

Safety:
- no order_send/order_check
- no position/order modification
- no live authorization
- REAL accounts fail closed

v1.1 adds a read-only MT5 symbol-catalog readiness pass before invoking the
existing Gold resolver, plus exact resolver diagnostics. Symbol matching rules
are not broadened and no fallback symbol is silently accepted.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Callable, Sequence

VERSION = "1.1"

MODE = (
    "EXNESS_DEMO_XAUUSD_READ_ONLY_"
    "CONTEXT_ATTESTATION_OPERATION_ONLY"
)


@dataclass(frozen=True)
class ResolverReadinessEvidence:
    attempt_count: int = 0
    symbol_catalog_count: int = 0
    gold_candidates: tuple[str, ...] = ()
    resolver_error: str = ""
    mt5_error: str = ""


@dataclass(frozen=True)
class ExnessDemoXAUUSDAttestationResult:
    valid: bool
    reason: str
    action: str
    mode: str
    version: str
    live_authorized: bool
    initialized: bool
    terminal_connected: bool
    demo_account_verified: bool
    broker_verified: bool
    requested_symbol: str
    resolved_symbol: str
    history_bar_count: int
    broker_id: str
    account_scope_id: str
    account_identity_fingerprint: str
    symbol_attestation_fingerprint: str
    contract_spec_id: str
    context_identity_fingerprint: str
    symbol_attestation_reason: str
    binding_reason: str
    context: Any
    resolver_attempt_count: int = 0
    symbol_catalog_count: int = 0
    resolver_gold_candidates: tuple[str, ...] = ()
    resolver_error: str = ""
    mt5_error: str = ""

    def to_document(
        self,
    ) -> dict[str, Any]:

        context_document = None

        if (
            self.context is not None
            and
            hasattr(
                self.context,
                "identity_document",
            )
        ):
            context_document = (
                self.context.identity_document()
            )

        return {
            "valid": self.valid,
            "reason": self.reason,
            "action": self.action,
            "mode": self.mode,
            "version": self.version,
            "live_authorized": False,
            "initialized": self.initialized,
            "terminal_connected": (
                self.terminal_connected
            ),
            "demo_account_verified": (
                self.demo_account_verified
            ),
            "broker_verified": (
                self.broker_verified
            ),
            "requested_symbol": (
                self.requested_symbol
            ),
            "resolved_symbol": (
                self.resolved_symbol
            ),
            "history_bar_count": (
                self.history_bar_count
            ),
            "broker_id": self.broker_id,
            "account_scope_id": (
                self.account_scope_id
            ),
            "account_identity_fingerprint": (
                self.account_identity_fingerprint
            ),
            "symbol_attestation_fingerprint": (
                self.symbol_attestation_fingerprint
            ),
            "contract_spec_id": (
                self.contract_spec_id
            ),
            "context_identity_fingerprint": (
                self.context_identity_fingerprint
            ),
            "symbol_attestation_reason": (
                self.symbol_attestation_reason
            ),
            "binding_reason": (
                self.binding_reason
            ),
            "resolver_attempt_count": (
                self.resolver_attempt_count
            ),
            "symbol_catalog_count": (
                self.symbol_catalog_count
            ),
            "resolver_gold_candidates": list(
                self.resolver_gold_candidates
            ),
            "resolver_error": (
                self.resolver_error
            ),
            "mt5_error": (
                self.mt5_error
            ),
            "context": context_document,
        }


def canonical_hash(
    document: Any,
) -> str:

    payload = json.dumps(
        document,
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
        payload
    ).hexdigest()


def field(
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

    return getattr(
        value,
        name,
        default,
    )


def last_error_text(
    api: Any,
) -> str:

    try:
        return str(
            api.last_error()
        )

    except Exception:
        return "unavailable"


def account_identity_fingerprint(
    account_info: Any,
) -> str:

    return canonical_hash(
        {
            "login": str(
                field(
                    account_info,
                    "login",
                    "",
                )
            ),
            "server": str(
                field(
                    account_info,
                    "server",
                    "",
                )
            ).strip(),
            "company": str(
                field(
                    account_info,
                    "company",
                    "",
                )
            ).strip(),
            "trade_mode": int(
                field(
                    account_info,
                    "trade_mode",
                    -1,
                )
            ),
            "currency": str(
                field(
                    account_info,
                    "currency",
                    "",
                )
            ).strip().upper(),
        }
    )


def derive_contract_spec_id(
    *,
    broker_id: str,
    attestation: Any,
) -> str:

    document = {
        "canonical_symbol": "XAUUSD",
        "asset_class": "METAL",
        "broker_id": str(
            broker_id
        ).strip().upper(),
        "broker_symbol": str(
            attestation.name
        ),
        "currency_base": str(
            attestation.currency_base
        ).upper(),
        "currency_profit": str(
            attestation.currency_profit
        ).upper(),
        "digits": int(
            attestation.digits
        ),
        "point": float(
            attestation.point
        ),
        "trade_contract_size": float(
            attestation.trade_contract_size
        ),
        "volume_min": float(
            attestation.volume_min
        ),
        "volume_max": float(
            attestation.volume_max
        ),
        "volume_step": float(
            attestation.volume_step
        ),
    }

    digest = canonical_hash(
        document
    )

    return (
        f"{str(broker_id).strip().upper()}_"
        f"XAUUSD_SPEC_"
        f"{digest[:16].upper()}"
    )


def _gold_candidates_from_symbols(
    symbols: Sequence[Any],
) -> tuple[str, ...]:

    names: list[str] = []

    for item in symbols:

        name = str(
            field(
                item,
                "name",
                "",
            )
        ).strip()

        description = str(
            field(
                item,
                "description",
                "",
            )
        ).strip()

        base = str(
            field(
                item,
                "currency_base",
                "",
            )
        ).strip().upper()

        profit = str(
            field(
                item,
                "currency_profit",
                "",
            )
        ).strip().upper()

        if (
            "XAU"
            in
            name.upper()
            or
            "GOLD"
            in
            name.upper()
            or
            "GOLD"
            in
            description.upper()
            or
            base
            ==
            "XAU"
            or
            profit
            ==
            "XAU"
        ):

            if name:
                names.append(
                    name
                )

    return tuple(
        sorted(
            set(
                names
            )
        )
    )


def resolve_with_readiness(
    *,
    api: Any,
    fetcher: Any,
    requested_symbol: str,
    timeframe: int,
    max_attempts: int = 3,
) -> tuple[
    str,
    ResolverReadinessEvidence,
]:
    """
    Warm the read-only MT5 symbol catalog, then invoke the existing resolver.

    No discovered candidate is used as a fallback. The existing resolver must
    still accept/probe the symbol itself.
    """

    if (
        isinstance(
            max_attempts,
            bool,
        )
        or
        not isinstance(
            max_attempts,
            int,
        )
        or
        max_attempts
        <=
        0
    ):

        raise ValueError(
            "max_attempts must be a positive integer"
        )

    catalog_count = 0

    gold_candidates: tuple[
        str,
        ...
    ] = ()

    resolver_error = ""

    mt5_error = ""

    for attempt in range(
        1,
        max_attempts
        +
        1,
    ):

        try:

            raw_symbols = (
                api.symbols_get()
            )

            symbols = (
                tuple(
                    raw_symbols
                )
                if raw_symbols
                is not None
                else
                ()
            )

            catalog_count = len(
                symbols
            )

            gold_candidates = (
                _gold_candidates_from_symbols(
                    symbols
                )
            )

        except Exception as exc:

            resolver_error = (
                "symbols_get "
                f"{type(exc).__name__}: {exc}"
            )

            mt5_error = (
                last_error_text(
                    api
                )
            )

        try:

            resolved = str(
                fetcher.resolve_symbol(
                    requested_symbol=(
                        requested_symbol
                    ),
                    timeframe=timeframe,
                )
            ).strip()

            if resolved:

                return (
                    resolved,
                    ResolverReadinessEvidence(
                        attempt_count=(
                            attempt
                        ),
                        symbol_catalog_count=(
                            catalog_count
                        ),
                        gold_candidates=(
                            gold_candidates
                        ),
                        resolver_error="",
                        mt5_error=(
                            last_error_text(
                                api
                            )
                        ),
                    ),
                )

            resolver_error = (
                "RuntimeError: resolver "
                "returned an empty symbol"
            )

        except Exception as exc:

            resolver_error = (
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            mt5_error = (
                last_error_text(
                    api
                )
            )

    return (
        "",
        ResolverReadinessEvidence(
            attempt_count=(
                max_attempts
            ),
            symbol_catalog_count=(
                catalog_count
            ),
            gold_candidates=(
                gold_candidates
            ),
            resolver_error=(
                resolver_error
            ),
            mt5_error=(
                mt5_error
            ),
        ),
    )


def _invalid(
    *,
    reason: str,
    initialized: bool = False,
    terminal_connected: bool = False,
    demo_account_verified: bool = False,
    broker_verified: bool = False,
    requested_symbol: str = "",
    resolved_symbol: str = "",
    history_bar_count: int = 0,
    broker_id: str = "EXNESS",
    account_scope_id: str = "PRIMARY_DEMO",
    account_fingerprint: str = "",
    symbol_fingerprint: str = "",
    contract_spec_id: str = "",
    symbol_reason: str = "",
    binding_reason: str = "",
    resolver_evidence: (
        ResolverReadinessEvidence
        |
        None
    ) = None,
) -> ExnessDemoXAUUSDAttestationResult:

    evidence = (
        resolver_evidence
        if resolver_evidence
        is not None
        else
        ResolverReadinessEvidence()
    )

    return ExnessDemoXAUUSDAttestationResult(
        valid=False,
        reason=reason,
        action="NO_ACTION",
        mode=MODE,
        version=VERSION,
        live_authorized=False,
        initialized=initialized,
        terminal_connected=(
            terminal_connected
        ),
        demo_account_verified=(
            demo_account_verified
        ),
        broker_verified=(
            broker_verified
        ),
        requested_symbol=(
            requested_symbol
        ),
        resolved_symbol=(
            resolved_symbol
        ),
        history_bar_count=(
            history_bar_count
        ),
        broker_id=broker_id,
        account_scope_id=(
            account_scope_id
        ),
        account_identity_fingerprint=(
            account_fingerprint
        ),
        symbol_attestation_fingerprint=(
            symbol_fingerprint
        ),
        contract_spec_id=(
            contract_spec_id
        ),
        context_identity_fingerprint="",
        symbol_attestation_reason=(
            symbol_reason
        ),
        binding_reason=(
            binding_reason
        ),
        context=None,
        resolver_attempt_count=(
            evidence.attempt_count
        ),
        symbol_catalog_count=(
            evidence.symbol_catalog_count
        ),
        resolver_gold_candidates=(
            evidence.gold_candidates
        ),
        resolver_error=(
            evidence.resolver_error
        ),
        mt5_error=(
            evidence.mt5_error
        ),
    )


def run_attestation(
    *,
    requested_symbol: str = "XAUUSDm",
    probe_bars: int = 32,
    broker_id: str = "EXNESS",
    account_scope_id: str = "PRIMARY_DEMO",
    data_schema_version: str = "MARKET_V1",
    feature_contract_version: str = "FEATURES_V1",
    resolver_attempts: int = 3,
    mt5_api: Any | None = None,
    resolver: (
        Callable[
            [
                str,
                int,
            ],
            str,
        ]
        |
        None
    ) = None,
) -> ExnessDemoXAUUSDAttestationResult:

    requested = str(
        requested_symbol
    ).strip()

    broker = str(
        broker_id
    ).strip().upper()

    scope = str(
        account_scope_id
    ).strip().upper()

    if not requested:

        return _invalid(
            reason=(
                "INVALID_REQUESTED_SYMBOL"
            ),
            broker_id=broker,
            account_scope_id=scope,
        )

    if (
        isinstance(
            probe_bars,
            bool,
        )
        or
        not isinstance(
            probe_bars,
            int,
        )
        or
        probe_bars
        <=
        0
    ):

        return _invalid(
            reason=(
                "INVALID_PROBE_BAR_COUNT"
            ),
            requested_symbol=(
                requested
            ),
            broker_id=broker,
            account_scope_id=scope,
        )

    if (
        isinstance(
            resolver_attempts,
            bool,
        )
        or
        not isinstance(
            resolver_attempts,
            int,
        )
        or
        resolver_attempts
        <=
        0
    ):

        return _invalid(
            reason=(
                "INVALID_RESOLVER_ATTEMPT_COUNT"
            ),
            requested_symbol=(
                requested
            ),
            broker_id=broker,
            account_scope_id=scope,
        )

    api = (
        mt5_api
        if mt5_api
        is not None
        else
        importlib.import_module(
            "MetaTrader5"
        )
    )

    initialized = False

    account_fingerprint = ""

    resolver_evidence = (
        ResolverReadinessEvidence()
    )

    try:

        try:

            initialized = bool(
                api.initialize()
            )

        except Exception:

            return _invalid(
                reason=(
                    "MT5_INITIALIZE_EXCEPTION"
                ),
                requested_symbol=(
                    requested
                ),
                broker_id=broker,
                account_scope_id=scope,
            )

        if not initialized:

            return _invalid(
                reason=(
                    "MT5_INITIALIZE_FAILED"
                ),
                requested_symbol=(
                    requested
                ),
                broker_id=broker,
                account_scope_id=scope,
            )

        try:

            terminal = (
                api.terminal_info()
            )

        except Exception:

            return _invalid(
                reason=(
                    "MT5_TERMINAL_INFO_EXCEPTION"
                ),
                initialized=True,
                requested_symbol=(
                    requested
                ),
                broker_id=broker,
                account_scope_id=scope,
            )

        if terminal is None:

            return _invalid(
                reason=(
                    "MT5_TERMINAL_INFO_UNAVAILABLE"
                ),
                initialized=True,
                requested_symbol=(
                    requested
                ),
                broker_id=broker,
                account_scope_id=scope,
            )

        if not bool(
            field(
                terminal,
                "connected",
                False,
            )
        ):

            return _invalid(
                reason=(
                    "MT5_TERMINAL_NOT_CONNECTED"
                ),
                initialized=True,
                requested_symbol=(
                    requested
                ),
                broker_id=broker,
                account_scope_id=scope,
            )

        try:

            account = (
                api.account_info()
            )

        except Exception:

            return _invalid(
                reason=(
                    "MT5_ACCOUNT_INFO_EXCEPTION"
                ),
                initialized=True,
                terminal_connected=True,
                requested_symbol=(
                    requested
                ),
                broker_id=broker,
                account_scope_id=scope,
            )

        if account is None:

            return _invalid(
                reason=(
                    "MT5_ACCOUNT_INFO_UNAVAILABLE"
                ),
                initialized=True,
                terminal_connected=True,
                requested_symbol=(
                    requested
                ),
                broker_id=broker,
                account_scope_id=scope,
            )

        try:

            trade_mode = int(
                field(
                    account,
                    "trade_mode",
                    -1,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            return _invalid(
                reason=(
                    "INVALID_MT5_ACCOUNT_TRADE_MODE"
                ),
                initialized=True,
                terminal_connected=True,
                requested_symbol=(
                    requested
                ),
                broker_id=broker,
                account_scope_id=scope,
            )

        demo_constant = int(
            getattr(
                api,
                "ACCOUNT_TRADE_MODE_DEMO",
                0,
            )
        )

        if (
            trade_mode
            !=
            demo_constant
        ):

            return _invalid(
                reason=(
                    "ACTIVE_MT5_ACCOUNT_IS_NOT_DEMO"
                ),
                initialized=True,
                terminal_connected=True,
                requested_symbol=(
                    requested
                ),
                broker_id=broker,
                account_scope_id=scope,
            )

        server = str(
            field(
                account,
                "server",
                "",
            )
        ).strip()

        company = str(
            field(
                account,
                "company",
                "",
            )
        ).strip()

        broker_text = (
            f"{server} {company}"
        ).upper()

        if (
            broker
            and
            broker
            not in
            broker_text
        ):

            return _invalid(
                reason=(
                    "BROKER_IDENTITY_MISMATCH"
                ),
                initialized=True,
                terminal_connected=True,
                demo_account_verified=True,
                requested_symbol=(
                    requested
                ),
                broker_id=broker,
                account_scope_id=scope,
            )

        try:

            account_fingerprint = (
                account_identity_fingerprint(
                    account
                )
            )

        except Exception:

            return _invalid(
                reason=(
                    "ACCOUNT_IDENTITY_FINGERPRINT_FAILED"
                ),
                initialized=True,
                terminal_connected=True,
                demo_account_verified=True,
                broker_verified=True,
                requested_symbol=(
                    requested
                ),
                broker_id=broker,
                account_scope_id=scope,
            )

        timeframe = int(
            getattr(
                api,
                "TIMEFRAME_M1",
                1,
            )
        )

        if resolver is None:

            try:

                fetcher = (
                    importlib.import_module(
                        "02_AI.Dataset.data_fetcher"
                    )
                    .fetcher
                )

                (
                    resolved,
                    resolver_evidence,
                ) = resolve_with_readiness(
                    api=api,
                    fetcher=fetcher,
                    requested_symbol=(
                        requested
                    ),
                    timeframe=(
                        timeframe
                    ),
                    max_attempts=(
                        resolver_attempts
                    ),
                )

            except Exception as exc:

                resolved = ""

                resolver_evidence = (
                    ResolverReadinessEvidence(
                        resolver_error=(
                            f"{type(exc).__name__}: "
                            f"{exc}"
                        ),
                        mt5_error=(
                            last_error_text(
                                api
                            )
                        ),
                    )
                )

        else:

            try:

                resolved = str(
                    resolver(
                        requested,
                        timeframe,
                    )
                ).strip()

                resolver_evidence = (
                    ResolverReadinessEvidence(
                        attempt_count=1,
                        mt5_error=(
                            last_error_text(
                                api
                            )
                        ),
                    )
                )

            except Exception as exc:

                resolved = ""

                resolver_evidence = (
                    ResolverReadinessEvidence(
                        attempt_count=1,
                        resolver_error=(
                            f"{type(exc).__name__}: "
                            f"{exc}"
                        ),
                        mt5_error=(
                            last_error_text(
                                api
                            )
                        ),
                    )
                )

        if not resolved:

            return _invalid(
                reason=(
                    "XAUUSD_BROKER_SYMBOL_RESOLUTION_FAILED"
                ),
                initialized=True,
                terminal_connected=True,
                demo_account_verified=True,
                broker_verified=True,
                requested_symbol=(
                    requested
                ),
                broker_id=broker,
                account_scope_id=scope,
                account_fingerprint=(
                    account_fingerprint
                ),
                resolver_evidence=(
                    resolver_evidence
                ),
            )

        try:

            rates = (
                api.copy_rates_from_pos(
                    resolved,
                    timeframe,
                    0,
                    probe_bars,
                )
            )

        except Exception:

            return _invalid(
                reason=(
                    "MT5_HISTORY_PROBE_EXCEPTION"
                ),
                initialized=True,
                terminal_connected=True,
                demo_account_verified=True,
                broker_verified=True,
                requested_symbol=(
                    requested
                ),
                resolved_symbol=(
                    resolved
                ),
                broker_id=broker,
                account_scope_id=scope,
                account_fingerprint=(
                    account_fingerprint
                ),
                resolver_evidence=(
                    resolver_evidence
                ),
            )

        if rates is None:

            return _invalid(
                reason=(
                    "MT5_HISTORY_PROBE_UNAVAILABLE"
                ),
                initialized=True,
                terminal_connected=True,
                demo_account_verified=True,
                broker_verified=True,
                requested_symbol=(
                    requested
                ),
                resolved_symbol=(
                    resolved
                ),
                broker_id=broker,
                account_scope_id=scope,
                account_fingerprint=(
                    account_fingerprint
                ),
                resolver_evidence=(
                    resolver_evidence
                ),
            )

        try:

            history_count = len(
                rates
            )

        except TypeError:

            history_count = 0

        if (
            history_count
            <=
            0
        ):

            return _invalid(
                reason=(
                    "MT5_HISTORY_PROBE_EMPTY"
                ),
                initialized=True,
                terminal_connected=True,
                demo_account_verified=True,
                broker_verified=True,
                requested_symbol=(
                    requested
                ),
                resolved_symbol=(
                    resolved
                ),
                broker_id=broker,
                account_scope_id=scope,
                account_fingerprint=(
                    account_fingerprint
                ),
                resolver_evidence=(
                    resolver_evidence
                ),
            )

        adapter_module = (
            importlib.import_module(
                "02_AI.Dataset."
                "mt5_read_only_instrument_"
                "attestation_adapter"
            )
        )

        adapter = (
            adapter_module
            .MT5ReadOnlyInstrumentAttestationAdapter(
                mt5_api=api
            )
        )

        symbol_result = (
            adapter.read_symbol(
                expected_symbol=(
                    resolved
                )
            )
        )

        if (
            not bool(
                symbol_result.valid
            )
            or
            not bool(
                symbol_result.attested
            )
        ):

            return _invalid(
                reason=(
                    "MT5_SYMBOL_ATTESTATION_REJECTED"
                ),
                initialized=True,
                terminal_connected=True,
                demo_account_verified=True,
                broker_verified=True,
                requested_symbol=(
                    requested
                ),
                resolved_symbol=(
                    resolved
                ),
                history_bar_count=(
                    history_count
                ),
                broker_id=broker,
                account_scope_id=scope,
                account_fingerprint=(
                    account_fingerprint
                ),
                symbol_reason=str(
                    symbol_result.reason
                ),
                resolver_evidence=(
                    resolver_evidence
                ),
            )

        attestation = (
            symbol_result.attestation
        )

        symbol_fingerprint = str(
            symbol_result
            .attestation_fingerprint
        )

        try:

            contract_spec_id = (
                derive_contract_spec_id(
                    broker_id=broker,
                    attestation=(
                        attestation
                    ),
                )
            )

        except Exception:

            return _invalid(
                reason=(
                    "CONTRACT_SPEC_ID_DERIVATION_FAILED"
                ),
                initialized=True,
                terminal_connected=True,
                demo_account_verified=True,
                broker_verified=True,
                requested_symbol=(
                    requested
                ),
                resolved_symbol=(
                    resolved
                ),
                history_bar_count=(
                    history_count
                ),
                broker_id=broker,
                account_scope_id=scope,
                account_fingerprint=(
                    account_fingerprint
                ),
                symbol_fingerprint=(
                    symbol_fingerprint
                ),
                symbol_reason=str(
                    symbol_result.reason
                ),
                resolver_evidence=(
                    resolver_evidence
                ),
            )

        fetcher_state = (
            SimpleNamespace(
                last_requested_symbol=(
                    requested
                ),
                last_resolved_symbol=(
                    resolved
                ),
                last_bar_count=(
                    history_count
                ),
            )
        )

        binding_module = (
            importlib.import_module(
                "02_AI.Dataset."
                "broker_instrument_context_binding"
            )
        )

        binder = (
            binding_module
            .XAUUSDBrokerInstrumentContextBinder()
        )

        binding = (
            binder.bind_fetcher_resolution(
                fetcher_state=(
                    fetcher_state
                ),
                symbol_info=(
                    attestation
                ),
                broker_id=broker,
                account_scope_id=scope,
                execution_environment=(
                    "DEMO"
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
                binding.valid
            )
            or
            not bool(
                binding.bound
            )
            or
            binding.context
            is None
        ):

            return _invalid(
                reason=(
                    "XAUUSD_CONTEXT_BINDING_REJECTED"
                ),
                initialized=True,
                terminal_connected=True,
                demo_account_verified=True,
                broker_verified=True,
                requested_symbol=(
                    requested
                ),
                resolved_symbol=(
                    resolved
                ),
                history_bar_count=(
                    history_count
                ),
                broker_id=broker,
                account_scope_id=scope,
                account_fingerprint=(
                    account_fingerprint
                ),
                symbol_fingerprint=(
                    symbol_fingerprint
                ),
                contract_spec_id=(
                    contract_spec_id
                ),
                symbol_reason=str(
                    symbol_result.reason
                ),
                binding_reason=str(
                    binding.reason
                ),
                resolver_evidence=(
                    resolver_evidence
                ),
            )

        context = binding.context

        if (
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
                context.execution_environment
            )
            !=
            "DEMO"
            or
            str(
                context.broker_symbol
            )
            !=
            resolved
        ):

            return _invalid(
                reason=(
                    "ATTESTED_CONTEXT_BOUNDARY_VIOLATION"
                ),
                initialized=True,
                terminal_connected=True,
                demo_account_verified=True,
                broker_verified=True,
                requested_symbol=(
                    requested
                ),
                resolved_symbol=(
                    resolved
                ),
                history_bar_count=(
                    history_count
                ),
                broker_id=broker,
                account_scope_id=scope,
                account_fingerprint=(
                    account_fingerprint
                ),
                symbol_fingerprint=(
                    symbol_fingerprint
                ),
                contract_spec_id=(
                    contract_spec_id
                ),
                symbol_reason=str(
                    symbol_result.reason
                ),
                binding_reason=str(
                    binding.reason
                ),
                resolver_evidence=(
                    resolver_evidence
                ),
            )

        return ExnessDemoXAUUSDAttestationResult(
            valid=True,
            reason=(
                "OK_EXNESS_DEMO_XAUUSD_CONTEXT_ATTESTED"
            ),
            action=(
                "USE_ATTESTED_XAUUSD_DEMO_CONTEXT"
            ),
            mode=MODE,
            version=VERSION,
            live_authorized=False,
            initialized=True,
            terminal_connected=True,
            demo_account_verified=True,
            broker_verified=True,
            requested_symbol=(
                requested
            ),
            resolved_symbol=(
                resolved
            ),
            history_bar_count=(
                history_count
            ),
            broker_id=broker,
            account_scope_id=scope,
            account_identity_fingerprint=(
                account_fingerprint
            ),
            symbol_attestation_fingerprint=(
                symbol_fingerprint
            ),
            contract_spec_id=(
                contract_spec_id
            ),
            context_identity_fingerprint=str(
                context.identity_fingerprint
            ),
            symbol_attestation_reason=str(
                symbol_result.reason
            ),
            binding_reason=str(
                binding.reason
            ),
            context=context,
            resolver_attempt_count=(
                resolver_evidence.attempt_count
            ),
            symbol_catalog_count=(
                resolver_evidence.symbol_catalog_count
            ),
            resolver_gold_candidates=(
                resolver_evidence.gold_candidates
            ),
            resolver_error="",
            mt5_error=(
                resolver_evidence.mt5_error
            ),
        )

    finally:

        if initialized:

            try:
                api.shutdown()

            except Exception:
                pass


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Read-only Exness DEMO XAUUSD "
            "InstrumentContext attestation."
        )
    )

    parser.add_argument(
        "--symbol",
        default="XAUUSDm",
    )

    parser.add_argument(
        "--probe-bars",
        type=int,
        default=32,
    )

    parser.add_argument(
        "--broker-id",
        default="EXNESS",
    )

    parser.add_argument(
        "--account-scope-id",
        default="PRIMARY_DEMO",
    )

    parser.add_argument(
        "--data-schema-version",
        default="MARKET_V1",
    )

    parser.add_argument(
        "--feature-contract-version",
        default="FEATURES_V1",
    )

    parser.add_argument(
        "--resolver-attempts",
        type=int,
        default=3,
    )

    args = parser.parse_args()

    result = run_attestation(
        requested_symbol=(
            args.symbol
        ),
        probe_bars=(
            args.probe_bars
        ),
        broker_id=(
            args.broker_id
        ),
        account_scope_id=(
            args.account_scope_id
        ),
        data_schema_version=(
            args.data_schema_version
        ),
        feature_contract_version=(
            args.feature_contract_version
        ),
        resolver_attempts=(
            args.resolver_attempts
        ),
    )

    print(
        json.dumps(
            result.to_document(),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
    )

    return (
        0
        if result.valid
        else
        2
    )


if __name__ == "__main__":

    raise SystemExit(
        main()
    )