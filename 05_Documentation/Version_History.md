# PulseViper XAU AI — Version History & Research Timeline

## 1. Purpose

This document records the major engineering and research milestones of PulseViper XAU AI.

It is not intended to list every small Git commit.

Instead, it explains:

* how the project evolved;
* why major architecture changes were made;
* which experiments are historical;
* which model lineage is current;
* which milestones are frozen;
* and where current development stands.

A new student should read this document after:

```text
README.md
Developer_Guide.md
Architecture.md
```

to understand how the current system came to exist.

---

# 2. How to Read This History

PulseViper development has included several generations of XAUUSD research.

Important distinction:

```text
HISTORICAL EXPERIMENT
        ≠
CURRENT FROZEN EXPERIMENT
```

Older V3/V4 results remain useful as research history.

They do not replace the current portable 331-feature C04 lineage.

---

# 3. Current Research Lineage

The current lineage is no longer the original C04-only forward lane.

```text
Portable 331 Feature Contract
        ↓
Historical C04 control
        ↓
30 matured Forward30 outcomes
        ↓
Weak forward discrimination
        ↓
G7-A → G7-B → G7-C → G7-D → G7-E
        ↓
G7-F-A → G7-F-B → G7-F-C
        ↓
G7-G-A → G7-G-B
        ↓
G7-H R03 prospective lane
        ↓
CURRENT: first genuine R03 capture blocked
```

Current remediation winner:

```text
R03_FLAT_EXTRA_TREES_SMOOTH
```

Historical C04 remains preserved as the control lineage. R03 is the active remediation lineage.

# 4. Current Repository Status

The current `main` branch contains the G7 remediation implementation, R03 prospective infrastructure, and subsequent documentation synchronization commits.

The latest scientific/protocol authority remains the frozen R03 recovery lane; documentation-only commits do not replace scientific evidence authority.

Current R03 state:

```text
R03 winner = R03_FLAT_EXTRA_TREES_SMOOTH
R03 sealed TEST = SEALED_TEST_CONFIRMED
R03 observations = 0
R03 anchors = 0
R03 matured outcomes = 0
R03 prospective evaluation = NOT STARTED
live_authorized = false
execution_authorized = false
```

First genuine capture and recovery attempts were blocked by:

```text
TIMESTAMP_BASIS_NOT_UNIQUELY_PROVEN
raw_tick=1790985539
candidate_count=0
```

This block is intentionally preserved. The timestamp basis must be proven or a valid fresh capture context obtained; the check must not be weakened.

# 4. G7 Remediation and R03 Prospective Validation

The first matured C04 forward sample set demonstrated weak forward discrimination. The project did **not** tune against those forward observations. Instead, a separate finite remediation lineage was frozen.

### G7 remediation sequence

- **G7-A:** remediation rules frozen.
- **G7-B:** data authority and protected-data boundaries frozen.
- **G7-C:** exact training snapshot frozen.
- **G7-D:** remediation research protocol frozen.
- **G7-E:** exactly six remediation candidates frozen before evaluation.
- **G7-F-A:** TRAIN + VALIDATION access authorized while TEST remained sealed.
- **G7-F-B:** all six candidates evaluated.
- **G7-F-C:** `R03_FLAT_EXTRA_TREES_SMOOTH` frozen as the final remediation winner.
- **G7-G-A:** sealed TEST confirmation criteria frozen.
- **G7-G-B:** one-shot sealed TEST consumed exactly once and confirmed.

G7-G-B confirmation:

```text
balanced_accuracy = 0.3636245672
macro_f1 = 0.3490621418
minimum_per_class_recall = 0.2983711747
multiclass_brier = 0.6647780980
multiclass_log_loss = 1.0958700266
status = SEALED_TEST_CONFIRMED
```

### G7-H R03 prospective lane

The R03 prospective validation contract is frozen with:

```text
minimum_matured_outcomes = 60
minimum_distinct_observation_utc_dates = 5
horizon = 12 completed M5 rows
profit_atr = 1.25
max_adverse_atr = 0.75
```

The train-only artifact, runtime binding, outcome maturer, collection controller, and first-capture/recovery runners are frozen.

The current collection state is:

```text
observations = 0
anchors = 0
matured_outcomes = 0
```

The first genuine capture and R1/R2 recovery attempts were blocked by:

```text
TIMESTAMP_BASIS_NOT_UNIQUELY_PROVEN
raw_tick=1790985539
candidate_count=0
```

This is intentionally preserved as a fail-closed evidence block. The timestamp proof must be established; the safety check must not be weakened.

Live and execution authorization remain disabled.

# 4. Early Core-System Development

The earlier PulseViper architecture established modular market-analysis and trading infrastructure.

Important system concepts included:

```text
market structure
liquidity
patterns
institutional zones
market regime
feature generation
confidence / permission
risk management
broker-aware sizing
account protection
execution
shadow operation
```

