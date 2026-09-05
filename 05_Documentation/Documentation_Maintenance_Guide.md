# PulseViper XAU AI — Documentation Maintenance Guide

## 1. Purpose

This guide defines how PulseViper documentation should be maintained.

The project contains:

```text
Python source code
machine-readable research evidence
model artifacts
Git history
human-readable Markdown documentation
```

These sources serve different purposes.

The goal of documentation maintenance is to keep them consistent without creating duplicate authoritative contracts.

---

# 2. Documentation Principle

Documentation should help a new developer answer:

```text
What does the system do?

Why does it work this way?

Where is the implementation?

What is frozen?

What can I safely modify?

How do I test it?

What evidence supports the current state?
```

A document that only lists filenames is not enough.

---

# 3. Source-of-Truth Hierarchy

Different information has different authoritative sources.

## Scientific artifact identity

Authoritative:

```text
machine-readable frozen evidence
```

Examples:

```text
dataset SHA
feature SHA
model SHA
result fingerprint
ledger state
```

---

## Exact feature order

Authoritative:

```text
frozen machine-readable manifest
```

Not a manually copied Markdown list.

---

## Runtime behavior

Authoritative:

```text
current source code
+
current runtime configuration
```

Documentation explains it but should not invent unverified numerical settings.

---

## Project history

Authoritative:

```text
Git history
+
frozen research evidence
```

Markdown summarizes these sources.

---

# 4. Documentation Structure

Recommended repository documentation:

```text
README.md

05_Documentation/
├── Developer_Guide.md
├── Architecture.md
├── Development_Roadmap.md
├── Feature_List.md
├── Module_List.md
├── Trading_Rules.md
├── Testing_Guide.md
├── Research_Evidence_Index.md
├── Troubleshooting.md
├── Version_History.md
└── Documentation_Maintenance_Guide.md
```

Each file has a distinct job.

---

# 5. `README.md`

Purpose:

```text
5–10 minute orientation
```

Should answer:

```text
What is PulseViper?
What is current status?
Where should a new student start?
What major safety boundaries exist?
```

Do not turn README into a 100-page technical manual.

Detailed material belongs in `05_Documentation/`.

---

# 6. `Developer_Guide.md`

Purpose:

```text
main student/developer handbook
```

Should teach:

```text
project mental model
development workflow
research rules
examples
Git discipline
definition of done
```

This is the primary onboarding document.

---

# 7. `Architecture.md`

Purpose:

```text
system ownership and data flow
```

Should explain:

```text
data
features
dataset
ML research
model
risk
shadow
execution
```

A developer should use this file to determine which layer owns a proposed change.

---

# 8. `Development_Roadmap.md`

Purpose:

```text
live project status
```

Should contain:

```text
completed
current
pending
blocked
estimated remaining work
```

This is one of the most frequently updated documents.

---

# 9. `Feature_List.md`

Purpose:

```text
feature semantics and portability education
```

Important rule:

> Do not manually duplicate all authoritative feature names if a machine-readable manifest already owns the exact list.

This reduces documentation drift.

---

# 10. `Module_List.md`

Purpose:

```text
developer module map
```

Every important module entry should explain:

```text
responsibility
input
output
dependencies
safety level
modification consequences
```

---

# 11. `Trading_Rules.md`

Purpose:

```text
explain trading safety boundaries
```

Should clearly distinguish:

```text
prediction
permission
risk
execution
```

Do not document unverified risk numbers as facts.

---

# 12. `Testing_Guide.md`

Purpose:

```text
how to verify development safely
```

Should distinguish:

```text
compile
unit
synthetic
integration
protected holdout
regression
shadow
```

---

# 13. `Research_Evidence_Index.md`

Purpose:

```text
human map of machine-readable evidence
```

Every major research gate should eventually be traceable through this file.

---

# 14. `Troubleshooting.md`

Purpose:

```text
failure diagnosis and recovery
```

Include real recurring problems rather than generic Python advice.

Examples:

```text
JSON encoding
fingerprint mismatch
feature mismatch
ledger state
package import
PowerShell errors
```

---

# 15. `Version_History.md`

Purpose:

```text
why the project evolved
```

It should preserve:

```text
successful milestones
failed research directions
major lessons
frozen transitions
```

Do not rewrite history just because an experiment was unsuccessful.

---

# 16. Documentation Update Triggers

Update documentation when any of these change:

```text
current project status
feature contract
target contract
dataset identity
model identity
research protocol
holdout state
trading architecture
module responsibilities
testing process
production architecture
authorization state
```

---

# 17. Changes That Usually Do Not Need Broad Documentation Updates

Examples:

```text
internal variable rename
test fixture cleanup
comment correction
minor performance optimization
```

provided public/scientific behavior is unchanged.

A brief version-control record may be enough.

---

# 18. Scientific State Must Be Consistent Everywhere

Example incorrect state:

```text
README:
VALIDATION passed

Roadmap:
VALIDATION pending

Evidence:
VALIDATION accepted and consumed
```

This confuses students.

After a major scientific gate, search documentation for stale status terms.

---

# 19. Example Documentation Consistency Search

PowerShell:

```powershell
Get-ChildItem -Recurse -Filter *.md | Select-String -Pattern "VALIDATION"
```

Review whether old statements such as:

```text
VALIDATION pending
```

still exist.

Do not mechanically replace all text.

Historical sections may intentionally describe an earlier state.

---

# 20. Search for Old Feature Counts

Current feature count:

```text
331
```

Legacy documentation may contain:

```text
333
```

Use:

```powershell
Get-ChildItem -Recurse -Filter *.md | Select-String -Pattern "333"
```

Do not automatically delete every reference.

Historical V3/V4 sections may legitimately describe 333 features.

The document should clearly mark them as historical.

---

# 21. Search for Live Authorization Claims

Current state:

```text
live_authorized = false
```

Search:

```powershell
Get-ChildItem -Recurse -Filter *.md | Select-String -Pattern "live_authorized|live ready|live-ready"
```

Review every claim.

Historical or future roadmap descriptions may mention live readiness, but current state must not falsely claim authorization.

---

# 22. Search for TEST Claims

Current portable C04 TEST:

```text
untouched
```

Search:

```powershell
Get-ChildItem -Recurse -Filter *.md | Select-String -Pattern "TEST"
```

Ensure no document claims current final TEST has completed before the corresponding evidence exists.

---

# 23. Search for Model Identity

Current model:

```text
C04_FLAT_EXTRA_TREES_CONSTRAINED
```

Search:

```powershell
Get-ChildItem -Recurse -Filter *.md | Select-String -Pattern "C04_FLAT_EXTRA_TREES_CONSTRAINED"
```

The model should be documented in:

```text
README
Developer Guide
Roadmap
Architecture
Evidence Index
Version History
```

where appropriate.

---

# 24. Fingerprint Documentation Rule

A fingerprint should be copied carefully.

Examples:

```text
dataset SHA
feature columns SHA
model SHA
validation result fingerprint
```

One character error makes the identity invalid.

When possible, copy from the machine-readable artifact.

Do not type long hashes from memory.

---

# 25. Which Fingerprints Belong in Human Documentation?

Good candidates:

```text
dataset SHA
feature-column SHA
candidate registry fingerprint
winner config fingerprint
model artifact SHA
validation protocol fingerprint
validation result fingerprint
validation freeze fingerprint
```

Not every internal helper hash needs to appear in every document.

Detailed identities belong primarily in:

```text
Research_Evidence_Index.md
```

---

# 26. Avoid Duplicate Source-of-Truth Tables

Bad maintenance pattern:

```text
README contains exact 331 names

Feature_List contains exact 331 names

Architecture contains exact 331 names

Manifest contains exact 331 names
```

Eventually they diverge.

Better:

```text
Manifest:
authoritative exact list

Feature_List:
explains semantics

README:
states count + fingerprint

Evidence Index:
links identity
```

---

# 27. Code Examples in Documentation

Examples should be:

```text
small
correct
purposeful
safe
```

They should teach concepts.

Avoid examples that look executable but contain placeholders.

Bad:

```text
python SCRIPT_NAME.py
```

Good:

```powershell
python -m pytest 04_Testing\test_freeze_xauusd_portable_331_one_time_validation_result.py -q
```

---

# 28. Example vs Production Code

Clearly label conceptual examples.

For example:

```python
probabilities = model.predict_proba(X)
```

may be a valid teaching example.

But runtime inference may need additional:

```text
artifact verification
feature validation
staleness checks
logging
risk integration
```

Do not imply a two-line example is the complete production path.

---

# 29. Numerical Trading Rules

Do not invent numbers.

For example, do not write:

```text
Risk per trade = 1%
```

unless current authoritative runtime configuration verifies it.

Better:

```text
The active risk percentage is owned by RiskEngine/configuration.
```

This avoids stale safety documentation.

---

# 30. Historical Numbers

Historical model metrics should be clearly marked:

```text
HISTORICAL V3
```

or:

```text
HISTORICAL V4
```

Do not present them beside current C04 metrics without labels.

---

# 31. Current-State Banner

Important documents should contain a concise current-state section.

Example:

```text
Current model:
C04

VALIDATION:
passed and consumed

TEST:
untouched

Shadow:
not authorized

Live:
not authorized
```

This helps prevent old sections from being misinterpreted.

---

# 32. Documentation for New Modules

When a major module is introduced, update:

```text
Module_List.md
Architecture.md
Development_Roadmap.md
```

if relevant.

For a new scientific evidence generator, also update:

```text
Research_Evidence_Index.md
```

---

# 33. Documentation for a New Feature Contract

Update:

```text
Feature_List.md
Architecture.md
Development_Roadmap.md
Research_Evidence_Index.md
Version_History.md
```

and possibly:

```text
README.md
Developer_Guide.md
```

if it becomes the active model contract.

---

# 34. Documentation for a New Model Winner

Update:

```text
README.md
Developer_Guide.md
Development_Roadmap.md
Research_Evidence_Index.md
Version_History.md
```

Do not overwrite the history of the previous winner.

---

# 35. Documentation for a Holdout Result

When VALIDATION or TEST is consumed, document:

```text
result
fingerprint
consumed state
rerun policy
next authorization
```

Do not only document metrics.

---

# 36. Documentation for a Failed Holdout

A failure should still be documented.

Example:

```text
TEST_REJECTED
```

should not disappear from history.

Document:

```text
which hard check failed
holdout consumed
what operations became forbidden
```

A failed scientific gate is still valuable evidence.

---

# 37. Documentation Review Before Git Commit

Check:

```text
[ ] filenames correct
[ ] current model correct
[ ] current feature count correct
[ ] current holdout state correct
[ ] fingerprints copied correctly
[ ] old statements clearly historical
[ ] no secrets
[ ] examples use exact commands
[ ] links are relative where appropriate
```

---

# 38. Git Review

Before commit:

```powershell
git status --short
```

Review Markdown changes:

```powershell
git diff -- README.md 05_Documentation
```

This helps catch:

```text
accidental deletion
bad paste
wrong heading
duplicate section
```

---

# 39. Documentation Commit Strategy

Documentation can be committed in logical groups.

Example:

```text
onboarding
architecture
research workflow
safety/troubleshooting
history
```

A final consolidated documentation commit may be used for consistency fixes.

---

# 40. GitHub Sync Rule

Do not push half-finished documentation when a coordinated refresh is underway.

Preferred:

```text
finish local documentation
       ↓
review consistency
       ↓
review evidence
       ↓
review Git commits
       ↓
push controlled state
```

---

# 41. GitHub Is Not the Only Source of Truth

A public GitHub branch may temporarily lag behind local development.

Therefore a developer should check:

```powershell
git status
```

and:

```powershell
git log --oneline -20
```

before assuming a web page reflects the newest local research.

---

# 42. Documentation Must Not Expose Secrets

Never include:

```text
MT5 login
MT5 password
API secret
access token
private account information
```

Use safe placeholders.

Example:

```text
MT5_LOGIN=<your-login>
```

not a real value.

---

# 43. Student-Friendly Writing Style

Prefer:

```text
simple explanation
        ↓
diagram
        ↓
example
        ↓
technical rule
        ↓
warning
```

Do not assume the reader already understands:

```text
walk-forward
purge
data leakage
feature fingerprint
holdout consumption
```

Explain important terms when first introduced.

---

# 44. Good Documentation Example

Instead of:

```text
C04 passed validation.
```

write:

```text
C04 was selected using TRAIN-only walk-forward research.

The model was then frozen and fitted on all TRAIN rows.

After acceptance rules were frozen, it was evaluated once on untouched VALIDATION.

VALIDATION passed and is now consumed.
```

This teaches the scientific sequence.

---

# 45. Avoid Artificial Confidence

Documentation should distinguish:

```text
proven
tested
estimated
planned
```

Example:

```text
Production feature parity:
PENDING
```

is better than:

```text
The model works on all brokers.
```

when that has not yet been proven.

---

# 46. Estimates Must Be Labeled

Engineering estimates such as:

```text
35–55 hours remaining
```

should be clearly described as estimates.

They are not frozen scientific facts.

Update them as the roadmap changes.

---

# 47. Documentation Version Review Trigger

Perform a broad documentation review after:

```text
final TEST
production feature parity
shadow authorization
forward-validation milestone
live-promotion decision
```

These gates materially change project state.

---

# 48. Final Documentation Audit Checklist

Before publishing the refreshed docs:

```text
[ ] README current

[ ] Developer Guide current

[ ] Architecture current

[ ] Module List current

[ ] Development Roadmap current

[ ] Feature List current

[ ] Testing Guide current

[ ] Research Evidence Index current

[ ] Troubleshooting current

[ ] Trading Rules current

[ ] Version History current

[ ] Documentation Maintenance Guide current
```

Then verify:

```text
[ ] C04 is current winner

[ ] 331 is current feature count

[ ] VALIDATION is PASSED + CONSUMED

[ ] VALIDATION rerun is blocked

[ ] TEST is untouched

[ ] shadow is not authorized

[ ] live is not authorized
```

---

# 49. Future TEST Documentation Update

After final TEST completes, at minimum update:

```text
README.md

Developer_Guide.md

Development_Roadmap.md

Research_Evidence_Index.md

Version_History.md
```

Potentially also:

```text
Architecture.md
```

if the final research state changes workflow.

---

# 50. Future Shadow Documentation Update

When shadow is authorized:

Update:

```text
Architecture.md
Trading_Rules.md
Module_List.md
Development_Roadmap.md
Version_History.md
```

Document:

```text
production feature source
model verification
logging
risk integration
no-live-order boundary
```

---

# 51. Future Live Documentation Update

Live authorization should be a major version-history event.

Documentation must record:

```text
authorization evidence
model identity
feature identity
risk/runtime version
shadow evidence
forward evidence
monitoring
kill switch
```

Do not simply change:

```text
live_authorized = false
```

to:

```text
true
```

without documenting why.

---

# 52. Golden Documentation Rules

```text
1. Teach why, not only what.

2. Keep machine-readable contracts authoritative.

3. Do not duplicate exact feature contracts manually.

4. Never invent runtime numerical settings.

5. Clearly label historical experiments.

6. Update holdout state immediately after major gates.

7. Use exact executable commands.

8. Keep secrets out of documentation.

9. Preserve failed experiments in history.

10. Documentation must never overstate project readiness.
```

---

# 53. Final Principle

Good documentation should allow a future student to understand the project even if the original developer is unavailable.

The ideal result is:

```text
new developer
      ↓
reads documentation
      ↓
understands architecture
      ↓
finds relevant module
      ↓
understands contract
      ↓
runs correct tests
      ↓
makes safe change
```

without needing undocumented project history.

<!-- REPOSITORY-ARCHITECTURE-MANAGED:START -->
## Documentation Synchronization Requirement

> Managed documentation-governance section.

Documentation synchronization is a required part of an engineering gate.

When a change affects any of the following:

- repository structure;
- module ownership;
- test locations;
- CI test paths;
- data/evidence locations;
- research lifecycle;
- frozen artifacts;
- execution or deployment authorization;
- developer workflow;

the relevant Markdown documentation must be updated in the same gate before
the change is considered frozen.

At minimum, review:

- `README.md`
- `Architecture.md`
- `Developer_Guide.md`
- `Development_Roadmap.md`
- `Module_List.md`
- `Research_Evidence_Index.md`
- `Testing_Guide.md`
- `Troubleshooting.md`
- `Version_History.md`

Only documents materially affected by the gate need textual changes, but the
review itself is mandatory.

Generated inventory/migration reports do not replace maintained explanatory
documentation. Generated reports describe repository state; maintained
documentation explains architecture, intent, constraints, and operating rules.
<!-- REPOSITORY-ARCHITECTURE-MANAGED:END -->
