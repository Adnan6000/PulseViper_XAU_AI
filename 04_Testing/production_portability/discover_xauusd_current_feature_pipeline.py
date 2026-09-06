from __future__ import annotations

import ast
import json
import sys
import tokenize
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]

ANALYSIS_VERSION = (
    "XAUUSD_CURRENT_FEATURE_PIPELINE_DISCOVERY_V1"
)

EXPECTED_TRAINING_CONTRACT = (
    "XAUUSD_MTF_TRAINING_V3"
)

EXPECTED_DATASET_ID = (
    "train_66ff363d25d8143d4e2c3410"
)

EXPECTED_DATASET_SHA256 = (
    "66ff363d25d8143d4e2c3410964ad26b"
    "5bd72f2e98806c3e0997ce420d18413d"
)

EXPECTED_TRAINING_MANIFEST_SHA256 = (
    "a205403a6cb5a2d1b17159a2296d1f4a"
    "fb01ea5b9b90b2710feafa7dd9476aa3"
)

EXPECTED_FEATURE_COUNT = 333


SCAN_ROOTS = (
    ROOT_DIR / "02_AI",
    ROOT_DIR / "04_Testing",
)


EXCLUDED_DIR_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "models",
}


SEARCH_TOKENS: dict[str, int] = {
    "m5_spread_points": 20,
    "m5_tick_volume_log1p": 20,
    "m5_tick_volume_ratio20": 20,
    "XAUUSD_MTF_TRAINING_V3": 16,
    "FEATURES_V1": 10,
    "feature_columns": 8,
    "m15_ema20": 8,
    "m30_ema20": 8,
    "h1_ema20": 8,
    "h4_ema20": 8,
    "d1_ema20": 8,
    "target_tradeable": 4,
}


DEFINITION_NAME_TERMS = (
    "feature",
    "generator",
    "builder",
    "dataset",
    "training",
    "mtf",
    "multi",
    "timeframe",
)


SAFE_MANIFEST_SCALAR_KEYS = {
    "dataset_id",
    "dataset_sha256",
    "training_manifest_sha256",
    "training_contract_version",
    "feature_contract_version",
    "data_schema_version",
    "canonical_symbol",
    "broker_id",
    "broker_symbol",
    "asset_class",
    "execution_environment",
    "contract_spec_id",
    "row_count",
    "feature_count",
}


SENSITIVE_KEY_TERMS = (
    "account_scope",
    "account_id",
    "account_login",
    "login",
    "password",
    "secret",
    "token",
    "api_key",
    "holder_name",
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


def _is_excluded(
    path: Path,
) -> bool:

    return any(
        part
        in EXCLUDED_DIR_NAMES
        for part
        in path.parts
    )


def _read_python_source(
    path: Path,
) -> str:

    with tokenize.open(
        path
    ) as handle:

        return handle.read()


def _source_matches(
    source: str,
) -> dict[str, list[int]]:

    lines = (
        source.splitlines()
    )

    result: dict[
        str,
        list[int],
    ] = {}

    for token in (
        SEARCH_TOKENS
    ):

        matches = [
            index
            for index, line
            in enumerate(
                lines,
                start=1,
            )
            if token.lower()
            in line.lower()
        ]

        if matches:
            result[
                token
            ] = (
                matches
            )

    return result


def _ast_inventory(
    source: str,
) -> dict[str, Any]:

    try:

        tree = ast.parse(
            source
        )

    except SyntaxError as exc:

        return {
            "parse_ok": False,
            "syntax_error": (
                f"{exc.msg} "
                f"line={exc.lineno}"
            ),
            "classes": [],
            "functions": [],
            "imports": [],
        }

    classes: list[str] = []

    functions: list[str] = []

    imports: set[str] = set()

    for node in ast.walk(
        tree
    ):

        if isinstance(
            node,
            ast.ClassDef,
        ):

            classes.append(
                node.name
            )

        elif isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):

            functions.append(
                node.name
            )

        elif isinstance(
            node,
            ast.Import,
        ):

            for alias in node.names:
                imports.add(
                    alias.name
                )

        elif isinstance(
            node,
            ast.ImportFrom,
        ):

            module = (
                node.module
            )

            if module:
                imports.add(
                    module
                )

    return {
        "parse_ok": True,
        "classes": sorted(
            set(
                classes
            )
        ),
        "functions": sorted(
            set(
                functions
            )
        ),
        "imports": sorted(
            imports
        ),
    }


