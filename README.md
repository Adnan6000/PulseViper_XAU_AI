# PulseViper XAU AI

> **Symbol-Isolated Gold Trading Intelligence & Machine-Learning Research System**

PulseViper XAU AI is a modular quantitative research system currently focused on **XAUUSD (Gold)**.

The project combines:

- MetaTrader 5 broker data
- strict instrument identity isolation
- causal multi-timeframe feature engineering
- market structure intelligence
- liquidity research
- institutional-zone analysis
- risk and execution-friction research
- immutable dataset lineage
- supervised machine learning
- shadow / DEMO execution evidence
- controlled future model-inference architecture

The current development environment is connected to an **Exness DEMO account** for research, broker validation, dataset construction, and forward evidence collection.

> **Live trading is not currently authorized by the research, dataset, model, or shadow pipelines.**

---

## Project Mission

The long-term objective of PulseViper is to build an AI system that understands Gold as a market rather than simply predicting the next candle.

The system is being designed to reason about:

- market structure
- multi-timeframe alignment
- volatility
- liquidity
- displacement
- Fair Value Gaps
- institutional zones
- execution conditions
- risk
- uncertainty
- tradeability

The AI must also be capable of concluding:

```text
NO_TRADE
```

when market conditions are uncertain, noisy, conflicting, or operationally unsuitable.

---

# Core Engineering Rules

PulseViper currently follows these rules.

## 1. Symbol Isolation

Algorithms may be reusable across instruments.

However, the following must never silently mix across symbols:

- historical data
- feature contracts
- learned models
- scalers
- model evaluation
- execution statistics
- journals
- broker calibration
- risk calibration
- performance history

Current canonical instrument:

```text
XAUUSD
```

Current asset class:

```text
METAL
```

---

## 2. Exact Broker Identity

Broker symbols are explicitly mapped to canonical instruments.

Current verified Exness DEMO Gold contract:

```text
Canonical Symbol : XAUUSD
Asset Class      : METAL
Broker            : EXNESS
Broker Symbol     : XAUUSDm
Base Currency     : XAU
Profit Currency   : USD
Environment       : DEMO
Live Authorized   : false
```

Current verified contract specification:

```text
EXNESS_XAUUSD_SPEC_D133951851B554C9
```

Broker-like names are not accepted through wildcard guessing.

A symbol with a Gold-like description but incompatible metadata must fail closed.

---

## 3. Causal Feature Generation

A model feature may use:

```text
current market information
past information
already-confirmed historical events
completed higher-timeframe bars
```

A model feature must not use:

```text
future candle highs/lows
future target outcomes
future-confirmed pivots projected backward
retrospective labels
hindsight rankings
```

Future market information is allowed only inside clearly separated supervised target / outcome columns.

---

## 4. NO_TRADE Is a Real Decision

The system must not force LONG or SHORT predictions.

The model architecture treats:

```text
LONG
SHORT
NO_TRADE
```

as meaningful outcomes.

The next research architecture will separate:

```text
TRADEABLE vs NO_TRADE
```

from:

```text
LONG vs SHORT
```

---

## 5. DEMO Before REAL

The current broker environment is used for DEMO research.

A context containing:

```text
execution_environment = REAL
```

must never automatically mean:

```text
live_authorized = true
```

Real-account authorization requires a future, explicit safety boundary.

---

# Current System Architecture

```text
MetaTrader 5 / Exness DEMO
            |
            v
Broker & Instrument Attestation
            |
            v
Canonical InstrumentContext
            |
            v
Multi-Timeframe Historical Data
            |
            v
Canonical Immutable Datasets
            |
            v
Causal Feature Engineering
            |
            v
Gold Market Intelligence
            |
            v
Future-Only Supervised Targets
            |
            v
Chronological Dataset Splits
            |
            v
Model Training
            |
            v
Offline Evaluation
            |
            v
Future Shadow Inference
            |
            v
Controlled DEMO Validation
```

---

# Instrument Identity Architecture

The central identity implementation is:

```text
02_AI/Common/instrument_context.py
```

Important identity fields include:

```text
canonical_symbol
asset_class
broker_id
broker_symbol
account_scope_id
execution_environment
contract_spec_id
data_schema_version
feature_contract_version
```

The system also generates deterministic fingerprints for:

- instrument identity
- learning scope
- execution scope

This allows future BTC, NASDAQ, or other instruments to use shared algorithms without silently contaminating XAUUSD state.

---

# Canonical Data Pipeline

