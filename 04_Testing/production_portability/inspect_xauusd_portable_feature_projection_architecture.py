from __future__ import annotations

import ast
import json
import sys
import tokenize
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[2]


ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_FEATURE_PROJECTION_ARCHITECTURE_INSPECTION_V1"
)

PORTABLE_CONTRACT_VERSION = (
    "XAUUSD_MTF_PORTABLE_FEATURE_V1"
)

PARENT_CONTRACT_VERSION = (
    "XAUUSD_MTF_TRAINING_V3"
)

EXPECTED_PARENT_FEATURE_COUNT = 333

EXPECTED_PORTABLE_FEATURE_COUNT = 331

EXPECTED_DROPPED_FEATURES = (
    "m5_spread_points",
    "m5_tick_volume_log1p",
)

EXPECTED_RETAINED_FEATURE = (
    "m5_tick_volume_ratio20"
)


SOURCE_FILES = {
    "training_feature_enricher": (
        ROOT_DIR
        /
        "02_AI"
        /
        "Dataset"
        /
        "training_feature_enricher.py"
    ),
    "training_matrix_builder": (
        ROOT_DIR
        /
        "02_AI"
        /
        "Dataset"
        /
        "training_matrix_builder.py"
    ),
    "training_target_relabeler": (
        ROOT_DIR
        /
        "02_AI"
        /
        "Dataset"
        /
        "training_target_relabeler.py"
    ),
    "hierarchical_v4_trainer": (
        ROOT_DIR
        /
        "02_AI"
        /
        "Models"
        /
        "xauusd_hierarchical_model_v4_trainer.py"
    ),
}


INTERESTING_CLASSES = {
    "training_feature_enricher": (
        "TrainingFeatureEnricher",
        "TrainingFeatureEnrichmentResult",
        "TrainingFeatureEnrichmentError",
    ),
    "training_matrix_builder": (
        "TrainingMatrixBuilder",
        "TrainingMatrixResult",
        "TrainingMatrixError",
    ),
    "training_target_relabeler": (
        "TrainingTargetRelabeler",
        "TrainingTargetRelabelResult",
        "TrainingTargetRelabelError",
    ),
    "hierarchical_v4_trainer": (
        "XAUUSDHierarchicalModelV4Trainer",
    ),
}


INTERESTING_METHODS = {
    "TrainingFeatureEnricher": (
        "__init__",
        "_discover_v2",
        "_validate_context",
        "_write_dataframe",
        "_write_immutable",
        "enrich",
    ),
    "TrainingMatrixBuilder": (
        "__init__",
        "_generate_feature_frame",
        "build",
    ),
    "TrainingTargetRelabeler": (
        "__init__",
        "_discover_source",
        "_validate_context",
        "_write_dataframe",
        "_write_immutable",
        "relabel",
    ),
    "XAUUSDHierarchicalModelV4Trainer": (
        "__init__",
        "train",
    ),
}


INTERESTING_STRINGS = (
    "XAUUSD_MTF_TRAINING_V2",
    "XAUUSD_MTF_TRAINING_V3",
    "XAUUSD_MTF_PORTABLE_FEATURE_V1",
    "PULSEVIPER_TRAINING_MATRIX_MANIFEST_V1",
    "PULSEVIPER_TRAINING_MATRIX_MANIFEST_V3",
    "feature_columns",
    "feature_count",
    "training_contract_version",
    "source_training_matrix",
    "dataset_id",
    "dataset_sha256",
    "manifest_sha256",
    "target_contract",
    "target_contract_version",
    "target_tradeable",
    "split",
    "decision_time",
    "live_authorized",
)


REQUIRED_ENRICHER_EVIDENCE = (
    "feature_columns",
    "feature_count",
    "training_contract_version",
    "source_training_matrix",
)


def _require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise RuntimeError(
            reason
        )


def _relative(
    path: Path,
) -> str:

    try:
        return str(
            path.relative_to(
                ROOT_DIR
            )
        )

    except ValueError:
        return path.name


def _read_python_source(
    path: Path,
) -> str:

    _require(
        path.is_file(),
        (
            "SOURCE_FILE_NOT_FOUND:"
            f"{_relative(path)}"
        ),
    )

    with tokenize.open(
        str(
            path
        )
    ) as handle:
        return handle.read()


