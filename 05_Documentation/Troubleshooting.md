# PulseViper XAU AI — Troubleshooting & Recovery Guide

## 1. Purpose

This guide explains how to diagnose common PulseViper XAU AI development, testing, research, artifact, and protected-data problems.

It is written so that a new student can answer:

* What failed?
* Which layer failed?
* Is the failure safe to retry?
* Was protected data already consumed?
* Which file or fingerprint should be checked?
* What should NOT be changed just to make the error disappear?

The main troubleshooting principle is:

> Fix the responsible engineering problem without weakening the scientific or safety contract.

---

# 2. First Rule When Something Fails

Do not immediately change code.

First classify the failure.

```text
Failure
  ↓
Syntax?
Import?
File/path?
Encoding?
Contract?
Dataset?
Feature?
Model artifact?
Protected holdout?
Runtime/broker?
```

Then determine whether any protected data was accessed.

For VALIDATION or TEST work, always ask:

```text
Did failure happen BEFORE protected values were read?

or

Did failure happen AFTER protected values were read?
```

This distinction can determine whether retrying is scientifically valid.

---

# 3. Recommended Failure Investigation Order

When a command fails:

```text
1. Read the first meaningful exception.

2. Identify the exact file/function involved.

3. Identify which project layer owns the failure.

4. Check whether a frozen fingerprint mismatched.

5. Check whether protected data was accessed.

6. Check persistent ledger if applicable.

7. Fix the smallest responsible layer.

8. Re-run only the focused gate.

9. Do not weaken frozen rules.
```

---

# 4. Basic Environment Check

The normal project location is:

```text
D:\PulseViper_XAU_AI
```

When PowerShell shows:

```text
(.venv)
```

the project virtual environment is active.

Commands should normally use:

```powershell
python ...
```

rather than hard-coding a separate Python executable.

Check Python:

```powershell
python --version
```

Check current directory:

```powershell
Get-Location
```

Expected repository directory:

```text
D:\PulseViper_XAU_AI
```

---

# 5. Wrong Working Directory

Example error:

```text
python: can't open file ...
```

or a relative project file cannot be found.

Check:

```powershell
Get-Location
```

Move to repo:

```powershell
Set-Location D:\PulseViper_XAU_AI
```

Then run the exact command again.

---

# 6. Do Not Use Placeholder Commands

A historical development mistake occurred when a placeholder command was pasted literally.

Bad documentation:

```text
python SCRIPT_NAME.py
```

or:

```text
python some_script.py
```

The shell interprets that as an actual filename.

Documentation and troubleshooting instructions should use exact known project files.

Example:

```powershell
python 04_Testing\freeze_xauusd_portable_331_one_time_validation_result.py
```

---

# 7. Python Syntax Errors

First compile only the affected file.

Example:

```powershell
python -m py_compile 04_Testing\freeze_xauusd_portable_331_one_time_validation_result.py
```

Typical failures:

```text
SyntaxError
IndentationError
unterminated string
invalid syntax
```

Fix syntax before running pytest or real research operations.

---

# 8. Compile Both Implementation and Test

For a new gate, compile implementation:

```powershell
python -m py_compile 04_Testing\freeze_xauusd_portable_331_one_time_validation_result.py
```

Then its focused test:

```powershell
python -m py_compile 04_Testing\test_freeze_xauusd_portable_331_one_time_validation_result.py
```

Only then run pytest.

---

# 9. Focused Pytest Failure

Example:

```powershell
python -m pytest 04_Testing\test_freeze_xauusd_portable_331_one_time_validation_result.py -q
```

If a test fails:

```text
Do not immediately run the entire regression suite.
```

Instead inspect:

```text
first failing test
first real traceback
assertion message
contract being checked
```

Fix that gate first.

---

# 10. Import Errors

Possible error:

```text
ModuleNotFoundError
```

Common causes:

* wrong working directory;
* wrong virtual environment;
* package-relative import;
* dynamic import path;
* missing dependency;
* filename mismatch.

First verify:

```powershell
Get-Location
```

Then:

```powershell
python --version
```

Then compile the exact module.

Do not copy files into random directories just to make imports work.

---

# 11. Package-Aware Import Problems

PulseViper research scripts sometimes load modules from folders whose names or project layout make ordinary imports inconvenient.

Existing integration code may use explicit package-aware or `importlib` loading.

If an import works in one runner but fails in another:

```text
compare import strategy
```

rather than creating duplicate module copies.

Duplicating source files creates provenance problems.

---

# 12. Missing Dependency

Example:

```text
ModuleNotFoundError: No module named 'sklearn'
```

Confirm the virtual environment is active.

Then install repository requirements:

```powershell
python -m pip install -r requirements.txt
```

Avoid installing random newer package versions unless required.

Dependency changes can alter model serialization or numerical behavior.

---

# 13. JSON Decode Error — UTF-16

A real project incident produced an error similar to:

```text
UnicodeDecodeError:
'utf-8' codec can't decode byte 0xff
```

Cause:

The JSON file was written as UTF-16 by shell output behavior.

Machine-readable PulseViper evidence should normally use:

```text
UTF-8 without BOM
```

---

# 14. Repairing Known UTF-16 JSON

For a known file that was accidentally written as UTF-16, a one-time normalization pattern is:

```powershell
python -c "from pathlib import Path; p=Path('xauusd_portable_331_train_model_candidate_registry_design.json'); p.write_text(p.read_text(encoding='utf-16'), encoding='utf-8')"
```

Only use this when the content is known to be semantically correct and only the encoding is wrong.

Do not use encoding repair as an excuse to alter scientific values.

---

# 15. JSON Decode Error — UTF-8 BOM

Another historical error:

```text
JSONDecodeError:
Unexpected UTF-8 BOM
```

This occurs when a file starts with:

```text
EF BB BF
```

A strict `utf-8` reader may reject it.

Preferred project output:

```text
UTF-8
without BOM
```

---

# 16. Why PowerShell Redirection Can Be Dangerous for JSON

Avoid treating commands such as:

```text
python script.py > report.json
```

as the preferred way to create scientific artifacts.

PowerShell encoding behavior can vary.

Similarly, historical use of:

```text
Out-File -Encoding utf8
```

created BOM-related compatibility problems.

Preferred approach:

```python
Path("report.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
```

Scientific runners should write their own evidence files.

---

# 17. Invalid JSON

If a report cannot be parsed:

Check whether it contains:

```text
terminal prompts
warnings
PowerShell formatting
partial output
stack traces
```

Scientific JSON should contain only JSON.

Do not paste console output into an evidence file.

---

# 18. Feature Count Mismatch

Expected current portable model feature count:

```text
331
```

Possible error:

```text
expected 331 features
received 330
```

Do not solve by:

```text
padding with zero
dropping another feature
disabling the check
```

Investigate:

```text
manifest
feature projection
feature generation
column filtering
missing column
extra column
```

---

# 19. Feature Fingerprint Mismatch

Expected feature-column fingerprint:

```text
65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2
```

A mismatch may mean:

```text
feature added
feature removed
feature reordered
wrong manifest
wrong dataset
different experiment
```

Even if:

```text
X.shape[1] == 331
```

the matrix can still be invalid.

Do not disable the fingerprint check.

---

# 20. Non-Finite Feature Values

Possible failure:

```text
NaN
Infinity
-Infinity
```

Investigate feature-generation source.

Common causes:

```text
division by zero
insufficient warm-up
missing bars
invalid rolling window
corrupted source values
```

Do not automatically replace non-finite values with zero unless the frozen feature contract explicitly requires that behavior.

---

# 21. Decision-Time Ordering Failure

The supervised batch requires chronological consistency.

Possible causes:

```text
unsorted input
duplicate timestamps
timezone conversion
row concatenation
incorrect resampling
```

Fix chronology at the responsible data layer.

Do not sort only model outputs while leaving features/targets misaligned.

---

# 22. Target Class Error

Expected target classes:

```text
[-1, 0, 1]
```

Meaning:

```text
-1 SHORT
 0 NO_TRADE
 1 LONG
```

Unexpected classes may indicate:

```text
wrong target file
wrong normalization
corrupt dataset
different target contract
```

Do not silently remap unknown values.

---

# 23. Tradeability Linkage Failure

Required:

```python
target_tradeable = (target_class != 0).astype("int8")
```

Examples:

```text
SHORT → 1
NO_TRADE → 0
LONG → 1
```

If this fails, investigate target construction/alignment.

Do not edit tradeability labels independently just to satisfy the assertion.

---

# 24. Dataset SHA Mismatch

Current frozen portable dataset SHA256:

```text
cff75b0686383a3ab6f8352bfcdcd55308b99b7a4c6edbf7d2e7215f6f33dd07
```

If actual SHA differs:

```text
STOP
```

Possible explanations:

* wrong file;
* modified file;
* new dataset;
* incomplete copy;
* different research lineage.

Do not update the expected SHA merely because another file exists.

First establish what dataset is actually being used.

---

