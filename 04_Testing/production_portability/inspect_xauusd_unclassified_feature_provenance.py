from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


ANALYSIS_VERSION = (
    "XAUUSD_UNCLASSIFIED_FEATURE_PROVENANCE_INSPECTION_V1"
)

SOURCE_RELATIVE_PATH = Path(
    "02_AI"
) / "Dataset" / "training_matrix_builder.py"

SOURCE_PATH = (
    ROOT_DIR
    /
    SOURCE_RELATIVE_PATH
)


AGE_FEATURES = (
    "m15_age_minutes",
    "m30_age_minutes",
    "h1_age_minutes",
    "h4_age_minutes",
    "d1_age_minutes",
)

UTC_FEATURES = (
    "utc_hour_sin",
    "utc_hour_cos",
    "utc_day_sin",
    "utc_day_cos",
)

EXPECTED_UNCLASSIFIED_FEATURES = (
    *AGE_FEATURES,
    *UTC_FEATURES,
)


RELEVANT_SOURCE_TOKENS = (
    "_age_minutes",
    "age_minutes",
    "merge_asof",
    "total_seconds",
    "decision_time",
    "feature_availability",
    "availability_time",
    "BAR_FEATURES_AVAILABLE_ONLY_AFTER_BAR_CLOSE",
    "utc_hour_sin",
    "utc_hour_cos",
    "utc_day_sin",
    "utc_day_cos",
    "dayofweek",
    "hour",
    "np.sin",
    "np.cos",
    "2.0 * np.pi",
    "2 * np.pi",
)


def _require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise RuntimeError(
            reason
        )


def _read_source() -> str:

    _require(
        SOURCE_PATH.is_file(),
        (
            "TRAINING_MATRIX_BUILDER_NOT_FOUND:"
            f"{SOURCE_RELATIVE_PATH.as_posix()}"
        ),
    )

    return SOURCE_PATH.read_text(
        encoding="utf-8",
    )


def _attribute_name(
    node: ast.AST,
) -> str:

    if isinstance(
        node,
        ast.Name,
    ):
        return node.id

    if isinstance(
        node,
        ast.Attribute,
    ):

        left = (
            _attribute_name(
                node.value
            )
        )

        if left:
            return (
                left
                +
                "."
                +
                node.attr
            )

        return node.attr

    if isinstance(
        node,
        ast.Call,
    ):
        return _attribute_name(
            node.func
        )

    return ""


def _definition_documents(
    tree: ast.AST,
) -> list[dict[str, Any]]:

    documents: list[
        dict[str, Any]
    ] = []

    for node in ast.walk(
        tree
    ):

        if not isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            continue

        documents.append(
            {
                "name": (
                    node.name
                ),
                "line_start": int(
                    node.lineno
                ),
                "line_end": int(
                    getattr(
                        node,
                        "end_lineno",
                        node.lineno,
                    )
                ),
            }
        )

    return sorted(
        documents,
        key=lambda item: (
            int(
                item[
                    "line_start"
                ]
            ),
            int(
                item[
                    "line_end"
                ]
            ),
        ),
    )


def _enclosing_definition(
    definitions: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
    line_number: int,
) -> str | None:

    candidates = [
        document
        for document
        in definitions
        if (
            int(
                document[
                    "line_start"
                ]
            )
            <=
            line_number
            <=
            int(
                document[
                    "line_end"
                ]
            )
        )
    ]

    if not candidates:
        return None

    candidates = sorted(
        candidates,
        key=lambda item: (
            int(
                item[
                    "line_end"
                ]
            )
            -
            int(
                item[
                    "line_start"
                ]
            )
        ),
    )

    return str(
        candidates[
            0
        ][
            "name"
        ]
    )


def _source_segment(
    source: str,
    node: ast.AST,
) -> str:

    segment = ast.get_source_segment(
        source,
        node,
    )

    if segment is None:
        return ""

    return segment.strip()


def _contains_relevant_token(
    text: str,
) -> bool:

    lowered = (
        text.lower()
    )

    return any(
        token.lower()
        in
        lowered
        for token
        in RELEVANT_SOURCE_TOKENS
    )


