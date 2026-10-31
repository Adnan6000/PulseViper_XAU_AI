# Contributing to PulseViper XAU AI

Thank you for considering a contribution to PulseViper XAU AI.

PulseViper is a research-first XAUUSD machine-learning and trading-infrastructure project with strict scientific, testing, and execution-safety boundaries.

Please read this document before modifying the project.

---

## Read the Documentation First

Before making substantial changes, review:

1. `README.md`
2. `05_Documentation/Developer_Guide.md`
3. `05_Documentation/Architecture.md`
4. `05_Documentation/Testing_Guide.md`
5. `05_Documentation/Research_Evidence_Index.md`

For trading-related changes also review:

- `05_Documentation/Trading_Rules.md`
- `05_Documentation/Feature_List.md`
- `05_Documentation/Module_List.md`

---

## Protected Research Boundaries

The project uses strict TRAIN, VALIDATION, and TEST separation.

Unless a dedicated engineering or research task explicitly authorizes it, contributors must not:

- rerun consumed VALIDATION for performance tuning;
- inspect or consume final TEST during model development;
- tune model thresholds after VALIDATION;
- perform post-validation probability calibration;
- reorder the frozen 331-feature contract;
- change target semantics while keeping the previous experiment identity;
- replace the frozen model while presenting it as the same experiment;
- modify RiskEngine simply to improve model performance metrics;
- bypass scientific fingerprints or artifact verification;
- describe the project as live-ready.

When scientific provenance, dataset identity, feature order, model identity, or protected-data state cannot be proven, stop rather than continue with an uncertain state.

---

## Development Setup

Clone the repository:

```powershell
git clone https://github.com/Adnan6000/PulseViper_XAU_AI.git
cd PulseViper_XAU_AI
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

---

## Branch Naming

Use descriptive branch names.

Examples:

```text
fix/data-loader-boundary
feature/shadow-inference-adapter
docs/testing-guide-update
test/risk-engine-contract
refactor/feature-pipeline
```

Keep each branch and pull request focused on one coherent change.

---

## Testing

At minimum, run the tests related to your change.

Syntax check:

```powershell
python -m py_compile path\to\file.py
```

Focused test:

```powershell
python -m pytest path\to\test_file.py -q
```

Do not execute:

- protected-data evaluations;
- one-time validation/test workflows;
- MT5-connected operations;
- expensive research experiments;

unless the task explicitly requires and authorizes them.

---

## Scientific Integrity

If your change affects research behavior, document whether it changes:

- feature ordering;
- dataset identity;
- target semantics;
- model configuration;
- experiment lineage;
- artifact fingerprints;
- candidate selection;
- thresholds;
- calibration;
- VALIDATION status;
- TEST status.

Scientific evidence should be reproducible whenever possible.

---

## Security

Never commit:

- MT5 passwords;
- API keys;
- access tokens;
- broker credentials;
- private account numbers;
- production secrets;
- private keys;
- real `.env` files.

Use environment variables or safe local configuration.

Before committing:

```powershell
git status --short
```

Review every staged file carefully.

---

## Pull Requests

A pull request should clearly explain:

- what changed;
- why the change was required;
- which components were affected;
- which tests were executed;
- whether scientific fingerprints changed;
- whether VALIDATION or TEST was accessed;
- whether broker-facing behavior changed;
- whether risk or execution behavior changed;
- any limitations or follow-up work.

Use the repository pull request template.

---

## Documentation

Update documentation whenever a change affects:

- architecture;
- feature contracts;
- model behavior;
- testing procedures;
- data flow;
- risk controls;
- execution behavior;
- security;
- project status;
- development roadmap.

---

## Financial Research Disclaimer

PulseViper is software-engineering and financial-market research software.

Historical TRAIN, VALIDATION, TEST, backtest, or shadow results do not guarantee future profitability.

Any future live deployment requires separate authorization, operational review, broker testing, forward validation, and risk-control verification.