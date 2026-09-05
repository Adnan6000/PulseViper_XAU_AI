# Repository Migration Readiness V2 - Current State

This report is the current-state companion to the frozen `Repository_Migration_Manifest_v2`.

The frozen V2 manifest remains historical decision evidence and is not rewritten as review execution progresses.

## Current summary

- Executed READY migrations: 78
- Review-executed migrations: 4
- Review required: 73
- Frozen stay: 18
- Support stay: 1

## Review execution

Two reviewed cross-domain tests live under `04_Testing/integration/`.

Two historical root-level `test_*.py` files were proven not to be pytest tests at all. They contained zero test functions and executed diagnostics at import time.

Those files are now explicit standalone diagnostics:

- `04_Testing/diagnostics/logger_diagnostic.py`
- `04_Testing/diagnostics/settings_diagnostic.py`

Standalone diagnostic repository-root discovery is provided by `04_Testing/diagnostics/_repository_bootstrap.py`. It uses repository markers rather than fixed parent depth and is intentionally independent from pytest `conftest.py`.

The frozen V2 manifest's original self-target proposals remain unchanged as historical evidence. The reviewed actual targets are recorded by the execution log and current documentation.

A scanner correction was also established: a root-level Python module stem such as `test_settings` must not be treated as an operational dotted-module reference by raw substring matching. The earlier apparent consumer was only the function name `test_settings_load_successfully`.

Permanently consumed VALIDATION and one-time TEST were not executed.
