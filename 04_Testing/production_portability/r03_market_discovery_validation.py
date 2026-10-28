from __future__ import annotations

import argparse
import importlib
import json
import math
from collections import defaultdict
from typing import Any

import numpy as np
import pandas as pd


VERSION = "R03_DISCOVERY_VALIDATION_V2"
LOOKBACK = 60
HORIZON = 12
MIN_EVENTS_FOR_RESEARCH = 30

brain: Any = importlib.import_module(
    "04_Testing.production_portability."
    "r03_market_discovery_brain"
)

orchestrator: Any = importlib.import_module(
    "04_Testing.production_portability."
    "run_xauusd_r03_v2_orchestrator"
)

HYPOTHESES = {
    "UPPER_ZONE_REJECTION": -1,
    "LOWER_ZONE_DEFENSE": 1,
    "FAILED_BREAK_CONTINUATION": 0,
}


class ValidationError(RuntimeError):
    pass


def prepare_history(frame: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise ValidationError("M5_DATAFRAME_REQUIRED")

    required = {"time", "open", "high", "low", "close"}
    if not required.issubset(frame.columns):
        raise ValidationError("M5_COLUMNS_MISSING")

    if len(frame) < LOOKBACK + HORIZON:
        raise ValidationError("INSUFFICIENT_M5_HISTORY")

    data = frame.copy()
    data["time"] = pd.to_datetime(
        data["time"], utc=True, errors="raise"
    )

    if bool(data["time"].isna().to_numpy().any()):
        raise ValidationError("INVALID_TIME")

    if bool(data["time"].duplicated().to_numpy().any()):
        raise ValidationError("DUPLICATE_TIME")

    data = data.sort_values("time").reset_index(drop=True)

    for name in ("open", "high", "low", "close"):
        data[name] = pd.to_numeric(
            data[name], errors="raise"
        )

    values = data[
        ["open", "high", "low", "close"]
    ].to_numpy(dtype=np.float64)

    if not np.isfinite(values).all():
        raise ValidationError("NONFINITE_PRICE")

    if not (values > 0).all():
        raise ValidationError("NONPOSITIVE_PRICE")

    opens = values[:, 0]
    highs = values[:, 1]
    lows = values[:, 2]
    closes = values[:, 3]

    valid_highs = np.all(
        highs >= np.maximum.reduce(
            [opens, closes, lows]
        )
    )
    valid_lows = np.all(
        lows <= np.minimum.reduce(
            [opens, closes, highs]
        )
    )

    if not (bool(valid_highs) and bool(valid_lows)):
        raise ValidationError("INVALID_OHLC")

    if "tick_volume" in data.columns:
        volume = np.asarray(
            pd.to_numeric(
                data["tick_volume"].to_numpy(),
                errors="raise",
            ),
            dtype=np.float64,
        )
        if (
            not np.isfinite(volume).all()
            or (volume < 0).any()
        ):
            raise ValidationError("INVALID_TICK_VOLUME")
        data["tick_volume"] = volume

    return data


def consecutive_m5(data: pd.DataFrame) -> bool:
    deltas = data["time"].diff().dropna()
    return bool(
        (deltas == pd.Timedelta(minutes=5)).all()
    )


def statistics(values: list[float]) -> dict[str, Any]:
    if not values:
        return {
            "count": 0,
            "mean_atr_normalized_return": None,
            "positive_return_share": None,
        }

    array = np.asarray(values, dtype=np.float64)

    return {
        "count": len(values),
        "mean_atr_normalized_return": round(
            float(np.mean(array)), 6
        ),
        "positive_return_share": round(
            float(np.mean(array > 0)), 6
        ),
    }


def validate_history(
    frame: pd.DataFrame,
) -> dict[str, Any]:
    data = prepare_history(frame)

    # A hypothesis is evaluated at the close of
    # decision bar i. Future bars i+1 ... i+12
    # are unavailable to the hypothesis detector.
    groups: dict[str, list[float]] = defaultdict(list)
    baseline_up: list[float] = []
    baseline_down: list[float] = []
    examples: dict[str, list[dict[str, Any]]] = defaultdict(
        list
    )

    skipped_gaps = 0
    evaluated_decisions = 0

    for i in range(LOOKBACK - 1, len(data) - HORIZON):
        past = data.iloc[
            i - LOOKBACK + 1 : i + 1
        ].copy()

        future = data.iloc[
            i + 1 : i + HORIZON + 1
        ].copy()

        combined = data.iloc[
            i - LOOKBACK + 1 : i + HORIZON + 1
        ]

        # No horizon is scored when the 60-bar
        # lookback or 12-bar future contains a gap.
        if not consecutive_m5(combined):
            skipped_gaps += 1
            continue

        discovery = brain.analyze_m5(past)

        start_close = float(
            past["close"].iloc[-1]
        )
        end_close = float(
            future["close"].iloc[-1]
        )
        atr = float(
            discovery["atr14_price_units"]
        )

        if not math.isfinite(atr) or atr <= 0:
            raise ValidationError("INVALID_ATR")

        forward = (end_close - start_close) / atr

        baseline_up.append(forward)
        baseline_down.append(-forward)
        evaluated_decisions += 1

        decision_time = (
            past["time"].iloc[-1]
            + pd.Timedelta(minutes=5)
        ).isoformat()

        for hypothesis in discovery[
            "candidate_hypotheses"
        ]:
            hypothesis_id = hypothesis["id"]

            if hypothesis_id not in HYPOTHESES:
                continue

            direction = HYPOTHESES[hypothesis_id]

            # Failed-break hypothesis is treated
            # directionally: an upper sweep implies
            # a bearish test, a lower sweep bullish.
            if direction == 0:
                if discovery["failed_break_above"]:
                    direction = -1
                elif discovery["failed_break_below"]:
                    direction = 1
                else:
                    continue

            signed_return = direction * forward
            groups[hypothesis_id].append(
                signed_return
            )

            if len(examples[hypothesis_id]) < 3:
                examples[hypothesis_id].append({
                    "decision_time_utc": decision_time,
                    "direction": (
                        "LONG" if direction == 1
                        else "SHORT"
                    ),
                    "forward_12_bar_atr_return": round(
                        signed_return, 6
                    ),
                })

    baseline = {
        "long": statistics(baseline_up),
        "short": statistics(baseline_down),
    }

    results = {}

    for hypothesis_id, direction in HYPOTHESES.items():
        sample = groups[hypothesis_id]
        measured = statistics(sample)

        if direction == 1:
            reference = baseline["long"]
        elif direction == -1:
            reference = baseline["short"]
        else:
            reference = None

        results[hypothesis_id] = {
            **measured,
            "baseline": reference,
            "sample_count_sufficient_for_research": (
                len(sample) >= MIN_EVENTS_FOR_RESEARCH
            ),
            "example_decisions": examples[
                hypothesis_id
            ],
            "independently_validated": False,
            "predictive_edge_established": False,
        }

    return {
        "version": VERSION,
        "status": "EXPLORATORY_READ_ONLY",
        "history_bars": len(data),
        "lookback_bars": LOOKBACK,
        "future_horizon_bars": HORIZON,
        "evaluated_decisions": evaluated_decisions,
        "skipped_due_to_m5_gaps": skipped_gaps,
        "baseline": baseline,
        "hypotheses": results,
        "warnings": [
            "Historical exploratory analysis only",
            "Overlapping future windows are not independent",
            "Same-sample exploration can overfit",
            "No multiple-testing adjustment",
            "No spread, slippage or transaction-cost model",
            "Forward prospective validation remains required",
            "Tick volume does not reveal hidden orders",
        ],
        "v2_prospective_outcomes_written": False,
        "model_retraining_authorized": False,
        "execution_authorized": False,
    }


def run_genuine_mt5() -> dict[str, Any]:
    snapshot = orchestrator.acquire_genuine_snapshot()
    orchestrator.verify_snapshot_authority(snapshot)

    if snapshot.is_synthetic is not False:
        raise ValidationError("SYNTHETIC_DATA_FORBIDDEN")

    if snapshot.canonical_instrument != "XAUUSD":
        raise ValidationError("WRONG_INSTRUMENT")

    market = snapshot.market_data
    if not isinstance(market, dict) or "M5" not in market:
        raise ValidationError("M5_MARKET_DATA_MISSING")

    result = validate_history(market["M5"])
    result["source_snapshot_id"] = (
        snapshot.source_snapshot_id
    )
    result["broker_symbol"] = (
        snapshot.broker_symbol
    )
    result["decision_time_utc"] = (
        snapshot.decision_time_utc
    )

    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    if not args.once:
        print("Use --once for genuine read-only validation.")
        return 0

    try:
        result = run_genuine_mt5()
    except Exception as exc:
        print("DISCOVERY_V2_STATUS=BLOCKED")
        print("ERROR_TYPE=" + type(exc).__name__)
        print("ERROR=" + str(exc))
        return 2

    print("DISCOVERY_V2_STATUS=PASS_READ_ONLY")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
