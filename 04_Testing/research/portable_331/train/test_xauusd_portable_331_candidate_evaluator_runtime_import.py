from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "run_xauusd_portable_331_candidate_evaluator_integration.py"
)

spec = importlib.util.spec_from_file_location(
    "xauusd_candidate_runtime_import_test_target",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

runner = importlib.util.module_from_spec(
    spec
)

sys.modules[
    spec.name
] = runner

spec.loader.exec_module(
    runner
)


def test_training_loader_imports_in_dataset_package_context():
    module = (
        runner._load_loader_module()
    )

    assert (
        module.__name__
        == (
            "02_AI.Dataset."
            "portable_331_training_input_loader"
        )
    )

    assert (
        module.__package__
        == "02_AI.Dataset"
    )

    assert hasattr(
        module,
        "Portable331TrainingInputLoader",
    )