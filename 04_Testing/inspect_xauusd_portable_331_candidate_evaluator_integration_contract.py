#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_CANDIDATE_"
    "EVALUATOR_INTEGRATION_CONTRACT_INSPECTION_V1"
)

REPO_ROOT = Path(__file__).resolve().parents[1]

LOADER_PATH = (
    REPO_ROOT
    / "02_AI"
    / "Dataset"
    / "portable_331_training_input_loader.py"
)

EVALUATOR_PATH = (
    REPO_ROOT
    / "04_Testing"
    / "evaluate_xauusd_portable_331_train_model_candidates.py"
)

PROTOCOL_JSON_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_train_model_research_protocol_design.json"
)

REGISTRY_JSON_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_train_model_candidate_registry_design.json"
)

SUPERVISED_BATCH_JSON_PATH = (
    REPO_ROOT
    / "xauusd_portable_331_train_supervised_batch_integration.json"
)

EXPECTED_REGISTRY_FINGERPRINT = (
    "b8088bb34ce8940f7de5946fbb9b0fd20f40d7cc93a76b76fd7975591f00066c"
)

RELEVANT_KEY_TOKENS = (
    "train",
    "validation",
    "test",
    "fold",
    "purge",
    "feature",
    "target",
    "batch",
    "dataset",
    "manifest",
    "fingerprint",
    "row_count",
    "shape",
    "split",
    "loader",
    "supervised",
)

IDENTITY_KEYS = {
    "dataset_id",
    "dataset_sha256",
    "feature_count",
    "manifest_sha256",
    "row_count",
    "train_input_fingerprint_sha256",
    "train_target_fingerprint_sha256",
    "fingerprint_sha256",
    "candidate_registry_fingerprint_sha256",
    "purge_rows",
    "walk_forward_fold_count",
}


class InspectionError(
    RuntimeError
):
    pass


def _sha256_bytes(
    value: bytes,
) -> str:
    return hashlib.sha256(
        value
    ).hexdigest()


def _read_text_auto(
    path: Path,
) -> tuple[
    str,
    str,
]:
    raw = path.read_bytes()

    if raw.startswith(
        b"\xff\xfe"
    ):
        return (
            raw.decode(
                "utf-16"
            ),
            "utf-16",
        )

    if raw.startswith(
        b"\xfe\xff"
    ):
        return (
            raw.decode(
                "utf-16"
            ),
            "utf-16",
        )

    if raw.startswith(
        b"\xef\xbb\xbf"
    ):
        return (
            raw.decode(
                "utf-8-sig"
            ),
            "utf-8-sig",
        )

    try:
        return (
            raw.decode(
                "utf-8"
            ),
            "utf-8",
        )

    except UnicodeDecodeError as exc:
        raise InspectionError(
            f"Unsupported text encoding: {path}"
        ) from exc


def _load_json_auto(
    path: Path,
) -> tuple[
    Any,
    str,
    str,
]:
    text, encoding = (
        _read_text_auto(
            path
        )
    )

    try:
        payload = json.loads(
            text
        )

    except json.JSONDecodeError as exc:
        raise InspectionError(
            f"Invalid JSON: {path}: {exc}"
        ) from exc

    return (
        payload,
        encoding,
        _sha256_bytes(
            path.read_bytes()
        ),
    )


def _node_name(
    node: ast.AST,
) -> str:
    try:
        return ast.unparse(
            node
        )

    except Exception:
        return node.__class__.__name__


