# PulseViper XAU AI — Testing & Scientific Validation Guide

## 1. Purpose

This document explains how testing works inside PulseViper XAU AI.

It is written for:

* new students;
* Python developers;
* ML researchers;
* maintainers;
* reviewers.

The goal is not simply to teach:

```text
how to run pytest
```

The more important goal is to teach:

```text
which test should be run,
when it should be run,
what data it may access,
and what conclusions it is allowed to support.
```

PulseViper contains both ordinary software tests and protected scientific evaluations.

They must not be confused.

---

# 2. Core Testing Principle

The preferred development sequence is:

```text
DESIGN
   ↓
IMPLEMENT
   ↓
PY_COMPILE
   ↓
FOCUSED UNIT TEST
   ↓
SYNTHETIC TEST
   ↓
INTEGRATION TEST
   ↓
AUTHORIZED REAL OPERATION
   ↓
FREEZE EVIDENCE
   ↓
BROADER REGRESSION
```

Do not begin every change by running the entire project.

Focused failures are easier to diagnose.

---

# 3. Main Test Categories

PulseViper uses several different test categories.

```text
1. Syntax / compile checks
2. Unit tests
3. Synthetic scientific tests
4. Contract tests
5. Integration tests
6. Artifact verification
7. Dry preflight
8. Protected holdout evaluation
9. Broader regression
10. Shadow / forward validation
```

Each category answers a different question.

---

# 4. Syntax Checks

Python syntax should normally be checked first.

Example:

```powershell
python -m py_compile 04_Testing\freeze_xauusd_portable_331_one_time_validation_result.py
```

A successful command usually prints nothing.

That means Python was able to compile the file.

---

## What `py_compile` proves

It can detect problems such as:

```text
SyntaxError
IndentationError
invalid Python syntax
some import-time syntax problems
```

---

## What `py_compile` does NOT prove

It does not prove:

```text
business logic is correct
dataset identity is correct
model behavior is correct
holdout policy is correct
runtime integration works
```

Compilation is only the first gate.

---

# 5. Focused Unit Tests

After compilation, run the focused test file associated with the module.

Example:

```powershell
python -m pytest 04_Testing\test_freeze_xauusd_portable_331_one_time_validation_result.py -q
```

Typical output:

```text
...... [100%]
6 passed
```

This is preferable to immediately running the entire repository.

---

# 6. Why Focused Tests Come First

Suppose you modify one validation-freeze module.

Running:

```text
500 unrelated tests
```

may create noise.

Running:

```text
the six tests that directly protect the modified contract
```

provides a cleaner signal.

Recommended order:

```text
changed module
      ↓
its focused tests
      ↓
its integration tests
      ↓
broader regression
```

---

# 7. Synthetic Tests

Synthetic tests use artificial data rather than protected real research data.

They are extremely important in PulseViper.

Example synthetic target:

```python
y = [-1, 0, 1, -1, 1, 0]
```

Example synthetic feature matrix:

```python
X.shape == (6, 331)
```

A synthetic test can verify:

```text
shape validation
class validation
probability handling
metric computation
ledger transitions
tamper detection
failure behavior
```

without touching VALIDATION or TEST.

---

# 8. Why Synthetic Tests Matter

Suppose we need to verify:

```text
a rejected VALIDATION result prevents TEST access
```

We should not intentionally fail the real VALIDATION split just to test this behavior.

Instead:

```text
synthetic validation batch
       ↓
synthetic model probabilities
       ↓
rejection case
       ↓
assert TEST remains blocked
```

This preserves real holdouts.

---

# 9. Contract Tests

A contract test verifies assumptions between modules.

Examples:

```text
feature_count == 331
class_order == [-1, 0, 1]
target_tradeable == target_class != 0
feature_columns_sha256 matches
dataset fingerprint matches
```

Contract tests are often more important than ordinary output tests.

A module may produce numerically plausible output while violating a frozen scientific contract.

---

# 10. Example Feature Contract Test

A simplified conceptual test:

```python
assert X.shape[1] == 331
```

But this alone is not enough.

A stronger contract also verifies:

```text
exact ordered feature names
exact feature-list fingerprint
finite numerical values
```

Current frozen feature-list SHA256:

```text
65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2
```

---

# 11. Example Target Contract Test

Current classes:

```text
-1 = SHORT
 0 = NO_TRADE
 1 = LONG
```

Required binary relationship:

