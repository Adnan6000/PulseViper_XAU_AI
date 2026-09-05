# PulseViper XAU AI — System Architecture

## 1. Purpose of This Document

This document explains how PulseViper XAU AI is structured from raw market data to machine-learning research, risk management, shadow operation, and eventual execution.

It is written for:

* new students;
* developers;
* ML researchers;
* maintainers;
* reviewers;
* future contributors.

You should read this document before modifying a major subsystem.

The most important architectural idea is:

> PulseViper is not one trading script. It is a collection of isolated systems connected through explicit contracts.

A simplified end-to-end view is:

```text
BROKER / MARKET DATA
        ↓
MARKET & FEATURE ENGINES
        ↓
PORTABLE FEATURE PROJECTION
        ↓
FROZEN 331-FEATURE CONTRACT
        ↓
DATASET + TARGET CONTRACT
        ↓
ML RESEARCH PIPELINE
        ↓
FROZEN MODEL ARTIFACT
        ↓
HOLDOUT VALIDATION / TEST
        ↓
PRODUCTION FEATURE PARITY
        ↓
MODEL INFERENCE
        ↓
TRADE PERMISSION / RISK
        ↓
SHADOW / EXECUTION
```

These layers should not be mixed casually.

---

# 2. Architectural Principles

PulseViper follows several design principles.

## 2.1 Separation of concerns

Each subsystem should solve one problem.

Examples:

```text
MarketStructureEngine
    → market structure

LiquidityEngine
    → liquidity behavior

Feature pipeline
    → model inputs

Candidate evaluator
    → research evaluation

RiskEngine
    → risk and sizing

Execution layer
    → order routing
```

A model evaluator should not place trades.

A RiskEngine should not select ML hyperparameters.

---

## 2.2 Reproducibility

Research artifacts are connected through fingerprints.

Conceptually:

```text
Dataset SHA
    ↓
Feature Contract SHA
    ↓
Research Protocol SHA
    ↓
Candidate Registry SHA
    ↓
Evaluation SHA
    ↓
Winner Config SHA
    ↓
Model Artifact SHA
    ↓
Validation Result SHA
```

This allows a future developer to prove exactly which model, dataset, feature order, and protocol produced a result.

---

## 2.3 Fail closed

If important identity cannot be verified:

```text
STOP
```

rather than:

```text
guess and continue
```

Examples:

* wrong model SHA;
* wrong number of features;
* wrong feature-column fingerprint;
* consumed holdout ledger;
* invalid artifact provenance;
* missing required class;
* non-finite feature values.

---

## 2.4 Research is separate from production

A historically successful model is not automatically safe to use in a live trading system.

Historical research answers:

> Does the model appear to generalize on historical holdout data?

Production validation answers:

> Can the same model receive the same feature semantics from a real broker and operate safely over future unseen conditions?

Those are separate questions.

---

# 3. High-Level Architecture

The complete architecture can be viewed as seven major layers.

```text
┌─────────────────────────────────────┐
│ 1. DATA / BROKER LAYER              │
└──────────────────┬──────────────────┘
                   ↓
┌─────────────────────────────────────┐
│ 2. MARKET ANALYSIS / FEATURE LAYER  │
└──────────────────┬──────────────────┘
                   ↓
┌─────────────────────────────────────┐
│ 3. PORTABILITY / DATASET LAYER      │
└──────────────────┬──────────────────┘
                   ↓
┌─────────────────────────────────────┐
│ 4. ML RESEARCH LAYER                │
└──────────────────┬──────────────────┘
                   ↓
┌─────────────────────────────────────┐
│ 5. MODEL ARTIFACT / INFERENCE       │
└──────────────────┬──────────────────┘
                   ↓
┌─────────────────────────────────────┐
│ 6. RISK / DECISION LAYER            │
└──────────────────┬──────────────────┘
                   ↓
┌─────────────────────────────────────┐
│ 7. SHADOW / EXECUTION LAYER         │
└─────────────────────────────────────┘
```

The current project has strong historical research coverage through Layer 4 and the frozen artifact portion of Layer 5.

Production inference, broker parity, and forward shadow validation remain future engineering gates.

---

# 4. Layer 1 — Broker and Market Data

## Responsibility

