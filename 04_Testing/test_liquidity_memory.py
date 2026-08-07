from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

Liquidity = importlib.import_module(
    "02_AI.Objects.liquidity"
).Liquidity

memory = importlib.import_module(
    "02_AI.Memory.liquidity_memory"
).liquidity_memory


def test_liquidity_memory():

    memory.reset()

    obj = Liquidity(

        liquidity_id=memory.generate_id(),

        liquidity_type="BUY_SIDE",

        price=3400.00,

        touches=2,

        first_index=10,

        last_index=20

    )

    memory.register(obj)

    assert len(memory.get_active()) == 1

    memory.mark_swept(

        liquidity_id=obj.liquidity_id,

        index=50

    )

    assert len(memory.get_active()) == 0

    assert len(memory.get_swept()) == 1