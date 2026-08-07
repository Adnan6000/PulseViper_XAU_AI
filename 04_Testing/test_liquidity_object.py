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


def test_liquidity_object():

    obj = Liquidity(

        liquidity_id=1,

        liquidity_type=LiquidityType.BUY_SIDE,

        price=3400.25,

        touches=1,

        first_index=100,

        last_index=100,

    )

    assert obj.liquidity_type == LiquidityType.BUY_SIDE

    obj.increase_touch(
        index=120,
        price=3400.25,
        touch_type="RETEST",
    )

    assert obj.touches == 2
    assert obj.last_index == 120
    assert len(obj.touch_history) == 1

    obj.update_last_touch(
        index=150,
        price=3400.30,
        touch_type="RETEST",
    )

    assert obj.last_index == 150
    assert len(obj.touch_history) == 2

    obj.mark_swept(180)

    assert obj.swept is True
    assert obj.active is False

    data = obj.to_dict()

    assert data["liquidity_id"] == 1
    assert data["liquidity_type"] == "BUY_SIDE"
    assert data["touches"] == 2
    assert len(data["touch_history"]) == 2