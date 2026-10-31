from __future__ import annotations

import dataclasses
import importlib
import importlib.util
from pathlib import Path
from typing import Any


RUNNER_PATH = (
    Path(__file__)
    .resolve()
    .parent
    /
    "run_xauusd_gate_15d_c_b2d_g7_h_e_a_r03_collector_controller_freeze.py"
)


spec = importlib.util.spec_from_file_location(
    "g7hea",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g7hea: Any = (
    importlib.util.module_from_spec(
        spec
    )
)

spec.loader.exec_module(
    g7hea
)


controller: Any = importlib.import_module(
    "02_AI.Models."
    "r03_prospective_collection_controller"
)

runtime: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_r03_prospective_runtime"
)

maturer: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_r03_prospective_outcome_maturer"
)

contract: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_r03_prospective_forward_validation_contract"
)


@dataclasses.dataclass(
    frozen=True
)
class FakeRecord:

    logical_observation_id: str

    decision_time_utc: str = (
        "2026-10-05T10:00:00Z"
    )


def fake(
    logical_id: str,
    *,
    decision_time: str = (
        "2026-10-05T10:00:00Z"
    ),
) -> FakeRecord:

    return FakeRecord(
        logical_observation_id=(
            logical_id
        ),
        decision_time_utc=(
            decision_time
        ),
    )


def test_01_base_commit_exact() -> None:

    assert (
        g7hea.BASE_AUTHORITY_COMMIT
        ==
        "d9ad9e5b1c5deb2e3b62f6110a1f5b4ffe934d08"
    )


def test_02_controller_version() -> None:

    assert (
        controller.CONTROLLER_VERSION
        ==
        "R03_PROSPECTIVE_COLLECTION_CONTROLLER_V1"
    )


def test_03_collection_policy_exact() -> None:

    assert (
        controller.COLLECTION_POLICY
        ==
        "SINGLE_PENDING_NON_OVERLAPPING_PROSPECTIVE_SAMPLE"
    )


def test_04_single_collector_required() -> None:

    assert (
        controller.SINGLE_COLLECTOR_PROCESS_REQUIRED
        is True
    )


def test_05_max_pending_one() -> None:

    assert (
        controller.MAX_PENDING_OBSERVATIONS
        ==
        1
    )


def test_06_minimum_matured_exact() -> None:

    assert (
        controller.MINIMUM_MATURED_OUTCOMES
        ==
        contract.MINIMUM_MATURED_OUTCOMES
        ==
        60
    )


def test_07_minimum_distinct_dates_exact() -> None:

    assert (
        controller.MINIMUM_DISTINCT_OBSERVATION_UTC_DATES
        ==
        contract.MINIMUM_DISTINCT_OBSERVATION_UTC_DATES
        ==
        5
    )


def test_08_observation_path_exact() -> None:

    assert (
        controller.OBSERVATION_LEDGER_RELATIVE_PATH
        ==
        runtime.OBSERVATION_LEDGER_RELATIVE_PATH
    )


def test_09_anchor_path_exact() -> None:

    assert (
        controller.ANCHOR_LEDGER_RELATIVE_PATH
        ==
        runtime.ANCHOR_LEDGER_RELATIVE_PATH
    )


def test_10_outcome_path_exact() -> None:

    assert (
        controller.OUTCOME_LEDGER_RELATIVE_PATH
        ==
        maturer.OUTCOME_LEDGER_RELATIVE_PATH
        ==
        runtime.OUTCOME_LEDGER_RELATIVE_PATH
    )


def test_11_empty_state_requests_capture() -> None:

    state = (
        controller
        .derive_state_from_records(
            observations={},
            anchors={},
            outcomes={},
        )
    )

    assert (
        state.next_action
        ==
        controller.ACTION_CAPTURE_NEW_OBSERVATION
    )


def test_12_empty_state_not_target() -> None:

    state = (
        controller
        .derive_state_from_records(
            observations={},
            anchors={},
            outcomes={},
        )
    )

    assert (
        state.collection_target_reached
        is False
    )


