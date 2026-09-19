# Security Policy

## Security Scope

Security reports are welcome for the current PulseViper XAU AI codebase.

Because the project contains machine-learning, trading, risk-management, and broker-facing components, security issues may include:

- exposed credentials;
- insecure MT5 credential handling;
- API key or token exposure;
- command injection;
- unsafe file operations;
- path traversal;
- malicious deserialization;
- dependency vulnerabilities;
- unsafe model or artifact loading;
- unauthorized order execution;
- risk-control bypasses;
- sensitive information appearing in logs;
- insecure configuration defaults.

---

## Reporting a Vulnerability

Please do not open a public GitHub issue containing:

- passwords;
- API keys;
- access tokens;
- broker credentials;
- private account information;
- sensitive exploit details;
- confidential data.

Preferred reporting method:

Use GitHub's private vulnerability reporting / Security Advisory system if enabled for this repository.

If private vulnerability reporting is unavailable, contact the repository owner through a private contact method available on the maintainer's GitHub profile.

---

## Information to Include

A useful security report should contain:

- a clear description of the vulnerability;
- affected file or component;
- steps to reproduce;
- expected behavior;
- actual behavior;
- potential security impact;
- safe proof of concept where appropriate;
- suggested mitigation if known.

Never include real credentials in a report.

---

## Trading and Execution Safety

Security fixes must not silently weaken:

- RiskEngine;
- account protection;
- broker-aware sizing;
- `trade_ready`;
- execution safeguards;
- shadow execution semantics;
- protected research boundaries.

Changes affecting broker-facing or order-execution code must be reviewed and tested in a controlled environment.

---

## Secrets

Never commit:

- MT5 passwords;
- broker login credentials;
- API keys;
- access tokens;
- private keys;
- production `.env` files;
- personal account information;
- confidential broker information.

If a secret is accidentally committed, consider the secret compromised.

Deleting the secret from the latest commit is not enough.

The credential should be revoked or rotated.

---

## Responsible Disclosure

Please allow reasonable time for investigation and remediation before publicly disclosing security-sensitive details.

---

## Project Status

PulseViper is currently a research and validation project.

Security testing or fixing a vulnerability does not authorize live trading.

```text
live_authorized = false
```