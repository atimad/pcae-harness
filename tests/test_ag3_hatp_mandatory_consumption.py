"""AG3 Mandatory Consumption Integration -- Phase 149O.18C behavioral tests.

Covers the requirement subset HMRC-REQ-036/052/061/063/066/074 (and MC-4,
MC-6, MC-7, MC-10, MC-11, MC-14) as wired into `execute_rollback`
(`src/pcae/core/agent.py`) this phase: fresh cutover-mode resolution
(149O.18A), mandatory evidence-ID requirement, and the 149O.18B real-effect
Consumption Attempt gate, placed immediately before `_run_git_revert`.

Reuses `tests/test_agent.py`'s existing, already-verified AG3 job-lifecycle
fixture helpers (`_setup_approved_rollback`/`_patch_rollback_execute_helpers`)
rather than hand-rolling a second job-fixture harness -- this phase's own
authority gate is new, but the surrounding job/commit/approval lifecycle is
not, and duplicating it risks a subtly-wrong fixture giving false
confidence (precedent: `tests/test_phase_149o_12c_hsce_attack_matrix.py`
already imports fixtures from `tests.test_hatp_signing_ceremony`).

`resolve_production_hatp_cutover_mode`/`evaluate_for_real_effect` are
imported *locally* inside `execute_rollback` (not module-level in
`agent.py`), so tests monkeypatch the attribute on its *owning* module
(`pcae.core.hatp_mandatory_cutover`/`pcae.core.hatp_rollback_consumption`),
which a fresh `from module import name` re-reads on every call -- never the
`pcae.core.agent` module's own namespace.
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
from pcae.core.permission_broker_foundation import DECISION_ALLOW, DECISION_DENY, DECISION_HUMAN_REVIEW

from tests.test_agent import (
    _fake_git_head,
    _patch_rollback_execute_helpers,
    _setup_approved_rollback,
)

_VALID_EVIDENCE_ID = "a" * 64


def _fixed_mode(mode: CutoverMode) -> CutoverModeResolution:
    return CutoverModeResolution(mode, f"test_fixed_{mode.value}")


def _patch_mode(monkeypatch, mode: CutoverMode) -> None:
    monkeypatch.setattr(
        _cutover_mod,
        "resolve_production_hatp_cutover_mode",
        lambda root: _fixed_mode(mode),
    )


def _patch_consumption(monkeypatch, pb_decision: str, *, calls: list | None = None) -> None:
    """Deterministic internal test seam (governing-prompt item 41): replaces
    the module-level `evaluate_for_real_effect` symbol -- never a caller-
    supplied `allow=True`/`pb_decision=` parameter on `execute_rollback`
    itself, which has no such parameter (see
    `TestNoCallerAuthorityOverride` below)."""

    def _fake_evaluate(request, *, root):
        if calls is not None:
            calls.append(request.evidence_id)
        return HATPRollbackConsumptionResult(
            evidence_id=request.evidence_id,
            hatp_status=HATPVerificationStatus.VALID,
            pb_decision=pb_decision,
            reasons=("test_seam",),
        )

    monkeypatch.setattr(_consumption_mod, "evaluate_for_real_effect", _fake_evaluate)


# ─────────────────────────────────────────────────────────────────────────
# LEGACY_COMPATIBLE / PREPARED regression (HMRC-REQ-032/035): unchanged
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("mode", [CutoverMode.LEGACY_COMPATIBLE, CutoverMode.PREPARED])
def test_legacy_and_prepared_dispatch_unchanged(
    tmp_path: Path, monkeypatch, capsys, mode: CutoverMode
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, mode)

    exit_code = main(["remote", "rollback", "execute", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data["rolled_back"] is True


def test_prepared_does_not_require_evidence(tmp_path: Path, monkeypatch, capsys) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.PREPARED)

    exit_code = main(["remote", "rollback", "execute", job_id, "--json"])
    assert exit_code == 0


def test_legacy_compatible_still_enforces_approval_state(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Attack #23-adjacent baseline: LEGACY_COMPATIBLE's own legacy gate
    (rollback_approval_state) still applies -- this phase must not weaken
    it. Uses the un-approved 43D-style setup indirectly via a fresh job
    with no approval."""
    from tests.test_agent import _setup_committed_change

    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.LEGACY_COMPATIBLE)

    exit_code = main(["remote", "rollback", "execute", job_id, "--json"])
    output = capsys.readouterr().out
    assert exit_code == 1
    assert "pending" in output.lower()