def _argument_names(
    node: (
        ast.FunctionDef
        |
        ast.AsyncFunctionDef
    ),
) -> list[str]:

    arguments: list[str] = []

    for argument in (
        node.args.posonlyargs
    ):
        arguments.append(
            argument.arg
        )

    for argument in (
        node.args.args
    ):
        arguments.append(
            argument.arg
        )

    if (
        node.args.vararg
        is not None
    ):
        arguments.append(
            "*"
            +
            node.args.vararg.arg
        )

    for argument in (
        node.args.kwonlyargs
    ):
        arguments.append(
            argument.arg
        )

    if (
        node.args.kwarg
        is not None
    ):
        arguments.append(
            "**"
            +
            node.args.kwarg.arg
        )

    return arguments


def _call_name(
    node: ast.Call,
) -> str:

    function = node.func

    if isinstance(
        function,
        ast.Name,
    ):
        return function.id

    if isinstance(
        function,
        ast.Attribute,
    ):

        parts: list[str] = [
            function.attr
        ]

        current = (
            function.value
        )

        while isinstance(
            current,
            ast.Attribute,
        ):

            parts.append(
                current.attr
            )

            current = (
                current.value
            )

        if isinstance(
            current,
            ast.Name,
        ):
            parts.append(
                current.id
            )

        parts.reverse()

        return ".".join(
            parts
        )

    return (
        type(
            function
        ).__name__
    )


def _method_calls(
    node: (
        ast.FunctionDef
        |
        ast.AsyncFunctionDef
    ),
) -> list[dict[str, Any]]:

    documents: list[
        dict[str, Any]
    ] = []

    for child in ast.walk(
        node
    ):

        if not isinstance(
            child,
            ast.Call,
        ):
            continue

        documents.append(
            {
                "line": int(
                    getattr(
                        child,
                        "lineno",
                        0,
                    )
                ),
                "call": (
                    _call_name(
                        child
                    )
                ),
            }
        )

    documents.sort(
        key=lambda item: (
            int(
                item[
                    "line"
                ]
            ),
            str(
                item[
                    "call"
                ]
            ),
        )
    )

    return documents


def _string_literals(
    node: ast.AST,
) -> list[
    dict[str, Any]
]:

    documents: list[
        dict[str, Any]
    ] = []

    for child in ast.walk(
        node
    ):

        if not isinstance(
            child,
            ast.Constant,
        ):
            continue

        if not isinstance(
            child.value,
            str,
        ):
            continue

        value = (
            child.value
        )

        if not any(
            token
            in
            value
            for token
            in INTERESTING_STRINGS
        ):
            continue

        documents.append(
            {
                "line": int(
                    getattr(
                        child,
                        "lineno",
                        0,
                    )
                ),
                "value": (
                    value
                ),
            }
        )

    documents.sort(
        key=lambda item: (
            int(
                item[
                    "line"
                ]
            ),
            str(
                item[
                    "value"
                ]
            ),
        )
    )

    return documents


def _dict_literal_keys(
    node: ast.AST,
) -> list[
    dict[str, Any]
]:

    documents: list[
        dict[str, Any]
    ] = []

    seen: set[
        tuple[
            int,
            str,
        ]
    ] = set()

    for child in ast.walk(
        node
    ):

        if not isinstance(
            child,
            ast.Dict,
        ):
            continue

        for key_node in (
            child.keys
        ):

            if not isinstance(
                key_node,
                ast.Constant,
            ):
                continue

            if not isinstance(
                key_node.value,
                str,
            ):
                continue

            key = str(
                key_node.value
            )

            identity = (
                int(
                    getattr(
                        key_node,
                        "lineno",
                        0,
                    )
                ),
                key,
            )

            if (
                identity
                in
                seen
            ):
                continue

            seen.add(
                identity
            )

            documents.append(
                {
                    "line": (
                        identity[
                            0
                        ]
                    ),
                    "key": (
                        key
                    ),
                }
            )

    documents.sort(
        key=lambda item: (
            int(
                item[
                    "line"
                ]
            ),
            str(
                item[
                    "key"
                ]
            ),
        )
    )

    return documents


def _class_fields(
    node: ast.ClassDef,
) -> list[str]:

    fields: list[str] = []

    for child in (
        node.body
    ):

        if isinstance(
            child,
            ast.AnnAssign,
        ):

            if isinstance(
                child.target,
                ast.Name,
            ):
                fields.append(
                    child.target.id
                )

        elif isinstance(
            child,
            ast.Assign,
        ):

            for target in (
                child.targets
            ):

                if isinstance(
                    target,
                    ast.Name,
                ):
                    fields.append(
                        target.id
                    )

    return fields


def _method_document(
    node: (
        ast.FunctionDef
        |
        ast.AsyncFunctionDef
    ),
) -> dict[str, Any]:

    return {
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
        "arguments": (
            _argument_names(
                node
            )
        ),
        "calls": (
            _method_calls(
                node
            )
        ),
        "interesting_strings": (
            _string_literals(
                node
            )
        ),
        "dict_literal_keys": (
            _dict_literal_keys(
                node
            )
        ),
    }


def _class_document(
    node: ast.ClassDef,
) -> dict[str, Any]:

    selected_methods = set(
        INTERESTING_METHODS.get(
            node.name,
            (),
        )
    )

    methods: dict[
        str,
        Any
    ] = {}

    for child in (
        node.body
    ):

        if not isinstance(
            child,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            continue

        if (
            child.name
            not in
            selected_methods
        ):
            continue

        methods[
            child.name
        ] = (
            _method_document(
                child
            )
        )

    return {
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
        "fields": (
            _class_fields(
                node
            )
        ),
        "methods": (
            methods
        ),
    }


def _source_document(
    *,
    logical_name: str,
    path: Path,
) -> dict[str, Any]:

    source = (
        _read_python_source(
            path
        )
    )

    try:
        tree = ast.parse(
            source,
            filename=(
                str(
                    path
                )
            ),
        )

    except SyntaxError as exc:
        raise RuntimeError(
            (
                "SOURCE_AST_PARSE_FAILED:"
                f"{_relative(path)}:"
                f"{exc}"
            )
        ) from exc

    expected_classes = set(
        INTERESTING_CLASSES.get(
            logical_name,
            (),
        )
    )

    classes: dict[
        str,
        Any
    ] = {}

    for child in (
        tree.body
    ):

        if not isinstance(
            child,
            ast.ClassDef,
        ):
            continue

        if (
            child.name
            not in
            expected_classes
        ):
            continue

        classes[
            child.name
        ] = (
            _class_document(
                child
            )
        )

    return {
        "path": (
            _relative(
                path
            )
        ),
        "line_count": int(
            len(
                source.splitlines()
            )
        ),
        "ast_parse_ok": (
            True
        ),
        "classes": (
            classes
        ),
        "module_interesting_strings": (
            _string_literals(
                tree
            )
        ),
    }


def _method(
    source_document: Mapping[
        str,
        Any,
    ],
    *,
    class_name: str,
    method_name: str,
) -> Mapping[
    str,
    Any
]:

    classes = (
        source_document.get(
            "classes"
        )
    )

    if not isinstance(
        classes,
        Mapping,
    ):
        raise RuntimeError(
            (
                "SOURCE_CLASSES_MISSING:"
                f"{class_name}"
            )
        )

    class_document = (
        classes.get(
            class_name
        )
    )

    if not isinstance(
        class_document,
        Mapping,
    ):
        raise RuntimeError(
            (
                "EXPECTED_CLASS_MISSING:"
                f"{class_name}"
            )
        )

    methods = (
        class_document.get(
            "methods"
        )
    )

    if not isinstance(
        methods,
        Mapping,
    ):
        raise RuntimeError(
            (
                "CLASS_METHODS_MISSING:"
                f"{class_name}"
            )
        )

    method_document = (
        methods.get(
            method_name
        )
    )

    if not isinstance(
        method_document,
        Mapping,
    ):
        raise RuntimeError(
            (
                "EXPECTED_METHOD_MISSING:"
                f"{class_name}."
                f"{method_name}"
            )
        )

    return (
        method_document
    )


def _method_dict_keys(
    method_document: Mapping[
        str,
        Any,
    ],
) -> set[str]:

    raw_keys = (
        method_document.get(
            "dict_literal_keys"
        )
    )

    if not isinstance(
        raw_keys,
        list,
    ):
        return set()

    result: set[str] = set()

    for item in (
        raw_keys
    ):

        if not isinstance(
            item,
            Mapping,
        ):
            continue

        key = str(
            item.get(
                "key",
                "",
            )
        )

        if key:
            result.add(
                key
            )

    return (
        result
    )


def _method_call_names(
    method_document: Mapping[
        str,
        Any,
    ],
) -> set[str]:

    raw_calls = (
        method_document.get(
            "calls"
        )
    )

    if not isinstance(
        raw_calls,
        list,
    ):
        return set()

    result: set[str] = set()

    for item in (
        raw_calls
    ):

        if not isinstance(
            item,
            Mapping,
        ):
            continue

        call = str(
            item.get(
                "call",
                "",
            )
        )

        if call:
            result.add(
                call
            )

    return result


def _contains_module_string(
    source_document: Mapping[
        str,
        Any,
    ],
    token: str,
) -> bool:

    raw_strings = (
        source_document.get(
            "module_interesting_strings"
        )
    )

    if not isinstance(
        raw_strings,
        list,
    ):
        return False

    for item in raw_strings:

        if not isinstance(
            item,
            Mapping,
        ):
            continue

        value = str(
            item.get(
                "value",
                "",
            )
        )

        if (
            token
            in
            value
        ):
            return True

    return False


def _decision(
    documents: Mapping[
        str,
        Mapping[
            str,
            Any,
        ],
    ],
) -> dict[str, Any]:

    enricher = (
        documents[
            "training_feature_enricher"
        ]
    )

    enricher_method = (
        _method(
            enricher,
            class_name=(
                "TrainingFeatureEnricher"
            ),
            method_name=(
                "enrich"
            ),
        )
    )

    enricher_keys = (
        _method_dict_keys(
            enricher_method
        )
    )

    enricher_calls = (
        _method_call_names(
            enricher_method
        )
    )

    missing_manifest_keys = sorted(
        set(
            REQUIRED_ENRICHER_EVIDENCE
        )
        -
        enricher_keys
    )

    parent_contract_found = (
        _contains_module_string(
            enricher,
            PARENT_CONTRACT_VERSION,
        )
    )

    immutable_write_evidence = bool(
        any(
            (
                "_write_immutable"
                in
                call
            )
            or
            (
                "_write_dataframe"
                in
                call
            )
            for call
            in enricher_calls
        )
    )

    target_relabeler = (
        documents.get(
            "training_target_relabeler"
        )
    )

    relabeler_present = bool(
        isinstance(
            target_relabeler,
            Mapping,
        )
        and
        bool(
            target_relabeler.get(
                "classes"
            )
        )
    )

    if (
        parent_contract_found
        and
        not missing_manifest_keys
        and
        immutable_write_evidence
    ):

        status = (
            "NEW_DOWNSTREAM_IMMUTABLE_PROJECTOR_ARCHITECTURE_CONFIRMED"
        )

        reason = (
            "FROZEN_V3_ENRICHER_ALREADY_OWNS_THE_PARENT_"
            "ARTIFACT_AND_MANIFEST_CONTRACT_SO_PORTABLE_V1_"
            "SHOULD_BE_A_SEPARATE_POST_V3_PROJECTION_STAGE"
        )

        next_action = (
            "IMPLEMENT_NEW_PORTABLE_TRAINING_FEATURE_PROJECTOR_"
            "WITHOUT_MODIFYING_V3_ENRICHER_OR_MATRIX_BUILDER"
        )

        implementation_authorized = (
            True
        )

    else:

        status = (
            "PORTABLE_PROJECTOR_ARCHITECTURE_NOT_CONFIRMED"
        )

        reason = (
            "LOCAL_SOURCE_INSPECTION_DID_NOT_CONFIRM_ALL_"
            "REQUIRED_PARENT_ARTIFACT_AND_MANIFEST_INSERTION_POINTS"
        )

        next_action = (
            "RESOLVE_ONLY_MISSING_LOCAL_PIPELINE_ARCHITECTURE_EVIDENCE"
        )

        implementation_authorized = (
            False
        )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "parent_contract_found_in_enricher": (
            parent_contract_found
        ),
        "required_enricher_manifest_keys": list(
            REQUIRED_ENRICHER_EVIDENCE
        ),
        "missing_enricher_manifest_keys": (
            missing_manifest_keys
        ),
        "immutable_write_evidence_found": (
            immutable_write_evidence
        ),
        "training_target_relabeler_present": (
            relabeler_present
        ),
        "recommended_new_module": (
            "02_AI\\Dataset\\portable_training_feature_projector.py"
        ),
        "recommended_new_class": (
            "PortableTrainingFeatureProjector"
        ),
        "recommended_source_contract": (
            PARENT_CONTRACT_VERSION
        ),
        "recommended_output_contract": (
            PORTABLE_CONTRACT_VERSION
        ),
        "recommended_parent_feature_count": (
            EXPECTED_PARENT_FEATURE_COUNT
        ),
        "recommended_output_feature_count": (
            EXPECTED_PORTABLE_FEATURE_COUNT
        ),
        "recommended_dropped_features": list(
            EXPECTED_DROPPED_FEATURES
        ),
        "recommended_retained_feature": (
            EXPECTED_RETAINED_FEATURE
        ),
        "modify_training_feature_enricher": (
            False
        ),
        "modify_training_matrix_builder": (
            False
        ),
        "modify_training_target_relabeler": (
            False
        ),
        "modify_existing_model_trainer": (
            False
        ),
        "research_projector_implementation_authorized": (
            implementation_authorized
        ),
        "dataset_rebuild_authorized": (
            False
        ),
        "model_retraining_authorized": (
            False
        ),
        "validation_evaluation_authorized": (
            False
        ),
        "test_evaluation_authorized": (
            False
        ),
        "target_contract_change_authorized": (
            False
        ),
        "live_authorized": (
            False
        ),
        "next_action": (
            next_action
        ),
    }


