from __future__ import annotations

import contextlib
import dataclasses
import datetime
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Generator, Mapping, cast

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier


REPO_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)


# =============================================================================
# Frozen authorities
# =============================================================================

RUNTIME_VERSION = (
    "FROZEN_R03_PROSPECTIVE_RUNTIME_V1"
)

OBSERVATION_SCHEMA_VERSION = (
    "R03_PROSPECTIVE_OBSERVATION_V1"
)

ANCHOR_SCHEMA_VERSION = (
    "R03_PROSPECTIVE_ANCHOR_V1"
)

WINNER_CANDIDATE_ID = (
    "R03_FLAT_EXTRA_TREES_SMOOTH"
)

WINNER_CANDIDATE_FINGERPRINT_SHA256 = (
    "ae644c7272a015c26daeaaa7e655120bd7a3e4d267b2acd0d1f235e10bfa2e5f"
)

ARTIFACT_RELATIVE_PATH = (
    "02_AI/Models/artifacts/"
    "xauusd_r03_train_only_frozen.joblib"
)

ARTIFACT_SHA256 = (
    "b5da550921ef227b847207cfbfe5774e86f083f1d3354069a9624a5029ea2a03"
)

MANIFEST_RELATIVE_PATH = (
    "02_AI/Models/artifacts/"
    "xauusd_r03_train_only_frozen_manifest.json"
)

MANIFEST_SHA256 = (
    "a1507666518e3289b0678525c0808fc91b45d54105ef1fb59f3c22fe5d52baf6"
)

PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256 = (
    "e70d8e26c8f4734c456022689d47de406fe3f8daf1827d01b7f0f0d7fe752b9e"
)

FORWARD_OUTCOME_CONTRACT_FINGERPRINT_SHA256 = (
    "01fe52a2f068fcc8fb2fc5b89dd7e19dc974fc2d967cfb791e75c3415804ce87"
)

FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

FEATURE_COUNT = 331

CLASS_ORDER = (
    -1,
    0,
    1,
)

LABEL_MAP = {
    -1: "SHORT",
    0: "NO_TRADE",
    1: "LONG",
}

EARLIEST_PROSPECTIVE_AUTHORITY_TIME_UTC = (
    "2026-10-03T04:32:41Z"
)

CANONICAL_INSTRUMENT = (
    "XAUUSD"
)

SOURCE_PROVENANCE = (
    "TRUE_FORWARD_OBSERVATION"
)

PREDICTION_RULE = (
    "ARGMAX_3CLASS_PROBABILITY"
)

OBSERVATION_LEDGER_RELATIVE_PATH = (
    "01_Data/Shadow/"
    "xauusd_r03_prospective_observations.jsonl"
)

ANCHOR_LEDGER_RELATIVE_PATH = (
    "01_Data/Shadow/"
    "xauusd_r03_prospective_forward_outcome_anchors.jsonl"
)

OUTCOME_LEDGER_RELATIVE_PATH = (
    "01_Data/Shadow/"
    "xauusd_r03_prospective_forward_outcomes.jsonl"
)

LIVE_AUTHORIZED = False
EXECUTION_AUTHORIZED = False
PERFORMANCE_EVALUATION_AUTHORIZED = False
PNL_EVALUATION_AUTHORIZED = False


_acquisition: Any = importlib.import_module(
    "02_AI.Adapters."
    "mt5_read_only_forward_acquisition_adapter"
)

_feature_generator_module: Any = importlib.import_module(
    "02_AI.Features.feature_generator"
)

FeatureGenerator: Any = (
    _feature_generator_module.FeatureGenerator
)


# =============================================================================
# Errors
# =============================================================================

class R03ProspectiveRuntimeError(
    RuntimeError
):
    pass


class ArtifactAuthorityError(
    R03ProspectiveRuntimeError
):
    pass


class ProspectiveFreshnessError(
    R03ProspectiveRuntimeError
):
    pass


class RuntimeLedgerError(
    R03ProspectiveRuntimeError
):
    pass


class RuntimeLedgerConflictError(
    RuntimeLedgerError
):
    pass


# =============================================================================
# Generic helpers
# =============================================================================

def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise R03ProspectiveRuntimeError(
            reason
        )


def sha256_file(
    path: Path,
) -> str:

    if not path.is_file():
        raise ArtifactAuthorityError(
            f"FILE_MISSING:{path}"
        )

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as handle:

        while True:

            block = handle.read(
                1024 * 1024
            )

            if not block:
                break

            digest.update(
                block
            )

    return digest.hexdigest()


def utc_timestamp(
    value: Any,
) -> pd.Timestamp:

    try:

        parsed = pd.Timestamp(
            value
        )

    except Exception as exc:

        raise R03ProspectiveRuntimeError(
            "INVALID_UTC_TIMESTAMP"
        ) from exc

    if parsed is pd.NaT:

        raise R03ProspectiveRuntimeError(
            "INVALID_UTC_TIMESTAMP"
        )

    timestamp = parsed

    if timestamp.tzinfo is None:

        raise R03ProspectiveRuntimeError(
            "TIMESTAMP_MUST_BE_TIMEZONE_AWARE"
        )

    converted = timestamp.tz_convert(
        "UTC"
    )

    if converted is pd.NaT:
        raise R03ProspectiveRuntimeError(
            "TIMESTAMP_UTC_CONVERSION_FAILED"
        )

    return cast(
        pd.Timestamp,
        converted,
    )


def utc_iso(
    value: Any,
) -> str:

    timestamp = utc_timestamp(
        value
    )

    output = timestamp.isoformat()

    if output.endswith(
        "+00:00"
    ):

        output = (
            output[
                :-6
            ]
            +
            "Z"
        )

    return output


def validate_sha256(
    value: Any,
    field: str,
) -> str:

    if not isinstance(
        value,
        str,
    ):
        raise R03ProspectiveRuntimeError(
            f"{field}_NOT_STRING"
        )

    normalized = (
        value.strip()
        .lower()
    )

    if (
        len(
            normalized
        )
        !=
        64
    ):

        raise R03ProspectiveRuntimeError(
            f"{field}_INVALID_SHA256"
        )

    if any(
        char
        not in
        "0123456789abcdef"
        for char
        in normalized
    ):
        raise R03ProspectiveRuntimeError(
            f"{field}_INVALID_SHA256"
        )

    return normalized


def require_finite_float(
    value: Any,
    field: str,
) -> float:

    if value is None:
        raise R03ProspectiveRuntimeError(
            f"{field}_MISSING"
        )

    try:
        number = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise R03ProspectiveRuntimeError(
            f"{field}_NOT_NUMERIC"
        ) from exc

    if not math.isfinite(
        number
    ):
        raise R03ProspectiveRuntimeError(
            f"{field}_NON_FINITE"
        )

    return number


