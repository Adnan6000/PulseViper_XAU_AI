"""
Temporary verification script for configuration settings.
Path: test_settings.py
"""

import importlib
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

settings_module = importlib.import_module("02_AI.Config.settings")
settings = settings_module.settings

print(settings.project)
print(settings.trading)
print(settings.risk)