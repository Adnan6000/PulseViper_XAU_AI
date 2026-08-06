from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

Liquidity = importlib.import_module(
    "02_AI.Objects.liquidity"
).Liquidity


def test_liquidity_object():

    obj = Liquidity(

        liquidity_id=1,

        liquidity_type="BUY_SIDE",

        price=3400.25,

        touches=2,

        first_index=100,

        last_index=120

    )

    obj.increase_touch()

    assert obj.touches == 3

    obj.update_last_touch(150)

    assert obj.last_index == 150

    obj.mark_swept(180)

    assert obj.swept

    assert not obj.active