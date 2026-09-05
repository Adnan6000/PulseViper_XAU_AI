import importlib



bos_memory = importlib.import_module(
    "02_AI.Memory.bos_memory"
).bos_memory


def test_memory():

    bos_memory.reset()

    bos_id = bos_memory.generate_id()

    assert bos_id == 1

    bos_memory.register_high_break(10)

    assert bos_memory.high_already_broken(10)

    bos = {

        "bos_id": bos_id,

        "direction": "BUY"

    }

    bos_memory.activate(bos)

    assert bos_id in bos_memory.active_bos

    bos_memory.complete(bos_id)

    assert bos_id in bos_memory.completed_bos
