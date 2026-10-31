from __future__ import annotations

import ast
import json
import sys
import tokenize
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]

ANALYSIS_VERSION = (
    "XAUUSD_FEATURE_PIPELINE_CONTRACT_INSPECTION_V1"
)

TARGET_FILES = (
    ROOT_DIR
    / "02_AI"
    / "Dataset"
    / "training_matrix_builder.py",
    ROOT_DIR
    / "02_AI"
    / "Dataset"
    / "training_feature_enricher.py",
    ROOT_DIR
    / "02_AI"
    / "Features"
    / "feature_list.py",
)

TARGET_METHODS = {
    "training_matrix_builder.py": {
        "TrainingMatrixBuilder": {
            "__init__",
            "_generate_feature_frame",
            "build",
        }
    },
    "training_feature_enricher.py": {
        "TrainingFeatureEnricher": {
            "__init__",
            "_domain_features",
            "enrich",
        }
    },
}

EXPECTED_FEATURES = (
    "m5_spread_points",
    "m5_tick_volume_log1p",
    "m5_tick_volume_ratio20",
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
        return str(
            path
        )


def _read_source(
    path: Path,
) -> str:

    with tokenize.open(
        path
    ) as handle:
        return handle.read()


def _argument_names(
    node: ast.FunctionDef
    | ast.AsyncFunctionDef,
) -> list[str]:

    names: list[str] = []

    for argument in (
        node.args.posonlyargs
        +
        node.args.args
    ):
        names.append(
            argument.arg
        )

    if node.args.vararg is not None:
        names.append(
            "*"
            +
            node.args.vararg.arg
        )

    for argument in (
        node.args.kwonlyargs
    ):
        names.append(
            argument.arg
        )

    if node.args.kwarg is not None:
        names.append(
            "**"
            +
            node.args.kwarg.arg
        )

    return names


def _literal_value(
    node: ast.AST,
) -> Any:

    try:
        return ast.literal_eval(
            node
        )

    except (
        ValueError,
        TypeError,
        SyntaxError,
    ):
        return None


def _call_name(
    node: ast.Call,
) -> str:

    func = node.func

    if isinstance(
        func,
        ast.Name,
    ):
        return func.id

    if isinstance(
        func,
        ast.Attribute,
    ):

        parts: list[str] = [
            func.attr
        ]

        value = func.value

        while isinstance(
            value,
            ast.Attribute,
        ):

            parts.append(
                value.attr
            )

            value = value.value

        if isinstance(
            value,
            ast.Name,
        ):
            parts.append(
                value.id
            )

        return ".".join(
            reversed(
                parts
            )
        )

    return ""


def _import_inventory(
    tree: ast.AST,
) -> dict[str, Any]:

    imports: list[
        dict[str, Any]
    ] = []

    dynamic_imports: list[
        dict[str, Any]
    ] = []

    for node in ast.walk(
        tree
    ):

        if isinstance(
            node,
            ast.Import,
        ):

            for alias in node.names:

                imports.append(
                    {
                        "type": (
                            "import"
                        ),
                        "module": (
                            alias.name
                        ),
                        "alias": (
                            alias.asname
                        ),
                        "line": (
                            node.lineno
                        ),
                    }
                )

        elif isinstance(
            node,
            ast.ImportFrom,
        ):

            imports.append(
                {
                    "type": (
                        "from"
                    ),
                    "module": (
                        node.module
                    ),
                    "names": [
                        {
                            "name": (
                                alias.name
                            ),
                            "alias": (
                                alias.asname
                            ),
                        }
                        for alias
                        in node.names
                    ],
                    "line": (
                        node.lineno
                    ),
                }
            )

        elif isinstance(
            node,
            ast.Call,
        ):

            call_name = (
                _call_name(
                    node
                )
            )

            if call_name in {
                "importlib.import_module",
                "import_module",
            }:

                module_name: Any = None

                if node.args:

                    module_name = (
                        _literal_value(
                            node.args[
                                0
                            ]
                        )
                    )

                dynamic_imports.append(
                    {
                        "module": (
                            module_name
                        ),
                        "line": (
                            node.lineno
                        ),
                    }
                )

    return {
        "static_imports": (
            imports
        ),
        "dynamic_imports": (
            dynamic_imports
        ),
    }


def _method_call_inventory(
    method: ast.FunctionDef
    | ast.AsyncFunctionDef,
) -> list[dict[str, Any]]:

    calls: list[
        dict[str, Any]
    ] = []

    for node in ast.walk(
        method
    ):

        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        call_name = (
            _call_name(
                node
            )
        )

        if not call_name:
            continue

        literal_args: list[
            Any
        ] = []

        for argument in node.args:

            literal = (
                _literal_value(
                    argument
                )
            )

            if isinstance(
                literal,
                (
                    str,
                    int,
                    float,
                    bool,
                    type(
                        None
                    ),
                ),
            ):

                literal_args.append(
                    literal
                )

            else:

                literal_args.append(
                    None
                )

        calls.append(
            {
                "call": (
                    call_name
                ),
                "line": (
                    node.lineno
                ),
                "literal_args": (
                    literal_args
                ),
            }
        )

    calls.sort(
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

    return calls


def _attribute_assignments(
    method: ast.FunctionDef
    | ast.AsyncFunctionDef,
) -> list[dict[str, Any]]:

    assignments: list[
        dict[str, Any]
    ] = []

    for node in ast.walk(
        method
    ):

        if not isinstance(
            node,
            (
                ast.Assign,
                ast.AnnAssign,
            ),
        ):
            continue

        if isinstance(
            node,
            ast.Assign,
        ):

            targets = (
                node.targets
            )

            value_node = (
                node.value
            )

        else:

            targets = [
                node.target
            ]

            value_node = (
                node.value
            )

        if value_node is None:
            continue

        for target in targets:

            if not isinstance(
                target,
                ast.Attribute,
            ):
                continue

            if not isinstance(
                target.value,
                ast.Name,
            ):
                continue

            if (
                target.value.id
                !=
                "self"
            ):
                continue

            assignments.append(
                {
                    "attribute": (
                        target.attr
                    ),
                    "line": (
                        node.lineno
                    ),
                    "literal_value": (
                        _literal_value(
                            value_node
                        )
                    ),
                }
            )

    assignments.sort(
        key=lambda item: int(
            item[
                "line"
            ]
        )
    )

    return assignments


def _return_inventory(
    method: ast.FunctionDef
    | ast.AsyncFunctionDef,
) -> list[dict[str, Any]]:

    returns: list[
        dict[str, Any]
    ] = []

    for node in ast.walk(
        method
    ):

        if not isinstance(
            node,
            ast.Return,
        ):
            continue

        value_type = (
            type(
                node.value
            ).__name__
            if node.value
            is not None
            else
            None
        )

        returns.append(
            {
                "line": (
                    node.lineno
                ),
                "value_ast_type": (
                    value_type
                ),
            }
        )

    return sorted(
        returns,
        key=lambda item: int(
            item[
                "line"
            ]
        ),
    )


def _string_constants(
    node: ast.AST,
) -> list[dict[str, Any]]:

    results: list[
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

        interesting = bool(
            "XAUUSD"
            in value
            or
            "FEATURE"
            in value.upper()
            or
            "TRAINING"
            in value.upper()
            or
            value
            in EXPECTED_FEATURES
        )

        if not interesting:
            continue

        key = (
            int(
                getattr(
                    child,
                    "lineno",
                    0,
                )
            ),
            value,
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        results.append(
            {
                "line": (
                    key[
                        0
                    ]
                ),
                "value": (
                    value
                ),
            }
        )

    return sorted(
        results,
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
        ),
    )


def _class_method_document(
    class_node: ast.ClassDef,
    wanted_methods: set[str],
) -> dict[str, Any]:

    methods: dict[
        str,
        Any
    ] = {}

    for node in (
        class_node.body
    ):

        if not isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            continue

        if (
            node.name
            not in wanted_methods
        ):
            continue

        methods[
            node.name
        ] = {
            "line_start": (
                node.lineno
            ),
            "line_end": (
                getattr(
                    node,
                    "end_lineno",
                    None,
                )
            ),
            "arguments": (
                _argument_names(
                    node
                )
            ),
            "calls": (
                _method_call_inventory(
                    node
                )
            ),
            "self_attribute_assignments": (
                _attribute_assignments(
                    node
                )
            ),
            "returns": (
                _return_inventory(
                    node
                )
            ),
            "interesting_strings": (
                _string_constants(
                    node
                )
            ),
        }

    return methods


def _inspect_python_file(
    path: Path,
) -> dict[str, Any]:

    if not path.exists():

        return {
            "path": (
                _relative(
                    path
                )
            ),
            "exists": False,
        }

    source = (
        _read_source(
            path
        )
    )

    tree = ast.parse(
        source,
        filename=str(
            path
        ),
    )

    file_name = (
        path.name
    )

    wanted_classes = (
        TARGET_METHODS.get(
            file_name,
            {},
        )
    )

    classes: dict[
        str,
        Any
    ] = {}

    for node in (
        tree.body
    ):

        if not isinstance(
            node,
            ast.ClassDef,
        ):
            continue

        if (
            node.name
            not in wanted_classes
        ):
            continue

        classes[
            node.name
        ] = {
            "line_start": (
                node.lineno
            ),
            "line_end": (
                getattr(
                    node,
                    "end_lineno",
                    None,
                )
            ),
            "methods": (
                _class_method_document(
                    node,
                    wanted_classes[
                        node.name
                    ],
                )
            ),
        }

    source_lines = (
        source.splitlines()
    )

    feature_occurrences: dict[
        str,
        list[int],
    ] = {}

    for feature in (
        EXPECTED_FEATURES
    ):

        lines = [
            index
            for index, line
            in enumerate(
                source_lines,
                start=1,
            )
            if feature
            in line
        ]

        if lines:

            feature_occurrences[
                feature
            ] = (
                lines
            )

    return {
        "path": (
            _relative(
                path
            )
        ),
        "exists": True,
        "line_count": (
            len(
                source_lines
            )
        ),
        "imports": (
            _import_inventory(
                tree
            )
        ),
        "classes": (
            classes
        ),
        "expected_feature_occurrences": (
            feature_occurrences
        ),
        "interesting_strings": (
            _string_constants(
                tree
            )
        ),
    }


def _feature_list_document(
    path: Path,
) -> dict[str, Any]:

    if not path.exists():

        return {
            "path": (
                _relative(
                    path
                )
            ),
            "exists": False,
        }

    source = (
        _read_source(
            path
        )
    )

    tree = ast.parse(
        source,
        filename=str(
            path
        ),
    )

    assignments: list[
        dict[str, Any]
    ] = []

    for node in (
        tree.body
    ):

        if not isinstance(
            node,
            (
                ast.Assign,
                ast.AnnAssign,
            ),
        ):
            continue

        if isinstance(
            node,
            ast.Assign,
        ):

            targets = (
                node.targets
            )

            value_node = (
                node.value
            )

        else:

            targets = [
                node.target
            ]

            value_node = (
                node.value
            )

        if value_node is None:
            continue

        literal = (
            _literal_value(
                value_node
            )
        )

        if not isinstance(
            literal,
            (
                list,
                tuple,
            ),
        ):
            continue

        if not all(
            isinstance(
                value,
                str,
            )
            for value
            in literal
        ):
            continue

        names: list[str] = []

        for target in targets:

            if isinstance(
                target,
                ast.Name,
            ):
                names.append(
                    target.id
                )

        if not names:
            continue

        assignments.append(
            {
                "names": (
                    names
                ),
                "line": (
                    node.lineno
                ),
                "count": (
                    len(
                        literal
                    )
                ),
                "contains_expected_broker_sensitive_features": {
                    feature: (
                        feature
                        in literal
                    )
                    for feature
                    in EXPECTED_FEATURES
                },
                "first_10": list(
                    literal[
                        :10
                    ]
                ),
                "last_10": list(
                    literal[
                        -10:
                    ]
                ),
            }
        )

    return {
        "path": (
            _relative(
                path
            )
        ),
        "exists": True,
        "assignments": (
            assignments
        ),
    }


def _decision(
    documents: list[
        dict[str, Any]
    ],
    feature_list: dict[str, Any],
) -> dict[str, Any]:

    matrix_document = next(
        (
            item
            for item
            in documents
            if item.get(
                "path",
                ""
            ).endswith(
                "training_matrix_builder.py"
            )
        ),
        None,
    )

    enricher_document = next(
        (
            item
            for item
            in documents
            if item.get(
                "path",
                ""
            ).endswith(
                "training_feature_enricher.py"
            )
        ),
        None,
    )

    matrix_method_found = False
    enricher_method_found = False

    if matrix_document:

        matrix_method_found = bool(
            matrix_document
            .get(
                "classes",
                {},
            )
            .get(
                "TrainingMatrixBuilder",
                {},
            )
            .get(
                "methods",
                {},
            )
            .get(
                "_generate_feature_frame"
            )
        )

    if enricher_document:

        enricher_method_found = bool(
            enricher_document
            .get(
                "classes",
                {},
            )
            .get(
                "TrainingFeatureEnricher",
                {},
            )
            .get(
                "methods",
                {},
            )
            .get(
                "enrich"
            )
        )

    feature_list_exists = bool(
        feature_list.get(
            "exists",
            False,
        )
    )

    ready = bool(
        matrix_method_found
        and
        enricher_method_found
        and
        feature_list_exists
    )

    return {
        "training_matrix_generate_feature_frame_found": (
            matrix_method_found
        ),
        "training_feature_enricher_enrich_found": (
            enricher_method_found
        ),
        "feature_list_source_found": (
            feature_list_exists
        ),
        "ready_for_exact_domain_shift_runner": (
            ready
        ),
        "next_gate": (
            "BUILD_CURRENT_BROKER_TRAIN_ONLY_DOMAIN_SHIFT_AUDIT"
            if ready
            else
            "REVIEW_MISSING_PIPELINE_COMPONENT"
        ),
    }


def run_inspection(
) -> dict[str, Any]:

    documents = [
        _inspect_python_file(
            path
        )
        for path
        in TARGET_FILES[
            :2
        ]
    ]

    feature_list = (
        _feature_list_document(
            TARGET_FILES[
                2
            ]
        )
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_FEATURE_PIPELINE_CONTRACT_INSPECTION"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "inspection_policy": {
            "local_source_read": True,
            "ast_only": True,
            "project_modules_imported": False,
            "project_code_executed": False,
            "mt5_used": False,
            "dataset_loaded": False,
            "train_loaded": False,
            "validation_loaded": False,
            "test_loaded": False,
            "model_loaded": False,
            "model_artifacts_written": False,
            "orders_sent": False,
            "live_authorized": False,
        },
        "pipeline_documents": (
            documents
        ),
        "feature_list_document": (
            feature_list
        ),
        "decision": (
            _decision(
                documents,
                feature_list,
            )
        ),
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
                        "XAUUSD_FEATURE_PIPELINE_"
                        "CONTRACT_INSPECTION_FAILED"
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
                    "project_code_executed": False,
                    "mt5_used": False,
                    "test_loaded": False,
                    "orders_sent": False,
                    "live_authorized": False,
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