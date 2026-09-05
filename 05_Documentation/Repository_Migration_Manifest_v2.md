# Repository Migration Manifest V2

This manifest supersedes the original manifest for future repository-structure decisions.

The original manifest remains historical planning evidence and is not modified.

V2 uses source ownership, dynamic-loader evidence, CI references, path-depth risk, frozen lifecycle, and documentation impact.

REVIEW_REQUIRED is an intentional fail-closed state. It must not be treated as approval to move a file.

## Summary

- Scope rows: 174
- READY: 78
- REVIEW_REQUIRED: 77
- FROZEN_STAY: 18
- SUPPORT_STAY: 1
- CI referenced: 21
- Dynamic-loader users: 157
- Parent-depth-sensitive: 68

## Acceptance semantics

- READY means ownership evidence is strong enough to prepare a later migration gate.
- READY does not itself move or authorize execution.
- REVIEW_REQUIRED stays in place until a focused ownership/behavior review resolves it.
- FROZEN_STAY must remain at its compatibility path.
- SUPPORT_STAY remains at the test root.

## READY candidates

| Source | Proposed target | Ownership | CI | Path risk |
|---|---|---|---|---|
| `04_Testing/test_account_protected_compounding_admission.py` | `04_Testing/ai/shadow/test_account_protected_compounding_admission.py` | Shadow | NO | NONE |
| `04_Testing/test_account_protected_execution_lifecycle.py` | `04_Testing/ai/shadow/test_account_protected_execution_lifecycle.py` | Shadow | NO | NONE |
| `04_Testing/test_account_protection_guard.py` | `04_Testing/ai/shadow/test_account_protection_guard.py` | Shadow | NO | NONE |
| `04_Testing/test_backup.py` | `04_Testing/ai/database/test_backup.py` | Database | NO | HIGH |
| `04_Testing/test_bootstrap_compounding_planner.py` | `04_Testing/ai/shadow/test_bootstrap_compounding_planner.py` | Shadow | NO | NONE |
| `04_Testing/test_bos.py` | `04_Testing/ai/core/test_bos.py` | Core | NO | NONE |
| `04_Testing/test_bos_memory.py` | `04_Testing/ai/memory/test_bos_memory.py` | Memory | NO | HIGH |
| `04_Testing/test_candle_swing_intelligence.py` | `04_Testing/ai/core/test_candle_swing_intelligence.py` | Core | YES | NONE |
| `04_Testing/test_canonical_history_pipeline.py` | `04_Testing/ai/dataset/test_canonical_history_pipeline.py` | Dataset | NO | NONE |
| `04_Testing/test_compounding_account_state_adapter.py` | `04_Testing/ai/shadow/test_compounding_account_state_adapter.py` | Shadow | NO | NONE |
| `04_Testing/test_compounding_lifecycle_accounting.py` | `04_Testing/ai/shadow/test_compounding_lifecycle_accounting.py` | Shadow | NO | NONE |
| `04_Testing/test_compounding_pnl_ledger.py` | `04_Testing/ai/shadow/test_compounding_pnl_ledger.py` | Shadow | NO | NONE |
| `04_Testing/test_compounding_risk_watermark.py` | `04_Testing/ai/shadow/test_compounding_risk_watermark.py` | Shadow | NO | NONE |
| `04_Testing/test_compounding_trade_state_machine.py` | `04_Testing/ai/shadow/test_compounding_trade_state_machine.py` | Shadow | NO | NONE |
| `04_Testing/test_confidence.py` | `04_Testing/ai/core/test_confidence.py` | Core | NO | NONE |
| `04_Testing/test_confidence_integration.py` | `04_Testing/ai/core/test_confidence_integration.py` | Core | NO | NONE |
| `04_Testing/test_confidence_pipeline.py` | `04_Testing/ai/core/test_confidence_pipeline.py` | Core | NO | NONE |
| `04_Testing/test_confidence_temporal.py` | `04_Testing/ai/core/test_confidence_temporal.py` | Core | NO | NONE |
| `04_Testing/test_config.py` | `04_Testing/ai/config/test_config.py` | Config | NO | HIGH |
| `04_Testing/test_database.py` | `04_Testing/ai/database/test_database.py` | Database | NO | HIGH |
| `04_Testing/test_enums.py` | `04_Testing/ai/common/test_enums.py` | Common | NO | HIGH |
| `04_Testing/test_execution_aware_compounding_admission.py` | `04_Testing/ai/shadow/test_execution_aware_compounding_admission.py` | Shadow | NO | NONE |
| `04_Testing/test_execution_aware_lifecycle_gate.py` | `04_Testing/ai/shadow/test_execution_aware_lifecycle_gate.py` | Shadow | NO | NONE |
| `04_Testing/test_execution_friction_model.py` | `04_Testing/ai/shadow/test_execution_friction_model.py` | Shadow | NO | NONE |
| `04_Testing/test_exporter.py` | `04_Testing/ai/dataset/test_exporter.py` | Dataset | NO | HIGH |
| `04_Testing/test_feature_list.py` | `04_Testing/ai/features/test_feature_list.py` | Features | NO | HIGH |
| `04_Testing/test_fetcher.py` | `04_Testing/ai/dataset/test_fetcher.py` | Dataset | NO | HIGH |
| `04_Testing/test_forward_demo_execution_evidence_journal.py` | `04_Testing/ai/shadow/test_forward_demo_execution_evidence_journal.py` | Shadow | NO | NONE |
| `04_Testing/test_forward_demo_journal_realized_fill_bridge_integration.py` | `04_Testing/ai/shadow/test_forward_demo_journal_realized_fill_bridge_integration.py` | Shadow | NO | NONE |
| `04_Testing/test_forward_execution_evidence_capture.py` | `04_Testing/ai/shadow/test_forward_execution_evidence_capture.py` | Shadow | NO | NONE |
| `04_Testing/test_fvg.py` | `04_Testing/ai/core/test_fvg.py` | Core | NO | HIGH |
| `04_Testing/test_fvg_mitigation.py` | `04_Testing/ai/core/test_fvg_mitigation.py` | Core | NO | NONE |
| `04_Testing/test_fvg_quality.py` | `04_Testing/ai/core/test_fvg_quality.py` | Core | NO | NONE |
| `04_Testing/test_history_cleaner.py` | `04_Testing/ai/dataset/test_history_cleaner.py` | Dataset | NO | HIGH |
| `04_Testing/test_history_downloader.py` | `04_Testing/ai/dataset/test_history_downloader.py` | Dataset | NO | HIGH |
| `04_Testing/test_history_manager.py` | `04_Testing/ai/dataset/test_history_manager.py` | Dataset | NO | HIGH |
| `04_Testing/test_history_validator.py` | `04_Testing/ai/dataset/test_history_validator.py` | Dataset | NO | HIGH |
| `04_Testing/test_institutional_zone_context.py` | `04_Testing/ai/shadow/test_institutional_zone_context.py` | Shadow | YES | NONE |
| `04_Testing/test_institutional_zone_lifecycle.py` | `04_Testing/ai/shadow/test_institutional_zone_lifecycle.py` | Shadow | YES | NONE |
| `04_Testing/test_institutional_zones.py` | `04_Testing/ai/core/test_institutional_zones.py` | Core | NO | NONE |
| `04_Testing/test_institutional_zones_causal.py` | `04_Testing/ai/core/test_institutional_zones_causal.py` | Core | YES | NONE |
| `04_Testing/test_instrument_context.py` | `04_Testing/ai/common/test_instrument_context.py` | Common | NO | NONE |
| `04_Testing/test_level_entry_intelligence.py` | `04_Testing/ai/core/test_level_entry_intelligence.py` | Core | YES | NONE |
| `04_Testing/test_liquidity_lifecycle.py` | `04_Testing/ai/core/test_liquidity_lifecycle.py` | Core | YES | NONE |
| `04_Testing/test_liquidity_structure_intelligence.py` | `04_Testing/ai/core/test_liquidity_structure_intelligence.py` | Core | YES | NONE |
| `04_Testing/test_liquidity_sweep_validator.py` | `04_Testing/ai/core/test_liquidity_sweep_validator.py` | Core | NO | HIGH |
| `04_Testing/test_market_context_liquidity.py` | `04_Testing/ai/core/test_market_context_liquidity.py` | Core | YES | NONE |
| `04_Testing/test_market_decision_clarity.py` | `04_Testing/ai/core/test_market_decision_clarity.py` | Core | YES | NONE |
| `04_Testing/test_market_regime.py` | `04_Testing/ai/core/test_market_regime.py` | Core | YES | NONE |
| `04_Testing/test_market_structure.py` | `04_Testing/ai/core/test_market_structure.py` | Core | NO | NONE |
| `04_Testing/test_mt5_read_only_completed_fill_adapter.py` | `04_Testing/ai/shadow/test_mt5_read_only_completed_fill_adapter.py` | Shadow | NO | NONE |
| `04_Testing/test_mt5_read_only_fill_telemetry_adapter.py` | `04_Testing/ai/shadow/test_mt5_read_only_fill_telemetry_adapter.py` | Shadow | NO | NONE |
| `04_Testing/test_mt5_read_only_instrument_attestation_adapter.py` | `04_Testing/ai/dataset/test_mt5_read_only_instrument_attestation_adapter.py` | Dataset | NO | NONE |
| `04_Testing/test_paper_ledger.py` | `04_Testing/ai/shadow/test_paper_ledger.py` | Shadow | YES | NONE |
| `04_Testing/test_realized_execution_cost_accounting.py` | `04_Testing/ai/shadow/test_realized_execution_cost_accounting.py` | Shadow | NO | NONE |
| `04_Testing/test_realized_execution_cost_lifecycle_observer.py` | `04_Testing/ai/shadow/test_realized_execution_cost_lifecycle_observer.py` | Shadow | NO | NONE |
| `04_Testing/test_realized_fill_observation_coordinator.py` | `04_Testing/ai/shadow/test_realized_fill_observation_coordinator.py` | Shadow | NO | NONE |
| `04_Testing/test_realized_fill_telemetry_bridge.py` | `04_Testing/ai/shadow/test_realized_fill_telemetry_bridge.py` | Shadow | NO | NONE |
| `04_Testing/test_repository.py` | `04_Testing/ai/database/test_repository.py` | Database | NO | HIGH |
| `04_Testing/test_research_candidate_episode.py` | `04_Testing/ai/shadow/test_research_candidate_episode.py` | Shadow | YES | NONE |
| `04_Testing/test_research_candidate_ledger.py` | `04_Testing/ai/shadow/test_research_candidate_ledger.py` | Shadow | YES | NONE |
| `04_Testing/test_research_intelligence_pipeline.py` | `04_Testing/ai/core/test_research_intelligence_pipeline.py` | Core | YES | NONE |
| `04_Testing/test_research_opportunity_quality.py` | `04_Testing/ai/shadow/test_research_opportunity_quality.py` | Shadow | YES | NONE |
| `04_Testing/test_research_opportunity_weight_engine.py` | `04_Testing/ai/shadow/test_research_opportunity_weight_engine.py` | Shadow | YES | NONE |
| `04_Testing/test_research_telemetry.py` | `04_Testing/ai/shadow/test_research_telemetry.py` | Shadow | YES | NONE |
| `04_Testing/test_research_weight_forward_ledger.py` | `04_Testing/ai/shadow/test_research_weight_forward_ledger.py` | Shadow | YES | NONE |
| `04_Testing/test_research_zone_context_forward_ledger.py` | `04_Testing/ai/shadow/test_research_zone_context_forward_ledger.py` | Shadow | YES | NONE |
| `04_Testing/test_research_zone_context_outcome.py` | `04_Testing/ai/shadow/test_research_zone_context_outcome.py` | Shadow | YES | NONE |
| `04_Testing/test_risk_engine.py` | `04_Testing/ai/core/test_risk_engine.py` | Core | NO | NONE |
| `04_Testing/test_risk_mode_basket_reconciliation.py` | `04_Testing/ai/shadow/test_risk_mode_basket_reconciliation.py` | Shadow | NO | NONE |
| `04_Testing/test_risk_policy_scenario_matrix.py` | `04_Testing/ai/shadow/test_risk_policy_scenario_matrix.py` | Shadow | NO | NONE |
| `04_Testing/test_risk_reconciled_account_protected_lifecycle.py` | `04_Testing/ai/shadow/test_risk_reconciled_account_protected_lifecycle.py` | Shadow | NO | NONE |
| `04_Testing/test_scalping_pipeline.py` | `04_Testing/ai/objects/test_scalping_pipeline.py` | Objects | NO | NONE |
| `04_Testing/test_schema.py` | `04_Testing/ai/database/test_schema.py` | Database | NO | HIGH |
| `04_Testing/test_setup_state.py` | `04_Testing/ai/core/test_setup_state.py` | Core | NO | NONE |
| `04_Testing/test_v1_health.py` | `04_Testing/ai/config/test_v1_health.py` | Config | YES | HIGH |
| `04_Testing/test_xauusd_portable_331_training_input_loader.py` | `04_Testing/ai/dataset/test_xauusd_portable_331_training_input_loader.py` | Dataset | NO | NONE |
| `04_Testing/test_xauusd_portable_training_feature_projector.py` | `04_Testing/ai/dataset/test_xauusd_portable_training_feature_projector.py` | Dataset | NO | NONE |

