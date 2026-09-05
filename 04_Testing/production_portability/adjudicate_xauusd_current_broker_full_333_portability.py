from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


ANALYSIS_VERSION = (
    "XAUUSD_CURRENT_BROKER_FULL_333_EVIDENCE_ADJUDICATION_V1"
)

EXPECTED_FULL_AUDIT_VERSION = (
    "XAUUSD_CURRENT_BROKER_FULL_MTF_PORTABILITY_V2"
)

EXPECTED_CORRECTED_D1_VERSION = (
    "XAUUSD_CURRENT_BROKER_D1_CORRECTED_PORTABILITY_V1"
)


FULL_AUDIT_JSON = (
    ROOT_DIR
    /
    "04_Testing/evidence/production_portability/xauusd_current_broker_full_mtf_portability.json"
)

CORRECTED_D1_JSON = (
    ROOT_DIR
    /
    "04_Testing/evidence/production_portability/xauusd_current_broker_d1_corrected_portability.json"
)


EXPECTED_TOTAL_FEATURE_COUNT = 333

EXPECTED_TECHNICAL_FEATURE_COUNT = 258

EXPECTED_TECHNICAL_FEATURE_COUNT_PER_TIMEFRAME = 43

EXPECTED_DOMAIN_FEATURE_COUNT = 63

EXPECTED_BROKER_SENSITIVE_FEATURE_COUNT = 3

EXPECTED_AGE_FEATURE_COUNT = 5

EXPECTED_UTC_FEATURE_COUNT = 4

EXPECTED_NON_BROKER_SENSITIVE_FEATURE_COUNT = 330

EXPECTED_TRAIN_ROWS = 69966

EXPECTED_D1_STATE_COUNT = 309


TECHNICAL_TIMEFRAMES = (
    "M5",
    "M15",
    "M30",
    "H1",
    "H4",
    "D1",
)

UNCHANGED_TECHNICAL_TIMEFRAMES = (
    "M5",
    "M15",
    "M30",
    "H1",
    "H4",
)


UTC_FEATURES = (
    "utc_hour_sin",
    "utc_hour_cos",
    "utc_day_sin",
    "utc_day_cos",
)


BROKER_SENSITIVE_FEATURES = (
    "m5_spread_points",
    "m5_tick_volume_log1p",
    "m5_tick_volume_ratio20",
)


UTC_MINIMUM_FINITE_PAIR_FRACTION = 0.999999

UTC_MINIMUM_PAIRED_CORRELATION = 0.999999

UTC_MAX_ABS_STANDARDIZED_MEAN_SHIFT = 1e-8

UTC_MAX_PAIRED_MEDIAN_ABS_DIFF_REFERENCE_STD = 1e-8

UTC_MAX_MEDIAN_SHIFT_REFERENCE_STD = 1e-8


def _require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise RuntimeError(
            reason
        )


def _safe_float(
    value: Any,
) -> float | None:

    try:
        result = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):
        return None

    if not math.isfinite(
        result
    ):
        return None

    return result


def _decode_json_bytes(
    raw: bytes,
    *,
    source_name: str,
) -> tuple[
    str,
    str,
]:

    _require(
        bool(
            raw
        ),
        (
            "EVIDENCE_JSON_EMPTY:"
            f"{source_name}"
        ),
    )

    if raw.startswith(
        b"\xff\xfe"
    ) or raw.startswith(
        b"\xfe\xff"
    ):

        try:
            return (
                raw.decode(
                    "utf-16"
                ),
                "utf-16",
            )

        except UnicodeDecodeError as exc:
            raise RuntimeError(
                (
                    "EVIDENCE_JSON_UTF16_DECODE_FAILED:"
                    f"{source_name}:"
                    f"{exc}"
                )
            ) from exc

    if raw.startswith(
        b"\xef\xbb\xbf"
    ):

        try:
            return (
                raw.decode(
                    "utf-8-sig"
                ),
                "utf-8-sig",
            )

        except UnicodeDecodeError as exc:
            raise RuntimeError(
                (
                    "EVIDENCE_JSON_UTF8_BOM_DECODE_FAILED:"
                    f"{source_name}:"
                    f"{exc}"
                )
            ) from exc

    try:
        return (
            raw.decode(
                "utf-8"
            ),
            "utf-8",
        )

    except UnicodeDecodeError:
        pass

    try:
        return (
            raw.decode(
                "utf-16"
            ),
            "utf-16-fallback",
        )

    except UnicodeDecodeError:
        pass

    try:
        return (
            raw.decode(
                "utf-16-le"
            ),
            "utf-16-le-fallback",
        )

    except UnicodeDecodeError:
        pass

    try:
        return (
            raw.decode(
                "utf-16-be"
            ),
            "utf-16-be-fallback",
        )

    except UnicodeDecodeError as exc:
        raise RuntimeError(
            (
                "EVIDENCE_JSON_ENCODING_UNSUPPORTED:"
                f"{source_name}"
            )
        ) from exc


def _load_json(
    path: Path,
) -> dict[str, Any]:

    _require(
        path.is_file(),
        (
            "REQUIRED_EVIDENCE_JSON_NOT_FOUND:"
            f"{path.name}"
        ),
    )

    raw = path.read_bytes()

    (
        text,
        detected_encoding,
    ) = (
        _decode_json_bytes(
            raw,
            source_name=(
                path.name
            ),
        )
    )

    try:
        document = json.loads(
            text
        )

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            (
                "EVIDENCE_JSON_PARSE_FAILED:"
                f"{path.name}:"
                f"{detected_encoding}:"
                f"line={exc.lineno}:"
                f"column={exc.colno}:"
                f"{exc.msg}"
            )
        ) from exc

    if not isinstance(
        document,
        dict,
    ):
        raise RuntimeError(
            (
                "EVIDENCE_JSON_ROOT_NOT_OBJECT:"
                f"{path.name}"
            )
        )

    return (
        document
    )


