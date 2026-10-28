
from __future__ import annotations

import importlib
import json
from typing import Any, Mapping

import numpy as np
import pandas as pd

VERSION = "PULSEVIPER_MTF_REASONING_V1"

contract: Any = importlib.import_module(
    "02_AI.Features.portable_feature_contract"
)

TIMEFRAMES = tuple(tf for tf in contract.ALL_TIMEFRAMES if tf != "D1")
MINUTES = dict(contract.TIMEFRAME_MINUTES)
MIN_CLOSED = 12


class MTFError(RuntimeError):
    pass


def utc_timestamp(value: Any) -> pd.Timestamp:
    result = pd.Timestamp(value)
    if not isinstance(result, pd.Timestamp):
        raise MTFError("INVALID_TIMESTAMP")
    if result.tzinfo is None:
        raise MTFError("NAIVE_TIMESTAMP_FORBIDDEN")
    return result.tz_convert("UTC")


def closed_bars(
    frame: pd.DataFrame,
    timeframe: str,
    decision: pd.Timestamp,
) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise MTFError("DATAFRAME_REQUIRED_" + timeframe)

    required = {"time", "open", "high", "low", "close"}
    if not required.issubset(frame.columns):
        raise MTFError("MISSING_OHLC_" + timeframe)

    data = frame.copy()
    data["time"] = pd.to_datetime(
        data["time"], utc=True, errors="raise"
    )

    if bool(data["time"].isna().to_numpy().any()):
        raise MTFError("INVALID_TIME_" + timeframe)

    if bool(data["time"].duplicated().to_numpy().any()):
        raise MTFError("DUPLICATE_TIME_" + timeframe)

    data = data.sort_values("time").reset_index(drop=True)

    for name in ("open", "high", "low", "close"):
        data[name] = pd.to_numeric(
            data[name], errors="raise"
        )

    prices = data[
        ["open", "high", "low", "close"]
    ].to_numpy(dtype=np.float64)

    if not bool(np.isfinite(prices).all()):
        raise MTFError("NONFINITE_PRICE_" + timeframe)

    if not bool((prices > 0).all()):
        raise MTFError("NONPOSITIVE_PRICE_" + timeframe)

    o, h, l, c = (
        prices[:, 0],
        prices[:, 1],
        prices[:, 2],
        prices[:, 3],
    )

    if not bool(
        np.all(h >= np.maximum.reduce([o, l, c]))
        and np.all(l <= np.minimum.reduce([o, h, c]))
    ):
        raise MTFError("INVALID_OHLC_" + timeframe)

    duration = pd.Timedelta(minutes=MINUTES[timeframe])

    # The candle is usable only after its close.
    data = data.loc[
        data["time"] + duration <= decision
    ].copy()

    if len(data) < MIN_CLOSED:
        raise MTFError(
            "INSUFFICIENT_CLOSED_BARS_" + timeframe
        )

    return data.tail(30).reset_index(drop=True)


def timeframe_context(
    frame: pd.DataFrame,
    timeframe: str,
    decision: pd.Timestamp,
) -> dict[str, Any]:
    data = closed_bars(frame, timeframe, decision)

    close = data["close"].to_numpy(dtype=np.float64)
    high = data["high"].to_numpy(dtype=np.float64)
    low = data["low"].to_numpy(dtype=np.float64)

    # Prior structure excludes the last decision candle.
    previous_high = float(np.max(high[:-1]))
    previous_low = float(np.min(low[:-1]))

    previous_close = float(close[-7])
    latest_close = float(close[-1])

    impulse = latest_close - previous_close
    range_scale = float(
        np.median(np.maximum(high - low, 1e-9))
    )

    normalized_impulse = impulse / range_scale

    if normalized_impulse > 0.5:
        structure = "UPWARD"
    elif normalized_impulse < -0.5:
        structure = "DOWNWARD"
    else:
        structure = "SIDEWAYS"

    if latest_close > previous_high:
        position = "ABOVE_PRIOR_RANGE"
    elif latest_close < previous_low:
        position = "BELOW_PRIOR_RANGE"
    else:
        position = "INSIDE_PRIOR_RANGE"

    latest_open = data["time"].iloc[-1]
    latest_close_time = (
        latest_open
        + pd.Timedelta(minutes=MINUTES[timeframe])
    )

    return {
        "timeframe": timeframe,
        "bars_used": len(data),
        "last_bar_open_utc": latest_open.isoformat(),
        "last_bar_close_utc": latest_close_time.isoformat(),
        "last_close": latest_close,
        "structure": structure,
        "normalized_impulse": round(
            normalized_impulse, 5
        ),
        "range_position": position,
        "prior_resistance": previous_high,
        "prior_support": previous_low,
        "median_bar_range": round(range_scale, 6),
    }


def analyze_mtf(
    market: Mapping[str, pd.DataFrame],
    decision_time_utc: Any,
) -> dict[str, Any]:
    decision = utc_timestamp(decision_time_utc)

    if not all(tf in market for tf in TIMEFRAMES):
        raise MTFError("REQUIRED_TIMEFRAME_MISSING")

    contexts = {
        tf: timeframe_context(
            market[tf], tf, decision
        )
        for tf in TIMEFRAMES
    }

    higher = [
        contexts[tf]["structure"]
        for tf in ("H1", "H4")
    ]

    lower = [
        contexts[tf]["structure"]
        for tf in ("M5", "M15")
    ]

    contradictions = []

    if "UPWARD" in higher and "DOWNWARD" in lower:
        contradictions.append(
            "LOWER_TIMEFRAME_BEARISH_AGAINST_BULLISH_HTF"
        )

    if "DOWNWARD" in higher and "UPWARD" in lower:
        contradictions.append(
            "LOWER_TIMEFRAME_BULLISH_AGAINST_BEARISH_HTF"
        )

    # This is descriptive structure alignment,
    # not a trade probability or trading signal.
    upward = sum(
        c["structure"] == "UPWARD"
        for c in contexts.values()
    )
    downward = sum(
        c["structure"] == "DOWNWARD"
        for c in contexts.values()
    )

    if upward >= 4 and downward == 0:
        alignment = "BROAD_UPWARD"
    elif downward >= 4 and upward == 0:
        alignment = "BROAD_DOWNWARD"
    else:
        alignment = "MIXED_OR_UNCERTAIN"

    return {
        "version": VERSION,
        "status": "MTF_RESEARCH_ONLY",
        "decision_time_utc": decision.isoformat(),
        "timeframes": contexts,
        "structure_alignment": alignment,
        "contradictions": contradictions,
        "reasoning": {
            "observed": (
                "Closed-bar structure across six timeframes"
            ),
            "inferred": alignment,
            "unknown": [
                "Actual hidden resting orders",
                "Institutional cash flow",
                "Future price direction",
            ],
        },
        "predictive_edge_established": False,
        "trade_authorized": False,
        "ledger_written": False,
    }


def main() -> int:
    try:
        orchestrator: Any = importlib.import_module(
            "04_Testing.production_portability."
            "run_xauusd_r03_v2_orchestrator"
        )

        snapshot = orchestrator.acquire_genuine_snapshot()
        orchestrator.verify_snapshot_authority(snapshot)

        if snapshot.is_synthetic is not False:
            raise MTFError("SYNTHETIC_DATA_FORBIDDEN")

        if snapshot.canonical_instrument != "XAUUSD":
            raise MTFError("INSTRUMENT_MISMATCH")

        result = analyze_mtf(
            snapshot.market_data,
            snapshot.decision_time_utc,
        )
        result["source_snapshot_id"] = (
            snapshot.source_snapshot_id
        )
        result["broker_symbol"] = snapshot.broker_symbol

    except Exception as exc:
        print("MTF_REASONING_STATUS=BLOCKED")
        print("ERROR_TYPE=" + type(exc).__name__)
        print("ERROR=" + str(exc))
        return 2

    print("MTF_REASONING_STATUS=PASS_READ_ONLY")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
