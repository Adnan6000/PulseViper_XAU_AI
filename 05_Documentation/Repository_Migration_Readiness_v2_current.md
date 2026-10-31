# Repository Migration Readiness V2 - Current State

This report is the current-state companion to the frozen `Repository_Migration_Manifest_v2`.

The frozen V2 manifest remains historical decision evidence and is not rewritten as review execution progresses.

## Current summary

- Executed READY migrations: 78
- Review-executed migrations: 77
- Review required: 0
- Frozen stay: 18
- Support stay: 1
- Total items: 174

## Final Coordinated Review Execution

All 73 remaining `REVIEW_REQUIRED` files have undergone rigorous evidence review, re-verified ownership, taxonomy refinement, reference normalization, and test execution in a single coordinated cleanup pass (Gate `V2-FINAL-COORDINATED-CLEANUP-11`).

### Taxonomy of Relocated Clusters

1. **`04_Testing/integration/` (10 files)**:
   Cross-domain feature and pipeline integration test suites:
   `test_candle_features.py`, `test_displacement.py`, `test_feature_generator.py`, `test_liquidity.py`, `test_liquidity_memory.py`, `test_liquidity_object.py`, `test_liquidity_sweep.py`, `test_momentum_features.py`, `test_trend_features.py`, `test_volatility_features.py`.

2. **`04_Testing/research/portable_331/train/` (24 files)**:
   Research scripts (17) and companion test suites (7) for Portable 331 model candidate training, evaluation, walk-forward validation, and artifact freezing. Preserves intentional sibling `Path(__file__).with_name(...)` contracts while resolving repository root via `_find_repo_root()`.

3. **`04_Testing/research/legacy_ml/` (11 files)**:
   Historical training, feature stability, temporal robustness, and tuning scripts (`train_xauusd_model_v1.py`..`v4`, `tune_xauusd_hierarchical_model_v4_stage_b.py`, etc.).

4. **`04_Testing/research/shadow_experiments/` (9 files)**:
   Experimental shadow paper operations, forward weighting, compounding lifecycle, and setup outcome diagnostics.

5. **`04_Testing/research/legacy_validation/` (6 files)**:
   Historical offline validation workflows (walk-forward, regime-conditioned, multi-day scalping).

6. **`04_Testing/production_portability/` (2 files)**:
   Broker canonical dataset construction (`build_exness_demo_xauusd_canonical_history.py`) and live feature pipeline discovery (`discover_xauusd_current_feature_pipeline.py`).

7. **`04_Testing/diagnostics/` (11 files)**:
   Operational telemetry diagnostics and tests (`exness_historical_fill_telemetry_diagnostic.py`, `test_exness_historical_fill_telemetry_diagnostic.py`, direct script test), context attestation operations and launcher tests, and standalone readiness checks (`daily_trade_readiness_diagnostic.py`, `symbol_specification_diagnostic.py`, `terminal_connection_diagnostic.py`).

### Cleanliness of `04_Testing/` Root

Exactly 19 files remain at `04_Testing/` root:
- **18 `FROZEN_STAY` files**: One-time validation/test holdout scripts (`run_xauusd_portable_331_one_time_validation.py`, etc.) protected against rerun or collection.
- **1 `SUPPORT_STAY` file**: `conftest.py`, providing repository-root discovery fixture and `collect_ignore` guard for all 18 frozen files.
Zero review files, misplaced tests, or unclassified scripts remain at the testing root.

### Frozen Safeguards Compliance

- All 33 frozen compatibility files are 100% byte-identical to baseline.
- `05_Documentation/Repository_Migration_Manifest_v2.csv` and `.md` remain untouched historical evidence.
- Frozen model SHA256 matches: `48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769`.
- Full test suites pass cleanly under project `.venv` (1174 collected tests across active suites).
