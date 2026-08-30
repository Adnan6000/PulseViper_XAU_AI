from __future__ import annotations

import hashlib
import json
import math
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping


CANONICAL_GOLD_SYMBOL = "XAUUSD"
CANONICAL_ASSET = "GOLD"
CANONICAL_QUOTE_CURRENCY = "USD"

DEFAULT_MAX_TICK_AGE_SECONDS = 180
DEFAULT_ATR_PERIOD = 14
DEFAULT_ATR_HISTORY_BARS = 250

BROKER_CONTRACT_FINGERPRINT_VERSION = (
    "XAUUSD_BROKER_CONTRACT_FINGERPRINT_V1"
)

EQUITY_LIKE_MARKERS = (
    " INC",
    " INC.",
    " CORP",
    " CORPORATION",
    " PLC",
    " LTD",
    " LIMITED",
    " NYSE",
    " NASDAQ",
    " STOCK",
    " SHARE",
    " EQUITY",
)

METAL_LIKE_MARKERS = (
    "GOLD",
    "XAU",
    "METAL",
    "PRECIOUS",
    "SPOT",
)


class GoldSymbolResolutionError(RuntimeError):
    pass


class BrokerCostSnapshotError(RuntimeError):
    pass


@dataclass(frozen=True)
class GoldSymbolResolution:
    canonical_symbol: str
    broker_symbol: str
    normalized_broker_symbol: str
    candidate_count: int
    rejected_gold_like_count: int
    candidates: tuple[dict[str, Any], ...]
    rejected_gold_like_symbols: tuple[dict[str, Any], ...]
    selection_policy: tuple[str, ...]

    def to_document(
        self,
    ) -> dict[str, Any]:

        return {
            "canonical_symbol": (
                self.canonical_symbol
            ),
            "broker_symbol": (
                self.broker_symbol
            ),
            "normalized_broker_symbol": (
                self.normalized_broker_symbol
            ),
            "candidate_count": (
                self.candidate_count
            ),
            "rejected_gold_like_count": (
                self.rejected_gold_like_count
            ),
            "candidates": [
                dict(
                    candidate
                )
                for candidate
                in self.candidates
            ],
            "rejected_gold_like_symbols": [
                dict(
                    candidate
                )
                for candidate
                in self.rejected_gold_like_symbols
            ],
            "selection_policy": list(
                self.selection_policy
            ),
            "suffix_or_prefix_hardcoded": (
                False
            ),
        }


def normalize_symbol_token(
    value: Any,
) -> str:

    return re.sub(
        r"[^A-Z0-9]",
        "",
        str(
            value
        ).upper(),
    )


def _safe_float(
    value: Any,
) -> float | None:

    try:

        result = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    if not math.isfinite(
        result
    ):

        return None

    return result


def _positive_float(
    value: Any,
) -> float | None:

    result = (
        _safe_float(
            value
        )
    )

    if (
        result is None
        or
        result <= 0.0
    ):

        return None

    return result