An important architectural decision emerged from this work:

> ML research should not be allowed to casually modify risk and execution behavior.

This separation remains a current project rule.

---

# 5. Historical V3 Model Generation

An earlier model generation used:

```text
333 features
```

under the historical V3 training contract.

Historical V3 work helped establish:

* end-to-end dataset handling;
* multi-class XAUUSD prediction;
* TRAIN / VALIDATION / TEST usage;
* probability metrics;
* per-class analysis;
* model artifact generation.

However, later work identified an important problem:

```text
historical model performance
        ≠
guaranteed broker portability
```

This motivated a deeper portability research lane.

---

# 6. Historical V4 Hierarchical Research

A later experimental architecture introduced a hierarchical classifier.

Conceptually:

```text
Stage A
NO_TRADE vs TRADEABLE

        ↓

Stage B
SHORT vs LONG
```

Final probabilities were combined conceptually as:

```text
P(SHORT)
=
P(TRADEABLE)
×
P(SHORT | TRADEABLE)

P(NO_TRADE)
=
1 - P(TRADEABLE)

P(LONG)
=
P(TRADEABLE)
×
P(LONG | TRADEABLE)
```

This architecture was scientifically interesting because it separated:

```text
Should we trade?
```

from:

```text
Which direction?
```

However, historical V4 research showed substantial generalization concerns and did not become the final portable winner.

Important lesson:

> More complex architecture is not automatically more robust.

---

# 7. Shift to Broker Portability Research

The next major research direction focused on broker portability.

Main question:

> Can the model use features whose meaning remains sufficiently stable when moving between XAUUSD brokers?

This work investigated areas such as:

```text
broker-sensitive features
time semantics
multi-timeframe alignment
D1 candle behavior
symbol naming
portable transformations
```

The result was a new portable feature lineage.

---

# 8. Portable 331 Feature Contract

The portable feature contract was frozen at:

```text
331 ordered features
```

Feature-column fingerprint:

```text
65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2
```

This became the input contract for the current model research.

Important architectural improvement:

```text
feature count
+
feature order
+
feature fingerprint
```

became part of model identity.

---

# 9. Portable Dataset Freeze

Current portable dataset identity:

```text
dataset_id:
portable_cff75b0686383a3ab6f8352b
```

Dataset SHA256:

```text
cff75b0686383a3ab6f8352bfcdcd55308b99b7a4c6edbf7d2e7215f6f33dd07
```

Manifest SHA256:

```text
1b8e3599b227c9cbbc6b12f8ab0e275ca4deb4a65839fb626ca90720d59512dc
```

Frozen TRAIN rows:

```text
69,966
```

This created a reproducible basis for current model research.

---

# 10. Portable TRAIN Loader

A dedicated portable loader was implemented.

Important module:

```text
02_AI/Dataset/portable_331_training_input_loader.py
```

Major responsibilities included:

```text
artifact discovery
manifest verification
feature-order enforcement
split validation
numeric matrix construction
target normalization
TRAIN supervised loading
```

Public VALIDATION and TEST access remained blocked during TRAIN research.

This was deliberate.

---

# 11. Target Access Contract

Target loading was separated and validated.

Current classes:

```text
-1 = SHORT
 0 = NO_TRADE
 1 = LONG
```

Required relationship:

```python
target_tradeable = (target_class != 0).astype("int8")
```

This prevented silent disagreement between directional class and tradeability label.

---

# 12. Portable TRAIN Supervised Batch

A complete supervised TRAIN batch was established.

Current shape:

```text
69,966 rows
×
331 features
```

Research checks included:

```text
feature finiteness
target validity
decision-time chronology
row alignment
feature order
dataset identity
```

---

# 13. TRAIN Research Protocol Freeze

Before candidate model fitting, the model-selection protocol was frozen.

Protocol characteristics:

```text
TRAIN only
4 chronological expanding folds
12-row purge
no shuffle
```

Forbidden during current candidate selection:

```text
VALIDATION peeking
TEST peeking
grid search
Bayesian optimization
threshold search
post-result candidate addition
results-driven feature selection
```

Parent protocol fingerprint:

```text
69e51e1b249b9da68cbf6f6778a8ae10f9f33f7082a07e5073a1ba731fa1640d
```

This was a major improvement in scientific discipline.

---

# 14. Candidate Registry Freeze

Exactly six candidates were frozen:

```text
C01_FLAT_LOGREG_BALANCED_C005

C02_FLAT_LOGREG_BALANCED_C020

C03_FLAT_HGB_SHALLOW

C04_FLAT_EXTRA_TREES_CONSTRAINED

C05_HIER_LOGREG_REGULARIZED

C06_HIER_HGB_LOGREG_CONSTRAINED
```

Registry fingerprint:

```text
b8088bb34ce8940f7de5946fbb9b0fd20f40d7cc93a76b76fd7975591f00066c
```

