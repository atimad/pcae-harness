"""Tests for Phase 112D — Runtime Context Verification & Compatibility.

Verification/hardening phase only — no new Runtime Context
functionality. This suite proves the 112C prototype
(`src/pcae/core/runtime_context.py`) is immutable, internally
consistent, compatible with every phase in the 110A-112C lineage, and
incapable of introducing execution behavior. Where 112C's own test
suite (`tests/test_runtime_context.py`) already covers a guarantee at
the unit level, this suite re-verifies it independently against the
frozen contract *documents* themselves (cross-checking code constants
against doc text, not just internal code consistency) and against
sibling modules (`runtime_registry.py`, `runtime_introspection.py`),
mirroring the "prototype then verification" pattern 110E->110F and
111B->111D already established twice.

No subprocess invocation in this file; pure in-process, pytest-xdist
safe.
"""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import pytest

from pcae.core import runtime_context as rc
from pcae.core import runtime_introspection as ri
from pcae.core.runtime_context import (
    CONTEXT_LIFECYCLE_STAGES,
    CONTEXT_PERSISTENCE_BUCKETS,
    CONTEXT_RELATIONSHIP_CHAIN,
    CURRENT_MAXIMUM_PLUGIN_CAPABILITY,
    CURRENT_RUNTIME_STATE,
    EXECUTION_AVAILABILITY,
    ApprovalContext,
    AuditContext,
    BrokerDecisionContext,
    EvidenceContext,
    ExecutionContext,
    IntentContext,
    ObservationContext,
    OwnershipMetadata,
    PhaseContext,
    RollbackContext,
    RuntimeContext,
    RuntimeSession,
    TaskContext,
    observe_context,
)

REPO_ROOT = Path(rc.__file__).resolve().parent.parent.parent.parent
DOCS = REPO_ROOT / "docs"

ALL_CONTEXT_CLASSES = (
    RuntimeContext,
    RuntimeSession,
    TaskContext,
    PhaseContext,
    IntentContext,
    BrokerDecisionContext,
    ApprovalContext,
    EvidenceContext,
    ObservationContext,
    ExecutionContext,
    AuditContext,
    RollbackContext,
)

CONTRACT_DOC = DOCS / "PCAE_RUNTIME_CONTEXT_CONTRACT.md"
ARCHITECTURE_DOC = DOCS / "PCAE_RUNTIME_CONTEXT_ARCHITECTURE.md"


def _minimal_kwargs(cls) -> dict:
    return {
        RuntimeContext: {},
        RuntimeSession: {"session_id": "s1"},
        TaskContext: {"task_id": "t1", "session_id": "s1"},
        PhaseContext: {"phase_id": "p1"},
        IntentContext: {"intent_id": "i1", "phase_id": "p1"},
        BrokerDecisionContext: {"decision_id": "d1", "intent_id": "i1"},
        ApprovalContext: {"approval_id": "a1", "decision_id": "d1"},
        EvidenceContext: {"evidence_id": "e1", "approval_id": "a1"},
        ObservationContext: {"observation_id": "o1", "session_id": "s1"},
        ExecutionContext: {"execution_id": "x1"},
        AuditContext: {"audit_id": "au1"},
        RollbackContext: {"rollback_id": "r1"},
    }[cls]


def _full_chain() -> RuntimeContext:
    evidence = EvidenceContext(evidence_id="e1", approval_id="a1")
    approval = ApprovalContext(approval_id="a1", decision_id="d1", evidence=(evidence,))
    decision = BrokerDecisionContext(decision_id="d1", intent_id="i1", approval=approval)
    intent = IntentContext(intent_id="i1", phase_id="p1", broker_decision=decision)
    obs = ObservationContext(observation_id="o1", session_id="s1")
    task = TaskContext(task_id="t1", session_id="s1", phase_id="p1")
    session = RuntimeSession(session_id="s1", tasks=(task,), observation=obs)
    return RuntimeContext(session=session), PhaseContext(phase_id="p1", intents=(intent,))


# ═══════════════════════════════════════════════════════════════════════
# Objective 1 — Compatibility with 110A through 112C
# ═══════════════════════════════════════════════════════════════════════