# 25. Manifest SHA Mismatch

Expected manifest SHA256:

```text
1b8e3599b227c9cbbc6b12f8ab0e275ca4deb4a65839fb626ca90720d59512dc
```

A mismatch can alter:

```text
feature definitions
column order
target columns
dataset identity
contract metadata
```

Treat it as a scientific identity change.

---

# 26. Candidate Registry Fingerprint Mismatch

Frozen registry fingerprint:

```text
b8088bb34ce8940f7de5946fbb9b0fd20f40d7cc93a76b76fd7975591f00066c
```

If it changes:

```text
candidate configuration
candidate ordering
selection rules
anti-overfit policy
```

may have changed.

Do not continue the frozen C04 lineage until the reason is known.

---

# 27. Model Artifact SHA Mismatch

Expected model artifact SHA256:

```text
48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769
```

A mismatch is critical.

Possible causes:

```text
model overwritten
new fit
file corruption
different serialization
wrong artifact
```

Do not simply update documentation to the new hash.

The current frozen research result belongs to the exact frozen artifact.

---

# 28. `joblib` / NumPy Warnings

Model artifact loading may produce deprecation warnings originating from package compatibility.

Warnings are not automatically scientific failures.

If:

```text
artifact SHA matches
model structure verifies
tests pass
predictions remain contract-valid
```

the warning may be non-blocking.

However, do not globally suppress it without investigation.

Package upgrades should eventually include explicit compatibility verification.

---

# 29. Pandas Fragmentation Warning

Synthetic tests that insert 331 columns one by one can produce:

```text
PerformanceWarning:
DataFrame is highly fragmented
```

This usually indicates inefficient test construction.

If:

```text
tests pass
values are correct
science is unchanged
```

it is generally non-blocking.

The fixture may later be optimized using vectorized DataFrame construction.

---

# 30. Wrong Model Class Order

Expected C04 class order:

```text
[-1, 0, 1]
```

Never assume:

```text
probabilities[:, 0] == LONG
```

Current interpretation:

```text
column 0 = SHORT
column 1 = NO_TRADE
column 2 = LONG
```

If `model.classes_` differs:

```text
STOP
```

Do not reorder probability columns by guesswork.

---

# 31. Probability Sum Failure

For each row:

```text
P(SHORT)
+
P(NO_TRADE)
+
P(LONG)
≈
1
```

If not:

Investigate:

```text
model output
hierarchical probability composition
column ordering
normalization
NaN/inf
```

Do not normalize arbitrary invalid probabilities after inference unless explicitly part of the frozen model contract.

---

# 32. VALIDATION Access Error

Original portable loader public methods intentionally block direct VALIDATION access.

Examples conceptually include:

```text
VALIDATION_FEATURE_ACCESS_NOT_AUTHORIZED
VALIDATION_TARGET_ACCESS_NOT_AUTHORIZED
```

This is expected behavior.

Do not remove these guards.

The completed real VALIDATION operation used a dedicated authorized one-time source adapter.

---

# 33. TEST Access Error

The original loader also blocks:

```text
TEST feature access
TEST target access
```

This is currently correct.

TEST remains protected until the dedicated TEST gate is implemented and authorized.

Do not expose TEST by modifying the original loader.

---

# 34. VALIDATION Is Already Consumed

Current state:

```text
validation_consumed = true
validation_rerun_authorized = false
```

If a developer thinks:

> I will rerun VALIDATION just to verify one change.

Do not.

The current C04 validation result is already scientifically consumed.

Use:

```text
synthetic tests
TRAIN data
existing frozen evidence
```

for development.

---

# 35. Validation Ledger

Current ledger:

```text
xauusd_portable_331_one_time_validation_access_ledger.json
```

Final status:

```text
VALIDATION_COMPLETE_ACCEPTED
```

Expected read attempt count:

```text
1
```

Expected consumed state:

```text
true
```

Do not reset this file.

---

# 36. Never Delete a Ledger to Enable a Rerun

Deleting:

```text
xauusd_portable_331_one_time_validation_access_ledger.json
```

does not make the real-world VALIDATION split untouched again.

Scientific consumption is a historical fact.

The ledger records that fact.

It does not create it.

---

# 37. Pre-Read Technical Failure

For future protected TEST operations:

If failure occurs before any TEST feature/target value is read, recovery may potentially be allowed if the frozen protocol explicitly supports it.

Examples:

```text
wrong model SHA
missing protocol
invalid preflight
missing source module
```

The ledger should prove:

```text
read_attempt_count = 0
holdout_consumed = false
```

