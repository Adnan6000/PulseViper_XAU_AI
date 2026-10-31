"""
===============================================================================
Module      : data_fetcher.py
Project     : PulseViper XAU AI
Version     : 2.0
Purpose     : Broker-Safe MetaTrader 5 Historical Data Fetcher
===============================================================================

Responsibilities
----------------
- initialize/shutdown MetaTrader 5 safely
- resolve broker-specific XAU/Gold symbol names
- preserve explicitly requested symbols when available
- fall back from names such as XAUUSDm to XAUUSD / XAUUSD.a / GOLD, etc.
- verify that a candidate actually has history before selecting it
- fetch and validate OHLC data
- expose the resolved symbol for diagnostics

This module does NOT contain trading logic.
"""

from __future__ import annotations

from typing import Any

import MetaTrader5 as mt5
import pandas as pd


class MT5DataFetcher:
    """
    Robust MetaTrader 5 historical market-data fetcher.

    The trading system conceptually trades XAUUSD, but individual brokers may
    expose Gold using different symbol names, for example:

        XAUUSD
        XAUUSDm
        XAUUSD.a
        XAUUSD.pro
        GOLD
        GOLDm

    The fetcher therefore treats the requested symbol as a preference rather
    than blindly assuming that every broker exposes the same symbol name.
    """

    def __init__(
        self,
    ) -> None:

        self.last_requested_symbol: str = ""
        self.last_resolved_symbol: str = ""
        self.last_bar_count: int = 0

    # =========================================================================
    # MT5 lifecycle
    # =========================================================================

    @staticmethod
    def initialize() -> None:

        if not mt5.initialize():

            raise RuntimeError(
                "MT5 initialization failed: "
                f"{MT5DataFetcher._last_error_text()}"
            )

    @staticmethod
    def shutdown() -> None:

        mt5.shutdown()

    @staticmethod
    def _last_error_text() -> str:

        try:

            return str(
                mt5.last_error()
            )

        except Exception:

            return "unavailable"

    # =========================================================================
    # Symbol helpers
    # =========================================================================

    @staticmethod
    def _normalize_symbol_name(
        name: str,
    ) -> str:
        """
        Convert broker-specific symbol names into a normalized comparable form.

        Examples
        --------
        XAUUSD.a  -> XAUUSDA
        XAUUSD-m  -> XAUUSDM
        GOLD.pro  -> GOLDPRO
        """

        return "".join(
            character
            for character
            in name.upper()
            if character.isalnum()
        )

    @classmethod
    def _symbol_score(
        cls,
        symbol_info: Any,
        requested_symbol: str,
    ) -> int:
        """
        Rank a terminal symbol for XAUUSD / Gold relevance.

        Higher scores indicate a stronger candidate.
        """

        name = str(
            getattr(
                symbol_info,
                "name",
                "",
            )
        )

        description = str(
            getattr(
                symbol_info,
                "description",
                "",
            )
        )

        currency_base = str(
            getattr(
                symbol_info,
                "currency_base",
                "",
            )
        )

        currency_profit = str(
            getattr(
                symbol_info,
                "currency_profit",
                "",
            )
        )

        upper_name = (
            name.upper()
        )

        normalized_name = (
            cls._normalize_symbol_name(
                name
            )
        )

        upper_description = (
            description.upper()
        )

        requested_upper = (
            requested_symbol.upper()
        )

        normalized_requested = (
            cls._normalize_symbol_name(
                requested_symbol
            )
        )

        base_upper = (
            currency_base.upper()
        )

        profit_upper = (
            currency_profit.upper()
        )

        score = 0

        # =====================================================================
        # Explicit request
        #
        # If the requested broker symbol really exists, it gets the highest
        # priority.
        # =====================================================================

        if requested_upper not in (
            "",
            "AUTO",
        ):

            if (
                upper_name
                == requested_upper
            ):

                score += 100_000

            elif (
                normalized_requested
                and
                normalized_name
                == normalized_requested
            ):

                score += 95_000

        # =====================================================================
        # Canonical XAUUSD naming
        # =====================================================================

        if (
            normalized_name
            == "XAUUSD"
        ):

            score += 90_000

        elif normalized_name.startswith(
            "XAUUSD"
        ):

            score += 85_000

        elif (
            "XAUUSD"
            in normalized_name
        ):

            score += 80_000

        # =====================================================================
        # Common GOLD naming
        # =====================================================================

        if (
            normalized_name
            == "GOLD"
        ):

            score += 75_000

        elif normalized_name.startswith(
            "GOLD"
        ):

            score += 70_000

        elif (
            "GOLD"
            in normalized_name
        ):

            score += 65_000

        # =====================================================================
        # Symbol metadata
        #
        # Some brokers use unusual visible names while MT5 metadata still says
        # base=XAU and profit=USD.
        # =====================================================================

        if (
            base_upper
            == "XAU"
            and
            profit_upper
            == "USD"
        ):

            score += 60_000

        if (
            "GOLD"
            in upper_description
        ):

            score += 20_000

        # =====================================================================
        # Mild preference for Market Watch symbols
        # =====================================================================

        if bool(
            getattr(
                symbol_info,
                "visible",
                False,
            )
        ):

            score += 100

        if bool(
            getattr(
                symbol_info,
                "select",
                False,
            )
        ):

            score += 50

        # =====================================================================
        # Exclude unrelated instruments
        # =====================================================================

        is_xau_metadata = (
            base_upper
            == "XAU"
            and
            profit_upper
            == "USD"
        )

        if (
            "XAU"
            not in upper_name
            and
            "GOLD"
            not in upper_name
            and
            "GOLD"
            not in upper_description
            and
            not is_xau_metadata
        ):

            score -= 1_000_000

        return score

    @classmethod
    def _candidate_symbols(
        cls,
        requested_symbol: str,
    ) -> list[str]:
        """
        Build an ordered list of likely XAU/Gold broker symbols.
        """

        symbols: Any = (
            mt5.symbols_get()
        )

        if symbols is None:

            raise RuntimeError(
                "MT5 symbols_get() failed: "
                f"{cls._last_error_text()}"
            )

        scored: list[
            tuple[
                int,
                str,
            ]
        ] = []

        for symbol_info in symbols:

            name = str(
                getattr(
                    symbol_info,
                    "name",
                    "",
                )
            )

            if not name:

                continue

            score = cls._symbol_score(
                symbol_info,
                requested_symbol,
            )

            if score > 0:

                scored.append(
                    (
                        score,
                        name,
                    )
                )

        # Highest-quality symbols first.
        #
        # For equal scores:
        # - shorter names first
        # - alphabetical order for deterministic behavior

        scored.sort(
            key=lambda item: (
                -item[
                    0
                ],
                len(
                    item[
                        1
                    ]
                ),
                item[
                    1
                ],
            )
        )

        ordered: list[
            str
        ] = []

        seen: set[
            str
        ] = set()

        # =====================================================================
        # Explicit request always gets the first attempt.
        #
        # Even when terminal enumeration does not report it as expected, this
        # preserves normal exact-symbol behavior.
        # =====================================================================

        requested_upper = (
            requested_symbol.upper()
        )

        if requested_upper not in (
            "",
            "AUTO",
        ):

            ordered.append(
                requested_symbol
            )

            seen.add(
                requested_upper
            )

        # =====================================================================
        # Add discovered candidates
        # =====================================================================

        for (
            _,
            name,
        ) in scored:

            key = (
                name.upper()
            )

            if key in seen:

                continue

            ordered.append(
                name
            )

            seen.add(
                key
            )

        return ordered

    @staticmethod
    def _probe_symbol(
        symbol: str,
        timeframe: int,
        probe_bars: int = 10,
    ) -> bool:
        """
        Verify that:
        1. MT5 can select the symbol.
        2. The symbol actually returns historical bars.

        A symbol existing in the terminal does not automatically guarantee that
        useful history is available.
        """

        if not mt5.symbol_select(
            symbol,
            True,
        ):

            return False

        rates: Any = (
            mt5.copy_rates_from_pos(
                symbol,
                timeframe,
                0,
                probe_bars,
            )
        )

        if rates is None:

            return False

        try:

            return (
                len(
                    rates
                )
                > 0
            )

        except TypeError:

            return False

    @classmethod
    def resolve_symbol(
        cls,
        requested_symbol: str = "AUTO",
        timeframe: int = mt5.TIMEFRAME_M1,
    ) -> str:
        """
        Resolve a usable XAU/Gold broker symbol.

        Resolution order
        ----------------
        1. Explicit requested symbol.
        2. Broker XAUUSD variants.
        3. Broker GOLD variants.
        4. XAU/USD metadata candidates.

        Every candidate is tested for actual historical data.
        """

        candidates = (
            cls._candidate_symbols(
                requested_symbol
            )
        )

        if not candidates:

            raise RuntimeError(
                (
                    "No XAU/Gold-like symbols were found in the connected "
                    "MT5 terminal. Verify that the intended broker terminal "
                    "and account are open and connected."
                )
            )

        attempted: list[
            str
        ] = []

        for candidate in candidates:

            attempted.append(
                candidate
            )

            if cls._probe_symbol(
                candidate,
                timeframe,
            ):

                return candidate

        raise RuntimeError(
            (
                "XAU/Gold candidates were discovered, but none returned "
                "historical data. Tried: "
                +
                ", ".join(
                    attempted[
                        :20
                    ]
                )
                +
                ". MT5 last_error="
                +
                cls._last_error_text()
            )
        )

    # =========================================================================
    # Data conversion / validation
    # =========================================================================

    @staticmethod
    def _rates_to_frame(
        rates: Any,
        symbol: str,
    ) -> pd.DataFrame:
        """
        Convert MT5 rates to a clean chronological DataFrame.
        """

        frame = pd.DataFrame(
            rates
        )

        if frame.empty:

            raise RuntimeError(
                f"MT5 returned an empty dataset for {symbol}"
            )

        required = {
            "time",
            "open",
            "high",
            "low",
            "close",
        }

        missing = (
            required
            - set(
                frame.columns
            )
        )

        if missing:

            raise RuntimeError(
                (
                    "MT5 rates payload is missing columns: "
                    +
                    ", ".join(
                        sorted(
                            missing
                        )
                    )
                )
            )

        # =====================================================================
        # Timestamp
        #
        # MT5 rate timestamps represent UTC.
        #
        # Convert explicitly as UTC, then remove timezone information to remain
        # compatible with the project's existing naive datetime contract.
        # =====================================================================

        time_values: Any = (
            pd.to_datetime(
                frame[
                    "time"
                ],
                unit="s",
                utc=True,
                errors="coerce",
            )
        )

        frame[
            "time"
        ] = (
            time_values
            .dt
            .tz_convert(
                None
            )
        )

        # =====================================================================
        # OHLC numeric validation
        # =====================================================================

        for column in (
            "open",
            "high",
            "low",
            "close",
        ):

            numeric: Any = (
                pd.to_numeric(
                    frame[
                        column
                    ],
                    errors="coerce",
                )
            )

            frame[
                column
            ] = numeric

        # =====================================================================
        # Remove invalid rows
        # =====================================================================

        frame = (
            frame
            .dropna(
                subset=[
                    "time",
                    "open",
                    "high",
                    "low",
                    "close",
                ]
            )
        )

        # =====================================================================
        # Remove duplicate candles
        # =====================================================================

        frame = (
            frame
            .drop_duplicates(
                subset=[
                    "time"
                ],
                keep="last",
            )
        )

        # =====================================================================
        # Canonical chronological ordering
        # =====================================================================

        frame = (
            frame
            .sort_values(
                "time"
            )
            .reset_index(
                drop=True
            )
        )

        if frame.empty:

            raise RuntimeError(
                (
                    f"No valid OHLC bars remained for {symbol} "
                    "after validation"
                )
            )

        return frame

    # =========================================================================
    # Public fetch API
    # =========================================================================

    def fetch(
        self,
        symbol: str = "AUTO",
        timeframe: int = mt5.TIMEFRAME_M1,
        bars: int = 10000,
    ) -> pd.DataFrame:
        """
        Fetch validated historical bars.

        Existing code remains compatible with calls such as:

            fetcher.fetch(
                symbol="XAUUSDm",
                bars=30000,
            )

        If XAUUSDm does not exist at the connected broker, the fetcher
        automatically resolves the broker's actual Gold symbol.
        """

        if bars <= 0:

            raise ValueError(
                "bars must be greater than zero"
            )

        self.last_requested_symbol = str(
            symbol
        )

        self.last_resolved_symbol = ""
        self.last_bar_count = 0

        self.initialize()

        try:

            # =================================================================
            # Resolve broker symbol
            # =================================================================

            resolved_symbol = (
                self.resolve_symbol(
                    requested_symbol=(
                        symbol
                    ),
                    timeframe=(
                        timeframe
                    ),
                )
            )

            self.last_resolved_symbol = (
                resolved_symbol
            )

            # =================================================================
            # Report broker fallback
            # =================================================================

            if (
                str(
                    symbol
                ).upper()
                !=
                resolved_symbol.upper()
            ):

                print(
                    (
                        "[MT5DataFetcher] "
                        f"Requested '{symbol}' is unavailable; "
                        f"using broker symbol '{resolved_symbol}'."
                    )
                )

            # =================================================================
            # Final select
            # =================================================================

            if not mt5.symbol_select(
                resolved_symbol,
                True,
            ):

                raise RuntimeError(
                    (
                        "Cannot select resolved symbol "
                        f"{resolved_symbol}: "
                        f"{self._last_error_text()}"
                    )
                )

            # =================================================================
            # Fetch
            # =================================================================

            rates: Any = (
                mt5.copy_rates_from_pos(
                    resolved_symbol,
                    timeframe,
                    0,
                    bars,
                )
            )

            if rates is None:

                raise RuntimeError(
                    (
                        f"No data returned for {resolved_symbol}: "
                        f"{self._last_error_text()}"
                    )
                )

            # =================================================================
            # Convert and validate
            # =================================================================

            frame = (
                self._rates_to_frame(
                    rates,
                    resolved_symbol,
                )
            )

            self.last_bar_count = (
                len(
                    frame
                )
            )

            # =================================================================
            # History warning
            #
            # MT5 may return fewer bars than requested depending on terminal
            # history availability.
            # =================================================================

            if (
                len(
                    frame
                )
                < bars
            ):

                print(
                    (
                        "[MT5DataFetcher] "
                        f"Requested {bars} bars; "
                        f"MT5 returned {len(frame)} valid bars."
                    )
                )

            return frame

        finally:

            # MT5 should always shut down cleanly, including exceptions.
            self.shutdown()


# =============================================================================
# Global project fetcher
# =============================================================================

fetcher = (
    MT5DataFetcher()
)