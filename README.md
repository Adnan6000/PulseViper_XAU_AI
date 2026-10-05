# PulseViper XAU AI

An AI-assisted XAUUSD trading system being developed for controlled real-money live trading, using research-first validation, broker calibration, risk management, and documented evidence gates.

> **Disclaimer:** This project is for educational, research, and automation purposes only. It does not provide financial advice and does not guarantee trading outcomes.

## What This Project Does

PulseViper is an engineering project that combines:

- Historical XAUUSD data processing
- Portable feature engineering (331 features)
- Machine-learning models (currently ExtraTrees classifier)
- Risk management and safety checks
- Shadow trading and MetaTrader 5 integration research

The ultimate goal is controlled real-money live trading. Research, testing, shadow validation, broker calibration, and evidence gates are the engineering methodology used to decide what may be promoted into live production.

## Live Trading Objective

PulseViper is being developed for **controlled real-money live XAUUSD trading** under explicit risk, account-protection, execution, and operational controls.

The development lifecycle is:

```text
Research → Implement → Offline/Test → Shadow → Demo → Forward Validation → Broker Calibration → Risk & Execution Validation → Controlled Production Promotion → Live Trading → Continuous Monitoring
```

The current live state remains **not authorized** until the defined historical, forward, risk, execution, recovery, and operational gates are completed. This is a temporary authorization state, not the project's final objective.

## Authoritative Current State (2026-10-05)

The repository has progressed beyond the original C04-only forward-validation phase.

```text
Historical C04 forward baseline
        ↓
30 matured forward outcomes
        ↓
Weak forward discrimination
        ↓
G7-A → G7-B → G7-C → G7-D → G7-E
        ↓
G7-F-A TRAIN + VALIDATION access
        ↓
G7-F-B six-candidate evaluation
        ↓
G7-F-C R03 winner freeze
        ↓
G7-G-A sealed TEST criteria
        ↓
G7-G-B one-shot sealed TEST
        ↓
G7-H R03 prospective forward lane
        ↓
CURRENT: first genuine R03 capture blocked
```

Current remediation winner:

```text
R03_FLAT_EXTRA_TREES_SMOOTH
```

Historical C04 remains preserved as the control lineage.

Current R03 prospective collection state:

```text
observations = 0
anchors = 0
matured_outcomes = 0
distinct_matured_utc_dates = 0
minimum_matured_outcomes = 60
minimum_distinct_utc_dates = 5
```

The latest first-capture/recovery attempts remain fail-closed because the broker timestamp basis could not be uniquely proven:

```text
TIMESTAMP_BASIS_NOT_UNIQUELY_PROVEN
raw_tick=1790985539
candidate_count=0
```

No prospective observation or anchor has been fabricated or backfilled.

```text
live_authorized = false
execution_authorized = false
performance_evaluated = false
pnl_evaluated = false
```

The next engineering action is to establish a valid timestamp basis or obtain a valid fresh capture context, then execute the already-frozen R03 capture lane.

## Key Highlights

- **331 portable features** with frozen order and SHA256 fingerprint (`65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2`)
- **Historical C04 control lineage:** `C04_FLAT_EXTRA_TREES_CONSTRAINED` remains frozen as the original baseline.
- **G7 remediation registry:** exactly 6 candidates frozen under G7-E; no post-result candidate replacement is allowed in that experiment.
- **G7-F-B:** six remediation candidates evaluated using the authorized TRAIN + VALIDATION remediation boundary.
- **G7-F-C:** remediation winner frozen as `R03_FLAT_EXTRA_TREES_SMOOTH`.
- **G7-G-B:** one-shot sealed TEST for R03 completed and confirmed; TEST rerun is permanently blocked.
- **G7-H:** R03 prospective forward-validation contract, train-only artifact, runtime binding, outcome maturation, collection controller, and first-capture recovery lanes are frozen.
- **Current R03 forward collection:** no genuine R03 observation has yet been persisted; first capture is currently blocked by an unresolved unique timestamp-basis condition.
- **Live trading / execution:** NOT AUTHORIZED (`live_authorized = false`, `execution_authorized = false`)

