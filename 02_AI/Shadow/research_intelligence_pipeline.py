"""
===============================================================================
Module      : research_intelligence_pipeline.py
Project     : PulseViper XAU AI
Version     : 1.0.1
Purpose     : Shadow-Only Causal Research Intelligence Orchestrator
===============================================================================

Pipeline
--------
Frozen Canonical Scalping Pipeline
        ↓
Market Context Liquidity
        ↓
Liquidity Lifecycle
        ↓
Liquidity Structure Intelligence
        ↓
Candle / Swing Intelligence
        ↓
Market Decision Clarity
        ↓
Level Entry Intelligence

Research contract
-----------------
This module composes the frozen production pipeline with causal research-only
intelligence.

It does NOT:
- place trades
- communicate with MT5 for execution
- modify trade_ready
- modify Confidence
- modify SetupState
- modify BOS
- modify canonical production pipeline metadata
- use retrospective cslabel_* features
- calculate account risk

Safety
------
The canonical pipeline remains the sole owner of production trade decisions.

Research engines may append metadata, but canonical production outputs are
protected and restored exactly before the final result is returned.

Performance
-----------
v1.0.1 avoids repeated DataFrame column insertion while composing the final
wide research frame.

Canonical columns, research-only columns, and research metadata are joined
in blocks rather than inserted one column at a time. This avoids pandas
fragmentation warnings while remaining friendly to static analysis tools
such as Pylance.
"""

from __future__ import annotations

import importlib
from typing import Any

import pandas as pd


