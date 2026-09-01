# PulseViper XAU AI — Research Evidence Index

## 1. Purpose

This document is the human-readable index for PulseViper XAU AI research evidence.

PulseViper generates machine-readable JSON reports throughout the research process.

A new developer should be able to use this document to answer:

* Which experiment produced the current model?
* Which dataset was used?
* Which feature contract was used?
* Which model candidates were allowed?
* Why was C04 selected?
* Was VALIDATION untouched before evaluation?
* What result did VALIDATION produce?
* Is VALIDATION now consumed?
* Is TEST still untouched?
* Which fingerprints connect the research chain?

This document does not replace JSON evidence.

The JSON artifacts remain the machine-readable scientific record.

---

# 2. How to Think About Evidence

A research result is not just:

```text
macro-F1 = 0.35
```

A complete research result should prove:

```text
which dataset
+
which features
+
which target
+
which model
+
which protocol
+
which code
+
which holdout state
+
which decision rule
```

produced the metric.

---

# 3. Evidence Chain Overview

Current frozen research lineage:

```text
Portable Dataset
      ↓
Portable Feature Contract
      ↓
TRAIN Input / Target Contract
      ↓
TRAIN Research Protocol
      ↓
Frozen Candidate Registry
      ↓
Real Walk-Forward Evaluation
      ↓
Frozen C04 Winner
      ↓
Full TRAIN Fit
      ↓
Model Artifact Verification
      ↓
Frozen VALIDATION Protocol
      ↓
Validation Core
      ↓
Bounded Validation Source
      ↓
Dry Preflight
      ↓
Real One-Time VALIDATION
      ↓
Validation Ledger
      ↓
Validation Result Freeze
      ↓
FINAL TEST
      ⏳
```

---

# 4. Current Core Identity

## Symbol / research scope

```text
XAUUSD / XAUUSDm
```

## Feature count

```text
331
```

## Target classes

```text
[-1, 0, 1]
```

Meaning:

```text
-1 = SHORT
 0 = NO_TRADE
 1 = LONG
```

---

# 5. Dataset Identity

Current frozen portable dataset ID:

```text
portable_cff75b0686383a3ab6f8352b
```

Dataset SHA256:

```text
cff75b0686383a3ab6f8352bfcdcd55308b99b7a4c6edbf7d2e7215f6f33dd07
```

TRAIN rows:

```text
69,966
```

Feature count:

```text
331
```

Manifest SHA256:

```text
1b8e3599b227c9cbbc6b12f8ab0e275ca4deb4a65839fb626ca90720d59512dc
```

---

# 6. Feature Contract Identity

Frozen ordered feature-list SHA256:

```text
65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2
```

This proves the exact ordered feature contract.

Do not manually reconstruct the authoritative feature list from Markdown documentation.

Use the frozen manifest.

---

# 7. TRAIN Input Fingerprints

Current frozen TRAIN input fingerprint:

```text
9ffb72759499cfc202e88cfdbd61b42cee5b5c7cbb7db5870470453caa5ed2c5
```

TRAIN target fingerprint:

```text
bc063a790e70cdbc931b2170ccfef883634b40ee7336a529a32bda0eaf0babe3
```

Supervised batch fingerprint:

```text
1e7bd0751234282d4081ef87783de8633aac815a2f6aa13010fbb5a06156aec4
```

Target access fingerprint:

```text
a640b9cda2522b734515a2cdf05259abbf77e4c6488afd635aedc21f62458266
```

Trainer input fingerprint:

```text
b192ce16291fe9ddca9ead9561224fb942c331d1f30fc1b53cee396efa5accdf
```

These identities link the model research pipeline to the exact supervised TRAIN representation.

---

# 8. Research Protocol Evidence

Parent TRAIN protocol fingerprint:

```text
69e51e1b249b9da68cbf6f6778a8ae10f9f33f7082a07e5073a1ba731fa1640d
```

Protocol principles:

```text
TRAIN only
4 chronological expanding folds
12-row purge
no shuffle
no VALIDATION
no TEST
```