def require_int(
    value: Any,
    field: str,
) -> int:

    if value is None:
        raise R03ProspectiveRuntimeError(
            f"{field}_MISSING"
        )

    try:
        number = int(
            value
        )

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise R03ProspectiveRuntimeError(
            f"{field}_NOT_INTEGER"
        ) from exc

    return number


def canonical_json_sha256(
    document: Mapping[str, Any],
) -> str:

    encoded = json.dumps(
        dict(
            document
        ),
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=False,
        allow_nan=False,
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        encoded
    ).hexdigest()


def enforce_prospective_freshness(
    decision_time_utc: str,
) -> None:

    decision = utc_timestamp(
        decision_time_utc
    )

    boundary = utc_timestamp(
        EARLIEST_PROSPECTIVE_AUTHORITY_TIME_UTC
    )

    if (
        decision
        <=
        boundary
    ):
        raise ProspectiveFreshnessError(
            (
                "DECISION_TIME_NOT_AFTER_"
                "PROSPECTIVE_AUTHORITY_BOUNDARY"
            )
        )


# =============================================================================
# Frozen inference adapter
# =============================================================================

@dataclasses.dataclass(
    frozen=True
)
class R03InferenceResult:

    probability_short: float

    probability_no_trade: float

    probability_long: float

    predicted_class: int

    predicted_label: str

    winning_probability: float


class R03FrozenArtifactInferenceAdapter:

    def __init__(
        self,
        *,
        repo_root: Path = REPO_ROOT,
    ) -> None:

        self._repo_root = (
            repo_root.resolve()
        )

        self._artifact_path = (
            self._repo_root
            /
            ARTIFACT_RELATIVE_PATH
        )

        self._manifest_path = (
            self._repo_root
            /
            MANIFEST_RELATIVE_PATH
        )

        self._manifest = (
            self._load_and_verify_manifest()
        )

        self._bundle = (
            self._load_and_verify_artifact()
        )

        estimator = self._bundle.get(
            "estimator"
        )

        if not isinstance(
            estimator,
            ExtraTreesClassifier,
        ):
            raise ArtifactAuthorityError(
                "ARTIFACT_ESTIMATOR_TYPE_MISMATCH"
            )

        self._estimator: ExtraTreesClassifier = (
            estimator
        )

    @property
    def artifact_sha256(
        self,
    ) -> str:

        return ARTIFACT_SHA256

    @property
    def feature_columns(
        self,
    ) -> tuple[str, ...]:

        raw = self._bundle.get(
            "feature_columns"
        )

        if not isinstance(
            raw,
            (
                list,
                tuple,
            ),
        ):
            raise ArtifactAuthorityError(
                "ARTIFACT_FEATURE_COLUMNS_INVALID"
            )

        return tuple(
            str(
                value
            )
            for value
            in raw
        )

    def _load_and_verify_manifest(
        self,
    ) -> Mapping[str, Any]:

        actual_hash = sha256_file(
            self._manifest_path
        )

        if (
            actual_hash
            !=
            MANIFEST_SHA256
        ):
            raise ArtifactAuthorityError(
                "R03_MANIFEST_HASH_MISMATCH"
            )

        try:

            value = json.loads(
                self._manifest_path.read_text(
                    encoding="utf-8"
                )
            )

        except Exception as exc:

            raise ArtifactAuthorityError(
                "R03_MANIFEST_READ_FAILED"
            ) from exc

        if not isinstance(
            value,
            dict,
        ):
            raise ArtifactAuthorityError(
                "R03_MANIFEST_NOT_OBJECT"
            )

        if (
            value.get(
                "artifact_sha256"
            )
            !=
            ARTIFACT_SHA256
        ):
            raise ArtifactAuthorityError(
                "MANIFEST_ARTIFACT_HASH_MISMATCH"
            )

        if (
            value.get(
                "candidate_id"
            )
            !=
            WINNER_CANDIDATE_ID
        ):
            raise ArtifactAuthorityError(
                "MANIFEST_CANDIDATE_ID_MISMATCH"
            )

        if (
            value.get(
                "candidate_fingerprint_sha256"
            )
            !=
            WINNER_CANDIDATE_FINGERPRINT_SHA256
        ):
            raise ArtifactAuthorityError(
                "MANIFEST_CANDIDATE_FINGERPRINT_MISMATCH"
            )

        if (
            value.get(
                "feature_columns_sha256"
            )
            !=
            FEATURE_COLUMNS_SHA256
        ):
            raise ArtifactAuthorityError(
                "MANIFEST_FEATURE_HASH_MISMATCH"
            )

        if (
            int(
                value.get(
                    "feature_count",
                    -1,
                )
            )
            !=
            FEATURE_COUNT
        ):
            raise ArtifactAuthorityError(
                "MANIFEST_FEATURE_COUNT_MISMATCH"
            )

        if (
            value.get(
                "train_only_fit"
            )
            is not True
        ):
            raise ArtifactAuthorityError(
                "MANIFEST_NOT_TRAIN_ONLY"
            )

        if (
            value.get(
                "validation_values_loaded"
            )
            is not False
        ):
            raise ArtifactAuthorityError(
                "MANIFEST_VALIDATION_ACCESS_VIOLATION"
            )

        if (
            value.get(
                "test_values_loaded"
            )
            is not False
        ):
            raise ArtifactAuthorityError(
                "MANIFEST_TEST_ACCESS_VIOLATION"
            )

        return value

    def _load_and_verify_artifact(
        self,
    ) -> Mapping[str, Any]:

        actual_hash = sha256_file(
            self._artifact_path
        )

        if (
            actual_hash
            !=
            ARTIFACT_SHA256
        ):
            raise ArtifactAuthorityError(
                "R03_ARTIFACT_HASH_MISMATCH"
            )

        try:

            value: Any = joblib.load(
                self._artifact_path
            )

        except Exception as exc:

            raise ArtifactAuthorityError(
                "R03_ARTIFACT_LOAD_FAILED"
            ) from exc

        if not isinstance(
            value,
            dict,
        ):
            raise ArtifactAuthorityError(
                "R03_ARTIFACT_NOT_MAPPING"
            )

        if (
            value.get(
                "candidate_id"
            )
            !=
            WINNER_CANDIDATE_ID
        ):
            raise ArtifactAuthorityError(
                "ARTIFACT_CANDIDATE_ID_MISMATCH"
            )

        if (
            value.get(
                "candidate_fingerprint_sha256"
            )
            !=
            WINNER_CANDIDATE_FINGERPRINT_SHA256
        ):
            raise ArtifactAuthorityError(
                "ARTIFACT_CANDIDATE_FINGERPRINT_MISMATCH"
            )

        if (
            value.get(
                "feature_columns_sha256"
            )
            !=
            FEATURE_COLUMNS_SHA256
        ):
            raise ArtifactAuthorityError(
                "ARTIFACT_FEATURE_HASH_MISMATCH"
            )

        return value

    def infer_single(
        self,
        feature_row: Any,
    ) -> R03InferenceResult:

        if isinstance(
            feature_row,
            pd.Series,
        ):

            columns = tuple(
                str(
                    value
                )
                for value
                in feature_row.index
            )

            if (
                columns
                !=
                self.feature_columns
            ):
                raise ArtifactAuthorityError(
                    "INFERENCE_FEATURE_ORDER_MISMATCH"
                )

            matrix = (
                feature_row
                .to_numpy(
                    dtype=np.float64
                )
                .reshape(
                    1,
                    -1,
                )
            )

        elif isinstance(
            feature_row,
            pd.DataFrame,
        ):

            if (
                len(
                    feature_row
                )
                !=
                1
            ):
                raise ArtifactAuthorityError(
                    "INFERENCE_DATAFRAME_MUST_HAVE_ONE_ROW"
                )

            columns = tuple(
                str(
                    value
                )
                for value
                in feature_row.columns
            )

            if (
                columns
                !=
                self.feature_columns
            ):
                raise ArtifactAuthorityError(
                    "INFERENCE_FEATURE_ORDER_MISMATCH"
                )

            matrix = feature_row.to_numpy(
                dtype=np.float64
            )

        else:

            matrix = np.asarray(
                feature_row,
                dtype=np.float64,
            )

            if (
                matrix.ndim
                ==
                1
            ):

                matrix = matrix.reshape(
                    1,
                    -1,
                )

        if (
            matrix.shape
            !=
            (
                1,
                FEATURE_COUNT,
            )
        ):
            raise ArtifactAuthorityError(
                (
                    "INFERENCE_MATRIX_SHAPE_MISMATCH:"
                    f"{matrix.shape}"
                )
            )

        if not bool(
            np.isfinite(
                matrix
            ).all()
        ):
            raise ArtifactAuthorityError(
                "INFERENCE_MATRIX_NON_FINITE"
            )

        probabilities_raw = np.asarray(
            self._estimator.predict_proba(
                matrix
            ),
            dtype=np.float64,
        )

        classes = tuple(
            int(
                value
            )
            for value
            in self._estimator.classes_
        )

        if any(
            label
            not in
            classes
            for label
            in CLASS_ORDER
        ):
            raise ArtifactAuthorityError(
                "ARTIFACT_CLASS_ORDER_INCOMPLETE"
            )

        columns = [
            classes.index(
                label
            )
            for label
            in CLASS_ORDER
        ]

        probabilities = probabilities_raw[
            0,
            columns,
        ]

        if not bool(
            np.isfinite(
                probabilities
            ).all()
        ):
            raise ArtifactAuthorityError(
                "INFERENCE_PROBABILITY_NON_FINITE"
            )

        if not bool(
            np.allclose(
                probabilities.sum(),
                1.0,
                rtol=1e-9,
                atol=1e-9,
            )
        ):
            raise ArtifactAuthorityError(
                "INFERENCE_PROBABILITY_SUM_MISMATCH"
            )

        winner_index = int(
            np.argmax(
                probabilities
            )
        )

        predicted_class = int(
            CLASS_ORDER[
                winner_index
            ]
        )

        return R03InferenceResult(
            probability_short=float(
                probabilities[
                    0
                ]
            ),
            probability_no_trade=float(
                probabilities[
                    1
                ]
            ),
            probability_long=float(
                probabilities[
                    2
                ]
            ),
            predicted_class=(
                predicted_class
            ),
            predicted_label=(
                LABEL_MAP[
                    predicted_class
                ]
            ),
            winning_probability=float(
                probabilities[
                    winner_index
                ]
            ),
        )


# =============================================================================
# Observation record
# =============================================================================

@dataclasses.dataclass(
    frozen=True
)
class R03ProspectiveObservationRecord:

    logical_observation_id: str

    semantic_record_fingerprint: str

    observed_at_utc: str

    decision_time_utc: str

    canonical_instrument: str

    broker_symbol: str

    feature_count: int

    feature_columns_sha256: str

    model_artifact_sha256: str

    candidate_id: str

    candidate_fingerprint_sha256: str

    probability_short: float

    probability_no_trade: float

    probability_long: float

    predicted_class: int

    predicted_label: str

    winning_probability: float

    source_snapshot_id: str

    source_provenance: str

    acquisition_authority: str

    prospective_contract_fingerprint_sha256: str

    live_authorized: bool = False

    execution_authorized: bool = False

    def semantic_document(
        self,
    ) -> dict[str, Any]:

        return {
            "schema_version": (
                OBSERVATION_SCHEMA_VERSION
            ),
            "logical_observation_id": (
                self.logical_observation_id
            ),
            "observed_at_utc": (
                self.observed_at_utc
            ),
            "decision_time_utc": (
                self.decision_time_utc
            ),
            "canonical_instrument": (
                self.canonical_instrument
            ),
            "broker_symbol": (
                self.broker_symbol
            ),
            "feature_count": (
                self.feature_count
            ),
            "feature_columns_sha256": (
                self.feature_columns_sha256
            ),
            "model_artifact_sha256": (
                self.model_artifact_sha256
            ),
            "candidate_id": (
                self.candidate_id
            ),
            "candidate_fingerprint_sha256": (
                self.candidate_fingerprint_sha256
            ),
            "probability_short": (
                self.probability_short
            ),
            "probability_no_trade": (
                self.probability_no_trade
            ),
            "probability_long": (
                self.probability_long
            ),
            "predicted_class": (
                self.predicted_class
            ),
            "predicted_label": (
                self.predicted_label
            ),
            "winning_probability": (
                self.winning_probability
            ),
            "source_snapshot_id": (
                self.source_snapshot_id
            ),
            "source_provenance": (
                self.source_provenance
            ),
            "acquisition_authority": (
                self.acquisition_authority
            ),
            "prospective_contract_fingerprint_sha256": (
                self.prospective_contract_fingerprint_sha256
            ),
            "live_authorized": False,
            "execution_authorized": False,
        }

    def to_dict(
        self,
    ) -> dict[str, Any]:

        document = (
            self.semantic_document()
        )

        document[
            "semantic_record_fingerprint"
        ] = (
            self.semantic_record_fingerprint
        )

        return document


def compute_observation_logical_id(
    *,
    decision_time_utc: str,
) -> str:

    payload = (
        f"{OBSERVATION_SCHEMA_VERSION}:"
        f"{CANONICAL_INSTRUMENT}:"
        f"{decision_time_utc}:"
        f"{FEATURE_COLUMNS_SHA256}:"
        f"{ARTIFACT_SHA256}"
    )

    return hashlib.sha256(
        payload.encode(
            "utf-8"
        )
    ).hexdigest()


