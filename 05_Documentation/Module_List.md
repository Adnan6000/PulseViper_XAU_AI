# PulseViper XAU AI — Module Reference & Developer Map

## 1. Purpose

This document is a practical map of important PulseViper modules.

It answers four questions for a new developer:

1. What does this module do?
2. What goes into it?
3. What comes out of it?
4. Is it safe to modify?

The repository contains both production/runtime modules and research/testing modules.

Do not assume that a file under `04_Testing/` is unimportant.

Many scientific contracts and evidence generators intentionally live there.

---

# 2. Module Safety Levels

Each module in this guide is conceptually classified as one of the following.

## GREEN — Safe research/documentation area

Usually safe for isolated development with focused tests.

Examples:

```text
report generators
documentation
synthetic tests
research inspectors
```

---

## YELLOW — Contract-sensitive

Changes may invalidate research artifacts.

Examples:

```text
feature projection
dataset loader
target normalization
model evaluator
```

A change requires careful contract review.

---

## RED — Protected runtime area

Do not change without a dedicated authorized task.

Examples:

```text
RiskEngine
trade_ready
execution
position sizing
account protection
```

---

# 3. `02_AI/Core/market_structure.py`

**Area:** Core market analysis
**Safety:** YELLOW

## Responsibility

Analyzes market structure.

Typical outputs may include:

```text
swing highs
swing lows
BOS
CHoCH
trend
internal/external legs
```

## Input

Conceptually:

```text
OHLC / market DataFrame
```

Example:

```text
timestamp
open
high
low
close
volume
```

## Output

Structured market-state information.

Example:

```text
trend = bullish
bos = true
choch = false
```

## Used by

Potentially:

```text
feature generation
liquidity analysis
confidence/context systems
```

## Student guidance

Good first task:

```text
read its tests
trace one DataFrame through the engine
document output columns
```

Avoid changing structural definitions without understanding downstream feature impact.

---

# 4. `02_AI/Core/liquidity_engine.py`

**Area:** Core market analysis
**Safety:** YELLOW

## Responsibility

Detects liquidity-related structures.

Typical concepts:

```text
EQH
EQL
buy-side sweeps
sell-side sweeps
inducement
liquidity pools
```

## Input

Conceptually:

```text
market DataFrame
+
market structure context
```

## Output

Liquidity flags and measurements.

## Example

```text
equal_high_detected = true
high_swept = true
close_back_below = true

→ possible buy-side liquidity sweep
```

## Modification risk

Changing sweep definitions may alter downstream model features.

Treat such a change as feature-semantic research.

---

# 5. `02_AI/Core/pattern_engine.py`

**Area:** Core analysis
**Safety:** YELLOW

## Responsibility

Detects pattern/regime behavior such as:

```text
compression
expansion
rectangles
breakouts
fake breakouts
```

## Input

```text
price data
+
volatility context
```

## Output

Pattern states/scores.

## Example

```text
range_width ↓
ATR ↓
candle_size ↓

→ compression = true
```

---

# 6. `02_AI/Core/institutional_zones.py`

**Area:** Core analysis
**Safety:** YELLOW

## Responsibility

Institutional-style price-zone analysis.

Typical concepts:

```text
order blocks
fair value gaps
imbalances
zones
```

## Important rule

Output is context/features.

It should not independently bypass the main trading permission/risk system.

---

# 7. `02_AI/Core/market_regime.py`

**Area:** Market-state classification
**Safety:** YELLOW

## Responsibility

Describes current market environment.

Possible outputs:

```text
trend
range
high volatility
low volatility
expansion
compression
```

## Why it matters

A model or trading rule can behave differently in different regimes.

Forward shadow testing should later compare performance by regime.

---

# 8. `02_AI/Core/feature_generator.py`

**Area:** Feature generation
**Safety:** YELLOW / HIGH CONTRACT SENSITIVITY

## Responsibility

Combines market-analysis outputs into machine-readable features.

Conceptual flow:

```text
Structure ──────┐
Liquidity ──────┤
Patterns ───────┤
Zones ──────────┤
Regime ─────────┼──→ Feature Generator
MTF Context ────┘
```