def _safe_int(
    value: Any,
) -> int | None:

    try:

        return int(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


def _attr(
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


def _upper_text(
    value: Any,
) -> str:

    return str(
        value
        or
        ""
    ).strip().upper()


def _looks_equity_like(
    *,
    name: str,
    description: str,
    path: str,
) -> bool:

    combined = (
        f" {name} {description} {path} "
        .upper()
    )

    return any(
        marker
        in combined
        for marker
        in EQUITY_LIKE_MARKERS
    )


def _looks_metal_like(
    *,
    name: str,
    description: str,
    path: str,
) -> bool:

    combined = (
        f"{name} {description} {path}"
        .upper()
    )

    return any(
        marker
        in combined
        for marker
        in METAL_LIKE_MARKERS
    )


def gold_usd_semantics(
    symbol_info: Any,
) -> dict[str, Any]:

    name = str(
        _attr(
            symbol_info,
            "name",
            "",
        )
    )

    description = str(
        _attr(
            symbol_info,
            "description",
            "",
        )
    )

    path = str(
        _attr(
            symbol_info,
            "path",
            "",
        )
    )

    currency_base = (
        _upper_text(
            _attr(
                symbol_info,
                "currency_base",
                "",
            )
        )
    )

    currency_profit = (
        _upper_text(
            _attr(
                symbol_info,
                "currency_profit",
                "",
            )
        )
    )

    normalized_name = (
        normalize_symbol_token(
            name
        )
    )

    name_xauusd_family = bool(
        "XAUUSD"
        in normalized_name
    )

    name_gold_family = bool(
        normalized_name.startswith(
            "GOLD"
        )
    )

    semantic_xau_usd = bool(
        currency_base
        ==
        "XAU"
        and
        currency_profit
        ==
        "USD"
    )

    equity_like = (
        _looks_equity_like(
            name=name,
            description=description,
            path=path,
        )
    )

    metal_like = (
        _looks_metal_like(
            name=name,
            description=description,
            path=path,
        )
    )

    xauusd_name_contract = bool(
        name_xauusd_family
        and
        currency_base
        in {
            "",
            "XAU",
        }
        and
        currency_profit
        in {
            "",
            "USD",
        }
        and
        not equity_like
    )

    gold_name_contract = bool(
        name_gold_family
        and
        currency_base
        in {
            "",
            "XAU",
        }
        and
        currency_profit
        in {
            "",
            "USD",
        }
        and
        metal_like
        and
        not equity_like
    )

    accepted = bool(
        semantic_xau_usd
        or
        xauusd_name_contract
        or
        gold_name_contract
    )

    return {
        "accepted": (
            accepted
        ),
        "name": (
            name
        ),
        "normalized_name": (
            normalized_name
        ),
        "description": (
            description
        ),
        "path": (
            path
        ),
        "currency_base": (
            currency_base
        ),
        "currency_profit": (
            currency_profit
        ),
        "name_xauusd_family": (
            name_xauusd_family
        ),
        "name_gold_family": (
            name_gold_family
        ),
        "semantic_xau_usd": (
            semantic_xau_usd
        ),
        "xauusd_name_contract": (
            xauusd_name_contract
        ),
        "gold_name_contract": (
            gold_name_contract
        ),
        "equity_like": (
            equity_like
        ),
        "metal_like": (
            metal_like
        ),
    }


def _identity_score(
    symbol_info: Any,
) -> tuple[
    int,
    list[str],
]:

    semantics = (
        gold_usd_semantics(
            symbol_info
        )
    )

    if not bool(
        semantics[
            "accepted"
        ]
    ):

        return (
            0,
            [
                (
                    "REJECTED_NOT_CANONICAL_"
                    "XAUUSD_GOLD_USD"
                )
            ],
        )

    normalized_name = str(
        semantics[
            "normalized_name"
        ]
    )

    score = 0

    reasons: list[
        str
    ] = []

    if (
        normalized_name
        ==
        "XAUUSD"
    ):

        score += 1000

        reasons.append(
            "NORMALIZED_NAME_EXACT_XAUUSD"
        )

    elif (
        "XAUUSD"
        in normalized_name
    ):

        score += 900

        reasons.append(
            "NORMALIZED_NAME_XAUUSD_FAMILY"
        )

    elif (
        normalized_name
        ==
        "GOLD"
    ):

        score += 850

        reasons.append(
            "NORMALIZED_NAME_EXACT_GOLD"
        )

    elif normalized_name.startswith(
        "GOLD"
    ):

        score += 800

        reasons.append(
            "NORMALIZED_NAME_GOLD_FAMILY"
        )

    if bool(
        semantics[
            "semantic_xau_usd"
        ]
    ):

        score += 300

        reasons.append(
            "CONTRACT_CURRENCY_XAU_USD"
        )

    if bool(
        semantics[
            "metal_like"
        ]
    ):

        score += 50

        reasons.append(
            "METAL_SEMANTICS_PRESENT"
        )

    trade_mode = (
        _safe_int(
            _attr(
                symbol_info,
                "trade_mode",
                None,
            )
        )
    )

    if (
        trade_mode is not None
        and
        trade_mode != 0
    ):

        score += 20

        reasons.append(
            "TRADE_MODE_ENABLED"
        )

    if bool(
        _attr(
            symbol_info,
            "visible",
            False,
        )
    ):

        score += 10

        reasons.append(
            "VISIBLE_IN_MARKET_WATCH"
        )

    return (
        score,
        reasons,
    )


def _tick_document(
    mt5_module: Any,
    symbol_name: str,
    *,
    now_epoch: int,
    max_tick_age_seconds: int,
) -> dict[str, Any]:

    tick = (
        mt5_module
        .symbol_info_tick(
            symbol_name
        )
    )

    if tick is None:

        return {
            "available": False,
            "valid_bid_ask": False,
            "fresh": False,
            "tick_age_seconds": None,
        }

    bid = (
        _safe_float(
            _attr(
                tick,
                "bid",
                None,
            )
        )
    )

    ask = (
        _safe_float(
            _attr(
                tick,
                "ask",
                None,
            )
        )
    )

    tick_time = (
        _safe_int(
            _attr(
                tick,
                "time",
                None,
            )
        )
    )

    tick_age_seconds: (
        int
        |
        None
    ) = None

    if (
        tick_time is not None
        and
        tick_time > 0
    ):

        tick_age_seconds = max(
            0,
            int(
                now_epoch
            )
            -
            tick_time,
        )

    valid_bid_ask = bool(
        bid is not None
        and
        ask is not None
        and
        bid > 0.0
        and
        ask > 0.0
        and
        ask >= bid
    )

    fresh = bool(
        valid_bid_ask
        and
        tick_age_seconds
        is not None
        and
        tick_age_seconds
        <=
        int(
            max_tick_age_seconds
        )
    )

    return {
        "available": True,
        "valid_bid_ask": (
            valid_bid_ask
        ),
        "fresh": (
            fresh
        ),
        "tick_age_seconds": (
            tick_age_seconds
        ),
        "max_tick_age_seconds": int(
            max_tick_age_seconds
        ),
        "bid": (
            bid
        ),
        "ask": (
            ask
        ),
        "last": (
            _safe_float(
                _attr(
                    tick,
                    "last",
                    None,
                )
            )
        ),
        "time": (
            tick_time
        ),
        "time_msc": (
            _safe_int(
                _attr(
                    tick,
                    "time_msc",
                    None,
                )
            )
        ),
    }


def _spread_document(
    symbol_info: Any,
    tick: dict[str, Any],
    *,
    atr14: float | None,
) -> dict[str, Any]:

    if not bool(
        tick.get(
            "valid_bid_ask",
            False,
        )
    ):

        return {
            "available": False,
            "usable_for_runtime_costs": False,
            "reason": (
                "VALID_BID_ASK_REQUIRED"
            ),
            "spread_atr14": None,
        }

    bid = float(
        tick[
            "bid"
        ]
    )

    ask = float(
        tick[
            "ask"
        ]
    )

    spread_price = (
        ask
        -
        bid
    )

    mid = (
        ask
        +
        bid
    ) / 2.0

    point = (
        _positive_float(
            _attr(
                symbol_info,
                "point",
                None,
            )
        )
    )

    tick_size = (
        _positive_float(
            _attr(
                symbol_info,
                "trade_tick_size",
                None,
            )
        )
    )

    spread_points = (
        spread_price
        /
        point
        if point is not None
        else None
    )

    spread_ticks = (
        spread_price
        /
        tick_size
        if tick_size is not None
        else None
    )

    spread_bps = (
        spread_price
        /
        mid
        *
        10000.0
        if mid > 0.0
        else None
    )

    fresh = bool(
        tick.get(
            "fresh",
            False,
        )
    )

    spread_atr14: (
        float
        |
        None
    ) = None

    if (
        fresh
        and
        atr14 is not None
        and
        math.isfinite(
            atr14
        )
        and
        atr14 > 0.0
    ):

        spread_atr14 = (
            spread_price
            /
            atr14
        )

    return {
        "available": True,
        "usable_for_runtime_costs": (
            fresh
        ),
        "fresh_tick_required": True,
        "fresh_tick": (
            fresh
        ),
        "stale_reason": (
            None
            if fresh
            else
            (
                "STALE_TICK_SPREAD_NOT_VALID_"
                "FOR_RUNTIME_COSTS"
            )
        ),
        "bid": (
            bid
        ),
        "ask": (
            ask
        ),
        "mid": (
            mid
        ),
        "spread_price": (
            spread_price
        ),
        "spread_points": (
            spread_points
        ),
        "spread_ticks": (
            spread_ticks
        ),
        "spread_bps": (
            spread_bps
        ),
        "spread_atr14": (
            spread_atr14
        ),
        "point": (
            point
        ),
        "tick_size": (
            tick_size
        ),
    }


def _contract_document(
    symbol_info: Any,
) -> dict[str, Any]:

    fields = (
        "name",
        "description",
        "path",
        "currency_base",
        "currency_profit",
        "currency_margin",
        "digits",
        "point",
        "trade_tick_size",
        "trade_tick_value",
        "trade_tick_value_profit",
        "trade_tick_value_loss",
        "trade_contract_size",
        "trade_stops_level",
        "trade_freeze_level",
        "volume_min",
        "volume_max",
        "volume_step",
        "volume_limit",
        "spread",
        "spread_float",
        "trade_mode",
        "trade_calc_mode",
        "filling_mode",
        "order_mode",
        "swap_mode",
        "swap_long",
        "swap_short",
        "margin_initial",
        "margin_maintenance",
        "visible",
    )

    return {
        field: (
            _attr(
                symbol_info,
                field,
                None,
            )
        )
        for field
        in fields
    }


def _fingerprint_safe_value(
    value: Any,
) -> Any:

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ) or value is None:

        return value

    return str(
        value
    )


def broker_contract_fingerprint(
    *,
    broker_server: str,
    contract: Mapping[
        str,
        Any,
    ],
) -> str:

    fingerprint_fields = (
        "name",
        "currency_base",
        "currency_profit",
        "currency_margin",
        "digits",
        "point",
        "trade_tick_size",
        "trade_tick_value",
        "trade_tick_value_profit",
        "trade_tick_value_loss",
        "trade_contract_size",
        "trade_stops_level",
        "trade_freeze_level",
        "volume_min",
        "volume_max",
        "volume_step",
        "volume_limit",
        "trade_mode",
        "trade_calc_mode",
        "filling_mode",
        "order_mode",
        "margin_initial",
        "margin_maintenance",
    )

    payload = {
        "version": (
            BROKER_CONTRACT_FINGERPRINT_VERSION
        ),
        "canonical_symbol": (
            CANONICAL_GOLD_SYMBOL
        ),
        "broker_server": (
            normalize_symbol_token(
                broker_server
            )
        ),
        "contract": {
            field: (
                _fingerprint_safe_value(
                    contract.get(
                        field
                    )
                )
            )
            for field
            in fingerprint_fields
        },
    }

    serialized = (
        json.dumps(
            payload,
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
            ensure_ascii=True,
            allow_nan=False,
        )
        .encode(
            "utf-8"
        )
    )

    return (
        hashlib
        .sha256(
            serialized
        )
        .hexdigest()
    )


def _rate_field(
    row: Any,
    field: str,
) -> float:

    value: Any

    if isinstance(
        row,
        Mapping,
    ):

        value = (
            row[
                field
            ]
        )

    else:

        try:

            value = (
                row[
                    field
                ]
            )

        except (
            TypeError,
            KeyError,
            IndexError,
        ):

            value = getattr(
                row,
                field,
            )

    result = (
        _safe_float(
            value
        )
    )

    if result is None:

        raise BrokerCostSnapshotError(
            (
                "INVALID_RATE_FIELD:"
                f"{field}"
            )
        )

    return result


def read_m5_atr14(
    mt5_module: Any,
    symbol_name: str,
    *,
    period: int = (
        DEFAULT_ATR_PERIOD
    ),
    history_bars: int = (
        DEFAULT_ATR_HISTORY_BARS
    ),
) -> dict[str, Any]:

    if period < 2:

        raise ValueError(
            "ATR_PERIOD_MUST_BE_AT_LEAST_2"
        )

    if (
        history_bars
        <
        period
        +
        1
    ):

        raise ValueError(
            "ATR_HISTORY_BARS_TOO_SMALL"
        )

    timeframe_m5 = getattr(
        mt5_module,
        "TIMEFRAME_M5",
        None,
    )

    if timeframe_m5 is None:

        return {
            "available": False,
            "reason": (
                "MT5_TIMEFRAME_M5_UNAVAILABLE"
            ),
        }

    rates = (
        mt5_module
        .copy_rates_from_pos(
            symbol_name,
            timeframe_m5,
            1,
            history_bars,
        )
    )

    if rates is None:

        return {
            "available": False,
            "reason": (
                "MT5_COPY_RATES_RETURNED_NONE"
            ),
        }

    rows = list(
        rates
    )

    if (
        len(
            rows
        )
        <
        period
        +
        1
    ):

        return {
            "available": False,
            "reason": (
                "INSUFFICIENT_COMPLETED_M5_BARS"
            ),
            "rows": len(
                rows
            ),
        }

    true_ranges: list[
        float
    ] = []

    for index in range(
        1,
        len(
            rows
        ),
    ):

        high = (
            _rate_field(
                rows[
                    index
                ],
                "high",
            )
        )

        low = (
            _rate_field(
                rows[
                    index
                ],
                "low",
            )
        )

        previous_close = (
            _rate_field(
                rows[
                    index
                    -
                    1
                ],
                "close",
            )
        )

        true_ranges.append(
            max(
                high
                -
                low,
                abs(
                    high
                    -
                    previous_close
                ),
                abs(
                    low
                    -
                    previous_close
                ),
            )
        )

    if (
        len(
            true_ranges
        )
        <
        period
    ):

        return {
            "available": False,
            "reason": (
                "INSUFFICIENT_TRUE_RANGE_ROWS"
            ),
        }

    atr14 = (
        sum(
            true_ranges[
                -period:
            ]
        )
        /
        float(
            period
        )
    )

    if (
        not math.isfinite(
            atr14
        )
        or
        atr14 <= 0.0
    ):

        return {
            "available": False,
            "reason": (
                "INVALID_ATR_VALUE"
            ),
        }

    return {
        "available": True,
        "timeframe": (
            "M5"
        ),
        "period": int(
            period
        ),
        "method": (
            "SIMPLE_MEAN_TRUE_RANGE"
        ),
        "source_completed_bars": len(
            rows
        ),
        "atr14": float(
            atr14
        ),
    }


class CanonicalGoldResolver:

    def __init__(
        self,
        mt5_module: Any,
        *,
        max_tick_age_seconds: int = (
            DEFAULT_MAX_TICK_AGE_SECONDS
        ),
        now_provider: Callable[
            [],
            float,
        ] = time.time,
    ) -> None:

        if (
            max_tick_age_seconds
            <=
            0
        ):

            raise ValueError(
                (
                    "MAX_TICK_AGE_SECONDS_"
                    "MUST_BE_POSITIVE"
                )
            )

        self._mt5 = (
            mt5_module
        )

        self._max_tick_age_seconds = int(
            max_tick_age_seconds
        )

        self._now_provider = (
            now_provider
        )

    def resolve(
        self,
    ) -> GoldSymbolResolution:

        symbols = (
            self._mt5
            .symbols_get()
        )

        if symbols is None:

            raise GoldSymbolResolutionError(
                "MT5_SYMBOLS_GET_FAILED"
            )

        now_epoch = int(
            self._now_provider()
        )

        candidates: list[
            dict[str, Any]
        ] = []

        rejected: list[
            dict[str, Any]
        ] = []

        for symbol_info in symbols:

            semantics = (
                gold_usd_semantics(
                    symbol_info
                )
            )

            name = str(
                semantics[
                    "name"
                ]
            )

            normalized_name = str(
                semantics[
                    "normalized_name"
                ]
            )

            looks_gold_like = bool(
                "XAU"
                in normalized_name
                or
                "GOLD"
                in normalized_name
            )

            if not bool(
                semantics[
                    "accepted"
                ]
            ):

                if looks_gold_like:

                    rejected.append(
                        {
                            "name": (
                                name
                            ),
                            "normalized_name": (
                                normalized_name
                            ),
                            "currency_base": (
                                semantics[
                                    "currency_base"
                                ]
                            ),
                            "currency_profit": (
                                semantics[
                                    "currency_profit"
                                ]
                            ),
                            "description": (
                                semantics[
                                    "description"
                                ]
                            ),
                            "path": (
                                semantics[
                                    "path"
                                ]
                            ),
                            "reason": (
                                "NOT_CANONICAL_"
                                "XAUUSD_GOLD_USD"
                            ),
                        }
                    )

                continue

            (
                score,
                reasons,
            ) = (
                _identity_score(
                    symbol_info
                )
            )

            tick = (
                _tick_document(
                    self._mt5,
                    name,
                    now_epoch=(
                        now_epoch
                    ),
                    max_tick_age_seconds=(
                        self
                        ._max_tick_age_seconds
                    ),
                )
            )

            spread = (
                _spread_document(
                    symbol_info,
                    tick,
                    atr14=None,
                )
            )

            candidates.append(
                {
                    "name": (
                        name
                    ),
                    "normalized_name": (
                        normalized_name
                    ),
                    "identity_score": int(
                        score
                    ),
                    "identity_reasons": (
                        reasons
                    ),
                    "semantic_xau_usd": bool(
                        semantics[
                            "semantic_xau_usd"
                        ]
                    ),
                    "currency_base": (
                        semantics[
                            "currency_base"
                        ]
                    ),
                    "currency_profit": (
                        semantics[
                            "currency_profit"
                        ]
                    ),
                    "description": (
                        semantics[
                            "description"
                        ]
                    ),
                    "path": (
                        semantics[
                            "path"
                        ]
                    ),
                    "trade_mode": (
                        _safe_int(
                            _attr(
                                symbol_info,
                                "trade_mode",
                                None,
                            )
                        )
                    ),
                    "visible": bool(
                        _attr(
                            symbol_info,
                            "visible",
                            False,
                        )
                    ),
                    "tick": (
                        tick
                    ),
                    "spread": (
                        spread
                    ),
                }
            )

        if not candidates:

            raise GoldSymbolResolutionError(
                (
                    "NO_CANONICAL_XAUUSD_"
                    "GOLD_USD_SYMBOL_FOUND"
                )
            )

        candidates.sort(
            key=(
                self
                ._candidate_sort_key
            ),
            reverse=True,
        )

        best = (
            candidates[
                0
            ]
        )

        return (
            GoldSymbolResolution(
                canonical_symbol=(
                    CANONICAL_GOLD_SYMBOL
                ),
                broker_symbol=str(
                    best[
                        "name"
                    ]
                ),
                normalized_broker_symbol=str(
                    best[
                        "normalized_name"
                    ]
                ),
                candidate_count=len(
                    candidates
                ),
                rejected_gold_like_count=len(
                    rejected
                ),
                candidates=tuple(
                    candidates
                ),
                rejected_gold_like_symbols=tuple(
                    rejected
                ),
                selection_policy=(
                    (
                        "CANONICAL_XAU_USD_"
                        "SEMANTICS_REQUIRED"
                    ),
                    (
                        "TRADE_MODE_ENABLED_"
                        "PREFERRED"
                    ),
                    (
                        "VISIBLE_SYMBOL_PREFERRED"
                    ),
                    (
                        "FRESH_TICK_PREFERRED"
                    ),
                    (
                        "VALID_BID_ASK_PREFERRED"
                    ),
                    (
                        "XAUUSD_OR_GOLD_"
                        "IDENTITY_SCORE"
                    ),
                    (
                        "LOWER_FRESH_NORMALIZED_"
                        "SPREAD_TIEBREAK"
                    ),
                    (
                        "SHORTER_SYMBOL_NAME_"
                        "FINAL_TIEBREAK"
                    ),
                ),
            )
        )

    @staticmethod
    def _candidate_sort_key(
        candidate: Mapping[
            str,
            Any,
        ],
    ) -> tuple[
        int,
        int,
        int,
        int,
        int,
        float,
        int,
    ]:

        trade_mode = (
            _safe_int(
                candidate.get(
                    "trade_mode"
                )
            )
        )

        trade_enabled = int(
            trade_mode is not None
            and
            trade_mode != 0
        )

        visible = int(
            bool(
                candidate.get(
                    "visible",
                    False,
                )
            )
        )

        tick = candidate.get(
            "tick",
            {},
        )

        if not isinstance(
            tick,
            Mapping,
        ):

            tick = {}

        fresh = int(
            bool(
                tick.get(
                    "fresh",
                    False,
                )
            )
        )

        valid_bid_ask = int(
            bool(
                tick.get(
                    "valid_bid_ask",
                    False,
                )
            )
        )

        identity_score = int(
            candidate.get(
                "identity_score",
                0,
            )
        )

        spread = candidate.get(
            "spread",
            {},
        )

        if not isinstance(
            spread,
            Mapping,
        ):

            spread = {}

        spread_bps = (
            _safe_float(
                spread.get(
                    "spread_bps"
                )
            )
            if fresh
            else None
        )

        spread_rank = (
            -spread_bps
            if spread_bps is not None
            else
            -1_000_000_000.0
        )

        name_length_rank = (
            -len(
                str(
                    candidate.get(
                        "name",
                        "",
                    )
                )
            )
        )

        return (
            trade_enabled,
            visible,
            fresh,
            valid_bid_ask,
            identity_score,
            spread_rank,
            name_length_rank,
        )


class BrokerCostAdapter:

    def __init__(
        self,
        mt5_module: Any,
        *,
        max_tick_age_seconds: int = (
            DEFAULT_MAX_TICK_AGE_SECONDS
        ),
        now_provider: Callable[
            [],
            float,
        ] = time.time,
    ) -> None:

        self._mt5 = (
            mt5_module
        )

        self._max_tick_age_seconds = int(
            max_tick_age_seconds
        )

        self._now_provider = (
            now_provider
        )

        self._resolver = (
            CanonicalGoldResolver(
                mt5_module,
                max_tick_age_seconds=(
                    max_tick_age_seconds
                ),
                now_provider=(
                    now_provider
                ),
            )
        )

    def snapshot(
        self,
        *,
        include_m5_atr: bool = True,
    ) -> dict[str, Any]:

        resolution = (
            self._resolver
            .resolve()
        )

        symbol_info = (
            self._mt5
            .symbol_info(
                resolution
                .broker_symbol
            )
        )

        if symbol_info is None:

            raise BrokerCostSnapshotError(
                (
                    "RESOLVED_SYMBOL_INFO_"
                    "UNAVAILABLE:"
                    f"{resolution.broker_symbol}"
                )
            )

        now_epoch = int(
            self._now_provider()
        )

        tick = (
            _tick_document(
                self._mt5,
                resolution.broker_symbol,
                now_epoch=(
                    now_epoch
                ),
                max_tick_age_seconds=(
                    self
                    ._max_tick_age_seconds
                ),
            )
        )

        if include_m5_atr:

            atr = (
                read_m5_atr14(
                    self._mt5,
                    resolution.broker_symbol,
                )
            )

        else:

            atr = {
                "available": False,
                "reason": (
                    "ATR_NOT_REQUESTED"
                ),
            }

        atr14 = (
            _safe_float(
                atr.get(
                    "atr14"
                )
            )
            if bool(
                atr.get(
                    "available",
                    False,
                )
            )
            else None
        )

        spread = (
            _spread_document(
                symbol_info,
                tick,
                atr14=(
                    atr14
                ),
            )
        )

        account_info = (
            self._mt5
            .account_info()
        )

        broker_server = str(
            _attr(
                account_info,
                "server",
                "",
            )
        )

        contract = (
            _contract_document(
                symbol_info
            )
        )

        fingerprint = (
            broker_contract_fingerprint(
                broker_server=(
                    broker_server
                ),
                contract=(
                    contract
                ),
            )
        )

        return {
            "valid": True,
            "canonical_instrument": {
                "canonical_symbol": (
                    CANONICAL_GOLD_SYMBOL
                ),
                "asset": (
                    CANONICAL_ASSET
                ),
                "quote_currency": (
                    CANONICAL_QUOTE_CURRENCY
                ),
            },
            "resolution": (
                resolution
                .to_document()
            ),
            "broker_identity": {
                "source": (
                    "MT5_ACCOUNT_SERVER"
                ),
                "server": (
                    broker_server
                ),
                "normalized_server": (
                    normalize_symbol_token(
                        broker_server
                    )
                ),
                "account_login_emitted": (
                    False
                ),
                "account_holder_name_emitted": (
                    False
                ),
            },
            "contract": (
                contract
            ),
            "contract_fingerprint": {
                "version": (
                    BROKER_CONTRACT_FINGERPRINT_VERSION
                ),
                "sha256": (
                    fingerprint
                ),
            },
            "tick": (
                tick
            ),
            "spread": {
                **spread,
                "normalization_policy": {
                    "broker_name_based_spread_assumptions": (
                        False
                    ),
                    "fresh_tick_required": (
                        True
                    ),
                    "preferred_cross_broker_measures": [
                        "spread_price",
                        "spread_ticks",
                        "spread_bps",
                        "spread_atr14",
                    ],
                    "raw_spread_points": (
                        "BROKER_SPECIFIC_DIAGNOSTIC"
                    ),
                },
            },
            "m5_atr": (
                atr
            ),
            "safety": {
                "read_only_market_adapter": (
                    True
                ),
                "orders_sent": (
                    False
                ),
                "positions_modified": (
                    False
                ),
                "risk_engine_modified": (
                    False
                ),
                "sizing_modified": (
                    False
                ),
                "live_authorized": (
                    False
                ),
            },
        }