def _format_function_signature(
    node: (
        ast.FunctionDef
        | ast.AsyncFunctionDef
    ),
) -> str:
    args = node.args

    parts: list[
        str
    ] = []

    positional = (
        list(
            args.posonlyargs
        )
        + list(
            args.args
        )
    )

    positional_default_count = len(
        args.defaults
    )

    default_start = (
        len(
            positional
        )
        - positional_default_count
    )

    for index, argument in enumerate(
        positional
    ):
        text = argument.arg

        if (
            argument.annotation
            is not None
        ):
            text += (
                ": "
                + _node_name(
                    argument.annotation
                )
            )

        if (
            index
            >= default_start
        ):
            default_node = args.defaults[
                index
                - default_start
            ]

            text += (
                " = "
                + _node_name(
                    default_node
                )
            )

        parts.append(
            text
        )

    if args.vararg is not None:
        vararg_text = (
            "*"
            + args.vararg.arg
        )

        if (
            args.vararg.annotation
            is not None
        ):
            vararg_text += (
                ": "
                + _node_name(
                    args.vararg.annotation
                )
            )

        parts.append(
            vararg_text
        )

    elif args.kwonlyargs:
        parts.append(
            "*"
        )

    for argument, default_node in zip(
        args.kwonlyargs,
        args.kw_defaults,
    ):
        text = argument.arg

        if (
            argument.annotation
            is not None
        ):
            text += (
                ": "
                + _node_name(
                    argument.annotation
                )
            )

        if (
            default_node
            is not None
        ):
            text += (
                " = "
                + _node_name(
                    default_node
                )
            )

        parts.append(
            text
        )

    if args.kwarg is not None:
        kwarg_text = (
            "**"
            + args.kwarg.arg
        )

        if (
            args.kwarg.annotation
            is not None
        ):
            kwarg_text += (
                ": "
                + _node_name(
                    args.kwarg.annotation
                )
            )

        parts.append(
            kwarg_text
        )

    signature = (
        f"{node.name}("
        + ", ".join(
            parts
        )
        + ")"
    )

    if (
        node.returns
        is not None
    ):
        signature += (
            " -> "
            + _node_name(
                node.returns
            )
        )

    return signature


