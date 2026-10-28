"""PulseViper Self-Evolution V1: read-only code intelligence.

Audits code and proposes experiments.
Never edits source, runs trades, changes permissions or pushes commits.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

VERSION = "PULSEVIPER_SELF_EVOLUTION_V1"
ROOT = Path(__file__).resolve().parents[2]

AI = ROOT / "02_AI"
INTELLIGENCE = AI / "MarketIntelligence"
ADAPTER = AI / "Adapters" / (
    "mt5_read_only_forward_acquisition_adapter.py"
)
CONTRACT = AI / "Features" / "portable_feature_contract.py"

TEST_DIR = ROOT / "04_Testing" / "production_portability"
TEST_NAMES = (
    "test_r03_market_discovery_brain.py",
    "test_r03_market_discovery_validation.py",
    "test_r03_event_evidence.py",
    "test_r03_mtf_reasoning.py",
)


def run_check(
    name: str,
    args: list[str],
    timeout: int = 120,
) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
        )
        output = (
            result.stdout + "\n" + result.stderr
        ).strip()

        return {
            "name": name,
            "status": (
                "PASS" if result.returncode == 0
                else "FAIL"
            ),
            "exit_code": result.returncode,
            "output_tail": output[-2500:],
        }

    except subprocess.TimeoutExpired:
        return {
            "name": name,
            "status": "TIMEOUT",
            "output_tail": "Command exceeded timeout",
        }
    except Exception as exc:
        return {
            "name": name,
            "status": "BLOCKED",
            "output_tail": (
                type(exc).__name__ + ": " + str(exc)
            ),
        }


def inspect_capabilities() -> dict[str, Any]:
    adapter = (
        ADAPTER.read_text(encoding="utf-8-sig")
        if ADAPTER.is_file() else ""
    )
    contract = (
        CONTRACT.read_text(encoding="utf-8-sig")
        if CONTRACT.is_file() else ""
    )

    modules = {
        "market_discovery": (
            INTELLIGENCE / "r03_market_discovery_brain.py"
        ).is_file(),
        "historical_validation": (
            INTELLIGENCE / "r03_market_discovery_validation.py"
        ).is_file(),
        "autonomous_research": (
            INTELLIGENCE / "r03_autonomous_research_agent.py"
        ).is_file(),
        "event_evidence": (
            INTELLIGENCE / "r03_event_evidence.py"
        ).is_file(),
        "mtf_reasoning": (
            INTELLIGENCE / "r03_mtf_reasoning.py"
        ).is_file(),
    }

    return {
        "modules": modules,
        "m1_defined_in_feature_contract": (
            '"M1": 1' in contract
        ),
        "m1_native_acquisition_configured": (
            '"TIMEFRAME_M1"' in adapter
            and '"M1"' in adapter
        ),
        "native_d1_required_by_acquisition": (
            '"D1"' in adapter.split(
                "REQUIRED_TIMEFRAMES:", 1
            )[1].split(")", 1)[0]
            if "REQUIRED_TIMEFRAMES:" in adapter
            else None
        ),
    }


def propose(
    capabilities: dict[str, Any],
    checks: list[dict[str, Any]],
) -> list[dict[str, str]]:
    proposals: list[dict[str, str]] = []

    if any(
        check["status"] != "PASS"
        for check in checks
        if check["name"] in ("PYRIGHT", "PYTEST")
    ):
        proposals.append({
            "priority": "P0",
            "task": "Repair current static or regression failures",
            "verification": "Pyright and pytest must pass",
        })

    if (
        capabilities["m1_defined_in_feature_contract"]
        and not capabilities[
            "m1_native_acquisition_configured"
        ]
    ):
        proposals.append({
            "priority": "P1",
            "task": (
                "Experiment with read-only completed-M1 "
                "acquisition without altering frozen R03 schema"
            ),
            "verification": (
                "M1 timestamp, provenance and "
                "closed-bar integration tests"
            ),
        })

    if capabilities["modules"]["mtf_reasoning"]:
        proposals.append({
            "priority": "P1",
            "task": (
                "Verify native MTF freshness and canonical "
                "closed-D1 reconstruction"
            ),
            "verification": (
                "Real snapshot alignment and "
                "future-leakage regression tests"
            ),
        })

    if capabilities["modules"]["event_evidence"]:
        proposals.append({
            "priority": "P2",
            "task": (
                "Evaluate event matching across longer "
                "history and untouched market sessions"
            ),
            "verification": (
                "Non-overlap, paired controls and "
                "out-of-sample research tests"
            ),
        })

    return proposals


def audit() -> dict[str, Any]:
    capabilities = inspect_capabilities()

    tests = [
        str(TEST_DIR / name)
        for name in TEST_NAMES
        if (TEST_DIR / name).is_file()
    ]

    checks = [
        run_check(
            "GIT_STATUS",
            ["git", "status", "--short"],
            timeout=20,
        ),
        run_check(
            "PYRIGHT",
            [
                sys.executable,
                "-m",
                "pyright",
                str(INTELLIGENCE),
                str(AI / "SelfEvolution"),
            ],
        ),
    ]

    if tests:
        checks.append(
            run_check(
                "PYTEST",
                [sys.executable, "-m", "pytest", *tests, "-q"],
            )
        )
    else:
        checks.append({
            "name": "PYTEST",
            "status": "BLOCKED",
            "output_tail": "No targeted tests found",
        })

    return {
        "version": VERSION,
        "status": "AUDIT_COMPLETE",
        "capabilities": capabilities,
        "checks": checks,
        "proposed_upgrades": propose(
            capabilities, checks
        ),
        "code_modified": False,
        "git_written": False,
        "model_retrained": False,
        "trades_executed": False,
        "production_upgrade_authorized": False,
    }


def main() -> int:
    try:
        result = audit()
    except Exception as exc:
        print("SELF_EVOLUTION_STATUS=BLOCKED")
        print(type(exc).__name__ + ": " + str(exc))
        return 2

    print("SELF_EVOLUTION_STATUS=AUDIT_COMPLETE")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