## Review-required candidates

| Source | Suggested ownership | Confidence | Old classification |
|---|---|---|---|
| `04_Testing/analyze_xauusd_hierarchical_model_v4_stage_b_feature_stability_reduction.py` | research.legacy_ml | MEDIUM | research.legacy_ml |
| `04_Testing/analyze_xauusd_hierarchical_model_v4_stage_b_temporal_robustness.py` | research.legacy_ml | MEDIUM | research.legacy_ml |
| `04_Testing/audit_xauusd_portable_331_train_input_readiness.py` | research.portable_331.train | MEDIUM | research.portable_331.train |
| `04_Testing/build_exness_demo_xauusd_canonical_history.py` | Dataset | MEDIUM | unclassified |
| `04_Testing/build_xauusd_training_matrix.py` | research.legacy_ml | MEDIUM | research.legacy_ml |
| `04_Testing/build_xauusd_training_v2.py` | research.legacy_ml | MEDIUM | research.legacy_ml |
| `04_Testing/build_xauusd_training_v3.py` | research.legacy_ml | MEDIUM | research.legacy_ml |
| `04_Testing/check_symbols.py` | unclassified | LOW | unclassified |
| `04_Testing/check_terminal.py` | unclassified | LOW | unclassified |
| `04_Testing/confidence_v21_research_validation.py` | research.shadow_or_legacy | MEDIUM | research.shadow_or_legacy |
| `04_Testing/confidence_v21_shadow_validation.py` | research.shadow_or_legacy | MEDIUM | research.shadow_or_legacy |
| `04_Testing/confidence_v21_walk_forward_validation.py` | research.shadow_or_legacy | MEDIUM | research.shadow_or_legacy |
| `04_Testing/daily_trade_readiness_diagnostic.py` | Core | MEDIUM | unclassified |
| `04_Testing/design_xauusd_portable_331_train_model_candidate_registry.py` | research.portable_331.train | MEDIUM | research.portable_331.train |
| `04_Testing/design_xauusd_portable_331_train_model_research_protocol.py` | research.portable_331.train | MEDIUM | research.portable_331.train |
| `04_Testing/design_xauusd_portable_331_train_supervised_batch_contract.py` | research.portable_331.train | MEDIUM | research.portable_331.train |
| `04_Testing/design_xauusd_portable_331_train_target_access_contract.py` | research.portable_331.train | MEDIUM | research.portable_331.train |
| `04_Testing/design_xauusd_portable_331_trainer_input_contract.py` | research.portable_331.train | MEDIUM | research.portable_331.train |
| `04_Testing/diagnose_xauusd_portable_331_float_roundtrip.py` | research.portable_331.train | MEDIUM | research.portable_331.train |
| `04_Testing/discover_xauusd_current_feature_pipeline.py` | unclassified | LOW | unclassified |
| `04_Testing/evaluate_xauusd_portable_331_train_model_candidates.py` | research.portable_331.train | MEDIUM | research.portable_331.train |
| `04_Testing/exness_demo_xauusd_context_attestation_operation.py` | Dataset | MEDIUM | unclassified |
| `04_Testing/exness_historical_fill_telemetry_operation.py` | Shadow | MEDIUM | unclassified |
| `04_Testing/fit_xauusd_portable_331_c04_full_train_model.py` | research.portable_331.train | MEDIUM | research.portable_331.train |
| `04_Testing/freeze_xauusd_portable_331_train_internal_winner.py` | research.portable_331.train | MEDIUM | research.portable_331.train |
| `04_Testing/inspect_xauusd_portable_331_candidate_evaluator_integration_contract.py` | research.portable_331.train | MEDIUM | research.portable_331.train |
| `04_Testing/multi_day_scalping_validation.py` | research.shadow_or_legacy | MEDIUM | research.shadow_or_legacy |
| `04_Testing/regime_conditioned_quality_validation.py` | research.shadow_or_legacy | MEDIUM | research.shadow_or_legacy |
| `04_Testing/regime_hypothesis_validation.py` | research.shadow_or_legacy | MEDIUM | research.shadow_or_legacy |
| `04_Testing/research_opportunity_quality_operation.py` | research.shadow_or_legacy | MEDIUM | research.shadow_or_legacy |
| `04_Testing/research_zone_context_outcome_operation.py` | research.shadow_or_legacy | MEDIUM | research.shadow_or_legacy |
| `04_Testing/run_exness_demo_xauusd_context_attestation.py` | unclassified | LOW | unclassified |
| `04_Testing/run_xauusd_portable_331_candidate_evaluator_integration.py` | research.portable_331.train | MEDIUM | research.portable_331.train |
| `04_Testing/run_xauusd_portable_331_train_candidate_walk_forward_evaluation.py` | research.portable_331.train | MEDIUM | research.portable_331.train |
| `04_Testing/run_xauusd_portable_331_train_supervised_batch_integration.py` | research.portable_331.train | MEDIUM | research.portable_331.train |
| `04_Testing/run_xauusd_portable_331_train_target_loader_integration.py` | research.portable_331.train | MEDIUM | research.portable_331.train |
| `04_Testing/run_xauusd_portable_331_training_input_loader_integration.py` | research.portable_331.train | MEDIUM | research.portable_331.train |
| `04_Testing/scalping_setup_outcome_diagnostic.py` | research.shadow_or_legacy | MEDIUM | research.shadow_or_legacy |
| `04_Testing/shadow_bootstrap_compounding_operation.py` | research.shadow_or_legacy | MEDIUM | research.shadow_or_legacy |
| `04_Testing/shadow_compounding_trade_lifecycle_operation.py` | research.shadow_or_legacy | MEDIUM | research.shadow_or_legacy |
| `04_Testing/shadow_paper_operation.py` | research.shadow_or_legacy | MEDIUM | research.shadow_or_legacy |
| `04_Testing/shadow_research_operation.py` | research.shadow_or_legacy | MEDIUM | research.shadow_or_legacy |
| `04_Testing/shadow_weight_forward_operation.py` | research.shadow_or_legacy | MEDIUM | research.shadow_or_legacy |
| `04_Testing/shadow_zone_context_forward_operation.py` | research.shadow_or_legacy | MEDIUM | research.shadow_or_legacy |
| `04_Testing/swing_price_lattice_analysis.py` | research.legacy_ml | MEDIUM | research.legacy_ml |
| `04_Testing/test_candle_features.py` | multi_domain | MEDIUM | runtime.market_intelligence |
| `04_Testing/test_displacement.py` | multi_domain | MEDIUM | runtime.market_intelligence |
| `04_Testing/test_evaluate_xauusd_portable_331_train_model_candidates.py` | unresolved | LOW | research.portable_331.train |
| `04_Testing/test_exness_demo_xauusd_attestation_launcher.py` | unresolved | LOW | runtime.misc |
| `04_Testing/test_exness_demo_xauusd_context_attestation_operation.py` | Common | MEDIUM | runtime.misc |
| `04_Testing/test_exness_demo_xauusd_resolver_readiness.py` | Common | MEDIUM | runtime.misc |
| `04_Testing/test_exness_historical_fill_telemetry_direct_script.py` | unresolved | LOW | runtime.execution_risk |
| `04_Testing/test_exness_historical_fill_telemetry_operation.py` | unresolved | LOW | runtime.execution_risk |
| `04_Testing/test_feature_generator.py` | multi_domain | MEDIUM | runtime.infrastructure |
| `04_Testing/test_fit_xauusd_portable_331_c04_full_train_model.py` | unresolved | LOW | research.portable_331.train |
| `04_Testing/test_freeze_xauusd_portable_331_train_internal_winner.py` | unresolved | LOW | research.portable_331.train |
| `04_Testing/test_instrument_frame_guard.py` | multi_domain | MEDIUM | runtime.misc |
| `04_Testing/test_liquidity.py` | multi_domain | MEDIUM | runtime.market_intelligence |
| `04_Testing/test_liquidity_memory.py` | multi_domain | MEDIUM | runtime.market_intelligence |
| `04_Testing/test_liquidity_object.py` | multi_domain | MEDIUM | runtime.market_intelligence |
| `04_Testing/test_liquidity_sweep.py` | multi_domain | MEDIUM | runtime.market_intelligence |
| `04_Testing/test_momentum_features.py` | multi_domain | MEDIUM | runtime.market_intelligence |
| `04_Testing/test_run_xauusd_portable_331_candidate_evaluator_integration.py` | Common | MEDIUM | research.portable_331.train |
| `04_Testing/test_run_xauusd_portable_331_train_candidate_walk_forward_evaluation.py` | unresolved | LOW | research.portable_331.train |
| `04_Testing/test_trend_features.py` | multi_domain | MEDIUM | runtime.market_intelligence |
| `04_Testing/test_verify_xauusd_portable_331_c04_full_train_model_artifact.py` | unresolved | LOW | research.portable_331.train |
| `04_Testing/test_volatility_features.py` | multi_domain | MEDIUM | runtime.market_intelligence |
| `04_Testing/test_xauusd_hierarchical_model_v4_trainer.py` | multi_domain | MEDIUM | research.legacy_ml |
| `04_Testing/test_xauusd_portable_331_candidate_evaluator_runtime_import.py` | unresolved | LOW | research.portable_331.train |
| `04_Testing/train_xauusd_hierarchical_model_v4.py` | research.legacy_ml | MEDIUM | research.legacy_ml |
| `04_Testing/train_xauusd_model_v1.py` | research.legacy_ml | MEDIUM | research.legacy_ml |
| `04_Testing/train_xauusd_model_v2.py` | research.legacy_ml | MEDIUM | research.legacy_ml |
| `04_Testing/train_xauusd_model_v3.py` | research.legacy_ml | MEDIUM | research.legacy_ml |
| `04_Testing/tune_xauusd_hierarchical_model_v4_stage_b.py` | research.legacy_ml | MEDIUM | research.legacy_ml |
| `04_Testing/verify_xauusd_portable_331_c04_full_train_model_artifact.py` | research.portable_331.train | MEDIUM | research.portable_331.train |
| `test_logger.py` | Utils | MEDIUM | - |
| `test_settings.py` | Config | MEDIUM | - |

## Frozen compatibility

- `04_Testing/design_xauusd_portable_331_one_time_test_protocol.py`
- `04_Testing/design_xauusd_portable_331_one_time_validation_protocol.py`
- `04_Testing/freeze_xauusd_portable_331_one_time_validation_result.py`
- `04_Testing/run_xauusd_portable_331_one_time_test.py`
- `04_Testing/run_xauusd_portable_331_one_time_validation.py`
- `04_Testing/test_design_xauusd_portable_331_one_time_test_protocol.py`
- `04_Testing/test_design_xauusd_portable_331_one_time_validation_protocol.py`
- `04_Testing/test_freeze_xauusd_portable_331_one_time_validation_result.py`
- `04_Testing/test_run_xauusd_portable_331_one_time_test.py`
- `04_Testing/test_run_xauusd_portable_331_one_time_validation.py`
- `04_Testing/test_xauusd_portable_331_authorized_test_source.py`
- `04_Testing/test_xauusd_portable_331_authorized_validation_source.py`
- `04_Testing/test_xauusd_portable_331_one_time_test_core.py`
- `04_Testing/test_xauusd_portable_331_one_time_validation_core.py`
- `04_Testing/xauusd_portable_331_authorized_test_source.py`
- `04_Testing/xauusd_portable_331_authorized_validation_source.py`
- `04_Testing/xauusd_portable_331_one_time_test_core.py`
- `04_Testing/xauusd_portable_331_one_time_validation_core.py`

## Verification contract for later moves

Later migration gates must include syntax parsing, py_compile, focused pytest where applicable, stale path scanning, frozen hash verification, CI path updates, documentation synchronization, and repository-root semantic checks where required.

Permanently consumed one-time VALIDATION and TEST must not be rerun for repository cleanup.
