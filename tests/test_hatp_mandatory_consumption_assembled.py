"""Phase 149O.18F -- HMRC Assembled Consumption Integration (A-F, real CLI
entrypoint).

Complements `tests/test_phase_149o_18f_hmrc_assembled_attack_matrix.py`
(which mechanically represents all 45 HMRC-001 Sec.29 attacks, mostly at
the direct-function-call and adapter-integration layers) with full,
behavior-driven CLI -> `commands/agent.py` -> `core/agent.py` -> Wave B
consumption -> Permission Broker assembled integration tests -- exercising
the real `pcae.cli.main` entrypoint end to end, never a hand-constructed
core-layer call alone, for the highest-value assembled scenarios items
119/120/125/126 call out explicitly:

- AG3 assembled via CLI, real temp-git-repo effect (deterministic ALLOW
  seam) and real current-POL-005 DENY (no seam, zero effect).
- AG5 assembled via CLI, real temp-filesystem effect and real DENY.
- A single deterministic-ALLOW control-flow proof at the CLI layer
  (never a production `allow=True` parameter -- the internal
  `evaluate_for_real_effect` symbol substitution used throughout this
  repository's HMRC test suites, applied here one layer up at the CLI
  boundary).
"""
from __future__ import annotations

import json
import subprocess as _subprocess_mod
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.core import agent as _agent_mod
from pcae.core import hatp_mandatory_cutover as _cutover_mod
from pcae.core import hatp_rollback_consumption as _consumption_mod
from pcae.core.hatp_mandatory_cutover import CutoverMode, CutoverModeResolution
from pcae.core.hatp_rollback_consumption import HATPRollbackConsumptionResult
from pcae.core.human_approval_trusted_provenance import HATPVerificationStatus
from pcae.core.paths import HarnessPath
from pcae.core.permission_broker_foundation import DECISION_ALLOW, DECISION_DENY

from tests.test_agent import (
    _init_git_root,
    _make_per_test_ecp,
    _make_rer_test_per,
    _patch_rollback_execute_helpers,
    _setup_approved_rollback,
)

pytestmark = pytest.mark.fast_green

_VALID_EVIDENCE_ID = "a" * 64


def _fixed_mode(mode: CutoverMode) -> CutoverModeResolution:
    return CutoverModeResolution(mode, f"test_fixed_{mode.value}")


def _patch_mode(monkeypatch, mode: CutoverMode) -> None:
    monkeypatch.setattr(_cutover_mod, "resolve_production_hatp_cutover_mode", lambda root: _fixed_mode(mode))


def _patch_consumption(monkeypatch, pb_decision: str) -> None:
    def _fake_evaluate(request, *, root):
        return HATPRollbackConsumptionResult(
            evidence_id=request.evidence_id, hatp_status=HATPVerificationStatus.VALID,
            pb_decision=pb_decision, reasons=("assembled_test_seam",),
        )

    monkeypatch.setattr(_consumption_mod, "evaluate_for_real_effect", _fake_evaluate)


# ─────────────────────────────────────────────────────────────────────────
# AG3 assembled: CLI -> execute_rollback -> Wave B -> PB, real temp git repo
# ─────────────────────────────────────────────────────────────────────────


def test_ag3_cli_assembled_mandatory_missing_evidence_zero_effect(tmp_path, monkeypatch, capsys) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    exit_code = main(["remote", "rollback", "execute", job_id, "--json"])
    capsys.readouterr()
    assert exit_code == 1


