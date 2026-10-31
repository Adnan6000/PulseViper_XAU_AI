"""
===============================================================================
Module      : research_intelligence_pipeline.py
Project     : PulseViper XAU AI
Version     : 1.1.0
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
        ↓
Institutional Zone causal events
        ↓
Institutional Zone causal lifecycle
        ↓
Institutional Zone Context Adapter
        ↓
Final research-only wide frame

Institutional Zone architecture
-------------------------------
Institutional-zone detection and lifecycle are side-chain event tables.

They are NOT passed through the ordinary row-aligned stage loop.

Only the final causal izctx_* context is attached to the bar-aligned research
dataframe.

Critically, this happens AFTER Level Entry Intelligence. Therefore the new
institutional-zone context cannot change LEI decisions in this version.

Research contract
-----------------
This module does NOT:

- place trades
- modify trade_ready
- modify Confidence
- modify SetupState
- modify BOS
- modify canonical production metadata
- modify existing MDC / LEI outputs through the zone side-chain
- attach retrospective cslabel_* data
- attach retrospective izlabel_* data
- calculate account risk
- authorize execution

The canonical production pipeline remains the sole owner of trade_ready.
"""

from __future__ import annotations

import importlib
from typing import Any

import pandas as pd


class ResearchIntelligencePipeline:
    """
    Causal shadow research orchestrator with frozen production protection.
    """

    VERSION = "1.1.0"

    MODE = "SHADOW_CAUSAL_RESEARCH_ONLY"

    REQUIRED_COLUMNS = (
        "time",
        "open",
        "high",
        "low",
        "close",
    )

    ALIGNED_RESEARCH_STAGE_COUNT = 6

    ZONE_SIDECHAIN_STAGE_COUNT = 3

    TOTAL_RESEARCH_STAGE_COUNT = (
        ALIGNED_RESEARCH_STAGE_COUNT
        +
        ZONE_SIDECHAIN_STAGE_COUNT
    )

    # =========================================================================
    # Frozen production protection
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

    RESEARCH_PREFIXES = (
        "ctx_",
        "liq_",
        "liqintel_",
        "csi_",
        "mdc_",
        "lei_",

        "iz_",
        "izl_",
        "izctx_",

        "research_",
    )

    HINDSIGHT_PREFIXES = (
        "cslabel_",
        "izlabel_",
    )

    # =========================================================================
    # Construction
    # =========================================================================

    def __init__(
        self,
        production_pipeline: Any | None = None,
        market_context_engine: Any | None = None,
        liquidity_lifecycle_engine: Any | None = None,
        liquidity_intelligence_engine: Any | None = None,
        candle_swing_engine: Any | None = None,
        decision_clarity_engine: Any | None = None,
        level_entry_engine: Any | None = None,
        institutional_zones_engine: Any | None = None,
        institutional_zone_lifecycle_engine: Any | None = None,
        institutional_zone_context_engine: Any | None = None,
    ) -> None:

        self.production_pipeline: Any = (
            production_pipeline
            if production_pipeline is not None
            else self._load(
                "02_AI.Core.scalping_pipeline",
                "scalping_pipeline",
            )
        )

        self.market_context_engine: Any = (
            market_context_engine
            if market_context_engine is not None
            else self._load(
                "02_AI.Core.market_context_liquidity",
                "market_context_liquidity",
            )
        )

        self.liquidity_lifecycle_engine: Any = (
            liquidity_lifecycle_engine
            if liquidity_lifecycle_engine is not None
            else self._load(
                "02_AI.Core.liquidity_lifecycle",
                "liquidity_lifecycle",
            )
        )

        self.liquidity_intelligence_engine: Any = (
            liquidity_intelligence_engine
            if liquidity_intelligence_engine is not None
            else self._load(
                "02_AI.Core.liquidity_structure_intelligence",
                "liquidity_structure_intelligence",
            )
        )

        self.candle_swing_engine: Any = (
            candle_swing_engine
            if candle_swing_engine is not None
            else self._load(
                "02_AI.Core.candle_swing_intelligence",
                "candle_swing_intelligence",
            )
        )

        self.decision_clarity_engine: Any = (
            decision_clarity_engine
            if decision_clarity_engine is not None
            else self._load(
                "02_AI.Core.market_decision_clarity",
                "market_decision_clarity",
            )
        )

        self.level_entry_engine: Any = (
            level_entry_engine
            if level_entry_engine is not None
            else self._load(
                "02_AI.Core.level_entry_intelligence",
                "level_entry_intelligence",
            )
        )

        self.institutional_zones_engine: Any = (
            institutional_zones_engine
            if institutional_zones_engine is not None
            else self._load(
                "02_AI.Core.institutional_zones",
                "institutional_zones",
            )
        )

        self.institutional_zone_lifecycle_engine: Any = (
            institutional_zone_lifecycle_engine
            if institutional_zone_lifecycle_engine is not None
            else self._load(
                "02_AI.Shadow.institutional_zone_lifecycle",
                "institutional_zone_lifecycle",
            )
        )

        self.institutional_zone_context_engine: Any = (
            institutional_zone_context_engine
            if institutional_zone_context_engine is not None
            else self._load(
                "02_AI.Shadow.institutional_zone_context",
                "institutional_zone_context",
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

        result = (
            data.drop(
                columns=removable,
                errors="ignore",
            )
            .copy()
            .reset_index(
                drop=True
            )
        )

        return result

    # =========================================================================
    # Production protection
    # =========================================================================

    @classmethod
    def _protected_columns(
        cls,
        canonical: pd.DataFrame,
    ) -> list[str]:

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

        return (
            left
            .reset_index(
                drop=True
            )
            .equals(
                right.reset_index(
                    drop=True
                )
            )
        )

    @staticmethod
    def _normalized_time(
        frame: pd.DataFrame,
    ) -> pd.Series:

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

        if not enriched.columns.is_unique:
            raise RuntimeError(
                "Research stage produced duplicate columns: "
                f"{stage_name}"
            )

        if (
            "time" in canonical.columns
            and
            "time" in enriched.columns
        ):

            if not cls._normalized_time(
                canonical
            ).equals(
                cls._normalized_time(
                    enriched
                )
            ):
                raise RuntimeError(
                    "Research/canonical time alignment mismatch "
                    f"after {stage_name}"
                )

        for column in cls._protected_columns(
            canonical
        ):

            if column not in enriched.columns:
                raise RuntimeError(
                    "Research stage removed protected canonical "
                    f"column {column!r}: {stage_name}"
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
                    "Research stage modified protected canonical "
                    f"column {column!r}: {stage_name}"
                )

    # =========================================================================
    # Append-only protection
    # =========================================================================

    @classmethod
    def _assert_existing_columns_unchanged(
        cls,
        before: pd.DataFrame,
        after: pd.DataFrame,
        stage_name: str,
    ) -> None:
        """
        Require a side-chain adapter to be append-only.

        This protects MDC, LEI and every other already-calculated field,
        not only canonical production fields.
        """

        if len(
            before
        ) != len(
            after
        ):
            raise RuntimeError(
                f"{stage_name} changed row count"
            )

        for column in before.columns:

            if column not in after.columns:
                raise RuntimeError(
                    f"{stage_name} removed existing column "
                    f"{column!r}"
                )

            if not cls._same_series(
                before[
                    column
                ],
                after[
                    column
                ],
            ):
                raise RuntimeError(
                    f"{stage_name} modified existing column "
                    f"{column!r}"
                )

    # =========================================================================
    # One-input aligned stage
    # =========================================================================

    @staticmethod
    def _run_stage(
        engine: Any,
        data: pd.DataFrame,
        stage_name: str,
    ) -> pd.DataFrame:

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
    # Zone side-chain execution
    # =========================================================================

    @staticmethod
    def _run_zone_events(
        engine: Any,
        market: pd.DataFrame,
    ) -> pd.DataFrame:

        generate = getattr(
            engine,
            "generate",
            None,
        )

        if not callable(
            generate
        ):
            raise TypeError(
                "institutional_zones does not expose callable generate()"
            )

        output: Any = generate(
            market
        )

        if not isinstance(
            output,
            pd.DataFrame,
        ):
            raise TypeError(
                "institutional_zones generate() "
                "did not return a DataFrame"
            )

        return (
            output
            .copy()
            .reset_index(
                drop=True
            )
        )

    @staticmethod
    def _run_zone_lifecycle(
        engine: Any,
        market: pd.DataFrame,
        zone_events: pd.DataFrame,
    ) -> pd.DataFrame:

        generate = getattr(
            engine,
            "generate",
            None,
        )

        if not callable(
            generate
        ):
            raise TypeError(
                "institutional_zone_lifecycle does not "
                "expose callable generate()"
            )

        output: Any = generate(
            market,
            zone_events,
        )

        if not isinstance(
            output,
            pd.DataFrame,
        ):
            raise TypeError(
                "institutional_zone_lifecycle generate() "
                "did not return a DataFrame"
            )

        return (
            output
            .copy()
            .reset_index(
                drop=True
            )
        )

    @staticmethod
    def _run_zone_context(
        engine: Any,
        market: pd.DataFrame,
        zone_events: pd.DataFrame,
        lifecycle: pd.DataFrame,
    ) -> pd.DataFrame:

        generate = getattr(
            engine,
            "generate",
            None,
        )

        if not callable(
            generate
        ):
            raise TypeError(
                "institutional_zone_context does not "
                "expose callable generate()"
            )

        output: Any = generate(
            market,
            zone_events,
            lifecycle,
        )

        if not isinstance(
            output,
            pd.DataFrame,
        ):
            raise TypeError(
                "institutional_zone_context generate() "
                "did not return a DataFrame"
            )

        return (
            output
            .copy()
            .reset_index(
                drop=True
            )
        )

    # =========================================================================
    # Zone side-chain safety checks
    # =========================================================================

    @classmethod
    def _assert_zone_events_safe(
        cls,
        zone_events: pd.DataFrame,
    ) -> None:

        cls._assert_no_hindsight(
            zone_events
        )

        required = {
            "iz_event_id",
            "iz_event_flag",
            "iz_live_safe",
        }

        missing = (
            required
            -
            set(
                zone_events.columns
            )
        )

        if missing:
            raise RuntimeError(
                "Institutional-zone causal output missing: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )

        if not zone_events.empty:

            live_safe = (
                pd.to_numeric(
                    zone_events[
                        "iz_live_safe"
                    ],
                    errors="coerce",
                )
                .fillna(
                    0
                )
                .eq(
                    1
                )
            )

            if not bool(
                live_safe.all()
            ):
                raise RuntimeError(
                    "Institutional-zone output is not live safe"
                )

            event_flag = (
                pd.to_numeric(
                    zone_events[
                        "iz_event_flag"
                    ],
                    errors="coerce",
                )
                .fillna(
                    0
                )
                .eq(
                    1
                )
            )

            if not bool(
                event_flag.all()
            ):
                raise RuntimeError(
                    "Institutional-zone output contains "
                    "non-event rows"
                )

    @classmethod
    def _assert_zone_lifecycle_safe(
        cls,
        lifecycle: pd.DataFrame,
    ) -> None:

        cls._assert_no_hindsight(
            lifecycle
        )

        required = {
            "izl_event_id",
            "izl_state",
            "izl_live_safe",
        }

        missing = (
            required
            -
            set(
                lifecycle.columns
            )
        )

        if missing:
            raise RuntimeError(
                "Institutional-zone lifecycle output missing: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )

        if not lifecycle.empty:

            live_safe = (
                pd.to_numeric(
                    lifecycle[
                        "izl_live_safe"
                    ],
                    errors="coerce",
                )
                .fillna(
                    0
                )
                .eq(
                    1
                )
            )

            if not bool(
                live_safe.all()
            ):
                raise RuntimeError(
                    "Institutional-zone lifecycle "
                    "is not live safe"
                )

    # =========================================================================
    # Hindsight protection
    # =========================================================================

    @classmethod
    def _assert_no_hindsight(
        cls,
        frame: pd.DataFrame,
    ) -> None:

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
                "Retrospective research labels are forbidden "
                "in the causal research pipeline: "
                +
                ", ".join(
                    hindsight_columns
                )
            )

    # =========================================================================
    # Final composition
    # =========================================================================

    @staticmethod
    def _research_only_columns(
        canonical: pd.DataFrame,
        enriched: pd.DataFrame,
    ) -> list[Any]:

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
            return canonical_block

        research_block = (
            enriched.loc[
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

        return (
            result
            .copy()
            .reset_index(
                drop=True
            )
        )

    # =========================================================================
    # Metadata
    # =========================================================================

    @classmethod
    def _attach_metadata(
        cls,
        frame: pd.DataFrame,
    ) -> pd.DataFrame:

        metadata = pd.DataFrame(
            {
                "research_pipeline_version": (
                    cls.VERSION
                ),

                "research_pipeline_mode": (
                    cls.MODE
                ),

                "research_stage_count": int(
                    cls.TOTAL_RESEARCH_STAGE_COUNT
                ),

                "research_zone_context_attached": 1,

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

        self._validate_input(
            data
        )

        # =====================================================================
        # 0. Remove stale research and hindsight metadata.
        # =====================================================================

        raw = self._strip_prior_research_columns(
            data
        )

        # =====================================================================
        # 1. Frozen canonical production pipeline.
        # =====================================================================

        canonical = self._run_stage(
            engine=self.production_pipeline,
            data=raw,
            stage_name="canonical_scalping_pipeline",
        )

        # =====================================================================
        # 2-7. Existing aligned causal research chain.
        # =====================================================================

        aligned_stages: tuple[
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
        ) in aligned_stages:

            current = self._run_stage(
                engine=engine,
                data=current,
                stage_name=stage_name,
            )

            self._assert_alignment(
                canonical=canonical,
                enriched=current,
                stage_name=stage_name,
            )

            self._assert_no_hindsight(
                current
            )

        # =====================================================================
        # 8. Causal Institutional Zone events.
        #
        # Use raw market data so event positions map directly to original bars.
        # =====================================================================

        zone_events = self._run_zone_events(
            engine=self.institutional_zones_engine,
            market=raw,
        )

        self._assert_zone_events_safe(
            zone_events
        )

        # =====================================================================
        # 9. Causal Institutional Zone lifecycle.
        # =====================================================================

        zone_lifecycle = self._run_zone_lifecycle(
            engine=self.institutional_zone_lifecycle_engine,
            market=raw,
            zone_events=zone_events,
        )

        self._assert_zone_lifecycle_safe(
            zone_lifecycle
        )

        # =====================================================================
        # 10. Bar-aligned Institutional Zone context.
        #
        # This is deliberately AFTER LEI.
        # =====================================================================

        pre_zone_context = (
            current
            .copy()
            .reset_index(
                drop=True
            )
        )

        current = self._run_zone_context(
            engine=self.institutional_zone_context_engine,
            market=current,
            zone_events=zone_events,
            lifecycle=zone_lifecycle,
        )

        # Zone context must be append-only.
        self._assert_existing_columns_unchanged(
            before=pre_zone_context,
            after=current,
            stage_name="institutional_zone_context",
        )

        self._assert_alignment(
            canonical=canonical,
            enriched=current,
            stage_name="institutional_zone_context",
        )

        self._assert_no_hindsight(
            current
        )

        required_context = {
            "izctx_live_safe",
            "izctx_version",
            "izctx_mode",
        }

        missing_context = (
            required_context
            -
            set(
                current.columns
            )
        )

        if missing_context:
            raise RuntimeError(
                "Institutional-zone context missing columns: "
                +
                ", ".join(
                    sorted(
                        missing_context
                    )
                )
            )

        if not bool(
            pd.to_numeric(
                current[
                    "izctx_live_safe"
                ],
                errors="coerce",
            )
            .fillna(
                0
            )
            .eq(
                1
            )
            .all()
        ):
            raise RuntimeError(
                "Institutional-zone context is not live safe"
            )

        # =====================================================================
        # Final wide-frame composition.
        # =====================================================================

        result = self._compose_final_result(
            canonical=canonical,
            enriched=current,
        )

        self._assert_alignment(
            canonical=canonical,
            enriched=result,
            stage_name="final_research_composition",
        )

        self._assert_no_hindsight(
            result
        )

        # =====================================================================
        # Research metadata.
        # =====================================================================

        result = self._attach_metadata(
            result
        )

        # =====================================================================
        # Final defensive checks.
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


research_intelligence_pipeline = (
    ResearchIntelligencePipeline()
)