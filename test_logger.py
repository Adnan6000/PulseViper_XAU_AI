"""
Test execution for Logger System.
Path: test_logger.py
"""

import importlib
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

logger_module = importlib.import_module("02_AI.Utils.logger")
get_logger = logger_module.get_logger

logger = get_logger("TEST")
logger.info("Logger Started")
logger.warning("Spread High")
logger.error("Database Not Connected")