The registry was frozen before real candidate results.

---

# 15. Candidate Evaluation Infrastructure

A reusable candidate evaluator was implemented.

Important module:

```text
04_Testing/research/portable_331/train/evaluate_xauusd_portable_331_train_model_candidates.py
```

The evaluator supported:

```text
flat classifiers
hierarchical classifiers
fold-local preprocessing
fold-local class weighting
frozen probability order
eligibility rules
lexicographic model selection
```

It used a fixed 15-metric contract.

---

# 16. Metric Contract

Current main metrics include:

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

This metric set was reused later for VALIDATION.

---

# 17. Real TRAIN Walk-Forward Evaluation

All six candidates were evaluated across all four frozen TRAIN folds.

Walk-forward result fingerprint:

```text
15516174ba6f3d8932425b20dcde33db25c040e0901c86af39796f97847ac7ed
```

Four candidates were eligible under the frozen rules.

The winner was:

```text
C04_FLAT_EXTRA_TREES_CONSTRAINED
```

---

# 18. Why C04 Won

Primary selection priority:

```text
maximize worst-fold directional macro-F1
```

C04 TRAIN summary:

```text
mean directional macro-F1:
0.3105791161393638

worst-fold directional macro-F1:
0.25365034089349603

mean balanced accuracy:
0.35438789335022963

mean macro-F1:
0.2846765787595467
```

The project deliberately did not switch to another candidate after observing results.

---

# 19. C04 Winner Freeze

Winner configuration fingerprint:

```text
f1b11c6f91561f2eba1bd56195e2239e9598b1906c88f11ada67eac6cdeb09e3
```

Configuration:

```text
ExtraTreesClassifier

n_estimators = 500
max_depth = 10
max_features = 0.35
min_samples_leaf = 25
bootstrap = false
class_weight = balanced
random_state = 271828
n_jobs = -1
```

C04 became the frozen TRAIN-internal winner.

---

# 20. Full TRAIN Model Fit

The exact frozen C04 configuration was fitted on all:

```text
69,966 TRAIN rows
```

using:

```text
331 features
```

Artifact:

```text
xauusd_portable_331_c04_full_train_model.joblib
```

Artifact SHA256:

```text
48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769
```

Model record fingerprint:

```text
bd6d76f92d3c6274bed756683f4263b9cce9a3f0e5ffbb8bd4ba3fcbe6f6ff74
```

---

# 21. Model Artifact Verification

The serialized model was subsequently verified.

Verification covered:

```text
model file SHA
ExtraTrees model class
331 input features
classes [-1, 0, 1]
500 trees
frozen hyperparameters
parent provenance
```

Verification record fingerprint:

```text
a2759a429b90998a7d24c8b217e570813e36dcf43df5de6cf98daf875b8678ef
```

This established the exact artifact intended for holdout evaluation.

---

# 22. One-Time VALIDATION Protocol Freeze

Before VALIDATION values were read, an acceptance protocol was frozen.

Protocol fingerprint:

```text
ce78180a5f2472c36c74cea2c447307641aa3d5fedfb7a01d9b65260b5a6fcea
```

Hard requirements included:

```text
directional macro-F1 floor
balanced accuracy floor
macro-F1 floor
positive SHORT recall
positive LONG recall
trade coverage bounds
finite metrics
all target classes present
```

Log-loss and Brier remained report-only.

---

# 23. One-Time Validation Ledger Infrastructure

A persistent validation-access ledger was implemented.

Purpose:

```text
prove when protected values were first read
+
prevent performance-driven reruns
```

Important policy:

```text
pre-read technical failure
may be recoverable

post-read technical failure
consumes holdout
```

This formalized holdout governance.

---

# 24. Bounded Validation Source

A dedicated authorized source adapter was created.

It preserved the original loader's blocked public holdout accessors.

The adapter:

```text
verified loader source
verified manifest
read structural split information
located contiguous VALIDATION
read only VALIDATION value rows
stopped before TEST values
reused frozen feature/target normalization
```

Loader source SHA256:

```text
49c86c269f2742fec7c6991eaf7a8a9c0466066a3db230a80375ba2e2c33680c
```

---

# 25. Validation Dry Preflight

A final dry preflight was executed before consuming VALIDATION.

Preflight fingerprint:

```text
5ee6d0948d93f83f7969662e103066f1a09d7b081883290aba104b52f0038f41
```

Pre-read state:

```text
ledger_state = ABSENT

validation_read_attempt_count = 0

holdout_consumed = false
```

This proved the holdout was still protected immediately before execution.

---

# 26. Real Untouched VALIDATION

The first and only real VALIDATION execution completed successfully.

Status:

```text
ONE_TIME_VALIDATION_ACCEPTED
```

Key results:

```text
balanced_accuracy_3class:
0.37656763760203776

macro_f1_3class:
0.34890395261998247

directional_macro_f1_short_long:
0.33640257616029445

short_recall:
0.3190499510284035

long_recall:
0.529248683116163

predicted_trade_coverage:
0.7541213375158513

log_loss_3class:
1.0979186095143678

multiclass_brier:
0.6664287278633827
```

All frozen hard checks passed.

---

# 27. Validation Result Fingerprint

Result fingerprint:

```text
ea8b482e60f854f58e27f3be387b7bb82f0c16a6cf1a99555b12643aeeca5fa1
```

Scientific state became:

```text
validation_accepted = true
validation_consumed = true
validation_rerun_authorized = false
```

---

# 28. Validation Result Freeze

Validation result, ledger, model identity, feature identity, and preflight were frozen together.

Freeze fingerprint:

```text
521a97b41a86231b049cc65aebfd85ffc7c83ae7141134d6ae1158d112b1468c
```

Status:

```text
ONE_TIME_VALIDATION_RESULT_FROZEN_ACCEPTED
```

This closed the VALIDATION research gate.

---

# 29. Current Development Position

Current historical research status:

```text
Feature portability research         ✅
Portable 331 contract                ✅
TRAIN dataset                        ✅
TRAIN model research                 ✅
C04 winner                           ✅
Full TRAIN model                     ✅
Model verification                   ✅
Untouched VALIDATION                 ✅ PASS
Validation freeze                    ✅

Final TEST                           ⏳ NEXT
Final research verdict               ⬜
Production broker parity             ⬜
Shadow inference                     ⬜
Forward shadow validation            ⬜
Live promotion                       ⛔
```

---

# 30. Known Local Git Milestones

The following commit IDs are known from the current development record.

| Commit    | Milestone                                                       |
| --------- | --------------------------------------------------------------- |
| `67fccb4` | Implement XAUUSD portable 331 training input loader             |
| `62ce64b` | Freeze XAUUSD portable train target access contract             |
| `2ca78fd` | Implement XAUUSD portable train target loader                   |
| `afbb2da` | Freeze XAUUSD portable train supervised batch contract          |
| `ca7f156` | Implement XAUUSD portable train supervised batch                |
| `fb320cc` | Freeze XAUUSD portable train model research protocol            |
| `259e477` | Add XAUUSD portability research evidence and candidate registry |
| `9814160` | Implement XAUUSD portable train candidate evaluator             |
| `0650446` | Freeze XAUUSD one time validation preflight                     |
| `d70d5e0` | Freeze XAUUSD one time validation result                        |

This table intentionally lists only commit IDs that are known and reported.

Future documentation must not invent missing commit hashes.

Use Git to retrieve authoritative history:

```powershell
git log --oneline --decorate -30
```

---

# 31. Documentation Refresh Milestone

After the VALIDATION result was frozen, the project documentation began a major refresh.

Objective:

> Make the repository understandable to a new student without requiring private development history.

Documentation areas include:

```text
README.md
Developer_Guide.md
Architecture.md
Module_List.md
Development_Roadmap.md
Feature_List.md
Testing_Guide.md
Research_Evidence_Index.md
Troubleshooting.md
Trading_Rules.md
Version_History.md
Documentation_Maintenance_Guide.md
```

---

# 32. Important Historical Lesson — V3/V4

The legacy V3/V4 research demonstrated that:

```text
more complexity
        ≠
better generalization
```

and:

```text
historical performance
        ≠
broker portability
```

These lessons directly motivated the current finite-candidate, portable-feature, one-time-holdout methodology.

---

# 33. Important Historical Lesson — Encoding

Research development encountered JSON encoding problems caused by:

```text
UTF-16 shell output
UTF-8 BOM output
```

This led to the current evidence policy:

```text
machine-readable JSON
=
UTF-8 without BOM
```

Scientific runners should write their own JSON artifacts.

---

# 34. Important Historical Lesson — Exact Commands

A generic placeholder command was previously copied literally.

This led to a documentation rule:

> Always provide exact executable filenames in commands.

Prefer:

```powershell
python 04_Testing\exact_script.py
```

not:

```text
python SCRIPT_NAME.py
```

---

# 35. Important Historical Lesson — Finite Gates

The project moved toward:

```text
one finite engineering gate at a time
```

because large multi-component changes made it harder to distinguish:

```text
software failure
scientific failure
data failure
integration failure
```

Current preferred workflow:

```text
design
  ↓
implement
  ↓
compile
  ↓
focused tests
  ↓
integration
  ↓
authorized real operation
  ↓
freeze
  ↓
commit
```

---

# 36. Important Historical Lesson — Holdout Governance

The project evolved from ordinary evaluation toward explicit one-time holdout governance.

Current principle:

> A protected holdout should be treated as a consumable scientific asset.

This is why:

```text
protocol
preflight
ledger
bounded source
result
freeze
```

all exist.

---

# 37. Upcoming Version Milestones