def _inspect_python_source(
    path: Path,
) -> dict[
    str,
    Any,
]:
    text, encoding = (
        _read_text_auto(
            path
        )
    )

    try:
        tree = ast.parse(
            text,
            filename=str(
                path
            ),
        )

    except SyntaxError as exc:
        raise InspectionError(
            f"Cannot parse Python source "
            f"{path}: {exc}"
        ) from exc

    functions: list[
        dict[
            str,
            Any,
        ]
    ] = []

    classes: list[
        dict[
            str,
            Any,
        ]
    ] = []

    imports: list[
        str
    ] = []

    constants: dict[
        str,
        Any,
    ] = {}

    for node in tree.body:
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            functions.append(
                {
                    "name": (
                        node.name
                    ),
                    "line": (
                        node.lineno
                    ),
                    "signature": (
                        _format_function_signature(
                            node
                        )
                    ),
                    "public": (
                        not node.name.startswith(
                            "_"
                        )
                    ),
                }
            )

        elif isinstance(
            node,
            ast.ClassDef,
        ):
            methods: list[
                dict[
                    str,
                    Any,
                ]
            ] = []

            annotated_fields: list[
                dict[
                    str,
                    Any,
                ]
            ] = []

            for child in node.body:
                if isinstance(
                    child,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                    ),
                ):
                    methods.append(
                        {
                            "name": (
                                child.name
                            ),
                            "line": (
                                child.lineno
                            ),
                            "signature": (
                                _format_function_signature(
                                    child
                                )
                            ),
                        }
                    )

                elif isinstance(
                    child,
                    ast.AnnAssign,
                ):
                    if isinstance(
                        child.target,
                        ast.Name,
                    ):
                        annotated_fields.append(
                            {
                                "name": (
                                    child.target.id
                                ),
                                "annotation": (
                                    _node_name(
                                        child.annotation
                                    )
                                ),
                            }
                        )

            classes.append(
                {
                    "name": (
                        node.name
                    ),
                    "line": (
                        node.lineno
                    ),
                    "bases": [
                        _node_name(
                            base
                        )
                        for base
                        in node.bases
                    ],
                    "annotated_fields": (
                        annotated_fields
                    ),
                    "methods": (
                        methods
                    ),
                }
            )

        elif isinstance(
            node,
            ast.Import,
        ):
            for alias in node.names:
                imports.append(
                    alias.name
                )

        elif isinstance(
            node,
            ast.ImportFrom,
        ):
            module = (
                node.module
                or ""
            )

            names = ",".join(
                alias.name
                for alias
                in node.names
            )

            imports.append(
                f"{module}:{names}"
            )

        elif isinstance(
            node,
            (
                ast.Assign,
                ast.AnnAssign,
            ),
        ):
            target_name = None
            value_node = None

            if isinstance(
                node,
                ast.Assign,
            ):
                if (
                    len(
                        node.targets
                    )
                    == 1
                    and isinstance(
                        node.targets[0],
                        ast.Name,
                    )
                ):
                    target_name = (
                        node.targets[
                            0
                        ].id
                    )

                value_node = (
                    node.value
                )

            else:
                if isinstance(
                    node.target,
                    ast.Name,
                ):
                    target_name = (
                        node.target.id
                    )

                value_node = (
                    node.value
                )

            if (
                target_name
                and target_name.isupper()
                and value_node
                is not None
            ):
                try:
                    value = ast.literal_eval(
                        value_node
                    )

                except Exception:
                    continue

                if isinstance(
                    value,
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
                    constants[
                        target_name
                    ] = value

                elif isinstance(
                    value,
                    (
                        tuple,
                        list,
                    ),
                ):
                    if (
                        len(
                            value
                        )
                        <= 50
                    ):
                        constants[
                            target_name
                        ] = value

    relevant_functions = [
        entry
        for entry
        in functions
        if (
            entry[
                "public"
            ]
            or any(
                token
                in entry[
                    "name"
                ].lower()
                for token
                in (
                    "load",
                    "train",
                    "batch",
                    "target",
                    "feature",
                    "fold",
                    "evaluate",
                )
            )
        )
    ]

    return {
        "path": str(
            path.relative_to(
                REPO_ROOT
            )
        ),
        "encoding": (
            encoding
        ),
        "sha256": (
            _sha256_bytes(
                path.read_bytes()
            )
        ),
        "line_count": (
            len(
                text.splitlines()
            )
        ),
        "imports": sorted(
            set(
                imports
            )
        ),
        "constants": (
            constants
        ),
        "functions": (
            relevant_functions
        ),
        "classes": (
            classes
        ),
    }


def _path_to_string(
    path: Iterable[
        str
        | int
    ],
) -> str:
    parts: list[
        str
    ] = []

    for item in path:
        if isinstance(
            item,
            int,
        ):
            parts.append(
                f"[{item}]"
            )

        else:
            if parts:
                parts.append(
                    "."
                )

            parts.append(
                item
            )

    return "".join(
        parts
    )


def _walk_json(
    value: Any,
    path: tuple[
        str
        | int,
        ...,
    ] = (),
):
    yield (
        path,
        value,
    )

    if isinstance(
        value,
        Mapping,
    ):
        for key, child in value.items():
            yield from _walk_json(
                child,
                path
                + (
                    str(
                        key
                    ),
                ),
            )

    elif isinstance(
        value,
        list,
    ):
        for index, child in enumerate(
            value
        ):
            yield from _walk_json(
                child,
                path
                + (
                    index,
                ),
            )


def _is_scalar(
    value: Any,
) -> bool:
    return isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
            type(
                None
            ),
        ),
    )


def _collect_identity_occurrences(
    payload: Any,
) -> list[
    dict[
        str,
        Any,
    ]
]:
    found: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for path, value in _walk_json(
        payload
    ):
        if (
            not path
            or not _is_scalar(
                value
            )
        ):
            continue

        last = path[
            -1
        ]

        if (
            isinstance(
                last,
                str,
            )
            and last
            in IDENTITY_KEYS
        ):
            found.append(
                {
                    "path": (
                        _path_to_string(
                            path
                        )
                    ),
                    "key": (
                        last
                    ),
                    "value": (
                        value
                    ),
                }
            )

    return found


def _collect_relevant_scalars(
    payload: Any,
    limit: int = 250,
) -> list[
    dict[
        str,
        Any,
    ]
]:
    found: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for path, value in _walk_json(
        payload
    ):
        if (
            not path
            or not _is_scalar(
                value
            )
        ):
            continue

        path_text = (
            _path_to_string(
                path
            ).lower()
        )

        if any(
            token
            in path_text
            for token
            in RELEVANT_KEY_TOKENS
        ):
            found.append(
                {
                    "path": (
                        _path_to_string(
                            path
                        )
                    ),
                    "value": (
                        value
                    ),
                }
            )

        if (
            len(
                found
            )
            >= limit
        ):
            break

    return found


