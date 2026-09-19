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

Create a virtual environment:

```powershell
python -m venv .venv

Activate it:

```powershell
.venv\Scripts\Activate

Install dependencies:

```powershell
pip install -r requirements.txt
