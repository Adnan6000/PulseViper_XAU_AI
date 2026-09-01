# PulseViper XAU AI — Feature Contract & Feature Guide

## 1. Purpose

This document explains how features are treated inside PulseViper XAU AI.

It is intended for:

* students;
* feature engineers;
* ML researchers;
* production developers;
* reviewers.

This file explains:

* what a feature is;
* why feature semantics matter;
* how feature families are organized;
* how multi-timeframe features work;
* what broker portability means;
* why feature order is frozen;
* how to safely add or modify features;
* and how production features must match historical research.

---

# 2. Important Source-of-Truth Rule

The current frozen portable model uses:

```text
331 ordered features
```

The authoritative ordered feature list belongs to the frozen machine-readable feature/manifest contract.

This Markdown document is an educational guide.

It must **not** become an independent competing source of truth for feature order.

Frozen feature-column SHA256:

```text
65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2
```

Therefore:

```text
AUTHORITATIVE FEATURE ORDER
        =
FROZEN MACHINE-READABLE MANIFEST
```

not:

```text
whatever order appears in a Markdown table
```

This rule prevents documentation drift.

---

# 3. What Is a Feature?

A feature is a numerical input supplied to a machine-learning model.

Example raw candles:

```text
time
open
high
low
close
```

A derived feature may be:

```text
candle_range = high - low
```

Example:

```python
candle_range = high - low
```

If:

```text
high = 2350.20
low  = 2346.70
```

then:

```text
candle_range = 3.50
```

The model does not understand the words:

```text
strong bullish market
```

It receives numerical representations of market behavior.

---

# 4. A Feature Is More Than a Column Name

A valid feature requires several properties.

For example:

```text
feature_name:
H1_ATR_RATIO
```

is not enough.

The real contract should include concepts such as:

```text
formula
timeframe
lookback
units
missing-data behavior
timestamp alignment
broker dependency
normalization behavior
feature order
```

Two developers can calculate a column with the same name differently.

That is why feature semantics matter.

---

# 5. Current Frozen Feature Contract

Current portable model input:

```text
feature_count = 331
```

Frozen feature-order fingerprint:

```text
65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2
```

Model artifact:

```text
xauusd_portable_331_c04_full_train_model.joblib
```

The model expects the exact feature contract it was trained on.

---

# 6. Why Feature Order Matters

Suppose training input was:

```text
index 0 = feature_A
index 1 = feature_B
index 2 = feature_C
```

Training row:

```text
[10.2, 4.5, 0.7]
```

Later production sends:

```text
index 0 = feature_B
index 1 = feature_A
index 2 = feature_C
```

Production row:

```text
[4.5, 10.2, 0.7]
```

The model still receives three numbers.

No Python shape error necessarily occurs.

But the model interprets each value incorrectly.

Therefore:

```text
correct shape
    ≠
correct feature contract
```

---

# 7. Required Production Feature Checks

Before inference, production should eventually verify:

```text
[ ] feature_count == 331
[ ] exact ordered feature names
[ ] feature_columns_sha256 matches
[ ] all values numeric
[ ] all values finite
[ ] timestamp valid
[ ] required warm-up available
[ ] no stale market data
[ ] broker/time semantics valid
```

Fail closed if the feature contract cannot be proven.

---

# 8. Feature Families

PulseViper features can be understood conceptually through feature families.

The exact frozen 331 names remain defined by the machine-readable contract.

Major conceptual families include:

```text
Price / candle geometry
Volatility
Market structure
Liquidity
Patterns
Institutional zones
Market regime
Multi-timeframe context
Session / time context
Relative / normalized measurements
Broker-portable replacements
```

Not every implementation necessarily uses every conceptual example shown below.

Examples in this document teach feature design principles.

---

# 9. Price and Candle Geometry Features

These describe the shape of price bars.

Possible concepts include:

```text
range
body size
upper wick
lower wick
body/range ratio
close location
direction
```

Example:

```python
range_size = high - low
body_size = abs(close - open)
```

Possible normalized form:

```python
body_ratio = body_size / range_size
```

Why normalization can help:

A raw `$4` candle has different meaning depending on current volatility.

A ratio can express relative candle structure.

---

# 10. Example — Candle Location

Suppose:

```text
high  = 2350
low   = 2340
close = 2348
```

A close-location feature could conceptually represent:

```python
(close - low) / (high - low)
```

Result:

```text
0.80
```

Interpretation:

The candle closed near the upper part of its range.

A feature definition should specify what happens when:

```text
high == low
```

Division-by-zero behavior must be deterministic.

