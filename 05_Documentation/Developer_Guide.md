# PulseViper XAU AI — Developer & Student Guide

## Purpose

This is the main technical onboarding guide for developers, students, researchers, and maintainers working on PulseViper XAU AI.

The objective is that a new contributor should be able to enter the project without relying on private development history or previous chat context.

After studying this guide, you should understand:

* what the project does;
* how its major components interact;
* how the ML research process is controlled;
* how data moves through TRAIN, VALIDATION, and TEST;
* why fingerprints and JSON evidence exist;
* which parts of the system are frozen;
* how to develop safely;
* how to test changes;
* how to create a new experiment correctly;
* and when a change requires a new research lineage.

---

# 1. Mental Model of the Project

Do not think of PulseViper as one trading bot script.

Think of it as several systems connected by contracts.

```text
MARKET DATA SYSTEM
        ↓
FEATURE ENGINEERING SYSTEM
        ↓
PORTABILITY SYSTEM
        ↓
DATASET / TARGET SYSTEM
        ↓
ML RESEARCH SYSTEM
        ↓
MODEL ARTIFACT
        ↓
INFERENCE SYSTEM
        ↓
TRADING SAFETY SYSTEM
        ↓
RISK SYSTEM
        ↓
EXECUTION SYSTEM
```

A change in one layer can invalidate assumptions in another.

That is why PulseViper uses explicit contracts and fingerprints.

---

# 2. Research Lane vs Production Lane

The project has two fundamentally different types of work.

## Research Lane

Examples:

* feature research;
* dataset analysis;
* candidate model comparison;
* model validation;
* probability analysis;
* synthetic experiments.

Research code is commonly located under:

```text
04_Testing/
```

Research work may generate immutable JSON evidence.

---

## Production / Runtime Lane

Examples:

* broker connection;
* current market data;
* risk controls;
* lot sizing;
* execution;
* shadow orders;
* live orders.

Runtime changes carry higher operational risk.

Important runtime systems should not be modified simply because an ML metric looks weak.

---

# 3. Frozen Runtime Boundary

The following components are considered protected unless a dedicated task explicitly authorizes a change:

```text
MT5 order/execution semantics
RiskEngine
trade_ready
account protection
broker-aware sizing
core execution
shadow execution semantics
```

If you are working on a model and think:

> “I can improve the result by changing RiskEngine.”

Stop.

That would mix research-layer optimization with runtime-layer behavior.

First determine whether you are measuring:

```text
model quality
```

or:

```text
complete trading-strategy quality
```

They are different research questions.

---

# 4. Repository Navigation

The repository currently contains these major areas.

## `01_Data/`

Data-related resources.

Treat frozen research datasets as immutable unless a new dataset lineage is deliberately created.

---

## `02_AI/`

Main system code.

One important current dataset module is:

```text
02_AI/Dataset/portable_331_training_input_loader.py
```

The portable loader owns important responsibilities such as:

* exact artifact discovery;
* manifest validation;
* feature ordering;
* numeric matrix construction;
* target normalization;
* split structure validation.

Its original public VALIDATION and TEST accessors were deliberately fail-closed during model research.

Protected access should not be reopened casually.

---

## `04_Testing/`

This directory is much more than conventional unit tests.

It contains:

* unit tests;
* contract tests;
* design scripts;
* scientific protocols;
* candidate evaluators;
* integration runners;
* artifact verification;
* one-time holdout access machinery;
* research evidence generators.

Example current files include:

```text
04_Testing/evaluate_xauusd_portable_331_train_model_candidates.py

04_Testing/fit_xauusd_portable_331_c04_full_train_model.py

04_Testing/verify_xauusd_portable_331_c04_full_train_model_artifact.py

04_Testing/design_xauusd_portable_331_one_time_validation_protocol.py

04_Testing/xauusd_portable_331_one_time_validation_core.py

04_Testing/xauusd_portable_331_authorized_validation_source.py

04_Testing/run_xauusd_portable_331_one_time_validation.py

04_Testing/freeze_xauusd_portable_331_one_time_validation_result.py
```

Each important runner normally has a corresponding focused test file.

---

## `05_Documentation/`

Human-facing knowledge.

