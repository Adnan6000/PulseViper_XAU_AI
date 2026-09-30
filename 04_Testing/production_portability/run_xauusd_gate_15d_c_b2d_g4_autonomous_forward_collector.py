"""Gate 15D-C-B2D-G4 — Autonomous Prospective Sample Collector."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess, sys, time
from typing import Mapping

REPO_ROOT = Path(__file__).resolve().parents[2]
G1_RUNNER = REPO_ROOT / "04_Testing/production_portability/run_xauusd_gate_15d_c_b2d_g1_genuine_anchored_forward_capture.py"
G2_RUNNER = REPO_ROOT / "04_Testing/production_portability/run_xauusd_gate_15d_c_b2d_g2_genuine_outcome_maturation.py"
G3_RUNNER = REPO_ROOT / "04_Testing/production_portability/run_xauusd_gate_15d_c_b2d_g3_forward_sample_controller.py"
G1_EVIDENCE_REL = "04_Testing/evidence/forward_shadow/xauusd_gate_15d_c_b2d_g1_genuine_anchored_forward_capture_evidence.json"
G2_EVIDENCE_REL = "04_Testing/evidence/forward_shadow/xauusd_gate_15d_c_b2d_g2_genuine_outcome_maturation_evidence.json"
LOG_PATH = REPO_ROOT / "01_Data/Shadow/xauusd_g4_autonomous_collector.log"
DEFAULT_TARGET_MATURED = 30
DEFAULT_POLL_SECONDS = 60
PERFORMANCE_EVALUATION_AUTHORIZED = False
PNL_EVALUATION_AUTHORIZED = False
LIVE_AUTHORIZED = False
EXECUTION_AUTHORIZED = False

class G4CollectorError(RuntimeError): pass

def require(condition: bool, reason: str) -> None:
    if not condition: raise G4CollectorError(reason)

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def append_log(message: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8", newline="\n") as h:
        h.write(f"[{utc_now()}] {message}\n"); h.flush()

def run_process(args: list[str], *, check: bool=False) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    append_log("COMMAND=" + " ".join(args) + f" RETURN_CODE={p.returncode}")
    if p.stdout:
        append_log("STDOUT_BEGIN")
        for line in p.stdout.rstrip().splitlines(): append_log(line)
        append_log("STDOUT_END")
    if p.stderr:
        append_log("STDERR_BEGIN")
        for line in p.stderr.rstrip().splitlines(): append_log(line)
        append_log("STDERR_END")
    if check: require(p.returncode == 0, "COMMAND_FAILED:" + " ".join(args))
    return p

def git(*args: str, check: bool=True) -> subprocess.CompletedProcess[str]: return run_process(["git", *args], check=check)
def git_output(*args: str) -> str: return git(*args).stdout.rstrip("\r\n")

def normalize_status_path(line: str) -> str:
    value=line[3:].strip()
    if " -> " in value: value=value.split(" -> ",1)[1]
    if value.startswith('"') and value.endswith('"'): value=value[1:-1]
    return value.replace("\\","/")

def status_paths() -> set[str]:
    out=git_output("status","--porcelain","--untracked-files=all")
    return {normalize_status_path(x) for x in out.splitlines() if len(x)>=4}

def verify_clean_synced_repository() -> str:
    git("fetch","origin")
    branch=git_output("branch","--show-current"); head=git_output("rev-parse","HEAD"); origin=git_output("rev-parse","origin/main")
    require(branch=="main",f"UNEXPECTED_BRANCH:{branch}")
    require(head==origin,f"HEAD_ORIGIN_MAIN_DIVERGENCE:{head}!={origin}")
    dirty=status_paths(); require(not dirty,f"WORKTREE_NOT_CLEAN:{sorted(dirty)}")
    return head

def parse_kv(stdout: str) -> dict[str,str]:
    result={}
    for raw in stdout.splitlines():
        line=raw.strip()
        if "=" not in line: continue
        k,v=line.split("=",1)
        if k and v: result[k.strip()]=v.strip()
    return result

def run_python(path: Path,*args: str):
    p=run_process([sys.executable,str(path),*args],check=False)
    return p,parse_kv(p.stdout)

def require_false(data: Mapping[str,str], key: str) -> None:
    require(data.get(key,"").lower()=="false",f"{key}_NOT_FALSE:{data.get(key)}")

def verify_common_safety(data: Mapping[str,str]) -> None:
    for k in ("LIVE_AUTHORIZED","EXECUTION_AUTHORIZED"): require_false(data,k)
    if "FORWARD_PERFORMANCE_EVALUATED" in data: require_false(data,"FORWARD_PERFORMANCE_EVALUATED")
    if "PERFORMANCE_EVALUATED" in data: require_false(data,"PERFORMANCE_EVALUATED")
    if "PNL_EVALUATED" in data: require_false(data,"PNL_EVALUATED")

def commit_and_push_expected_evidence(expected_rel: str, *, message: str) -> str:
    dirty=status_paths(); require(dirty=={expected_rel},f"UNEXPECTED_DIRTY_PATHS:{sorted(dirty)}")
    git("fetch","origin")
    head_before=git_output("rev-parse","HEAD"); origin_before=git_output("rev-parse","origin/main")
    require(head_before==origin_before,f"REMOTE_MOVED_BEFORE_EVIDENCE_COMMIT:{head_before}!={origin_before}")
    git("add","--",expected_rel)
    chk=git("diff","--cached","--check",check=False); require(chk.returncode==0,"CACHED_DIFF_CHECK_FAILED")
    staged={x.strip().replace("\\","/") for x in git_output("diff","--cached","--name-only").splitlines() if x.strip()}
    require(staged=={expected_rel},f"UNEXPECTED_STAGED_PATHS:{sorted(staged)}")
    c=git("commit","-m",message,check=False); require(c.returncode==0,"EVIDENCE_COMMIT_FAILED")
    git("fetch","origin")
    parent=git_output("rev-parse","HEAD^"); origin_now=git_output("rev-parse","origin/main")
    require(parent==origin_now,f"REMOTE_MOVED_AFTER_LOCAL_COMMIT:{parent}!={origin_now}")
    p=git("push","origin","main",check=False); require(p.returncode==0,"EVIDENCE_PUSH_FAILED")
    head=git_output("rev-parse","HEAD"); origin=git_output("rev-parse","origin/main")
    require(head==origin,f"POST_PUSH_DIVERGENCE:{head}!={origin}"); require(not status_paths(),"POST_PUSH_WORKTREE_NOT_CLEAN")
    return head

def run_g3() -> dict[str,str]:
    p,d=run_python(G3_RUNNER); require(p.returncode==0,"G3_PROCESS_FAILED"); require(d.get("GATE_15D_C_B2D_G3_STATUS")=="PASS","G3_NOT_PASS"); verify_common_safety(d); return d

def run_g1() -> dict[str,str]:
    p,d=run_python(G1_RUNNER); require(p.returncode==0,"G1_PROCESS_FAILED"); require(d.get("GATE_15D_C_B2D_G1_STATUS")=="PASS","G1_NOT_PASS")
    require(d.get("GENUINE_MT5_ACQUISITION","").lower()=="true","G1_NOT_GENUINE_MT5")
    require(d.get("ANCHOR_APPENDED","").lower()=="true","G1_ANCHOR_NOT_APPENDED")
    require(d.get("OBSERVATION_APPENDED","").lower()=="true","G1_OBSERVATION_NOT_APPENDED")
    require(d.get("OUTCOME_LEDGER_UNCHANGED","").lower()=="true","G1_OUTCOME_LEDGER_CHANGED"); verify_common_safety(d); return d

def run_g2_dry(obs: str) -> dict[str,str]:
    p,d=run_python(G2_RUNNER,"--observation-id",obs); require(p.returncode==0,"G2_DRY_PROCESS_FAILED"); require(d.get("GATE_15D_C_B2D_G2_STATUS")=="PASS","G2_DRY_NOT_PASS")
    require(d.get("MODE")=="DRY_RUN","G2_DRY_MODE_MISMATCH"); require(d.get("HORIZON_BARS")=="12","G2_DRY_HORIZON_MISMATCH")
    require(d.get("OUTCOME_APPENDED","").lower()=="false","G2_DRY_APPENDED_OUTCOME"); require(d.get("OUTCOME_IDEMPOTENT_DUPLICATE","").lower()=="false","G2_DRY_UNEXPECTED_DUPLICATE"); verify_common_safety(d); return d

def run_g2_first_append(obs: str) -> dict[str,str]:
    p,d=run_python(G2_RUNNER,"--observation-id",obs,"--append-outcome"); require(p.returncode==0,"G2_APPEND_PROCESS_FAILED"); require(d.get("GATE_15D_C_B2D_G2_STATUS")=="PASS","G2_APPEND_NOT_PASS")
    require(d.get("MODE")=="APPEND_OUTCOME","G2_APPEND_MODE_MISMATCH"); require(d.get("HORIZON_BARS")=="12","G2_APPEND_HORIZON_MISMATCH")
    require(d.get("OUTCOME_APPENDED","").lower()=="true","G2_FIRST_APPEND_NOT_TRUE"); require(d.get("OUTCOME_IDEMPOTENT_DUPLICATE","").lower()=="false","G2_FIRST_APPEND_UNEXPECTED_DUPLICATE"); verify_common_safety(d); return d

def run_g2_idempotency(obs: str) -> dict[str,str]:
    p,d=run_python(G2_RUNNER,"--observation-id",obs,"--append-outcome"); require(p.returncode==0,"G2_IDEMPOTENCY_PROCESS_FAILED"); require(d.get("GATE_15D_C_B2D_G2_STATUS")=="PASS","G2_IDEMPOTENCY_NOT_PASS")
    require(d.get("OUTCOME_APPENDED","").lower()=="false","G2_IDEMPOTENCY_APPENDED_DUPLICATE"); require(d.get("OUTCOME_IDEMPOTENT_DUPLICATE","").lower()=="true","G2_IDEMPOTENCY_NOT_CONFIRMED"); verify_common_safety(d); return d

def parse_positive_int(data: Mapping[str,str], key: str) -> int:
    try: value=int(data[key])
    except Exception as exc: raise G4CollectorError(f"INVALID_INTEGER:{key}:{data.get(key)}") from exc
    require(value>=0,f"NEGATIVE_INTEGER:{key}:{value}"); return value

def run_collector(*, target_matured: int, poll_seconds: int) -> int:
    require(target_matured>0,"TARGET_MATURED_MUST_BE_POSITIVE"); require(poll_seconds>=10,"POLL_SECONDS_TOO_SMALL")
    require(not PERFORMANCE_EVALUATION_AUTHORIZED,"PERFORMANCE_AUTHORIZED"); require(not PNL_EVALUATION_AUTHORIZED,"PNL_AUTHORIZED"); require(not LIVE_AUTHORIZED,"LIVE_AUTHORIZED"); require(not EXECUTION_AUTHORIZED,"EXECUTION_AUTHORIZED")
    verify_clean_synced_repository(); append_log(f"G4_START target_matured={target_matured} poll_seconds={poll_seconds}")
    while True:
        g3=run_g3(); matured=parse_positive_int(g3,"MATURED_COUNT"); pending=parse_positive_int(g3,"PENDING_COUNT"); action=g3.get("NEXT_ACTION","")
        print(f"G4_STATUS matured={matured}/{target_matured} pending={pending} next_action={action}",flush=True); append_log(f"G4_STATE matured={matured}/{target_matured} pending={pending} next_action={action}")
        if matured>=target_matured:
            append_log("G4_TARGET_REACHED"); print("G4_AUTONOMOUS_COLLECTOR_STATUS=TARGET_REACHED"); print(f"MATURED_COUNT={matured}"); print(f"TARGET_MATURED_SAMPLES={target_matured}"); print("PERFORMANCE_EVALUATED=false"); print("PNL_EVALUATED=false"); print("LIVE_AUTHORIZED=false"); print("EXECUTION_AUTHORIZED=false"); return 0
        if action=="RUN_G1_CAPTURE":
            require(pending==0,"G1_REQUESTED_WITH_PENDING_SAMPLE"); g1=run_g1(); obs=g1.get("LOGICAL_OBSERVATION_ID",""); require(len(obs)==64,"G1_OBSERVATION_ID_INVALID"); append_log(f"G1_CAPTURED observation_id={obs}")
            commit_and_push_expected_evidence(G1_EVIDENCE_REL,message=f"evidence(shadow): record autonomous anchored capture {obs[:12]}"); continue
        if action=="WAIT_FOR_MATURATION":
            require(pending==1,"WAIT_WITH_UNEXPECTED_PENDING_COUNT"); append_log(f"WAIT available_future_m5_bars={g3.get('AVAILABLE_FUTURE_M5_BARS','?')} missing_future_m5_bars={g3.get('MISSING_FUTURE_M5_BARS','?')}"); time.sleep(poll_seconds); continue
        if action=="RUN_G2_APPEND":
            require(pending==1,"G2_REQUESTED_WITH_UNEXPECTED_PENDING_COUNT"); obs=g3.get("TARGET_LOGICAL_OBSERVATION_ID",""); require(len(obs)==64,"G2_TARGET_OBSERVATION_ID_INVALID")
            dry=run_g2_dry(obs); cls=dry.get("OUTCOME_CLASS",""); label=dry.get("OUTCOME_LABEL",""); append_log(f"G2_DRY_PASS observation_id={obs} outcome_class={cls} outcome_label={label}")
            first=run_g2_first_append(obs); require(first.get("OUTCOME_CLASS")==cls,"G2_OUTCOME_CLASS_CHANGED_BETWEEN_DRY_AND_APPEND"); require(first.get("OUTCOME_LABEL")==label,"G2_OUTCOME_LABEL_CHANGED_BETWEEN_DRY_AND_APPEND")
            dup=run_g2_idempotency(obs); require(dup.get("OUTCOME_CLASS")==cls,"G2_OUTCOME_CLASS_CHANGED_AT_IDEMPOTENCY"); require(dup.get("OUTCOME_LABEL")==label,"G2_OUTCOME_LABEL_CHANGED_AT_IDEMPOTENCY")
            commit_and_push_expected_evidence(G2_EVIDENCE_REL,message=f"evidence(shadow): record autonomous outcome idempotency {obs[:12]}"); continue
        raise G4CollectorError(f"UNKNOWN_G3_NEXT_ACTION:{action}")

def parse_args() -> argparse.Namespace:
    p=argparse.ArgumentParser(); p.add_argument("--target-matured",type=int,default=DEFAULT_TARGET_MATURED); p.add_argument("--poll-seconds",type=int,default=DEFAULT_POLL_SECONDS); return p.parse_args()

def main() -> int:
    args=parse_args()
    try: return run_collector(target_matured=int(args.target_matured),poll_seconds=int(args.poll_seconds))
    except KeyboardInterrupt:
        append_log("G4_STOPPED_BY_USER"); print("G4_AUTONOMOUS_COLLECTOR_STATUS=STOPPED_BY_USER"); print("PERFORMANCE_EVALUATED=false"); print("PNL_EVALUATED=false"); print("LIVE_AUTHORIZED=false"); print("EXECUTION_AUTHORIZED=false"); return 130
    except Exception as exc:
        append_log(f"G4_BLOCKED error_type={type(exc).__name__} error={str(exc)[:2000]}"); print("G4_AUTONOMOUS_COLLECTOR_STATUS=BLOCKED"); print("ERROR_TYPE="+type(exc).__name__); print("ERROR="+str(exc)); print("PERFORMANCE_EVALUATED=false"); print("PNL_EVALUATED=false"); print("LIVE_AUTHORIZED=false"); print("EXECUTION_AUTHORIZED=false"); return 2

if __name__=="__main__": raise SystemExit(main())
