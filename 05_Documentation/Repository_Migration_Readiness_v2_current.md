# Repository Migration Readiness V2 - Current State

This report is the current-state companion to the frozen `Repository_Migration_Manifest_v2`.

The frozen V2 manifest remains historical decision evidence and is not rewritten as execution progresses.

## Current summary

- Executed READY migrations: 59
- Pending relocation-ready after pytest bootstrap consolidation: 17
- Pending import normalization: 1
- Pending repository-root abstraction: 1
- Review required: 77
- Frozen stay: 18
- Support stay: 1

## Pytest bootstrap consolidation

`04_Testing/conftest.py` is the shared repository-root `sys.path` bootstrap authority for the 17 relocation-ready tests.

The 17 tests no longer derive repository root from their own `__file__` location and no longer mutate `sys.path` independently.

Their focused verification passed under the project `.venv`: 41 tests passed.

During verification, two pre-existing Dataset tests were found to use obsolete pre-context API calls. They were aligned to the current fail-closed InstrumentContext contract without changing production code.

`test_exporter.py` and `test_history_manager.py` now use deterministic temporary-output fixtures instead of broker MT5 state.

## Pending relocation-ready files

- `04_Testing/test_backup.py` -> `04_Testing/ai/database/test_backup.py`
- `04_Testing/test_bos.py` -> `04_Testing/ai/core/test_bos.py`
- `04_Testing/test_bos_memory.py` -> `04_Testing/ai/memory/test_bos_memory.py`
- `04_Testing/test_config.py` -> `04_Testing/ai/config/test_config.py`
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

## Remaining special cases

- `04_Testing/test_database.py`: requires canonical import normalization away from legacy `Database.database` resolution.
- `04_Testing/test_v1_health.py`: genuinely uses repository-root filesystem paths and requires a location-independent root abstraction.

## Verification environment

Repository-focused pytest verification uses the project `.venv` interpreter and its declared dependencies.

The earlier system-Python collection failure was environmental: PyYAML was declared by the repository but absent from that external Python installation.

The focused project-environment suite passed 41 tests. Seven existing `datetime.utcnow()` deprecation warnings were reported by `history_downloader.py` and are not bootstrap failures.

Permanently consumed VALIDATION and TEST were not executed.
