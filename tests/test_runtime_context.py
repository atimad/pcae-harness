"""Tests for Phase 112C — Runtime Context Prototype (Observation-Only).

Verifies the first observation-only Runtime Context implementation
(`src/pcae/core/runtime_context.py`): all twelve Context objects frozen
by 112A/112B, immutable identities, composition (RuntimeContext
containing RuntimeSession containing further objects down the resolved
chain), ownership/persistence metadata, the resolved relationship
chain (Broker Decision before Approval, per 112B §8.2), the one
implemented lifecycle transition (observation only), and module
isolation (no broker evaluation, no plugin loading, no execution
capability, no shell/subprocess/network dependency).

No subprocess invocation in this file; pure in-process, pytest-xdist
safe.
"""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import pytest

from pcae.core import runtime_context as rc
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


# ═══════════════════════════════════════════════════════════════════════
# Objective 1 — Runtime Context model implemented, twelve objects exist
# ═══════════════════════════════════════════════════════════════════════


def test_twelve_context_classes_importable():
    assert len(ALL_CONTEXT_CLASSES) == 12
    for cls in ALL_CONTEXT_CLASSES:
        assert dataclasses.is_dataclass(cls)


@pytest.mark.parametrize("cls", ALL_CONTEXT_CLASSES)
def test_every_context_class_is_frozen(cls):
    assert cls.__dataclass_params__.frozen is True


def test_module_docstring_cites_112a_and_112b():
    text = Path(rc.__file__).read_text()
    assert "112A" in text
    assert "112B" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 2 — Immutable identity
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_session_requires_non_empty_session_id():
    RuntimeSession(session_id="s1")
    with pytest.raises(ValueError):
        RuntimeSession(session_id="")
    with pytest.raises(ValueError):
        RuntimeSession(session_id="   ")


def test_task_context_requires_task_id_and_session_id():
    TaskContext(task_id="t1", session_id="s1")
    with pytest.raises(ValueError):
        TaskContext(task_id="", session_id="s1")
    with pytest.raises(ValueError):
        TaskContext(task_id="t1", session_id="")


def test_phase_context_requires_phase_id():
    PhaseContext(phase_id="p1")
    with pytest.raises(ValueError):
        PhaseContext(phase_id="")


def test_intent_context_requires_intent_id_and_phase_id():
    IntentContext(intent_id="i1", phase_id="p1")
    with pytest.raises(ValueError):
        IntentContext(intent_id="", phase_id="p1")


def test_broker_decision_context_requires_decision_id_and_intent_id():
    BrokerDecisionContext(decision_id="d1", intent_id="i1")
    with pytest.raises(ValueError):
        BrokerDecisionContext(decision_id="", intent_id="i1")


def test_approval_context_requires_approval_id_and_decision_id():
    ApprovalContext(approval_id="a1", decision_id="d1")
    with pytest.raises(ValueError):
        ApprovalContext(approval_id="a1", decision_id="")


def test_evidence_context_requires_evidence_id_and_approval_id():
    EvidenceContext(evidence_id="e1", approval_id="a1")
    with pytest.raises(ValueError):
        EvidenceContext(evidence_id="", approval_id="a1")


def test_observation_context_requires_observation_id_and_session_id():
    ObservationContext(observation_id="o1", session_id="s1")
    with pytest.raises(ValueError):
        ObservationContext(observation_id="o1", session_id="")


def test_future_stub_identities_required_as_placeholders():
    ExecutionContext(execution_id="x1")
    AuditContext(audit_id="au1")
    RollbackContext(rollback_id="r1")
    with pytest.raises(ValueError):
        ExecutionContext(execution_id="")
    with pytest.raises(ValueError):
        AuditContext(audit_id="")
    with pytest.raises(ValueError):
        RollbackContext(rollback_id="")


def test_runtime_context_has_no_independent_identity():
    """112B §2: RuntimeContext is a root aggregate, not independently
    identified -- it should accept construction with no identity field
    at all."""
    ctx = RuntimeContext()
    assert not hasattr(ctx, "context_id")
    assert not hasattr(ctx, "runtime_context_id")