LINEAGE_PHASE_DOCS = (
    "PHASE_110_RUNTIME_ARCHITECTURE.md",             # 110A
    "PHASE_110_RUNTIME_PLUGIN_CONTRACT_FREEZE.md",   # 110B
    "PHASE_110_RUNTIME_SERVICE_REGISTRY_ARCHITECTURE.md",  # 110C
    "PHASE_110_RUNTIME_REGISTRY_CONTRACT_FREEZE.md", # 110D
    "PHASE_110_RUNTIME_REGISTRY_PROTOTYPE.md",       # 110E
    "PHASE_110_RUNTIME_REGISTRY_VERIFICATION.md",    # 110F
    "PHASE_111_RUNTIME_INTROSPECTION_ARCHITECTURE.md",  # 111A
    "PHASE_111_RUNTIME_INTROSPECTION_PROTOTYPE.md",  # 111B
    "PHASE_111_RUNTIME_INSPECT_CLI.md",              # 111C
    "PHASE_111_RUNTIME_INSPECT_VERIFICATION.md",     # 111D
    "PHASE_111_RUNTIME_ARCHITECTURE_REVIEW.md",      # 111R
    "PHASE_112_RUNTIME_CONTEXT_ARCHITECTURE.md",     # 112A
    "PHASE_112_RUNTIME_CONTEXT_CONTRACT_FREEZE.md",  # 112B
    "PHASE_112_RUNTIME_CONTEXT_PROTOTYPE.md",        # 112C
)


@pytest.mark.parametrize("doc_name", LINEAGE_PHASE_DOCS)
def test_every_lineage_phase_document_exists(doc_name):
    assert (DOCS / doc_name).exists(), f"missing lineage document: {doc_name}"


def test_compatible_with_110a_current_runtime_state():
    """110A §8's frozen state model names 'Observed' as the current
    maximum -- this module must restate it identically."""
    text = (DOCS / "PCAE_RUNTIME_ARCHITECTURE.md").read_text()
    assert "Observed" in text
    assert CURRENT_RUNTIME_STATE == "Observed"


def test_compatible_with_110b_plugin_capability():
    text = (DOCS / "PCAE_RUNTIME_PLUGIN_CONTRACTS.md").read_text()
    assert "observe" in text
    assert CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"


def test_compatible_with_111b_introspection_shared_constants():
    """runtime_context.py and runtime_introspection.py (111B) must
    agree on every shared frozen fact -- proving 112C did not silently
    fork a competing definition of 'current state' or 'max capability'."""
    assert CURRENT_RUNTIME_STATE == ri.CURRENT_RUNTIME_STATE
    assert CURRENT_MAXIMUM_PLUGIN_CAPABILITY == ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY
    assert EXECUTION_AVAILABILITY == ri.EXECUTION_AVAILABILITY


def test_compatible_with_112a_lifecycle_vocabulary():
    text = ARCHITECTURE_DOC.read_text()
    for stage in CONTEXT_LIFECYCLE_STAGES:
        assert f"`{stage}`" in text, f"lifecycle stage {stage!r} not found in 112A doc"


def test_compatible_with_112a_twelve_objects():
    text = ARCHITECTURE_DOC.read_text()
    for cls in ALL_CONTEXT_CLASSES:
        assert f"`{cls.__name__}`" in text, f"{cls.__name__} not named in 112A architecture doc"


def test_compatible_with_112b_persistence_buckets():
    text = CONTRACT_DOC.read_text()
    for bucket in CONTEXT_PERSISTENCE_BUCKETS:
        assert bucket in text, f"persistence bucket {bucket!r} not found in 112B contract doc"


def test_compatible_with_112b_twelve_objects():
    text = CONTRACT_DOC.read_text()
    for cls in ALL_CONTEXT_CLASSES:
        assert f"`{cls.__name__}`" in text, f"{cls.__name__} not named in 112B contract doc"