before retry authorization is considered.

---

# 38. Post-Read Technical Failure

If TEST values have already been loaded:

```text
holdout consumed
```

even if:

```text
JSON writing later fails
console printing fails
metric report crashes
```

Do not rerun automatically.

Inspect the persistent ledger first.

---

# 39. Dry Preflight Fingerprint Mismatch

Current completed VALIDATION preflight fingerprint:

```text
5ee6d0948d93f83f7969662e103066f1a09d7b081883290aba104b52f0038f41
```

A future TEST preflight will have its own fingerprint.

If execution requires one fingerprint and the stored preflight has another:

```text
STOP
```

It usually means provenance or state changed after preflight.

---

# 40. Result Fingerprint Mismatch

Current VALIDATION result fingerprint:

```text
ea8b482e60f854f58e27f3be387b7bb82f0c16a6cf1a99555b12643aeeca5fa1
```

If recalculating canonical fingerprint produces another result:

Possible causes:

```text
evidence edited
serialization contract changed
result tampered
wrong file
```

Do not hand-edit the expected fingerprint.

---

# 41. Validation Freeze Mismatch

Current frozen validation fingerprint:

```text
521a97b41a86231b049cc65aebfd85ffc7c83ae7141134d6ae1158d112b1468c
```

The freeze binds:

```text
preflight
result
ledger
model identity
feature identity
acceptance decision
```

A mismatch means the provenance chain is inconsistent.

---

# 42. Git Shows Unexpected Files

Before committing:

```powershell
git status --short
```

Investigate unexpected:

```text
output.json
temporary files
cache files
model binaries
credentials
debug files
```

Do not stage everything blindly with:

```text
git add .
```

for scientific gates.

Prefer exact files.

---

# 43. Accidental Generated File

If an unrelated generated file appears:

```text
do not delete automatically
```

First determine:

```text
Is it scientific evidence?
Is it referenced by another report?
Is it historical output?
Is it untracked temporary output?
```

Use:

```powershell
git status --short
```

and:

```powershell
git log --oneline -- exact_filename
```

when appropriate.

---

# 44. Git Commit Contains Too Much

Inspect current commit before pushing:

```powershell
git show --stat --oneline HEAD
```

Inspect files:

```powershell
git status --short
```

Scientific commits should ideally group one logical gate.

Examples:

```text
implement TEST source
freeze TEST preflight
freeze TEST result
documentation refresh
```

rather than mixing unrelated development.

---

# 45. Local Git Ahead of GitHub

Local work may contain commits not yet present on remote GitHub.

Check:

```powershell
git status
```

and:

```powershell
git log --oneline -10
```

Do not assume the public GitHub documentation is the latest scientific state until local work has been deliberately pushed.

---

# 46. Secrets Before Git Push

Before staging or pushing, check that no file contains:

```text
MT5 passwords
account credentials
API tokens
private keys
personal authentication tokens
```

Use environment variables or local `.env`.

Never put real credentials into documentation examples.

---

# 47. Broker Symbol Not Found

Possible issue:

```text
XAUUSD
```

may be named:

```text
XAUUSDm
```

or another broker-specific variant.

Production portability should eventually normalize symbol identity.

Do not hard-code a new broker symbol across random modules.

Use a dedicated broker/symbol abstraction.

---

# 48. Broker Time Mismatch

Symptoms may include:

```text
D1 features differ
session features shift
H4 alignment differs
historical/live parity fails
```

Possible cause:

```text
broker server timezone
```

Production work should canonicalize timestamps before model feature generation.

Do not simply add/subtract a fixed number of hours without a documented time contract.

---

# 49. D1 Candle Mismatch

Two brokers may construct D1 candles differently.

Symptoms:

```text
different daily OHLC
different ATR
different structure
different D1-derived features
```

Future production architecture should reconstruct canonical D1 bars rather than assuming broker-native D1 semantics are identical.

---

# 50. Missing Bars

Symptoms:

```text
NaN
incorrect rolling values
wrong MTF alignment
stale features
```

Required production behavior should eventually include:

```text
detect missing bars
reject invalid feature batch
or
apply explicitly documented recovery
```

Do not silently manufacture candles without a frozen rule.

---

# 51. Stale Data

A valid-looking 331-feature vector can still be unsafe if it is old.

Production inference should eventually verify:

```text
latest market timestamp
expected update interval
current broker state
```

Stale data should fail closed.

---

# 52. Model Predicts Mostly One Class

Possible causes:

```text
real regime shift
feature drift
wrong feature ordering
broker-time mismatch
D1 mismatch
stale input
integration bug
```

