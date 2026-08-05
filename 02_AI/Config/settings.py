"""
PulseViper XAUUSD AI - Central Configuration Subsystem
Path: 02_AI/Config/settings.py
Provides encapsulated, property-based access to config.yaml across all layers.
"""

from pathlib import Path
from typing import Any, Dict
import yaml

ROOT_DIR: Path = Path(__file__).resolve().parents[2]
CONFIG_FILE: Path = ROOT_DIR / "config.yaml"


class Settings:
    """Loads and encapsulates project configuration from config.yaml."""

    def __init__(self) -> None:
        if not CONFIG_FILE.exists():
            raise FileNotFoundError(f"Configuration file not found at: {CONFIG_FILE}")

        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            self._config: Dict[str, Any] = yaml.safe_load(file)

    @property
    def project(self) -> Dict[str, Any]:
        """Returns project metadata configurations."""
        return self._config["project"]

    @property
    def trading(self) -> Dict[str, Any]:
        """Returns market and trading symbol configurations."""
        return self._config["trading"]

    @property
    def risk(self) -> Dict[str, Any]:
        """Returns risk management parameters."""
        return self._config["risk"]

    @property
    def training(self) -> Dict[str, Any]:
        """Returns model training hyper-parameters."""
        return self._config["training"]

    @property
    def database(self) -> Dict[str, Any]:
        """Returns SQLite database file properties."""
        return self._config["database"]

    @property
    def logging(self) -> Dict[str, Any]:
        """Returns system logging preferences."""
        return self._config["logging"]


# Global Instance Export
settings = Settings()