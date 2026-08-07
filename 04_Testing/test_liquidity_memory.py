from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

Liquidity = importlib.import_module(
    "02_AI.Objects.liquidity"
).Liquidity

LiquidityType = importlib.import_module(
    "02_AI.Common.enums"
).LiquidityType

memory = importlib.import_module(
    "02_AI.Memory.liquidity_memory"
).LiquidityMemory


def test_liquidity_memory():

    manager = memory(
        price_tolerance=0.20
    )

    first = Liquidity(
        liquidity_id=manager.generate_id(),
        liquidity_type=LiquidityType.BUY_SIDE,
        price=3400.00,
        touches=1,
        first_index=10,
        last_index=10,
    )

    registered = manager.register(first)

    assert registered is first
    assert manager.active_count() == 1

    second = Liquidity(
        liquidity_id=manager.generate_id(),
        liquidity_type=LiquidityType.BUY_SIDE,
        price=3400.10,
        touches=1,
        first_index=20,
        last_index=20,
    )

    merged = manager.register(second)

    assert merged is first
    assert manager.active_count() == 1
    assert first.touches == 2
    assert len(first.touch_history) == 1

    manager.mark_swept(
        liquidity_id=first.liquidity_id,
        index=50,
    )

    assert manager.active_count() == 0
    assert manager.swept_count() == 1

    swept = manager.get_swept()[0]

    assert swept.swept is True
    assert swept.active is False