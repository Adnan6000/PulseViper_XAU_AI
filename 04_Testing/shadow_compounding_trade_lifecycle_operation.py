"""
===============================================================================
Module      : shadow_compounding_trade_lifecycle_operation.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Real Exness-Calibrated Stateful Compounding Lifecycle Simulation
===============================================================================

Status
------
READ-ONLY / SHADOW / RESEARCH / DEMO ONLY.

This operation DOES NOT:
- call mt5.order_send()
- open positions
- close positions
- modify positions
- modify SL
- modify TP
- authorize live trading
- modify production trade_ready
- modify LEI
- modify RWEI
- modify production RiskEngine

Purpose
-------
Use the connected Exness / MT5 environment only for broker-native monetary
calibration:

    mt5.order_calc_profit()
    mt5.order_calc_margin()

Then simulate the complete PulseViper compounding lifecycle:

    Leg-1
      ->
    profit proof
      ->
    Leg-2 admission attempt
      ->
    partial booking / structure trail
      ->
    runner state
      ->
    optional later Leg-3 admission

The account balances are hypothetical:

    $3
    $5
    $10
    $20
    $50
    $100

but broker economics come from the CURRENT connected account:

- symbol contract
- leverage environment
- minimum lot
- volume step
- spread
- margin
- P/L behavior

Important
---------
Future prices are unknown.

Therefore each hypothetical new leg uses CURRENT broker quote economics as a
static calibration reference.

This is a capacity / lifecycle experiment, not a future-price backtest.
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
# Project modules
# =============================================================================


fetcher: Any = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher


basket_module: Any = importlib.import_module(
    "02_AI.Shadow.bootstrap_compounding_planner"
)


adapter_module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_account_state_adapter"
)


state_module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_trade_state_machine"
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


CompoundingAccountStateAdapter: Any = (
    adapter_module.CompoundingAccountStateAdapter
)


CompoundingTradeStateMachine: Any = (
    state_module.CompoundingTradeStateMachine
)


# =============================================================================
# Display
# =============================================================================


def section(
    title: str,
) -> None:

    print()

    print(
        "=" * 150
    )

    print(
        title
    )

    print(
        "=" * 150
    )


def line(
    label: str,
    value: Any,
) -> None:

    print(
        f"{label:<44}: {value}"
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


def parse_positive_floats(
    text: str,
    name: str,
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

        result.append(
            value
        )

    if not result:

        raise ValueError(
            f"No {name} supplied"
        )

    return result


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
# Broker calculations
# =============================================================================


def order_type_for(
    direction: str,
) -> int:

    if direction == "LONG":

        return mt5.ORDER_TYPE_BUY

    return mt5.ORDER_TYPE_SELL


def broker_stop_loss(
    *,
    direction: str,
    symbol: str,
    volume: float,
    entry: float,
    stop: float,
) -> float:

    result = mt5.order_calc_profit(
        order_type_for(
            direction
        ),
        symbol,
        volume,
        entry,
        stop,
    )

    if result is None:

        raise RuntimeError(
            (
                "order_calc_profit() failed for SL: "
                f"{last_error()}"
            )
        )

    value = abs(
        float(
            result
        )
    )

    if (
        not math.isfinite(
            value
        )
        or
        value <= 0.0
    ):

        raise RuntimeError(
            "Invalid broker SL calculation"
        )

    return value


def broker_margin(
    *,
    direction: str,
    symbol: str,
    volume: float,
    entry: float,
) -> float:

    result = mt5.order_calc_margin(
        order_type_for(
            direction
        ),
        symbol,
        volume,
        entry,
    )

    if result is None:

        raise RuntimeError(
            (
                "order_calc_margin() failed: "
                f"{last_error()}"
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
            "Invalid broker margin calculation"
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

        open_price = ask

        close_price = bid

    else:

        open_price = bid

        close_price = ask

    result = mt5.order_calc_profit(
        order_type_for(
            direction
        ),
        symbol,
        volume,
        open_price,
        close_price,
    )

    if result is None:

        raise RuntimeError(
            (
                "order_calc_profit() failed for spread: "
                f"{last_error()}"
            )
        )

    value = abs(
        float(
            result
        )
    )

    if not math.isfinite(
        value
    ):

        raise RuntimeError(
            "Invalid broker spread calculation"
        )

    return value


# =============================================================================
# Candidate
# =============================================================================


def make_candidate(
    *,
    leg_id: str,
    direction: str,
    distance: float,
    volume: float,
    loss: float,
    margin: float,
    spread: float,
) -> Any:

    return BasketLegCandidate(
        leg_id=leg_id,
        direction=direction,
        volume=volume,
        projected_stop_loss=loss,
        margin_required=margin,
        spread_cost=spread,
        structural_stop_distance=distance,
    )


# =============================================================================
# Simulated account state
# =============================================================================


def simulated_account(
    *,
    starting_balance: float,
    floating_profit: float,
    basket_margin: float,
) -> tuple[
    float,
    float,
    float,
]:

    equity = (
        starting_balance
        +
        floating_profit
    )

    margin_used = max(
        0.0,
        basket_margin,
    )

    free_margin = max(
        0.0,
        equity
        -
        margin_used,
    )

    return (
        equity,
        free_margin,
        margin_used,
    )


# =============================================================================
# Lifecycle row
# =============================================================================


def lifecycle_row(
    *,
    balance: float,
    distance: float,
    direction: str,
    stage: str,
    floating_profit: float,
    transition: Any,
    equity: float,
    free_margin: float,
    margin_used: float,
) -> dict[
    str,
    Any,
]:

    state = (
        transition.state_after
    )

    return {
        "bal": number(
            balance,
            2,
        ),

        "SL": number(
            distance,
            2,
        ),

        "dir": direction,

        "stage": stage,

        "ok": (
            "YES"
            if transition.valid
            else
            "NO"
        ),

        "action": transition.action,

        "status": state.status,

        "legs": len(
            state.active_legs
        ),

        "vol": number(
            state.active_volume,
            4,
        ),

        "risk": number(
            state.projected_stop_loss,
            3,
        ),

        "eq": number(
            equity,
            3,
        ),

        "free": number(
            free_margin,
            3,
        ),

        "margin": number(
            margin_used,
            3,
        ),

        "float": number(
            floating_profit,
            3,
        ),

        "R": number(
            state.current_r,
            2,
        ),

        "admit": (
            ",".join(
                transition.admitted_leg_ids
            )
            if transition.admitted_leg_ids
            else
            "-"
        ),

        "close": (
            number(
                transition.simulated_close_volume,
                4,
            )
        ),

        "reason": transition.reason,
    }


# =============================================================================
# Main
# =============================================================================


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "PulseViper stateful Exness-calibrated "
            "compounding lifecycle simulation"
        )
    )

    parser.add_argument(
        "--symbol",
        default="XAUUSDm",
    )

    parser.add_argument(
        "--balances",
        default="3,5,10,20,50,100",
    )

    parser.add_argument(
        "--distances",
        default="0.50,0.75,1.00",
    )

    parser.add_argument(
        "--profit-proof-r",
        type=float,
        default=0.35,
    )

    parser.add_argument(
        "--partial-r",
        type=float,
        default=0.85,
    )

    parser.add_argument(
        "--runner-r",
        type=float,
        default=1.50,
    )

    args = parser.parse_args()

    balances = parse_positive_floats(
        args.balances,
        "balance",
    )

    distances = parse_positive_floats(
        args.distances,
        "distance",
    )

    if (
        args.profit_proof_r <= 0.0
        or
        args.partial_r <= 0.0
        or
        args.runner_r <= 0.0
    ):

        raise ValueError(
            "R thresholds must be > 0"
        )

    # =========================================================================
    # Stateful policy
    # =========================================================================

    policy = BootstrapCompoundingPolicy(
        compounding_enabled=True,

        # Lifecycle starts with ONE leg.
        allow_initial_multi_leg=False,

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

        # Later additions need proof.
        add_only_after_profit=True,

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

    adapter = CompoundingAccountStateAdapter(
        planner=planner
    )

    machine = CompoundingTradeStateMachine(
        planner=planner,
        adapter=adapter,
    )

    initialized = False

    # =========================================================================
    # Header
    # =========================================================================

    section(
        "PulseViper XAU AI — "
        "STATEFUL EXNESS COMPOUNDING LIFECYCLE v1.0"
    )

    line(
        "Requested symbol",
        args.symbol,
    )

    line(
        "State machine",
        machine.MODE,
    )

    line(
        "Compounding",
        "SHADOW ENABLED",
    )

    line(
        "Initial entry",
        "ONE LEG",
    )

    line(
        "Maximum active legs",
        policy.max_simultaneous_legs,
    )

    line(
        "Maximum basket volume",
        policy.max_total_volume,
    )

    line(
        "Profit proof",
        (
            f"{args.profit_proof_r}R"
        ),
    )

    line(
        "Partial-book simulation",
        (
            f"{args.partial_r}R"
        ),
    )

    line(
        "Runner simulation",
        (
            f"{args.runner_r}R"
        ),
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
        "FALSE",
    )

    try:

        # =====================================================================
        # MT5
        # =====================================================================

        fetcher.initialize()

        initialized = True

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
            "CONNECTED EXNESS ACCOUNT"
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

        line(
            "Actual positions",
            mt5.positions_total(),
        )

        line(
            "Actual pending orders",
            mt5.orders_total(),
        )

        # =====================================================================
        # Symbol
        # =====================================================================

        symbol = fetcher.resolve_symbol(
            requested_symbol=args.symbol,
            timeframe=mt5.TIMEFRAME_M1,
        )

        if not mt5.symbol_select(
            symbol,
            True,
        ):

            raise RuntimeError(
                (
                    f"symbol_select({symbol}) failed: "
                    f"{last_error()}"
                )
            )

        info = mt5.symbol_info(
            symbol
        )

        tick = mt5.symbol_info_tick(
            symbol
        )

        if info is None:

            raise RuntimeError(
                (
                    f"symbol_info({symbol}) failed: "
                    f"{last_error()}"
                )
            )

        if tick is None:

            raise RuntimeError(
                (
                    f"symbol_info_tick({symbol}) failed: "
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
            point
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

        stops_level_points = float(
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
            or
            volume_min <= 0.0
            or
            volume_step <= 0.0
        ):

            raise RuntimeError(
                "Invalid symbol metadata"
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

        stop_buffer = max(
            stops_level_points
            *
            point,
            tick_size,
        )

        operational_min_distance = (
            spread_price
            +
            stop_buffer
        )

        section(
            "CURRENT BROKER CALIBRATION"
        )

        line(
            "Resolved symbol",
            symbol,
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
            "Spread",
            number(
                spread_price,
                digits,
            ),
        )

        line(
            "Spread points",
            number(
                spread_points,
                2,
            ),
        )

        line(
            "Minimum volume",
            volume_min,
        )

        line(
            "Volume step",
            volume_step,
        )

        line(
            "Operational minimum SL distance",
            number(
                operational_min_distance,
                digits,
            ),
        )

        print()
        print(
            "NOTE: simulated future legs reuse CURRENT broker quote "
            "economics; no future price is assumed."
        )

        # =====================================================================
        # Broker leg calibration
        # =====================================================================

        section(
            "MINIMUM-LOT LEG CALIBRATION"
        )

        calibration_rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        calibrations: dict[
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

            margin = broker_margin(
                direction=direction,
                symbol=symbol,
                volume=volume_min,
                entry=entry,
            )

            spread_cost = (
                broker_spread_cost(
                    direction=direction,
                    symbol=symbol,
                    volume=volume_min,
                    bid=bid,
                    ask=ask,
                )
            )

            for distance in distances:

                geometry_valid = (
                    distance
                    +
                    1e-9
                    >=
                    operational_min_distance
                )

                if direction == "LONG":

                    stop = (
                        entry
                        -
                        distance
                    )

                else:

                    stop = (
                        entry
                        +
                        distance
                    )

                stop = round(
                    stop,
                    digits,
                )

                loss = broker_stop_loss(
                    direction=direction,
                    symbol=symbol,
                    volume=volume_min,
                    entry=entry,
                    stop=stop,
                )

                calibrations[
                    (
                        direction,
                        distance,
                    )
                ] = {
                    "entry": entry,
                    "stop": stop,
                    "loss": loss,
                    "margin": margin,
                    "spread": spread_cost,
                    "geometry_valid": (
                        1.0
                        if geometry_valid
                        else
                        0.0
                    ),
                }

                calibration_rows.append(
                    {
                        "dir": direction,

                        "SL": number(
                            distance,
                            3,
                        ),

                        "geometry": (
                            "OK"
                            if geometry_valid
                            else
                            "TOO_TIGHT"
                        ),

                        "loss": number(
                            loss,
                            4,
                        ),

                        "margin": number(
                            margin,
                            4,
                        ),

                        "spread": number(
                            spread_cost,
                            4,
                        ),
                    }
                )

        print_table(
            calibration_rows,
            (
                "dir",
                "SL",
                "geometry",
                "loss",
                "margin",
                "spread",
            ),
        )

        # =====================================================================
        # Stateful lifecycle
        # =====================================================================

        section(
            "STATEFUL COMPOUNDING LIFECYCLE"
        )

        lifecycle_rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        summary_rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for balance in balances:

            for distance in distances:

                for direction in (
                    "LONG",
                    "SHORT",
                ):

                    calibration = (
                        calibrations[
                            (
                                direction,
                                distance,
                            )
                        ]
                    )

                    if not bool(
                        calibration[
                            "geometry_valid"
                        ]
                    ):

                        summary_rows.append(
                            {
                                "bal": number(
                                    balance,
                                    2,
                                ),

                                "SL": number(
                                    distance,
                                    2,
                                ),

                                "dir": direction,

                                "L1": "NO",

                                "L2": "NO",

                                "partial": "NO",

                                "runner": "NO",

                                "L3": "NO",

                                "final_legs": 0,

                                "final_vol": "0",

                                "spread_paid": "0",

                                "note": (
                                    "STOP_GEOMETRY_TOO_TIGHT"
                                ),
                            }
                        )

                        continue

                    leg_loss = float(
                        calibration[
                            "loss"
                        ]
                    )

                    leg_margin = float(
                        calibration[
                            "margin"
                        ]
                    )

                    leg_spread = float(
                        calibration[
                            "spread"
                        ]
                    )

                    # =========================================================
                    # START LEG-1
                    # =========================================================

                    state = (
                        machine.empty_state()
                    )

                    l1 = make_candidate(
                        leg_id="L1",
                        direction=direction,
                        distance=distance,
                        volume=volume_min,
                        loss=leg_loss,
                        margin=leg_margin,
                        spread=leg_spread,
                    )

                    start_transition = (
                        machine.start(
                            state=state,
                            account_balance=balance,
                            account_equity=balance,
                            account_free_margin=balance,
                            account_margin_used=0.0,
                            candidates=[
                                l1
                            ],
                            volume_min=volume_min,
                            volume_step=volume_step,
                        )
                    )

                    lifecycle_rows.append(
                        lifecycle_row(
                            balance=balance,
                            distance=distance,
                            direction=direction,
                            stage="START_L1",
                            floating_profit=0.0,
                            transition=start_transition,
                            equity=balance,
                            free_margin=balance,
                            margin_used=0.0,
                        )
                    )

                    if not start_transition.valid:

                        summary_rows.append(
                            {
                                "bal": number(
                                    balance,
                                    2,
                                ),

                                "SL": number(
                                    distance,
                                    2,
                                ),

                                "dir": direction,

                                "L1": "NO",

                                "L2": "NO",

                                "partial": "NO",

                                "runner": "NO",

                                "L3": "NO",

                                "final_legs": 0,

                                "final_vol": "0",

                                "spread_paid": "0",

                                "note": (
                                    start_transition.reason
                                ),
                            }
                        )

                        continue

                    state = (
                        start_transition.state_after
                    )

                    # =========================================================
                    # PROFIT PROOF -> TRY LEG-2
                    # =========================================================

                    profit_proof = (
                        state.first_leg_initial_risk
                        *
                        args.profit_proof_r
                    )

                    (
                        equity,
                        free_margin,
                        margin_used,
                    ) = simulated_account(
                        starting_balance=balance,
                        floating_profit=profit_proof,
                        basket_margin=state.basket_margin,
                    )

                    l2 = make_candidate(
                        leg_id="L2",
                        direction=direction,
                        distance=distance,
                        volume=volume_min,
                        loss=leg_loss,
                        margin=leg_margin,
                        spread=leg_spread,
                    )

                    l2_transition = (
                        machine.step(
                            state=state,
                            account_balance=balance,
                            account_equity=equity,
                            account_free_margin=free_margin,
                            account_margin_used=margin_used,
                            current_floating_profit=profit_proof,
                            volume_min=volume_min,
                            volume_step=volume_step,
                            add_candidates=[
                                l2
                            ],
                        )
                    )

                    lifecycle_rows.append(
                        lifecycle_row(
                            balance=balance,
                            distance=distance,
                            direction=direction,
                            stage="PROOF_ADD_L2",
                            floating_profit=profit_proof,
                            transition=l2_transition,
                            equity=equity,
                            free_margin=free_margin,
                            margin_used=margin_used,
                        )
                    )

                    l2_added = (
                        "L2"
                        in
                        l2_transition.admitted_leg_ids
                    )

                    state = (
                        l2_transition.state_after
                    )

                    # =========================================================
                    # PARTIAL / STRUCTURE TRAIL
                    # =========================================================

                    partial_reference_risk = max(
                        state.initial_basket_risk,
                        state.projected_stop_loss,
                    )

                    partial_profit = (
                        partial_reference_risk
                        *
                        args.partial_r
                    )

                    (
                        equity,
                        free_margin,
                        margin_used,
                    ) = simulated_account(
                        starting_balance=balance,
                        floating_profit=partial_profit,
                        basket_margin=state.basket_margin,
                    )

                    partial_transition = (
                        machine.step(
                            state=state,
                            account_balance=balance,
                            account_equity=equity,
                            account_free_margin=free_margin,
                            account_margin_used=margin_used,
                            current_floating_profit=partial_profit,
                            volume_min=volume_min,
                            volume_step=volume_step,
                        )
                    )

                    lifecycle_rows.append(
                        lifecycle_row(
                            balance=balance,
                            distance=distance,
                            direction=direction,
                            stage="PARTIAL_TRAIL",
                            floating_profit=partial_profit,
                            transition=partial_transition,
                            equity=equity,
                            free_margin=free_margin,
                            margin_used=margin_used,
                        )
                    )

                    partial_booked = (
                        partial_transition.simulated_close_volume
                        >
                        0.0
                    )

                    state = (
                        partial_transition.state_after
                    )

                    # =========================================================
                    # RUNNER
                    # =========================================================

                    runner_reference_risk = max(
                        state.initial_basket_risk,
                        state.projected_stop_loss,
                    )

                    runner_profit = (
                        runner_reference_risk
                        *
                        args.runner_r
                    )

                    (
                        equity,
                        free_margin,
                        margin_used,
                    ) = simulated_account(
                        starting_balance=balance,
                        floating_profit=runner_profit,
                        basket_margin=state.basket_margin,
                    )

                    runner_transition = (
                        machine.step(
                            state=state,
                            account_balance=balance,
                            account_equity=equity,
                            account_free_margin=free_margin,
                            account_margin_used=margin_used,
                            current_floating_profit=runner_profit,
                            volume_min=volume_min,
                            volume_step=volume_step,
                        )
                    )

                    lifecycle_rows.append(
                        lifecycle_row(
                            balance=balance,
                            distance=distance,
                            direction=direction,
                            stage="RUNNER",
                            floating_profit=runner_profit,
                            transition=runner_transition,
                            equity=equity,
                            free_margin=free_margin,
                            margin_used=margin_used,
                        )
                    )

                    state = (
                        runner_transition.state_after
                    )

                    runner_active = (
                        state.runner_mode
                    )

                    # =========================================================
                    # OPTIONAL LATER LEG-3
                    # =========================================================

                    (
                        equity,
                        free_margin,
                        margin_used,
                    ) = simulated_account(
                        starting_balance=balance,
                        floating_profit=runner_profit,
                        basket_margin=state.basket_margin,
                    )

                    l3 = make_candidate(
                        leg_id="L3",
                        direction=direction,
                        distance=distance,
                        volume=volume_min,
                        loss=leg_loss,
                        margin=leg_margin,
                        spread=leg_spread,
                    )

                    l3_transition = (
                        machine.step(
                            state=state,
                            account_balance=balance,
                            account_equity=equity,
                            account_free_margin=free_margin,
                            account_margin_used=margin_used,
                            current_floating_profit=runner_profit,
                            volume_min=volume_min,
                            volume_step=volume_step,
                            add_candidates=[
                                l3
                            ],
                        )
                    )

                    lifecycle_rows.append(
                        lifecycle_row(
                            balance=balance,
                            distance=distance,
                            direction=direction,
                            stage="RUNNER_ADD_L3",
                            floating_profit=runner_profit,
                            transition=l3_transition,
                            equity=equity,
                            free_margin=free_margin,
                            margin_used=margin_used,
                        )
                    )

                    l3_added = (
                        "L3"
                        in
                        l3_transition.admitted_leg_ids
                    )

                    final_state = (
                        l3_transition.state_after
                    )

                    summary_rows.append(
                        {
                            "bal": number(
                                balance,
                                2,
                            ),

                            "SL": number(
                                distance,
                                2,
                            ),

                            "dir": direction,

                            "L1": "YES",

                            "L2": (
                                "YES"
                                if l2_added
                                else
                                "NO"
                            ),

                            "partial": (
                                "YES"
                                if partial_booked
                                else
                                "NO"
                            ),

                            "runner": (
                                "YES"
                                if runner_active
                                else
                                "NO"
                            ),

                            "L3": (
                                "YES"
                                if l3_added
                                else
                                "NO"
                            ),

                            "final_legs": len(
                                final_state.active_legs
                            ),

                            "final_vol": number(
                                final_state.active_volume,
                                4,
                            ),

                            "spread_paid": number(
                                final_state.cumulative_spread_cost,
                                3,
                            ),

                            "note": (
                                l3_transition.reason
                            ),
                        }
                    )

        print_table(
            lifecycle_rows,
            (
                "bal",
                "SL",
                "dir",
                "stage",
                "ok",
                "action",
                "status",
                "legs",
                "vol",
                "risk",
                "eq",
                "free",
                "margin",
                "float",
                "R",
                "admit",
                "close",
                "reason",
            ),
        )

        # =====================================================================
        # Summary
        # =====================================================================

        section(
            "LIFECYCLE SUMMARY"
        )

        print_table(
            summary_rows,
            (
                "bal",
                "SL",
                "dir",
                "L1",
                "L2",
                "partial",
                "runner",
                "L3",
                "final_legs",
                "final_vol",
                "spread_paid",
                "note",
            ),
        )

        # =====================================================================
        # Interpretation
        # =====================================================================

        section(
            "WHAT THIS OPERATION IS TESTING"
        )

        print(
            "- structural stop distance is preserved"
        )

        print(
            "- Leg-2 requires favorable-profit proof"
        )

        print(
            "- current account free margin is checked before add-on"
        )

        print(
            "- combined basket loss / margin / spread remains bounded"
        )

        print(
            "- partial booking gets priority over a fresh add-on"
        )

        print(
            "- 0.02 basket may release 0.01 and retain a 0.01 runner"
        )

        print(
            "- cumulative paid spread survives simulated scale-out"
        )

        print(
            "- optional later leg is independently re-admitted"
        )

        print(
            "- tiny balances may remain one-leg only even with compounding ON"
        )

        print(
            "- compounding ON means permission to compound when capacity exists"
        )

        print(
            "- compounding ON does NOT mean blindly force multiple orders"
        )

        # =====================================================================
        # Safety
        # =====================================================================

        section(
            "SAFETY STATUS"
        )

        line(
            "MT5 access",
            "READ ONLY",
        )

        line(
            "order_calc_profit",
            "USED",
        )

        line(
            "order_calc_margin",
            "USED",
        )

        line(
            "order_send",
            "NEVER CALLED",
        )

        line(
            "Actual orders opened",
            "0",
        )

        line(
            "Actual positions closed",
            "0",
        )

        line(
            "Actual SL/TP modifications",
            "0",
        )

        line(
            "Production RiskEngine",
            "UNCHANGED / UNWIRED",
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