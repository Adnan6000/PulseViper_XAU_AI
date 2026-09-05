# Repository Migration Readiness V2 - Current State

This report is a current-state companion to the frozen `Repository_Migration_Manifest_v2`.

The frozen manifest remains historical decision evidence and is not rewritten as migrations execute.

## Current summary

- Executed READY migrations: 59
- Pending location-sensitive READY: 19
- Review required: 77
- Frozen stay: 18
- Support stay: 1

Source-aligned test directories currently contain:

- `04_Testing/ai/common/`: 1 test
- `04_Testing/ai/core/`: 18 tests
- `04_Testing/ai/dataset/`: 4 tests
- `04_Testing/ai/objects/`: 1 test
- `04_Testing/ai/shadow/`: 35 tests

Total source-aligned tests: 59.

## Pending location-sensitive READY files

- `04_Testing/test_backup.py` -> `04_Testing/ai/database/test_backup.py`
- `04_Testing/test_bos.py` -> `04_Testing/ai/core/test_bos.py`
- `04_Testing/test_bos_memory.py` -> `04_Testing/ai/memory/test_bos_memory.py`
- `04_Testing/test_config.py` -> `04_Testing/ai/config/test_config.py`
- `04_Testing/test_database.py` -> `04_Testing/ai/database/test_database.py`
- `04_Testing/test_enums.py` -> `04_Testing/ai/common/test_enums.py`
- `04_Testing/test_exporter.py` -> `04_Testing/ai/dataset/test_exporter.py`
- `04_Testing/test_feature_list.py` -> `04_Testing/ai/features/test_feature_list.py`
- `04_Testing/test_fetcher.py` -> `04_Testing/ai/dataset/test_fetcher.py`
- `04_Testing/test_fvg.py` -> `04_Testing/ai/core/test_fvg.py`
- `04_Testing/test_history_cleaner.py` -> `04_Testing/ai/dataset/test_history_cleaner.py`
- `04_Testing/test_history_downloader.py` -> `04_Testing/ai/dataset/test_history_downloader.py`
- `04_Testing/test_history_manager.py` -> `04_Testing/ai/dataset/test_history_manager.py`
- `04_Testing/test_history_validator.py` -> `04_Testing/ai/dataset/test_history_validator.py`
- `04_Testing/test_liquidity_sweep_validator.py` -> `04_Testing/ai/core/test_liquidity_sweep_validator.py`
- `04_Testing/test_market_structure.py` -> `04_Testing/ai/core/test_market_structure.py`
- `04_Testing/test_repository.py` -> `04_Testing/ai/database/test_repository.py`
- `04_Testing/test_schema.py` -> `04_Testing/ai/database/test_schema.py`
- `04_Testing/test_v1_health.py` -> `04_Testing/ai/config/test_v1_health.py`

These 19 files remain intentionally unmoved because their current test-file location participates in repository-root or import bootstrap behavior.

They require a dedicated path-bootstrap migration gate rather than a mechanical folder move.

Permanently consumed VALIDATION and TEST are outside that migration work and must not be rerun.
