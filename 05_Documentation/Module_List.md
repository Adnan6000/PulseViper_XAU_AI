# PulseViper XAU AI
## Current Module Map

This document lists important modules that currently exist in the repository.

---

# 1. Common

## `02_AI/Common/instrument_context.py`

Responsibilities:

- canonical instrument definitions
- broker alias validation
- account/environment identity
- contract identity
- deterministic fingerprints
- instrument scope
- learning scope
- execution scope
- fail-closed mismatch checks

---

# 2. Configuration

## `02_AI/Config/settings.py`

Responsibilities:

- application configuration loading
- YAML configuration integration
- project settings access

---

# 3. Dataset / Instrument Layer

## `02_AI/Dataset/data_fetcher.py`

Responsibilities:

- MetaTrader 5 initialization
- symbol resolution
- historical bar acquisition
- exact resolved-symbol tracking

---

## `02_AI/Dataset/broker_instrument_context_binding.py`

Responsibilities:

- XAUUSD broker evidence
- explicit Gold aliases
- canonical binding
- context creation
- broker metadata validation

---

## `02_AI/Dataset/mt5_read_only_instrument_attestation_adapter.py`

Responsibilities:

- read-only `symbol_info`
- base/profit verification
- contract metadata verification
- volume semantics
- symbol attestation fingerprint

---

## `02_AI/Dataset/instrument_frame_guard.py`

Responsibilities:

- DataFrame instrument identity
- identity columns
- cross-symbol rejection
- exact-context concatenation
- frame validation

---

## `02_AI/Dataset/history_validator.py`

Responsibilities:

- required OHLC fields
- duplicate detection
- null validation
- OHLC relationship validation
- timestamp ordering

---

## `02_AI/Dataset/history_manager.py`

Responsibilities:

- context-aware history building
- exact broker-symbol requests
- timeframe orchestration
- canonical materialization

---

## `02_AI/Dataset/export_dataset.py`

Responsibilities:

- immutable canonical CSV
- manifest generation
- SHA256 verification
- content addressing
- identity-aware persistence

---

## `02_AI/Dataset/training_matrix_builder.py`

Responsibilities:

- historical snapshot loading
- causal base features
- causal HTF alignment
- future-only targets
- chronological split
- purge gaps
- immutable training matrix

---

## `02_AI/Dataset/training_target_relabeler.py`

Responsibilities:

- reuse existing V1 features
- V2 target calibration
- clean LONG / SHORT excursion labels
- meaningful NO_TRADE labeling
- immutable V2 matrix

---

## `02_AI/Dataset/training_feature_enricher.py`

Responsibilities:

- V3 Gold-domain feature generation
- causal market regime
- causal market structure
- BOS context
- FVG context
- causal institutional-zone events

---

# 4. Base Feature Engineering

## `02_AI/Features/feature_generator.py`

Combines base feature modules.

## `02_AI/Features/feature_list.py`

Defines explicit feature ordering.

## `02_AI/Features/trend_features.py`

Trend features.

## `02_AI/Features/momentum_features.py`

Momentum features.

## `02_AI/Features/volatility_features.py`

Volatility features.

## `02_AI/Features/candle_features.py`

Candle morphology and candle-pattern features.

---

# 5. Core Market Intelligence

## `02_AI/Core/market_structure.py`

Adaptive causal swing and structural-state engine.

---

## `02_AI/Core/bos_engine.py`

Break of Structure detection using previously known structure.

---

## `02_AI/Core/liquidity_engine.py`

Liquidity research.

---

## `02_AI/Core/liquidity_sweep_engine.py`

Liquidity sweep detection.

---

## `02_AI/Core/liquidity_sweep_validator.py`

Sweep validation.

---

## `02_AI/Core/liquidity_lifecycle.py`

Liquidity lifecycle state research.

---

## `02_AI/Core/liquidity_structure_intelligence.py`

Higher-level liquidity and structure interaction.

---

## `02_AI/Core/market_context_liquidity.py`

Market-context liquidity research.

---

## `02_AI/Core/displacement_engine.py`

Displacement intelligence.

---

## `02_AI/Core/fvg_engine.py`