---

# 11. Volatility Features

Volatility features describe price movement magnitude.

Possible concepts:

```text
ATR
rolling range
normalized candle range
volatility expansion
volatility contraction
relative volatility
```

Example:

```text
current ATR = 7
rolling median ATR = 5
```

Conceptual ratio:

```text
ATR ratio = 7 / 5 = 1.4
```

Interpretation:

Current volatility is elevated relative to recent history.

---

# 12. Why Raw Volatility Can Be Broker Sensitive

Raw price distances may depend on:

* symbol price formatting;
* broker digits;
* contract conventions;
* spread;
* data quality.

Portable feature design often prefers normalized relationships where scientifically appropriate.

Example:

```text
range / ATR
```

may be more transferable than an uncontextualized absolute range.

This does not mean every absolute feature is invalid.

Portability must be evaluated feature by feature.

---

# 13. Market Structure Features

Market structure describes directional organization of price.

Conceptual features may include:

```text
swing-high state
swing-low state
break of structure
change of character
trend state
distance to structural level
```

Example conceptual representation:

```text
bullish BOS = 1
no bullish BOS = 0
```

Or:

```text
distance_to_swing_high / ATR
```

The exact calculation must be deterministic.

---

# 14. Structural Leakage Warning

A structure feature must only use information available at the decision time.

Bad conceptual implementation:

```text
Current row
    ↓
look into future bars
    ↓
confirm swing
    ↓
write result back to current row
```

This may create future leakage.

Feature construction must respect decision-time availability.

---

# 15. Liquidity Features

Liquidity-related concepts may include:

```text
equal highs
equal lows
liquidity pools
liquidity sweeps
inducement
distance to liquidity
```

Example conceptual feature:

```text
distance_to_equal_high / ATR
```

Another:

```text
recent_buy_side_sweep = 1
```

A production implementation must define exactly how equality tolerance is measured.

For example:

```text
absolute points?
ATR fraction?
percentage?
tick size?
```

Ambiguity is a portability risk.

---

# 16. Pattern Features

Pattern features may represent:

```text
compression
expansion
range breakout
failed breakout
candle clusters
momentum transitions
```

Example conceptual compression feature:

```text
short-term ATR
        /
long-term ATR
```

If ratio is low:

```text
relative compression
```

Again, actual frozen semantics must come from code/contract.

---

# 17. Institutional Zone Features

Conceptual institutional features may include:

```text
order blocks
fair value gaps
imbalances
distance to zones
zone interaction
```

Example:

```text
distance_to_nearest_bullish_zone / ATR
```

Potential problems:

* zone repainting;
* future confirmation;
* ambiguous invalidation;
* broker-dependent gaps.

Such features need careful causal validation.

---

# 18. Market Regime Features

Regime features describe broader market state.

Examples:

```text
trend
range
high volatility
low volatility
expansion
compression
```

Possible representation:

```text
regime_trending = 1
regime_ranging = 0
```

or continuous:

```text
trend_strength = 0.72
```

Categorical features should have stable encoding.

---

# 19. Multi-Timeframe Features

PulseViper uses multi-timeframe context.

Conceptually:

```text
Lower timeframe
        +
Higher timeframe
        +
Daily context
        ↓
combined model state
```

Possible timeframes may include combinations of intraday and daily bars depending on the feature pipeline.

The important rule is alignment.

---

# 20. Multi-Timeframe Alignment Example

Suppose a decision is made at:

```text
10:37
```

If an H1 candle is still forming from:

```text
10:00 → 10:59
```

a feature must explicitly define whether it uses:

```text
last completed H1 candle
```

or:

```text
current incomplete H1 candle
```

Using one during training and the other during production creates feature drift.

---

# 21. D1 Feature Risk

Daily candles are especially broker sensitive.

Different brokers may have different daily rollover boundaries.

Example:

```text
Broker A D1:
00:00 → 23:59

Broker B D1:
server-time rollover
```

These can produce different:

```text
open
high
low
close
ATR
structure
```

for what a human thinks is the same calendar day.

Therefore production D1 reconstruction is a major remaining portability task.

---

# 22. Canonical Time Architecture

Desired future production path:

```text
Broker timestamp
        ↓
Canonical timestamp
        ↓
Canonical MTF bars
        ↓
Canonical D1
        ↓
Feature calculations
```

This makes feature meaning less dependent on broker-native candle boundaries.

---

# 23. Session and Time Features

Time-related features may encode:

```text
hour
session
day-of-week
market transition
session overlap
```

These features are dangerous if they directly use broker-local server time without normalization.

