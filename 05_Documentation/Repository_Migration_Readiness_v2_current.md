# Repository Migration Readiness V2 - Current State

This report is the current-state companion to the frozen `Repository_Migration_Manifest_v2`.

The frozen V2 manifest remains historical decision evidence and is not rewritten as execution progresses.

## Current summary

- Executed READY migrations: 78
- Pending READY migrations: 0
- Review required: 77
- Frozen stay: 18
- Support stay: 1

## READY structural migration complete

All 78 V2 READY tests are now source-aligned under `04_Testing/ai/<domain>/`.

The final READY special case, `test_v1_health.py`, was first decoupled from its filesystem depth using the shared `repo_root` pytest fixture.

`04_Testing/conftest.py` now discovers repository root using stable repository markers rather than a fixed `parents[n]` depth. The same discovered root owns pytest `sys.path` visibility and the session-scoped `repo_root` fixture.

`test_v1_health.py` then moved to `04_Testing/ai/config/test_v1_health.py`, and its explicit CI path was updated.

The source-aligned direct test-file population is now 78:

- common: 2
- config: 2
- core: 22
- database: 4
- dataset: 10
- features: 1
- memory: 1
- objects: 1
- shadow: 35

The remaining V2 queue consists of REVIEW_REQUIRED, FROZEN_STAY, and SUPPORT_STAY decisions rather than ordinary READY relocation work.

Permanently consumed VALIDATION and TEST were not executed.
