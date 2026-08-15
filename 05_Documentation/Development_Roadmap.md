# PulseViper XAU AI
## Development Roadmap

> This roadmap is planning guidance.
>
> It is not an authoritative completion record.

---

# Phase 1 — Core Market Intelligence

## Implemented Research Areas

- adaptive market structure
- swing confirmation
- HH / HL / LH / LL
- BOS
- liquidity research
- liquidity sweeps
- displacement
- Fair Value Gaps
- FVG mitigation
- FVG quality
- institutional zones
- market regime
- candle / swing intelligence
- setup-state intelligence
- confidence research
- risk research

Status:

```text
IMPLEMENTED / EXISTING
```

Further calibration may still be required.

---

# Phase 2 — Shadow & Risk Infrastructure

Implemented areas include:

- broker-aware risk
- account protection
- execution-aware admission
- compounding planning
- lifecycle accounting
- execution-friction modeling
- paper ledger
- research candidate ledger
- research telemetry
- forward execution evidence
- historical fill telemetry
- completed-fill telemetry
- realized execution-cost accounting

Status:

```text
IMPLEMENTED / RESEARCH-VALIDATED IN MULTIPLE GATES
```

---

# Phase 3 — Instrument Isolation

Implemented:

- canonical symbol identity
- asset-class identity
- explicit broker aliases
- exact broker-symbol identity
- contract-spec identity
- account/environment identity
- learning namespace
- execution namespace
- deterministic fingerprints
- fail-closed context validation
- DataFrame identity stamping

Status:

```text
GREEN
```

---

# Phase 4 — Exness DEMO XAUUSD Attestation

Verified:

```text
Broker          : EXNESS
Broker Symbol   : XAUUSDm
Canonical       : XAUUSD
Asset Class     : METAL
Base Currency   : XAU
Profit Currency : USD
Environment     : DEMO
Live Authorized : false
```

Contract identity:

```text
EXNESS_XAUUSD_SPEC_D133951851B554C9
```

Status:

```text
GREEN
```

---

# Phase 5 — Canonical Historical Data

Implemented:

- exact broker-symbol fetching
- strict history validation
- identity-stamped datasets
- immutable CSV persistence
- immutable manifests
- SHA256 verification
- contract-aware namespace isolation

Verified real DEMO history:

```text
M1  : 100,000
M5  : 100,000
M15 : 100,000
M30 : 100,000
H1  : 56,723
H4  : 16,045
D1  : 3,872
```

Status:

```text
GREEN
```

---

# Phase 6 — Training Matrix V1

Implemented:

```text
Contract        : XAUUSD_MTF_TRAINING_V1
Rows            : 99,945
Base Timeframe  : M5
Context         : M15, M30, H1, H4, D1
Features        : 270
```

Also implemented:

- completed-bar HTF alignment
- future-only targets
- chronological split
- purge gaps
- immutable training artifacts

Status:

```text
GREEN
```

---

# Phase 7 — Target Calibration V2

Implemented target:

```text
Profit Threshold      : 1.25 ATR
Max Adverse Excursion : 0.75 ATR
```

Result:

```text
SHORT     ~25.5%
NO_TRADE  ~48.6%
LONG      ~25.8%
```

Status:

```text
GREEN
```

Target should remain frozen unless later evidence provides a strong reason to change it.

---

# Phase 8 — Gold Domain Features V3

Added:

```text
63 causal Gold-domain features
```

Including:

- regime
- adaptive structure
- BOS
- FVG
- institutional-zone confirmations

Total:

```text
333 features
```

Status:

```text
GREEN
```

---

# Phase 9 — Model Training Infrastructure

Implemented:

- exact training artifact discovery
- dataset hash verification
- explicit feature ordering
- TRAIN-only scaling
- TRAIN-only fitting
- class probabilities
- confidence
- entropy uncertainty
- validation/test evaluation
- immutable model artifacts

Current model experiments:

```text
XAUUSD_MODEL_v1
XAUUSD_MODEL_v2
XAUUSD_MODEL_v3
```

Infrastructure status:

```text
GREEN
```

Predictive quality status:

```text
NOT ACCEPTED
```

---

# Current Priority — Hierarchical Model V4

The next major model experiment should separate:

```text
Question 1:
Is this market state worth trading?
```

from:

```text
Question 2:
If tradeable, which direction?
```

---

## Stage A — Tradeability

Classes:

```text
TRADEABLE
NO_TRADE
```

Primary metrics:

- balanced accuracy
- F1
- precision
- recall
- calibration
- confidence coverage

---

## Stage B — Direction

Training subset:

```text
TRADEABLE samples only
```

Classes:

```text
LONG
SHORT
```

Primary metrics:

- balanced accuracy
- LONG recall
- SHORT recall
- precision
- directional stability

Status:

```text
NEXT
```

---

# Following Priority — Higher-Timeframe Domain Intelligence

Current V3 Gold-domain features are primarily base-timeframe domain context.

Future work should test whether causal domain features from:

```text
M15
H1
H4
```

improve generalization.

Only features demonstrating real out-of-sample benefit should be retained.

Status:

```text
PLANNED
```

---

# Following Priority — Liquidity Calibration

Existing liquidity logic requires careful ML calibration.

Future work:

- ATR-normalized distances
- volatility-aware tolerance
- regime-aware liquidity
- causal sweep lifecycle
- session-sensitive liquidity
- pool age
- mitigation state

Absolute thresholds should not be blindly inserted into long-history Gold models.

Status:

```text
PLANNED
```

---

# Following Priority — Execution-Aware Learning

Future learning datasets may incorporate:

- actual spread
- forward slippage
- commission
- MFE
- MAE
- realized R
- stop outcome
- target outcome
- time to resolution

Forward broker evidence should remain distinct from reconstructed historical execution estimates.

Status:

```text
PLANNED
```

---

# Shadow Model Inference

Once an offline model demonstrates meaningful edge:

- load exact model artifact
- load exact scaler
- validate exact feature contract
- validate exact instrument scope
- build causal real-time features
- output probabilities
- journal inference
- collect forward outcomes

Initial inference stage:

```text
NO ORDER EXECUTION
```

Status:

```text
BLOCKED BY MODEL QUALITY
```

---

# Controlled DEMO Decision Integration

Only after successful shadow inference:

- integrate model probabilities
- preserve deterministic risk rules
- preserve NO_TRADE
- preserve broker identity checks
- preserve account protection
- preserve execution evidence

Status:

```text
FUTURE
```

---

# REAL Account Consideration

Not currently authorized.

Requirements should include:

- strong out-of-sample evidence
- walk-forward stability
- forward DEMO evidence
- execution-friction validation
- calibration stability
- failure-mode tests
- account-protection proof
- explicit live authorization
- fail-closed deployment architecture

Status:

```text
NOT AUTHORIZED
```