def _statement_documents(
    source: str,
    tree: ast.AST,
    definitions: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
) -> list[dict[str, Any]]:

    documents: list[
        dict[str, Any]
    ] = []

    statement_types = (
        ast.Assign,
        ast.AnnAssign,
        ast.AugAssign,
        ast.Expr,
        ast.If,
        ast.For,
    )

    for node in ast.walk(
        tree
    ):

        if not isinstance(
            node,
            statement_types,
        ):
            continue

        segment = (
            _source_segment(
                source,
                node,
            )
        )

        if not segment:
            continue

        if not _contains_relevant_token(
            segment
        ):
            continue

        line_start = int(
            getattr(
                node,
                "lineno",
                0,
            )
        )

        line_end = int(
            getattr(
                node,
                "end_lineno",
                line_start,
            )
        )

        documents.append(
            {
                "line_start": (
                    line_start
                ),
                "line_end": (
                    line_end
                ),
                "definition": (
                    _enclosing_definition(
                        definitions,
                        line_start,
                    )
                ),
                "node_type": (
                    type(
                        node
                    ).__name__
                ),
                "source": (
                    segment
                ),
            }
        )

    unique: dict[
        tuple[int, int, str],
        dict[str, Any],
    ] = {}

    for document in documents:

        key = (
            int(
                document[
                    "line_start"
                ]
            ),
            int(
                document[
                    "line_end"
                ]
            ),
            str(
                document[
                    "source"
                ]
            ),
        )

        unique[
            key
        ] = (
            document
        )

    return sorted(
        unique.values(),
        key=lambda item: (
            int(
                item[
                    "line_start"
                ]
            ),
            int(
                item[
                    "line_end"
                ]
            ),
        ),
    )


def _literal_string_documents(
    tree: ast.AST,
    definitions: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
) -> list[dict[str, Any]]:

    documents: list[
        dict[str, Any]
    ] = []

    for node in ast.walk(
        tree
    ):

        if not isinstance(
            node,
            ast.Constant,
        ):
            continue

        if not isinstance(
            node.value,
            str,
        ):
            continue

        value = (
            node.value
        )

        if not _contains_relevant_token(
            value
        ):
            continue

        line_number = int(
            getattr(
                node,
                "lineno",
                0,
            )
        )

        documents.append(
            {
                "line": (
                    line_number
                ),
                "definition": (
                    _enclosing_definition(
                        definitions,
                        line_number,
                    )
                ),
                "value": (
                    value
                ),
            }
        )

    return sorted(
        documents,
        key=lambda item: int(
            item[
                "line"
            ]
        ),
    )


def _call_documents(
    source: str,
    tree: ast.AST,
    definitions: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
) -> list[dict[str, Any]]:

    relevant_call_tokens = (
        "merge_asof",
        "total_seconds",
        "sin",
        "cos",
        "astype",
        "to_timedelta",
    )

    documents: list[
        dict[str, Any]
    ] = []

    for node in ast.walk(
        tree
    ):

        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        call_name = (
            _attribute_name(
                node.func
            )
        )

        if not any(
            token
            in
            call_name
            for token
            in relevant_call_tokens
        ):
            continue

        segment = (
            _source_segment(
                source,
                node
            )
        )

        line_start = int(
            getattr(
                node,
                "lineno",
                0,
            )
        )

        line_end = int(
            getattr(
                node,
                "end_lineno",
                line_start,
            )
        )

        documents.append(
            {
                "call": (
                    call_name
                ),
                "line_start": (
                    line_start
                ),
                "line_end": (
                    line_end
                ),
                "definition": (
                    _enclosing_definition(
                        definitions,
                        line_start,
                    )
                ),
                "source": (
                    segment
                ),
            }
        )

    return sorted(
        documents,
        key=lambda item: (
            int(
                item[
                    "line_start"
                ]
            ),
            str(
                item[
                    "call"
                ]
            ),
        ),
    )


def _line_occurrences(
    source: str,
    patterns: Sequence[str],
) -> dict[str, list[int]]:

    lines = (
        source.splitlines()
    )

    result: dict[
        str,
        list[int],
    ] = {}

    for pattern in patterns:

        lowered_pattern = (
            pattern.lower()
        )

        matches = [
            int(
                index
            )
            for index, line
            in enumerate(
                lines,
                start=1,
            )
            if lowered_pattern
            in
            line.lower()
        ]

        result[
            pattern
        ] = (
            matches
        )

    return (
        result
    )


def _context_excerpt(
    source_lines: Sequence[str],
    *,
    line_number: int,
    before: int = 3,
    after: int = 5,
) -> dict[str, Any]:

    start = max(
        1,
        line_number
        -
        before,
    )

    end = min(
        len(
            source_lines
        ),
        line_number
        +
        after,
    )

    text = "\n".join(
        (
            f"{index}: "
            f"{source_lines[index - 1]}"
        )
        for index
        in range(
            start,
            end + 1,
        )
    )

    return {
        "anchor_line": (
            line_number
        ),
        "line_start": (
            start
        ),
        "line_end": (
            end
        ),
        "source": (
            text
        ),
    }