def test_13_one_pending_requests_maturity_check() -> None:

    logical_id = "a" * 64

    state = (
        controller
        .derive_state_from_records(
            observations={
                logical_id: fake(
                    logical_id
                )
            },
            anchors={
                logical_id: fake(
                    logical_id
                )
            },
            outcomes={},
        )
    )

    assert (
        state.next_action
        ==
        controller.ACTION_CHECK_PENDING_MATURITY
    )

    assert (
        state.pending_count
        ==
        1
    )


def test_14_pending_id_preserved() -> None:

    logical_id = "b" * 64

    state = (
        controller
        .derive_state_from_records(
            observations={
                logical_id: fake(
                    logical_id
                )
            },
            anchors={
                logical_id: fake(
                    logical_id
                )
            },
            outcomes={},
        )
    )

    assert (
        state.pending_logical_observation_id
        ==
        logical_id
    )


def test_15_matured_sample_allows_next_capture() -> None:

    logical_id = "c" * 64

    record = fake(
        logical_id
    )

    state = (
        controller
        .derive_state_from_records(
            observations={
                logical_id: record
            },
            anchors={
                logical_id: record
            },
            outcomes={
                logical_id: record
            },
        )
    )

    assert (
        state.next_action
        ==
        controller.ACTION_CAPTURE_NEW_OBSERVATION
    )

    assert (
        state.matured_outcome_count
        ==
        1
    )


def test_16_orphan_anchor_requires_review() -> None:

    logical_id = "d" * 64

    state = (
        controller
        .derive_state_from_records(
            observations={},
            anchors={
                logical_id: fake(
                    logical_id
                )
            },
            outcomes={},
        )
    )

    assert (
        state.next_action
        ==
        controller.ACTION_REVIEW_ORPHAN_ANCHOR
    )


def test_17_observation_without_anchor_blocked() -> None:

    logical_id = "e" * 64

    try:

        controller.derive_state_from_records(
            observations={
                logical_id: fake(
                    logical_id
                )
            },
            anchors={},
            outcomes={},
        )

    except controller.R03LedgerStateError:

        return

    raise AssertionError(
        "observation without anchor was accepted"
    )


def test_18_outcome_without_observation_blocked() -> None:

    logical_id = "f" * 64

    try:

        controller.derive_state_from_records(
            observations={},
            anchors={
                logical_id: fake(
                    logical_id
                )
            },
            outcomes={
                logical_id: fake(
                    logical_id
                )
            },
        )

    except controller.R03LedgerStateError:

        return

    raise AssertionError(
        "outcome without observation was accepted"
    )


def test_19_multiple_pending_blocked() -> None:

    first = "1" * 64
    second = "2" * 64

    try:

        controller.derive_state_from_records(
            observations={
                first: fake(
                    first
                ),
                second: fake(
                    second
                ),
            },
            anchors={
                first: fake(
                    first
                ),
                second: fake(
                    second
                ),
            },
            outcomes={},
        )

    except controller.R03LedgerStateError:

        return

    raise AssertionError(
        "multiple pending observations were accepted"
    )


def test_20_distinct_dates_count_matured_only() -> None:

    first = "3" * 64
    second = "4" * 64

    state = (
        controller
        .derive_state_from_records(
            observations={
                first: fake(
                    first,
                    decision_time=(
                        "2026-10-05T10:00:00Z"
                    ),
                ),
                second: fake(
                    second,
                    decision_time=(
                        "2026-10-06T10:00:00Z"
                    ),
                ),
            },
            anchors={
                first: fake(
                    first
                ),
                second: fake(
                    second
                ),
            },
            outcomes={
                first: fake(
                    first
                )
            },
        )
    )

    assert (
        state.distinct_matured_observation_utc_dates
        ==
        1
    )


def test_21_target_requires_60_outcomes() -> None:

    observations = {}
    anchors = {}
    outcomes = {}

    for index in range(
        59
    ):

        logical_id = (
            f"{index:064x}"
        )

        date = (
            5
            +
            (
                index
                %
                5
            )
        )

        record = fake(
            logical_id,
            decision_time=(
                f"2026-10-{date:02d}T10:00:00Z"
            ),
        )

        observations[
            logical_id
        ] = record

        anchors[
            logical_id
        ] = record

        outcomes[
            logical_id
        ] = record

    state = (
        controller
        .derive_state_from_records(
            observations=observations,
            anchors=anchors,
            outcomes=outcomes,
        )
    )

    assert (
        state.collection_target_reached
        is False
    )