Anti-overfit rules included:

```text
no Bayesian optimization
no grid search
no validation peeking
no test peeking
no threshold search
no results-driven feature selection
no candidate addition after results
```

---

# 9. Candidate Registry Evidence

Primary JSON:

```text
xauusd_portable_331_train_model_candidate_registry_design.json
```

Analysis version:

```text
XAUUSD_PORTABLE_331_TRAIN_MODEL_CANDIDATE_REGISTRY_DESIGN_V1
```

Registry fingerprint:

```text
b8088bb34ce8940f7de5946fbb9b0fd20f40d7cc93a76b76fd7975591f00066c
```

Candidate count:

```text
6
```

Candidates:

```text
C01_FLAT_LOGREG_BALANCED_C005
C02_FLAT_LOGREG_BALANCED_C020
C03_FLAT_HGB_SHALLOW
C04_FLAT_EXTRA_TREES_CONSTRAINED
C05_HIER_LOGREG_REGULARIZED
C06_HIER_HGB_LOGREG_CONSTRAINED
```

---

# 10. Why the Candidate Registry Matters

The registry proves that model choices were fixed before real candidate results were observed.

This prevents:

```text
run candidate
     ↓
see result
     ↓
invent another candidate
     ↓
repeat until something looks good
```

The registry is therefore part of the scientific evidence.

---

# 11. Candidate Evaluation Evidence

Primary JSON:

```text
xauusd_portable_331_train_model_candidate_walk_forward_evaluation.json
```

Evaluation fingerprint:

```text
15516174ba6f3d8932425b20dcde33db25c040e0901c86af39796f97847ac7ed
```

Research design:

```text
6 frozen candidates
×
4 TRAIN-only folds
```

No portable VALIDATION or TEST was used for winner selection.

---

# 12. Current Winner

Winner:

```text
C04_FLAT_EXTRA_TREES_CONSTRAINED
```

C04 TRAIN walk-forward summary:

```text
mean balanced accuracy:
0.35438789335022963

mean directional macro-F1:
0.3105791161393638

worst-fold directional macro-F1:
0.25365034089349603

mean macro-F1:
0.2846765787595467

mean predicted trade coverage:
0.8691757979990471
```

---

# 13. C04 Selection Key

Frozen lexicographic C04 selection key:

```text
[
  0.25365034089349603,
  0.3105791161393638,
  0.34040386328178984,
  0.2846765787595467,
  -0.034141428338313996,
  -1.1183066797532708
]
```

Selection priority was frozen before results.

Primary goal:

```text
maximize worst-fold directional macro-F1
```

---

# 14. Winner Freeze Evidence

Primary JSON:

```text
xauusd_portable_331_train_internal_winner_freeze.json
```

Status:

```text
TRAIN_INTERNAL_WINNER_FROZEN
```

Winner configuration fingerprint:

```text
f1b11c6f91561f2eba1bd56195e2239e9598b1906c88f11ada67eac6cdeb09e3
```

This evidence establishes that C04 was frozen before full TRAIN fitting and before holdout evaluation.

---

# 15. Frozen C04 Configuration

Model:

```text
ExtraTreesClassifier
```

Configuration:

```text
n_estimators = 500
max_depth = 10
max_features = 0.35
min_samples_leaf = 25
bootstrap = false
class_weight = balanced
random_state = 271828
n_jobs = -1
```

---

# 16. Full TRAIN Fit Evidence

Primary JSON:

```text
xauusd_portable_331_c04_full_train_model_fit.json
```

Model artifact:

```text
xauusd_portable_331_c04_full_train_model.joblib
```

Rows used:

```text
69,966
```

Features:

```text
331
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

# 17. Model Artifact Verification Evidence

Primary JSON:

```text
xauusd_portable_331_c04_full_train_model_artifact_verification.json
```

Verification record fingerprint:

```text
a2759a429b90998a7d24c8b217e570813e36dcf43df5de6cf98daf875b8678ef
```

Verified areas include:

```text
model artifact SHA
model family
class order
feature count
hyperparameters
number of trees
TRAIN provenance
```

---

# 18. Frozen Class Order

Model probability class order:

```text
[-1, 0, 1]
```

Meaning:

```text
probability column 0 = SHORT
probability column 1 = NO_TRADE
probability column 2 = LONG
```

This order must be preserved during inference.

---

# 19. VALIDATION Protocol Evidence

Primary JSON:

```text
xauusd_portable_331_one_time_validation_protocol.json
```

Protocol fingerprint:

```text
ce78180a5f2472c36c74cea2c447307641aa3d5fedfb7a01d9b65260b5a6fcea
```

Status:

```text
ONE_TIME_VALIDATION_PROTOCOL_FROZEN
```

This file was created before real VALIDATION results were observed.

---

# 20. VALIDATION Hard Gates

Frozen hard requirements:

```text
directional macro-F1
>= 0.25365034089349603

balanced accuracy
>= 0.34040386328178984

macro-F1
>= 0.24533114425757888

SHORT recall
> 0

LONG recall
> 0

trade coverage
>= 0.05

trade coverage
<= 0.95

all metrics finite

all target classes present
```

Report-only:

```text
log-loss
multiclass Brier
```

---

# 21. Validation Core Evidence

Primary JSON:

```text
xauusd_portable_331_one_time_validation_core_attestation.json
```

Status:

```text
ONE_TIME_VALIDATION_CORE_IMPLEMENTED_NOT_REAL_EXECUTED
```

This evidence proved:

```text
ledger created before read
post-read rerun blocked
pre-read technical recovery supported
metric evaluator reused
no real VALIDATION loaded during implementation gate
no TEST path
```

---

# 22. Authorized Validation Source Evidence

Primary JSON:

```text
xauusd_portable_331_authorized_validation_source_attestation.json
```

Analysis version:

```text
XAUUSD_PORTABLE_331_AUTHORIZED_VALIDATION_SOURCE_IMPLEMENTATION_V1
```

Status:

```text
AUTHORIZED_VALIDATION_SOURCE_IMPLEMENTED_NOT_REAL_EXECUTED
```

Loader source SHA256:

```text
49c86c269f2742fec7c6991eaf7a8a9c0466066a3db230a80375ba2e2c33680c
```

This evidence proved that the source:

```text
reads structural split information
locates contiguous VALIDATION
reads only the VALIDATION value block
stops before TEST values
preserves frozen feature order
does not modify public holdout accessors
```

---

# 23. Validation Dry Preflight Evidence

Primary JSON:

```text
xauusd_portable_331_one_time_validation_preflight.json
```

Preflight fingerprint:

```text
5ee6d0948d93f83f7969662e103066f1a09d7b081883290aba104b52f0038f41
```

State before real VALIDATION:

```text
ledger_state = ABSENT
validation_read_attempt_count_before_execution = 0
holdout_consumed_before_execution = false
```

The preflight linked:

```text
model artifact
validation protocol
loader source
feature contract
validation source
ledger policy
```

before the real holdout was touched.

---

# 24. Validation Access Ledger

Primary JSON:

```text
xauusd_portable_331_one_time_validation_access_ledger.json
```

This is persistent evidence of the one-time holdout read.

Final expected/current state includes:

```text
validation_read_attempt_count = 1
holdout_consumed_for_rerun_policy = true
validation_values_loaded = true
validation_metrics_computed = true
validation_accepted = true
test_values_accessed = false
test_access_authorized_next = true
```

Status:

```text
VALIDATION_COMPLETE_ACCEPTED
```

---

# 25. Real VALIDATION Result Evidence

Primary JSON:

```text
xauusd_portable_331_one_time_validation_result.json
```

Result fingerprint:

```text
ea8b482e60f854f58e27f3be387b7bb82f0c16a6cf1a99555b12643aeeca5fa1
```

Decision:

```text
ONE_TIME_VALIDATION_ACCEPTED
```

---

# 26. VALIDATION Metrics

Current one-time VALIDATION result:

| Metric                          |               Value |
| ------------------------------- | ------------------: |
| balanced_accuracy_3class        | 0.37656763760203776 |
| macro_f1_3class                 | 0.34890395261998247 |
| directional_macro_f1_short_long | 0.33640257616029445 |
| short_precision                 |  0.3293731041456016 |
| short_recall                    |  0.3190499510284035 |
| short_f1                        | 0.32412935323383085 |
| no_trade_precision              |  0.5570032573289903 |
| no_trade_recall                 |  0.2814042786615469 |
| no_trade_f1                     |  0.3739067055393586 |
| long_precision                  | 0.25997548685823235 |
| long_recall                     |   0.529248683116163 |
| long_f1                         |   0.348675799086758 |
| log_loss_3class                 |  1.0979186095143678 |
| multiclass_brier                |  0.6664287278633827 |
| predicted_trade_coverage        |  0.7541213375158513 |

All frozen hard checks passed.

---

# 27. Validation Result Freeze Evidence

Primary JSON:

```text
xauusd_portable_331_one_time_validation_result_freeze.json
```

Freeze fingerprint:

```text
521a97b41a86231b049cc65aebfd85ffc7c83ae7141134d6ae1158d112b1468c
```

Status:

```text
ONE_TIME_VALIDATION_RESULT_FROZEN_ACCEPTED
```

Current authorization:

```text
validation_result_frozen = true
validation_consumed = true
validation_rerun_authorized = false

test_runner_implementation_authorized_next = true
test_execution_authorized = false

shadow_authorized = false
live_authorized = false
```

---

# 28. VALIDATION Evidence Chain

The complete current VALIDATION provenance can be read as:

```text
Frozen C04 Model
SHA:
48a1d70d...
       ↓
Frozen Validation Protocol
SHA:
ce78180a...
       ↓
Authorized Validation Source
loader SHA:
49c86c26...
       ↓
Dry Preflight
SHA:
5ee6d094...
       ↓
One-Time Access Ledger
read_attempt = 1
       ↓
Validation Result
SHA:
ea8b482e...
       ↓
Validation Freeze
SHA:
521a97b4...
```

This is one of the most important scientific chains in the repository.

---

# 29. Current TEST Evidence State

Current TEST status:

```text
untouched
```

No final TEST result should exist yet for the current frozen portable C04 lineage.

The next expected evidence sequence is:

```text
TEST protocol
      ↓
TEST source attestation
      ↓
TEST dry preflight
      ↓
TEST access ledger
      ↓
TEST result
      ↓
TEST result freeze
      ↓
final research verdict
```

Do not create a TEST result manually.

It must come from the one-shot protected TEST runner.

---

# 30. Final Research Verdict Evidence

After TEST, the project should create a final historical research report connecting:

```text
TRAIN walk-forward
+
VALIDATION
+
TEST
```

The report should evaluate:

```text
directional robustness
balanced accuracy stability
macro-F1 stability
SHORT recall
LONG recall
coverage stability
probability quality
generalization gaps
limitations
```

The verdict may authorize:

```text
shadow research
```

but must not automatically authorize live trading.

---

# 31. Auxiliary Research Reports

The repository also contains research/design/integration artifacts from earlier gates.

Examples include reports associated with:

```text
portable feature projection
target access
TRAIN supervised batch
TRAIN integration
candidate evaluator integration
research protocol design
```

These remain useful provenance.

This index prioritizes the **critical frozen C04 → VALIDATION lineage**.

When new auxiliary reports are added, document:

```text
filename
creating script
purpose
important fingerprint
decision
parent evidence
```

rather than merely listing filenames.

---

# 32. How to Inspect Evidence

Example:

```powershell
Get-Content xauusd_portable_331_one_time_validation_result.json
```

For machine processing, prefer Python.

Example:

```powershell
python -c "import json; from pathlib import Path; p=Path('xauusd_portable_331_one_time_validation_result.json'); d=json.loads(p.read_text(encoding='utf-8')); print(d['decision'])"
```

---

# 33. How to Trace Evidence to Git

To see commits affecting a specific artifact:

```powershell
git log --oneline -- xauusd_portable_331_one_time_validation_result.json
```

To inspect a specific commit:

```powershell
git show d70d5e0
```

Current confirmed local validation-freeze commit:

```text
d70d5e0
Freeze XAUUSD one time validation result
```

Current confirmed local validation-preflight commit:

```text
0650446
Freeze XAUUSD one time validation preflight
```

---

# 34. Evidence File Rule

Do not casually edit a frozen evidence JSON by hand.

If an evidence file is wrong:

```text
identify whether it is:
technical formatting error
or
scientific result change
```

A formatting repair may sometimes preserve semantics.

Changing values in a frozen research result does not.

---

# 35. Evidence Encoding Rule

All machine-readable evidence should preferably be:

```text
UTF-8 without BOM
```

Historical development encountered:

```text
UTF-16 PowerShell output
UTF-8 BOM
```

which caused strict JSON-loading failures.

---

# 36. Evidence Fingerprint Rule

If a report contains a canonical fingerprint:

```text
change report content
       ↓
fingerprint should change
```

If content changes while fingerprint remains unchanged:

```text
evidence is inconsistent
```

---

# 37. Evidence Tampering

Examples of invalid operations:

```text
manually changing validation metrics
changing accepted=false to true
changing model SHA
changing feature SHA
resetting ledger read_attempt_count
```

These destroy provenance.

The correct response to an unfavorable scientific result is not to edit its evidence.

---

# 38. Evidence vs Logs

Not every terminal log is frozen scientific evidence.

Distinguish:

## Operational log

```text
script started
loading model
finished in 3 seconds
```

## Scientific evidence

```text
dataset identity
feature identity
model identity
metric result
decision
fingerprint
```

Scientific evidence belongs in structured artifacts.

---

# 39. Evidence vs Documentation

Markdown explains:

```text
what happened
why it happened
how to understand it
```

JSON proves:

```text
exact machine-readable state
```

Both are useful.

Neither should silently contradict the other.

---

# 40. Student Evidence Exercise

A new student should be able to trace:

```text
Why is C04 the current model?
```

using:

```text
Candidate Registry
      ↓
Walk-Forward Evaluation
      ↓
Winner Freeze
      ↓
Full TRAIN Fit
      ↓
Artifact Verification
```

Then answer:

```text
Did VALIDATION choose C04?
```

Correct answer:

```text
No.
```

C04 was frozen using TRAIN-only research.

VALIDATION only evaluated the already-frozen C04.

---

# 41. Student Evidence Exercise — Why Can't VALIDATION Be Rerun?

Trace:

```text
Validation Preflight
      ↓
Validation Ledger
      ↓
Validation Result
      ↓
Validation Freeze
```

The ledger records:

```text
one read attempt
holdout consumed
```

The freeze records:

```text
validation_rerun_authorized = false
```

Therefore rerunning it for tuning would violate the protocol.

---

# 42. Student Evidence Exercise — Is TEST Available?

Look at current validation freeze decision:

```text
test_runner_implementation_authorized_next = true
test_execution_authorized = false
```

Meaning:

```text
developers may build and test TEST infrastructure
```

but:

```text
developers may not yet consume real TEST values
```

---

# 43. Research Evidence Review Checklist

Before accepting a research result:

```text
[ ] valid == true
[ ] analysis_version understood
[ ] dataset identity matches
[ ] feature identity matches
[ ] model identity matches
[ ] parent fingerprints match
[ ] protected-data state understood
[ ] metrics finite
[ ] decision understood
[ ] scientific_policy checked
[ ] result fingerprint recorded
```

---

# 44. Before Committing New Evidence

Review:

```powershell
git status --short
```

Check:

```text
correct JSON file
correct implementation
correct tests
no temporary output
no secrets
no unrelated binary files
```

---

# 45. Binary Model Artifact Policy

The current frozen model is:

```text
xauusd_portable_331_c04_full_train_model.joblib
```

Whether binary artifacts are committed to Git should follow repository storage policy.

Even if the binary is not stored remotely, its SHA256 and provenance must remain recorded in research evidence.

Do not add large binaries automatically without checking repository policy.

---

# 46. Current Research Evidence Status

```text
Portable dataset identity              ✅
Feature identity                       ✅
TRAIN supervised identity              ✅
Research protocol                      ✅
Candidate registry                     ✅
Real walk-forward evaluation           ✅
Winner freeze                          ✅
Full TRAIN fit                         ✅
Model artifact verification            ✅
VALIDATION protocol                    ✅
Validation core                        ✅
Bounded validation source              ✅
Validation dry preflight               ✅
Real VALIDATION result                 ✅ PASS
Validation access ledger               ✅
Validation result freeze               ✅