def run_inspection(
) -> dict[str, Any]:

    documents: dict[
        str,
        Mapping[
            str,
            Any,
        ],
    ] = {}

    for (
        logical_name,
        path,
    ) in SOURCE_FILES.items():

        if (
            not path.is_file()
            and
            logical_name
            in (
                "training_target_relabeler",
                "hierarchical_v4_trainer",
            )
        ):

            documents[
                logical_name
            ] = {
                "path": (
                    _relative(
                        path
                    )
                ),
                "exists": (
                    False
                ),
                "optional_source": (
                    True
                ),
            }

            continue

        documents[
            logical_name
        ] = (
            _source_document(
                logical_name=(
                    logical_name
                ),
                path=(
                    path
                ),
            )
        )

    decision = (
        _decision(
            documents
        )
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_PORTABLE_FEATURE_PROJECTION_"
            "ARCHITECTURE_INSPECTION"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "research_scope": (
            "AST_ONLY_LOCAL_SOURCE_INSPECTION_FOR_PORTABLE_"
            "331_FEATURE_DATASET_PROJECTION_INSERTION_POINTS"
        ),
        "portable_contract": {
            "version": (
                PORTABLE_CONTRACT_VERSION
            ),
            "parent_contract": (
                PARENT_CONTRACT_VERSION
            ),
            "parent_feature_count": (
                EXPECTED_PARENT_FEATURE_COUNT
            ),
            "portable_feature_count": (
                EXPECTED_PORTABLE_FEATURE_COUNT
            ),
            "dropped_features": list(
                EXPECTED_DROPPED_FEATURES
            ),
            "added_features": [],
            "retained_relative_volume_feature": (
                EXPECTED_RETAINED_FEATURE
            ),
        },
        "source_documents": (
            documents
        ),
        "decision": (
            decision
        ),
        "scientific_policy": {
            "local_source_read": (
                True
            ),
            "ast_only": (
                True
            ),
            "project_modules_imported": (
                False
            ),
            "project_code_executed": (
                False
            ),
            "dataset_loaded": (
                False
            ),
            "new_market_data_loaded": (
                False
            ),
            "mt5_used": (
                False
            ),
            "labels_loaded": (
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
            "model_loaded": (
                False
            ),
            "model_trained": (
                False
            ),
            "model_artifacts_written": (
                False
            ),
            "feature_pipeline_modified": (
                False
            ),
            "frozen_v3_contract_mutated": (
                False
            ),
            "target_contract_changed": (
                False
            ),
            "execution_integration_modified": (
                False
            ),
            "risk_engine_modified": (
                False
            ),
            "sizing_modified": (
                False
            ),
            "orders_sent": (
                False
            ),
            "positions_modified": (
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
            "if_projector_architecture_confirmed": (
                "IMPLEMENT_NEW_PORTABLE_TRAINING_FEATURE_PROJECTOR_"
                "AS_A_SEPARATE_POST_V3_RESEARCH_STAGE"
            ),
            "existing_v3_enricher_must_remain_unchanged": (
                True
            ),
            "existing_training_matrix_builder_must_remain_unchanged": (
                True
            ),
            "portable_dataset_not_built_yet": (
                True
            ),
            "model_retraining_not_authorized": (
                True
            ),
            "test_holdout_remains_untouched": (
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
                        "XAUUSD_PORTABLE_FEATURE_PROJECTION_"
                        "ARCHITECTURE_INSPECTION_FAILED"
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
                    "project_modules_imported": (
                        False
                    ),
                    "dataset_loaded": (
                        False
                    ),
                    "mt5_used": (
                        False
                    ),
                    "validation_loaded": (
                        False
                    ),
                    "test_loaded": (
                        False
                    ),
                    "model_loaded": (
                        False
                    ),
                    "model_trained": (
                        False
                    ),
                    "feature_pipeline_modified": (
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