The data layer obtains and stores market information required by the rest of the system.

Typical market information includes:

```text
timestamp
open
high
low
close
volume / tick volume
spread information
symbol information
broker metadata
```

The system is primarily focused on:

```text
XAUUSD
XAUUSDm
```

and potentially broker-specific symbol variants.

---

## Why broker identity matters

Two brokers may expose gold differently.

Examples:

```text
Broker A:
XAUUSD

Broker B:
XAUUSDm
```

Other differences may include:

* spread behavior;
* server timezone;
* D1 candle boundary;
* historical bar availability;
* missing candles;
* symbol digits;
* trading session conventions.

Therefore raw broker data must not automatically be assumed to produce identical ML features.

---

# 5. Layer 2 — Market Analysis and Feature Engines

The original PulseViper architecture contains modular analysis engines under the AI/core system.

Important conceptual modules include:

```text
market_structure.py
liquidity_engine.py
pattern_engine.py
institutional_zones.py
market_regime.py
feature_generator.py
confidence_engine.py
risk_engine.py
```

These modules should remain logically isolated.

---

# 6. Market Structure Engine

Typical responsibility:

```text
Raw OHLC data
       ↓
Swing High / Low
       ↓
BOS / CHoCH
       ↓
Trend / structural state
```

Example conceptual input:

```text
timestamp | open | high | low | close
```

Example conceptual output:

```text
swing_high = True
bos = False
choch = True
trend = bearish
```

A structure engine should not be responsible for:

* model fitting;
* order sizing;
* TEST evaluation.

---

# 7. Liquidity Engine

The liquidity system analyzes concepts such as:

```text
EQH
EQL
buy-side liquidity
sell-side liquidity
liquidity sweeps
inducement
```

Conceptually:

```text
Market Data
     +
Structure Context
        ↓
Liquidity Engine
        ↓
Liquidity Features
```

Example:

```text
previous_equal_high = 2345.20
current_high = 2345.50
close_back_below = True

possible_buy_side_sweep = True
```

---

# 8. Pattern Engine

The pattern layer detects price behavior such as:

```text
compression
expansion
breakouts
failed breakouts
range behavior
```

Conceptual example:

```text
Recent ATR falling
Range width contracting
Multiple small candles
        ↓
compression_state = True
```

Again, these are feature-generation concepts, not direct permission to place a trade.

---

# 9. Institutional Zone Logic

Institutional-zone analysis may include:

```text
Order Blocks
Fair Value Gaps
Imbalances
Supply / Demand style zones
```

The architectural rule is:

```text
Zone detection
        ↓
Feature / context

NOT

Zone detected
        ↓
immediately place order
```

Trade execution still belongs to later safety layers.

---

# 10. Market Regime Layer

The market regime layer describes broader market state.

Possible regime concepts include:

```text
trending
ranging
high volatility
low volatility
expansion
compression
```

Example:

```text
ATR increasing
Directional persistence increasing
Breakout structure confirmed
        ↓
regime = trending_expansion
```

Regime context can influence features and trading permissions.

---

# 11. Feature Generation Layer

The feature generator combines outputs from multiple engines into model-consumable values.

Conceptually:

```text
Market Structure ─────┐
Liquidity ────────────┤
Patterns ─────────────┤
Institutional Zones ──┤
Market Regime ────────┼──→ Feature Generator
MTF Context ──────────┤
Session Context ──────┘
```

The output is not yet automatically safe for the current frozen ML model.

It must first pass the portability contract.

---

# 12. Layer 3 — Portable Feature Projection

The current ML experiment uses a broker-portable feature contract.

Frozen feature count:

```text
331
```

Frozen ordered feature-list fingerprint:

```text
65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2
```

The portability layer exists because not every historical feature is guaranteed to mean the same thing on every broker.

---

# 13. Why Feature Order Is Part of Architecture

Suppose training used:

```text
index 0 = H1_ATR
index 1 = H4_range
index 2 = D1_structure
```

but production sends:

```text
index 0 = D1_structure
index 1 = H1_ATR
index 2 = H4_range
```

Both have:

```text
3 columns
```

but the model receives incorrect semantics.

Therefore model input validation must verify:

```text
feature_count
+
feature order
+
feature fingerprint
```