def _mapping(
    document: Mapping[
        str,
        Any,
    ],
    key: str,
) -> Mapping[
    str,
    Any,
]:

    value = (
        document.get(
            key
        )
    )

    if not isinstance(
        value,
        Mapping,
    ):
        raise RuntimeError(
            (
                "EXPECTED_MAPPING_MISSING:"
                f"{key}"
            )
        )

    return (
        value
    )


def _sequence(
    document: Mapping[
        str,
        Any,
    ],
    key: str,
) -> Sequence[
    Any
]:

    value = (
        document.get(
            key
        )
    )

    if not isinstance(
        value,
        list,
    ):
        raise RuntimeError(
            (
                "EXPECTED_LIST_MISSING:"
                f"{key}"
            )
        )

    return (
        value
    )


def _portable_status(
    document: Mapping[
        str,
        Any,
    ],
) -> bool:

    return bool(
        document.get(
            "portable",
            False,
        )
    )


def _fingerprint_sha256(
    document: Mapping[
        str,
        Any,
    ],
) -> str:

    current_broker = (
        _mapping(
            document,
            "current_broker",
        )
    )

    fingerprint = (
        _mapping(
            current_broker,
            "contract_fingerprint",
        )
    )

    value = str(
        fingerprint.get(
            "sha256",
            "",
        )
    ).strip()

    _require(
        bool(
            value
        ),
        "BROKER_CONTRACT_FINGERPRINT_SHA256_MISSING",
    )

    return (
        value
    )


def _fingerprint_version(
    document: Mapping[
        str,
        Any,
    ],
) -> str:

    current_broker = (
        _mapping(
            document,
            "current_broker",
        )
    )

    fingerprint = (
        _mapping(
            current_broker,
            "contract_fingerprint",
        )
    )

    value = str(
        fingerprint.get(
            "version",
            "",
        )
    ).strip()

    _require(
        bool(
            value
        ),
        "BROKER_CONTRACT_FINGERPRINT_VERSION_MISSING",
    )

    return (
        value
    )


def _canonical_symbol(
    document: Mapping[
        str,
        Any,
    ],
) -> str:

    current_broker = (
        _mapping(
            document,
            "current_broker",
        )
    )

    value = str(
        current_broker.get(
            "canonical_symbol",
            "",
        )
    ).strip()

    _require(
        value
        ==
        "XAUUSD",
        (
            "CANONICAL_SYMBOL_MISMATCH:"
            f"{value}"
        ),
    )

    return (
        value
    )


def _broker_symbol(
    document: Mapping[
        str,
        Any,
    ],
) -> str:

    current_broker = (
        _mapping(
            document,
            "current_broker",
        )
    )

    value = str(
        current_broker.get(
            "broker_symbol",
            "",
        )
    ).strip()

    _require(
        bool(
            value
        ),
        "BROKER_SYMBOL_MISSING",
    )

    return (
        value
    )


def _broker_server(
    document: Mapping[
        str,
        Any,
    ],
) -> str:

    current_broker = (
        _mapping(
            document,
            "current_broker",
        )
    )

    value = str(
        current_broker.get(
            "broker_server",
            "",
        )
    ).strip()

    _require(
        bool(
            value
        ),
        "BROKER_SERVER_MISSING",
    )

    return (
        value
    )


