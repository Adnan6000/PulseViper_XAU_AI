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
Historical C04 forward baseline
      ↓
G7 remediation cycle
      ↓
G7-G-B sealed TEST confirmation
      ↓
G7-H R03 prospective validation lane
      ⏳ CURRENT

---

## Current Forward Evidence Status

Latest engineering/protocol HEAD before this documentation synchronization: `c5ec7069a4dff846d663bee05c862f38f9e8b891`.

The historical C04 forward baseline is complete as a failed/weak discrimination signal and is excluded from remediation tuning.

The current R03 lane has frozen:
- prospective validation contract;
- train-only model artifact;
- runtime binding;
- outcome maturation;
- finite collection controller;
- first-capture runner and R1/R2 recovery runners.

Current R03 evidence state:

- observations: **0**
- anchors: **0**
- matured outcomes: **0**
- minimum matured outcomes: **60**
- minimum distinct UTC observation dates: **5**
- formal performance evaluation: `false`
- formal PnL evaluation: `false`
- live authorization: `false`
- execution authorization: `false`

The first genuine R03 capture is currently blocked by `TIMESTAMP_BASIS_NOT_UNIQUELY_PROVEN` for `raw_tick=1790985539` with `candidate_count=0`. The block is preserved as evidence and the timestamp proof must not be weakened.

# 4. Current Core Identity

## Historical control

```text
C04_FLAT_EXTRA_TREES_CONSTRAINED
```

C04 remains the historical control lineage that motivated remediation.

## Current remediation winner

```text
R03_FLAT_EXTRA_TREES_SMOOTH
```

## Feature count

```text
331
```

## Target classes

```text
[-1, 0, 1]
```

## Current R03 prospective authority

```text
minimum matured outcomes = 60
minimum distinct UTC observation dates = 5
horizon = 12 completed M5 rows
profit_atr = 1.25
max_adverse_atr = 0.75
```

Current R03 runtime collection remains read-only and non-trading.

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
04_Testing/evidence/research/portable_331/train/xauusd_portable_331_train_internal_winner_freeze.json
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
04_Testing/evidence/research/portable_331/train/xauusd_portable_331_c04_full_train_model_fit.json
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

---

# 51. Gate 13 — Production Feature Provenance & Parity Evidence

Gate 13 proves parity of the production feature pipeline using canonical broker-derived historical execution snapshots against non-holdout frozen TRAIN rows, producing the exact frozen 331-feature model input contract with zero mismatches. Live MT5 feed ingestion and live runtime parity are outside this scope and have not yet been proven by Gate 13.

### Provenance Map Artifact
- **File**: `04_Testing/evidence/production_portability/xauusd_portable_331_feature_provenance_map.json`
- **SHA256**: `bee22e57982aeddc4c2a673ee54c1720ea264b844329976138d4ebf94f05e7b4`
- **Total Features**: 331
- **Feature Columns SHA256**: `65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2`
- **Family Distribution**:
  - `technical_mtf`: 258 features (43 indicators x 6 timeframes)
  - `retained_volume`: 1 feature (`m5_tick_volume_ratio20`)
  - `domain_structure`: 18 features (3 indicators x 6 timeframes)
  - `domain_liquidity`: 6 features (1 indicator x 6 timeframes)
  - `domain_patterns`: 12 features (2 indicators x 6 timeframes)
  - `domain_zones`: 15 features (3 indicators x 5 timeframes: M15..D1)
  - `domain_regimes`: 12 features (2 indicators x 6 timeframes)
  - `age_features`: 5 features (M15..D1 bar age in M5 bars)
  - `cyclical_time`: 4 features (`sin_hour_utc`, `cos_hour_utc`, `sin_dow_utc`, `cos_dow_utc`)
- **Family Numerical Tolerances**:
  - `EXACT_DISCRETE`: `rtol=0.0, atol=0.0`
  - `INTEGER_COUNT`: `rtol=0.0, atol=0.0`
  - `FLOAT32_TRIGONOMETRIC`: `rtol=1e-5, atol=1e-6`
  - `FLOAT32_NUMERIC`: `rtol=1e-4, atol=1e-5`

### Production Parity Evidence Artifact
- **File**: `04_Testing/evidence/production_portability/xauusd_portable_331_production_parity_evidence.json`
- **Verdict**: **PASS**
- **Evaluation Set**: 481 non-holdout TRAIN rows evaluated against `Portable331TrainingInputLoader`
- **Total Compared Features**: 331
- **Mismatches**: 0 across all 331 features
- **Maximum Observed Differences**:
  - `FLOAT32_NUMERIC`: `5.00e-07`
  - `FLOAT32_TRIGONOMETRIC`: `4.79e-11`
  - `EXACT_DISCRETE`: `0.0`
  - `INTEGER_COUNT`: `0.0`
- **Frozen Model Compatibility**:
  - Model Artifact: `xauusd_portable_331_c04_full_train_model.joblib`
  - Model SHA256: `48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769`
  - `n_features_in_`: 331
  - `classes_`: `[-1, 0, 1]`

---

# 52. Gate 14 — Frozen C04 Offline Inference Adapter Evidence

Gate 14 proves that the production-quality offline inference adapter (`FrozenC04InferenceAdapter`) faithfully wraps the frozen C04 ExtraTrees model, strictly validates the exact Gate 13 331-feature contract, and produces deterministic probabilities and class decisions matching direct model invocation with zero mismatches.

### Inference Adapter Evidence Artifact
- **File**: `04_Testing/evidence/production_portability/xauusd_frozen_c04_inference_adapter_evidence.json`
- **Verdict**: **PASS**
- **Input Source Classification**: `NON_HOLDOUT_TRAIN_OR_GATE13_ENGINEERING_INPUT`
- **Model Authority**:
  - Model Path: `xauusd_portable_331_c04_full_train_model.joblib`
  - Model SHA256: `48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769`
  - Model Class: `ExtraTreesClassifier`
  - `n_features_in_`: `331`
  - `classes_`: `[-1, 0, 1]` (`-1 = SHORT`, `0 = NO_TRADE`, `1 = LONG`)
- **Parity Evaluation**:
  - Evaluated Rows: 500 non-holdout TRAIN engineering rows
  - Direct Model Max Probability Difference: `3.33e-16` (machine precision / floating-point summation order)
  - Probability Mismatch Count: **0**
  - Class Prediction Mismatch Count: **0**
- **Decision Rule Contract**:
  - Argmax Decision: `classes_[np.argmax(probabilities, axis=1)]`
  - Decision Logic: Strictly frozen argmax without thresholding, calibration, or bias
  - First-index tie behavior verified: index 0 (-1 / SHORT) on equal probabilities
- **Safety Flags**:
  - `live_authorized = False`
  - `shadow_authorized = False`
  - Zero trading runtime dependencies imported or called

---

# 53. Gate 15A — Forward Shadow Observation Infrastructure Evidence

Gate 15A establishes the production-safe forward shadow observation infrastructure required for future forward shadow validation:
- Validated Gate 13 features -> Gate 14 inference adapter -> typed immutable `FrozenC04ObservationRecord` -> locked durable append ledger with fail-closed corruption detection.
- Proves machine-readable frozen research boundary (`2026-08-14T20:55:00Z`) from `source_historical_snapshots.M5.end_time`.
- Persists activation authority (`2026-09-06T13:20:00Z`).
- Strictly marks outcome horizon contract `BLOCKED_NOT_PREDEFINED`.
- Enforces provenance-based forward eligibility with fail-closed rejection of unauthorized `TRUE_FORWARD_OBSERVATION` attempts.
- Performs zero model retraining, accesses zero holdout data, and imports zero trading runtime logic.

### Forward Shadow Infrastructure Evidence Artifact
- **File**: `04_Testing/evidence/forward_shadow/xauusd_frozen_c04_shadow_observation_infrastructure_evidence.json`
- **Verdict**: **PASS**
- **Observer Schema Version**: `1.0.0`
- **Model Authority**:
  - Model Path: `xauusd_portable_331_c04_full_train_model.joblib`
  - Model SHA256: `48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769`
  - Model Class: `ExtraTreesClassifier`
  - `classes_`: `[-1, 0, 1]`
- **Feature Contract**:
  - `expected_feature_count`: `331`
  - `feature_columns_sha256`: `65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2`
- **Research Freeze Boundary**:
  - Authority Source: `01_Data/Canonical/Instruments/XAUUSD/learning/scope_c8705b79f4cb595c4a2dec477d76a64956ae63133a2f91426f1647a3c5f5cfef/training/XAUUSD_MTF_TRAINING_V3/portable_v1/pv_portable_xauusd_cff75b0686383a3ab6f8352b.manifest.json`
  - Authority Key: `source_historical_snapshots.M5.end_time`
  - Maximum Historical Timestamp: `2026-08-14T20:55:00Z`
  - Boundary verified without holdout access: `True`
- **Activation Authority**:
  - `gate_15a_activation_utc`: `2026-09-06T13:20:00Z` (persisted frozen authority)
- **Outcome Horizon Contract**:
  - Status: `BLOCKED_NOT_PREDEFINED`
  - `forward_performance_evaluated`: **False**
- **Provenance Evaluation**:
  - Historical Engineering Rows Tested: 100
  - Synthetic Engineering Rows Tested: 1
  - True Forward Observation Count: **0**
  - True Forward Live Acquisition Authorized: **False**
  - True Forward Attempt Rejected Fail-Closed: `True`
  - Outcome Evaluation Attempt Rejected Fail-Closed: `True`
- **Static Safety Verification**:
  - Reachable dependency graph: 0 violations, 0 forbidden symbols
- **Storage Contract**:
  - Mechanism: Locked durable append with fail-closed corruption detection
  - Format: JSON Lines (`.jsonl`)
  - Operational Runtime Path: `01_Data/Shadow/xauusd_frozen_c04_shadow_observations.jsonl` (git-ignored)
- **Safety Invariants**:
  - `live_authorized = False`
  - `execution_authorized = False`
  - `forward_performance_evaluated = False`
  - `holdouts_unaccessed = True`
  - `models_unmodified = True`
  - `risk_engine_unmodified = True`

---

# 54. Gate 15B-A — Read-Only Forward Acquisition Authority Evidence

Gate 15B-A establishes the production-safe, provably isolated, read-only MetaTrader 5 forward market data acquisition authority:
- Wraps MT5 sessions in `MT5ReadOnlyCapabilityFacade`, exposing strictly whitelisted read-only methods (`symbols_get`, `symbol_info`, `symbol_info_tick`, `copy_rates_from_pos`).
- Raises `PermissionError` on any attempt to invoke mutating broker/order methods (`order_send`, `positions_get`, etc.).
- Strictly enforces `start_pos >= 1` in rate requests to exclude forming/incomplete candles.
- Normalizes integer Unix timestamps to UTC (`pd.to_datetime(..., unit='s', utc=True)`).
- Acquires complete multi-timeframe OHLCV bars (`M5`, `M15`, `M30`, `H1`, `H4`, `D1`) required by Gate 13 `PortableFeaturePipeline`.
- Computes deterministic lowercase 64-hex SHA256 snapshot fingerprint (`source_snapshot_id`).
- Produces tamper-evident `ForwardAcquisitionAttestation` and `ForwardMarketSnapshot`.
- Strictly marks synthetic/mock data to prevent unauthorized true-forward escalation.
- Enforces frozen research boundary (`2026-08-14T20:55:00Z`) and Gate 15A activation authority (`2026-09-06T13:20:00Z`).
- Zero dependencies on `RiskEngine`, `trade_ready`, or execution order routing.

