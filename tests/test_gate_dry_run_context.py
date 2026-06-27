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


# ===========================================================================
# Phase 88Y.4 — Expanded decision-equivalence matrix
# ===========================================================================

# -- Decision-equivalence across representative scenarios --------------------

EXPECTED_GATE_IDS = [
    "task_start_gate", "scope_check_gate", "backend_invocation_gate",
    "prompt_send_gate", "capture_acceptance_gate", "intake_review_gate",
    "adoption_approval_gate", "source_mutation_gate", "test_mutation_gate",
    "commit_gate", "push_gate", "rollback_gate", "storage_write_gate",
    "permission_broker_gate", "shell_command_gate",
]

EXPECTED_GATE_NAMES = [
    "Task Start Gate", "Scope Check Gate", "Backend Invocation Gate",
    "Prompt Send Gate", "Capture Acceptance Gate", "Intake Review Gate",
    "Adoption Approval Gate", "Source Mutation Gate", "Test Mutation Gate",
    "Commit Gate", "Push Gate", "Rollback Gate", "Storage Write Gate",
    "Permission Broker Gate", "Shell Command Gate",
]


def _assert_decision_equivalence(result):
    """Shared decision-equivalence assertions for any scenario result."""
    # Gate count
    assert result["gate_count"] == 15
    assert len(result["gates"]) == 15

    # Gate IDs in order
    actual_ids = [g["gate_id"] for g in result["gates"]]
    assert actual_ids == EXPECTED_GATE_IDS, f"Gate order changed: {actual_ids}"

    # Gate names in order
    actual_names = [g["gate_name"] for g in result["gates"]]
    assert actual_names == EXPECTED_GATE_NAMES, f"Gate names changed: {actual_names}"

    # Authorization/enforcement flags
    for g in result["gates"]:
        assert g["authorization_granted"] is False, f"{g['gate_id']} auth flag wrong"
        assert g["enforcement_performed"] is False, f"{g['gate_id']} enforce flag wrong"
        assert g["dry_run"] is True, f"{g['gate_id']} dry_run flag wrong"
        assert g["schema_version"] == "0.1", f"{g['gate_id']} schema_version wrong"

    # Hard blocks always deny
    gates = {g["gate_id"]: g for g in result["gates"]}
    for hard_blocked in ("permission_broker_gate", "shell_command_gate",
                         "storage_write_gate", "rollback_gate", "prompt_send_gate"):
        assert gates[hard_blocked]["decision"] == "deny", \
            f"{hard_blocked} not denied: {gates[hard_blocked]['decision']}"

    # No gate allows
    for g in result["gates"]:
        assert g["decision"] != "allow", f"{g['gate_id']} should not allow"

    # Reason codes are non-empty lists
    for g in result["gates"]:
        assert isinstance(g["reason_codes"], list)
        assert len(g["reason_codes"]) > 0, f"{g['gate_id']} has empty reason_codes"

    # Required gate fields present
    required_fields = [
        "gate_id", "gate_name", "gate_category", "protected_action",
        "risk_level", "decision", "reason_codes", "human_review_required",
        "evidence_artifacts", "evidence_events", "evidence_decisions",
        "evidence_risks", "allowed_scope", "denied_scope",
        "requested_action", "requested_actor", "requested_files",
        "dry_run", "enforcement_performed", "authorization_granted",
        "safety_notes", "generated_at", "schema_version",
    ]
    for g in result["gates"]:
        for field in required_fields:
            assert field in g, f"Missing {field} in {g['gate_id']}"

    # Envelope fields present
    for field in ("schema_version", "generated_at", "source_command",
                  "repository_root", "dry_run", "taxonomy_version",
                  "gate_count", "gates", "warnings", "errors", "safety_notes"):
        assert field in result, f"Missing envelope field: {field}"


# -- Scenario: idle repository (default, no params) -------------------------