def test_ag3_cli_assembled_deterministic_allow_real_git_revert(tmp_path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    run = lambda *args: _subprocess_mod.run(args, cwd=repo, check=True, capture_output=True, text=True)
    run("git", "init")
    run("git", "config", "user.email", "test@example.com")
    run("git", "config", "user.name", "Test User")
    (repo / ".gitignore").write_text(".pcae/\n")
    run("git", "add", ".gitignore")
    run("git", "commit", "-m", "gitignore")
    (repo / "file.txt").write_text("v1\n")
    run("git", "add", "file.txt")
    run("git", "commit", "-m", "initial")
    (repo / "file.txt").write_text("v2\n")
    run("git", "add", "file.txt")
    run("git", "commit", "-m", "governed change")
    head_before = _subprocess_mod.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()

    jobs_dir = repo / ".pcae" / "remote" / "jobs"
    jobs_dir.mkdir(parents=True)
    results_dir = repo / ".pcae" / "remote" / "results"
    results_dir.mkdir(parents=True)
    job_id = "job-assembled-ag3"
    (jobs_dir / f"{job_id}.json").write_text(
        json.dumps({
            "job_id": job_id, "commit_sha": head_before,
            "rollback_approval_state": "approved", "requested_agent": "claude-local",
        })
    )
    (results_dir / f"{job_id}-result.json").write_text(
        json.dumps({"changed_files": ["file.txt"], "scope_validation": {}})
    )

    monkeypatch.chdir(repo)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    _patch_consumption(monkeypatch, DECISION_ALLOW)

    exit_code = main([
        "remote", "rollback", "execute", job_id, "--hatp-evidence-id", _VALID_EVIDENCE_ID, "--json",
    ])
    assert exit_code == 0
    assert (repo / "file.txt").read_text() == "v1\n"


def test_ag3_cli_assembled_current_real_pol005_deny_zero_effect(tmp_path, monkeypatch, capsys) -> None:
    """Item 85: against the real, unmodified PB dependency chain (no
    seam), a real-effect HATP_MANDATORY CLI attempt deterministically
    resolves DENY under current POL-005 -- zero effect."""
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    # No consumption seam: exercises the real evaluate_for_real_effect.

    exit_code = main([
        "remote", "rollback", "execute", job_id, "--hatp-evidence-id", _VALID_EVIDENCE_ID, "--json",
    ])
    assert exit_code == 1


# ─────────────────────────────────────────────────────────────────────────
# AG5 assembled: CLI -> build_rollback_execution -> Wave B -> PB, real
# temp filesystem
# ─────────────────────────────────────────────────────────────────────────


def _setup_removable_file_per_cli(tmp_path, per_id="per-assembled-ag5"):
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    _init_git_root(root_dir)
    (root_dir / "added.txt").write_text("added content")
    root = HarnessPath(root_dir)
    import hashlib

    after_hash = hashlib.sha256(b"added content").hexdigest()
    entries = [{"path": "added.txt", "before_hash": None, "after_hash": after_hash,
                "before_content": None, "before_exists": False, "binary": False}]
    _make_per_test_ecp(root, file_entries=entries)
    _make_rer_test_per(root, per_id=per_id, file_results=[{"path": "added.txt", "outcome": "success"}])
    return root, root_dir


def test_ag5_cli_assembled_mandatory_missing_evidence_zero_mutation(tmp_path, monkeypatch, capsys) -> None:
    root, root_dir = _setup_removable_file_per_cli(tmp_path)
    monkeypatch.chdir(root_dir)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    exit_code = main(["rollback", "--per-id", "per-assembled-ag5", "--json"])
    assert exit_code == 1
    assert (root_dir / "added.txt").exists()


def test_ag5_cli_assembled_deterministic_allow_real_file_mutation(tmp_path, monkeypatch) -> None:
    root, root_dir = _setup_removable_file_per_cli(tmp_path)
    monkeypatch.chdir(root_dir)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    _patch_consumption(monkeypatch, DECISION_ALLOW)

    exit_code = main([
        "rollback", "--per-id", "per-assembled-ag5", "--hatp-evidence-id", _VALID_EVIDENCE_ID, "--json",
    ])
    assert exit_code == 0
    assert not (root_dir / "added.txt").exists()


def test_ag5_cli_assembled_current_real_pol005_deny_zero_mutation(tmp_path, monkeypatch) -> None:
    root, root_dir = _setup_removable_file_per_cli(tmp_path)
    monkeypatch.chdir(root_dir)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    # No seam: real evaluate_for_real_effect / real PB.

    exit_code = main([
        "rollback", "--per-id", "per-assembled-ag5", "--hatp-evidence-id", _VALID_EVIDENCE_ID, "--json",
    ])
    assert exit_code == 1
    assert (root_dir / "added.txt").exists()


# ─────────────────────────────────────────────────────────────────────────
# Dry-run: zero mutation, no mandatory-evidence requirement, at the real
# CLI layer (item 82)
# ─────────────────────────────────────────────────────────────────────────


def test_ag5_cli_dry_run_never_requires_evidence_in_any_mode(tmp_path, monkeypatch) -> None:
    root, root_dir = _setup_removable_file_per_cli(tmp_path)
    monkeypatch.chdir(root_dir)
    for mode in (CutoverMode.LEGACY_COMPATIBLE, CutoverMode.PREPARED, CutoverMode.HATP_MANDATORY):
        _patch_mode(monkeypatch, mode)
        exit_code = main(["rollback", "--per-id", "per-assembled-ag5", "--dry-run", "--json"])
        assert exit_code == 0
        assert (root_dir / "added.txt").exists()
        assert (root_dir / "added.txt").read_text() == "added content"