## Next

```text
FINAL TEST INFRASTRUCTURE
```

Expected milestones:

```text
TEST protocol
TEST bounded source
TEST access ledger
TEST dry preflight
```

---

## Then

```text
FIRST AND ONLY REAL TEST
```

Expected outputs:

```text
TEST metrics
TEST result fingerprint
TEST freeze
```

---

## Then

```text
FINAL HISTORICAL RESEARCH VERDICT
```

Comparing:

```text
TRAIN
VALIDATION
TEST
```

---

## Production Lane

Expected milestones:

```text
broker-time canonicalization
canonical D1 reconstruction
production 331 feature parity
frozen-model inference adapter
shadow integration
forward shadow validation
```

---

# 38. Version Naming Guidance

New major research generations should receive new identifiers.

Examples:

```text
PORTABLE_331_V1
PORTABLE_331_V2
```

or another documented scheme.

Do not silently reuse:

```text
C04 frozen experiment
```

for a model whose:

```text
features
targets
thresholds
hyperparameters
dataset
```

have changed.

---

# 39. When to Add a Version-History Entry

Add an entry when one of these changes:

```text
major architecture
feature contract
target contract
dataset lineage
candidate registry
winner
model artifact
holdout protocol
holdout result
production architecture
risk/execution contract
shadow/live authorization
```

Do not add a history section for every formatting change.

---

# 40. Required Information for Future Milestones

A good history entry should record:

```text
What changed?
Why?
What became frozen?
What evidence exists?
What fingerprint identifies it?
What became authorized next?
What remained forbidden?
Which Git commit records it?
```

---

# 41. Current Scientific Boundary

At the time of this documentation version:

```text
C04 model:
frozen

Model SHA:
48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769

VALIDATION:
passed and consumed

VALIDATION rerun:
not authorized

TEST:
untouched

TEST execution:
not yet authorized

Shadow:
not authorized

Live:
not authorized
```

---

# 42. Final Historical Principle

PulseViper history should preserve failed and superseded ideas as well as successful ones.

The purpose of version history is not to make development look perfect.

Its purpose is to make future decisions understandable.

A failed experiment with clear provenance is more useful than a successful-looking result whose origin cannot be reconstructed.

<!-- REPOSITORY-ARCHITECTURE-MANAGED:START -->
## Repository Structure Stabilization

> Managed repository-history section.

Recent repository-structure milestones:

- `820d80f` — froze repository testing and evidence inventory.
- `bbce3fa` — froze the original repository migration manifest.
- `29da975` — reorganized unreferenced repository evidence JSON.
- `b1bc11f` — reorganized referenced repository evidence JSON with consumer
  path updates.
- `0c2fb24` — reorganized production-portability testing tools.

The portability migration moved 38 Python files, preserved frozen artifacts,
passed Python compilation, and passed 113 focused regression tests.

A subsequent architecture audit established the numbered top-level repository
layout as canonical and removed the empty duplicate `Data/` directory while
leaving `01_Data/` unchanged.

The original migration manifest is retained as historical planning evidence.
Further migration uses architecture V2 principles based on actual source
ownership, CI dependencies, dynamic-loading behavior, and path semantics.
<!-- REPOSITORY-ARCHITECTURE-MANAGED:END -->

<!-- REPOSITORY-EOL-GOVERNANCE:START -->
## Repository Line-Ending Governance

A repository-wide EOL audit established that tracked text is normalized to LF
in the Git index while the primary Windows worktree uses CRLF through
`core.autocrlf=true`.

No mixed source/documentation line endings were found.

The repository therefore adopted explicit `.gitattributes` text/binary
governance without performing blanket renormalization or forcing all worktree
files to LF. This preserves existing frozen and byte-sensitive compatibility
while making future Git behavior more predictable.
<!-- REPOSITORY-EOL-GOVERNANCE:END -->

<!-- REPOSITORY-MIGRATION-V2:START -->
## Architecture V2 Manifest Freeze

A second-generation repository migration manifest was introduced after the
architecture, documentation, UTF-8, and line-ending governance audits.

V2 records 174 remaining loose/root Python candidates and distinguishes
READY files from REVIEW_REQUIRED, FROZEN_STAY, and SUPPORT_STAY files.

This replaces filename-token migration as the decision mechanism for future
repository restructuring. Ambiguous ownership remains fail-closed rather than
being guessed.
<!-- REPOSITORY-MIGRATION-V2:END -->

<!-- V2-CORE-SAFE-A-MIGRATION:START -->
## First Architecture V2 Test Migration

The first executable Architecture V2 migration batch moved 18
HIGH-confidence, location-independent tests owned by `02_AI/Core` into
`04_Testing/ai/core/`.

The same gate updated 9 CI paths, preserved frozen compatibility material,
passed Python compilation, and passed the focused moved-Core pytest suite.