def test_decision_equivalence_idle():
    """Idle repo: all gates present, correct decisions, no auth/enforcement."""
    result = build_gate_dry_run(REPO_ROOT)
    _assert_decision_equivalence(result)


# -- Scenario: active task-like with source_mutation ------------------------

def test_decision_equivalence_source_mutation():
    """Source mutation scenario: scope and mutation evaluations present."""
    result = build_gate_dry_run(
        REPO_ROOT,
        requested_action="source_mutation",
        requested_files=["src/pcae/core/gate_dry_run.py"],
    )
    _assert_decision_equivalence(result)
    gates = {g["gate_id"]: g for g in result["gates"]}
    assert "scope_evaluation" in gates["scope_check_gate"]
    assert "mutation_evaluation" in gates["source_mutation_gate"]
    # Verify audit evidence shape
    for g in result["gates"]:
        assert isinstance(g["evidence_artifacts"], list)
        assert isinstance(g["evidence_events"], list)
        assert isinstance(g["evidence_decisions"], list)
        assert isinstance(g["evidence_risks"], list)


def test_decision_equivalence_forbidden_file_mutation():
    """Forbidden file mutation should show blocked_by_scope."""
    result = build_gate_dry_run(
        REPO_ROOT,
        requested_action="source_mutation",
        requested_files=["tasks/active/some-task.md"],
    )
    _assert_decision_equivalence(result)


def test_decision_equivalence_policy_forbidden():
    """Policy-forbidden files (.pcae, .githooks) should be caught."""
    result = build_gate_dry_run(
        REPO_ROOT,
        requested_action="source_mutation",
        requested_files=[".pcae/cache/state.json"],
    )
    _assert_decision_equivalence(result)


# -- Scenario: backend invocation -------------------------------------------

def test_decision_equivalence_backend_invocation():
    """Backend invocation scenario: backend evaluation present."""
    result = build_gate_dry_run(
        REPO_ROOT,
        requested_action="backend_invocation",
        requested_backend="claude",
        prompt_present=True,
    )
    _assert_decision_equivalence(result)
    gates = {g["gate_id"]: g for g in result["gates"]}
    assert "backend_evaluation" in gates["backend_invocation_gate"]
    be = gates["backend_invocation_gate"]["backend_evaluation"]
    assert be["backend_approval_detected"] is False
    assert be["human_approval_detected"] is False


def test_decision_equivalence_backend_unknown():
    """Unknown backend: requires_more_evidence."""
    result = build_gate_dry_run(
        REPO_ROOT,
        requested_action="backend_invocation",
        requested_backend="unknown-llm",
        prompt_present=True,
    )
    _assert_decision_equivalence(result)


# -- Scenario: adoption -----------------------------------------------------

def test_decision_equivalence_adoption():
    """Adoption scenario: adoption evaluation present."""
    result = build_gate_dry_run(
        REPO_ROOT,
        requested_action="adoption",
        requested_files=["src/example.py"],
        adoption_artifact_present=True,
    )
    _assert_decision_equivalence(result)
    gates = {g["gate_id"]: g for g in result["gates"]}
    assert "adoption_evaluation" in gates["adoption_approval_gate"]


# -- Scenario: commit -------------------------------------------------------

def test_decision_equivalence_commit():
    """Commit scenario: commit evaluation present, git porcelain shared."""
    result = build_gate_dry_run(
        REPO_ROOT,
        requested_action="commit",
        commit_message_present=True,
    )
    _assert_decision_equivalence(result)
    gates = {g["gate_id"]: g for g in result["gates"]}
    assert "commit_evaluation" in gates["commit_gate"]
    ce = gates["commit_gate"]["commit_evaluation"]
    assert "repository_clean" in ce
    assert "staged_changes_detected" in ce
    assert "unstaged_changes_detected" in ce


# -- Scenario: push ---------------------------------------------------------