class ResearchIntelligencePipeline:
    """
    Causal shadow/research orchestration with strict production protection.
    """

    VERSION = "1.0.1"

    MODE = "SHADOW_CAUSAL_RESEARCH_ONLY"

    REQUIRED_COLUMNS = (
        "time",
        "open",
        "high",
        "low",
        "close",
    )

    # =========================================================================
    # Production protection
    # =========================================================================

    PROTECTED_EXACT_COLUMNS = {
        "trade_ready",
        "pipeline_version",
        "pipeline_mode",
    }

    PROTECTED_PREFIXES = (
        "confidence_",
        "setup_",
        "bos_",
    )

    # =========================================================================
    # Research namespaces
    # =========================================================================
    #
    # These namespaces are removed from a previously enriched input before
    # the canonical pipeline is replayed.
    #
    # This prevents stale research state from contaminating a fresh causal
    # calculation.
    # =========================================================================

    RESEARCH_PREFIXES = (
        "ctx_",
        "liq_",
        "liqintel_",
        "csi_",
        "mdc_",
        "lei_",
        "research_",
    )

    HINDSIGHT_PREFIXES = (
        "cslabel_",
    )

    def __init__(
        self,
        production_pipeline: Any | None = None,
        market_context_engine: Any | None = None,
        liquidity_lifecycle_engine: Any | None = None,
        liquidity_intelligence_engine: Any | None = None,
        candle_swing_engine: Any | None = None,
        decision_clarity_engine: Any | None = None,
        level_entry_engine: Any | None = None,
    ) -> None:

        # =====================================================================
        # Frozen canonical production pipeline
        # =====================================================================

        self.production_pipeline: Any = (
            production_pipeline
            if production_pipeline is not None
            else self._load(
                "02_AI.Core.scalping_pipeline",
                "scalping_pipeline",
            )
        )

        # =====================================================================
        # Market context
        # =====================================================================

        self.market_context_engine: Any = (
            market_context_engine
            if market_context_engine is not None
            else self._load(
                "02_AI.Core.market_context_liquidity",
                "market_context_liquidity",
            )
        )

        # =====================================================================
        # Liquidity lifecycle
        # =====================================================================

        self.liquidity_lifecycle_engine: Any = (
            liquidity_lifecycle_engine
            if liquidity_lifecycle_engine is not None
            else self._load(
                "02_AI.Core.liquidity_lifecycle",
                "liquidity_lifecycle",
            )
        )

        # =====================================================================
        # Liquidity structure intelligence
        # =====================================================================

        self.liquidity_intelligence_engine: Any = (
            liquidity_intelligence_engine
            if liquidity_intelligence_engine is not None
            else self._load(
                "02_AI.Core.liquidity_structure_intelligence",
                "liquidity_structure_intelligence",
            )
        )

        # =====================================================================
        # Candle / swing intelligence
        # =====================================================================

        self.candle_swing_engine: Any = (
            candle_swing_engine
            if candle_swing_engine is not None
            else self._load(
                "02_AI.Core.candle_swing_intelligence",
                "candle_swing_intelligence",
            )
        )

        # =====================================================================
        # Market decision clarity
        # =====================================================================

        self.decision_clarity_engine: Any = (
            decision_clarity_engine
            if decision_clarity_engine is not None
            else self._load(
                "02_AI.Core.market_decision_clarity",
                "market_decision_clarity",
            )
        )

        # =====================================================================
        # Level entry intelligence
        # =====================================================================

        self.level_entry_engine: Any = (
            level_entry_engine
            if level_entry_engine is not None
            else self._load(
                "02_AI.Core.level_entry_intelligence",
                "level_entry_intelligence",
            )
        )

    # =========================================================================
    # Dynamic loading
    # =========================================================================

    @staticmethod
    def _load(
        module_name: str,
        attribute_name: str,
    ) -> Any:
        """
        Import one engine lazily.

        Lazy importing keeps this shadow orchestration layer decoupled from
        direct hard dependencies at module import time.
        """

        module = importlib.import_module(
            module_name
        )

        if not hasattr(
            module,
            attribute_name,
        ):
            raise AttributeError(
                f"{module_name} does not expose {attribute_name}"
            )

        return getattr(
            module,
            attribute_name,
        )

    # =========================================================================
    # Input validation
    # =========================================================================

    @classmethod
    def _validate_input(
        cls,
        data: pd.DataFrame,
    ) -> None:
        """
        Validate minimum live-safe research input contract.
        """

        if not isinstance(
            data,
            pd.DataFrame,
        ):
            raise TypeError(
                "ResearchIntelligencePipeline input "
                "must be a pandas DataFrame"
            )

        missing = (
            set(
                cls.REQUIRED_COLUMNS
            )
            -
            set(
                data.columns
            )
        )

        if missing:
            raise ValueError(
                "Missing required research-pipeline columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )

        if not data.columns.is_unique:
            raise ValueError(
                "ResearchIntelligencePipeline input "
                "contains duplicate column names"
            )

    # =========================================================================
    # Clean replay input
    # =========================================================================

    @classmethod
    def _strip_prior_research_columns(
        cls,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Remove stale research and hindsight namespaces before replay.

        This allows callers to accidentally pass an already-enriched shadow
        dataframe without contaminating the next causal calculation.
        """

        removable: list[Any] = []

        for column in data.columns:

            if not isinstance(
                column,
                str,
            ):
                continue

            if (
                column.startswith(
                    cls.RESEARCH_PREFIXES
                )
                or
                column.startswith(
                    cls.HINDSIGHT_PREFIXES
                )
            ):
                removable.append(
                    column
                )

        if not removable:
            return (
                data
                .copy()
                .reset_index(
                    drop=True
                )
            )

        return (
            data
            .drop(
                columns=removable,
            )
            .copy()
            .reset_index(
                drop=True
            )
        )

    # =========================================================================
    # Production protection helpers
    # =========================================================================

    @classmethod
    def _protected_columns(
        cls,
        canonical: pd.DataFrame,
    ) -> list[str]:
        """
        Return canonical columns that research stages may never change.
        """

        protected: list[str] = []

        for raw_column in canonical.columns:

            if not isinstance(
                raw_column,
                str,
            ):
                continue

            if (
                raw_column
                in
                cls.PROTECTED_EXACT_COLUMNS
                or
                raw_column.startswith(
                    cls.PROTECTED_PREFIXES
                )
            ):
                protected.append(
                    raw_column
                )

        return protected

    @staticmethod
    def _same_series(
        left: pd.Series,
        right: pd.Series,
    ) -> bool:
        """
        Compare two series after removing index differences.
        """

        left_values = (
            left
            .reset_index(
                drop=True
            )
        )

        right_values = (
            right
            .reset_index(
                drop=True
            )
        )

        return left_values.equals(
            right_values
        )

    @staticmethod
    def _normalized_time(
        frame: pd.DataFrame,
    ) -> pd.Series:
        """
        Normalize timestamps only for alignment comparison.

        This does not alter the timestamp representation returned to callers.
        """

        converted: Any = pd.to_datetime(
            frame[
                "time"
            ],
            errors="coerce",
            utc=True,
        )

        return (
            pd.Series(
                converted
            )
            .reset_index(
                drop=True
            )
        )

    @classmethod
    def _assert_alignment(
        cls,
        canonical: pd.DataFrame,
        enriched: pd.DataFrame,
        stage_name: str,
    ) -> None:
        """
        Verify row alignment and frozen-production invariants.
        """

        # ---------------------------------------------------------------------
        # Row count
        # ---------------------------------------------------------------------

        if len(
            canonical
        ) != len(
            enriched
        ):
            raise RuntimeError(
                "Research/canonical row-count mismatch after "
                f"{stage_name}: "
                f"{len(enriched)} != {len(canonical)}"
            )

        # ---------------------------------------------------------------------
        # Duplicate columns
        # ---------------------------------------------------------------------

        if not enriched.columns.is_unique:
            raise RuntimeError(
                "Research stage produced duplicate columns: "
                f"{stage_name}"
            )

        # ---------------------------------------------------------------------
        # Time alignment
        # ---------------------------------------------------------------------

        if (
            "time" in canonical.columns
            and
            "time" in enriched.columns
        ):

            canonical_time = (
                cls._normalized_time(
                    canonical
                )
            )

            enriched_time = (
                cls._normalized_time(
                    enriched
                )
            )

            if not canonical_time.equals(
                enriched_time
            ):
                raise RuntimeError(
                    "Research/canonical time alignment mismatch "
                    f"after {stage_name}"
                )

        # ---------------------------------------------------------------------
        # Protected production values
        # ---------------------------------------------------------------------

        for column in cls._protected_columns(
            canonical
        ):

            if column not in enriched.columns:
                raise RuntimeError(
                    "Research stage removed protected canonical column "
                    f"{column!r}: {stage_name}"
                )

            if not cls._same_series(
                canonical[
                    column
                ],
                enriched[
                    column
                ],
            ):
                raise RuntimeError(
                    "Research stage modified protected canonical column "
                    f"{column!r}: {stage_name}"
                )

    # =========================================================================
    # Stage execution
    # =========================================================================

    @staticmethod
    def _run_stage(
        engine: Any,
        data: pd.DataFrame,
        stage_name: str,
    ) -> pd.DataFrame:
        """
        Run one research/production engine through its generate() contract.
        """

        generate = getattr(
            engine,
            "generate",
            None,
        )

        if not callable(
            generate
        ):
            raise TypeError(
                f"{stage_name} does not expose callable generate()"
            )

        output: Any = generate(
            data
        )

        if not isinstance(
            output,
            pd.DataFrame,
        ):
            raise TypeError(
                f"{stage_name} generate() did not return a DataFrame"
            )

        return (
            output
            .copy()
            .reset_index(
                drop=True
            )
        )

    # =========================================================================
    # Hindsight protection
    # =========================================================================

    @classmethod
    def _assert_no_hindsight(
        cls,
        frame: pd.DataFrame,
    ) -> None:
        """
        Reject retrospective swing labels from the live-safe research chain.
        """

        hindsight_columns = [
            column
            for column in frame.columns
            if (
                isinstance(
                    column,
                    str,
                )
                and
                column.startswith(
                    cls.HINDSIGHT_PREFIXES
                )
            )
        ]

        if hindsight_columns:
            raise RuntimeError(
                "Retrospective cslabel_* columns are forbidden in "
                "the causal research pipeline: "
                +
                ", ".join(
                    hindsight_columns
                )
            )

    # =========================================================================
    # Final wide-frame composition
    # =========================================================================

    @staticmethod
    def _research_only_columns(
        canonical: pd.DataFrame,
        enriched: pd.DataFrame,
    ) -> list[Any]:
        """
        Return only columns introduced by research stages.

        Canonical columns are intentionally excluded because the final result
        must use the exact canonical production values.
        """

        canonical_columns = set(
            canonical.columns
        )

        return [
            column
            for column in enriched.columns
            if column not in canonical_columns
        ]

    @classmethod
    def _compose_final_result(
        cls,
        canonical: pd.DataFrame,
        enriched: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Compose frozen canonical output and research-only additions.

        DataFrame.join() is used instead of repeated column assignment or
        pd.concat(copy=False).

        Advantages:
        - avoids DataFrame fragmentation
        - avoids the pandas/Pylance concat overload mismatch
        - preserves deterministic RangeIndex alignment
        - makes duplicate-column collisions fail visibly
        """

        canonical_block = (
            canonical
            .copy()
            .reset_index(
                drop=True
            )
        )

        research_columns = (
            cls._research_only_columns(
                canonical=canonical,
                enriched=enriched,
            )
        )

        if not research_columns:
            return (
                canonical_block
                .copy()
                .reset_index(
                    drop=True
                )
            )

        research_block = (
            enriched
            .loc[
                :,
                research_columns,
            ]
            .copy()
            .reset_index(
                drop=True
            )
        )

        result = canonical_block.join(
            research_block,
            how="left",
        )

        # Deep copy consolidates the final wide dataframe.
        return (
            result
            .copy()
            .reset_index(
                drop=True
            )
        )

    # =========================================================================
    # Research metadata
    # =========================================================================

    @classmethod
    def _attach_metadata(
        cls,
        frame: pd.DataFrame,
        stage_count: int,
    ) -> pd.DataFrame:
        """
        Attach all research-pipeline metadata as a single dataframe block.

        This avoids repeated result[column] assignments and therefore avoids
        pandas fragmentation warnings.
        """

        metadata = pd.DataFrame(
            {
                "research_pipeline_version": cls.VERSION,

                "research_pipeline_mode": cls.MODE,

                "research_stage_count": int(
                    stage_count
                ),

                "research_trade_ready_unchanged": 1,

                "research_live_safe": 1,
            },
            index=frame.index,
        )

        result = frame.join(
            metadata,
            how="left",
        )

        return (
            result
            .copy()
            .reset_index(
                drop=True
            )
        )

    # =========================================================================
    # Main
    # =========================================================================

    def generate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Generate the full causal shadow research intelligence dataframe.
        """

        self._validate_input(
            data
        )

        # =====================================================================
        # 0. Strip stale research metadata
        # =====================================================================

        raw = (
            self._strip_prior_research_columns(
                data
            )
        )

        # =====================================================================
        # 1. Frozen canonical production baseline
        # =====================================================================

        canonical = self._run_stage(
            engine=self.production_pipeline,
            data=raw,
            stage_name="canonical_scalping_pipeline",
        )

        # =====================================================================
        # 2-7. Research-only causal intelligence chain
        # =====================================================================

        stages: tuple[
            tuple[
                str,
                Any,
            ],
            ...,
        ] = (
            (
                "market_context_liquidity",
                self.market_context_engine,
            ),

            (
                "liquidity_lifecycle",
                self.liquidity_lifecycle_engine,
            ),

            (
                "liquidity_structure_intelligence",
                self.liquidity_intelligence_engine,
            ),

            (
                "candle_swing_intelligence",
                self.candle_swing_engine,
            ),

            (
                "market_decision_clarity",
                self.decision_clarity_engine,
            ),

            (
                "level_entry_intelligence",
                self.level_entry_engine,
            ),
        )

        current = (
            canonical
            .copy()
            .reset_index(
                drop=True
            )
        )

        for (
            stage_name,
            engine,
        ) in stages:

            current = self._run_stage(
                engine=engine,
                data=current,
                stage_name=stage_name,
            )

            # -----------------------------------------------------------------
            # Each individual stage must preserve canonical authority.
            # -----------------------------------------------------------------

            self._assert_alignment(
                canonical=canonical,
                enriched=current,
                stage_name=stage_name,
            )

            # -----------------------------------------------------------------
            # No retrospective labels may enter this chain.
            # -----------------------------------------------------------------

            self._assert_no_hindsight(
                current
            )

        # =====================================================================
        # Final composition
        # =====================================================================

        result = self._compose_final_result(
            canonical=canonical,
            enriched=current,
        )

        # =====================================================================
        # Final canonical protection before metadata
        # =====================================================================

        self._assert_alignment(
            canonical=canonical,
            enriched=result,
            stage_name="final_research_composition",
        )

        self._assert_no_hindsight(
            result
        )

        # =====================================================================
        # Research pipeline metadata
        # =====================================================================

        result = self._attach_metadata(
            frame=result,
            stage_count=len(
                stages
            ),
        )

        # =====================================================================
        # Final defensive checks
        # =====================================================================

        if not result.columns.is_unique:
            raise RuntimeError(
                "Final research pipeline output contains "
                "duplicate column names"
            )

        self._assert_alignment(
            canonical=canonical,
            enriched=result,
            stage_name="final_research_output",
        )

        self._assert_no_hindsight(
            result
        )

        return result


# =============================================================================
# Global research pipeline
# =============================================================================

research_intelligence_pipeline = (
    ResearchIntelligencePipeline()
)