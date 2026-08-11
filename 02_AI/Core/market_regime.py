"""
===============================================================================
Module      : market_regime.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Causal Market Regime Metadata Engine
===============================================================================

Contract
--------
Uses current/past OHLC only. No future candles, centered windows, outcomes,
Confidence, trade_ready, setup direction, risk sizing, or trade filtering.

Outputs are research metadata until independent validation justifies downstream use.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class MarketRegimeEngine:
    VERSION = "1.0"
    MODE = "CAUSAL_METADATA_ONLY"

    REQUIRED_COLUMNS = (
        "open",
        "high",
        "low",
        "close",
    )

    OUTPUT_COLUMNS = (
        "regime_ready",
        "regime_atr",
        "regime_atr_percentile",
        "regime_range_atr",
        "regime_efficiency",
        "regime_directional_move_atr",
        "regime_volatility",
        "regime_trend",
        "regime_state",
        "regime_trend_strength",
        "regime_time_bucket_utc",
        "regime_version",
    )

    def __init__(
        self,
        atr_period: int = 14,
        volatility_lookback: int = 240,
        volatility_min_periods: int = 60,
        low_volatility_percentile: float = 33.0,
        high_volatility_percentile: float = 67.0,
        trend_lookback: int = 20,
        min_trend_efficiency: float = 0.35,
        min_trend_move_atr: float = 1.00,
        strength_move_atr_cap: float = 3.00,
    ) -> None:

        if atr_period <= 0:
            raise ValueError(
                "atr_period must be greater than zero"
            )

        if volatility_lookback <= 1:
            raise ValueError(
                "volatility_lookback must be greater than one"
            )

        if not (
            2
            <= volatility_min_periods
            <= volatility_lookback
        ):
            raise ValueError(
                "volatility_min_periods must be in "
                "[2, volatility_lookback]"
            )

        if not (
            0.0
            < low_volatility_percentile
            < high_volatility_percentile
            < 100.0
        ):
            raise ValueError(
                "volatility percentile thresholds must satisfy "
                "0 < low < high < 100"
            )

        if trend_lookback <= 1:
            raise ValueError(
                "trend_lookback must be greater than one"
            )

        if not (
            0.0
            <= min_trend_efficiency
            <= 1.0
        ):
            raise ValueError(
                "min_trend_efficiency must be between 0 and 1"
            )

        if min_trend_move_atr <= 0.0:
            raise ValueError(
                "min_trend_move_atr must be greater than zero"
            )

        if strength_move_atr_cap <= 0.0:
            raise ValueError(
                "strength_move_atr_cap must be greater than zero"
            )

        self.atr_period = int(
            atr_period
        )

        self.volatility_lookback = int(
            volatility_lookback
        )

        self.volatility_min_periods = int(
            volatility_min_periods
        )

        self.low_volatility_percentile = float(
            low_volatility_percentile
        )

        self.high_volatility_percentile = float(
            high_volatility_percentile
        )

        self.trend_lookback = int(
            trend_lookback
        )

        self.min_trend_efficiency = float(
            min_trend_efficiency
        )

        self.min_trend_move_atr = float(
            min_trend_move_atr
        )

        self.strength_move_atr_cap = float(
            strength_move_atr_cap
        )

    # =========================================================================
    # Validation
    # =========================================================================

    @classmethod
    def _validate_input(
        cls,
        data: pd.DataFrame,
    ) -> None:

        if not isinstance(
            data,
            pd.DataFrame,
        ):
            raise TypeError(
                "MarketRegimeEngine input must be a pandas DataFrame"
            )

        missing = (
            set(
                cls.REQUIRED_COLUMNS
            )
            - set(
                data.columns
            )
        )

        if missing:
            raise ValueError(
                "Missing required regime columns: "
                + ", ".join(
                    sorted(
                        missing
                    )
                )
            )

    @staticmethod
    def _numeric(
        series: pd.Series,
    ) -> pd.Series:

        values: Any = pd.to_numeric(
            series,
            errors="coerce",
        )

        return pd.Series(
            values,
            index=series.index,
            dtype="float64",
        )

    # =========================================================================
    # ATR
    # =========================================================================

    def _calculate_atr(
        self,
        df: pd.DataFrame,
    ) -> pd.Series:

        high = self._numeric(
            df[
                "high"
            ]
        )

        low = self._numeric(
            df[
                "low"
            ]
        )

        close = self._numeric(
            df[
                "close"
            ]
        )

        previous_close = close.shift(
            1
        )

        true_range = pd.concat(
            [
                high - low,
                (
                    high
                    - previous_close
                ).abs(),
                (
                    low
                    - previous_close
                ).abs(),
            ],
            axis=1,
        ).max(
            axis=1
        )

        return (
            true_range
            .rolling(
                window=self.atr_period,
                min_periods=self.atr_period,
            )
            .mean()
            .astype(
                "float64"
            )
        )

    def _atr_series(
        self,
        df: pd.DataFrame,
    ) -> pd.Series:

        calculated = self._calculate_atr(
            df
        )

        if (
            "atr"
            not in df.columns
        ):
            return calculated

        supplied = (
            self._numeric(
                df[
                    "atr"
                ]
            )
            .replace(
                [
                    np.inf,
                    -np.inf,
                ],
                np.nan,
            )
            .where(
                lambda values: (
                    values
                    > 0.0
                )
            )
        )

        return (
            supplied
            .fillna(
                calculated
            )
            .astype(
                "float64"
            )
        )

    # =========================================================================
    # Causal factors
    # =========================================================================

    def _atr_percentile(
        self,
        atr: pd.Series,
    ) -> pd.Series:
        """
        Current ATR rank inside trailing history.

        Rolling.rank is right-aligned and therefore causal.
        """

        return (
            atr
            .rolling(
                window=self.volatility_lookback,
                min_periods=self.volatility_min_periods,
            )
            .rank(
                method="average",
                pct=True,
            )
            .mul(
                100.0
            )
            .clip(
                lower=0.0,
                upper=100.0,
            )
            .astype(
                "float64"
            )
        )

    def _efficiency_ratio(
        self,
        close: pd.Series,
    ) -> pd.Series:
        """
        Kaufman-style trailing path efficiency.

        efficiency =
            absolute net movement
            /
            total absolute path travelled
        """

        net_move = (
            close
            - close.shift(
                self.trend_lookback
            )
        ).abs()

        path = (
            close
            .diff()
            .abs()
            .rolling(
                window=self.trend_lookback,
                min_periods=self.trend_lookback,
            )
            .sum()
        )

        return (
            (
                net_move
                /
                path.replace(
                    0.0,
                    np.nan,
                )
            )
            .clip(
                lower=0.0,
                upper=1.0,
            )
            .astype(
                "float64"
            )
        )

    def _directional_move_atr(
        self,
        close: pd.Series,
        atr: pd.Series,
    ) -> pd.Series:

        move = (
            close
            - close.shift(
                self.trend_lookback
            )
        )

        return (
            (
                move
                /
                atr.replace(
                    0.0,
                    np.nan,
                )
            )
            .replace(
                [
                    np.inf,
                    -np.inf,
                ],
                np.nan,
            )
            .astype(
                "float64"
            )
        )

    @staticmethod
    def _range_atr(
        high: pd.Series,
        low: pd.Series,
        atr: pd.Series,
    ) -> pd.Series:

        return (
            (
                (
                    high
                    - low
                )
                /
                atr.replace(
                    0.0,
                    np.nan,
                )
            )
            .replace(
                [
                    np.inf,
                    -np.inf,
                ],
                np.nan,
            )
            .clip(
                lower=0.0
            )
            .astype(
                "float64"
            )
        )

    # =========================================================================
    # Volatility classification
    # =========================================================================

    def _volatility_labels(
        self,
        percentile: pd.Series,
        ready: pd.Series,
    ) -> pd.Series:

        labels: list[
            str
        ] = []

        for (
            is_ready,
            raw_value,
        ) in zip(
            ready.tolist(),
            percentile.tolist(),
        ):

            if not bool(
                is_ready
            ):
                labels.append(
                    "UNKNOWN"
                )
                continue

            value = float(
                raw_value
            )

            if (
                value
                <= self.low_volatility_percentile
            ):
                labels.append(
                    "LOW"
                )

            elif (
                value
                >= self.high_volatility_percentile
            ):
                labels.append(
                    "HIGH"
                )

            else:
                labels.append(
                    "NORMAL"
                )

        return pd.Series(
            labels,
            index=percentile.index,
            dtype="object",
        )

    # =========================================================================
    # Trend classification
    # =========================================================================

    def _trend_labels(
        self,
        efficiency: pd.Series,
        directional_move_atr: pd.Series,
        ready: pd.Series,
    ) -> pd.Series:

        labels: list[
            str
        ] = []

        for (
            is_ready,
            raw_efficiency,
            raw_move,
        ) in zip(
            ready.tolist(),
            efficiency.tolist(),
            directional_move_atr.tolist(),
        ):

            if not bool(
                is_ready
            ):
                labels.append(
                    "UNKNOWN"
                )
                continue

            efficiency_value = float(
                raw_efficiency
            )

            move_value = float(
                raw_move
            )

            trending = (
                efficiency_value
                >= self.min_trend_efficiency
                and
                abs(
                    move_value
                )
                >= self.min_trend_move_atr
            )

            if not trending:
                labels.append(
                    "RANGE"
                )

            elif (
                move_value
                > 0.0
            ):
                labels.append(
                    "BULLISH"
                )

            else:
                labels.append(
                    "BEARISH"
                )

        return pd.Series(
            labels,
            index=efficiency.index,
            dtype="object",
        )

    # =========================================================================
    # Strength
    # =========================================================================

    def _trend_strength(
        self,
        efficiency: pd.Series,
        directional_move_atr: pd.Series,
        ready: pd.Series,
    ) -> pd.Series:

        efficiency_component = (
            efficiency
            .fillna(
                0.0
            )
            .clip(
                0.0,
                1.0,
            )
        )

        move_component = (
            (
                directional_move_atr
                .abs()
                .fillna(
                    0.0
                )
            )
            /
            self.strength_move_atr_cap
        ).clip(
            0.0,
            1.0,
        )

        strength = (
            (
                efficiency_component
                * 0.60
            )
            +
            (
                move_component
                * 0.40
            )
        ) * 100.0

        return (
            strength
            .where(
                ready,
                0.0,
            )
            .clip(
                0.0,
                100.0,
            )
            .astype(
                "float64"
            )
        )

    # =========================================================================
    # Combined regime
    # =========================================================================

    @staticmethod
    def _combined_state(
        trend: pd.Series,
        volatility: pd.Series,
    ) -> pd.Series:

        labels: list[
            str
        ] = []

        for (
            trend_value,
            volatility_value,
        ) in zip(
            trend.tolist(),
            volatility.tolist(),
        ):

            trend_text = str(
                trend_value
            )

            volatility_text = str(
                volatility_value
            )

            if (
                "UNKNOWN"
                in (
                    trend_text,
                    volatility_text,
                )
            ):
                labels.append(
                    "UNKNOWN"
                )

            else:
                labels.append(
                    (
                        f"{trend_text}_"
                        f"{volatility_text}_VOL"
                    )
                )

        return pd.Series(
            labels,
            index=trend.index,
            dtype="object",
        )

    # =========================================================================
    # UTC time context
    # =========================================================================

    @staticmethod
    def _time_bucket_utc(
        df: pd.DataFrame,
    ) -> pd.Series:

        if (
            "time"
            not in df.columns
        ):
            return pd.Series(
                "UNKNOWN",
                index=df.index,
                dtype="object",
            )

        parsed: Any = pd.to_datetime(
            df[
                "time"
            ],
            errors="coerce",
        )

        labels: list[
            str
        ] = []

        for raw_hour in (
            parsed
            .dt
            .hour
            .tolist()
        ):

            if pd.isna(
                raw_hour
            ):
                labels.append(
                    "UNKNOWN"
                )
                continue

            hour = int(
                raw_hour
            )

            if hour <= 5:
                labels.append(
                    "UTC_00_05"
                )

            elif hour <= 11:
                labels.append(
                    "UTC_06_11"
                )

            elif hour <= 17:
                labels.append(
                    "UTC_12_17"
                )

            else:
                labels.append(
                    "UTC_18_23"
                )

        return pd.Series(
            labels,
            index=df.index,
            dtype="object",
        )

    # =========================================================================
    # Generate
    # =========================================================================

    def generate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        self._validate_input(
            data
        )

        df = data.copy()

        high = self._numeric(
            df[
                "high"
            ]
        )

        low = self._numeric(
            df[
                "low"
            ]
        )

        close = self._numeric(
            df[
                "close"
            ]
        )

        atr = self._atr_series(
            df
        )

        percentile = self._atr_percentile(
            atr
        )

        efficiency = self._efficiency_ratio(
            close
        )

        directional_move_atr = (
            self._directional_move_atr(
                close,
                atr,
            )
        )

        range_atr = self._range_atr(
            high,
            low,
            atr,
        )

        ready = (
            atr.notna()
            &
            percentile.notna()
            &
            efficiency.notna()
            &
            directional_move_atr.notna()
            &
            range_atr.notna()
        )

        volatility = self._volatility_labels(
            percentile,
            ready,
        )

        trend = self._trend_labels(
            efficiency,
            directional_move_atr,
            ready,
        )

        df[
            "regime_ready"
        ] = ready.astype(
            "int8"
        )

        df[
            "regime_atr"
        ] = atr

        df[
            "regime_atr_percentile"
        ] = percentile

        df[
            "regime_range_atr"
        ] = range_atr

        df[
            "regime_efficiency"
        ] = efficiency

        df[
            "regime_directional_move_atr"
        ] = directional_move_atr

        df[
            "regime_volatility"
        ] = volatility

        df[
            "regime_trend"
        ] = trend

        df[
            "regime_state"
        ] = self._combined_state(
            trend,
            volatility,
        )

        df[
            "regime_trend_strength"
        ] = self._trend_strength(
            efficiency,
            directional_move_atr,
            ready,
        )

        df[
            "regime_time_bucket_utc"
        ] = self._time_bucket_utc(
            df
        )

        df[
            "regime_version"
        ] = self.VERSION

        return df


market_regime = MarketRegimeEngine()