Primary modules:

```text
02_AI/Dataset/broker_instrument_context_binding.py
02_AI/Dataset/mt5_read_only_instrument_attestation_adapter.py
02_AI/Dataset/instrument_frame_guard.py
02_AI/Dataset/history_manager.py
02_AI/Dataset/export_dataset.py
```

Canonical datasets are:

- identity stamped
- symbol validated
- broker-context validated
- content addressed
- SHA256 verified
- immutable
- accompanied by manifests

Generated canonical data is stored locally under:

```text
01_Data/Canonical/
```

This directory is intentionally excluded from Git.

---

# Verified Exness DEMO Historical Data

A real Exness DEMO XAUUSD history build successfully materialized:

| Timeframe | Rows |
|---|---:|
| M1 | 100,000 |
| M5 | 100,000 |
| M15 | 100,000 |
| M30 | 100,000 |
| H1 | 56,723 |
| H4 | 16,045 |
| D1 | 3,872 |

The lower H1/H4/D1 counts reflect actual broker-available history.

The system does not fabricate missing history to reach a requested row count.

---

# Market Intelligence Layer

PulseViper currently contains research engines for:

- adaptive swing detection
- HH / HL / LH / LL structure
- market structure bias
- Break of Structure
- BOS memory
- liquidity
- liquidity sweeps
- sweep validation
- displacement
- Fair Value Gaps
- FVG mitigation
- FVG quality
- institutional zones
- market regime
- candle / swing intelligence
- market decision clarity
- setup state
- confidence research
- risk intelligence

Important implementation rule:

> Causal engine outputs and retrospective research labels must remain explicitly separated.

---

# Base Technical Features

The current central feature registry includes trend, momentum, volatility, and candle features.

## Trend

- EMA20
- EMA50
- EMA200
- EMA distances
- EMA slopes
- trend strength
- trend direction

## Momentum

- RSI14
- RSI slope
- MACD
- MACD signal
- MACD histogram
- ROC10
- Momentum10

## Volatility

- true range
- ATR14
- ATR percentage
- candle range
- average range
- volatility ratio
- rolling standard deviation

## Candle Context

- body size
- candle range
- wick sizes
- wick ratios
- bullish / bearish state
- doji
- marubozu
- pinbar
- bullish engulfing
- bearish engulfing
- inside bar
- outside bar
- expansion
- compression

---

# Machine-Learning Research

Machine learning is already operational as a research pipeline.

Three experiment generations have been created.

---

## Training Matrix V1

Training contract:

```text
XAUUSD_MTF_TRAINING_V1
```

Verified:

```text
Rows              : 99,945
Feature Count     : 270
Base Timeframe    : M5
Context Timeframes: M15, M30, H1, H4, D1
```

Chronological splits:

```text
TRAIN       : 69,966
VALIDATION  : 14,983
TEST        : 14,996
```

Higher-timeframe features become available only after their source candle has completed.

V1 demonstrated that the full causal dataset and model-training pipeline worked, but its target produced too few NO_TRADE samples.

---

## Training Matrix V2

Training contract:

```text
XAUUSD_MTF_TRAINING_V2
```

V2 retained the same causal 270-feature matrix but redesigned the supervised target.

Current calibrated directional target:

```text
Profit Excursion      : 1.25 ATR
Max Adverse Excursion : 0.75 ATR
```

Class distribution:

```text
SHORT     : 25,519
NO_TRADE  : 48,623
LONG      : 25,803
```

Approximate percentages:

```text
SHORT     : 25.5%
NO_TRADE  : 48.6%
LONG      : 25.8%
```

The distribution remains highly stable across TRAIN, VALIDATION, and TEST.

---

## Training Matrix V3

Training contract:

```text
XAUUSD_MTF_TRAINING_V3
```

V3 retained the V2 target contract and added:

```text
63 causal Gold-domain features
```

Total V3 feature count:

```text
333
```

V3 domain features include information derived from:

- market regime
- adaptive market structure
- BOS
- FVG
- causal institutional-zone confirmation events

---

# Model Research Results

Model artifacts are stored locally and are not committed to Git.

Every build records:

- training dataset identity
- feature order
- model ID
- model SHA256
- scaler SHA256
- manifest SHA256
- learning-scope fingerprint
- evaluation metrics

---

## XAUUSD_MODEL_v1

Test metrics approximately:

```text
Accuracy          : 47.76%
Balanced Accuracy : 33.66%
Macro F1          : 33.27%
```