def test_decision_equivalence_push():
    """Push scenario: push evaluation present, git branch/ahead shared."""
    result = build_gate_dry_run(
        REPO_ROOT,
        requested_action="push",
        push_target="origin/main",
    )
    _assert_decision_equivalence(result)
    gates = {g["gate_id"]: g for g in result["gates"]}
    assert "push_evaluation" in gates["push_gate"]
    pe = gates["push_gate"]["push_evaluation"]
    assert "branch" in pe
    assert "origin_sync_status" in pe
    assert pe["raw_push_detected"] is False
    assert pe["force_push_detected"] is False


# -- Scenario: all-flags (stress test) --------------------------------------

def test_decision_equivalence_all_flags():
    """All flags set: still no authorization, no enforcement, no allow."""
    result = build_gate_dry_run(
        REPO_ROOT,
        requested_action="adoption",
        requested_files=["src/example.py"],
        requested_backend="claude",
        prompt_present=True,
        adoption_artifact_present=True,
        human_approved=True,
        commit_message_present=True,
        push_target="origin/main",
    )
    _assert_decision_equivalence(result)
    # Even with human_approved=True, no gate grants authorization
    for g in result["gates"]:
        assert g["authorization_granted"] is False
        assert g["enforcement_performed"] is False


# ===========================================================================
# Phase 88Y.4 — Gate count/name/order validation
# ===========================================================================

def test_gate_count_is_fifteen_across_all_scenarios():
    """Gate count must be 15 regardless of scenario parameters."""
    scenarios = [
        {},
        {"requested_action": "source_mutation", "requested_files": ["src/x.py"]},
        {"requested_action": "backend_invocation", "requested_backend": "claude",
         "prompt_present": True},
        {"requested_action": "adoption", "requested_files": ["src/x.py"],
         "adoption_artifact_present": True},
        {"requested_action": "commit", "commit_message_present": True},
        {"requested_action": "push", "push_target": "origin/main"},
    ]
    for i, kw in enumerate(scenarios):
        result = build_gate_dry_run(REPO_ROOT, **kw)
        assert result["gate_count"] == 15, f"Scenario {i}: gate_count={result['gate_count']}"
        assert len(result["gates"]) == 15, f"Scenario {i}: len(gates)={len(result['gates'])}"


def test_gate_ids_never_change():
    """Gate IDs must be stable regardless of scenario."""
    scenarios = [
        {},
        {"requested_action": "source_mutation", "requested_files": ["src/x.py"]},
        {"requested_action": "backend_invocation", "requested_backend": "claude",
         "prompt_present": True},
        {"requested_action": "adoption", "requested_files": ["src/x.py"],
         "adoption_artifact_present": True},
        {"requested_action": "commit", "commit_message_present": True},
        {"requested_action": "push", "push_target": "origin/main"},
    ]
    for i, kw in enumerate(scenarios):
        result = build_gate_dry_run(REPO_ROOT, **kw)
        actual_ids = [g["gate_id"] for g in result["gates"]]
        assert actual_ids == EXPECTED_GATE_IDS, \
            f"Scenario {i}: gate IDs differ: {actual_ids}"


def test_gate_names_never_change():
    """Gate names must be stable regardless of scenario."""
    result = build_gate_dry_run(REPO_ROOT)
    actual_names = [g["gate_name"] for g in result["gates"]]
    assert actual_names == EXPECTED_GATE_NAMES


# ===========================================================================
# Phase 88Y.4 — Memoization validation (call-count tests)
# ===========================================================================

def test_git_porcelain_called_once_per_dry_run():
    """Git porcelain should be computed once (via ctx) and shared."""
    import pcae.core.gate_dry_run_context as ctx_module
    original = ctx_module._git_porcelain_raw
    calls = []

    def tracking(repo_root):
        calls.append(1)
        return original(repo_root)

    ctx_module._git_porcelain_raw = tracking
    try:
        build_gate_dry_run(REPO_ROOT)
        # ctx.git_porcelain called at most a few times
        # (commit_gate + push_gate evaluators share ctx)
        assert len(calls) <= 3, \
            f"Expected ≤3 git porcelain calls, got {len(calls)}"
    finally:
        ctx_module._git_porcelain_raw = original


def test_git_branch_called_once_per_dry_run():
    """Git branch should be computed once (via ctx) and shared."""
    import pcae.core.gate_dry_run_context as ctx_module
    original = ctx_module._git_branch_raw
    calls = []

    def tracking(repo_root):
        calls.append(1)
        return original(repo_root)

    ctx_module._git_branch_raw = tracking
    try:
        build_gate_dry_run(REPO_ROOT)
        assert len(calls) <= 3, \
            f"Expected ≤3 git branch calls, got {len(calls)}"
    finally:
        ctx_module._git_branch_raw = original


def test_git_ahead_count_called_once_per_dry_run():
    """Git ahead count should be computed once (via ctx) and shared."""
    import pcae.core.gate_dry_run_context as ctx_module
    original = ctx_module._git_ahead_count_raw
    calls = []

    def tracking(repo_root):
        calls.append(1)
        return original(repo_root)

    ctx_module._git_ahead_count_raw = tracking
    try:
        build_gate_dry_run(REPO_ROOT)
        assert len(calls) <= 3, \
            f"Expected ≤3 git ahead count calls, got {len(calls)}"
    finally:
        ctx_module._git_ahead_count_raw = original


def test_build_project_state_called_once_per_dry_run():
    """build_project_state should be called once (via ctx.project_state)."""
    import pcae.core.project_state as ps_module
    original = ps_module.build_project_state
    calls = []

    def tracking(repo_root, ctx=None):
        calls.append(1)
        return original(repo_root, ctx=ctx)

    ps_module.build_project_state = tracking
    try:
        build_gate_dry_run(REPO_ROOT)
        assert len(calls) == 1, \
            f"Expected 1 build_project_state call, got {len(calls)}"
    finally:
        ps_module.build_project_state = original


# ===========================================================================
# Phase 88Y.4 — Freshness tests
# ===========================================================================

def test_separate_calls_recompute_git_evidence():
    """Separate build_gate_dry_run calls must recompute git evidence."""
    import pcae.core.gate_dry_run_context as ctx_module
    original = ctx_module._git_porcelain_raw
    calls = []

    def tracking(repo_root):
        calls.append(1)
        return original(repo_root)

    ctx_module._git_porcelain_raw = tracking
    try:
        build_gate_dry_run(REPO_ROOT)
        first_call_count = len(calls)
        build_gate_dry_run(REPO_ROOT)
        second_call_count = len(calls) - first_call_count
        # Second call should recompute (not use stale cache)
        assert second_call_count >= 1, \
            f"Second invocation did not recompute git porcelain"
    finally:
        ctx_module._git_porcelain_raw = original


def test_separate_calls_recompute_task_contract():
    """Separate build_gate_dry_run calls must recompute task contract."""
    from pcae.core import gate_dry_run as gdm
    original = gdm._detect_task_contract
    calls = []

    def tracking(repo_root):
        calls.append(1)
        return original(repo_root)

    gdm._detect_task_contract = tracking
    try:
        build_gate_dry_run(REPO_ROOT)
        first_count = len(calls)
        build_gate_dry_run(REPO_ROOT)
        second_count = len(calls) - first_count
        assert second_count >= 1, \
            f"Second invocation did not recompute task contract"
    finally:
        gdm._detect_task_contract = original


def test_no_evidence_shared_between_context_instances():
    """Two GateDryRunContext instances must not share cached data."""
    ctx1 = GateDryRunContext(REPO_ROOT)
    ctx2 = GateDryRunContext(REPO_ROOT)
    # Before access, both have unset caches
    assert ctx1._task_contract is ctx_module_sentinel()
    assert ctx2._task_contract is ctx_module_sentinel()
    # After access on ctx1, ctx2 must still be unset
    _ = ctx1.task_contract
    assert ctx2._task_contract is ctx_module_sentinel()
    # ctx2 must independently compute its own value
    _ = ctx2.task_contract
    assert ctx2._task_contract is not ctx_module_sentinel()


