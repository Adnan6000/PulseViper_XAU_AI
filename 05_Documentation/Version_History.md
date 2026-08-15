# PulseViper XAU AI
## Development & Research Version History

This document records major verified milestones.

It does not attempt to list every source-file edit.

---

# Core Intelligence Foundation

PulseViper developed deterministic/research engines for:

- structure
- BOS
- liquidity
- sweeps
- displacement
- FVG
- institutional zones
- regime
- confidence
- setup state
- risk
- shadow execution research

A trusted broad regression checkpoint reached:

```text
1005 passed
14 warnings
```

Warnings were existing `datetime.utcnow()` deprecation warnings in the historical downloader.

---

# Instrument Isolation Milestone

Introduced:

```text
02_AI/Common/instrument_context.py
```

Capabilities:

- canonical symbol identity
- asset class
- broker symbol identity
- contract specification
- account scope
- environment identity
- deterministic fingerprints
- learning namespace
- execution namespace

Result:

```text
Cross-symbol contamination now has an explicit fail-closed boundary.
```

---

# Instrument Frame Guard Milestone

Introduced:

```text
02_AI/Dataset/instrument_frame_guard.py
```

Added identity columns for canonical market datasets and strict context validation.

Result:

```text
mixed-symbol / mixed-context DataFrames can be rejected.
```

---

# Broker Binding Milestone

Introduced:

```text
02_AI/Dataset/broker_instrument_context_binding.py
```

Verified explicit Gold broker aliases.

No arbitrary suffix wildcarding.

---

# Read-Only MT5 Attestation Milestone

Introduced:

```text
02_AI/Dataset/mt5_read_only_instrument_attestation_adapter.py
```

Validated:

- exact broker symbol
- currency base
- currency profit
- point
- digits
- contract size
- volume constraints

No live authorization was added.

---

# Exness DEMO XAUUSD Attestation Milestone

Real Exness DEMO verification confirmed:

```text
Broker Symbol     : XAUUSDm
Base Currency     : XAU
Profit Currency   : USD
Description       : Gold vs US Dollar
Point             : 0.001
Digits            : 3
Contract Size     : 100
Volume Minimum    : 0.01
Volume Maximum    : 200
Volume Step       : 0.01
```

Derived contract identity:

```text
EXNESS_XAUUSD_SPEC_D133951851B554C9
```

Status:

```text
GREEN
```

---

# Canonical History Milestone

Implemented immutable historical persistence.

Real DEMO materialization:

```text
M1  : 100,000
M5  : 100,000
M15 : 100,000
M30 : 100,000
H1  : 56,723
H4  : 16,045
D1  : 3,872
```

Each artifact receives:

- SHA256
- manifest
- context identity
- exact broker symbol
- contract identity

Status:

```text
GREEN
```

---

# Forward Execution Evidence Milestone

Introduced:

```text
02_AI/Shadow/forward_demo_execution_evidence_journal.py
```

Capabilities:

- current executable Bid/Ask evidence
- PREPARED evidence persistence
- hash-linked journal
- external ticket binding
- forward slippage evidence
- fail-closed recovery

Focused validation:

```text
133 passed
```

---

# Realized Fill Integration Milestone

Verified journal-to-fill lifecycle integration.

Focused validation:

```text
65 passed
```

Added normalized:

- spread
- slippage
- commission
- fill evidence

---

# Exactly-Once Observation Milestone

Introduced:

```text
02_AI/Shadow/realized_fill_observation_coordinator.py
```

Capabilities:

- durable observation journal
- exactly-once request handling
- duplicate execution rejection
- recovery without broker replay

Focused validation:

```text
86 passed
```

---

# Training Matrix V1

Introduced:

```text
02_AI/Dataset/training_matrix_builder.py
```

Result:

```text
Contract         : XAUUSD_MTF_TRAINING_V1
Rows             : 99,945
Features         : 270
Base Timeframe   : M5
Context          : M15/M30/H1/H4/D1
```

Chronological splits:

```text
TRAIN       : 69,966
VALIDATION  : 14,983
TEST        : 14,996
```

Status:

```text
GREEN
```

---

# XAUUSD_MODEL_v1

First complete immutable ML training pipeline.

Model successfully trained and stored.

Test:

```text
Accuracy          : ~47.76%
Balanced Accuracy : ~33.66%
Macro F1          : ~33.27%
NO_TRADE Recall   : ~1.35%
```

Conclusion:

```text
V1 target contract produced an inadequate NO_TRADE class.
Not promoted.
```

---

# Target Calibration V2

Calibrated labels:

```text
Profit Threshold      : 1.25 ATR
Max Adverse Excursion : 0.75 ATR
```

Distribution:

```text
SHORT     : 25,519
NO_TRADE  : 48,623
LONG      : 25,803
```

Status:

```text
GREEN
```

---

# XAUUSD_MODEL_v2

Test:

```text
Accuracy          : ~37.55%
Balanced Accuracy : ~34.97%
Macro F1          : ~32.96%
```

NO_TRADE recall:

```text
~48.16%
```

Conclusion:

```text
Target quality improved.
Predictive quality remained insufficient.
Not promoted.
```

---

# Gold Feature Enrichment V3

Introduced:

```text
02_AI/Dataset/training_feature_enricher.py
```

Added:

```text
63 causal Gold-domain features
```

New total:

```text
333 features
```

Sources:

- market regime
- adaptive structure
- BOS
- FVG
- causal institutional-zone confirmations

Status:

```text
GREEN
```

---

# XAUUSD_MODEL_v3

Test:

```text
Accuracy          : ~38.42%
Balanced Accuracy : ~34.56%
Macro F1          : ~33.06%
```

Recall:

```text
SHORT     : ~12.19%
NO_TRADE  : ~53.02%
LONG      : ~38.47%
```

Conclusion:

```text
NO_TRADE recognition improved.
Directional predictive edge remained weak.
Not promoted.
```

---

# Current Model Research Direction

The next architecture is hierarchical:

```text
TRADEABLE
vs
NO_TRADE
```

followed by:

```text
LONG
vs
SHORT
```

for tradeable observations only.

Target V2 remains the preferred current label contract unless new evidence justifies changing it.

---

# Major Git Checkpoint

Commit:

```text
23c1d01
```

Message:

```text
Add symbol-isolated XAUUSD data and model research pipeline
```

This checkpoint contains major work for:

- instrument isolation
- broker binding
- Exness DEMO attestation
- canonical data
- training V1/V2/V3
- model V1/V2/V3
- execution evidence
- realized-fill coordination

---

# Current State

```text
Instrument Identity       : GREEN
Broker DEMO Attestation   : GREEN
Canonical Historical Data : GREEN
Training Pipeline         : GREEN
Model Artifact Pipeline   : GREEN
Model Predictive Quality  : NOT ACCEPTED
Shadow Research           : ACTIVE
Live Authorization        : FALSE
```