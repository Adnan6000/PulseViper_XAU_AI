from __future__ import annotations
import importlib.util
from pathlib import Path
from typing import Any
MODULE_PATH=Path(__file__).resolve().parent/"run_xauusd_gate_15d_c_b2d_g4_autonomous_forward_collector.py"
spec=importlib.util.spec_from_file_location("g4_collector",MODULE_PATH); assert spec and spec.loader
g4: Any=importlib.util.module_from_spec(spec); spec.loader.exec_module(g4)
def test_01_defaults_are_safe():
    assert g4.DEFAULT_TARGET_MATURED==30 and g4.DEFAULT_POLL_SECONDS>=10
    assert g4.PERFORMANCE_EVALUATION_AUTHORIZED is False and g4.PNL_EVALUATION_AUTHORIZED is False and g4.LIVE_AUTHORIZED is False and g4.EXECUTION_AUTHORIZED is False
def test_02_master_log_is_shadow_runtime_artifact():
    n=str(g4.LOG_PATH).replace("\\","/"); assert "/01_Data/Shadow/" in n and n.endswith(".log")
def test_03_parse_kv(): assert g4.parse_kv("A=1\nB=true\nX\nC=hello=world\n")=={"A":"1","B":"true","C":"hello=world"}
def test_04_common_safety_accepts_false_flags(): g4.verify_common_safety({"LIVE_AUTHORIZED":"false","EXECUTION_AUTHORIZED":"false","FORWARD_PERFORMANCE_EVALUATED":"false"})
def test_05_common_safety_rejects_live_true():
    try: g4.verify_common_safety({"LIVE_AUTHORIZED":"true","EXECUTION_AUTHORIZED":"false"})
    except g4.G4CollectorError: return
    raise AssertionError("Expected fail-closed rejection")
def test_06_positive_int_parser(): assert g4.parse_positive_int({"X":"0"},"X")==0 and g4.parse_positive_int({"X":"30"},"X")==30
def test_07_positive_int_parser_rejects_negative():
    try: g4.parse_positive_int({"X":"-1"},"X")
    except g4.G4CollectorError: return
    raise AssertionError("Expected rejection")
def test_08_expected_evidence_paths_are_narrow():
    assert g4.G1_EVIDENCE_REL.endswith("g1_genuine_anchored_forward_capture_evidence.json")
    assert g4.G2_EVIDENCE_REL.endswith("g2_genuine_outcome_maturation_evidence.json")
def test_09_no_force_push_literal():
    s=MODULE_PATH.read_text(encoding="utf-8"); assert "push --force" not in s and "--force-with-lease" not in s and 'git("push","origin","main"' in s
def test_10_no_order_api_literals():
    s=MODULE_PATH.read_text(encoding="utf-8")
    for t in ("order_send(","order_check(","order_calc_margin(","order_calc_profit(","positions_get(","orders_get(","history_orders_get(","history_deals_get("): assert t not in s
def test_11_thin_orchestrator():
    s=MODULE_PATH.read_text(encoding="utf-8"); assert "G1_RUNNER" in s and "G2_RUNNER" in s and "G3_RUNNER" in s and "MetaTrader5" not in s
def test_12_wait_requires_single_pending():
    s=MODULE_PATH.read_text(encoding="utf-8"); assert 'require(pending==1,"WAIT_WITH_UNEXPECTED_PENDING_COUNT")' in s
def test_13_g2_sequence_is_dry_append_duplicate():
    s=MODULE_PATH.read_text(encoding="utf-8"); assert s.index("dry=run_g2_dry(obs)") < s.index("first=run_g2_first_append(obs)") < s.index("dup=run_g2_idempotency(obs)")
def test_14_target_reached_stops_without_performance():
    s=MODULE_PATH.read_text(encoding="utf-8"); assert "if matured>=target_matured:" in s and 'print("PERFORMANCE_EVALUATED=false")' in s and 'print("PNL_EVALUATED=false")' in s
def test_15_remote_movement_is_fail_closed():
    s=MODULE_PATH.read_text(encoding="utf-8"); assert "REMOTE_MOVED_BEFORE_EVIDENCE_COMMIT" in s and "REMOTE_MOVED_AFTER_LOCAL_COMMIT" in s
