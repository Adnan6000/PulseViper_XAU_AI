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

Current active/frozen historical ML lineage:

```text
Portable 331 Feature Contract
        ↓
Portable Dataset
        ↓
TRAIN-only Research
        ↓
Six Frozen Candidates
        ↓
Purged Walk-Forward
        ↓
C04 Winner
        ↓
Full TRAIN Fit
        ↓
Artifact Verification
        ↓
Untouched VALIDATION
        ↓
VALIDATION PASS
        ↓
Validation Result Freeze
        ↓
Final TEST
        ⏳ NEXT
```

Current frozen model:

```text
C04_FLAT_EXTRA_TREES_CONSTRAINED
```

Current live state:

```text
live_authorized = false
```

---

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
04_Testing/evaluate_xauusd_portable_331_train_model_candidates.py
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