READY files with file-location dependencies were intentionally left at their
existing paths.
<!-- V2-CORE-SAFE-A-MIGRATION:END -->

<!-- V2-SHADOW-SAFE-A-MIGRATION:START -->
## Second Architecture V2 Test Migration

The second executable Architecture V2 migration moved 35 Shadow-owned tests
into `04_Testing/ai/shadow/` and updated 11 CI paths.

The initial post-move suite exposed one stale internal dotted module import.
Exactly one test required a structural import-path edit.

After repair, the focused Shadow suite passed all 662 tests. All 33 frozen
compatibility files remained unchanged, and neither permanently consumed
VALIDATION nor one-time TEST was executed.
<!-- V2-SHADOW-SAFE-A-MIGRATION:END -->

<!-- V2-FINAL-LOCATION-INDEPENDENT-BATCH:START -->
## Completion of Location-Independent V2 Test Migration

A final six-test location-independent batch populated the Common, Dataset, and
Objects source-aligned test directories.

Together with the completed Core and Shadow batches, 59 READY tests have now
been migrated.

Nineteen READY tests remain deliberately unmoved because their current
`__file__`/repository-depth behavior requires a dedicated bootstrap refactor.
<!-- V2-FINAL-LOCATION-INDEPENDENT-BATCH:END -->

<!-- V2-PYTEST-BOOTSTRAP-CONSOLIDATION:START -->
## Pytest Bootstrap Consolidation and Dataset Test Refresh

Redundant `__file__`-derived repository-root and `sys.path` bootstrap logic was
removed from 17 READY tests.

The tests remain at their original locations. Their focused suite passed 41
tests under the repository project `.venv`.

During verification, two existing Dataset tests were found to use obsolete
pre-InstrumentContext call signatures. They were updated to the current
fail-closed production contract using deterministic temporary-output fixtures.

No production Dataset behavior was changed.
<!-- V2-PYTEST-BOOTSTRAP-CONSOLIDATION:END -->

<!-- V2-DATABASE-IMPORT-NORMALIZATION:START -->
## Database Test Import Normalization

The remaining database-test import-path exception was removed.

`test_database.py` now uses canonical `02_AI.Database.database` module identity
instead of adding `02_AI` to `sys.path` and importing `Database.database`.

The test remains at its original path pending the coordinated 18-file
source-aligned relocation gate.
<!-- V2-DATABASE-IMPORT-NORMALIZATION:END -->

<!-- V2-READY-18-RELOCATION:START -->
## 18-File Source-Aligned READY Relocation

Eighteen READY tests moved into their source-aligned test domains.

The initial moves were `R100`. A stale human-readable path header in the moved
config test was then corrected with executable AST identity preserved after
docstring normalization.

The corrected reference audit found zero true external old-path consumers.

Source-aligned test population: 77.
<!-- V2-READY-18-RELOCATION:END -->

<!-- V2-V1-ROOT-ABSTRACTION-RELOCATION:START -->
## Final V2 READY Root-Sensitive Test Migration

`test_v1_health.py` was decoupled from `parents[1]` repository-root discovery,
converted to the shared `repo_root` pytest fixture, and relocated into the
Config-aligned test directory.

`04_Testing/conftest.py` now uses marker-based repository-root discovery.

The CI path was updated, and the V2 READY structural migration population
reached 78 executed tests with zero READY items pending.
<!-- V2-V1-ROOT-ABSTRACTION-RELOCATION:END -->

<!-- V2-REVIEW-INTEGRATION-BATCH-01:START -->
## First REVIEW_REQUIRED Integration Migration

Two reviewed cross-domain tests were moved into
`04_Testing/integration/`.

The readiness state now records 78 executed READY rows, 2 REVIEW_EXECUTED
rows, and 75 REVIEW_REQUIRED rows.

No production code or frozen research evidence was changed.
<!-- V2-REVIEW-INTEGRATION-BATCH-01:END -->

<!-- V2-REVIEW-DIAGNOSTICS-BATCH-01:START -->
## Root Diagnostic Reclassification

`test_logger.py` and `test_settings.py` were reclassified from misleading
root-level test names into standalone diagnostics.

Both now use explicit `main()` entrypoints and shared marker-based repository
bootstrap. Import-time diagnostic behavior and root-level pytest naming
ambiguity were removed.

Review state is now 4 REVIEW_EXECUTED and 73 REVIEW_REQUIRED.
<!-- V2-REVIEW-DIAGNOSTICS-BATCH-01:END -->

<!-- V2-SELF-TARGET-DIRECT-SCRIPT-ROOT-NORMALIZATION:START -->
## Direct-Script Test Root Normalization

Removed fixed `Path(__file__).resolve().parents[1]` repository discovery from
the Exness historical telemetry direct-script regression test.

The test now uses the centralized pytest `repo_root` fixture. No relocation or
review-state transition was performed.
<!-- V2-SELF-TARGET-DIRECT-SCRIPT-ROOT-NORMALIZATION:END -->