```python
target_tradeable = (target_class != 0).astype("int8")
```

A test should fail if:

```text
target_class = 0
target_tradeable = 1
```

because the target contract is inconsistent.

---

# 12. Integration Tests

Integration tests connect real modules together.

Example:

```text
real portable loader
       +
real supervised batch
       +
real candidate evaluator
```

An integration test answers:

> Do independently implemented modules agree on the same contract?

---

# 13. Unit vs Integration Example

Unit test:

```text
Does `_numeric_matrix()` reject NaN?
```

Integration test:

```text
Can the actual portable dataset loader produce
a 69,966 × 331 supervised TRAIN batch that the evaluator accepts?
```

Both are useful.

They prove different things.

---

# 14. Real TRAIN Integration

TRAIN may be used during model research.

Current frozen TRAIN size:

```text
69,966 rows
331 features
```

TRAIN integration may verify:

```text
dataset discovery
manifest compatibility
feature order
target alignment
chronology
candidate/evaluator compatibility
```

TRAIN is not a protected final holdout.

However, TRAIN research rules still need to remain frozen and reproducible.

---

# 15. Purged Walk-Forward Testing

Financial data should not be randomly shuffled for the current model protocol.

Current research uses:

```text
4 chronological folds
12-row purge
expanding TRAIN window
```

Example:

```text
Fold 1
TRAIN ----------------
                     PURGE
                           EVALUATE

Fold 2
TRAIN --------------------------
                               PURGE
                                     EVALUATE
```

The purge protects against target-horizon leakage around fold boundaries.

---

# 16. Candidate Evaluation Tests

Important evaluator module:

```text
04_Testing\evaluate_xauusd_portable_331_train_model_candidates.py
```

Focused test:

```text
04_Testing\test_evaluate_xauusd_portable_331_train_model_candidates.py
```

This contract verifies areas such as:

```text
frozen registry
candidate construction
probability ordering
hierarchical probability combination
metrics
eligibility
selection priority
tamper detection
```

---

# 17. Frozen Metric Contract

Current evaluator uses 15 primary metrics:

```text
balanced_accuracy_3class
macro_f1_3class
directional_macro_f1_short_long

short_precision
short_recall
short_f1

no_trade_precision
no_trade_recall
no_trade_f1

long_precision
long_recall
long_f1

log_loss_3class
multiclass_brier
predicted_trade_coverage
```

A developer must distinguish:

```text
hard-gate metric
```

from:

```text
report-only metric
```

before observing protected holdout results.

---

# 18. Artifact Verification Tests

Serialized machine-learning models must be verified.

Current frozen model:

```text
xauusd_portable_331_c04_full_train_model.joblib
```

SHA256:

```text
48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769
```

Verification should cover:

```text
file SHA
model class
classes_
feature count
hyperparameters
tree count
research provenance
```

A `.joblib` file existing on disk does not prove it is the correct model.

---

# 19. Tamper Tests

Many PulseViper tests intentionally modify a copy of a contract or artifact identity.

Example:

```python
tampered["feature_count"] = 330
```

Expected:

```text
FAIL
```

This proves the system fails closed when scientific evidence changes.

---

# 20. Why Tamper Tests Are Important

Suppose an artifact validator only checks:

```text
file exists
```

Then replacing the model file may go unnoticed.

A strong validator should detect identity changes.

Tamper tests prove this behavior.

---

# 21. Dry Preflight

A dry preflight validates everything that can safely be validated before protected data is read.

Examples:

```text
model artifact SHA
protocol fingerprint
source contract
feature fingerprint
ledger state
previous evidence
```

Dry preflight should not load protected feature/target values.

---

# 22. Current VALIDATION Preflight Example

Frozen VALIDATION preflight fingerprint:

```text
5ee6d0948d93f83f7969662e103066f1a09d7b081883290aba104b52f0038f41
```

Before real VALIDATION execution:

```text
validation_read_attempt_count = 0
holdout_consumed = false
ledger_state = ABSENT
```

This evidence was frozen before real holdout access.

---

# 23. Protected Holdout Tests

Protected holdouts are fundamentally different from ordinary tests.

Current protected datasets:

```text
VALIDATION
TEST
```

VALIDATION is already consumed.

TEST is still untouched.

---

# 24. VALIDATION Current State

Current state:

```text
validation_accepted = true
validation_consumed = true
validation_rerun_authorized = false
```

