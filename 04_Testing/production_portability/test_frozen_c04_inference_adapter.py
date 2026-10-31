"""
===============================================================================
Module      : test_frozen_c04_inference_adapter.py
Project     : PulseViper XAU AI
Purpose     : Comprehensive Unit & Contract Tests for Gate 14 Inference Adapter
===============================================================================

Validates all 30 core contract requirements for FrozenC04InferenceAdapter:
1. Correct model SHA accepted
2. Incorrect SHA rejected
3. Model file missing rejected
4. Exact 331 feature contract accepted
5. Feature count mismatch rejected
6. Feature order mismatch rejected
7. Renamed column rejected
8. Duplicate feature names rejected
9. NaN rejected
10. +inf/-inf rejected
11. Malformed dtype rejected
12. Single-row inference
13. Multi-row inference
14. Row-order preservation
15. Probability shape (N, 3)
16. Finite probabilities
17. Probability bounds [0, 1]
18. Probability sums approximately 1.0
19. Exact class order [-1, 0, 1]
20. SHORT mapping
21. NO_TRADE mapping
22. LONG mapping
23. Argmax decision rule
24. Deterministic repeated inference
25. Direct model vs adapter probability parity
26. Direct model vs adapter class parity
27. Immutable result dataclass
28. live_authorized is always False
29. shadow_authorized is always False
30. No trading runtime dependencies imported or called

Safety:
- Consumes ONLY synthetic matrices or authorized non-holdout TRAIN rows.
- NEVER reads or executes VALIDATION or TEST holdouts.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

adapter_mod = importlib.import_module("02_AI.Models.frozen_c04_inference_adapter")
contract_mod = importlib.import_module("02_AI.Features.portable_feature_contract")
loader_mod = importlib.import_module("02_AI.Dataset.portable_331_training_input_loader")

FrozenC04InferenceAdapter = adapter_mod.FrozenC04InferenceAdapter
FrozenC04InferenceError = adapter_mod.FrozenC04InferenceError
FrozenC04InferenceRow = adapter_mod.FrozenC04InferenceRow
FrozenC04InferenceBatch = adapter_mod.FrozenC04InferenceBatch
LABEL_MAP = adapter_mod.LABEL_MAP

EXPECTED_FEATURE_COUNT = contract_mod.EXPECTED_FEATURE_COUNT
EXPECTED_FEATURE_COLUMNS_SHA256 = contract_mod.EXPECTED_FEATURE_COLUMNS_SHA256
FROZEN_MODEL_SHA256 = contract_mod.FROZEN_MODEL_SHA256
FROZEN_MODEL_CLASSES = contract_mod.FROZEN_MODEL_CLASSES
FROZEN_FEATURE_COLUMNS = contract_mod.FROZEN_FEATURE_COLUMNS
Portable331TrainingInputLoader = loader_mod.Portable331TrainingInputLoader


@pytest.fixture(scope="module")
def adapter() -> FrozenC04InferenceAdapter:
    """Instantiate the authoritative frozen C04 adapter."""
    return FrozenC04InferenceAdapter()


@pytest.fixture(scope="module")
def sample_features_df() -> pd.DataFrame:
    """Create a valid synthetic DataFrame matching the 331 feature schema."""
    np.random.seed(42)
    data = np.random.randn(10, EXPECTED_FEATURE_COUNT).astype(np.float32)
    return pd.DataFrame(data, columns=list(FROZEN_FEATURE_COLUMNS))


@pytest.fixture(scope="module")
def sample_train_rows() -> tuple[np.ndarray, list[str]]:
    """Load sample non-holdout TRAIN rows for parity testing."""
    canonical_root = REPO_ROOT / "01_Data" / "Canonical"
    loader = Portable331TrainingInputLoader(canonical_root=canonical_root)
    batch = loader.load_train_features()
    return batch.X[:50], list(batch.decision_time[:50])


# -----------------------------------------------------------------------------
# Test Cases 1-3: Model File & SHA Verification
# -----------------------------------------------------------------------------

def test_01_correct_model_sha_accepted(adapter: FrozenC04InferenceAdapter) -> None:
    """1. Correct model artifact and SHA256 accepted at startup."""
    assert adapter.model_sha256 == FROZEN_MODEL_SHA256
    assert adapter.model_class == "ExtraTreesClassifier"
    assert adapter.n_features_in == EXPECTED_FEATURE_COUNT
    assert adapter.classes == FROZEN_MODEL_CLASSES


def test_02_incorrect_sha_rejected(tmp_path: Path) -> None:
    """2. Incorrect SHA256 raises FrozenC04InferenceError."""
    fake_model = tmp_path / "fake_model.joblib"
    fake_model.write_bytes(b"corrupt model payload")
    with pytest.raises(FrozenC04InferenceError, match="SHA256 mismatch"):
        FrozenC04InferenceAdapter(model_path=fake_model)


def test_03_model_file_missing_rejected(tmp_path: Path) -> None:
    """3. Missing model file raises FrozenC04InferenceError."""
    missing_path = tmp_path / "non_existent_model.joblib"
    with pytest.raises(FrozenC04InferenceError, match="missing at resolved path"):
        FrozenC04InferenceAdapter(model_path=missing_path)


# -----------------------------------------------------------------------------
# Test Cases 4-8: Feature Contract & Ordering Verification
# -----------------------------------------------------------------------------

def test_04_exact_331_feature_contract_accepted(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """4. Exact 331-feature schema is accepted."""
    batch = adapter.infer(sample_features_df)
    assert len(batch) == len(sample_features_df)
    assert batch.feature_count == EXPECTED_FEATURE_COUNT
    assert batch.feature_columns_sha256 == EXPECTED_FEATURE_COLUMNS_SHA256


def test_05_feature_count_mismatch_rejected(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """5. Feature count mismatch (< or > 331) is rejected fail-closed."""
    df_fewer = sample_features_df.iloc[:, :-1]
    with pytest.raises(FrozenC04InferenceError, match="column count mismatch"):
        adapter.infer(df_fewer)

    df_more = sample_features_df.copy()
    df_more["extra_feature"] = 0.0
    with pytest.raises(FrozenC04InferenceError, match="column count mismatch"):
        adapter.infer(df_more)


def test_06_feature_order_mismatch_rejected(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """6. Swapped or reordered feature columns are rejected fail-closed."""
    cols = list(sample_features_df.columns)
    # Swap first two columns
    cols[0], cols[1] = cols[1], cols[0]
    df_reordered = sample_features_df[cols]
    with pytest.raises(FrozenC04InferenceError, match="contract failed"):
        adapter.infer(df_reordered)


def test_07_renamed_column_rejected(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """7. Renamed feature column is rejected fail-closed."""
    df_renamed = sample_features_df.rename(columns={FROZEN_FEATURE_COLUMNS[0]: "renamed_col"})
    with pytest.raises(FrozenC04InferenceError, match="contract failed"):
        adapter.infer(df_renamed)


def test_08_duplicate_feature_names_rejected(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """8. Duplicate feature names in DataFrame are rejected fail-closed."""
    cols = list(sample_features_df.columns)
    cols[1] = cols[0]  # Duplicate first column name
    df_dupe = sample_features_df.copy()
    df_dupe.columns = cols
    with pytest.raises(FrozenC04InferenceError, match="contract failed"):
        adapter.infer(df_dupe)


# -----------------------------------------------------------------------------
# Test Cases 9-11: Data Type & Numerical Validity Rejections
# -----------------------------------------------------------------------------

def test_09_nan_rejected(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """9. NaN values in features are rejected fail-closed."""
    df_nan = sample_features_df.copy()
    df_nan.iloc[2, 5] = np.nan
    with pytest.raises(FrozenC04InferenceError, match="contain NaN"):
        adapter.infer(df_nan)


def test_10_inf_rejected(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """10. +inf / -inf values are rejected fail-closed."""
    df_inf = sample_features_df.copy()
    df_inf.iloc[1, 10] = np.inf
    with pytest.raises(FrozenC04InferenceError, match="contain NaN, \\+inf, or -inf"):
        adapter.infer(df_inf)

    df_neginf = sample_features_df.copy()
    df_neginf.iloc[1, 10] = -np.inf
    with pytest.raises(FrozenC04InferenceError, match="contain NaN, \\+inf, or -inf"):
        adapter.infer(df_neginf)


def test_11_malformed_dtype_rejected(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """11. Object / string columns are rejected fail-closed."""
    df_str = sample_features_df.copy()
    df_str[FROZEN_FEATURE_COLUMNS[0]] = "invalid_string_val"
    with pytest.raises(FrozenC04InferenceError, match="Non-numeric dtype"):
        adapter.infer(df_str)


# -----------------------------------------------------------------------------
# Test Cases 12-14: Single-Row, Multi-Row, and Ordering Preservation
# -----------------------------------------------------------------------------

def test_12_single_row_inference(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """12. Single-row inference returns typed FrozenC04InferenceRow."""
    row_df = sample_features_df.iloc[[0]]
    row_result = adapter.infer_single(row_df, decision_time="2026-01-01T12:00:00Z")
    assert isinstance(row_result, FrozenC04InferenceRow)
    assert row_result.decision_time == "2026-01-01T12:00:00Z"
    assert row_result.predicted_class in (-1, 0, 1)
    assert row_result.predicted_label in ("SHORT", "NO_TRADE", "LONG")


def test_13_multi_row_inference(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """13. Multi-row batch inference returns typed FrozenC04InferenceBatch."""
    batch = adapter.infer(sample_features_df)
    assert isinstance(batch, FrozenC04InferenceBatch)
    assert len(batch) == 10
    assert len(batch.rows) == 10
    assert batch.probabilities.shape == (10, 3)
    assert batch.predicted_classes.shape == (10,)


def test_14_row_order_preservation(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """14. Row order is preserved exactly between input and output."""
    times = [f"2026-01-01T12:{i:02d}:00Z" for i in range(10)]
    batch = adapter.infer(sample_features_df, decision_times=times)
    for i, row in enumerate(batch):
        assert row.decision_time == times[i]


# -----------------------------------------------------------------------------
# Test Cases 15-18: Probability Distribution Guarantees
# -----------------------------------------------------------------------------

def test_15_probability_shape(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """15. Probability output has exact shape (N, 3)."""
    batch = adapter.infer(sample_features_df)
    assert batch.probabilities.shape == (len(sample_features_df), 3)


def test_16_finite_probabilities(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """16. All probability outputs are finite."""
    batch = adapter.infer(sample_features_df)
    assert np.all(np.isfinite(batch.probabilities))


def test_17_probability_bounds(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """17. All probabilities fall strictly within [0.0, 1.0]."""
    batch = adapter.infer(sample_features_df)
    assert np.all(batch.probabilities >= 0.0)
    assert np.all(batch.probabilities <= 1.0)


def test_18_probability_sums_to_one(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """18. Each row of probabilities sums to 1.0 within numerical tolerance."""
    batch = adapter.infer(sample_features_df)
    row_sums = np.sum(batch.probabilities, axis=1)
    assert np.all(np.isclose(row_sums, 1.0, atol=1e-4))


# -----------------------------------------------------------------------------
# Test Cases 19-23: Exact Class Order & Argmax Contract
# -----------------------------------------------------------------------------

def test_19_exact_class_order(adapter: FrozenC04InferenceAdapter) -> None:
    """19. Class order is verified as [-1, 0, 1]."""
    assert adapter.classes == (-1, 0, 1)


def test_20_short_mapping(adapter: FrozenC04InferenceAdapter) -> None:
    """20. Class -1 maps to label 'SHORT'."""
    assert LABEL_MAP[-1] == "SHORT"


def test_21_no_trade_mapping(adapter: FrozenC04InferenceAdapter) -> None:
    """21. Class 0 maps to label 'NO_TRADE'."""
    assert LABEL_MAP[0] == "NO_TRADE"


def test_22_long_mapping(adapter: FrozenC04InferenceAdapter) -> None:
    """22. Class 1 maps to label 'LONG'."""
    assert LABEL_MAP[1] == "LONG"


def test_23_argmax_decision_rule(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """23. Predicted class strictly follows classes_[argmax(proba)]."""
    batch = adapter.infer(sample_features_df)
    expected_indices = np.argmax(batch.probabilities, axis=1)
    expected_classes = np.array(FROZEN_MODEL_CLASSES)[expected_indices]
    assert np.array_equal(batch.predicted_classes, expected_classes)

    for i, row in enumerate(batch):
        assert row.predicted_class == expected_classes[i]
        assert row.winning_probability == batch.probabilities[i, expected_indices[i]]


# -----------------------------------------------------------------------------
# Test Case 24: Deterministic Repeated Inference
# -----------------------------------------------------------------------------

def test_24_deterministic_repeated_inference(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """24. Repeated inference on identical features yields deterministic results."""
    batch1 = adapter.infer(sample_features_df)
    batch2 = adapter.infer(sample_features_df)

    max_diff = np.max(np.abs(batch1.probabilities - batch2.probabilities))
    assert max_diff < 1e-12, f"Probabilities differed between runs: max_diff={max_diff}"
    assert np.array_equal(batch1.predicted_classes, batch2.predicted_classes)
    assert batch1.predicted_labels == batch2.predicted_labels


# -----------------------------------------------------------------------------
# Test Cases 25-26: Direct Model vs Adapter Parity
# -----------------------------------------------------------------------------

def test_25_direct_model_probability_parity(
    adapter: FrozenC04InferenceAdapter,
    sample_train_rows: tuple[np.ndarray, list[str]],
) -> None:
    """25. Adapter probabilities match direct model predict_proba."""
    X_sample, d_times = sample_train_rows
    direct_model = joblib.load(adapter.model_path)
    direct_proba = direct_model.predict_proba(X_sample)

    batch = adapter.infer(X_sample, decision_times=d_times)
    max_diff = np.max(np.abs(direct_proba - batch.probabilities))
    assert max_diff < 1e-12, f"Probability mismatch vs direct model: max_diff={max_diff}"


def test_26_direct_model_class_parity(
    adapter: FrozenC04InferenceAdapter,
    sample_train_rows: tuple[np.ndarray, list[str]],
) -> None:
    """26. Adapter predicted classes match direct model argmax classes."""
    X_sample, d_times = sample_train_rows
    direct_model = joblib.load(adapter.model_path)
    direct_proba = direct_model.predict_proba(X_sample)
    direct_preds = direct_model.classes_[np.argmax(direct_proba, axis=1)]

    batch = adapter.infer(X_sample, decision_times=d_times)
    assert np.array_equal(direct_preds, batch.predicted_classes)


# -----------------------------------------------------------------------------
# Test Cases 27-29: Safety & Immutability Flags
# -----------------------------------------------------------------------------

def test_27_immutable_result_dataclass(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """27. Result dataclass is frozen and immutable."""
    batch = adapter.infer(sample_features_df)
    row = batch[0]
    with pytest.raises(AttributeError):
        row.predicted_class = 1  # type: ignore[misc]


def test_28_live_authorized_always_false(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """28. live_authorized is strictly False on all results."""
    batch = adapter.infer(sample_features_df)
    assert batch.live_authorized is False
    for row in batch:
        assert row.live_authorized is False


def test_29_shadow_authorized_always_false(
    adapter: FrozenC04InferenceAdapter,
    sample_features_df: pd.DataFrame,
) -> None:
    """29. shadow_authorized is strictly False on all results."""
    batch = adapter.infer(sample_features_df)
    assert batch.shadow_authorized is False
    for row in batch:
        assert row.shadow_authorized is False


# -----------------------------------------------------------------------------
# Test Case 30: Isolation from Trading Runtime
# -----------------------------------------------------------------------------

def test_30_no_trading_runtime_dependency_imported() -> None:
    """30. Adapter module does not import RiskEngine, execution, or MT5 runtime."""
    with open(REPO_ROOT / "02_AI" / "Models" / "frozen_c04_inference_adapter.py", "r") as f:
        code = f.read()

    forbidden_terms = [
        "RiskEngine",
        "risk_engine",
        "trade_ready",
        "MetaTrader5",
        "order_send",
        "position_open",
        "account_protection",
        "execute_one_time",
    ]
    for term in forbidden_terms:
        assert term not in code, f"Forbidden runtime dependency '{term}' found in adapter module"
