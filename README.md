# PulseViper XAU AI

A research-first, safety-gated Python framework for **XAUUSD / XAUUSDm machine-learning research, broker-portable feature generation, shadow trading, risk management, and MetaTrader 5 execution**.

> **Current status:** Research / validation stage
> **Frozen model:** C04 constrained ExtraTrees, 331 portable features
> **Untouched VALIDATION:** Passed and permanently consumed
> **Final TEST:** Not yet consumed
> **Shadow deployment:** Not yet authorized
> **Live trading:** Not authorized

---

## Table of Contents

1. [What Is PulseViper?](#what-is-pulseviper)
2. [Project Philosophy](#project-philosophy)
3. [Current Research Status](#current-research-status)
4. [System Overview](#system-overview)
5. [Repository Structure](#repository-structure)
6. [Machine-Learning Pipeline](#machine-learning-pipeline)
7. [Current Frozen Model](#current-frozen-model)
8. [Validation Result](#validation-result)
9. [Quick Start for Students](#quick-start-for-students)
10. [Development Workflow](#development-workflow)
11. [Testing](#testing)
12. [Protected Research Boundaries](#protected-research-boundaries)
13. [Documentation](#documentation)
14. [Remaining Roadmap](#remaining-roadmap)
15. [Security and Secrets](#security-and-secrets)
16. [Important Disclaimer](#important-disclaimer)

---

# What Is PulseViper?

PulseViper is an engineering and research project focused on developing a reproducible XAUUSD machine-learning trading system.

The project is not only a model.

It includes multiple independent layers:

```text
Market / Broker Data
        ↓
Multi-Timeframe Processing
        ↓
Portable Feature Generation
        ↓
331-Feature Contract
        ↓
Machine-Learning Model
        ↓
Prediction / Signal
        ↓
Trading Safety Checks
        ↓
Risk Management
        ↓
Shadow / Execution Layer
```

Each layer has its own responsibility.

A good ML result does **not** automatically authorize live trading.

---

# Project Philosophy

PulseViper follows several core engineering principles.

## 1. Research must be reproducible

Important datasets, feature contracts, models, experiments, and decisions are identified using SHA256 fingerprints.

For example, the current frozen model artifact has a specific SHA256.

Changing the artifact means it is no longer the same experiment.

---

## 2. TRAIN, VALIDATION, and TEST have different jobs

```text
TRAIN
    Used for fitting and model research

VALIDATION
    Used once after research decisions are frozen

TEST
    Final untouched estimate of generalization
```

TEST must never become another tuning dataset.

---

## 3. Protected holdouts are one-time scientific assets

The current VALIDATION split has already been consumed.

It may not be rerun for performance-driven tuning.

The final TEST split is still protected.

---

## 4. Execution safety is separate from ML research

The following runtime areas are treated as frozen unless a dedicated engineering task explicitly authorizes modification:

* MT5 order/execution semantics
* RiskEngine
* `trade_ready`
* account protection
* broker-aware sizing
* core execution logic
* shadow execution semantics

Research code should not modify these components just to improve model metrics.

---

## 5. Fail closed

When artifact identity, feature order, dataset identity, protected-data state, or scientific provenance cannot be proven, the preferred behavior is to stop rather than continue with uncertain state.

---

# Current Research Status

The current portable ML experiment has completed the following stages:

```text
Portable feature research             ✅
331-feature contract                   ✅
Portable TRAIN dataset                 ✅
TRAIN input loader                     ✅
Target loader                          ✅
Supervised TRAIN batch                 ✅
TRAIN-only research protocol           ✅
Frozen six-model candidate registry    ✅
4-fold purged walk-forward evaluation  ✅
TRAIN-internal winner selection        ✅
Full TRAIN model fit                   ✅
Model artifact verification            ✅
VALIDATION protocol freeze             ✅
One-time VALIDATION infrastructure     ✅
Untouched VALIDATION                   ✅ PASSED
VALIDATION result freeze               ✅

Final untouched TEST                   ⏳ NEXT
Final research verdict                 ⏳
Production broker feature parity       ⏳
Frozen-model inference integration     ⏳
Shadow deployment                      ⏳
Forward shadow validation              ⏳
Live promotion                         ⛔ NOT AUTHORIZED
```

---

# System Overview

A simplified research-to-production flow is:

```text
Historical XAUUSD Data
        ↓
Feature Pipeline
        ↓
Portable Projection
        ↓
331 Ordered Features
        ↓
Frozen Target Labels
        ↓
TRAIN Dataset
        ↓
Purged Walk-Forward Research
        ↓
Frozen Candidate Winner
        ↓
Full TRAIN Fit
        ↓
Untouched VALIDATION
        ↓
Final TEST
        ↓
Production Feature Parity
        ↓
Shadow Inference
        ↓
Forward Validation
        ↓
Possible Live Promotion
```

The current project is between:

```text
VALIDATION RESULT FROZEN
        ↓
FINAL TEST
```

---

# Repository Structure

The main repository areas are conceptually:

```text
PulseViper_XAU_AI/
│
├── 01_Data/
│   └── Data-related resources
│
├── 02_AI/
│   ├── Dataset/
│   ├── feature/data infrastructure
│   ├── model-related code
│   ├── risk/runtime components
│   └── execution-related components
│
├── 04_Testing/
│   ├── unit tests
│   ├── integration tests
│   ├── research runners
│   ├── evidence generators
│   └── scientific contract checks
│
├── 05_Documentation/
│   ├── Developer_Guide.md
│   ├── Architecture.md
│   ├── Development_Roadmap.md
│   ├── Feature_List.md
│   ├── Module_List.md
│   ├── Trading_Rules.md
│   ├── Testing_Guide.md
│   ├── Research_Evidence_Index.md
│   ├── Troubleshooting.md
│   └── Version_History.md
│
├── config.yaml
├── requirements.txt
└── README.md
```

See `05_Documentation/Developer_Guide.md` before making substantial changes.

---

# Machine-Learning Pipeline

## Target Classes

The main classifier uses three classes:

```text
-1 = SHORT
 0 = NO_TRADE
 1 = LONG
```

The binary tradeability relationship must remain:

```python
target_tradeable = (target_class != 0)
```

---

## Frozen Portable Feature Count

Current model input:

```text
331 features
```

Frozen ordered feature-list fingerprint:

```text
65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2
```

Feature order matters.

Two matrices may both contain 331 columns and still represent completely different model inputs if their column order differs.

---

## Frozen TRAIN Dataset

```text
Dataset ID:
portable_cff75b0686383a3ab6f8352b

TRAIN rows:
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

# Current Frozen Model

TRAIN-internal winner:

```text
C04_FLAT_EXTRA_TREES_CONSTRAINED
```

Model family:

```text
sklearn.ensemble.ExtraTreesClassifier
```

Frozen configuration:

```python
ExtraTreesClassifier(
    n_estimators=500,
    max_depth=10,
    max_features=0.35,
    min_samples_leaf=25,
    bootstrap=False,
    class_weight="balanced",
    random_state=271828,
    n_jobs=-1,
)
```

Frozen candidate configuration fingerprint:

```text
f1b11c6f91561f2eba1bd56195e2239e9598b1906c88f11ada67eac6cdeb09e3
```

Model artifact:

```text
xauusd_portable_331_c04_full_train_model.joblib
```

Artifact SHA256:

```text
48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769
```

Prediction class order:

```text
[-1, 0, 1]
```

Prediction rule:

```python
probabilities = model.predict_proba(X)
prediction = model.classes_[probabilities.argmax(axis=1)]
```

No post-validation threshold tuning or probability calibration is allowed for this frozen experiment.

---

# Validation Result

The frozen C04 model completed its first and only untouched VALIDATION evaluation.

Status:

```text
ONE_TIME_VALIDATION_ACCEPTED
```

Important metrics:

| Metric                   |   Result |
| ------------------------ | -------: |
| Balanced accuracy        | 0.376568 |
| Macro-F1                 | 0.348904 |
| Directional macro-F1     | 0.336403 |
| SHORT precision          | 0.329373 |
| SHORT recall             | 0.319050 |
| SHORT F1                 | 0.324129 |
| LONG precision           | 0.259975 |
| LONG recall              | 0.529249 |
| LONG F1                  | 0.348676 |
| NO_TRADE recall          | 0.281404 |
| Predicted trade coverage | 0.754121 |
| Log-loss                 | 1.097919 |
| Multiclass Brier         | 0.666429 |

All predeclared hard validation requirements passed.

Validation result fingerprint:

```text
ea8b482e60f854f58e27f3be387b7bb82f0c16a6cf1a99555b12643aeeca5fa1
```

Validation-result freeze fingerprint:

```text
521a97b41a86231b049cc65aebfd85ffc7c83ae7141134d6ae1158d112b1468c
```

Important:

```text
validation_consumed = true
validation_rerun_authorized = false
```

---

# Quick Start for Students

## Step 1 — Clone the repository

```powershell
git clone https://github.com/Adnan6000/PulseViper_XAU_AI.git
cd PulseViper_XAU_AI
```

---

## Step 2 — Create a virtual environment

Windows:

```powershell
python -m venv .venv
```

Activate:

```powershell
.venv\Scripts\Activate.ps1
```

---

## Step 3 — Install dependencies

```powershell
python -m pip install -r requirements.txt
```

---

## Step 4 — Read the documentation

Recommended order:

```text
README.md
        ↓
05_Documentation/Developer_Guide.md
        ↓
05_Documentation/Architecture.md
        ↓
05_Documentation/Feature_List.md
        ↓
05_Documentation/Module_List.md
        ↓
05_Documentation/Testing_Guide.md
        ↓
05_Documentation/Research_Evidence_Index.md
```

---

## Step 5 — Do not start with live execution

A new developer should begin with:

1. reading tests;
2. running focused synthetic tests;
3. understanding research evidence;
4. modifying isolated research utilities;
5. only later working on runtime integration.

---

# Development Workflow

PulseViper uses finite engineering gates.

Typical workflow:

```text
Understand contract
        ↓
Design change
        ↓
Implement
        ↓
py_compile
        ↓
Focused pytest
        ↓
Synthetic / integration verification
        ↓
Authorized real operation
        ↓
Freeze evidence
        ↓
Update documentation
        ↓
Git commit
```

Example:

```powershell
python -m py_compile 04_Testing\exact_script.py
```

Then:

```powershell
python -m pytest 04_Testing\test_exact_script.py -q
```

Use exact filenames.

Do not use placeholder commands such as:

```text
python SCRIPT_NAME.py
```

---

# Testing

Different tests protect different things.

## Syntax check

```powershell
python -m py_compile path\to\file.py
```

## Focused unit test

```powershell
python -m pytest path\to\test_file.py -q
```

## Integration test

Used to verify contracts between real modules.

## Synthetic scientific test

Used to verify model/ledger/data-boundary behavior without consuming protected holdout data.

## Real protected-data evaluation

Only run after:

```text
protocol frozen
        +
implementation tested
        +
preflight passed
        +
explicit execution authorization
```

See:

```text
05_Documentation/Testing_Guide.md
```

---

# Protected Research Boundaries

Do not casually perform any of the following:

* rerun consumed VALIDATION for performance improvement;
* inspect TEST during model development;
* add a candidate after seeing candidate results;
* change thresholds after VALIDATION;
* calibrate probabilities after VALIDATION for this experiment;
* reorder the 331 model features;
* replace the frozen C04 model without creating a new experiment lineage;
* change target semantics while retaining old fingerprints;
* alter RiskEngine to improve ML backtest results.

When uncertain, stop and inspect the relevant contract/evidence file.

---

# Documentation

New contributors should use:

## `05_Documentation/Developer_Guide.md`

Detailed student/developer onboarding manual.

## `05_Documentation/Architecture.md`

System components and data flow.

## `05_Documentation/Development_Roadmap.md`

Completed, current, and remaining engineering gates.

## `05_Documentation/Feature_List.md`

Feature families, portability rules, and input contract.

## `05_Documentation/Module_List.md`

Important Python modules and their responsibilities.

## `05_Documentation/Trading_Rules.md`

Trading, risk, and execution boundaries.

## `05_Documentation/Testing_Guide.md`

How to test safely.

## `05_Documentation/Research_Evidence_Index.md`

Human-readable index of scientific JSON reports and fingerprints.

## `05_Documentation/Troubleshooting.md`

Common project errors and fixes.

## `05_Documentation/Version_History.md`

Major engineering and research milestones.

---

# Remaining Roadmap

Immediate next milestone:

```text
Final one-time TEST infrastructure
        ↓
Dry preflight
        ↓
First and only TEST evaluation
        ↓
Final research verdict
```

After research completion:

```text
Production broker feature parity
        ↓
Broker-time canonicalization
        ↓
D1 reconstruction
        ↓
Frozen-model inference adapter
        ↓
Shadow integration
        ↓
Forward unseen-market validation
        ↓
Production safety review
        ↓
Possible live promotion decision
```

The current project must not be described as live-ready.

---

# Security and Secrets

Never commit:

* MT5 account passwords;
* private API keys;
* access tokens;
* personal credentials;
* production secrets.

Use environment variables or local `.env` files.

`.env.example` should contain example names only, not real credentials.

Before committing:

```powershell
git status --short
```

Review every staged file.

---

# Important Disclaimer

PulseViper is a research and engineering project involving financial-market data and trading infrastructure.

Historical TRAIN, VALIDATION, TEST, or shadow results do not guarantee future profitability.

Any eventual live deployment requires independent risk review, broker testing, forward validation, operational safeguards, and explicit authorization.

Current state:

```text
live_authorized = false
```

---

# Where Should I Start?

If you are a new student or developer:

```text
1. Read this README
2. Read 05_Documentation/Developer_Guide.md
3. Understand Architecture.md
4. Run focused tests
5. Study Research_Evidence_Index.md
6. Pick one isolated development task
7. Never bypass protected-data or runtime safety boundaries
```

The project is designed so that a developer should be able to understand **why** a component exists before changing **how** it works.

<!-- REPOSITORY-ARCHITECTURE-MANAGED:START -->
## Repository Architecture Status

> This section is maintained as part of repository-structure gates.

The canonical top-level project layout is:

- `01_Data/` — canonical project data, datasets, databases, model/data artifacts.
- `02_AI/` — production Python application, intelligence, model, data, risk, and shadow runtime.
- `03_MT5/` — MT5-specific project area.
- `04_Testing/` — tests, diagnostics, research tooling, portability tooling, and testing evidence.
- `05_Documentation/` — project documentation and repository governance material.
- `06_Exports/` — generated exports; intentionally ignored by Git.
- `07_Git/` — reserved project Git-support area.
- `Logs/` — runtime logs; intentionally ignored by Git.

`01_Data/` is the only canonical top-level data directory. The empty duplicate
top-level `Data/` directory was removed after confirming that it contained no
files and had no exact repository references.

Current structured testing areas include:

- `04_Testing/ai/common/`
- `04_Testing/ai/core/`
- `04_Testing/ai/dataset/`
- `04_Testing/ai/objects/`
- `04_Testing/ai/shadow/`
- `04_Testing/evidence/`
- `04_Testing/production_portability/`

Additional restructuring remains controlled and evidence-driven. Frozen
one-time VALIDATION / TEST code and evidence remain compatibility exceptions
and must not be moved, rewritten, or executed merely for repository cleanup.

Repository restructuring does not authorize live or shadow deployment.
<!-- REPOSITORY-ARCHITECTURE-MANAGED:END -->

<!-- V2-READY-18-RELOCATION:START -->
## Source-Aligned READY Test Layout

The V2 READY migration now has 77 source-aligned tests under
`04_Testing/ai/<domain>/`.

The latest gate relocated 18 bootstrap-clean/import-normalized tests. The
original moves were `R100`; one human-readable path header in the config test
was corrected afterward without changing executable Python semantics.

`test_v1_health.py` is the only remaining READY location-sensitive test.
<!-- V2-READY-18-RELOCATION:END -->