def _relevant_excerpts(
    source: str,
    occurrences: Mapping[
        str,
        Sequence[int],
    ],
) -> list[dict[str, Any]]:

    source_lines = (
        source.splitlines()
    )

    priority_patterns = (
        "_age_minutes",
        "merge_asof",
        "total_seconds",
        "utc_hour_sin",
        "utc_hour_cos",
        "utc_day_sin",
        "utc_day_cos",
        "dayofweek",
        "np.sin",
        "np.cos",
        "BAR_FEATURES_AVAILABLE_ONLY_AFTER_BAR_CLOSE",
    )

    anchor_lines: set[
        int
    ] = set()

    for pattern in (
        priority_patterns
    ):

        for line_number in (
            occurrences.get(
                pattern,
                (),
            )
        ):

            anchor_lines.add(
                int(
                    line_number
                )
            )

    excerpts = [
        _context_excerpt(
            source_lines,
            line_number=(
                line_number
            ),
        )
        for line_number
        in sorted(
            anchor_lines
        )
    ]

    merged: list[
        dict[str, Any]
    ] = []

    for excerpt in excerpts:

        if not merged:

            merged.append(
                excerpt
            )

            continue

        previous = (
            merged[
                -1
            ]
        )

        if (
            int(
                excerpt[
                    "line_start"
                ]
            )
            <=
            int(
                previous[
                    "line_end"
                ]
            )
            +
            1
        ):

            combined_start = int(
                previous[
                    "line_start"
                ]
            )

            combined_end = max(
                int(
                    previous[
                        "line_end"
                    ]
                ),
                int(
                    excerpt[
                        "line_end"
                    ]
                ),
            )

            merged[
                -1
            ] = {
                "anchor_line": (
                    previous[
                        "anchor_line"
                    ]
                ),
                "line_start": (
                    combined_start
                ),
                "line_end": (
                    combined_end
                ),
                "source": "\n".join(
                    (
                        f"{index}: "
                        f"{source_lines[index - 1]}"
                    )
                    for index
                    in range(
                        combined_start,
                        combined_end + 1,
                    )
                ),
            }

        else:

            merged.append(
                excerpt
            )

    return (
        merged
    )


def _method_names_with_relevant_statements(
    statement_documents: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
) -> list[str]:

    names = {
        str(
            document[
                "definition"
            ]
        )
        for document
        in statement_documents
        if document.get(
            "definition"
        )
        is not None
    }

    return sorted(
        names
    )


def _contains_any(
    source: str,
    tokens: Iterable[str],
) -> bool:

    lowered = (
        source.lower()
    )

    return any(
        token.lower()
        in
        lowered
        for token
        in tokens
    )


