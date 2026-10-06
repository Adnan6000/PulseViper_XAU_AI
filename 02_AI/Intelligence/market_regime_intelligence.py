from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, cast

import numpy as np
import pandas as pd


INTELLIGENCE_VERSION = "MARKET_REGIME_INTELLIGENCE_V1"

CANONICAL_INSTRUMENT = "XAUUSD"
BASE_TIMEFRAME = "M5"
BAR_MINUTES = 5

MINIMUM_HISTORY_BARS = 220

REGIME_TREND_UP = "TREND_UP"
REGIME_TREND_DOWN = "TREND_DOWN"
REGIME_RANGE = "RANGE"
REGIME_COMPRESSION = "COMPRESSION"
REGIME_BREAKOUT_UP = "BREAKOUT_UP"
REGIME_BREAKOUT_DOWN = "BREAKOUT_DOWN"
REGIME_TRANSITION = "TRANSITION"

VOLATILITY_QUIET = "QUIET"
VOLATILITY_NORMAL = "NORMAL"
VOLATILITY_HIGH = "HIGH"
VOLATILITY_EXTREME = "EXTREME"

LIVE_AUTHORIZED = False
EXECUTION_AUTHORIZED = False
TRADE_AUTHORIZED = False


class MarketRegimeIntelligenceError(RuntimeError):
    """Fail-closed market-regime intelligence error."""


@dataclass(frozen=True)
class MarketRegimeSnapshot:
    intelligence_version: str
    canonical_instrument: str
    timeframe: str
    decision_time_utc: str
    source_bar_open_time_utc: str

    regime: str
    regime_confidence: float
    volatility_state: str

    directional_efficiency: float
    trend_direction_score: float
    trend_strength_atr: float

    atr14: float
    atr_ratio_to_median100: float
    recent_range_ratio: float

    compression_detected: bool
    breakout_up_detected: bool
    breakout_down_detected: bool

    ema20: float
    ema50: float
    ema200: float
    ema20_slope_atr: float
    ema50_slope_atr: float

    distance_to_20_bar_high_atr: float
    distance_to_20_bar_low_atr: float

    trade_authorized: bool = False
    live_authorized: bool = False
    execution_authorized: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _require(
    condition: bool,
    reason: str,
) -> None:
    if not condition:
        raise MarketRegimeIntelligenceError(reason)


def _utc_timestamp(
    value: Any,
) -> pd.Timestamp:

    try:
        parsed = pd.Timestamp(value)
    except Exception as exc:
        raise MarketRegimeIntelligenceError(
            "INVALID_DECISION_TIME"
        ) from exc

    _require(
        parsed is not pd.NaT,
        "INVALID_DECISION_TIME_NAT",
    )

    timestamp = cast(
        pd.Timestamp,
        parsed,
    )

    _require(
        timestamp.tzinfo is not None,
        "DECISION_TIME_MUST_BE_TIMEZONE_AWARE",
    )

    return cast(
        pd.Timestamp,
        timestamp.tz_convert("UTC"),
    )


def _iso_utc(
    timestamp: pd.Timestamp,
) -> str:

    value = timestamp.isoformat()

    if value.endswith("+00:00"):
        value = value[:-6] + "Z"

    return value


def _ema(
    series: pd.Series,
    span: int,
) -> pd.Series:

    return cast(
        pd.Series,
        series.ewm(
            span=span,
            adjust=False,
        ).mean(),
    )


def _true_range(
    frame: pd.DataFrame,
) -> pd.Series:

    previous_close = cast(
        pd.Series,
        frame["close"].shift(1),
    )

    high_low = cast(
        pd.Series,
        frame["high"] - frame["low"],
    )

    high_previous_close = cast(
        pd.Series,
        (
            frame["high"]
            -
            previous_close
        ).abs(),
    )

    low_previous_close = cast(
        pd.Series,
        (
            frame["low"]
            -
            previous_close
        ).abs(),
    )

    return cast(
        pd.Series,
        pd.concat(
            [
                high_low,
                high_previous_close,
                low_previous_close,
            ],
            axis=1,
        ).max(axis=1),
    )