def _training_identity(
    document: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    frozen = (
        _mapping(
            document,
            "frozen_reference",
        )
    )

    dataset_id = str(
        frozen.get(
            "training_dataset_id",
            frozen.get(
                "dataset_id",
                "",
            ),
        )
    ).strip()

    dataset_sha256 = str(
        frozen.get(
            "training_dataset_sha256",
            frozen.get(
                "dataset_sha256",
                "",
            ),
        )
    ).strip()

    manifest_sha256 = str(
        frozen.get(
            "training_manifest_sha256",
            "",
        )
    ).strip()

    training_contract = str(
        frozen.get(
            "training_contract",
            "",
        )
    ).strip()

    rows_raw = (
        frozen.get(
            "train_rows",
            frozen.get(
                "rows_loaded",
                0,
            ),
        )
    )

    try:
        rows = int(
            rows_raw
        )

    except (
        TypeError,
        ValueError,
    ):

        rows = 0

    _require(
        bool(
            dataset_id
        ),
        "TRAINING_DATASET_ID_MISSING",
    )

    _require(
        bool(
            dataset_sha256
        ),
        "TRAINING_DATASET_SHA256_MISSING",
    )

    _require(
        bool(
            manifest_sha256
        ),
        "TRAINING_MANIFEST_SHA256_MISSING",
    )

    _require(
        bool(
            training_contract
        ),
        "TRAINING_CONTRACT_MISSING",
    )

    _require(
        rows
        ==
        EXPECTED_TRAIN_ROWS,
        (
            "TRAIN_ROW_COUNT_MISMATCH:"
            f"{rows}:"
            f"{EXPECTED_TRAIN_ROWS}"
        ),
    )

    return {
        "dataset_id": (
            dataset_id
        ),
        "dataset_sha256": (
            dataset_sha256
        ),
        "training_manifest_sha256": (
            manifest_sha256
        ),
        "training_contract": (
            training_contract
        ),
        "train_rows": (
            rows
        ),
    }


def _validate_same_evidence_identity(
    full_document: Mapping[
        str,
        Any,
    ],
    corrected_d1_document: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    full_identity = (
        _training_identity(
            full_document
        )
    )

    corrected_identity = (
        _training_identity(
            corrected_d1_document
        )
    )

    for key in (
        "dataset_id",
        "dataset_sha256",
        "training_manifest_sha256",
        "training_contract",
        "train_rows",
    ):

        _require(
            full_identity[
                key
            ]
            ==
            corrected_identity[
                key
            ],
            (
                "EVIDENCE_TRAINING_IDENTITY_MISMATCH:"
                f"{key}"
            ),
        )

    full_fingerprint_sha = (
        _fingerprint_sha256(
            full_document
        )
    )

    corrected_fingerprint_sha = (
        _fingerprint_sha256(
            corrected_d1_document
        )
    )

    _require(
        full_fingerprint_sha
        ==
        corrected_fingerprint_sha,
        "BROKER_CONTRACT_FINGERPRINT_MISMATCH",
    )

    full_fingerprint_version = (
        _fingerprint_version(
            full_document
        )
    )

    corrected_fingerprint_version = (
        _fingerprint_version(
            corrected_d1_document
        )
    )

    _require(
        full_fingerprint_version
        ==
        corrected_fingerprint_version,
        "BROKER_CONTRACT_FINGERPRINT_VERSION_MISMATCH",
    )

    full_symbol = (
        _canonical_symbol(
            full_document
        )
    )

    corrected_symbol = (
        _canonical_symbol(
            corrected_d1_document
        )
    )

    _require(
        full_symbol
        ==
        corrected_symbol,
        "CANONICAL_SYMBOL_EVIDENCE_MISMATCH",
    )

    full_broker_symbol = (
        _broker_symbol(
            full_document
        )
    )

    corrected_broker_symbol = (
        _broker_symbol(
            corrected_d1_document
        )
    )

    _require(
        full_broker_symbol
        ==
        corrected_broker_symbol,
        "BROKER_SYMBOL_EVIDENCE_MISMATCH",
    )

    full_broker_server = (
        _broker_server(
            full_document
        )
    )

    corrected_broker_server = (
        _broker_server(
            corrected_d1_document
        )
    )

    _require(
        full_broker_server
        ==
        corrected_broker_server,
        "BROKER_SERVER_EVIDENCE_MISMATCH",
    )

    return {
        "training_identity": (
            full_identity
        ),
        "canonical_symbol": (
            full_symbol
        ),
        "broker_symbol": (
            full_broker_symbol
        ),
        "broker_server": (
            full_broker_server
        ),
        "contract_fingerprint": {
            "sha256": (
                full_fingerprint_sha
            ),
            "version": (
                full_fingerprint_version
            ),
        },
    }


def _validate_research_only_policy(
    document: Mapping[
        str,
        Any,
    ],
    *,
    source_name: str,
) -> None:

    policy = (
        _mapping(
            document,
            "scientific_policy",
        )
    )

    must_be_false = (
        "validation_loaded",
        "validation_evaluated",
        "test_loaded",
        "test_evaluated",
        "labels_used",
        "target_columns_loaded",
        "model_loaded",
        "model_trained",
        "model_artifacts_written",
        "orders_sent",
        "positions_modified",
        "risk_engine_modified",
        "sizing_modified",
        "execution_integration_modified",
        "live_authorized",
    )

    for key in (
        must_be_false
    ):

        if (
            key
            in
            policy
        ):

            _require(
                not bool(
                    policy.get(
                        key
                    )
                ),
                (
                    "RESEARCH_ONLY_POLICY_VIOLATION:"
                    f"{source_name}:"
                    f"{key}"
                ),
            )


def _validate_feature_contract(
    full_document: Mapping[
        str,
        Any,
    ],
) -> Mapping[
    str,
    Any
]:

    contract = (
        _mapping(
            full_document,
            "feature_contract",
        )
    )

    expected_counts = {
        "total_feature_count": (
            EXPECTED_TOTAL_FEATURE_COUNT
        ),
        "technical_feature_count": (
            EXPECTED_TECHNICAL_FEATURE_COUNT
        ),
        "technical_feature_count_per_timeframe": (
            EXPECTED_TECHNICAL_FEATURE_COUNT_PER_TIMEFRAME
        ),
        "domain_feature_count": (
            EXPECTED_DOMAIN_FEATURE_COUNT
        ),
        "broker_sensitive_feature_count": (
            EXPECTED_BROKER_SENSITIVE_FEATURE_COUNT
        ),
        "age_feature_count": (
            EXPECTED_AGE_FEATURE_COUNT
        ),
        "utc_feature_count": (
            EXPECTED_UTC_FEATURE_COUNT
        ),
    }

    for key, expected in (
        expected_counts.items()
    ):

        try:
            observed = int(
                contract.get(
                    key,
                    -1,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            observed = -1

        _require(
            observed
            ==
            expected,
            (
                "FEATURE_CONTRACT_COUNT_MISMATCH:"
                f"{key}:"
                f"{observed}:"
                f"{expected}"
            ),
        )

    timeframes = tuple(
        str(
            value
        )
        for value
        in contract.get(
            "timeframes",
            [],
        )
    )

    _require(
        timeframes
        ==
        TECHNICAL_TIMEFRAMES,
        (
            "TECHNICAL_TIMEFRAME_CONTRACT_MISMATCH:"
            f"{timeframes}"
        ),
    )

    broker_features = tuple(
        str(
            value
        )
        for value
        in contract.get(
            "broker_sensitive_features",
            [],
        )
    )

    _require(
        broker_features
        ==
        BROKER_SENSITIVE_FEATURES,
        (
            "BROKER_SENSITIVE_FEATURE_CONTRACT_MISMATCH:"
            f"{broker_features}"
        ),
    )

    utc_features = tuple(
        str(
            value
        )
        for value
        in contract.get(
            "utc_features",
            [],
        )
    )

    _require(
        utc_features
        ==
        UTC_FEATURES,
        (
            "UTC_FEATURE_CONTRACT_MISMATCH:"
            f"{utc_features}"
        ),
    )

    return (
        contract
    )


def _technical_adjudication(
    full_document: Mapping[
        str,
        Any,
    ],
    corrected_d1_document: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    group_statuses = (
        _mapping(
            full_document,
            "group_statuses",
        )
    )

    original_by_timeframe = (
        _mapping(
            group_statuses,
            "technical_by_timeframe",
        )
    )

    corrected_technical = (
        _mapping(
            corrected_d1_document,
            "technical_d1",
        )
    )

    corrected_d1_status = (
        _mapping(
            corrected_technical,
            "status",
        )
    )

    statuses: dict[
        str,
        dict[str, Any]
    ] = {}

    for timeframe in (
        UNCHANGED_TECHNICAL_TIMEFRAMES
    ):

        original_status = (
            _mapping(
                original_by_timeframe,
                timeframe,
            )
        )

        statuses[
            timeframe
        ] = {
            "portable": (
                _portable_status(
                    original_status
                )
            ),
            "evidence_source": (
                "FULL_MTF_PORTABILITY_V2"
            ),
            "status": str(
                original_status.get(
                    "status",
                    "",
                )
            ),
            "reason": str(
                original_status.get(
                    "reason",
                    "",
                )
            ),
        }

    original_d1_status = (
        _mapping(
            original_by_timeframe,
            "D1",
        )
    )

    statuses[
        "D1"
    ] = {
        "portable": (
            _portable_status(
                corrected_d1_status
            )
        ),
        "evidence_source": (
            "CORRECTED_D1_PORTABILITY_V1"
        ),
        "status": str(
            corrected_d1_status.get(
                "status",
                "",
            )
        ),
        "reason": str(
            corrected_d1_status.get(
                "reason",
                "",
            )
        ),
        "supersedes_original_v2_d1": (
            True
        ),
        "original_v2_d1_portable": (
            _portable_status(
                original_d1_status
            )
        ),
        "original_v2_d1_status": str(
            original_d1_status.get(
                "status",
                "",
            )
        ),
    }

    all_portable = all(
        bool(
            statuses[
                timeframe
            ][
                "portable"
            ]
        )
        for timeframe
        in TECHNICAL_TIMEFRAMES
    )

    failed_timeframes = [
        timeframe
        for timeframe
        in TECHNICAL_TIMEFRAMES
        if not bool(
            statuses[
                timeframe
            ][
                "portable"
            ]
        )
    ]

    return {
        "portable": (
            all_portable
        ),
        "failed_timeframes": (
            failed_timeframes
        ),
        "timeframes": (
            statuses
        ),
        "d1_evidence_superseded": (
            True
        ),
    }


def _age_adjudication(
    full_document: Mapping[
        str,
        Any,
    ],
    corrected_d1_document: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    full_group_statuses = (
        _mapping(
            full_document,
            "group_statuses",
        )
    )

    original_age_status = (
        _mapping(
            full_group_statuses,
            "age",
        )
    )

    corrected_age = (
        _mapping(
            corrected_d1_document,
            "d1_age",
        )
    )

    corrected_d1_age_status = (
        _mapping(
            corrected_age,
            "status",
        )
    )

    original_group_portable = (
        _portable_status(
            original_age_status
        )
    )

    corrected_d1_age_portable = (
        _portable_status(
            corrected_d1_age_status
        )
    )

    portable = bool(
        original_group_portable
        and
        corrected_d1_age_portable
    )

    return {
        "portable": (
            portable
        ),
        "original_full_age_group_portable": (
            original_group_portable
        ),
        "corrected_d1_age_portable": (
            corrected_d1_age_portable
        ),
        "d1_age_evidence_superseded": (
            True
        ),
        "reason": (
            "ORIGINAL_FIVE_FEATURE_AGE_GROUP_ALREADY_PASSED_"
            "AND_CORRECTED_D1_AGE_NOW_INDIVIDUALLY_PASSES"
            if portable
            else
            "AGE_PORTABILITY_NOT_CONFIRMED_AFTER_D1_CORRECTION"
        ),
    }


def _domain_adjudication(
    full_document: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    statuses = (
        _mapping(
            full_document,
            "group_statuses",
        )
    )

    domain = (
        _mapping(
            statuses,
            "domain",
        )
    )

    return {
        "portable": (
            _portable_status(
                domain
            )
        ),
        "status": str(
            domain.get(
                "status",
                "",
            )
        ),
        "reason": str(
            domain.get(
                "reason",
                "",
            )
        ),
        "evidence_source": (
            "FULL_MTF_PORTABILITY_V2"
        ),
    }


def _broker_sensitive_adjudication(
    full_document: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    statuses = (
        _mapping(
            full_document,
            "group_statuses",
        )
    )

    broker_sensitive = (
        _mapping(
            statuses,
            "broker_sensitive",
        )
    )

    summaries = (
        _mapping(
            full_document,
            "group_summaries",
        )
    )

    summary = (
        _mapping(
            summaries,
            "broker_sensitive",
        )
    )

    material_features = [
        str(
            value
        )
        for value
        in summary.get(
            "material_distribution_shift_features",
            [],
        )
    ]

    feature_count = int(
        summary.get(
            "feature_count",
            0,
        )
    )

    _require(
        feature_count
        ==
        EXPECTED_BROKER_SENSITIVE_FEATURE_COUNT,
        (
            "BROKER_SENSITIVE_SUMMARY_FEATURE_COUNT_MISMATCH:"
            f"{feature_count}"
        ),
    )

    return {
        "portable_as_is": (
            _portable_status(
                broker_sensitive
            )
        ),
        "normalization_required": (
            not
            _portable_status(
                broker_sensitive
            )
        ),
        "status": str(
            broker_sensitive.get(
                "status",
                "",
            )
        ),
        "reason": str(
            broker_sensitive.get(
                "reason",
                "",
            )
        ),
        "feature_count": (
            feature_count
        ),
        "material_distribution_shift_feature_count": int(
            summary.get(
                "material_distribution_shift_feature_count",
                0,
            )
        ),
        "material_distribution_shift_features": (
            material_features
        ),
        "material_distribution_shift_share": (
            _safe_float(
                summary.get(
                    "material_distribution_shift_share"
                )
            )
        ),
        "evidence_source": (
            "FULL_MTF_PORTABILITY_V2"
        ),
    }


def _feature_comparison_map(
    full_document: Mapping[
        str,
        Any,
    ],
) -> dict[
    str,
    Mapping[
        str,
        Any,
    ],
]:

    comparisons = (
        _sequence(
            full_document,
            "feature_comparisons",
        )
    )

    result: dict[
        str,
        Mapping[
            str,
            Any,
        ],
    ] = {}

    for item in (
        comparisons
    ):

        if not isinstance(
            item,
            Mapping,
        ):
            continue

        feature = str(
            item.get(
                "feature",
                "",
            )
        ).strip()

        if not feature:
            continue

        _require(
            feature
            not in
            result,
            (
                "DUPLICATE_FEATURE_COMPARISON:"
                f"{feature}"
            ),
        )

        result[
            feature
        ] = (
            item
        )

    return (
        result
    )


def _utc_feature_adjudication(
    feature: str,
    comparison: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    finite_fraction = (
        _safe_float(
            comparison.get(
                "finite_pair_fraction"
            )
        )
    )

    correlation = (
        _safe_float(
            comparison.get(
                "paired_correlation"
            )
        )
    )

    standardized_mean_shift = (
        _safe_float(
            comparison.get(
                "standardized_mean_shift"
            )
        )
    )

    paired_median_abs_diff = (
        _safe_float(
            comparison.get(
                "paired_median_abs_diff_reference_std"
            )
        )
    )

    median_shift = (
        _safe_float(
            comparison.get(
                "median_shift_reference_std"
            )
        )
    )

    psi = (
        _safe_float(
            comparison.get(
                "psi"
            )
        )
    )

    finite_ok = bool(
        finite_fraction
        is not None
        and
        finite_fraction
        >=
        UTC_MINIMUM_FINITE_PAIR_FRACTION
    )

    correlation_ok = bool(
        correlation
        is not None
        and
        correlation
        >=
        UTC_MINIMUM_PAIRED_CORRELATION
    )

    standardized_shift_ok = bool(
        standardized_mean_shift
        is not None
        and
        abs(
            standardized_mean_shift
        )
        <=
        UTC_MAX_ABS_STANDARDIZED_MEAN_SHIFT
    )

    paired_difference_ok = bool(
        paired_median_abs_diff
        is not None
        and
        abs(
            paired_median_abs_diff
        )
        <=
        UTC_MAX_PAIRED_MEDIAN_ABS_DIFF_REFERENCE_STD
    )

    median_shift_ok = bool(
        median_shift
        is not None
        and
        abs(
            median_shift
        )
        <=
        UTC_MAX_MEDIAN_SHIFT_REFERENCE_STD
    )

    equivalent = bool(
        finite_ok
        and
        correlation_ok
        and
        standardized_shift_ok
        and
        paired_difference_ok
        and
        median_shift_ok
    )

    return {
        "feature": (
            feature
        ),
        "portable": (
            equivalent
        ),
        "finite_pair_fraction": (
            finite_fraction
        ),
        "paired_correlation": (
            correlation
        ),
        "standardized_mean_shift": (
            standardized_mean_shift
        ),
        "paired_median_abs_diff_reference_std": (
            paired_median_abs_diff
        ),
        "median_shift_reference_std": (
            median_shift
        ),
        "psi": (
            psi
        ),
        "psi_used_for_portability_decision": (
            False
        ),
        "psi_exclusion_reason": (
            "UTC_CYCLICAL_FEATURE_IS_A_DETERMINISTIC_DISCRETE_"
            "TRANSFORM_OF_CANONICAL_DECISION_TIME_AND_PAIRED_"
            "NUMERICAL_EQUIVALENCE_IS_THE_APPROPRIATE_TEST"
        ),
        "checks": {
            "finite_pair_fraction_ok": (
                finite_ok
            ),
            "paired_correlation_ok": (
                correlation_ok
            ),
            "standardized_mean_shift_ok": (
                standardized_shift_ok
            ),
            "paired_median_abs_diff_ok": (
                paired_difference_ok
            ),
            "median_shift_ok": (
                median_shift_ok
            ),
        },
    }


def _utc_adjudication(
    full_document: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    time_semantics = (
        _mapping(
            full_document,
            "confirmed_time_semantics",
        )
    )

    utc_rule = str(
        time_semantics.get(
            "utc_feature_rule",
            "",
        )
    ).strip()

    _require(
        utc_rule
        ==
        "SINE_COSINE_FROM_CANONICAL_DECISION_TIME",
        (
            "UTC_FEATURE_RULE_NOT_CONFIRMED:"
            f"{utc_rule}"
        ),
    )

    comparison_map = (
        _feature_comparison_map(
            full_document
        )
    )

    feature_documents: list[
        dict[str, Any]
    ] = []

    for feature in (
        UTC_FEATURES
    ):

        _require(
            feature
            in
            comparison_map,
            (
                "UTC_FEATURE_COMPARISON_MISSING:"
                f"{feature}"
            ),
        )

        feature_document = (
            _utc_feature_adjudication(
                feature,
                comparison_map[
                    feature
                ],
            )
        )

        feature_documents.append(
            feature_document
        )

    portable = all(
        bool(
            document[
                "portable"
            ]
        )
        for document
        in feature_documents
    )

    failed_features = [
        str(
            document[
                "feature"
            ]
        )
        for document
        in feature_documents
        if not bool(
            document[
                "portable"
            ]
        )
    ]

    return {
        "portable": (
            portable
        ),
        "status": (
            "UTC_DETERMINISTIC_DECISION_TIME_EQUIVALENCE_CONFIRMED"
            if portable
            else
            "UTC_DETERMINISTIC_DECISION_TIME_EQUIVALENCE_NOT_CONFIRMED"
        ),
        "reason": (
            "ALL_FOUR_UTC_CYCLICAL_FEATURES_ARE_NUMERICALLY_"
            "EQUIVALENT_ON_THE_SAME_CANONICAL_DECISION_TIME_GRID"
            if portable
            else
            "ONE_OR_MORE_UTC_CYCLICAL_FEATURES_FAIL_PAIRED_"
            "NUMERICAL_EQUIVALENCE_THRESHOLDS"
        ),
        "feature_rule": (
            utc_rule
        ),
        "failed_features": (
            failed_features
        ),
        "features": (
            feature_documents
        ),
        "psi_policy": (
            "PSI_NOT_USED_FOR_DETERMINISTIC_UTC_CYCLICAL_"
            "FEATURE_PORTABILITY_ADJUDICATION"
        ),
        "evidence_source": (
            "FULL_MTF_PORTABILITY_V2"
        ),
    }


def _validate_corrected_d1_result(
    corrected_document: Mapping[
        str,
        Any,
    ],
) -> None:

    decision = (
        _mapping(
            corrected_document,
            "decision",
        )
    )

    _require(
        str(
            decision.get(
                "status",
                "",
            )
        )
        ==
        "D1_CORRECTED_TRAIN_ROW_PORTABILITY_CONFIRMED",
        (
            "CORRECTED_D1_PREREQUISITE_NOT_CONFIRMED:"
            f"{decision.get('status')}"
        ),
    )

    _require(
        bool(
            decision.get(
                "technical_portable",
                False,
            )
        ),
        "CORRECTED_D1_TECHNICAL_NOT_PORTABLE",
    )

    _require(
        bool(
            decision.get(
                "d1_age_portable",
                False,
            )
        ),
        "CORRECTED_D1_AGE_NOT_PORTABLE",
    )

    alignment = (
        _mapping(
            corrected_document,
            "alignment",
        )
    )

    _require(
        int(
            alignment.get(
                "train_rows",
                0,
            )
        )
        ==
        EXPECTED_TRAIN_ROWS,
        "CORRECTED_D1_TRAIN_ROWS_MISMATCH",
    )

    _require(
        int(
            alignment.get(
                "matched_train_rows",
                0,
            )
        )
        ==
        EXPECTED_TRAIN_ROWS,
        "CORRECTED_D1_MATCHED_TRAIN_ROWS_MISMATCH",
    )

    _require(
        int(
            alignment.get(
                "unique_d1_states_on_train_grid",
                0,
            )
        )
        ==
        EXPECTED_D1_STATE_COUNT,
        "CORRECTED_D1_STATE_COUNT_MISMATCH",
    )

    _require(
        int(
            alignment.get(
                "negative_d1_age_rows",
                -1,
            )
        )
        ==
        0,
        "CORRECTED_D1_NEGATIVE_AGE_ROWS_PRESENT",
    )


def _final_classification(
    *,
    technical: Mapping[
        str,
        Any,
    ],
    domain: Mapping[
        str,
        Any,
    ],
    age: Mapping[
        str,
        Any,
    ],
    utc: Mapping[
        str,
        Any,
    ],
    broker_sensitive: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    technical_portable = bool(
        technical.get(
            "portable",
            False,
        )
    )

    domain_portable = bool(
        domain.get(
            "portable",
            False,
        )
    )

    age_portable = bool(
        age.get(
            "portable",
            False,
        )
    )

    utc_portable = bool(
        utc.get(
            "portable",
            False,
        )
    )

    broker_sensitive_portable = bool(
        broker_sensitive.get(
            "portable_as_is",
            False,
        )
    )

    non_broker_sensitive_portable = bool(
        technical_portable
        and
        domain_portable
        and
        age_portable
        and
        utc_portable
    )

    if (
        non_broker_sensitive_portable
        and
        not broker_sensitive_portable
    ):

        classification = (
            "XAUUSD_330_NON_BROKER_SENSITIVE_FEATURES_"
            "TRAIN_PORTABILITY_CONFIRMED"
        )

        reason = (
            "ALL_NON_BROKER_SENSITIVE_GROUPS_PASS_AFTER_"
            "CORRECTED_D1_AND_DETERMINISTIC_UTC_ADJUDICATION_"
            "WHILE_THE_BROKER_SENSITIVE_GROUP_REQUIRES_NORMALIZATION"
        )

        next_action = (
            "DESIGN_NEW_XAUUSD_PORTABLE_FEATURE_CONTRACT_"
            "WITHOUT_MUTATING_FROZEN_V3"
        )

    elif (
        non_broker_sensitive_portable
        and
        broker_sensitive_portable
    ):

        classification = (
            "XAUUSD_FULL_333_TRAIN_PORTABILITY_CONFIRMED"
        )

        reason = (
            "ALL_FEATURE_GROUPS_PASS_TRAIN_ONLY_"
            "CROSS_BROKER_PORTABILITY_ADJUDICATION"
        )

        next_action = (
            "FREEZE_RESEARCH_PORTABILITY_CONTRACT_BEFORE_"
            "FORWARD_OR_MODEL_EVALUATION"
        )

    else:

        classification = (
            "XAUUSD_NON_BROKER_SENSITIVE_PORTABILITY_NOT_CONFIRMED"
        )

        reason = (
            "ONE_OR_MORE_NON_BROKER_SENSITIVE_GROUPS_"
            "REMAIN_UNRESOLVED"
        )

        next_action = (
            "ISOLATE_ONLY_FAILED_NON_BROKER_SENSITIVE_GROUPS"
        )

    return {
        "classification": (
            classification
        ),
        "reason": (
            reason
        ),
        "technical_all_portable": (
            technical_portable
        ),
        "domain_group_portable": (
            domain_portable
        ),
        "age_group_portable": (
            age_portable
        ),
        "utc_group_portable": (
            utc_portable
        ),
        "broker_sensitive_group_portable_as_is": (
            broker_sensitive_portable
        ),
        "broker_sensitive_normalization_required": (
            not broker_sensitive_portable
        ),
        "non_broker_sensitive_330_portable": (
            non_broker_sensitive_portable
        ),
        "portable_feature_count_before_broker_sensitive_redesign": (
            EXPECTED_NON_BROKER_SENSITIVE_FEATURE_COUNT
            if non_broker_sensitive_portable
            else None
        ),
        "full_333_portable_as_is": bool(
            non_broker_sensitive_portable
            and
            broker_sensitive_portable
        ),
        "research_portability_verdict_issued": (
            True
        ),
        "full_333_live_portability_claimed": (
            False
        ),
        "broker_specific_retraining_authorized": (
            False
        ),
        "test_evaluation_authorized": (
            False
        ),
        "portable_feature_contract_design_authorized": bool(
            non_broker_sensitive_portable
            and
            not broker_sensitive_portable
        ),
        "next_action": (
            next_action
        ),
    }


def run_adjudication(
) -> dict[str, Any]:

    full_document = (
        _load_json(
            FULL_AUDIT_JSON
        )
    )

    corrected_d1_document = (
        _load_json(
            CORRECTED_D1_JSON
        )
    )

    _require(
        bool(
            full_document.get(
                "valid",
                False,
            )
        ),
        "FULL_MTF_V2_EVIDENCE_NOT_VALID",
    )

    _require(
        bool(
            corrected_d1_document.get(
                "valid",
                False,
            )
        ),
        "CORRECTED_D1_EVIDENCE_NOT_VALID",
    )

    _require(
        str(
            full_document.get(
                "analysis_version",
                "",
            )
        )
        ==
        EXPECTED_FULL_AUDIT_VERSION,
        (
            "FULL_MTF_ANALYSIS_VERSION_MISMATCH:"
            f"{full_document.get('analysis_version')}"
        ),
    )

    _require(
        str(
            corrected_d1_document.get(
                "analysis_version",
                "",
            )
        )
        ==
        EXPECTED_CORRECTED_D1_VERSION,
        (
            "CORRECTED_D1_ANALYSIS_VERSION_MISMATCH:"
            f"{corrected_d1_document.get('analysis_version')}"
        ),
    )

    _validate_research_only_policy(
        full_document,
        source_name=(
            "FULL_MTF_PORTABILITY_V2"
        ),
    )

    _validate_research_only_policy(
        corrected_d1_document,
        source_name=(
            "CORRECTED_D1_PORTABILITY_V1"
        ),
    )

    evidence_identity = (
        _validate_same_evidence_identity(
            full_document,
            corrected_d1_document,
        )
    )

    feature_contract = (
        _validate_feature_contract(
            full_document
        )
    )

    _validate_corrected_d1_result(
        corrected_d1_document
    )

    technical = (
        _technical_adjudication(
            full_document,
            corrected_d1_document,
        )
    )

    domain = (
        _domain_adjudication(
            full_document
        )
    )

    age = (
        _age_adjudication(
            full_document,
            corrected_d1_document,
        )
    )

    utc = (
        _utc_adjudication(
            full_document
        )
    )

    broker_sensitive = (
        _broker_sensitive_adjudication(
            full_document
        )
    )

    classification = (
        _final_classification(
            technical=(
                technical
            ),
            domain=(
                domain
            ),
            age=(
                age
            ),
            utc=(
                utc
            ),
            broker_sensitive=(
                broker_sensitive
            ),
        )
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_CURRENT_BROKER_FULL_333_"
            "EVIDENCE_ADJUDICATION"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "research_scope": (
            "FINAL_TRAIN_ONLY_CROSS_BROKER_333_FEATURE_"
            "PORTABILITY_EVIDENCE_ADJUDICATION"
        ),
        "evidence_inputs": {
            "full_mtf": {
                "analysis_version": (
                    EXPECTED_FULL_AUDIT_VERSION
                ),
                "immutable_evidence": (
                    True
                ),
                "rerun_performed": (
                    False
                ),
            },
            "corrected_d1": {
                "analysis_version": (
                    EXPECTED_CORRECTED_D1_VERSION
                ),
                "supersedes_original_full_mtf_d1_evidence": (
                    True
                ),
            },
        },
        "evidence_identity": (
            evidence_identity
        ),
        "feature_contract": {
            "total_feature_count": int(
                feature_contract[
                    "total_feature_count"
                ]
            ),
            "technical_feature_count": int(
                feature_contract[
                    "technical_feature_count"
                ]
            ),
            "domain_feature_count": int(
                feature_contract[
                    "domain_feature_count"
                ]
            ),
            "broker_sensitive_feature_count": int(
                feature_contract[
                    "broker_sensitive_feature_count"
                ]
            ),
            "age_feature_count": int(
                feature_contract[
                    "age_feature_count"
                ]
            ),
            "utc_feature_count": int(
                feature_contract[
                    "utc_feature_count"
                ]
            ),
            "non_broker_sensitive_feature_count": (
                EXPECTED_NON_BROKER_SENSITIVE_FEATURE_COUNT
            ),
            "broker_sensitive_features": list(
                BROKER_SENSITIVE_FEATURES
            ),
            "utc_features": list(
                UTC_FEATURES
            ),
        },
        "adjudicated_groups": {
            "technical": (
                technical
            ),
            "domain": (
                domain
            ),
            "age": (
                age
            ),
            "utc": (
                utc
            ),
            "broker_sensitive": (
                broker_sensitive
            ),
        },
        "classification": (
            classification
        ),
        "utc_adjudication_policy": {
            "minimum_finite_pair_fraction": (
                UTC_MINIMUM_FINITE_PAIR_FRACTION
            ),
            "minimum_paired_correlation": (
                UTC_MINIMUM_PAIRED_CORRELATION
            ),
            "maximum_abs_standardized_mean_shift": (
                UTC_MAX_ABS_STANDARDIZED_MEAN_SHIFT
            ),
            "maximum_paired_median_abs_diff_reference_std": (
                UTC_MAX_PAIRED_MEDIAN_ABS_DIFF_REFERENCE_STD
            ),
            "maximum_median_shift_reference_std": (
                UTC_MAX_MEDIAN_SHIFT_REFERENCE_STD
            ),
            "psi_used": (
                False
            ),
            "psi_exclusion_scope": (
                "ONLY_THE_FOUR_DETERMINISTIC_UTC_CYCLICAL_FEATURES"
            ),
            "psi_exclusion_does_not_apply_to_other_feature_groups": (
                True
            ),
        },
        "scientific_policy": {
            "train_evidence_used": (
                True
            ),
            "validation_loaded": (
                False
            ),
            "validation_evaluated": (
                False
            ),
            "test_loaded": (
                False
            ),
            "test_evaluated": (
                False
            ),
            "labels_used": (
                False
            ),
            "target_columns_loaded": (
                False
            ),
            "model_loaded": (
                False
            ),
            "model_trained": (
                False
            ),
            "model_artifacts_written": (
                False
            ),
            "mt5_used": (
                False
            ),
            "orders_sent": (
                False
            ),
            "positions_modified": (
                False
            ),
            "risk_engine_modified": (
                False
            ),
            "sizing_modified": (
                False
            ),
            "execution_integration_modified": (
                False
            ),
            "frozen_v3_contract_mutated": (
                False
            ),
            "broker_specific_retraining_authorized": (
                False
            ),
            "test_evaluation_authorized": (
                False
            ),
            "live_authorized": (
                False
            ),
            "account_login_emitted": (
                False
            ),
            "account_holder_name_emitted": (
                False
            ),
            "account_scope_identifier_emitted": (
                False
            ),
            "filesystem_paths_emitted": (
                False
            ),
        },
        "next_decision_contract": {
            "if_only_broker_sensitive_normalization_remains": (
                "DESIGN_NEW_XAUUSD_PORTABLE_FEATURE_CONTRACT_"
                "WITHOUT_MUTATING_FROZEN_V3"
            ),
            "portable_spread_direction": (
                "REPLACE_OR_REMOVE_RAW_SPREAD_POINTS_USING_"
                "BROKER_INVARIANT_SPREAD_NORMALIZATION"
            ),
            "portable_tick_volume_direction": (
                "NORMALIZE_OR_REMOVE_ABSOLUTE_TICK_VOLUME_LEVEL_"
                "WHILE_REASSESSING_RELATIVE_TICK_VOLUME_RATIO"
            ),
            "new_target_contract_required": (
                False
            ),
            "target_contract_change_authorized": (
                False
            ),
            "model_retraining_authorized": (
                False
            ),
            "test_holdout_remains_untouched": (
                True
            ),
            "v3_contract_not_mutated": (
                True
            ),
            "live_authorization_not_changed": (
                True
            ),
        },
    }


def main() -> int:

    try:

        result = (
            run_adjudication()
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_CURRENT_BROKER_FULL_333_"
                        "EVIDENCE_ADJUDICATION_FAILED"
                    ),
                    "analysis_version": (
                        ANALYSIS_VERSION
                    ),
                    "error_type": (
                        type(
                            exc
                        ).__name__
                    ),
                    "error": (
                        str(
                            exc
                        )
                    ),
                    "validation_loaded": (
                        False
                    ),
                    "test_loaded": (
                        False
                    ),
                    "test_evaluated": (
                        False
                    ),
                    "model_loaded": (
                        False
                    ),
                    "model_trained": (
                        False
                    ),
                    "model_artifacts_written": (
                        False
                    ),
                    "mt5_used": (
                        False
                    ),
                    "orders_sent": (
                        False
                    ),
                    "positions_modified": (
                        False
                    ),
                    "risk_engine_modified": (
                        False
                    ),
                    "live_authorized": (
                        False
                    ),
                },
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
        )

        return 2

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    )

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )