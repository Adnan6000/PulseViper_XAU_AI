
"""
PulseViper V10 - Forward Shadow Logger

Research-only forward predictions.

Uses the V7 feature preparation / regression approach.
Trains once at startup, then never refits in this process.
Logs predictions before their future outcomes are known.

Requires running MT5 recorder and auto feature pipeline.

IMPORTANT:
--server-offset-hours is required.
It must be verified against the MT5 server clock.
Do NOT guess the offset to obtain apparent matches.

No orders. No model promotion. No checkpoint changes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import tempfile
import time
import uuid
from bisect import bisect_left
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from sklearn.ensemble import RandomForestRegressor

import pulseviper_decision_intelligence_v7 as v7


OUTPUT = v7.MEMORY / "ShadowLoggerV10"

POLL_SECONDS = 10
MAX_FEATURE_AGE_MS = 90_000
MAX_RECORDER_AGE_MS = 45_000
MAX_FEATURE_QUOTE_GAP_MS = 75_000
OUTCOME_LAG_MS = 3_000
OUTCOME_HORIZON_MS = 60_000


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(
    path: Path,
    value: dict[str, Any],
) -> None:
    line = json.dumps(
        value, sort_keys=True, allow_nan=False
    )

    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        return list(csv.DictReader(handle))


def load_feature_rows(
    feature_names: list[str],
) -> list[dict[str, str]]:
    # Avoid reading a file actively being replaced.
    source = v7.FEATURES

    for _ in range(3):
        before = (
            source.stat().st_size,
            source.stat().st_mtime_ns,
        )
        rows = read_csv(source)
        after = (
            source.stat().st_size,
            source.stat().st_mtime_ns,
        )
        if before == after:
            break
    else:
        raise RuntimeError("Feature file changed during read")

    if not rows:
        return []

    required = (
        set(feature_names)
        | {"symbol", "tick_server_msc"}
    )

    if required - rows[0].keys():
        raise RuntimeError("Feature schema mismatch")

    return rows


def recorder_quotes() -> dict[str, list[v7.Quote]]:
    # Copy to a scratch file because the recorder is live.
    with tempfile.TemporaryDirectory(
        prefix=".pv_rec_",
        dir=OUTPUT,
        ignore_cleanup_errors=True,
    ) as temp:
        scratch = Path(temp) / "recorder.csv"
        source = v7.RECORDER

        for _ in range(3):
            before = (
                source.stat().st_size,
                source.stat().st_mtime_ns,
            )
            shutil.copyfile(source, scratch)
            after = (
                source.stat().st_size,
                source.stat().st_mtime_ns,
            )
            if before == after:
                break
        else:
            raise RuntimeError("Recorder changed during read")

        raw = scratch.read_bytes()
        last = raw.rfind(b"\n")

        if last < 0:
            return {}

        scratch.write_bytes(raw[:last + 1])

        grouped: dict[
            str, dict[int, v7.Quote]
        ] = {}

        for row in read_csv(scratch):
            try:
                symbol = row["symbol"]
                timestamp = int(row["tick_server_msc"])
                bid = float(row["bid"])
                ask = float(row["ask"])

                if (
                    not symbol
                    or timestamp <= 0
                    or not math.isfinite(bid)
                    or not math.isfinite(ask)
                    or bid <= 0
                    or ask < bid
                ):
                    continue

                grouped.setdefault(symbol, {})[
                    timestamp
                ] = v7.Quote(timestamp, bid, ask)

            except (KeyError, ValueError, TypeError):
                continue

        return {
            symbol: sorted(
                records.values(),
                key=lambda q: q.time,
            )
            for symbol, records in grouped.items()
        }


def choose_action(
    predicted_buy: float,
    predicted_sell: float,
    buy_error: float,
    sell_error: float,
    cost: float,
    risk: float,
) -> tuple[str, str]:
    if max(predicted_buy, predicted_sell) <= 0:
        return "WAIT", "NEGATIVE_EXPECTED_PAYOFF"

    buy_after_risk = predicted_buy - risk * buy_error
    sell_after_risk = predicted_sell - risk * sell_error

    if max(buy_after_risk, sell_after_risk) <= 0:
        return "WAIT", "UNCERTAINTY_PENALTY"

    buy_final = buy_after_risk - cost
    sell_final = sell_after_risk - cost

    if max(buy_final, sell_final) <= 0:
        return "WAIT", "EXECUTION_COST"

    if buy_final >= sell_final:
        return "BUY", "POSITIVE_ADJUSTED_BUY"

    return "SELL", "POSITIVE_ADJUSTED_SELL"


def latest_feature(
    rows: list[dict[str, str]],
    names: list[str],
) -> tuple[str, int, NDArray[np.float64]] | None:
    eligible: list[
        tuple[str, int, NDArray[np.float64]]
    ] = []

    for row in rows:
        try:
            vector = np.asarray(
                [float(row[name]) for name in names],
                dtype=np.float64,
            )
            if not bool(np.all(np.isfinite(vector))):
                continue

            eligible.append((
                row["symbol"],
                int(row["tick_server_msc"]),
                vector,
            ))
        except (ValueError, TypeError, KeyError):
            continue

    if not eligible:
        return None

    return max(eligible, key=lambda r: r[1])


def find_quote(
    quotes: list[v7.Quote],
    timestamp: int,
) -> v7.Quote | None:
    times = [q.time for q in quotes]
    index = bisect_left(times, timestamp)

    if index >= len(quotes):
        return None

    quote = quotes[index]

    if quote.time - timestamp > OUTCOME_LAG_MS:
        return None

    return quote


def settle_pending(
    pending: dict[str, dict[str, Any]],
    quotes_by_symbol: dict[str, list[v7.Quote]],
    outcome_file: Path,
) -> None:
    for prediction_id, record in list(pending.items()):
        quotes = quotes_by_symbol.get(
            str(record["symbol"]), []
        )

        if not quotes:
            continue

        target = (
            int(record["feature_timestamp_msc"])
            + OUTCOME_HORIZON_MS
        )

        if quotes[-1].time < target:
            continue

        exit_quote = find_quote(quotes, target)

        if exit_quote is None:
            # Do not invent an exit quote.
            if quotes[-1].time > target + OUTCOME_LAG_MS:
                append_jsonl(outcome_file, {
                    "prediction_id": prediction_id,
                    "recorded_at_utc": utc_now(),
                    "status": "NO_VALID_60S_EXIT_QUOTE",
                    "trading_enabled": False,
                })
                del pending[prediction_id]
            continue

        buy_raw = (
            exit_quote.bid - float(record["entry_ask"])
        )
        sell_raw = (
            float(record["entry_bid"]) - exit_quote.ask
        )
        cost = float(record["extra_cost"])

        action = str(record["action"])

        if action == "BUY":
            realized = buy_raw - cost
        elif action == "SELL":
            realized = sell_raw - cost
        else:
            realized = 0.0

        append_jsonl(outcome_file, {
            "prediction_id": prediction_id,
            "recorded_at_utc": utc_now(),
            "status": "MATURED",
            "exit_timestamp_msc": exit_quote.time,
            "exit_bid": exit_quote.bid,
            "exit_ask": exit_quote.ask,
            "buy_net_price": buy_raw - cost,
            "sell_net_price": sell_raw - cost,
            "action": action,
            "realized_net_price": realized,
            "trading_enabled": False,
        })

        del pending[prediction_id]


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--server-offset-hours",
        type=float,
        required=True,
        help=(
            "Verified difference between recorder's "
            "timestamp clock and UTC, in hours"
        ),
    )
    parser.add_argument(
        "--extra-cost",
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--risk-multiplier",
        type=float,
        default=0.5,
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=POLL_SECONDS,
    )

    args = parser.parse_args()

    if (
        not -12 <= args.server_offset_hours <= 14
        or not math.isfinite(args.extra_cost)
        or args.extra_cost < 0
        or not math.isfinite(args.risk_multiplier)
        or args.risk_multiplier < 0
        or not 5 <= args.poll_seconds <= 300
    ):
        parser.error("Invalid settings")

    OUTPUT.mkdir(parents=True, exist_ok=True)

    checkpoint_id, feature_names = (
        v7.checkpoint_schema()
    )

    # The model is constructed from a frozen
    # historical snapshot, ONCE per run.
    with tempfile.TemporaryDirectory(
        prefix=".pv_train_",
        dir=OUTPUT,
        ignore_cleanup_errors=True,
    ) as temporary:
        folder = Path(temporary)

        feature_path, label_path, recorder_path = (
            v7.stable_copies(folder)
        )

        historical, skipped = v7.prepare(
            feature_path,
            label_path,
            recorder_path,
            feature_names,
        )

        historical.sort(
            key=lambda r: (r.time, r.symbol)
        )

        if len(historical) < 150:
            print("STATUS=INSUFFICIENT_TRAINING_HISTORY")
            return

        # 80% historical train, later 20% calibration.
        # Both are already matured observations.
        boundary = int(len(historical) * 0.80)
        calibration_start = historical[boundary].time

        train = [
            row for row in historical[:boundary]
            if row.time + v7.PURGE_MS
            < calibration_start
        ]

        calibration = historical[boundary:]

        if len(train) < 80 or len(calibration) < 30:
            print("STATUS=INSUFFICIENT_CALIBRATION_HISTORY")
            return

        model = RandomForestRegressor(
            n_estimators=200,
            max_depth=5,
            min_samples_leaf=8,
            random_state=42,
            n_jobs=1,
        )

        model.fit(
            v7.matrix(train), v7.targets(train)
        )

        calibration_predictions = np.asarray(
            model.predict(v7.matrix(calibration)),
            dtype=np.float64,
        )

        errors = np.mean(
            np.abs(
                calibration_predictions
                - v7.targets(calibration)
            ),
            axis=0,
        )

        source_hashes = {
            "features": v7.file_hash(feature_path),
            "labels": v7.file_hash(label_path),
            "recorder": v7.file_hash(recorder_path),
        }

    run_id = (
        datetime.now(timezone.utc).strftime(
            "%Y%m%dT%H%M%SZ"
        )
        + "_"
        + uuid.uuid4().hex[:8]
    )

    run_folder = OUTPUT / run_id
    run_folder.mkdir(parents=True, exist_ok=False)

    prediction_file = run_folder / "predictions.jsonl"
    outcome_file = run_folder / "outcomes.jsonl"

    offset_ms = int(
        args.server_offset_hours * 3_600_000
    )

    # Never backfill the past and claim it was
    # predicted in real time.
    startup_features = load_feature_rows(feature_names)
    startup_latest = latest_feature(
        startup_features, feature_names
    )

    if startup_latest is None:
        print("STATUS=NO_COMPLETE_FEATURES")
        return

    high_watermark = startup_latest[1]

    manifest = {
        "schema": "PV_SHADOW_LOGGER_V10",
        "run_id": run_id,
        "started_at_utc": utc_now(),
        "checkpoint_id": checkpoint_id,
        "source_hashes_at_training": source_hashes,
        "training_samples": len(train),
        "calibration_samples": len(calibration),
        "training_skipped": dict(skipped),
        "feature_dimensions": len(feature_names),
        "calibration_buy_mae": float(errors[0]),
        "calibration_sell_mae": float(errors[1]),
        "server_offset_hours_assumed": (
            args.server_offset_hours
        ),
        "startup_feature_high_watermark_msc": high_watermark,
        "extra_cost": args.extra_cost,
        "risk_multiplier": args.risk_multiplier,
        "model_persisted": False,
        "model_promoted": False,
        "trading_enabled": False,
    }

    (run_folder / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print("PV_SHADOW_LOGGER=V10")
    print(f"CHECKPOINT_ID={checkpoint_id}")
    print(f"RUN_ID={run_id}")
    print(f"TRAIN_SAMPLES={len(train)}")
    print(f"CALIBRATION_SAMPLES={len(calibration)}")
    print(f"CALIBRATION_BUY_MAE={errors[0]:.5f}")
    print(f"CALIBRATION_SELL_MAE={errors[1]:.5f}")
    print(f"STARTUP_HIGH_WATERMARK={high_watermark}")
    print(f"SERVER_OFFSET_HOURS={args.server_offset_hours}")
    print(f"OUTPUT={run_folder}")
    print("BACKFILL_ENABLED=NO")
    print("MODEL_PROMOTED=NO")
    print("TRADING_ENABLED=NO")
    print("STATUS=RUNNING_PRESS_CTRL_C_TO_STOP")

    pending: dict[str, dict[str, Any]] = {}
    last_minute: dict[str, int] = {}
    last_status = ""

    try:
        while True:
            try:
                quotes_by_symbol = recorder_quotes()

                settle_pending(
                    pending,
                    quotes_by_symbol,
                    outcome_file,
                )

                features = load_feature_rows(
                    feature_names
                )

                latest = latest_feature(
                    features, feature_names
                )

                if latest is None:
                    time.sleep(args.poll_seconds)
                    continue

                symbol, timestamp, vector = latest

                if timestamp <= high_watermark:
                    time.sleep(args.poll_seconds)
                    continue

                series = quotes_by_symbol.get(
                    symbol, []
                )

                if not series:
                    time.sleep(args.poll_seconds)
                    continue

                recorder_latest = series[-1].time
                effective_now = (
                    int(time.time() * 1000)
                    + offset_ms
                )

                recorder_age = (
                    effective_now - recorder_latest
                )

                feature_age = (
                    effective_now - timestamp
                )

                feature_quote_gap = (
                    recorder_latest - timestamp
                )

                if not (
                    0 <= recorder_age <= MAX_RECORDER_AGE_MS
                    and 0 <= feature_age <= MAX_FEATURE_AGE_MS
                    and 0 <= feature_quote_gap
                    <= MAX_FEATURE_QUOTE_GAP_MS
                ):
                    status = (
                        f"STALE_OR_MISALIGNED "
                        f"RECORDER_AGE_MS={recorder_age} "
                        f"FEATURE_AGE_MS={feature_age} "
                        f"FEATURE_QUOTE_GAP_MS="
                        f"{feature_quote_gap}"
                    )

                    if status != last_status:
                        print(status, flush=True)
                        last_status = status

                    time.sleep(args.poll_seconds)
                    continue

                # Only a feature timestamp that has
                # an exact observed entry quote is valid.
                quote_by_time = {
                    q.time: q for q in series
                }

                entry = quote_by_time.get(timestamp)

                if entry is None:
                    print(
                        "SKIPPED_NO_EXACT_ENTRY_QUOTE="
                        f"{timestamp}",
                        flush=True,
                    )
                    high_watermark = timestamp
                    time.sleep(args.poll_seconds)
                    continue

                minute_key = timestamp // 60_000

                if last_minute.get(symbol) == minute_key:
                    high_watermark = timestamp
                    time.sleep(args.poll_seconds)
                    continue

                last_minute[symbol] = minute_key

                estimated = np.asarray(
                    model.predict(
                        vector.reshape(1, -1)
                    )[0],
                    dtype=np.float64,
                )

                buy = float(estimated[0])
                sell = float(estimated[1])

                action, reason = choose_action(
                    buy, sell,
                    float(errors[0]),
                    float(errors[1]),
                    args.extra_cost,
                    args.risk_multiplier,
                )

                prediction_id = uuid.uuid4().hex

                event: dict[str, Any] = {
                    "schema": "PV_SHADOW_PREDICTION_V10",
                    "run_id": run_id,
                    "prediction_id": prediction_id,
                    "recorded_at_utc": utc_now(),
                    "symbol": symbol,
                    "feature_timestamp_msc": timestamp,
                    "entry_bid": entry.bid,
                    "entry_ask": entry.ask,
                    "estimated_buy_net_before_extra_cost": buy,
                    "estimated_sell_net_before_extra_cost": sell,
                    "calibration_buy_mae": float(errors[0]),
                    "calibration_sell_mae": float(errors[1]),
                    "action": action,
                    "reason": reason,
                    "extra_cost": args.extra_cost,
                    "risk_multiplier": args.risk_multiplier,
                    "feature_age_ms": feature_age,
                    "recorder_age_ms": recorder_age,
                    "training_checkpoint": checkpoint_id,
                    "outcome_known_at_decision": False,
                    "trading_enabled": False,
                }

                # This is written BEFORE the 60-second
                # result is attached.
                append_jsonl(prediction_file, event)

                pending[prediction_id] = event
                high_watermark = timestamp

                print(
                    f"SHADOW_PREDICTION "
                    f"TIME={timestamp} "
                    f"ACTION={action} "
                    f"REASON={reason} "
                    f"BUY_EST={buy:+.5f} "
                    f"SELL_EST={sell:+.5f}",
                    flush=True,
                )

            except (
                OSError,
                ValueError,
                KeyError,
                RuntimeError,
                csv.Error,
            ) as exc:
                print(
                    f"SHADOW_WARNING={type(exc).__name__}: "
                    f"{exc}",
                    flush=True,
                )

            time.sleep(args.poll_seconds)

    except KeyboardInterrupt:
        print("\nSHADOW_LOGGER_STOPPED=YES")
        print(
            "UNSETTLED_PREDICTIONS="
            f"{len(pending)}"
        )
        print(f"OUTPUT={run_folder}")
        print("TRADING_ENABLED=NO")


if __name__ == "__main__":
    main()
