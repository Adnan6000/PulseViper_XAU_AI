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

The project has moved beyond the original C04 forward-evaluation lane into a completed historical remediation cycle.

```text
Original C04 research baseline
        ↓
30 matured prospective samples
        ↓
Weak forward discrimination
        ↓
G7-A remediation rules freeze
        ↓
G7-B remediation data authority freeze
        ↓
G7-C exact training snapshot freeze
        ↓
G7-D remediation research protocol freeze
        ↓
G7-E six-candidate registry freeze
        ↓
G7-F-A TRAIN + VALIDATION remediation access
        ↓
G7-F-B six-candidate evaluation
        ↓
G7-F-C R03 remediation winner freeze
        ↓
G7-G-A sealed TEST confirmation criteria
        ↓
G7-G-B one-shot sealed TEST
        ↓
R03 TEST CONFIRMED
        ↓
G7-H-A R03 prospective forward contract
        ↓
G7-H-B R03 train-only artifact
        ↓
G7-H-C prospective runtime binding
        ↓
G7-H-D outcome maturation binding
        ↓
G7-H-E-A collection controller
        ↓
G7-H-E-B first genuine capture
        ↓
R1/R2 recovery lanes
        ↓
CURRENT: first genuine R03 capture still blocked
```

### Current authority

- Historical C04 remains preserved as the original control lineage.
- G7-E froze exactly six remediation candidates.
- G7-F-C froze `R03_FLAT_EXTRA_TREES_SMOOTH` as the remediation winner.
- G7-G-B performed the one-shot sealed TEST on R03 and recorded `SEALED_TEST_CONFIRMED`.
- G7-H froze the prospective R03 forward contract and its train-only runtime path.
- No old Forward30 sample was used for remediation training, candidate selection, TEST tuning, or PnL optimization.
- No live execution or account-risk integration is authorized.

### Current R03 prospective collection state

```text
observations = 0
anchors = 0
matured_outcomes = 0
distinct_matured_utc_dates = 0
minimum_matured_outcomes = 60
minimum_distinct_utc_dates = 5
```

The latest first-capture recovery runner is frozen, but capture remains blocked by:

```text
TIMESTAMP_BASIS_NOT_UNIQUELY_PROVEN
raw_tick=1790985539
candidate_count=0
```

The correct response is to prove the timestamp basis or obtain a valid fresh observation. The timestamp check must not be weakened.

Current authorization:

```text
live_authorized = false
execution_authorized = false
performance_evaluated = false
pnl_evaluated = false
```

---

# 4. Current Completion / Remaining Work

The earlier percentage estimates were tied to the pre-remediation C04/forward infrastructure state and are no longer authoritative.

Current milestone state:

| Area | Current state |
|---|---|
| Original C04 research lineage | Frozen historical control |
| G7 remediation protocol | Complete |
| G7 six-candidate registry | Frozen |
| G7-F-B candidate evaluation | Complete |
| R03 remediation winner | Frozen |
| G7-G-B sealed TEST | Passed and consumed |
| R03 prospective contract | Frozen |
| R03 train-only artifact | Frozen and verified |
| R03 runtime/maturation/controller | Frozen and safety-tested |
| First genuine R03 forward capture | **Blocked** |
| Matured R03 forward evaluation | Not started |
| Production/live execution | Not authorized |

The current bottleneck is **prospective evidence acquisition**, not candidate-model research.

# 5. Immediate Remaining Work

1. Resolve the R03 timestamp-basis proof without weakening the fail-closed check.
2. Execute the frozen first-genuine-capture runner when a valid unique timestamp basis is available.
3. Preserve anchor-first → observation persistence ordering.
4. Accumulate at least 60 matured R03 outcomes spanning at least 5 distinct UTC observation dates.
5. Perform the separately authorized prospective R03 evaluation.
6. Only after sufficient forward evidence, perform the next production-safety and live-promotion review.

No TEST rerun, candidate replacement, threshold tuning, calibration, or old Forward30 tuning is authorized by this lane.

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

Historical portability research is complete and Gate 13 production broker feature parity is complete. Remaining production work is integration/operational rather than redoing the portability research:

* [x] canonicalize broker timestamps under the Gate 15B-A authority
* [x] reconstruct D1 consistently under the production feature pipeline
* [x] test missing/duplicate-bar behavior and stale-bar handling
* [x] compare historical vs production feature generation for Gate 13 parity
* [x] enforce the feature fingerprint in the frozen inference path
* [ ] complete end-to-end production runtime integration and operational validation

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