not just array shape.

---

# 14. Production Portability Architecture

The desired production feature path is:

```text
NEW BROKER
    ↓
Symbol Normalization
    ↓
Time Canonicalization
    ↓
Canonical MTF Bars
    ↓
Canonical D1 Reconstruction
    ↓
Feature Generation
    ↓
Portable Projection
    ↓
Exact 331 Ordered Features
    ↓
Fingerprint / Schema Validation
```

This stage is not fully finished yet.

It is one of the main remaining production engineering blocks.

---

# 15. Dataset Layer

Current frozen portable TRAIN dataset:

```text
Dataset ID:
portable_cff75b0686383a3ab6f8352b

Rows:
69,966

Feature count:
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

# 16. Portable Training Input Loader

Important module:

```text
02_AI/Dataset/portable_331_training_input_loader.py
```

Its responsibilities include:

```text
artifact discovery
manifest validation
split validation
feature-order validation
numeric feature conversion
target normalization
TRAIN supervised-batch construction
```

Conceptually:

```text
Frozen Dataset
      +
Manifest
        ↓
Portable331TrainingInputLoader
        ↓
Validated TRAIN Batch
```

---

# 17. Loader Holdout Boundary

During TRAIN research, public methods for:

```text
load_validation_features
load_validation_targets
load_test_features
load_test_targets
```

were deliberately fail-closed.

This prevented accidental holdout access while candidate research was still active.

Later validation access was implemented through a dedicated one-time bounded source rather than silently changing the frozen research loader.

This architectural separation is intentional.

---

# 18. Target Layer

Current model uses three classes:

```text
-1 = SHORT
 0 = NO_TRADE
 1 = LONG
```

Tradeability relationship:

```python
target_tradeable = (target_class != 0).astype("int8")
```

Therefore:

```text
SHORT → tradeable
NO_TRADE → not tradeable
LONG → tradeable
```

A mismatch means target corruption.

---

# 19. Frozen Target Semantics

Directional-excursion contract:

```text
profit_atr = 1.25
max_adverse_atr = 0.75
```

Conceptually:

```text
future favorable excursion
        +
maximum allowed adverse excursion
            ↓
SHORT / NO_TRADE / LONG
```

Changing these values changes the meaning of the target and requires a new experiment lineage.

---

# 20. Layer 4 — ML Research Architecture

The model research system follows this sequence:

```text
Frozen TRAIN Dataset
        ↓
Research Protocol
        ↓
Frozen Candidate Registry
        ↓
Purged Walk-Forward Evaluation
        ↓
Frozen Winner
        ↓
Full TRAIN Fit
        ↓
Artifact Verification
```

VALIDATION and TEST are not used for candidate selection.

---

# 21. Research Protocol

Current protocol:

```text
TRAIN only
4 expanding chronological folds
12-row purge
no shuffle
no TEST
no VALIDATION
```

Conceptually:

```text
TRAIN history ─────────────────────────→ time

Fold 1:
[TRAIN]
       [PURGE]
              [EVAL]

Fold 2:
[      TRAIN      ]
                    [PURGE]
                           [EVAL]

Fold 3:
[          TRAIN           ]
                            [PURGE]
                                   [EVAL]
```

This architecture reduces temporal leakage.

---

# 22. Candidate Registry

Six candidates were frozen before real model results were available.

This layer exists to prevent adaptive model hunting.

Conceptual rule:

```text
CANDIDATES FROZEN
        ↓
RESULTS OBSERVED
```

not:

```text
RESULTS OBSERVED
        ↓
NEW CANDIDATES INVENTED
        ↓