A future maintainer should not need to reverse-engineer the entire repository just to understand why a model exists.

---

# 5. Current ML Experiment

The current active/frozen model research lineage uses:

```text
331 broker-portable features
```

with three target classes:

```text
-1 = SHORT
 0 = NO_TRADE
 1 = LONG
```

The selected candidate is:

```text
C04_FLAT_EXTRA_TREES_CONSTRAINED
```

It has passed the one-time untouched VALIDATION gate.

The final TEST split remains protected.

---

# 6. Feature Contract

## Why feature contracts matter

Suppose a model was trained with:

```text
column 0 → H1 feature A
column 1 → H4 feature B
column 2 → D1 feature C
```

Later runtime code provides:

```text
column 0 → H4 feature B
column 1 → H1 feature A
column 2 → D1 feature C
```

The matrix shape remains identical.

The model may still run.

But the predictions are invalid.

This is one of the most dangerous ML integration errors because it may not raise an exception.

---

## Current frozen feature identity

Feature count:

```text
331
```

Ordered feature-list SHA256:

```text
65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2
```

Any production inference path must eventually verify:

```text
feature_count == 331

AND

feature_columns_sha256 ==
65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2
```

---

# 7. Target Contract

The frozen label contract is directional.

Parameters:

```text
profit_atr = 1.25
max_adverse_atr = 0.75
```

Conceptually:

## LONG

Future price must achieve sufficient favorable upward excursion while respecting the allowed adverse excursion.

## SHORT

Future price must achieve sufficient favorable downward excursion while respecting the allowed adverse excursion.

## NO_TRADE

Neither directional condition qualifies.

---

## Tradeability linkage

The project also uses:

```text
target_tradeable
```

Required relationship:

```python
target_tradeable = (target_class != 0).astype("int8")
```

Example:

```text
target_class = -1  → target_tradeable = 1
target_class =  0  → target_tradeable = 0
target_class =  1  → target_tradeable = 1
```

If this linkage fails, the supervised data contract is invalid.

---

# 8. Frozen TRAIN Dataset

Current portable TRAIN identity:

```text
dataset_id =
portable_cff75b0686383a3ab6f8352b
```

Rows:

```text
69,966
```

Features:

```text
331
```

Dataset SHA256:

```text
cff75b0686383a3ab6f8352bfcdcd55308b99b7a4c6edbf7d2e7215f6f33dd07
```

Manifest SHA256:

```text
1b8e3599b227c9cbbc6b12f8ab0e275ca4deb4a65839fb626ca90720d59512dc
```

The exact dataset identity matters.

Do not replace the file and continue using the old fingerprint.

---

# 9. TRAIN, VALIDATION, TEST

These are scientific roles, not merely CSV labels.

## TRAIN

TRAIN may be used for:

* fitting;
* candidate comparison;
* TRAIN-internal walk-forward;
* scaler fitting where candidate rules permit;
* class-weight computation where candidate rules permit.

---

## VALIDATION

VALIDATION is a holdout used after model-selection rules are frozen.

For the current C04 experiment:

```text
VALIDATION has already been consumed.
```

Current state:

```text
validation_accepted = true
validation_consumed = true
validation_rerun_authorized = false
```

A developer must not rerun VALIDATION simply to see whether a new tweak improves performance.

A tweak after validation creates a new research experiment.

---

## TEST

TEST is the final untouched holdout.

Current state:

```text
TEST not yet consumed.
```

TEST must not be used for:

* candidate selection;
* threshold tuning;
* calibration;
* feature selection;
* model architecture changes;
* hyperparameter changes.

---

# 10. What Is Data Leakage?

Data leakage happens when information that should be unavailable during model development influences the model or its decisions.

Examples:

## Leakage example 1

```text
Look at TEST metrics
        ↓
change max_depth
        ↓
run TEST again
```

TEST is no longer unbiased.

---

## Leakage example 2

Fit normalization on all rows before splitting.

```python
# BAD CONCEPTUAL EXAMPLE
scaler.fit(all_data)
```

The model indirectly learns statistics from future holdout rows.

---

## Leakage example 3

Select features using VALIDATION or TEST after examining their performance.

---

# 11. Why PulseViper Uses Purged Walk-Forward