## Output

Feature values used by downstream AI/research pipelines.

## Important warning

Changing feature meaning may require:

```text
new feature contract
new dataset
new model lineage
```

Do not modify a frozen feature while continuing to claim the old fingerprint.

---

# 9. `02_AI/Core/confidence_engine.py`

**Area:** Trading context / decision support
**Safety:** RED/YELLOW depending on use

## Responsibility

Combines engine-level confidence or confluence information.

Potential output:

```text
combined confidence
directional confidence
engine agreement
```

## Important distinction

The frozen C04 model uses its own probability output.

Do not silently mix model probabilities with legacy confidence thresholds and claim it is the same ML experiment.

Such an integration requires an explicit shadow/inference contract.

---

# 10. `02_AI/Core/risk_engine.py`

**Area:** Risk management
**Safety:** RED — PROTECTED

## Responsibility

Risk-related trading controls.

Possible responsibilities include:

```text
position sizing
risk percentage
exposure checks
SL/TP risk
account protection
trade permission
```

## Modification rule

Do not modify RiskEngine to improve ML research metrics.

Model research and risk management must remain separate.

## Student guidance

Read-only study is encouraged.

Modification should happen only under an explicitly scoped runtime/risk task.

---

# 11. `market_dna.py`

**Area:** Candle / pattern analysis
**Safety:** YELLOW

The existing module documentation identifies a candle-DNA style engine.

Typical responsibility:

```text
single/multi-candle attributes
manipulation
impulse
trap
expansion
exhaustion
```

## Input

Single-candle or multi-candle vectors.

## Output

Candle personality/context encodings.

## Development rule

If outputs are consumed by model features, semantic changes require feature-contract review.

---

# 12. `db_archiver.py`

**Area:** Persistence / database
**Safety:** YELLOW

Existing project documentation describes a market database archiver.

Typical responsibility:

```text
market bars
calculated features
        ↓
SQLite persistence
```

Historical database path documented by the project:

```text
01_Data/pulseviper_market.db
```

## Developer warning

Do not overwrite immutable research evidence simply because database or archival logic changes.

Research datasets should be explicitly versioned/fingerprinted.

---

# 13. `02_AI/Dataset/portable_331_training_input_loader.py`

**Area:** Portable research dataset
**Safety:** YELLOW — FROZEN-CONTRACT SENSITIVE

This is one of the most important current research modules.

## Main class

```text
Portable331TrainingInputLoader
```

## Responsibilities

Includes:

```text
exact artifact discovery
manifest validation
feature-column validation
split validation
numeric conversion
target normalization
TRAIN feature loading
TRAIN target loading
supervised TRAIN batch creation
```

## Important methods

Current known methods include:

```text
inspect_contract()
load_train_features()
load_train_targets()
load_train_supervised()
```

Internal helpers include concepts such as:

```text
_discover_exact_artifact()
_validate_manifest()
_validate_split_structure()
_numeric_matrix()
_normalize_target_class_array()
_normalize_target_tradeable_array()
```

## Holdout methods

The original public accessors:

```text
load_validation_features()
load_validation_targets()
load_test_features()
load_test_targets()
```

were intentionally fail-closed during research.

Do not casually reopen them.

---

# 14. Portable TRAIN Batch Contract

The supervised TRAIN batch conceptually contains:

```text
dataset identity
manifest identity
feature columns
feature fingerprint
decision_time
X
target_class
target_tradeable
row count
```

Expected current dimensions:

```text
X.shape = (69966, 331)
```

---

# 15. `04_Testing/evaluate_xauusd_portable_331_train_model_candidates.py`

**Area:** ML research
**Safety:** YELLOW — SCIENTIFIC CONTRACT

## Responsibility

Evaluates the six frozen model candidates using the frozen TRAIN-only walk-forward protocol.

## Does

```text
candidate construction
fold-level model fitting
probability prediction
15-metric calculation
eligibility checks
lexicographic selection
```

## Does not

```text
read TEST
read portable VALIDATION
write live orders
change RiskEngine
```

