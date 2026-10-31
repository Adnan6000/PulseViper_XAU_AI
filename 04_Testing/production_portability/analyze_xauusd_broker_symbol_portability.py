from __future__ import annotations

import importlib
import json
import math
import re
import sys
import time
from pathlib import Path
from typing import Any

import MetaTrader5 as mt5
import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


sweep_module: Any = importlib.import_module(
    "04_Testing.research.legacy_ml.tune_xauusd_hierarchical_model_v4_stage_b"
)

temporal_module: Any = importlib.import_module(
    "04_Testing.research.legacy_ml.analyze_xauusd_hierarchical_model_v4_stage_b_temporal_robustness"
)

trainer_module: Any = importlib.import_module(
    "02_AI.Models.xauusd_hierarchical_model_v4_trainer"
)


XAUUSDHierarchicalModelV4Trainer: Any = (
    trainer_module.XAUUSDHierarchicalModelV4Trainer
)


ANALYSIS_VERSION = (
    "XAUUSD_BROKER_SYMBOL_PORTABILITY_V2"
)

CANONICAL_SYMBOL = "XAUUSD"

ATR_PERIOD = 14

ATR_HISTORY_BARS = 250

MAX_CANDIDATES_TO_REPORT = 20

MAX_LIVE_TICK_AGE_SECONDS = 180


BROKER_SENSITIVE_FEATURE_TERMS = (
    "spread",
    "tick_volume",
)