NO_TRADE recall:

```text
1.35%
```

Conclusion:

```text
Target formulation unsuitable.
Model not promoted.
```

---

## XAUUSD_MODEL_v2

Test metrics:

```text
Accuracy          : 37.55%
Balanced Accuracy : 34.97%
Macro F1          : 32.96%
```

NO_TRADE recall:

```text
48.16%
```

Conclusion:

```text
NO_TRADE target improved substantially.
Overall predictive edge remained weak.
Model not promoted.
```

---

## XAUUSD_MODEL_v3

Test metrics:

```text
Accuracy          : 38.42%
Balanced Accuracy : 34.56%
Macro F1          : 33.06%
```

Per-class recall:

```text
SHORT     : 12.19%
NO_TRADE  : 53.02%
LONG      : 38.47%
```

Conclusion:

```text
Gold-domain features improved NO_TRADE recognition,
but did not create sufficient directional predictive edge.
Model not promoted.
```

---

# Next Model Architecture

The next research direction is hierarchical classification.

```text
                Market State
                     |
                     v
        +--------------------------+
        | Stage A                  |
        | TRADEABLE vs NO_TRADE    |
        +--------------------------+
                     |
              if TRADEABLE
                     |
                     v
        +--------------------------+
        | Stage B                  |
        | LONG vs SHORT            |
        +--------------------------+
```

Combined probabilities can later be expressed as:

```text
P(LONG)
=
P(TRADEABLE)
*
P(LONG | TRADEABLE)
```

and:

```text
P(SHORT)
=
P(TRADEABLE)
*
P(SHORT | TRADEABLE)
```

This design separates two different questions:

```text
Should the system trade?
```

from:

```text
If trading, what direction?
```

---

# Shadow / Execution Evidence

The repository contains substantial research-only infrastructure inside:

```text
02_AI/Shadow/
```

including:

- account protection
- broker-aware risk
- execution-friction modeling
- compounding research
- paper ledgers
- research candidate ledgers
- opportunity-quality research
- forward execution evidence capture
- forward DEMO execution evidence journal
- read-only fill telemetry
- completed-fill telemetry
- realized execution-cost accounting
- realized-fill telemetry bridge
- exactly-once realized-fill observation coordination

These components do not independently grant live execution permission.

---

# Validation History

A trusted full regression checkpoint completed with:

```text
1005 passed
14 warnings
```

The warnings were existing `datetime.utcnow()` deprecation warnings in the historical downloader.

Later major focused gates also passed for:

- instrument identity
- frame isolation
- broker binding
- read-only MT5 attestation
- Exness DEMO Gold context
- canonical history
- forward execution evidence
- realized-fill coordination
- training matrix V1
- target V2
- feature enrichment V3
- model V1/V2/V3 artifact generation

Successful training does not imply model acceptance.

Predictive quality is evaluated separately.

---

# Repository Structure

```text
PulseViper_XAU_AI/
|
+-- 01_Data/
|   +-- Raw/
|   +-- Backups/
|
+-- 02_AI/
|   +-- Common/
|   +-- Config/
|   +-- Core/
|   +-- Database/
|   +-- Dataset/
|   +-- Features/
|   +-- Memory/
|   +-- Models/
|   +-- Objects/
|   +-- Shadow/
|   +-- Utils/
|
+-- 04_Testing/
|
+-- 05_Documentation/
|
+-- config.yaml
+-- pyproject.toml
+-- requirements.txt
+-- README.md
```

---

# Documentation Authority

Documentation is intended to explain the system.

It is **not** the authoritative completion record.

For actual implementation status, priority should be given to:

1. source code
2. automated test output
3. broker attestation
4. immutable manifests
5. real DEMO operation output
6. Git history

A roadmap item is not considered complete merely because a document marks it complete.

---

# Author

## Muhammad Adnan

**BSIT Graduate | Full Stack Software Engineer | Certified Ethical Hacker (CEH) | Forex Trader**

GitHub:

```text
@Adnan6000
```

---

# Risk Disclaimer

PulseViper XAU AI is a quantitative-research and software-development project.

Nothing in this repository constitutes financial advice, investment advice, or a guarantee of profitability.

Trading Gold, Forex, CFDs, or any leveraged financial product can result in substantial financial loss.

Any future REAL-account deployment should require strong independent validation, execution-friction analysis, out-of-sample testing, walk-forward testing, controlled DEMO forward evidence, account-protection verification, and an explicit live-authorization architecture.