def observation_fingerprint(
    document: Mapping[str, Any],
) -> str:

    semantic = dict(
        document
    )

    semantic.pop(
        "semantic_record_fingerprint",
        None,
    )

    return canonical_json_sha256(
        semantic
    )


def validate_observation_document(
    document: Mapping[str, Any],
) -> R03ProspectiveObservationRecord:

    if (
        document.get(
            "schema_version"
        )
        !=
        OBSERVATION_SCHEMA_VERSION
    ):
        raise R03ProspectiveRuntimeError(
            "OBSERVATION_SCHEMA_MISMATCH"
        )

    logical_id = validate_sha256(
        document.get(
            "logical_observation_id"
        ),
        "LOGICAL_OBSERVATION_ID",
    )

    semantic_fingerprint = validate_sha256(
        document.get(
            "semantic_record_fingerprint"
        ),
        "SEMANTIC_RECORD_FINGERPRINT",
    )

    decision_time = utc_iso(
        document.get(
            "decision_time_utc"
        )
    )

    enforce_prospective_freshness(
        decision_time
    )

    if (
        document.get(
            "canonical_instrument"
        )
        !=
        CANONICAL_INSTRUMENT
    ):
        raise R03ProspectiveRuntimeError(
            "OBSERVATION_INSTRUMENT_MISMATCH"
        )

    if (
        int(
            document.get(
                "feature_count",
                -1,
            )
        )
        !=
        FEATURE_COUNT
    ):
        raise R03ProspectiveRuntimeError(
            "OBSERVATION_FEATURE_COUNT_MISMATCH"
        )

    if (
        document.get(
            "feature_columns_sha256"
        )
        !=
        FEATURE_COLUMNS_SHA256
    ):
        raise R03ProspectiveRuntimeError(
            "OBSERVATION_FEATURE_HASH_MISMATCH"
        )

    if (
        document.get(
            "model_artifact_sha256"
        )
        !=
        ARTIFACT_SHA256
    ):
        raise R03ProspectiveRuntimeError(
            "OBSERVATION_ARTIFACT_HASH_MISMATCH"
        )

    if (
        document.get(
            "candidate_id"
        )
        !=
        WINNER_CANDIDATE_ID
    ):
        raise R03ProspectiveRuntimeError(
            "OBSERVATION_CANDIDATE_ID_MISMATCH"
        )

    if (
        document.get(
            "candidate_fingerprint_sha256"
        )
        !=
        WINNER_CANDIDATE_FINGERPRINT_SHA256
    ):
        raise R03ProspectiveRuntimeError(
            "OBSERVATION_CANDIDATE_FINGERPRINT_MISMATCH"
        )

    if (
        document.get(
            "source_provenance"
        )
        !=
        SOURCE_PROVENANCE
    ):
        raise R03ProspectiveRuntimeError(
            "OBSERVATION_SOURCE_PROVENANCE_MISMATCH"
        )

    if (
        document.get(
            "prospective_contract_fingerprint_sha256"
        )
        !=
        PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256
    ):
        raise R03ProspectiveRuntimeError(
            "OBSERVATION_CONTRACT_FINGERPRINT_MISMATCH"
        )

    if (
        document.get(
            "live_authorized"
        )
        is not False
    ):
        raise R03ProspectiveRuntimeError(
            "OBSERVATION_LIVE_AUTHORIZATION_VIOLATION"
        )

    if (
        document.get(
            "execution_authorized"
        )
        is not False
    ):
        raise R03ProspectiveRuntimeError(
            "OBSERVATION_EXECUTION_AUTHORIZATION_VIOLATION"
        )

    probabilities = [
        require_finite_float(
            document.get(
                "probability_short"
            ),
            "PROBABILITY_SHORT",
        ),
        require_finite_float(
            document.get(
                "probability_no_trade"
            ),
            "PROBABILITY_NO_TRADE",
        ),
        require_finite_float(
            document.get(
                "probability_long"
            ),
            "PROBABILITY_LONG",
        ),
    ]

    if not all(
        math.isfinite(
            value
        )
        for value
        in probabilities
    ):
        raise R03ProspectiveRuntimeError(
            "OBSERVATION_PROBABILITY_NON_FINITE"
        )

    if not math.isclose(
        sum(
            probabilities
        ),
        1.0,
        rel_tol=1e-9,
        abs_tol=1e-9,
    ):
        raise R03ProspectiveRuntimeError(
            "OBSERVATION_PROBABILITY_SUM_MISMATCH"
        )

    predicted_class = require_int(
        document.get(
            "predicted_class"
        ),
        "PREDICTED_CLASS",
    )

    if (
        predicted_class
        not in
        CLASS_ORDER
    ):
        raise R03ProspectiveRuntimeError(
            "OBSERVATION_PREDICTED_CLASS_INVALID"
        )

    expected_logical_id = (
        compute_observation_logical_id(
            decision_time_utc=(
                decision_time
            )
        )
    )

    if (
        logical_id
        !=
        expected_logical_id
    ):
        raise R03ProspectiveRuntimeError(
            "OBSERVATION_LOGICAL_ID_MISMATCH"
        )

    expected_fingerprint = (
        observation_fingerprint(
            document
        )
    )

    if (
        semantic_fingerprint
        !=
        expected_fingerprint
    ):
        raise R03ProspectiveRuntimeError(
            "OBSERVATION_SEMANTIC_FINGERPRINT_MISMATCH"
        )

    return R03ProspectiveObservationRecord(
        logical_observation_id=(
            logical_id
        ),
        semantic_record_fingerprint=(
            semantic_fingerprint
        ),
        observed_at_utc=utc_iso(
            document.get(
                "observed_at_utc"
            )
        ),
        decision_time_utc=(
            decision_time
        ),
        canonical_instrument=(
            CANONICAL_INSTRUMENT
        ),
        broker_symbol=str(
            document.get(
                "broker_symbol"
            )
        ),
        feature_count=(
            FEATURE_COUNT
        ),
        feature_columns_sha256=(
            FEATURE_COLUMNS_SHA256
        ),
        model_artifact_sha256=(
            ARTIFACT_SHA256
        ),
        candidate_id=(
            WINNER_CANDIDATE_ID
        ),
        candidate_fingerprint_sha256=(
            WINNER_CANDIDATE_FINGERPRINT_SHA256
        ),
        probability_short=(
            probabilities[
                0
            ]
        ),
        probability_no_trade=(
            probabilities[
                1
            ]
        ),
        probability_long=(
            probabilities[
                2
            ]
        ),
        predicted_class=(
            predicted_class
        ),
        predicted_label=str(
            document.get(
                "predicted_label"
            )
        ),
        winning_probability=require_finite_float(
            document.get(
                "winning_probability"
            ),
            "WINNING_PROBABILITY",
        ),
        source_snapshot_id=validate_sha256(
            document.get(
                "source_snapshot_id"
            ),
            "SOURCE_SNAPSHOT_ID",
        ),
        source_provenance=(
            SOURCE_PROVENANCE
        ),
        acquisition_authority=str(
            document.get(
                "acquisition_authority"
            )
        ),
        prospective_contract_fingerprint_sha256=(
            PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256
        ),
        live_authorized=False,
        execution_authorized=False,
    )