Therefore:

```text
DO NOT RUN VALIDATION AGAIN
```

for performance-driven development.

---

# 25. TEST Current State

Current state:

```text
TEST not yet consumed
```

Therefore:

```text
DO NOT inspect TEST features or targets
DO NOT run predictions on TEST
DO NOT calculate TEST metrics
```

until the one-shot TEST infrastructure is implemented, synthetic-tested, dry-preflighted, and explicitly authorized.

---

# 26. Why TEST Is Special

TEST exists to answer:

> How well does the already-frozen research model generalize on the final unseen historical holdout?

TEST does not exist to answer:

> What should we change?

If TEST suggests a change is needed:

```text
close current research lineage
       ↓
design a new experiment
```

Do not tune against TEST and rerun.

---

# 27. One-Time Ledger Testing

Protected-data access uses a persistent ledger.

Conceptual states:

```text
RESERVED_BEFORE_READ
READ_INITIATED_CONSUMED_BOUNDARY
VALUES_LOADED
METRICS_COMPUTED
COMPLETE
```

A test should verify that:

```text
second performance-driven read attempt
```

is blocked after the consumed boundary.

---

# 28. Pre-Read Failure

Example:

```text
protocol file missing
```

before protected values are read.

Expected behavior:

```text
PRE_READ_TECHNICAL_FAILURE
```

If read attempt count remains zero and holdout was not exposed, technical recovery may be allowed.

---

# 29. Post-Read Failure

Example:

```text
protected values loaded
metric serialization crashes
```

Expected:

```text
CONSUMED_TECHNICAL_FAILURE
```

The holdout is now consumed.

Do not automatically rerun the operation.

---

# 30. Example of a Dangerous Test

Bad:

```python
def test_model_quality():
    X_test = load_real_test_features()
    ...
```

This silently turns the final TEST holdout into a development dependency.

Protected real datasets should not be ordinary unit-test fixtures.

---

# 31. Example of a Better Test

Use synthetic data:

```python
def test_model_quality_gate_rejects_low_directional_f1():
    ...
```

This proves gate logic without spending the scientific holdout.

---

# 32. Warning Handling

Not every warning is a failure.

Examples already encountered include:

```text
pandas PerformanceWarning
joblib / NumPy deprecation warnings
```

A warning may be acceptable if:

```text
tests pass
scientific semantics are unaffected
```

But warnings should still be understood.

Do not globally suppress warnings simply because they are inconvenient.

---

# 33. Example: Pandas Fragmentation Warning

Synthetic test construction may repeatedly add hundreds of columns.

Pandas can report:

```text
DataFrame is highly fragmented
```

This is primarily a performance warning.

If synthetic tests still produce correct values and pass:

```text
scientific gate may remain valid
```

The test implementation can later be optimized without changing model science.

---

# 34. JSON Encoding Tests

Machine-readable reports must use deterministic encoding.

Preferred:

```text
UTF-8 without BOM
```

Historical failures occurred because PowerShell output produced:

```text
UTF-16
```

or:

```text
UTF-8 with BOM
```

which broke strict JSON loaders.

---

# 35. Preferred JSON Writing

Use Python:

```python
from pathlib import Path
import json

Path("report.json").write_text(
    json.dumps(
        report,
        indent=2,
        sort_keys=True,
    ) + "\n",
    encoding="utf-8",
)
```

Avoid relying on generic shell redirection for machine-readable scientific evidence.

---

# 36. Exact Commands Only

Documentation should use exact filenames.

Good:

```powershell
python -m pytest 04_Testing\test_freeze_xauusd_portable_331_one_time_validation_result.py -q
```

Bad:

```powershell
python -m pytest TEST_FILE.py
```

Placeholder commands can accidentally be pasted literally.

---

# 37. Recommended Local Development Sequence

For a changed Python module:

```text
1. Save file
2. py_compile implementation
3. py_compile test
4. run focused pytest
5. run focused integration
6. inspect generated evidence
7. git status
8. commit exact files
```

Example:

```powershell
python -m py_compile 04_Testing\freeze_xauusd_portable_331_one_time_validation_result.py
```

Then:

```powershell
python -m py_compile 04_Testing\test_freeze_xauusd_portable_331_one_time_validation_result.py
```

Then:

```powershell
python -m pytest 04_Testing\test_freeze_xauusd_portable_331_one_time_validation_result.py -q
```

---