def _validate_completed_m5(
    frame: pd.DataFrame,
    *,
    decision_time_utc: pd.Timestamp,
) -> pd.DataFrame:

    _require(
        isinstance(frame, pd.DataFrame),
        "M5_INPUT_NOT_DATAFRAME",
    )

    _require(
        not frame.empty,
        "M5_INPUT_EMPTY",
    )

    required_columns = (
        "time",
        "open",
        "high",
        "low",
        "close",
    )

    missing = [
        column
        for column
        in required_columns
        if column not in frame.columns
    ]

    _require(
        not missing,
        (
            "M5_REQUIRED_COLUMNS_MISSING:"
            +
            ",".join(missing)
        ),
    )

    data = frame.copy()

    try:
        data["time"] = pd.to_datetime(
            data["time"],
            utc=True,
            errors="raise",
        )
    except Exception as exc:
        raise MarketRegimeIntelligenceError(
            "M5_TIMESTAMP_INVALID"
        ) from exc

    time_series = cast(
        pd.Series,
        data["time"],
    )

    _require(
        bool(
            time_series
            .is_monotonic_increasing
        ),
        "M5_TIMESTAMPS_NOT_MONOTONIC",
    )

    _require(
        not bool(
            time_series
            .duplicated()
            .any()
        ),
        "M5_DUPLICATE_TIMESTAMPS",
    )

    for column in (
        "open",
        "high",
        "low",
        "close",
    ):
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        )

    numeric = data[
        [
            "open",
            "high",
            "low",
            "close",
        ]
    ].to_numpy(
        dtype=np.float64
    )

    _require(
        bool(
            np.isfinite(
                numeric
            ).all()
        ),
        "M5_NON_FINITE_OHLC",
    )

    _require(
        len(data)
        >=
        MINIMUM_HISTORY_BARS,
        (
            "M5_INSUFFICIENT_HISTORY:"
            f"{len(data)}"
            f"<{MINIMUM_HISTORY_BARS}"
        ),
    )

    high = data["high"].to_numpy(
        dtype=np.float64
    )

    low = data["low"].to_numpy(
        dtype=np.float64
    )

    open_ = data["open"].to_numpy(
        dtype=np.float64
    )

    close = data["close"].to_numpy(
        dtype=np.float64
    )

    _require(
        bool(
            (
                low > 0
            ).all()
        ),
        "M5_NON_POSITIVE_PRICE",
    )

    _require(
        bool(
            (
                high >= low
            ).all()
        ),
        "M5_HIGH_BELOW_LOW",
    )

    _require(
        bool(
            (
                high >= open_
            ).all()
            and
            (
                high >= close
            ).all()
            and
            (
                low <= open_
            ).all()
            and
            (
                low <= close
            ).all()
        ),
        "M5_INVALID_OHLC_RELATION",
    )

    last_open = cast(
        pd.Timestamp,
        data["time"].iloc[-1],
    )

    last_completed_at = (
        last_open
        +
        pd.Timedelta(
            minutes=BAR_MINUTES
        )
    )

    _require(
        last_completed_at
        <=
        decision_time_utc,
        (
            "FORMING_M5_BAR_FORBIDDEN:"
            f"{_iso_utc(last_open)}"
        ),
    )

    return data.reset_index(
        drop=True
    )


def _clamp01(
    value: float,
) -> float:

    return float(
        min(
            1.0,
            max(
                0.0,
                value,
            ),
        )
    )


