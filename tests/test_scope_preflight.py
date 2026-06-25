from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(extra_args: list[str] | None = None) -> dict:
    cmd = [sys.executable, "-m", "pcae", "preflight", "scope", "--json"]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    return json.loads(result.stdout)


# --- Command exists ---


def test_command_exits_successfully():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "preflight", "scope", "--json",
         "--requested-action", "read"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0


def test_command_output_is_valid_json():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "preflight", "scope", "--json",
         "--requested-action", "read"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    data = json.loads(result.stdout)
    assert isinstance(data, dict)


# --- JSON envelope fields ---


def test_envelope_has_schema_version():
    data = _run(["--requested-action", "read"])
    assert data["schema_version"] == "0.1"


def test_envelope_has_generated_at():
    data = _run(["--requested-action", "read"])
    assert "generated_at" in data


def test_envelope_has_source_command():
    data = _run(["--requested-action", "read"])
    assert data["source_command"] == "pcae preflight scope"


def test_envelope_has_repository_root():
    data = _run(["--requested-action", "read"])
    assert "repository_root" in data


def test_envelope_has_preflight():
    data = _run(["--requested-action", "read"])
    assert "preflight" in data
    assert isinstance(data["preflight"], dict)


def test_envelope_has_warnings():
    data = _run(["--requested-action", "read"])
    assert "warnings" in data
    assert isinstance(data["warnings"], list)


def test_envelope_has_errors():
    data = _run(["--requested-action", "read"])
    assert "errors" in data
    assert isinstance(data["errors"], list)


def test_envelope_has_safety_notes():
    data = _run(["--requested-action", "read"])
    assert "safety_notes" in data
    assert isinstance(data["safety_notes"], dict)


# --- Preflight object fields ---


def test_preflight_has_all_required_fields():
    data = _run(["--requested-action", "read", "--requested-file", "PROJECT_STATUS.md"])
    pf = data["preflight"]
    required = [
        "preflight_type", "requested_action", "requested_files",
        "decision", "reason_codes", "task_contract_detected",
        "task_contract_path", "lifecycle_state", "allowed_files",
        "forbidden_files", "matched_allowed_files", "matched_forbidden_files",
        "unknown_files", "human_review_required", "more_evidence_required",
        "evidence_sources", "scope_notes", "authorization_granted",
        "execution_authorized", "repo_mutation_performed", "storage_written",
        "backend_invocation_performed",
    ]
    for field in required:
        assert field in pf, f"Missing preflight field: {field}"


def test_preflight_type_is_scope_gate():
    data = _run(["--requested-action", "read"])
    assert data["preflight"]["preflight_type"] == "scope_gate_preflight"


# --- Active task contract detection ---


def test_active_task_contract_detected():
    data = _run(["--requested-action", "read", "--requested-file", "PROJECT_STATUS.md"])
    pf = data["preflight"]
    assert pf["task_contract_detected"] is True
    assert pf["task_contract_path"] is not None


# --- Allowed file returns allow_preflight ---


def test_allowed_file_returns_allow_preflight():
    data = _run(["--requested-action", "read", "--requested-file", "PROJECT_STATUS.md"])
    pf = data["preflight"]
    assert pf["decision"] == "allow_preflight"
    assert "scope_allowed" in pf["reason_codes"]
    assert "PROJECT_STATUS.md" in pf["matched_allowed_files"]


def test_allowed_source_file_returns_allow_preflight():
    data = _run(["--requested-action", "docs_mutation",
                 "--requested-file", "CHANGELOG.md"])
    pf = data["preflight"]
    assert pf["decision"] == "allow_preflight"


def test_allowed_test_file_returns_allow_preflight():
    data = _run(["--requested-action", "read",
                 "--requested-file", "CHANGELOG.md"])
    pf = data["preflight"]
    assert pf["decision"] == "allow_preflight"


def test_allowed_docs_file_returns_allow_preflight():
    data = _run(["--requested-action", "docs_mutation",
                 "--requested-file", "PROJECT_STATUS.md"])
    pf = data["preflight"]
    assert pf["decision"] == "allow_preflight"


# --- Forbidden file returns deny/block ---


def test_forbidden_file_blocked_by_scope():
    data = _run(["--requested-action", "source_mutation",
                 "--requested-file", "README.md"])
    pf = data["preflight"]
    assert pf["decision"] in ("blocked_by_scope", "deny_preflight")
    assert "README.md" in pf["matched_forbidden_files"]
    assert "forbidden_file_requested" in pf["reason_codes"]


def test_forbidden_docs_file_blocked():
    data = _run(["--requested-action", "docs_mutation",
                 "--requested-file", "docs/REAL_CAPTURED_TASKS.md"])
    pf = data["preflight"]
    assert pf["decision"] in ("blocked_by_scope", "deny_preflight")
    assert "docs/REAL_CAPTURED_TASKS.md" in pf["matched_forbidden_files"]


def test_forbidden_pcae_dir_blocked():
    data = _run(["--requested-action", "storage_write",
                 "--requested-file", ".pcae/some_file.json"])
    pf = data["preflight"]
    assert ".pcae/some_file.json" in pf["matched_forbidden_files"] or \
        pf["decision"] in ("requires_human_review",)


# --- Out-of-scope file returns deny/review/more-evidence ---


def test_out_of_scope_file_returns_requires_more_evidence():
    data = _run(["--requested-action", "read",
                 "--requested-file", "random_out_of_scope_file.txt"])
    pf = data["preflight"]
    assert pf["decision"] in ("requires_more_evidence", "requires_human_review",
                               "blocked_by_scope", "deny_preflight")
    assert "random_out_of_scope_file.txt" in pf["unknown_files"]


def test_out_of_scope_random_file():
    data = _run(["--requested-action", "read",
                 "--requested-file", "random_nonexistent_file.txt"])
    pf = data["preflight"]
    assert pf["decision"] in ("requires_more_evidence", "requires_human_review")
    assert "random_nonexistent_file.txt" in pf["unknown_files"]


# --- Unknown file returns review/more-evidence ---


def test_unknown_file_scope_requires_evidence():
    data = _run(["--requested-action", "read",
                 "--requested-file", "unknown/path/file.py"])
    pf = data["preflight"]
    assert pf["decision"] in ("requires_more_evidence", "requires_human_review")
    assert "unknown/path/file.py" in pf["unknown_files"]


# --- Unknown action returns review/unknown ---


def test_unknown_action_requires_human_review():
    data = _run(["--requested-action", "unknown",
                 "--requested-file", "PROJECT_STATUS.md"])
    pf = data["preflight"]
    assert pf["decision"] in ("requires_human_review", "unknown")
    assert "unknown_action" in pf["reason_codes"]


def test_unrecognized_action_requires_human_review():
    data = _run(["--requested-action", "destroy_everything",
                 "--requested-file", "PROJECT_STATUS.md"])
    pf = data["preflight"]
    assert pf["decision"] in ("requires_human_review", "unknown")
    assert "unknown_action" in pf["reason_codes"]


# --- Multiple requested files ---


def test_multiple_allowed_files():
    data = _run(["--requested-action", "read",
                 "--requested-file", "PROJECT_STATUS.md",
                 "--requested-file", "CHANGELOG.md"])
    pf = data["preflight"]
    assert pf["decision"] == "allow_preflight"
    assert len(pf["matched_allowed_files"]) == 2


def test_multiple_files_with_forbidden():
    data = _run(["--requested-action", "docs_mutation",
                 "--requested-file", "PROJECT_STATUS.md",
                 "--requested-file", "README.md"])
    pf = data["preflight"]
    assert pf["decision"] in ("deny_preflight", "blocked_by_scope")
    assert "README.md" in pf["matched_forbidden_files"]
    assert "PROJECT_STATUS.md" in pf["matched_allowed_files"]


def test_multiple_files_with_unknown():
    data = _run(["--requested-action", "read",
                 "--requested-file", "PROJECT_STATUS.md",
                 "--requested-file", "some_totally_unknown.py"])
    pf = data["preflight"]
    assert pf["decision"] in ("requires_human_review", "requires_more_evidence")
    assert "some_totally_unknown.py" in pf["unknown_files"]
    assert "PROJECT_STATUS.md" in pf["matched_allowed_files"]


# --- Conflicting allowed/forbidden match denies ---


def test_conflicting_allowed_forbidden_denies():
    data = _run(["--requested-action", "source_mutation",
                 "--requested-file", "PROJECT_STATUS.md",
                 "--requested-file", "docs/REAL_CAPTURED_TASKS.md"])
    pf = data["preflight"]
    assert pf["decision"] in ("deny_preflight", "blocked_by_scope")


# --- allow_preflight does not set execution_authorized true ---


def test_allow_preflight_does_not_authorize_execution():
    data = _run(["--requested-action", "read",
                 "--requested-file", "PROJECT_STATUS.md"])
    pf = data["preflight"]
    assert pf["decision"] == "allow_preflight"
    assert pf["execution_authorized"] is False


# --- authorization_granted remains false ---


def test_authorization_granted_always_false():
    data = _run(["--requested-action", "read",
                 "--requested-file", "PROJECT_STATUS.md"])
    assert data["preflight"]["authorization_granted"] is False


def test_authorization_granted_false_for_forbidden():
    data = _run(["--requested-action", "source_mutation",
                 "--requested-file", "README.md"])
    assert data["preflight"]["authorization_granted"] is False


def test_authorization_granted_false_for_unknown():
    data = _run(["--requested-action", "unknown",
                 "--requested-file", "PROJECT_STATUS.md"])
    assert data["preflight"]["authorization_granted"] is False


# --- repo_mutation_performed false ---


def test_repo_mutation_performed_false():
    data = _run(["--requested-action", "source_mutation",
                 "--requested-file", "src/pcae/core/scope_preflight.py"])
    assert data["preflight"]["repo_mutation_performed"] is False


# --- storage_written false ---


def test_storage_written_false():
    data = _run(["--requested-action", "read",
                 "--requested-file", "PROJECT_STATUS.md"])
    assert data["preflight"]["storage_written"] is False


# --- backend_invocation_performed false ---


def test_backend_invocation_performed_false():
    data = _run(["--requested-action", "backend_invocation",
                 "--requested-file", "PROJECT_STATUS.md"])
    assert data["preflight"]["backend_invocation_performed"] is False


# --- No cache/state/.pcae files created ---


def test_no_cache_files_created():
    pcae_dir = REPO_ROOT / ".pcae"
    dirs = [
        pcae_dir / "cache", pcae_dir / "gates", pcae_dir / "scope",
        pcae_dir / "preflight", pcae_dir / "broker", pcae_dir / "shell_gate",
    ]
    before = {d: d.exists() for d in dirs}
    _run(["--requested-action", "source_mutation", "--requested-file", "src/example.py"])
    for d, existed in before.items():
        if not existed:
            assert not d.exists(), f"{d} was created by scope preflight"


def test_no_preflight_state_files():
    pcae_dir = REPO_ROOT / ".pcae"
    candidates = [
        pcae_dir / "preflight_state.json",
        pcae_dir / "scope_preflight.json",
        pcae_dir / "gate_state.json",
    ]
    _run(["--requested-action", "source_mutation", "--requested-file", "src/example.py"])
    for f in candidates:
        assert not f.exists(), f"{f} was created by scope preflight"


# --- Command does not mutate requested files ---


def test_no_repository_mutation():
    r1 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    before = r1.stdout
    _run(["--requested-action", "source_mutation", "--requested-file", "src/example.py"])
    r2 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    assert r2.stdout == before


# --- Command does not stage/commit/push ---


def test_no_staging_performed():
    r1 = subprocess.run(["git", "diff", "--cached", "--name-only"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    before = r1.stdout
    _run(["--requested-action", "source_mutation", "--requested-file", "src/example.py"])
    r2 = subprocess.run(["git", "diff", "--cached", "--name-only"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    assert r2.stdout == before


# --- Existing gate-dry-run still works ---


def test_gate_dry_run_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "gate-dry-run", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["gate_count"] == 15


# --- Existing read-only intelligence commands still work ---


def test_existing_intelligence_commands_still_work():
    for cmd in ["artifact-index", "memory-snapshot", "governance-timeline",
                "decision-log", "risk-register", "project-state"]:
        result = subprocess.run(
            [sys.executable, "-m", "pcae", cmd, "--json"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"{cmd} failed: {result.stderr}"


# --- Safety notes ---


def test_safety_notes_scope_preflight_only():
    data = _run(["--requested-action", "read"])
    sn = data["safety_notes"]
    assert sn["scope_preflight_only"] is True


def test_safety_notes_does_not_intercept_shell():
    data = _run(["--requested-action", "read"])
    assert data["safety_notes"]["scope_preflight_does_not_intercept_shell"] is True


def test_safety_notes_does_not_authorize_execution():
    data = _run(["--requested-action", "read"])
    assert data["safety_notes"]["scope_preflight_does_not_authorize_execution"] is True


def test_safety_notes_does_not_invoke_backends():
    data = _run(["--requested-action", "read"])
    assert data["safety_notes"]["scope_preflight_does_not_invoke_backends"] is True


def test_safety_notes_does_not_send_prompts():
    data = _run(["--requested-action", "read"])
    assert data["safety_notes"]["scope_preflight_does_not_send_prompts"] is True


def test_safety_notes_does_not_capture_outputs():
    data = _run(["--requested-action", "read"])
    assert data["safety_notes"]["scope_preflight_does_not_capture_outputs"] is True


def test_safety_notes_does_not_perform_intake():
    data = _run(["--requested-action", "read"])
    assert data["safety_notes"]["scope_preflight_does_not_perform_intake"] is True


def test_safety_notes_does_not_perform_adoption():
    data = _run(["--requested-action", "read"])
    assert data["safety_notes"]["scope_preflight_does_not_perform_adoption"] is True


def test_safety_notes_does_not_mutate_repo():
    data = _run(["--requested-action", "read"])
    assert data["safety_notes"]["scope_preflight_does_not_mutate_repo"] is True


def test_safety_notes_does_not_commit():
    data = _run(["--requested-action", "read"])
    assert data["safety_notes"]["scope_preflight_does_not_commit"] is True


def test_safety_notes_does_not_push():
    data = _run(["--requested-action", "read"])
    assert data["safety_notes"]["scope_preflight_does_not_push"] is True


def test_safety_notes_does_not_write_storage():
    data = _run(["--requested-action", "read"])
    assert data["safety_notes"]["scope_preflight_does_not_write_storage"] is True


def test_safety_notes_permission_broker_not_implemented():
    data = _run(["--requested-action", "read"])
    assert data["safety_notes"]["permission_broker_not_implemented"] is True


def test_safety_notes_shell_gate_not_implemented():
    data = _run(["--requested-action", "read"])
    assert data["safety_notes"]["shell_gate_not_implemented"] is True


def test_safety_notes_storage_not_implemented():
    data = _run(["--requested-action", "read"])
    assert data["safety_notes"]["storage_not_implemented"] is True


# --- Not-scope-decidable actions ---


def test_backend_invocation_requires_human_review():
    data = _run(["--requested-action", "backend_invocation",
                 "--requested-file", "PROJECT_STATUS.md"])
    pf = data["preflight"]
    assert pf["decision"] == "requires_human_review"
    assert pf["human_review_required"] is True


def test_commit_requires_human_review():
    data = _run(["--requested-action", "commit",
                 "--requested-file", "PROJECT_STATUS.md"])
    pf = data["preflight"]
    assert pf["decision"] == "requires_human_review"


def test_push_requires_human_review():
    data = _run(["--requested-action", "push",
                 "--requested-file", "PROJECT_STATUS.md"])
    pf = data["preflight"]
    assert pf["decision"] == "requires_human_review"


def test_rollback_requires_human_review():
    data = _run(["--requested-action", "rollback",
                 "--requested-file", "PROJECT_STATUS.md"])
    pf = data["preflight"]
    assert pf["decision"] == "requires_human_review"


def test_storage_write_requires_human_review():
    data = _run(["--requested-action", "storage_write",
                 "--requested-file", "PROJECT_STATUS.md"])
    pf = data["preflight"]
    assert pf["decision"] == "requires_human_review"


def test_adoption_requires_human_review():
    data = _run(["--requested-action", "adoption",
                 "--requested-file", "PROJECT_STATUS.md"])
    pf = data["preflight"]
    assert pf["decision"] == "requires_human_review"


# --- No files requested ---


def test_no_files_requested_requires_more_evidence():
    data = _run(["--requested-action", "read"])
    pf = data["preflight"]
    assert pf["decision"] in ("requires_more_evidence", "requires_human_review")
    assert pf["more_evidence_required"] is True or pf["human_review_required"] is True


# --- Reason codes ---


def test_reason_codes_include_preflight_disclaimer():
    data = _run(["--requested-action", "read", "--requested-file", "PROJECT_STATUS.md"])
    pf = data["preflight"]
    assert "preflight_only_not_execution_authorization" in pf["reason_codes"]


# --- Plain text output ---


def test_plain_text_output():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "preflight", "scope",
         "--requested-action", "read", "--requested-file", "PROJECT_STATUS.md"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    assert "Scope gate preflight evaluation" in result.stdout
    assert "Decision:" in result.stdout