# 38. When to Run Broader Regression

Broader regression is useful when:

```text
a meaningful increment is complete
multiple modules changed
shared contracts changed
production integration changed
```

It is usually unnecessary after every documentation typo or isolated helper change.

---

# 39. Regression Before Major Milestones

Before important transitions such as:

```text
final TEST
shadow integration
live promotion
```

a broader relevant regression should be considered.

Protected holdout access should still remain separate from regression testing.

---

# 40. Documentation Tests

Markdown files do not normally need `py_compile`.

Documentation should instead be checked for:

```text
correct filenames
correct fingerprints
working relative links
current authorization state
no contradictory instructions
no secrets
```

A future documentation lint workflow may be added.

---

# 41. Test File Naming

Preferred convention:

```text
implementation.py
test_implementation.py
```

Example:

```text
xauusd_portable_331_authorized_validation_source.py

test_xauusd_portable_331_authorized_validation_source.py
```

This makes module/test relationships easy for students to discover.

---

# 42. Test Failure Investigation

When a test fails:

```text
1. Read the first real exception.
2. Identify the failing contract.
3. Determine whether protected data was accessed.
4. Check persistent ledger if applicable.
5. Fix the smallest responsible layer.
6. Do not weaken the scientific rule just to make the test green.
```

---

# 43. Example Failure Classification

Failure:

```text
feature_columns_sha256 mismatch
```

Do not solve by:

```text
removing the hash check
```

Instead investigate:

```text
feature list changed?
column order changed?
wrong manifest loaded?
wrong dataset loaded?
```

---

# 44. Test Anti-Pattern — Weakening the Gate

Suppose a test fails because:

```text
trade coverage = 0.97
```

but frozen maximum allowed coverage is:

```text
0.95
```

Do not modify the maximum to:

```text
0.98
```

after observing the result.

The failure is scientific information.

---

# 45. Test Anti-Pattern — Catch-All Exceptions

Bad pattern:

```python
try:
    ...
except Exception:
    pass
```

This can hide:

```text
artifact mismatch
data corruption
holdout leakage
model incompatibility
```

Contract failures should normally be explicit.

---

# 46. Test Anti-Pattern — Accidental Real Data Access

A unit test should not trigger:

```text
real VALIDATION source
real TEST source
live MT5 account
live order execution
```

unless the test is explicitly a separately authorized integration/operation.

---

# 47. Student Testing Levels

Recommended progression:

## Level 1

Run `py_compile`.

## Level 2

Run existing unit tests.

## Level 3

Read synthetic fixtures.

## Level 4

Write tamper tests.

## Level 5

Read integration tests.

## Level 6

Work on TRAIN-only research integration.

## Level 7

Study protected holdout infrastructure.

## Level 8

Shadow/runtime tests.

A student should understand lower levels before working with protected data.

---

# 48. Current Known Focused Milestones

Examples of successfully completed focused test gates include:

```text
candidate evaluator tests
portable loader integration
full TRAIN fit tests
artifact verification tests
validation protocol tests
validation core tests
authorized validation source tests
validation freeze tests
```

The validation source gate passed:

```text
8 passed
```

The validation result freeze gate passed:

```text
6 passed
```

---

# 49. Final TEST Testing Plan

Before first TEST access:

```text
[ ] TEST protocol frozen
[ ] TEST source implemented
[ ] source synthetic tests passed
[ ] TEST ledger tests passed
[ ] model SHA verified
[ ] feature fingerprint verified
[ ] TEST dry preflight passed
[ ] dry preflight fingerprint frozen
[ ] real TEST read count = 0
```

Only then:

```text
first and only TEST execution
```

---

# 50. Shadow Testing Plan

After historical TEST:

```text
[ ] production feature adapter tests
[ ] broker-time tests
[ ] D1 reconstruction tests
[ ] feature parity tests
[ ] inference adapter tests
[ ] model SHA startup test
[ ] non-finite feature rejection
[ ] stale-data rejection
[ ] shadow signal test
[ ] risk integration test
[ ] no-real-order assertion
```

---

# 51. Live Safety Testing

Before eventual live promotion:

```text
[ ] shadow/live mode separation
[ ] kill switch
[ ] stale-data fail closed
[ ] broker disconnect handling
[ ] symbol mismatch handling
[ ] model mismatch handling
[ ] risk ceiling
[ ] account protection
[ ] execution error handling
[ ] audit logging
```

