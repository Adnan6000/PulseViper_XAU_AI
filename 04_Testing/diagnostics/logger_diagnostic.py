"""
===============================================================================
Logger diagnostic for PulseViper XAU AI.
Path: 04_Testing/diagnostics/logger_diagnostic.py
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

    logger_module = (
        importlib.import_module(
            "02_AI.Utils.logger"
        )
    )

    get_logger = (
        logger_module.get_logger
    )

    logger = get_logger(
        "TEST"
    )

    logger.info(
        "Logger Started"
    )

    logger.warning(
        "Spread High"
    )

    logger.error(
        "Database Not Connected"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
