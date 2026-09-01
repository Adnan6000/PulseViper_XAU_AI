# PulseViper XAU AI — Trading, Risk & Execution Rules

## 1. Purpose

This document explains the trading safety architecture of PulseViper XAU AI.

It is written for students and developers who need to understand the difference between:

```text
ML prediction
trade candidate
trade permission
risk approval
order execution
```

These are not the same thing.

The central rule is:

> A model prediction is information. It is not permission to place a trade.

---

# 2. Current Operational State

Current frozen research state:

```text
TRAIN:
complete

VALIDATION:
passed and consumed

TEST:
not yet consumed

Shadow ML integration:
not yet authorized

Live ML trading:
not authorized
```

Therefore:

```text
live_authorized = false
```

Nothing in historical ML research overrides this state.

---

# 3. Trading Architecture

Conceptual trading flow:

```text
MARKET DATA
    ↓
FEATURES
    ↓
ML MODEL / ANALYSIS
    ↓
SIGNAL CANDIDATE
    ↓
TRADE PERMISSION
    ↓
RISK ENGINE
    ↓
POSITION SIZE / PROTECTION
    ↓
SHADOW OR EXECUTION
```

Every stage can reject the trade.

---

# 4. Model Prediction Is Not an Order

Current C04 model predicts one of:

```text
-1 = SHORT
 0 = NO_TRADE
 1 = LONG
```

Example probability output:

```text
SHORT     0.21
NO_TRADE  0.29
LONG      0.50
```

Frozen model decision:

```text
LONG
```

This means:

```text
model prefers LONG
```

It does not mean:

```text
send BUY order immediately
```

---

# 5. Why This Separation Exists

The ML model does not independently know all operational constraints.

For example:

```text
spread may be too large
broker may be disconnected
account protection may block trading
position size may violate risk
data may be stale
symbol may be unavailable
market may be in restricted state
```

Therefore inference must pass through existing trading safety systems.

---

# 6. Frozen Runtime Boundary

The following existing components are protected unless a dedicated engineering task explicitly authorizes changes:

```text
MT5 order/execution semantics
RiskEngine
trade_ready
account protection
broker-aware sizing
core execution logic
shadow execution semantics
```

Do not change these components to make the ML model look better.

---

# 7. Research Metrics vs Trading Performance

Historical classifier metrics include:

```text
directional macro-F1
balanced accuracy
SHORT recall
LONG recall
trade coverage
log-loss
Brier
```

Trading-system performance may involve different measures:

```text
profit/loss
expectancy
drawdown
risk-adjusted return
slippage
transaction costs
spread
trade lifecycle
```

Good classification does not guarantee profitable execution.

---

# 8. Signal Layer

The signal layer answers a question similar to:

```text
What directional state does the analysis/model prefer?
```

Possible model output:

```text
SHORT
NO_TRADE
LONG
```

This is the first decision layer.

It is not the final execution decision.

---

# 9. NO_TRADE Is a Real Prediction

Class:

```text
0
```

means:

```text
NO_TRADE
```

It should not automatically be converted into:

```text
choose whichever direction is second-best
```

Doing that would change the frozen model decision rule.

---

# 10. Frozen Prediction Rule

Current C04 uses:

```python
probabilities = model.predict_proba(X)

prediction = model.classes_[
    probabilities.argmax(axis=1)
]
```

Expected class order:

```text
[-1, 0, 1]
```

No post-validation probability threshold tuning is part of the frozen experiment.

---

# 11. Do Not Add Hidden Thresholds

For example:

```python
if p_long > 0.60:
    trade_long()
```

would create a new decision policy.

Likewise:

```python
if p_short < 0.40:
    ignore_short()
```

would alter the frozen model behavior.

Threshold research belongs to a new experiment if scientifically authorized.

---

# 12. Trade Permission Layer

After a directional signal exists, the trading system can apply permission checks.

Examples may include:

```text
system mode
data validity
market conditions
spread state
execution availability
existing account/risk state
trade_ready logic
```

Exact active rules are owned by the corresponding runtime source/configuration.

This documentation does not invent numerical settings that have not been verified.

---

# 13. `trade_ready`

`trade_ready` represents an operational permission boundary.

Conceptually:

```text
signal exists
      +
required market/risk conditions satisfied
      ↓
trade_ready = true
```

A prediction should not bypass `trade_ready`.

---

# 14. Why `trade_ready` Is Protected

Without this boundary:

```text
model predicts LONG
    ↓
direct order
```

the model could bypass:

```text
execution checks
account protection
risk limits
market availability
```

Therefore production ML integration must adapt to the existing runtime contract.

---

# 15. RiskEngine

RiskEngine owns risk-related trading behavior.

Depending on current runtime implementation/configuration, responsibilities can include:

```text
risk limits
position sizing
account protection
exposure control
SL-related risk
trade permission
```

Exact numerical risk settings should be read from the authoritative runtime/configuration.

Do not guess them from documentation.

---

# 16. Model Must Not Choose Lot Size Directly

Bad architecture:

```text
model confidence = 0.90
        ↓
large lot automatically
```

unless such a sizing policy has been separately designed, tested, and authorized.

Preferred separation:

```text
model
  ↓
directional signal
  ↓
existing RiskEngine
  ↓
allowed position size
```

---

# 17. Broker-Aware Position Sizing

Broker specifications can affect position size.

Examples:

```text
contract size
minimum volume
maximum volume
volume step
tick size
tick value
symbol digits
```

Therefore lot sizing should remain broker aware.

Do not hard-code a lot size because a backtest used one.

---

# 18. Account Protection

Account protection is a higher-priority safety layer.

Conceptually:

```text
good model signal
      +
unsafe account state
      ↓
NO TRADE
```

The ML layer does not override account protection.

---

# 19. Risk Has Priority Over Prediction

If:

```text
prediction = LONG
```

but:

```text
risk permission = false
```

final action is:

```text
NO ORDER
```

This is expected behavior.

---

# 20. Execution Has Priority Over Prediction

Likewise:

```text
prediction = SHORT
```

but broker/execution state is invalid:

```text
NO ORDER
```

The prediction can still be logged for research.

---

# 21. Three Conceptual Execution Stages

PulseViper can be understood as three operational stages.

## Stage 1 — Permission

Questions:

```text
Is trading allowed?
Is input valid?
Is market state acceptable?
Is account state acceptable?
```

## Stage 2 — Signal / Timing

Questions:

```text
SHORT, NO_TRADE, or LONG?
Does required context agree?
```

## Stage 3 — Risk / Execution

Questions:

```text
What position size is permitted?
What protection is required?
Can the broker execute safely?
```

---

# 22. Market Data Must Be Valid

No inference or trade decision should rely on invalid market data.

Future production checks should include:

```text
latest timestamp
expected symbol
required bars
missing-bar detection
finite prices
MTF availability
```

Invalid data should fail closed.

---

# 23. Stale Data Rule

A mathematically valid 331-feature vector can still be unsafe if it was generated from stale market data.

Future production inference should verify freshness.

Conceptually:

```text
feature timestamp too old
        ↓
no inference / no trade
```

---

# 24. Feature Contract Before Trading

The model expects exactly:

```text
331 ordered features
```

Frozen feature-column SHA256:

```text
65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2
```

Before production prediction:

```text
feature count
+
feature order
+
feature semantics
+
finiteness
```

must be valid.

---

# 25. Wrong Features Must Fail Closed

Never do:

```text
331 expected
330 received
      ↓
append zero
```

or:

```text
unknown feature order
      ↓
predict anyway
```

A trading system should reject invalid model input.

---

# 26. Model Artifact Before Trading

Expected frozen model SHA256:

```text
48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769
```

A future inference adapter should verify the artifact.

If SHA differs:

```text
NO ML INFERENCE
NO ML-DRIVEN TRADE
```

until the artifact identity is understood.

---

# 27. Model Class Order Before Trading

Required:

```text
[-1, 0, 1]
```

Never guess probability-column semantics.

If class order differs:

```text
fail closed
```

---

# 28. Broker Symbol Normalization

Model research focuses on:

```text
XAUUSD / XAUUSDm
```

Different brokers may use different symbols.

Future production architecture should map:

```text
broker symbol
      ↓
canonical XAUUSD identity
```

before feature generation and trading.

---

# 29. Broker-Time Normalization