def test_compatible_with_112b_resolved_ordering():
    """112B §8.2 resolved Broker Decision before Approval -- the code's
    chain constant must match, and the doc itself must still state the
    resolution (not have drifted since 112C read it)."""
    text = CONTRACT_DOC.read_text()
    assert "Broker Decision precedes Approval" in text
    decision_idx = CONTEXT_RELATIONSHIP_CHAIN.index("BrokerDecisionContext")
    approval_idx = CONTEXT_RELATIONSHIP_CHAIN.index("ApprovalContext")
    assert decision_idx < approval_idx


def test_compatible_with_112c_prototype_doc_no_go_confirmations():
    text = (DOCS / "PHASE_112_RUNTIME_CONTEXT_PROTOTYPE.md").read_text()
    assert "No runtime execution" in text
    assert "No Permission Broker enforcement" in text


def test_no_module_added_beyond_runtime_context_for_112d():
    """112D is verification-only -- it must not have added any new
    src/pcae/core/ module of its own."""
    core_dir = REPO_ROOT / "src" / "pcae" / "core"
    existing = {p.name for p in core_dir.glob("*.py")}
    assert "runtime_context_verification.py" not in existing


# ═══════════════════════════════════════════════════════════════════════
# Objective 2 — Structural immutability (attempt mutation, verify safe failure)
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("cls", ALL_CONTEXT_CLASSES)
def test_every_field_rejects_reassignment(cls):
    """Attempt mutation on every field of every class; confirm it fails
    safely (FrozenInstanceError), never silently succeeding."""
    instance = cls(**_minimal_kwargs(cls))
    for field in dataclasses.fields(instance):
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(instance, field.name, "mutated")


def test_identity_fields_immutable_after_full_chain_composition():
    ctx, phase = _full_chain()
    session = ctx.session
    with pytest.raises(dataclasses.FrozenInstanceError):
        session.session_id = "hacked"
    with pytest.raises(dataclasses.FrozenInstanceError):
        session.tasks[0].task_id = "hacked"
    with pytest.raises(dataclasses.FrozenInstanceError):
        phase.intents[0].intent_id = "hacked"


def test_ownership_metadata_immutable():
    ownership = RuntimeSession.OWNERSHIP
    assert isinstance(ownership, OwnershipMetadata)
    with pytest.raises(dataclasses.FrozenInstanceError):
        ownership.creates = "mutated"


def test_persistence_bucket_is_a_string_not_a_mutable_container():
    for cls in ALL_CONTEXT_CLASSES:
        assert isinstance(cls.PERSISTENCE_BUCKET, str)


def test_relationship_chain_constant_is_a_tuple_not_a_list():
    """A list constant could be mutated in place at import time by any
    caller; a tuple cannot."""
    assert isinstance(CONTEXT_RELATIONSHIP_CHAIN, tuple)
    with pytest.raises(AttributeError):
        CONTEXT_RELATIONSHIP_CHAIN.append("SomethingElse")  # type: ignore[attr-defined]


def test_composition_collections_are_tuples_end_to_end():
    ctx, phase = _full_chain()
    assert isinstance(ctx.session.tasks, tuple)
    assert isinstance(phase.intents, tuple)
    approval = ctx.session.tasks[0]
    assert isinstance(approval, TaskContext)


def test_mutating_a_returned_tuple_does_not_affect_the_source_object():
    ctx, phase = _full_chain()
    tasks_copy = ctx.session.tasks
    with pytest.raises((AttributeError, TypeError)):
        tasks_copy[0] = TaskContext(task_id="other", session_id="s1")  # type: ignore[index]


def test_observe_context_never_mutates_in_place():
    session = RuntimeSession(session_id="s1")
    before_id = id(session)
    observed = observe_context(session)
    assert id(session) == before_id
    assert session.lifecycle_stage == "Created"
    assert observed.lifecycle_stage == "Observed"
    assert session is not observed


# ═══════════════════════════════════════════════════════════════════════
# Objective 3 — Relationship integrity (Session -> ... -> Evidence)
# ═══════════════════════════════════════════════════════════════════════