Example:

```text
London session
```

should mean the same market period regardless of broker server timezone.

---

# 24. Broker-Sensitive Features

A broker-sensitive feature is one whose value can materially change because of broker implementation rather than market behavior.

Examples may involve:

```text
broker-specific symbol naming
broker-native D1 boundaries
broker-local timestamps
spread
tick volume
missing bars
server session
```

Broker-sensitive does not always mean unusable.

It means its semantics require explicit handling.

---

# 25. Portable Features

A portable feature is intended to preserve meaning across broker environments.

Typical portability strategies include:

```text
normalization
canonical timestamps
canonical D1 reconstruction
symbol abstraction
broker metadata normalization
relative measurements
explicit missing-data rules
```

A feature should not be declared portable merely because it runs on a second broker.

Semantic equivalence must be tested.

---

# 26. Feature Portability Test

A useful conceptual test:

```text
Same market period
Broker A raw data
        ↓
canonical feature pipeline
        ↓
Feature A

Same market period
Broker B raw data
        ↓
canonical feature pipeline
        ↓
Feature B
```

Then compare:

```text
Feature A
vs
Feature B
```

Not every value must necessarily be identical.

But differences should be understood and acceptable.

---

# 27. Missing Data Behavior

Production feeds can contain:

```text
missing bars
delayed bars
duplicate bars
out-of-order bars
```

A feature contract should define what happens.

Dangerous behavior:

```text
missing H1 candle
        ↓
silently use an unrelated previous value
```

Preferred behavior may be:

```text
detect missing dependency
        ↓
mark feature batch invalid
        ↓
do not infer
```

depending on the specific feature contract.

---

# 28. Non-Finite Values

Model inputs should not contain:

```text
NaN
+Infinity
-Infinity
```

A production feature batch should fail validation if any required model feature is non-finite.

Example:

```python
if not np.isfinite(X).all():
    raise ValueError("Non-finite feature input")
```

Conceptual example only; actual implementation should follow the project contract.

---

# 29. Warm-Up Windows

Many features require historical observations.

Examples:

```text
ATR(14)
rolling mean(50)
swing detection
regime windows
```

A system cannot calculate a valid feature immediately after receiving one candle.

Production architecture should define a warm-up requirement.

Example:

```text
minimum_required_history = maximum dependency window
```

Do not fill unavailable warm-up features with arbitrary zero values unless the frozen contract explicitly defines that behavior.

---

# 30. Frozen Feature Matrix

Current TRAIN matrix:

```text
X.shape = (69966, 331)
```

A valid batch requires:

```text
row alignment
column alignment
finite values
correct chronology
correct target linkage
```

Feature correctness is more than dimensionality.

---

# 31. Feature-to-Target Alignment

For supervised learning:

```text
X[row i]
```

must correspond to:

```text
target_class[row i]
target_tradeable[row i]
decision_time[row i]
```

A one-row shift can destroy scientific validity while still allowing model training to complete.

Example dangerous mistake:

```text
features row 100
paired with
target row 101
```

No shape error occurs if lengths are still equal.

Therefore alignment checks matter.

---

# 32. Decision Time

`decision_time` represents when a model observation exists.

Features at a given decision time must not include information that became available later.

Conceptual requirement:

```text
feature_information_time
    <=
decision_time
```

except where a specific offline label-generation process deliberately uses future values for targets.

Targets may look forward.

Features may not.

---

# 33. Feature vs Target

Important distinction:

```text
FEATURE
    = information available to the model

TARGET
    = future outcome being predicted
```

Example:

```text
Feature:
current ATR

Target:
whether future price reaches directional excursion threshold
```

Using future target information as a feature is leakage.

---

# 34. Example of Leakage

Bad feature:

```python
future_high = high.shift(-5)
```

used as a model input at the current row.

This exposes the future.

Such a model may look excellent historically and fail in reality.

---

# 35. Scaling and Normalization

Not all models require feature scaling.

The frozen candidate registry contained some candidates with fold-local scalers.

The current winning model is ExtraTrees, which does not use a standard scaler in the frozen C04 configuration.

Important rule:

> Do not add a scaler to production C04 inference if training C04 did not use one.

The production transformation chain must match training.

---

# 36. Feature Selection

The current frozen model-selection protocol did not perform results-driven feature selection.

Current feature count remained:

```text
331
```

after the portable contract was frozen.

Do not inspect TEST and remove weak-looking features.

That would create a new experiment.

---

# 37. Adding a New Feature

Suppose a developer wants:

```text
H1_range_percentile
```

Correct process:

```text
1. Define exact mathematical formula.
2. Define source timeframe.
3. Define lookback.
4. Define decision-time availability.
5. Define missing-data behavior.
6. Test leakage.
7. Test broker portability.
8. Add deterministic unit tests.
9. Create a new feature-contract version.
10. Generate a new ordered feature fingerprint.
11. Build a new dataset lineage.
12. Start new model research.
```

Do not simply turn:

```text
331 features
```

into:

```text
332 features
```

inside the current experiment.

---

# 38. Removing a Feature

Removing a feature also creates a different model input contract.

Example:

```text
331
    ↓
remove one feature
    ↓
330
```

The existing C04 model is no longer compatible.

A new model must be trained.

---

# 39. Changing a Feature Formula

Even when the name stays the same, changing formula semantics creates a different contract.

Example:

Old:

```python
feature = distance / ATR_14
```

New:

```python
feature = distance / ATR_20
```

Same column name.

Different meaning.

Therefore a semantic fingerprint/version should change.

---

# 40. Changing a Timeframe

Old:

```text
H1 volatility
```

New:

```text
M30 volatility
```

is a feature change even if the formula is otherwise identical.

Timeframe is part of feature identity.

---

# 41. Changing Broker Time Logic

Changing:

```text
broker-native D1
```

to:

```text
canonical reconstructed D1
```

may be scientifically correct for portability.

But it changes historical feature semantics unless the frozen training dataset already used that canonical logic.

Therefore production work must prove compatibility rather than assume it.

---

# 42. Student Exercise — Define a Feature Properly

Bad description:

```text
ATR feature
```

Better:

```text
Name:
H1_ATR_RATIO

Input timeframe:
H1

Current value:
ATR(14)

Reference:
rolling median ATR over specified history

Formula:
current ATR / reference ATR

Decision-time rule:
completed H1 bars only

Missing data:
fail batch

Broker dependency:
timeframe aggregation must be canonical
```

This level of detail makes implementation reproducible.

---

# 43. Student Exercise — Inspect a Feature for Leakage

For any feature ask:

```text
Does it use future bars?

Does it use a centered rolling window?

Does swing confirmation write backward?

Does higher-timeframe data include an incomplete candle?

Does a resample operation accidentally include future timestamps?
```

If yes or unclear, investigate before using it in research.

---

# 44. Student Exercise — Inspect Portability

For any feature ask:

```text
Does it depend on broker timezone?

Does it depend on tick volume?

Does it depend on spread?

Does it depend on symbol digits?

Does it depend on native D1 bars?

Does it depend on missing-bar patterns?

Does it depend on broker naming?
```

If yes, portability strategy must be documented.

---

# 45. Feature Testing Categories

A strong feature implementation should have several test types.

## Formula test

Known input produces expected numerical result.

## Boundary test

Handles:

```text
zero range
missing dependency
first available rows
```

## Leakage test

No future information enters decision-time features.

## Alignment test

Output timestamp corresponds to intended source data.

## Portability test

Broker-dependent inputs produce understood behavior.

## Finiteness test

No required feature contains non-finite values.

---

# 46. Example Formula Test

Suppose:

```text
high = 10
low = 6
open = 7
close = 9
```

Then:

```text
range = 4
body = 2
body/range = 0.5
```

A deterministic unit test can verify these simple relationships.

---

# 47. Feature Fingerprints

Why hash the feature list?

Suppose a developer accidentally changes:

```text
feature_120
feature_121
```

order.

The row count and feature count remain unchanged.

A feature-list fingerprint detects this contract change.

Current frozen hash:

```text
65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2
```

---

# 48. Why This Markdown Does Not Duplicate All 331 Names

There are two possible documentation designs.

## Design A

Manually maintain all 331 ordered feature names in Markdown.

Problem:

```text
code changes
manifest changes
Markdown forgotten
```

Now two conflicting sources exist.

## Design B

Keep the machine-readable frozen manifest authoritative and use this document to explain semantics, families, rules, and navigation.

PulseViper follows Design B.

If a human-readable exact 331-column appendix is later desired, it should be automatically generated from the frozen manifest rather than manually maintained.

---

# 49. Historical vs Production Features

Historical feature generation happens on frozen research data.

Production feature generation happens on live broker data.

They must converge on the same semantic contract.

Desired architecture:

```text
Historical Data
      ↓
Portable Feature Pipeline
      ↓
331 Feature Contract
      ↓
Frozen Model

Live Broker Data
      ↓
Canonicalization
      ↓
Portable Feature Pipeline
      ↓
SAME 331 Feature Contract
      ↓
SAME Frozen Model
```

