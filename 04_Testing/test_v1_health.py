"""
===============================================================================
Module      : test_v1_health.py
Project     : PulseViper XAU AI
Purpose     : Deterministic offline V1 repository health checks
===============================================================================

These tests:
- require no MetaTrader 5 connection
- require no market data
- perform no trading
- do not modify production strategy logic
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


pytestmark = pytest.mark.offline


# =============================================================================
# Configuration
# =============================================================================


def test_config_file_exists() -> None:

    config_file = (
        PROJECT_ROOT
        / "config.yaml"
    )

    assert config_file.is_file(), (
        "Root config.yaml is missing."
    )


def test_settings_load_successfully() -> None:

    module: Any = importlib.import_module(
        "02_AI.Config.settings"
    )

    settings: Any = module.settings

    assert settings is not None


def test_required_configuration_sections_exist() -> None:

    module: Any = importlib.import_module(
        "02_AI.Config.settings"
    )

    settings: Any = module.settings

    assert isinstance(
        settings.project,
        dict,
    )

    assert isinstance(
        settings.trading,
        dict,
    )

    assert isinstance(
        settings.risk,
        dict,
    )

    assert isinstance(
        settings.training,
        dict,
    )

    assert isinstance(
        settings.database,
        dict,
    )

    assert isinstance(
        settings.logging,
        dict,
    )


def test_project_identity_is_configured() -> None:

    module: Any = importlib.import_module(
        "02_AI.Config.settings"
    )

    settings: Any = module.settings

    name = str(
        settings.project.get(
            "name",
            "",
        )
    ).strip()

    version = str(
        settings.project.get(
            "version",
            "",
        )
    ).strip()

    assert name
    assert version


def test_trading_configuration_is_valid() -> None:

    module: Any = importlib.import_module(
        "02_AI.Config.settings"
    )

    settings: Any = module.settings

    symbol = str(
        settings.trading.get(
            "symbol",
            "",
        )
    ).strip()

    timeframe = str(
        settings.trading.get(
            "timeframe",
            "",
        )
    ).strip()

    assert symbol
    assert timeframe


# =============================================================================
# Database path contract
# =============================================================================


def test_database_path_is_inside_data_directory() -> None:

    database_module: Any = (
        importlib.import_module(
            "02_AI.Database.database"
        )
    )

    settings_module: Any = (
        importlib.import_module(
            "02_AI.Config.settings"
        )
    )

    database: Any = (
        database_module.database
    )

    settings: Any = (
        settings_module.settings
    )

    expected_directory = (
        PROJECT_ROOT
        / "01_Data"
    ).resolve()

    actual_path = Path(
        database.database_path
    ).resolve()

    assert (
        actual_path.parent
        ==
        expected_directory
    )

    assert (
        actual_path.name
        ==
        settings.database[
            "filename"
        ]
    )


# =============================================================================
# Research / production separation
# =============================================================================


def test_market_regime_is_metadata_only() -> None:

    module: Any = importlib.import_module(
        "02_AI.Core.market_regime"
    )

    engine: Any = (
        module.market_regime
    )

    assert (
        engine.MODE
        ==
        "CAUSAL_METADATA_ONLY"
    )


def test_market_regime_has_version() -> None:

    module: Any = importlib.import_module(
        "02_AI.Core.market_regime"
    )

    engine: Any = (
        module.market_regime
    )

    assert str(
        engine.VERSION
    ).strip()


# =============================================================================
# Repository hygiene
# =============================================================================


def test_runtime_database_is_gitignored() -> None:

    gitignore = (
        PROJECT_ROOT
        / ".gitignore"
    )

    assert gitignore.is_file()

    text = gitignore.read_text(
        encoding="utf-8",
    )

    assert (
        "01_Data/*.db"
        in text
    )


def test_environment_file_is_gitignored() -> None:

    gitignore = (
        PROJECT_ROOT
        / ".gitignore"
    )

    text = gitignore.read_text(
        encoding="utf-8",
    )

    assert ".env" in text

    assert (
        "!.env.example"
        in text
    )