"""XAUUSD_MODEL_v2 trainer.

Reuses the validated XAUUSDModelTrainer implementation while changing the
artifact/model identity. This avoids duplicating the complete trainer.
"""

from __future__ import annotations

import importlib
from typing import Any


base_module: Any = importlib.import_module(
    "02_AI.Models.xauusd_model_trainer"
)


class XAUUSDModelV2Trainer(
    base_module.XAUUSDModelTrainer
):

    VERSION = "2.0"

    MODEL_ID = (
        "XAUUSD_MODEL_v2"
    )