# ─────────────────────────────────────────────────────────────────────────
# HATP_MANDATORY -- missing/invalid evidence fails closed
# ─────────────────────────────────────────────────────────────────────────


def test_mandatory_missing_evidence_id_fails_closed(tmp_path: Path, monkeypatch, capsys) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    revert_calls: list = []
    _patch_rollback_execute_helpers(monkeypatch)
    monkeypatch.setattr(_agent_mod, "_run_git_revert", lambda sha, cwd: revert_calls.append(1) or (_ for _ in ()).throw(AssertionError("must not be called")))
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    exit_code = main(["remote", "rollback", "execute", job_id, "--json"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "hatp" in output.lower()
    assert revert_calls == []


def test_mandatory_legacy_approved_but_missing_evidence_still_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Attacks #20/#23/#63: legacy `rollback_approval_state == 'approved'`
    supplies zero authority once HATP_MANDATORY applies."""
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    exit_code = main(["remote", "rollback", "execute", job_id, "--json"])
    assert exit_code == 1


# ─────────────────────────────────────────────────────────────────────────
# HATP_MANDATORY -- no dual authority (attack #64: legacy-unapproved + HMRC
# ALLOW must still reach effect; legacy state is not consulted at all)
# ─────────────────────────────────────────────────────────────────────────


def test_mandatory_legacy_unapproved_plus_deterministic_allow_reaches_effect(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from tests.test_agent import _setup_committed_change

    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)  # never approved
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    _patch_consumption(monkeypatch, DECISION_ALLOW)

    # No `--hatp-evidence-id` CLI flag exists yet (HMRC-REQ-011 staging,
    # item 70): supplied via direct function call, exactly as 149O.18B's
    # own "recommended next phase" note specifies for 18C.
    result = _agent_mod.execute_rollback(
        HarnessPath(tmp_path), job_id, hatp_evidence_id=_VALID_EVIDENCE_ID
    )

    assert result["rolled_back"] is True


# ─────────────────────────────────────────────────────────────────────────
# HATP_MANDATORY -- PB DENY / HUMAN_REVIEW never reach effect (attacks
# #32/#33/#65/#66/#90/#91)
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("decision", [DECISION_DENY, DECISION_HUMAN_REVIEW])
def test_mandatory_pb_deny_or_human_review_blocks_effect(
    tmp_path: Path, monkeypatch, capsys, decision: str
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    revert_calls: list = []
    _patch_rollback_execute_helpers(monkeypatch)
    monkeypatch.setattr(
        _agent_mod,
        "_run_git_revert",
        lambda sha, cwd: revert_calls.append(1) or (_ for _ in ()).throw(AssertionError("must not be called")),
    )
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    _patch_consumption(monkeypatch, decision)

    with pytest.raises(ValueError, match="HATP"):
        _agent_mod.execute_rollback(
            HarnessPath(tmp_path), job_id, hatp_evidence_id=_VALID_EVIDENCE_ID
        )
    assert revert_calls == []


def test_mandatory_current_production_pol005_consequence_confirmed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Item 36/68: against the real, unmodified 149O.18B adapter (no test
    seam), a real-effect HATP_MANDATORY attempt on this deployment
    deterministically resolves PB DENY under current POL-005 -- confirmed
    end-to-end through the real `execute_rollback` wiring, not weakened or
    worked around."""
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    # No _patch_consumption: exercises the real evaluate_for_real_effect.

    with pytest.raises(ValueError, match="HATP"):
        _agent_mod.execute_rollback(
            HarnessPath(tmp_path), job_id, hatp_evidence_id=_VALID_EVIDENCE_ID
        )


# ─────────────────────────────────────────────────────────────────────────
# HATP_MANDATORY -- deterministic ALLOW permits exactly one effect (item 67)
# ─────────────────────────────────────────────────────────────────────────


def test_mandatory_deterministic_allow_permits_exactly_one_effect(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    revert_calls: list = []

    def _spy_revert(sha, cwd):
        revert_calls.append(sha)
        return _subprocess_mod.CompletedProcess(args=[], returncode=0, stdout="[main rev1234] Revert ...\n", stderr="")

    _patch_rollback_execute_helpers(monkeypatch)
    monkeypatch.setattr(_agent_mod, "_run_git_revert", _spy_revert)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    _patch_consumption(monkeypatch, DECISION_ALLOW)

    result = _agent_mod.execute_rollback(
        HarnessPath(tmp_path), job_id, hatp_evidence_id=_VALID_EVIDENCE_ID
    )

    assert result["rolled_back"] is True
    assert len(revert_calls) == 1


# ─────────────────────────────────────────────────────────────────────────
# Direct-call bypass prevention (HMRC-REQ-065/068, attack #24/#83)
# ─────────────────────────────────────────────────────────────────────────


def test_direct_call_bypass_still_enforces_mandatory_gate(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Calling `execute_rollback` directly (skipping `commands/agent.py`
    entirely) must still encounter the mandatory gate."""
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    with pytest.raises(ValueError, match="HATP"):
        _agent_mod.execute_rollback(HarnessPath(tmp_path), job_id)


def test_direct_call_with_deterministic_allow_still_requires_gate_pass(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    _patch_consumption(monkeypatch, DECISION_ALLOW)

    result = _agent_mod.execute_rollback(
        HarnessPath(tmp_path), job_id, hatp_evidence_id=_VALID_EVIDENCE_ID
    )
    assert result["rolled_back"] is True


# ─────────────────────────────────────────────────────────────────────────
# Raw hook bypass rejection (HMRC-REQ-071, attacks #30/#31/#84/#85)
# ─────────────────────────────────────────────────────────────────────────


def test_raw_hatp_proof_alone_does_not_authorize_in_mandatory_mode(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    with pytest.raises(ValueError, match="HATP"):
        _agent_mod.execute_rollback(
            HarnessPath(tmp_path),
            job_id,
            hatp_proof=object(),
            hatp_evidence=object(),
        )


def test_consumption_call_ignores_raw_proof_even_with_evidence_id(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """The mandatory path only ever passes `hatp_evidence_id` into the 18B
    request -- raw `hatp_proof`/`hatp_evidence` are structurally never
    forwarded (`HATPRollbackConsumptionRequest` has no such field)."""
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    captured: list = []
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    _patch_consumption(monkeypatch, DECISION_ALLOW, calls=captured)

    _agent_mod.execute_rollback(
        HarnessPath(tmp_path),
        job_id,
        hatp_evidence_id=_VALID_EVIDENCE_ID,
        hatp_proof="not-a-real-proof",
        hatp_evidence="not-real-evidence",
    )
    assert captured == [_VALID_EVIDENCE_ID]


# ─────────────────────────────────────────────────────────────────────────
# No cache / repeat attempt (HMRC-REQ-076/077, attacks #25-#28/#87)
# ─────────────────────────────────────────────────────────────────────────


def test_no_cache_second_attempt_reevaluates_and_can_deny(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    revert_calls: list = []

    def _spy_revert(sha, cwd):
        revert_calls.append(sha)
        return _subprocess_mod.CompletedProcess(args=[], returncode=0, stdout="[main rev1234] Revert ...\n", stderr="")

    _patch_rollback_execute_helpers(monkeypatch)
    monkeypatch.setattr(_agent_mod, "_run_git_revert", _spy_revert)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    decisions = iter([DECISION_ALLOW, DECISION_DENY])

    def _fake_evaluate(request, *, root):
        return HATPRollbackConsumptionResult(
            evidence_id=request.evidence_id,
            hatp_status=HATPVerificationStatus.VALID,
            pb_decision=next(decisions),
            reasons=("test_seam",),
        )

    monkeypatch.setattr(_consumption_mod, "evaluate_for_real_effect", _fake_evaluate)

    result_1 = _agent_mod.execute_rollback(
        HarnessPath(tmp_path), job_id, hatp_evidence_id=_VALID_EVIDENCE_ID
    )
    assert result_1["rolled_back"] is True
    assert len(revert_calls) == 1

    # Reset the job's rollback fields on disk (simulating a fresh Consumption
    # Attempt for the same job -- e.g. a retry after a failed push) rather
    # than the idempotent already_rolled_back short-circuit, which performs
    # no new evaluation at all by design and would prove nothing here.
    job_file = tmp_path / ".pcae" / "remote" / "jobs" / f"{job_id}.json"
    job_document = json.loads(job_file.read_text())
    job_document.pop("rollback_commit_sha", None)
    job_document.pop("rollback_status", None)
    job_document.pop("rolled_back_at", None)
    job_file.write_text(json.dumps(job_document))

    with pytest.raises(ValueError, match="HATP"):
        _agent_mod.execute_rollback(
            HarnessPath(tmp_path), job_id, hatp_evidence_id=_VALID_EVIDENCE_ID
        )
    assert len(revert_calls) == 1  # second attempt performed no additional effect


# ─────────────────────────────────────────────────────────────────────────
# No caller authority override (HMRC-REQ-073/074, attacks #16-#19/#42/#43)
# ─────────────────────────────────────────────────────────────────────────


def test_execute_rollback_signature_has_no_authority_override_params() -> None:
    import inspect

    params = set(inspect.signature(_agent_mod.execute_rollback).parameters)
    forbidden = {
        "approval_present",
        "pb_decision",
        "permission_result",
        "allow",
        "broker",
        "policy",
        "cutover_mode",
        "mandatory",
        "hatp_mandatory",
        "mode",
    }
    assert params.isdisjoint(forbidden)
    assert params == {"root", "job_id", "hatp_evidence_id", "hatp_proof", "hatp_evidence"}


# ─────────────────────────────────────────────────────────────────────────
# Effect-truthfulness (MC-14): real path uses the real-effect entrypoint,
# never the advisory one (attacks #34/#92/#93)
# ─────────────────────────────────────────────────────────────────────────


def test_mandatory_gate_calls_real_effect_entrypoint_not_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    calls: list = []
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    def _fake_real_effect(request, *, root):
        calls.append("real_effect")
        return HATPRollbackConsumptionResult(
            evidence_id=request.evidence_id,
            hatp_status=HATPVerificationStatus.VALID,
            pb_decision=DECISION_ALLOW,
            reasons=(),
        )

    def _fail_if_advisory_called(request, *, root):
        raise AssertionError("evaluate_for_advisory must never be called on the real effect path")

    monkeypatch.setattr(_consumption_mod, "evaluate_for_real_effect", _fake_real_effect)
    monkeypatch.setattr(_consumption_mod, "evaluate_for_advisory", _fail_if_advisory_called)

    result = _agent_mod.execute_rollback(
        HarnessPath(tmp_path), job_id, hatp_evidence_id=_VALID_EVIDENCE_ID
    )
    assert result["rolled_back"] is True
    assert calls == ["real_effect"]


def test_agent_source_never_calls_evaluate_for_advisory() -> None:
    """Static/AST check (item 93): `agent.py` must not reference
    `evaluate_for_advisory` anywhere -- the real `_run_git_revert` path may
    only ever use `evaluate_for_real_effect`."""
    import ast
    import inspect

    source = inspect.getsource(_agent_mod)
    tree = ast.parse(source)
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    attrs = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert "evaluate_for_advisory" not in names
    assert "evaluate_for_advisory" not in attrs


# ─────────────────────────────────────────────────────────────────────────
# Real git effect test (item 60): temporary git repository, not the real
# project repo
# ─────────────────────────────────────────────────────────────────────────


def test_real_git_revert_in_temp_repo_legacy_vs_mandatory(tmp_path: Path, monkeypatch) -> None:
    from pcae.core.paths import HarnessPath as _HP

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
    job_id = "job-real-git-1"
    (jobs_dir / f"{job_id}.json").write_text(
        json.dumps(
            {
                "job_id": job_id,
                "commit_sha": head_before,
                "rollback_approval_state": "approved",
                "requested_agent": "claude-local",
            }
        )
    )
    (results_dir / f"{job_id}-result.json").write_text(
        json.dumps({"changed_files": ["file.txt"], "scope_validation": {}})
    )

    root = _HP(repo)

    # LEGACY_COMPATIBLE: real git revert happens.
    _patch_mode(monkeypatch, CutoverMode.LEGACY_COMPATIBLE)
    result = _agent_mod.execute_rollback(root, job_id)
    assert result["rolled_back"] is True
    assert (repo / "file.txt").read_text() == "v1\n"

    # Second job, same repo state: HATP_MANDATORY with no evidence blocks
    # the effect entirely -- no additional commit created.
    (repo / "file2.txt").write_text("v1\n")
    run("git", "add", "file2.txt")
    run("git", "commit", "-m", "second governed change")
    head_before_2 = _subprocess_mod.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    job_id_2 = "job-real-git-2"
    (jobs_dir / f"{job_id_2}.json").write_text(
        json.dumps(
            {
                "job_id": job_id_2,
                "commit_sha": head_before_2,
                "rollback_approval_state": "approved",
                "requested_agent": "claude-local",
            }
        )
    )
    (results_dir / f"{job_id_2}-result.json").write_text(
        json.dumps({"changed_files": ["file2.txt"], "scope_validation": {}})
    )

    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    log_before = _subprocess_mod.run(
        ["git", "log", "--oneline"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout
    with pytest.raises(ValueError, match="HATP"):
        _agent_mod.execute_rollback(root, job_id_2)
    log_after = _subprocess_mod.run(
        ["git", "log", "--oneline"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout
    assert log_before == log_after  # no new commit -- no partial/silent effect