# =============================================================================
# Anchor
# =============================================================================

@dataclasses.dataclass(
    frozen=True
)
class R03ProspectiveAnchorRecord:

    logical_observation_id: str

    semantic_observation_fingerprint: str

    anchor_semantic_fingerprint: str

    source_snapshot_id: str

    canonical_instrument: str

    decision_time_utc: str

    decision_bar_open_time_utc: str

    decision_m5_close: float

    decision_m5_atr14: float

    feature_columns_sha256: str

    model_artifact_sha256: str

    acquisition_authority: str

    source_provenance: str

    forward_outcome_contract_fingerprint_sha256: str

    prospective_contract_fingerprint_sha256: str

    performance_evaluation_authorized: bool = False

    live_authorized: bool = False

    execution_authorized: bool = False

    def semantic_document(
        self,
    ) -> dict[str, Any]:

        return {
            "schema_version": (
                ANCHOR_SCHEMA_VERSION
            ),
            "logical_observation_id": (
                self.logical_observation_id
            ),
            "semantic_observation_fingerprint": (
                self.semantic_observation_fingerprint
            ),
            "source_snapshot_id": (
                self.source_snapshot_id
            ),
            "canonical_instrument": (
                self.canonical_instrument
            ),
            "decision_time_utc": (
                self.decision_time_utc
            ),
            "decision_bar_open_time_utc": (
                self.decision_bar_open_time_utc
            ),
            "decision_m5_close": (
                self.decision_m5_close
            ),
            "decision_m5_atr14": (
                self.decision_m5_atr14
            ),
            "feature_columns_sha256": (
                self.feature_columns_sha256
            ),
            "model_artifact_sha256": (
                self.model_artifact_sha256
            ),
            "acquisition_authority": (
                self.acquisition_authority
            ),
            "source_provenance": (
                self.source_provenance
            ),
            "forward_outcome_contract_fingerprint_sha256": (
                self.forward_outcome_contract_fingerprint_sha256
            ),
            "prospective_contract_fingerprint_sha256": (
                self.prospective_contract_fingerprint_sha256
            ),
            "performance_evaluation_authorized": False,
            "live_authorized": False,
            "execution_authorized": False,
        }

    def to_dict(
        self,
    ) -> dict[str, Any]:

        document = (
            self.semantic_document()
        )

        document[
            "anchor_semantic_fingerprint"
        ] = (
            self.anchor_semantic_fingerprint
        )

        return document


def anchor_fingerprint(
    document: Mapping[str, Any],
) -> str:

    semantic = dict(
        document
    )

    semantic.pop(
        "anchor_semantic_fingerprint",
        None,
    )

    return canonical_json_sha256(
        semantic
    )


def validate_anchor_document(
    document: Mapping[str, Any],
) -> R03ProspectiveAnchorRecord:

    if (
        document.get(
            "schema_version"
        )
        !=
        ANCHOR_SCHEMA_VERSION
    ):
        raise R03ProspectiveRuntimeError(
            "ANCHOR_SCHEMA_MISMATCH"
        )

    logical_id = validate_sha256(
        document.get(
            "logical_observation_id"
        ),
        "LOGICAL_OBSERVATION_ID",
    )

    observation_fingerprint_value = (
        validate_sha256(
            document.get(
                "semantic_observation_fingerprint"
            ),
            "SEMANTIC_OBSERVATION_FINGERPRINT",
        )
    )

    supplied_anchor_fingerprint = (
        validate_sha256(
            document.get(
                "anchor_semantic_fingerprint"
            ),
            "ANCHOR_SEMANTIC_FINGERPRINT",
        )
    )

    if (
        document.get(
            "canonical_instrument"
        )
        !=
        CANONICAL_INSTRUMENT
    ):
        raise R03ProspectiveRuntimeError(
            "ANCHOR_INSTRUMENT_MISMATCH"
        )

    if (
        document.get(
            "feature_columns_sha256"
        )
        !=
        FEATURE_COLUMNS_SHA256
    ):
        raise R03ProspectiveRuntimeError(
            "ANCHOR_FEATURE_HASH_MISMATCH"
        )

    if (
        document.get(
            "model_artifact_sha256"
        )
        !=
        ARTIFACT_SHA256
    ):
        raise R03ProspectiveRuntimeError(
            "ANCHOR_ARTIFACT_HASH_MISMATCH"
        )

    if (
        document.get(
            "source_provenance"
        )
        !=
        SOURCE_PROVENANCE
    ):
        raise R03ProspectiveRuntimeError(
            "ANCHOR_SOURCE_PROVENANCE_MISMATCH"
        )

    if (
        document.get(
            "forward_outcome_contract_fingerprint_sha256"
        )
        !=
        FORWARD_OUTCOME_CONTRACT_FINGERPRINT_SHA256
    ):
        raise R03ProspectiveRuntimeError(
            "ANCHOR_OUTCOME_CONTRACT_MISMATCH"
        )

    if (
        document.get(
            "prospective_contract_fingerprint_sha256"
        )
        !=
        PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256
    ):
        raise R03ProspectiveRuntimeError(
            "ANCHOR_PROSPECTIVE_CONTRACT_MISMATCH"
        )

    if (
        document.get(
            "performance_evaluation_authorized"
        )
        is not False
    ):
        raise R03ProspectiveRuntimeError(
            "ANCHOR_PERFORMANCE_AUTHORIZATION_VIOLATION"
        )

    if (
        document.get(
            "live_authorized"
        )
        is not False
    ):
        raise R03ProspectiveRuntimeError(
            "ANCHOR_LIVE_AUTHORIZATION_VIOLATION"
        )

    if (
        document.get(
            "execution_authorized"
        )
        is not False
    ):
        raise R03ProspectiveRuntimeError(
            "ANCHOR_EXECUTION_AUTHORIZATION_VIOLATION"
        )

    decision_time = utc_iso(
        document.get(
            "decision_time_utc"
        )
    )

    decision_open = utc_iso(
        document.get(
            "decision_bar_open_time_utc"
        )
    )

    expected_decision = (
        utc_timestamp(
            decision_open
        )
        +
        pd.Timedelta(
            minutes=5
        )
    )

    if (
        utc_iso(
            expected_decision
        )
        !=
        decision_time
    ):
        raise R03ProspectiveRuntimeError(
            "ANCHOR_DECISION_TIME_MAPPING_MISMATCH"
        )

    decision_close = require_finite_float(
        document.get(
            "decision_m5_close"
        ),
        "DECISION_M5_CLOSE",
    )

    decision_atr = require_finite_float(
        document.get(
            "decision_m5_atr14"
        ),
        "DECISION_M5_ATR14",
    )

    if (
        not math.isfinite(
            decision_close
        )
        or
        decision_close
        <=
        0.0
    ):
        raise R03ProspectiveRuntimeError(
            "ANCHOR_DECISION_CLOSE_INVALID"
        )

    if (
        not math.isfinite(
            decision_atr
        )
        or
        decision_atr
        <=
        0.0
    ):
        raise R03ProspectiveRuntimeError(
            "ANCHOR_DECISION_ATR_INVALID"
        )

    expected_anchor_fingerprint = (
        anchor_fingerprint(
            document
        )
    )

    if (
        supplied_anchor_fingerprint
        !=
        expected_anchor_fingerprint
    ):
        raise R03ProspectiveRuntimeError(
            "ANCHOR_SEMANTIC_FINGERPRINT_MISMATCH"
        )

    return R03ProspectiveAnchorRecord(
        logical_observation_id=(
            logical_id
        ),
        semantic_observation_fingerprint=(
            observation_fingerprint_value
        ),
        anchor_semantic_fingerprint=(
            supplied_anchor_fingerprint
        ),
        source_snapshot_id=validate_sha256(
            document.get(
                "source_snapshot_id"
            ),
            "SOURCE_SNAPSHOT_ID",
        ),
        canonical_instrument=(
            CANONICAL_INSTRUMENT
        ),
        decision_time_utc=(
            decision_time
        ),
        decision_bar_open_time_utc=(
            decision_open
        ),
        decision_m5_close=(
            decision_close
        ),
        decision_m5_atr14=(
            decision_atr
        ),
        feature_columns_sha256=(
            FEATURE_COLUMNS_SHA256
        ),
        model_artifact_sha256=(
            ARTIFACT_SHA256
        ),
        acquisition_authority=str(
            document.get(
                "acquisition_authority"
            )
        ),
        source_provenance=(
            SOURCE_PROVENANCE
        ),
        forward_outcome_contract_fingerprint_sha256=(
            FORWARD_OUTCOME_CONTRACT_FINGERPRINT_SHA256
        ),
        prospective_contract_fingerprint_sha256=(
            PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256
        ),
        performance_evaluation_authorized=False,
        live_authorized=False,
        execution_authorized=False,
    )


