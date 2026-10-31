"""
===============================================================================
Module      : scalping_pipeline.py
Project     : PulseViper XAU AI
Version     : 1.0
Author      : Muhammad Adnan
Purpose     : Canonical XAUUSD Temporal Scalping AI Pipeline
===============================================================================

Pipeline
--------
OHLC
  ↓
Liquidity
  ↓
Causal Liquidity Sweep
  ↓
Displacement
  ↓
Adaptive Market Structure
  ↓
Causal BOS
  ↓
FVG
  ↓
FVG Mitigation / Rejection
  ↓
FVG Quality Metadata
  ↓
Temporal Setup State
  ↓
Temporal Confidence
  ↓
trade_ready event

This module is the canonical orchestration layer.

Individual engines remain responsible for their own domain logic.
This class only guarantees correct execution order and integration.
"""

from __future__ import annotations

import importlib
from typing import Any

import pandas as pd


class ScalpingPipeline:

    VERSION = "1.0"

    MODE = "SCALPING_TEMPORAL"

    def __init__(
        self,
        liquidity_engine: Any | None = None,
        sweep_engine: Any | None = None,
        displacement_engine: Any | None = None,
        market_structure_engine: Any | None = None,
        bos_engine: Any | None = None,
        fvg_engine: Any | None = None,
        mitigation_engine: Any | None = None,
        quality_engine: Any | None = None,
        setup_state_engine: Any | None = None,
        confidence_engine: Any | None = None,
    ) -> None:

        # =====================================================================
        # Liquidity
        # =====================================================================

        if liquidity_engine is None:

            liquidity_module = (
                importlib.import_module(
                    "02_AI.Core.liquidity_engine"
                )
            )

            liquidity_engine = (
                liquidity_module
                .liquidity_engine
            )

        # Explicit Any removes Optional inference after resolution.
        self.liquidity_engine: Any = (
            liquidity_engine
        )

        # =====================================================================
        # Sweep
        # =====================================================================

        if sweep_engine is None:

            sweep_module = (
                importlib.import_module(
                    "02_AI.Core.liquidity_sweep_engine"
                )
            )

            liquidity_memory = getattr(
                self.liquidity_engine,
                "memory",
            )

            sweep_engine = (
                sweep_module
                .LiquiditySweepEngine(
                    memory=(
                        liquidity_memory
                    )
                )
            )

        self.sweep_engine: Any = (
            sweep_engine
        )

        # =====================================================================
        # Displacement
        # =====================================================================

        if displacement_engine is None:

            displacement_engine = (
                importlib.import_module(
                    "02_AI.Core.displacement_engine"
                )
                .displacement_engine
            )

        self.displacement_engine: Any = (
            displacement_engine
        )

        # =====================================================================
        # Market Structure
        # =====================================================================

        if market_structure_engine is None:

            market_structure_engine = (
                importlib.import_module(
                    "02_AI.Core.market_structure"
                )
                .market_structure
            )

        self.market_structure_engine: Any = (
            market_structure_engine
        )

        # =====================================================================
        # BOS
        # =====================================================================

        if bos_engine is None:

            bos_engine = (
                importlib.import_module(
                    "02_AI.Core.bos_engine"
                )
                .bos_engine
            )

        self.bos_engine: Any = (
            bos_engine
        )

        # =====================================================================
        # FVG Detection
        # =====================================================================

        if fvg_engine is None:

            fvg_engine = (
                importlib.import_module(
                    "02_AI.Core.fvg_engine"
                )
                .fvg_engine
            )

        self.fvg_engine: Any = (
            fvg_engine
        )

        # =====================================================================
        # FVG Mitigation
        # =====================================================================

        if mitigation_engine is None:

            mitigation_engine = (
                importlib.import_module(
                    "02_AI.Core.fvg_mitigation_engine"
                )
                .fvg_mitigation_engine
            )

        self.mitigation_engine: Any = (
            mitigation_engine
        )

        # =====================================================================
        # FVG Quality
        #
        # Quality remains useful metadata / diagnostics.
        # Temporal Confidence does not depend on same-row FVG Quality.
        # =====================================================================

        if quality_engine is None:

            quality_engine = (
                importlib.import_module(
                    "02_AI.Core.fvg_quality_engine"
                )
                .fvg_quality_engine
            )

        self.quality_engine: Any = (
            quality_engine
        )

        # =====================================================================
        # Temporal Setup State
        # =====================================================================

        if setup_state_engine is None:

            setup_state_engine = (
                importlib.import_module(
                    "02_AI.Core.setup_state_engine"
                )
                .setup_state_engine
            )

        self.setup_state_engine: Any = (
            setup_state_engine
        )

        # =====================================================================
        # Confidence
        # =====================================================================

        if confidence_engine is None:

            confidence_engine = (
                importlib.import_module(
                    "02_AI.Core.confidence_engine"
                )
                .confidence_engine
            )

        self.confidence_engine: Any = (
            confidence_engine
        )

    # =========================================================================
    # Validation
    # =========================================================================

    @staticmethod
    def _validate_input(
        df: pd.DataFrame,
    ) -> None:

        if not isinstance(
            df,
            pd.DataFrame,
        ):

            raise TypeError(
                "ScalpingPipeline input must be a pandas DataFrame"
            )

        required = {
            "open",
            "high",
            "low",
            "close",
        }

        missing = (
            required
            - set(
                df.columns
            )
        )

        if missing:

            raise ValueError(
                "Missing required pipeline columns: "
                + ", ".join(
                    sorted(
                        missing
                    )
                )
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

        # =====================================================================
        # 1. Liquidity candidate detection
        # =====================================================================

        df = (
            self.liquidity_engine
            .generate(
                df
            )
        )

        # =====================================================================
        # 2. Causal chronological liquidity sweep
        # =====================================================================

        df = (
            self.sweep_engine
            .generate(
                df,
                reset_memory=True,
            )
        )

        # =====================================================================
        # 3. Displacement
        # =====================================================================

        df = (
            self.displacement_engine
            .generate(
                df
            )
        )

        # =====================================================================
        # 4. Adaptive market structure
        # =====================================================================

        df = (
            self.market_structure_engine
            .generate(
                df
            )
        )

        # =====================================================================
        # 5. Causal BOS
        # =====================================================================

        df = (
            self.bos_engine
            .generate(
                df,
                reset_memory=True,
            )
        )

        # =====================================================================
        # 6. FVG detection
        # =====================================================================

        df = (
            self.fvg_engine
            .generate(
                df
            )
        )

        # =====================================================================
        # 7. FVG lifecycle
        # =====================================================================

        df = (
            self.mitigation_engine
            .generate(
                df
            )
        )

        # =====================================================================
        # 8. FVG quality metadata
        #
        # Kept for diagnostics / ML features.
        # It is no longer the temporal entry-state authority.
        # =====================================================================

        df = (
            self.quality_engine
            .generate(
                df
            )
        )

        # =====================================================================
        # 9. Temporal scalp setup state
        # =====================================================================

        df = (
            self.setup_state_engine
            .generate(
                df
            )
        )

        # =====================================================================
        # 10. Temporal confidence
        # =====================================================================

        df = (
            self.confidence_engine
            .generate(
                df
            )
        )

        # =====================================================================
        # Pipeline Metadata
        # =====================================================================

        df[
            "pipeline_version"
        ] = self.VERSION

        df[
            "pipeline_mode"
        ] = self.MODE

        return df


# =============================================================================
# Global Pipeline
# =============================================================================

scalping_pipeline = (
    ScalpingPipeline()
)