"""Canonical instrument identity and isolation context.

This module is intentionally broker-I/O free. It defines the identity contract
used to keep market data, model artifacts, execution telemetry, journals, and
future learning state isolated by instrument.

A context may describe a REAL environment, but this module never authorizes
live execution. ``live_authorized`` is always False.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


class InstrumentIsolationError(ValueError):
    """Raised when instrument identity or namespace isolation is violated."""


SUPPORTED_ASSET_CLASSES = frozenset(
    {
        "METAL",
        "CRYPTO",
        "INDEX",
        "FOREX",
        "ENERGY",
        "EQUITY",
        "OTHER",
    }
)

SUPPORTED_EXECUTION_ENVIRONMENTS = frozenset(
    {
        "RESEARCH",
        "DEMO",
        "REAL",
    }
)

SUPPORTED_NAMESPACE_SCOPES = frozenset(
    {
        "INSTRUMENT",
        "LEARNING",
        "EXECUTION",
    }
)

_CANONICAL_SYMBOL_RE = re.compile(
    r"^[A-Z0-9][A-Z0-9._-]{0,63}$"
)

_SAFE_TOKEN_RE = re.compile(
    r"^[A-Z0-9][A-Z0-9._-]{0,127}$"
)

_SAFE_PURPOSE_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"
)


def _canonical_json(
    document: Any,
) -> str:

    try:

        return json.dumps(
            document,
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
            ensure_ascii=False,
            allow_nan=False,
        )

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise InstrumentIsolationError(
            "NON_CANONICAL_INSTRUMENT_DOCUMENT"
        ) from exc


def _fingerprint(
    document: Any,
) -> str:

    return hashlib.sha256(
        _canonical_json(
            document
        ).encode(
            "utf-8"
        )
    ).hexdigest()


def _normalized_token(
    value: Any,
    *,
    field: str,
) -> str:

    resolved = str(
        value
    ).strip().upper()

    if not _SAFE_TOKEN_RE.fullmatch(
        resolved
    ):

        raise InstrumentIsolationError(
            f"INVALID_{field}"
        )

    return resolved


def _canonical_symbol(
    value: Any,
) -> str:

    resolved = str(
        value
    ).strip().upper()

    if not _CANONICAL_SYMBOL_RE.fullmatch(
        resolved
    ):

        raise InstrumentIsolationError(
            "INVALID_CANONICAL_SYMBOL"
        )

    return resolved


def _broker_symbol(
    value: Any,
) -> str:

    resolved = str(
        value
    ).strip()

    if (
        not resolved
        or
        len(
            resolved
        )
        >
        64
    ):

        raise InstrumentIsolationError(
            "INVALID_BROKER_SYMBOL"
        )

    if resolved in {
        ".",
        "..",
    }:

        raise InstrumentIsolationError(
            "INVALID_BROKER_SYMBOL"
        )

    if any(
        character
        in resolved
        for character
        in (
            "/",
            "\\",
            "\x00",
        )
    ):

        raise InstrumentIsolationError(
            "INVALID_BROKER_SYMBOL"
        )

    if any(
        ord(
            character
        )
        <
        32
        for character
        in resolved
    ):

        raise InstrumentIsolationError(
            "INVALID_BROKER_SYMBOL"
        )

    return resolved


def _scope(
    value: Any,
) -> str:

    resolved = str(
        value
    ).strip().upper()

    if resolved not in SUPPORTED_NAMESPACE_SCOPES:

        raise InstrumentIsolationError(
            "INVALID_INSTRUMENT_NAMESPACE_SCOPE"
        )

    return resolved


@dataclass(
    frozen=True,
)
class InstrumentDefinition:
    """Explicit mapping from one canonical market to allowed broker symbols."""

    canonical_symbol: str

    asset_class: str

    broker_symbols: tuple[
        str,
        ...,
    ]

    definition_version: str = "1"

    def __post_init__(
        self,
    ) -> None:

        canonical = _canonical_symbol(
            self.canonical_symbol
        )

        asset_class = _normalized_token(
            self.asset_class,
            field="ASSET_CLASS",
        )

        if asset_class not in SUPPORTED_ASSET_CLASSES:

            raise InstrumentIsolationError(
                "UNSUPPORTED_ASSET_CLASS"
            )

        version = _normalized_token(
            self.definition_version,
            field="INSTRUMENT_DEFINITION_VERSION",
        )

        if (
            not isinstance(
                self.broker_symbols,
                tuple,
            )
            or
            not self.broker_symbols
        ):

            raise InstrumentIsolationError(
                "BROKER_SYMBOL_ALIASES_REQUIRED"
            )

        aliases = tuple(
            _broker_symbol(
                value
            )
            for value
            in self.broker_symbols
        )

        if (
            len(
                set(
                    aliases
                )
            )
            !=
            len(
                aliases
            )
        ):

            raise InstrumentIsolationError(
                "DUPLICATE_BROKER_SYMBOL_ALIAS"
            )

        if (
            len(
                {
                    value.casefold()
                    for value
                    in aliases
                }
            )
            !=
            len(
                aliases
            )
        ):

            raise InstrumentIsolationError(
                "AMBIGUOUS_BROKER_SYMBOL_ALIAS_CASE"
            )

        object.__setattr__(
            self,
            "canonical_symbol",
            canonical,
        )

        object.__setattr__(
            self,
            "asset_class",
            asset_class,
        )

        object.__setattr__(
            self,
            "definition_version",
            version,
        )

        object.__setattr__(
            self,
            "broker_symbols",
            tuple(
                sorted(
                    aliases
                )
            ),
        )

    def accepts_broker_symbol(
        self,
        broker_symbol: str,
    ) -> bool:

        return (
            _broker_symbol(
                broker_symbol
            )
            in
            self.broker_symbols
        )

    def to_document(
        self,
    ) -> dict[
        str,
        Any,
    ]:

        return {
            "canonical_symbol": (
                self.canonical_symbol
            ),
            "asset_class": (
                self.asset_class
            ),
            "broker_symbols": list(
                self.broker_symbols
            ),
            "definition_version": (
                self.definition_version
            ),
        }

    @property
    def fingerprint(
        self,
    ) -> str:

        return _fingerprint(
            self.to_document()
        )


@dataclass(
    frozen=True,
)
class InstrumentContext:
    """Immutable instrument + broker + account + schema isolation context."""

    definition: InstrumentDefinition

    broker_id: str

    broker_symbol: str

    account_scope_id: str

    execution_environment: str

    contract_spec_id: str

    data_schema_version: str

    feature_contract_version: str

    def __post_init__(
        self,
    ) -> None:

        if not isinstance(
            self.definition,
            InstrumentDefinition,
        ):

            raise InstrumentIsolationError(
                "INVALID_INSTRUMENT_DEFINITION"
            )

        broker_id = _normalized_token(
            self.broker_id,
            field="BROKER_ID",
        )

        broker_symbol = _broker_symbol(
            self.broker_symbol
        )

        account_scope = _normalized_token(
            self.account_scope_id,
            field="ACCOUNT_SCOPE_ID",
        )

        environment = _normalized_token(
            self.execution_environment,
            field="EXECUTION_ENVIRONMENT",
        )

        if (
            environment
            not in
            SUPPORTED_EXECUTION_ENVIRONMENTS
        ):

            raise InstrumentIsolationError(
                "UNSUPPORTED_EXECUTION_ENVIRONMENT"
            )

        contract_spec = _normalized_token(
            self.contract_spec_id,
            field="CONTRACT_SPEC_ID",
        )

        data_schema = _normalized_token(
            self.data_schema_version,
            field="DATA_SCHEMA_VERSION",
        )

        feature_contract = _normalized_token(
            self.feature_contract_version,
            field="FEATURE_CONTRACT_VERSION",
        )

        if not self.definition.accepts_broker_symbol(
            broker_symbol
        ):

            raise InstrumentIsolationError(
                "BROKER_SYMBOL_NOT_ALLOWED_FOR_CANONICAL_INSTRUMENT"
            )

        object.__setattr__(
            self,
            "broker_id",
            broker_id,
        )

        object.__setattr__(
            self,
            "broker_symbol",
            broker_symbol,
        )

        object.__setattr__(
            self,
            "account_scope_id",
            account_scope,
        )

        object.__setattr__(
            self,
            "execution_environment",
            environment,
        )

        object.__setattr__(
            self,
            "contract_spec_id",
            contract_spec,
        )

        object.__setattr__(
            self,
            "data_schema_version",
            data_schema,
        )

        object.__setattr__(
            self,
            "feature_contract_version",
            feature_contract,
        )

    @property
    def canonical_symbol(
        self,
    ) -> str:

        return (
            self.definition
            .canonical_symbol
        )

    @property
    def asset_class(
        self,
    ) -> str:

        return (
            self.definition
            .asset_class
        )

    @property
    def live_authorized(
        self,
    ) -> bool:

        return False

    def identity_document(
        self,
    ) -> dict[
        str,
        Any,
    ]:

        return {
            "definition_fingerprint": (
                self.definition
                .fingerprint
            ),
            "definition_version": (
                self.definition
                .definition_version
            ),
            "canonical_symbol": (
                self.canonical_symbol
            ),
            "asset_class": (
                self.asset_class
            ),
            "broker_id": (
                self.broker_id
            ),
            "broker_symbol": (
                self.broker_symbol
            ),
            "account_scope_id": (
                self.account_scope_id
            ),
            "execution_environment": (
                self.execution_environment
            ),
            "contract_spec_id": (
                self.contract_spec_id
            ),
            "data_schema_version": (
                self.data_schema_version
            ),
            "feature_contract_version": (
                self.feature_contract_version
            ),
            "live_authorized": False,
        }

    @property
    def identity_fingerprint(
        self,
    ) -> str:

        return _fingerprint(
            self.identity_document()
        )

    def instrument_scope_document(
        self,
    ) -> dict[
        str,
        Any,
    ]:

        return {
            "definition_fingerprint": (
                self.definition
                .fingerprint
            ),
            "canonical_symbol": (
                self.canonical_symbol
            ),
            "asset_class": (
                self.asset_class
            ),
        }

    def learning_scope_document(
        self,
    ) -> dict[
        str,
        Any,
    ]:

        return {
            "definition_fingerprint": (
                self.definition
                .fingerprint
            ),
            "canonical_symbol": (
                self.canonical_symbol
            ),
            "asset_class": (
                self.asset_class
            ),
            "broker_id": (
                self.broker_id
            ),
            "broker_symbol": (
                self.broker_symbol
            ),
            "contract_spec_id": (
                self.contract_spec_id
            ),
            "data_schema_version": (
                self.data_schema_version
            ),
            "feature_contract_version": (
                self.feature_contract_version
            ),
        }

    def execution_scope_document(
        self,
    ) -> dict[
        str,
        Any,
    ]:

        return (
            self.identity_document()
        )

    def scope_document(
        self,
        scope: str,
    ) -> dict[
        str,
        Any,
    ]:

        resolved = _scope(
            scope
        )

        if resolved == "INSTRUMENT":

            return (
                self.instrument_scope_document()
            )

        if resolved == "LEARNING":

            return (
                self.learning_scope_document()
            )

        return (
            self.execution_scope_document()
        )

    def scope_fingerprint(
        self,
        scope: str,
    ) -> str:

        return _fingerprint(
            self.scope_document(
                scope
            )
        )

    def assert_same_instrument(
        self,
        other: "InstrumentContext",
    ) -> None:

        self._assert_context(
            other
        )

        if (
            self.instrument_scope_document()
            !=
            other.instrument_scope_document()
        ):

            raise InstrumentIsolationError(
                "CROSS_INSTRUMENT_SCOPE_MISMATCH"
            )

    def assert_same_learning_scope(
        self,
        other: "InstrumentContext",
    ) -> None:

        self._assert_context(
            other
        )

        if (
            self.learning_scope_document()
            !=
            other.learning_scope_document()
        ):

            raise InstrumentIsolationError(
                "CROSS_LEARNING_SCOPE_MISMATCH"
            )

    def assert_same_execution_scope(
        self,
        other: "InstrumentContext",
    ) -> None:

        self._assert_context(
            other
        )

        if (
            self.execution_scope_document()
            !=
            other.execution_scope_document()
        ):

            raise InstrumentIsolationError(
                "CROSS_EXECUTION_SCOPE_MISMATCH"
            )

    @staticmethod
    def _assert_context(
        other: Any,
    ) -> None:

        if not isinstance(
            other,
            InstrumentContext,
        ):

            raise InstrumentIsolationError(
                "INVALID_COMPARISON_INSTRUMENT_CONTEXT"
            )

    def namespace(
        self,
        root: str | Path,
        purpose: str,
        *,
        scope: str = "EXECUTION",
    ) -> Path:

        resolved_scope = _scope(
            scope
        )

        resolved_purpose = str(
            purpose
        ).strip()

        if not _SAFE_PURPOSE_RE.fullmatch(
            resolved_purpose
        ):

            raise InstrumentIsolationError(
                "INVALID_INSTRUMENT_NAMESPACE_PURPOSE"
            )

        fingerprint = (
            self.scope_fingerprint(
                resolved_scope
            )[
                :20
            ]
        )

        return (
            Path(
                root
            )
            /
            "Instruments"
            /
            self.canonical_symbol
            /
            resolved_scope.lower()
            /
            f"scope_{fingerprint}"
            /
            resolved_purpose.lower()
        )

    def stamp_metadata(
        self,
        metadata: Mapping[
            str,
            Any,
        ]
        |
        None = None,
        *,
        scope: str = "EXECUTION",
    ) -> dict[
        str,
        Any,
    ]:

        resolved_scope = _scope(
            scope
        )

        result = dict(
            metadata
            or
            {}
        )

        identity_key = (
            "_pulseviper_instrument_identity"
        )

        scope_key = (
            "_pulseviper_instrument_scope"
        )

        expected_identity = (
            self.identity_document()
        )

        expected_scope = {
            "scope": (
                resolved_scope
            ),
            "fingerprint": (
                self.scope_fingerprint(
                    resolved_scope
                )
            ),
        }

        if (
            identity_key
            in result
            and
            result[
                identity_key
            ]
            !=
            expected_identity
        ):

            raise InstrumentIsolationError(
                "INSTRUMENT_METADATA_IDENTITY_MISMATCH"
            )

        if (
            scope_key
            in result
            and
            result[
                scope_key
            ]
            !=
            expected_scope
        ):

            raise InstrumentIsolationError(
                "INSTRUMENT_METADATA_SCOPE_MISMATCH"
            )

        result[
            identity_key
        ] = expected_identity

        result[
            scope_key
        ] = expected_scope

        return result

    def validate_metadata(
        self,
        metadata: Mapping[
            str,
            Any,
        ],
        *,
        scope: str = "EXECUTION",
    ) -> None:

        if not isinstance(
            metadata,
            Mapping,
        ):

            raise InstrumentIsolationError(
                "INVALID_INSTRUMENT_METADATA"
            )

        stamped = self.stamp_metadata(
            metadata,
            scope=scope,
        )

        if (
            dict(
                metadata
            )
            !=
            stamped
        ):

            raise InstrumentIsolationError(
                "INSTRUMENT_METADATA_MISSING_IDENTITY"
            )