def _normalize_token(
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


def _dataset_identity(
    frame: pd.DataFrame,
) -> dict[str, Any]:

    return (
        temporal_module
        ._dataset_identity(
            frame
        )
    )


def _broker_sensitive_features(
    features: list[str],
) -> dict[str, Any]:

    groups: dict[
        str,
        list[str],
    ] = {}

    union: set[
        str
    ] = set()

    for term in (
        BROKER_SENSITIVE_FEATURE_TERMS
    ):

        matches = [
            feature
            for feature
            in features
            if term
            in feature.lower()
        ]

        groups[
            term
        ] = (
            matches
        )

        union.update(
            matches
        )

    return {
        "terms": list(
            BROKER_SENSITIVE_FEATURE_TERMS
        ),
        "by_term": (
            groups
        ),
        "all": sorted(
            union
        ),
        "count": int(
            len(
                union
            )
        ),
        "policy": (
            "THESE_FEATURES_REQUIRE_SPECIAL_"
            "CROSS_BROKER_INTERPRETATION"
        ),
    }


def _training_spread_distribution(
    frame: pd.DataFrame,
) -> dict[str, Any]:

    column = (
        "m5_spread_points"
    )

    if column not in frame.columns:

        return {
            "available": False,
            "column": column,
        }

    values = pd.to_numeric(
        frame[
            column
        ],
        errors="coerce",
    ).to_numpy(
        dtype=np.float64
    )

    values = values[
        np.isfinite(
            values
        )
    ]

    if values.size == 0:

        return {
            "available": False,
            "column": column,
        }

    return {
        "available": True,
        "column": column,
        "rows": int(
            values.size
        ),
        "mean": float(
            np.mean(
                values
            )
        ),
        "std": float(
            np.std(
                values
            )
        ),
        "min": float(
            np.min(
                values
            )
        ),
        "p25": float(
            np.percentile(
                values,
                25,
            )
        ),
        "median": float(
            np.percentile(
                values,
                50,
            )
        ),
        "p75": float(
            np.percentile(
                values,
                75,
            )
        ),
        "p90": float(
            np.percentile(
                values,
                90,
            )
        ),
        "p95": float(
            np.percentile(
                values,
                95,
            )
        ),
        "p99": float(
            np.percentile(
                values,
                99,
            )
        ),
        "max": float(
            np.max(
                values
            )
        ),
        "cross_broker_warning": (
            "RAW_SPREAD_POINTS_ARE_NOT_DIRECTLY_"
            "COMPARABLE_WHEN_POINT_SIZE_OR_"
            "PRICING_CONVENTION_DIFFERS"
        ),
    }


def _gold_usd_semantics(
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

    currency_base = str(
        _attr(
            symbol_info,
            "currency_base",
            "",
        )
    ).upper()

    currency_profit = str(
        _attr(
            symbol_info,
            "currency_profit",
            "",
        )
    ).upper()

    normalized_name = (
        _normalize_token(
            name
        )
    )

    normalized_description = (
        _normalize_token(
            description
        )
    )

    name_xauusd_family = (
        "XAUUSD"
        in normalized_name
    )

    name_gold_family = (
        normalized_name
        .startswith(
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

    exact_gold_with_usd_quote = bool(
        normalized_name
        ==
        "GOLD"
        and
        currency_profit
        ==
        "USD"
        and
        "GOLD"
        in normalized_description
    )

    gold_family_with_xau_usd_contract = bool(
        name_gold_family
        and
        semantic_xau_usd
    )

    accepted = bool(
        (
            name_xauusd_family
            and
            currency_profit
            ==
            "USD"
        )
        or
        semantic_xau_usd
        or
        exact_gold_with_usd_quote
        or
        gold_family_with_xau_usd_contract
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
        "exact_gold_with_usd_quote": (
            exact_gold_with_usd_quote
        ),
    }


def _gold_identity_score(
    symbol_info: Any,
) -> dict[str, Any]:

    semantics = (
        _gold_usd_semantics(
            symbol_info
        )
    )

    if not bool(
        semantics[
            "accepted"
        ]
    ):

        return {
            **semantics,
            "identity_score": 0,
            "reasons": [
                (
                    "REJECTED_NOT_CANONICAL_"
                    "XAUUSD_GOLD_USD"
                )
            ],
        }

    normalized_name = str(
        semantics[
            "normalized_name"
        ]
    )

    score = 0

    reasons: list[
        str
    ] = []

    if normalized_name == "XAUUSD":

        score += 2000

        reasons.append(
            "NORMALIZED_NAME_EXACT_XAUUSD"
        )

    elif "XAUUSD" in normalized_name:

        score += 1800

        reasons.append(
            "NORMALIZED_NAME_XAUUSD_FAMILY"
        )

    elif normalized_name == "GOLD":

        score += 1700

        reasons.append(
            "NORMALIZED_NAME_EXACT_GOLD"
        )

    elif normalized_name.startswith(
        "GOLD"
    ):

        score += 1500

        reasons.append(
            "NORMALIZED_NAME_GOLD_FAMILY"
        )

    if bool(
        semantics[
            "semantic_xau_usd"
        ]
    ):

        score += 1000

        reasons.append(
            "CONTRACT_CURRENCY_XAU_USD"
        )

    if str(
        semantics[
            "currency_profit"
        ]
    ) == "USD":

        score += 300

        reasons.append(
            "PROFIT_CURRENCY_USD"
        )

    description = str(
        semantics[
            "description"
        ]
    ).upper()

    if (
        "GOLD"
        in description
    ):

        score += 100

        reasons.append(
            "DESCRIPTION_CONTAINS_GOLD"
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

        score += 50

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

    return {
        **semantics,
        "identity_score": int(
            score
        ),
        "reasons": (
            reasons
        ),
    }


def _is_gold_candidate(
    symbol_info: Any,
) -> bool:

    semantics = (
        _gold_usd_semantics(
            symbol_info
        )
    )

    return bool(
        semantics[
            "accepted"
        ]
    )


def _tick_document(
    symbol_name: str,
) -> dict[str, Any]:

    tick = (
        mt5.symbol_info_tick(
            symbol_name
        )
    )

    selected_by_runner = False

    if tick is None:

        selected = (
            mt5.symbol_select(
                symbol_name,
                True,
            )
        )

        if selected:

            selected_by_runner = True

            tick = (
                mt5.symbol_info_tick(
                    symbol_name
                )
            )

    if tick is None:

        return {
            "available": False,
            "fresh": False,
            "selected_by_runner": (
                selected_by_runner
            ),
            "mt5_last_error": list(
                mt5.last_error()
            ),
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

    now_epoch = int(
        time.time()
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

        tick_age_seconds = int(
            max(
                0,
                now_epoch
                -
                tick_time,
            )
        )

    fresh = bool(
        tick_age_seconds
        is not None
        and
        tick_age_seconds
        <=
        MAX_LIVE_TICK_AGE_SECONDS
    )

    valid = bool(
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

    return {
        "available": True,
        "valid_bid_ask": (
            valid
        ),
        "fresh": (
            fresh
        ),
        "max_live_tick_age_seconds": (
            MAX_LIVE_TICK_AGE_SECONDS
        ),
        "tick_age_seconds": (
            tick_age_seconds
        ),
        "local_now_epoch": (
            now_epoch
        ),
        "bid": bid,
        "ask": ask,
        "last": (
            _safe_float(
                _attr(
                    tick,
                    "last",
                    None,
                )
            )
        ),
        "volume": (
            _safe_float(
                _attr(
                    tick,
                    "volume",
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
        "selected_by_runner": (
            selected_by_runner
        ),
    }


def _symbol_contract_document(
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
        "select",
    )

    result: dict[
        str,
        Any
    ] = {}

    for field in fields:

        value = (
            _attr(
                symbol_info,
                field,
                None,
            )
        )

        if isinstance(
            value,
            np.generic,
        ):
            value = (
                value.item()
            )

        result[
            field
        ] = (
            value
        )

    return result


def _spread_document(
    symbol_info: Any,
    tick_document: dict[str, Any],
) -> dict[str, Any]:

    if not bool(
        tick_document.get(
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
        }

    bid = float(
        tick_document[
            "bid"
        ]
    )

    ask = float(
        tick_document[
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
        tick_document.get(
            "fresh",
            False,
        )
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
            "STALE_TICK_SPREAD_NOT_VALID_FOR_LIVE_COST_COMPARISON"
        ),
        "bid": bid,
        "ask": ask,
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
        "point": (
            point
        ),
        "tick_size": (
            tick_size
        ),
    }


def _m5_atr14(
    symbol_name: str,
) -> dict[str, Any]:

    rates = (
        mt5.copy_rates_from_pos(
            symbol_name,
            mt5.TIMEFRAME_M5,
            1,
            ATR_HISTORY_BARS,
        )
    )

    if rates is None:

        return {
            "available": False,
            "reason": (
                "MT5_COPY_RATES_RETURNED_NONE"
            ),
            "mt5_last_error": list(
                mt5.last_error()
            ),
        }

    if (
        len(
            rates
        )
        <
        ATR_PERIOD
        +
        1
    ):

        return {
            "available": False,
            "reason": (
                "INSUFFICIENT_M5_HISTORY"
            ),
            "rows": int(
                len(
                    rates
                )
            ),
        }

    high = np.asarray(
        rates[
            "high"
        ],
        dtype=np.float64,
    )

    low = np.asarray(
        rates[
            "low"
        ],
        dtype=np.float64,
    )

    close = np.asarray(
        rates[
            "close"
        ],
        dtype=np.float64,
    )

    if not (
        np.isfinite(
            high
        ).all()
        and
        np.isfinite(
            low
        ).all()
        and
        np.isfinite(
            close
        ).all()
    ):

        return {
            "available": False,
            "reason": (
                "NONFINITE_M5_HISTORY"
            ),
        }

    previous_close = (
        close[
            :-1
        ]
    )

    current_high = (
        high[
            1:
        ]
    )

    current_low = (
        low[
            1:
        ]
    )

    true_range = np.maximum.reduce(
        [
            current_high
            -
            current_low,
            np.abs(
                current_high
                -
                previous_close
            ),
            np.abs(
                current_low
                -
                previous_close
            ),
        ]
    )

    if (
        true_range.size
        <
        ATR_PERIOD
    ):

        return {
            "available": False,
            "reason": (
                "INSUFFICIENT_TRUE_RANGE_ROWS"
            ),
        }

    atr14 = float(
        np.mean(
            true_range[
                -ATR_PERIOD:
            ]
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
                "INVALID_ATR14"
            ),
        }

    return {
        "available": True,
        "timeframe": (
            "M5"
        ),
        "period": (
            ATR_PERIOD
        ),
        "source_completed_bars": int(
            len(
                rates
            )
        ),
        "atr14": (
            atr14
        ),
    }


def _candidate_document(
    symbol_info: Any,
) -> dict[str, Any]:

    identity = (
        _gold_identity_score(
            symbol_info
        )
    )

    symbol_name = str(
        _attr(
            symbol_info,
            "name",
            "",
        )
    )

    tick = (
        _tick_document(
            symbol_name
        )
    )

    spread = (
        _spread_document(
            symbol_info,
            tick,
        )
    )

    spread_bps: (
        float
        |
        None
    ) = None

    if spread.get(
        "usable_for_runtime_costs",
        False,
    ):

        spread_bps = (
            _safe_float(
                spread.get(
                    "spread_bps"
                )
            )
        )

    return {
        "name": (
            identity[
                "name"
            ]
        ),
        "normalized_name": (
            identity[
                "normalized_name"
            ]
        ),
        "identity_score": int(
            identity[
                "identity_score"
            ]
        ),
        "identity_reasons": (
            identity[
                "reasons"
            ]
        ),
        "semantic_xau_usd": bool(
            identity[
                "semantic_xau_usd"
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
        "currency_base": str(
            _attr(
                symbol_info,
                "currency_base",
                "",
            )
        ),
        "currency_profit": str(
            _attr(
                symbol_info,
                "currency_profit",
                "",
            )
        ),
        "description": str(
            _attr(
                symbol_info,
                "description",
                "",
            )
        ),
        "tick": (
            tick
        ),
        "spread": (
            spread
        ),
        "_sort_spread_bps": (
            spread_bps
        ),
    }


def _candidate_sort_key(
    candidate: dict[str, Any],
) -> tuple[
    int,
    int,
    int,
    int,
    int,
    float,
    int,
]:

    tick_valid = int(
        bool(
            candidate[
                "tick"
            ].get(
                "valid_bid_ask",
                False,
            )
        )
    )

    tick_fresh = int(
        bool(
            candidate[
                "tick"
            ].get(
                "fresh",
                False,
            )
        )
    )

    trade_mode = (
        candidate.get(
            "trade_mode"
        )
    )

    trade_enabled = int(
        trade_mode is not None
        and
        int(
            trade_mode
        )
        !=
        0
    )

    identity_score = int(
        candidate[
            "identity_score"
        ]
    )

    visible = int(
        bool(
            candidate.get(
                "visible",
                False,
            )
        )
    )

    spread_bps = (
        candidate.get(
            "_sort_spread_bps"
        )
    )

    if spread_bps is None:

        spread_rank = (
            -1_000_000_000.0
        )

    else:

        spread_rank = (
            -float(
                spread_bps
            )
        )

    name_length_rank = (
        -len(
            str(
                candidate[
                    "name"
                ]
            )
        )
    )

    return (
        tick_valid,
        tick_fresh,
        trade_enabled,
        identity_score,
        visible,
        spread_rank,
        name_length_rank,
    )


def _discover_gold_symbol(
) -> dict[str, Any]:

    symbols = (
        mt5.symbols_get()
    )

    if symbols is None:

        raise RuntimeError(
            (
                "MT5_SYMBOLS_GET_FAILED: "
                f"{mt5.last_error()}"
            )
        )

    candidates: list[
        dict[str, Any]
    ] = []

    rejected_gold_like: list[
        dict[str, Any]
    ] = []

    for symbol_info in symbols:

        name = str(
            _attr(
                symbol_info,
                "name",
                "",
            )
        )

        normalized_name = (
            _normalize_token(
                name
            )
        )

        looks_gold_like = bool(
            "XAU"
            in normalized_name
            or
            "GOLD"
            in normalized_name
        )

        if not (
            _is_gold_candidate(
                symbol_info
            )
        ):

            if looks_gold_like:

                semantics = (
                    _gold_usd_semantics(
                        symbol_info
                    )
                )

                rejected_gold_like.append(
                    {
                        "name": (
                            name
                        ),
                        "normalized_name": (
                            normalized_name
                        ),
                        "description": str(
                            _attr(
                                symbol_info,
                                "description",
                                "",
                            )
                        ),
                        "currency_base": str(
                            _attr(
                                symbol_info,
                                "currency_base",
                                "",
                            )
                        ),
                        "currency_profit": str(
                            _attr(
                                symbol_info,
                                "currency_profit",
                                "",
                            )
                        ),
                        "reason": (
                            "NOT_CANONICAL_XAUUSD_GOLD_USD"
                        ),
                        "semantic_details": (
                            semantics
                        ),
                    }
                )

            continue

        candidates.append(
            _candidate_document(
                symbol_info
            )
        )

    if not candidates:

        raise RuntimeError(
            "NO_CANONICAL_XAUUSD_GOLD_USD_CANDIDATE_FOUND"
        )

    candidates.sort(
        key=(
            _candidate_sort_key
        ),
        reverse=True,
    )

    best = (
        candidates[
            0
        ]
    )

    if not bool(
        best[
            "tick"
        ].get(
            "valid_bid_ask",
            False,
        )
    ):

        raise RuntimeError(
            (
                "GOLD_SYMBOL_FOUND_BUT_"
                "NO_VALID_BID_ASK: "
                f"{best['name']}"
            )
        )

    public_candidates: list[
        dict[str, Any]
    ] = []

    for candidate in (
        candidates[
            :MAX_CANDIDATES_TO_REPORT
        ]
    ):

        public_candidates.append(
            {
                key: value
                for (
                    key,
                    value,
                )
                in candidate.items()
                if key
                !=
                "_sort_spread_bps"
            }
        )

    return {
        "resolved_symbol": str(
            best[
                "name"
            ]
        ),
        "resolved_normalized_name": str(
            best[
                "normalized_name"
            ]
        ),
        "candidate_count": int(
            len(
                candidates
            )
        ),
        "rejected_gold_like_count": int(
            len(
                rejected_gold_like
            )
        ),
        "selection_policy": [
            (
                "CANONICAL_XAU_USD_SEMANTICS_REQUIRED"
            ),
            (
                "VALID_BID_ASK_REQUIRED"
            ),
            (
                "FRESH_TICK_PREFERRED"
            ),
            (
                "TRADE_MODE_ENABLED_PREFERRED"
            ),
            (
                "XAUUSD_OR_GOLD_IDENTITY_SCORE"
            ),
            (
                "VISIBLE_SYMBOL_PREFERRED"
            ),
            (
                "LOWER_FRESH_NORMALIZED_SPREAD_TIEBREAK"
            ),
            (
                "SHORTER_SYMBOL_NAME_FINAL_TIEBREAK"
            ),
        ],
        "suffix_policy": (
            "NO_HARDCODED_SUFFIX_OR_PREFIX_LIST"
        ),
        "canonical_mapping": {
            "canonical_symbol": (
                CANONICAL_SYMBOL
            ),
            "broker_symbol": str(
                best[
                    "name"
                ]
            ),
        },
        "candidates": (
            public_candidates
        ),
        "rejected_gold_like_symbols": (
            rejected_gold_like[
                :MAX_CANDIDATES_TO_REPORT
            ]
        ),
    }


def _runtime_terminal_document(
) -> dict[str, Any]:

    terminal = (
        mt5.terminal_info()
    )

    account = (
        mt5.account_info()
    )

    if terminal is None:

        raise RuntimeError(
            (
                "MT5_TERMINAL_INFO_FAILED: "
                f"{mt5.last_error()}"
            )
        )

    if account is None:

        raise RuntimeError(
            (
                "MT5_ACCOUNT_INFO_FAILED: "
                f"{mt5.last_error()}"
            )
        )

    server = str(
        _attr(
            account,
            "server",
            "",
        )
    )

    return {
        "broker_identity": {
            "source": (
                "MT5_ACCOUNT_SERVER"
            ),
            "server": (
                server
            ),
            "normalized_server": (
                _normalize_token(
                    server
                )
            ),
            "terminal_company_not_used_as_broker_identity": True,
        },
        "terminal": {
            "connected": bool(
                _attr(
                    terminal,
                    "connected",
                    False,
                )
            ),
            "trade_allowed": bool(
                _attr(
                    terminal,
                    "trade_allowed",
                    False,
                )
            ),
            "tradeapi_disabled": bool(
                _attr(
                    terminal,
                    "tradeapi_disabled",
                    False,
                )
            ),
            "company": str(
                _attr(
                    terminal,
                    "company",
                    "",
                )
            ),
            "name": str(
                _attr(
                    terminal,
                    "name",
                    "",
                )
            ),
        },
        "account": {
            "server": (
                server
            ),
            "trade_mode": (
                _safe_int(
                    _attr(
                        account,
                        "trade_mode",
                        None,
                    )
                )
            ),
            "leverage": (
                _safe_int(
                    _attr(
                        account,
                        "leverage",
                        None,
                    )
                )
            ),
            "currency": str(
                _attr(
                    account,
                    "currency",
                    "",
                )
            ),
        },
        "privacy_policy": (
            "ACCOUNT_LOGIN_AND_ACCOUNT_HOLDER_"
            "NAME_INTENTIONALLY_NOT_EMITTED"
        ),
    }


def _broker_matches_frozen(
    *,
    frozen_broker_id: str,
    runtime: dict[str, Any],
) -> bool:

    frozen = (
        _normalize_token(
            frozen_broker_id
        )
    )

    server = str(
        runtime[
            "broker_identity"
        ].get(
            "normalized_server",
            "",
        )
    )

    if (
        not frozen
        or
        not server
    ):
        return False

    return (
        frozen
        in server
    )


def _symbol_matches_frozen(
    *,
    frozen_symbol: str,
    runtime_symbol: str,
) -> bool:

    return (
        _normalize_token(
            frozen_symbol
        )
        ==
        _normalize_token(
            runtime_symbol
        )
    )


def _portability_classification(
    *,
    frozen_identity: dict[str, Any],
    runtime: dict[str, Any],
    resolved_symbol: str,
    spread: dict[str, Any],
) -> dict[str, Any]:

    frozen_broker = str(
        frozen_identity.get(
            "broker_id",
            "",
        )
    )

    frozen_symbol = str(
        frozen_identity.get(
            "broker_symbol",
            "",
        )
    )

    broker_match = (
        _broker_matches_frozen(
            frozen_broker_id=(
                frozen_broker
            ),
            runtime=runtime,
        )
    )

    symbol_match = (
        _symbol_matches_frozen(
            frozen_symbol=(
                frozen_symbol
            ),
            runtime_symbol=(
                resolved_symbol
            ),
        )
    )

    spread_available = bool(
        spread.get(
            "available",
            False,
        )
    )

    runtime_costs_usable = bool(
        spread.get(
            "usable_for_runtime_costs",
            False,
        )
    )

    if (
        broker_match
        and
        symbol_match
    ):

        classification = (
            "SAME_BROKER_SYMBOL_DOMAIN"
        )

    else:

        classification = (
            "BROKER_RUNTIME_ADAPTER_REQUIRED"
        )

    if runtime_costs_usable:

        runtime_cost_status = (
            "FRESH_RUNTIME_COST_SNAPSHOT_AVAILABLE"
        )

    elif spread_available:

        runtime_cost_status = (
            "STALE_TICK_WAIT_FOR_FRESH_MARKET_TICK"
        )

    else:

        runtime_cost_status = (
            "RUNTIME_COST_SNAPSHOT_UNAVAILABLE"
        )

    return {
        "classification": (
            classification
        ),
        "runtime_cost_status": (
            runtime_cost_status
        ),
        "frozen_broker_matches_runtime": (
            broker_match
        ),
        "frozen_symbol_matches_runtime": (
            symbol_match
        ),
        "canonical_symbol_matches": True,
        "spread_snapshot_available": (
            spread_available
        ),
        "spread_snapshot_usable_for_runtime_costs": (
            runtime_costs_usable
        ),
        "model_policy": (
            "RESEARCH_SHADOW_ONLY_UNTIL_"
            "CURRENT_BROKER_DOMAIN_IS_"
            "FORWARD_VALIDATED"
        ),
        "execution_policy": (
            "USE_CURRENT_RUNTIME_CONTRACT_"
            "AND_FRESH_RUNTIME_SPREAD_"
            "NEVER_FROZEN_BROKER_COST_ASSUMPTIONS"
        ),
    }


def run_analysis(
) -> dict[str, Any]:

    trainer = (
        XAUUSDHierarchicalModelV4Trainer()
    )

    snapshot = (
        sweep_module
        ._discover_frozen_training_snapshot(
            trainer=trainer
        )
    )

    trainer._load_and_validate_v3_manifest(
        snapshot=snapshot
    )

    research_frame = (
        sweep_module
        ._load_train_validation_frame(
            trainer=trainer,
            snapshot=snapshot,
        )
    )

    if (
        "dataset_split"
        not in research_frame.columns
    ):

        raise RuntimeError(
            "DATASET_SPLIT_COLUMN_MISSING"
        )

    illegal_splits = {
        str(
            value
        )
        for value
        in research_frame[
            "dataset_split"
        ].unique()
        if str(
            value
        )
        not in {
            "TRAIN",
            "VALIDATION",
        }
    }

    if illegal_splits:

        raise RuntimeError(
            (
                "ILLEGAL_SPLIT_LOADED_IN_"
                "BROKER_PORTABILITY_GATE: "
                f"{sorted(illegal_splits)}"
            )
        )

    features = list(
        snapshot.feature_columns
    )

    frozen_identity = (
        _dataset_identity(
            research_frame
        )
    )

    frozen_spread = (
        _training_spread_distribution(
            research_frame
        )
    )

    sensitive_features = (
        _broker_sensitive_features(
            features
        )
    )

    initialized = (
        mt5.initialize()
    )

    if not initialized:

        raise RuntimeError(
            (
                "MT5_INITIALIZE_FAILED: "
                f"{mt5.last_error()}"
            )
        )

    try:

        runtime = (
            _runtime_terminal_document()
        )

        discovery = (
            _discover_gold_symbol()
        )

        resolved_symbol = str(
            discovery[
                "resolved_symbol"
            ]
        )

        symbol_info = (
            mt5.symbol_info(
                resolved_symbol
            )
        )

        if symbol_info is None:

            raise RuntimeError(
                (
                    "RESOLVED_SYMBOL_INFO_FAILED: "
                    f"{resolved_symbol}: "
                    f"{mt5.last_error()}"
                )
            )

        tick = (
            _tick_document(
                resolved_symbol
            )
        )

        spread = (
            _spread_document(
                symbol_info,
                tick,
            )
        )

        atr = (
            _m5_atr14(
                resolved_symbol
            )
        )

        spread_atr: (
            float
            |
            None
        ) = None

        if (
            spread.get(
                "usable_for_runtime_costs",
                False,
            )
            and
            atr.get(
                "available",
                False,
            )
        ):

            spread_price = (
                _safe_float(
                    spread.get(
                        "spread_price"
                    )
                )
            )

            atr14 = (
                _safe_float(
                    atr.get(
                        "atr14"
                    )
                )
            )

            if (
                spread_price is not None
                and
                atr14 is not None
                and
                atr14 > 0.0
            ):

                spread_atr = (
                    spread_price
                    /
                    atr14
                )

        spread[
            "spread_atr14"
        ] = (
            spread_atr
        )

        spread[
            "normalization_policy"
        ] = {
            "preferred_cross_broker_measures": [
                "spread_price",
                "spread_ticks",
                "spread_bps",
                "spread_atr14",
            ],
            "spread_atr_requires_fresh_tick": True,
            "raw_spread_points_policy": (
                "DIAGNOSTIC_ONLY_ACROSS_"
                "DIFFERENT_BROKER_CONTRACTS"
            ),
            "broker_name_based_spread_assumptions": (
                False
            ),
        }

        contract = (
            _symbol_contract_document(
                symbol_info
            )
        )

        portability = (
            _portability_classification(
                frozen_identity=(
                    frozen_identity
                ),
                runtime=runtime,
                resolved_symbol=(
                    resolved_symbol
                ),
                spread=spread,
            )
        )

        return {
            "valid": True,
            "reason": (
                "OK_XAUUSD_BROKER_"
                "SYMBOL_PORTABILITY_ANALYSIS"
            ),
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "canonical_instrument": {
                "canonical_symbol": (
                    CANONICAL_SYMBOL
                ),
                "asset": (
                    "GOLD"
                ),
                "quote_currency": (
                    "USD"
                ),
            },
            "frozen_research_domain": {
                "dataset_id": (
                    snapshot.dataset_id
                ),
                "dataset_sha256": (
                    snapshot.dataset_sha256
                ),
                "training_manifest_sha256": (
                    snapshot.manifest_sha256
                ),
                "feature_count": int(
                    len(
                        features
                    )
                ),
                "identity": (
                    frozen_identity
                ),
                "spread_points_distribution_train_validation_only": (
                    frozen_spread
                ),
            },
            "runtime_mt5": (
                runtime
            ),
            "gold_symbol_resolution": (
                discovery
            ),
            "resolved_contract": (
                contract
            ),
            "current_tick": (
                tick
            ),
            "current_spread": (
                spread
            ),
            "current_m5_atr": (
                atr
            ),
            "broker_sensitive_features": (
                sensitive_features
            ),
            "portability": (
                portability
            ),
            "scientific_policy": {
                "purpose": (
                    "BROKER_AND_SYMBOL_DOMAIN_"
                    "PORTABILITY_DIAGNOSTIC"
                ),
                "canonical_xau_usd_semantics_required": True,
                "non_usd_xau_crosses_rejected": True,
                "gold_named_non_xauusd_assets_rejected": True,
                "symbol_suffixes_hardcoded": False,
                "symbol_prefixes_hardcoded": False,
                "terminal_symbols_enumerated": True,
                "xauusd_family_auto_detected": True,
                "gold_name_family_auto_detected": True,
                "fresh_tick_required_for_runtime_costs": True,
                "runtime_contract_used": True,
                "broker_identity_source": (
                    "MT5_ACCOUNT_SERVER"
                ),
                "runtime_spread_normalized": True,
                "orders_sent": False,
                "positions_modified": False,
                "risk_engine_modified": False,
                "model_artifacts_written": False,
                "test_evaluated": False,
                "test_selected": False,
                "live_authorized": False,
            },
            "next_decision_contract": {
                "if_broker_runtime_adapter_required": (
                    "IMPLEMENT_CANONICAL_GOLD_SYMBOL_"
                    "RESOLVER_AND_BROKER_COST_ADAPTER_"
                    "IN_DATA_PIPELINE"
                ),
                "if_runtime_cost_status_is_stale": (
                    "RERUN_DURING_ACTIVE_GOLD_MARKET_"
                    "FOR_FRESH_SPREAD_SNAPSHOT"
                ),
                "if_same_broker_symbol_domain": (
                    "KEEP_EXISTING_RESEARCH_DOMAIN_"
                    "BUT_USE_FRESH_RUNTIME_COSTS_"
                    "FOR_EXECUTION"
                ),
                "never_do": [
                    (
                        "NEVER_ASSUME_XAUUSD_SUFFIX_OR_PREFIX"
                    ),
                    (
                        "NEVER_TREAT_GOLD_NAMED_STOCKS_AS_XAUUSD"
                    ),
                    (
                        "NEVER_TREAT_XAUEUR_OR_OTHER_XAU_CROSSES_AS_XAUUSD"
                    ),
                    (
                        "NEVER_HARDCODE_BROKER_SPREAD"
                    ),
                    (
                        "NEVER_USE_STALE_TICK_AS_CURRENT_SPREAD"
                    ),
                    (
                        "NEVER_REUSE_FROZEN_EXNESS_"
                        "EXECUTION_COSTS_ON_OTHER_BROKERS"
                    ),
                ],
            },
            "live_authorized": False,
        }

    finally:

        mt5.shutdown()


def main() -> int:

    try:

        result = (
            run_analysis()
        )

    except Exception as exc:

        try:
            mt5.shutdown()

        except Exception:
            pass

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_BROKER_SYMBOL_"
                        "PORTABILITY_ANALYSIS_FAILED"
                    ),
                    "error_type": (
                        type(
                            exc
                        ).__name__
                    ),
                    "error": str(
                        exc
                    ),
                    "orders_sent": False,
                    "positions_modified": False,
                    "test_evaluated": False,
                    "model_artifacts_written": False,
                    "live_authorized": False,
                },
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
        )

        return 2

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    )

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )