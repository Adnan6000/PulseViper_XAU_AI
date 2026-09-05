# PulseViper XAU AI — Development Roadmap

## 1. Purpose

This document is the live engineering roadmap for PulseViper XAU AI.

It tells a developer:

* what has already been completed;
* what is currently frozen;
* what is safe to work on;
* what remains;
* which tasks depend on other tasks;
* which tasks require protected data;
* and approximately how much engineering effort remains.

This roadmap should be updated whenever a major engineering or research gate is completed.

---

# 2. Status Legend

```text
✅ COMPLETE
🟢 READY / AUTHORIZED NEXT
🟡 PARTIAL / IN PROGRESS
🔴 BLOCKED / PROTECTED
⬜ NOT STARTED
⛔ NOT AUTHORIZED
```

---

# 3. Current Project Position

Current high-level state:

```text
Portable ML Research
        ↓
TRAIN research
        ✅
        ↓
Frozen C04 winner
        ✅
        ↓
Full TRAIN fit
        ✅
        ↓
Untouched VALIDATION
        ✅ PASSED
        ↓
VALIDATION freeze
        ✅
        ↓
FINAL TEST
        🟢 NEXT
        ↓
Production portability
        ⬜
        ↓
Shadow integration
        ⬜
        ↓
Forward shadow validation
        ⬜
        ↓
Live promotion
        ⛔
```

Current frozen model:

```text
C04_FLAT_EXTRA_TREES_CONSTRAINED
```

Current feature contract:

```text
331 ordered portable features
```

Current live status:

```text
live_authorized = false
```

---

# 4. Overall Completion Estimate

Approximate engineering maturity:

| Area                              | Approximate State |
| --------------------------------- | ----------------: |
| Core runtime / risk foundation    |            90–95% |
| Portable feature research         |            90–95% |
| Historical ML research pipeline   |              95%+ |
| TRAIN model research              |              100% |
| Untouched VALIDATION              |              100% |
| Final TEST                        |           Pending |
| Production broker portability     |            55–65% |
| Frozen-model production inference |            30–40% |
| Shadow integration                |            30–40% |
| Forward shadow validation         |             Early |
| Safe live promotion readiness     |           ~50–60% |

These percentages are engineering estimates, not scientific metrics.

---

# 5. Remaining Engineering Time Estimate

Approximate active engineering effort from the current state:

| Remaining Area                        | Estimated Active Work |
| ------------------------------------- | --------------------: |
| Final TEST infrastructure + execution |             2–4 hours |
| Final research verdict/report         |             1–2 hours |
| Documentation/evidence cleanup        |             3–5 hours |
| Production broker portability         |           12–20 hours |
| Frozen inference + shadow integration |            8–14 hours |
| Production safety / monitoring        |            8–12 hours |

Approximate remaining active engineering:

```text
35–55 focused hours
```

A realistic focused development schedule is approximately:

```text
5–8 working days
```

However, full project completion requires genuine future unseen market data.

Therefore expected calendar duration is more realistically:

```text
3–6 weeks
```

The longer calendar estimate is mainly due to forward-shadow observation, not coding speed.

---

# 6. Phase 1 — Core Runtime Foundation

**Status: ✅ COMPLETE / PROTECTED**

Completed areas include:

* [x] MetaTrader/runtime structure
* [x] trading permission concepts
* [x] RiskEngine
* [x] `trade_ready`
* [x] account protection
* [x] broker-aware sizing
* [x] execution semantics
* [x] shadow execution concepts
* [x] separation between ML research and execution

Current rule:

> Do not modify the runtime simply to improve ML metrics.

Protected areas include:

```text
RiskEngine
trade_ready
account protection
broker-aware sizing
MT5 order semantics
core execution
shadow execution semantics
```

---

# 7. Phase 2 — Feature Pipeline Research

**Status: ✅ MAJOR RESEARCH COMPLETE**

Completed:

* [x] existing feature pipeline analyzed
* [x] broker-sensitive features investigated
* [x] portable feature strategy designed
* [x] portable feature contract created
* [x] final portable feature count frozen
* [x] ordered feature contract frozen
* [x] feature fingerprint frozen
* [x] dataset integration verified

Current feature count:

```text
331
```

Frozen ordered feature fingerprint:

```text
65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2
```

Still required for production:

* [ ] prove same semantic features on a different broker
* [ ] canonicalize broker timestamps
* [ ] reconstruct D1 consistently
* [ ] test missing-bar behavior
* [ ] test session transitions
* [ ] compare historical vs production feature generation
* [ ] enforce feature fingerprint at inference

---

# 8. Phase 3 — Portable Dataset Infrastructure

**Status: ✅ COMPLETE**

Completed:

* [x] exact portable artifact discovery
* [x] manifest validation
* [x] dataset identity validation
* [x] split structure validation
* [x] TRAIN feature loader
* [x] TRAIN target loader
* [x] supervised TRAIN batch
* [x] feature/target row alignment
* [x] chronology validation
* [x] tradeability linkage
* [x] original VALIDATION access fail-closed
* [x] original TEST access fail-closed

Frozen TRAIN dataset:

```text
dataset_id:
portable_cff75b0686383a3ab6f8352b

TRAIN rows:
69,966

features:
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

---

# 9. Phase 4 — Frozen Target Contract

**Status: ✅ COMPLETE**

Target classes:

```text
-1 = SHORT
 0 = NO_TRADE
 1 = LONG
```

Frozen directional-excursion parameters:

```text
profit_atr = 1.25
max_adverse_atr = 0.75
```

Required linkage:

```python
target_tradeable = (target_class != 0).astype("int8")
```

Changing target semantics requires:

```text
new target contract
        +
new dataset lineage
        +
new model experiment
```

---

# 10. Phase 5 — TRAIN Research Protocol

**Status: ✅ COMPLETE**

Frozen model research protocol includes:

* [x] TRAIN-only model research
* [x] chronological folds
* [x] expanding window
* [x] no shuffle
* [x] four folds
* [x] twelve-row purge
* [x] no portable VALIDATION during selection
* [x] no TEST during selection
* [x] no grid search
* [x] no Bayesian optimization
* [x] no threshold tuning
* [x] no calibration
* [x] no results-driven feature selection

Research protocol fingerprint:

```text
69e51e1b249b9da68cbf6f6778a8ae10f9f33f7082a07e5073a1ba731fa1640d
```

---

# 11. Phase 6 — Candidate Registry

**Status: ✅ COMPLETE**

Exactly six candidates were frozen before real candidate evaluation.

* [x] C01 balanced Logistic Regression
* [x] C02 balanced Logistic Regression
* [x] C03 constrained HistGradientBoosting
* [x] C04 constrained ExtraTrees
* [x] C05 hierarchical Logistic Regression
* [x] C06 hierarchical HGB + Logistic Regression

Candidate registry fingerprint:

```text
b8088bb34ce8940f7de5946fbb9b0fd20f40d7cc93a76b76fd7975591f00066c
```

Important rule:

> Do not add Candidate 7 to this frozen experiment after seeing results.

A new candidate belongs to a new research lineage.

---

# 12. Phase 7 — Candidate Evaluator

**Status: ✅ COMPLETE**

Completed:

* [x] input validation
* [x] fold validation
* [x] probability validation
* [x] flat model support
* [x] hierarchical model support
* [x] fold-local scaling where required
* [x] fold-local weighting where required
* [x] exact class order
* [x] 15-metric contract
* [x] eligibility rules
* [x] frozen winner selection
* [x] dummy-prior diagnostic
* [x] synthetic tests
* [x] package/runtime import tests
* [x] integration attestation

---

# 13. Phase 8 — Real TRAIN Walk-Forward

**Status: ✅ COMPLETE**

All frozen candidates were evaluated on:

```text
6 candidates
×
4 chronological TRAIN folds
```

Winner:

```text
C04_FLAT_EXTRA_TREES_CONSTRAINED
```

Important C04 TRAIN statistics:

```text
Mean directional macro-F1:
0.3105791161393638

Worst-fold directional macro-F1:
0.25365034089349603

Mean balanced accuracy:
0.35438789335022963

Mean macro-F1:
0.2846765787595467
```

Walk-forward evaluation fingerprint:

```text
15516174ba6f3d8932425b20dcde33db25c040e0901c86af39796f97847ac7ed
```

---

# 14. Phase 9 — Winner Freeze

**Status: ✅ COMPLETE**

Frozen winner:

```text
C04_FLAT_EXTRA_TREES_CONSTRAINED
```

Frozen candidate configuration fingerprint:

```text
f1b11c6f91561f2eba1bd56195e2239e9598b1906c88f11ada67eac6cdeb09e3
```

Winner was frozen before full TRAIN fitting.

No VALIDATION or TEST values were required for this decision.

---

# 15. Phase 10 — Full TRAIN Fit

**Status: ✅ COMPLETE**

C04 was fitted on all:

```text
69,966 TRAIN rows
```

using:

```text
331 features
```

Frozen model artifact:

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

# 16. Phase 11 — Model Artifact Verification

**Status: ✅ COMPLETE**

Verified:

* [x] model file SHA
* [x] ExtraTrees model type
* [x] 331 input features
* [x] class order `[-1, 0, 1]`
* [x] 500 trees
* [x] exact frozen hyperparameters
* [x] full TRAIN provenance chain
* [x] no holdout access during verification

Verification record fingerprint:

```text
a2759a429b90998a7d24c8b217e570813e36dcf43df5de6cf98daf875b8678ef
```

---

# 17. Phase 12 — VALIDATION Acceptance Protocol

**Status: ✅ COMPLETE**

Acceptance criteria were frozen before the first real VALIDATION value read.

Protocol fingerprint:

```text
ce78180a5f2472c36c74cea2c447307641aa3d5fedfb7a01d9b65260b5a6fcea
```

Hard checks included:

* [x] all required metrics finite
* [x] all target classes present
* [x] directional macro-F1 floor
* [x] balanced accuracy floor
* [x] macro-F1 floor
* [x] SHORT recall positive
* [x] LONG recall positive
* [x] minimum trade coverage
* [x] maximum trade coverage

Report-only metrics:

```text
log-loss
multiclass Brier
```

No post-hoc calibration was allowed.

---

# 18. Phase 13 — One-Time VALIDATION Infrastructure

**Status: ✅ COMPLETE**

Completed:

* [x] one-time access ledger
* [x] pre-read reservation
* [x] consumed-read boundary
* [x] pre-read failure recovery
* [x] post-read rerun blocking
* [x] validation batch contract
* [x] metric reuse from frozen evaluator
* [x] synthetic pass test
* [x] synthetic rejection test
* [x] synthetic technical-failure tests
* [x] bounded VALIDATION source
* [x] TEST rows protected
* [x] dry preflight
* [x] preflight fingerprint

Preflight fingerprint:

```text
5ee6d0948d93f83f7969662e103066f1a09d7b081883290aba104b52f0038f41
```

---

# 19. Phase 14 — Real Untouched VALIDATION

**Status: ✅ PASSED AND CONSUMED**

Result:

```text
ONE_TIME_VALIDATION_ACCEPTED
```

Metrics:

| Metric               |   Result |
| -------------------- | -------: |
| Balanced accuracy    | 0.376568 |
| Macro-F1             | 0.348904 |
| Directional macro-F1 | 0.336403 |
| SHORT precision      | 0.329373 |
| SHORT recall         | 0.319050 |
| SHORT F1             | 0.324129 |
| NO_TRADE precision   | 0.557003 |
| NO_TRADE recall      | 0.281404 |
| NO_TRADE F1          | 0.373907 |
| LONG precision       | 0.259975 |
| LONG recall          | 0.529249 |
| LONG F1              | 0.348676 |
| Trade coverage       | 0.754121 |
| Log-loss             | 1.097919 |
| Brier                | 0.666429 |

Result fingerprint:

```text
ea8b482e60f854f58e27f3be387b7bb82f0c16a6cf1a99555b12643aeeca5fa1
```

Current rule:

```text
validation_consumed = true
validation_rerun_authorized = false
```

---

# 20. Phase 15 — VALIDATION Result Freeze

**Status: ✅ COMPLETE**

Freeze fingerprint:

```text
521a97b41a86231b049cc65aebfd85ffc7c83ae7141134d6ae1158d112b1468c
```

Current decision:

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

# 21. Phase 16 — Final Untouched TEST

**Status: 🟢 IMMEDIATE NEXT ENGINEERING GATE**

The TEST split is still protected.

Required implementation:

* [ ] one-time TEST access contract
* [ ] TEST-specific ledger
* [ ] bounded TEST source
* [ ] frozen model verification before TEST read
* [ ] synthetic source tests
* [ ] synthetic ledger tests
* [ ] TEST dry preflight
* [ ] freeze TEST preflight fingerprint
* [ ] first and only real TEST read
* [ ] compute exact same evaluation metrics
* [ ] persist TEST result
* [ ] freeze TEST result
* [ ] prohibit rerun

Important:

> TEST does not select a new model.

It evaluates the already frozen model.

---

# 22. TEST Success Criteria Philosophy

The final TEST should answer:

> Does C04 still show acceptable generalization on the final untouched holdout?

It should not answer:

> Which parameters should we change next?

If TEST is weak, the current model lineage should be closed and a new research iteration designed.

Do not tune C04 against TEST.

---

# 23. Phase 17 — Final Historical Research Verdict

**Status: ⬜ PENDING TEST**

After TEST:

* [ ] compare TRAIN walk-forward
* [ ] compare VALIDATION
* [ ] compare TEST
* [ ] directional degradation analysis
* [ ] class-recall stability
* [ ] trade-coverage stability
* [ ] probability-quality review
* [ ] document limitations
* [ ] freeze final historical research verdict

Possible state:

```text
RESEARCH_ACCEPTED_FOR_SHADOW
```

This is different from:

```text
LIVE_READY
```

---

# 24. Phase 18 — Production Broker Portability

**Status: 🟡 PARTIAL**

Major remaining engineering block.

Required work:

* [ ] broker symbol mapping
* [ ] XAUUSD/XAUUSDm normalization
* [ ] broker server-time analysis
* [ ] canonical timestamp definition
* [ ] session boundary normalization
* [ ] D1 candle reconstruction
* [ ] MTF synchronization
* [ ] missing-bar handling
* [ ] stale-bar detection
* [ ] warm-up window definition
* [ ] 331-feature generation
* [ ] feature-order enforcement
* [ ] feature fingerprint validation
* [ ] replay parity testing

Estimated active effort:

```text
12–20 hours
```

---

# 25. Phase 19 — Production Feature Parity

**Status: ⬜ PENDING**

The key question:

```text
Does production generate the same feature semantics
that the historical model was trained on?
```

Required evidence:

* [ ] same feature count
* [ ] same ordered columns
* [ ] same formulas
* [ ] same units
* [ ] same timezone semantics
* [ ] same D1 semantics
* [ ] finite values
* [ ] deterministic replay
* [ ] acceptable broker-to-broker differences

---

# 26. Phase 20 — Frozen Model Inference Adapter

**Status: ⬜ PENDING**

Required:

* [ ] verify model artifact SHA at startup
* [ ] verify model class
* [ ] verify class order
* [ ] verify feature count
* [ ] verify feature-column fingerprint
* [ ] reject non-finite inputs
* [ ] reject stale inputs
* [ ] call `predict_proba`
* [ ] use frozen argmax
* [ ] no runtime threshold tuning
* [ ] structured inference log

Expected inference flow:

```text
Portable 331 Features
        ↓
Feature Contract Check
        ↓
Model SHA Check
        ↓
predict_proba
        ↓
argmax
        ↓
SHORT / NO_TRADE / LONG
```

---

# 27. Phase 21 — Shadow Integration

**Status: ⬜ PENDING**

Required:

* [ ] connect inference to shadow decision path
* [ ] preserve RiskEngine
* [ ] preserve sizing logic
* [ ] preserve trade readiness checks
* [ ] no live orders
* [ ] log probabilities
* [ ] log predicted class
* [ ] log feature identity
* [ ] log hypothetical trade
* [ ] log hypothetical SL/TP
* [ ] log spread/cost context

Estimated active effort:

```text
8–14 hours
```

---

# 28. Phase 22 — Forward Shadow Validation

**Status: ⬜ PENDING**

This phase requires real future time.

Measure:

* [ ] unseen market period
* [ ] directional performance
* [ ] SHORT/LONG balance
* [ ] prediction distribution
* [ ] trade coverage
* [ ] high-volatility behavior
* [ ] low-volatility behavior
* [ ] trending regimes
* [ ] ranging regimes
* [ ] session transitions
* [ ] spread expansion
* [ ] missing data
* [ ] feature drift
* [ ] prediction drift
* [ ] hypothetical costs
* [ ] hypothetical drawdown
* [ ] hypothetical expectancy

Expected calendar observation:

```text
approximately 2–4+ weeks
```

depending on required market coverage.

---

# 29. Phase 23 — Production Safety and Monitoring

**Status: ⬜ PENDING**

Before live promotion:

* [ ] model SHA startup enforcement
* [ ] feature SHA startup enforcement
* [ ] symbol validation
* [ ] timezone validation
* [ ] stale-data kill condition
* [ ] missing-bar protection
* [ ] non-finite feature protection
* [ ] inference exception handling
* [ ] feature drift monitoring
* [ ] prediction drift monitoring
* [ ] spread protection
* [ ] operational audit log
* [ ] shadow/live mode separation
* [ ] emergency kill switch
* [ ] rollback procedure

Estimated active effort:

```text
8–12 hours
```

---

# 30. Phase 24 — Live Promotion Decision

**Status: ⛔ NOT AUTHORIZED**

Required before live:

```text
[ ] Final TEST acceptable
[ ] Final research verdict frozen
[ ] New-broker feature parity proven
[ ] Production inference verified
[ ] Shadow integration stable
[ ] Forward unseen-market evidence acceptable
[ ] Costs reviewed
[ ] Drawdown reviewed
[ ] RiskEngine verified
[ ] Failure behavior tested
[ ] Kill switch tested
[ ] Explicit live promotion decision
```

Only after all required gates:

```text
live_authorized = true
```

Current:

```text
live_authorized = false
```

---

# 31. Documentation Roadmap

Documentation should also be treated as engineering work.

Current documentation refresh plan:

```text
README.md
    ✅ planned/current refresh

Developer_Guide.md
    ✅ planned/current refresh

Architecture.md
    ✅ planned/current refresh

Module_List.md
    ✅ planned/current refresh

Development_Roadmap.md
    ✅ THIS DOCUMENT

Feature_List.md
    ✅ paired with this gate

Testing_Guide.md
    ⬜ NEXT DOC GATE

Research_Evidence_Index.md
    ⬜ NEXT DOC GATE

Troubleshooting.md
    ⬜

Trading_Rules.md
    ⬜ refresh

Version_History.md
    ⬜ refresh
```

After all documentation is updated:

* [ ] review links
* [ ] review fingerprints
* [ ] review current project status
* [ ] review Git history
* [ ] commit docs
* [ ] controlled GitHub push

---

# 32. Recommended Development Order From Here

The preferred sequence is:

```text
1. Finish documentation baseline
2. Final TEST infrastructure
3. Final TEST
4. Final historical research verdict
5. Production broker portability
6. Production feature parity
7. Frozen inference adapter
8. Shadow integration
9. Forward shadow validation
10. Production safety review
11. Live promotion decision
```

The ordering is important.

For example, there is little value integrating a model into shadow production before its final untouched TEST result is known.

---

# 33. New Student Roadmap

A new student should progress in stages.

## Stage A — Learn

* [ ] read README
* [ ] read Developer Guide
* [ ] read Architecture
* [ ] read this Roadmap
* [ ] understand TRAIN/VALIDATION/TEST

## Stage B — Observe

* [ ] run existing focused tests
* [ ] inspect evidence JSON
* [ ] trace a feature through code
* [ ] trace model provenance

## Stage C — Contribute Safely

Start with:

* [ ] documentation
* [ ] synthetic tests
* [ ] report generators
* [ ] non-production research tools

Then later:

* [ ] feature research
* [ ] portability
* [ ] model research

Protected runtime work should come last.

---

# 34. New Feature Development Roadmap

If a student wants to add a feature:

```text
Feature idea
    ↓
Define exact formula
    ↓
Define timeframe
    ↓
Define units
    ↓
Check leakage
    ↓
Check broker portability
    ↓
Write tests
    ↓
Create new feature contract
    ↓
Create new dataset lineage
    ↓
Create new model experiment
```

Do not edit the frozen 331 experiment in place.

---

# 35. New Model Development Roadmap

If a future developer wants a new model:

```text
New research question
    ↓
TRAIN-only protocol
    ↓
Frozen finite candidate registry
    ↓
Walk-forward evaluation
    ↓
Winner freeze
    ↓
Full TRAIN fit
    ↓
Artifact verification
    ↓
Frozen validation criteria
    ↓
Untouched VALIDATION
    ↓
Untouched TEST
```

Do not start from TEST.

---

# 36. Definition of Project Completion

PulseViper should not be considered fully complete when:

```text
model.fit() works
```

A production-grade milestone requires:

```text
research reproducibility
+
generalization evidence
+
broker portability
+
runtime correctness
+
shadow evidence
+
forward evidence
+
operational safety
```

---

# 37. Current Bottom Line

Completed:

```text
Historical portable ML research:
nearly complete

Untouched VALIDATION:
PASSED

Model artifact:
frozen and verified
```

Immediate next research task:

```text
Final untouched TEST infrastructure
```

Largest remaining engineering task:

```text
Production broker feature parity
+
shadow integration
```

Largest remaining calendar-time task:

```text
Forward shadow validation
```

Current live state:

```text
NOT AUTHORIZED
```

<!-- REPOSITORY-ARCHITECTURE-MANAGED:START -->
## Repository Architecture Cleanup Subphase

> Managed roadmap section.

Repository organization is being stabilized before further large-scale
testing/research migration.

Completed:

- froze a repository testing/evidence inventory;
- froze the original migration manifest as historical planning evidence;
- reduced root-level JSON evidence from 68 files to 19 intentional/frozen
  exceptions;
- moved 49 non-frozen JSON evidence artifacts into structured
  `04_Testing/evidence/` locations;
- created `04_Testing/production_portability/`;
- migrated 38 production-portability Python files;
- preserved frozen holdout material during those migrations;
- passed Python compilation for the portability batch;
- passed the focused portability regression suite with 113 tests;
- removed the empty duplicate top-level `Data/` directory while preserving
  canonical `01_Data/`.

Current work:

- replace the original filename-token migration approach with architecture V2;
- resolve test ownership from actual source behavior and dynamic loading;
- preserve and update CI test paths during relocation;
- reduce repository-root depth coupling before broad nested migration;
- continuously synchronize architecture/testing/module documentation.

The current source-ownership resolver is not yet sufficient for mass
migration: many tests use dynamic imports/loaders and remain unresolved.

This repository-cleanup subphase does not change the frozen XAUUSD historical
research verdict and does not authorize live or shadow deployment.
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
## Architecture V2 Execution Progress

The first V2 execution batch migrated 18 HIGH-confidence SAFE_A Core tests to
`04_Testing/ai/core/`.

The batch preserved file contents, updated 9 CI paths, passed Python
compilation, and passed the focused moved-Core pytest suite.

Nineteen READY-but-location-sensitive tests remain intentionally unmoved.
Further V2 batches continue to fail closed on file-location dependencies.
<!-- V2-CORE-SAFE-A-MIGRATION:END -->

<!-- V2-SHADOW-SAFE-A-MIGRATION:START -->
## Architecture V2 Shadow Progress

The second executable V2 batch migrated 35 Shadow-owned tests to
`04_Testing/ai/shadow/` and updated 11 CI paths.

The first focused Shadow run produced 661 passes and one failure. The failure
was caused by a stale dotted test-module import rather than by a production
behavior regression.

Exactly one Shadow test required a structural module-path edit. After that
repair, Python compilation passed and all 662 focused Shadow tests passed.

Core and Shadow source-aligned migration now covers 53 tests.
<!-- V2-SHADOW-SAFE-A-MIGRATION:END -->

<!-- V2-FINAL-LOCATION-INDEPENDENT-BATCH:START -->
## Location-Independent V2 Migration Completion

All currently proven location-independent READY tests have now been migrated.

Architecture V2 execution status:

- 59 READY migrations executed;
- 19 READY files remain location-sensitive;
- 77 files remain REVIEW_REQUIRED;
- 18 frozen compatibility files remain fixed;
- 1 pytest root-support file remains fixed.

The next structural phase is not another mechanical move batch. It is a
dedicated path-bootstrap design for the 19 location-sensitive READY tests.
<!-- V2-FINAL-LOCATION-INDEPENDENT-BATCH:END -->

<!-- V2-PYTEST-BOOTSTRAP-CONSOLIDATION:START -->
## Pytest Bootstrap Consolidation

Seventeen previously location-sensitive READY tests have had redundant local
pytest bootstrap removed while remaining at their existing filesystem paths.

Their focused project-environment suite passed 41 tests before relocation.

Two legacy Dataset tests encountered during verification were aligned to the
already-existing mandatory InstrumentContext API and converted to deterministic
temporary-output tests.

Current READY execution work is split into:

- 17 bootstrap-cleaned tests ready for relocation;
- 1 test requiring import normalization;
- 1 test requiring repository-root abstraction.

This removes path-depth debt instead of carrying `parents[n]` adjustments into
new test directories.
<!-- V2-PYTEST-BOOTSTRAP-CONSOLIDATION:END -->
