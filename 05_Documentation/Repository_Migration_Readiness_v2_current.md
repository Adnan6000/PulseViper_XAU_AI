# Repository Migration Readiness V2 - Current State

This report is the current-state companion to the frozen `Repository_Migration_Manifest_v2`.

The frozen V2 manifest remains historical decision evidence and is not rewritten as execution progresses.

## Current summary

- Executed READY migrations: 78
- Review-executed migrations: 2
- Review required: 75
- Frozen stay: 18
- Support stay: 1

## READY structural phase

All 78 READY rows remain complete under `04_Testing/ai/<domain>/`.

## Review execution - integration batch 01

Two REVIEW_REQUIRED rows were independently proven to have integration ownership, zero external consumers, zero fixed-depth bootstrap debt, zero local `sys.path` mutation, and no CI path dependency.

They now live under `04_Testing/integration/`:

- `test_instrument_frame_guard.py`
- `test_xauusd_hierarchical_model_v4_trainer.py`

The files moved byte-identically and passed focused verification at their new locations.

The portable-331 candidate evaluator remains intentionally outside this batch because it is a non-test research tool with a separate entrypoint and research-governance contract.

Current organized test-file population:

- source-aligned READY tests under `04_Testing/ai`: 78
- reviewed integration tests under `04_Testing/integration`: 2
- organized test files total: 80

Permanently consumed VALIDATION and one-time TEST were not executed.
