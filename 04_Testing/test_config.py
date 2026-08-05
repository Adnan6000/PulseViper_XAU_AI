"""
Automated unit tests for 02_AI/Config/settings.py
Path: 04_Testing/test_config.py
"""

import importlib
from pathlib import Path
import sys

# Add Workspace Root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Dynamic Import for folder starting with digits
settings_module = importlib.import_module("02_AI.Config.settings")
settings = settings_module.settings


def test_project_settings_keys() -> None:
    """Validate project structure parameters."""
    proj = settings.project
    assert proj["name"] == "PulseViper XAU AI"
    assert proj["version"] == "3.0.0"
    assert "author" in proj


def test_trading_and_risk_thresholds() -> None:
    """Validate institutional risk and trading bounds."""
    assert settings.trading["symbol"] == "XAUUSD"
    assert settings.risk["max_spread_points"] == 300
    assert settings.risk["minimum_rr"] == 2.0


def test_database_and_logging_config() -> None:
    """Validate system persistence and logging keys."""
    assert settings.database["filename"] == "pulseviper.db"
    assert settings.logging["level"] == "INFO"