<!-- V2-FINAL-COORDINATED-CLEANUP:START -->
## Coordinated Architecture Cleanup (Gate 11)

Executed the final coordinated cleanup of all remaining 73 `REVIEW_REQUIRED` files across the repository in a single structured pass, incorporating all 11 non-negotiable safeguards:
- Machine-checkable relocation classification frozen prior to file moves;
- Data-building scripts (`build_exness_demo_xauusd_canonical_history.py`) cleanly owned by `04_Testing/production_portability/`;
- Authoritative taxonomy splitting research into `portable_331/train/`, `legacy_ml/`, `shadow_experiments/`, and `legacy_validation/`;
- Pytest collection preflight protected frozen holdout workflows via `collect_ignore` in `04_Testing/conftest.py`;
- Byte-identical preservation of all 33 frozen compatibility files and frozen model SHA256 (`48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769`);
- Zero stale dotted imports, old paths, or subprocess/loader target residue;
- Companion test contracts (`Path(__file__).with_name(...)`) preserved;
- Root `04_Testing/` cleaned to exactly 19 files (18 `FROZEN_STAY`, 1 `SUPPORT_STAY`);
- Full active test suites verified: 1174 tests passing with zero frozen suites collected;
- Historical V2 manifest files (`Repository_Migration_Manifest_v2.csv` and `.md`) preserved untouched.

Final migration state: 78 READY EXECUTED, 77 REVIEW_EXECUTED, 0 REVIEW_REQUIRED, 18 FROZEN_STAY, 1 SUPPORT_STAY.
<!-- V2-FINAL-COORDINATED-CLEANUP:END -->

<!-- GATE-12-TEST-PROTECTION:START -->
## Protected TEST Holdout Preservation (Gate 12)

The final TEST holdout remains protected and unconsumed. The one-time VALIDATION evaluation was completed, passed, and permanently frozen (`ONE_TIME_VALIDATION_ACCEPTED`).
<!-- GATE-12-TEST-PROTECTION:END -->

<!-- GATE-13-FEATURE-PARITY:START -->
## Production Broker Feature Parity (Gate 13)

Established 331-feature production parity on canonical broker historical snapshots:
- Feature column SHA256: `65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2`.
- Matches historical ML research feature vector with zero leakage.
<!-- GATE-13-FEATURE-PARITY:END -->

<!-- GATE-14-INFERENCE-ADAPTER:START -->
## Frozen C04 Production Inference Adapter (Gate 14)

Created `02_AI/Models/frozen_c04_inference_adapter.py` wrapping the frozen C04 ExtraTrees model (`48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769`):
- Implements deterministic raw argmax decision rule across classes `[-1, 0, 1]`.
- Enforces `live_authorized = False` and `shadow_authorized = False`.
<!-- GATE-14-INFERENCE-ADAPTER:END -->

<!-- GATE-15A-SHADOW-OBSERVER:START -->
## Forward Shadow Observation Infrastructure (Gate 15A)

Created `02_AI/Models/frozen_c04_shadow_observer.py`:
- Locked, durable, append-only ledger (`01_Data/Shadow/xauusd_frozen_c04_shadow_observations.jsonl`).
- Machine-readable freeze boundary (`2026-08-14T20:55:00Z`) and activation authority (`2026-09-06T13:20:00Z`).
- Provenance enforcement (`HISTORICAL_ENGINEERING`, `SYNTHETIC_ENGINEERING`, `TRUE_FORWARD_OBSERVATION`).
- Blocked outcome contract status (`BLOCKED_NOT_PREDEFINED`).
<!-- GATE-15A-SHADOW-OBSERVER:END -->

<!-- GATE-15B-A-ACQUISITION-ADAPTER:START -->
## MT5 Read-Only Forward Acquisition Adapter v2.1.0 (Gate 15B-A)

Reopened and hardened `02_AI/Adapters/mt5_read_only_forward_acquisition_adapter.py`:
- `MT5ReadOnlyCapabilityFacade` restricts connected MT5 access to approved read-only methods (`symbols_get`, `symbol_info`, `symbol_info_tick`, `copy_rates_from_pos`).
- Blocks 10 mutating broker/order APIs with `PermissionError`.
- Forbids forming candles (`start_pos >= 1`).
- Dynamically resolves per-row historical DST transitions under `NY_CLOSE_SERVER_WALL_CLOCK` without fixed broker offset assumptions.
<!-- GATE-15B-A-ACQUISITION-ADAPTER:END -->

<!-- GATE-15B-B-GENUINE-OBSERVATION:START -->
## First Genuine Read-Only Forward Observation Proof (Gate 15B-B)