MORE RESULTS OBSERVED
```

---

# 23. Candidate Evaluation Layer

Important evaluator:

```text
04_Testing/evaluate_xauusd_portable_331_train_model_candidates.py
```

It evaluates the candidate registry using the frozen research protocol.

The evaluator calculates 15 required fold metrics.

Important groups:

```text
3-class classification
directional performance
per-class performance
probability quality
trade coverage
```

---

# 24. Winner Selection

Frozen TRAIN-internal winner:

```text
C04_FLAT_EXTRA_TREES_CONSTRAINED
```

The primary selection rule emphasized:

```text
worst-fold directional macro-F1
```

This was designed to prefer directional robustness rather than a single strong period.

---

# 25. Full TRAIN Fit

After candidate selection, the winner was fitted once on all frozen TRAIN rows.

```text
69,966 rows
331 features
```

Frozen model configuration:

```text
ExtraTreesClassifier
n_estimators = 500
max_depth = 10
max_features = 0.35
min_samples_leaf = 25
class_weight = balanced
random_state = 271828
```

---

# 26. Layer 5 — Frozen Model Artifact

Artifact:

```text
xauusd_portable_331_c04_full_train_model.joblib
```

SHA256:

```text
48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769
```

Model class order:

```text
[-1, 0, 1]
```

Meaning:

```text
SHORT
NO_TRADE
LONG
```

---

# 27. Model Artifact Verification

The model is not trusted only because a `.joblib` file exists.

Verification checks include:

```text
artifact SHA
model class
feature count
class order
number of trees
hyperparameters
parent research fingerprints
```

Conceptual architecture:

```text
Frozen model file
      +
Research evidence
        ↓
Artifact Verifier
        ↓
Verified inference artifact
```

---

# 28. Prediction Architecture

Frozen prediction rule:

```python
probabilities = model.predict_proba(X)
prediction = model.classes_[
    probabilities.argmax(axis=1)
]
```

There is currently:

```text
no probability calibration
no threshold tuning
no post-hoc class bias
```

for the frozen experiment.

---

# 29. Protected Holdout Architecture

After the frozen model exists:

```text
Frozen Model
    ↓
Frozen VALIDATION Protocol
    ↓
Dry Preflight
    ↓
One-Time Ledger
    ↓
Bounded VALIDATION Read
    ↓
Metrics
    ↓
Acceptance Gate
    ↓
Frozen Result
```

This is deliberately more complex than:

```text
pd.read_csv(...)
model.predict(...)
```

because the system must prove that scientific holdout rules were respected.

---

# 30. One-Time Access Ledger

The ledger controls protected holdout consumption.

Typical lifecycle:

```text
ABSENT
    ↓
RESERVED_BEFORE_READ
    ↓
READ_INITIATED_CONSUMED_BOUNDARY
    ↓
VALUES_LOADED
    ↓
METRICS_COMPUTED
    ↓
COMPLETE
```

Important distinction:

```text
technical failure before protected values
        ≠
technical failure after protected values
```

After the read boundary, the holdout is considered consumed.

---

# 31. Bounded Validation Source

Important module:

```text
04_Testing/xauusd_portable_331_authorized_validation_source.py
```

Instead of changing the original fail-closed loader API, this adapter:

```text
verifies loader source
verifies manifest
reads split structure
locates contiguous VALIDATION block
loads only the VALIDATION value block
stops before TEST rows
reuses frozen loader normalization
```

This protects the TEST boundary.

---

# 32. Current VALIDATION State

Current result:

```text
ONE_TIME_VALIDATION_ACCEPTED
```

Important metrics:

```text
Balanced accuracy:
0.37656763760203776

Macro-F1:
0.34890395261998247

Directional macro-F1:
0.33640257616029445

SHORT recall:
0.3190499510284035

LONG recall:
0.529248683116163

Trade coverage:
0.7541213375158513
```

Validation is now:

```text
accepted
consumed
frozen
not rerunnable for performance tuning
```

Freeze fingerprint:

```text
521a97b41a86231b049cc65aebfd85ffc7c83ae7141134d6ae1158d112b1468c
```

---

# 33. Final TEST Architecture

The next research stage is:

```text
Frozen VALIDATION Result
        ↓
One-Shot TEST Runner
        ↓
Dry Preflight
        ↓
TEST Ledger
        ↓
First and Only TEST Read
        ↓
Final Metrics
        ↓
Research Verdict
```

TEST must not feed back into model development.

---

# 34. Layer 6 — Decision and Risk Architecture

Historical model output alone is not an order.

Conceptually:

```text
Model Prediction
        ↓
Trade Permission
        ↓
Market / Execution Checks
        ↓
RiskEngine
        ↓
Position Sizing
        ↓
