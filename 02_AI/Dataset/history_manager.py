"""
===============================================================================
Module      : history_manager.py
Project     : PulseViper XAU AI
Version     : 2.0
Purpose     : Canonical Instrument-Aware Historical Dataset Builder
===============================================================================

The HistoryManager is now the canonical dataset-building entrypoint.

Unlike the legacy HistoryDownloader path, this manager:
- requires a verified InstrumentContext
- fetches the exact context broker symbol
- rejects broker resolution drift
- validates market history
- stamps every row with instrument identity
- materializes immutable content-addressed datasets
- writes lineage manifests
- never authorizes execution
"""

from __future__ import annotations

import importlib

from typing import Any, Iterable

import MetaTrader5 as mt5


fetcher_module: Any = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
)

exporter_module: Any = importlib.import_module(
    "02_AI.Dataset.export_dataset"
)


default_fetcher: Any = (
    fetcher_module.fetcher
)

default_exporter: Any = (
    exporter_module.exporter
)


class HistoryManager:

    TIMEFRAMES: dict[
        str,
        int,
    ] = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
    }

    def __init__(
        self,
        *,
        fetcher: Any | None = None,
        exporter: Any | None = None,
    ) -> None:

        self.fetcher = (
            fetcher
            if fetcher is not None
            else
            default_fetcher
        )

        self.exporter = (
            exporter
            if exporter is not None
            else
            default_exporter
        )

        self.last_materializations: list[
            Any
        ] = []

    # =========================================================================
    # Validation
    # =========================================================================

    @staticmethod
    def _validate_context(
        context: Any,
    ) -> None:

        if context is None:

            raise ValueError(
                "InstrumentContext is required"
            )

        required = (
            "canonical_symbol",
            "asset_class",
            "broker_id",
            "broker_symbol",
            "account_scope_id",
            "execution_environment",
            "contract_spec_id",
            "data_schema_version",
            "feature_contract_version",
            "identity_fingerprint",
            "live_authorized",
        )

        missing = [
            name
            for name
            in required
            if not hasattr(
                context,
                name,
            )
        ]

        if missing:

            raise ValueError(
                (
                    "Invalid InstrumentContext; "
                    "missing: "
                    +
                    ", ".join(
                        missing
                    )
                )
            )

        if bool(
            context.live_authorized
        ):

            raise ValueError(
                "Live-authorized context rejected"
            )

        if not str(
            context.canonical_symbol
        ).strip():

            raise ValueError(
                "canonical_symbol is required"
            )

        if not str(
            context.broker_symbol
        ).strip():

            raise ValueError(
                "broker_symbol is required"
            )

        if not str(
            context.identity_fingerprint
        ).strip():

            raise ValueError(
                "identity_fingerprint is required"
            )

    @classmethod
    def _resolve_timeframes(
        cls,
        timeframes: (
            Iterable[
                str
            ]
            |
            None
        ),
    ) -> tuple[
        str,
        ...
    ]:

        if timeframes is None:

            return tuple(
                cls.TIMEFRAMES.keys()
            )

        result: list[
            str
        ] = []

        seen: set[
            str
        ] = set()

        for raw in timeframes:

            name = str(
                raw
            ).strip().upper()

            if (
                not name
                or
                name
                not in cls.TIMEFRAMES
            ):

                raise ValueError(
                    (
                        "Unsupported timeframe: "
                        f"{raw}"
                    )
                )

            if name in seen:

                continue

            result.append(
                name
            )

            seen.add(
                name
            )

        if not result:

            raise ValueError(
                "At least one timeframe is required"
            )

        return tuple(
            result
        )

    # =========================================================================
    # Canonical build
    # =========================================================================

    def build_dataset(
        self,
        *,
        context: Any,
        bars: int = 100000,
        timeframes: (
            Iterable[
                str
            ]
            |
            None
        ) = None,
        symbol: str | None = None,
    ) -> list[
        Any
    ]:

        self._validate_context(
            context
        )

        if (
            isinstance(
                bars,
                bool,
            )
            or
            not isinstance(
                bars,
                int,
            )
            or
            bars <= 0
        ):

            raise ValueError(
                "bars must be a positive integer"
            )

        exact_broker_symbol = str(
            context.broker_symbol
        ).strip()

        requested_symbol = (
            exact_broker_symbol
            if symbol is None
            else
            str(
                symbol
            ).strip()
        )

        if (
            requested_symbol
            !=
            exact_broker_symbol
        ):

            raise ValueError(
                (
                    "Requested symbol does not match "
                    "verified InstrumentContext broker symbol"
                )
            )

        selected_timeframes = (
            self._resolve_timeframes(
                timeframes
            )
        )

        self.last_materializations = []

        for timeframe_name in selected_timeframes:

            timeframe_value = (
                self.TIMEFRAMES[
                    timeframe_name
                ]
            )

            dataframe = (
                self.fetcher.fetch(
                    symbol=(
                        exact_broker_symbol
                    ),
                    timeframe=(
                        timeframe_value
                    ),
                    bars=bars,
                )
            )

            resolved_symbol = str(
                getattr(
                    self.fetcher,
                    "last_resolved_symbol",
                    "",
                )
            ).strip()

            if (
                resolved_symbol
                !=
                exact_broker_symbol
            ):

                raise RuntimeError(
                    (
                        "BROKER_SYMBOL_CONTEXT_DRIFT: "
                        f"context={exact_broker_symbol}, "
                        f"resolved={resolved_symbol}"
                    )
                )

            if dataframe.empty:

                raise RuntimeError(
                    (
                        "No historical data returned "
                        f"for {timeframe_name}"
                    )
                )

            start_time: Any = None
            end_time: Any = None

            if (
                "time"
                in dataframe.columns
                and
                not dataframe.empty
            ):

                start_time = (
                    dataframe[
                        "time"
                    ].iloc[
                        0
                    ]
                )

                end_time = (
                    dataframe[
                        "time"
                    ].iloc[
                        -1
                    ]
                )

            source_metadata = {
                "source": (
                    "MT5_DATA_FETCHER"
                ),
                "requested_symbol": (
                    exact_broker_symbol
                ),
                "resolved_symbol": (
                    resolved_symbol
                ),
                "canonical_symbol": str(
                    context.canonical_symbol
                ),
                "asset_class": str(
                    context.asset_class
                ),
                "broker_id": str(
                    context.broker_id
                ),
                "account_scope_id": str(
                    context.account_scope_id
                ),
                "execution_environment": str(
                    context.execution_environment
                ),
                "contract_spec_id": str(
                    context.contract_spec_id
                ),
                "data_schema_version": str(
                    context.data_schema_version
                ),
                "feature_contract_version": str(
                    context.feature_contract_version
                ),
                "timeframe": (
                    timeframe_name
                ),
                "requested_bars": (
                    bars
                ),
                "returned_bars": int(
                    len(
                        dataframe
                    )
                ),
                "start_time": (
                    start_time
                ),
                "end_time": (
                    end_time
                ),
            }

            materialized = (
                self.exporter.materialize_history(
                    dataframe=(
                        dataframe
                    ),
                    context=context,
                    source_metadata=(
                        source_metadata
                    ),
                )
            )

            self.last_materializations.append(
                materialized
            )

        return list(
            self.last_materializations
        )


history = HistoryManager()