### Read-Only Forward Acquisition Evidence Artifact
- **File**: `04_Testing/evidence/forward_shadow/xauusd_gate_15b_a_read_only_forward_acquisition_evidence.json`
- **Verdict**: **PASS**
- **Acquisition Schema Version**: `1.0.0`
- **Architecture**: `OPTION_B_HYBRID_READ_ONLY_ACQUISITION_FACADE`
- **Capability Manifest**: `["copy_rates_from_pos", "symbol_info", "symbol_info_tick", "symbols_get"]`
- **Forbidden Mutating Methods Blocked**: 10
- **Forming Candle Access (start_pos < 1) Blocked**: `True`
- **Attestation Integrity Verified**: `True`
- **Gate 13 Pipeline Handoff**: `PASS` (331 features, SHA256 matches frozen authority)
- **Gate 14 Inference Handoff**: `PASS` (predicts deterministic class & probabilities)
- **Gate 15A Observer Handoff**: `PASS` (records typed observation, escalation prevented)
- **Observation Counts**:
  - `synthetic_true_forward_count`: **0**
  - `historical_true_forward_count`: **0**
  - `genuine_true_forward_observation_count`: **0**
  - `genuine_forward_acquisition_status`: **NOT_OBSERVED**
- **Static Safety Audit**: 0 violations, 0 forbidden symbols
- **Frozen Baseline Integrity**: 41/41 files byte-identical (**PASS**)
- **Safety Invariants**:
  - `live_authorized = False`
  - `execution_authorized = False`
  - `forward_performance_evaluated = False`

---

# 55. Gate 15B-B — First Genuine Read-Only Forward Observation Evidence

Gate 15B-B records the first genuine connected read-only forward market observation from real MetaTrader 5:
- Uses `MT5ReadOnlyForwardAcquisitionAdapter:2.1.0` under the approved read-only facade.
- Successfully discovered canonical broker symbol `XAUUSD`.
- Verified multi-timeframe completed bars (`M5`, `M15`, `M30`, `H1`, `H4`, `D1`) with `start_pos >= 1` (zero forming bars used).
- Reconstructed D1 from H1 bars with per-row DST normalization.
- Handed off 331 validated features to Gate 14 frozen inference (`C04_FLAT_EXTRA_TREES_CONSTRAINED`).
- Appended typed `TRUE_FORWARD_OBSERVATION` into `01_Data/Shadow/xauusd_frozen_c04_shadow_observations.jsonl`.
- Zero mutating broker write calls, zero execution dependencies.

### Genuine Forward Observation Evidence Artifacts
- **Primary Evidence**: `04_Testing/evidence/forward_shadow/xauusd_gate_15b_b_first_genuine_forward_observation_evidence.json`
- **Blocked Preflight Audit**: `04_Testing/evidence/forward_shadow/xauusd_gate_15b_b_first_genuine_forward_observation_blocked.json`
- **Verdict**: **PASS**
- **Observation Details**:
  - Observation Decision Time UTC: `2026-09-28T10:15:00Z`
  - Logical Observation ID: `42a457bffe6c6c14edfb4e7b4c6cf656ed27e10579e84f14e771853f5732ba4f`
  - Semantic Record Fingerprint: `cae166c3ab21e35fa57dfa0b652ee918072061329ee44243a7da8e7c10b27b3b`
  - Source Provenance: `TRUE_FORWARD_OBSERVATION`
  - Canonical Instrument: `XAUUSD`
  - Gate 13 Features: 331 columns, SHA256 verified
  - Gate 14 Inference: `PASS`
  - Formal Scoring Status: Pre-contract observation (captured prior to Gate 15C activation `2026-09-28T11:16:59Z`). Retained for audit; strictly excluded from formal forward performance.

---

# 56. Gate 15C — Frozen C04 Forward Outcome Contract Evidence

Gate 15C freezes the forward outcome definition for the frozen C04 model target:
- Declarative contract: `FROZEN_C04_FORWARD_OUTCOME_CONTRACT_V1`.
- Target: `CLEAN_DIRECTIONAL_EXCURSION_V2`.
- Thresholds: 1.25 ATR profit, 0.75 ATR maximum adverse excursion.
- Horizon: 12 completed future M5 rows (row-based, not wall-clock).
- Classes: SHORT = -1, NO_TRADE = 0, LONG = 1.
- Directional excursion rules (not barrier-first logic).
- Zero market data access, zero outcome calculation, zero performance evaluation, zero trading.

### Outcome Contract Evidence Artifact
- **File**: `04_Testing/evidence/forward_shadow/xauusd_gate_15c_forward_outcome_contract_evidence.json`
- **Verdict**: **PASS**
- **Contract Fingerprint SHA256**: `01fe52a2f068fcc8fb2fc5b89dd7e19dc974fc2d967cfb791e75c3415804ce87`
- **Candidate Artifact SHA256 (`02_AI/Models/frozen_c04_forward_outcome_contract.py`)**: `c07de67d9dee591195dc9e4cf5bb3e4d20791f691f8eadfcc6046351d494730a`
- **Safety Invariants**:
  - `live_authorized = False`
  - `execution_authorized = False`
  - `forward_performance_evaluated = False`
  - `forward_outcomes_matured = False`

---

# 57. Gate 15D-A — Prospective Forward Outcome Eligibility Authority Evidence

Gate 15D-A establishes the prospective eligibility boundary for forward outcome evaluation:
- Activation Cutoff UTC: `2026-09-28T11:16:59Z`.
- Policy: Observations recorded prior to or at activation are classified `PRE_CONTRACT_AUDIT_ONLY`; permanently retained for pipeline audit but strictly excluded from formal forward performance.
- Prospective Rule: Only observations with `decision_time > 2026-09-28T11:16:59Z` are prospectively eligible.
- Verified existing observation (Decision time `2026-09-28T10:15:00Z`) correctly excluded from formal scoring.
- Zero mutations to observation ledger; zero MT5 access; zero trading dependencies.

### Outcome Eligibility Evidence Artifact
- **File**: `04_Testing/evidence/forward_shadow/xauusd_gate_15d_a_forward_outcome_eligibility_evidence.json`
- **Verdict**: **PASS**
- **Eligibility Version**: `FROZEN_C04_FORWARD_OUTCOME_ELIGIBILITY_V1`
- **Candidate Artifact SHA256 (`02_AI/Models/frozen_c04_forward_outcome_eligibility.py`)**: `d56fd43cc31577cf5aa454f6eec35ba64387d248c410bfabe5ced6a30582b82e`
- **Pre-Contract Excluded Count**: 1 (`10:15:00Z`)
- **Formal Maturation Eligible Count**: 0
- **Safety Invariants**:
  - `live_authorized = False`
  - `execution_authorized = False`
  - `forward_performance_evaluated = False`

---

# 58. Gate 15D-B — Prospective Post-Contract Genuine Forward Observation Evidence

Gate 15D-B acquires the first genuine prospective post-contract forward observation:
- Uses `MT5ReadOnlyForwardAcquisitionAdapter:2.1.0` under approved read-only facade.
- Verified candidate decision time `2026-09-28T11:45:00Z` > Gate 15C activation (`2026-09-28T11:16:59Z`) -> passed Gate 15D-A prospective eligibility.
- Generated 331 features matching frozen Gate 13 hash; ran Gate 14 inference; durably appended observation record.
- **Formal Scoring Status**: Valid as genuine acquisition proof, but **EXCLUDED FROM FORMAL SCORING** because it did NOT receive a prospective frozen outcome anchor at acquisition time. Status: `POST_CONTRACT_ACQUISITION_PROOF_EXCLUDED_FROM_FORMAL_SCORING_MISSING_PROSPECTIVE_ANCHOR`. No anchor will ever be retroactively manufactured for it.

### Post-Contract Observation Evidence Artifact
- **File**: `04_Testing/evidence/forward_shadow/xauusd_gate_15d_b_post_contract_genuine_observation_evidence.json`
- **Verdict**: **PASS** (as acquisition proof)
- **Observation Decision Time UTC**: `2026-09-28T11:45:00Z`
- **Logical Observation ID**: `553e19273c50970ad37766635c0c995d33a6b685161f38e6ce73bbd8d8f99310`
- **Semantic Record Fingerprint**: `e83e9112ae7c2fc930491fb1737be70d89069d102e3b2e5601a7d6560416ee4f`
- **Broker Write Calls**: 0
- **Execution Dependencies**: 0
- **Safety Invariants**:
  - `live_authorized = False`
  - `execution_authorized = False`
  - `forward_performance_evaluated = False`

---

# 59. Gate 15D-C-A v1 / v1.1 — Forward Outcome Maturation Evidence & Semantic Correction (Historical / Superseded)

Gate 15D-C-A v1 and v1.1 established offline outcome maturation logic:
- V1 introduced offline maturation against completed M5 frames.
- V1.1 corrected decision-bar timing semantics: established that raw M5 `time` is bar open, hence `decision_bar_open = decision_time - 5 minutes`.
- **SUPERSEDED STATUS**: V1.1 is now superseded by `FROZEN_C04_FORWARD_OUTCOME_MATURER_V2` because V1.1 retrospectively reconstructed decision close and ATR14 from later completed data. For formal genuine forward maturation, reference values must be prospectively anchored.

### Maturation Historical Evidence Artifacts
- `04_Testing/evidence/forward_shadow/xauusd_gate_15d_c_a_forward_outcome_maturation_evidence.json` [Superseded]
- `04_Testing/evidence/forward_shadow/xauusd_gate_15d_c_a_v1_1_maturation_semantic_correction_evidence.json` [Superseded]

---

# 60. Gate 15D-C-B1 v1 / v1.1 — Forward Outcome Ledger Evidence & Semantic Alignment (Historical / Superseded)

Gate 15D-C-B1 v1 and v1.1 established outcome ledger storage:
- Aligned schema with corrected decision-bar timing semantics.
- **SUPERSEDED STATUS**: Superseded by `FROZEN_C04_FORWARD_OUTCOME_LEDGER_V2` which requires linked prospective anchors.

### Outcome Ledger Historical Evidence Artifacts
- `04_Testing/evidence/forward_shadow/xauusd_gate_15d_c_b1_outcome_ledger_evidence.json` [Superseded]
- `04_Testing/evidence/forward_shadow/xauusd_gate_15d_c_b1_v1_1_outcome_ledger_semantic_alignment_evidence.json` [Superseded]

---

# 61. Gate 15D-C-B2A — Prospective Forward Outcome Anchor Authority Evidence

Gate 15D-C-B2A establishes the prospective forward outcome anchor authority:
- Prospectively freezes decision entry close and ATR14 from the **SAME acquisition snapshot** before future outcome exposure.
- Enforces `FORMAL_MATURATION_REQUIRES_ANCHOR = true`.
- Capture policy: `SAME_ACQUISITION_SNAPSHOT_NO_FUTURE_M5_ROWS`.
- Implements locked, durable, append-only anchor ledger (`01_Data/Shadow/xauusd_frozen_c04_forward_outcome_anchors.jsonl`).
- Idempotent duplicates supported; conflicting anchors fail closed; ledger corruption fails closed.
- Zero genuine anchors were appended during the offline freeze.

### Prospective Anchor Evidence Artifact
- **File**: `04_Testing/evidence/forward_shadow/xauusd_gate_15d_c_b2a_forward_outcome_anchor_evidence.json`
- **Verdict**: **PASS**
- **Anchor Version**: `FROZEN_C04_FORWARD_OUTCOME_ANCHOR_V1`
- **Anchor Ledger Version**: `FROZEN_C04_FORWARD_OUTCOME_ANCHOR_LEDGER_V1`
- **Candidate Artifact SHA256 (`02_AI/Models/frozen_c04_forward_outcome_anchor.py`)**: `03687f2921962846801c7e3414b51c040626a647474218802619938f814187ea`
- **Genuine Anchors Appended**: 0 (offline freeze)
- **Safety Invariants**:
  - `live_authorized = False`
  - `execution_authorized = False`
  - `forward_performance_evaluated = False`

---

# 62. Gate 15D-C-B2B/B2C — Anchor-Required Maturation V2 + Outcome Ledger V2 Evidence

Gate 15D-C-B2B/B2C establishes the active formal maturation and outcome ledger authorities:
- **Maturer V2**: `FROZEN_C04_FORWARD_OUTCOME_MATURER_V2` (supersedes V1.1). Requires validated prospective anchor; strictly forbids post-hoc reconstruction of entry close and ATR14 (`POST_HOC_ENTRY_AND_ATR_RECONSTRUCTION_FORBIDDEN`).
- **Outcome Ledger V2**: `FROZEN_C04_FORWARD_OUTCOME_LEDGER_V2` (supersedes V1.1). Accepts only outcomes produced by Maturer V2; persists source observation fingerprint, source anchor fingerprint, source anchor version, and anchor reference policies.
- Confirms existing observation at `2026-09-28T11:45:00Z` is excluded from formal scoring: `POST_CONTRACT_ACQUISITION_PROOF_EXCLUDED_FROM_FORMAL_SCORING_MISSING_PROSPECTIVE_ANCHOR`.
- Zero genuine outcomes matured or appended during offline freeze.

### Anchor-Required Maturation & Ledger V2 Evidence Artifact
- **File**: `04_Testing/evidence/forward_shadow/xauusd_gate_15d_c_b2bc_anchor_required_maturation_ledger_v2_evidence.json`
- **Verdict**: **PASS**
- **Maturation Version**: `FROZEN_C04_FORWARD_OUTCOME_MATURER_V2`
- **Outcome Ledger Version**: `FROZEN_C04_FORWARD_OUTCOME_LEDGER_V2`
- **Candidate Artifact Hashes**:
  - `02_AI/Models/frozen_c04_forward_outcome_maturer.py`: `f2100d092874ca8acbcc0a43131540be0cebe1975f2fcd875f81ac44be50901f`
  - `02_AI/Models/frozen_c04_forward_outcome_ledger.py`: `6781e04d79377784de257177191007ec707a486ead4ca88ee70a7a714f89d8ec`
- **Offline Protocol State**:
  - `genuine_anchor_appended`: `False`
  - `genuine_outcome_appended`: `False`
  - `forward_performance_evaluated`: `False`
- **Safety Invariants**:
  - `live_authorized = False`
  - `execution_authorized = False`
  - `forward_performance_evaluated = False`

---

# 63. Authoritative Current-State Summary (Baseline Commit `cbdeb30934213dc36863c334eb1e50879ba0dde1`)

### Published Implementation Baseline
- **Commit SHA**: `cbdeb30934213dc36863c334eb1e50879ba0dde1`
- **Branch**: `main`