def _definition_bonus(
    inventory: dict[str, Any],
) -> tuple[
    int,
    list[str],
]:

    names = (
        list(
            inventory.get(
                "classes",
                [],
            )
        )
        +
        list(
            inventory.get(
                "functions",
                [],
            )
        )
    )

    bonus = 0

    matched_names: list[
        str
    ] = []

    for name in names:

        lowered = (
            str(
                name
            ).lower()
        )

        if any(
            term
            in lowered
            for term
            in DEFINITION_NAME_TERMS
        ):

            bonus += 3

            matched_names.append(
                str(
                    name
                )
            )

    return (
        bonus,
        sorted(
            set(
                matched_names
            )
        ),
    )


def _scan_python_sources(
) -> list[dict[str, Any]]:

    candidates: list[
        dict[str, Any]
    ] = []

    for scan_root in (
        SCAN_ROOTS
    ):

        if not scan_root.exists():
            continue

        for path in (
            scan_root.rglob(
                "*.py"
            )
        ):

            if _is_excluded(
                path
            ):
                continue

            try:

                source = (
                    _read_python_source(
                        path
                    )
                )

            except (
                OSError,
                UnicodeError,
                SyntaxError,
            ):
                continue

            matches = (
                _source_matches(
                    source
                )
            )

            if not matches:
                continue

            inventory = (
                _ast_inventory(
                    source
                )
            )

            score = sum(
                SEARCH_TOKENS[
                    token
                ]
                for token
                in matches
            )

            (
                bonus,
                matched_definitions,
            ) = (
                _definition_bonus(
                    inventory
                )
            )

            score += (
                bonus
            )

            candidate_type = (
                "LIKELY_PIPELINE_DEFINITION"
                if (
                    matched_definitions
                    and
                    (
                        "m5_spread_points"
                        in matches
                        or
                        EXPECTED_TRAINING_CONTRACT
                        in matches
                    )
                )
                else
                "LIKELY_PIPELINE_CONSUMER_OR_TEST"
            )

            candidates.append(
                {
                    "path": (
                        _relative(
                            path
                        )
                    ),
                    "score": int(
                        score
                    ),
                    "candidate_type": (
                        candidate_type
                    ),
                    "matched_tokens": {
                        token: (
                            line_numbers
                        )
                        for (
                            token,
                            line_numbers,
                        )
                        in sorted(
                            matches.items()
                        )
                    },
                    "matching_definitions": (
                        matched_definitions
                    ),
                    "classes": (
                        inventory.get(
                            "classes",
                            [],
                        )
                    ),
                    "functions": (
                        inventory.get(
                            "functions",
                            [],
                        )
                    ),
                    "imports": (
                        inventory.get(
                            "imports",
                            [],
                        )
                    ),
                    "ast_parse_ok": bool(
                        inventory.get(
                            "parse_ok",
                            False,
                        )
                    ),
                }
            )

    candidates.sort(
        key=lambda item: (
            int(
                item[
                    "score"
                ]
            ),
            len(
                item[
                    "matched_tokens"
                ]
            ),
        ),
        reverse=True,
    )

    return candidates