Recorded first real forward observation from connected MetaTrader 5:
- Decision time: `2026-09-28T10:15:00Z`.
- Canonical instrument: `XAUUSD`.
- Status: Pre-contract observation (captured prior to Gate 15C activation); retained permanently for pipeline audit, strictly excluded from formal forward performance.
<!-- GATE-15B-B-GENUINE-OBSERVATION:END -->

<!-- GATE-15C-OUTCOME-CONTRACT:START -->
## Frozen C04 Forward Outcome Contract V1 (Gate 15C)

Created `02_AI/Models/frozen_c04_forward_outcome_contract.py`:
- Contract version: `FROZEN_C04_FORWARD_OUTCOME_CONTRACT_V1`.
- Contract fingerprint SHA256: `01fe52a2f068fcc8fb2fc5b89dd7e19dc974fc2d967cfb791e75c3415804ce87`.
- Target: `CLEAN_DIRECTIONAL_EXCURSION_V2` (1.25 ATR profit threshold, 0.75 ATR adverse excursion, 12 completed M5 rows).
<!-- GATE-15C-OUTCOME-CONTRACT:END -->

<!-- GATE-15D-A-ELIGIBILITY:START -->
## Prospective Forward Outcome Eligibility Authority (Gate 15D-A)

Created `02_AI/Models/frozen_c04_forward_outcome_eligibility.py`:
- Formal activation cutoff: `2026-09-28T11:16:59Z`.
- Observations prior to cutoff are permanently excluded from formal scoring.
<!-- GATE-15D-A-ELIGIBILITY:END -->

<!-- GATE-15D-B-POST-CONTRACT-OBSERVATION:START -->
## First Prospective Post-Contract Forward Observation (Gate 15D-B)

Acquired genuine post-contract observation proof:
- Decision time: `2026-09-28T11:45:00Z`.
- Passed Gate 15D-A prospective eligibility.
- **Formal Scoring Status**: Excluded from formal forward scoring (`POST_CONTRACT_ACQUISITION_PROOF_EXCLUDED_FROM_FORMAL_SCORING_MISSING_PROSPECTIVE_ANCHOR`) because it lacked a prospective outcome anchor at acquisition time. Valid as genuine acquisition proof only.
<!-- GATE-15D-B-POST-CONTRACT-OBSERVATION:END -->

<!-- GATE-15D-C-A-B1-HISTORICAL-CORRECTION:START -->
## Outcome Maturation Semantic Correction & Alignment [SUPERSEDED] (Gate 15D-C-A/B1 v1.1)

Corrected decision-bar timing semantics:
- Established that raw M5 `time` represents bar open, hence `decision_bar_open = decision_time - 5 minutes`.
- **Superseded Status**: Superseded by Maturer V2 because V1.1 retrospectively reconstructed decision close and ATR14 from later completed data.
<!-- GATE-15D-C-A-B1-HISTORICAL-CORRECTION:END -->

<!-- GATE-15D-C-B2A-ANCHOR:START -->
## Prospective Forward Outcome Anchor Authority V1 (Gate 15D-C-B2A)

Created `02_AI/Models/frozen_c04_forward_outcome_anchor.py`:
- Captures exact decision close and ATR14 from the **SAME acquisition snapshot** before future outcome rows exist (`SAME_ACQUISITION_SNAPSHOT_NO_FUTURE_M5_ROWS`).
- Enforces `FORMAL_MATURATION_REQUIRES_ANCHOR = true`.
- Locked append-only ledger `01_Data/Shadow/xauusd_frozen_c04_forward_outcome_anchors.jsonl`.
- Enforces orphan anchor retention rule.
<!-- GATE-15D-C-B2A-ANCHOR:END -->

<!-- GATE-15D-C-B2BC-MATURER-LEDGER-V2:START -->
## Anchor-Required Forward Outcome Maturer V2 & Outcome Ledger V2 (Gate 15D-C-B2B/B2C)

Published baseline commit `cbdeb30934213dc36863c334eb1e50879ba0dde1`:
- `02_AI/Models/frozen_c04_forward_outcome_maturer.py` (Maturer V2): Requires validated prospective anchor; strictly forbids post-hoc reconstruction of entry close and ATR14 (`POST_HOC_ENTRY_AND_ATR_RECONSTRUCTION_FORBIDDEN`).
- `02_AI/Models/frozen_c04_forward_outcome_ledger.py` (Ledger V2): Durably stores outcomes linked to prospective anchors and Maturer V2 into `01_Data/Shadow/xauusd_frozen_c04_forward_outcomes.jsonl`.
- Confirms existing 11:45 UTC observation is excluded from formal scoring (`POST_CONTRACT_ACQUISITION_PROOF_EXCLUDED_FROM_FORMAL_SCORING_MISSING_PROSPECTIVE_ANCHOR`).
- Prepares for Gate 15D-C-B2D (Genuine Prospective Observation + Same-Snapshot Anchor Integration).
<!-- GATE-15D-C-B2BC-MATURER-LEDGER-V2:END -->