Broker server time can affect:

```text
sessions
H4 bars
D1 bars
daily features
rollover behavior
```

Therefore future production data should use documented canonical time semantics.

Do not modify historical feature meaning at runtime without parity evidence.

---

# 30. D1 Reconstruction

Daily candles are especially important for broker portability.

Desired future flow:

```text
broker intraday bars
      ↓
canonical timestamp
      ↓
canonical D1 reconstruction
      ↓
D1-dependent features
```

This should be verified before production ML use.

---

# 31. Spread

Spread affects trading economics and execution safety.

A model may make a correct directional prediction but still face:

```text
spread too large
```

making the trade unattractive or unsafe.

Spread controls belong to operational trading logic, not the ML classifier.

---

# 32. Slippage

Historical classifier evaluation does not automatically include real slippage.

Shadow/forward analysis should later account for:

```text
entry slippage
exit slippage
spread
execution delay
```

A model should not be promoted based only on classification metrics.

---

# 33. Stop Loss / Take Profit

SL/TP behavior belongs to the trading/risk contract.

Do not infer an exact active SL/TP formula from the ML target.

The research target:

```text
profit_atr = 1.25
max_adverse_atr = 0.75
```

defines supervised labels.

It does not automatically mean production orders must use:

```text
TP = 1.25 ATR
SL = 0.75 ATR
```

unless runtime code explicitly defines that behavior.

This distinction is critical.

---

# 34. Target Contract Is Not Execution Contract

Research labels answer:

> Did future directional price excursion satisfy the frozen target definition?

Execution rules answer:

> How should a real or simulated trade be managed?

These are related research concepts but are not automatically identical.

---

# 35. Current Target Contract

Research target:

```text
CLEAN_DIRECTIONAL_EXCURSION_V2
```

Parameters:

```text
profit_atr = 1.25
max_adverse_atr = 0.75
```

Target classes:

```text
SHORT
NO_TRADE
LONG
```

This contract must remain separate from undocumented runtime assumptions.

---

# 36. Shadow Mode

Shadow mode should allow the production-like system to run without sending real orders.

Desired flow:

```text
live broker data
      ↓
production feature pipeline
      ↓
frozen model
      ↓
signal
      ↓
existing permission/risk logic
      ↓
hypothetical trade
      ↓
shadow log
```

No real financial exposure is required.

---

# 37. What Shadow Should Record

Future shadow logs should include:

```text
decision timestamp
broker symbol
feature identity
model SHA
probabilities
predicted class
trade permission
risk decision
hypothetical size
spread
hypothetical entry
hypothetical exit
reason for rejection
```

This makes production behavior auditable.

---

# 38. Why Rejected Signals Should Be Logged

Suppose:

```text
model predicts LONG
```

but:

```text
RiskEngine rejects trade
```

That event is still useful research data.

Log:

```text
prediction
risk rejection reason
market state
```

Do not only log successful hypothetical trades.

---

# 39. Shadow Is Not Live

Even if shadow performance is strong:

```text
live_authorized
```

does not automatically become true.

Shadow is another evidence gate.

---

# 40. Forward Validation

After shadow integration, collect genuinely unseen market periods.

Evaluate:

```text
directional stability
coverage
SHORT/LONG balance
feature drift
prediction drift
transaction costs
drawdown
expectancy
regime stability
```

This is stronger evidence than repeatedly reusing historical holdouts.

---

# 41. Market-Regime Review

A strategy should not be assessed only on aggregate performance.

Forward research should inspect:

```text
trend
range
high volatility
low volatility
news-like expansion
session transitions
```

A model may perform well overall while failing catastrophically in one regime.

---

# 42. Trade Coverage

Current untouched VALIDATION predicted trade coverage:

```text
0.7541213375158513
```

This is a model diagnostic.

Future shadow coverage should be monitored for major changes.

Example:

```text
historical ≈ 75%
future ≈ 5%
```

requires investigation.

Do not automatically change thresholds.

---

# 43. Directional Balance

Current VALIDATION:

```text
SHORT recall:
0.3190499510284035

LONG recall:
0.529248683116163
```

The model is not perfectly symmetric.

Future monitoring should inspect whether one direction collapses.

Directional imbalance can reflect:

```text
market regime
feature drift
broker mismatch
model limitations
```

---

# 44. Probability Quality

Current VALIDATION report-only values:

```text
log_loss_3class =
1.0979186095143678

multiclass_brier =
0.6664287278633827
```

These do not currently authorize post-hoc calibration.

A future new research experiment may investigate calibration using a scientifically valid protocol.

---

# 45. No TEST-Driven Trading Rules

TEST must not be used to invent:

```text
new thresholds
new direction filters
new confidence cutoffs
new risk multipliers
```

for the current frozen experiment.

TEST evaluates the existing system/model hypothesis.

It does not develop it.

---

# 46. No VALIDATION-Driven Runtime Tweaks

VALIDATION has already been consumed.

Do not say:

```text
LONG recall was 0.529,
so increase LONG lot size.
```

That would convert holdout analysis into runtime tuning.

Any such idea requires a new research design.

---

# 47. Risk Configuration Source of Truth

This document intentionally does not declare unverified exact values such as:

```text
risk per trade = X%
maximum daily loss = Y%
```

unless those values are frozen and verified from actual runtime configuration.

For current numerical runtime rules:

```text
source code + configuration
```

are authoritative.

Documentation should be updated after those values are audited.

---

# 48. Execution Configuration Source of Truth

Likewise, exact current:

```text
order type
retry logic
broker filling mode
SL/TP placement semantics
execution timeout
```

must come from the actual frozen execution modules/configuration.

Do not copy assumptions from an old README.

---

# 49. No Direct MT5 Calls From Research Code

Research scripts should not casually call live MT5 order functions.

Separation should remain:

```text
04_Testing research
      ≠
live order execution
```

A research runner should not gain order privileges.

---

# 50. Development Example — Correct ML Integration

Future correct integration:

```text
Authorized production feature batch
          ↓
Feature validation
          ↓
Frozen C04 inference
          ↓
Prediction object
          ↓
Existing trade permission
          ↓
Existing RiskEngine
          ↓
Shadow execution
```

Not:

```text
model.predict()
      ↓
mt5.order_send()
```

---

# 51. Development Example — Risk Rejection

Suppose:

```text
model = LONG
trade_ready = true
risk_engine = rejected
```

Final state:

```text
NO ORDER
```

Log:

```text
model LONG
risk rejected
reason
```

Do not bypass risk because the model probability looked strong.

---

# 52. Development Example — Invalid Feature Batch

Suppose:

```text
feature count = 331
```

but:

```text
one value = NaN
```

Final state:

```text
NO INFERENCE
NO ORDER
```

Do not replace arbitrary NaN with zero in the execution adapter.

---

# 53. Development Example — Wrong Model

Expected SHA:

```text
48a1d70d...
```

Actual SHA differs.

Final state:

```text
MODEL IDENTITY FAILURE
NO ML SIGNAL
NO ML ORDER
```

This protects against accidental artifact replacement.

---

# 54. Development Example — Broker Disconnect

Suppose:

```text
model generated LONG
```

then broker connection becomes invalid.

Final state:

```text
NO NEW ORDER
```

Operational state has priority over stale model intent.

---

# 55. Development Example — NO_TRADE

Prediction:

```text
NO_TRADE
```

The downstream system should not manufacture a directional trade.

Final model signal:

```text
ABSTAIN / NO_TRADE
```

---

# 56. Auditability

Every future ML-driven shadow or live decision should ideally answer:

```text
Which model?
Which feature contract?
Which timestamp?
Which probabilities?
Which predicted class?
Was trade_ready true?
What did RiskEngine decide?
Was execution attempted?
What happened?
```

Without this evidence, debugging live behavior becomes difficult.

---

# 57. Kill Switch

Before live promotion, the system should have an explicit mechanism to prevent new orders when required.

Possible triggers include:

```text
operator action
data failure
model identity failure
broker failure
risk condition
system health failure
```

Exact implementation belongs to the future production safety gate.

---

# 58. Fail-Closed Conditions

Future runtime should fail closed when critical conditions are invalid.

Examples:

```text
wrong feature fingerprint
wrong model SHA
missing features
non-finite features
stale market data
unresolved broker symbol
invalid time alignment
risk rejection
account protection rejection
execution unavailable
```

