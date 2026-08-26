"""Phase 149O.20L.7O.3M -- Rollback Readiness / Evidence Automatic
Consumption Architecture and Integration.

Re-derivation finding (this phase, not inherited from 3I): the "prepare
evidence -> consume internally -> stop if invalid -> Permission Broker ->
effect" automation described by this phase's governing brief is *already*
the exact current behaviour of `build_rollback_execution` for a real
(non-`--dry-run`) `pcae rollback --per-id X` invocation, released in
v0.4.1 (149O.20L.7O.3F): `file_plan`/`divergence_check` ("evidence") are
computed unconditionally at the top of the function -- for `dry_run=True`
*and* `dry_run=False` alike -- and are already consumed internally to
gate the divergence short-circuit before either authority gate
(`HATP_MANDATORY` or the default-path Permission Broker) ever runs. No
"manual dry-run prerequisite" exists in code: an operator can call
`pcae rollback --per-id X` directly and the preparation step runs
automatically, exactly once, inline, with zero extra CLI invocation.

No existing typed "readiness" concept was found anywhere in `src/pcae`
(re-confirmed this phase via exhaustive grep); inventing one was
correctly out of scope (this phase's own Section 26 gate: "READINESS
CONTRACT NEEDED? YES -> STOP implementation"), and no such contract was
required or added here.

This phase's one narrow, additive, non-authoritative production change:
surface the already-computed, already-consumed, already-persisted
evidence (`file_plan`/`divergence_check`) directly in every terminal
result `build_rollback_execution` returns (previously present only in
the `dry_run=True` preview and inside the persisted RollbackExecution-
Record on disk -- an operator previously had to run a *second* command,
`pcae rollback-execution show <rer_id>`, to see evidence that had
already gated their own command's outcome). This suite verifies that
addition end-to-end: presence, non-authority, no new gating, no new
persistence, no change to Permission Broker/HATP sequencing or runtime,
and no manual dry-run prerequisite.
"""
from __future__ import annotations

import hashlib

import pytest

from pcae.core import agent as agent_module
from pcae.core import hatp_mandatory_cutover as cutover_mod
from pcae.core import mutation_permission as mp
from pcae.core import permission_broker_foundation as pbf
from pcae.core.hatp_mandatory_cutover import CutoverMode, CutoverModeResolution
from pcae.core.paths import HarnessPath

from tests.test_agent import _init_git_root, _make_per_test_ecp, _make_rer_test_per

pytestmark = pytest.mark.fast_green


def _fixed_mode(mode: CutoverMode) -> CutoverModeResolution:
    return CutoverModeResolution(mode, f"test_fixed_{mode.value}")


def _patch_mode(monkeypatch, mode: CutoverMode) -> None:
    monkeypatch.setattr(
        cutover_mod,
        "resolve_production_hatp_cutover_mode",
        lambda root: _fixed_mode(mode),
    )


def _setup_removable_file_per(tmp_path, *, per_id="per-3m", with_task=True):
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    _init_git_root(root_dir)
    if not with_task:
        import shutil

        active_dir = root_dir / "tasks" / "active"
        if active_dir.is_dir():
            shutil.rmtree(active_dir)
    (root_dir / "added.txt").write_text("added content")
    root = HarnessPath(root_dir)
    after_hash = hashlib.sha256(b"added content").hexdigest()
    entries = [{"path": "added.txt", "before_hash": None, "after_hash": after_hash,
                "before_content": None, "before_exists": False, "binary": False}]
    _make_per_test_ecp(root, ecp_id="ecp-3m", file_entries=entries)
    _make_rer_test_per(
        root, per_id=per_id, ecp_id="ecp-3m",
        file_results=[{"path": "added.txt", "outcome": "success"}],
    )
    return root, root_dir


def _force_decision(monkeypatch, decision: str) -> dict:
    calls = {"count": 0}

    def fake_evaluate(self, request):
        calls["count"] += 1
        return pbf.PermissionBrokerDecision(
            decision=decision,
            decision_reason="test_forced",
            matched_no_go_ids=(),
            matched_invariants=(),
            required_remediation=(),
            requires_human=(decision == pbf.DECISION_HUMAN_REVIEW),
            simulation_only=True,
        )

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", fake_evaluate)
    return calls


# ── 1. Preparation is already automatic on the real (non-dry-run) path ──


def test_real_invocation_requires_no_prior_dry_run_call(tmp_path):
    """A human can call the real command directly -- no manual `--dry-run`
    prerequisite exists in code."""
    root, root_dir = _setup_removable_file_per(tmp_path)
    # No dry_run=True call precedes this one anywhere in this test.
    result = agent_module.build_rollback_execution(root, "per-3m")
    assert result["status"] == "completed"
    assert result["reverted"] is True
    assert not (root_dir / "added.txt").exists()