Do not immediately change thresholds.

First verify feature and artifact contracts.

---

# 53. Trade Coverage Changes Dramatically

Historical VALIDATION coverage:

```text
0.7541213375158513
```

Future shadow coverage may differ.

If it becomes extreme:

```text
near 0
or
near 1
```

investigate:

```text
feature drift
market regime
prediction integration
class-order handling
broker semantics
```

Do not tune against the symptom before diagnosing the cause.

---

# 54. Good Accuracy but Weak Directional Behavior

This is a three-class problem.

A model can achieve acceptable-looking overall statistics while doing poorly on SHORT/LONG.

Always inspect:

```text
directional macro-F1
SHORT recall
LONG recall
trade coverage
class distribution
```

Do not evaluate the project using raw accuracy alone.

---

# 55. Probability Metrics Worse Than Baseline

Log-loss and Brier are useful diagnostics.

For the current validation protocol they are:

```text
REPORT ONLY
```

They do not authorize post-hoc calibration for the frozen C04 experiment.

A weak probability metric should be documented, not retroactively optimized against consumed VALIDATION.

---

# 56. Documentation Contradicts JSON

Machine-readable frozen evidence is authoritative for scientific gate state.

If Markdown says:

```text
VALIDATION pending
```

but frozen evidence proves:

```text
VALIDATION accepted and consumed
```

the Markdown is stale.

Update documentation.

Do not edit evidence to match stale documentation.

---

# 57. Documentation Contradicts Code

For runtime numerical settings that have not been frozen in research documentation:

```text
code/config is authoritative
```

Do not invent a number in Markdown.

Example:

If exact risk percentage has not been verified:

Bad:

```text
risk = 1%
```

Better:

```text
RiskEngine/config owns the active numerical risk setting.
```

---

# 58. Broad Regression Fails After Focused Tests Pass

Possible causes:

```text
shared contract changed
import side effect
global state
old test expecting obsolete behavior
unintended file modification
```

Do not revert a scientifically correct contract merely to satisfy an obsolete test.

Determine whether:

```text
implementation is wrong
or
test is stale
```

Update only the responsible side.

---

# 59. When to Stop

Stop the current operation if any of these occur:

```text
unknown model SHA
unknown dataset SHA
unknown feature order
TEST accidentally accessed
consumed ledger inconsistent
unexpected live-order path
account credentials exposed
non-finite production features
time alignment unknown
```

Failing closed is expected behavior.

---

# 60. Escalation Checklist for Developers

When you cannot solve an issue, collect:

```text
[ ] exact command
[ ] exact traceback
[ ] git commit
[ ] git status --short
[ ] affected filename
[ ] relevant fingerprint
[ ] whether protected data was read
[ ] ledger state if applicable
[ ] focused test result
```

This is more useful than reporting:

```text
"It doesn't work."
```

---

# 61. Current Critical Identities

Feature columns:

```text
65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2
```

Dataset:

```text
cff75b0686383a3ab6f8352bfcdcd55308b99b7a4c6edbf7d2e7215f6f33dd07
```

Candidate registry:

```text
b8088bb34ce8940f7de5946fbb9b0fd20f40d7cc93a76b76fd7975591f00066c
```

Model artifact:

```text
48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769
```

VALIDATION protocol:

```text
ce78180a5f2472c36c74cea2c447307641aa3d5fedfb7a01d9b65260b5a6fcea
```

VALIDATION result:

```text
ea8b482e60f854f58e27f3be387b7bb82f0c16a6cf1a99555b12643aeeca5fa1
```

VALIDATION freeze:

```text
521a97b41a86231b049cc65aebfd85ffc7c83ae7141134d6ae1158d112b1468c
```

---

# 62. Golden Troubleshooting Rules

```text
1. Diagnose before changing.

2. Fix the smallest responsible layer.

3. Never disable a fingerprint check to make code run.

4. Never reset a consumed holdout ledger.

5. Never tune against consumed VALIDATION.

6. Never inspect TEST to debug ordinary code.

7. Prefer synthetic fixtures for protected-data logic.

8. Preserve artifact provenance.

9. Treat encoding separately from scientific content.

10. When scientific state is uncertain, fail closed.
```

---

# 63. Final Principle

The most dangerous failure is not always a Python exception.

A Python exception is often visible.

More dangerous is:

```text
code runs successfully
but
wrong data / wrong feature / wrong model / wrong time semantics are used
```

PulseViper troubleshooting therefore focuses on both software correctness and scientific identity.
