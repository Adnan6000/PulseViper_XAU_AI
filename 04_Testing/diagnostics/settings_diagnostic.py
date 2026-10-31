"""
===============================================================================
Configuration settings diagnostic for PulseViper XAU AI.
Path: 04_Testing/diagnostics/settings_diagnostic.py
===============================================================================
"""

from __future__ import annotations

import importlib
from pathlib import Path

from _repository_bootstrap import (
    ensure_repository_root_on_sys_path,
)


def main() -> int:

    ensure_repository_root_on_sys_path(
        Path(__file__).resolve().parent
    )

    settings_module = (
        importlib.import_module(
            "02_AI.Config.settings"
        )
    )

    settings = (
        settings_module.settings
    )

    print(
        settings.project
    )

    print(
        settings.trading
    )

    print(
        settings.risk
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
