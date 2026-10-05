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

## 1.1 Current Live-Deployment Objective

PulseViper is architected for eventual **controlled real-money live XAUUSD trading**. Research, protected holdouts, shadow operation, broker calibration, demo validation, forward evidence, and operational safety are gates in the path to live deployment—not the final purpose of the system.

Current authorization remains fail-closed:

```text
live_authorized = false
execution_authorized = false
```

The current remediation lineage is now the **R03 remediation winner**. The historical C04 model remains preserved as a control/baseline lineage and is not silently replaced. G7-F-C froze `R03_FLAT_EXTRA_TREES_SMOOTH`, G7-G-B completed its one-shot sealed TEST, and G7-H froze the new R03 prospective validation contract and runtime collection infrastructure.

The current R03 prospective lane has **not yet produced a genuine persisted observation**. The first capture and two recovery attempts were blocked because the broker timestamp basis could not be uniquely proven. The latest recovery runner is frozen; this is an evidence-preserving block, not permission to weaken timestamp checks.

Current authorization remains fail-closed and no performance/PnL verdict is active:

```text
live_authorized = false
execution_authorized = false
performance_evaluated = false
pnl_evaluated = false
```

## 1.2 Broker-Agnostic Multi-Broker Architecture

No permanent broker has been selected for PulseViper.

The canonical research identity is:

```text
XAUUSD
```

A broker may expose gold under a broker-specific symbol such as:

```text
XAUUSD
XAUUSDm
XAUUSDb
```

These are **broker calibration/adapter contexts**, not separate model identities and not permanent broker selection.

The architecture therefore separates:

```text
Broker discovery
      ↓
Dynamic symbol resolution
      ↓
Broker instrument context
      ↓
Canonical XAUUSD market representation
      ↓
Portable feature contract
      ↓
Model / research logic
```

Broker-specific metadata such as digits, point size, tick value, contract size, spread, session/time semantics, filling rules, and other constraints must be discovered and validated at the broker boundary. Core research and model contracts must not hard-code a single broker symbol.

The project is intended to become compatible with many brokers/accounts; individual brokers used during calibration are evidence sources, not a final broker choice.

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

Gate 13 (production broker feature generation on canonical snapshots), Gate 14 (frozen offline inference adapter), Gate 15A (forward shadow observation infrastructure), Gate 15B-A (read-only forward acquisition authority v2.1.0), Gate 15C (frozen forward outcome contract V1), Gate 15D-A (prospective eligibility authority), Gate 15D-C-B2A (prospective outcome anchor authority V1), Gate 15D-C-B2B (anchor-required outcome maturer V2), and Gate 15D-C-B2C (outcome ledger V2) are complete. Gate 15D-C-B2D (Genuine Prospective Observation + Same-Snapshot Anchor Integration) is currently in progress, with G1 capture and G2 maturation evidence active and G3 controller frozen. Read-only acquisition does NOT authorize live trading or execution (`live_authorized = false`, `execution_authorized = false`).

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

The system uses a canonical research identity:

```text
XAUUSD
```

and is designed for broker-agnostic multi-broker deployment. Broker-specific Gold symbols are resolved dynamically at the broker/instrument-context boundary.

Examples:

```text
XAUUSD
XAUUSDm
XAUUSDb
```

are broker-specific symbol contexts, not permanent broker selections.

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

Gate 13 production feature generation is broker-agnostic at the instrument boundary:

```text
broker discovery
    ↓
dynamic symbol resolution
    ↓
validated broker instrument context
    ↓
canonical XAUUSD identity
    ↓
331-feature portable contract
```

Broker-specific symbols such as `XAUUSD`, `XAUUSDm`, and `XAUUSDb` are calibration/adapter contexts, not permanent broker choices. The core model and research contracts must not hard-code a single broker symbol.

Gate 13 parity proved historical canonical broker-derived snapshots against the frozen feature contract. Live broker feed parity remains a downstream operational integration concern.

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
04_Testing/research/portable_331/train/evaluate_xauusd_portable_331_train_model_candidates.py
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

# 28. Prediction Architecture & Offline Inference Adapter

Under Gate 14, offline model inference is encapsulated by:

```text
02_AI/Models/frozen_c04_inference_adapter.py
```

`FrozenC04InferenceAdapter` provides production-quality, fail-closed offline inference wrapping `xauusd_portable_331_c04_full_train_model.joblib`:
- Enforces model SHA256 (`48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769`), class (`ExtraTreesClassifier`), `n_features_in_ == 331`, and `classes_ == [-1, 0, 1]`.
- Enforces exact Gate 13 331-feature schema validation and rejects non-finite/malformed matrices.
- Maps output probabilities strictly according to `classes_` (`col 0 -> SHORT (-1)`, `col 1 -> NO_TRADE (0)`, `col 2 -> LONG (1)`).
- Frozen prediction rule:
```python
probabilities = model.predict_proba(X)
prediction = model.classes_[
    probabilities.argmax(axis=1)
]
```
- There is currently no probability calibration, no threshold tuning, and no post-hoc class bias.
- Pure ML inference: `live_authorized = False, shadow_authorized = False`, with zero trading runtime dependencies.

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

The architecture is currently centered on the frozen R03 remediation lineage, while historical C04 remains preserved as the control lineage.

```text
Historical C04 forward baseline
        ↓
G7 remediation protocol + six-candidate registry
        ↓
G7-F-B evaluation
        ↓
R03 winner freeze
        ↓
R03 sealed TEST confirmation
        ↓
R03 train-only artifact + prospective runtime
        ↓
CURRENT: R03 first genuine forward capture blocked
```

Current R03 authority:

```text
candidate = R03_FLAT_EXTRA_TREES_SMOOTH
artifact_sha256 = b5da550921ef227b847207cfbfe5774e86f083f1d3354069a9624a5029ea2a03
feature_count = 331
train_rows = 69966
minimum_matured_outcomes = 60
minimum_distinct_utc_dates = 5
```

The first genuine capture and recovery attempts are blocked by `TIMESTAMP_BASIS_NOT_UNIQUELY_PROVEN` for `raw_tick=1790985539` with `candidate_count=0`. This is a fail-closed evidence condition.

Production/live architecture remains unauthorized:

```text
live_authorized = false
execution_authorized = false
performance_evaluated = false
pnl_evaluated = false
```

Gate 13/14 production feature parity and frozen C04 inference work remain valid historical/compatibility infrastructure. The active forward lane is R03 and must not be confused with the historical C04 model.

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

- `04_Testing/ai/common/`
- `04_Testing/ai/config/`
- `04_Testing/ai/core/`
- `04_Testing/ai/database/`
- `04_Testing/ai/dataset/`
- `04_Testing/ai/objects/`
- `04_Testing/ai/shadow/`
- `04_Testing/integration/`
- `04_Testing/diagnostics/`
- `04_Testing/production_portability/`
- `04_Testing/research/portable_331/train/`
- `04_Testing/research/legacy_ml/`
- `04_Testing/research/shadow_experiments/`
- `04_Testing/research/legacy_validation/`
- `04_Testing/evidence/`
- `04_Testing/evidence/production_portability/`
- `04_Testing/evidence/research/`

All 78 READY files and 77 REVIEW files have been migrated to their source-aligned and research/diagnostic targets. Exactly 19 files remain at the `04_Testing/` root: 18 frozen validation/holdout files and `conftest.py`.

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

<!-- V2-CORE-SAFE-A-MIGRATION:START -->
## V2 Core Test Layout

The first Architecture V2 execution batch established
`04_Testing/ai/core/`.

Eighteen HIGH-confidence, location-independent Core tests were relocated from
the loose `04_Testing/` root into this source-aligned directory.

Location-sensitive READY tests were deliberately excluded from the batch.
Their existing paths remain unchanged until repository-root and file-location
semantics are handled explicitly.

The Core migration also updated all affected CI test paths in the same
engineering gate.
<!-- V2-CORE-SAFE-A-MIGRATION:END -->

<!-- V2-SHADOW-SAFE-A-MIGRATION:START -->
## V2 Shadow Test Layout

The second Architecture V2 execution batch established
`04_Testing/ai/shadow/` for tests owned by `02_AI/Shadow`.

Thirty-five HIGH-confidence Shadow tests were relocated from the loose testing
root.

The initial focused post-move run exposed one hidden test-to-test dynamic
import. A moved test still referenced another moved test by its former dotted
Python module name.

That reference was changed from
`04_Testing.test_realized_fill_telemetry_bridge` to
`04_Testing.ai.shadow.test_realized_fill_telemetry_bridge`.

After the structural import repair, all 662 focused Shadow tests passed.

This refines the repository migration safety model: dotted module strings used
by `importlib` are location dependencies even when no `.py` filename or
`__file__` expression is present.
<!-- V2-SHADOW-SAFE-A-MIGRATION:END -->

<!-- V2-FINAL-LOCATION-INDEPENDENT-BATCH:START -->
## Final Location-Independent V2 Batch

The remaining six location-independent READY tests were migrated into
source-aligned Common, Dataset, and Objects test directories.

The source-aligned V2 layout now contains 59 tests:

- Common: 1
- Core: 18
- Dataset: 4
- Objects: 1
- Shadow: 35

Nineteen READY tests remain at the loose testing root because their file
location participates in repository-root or import-bootstrap behavior.

Those files require a dedicated path-bootstrap refactor and must not be moved
mechanically.
<!-- V2-FINAL-LOCATION-INDEPENDENT-BATCH:END -->

<!-- V2-PYTEST-BOOTSTRAP-CONSOLIDATION:START -->
## Centralized Pytest Repository Bootstrap

`04_Testing/conftest.py` is the single pytest repository-root path bootstrap
authority for 17 relocation-ready tests.

Those tests previously derived repository root from their own `__file__`
depth and independently mutated `sys.path`. That duplication has been removed
before relocation.

Focused project-environment verification passed 41 tests.

Verification also exposed two legacy Dataset tests whose calls predated the
mandatory InstrumentContext materialization contract. Those tests were aligned
to the current production contract using deterministic temporary-output
fixtures; production Dataset behavior was not weakened or changed.

Two READY special cases remain outside this consolidation:

- `test_database.py` requires legacy import normalization;
- `test_v1_health.py` genuinely consumes repository-root filesystem paths.
<!-- V2-PYTEST-BOOTSTRAP-CONSOLIDATION:END -->

<!-- V2-DATABASE-IMPORT-NORMALIZATION:START -->
## Database Test Import Normalization

`04_Testing/test_database.py` no longer adds the `02_AI` directory directly to
`sys.path`.

Its former `Database.database` import depended on that extra path entry. The
test now resolves the canonical repository-visible module identity
`02_AI.Database.database` through `importlib`.

This removes the final import-path exception among the 18 relocation-ready
READY tests. Those files can now move without parent-depth or local `sys.path`
adjustments.
<!-- V2-DATABASE-IMPORT-NORMALIZATION:END -->

<!-- V2-READY-18-RELOCATION:START -->
## READY Test Relocation Completion

Eighteen previously loose READY tests now live in source-aligned
`04_Testing/ai/<domain>/` ownership.

The corrected post-move reference audit found zero true external old-path or
old-dotted-module consumers.

The first scanner pass had incorrectly treated a moved file's own new target
as an external consumer. The recovery logic now excludes both sides of the
same logical relocation.

The source-aligned READY population is 77 tests. `test_v1_health.py` remains
the only READY root-sensitive exception.
<!-- V2-READY-18-RELOCATION:END -->

<!-- V2-V1-ROOT-ABSTRACTION-RELOCATION:START -->
## Stable Pytest Repository Root

`04_Testing/conftest.py` owns both repository import visibility and the
session-scoped `repo_root` fixture.

Repository root is discovered by walking upward until the expected
`pyproject.toml`, `02_AI`, `04_Testing`, and `05_Documentation` markers are
present.

