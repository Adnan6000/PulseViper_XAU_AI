from __future__ import annotations

import importlib
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


_acquisition: Any = importlib.import_module(
    "02_AI.Adapters.mt5_read_only_forward_acquisition_adapter"
)

mt5: Any = importlib.import_module(
    "MetaTrader5"
)


PRECHECK_VERSION = (
    "R03_MARKET_FRESHNESS_PRECHECK_V1"
)

LIVE_AUTHORIZED = False
EXECUTION_AUTHORIZED = False


def main() -> int:

    initialized = False

    try:

        initialized = bool(
            mt5.initialize()
        )

        if not initialized:

            print(
                "R03_MARKET_PRECHECK_STATUS=MARKET_NOT_READY"
            )
            print(
                "REASON=MT5_INITIALIZE_FAILED"
            )
            print(
                "LEDGERS_WRITTEN=false"
            )
            print(
                "LIVE_AUTHORIZED=false"
            )
            print(
                "EXECUTION_AUTHORIZED=false"
            )

            return 1

        read_only_api = (
            _acquisition
            .MT5ReadOnlyCapabilityFacade(
                mt5
            )
        )

        adapter = (
            _acquisition
            .MT5ReadOnlyForwardAcquisitionAdapter(
                read_only_api,
                is_synthetic=False,
                include_native_d1=False,
                timestamp_basis="AUTO",
            )
        )

        broker_symbol = (
            adapter.resolve_broker_symbol()
        )

        tick = (
            read_only_api
            .symbol_info_tick(
                broker_symbol
            )
        )

        if tick is None:

            print(
                "R03_MARKET_PRECHECK_STATUS=MARKET_NOT_READY"
            )
            print(
                "REASON=TICK_UNAVAILABLE"
            )
            print(
                f"BROKER_SYMBOL={broker_symbol}"
            )
            print(
                "LEDGERS_WRITTEN=false"
            )
            print(
                "LIVE_AUTHORIZED=false"
            )
            print(
                "EXECUTION_AUTHORIZED=false"
            )

            return 1

        raw_tick = int(
            getattr(
                tick,
                "time",
            )
        )

        import time

        now_epoch = float(
            time.time()
        )

        try:

            resolution = (
                _acquisition
                .detect_timestamp_basis_from_tick(
                    raw_tick_epoch=(
                        raw_tick
                    ),
                    now_epoch=(
                        now_epoch
                    ),
                )
            )

        except _acquisition.TimestampBasisResolutionError as exc:

            print(
                "R03_MARKET_PRECHECK_STATUS=MARKET_NOT_READY"
            )

            print(
                "REASON="
                +
                str(
                    exc
                )
            )

            print(
                f"BROKER_SYMBOL={broker_symbol}"
            )

            print(
                f"RAW_TICK={raw_tick}"
            )

            print(
                "LEDGERS_WRITTEN=false"
            )

            print(
                "LIVE_AUTHORIZED=false"
            )

            print(
                "EXECUTION_AUTHORIZED=false"
            )

            return 1

        print(
            "R03_MARKET_PRECHECK_STATUS=READY"
        )

        print(
            f"BROKER_SYMBOL={broker_symbol}"
        )

        print(
            f"RAW_TICK={raw_tick}"
        )

        print(
            "TIME_BASIS_POLICY="
            +
            str(
                resolution.policy
            )
        )

        print(
            "REFERENCE_TICK_UTC="
            +
            str(
                resolution.reference_tick_utc
            )
        )

        print(
            "REFERENCE_TICK_AGE_SECONDS="
            +
            str(
                resolution.reference_tick_age_seconds
            )
        )

        print(
            "LEDGERS_WRITTEN=false"
        )

        print(
            "PERFORMANCE_EVALUATED=false"
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 0

    finally:

        if initialized:

            try:
                mt5.shutdown()
            except Exception:
                pass


if __name__ == "__main__":

    raise SystemExit(
        main()
    )