def test_22_target_requires_five_dates() -> None:

    observations = {}
    anchors = {}
    outcomes = {}

    for index in range(
        60
    ):

        logical_id = (
            f"{index + 100:064x}"
        )

        date = (
            5
            +
            (
                index
                %
                4
            )
        )

        record = fake(
            logical_id,
            decision_time=(
                f"2026-10-{date:02d}T10:00:00Z"
            ),
        )

        observations[
            logical_id
        ] = record

        anchors[
            logical_id
        ] = record

        outcomes[
            logical_id
        ] = record

    state = (
        controller
        .derive_state_from_records(
            observations=observations,
            anchors=anchors,
            outcomes=outcomes,
        )
    )

    assert (
        state.collection_target_reached
        is False
    )


def test_23_target_reached_at_60_and_five_dates() -> None:

    observations = {}
    anchors = {}
    outcomes = {}

    for index in range(
        60
    ):

        logical_id = (
            f"{index + 200:064x}"
        )

        date = (
            5
            +
            (
                index
                %
                5
            )
        )

        record = fake(
            logical_id,
            decision_time=(
                f"2026-10-{date:02d}T10:00:00Z"
            ),
        )

        observations[
            logical_id
        ] = record

        anchors[
            logical_id
        ] = record

        outcomes[
            logical_id
        ] = record

    state = (
        controller
        .derive_state_from_records(
            observations=observations,
            anchors=anchors,
            outcomes=outcomes,
        )
    )

    assert (
        state.collection_target_reached
        is True
    )

    assert (
        state.next_action
        ==
        controller.ACTION_COLLECTION_TARGET_REACHED
    )


def test_24_controller_uses_r03_runtime_binder() -> None:

    text = Path(
        controller.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "R03ProspectiveRuntimeBinder"
        in text
    )


def test_25_controller_uses_r03_frozen_artifact() -> None:

    text = Path(
        controller.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "R03FrozenArtifactInferenceAdapter"
        in text
    )


def test_26_anchor_first_persistence_reused() -> None:

    text = Path(
        controller.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "persist_anchor_first"
        in text
    )


def test_27_controller_uses_r03_maturer() -> None:

    text = Path(
        controller.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "mature_observation"
        in text
    )


def test_28_insufficient_future_bars_waits() -> None:

    text = Path(
        controller.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "WAIT_FOR_MORE_COMPLETED_M5_BARS"
        in text
    )


def test_29_no_model_fit() -> None:

    text = Path(
        controller.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert ".fit(" not in text


def test_30_no_test_partition_access() -> None:

    text = Path(
        controller.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "load_test" not in text


def test_31_no_validation_partition_access() -> None:

    text = Path(
        controller.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "load_validation" not in text


def test_32_no_old_forward30_access() -> None:

    text = Path(
        controller.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "xauusd_frozen_c04_forward_outcomes"
        not in text
    )


def test_33_controller_has_no_mt5_import() -> None:

    text = Path(
        controller.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text


def test_34_freeze_runner_has_no_mt5_import() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text


def test_35_freeze_runner_does_not_capture() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "capture_new_observation_from_snapshot("
        not in text
    )


def test_36_freeze_runner_does_not_mature() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "mature_pending_from_snapshot("
        not in text
    )


def test_37_performance_blocked() -> None:

    assert (
        controller.PERFORMANCE_EVALUATION_AUTHORIZED
        is False
    )


def test_38_pnl_blocked() -> None:

    assert (
        controller.PNL_EVALUATION_AUTHORIZED
        is False
    )


def test_39_live_blocked() -> None:

    assert (
        controller.LIVE_AUTHORIZED
        is False
    )


def test_40_execution_blocked() -> None:

    assert (
        controller.EXECUTION_AUTHORIZED
        is False
    )