def _find_manifest_candidates(
) -> list[Path]:

    base = (
        ROOT_DIR
        /
        "01_Data"
        /
        "Canonical"
        /
        "Instruments"
        /
        "XAUUSD"
    )

    if not base.exists():
        return []

    results: list[
        Path
    ] = []

    patterns = (
        "*XAUUSD_MTF_TRAINING_V3*.manifest.json",
        "*.manifest.json",
    )

    seen: set[
        Path
    ] = set()

    for pattern in patterns:

        for path in base.rglob(
            pattern
        ):

            if path in seen:
                continue

            seen.add(
                path
            )

            if _is_excluded(
                path
            ):
                continue

            try:

                text = (
                    path.read_text(
                        encoding="utf-8"
                    )
                )

            except (
                OSError,
                UnicodeError,
            ):
                continue

            if (
                EXPECTED_DATASET_ID
                in text
                or
                EXPECTED_DATASET_SHA256
                in text
                or
                EXPECTED_TRAINING_CONTRACT
                in text
            ):

                results.append(
                    path
                )

    return sorted(
        results
    )


def _is_sensitive_key(
    key: str,
) -> bool:

    lowered = (
        key.lower()
    )

    return any(
        term
        in lowered
        for term
        in SENSITIVE_KEY_TERMS
    )


def _find_large_feature_lists(
    value: Any,
    *,
    path: str = "$",
) -> list[dict[str, Any]]:

    found: list[
        dict[str, Any]
    ] = []

    if isinstance(
        value,
        dict,
    ):

        for key, child in (
            value.items()
        ):

            if _is_sensitive_key(
                str(
                    key
                )
            ):
                continue

            found.extend(
                _find_large_feature_lists(
                    child,
                    path=(
                        f"{path}.{key}"
                    ),
                )
            )

    elif isinstance(
        value,
        list,
    ):

        if (
            len(
                value
            )
            >=
            20
            and
            all(
                isinstance(
                    item,
                    str,
                )
                for item
                in value
            )
        ):

            feature_like = sum(
                1
                for item
                in value
                if any(
                    prefix
                    in item.lower()
                    for prefix
                    in (
                        "m5_",
                        "m15_",
                        "m30_",
                        "h1_",
                        "h4_",
                        "d1_",
                    )
                )
            )

            if (
                feature_like
                >=
                10
            ):

                found.append(
                    {
                        "json_path": (
                            path
                        ),
                        "count": int(
                            len(
                                value
                            )
                        ),
                        "feature_like_count": int(
                            feature_like
                        ),
                        "first_20": (
                            value[
                                :20
                            ]
                        ),
                        "last_20": (
                            value[
                                -20:
                            ]
                        ),
                        "contains_broker_sensitive_features": {
                            "m5_spread_points": (
                                "m5_spread_points"
                                in value
                            ),
                            "m5_tick_volume_log1p": (
                                "m5_tick_volume_log1p"
                                in value
                            ),
                            "m5_tick_volume_ratio20": (
                                "m5_tick_volume_ratio20"
                                in value
                            ),
                        },
                    }
                )

        for index, child in (
            enumerate(
                value
            )
        ):

            if isinstance(
                child,
                (
                    dict,
                    list,
                ),
            ):

                found.extend(
                    _find_large_feature_lists(
                        child,
                        path=(
                            f"{path}[{index}]"
                        ),
                    )
                )

    return found


def _safe_manifest_scalars(
    value: Any,
    *,
    path: str = "$",
) -> dict[str, Any]:

    result: dict[
        str,
        Any
    ] = {}

    if not isinstance(
        value,
        dict,
    ):
        return result

    for key, child in (
        value.items()
    ):

        key_string = str(
            key
        )

        if _is_sensitive_key(
            key_string
        ):
            continue

        child_path = (
            f"{path}.{key_string}"
        )

        if (
            key_string
            in SAFE_MANIFEST_SCALAR_KEYS
            and
            isinstance(
                child,
                (
                    str,
                    int,
                    float,
                    bool,
                ),
            )
        ):

            result[
                child_path
            ] = (
                child
            )

        elif isinstance(
            child,
            dict,
        ):

            result.update(
                _safe_manifest_scalars(
                    child,
                    path=(
                        child_path
                    ),
                )
            )

    return result


