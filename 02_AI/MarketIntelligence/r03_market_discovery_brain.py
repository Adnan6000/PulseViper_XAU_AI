
from __future__ import annotations

import argparse
import importlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


VERSION = "R03_MARKET_DISCOVERY_BRAIN_V1"
ROOT = Path(__file__).resolve().parents[2]

REQUIRED = (
    "time", "open", "high", "low", "close"
)

MIN_BARS = 30
WINDOW = 60


class DiscoveryError(RuntimeError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise DiscoveryError(reason)


def prepare_m5(frame: pd.DataFrame) -> pd.DataFrame:
    """
    Accept completed M5 bars only.

    Caller must supply an acquisition-authorized,
    completed-bar-only snapshot.
    """
    require(
        isinstance(frame, pd.DataFrame),
        "M5_DATAFRAME_REQUIRED",
    )
    require(
        set(REQUIRED).issubset(frame.columns),
        "M5_REQUIRED_COLUMNS_MISSING",
    )
    require(
        len(frame) >= MIN_BARS,
        "INSUFFICIENT_COMPLETED_M5_BARS",
    )

    data = frame.copy()

    data["time"] = pd.to_datetime(
        data["time"], utc=True, errors="raise"
    )

    require(
        not bool(data["time"].isna().any()),
        "INVALID_M5_TIME",
    )
    require(
        not bool(data["time"].duplicated().any()),
        "DUPLICATE_M5_TIME",
    )

    data = (
        data.sort_values("time")
        .reset_index(drop=True)
        .tail(WINDOW)
        .reset_index(drop=True)
    )

    differences = data["time"].diff().dropna()
    require(
        bool(
            (differences >= pd.Timedelta(minutes=5)).all()
        ),
        "M5_TIME_ORDER_INVALID",
    )
    require(
        bool(
            (
                differences.dt.total_seconds() % 300 == 0
            ).all()
        ),
        "M5_GRID_MISMATCH",
    )

    for name in REQUIRED[1:]:
        data[name] = pd.to_numeric(
            data[name], errors="raise"
        )

    values = data[list(REQUIRED[1:])].to_numpy(
        dtype=float
    )

    require(
        bool(np.isfinite(values).all()),
        "NONFINITE_M5_OHLC",
    )
    require(
        bool((values > 0).all()),
        "NONPOSITIVE_M5_PRICE",
    )

    require(
        bool(
            (
                data["high"]
                >= data[["open", "close", "low"]].max(
                    axis=1
                )
            ).all()
        ),
        "INVALID_M5_HIGH",
    )
    require(
        bool(
            (
                data["low"]
                <= data[["open", "close", "high"]].min(
                    axis=1
                )
            ).all()
        ),
        "INVALID_M5_LOW",
    )

    if "tick_volume" in data.columns:
        volume = np.asarray(
            pd.to_numeric(
                data["tick_volume"].to_numpy(),
                errors="raise",
            ),
            dtype=np.float64,
        )
        require(
            bool(np.isfinite(volume).all())
            and bool((volume >= 0).all()),
            "INVALID_TICK_VOLUME",
        )
        data["tick_volume"] = volume

    return data


def analyze_m5(frame: pd.DataFrame) -> dict[str, Any]:
    data = prepare_m5(frame)

    opens = data["open"].to_numpy(float)
    highs = data["high"].to_numpy(float)
    lows = data["low"].to_numpy(float)
    closes = data["close"].to_numpy(float)

    ranges = np.maximum(highs - lows, 1e-12)
    upper_wicks = highs - np.maximum(opens, closes)
    lower_wicks = np.minimum(opens, closes) - lows

    true_ranges = np.maximum.reduce([
        highs - lows,
        np.abs(highs - np.r_[closes[0], closes[:-1]]),
        np.abs(lows - np.r_[closes[0], closes[:-1]]),
    ])

    atr = float(np.mean(true_ranges[-14:]))
    require(
        math.isfinite(atr) and atr > 0,
        "INVALID_VOLATILITY_SCALE",
    )

    # A zone is a price area, not an exact tick.
    tolerance = max(atr * 0.20, 1e-10)

    # Reference zones are defined from prior bars,
    # never from the final bar under assessment.
    prior_highs = highs[:-1]
    prior_lows = lows[:-1]

    resistance = float(np.max(prior_highs))
    support = float(np.min(prior_lows))

    resistance_touches = (
        (prior_highs >= resistance - tolerance)
        & (
            np.maximum(opens[:-1], closes[:-1])
            < resistance
        )
    )

    support_touches = (
        (prior_lows <= support + tolerance)
        & (
            np.minimum(opens[:-1], closes[:-1])
            > support
        )
    )

    resistance_rejections = int(
        np.sum(
            resistance_touches
            & (
                upper_wicks[:-1]
                >= ranges[:-1] * 0.30
            )
        )
    )

    support_rejections = int(
        np.sum(
            support_touches
            & (
                lower_wicks[:-1]
                >= ranges[:-1] * 0.30
            )
        )
    )

    last_high = float(highs[-1])
    last_low = float(lows[-1])
    last_close = float(closes[-1])

    # No future bars are inspected.
    sweep_above = (
        last_high > resistance + tolerance
        and last_close < resistance
    )
    sweep_below = (
        last_low < support - tolerance
        and last_close > support
    )

    close_break_above = (
        last_close > resistance + tolerance
    )
    close_break_below = (
        last_close < support - tolerance
    )

    returns = np.diff(closes)
    velocity = float(returns[-1] / atr)
    curvature = float(
        (returns[-1] - returns[-2]) / atr
    )

    volume_report: dict[str, Any] = {
        "available": False,
        "source": "not_available",
        "relative_tick_activity": None,
        "cash_flow_measured": False,
        "resting_orders_observed": False,
    }

    if "tick_volume" in data.columns:
        volumes = data["tick_volume"].to_numpy(float)
        baseline = float(
            np.median(volumes[:-1])
        )

        volume_report = {
            "available": True,
            "source": "MT5_tick_volume_proxy",
            "relative_tick_activity": (
                round(float(volumes[-1] / baseline), 4)
                if baseline > 0 else None
            ),
            "cash_flow_measured": False,
            "resting_orders_observed": False,
        }

    evidence: list[str] = []
    contradictions: list[str] = []

    if resistance_rejections >= 2:
        evidence.append(
            "REPEATED_UPPER_ZONE_REJECTION"
        )
    if support_rejections >= 2:
        evidence.append(
            "REPEATED_LOWER_ZONE_REJECTION"
        )
    if sweep_above:
        evidence.append(
            "FAILED_BREAK_ABOVE_PRIOR_RANGE"
        )
    if sweep_below:
        evidence.append(
            "FAILED_BREAK_BELOW_PRIOR_RANGE"
        )
    if curvature < -0.25:
        evidence.append(
            "NEGATIVE_PRICE_ACCELERATION"
        )
    if curvature > 0.25:
        evidence.append(
            "POSITIVE_PRICE_ACCELERATION"
        )

    if close_break_above:
        contradictions.append(
            "CLOSE_CONFIRMED_ABOVE_PRIOR_RESISTANCE"
        )
    if close_break_below:
        contradictions.append(
            "CLOSE_CONFIRMED_BELOW_PRIOR_SUPPORT"
        )

    # Competing hypotheses are suggestions for
    # forward testing, not predictions.
    hypotheses = []

    if resistance_rejections >= 2:
        hypotheses.append({
            "id": "UPPER_ZONE_REJECTION",
            "question": (
                "Does repeated upper-zone rejection "
                "precede below-baseline forward returns?"
            ),
            "supporting_evidence": [
                "REPEATED_UPPER_ZONE_REJECTION"
            ],
            "invalidation": (
                "Subsequent completed close sustains "
                "above the prior resistance zone"
            ),
            "validated": False,
        })

    if support_rejections >= 2:
        hypotheses.append({
            "id": "LOWER_ZONE_DEFENSE",
            "question": (
                "Does repeated lower-zone defense "
                "precede above-baseline forward returns?"
            ),
            "supporting_evidence": [
                "REPEATED_LOWER_ZONE_REJECTION"
            ],
            "invalidation": (
                "Subsequent completed close sustains "
                "below the prior support zone"
            ),
            "validated": False,
        })

    if sweep_above or sweep_below:
        hypotheses.append({
            "id": "FAILED_BREAK_CONTINUATION",
            "question": (
                "Do failed range breaks predict "
                "reversion better than the baseline?"
            ),
            "supporting_evidence": [
                (
                    "FAILED_BREAK_ABOVE_PRIOR_RANGE"
                    if sweep_above else
                    "FAILED_BREAK_BELOW_PRIOR_RANGE"
                )
            ],
            "invalidation": (
                "Price establishes acceptance "
                "outside the swept range"
            ),
            "validated": False,
        })

    return {
        "version": VERSION,
        "market_time_utc": (
            data["time"].iloc[-1].isoformat()
        ),
        "completed_bars_analyzed": len(data),
        "last_close": last_close,
        "atr14_price_units": round(atr, 6),
        "zone_tolerance_price_units": round(
            tolerance, 6
        ),
        "resistance_zone_center": resistance,
        "support_zone_center": support,
        "resistance_rejections": resistance_rejections,
        "support_rejections": support_rejections,
        "last_upper_wick_ratio": round(
            float(upper_wicks[-1] / ranges[-1]), 4
        ),
        "last_lower_wick_ratio": round(
            float(lower_wicks[-1] / ranges[-1]), 4
        ),
        "last_close_location": round(
            float((closes[-1] - lows[-1]) / ranges[-1]),
            4,
        ),
        "normalized_velocity": round(velocity, 4),
        "normalized_curvature": round(curvature, 4),
        "failed_break_above": bool(sweep_above),
        "failed_break_below": bool(sweep_below),
        "volume": volume_report,
        "evidence": evidence,
        "contradictions": contradictions,
        "candidate_hypotheses": hypotheses,
        "hypotheses_validated": 0,
        "hidden_orders_detected": False,
        "predictive_edge_established": False,
        "v2_observation_written": False,
        "outcome_written": False,
        "live_authorized": False,
        "execution_authorized": False,
    }


def run_genuine_mt5() -> dict[str, Any]:
    orchestrator: Any = importlib.import_module(
        "04_Testing.production_portability."
        "run_xauusd_r03_v2_orchestrator"
    )

    snapshot = (
        orchestrator.acquire_genuine_snapshot()
    )
    orchestrator.verify_snapshot_authority(
        snapshot
    )

    require(
        snapshot.is_synthetic is False,
        "SYNTHETIC_SNAPSHOT_FORBIDDEN",
    )
    require(
        snapshot.canonical_instrument == "XAUUSD",
        "INSTRUMENT_MISMATCH",
    )

    market = snapshot.market_data
    require(
        isinstance(market, dict) and "M5" in market,
        "M5_MARKET_DATA_MISSING",
    )

    report = analyze_m5(market["M5"])
    report["source_snapshot_id"] = (
        snapshot.source_snapshot_id
    )
    report["broker_symbol"] = (
        snapshot.broker_symbol
    )
    report["decision_time_utc"] = (
        snapshot.decision_time_utc
    )

    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--once",
        action="store_true",
        help="One genuine MT5 research-only analysis",
    )
    args = parser.parse_args()

    if not args.once:
        print(
            "Use --once for one genuine read-only "
            "market discovery cycle."
        )
        return 0

    try:
        report = run_genuine_mt5()
    except Exception as exc:
        print("MARKET_DISCOVERY_STATUS=BLOCKED")
        print(f"ERROR_TYPE={type(exc).__name__}")
        print(f"ERROR={exc}")
        return 2

    print("MARKET_DISCOVERY_STATUS=PASS_READ_ONLY")
    print(json.dumps(
        report, indent=2, sort_keys=True
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
