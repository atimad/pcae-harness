"""Tests for 88Y.5 project-state shared evidence optimization.

Verifies decision equivalence, memoization, freshness, and no-persistence
guarantees when build_project_state() and the upstream build functions receive
a GateDryRunContext instead of computing their dependencies from scratch.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pcae.core.gate_dry_run_context import GateDryRunContext
from pcae.core.project_state import build_project_state
import pcae.core.artifact_index as ai_module
import pcae.core.memory_snapshot as ms_module
import pcae.core.governance_timeline as gt_module
import pcae.core.decision_log as dl_module
import pcae.core.risk_register as rr_module
import pcae.core.project_state as ps_module

REPO_ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.fast_green


# ---------------------------------------------------------------------------
# Decision equivalence
# ---------------------------------------------------------------------------

def test_build_project_state_with_ctx_matches_standalone_schema_version():
    ctx = GateDryRunContext(repo_root=REPO_ROOT)
    with_ctx = build_project_state(REPO_ROOT, ctx=ctx)
    standalone = build_project_state(REPO_ROOT)
    assert with_ctx["schema_version"] == standalone["schema_version"]


def test_build_project_state_with_ctx_matches_standalone_snapshot_keys():
    ctx = GateDryRunContext(repo_root=REPO_ROOT)
    with_ctx = build_project_state(REPO_ROOT, ctx=ctx)
    standalone = build_project_state(REPO_ROOT)
    assert set(with_ctx["snapshot"].keys()) == set(standalone["snapshot"].keys())


def test_build_project_state_with_ctx_matches_standalone_layer_summary():
    ctx = GateDryRunContext(repo_root=REPO_ROOT)
    with_ctx = build_project_state(REPO_ROOT, ctx=ctx)
    standalone = build_project_state(REPO_ROOT)
    assert with_ctx["layer_summary"]["artifact_index"] == standalone["layer_summary"]["artifact_index"]
    assert with_ctx["layer_summary"]["governance_timeline"] == standalone["layer_summary"]["governance_timeline"]
    assert with_ctx["layer_summary"]["decision_log"] == standalone["layer_summary"]["decision_log"]
    assert with_ctx["layer_summary"]["risk_register"] == standalone["layer_summary"]["risk_register"]


def test_build_project_state_with_ctx_authorization_flags_unchanged():
    ctx = GateDryRunContext(repo_root=REPO_ROOT)
    with_ctx = build_project_state(REPO_ROOT, ctx=ctx)
    snap = with_ctx["snapshot"]
    assert snap["execution_authorized"] is False
    assert snap["backend_invocation_authorized"] is False
    assert snap["prompt_sending_authorized"] is False
    assert snap["capture_authorized"] is False
    assert snap["intake_authorized"] is False
    assert snap["adoption_authorized"] is False
    assert snap["source_mutation_authorized"] is False
    assert snap["test_mutation_authorized"] is False


def test_build_project_state_with_ctx_safety_notes_preserved():
    ctx = GateDryRunContext(repo_root=REPO_ROOT)
    with_ctx = build_project_state(REPO_ROOT, ctx=ctx)
    notes = with_ctx["safety_notes"]
    assert notes["project_state_is_read_only"] is True
    assert notes["project_state_does_not_authorize_execution"] is True
    assert notes["project_state_does_not_authorize_backend_invocation"] is True
    assert notes["project_state_does_not_authorize_adoption"] is True
    assert notes["project_state_does_not_authorize_commit_or_push"] is True
    assert notes["generated_cache_created"] is False
    assert notes["pcae_storage_created"] is False


def test_build_project_state_with_ctx_snapshot_id_format():
    ctx = GateDryRunContext(repo_root=REPO_ROOT)
    with_ctx = build_project_state(REPO_ROOT, ctx=ctx)
    snap_id = with_ctx["snapshot"]["snapshot_id"]
    assert snap_id.startswith("pstate-"), f"Unexpected snapshot_id: {snap_id}"
    assert len(snap_id) > 10


def test_build_project_state_with_ctx_risk_counts_match():
    ctx = GateDryRunContext(repo_root=REPO_ROOT)
    with_ctx = build_project_state(REPO_ROOT, ctx=ctx)
    standalone = build_project_state(REPO_ROOT)
    rr_with = with_ctx["layer_summary"]["risk_register"]
    rr_alone = standalone["layer_summary"]["risk_register"]
    assert rr_with["risk_count"] == rr_alone["risk_count"]
    assert rr_with["active_count"] == rr_alone["active_count"]
    assert rr_with["accepted_count"] == rr_alone["accepted_count"]


def test_build_project_state_with_ctx_repository_root_preserved():
    ctx = GateDryRunContext(repo_root=REPO_ROOT)
    with_ctx = build_project_state(REPO_ROOT, ctx=ctx)
    assert with_ctx["repository_root"] == str(REPO_ROOT)


# ---------------------------------------------------------------------------
# Memoization — upstream build functions called fewer times when ctx provided
# ---------------------------------------------------------------------------

def test_build_memory_snapshot_with_ctx_uses_artifact_index_once():
    """build_artifact_index should be called once (via ctx.artifact_index), not twice."""
    from pcae.core.memory_snapshot import build_memory_snapshot

    calls: list[object] = []
    original = ai_module.build_artifact_index
    try:
        ai_module.build_artifact_index = lambda root: (calls.append(root), original(root))[1]
        ctx = GateDryRunContext(repo_root=REPO_ROOT)
        _ = ctx.artifact_index
        _ = build_memory_snapshot(REPO_ROOT, ctx=ctx)
        assert len(calls) == 1, f"Expected 1 build_artifact_index call, got {len(calls)}"
    finally:
        ai_module.build_artifact_index = original


def test_build_governance_timeline_with_ctx_skips_unused_calls():
    """When ctx is provided, governance_timeline skips the artifact_index and memory_snapshot calls."""
    from pcae.core.governance_timeline import build_governance_timeline

    ai_calls: list[object] = []
    ms_calls: list[object] = []
    orig_ai = ai_module.build_artifact_index
    orig_ms = ms_module.build_memory_snapshot
    try:
        ai_module.build_artifact_index = lambda root: (ai_calls.append(root), orig_ai(root))[1]
        ms_module.build_memory_snapshot = lambda root, ctx=None: (ms_calls.append(root), orig_ms(root, ctx=ctx))[1]
        ctx = GateDryRunContext(repo_root=REPO_ROOT)
        _ = build_governance_timeline(REPO_ROOT, ctx=ctx)
        assert len(ai_calls) == 0, f"Expected 0 artifact_index calls, got {len(ai_calls)}"
        assert len(ms_calls) == 0, f"Expected 0 memory_snapshot calls, got {len(ms_calls)}"
    finally:
        ai_module.build_artifact_index = orig_ai
        ms_module.build_memory_snapshot = orig_ms


def test_build_decision_log_with_ctx_skips_all_upstream_calls():
    """When ctx is provided, decision_log skips all 3 upstream build calls."""
    from pcae.core.decision_log import build_decision_log

    ai_calls: list[object] = []
    ms_calls: list[object] = []
    gt_calls: list[object] = []
    orig_ai = ai_module.build_artifact_index
    orig_ms = ms_module.build_memory_snapshot
    orig_gt = gt_module.build_governance_timeline
    try:
        ai_module.build_artifact_index = lambda root: (ai_calls.append(root), orig_ai(root))[1]
        ms_module.build_memory_snapshot = lambda root, ctx=None: (ms_calls.append(root), orig_ms(root, ctx=ctx))[1]
        gt_module.build_governance_timeline = lambda root, ctx=None: (gt_calls.append(root), orig_gt(root, ctx=ctx))[1]
        ctx = GateDryRunContext(repo_root=REPO_ROOT)
        _ = build_decision_log(REPO_ROOT, ctx=ctx)
        assert len(ai_calls) == 0, f"Expected 0 artifact_index calls, got {len(ai_calls)}"
        assert len(ms_calls) == 0, f"Expected 0 memory_snapshot calls, got {len(ms_calls)}"
        assert len(gt_calls) == 0, f"Expected 0 governance_timeline calls, got {len(gt_calls)}"
    finally:
        ai_module.build_artifact_index = orig_ai
        ms_module.build_memory_snapshot = orig_ms
        gt_module.build_governance_timeline = orig_gt


def test_build_risk_register_with_ctx_skips_all_upstream_calls():
    """When ctx is provided, risk_register skips all 4 upstream build calls."""
    from pcae.core.risk_register import build_risk_register

    ai_calls: list[object] = []
    ms_calls: list[object] = []
    gt_calls: list[object] = []
    dl_calls: list[object] = []
    orig_ai = ai_module.build_artifact_index
    orig_ms = ms_module.build_memory_snapshot
    orig_gt = gt_module.build_governance_timeline
    orig_dl = dl_module.build_decision_log
    try:
        ai_module.build_artifact_index = lambda root: (ai_calls.append(root), orig_ai(root))[1]
        ms_module.build_memory_snapshot = lambda root, ctx=None: (ms_calls.append(root), orig_ms(root, ctx=ctx))[1]
        gt_module.build_governance_timeline = lambda root, ctx=None: (gt_calls.append(root), orig_gt(root, ctx=ctx))[1]
        dl_module.build_decision_log = lambda root, ctx=None: (dl_calls.append(root), orig_dl(root, ctx=ctx))[1]
        ctx = GateDryRunContext(repo_root=REPO_ROOT)
        _ = build_risk_register(REPO_ROOT, ctx=ctx)
        assert len(ai_calls) == 0, f"Expected 0 artifact_index calls, got {len(ai_calls)}"
        assert len(ms_calls) == 0, f"Expected 0 memory_snapshot calls, got {len(ms_calls)}"
        assert len(gt_calls) == 0, f"Expected 0 governance_timeline calls, got {len(gt_calls)}"
        assert len(dl_calls) == 0, f"Expected 0 decision_log calls, got {len(dl_calls)}"
    finally:
        ai_module.build_artifact_index = orig_ai
        ms_module.build_memory_snapshot = orig_ms
        gt_module.build_governance_timeline = orig_gt
        dl_module.build_decision_log = orig_dl


def test_build_project_state_with_ctx_artifact_index_called_once():
    """build_artifact_index should be called exactly once across the full ctx.project_state path."""
    calls: list[object] = []
    original = ai_module.build_artifact_index
    try:
        ai_module.build_artifact_index = lambda root: (calls.append(root), original(root))[1]
        ctx = GateDryRunContext(repo_root=REPO_ROOT)
        _ = ctx.project_state
        assert len(calls) == 1, f"Expected 1 build_artifact_index call, got {len(calls)}"
    finally:
        ai_module.build_artifact_index = original


def test_build_project_state_with_ctx_all_builders_called_once():
    """Each build function called at most once when ctx orchestrates project_state."""
    ai_calls: list[object] = []
    ms_calls: list[object] = []
    gt_calls: list[object] = []
    dl_calls: list[object] = []
    rr_calls: list[object] = []
    orig_ai = ai_module.build_artifact_index
    orig_ms = ms_module.build_memory_snapshot
    orig_gt = gt_module.build_governance_timeline
    orig_dl = dl_module.build_decision_log
    orig_rr = rr_module.build_risk_register
    try:
        ai_module.build_artifact_index = lambda root: (ai_calls.append(root), orig_ai(root))[1]
        ms_module.build_memory_snapshot = lambda root, ctx=None: (ms_calls.append(root), orig_ms(root, ctx=ctx))[1]
        gt_module.build_governance_timeline = lambda root, ctx=None: (gt_calls.append(root), orig_gt(root, ctx=ctx))[1]
        dl_module.build_decision_log = lambda root, ctx=None: (dl_calls.append(root), orig_dl(root, ctx=ctx))[1]
        rr_module.build_risk_register = lambda root, ctx=None: (rr_calls.append(root), orig_rr(root, ctx=ctx))[1]
        ctx = GateDryRunContext(repo_root=REPO_ROOT)
        _ = ctx.project_state
        assert len(ai_calls) == 1, f"build_artifact_index called {len(ai_calls)}× (expected 1)"
        assert len(ms_calls) == 1, f"build_memory_snapshot called {len(ms_calls)}× (expected 1)"
        assert len(gt_calls) == 1, f"build_governance_timeline called {len(gt_calls)}× (expected 1)"
        assert len(dl_calls) == 1, f"build_decision_log called {len(dl_calls)}× (expected 1)"
        assert len(rr_calls) == 1, f"build_risk_register called {len(rr_calls)}× (expected 1)"
    finally:
        ai_module.build_artifact_index = orig_ai
        ms_module.build_memory_snapshot = orig_ms
        gt_module.build_governance_timeline = orig_gt
        dl_module.build_decision_log = orig_dl
        rr_module.build_risk_register = orig_rr


def test_project_state_ctx_idempotent_on_repeated_access():
    """ctx.project_state returns the same object on repeated access (memoized)."""
    ctx = GateDryRunContext(repo_root=REPO_ROOT)
    first = ctx.project_state
    second = ctx.project_state
    assert first is second


# ---------------------------------------------------------------------------
# Freshness — separate ctx instances produce independent results
# ---------------------------------------------------------------------------

def test_project_state_separate_ctx_instances_are_independent():
    """Two separate GateDryRunContext instances must not share any cached state."""
    ctx1 = GateDryRunContext(repo_root=REPO_ROOT)
    ctx2 = GateDryRunContext(repo_root=REPO_ROOT)
    ps1 = ctx1.project_state
    ps2 = ctx2.project_state
    assert ps1 is not ps2


def test_project_state_ctx2_recomputes_after_ctx1_accessed():
    """Accessing ctx1.project_state must not pre-populate ctx2."""
    calls: list[object] = []
    original = ps_module.build_project_state
    try:
        ps_module.build_project_state = lambda root, ctx=None: (calls.append(root), original(root, ctx=ctx))[1]
        ctx1 = GateDryRunContext(repo_root=REPO_ROOT)
        ctx2 = GateDryRunContext(repo_root=REPO_ROOT)
        _ = ctx1.project_state
        _ = ctx2.project_state
        assert len(calls) == 2, f"Expected 2 build_project_state calls, got {len(calls)}"
    finally:
        ps_module.build_project_state = original


def test_build_project_state_standalone_still_works_without_ctx():
    """build_project_state must remain fully functional without ctx (backward compat)."""
    result = build_project_state(REPO_ROOT)
    assert result["schema_version"] == "0.1"
    assert "snapshot" in result
    assert result["snapshot"]["execution_authorized"] is False


# ---------------------------------------------------------------------------
# No-persistence — no files written under .pcae
# ---------------------------------------------------------------------------

def test_project_state_ctx_no_pcae_files_created():
    """ctx.project_state must not create any files under .pcae."""
    pcae_dir = REPO_ROOT / ".pcae"
    files_before: set[Path] = set(pcae_dir.rglob("*")) if pcae_dir.exists() else set()
    ctx = GateDryRunContext(repo_root=REPO_ROOT)
    _ = ctx.project_state
    files_after: set[Path] = set(pcae_dir.rglob("*")) if pcae_dir.exists() else set()
    new_files = files_after - files_before
    assert not new_files, f"Unexpected files created: {new_files}"


def test_build_project_state_with_ctx_no_pcae_cache_dirs():
    """No cache subdirectories must be created after build_project_state(ctx=ctx)."""
    forbidden_dirs = [
        REPO_ROOT / ".pcae" / "cache",
        REPO_ROOT / ".pcae" / "gates",
        REPO_ROOT / ".pcae" / "state",
        REPO_ROOT / ".pcae" / "decisions",
        REPO_ROOT / ".pcae" / "context",
    ]
    ctx = GateDryRunContext(repo_root=REPO_ROOT)
    _ = build_project_state(REPO_ROOT, ctx=ctx)
    for d in forbidden_dirs:
        assert not d.exists(), f"Unexpected cache dir created: {d}"


# ---------------------------------------------------------------------------
# Backward compatibility — build functions without ctx
# ---------------------------------------------------------------------------

def test_build_memory_snapshot_backward_compatible():
    from pcae.core.memory_snapshot import build_memory_snapshot
    result = build_memory_snapshot(REPO_ROOT)
    assert "snapshot" in result
    assert result["snapshot"]["memory_model_version"] == "0.1"


def test_build_governance_timeline_backward_compatible():
    from pcae.core.governance_timeline import build_governance_timeline
    result = build_governance_timeline(REPO_ROOT)
    assert "events" in result
    assert isinstance(result["events"], list)


def test_build_decision_log_backward_compatible():
    from pcae.core.decision_log import build_decision_log
    result = build_decision_log(REPO_ROOT)
    assert "decisions" in result
    assert isinstance(result["decisions"], list)


def test_build_risk_register_backward_compatible():
    from pcae.core.risk_register import build_risk_register
    result = build_risk_register(REPO_ROOT)
    assert "risks" in result
    assert isinstance(result["risks"], list)