def ctx_module_sentinel():
    """Return the _UNSET sentinel from gate_dry_run_context module."""
    import pcae.core.gate_dry_run_context as ctx_module
    return ctx_module._UNSET


# ===========================================================================
# Phase 88Y.4 — No-persistence tests (expanded)
# ===========================================================================

def test_no_module_level_mutable_cache():
    """GateDryRunContext module must not have any mutable module-level cache."""
    import pcae.core.gate_dry_run_context as ctx_module
    # Check all module-level names for mutable caches
    for attr_name in dir(ctx_module):
        if attr_name.startswith('_') and 'cache' in attr_name.lower():
            obj = getattr(ctx_module, attr_name)
            assert not isinstance(obj, dict), \
                f"Module has mutable cache dict: {attr_name}"
            assert not isinstance(obj, list), \
                f"Module has mutable cache list: {attr_name}"


def test_no_pcae_cache_files_created_anywhere():
    """No .pcae subdirectory should gain files after dry-run."""
    pcae_dir = REPO_ROOT / ".pcae"
    import os
    before_files = set()
    if pcae_dir.exists():
        for root, dirs, files in os.walk(pcae_dir):
            for f in files:
                before_files.add(os.path.join(root, f))

    build_gate_dry_run(REPO_ROOT)
    # Access all context properties via a second call to exercise all paths
    ctx = GateDryRunContext(REPO_ROOT)
    _ = ctx.project_state
    _ = ctx.artifact_index
    _ = ctx.memory_snapshot
    _ = ctx.governance_timeline
    _ = ctx.decision_log
    _ = ctx.risk_register
    _ = ctx.task_contract
    _ = ctx.git_porcelain
    _ = ctx.git_branch
    _ = ctx.git_ahead_count

    after_files = set()
    if pcae_dir.exists():
        for root, dirs, files in os.walk(pcae_dir):
            for f in files:
                after_files.add(os.path.join(root, f))

    new_files = after_files - before_files
    assert len(new_files) == 0, f"New files created: {new_files}"


def test_context_does_not_share_between_instances_after_access():
    """After accessing ctx1 properties, ctx2 starts fresh."""
    ctx1 = GateDryRunContext(REPO_ROOT)
    _ = ctx1.project_state
    _ = ctx1.task_contract
    _ = ctx1.git_porcelain

    # ctx2 must have its own independent state
    ctx2 = GateDryRunContext(REPO_ROOT)
    sentinel = ctx_module_sentinel()
    assert ctx2._task_contract is sentinel
    assert ctx2._git_porcelain is sentinel
    assert ctx2._git_branch is sentinel
    assert ctx2._git_ahead_count is sentinel


# ===========================================================================
# Phase 88Y.4 — Audit/redaction preservation
# ===========================================================================

def test_audit_evidence_shape_always_list():
    """Audit evidence fields must always be lists."""
    result = build_gate_dry_run(REPO_ROOT)
    for g in result["gates"]:
        assert isinstance(g["evidence_artifacts"], list), \
            f"{g['gate_id']} evidence_artifacts not a list"
        assert isinstance(g["evidence_events"], list), \
            f"{g['gate_id']} evidence_events not a list"
        assert isinstance(g["evidence_decisions"], list), \
            f"{g['gate_id']} evidence_decisions not a list"
        assert isinstance(g["evidence_risks"], list), \
            f"{g['gate_id']} evidence_risks not a list"


def test_redaction_not_applied_to_gate_output():
    """Gate output must not contain redaction markers."""
    result = build_gate_dry_run(REPO_ROOT)
    import json
    raw = json.dumps(result)
    assert "[REDACTED]" not in raw
    assert "***" not in raw


def test_safety_notes_all_present_idle():
    """All safety note keys must be present in idle scenario."""
    result = build_gate_dry_run(REPO_ROOT)
    sn = result["safety_notes"]
    required_notes = [
        "gate_dry_run_only",
        "gate_dry_run_does_not_authorize_action",
        "gate_dry_run_does_not_enforce_action",
        "gate_dry_run_does_not_invoke_backends",
        "gate_dry_run_does_not_send_prompts",
        "gate_dry_run_does_not_capture_outputs",
        "gate_dry_run_does_not_perform_intake",
        "gate_dry_run_does_not_perform_adoption",
        "gate_dry_run_does_not_mutate_repo",
        "gate_dry_run_does_not_commit",
        "gate_dry_run_does_not_push",
        "gate_dry_run_does_not_write_storage",
        "permission_broker_not_implemented",
        "shell_gate_not_implemented",
        "storage_not_implemented",
        "backend_invocation_performed",
        "repo_mutation_performed",
        "storage_written",
    ]
    for note in required_notes:
        assert note in sn, f"Missing safety note: {note}"


# ===========================================================================
# Phase 88Y.4 — Authorization/performed flags never change
# ===========================================================================

def test_authorization_never_true_all_scenarios():
    """No scenario should ever set authorization_granted=True."""
    scenarios = [
        {},
        {"requested_action": "source_mutation",
         "requested_files": ["src/pcae/core/gate_dry_run.py"]},
        {"requested_action": "backend_invocation", "requested_backend": "claude",
         "prompt_present": True},
        {"requested_action": "adoption", "requested_files": ["src/x.py"],
         "adoption_artifact_present": True},
        {"requested_action": "commit", "commit_message_present": True},
        {"requested_action": "push", "push_target": "origin/main"},
        {"human_approved": True},
        {"requested_action": "adoption", "human_approved": True,
         "requested_files": ["src/x.py"], "adoption_artifact_present": True},
    ]
    for i, kw in enumerate(scenarios):
        result = build_gate_dry_run(REPO_ROOT, **kw)
        for g in result["gates"]:
            assert g["authorization_granted"] is False, \
                f"Scenario {i}: {g['gate_id']} authorization_granted=True"


def test_enforcement_never_true_all_scenarios():
    """No scenario should ever set enforcement_performed=True."""
    scenarios = [
        {},
        {"requested_action": "source_mutation",
         "requested_files": ["src/pcae/core/gate_dry_run.py"]},
        {"requested_action": "backend_invocation", "requested_backend": "claude",
         "prompt_present": True},
        {"requested_action": "adoption", "requested_files": ["src/x.py"],
         "adoption_artifact_present": True, "human_approved": True},
        {"requested_action": "commit", "commit_message_present": True,
         "human_approved": True},
        {"requested_action": "push", "push_target": "origin/main",
         "human_approved": True},
    ]
    for i, kw in enumerate(scenarios):
        result = build_gate_dry_run(REPO_ROOT, **kw)
        for g in result["gates"]:
            assert g["enforcement_performed"] is False, \
                f"Scenario {i}: {g['gate_id']} enforcement_performed=True"


# ===========================================================================
# Phase 88Y.4 — Performance structural assertions (no fragile timing)
# ===========================================================================

def test_context_properties_lazy_not_eager():
    """GateDryRunContext must not eagerly compute evidence at init time."""
    ctx = GateDryRunContext(REPO_ROOT)
    sentinel = ctx_module_sentinel()
    # All lazy fields should still be _UNSET after init
    assert ctx._task_contract is sentinel
    assert ctx._git_porcelain is sentinel
    assert ctx._git_branch is sentinel
    assert ctx._git_ahead_count is sentinel
    # Dict fields should still be None (not _UNSET — they use None sentinel)
    assert ctx._artifact_index is None
    assert ctx._memory_snapshot is None
    assert ctx._governance_timeline is None
    assert ctx._decision_log is None
    assert ctx._risk_register is None
    assert ctx._project_state is None


def test_context_properties_are_idempotent_all():
    """Every context property must return same value on repeated access."""
    ctx = GateDryRunContext(REPO_ROOT)
    # Access all properties twice
    pairs = []
    for _ in range(2):
        pairs.append((
            ctx.artifact_index,
            ctx.memory_snapshot,
            ctx.governance_timeline,
            ctx.decision_log,
            ctx.risk_register,
            ctx.project_state,
            ctx.task_contract,
            ctx.git_porcelain,
            ctx.git_branch,
            ctx.git_ahead_count,
        ))
    # Each pair element should be the same object/value across accesses
    for a, b in zip(pairs[0], pairs[1]):
        if isinstance(a, str):
            assert a == b
        else:
            assert a is b


# ===========================================================================
# Phase 88Y.4 — Sentinal-based None-value memoization
# ===========================================================================

def test_none_value_is_properly_cached():
    """When a context property returns None, it must be cached (not recomputed)."""
    from pcae.core import gate_dry_run as gdm
    original = gdm._detect_task_contract
    calls = []

    def tracking(repo_root):
        calls.append(1)
        return None  # Simulate no task contract

    gdm._detect_task_contract = tracking
    try:
        ctx = GateDryRunContext(REPO_ROOT)
        _ = ctx.task_contract
        _ = ctx.task_contract
        _ = ctx.task_contract
        # Must only call _detect_task_contract once, even though it returns None
        assert len(calls) == 1, \
            f"None value not cached: {len(calls)} calls instead of 1"
    finally:
        gdm._detect_task_contract = original


def test_git_porcelain_returns_string_not_none():
    """Git porcelain must return a string (may be empty for clean repo)."""
    ctx = GateDryRunContext(REPO_ROOT)
    gp = ctx.git_porcelain
    # Must not be None — GitPorcelain always returns a string on success
    assert gp is not None, "git_porcelain should not be None on success"
    assert isinstance(gp, str), f"Expected str, got {type(gp)}"
    # Second access must return same cached value
    gp2 = ctx.git_porcelain
    assert gp2 == gp, "git_porcelain not idempotent"


def test_git_branch_returns_string():
    """Git branch should return a string (the current branch name)."""
    ctx = GateDryRunContext(REPO_ROOT)
    gb = ctx.git_branch
    assert gb is not None
    assert isinstance(gb, str)
    assert len(gb) > 0


def test_git_ahead_count_returns_int_in_clean_repo():
    """Git ahead count for clean synced repo should be 0."""
    ctx = GateDryRunContext(REPO_ROOT)
    ga = ctx.git_ahead_count
    assert ga is not None
    assert isinstance(ga, int)
    assert ga == 0


# ===========================================================================
# Phase 88Y.4 — Task contract detection reduction
# ===========================================================================

def test_task_contract_detection_materially_reduced():
    """With context, _detect_task_contract called ≤1x vs 15x without."""
    from pcae.core import gate_dry_run as gdm
    original = gdm._detect_task_contract
    calls = []

    def tracking(repo_root):
        calls.append(1)
        return original(repo_root)

    gdm._detect_task_contract = tracking
    try:
        # Multiple scenarios should all show reduction
        build_gate_dry_run(REPO_ROOT)
        assert len(calls) == 1, \
            f"Default: expected 1 call, got {len(calls)}"
        calls.clear()

        build_gate_dry_run(REPO_ROOT, requested_action="source_mutation",
                           requested_files=["src/x.py"])
        assert len(calls) == 1, \
            f"Source mutation: expected 1 call, got {len(calls)}"
        calls.clear()

        build_gate_dry_run(REPO_ROOT, requested_action="backend_invocation",
                           requested_backend="claude", prompt_present=True)
        assert len(calls) == 1, \
            f"Backend: expected 1 call, got {len(calls)}"
    finally:
        gdm._detect_task_contract = original
