# Repository Migration Execution Log V2

This file records execution against the frozen Architecture V2 migration
manifest. The manifest remains the decision record; this log records which
approved subsets were actually migrated and verified.

## Batch V2-CORE-SAFE-A-01

- Manifest baseline: `1499f75`
- Ownership: `02_AI/Core`
- Source class: READY / HIGH confidence
- Safety class: SAFE_A
- Files moved: 18
- Target: `04_Testing/ai/core/`
- CI paths updated: 9
- File content changes: none; relocation byte identity required
- `py_compile`: required and passed before documentation freeze
- focused pytest: required and passed before documentation freeze
- frozen compatibility material: unchanged
- VALIDATION rerun: no
- one-time TEST rerun: no
- location-sensitive READY files included: no

The batch intentionally excludes tests that depend on `__file__`,
hard-coded parent depth, or external Python consumers.

<!-- V2-SHADOW-SAFE-A-02:START -->
## Batch V2-SHADOW-SAFE-A-02

- Baseline before execution: `9a86e81`
- Ownership: `02_AI/Shadow`
- Files moved: 35
- Target: `04_Testing/ai/shadow/`
- CI paths updated: 11
- Initial relocation byte identity: passed
- Initial focused Shadow pytest: 661 passed, 1 failed
- Failure class: stale test-to-test dotted module import
- Semantic Python files requiring relocation edit: 1
- Dotted module references repaired: 1
- Shadow `py_compile` after recovery: passed
- Final focused Shadow pytest: 662 passed
- Frozen compatibility files checked: 33
- Old Shadow dotted module residue: 0
- VALIDATION rerun: no
- one-time TEST rerun: no

The initial safety preflight handled filesystem paths and `.py` basename
references but did not classify dotted `importlib` module strings as
file-location dependencies.

The focused suite exposed that blind spot before commit. The migration
methodology and educational documentation were updated accordingly.
<!-- V2-SHADOW-SAFE-A-02:END -->

<!-- V2-FINAL-SAFE-A-03:START -->
## Batch V2-FINAL-SAFE-A-03

- Baseline before execution: `499437f`
- Files moved: 6
- Common-owned tests: 1
- Dataset-owned tests: 4
- Objects-owned tests: 1
- CI paths updated: 0
- Dependency safety revalidation: passed
- Byte-identical relocation: passed
- `py_compile`: passed
- focused pytest: passed
- frozen compatibility files checked: 33
- stale old filesystem/module references: 0
- total executed READY migrations after batch: 59
- remaining location-sensitive READY files: 19
- VALIDATION rerun: no
- one-time TEST rerun: no

This completes migration of all READY files whose current relocation was
proven independent of test-file location.
<!-- V2-FINAL-SAFE-A-03:END -->

<!-- V2-BOOTSTRAP-CONSOLIDATION-04:START -->
## Gate V2-BOOTSTRAP-CONSOLIDATION-04

- Baseline: `d664329`
- Bootstrap-cleaned tests: 17
- Files relocated: 0
- Shared bootstrap authority: `04_Testing/conftest.py`
- Project verification interpreter: `.venv\Scripts\python.exe`
- Project Python: 3.12.10
- Production files modified: 0
- Legacy Dataset tests refreshed: 2
- `test_exporter.py`: aligned to mandatory InstrumentContext/source-metadata contract
- `test_history_manager.py`: aligned to mandatory InstrumentContext contract
- Repaired Dataset tests use deterministic temporary output and no MT5 dependency
- `test_database.py`: excluded for separate import normalization
- `test_v1_health.py`: excluded for separate repository-root abstraction
- `py_compile`: passed
- focused pytest: 41 passed
- focused pytest warnings: 7 existing `datetime.utcnow()` deprecation warnings
- frozen compatibility files checked: 33
- VALIDATION rerun: no
- one-time TEST rerun: no

Verification history:

1. A system-Python run stopped because PyYAML was absent from that external
   interpreter. PyYAML was already declared and present in the project `.venv`.
2. The project `.venv` then exposed two pre-existing stale Dataset test
   contracts.
3. HEAD equivalence proved those failing test bodies were unchanged by the
   bootstrap edit and that mandatory context contracts predated this gate.
4. The two tests were aligned to current production behavior without modifying
   production code.
5. The complete focused suite passed 41 tests under the project `.venv`.
6. Readiness reporting initially stopped after verification because Python
   attempted to sort dictionaries without a key. The reporting-only bug was
   corrected without rerunning or altering verified Python behavior.

This gate separates bootstrap cleanup from filesystem relocation and removes
test-depth dependence rather than shifting it to a new parent index.
<!-- V2-BOOTSTRAP-CONSOLIDATION-04:END -->