def _mapping_scalar_excerpt(
    mapping: Mapping[
        str,
        Any,
    ],
) -> dict[
    str,
    Any,
]:
    result: dict[
        str,
        Any,
    ] = {}

    for key, value in mapping.items():
        if _is_scalar(
            value
        ):
            result[
                str(
                    key
                )
            ] = value

        elif isinstance(
            value,
            list,
        ):
            if (
                len(
                    value
                )
                <= 20
                and all(
                    _is_scalar(
                        item
                    )
                    for item
                    in value
                )
            ):
                result[
                    str(
                        key
                    )
                ] = value

    return result


def _collect_fold_like_mappings(
    payload: Any,
    limit: int = 100,
) -> list[
    dict[
        str,
        Any,
    ]
]:
    found: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for path, value in _walk_json(
        payload
    ):
        if not isinstance(
            value,
            Mapping,
        ):
            continue

        keys_lower = {
            str(
                key
            ).lower()
            for key
            in value.keys()
        }

        joined = " ".join(
            keys_lower
        )

        score = sum(
            token
            in joined
            for token
            in (
                "fold",
                "train",
                "validation",
                "purge",
                "start",
                "stop",
                "end",
            )
        )

        path_text = (
            _path_to_string(
                path
            ).lower()
        )

        if (
            "fold"
            in path_text
        ):
            score += 2

        if (
            score
            >= 3
        ):
            excerpt = (
                _mapping_scalar_excerpt(
                    value
                )
            )

            if excerpt:
                found.append(
                    {
                        "path": (
                            _path_to_string(
                                path
                            )
                        ),
                        "keys": sorted(
                            str(
                                key
                            )
                            for key
                            in value.keys()
                        ),
                        "scalar_excerpt": (
                            excerpt
                        ),
                    }
                )

        if (
            len(
                found
            )
            >= limit
        ):
            break

    return found


def _inspect_json_contract(
    path: Path,
) -> dict[
    str,
    Any,
]:
    payload, encoding, sha256 = (
        _load_json_auto(
            path
        )
    )

    top_level_keys: list[
        str
    ] = []

    if isinstance(
        payload,
        Mapping,
    ):
        top_level_keys = sorted(
            str(
                key
            )
            for key
            in payload.keys()
        )

    summary: dict[
        str,
        Any,
    ] = {
        "path": str(
            path.relative_to(
                REPO_ROOT
            )
        ),
        "encoding": (
            encoding
        ),
        "sha256": (
            sha256
        ),
        "top_level_keys": (
            top_level_keys
        ),
        "identity_occurrences": (
            _collect_identity_occurrences(
                payload
            )
        ),
        "relevant_scalars": (
            _collect_relevant_scalars(
                payload
            )
        ),
        "fold_like_mappings": (
            _collect_fold_like_mappings(
                payload
            )
        ),
    }

    if isinstance(
        payload,
        Mapping,
    ):
        for key in (
            "analysis_version",
            "contract_version",
            "research_scope",
            "reason",
            "valid",
        ):
            if (
                key
                in payload
                and _is_scalar(
                    payload[
                        key
                    ]
                )
            ):
                summary[
                    key
                ] = payload[
                    key
                ]

    return summary


def _all_values_for_key(
    payload: Any,
    key_name: str,
) -> list[
    Any
]:
    values: list[
        Any
    ] = []

    for path, value in _walk_json(
        payload
    ):
        if (
            not path
        ):
            continue

        last = path[
            -1
        ]

        if (
            last
            == key_name
            and _is_scalar(
                value
            )
        ):
            values.append(
                value
            )

    return values


def _unique_scalar_values(
    values: Iterable[
        Any
    ],
) -> list[
    Any
]:
    result: list[
        Any
    ] = []

    seen: set[
        str
    ] = set()

    for value in values:
        token = json.dumps(
            value,
            sort_keys=True,
        )

        if token in seen:
            continue

        seen.add(
            token
        )

        result.append(
            value
        )

    return result


def _cross_check_contracts(
    protocol_payload: Any,
    registry_payload: Any,
    supervised_payload: Any,
) -> dict[
    str,
    Any,
]:
    registry_contract = None

    if isinstance(
        registry_payload,
        Mapping,
    ):
        registry_contract = (
            registry_payload.get(
                "contract"
            )
        )

    frozen_train: Mapping[
        str,
        Any,
    ] = {}

    if isinstance(
        registry_contract,
        Mapping,
    ):
        candidate = (
            registry_contract.get(
                "frozen_train_identity"
            )
        )

        if isinstance(
            candidate,
            Mapping,
        ):
            frozen_train = (
                candidate
            )

    checks: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for key in (
        "dataset_id",
        "dataset_sha256",
        "feature_count",
        "manifest_sha256",
        "row_count",
        "train_input_fingerprint_sha256",
        "train_target_fingerprint_sha256",
    ):
        expected = (
            frozen_train.get(
                key
            )
        )

        protocol_values = (
            _unique_scalar_values(
                _all_values_for_key(
                    protocol_payload,
                    key,
                )
            )
        )

        supervised_values = (
            _unique_scalar_values(
                _all_values_for_key(
                    supervised_payload,
                    key,
                )
            )
        )

        protocol_match = (
            expected
            in protocol_values
            if expected
            is not None
            else False
        )

        supervised_match = (
            expected
            in supervised_values
            if expected
            is not None
            else False
        )

        checks.append(
            {
                "key": (
                    key
                ),
                "registry_expected": (
                    expected
                ),
                "protocol_values": (
                    protocol_values
                ),
                "supervised_batch_values": (
                    supervised_values
                ),
                "protocol_match": (
                    protocol_match
                ),
                "supervised_batch_match": (
                    supervised_match
                ),
            }
        )

    registry_fingerprint = None

    if isinstance(
        registry_payload,
        Mapping,
    ):
        fingerprint_obj = (
            registry_payload.get(
                "registry_fingerprint"
            )
        )

        if isinstance(
            fingerprint_obj,
            Mapping,
        ):
            registry_fingerprint = (
                fingerprint_obj.get(
                    "sha256"
                )
            )

    return {
        "registry_fingerprint": (
            registry_fingerprint
        ),
        "registry_fingerprint_matches_expected": (
            registry_fingerprint
            == EXPECTED_REGISTRY_FINGERPRINT
        ),
        "frozen_train_identity_checks": (
            checks
        ),
    }


def _assert_required_files() -> None:
    required = (
        LOADER_PATH,
        EVALUATOR_PATH,
        PROTOCOL_JSON_PATH,
        REGISTRY_JSON_PATH,
        SUPERVISED_BATCH_JSON_PATH,
    )

    missing = [
        str(
            path.relative_to(
                REPO_ROOT
            )
        )
        for path
        in required
        if not path.is_file()
    ]

    if missing:
        raise InspectionError(
            "Missing required integration "
            f"evidence/files: {missing}"
        )


def build_report() -> dict[
    str,
    Any,
]:
    _assert_required_files()

    protocol_payload, _, _ = (
        _load_json_auto(
            PROTOCOL_JSON_PATH
        )
    )

    registry_payload, _, _ = (
        _load_json_auto(
            REGISTRY_JSON_PATH
        )
    )

    supervised_payload, _, _ = (
        _load_json_auto(
            SUPERVISED_BATCH_JSON_PATH
        )
    )

    loader_source = (
        _inspect_python_source(
            LOADER_PATH
        )
    )

    evaluator_source = (
        _inspect_python_source(
            EVALUATOR_PATH
        )
    )

    protocol_contract = (
        _inspect_json_contract(
            PROTOCOL_JSON_PATH
        )
    )

    registry_contract = (
        _inspect_json_contract(
            REGISTRY_JSON_PATH
        )
    )

    supervised_contract = (
        _inspect_json_contract(
            SUPERVISED_BATCH_JSON_PATH
        )
    )

    cross_checks = (
        _cross_check_contracts(
            protocol_payload,
            registry_payload,
            supervised_payload,
        )
    )

    evaluator_function_names = {
        entry[
            "name"
        ]
        for entry
        in evaluator_source[
            "functions"
        ]
    }

    required_evaluator_api_present = all(
        name
        in evaluator_function_names
        for name
        in (
            "load_frozen_candidate_registry",
            "validate_train_only_inputs",
            "validate_fold_specs",
            "evaluate_registry_train_only",
        )
    )

    fold_evidence_present = bool(
        protocol_contract[
            "fold_like_mappings"
        ]
    )

    valid = all(
        (
            cross_checks[
                "registry_fingerprint_matches_expected"
            ],
            required_evaluator_api_present,
            fold_evidence_present,
        )
    )

    return {
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "valid": (
            valid
        ),
        "research_scope": (
            "STATIC_LOCAL_INTEGRATION_CONTRACT_"
            "INSPECTION_ONLY_NO_DATA_VALUES_LOADED"
        ),
        "sources": {
            "portable_training_input_loader": (
                loader_source
            ),
            "candidate_evaluator": (
                evaluator_source
            ),
            "research_protocol_design": (
                protocol_contract
            ),
            "candidate_registry_design": (
                registry_contract
            ),
            "supervised_batch_integration": (
                supervised_contract
            ),
        },
        "cross_checks": (
            cross_checks
        ),
        "decision": {
            "required_evaluator_api_present": (
                required_evaluator_api_present
            ),
            "research_protocol_fold_evidence_present": (
                fold_evidence_present
            ),
            "real_candidate_fit_authorized": (
                False
            ),
            "validation_access_authorized": (
                False
            ),
            "test_access_authorized": (
                False
            ),
            "live_authorized": (
                False
            ),
            "next_action_if_valid": (
                "IMPLEMENT_EXACT_TRAIN_ONLY_"
                "SUPERVISED_BATCH_TO_FROZEN_FOLDS_"
                "CANDIDATE_EVALUATOR_INTEGRATION_RUNNER"
            ),
        },
        "scientific_policy": {
            "python_project_modules_imported": (
                False
            ),
            "portable_dataset_rows_loaded": (
                False
            ),
            "train_feature_values_loaded": (
                False
            ),
            "train_target_values_loaded": (
                False
            ),
            "validation_feature_values_loaded": (
                False
            ),
            "validation_target_values_loaded": (
                False
            ),
            "test_feature_values_loaded": (
                False
            ),
            "test_target_values_loaded": (
                False
            ),
            "model_fit_performed": (
                False
            ),
            "scaler_fit_performed": (
                False
            ),
            "model_artifacts_written": (
                False
            ),
            "threshold_search_performed": (
                False
            ),
            "feature_selection_performed": (
                False
            ),
            "execution_integration_modified": (
                False
            ),
            "risk_engine_modified": (
                False
            ),
            "orders_sent": (
                False
            ),
            "live_authorized": (
                False
            ),
        },
    }


def _write_json_utf8(
    path: Path,
    payload: Mapping[
        str,
        Any,
    ],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    text = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )

    path.write_text(
        text
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect exact local contracts required "
            "to wire the portable 331 supervised "
            "TRAIN batch into the frozen candidate "
            "walk-forward evaluator."
        )
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=(
            REPO_ROOT
            / "xauusd_portable_331_candidate_evaluator_integration_contract.json"
        ),
    )

    args = parser.parse_args()

    try:
        report = build_report()

    except Exception as exc:
        failure = {
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "valid": False,
            "reason": (
                "INTEGRATION_CONTRACT_INSPECTION_FAILED"
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
            "scientific_policy": {
                "portable_dataset_rows_loaded": (
                    False
                ),
                "model_fit_performed": (
                    False
                ),
                "validation_access_authorized": (
                    False
                ),
                "test_access_authorized": (
                    False
                ),
                "live_authorized": (
                    False
                ),
            },
        }

        _write_json_utf8(
            args.output,
            failure,
        )

        print(
            json.dumps(
                failure,
                indent=2,
                sort_keys=True,
            )
        )

        return 1

    _write_json_utf8(
        args.output,
        report,
    )

    print(
        json.dumps(
            {
                "analysis_version": (
                    report[
                        "analysis_version"
                    ]
                ),
                "valid": (
                    report[
                        "valid"
                    ]
                ),
                "output": str(
                    args.output
                ),
                "decision": (
                    report[
                        "decision"
                    ]
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )

    return (
        0
        if report[
            "valid"
        ]
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )