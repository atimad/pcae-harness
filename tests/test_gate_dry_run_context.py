"""Tests for GateDryRunContext memoization, freshness, and decision equivalence."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pcae.core.gate_dry_run import build_gate_dry_run, _GATE_DEFS
from pcae.core.gate_dry_run_context import GateDryRunContext

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Decision equivalence — golden invariants
# ---------------------------------------------------------------------------

def test_context_gate_count_equals_direct():
    """Gate count must be 15 with or without context."""
    result = build_gate_dry_run(REPO_ROOT)
    assert result["gate_count"] == 15
    assert len(result["gates"]) == 15


def test_context_all_expected_gate_names():
    """All 15 expected gate IDs must be present."""
    result = build_gate_dry_run(REPO_ROOT)
    expected = {g["gate_id"] for g in _GATE_DEFS}
    actual = {g["gate_id"] for g in result["gates"]}
    assert actual == expected


def test_context_no_gate_produces_allow():
    """No gate should auto-allow in dry-run mode."""
    result = build_gate_dry_run(REPO_ROOT)
    for g in result["gates"]:
        assert g["decision"] != "allow", f"{g['gate_id']} should not allow"


def test_context_all_authorization_false():
    """All gates must have authorization_granted=False."""
    result = build_gate_dry_run(REPO_ROOT)
    for g in result["gates"]:
        assert g["authorization_granted"] is False, f"{g['gate_id']}"


def test_context_all_enforcement_false():
    """All gates must have enforcement_performed=False."""
    result = build_gate_dry_run(REPO_ROOT)
    for g in result["gates"]:
        assert g["enforcement_performed"] is False, f"{g['gate_id']}"


def test_context_required_envelope_fields_present():
    """Envelope fields must be present."""
    result = build_gate_dry_run(REPO_ROOT)
    for field in ("schema_version", "generated_at", "source_command",
                  "repository_root", "dry_run", "taxonomy_version",
                  "gate_count", "gates", "warnings", "errors", "safety_notes"):
        assert field in result, f"Missing envelope field: {field}"


def test_context_required_gate_fields_present():
    """Required gate fields must be present on every gate."""
    result = build_gate_dry_run(REPO_ROOT)
    required = [
        "gate_id", "gate_name", "gate_category", "protected_action",
        "risk_level", "decision", "reason_codes", "human_review_required",
        "evidence_artifacts", "evidence_events", "evidence_decisions",
        "evidence_risks", "allowed_scope", "denied_scope",
        "requested_action", "requested_actor", "requested_files",
        "dry_run", "enforcement_performed", "authorization_granted",
        "safety_notes", "generated_at", "schema_version",
    ]
    for gate in result["gates"]:
        for field in required:
            assert field in gate, f"Missing {field} in {gate['gate_id']}"


def test_context_decisions_are_valid():
    """All decisions must be from the valid vocabulary."""
    valid = {
        "allow", "deny", "requires_human_review", "requires_more_evidence",
        "blocked_by_risk", "blocked_by_scope", "blocked_by_lifecycle_state",
        "blocked_by_missing_artifact", "blocked_by_must_never_repeat_control",
        "unknown",
    }
    result = build_gate_dry_run(REPO_ROOT)
    for g in result["gates"]:
        assert g["decision"] in valid, f"Invalid decision {g['decision']} in {g['gate_id']}"


def test_context_reason_codes_are_lists():
    """All reason_codes must be lists."""
    result = build_gate_dry_run(REPO_ROOT)
    for g in result["gates"]:
        assert isinstance(g["reason_codes"], list)


def test_context_safety_notes_preserved():
    """Safety notes invariants must be preserved."""
    result = build_gate_dry_run(REPO_ROOT)
    sn = result["safety_notes"]
    assert sn["gate_dry_run_only"] is True
    assert sn["backend_invocation_performed"] is False
    assert sn["repo_mutation_performed"] is False
    assert sn["storage_written"] is False
    assert sn["permission_broker_not_implemented"] is True
    assert sn["shell_gate_not_implemented"] is True


def test_context_hard_blocks_preserved():
    """Hard-blocked gates must remain denied."""
    result = build_gate_dry_run(REPO_ROOT)
    gates = {g["gate_id"]: g for g in result["gates"]}
    assert gates["permission_broker_gate"]["decision"] == "deny"
    assert gates["shell_command_gate"]["decision"] == "deny"
    assert gates["storage_write_gate"]["decision"] == "deny"
    assert gates["rollback_gate"]["decision"] == "deny"
    assert gates["prompt_send_gate"]["decision"] == "deny"


def test_context_specific_evaluations_with_params():
    """Gates with specific actions produce sub-evaluations."""
    result = build_gate_dry_run(
        REPO_ROOT,
        requested_action="source_mutation",
        requested_files=["src/pcae/core/gate_dry_run.py"],
    )
    gates = {g["gate_id"]: g for g in result["gates"]}
    assert "scope_evaluation" in gates["scope_check_gate"]
    assert "mutation_evaluation" in gates["source_mutation_gate"]


def test_context_deterministic():
    """Two calls with same parameters must produce same gate IDs and decisions."""
    d1 = build_gate_dry_run(REPO_ROOT)
    d2 = build_gate_dry_run(REPO_ROOT)
    assert d1["gate_count"] == d2["gate_count"]
    ids1 = [g["gate_id"] for g in d1["gates"]]
    ids2 = [g["gate_id"] for g in d2["gates"]]
    assert ids1 == ids2
    decisions1 = [g["decision"] for g in d1["gates"]]
    decisions2 = [g["decision"] for g in d2["gates"]]
    assert decisions1 == decisions2


# ---------------------------------------------------------------------------
# Memoization tests — monkeypatch builders to count calls
# ---------------------------------------------------------------------------

def _patch_counter(module_path: str, func_name: str):
    """Create a mock that counts calls and delegates to the real function."""
    real = __import__(module_path, fromlist=[func_name])
    real_func = getattr(real, func_name)

    counter = {"count": 0}

    def wrapper(*args, **kwargs):
        counter["count"] += 1
        return real_func(*args, **kwargs)

    return wrapper, counter, real_func


def test_task_contract_called_once_per_dry_run():
    """_detect_task_contract should be called once, not 15 times."""
    from pcae.core import gate_dry_run as gdm
    original = gdm._detect_task_contract
    calls = []

    def tracking(repo_root):
        calls.append(1)
        return original(repo_root)

    gdm._detect_task_contract = tracking
    try:
        build_gate_dry_run(REPO_ROOT)
        # After context optimization, called once (via ctx.task_contract)
        assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
    finally:
        gdm._detect_task_contract = original


def test_context_lazy_properties_are_idempotent():
    """Each context property must return the same value on repeated access."""
    ctx = GateDryRunContext(REPO_ROOT)

    # Access twice and compare
    ai1 = ctx.artifact_index
    ai2 = ctx.artifact_index
    assert ai1 is ai2  # Same object reference

    ms1 = ctx.memory_snapshot
    ms2 = ctx.memory_snapshot
    assert ms1 is ms2

    tc1 = ctx.task_contract
    tc2 = ctx.task_contract
    assert tc1 is tc2

    gp1 = ctx.git_porcelain
    gp2 = ctx.git_porcelain
    assert gp1 == gp2  # strings compare by value


def test_context_project_state_lazy_loading():
    """project_state property loads lazily."""
    ctx = GateDryRunContext(REPO_ROOT)
    assert ctx._project_state is None
    ps = ctx.project_state
    assert ctx._project_state is not None
    assert "snapshot" in ps


# ---------------------------------------------------------------------------
# Freshness tests — separate invocations must not share context
# ---------------------------------------------------------------------------

def test_separate_invocations_have_different_contexts():
    """Each build_gate_dry_run() creates a fresh context."""
    ctx_list = []

    original_init = GateDryRunContext.__init__

    def tracking_init(self, repo_root):
        ctx_list.append(self)
        original_init(self, repo_root)

    GateDryRunContext.__init__ = tracking_init
    try:
        build_gate_dry_run(REPO_ROOT)
        build_gate_dry_run(REPO_ROOT)
        assert len(ctx_list) == 2
        assert ctx_list[0] is not ctx_list[1]
    finally:
        GateDryRunContext.__init__ = original_init


def test_no_module_level_context_cache():
    """GateDryRunContext must not be cached at module level."""
    import pcae.core.gate_dry_run_context as ctx_module
    # The module should not have any persistent cache
    assert not hasattr(ctx_module, '_global_context') or \
        getattr(ctx_module, '_global_context', None) is None


# ---------------------------------------------------------------------------
# No-persistence tests
# ---------------------------------------------------------------------------

def test_context_creates_no_pcae_files():
    """GateDryRunContext must not write to .pcae."""
    pcae_dir = REPO_ROOT / ".pcae"
    dirs_to_check = [
        pcae_dir / "cache", pcae_dir / "gates", pcae_dir / "state",
        pcae_dir / "decisions", pcae_dir / "context",
    ]
    before = {d: d.exists() for d in dirs_to_check}

    ctx = GateDryRunContext(REPO_ROOT)
    _ = ctx.project_state
    _ = ctx.task_contract
    _ = ctx.git_porcelain
    _ = ctx.git_branch
    _ = ctx.git_ahead_count

    for d, existed in before.items():
        if not existed:
            assert not d.exists(), f"{d} was created by GateDryRunContext"


def test_context_no_cache_after_dry_run():
    """After build_gate_dry_run, no cache files should exist."""
    pcae_dir = REPO_ROOT / ".pcae"
    cache_dirs = [
        pcae_dir / "cache", pcae_dir / "gates", pcae_dir / "broker",
        pcae_dir / "shell", pcae_dir / "state",
    ]
    before = {d: d.exists() for d in cache_dirs}
    build_gate_dry_run(REPO_ROOT)
    for d, existed in before.items():
        if not existed:
            assert not d.exists(), f"{d} was created"