Financial observations have time order.

Random K-fold cross-validation can create unrealistic training relationships.

Current research protocol uses:

```text
4 chronological folds
12-row purge
no shuffle
TRAIN only
```

A simplified structure:

```text
TIME ───────────────────────────────→

Fold 1:
[ TRAIN ]
         [PURGE]
                [VALIDATE]

Fold 2:
[      TRAIN       ]
                     [PURGE]
                            [VALIDATE]

Fold 3:
[           TRAIN            ]
                              [PURGE]
                                     [VALIDATE]
```

The purge separates training observations from the validation boundary.

This matters because target construction looks into a future horizon.

---

# 12. Candidate Registry

Before real fitting, exactly six candidates were frozen.

This prevents:

```text
run models
    ↓
see weak result
    ↓
invent candidate 7
    ↓
see result
    ↓
invent candidate 8
```

That process eventually overfits the research procedure itself.

---

# 13. Current Winner

Frozen winner:

```text
C04_FLAT_EXTRA_TREES_CONSTRAINED
```

Configuration:

```python
ExtraTreesClassifier(
    bootstrap=False,
    class_weight="balanced",
    max_depth=10,
    max_features=0.35,
    min_samples_leaf=25,
    n_estimators=500,
    n_jobs=-1,
    random_state=271828,
)
```

Configuration fingerprint:

```text
f1b11c6f91561f2eba1bd56195e2239e9598b1906c88f11ada67eac6cdeb09e3
```

---

# 14. Selection Philosophy

The winner was selected using a predeclared lexicographic policy.

Primary objective:

```text
maximize worst-fold directional macro-F1
```

Secondary objectives included:

* mean directional macro-F1;
* worst-fold balanced accuracy;
* mean 3-class macro-F1;
* directional stability;
* log-loss.

This matters because another candidate may look better on one secondary statistic.

Changing the selection rule after results are known would invalidate the protocol.

---

# 15. Full TRAIN Fit

After C04 was frozen, it was fitted once on the entire frozen TRAIN dataset.

Rows:

```text
69,966
```

Feature count:

```text
331
```

Artifact:

```text
xauusd_portable_331_c04_full_train_model.joblib
```

Artifact SHA256:

```text
48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769
```

---

# 16. Model Artifact Verification

Serialization alone is not enough.

The project subsequently verified:

* actual file SHA;
* model class;
* class order;
* feature count;
* number of trees;
* exact hyperparameters;
* parent research identities.

Current model verification fingerprint:

```text
a2759a429b90998a7d24c8b217e570813e36dcf43df5de6cf98daf875b8678ef
```

This gives a provenance chain such as:

```text
dataset
   ↓
feature contract
   ↓
candidate registry
   ↓
walk-forward result
   ↓
winner freeze
   ↓
full TRAIN fit
   ↓
model SHA
   ↓
artifact verification
```

---

# 17. Prediction Contract

Frozen model class order:

```text
[-1, 0, 1]
```

Equivalent interpretation:

```text
0th probability = SHORT
1st probability = NO_TRADE
2nd probability = LONG
```

Correct:

```python
probabilities = model.predict_proba(X)

prediction = model.classes_[
    probabilities.argmax(axis=1)
]
```

Do not assume:

```python
probabilities[:, 0]
```

means LONG.

Always respect `model.classes_`.

---

# 18. Threshold Tuning

The current experiment uses:

```text
argmax
```

No threshold search.

Therefore this would create a new model decision policy:

```python
if p_long > 0.60:
    return LONG
```

Even if the underlying ExtraTrees model remains unchanged.

A prediction policy is part of the scientific experiment.

---

# 19. Validation Acceptance Contract

Before viewing real VALIDATION results, the project froze hard acceptance requirements.

Important floors included approximately:

```text
Directional macro-F1 >= 0.253650
Balanced accuracy    >= 0.340404
Macro-F1             >= 0.245331
SHORT recall         > 0
LONG recall          > 0
Trade coverage       between 0.05 and 0.95
All required metrics finite
All target classes present
```

Probability metrics were intentionally report-only.

This prevents a rule such as:

> “Now that I have seen validation, I think 0.30 would be a good passing threshold.”

That is post-hoc decision making.

---