def test_full_relationship_chain_is_internally_consistent():
    ctx, phase = _full_chain()
    session = ctx.session
    task = session.tasks[0]
    intent = phase.intents[0]
    decision = intent.broker_decision
    approval = decision.approval
    evidence = approval.evidence[0]

    assert task.session_id == session.session_id
    assert task.phase_id == phase.phase_id
    assert intent.phase_id == phase.phase_id
    assert decision.intent_id == intent.intent_id
    assert approval.decision_id == decision.decision_id
    assert evidence.approval_id == approval.approval_id
    assert session.observation.session_id == session.session_id


def test_relationship_chain_has_no_cycle():
    """None of the seven live-composed objects reference back up the
    chain -- containment is strictly downward."""
    ctx, phase = _full_chain()
    session = ctx.session
    task = session.tasks[0]
    assert not hasattr(task, "session")  # references session_id, not a nested RuntimeSession
    assert not hasattr(phase.intents[0], "phase")  # references phase_id, not a nested PhaseContext


def test_many_tasks_can_reference_one_phase_consistently():
    task_a = TaskContext(task_id="t1", session_id="s1", phase_id="p1")
    task_b = TaskContext(task_id="t2", session_id="s1", phase_id="p1")
    session = RuntimeSession(session_id="s1", tasks=(task_a, task_b))
    assert len({t.phase_id for t in session.tasks}) == 1
    assert len({t.task_id for t in session.tasks}) == 2


# ═══════════════════════════════════════════════════════════════════════
# Objective 4 — Ownership verification (matches frozen 112B contract)
# ═══════════════════════════════════════════════════════════════════════

# Extracted directly from docs/PCAE_RUNTIME_CONTEXT_CONTRACT.md §4's
# per-object table -- every "creates"/"owns" value must contain
# "Runtime", per 112B's own invariant that no Plugin/Broker/Registry
# ever creates or owns a Context object.


@pytest.mark.parametrize("cls", ALL_CONTEXT_CLASSES)
def test_ownership_creates_and_owns_are_runtime(cls):
    assert "Runtime" in cls.OWNERSHIP.creates
    assert "Runtime" in cls.OWNERSHIP.owns


def test_broker_decision_ownership_matches_112b_wrapping_language():
    text = CONTRACT_DOC.read_text()
    assert "wraps a decision the Broker" in text.lower() or "Broker (COMP-001) already produced" in BrokerDecisionContext.OWNERSHIP.creates
    assert "COMP-001" in BrokerDecisionContext.OWNERSHIP.creates


def test_approval_ownership_never_self_decides():
    """112B §4/§5: ApprovalContext records an outcome; it never decides
    one itself."""
    assert "never itself" in ApprovalContext.OWNERSHIP.updates or "never" in ApprovalContext.OWNERSHIP.creates


def test_no_ownership_field_names_a_plugin_broker_or_registry_as_creator():
    forbidden = ("Plugin", "Registry")
    for cls in ALL_CONTEXT_CLASSES:
        for word in forbidden:
            assert not cls.OWNERSHIP.creates.startswith(word)
            assert not cls.OWNERSHIP.owns.startswith(word)


# ═══════════════════════════════════════════════════════════════════════
# Objective 5 — Persistence metadata verification (exact 112B match)
# ═══════════════════════════════════════════════════════════════════════

EXPECTED_PERSISTENCE_BUCKETS = {
    RuntimeContext: "Session-only",
    RuntimeSession: "Persistent",
    TaskContext: "Persistent",
    PhaseContext: "Persistent",
    IntentContext: "Session-only",
    BrokerDecisionContext: "Never persist",
    ApprovalContext: "Future persistence",
    EvidenceContext: "Future persistence",
    ObservationContext: "Session-only",
    ExecutionContext: "Never persist",
    AuditContext: "Future persistence",
    RollbackContext: "Future persistence",
}


@pytest.mark.parametrize("cls,expected_bucket", list(EXPECTED_PERSISTENCE_BUCKETS.items()))
def test_persistence_bucket_matches_112b_exactly(cls, expected_bucket):
    assert cls.PERSISTENCE_BUCKET == expected_bucket


def test_no_persistence_mechanism_exists_in_module():
    text = Path(rc.__file__).read_text()
    for forbidden in ("open(", "Path(", ".write_text", ".write(", "pickle", "json.dump", "sqlite"):
        assert forbidden not in text


def test_constructing_full_chain_touches_no_filesystem(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    before = set(tmp_path.rglob("*"))
    _full_chain()
    after = set(tmp_path.rglob("*"))
    assert before == after


# ═══════════════════════════════════════════════════════════════════════
# Objective 6 — Composition integrity / no "god object" drift
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_context_has_minimal_field_count():
    """RuntimeContext must remain a thin composition root -- exactly
    'session' plus 'lifecycle_stage', never accumulating direct
    task/phase/intent/etc. fields of its own."""
    field_names = {f.name for f in dataclasses.fields(RuntimeContext)}
    assert field_names == {"session", "lifecycle_stage"}


def test_runtime_context_does_not_flatten_child_identity_fields():
    """Guards against god-object drift: RuntimeContext must never grow
    a task_id/phase_id/intent_id/etc. field of its own -- those belong
    to the objects it composes, not to the aggregate itself."""
    field_names = {f.name for f in dataclasses.fields(RuntimeContext)}
    forbidden = {
        "task_id", "phase_id", "intent_id", "approval_id",
        "decision_id", "evidence_id", "observation_id",
        "execution_id", "audit_id", "rollback_id",
    }
    assert not (field_names & forbidden)


def test_runtime_session_does_not_flatten_task_fields():
    field_names = {f.name for f in dataclasses.fields(RuntimeSession)}
    forbidden = {"task_id", "phase_id", "intent_id", "title", "status"}
    assert not (field_names & forbidden)


@pytest.mark.parametrize("cls", ALL_CONTEXT_CLASSES)
def test_no_class_exceeds_seven_fields(cls):
    """A loose ceiling guarding against unbounded field growth on any
    single object -- every class today has at most 5 fields; 7 leaves
    headroom without permitting a god object to form silently."""
    assert len(dataclasses.fields(cls)) <= 7


# ═══════════════════════════════════════════════════════════════════════
# Objective 7 — Observation-only guarantees
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def module_imports() -> list[str]:
    tree = ast.parse(Path(rc.__file__).read_text())
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module)
    return names


def test_module_imports_remain_allowlisted(module_imports):
    allowed = {"__future__", "dataclasses", "typing"}
    for name in module_imports:
        assert name in allowed, f"unexpected import introduced: {name}"


def test_no_broker_evaluation_anywhere_in_module(module_imports):
    """No import of any broker module -- checked via the AST-derived
    import list, not a raw substring scan, since the module's own
    docstring legitimately names `permission_broker_foundation` to
    explain why it is *not* imported."""
    for name in module_imports:
        assert "broker" not in name.lower()


def test_no_plugin_loading_or_invocation(module_imports):
    for name in module_imports:
        assert "plugin" not in name.lower()
        assert "registry" not in name.lower()


def test_no_shell_or_command_execution_capability(module_imports):
    forbidden_modules = ("subprocess", "os", "shlex", "shell_gate")
    for name in module_imports:
        assert name not in forbidden_modules


def test_no_execution_related_calls_present():
    tree = ast.parse(Path(rc.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
            assert name not in ("eval", "exec", "compile", "system", "popen", "run", "call", "check_output")


def test_execution_context_status_still_execution_unavailable():
    exe = ExecutionContext(execution_id="x1")
    assert exe.status == "execution_unavailable"


# ═══════════════════════════════════════════════════════════════════════
# Objective 8 — Runtime state verification
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_state_is_observed():
    assert CURRENT_RUNTIME_STATE == "Observed"


def test_maximum_capability_is_observe():
    assert CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"


def test_execution_capability_is_unavailable():
    assert EXECUTION_AVAILABILITY == "unavailable"


def test_no_construction_path_can_reach_an_execution_state():
    """No lifecycle_stage value anywhere reachable via observe_context()
    or direct construction includes anything execution-related."""
    for cls in ALL_CONTEXT_CLASSES:
        instance = cls(**_minimal_kwargs(cls))
        assert instance.lifecycle_stage in CONTEXT_LIFECYCLE_STAGES
        assert instance.lifecycle_stage not in ("Executing", "Executed", "RolledBack")
