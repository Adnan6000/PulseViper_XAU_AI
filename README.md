# PulseViper XAU AI

**PulseViper XAU AI** is an AI-driven research and automated trading system focused on **XAUUSD (Gold)**.

The project combines quantitative feature engineering, institutional-style market structure analysis, liquidity concepts, trade-quality scoring, risk management, machine learning, ONNX deployment, and MetaTrader 5 integration into a modular trading research architecture.

> **Status:** Active development and research project.
> This repository is intended for software engineering, quantitative research, testing, and educational purposes.

---

## Core Objectives

PulseViper is being designed to transform raw XAUUSD market data into structured trading intelligence through a layered pipeline:

```text
XAUUSD / MT5 Data
        ↓
Feature Engineering
        ↓
Market Structure
        ↓
Liquidity Analysis
        ↓
Liquidity Sweeps
        ↓
Displacement
        ↓
BOS / Structural Events
        ↓
Fair Value Gaps
        ↓
FVG Quality & Mitigation
        ↓
Market Regime
        ↓
Confidence Engine
        ↓
Risk Engine
        ↓
Trade Decision
        ↓
MT5 Execution
        ↓
Trade Logging & Learning Data
```

---

## Current Architecture

### Data Layer

Responsible for:

* MetaTrader 5 historical data acquisition
* Multi-timeframe XAUUSD datasets
* Data validation
* Resume-safe historical downloads
* CSV export
* SQLite persistence
* Dataset preparation

### Feature Engineering

The feature layer is designed around reusable market evidence including:

* Trend
* Momentum
* Volatility
* Candle behaviour
* Structural context

Feature ordering and model contracts are explicitly controlled to prevent accidental ML input drift.

### Institutional Market Intelligence

PulseViper contains modular engines for:

* Swing and pivot detection
* HH / HL / LH / LL market structure
* Liquidity identification
* Liquidity sweeps
* Sweep validation
* Displacement
* Break of Structure
* BOS memory
* Fair Value Gaps
* FVG mitigation
* FVG quality
* Institutional zones
* Persistent structure state

Each engine is designed to own one responsibility rather than duplicating logic across the system.

### Confidence Engine

The Confidence Engine aggregates upstream market evidence to evaluate trade quality.

It does not independently rediscover indicators or institutional events. Instead, it consumes validated signals produced by dedicated engines.

### Risk Engine

The Risk Engine manages:

* Risk per trade
* Small-account risk handling
* Position sizing
* Lot-size validation
* Stop-loss validation
* Take-profit validation
* Risk/reward calculations
* Maximum exposure protection

### Machine Learning

The planned ML pipeline includes:

* Structured dataset generation
* Feature contract versioning
* Label generation
* Time-series-aware validation
* Model training
* Evaluation
* Optimization
* ONNX export
* MT5-compatible inference

Special attention is given to preventing look-ahead bias and training-data leakage.

### MetaTrader 5 Integration

The final execution layer is designed to support:

* ONNX model inference
* Trade filtering
* Risk-aware position sizing
* Stop-loss and take-profit placement
* Execution safeguards
* Trade logging
* Demo/forward validation
* Future learning-data collection

---

## Engineering Principles

PulseViper follows several development rules:

* One responsibility per engine
* No unnecessary duplicate calculations
* Deterministic unit testing
* Integration testing between engines
* Explicit feature contracts
* No silent model-input changes
* Look-ahead leakage prevention
* Risk-first execution design
* Git checkpoints after stable development stages
* Real XAUUSD validation before production decisions

---

## Project Structure

```text
PulseViper_XAU_AI/
│
├── 01_Data/
│   ├── Raw/
│   ├── Processed/
│   ├── Labels/
│   └── Backups/
│
├── 02_AI/
│   ├── Common/
│   ├── Config/
│   ├── Core/
│   ├── Database/
│   ├── Dataset/
│   ├── Features/
│   ├── Memory/
│   ├── Objects/
│   ├── Trainer/
│   └── Utils/
│
├── 03_MT5/
│   ├── Experts/
│   ├── Include/
│   ├── Indicators/
│   └── Scripts/
│
├── 04_Testing/
├── 05_Documentation/
├── 06_Exports/
├── 07_Git/
└── Logs/
```

---

## Development Workflow

The project is developed using a test-first and checkpoint-based workflow:

```text
Audit existing implementation
        ↓
Add deterministic tests
        ↓
Reproduce defects
        ↓
Apply minimum safe fix
        ↓
Run focused tests
        ↓
Run integration tests
        ↓
Run full project suite
        ↓
Validate against real XAUUSD data
        ↓
Git checkpoint
```

---

## Author

### Muhammad Adnan

**BSIT Graduate | Full Stack Software Engineer | Certified Ethical Hacker (CEH) | Forex Trader**

Additional areas of work and expertise include:

* AI Integration & Automation
* Backend Engineering
* Full Stack Development
* Cybersecurity
* Algorithmic Trading Research
* Server Deployment & Administration
* API Development & Integration
* Database Systems
* Project Planning & Management
* Software Architecture

GitHub: **@Adnan6000**

PulseViper represents the intersection of software engineering, artificial intelligence, cybersecurity, quantitative market research, and automated trading systems.

---

## Risk Disclaimer

PulseViper XAU AI is a research and software-development project.

Nothing in this repository should be interpreted as financial advice, an investment recommendation, or a guarantee of profitability.

Trading Forex, Gold, CFDs, leveraged products, and other financial instruments involves substantial risk and may result in significant financial loss.

Any live deployment should only occur after extensive testing, backtesting, out-of-sample validation, walk-forward analysis, and controlled demo/forward testing.