# 20. Real VALIDATION Result

The model passed its untouched VALIDATION gate.

Metrics:

```text
balanced_accuracy_3class
0.37656763760203776

macro_f1_3class
0.34890395261998247

directional_macro_f1_short_long
0.33640257616029445

short_recall
0.3190499510284035

long_recall
0.529248683116163

predicted_trade_coverage
0.7541213375158513

log_loss_3class
1.0979186095143678

multiclass_brier
0.6664287278633827
```

All frozen hard checks passed.

---

# 21. One-Time Holdout Ledger

One-time holdout evaluation uses an access ledger.

Why?

Because simply saying:

> “We only ran validation once.”

is weaker than storing evidence that records the read boundary.

Conceptual states include:

```text
RESERVED_BEFORE_READ
        ↓
READ_INITIATED_CONSUMED_BOUNDARY
        ↓
VALIDATION_VALUES_LOADED
        ↓
VALIDATION_COMPLETE_ACCEPTED
```

Once the protected read boundary has been crossed, performance-driven rerun is blocked.

---

# 22. Pre-Read vs Post-Read Failure

This distinction is critical.

## Pre-read technical failure

Example:

```text
model artifact cannot be loaded
```

and no holdout values were touched.

Infrastructure may be repaired safely.

---

## Post-read technical failure

Example:

```text
holdout values loaded
        ↓
metric script crashes
```

The holdout has already been exposed.

Do not simply rerun the evaluation.

Investigate the ledger and scientific policy.

---

# 23. Current Validation Freeze

Validation result fingerprint:

```text
ea8b482e60f854f58e27f3be387b7bb82f0c16a6cf1a99555b12643aeeca5fa1
```

Frozen validation-result fingerprint:

```text
521a97b41a86231b049cc65aebfd85ffc7c83ae7141134d6ae1158d112b1468c
```

Current state:

```text
validation_result_frozen = true
validation_accepted = true
validation_consumed = true
validation_rerun_authorized = false

test_runner_implementation_authorized_next = true
test_execution_authorized = false

shadow_authorized = false
live_authorized = false
```

---

# 24. Current Exact Development Position

```text
Portable feature research              DONE
Portable feature contract              DONE
Portable dataset                       DONE
TRAIN input loader                     DONE
TRAIN target loader                    DONE
Supervised batch                       DONE
Model research protocol                DONE
Candidate registry                     DONE
Candidate evaluator                    DONE
Real TRAIN walk-forward                DONE
Winner freeze                          DONE
Full TRAIN fit                         DONE
Model provenance verification          DONE
VALIDATION acceptance protocol         DONE
One-time validation core               DONE
Authorized validation source           DONE
Validation dry preflight               DONE
Real untouched VALIDATION              PASSED
Validation freeze                      DONE

One-shot TEST runner                    NEXT
Final TEST                             PENDING
Final model research verdict           PENDING
Production broker portability          PENDING
Shadow inference                       PENDING
Forward shadow validation              PENDING
Live promotion                         NOT AUTHORIZED
```

---

# 25. Finite-Gate Development Method

PulseViper development should happen one finite gate at a time.

Use:

```text
DESIGN
  ↓
IMPLEMENT
  ↓
COMPILE
  ↓
FOCUSED TEST
  ↓
SYNTHETIC / INTEGRATION
  ↓
AUTHORIZED REAL OPERATION
  ↓
FREEZE EVIDENCE
  ↓
DOCUMENT
  ↓
COMMIT
```

Avoid:

```text
change 10 things
run entire bot
see what happens
```

Small gates improve debugging and scientific traceability.

---

# 26. Example: Adding a Research Utility

Suppose you want to calculate a new diagnostic metric.

Safe workflow:

```text
1. Confirm metric does not change model selection.
2. Implement metric in an isolated research utility.
3. Write synthetic tests.
4. Run py_compile.
5. Run focused pytest.
6. Verify no VALIDATION/TEST access.
7. Generate report.
8. Document whether metric is informational or decision-making.
9. Commit.
```

If the metric will decide whether a model passes TEST, that rule must be declared before TEST values are seen.

---

# 27. Example: Adding a Feature

Adding a model feature is a much larger change.

Suppose you want:

