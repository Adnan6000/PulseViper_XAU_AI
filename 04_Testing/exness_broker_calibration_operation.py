"""
===============================================================================
Module      : exness_broker_calibration_operation.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Read-Only Exness / MT5 Broker Calibration for XAUUSD Risk Design
===============================================================================

Purpose
-------
Collect real broker/account metadata required before redesigning PulseViper's
Risk Engine.

This operation inspects:

ACCOUNT
- account mode
- balance
- equity
- profit
- margin
- free margin
- margin level
- leverage
- currency
- trade permissions
- server/company

TERMINAL
- connection state
- terminal trade permission
- Python trading API state
- terminal/build metadata

SYMBOL
- resolved Gold symbol
- bid / ask
- live spread
- point / digits
- tick size
- tick value
- tick value profit/loss
- contract size
- volume min/max/step/limit
- stops level
- freeze level
- trade mode
- execution mode
- filling mode
- order mode
- margin properties

BROKER-AWARE CALIBRATION
- hypothetical BUY/SELL loss through mt5.order_calc_profit()
- hypothetical BUY/SELL margin through mt5.order_calc_margin()
- minimum-volume monetary exposure at multiple stop distances
- risk as % of account balance/equity

Safety
------
READ ONLY with respect to the broker account.

This file:
- does not place trades
- does not modify positions
- does not modify pending orders
- does not size a live trade
- does not modify production trade_ready
- does not modify LEI
- does not modify RWEI
- does not modify the existing RiskEngine
"""

from __future__ import annotations

import argparse
import importlib
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import MetaTrader5 as mt5


# =============================================================================
# Project path
# =============================================================================

PROJECT_ROOT = Path(
    __file__
).resolve().parents[
    1
]

if str(
    PROJECT_ROOT
) not in sys.path:

    sys.path.insert(
        0,
        str(
            PROJECT_ROOT
        ),
    )


# =============================================================================
# Existing broker-safe symbol resolver
# =============================================================================

fetcher: Any = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher


# =============================================================================
# Display helpers
# =============================================================================


def section(
    title: str,
) -> None:

    print()

    print(
        "=" * 118
    )

    print(
        title
    )

    print(
        "=" * 118
    )


def line(
    label: str,
    value: Any,
) -> None:

    print(
        f"{label:<34}: {value}"
    )


def fmt_number(
    value: Any,
    digits: int = 6,
) -> str:

    if value is None:
        return "N/A"

    try:

        number = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return str(
            value
        )

    if not math.isfinite(
        number
    ):

        return "N/A"

    return (
        f"{number:.{digits}f}"
        .rstrip(
            "0"
        )
        .rstrip(
            "."
        )
    )


def fmt_money(
    value: Any,
    currency: str,
) -> str:

    if value is None:
        return "N/A"

    try:

        number = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return "N/A"

    if not math.isfinite(
        number
    ):

        return "N/A"

    return (
        f"{number:,.4f} {currency}"
    )


def safe_get(
    obj: Any,
    name: str,
    default: Any = None,
) -> Any:

    if obj is None:
        return default

    return getattr(
        obj,
        name,
        default,
    )


def last_error_text() -> str:

    try:

        return str(
            mt5.last_error()
        )

    except Exception:

        return "unavailable"


# =============================================================================
# Enum helpers
# =============================================================================


def enum_label(
    value: Any,
    names: tuple[
        str,
        ...,
    ],
) -> str:

    for name in names:

        constant = getattr(
            mt5,
            name,
            None,
        )

        if (
            constant is not None
            and
            value == constant
        ):

            return (
                f"{name} ({value})"
            )

    return str(
        value
    )