Fair Value Gap detection.

---

## `02_AI/Core/fvg_mitigation_engine.py`

FVG mitigation lifecycle.

---

## `02_AI/Core/fvg_quality_engine.py`

FVG quality research.

---

## `02_AI/Core/institutional_zones.py`

Responsibilities:

- causal institutional-zone confirmation
- separate retrospective research labeling

Primary causal interface:

```text
generate()
```

Legacy retrospective interfaces must not be confused with causal ML features.

---

## `02_AI/Core/market_regime.py`

Causal regime metadata.

---

## `02_AI/Core/market_decision_clarity.py`

Market conflict and decision-clarity research.

---

## `02_AI/Core/candle_swing_intelligence.py`

Candle / swing intelligence.

---

## `02_AI/Core/confidence_engine.py`

Confidence aggregation research.

---

## `02_AI/Core/setup_state_engine.py`

Setup-state modeling.

---

## `02_AI/Core/risk_engine.py`

Core deterministic risk logic.

---

# 6. Models

## `02_AI/Models/xauusd_model_trainer.py`

Base XAUUSD model trainer.

Responsibilities:

- exact dataset discovery
- manifest verification
- feature-contract verification
- TRAIN-only scaler fitting
- TRAIN-only model fitting
- probabilities
- confidence
- uncertainty
- metrics
- immutable model persistence

---

## `02_AI/Models/xauusd_model_v2_trainer.py`

Model identity:

```text
XAUUSD_MODEL_v2
```

Uses calibrated V2 training contract.

---

## `02_AI/Models/xauusd_model_v3_trainer.py`

Model identity:

```text
XAUUSD_MODEL_v3
```

Uses V3 domain-enriched training data.

---

# 7. Shadow / Risk Research

Important modules include:

```text
account_protection_guard.py
account_protected_compounding_admission.py
account_protected_execution_lifecycle.py

broker_aware_risk_engine.py
broker_execution_stress_matrix.py

bootstrap_compounding_planner.py
compounding_account_state_adapter.py
compounding_lifecycle_accounting.py
compounding_pnl_ledger.py
compounding_trade_state_machine.py

execution_aware_compounding_admission.py
execution_aware_lifecycle_gate.py
execution_friction_model.py

paper_ledger.py

research_candidate_episode.py
research_candidate_ledger.py
research_intelligence_pipeline.py
research_opportunity_quality.py
research_opportunity_weight_engine.py
research_telemetry.py
```

---

# 8. Execution Evidence

## `forward_execution_evidence_capture.py`

Captures forward execution evidence.

## `forward_demo_execution_evidence_journal.py`

Durable DEMO execution evidence journal.

## `mt5_read_only_fill_telemetry_adapter.py`

Read-only historical fill telemetry.

## `mt5_read_only_completed_fill_adapter.py`

Read-only completed-fill telemetry.

## `realized_execution_cost_accounting.py`

Realized execution-cost calculation.

## `realized_execution_cost_lifecycle_observer.py`

Lifecycle observation for realized cost.

## `realized_fill_telemetry_bridge.py`

Bridges realized broker fill evidence.

## `realized_fill_observation_coordinator.py`

Durable exactly-once observation coordination.

---

# 9. Important Testing / Operation Entry Points

Broker / instrument:

```text
04_Testing/run_exness_demo_xauusd_context_attestation.py
04_Testing/exness_demo_xauusd_context_attestation_operation.py
```

Canonical data:

```text
04_Testing/build_exness_demo_xauusd_canonical_history.py
```

Training:

```text
04_Testing/build_xauusd_training_matrix.py
04_Testing/build_xauusd_training_v2.py
04_Testing/build_xauusd_training_v3.py
```

Model experiments:

```text
04_Testing/train_xauusd_model_v1.py
04_Testing/train_xauusd_model_v2.py
04_Testing/train_xauusd_model_v3.py
```

---

# 10. Documentation Cleanup Rule

Do not document nonexistent modules as implemented.

Old documentation references such as:

```text
pattern_engine.py
market_dna.py
CandleDNAEngine
MarketStructureEngine
```

must not be treated as current implementation unless such files/classes are actually added later.