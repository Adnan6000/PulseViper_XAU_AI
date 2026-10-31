"""PulseViper: read-only, completed-candle conditional signal planner."""
from __future__ import annotations

import importlib
import json
from typing import Any, Mapping

import numpy as np
import pandas as pd

VERSION = "PULSEVIPER_SIGNAL_PLANNER_V1"
MTF: Any = importlib.import_module("02_AI.MarketIntelligence.r03_mtf_reasoning")
ORCH_NAME = "04_Testing.production_portability.run_xauusd_r03_v2_orchestrator"


def plan(market: Mapping[str, pd.DataFrame], decision_time_utc: str) -> dict[str, Any]:
    context = MTF.analyze_mtf(market, decision_time_utc)
    decision = MTF.utc_timestamp(decision_time_utc)
    m5 = MTF.closed_bars(market["M5"], "M5", decision)
    if len(m5) < 20:
        raise ValueError("NEED_20_COMPLETED_M5_BARS")

    close = m5["close"].to_numpy(dtype=np.float64)
    high = m5["high"].to_numpy(dtype=np.float64)
    low = m5["low"].to_numpy(dtype=np.float64)
    previous_close = np.r_[close[0], close[:-1]]
    tr = np.maximum.reduce([high - low, np.abs(high - previous_close),
                            np.abs(low - previous_close)])
    atr = float(np.mean(tr[-14:]))
    if not np.isfinite(atr) or atr <= 0:
        raise ValueError("INVALID_ATR")

    # The latest closed M5 candle never sets its own breakout reference.
    resistance = float(np.max(high[-21:-1]))
    support = float(np.min(low[-21:-1]))
    price = float(close[-1])
    buffer = max(0.15 * atr, 0.01)
    stop_buffer = 0.25 * atr
    ctx = context["timeframes"]
    htf = [str(ctx[tf]["structure"]) for tf in ("H1", "H4")]
    buy_aligned = "DOWNWARD" not in htf
    sell_aligned = "UPWARD" not in htf
    buy_confirmed = price > resistance + buffer and buy_aligned
    sell_confirmed = price < support - buffer and sell_aligned

    buy_entry = resistance + buffer
    sell_entry = support - buffer
    buy_stop = support - stop_buffer
    sell_stop = resistance + stop_buffer

    # Avoid impractical setups where opposite side of range creates extreme risk.
    buy_risk = buy_entry - buy_stop
    sell_risk = sell_stop - sell_entry
    buy_valid = buy_risk > 0 and buy_risk <= 5 * atr
    sell_valid = sell_risk > 0 and sell_risk <= 5 * atr

    if buy_confirmed and buy_valid:
        decision_label = "BUY_WATCH"
        reason = "M5 closed above prior resistance; H1/H4 not bearish."
    elif sell_confirmed and sell_valid:
        decision_label = "SELL_WATCH"
        reason = "M5 closed below prior support; H1/H4 not bullish."
    else:
        decision_label = "WAIT"
        reason = "No confirmed M5 breakout with acceptable H1/H4 context and risk."

    def fmt(v: float) -> float:
        return round(v, 3)

    return {
        "version": VERSION,
        "source": "COMPLETED_MT5_CANDLES_ONLY",
        "decision_time_utc": str(decision),
        "last_closed_m5_price": fmt(price),
        "market_context": context["structure_alignment"],
        "h1_structure": htf[0],
        "h4_structure": htf[1],
        "decision": decision_label,
        "reason": reason,
        "buy_setup": {
            "type": "CONDITIONAL_BREAKOUT",
            "trigger_above": fmt(buy_entry),
            "stop_loss": fmt(buy_stop) if buy_valid else None,
            "target_1": fmt(buy_entry + buy_risk) if buy_valid else None,
            "target_2": fmt(buy_entry + 2 * buy_risk) if buy_valid else None,
            "eligible": bool(buy_valid and buy_aligned),
            "condition": "Completed M5 close above trigger, H1/H4 not downward.",
        },
        "sell_setup": {
            "type": "CONDITIONAL_BREAKDOWN",
            "trigger_below": fmt(sell_entry),
            "stop_loss": fmt(sell_stop) if sell_valid else None,
            "target_1": fmt(sell_entry - sell_risk) if sell_valid else None,
            "target_2": fmt(sell_entry - 2 * sell_risk) if sell_valid else None,
            "eligible": bool(sell_valid and sell_aligned),
            "condition": "Completed M5 close below trigger, H1/H4 not upward.",
        },
        "warnings": [
            "Research-only hypothetical levels; no proven predictive edge.",
            "Spread, slippage, fees, broker stop limits and tick freshness not modeled.",
            "Do not treat conditional zones as executable orders.",
        ],
        "trade_authorized": False,
        "edge_established": False,
    }


def speak(report: dict[str, Any]) -> str:
    buy = report["buy_setup"]
    sell = report["sell_setup"]
    return "\n".join([
        "=== PULSEVIPER GOLD SIGNAL REPORT (Roman Urdu) ===",
        f"Decision: {report['decision']} | Gold last closed M5: {report['last_closed_m5_price']}",
        f"H1: {report['h1_structure']} | H4: {report['h4_structure']}",
        f"BUY: {('possible' if buy['eligible'] else 'blocked')} agar M5 {buy['trigger_above']} se upar CLOSE kare.",
        f"  SL: {buy['stop_loss']} | TP1: {buy['target_1']} | TP2: {buy['target_2']}",
        f"SELL: {('possible' if sell['eligible'] else 'blocked')} agar M5 {sell['trigger_below']} se neeche CLOSE kare.",
        f"  SL: {sell['stop_loss']} | TP1: {sell['target_1']} | TP2: {sell['target_2']}",
        f"Wajah: {report['reason']}",
        "Yeh read-only research setup hai, confirmed profitable signal nahi. Koi trade execute nahi hua.",
    ])


def main() -> int:
    try:
        orchestrator: Any = importlib.import_module(ORCH_NAME)
        snap = orchestrator.acquire_genuine_snapshot()
        orchestrator.verify_snapshot_authority(snap)
        if snap.is_synthetic is not False or snap.canonical_instrument != "XAUUSD":
            raise ValueError("GENUINE_XAUUSD_ONLY")
        result = plan(snap.market_data, snap.decision_time_utc)
        result["broker_symbol"] = snap.broker_symbol
        print("SIGNAL_PLANNER_STATUS=PASS_READ_ONLY")
        print(speak(result))
        print("=== MACHINE_READABLE ===")
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        print("SIGNAL_PLANNER_STATUS=BLOCKED")
        print(f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
