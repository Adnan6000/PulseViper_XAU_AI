"""
===============================================================================
Module      : training_feature_enricher.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Causal Gold Domain Feature Enrichment
===============================================================================

Builds XAUUSD_MTF_TRAINING_V3 from the already validated V2 matrix.

V2 labels remain unchanged.

Adds causal base-timeframe Gold context from existing PulseViper engines:

- Market regime
- Adaptive market structure
- BOS
- FVG creation events
- Causal institutional-zone confirmation events

No future data is used for features.
No MT5 calls.
No trading.
No live authorization.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import tempfile

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
)

CANONICAL_ROOT = (
    ROOT_DIR
    /
    "01_Data"
    /
    "Canonical"
)


matrix_module: Any = importlib.import_module(
    "02_AI.Dataset.training_matrix_builder"
)

structure_module: Any = importlib.import_module(
    "02_AI.Core.market_structure"
)

bos_module: Any = importlib.import_module(
    "02_AI.Core.bos_engine"
)

regime_module: Any = importlib.import_module(
    "02_AI.Core.market_regime"
)

fvg_module: Any = importlib.import_module(
    "02_AI.Core.fvg_engine"
)

zone_module: Any = importlib.import_module(
    "02_AI.Core.institutional_zones"
)


TrainingMatrixBuilder: Any = (
    matrix_module.TrainingMatrixBuilder
)

MarketStructure: Any = (
    structure_module.MarketStructure
)

BOSEngine: Any = (
    bos_module.BOSEngine
)

MarketRegimeEngine: Any = (
    regime_module.MarketRegimeEngine
)

FVGEngine: Any = (
    fvg_module.FVGEngine
)

InstitutionalZonesEngine: Any = (
    zone_module.InstitutionalZonesEngine
)


class TrainingFeatureEnrichmentError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class TrainingFeatureEnrichmentResult:

    dataset_id: str
    dataset_path: Path
    manifest_path: Path

    dataset_sha256: str
    manifest_sha256: str

    row_count: int
    feature_count: int
    added_feature_count: int

    class_distribution: dict[str, int]

    learning_scope_fingerprint: str
    training_contract_version: str

    live_authorized: bool = False


class TrainingFeatureEnricher:

    VERSION = "1.0"

    SOURCE_CONTRACT = (
        "XAUUSD_MTF_TRAINING_V2"
    )

    TARGET_CONTRACT = (
        "XAUUSD_MTF_TRAINING_V3"
    )

    DOMAIN_FEATURE_VERSION = (
        "XAUUSD_CAUSAL_DOMAIN_FEATURES_V1"
    )

    EVENT_AGE_CAP = 500

    def __init__(
        self,
        *,
        canonical_root: Path | None = None,
    ) -> None:

        self.canonical_root = (
            Path(canonical_root)
            if canonical_root is not None
            else CANONICAL_ROOT
        )

    # =========================================================================
    # Hash helpers
    # =========================================================================

    @staticmethod
    def _sha256_file(
        path: Path,
    ) -> str:

        digest = hashlib.sha256()

        with path.open("rb") as handle:

            while True:

                chunk = handle.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                digest.update(chunk)

        return digest.hexdigest()

    @staticmethod
    def _sha256_bytes(
        payload: bytes,
    ) -> str:

        return hashlib.sha256(
            payload
        ).hexdigest()

    @staticmethod
    def _canonical_json_bytes(
        document: Mapping[str, Any],
    ) -> bytes:

        return (
            json.dumps(
                document,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
            +
            "\n"
        ).encode("utf-8")

    # =========================================================================
    # Context
    # =========================================================================

    @staticmethod
    def _validate_context(
        context: Any,
    ) -> None:

        if context is None:

            raise TrainingFeatureEnrichmentError(
                "INSTRUMENT_CONTEXT_REQUIRED"
            )

        if bool(
            getattr(
                context,
                "live_authorized",
                False,
            )
        ):

            raise TrainingFeatureEnrichmentError(
                "LIVE_AUTHORIZED_CONTEXT_REJECTED"
            )

        if (
            str(
                getattr(
                    context,
                    "canonical_symbol",
                    "",
                )
            )
            !=
            "XAUUSD"
        ):

            raise TrainingFeatureEnrichmentError(
                "CANONICAL_SYMBOL_MISMATCH"
            )

    # =========================================================================
    # V2 discovery
    # =========================================================================

    def _discover_v2(
        self,
        *,
        context: Any,
    ) -> tuple[
        Path,
        Path,
        dict[str, Any],
        str,
        str,
    ]:

        learning_fingerprint = (
            TrainingMatrixBuilder
            .learning_scope_fingerprint(
                context
            )
        )

        directory = (
            self.canonical_root
            /
            "Instruments"
            /
            "XAUUSD"
            /
            "learning"
            /
            (
                "scope_"
                +
                learning_fingerprint
            )
            /
            "training"
            /
            self.SOURCE_CONTRACT
        )

        if not directory.is_dir():

            raise TrainingFeatureEnrichmentError(
                "V2_TRAINING_DIRECTORY_MISSING"
            )

        candidates: list[
            tuple[
                pd.Timestamp,
                str,
                Path,
                dict[str, Any],
            ]
        ] = []

        for manifest_path in directory.glob(
            "*.manifest.json"
        ):

            manifest = json.loads(
                manifest_path.read_text(
                    encoding="utf-8"
                )
            )

            if (
                str(
                    manifest.get(
                        "training_contract_version",
                        "",
                    )
                )
                !=
                self.SOURCE_CONTRACT
            ):

                continue

            if (
                str(
                    manifest.get(
                        "learning_scope_fingerprint",
                        "",
                    )
                )
                !=
                learning_fingerprint
            ):

                continue

            if bool(
                manifest.get(
                    "live_authorized",
                    False,
                )
            ):

                raise TrainingFeatureEnrichmentError(
                    "LIVE_AUTHORIZED_V2_REJECTED"
                )

            base_tf = str(
                manifest.get(
                    "base_timeframe",
                    "",
                )
            ).upper()

            snapshots = manifest.get(
                "source_historical_snapshots",
                {},
            )

            base_snapshot = (
                snapshots.get(
                    base_tf,
                    {},
                )
                if isinstance(
                    snapshots,
                    Mapping,
                )
                else
                {}
            )

            raw_end = (
                base_snapshot.get(
                    "end_time",
                    "",
                )
                if isinstance(
                    base_snapshot,
                    Mapping,
                )
                else
                ""
            )

            try:

                end_time = pd.to_datetime(
                    raw_end,
                    utc=True,
                )

            except Exception:

                end_time = pd.Timestamp(
                    "1970-01-01",
                    tz="UTC",
                )

            candidates.append(
                (
                    end_time,
                    str(
                        manifest.get(
                            "dataset_id",
                            "",
                        )
                    ),
                    manifest_path,
                    manifest,
                )
            )

        if not candidates:

            raise TrainingFeatureEnrichmentError(
                "MATCHING_V2_MANIFEST_MISSING"
            )

        candidates.sort(
            key=lambda item: (
                item[0],
                item[1],
            )
        )

        (
            _end,
            _id,
            manifest_path,
            manifest,
        ) = candidates[-1]

        dataset_filename = str(
            manifest.get(
                "dataset_filename",
                "",
            )
        ).strip()

        dataset_path = (
            manifest_path.parent
            /
            dataset_filename
        )

        if not dataset_path.is_file():

            raise TrainingFeatureEnrichmentError(
                "V2_DATASET_MISSING"
            )

        expected_hash = str(
            manifest.get(
                "dataset_sha256",
                "",
            )
        )

        actual_hash = (
            self._sha256_file(
                dataset_path
            )
        )

        if (
            not expected_hash
            or
            actual_hash
            !=
            expected_hash
        ):

            raise TrainingFeatureEnrichmentError(
                "V2_DATASET_HASH_MISMATCH"
            )

        return (
            dataset_path,
            manifest_path,
            manifest,
            actual_hash,
            learning_fingerprint,
        )

    # =========================================================================
    # Numeric helpers
    # =========================================================================

    @staticmethod
    def _numeric(
        frame: pd.DataFrame,
        column: str,
    ) -> np.ndarray:

        if column not in frame.columns:

            return np.zeros(
                len(frame),
                dtype=np.float64,
            )

        return (
            pd.to_numeric(
                frame[column],
                errors="coerce",
            )
            .to_numpy(
                dtype=np.float64
            )
        )

    @staticmethod
    def _code(
        series: pd.Series,
        mapping: Mapping[str, float],
    ) -> np.ndarray:

        text = (
            series
            .astype(str)
            .str.upper()
        )

        return (
            text
            .map(mapping)
            .fillna(0.0)
            .to_numpy(
                dtype=np.float64
            )
        )

    @classmethod
    def _bars_since(
        cls,
        flags: np.ndarray,
    ) -> np.ndarray:

        flags = np.asarray(
            flags,
            dtype=bool,
        )

        output = np.full(
            len(flags),
            float(
                cls.EVENT_AGE_CAP
            ),
            dtype=np.float64,
        )

        last = -1

        for index in range(
            len(flags)
        ):

            if flags[index]:

                last = index

            if last >= 0:

                output[index] = float(
                    min(
                        cls.EVENT_AGE_CAP,
                        index - last,
                    )
                )

        return output

    @staticmethod
    def _last_event_value(
        *,
        values: np.ndarray,
        flags: np.ndarray,
        default: float = 0.0,
    ) -> np.ndarray:

        series = pd.Series(
            np.where(
                flags,
                values,
                np.nan,
            )
        )

        return (
            series
            .ffill()
            .fillna(default)
            .to_numpy(
                dtype=np.float64
            )
        )

    @staticmethod
    def _direction_code_scalar(
        value: Any,
    ) -> float:

        text = str(
            value
        ).strip().upper()

        if text in {
            "BULLISH",
            "BUY",
            "DEMAND",
            "LONG",
        }:

            return 1.0

        if text in {
            "BEARISH",
            "SELL",
            "SUPPLY",
            "SHORT",
        }:

            return -1.0

        return 0.0

    # =========================================================================
    # Domain feature generation
    # =========================================================================

    def _domain_features(
        self,
        *,
        raw: pd.DataFrame,
        base_timeframe: str,
    ) -> pd.DataFrame:

        raw = raw.copy()

        raw["time"] = pd.to_datetime(
            raw["time"],
            utc=True,
            errors="raise",
        )

        # ---------------------------------------------------------------------
        # Existing causal PulseViper engines
        # ---------------------------------------------------------------------

        structure = (
            MarketStructure()
            .generate(
                raw
            )
        )

        regime = (
            MarketRegimeEngine()
            .generate(
                structure
            )
        )

        bos = (
            BOSEngine()
            .generate(
                structure,
                reset_memory=True,
            )
        )

        fvg = (
            FVGEngine()
            .generate(
                structure
            )
        )

        zones = (
            InstitutionalZonesEngine()
            .generate_causal(
                structure
            )
        )

        count = len(
            raw
        )

        prefix = (
            base_timeframe.lower()
            +
            "_domain_"
        )

        atr = self._numeric(
            structure,
            "atr",
        )

        close = self._numeric(
            structure,
            "close",
        )

        valid_atr = (
            np.isfinite(atr)
            &
            (atr > 0.0)
        )

        # =====================================================================
        # Regime
        # =====================================================================

        regime_trend_code = self._code(
            regime["regime_trend"],
            {
                "BULLISH": 1.0,
                "RANGE": 0.0,
                "BEARISH": -1.0,
            },
        )

        regime_volatility_code = self._code(
            regime[
                "regime_volatility"
            ],
            {
                "LOW": -1.0,
                "NORMAL": 0.0,
                "HIGH": 1.0,
            },
        )

        # =====================================================================
        # Structure
        # =====================================================================

        structure_bias_code = self._code(
            structure[
                "structure_bias"
            ],
            {
                "BULLISH": 1.0,
                "NEUTRAL": 0.0,
                "BEARISH": -1.0,
            },
        )

        swing_direction_code = self._code(
            structure[
                "swing_type"
            ],
            {
                "HIGH": 1.0,
                "LOW": -1.0,
            },
        )

        swing_scale_code = self._code(
            structure[
                "swing_scale"
            ],
            {
                "MICRO": 1.0,
                "INTERNAL": 2.0,
                "MAJOR": 3.0,
            },
        )

        swing_event = (
            self._numeric(
                structure,
                "swing_id",
            )
            >
            0.0
        )

        last_high = self._numeric(
            structure,
            "last_swing_high",
        )

        last_low = self._numeric(
            structure,
            "last_swing_low",
        )

        last_major_high = self._numeric(
            structure,
            "last_major_high",
        )

        last_major_low = self._numeric(
            structure,
            "last_major_low",
        )

        last_high_known = np.isfinite(
            last_high
        )

        last_low_known = np.isfinite(
            last_low
        )

        major_high_known = np.isfinite(
            last_major_high
        )

        major_low_known = np.isfinite(
            last_major_low
        )

        dist_last_high = np.zeros(
            count,
            dtype=np.float64,
        )

        dist_last_low = np.zeros(
            count,
            dtype=np.float64,
        )

        dist_major_high = np.zeros(
            count,
            dtype=np.float64,
        )

        dist_major_low = np.zeros(
            count,
            dtype=np.float64,
        )

        mask = (
            valid_atr
            &
            last_high_known
        )

        dist_last_high[mask] = (
            (
                last_high[mask]
                -
                close[mask]
            )
            /
            atr[mask]
        )

        mask = (
            valid_atr
            &
            last_low_known
        )

        dist_last_low[mask] = (
            (
                close[mask]
                -
                last_low[mask]
            )
            /
            atr[mask]
        )

        mask = (
            valid_atr
            &
            major_high_known
        )

        dist_major_high[mask] = (
            (
                last_major_high[mask]
                -
                close[mask]
            )
            /
            atr[mask]
        )

        mask = (
            valid_atr
            &
            major_low_known
        )

        dist_major_low[mask] = (
            (
                close[mask]
                -
                last_major_low[mask]
            )
            /
            atr[mask]
        )

        dist_last_high = np.clip(
            dist_last_high,
            -20.0,
            20.0,
        )

        dist_last_low = np.clip(
            dist_last_low,
            -20.0,
            20.0,
        )

        dist_major_high = np.clip(
            dist_major_high,
            -30.0,
            30.0,
        )

        dist_major_low = np.clip(
            dist_major_low,
            -30.0,
            30.0,
        )

        range_position = np.zeros(
            count,
            dtype=np.float64,
        )

        structure_range = (
            last_high
            -
            last_low
        )

        mask = (
            last_high_known
            &
            last_low_known
            &
            np.isfinite(
                structure_range
            )
            &
            (
                structure_range
                >
                0.0
            )
        )

        range_position[mask] = (
            (
                close[mask]
                -
                last_low[mask]
            )
            /
            structure_range[mask]
        )

        range_position = np.clip(
            range_position,
            -2.0,
            3.0,
        )

        # =====================================================================
        # BOS
        # =====================================================================

        bullish_bos = (
            self._numeric(
                bos,
                "bullish_bos",
            )
            >
            0.0
        )

        bearish_bos = (
            self._numeric(
                bos,
                "bearish_bos",
            )
            >
            0.0
        )

        bos_event = (
            bullish_bos
            |
            bearish_bos
        )

        bos_direction = (
            bullish_bos.astype(
                np.float64
            )
            -
            bearish_bos.astype(
                np.float64
            )
        )

        last_bos_direction = (
            self._last_event_value(
                values=bos_direction,
                flags=bos_event,
            )
        )

        bos_context_text = (
            bos[
                "bos_context"
            ]
            .astype(str)
            .str.upper()
        )

        # =====================================================================
        # FVG
        # =====================================================================

        bullish_fvg = (
            self._numeric(
                fvg,
                "bullish_fvg",
            )
            >
            0.0
        )

        bearish_fvg = (
            self._numeric(
                fvg,
                "bearish_fvg",
            )
            >
            0.0
        )

        fvg_event = (
            bullish_fvg
            |
            bearish_fvg
        )

        fvg_direction = (
            bullish_fvg.astype(
                np.float64
            )
            -
            bearish_fvg.astype(
                np.float64
            )
        )

        fvg_ratio = self._numeric(
            fvg,
            "fvg_atr_ratio",
        )

        last_fvg_direction = (
            self._last_event_value(
                values=fvg_direction,
                flags=fvg_event,
            )
        )

        last_fvg_ratio = (
            self._last_event_value(
                values=fvg_ratio,
                flags=fvg_event,
            )
        )

        # =====================================================================
        # Institutional-zone causal events
        # =====================================================================

        iz_event = np.zeros(
            count,
            dtype=bool,
        )

        iz_bull = np.zeros(
            count,
            dtype=bool,
        )

        iz_bear = np.zeros(
            count,
            dtype=bool,
        )

        iz_direction = np.zeros(
            count,
            dtype=np.float64,
        )

        iz_strength = np.zeros(
            count,
            dtype=np.float64,
        )

        iz_displacement = np.zeros(
            count,
            dtype=np.float64,
        )

        iz_body_ratio = np.zeros(
            count,
            dtype=np.float64,
        )

        iz_size_atr = np.zeros(
            count,
            dtype=np.float64,
        )

        iz_delay = np.zeros(
            count,
            dtype=np.float64,
        )

        best_strength = np.full(
            count,
            -np.inf,
            dtype=np.float64,
        )

        if not zones.empty:

            for event in zones.to_dict(
                orient="records"
            ):

                try:

                    position = int(
                        event[
                            "iz_confirmation_position"
                        ]
                    )

                except Exception:

                    continue

                if (
                    position < 0
                    or
                    position >= count
                ):

                    continue

                direction = (
                    self._direction_code_scalar(
                        event.get(
                            "iz_direction",
                            "",
                        )
                    )
                )

                if direction > 0:

                    iz_bull[
                        position
                    ] = True

                elif direction < 0:

                    iz_bear[
                        position
                    ] = True

                candidate_strength = float(
                    event.get(
                        "iz_strength",
                        0.0,
                    )
                    or
                    0.0
                )

                iz_event[
                    position
                ] = True

                # Keep strongest event if several confirm on same candle.
                if (
                    candidate_strength
                    <
                    best_strength[
                        position
                    ]
                ):

                    continue

                best_strength[
                    position
                ] = (
                    candidate_strength
                )

                iz_direction[
                    position
                ] = direction

                iz_strength[
                    position
                ] = candidate_strength

                iz_displacement[
                    position
                ] = float(
                    event.get(
                        "iz_displacement_score",
                        0.0,
                    )
                    or
                    0.0
                )

                iz_body_ratio[
                    position
                ] = float(
                    event.get(
                        "iz_body_ratio",
                        0.0,
                    )
                    or
                    0.0
                )

                zone_size = float(
                    event.get(
                        "iz_zone_size",
                        0.0,
                    )
                    or
                    0.0
                )

                if valid_atr[
                    position
                ]:

                    iz_size_atr[
                        position
                    ] = (
                        zone_size
                        /
                        atr[
                            position
                        ]
                    )

                iz_delay[
                    position
                ] = float(
                    event.get(
                        "iz_confirmation_delay_bars",
                        0.0,
                    )
                    or
                    0.0
                )

        last_iz_direction = (
            self._last_event_value(
                values=iz_direction,
                flags=iz_event,
            )
        )

        last_iz_strength = (
            self._last_event_value(
                values=iz_strength,
                flags=iz_event,
            )
        )

        # =====================================================================
        # Build all columns once — avoids pandas fragmentation
        # =====================================================================

        values: dict[
            str,
            Any,
        ] = {
            "time": raw["time"],

            # Regime
            prefix + "regime_ready":
                self._numeric(
                    regime,
                    "regime_ready",
                ),

            prefix + "regime_atr_percentile":
                self._numeric(
                    regime,
                    "regime_atr_percentile",
                ),

            prefix + "regime_range_atr":
                self._numeric(
                    regime,
                    "regime_range_atr",
                ),

            prefix + "regime_efficiency":
                self._numeric(
                    regime,
                    "regime_efficiency",
                ),

            prefix + "regime_directional_move_atr":
                self._numeric(
                    regime,
                    "regime_directional_move_atr",
                ),

            prefix + "regime_trend_strength":
                self._numeric(
                    regime,
                    "regime_trend_strength",
                ),

            prefix + "regime_trend_code":
                regime_trend_code,

            prefix + "regime_volatility_code":
                regime_volatility_code,

            # Structure
            prefix + "hh":
                self._numeric(
                    structure,
                    "HH",
                ),

            prefix + "hl":
                self._numeric(
                    structure,
                    "HL",
                ),

            prefix + "lh":
                self._numeric(
                    structure,
                    "LH",
                ),

            prefix + "ll":
                self._numeric(
                    structure,
                    "LL",
                ),

            prefix + "micro_high":
                self._numeric(
                    structure,
                    "micro_high",
                ),

            prefix + "micro_low":
                self._numeric(
                    structure,
                    "micro_low",
                ),

            prefix + "internal_high":
                self._numeric(
                    structure,
                    "internal_high",
                ),

            prefix + "internal_low":
                self._numeric(
                    structure,
                    "internal_low",
                ),

            prefix + "major_high":
                self._numeric(
                    structure,
                    "major_high",
                ),

            prefix + "major_low":
                self._numeric(
                    structure,
                    "major_low",
                ),

            prefix + "swing_score":
                self._numeric(
                    structure,
                    "swing_score",
                ),

            prefix + "swing_excursion_atr":
                self._numeric(
                    structure,
                    "swing_excursion_atr",
                ),

            prefix + "swing_reversal_atr":
                self._numeric(
                    structure,
                    "swing_reversal_atr",
                ),

            prefix + "swing_direction_code":
                swing_direction_code,

            prefix + "swing_scale_code":
                swing_scale_code,

            prefix + "structure_bias_code":
                structure_bias_code,

            prefix + "last_swing_high_known":
                last_high_known.astype(
                    np.float64
                ),

            prefix + "last_swing_low_known":
                last_low_known.astype(
                    np.float64
                ),

            prefix + "last_major_high_known":
                major_high_known.astype(
                    np.float64
                ),

            prefix + "last_major_low_known":
                major_low_known.astype(
                    np.float64
                ),

            prefix + "dist_last_swing_high_atr":
                dist_last_high,

            prefix + "dist_last_swing_low_atr":
                dist_last_low,

            prefix + "dist_last_major_high_atr":
                dist_major_high,

            prefix + "dist_last_major_low_atr":
                dist_major_low,

            prefix + "structure_range_position":
                range_position,

            prefix + "bars_since_swing":
                self._bars_since(
                    swing_event
                ),

            # BOS
            prefix + "bullish_bos":
                bullish_bos.astype(
                    np.float64
                ),

            prefix + "bearish_bos":
                bearish_bos.astype(
                    np.float64
                ),

            prefix + "micro_bos":
                self._numeric(
                    bos,
                    "micro_bos",
                ),

            prefix + "internal_bos":
                self._numeric(
                    bos,
                    "internal_bos",
                ),

            prefix + "major_bos":
                self._numeric(
                    bos,
                    "major_bos",
                ),

            prefix + "bos_strength_atr":
                self._numeric(
                    bos,
                    "bos_strength_atr",
                ),

            prefix + "bos_continuation":
                (
                    bos_context_text
                    ==
                    "CONTINUATION"
                ).astype(
                    np.float64
                ),

            prefix + "bos_reversal":
                (
                    bos_context_text
                    ==
                    "REVERSAL"
                ).astype(
                    np.float64
                ),

            prefix + "bars_since_bullish_bos":
                self._bars_since(
                    bullish_bos
                ),

            prefix + "bars_since_bearish_bos":
                self._bars_since(
                    bearish_bos
                ),

            prefix + "last_bos_direction":
                last_bos_direction,

            # FVG
            prefix + "bullish_fvg":
                bullish_fvg.astype(
                    np.float64
                ),

            prefix + "bearish_fvg":
                bearish_fvg.astype(
                    np.float64
                ),

            prefix + "fvg_atr_ratio":
                fvg_ratio,

            prefix + "bars_since_bullish_fvg":
                self._bars_since(
                    bullish_fvg
                ),

            prefix + "bars_since_bearish_fvg":
                self._bars_since(
                    bearish_fvg
                ),

            prefix + "last_fvg_direction":
                last_fvg_direction,

            prefix + "last_fvg_atr_ratio":
                last_fvg_ratio,

            # Institutional zones
            prefix + "iz_event":
                iz_event.astype(
                    np.float64
                ),

            prefix + "iz_direction":
                iz_direction,

            prefix + "iz_strength":
                iz_strength,

            prefix + "iz_displacement_score":
                iz_displacement,

            prefix + "iz_body_ratio":
                iz_body_ratio,

            prefix + "iz_zone_size_atr":
                iz_size_atr,

            prefix + "iz_confirmation_delay_bars":
                iz_delay,

            prefix + "bars_since_bullish_iz":
                self._bars_since(
                    iz_bull
                ),

            prefix + "bars_since_bearish_iz":
                self._bars_since(
                    iz_bear
                ),

            prefix + "last_iz_direction":
                last_iz_direction,

            prefix + "last_iz_strength":
                last_iz_strength,
        }

        result = pd.DataFrame(
            values
        )

        feature_columns = [
            column
            for column
            in result.columns
            if column != "time"
        ]

        result[
            feature_columns
        ] = (
            result[
                feature_columns
            ]
            .replace(
                [
                    np.inf,
                    -np.inf,
                ],
                np.nan,
            )
            .fillna(0.0)
            .astype(
                "float32"
            )
        )

        return result

    # =========================================================================
    # Immutable writer
    # =========================================================================

    def _write_dataframe(
        self,
        *,
        frame: pd.DataFrame,
        directory: Path,
        prefix: str,
    ) -> tuple[
        Path,
        str,
    ]:

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_path: Path | None = None

        try:

            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                suffix=".tmp.csv",
                dir=directory,
                delete=False,
            ) as handle:

                temp_path = Path(
                    handle.name
                )

                frame.to_csv(
                    handle,
                    index=False,
                    lineterminator="\n",
                    float_format="%.10g",
                )

                handle.flush()

                os.fsync(
                    handle.fileno()
                )

            digest = (
                self._sha256_file(
                    temp_path
                )
            )

            final_path = (
                directory
                /
                (
                    prefix
                    +
                    "_"
                    +
                    digest[:16]
                    +
                    ".csv"
                )
            )

            if final_path.exists():

                if (
                    self._sha256_file(
                        final_path
                    )
                    !=
                    digest
                ):

                    raise TrainingFeatureEnrichmentError(
                        "V3_DATASET_COLLISION"
                    )

                temp_path.unlink(
                    missing_ok=True
                )

                temp_path = None

                return (
                    final_path,
                    digest,
                )

            os.replace(
                temp_path,
                final_path,
            )

            temp_path = None

            return (
                final_path,
                digest,
            )

        finally:

            if temp_path is not None:

                temp_path.unlink(
                    missing_ok=True
                )

    @staticmethod
    def _write_immutable(
        *,
        path: Path,
        payload: bytes,
    ) -> None:

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if path.exists():

            if (
                path.read_bytes()
                !=
                payload
            ):

                raise TrainingFeatureEnrichmentError(
                    "V3_MANIFEST_COLLISION"
                )

            return

        with path.open("xb") as handle:

            handle.write(payload)

            handle.flush()

            os.fsync(
                handle.fileno()
            )

    # =========================================================================
    # Public build
    # =========================================================================

    def enrich(
        self,
        *,
        context: Any,
    ) -> TrainingFeatureEnrichmentResult:

        self._validate_context(
            context
        )

        (
            source_path,
            source_manifest_path,
            source_manifest,
            source_hash,
            learning_fingerprint,
        ) = self._discover_v2(
            context=context
        )

        matrix = pd.read_csv(
            source_path
        )

        if matrix.empty:

            raise TrainingFeatureEnrichmentError(
                "V2_MATRIX_EMPTY"
            )

        source_features = [
            str(value)
            for value
            in source_manifest.get(
                "feature_columns",
                [],
            )
        ]

        if not source_features:

            raise TrainingFeatureEnrichmentError(
                "V2_FEATURE_COLUMNS_MISSING"
            )

        base_timeframe = str(
            source_manifest.get(
                "base_timeframe",
                "",
            )
        ).upper()

        if not base_timeframe:

            raise TrainingFeatureEnrichmentError(
                "BASE_TIMEFRAME_MISSING"
            )

        # ---------------------------------------------------------------------
        # Load exact canonical raw snapshot using existing validated loader.
        # ---------------------------------------------------------------------

        historical_loader = (
            TrainingMatrixBuilder(
                canonical_root=(
                    self.canonical_root
                )
            )
        )

        historical_snapshot = (
            historical_loader
            ._select_historical_snapshot(
                context=context,
                timeframe=base_timeframe,
            )
        )

        raw = (
            historical_loader
            ._load_snapshot_frame(
                context=context,
                snapshot=(
                    historical_snapshot
                ),
            )
        )

        domain = self._domain_features(
            raw=raw,
            base_timeframe=(
                base_timeframe
            ),
        )

        domain_features = [
            column
            for column
            in domain.columns
            if column != "time"
        ]

        collisions = (
            set(
                source_features
            )
            &
            set(
                domain_features
            )
        )

        if collisions:

            raise TrainingFeatureEnrichmentError(
                (
                    "DOMAIN_FEATURE_COLLISION: "
                    +
                    ", ".join(
                        sorted(collisions)
                    )
                )
            )

        matrix[
            "time"
        ] = pd.to_datetime(
            matrix[
                "time"
            ],
            utc=True,
            errors="raise",
        )

        domain[
            "time"
        ] = pd.to_datetime(
            domain[
                "time"
            ],
            utc=True,
            errors="raise",
        )

        before_rows = len(
            matrix
        )

        enriched = matrix.merge(
            domain,
            on="time",
            how="left",
            validate="one_to_one",
        )

        if (
            len(enriched)
            !=
            before_rows
        ):

            raise TrainingFeatureEnrichmentError(
                "V3_ROW_COUNT_CHANGED"
            )

        if bool(
            enriched[
                domain_features
            ]
            .isna()
            .any()
            .any()
        ):

            raise TrainingFeatureEnrichmentError(
                "V3_DOMAIN_ALIGNMENT_MISSING"
            )

        feature_columns = (
            source_features
            +
            domain_features
        )

        numeric_features = (
            enriched[
                feature_columns
            ]
            .apply(
                pd.to_numeric,
                errors="coerce",
            )
        )

        if not np.isfinite(
            numeric_features.to_numpy(
                dtype=np.float64
            )
        ).all():

            raise TrainingFeatureEnrichmentError(
                "V3_NONFINITE_FEATURES"
            )

        # Replace feature block in one operation.
        enriched[
            feature_columns
        ] = numeric_features

        class_distribution = {
            str(key): int(value)
            for (
                key,
                value,
            )
            in enriched[
                "target_class"
            ]
            .value_counts()
            .items()
        }

        output_directory = (
            self.canonical_root
            /
            "Instruments"
            /
            "XAUUSD"
            /
            "learning"
            /
            (
                "scope_"
                +
                learning_fingerprint
            )
            /
            "training"
            /
            self.TARGET_CONTRACT
        )

        prefix = (
            "XAUUSD_"
            +
            base_timeframe
            +
            "_"
            +
            self.TARGET_CONTRACT
        )

        (
            dataset_path,
            dataset_hash,
        ) = self._write_dataframe(
            frame=enriched,
            directory=output_directory,
            prefix=prefix,
        )

        dataset_id = (
            "train_"
            +
            dataset_hash[:24]
        )

        manifest = {
            "manifest_version": (
                "PULSEVIPER_TRAINING_MATRIX_MANIFEST_V3"
            ),
            "builder_version": (
                self.VERSION
            ),
            "dataset_kind": (
                "XAUUSD_MULTI_TIMEFRAME_CLASSIFICATION_MATRIX"
            ),
            "dataset_id": (
                dataset_id
            ),
            "dataset_filename": (
                dataset_path.name
            ),
            "dataset_sha256": (
                dataset_hash
            ),
            "row_count": int(
                len(enriched)
            ),
            "feature_count": int(
                len(feature_columns)
            ),
            "feature_columns": (
                feature_columns
            ),
            "target_columns": (
                source_manifest.get(
                    "target_columns",
                    [],
                )
            ),
            "target_classes": (
                source_manifest.get(
                    "target_classes",
                    [
                        "SHORT",
                        "NO_TRADE",
                        "LONG",
                    ],
                )
            ),
            "target_class_mapping": (
                source_manifest.get(
                    "target_class_mapping",
                    {
                        "SHORT": -1,
                        "NO_TRADE": 0,
                        "LONG": 1,
                    },
                )
            ),
            "target_label_contract": (
                source_manifest.get(
                    "target_label_contract"
                )
            ),
            "base_timeframe": (
                base_timeframe
            ),
            "context_timeframes": (
                source_manifest.get(
                    "context_timeframes",
                    [],
                )
            ),
            "target_horizon_bars": (
                source_manifest.get(
                    "target_horizon_bars"
                )
            ),
            "train_fraction": (
                source_manifest.get(
                    "train_fraction"
                )
            ),
            "validation_fraction": (
                source_manifest.get(
                    "validation_fraction"
                )
            ),
            "test_fraction": (
                source_manifest.get(
                    "test_fraction"
                )
            ),
            "split_purge_bars": (
                source_manifest.get(
                    "split_purge_bars"
                )
            ),
            "class_distribution": (
                class_distribution
            ),
            "split_class_distribution": (
                source_manifest.get(
                    "split_class_distribution"
                )
            ),
            "learning_scope": (
                source_manifest.get(
                    "learning_scope"
                )
            ),
            "learning_scope_fingerprint": (
                learning_fingerprint
            ),
            "source_execution_context_fingerprint": (
                source_manifest.get(
                    "source_execution_context_fingerprint"
                )
            ),
            "source_historical_snapshots": (
                source_manifest.get(
                    "source_historical_snapshots"
                )
            ),
            "source_training_matrix": {
                "dataset_id": (
                    source_manifest.get(
                        "dataset_id"
                    )
                ),
                "dataset_sha256": (
                    source_hash
                ),
                "manifest_sha256": (
                    self._sha256_file(
                        source_manifest_path
                    )
                ),
                "training_contract_version": (
                    self.SOURCE_CONTRACT
                ),
            },
            "domain_feature_contract": {
                "version": (
                    self.DOMAIN_FEATURE_VERSION
                ),
                "feature_count": (
                    len(
                        domain_features
                    )
                ),
                "feature_columns": (
                    domain_features
                ),
                "base_timeframe": (
                    base_timeframe
                ),
                "source_historical_dataset_id": (
                    historical_snapshot.dataset_id
                ),
                "source_historical_dataset_sha256": (
                    historical_snapshot.dataset_sha256
                ),
                "engines": {
                    "market_structure": (
                        "6.1"
                    ),
                    "bos_engine": (
                        "3.0"
                    ),
                    "market_regime": (
                        "1.0"
                    ),
                    "fvg_engine": (
                        "1.1"
                    ),
                    "institutional_zones": (
                        "2.0_CAUSAL_ONLY"
                    ),
                },
                "causality_rule": (
                    "BASE_BAR_DOMAIN_FEATURES_AVAILABLE_ONLY_AFTER_BASE_BAR_CLOSE"
                ),
            },
            "feature_availability_rule": (
                "ALL_FEATURES_CAUSAL_AT_DECISION_TIME"
            ),
            "target_future_data_rule": (
                "FUTURE_DATA_ALLOWED_ONLY_IN_TARGET_COLUMNS"
            ),
            "training_contract_version": (
                self.TARGET_CONTRACT
            ),
            "live_authorized": False,
        }

        manifest_bytes = (
            self._canonical_json_bytes(
                manifest
            )
        )

        manifest_hash = (
            self._sha256_bytes(
                manifest_bytes
            )
        )

        manifest_path = (
            dataset_path.with_suffix(
                ".manifest.json"
            )
        )

        self._write_immutable(
            path=manifest_path,
            payload=manifest_bytes,
        )

        return TrainingFeatureEnrichmentResult(
            dataset_id=dataset_id,
            dataset_path=dataset_path,
            manifest_path=manifest_path,
            dataset_sha256=dataset_hash,
            manifest_sha256=manifest_hash,
            row_count=len(
                enriched
            ),
            feature_count=len(
                feature_columns
            ),
            added_feature_count=len(
                domain_features
            ),
            class_distribution=(
                class_distribution
            ),
            learning_scope_fingerprint=(
                learning_fingerprint
            ),
            training_contract_version=(
                self.TARGET_CONTRACT
            ),
            live_authorized=False,
        )