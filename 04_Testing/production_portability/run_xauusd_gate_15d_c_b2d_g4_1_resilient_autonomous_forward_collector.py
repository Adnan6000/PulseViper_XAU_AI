"""Gate 15D-C-B2D-G4.1 — Resilient Autonomous Prospective Sample Collector."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import time
from typing import Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]

G1_RUNNER = (
    REPO_ROOT
    / "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g1_genuine_anchored_forward_capture.py"
)

G2_RUNNER = (
    REPO_ROOT
    / "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g2_genuine_outcome_maturation.py"
)

G3_RUNNER = (
    REPO_ROOT
    / "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g3_forward_sample_controller.py"
)

G1_EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g1_genuine_anchored_forward_capture_evidence.json"
)

G2_EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g2_genuine_outcome_maturation_evidence.json"
)

LOG_PATH = (
    REPO_ROOT
    / "01_Data/Shadow/xauusd_g4_1_resilient_autonomous_collector.log"
)

DEFAULT_TARGET_MATURED = 30
DEFAULT_POLL_SECONDS = 60
DEFAULT_RETRY_SECONDS = 60

PERFORMANCE_EVALUATION_AUTHORIZED = False
PNL_EVALUATION_AUTHORIZED = False
LIVE_AUTHORIZED = False
EXECUTION_AUTHORIZED = False


class G41CollectorError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:
    if not condition:
        raise G41CollectorError(reason)


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def append_log(
    message: str,
) -> None:
    LOG_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with LOG_PATH.open(
        "a",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(
            f"[{utc_now()}] {message}\n"
        )
        handle.flush()


def run_process(
    args: list[str],
    *,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:

    process = subprocess.run(
        args,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    append_log(
        "COMMAND="
        + " ".join(args)
        + f" RETURN_CODE={process.returncode}"
    )

    if process.stdout:
        append_log("STDOUT_BEGIN")

        for line in process.stdout.rstrip().splitlines():
            append_log(line)

        append_log("STDOUT_END")

    if process.stderr:
        append_log("STDERR_BEGIN")

        for line in process.stderr.rstrip().splitlines():
            append_log(line)

        append_log("STDERR_END")

    if check:
        require(
            process.returncode == 0,
            "COMMAND_FAILED:"
            + " ".join(args),
        )

    return process


def git(
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:

    return run_process(
        ["git", *args],
        check=check,
    )


def git_output(
    *args: str,
) -> str:

    return git(
        *args
    ).stdout.rstrip("\r\n")


def normalize_status_path(
    line: str,
) -> str:

    value = line[3:].strip()

    if " -> " in value:
        value = value.split(
            " -> ",
            1,
        )[1]

    if (
        value.startswith('"')
        and value.endswith('"')
    ):
        value = value[1:-1]

    return value.replace(
        "\\",
        "/",
    )


def status_paths() -> set[str]:

    output = git_output(
        "status",
        "--porcelain",
        "--untracked-files=all",
    )

    return {
        normalize_status_path(line)
        for line in output.splitlines()
        if len(line) >= 4
    }


def parse_kv(
    stdout: str,
) -> dict[str, str]:

    result: dict[str, str] = {}

    for raw in stdout.splitlines():

        line = raw.strip()

        if "=" not in line:
            continue

        key, value = line.split(
            "=",
            1,
        )

        if key and value:
            result[
                key.strip()
            ] = value.strip()

    return result


def run_python(
    path: Path,
    *args: str,
) -> tuple[
    subprocess.CompletedProcess[str],
    dict[str, str],
]:

    process = run_process(
        [
            sys.executable,
            str(path),
            *args,
        ],
        check=False,
    )

    return (
        process,
        parse_kv(
            process.stdout
        ),
    )


def require_false(
    data: Mapping[str, str],
    key: str,
) -> None:

    require(
        data.get(
            key,
            "",
        ).lower()
        ==
        "false",
        (
            f"{key}_NOT_FALSE:"
            f"{data.get(key)}"
        ),
    )


def verify_common_safety(
    data: Mapping[str, str],
) -> None:

    for key in (
        "LIVE_AUTHORIZED",
        "EXECUTION_AUTHORIZED",
    ):
        require_false(
            data,
            key,
        )

    if (
        "FORWARD_PERFORMANCE_EVALUATED"
        in data
    ):
        require_false(
            data,
            "FORWARD_PERFORMANCE_EVALUATED",
        )

    if (
        "PERFORMANCE_EVALUATED"
        in data
    ):
        require_false(
            data,
            "PERFORMANCE_EVALUATED",
        )

    if "PNL_EVALUATED" in data:
        require_false(
            data,
            "PNL_EVALUATED",
        )


def parse_positive_int(
    data: Mapping[str, str],
    key: str,
) -> int:

    try:
        value = int(
            data[key]
        )

    except Exception as exc:
        raise G41CollectorError(
            f"INVALID_INTEGER:"
            f"{key}:"
            f"{data.get(key)}"
        ) from exc

    require(
        value >= 0,
        (
            f"NEGATIVE_INTEGER:"
            f"{key}:{value}"
        ),
    )

    return value


def is_transient_git_fetch_failure(
    process: subprocess.CompletedProcess[str],
    data: Mapping[str, str],
) -> bool:

    combined = (
        process.stdout
        + "\n"
        + process.stderr
    ).lower()

    error = (
        data.get(
            "ERROR",
            ""
        )
        .lower()
    )

    transient_markers = (
        "git_fetch_origin_failed",
        "git fetch origin",
        "could not resolve host",
        "failed to connect",
        "connection timed out",
        "connection reset",
        "network is unreachable",
        "temporary failure in name resolution",
        "unable to access",
        "tls",
        "ssl",
    )

    haystack = (
        combined
        + "\n"
        + error
    )

    return any(
        marker in haystack
        for marker in transient_markers
    )


def resilient_fetch_origin(
    *,
    retry_seconds: int,
    context: str,
) -> None:

    require(
        retry_seconds >= 10,
        "RETRY_SECONDS_TOO_SMALL",
    )

    attempt = 0

    while True:

        attempt += 1

        process = git(
            "fetch",
            "origin",
            check=False,
        )

        if process.returncode == 0:

            if attempt > 1:
                append_log(
                    f"TRANSIENT_RECOVERED "
                    f"context={context} "
                    f"attempt={attempt}"
                )

                print(
                    "G4_1_NETWORK_RECOVERED "
                    f"context={context} "
                    f"attempt={attempt}",
                    flush=True,
                )

            return

        append_log(
            f"TRANSIENT_WAIT "
            f"context={context} "
            f"attempt={attempt} "
            f"retry_seconds={retry_seconds}"
        )

        print(
            "G4_1_TRANSIENT_WAIT "
            f"context={context} "
            f"retry_in={retry_seconds}s",
            flush=True,
        )

        time.sleep(
            retry_seconds
        )


def verify_clean_synced_repository(
    *,
    retry_seconds: int,
) -> str:

    resilient_fetch_origin(
        retry_seconds=retry_seconds,
        context="startup_fetch",
    )

    branch = git_output(
        "branch",
        "--show-current",
    )

    head = git_output(
        "rev-parse",
        "HEAD",
    )

    origin = git_output(
        "rev-parse",
        "origin/main",
    )

    require(
        branch == "main",
        f"UNEXPECTED_BRANCH:{branch}",
    )

    require(
        head == origin,
        (
            "HEAD_ORIGIN_MAIN_DIVERGENCE:"
            f"{head}!={origin}"
        ),
    )

    dirty = status_paths()

    require(
        not dirty,
        (
            "WORKTREE_NOT_CLEAN:"
            f"{sorted(dirty)}"
        ),
    )

    return head


def run_g3_once() -> tuple[
    subprocess.CompletedProcess[str],
    dict[str, str],
]:

    return run_python(
        G3_RUNNER
    )


def run_g3_resilient(
    *,
    retry_seconds: int,
) -> dict[str, str]:

    attempt = 0

    while True:

        attempt += 1

        process, data = (
            run_g3_once()
        )

        if process.returncode == 0:

            require(
                data.get(
                    "GATE_15D_C_B2D_G3_STATUS"
                )
                ==
                "PASS",
                "G3_NOT_PASS",
            )

            verify_common_safety(
                data
            )

            if attempt > 1:
                append_log(
                    "G3_TRANSIENT_RECOVERED "
                    f"attempt={attempt}"
                )

            return data

        verify_common_safety(
            data
        )

        if is_transient_git_fetch_failure(
            process,
            data,
        ):

            append_log(
                "G3_TRANSIENT_WAIT "
                f"attempt={attempt} "
                f"retry_seconds={retry_seconds}"
            )

            print(
                "G4_1_TRANSIENT_WAIT "
                "context=g3_git_fetch "
                f"retry_in={retry_seconds}s",
                flush=True,
            )

            time.sleep(
                retry_seconds
            )

            continue

        raise G41CollectorError(
            "G3_PROCESS_FAILED:"
            + data.get(
                "ERROR",
                "UNKNOWN",
            )
        )


def run_g1() -> dict[str, str]:

    process, data = run_python(
        G1_RUNNER
    )

    require(
        process.returncode == 0,
        "G1_PROCESS_FAILED",
    )

    require(
        data.get(
            "GATE_15D_C_B2D_G1_STATUS"
        )
        ==
        "PASS",
        "G1_NOT_PASS",
    )

    require(
        data.get(
            "GENUINE_MT5_ACQUISITION",
            "",
        ).lower()
        ==
        "true",
        "G1_NOT_GENUINE_MT5",
    )

    require(
        data.get(
            "ANCHOR_APPENDED",
            "",
        ).lower()
        ==
        "true",
        "G1_ANCHOR_NOT_APPENDED",
    )

    require(
        data.get(
            "OBSERVATION_APPENDED",
            "",
        ).lower()
        ==
        "true",
        "G1_OBSERVATION_NOT_APPENDED",
    )

    require(
        data.get(
            "OUTCOME_LEDGER_UNCHANGED",
            "",
        ).lower()
        ==
        "true",
        "G1_OUTCOME_LEDGER_CHANGED",
    )

    verify_common_safety(
        data
    )

    return data


def run_g2_dry(
    observation_id: str,
) -> dict[str, str]:

    process, data = run_python(
        G2_RUNNER,
        "--observation-id",
        observation_id,
    )

    require(
        process.returncode == 0,
        "G2_DRY_PROCESS_FAILED",
    )

    require(
        data.get(
            "GATE_15D_C_B2D_G2_STATUS"
        )
        ==
        "PASS",
        "G2_DRY_NOT_PASS",
    )

    require(
        data.get("MODE")
        ==
        "DRY_RUN",
        "G2_DRY_MODE_MISMATCH",
    )

    require(
        data.get(
            "HORIZON_BARS"
        )
        ==
        "12",
        "G2_DRY_HORIZON_MISMATCH",
    )

    require(
        data.get(
            "OUTCOME_APPENDED",
            "",
        ).lower()
        ==
        "false",
        "G2_DRY_APPENDED_OUTCOME",
    )

    require(
        data.get(
            "OUTCOME_IDEMPOTENT_DUPLICATE",
            "",
        ).lower()
        ==
        "false",
        "G2_DRY_UNEXPECTED_DUPLICATE",
    )

    verify_common_safety(
        data
    )

    return data


def run_g2_first_append(
    observation_id: str,
) -> dict[str, str]:

    process, data = run_python(
        G2_RUNNER,
        "--observation-id",
        observation_id,
        "--append-outcome",
    )

    require(
        process.returncode == 0,
        "G2_APPEND_PROCESS_FAILED",
    )

    require(
        data.get(
            "GATE_15D_C_B2D_G2_STATUS"
        )
        ==
        "PASS",
        "G2_APPEND_NOT_PASS",
    )

    require(
        data.get("MODE")
        ==
        "APPEND_OUTCOME",
        "G2_APPEND_MODE_MISMATCH",
    )

    require(
        data.get(
            "HORIZON_BARS"
        )
        ==
        "12",
        "G2_APPEND_HORIZON_MISMATCH",
    )

    require(
        data.get(
            "OUTCOME_APPENDED",
            "",
        ).lower()
        ==
        "true",
        "G2_FIRST_APPEND_NOT_TRUE",
    )

    require(
        data.get(
            "OUTCOME_IDEMPOTENT_DUPLICATE",
            "",
        ).lower()
        ==
        "false",
        "G2_FIRST_APPEND_UNEXPECTED_DUPLICATE",
    )

    verify_common_safety(
        data
    )

    return data


def run_g2_idempotency(
    observation_id: str,
) -> dict[str, str]:

    process, data = run_python(
        G2_RUNNER,
        "--observation-id",
        observation_id,
        "--append-outcome",
    )

    require(
        process.returncode == 0,
        "G2_IDEMPOTENCY_PROCESS_FAILED",
    )

    require(
        data.get(
            "GATE_15D_C_B2D_G2_STATUS"
        )
        ==
        "PASS",
        "G2_IDEMPOTENCY_NOT_PASS",
    )

    require(
        data.get(
            "OUTCOME_APPENDED",
            "",
        ).lower()
        ==
        "false",
        "G2_IDEMPOTENCY_APPENDED_DUPLICATE",
    )

    require(
        data.get(
            "OUTCOME_IDEMPOTENT_DUPLICATE",
            "",
        ).lower()
        ==
        "true",
        "G2_IDEMPOTENCY_NOT_CONFIRMED",
    )

    verify_common_safety(
        data
    )

    return data


def commit_and_push_expected_evidence(
    expected_rel: str,
    *,
    message: str,
    retry_seconds: int,
) -> str:

    dirty = status_paths()

    require(
        dirty == {
            expected_rel
        },
        (
            "UNEXPECTED_DIRTY_PATHS:"
            f"{sorted(dirty)}"
        ),
    )

    resilient_fetch_origin(
        retry_seconds=retry_seconds,
        context="before_evidence_commit",
    )

    head_before = git_output(
        "rev-parse",
        "HEAD",
    )

    origin_before = git_output(
        "rev-parse",
        "origin/main",
    )

    require(
        head_before
        ==
        origin_before,
        (
            "REMOTE_MOVED_BEFORE_EVIDENCE_COMMIT:"
            f"{head_before}!="
            f"{origin_before}"
        ),
    )

    git(
        "add",
        "--",
        expected_rel,
    )

    check = git(
        "diff",
        "--cached",
        "--check",
        check=False,
    )

    require(
        check.returncode == 0,
        "CACHED_DIFF_CHECK_FAILED",
    )

    staged = {
        line.strip().replace(
            "\\",
            "/",
        )
        for line
        in git_output(
            "diff",
            "--cached",
            "--name-only",
        ).splitlines()
        if line.strip()
    }

    require(
        staged
        ==
        {
            expected_rel
        },
        (
            "UNEXPECTED_STAGED_PATHS:"
            f"{sorted(staged)}"
        ),
    )

    commit = git(
        "commit",
        "-m",
        message,
        check=False,
    )

    require(
        commit.returncode == 0,
        "EVIDENCE_COMMIT_FAILED",
    )

    resilient_fetch_origin(
        retry_seconds=retry_seconds,
        context="after_local_commit",
    )

    parent = git_output(
        "rev-parse",
        "HEAD^",
    )

    origin_now = git_output(
        "rev-parse",
        "origin/main",
    )

    require(
        parent
        ==
        origin_now,
        (
            "REMOTE_MOVED_AFTER_LOCAL_COMMIT:"
            f"{parent}!="
            f"{origin_now}"
        ),
    )

    while True:

        push = git(
            "push",
            "origin",
            "main",
            check=False,
        )

        if push.returncode == 0:
            break

        append_log(
            "PUSH_TRANSIENT_WAIT "
            f"retry_seconds={retry_seconds}"
        )

        print(
            "G4_1_TRANSIENT_WAIT "
            "context=git_push "
            f"retry_in={retry_seconds}s",
            flush=True,
        )

        time.sleep(
            retry_seconds
        )

        resilient_fetch_origin(
            retry_seconds=retry_seconds,
            context="push_retry_guard",
        )

        parent = git_output(
            "rev-parse",
            "HEAD^",
        )

        origin_now = git_output(
            "rev-parse",
            "origin/main",
        )

        require(
            parent
            ==
            origin_now,
            (
                "REMOTE_MOVED_DURING_PUSH_RETRY:"
                f"{parent}!="
                f"{origin_now}"
            ),
        )

    resilient_fetch_origin(
        retry_seconds=retry_seconds,
        context="post_push_verify",
    )

    head = git_output(
        "rev-parse",
        "HEAD",
    )

    origin = git_output(
        "rev-parse",
        "origin/main",
    )

    require(
        head
        ==
        origin,
        (
            "POST_PUSH_DIVERGENCE:"
            f"{head}!={origin}"
        ),
    )

    require(
        not status_paths(),
        "POST_PUSH_WORKTREE_NOT_CLEAN",
    )

    return head


def run_collector(
    *,
    target_matured: int,
    poll_seconds: int,
    retry_seconds: int,
) -> int:

    require(
        target_matured > 0,
        "TARGET_MATURED_MUST_BE_POSITIVE",
    )

    require(
        poll_seconds >= 10,
        "POLL_SECONDS_TOO_SMALL",
    )

    require(
        retry_seconds >= 10,
        "RETRY_SECONDS_TOO_SMALL",
    )

    require(
        not PERFORMANCE_EVALUATION_AUTHORIZED,
        "PERFORMANCE_AUTHORIZED",
    )

    require(
        not PNL_EVALUATION_AUTHORIZED,
        "PNL_AUTHORIZED",
    )

    require(
        not LIVE_AUTHORIZED,
        "LIVE_AUTHORIZED",
    )

    require(
        not EXECUTION_AUTHORIZED,
        "EXECUTION_AUTHORIZED",
    )

    verify_clean_synced_repository(
        retry_seconds=retry_seconds,
    )

    append_log(
        "G4_1_START "
        f"target_matured={target_matured} "
        f"poll_seconds={poll_seconds} "
        f"retry_seconds={retry_seconds}"
    )

    while True:

        g3 = run_g3_resilient(
            retry_seconds=retry_seconds,
        )

        matured = parse_positive_int(
            g3,
            "MATURED_COUNT",
        )

        pending = parse_positive_int(
            g3,
            "PENDING_COUNT",
        )

        action = g3.get(
            "NEXT_ACTION",
            "",
        )

        print(
            "G4_1_STATUS "
            f"matured={matured}/{target_matured} "
            f"pending={pending} "
            f"next_action={action}",
            flush=True,
        )

        append_log(
            "G4_1_STATE "
            f"matured={matured}/{target_matured} "
            f"pending={pending} "
            f"next_action={action}"
        )

        if matured >= target_matured:

            append_log(
                "G4_1_TARGET_REACHED"
            )

            print(
                "G4_1_AUTONOMOUS_COLLECTOR_STATUS="
                "TARGET_REACHED"
            )

            print(
                f"MATURED_COUNT={matured}"
            )

            print(
                "TARGET_MATURED_SAMPLES="
                f"{target_matured}"
            )

            print(
                "PERFORMANCE_EVALUATED=false"
            )

            print(
                "PNL_EVALUATED=false"
            )

            print(
                "LIVE_AUTHORIZED=false"
            )

            print(
                "EXECUTION_AUTHORIZED=false"
            )

            return 0

        if action == "RUN_G1_CAPTURE":

            require(
                pending == 0,
                "G1_REQUESTED_WITH_PENDING_SAMPLE",
            )

            g1 = run_g1()

            observation_id = g1.get(
                "LOGICAL_OBSERVATION_ID",
                "",
            )

            require(
                len(observation_id) == 64,
                "G1_OBSERVATION_ID_INVALID",
            )

            append_log(
                "G1_CAPTURED "
                f"observation_id={observation_id}"
            )

            commit_and_push_expected_evidence(
                G1_EVIDENCE_REL,
                message=(
                    "evidence(shadow): "
                    "record resilient autonomous "
                    "anchored capture "
                    f"{observation_id[:12]}"
                ),
                retry_seconds=retry_seconds,
            )

            continue

        if action == "WAIT_FOR_MATURATION":

            require(
                pending == 1,
                "WAIT_WITH_UNEXPECTED_PENDING_COUNT",
            )

            append_log(
                "WAIT "
                "available_future_m5_bars="
                f"{g3.get('AVAILABLE_FUTURE_M5_BARS', '?')} "
                "missing_future_m5_bars="
                f"{g3.get('MISSING_FUTURE_M5_BARS', '?')}"
            )

            time.sleep(
                poll_seconds
            )

            continue

        if action == "RUN_G2_APPEND":

            require(
                pending == 1,
                "G2_REQUESTED_WITH_UNEXPECTED_PENDING_COUNT",
            )

            observation_id = g3.get(
                "TARGET_LOGICAL_OBSERVATION_ID",
                "",
            )

            require(
                len(observation_id) == 64,
                "G2_TARGET_OBSERVATION_ID_INVALID",
            )

            dry = run_g2_dry(
                observation_id
            )

            outcome_class = dry.get(
                "OUTCOME_CLASS",
                "",
            )

            outcome_label = dry.get(
                "OUTCOME_LABEL",
                "",
            )

            append_log(
                "G2_DRY_PASS "
                f"observation_id={observation_id} "
                f"outcome_class={outcome_class} "
                f"outcome_label={outcome_label}"
            )

            first = run_g2_first_append(
                observation_id
            )

            require(
                first.get(
                    "OUTCOME_CLASS"
                )
                ==
                outcome_class,
                "G2_OUTCOME_CLASS_CHANGED_BETWEEN_DRY_AND_APPEND",
            )

            require(
                first.get(
                    "OUTCOME_LABEL"
                )
                ==
                outcome_label,
                "G2_OUTCOME_LABEL_CHANGED_BETWEEN_DRY_AND_APPEND",
            )

            duplicate = run_g2_idempotency(
                observation_id
            )

            require(
                duplicate.get(
                    "OUTCOME_CLASS"
                )
                ==
                outcome_class,
                "G2_OUTCOME_CLASS_CHANGED_AT_IDEMPOTENCY",
            )

            require(
                duplicate.get(
                    "OUTCOME_LABEL"
                )
                ==
                outcome_label,
                "G2_OUTCOME_LABEL_CHANGED_AT_IDEMPOTENCY",
            )

            commit_and_push_expected_evidence(
                G2_EVIDENCE_REL,
                message=(
                    "evidence(shadow): "
                    "record resilient autonomous "
                    "outcome idempotency "
                    f"{observation_id[:12]}"
                ),
                retry_seconds=retry_seconds,
            )

            continue

        raise G41CollectorError(
            "UNKNOWN_G3_NEXT_ACTION:"
            f"{action}"
        )


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--target-matured",
        type=int,
        default=DEFAULT_TARGET_MATURED,
    )

    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=DEFAULT_POLL_SECONDS,
    )

    parser.add_argument(
        "--retry-seconds",
        type=int,
        default=DEFAULT_RETRY_SECONDS,
    )

    return parser.parse_args()


def main() -> int:

    args = parse_args()

    try:

        return run_collector(
            target_matured=int(
                args.target_matured
            ),
            poll_seconds=int(
                args.poll_seconds
            ),
            retry_seconds=int(
                args.retry_seconds
            ),
        )

    except KeyboardInterrupt:

        append_log(
            "G4_1_STOPPED_BY_USER"
        )

        print(
            "G4_1_AUTONOMOUS_COLLECTOR_STATUS="
            "STOPPED_BY_USER"
        )

        print(
            "PERFORMANCE_EVALUATED=false"
        )

        print(
            "PNL_EVALUATED=false"
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 130

    except Exception as exc:

        append_log(
            "G4_1_BLOCKED "
            f"error_type={type(exc).__name__} "
            f"error={str(exc)[:2000]}"
        )

        print(
            "G4_1_AUTONOMOUS_COLLECTOR_STATUS="
            "BLOCKED"
        )

        print(
            "ERROR_TYPE="
            + type(exc).__name__
        )

        print(
            "ERROR="
            + str(exc)
        )

        print(
            "PERFORMANCE_EVALUATED=false"
        )

        print(
            "PNL_EVALUATED=false"
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 2


if __name__ == "__main__":
    raise SystemExit(
        main()
    )