## Important prediction classes

```text
[-1, 0, 1]
```

---

# 16. Evaluator Metric Contract

Required fold metrics:

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

A developer adding metrics should determine whether they are:

```text
report-only
```

or:

```text
selection-driving
```

before results are observed.

---

# 17. `04_Testing/run_xauusd_portable_331_candidate_evaluator_integration.py`

**Area:** Integration verification
**Safety:** GREEN/YELLOW

## Responsibility

Verifies that the candidate evaluator and real TRAIN supervised batch integrate correctly.

This type of runner confirms plumbing without necessarily performing the final candidate search.

## Student lesson

Integration tests answer:

> Do two real modules agree on their contracts?

This differs from a unit test.

---

# 18. `04_Testing/run_xauusd_portable_331_train_candidate_walk_forward_evaluation.py`

**Area:** Real TRAIN research
**Safety:** YELLOW / FROZEN EVIDENCE

## Responsibility

Executes the frozen six-candidate, four-fold TRAIN-only evaluation.

## Scientific boundary

It was allowed to use:

```text
TRAIN
```

and forbidden to use:

```text
portable VALIDATION
TEST
```

## Result

Winner:

```text
C04_FLAT_EXTRA_TREES_CONSTRAINED
```

---

# 19. `04_Testing/freeze_xauusd_portable_331_train_internal_winner.py`

**Area:** Research decision freeze
**Safety:** GREEN/YELLOW

## Responsibility

Freezes the TRAIN-internal winner after the walk-forward result.

## Important concept

This script should not:

```text
retrain models
invent new candidates
read VALIDATION
read TEST
```

It turns a research decision into immutable provenance.

---

# 20. `04_Testing/fit_xauusd_portable_331_c04_full_train_model.py`

**Area:** Model fitting
**Safety:** YELLOW — FROZEN MODEL

## Responsibility

Fits the exact frozen C04 winner on all:

```text
69,966 TRAIN rows
```

using:

```text
331 features
```

## Output

```text
xauusd_portable_331_c04_full_train_model.joblib
```

## Current artifact SHA256

```text
48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769
```

## Modification warning

Changing C04 configuration requires a new experiment.

Do not overwrite this artifact with a modified model.

---

# 21. `04_Testing/verify_xauusd_portable_331_c04_full_train_model_artifact.py`

**Area:** Artifact provenance
**Safety:** GREEN/YELLOW

## Responsibility

Confirms that the frozen `.joblib` artifact matches expected research provenance.

Checks include:

```text
artifact SHA
class order
feature count
model parameters
tree count
winner identity
parent fingerprints
```

## Student lesson

A serialized model is not sufficient evidence by itself.

Its provenance matters.

---

# 22. `04_Testing/design_xauusd_portable_331_one_time_validation_protocol.py`

**Area:** Holdout governance
**Safety:** YELLOW — FROZEN DECISION CONTRACT

## Responsibility

Defines VALIDATION acceptance rules before VALIDATION results are read.

Frozen hard requirements include:

```text
directional F1 floor
balanced accuracy floor
macro-F1 floor
SHORT recall > 0
LONG recall > 0
trade coverage range
all required metrics finite
all target classes present
```

## Why this module exists

Without it a researcher could inspect validation and then invent a convenient pass/fail rule.

---

# 23. `04_Testing/xauusd_portable_331_one_time_validation_core.py`

**Area:** Protected holdout infrastructure
**Safety:** YELLOW

## Responsibilities

```text
protocol validation
ValidationBatch validation
model inference validation
metric computation
acceptance gate
persistent access ledger
one-time consumption policy
```

## Important class

```text
ValidationAccessLedger
```

## Ledger principle

The ledger must exist before the first protected value read.

---

# 24. `ValidationAccessLedger`

Conceptual states:

```text
RESERVED_BEFORE_READ
READ_INITIATED_CONSUMED_BOUNDARY
VALIDATION_VALUES_LOADED
VALIDATION_COMPLETE_ACCEPTED
VALIDATION_COMPLETE_REJECTED
PRE_READ_TECHNICAL_FAILURE
CONSUMED_TECHNICAL_FAILURE
```

