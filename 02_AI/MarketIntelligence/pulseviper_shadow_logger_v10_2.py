
"""
PulseViper Quantum Brain
Forward Shadow Logger V10.2

COMPLETE SOURCE FILE

Features:
- Fast Live Bridge V10.1 feature input
- One frozen regression model per logger process
- Strict forward-only prediction recording
- Entry quote must be AFTER prediction
- 60-second spread-inclusive outcome
- JSONL persistent event records
- Recovery of unfinished V10.2 predictions
- UTC/server offset freshness validation
- No trades, no promotion, no champion changes

Requires:
    numpy
    scikit-learn
    pulseviper_decision_intelligence_v7.py

Research only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import tempfile
import time
import uuid

from bisect import bisect_left
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from sklearn.ensemble import RandomForestRegressor

import pulseviper_decision_intelligence_v7 as v7


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DATA = ROOT / "01_Data" / "VolumeMemory"

MEMORY = DATA / "StableMemoryV2"

OUTPUT = MEMORY / "ShadowLoggerV10_2"

LIVE_FEATURES = (
    DATA / "live_pattern_features_v1.csv"
)

RECORDER = v7.RECORDER


# ============================================================
# SETTINGS
# ============================================================

MAX_FEATURE_AGE_MS = 90_000
MAX_RECORDER_AGE_MS = 45_000

# Reject a feature too far behind the recorder.
MAX_FEATURE_QUOTE_GAP_MS = 90_000

# Entry must follow prediction by at least 2 seconds.
ENTRY_SAFETY_DELAY_MS = 2_000

ENTRY_TIMEOUT_MS = 180_000

HORIZON_MS = 60_000
MAX_EXIT_LAG_MS = 3_000

POLL_DEFAULT_SECONDS = 10


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass(frozen=True)
class Quote:
    symbol: str
    timestamp: int
    bid: float
    ask: float


@dataclass
class Pending:
    prediction_id: str
    directory: Path
    symbol: str
    prediction_server_msc: int
    action: str
    extra_cost: float
    entry_timestamp: int | None = None
    entry_bid: float | None = None
    entry_ask: float | None = None


# ============================================================
# GENERAL HELPERS
# ============================================================

def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def append_jsonl(
    path: Path,
    record: dict[str, Any],
) -> None:
    payload = json.dumps(
        record,
        sort_keys=True,
        allow_nan=False,
    )

    with path.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(payload + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []

    result: list[dict[str, Any]] = []

    with path.open(
        "r", encoding="utf-8"
    ) as handle:
        for line in handle:
            if not line.strip():
                continue

            try:
                value = json.loads(line)

                if isinstance(value, dict):
                    result.append(value)

            except json.JSONDecodeError:
                # Ignore a torn final record. Completed
                # records remain recoverable.
                continue

    return result


def read_csv_stable(
    path: Path,
) -> list[dict[str, str]]:
    for _ in range(3):
        before = path.stat()

        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            rows = list(csv.DictReader(handle))

        after = path.stat()

        if (
            before.st_size == after.st_size
            and before.st_mtime_ns == after.st_mtime_ns
        ):
            return rows

    raise RuntimeError(
        f"File changed during read: {path}"
    )


def server_now_ms(
    offset_hours: float,
) -> int:
    return int(
        time.time() * 1000
        + offset_hours * 3_600_000
    )


# ============================================================
# RECORDER
# ============================================================

def read_quotes() -> dict[str, list[Quote]]:
    """
    Reads complete recorder rows.

    Duplicate timestamps are deduplicated by symbol.
    """
    grouped: dict[
        str, dict[int, Quote]
    ] = {}

    for row in read_csv_stable(RECORDER):
        try:
            symbol = row["symbol"]
            timestamp = int(
                row["tick_server_msc"]
            )

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

            quote = Quote(
                symbol=symbol,
                timestamp=timestamp,
                bid=bid,
                ask=ask,
            )

            grouped.setdefault(
                symbol, {}
            )[timestamp] = quote

        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            continue

    return {
        symbol: sorted(
            records.values(),
            key=lambda q: q.timestamp,
        )
        for symbol, records in grouped.items()
    }


def first_quote_after(
    quotes: list[Quote],
    timestamp: int,
) -> Quote | None:
    times = [
        q.timestamp for q in quotes
    ]

    index = bisect_left(
        times, timestamp
    )

    if index >= len(quotes):
        return None

    return quotes[index]


# ============================================================
# LIVE FEATURE INPUT
# ============================================================

def latest_live_feature(
    feature_names: list[str],
) -> tuple[str, int, NDArray[np.float64]] | None:
    if not LIVE_FEATURES.is_file():
        return None

    rows = read_csv_stable(
        LIVE_FEATURES
    )

    if not rows:
        return None

    required = (
        set(feature_names)
        | {"symbol", "tick_server_msc"}
    )

    if required - rows[0].keys():
        raise RuntimeError(
            "Live feature schema mismatch"
        )

    latest: tuple[
        str, int, NDArray[np.float64]
    ] | None = None

    for row in rows:
        try:
            symbol = row["symbol"]
            timestamp = int(
                row["tick_server_msc"]
            )

            vector = np.asarray(
                [
                    float(row[name])
                    for name in feature_names
                ],
                dtype=np.float64,
            )

            if not bool(
                np.all(np.isfinite(vector))
            ):
                continue

            if (
                latest is None
                or timestamp > latest[1]
            ):
                latest = (
                    symbol,
                    timestamp,
                    vector,
                )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            continue

    return latest


# ============================================================
# DECISION LOGIC
# ============================================================

def choose_action(
    estimated_buy: float,
    estimated_sell: float,
    buy_mae: float,
    sell_mae: float,
    cost: float,
    risk: float,
) -> tuple[str, str]:
    if max(
        estimated_buy,
        estimated_sell,
    ) <= 0:
        return (
            "WAIT",
            "NEGATIVE_EXPECTED_PAYOFF",
        )

    buy_risk = (
        estimated_buy - risk * buy_mae
    )
    sell_risk = (
        estimated_sell - risk * sell_mae
    )

    if max(buy_risk, sell_risk) <= 0:
        return (
            "WAIT",
            "UNCERTAINTY_PENALTY",
        )

    buy_final = buy_risk - cost
    sell_final = sell_risk - cost

    if max(buy_final, sell_final) <= 0:
        return (
            "WAIT",
            "EXECUTION_COST",
        )

    if buy_final >= sell_final:
        return (
            "BUY",
            "POSITIVE_ADJUSTED_BUY",
        )

    return (
        "SELL",
        "POSITIVE_ADJUSTED_SELL",
    )


# ============================================================
# PENDING RECOVERY
# ============================================================

def recover_pending() -> dict[str, Pending]:
    """
    Recover unfinished V10.2 records across runs.

    Predictions and entries are read from disk.
    Already settled predictions are excluded.
    """
    pending: dict[str, Pending] = {}

    if not OUTPUT.exists():
        return pending

    for directory in OUTPUT.iterdir():
        if not directory.is_dir():
            continue

        manifest_path = (
            directory / "manifest.json"
        )

        if not manifest_path.is_file():
            continue

        try:
            manifest = json.loads(
                manifest_path.read_text(
                    encoding="utf-8"
                )
            )

            if (
                manifest.get("schema")
                != "PV_SHADOW_LOGGER_V10_2"
            ):
                continue

        except (
            OSError,
            ValueError,
        ):
            continue

        predictions = read_jsonl(
            directory / "predictions.jsonl"
        )

        entries = read_jsonl(
            directory / "entries.jsonl"
        )

        outcomes = read_jsonl(
            directory / "outcomes.jsonl"
        )

        completed = {
            str(row["prediction_id"])
            for row in outcomes
            if "prediction_id" in row
        }

        entry_map = {
            str(row["prediction_id"]): row
            for row in entries
            if "prediction_id" in row
        }

        for row in predictions:
            try:
                identity = str(
                    row["prediction_id"]
                )

                if identity in completed:
                    continue

                item = Pending(
                    prediction_id=identity,
                    directory=directory,
                    symbol=str(row["symbol"]),
                    prediction_server_msc=int(
                        row["prediction_server_msc"]
                    ),
                    action=str(row["action"]),
                    extra_cost=float(
                        row["extra_cost"]
                    ),
                )

                entry = entry_map.get(
                    identity
                )

                if entry is not None:
                    item.entry_timestamp = int(
                        entry["entry_timestamp_msc"]
                    )
                    item.entry_bid = float(
                        entry["entry_bid"]
                    )
                    item.entry_ask = float(
                        entry["entry_ask"]
                    )

                pending[identity] = item

            except (
                KeyError,
                ValueError,
                TypeError,
            ):
                continue

    return pending


# ============================================================
# ENTRY AND OUTCOME SETTLEMENT
# ============================================================

def process_pending(
    pending: dict[str, Pending],
    quotes_by_symbol: dict[str, list[Quote]],
    current_server_ms: int,
) -> None:
    for identity, item in list(
        pending.items()
    ):
        quotes = quotes_by_symbol.get(
            item.symbol, []
        )

        if not quotes:
            continue

        outcome_path = (
            item.directory / "outcomes.jsonl"
        )

        entry_path = (
            item.directory / "entries.jsonl"
        )

        # ----------------------------------------
        # Stage A: Forward hypothetical entry
        # ----------------------------------------

        if item.entry_timestamp is None:
            earliest = (
                item.prediction_server_msc
                + ENTRY_SAFETY_DELAY_MS
            )

            candidate = first_quote_after(
                quotes,
                earliest,
            )

            if (
                candidate is not None
                and candidate.timestamp
                <= item.prediction_server_msc
                + ENTRY_TIMEOUT_MS
            ):
                append_jsonl(
                    entry_path,
                    {
                        "prediction_id": identity,
                        "recorded_at_utc": utc_now(),
                        "entry_timestamp_msc":
                            candidate.timestamp,
                        "entry_bid": candidate.bid,
                        "entry_ask": candidate.ask,
                        "status": "ENTRY_OBSERVED",
                    },
                )

                item.entry_timestamp = (
                    candidate.timestamp
                )
                item.entry_bid = (
                    candidate.bid
                )
                item.entry_ask = (
                    candidate.ask
                )

                print(
                    f"SHADOW_ENTRY "
                    f"ID={identity[:8]} "
                    f"TIME={candidate.timestamp} "
                    f"BID={candidate.bid:.5f} "
                    f"ASK={candidate.ask:.5f}",
                    flush=True,
                )

            elif (
                current_server_ms
                > item.prediction_server_msc
                + ENTRY_TIMEOUT_MS
            ):
                append_jsonl(
                    outcome_path,
                    {
                        "prediction_id": identity,
                        "status": "ENTRY_TIMEOUT",
                        "recorded_at_utc": utc_now(),
                        "trading_enabled": False,
                    },
                )
                del pending[identity]

            continue

        # ----------------------------------------
        # Stage B: Future 60-second outcome
        # ----------------------------------------

        target = (
            item.entry_timestamp
            + HORIZON_MS
        )

        exit_quote = first_quote_after(
            quotes, target
        )

        if exit_quote is None:
            continue

        if (
            exit_quote.timestamp
            > target + MAX_EXIT_LAG_MS
        ):
            append_jsonl(
                outcome_path,
                {
                    "prediction_id": identity,
                    "status": "NO_VALID_EXIT_QUOTE",
                    "recorded_at_utc": utc_now(),
                    "trading_enabled": False,
                },
            )

            del pending[identity]
            continue

        assert item.entry_bid is not None
        assert item.entry_ask is not None

        buy_net = (
            exit_quote.bid
            - item.entry_ask
            - item.extra_cost
        )

        sell_net = (
            item.entry_bid
            - exit_quote.ask
            - item.extra_cost
        )

        if item.action == "BUY":
            realized = buy_net
        elif item.action == "SELL":
            realized = sell_net
        else:
            realized = 0.0

        append_jsonl(
            outcome_path,
            {
                "prediction_id": identity,
                "recorded_at_utc": utc_now(),
                "status": "MATURED",
                "action": item.action,
                "entry_timestamp_msc":
                    item.entry_timestamp,
                "exit_timestamp_msc":
                    exit_quote.timestamp,
                "exit_bid": exit_quote.bid,
                "exit_ask": exit_quote.ask,
                "buy_net_price": buy_net,
                "sell_net_price": sell_net,
                "realized_net_price": realized,
                "trading_enabled": False,
            },
        )

        print(
            f"SHADOW_OUTCOME "
            f"ID={identity[:8]} "
            f"ACTION={item.action} "
            f"NET={realized:+.5f}",
            flush=True,
        )

        del pending[identity]


# ============================================================
# HISTORICAL MODEL TRAINING
# ============================================================

def train_frozen_model(
    names: list[str],
) -> tuple[
    RandomForestRegressor,
    NDArray[np.float64],
    dict[str, Any],
]:
    """
    Train once from matured historical outcomes.

    The model is not refitted during forward logging.
    """
    with tempfile.TemporaryDirectory(
        prefix=".pv_v10_2_train_",
        dir=OUTPUT,
        ignore_cleanup_errors=True,
    ) as temporary:
        folder = Path(temporary)

        features, labels, recorder = (
            v7.stable_copies(folder)
        )

        samples, skipped = v7.prepare(
            features,
            labels,
            recorder,
            names,
        )

        samples.sort(
            key=lambda row: (
                row.time,
                row.symbol,
            )
        )

        if len(samples) < 150:
            raise RuntimeError(
                "Insufficient historical training data"
            )

        boundary = int(
            len(samples) * 0.80
        )

        calibration_start = (
            samples[boundary].time
        )

        train = [
            row
            for row in samples[:boundary]
            if (
                row.time + v7.PURGE_MS
                < calibration_start
            )
        ]

        calibration = (
            samples[boundary:]
        )

        if (
            len(train) < 80
            or len(calibration) < 30
        ):
            raise RuntimeError(
                "Insufficient training/calibration split"
            )

        model = RandomForestRegressor(
            n_estimators=200,
            max_depth=5,
            min_samples_leaf=8,
            random_state=42,
            n_jobs=1,
        )

        model.fit(
            v7.matrix(train),
            v7.targets(train),
        )

        predictions = np.asarray(
            model.predict(
                v7.matrix(calibration)
            ),
            dtype=np.float64,
        )

        errors = np.asarray(
            np.mean(
                np.abs(
                    predictions
                    - v7.targets(calibration)
                ),
                axis=0,
            ),
            dtype=np.float64,
        )

        metadata: dict[str, Any] = {
            "train_samples": len(train),
            "calibration_samples":
                len(calibration),
            "training_skipped": dict(skipped),
            "source_hashes": {
                "features": v7.file_hash(features),
                "labels": v7.file_hash(labels),
                "recorder": v7.file_hash(recorder),
            },
        }

        return model, errors, metadata


# ============================================================
# MAIN LOGGER
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--server-offset-hours",
        type=float,
        required=True,
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
        default=POLL_DEFAULT_SECONDS,
    )

    args = parser.parse_args()

    if (
        not math.isfinite(
            args.server_offset_hours
        )
        or not -12 <= args.server_offset_hours <= 14
        or not math.isfinite(
            args.extra_cost
        )
        or args.extra_cost < 0
        or not math.isfinite(
            args.risk_multiplier
        )
        or args.risk_multiplier < 0
        or not 5 <= args.poll_seconds <= 300
    ):
        parser.error("Invalid settings")

    OUTPUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    checkpoint_id, names = (
        v7.checkpoint_schema()
    )

    # Recover unfinished events from prior V10.2 runs.
    pending = recover_pending()

    print("PV_SHADOW_LOGGER=V10.2")
    print(
        f"RECOVERED_PENDING={len(pending)}"
    )

    # Fixed training at startup.
    model, errors, training_info = (
        train_frozen_model(names)
    )

    latest = latest_live_feature(
        names
    )

    if latest is None:
        print("STATUS=NO_LIVE_FEATURES")
        return

    # High watermark prevents historical backfill.
    high_watermark = latest[1]

    run_id = (
        datetime.now(
            timezone.utc
        ).strftime("%Y%m%dT%H%M%SZ")
        + "_"
        + uuid.uuid4().hex[:8]
    )

    directory = OUTPUT / run_id

    directory.mkdir(
        parents=True,
        exist_ok=False,
    )

    manifest: dict[str, Any] = {
        "schema": "PV_SHADOW_LOGGER_V10_2",
        "run_id": run_id,
        "created_at_utc": utc_now(),
        "checkpoint_id": checkpoint_id,
        "feature_dimensions": len(names),
        "startup_high_watermark_msc":
            high_watermark,
        "server_offset_hours":
            args.server_offset_hours,
        "extra_cost": args.extra_cost,
        "risk_multiplier":
            args.risk_multiplier,
        "calibration_buy_mae":
            float(errors[0]),
        "calibration_sell_mae":
            float(errors[1]),
        "training": training_info,
        "model_refitted_during_run": False,
        "model_promoted": False,
        "trading_enabled": False,
    }

    (directory / "manifest.json").write_text(
        json.dumps(
            manifest,
            indent=2,
        ),
        encoding="utf-8",
    )

    prediction_path = (
        directory / "predictions.jsonl"
    )

    offset = (
        args.server_offset_hours
    )

    last_minute: dict[str, int] = {}
    last_warning = ""

    print(f"CHECKPOINT_ID={checkpoint_id}")
    print(
        f"TRAIN_SAMPLES="
        f"{training_info['train_samples']}"
    )
    print(
        f"CALIBRATION_SAMPLES="
        f"{training_info['calibration_samples']}"
    )
    print(
        f"CALIBRATION_BUY_MAE={errors[0]:.5f}"
    )
    print(
        f"CALIBRATION_SELL_MAE={errors[1]:.5f}"
    )
    print(f"RUN_ID={run_id}")
    print(f"OUTPUT={directory}")
    print("BACKFILL_ENABLED=NO")
    print("TRADING_ENABLED=NO")
    print("STATUS=RUNNING_PRESS_CTRL_C_TO_STOP")

    try:
        while True:
            try:
                current_server = (
                    server_now_ms(offset)
                )

                quotes_by_symbol = (
                    read_quotes()
                )

                # Settle old events first.
                process_pending(
                    pending,
                    quotes_by_symbol,
                    current_server,
                )

                latest = latest_live_feature(
                    names
                )

                if latest is None:
                    time.sleep(
                        args.poll_seconds
                    )
                    continue

                symbol, timestamp, vector = (
                    latest
                )

                if timestamp <= high_watermark:
                    time.sleep(
                        args.poll_seconds
                    )
                    continue

                series = quotes_by_symbol.get(
                    symbol, []
                )

                if not series:
                    time.sleep(
                        args.poll_seconds
                    )
                    continue

                recorder_latest = (
                    series[-1].timestamp
                )

                feature_age = (
                    current_server - timestamp
                )

                recorder_age = (
                    current_server - recorder_latest
                )

                feature_gap = (
                    recorder_latest - timestamp
                )

                # Allow up to 3s apparent clock jitter,
                # but never allow old/stale inputs.
                valid = (
                    -3000 <= recorder_age
                    <= MAX_RECORDER_AGE_MS
                    and -3000 <= feature_age
                    <= MAX_FEATURE_AGE_MS
                    and 0 <= feature_gap
                    <= MAX_FEATURE_QUOTE_GAP_MS
                )

                if not valid:
                    status = (
                        "STALE_OR_MISALIGNED "
                        f"RECORDER_AGE_MS={recorder_age} "
                        f"FEATURE_AGE_MS={feature_age} "
                        f"FEATURE_GAP_MS={feature_gap}"
                    )

                    if status != last_warning:
                        print(
                            status,
                            flush=True,
                        )
                        last_warning = status

                    time.sleep(
                        args.poll_seconds
                    )
                    continue

                minute_key = (
                    timestamp // 60_000
                )

                if (
                    last_minute.get(symbol)
                    == minute_key
                ):
                    high_watermark = timestamp
                    time.sleep(
                        args.poll_seconds
                    )
                    continue

                estimate = np.asarray(
                    model.predict(
                        vector.reshape(1, -1)
                    )[0],
                    dtype=np.float64,
                )

                buy = float(
                    estimate[0]
                )
                sell = float(
                    estimate[1]
                )

                action, reason = choose_action(
                    buy,
                    sell,
                    float(errors[0]),
                    float(errors[1]),
                    args.extra_cost,
                    args.risk_multiplier,
                )

                # Anchor prediction to the actual
                # server-adjusted time at publication.
                prediction_time = (
                    server_now_ms(offset)
                )

                identity = (
                    uuid.uuid4().hex
                )

                event: dict[str, Any] = {
                    "schema":
                        "PV_SHADOW_PREDICTION_V10_2",
                    "prediction_id":
                        identity,
                    "run_id": run_id,
                    "recorded_at_utc":
                        utc_now(),
                    "symbol": symbol,
                    "feature_timestamp_msc":
                        timestamp,
                    "prediction_server_msc":
                        prediction_time,
                    "estimated_buy_raw":
                        buy,
                    "estimated_sell_raw":
                        sell,
                    "calibration_buy_mae":
                        float(errors[0]),
                    "calibration_sell_mae":
                        float(errors[1]),
                    "action": action,
                    "reason": reason,
                    "extra_cost":
                        args.extra_cost,
                    "risk_multiplier":
                        args.risk_multiplier,
                    "feature_age_ms":
                        feature_age,
                    "recorder_age_ms":
                        recorder_age,
                    "outcome_known_at_decision":
                        False,
                    "trading_enabled":
                        False,
                }

                # Durable prediction BEFORE entry.
                append_jsonl(
                    prediction_path,
                    event,
                )

                pending[identity] = Pending(
                    prediction_id=identity,
                    directory=directory,
                    symbol=symbol,
                    prediction_server_msc=
                        prediction_time,
                    action=action,
                    extra_cost=args.extra_cost,
                )

                high_watermark = timestamp
                last_minute[symbol] = (
                    minute_key
                )

                print(
                    "SHADOW_PREDICTION "
                    f"ID={identity[:8]} "
                    f"FEATURE_TIME={timestamp} "
                    f"PREDICTION_TIME={prediction_time} "
                    f"ACTION={action} "
                    f"REASON={reason} "
                    f"BUY_EST={buy:+.5f} "
                    f"SELL_EST={sell:+.5f}",
                    flush=True,
                )

            except (
                OSError,
                ValueError,
                RuntimeError,
                KeyError,
                csv.Error,
            ) as exc:
                print(
                    "SHADOW_WARNING="
                    f"{type(exc).__name__}: "
                    f"{exc}",
                    flush=True,
                )

            time.sleep(
                args.poll_seconds
            )

    except KeyboardInterrupt:
        print("\nSHADOW_LOGGER_STOPPED=YES")
        print(
            f"UNSETTLED_PREDICTIONS={len(pending)}"
        )
        print(f"OUTPUT={directory}")
        print("TRADING_ENABLED=NO")


if __name__ == "__main__":
    main()