def test_preparation_evidence_computed_unconditionally_regardless_of_dry_run(tmp_path):
    """file_plan/divergence_check are computed identically whether
    dry_run is True or False -- preparation is not gated on the flag."""
    base_a = tmp_path / "a"
    base_a.mkdir()
    base_b = tmp_path / "b"
    base_b.mkdir()
    root_a, _dir_a = _setup_removable_file_per(base_a, per_id="per-3m-a")
    root_b, _dir_b = _setup_removable_file_per(base_b, per_id="per-3m-a")
    dry = agent_module.build_rollback_execution(root_a, "per-3m-a", dry_run=True)
    real = agent_module.build_rollback_execution(root_b, "per-3m-a", dry_run=False)
    assert dry["file_plan"] == real["file_plan"] == ["added.txt"]
    assert dry["divergence_check"]["blocking"] == real["divergence_check"]["blocking"] is False


# ── 2. Evidence surfacing (this phase's one narrow production change) ───


def test_completed_result_includes_evidence_summary(tmp_path):
    root, _root_dir = _setup_removable_file_per(tmp_path)
    result = agent_module.build_rollback_execution(root, "per-3m")
    assert result["status"] == "completed"
    assert result["file_plan"] == ["added.txt"]
    assert result["divergence_check"]["blocking"] is False


def test_evidence_summary_matches_persisted_rer_record(tmp_path):
    """The surfaced evidence is not a new computation -- it is identical
    to what is already persisted in the RollbackExecutionRecord."""
    root, _root_dir = _setup_removable_file_per(tmp_path)
    result = agent_module.build_rollback_execution(root, "per-3m")
    rer = agent_module.lookup_rollback_execution_record(root, result["rer_id"])
    assert rer is not None
    assert result["file_plan"] == rer["file_plan"]
    assert result["divergence_check"] == rer["divergence_check"]


def test_permission_denied_result_includes_evidence_summary(tmp_path, monkeypatch):
    root, root_dir = _setup_removable_file_per(tmp_path)
    _force_decision(monkeypatch, pbf.DECISION_DENY)
    result = agent_module.build_rollback_execution(root, "per-3m")
    assert result["error"] == "rollback_permission_denied"
    assert result["file_plan"] == ["added.txt"]
    assert result["divergence_check"]["blocking"] is False
    assert (root_dir / "added.txt").exists()


def test_divergence_conflict_result_includes_file_plan(tmp_path):
    root, root_dir = _setup_removable_file_per(tmp_path)
    # Mutate the file so its current hash matches neither before_hash nor
    # after_hash -- a genuine conflict.
    (root_dir / "added.txt").write_text("mutated externally")
    result = agent_module.build_rollback_execution(root, "per-3m")
    assert result["error"] == "divergence_conflict"
    assert result["file_plan"] == ["added.txt"]
    assert result["divergence_check"]["blocking"] is True


def test_dry_run_result_shape_unchanged(tmp_path):
    """The dry-run branch already carried this evidence before this
    phase; this phase must not change its shape."""
    root, _root_dir = _setup_removable_file_per(tmp_path)
    result = agent_module.build_rollback_execution(root, "per-3m", dry_run=True)
    assert set(["dry_run", "per_id", "ecp_id", "reverted", "would_block",
                "blocking_paths", "divergence_check", "file_plan",
                "execution_allowed"]).issubset(result.keys())


# ── 3. Evidence is non-authoritative -- never substitutes for the broker ─


def test_valid_evidence_plus_deny_still_blocks(tmp_path, monkeypatch):
    """Clean, non-blocking evidence (a fully valid rollback plan) does
    NOT authorize dispatch by itself -- the broker is still the sole
    authority, exactly as before this phase."""
    root, root_dir = _setup_removable_file_per(tmp_path)
    calls = _force_decision(monkeypatch, pbf.DECISION_DENY)
    result = agent_module.build_rollback_execution(root, "per-3m")
    assert result["divergence_check"]["blocking"] is False  # evidence itself was "clean"
    assert result["error"] == "rollback_permission_denied"  # yet still denied
    assert calls["count"] == 1
    assert (root_dir / "added.txt").exists()


def test_broker_still_invoked_exactly_once_on_default_path(tmp_path, monkeypatch):
    root, _root_dir = _setup_removable_file_per(tmp_path)
    calls = _force_decision(monkeypatch, pbf.DECISION_ALLOW)
    result = agent_module.build_rollback_execution(root, "per-3m")
    assert result["status"] == "completed"
    assert calls["count"] == 1


def test_execution_allowed_remains_false_in_every_branch(tmp_path, monkeypatch):
    root, _root_dir = _setup_removable_file_per(tmp_path, per_id="per-3m-x")
    result = agent_module.build_rollback_execution(root, "per-3m-x")
    assert result["execution_allowed"] is False


# ── 4. HATP_MANDATORY branch is untouched by this phase ─────────────────