class MarketRegimeIntelligence:
    """
    Deterministic, causal market-regime sidecar.

    V1 is descriptive/research intelligence only.

    It does not:
    - modify the frozen R03 331-feature contract,
    - retrain or calibrate R03,
    - authorize trades,
    - authorize live execution.
    """

    def analyze(
        self,
        *,
        completed_m5: pd.DataFrame,
        decision_time_utc: Any,
        canonical_instrument: str = CANONICAL_INSTRUMENT,
    ) -> MarketRegimeSnapshot:

        _require(
            canonical_instrument
            ==
            CANONICAL_INSTRUMENT,
            (
                "UNSUPPORTED_CANONICAL_INSTRUMENT:"
                f"{canonical_instrument}"
            ),
        )

        decision_time = (
            _utc_timestamp(
                decision_time_utc
            )
        )

        data = (
            _validate_completed_m5(
                completed_m5,
                decision_time_utc=(
                    decision_time
                ),
            )
        )

        close = cast(
            pd.Series,
            data["close"],
        )

        high = cast(
            pd.Series,
            data["high"],
        )

        low = cast(
            pd.Series,
            data["low"],
        )

        open_ = cast(
            pd.Series,
            data["open"],
        )

        true_range = (
            _true_range(
                data
            )
        )

        atr14_series = cast(
            pd.Series,
            true_range
            .rolling(
                14,
                min_periods=14,
            )
            .mean(),
        )

        atr14 = float(
            atr14_series.iloc[-1]
        )

        _require(
            np.isfinite(atr14)
            and
            atr14 > 0,
            "ATR14_INVALID",
        )

        atr_median100 = float(
            atr14_series
            .iloc[-100:]
            .median()
        )

        _require(
            np.isfinite(
                atr_median100
            )
            and
            atr_median100 > 0,
            "ATR_MEDIAN100_INVALID",
        )

        atr_ratio = (
            atr14
            /
            atr_median100
        )

        ema20_series = (
            _ema(
                close,
                20,
            )
        )

        ema50_series = (
            _ema(
                close,
                50,
            )
        )

        ema200_series = (
            _ema(
                close,
                200,
            )
        )

        ema20 = float(
            ema20_series.iloc[-1]
        )

        ema50 = float(
            ema50_series.iloc[-1]
        )

        ema200 = float(
            ema200_series.iloc[-1]
        )

        ema20_slope_atr = float(
            (
                ema20_series.iloc[-1]
                -
                ema20_series.iloc[-6]
            )
            /
            atr14
        )

        ema50_slope_atr = float(
            (
                ema50_series.iloc[-1]
                -
                ema50_series.iloc[-11]
            )
            /
            atr14
        )

        trend_strength_atr = float(
            (
                abs(
                    ema20
                    -
                    ema50
                )
                +
                abs(
                    ema50
                    -
                    ema200
                )
            )
            /
            atr14
        )

        price_change_20 = float(
            close.iloc[-1]
            -
            close.iloc[-21]
        )

        path_length_20 = float(
            close
            .iloc[-21:]
            .diff()
            .abs()
            .sum()
        )

        if path_length_20 <= 0:
            directional_efficiency = 0.0
        else:
            directional_efficiency = float(
                abs(
                    price_change_20
                )
                /
                path_length_20
            )

        direction_sign = float(
            np.sign(
                price_change_20
            )
        )

        directional_efficiency = (
            _clamp01(
                directional_efficiency
            )
        )

        trend_direction_score = float(
            direction_sign
            *
            directional_efficiency
        )

        candle_range = cast(
            pd.Series,
            high - low,
        )

        recent_range_mean = float(
            candle_range
            .iloc[-10:]
            .mean()
        )

        baseline_range_mean = float(
            candle_range
            .iloc[-50:-10]
            .mean()
        )

        _require(
            np.isfinite(
                baseline_range_mean
            )
            and
            baseline_range_mean > 0,
            "BASELINE_RANGE_INVALID",
        )

        recent_range_ratio = float(
            recent_range_mean
            /
            baseline_range_mean
        )

        compression_detected = bool(
            recent_range_ratio
            <=
            0.70
            and
            atr_ratio
            <=
            0.90
        )

        previous_20_high = float(
            high
            .iloc[-21:-1]
            .max()
        )

        previous_20_low = float(
            low
            .iloc[-21:-1]
            .min()
        )

        current_close = float(
            close.iloc[-1]
        )

        current_open = float(
            open_.iloc[-1]
        )

        current_high = float(
            high.iloc[-1]
        )

        current_low = float(
            low.iloc[-1]
        )

        current_range = (
            current_high
            -
            current_low
        )

        if current_range <= 0:
            body_ratio = 0.0
        else:
            body_ratio = float(
                abs(
                    current_close
                    -
                    current_open
                )
                /
                current_range
            )

        breakout_buffer = (
            0.10
            *
            atr14
        )

        breakout_up_detected = bool(
            current_close
            >
            (
                previous_20_high
                +
                breakout_buffer
            )
            and
            body_ratio
            >=
            0.55
            and
            current_close
            >
            current_open
        )

        breakout_down_detected = bool(
            current_close
            <
            (
                previous_20_low
                -
                breakout_buffer
            )
            and
            body_ratio
            >=
            0.55
            and
            current_close
            <
            current_open
        )

        distance_to_20_high_atr = float(
            (
                current_close
                -
                previous_20_high
            )
            /
            atr14
        )

        distance_to_20_low_atr = float(
            (
                current_close
                -
                previous_20_low
            )
            /
            atr14
        )

        bullish_alignment = bool(
            ema20
            >
            ema50
            >
            ema200
        )

        bearish_alignment = bool(
            ema20
            <
            ema50
            <
            ema200
        )

        bullish_slopes = bool(
            ema20_slope_atr > 0
            and
            ema50_slope_atr > 0
        )

        bearish_slopes = bool(
            ema20_slope_atr < 0
            and
            ema50_slope_atr < 0
        )

        trending_up = bool(
            bullish_alignment
            and
            bullish_slopes
            and
            trend_direction_score
            >=
            0.30
            and
            trend_strength_atr
            >=
            0.50
        )

        trending_down = bool(
            bearish_alignment
            and
            bearish_slopes
            and
            trend_direction_score
            <=
            -0.30
            and
            trend_strength_atr
            >=
            0.50
        )

        range_detected = bool(
            directional_efficiency
            <=
            0.22
            and
            trend_strength_atr
            <=
            0.75
        )

        if breakout_up_detected:
            regime = (
                REGIME_BREAKOUT_UP
            )

        elif breakout_down_detected:
            regime = (
                REGIME_BREAKOUT_DOWN
            )

        elif compression_detected:
            regime = (
                REGIME_COMPRESSION
            )

        elif trending_up:
            regime = (
                REGIME_TREND_UP
            )

        elif trending_down:
            regime = (
                REGIME_TREND_DOWN
            )

        elif range_detected:
            regime = (
                REGIME_RANGE
            )

        else:
            regime = (
                REGIME_TRANSITION
            )

        if atr_ratio <= 0.70:
            volatility_state = (
                VOLATILITY_QUIET
            )

        elif atr_ratio < 1.35:
            volatility_state = (
                VOLATILITY_NORMAL
            )

        elif atr_ratio < 2.00:
            volatility_state = (
                VOLATILITY_HIGH
            )

        else:
            volatility_state = (
                VOLATILITY_EXTREME
            )

        if regime in (
            REGIME_BREAKOUT_UP,
            REGIME_BREAKOUT_DOWN,
        ):

            breakout_distance = max(
                abs(
                    distance_to_20_high_atr
                ),
                abs(
                    distance_to_20_low_atr
                ),
            )

            regime_confidence = (
                0.50
                +
                min(
                    0.25,
                    body_ratio
                    *
                    0.25,
                )
                +
                min(
                    0.25,
                    breakout_distance
                    *
                    0.20,
                )
            )

        elif regime in (
            REGIME_TREND_UP,
            REGIME_TREND_DOWN,
        ):

            regime_confidence = (
                0.35
                +
                min(
                    0.35,
                    directional_efficiency
                    *
                    0.50,
                )
                +
                min(
                    0.30,
                    trend_strength_atr
                    *
                    0.12,
                )
            )

        elif regime == REGIME_COMPRESSION:

            compression_strength = (
                max(
                    0.0,
                    1.0
                    -
                    recent_range_ratio,
                )
            )

            regime_confidence = (
                0.45
                +
                min(
                    0.35,
                    compression_strength
                    *
                    0.80,
                )
                +
                min(
                    0.20,
                    max(
                        0.0,
                        1.0
                        -
                        atr_ratio,
                    )
                    *
                    0.50,
                )
            )

        elif regime == REGIME_RANGE:

            regime_confidence = (
                0.40
                +
                min(
                    0.35,
                    (
                        1.0
                        -
                        directional_efficiency
                    )
                    *
                    0.35,
                )
                +
                min(
                    0.25,
                    max(
                        0.0,
                        1.0
                        -
                        (
                            trend_strength_atr
                            /
                            0.75
                        ),
                    )
                    *
                    0.25,
                )
            )

        else:

            regime_confidence = (
                0.30
                +
                min(
                    0.25,
                    directional_efficiency
                    *
                    0.20,
                )
                +
                min(
                    0.20,
                    trend_strength_atr
                    *
                    0.08,
                )
            )

        regime_confidence = (
            _clamp01(
                float(
                    regime_confidence
                )
            )
        )

        source_bar_open = cast(
            pd.Timestamp,
            data["time"].iloc[-1],
        )

        return MarketRegimeSnapshot(
            intelligence_version=(
                INTELLIGENCE_VERSION
            ),
            canonical_instrument=(
                canonical_instrument
            ),
            timeframe=(
                BASE_TIMEFRAME
            ),
            decision_time_utc=(
                _iso_utc(
                    decision_time
                )
            ),
            source_bar_open_time_utc=(
                _iso_utc(
                    source_bar_open
                )
            ),
            regime=regime,
            regime_confidence=(
                regime_confidence
            ),
            volatility_state=(
                volatility_state
            ),
            directional_efficiency=(
                float(
                    directional_efficiency
                )
            ),
            trend_direction_score=(
                trend_direction_score
            ),
            trend_strength_atr=(
                trend_strength_atr
            ),
            atr14=atr14,
            atr_ratio_to_median100=(
                float(
                    atr_ratio
                )
            ),
            recent_range_ratio=(
                recent_range_ratio
            ),
            compression_detected=(
                compression_detected
            ),
            breakout_up_detected=(
                breakout_up_detected
            ),
            breakout_down_detected=(
                breakout_down_detected
            ),
            ema20=ema20,
            ema50=ema50,
            ema200=ema200,
            ema20_slope_atr=(
                ema20_slope_atr
            ),
            ema50_slope_atr=(
                ema50_slope_atr
            ),
            distance_to_20_bar_high_atr=(
                distance_to_20_high_atr
            ),
            distance_to_20_bar_low_atr=(
                distance_to_20_low_atr
            ),
            trade_authorized=False,
            live_authorized=False,
            execution_authorized=False,
        )


def analyze_market_regime(
    *,
    completed_m5: pd.DataFrame,
    decision_time_utc: Any,
    canonical_instrument: str = CANONICAL_INSTRUMENT,
) -> MarketRegimeSnapshot:

    engine = (
        MarketRegimeIntelligence()
    )

    return engine.analyze(
        completed_m5=completed_m5,
        decision_time_utc=decision_time_utc,
        canonical_instrument=(
            canonical_instrument
        ),
    )