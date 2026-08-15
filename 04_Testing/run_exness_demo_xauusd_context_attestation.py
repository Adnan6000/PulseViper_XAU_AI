"""Standalone launcher for the Exness DEMO XAUUSD attestation operation.

This launcher owns only project-path bootstrap. The underlying operation owns
all MT5/read-only attestation behavior.

No broker calls or execution authority live here.
"""

from __future__ import annotations

import importlib
import sys

from pathlib import Path
from typing import Any


PROJECT_ROOT = (
    Path(
        __file__
    )
    .resolve()
    .parents[
        1
    ]
)

if str(
    PROJECT_ROOT
) not in sys.path:

    sys.path.insert(
        0,
        str(
            PROJECT_ROOT
        ),
    )


operation: Any = importlib.import_module(
    "04_Testing."
    "exness_demo_xauusd_context_"
    "attestation_operation"
)


def main() -> int:

    return int(
        operation.main()
    )


if __name__ == "__main__":

    raise SystemExit(
        main()
    )