def _inspect_manifests(
) -> list[dict[str, Any]]:

    documents: list[
        dict[str, Any]
    ] = []

    for path in (
        _find_manifest_candidates()
    ):

        try:

            payload = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
        ) as exc:

            documents.append(
                {
                    "path": (
                        _relative(
                            path
                        )
                    ),
                    "valid_json": False,
                    "error": (
                        type(
                            exc
                        ).__name__
                    ),
                }
            )

            continue

        feature_lists = (
            _find_large_feature_lists(
                payload
            )
        )

        documents.append(
            {
                "path": (
                    _relative(
                        path
                    )
                ),
                "valid_json": True,
                "safe_scalar_metadata": (
                    _safe_manifest_scalars(
                        payload
                    )
                ),
                "feature_lists": (
                    feature_lists
                ),
            }
        )

    return documents


def _decision(
    source_candidates: list[
        dict[str, Any]
    ],
    manifests: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:

    high_confidence = [
        candidate
        for candidate
        in source_candidates
        if (
            candidate[
                "score"
            ]
            >=
            40
            and
            (
                "m5_spread_points"
                in candidate[
                    "matched_tokens"
                ]
                or
                EXPECTED_TRAINING_CONTRACT
                in candidate[
                    "matched_tokens"
                ]
            )
        )
    ]

    feature_contract_found = any(
        any(
            int(
                feature_list.get(
                    "count",
                    0,
                )
            )
            ==
            EXPECTED_FEATURE_COUNT
            for feature_list
            in manifest.get(
                "feature_lists",
                []
            )
        )
        for manifest
        in manifests
        if manifest.get(
            "valid_json",
            False,
        )
    )

    if high_confidence:

        status = (
            "PIPELINE_SOURCE_CANDIDATES_FOUND"
        )

    else:

        status = (
            "PIPELINE_SOURCE_NOT_YET_IDENTIFIED"
        )

    return {
        "status": (
            status
        ),
        "high_confidence_candidate_count": int(
            len(
                high_confidence
            )
        ),
        "high_confidence_candidate_paths": [
            candidate[
                "path"
            ]
            for candidate
            in high_confidence[
                :10
            ]
        ],
        "frozen_333_feature_list_found_in_manifest": (
            feature_contract_found
        ),
        "next_gate": (
            "USE_IDENTIFIED_LOCAL_PIPELINE_TO_BUILD_"
            "CURRENT_BROKER_TRAIN_ONLY_DOMAIN_SHIFT_AUDIT"
            if high_confidence
            else
            "INSPECT_TOP_LOCAL_SOURCE_CANDIDATES_BEFORE_DOMAIN_SHIFT"
        ),
    }


def run_discovery(
) -> dict[str, Any]:

    source_candidates = (
        _scan_python_sources()
    )

    manifests = (
        _inspect_manifests()
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_CURRENT_FEATURE_PIPELINE_DISCOVERY"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "expected_contract": {
            "training_contract": (
                EXPECTED_TRAINING_CONTRACT
            ),
            "dataset_id": (
                EXPECTED_DATASET_ID
            ),
            "dataset_sha256": (
                EXPECTED_DATASET_SHA256
            ),
            "training_manifest_sha256": (
                EXPECTED_TRAINING_MANIFEST_SHA256
            ),
            "feature_count": (
                EXPECTED_FEATURE_COUNT
            ),
        },
        "scan_policy": {
            "roots": [
                _relative(
                    path
                )
                for path
                in SCAN_ROOTS
            ],
            "python_source_executed": False,
            "python_source_ast_parsed": True,
            "imports_executed": False,
            "model_loaded": False,
            "mt5_used": False,
            "orders_sent": False,
            "train_data_loaded": False,
            "validation_data_loaded": False,
            "test_data_loaded": False,
            "model_artifacts_written": False,
            "live_authorized": False,
        },
        "source_candidates": (
            source_candidates[
                :30
            ]
        ),
        "manifest_candidates": (
            manifests
        ),
        "decision": (
            _decision(
                source_candidates,
                manifests,
            )
        ),
    }


def main() -> int:

    try:

        result = (
            run_discovery()
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_CURRENT_FEATURE_"
                        "PIPELINE_DISCOVERY_FAILED"
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
                    "mt5_used": False,
                    "orders_sent": False,
                    "test_data_loaded": False,
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