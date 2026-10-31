# Repository Migration Manifest

> Generated from the frozen repository testing/evidence inventory.
> This manifest does not execute tests, models, VALIDATION, or TEST.
> This manifest does not move, rename, delete, or rewrite existing artifacts.

## Migration Safety Policy

- Frozen holdout code/evidence remains in its current path.
- Final historical research verdict remains frozen.
- Unclassified files are not automatically moved.
- JSON files with tracked references require reference updates when migrated.
- Python relocation requires an import/path integrity gate before movement.
- No live or shadow deployment is authorized by this migration.

## Actions

| Action | Files |
|---|---:|
| `MOVE_JSON_UPDATE_REFERENCES` | 54 |
| `MOVE_REQUIRES_IMPORT_CHECK` | 184 |
| `STAY_FROZEN` | 32 |
| `STAY_REVIEW_REQUIRED` | 8 |

## Planned Moves by Module

| Module | Files |
|---|---:|
| `production_portability` | 71 |
| `research.legacy_ml` | 15 |
| `research.portable_331.train` | 43 |
| `research.shadow_or_legacy` | 29 |
| `runtime.execution_risk` | 29 |
| `runtime.infrastructure` | 16 |
| `runtime.market_intelligence` | 28 |
| `runtime.misc` | 7 |

## Full Migration Manifest

| Source | Target | Module | Lifecycle | Refs | Action |
|---|---|---|---|---:|---|
| `xauusd_broker_adapter_mt5_integration.json` | `04_Testing/evidence/production_portability/xauusd_broker_adapter_mt5_integration.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_broker_sensitive_feature_actions.json` | `04_Testing/evidence/production_portability/xauusd_broker_sensitive_feature_actions.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 2 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_broker_symbol_portability.json` | `04_Testing/evidence/production_portability/xauusd_broker_symbol_portability.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_broker_symbol_portability_v2.json` | `04_Testing/evidence/production_portability/xauusd_broker_symbol_portability_v2.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_current_broker_d1_availability_alignment.json` | `04_Testing/evidence/production_portability/xauusd_current_broker_d1_availability_alignment.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_current_broker_d1_corrected_portability.json` | `04_Testing/evidence/production_portability/xauusd_current_broker_d1_corrected_portability.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 2 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_current_broker_d1_feature_state_warmup.json` | `04_Testing/evidence/production_portability/xauusd_current_broker_d1_feature_state_warmup.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_current_broker_d1_full_state_recovery.json` | `04_Testing/evidence/production_portability/xauusd_current_broker_d1_full_state_recovery.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_current_broker_d1_h1_reaggregation_boundary.json` | `04_Testing/evidence/production_portability/xauusd_current_broker_d1_h1_reaggregation_boundary.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_current_broker_full_333_evidence_adjudication.json` | `04_Testing/evidence/production_portability/xauusd_current_broker_full_333_evidence_adjudication.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 4 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_current_broker_full_mtf_portability.json` | `04_Testing/evidence/production_portability/xauusd_current_broker_full_mtf_portability.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 3 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_current_broker_h1_session_hour_residual.json` | `04_Testing/evidence/production_portability/xauusd_current_broker_h1_session_hour_residual.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_current_broker_m5_clock_offset.json` | `04_Testing/evidence/production_portability/xauusd_current_broker_m5_clock_offset.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_current_broker_m5_clock_offset_temporal.json` | `04_Testing/evidence/production_portability/xauusd_current_broker_m5_clock_offset_temporal.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_current_broker_m5_clock_transition_dates.json` | `04_Testing/evidence/production_portability/xauusd_current_broker_m5_clock_transition_dates.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_current_broker_m5_clock_transition_intraday.json` | `04_Testing/evidence/production_portability/xauusd_current_broker_m5_clock_transition_intraday.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_current_broker_m5_domain_shift.json` | `04_Testing/evidence/production_portability/xauusd_current_broker_m5_domain_shift.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_current_broker_m5_domain_shift_mapped.json` | `04_Testing/evidence/production_portability/xauusd_current_broker_m5_domain_shift_mapped.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_current_broker_m5_feature_alignment.json` | `04_Testing/evidence/production_portability/xauusd_current_broker_m5_feature_alignment.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_current_broker_m5_feature_availability_lag.json` | `04_Testing/evidence/production_portability/xauusd_current_broker_m5_feature_availability_lag.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_current_broker_m5_raw_ohlc_alignment.json` | `04_Testing/evidence/production_portability/xauusd_current_broker_m5_raw_ohlc_alignment.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_current_feature_pipeline.json` | `04_Testing/evidence/production_portability/xauusd_current_feature_pipeline.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_d1_short_session_state_gap.json` | `04_Testing/evidence/production_portability/xauusd_d1_short_session_state_gap.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_feature_pipeline_contract.json` | `04_Testing/evidence/production_portability/xauusd_feature_pipeline_contract.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_frozen_d1_feature_state_replay.json` | `04_Testing/evidence/production_portability/xauusd_frozen_d1_feature_state_replay.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_frozen_d1_source_aggregation.json` | `04_Testing/evidence/production_portability/xauusd_frozen_d1_source_aggregation.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_frozen_m5_feature_availability_semantics.json` | `04_Testing/evidence/production_portability/xauusd_frozen_m5_feature_availability_semantics.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_full_mtf_portability_contract.json` | `04_Testing/evidence/production_portability/xauusd_full_mtf_portability_contract.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_broker_sensitive_replacements.json` | `04_Testing/evidence/production_portability/xauusd_portable_broker_sensitive_replacements.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 2 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_feature_contract_v1.json` | `04_Testing/evidence/production_portability/xauusd_portable_feature_contract_v1.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_feature_projection_architecture.json` | `04_Testing/evidence/production_portability/xauusd_portable_feature_projection_architecture.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_training_feature_projection.json` | `04_Testing/evidence/production_portability/xauusd_portable_training_feature_projection.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_unclassified_feature_provenance.json` | `04_Testing/evidence/production_portability/xauusd_unclassified_feature_provenance.json` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `v4_stage_b_feature_stability_reduction.json` | `04_Testing/evidence/research/legacy_ml/v4_stage_b_feature_stability_reduction.json` | `research.legacy_ml` | `HISTORICAL` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `v4_stage_b_temporal_robustness.json` | `04_Testing/evidence/research/legacy_ml/v4_stage_b_temporal_robustness.json` | `research.legacy_ml` | `HISTORICAL` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `v4_stage_b_validation_sweep.json` | `04_Testing/evidence/research/legacy_ml/v4_stage_b_validation_sweep.json` | `research.legacy_ml` | `HISTORICAL` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_331_authorized_test_source_attestation.json` | `04_Testing/evidence/research/portable_331/train/xauusd_portable_331_authorized_test_source_attestation.json` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 3 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_331_authorized_validation_source_attestation.json` | `04_Testing/evidence/research/portable_331/train/xauusd_portable_331_authorized_validation_source_attestation.json` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 4 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_331_c04_full_train_model_artifact_verification.json` | `04_Testing/evidence/research/portable_331/train/xauusd_portable_331_c04_full_train_model_artifact_verification.json` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 5 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_331_c04_full_train_model_fit.json` | `04_Testing/evidence/research/portable_331/train/xauusd_portable_331_c04_full_train_model_fit.json` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 4 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_331_candidate_evaluator_integration.json` | `04_Testing/evidence/research/portable_331/train/xauusd_portable_331_candidate_evaluator_integration.json` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 3 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_331_candidate_evaluator_integration_contract.json` | `04_Testing/evidence/research/portable_331/train/xauusd_portable_331_candidate_evaluator_integration_contract.json` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 2 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_331_float_roundtrip.json` | `04_Testing/evidence/research/portable_331/train/xauusd_portable_331_float_roundtrip.json` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_331_train_input_readiness.json` | `04_Testing/evidence/research/portable_331/train/xauusd_portable_331_train_input_readiness.json` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 2 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_331_train_internal_winner_freeze.json` | `04_Testing/evidence/research/portable_331/train/xauusd_portable_331_train_internal_winner_freeze.json` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 5 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_331_train_model_candidate_registry_design.json` | `04_Testing/evidence/research/portable_331/train/xauusd_portable_331_train_model_candidate_registry_design.json` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 9 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_331_train_model_candidate_walk_forward_evaluation.json` | `04_Testing/evidence/research/portable_331/train/xauusd_portable_331_train_model_candidate_walk_forward_evaluation.json` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 5 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_331_train_model_research_protocol_design.json` | `04_Testing/evidence/research/portable_331/train/xauusd_portable_331_train_model_research_protocol_design.json` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 5 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_331_train_supervised_batch_contract_design.json` | `04_Testing/evidence/research/portable_331/train/xauusd_portable_331_train_supervised_batch_contract_design.json` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_331_train_supervised_batch_integration.json` | `04_Testing/evidence/research/portable_331/train/xauusd_portable_331_train_supervised_batch_integration.json` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 3 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_331_train_target_access_contract_design.json` | `04_Testing/evidence/research/portable_331/train/xauusd_portable_331_train_target_access_contract_design.json` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_331_train_target_loader_integration.json` | `04_Testing/evidence/research/portable_331/train/xauusd_portable_331_train_target_loader_integration.json` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 2 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_331_trainer_input_contract_design.json` | `04_Testing/evidence/research/portable_331/train/xauusd_portable_331_trainer_input_contract_design.json` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_JSON_UPDATE_REFERENCES` |
| `xauusd_portable_331_training_input_loader_integration.json` | `04_Testing/evidence/research/portable_331/train/xauusd_portable_331_training_input_loader_integration.json` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 2 | `MOVE_JSON_UPDATE_REFERENCES` |
| `04_Testing/adjudicate_xauusd_broker_sensitive_feature_actions.py` | `04_Testing/production_portability/adjudicate_xauusd_broker_sensitive_feature_actions.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/adjudicate_xauusd_current_broker_full_333_portability.py` | `04_Testing/production_portability/adjudicate_xauusd_current_broker_full_333_portability.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/analyze_xauusd_broker_symbol_portability.py` | `04_Testing/production_portability/analyze_xauusd_broker_symbol_portability.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/analyze_xauusd_current_broker_domain_shift.py` | `04_Testing/production_portability/analyze_xauusd_current_broker_domain_shift.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/analyze_xauusd_current_broker_full_mtf_portability.py` | `04_Testing/production_portability/analyze_xauusd_current_broker_full_mtf_portability.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/analyze_xauusd_current_broker_m5_domain_shift.py` | `04_Testing/production_portability/analyze_xauusd_current_broker_m5_domain_shift.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/analyze_xauusd_current_broker_m5_domain_shift_mapped.py` | `04_Testing/production_portability/analyze_xauusd_current_broker_m5_domain_shift_mapped.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/audit_xauusd_current_broker_d1_corrected_portability.py` | `04_Testing/production_portability/audit_xauusd_current_broker_d1_corrected_portability.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/audit_xauusd_portable_broker_sensitive_replacements.py` | `04_Testing/production_portability/audit_xauusd_portable_broker_sensitive_replacements.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/design_xauusd_portable_feature_contract_v1.py` | `04_Testing/production_portability/design_xauusd_portable_feature_contract_v1.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/diagnose_xauusd_current_broker_d1_availability_alignment.py` | `04_Testing/production_portability/diagnose_xauusd_current_broker_d1_availability_alignment.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/diagnose_xauusd_current_broker_d1_feature_state_warmup.py` | `04_Testing/production_portability/diagnose_xauusd_current_broker_d1_feature_state_warmup.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/diagnose_xauusd_current_broker_d1_full_state_recovery.py` | `04_Testing/production_portability/diagnose_xauusd_current_broker_d1_full_state_recovery.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/diagnose_xauusd_current_broker_d1_h1_reaggregation_boundary.py` | `04_Testing/production_portability/diagnose_xauusd_current_broker_d1_h1_reaggregation_boundary.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/diagnose_xauusd_current_broker_h1_session_hour_residual.py` | `04_Testing/production_portability/diagnose_xauusd_current_broker_h1_session_hour_residual.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/diagnose_xauusd_current_broker_m5_clock_offset.py` | `04_Testing/production_portability/diagnose_xauusd_current_broker_m5_clock_offset.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/diagnose_xauusd_current_broker_m5_clock_offset_temporal.py` | `04_Testing/production_portability/diagnose_xauusd_current_broker_m5_clock_offset_temporal.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/diagnose_xauusd_current_broker_m5_clock_transition_dates.py` | `04_Testing/production_portability/diagnose_xauusd_current_broker_m5_clock_transition_dates.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/diagnose_xauusd_current_broker_m5_clock_transition_intraday.py` | `04_Testing/production_portability/diagnose_xauusd_current_broker_m5_clock_transition_intraday.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/diagnose_xauusd_current_broker_m5_feature_alignment.py` | `04_Testing/production_portability/diagnose_xauusd_current_broker_m5_feature_alignment.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/diagnose_xauusd_current_broker_m5_feature_availability_lag.py` | `04_Testing/production_portability/diagnose_xauusd_current_broker_m5_feature_availability_lag.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/diagnose_xauusd_current_broker_m5_raw_ohlc_alignment.py` | `04_Testing/production_portability/diagnose_xauusd_current_broker_m5_raw_ohlc_alignment.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/diagnose_xauusd_d1_short_session_state_gap.py` | `04_Testing/production_portability/diagnose_xauusd_d1_short_session_state_gap.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/diagnose_xauusd_frozen_d1_feature_state_replay.py` | `04_Testing/production_portability/diagnose_xauusd_frozen_d1_feature_state_replay.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/diagnose_xauusd_frozen_d1_source_aggregation.py` | `04_Testing/production_portability/diagnose_xauusd_frozen_d1_source_aggregation.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/diagnose_xauusd_frozen_m5_feature_availability_semantics.py` | `04_Testing/production_portability/diagnose_xauusd_frozen_m5_feature_availability_semantics.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/exness_broker_calibration_operation.py` | `04_Testing/production_portability/exness_broker_calibration_operation.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/inspect_xauusd_feature_pipeline_contract.py` | `04_Testing/production_portability/inspect_xauusd_feature_pipeline_contract.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/inspect_xauusd_full_mtf_portability_contract.py` | `04_Testing/production_portability/inspect_xauusd_full_mtf_portability_contract.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/inspect_xauusd_portable_feature_projection_architecture.py` | `04_Testing/production_portability/inspect_xauusd_portable_feature_projection_architecture.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/inspect_xauusd_unclassified_feature_provenance.py` | `04_Testing/production_portability/inspect_xauusd_unclassified_feature_provenance.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/run_xauusd_portable_training_feature_projection.py` | `04_Testing/production_portability/run_xauusd_portable_training_feature_projection.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/shadow_broker_aware_risk_operation.py` | `04_Testing/production_portability/shadow_broker_aware_risk_operation.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_broker_aware_risk_engine.py` | `04_Testing/production_portability/test_broker_aware_risk_engine.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_broker_execution_stress_matrix.py` | `04_Testing/production_portability/test_broker_execution_stress_matrix.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_broker_instrument_context_binding.py` | `04_Testing/production_portability/test_broker_instrument_context_binding.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_xauusd_broker_adapter.py` | `04_Testing/production_portability/test_xauusd_broker_adapter.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/verify_xauusd_broker_adapter_mt5.py` | `04_Testing/production_portability/verify_xauusd_broker_adapter_mt5.py` | `production_portability` | `ACTIVE_GATE_13_INPUT` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/analyze_xauusd_hierarchical_model_v4_stage_b_feature_stability_reduction.py` | `04_Testing/research/legacy_ml/analyze_xauusd_hierarchical_model_v4_stage_b_feature_stability_reduction.py` | `research.legacy_ml` | `HISTORICAL` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/analyze_xauusd_hierarchical_model_v4_stage_b_temporal_robustness.py` | `04_Testing/research/legacy_ml/analyze_xauusd_hierarchical_model_v4_stage_b_temporal_robustness.py` | `research.legacy_ml` | `HISTORICAL` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/build_xauusd_training_matrix.py` | `04_Testing/research/legacy_ml/build_xauusd_training_matrix.py` | `research.legacy_ml` | `HISTORICAL` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/build_xauusd_training_v2.py` | `04_Testing/research/legacy_ml/build_xauusd_training_v2.py` | `research.legacy_ml` | `HISTORICAL` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/build_xauusd_training_v3.py` | `04_Testing/research/legacy_ml/build_xauusd_training_v3.py` | `research.legacy_ml` | `HISTORICAL` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/swing_price_lattice_analysis.py` | `04_Testing/research/legacy_ml/swing_price_lattice_analysis.py` | `research.legacy_ml` | `HISTORICAL` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_xauusd_hierarchical_model_v4_trainer.py` | `04_Testing/research/legacy_ml/test_xauusd_hierarchical_model_v4_trainer.py` | `research.legacy_ml` | `HISTORICAL` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/train_xauusd_hierarchical_model_v4.py` | `04_Testing/research/legacy_ml/train_xauusd_hierarchical_model_v4.py` | `research.legacy_ml` | `HISTORICAL` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/train_xauusd_model_v1.py` | `04_Testing/research/legacy_ml/train_xauusd_model_v1.py` | `research.legacy_ml` | `HISTORICAL` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/train_xauusd_model_v2.py` | `04_Testing/research/legacy_ml/train_xauusd_model_v2.py` | `research.legacy_ml` | `HISTORICAL` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/train_xauusd_model_v3.py` | `04_Testing/research/legacy_ml/train_xauusd_model_v3.py` | `research.legacy_ml` | `HISTORICAL` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/tune_xauusd_hierarchical_model_v4_stage_b.py` | `04_Testing/research/legacy_ml/tune_xauusd_hierarchical_model_v4_stage_b.py` | `research.legacy_ml` | `HISTORICAL` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/audit_xauusd_portable_331_train_input_readiness.py` | `04_Testing/research/portable_331/train/audit_xauusd_portable_331_train_input_readiness.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/design_xauusd_portable_331_train_model_candidate_registry.py` | `04_Testing/research/portable_331/train/design_xauusd_portable_331_train_model_candidate_registry.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/design_xauusd_portable_331_train_model_research_protocol.py` | `04_Testing/research/portable_331/train/design_xauusd_portable_331_train_model_research_protocol.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/design_xauusd_portable_331_train_supervised_batch_contract.py` | `04_Testing/research/portable_331/train/design_xauusd_portable_331_train_supervised_batch_contract.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/design_xauusd_portable_331_train_target_access_contract.py` | `04_Testing/research/portable_331/train/design_xauusd_portable_331_train_target_access_contract.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/design_xauusd_portable_331_trainer_input_contract.py` | `04_Testing/research/portable_331/train/design_xauusd_portable_331_trainer_input_contract.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/diagnose_xauusd_portable_331_float_roundtrip.py` | `04_Testing/research/portable_331/train/diagnose_xauusd_portable_331_float_roundtrip.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/evaluate_xauusd_portable_331_train_model_candidates.py` | `04_Testing/research/portable_331/train/evaluate_xauusd_portable_331_train_model_candidates.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 5 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/fit_xauusd_portable_331_c04_full_train_model.py` | `04_Testing/research/portable_331/train/fit_xauusd_portable_331_c04_full_train_model.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 3 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/freeze_xauusd_portable_331_train_internal_winner.py` | `04_Testing/research/portable_331/train/freeze_xauusd_portable_331_train_internal_winner.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/inspect_xauusd_portable_331_candidate_evaluator_integration_contract.py` | `04_Testing/research/portable_331/train/inspect_xauusd_portable_331_candidate_evaluator_integration_contract.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/run_xauusd_portable_331_candidate_evaluator_integration.py` | `04_Testing/research/portable_331/train/run_xauusd_portable_331_candidate_evaluator_integration.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/run_xauusd_portable_331_train_candidate_walk_forward_evaluation.py` | `04_Testing/research/portable_331/train/run_xauusd_portable_331_train_candidate_walk_forward_evaluation.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/run_xauusd_portable_331_train_supervised_batch_integration.py` | `04_Testing/research/portable_331/train/run_xauusd_portable_331_train_supervised_batch_integration.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/run_xauusd_portable_331_train_target_loader_integration.py` | `04_Testing/research/portable_331/train/run_xauusd_portable_331_train_target_loader_integration.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/run_xauusd_portable_331_training_input_loader_integration.py` | `04_Testing/research/portable_331/train/run_xauusd_portable_331_training_input_loader_integration.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_evaluate_xauusd_portable_331_train_model_candidates.py` | `04_Testing/research/portable_331/train/test_evaluate_xauusd_portable_331_train_model_candidates.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_fit_xauusd_portable_331_c04_full_train_model.py` | `04_Testing/research/portable_331/train/test_fit_xauusd_portable_331_c04_full_train_model.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_freeze_xauusd_portable_331_train_internal_winner.py` | `04_Testing/research/portable_331/train/test_freeze_xauusd_portable_331_train_internal_winner.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_run_xauusd_portable_331_candidate_evaluator_integration.py` | `04_Testing/research/portable_331/train/test_run_xauusd_portable_331_candidate_evaluator_integration.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_run_xauusd_portable_331_train_candidate_walk_forward_evaluation.py` | `04_Testing/research/portable_331/train/test_run_xauusd_portable_331_train_candidate_walk_forward_evaluation.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_verify_xauusd_portable_331_c04_full_train_model_artifact.py` | `04_Testing/research/portable_331/train/test_verify_xauusd_portable_331_c04_full_train_model_artifact.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_xauusd_portable_331_candidate_evaluator_runtime_import.py` | `04_Testing/research/portable_331/train/test_xauusd_portable_331_candidate_evaluator_runtime_import.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_xauusd_portable_331_training_input_loader.py` | `04_Testing/research/portable_331/train/test_xauusd_portable_331_training_input_loader.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/verify_xauusd_portable_331_c04_full_train_model_artifact.py` | `04_Testing/research/portable_331/train/verify_xauusd_portable_331_c04_full_train_model_artifact.py` | `research.portable_331.train` | `HISTORICAL_FROZEN` | 3 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/confidence_v21_research_validation.py` | `04_Testing/research/shadow_or_legacy/confidence_v21_research_validation.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/confidence_v21_shadow_validation.py` | `04_Testing/research/shadow_or_legacy/confidence_v21_shadow_validation.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/confidence_v21_walk_forward_validation.py` | `04_Testing/research/shadow_or_legacy/confidence_v21_walk_forward_validation.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/multi_day_scalping_validation.py` | `04_Testing/research/shadow_or_legacy/multi_day_scalping_validation.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/regime_conditioned_quality_validation.py` | `04_Testing/research/shadow_or_legacy/regime_conditioned_quality_validation.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/regime_hypothesis_validation.py` | `04_Testing/research/shadow_or_legacy/regime_hypothesis_validation.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/research_opportunity_quality_operation.py` | `04_Testing/research/shadow_or_legacy/research_opportunity_quality_operation.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/research_zone_context_outcome_operation.py` | `04_Testing/research/shadow_or_legacy/research_zone_context_outcome_operation.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/scalping_setup_outcome_diagnostic.py` | `04_Testing/research/shadow_or_legacy/scalping_setup_outcome_diagnostic.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/shadow_bootstrap_compounding_operation.py` | `04_Testing/research/shadow_or_legacy/shadow_bootstrap_compounding_operation.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/shadow_compounding_trade_lifecycle_operation.py` | `04_Testing/research/shadow_or_legacy/shadow_compounding_trade_lifecycle_operation.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/shadow_paper_operation.py` | `04_Testing/research/shadow_or_legacy/shadow_paper_operation.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/shadow_research_operation.py` | `04_Testing/research/shadow_or_legacy/shadow_research_operation.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/shadow_weight_forward_operation.py` | `04_Testing/research/shadow_or_legacy/shadow_weight_forward_operation.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/shadow_zone_context_forward_operation.py` | `04_Testing/research/shadow_or_legacy/shadow_zone_context_forward_operation.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_confidence.py` | `04_Testing/research/shadow_or_legacy/test_confidence.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_confidence_integration.py` | `04_Testing/research/shadow_or_legacy/test_confidence_integration.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_confidence_pipeline.py` | `04_Testing/research/shadow_or_legacy/test_confidence_pipeline.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_confidence_temporal.py` | `04_Testing/research/shadow_or_legacy/test_confidence_temporal.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_research_candidate_episode.py` | `04_Testing/research/shadow_or_legacy/test_research_candidate_episode.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_research_candidate_ledger.py` | `04_Testing/research/shadow_or_legacy/test_research_candidate_ledger.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_research_intelligence_pipeline.py` | `04_Testing/research/shadow_or_legacy/test_research_intelligence_pipeline.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_research_opportunity_quality.py` | `04_Testing/research/shadow_or_legacy/test_research_opportunity_quality.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_research_opportunity_weight_engine.py` | `04_Testing/research/shadow_or_legacy/test_research_opportunity_weight_engine.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_research_telemetry.py` | `04_Testing/research/shadow_or_legacy/test_research_telemetry.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_research_weight_forward_ledger.py` | `04_Testing/research/shadow_or_legacy/test_research_weight_forward_ledger.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_research_zone_context_forward_ledger.py` | `04_Testing/research/shadow_or_legacy/test_research_zone_context_forward_ledger.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_research_zone_context_outcome.py` | `04_Testing/research/shadow_or_legacy/test_research_zone_context_outcome.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_scalping_pipeline.py` | `04_Testing/research/shadow_or_legacy/test_scalping_pipeline.py` | `research.shadow_or_legacy` | `HISTORICAL_OR_SHADOW` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_account_protected_compounding_admission.py` | `04_Testing/runtime/execution_risk/test_account_protected_compounding_admission.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_account_protected_execution_lifecycle.py` | `04_Testing/runtime/execution_risk/test_account_protected_execution_lifecycle.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_account_protection_guard.py` | `04_Testing/runtime/execution_risk/test_account_protection_guard.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_bootstrap_compounding_planner.py` | `04_Testing/runtime/execution_risk/test_bootstrap_compounding_planner.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_compounding_account_state_adapter.py` | `04_Testing/runtime/execution_risk/test_compounding_account_state_adapter.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_compounding_lifecycle_accounting.py` | `04_Testing/runtime/execution_risk/test_compounding_lifecycle_accounting.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_compounding_pnl_ledger.py` | `04_Testing/runtime/execution_risk/test_compounding_pnl_ledger.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_compounding_risk_watermark.py` | `04_Testing/runtime/execution_risk/test_compounding_risk_watermark.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_compounding_trade_state_machine.py` | `04_Testing/runtime/execution_risk/test_compounding_trade_state_machine.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_execution_aware_compounding_admission.py` | `04_Testing/runtime/execution_risk/test_execution_aware_compounding_admission.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_execution_aware_lifecycle_gate.py` | `04_Testing/runtime/execution_risk/test_execution_aware_lifecycle_gate.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_execution_friction_model.py` | `04_Testing/runtime/execution_risk/test_execution_friction_model.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_exness_historical_fill_telemetry_direct_script.py` | `04_Testing/runtime/execution_risk/test_exness_historical_fill_telemetry_direct_script.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_exness_historical_fill_telemetry_operation.py` | `04_Testing/runtime/execution_risk/test_exness_historical_fill_telemetry_operation.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_forward_demo_execution_evidence_journal.py` | `04_Testing/runtime/execution_risk/test_forward_demo_execution_evidence_journal.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_forward_demo_journal_realized_fill_bridge_integration.py` | `04_Testing/runtime/execution_risk/test_forward_demo_journal_realized_fill_bridge_integration.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_forward_execution_evidence_capture.py` | `04_Testing/runtime/execution_risk/test_forward_execution_evidence_capture.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_instrument_context.py` | `04_Testing/runtime/execution_risk/test_instrument_context.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_mt5_read_only_completed_fill_adapter.py` | `04_Testing/runtime/execution_risk/test_mt5_read_only_completed_fill_adapter.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_mt5_read_only_fill_telemetry_adapter.py` | `04_Testing/runtime/execution_risk/test_mt5_read_only_fill_telemetry_adapter.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_paper_ledger.py` | `04_Testing/runtime/execution_risk/test_paper_ledger.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_realized_execution_cost_accounting.py` | `04_Testing/runtime/execution_risk/test_realized_execution_cost_accounting.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_realized_execution_cost_lifecycle_observer.py` | `04_Testing/runtime/execution_risk/test_realized_execution_cost_lifecycle_observer.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_realized_fill_observation_coordinator.py` | `04_Testing/runtime/execution_risk/test_realized_fill_observation_coordinator.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_realized_fill_telemetry_bridge.py` | `04_Testing/runtime/execution_risk/test_realized_fill_telemetry_bridge.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_risk_engine.py` | `04_Testing/runtime/execution_risk/test_risk_engine.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_risk_mode_basket_reconciliation.py` | `04_Testing/runtime/execution_risk/test_risk_mode_basket_reconciliation.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_risk_policy_scenario_matrix.py` | `04_Testing/runtime/execution_risk/test_risk_policy_scenario_matrix.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_risk_reconciled_account_protected_lifecycle.py` | `04_Testing/runtime/execution_risk/test_risk_reconciled_account_protected_lifecycle.py` | `runtime.execution_risk` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_backup.py` | `04_Testing/runtime/infrastructure/test_backup.py` | `runtime.infrastructure` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_canonical_history_pipeline.py` | `04_Testing/runtime/infrastructure/test_canonical_history_pipeline.py` | `runtime.infrastructure` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_config.py` | `04_Testing/runtime/infrastructure/test_config.py` | `runtime.infrastructure` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_database.py` | `04_Testing/runtime/infrastructure/test_database.py` | `runtime.infrastructure` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_enums.py` | `04_Testing/runtime/infrastructure/test_enums.py` | `runtime.infrastructure` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_exporter.py` | `04_Testing/runtime/infrastructure/test_exporter.py` | `runtime.infrastructure` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_feature_generator.py` | `04_Testing/runtime/infrastructure/test_feature_generator.py` | `runtime.infrastructure` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_feature_list.py` | `04_Testing/runtime/infrastructure/test_feature_list.py` | `runtime.infrastructure` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_fetcher.py` | `04_Testing/runtime/infrastructure/test_fetcher.py` | `runtime.infrastructure` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_history_cleaner.py` | `04_Testing/runtime/infrastructure/test_history_cleaner.py` | `runtime.infrastructure` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_history_downloader.py` | `04_Testing/runtime/infrastructure/test_history_downloader.py` | `runtime.infrastructure` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_history_manager.py` | `04_Testing/runtime/infrastructure/test_history_manager.py` | `runtime.infrastructure` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_history_validator.py` | `04_Testing/runtime/infrastructure/test_history_validator.py` | `runtime.infrastructure` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_repository.py` | `04_Testing/runtime/infrastructure/test_repository.py` | `runtime.infrastructure` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_schema.py` | `04_Testing/runtime/infrastructure/test_schema.py` | `runtime.infrastructure` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_v1_health.py` | `04_Testing/runtime/infrastructure/test_v1_health.py` | `runtime.infrastructure` | `ACTIVE_REGRESSION` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_bos.py` | `04_Testing/runtime/market_intelligence/test_bos.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_bos_memory.py` | `04_Testing/runtime/market_intelligence/test_bos_memory.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_candle_features.py` | `04_Testing/runtime/market_intelligence/test_candle_features.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_candle_swing_intelligence.py` | `04_Testing/runtime/market_intelligence/test_candle_swing_intelligence.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_displacement.py` | `04_Testing/runtime/market_intelligence/test_displacement.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_fvg.py` | `04_Testing/runtime/market_intelligence/test_fvg.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_fvg_mitigation.py` | `04_Testing/runtime/market_intelligence/test_fvg_mitigation.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_fvg_quality.py` | `04_Testing/runtime/market_intelligence/test_fvg_quality.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_institutional_zone_context.py` | `04_Testing/runtime/market_intelligence/test_institutional_zone_context.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_institutional_zone_lifecycle.py` | `04_Testing/runtime/market_intelligence/test_institutional_zone_lifecycle.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_institutional_zones.py` | `04_Testing/runtime/market_intelligence/test_institutional_zones.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_institutional_zones_causal.py` | `04_Testing/runtime/market_intelligence/test_institutional_zones_causal.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_level_entry_intelligence.py` | `04_Testing/runtime/market_intelligence/test_level_entry_intelligence.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_liquidity.py` | `04_Testing/runtime/market_intelligence/test_liquidity.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_liquidity_lifecycle.py` | `04_Testing/runtime/market_intelligence/test_liquidity_lifecycle.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_liquidity_memory.py` | `04_Testing/runtime/market_intelligence/test_liquidity_memory.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_liquidity_object.py` | `04_Testing/runtime/market_intelligence/test_liquidity_object.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_liquidity_structure_intelligence.py` | `04_Testing/runtime/market_intelligence/test_liquidity_structure_intelligence.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_liquidity_sweep.py` | `04_Testing/runtime/market_intelligence/test_liquidity_sweep.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_liquidity_sweep_validator.py` | `04_Testing/runtime/market_intelligence/test_liquidity_sweep_validator.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_market_context_liquidity.py` | `04_Testing/runtime/market_intelligence/test_market_context_liquidity.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_market_decision_clarity.py` | `04_Testing/runtime/market_intelligence/test_market_decision_clarity.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_market_regime.py` | `04_Testing/runtime/market_intelligence/test_market_regime.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 2 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_market_structure.py` | `04_Testing/runtime/market_intelligence/test_market_structure.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_momentum_features.py` | `04_Testing/runtime/market_intelligence/test_momentum_features.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_setup_state.py` | `04_Testing/runtime/market_intelligence/test_setup_state.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_trend_features.py` | `04_Testing/runtime/market_intelligence/test_trend_features.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_volatility_features.py` | `04_Testing/runtime/market_intelligence/test_volatility_features.py` | `runtime.market_intelligence` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/conftest.py` | `04_Testing/runtime/misc/conftest.py` | `runtime.misc` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_exness_demo_xauusd_attestation_launcher.py` | `04_Testing/runtime/misc/test_exness_demo_xauusd_attestation_launcher.py` | `runtime.misc` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_exness_demo_xauusd_context_attestation_operation.py` | `04_Testing/runtime/misc/test_exness_demo_xauusd_context_attestation_operation.py` | `runtime.misc` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_exness_demo_xauusd_resolver_readiness.py` | `04_Testing/runtime/misc/test_exness_demo_xauusd_resolver_readiness.py` | `runtime.misc` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_instrument_frame_guard.py` | `04_Testing/runtime/misc/test_instrument_frame_guard.py` | `runtime.misc` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_mt5_read_only_instrument_attestation_adapter.py` | `04_Testing/runtime/misc/test_mt5_read_only_instrument_attestation_adapter.py` | `runtime.misc` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `04_Testing/test_xauusd_portable_training_feature_projector.py` | `04_Testing/runtime/misc/test_xauusd_portable_training_feature_projector.py` | `runtime.misc` | `ACTIVE_REGRESSION` | 1 | `MOVE_REQUIRES_IMPORT_CHECK` |
| `xauusd_portable_331_final_historical_research_verdict.json` | `xauusd_portable_331_final_historical_research_verdict.json` | `research.portable_331.final` | `FROZEN_FINAL_VERDICT` | 2 | `STAY_FROZEN` |
| `04_Testing/design_xauusd_portable_331_one_time_test_protocol.py` | `04_Testing/design_xauusd_portable_331_one_time_test_protocol.py` | `research.portable_331.holdout` | `FROZEN_HOLDOUT` | 1 | `STAY_FROZEN` |
| `04_Testing/design_xauusd_portable_331_one_time_validation_protocol.py` | `04_Testing/design_xauusd_portable_331_one_time_validation_protocol.py` | `research.portable_331.holdout` | `FROZEN_HOLDOUT` | 3 | `STAY_FROZEN` |
| `04_Testing/freeze_xauusd_portable_331_one_time_validation_result.py` | `04_Testing/freeze_xauusd_portable_331_one_time_validation_result.py` | `research.portable_331.holdout` | `FROZEN_HOLDOUT` | 3 | `STAY_FROZEN` |
| `04_Testing/run_xauusd_portable_331_one_time_test.py` | `04_Testing/run_xauusd_portable_331_one_time_test.py` | `research.portable_331.holdout` | `FROZEN_HOLDOUT` | 1 | `STAY_FROZEN` |
| `04_Testing/run_xauusd_portable_331_one_time_validation.py` | `04_Testing/run_xauusd_portable_331_one_time_validation.py` | `research.portable_331.holdout` | `FROZEN_HOLDOUT` | 3 | `STAY_FROZEN` |
| `04_Testing/test_design_xauusd_portable_331_one_time_test_protocol.py` | `04_Testing/test_design_xauusd_portable_331_one_time_test_protocol.py` | `research.portable_331.holdout` | `FROZEN_HOLDOUT` | 1 | `STAY_FROZEN` |
| `04_Testing/test_design_xauusd_portable_331_one_time_validation_protocol.py` | `04_Testing/test_design_xauusd_portable_331_one_time_validation_protocol.py` | `research.portable_331.holdout` | `FROZEN_HOLDOUT` | 1 | `STAY_FROZEN` |
| `04_Testing/test_freeze_xauusd_portable_331_one_time_validation_result.py` | `04_Testing/test_freeze_xauusd_portable_331_one_time_validation_result.py` | `research.portable_331.holdout` | `FROZEN_HOLDOUT` | 1 | `STAY_FROZEN` |
| `04_Testing/test_run_xauusd_portable_331_one_time_test.py` | `04_Testing/test_run_xauusd_portable_331_one_time_test.py` | `research.portable_331.holdout` | `FROZEN_HOLDOUT` | 1 | `STAY_FROZEN` |
| `04_Testing/test_run_xauusd_portable_331_one_time_validation.py` | `04_Testing/test_run_xauusd_portable_331_one_time_validation.py` | `research.portable_331.holdout` | `FROZEN_HOLDOUT` | 1 | `STAY_FROZEN` |
| `04_Testing/test_xauusd_portable_331_authorized_test_source.py` | `04_Testing/test_xauusd_portable_331_authorized_test_source.py` | `research.portable_331.holdout` | `FROZEN_HOLDOUT` | 1 | `STAY_FROZEN` |
| `04_Testing/test_xauusd_portable_331_authorized_validation_source.py` | `04_Testing/test_xauusd_portable_331_authorized_validation_source.py` | `research.portable_331.holdout` | `FROZEN_HOLDOUT` | 1 | `STAY_FROZEN` |
| `04_Testing/test_xauusd_portable_331_one_time_test_core.py` | `04_Testing/test_xauusd_portable_331_one_time_test_core.py` | `research.portable_331.holdout` | `FROZEN_HOLDOUT` | 1 | `STAY_FROZEN` |
| `04_Testing/test_xauusd_portable_331_one_time_validation_core.py` | `04_Testing/test_xauusd_portable_331_one_time_validation_core.py` | `research.portable_331.holdout` | `FROZEN_HOLDOUT` | 1 | `STAY_FROZEN` |
| `04_Testing/xauusd_portable_331_authorized_test_source.py` | `04_Testing/xauusd_portable_331_authorized_test_source.py` | `research.portable_331.holdout` | `FROZEN_HOLDOUT` | 1 | `STAY_FROZEN` |
| `04_Testing/xauusd_portable_331_authorized_validation_source.py` | `04_Testing/xauusd_portable_331_authorized_validation_source.py` | `research.portable_331.holdout` | `FROZEN_HOLDOUT` | 4 | `STAY_FROZEN` |
| `04_Testing/xauusd_portable_331_one_time_test_core.py` | `04_Testing/xauusd_portable_331_one_time_test_core.py` | `research.portable_331.holdout` | `FROZEN_HOLDOUT` | 2 | `STAY_FROZEN` |
| `04_Testing/xauusd_portable_331_one_time_validation_core.py` | `04_Testing/xauusd_portable_331_one_time_validation_core.py` | `research.portable_331.holdout` | `FROZEN_HOLDOUT` | 3 | `STAY_FROZEN` |
| `xauusd_portable_331_one_time_test_access_ledger.json` | `xauusd_portable_331_one_time_test_access_ledger.json` | `research.portable_331.holdout` | `FROZEN_HOLDOUT_EVIDENCE` | 3 | `STAY_FROZEN` |
| `xauusd_portable_331_one_time_test_core_attestation.json` | `xauusd_portable_331_one_time_test_core_attestation.json` | `research.portable_331.holdout` | `FROZEN_HOLDOUT_EVIDENCE` | 3 | `STAY_FROZEN` |
| `xauusd_portable_331_one_time_test_preflight.json` | `xauusd_portable_331_one_time_test_preflight.json` | `research.portable_331.holdout` | `FROZEN_HOLDOUT_EVIDENCE` | 2 | `STAY_FROZEN` |
| `xauusd_portable_331_one_time_test_protocol.json` | `xauusd_portable_331_one_time_test_protocol.json` | `research.portable_331.holdout` | `FROZEN_HOLDOUT_EVIDENCE` | 5 | `STAY_FROZEN` |
| `xauusd_portable_331_one_time_test_recovery_preflight.json` | `xauusd_portable_331_one_time_test_recovery_preflight.json` | `research.portable_331.holdout` | `FROZEN_HOLDOUT_EVIDENCE` | 2 | `STAY_FROZEN` |
| `xauusd_portable_331_one_time_test_recovery_result.json` | `xauusd_portable_331_one_time_test_recovery_result.json` | `research.portable_331.holdout` | `FROZEN_HOLDOUT_EVIDENCE` | 3 | `STAY_FROZEN` |
| `xauusd_portable_331_one_time_test_result.json` | `xauusd_portable_331_one_time_test_result.json` | `research.portable_331.holdout` | `FROZEN_HOLDOUT_EVIDENCE` | 2 | `STAY_FROZEN` |
| `xauusd_portable_331_one_time_validation_access_ledger.json` | `xauusd_portable_331_one_time_validation_access_ledger.json` | `research.portable_331.holdout` | `FROZEN_HOLDOUT_EVIDENCE` | 6 | `STAY_FROZEN` |
| `xauusd_portable_331_one_time_validation_core_attestation.json` | `xauusd_portable_331_one_time_validation_core_attestation.json` | `research.portable_331.holdout` | `FROZEN_HOLDOUT_EVIDENCE` | 4 | `STAY_FROZEN` |
| `xauusd_portable_331_one_time_validation_preflight.json` | `xauusd_portable_331_one_time_validation_preflight.json` | `research.portable_331.holdout` | `FROZEN_HOLDOUT_EVIDENCE` | 4 | `STAY_FROZEN` |
| `xauusd_portable_331_one_time_validation_protocol.json` | `xauusd_portable_331_one_time_validation_protocol.json` | `research.portable_331.holdout` | `FROZEN_HOLDOUT_EVIDENCE` | 6 | `STAY_FROZEN` |
| `xauusd_portable_331_one_time_validation_result.json` | `xauusd_portable_331_one_time_validation_result.json` | `research.portable_331.holdout` | `FROZEN_HOLDOUT_EVIDENCE` | 8 | `STAY_FROZEN` |
| `xauusd_portable_331_one_time_validation_result_freeze.json` | `xauusd_portable_331_one_time_validation_result_freeze.json` | `research.portable_331.holdout` | `FROZEN_HOLDOUT_EVIDENCE` | 6 | `STAY_FROZEN` |
| `04_Testing/build_exness_demo_xauusd_canonical_history.py` | `04_Testing/build_exness_demo_xauusd_canonical_history.py` | `unclassified` | `REVIEW_REQUIRED` | 1 | `STAY_REVIEW_REQUIRED` |
| `04_Testing/check_symbols.py` | `04_Testing/check_symbols.py` | `unclassified` | `REVIEW_REQUIRED` | 1 | `STAY_REVIEW_REQUIRED` |
| `04_Testing/check_terminal.py` | `04_Testing/check_terminal.py` | `unclassified` | `REVIEW_REQUIRED` | 1 | `STAY_REVIEW_REQUIRED` |
| `04_Testing/daily_trade_readiness_diagnostic.py` | `04_Testing/daily_trade_readiness_diagnostic.py` | `unclassified` | `REVIEW_REQUIRED` | 1 | `STAY_REVIEW_REQUIRED` |
| `04_Testing/discover_xauusd_current_feature_pipeline.py` | `04_Testing/discover_xauusd_current_feature_pipeline.py` | `unclassified` | `REVIEW_REQUIRED` | 1 | `STAY_REVIEW_REQUIRED` |
| `04_Testing/exness_demo_xauusd_context_attestation_operation.py` | `04_Testing/exness_demo_xauusd_context_attestation_operation.py` | `unclassified` | `REVIEW_REQUIRED` | 1 | `STAY_REVIEW_REQUIRED` |
| `04_Testing/exness_historical_fill_telemetry_operation.py` | `04_Testing/exness_historical_fill_telemetry_operation.py` | `unclassified` | `REVIEW_REQUIRED` | 2 | `STAY_REVIEW_REQUIRED` |
| `04_Testing/run_exness_demo_xauusd_context_attestation.py` | `04_Testing/run_exness_demo_xauusd_context_attestation.py` | `unclassified` | `REVIEW_REQUIRED` | 1 | `STAY_REVIEW_REQUIRED` |