Order Candidate
```

This keeps research predictions separate from operational safety.

---

# 35. Confidence and Permission Stage

The original architecture includes confidence and permission concepts.

Typical checks may include:

```text
spread
market conditions
regime
structural alignment
confidence
trading mode
```

A future ML integration must plug into existing rules rather than silently replacing them.

---

# 36. Three-Stage Execution Concept

The existing project architecture describes a three-stage execution pipeline.

## Stage 1 — Permission

Examples:

```text
spread acceptable?
market tradable?
macro restrictions?
regime allowed?
```

## Stage 2 — Timing / Direction

Examples:

```text
signal direction
structure alignment
confidence checks
```

## Stage 3 — Execution

Examples:

```text
position size
SL / TP
order routing
trade lifecycle
```

ML research should not bypass these stages.

---

# 37. RiskEngine Boundary

The RiskEngine is a protected subsystem.

Responsibilities may include:

```text
risk percentage
position sizing
account protection
exposure limits
SL / TP related risk
```

ML code should provide a signal or probability result.

It should not directly determine unsafe lot size.

---

# 38. Layer 7 — Shadow and Execution

Shadow mode exists between:

```text
historical research
```

and:

```text
live trading
```

Desired shadow architecture:

```text
Live Broker Data
       ↓
Portable Features
       ↓
Frozen Model
       ↓
Prediction
       ↓
Existing Safety / Risk Logic
       ↓
Hypothetical Trade
       ↓
Shadow Log
```

No real order is required for research.

---

# 39. Why Shadow Is Necessary

Historical TEST cannot reproduce all operational conditions.

Shadow testing exposes the system to:

```text
real spreads
live timestamps
broker outages
missing candles
session transitions
future market regimes
feature drift
prediction drift
```

without risking capital.

---

# 40. Future Forward Validation Layer

After shadow integration, future unseen market data should be accumulated.

Measure:

```text
prediction stability
SHORT/LONG balance
trade coverage
feature drift
spread sensitivity
slippage assumptions
drawdown
expectancy
market-regime stability
```

Only after this stage should live promotion even be considered.

---

# 41. Current Authorization Matrix

Current architectural authorization:

| Capability                 | State               |
| -------------------------- | ------------------- |
| TRAIN research             | Complete            |
| TRAIN model fit            | Complete            |
| VALIDATION                 | Passed and consumed |
| VALIDATION rerun           | Not authorized      |
| Final TEST                 | Not yet consumed    |
| TEST runner implementation | Authorized next     |
| Shadow inference           | Not authorized yet  |
| Live trading               | Not authorized      |

---

# 42. Architectural Change Classification

Before modifying code, classify the change.

## Type A — Documentation only

Example:

```text
fix explanation
add diagram
```

Usually low risk.

---

## Type B — Research utility

Example:

```text
new report generator
new non-decision diagnostic
```

Requires focused tests.

---

## Type C — Feature semantics

Example:

```text
change D1 feature calculation
```

May invalidate feature contract.

---

## Type D — Target semantics

Example:

```text
change profit_atr
```

Requires new target/dataset lineage.

---

## Type E — Model decision policy

Example:

```text
new probability threshold
```

Creates a new experiment.

---

## Type F — Runtime / Risk / Execution

Example:

```text
change lot sizing
change order routing
```

High-risk protected area.

---

# 43. Student Example — Trace One Prediction

A useful exercise for a new student is to trace one prediction conceptually.

```text
1. Obtain one canonical XAUUSD observation.

2. Generate required MTF context.

3. Produce portable features.

4. Order exactly 331 features.

5. Verify feature fingerprint.

6. Build X shape:
   (1, 331)

7. Run:
   model.predict_proba(X)

8. Example result:
   SHORT     0.28
   NO_TRADE  0.31
   LONG      0.41

9. Argmax:
   LONG

10. Prediction is then passed to the
    trading safety/risk architecture.

11. Prediction alone does not place an order.
```

---

# 44. Student Example — Detect an Invalid Model Input

Suppose:

```python
X.shape == (100, 331)
```

This alone does not prove validity.

Check:

```text
Are columns in exact frozen order?
Are all values finite?
Was the correct broker-time logic used?
Was D1 reconstructed correctly?
Does feature_columns_sha256 match?
```

If not:

```text
FAIL CLOSED
```

---

# 45. Student Example — New Model Research

Suppose a student wants to try XGBoost.

Do not replace C04 directly.

Correct architecture:

```text
New research question
      ↓