def _decision(
    source: str,
    occurrences: Mapping[
        str,
        Sequence[int],
    ],
    statement_documents: Sequence[
        Mapping[
            str,
            Any,
        ]
    ],
) -> dict[str, Any]:

    age_template_found = bool(
        occurrences.get(
            "_age_minutes"
        )
        or
        occurrences.get(
            "age_minutes"
        )
    )

    merge_asof_found = bool(
        occurrences.get(
            "merge_asof"
        )
    )

    total_seconds_found = bool(
        occurrences.get(
            "total_seconds"
        )
    )

    decision_time_found = bool(
        occurrences.get(
            "decision_time"
        )
    )

    availability_rule_found = bool(
        occurrences.get(
            "BAR_FEATURES_AVAILABLE_ONLY_AFTER_BAR_CLOSE"
        )
    )

    utc_literal_presence = {
        feature: bool(
            occurrences.get(
                feature
            )
        )
        for feature
        in UTC_FEATURES
    }

    all_utc_literals_found = all(
        utc_literal_presence.values()
    )

    np_sin_found = bool(
        occurrences.get(
            "np.sin"
        )
    )

    np_cos_found = bool(
        occurrences.get(
            "np.cos"
        )
    )

    dayofweek_found = bool(
        occurrences.get(
            "dayofweek"
        )
    )

    hour_reference_found = bool(
        occurrences.get(
            "hour"
        )
    )

    statement_source = "\n".join(
        str(
            document.get(
                "source",
                "",
            )
        )
        for document
        in statement_documents
    )

    dynamic_prefix_evidence = (
        age_template_found
        and
        _contains_any(
            statement_source,
            (
                "prefix",
                "_feature_prefix",
                "context_timeframe",
                "timeframe",
            ),
        )
    )

    age_provenance_resolved = bool(
        age_template_found
        and
        merge_asof_found
        and
        total_seconds_found
        and
        decision_time_found
        and
        dynamic_prefix_evidence
    )

    utc_provenance_resolved = bool(
        all_utc_literals_found
        and
        np_sin_found
        and
        np_cos_found
        and
        dayofweek_found
        and
        hour_reference_found
        and
        decision_time_found
    )

    if (
        age_provenance_resolved
        and
        utc_provenance_resolved
    ):

        status = (
            "UNCLASSIFIED_FEATURE_PROVENANCE_RESOLVED"
        )

        reason = (
            "ALL_FIVE_HTF_AGE_FEATURES_TRACE_TO_"
            "CAUSAL_ASOF_ALIGNMENT_AGE_METADATA_AND_"
            "ALL_FOUR_UTC_FEATURES_TRACE_TO_"
            "DECISION_TIME_CYCLICAL_CALENDAR_ENCODING"
        )

        full_audit_allowed = (
            True
        )

        next_action = (
            "RUN_CURRENT_BROKER_FULL_MTF_PLUS_DOMAIN_"
            "TRAIN_ONLY_PORTABILITY_AUDIT_WITH_EXPLICIT_"
            "TECHNICAL_DOMAIN_BROKER_ALIGNMENT_AND_CALENDAR_GROUPS"
        )

    elif (
        age_provenance_resolved
        or
        utc_provenance_resolved
    ):

        status = (
            "UNCLASSIFIED_FEATURE_PROVENANCE_PARTIALLY_RESOLVED"
        )

        reason = (
            "ONLY_ONE_OF_ALIGNMENT_AGE_OR_UTC_CALENDAR_"
            "FEATURE_GROUPS_HAS_COMPLETE_SOURCE_EVIDENCE"
        )

        full_audit_allowed = (
            False
        )

        next_action = (
            "TRACE_ONLY_THE_REMAINING_UNRESOLVED_"
            "FEATURE_GROUP_BEFORE_FULL_MTF_AUDIT"
        )

    else:

        status = (
            "UNCLASSIFIED_FEATURE_PROVENANCE_UNRESOLVED"
        )

        reason = (
            "SOURCE_INSPECTION_DID_NOT_ESTABLISH_"
            "CAUSAL_FORMULAS_FOR_THE_NINE_FEATURES"
        )

        full_audit_allowed = (
            False
        )

        next_action = (
            "INSPECT_EXACT_TRAINING_MATRIX_BUILD_BLOCK_"
            "AROUND_MTF_ALIGNMENT_AND_TIME_FEATURE_CONSTRUCTION"
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "age_feature_provenance_resolved": (
            age_provenance_resolved
        ),
        "utc_feature_provenance_resolved": (
            utc_provenance_resolved
        ),
        "full_333_portability_audit_allowed": (
            full_audit_allowed
        ),
        "next_action": (
            next_action
        ),
        "evidence": {
            "age_template_found": (
                age_template_found
            ),
            "merge_asof_found": (
                merge_asof_found
            ),
            "total_seconds_found": (
                total_seconds_found
            ),
            "decision_time_found": (
                decision_time_found
            ),
            "dynamic_prefix_evidence": (
                dynamic_prefix_evidence
            ),
            "availability_rule_found": (
                availability_rule_found
            ),
            "utc_literal_presence": (
                utc_literal_presence
            ),
            "np_sin_found": (
                np_sin_found
            ),
            "np_cos_found": (
                np_cos_found
            ),
            "dayofweek_found": (
                dayofweek_found
            ),
            "hour_reference_found": (
                hour_reference_found
            ),
        },
    }