# =============================================================================
# Atomic append-only ledgers
# =============================================================================

@contextlib.contextmanager
def file_lock(
    handle: Any,
) -> Generator[
    None,
    None,
    None,
]:

    if sys.platform == "win32":

        import msvcrt

        handle.seek(
            0,
            os.SEEK_SET,
        )

        msvcrt.locking(
            handle.fileno(),
            msvcrt.LK_LOCK,
            1,
        )

        try:

            yield

        finally:

            handle.seek(
                0,
                os.SEEK_SET,
            )

            msvcrt.locking(
                handle.fileno(),
                msvcrt.LK_UNLCK,
                1,
            )

    else:

        import fcntl

        fcntl.flock(
            handle.fileno(),
            fcntl.LOCK_EX,
        )

        try:

            yield

        finally:

            fcntl.flock(
                handle.fileno(),
                fcntl.LOCK_UN,
            )


@dataclasses.dataclass(
    frozen=True
)
class LedgerAppendResult:

    appended: bool

    is_duplicate: bool

    logical_observation_id: str


class _AtomicJsonlLedger:

    def __init__(
        self,
        *,
        path: Path,
        validator: Any,
        fingerprint_field: str,
    ) -> None:

        self._path = path.resolve()

        self._validator = (
            validator
        )

        self._fingerprint_field = (
            fingerprint_field
        )

        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    @property
    def path(
        self,
    ) -> Path:

        return self._path

    def _read_index_from_handle(
        self,
        handle: Any,
    ) -> dict[str, str]:

        index: dict[
            str,
            str,
        ] = {}

        handle.seek(
            0,
            os.SEEK_SET,
        )

        for (
            line_number,
            raw_line,
        ) in enumerate(
            handle,
            start=1,
        ):

            line = raw_line.strip()

            if not line:
                continue

            try:

                value = json.loads(
                    line
                )

            except Exception as exc:

                raise RuntimeLedgerError(
                    (
                        "LEDGER_JSON_CORRUPTION:"
                        f"{line_number}"
                    )
                ) from exc

            if not isinstance(
                value,
                dict,
            ):
                raise RuntimeLedgerError(
                    (
                        "LEDGER_RECORD_NOT_OBJECT:"
                        f"{line_number}"
                    )
                )

            record = self._validator(
                value
            )

            logical_id = str(
                record.logical_observation_id
            )

            fingerprint = str(
                value[
                    self._fingerprint_field
                ]
            )

            if (
                logical_id
                in
                index
                and
                index[
                    logical_id
                ]
                !=
                fingerprint
            ):
                raise RuntimeLedgerConflictError(
                    (
                        "LEDGER_EXISTING_CONFLICT:"
                        f"{logical_id}"
                    )
                )

            index[
                logical_id
            ] = fingerprint

        return index

    def append(
        self,
        document: Mapping[str, Any],
    ) -> LedgerAppendResult:

        validated = self._validator(
            document
        )

        logical_id = str(
            validated.logical_observation_id
        )

        fingerprint = str(
            document[
                self._fingerprint_field
            ]
        )

        with self._path.open(
            "a+",
            encoding="utf-8",
        ) as handle:

            with file_lock(
                handle
            ):

                index = (
                    self._read_index_from_handle(
                        handle
                    )
                )

                if logical_id in index:

                    if (
                        index[
                            logical_id
                        ]
                        !=
                        fingerprint
                    ):
                        raise RuntimeLedgerConflictError(
                            (
                                "LEDGER_APPEND_CONFLICT:"
                                f"{logical_id}"
                            )
                        )

                    return LedgerAppendResult(
                        appended=False,
                        is_duplicate=True,
                        logical_observation_id=(
                            logical_id
                        ),
                    )

                line = (
                    json.dumps(
                        dict(
                            document
                        ),
                        sort_keys=True,
                        separators=(
                            ",",
                            ":",
                        ),
                        ensure_ascii=False,
                        allow_nan=False,
                    )
                    +
                    "\n"
                )

                handle.seek(
                    0,
                    os.SEEK_END,
                )

                handle.write(
                    line
                )

                handle.flush()

                os.fsync(
                    handle.fileno()
                )

        return LedgerAppendResult(
            appended=True,
            is_duplicate=False,
            logical_observation_id=(
                logical_id
            ),
        )

    def validate_integrity(
        self,
    ) -> bool:

        if not self._path.exists():

            return True

        with self._path.open(
            "r",
            encoding="utf-8",
        ) as handle:

            self._read_index_from_handle(
                handle
            )

        return True

    def count(
        self,
    ) -> int:

        if not self._path.exists():

            return 0

        with self._path.open(
            "r",
            encoding="utf-8",
        ) as handle:

            return len(
                self._read_index_from_handle(
                    handle
                )
            )


class R03ProspectiveObservationLedger(
    _AtomicJsonlLedger
):

    def __init__(
        self,
        path: Path,
    ) -> None:

        super().__init__(
            path=path,
            validator=(
                validate_observation_document
            ),
            fingerprint_field=(
                "semantic_record_fingerprint"
            ),
        )


class R03ProspectiveAnchorLedger(
    _AtomicJsonlLedger
):

    def __init__(
        self,
        path: Path,
    ) -> None:

        super().__init__(
            path=path,
            validator=(
                validate_anchor_document
            ),
            fingerprint_field=(
                "anchor_semantic_fingerprint"
            ),
        )


# =============================================================================
# Prospective runtime binding
# =============================================================================

class R03ProspectiveRuntimeBinder:

    def __init__(
        self,
        *,
        inference_adapter: (
            R03FrozenArtifactInferenceAdapter
            |
            None
        ) = None,
    ) -> None:

        self._inference = (
            inference_adapter
            or
            R03FrozenArtifactInferenceAdapter()
        )

    @property
    def inference_adapter(
        self,
    ) -> R03FrozenArtifactInferenceAdapter:

        return self._inference

    def verify_genuine_snapshot_authority(
        self,
        snapshot: Any,
    ) -> Any:

        authority = getattr(
            snapshot,
            "authority",
            None,
        )

        if authority is None:

            raise R03ProspectiveRuntimeError(
                "GENUINE_FORWARD_AUTHORITY_MISSING"
            )

        # The existing acquisition adapter predates R03 and its attestation
        # is cryptographically bound to the historical acquisition-model
        # authority. We verify that exact acquisition authority here ONLY
        # as proof of genuine read-only MT5 provenance.
        #
        # R03 inference authority is separately and independently fixed by
        # ARTIFACT_SHA256 above.
        verified = (
            _acquisition
            .verify_forward_acquisition_authority(
                authority,
                expected_decision_time_utc=(
                    snapshot.decision_time_utc
                ),
                expected_source_snapshot_id=(
                    snapshot.source_snapshot_id
                ),
                expected_canonical_instrument=(
                    snapshot.canonical_instrument
                ),
                expected_feature_columns_sha256=(
                    FEATURE_COLUMNS_SHA256
                ),
                expected_model_sha256=(
                    _acquisition.FROZEN_MODEL_SHA256
                ),
            )
        )

        return verified

    def create_observation(
        self,
        *,
        snapshot: Any,
        feature_result: Any,
        observed_at_utc: str | None = None,
    ) -> R03ProspectiveObservationRecord:

        verified_attestation = (
            self.verify_genuine_snapshot_authority(
                snapshot
            )
        )

        decision_time = utc_iso(
            snapshot.decision_time_utc
        )

        enforce_prospective_freshness(
            decision_time
        )

        canonical_snapshot_id = (
            _acquisition
            .compute_canonical_snapshot_id(
                snapshot.market_data
            )
        )

        if (
            canonical_snapshot_id
            !=
            snapshot.source_snapshot_id
        ):
            raise R03ProspectiveRuntimeError(
                "SNAPSHOT_IDENTITY_MISMATCH"
            )

        if (
            snapshot.canonical_instrument
            !=
            CANONICAL_INSTRUMENT
        ):
            raise R03ProspectiveRuntimeError(
                "SNAPSHOT_INSTRUMENT_MISMATCH"
            )

        if (
            feature_result.feature_count
            !=
            FEATURE_COUNT
        ):
            raise R03ProspectiveRuntimeError(
                "FEATURE_RESULT_COUNT_MISMATCH"
            )

        if (
            feature_result.feature_columns_sha256
            !=
            FEATURE_COLUMNS_SHA256
        ):
            raise R03ProspectiveRuntimeError(
                "FEATURE_RESULT_HASH_MISMATCH"
            )

        if (
            feature_result.row_count
            <=
            0
        ):
            raise R03ProspectiveRuntimeError(
                "FEATURE_RESULT_EMPTY"
            )

        latest_feature_time = utc_iso(
            feature_result
            .decision_times
            .iloc[
                -1
            ]
        )

        if (
            latest_feature_time
            !=
            decision_time
        ):
            raise R03ProspectiveRuntimeError(
                "FEATURE_DECISION_TIME_MISMATCH"
            )

        inference = (
            self._inference.infer_single(
                feature_result
                .features
                .iloc[
                    -1
                ]
            )
        )

        logical_id = (
            compute_observation_logical_id(
                decision_time_utc=(
                    decision_time
                )
            )
        )

        if observed_at_utc is None:

            observed_at = utc_iso(
                datetime.datetime.now(
                    datetime.timezone.utc
                )
            )

        else:

            observed_at = utc_iso(
                observed_at_utc
            )

        base_document: dict[str, Any] = {
            "schema_version": (
                OBSERVATION_SCHEMA_VERSION
            ),
            "logical_observation_id": (
                logical_id
            ),
            "observed_at_utc": (
                observed_at
            ),
            "decision_time_utc": (
                decision_time
            ),
            "canonical_instrument": (
                CANONICAL_INSTRUMENT
            ),
            "broker_symbol": str(
                snapshot.broker_symbol
            ),
            "feature_count": (
                FEATURE_COUNT
            ),
            "feature_columns_sha256": (
                FEATURE_COLUMNS_SHA256
            ),
            "model_artifact_sha256": (
                ARTIFACT_SHA256
            ),
            "candidate_id": (
                WINNER_CANDIDATE_ID
            ),
            "candidate_fingerprint_sha256": (
                WINNER_CANDIDATE_FINGERPRINT_SHA256
            ),
            "probability_short": (
                inference.probability_short
            ),
            "probability_no_trade": (
                inference.probability_no_trade
            ),
            "probability_long": (
                inference.probability_long
            ),
            "predicted_class": (
                inference.predicted_class
            ),
            "predicted_label": (
                inference.predicted_label
            ),
            "winning_probability": (
                inference.winning_probability
            ),
            "source_snapshot_id": (
                snapshot.source_snapshot_id
            ),
            "source_provenance": (
                SOURCE_PROVENANCE
            ),
            "acquisition_authority": (
                verified_attestation
                .acquisition_authority
            ),
            "prospective_contract_fingerprint_sha256": (
                PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256
            ),
            "live_authorized": False,
            "execution_authorized": False,
        }

        base_document[
            "semantic_record_fingerprint"
        ] = observation_fingerprint(
            base_document
        )

        return validate_observation_document(
            base_document
        )

    def create_anchor(
        self,
        *,
        observation: R03ProspectiveObservationRecord,
        market_data: Mapping[
            str,
            pd.DataFrame,
        ],
    ) -> R03ProspectiveAnchorRecord:

        canonical_snapshot_id = (
            _acquisition
            .compute_canonical_snapshot_id(
                market_data
            )
        )

        if (
            canonical_snapshot_id
            !=
            observation.source_snapshot_id
        ):
            raise R03ProspectiveRuntimeError(
                "ANCHOR_SNAPSHOT_ID_MISMATCH"
            )

        if (
            "M5"
            not in
            market_data
        ):
            raise R03ProspectiveRuntimeError(
                "ANCHOR_M5_MISSING"
            )

        m5 = (
            market_data[
                "M5"
            ]
            .copy()
        )

        if m5.empty:

            raise R03ProspectiveRuntimeError(
                "ANCHOR_M5_EMPTY"
            )

        m5[
            "time"
        ] = pd.to_datetime(
            m5[
                "time"
            ],
            utc=True,
            errors="raise",
        )

        m5 = (
            m5
            .sort_values(
                by="time"
            )
            .reset_index(
                drop=True
            )
        )

        if bool(
            m5[
                "time"
            ]
            .duplicated()
            .any()
        ):
            raise R03ProspectiveRuntimeError(
                "ANCHOR_M5_DUPLICATE_TIME"
            )

        decision_open = utc_iso(
            m5[
                "time"
            ]
            .iloc[
                -1
            ]
        )

        expected_decision_time = utc_iso(
            utc_timestamp(
                decision_open
            )
            +
            pd.Timedelta(
                minutes=5
            )
        )

        if (
            expected_decision_time
            !=
            observation.decision_time_utc
        ):
            raise R03ProspectiveRuntimeError(
                "ANCHOR_DECISION_BAR_MAPPING_MISMATCH"
            )

        featured = FeatureGenerator().generate(
            m5.copy()
        )

        if (
            "atr14"
            not in
            featured.columns
        ):
            raise R03ProspectiveRuntimeError(
                "ANCHOR_ATR14_MISSING"
            )

        if featured.empty:

            raise R03ProspectiveRuntimeError(
                "ANCHOR_FEATURED_M5_EMPTY"
            )

        decision_close = float(
            m5[
                "close"
            ]
            .iloc[
                -1
            ]
        )

        decision_atr = float(
            featured[
                "atr14"
            ]
            .iloc[
                -1
            ]
        )

        if (
            not math.isfinite(
                decision_close
            )
            or
            decision_close
            <=
            0.0
        ):
            raise R03ProspectiveRuntimeError(
                "ANCHOR_CLOSE_INVALID"
            )

        if (
            not math.isfinite(
                decision_atr
            )
            or
            decision_atr
            <=
            0.0
        ):
            raise R03ProspectiveRuntimeError(
                "ANCHOR_ATR_INVALID"
            )

        base_document: dict[str, Any] = {
            "schema_version": (
                ANCHOR_SCHEMA_VERSION
            ),
            "logical_observation_id": (
                observation.logical_observation_id
            ),
            "semantic_observation_fingerprint": (
                observation.semantic_record_fingerprint
            ),
            "source_snapshot_id": (
                observation.source_snapshot_id
            ),
            "canonical_instrument": (
                CANONICAL_INSTRUMENT
            ),
            "decision_time_utc": (
                observation.decision_time_utc
            ),
            "decision_bar_open_time_utc": (
                decision_open
            ),
            "decision_m5_close": (
                decision_close
            ),
            "decision_m5_atr14": (
                decision_atr
            ),
            "feature_columns_sha256": (
                FEATURE_COLUMNS_SHA256
            ),
            "model_artifact_sha256": (
                ARTIFACT_SHA256
            ),
            "acquisition_authority": (
                observation.acquisition_authority
            ),
            "source_provenance": (
                SOURCE_PROVENANCE
            ),
            "forward_outcome_contract_fingerprint_sha256": (
                FORWARD_OUTCOME_CONTRACT_FINGERPRINT_SHA256
            ),
            "prospective_contract_fingerprint_sha256": (
                PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256
            ),
            "performance_evaluation_authorized": False,
            "live_authorized": False,
            "execution_authorized": False,
        }

        base_document[
            "anchor_semantic_fingerprint"
        ] = anchor_fingerprint(
            base_document
        )

        return validate_anchor_document(
            base_document
        )

    def persist_anchor_first(
        self,
        *,
        observation: R03ProspectiveObservationRecord,
        anchor: R03ProspectiveAnchorRecord,
        observation_ledger: R03ProspectiveObservationLedger,
        anchor_ledger: R03ProspectiveAnchorLedger,
    ) -> dict[str, Any]:

        if (
            anchor.logical_observation_id
            !=
            observation.logical_observation_id
        ):
            raise R03ProspectiveRuntimeError(
                "ANCHOR_OBSERVATION_ID_MISMATCH"
            )

        if (
            anchor.semantic_observation_fingerprint
            !=
            observation.semantic_record_fingerprint
        ):
            raise R03ProspectiveRuntimeError(
                "ANCHOR_OBSERVATION_FINGERPRINT_MISMATCH"
            )

        if (
            anchor.source_snapshot_id
            !=
            observation.source_snapshot_id
        ):
            raise R03ProspectiveRuntimeError(
                "ANCHOR_OBSERVATION_SNAPSHOT_MISMATCH"
            )

        anchor_result = (
            anchor_ledger.append(
                anchor.to_dict()
            )
        )

        if (
            anchor_ledger
            .validate_integrity()
            is not True
        ):
            raise RuntimeLedgerError(
                "ANCHOR_LEDGER_INTEGRITY_FAILED"
            )

        try:

            observation_result = (
                observation_ledger.append(
                    observation.to_dict()
                )
            )

        except Exception as exc:

            raise RuntimeLedgerError(
                (
                    "OBSERVATION_APPEND_FAILED_AFTER_ANCHOR_PRESERVED:"
                    f"{exc}"
                )
            ) from exc

        if (
            observation_ledger
            .validate_integrity()
            is not True
        ):
            raise RuntimeLedgerError(
                "OBSERVATION_LEDGER_INTEGRITY_FAILED"
            )

        return {
            "logical_observation_id": (
                observation.logical_observation_id
            ),
            "persistence_order": (
                "ANCHOR_FIRST_THEN_OBSERVATION"
            ),
            "anchor_appended": (
                anchor_result.appended
            ),
            "anchor_idempotent_duplicate": (
                anchor_result.is_duplicate
            ),
            "observation_appended": (
                observation_result.appended
            ),
            "observation_idempotent_duplicate": (
                observation_result.is_duplicate
            ),
            "performance_evaluated": False,
            "pnl_evaluated": False,
            "live_authorized": False,
            "execution_authorized": False,
        }