Historical ML performance is only one part of this gate.

---

# 52. Definition of a Passing Engineering Gate

A normal engineering increment should typically have:

```text
[ ] implementation complete
[ ] syntax check passed
[ ] focused tests passed
[ ] integration tested when applicable
[ ] evidence reviewed
[ ] documentation updated
[ ] no protected-data violation
[ ] exact files committed
```

---

# 53. Definition of a Passing Scientific Gate

Additionally:

```text
[ ] protocol was frozen before results
[ ] dataset identity verified
[ ] feature identity verified
[ ] model identity verified
[ ] required metrics computed
[ ] no unauthorized tuning
[ ] result fingerprint generated
[ ] next authorization explicit
```

---

# 54. Current Scientific Boundary

Current state:

```text
TRAIN:
available for research

VALIDATION:
passed
consumed
frozen
no rerun

TEST:
untouched
protected

SHADOW:
not authorized yet

LIVE:
not authorized
```

---

# 55. Golden Testing Rules

```text
1. Compile before running.

2. Run focused tests before broad tests.

3. Prefer synthetic data for logic tests.

4. Do not make protected holdouts ordinary test fixtures.

5. Verify identities, not only shapes.

6. Test failure paths.

7. Test tamper detection.

8. Distinguish pre-read and post-read failures.

9. Never weaken a frozen gate after seeing results.

10. TEST is an evaluation asset, not a tuning tool.
```

---

# 56. Final Principle

A green test suite is useful only when the tests protect the correct scientific and engineering contracts.

The objective is not:

```text
make pytest green
```

The objective is:

```text
prove that the system behaved exactly as authorized.
```

<!-- REPOSITORY-ARCHITECTURE-MANAGED:START -->
## Testing Repository Layout and Migration Rules

> Managed testing-architecture section.

Pytest is configured to discover tests recursively beneath `04_Testing/` using
the `test_*.py` naming convention. Therefore nested test directories remain
compatible with normal pytest discovery.

The current CI workflow also contains explicit file paths for a focused test
set. Any migration of those files must update `.github/workflows/ci.yml` in the
same commit and must run the equivalent focused test set before freeze.

Current structured testing areas include:

- `04_Testing/ai/common/`
- `04_Testing/ai/core/`
- `04_Testing/ai/dataset/`
- `04_Testing/ai/objects/`
- `04_Testing/ai/shadow/`
- `04_Testing/production_portability/`
- `04_Testing/evidence/`

The production-portability restructuring moved 38 Python files. The migrated
batch passed Python compilation and its focused regression suite with 113
tests passing.

Repository cleanup must never execute the permanently consumed one-time TEST or
rerun the permanently consumed VALIDATION.

Frozen holdout-related scripts/tests remain compatibility exceptions where
their established path is part of the frozen protocol.

Before future test relocation:

- establish real source ownership;
- inspect dynamic `importlib` / file-loader usage;
- preserve repository-root semantics;
- update CI references;
- run `py_compile`;
- run the focused affected pytest suite;
- check for stale old paths;
- verify frozen artifacts remain unchanged;
- commit only from a clean verified state.
<!-- REPOSITORY-ARCHITECTURE-MANAGED:END -->

<!-- REPOSITORY-MIGRATION-V2:START -->
## Architecture V2 Migration State

The repository now uses
`05_Documentation/Repository_Migration_Manifest_v2.csv`
and
`05_Documentation/Repository_Migration_Manifest_v2.md`
as the decision record for future testing/research relocation.

The V2 manifest currently covers 174 remaining loose/root Python
candidates.

Current classification:

- READY: 78
- REVIEW_REQUIRED: 77
- FROZEN_STAY: 18
- SUPPORT_STAY: 1

V2 is fail-closed. A proposed target is not permission to move a file unless
its status is READY and the later migration gate independently verifies path,
CI, import/dynamic-loader, frozen-artifact, and documentation constraints.

The original migration manifest remains historical planning evidence and must
not be used as automatic authority for remaining moves.
<!-- REPOSITORY-MIGRATION-V2:END -->

<!-- V2-CORE-SAFE-A-MIGRATION:START -->
## Architecture V2 Core Test Migration

The first V2 test migration moved 18 location-independent Core tests to
`04_Testing/ai/core/`.

Nine moved tests were explicitly addressed by CI, so their workflow paths were
updated in the same gate.

Acceptance for this batch required:

