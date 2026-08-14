"""
===============================================================================
Module      : shadow_bootstrap_compounding_operation.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Real Exness Bootstrap / Compounding Basket Calibration
===============================================================================

Purpose
-------
Use the connected MT5 / Exness broker environment to evaluate hypothetical
bootstrap and compounding baskets across simulated account balances.

The operation uses:

    mt5.order_calc_profit()
    mt5.order_calc_margin()

to measure actual broker monetary characteristics for:

- $3
- $5
- $10
- $20
- $50
- $100

and hypothetical:

- LONG baskets
- SHORT baskets
- 1 leg
- 2 legs
- 3 legs
- broker minimum volume
- multiple structural stop distances

The operation answers:

- how many minimum-lot legs can fit?
- what is combined projected SL loss?
- what percentage of balance is at risk?
- what combined margin is required?
- how much spread friction is paid?
- does bootstrap basket policy accept/reject the basket?
- when does STANDARD_COMPOUND_BASKET replace MICRO_BOOTSTRAP_BASKET?

Management examples also demonstrate:

- single 0.01 cannot partial-close below broker minimum
- 0.02 can release 0.01
- 0.03 can scale out while preserving a runner
- trailing / runner instructions are observational only

Safety
------
READ ONLY.

This operation does NOT:

- call mt5.order_send()
- open orders
- close orders
- modify SL
- modify TP
- modify positions
- authorize live trading
- modify production trade_ready
- modify LEI
- modify RWEI
- modify production RiskEngine

This is calibration evidence only.
"""

from __future__ import annotations

import argparse
import importlib
import math
import sys
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
# Existing project modules
# =============================================================================


fetcher: Any = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher


basket_module: Any = importlib.import_module(
    "02_AI.Shadow.bootstrap_compounding_planner"
)


BootstrapCompoundingPlanner: Any = (
    basket_module.BootstrapCompoundingPlanner
)


BootstrapCompoundingPolicy: Any = (
    basket_module.BootstrapCompoundingPolicy
)


BasketLegCandidate: Any = (
    basket_module.BasketLegCandidate
)


# =============================================================================
# Display helpers
# =============================================================================


def section(
    title: str,
) -> None:

    print()

    print(
        "=" * 130
    )

    print(
        title
    )

    print(
        "=" * 130
    )


def line(
    label: str,
    value: Any,
) -> None:

    print(
        f"{label:<40}: {value}"
    )


def number(
    value: Any,
    digits: int = 6,
) -> str:

    if value is None:

        return "N/A"

    try:

        numeric = float(
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
        numeric
    ):

        return "N/A"

    return (
        f"{numeric:.{digits}f}"
        .rstrip(
            "0"
        )
        .rstrip(
            "."
        )
    )


def money(
    value: Any,
    currency: str,
) -> str:

    if value is None:

        return "N/A"

    try:

        numeric = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return "N/A"

    if not math.isfinite(
        numeric
    ):

        return "N/A"

    return (
        f"{numeric:.4f} {currency}"
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


def last_error() -> str:

    try:

        return str(
            mt5.last_error()
        )

    except Exception:

        return "unavailable"


# =============================================================================
# Parsing
# =============================================================================


def parse_positive_values(
    text: str,
    name: str,
) -> list[
    float
]:

    values: list[
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
                f"Invalid {name}: {raw}"
            ) from exc

        if (
            not math.isfinite(
                value
            )
            or
            value <= 0.0
        ):

            raise ValueError(
                f"{name} values must be > 0"
            )

        values.append(
            value
        )

    if not values:

        raise ValueError(
            f"No {name} values supplied"
        )

    return values


def parse_positive_integers(
    text: str,
    name: str,
) -> list[
    int
]:

    values: list[
        int
    ] = []

    for raw in text.split(
        ","
    ):

        raw = raw.strip()

        if not raw:

            continue

        try:

            value = int(
                raw
            )

        except ValueError as exc:

            raise ValueError(
                f"Invalid {name}: {raw}"
            ) from exc

        if value <= 0:

            raise ValueError(
                f"{name} values must be > 0"
            )

        values.append(
            value
        )

    if not values:

        raise ValueError(
            f"No {name} values supplied"
        )

    return values


# =============================================================================
# Broker calculations
# =============================================================================


def broker_loss(
    *,
    direction: str,
    symbol: str,
    volume: float,
    entry: float,
    stop: float,
) -> float:

    order_type = (
        mt5.ORDER_TYPE_BUY
        if direction == "LONG"
        else mt5.ORDER_TYPE_SELL
    )

    result = mt5.order_calc_profit(
        order_type,
        symbol,
        volume,
        entry,
        stop,
    )

    if result is None:

        raise RuntimeError(
            (
                "order_calc_profit() failed: "
                f"direction={direction}, "
                f"volume={volume}, "
                f"last_error={last_error()}"
            )
        )

    value = float(
        result
    )

    if not math.isfinite(
        value
    ):

        raise RuntimeError(
            "order_calc_profit() returned non-finite value"
        )

    return abs(
        value
    )


def broker_margin(
    *,
    direction: str,
    symbol: str,
    volume: float,
    entry: float,
) -> float:

    order_type = (
        mt5.ORDER_TYPE_BUY
        if direction == "LONG"
        else mt5.ORDER_TYPE_SELL
    )

    result = mt5.order_calc_margin(
        order_type,
        symbol,
        volume,
        entry,
    )

    if result is None:

        raise RuntimeError(
            (
                "order_calc_margin() failed: "
                f"direction={direction}, "
                f"volume={volume}, "
                f"last_error={last_error()}"
            )
        )

    value = float(
        result
    )

    if (
        not math.isfinite(
            value
        )
        or
        value <= 0.0
    ):

        raise RuntimeError(
            "order_calc_margin() returned invalid value"
        )

    return value


def broker_spread_cost(
    *,
    direction: str,
    symbol: str,
    volume: float,
    bid: float,
    ask: float,
) -> float:

    if direction == "LONG":

        order_type = (
            mt5.ORDER_TYPE_BUY
        )

        price_open = (
            ask
        )

        price_close = (
            bid
        )

    else:

        order_type = (
            mt5.ORDER_TYPE_SELL
        )

        price_open = (
            bid
        )

        price_close = (
            ask
        )

    result = mt5.order_calc_profit(
        order_type,
        symbol,
        volume,
        price_open,
        price_close,
    )

    if result is None:

        raise RuntimeError(
            (
                "spread order_calc_profit() failed: "
                f"direction={direction}, "
                f"last_error={last_error()}"
            )
        )

    value = float(
        result
    )

    if not math.isfinite(
        value
    ):

        raise RuntimeError(
            "Spread calculation returned non-finite value"
        )

    return abs(
        value
    )


# =============================================================================
# Table
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

    print(
        "  ".join(
            column.ljust(
                widths[
                    column
                ]
            )
            for column in columns
        )
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
            "PulseViper real Exness bootstrap / compounding "
            "basket calibration v1.0"
        )
    )

    parser.add_argument(
        "--symbol",
        default="XAUUSDm",
    )

    parser.add_argument(
        "--balances",
        default="3,5,10,20,50,100",
        help=(
            "Simulated account balances."
        ),
    )

    parser.add_argument(
        "--distances",
        default="0.30,0.50,0.75,1.00",
        help=(
            "Structural stop distances in XAU price units."
        ),
    )

    parser.add_argument(
        "--legs",
        default="1,2,3",
        help=(
            "Requested simultaneous leg counts."
        ),
    )

    args = parser.parse_args()

    balances = parse_positive_values(
        args.balances,
        "balance",
    )

    distances = parse_positive_values(
        args.distances,
        "distance",
    )

    requested_leg_counts = (
        parse_positive_integers(
            args.legs,
            "leg count",
        )
    )

    # =========================================================================
    # Aggressive compounding calibration policy
    #
    # This intentionally enables simultaneous legs so we can measure the full
    # broker/account capacity envelope.
    #
    # It does NOT authorize execution.
    # =========================================================================

    policy = BootstrapCompoundingPolicy(
        compounding_enabled=True,
        allow_initial_multi_leg=True,
        max_simultaneous_legs=3,
        max_total_volume=0.03,

        bootstrap_balance_max=20.0,

        bootstrap_loss_budget_floor_usd=0.50,

        bootstrap_loss_budget_percent=16.67,

        bootstrap_loss_budget_ceiling_usd=2.00,

        bootstrap_margin_cap_percent=85.0,

        standard_basket_hard_loss_percent=2.00,

        standard_margin_cap_percent=35.0,

        max_total_spread_to_basket_loss_ratio=1.00,

        # Initial simultaneous capacity test:
        # profit gating is irrelevant before first basket exists.
        add_only_after_profit=False,

        minimum_profit_r_before_add=0.25,

        partial_booking_enabled=True,

        partial_booking_r=0.75,

        partial_booking_fraction=0.50,

        trail_enabled=True,

        trail_start_r=0.50,

        runner_r=1.25,
    )

    planner = BootstrapCompoundingPlanner(
        policy=policy
    )

    initialized = False

    # =========================================================================
    # Header
    # =========================================================================

    section(
        "PulseViper XAU AI — "
        "REAL EXNESS BOOTSTRAP / COMPOUNDING CALIBRATION v1.0"
    )

    line(
        "Requested symbol",
        args.symbol,
    )

    line(
        "Planner mode",
        planner.MODE,
    )

    line(
        "Compounding",
        "ENABLED FOR SHADOW SIMULATION",
    )

    line(
        "Initial multi-leg",
        "ENABLED FOR CAPACITY TEST",
    )

    line(
        "Maximum legs",
        policy.max_simultaneous_legs,
    )

    line(
        "Maximum basket volume",
        policy.max_total_volume,
    )

    line(
        "Bootstrap balance max",
        policy.bootstrap_balance_max,
    )

    line(
        "Bootstrap loss floor",
        policy.bootstrap_loss_budget_floor_usd,
    )

    line(
        "Bootstrap loss %",
        policy.bootstrap_loss_budget_percent,
    )

    line(
        "Bootstrap loss ceiling",
        policy.bootstrap_loss_budget_ceiling_usd,
    )

    line(
        "Standard basket loss %",
        policy.standard_basket_hard_loss_percent,
    )

    line(
        "Broker access",
        "READ ONLY",
    )

    line(
        "order_send",
        "NEVER CALLED",
    )

    line(
        "Live authorization",
        "DISABLED",
    )

    try:

        # =====================================================================
        # Initialize MT5
        # =====================================================================

        fetcher.initialize()

        initialized = True

        # =====================================================================
        # Actual account context
        # =====================================================================

        account = mt5.account_info()

        if account is None:

            raise RuntimeError(
                (
                    "account_info() failed: "
                    f"{last_error()}"
                )
            )

        currency = str(
            safe_get(
                account,
                "currency",
                "UNKNOWN",
            )
        )

        section(
            "CONNECTED ACCOUNT"
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
            "Server",
            safe_get(
                account,
                "server",
                "UNKNOWN",
            ),
        )

        line(
            "Company",
            safe_get(
                account,
                "company",
                "UNKNOWN",
            ),
        )

        line(
            "Actual balance",
            money(
                safe_get(
                    account,
                    "balance",
                    None,
                ),
                currency,
            ),
        )

        line(
            "Actual equity",
            money(
                safe_get(
                    account,
                    "equity",
                    None,
                ),
                currency,
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

        # =====================================================================
        # Symbol
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
                (
                    f"Unable to select {resolved_symbol}: "
                    f"{last_error()}"
                )
            )

        info = mt5.symbol_info(
            resolved_symbol
        )

        tick = mt5.symbol_info_tick(
            resolved_symbol
        )

        if info is None:

            raise RuntimeError(
                (
                    f"symbol_info({resolved_symbol}) failed: "
                    f"{last_error()}"
                )
            )

        if tick is None:

            raise RuntimeError(
                (
                    f"symbol_info_tick({resolved_symbol}) failed: "
                    f"{last_error()}"
                )
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

        digits = int(
            safe_get(
                info,
                "digits",
                3,
            )
            or
            3
        )

        point = float(
            safe_get(
                info,
                "point",
                0.0,
            )
            or
            0.0
        )

        volume_min = float(
            safe_get(
                info,
                "volume_min",
                0.0,
            )
            or
            0.0
        )

        volume_step = float(
            safe_get(
                info,
                "volume_step",
                0.0,
            )
            or
            0.0
        )

        if (
            bid <= 0.0
            or
            ask <= 0.0
            or
            ask < bid
            or
            point <= 0.0
            or
            volume_min <= 0.0
            or
            volume_step <= 0.0
        ):

            raise RuntimeError(
                "Invalid broker symbol metadata"
            )

        spread_price = (
            ask
            -
            bid
        )

        spread_points = (
            spread_price
            /
            point
        )

        section(
            "CURRENT XAUUSD BROKER CALIBRATION"
        )

        line(
            "Resolved symbol",
            resolved_symbol,
        )

        line(
            "Bid",
            number(
                bid,
                digits,
            ),
        )

        line(
            "Ask",
            number(
                ask,
                digits,
            ),
        )

        line(
            "Spread price",
            number(
                spread_price,
                digits,
            ),
        )

        line(
            "Spread points",
            number(
                spread_points,
                3,
            ),
        )

        line(
            "Broker minimum volume",
            number(
                volume_min,
                8,
            ),
        )

        line(
            "Broker volume step",
            number(
                volume_step,
                8,
            ),
        )

        # =====================================================================
        # Per-leg broker characteristics
        # =====================================================================

        section(
            "BROKER MINIMUM-LOT CHARACTERISTICS"
        )

        characteristic_rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        per_leg: dict[
            tuple[
                str,
                float,
            ],
            dict[
                str,
                float,
            ],
        ] = {}

        for direction in (
            "LONG",
            "SHORT",
        ):

            entry = (
                ask
                if direction == "LONG"
                else bid
            )

            spread_cost = broker_spread_cost(
                direction=direction,
                symbol=resolved_symbol,
                volume=volume_min,
                bid=bid,
                ask=ask,
            )

            margin = broker_margin(
                direction=direction,
                symbol=resolved_symbol,
                volume=volume_min,
                entry=entry,
            )

            for distance in distances:

                stop = (
                    entry
                    -
                    distance
                    if direction == "LONG"
                    else
                    entry
                    +
                    distance
                )

                stop = round(
                    stop,
                    digits,
                )

                stop_loss = broker_loss(
                    direction=direction,
                    symbol=resolved_symbol,
                    volume=volume_min,
                    entry=entry,
                    stop=stop,
                )

                per_leg[
                    (
                        direction,
                        distance,
                    )
                ] = {
                    "loss": (
                        stop_loss
                    ),
                    "margin": (
                        margin
                    ),
                    "spread": (
                        spread_cost
                    ),
                    "stop": (
                        stop
                    ),
                }

                characteristic_rows.append(
                    {
                        "dir": (
                            direction
                        ),

                        "SL_dist": (
                            number(
                                distance,
                                3,
                            )
                        ),

                        "lot": (
                            number(
                                volume_min,
                                4,
                            )
                        ),

                        "SL_loss": (
                            number(
                                stop_loss,
                                4,
                            )
                        ),

                        "margin": (
                            number(
                                margin,
                                4,
                            )
                        ),

                        "spread": (
                            number(
                                spread_cost,
                                4,
                            )
                        ),
                    }
                )

        print_table(
            characteristic_rows,
            (
                "dir",
                "SL_dist",
                "lot",
                "SL_loss",
                "margin",
                "spread",
            ),
        )

        # =====================================================================
        # Balance ladder
        # =====================================================================

        section(
            "BALANCE LADDER — 1 / 2 / 3 LEG BASKET CAPACITY"
        )

        rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for balance in balances:

            for direction in (
                "LONG",
                "SHORT",
            ):

                for distance in distances:

                    calibration = per_leg[
                        (
                            direction,
                            distance,
                        )
                    ]

                    for requested_legs in requested_leg_counts:

                        candidates = [
                            BasketLegCandidate(
                                leg_id=(
                                    f"{direction}_"
                                    f"{number(balance, 2)}_"
                                    f"{number(distance, 3)}_"
                                    f"L{index + 1}"
                                ),
                                direction=direction,
                                volume=volume_min,
                                projected_stop_loss=(
                                    calibration[
                                        "loss"
                                    ]
                                ),
                                margin_required=(
                                    calibration[
                                        "margin"
                                    ]
                                ),
                                spread_cost=(
                                    calibration[
                                        "spread"
                                    ]
                                ),
                                structural_stop_distance=distance,
                            )
                            for index
                            in range(
                                requested_legs
                            )
                        ]

                        plan = planner.plan(
                            account_balance=balance,
                            account_equity=balance,
                            free_margin=balance,
                            candidates=candidates,
                            volume_min=volume_min,
                            volume_step=volume_step,
                        )

                        rows.append(
                            {
                                "bal": (
                                    number(
                                        balance,
                                        2,
                                    )
                                ),

                                "mode": (
                                    "MICRO"
                                    if plan.basket_mode
                                    ==
                                    planner.BOOTSTRAP_MODE
                                    else
                                    "STD"
                                ),

                                "dir": (
                                    direction
                                ),

                                "SL": (
                                    number(
                                        distance,
                                        2,
                                    )
                                ),

                                "req": (
                                    requested_legs
                                ),

                                "acc": (
                                    plan.accepted_new_legs
                                ),

                                "lot": (
                                    number(
                                        plan.total_volume,
                                        4,
                                    )
                                ),

                                "loss_cap": (
                                    number(
                                        plan.basket_loss_cap,
                                        3,
                                    )
                                ),

                                "SL_loss": (
                                    number(
                                        plan.total_projected_loss,
                                        3,
                                    )
                                ),

                                "risk_%": (
                                    number(
                                        plan.total_projected_loss_percent,
                                        2,
                                    )
                                ),

                                "margin_%": (
                                    number(
                                        plan.total_margin_percent_of_free,
                                        1,
                                    )
                                ),

                                "spread": (
                                    number(
                                        plan.total_spread_cost,
                                        3,
                                    )
                                ),

                                "result": (
                                    plan.reason
                                ),
                            }
                        )

        print_table(
            rows,
            (
                "bal",
                "mode",
                "dir",
                "SL",
                "req",
                "acc",
                "lot",
                "loss_cap",
                "SL_loss",
                "risk_%",
                "margin_%",
                "spread",
                "result",
            ),
        )

        # =====================================================================
        # Maximum feasible legs summary
        # =====================================================================

        section(
            "MAXIMUM FEASIBLE INITIAL LEGS"
        )

        summary_rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for balance in balances:

            for direction in (
                "LONG",
                "SHORT",
            ):

                for distance in distances:

                    matching = [
                        row
                        for row in rows
                        if (
                            float(
                                row[
                                    "bal"
                                ]
                            )
                            ==
                            float(
                                number(
                                    balance,
                                    2,
                                )
                            )
                            and
                            row[
                                "dir"
                            ]
                            ==
                            direction
                            and
                            float(
                                row[
                                    "SL"
                                ]
                            )
                            ==
                            float(
                                number(
                                    distance,
                                    2,
                                )
                            )
                        )
                    ]

                    maximum_accepted = max(
                        (
                            int(
                                row[
                                    "acc"
                                ]
                            )
                            for row in matching
                        ),
                        default=0,
                    )

                    total_volume = (
                        maximum_accepted
                        *
                        volume_min
                    )

                    calibration = per_leg[
                        (
                            direction,
                            distance,
                        )
                    ]

                    projected_loss = (
                        maximum_accepted
                        *
                        calibration[
                            "loss"
                        ]
                    )

                    risk_percent = (
                        (
                            projected_loss
                            /
                            balance
                            *
                            100.0
                        )
                        if balance > 0.0
                        else 0.0
                    )

                    summary_rows.append(
                        {
                            "balance": (
                                number(
                                    balance,
                                    2,
                                )
                            ),

                            "dir": (
                                direction
                            ),

                            "SL": (
                                number(
                                    distance,
                                    2,
                                )
                            ),

                            "max_legs": (
                                maximum_accepted
                            ),

                            "volume": (
                                number(
                                    total_volume,
                                    4,
                                )
                            ),

                            "SL_loss": (
                                number(
                                    projected_loss,
                                    3,
                                )
                            ),

                            "risk_%": (
                                number(
                                    risk_percent,
                                    2,
                                )
                            ),
                        }
                    )

        print_table(
            summary_rows,
            (
                "balance",
                "dir",
                "SL",
                "max_legs",
                "volume",
                "SL_loss",
                "risk_%",
            ),
        )

        # =====================================================================
        # Management simulation
        # =====================================================================

        section(
            "COMPOUNDING MANAGEMENT / SCALE-OUT SIMULATION"
        )

        management_rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for total_volume in (
            volume_min,
            volume_min * 2.0,
            volume_min * 3.0,
        ):

            for current_r in (
                0.25,
                0.50,
                0.75,
                1.00,
                1.25,
                1.50,
            ):

                initial_risk = (
                    0.50
                )

                floating_profit = (
                    initial_risk
                    *
                    current_r
                )

                management = (
                    planner.management_plan(
                        current_volume=total_volume,
                        volume_min=volume_min,
                        volume_step=volume_step,
                        current_unrealized_profit=floating_profit,
                        initial_basket_risk=initial_risk,
                    )
                )

                management_rows.append(
                    {
                        "volume": (
                            number(
                                total_volume,
                                4,
                            )
                        ),

                        "R": (
                            number(
                                current_r,
                                2,
                            )
                        ),

                        "profit": (
                            number(
                                floating_profit,
                                3,
                            )
                        ),

                        "book": (
                            number(
                                management.close_volume,
                                4,
                            )
                        ),

                        "remain": (
                            number(
                                management.remaining_volume,
                                4,
                            )
                        ),

                        "trail": (
                            "YES"
                            if management.trail_active
                            else
                            "NO"
                        ),

                        "runner": (
                            "YES"
                            if management.runner_mode
                            else
                            "NO"
                        ),

                        "instruction": (
                            management.instruction
                        ),
                    }
                )

        print_table(
            management_rows,
            (
                "volume",
                "R",
                "profit",
                "book",
                "remain",
                "trail",
                "runner",
                "instruction",
            ),
        )

        # =====================================================================
        # Interpretation
        # =====================================================================

        section(
            "INTERPRETATION"
        )

        print(
            "MICRO = MICRO_BOOTSTRAP_BASKET"
        )

        print(
            "STD   = STANDARD_COMPOUND_BASKET"
        )

        print()

        print(
            "Important:"
        )

        print(
            "- structural SL was NEVER modified by this operation"
        )

        print(
            "- larger balances may support more legs / volume"
        )

        print(
            "- tiny balances remain constrained by broker minimum margin"
        )

        print(
            "- combined basket risk is evaluated, not just individual order risk"
        )

        print(
            "- simultaneous legs are enabled here ONLY to measure capacity"
        )

        print(
            "- management instructions do NOT modify any actual position"
        )

        print(
            "- 0.01 single position cannot scale below broker minimum"
        )

        print(
            "- 0.02 / 0.03 baskets can scale out by releasing 0.01 units"
        )

        print(
            "- future trailing stop prices must come from market structure"
        )

        # =====================================================================
        # Safety
        # =====================================================================

        section(
            "SAFETY STATUS"
        )

        line(
            "Broker access",
            "READ ONLY",
        )

        line(
            "Orders sent",
            "0",
        )

        line(
            "Positions modified",
            "0",
        )

        line(
            "SL/TP modified",
            "0",
        )

        line(
            "Production RiskEngine",
            "UNCHANGED",
        )

        line(
            "Production trade_ready",
            "UNCHANGED",
        )

        line(
            "Live authorization",
            "FALSE",
        )

    finally:

        if initialized:

            fetcher.shutdown()


if __name__ == "__main__":

    main()