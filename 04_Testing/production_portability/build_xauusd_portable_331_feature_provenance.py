"""
===============================================================================
Script      : build_xauusd_portable_331_feature_provenance.py
Project     : PulseViper XAU AI
Purpose     : Generate Machine-Checkable Feature Provenance Map (Gate 13)
===============================================================================

Generates a machine-checkable provenance map for each of the 331 frozen features:
frozen_feature -> producer/module -> required source columns -> timeframe ->
lookback -> availability-time rule -> expected dtype -> parity method -> tolerance.

No live trading.
No execution authority.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_contract = importlib.import_module("02_AI.Features.portable_feature_contract")

EXPECTED_FEATURE_COLUMNS_SHA256: str = _contract.EXPECTED_FEATURE_COLUMNS_SHA256
EXPECTED_FEATURE_COUNT: int = _contract.EXPECTED_FEATURE_COUNT
FROZEN_FEATURE_COLUMNS: tuple[str, ...] = _contract.FROZEN_FEATURE_COLUMNS
PORTABLE_FEATURE_CONTRACT_VERSION: str = _contract.PORTABLE_FEATURE_CONTRACT_VERSION

PROVENANCE_VERSION: str = "XAUUSD_PORTABLE_331_FEATURE_PROVENANCE_V1"

OUTPUT_PATH: Path = (
    REPO_ROOT
    / "04_Testing"
    / "evidence"
    / "production_portability"
    / "xauusd_portable_331_feature_provenance_map.json"
)

# Explicit tolerance specifications per family (Directive 6)
TOLERANCE_POLICIES: dict[str, dict[str, Any]] = {
    "EXACT_DISCRETE": {
        "policy_id": "EXACT_DISCRETE",
        "description": "Discrete integer codes, categorical classifications, boolean states, and structural flags require exact equality.",
        "atol": 0.0,
        "rtol": 0.0,
        "exact_match_required": True,
    },
    "INTEGER_COUNT": {
        "policy_id": "INTEGER_COUNT",
        "description": "Integer bar counts, age in minutes, and distance metrics.",
        "atol": 0.0,
        "rtol": 0.0,
        "exact_match_required": True,
    },
    "FLOAT32_NUMERIC": {
        "policy_id": "FLOAT32_NUMERIC",
        "description": "Continuous technical indicator values, moving averages, momentum oscillators, volatility bands.",
        "atol": 1e-4,
        "rtol": 1e-4,
        "exact_match_required": False,
    },
    "FLOAT32_TRIGONOMETRIC": {
        "policy_id": "FLOAT32_TRIGONOMETRIC",
        "description": "Cyclical trigonometric time encodings (sin/cos of UTC hour and day).",
        "atol": 1e-5,
        "rtol": 1e-5,
        "exact_match_required": False,
    },
}

# Sets of discrete features across technical and domain families
DISCRETE_TECHNICAL_SUFFIXES: set[str] = {
    "trend_direction",
    "bullish",
    "bearish",
    "doji",
    "marubozu",
    "pinbar",
    "bullish_engulfing",
    "bearish_engulfing",
    "inside_bar",
    "outside_bar",
    "expansion",
    "compression",
}

DISCRETE_DOMAIN_FEATURES: set[str] = {
    "m5_domain_regime_ready",
    "m5_domain_regime_trend_code",
    "m5_domain_regime_volatility_code",
    "m5_domain_hh",
    "m5_domain_hl",
    "m5_domain_lh",
    "m5_domain_ll",
    "m5_domain_micro_high",
    "m5_domain_micro_low",
    "m5_domain_internal_high",
    "m5_domain_internal_low",
    "m5_domain_major_high",
    "m5_domain_major_low",
    "m5_domain_swing_direction_code",
    "m5_domain_swing_scale_code",
    "m5_domain_structure_bias_code",
    "m5_domain_last_swing_high_known",
    "m5_domain_last_swing_low_known",
    "m5_domain_last_major_high_known",
    "m5_domain_last_major_low_known",
    "m5_domain_bullish_bos",
    "m5_domain_bearish_bos",
    "m5_domain_micro_bos",
    "m5_domain_internal_bos",
    "m5_domain_major_bos",
    "m5_domain_bos_continuation",
    "m5_domain_bos_reversal",
    "m5_domain_last_bos_direction",
    "m5_domain_bullish_fvg",
    "m5_domain_bearish_fvg",
    "m5_domain_last_fvg_direction",
    "m5_domain_iz_event",
    "m5_domain_iz_direction",
    "m5_domain_last_iz_direction",
}

INTEGER_COUNT_FEATURES: set[str] = {
    "m15_age_minutes",
    "m30_age_minutes",
    "h1_age_minutes",
    "h4_age_minutes",
    "d1_age_minutes",
    "m5_domain_bars_since_swing",
    "m5_domain_bars_since_bullish_bos",
    "m5_domain_bars_since_bearish_bos",
    "m5_domain_bars_since_bullish_fvg",
    "m5_domain_bars_since_bearish_fvg",
    "m5_domain_iz_confirmation_delay_bars",
    "m5_domain_bars_since_bullish_iz",
    "m5_domain_bars_since_bearish_iz",
}


def classify_feature(feature_name: str) -> dict[str, Any]:
    """Classify a single frozen feature into its full provenance record."""
    if feature_name.startswith("utc_"):
        return {
            "feature_name": feature_name,
            "feature_family": "utc_cyclical",
            "timeframe": "M5",
            "producer_module": "02_AI.Features.portable_feature_pipeline.PortableFeaturePipeline._generate_cyclical_utc_features",
            "required_source_columns": ["decision_time"],
            "lookback_bars": 0,
            "availability_rule": "INSTANTANEOUS_AT_DECISION_TIME",
            "expected_dtype": "float32",
            "tolerance_policy": "FLOAT32_TRIGONOMETRIC",
            "parity_method": "strict_float_tolerance",
        }

    if feature_name.endswith("_age_minutes"):
        tf_prefix = feature_name.split("_")[0].upper()
        return {
            "feature_name": feature_name,
            "feature_family": "htf_age",
            "timeframe": tf_prefix,
            "producer_module": "02_AI.Features.portable_feature_pipeline.PortableFeaturePipeline._align_htf_features",
            "required_source_columns": ["time"],
            "lookback_bars": 1,
            "availability_rule": f"AVAILABLE_AFTER_HTF_CLOSE_LEQ_DECISION_TIME ({tf_prefix})",
            "expected_dtype": "float32",
            "tolerance_policy": "INTEGER_COUNT",
            "parity_method": "exact_integer_equality",
        }

    if feature_name == "m5_tick_volume_ratio20":
        return {
            "feature_name": feature_name,
            "feature_family": "m5_relative_volume",
            "timeframe": "M5",
            "producer_module": "02_AI.Features.portable_feature_pipeline.PortableFeaturePipeline._generate_m5_tick_volume_ratio20",
            "required_source_columns": ["time", "tick_volume"],
            "lookback_bars": 20,
            "availability_rule": "BASE_BAR_AVAILABLE_AFTER_M5_CLOSE",
            "expected_dtype": "float32",
            "tolerance_policy": "FLOAT32_NUMERIC",
            "parity_method": "strict_float_tolerance",
        }

    if feature_name.startswith("m5_domain_"):
        if feature_name in DISCRETE_DOMAIN_FEATURES:
            tol = "EXACT_DISCRETE"
            parity_m = "exact_discrete_equality"
        elif feature_name in INTEGER_COUNT_FEATURES:
            tol = "INTEGER_COUNT"
            parity_m = "exact_integer_equality"
        else:
            tol = "FLOAT32_NUMERIC"
            parity_m = "strict_float_tolerance"

        return {
            "feature_name": feature_name,
            "feature_family": "m5_domain",
            "timeframe": "M5",
            "producer_module": "02_AI.Core.(MarketStructure|MarketRegimeEngine|BOSEngine|FVGEngine|InstitutionalZonesEngine)",
            "required_source_columns": ["time", "open", "high", "low", "close", "tick_volume"],
            "lookback_bars": "CAUSAL_DYNAMIC_STRUCTURE_STATE",
            "availability_rule": "BASE_BAR_AVAILABLE_AFTER_M5_CLOSE",
            "expected_dtype": "float32",
            "tolerance_policy": tol,
            "parity_method": parity_m,
        }

    # Technical features: timeframe prefix
    parts = feature_name.split("_", 1)
    tf_prefix = parts[0].upper()
    tech_suffix = parts[1]

    if tech_suffix in DISCRETE_TECHNICAL_SUFFIXES:
        tol = "EXACT_DISCRETE"
        parity_m = "exact_discrete_equality"
    else:
        tol = "FLOAT32_NUMERIC"
        parity_m = "strict_float_tolerance"

    avail = (
        "BASE_BAR_AVAILABLE_AFTER_M5_CLOSE"
        if tf_prefix == "M5"
        else f"AVAILABLE_AFTER_HTF_CLOSE_LEQ_DECISION_TIME ({tf_prefix})"
    )

    return {
        "feature_name": feature_name,
        "feature_family": f"{tf_prefix.lower()}_technical",
        "timeframe": tf_prefix,
        "producer_module": "02_AI.Features.feature_generator.FeatureGenerator",
        "required_source_columns": ["time", "open", "high", "low", "close", "tick_volume"],
        "lookback_bars": 200,
        "availability_rule": avail,
        "expected_dtype": "float32",
        "tolerance_policy": tol,
        "parity_method": parity_m,
    }


def generate_provenance_map() -> dict[str, Any]:
    """Build the full machine-checkable provenance document."""
    records: list[dict[str, Any]] = [classify_feature(f) for f in FROZEN_FEATURE_COLUMNS]

    assert len(records) == EXPECTED_FEATURE_COUNT, (
        f"Feature count mismatch: {len(records)} != {EXPECTED_FEATURE_COUNT}"
    )

    # Summarize families
    family_counts: dict[str, int] = {}
    tolerance_counts: dict[str, int] = {}
    for r in records:
        family_counts[r["feature_family"]] = family_counts.get(r["feature_family"], 0) + 1
        tolerance_counts[r["tolerance_policy"]] = tolerance_counts.get(r["tolerance_policy"], 0) + 1

    payload_for_sha = json.dumps(
        records,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=True,
    ).encode("utf-8")
    provenance_sha256 = hashlib.sha256(payload_for_sha).hexdigest()

    doc: dict[str, Any] = {
        "provenance_version": PROVENANCE_VERSION,
        "contract_version": PORTABLE_FEATURE_CONTRACT_VERSION,
        "expected_feature_count": EXPECTED_FEATURE_COUNT,
        "expected_feature_columns_sha256": EXPECTED_FEATURE_COLUMNS_SHA256,
        "provenance_sha256": provenance_sha256,
        "family_counts": family_counts,
        "tolerance_policy_counts": tolerance_counts,
        "tolerance_policies": TOLERANCE_POLICIES,
        "feature_records": records,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return doc


if __name__ == "__main__":
    doc = generate_provenance_map()
    print("Provenance map generated successfully!")
    print(f"File: {OUTPUT_PATH}")
    print(f"Total features: {doc['expected_feature_count']}")
    print(f"Provenance SHA256: {doc['provenance_sha256']}")
    print("Family counts:", doc["family_counts"])
    print("Tolerance counts:", doc["tolerance_policy_counts"])