# 21. Phase 16 — G7 Remediation Cycle

**Status: ✅ COMPLETE**

The remediation cycle replaced the old “C04 TEST pending” state.

Completed:

* [x] G7-A remediation rules freeze
* [x] G7-B remediation data authority
* [x] G7-C exact training snapshot
* [x] G7-D research protocol freeze
* [x] G7-E six-candidate registry freeze
* [x] G7-F-A TRAIN + VALIDATION access
* [x] G7-F-B six-candidate evaluation
* [x] G7-F-C R03 final winner freeze
* [x] G7-G-A sealed TEST criteria
* [x] G7-G-B one-shot sealed TEST

Final remediation winner:

```text
R03_FLAT_EXTRA_TREES_SMOOTH
```

G7-G-B result:

```text
status = SEALED_TEST_CONFIRMED
balanced_accuracy = 0.3636245672
macro_f1 = 0.3490621418
minimum_per_class_recall = 0.2983711747
multiclass_brier = 0.6647780980
multiclass_log_loss = 1.0958700266
test_access_count = 1
same_test_rerun_authorized = false
```

The sealed TEST was an offline research confirmation. It did not authorize live trading.

---

# 22. Phase 17 — R03 Prospective Forward Validation

**Status: 🟡 ACTIVE COLLECTION / BLOCKED AT FIRST CAPTURE**

G7-H completed the frozen prospective infrastructure for R03:

* [x] G7-H-A prospective validation contract
* [x] G7-H-B train-only frozen R03 artifact
* [x] G7-H-C prospective runtime binding
* [x] G7-H-D outcome maturation binding
* [x] G7-H-E-A finite collection controller
* [x] G7-H-E-B first genuine capture runner
* [x] R1 first-capture recovery runner
* [x] R2 first-capture recovery runner

Frozen R03 prospective requirements:

```text
minimum_matured_outcomes = 60
minimum_distinct_observation_utc_dates = 5
horizon = next 12 completed M5 rows
profit_atr = 1.25
max_adverse_atr = 0.75
```

R03 artifact authority:

```text
candidate = R03_FLAT_EXTRA_TREES_SMOOTH
artifact_sha256 = b5da550921ef227b847207cfbfe5774e86f083f1d3354069a9624a5029ea2a03
feature_count = 331
train_rows = 69966
```

Current collection state:

```text
observations = 0
anchors = 0
matured_outcomes = 0
distinct_matured_utc_dates = 0
```

The first genuine capture and both recovery attempts were blocked by:

```text
TIMESTAMP_BASIS_NOT_UNIQUELY_PROVEN
raw_tick=1790985539
candidate_count=0
```

This is a **fail-closed evidence block**. The timestamp-basis validation must be proven, not weakened.

The latest R2 recovery runner is frozen and preserves the original blocked evidence.

### Next authorized engineering action

Resolve the timestamp-basis proof / obtain a valid fresh capture context, then run the already-frozen capture lane.

Do not:

* weaken timestamp validation;
* fabricate or backfill a prospective anchor;
* rewrite protected runtime ledgers;
* rerun the sealed TEST;
* tune R03 from prospective observations;
* use the old Forward30 for remediation.

---

# 24. Phase 18 — Production Broker Portability

**Status: ✅ COMPLETE (Gate 13)**

Completed under Gate 13:

* [x] broker symbol mapping (`XAUUSD`, `XAUUSDm`)
* [x] XAUUSD/XAUUSDm normalization & strict fail-closed rejection of unproven symbols
* [x] broker server-time analysis & 00:00:00 UTC session boundary proof
* [x] canonical timestamp definition (ISO-8601 UTC / pandas DatetimeIndex)
* [x] session boundary normalization
* [x] D1 candle reconstruction (from H1/intraday with 0-mismatch verification vs native broker D1)
* [x] MTF synchronization (causal `merge_asof` with backward direction)
* [x] missing-bar handling & insufficient history fail-closed check
* [x] stale-bar detection & duplicate timestamp rejection
* [x] warm-up window definition
* [x] 331-feature generation via `PortableFeaturePipeline`
* [x] feature-order enforcement via `PortableFeatureContract`
* [x] feature fingerprint validation (`65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2`)
* [x] replay parity testing

---

# 25. Phase 19 — Production Feature Parity

**Status: ✅ COMPLETE (Gate 13)**

The key question:

```text
Does the production feature pipeline generate the same feature semantics
that the historical model was trained on?
```

Verdict: **PASS** (Zero mismatches across all 331 features across 481 common TRAIN reference rows).

Scope & Evidence:
- Proves parity of the production feature pipeline using canonical broker-derived historical execution snapshots against non-holdout frozen TRAIN rows.
- Live MT5 feed ingestion and live runtime parity have not yet been proven by Gate 13 and belong to downstream integration.
- `04_Testing/evidence/production_portability/xauusd_portable_331_feature_provenance_map.json`
- `04_Testing/evidence/production_portability/xauusd_portable_331_production_parity_evidence.json`

Completed:

* [x] same feature count (331)
* [x] same ordered columns
* [x] same formulas & engine reproduction
* [x] same units
* [x] same timezone semantics (UTC)
* [x] same D1 semantics (00:00:00 UTC boundary)
* [x] finite values (fail-closed check on non-finite values)
* [x] deterministic replay
* [x] acceptable tolerances by feature family (max float numeric diff 5.0e-7, discrete 0.0)

---

# 26. Phase 20 — Frozen Model Inference Adapter

**Status: ✅ COMPLETE (Gate 14)**

Completed under Gate 14:

* [x] verify model artifact SHA at startup (`48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769`)
* [x] verify model class (`ExtraTreesClassifier`)
* [x] verify class order (`[-1, 0, 1]`)
* [x] verify feature count (331)
* [x] verify feature-column fingerprint (`65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2`)
* [x] reject non-finite inputs (NaN, +inf, -inf)
* [x] reject malformed/non-numeric inputs
* [x] call `predict_proba` read-only
* [x] use frozen argmax (`classes_[argmax(proba)]`)
* [x] no runtime threshold tuning or probability calibration
* [x] structured immutable inference result (`FrozenC04InferenceBatch`, `FrozenC04InferenceRow`)
* [x] zero trading runtime dependencies (`live_authorized=False, shadow_authorized=False`)
* [x] direct-model parity verified with zero probability or class mismatches

Evidence artifact:
- `04_Testing/evidence/production_portability/xauusd_frozen_c04_inference_adapter_evidence.json`

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

**Status: ⬜ PENDING / downstream of R03 forward evidence**

Shadow integration is not the current next action. The immediate active bottleneck is genuine R03 prospective evidence acquisition.

Before shadow/live promotion, the eventual integration must:

* [ ] connect the current frozen R03 inference artifact to the shadow decision path;
* [ ] preserve RiskEngine and `trade_ready` boundaries;
* [ ] preserve broker-aware sizing and account protection;
* [ ] log model probabilities, predicted class, feature identity, broker context, spread/cost context, and hypothetical trade state;
* [ ] keep all order routing and live execution disabled until explicitly authorized.

# 28. Phase 22 — R03 Forward Shadow Validation & Prospective Outcome Protocol

**Status: 🟡 ACTIVE COLLECTION / BLOCKED AT FIRST CAPTURE**

The G7-H R03 prospective lane is frozen and ready for genuine forward collection.

Frozen requirements:

```text
candidate = R03_FLAT_EXTRA_TREES_SMOOTH
artifact_sha256 = b5da550921ef227b847207cfbfe5774e86f083f1d3354069a9624a5029ea2a03
minimum_matured_outcomes = 60
minimum_distinct_observation_utc_dates = 5
horizon = 12 completed M5 rows
profit_atr = 1.25
max_adverse_atr = 0.75
```

Current collection state:

```text
observations = 0
anchors = 0
matured_outcomes = 0
distinct_matured_utc_dates = 0
```

The first genuine capture and R1 recovery were blocked by:

```text
TIMESTAMP_BASIS_NOT_UNIQUELY_PROVEN
raw_tick=1790985539
candidate_count=0
```

R2 recovery is also frozen; the block remains fail-closed. No prospective observation, anchor, or outcome is to be fabricated, reconstructed, or backfilled.

### Next authorized engineering action

Resolve the timestamp-basis proof or obtain a valid fresh capture context, then run the existing frozen capture lane.

Do not:

* weaken timestamp validation;
* rerun sealed TEST;
* tune R03 using prospective observations;
* use the old Forward30 for remediation development;
* rewrite protected runtime ledgers;
* enable live execution.

# 29. Phase 23 — Production Safety and Monitoring

**Status: ⬜ PENDING**

This phase begins only after the required forward evidence and review gates. It includes:

* [ ] model and feature SHA startup enforcement;
* [ ] symbol/timezone/stale-data validation;
* [ ] missing-bar and non-finite feature protection;
* [ ] inference exception handling;
* [ ] feature/prediction drift monitoring;
* [ ] spread/cost protection;
* [ ] operational audit logging;
* [ ] shadow/live separation;
* [ ] emergency kill switch;
* [ ] rollback/recovery procedure.

# 30. Phase 24 — Live Promotion Decision

**Status: ⛔ NOT AUTHORIZED**

Required evidence includes:

```text
[ ] R03 prospective forward evaluation acceptable
[ ] forward evidence frozen
[ ] production feature/runtime parity proven for the deployment broker context
[ ] shadow integration stable
[ ] costs and drawdown reviewed
[ ] RiskEngine/account protection verified
[ ] failure/recovery behavior tested
[ ] kill switch tested
[ ] explicit live promotion decision
```

Only after all required gates may:

```text
live_authorized = true
```

Current:

```text
live_authorized = false
execution_authorized = false
```

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

The current order is evidence-driven:

```text
1. Resolve R03 timestamp-basis proof / obtain valid fresh capture context
2. Execute frozen R03 genuine capture lane
3. Accumulate and mature ≥60 outcomes across ≥5 UTC observation dates
4. Perform prospective R03 evaluation
5. Freeze the forward result
6. Complete shadow/runtime integration review
7. Complete production safety, monitoring, recovery and kill-switch review
8. Perform controlled live-promotion review
```

Historical C04 TEST work and the G7 remediation TEST are already complete; do not reopen them for tuning.

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

<!-- V2-DATABASE-IMPORT-NORMALIZATION:START -->
## Relocation-Ready READY Set

Database test import normalization is complete.

The READY migration queue now contains:

- 18 tests ready for source-aligned relocation;
- 1 test requiring repository-root abstraction.

The 18 relocation-ready tests contain no test-file-depth repository bootstrap
dependency. `test_database.py` also no longer depends on a legacy `02_AI`
`sys.path` insertion.
<!-- V2-DATABASE-IMPORT-NORMALIZATION:END -->

<!-- V2-READY-18-RELOCATION:START -->
## READY Relocation Status

The coordinated 18-file source-aligned relocation is complete.

READY status is now:

- executed source-aligned migrations: 77;
- pending repository-root abstraction: 1.

Normal mechanical relocation is complete. The remaining READY file is
`test_v1_health.py`.
<!-- V2-READY-18-RELOCATION:END -->

<!-- V2-V1-ROOT-ABSTRACTION-RELOCATION:START -->
## V2 READY Phase Complete

All 78 READY migration rows are executed.

The final V1 health special case now uses stable repository-root fixture
injection, lives under `04_Testing/ai/config/`, and has its CI path updated.

Remaining V2 migration work is no longer normal READY movement; it consists of
the 77 REVIEW_REQUIRED decisions while FROZEN_STAY and SUPPORT_STAY remain
governed exceptions.
<!-- V2-V1-ROOT-ABSTRACTION-RELOCATION:END -->

<!-- V2-REVIEW-INTEGRATION-BATCH-01:START -->
## Review Phase Progress

READY migration remains complete at 78 executed rows.

The first review-execution batch has completed 2 integration-owned test
migrations, leaving 75 rows in REVIEW_REQUIRED.

The remaining review queue includes path-sensitive research tooling,
testing-module-string consumers, integration cases requiring bootstrap cleanup,
and self-target/no-relocation rows.
<!-- V2-REVIEW-INTEGRATION-BATCH-01:END -->

<!-- V2-REVIEW-DIAGNOSTICS-BATCH-01:START -->
## Review Phase Progress

Current migration state is 78 READY executed, 4 REVIEW_EXECUTED, and 73
REVIEW_REQUIRED.

The first diagnostic ownership correction removed two misleading root-level
`test_*.py` scripts and established explicit standalone diagnostic structure.

Remaining self-target review rows still contain executable-tool or pytest
technical debt and require independent review.
<!-- V2-REVIEW-DIAGNOSTICS-BATCH-01:END -->

<!-- V2-SELF-TARGET-DIRECT-SCRIPT-ROOT-NORMALIZATION:START -->
## Self-Target Pytest Debt Normalization

The first self-target pytest debt cleanup normalized
`test_exness_historical_fill_telemetry_direct_script.py` to the centralized
`repo_root` fixture.

Its migration state intentionally remains REVIEW_REQUIRED because final
placement should be decided together with the historical telemetry operation
that the test launches.
<!-- V2-SELF-TARGET-DIRECT-SCRIPT-ROOT-NORMALIZATION:END -->