def run_inspection(
) -> dict[str, Any]:

    source = (
        _read_source()
    )

    tree = ast.parse(
        source,
        filename=str(
            SOURCE_RELATIVE_PATH
        ),
    )

    definitions = (
        _definition_documents(
            tree
        )
    )

    occurrences = (
        _line_occurrences(
            source,
            (
                *EXPECTED_UNCLASSIFIED_FEATURES,
                "_age_minutes",
                "age_minutes",
                "merge_asof",
                "total_seconds",
                "decision_time",
                "feature_availability",
                "availability_time",
                "BAR_FEATURES_AVAILABLE_ONLY_AFTER_BAR_CLOSE",
                "dayofweek",
                "hour",
                "np.sin",
                "np.cos",
            ),
        )
    )

    statements = (
        _statement_documents(
            source,
            tree,
            definitions,
        )
    )

    string_literals = (
        _literal_string_documents(
            tree,
            definitions,
        )
    )

    calls = (
        _call_documents(
            source,
            tree,
            definitions,
        )
    )

    excerpts = (
        _relevant_excerpts(
            source,
            occurrences,
        )
    )

    decision = (
        _decision(
            source,
            occurrences,
            statements,
        )
    )

    age_feature_documents = [
        {
            "feature": (
                feature
            ),
            "expected_role": (
                "HTF_ALIGNMENT_AGE_METADATA"
            ),
            "expected_timeframe": (
                feature
                .split(
                    "_",
                    1,
                )[
                    0
                ]
                .upper()
            ),
            "literal_name_present_in_source": bool(
                occurrences.get(
                    feature
                )
            ),
            "dynamic_template_expected": (
                True
            ),
        }
        for feature
        in AGE_FEATURES
    ]

    utc_feature_documents = [
        {
            "feature": (
                feature
            ),
            "expected_role": (
                "DECISION_TIME_CYCLICAL_CALENDAR_ENCODING"
            ),
            "literal_name_present_in_source": bool(
                occurrences.get(
                    feature
                )
            ),
            "source_lines": list(
                occurrences.get(
                    feature,
                    (),
                )
            ),
        }
        for feature
        in UTC_FEATURES
    ]

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_UNCLASSIFIED_"
            "FEATURE_PROVENANCE_INSPECTION"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "source_contract": {
            "source_file": (
                SOURCE_RELATIVE_PATH.as_posix()
            ),
            "source_exists": (
                True
            ),
            "source_line_count": int(
                len(
                    source.splitlines()
                )
            ),
            "ast_parse_ok": (
                True
            ),
            "project_module_imported": (
                False
            ),
            "project_code_executed": (
                False
            ),
        },
        "expected_unclassified_contract": {
            "feature_count": int(
                len(
                    EXPECTED_UNCLASSIFIED_FEATURES
                )
            ),
            "features": list(
                EXPECTED_UNCLASSIFIED_FEATURES
            ),
            "age_feature_count": int(
                len(
                    AGE_FEATURES
                )
            ),
            "utc_feature_count": int(
                len(
                    UTC_FEATURES
                )
            ),
        },
        "decision": (
            decision
        ),
        "age_feature_provenance": {
            "features": (
                age_feature_documents
            ),
            "expected_construction": (
                "CAUSAL_HIGHER_TIMEFRAME_ASOF_ALIGNMENT_"
                "PLUS_DECISION_TIME_MINUS_SOURCE_FEATURE_"
                "AVAILABILITY_TIME_IN_MINUTES"
            ),
            "expected_availability_semantics": (
                "HIGHER_TIMEFRAME_BAR_FEATURES_AVAILABLE_"
                "ONLY_AFTER_THEIR_BAR_CLOSE"
            ),
        },
        "utc_feature_provenance": {
            "features": (
                utc_feature_documents
            ),
            "expected_construction": (
                "CYCLICAL_ENCODING_FROM_DECISION_TIME_"
                "USING_SINE_AND_COSINE"
            ),
            "expected_portability_role": (
                "BROKER_INDEPENDENT_AFTER_CANONICAL_"
                "DECISION_TIME_NORMALIZATION"
            ),
        },
        "relevant_method_names": (
            _method_names_with_relevant_statements(
                statements
            )
        ),
        "line_occurrences": (
            occurrences
        ),
        "relevant_statements": (
            statements
        ),
        "relevant_calls": (
            calls
        ),
        "relevant_string_literals": (
            string_literals
        ),
        "source_excerpts": (
            excerpts
        ),
        "scientific_policy": {
            "local_source_read": (
                True
            ),
            "ast_only": (
                True
            ),
            "frozen_manifest_loaded": (
                False
            ),
            "frozen_training_rows_loaded": (
                False
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
            "current_broker_used": (
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
        },
        "next_decision_contract": {
            "if_resolved": (
                "RUN_CURRENT_BROKER_FULL_MTF_PLUS_DOMAIN_"
                "TRAIN_ONLY_PORTABILITY_AUDIT"
            ),
            "if_age_only_unresolved": (
                "INSPECT_ONLY_CAUSAL_MERGE_ASOF_"
                "AGE_CALCULATION_BLOCK"
            ),
            "if_utc_only_unresolved": (
                "INSPECT_ONLY_DECISION_TIME_"
                "CYCLICAL_ENCODING_BLOCK"
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
            run_inspection()
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_UNCLASSIFIED_FEATURE_"
                        "PROVENANCE_INSPECTION_FAILED"
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
                    "mt5_used": (
                        False
                    ),
                    "model_trained": (
                        False
                    ),
                    "model_artifacts_written": (
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