Fail closed means:

```text
do not place a new ML-driven trade
```

---

# 59. Trading Development Safety Levels

## GREEN

Safe examples:

```text
documentation
shadow report formatting
offline synthetic signal tests
```

## YELLOW

Careful review:

```text
feature adapters
inference adapter
signal mapping
broker normalization
```

## RED

Protected:

```text
RiskEngine
account protection
lot sizing
trade_ready
order routing
live execution
```

---

# 60. Before Editing Trading Code

Ask:

```text
What exact component owns this rule?

Is it ML research or runtime behavior?

Will risk change?

Will lot size change?

Will real orders change?

Will trade_ready change?

Will account protection change?

What tests protect this behavior?

Does this create a new scientific experiment?
```

Do not modify until these are understood.

---

# 61. Before Shadow Authorization

Required conceptually:

```text
[ ] Final TEST completed
[ ] final research verdict acceptable
[ ] production 331 features verified
[ ] broker-time semantics verified
[ ] D1 semantics verified
[ ] model SHA enforced
[ ] feature SHA enforced
[ ] inference tests passed
[ ] RiskEngine integration preserved
[ ] no-real-order shadow assertion passed
```

---

# 62. Before Live Authorization

Required conceptually:

```text
[ ] shadow integration stable
[ ] forward unseen-market evidence acceptable
[ ] transaction costs considered
[ ] drawdown considered
[ ] drift monitoring implemented
[ ] stale-data behavior tested
[ ] broker failure behavior tested
[ ] account protection verified
[ ] risk controls verified
[ ] kill switch verified
[ ] explicit promotion decision recorded
```

---

# 63. Current Authorization Matrix

| Capability                | Current State      |
| ------------------------- | ------------------ |
| Model TRAIN research      | Complete           |
| Full TRAIN fit            | Complete           |
| Untouched VALIDATION      | Passed             |
| VALIDATION rerun          | Not authorized     |
| Final TEST infrastructure | Next               |
| Final TEST execution      | Not yet authorized |
| Production feature parity | Pending            |
| Shadow ML inference       | Not authorized     |
| Live ML execution         | Not authorized     |

---

# 64. Trading Rule Hierarchy

When rules conflict, the safe conceptual priority is:

```text
SYSTEM / ACCOUNT SAFETY
        ↓
RISK PERMISSION
        ↓
EXECUTION VALIDITY
        ↓
TRADE PERMISSION
        ↓
MODEL SIGNAL
```

A model signal should never override a higher safety layer.

---

# 65. Historical Research Does Not Override Safety

Even if future TEST produces excellent numbers:

```text
excellent TEST
```

does not imply:

```text
bypass RiskEngine
```

or:

```text
live_authorized = true
```

Research quality and runtime authorization remain separate.

---

# 66. Student Mental Model

A useful analogy:

```text
ML MODEL
=
analyst recommendation

RiskEngine / trade_ready / account protection
=
risk committee

Execution layer
=
trading desk
```

The analyst can recommend:

```text
LONG
```

but cannot independently place the trade.

---

# 67. Golden Trading Rules

```text
1. Prediction is not trade permission.

2. NO_TRADE must remain a valid outcome.

3. Never bypass trade_ready.

4. Never bypass RiskEngine.

5. Never bypass account protection.

6. Feature identity must be proven before inference.

7. Model identity must be proven before inference.

8. Runtime risk settings are not ML hyperparameters.

9. Historical holdouts must not tune live rules.

10. Shadow comes before live.
```

---

# 68. Current Project Trading State

```text
Frozen model:
C04_FLAT_EXTRA_TREES_CONSTRAINED

Features:
331

VALIDATION:
PASSED AND CONSUMED

TEST:
PENDING

Production feature parity:
PENDING

Shadow ML deployment:
NOT AUTHORIZED

Live ML deployment:
NOT AUTHORIZED
```

---

# 69. Final Principle

The goal of PulseViper is not to make the model trade as often as possible.

The goal is to build a system where:

```text
model
+
data
+
risk
+
execution
+
evidence
```

remain individually understandable and collectively safe.

A valid trading decision is therefore the result of the complete authorized system—not a single classifier output.
