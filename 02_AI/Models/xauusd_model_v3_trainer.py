"""PulseViper XAUUSD_MODEL_v3 trainer."""

from __future__ import annotations

import importlib
from typing import Any


base_module: Any = importlib.import_module(
    "02_AI.Models.xauusd_model_trainer"
)


class XAUUSDModelV3Trainer(
    base_module.XAUUSDModelTrainer
):

    VERSION = "3.0"

    MODEL_ID = (
        "XAUUSD_MODEL_v3"
    )