This removes the central pytest bootstrap's dependency on
`Path(__file__).parents[n]` and allows root-consuming tests to move without
changing parent-depth arithmetic.

All 78 V2 READY tests are now source-aligned.
<!-- V2-V1-ROOT-ABSTRACTION-RELOCATION:END -->

<!-- V2-REVIEW-INTEGRATION-BATCH-01:START -->
## Integration Test Ownership

Cross-domain tests with no single production-domain owner may live under
`04_Testing/integration/` when review proves that integration ownership is
stronger than an `ai/<domain>` assignment.

The first reviewed integration batch contains the instrument frame guard
contract test and hierarchical model V4 trainer test.

Both were free of file-depth bootstrap, local `sys.path` mutation, external
path/module consumers, and CI path coupling before relocation.
<!-- V2-REVIEW-INTEGRATION-BATCH-01:END -->

<!-- V2-REVIEW-DIAGNOSTICS-BATCH-01:START -->
## Diagnostic Ownership

Standalone verification and diagnostic scripts belong under
`04_Testing/diagnostics/`, not at repository root and not in pytest
source-aligned test domains.

The diagnostic bootstrap discovers repository root using stable markers and
adds it to `sys.path` only when a diagnostic entrypoint is explicitly run.

Pytest bootstrap remains owned by `04_Testing/conftest.py`; standalone
diagnostics do not import or depend on conftest.
<!-- V2-REVIEW-DIAGNOSTICS-BATCH-01:END -->

---

# 43. Forward Shadow Observation Architecture (Gate 15A)

Under Gate 15A, the forward shadow observation infrastructure is established by:

```text
02_AI/Models/frozen_c04_shadow_observer.py
```

### Purpose & Safe Read-Only Pipeline
Gate 15A establishes the production-safe observation infrastructure required for future unseen-regime forward shadow validation:
```
broker-derived market snapshot
  → Gate 13 PortableFeaturePipeline
  → validated frozen 331 matrix
  → Gate 14 FrozenC04InferenceAdapter
  → READ-ONLY shadow observation record
```

### Key Architectural Principles
1. **Module Ownership & Trading Isolation**:
   The observer lives in `02_AI/Models/`, next to `frozen_c04_inference_adapter.py`. It is completely isolated from `02_AI/Shadow/`'s 36 files of order routing, risk scenarios, compounding accounting, and execution lifecycles.
2. **Immutable Observation Record (`FrozenC04ObservationRecord`)**:
   Frozen dataclass capturing:
   - `logical_observation_id = SHA256(schema:instrument:decision_time:feature_sha:model_sha)`
   - `semantic_record_fingerprint = SHA256(canonical JSON excluding observed_at_utc)`
   - Exact frozen model SHA256, feature columns SHA256, probabilities, class predictions, and source snapshot fingerprint.
   - `live_authorized = False`, `execution_authorized = False`.
3. **Locked Durable Append Ledger (`FrozenC04ObservationLedger`)**:
   - Stores records in JSON Lines (`.jsonl`).
   - Uses file locking (`msvcrt` on Windows, `fcntl` on POSIX) with byte-0 seek alignment.
   - Flushes and fsyncs on each append.
   - Fail-closed deduplication: identical records are idempotent duplicates; conflicting records raise `ConflictingObservationError`.
   - Corruption detection: validates every line on load; partial/truncated/corrupt writes raise `CorruptedLedgerError`.
   - Operational runtime ledger resides in `01_Data/Shadow/` (git-ignored); test evidence resides in `04_Testing/evidence/forward_shadow/`.
4. **Machine-Readable Frozen Boundary Authority**:
   - Proven maximum historical source timestamp: `2026-08-14T20:55:00Z`.
   - Source: `01_Data/Canonical/Instruments/XAUUSD/learning/scope_c8705b79f4cb595c4a2dec477d76a64956ae63133a2f91426f1647a3c5f5cfef/training/XAUUSD_MTF_TRAINING_V3/portable_v1/pv_portable_xauusd_cff75b0686383a3ab6f8352b.manifest.json` (`source_historical_snapshots.M5.end_time`).
   - Activation authority: `2026-09-06T13:20:00Z` (persisted frozen timestamp).
5. **Outcome Horizon Contract Status**:
   - Strictly marked `BLOCKED_NOT_PREDEFINED`. No forward outcome horizons or directional excursion evaluation rules are fabricated post-hoc.
6. **Provenance-Based Eligibility**:
   - Sources classified as `HISTORICAL_ENGINEERING`, `SYNTHETIC_ENGINEERING`, or `TRUE_FORWARD_OBSERVATION`.
   - Gate 15A does not connect a live broker feed; attempts to submit `TRUE_FORWARD_OBSERVATION` fail closed (`TrueForwardAcquisitionNotAuthorizedError`).
   - `true_forward_observation_count = 0`.
   - `forward_performance_evaluated = False`.
7. **Gate Phasing & Forward Validation Stack**:
   - Gate 13 = production feature parity on canonical broker-derived historical snapshots.
   - Gate 14 = frozen offline inference parity.
   - Gate 15A = forward shadow observation infrastructure.
   - Gate 15B-A = read-only MT5 forward acquisition authority v2.1.0.
   - Gate 15B-B = first genuine read-only forward observation proof (Obs 1, pre-contract audit).
   - Gate 15C = frozen forward outcome contract V1 (`CLEAN_DIRECTIONAL_EXCURSION_V2`).
   - Gate 15D-A = prospective forward outcome eligibility authority.
   - Gate 15D-B = prospective post-contract genuine forward observation proof (Obs 2).
   - Gate 15D-C-A v1.1 = decision-bar timing semantic correction (Historical / Superseded).
   - Gate 15D-C-B1 v1.1 = outcome ledger semantic alignment (Historical / Superseded).
   - Gate 15D-C-B2A = prospective forward outcome anchor authority V1.
   - Gate 15D-C-B2B = anchor-required forward outcome maturer V2.
   - Gate 15D-C-B2C = anchor-required forward outcome ledger V2.
   - Gate 15D-C-B2D = genuine prospective observation + same-snapshot anchor integration (🟢 NEXT PLANNED GATE).
   - Gate 15E = matured forward shadow evaluation across real calendar time (⬜ PENDING).

---

# 44. Read-Only MT5 Forward Acquisition Architecture (Gate 15B-A v2.1.0)

Under Gate 15B-A v2.1.0, connected market-data acquisition is governed by:

```text
02_AI/Adapters/mt5_read_only_forward_acquisition_adapter.py
```

### Purpose & Isolation Facade
Gate 15B-A provides provably isolated, read-only MetaTrader 5 market data acquisition:
- Wraps the MT5 session in `MT5ReadOnlyCapabilityFacade`, exposing strictly whitelisted read-only methods (`symbols_get`, `symbol_info`, `symbol_info_tick`, `copy_rates_from_pos`).
- Raises `PermissionError` on any call to mutating broker/order APIs (`order_send`, `order_check`, `positions_get`, `orders_get`, `history_orders_get`, `history_deals_get`).
- Enforces `start_pos >= 1` in rate requests to strictly exclude forming/incomplete candles.
- MT5 initialization failure fails closed immediately (`BrokerConnectionError`).

### Broker Timezone & Historical DST Normalization
- Supports three timestamp interpretation modes: `AUTO`, `UNIX_UTC`, and `NY_CLOSE_SERVER_WALL_CLOCK`.
- Under `NY_CLOSE_SERVER_WALL_CLOCK` (default for retail Forex brokers such as Exness / IC Markets where server clock tracks Eastern European Time / US DST transitions):
  - Integer timestamps are interpreted as server wall-clock seconds.
  - Dynamically calculates UTC offset per row based on US DST boundary transitions (UTC+2 in winter, UTC+3 in summer).
  - Eliminates fixed broker offset assumptions and prevents temporal leakage across historical H1 D1 reconstruction.

### Content-Addressed Snapshot Fingerprinting
- Fetches multi-timeframe OHLCV bars (`M5`, `M15`, `M30`, `H1`, `H4`, `D1`) required by Gate 13.
- Normalizes column names and types into deterministic pandas DataFrames.
- Computes canonical lowercase 64-hex SHA256 snapshot hash (`source_snapshot_id`).
- Emits tamper-evident `ForwardAcquisitionAttestation` and `ForwardMarketSnapshot`.

### Safety Distinction
- Read-only forward acquisition is **NOT** trading authority.
- The adapter contains zero risk calculations, zero position tracking, and zero execution routing.

---

# 45. Frozen Forward Outcome Contract Architecture (Gate 15C)

Under Gate 15C, the forward outcome definition corresponding to the frozen C04 model target is established by:

```text
02_AI/Models/frozen_c04_forward_outcome_contract.py
```

### Frozen Target Semantics
- **Contract Version**: `FROZEN_C04_FORWARD_OUTCOME_CONTRACT_V1`
- **Contract Fingerprint SHA256**: `01fe52a2f068fcc8fb2fc5b89dd7e19dc974fc2d967cfb791e75c3415804ce87`
- **Target Contract**: `CLEAN_DIRECTIONAL_EXCURSION_V2`
- **Base Timeframe**: `M5`
- **Forward Horizon**: `12 completed M5 rows` (row-based, not wall-clock; weekend/session gaps allowed).
- **Profit Threshold**: `1.25 ATR`
- **Maximum Adverse Excursion (MAE)**: `0.75 ATR`
- **Classes**:
  - `SHORT = -1`: Future downside excursion >= 1.25 ATR AND future upside excursion <= 0.75 ATR.
  - `NO_TRADE = 0`: All other future paths (indeterminate, choppy, or conflicting excursions).
  - `LONG = 1`: Future upside excursion >= 1.25 ATR AND future downside excursion <= 0.75 ATR.
- **Directional Excursion Logic**: The target evaluates maximum excursions across the horizon. It is **not** barrier-first (first-touch) logic.

---

# 46. Prospective Forward Outcome Eligibility Architecture (Gate 15D-A)

Under Gate 15D-A, prospective forward eligibility is governed by:

```text
02_AI/Models/frozen_c04_forward_outcome_eligibility.py
```

### Eligibility Boundary & Pre-Contract Policy
- **Eligibility Version**: `FROZEN_C04_FORWARD_OUTCOME_ELIGIBILITY_V1`
- **Gate 15C Activation Cutoff**: `2026-09-28T11:16:59Z`
- **Pre-Contract Policy**: Observations recorded with `decision_time <= Gate 15C Activation` (such as Observation 1 at `10:15:00Z`) are classified as `PRE_CONTRACT_AUDIT_ONLY`. They are permanently retained for pipeline audit but strictly excluded from formal forward performance evaluation.
- **Prospective Rule**: An observation is eligible for prospective scoring only if `decision_time > 2026-09-28T11:16:59Z`.
- Timestamp eligibility alone is **necessary but not sufficient** for formal scoring; a validated same-snapshot prospective outcome anchor is now also mandatory.

---

# 47. Prospective Forward Outcome Anchor Architecture (Gate 15D-C-B2A)

Under Gate 15D-C-B2A, prospective outcome reference capture is governed by:

```text
02_AI/Models/frozen_c04_forward_outcome_anchor.py
```

### Architectural Purpose & Same-Snapshot Policy
- **Anchor Version**: `FROZEN_C04_FORWARD_OUTCOME_ANCHOR_V1`
- **Anchor Ledger Version**: `FROZEN_C04_FORWARD_OUTCOME_ANCHOR_LEDGER_V1`
- **Capture Policy**: `SAME_ACQUISITION_SNAPSHOT_NO_FUTURE_M5_ROWS`
- **Formal Invariant**: `FORMAL_MATURATION_REQUIRES_ANCHOR = true`

To prevent post-hoc reconstruction and subtle reference drift, entry reference values must be captured prospectively from the **exact same market data snapshot** used for feature generation and inference, **before** any future outcome rows are observed:
1. Decision candle open time UTC (`decision_bar_open = decision_time - 5 minutes`);
2. Exact decision candle M5 close (`decision_m5_close`);
3. Exact decision candle M5 ATR14 (`decision_m5_atr14`);
4. Source snapshot ID matching the canonical acquisition snapshot hash;
5. Semantic anchor fingerprint (`SHA256` of canonical JSON).

### Anchor Ledger Architecture
- **Runtime Path**: `01_Data/Shadow/xauusd_frozen_c04_forward_outcome_anchors.jsonl` (local, gitignored).
- **Durability**: OS file locking (`msvcrt`/`fcntl`), byte-0 seek alignment, flush, and fsync.
- **Fail-Closed Semantics**: Conflicting anchors for the same logical observation ID raise `ConflictingAnchorError`. Ledger corruption raises `CorruptedAnchorLedgerError`. Identical records are idempotent duplicates.
- **Orphan Anchor Rule**: If anchor append succeeds but observation append fails, the anchor must **never** be deleted or truncated. It remains an orphan prospective anchor and cannot be scored until the exact matching observation is appended.

---

# 48. Anchor-Required Forward Outcome Maturer V2 Architecture (Gate 15D-C-B2B)

Under Gate 15D-C-B2B, prospective outcome maturation is governed by:

```text
02_AI/Models/frozen_c04_forward_outcome_maturer.py
```

### Superseded Authority & V2 Invariants
- **Maturation Version**: `FROZEN_C04_FORWARD_OUTCOME_MATURER_V2`
- **Supersedes**: `FROZEN_C04_FORWARD_OUTCOME_MATURER_V1_1` (which established corrected bar-timing semantics but retrospectively reconstructed entry close and ATR14 from later completed frames).
- **Entry Reference**: `PROSPECTIVE_ANCHOR_DECISION_M5_CLOSE`
- **ATR Reference**: `PROSPECTIVE_ANCHOR_DECISION_M5_ATR14`
- **Anchor Requirement**: `VALIDATED_PROSPECTIVE_ANCHOR_REQUIRED`
- **Reconstruction Policy**: `POST_HOC_ENTRY_AND_ATR_RECONSTRUCTION_FORBIDDEN`

### Maturation Data Flow
The later completed M5 market data frame is restricted:
- Used **only** to locate the decision row and identify the **NEXT 12 completed M5 rows** (`horizon_rows`).
- Used to calculate `max_future_high` and `min_future_low` across those 12 rows.
- Evaluates directional excursion using the **already-frozen prospective anchor** entry close and ATR14.
- Must **never** overwrite or re-derive decision reference values.
- Matured outcomes carry source observation fingerprint, source anchor fingerprint, and source anchor version.

---

# 49. Forward Outcome Ledger V2 Architecture (Gate 15D-C-B2C)

Under Gate 15D-C-B2C, matured prospective outcome storage is governed by:

```text
02_AI/Models/frozen_c04_forward_outcome_ledger.py
```

### Ledger Authority & Persisted Fields
- **Ledger Version**: `FROZEN_C04_FORWARD_OUTCOME_LEDGER_V2`
- **Supersedes**: `FROZEN_C04_FORWARD_OUTCOME_LEDGER_V1_1`
- **Compatibility**: Accepts only outcomes produced by `FROZEN_C04_FORWARD_OUTCOME_MATURER_V2`.
- **Mandatory Persisted Authority Fields**:
  - `source_observation_fingerprint`
  - `source_anchor_fingerprint`
  - `source_anchor_version`
  - `entry_reference_policy = PROSPECTIVE_ANCHOR_DECISION_M5_CLOSE`
  - `atr_reference_policy = PROSPECTIVE_ANCHOR_DECISION_M5_ATR14`
  - `validated_prospective_anchor_required = true`
  - `reconstruction_policy = POST_HOC_ENTRY_AND_ATR_RECONSTRUCTION_FORBIDDEN`
  - `maturation_version = FROZEN_C04_FORWARD_OUTCOME_MATURER_V2`
  - `outcome_contract_fingerprint`
  - `outcome_semantic_fingerprint`
- **Runtime Path**: `01_Data/Shadow/xauusd_frozen_c04_forward_outcomes.jsonl` (local, gitignored, locked, append-only).

---

# 50. Forward Validation Scoring Rules, Runtime Ledgers & Next Engineering Gate

### Runtime Ledgers Status:
1. **Observation Ledger** (`01_Data/Shadow/xauusd_frozen_c04_shadow_observations.jsonl`):
   - Current count: **2**
   - Obs 1 (`2026-09-28T10:15:00Z`): Pre-contract audit only; permanently excluded from formal scoring.
   - Obs 2 (`2026-09-28T11:45:00Z`): Genuine post-contract acquisition proof; **EXCLUDED FROM FORMAL SCORING** due to missing prospective anchor at acquisition time (`POST_CONTRACT_ACQUISITION_PROOF_EXCLUDED_FROM_FORMAL_SCORING_MISSING_PROSPECTIVE_ANCHOR`).
2. **Anchor Ledger** (`01_Data/Shadow/xauusd_frozen_c04_forward_outcome_anchors.jsonl`):
   - Zero genuine runtime anchors appended during offline freeze.
3. **Outcome Ledger** (`01_Data/Shadow/xauusd_frozen_c04_forward_outcomes.jsonl`):
   - Zero genuine outcomes matured or appended.

### The 11 Strict Formal Scoring Conditions:
An observation is formally scoreable only if all 11 conditions are met:
1. Genuine approved read-only forward acquisition (`MT5ReadOnlyForwardAcquisitionAdapter:2.1.0`);
2. `TRUE_FORWARD_OBSERVATION` provenance;
3. Frozen Gate 13 feature authority (`331` columns, hash `65637cc2...`);
4. Frozen Gate 14 model authority (`C04_FLAT_EXTRA_TREES_CONSTRAINED`, hash `48a1d7...`);
5. Post-contract prospective eligibility (`decision_time > 2026-09-28T11:16:59Z`);
6. Valid same-snapshot prospective anchor captured at acquisition time;
7. Anchor captured and persisted BEFORE future outcome exposure;
8. Correct decision-bar timing semantics (`decision_bar_open = decision_time - 5 minutes`);
9. Exact 12 completed future M5 rows after the decision bar;
10. Execution via `FROZEN_C04_FORWARD_OUTCOME_MATURER_V2`;
11. Persistence into `FROZEN_C04_FORWARD_OUTCOME_LEDGER_V2`.

Because Observation 2 lacked a prospective anchor at acquisition time, condition #6 is not satisfied. It is permanently excluded from formal forward scoring, and no anchor may ever be retroactively manufactured for it.

### Next Planned Gate: Gate 15D-C-B2D
- **Title**: Genuine Prospective Observation + Same-Snapshot Anchor Integration
- **Execution Sequence**:
  ```text
  REAL Read-Only MT5 Acquisition
    → Same Immutable Acquisition Snapshot
    → Gate 13 Portable Features (331)
    → Gate 14 Frozen C04 Inference
    → Candidate TRUE_FORWARD Observation
    → Prospective Eligibility Check (PASS)
    → Capture Prospective Anchor from SAME Snapshot
    → Durably Append Anchor FIRST (Flush + Fsync)
    → Verify Anchor Ledger Integrity
    → Append Observation SECOND (Flush + Fsync)
    → Verify Observation Ledger Integrity
    → (No maturation or performance evaluation during capture step)
  ```
- **Operational Rules**:
  - The older Gate 15D-B runner must **NOT** be reused because it lacks the mandatory prospective-anchor ordering.
  - If anchor append succeeds but observation append fails, the anchor is retained as an orphan anchor (never delete, rewrite, or truncate). It cannot become formally scoreable until the exact linked observation exists.