## Critical rule

```text
POST-READ FAILURE
        ↓
HOLDOUT CONSUMED
```

Do not rerun automatically.

---

# 25. `04_Testing/xauusd_portable_331_authorized_validation_source.py`

**Area:** Bounded validation data access
**Safety:** YELLOW / PROTECTED DATA

## Responsibility

Loads exactly the VALIDATION block without loading TEST feature/target values.

## Architecture

```text
Frozen dataset
    ↓
Read dataset_split structure
    ↓
Locate TRAIN / VALIDATION / TEST blocks
    ↓
Bounded VALIDATION read
    ↓
Stop before TEST values
```

## Reuses

Existing portable loader helpers for:

```text
manifest
features
numeric conversion
target normalization
```

## Important rule

The original loader's public holdout accessors remain unchanged.

---

# 26. `04_Testing/run_xauusd_portable_331_one_time_validation.py`

**Area:** One-time holdout runner
**Safety:** RED/YELLOW — CONSUMABLE SCIENTIFIC ASSET

## Responsibility

Controls:

```text
dry preflight
provenance checks
preflight fingerprint
ledger state
explicit one-time execution
result generation
```

## Default behavior

Dry preflight only.

## Real execution requires explicit authorization flag and exact preflight fingerprint.

This reduces accidental holdout consumption.

---

# 27. Current VALIDATION Runner Result

Current validation status:

```text
ONE_TIME_VALIDATION_ACCEPTED
```

Result fingerprint:

```text
ea8b482e60f854f58e27f3be387b7bb82f0c16a6cf1a99555b12643aeeca5fa1
```

VALIDATION is now consumed.

Do not execute the runner again for performance-driven reasons.

---

# 28. `04_Testing/freeze_xauusd_portable_331_one_time_validation_result.py`

**Area:** Evidence freeze
**Safety:** GREEN/YELLOW

## Responsibility

Binds together:

```text
preflight fingerprint
validation result fingerprint
validation ledger
model artifact
feature fingerprint
acceptance result
```

## Current freeze fingerprint

```text
521a97b41a86231b049cc65aebfd85ffc7c83ae7141134d6ae1158d112b1468c
```

## Current authorization

```text
TEST runner implementation = authorized next

TEST execution = not yet authorized

shadow = false

live = false
```

---

# 29. Test Files

Most important research modules should have focused tests.

Naming pattern:

```text
module.py
test_module.py
```

Examples:

```text
evaluate_xauusd_portable_331_train_model_candidates.py
test_evaluate_xauusd_portable_331_train_model_candidates.py
```

and:

```text
freeze_xauusd_portable_331_one_time_validation_result.py
test_freeze_xauusd_portable_331_one_time_validation_result.py
```

---

# 30. What Unit Tests Should Check

Examples:

```text
contract validation
tamper detection
shape validation
class order
probability sums
metric ordering
eligibility rules
ledger states
failure boundaries
```

Unit tests should prefer synthetic data when protected real data is unnecessary.

---

# 31. What Integration Tests Should Check

Examples:

```text
real module imports
loader/evaluator compatibility
real artifact identity
schema compatibility
package-aware imports
```

Integration does not always mean:

```text
run everything
```

A narrow real integration test is often better.

---

# 32. Generated JSON Evidence Files

Root-level JSON files are often scientific artifacts rather than ordinary logs.

Typical categories include:

```text
contract designs
integration reports
candidate evaluations
winner freezes
model-fit reports
artifact verification
holdout protocols
preflights
ledgers
holdout results
result freezes
```

Do not delete them simply because they look like generated output.

Check `Research_Evidence_Index.md` first.

---

# 33. Frozen C04 Model Artifact

File:

```text
xauusd_portable_331_c04_full_train_model.joblib
```

This is a binary model artifact.

Important:

```text
Do not overwrite.
Do not refit in place.
Do not change hyperparameters and save to same identity.
```

New experiments should produce new artifacts.

---

# 34. Root-Level Research Reports

A root report commonly contains:

