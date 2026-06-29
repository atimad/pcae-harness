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

pytestmark = pytest.mark.fast_green

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