def test_identities_are_immutable_after_construction():
    session = RuntimeSession(session_id="s1")
    with pytest.raises(dataclasses.FrozenInstanceError):
        session.session_id = "s2"  # type: ignore[misc]


# ═══════════════════════════════════════════════════════════════════════
# Objective 3 — Composition model
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_context_contains_runtime_session_by_composition():
    session = RuntimeSession(session_id="s1")
    ctx = RuntimeContext(session=session)
    assert ctx.session is session


def test_runtime_session_contains_tasks_by_composition():
    task = TaskContext(task_id="t1", session_id="s1")
    session = RuntimeSession(session_id="s1", tasks=(task,))
    assert session.tasks == (task,)


def test_runtime_session_contains_observation_by_composition():
    obs = ObservationContext(observation_id="o1", session_id="s1")
    session = RuntimeSession(session_id="s1", observation=obs)
    assert session.observation is obs


def test_phase_context_contains_intents_by_composition():
    intent = IntentContext(intent_id="i1", phase_id="p1")
    phase = PhaseContext(phase_id="p1", intents=(intent,))
    assert phase.intents == (intent,)


def test_intent_context_contains_broker_decision_by_composition():
    decision = BrokerDecisionContext(decision_id="d1", intent_id="i1")
    intent = IntentContext(intent_id="i1", phase_id="p1", broker_decision=decision)
    assert intent.broker_decision is decision


def test_broker_decision_context_contains_approval_by_composition():
    approval = ApprovalContext(approval_id="a1", decision_id="d1")
    decision = BrokerDecisionContext(decision_id="d1", intent_id="i1", approval=approval)
    assert decision.approval is approval


def test_approval_context_contains_evidence_by_composition():
    evidence = EvidenceContext(evidence_id="e1", approval_id="a1")
    approval = ApprovalContext(approval_id="a1", decision_id="d1", evidence=(evidence,))
    assert approval.evidence == (evidence,)


def test_many_tasks_reference_one_phase_without_duplication():
    """Task:Phase cardinality is many-to-one (112B §6/§8.1) -- multiple
    tasks reference the same phase_id, not a nested copy each."""
    task_a = TaskContext(task_id="t1", session_id="s1", phase_id="p1")
    task_b = TaskContext(task_id="t2", session_id="s1", phase_id="p1")
    assert task_a.phase_id == task_b.phase_id == "p1"


def test_full_chain_composes_end_to_end():
    evidence = EvidenceContext(evidence_id="e1", approval_id="a1")
    approval = ApprovalContext(approval_id="a1", decision_id="d1", evidence=(evidence,))
    decision = BrokerDecisionContext(decision_id="d1", intent_id="i1", approval=approval)
    intent = IntentContext(intent_id="i1", phase_id="p1", broker_decision=decision)
    phase = PhaseContext(phase_id="p1", intents=(intent,))
    task = TaskContext(task_id="t1", session_id="s1", phase_id="p1")
    session = RuntimeSession(session_id="s1", tasks=(task,))
    ctx = RuntimeContext(session=session)

    assert ctx.session.tasks[0].phase_id == "p1"
    assert ctx.session.tasks[0].task_id == "t1"
    resolved_phase = phase
    resolved_intent = resolved_phase.intents[0]
    resolved_decision = resolved_intent.broker_decision
    resolved_approval = resolved_decision.approval
    resolved_evidence = resolved_approval.evidence[0]
    assert resolved_evidence.evidence_id == "e1"


def test_no_field_is_a_mutable_list():
    """Guards against the 110E/110F PluginDescriptor lesson: a mutable
    collection field would let a caller mutate a 'frozen' object's
    contents in place."""
    for cls in ALL_CONTEXT_CLASSES:
        for field in dataclasses.fields(cls):
            if field.default is not dataclasses.MISSING:
                assert not isinstance(field.default, (list, dict, set))