## Tech Stack

- Python
- scikit-learn (ExtraTreesClassifier)
- MetaTrader 5 (research integration)
- YAML-based configuration
- pytest-based testing suite
- Structured documentation under `05_Documentation/`

## Repository Structure

- `01_Data/` — datasets, databases, model artifacts
- `02_AI/` — feature pipelines, models, risk, shadow runtime
- `04_Testing/` — unit, integration, and scientific tests
- `05_Documentation/` — developer guides, architecture, roadmap, testing, evidence index
- `config.yaml`, `requirements.txt`, `.env.example`

## Who Is This For?

- Developers interested in ML pipelines, trading-system engineering, risk, execution, and structured research
- Students who want to study a real, safety-gated XAUUSD trading codebase
- Engineers exploring reproducible ML experiments, broker integration, and protected holdouts

New contributors should start with:

1. This README
2. `05_Documentation/Developer_Guide.md`
3. `05_Documentation/Architecture.md`
4. `05_Documentation/Testing_Guide.md`

## Security & Best Practices

- No secrets or credentials in the repository
- `.env` files ignored; only `.env.example` committed
- Protected VALIDATION and TEST splits must not be reused for tuning
- Execution safety (RiskEngine, MT5 logic) is separate from ML research

## Author

Muhammad Adnan  
Full-Stack Software Engineer | CEH  
[LinkedIn](https://www.linkedin.com/in/muhammadadnan001/) | [GitHub](https://github.com/Adnan6000)

---

## Detailed Technical Documentation

*(Original detailed README continues below for technical readers and contributors.)*

---

PulseViper XAU AI
=================

A research-first, safety-gated Python trading system for **canonical XAUUSD research and broker-agnostic multi-broker deployment**, with controlled real-money live trading as the eventual production objective.

> **Current status:** R03 remediation winner frozen; sealed TEST confirmed; prospective R03 forward-validation lane is active but the first genuine capture is currently blocked by an unresolved timestamp-basis proof condition.
> **Latest engineering/protocol HEAD before this documentation synchronization:** `c5ec7069a4dff846d663bee05c862f38f9e8b891`
> **Historical C04 baseline:** `C04_FLAT_EXTRA_TREES_CONSTRAINED` remains preserved as the original frozen control lineage.
> **Current remediation winner:** `R03_FLAT_EXTRA_TREES_SMOOTH`
> **Feature contract:** 331 ordered portable features
> **Sealed TEST:** G7-G-B one-shot confirmation PASSED; rerun prohibited
> **R03 forward contract:** minimum 60 matured outcomes across at least 5 distinct UTC observation dates
> **Current R03 capture state:** 0 observations, 0 anchors, 0 matured outcomes; first capture blocked by `TIMESTAMP_BASIS_NOT_UNIQUELY_PROVEN`
> **Live trading / execution:** NOT AUTHORIZED (`live_authorized = false`, `execution_authorized = false`)

Table of Contents
-----------------

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

What Is PulseViper?
===================

PulseViper is an engineering and research project focused on developing a reproducible XAUUSD machine-learning trading system.

The project is not only a model, and it is not intended to remain research-only.

It includes multiple independent layers:

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

Each layer has its own responsibility.

A good ML result does **not** automatically authorize live trading.

Project Philosophy
==================

PulseViper follows several core engineering principles.

1. Research must be reproducible
--------------------------------

Important datasets, feature contracts, models, experiments, and decisions are identified using SHA256 fingerprints.

For example, the current frozen model artifact has a specific SHA256.

Changing the artifact means it is no longer the same experiment.

2. TRAIN, VALIDATION, and TEST have different jobs
---------------------------------------------------

TRAIN   — Used for fitting and model research  
VALIDATION — Used once after research decisions are frozen  
TEST    — Final untouched estimate of generalization  

TEST must never become another tuning dataset.

3. Protected holdouts are one-time scientific assets
-----------------------------------------------------

The current VALIDATION split has already been consumed.

It may not be rerun for performance-driven tuning.

The final TEST split is still protected.

4. Execution safety is separate from ML research
-------------------------------------------------

The following runtime areas are treated as frozen unless a dedicated engineering task explicitly authorizes modification:

- MT5 order/execution semantics
- RiskEngine
- `trade_ready`
- account protection
- broker-aware sizing
- core execution logic
- shadow execution semantics

Research code should not modify these components just to improve model metrics.

5. Fail closed
---------------

When artifact identity, feature order, dataset identity, protected-data state, or scientific provenance cannot be proven, the preferred behavior is to stop rather than continue with uncertain state.

Current Research Status
=======================

The original C04 research/forward lineage is historical and preserved. The active remediation lineage is R03.

Completed remediation milestones:

1. G7-A remediation rules freeze
2. G7-B remediation data authority freeze
3. G7-C exact training snapshot freeze
4. G7-D remediation research protocol freeze
5. G7-E six-candidate registry freeze
6. G7-F-A TRAIN + VALIDATION access freeze
7. G7-F-B six-candidate evaluation
8. G7-F-C R03 final winner freeze
9. G7-G-A sealed TEST confirmation criteria
10. G7-G-B one-shot sealed TEST confirmation
11. G7-H-A R03 prospective forward contract
12. G7-H-B R03 train-only artifact
13. G7-H-C prospective runtime binding
14. G7-H-D outcome maturation binding
15. G7-H-E-A collection controller
16. G7-H-E-B first-capture runner and recovery lanes

Current status:

```text
R03 winner = R03_FLAT_EXTRA_TREES_SMOOTH
R03 sealed TEST = SEALED_TEST_CONFIRMED
R03 forward observations = 0
R03 forward anchors = 0
R03 matured outcomes = 0
R03 formal forward evaluation = false
R03 formal PnL evaluation = false
live_authorized = false
execution_authorized = false
```

The first genuine R03 capture remains blocked by `TIMESTAMP_BASIS_NOT_UNIQUELY_PROVEN`. This is a preserved scientific/safety block; the timestamp check must not be weakened.

Historical C04 remains useful as the control/baseline lineage and must not be silently relabeled as the current production model.

Runtime Observation Ledger Status
---------------------------------

Operational runtime ledger:

```text
01_Data/Shadow/xauusd_frozen_c04_shadow_observations.jsonl
```

- Append-only, local, gitignored, immutable operational history.
- Must never be truncated, rewritten, deleted for cleanup, or committed.
- Known `TRUE_FORWARD` observation count: **2**

1. **Observation 1 (Decision time `2026-09-28T10:15:00Z`)**:
   - Acquired during Gate 15B-B.
   - Pre-contract observation (captured prior to Gate 15C activation `2026-09-28T11:16:59Z`).
   - Retained permanently for pipeline audit; strictly excluded from formal forward performance.

2. **Observation 2 (Decision time `2026-09-28T11:45:00Z`)**:
   - Acquired during Gate 15D-B as genuine post-contract acquisition proof.
   - **NOT FORMALLY SCOREABLE**: Did not receive a prospective frozen outcome anchor at acquisition time.
   - Status: `POST_CONTRACT_ACQUISITION_PROOF_EXCLUDED_FROM_FORMAL_SCORING_MISSING_PROSPECTIVE_ANCHOR`.
   - The genuine acquisition proof is retained, but no outcome anchor will ever be retroactively manufactured for it.

Formal Forward Scoring Requirements
-----------------------------------

Under the active Maturer V2 / Outcome Ledger V2 authority, an observation is formally scoreable **only if all 11 conditions are satisfied**:

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

System Overview
===============

The research-to-production flow is:

Historical XAUUSD Data  
↓  
Portable Feature Pipeline (331 features)  
↓  
Train-Internal Research & Selection (C04 winner)  
↓  
Full TRAIN Fit & Verification  
↓  
Untouched VALIDATION (Passed & Frozen)  
↓  
Final TEST (Protected Holdout)  
↓  
Gate 13: Production Broker Feature Parity (COMPLETE)  
↓  
Gate 14: Frozen Offline Inference Adapter (COMPLETE)  
↓  
Gate 15A: Forward Shadow Observation Infrastructure (COMPLETE)  
↓  
Gate 15B-A: MT5 Read-Only Acquisition Adapter v2.1.0 (COMPLETE)  
↓  
Gate 15C: Frozen Forward Outcome Contract V1 (COMPLETE)  
↓  
Gate 15D-A: Prospective Eligibility Authority (COMPLETE)  
↓  
Gate 15D-C-B2A: Prospective Outcome Anchor Authority V1 (COMPLETE)  
↓  
Gate 15D-C-B2B/C: Maturer V2 & Outcome Ledger V2 (COMPLETE)  
↓  
Gate 15D-C-B2D: Prospective Observation + Same-Snapshot Anchor Integration (🟢 NEXT)  
↓  
Gate 15E: Matured Forward Shadow Evaluation (PENDING)  
↓  
Possible Live Promotion Decision (⛔ NOT AUTHORIZED)

The current project position is:

GATE 15D-C-B2BC PUBLISHED BASELINE (`cbdeb30934213dc36863c334eb1e50879ba0dde1`)  
↓  
GATE 15D-C-B2D PREPARATION (Prospective Observation + Same-Snapshot Anchor Integration)  

Repository Structure
====================

The main repository areas are conceptually:

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

See `05_Documentation/Developer_Guide.md` before making substantial changes.

Machine-Learning Pipeline
=========================

Target Classes
--------------

The main classifier uses three classes:

-1 = SHORT  
 0 = NO_TRADE  
 1 = LONG  

The binary tradeability relationship must remain:

target_tradeable = (target_class != 0)

Frozen Portable Feature Count
-----------------------------

Current model input:

331 features

Frozen ordered feature-list fingerprint:

65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2

Feature order matters.

Two matrices may both contain 331 columns and still represent completely different model inputs if their column order differs.

Frozen TRAIN Dataset
--------------------

Dataset ID: portable_cff75b0686383a3ab6f8352b  
TRAIN rows: 69,966  
Feature count: 331  

Dataset SHA256:

cff75b0686383a3ab6f8352bfcdcd55308b99b7a4c6edbf7d2e7215f6f33dd07

Manifest SHA256:

1b8e3599b227c9cbbc6b12f8ab0e275ca4deb4a65839fb626ca90720d59512dc

Current Frozen Model
====================

TRAIN-internal winner:

C04_FLAT_EXTRA_TREES_CONSTRAINED

Model family:

sklearn.ensemble.ExtraTreesClassifier

Frozen configuration:

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

Frozen candidate configuration fingerprint:

f1b11c6f91561f2eba1bd56195e2239e9598b1906c88f11ada67eac6cdeb09e3

Model artifact:

xauusd_portable_331_c04_full_train_model.joblib

Artifact SHA256:

48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769

Prediction class order:

[-1, 0, 1]

Prediction rule:

probabilities = model.predict_proba(X)
prediction = model.classes_[probabilities.argmax(axis=1)]

Supported symbols:

- `XAUUSD` (primary)
- `XAUUSDm` (micro / fallback)

Historical research freeze boundary:

`2026-08-14T20:55:00Z`

Gate 15A activation:

`2026-09-06T13:20:00Z`

No post-validation threshold tuning or probability calibration is allowed for this frozen experiment.

Validation Result
=================

The frozen C04 model completed its first and only untouched VALIDATION evaluation.

Status:

ONE_TIME_VALIDATION_ACCEPTED

Important metrics:

| Metric                  | Result   |
|-------------------------|----------|
| Balanced accuracy       | 0.376568 |
| Macro-F1                | 0.348904 |
| Directional macro-F1    | 0.336403 |
| SHORT precision         | 0.329373 |
| SHORT recall            | 0.319050 |
| SHORT F1                | 0.324129 |
| LONG precision          | 0.259975 |
| LONG recall             | 0.529249 |
| LONG F1                 | 0.348676 |
| NO_TRADE recall         | 0.281404 |
| Predicted trade coverage| 0.754121 |
| Log-loss                | 1.097919 |
| Multiclass Brier        | 0.666429 |

All predeclared hard validation requirements passed.

Validation result fingerprint:

ea8b482e60f854f58e27f3be387b7bb82f0c16a6cf1a99555b12643aeeca5fa1

Validation-result freeze fingerprint:

521a97b41a86231b049cc65aebfd85ffc7c83ae7141134d6ae1158d112b1468c

Important:

validation_consumed = true  
validation_rerun_authorized = false  

Quick Start for Students
========================

Step 1 — Clone the repository
-----------------------------

git clone https://github.com/Adnan6000/PulseViper_XAU_AI.git
cd PulseViper_XAU_AI

Step 2 — Create a virtual environment
-------------------------------------

Windows:

python -m venv .venv

Activate:

.venv\Scripts\Activate.ps1

Step 3 — Install dependencies
-----------------------------

python -m pip install -r requirements.txt

Step 4 — Read the documentation
-------------------------------

Recommended order:

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

Step 5 — Do not start with live execution
-----------------------------------------

A new developer should begin with:

1. reading tests;
2. running focused synthetic tests;
3. understanding research evidence;
4. modifying isolated research utilities;
5. only later working on runtime integration.

Development Workflow
====================

PulseViper uses finite engineering gates.

Typical workflow:

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

Example:

python -m py_compile 04_Testing\exact_script.py

Then:

python -m pytest 04_Testing\test_exact_script.py -q

Use exact filenames.

Do not use placeholder commands such as:

python SCRIPT_NAME.py

Testing
=======

Different tests protect different things.

Syntax check
------------

python -m py_compile path\to\file.py

Focused unit test
-----------------

python -m pytest path\to\test_file.py -q

Integration test
----------------

Used to verify contracts between real modules.

Synthetic scientific test
-------------------------

Used to verify model/ledger/data-boundary behavior without consuming protected holdout data.

Real protected-data evaluation
------------------------------

Only run after:

protocol frozen + implementation tested + preflight passed + explicit execution authorization

See:

05_Documentation/Testing_Guide.md

Protected Research Boundaries
=============================

Do not casually perform any of the following:

- rerun consumed VALIDATION for performance improvement;
- inspect TEST during model development;
- add a candidate after seeing candidate results;
- change thresholds after VALIDATION;
- calibrate probabilities after VALIDATION for this experiment;
- reorder the 331 model features;
- replace the frozen C04 model without creating a new experiment lineage;
- change target semantics while retaining old fingerprints;
- alter RiskEngine to improve ML backtest results.

When uncertain, stop and inspect the relevant contract/evidence file.

Documentation
=============

New contributors should use:

05_Documentation/Developer_Guide.md
-----------------------------------

Detailed student/developer onboarding manual.

05_Documentation/Architecture.md
--------------------------------

System components and data flow.

05_Documentation/Development_Roadmap.md
---------------------------------------

Completed, current, and remaining engineering gates.

05_Documentation/Feature_List.md
--------------------------------

Feature families, portability rules, and input contract.

05_Documentation/Module_List.md
-------------------------------

Important Python modules and their responsibilities.

05_Documentation/Trading_Rules.md
---------------------------------

Trading, risk, and execution boundaries.

05_Documentation/Testing_Guide.md
---------------------------------

How to test safely.

05_Documentation/Research_Evidence_Index.md
-------------------------------------------

Human-readable index of scientific JSON reports and fingerprints.

05_Documentation/Troubleshooting.md
-----------------------------------

Common project errors and fixes.

05_Documentation/Version_History.md
-----------------------------------

Major engineering and research milestones.

Remaining Roadmap
=================

Immediate active phase:

```text
R03 prospective forward collection
        ↓
resolve timestamp-basis proof
        ↓
genuine anchor-first observation capture
        ↓
mature at least 60 outcomes across at least 5 UTC observation dates
        ↓
prospective R03 performance evaluation
        ↓
production safety / monitoring review
        ↓
controlled live-promotion review
```

The following remain prohibited in the current R03 lane:

- rerunning sealed TEST;
- tuning R03 from prospective observations;
- using the old 30 Forward30 outcomes for remediation development;
- fabricating or backfilling prospective anchors;
- weakening timestamp validation;
- enabling live execution.

The project is **not live-ready** and **not execution-authorized**.

Security and Secrets
====================

Never commit:

- MT5 account passwords;
- private API keys;
- access tokens;
- personal credentials;
- production secrets.

Use environment variables or local `.env` files.

`.env.example` should contain example names only, not real credentials.

Before committing:

git status --short

Review every staged file.

Important Disclaimer
====================

PulseViper is a research and engineering project involving financial-market data and trading infrastructure.

Historical TRAIN, VALIDATION, TEST, or shadow results do not guarantee future profitability.

Any eventual live deployment requires independent risk review, broker testing, forward validation, operational safeguards, and explicit authorization.

Current state:

live_authorized = false

Where Should I Start?
=====================

If you are a new student or developer:

1. Read this README  
2. Read 05_Documentation/Developer_Guide.md  
3. Understand Architecture.md  
4. Run focused tests  
5. Study Research_Evidence_Index.md  
6. Pick one isolated development task  
7. Never bypass protected-data or runtime safety boundaries  

The project is designed so that a developer should be able to understand **why** a component exists before changing **how** it works.

Repository Architecture Status
------------------------------

The canonical top-level project layout is:

- `01_Data/` — canonical project data, datasets, databases, model/data artifacts.
- `02_AI/` — production Python application, intelligence, model, data, risk, and shadow runtime.
- `03_MT5/` — MT5-specific project area.
- `04_Testing/` — tests, diagnostics, research tooling, portability tooling, and testing evidence.
- `05_Documentation/` — project documentation and repository governance material.
- `06_Exports/` — generated exports; intentionally ignored by Git.
- `07_Git/` — reserved project Git-support area.
- `Logs/` — runtime logs; intentionally ignored by Git.

`01_Data/` is the only canonical top-level data directory. The empty duplicate top-level `Data/` directory was removed after confirming that it contained no files and had no exact repository references.

Current structured testing areas include:

- `04_Testing/ai/common/`
- `04_Testing/ai/core/`
- `04_Testing/ai/dataset/`
- `04_Testing/ai/objects/`
- `04_Testing/ai/shadow/`
- `04_Testing/evidence/`
- `04_Testing/production_portability/`

Additional restructuring remains controlled and evidence-driven. Frozen one-time VALIDATION / TEST code and evidence remain compatibility exceptions and must not be moved, rewritten, or executed merely for repository cleanup.

Repository restructuring does not authorize live or shadow deployment.

Source-Aligned READY Test Layout
--------------------------------

The V2 READY migration now has 77 source-aligned tests under `04_Testing/ai//`.

The latest gate relocated 18 bootstrap-clean/import-normalized tests. The original moves were `R100`; one human-readable path header in the config test was corrected afterward without changing executable Python semantics.

`test_v1_health.py` is the only remaining READY location-sensitive test.

V2 READY Structural Migration Complete
--------------------------------------

All 78 V2 READY tests now live in source-aligned `04_Testing/ai//` locations.

The final root-sensitive V1 health test was migrated only after replacing its file-depth-derived repository root with the shared `repo_root` pytest fixture.

`04_Testing/conftest.py` now discovers repository root from stable repository markers instead of a fixed parent index.

Reviewed Integration Test Layout
--------------------------------

The first V2 REVIEW_REQUIRED execution batch has moved two independently verified cross-domain tests into `04_Testing/integration/`.

These are separate from the 78 completed READY source-aligned tests and are tracked as REVIEW_EXECUTED rather than retroactively reclassified as READY.

Standalone Diagnostics
----------------------

Historical root-level `test_logger.py` and `test_settings.py` were not pytest tests. They executed logger/configuration diagnostics at module import time.

They now live under `04_Testing/diagnostics/` with descriptive names and explicit `main()` entrypoints.
