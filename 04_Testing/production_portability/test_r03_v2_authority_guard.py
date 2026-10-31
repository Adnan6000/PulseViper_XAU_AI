
from __future__ import annotations

import importlib

import pytest


g = importlib.import_module(
    "04_Testing.production_portability.r03_v2_authority_guard"
)


def fixture():
    original = dict(
        observation_count=14,
        anchor_count=14,
        matured_outcome_count=13,
        pending_count=1,
        pending_logical_observation_id=g.EXPECTED_ID,
    )

    candidate = dict(
        observations=14,
        anchors=14,
        matured_outcomes=13,
        terminal_exclusions=1,
        unresolved_pending=0,
    )

    terminal = dict(
        logical_observation_id=g.EXPECTED_ID,
        counts_as_matured_outcome=False,
        source_event_fingerprint_sha256="a" * 64,
    )

    evidence = dict(
        logical_observation_id=g.EXPECTED_ID,
        terminal_exclusion_authorized=False,
        controller_promotion_authorized=False,
        event_fingerprint_sha256="a" * 64,
    )

    return original, candidate, terminal, evidence


def evaluate(vals):
    a, b, c, d = vals

    return g.validate_recovery(
        original=a,
        candidate=b,
        terminal=c,
        evidence=d,
    )


def test_current_state_remains_blocked():
    result = evaluate(fixture())

    assert result["effective_unresolved_pending_count"] == 1

    assert result["capture_authorized"] is False

    assert result["matured_outcome_count"] == 13


@pytest.mark.parametrize(
    "index,key,value",
    [
        (0, "observation_count", 15),
        (0, "matured_outcome_count", 14),
        (0, "pending_count", 0),
        (0, "pending_logical_observation_id", "bad"),
        (1, "terminal_exclusions", 0),
        (1, "unresolved_pending", 1),
        (2, "counts_as_matured_outcome", True),
        (2, "source_event_fingerprint_sha256", "b" * 64),
        (3, "terminal_exclusion_authorized", True),
        (3, "controller_promotion_authorized", True),
    ],
)
def test_fail_closed(index, key, value):
    vals = list(fixture())

    vals[index][key] = value

    with pytest.raises(g.AuthorityError):
        evaluate(vals)