def bitmask_labels(
    value: Any,
    names: tuple[
        str,
        ...,
    ],
) -> str:

    try:

        numeric = int(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return str(
            value
        )

    matched: list[
        str
    ] = []

    for name in names:

        constant = getattr(
            mt5,
            name,
            None,
        )

        if constant is None:
            continue

        try:

            flag = int(
                constant
            )

        except (
            TypeError,
            ValueError,
        ):

            continue

        if (
            flag != 0
            and
            (
                numeric
                &
                flag
            )
            ==
            flag
        ):

            matched.append(
                name
            )

    if not matched:

        return str(
            numeric
        )

    return (
        f"{numeric} ["
        +
        ", ".join(
            matched
        )
        +
        "]"
    )


# =============================================================================
# Parsing
# =============================================================================


def parse_positive_numbers(
    text: str,
    argument_name: str,
) -> list[
    float
]:

    result: list[
        float
    ] = []

    for raw in text.split(
        ","
    ):

        raw = raw.strip()

        if not raw:
            continue

        try:

            value = float(
                raw
            )

        except ValueError as exc:

            raise ValueError(
                f"Invalid {argument_name} value: {raw}"
            ) from exc

        if (
            not math.isfinite(
                value
            )
            or
            value <= 0.0
        ):

            raise ValueError(
                f"{argument_name} values must be > 0"
            )

        result.append(
            value
        )

    if not result:

        raise ValueError(
            f"No valid {argument_name} values supplied"
        )

    return result


# =============================================================================
# Volume normalization
# =============================================================================


def decimal_places(
    value: float,
) -> int:

    text = (
        f"{value:.10f}"
        .rstrip(
            "0"
        )
        .rstrip(
            "."
        )
    )

    if "." not in text:
        return 0

    return len(
        text.split(
            "."
        )[
            1
        ]
    )


def normalize_volume(
    requested: float,
    volume_min: float,
    volume_max: float,
    volume_step: float,
) -> float | None:

    if (
        not math.isfinite(
            requested
        )
        or
        not math.isfinite(
            volume_min
        )
        or
        not math.isfinite(
            volume_max
        )
        or
        not math.isfinite(
            volume_step
        )
    ):
        return None

    if (
        volume_min <= 0.0
        or
        volume_max <= 0.0
        or
        volume_step <= 0.0
    ):
        return None

    requested = max(
        volume_min,
        min(
            volume_max,
            requested,
        ),
    )

    steps = math.floor(
        (
            requested
            /
            volume_step
        )
        +
        1e-9
    )

    normalized = (
        steps
        *
        volume_step
    )

    if normalized < volume_min:

        normalized = volume_min

    normalized = min(
        volume_max,
        normalized,
    )

    return round(
        normalized,
        max(
            2,
            decimal_places(
                volume_step
            ),
        ),
    )


def build_probe_volumes(
    symbol_info: Any,
    requested_volumes: list[
        float
    ] | None,
) -> list[
    float
]:

    volume_min = float(
        safe_get(
            symbol_info,
            "volume_min",
            0.0,
        )
        or
        0.0
    )

    volume_max = float(
        safe_get(
            symbol_info,
            "volume_max",
            0.0,
        )
        or
        0.0
    )

    volume_step = float(
        safe_get(
            symbol_info,
            "volume_step",
            0.0,
        )
        or
        0.0
    )

    if (
        volume_min <= 0.0
        or
        volume_max <= 0.0
        or
        volume_step <= 0.0
    ):

        raise RuntimeError(
            "Broker returned invalid volume min/max/step metadata"
        )

    raw = (
        requested_volumes
        if requested_volumes is not None
        else
        [
            volume_min,
            max(
                volume_min,
                0.01,
            ),
            max(
                volume_min,
                0.10,
            ),
            max(
                volume_min,
                1.00,
            ),
        ]
    )

    result: list[
        float
    ] = []

    seen: set[
        float
    ] = set()

    for requested in raw:

        normalized = normalize_volume(
            requested=requested,
            volume_min=volume_min,
            volume_max=volume_max,
            volume_step=volume_step,
        )

        if normalized is None:
            continue

        if normalized in seen:
            continue

        result.append(
            normalized
        )

        seen.add(
            normalized
        )

    result.sort()

    return result


# =============================================================================
# MT5 calculation helpers
# =============================================================================


def calc_profit(
    action: int,
    symbol: str,
    volume: float,
    price_open: float,
    price_close: float,
) -> float | None:

    result = mt5.order_calc_profit(
        action,
        symbol,
        volume,
        price_open,
        price_close,
    )

    if result is None:
        return None

    try:

        value = float(
            result
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    if not math.isfinite(
        value
    ):

        return None

    return value


def calc_margin(
    action: int,
    symbol: str,
    volume: float,
    price: float,
) -> float | None:

    result = mt5.order_calc_margin(
        action,
        symbol,
        volume,
        price,
    )

    if result is None:
        return None

    try:

        value = float(
            result
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    if not math.isfinite(
        value
    ):

        return None

    return value


def pct(
    amount: float | None,
    base: float,
) -> float | None:

    if (
        amount is None
        or
        base <= 0.0
        or
        not math.isfinite(
            base
        )
    ):

        return None

    return (
        abs(
            amount
        )
        /
        base
        *
        100.0
    )


# =============================================================================
# Simple table
# =============================================================================


def print_table(
    rows: list[
        dict[
            str,
            Any,
        ]
    ],
    columns: tuple[
        str,
        ...,
    ],
) -> None:

    if not rows:

        print(
            "No rows."
        )

        return

    widths: dict[
        str,
        int
    ] = {}

    for column in columns:

        widths[
            column
        ] = max(
            len(
                column
            ),
            max(
                len(
                    str(
                        row.get(
                            column,
                            "",
                        )
                    )
                )
                for row in rows
            ),
        )

    header = "  ".join(
        column.ljust(
            widths[
                column
            ]
        )
        for column in columns
    )

    print(
        header
    )

    print(
        "  ".join(
            "-" * widths[
                column
            ]
            for column in columns
        )
    )

    for row in rows:

        print(
            "  ".join(
                str(
                    row.get(
                        column,
                        "",
                    )
                ).ljust(
                    widths[
                        column
                    ]
                )
                for column in columns
            )
        )


# =============================================================================
# Main
# =============================================================================


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "PulseViper read-only Exness / MT5 "
            "broker calibration operation v1.0"
        )
    )

    parser.add_argument(
        "--symbol",
        type=str,
        default="XAUUSDm",
    )

    parser.add_argument(
        "--distances",
        type=str,
        default="50,100,250,500,1000",
        help=(
            "Hypothetical stop distances in broker points, "
            "comma separated."
        ),
    )

    parser.add_argument(
        "--volumes",
        type=str,
        default="",
        help=(
            "Optional probe volumes, comma separated. "
            "Default uses broker minimum plus 0.01/0.10/1.00 "
            "where valid."
        ),
    )

    args = parser.parse_args()

    distances = parse_positive_numbers(
        args.distances,
        "--distances",
    )

    requested_volumes = (
        parse_positive_numbers(
            args.volumes,
            "--volumes",
        )
        if args.volumes.strip()
        else
        None
    )

    initialized = False

    # =========================================================================
    # Header
    # =========================================================================

    section(
        "PulseViper XAU AI — "
        "EXNESS BROKER CALIBRATION v1.0"
    )

    line(
        "Requested symbol",
        args.symbol,
    )

    line(
        "Broker access",
        "READ ONLY",
    )

    line(
        "Orders",
        "DISABLED",
    )

    line(
        "Position modification",
        "DISABLED",
    )

    line(
        "Risk Engine wiring",
        "DISABLED",
    )

    line(
        "Production trade_ready",
        "FROZEN",
    )

    try:

        # =====================================================================
        # Initialize MT5
        # =====================================================================

        fetcher.initialize()

        initialized = True

        # =====================================================================
        # Terminal
        # =====================================================================

        terminal = mt5.terminal_info()

        if terminal is None:

            raise RuntimeError(
                "mt5.terminal_info() failed: "
                +
                last_error_text()
            )

        version = mt5.version()

        section(
            "MT5 TERMINAL"
        )

        line(
            "MetaTrader5 Python package",
            getattr(
                mt5,
                "__version__",
                "UNKNOWN",
            ),
        )

        line(
            "Terminal version",
            version,
        )

        line(
            "Connected",
            safe_get(
                terminal,
                "connected",
                "UNKNOWN",
            ),
        )

        line(
            "Terminal trade_allowed",
            safe_get(
                terminal,
                "trade_allowed",
                "UNKNOWN",
            ),
        )

        line(
            "Terminal tradeapi_disabled",
            safe_get(
                terminal,
                "tradeapi_disabled",
                "UNKNOWN",
            ),
        )

        line(
            "Terminal company",
            safe_get(
                terminal,
                "company",
                "UNKNOWN",
            ),
        )

        line(
            "Terminal name",
            safe_get(
                terminal,
                "name",
                "UNKNOWN",
            ),
        )

        line(
            "Terminal build",
            safe_get(
                terminal,
                "build",
                "UNKNOWN",
            ),
        )

        line(
            "Ping last",
            safe_get(
                terminal,
                "ping_last",
                "UNKNOWN",
            ),
        )

        # =====================================================================
        # Account
        # =====================================================================

        account = mt5.account_info()

        if account is None:

            raise RuntimeError(
                "mt5.account_info() failed: "
                +
                last_error_text()
            )

        currency = str(
            safe_get(
                account,
                "currency",
                "UNKNOWN",
            )
        )

        balance = float(
            safe_get(
                account,
                "balance",
                0.0,
            )
            or
            0.0
        )

        equity = float(
            safe_get(
                account,
                "equity",
                0.0,
            )
            or
            0.0
        )

        margin = float(
            safe_get(
                account,
                "margin",
                0.0,
            )
            or
            0.0
        )

        margin_free = float(
            safe_get(
                account,
                "margin_free",
                0.0,
            )
            or
            0.0
        )

        section(
            "ACCOUNT"
        )

        line(
            "Login",
            safe_get(
                account,
                "login",
                "UNKNOWN",
            ),
        )

        line(
            "Account mode",
            enum_label(
                safe_get(
                    account,
                    "trade_mode",
                    None,
                ),
                (
                    "ACCOUNT_TRADE_MODE_DEMO",
                    "ACCOUNT_TRADE_MODE_CONTEST",
                    "ACCOUNT_TRADE_MODE_REAL",
                ),
            ),
        )

        line(
            "Server",
            safe_get(
                account,
                "server",
                "UNKNOWN",
            ),
        )

        line(
            "Broker/company",
            safe_get(
                account,
                "company",
                "UNKNOWN",
            ),
        )

        line(
            "Currency",
            currency,
        )

        line(
            "Currency digits",
            safe_get(
                account,
                "currency_digits",
                "UNKNOWN",
            ),
        )

        line(
            "Leverage",
            safe_get(
                account,
                "leverage",
                "UNKNOWN",
            ),
        )

        line(
            "Balance",
            fmt_money(
                balance,
                currency,
            ),
        )

        line(
            "Equity",
            fmt_money(
                equity,
                currency,
            ),
        )

        line(
            "Floating profit",
            fmt_money(
                safe_get(
                    account,
                    "profit",
                    None,
                ),
                currency,
            ),
        )

        line(
            "Used margin",
            fmt_money(
                margin,
                currency,
            ),
        )

        line(
            "Free margin",
            fmt_money(
                margin_free,
                currency,
            ),
        )

        line(
            "Margin level %",
            fmt_number(
                safe_get(
                    account,
                    "margin_level",
                    None,
                ),
                3,
            ),
        )

        line(
            "Margin call level",
            safe_get(
                account,
                "margin_so_call",
                "UNKNOWN",
            ),
        )

        line(
            "Stop-out level",
            safe_get(
                account,
                "margin_so_so",
                "UNKNOWN",
            ),
        )

        line(
            "Account trade_allowed",
            safe_get(
                account,
                "trade_allowed",
                "UNKNOWN",
            ),
        )

        line(
            "Expert trading allowed",
            safe_get(
                account,
                "trade_expert",
                "UNKNOWN",
            ),
        )

        line(
            "Margin mode",
            safe_get(
                account,
                "margin_mode",
                "UNKNOWN",
            ),
        )

        line(
            "Active positions",
            mt5.positions_total(),
        )

        line(
            "Active orders",
            mt5.orders_total(),
        )

        legacy_one_pct = pct(
            1.0,
            balance,
        )

        line(
            "Legacy fixed 1 / balance %",
            (
                fmt_number(
                    legacy_one_pct,
                    4,
                )
                if legacy_one_pct is not None
                else
                "N/A"
            ),
        )

        # =====================================================================
        # Resolve Gold symbol
        # =====================================================================

        resolved_symbol = fetcher.resolve_symbol(
            requested_symbol=args.symbol,
            timeframe=mt5.TIMEFRAME_M1,
        )

        if not mt5.symbol_select(
            resolved_symbol,
            True,
        ):

            raise RuntimeError(
                f"Unable to select {resolved_symbol}: "
                +
                last_error_text()
            )

        symbol_info = mt5.symbol_info(
            resolved_symbol
        )

        if symbol_info is None:

            raise RuntimeError(
                f"symbol_info({resolved_symbol}) failed: "
                +
                last_error_text()
            )

        tick = mt5.symbol_info_tick(
            resolved_symbol
        )

        if tick is None:

            raise RuntimeError(
                f"symbol_info_tick({resolved_symbol}) failed: "
                +
                last_error_text()
            )

        point = float(
            safe_get(
                symbol_info,
                "point",
                0.0,
            )
            or
            0.0
        )

        digits = int(
            safe_get(
                symbol_info,
                "digits",
                0,
            )
            or
            0
        )

        bid = float(
            safe_get(
                tick,
                "bid",
                0.0,
            )
            or
            0.0
        )

        ask = float(
            safe_get(
                tick,
                "ask",
                0.0,
            )
            or
            0.0
        )

        if (
            point <= 0.0
            or
            bid <= 0.0
            or
            ask <= 0.0
            or
            ask < bid
        ):

            raise RuntimeError(
                "Invalid broker point/bid/ask metadata"
            )

        spread_price = (
            ask
            -
            bid
        )

        spread_points_live = (
            spread_price
            /
            point
        )

        tick_time = None

        tick_time_msc = safe_get(
            tick,
            "time_msc",
            None,
        )

        if tick_time_msc is not None:

            try:

                tick_time = datetime.fromtimestamp(
                    float(
                        tick_time_msc
                    )
                    /
                    1000.0,
                    tz=timezone.utc,
                )

            except (
                TypeError,
                ValueError,
                OSError,
            ):

                tick_time = None

        # =====================================================================
        # Symbol metadata
        # =====================================================================

        section(
            "RESOLVED GOLD SYMBOL"
        )

        line(
            "Requested symbol",
            args.symbol,
        )

        line(
            "Resolved symbol",
            resolved_symbol,
        )

        line(
            "Description",
            safe_get(
                symbol_info,
                "description",
                "UNKNOWN",
            ),
        )

        line(
            "Path",
            safe_get(
                symbol_info,
                "path",
                "UNKNOWN",
            ),
        )

        line(
            "Currency base",
            safe_get(
                symbol_info,
                "currency_base",
                "UNKNOWN",
            ),
        )

        line(
            "Currency profit",
            safe_get(
                symbol_info,
                "currency_profit",
                "UNKNOWN",
            ),
        )

        line(
            "Currency margin",
            safe_get(
                symbol_info,
                "currency_margin",
                "UNKNOWN",
            ),
        )

        line(
            "Visible",
            safe_get(
                symbol_info,
                "visible",
                "UNKNOWN",
            ),
        )

        line(
            "Selected",
            safe_get(
                symbol_info,
                "select",
                "UNKNOWN",
            ),
        )

        line(
            "Bid",
            fmt_number(
                bid,
                digits,
            ),
        )

        line(
            "Ask",
            fmt_number(
                ask,
                digits,
            ),
        )

        line(
            "Live spread price",
            fmt_number(
                spread_price,
                digits,
            ),
        )

        line(
            "Live spread points",
            fmt_number(
                spread_points_live,
                3,
            ),
        )

        line(
            "Symbol reported spread",
            safe_get(
                symbol_info,
                "spread",
                "UNKNOWN",
            ),
        )

        line(
            "Spread float",
            safe_get(
                symbol_info,
                "spread_float",
                "UNKNOWN",
            ),
        )

        line(
            "Tick UTC time",
            tick_time,
        )

        # =====================================================================
        # Contract / tick properties
        # =====================================================================

        section(
            "CONTRACT / TICK / VOLUME METADATA"
        )

        line(
            "Digits",
            digits,
        )

        line(
            "Point",
            fmt_number(
                point,
                10,
            ),
        )

        line(
            "Trade tick size",
            fmt_number(
                safe_get(
                    symbol_info,
                    "trade_tick_size",
                    None,
                ),
                10,
            ),
        )

        line(
            "Trade tick value",
            fmt_number(
                safe_get(
                    symbol_info,
                    "trade_tick_value",
                    None,
                ),
                10,
            ),
        )

        line(
            "Tick value profit",
            fmt_number(
                safe_get(
                    symbol_info,
                    "trade_tick_value_profit",
                    None,
                ),
                10,
            ),
        )

        line(
            "Tick value loss",
            fmt_number(
                safe_get(
                    symbol_info,
                    "trade_tick_value_loss",
                    None,
                ),
                10,
            ),
        )

        line(
            "Contract size",
            fmt_number(
                safe_get(
                    symbol_info,
                    "trade_contract_size",
                    None,
                ),
                6,
            ),
        )

        line(
            "Volume minimum",
            fmt_number(
                safe_get(
                    symbol_info,
                    "volume_min",
                    None,
                ),
                8,
            ),
        )

        line(
            "Volume maximum",
            fmt_number(
                safe_get(
                    symbol_info,
                    "volume_max",
                    None,
                ),
                8,
            ),
        )

        line(
            "Volume step",
            fmt_number(
                safe_get(
                    symbol_info,
                    "volume_step",
                    None,
                ),
                8,
            ),
        )

        line(
            "Volume limit",
            fmt_number(
                safe_get(
                    symbol_info,
                    "volume_limit",
                    None,
                ),
                8,
            ),
        )

        # =====================================================================
        # Execution constraints
        # =====================================================================

        section(
            "BROKER EXECUTION CONSTRAINTS"
        )

        line(
            "Symbol trade mode",
            enum_label(
                safe_get(
                    symbol_info,
                    "trade_mode",
                    None,
                ),
                (
                    "SYMBOL_TRADE_MODE_DISABLED",
                    "SYMBOL_TRADE_MODE_LONGONLY",
                    "SYMBOL_TRADE_MODE_SHORTONLY",
                    "SYMBOL_TRADE_MODE_CLOSEONLY",
                    "SYMBOL_TRADE_MODE_FULL",
                ),
            ),
        )

        line(
            "Execution mode",
            enum_label(
                safe_get(
                    symbol_info,
                    "trade_exemode",
                    None,
                ),
                (
                    "SYMBOL_TRADE_EXECUTION_REQUEST",
                    "SYMBOL_TRADE_EXECUTION_INSTANT",
                    "SYMBOL_TRADE_EXECUTION_MARKET",
                    "SYMBOL_TRADE_EXECUTION_EXCHANGE",
                ),
            ),
        )

        line(
            "Filling mode raw",
            bitmask_labels(
                safe_get(
                    symbol_info,
                    "filling_mode",
                    None,
                ),
                (
                    "SYMBOL_FILLING_FOK",
                    "SYMBOL_FILLING_IOC",
                    "SYMBOL_FILLING_BOC",
                ),
            ),
        )

        line(
            "Order mode raw",
            bitmask_labels(
                safe_get(
                    symbol_info,
                    "order_mode",
                    None,
                ),
                (
                    "SYMBOL_ORDER_MARKET",
                    "SYMBOL_ORDER_LIMIT",
                    "SYMBOL_ORDER_STOP",
                    "SYMBOL_ORDER_STOP_LIMIT",
                    "SYMBOL_ORDER_SL",
                    "SYMBOL_ORDER_TP",
                    "SYMBOL_ORDER_CLOSEBY",
                ),
            ),
        )

        stops_level = float(
            safe_get(
                symbol_info,
                "trade_stops_level",
                0.0,
            )
            or
            0.0
        )

        freeze_level = float(
            safe_get(
                symbol_info,
                "trade_freeze_level",
                0.0,
            )
            or
            0.0
        )

        line(
            "Stops level points",
            fmt_number(
                stops_level,
                3,
            ),
        )

        line(
            "Stops level price distance",
            fmt_number(
                stops_level
                *
                point,
                digits,
            ),
        )

        line(
            "Freeze level points",
            fmt_number(
                freeze_level,
                3,
            ),
        )

        line(
            "Freeze level price distance",
            fmt_number(
                freeze_level
                *
                point,
                digits,
            ),
        )

        line(
            "Trade calc mode",
            safe_get(
                symbol_info,
                "trade_calc_mode",
                "UNKNOWN",
            ),
        )

        line(
            "Margin initial",
            fmt_number(
                safe_get(
                    symbol_info,
                    "margin_initial",
                    None,
                ),
                8,
            ),
        )

        line(
            "Margin maintenance",
            fmt_number(
                safe_get(
                    symbol_info,
                    "margin_maintenance",
                    None,
                ),
                8,
            ),
        )

        line(
            "Margin hedged",
            fmt_number(
                safe_get(
                    symbol_info,
                    "margin_hedged",
                    None,
                ),
                8,
            ),
        )

        line(
            "Margin hedged use leg",
            safe_get(
                symbol_info,
                "margin_hedged_use_leg",
                "UNKNOWN",
            ),
        )

        # =====================================================================
        # Valid calibration volumes
        # =====================================================================

        probe_volumes = build_probe_volumes(
            symbol_info=symbol_info,
            requested_volumes=requested_volumes,
        )

        section(
            "CALIBRATION VOLUMES"
        )

        line(
            "Volumes",
            ", ".join(
                fmt_number(
                    value,
                    8,
                )
                for value
                in probe_volumes
            ),
        )

        # =====================================================================
        # Margin estimates
        # =====================================================================

        section(
            "HYPOTHETICAL MARGIN CALIBRATION"
        )

        margin_rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for volume in probe_volumes:

            buy_margin = calc_margin(
                mt5.ORDER_TYPE_BUY,
                resolved_symbol,
                volume,
                ask,
            )

            sell_margin = calc_margin(
                mt5.ORDER_TYPE_SELL,
                resolved_symbol,
                volume,
                bid,
            )

            buy_pct_free = pct(
                buy_margin,
                margin_free,
            )

            sell_pct_free = pct(
                sell_margin,
                margin_free,
            )

            margin_rows.append(
                {
                    "volume": (
                        fmt_number(
                            volume,
                            8,
                        )
                    ),

                    "buy_margin": (
                        fmt_money(
                            buy_margin,
                            currency,
                        )
                    ),

                    "sell_margin": (
                        fmt_money(
                            sell_margin,
                            currency,
                        )
                    ),

                    "buy_%free": (
                        fmt_number(
                            buy_pct_free,
                            3,
                        )
                        if buy_pct_free is not None
                        else
                        "N/A"
                    ),

                    "sell_%free": (
                        fmt_number(
                            sell_pct_free,
                            3,
                        )
                        if sell_pct_free is not None
                        else
                        "N/A"
                    ),
                }
            )

        print_table(
            margin_rows,
            (
                "volume",
                "buy_margin",
                "sell_margin",
                "buy_%free",
                "sell_%free",
            ),
        )

        # =====================================================================
        # Profit/loss calibration
        # =====================================================================

        section(
            "BROKER-AWARE STOP LOSS CALIBRATION"
        )

        line(
            "Method",
            "mt5.order_calc_profit()",
        )

        line(
            "BUY paper entry",
            fmt_number(
                ask,
                digits,
            ),
        )

        line(
            "SELL paper entry",
            fmt_number(
                bid,
                digits,
            ),
        )

        line(
            "Distance unit",
            "BROKER POINTS",
        )

        loss_rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for volume in probe_volumes:

            for distance_points in distances:

                price_distance = (
                    distance_points
                    *
                    point
                )

                buy_stop = (
                    ask
                    -
                    price_distance
                )

                sell_stop = (
                    bid
                    +
                    price_distance
                )

                buy_result = calc_profit(
                    mt5.ORDER_TYPE_BUY,
                    resolved_symbol,
                    volume,
                    ask,
                    buy_stop,
                )

                sell_result = calc_profit(
                    mt5.ORDER_TYPE_SELL,
                    resolved_symbol,
                    volume,
                    bid,
                    sell_stop,
                )

                buy_loss = (
                    abs(
                        buy_result
                    )
                    if (
                        buy_result is not None
                        and
                        buy_result < 0.0
                    )
                    else
                    (
                        0.0
                        if buy_result == 0.0
                        else
                        None
                    )
                )

                sell_loss = (
                    abs(
                        sell_result
                    )
                    if (
                        sell_result is not None
                        and
                        sell_result < 0.0
                    )
                    else
                    (
                        0.0
                        if sell_result == 0.0
                        else
                        None
                    )
                )

                buy_balance_pct = pct(
                    buy_loss,
                    balance,
                )

                sell_balance_pct = pct(
                    sell_loss,
                    balance,
                )

                loss_rows.append(
                    {
                        "volume": (
                            fmt_number(
                                volume,
                                8,
                            )
                        ),

                        "points": (
                            fmt_number(
                                distance_points,
                                3,
                            )
                        ),

                        "price_dist": (
                            fmt_number(
                                price_distance,
                                digits,
                            )
                        ),

                        "buy_loss": (
                            fmt_money(
                                buy_loss,
                                currency,
                            )
                        ),

                        "sell_loss": (
                            fmt_money(
                                sell_loss,
                                currency,
                            )
                        ),

                        "buy_%bal": (
                            fmt_number(
                                buy_balance_pct,
                                3,
                            )
                            if buy_balance_pct
                            is not None
                            else
                            "N/A"
                        ),

                        "sell_%bal": (
                            fmt_number(
                                sell_balance_pct,
                                3,
                            )
                            if sell_balance_pct
                            is not None
                            else
                            "N/A"
                        ),
                    }
                )

        print_table(
            loss_rows,
            (
                "volume",
                "points",
                "price_dist",
                "buy_loss",
                "sell_loss",
                "buy_%bal",
                "sell_%bal",
            ),
        )

        # =====================================================================
        # Minimum-lot safety view
        # =====================================================================

        section(
            "MINIMUM BROKER VOLUME — ACCOUNT RISK VIEW"
        )

        minimum_volume = probe_volumes[
            0
        ]

        line(
            "Minimum calibrated volume",
            fmt_number(
                minimum_volume,
                8,
            ),
        )

        minimum_rows = [
            row
            for row in loss_rows
            if row[
                "volume"
            ]
            ==
            fmt_number(
                minimum_volume,
                8,
            )
        ]

        print_table(
            minimum_rows,
            (
                "points",
                "price_dist",
                "buy_loss",
                "sell_loss",
                "buy_%bal",
                "sell_%bal",
            ),
        )

        # =====================================================================
        # Diagnostic conclusions
        # =====================================================================

        section(
            "CALIBRATION DIAGNOSTICS"
        )

        line(
            "Account currency",
            currency,
        )

        line(
            "Account balance",
            fmt_money(
                balance,
                currency,
            ),
        )

        line(
            "Broker minimum volume",
            fmt_number(
                safe_get(
                    symbol_info,
                    "volume_min",
                    None,
                ),
                8,
            ),
        )

        line(
            "Broker volume step",
            fmt_number(
                safe_get(
                    symbol_info,
                    "volume_step",
                    None,
                ),
                8,
            ),
        )

        line(
            "Broker point",
            fmt_number(
                point,
                10,
            ),
        )

        line(
            "Broker tick size",
            fmt_number(
                safe_get(
                    symbol_info,
                    "trade_tick_size",
                    None,
                ),
                10,
            ),
        )

        line(
            "Current spread points",
            fmt_number(
                spread_points_live,
                3,
            ),
        )

        line(
            "Existing RiskEngine",
            "NOT WIRED / NOT MODIFIED",
        )

        line(
            "Live sizing",
            "NOT PERFORMED",
        )

        line(
            "Order placement",
            "NOT PERFORMED",
        )

        print()
        print(
            "Next engineering use of this output:"
        )
        print(
            "- derive broker-aware monetary loss per valid volume"
        )
        print(
            "- determine whether broker minimum lot can satisfy safe account risk"
        )
        print(
            "- replace fixed $1 small-account logic"
        )
        print(
            "- design lot sizing around actual order_calc_profit results"
        )
        print(
            "- add volume-step / stops / margin / spread safety gates"
        )
        print(
            "- keep execution disabled until offline + demo validation is complete"
        )

    finally:

        if initialized:

            fetcher.shutdown()


if __name__ == "__main__":

    main()