from __future__ import annotations

import importlib

import pytest


monitor = importlib.import_module(
    "04_Testing.production_portability."
    "r03_market_intelligence_monitor"
)


def test_balanced_predictions():
    report = monitor.analyze_probabilities([
        (0.8, 0.1, 0.1),
        (0.1, 0.8, 0.1),
        (0.1, 0.1, 0.8),
    ])

    assert report["observation_count"] == 3
    assert report["unique_predicted_classes"] == 3
    assert report["predicted_class_distribution"] == {
        "SHORT": 1,
        "NO_TRADE": 1,
        "LONG": 1,
    }


def test_repeated_class_detected():
    report = monitor.analyze_probabilities([
        (0.7, 0.2, 0.1),
        (0.6, 0.2, 0.2),
    ])

    assert report["unique_predicted_classes"] == 1
    assert report["predicted_class_share"]["SHORT"] == 1.0


def test_invalid_probabilities_blocked():
    with pytest.raises(
        monitor.MarketIntelligenceError,
        match="PROBABILITIES_NOT_NORMALIZED",
    ):
        monitor.analyze_probabilities([
            (0.9, 0.9, 0.9),
        ])


def test_no_data_blocked():
    with pytest.raises(
        monitor.MarketIntelligenceError,
        match="NO_PROSPECTIVE_OBSERVATIONS",
    ):
        monitor.analyze_probabilities([])


def test_no_execution_authorization():
    report = monitor.analyze_probabilities([
        (0.2, 0.6, 0.2),
    ])

    assert report["predictive_edge_established"] is False
    assert report["market_regime_identified"] is False
    assert report["model_retraining_authorized"] is False
    assert report["live_authorized"] is False
    assert report["execution_authorized"] is False