# ═══════════════════════════════════════════════════════════════════════
# Objective 4 — Lifecycle representation, observation-only
# ═══════════════════════════════════════════════════════════════════════


def test_context_lifecycle_stages_match_112a():
    assert CONTEXT_LIFECYCLE_STAGES == (
        "Created",
        "Initialized",
        "Observed",
        "Updated",
        "Completed",
        "Archived",
    )


@pytest.mark.parametrize("cls", ALL_CONTEXT_CLASSES)
def test_default_lifecycle_stage_is_created(cls):
    kwargs = _minimal_kwargs(cls)
    instance = cls(**kwargs)
    assert instance.lifecycle_stage == "Created"


def test_invalid_lifecycle_stage_rejected():
    with pytest.raises(ValueError):
        RuntimeSession(session_id="s1", lifecycle_stage="Executing")


def test_observe_context_advances_created_to_observed():
    session = RuntimeSession(session_id="s1")
    observed = observe_context(session)
    assert observed.lifecycle_stage == "Observed"
    assert session.lifecycle_stage == "Created"  # original untouched


def test_observe_context_returns_new_instance_not_mutation():
    session = RuntimeSession(session_id="s1")
    observed = observe_context(session)
    assert observed is not session


def test_observe_context_rejects_already_observed():
    session = RuntimeSession(session_id="s1")
    observed = observe_context(session)
    with pytest.raises(ValueError):
        observe_context(observed)


def test_no_transition_beyond_observation_is_implemented():
    """112C objective 4: 'No transitions beyond observation.' There
    must be no complete()/archive()/update() method on any Context
    class."""
    for cls in ALL_CONTEXT_CLASSES:
        for forbidden in ("complete", "archive", "update", "execute"):
            assert not hasattr(cls, forbidden)


