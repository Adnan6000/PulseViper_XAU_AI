"""
===============================================================================
Module      : test_frozen_331_parity.py
Project     : PulseViper XAU AI
Purpose     : Parity Harness: Production Pipeline vs Frozen TRAIN Lineage (Gate 13)
===============================================================================

Validates that the production feature pipeline reproduces the exact frozen
331-feature model input contract across non-holdout TRAIN research evidence.

Safety:
- Strictly consumes non-holdout TRAIN rows via Portable331TrainingInputLoader.
- Never reads or executes VALIDATION or TEST holdout partitions.
- Never refits or retrains models.
- live_authorized = false.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

pipeline_mod = importlib.import_module("02_AI.Features.portable_feature_pipeline")
contract_mod = importlib.import_module("02_AI.Features.portable_feature_contract")
loader_mod = importlib.import_module("02_AI.Dataset.portable_331_training_input_loader")

PortableFeaturePipeline = pipeline_mod.PortableFeaturePipeline
Portable331TrainingInputLoader = loader_mod.Portable331TrainingInputLoader
EXPECTED_FEATURE_COUNT = contract_mod.EXPECTED_FEATURE_COUNT
EXPECTED_FEATURE_COLUMNS_SHA256 = contract_mod.EXPECTED_FEATURE_COLUMNS_SHA256


@pytest.fixture(scope="module")
def parity_verification_data() -> dict[str, Any]:
    """Load reference non-holdout TRAIN batch and raw execution snapshots for parity."""
    canonical_root = REPO_ROOT / "01_Data" / "Canonical"
    base_raw_path = canonical_root / "Instruments" / "XAUUSD" / "execution" / "scope_3ce3991250300a0ed5b5cafdd6825e73c9d3d52ede1b096d8e40708d9d8c2e95" / "historical"

    loader = Portable331TrainingInputLoader(canonical_root=canonical_root)
    train_batch = loader.load_train_features()

    # Load canonical snapshot slices containing the initial TRAIN evaluation window
    market_data = {
        "M5": pd.read_csv(base_raw_path / "M5" / "XAUUSD_XAUUSDm_M5_699191ac65db6057.csv").head(500),
        "M15": pd.read_csv(base_raw_path / "M15" / "XAUUSD_XAUUSDm_M15_28195707834fb8fa.csv").iloc[:67000],
        "M30": pd.read_csv(base_raw_path / "M30" / "XAUUSD_XAUUSDm_M30_b35bc4321456c259.csv").iloc[:83600],
        "H1": pd.read_csv(base_raw_path / "H1" / "XAUUSD_XAUUSDm_H1_13564bb5982dc309.csv").iloc[:48450],
        "H4": pd.read_csv(base_raw_path / "H4" / "XAUUSD_XAUUSDm_H4_d29fdd08a542b1d7.csv").iloc[:13820],
        "D1": pd.read_csv(base_raw_path / "D1" / "XAUUSD_XAUUSDm_D1_888ef01b91799cb1.csv").iloc[:3440],
    }

    pipeline = PortableFeaturePipeline()
    prod_result = pipeline.generate(market_data, symbol="XAUUSD")

    prov_path = REPO_ROOT / "04_Testing" / "evidence" / "production_portability" / "xauusd_portable_331_feature_provenance_map.json"
    with open(prov_path, "r", encoding="utf-8") as f:
        provenance = json.load(f)

    return {
        "train_batch": train_batch,
        "prod_result": prod_result,
        "provenance": provenance,
    }


def test_parity_contract_metadata(parity_verification_data: dict[str, Any]) -> None:
    """Verify high-level contract metadata match between production result and frozen lineage."""
    train_batch = parity_verification_data["train_batch"]
    prod_result = parity_verification_data["prod_result"]

    assert prod_result.feature_count == EXPECTED_FEATURE_COUNT
    assert prod_result.feature_columns_sha256 == EXPECTED_FEATURE_COLUMNS_SHA256
    assert prod_result.feature_columns_sha256 == train_batch.feature_columns_sha256
    assert tuple(prod_result.feature_names) == train_batch.feature_columns


def test_parity_feature_values_on_train_reference_rows(parity_verification_data: dict[str, Any]) -> None:
    """
    Verify feature-by-feature numerical parity across all 331 features
    against non-holdout TRAIN research evidence using explicit family tolerance policies.
    """
    train_batch = parity_verification_data["train_batch"]
    prod_result = parity_verification_data["prod_result"]
    provenance = parity_verification_data["provenance"]

    tol_map = {r["feature_name"]: r["tolerance_policy"] for r in provenance["feature_records"]}

    prod_dts = list(pd.to_datetime(list(prod_result.decision_times), utc=True))
    frozen_dts = list(pd.to_datetime(list(train_batch.decision_time), utc=True))

    dt_to_prod_idx = {dt: idx for idx, dt in enumerate(prod_dts)}
    dt_to_frozen_idx = {dt: idx for idx, dt in enumerate(frozen_dts)}

    common_dts = sorted(list(set(dt_to_prod_idx.keys()).intersection(set(dt_to_frozen_idx.keys()))))
    assert len(common_dts) >= 100, f"Expected at least 100 common comparison rows, got {len(common_dts)}"

    mismatches = []
    max_diffs: dict[str, float] = {}

    for dt in common_dts:
        prod_idx = dt_to_prod_idx[dt]
        frozen_idx = dt_to_frozen_idx[dt]

        p_row = prod_result.features.iloc[prod_idx]
        f_row = train_batch.X[frozen_idx]

        for c_idx, col in enumerate(train_batch.feature_columns):
            p_val = float(p_row[col])
            f_val = float(f_row[c_idx])
            diff = abs(p_val - f_val)

            tol_policy = tol_map[col]
            max_diffs[tol_policy] = max(max_diffs.get(tol_policy, 0.0), diff)

            if tol_policy in ("EXACT_DISCRETE", "INTEGER_COUNT"):
                if diff != 0.0:
                    mismatches.append((str(dt), col, tol_policy, f_val, p_val, diff))
            elif tol_policy == "FLOAT32_TRIGONOMETRIC":
                if diff > 1e-5:
                    mismatches.append((str(dt), col, tol_policy, f_val, p_val, diff))
            else:  # FLOAT32_NUMERIC
                if diff > 1e-4:
                    mismatches.append((str(dt), col, tol_policy, f_val, p_val, diff))

    assert len(mismatches) == 0, f"Found {len(mismatches)} parity mismatches! First 5: {mismatches[:5]}"
    # Exact discrete and integer must have 0.0 max diff
    assert max_diffs.get("EXACT_DISCRETE", 0.0) == 0.0
    assert max_diffs.get("INTEGER_COUNT", 0.0) == 0.0