- byte-identical test relocation;
- Python compilation;
- focused pytest execution of all 18 moved tests;
- stale operational path checks;
- frozen-file integrity verification;
- CI path synchronization;
- documentation synchronization.

Permanently consumed VALIDATION and TEST were not executed.
<!-- V2-CORE-SAFE-A-MIGRATION:END -->

<!-- V2-SHADOW-SAFE-A-MIGRATION:START -->
## Architecture V2 Shadow Test Migration

The Shadow V2 batch relocated 35 tests into
`04_Testing/ai/shadow/` and synchronized 11 explicit CI paths.

Initial focused result:

- 661 passed;
- 1 failed because a moved test dynamically imported another moved test using
  its former dotted module path.

Recovery:

- exactly one dotted module reference was updated;
- all 35 Shadow tests recompiled successfully;
- all 662 focused Shadow tests passed;
- 33 frozen compatibility files remained unchanged;
- no old Shadow dotted module references remained.

Future migration safety scans must include dotted dynamic module strings in
addition to filesystem paths, `.py` basenames, `__file__`, parent-depth
assumptions, CI paths, and documentation references.

Permanently consumed VALIDATION and TEST were not executed.
<!-- V2-SHADOW-SAFE-A-MIGRATION:END -->

<!-- V2-FINAL-LOCATION-INDEPENDENT-BATCH:START -->
## Completion of Location-Independent READY Migration

The final location-independent V2 batch moved six tests:

- four Dataset-owned tests;
- one Common-owned test;
- one Objects-owned test.

The batch required dependency revalidation, byte-identical relocation,
`py_compile`, focused pytest, frozen-file integrity checks, stale old-path and
old-module scans, current readiness reporting, and documentation
synchronization.

No CI paths required modification in this batch.

All 19 remaining READY tests use file-location-dependent bootstrap behavior and
remain intentionally unmoved.

Permanently consumed VALIDATION and TEST were not executed.
<!-- V2-FINAL-LOCATION-INDEPENDENT-BATCH:END -->

<!-- V2-PYTEST-BOOTSTRAP-CONSOLIDATION:START -->
## Shared Pytest Path Bootstrap

Repository-root import visibility for normal tests is provided centrally by
`04_Testing/conftest.py`.

A consolidation gate removed redundant local bootstrap logic from 17 READY
tests while every file remained at its original location.

Verification uses `.venv\Scripts\python.exe -m pytest` on Windows. The final
focused result for this gate was 41 passed.

An earlier system-Python run stopped because that external interpreter lacked
the repository-declared PyYAML dependency; this was an environment failure and
not treated as code evidence.

The project-environment run then exposed two tests with pre-existing obsolete
Dataset calls. `test_exporter.py` and `test_history_manager.py` were aligned to
the current fail-closed InstrumentContext contract using deterministic
`tmp_path` output and without changing production Dataset behavior.

Seven existing `datetime.utcnow()` deprecation warnings from
`history_downloader.py` remain separate maintenance debt.

Permanently consumed VALIDATION and TEST were not executed.
<!-- V2-PYTEST-BOOTSTRAP-CONSOLIDATION:END -->

<!-- V2-DATABASE-IMPORT-NORMALIZATION:START -->
## Database Import Normalization Verification

`test_database.py` was normalized separately from general pytest bootstrap
consolidation because it formerly inserted `02_AI` into `sys.path` and imported
`Database.database`.

The normalized test:

- has no `__file__` repository-depth dependency;
- does not mutate `sys.path`;
- resolves `02_AI.Database.database` through `importlib`;
- passes focused verification under the project `.venv`.

No production database code was changed.

Permanently consumed VALIDATION and TEST were not executed.
<!-- V2-DATABASE-IMPORT-NORMALIZATION:END -->

<!-- V2-READY-18-RELOCATION:START -->
## Verification of 18-File READY Relocation

Verification covered 18 original `R100` moves, all new-path `py_compile`,
focused pytest under the project `.venv`, frozen 33-file identity, zero true
external old-path/dotted-module consumers, and zero old filesystem paths.

One pre-existing config-test `Path:` docstring header was corrected after the
move. Because docstrings are represented in Python ASTs, executable semantic
identity was checked after normalizing docstring values rather than requiring
literal full-AST equality.

The one remaining basename-only BOS reference is a comment and is not an
operational path dependency.