New candidate registry / protocol
      ↓
TRAIN-only research
      ↓
Frozen winner
      ↓
New untouched holdout policy
```

The existing C04 lineage remains historical evidence.

---

# 46. Student Example — New Broker

Suppose training data came from one broker and deployment uses another.

Do not immediately run the model.

First:

```text
compare symbol metadata
compare timestamps
compare session boundaries
reconstruct D1 if required
generate same features
compare feature semantics
verify 331 order
```

Only then integrate the frozen model.

---

# 47. Architecture Development Rule

Before changing any subsystem, answer:

```text
Which layer owns this behavior?

What contract protects it?

What upstream assumptions does it use?

What downstream modules depend on it?

Will an existing fingerprint become invalid?

Does this touch protected holdout data?

Does this touch runtime execution?
```

If these questions cannot be answered, more architecture review is required before coding.

---

# 48. Current Architectural Milestone

The current research architecture has reached:

```text
TRAIN
  ✅
Walk-Forward
  ✅
Winner
  ✅
Full TRAIN Fit
  ✅
Artifact Verification
  ✅
Untouched VALIDATION
  ✅ PASS
Validation Freeze
  ✅
Final TEST
  ⏳ NEXT
```

Production architecture still needs:

```text
broker portability
D1 canonicalization
production feature generation
verified inference adapter
shadow integration
forward validation
production safety review
```

---

# 49. Golden Architecture Rule

The most important design rule is:

> Every layer should expose a clear contract and should not silently take over responsibilities belonging to another layer.

Examples:

```text
Feature generator
    should not place orders.

Model evaluator
    should not tune using TEST.

Model predictor
    should not choose lot size.

RiskEngine
    should not retrain models.

Execution layer
    should not reorder model features.
```

This separation keeps PulseViper understandable, testable, and safer to evolve.

<!-- REPOSITORY-ARCHITECTURE-MANAGED:START -->
## Repository Structure Governance

> Managed repository-architecture section.

### Canonical top-level structure

The repository uses the numbered project layout as the architectural source of
truth:

- `01_Data/` — canonical data layer.
- `02_AI/` — production Python system.
- `03_MT5/` — MT5 integration area.
- `04_Testing/` — testing, diagnostics, research tooling, and testing evidence.
- `05_Documentation/` — documentation and engineering governance.
- `06_Exports/` — generated exports.
- `07_Git/` — reserved Git-support area.
- `Logs/` — generated runtime logs.

No new top-level directory may be introduced when an existing canonical
numbered directory already owns the same responsibility.

The duplicate empty `Data/` directory was removed. `01_Data/` remains the
canonical data location.

### `02_AI` source domains

The current production Python source architecture contains these twelve
domains:

- `Adapters`
- `Common`
- `Config`
- `Core`
- `Database`
- `Dataset`
- `Features`
- `Memory`
- `Models`
- `Objects`
- `Shadow`
- `Utils`

Testing organization should reflect real source ownership where that ownership
can be established reliably. Cross-domain tests should be treated as
integration tests rather than being forced into an arbitrary subsystem.

### `04_Testing` structure

Currently established structured areas:

- `04_Testing/evidence/`
- `04_Testing/evidence/production_portability/`
- `04_Testing/evidence/research/`
- `04_Testing/production_portability/`

A future V2 migration may introduce source-aligned test and research
subdirectories only after ownership, CI paths, imports, dynamic loaders,
repository-root semantics, and frozen compatibility constraints are verified.

The earlier migration manifest is historical planning evidence and is not
authority for future file movement after the architecture audit.

### Frozen compatibility boundary

One-time VALIDATION and TEST code/evidence remain at their frozen compatibility
paths when relocation would alter their established path contract.

VALIDATION and TEST must not be rerun as part of structure cleanup.

### Path-resolution technical debt

The architecture audit found widespread repository-depth coupling and
`sys.path` mutation. Further large-scale relocation must not increase this
technical debt.

A stable repository-root/path bootstrap mechanism should be designed and
verified before broad migration of depth-sensitive scripts. Existing frozen
holdout logic is excluded from such refactoring unless explicitly authorized.
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