def _source_excluding_docstrings() -> str:
    """Every triple-quoted docstring (module, class, function) removed,
    leaving only executable code -- so a docstring that legitimately
    *names* a forbidden word to explain its absence cannot trip a
    substring check meant to verify the code itself."""
    tree = ast.parse(Path(rc.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                body[0].value.value = ""
    return ast.unparse(tree)


def test_no_executing_executed_rolledback_states_anywhere():
    code = _source_excluding_docstrings()
    for forbidden in ("Executing", "RolledBack", "'Executed'"):
        assert forbidden not in code


# ═══════════════════════════════════════════════════════════════════════
# Objective 5 — Ownership metadata (represented, not enforced)
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("cls", ALL_CONTEXT_CLASSES)
def test_every_class_carries_ownership_metadata(cls):
    assert isinstance(cls.OWNERSHIP, OwnershipMetadata)
    assert cls.OWNERSHIP.creates
    assert cls.OWNERSHIP.owns
    assert cls.OWNERSHIP.updates
    assert cls.OWNERSHIP.archives
    assert cls.OWNERSHIP.observes


def test_ownership_is_class_level_not_instance_field():
    """Ownership metadata must not be a constructor argument -- it is
    fixed per type, not per instance."""
    session = RuntimeSession(session_id="s1")
    field_names = {f.name for f in dataclasses.fields(session)}
    assert "OWNERSHIP" not in field_names


def test_runtime_owns_every_context_object():
    """112B §4: no row grants any Plugin, Broker, or Registry a
    create/update/archive action over any Context object."""
    for cls in ALL_CONTEXT_CLASSES:
        assert "Runtime" in cls.OWNERSHIP.creates
        assert "Runtime" in cls.OWNERSHIP.owns


# ═══════════════════════════════════════════════════════════════════════
# Objective 6 — Persistence metadata (represented, nothing persisted)
# ═══════════════════════════════════════════════════════════════════════


def test_persistence_buckets_match_112b():
    assert CONTEXT_PERSISTENCE_BUCKETS == (
        "Persistent",
        "Session-only",
        "Future persistence",
        "Never persist",
    )


@pytest.mark.parametrize("cls", ALL_CONTEXT_CLASSES)
def test_every_class_carries_a_valid_persistence_bucket(cls):
    assert cls.PERSISTENCE_BUCKET in CONTEXT_PERSISTENCE_BUCKETS


def test_broker_decision_bucket_is_never_persist():
    assert BrokerDecisionContext.PERSISTENCE_BUCKET == "Never persist"


def test_observation_bucket_is_session_only():
    assert ObservationContext.PERSISTENCE_BUCKET == "Session-only"


def test_session_task_phase_buckets_are_persistent():
    assert RuntimeSession.PERSISTENCE_BUCKET == "Persistent"
    assert TaskContext.PERSISTENCE_BUCKET == "Persistent"
    assert PhaseContext.PERSISTENCE_BUCKET == "Persistent"


def test_no_file_written_by_constructing_any_context_object(tmp_path, monkeypatch):
    """'Do not persist anything' -- constructing every object must not
    touch the filesystem."""
    monkeypatch.chdir(tmp_path)
    before = set(tmp_path.rglob("*"))
    evidence = EvidenceContext(evidence_id="e1", approval_id="a1")
    approval = ApprovalContext(approval_id="a1", decision_id="d1", evidence=(evidence,))
    decision = BrokerDecisionContext(decision_id="d1", intent_id="i1", approval=approval)
    intent = IntentContext(intent_id="i1", phase_id="p1", broker_decision=decision)
    phase = PhaseContext(phase_id="p1", intents=(intent,))
    task = TaskContext(task_id="t1", session_id="s1", phase_id="p1")
    obs = ObservationContext(observation_id="o1", session_id="s1")
    session = RuntimeSession(session_id="s1", tasks=(task,), observation=obs)
    RuntimeContext(session=session)
    after = set(tmp_path.rglob("*"))
    assert before == after


# ═══════════════════════════════════════════════════════════════════════
# Objective 7 — Relationship graph (resolved chain)
# ═══════════════════════════════════════════════════════════════════════


def test_relationship_chain_orders_broker_decision_before_approval():
    """112B §8.2's resolution, not 112A's original presentation order."""
    decision_idx = CONTEXT_RELATIONSHIP_CHAIN.index("BrokerDecisionContext")
    approval_idx = CONTEXT_RELATIONSHIP_CHAIN.index("ApprovalContext")
    assert decision_idx < approval_idx


def test_relationship_chain_extends_to_future_execution_audit_rollback():
    for future_item in ("ExecutionContext (future)", "AuditContext (future)", "RollbackContext (future)"):
        assert future_item in CONTEXT_RELATIONSHIP_CHAIN


def test_relationship_chain_full_order():
    assert CONTEXT_RELATIONSHIP_CHAIN == (
        "RuntimeSession",
        "TaskContext",
        "PhaseContext",
        "IntentContext",
        "BrokerDecisionContext",
        "ApprovalContext",
        "EvidenceContext",
        "ExecutionContext (future)",
        "AuditContext (future)",
        "RollbackContext (future)",
    )


def test_execution_remains_conceptual_only():
    """Execution/Audit/Rollback objects never appear as populated
    fields on any of the seven real objects -- they are named in the
    chain constant, not wired into live containment."""
    for cls in (RuntimeSession, TaskContext, PhaseContext, IntentContext, BrokerDecisionContext, ApprovalContext, EvidenceContext):
        field_types = {f.name for f in dataclasses.fields(cls)}
        assert "execution" not in field_types
        assert "audit" not in field_types
        assert "rollback" not in field_types


# ═══════════════════════════════════════════════════════════════════════
# Objective 8 — Observation-only guarantees
# ═══════════════════════════════════════════════════════════════════════


def test_current_runtime_state_is_observed():
    assert CURRENT_RUNTIME_STATE == "Observed"


def test_current_maximum_plugin_capability_is_observe():
    assert CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"


def test_execution_availability_is_unavailable():
    assert EXECUTION_AVAILABILITY == "unavailable"


def test_execution_context_status_is_execution_unavailable():
    exe = ExecutionContext(execution_id="x1")
    assert exe.status == "execution_unavailable"


def test_approval_context_status_defaults_not_implemented():
    approval = ApprovalContext(approval_id="a1", decision_id="d1")
    assert approval.status == "not_implemented"


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


def test_module_imports_are_allowlisted(module_imports):
    allowed = {"__future__", "dataclasses", "typing"}
    for name in module_imports:
        assert name in allowed, f"unexpected import: {name}"


def test_no_broker_evaluation_dependency(module_imports):
    forbidden = ("permission_broker", "command_path_observation")
    for name in module_imports:
        assert not any(f in name for f in forbidden), f"forbidden import: {name}"


def test_no_plugin_loading_dependency(module_imports):
    forbidden = ("runtime_registry", "plugin")
    for name in module_imports:
        assert not any(f in name for f in forbidden), f"forbidden import: {name}"


def test_module_has_no_shell_or_subprocess_dependency(module_imports):
    forbidden = ("subprocess", "os.system", "shell_gate")
    for name in module_imports:
        assert not any(f in name for f in forbidden), f"forbidden import: {name}"


def test_module_has_no_backend_or_network_dependency(module_imports):
    forbidden = ("backend_invocations", "backend_cli", "agent_backends", "socket", "requests", "urllib")
    for name in module_imports:
        assert not any(f in name for f in forbidden), f"forbidden import: {name}"


def test_no_eval_exec_importlib_in_module():
    tree = ast.parse(Path(rc.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
            assert name not in ("eval", "exec", "compile"), f"forbidden call: {name}"
    code = _source_excluding_docstrings()
    assert "importlib" not in code
    assert "subprocess" not in code


def test_no_cli_wiring_for_runtime_context():
    cli_text = (REPO_ROOT / "src" / "pcae" / "cli.py").read_text()
    assert "runtime_context" not in cli_text
    assert "runtime-context" not in cli_text


def test_no_pcae_commands_runtime_context_module():
    assert not (REPO_ROOT / "src" / "pcae" / "commands" / "runtime_context.py").exists()


def test_no_argparse_in_runtime_context_module():
    text = Path(rc.__file__).read_text()
    assert "argparse" not in text
    assert "add_parser" not in text


# ═══════════════════════════════════════════════════════════════════════
# Compatibility with 112B contract wording
# ═══════════════════════════════════════════════════════════════════════


def test_broker_decision_docstring_cites_resolved_ordering():
    text = BrokerDecisionContext.__doc__ or ""
    assert "112B" in text


def test_module_documents_deviation_from_112a_diagram_ordering():
    text = Path(rc.__file__).read_text()
    assert "resolved" in text.lower()
    assert "112B" in text


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════


def _minimal_kwargs(cls) -> dict:
    if cls is RuntimeContext:
        return {}
    if cls is RuntimeSession:
        return {"session_id": "s1"}
    if cls is TaskContext:
        return {"task_id": "t1", "session_id": "s1"}
    if cls is PhaseContext:
        return {"phase_id": "p1"}
    if cls is IntentContext:
        return {"intent_id": "i1", "phase_id": "p1"}
    if cls is BrokerDecisionContext:
        return {"decision_id": "d1", "intent_id": "i1"}
    if cls is ApprovalContext:
        return {"approval_id": "a1", "decision_id": "d1"}
    if cls is EvidenceContext:
        return {"evidence_id": "e1", "approval_id": "a1"}
    if cls is ObservationContext:
        return {"observation_id": "o1", "session_id": "s1"}
    if cls is ExecutionContext:
        return {"execution_id": "x1"}
    if cls is AuditContext:
        return {"audit_id": "au1"}
    if cls is RollbackContext:
        return {"rollback_id": "r1"}
    raise AssertionError(f"no minimal kwargs defined for {cls}")