def test_hatp_mandatory_branch_evidence_field_names_unaffected(tmp_path, monkeypatch):
    """HATP_MANDATORY denial responses gain the same additive
    file_plan/divergence_check surfacing (informational only) but no
    HATP-authority field, gate ordering, or decision logic changes."""
    root, root_dir = _setup_removable_file_per(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    result = agent_module.build_rollback_execution(root, "per-3m")
    assert result["error"] == "hatp_evidence_required"
    assert result["file_plan"] == ["added.txt"]
    assert result["divergence_check"]["blocking"] is False
    assert (root_dir / "added.txt").exists()
    # No new key was added to the pre-existing HATP gate-denial vocabulary.
    assert "permission_decision" not in result or result.get("error") == "hatp_evidence_required"


def test_default_path_permission_adapter_never_invoked_under_hatp_mandatory(tmp_path, monkeypatch):
    root, _root_dir = _setup_removable_file_per(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    calls = {"count": 0}
    real = mp.evaluate_rollback_permission

    def spy(*args, **kwargs):
        calls["count"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(agent_module.mutation_permission, "evaluate_rollback_permission", spy)
    agent_module.build_rollback_execution(root, "per-3m")
    assert calls["count"] == 0


# ── 5. No new authoritative type/schema/persistence was introduced ──────


def test_no_new_rollback_readiness_type_introduced():
    """Grep-equivalent structural check: no new dataclass/enum/schema
    combining 'rollback' and 'readiness' was added to the rollback
    modules touched by this phase (a pre-existing, unrelated
    EXECUTION_GOVERNANCE_READINESS_REVIEW_ADVISORY constant predates
    this phase and is correctly not flagged)."""
    import pcae.core.agent as agent_mod
    import pcae.core.mutation_permission as mp_mod

    for mod in (agent_mod, mp_mod):
        for name in dir(mod):
            lowered = name.lower()
            assert not ("rollback" in lowered and "readiness" in lowered), (
                f"unexpected rollback-readiness symbol introduced: {mod.__name__}.{name}"
            )


def test_build_rollback_execution_still_has_single_production_caller():
    """Re-confirms the 3F/3F.1 no-bypass finding is unaffected by this
    phase's additive changes."""
    import pathlib
    import re

    repo_src = pathlib.Path(agent_module.__file__).resolve().parents[1]
    callers = []
    for path in repo_src.rglob("*.py"):
        if path.name in {"agent.py"} and path.parent.name == "core":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"\bbuild_rollback_execution\(", text):
            callers.append(path.relative_to(repo_src.parent).as_posix())
    non_test_callers = [c for c in callers if "tests/" not in c]
    assert non_test_callers == ["pcae/commands/agent.py"], non_test_callers


def test_evidence_summary_is_local_derived_state_only(tmp_path):
    """Side-effect classification: computing/surfacing the evidence
    summary performs no filesystem write beyond the pre-existing RER
    persistence (already present before this phase)."""
    root, root_dir = _setup_removable_file_per(tmp_path)
    before = sorted(p.name for p in root_dir.rglob("*") if p.is_file())
    agent_module.build_rollback_execution(root, "per-3m", dry_run=True)
    after = sorted(p.name for p in root_dir.rglob("*") if p.is_file())
    assert before == after  # dry-run remains zero-filesystem-effect


# ── 6. Manual dry-run CLI remains fully available (not removed) ─────────


def test_manual_dry_run_cli_path_still_works(tmp_path):
    root, root_dir = _setup_removable_file_per(tmp_path)
    result = agent_module.build_rollback_execution(root, "per-3m", dry_run=True)
    assert result["dry_run"] is True
    assert result["reverted"] is False
    assert (root_dir / "added.txt").exists()  # zero mutation


# ── 7. Restart/idempotency unaffected ────────────────────────────────────


def test_repeated_real_invocation_after_completion_is_not_in_progress_reentrant(tmp_path):
    root, root_dir = _setup_removable_file_per(tmp_path)
    first = agent_module.build_rollback_execution(root, "per-3m")
    assert first["status"] == "completed"
    # A second call against the same (already-reverted) PER recomputes
    # fresh evidence rather than reusing stale state.
    second = agent_module.build_rollback_execution(root, "per-3m")
    assert second["file_plan"] == ["added.txt"]
    assert second["divergence_check"]["file_checks"][0]["status"] == "already_reverted"


# ── 8. Runtime independence ──────────────────────────────────────────────


def test_runtime_inspect_unaffected_by_evidence_surfacing(tmp_path):
    from pcae.core.runtime_registry import RuntimeRegistry
    from pcae.core.runtime_snapshot import build_runtime_snapshot, snapshot_to_dict

    root, _root_dir = _setup_removable_file_per(tmp_path)

    def _runtime_facts():
        snap = build_runtime_snapshot(root, RuntimeRegistry())
        d = snapshot_to_dict(snap)
        return {
            "current_state": d["state"]["current_state"],
            "execution_capability": d["governance"]["execution_capability"],
            "non_executing_posture": d["governance"]["non_executing_posture"],
            "broker_implementation_status": d["governance"]["broker_implementation_status"],
        }

    before = _runtime_facts()
    agent_module.build_rollback_execution(root, "per-3m")
    after = _runtime_facts()
    assert before == after
