# Repository Migration Readiness V2 - Current State

This report is the current-state companion to the frozen `Repository_Migration_Manifest_v2`.

The frozen V2 manifest remains historical decision evidence and is not rewritten as execution progresses.

## Current summary

- Executed READY migrations: 59
- Pending relocation-ready: 18
- Pending repository-root abstraction: 1
- Review required: 77
- Frozen stay: 18
- Support stay: 1

## Relocation-ready bootstrap state

Seventeen tests use `04_Testing/conftest.py` as their shared pytest repository-root bootstrap authority.

`04_Testing/test_database.py` has additionally been normalized away from its legacy `Database.database` import and now resolves the canonical `02_AI.Database.database` module without adding `02_AI` to `sys.path`.

All 18 files are now independent of their current filesystem depth and ready for a dedicated source-aligned relocation gate.

## Pending relocation-ready files

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

## Remaining READY special case

- `04_Testing/test_v1_health.py`: genuinely uses repository-root filesystem paths and requires a location-independent root abstraction.

Permanently consumed VALIDATION and TEST were not executed.