```text
analysis_version
valid
research_scope
artifact identities
fingerprints
decision
scientific_policy
```

Always inspect:

```text
decision
```

before deciding what operation is authorized next.

---

# 35. `README.md`

**Area:** Onboarding
**Safety:** GREEN

Purpose:

```text
5–10 minute project orientation
```

It should tell a new developer:

```text
what project is
current status
where to start
what not to touch
where full documentation lives
```

---

# 36. `05_Documentation/Developer_Guide.md`

**Area:** Developer handbook
**Safety:** GREEN

Purpose:

```text
complete student/developer onboarding
```

Read before significant coding.

---

# 37. `05_Documentation/Architecture.md`

**Area:** System design
**Safety:** GREEN

Purpose:

```text
explain how all layers connect
```

Use it to determine which subsystem owns a proposed change.

---

# 38. `05_Documentation/Development_Roadmap.md`

**Area:** Project planning
**Safety:** GREEN

Purpose:

```text
what is done
what is current
what remains
```

This document should always distinguish:

```text
research complete
```

from:

```text
production/live ready
```

---

# 39. `05_Documentation/Feature_List.md`

**Area:** Feature semantics
**Safety:** GREEN documentation / YELLOW source semantics

Purpose:

```text
feature families
feature portability
feature contract
examples
```

A student researching feature changes should start here.

---

# 40. `05_Documentation/Trading_Rules.md`

**Area:** Trading behavior
**Safety:** GREEN documentation / RED underlying runtime

Purpose:

```text
trade permission
risk rules
execution boundaries
```

Do not change actual trading behavior by editing documentation alone.

Code remains authoritative.

---

# 41. `05_Documentation/Research_Evidence_Index.md`

**Area:** Scientific provenance
**Safety:** GREEN

Purpose:

Provide human-readable mapping from:

```text
research milestone
        ↓
JSON report
        ↓
fingerprint
        ↓
decision
```

This is particularly important because the repository contains many generated JSON evidence files.

---

# 42. `05_Documentation/Testing_Guide.md`

**Area:** Development workflow
**Safety:** GREEN

Purpose:

Explain:

```text
py_compile
unit tests
synthetic tests
integration tests
real protected operations
regression timing
```

---

# 43. `05_Documentation/Troubleshooting.md`

**Area:** Developer support
**Safety:** GREEN

Should document known problems such as:

```text
UTF-16 JSON
UTF-8 BOM
package-relative imports
wrong feature count
wrong artifact fingerprint
holdout ledger consumed
joblib NumPy warnings
PowerShell command mistakes
```

---

# 44. `05_Documentation/Version_History.md`

**Area:** Project history
**Safety:** GREEN

Should describe major milestones rather than every tiny commit.

Examples:

```text
portable feature contract
TRAIN loader
candidate registry
walk-forward winner
full TRAIN model
VALIDATION pass
final TEST
shadow integration
```

---

# 45. Module Modification Decision Table

| Module Area              | Student Read |    Student Test |               Modify Freely? |
| ------------------------ | -----------: | --------------: | ---------------------------: |
| Documentation            |          Yes |             N/A |                      Usually |
| Synthetic research tests |          Yes |             Yes |                      Usually |
| Report generators        |          Yes |             Yes |      With contract awareness |
| Candidate evaluator      |          Yes |             Yes |                    Carefully |
| Dataset loader           |          Yes |             Yes |                    Carefully |
| Feature generation       |          Yes |             Yes | New contract may be required |
| Target generation        |          Yes |             Yes |   New dataset lineage likely |
| Model artifact           |          Yes |          Verify |             Do not overwrite |
| RiskEngine               |          Yes |  Existing tests |                    Protected |
| Execution                |          Yes |    Shadow tests |                    Protected |
| TEST access runner       |          Yes | Synthetic first |             Highly protected |

---

# 46. Example — Which Module Should I Edit?

## Goal

“I want to explain a feature better.”

Edit:

```text
Feature_List.md
```

---

## Goal

“I want to add a diagnostic report.”

Likely:

```text
04_Testing/
```

with synthetic tests.

---

