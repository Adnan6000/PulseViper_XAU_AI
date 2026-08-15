# PulseViper XAU AI
## Research Trading & Decision Rules

> These rules define engineering and research boundaries.
>
> They are not financial advice and are not a live trading strategy.

---

# Rule 1 — NO_TRADE Is Always Allowed

The system must never be forced to choose LONG or SHORT.

When evidence is weak, contradictory, noisy, or operationally unsafe:

```text
NO_TRADE
```

is the correct system action.

---

# Rule 2 — Canonical Instrument Must Match

Current instrument:

```text
XAUUSD
```

Current verified broker contract:

```text
EXNESS
XAUUSDm
XAU / USD
```

Unknown or incompatible broker symbols must fail closed.

---

# Rule 3 — Never Mix Instrument State

XAUUSD data must not silently mix with:

```text
BTCUSD
NAS100
EURUSD
or any other future instrument
```

Separate by instrument:

- models
- scalers
- datasets
- execution statistics
- journals
- risk state
- learned state

---

# Rule 4 — Features Must Be Causal

Allowed:

```text
current market information
past market information
completed higher-timeframe bars
already-confirmed historical structure
```

Forbidden:

```text
future bars
future targets
future stop/target outcomes
retrospective labels
future-confirmed pivots projected backward
```

---

# Rule 5 — Future Information Belongs Only to Targets

Future price paths may be used when constructing supervised learning outcomes.

Examples:

```text
future upside excursion
future downside excursion
target hit
stop hit
forward return
time to resolution
MFE
MAE
```

These must not become model input features.

---

# Rule 6 — Model Success Does Not Mean Trade Permission

The following do not automatically authorize a model:

```text
training completed
artifact saved
accuracy above random
high confidence on some rows
```

Promotion requires strong out-of-sample evidence.

---

# Rule 7 — Deterministic Risk Controls Remain Independent

The AI must not bypass:

- lot constraints
- broker volume rules
- stop rules
- maximum exposure
- account protection
- execution environment
- risk limits

Model confidence is not permission to ignore deterministic safety.

---

# Rule 8 — DEMO and REAL Must Remain Separate

Current research environment:

```text
DEMO
```

Even if a context is later labeled:

```text
REAL
```

it must still default to:

```text
live_authorized = false
```

until a dedicated authorization layer explicitly changes that state.

---

# Rule 9 — Execution Evidence Must Be Truthful

Forward execution evidence should use actual contemporaneous market/broker data.

Historical reconstructed Bid/Ask:

```text
ANALYTICS ONLY
```

It must not be represented as authoritative forward slippage.

---

# Rule 10 — Target Contract

Current preferred V2/V3 supervised label:

## LONG

```text
up excursion >= 1.25 ATR
down excursion <= 0.75 ATR
```

## SHORT

```text
down excursion >= 1.25 ATR
up excursion <= 0.75 ATR
```

## NO_TRADE

```text
everything else
```

---

# Rule 11 — Current Model Promotion Status

Current models:

```text
XAUUSD_MODEL_v1
XAUUSD_MODEL_v2
XAUUSD_MODEL_v3
```

Status:

```text
RESEARCH ONLY
NOT PROMOTED
```

---

# Rule 12 — Next Decision Architecture

Next model architecture should separate tradeability from direction.

```text
Stage A:
TRADEABLE vs NO_TRADE
```

then:

```text
Stage B:
LONG vs SHORT
```

---

# Rule 13 — Confidence Requires Coverage

A model should not be considered useful merely because a tiny number of observations have high-confidence accuracy.

Evaluation must consider:

```text
confidence
accuracy
coverage
calibration
class balance
time stability
```

together.

---

# Rule 14 — Test Set Is a Final Holdout

The TEST split should not be repeatedly optimized against.

Model design and hyperparameter decisions should primarily use:

```text
TRAIN
VALIDATION
```

TEST remains the final out-of-sample check for that experiment generation.

---

# Rule 15 — REAL Deployment Requirements

Before future real-money consideration, evidence should include:

- chronological out-of-sample performance
- walk-forward stability
- balanced directional performance
- reliable NO_TRADE discrimination
- probability calibration
- execution-friction evidence
- DEMO forward evidence
- account-protection validation
- failure-mode testing
- exact symbol identity
- explicit live authorization

Until then:

```text
NO REAL AUTONOMOUS EXECUTION
```