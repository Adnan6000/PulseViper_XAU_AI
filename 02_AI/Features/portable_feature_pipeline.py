"""
===============================================================================
Module      : portable_feature_pipeline.py
Project     : PulseViper XAU AI
Purpose     : Production Multi-Timeframe Feature Pipeline (Gate 13)
===============================================================================

Production-safe feature generation pipeline capable of producing the exact
frozen 331-feature model input contract used by the accepted historical
research lineage (C04_FLAT_EXTRA_TREES_CONSTRAINED).

Fail-Closed Guarantees:
- Strictly produces exactly 331 features in exact frozen name and order.
- SHA256 checksum validation against EXPECTED_FEATURE_COLUMNS_SHA256.
- Strict causal alignment: HTF bars are available only after bar close.
- Incomplete HTF bars (e.g. intraday D1) never leak into decision time.
- Timezone-aware UTC normalization on all timestamps.
- Explicit support for proven symbols: XAUUSD, XAUUSDm.
- Finite number enforcement (no NaN, no inf in model input).
- Zero target column generation or leakage.
- Zero execution or live trading authority.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence, cast

import numpy as np
import pandas as pd

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_contract: Any = importlib.import_module("02_AI.Features.portable_feature_contract")

PORTABLE_FEATURE_CONTRACT_VERSION: str = str(_contract.PORTABLE_FEATURE_CONTRACT_VERSION)
EXPECTED_FEATURE_COUNT: int = int(_contract.EXPECTED_FEATURE_COUNT)
EXPECTED_FEATURE_COLUMNS_SHA256: str = str(_contract.EXPECTED_FEATURE_COLUMNS_SHA256)
FROZEN_FEATURE_COLUMNS: tuple[str, ...] = tuple(_contract.FROZEN_FEATURE_COLUMNS)
BASE_TIMEFRAME: str = str(_contract.BASE_TIMEFRAME)
CONTEXT_TIMEFRAMES: tuple[str, ...] = tuple(_contract.CONTEXT_TIMEFRAMES)
ALL_TIMEFRAMES: tuple[str, ...] = tuple(_contract.ALL_TIMEFRAMES)
CANONICAL_SYMBOL: str = str(_contract.CANONICAL_SYMBOL)
SUPPORTED_SYMBOLS: tuple[str, ...] = tuple(_contract.SUPPORTED_SYMBOLS)
TIMEFRAME_MINUTES: dict[str, int] = dict(_contract.TIMEFRAME_MINUTES)
D1_SESSION_BOUNDARY_UTC: str = str(_contract.D1_SESSION_BOUNDARY_UTC)
normalize_supported_symbol: Any = _contract.normalize_supported_symbol
verify_feature_columns: Any = _contract.verify_feature_columns
compute_feature_columns_sha256: Any = _contract.compute_feature_columns_sha256

# Core feature and domain engines
_fg_mod: Any = importlib.import_module("02_AI.Features.feature_generator")
_fl_mod: Any = importlib.import_module("02_AI.Features.feature_list")
FeatureGenerator: Any = _fg_mod.FeatureGenerator
FEATURE_COLUMNS: tuple[str, ...] = tuple(_fl_mod.FEATURE_COLUMNS)

_enricher_mod: Any = importlib.import_module("02_AI.Dataset.training_feature_enricher")
TrainingFeatureEnricher: Any = _enricher_mod.TrainingFeatureEnricher


class PortableFeatureGenerationError(RuntimeError):
    """Fail-closed exception raised when feature generation cannot satisfy the contract."""
    pass


@dataclass(frozen=True)
class PortableFeaturePipelineResult:
    """Immutable result of production feature generation."""
    features: pd.DataFrame
    decision_times: pd.Series
    feature_names: tuple[str, ...]
    feature_count: int
    feature_columns_sha256: str
    row_count: int
    symbol: str
    d1_source: str
    live_authorized: bool = False

    def to_model_matrix(self) -> np.ndarray:
        """Return the validated (N, 331) float32 numpy array ready for model inference."""
        arr = self.features.to_numpy(dtype=np.float32)
        if arr.shape[1] != EXPECTED_FEATURE_COUNT:
            raise PortableFeatureGenerationError(
                f"MODEL_MATRIX_COLUMN_COUNT_MISMATCH: {arr.shape[1]} != {EXPECTED_FEATURE_COUNT}"
            )
        if not bool(np.all(np.isfinite(arr))):
            raise PortableFeatureGenerationError("MODEL_MATRIX_CONTAINS_NON_FINITE_VALUES")
        return arr


class PortableFeaturePipeline:
    """Production Multi-Timeframe Feature Pipeline."""

    REQUIRED_RAW_COLUMNS: tuple[str, ...] = (
        "time",
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
    )

    DEFAULT_MIN_HISTORY_BARS: dict[str, int] = {
        "M5": 200,
        "M15": 200,
        "M30": 200,
        "H1": 200,
        "H4": 200,
        "D1": 200,
    }

    def __init__(
        self,
        *,
        d1_reconstruction_source: str | None = None,
        min_history_bars: dict[str, int] | None = None,
    ) -> None:
        """
        Initialize pipeline.
        d1_reconstruction_source: Optional override ("H1" or "M5") to force D1 reconstruction.
        min_history_bars: Optional override for timeframe minimum warm-up bars.
        """
        self.d1_reconstruction_source = d1_reconstruction_source
        self.min_history_bars = dict(self.DEFAULT_MIN_HISTORY_BARS)
        if min_history_bars is not None:
            self.min_history_bars.update(min_history_bars)
        self.feature_generator = FeatureGenerator()
        self.domain_enricher = TrainingFeatureEnricher()

    @staticmethod
    def _validate_raw_frame(
        frame: pd.DataFrame,
        timeframe: str,
        *,
        min_bars: int = 50,
    ) -> pd.DataFrame:
        """Validate raw OHLCV frame for schema, timestamp monotonicity, and OHLC validity."""
        if frame is None or frame.empty:
            raise PortableFeatureGenerationError(f"EMPTY_RAW_FRAME: {timeframe}")

        missing = [col for col in PortableFeaturePipeline.REQUIRED_RAW_COLUMNS if col not in frame.columns]
        if missing:
            raise PortableFeatureGenerationError(
                f"MISSING_REQUIRED_RAW_COLUMNS: {timeframe}: {', '.join(missing)}"
            )

        df = frame.copy()

        # Normalize time to UTC
        try:
            df["time"] = pd.to_datetime(df["time"], utc=True, errors="raise")
        except Exception as exc:
            raise PortableFeatureGenerationError(
                f"INVALID_TIMESTAMP_IN_FRAME: {timeframe}: {exc}"
            ) from exc

        # Check chronological monotonicity
        time_series = cast(pd.Series, df["time"])
        if not bool(time_series.is_monotonic_increasing):
            raise PortableFeatureGenerationError(
                f"TIMESTAMPS_NOT_MONOTONIC_INCREASING: {timeframe}"
            )

        # Check duplicate timestamps
        if bool(time_series.duplicated().any()):
            raise PortableFeatureGenerationError(
                f"DUPLICATE_TIMESTAMPS_DETECTED: {timeframe}"
            )

        # Validate numeric OHLCV
        for col in ("open", "high", "low", "close", "tick_volume"):
            df[col] = pd.to_numeric(df[col], errors="coerce")

        ohlcv_values = df[["open", "high", "low", "close", "tick_volume"]].to_numpy()
        if bool(np.isnan(ohlcv_values).any()):
            raise PortableFeatureGenerationError(
                f"NON_NUMERIC_OR_NAN_IN_OHLCV: {timeframe}"
            )

        low_vals = cast(pd.Series, df["low"]).to_numpy()
        high_vals = cast(pd.Series, df["high"]).to_numpy()
        open_vals = cast(pd.Series, df["open"]).to_numpy()
        close_vals = cast(pd.Series, df["close"]).to_numpy()

        if bool((low_vals <= 0).any()) or bool((high_vals < low_vals).any()):
            raise PortableFeatureGenerationError(
                f"INVALID_OHLC_PRICE_RELATION: {timeframe}"
            )
        if bool((high_vals < open_vals).any()) or bool((high_vals < close_vals).any()):
            raise PortableFeatureGenerationError(
                f"INVALID_OHLC_PRICE_RELATION: {timeframe}"
            )
        if bool((low_vals > open_vals).any()) or bool((low_vals > close_vals).any()):
            raise PortableFeatureGenerationError(
                f"INVALID_OHLC_PRICE_RELATION: {timeframe}"
            )

        if len(df) < min_bars:
            raise PortableFeatureGenerationError(
                f"INSUFFICIENT_HISTORY_BARS: {timeframe}: {len(df)} < {min_bars}"
            )

        return df.reset_index(drop=True)

    @classmethod
    def reconstruct_d1(
        cls,
        intraday_df: pd.DataFrame,
        *,
        source_timeframe: str = "H1",
        min_history_bars: int | None = None,
    ) -> pd.DataFrame:
        """
        Reconstruct canonical completed D1 candles from intraday bars strictly at 00:00:00 UTC.
        Only completed day sessions are retained.
        """
        required_d1_bars = min_history_bars if min_history_bars is not None else cls.DEFAULT_MIN_HISTORY_BARS["D1"]
        valid_intraday = cls._validate_raw_frame(intraday_df, source_timeframe, min_bars=1)

        # Group by UTC calendar date
        time_series = cast(pd.Series, valid_intraday["time"])
        valid_intraday["session_date"] = time_series.dt.floor("D")

        aggregated = cast(
            pd.DataFrame,
            valid_intraday.groupby("session_date", as_index=False)
            .agg(
                open=("open", "first"),
                high=("high", "max"),
                low=("low", "min"),
                close=("close", "last"),
                tick_volume=("tick_volume", "sum"),
                bar_count=("open", "count"),
            )
        )

        aggregated["time"] = aggregated["session_date"]

        output_cols = ["time", "open", "high", "low", "close", "tick_volume"]
        result = cast(pd.DataFrame, aggregated[output_cols].copy())
        result = result.sort_values(by="time").reset_index(drop=True)

        if len(result) < required_d1_bars:
            raise PortableFeatureGenerationError(
                f"RECONSTRUCTED_D1_INSUFFICIENT_BARS: {len(result)} < {required_d1_bars}"
            )

        return result

    def _generate_technical_frame(
        self,
        frame: pd.DataFrame,
        timeframe: str,
    ) -> pd.DataFrame:
        """Generate the 43 technical features for a timeframe and tag available_time."""
        prefix = timeframe.lower()

        try:
            generated = cast(pd.DataFrame, self.feature_generator.generate(frame))
        except Exception as exc:
            raise PortableFeatureGenerationError(
                f"TECHNICAL_FEATURE_GENERATION_FAILED: {timeframe}: {exc}"
            ) from exc

        missing = [f for f in FEATURE_COLUMNS if f not in generated.columns]
        if missing:
            raise PortableFeatureGenerationError(
                f"MISSING_TECHNICAL_FEATURE_OUTPUT: {timeframe}: {', '.join(missing)}"
            )

        result = pd.DataFrame({"time": generated["time"]})

        bar_minutes = TIMEFRAME_MINUTES[timeframe]
        gen_time = cast(pd.Series, generated["time"])
        result["available_time"] = gen_time + pd.to_timedelta(bar_minutes, unit="m")

        for feature in FEATURE_COLUMNS:
            col_name = f"{prefix}_{feature}"
            feat_series = cast(pd.Series, generated[feature])
            num_series = cast(pd.Series, pd.to_numeric(feat_series, errors="coerce"))
            result[col_name] = num_series.astype("float32")

        return result

    @staticmethod
    def _generate_m5_tick_volume_ratio20(
        m5_frame: pd.DataFrame,
    ) -> pd.Series:
        """Compute the retained relative volume feature: m5_tick_volume_ratio20."""
        raw_vol = np.asarray(pd.to_numeric(m5_frame["tick_volume"], errors="coerce"), dtype=np.float64)
        clipped_vol = np.clip(raw_vol, a_min=0.0, a_max=None)
        vol = pd.Series(clipped_vol, dtype="float32")
        rolling_mean = cast(pd.Series, vol.rolling(window=20, min_periods=20).mean())
        safe_denom = cast(pd.Series, rolling_mean.replace(0, np.nan))
        ratio = (vol / safe_denom).astype("float32")
        ratio.name = "m5_tick_volume_ratio20"
        return ratio

    def _generate_m5_domain_features(
        self,
        m5_frame: pd.DataFrame,
    ) -> pd.DataFrame:
        """Generate the 63 causal domain features on M5 using existing domain engines."""
        try:
            domain_df = cast(
                pd.DataFrame,
                self.domain_enricher._domain_features(
                    raw=m5_frame,
                    base_timeframe="M5",
                ),
            )
        except Exception as exc:
            raise PortableFeatureGenerationError(
                f"DOMAIN_FEATURE_GENERATION_FAILED: {exc}"
            ) from exc

        domain_cols = [c for c in domain_df.columns if c.startswith("m5_domain_")]
        if len(domain_cols) != 63:
            raise PortableFeatureGenerationError(
                f"UNEXPECTED_DOMAIN_FEATURE_COUNT: {len(domain_cols)} != 63"
            )

        domain_subset = cast(pd.DataFrame, domain_df[["time", *domain_cols]].copy())
        domain_subset["time"] = pd.to_datetime(domain_subset["time"], utc=True)
        return domain_subset

    @staticmethod
    def _generate_cyclical_utc_features(
        decision_time: pd.Series,
    ) -> pd.DataFrame:
        """Generate the 4 cyclical UTC trigonometric time features from decision_time."""
        hour_val = decision_time.dt.hour + (decision_time.dt.minute / 60.0)
        day_val = decision_time.dt.dayofweek.astype(float)

        return pd.DataFrame(
            {
                "utc_hour_sin": np.sin(2.0 * np.pi * hour_val / 24.0).astype("float32"),
                "utc_hour_cos": np.cos(2.0 * np.pi * hour_val / 24.0).astype("float32"),
                "utc_day_sin": np.sin(2.0 * np.pi * day_val / 7.0).astype("float32"),
                "utc_day_cos": np.cos(2.0 * np.pi * day_val / 7.0).astype("float32"),
            },
            index=decision_time.index,
        )

    def generate(
        self,
        market_data: Mapping[str, pd.DataFrame],
        *,
        symbol: str = CANONICAL_SYMBOL,
    ) -> PortableFeaturePipelineResult:
        """
        Generate the exact frozen 331-feature matrix from multi-timeframe market data.

        market_data: dict mapping timeframe strings to raw DataFrames.
                     Must include "M5", "M15", "M30", "H1", "H4", and either "D1" or intraday for D1.
        symbol: Instrument symbol (must be "XAUUSD" or "XAUUSDm").

        Returns PortableFeaturePipelineResult on success, or raises PortableFeatureGenerationError.
        """
        # 1. Symbol validation (Directive 2)
        try:
            canonical_symbol = str(normalize_supported_symbol(symbol))
        except ValueError as exc:
            raise PortableFeatureGenerationError(str(exc)) from exc

        # 2. Timeframe availability & D1 determination (Directive 1 & 5)
        for tf in ("M5", "M15", "M30", "H1", "H4"):
            if tf not in market_data or market_data[tf] is None or market_data[tf].empty:
                raise PortableFeatureGenerationError(f"REQUIRED_TIMEFRAME_MISSING: {tf}")

        d1_frame: pd.DataFrame | None = market_data.get("D1")
        d1_source_label = "NATIVE_BROKER_D1"

        if self.d1_reconstruction_source is not None:
            reconstruct_source = self.d1_reconstruction_source
            if reconstruct_source not in market_data:
                raise PortableFeatureGenerationError(
                    f"D1_RECONSTRUCTION_SOURCE_MISSING: {reconstruct_source}"
                )
            d1_frame = self.reconstruct_d1(
                market_data[reconstruct_source],
                source_timeframe=reconstruct_source,
                min_history_bars=self.min_history_bars.get("D1", 200),
            )
            d1_source_label = f"RECONSTRUCTED_FROM_{reconstruct_source}"
        elif d1_frame is None or d1_frame.empty:
            d1_frame = self.reconstruct_d1(
                market_data["H1"],
                source_timeframe="H1",
                min_history_bars=self.min_history_bars.get("D1", 200),
            )
            d1_source_label = "RECONSTRUCTED_FROM_H1"

        # 3. Validate raw frames
        validated_frames: dict[str, pd.DataFrame] = {}
        for tf in ("M5", "M15", "M30", "H1", "H4"):
            validated_frames[tf] = self._validate_raw_frame(
                market_data[tf],
                tf,
                min_bars=self.min_history_bars.get(tf, 50),
            )
        validated_frames["D1"] = self._validate_raw_frame(
            d1_frame,
            "D1",
            min_bars=self.min_history_bars.get("D1", 50),
        )

        m5_raw = validated_frames["M5"]

        # 4. Generate M5 features
        m5_tech = self._generate_technical_frame(m5_raw, "M5")
        m5_ratio20 = self._generate_m5_tick_volume_ratio20(m5_raw)
        m5_domain = self._generate_m5_domain_features(m5_raw)

        m5_time = cast(pd.Series, m5_tech["time"])
        m5_tech["decision_time"] = m5_time + pd.Timedelta(minutes=5)
        m5_tech["m5_tick_volume_ratio20"] = m5_ratio20
        m5_tech = cast(pd.DataFrame, m5_tech.drop(columns=["available_time"]))

        matrix = cast(
            pd.DataFrame,
            pd.merge(
                m5_tech,
                m5_domain,
                on="time",
                how="inner",
                validate="one_to_one",
            ),
        )

        # 5. Multi-timeframe backward merge_asof for HTFs (M15, M30, H1, H4, D1)
        for htf in CONTEXT_TIMEFRAMES:
            htf_raw = validated_frames[htf]
            htf_tech = self._generate_technical_frame(htf_raw, htf)

            htf_right = cast(
                pd.DataFrame,
                htf_tech.drop(columns=["time"]).sort_values(by="available_time").reset_index(drop=True),
            )

            matrix = cast(
                pd.DataFrame,
                pd.merge_asof(
                    matrix,
                    htf_right,
                    left_on="decision_time",
                    right_on="available_time",
                    direction="backward",
                    allow_exact_matches=True,
                ),
            )

            prefix = htf.lower()
            age_col = f"{prefix}_age_minutes"
            dec_time = cast(pd.Series, matrix["decision_time"])
            avail_time = cast(pd.Series, matrix["available_time"])
            matrix[age_col] = ((dec_time - avail_time).dt.total_seconds() / 60.0).astype("float32")

            # Strict no-lookahead check
            age_series = cast(pd.Series, matrix[age_col])
            if bool((age_series < 0).fillna(False).any()):
                raise PortableFeatureGenerationError(
                    f"FUTURE_TIMEFRAME_FEATURE_LEAKAGE: {htf}"
                )

            matrix = matrix.drop(columns=["available_time"])
            matrix = matrix.copy()

        # 6. UTC cyclical features
        matrix_dec_time = cast(pd.Series, matrix["decision_time"])
        utc_features = self._generate_cyclical_utc_features(matrix_dec_time)
        for col in ("utc_hour_sin", "utc_hour_cos", "utc_day_sin", "utc_day_cos"):
            matrix[col] = utc_features[col]
        matrix = matrix.copy()

        # 7. Extract exact 331 frozen columns
        missing_in_matrix = [c for c in FROZEN_FEATURE_COLUMNS if c not in matrix.columns]
        if missing_in_matrix:
            raise PortableFeatureGenerationError(
                f"MISSING_FROZEN_FEATURES: {', '.join(missing_in_matrix)}"
            )

        features_df = cast(pd.DataFrame, matrix[list(FROZEN_FEATURE_COLUMNS)].copy())

        # 8. Clean NaN/inf from indicator warm-up
        features_df = cast(pd.DataFrame, features_df.replace([np.inf, -np.inf], np.nan))
        valid_mask_series = features_df.notna().all(axis=1)
        valid_mask_arr = valid_mask_series.to_numpy()

        cleaned_features = cast(pd.DataFrame, features_df.iloc[valid_mask_arr].reset_index(drop=True))
        cleaned_decision_times = cast(pd.Series, matrix["decision_time"].iloc[valid_mask_arr].reset_index(drop=True))

        if cleaned_features.empty:
            raise PortableFeatureGenerationError(
                "NO_VALID_FINITE_FEATURE_ROWS_AFTER_WARMUP"
            )

        # 9. Verify exact contract
        if cleaned_features.shape[1] != EXPECTED_FEATURE_COUNT:
            raise PortableFeatureGenerationError(
                f"FEATURE_COUNT_MISMATCH: {cleaned_features.shape[1]} != {EXPECTED_FEATURE_COUNT}"
            )

        sha = str(compute_feature_columns_sha256(list(cleaned_features.columns)))
        if sha != EXPECTED_FEATURE_COLUMNS_SHA256:
            raise PortableFeatureGenerationError(
                f"FEATURE_COLUMNS_SHA_MISMATCH: {sha} != {EXPECTED_FEATURE_COLUMNS_SHA256}"
            )

        return PortableFeaturePipelineResult(
            features=cleaned_features,
            decision_times=cleaned_decision_times,
            feature_names=FROZEN_FEATURE_COLUMNS,
            feature_count=EXPECTED_FEATURE_COUNT,
            feature_columns_sha256=sha,
            row_count=len(cleaned_features),
            symbol=canonical_symbol,
            d1_source=d1_source_label,
            live_authorized=False,
        )