## Goal

“I want to change target labels.”

This is not a small module edit.

It affects:

```text
target contract
dataset
model research
holdout lineage
```

Create a new research plan.

---

## Goal

“I want to change lot sizing.”

This belongs to:

```text
RiskEngine / runtime
```

Protected area.

Do not treat it as ML research.

---

## Goal

“I want to test a new model.”

Do not overwrite C04.

Create a new research lineage using TRAIN-only protocol.

---

# 47. Student Exercise — Find a Module Contract

Choose:

```text
portable_331_training_input_loader.py
```

Then answer:

```text
What data can it read?

What is its frozen feature count?

What does load_train_supervised return?

Which public holdout methods are blocked?

Which helper validates feature columns?

What fingerprint protects the feature order?
```

If you can answer these questions, you understand the module better than by only reading its function names.

---

# 48. Student Exercise — Follow One Research Result

Start from:

```text
C04 winner
```

Then locate conceptually:

```text
candidate registry
        ↓
walk-forward evaluation
        ↓
winner freeze
        ↓
full TRAIN fit
        ↓
model verification
        ↓
validation protocol
        ↓
validation preflight
        ↓
validation result
        ↓
validation freeze
```

This exercise teaches how PulseViper research provenance works.

---

# 49. Current Module Development Priority

Current immediate priority:

```text
ONE-SHOT FINAL TEST INFRASTRUCTURE
```

Expected new components will conceptually include:

```text
TEST access ledger
TEST-only bounded source
TEST dry preflight
TEST one-shot runner
TEST result freeze
final research verdict
```

These should reuse current scientific patterns where appropriate without reopening consumed VALIDATION.

---

# 50. Future Module Priority

After final TEST:

```text
production broker feature adapter
broker-time canonicalizer
D1 reconstruction
portable 331 production projector
verified model inference adapter
shadow inference logger
forward-validation reporting
feature-drift monitoring
prediction-drift monitoring
```

These areas will bridge historical research and production-like operation.

---

# 51. Golden Rule for Module Development

Before modifying a file, classify it:

```text
DOCUMENTATION?
RESEARCH?
DATA?
FEATURE CONTRACT?
TARGET CONTRACT?
MODEL?
PROTECTED HOLDOUT?
RISK?
EXECUTION?
```

Then identify:

```text
inputs
outputs
tests
fingerprints
upstream dependencies
downstream dependencies
scientific authorization
```

Only then edit the module.

The most dangerous repository changes are not always syntax errors.

They are changes that still run successfully while silently invalidating a contract.

<!-- REPOSITORY-ARCHITECTURE-MANAGED:START -->
## Repository Structure Mapping

> Managed module-structure section.

### Production source domains

`02_AI` currently contains twelve source domains:

`Adapters`, `Common`, `Config`, `Core`, `Database`, `Dataset`, `Features`,
`Memory`, `Models`, `Objects`, `Shadow`, and `Utils`.

These domains are the preferred ownership basis for future unit-test
organization.

### Testing support domains

Current established testing structure:

- `04_Testing/production_portability/` — broker/production portability
  diagnostics and regression tests.
- `04_Testing/evidence/production_portability/` — portability evidence.
- `04_Testing/evidence/research/` — historical/research evidence.
- loose `04_Testing/*.py` — transitional mixed testing/research area still
  undergoing controlled classification.

`04_Testing/conftest.py` remains test-root support.

Frozen one-time holdout code remains at its established compatibility paths.

Root `test_logger.py` and `test_settings.py` are under architecture review;
the ownership audit found no pytest-style `test_*` functions in either file,
so they must not be treated as ordinary test modules solely because of their
filenames.
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
## Source-Aligned Core Tests

`04_Testing/ai/core/` now contains the first source-aligned Architecture V2
test batch.

The directory contains 18 tests whose ownership maps to `02_AI/Core` and whose
migration safety analysis found no dependency on the test file's own location.

Tests that use `__file__`, parent-depth assumptions, or external Python
consumers remain outside this directory until separately verified.
<!-- V2-CORE-SAFE-A-MIGRATION:END -->
