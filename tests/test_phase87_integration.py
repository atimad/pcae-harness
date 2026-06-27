"""Phase 87 gate/broker/shell architecture integration tests.

Validates the gate dry-run evaluator, specific gate evaluations, architecture
artifacts, and non-authorizing boundary across the full Phase 87 layer.

88Y.1 optimization: most gate dry-run tests now call build_gate_dry_run()
directly instead of spawning subprocesses, eliminating Python startup overhead.
One CLI smoke test preserved for subprocess integration coverage.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.core.gate_dry_run import build_gate_dry_run
from pcae.core.artifact_index import build_artifact_index
from pcae.core.memory_snapshot import build_memory_snapshot
from pcae.core.governance_timeline import build_governance_timeline
from pcae.core.decision_log import build_decision_log
from pcae.core.risk_register import build_risk_register
from pcae.core.project_state import build_project_state

pytestmark = [pytest.mark.slow, pytest.mark.integration, pytest.mark.phase_closure]

REPO_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_GATES = [
    "task_start_gate", "scope_check_gate", "backend_invocation_gate",
    "prompt_send_gate", "capture_acceptance_gate", "intake_review_gate",
    "adoption_approval_gate", "source_mutation_gate", "test_mutation_gate",
    "commit_gate", "push_gate", "rollback_gate", "storage_write_gate",
    "permission_broker_gate", "shell_command_gate",
]

PHASE_87_ARTIFACTS = [
    "docs/PHASE_87_GOVERNED_ACTION_GATES_PLAN.md",
    "docs/PHASE_87_ACTION_GATE_TAXONOMY_DECISION_MODEL.md",
    "docs/PHASE_87_GATE_DRY_RUN_PROTOTYPE.md",
    "docs/PHASE_87_SCOPE_GATE_PROTOTYPE.md",
    "docs/PHASE_87_BACKEND_INVOCATION_GATE_DRY_RUN.md",
    "docs/PHASE_87_ADOPTION_MUTATION_GATE_DRY_RUN.md",
    "docs/PHASE_87_COMMIT_PUSH_GATE_DRY_RUN.md",
    "docs/PHASE_87_PERMISSION_BROKER_ARCHITECTURE.md",
    "docs/PHASE_87_SHELL_GATE_ARCHITECTURE.md",
]


def _run_gate_direct(action=None, files=None, backend=None,
                     prompt_present=False, adoption_artifact_present=False,
                     human_approved=False, commit_message_present=False,
                     push_target=None):
    """Call build_gate_dry_run directly — no subprocess overhead."""
    return build_gate_dry_run(
        REPO_ROOT,
        requested_action=action,
        requested_files=files or [],
        requested_backend=backend,
        prompt_present=prompt_present,
        adoption_artifact_present=adoption_artifact_present,
        human_approved=human_approved,
        commit_message_present=commit_message_present,
        push_target=push_target,
    )


def _run_gate(extra_args: list[str] | None = None) -> dict:
    """CLI smoke: run gate-dry-run via subprocess. Used only for CLI smoke test."""
    cmd = [sys.executable, "-m", "pcae", "gate-dry-run", "--json"]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    return json.loads(result.stdout)


def _gate(data: dict, gate_id: str) -> dict:
    for g in data["gates"]:
        if g["gate_id"] == gate_id:
            return g
    raise AssertionError(f"{gate_id} not found")


# --- Default gate dry-run surface ---

def test_default_gate_dry_run_works():
    data = _run_gate_direct()
    assert data["gate_count"] == 15
    assert data["dry_run"] is True


def test_all_15_gates_present():
    data = _run_gate_direct()
    gate_ids = {g["gate_id"] for g in data["gates"]}
    for expected in EXPECTED_GATES:
        assert expected in gate_ids, f"Missing gate: {expected}"


# --- Specific gate evaluations present ---

def test_scope_gate_has_scope_evaluation():
    data = _run_gate_direct(action="source_mutation",
                            files=["src/pcae/core/gate_dry_run.py"])
    assert "scope_evaluation" in _gate(data, "scope_check_gate")


def test_backend_gate_has_backend_evaluation():
    data = _run_gate_direct(action="backend_invocation",
                            backend="claude", prompt_present=True)
    assert "backend_evaluation" in _gate(data, "backend_invocation_gate")


def test_adoption_gate_has_adoption_evaluation():
    data = _run_gate_direct(action="adoption",
                            files=["src/example.py"],
                            adoption_artifact_present=True)
    assert "adoption_evaluation" in _gate(data, "adoption_approval_gate")


def test_source_mutation_gate_has_mutation_evaluation():
    data = _run_gate_direct(action="source_mutation",
                            files=["src/pcae/core/gate_dry_run.py"])
    assert "mutation_evaluation" in _gate(data, "source_mutation_gate")


def test_test_mutation_gate_has_mutation_evaluation():
    data = _run_gate_direct(action="test_mutation",
                            files=["tests/test_example.py"])
    assert "mutation_evaluation" in _gate(data, "test_mutation_gate")


def test_commit_gate_has_commit_evaluation():
    data = _run_gate_direct(action="commit", commit_message_present=True)
    assert "commit_evaluation" in _gate(data, "commit_gate")


def test_push_gate_has_push_evaluation():
    data = _run_gate_direct(action="push", push_target="origin/main")
    assert "push_evaluation" in _gate(data, "push_gate")


# --- Non-authorizing boundary ---

def test_all_gates_authorization_false_default():
    data = _run_gate_direct()
    for g in data["gates"]:
        assert g["authorization_granted"] is False, f"{g['gate_id']}"
        assert g["enforcement_performed"] is False, f"{g['gate_id']}"


def test_all_gates_authorization_false_with_all_flags():
    data = _run_gate_direct(action="adoption",
                            files=["src/example.py"],
                            adoption_artifact_present=True,
                            human_approved=True,
                            backend="claude", prompt_present=True,
                            commit_message_present=True,
                            push_target="origin/main")
    for g in data["gates"]:
        assert g["authorization_granted"] is False, f"{g['gate_id']}"
        assert g["enforcement_performed"] is False, f"{g['gate_id']}"


def test_no_gate_produces_allow():
    data = _run_gate_direct(action="adoption",
                            files=["src/example.py"],
                            adoption_artifact_present=True,
                            human_approved=True)
    for g in data["gates"]:
        assert g["decision"] != "allow", f"{g['gate_id']} should not allow"


def test_envelope_backend_invocation_false():
    data = _run_gate_direct()
    assert data["safety_notes"]["backend_invocation_performed"] is False


def test_envelope_repo_mutation_false():
    data = _run_gate_direct()
    assert data["safety_notes"]["repo_mutation_performed"] is False


def test_envelope_storage_written_false():
    data = _run_gate_direct()
    assert data["safety_notes"]["storage_written"] is False


# --- Specific non-invocation/non-execution ---

def test_backend_invocation_does_not_invoke():
    data = _run_gate_direct(action="backend_invocation",
                            backend="claude", prompt_present=True)
    bg = _gate(data, "backend_invocation_gate")
    assert bg["authorization_granted"] is False
    be = bg["backend_evaluation"]
    assert be["backend_approval_detected"] is False


def test_adoption_does_not_approve():
    data = _run_gate_direct(action="adoption",
                            files=["src/example.py"],
                            adoption_artifact_present=True,
                            human_approved=True)
    ag = _gate(data, "adoption_approval_gate")
    assert ag["authorization_granted"] is False
    ae = ag["adoption_evaluation"]
    assert ae["adoption_approval_detected"] is False


def test_commit_does_not_commit():
    data = _run_gate_direct(action="commit",
                            commit_message_present=True,
                            human_approved=True)
    cg = _gate(data, "commit_gate")
    assert cg["authorization_granted"] is False
    assert cg["decision"] != "allow"


def test_push_does_not_push():
    data = _run_gate_direct(action="push",
                            push_target="origin/main",
                            human_approved=True)
    pg = _gate(data, "push_gate")
    assert pg["authorization_granted"] is False
    assert pg["decision"] != "allow"
    pe = pg["push_evaluation"]
    assert pe["raw_push_detected"] is False
    assert pe["force_push_detected"] is False


def test_mutation_does_not_mutate():
    data = _run_gate_direct(action="source_mutation",
                            files=["src/example.py"],
                            human_approved=True)
    sm = _gate(data, "source_mutation_gate")
    assert sm["authorization_granted"] is False


# --- Architecture artifacts verification ---

def test_all_phase_87_artifacts_exist():
    for artifact in PHASE_87_ARTIFACTS:
        path = REPO_ROOT / artifact
        assert path.is_file(), f"Missing artifact: {artifact}"


def test_broker_architecture_is_design_only():
    path = REPO_ROOT / "docs/PHASE_87_PERMISSION_BROKER_ARCHITECTURE.md"
    content = path.read_text()
    assert "implementation_status=not_started" in content


def test_shell_gate_architecture_is_design_only():
    path = REPO_ROOT / "docs/PHASE_87_SHELL_GATE_ARCHITECTURE.md"
    content = path.read_text()
    assert "implementation_status=not_started" in content


def test_broker_architecture_distinguishes_evidence():
    path = REPO_ROOT / "docs/PHASE_87_PERMISSION_BROKER_ARCHITECTURE.md"
    content = path.read_text()
    assert "inform" in content.lower() and "not authorize" in content.lower()


def test_shell_gate_architecture_distinguishes_evidence():
    path = REPO_ROOT / "docs/PHASE_87_SHELL_GATE_ARCHITECTURE.md"
    content = path.read_text()
    assert "deny by default" in content.lower()


# --- No-write/no-storage ---

def test_no_cache_or_state_created():
    pcae_dir = REPO_ROOT / ".pcae"
    dirs = [
        pcae_dir / "cache", pcae_dir / "gates", pcae_dir / "broker",
        pcae_dir / "shell", pcae_dir / "state", pcae_dir / "commits",
        pcae_dir / "pushes", pcae_dir / "adoption", pcae_dir / "mutation",
    ]
    before = {d: d.exists() for d in dirs}
    _run_gate_direct(action="backend_invocation", backend="claude",
                     prompt_present=True)
    _run_gate_direct(action="commit", commit_message_present=True)
    _run_gate_direct(action="push", push_target="origin/main")
    for d, existed in before.items():
        if not existed:
            assert not d.exists(), f"{d} was created"


def test_no_repository_mutation():
    r1 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    before = r1.stdout
    _run_gate_direct(action="source_mutation",
                     files=["src/example.py"], human_approved=True)
    _run_gate_direct(action="push", push_target="origin/main")
    r2 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    assert r2.stdout == before


# --- Read-only project intelligence commands still work ---

_BUILDERS = {
    "artifact-index": build_artifact_index,
    "memory-snapshot": build_memory_snapshot,
    "governance-timeline": build_governance_timeline,
    "decision-log": build_decision_log,
    "risk-register": build_risk_register,
    "project-state": build_project_state,
}


def test_read_only_commands_still_work():
    for cmd_name, builder in _BUILDERS.items():
        data = builder(REPO_ROOT)
        assert "schema_version" in data, f"{cmd_name}: missing schema_version"
        assert "safety_notes" in data, f"{cmd_name}: missing safety_notes"


def test_read_only_commands_still_work_cli_smoke():
    """One CLI subprocess smoke test to verify CLI surface works."""
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "artifact-index", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0


# --- Determinism ---

def test_gate_dry_run_deterministic():
    d1 = _run_gate_direct()
    d2 = _run_gate_direct()
    assert d1["gate_count"] == d2["gate_count"]
    ids1 = [g["gate_id"] for g in d1["gates"]]
    ids2 = [g["gate_id"] for g in d2["gates"]]
    assert ids1 == ids2