```text
new_feature = H1_volume_ratio
```

Do not add it directly to the existing 331-feature model.

That would change the model contract.

Correct conceptual process:

```text
Research new feature
        ↓
Define semantics
        ↓
Check broker portability
        ↓
Add tests
        ↓
Create new feature-contract version
        ↓
Create new feature-list fingerprint
        ↓
Build new dataset lineage
        ↓
Create new research protocol
        ↓
Create new candidate/model experiment
```

The current 331 experiment remains frozen.

---

# 28. Example: Changing a Target

Suppose you want:

```text
profit_atr = 1.50
```

instead of:

```text
profit_atr = 1.25
```

This changes label semantics.

Therefore:

```text
OLD TARGET CONTRACT
        ≠
NEW TARGET CONTRACT
```

A new dataset and research lineage are required.

Do not reuse old model-performance claims.

---

# 29. Example: Model Hyperparameter Research

Suppose you want to test:

```python
max_depth=12
```

The current C04 experiment uses:

```python
max_depth=10
```

Because VALIDATION has already been consumed, you cannot modify C04 and evaluate the modified model against the same validation as if it were still untouched.

The new candidate belongs to a new research iteration.

---

# 30. Example: Production Broker Portability

A historically trained feature may depend on:

* broker timezone;
* broker symbol name;
* D1 session boundary;
* spread convention;
* bar availability;
* missing candles.

Therefore a production feature is not proven portable simply because Python can calculate it.

Example:

```text
Broker A daily candle:
00:00 → 23:59 UTC-like boundary

Broker B daily candle:
broker-server rollover boundary
```

If D1 features are calculated directly from broker-native candles, feature meaning may change.

Production work therefore requires canonical broker-time and D1 reconstruction.

---

# 31. Student Learning Path

A new student should not start with order execution.

Recommended learning stages:

## Level 1 — Orientation

Read:

```text
README.md
Developer_Guide.md
Architecture.md
```

Goal:

Understand the system.

---

## Level 2 — Tests

Read and execute safe synthetic tests.

Goal:

Understand how contracts are verified.

---

## Level 3 — Evidence

Study generated JSON research reports.

Goal:

Understand why reproducibility metadata exists.

---

## Level 4 — Data and Features

Study:

```text
02_AI/Dataset/
```

Goal:

Understand data identity and feature contracts.

---

## Level 5 — Model Research

Study candidate evaluator and walk-forward scripts.

Goal:

Understand how financial ML should be evaluated.

---

## Level 6 — Production Portability

Work on broker normalization, D1 reconstruction, and feature parity.

---

## Level 7 — Shadow / Runtime

Only after understanding protected runtime boundaries.

---

# 32. How to Read a Python Module

Before editing a module, answer:

```text
What is its responsibility?

What are its inputs?

What are its outputs?

What other modules depend on it?

Does it access protected data?

Does it modify persistent state?

Does it place or simulate orders?

Is its behavior frozen by a fingerprint or contract?
```

Then inspect its tests.

---

# 33. How to Read a Research JSON File

Most important fields:

## `analysis_version`

Which report contract created this artifact?

---

## `valid`

Did the gate complete successfully?

Expected:

```json
{
  "valid": true
}
```

---

## identity / fingerprint fields

Examples:

```text
dataset_sha256
manifest_sha256
model_artifact_sha256
contract_fingerprint
result_fingerprint
```

These connect evidence to exact artifacts.

---

## `decision`

Probably the most important human-facing section.

Example:

```json
{
  "test_access_authorized_next": true,
  "live_authorized": false
}
```

These mean different things.

---

## `scientific_policy`

This section records operations that were or were not performed.

Example:

```text
threshold_search_performed = false
probability_calibration_performed = false
portable_test_target_values_loaded = false
```

---

# 34. Machine-Readable JSON Encoding

Scientific JSON should use:

```text
UTF-8 without BOM
```

Preferred Python writing:

```python
from pathlib import Path
import json

report = {
    "valid": True
}

Path("report.json").write_text(
    json.dumps(
        report,
        indent=2,
        sort_keys=True,
    ) + "\n",
    encoding="utf-8",
)
```

Avoid relying on shell redirection for important JSON output when encoding may vary.

Historical development encountered both UTF-16 and UTF-8-BOM issues.

---

# 35. Testing Discipline

## Syntax

```powershell
python -m py_compile 04_Testing\exact_script.py
```

---

## Focused tests

```powershell
python -m pytest 04_Testing\test_exact_script.py -q
```

---

## Why focused first?

If one new module fails:

```text
focused test
```

usually provides a clearer signal than running hundreds of unrelated tests.

---

## Broader regression

Run broader regression after a meaningful increment has been completed.

Not after every single line change.

---

# 36. Do Not Use Placeholder Commands

Bad documentation:

```text
python SCRIPT_NAME.py
```

A student may paste it literally.

Prefer exact commands such as:

```powershell
python 04_Testing\freeze_xauusd_portable_331_one_time_validation_result.py
```

---

# 37. Git Discipline

Before committing:

```powershell
git status --short
```

Review exactly what changed.

Then stage only relevant files.

Example:

```powershell
git add README.md
git add 05_Documentation\Developer_Guide.md
```

Commit:

```powershell
git commit -m "Refresh project onboarding documentation"
```

Avoid unrelated files in a scientific milestone commit.

---

# 38. GitHub and Evidence

Important research evidence should eventually be represented by:

```text
code
+
tests
+
machine-readable report
+
human-readable documentation
+
Git commit
```

This lets a future researcher answer:

> Which exact code produced this result?

---

# 39. Secrets

Never commit:

```text
MT5 password
API secret
authentication token
private key
real account credential
```

Use:

```text
.env
```

and keep real secrets out of Git.

Example placeholders belong in:

```text
.env.example
```

---

# 40. Common Failure Patterns

## Wrong feature order

Model runs but semantics are invalid.

Fix:

Verify feature fingerprint.

---

## Dataset fingerprint mismatch

Do not continue.

Find out which artifact changed.

---

## Model SHA mismatch

Do not casually regenerate the model.

Determine why the artifact changed.

---

## VALIDATION rerun attempt

Current validation is consumed.

Do not rerun for performance tuning.

---

## TEST accessed too early

Stop.

TEST is the final holdout.

---

## Better metric after changing decision threshold

That is a new prediction policy.

Treat it as a new experiment.

---

# 41. Debugging Protected Data Operations

Always determine:

```text
Did the failure occur BEFORE protected values were read?

or

AFTER protected values were read?
```

This changes what operations remain scientifically valid.

Check the corresponding access ledger.

---

# 42. Definition of Done for Ordinary Code

A task is normally complete when:

```text
[ ] requirement understood
[ ] affected contract identified
[ ] implementation complete
[ ] syntax compile passed
[ ] focused tests passed
[ ] integration behavior checked
[ ] documentation updated
[ ] Git status reviewed
[ ] focused commit created
```

---

# 43. Definition of Done for Research

Additionally:

```text
[ ] dataset identity recorded
[ ] feature identity recorded
[ ] model identity recorded
[ ] selection policy declared before results
[ ] protected-data boundary respected
[ ] metrics finite
[ ] evidence JSON written
[ ] fingerprint frozen
[ ] next authorization explicitly recorded
[ ] no unauthorized tuning performed
```

---

# 44. Definition of Done for Production Integration

Additionally:

```text
[ ] broker behavior tested
[ ] feature parity proven
[ ] feature order enforced
[ ] stale data handled
[ ] missing bars handled
[ ] non-finite values fail closed
[ ] model SHA enforced
[ ] inference failure handled safely
[ ] RiskEngine unchanged unless explicitly authorized
[ ] shadow tests passed
[ ] no accidental live orders
```

---

# 45. Current Remaining Development

## Immediate

```text
One-shot TEST runner
```

Then:

```text
Final TEST
Final research verdict
```

---

## Production portability

Major tasks:

```text
broker symbol normalization
broker-time canonicalization
D1 reconstruction
331-feature live generation
feature parity testing
missing-data handling
```

---

## Shadow

Tasks:

```text
verified model loader
feature-contract enforcement
inference adapter
prediction logs
probability logs
shadow signal routing
hypothetical execution tracking
```

---

## Forward validation

Measure on genuinely unseen future data:

```text
directional stability
class balance
trade coverage
market regimes
spread behavior
cost sensitivity
drawdown
expectancy
feature drift
prediction drift
```

---

# 46. What Does “Live Ready” Mean?

It does **not** mean:

```text
VALIDATION passed
```

A live-ready system requires evidence across:

```text
historical generalization
+
final TEST
+
broker portability
+
runtime correctness
+
shadow stability
+
forward unseen-market behavior
+
transaction costs
+
risk controls
+
operational safeguards
```

Current state:

```text
live_authorized = false
```

---

# 47. Development Estimates

Rough active engineering effort remaining from the current stage:

```text
Final TEST lane:
~2–4 focused hours

Final research report:
~1–2 hours

Production broker portability:
~12–20 hours

Inference + shadow integration:
~8–14 hours

Production safety / monitoring:
~8–12 hours
```

Approximate active engineering total:

```text
35–55 hours
```

Calendar completion is longer because genuine forward-shadow validation requires future unseen market data.

A realistic full project horizon is roughly:

```text
3–6 weeks
```

depending on how much forward evidence is required.

---

# 48. Golden Rules

Remember these ten rules:

```text
1. Understand the contract before changing code.

2. Never use TEST for development.

3. Do not rerun consumed VALIDATION for performance tuning.

4. Never silently change the 331-feature order.

5. Never silently replace a frozen dataset or model.

6. Research improvements do not authorize runtime changes.

7. Use focused tests before real operations.

8. Protected-data failures must respect the ledger state.

9. Every major research decision should have evidence.

10. When identity or provenance is uncertain, fail closed.
```

---

# 49. New Developer Checklist

Before your first code change:

```text
[ ] README read
[ ] Developer Guide read
[ ] Architecture reviewed
[ ] Current roadmap reviewed
[ ] Relevant module identified
[ ] Relevant tests identified
[ ] Frozen boundary checked
[ ] No protected TEST access required
```

Before committing:

```text
[ ] py_compile passed
[ ] focused pytest passed
[ ] generated files reviewed
[ ] no credentials staged
[ ] documentation updated if behavior changed
[ ] git status reviewed
```

---

# 50. Current Project State Summary

Current frozen research state:

```text
Model:
C04_FLAT_EXTRA_TREES_CONSTRAINED

Features:
331 portable ordered features

TRAIN:
complete

TRAIN walk-forward:
complete

Full TRAIN fit:
complete

Model artifact verification:
complete

Untouched VALIDATION:
PASSED

VALIDATION:
consumed and frozen

Final TEST:
not yet consumed

Shadow:
not authorized

Live:
not authorized
```

Immediate next engineering objective:

```text
Implement and synthetically validate the
one-shot TEST evaluation infrastructure
before the first and only real TEST read.
```

---

# Final Principle

PulseViper is designed around one core engineering idea:

> A result is only useful when we can prove what data, features, model, code, and decision rules produced it.

When in doubt, preserve reproducibility, protect holdout data, and fail closed.

<!-- REPOSITORY-ARCHITECTURE-MANAGED:START -->
## Repository Structure Development Rules

> Managed engineering-governance section.

When adding or relocating project files:

1. Reuse the canonical numbered top-level architecture instead of creating a
   semantically duplicate top-level folder.
2. Treat `01_Data/` as the canonical data root.
3. Keep production implementation under the existing `02_AI` subsystem that
   owns the responsibility.
4. Keep tests and engineering diagnostics under `04_Testing/`.
5. Classify a test from actual source ownership, imports, dynamic loaders, CI
   usage, and runtime behavior rather than filename keywords alone.
6. Keep genuinely cross-subsystem tests in an integration-oriented testing
   area.
7. Keep research tooling separate from active runtime regression tests.
8. Never move or rewrite frozen one-time VALIDATION / TEST material merely to
   make the directory tree visually cleaner.
9. Update CI paths in the same engineering gate when a CI-addressed test moves.
10. Update relevant Markdown documentation in the same gate as architecture,
    path, module, testing, or evidence changes.
11. Avoid introducing new hard-coded `Path(__file__).resolve().parents[n]`
    dependencies. Prefer a stable project-root/path mechanism once the
    canonical helper is frozen.
12. Verify structure changes with syntax checks, focused tests where
    applicable, stale-path scans, frozen-artifact checks, and a clean Git
    working tree before committing.

Repository documentation is part of the implementation contract, not a
post-project reporting task.
<!-- REPOSITORY-ARCHITECTURE-MANAGED:END -->

<!-- REPOSITORY-EOL-GOVERNANCE:START -->
## Repository Line-Ending Policy

Git-normalized text in the repository index is canonical LF.

Developer worktrees may use platform-native line endings according to local Git
configuration. On the primary Windows development environment,
`core.autocrlf=true` means text files normally appear as CRLF in the worktree
while Git stores normalized LF content in the index.

This conversion is expected and must not be treated as repository corruption.

Engineering rules:

1. Do not run blanket repository renormalization merely to remove an LF/CRLF
   warning.
2. Do not introduce mixed line endings within a text file.
3. Do not force global `eol=lf` while frozen or byte-sensitive artifacts may
   depend on established worktree bytes.
4. Let `.gitattributes` define text/binary intent.
5. Treat data, evidence, model, and database formats conservatively when
   deciding whether Git should normalize their contents.
6. Documentation/code automation must preserve the existing newline convention
   of the file it edits unless a dedicated normalization gate explicitly
   authorizes otherwise.
7. Review `git diff --check` and Git EOL state before freezing repository-wide
   text-policy changes.
<!-- REPOSITORY-EOL-GOVERNANCE:END -->

<!-- V2-SHADOW-SAFE-A-MIGRATION:START -->
## Dynamic Test-Module Migration Rule

Relocating Python tests requires analysis of Python module identities as well
as filesystem paths.

A test can dynamically import another test using a dotted module string such
as:

`04_Testing.test_example`

When that target moves, the dotted module string is a structural dependency
and must be updated to its new module path.

Future migration preflights must inspect Python string constants and dynamic
imports for:

- exact old filesystem paths;
- `.py` basenames;
- dotted Python module paths;
- `importlib.import_module` targets;
- file-loader targets;
- `__file__` usage;
- repository-parent depth assumptions.

Focused post-move pytest remains mandatory because static migration analysis
must fail closed when runtime relationships are not fully proven.
<!-- V2-SHADOW-SAFE-A-MIGRATION:END -->

<!-- V2-PYTEST-BOOTSTRAP-CONSOLIDATION:START -->
## Pytest Bootstrap Ownership and Verification

Tests collected beneath `04_Testing/` must not add repository root to
`sys.path` individually when `04_Testing/conftest.py` already provides that
bootstrap.

Per-test `Path(__file__).resolve().parents[n]` plus `sys.path` mutation creates
folder-depth coupling.

Repository verification uses the project `.venv` interpreter and declared
dependencies; machine-wide Python installations are not the repository test
environment.

When structural cleanup exposes an already-stale test contract, production
fail-closed behavior must not be relaxed merely to satisfy the old test. The
test should instead be aligned to the current contract and isolated from
unnecessary external state where practical.
<!-- V2-PYTEST-BOOTSTRAP-CONSOLIDATION:END -->

<!-- V2-DATABASE-IMPORT-NORMALIZATION:START -->
## Canonical Imports for Numeric Source Root

Because `02_AI` begins with a digit, direct source syntax such as
`from 02_AI...` is not valid Python syntax.

Where repository code/tests need the canonical `02_AI` module identity,
`importlib.import_module("02_AI.<Domain>.<module>")` is the established
location-independent mechanism.

Do not compensate by adding `02_AI` itself to `sys.path` and importing
`Domain.module`; that creates a second module identity and path-dependent
behavior.
<!-- V2-DATABASE-IMPORT-NORMALIZATION:END -->

<!-- V2-READY-18-RELOCATION:START -->
## Structural Test Relocation Rule

Tests must be made independent of their current filesystem depth before moving.

Post-move reference scans must distinguish the moved file itself from true
external consumers: both its old source path and corresponding new target path
must be excluded when checking external references to the old identity.

Human-readable path metadata may be corrected after relocation, but such a
change must be recorded separately from byte-identical movement and verified
not to alter executable Python semantics.
<!-- V2-READY-18-RELOCATION:END -->
