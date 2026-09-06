"""
===============================================================================
Module      : test_portable_feature_contract.py
Project     : PulseViper XAU AI
Purpose     : Test Suite for Frozen 331 Feature Contract (Gate 13)
===============================================================================
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

contract_mod = importlib.import_module("02_AI.Features.portable_feature_contract")

EXPECTED_FEATURE_COUNT = contract_mod.EXPECTED_FEATURE_COUNT
EXPECTED_FEATURE_COLUMNS_SHA256 = contract_mod.EXPECTED_FEATURE_COLUMNS_SHA256
FROZEN_FEATURE_COLUMNS = contract_mod.FROZEN_FEATURE_COLUMNS
SUPPORTED_SYMBOLS = contract_mod.SUPPORTED_SYMBOLS
CANONICAL_SYMBOL = contract_mod.CANONICAL_SYMBOL
normalize_supported_symbol = contract_mod.normalize_supported_symbol
verify_feature_columns = contract_mod.verify_feature_columns
compute_feature_columns_sha256 = contract_mod.compute_feature_columns_sha256


def test_frozen_feature_count_is_exactly_331() -> None:
    """Validate that the contract mandates exactly 331 features."""
    assert EXPECTED_FEATURE_COUNT == 331
    assert len(FROZEN_FEATURE_COLUMNS) == 331


def test_frozen_feature_columns_sha256_matches_manifest() -> None:
    """Validate that the feature columns SHA256 matches the authoritative research manifest."""
    computed_sha = compute_feature_columns_sha256(FROZEN_FEATURE_COLUMNS)
    assert computed_sha == EXPECTED_FEATURE_COLUMNS_SHA256
    assert verify_feature_columns(FROZEN_FEATURE_COLUMNS) is True


def test_feature_verification_rejects_missing_column() -> None:
    """Verify that removing any single feature column fails validation."""
    tampered = list(FROZEN_FEATURE_COLUMNS)[:-1]
    assert verify_feature_columns(tampered) is False


def test_feature_verification_rejects_reordered_columns() -> None:
    """Verify that reordering columns fails validation even if all 331 features exist."""
    tampered = list(FROZEN_FEATURE_COLUMNS)
    tampered[0], tampered[1] = tampered[1], tampered[0]
    assert verify_feature_columns(tampered) is False


def test_feature_verification_rejects_unknown_column() -> None:
    """Verify that injecting an unknown column fails validation."""
    tampered = list(FROZEN_FEATURE_COLUMNS)[:-1] + ["extra_unknown_feature"]
    assert verify_feature_columns(tampered) is False


def test_symbol_normalization_accepts_proven_symbols() -> None:
    """Validate that XAUUSD and XAUUSDm are correctly normalized to canonical XAUUSD."""
    assert normalize_supported_symbol("XAUUSD") == CANONICAL_SYMBOL
    assert normalize_supported_symbol("XAUUSDm") == CANONICAL_SYMBOL
    assert normalize_supported_symbol(" XAUUSD ") == CANONICAL_SYMBOL
    assert normalize_supported_symbol(" XAUUSDm ") == CANONICAL_SYMBOL


def test_symbol_normalization_rejects_unproven_or_alien_symbols() -> None:
    """Validate that unproven symbols fail closed."""
    for alien in ("EURUSD", "GBPUSD", "GOLD", "XAUUSD.m", "XAUEUR", "BTCUSD"):
        with pytest.raises(ValueError, match="UNSUPPORTED_BROKER_SYMBOL"):
            normalize_supported_symbol(alien)


def test_feature_family_distribution() -> None:
    """Verify the exact count of features in each expected feature family."""
    m5_tech = [c for c in FROZEN_FEATURE_COLUMNS if c.startswith("m5_") and not c.startswith("m5_domain_") and c != "m5_tick_volume_ratio20"]
    assert len(m5_tech) == 43

    m5_vol = [c for c in FROZEN_FEATURE_COLUMNS if c == "m5_tick_volume_ratio20"]
    assert len(m5_vol) == 1

    m5_dom = [c for c in FROZEN_FEATURE_COLUMNS if c.startswith("m5_domain_")]
    assert len(m5_dom) == 63

    utc_cyc = [c for c in FROZEN_FEATURE_COLUMNS if c.startswith("utc_")]
    assert len(utc_cyc) == 4

    htf_age = [c for c in FROZEN_FEATURE_COLUMNS if c.endswith("_age_minutes")]
    assert len(htf_age) == 5

    for tf in ("m15", "m30", "h1", "h4", "d1"):
        htf_tech = [c for c in FROZEN_FEATURE_COLUMNS if c.startswith(f"{tf}_") and not c.endswith("_age_minutes")]
        assert len(htf_tech) == 43, f"Expected 43 technical features for {tf}, got {len(htf_tech)}"

    total = len(m5_tech) + len(m5_vol) + len(m5_dom) + len(utc_cyc) + len(htf_age) + (43 * 5)
    assert total == 331