Permanently consumed VALIDATION and TEST were not executed.
<!-- V2-READY-18-RELOCATION:END -->

<!-- V2-V1-ROOT-ABSTRACTION-RELOCATION:START -->
## `repo_root` Pytest Fixture

Tests requiring repository filesystem access use the session-scoped
`repo_root` fixture from `04_Testing/conftest.py`.

The root is marker-discovered rather than derived from a fixed parent index.

The V1 health migration was verified first at its original path using the new
fixture and then at `04_Testing/ai/config/test_v1_health.py`. The explicit CI
path was updated in the same gate.

Source-aligned `04_Testing/ai` collection was also verified after the central
conftest change.

Permanently consumed VALIDATION and TEST were not executed.
<!-- V2-V1-ROOT-ABSTRACTION-RELOCATION:END -->

<!-- V2-REVIEW-INTEGRATION-BATCH-01:START -->
## Reviewed Integration Relocation Verification

The first REVIEW_REQUIRED integration batch required:

- zero fixed-depth `__file__` bootstrap;
- zero local `sys.path` mutation;
- zero external full-path, dotted-module, and basename consumers;
- zero CI path dependency;
- byte-identical movement;
- `py_compile` at new locations;
- focused pytest at new locations;
- frozen 33-file identity verification.

Research executables are not combined into an integration-test migration gate.

Permanently consumed VALIDATION and one-time TEST workflows were not executed.
<!-- V2-REVIEW-INTEGRATION-BATCH-01:END -->

<!-- V2-REVIEW-DIAGNOSTICS-BATCH-01:START -->
## Test Naming Versus Diagnostics

A file named `test_*.py` is not automatically a valid pytest test module.

The former root-level logger and settings files contained zero pytest test
functions and performed observable work at import time. They were reclassified
as standalone diagnostics and renamed so pytest semantics are unambiguous.

Operational consumer scans must use exact path or import/module evidence;
root-level module stems must not be detected by unrestricted raw substring
matching.

Consumed VALIDATION and one-time TEST workflows were not executed.
<!-- V2-REVIEW-DIAGNOSTICS-BATCH-01:END -->

<!-- V2-SELF-TARGET-DIRECT-SCRIPT-ROOT-NORMALIZATION:START -->
## Direct-Script Bootstrap Test

`test_exness_historical_fill_telemetry_direct_script.py` now obtains repository
location through the canonical pytest `repo_root` fixture.

The test still launches the same telemetry operation with `--help`, so the
standalone project-root bootstrap behavior under test is unchanged.

File-loader harnesses that intentionally resolve sibling research scripts are
not converted to `repo_root` merely because they contain `__file__`.
<!-- V2-SELF-TARGET-DIRECT-SCRIPT-ROOT-NORMALIZATION:END -->

<!-- GATE-13-PORTABILITY-TESTING:START -->
## Gate 13 Production Portability & Feature Parity Tests

Gate 13 verifies that the production feature pipeline reproduces the exact frozen 331-feature model input contract without future leakage using canonical broker-derived historical execution snapshots against non-holdout frozen TRAIN rows (live MT5 feed ingestion and live runtime parity have not yet been proven by Gate 13):

- `04_Testing/production_portability/test_portable_feature_contract.py`:
  Validates 331 feature count, column ordering, SHA256 fingerprint, strict symbol allowlisting (`XAUUSD`, `XAUUSDm`), and rejection of invalid/reordered inputs.
- `04_Testing/production_portability/test_portable_feature_pipeline.py`:
  Validates production pipeline end-to-end:
  - Deterministic repeatability;
  - Rejection of alien symbols (`EURUSD`), missing timeframes, non-monotonic timestamps, duplicate timestamps, and inverted OHLC;
  - Strict no-future-leakage causal alignment;
  - D1 reconstruction from H1 matching 00:00:00 UTC boundary;
  - Read-only compatibility with frozen C04 model artifact.
- `04_Testing/production_portability/test_frozen_331_parity.py`:
  Validates numerical feature parity across non-holdout TRAIN reference rows against `Portable331TrainingInputLoader`.
- `04_Testing/production_portability/run_xauusd_portable_331_production_parity.py`:
  Standalone reproducible verification harness that executes full parity analysis and generates `xauusd_portable_331_production_parity_evidence.json`.

One-time VALIDATION and TEST holdouts are never executed or touched during portability verification.
<!-- GATE-13-PORTABILITY-TESTING:END -->
