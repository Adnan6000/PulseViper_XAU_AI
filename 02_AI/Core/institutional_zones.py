"""
PulseViper XAU AI
Institutional Zones Engine

Purpose
-------
Deterministically detect institutional-style price zones from OHLCV data.

The engine identifies:

- Bullish demand / order-block style zones
- Bearish supply / order-block style zones

This engine is intentionally deterministic and dependency-light.

Important architecture note
----------------------------
Institutional zones are a market-structure / feature layer.

They do NOT make trading decisions by themselves.

Higher-level PulseViper components can consume these zones together
with FVG, mitigation, BOS, liquidity, displacement, regime and
confidence signals.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import math

import pandas as pd


# ============================================================================
# DATA MODEL
# ============================================================================


@dataclass(frozen=True)
class InstitutionalZone:
    """Immutable representation of an institutional price zone."""

    zone_id: int
    direction: str
    zone_type: str

    index: Any

    high: float
    low: float
    midpoint: float
    size: float

    candle_open: float
    candle_close: float
    candle_high: float
    candle_low: float

    body_ratio: float
    displacement_score: float

    strength: float
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Return a serializable dictionary representation."""
        return asdict(self)


# ============================================================================
# ENGINE
# ============================================================================


class InstitutionalZonesEngine:
    """
    Detect institutional-style price zones.

    Detection model
    ---------------

    Bullish zone:
        Opposite/down candle
        +
        subsequent bullish displacement
        +
        optional breakout confirmation

    Bearish zone:
        Opposite/up candle
        +
        subsequent bearish displacement
        +
        optional breakout confirmation

    The implementation does not claim to detect actual institutional
    orders. It detects price-action structures commonly used as
    institutional/order-block proxies.

    Architectural role
    ------------------
    This engine is an upstream deterministic feature generator.

    It should not:
        - open trades
        - calculate account risk
        - produce final BUY/SELL decisions
        - replace confidence/risk engines
    """

    REQUIRED_COLUMNS = (
        "open",
        "high",
        "low",
        "close",
    )

    OPTIONAL_COLUMNS = (
        "volume",
        "atr",
    )

    DEFAULT_CONFIG = {
        # A modest threshold is intentional.
        #
        # Institutional candles can contain meaningful wicks.
        # Displacement is the stronger confirmation signal.
        "min_body_ratio": 0.25,

        "min_displacement_score": 55.0,

        "min_zone_size": 0.0,

        "max_zone_size_atr": 3.0,

        "lookahead": 3,

        "min_strength": 0.0,

        "merge_overlapping": True,

        "max_zones": 100,
    }

    OUTPUT_COLUMNS = (
        "zone_id",
        "direction",
        "zone_type",
        "index",
        "high",
        "low",
        "midpoint",
        "size",
        "candle_open",
        "candle_close",
        "candle_high",
        "candle_low",
        "body_ratio",
        "displacement_score",
        "strength",
        "active",
    )

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.config = self.DEFAULT_CONFIG.copy()

        if config:
            self.config.update(config)

        self._validate_config()

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def detect(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Detect institutional zones.

        Parameters
        ----------
        data:
            DataFrame containing OHLC data.

        Returns
        -------
        pd.DataFrame
            One row per detected zone.
        """

        df = self._prepare_dataframe(data)

        if df.empty:
            return self._empty_result()

        zones: List[InstitutionalZone] = []

        for position in range(len(df) - 1):
            zone = self._detect_at_position(
                df,
                position,
            )

            if zone is not None:
                zones.append(zone)

        if not zones:
            return self._empty_result()

        if self.config["merge_overlapping"]:
            zones = self._merge_overlapping_zones(zones)

        zones.sort(
            key=lambda zone: (
                -zone.strength,
                zone.zone_id,
            )
        )

        max_zones = int(
            self.config["max_zones"]
        )

        if max_zones > 0:
            zones = zones[:max_zones]

        return pd.DataFrame(
            [zone.to_dict() for zone in zones],
            columns=self.OUTPUT_COLUMNS,
        )

    def generate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        """Compatibility alias for the wider PulseViper pipeline."""
        return self.detect(data)

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def _validate_config(self) -> None:
        min_body_ratio = float(
            self.config["min_body_ratio"]
        )

        min_displacement_score = float(
            self.config["min_displacement_score"]
        )

        min_zone_size = float(
            self.config["min_zone_size"]
        )

        max_zone_size_atr = float(
            self.config["max_zone_size_atr"]
        )

        lookahead = int(
            self.config["lookahead"]
        )

        min_strength = float(
            self.config["min_strength"]
        )

        if not 0.0 <= min_body_ratio <= 1.0:
            raise ValueError(
                "min_body_ratio must be between 0 and 1."
            )

        if min_displacement_score < 0.0:
            raise ValueError(
                "min_displacement_score cannot be negative."
            )

        if min_zone_size < 0.0:
            raise ValueError(
                "min_zone_size cannot be negative."
            )

        if max_zone_size_atr <= 0.0:
            raise ValueError(
                "max_zone_size_atr must be greater than zero."
            )

        if lookahead < 1:
            raise ValueError(
                "lookahead must be at least 1."
            )

        if min_strength < 0.0:
            raise ValueError(
                "min_strength cannot be negative."
            )

    @classmethod
    def _ensure_columns(
        cls,
        data: pd.DataFrame,
    ) -> None:
        if not isinstance(data, pd.DataFrame):
            raise TypeError(
                "data must be a pandas DataFrame."
            )

        missing = [
            column
            for column in cls.REQUIRED_COLUMNS
            if column not in data.columns
        ]

        if missing:
            raise ValueError(
                f"Missing required OHLC columns: {missing}"
            )

    # ========================================================================
    # DATA PREPARATION
    # ========================================================================

    def _prepare_dataframe(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        self._ensure_columns(data)

        df = data.copy()

        for column in self.REQUIRED_COLUMNS:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

        df = df.dropna(
            subset=list(self.REQUIRED_COLUMNS)
        )

        if df.empty:
            return df

        # --------------------------------------------------------------
        # Validate OHLC relationships.
        # --------------------------------------------------------------

        valid_ohlc = (
            (df["high"] >= df["low"])
            & (df["high"] >= df["open"])
            & (df["high"] >= df["close"])
            & (df["low"] <= df["open"])
            & (df["low"] <= df["close"])
        )

        df = df.loc[valid_ohlc].copy()

        if df.empty:
            return df

        # --------------------------------------------------------------
        # ATR
        # --------------------------------------------------------------

        if "atr" in df.columns:
            df["atr"] = pd.to_numeric(
                df["atr"],
                errors="coerce",
            )

        if "atr" not in df.columns:
            df["atr"] = self._calculate_atr(df)

        df["atr"] = df["atr"].replace(
            [math.inf, -math.inf],
            math.nan,
        )

        fallback_atr = (
            df["high"] - df["low"]
        ).rolling(
            window=14,
            min_periods=1,
        ).mean()

        df["atr"] = df["atr"].fillna(
            fallback_atr
        )

        df["atr"] = df["atr"].replace(
            0.0,
            math.nan,
        )

        return df

    @staticmethod
    def _calculate_atr(
        df: pd.DataFrame,
        period: int = 14,
    ) -> pd.Series:
        previous_close = df["close"].shift(1)

        true_range = pd.concat(
            [
                df["high"] - df["low"],
                (
                    df["high"] - previous_close
                ).abs(),
                (
                    df["low"] - previous_close
                ).abs(),
            ],
            axis=1,
        ).max(axis=1)

        return true_range.rolling(
            window=period,
            min_periods=1,
        ).mean()

    # ========================================================================
    # DETECTION
    # ========================================================================

    def _detect_at_position(
        self,
        df: pd.DataFrame,
        position: int,
    ) -> Optional[InstitutionalZone]:

        candle = df.iloc[position]

        candle_open = self._safe_float(
            candle["open"]
        )

        candle_high = self._safe_float(
            candle["high"]
        )

        candle_low = self._safe_float(
            candle["low"]
        )

        candle_close = self._safe_float(
            candle["close"]
        )

        atr = self._safe_float(
            candle["atr"]
        )

        if any(
            value is None
            for value in (
                candle_open,
                candle_high,
                candle_low,
                candle_close,
            )
        ):
            return None

        # Type narrowing for static analyzers.
        assert candle_open is not None
        assert candle_high is not None
        assert candle_low is not None
        assert candle_close is not None

        if candle_high <= candle_low:
            return None

        body = abs(
            candle_close - candle_open
        )

        range_size = (
            candle_high - candle_low
        )

        if range_size <= 0.0:
            return None

        body_ratio = body / range_size

        # --------------------------------------------------------------
        # Body ratio is a candidate filter, not the primary confirmation.
        #
        # A valid order-block-style candle may have a meaningful wick.
        # Therefore 0.25 is used as the default threshold.
        # --------------------------------------------------------------

        if body_ratio < float(
            self.config["min_body_ratio"]
        ):
            return None

        lookahead = int(
            self.config["lookahead"]
        )

        future_end = min(
            position + 1 + lookahead,
            len(df),
        )

        future = df.iloc[
            position + 1:future_end
        ]

        if future.empty:
            return None

        # --------------------------------------------------------------
        # Bullish displacement
        # --------------------------------------------------------------

        if candle_close < candle_open:

            bullish_displacement = (
                self._bullish_displacement(
                    future=future,
                    reference_high=candle_high,
                    reference_close=candle_close,
                    atr=atr,
                )
            )

            if (
                bullish_displacement is not None
                and bullish_displacement
                >= float(
                    self.config[
                        "min_displacement_score"
                    ]
                )
            ):
                return self._build_zone(
                    df=df,
                    position=position,
                    direction="BULLISH",
                    zone_type="DEMAND",
                    high=candle_open,
                    low=candle_low,
                    body_ratio=body_ratio,
                    displacement_score=(
                        bullish_displacement
                    ),
                )

        # --------------------------------------------------------------
        # Bearish displacement
        # --------------------------------------------------------------

        if candle_close > candle_open:

            bearish_displacement = (
                self._bearish_displacement(
                    future=future,
                    reference_low=candle_low,
                    reference_close=candle_close,
                    atr=atr,
                )
            )

            if (
                bearish_displacement is not None
                and bearish_displacement
                >= float(
                    self.config[
                        "min_displacement_score"
                    ]
                )
            ):
                return self._build_zone(
                    df=df,
                    position=position,
                    direction="BEARISH",
                    zone_type="SUPPLY",
                    high=candle_high,
                    low=candle_open,
                    body_ratio=body_ratio,
                    displacement_score=(
                        bearish_displacement
                    ),
                )

        return None

    # ========================================================================
    # DISPLACEMENT
    # ========================================================================

    @classmethod
    def _bullish_displacement(
        cls,
        future: pd.DataFrame,
        reference_high: float,
        reference_close: float,
        atr: Optional[float],
    ) -> Optional[float]:

        max_close = cls._safe_float(
            future["close"].max()
        )

        max_high = cls._safe_float(
            future["high"].max()
        )

        if (
            max_close is None
            or max_high is None
        ):
            return None

        move = (
            max_close - reference_close
        )

        if move <= 0.0:
            return 0.0

        breakout = (
            100.0
            if max_high > reference_high
            else 0.0
        )

        atr_component = (
            cls._atr_displacement_score(
                move,
                atr,
            )
        )

        return min(
            100.0,
            atr_component * 0.70
            + breakout * 0.30,
        )

    @classmethod
    def _bearish_displacement(
        cls,
        future: pd.DataFrame,
        reference_low: float,
        reference_close: float,
        atr: Optional[float],
    ) -> Optional[float]:

        min_close = cls._safe_float(
            future["close"].min()
        )

        min_low = cls._safe_float(
            future["low"].min()
        )

        if (
            min_close is None
            or min_low is None
        ):
            return None

        move = (
            reference_close - min_close
        )

        if move <= 0.0:
            return 0.0

        breakout = (
            100.0
            if min_low < reference_low
            else 0.0
        )

        atr_component = (
            cls._atr_displacement_score(
                move,
                atr,
            )
        )

        return min(
            100.0,
            atr_component * 0.70
            + breakout * 0.30,
        )

    @staticmethod
    def _atr_displacement_score(
        move: float,
        atr: Optional[float],
    ) -> float:

        if atr is None or atr <= 0.0:
            return min(
                100.0,
                max(
                    0.0,
                    move * 100.0,
                ),
            )

        ratio = move / atr

        return min(
            100.0,
            max(
                0.0,
                ratio * 50.0,
            ),
        )

    # ========================================================================
    # ZONE CONSTRUCTION
    # ========================================================================

    def _build_zone(
        self,
        df: pd.DataFrame,
        position: int,
        direction: str,
        zone_type: str,
        high: float,
        low: float,
        body_ratio: float,
        displacement_score: float,
    ) -> Optional[InstitutionalZone]:

        if not math.isfinite(high):
            return None

        if not math.isfinite(low):
            return None

        if high <= low:
            return None

        size = high - low

        min_size = float(
            self.config["min_zone_size"]
        )

        if size < min_size:
            return None

        atr = self._safe_float(
            df.iloc[position]["atr"]
        )

        max_zone_size_atr = float(
            self.config["max_zone_size_atr"]
        )

        if (
            atr is not None
            and atr > 0.0
            and size / atr > max_zone_size_atr
        ):
            return None

        strength = self._calculate_strength(
            body_ratio=body_ratio,
            displacement_score=displacement_score,
            zone_size=size,
            atr=atr,
        )

        if strength < float(
            self.config["min_strength"]
        ):
            return None

        candle = df.iloc[position]

        candle_open = self._safe_float(
            candle["open"]
        )

        candle_close = self._safe_float(
            candle["close"]
        )

        candle_high = self._safe_float(
            candle["high"]
        )

        candle_low = self._safe_float(
            candle["low"]
        )

        if any(
            value is None
            for value in (
                candle_open,
                candle_close,
                candle_high,
                candle_low,
            )
        ):
            return None

        assert candle_open is not None
        assert candle_close is not None
        assert candle_high is not None
        assert candle_low is not None

        return InstitutionalZone(
            zone_id=int(position),
            direction=direction,
            zone_type=zone_type,
            index=df.index[position],
            high=float(high),
            low=float(low),
            midpoint=float(
                (high + low) / 2.0
            ),
            size=float(size),
            candle_open=float(
                candle_open
            ),
            candle_close=float(
                candle_close
            ),
            candle_high=float(
                candle_high
            ),
            candle_low=float(
                candle_low
            ),
            body_ratio=float(
                body_ratio
            ),
            displacement_score=float(
                displacement_score
            ),
            strength=float(strength),
            active=True,
        )

    @staticmethod
    def _calculate_strength(
        body_ratio: float,
        displacement_score: float,
        zone_size: float,
        atr: Optional[float],
    ) -> float:

        body_component = min(
            100.0,
            max(
                0.0,
                body_ratio * 100.0,
            ),
        )

        if atr is not None and atr > 0.0:
            size_ratio = zone_size / atr

            size_component = max(
                0.0,
                100.0 - size_ratio * 25.0,
            )
        else:
            size_component = 50.0

        score = (
            body_component * 0.30
            + displacement_score * 0.55
            + size_component * 0.15
        )

        return min(
            100.0,
            max(
                0.0,
                score,
            ),
        )

    # ========================================================================
    # ZONE MERGING
    # ========================================================================

    def _merge_overlapping_zones(
        self,
        zones: List[InstitutionalZone],
    ) -> List[InstitutionalZone]:

        if len(zones) < 2:
            return zones

        ordered = sorted(
            zones,
            key=lambda zone: (
                zone.direction,
                zone.low,
                zone.high,
            ),
        )

        merged: List[
            InstitutionalZone
        ] = []

        for zone in ordered:

            if not merged:
                merged.append(zone)
                continue

            previous = merged[-1]

            if (
                previous.direction
                == zone.direction
                and self._zones_overlap(
                    previous,
                    zone,
                )
            ):
                merged[-1] = (
                    self._merge_two_zones(
                        previous,
                        zone,
                    )
                )
            else:
                merged.append(zone)

        return merged

    @staticmethod
    def _zones_overlap(
        first: InstitutionalZone,
        second: InstitutionalZone,
    ) -> bool:

        return (
            first.low <= second.high
            and second.low <= first.high
        )

    @staticmethod
    def _merge_two_zones(
        first: InstitutionalZone,
        second: InstitutionalZone,
    ) -> InstitutionalZone:

        high = max(
            first.high,
            second.high,
        )

        low = min(
            first.low,
            second.low,
        )

        return InstitutionalZone(
            zone_id=min(
                first.zone_id,
                second.zone_id,
            ),
            direction=first.direction,
            zone_type=first.zone_type,
            index=first.index,
            high=float(high),
            low=float(low),
            midpoint=float(
                (high + low) / 2.0
            ),
            size=float(
                high - low
            ),
            candle_open=first.candle_open,
            candle_close=first.candle_close,
            candle_high=max(
                first.candle_high,
                second.candle_high,
            ),
            candle_low=min(
                first.candle_low,
                second.candle_low,
            ),
            body_ratio=max(
                first.body_ratio,
                second.body_ratio,
            ),
            displacement_score=max(
                first.displacement_score,
                second.displacement_score,
            ),
            strength=max(
                first.strength,
                second.strength,
            ),
            active=(
                first.active
                and second.active
            ),
        )

    # ========================================================================
    # HELPERS
    # ========================================================================

    @staticmethod
    def _safe_float(
        value: Any,
    ) -> Optional[float]:

        try:
            if value is None:
                return None

            number = float(value)

            if not math.isfinite(number):
                return None

            return number

        except (
            TypeError,
            ValueError,
        ):
            return None

    @classmethod
    def _empty_result(
        cls,
    ) -> pd.DataFrame:

        return pd.DataFrame(
            columns=list(
                cls.OUTPUT_COLUMNS
            )
        )


# ============================================================================
# MODULE-LEVEL SINGLETON
# ============================================================================

institutional_zones = (
    InstitutionalZonesEngine()
)


__all__ = [
    "InstitutionalZone",
    "InstitutionalZonesEngine",
    "institutional_zones",
]