Final TEST protocol                     ⬜
Final TEST preflight                    ⬜
Final TEST result                       ⬜
Final TEST freeze                       ⬜
Final historical research verdict       ⬜
Shadow evidence                         ⬜
Forward validation evidence             ⬜
Live promotion evidence                 ⛔
```

---

# 47. Current Critical Fingerprint Summary

## Dataset SHA256

```text
cff75b0686383a3ab6f8352bfcdcd55308b99b7a4c6edbf7d2e7215f6f33dd07
```

## Manifest SHA256

```text
1b8e3599b227c9cbbc6b12f8ab0e275ca4deb4a65839fb626ca90720d59512dc
```

## Feature Columns SHA256

```text
65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2
```

## Candidate Registry Fingerprint

```text
b8088bb34ce8940f7de5946fbb9b0fd20f40d7cc93a76b76fd7975591f00066c
```

## Walk-Forward Result Fingerprint

```text
15516174ba6f3d8932425b20dcde33db25c040e0901c86af39796f97847ac7ed
```

## Winner Configuration Fingerprint

```text
f1b11c6f91561f2eba1bd56195e2239e9598b1906c88f11ada67eac6cdeb09e3
```

## Model Artifact SHA256

```text
48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769
```

## Model Record Fingerprint

```text
bd6d76f92d3c6274bed756683f4263b9cce9a3f0e5ffbb8bd4ba3fcbe6f6ff74
```

## Model Verification Fingerprint

```text
a2759a429b90998a7d24c8b217e570813e36dcf43df5de6cf98daf875b8678ef
```

## VALIDATION Protocol Fingerprint

```text
ce78180a5f2472c36c74cea2c447307641aa3d5fedfb7a01d9b65260b5a6fcea
```

## VALIDATION Preflight Fingerprint

```text
5ee6d0948d93f83f7969662e103066f1a09d7b081883290aba104b52f0038f41
```

## VALIDATION Result Fingerprint

```text
ea8b482e60f854f58e27f3be387b7bb82f0c16a6cf1a99555b12643aeeca5fa1
```

## VALIDATION Freeze Fingerprint

```text
521a97b41a86231b049cc65aebfd85ffc7c83ae7141134d6ae1158d112b1468c
```

---

# 48. Current Research Decision Summary

```text
Winner:
C04_FLAT_EXTRA_TREES_CONSTRAINED

Full TRAIN fit:
COMPLETE

Model artifact:
VERIFIED

VALIDATION:
PASSED

VALIDATION consumed:
YES

VALIDATION rerun:
NO

TEST:
UNTOUCHED

TEST infrastructure:
AUTHORIZED NEXT

TEST real execution:
NOT YET AUTHORIZED

Shadow:
NOT AUTHORIZED

Live:
NOT AUTHORIZED
```

---

# 49. How Future Evidence Should Be Added

For every major new gate, add an entry containing:

```text
Name
Purpose
Creating Python script
Focused test
JSON artifact
Analysis version
Critical input fingerprints
Result fingerprint
Decision
Authorization created by the gate
Git commit
```

This keeps the repository understandable even years later.

---

# 50. Golden Evidence Rule

The most important evidence principle is:

> Never separate a metric from the identity and protocol that produced it.

A number without provenance is not enough.

A scientifically useful PulseViper result should always be traceable back to:

```text
data
features
target
protocol
model
code
holdout state
decision
```
