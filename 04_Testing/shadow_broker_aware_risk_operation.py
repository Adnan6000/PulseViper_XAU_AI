"""
===============================================================================
Module      : shadow_broker_aware_risk_operation.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Real Exness Demo Shadow Broker-Aware Risk Validation
===============================================================================

Purpose
-------
Connect the shadow BrokerAwareRiskEngine to the currently connected MT5 demo
account and validate realistic LONG / SHORT risk plans using broker-native:

    mt5.order_calc_profit()
    mt5.order_calc_margin()

This operation tests multiple hypothetical structural stop distances.

It reports:

- current account state
- current XAUUSDm bid / ask / spread
- target and hard monetary risk budget
- broker minimum volume
- selected valid volume
- exact broker-calculated SL loss
- actual account risk %
- required margin
- spread cost
- planner decision / block reason

Safety
------
RESEARCH / SHADOW ONLY.

This file DOES NOT:

- place trades
- send orders
- modify positions
- modify pending orders
- modify production trade_ready
- modify LEI
- modify RWEI
- modify production RiskEngine
- authorize live trading
"""

from __future__ import annotations

import argparse
import importlib
import math
import sys
from pathlib import Path
from typing import Any, Callable

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


risk_module: Any = importlib.import_module(
    "02_AI.Shadow.broker_aware_risk_engine"
)

BrokerAwareRiskEngine: Any = (
    risk_module.BrokerAwareRiskEngine
)

BrokerRiskPolicy: Any = (
    risk_module.BrokerRiskPolicy
)


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
        f"{label:<36}: {value}"
    )


def number(
    value: Any,
    digits: int = 6,
) -> str:

    if value is None:
        return "N/A"

    try:

        result = float(
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
        result
    ):

        return "N/A"

    return (
        f"{result:.{digits}f}"
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

        result = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return "N/A"

    if not math.isfinite(
        result
    ):

        return "N/A"

    return (
        f"{result:.4f} {currency}"
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
# Argument parsing
# =============================================================================


def parse_distances(
    text: str,
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
                f"Invalid stop distance: {raw}"
            ) from exc

        if (
            not math.isfinite(
                value
            )
            or
            value <= 0.0
        ):

            raise ValueError(
                "All stop distances must be > 0"
            )

        values.append(
            value
        )

    if not values:

        raise ValueError(
            "At least one stop distance is required"
        )

    return values


# =============================================================================
# Broker estimator factories
# =============================================================================


def loss_estimator(
    *,
    direction: str,
    symbol: str,
    entry: float,
    stop: float,
) -> Callable[
    [float],
    float | None,
]:

    order_type = (
        mt5.ORDER_TYPE_BUY
        if direction == "LONG"
        else mt5.ORDER_TYPE_SELL
    )

    def estimate(
        volume: float,
    ) -> float | None:

        result = mt5.order_calc_profit(
            order_type,
            symbol,
            volume,
            entry,
            stop,
        )

        if result is None:

            return None

        try:

            return float(
                result
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    return estimate


def margin_estimator(
    *,
    direction: str,
    symbol: str,
    entry: float,
) -> Callable[
    [float],
    float | None,
]:

    order_type = (
        mt5.ORDER_TYPE_BUY
        if direction == "LONG"
        else mt5.ORDER_TYPE_SELL
    )

    def estimate(
        volume: float,
    ) -> float | None:

        result = mt5.order_calc_margin(
            order_type,
            symbol,
            volume,
            entry,
        )

        if result is None:

            return None

        try:

            return float(
                result
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    return estimate


def spread_cost_estimator(
    *,
    direction: str,
    symbol: str,
    bid: float,
    ask: float,
) -> Callable[
    [float],
    float | None,
]:

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

    def estimate(
        volume: float,
    ) -> float | None:

        result = mt5.order_calc_profit(
            order_type,
            symbol,
            volume,
            price_open,
            price_close,
        )

        if result is None:

            return None

        try:

            return float(
                result
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    return estimate


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
            "PulseViper real Exness demo shadow "
            "broker-aware risk validation v1.0"
        )
    )

    parser.add_argument(
        "--symbol",
        default="XAUUSDm",
    )

    parser.add_argument(
        "--distances",
        default=(
            "0.30,"
            "0.40,"
            "0.50,"
            "0.60,"
            "0.75,"
            "1.00,"
            "1.50,"
            "2.00"
        ),
        help=(
            "Hypothetical structural SL distances "
            "in XAUUSD price units."
        ),
    )

    parser.add_argument(
        "--target-risk",
        type=float,
        default=0.75,
    )

    parser.add_argument(
        "--hard-risk",
        type=float,
        default=1.00,
    )

    parser.add_argument(
        "--max-margin-free-pct",
        type=float,
        default=25.0,
    )

    parser.add_argument(
        "--max-spread-hard-ratio",
        type=float,
        default=1.00,
    )

    args = parser.parse_args()

    distances = parse_distances(
        args.distances
    )

    policy = BrokerRiskPolicy(
        target_risk_percent=(
            args.target_risk
        ),
        hard_max_risk_percent=(
            args.hard_risk
        ),
        max_margin_percent_of_free=(
            args.max_margin_free_pct
        ),
        max_spread_cost_to_hard_risk_ratio=(
            args.max_spread_hard_ratio
        ),
    )

    planner = BrokerAwareRiskEngine(
        policy=policy
    )

    initialized = False

    # =========================================================================
    # Header
    # =========================================================================

    section(
        "PulseViper XAU AI — "
        "REAL EXNESS SHADOW RISK VALIDATION v1.0"
    )

    line(
        "Requested symbol",
        args.symbol,
    )

    line(
        "Risk mode",
        planner.MODE,
    )

    line(
        "Target risk",
        f"{policy.target_risk_percent}%",
    )

    line(
        "Hard max risk",
        f"{policy.hard_max_risk_percent}%",
    )

    line(
        "Margin cap",
        (
            f"{policy.max_margin_percent_of_free}% "
            "of free margin"
        ),
    )

    line(
        "Broker access",
        "READ ONLY",
    )

    line(
        "Order placement",
        "DISABLED",
    )

    line(
        "Live authorization",
        "DISABLED",
    )

    line(
        "Production RiskEngine",
        "UNCHANGED / UNWIRED",
    )

    try:

        # =====================================================================
        # Initialize MT5
        # =====================================================================

        fetcher.initialize()

        initialized = True

        # =====================================================================
        # Account
        # =====================================================================

        account = mt5.account_info()

        if account is None:

            raise RuntimeError(
                "account_info() failed: "
                +
                last_error()
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

        free_margin = float(
            safe_get(
                account,
                "margin_free",
                0.0,
            )
            or
            0.0
        )

        currency = str(
            safe_get(
                account,
                "currency",
                "UNKNOWN",
            )
        )

        risk_base = min(
            balance,
            equity,
        )

        target_amount = (
            risk_base
            *
            policy.target_risk_percent
            /
            100.0
        )

        hard_amount = (
            risk_base
            *
            policy.hard_max_risk_percent
            /
            100.0
        )

        section(
            "CURRENT ACCOUNT"
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
            "Currency",
            currency,
        )

        line(
            "Balance",
            money(
                balance,
                currency,
            ),
        )

        line(
            "Equity",
            money(
                equity,
                currency,
            ),
        )

        line(
            "Free margin",
            money(
                free_margin,
                currency,
            ),
        )

        line(
            "Risk base min(balance,equity)",
            money(
                risk_base,
                currency,
            ),
        )

        line(
            "Target risk amount",
            money(
                target_amount,
                currency,
            ),
        )

        line(
            "Hard max risk amount",
            money(
                hard_amount,
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

        line(
            "Open positions",
            mt5.positions_total(),
        )

        line(
            "Pending orders",
            mt5.orders_total(),
        )

        # =====================================================================
        # Symbol resolution
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

        point = float(
            safe_get(
                info,
                "point",
                0.0,
            )
            or
            0.0
        )

        tick_size = float(
            safe_get(
                info,
                "trade_tick_size",
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

        volume_max = float(
            safe_get(
                info,
                "volume_max",
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

        stops_level = float(
            safe_get(
                info,
                "trade_stops_level",
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

        if (
            bid <= 0.0
            or
            ask <= 0.0
            or
            ask < bid
            or
            point <= 0.0
            or
            tick_size <= 0.0
        ):

            raise RuntimeError(
                "Invalid live symbol metadata"
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

        # =====================================================================
        # Symbol view
        # =====================================================================

        section(
            "CURRENT XAUUSD BROKER STATE"
        )

        line(
            "Resolved symbol",
            resolved_symbol,
        )

        line(
            "Description",
            safe_get(
                info,
                "description",
                "UNKNOWN",
            ),
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
            "Point",
            number(
                point,
                10,
            ),
        )

        line(
            "Tick size",
            number(
                tick_size,
                10,
            ),
        )

        line(
            "Tick value",
            number(
                safe_get(
                    info,
                    "trade_tick_value",
                    None,
                ),
                8,
            ),
        )

        line(
            "Contract size",
            number(
                safe_get(
                    info,
                    "trade_contract_size",
                    None,
                ),
                4,
            ),
        )

        line(
            "Volume minimum",
            number(
                volume_min,
                8,
            ),
        )

        line(
            "Volume maximum",
            number(
                volume_max,
                8,
            ),
        )

        line(
            "Volume step",
            number(
                volume_step,
                8,
            ),
        )

        line(
            "Stops level points",
            number(
                stops_level,
                3,
            ),
        )

        line(
            "Freeze level points",
            number(
                safe_get(
                    info,
                    "trade_freeze_level",
                    None,
                ),
                3,
            ),
        )

        operational_min_price = (
            spread_price
            +
            max(
                stops_level
                *
                point,
                tick_size,
            )
        )

        line(
            "Operational min SL from entry",
            number(
                operational_min_price,
                digits,
            ),
        )

        line(
            "Operational min SL points",
            number(
                operational_min_price
                /
                point,
                3,
            ),
        )

        # =====================================================================
        # Risk probe
        # =====================================================================

        section(
            "REAL BROKER RISK PROBES"
        )

        rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        plans: list[
            Any
        ] = []

        for direction in (
            "LONG",
            "SHORT",
        ):

            for distance in distances:

                if direction == "LONG":

                    entry = (
                        ask
                    )

                    stop = (
                        entry
                        -
                        distance
                    )

                else:

                    entry = (
                        bid
                    )

                    stop = (
                        entry
                        +
                        distance
                    )

                stop = round(
                    stop,
                    digits,
                )

                plan = planner.plan(
                    direction=direction,
                    account_balance=balance,
                    account_equity=equity,
                    free_margin=free_margin,
                    bid=bid,
                    ask=ask,
                    stop_loss=stop,
                    point=point,
                    tick_size=tick_size,
                    volume_min=volume_min,
                    volume_max=volume_max,
                    volume_step=volume_step,
                    stops_level_points=stops_level,
                    loss_estimator=loss_estimator(
                        direction=direction,
                        symbol=resolved_symbol,
                        entry=entry,
                        stop=stop,
                    ),
                    margin_estimator=margin_estimator(
                        direction=direction,
                        symbol=resolved_symbol,
                        entry=entry,
                    ),
                    spread_cost_estimator=spread_cost_estimator(
                        direction=direction,
                        symbol=resolved_symbol,
                        bid=bid,
                        ask=ask,
                    ),
                )

                plans.append(
                    plan
                )

                rows.append(
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

                        "stop": (
                            number(
                                stop,
                                digits,
                            )
                        ),

                        "valid": (
                            "YES"
                            if plan.valid
                            else
                            "NO"
                        ),

                        "reason": (
                            plan.reason
                        ),

                        "lot": (
                            number(
                                plan.selected_volume,
                                4,
                            )
                        ),

                        "SL_loss": (
                            number(
                                plan.estimated_stop_loss_amount,
                                4,
                            )
                        ),

                        "risk_%": (
                            number(
                                plan.actual_risk_percent,
                                3,
                            )
                        ),

                        "margin": (
                            number(
                                plan.margin_required,
                                4,
                            )
                        ),

                        "spread": (
                            number(
                                plan.spread_cost,
                                4,
                            )
                        ),
                    }
                )

        print_table(
            rows,
            (
                "dir",
                "SL_dist",
                "stop",
                "valid",
                "reason",
                "lot",
                "SL_loss",
                "risk_%",
                "margin",
                "spread",
            ),
        )

        # =====================================================================
        # Valid plan detail
        # =====================================================================

        section(
            "VALID PLAN DETAILS"
        )

        valid_plans = [
            plan
            for plan in plans
            if plan.valid
        ]

        if not valid_plans:

            print(
                "No tested stop distance produced a valid shadow risk plan."
            )

        else:

            for plan in valid_plans:

                print()

                print(
                    (
                        f"{plan.direction} | "
                        f"SL distance "
                        f"{number(plan.stop_distance_price, 4)}"
                    )
                )

                line(
                    "Decision",
                    plan.reason,
                )

                line(
                    "Entry",
                    number(
                        plan.entry_price,
                        digits,
                    ),
                )

                line(
                    "Stop",
                    number(
                        plan.stop_loss,
                        digits,
                    ),
                )

                line(
                    "Selected volume",
                    number(
                        plan.selected_volume,
                        8,
                    ),
                )

                line(
                    "Minimum-volume SL loss",
                    money(
                        plan.minimum_volume_loss,
                        currency,
                    ),
                )

                line(
                    "Planned SL loss",
                    money(
                        plan.estimated_stop_loss_amount,
                        currency,
                    ),
                )

                line(
                    "Actual risk %",
                    (
                        f"{number(plan.actual_risk_percent, 4)}%"
                    ),
                )

                line(
                    "Target utilization",
                    (
                        f"{number(plan.risk_target_utilization_percent, 3)}%"
                    ),
                )

                line(
                    "Margin required",
                    money(
                        plan.margin_required,
                        currency,
                    ),
                )

                line(
                    "Margin % free",
                    (
                        f"{number(plan.margin_percent_of_free, 3)}%"
                    ),
                )

                line(
                    "Spread cost",
                    money(
                        plan.spread_cost,
                        currency,
                    ),
                )

                line(
                    "Spread / hard risk",
                    number(
                        plan.spread_cost_to_hard_risk_ratio,
                        4,
                    ),
                )

                line(
                    "Spread / stop risk",
                    number(
                        plan.spread_cost_to_stop_risk_ratio,
                        4,
                    ),
                )

                line(
                    "Live authorized",
                    plan.live_authorized,
                )

        # =====================================================================
        # Block summary
        # =====================================================================

        section(
            "BLOCK REASON SUMMARY"
        )

        reason_counts: dict[
            str,
            int
        ] = {}

        for plan in plans:

            if plan.valid:
                continue

            reason_counts[
                plan.reason
            ] = (
                reason_counts.get(
                    plan.reason,
                    0,
                )
                +
                1
            )

        if not reason_counts:

            print(
                "No probes were blocked."
            )

        else:

            for (
                reason,
                count,
            ) in sorted(
                reason_counts.items()
            ):

                line(
                    reason,
                    count,
                )

        # =====================================================================
        # Feasible range
        # =====================================================================

        section(
            "CURRENT SHADOW FEASIBILITY"
        )

        for direction in (
            "LONG",
            "SHORT",
        ):

            directional = [
                plan
                for plan in valid_plans
                if plan.direction
                ==
                direction
            ]

            if not directional:

                line(
                    f"{direction} valid probes",
                    "NONE",
                )

                continue

            smallest = min(
                directional,
                key=lambda plan: (
                    plan.stop_distance_price
                ),
            )

            largest = max(
                directional,
                key=lambda plan: (
                    plan.stop_distance_price
                ),
            )

            line(
                f"{direction} smallest valid SL",
                (
                    f"{number(smallest.stop_distance_price, 4)} "
                    "price"
                ),
            )

            line(
                f"{direction} largest tested valid SL",
                (
                    f"{number(largest.stop_distance_price, 4)} "
                    "price"
                ),
            )

            line(
                f"{direction} largest valid lot",
                number(
                    max(
                        plan.selected_volume
                        for plan in directional
                    ),
                    4,
                ),
            )

        # =====================================================================
        # Safety conclusion
        # =====================================================================

        section(
            "SAFETY STATUS"
        )

        line(
            "Production RiskEngine changed",
            "NO",
        )

        line(
            "Production trade_ready changed",
            "NO",
        )

        line(
            "Orders sent",
            "NO",
        )

        line(
            "Positions modified",
            "NO",
        )

        line(
            "Pending orders modified",
            "NO",
        )

        line(
            "Live authorization",
            "NO",
        )

        print()
        print(
            "This output is calibration evidence only."
        )

        print(
            (
                "A structural stop that cannot fit broker minimum volume "
                "inside the hard risk ceiling must be BLOCKED — "
                "the stop must not be artificially tightened."
            )
        )

    finally:

        if initialized:

            fetcher.shutdown()


if __name__ == "__main__":

    main()