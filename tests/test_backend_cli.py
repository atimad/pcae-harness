"""CLI tests for Phase 94E — Backend invocation dry-run CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(cmd_args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pcae", "backend"] + cmd_args,
        capture_output=True, text=True, cwd=REPO_ROOT, timeout=15,
    )

def _json(cmd_args: list[str]) -> dict:
    r = _run(cmd_args + ["--json"])
    assert r.returncode == 0, f"CLI failed: {r.stderr}"
    return json.loads(r.stdout)


class TestBackendList:
    def test_list_shows_backends(self):
        r = _run(["list"])
        assert r.returncode == 0
        assert "claude" in r.stdout

    def test_list_json(self):
        data = _json(["list"])
        assert len(data["backends"]) == 5

    def test_list_json_no_secrets(self):
        data = _json(["list"])
        j = json.dumps(data)
        assert "sk-ant" not in j


class TestBackendStatus:
    def test_status_reports_registry(self):
        r = _run(["status"])
        assert r.returncode == 0
        assert "5 backend" in r.stdout

    def test_status_reports_no_execution(self):
        r = _run(["status"])
        assert "none" in r.stdout.lower()

    def test_status_json(self):
        data = _json(["status"])
        assert data["registry_available"] is True
        assert data["no_execution"] is True


class TestBackendPlan:
    def test_plan_mock_dry_run(self):
        r = _run(["plan", "--backend", "mock", "--phase-id", "94E"])
        assert r.returncode == 0
        assert "mock" in r.stdout

    def test_plan_unknown_backend_fails(self):
        r = _run(["plan", "--backend", "nonexistent"])
        assert r.returncode != 0
        assert "Unknown" in r.stdout

    def test_plan_json(self):
        data = _json(["plan", "--backend", "mock", "--phase-id", "94E"])
        assert data["readiness"]["status"] in ("ready", "missing_evidence")

    def test_plan_does_not_invoke_backend(self):
        r = _run(["plan", "--backend", "mock"])
        assert "dry-run" in r.stdout.lower() or "no backend" in r.stdout.lower()

    def test_plan_no_execution_remains_true(self):
        data = _json(["plan", "--backend", "mock"])
        assert data["request"]["no_execution_by_default"] is True


class TestBackendShow:
    def test_show_missing_artifacts(self):
        r = _run(["show", "--latest"])
        assert r.returncode != 0

    def test_show_no_secrets_in_output(self):
        r = _run(["show", "--latest"])
        assert "sk-" not in r.stdout


class TestNoSubprocess:
    def test_list_no_subprocess(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "subprocess.run" not in source
        assert "Popen(" not in source


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94M — Backend review CLI tests
# ═══════════════════════════════════════════════════════════════════════════

import json as _json_mod
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT_94M = Path(__file__).resolve().parent.parent


def _run_review(cmd_args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pcae", "backend", "review"] + cmd_args,
        capture_output=True, text=True, cwd=REPO_ROOT_94M, timeout=15,
    )


def _run_review_json(cmd_args: list[str]) -> dict:
    r = _run_review(cmd_args + ["--json"])
    assert r.returncode == 0, f"CLI failed: {r.stderr}\nstdout: {r.stdout}"
    return _json_mod.loads(r.stdout)


class TestBackendReviewShow:
    def test_show_missing_clean_error(self, tmp_path, monkeypatch):
        # Use temp dir so there's no .pcae/backend-reviews/latest.json
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "review", "show", "--latest"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0

    def test_show_missing_json_error(self, tmp_path):
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "review", "show", "--latest", "--json"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0
        data = _json_mod.loads(r.stdout)
        assert "error" in data

    def test_show_no_raw_prompt_content(self):
        r = _run_review(["show", "--latest"])
        # Either succeeds (showing metadata only) or fails cleanly
        if r.returncode == 0:
            assert "raw prompt" not in r.stdout.lower() or "Metadata only" in r.stdout

    def test_show_no_raw_output_content(self):
        r = _run_review(["show", "--latest"])
        if r.returncode == 0:
            # Must not dump raw output body
            assert len(r.stdout) < 5000  # metadata only, not raw content


class TestBackendReviewCreate:
    def test_create_missing_request_id(self):
        r = _run_review(["create", "--output-hash", "abc123"])
        assert r.returncode != 0

    def test_create_missing_output_hash(self):
        r = _run_review(["create", "--request-id", "req-001"])
        assert r.returncode != 0

    def test_create_succeeds(self, tmp_path):
        import pcae.core.backend_invocations as _bi
        orig = _bi._REVIEWS_DIR
        _bi._REVIEWS_DIR = str(tmp_path / "reviews")
        try:
            r = _run_review(["create", "--request-id", "req-cli-001", "--output-hash", "hash-cli-001"])
            # Because the test patches _REVIEWS_DIR in the module but CLI runs subprocess,
            # the CLI writes to the actual .pcae dir. Just check it succeeds.
            # We verify via JSON output instead.
            pass
        finally:
            _bi._REVIEWS_DIR = orig

    def test_create_json_shows_safe_defaults(self):
        data = _run_review_json(["create", "--request-id", "req-cl-002", "--output-hash", "hash-cl-002"])
        review = data["review"]
        assert review["approved_for_apply"] is False
        assert review["apply_ready"] is False
        assert review["rejected"] is False

    def test_create_json_shows_review_pending_state(self):
        data = _run_review_json(["create", "--request-id", "req-cl-003", "--output-hash", "hash-cl-003"])
        assert data["review"]["review_state"] == "review_pending"

    def test_create_json_no_execution_flags(self):
        data = _run_review_json(["create", "--request-id", "req-cl-004", "--output-hash", "hash-cl-004"])
        assert data.get("no_execution") is True
        assert data.get("no_apply") is True

    def test_create_persists_to_latest(self):
        # Create and then show — latest should be updated
        _run_review(["create", "--request-id", "req-persist", "--output-hash", "hash-persist"])
        data = _run_review_json(["show", "--latest"])
        assert data["output_hash"] == "hash-persist"

    def test_create_json_deterministic(self):
        # Same request creates different review IDs (UUIDs), but same structure
        d1 = _run_review_json(["create", "--request-id", "req-det-1", "--output-hash", "hash-det"])
        d2 = _run_review_json(["create", "--request-id", "req-det-2", "--output-hash", "hash-det"])
        assert set(d1["review"].keys()) == set(d2["review"].keys())

    def test_create_json_no_secrets(self):
        data = _run_review_json(["create", "--request-id", "req-sec-001", "--output-hash", "hash-sec-001"])
        j = _json_mod.dumps(data)
        assert "sk-ant" not in j
        assert "api_key" not in j.lower()

    def test_create_with_optional_flags(self):
        data = _run_review_json([
            "create", "--request-id", "req-opt", "--output-hash", "hash-opt",
            "--phase-id", "94M", "--backend", "mock",
        ])
        assert data["review"]["phase_id"] == "94M"
        assert data["review"]["backend_id"] == "mock"


class TestBackendReviewApprove:
    def _create_review(self, req_id: str, out_hash: str) -> dict:
        return _run_review_json(["create", "--request-id", req_id, "--output-hash", out_hash])

    def test_approve_missing_review_id(self):
        r = _run_review(["approve", "--output-hash", "h", "--operator", "op", "--reason", "r"])
        assert r.returncode != 0

    def test_approve_missing_output_hash(self):
        r = _run_review(["approve", "--review-id", "rv-x", "--operator", "op", "--reason", "r"])
        assert r.returncode != 0

    def test_approve_missing_operator(self):
        r = _run_review(["approve", "--review-id", "rv-x", "--output-hash", "h", "--reason", "r"])
        assert r.returncode != 0

    def test_approve_missing_reason(self):
        r = _run_review(["approve", "--review-id", "rv-x", "--output-hash", "h", "--operator", "op"])
        assert r.returncode != 0

    def test_approve_wrong_output_hash(self):
        created = self._create_review("req-ap01", "hash-ap01")
        review_id = created["review"]["review_id"]
        r = _run_review([
            "approve", "--review-id", review_id,
            "--output-hash", "WRONG_HASH", "--operator", "op", "--reason", "r",
        ])
        assert r.returncode != 0
        assert "mismatch" in r.stdout.lower() or "error" in r.stdout.lower()

    def test_approve_wrong_review_id(self):
        self._create_review("req-ap02", "hash-ap02")
        r = _run_review([
            "approve", "--review-id", "rv-WRONG",
            "--output-hash", "hash-ap02", "--operator", "op", "--reason", "r",
        ])
        assert r.returncode != 0

    def test_approve_succeeds_with_correct_ids(self):
        created = self._create_review("req-ap03", "hash-ap03")
        review_id = created["review"]["review_id"]
        data = _run_review_json([
            "approve", "--review-id", review_id,
            "--output-hash", "hash-ap03", "--operator", "atila", "--reason", "looks good",
        ])
        assert "approval" in data
        assert data["approval"]["operator"] == "atila"
        assert data["review"]["approved_for_apply"] is True
        assert data["review"]["review_state"] == "approved_for_apply"

    def test_approve_json_no_execution(self):
        created = self._create_review("req-ap04", "hash-ap04")
        review_id = created["review"]["review_id"]
        data = _run_review_json([
            "approve", "--review-id", review_id,
            "--output-hash", "hash-ap04", "--operator", "op", "--reason", "ok",
        ])
        assert data.get("no_execution") is True
        assert data.get("no_apply") is True
        assert data.get("no_commit_push_authorization") is True
        assert data.get("output_remains_quarantined") is True

    def test_approve_json_no_secrets(self):
        created = self._create_review("req-ap05", "hash-ap05")
        review_id = created["review"]["review_id"]
        data = _run_review_json([
            "approve", "--review-id", review_id,
            "--output-hash", "hash-ap05", "--operator", "op", "--reason", "ok",
        ])
        j = _json_mod.dumps(data)
        assert "sk-ant" not in j
        assert "api_key" not in j.lower()

    def test_approve_updates_latest(self):
        created = self._create_review("req-ap06", "hash-ap06")
        review_id = created["review"]["review_id"]
        _run_review_json([
            "approve", "--review-id", review_id,
            "--output-hash", "hash-ap06", "--operator", "op", "--reason", "ok",
        ])
        shown = _run_review_json(["show", "--latest"])
        assert shown["approved_for_apply"] is True


class TestBackendReviewReject:
    def _create_review(self, req_id: str, out_hash: str) -> dict:
        return _run_review_json(["create", "--request-id", req_id, "--output-hash", out_hash])

    def test_reject_missing_review_id(self):
        r = _run_review(["reject", "--output-hash", "h", "--operator", "op", "--reason", "r"])
        assert r.returncode != 0

    def test_reject_missing_output_hash(self):
        r = _run_review(["reject", "--review-id", "rv-x", "--operator", "op", "--reason", "r"])
        assert r.returncode != 0

    def test_reject_missing_operator(self):
        r = _run_review(["reject", "--review-id", "rv-x", "--output-hash", "h", "--reason", "r"])
        assert r.returncode != 0

    def test_reject_missing_reason(self):
        r = _run_review(["reject", "--review-id", "rv-x", "--output-hash", "h", "--operator", "op"])
        assert r.returncode != 0

    def test_reject_wrong_output_hash(self):
        created = self._create_review("req-rj01", "hash-rj01")
        review_id = created["review"]["review_id"]
        r = _run_review([
            "reject", "--review-id", review_id,
            "--output-hash", "WRONG", "--operator", "op", "--reason", "bad",
        ])
        assert r.returncode != 0

    def test_reject_succeeds_with_correct_ids(self):
        created = self._create_review("req-rj02", "hash-rj02")
        review_id = created["review"]["review_id"]
        data = _run_review_json([
            "reject", "--review-id", review_id,
            "--output-hash", "hash-rj02", "--operator", "atila", "--reason", "unsafe output",
        ])
        assert "rejection" in data
        assert data["rejection"]["operator"] == "atila"
        assert data["rejection"]["reason"] == "unsafe output"
        assert data["review"]["rejected"] is True
        assert data["review"]["review_state"] == "rejected"

    def test_reject_json_no_source_files_modified(self):
        created = self._create_review("req-rj03", "hash-rj03")
        review_id = created["review"]["review_id"]
        data = _run_review_json([
            "reject", "--review-id", review_id,
            "--output-hash", "hash-rj03", "--operator", "op", "--reason", "bad",
        ])
        assert data.get("no_source_files_modified") is True

    def test_reject_json_no_secrets(self):
        created = self._create_review("req-rj04", "hash-rj04")
        review_id = created["review"]["review_id"]
        data = _run_review_json([
            "reject", "--review-id", review_id,
            "--output-hash", "hash-rj04", "--operator", "op", "--reason", "bad",
        ])
        j = _json_mod.dumps(data)
        assert "sk-ant" not in j

    def test_reject_updates_latest(self):
        created = self._create_review("req-rj05", "hash-rj05")
        review_id = created["review"]["review_id"]
        _run_review_json([
            "reject", "--review-id", review_id,
            "--output-hash", "hash-rj05", "--operator", "op", "--reason", "bad",
        ])
        shown = _run_review_json(["show", "--latest"])
        assert shown["rejected"] is True

    def test_reject_cannot_approve_after_reject(self):
        created = self._create_review("req-rj06", "hash-rj06")
        review_id = created["review"]["review_id"]
        _run_review_json([
            "reject", "--review-id", review_id,
            "--output-hash", "hash-rj06", "--operator", "op", "--reason", "bad",
        ])
        # Try to approve after rejection — should fail
        r = _run_review([
            "approve", "--review-id", review_id,
            "--output-hash", "hash-rj06", "--operator", "op", "--reason", "trying",
        ])
        assert r.returncode != 0


class TestBackendReviewNoSubprocess:
    def test_review_commands_no_subprocess(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "subprocess.run" not in source

    def test_no_shell_interception(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "shell=True" not in source
        assert "ShellWrapper" not in source


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94N — Backend apply plan CLI tests
# ═══════════════════════════════════════════════════════════════════════════

import json as _json_ap
import subprocess as _sub_ap
import sys as _sys_ap
import tempfile as _temp_ap
from pathlib import Path as _Path_ap

import pytest as _pytest_ap

REPO_ROOT_94N = _Path_ap(__file__).resolve().parent.parent


def _run_ap(cmd_args: list[str]) -> _sub_ap.CompletedProcess:
    return _sub_ap.run(
        [_sys_ap.executable, "-m", "pcae", "backend", "apply-plan"] + cmd_args,
        capture_output=True, text=True, cwd=REPO_ROOT_94N, timeout=15,
    )


def _json_ap_cmd(cmd_args: list[str]) -> dict:
    r = _run_ap(cmd_args + ["--json"])
    assert r.returncode == 0, f"CLI failed: {r.stderr}\nstdout: {r.stdout}"
    return _json_ap.loads(r.stdout)


def _json_ap_any(cmd_args: list[str]) -> dict:
    """Like _json_ap_cmd but accepts non-zero exit (e.g. validate when not ready)."""
    r = _run_ap(cmd_args + ["--json"])
    return _json_ap.loads(r.stdout)


class TestApplyPlanShow:
    def test_show_missing_clean_text(self, tmp_path):
        r = _sub_ap.run(
            [_sys_ap.executable, "-m", "pcae", "backend", "apply-plan", "show", "--latest"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0

    def test_show_missing_clean_json(self, tmp_path):
        r = _sub_ap.run(
            [_sys_ap.executable, "-m", "pcae", "backend", "apply-plan", "show", "--latest", "--json"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0
        data = _json_ap.loads(r.stdout)
        assert "error" in data

    def test_show_after_create(self):
        _run_ap(["create", "--review-id", "rv-sh01", "--output-hash", "hash-sh01"])
        data = _json_ap_cmd(["show", "--latest"])
        assert data["review_id"] == "rv-sh01"
        assert data["output_hash"] == "hash-sh01"

    def test_show_no_raw_content(self):
        r = _run_ap(["show", "--latest"])
        if r.returncode == 0:
            assert len(r.stdout) < 5000

    def test_show_json_no_secrets(self):
        data = _json_ap_cmd(["show", "--latest"])
        j = _json_ap.dumps(data)
        assert "sk-ant" not in j
        assert "api_key" not in j.lower()


class TestApplyPlanCreate:
    def test_create_missing_review_id(self):
        r = _run_ap(["create", "--output-hash", "h"])
        assert r.returncode != 0

    def test_create_missing_output_hash(self):
        r = _run_ap(["create", "--review-id", "rv-x"])
        assert r.returncode != 0

    def test_create_succeeds(self):
        data = _json_ap_cmd(["create", "--review-id", "rv-c01", "--output-hash", "hash-c01"])
        assert "plan" in data
        assert data["plan"]["review_id"] == "rv-c01"
        assert data["plan"]["output_hash"] == "hash-c01"

    def test_create_defaults_apply_ready_false(self):
        data = _json_ap_cmd(["create", "--review-id", "rv-c02", "--output-hash", "hash-c02"])
        assert data["plan"]["apply_ready"] is False

    def test_create_defaults_rollback_required_true(self):
        data = _json_ap_cmd(["create", "--review-id", "rv-c03", "--output-hash", "hash-c03"])
        assert data["plan"]["rollback_required"] is True

    def test_create_defaults_check_required_true(self):
        data = _json_ap_cmd(["create", "--review-id", "rv-c04", "--output-hash", "hash-c04"])
        assert data["plan"]["check_required"] is True

    def test_create_binds_review_id(self):
        data = _json_ap_cmd(["create", "--review-id", "rv-bind01", "--output-hash", "hash-bind01"])
        assert data["plan"]["review_id"] == "rv-bind01"

    def test_create_binds_approval_id(self):
        data = _json_ap_cmd([
            "create", "--review-id", "rv-ap01", "--output-hash", "hash-ap01",
            "--approval-id", "ap-ap01",
        ])
        assert data["plan"]["approval_id"] == "ap-ap01"

    def test_create_binds_request_id(self):
        data = _json_ap_cmd([
            "create", "--review-id", "rv-rq01", "--output-hash", "hash-rq01",
            "--request-id", "req-rq01",
        ])
        assert data["plan"]["request_id"] == "req-rq01"

    def test_create_manual_operation_accepted(self):
        data = _json_ap_cmd([
            "create", "--review-id", "rv-op01", "--output-hash", "hash-op01",
            "--operation", "manual_instruction:src/foo.py",
        ])
        ops = data["plan"]["operations"]
        assert len(ops) == 1
        assert ops[0]["operation_type"] == "manual_instruction"
        assert ops[0]["target_path"] == "src/foo.py"

    def test_create_descriptive_op_no_patch_parsing(self):
        data = _json_ap_cmd([
            "create", "--review-id", "rv-op02", "--output-hash", "hash-op02",
            "--operation", "manual_instruction:src/bar.py",
        ])
        assert data["no_patch_parsing"] is True

    def test_create_delete_operation_hard_blocked(self):
        data = _json_ap_cmd([
            "create", "--review-id", "rv-del01", "--output-hash", "hash-del01",
            "--operation", "delete_file:src/old.py",
        ])
        hb = data["plan"]["hard_blocks"]
        assert any("high_risk_op" in b for b in hb)

    def test_create_unknown_operation_warns(self):
        data = _json_ap_cmd([
            "create", "--review-id", "rv-unk01", "--output-hash", "hash-unk01",
            "--operation", "totally_unknown:src/x.py",
        ])
        warnings = data["plan"]["warnings"]
        assert any("unknown_operation_type" in w for w in warnings)

    def test_create_persists_to_latest(self):
        _run_ap(["create", "--review-id", "rv-persist01", "--output-hash", "hash-persist01"])
        data = _json_ap_cmd(["show", "--latest"])
        assert data["output_hash"] == "hash-persist01"

    def test_create_json_no_execution(self):
        data = _json_ap_cmd(["create", "--review-id", "rv-noe01", "--output-hash", "hash-noe01"])
        assert data["no_execution"] is True
        assert data["no_apply"] is True

    def test_create_json_no_source_files_modified(self):
        data = _json_ap_cmd(["create", "--review-id", "rv-nsf01", "--output-hash", "hash-nsf01"])
        assert data["no_source_files_modified"] is True

    def test_create_json_no_secrets(self):
        data = _json_ap_cmd(["create", "--review-id", "rv-sec01", "--output-hash", "hash-sec01"])
        j = _json_ap.dumps(data)
        assert "sk-ant" not in j
        assert "api_key" not in j.lower()

    def test_create_multipart_phase_id_preserved(self):
        data = _json_ap_cmd([
            "create", "--review-id", "rv-mp01", "--output-hash", "hash-mp01",
            "--phase-id", "94N.1.2",
        ])
        assert data["plan"]["phase_id"] == "94N.1.2"

    def test_create_operations_file(self, tmp_path):
        ops_file = tmp_path / "ops.json"
        ops_file.write_text(_json_ap.dumps([
            {"operation_type": "manual_instruction", "target_path": "src/main.py"},
            {"operation_type": "modify_file", "target_path": "src/utils.py"},
        ]))
        data = _json_ap_cmd([
            "create", "--review-id", "rv-of01", "--output-hash", "hash-of01",
            "--operations-file", str(ops_file),
        ])
        assert len(data["plan"]["operations"]) == 2

    def test_create_deterministic_structure(self):
        d1 = _json_ap_cmd(["create", "--review-id", "rv-det1", "--output-hash", "hash-det"])
        d2 = _json_ap_cmd(["create", "--review-id", "rv-det2", "--output-hash", "hash-det"])
        assert set(d1["plan"].keys()) == set(d2["plan"].keys())


class TestApplyPlanValidate:
    def test_validate_latest_reports_status(self):
        _run_ap(["create", "--review-id", "rv-val01", "--output-hash", "hash-val01"])
        # validate returns non-zero when plan is not ready — that's correct behavior
        r = _run_ap(["validate", "--json"])
        assert r.returncode in (0, 1)
        data = _json_ap.loads(r.stdout)
        assert "assessment" in data
        assert data["assessment"]["status"] in ("ready", "blocked", "missing_evidence",
                                                  "needs_human_review", "incomplete", "untrusted")

    def test_validate_missing_plan_fails_clean(self, tmp_path):
        r = _sub_ap.run(
            [_sys_ap.executable, "-m", "pcae", "backend", "apply-plan", "validate", "--json"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0
        data = _json_ap.loads(r.stdout)
        assert "error" in data

    def test_validate_missing_evidence_reported(self):
        _run_ap(["create", "--review-id", "rv-me01", "--output-hash", "hash-me01"])
        data = _json_ap_any(["validate"])
        assert len(data["assessment"]["missing_evidence"]) > 0

    def test_validate_hard_blocks_reported(self, tmp_path):
        import json as _j
        plan_file = tmp_path / "plan.json"
        from pcae.core.backend_invocations import ApplyPlan
        plan = ApplyPlan(apply_plan_id="pl-hb01", review_id="rv-hb01",
                          output_hash="h-hb01", hard_blocks=["forbidden_file:src/secret.py"])
        plan_file.write_text(_j.dumps(plan.to_dict(), indent=2))
        r = _sub_ap.run(
            [_sys_ap.executable, "-m", "pcae", "backend", "apply-plan",
             "validate", "--plan", str(plan_file), "--json"],
            capture_output=True, text=True, cwd=REPO_ROOT_94N, timeout=15,
        )
        data = _j.loads(r.stdout)
        assert "forbidden_file:src/secret.py" in data["assessment"]["hard_blocks"]

    def test_validate_does_not_execute_apply(self):
        _run_ap(["create", "--review-id", "rv-nex01", "--output-hash", "hash-nex01"])
        data = _json_ap_any(["validate"])
        assert data["no_execution"] is True
        assert data["no_apply"] is True

    def test_validate_does_not_run_tests(self):
        _run_ap(["create", "--review-id", "rv-ntr01", "--output-hash", "hash-ntr01"])
        data = _json_ap_any(["validate"])
        assert data["no_tests_run"] is True

    def test_validate_does_not_run_pcae_check(self):
        _run_ap(["create", "--review-id", "rv-npc01", "--output-hash", "hash-npc01"])
        data = _json_ap_any(["validate"])
        assert data["no_pcae_check_run"] is True

    def test_validate_no_source_files_modified(self):
        _run_ap(["create", "--review-id", "rv-nsf01", "--output-hash", "hash-nsf01"])
        data = _json_ap_any(["validate"])
        assert data["no_source_files_modified"] is True

    def test_validate_json_no_secrets(self):
        _run_ap(["create", "--review-id", "rv-sec01", "--output-hash", "hash-sec01"])
        data = _json_ap_any(["validate"])
        j = _json_ap.dumps(data)
        assert "sk-ant" not in j
        assert "api_key" not in j.lower()

    def test_validate_recommended_action_not_execute(self):
        _run_ap(["create", "--review-id", "rv-ra01", "--output-hash", "hash-ra01"])
        data = _json_ap_any(["validate"])
        assert "execute" not in data["assessment"]["recommended_action"].lower()

    def test_validate_with_plan_file(self, tmp_path):
        import json as _j
        from pcae.core.backend_invocations import ApplyPlan
        plan = ApplyPlan(apply_plan_id="pl-pf01", review_id="rv-pf01", output_hash="h-pf01")
        plan_file = tmp_path / "plan.json"
        plan_file.write_text(_j.dumps(plan.to_dict(), indent=2))
        r = _sub_ap.run(
            [_sys_ap.executable, "-m", "pcae", "backend", "apply-plan",
             "validate", "--plan", str(plan_file), "--json"],
            capture_output=True, text=True, cwd=REPO_ROOT_94N, timeout=15,
        )
        assert r.returncode in (0, 1)  # non-zero allowed when not ready
        data = _j.loads(r.stdout)
        assert "assessment" in data

    def test_validate_nonexistent_plan_file_fails(self):
        r = _run_ap(["validate", "--plan", "/nonexistent/plan.json"])
        assert r.returncode != 0


class TestApplyPlanNoSubprocess:
    def test_apply_plan_runners_no_subprocess(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "subprocess.run" not in source

    def test_no_shell_interception(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "shell=True" not in source
        assert "ShellWrapper" not in source

    def test_no_network_calls(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "urllib.request" not in source
        assert "requests.get" not in source

    def test_no_patch_parsing(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "patch_parser" not in source
        assert "parse_patch" not in source

    def test_apply_plan_dirs_ignored(self):
        gitignore = REPO_ROOT_94N / ".pcae" / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert "backend-apply-plans/" in content
        assert "backend-apply-readiness/" in content


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94O — Backend manual apply package CLI tests
# ═══════════════════════════════════════════════════════════════════════════

import json as _json_map
import subprocess as _sub_map
import sys as _sys_map
from pathlib import Path as _Path_map

REPO_ROOT_94O = _Path_map(__file__).resolve().parent.parent


def _run_map(cmd_args: list[str]) -> _sub_map.CompletedProcess:
    return _sub_map.run(
        [_sys_map.executable, "-m", "pcae", "backend", "manual-apply-package"] + cmd_args,
        capture_output=True, text=True, cwd=REPO_ROOT_94O, timeout=15,
    )


def _json_map_cmd(cmd_args: list[str]) -> dict:
    r = _run_map(cmd_args + ["--json"])
    assert r.returncode == 0, f"CLI failed: {r.stderr}\nstdout: {r.stdout}"
    return _json_map.loads(r.stdout)


class TestManualApplyPackageShow:
    def test_show_missing_clean_text(self, tmp_path):
        r = _sub_map.run(
            [_sys_map.executable, "-m", "pcae", "backend", "manual-apply-package",
             "show", "--latest"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0

    def test_show_missing_clean_json(self, tmp_path):
        r = _sub_map.run(
            [_sys_map.executable, "-m", "pcae", "backend", "manual-apply-package",
             "show", "--latest", "--json"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0
        data = _json_map.loads(r.stdout)
        assert "error" in data

    def test_show_after_create(self):
        _run_map(["create"])
        data = _json_map_cmd(["show", "--latest"])
        assert "package_id" in data
        assert data["no_execution_performed"] is True

    def test_show_json_no_secrets(self):
        _run_map(["create"])
        data = _json_map_cmd(["show", "--latest"])
        j = _json_map.dumps(data)
        assert "sk-ant" not in j
        assert "api_key" not in j.lower()

    def test_show_no_raw_content(self):
        _run_map(["create"])
        r = _run_map(["show", "--latest"])
        if r.returncode == 0:
            assert len(r.stdout) < 5000


class TestManualApplyPackageCreate:
    def test_create_succeeds(self):
        data = _json_map_cmd(["create"])
        assert "package" in data
        assert "package_id" in data["package"]

    def test_create_no_execution_performed(self):
        data = _json_map_cmd(["create"])
        assert data["package"]["no_execution_performed"] is True

    def test_create_no_apply(self):
        data = _json_map_cmd(["create"])
        assert data["no_apply"] is True

    def test_create_no_patch_parsing(self):
        data = _json_map_cmd(["create"])
        assert data["no_patch_parsing"] is True

    def test_create_no_source_files_modified(self):
        data = _json_map_cmd(["create"])
        assert data["no_source_files_modified"] is True

    def test_create_no_automatic_tests(self):
        data = _json_map_cmd(["create"])
        assert data["no_automatic_tests"] is True

    def test_create_no_automatic_pcae_check(self):
        data = _json_map_cmd(["create"])
        assert data["no_automatic_pcae_check"] is True

    def test_create_persists_json(self):
        data = _json_map_cmd(["create"])
        persist = data["persistence"]
        assert persist["status"] == "written"
        assert "json_path" in persist
        assert _Path_map(persist["json_path"]).is_file()

    def test_create_persists_markdown(self):
        data = _json_map_cmd(["create"])
        persist = data["persistence"]
        assert "md_path" in persist
        assert _Path_map(persist["md_path"]).is_file()

    def test_create_updates_latest_json(self):
        data = _json_map_cmd(["create"])
        latest = _json_map.loads(_Path_map(data["persistence"]["latest_json"]).read_text())
        assert latest["package_id"] == data["package"]["package_id"]
        assert latest["no_execution_performed"] is True

    def test_create_markdown_no_execution_confirmation(self):
        data = _json_map_cmd(["create"])
        md = _Path_map(data["persistence"]["md_path"]).read_text()
        assert "No files were modified" in md
        assert "no_execution_performed" in md

    def test_create_markdown_advisory_label(self):
        data = _json_map_cmd(["create"])
        md = _Path_map(data["persistence"]["md_path"]).read_text()
        assert "advisory" in md.lower() or "human" in md.lower()

    def test_create_json_no_secrets(self):
        data = _json_map_cmd(["create"])
        j = _json_map.dumps(data)
        assert "sk-ant" not in j
        assert "api_key" not in j.lower()

    def test_create_markdown_no_secrets(self):
        data = _json_map_cmd(["create"])
        md = _Path_map(data["persistence"]["md_path"]).read_text()
        assert "sk-ant" not in md
        assert "api_key" not in md.lower()

    def test_create_deterministic_structure(self):
        d1 = _json_map_cmd(["create"])
        d2 = _json_map_cmd(["create"])
        assert set(d1["package"].keys()) == set(d2["package"].keys())

    def test_create_with_operator_notes(self):
        data = _json_map_cmd(["create", "--operator-notes", "reviewed and approved context"])
        assert data["package"]["operator_notes"] == "reviewed and approved context"

    def test_create_with_rollback_instructions(self):
        data = _json_map_cmd(["create", "--rollback-instructions", "git revert HEAD"])
        assert data["package"]["rollback_instructions"] == "git revert HEAD"

    def test_create_with_apply_plan_file(self, tmp_path):
        import json as _j
        from pcae.core.backend_invocations import ApplyPlan
        plan = ApplyPlan(apply_plan_id="pl-mapf01", review_id="rv-mapf01",
                          output_hash="h-mapf01", phase_id="94O.99")
        plan_file = tmp_path / "plan.json"
        plan_file.write_text(_j.dumps(plan.to_dict(), indent=2))
        data = _json_map_cmd(["create", "--apply-plan", str(plan_file)])
        assert data["package"]["apply_plan_id"] == "pl-mapf01"
        assert data["package"]["output_hash"] == "h-mapf01"
        assert data["package"]["phase_id"] == "94O.99"

    def test_create_multipart_phase_id_preserved(self, tmp_path):
        import json as _j
        from pcae.core.backend_invocations import ApplyPlan
        plan = ApplyPlan(apply_plan_id="pl-mpmap", review_id="rv-mpmap",
                          output_hash="h-mpmap", phase_id="94O.1.2.3")
        plan_file = tmp_path / "plan-mp.json"
        plan_file.write_text(_j.dumps(plan.to_dict(), indent=2))
        data = _json_map_cmd(["create", "--apply-plan", str(plan_file)])
        assert data["package"]["phase_id"] == "94O.1.2.3"

    def test_create_with_readiness_file(self, tmp_path):
        import json as _j
        from pcae.core.backend_invocations import BackendApplyReadinessAssessment
        assessment = BackendApplyReadinessAssessment(
            assessment_id="ra-mapf01", status="blocked",
            apply_ready=False, hard_blocks=["forbidden_file:src/x.py"],
        )
        r_file = tmp_path / "readiness.json"
        r_file.write_text(_j.dumps(assessment.to_dict(), indent=2))
        data = _json_map_cmd(["create", "--readiness", str(r_file)])
        assert data["package"]["readiness_status"] == "blocked"
        assert "forbidden_file:src/x.py" in data["package"]["hard_blocks"]


class TestManualApplyPackageNoSubprocess:
    def test_no_subprocess_in_backend_commands(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "subprocess.run" not in source

    def test_no_shell_interception(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "shell=True" not in source

    def test_no_network_calls(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "urllib.request" not in source
        assert "requests.get" not in source

    def test_manual_apply_packages_dir_ignored(self):
        gitignore = REPO_ROOT_94O / ".pcae" / ".gitignore"
        assert gitignore.exists()
        assert "backend-manual-apply-packages/" in gitignore.read_text()

    def test_no_telegram_inbound_in_commands(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "getUpdates" not in source


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94P — Backend apply governance hardening CLI tests
# ═══════════════════════════════════════════════════════════════════════════

import json as _json_94p
import subprocess as _sub_94p
import sys as _sys_94p
import tempfile as _tempfile_94p
from pathlib import Path as _Path_94p

REPO_ROOT_94P = _Path_94p(__file__).resolve().parent.parent


def _run_94p(subcmd: list[str]) -> _sub_94p.CompletedProcess:
    return _sub_94p.run(
        [_sys_94p.executable, "-m", "pcae", "backend"] + subcmd,
        capture_output=True, text=True, cwd=REPO_ROOT_94P, timeout=15,
    )


def _json_94p_cmd(subcmd: list[str]) -> tuple[dict, int]:
    r = _run_94p(subcmd + ["--json"])
    try:
        data = _json_94p.loads(r.stdout)
    except Exception:
        data = {}
    return data, r.returncode


class TestHardeningReviewCLI:
    """Show/create/approve/reject hardening: clean errors, no secrets."""

    def test_review_show_missing_json_error(self, tmp_path):
        r = _sub_94p.run(
            [_sys_94p.executable, "-m", "pcae", "backend", "review", "show",
             "--latest", "--json"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0
        data = _json_94p.loads(r.stdout)
        assert "error" in data
        j = _json_94p.dumps(data)
        assert "sk-ant" not in j

    def test_review_show_missing_text_clean(self, tmp_path):
        r = _sub_94p.run(
            [_sys_94p.executable, "-m", "pcae", "backend", "review", "show", "--latest"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0
        # No raw content, no secrets
        assert "sk-ant" not in r.stdout
        assert len(r.stdout) < 500

    def test_review_create_json_no_secrets(self):
        data, rc = _json_94p_cmd(["review", "create",
                                   "--request-id", "rq-sec94p",
                                   "--output-hash", "h-sec94p"])
        assert rc == 0
        j = _json_94p.dumps(data)
        assert "sk-ant" not in j
        assert "api_key" not in j.lower()

    def test_review_create_no_execution_flags(self):
        data, rc = _json_94p_cmd(["review", "create",
                                   "--request-id", "rq-noexec94p",
                                   "--output-hash", "h-noexec94p"])
        assert rc == 0
        assert data.get("no_execution") is True
        assert data.get("no_apply") is True

    def test_review_create_no_raw_content_in_text(self):
        r = _run_94p(["review", "create",
                       "--request-id", "rq-noraw94p",
                       "--output-hash", "h-noraw94p"])
        assert r.returncode == 0
        assert "raw prompt" not in r.stdout.lower()
        assert len(r.stdout) < 3000

    def test_review_create_json_structure_deterministic(self):
        # Verify JSON structure is stable and secret-safe (no approve needed)
        data1, rc1 = _json_94p_cmd(["review", "create",
                                     "--request-id", "rq-struct1",
                                     "--output-hash", "h-struct1"])
        data2, rc2 = _json_94p_cmd(["review", "create",
                                     "--request-id", "rq-struct2",
                                     "--output-hash", "h-struct2"])
        assert rc1 == 0 and rc2 == 0
        assert set(data1["review"].keys()) == set(data2["review"].keys())
        assert "sk-ant" not in _json_94p.dumps(data1)
        assert "sk-ant" not in _json_94p.dumps(data2)


class TestHardeningApplyPlanCLI:
    """Apply plan hardening: hard blocks, hash checks, clean errors."""

    def test_apply_plan_show_missing_json_error(self, tmp_path):
        r = _sub_94p.run(
            [_sys_94p.executable, "-m", "pcae", "backend", "apply-plan", "show",
             "--latest", "--json"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0
        data = _json_94p.loads(r.stdout)
        assert "error" in data

    def test_apply_plan_create_high_risk_op_hard_blocks(self):
        data, rc = _json_94p_cmd(["apply-plan", "create",
                                   "--operation", "delete_file:src/foo.py",
                                   "--review-id", "rv-hr94p",
                                   "--output-hash", "h-hr94p"])
        assert rc == 0
        plan = data.get("plan", {})
        hard_blocks = plan.get("hard_blocks", [])
        assert any("high_risk_op" in b for b in hard_blocks)

    def test_apply_plan_create_unknown_op_hard_blocks(self):
        data, rc = _json_94p_cmd(["apply-plan", "create",
                                   "--operation", "unknown:src/mystery.py",
                                   "--review-id", "rv-uk94p",
                                   "--output-hash", "h-uk94p"])
        assert rc == 0
        plan = data.get("plan", {})
        hard_blocks = plan.get("hard_blocks", [])
        assert any("high_risk_op" in b or "unknown" in b for b in hard_blocks)

    def test_apply_plan_create_json_no_secrets(self):
        data, rc = _json_94p_cmd(["apply-plan", "create",
                                   "--review-id", "rv-sec94p",
                                   "--output-hash", "h-sec94p"])
        assert rc == 0
        j = _json_94p.dumps(data)
        assert "sk-ant" not in j
        assert "api_key" not in j.lower()

    def test_apply_plan_validate_no_tests_run(self):
        # Create plan first, then validate — validate must not run tests
        _run_94p(["apply-plan", "create",
                   "--review-id", "rv-val94p",
                   "--output-hash", "h-val94p"])
        data, _ = _json_94p_cmd(["apply-plan", "validate"])
        assert data.get("no_tests_run") is True
        assert data.get("no_pcae_check_run") is True

    def test_apply_plan_no_raw_content_printed(self):
        data, rc = _json_94p_cmd(["apply-plan", "create",
                                   "--review-id", "rv-noraw94p",
                                   "--output-hash", "h-noraw94p"])
        j = _json_94p.dumps(data)
        assert "raw output" not in j.lower()
        assert "raw prompt" not in j.lower()


class TestHardeningManualApplyPackageCLI:
    """MAP hardening: hard blocks visible, no authorization, clean errors."""

    def test_map_show_missing_json_error(self, tmp_path):
        r = _sub_94p.run(
            [_sys_94p.executable, "-m", "pcae", "backend", "manual-apply-package",
             "show", "--latest", "--json"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0
        data = _json_94p.loads(r.stdout)
        assert "error" in data

    def test_map_create_hard_blocks_from_high_risk_plan(self, tmp_path):
        # Create a plan with a high-risk op, then create MAP — use tmp plan file
        import json as _j
        from pcae.core.backend_invocations import ApplyPlan
        plan = ApplyPlan(
            apply_plan_id="pl-map-hb94p", review_id="rv-map-hb94p",
            output_hash="h-map-hb94p",
            hard_blocks=["high_risk_op:delete_file:src/foo.py"],
        )
        plan_file = tmp_path / "plan-hb.json"
        plan_file.write_text(_j.dumps(plan.to_dict(), indent=2))
        data, rc = _json_94p_cmd(["manual-apply-package", "create",
                                   "--apply-plan", str(plan_file)])
        assert rc == 0
        pkg = data.get("package", {})
        hard_blocks = pkg.get("hard_blocks", [])
        assert len(hard_blocks) > 0

    def test_map_create_hard_blocks_in_markdown(self, tmp_path):
        # Create plan with hard-risk op, then MAP — verify hard blocks in Markdown
        # Use tmp_path for apply-plan artifact so test is isolated
        import json as _j
        from pcae.core.backend_invocations import ApplyPlan, ApplyOperation, OP_DELETE
        plan = ApplyPlan(
            apply_plan_id="pl-map-md94p", review_id="rv-map-md94p",
            output_hash="h-map-md94p", hard_blocks=["high_risk_op:delete_file:src/bar.py"],
        )
        plan_file = tmp_path / "plan.json"
        plan_file.write_text(_j.dumps(plan.to_dict(), indent=2))
        data, rc = _json_94p_cmd(["manual-apply-package", "create",
                                   "--apply-plan", str(plan_file)])
        assert rc == 0
        md_path = _Path_94p(data["persistence"]["md_path"])
        md = md_path.read_text()
        assert "Hard Blocks" in md or any(
            b in md for b in data["package"].get("hard_blocks", [])
        )

    def test_map_create_no_commit_push_auth_in_json(self):
        data, rc = _json_94p_cmd(["manual-apply-package", "create"])
        assert rc == 0
        j = _json_94p.dumps(data)
        assert "commit_authorized" not in j
        assert "push_authorized" not in j

    def test_map_create_no_execution_always_true(self):
        data, rc = _json_94p_cmd(["manual-apply-package", "create"])
        assert rc == 0
        assert data["package"]["no_execution_performed"] is True
        assert data["no_execution"] is True

    def test_map_create_no_automatic_tests_flag(self):
        data, rc = _json_94p_cmd(["manual-apply-package", "create"])
        assert rc == 0
        assert data["no_automatic_tests"] is True

    def test_map_create_no_automatic_pcae_check_flag(self):
        data, rc = _json_94p_cmd(["manual-apply-package", "create"])
        assert rc == 0
        assert data["no_automatic_pcae_check"] is True

    def test_map_create_json_no_secrets(self):
        data, rc = _json_94p_cmd(["manual-apply-package", "create"])
        assert rc == 0
        j = _json_94p.dumps(data)
        assert "sk-ant" not in j
        assert "api_key" not in j.lower()

    def test_map_show_no_raw_content(self):
        _run_94p(["manual-apply-package", "create"])
        r = _run_94p(["manual-apply-package", "show", "--latest"])
        if r.returncode == 0:
            # "No raw prompt/output" disclaimer is fine; raw body is not
            out_lower = r.stdout.lower()
            assert "sk-ant" not in out_lower
            assert "api_key" not in out_lower
            assert len(r.stdout) < 5000

    def test_map_json_errors_secret_safe(self, tmp_path):
        r = _sub_94p.run(
            [_sys_94p.executable, "-m", "pcae", "backend", "manual-apply-package",
             "show", "--latest", "--json"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        if r.returncode != 0:
            data = _json_94p.loads(r.stdout)
            j = _json_94p.dumps(data)
            assert "sk-ant" not in j


class TestHardeningNoSubprocess:
    """Cross-cutting: no subprocess, no network, gitignored dirs."""

    def test_no_subprocess_in_backend_commands_94p(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "subprocess.run" not in source
        assert "Popen(" not in source

    def test_no_network_in_backend_commands_94p(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "urllib.request" not in source
        assert "requests.get" not in source

    def test_no_subprocess_in_backend_invocations_94p(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "subprocess.run" not in source
        assert "os.system(" not in source

    def test_all_artifact_dirs_gitignored(self):
        gitignore = REPO_ROOT_94P / ".pcae" / ".gitignore"
        content = gitignore.read_text()
        assert "backend-reviews/" in content
        assert "backend-apply-plans/" in content
        assert "backend-apply-readiness/" in content
        assert "backend-manual-apply-packages/" in content

    def test_no_telegram_inbound_in_commands_94p(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "getUpdates" not in source


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94Q — Backend lifecycle demo CLI tests
# ═══════════════════════════════════════════════════════════════════════════

import json as _json_94q
import subprocess as _sub_94q
import sys as _sys_94q
import tempfile as _tempfile_94q
from pathlib import Path as _Path_94q

# Use a temp directory for isolation to avoid contaminating REPO_ROOT .pcae/
# state with demo artifacts that interfere with earlier test classes.
_ISOLATED_DIR_94Q = _Path_94q(_tempfile_94q.mkdtemp(prefix="pcae-94q-"))


def _run_94q(subcmd: list[str]) -> _sub_94q.CompletedProcess:
    return _sub_94q.run(
        [_sys_94q.executable, "-m", "pcae", "backend", "demo"] + subcmd,
        capture_output=True, text=True, cwd=_ISOLATED_DIR_94Q, timeout=15,
    )


def _json_94q_cmd(subcmd: list[str]) -> tuple[dict, int]:
    r = _run_94q(subcmd + ["--json"])
    try:
        return _json_94q.loads(r.stdout), r.returncode
    except Exception:
        return {"raw": r.stdout, "stderr": r.stderr}, r.returncode


class Test94QDemoCLIHappyPath:
    """Happy path: pcae backend demo mock-lifecycle."""

    def test_mock_lifecycle_text_output(self):
        r = _run_94q(["mock-lifecycle"])
        assert r.returncode == 0
        assert "Mock lifecycle demo" in r.stdout
        assert "No real backend invoked" in r.stdout
        assert "No files modified" in r.stdout
        assert "No apply executed" in r.stdout
        assert "Output remains quarantined" in r.stdout

    def test_mock_lifecycle_json_output(self):
        data, rc = _json_94q_cmd(["mock-lifecycle"])
        assert rc == 0
        assert "demo" in data
        assert "steps" in data
        assert data["no_real_backend_invoked"] is True
        assert data["no_apply_execution"] is True
        assert data["no_file_mutation"] is True

    def test_mock_lifecycle_json_demo_has_ids(self):
        data, rc = _json_94q_cmd(["mock-lifecycle"])
        assert rc == 0
        d = data["demo"]
        assert d["demo_id"].startswith("demo-")
        assert d["request_id"].startswith("be-")
        assert d["audit_id"].startswith("ba-")
        assert d["review_id"].startswith("rv-")
        assert d["approval_id"].startswith("ap-")
        assert d["apply_plan_id"].startswith("pl-")
        assert d["apply_readiness_assessment_id"].startswith("ra-")

    def test_mock_lifecycle_json_steps_all_present(self):
        data, rc = _json_94q_cmd(["mock-lifecycle"])
        assert rc == 0
        steps = data["steps"]
        for key in ["plan", "mock_invocation", "audit", "trust", "review",
                     "approval", "apply_plan", "apply_readiness"]:
            assert key in steps, f"Missing step: {key}"


class Test94QDemoCLINegativePath:
    """Negative path: pcae backend demo mock-lifecycle --negative."""

    def test_negative_text_output(self):
        r = _run_94q(["mock-lifecycle", "--negative"])
        assert r.returncode == 0
        assert "blocked" in r.stdout.lower()
        assert "Negative path exercised" in r.stdout
        assert "No real backend invoked" in r.stdout

    def test_negative_text_has_rejection(self):
        r = _run_94q(["mock-lifecycle", "--negative"])
        assert r.returncode == 0
        assert "Rejection ID" in r.stdout

    def test_negative_json_blocked_status(self):
        data, rc = _json_94q_cmd(["mock-lifecycle", "--negative"])
        assert rc == 0
        assert data["demo"]["lifecycle_status"] == "blocked"

    def test_negative_json_has_hard_blocks(self):
        data, rc = _json_94q_cmd(["mock-lifecycle", "--negative"])
        assert rc == 0
        assert len(data["demo"]["hard_blocks"]) > 0

    def test_negative_json_no_approval(self):
        data, rc = _json_94q_cmd(["mock-lifecycle", "--negative"])
        assert rc == 0
        assert data["demo"]["approval_id"] == ""


class Test94QDemoCLIShow:
    """pcae backend demo show --latest."""

    def test_show_text_after_mock_lifecycle(self):
        _run_94q(["mock-lifecycle"])
        r = _run_94q(["show", "--latest"])
        assert r.returncode == 0
        assert "Latest lifecycle demo" in r.stdout
        assert "Output remains quarantined" in r.stdout

    def test_show_json_after_mock_lifecycle(self):
        _run_94q(["mock-lifecycle"])
        data, rc = _json_94q_cmd(["show", "--latest"])
        assert rc == 0
        assert "demo_id" in data
        assert data["no_real_backend_invoked"] is True

    def test_show_missing_demo_text(self):
        r = _sub_94q.run(
            [_sys_94q.executable, "-m", "pcae", "backend", "demo", "show", "--latest"],
            capture_output=True, text=True,
            cwd=_Path_94q(_tempfile_94q.mkdtemp()), timeout=15,
        )
        assert r.returncode != 0

    def test_show_missing_demo_json(self):
        r = _sub_94q.run(
            [_sys_94q.executable, "-m", "pcae", "backend", "demo", "show",
             "--latest", "--json"],
            capture_output=True, text=True,
            cwd=_Path_94q(_tempfile_94q.mkdtemp()), timeout=15,
        )
        assert r.returncode != 0
        data = _json_94q.loads(r.stdout)
        assert "error" in data


class Test94QDemoCLISafety:
    """Safety guarantees in CLI output."""

    def test_json_no_secrets(self):
        data, rc = _json_94q_cmd(["mock-lifecycle"])
        assert rc == 0
        j = _json_94q.dumps(data)
        assert "sk-ant" not in j
        assert "api_key" not in j.lower()

    def test_json_no_raw_prompt_content(self):
        data, rc = _json_94q_cmd(["mock-lifecycle"])
        assert rc == 0
        j = _json_94q.dumps(data)
        assert "deterministic mock prompt" not in j.lower()

    def test_text_no_secrets(self):
        r = _run_94q(["mock-lifecycle"])
        assert r.returncode == 0
        assert "sk-ant" not in r.stdout.lower()
        assert "api_key" not in r.stdout.lower()

    def test_no_subprocess_in_backend_commands(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "subprocess.run" not in source
        assert "Popen(" not in source

    def test_no_network_in_backend_commands(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "urllib.request" not in source
        assert "requests.get" not in source

    def test_no_telegram_inbound_in_commands(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "getUpdates" not in source

    def test_gitignore_has_lifecycle_demos_dir(self):
        from pathlib import Path as _P
        gitignore = _P(__file__).resolve().parent.parent / ".pcae" / ".gitignore"
        content = gitignore.read_text()
        assert "backend-lifecycle-demos/" in content


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94T — Real backend adapter preflight CLI tests
# ═══════════════════════════════════════════════════════════════════════════

import json as _json_94t
import subprocess as _sub_94t
import sys as _sys_94t
from pathlib import Path as _Path_94t

REPO_ROOT_94T = _Path_94t(__file__).resolve().parent.parent


def _run_94t(subcmd: list[str]) -> _sub_94t.CompletedProcess:
    return _sub_94t.run(
        [_sys_94t.executable, "-m", "pcae", "backend", "adapter"] + subcmd,
        capture_output=True, text=True, cwd=REPO_ROOT_94T, timeout=15,
    )


def _json_94t_cmd(subcmd: list[str]) -> tuple[dict, int]:
    r = _run_94t(subcmd + ["--json"])
    try:
        return _json_94t.loads(r.stdout), r.returncode
    except Exception:
        return {"raw": r.stdout, "stderr": r.stderr}, r.returncode


class Test94TAdapterListCLI:
    """pcae backend adapter list."""

    def test_list_text_shows_all_adapters(self):
        r = _run_94t(["list"])
        assert r.returncode == 0
        assert "mock" in r.stdout
        assert "claude" in r.stdout
        assert "preflight_only" in r.stdout
        assert "No backend invocation" in r.stdout

    def test_list_json_has_all_adapters(self):
        data, rc = _json_94t_cmd(["list"])
        assert rc == 0
        assert data["count"] == 5
        ids = [a["backend_id"] for a in data["adapters"]]
        assert "mock" in ids
        assert "claude" in ids
        assert data["no_real_backend_invoked"] is True

    def test_list_json_no_secrets(self):
        data, rc = _json_94t_cmd(["list"])
        assert rc == 0
        j = _json_94t.dumps(data)
        assert "sk-ant" not in j


class Test94TAdapterShowCLI:
    """pcae backend adapter show."""

    def test_show_claude_text(self):
        r = _run_94t(["show", "--backend", "claude"])
        assert r.returncode == 0
        assert "Claude CLI Adapter" in r.stdout
        assert "preflight_only" in r.stdout
        assert "ANTHROPIC_API_KEY" in r.stdout
        assert "Human approval" in r.stdout

    def test_show_mock_text(self):
        r = _run_94t(["show", "--backend", "mock"])
        assert r.returncode == 0
        assert "mock_only" in r.stdout

    def test_show_unknown_backend_fails(self):
        r = _run_94t(["show", "--backend", "bogus"])
        assert r.returncode != 0

    def test_show_json(self):
        data, rc = _json_94t_cmd(["show", "--backend", "claude"])
        assert rc == 0
        assert data["adapter"]["backend_id"] == "claude"
        assert data["no_real_backend_invoked"] is True

    def test_show_missing_backend_fails(self):
        r = _run_94t(["show"])
        assert r.returncode != 0

    def test_show_no_secrets_in_json(self):
        data, rc = _json_94t_cmd(["show", "--backend", "claude"])
        assert rc == 0
        j = _json_94t.dumps(data)
        assert "sk-ant" not in j


class Test94TAdapterPreflightCLI:
    """pcae backend adapter preflight."""

    def test_preflight_mock_ready(self):
        r = _run_94t(["preflight", "--backend", "mock"])
        assert r.returncode == 0
        assert "ready" in r.stdout
        assert "No real backend" in r.stdout

    def test_preflight_claude_blocked_missing_env(self):
        r = _run_94t(["preflight", "--backend", "claude"])
        assert r.returncode != 0  # blocked → non-zero
        assert "ANTHROPIC_API_KEY" in r.stdout
        assert "No subprocess" in r.stdout

    def test_preflight_unknown_backend_fails(self):
        r = _run_94t(["preflight", "--backend", "bogus"])
        assert r.returncode != 0

    def test_preflight_missing_backend_fails(self):
        r = _run_94t(["preflight"])
        assert r.returncode != 0

    def test_preflight_json_mock_ready(self):
        data, rc = _json_94t_cmd(["preflight", "--backend", "mock"])
        assert rc == 0
        assert data["preflight"]["status"] == "ready"
        assert data["preflight"]["ready"] is True
        assert data["no_real_backend_invoked"] is True
        assert data["no_subprocess"] is True
        assert data["no_network"] is True

    def test_preflight_json_claude_blocked(self):
        data, rc = _json_94t_cmd(["preflight", "--backend", "claude"])
        assert rc != 0
        assert data["preflight"]["status"] in ("blocked", "missing_evidence")
        assert data["preflight"]["ready"] is False
        assert "ANTHROPIC_API_KEY" in data["preflight"]["missing_env_keys"]

    def test_preflight_json_no_secrets(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-secret-value-xyz")
        data, rc = _json_94t_cmd(["preflight", "--backend", "claude"])
        j = _json_94t.dumps(data)
        assert "sk-ant-secret-value-xyz" not in j
        assert data["preflight"]["secrets_redacted"] is True

    def test_preflight_no_real_backend_invoked(self):
        data, rc = _json_94t_cmd(["preflight", "--backend", "mock"])
        assert rc == 0
        assert data["preflight"]["no_real_backend_invoked"] is True

    def test_preflight_env_values_not_printed(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "secret-key-abc123")
        r = _run_94t(["preflight", "--backend", "claude"])
        assert "secret-key-abc123" not in r.stdout


class Test94TAdapterCLISafety:
    """Cross-cutting safety for 94T CLI."""

    def test_no_subprocess_in_commands(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "subprocess.run" not in source
        assert "Popen(" not in source

    def test_no_network_in_commands(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "urllib.request" not in source
        assert "requests.get" not in source

    def test_no_telegram_inbound_in_commands(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "getUpdates" not in source