---

# 50. Production Feature Parity

Before shadow inference, prove:

```text
[ ] same feature count
[ ] same order
[ ] same formulas
[ ] same timeframe interpretation
[ ] same timestamp alignment
[ ] same missing-data policy
[ ] same normalization
[ ] same D1 semantics
```

Feature parity is one of the most important remaining production gates.

---

# 51. Feature Drift

Even if code is correct, future market feature distributions can change.

Examples:

```text
ATR distribution changes
spread distribution changes
session behavior changes
range ratios change
prediction-related inputs shift
```

Future shadow monitoring should measure feature drift.

Drift does not automatically mean failure.

It means the new input environment differs from research history.

---

# 52. Feature Drift vs Feature Bug

These are different.

## Feature drift

```text
correct formula
new market regime
different distribution
```

## Feature bug

```text
wrong formula
wrong timestamp
wrong order
wrong broker boundary
```

Monitoring should help distinguish them.

---

# 53. Prediction Drift

Feature changes may lead to changes in model prediction distribution.

Example historical:

```text
SHORT     30%
NO_TRADE  40%
LONG      30%
```

Future shadow:

```text
SHORT      2%
NO_TRADE  96%
LONG       2%
```

This should trigger investigation.

It may indicate:

```text
market regime shift
feature drift
integration bug
broker semantic mismatch
```

---

# 54. Current Feature Development Status

Completed:

```text
[✓] portable research contract
[✓] frozen 331 feature count
[✓] frozen feature order
[✓] feature-list SHA
[✓] frozen TRAIN integration
[✓] model trained against exact 331 inputs
[✓] VALIDATION used same contract
```

Remaining:

```text
[ ] new-broker canonical timestamps
[ ] canonical D1 reconstruction
[ ] live MTF synchronization
[ ] production feature parity
[ ] runtime feature hash enforcement
[ ] feature drift monitoring
```

---

# 55. New Student Feature Workflow

Before modifying features:

```text
[ ] Read Developer_Guide.md
[ ] Read Architecture.md
[ ] Read this file
[ ] Find feature source code
[ ] Find associated tests
[ ] Understand timeframe
[ ] Understand formula
[ ] Check leakage
[ ] Check broker dependency
[ ] Check downstream model impact
```

After modifying:

```text
[ ] New tests written
[ ] py_compile passed
[ ] focused pytest passed
[ ] contract version reviewed
[ ] new fingerprint generated if needed
[ ] dataset lineage reviewed
[ ] documentation updated
```

---

# 56. Feature Change Decision Table

| Change                                                         | Existing C04 Still Valid? |            New Experiment? |
| -------------------------------------------------------------- | ------------------------: | -------------------------: |
| Documentation typo                                             |                       Yes |                         No |
| Test improvement only                                          |                       Yes |                         No |
| Feature reorder                                                |                        No |                        Yes |
| Add feature                                                    |                        No |                        Yes |
| Remove feature                                                 |                        No |                        Yes |
| Change formula                                                 |                        No |                        Yes |
| Change timeframe                                               |                        No |                        Yes |
| Change missing-value semantics                                 |                Usually no |                    Usually |
| Change production implementation but prove identical semantics |               Potentially | Depends on parity evidence |
| Add runtime validation only                                    |                       Yes |                 Usually no |

---

# 57. Golden Feature Rules

```text
1. Features may not use future information.

2. Feature order is part of model identity.

3. Feature count alone does not prove compatibility.

4. Broker portability must be demonstrated.

5. D1 semantics require special attention.

6. Missing data must have explicit behavior.

7. Non-finite values must fail closed.

8. A changed formula creates a changed feature.

9. A changed feature usually requires a new model.

10. The frozen machine-readable manifest is authoritative.
```

---

# 58. Current Frozen Feature Summary

```text
Feature count:
331

Feature-column SHA256:
65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2

Frozen model:
C04_FLAT_EXTRA_TREES_CONSTRAINED

Model artifact SHA256:
48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769

VALIDATION:
PASSED

VALIDATION rerun:
NOT AUTHORIZED

TEST:
NOT YET CONSUMED

Production feature parity:
PENDING

Live:
NOT AUTHORIZED
```

---

# 59. Final Principle

A model does not receive “market knowledge.”

It receives an ordered numerical feature vector.

Therefore:

> If feature meaning, timing, ordering, or broker semantics change, the model's scientific meaning may change even when the Python code still executes successfully.

Feature contracts must be treated as carefully as model artifacts.