### Frozen Stack
- **Gate 13**: 331-feature portable pipeline (`65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2`)
- **Gate 14**: Frozen C04 inference adapter (`C04_FLAT_EXTRA_TREES_CONSTRAINED`, `48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769`, raw argmax, class order `[-1, 0, 1]`)
- **Gate 15B-A**: MT5 read-only acquisition adapter v2.1.0 (`MT5ReadOnlyForwardAcquisitionAdapter:2.1.0`, NY close server epoch, per-row historical DST normalization)
- **Gate 15C**: Frozen forward outcome contract V1 (`FROZEN_C04_FORWARD_OUTCOME_CONTRACT_V1`, `01fe52a2f068fcc8fb2fc5b89dd7e19dc974fc2d967cfb791e75c3415804ce87`, `CLEAN_DIRECTIONAL_EXCURSION_V2`, 1.25/0.75 ATR, 12 M5 rows)
- **Gate 15D-A**: Prospective eligibility authority (`FROZEN_C04_FORWARD_OUTCOME_ELIGIBILITY_V1`, cutoff `2026-09-28T11:16:59Z`)
- **Gate 15D-C-B2A**: Prospective outcome anchor authority V1 (`FROZEN_C04_FORWARD_OUTCOME_ANCHOR_V1`, capture policy `SAME_ACQUISITION_SNAPSHOT_NO_FUTURE_M5_ROWS`)
- **Gate 15D-C-B2B**: Anchor-required forward outcome maturer V2 (`FROZEN_C04_FORWARD_OUTCOME_MATURER_V2`, post-hoc reconstruction forbidden)
- **Gate 15D-C-B2C**: Forward outcome ledger V2 (`FROZEN_C04_FORWARD_OUTCOME_LEDGER_V2`)

### Runtime Ledgers Status
- **Observation Ledger** (`01_Data/Shadow/xauusd_frozen_c04_shadow_observations.jsonl`):
  - Current count: **2**
  - Obs 1 (`2026-09-28T10:15:00Z`): Pre-contract audit only; permanently excluded from formal performance.
  - Obs 2 (`2026-09-28T11:45:00Z`): Post-contract genuine acquisition proof; **EXCLUDED FROM FORMAL SCORING** due to missing prospective anchor (`POST_CONTRACT_ACQUISITION_PROOF_EXCLUDED_FROM_FORMAL_SCORING_MISSING_PROSPECTIVE_ANCHOR`).
- **Anchor Ledger** (`01_Data/Shadow/xauusd_frozen_c04_forward_outcome_anchors.jsonl`):
  - Current count: **0** (zero genuine anchors appended during offline freeze).
- **Outcome Ledger** (`01_Data/Shadow/xauusd_frozen_c04_forward_outcomes.jsonl`):
  - Current count: **0** (zero genuine outcomes matured or appended).

### Current Phase & Next Gate
- **Current Phase**: `Prospective Forward Observation + Anchor Integration Preparation`
- **Next Planned Gate**: `Gate 15D-C-B2D — Genuine Prospective Observation + Same-Snapshot Anchor Integration`

### Safety Invariants
- `formal_forward_scoring = NOT_STARTED` (`forward_performance_evaluated = false`)
- `live_trading = NOT_AUTHORIZED` (`live_authorized = false`)
- `execution = NOT_AUTHORIZED` (`execution_authorized = false`)
- Zero aggregate performance metrics reported. Zero trading runtime dependencies imported.

<!-- REPOSITORY-ARCHITECTURE-MANAGED:START -->
## Repository Evidence Location Note

> Managed evidence-structure section.

Non-frozen research and portability JSON evidence is being consolidated under
`04_Testing/evidence/`.

Current structured evidence areas include:

- `04_Testing/evidence/production_portability/`
- `04_Testing/evidence/research/legacy_ml/`
- `04_Testing/evidence/research/portable_331/train/`

Frozen one-time VALIDATION / TEST artifacts that participate in established
path contracts remain at their frozen root locations.

Evidence relocation does not alter the contents or scientific interpretation
of the frozen historical results and does not permit VALIDATION or TEST to be
rerun.

The final historical research verdict remains unchanged: historical
out-of-sample acceptance does not itself authorize live trading or automatic
shadow deployment.
<!-- REPOSITORY-ARCHITECTURE-MANAGED:END -->
