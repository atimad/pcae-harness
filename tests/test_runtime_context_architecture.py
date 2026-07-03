"""Tests for Phase 112A — Runtime Context Architecture.

This is a pure documentation-verification suite. Phase 112A is an
architecture/design phase: it designs how PCAE models the current
operational state of the Runtime while preserving the complete
non-executing guarantees established through 111R -- without
implementing any Runtime Context module, persistence mechanism, or
execution capability. There is no runtime code to unit-test -- these
tests verify the documents exist, contain the required frozen content,
make no implementation claims, and that the Persistent/Session split,
object model, lifecycle, ownership, relationships, persistence model,
and invariants are present as specified.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTEXT_DOC = REPO_ROOT / "docs" / "PCAE_RUNTIME_CONTEXT_ARCHITECTURE.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_112_RUNTIME_CONTEXT_ARCHITECTURE.md"


@pytest.fixture(scope="module")
def context_text() -> str:
    return CONTEXT_DOC.read_text()


@pytest.fixture(scope="module")
def phase_doc_text() -> str:
    return PHASE_DOC.read_text()


def _normalized(text: str) -> str:
    """Collapse markdown line-wrap whitespace so a multi-word phrase can
    be matched even when it happens to straddle a hard-wrapped line."""
    return re.sub(r"\s+", " ", text)


# ═══════════════════════════════════════════════════════════════════════
# Documents exist
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_context_document_exists():
    assert CONTEXT_DOC.exists()
    assert CONTEXT_DOC.stat().st_size > 0


def test_phase_112a_document_exists():
    assert PHASE_DOC.exists()
    assert PHASE_DOC.stat().st_size > 0


# ═══════════════════════════════════════════════════════════════════════
# Core architectural principle
# ═══════════════════════════════════════════════════════════════════════


def test_preserved_principles_present(context_text):
    text = _normalized(context_text)
    assert "Runtime orchestrates." in text
    assert "Registry resolves." in text
    assert "Plugins implement." in text
    assert "Metadata precedes behavior." in text
    assert "Visibility precedes authority." in text


def test_context_precedes_execution_principle_documented(context_text):
    text = _normalized(context_text)
    assert "Context precedes execution." in text


def test_context_precedes_execution_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    assert "Context precedes execution" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 1 — Runtime Context defined
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_context_definition_section_exists(context_text):
    assert "## 1. Runtime Context, Defined" in context_text


def test_context_defined_as_dynamic_operational_model(context_text):
    text = _normalized(context_text)
    assert "dynamic operational model" in text


def test_context_describes_never_executes(context_text):
    text = _normalized(context_text)
    assert "Context describes; it never executes" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 2 — Persistent vs Session Context
# ═══════════════════════════════════════════════════════════════════════


def test_persistent_vs_session_context_section_exists(context_text):
    assert "## 2. Persistent vs Session Context" in context_text


PERSISTENT_CONTEXT_EXAMPLES = (
    "Runtime identity",
    "Registry",
    "Plugin metadata",
    "Capability metadata",
    "Runtime version",
    "Contracts",
)

SESSION_CONTEXT_EXAMPLES = (
    "Session",
    "Task",
    "Phase",
    "Intent",
    "Approval state",
    "Broker decision",
    "Evidence",
    "Observation state",
)


@pytest.mark.parametrize("example", PERSISTENT_CONTEXT_EXAMPLES)
def test_persistent_context_example_documented(context_text, example):
    assert example in context_text


@pytest.mark.parametrize("example", SESSION_CONTEXT_EXAMPLES)
def test_session_context_example_documented(context_text, example):
    assert example in context_text


def test_persistent_session_split_explains_why_separate(context_text):
    text = _normalized(context_text)
    assert "Why separate" in text


def test_persistent_session_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text
    assert "Persistent Context" in text
    assert "Session Context" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 3 — Context object model
# ═══════════════════════════════════════════════════════════════════════

CONTEXT_OBJECTS = (
    "RuntimeContext",
    "RuntimeSession",
    "TaskContext",
    "PhaseContext",
    "IntentContext",
    "ApprovalContext",
    "BrokerDecisionContext",
    "EvidenceContext",
    "ObservationContext",
    "ExecutionContext",
    "AuditContext",
    "RollbackContext",
)


def test_context_object_model_section_exists(context_text):
    assert "## 3. Runtime Context Object Model" in context_text


@pytest.mark.parametrize("obj", CONTEXT_OBJECTS)
def test_context_object_documented(context_text, obj):
    assert f"`{obj}`" in context_text


def test_twelve_context_objects_documented(context_text):
    assert len(CONTEXT_OBJECTS) == 12
    for obj in CONTEXT_OBJECTS:
        assert obj in context_text


def test_execution_context_marked_execution_unavailable(context_text):
    text = _normalized(context_text)
    assert "execution_unavailable" in text


def test_context_objects_are_design_only(context_text):
    text = _normalized(context_text)
    assert "No implementation." in text


def test_context_objects_summarized_in_phase_doc(phase_doc_text):
    for obj in ("RuntimeContext", "RuntimeSession", "TaskContext", "PhaseContext", "ExecutionContext"):
        assert obj in phase_doc_text


# ═══════════════════════════════════════════════════════════════════════
# Objective 4 — Lifecycle
# ═══════════════════════════════════════════════════════════════════════

LIFECYCLE_STAGES = ("Created", "Initialized", "Observed", "Updated", "Completed", "Archived")


def test_lifecycle_section_exists(context_text):
    assert "## 4. Lifecycle" in context_text


@pytest.mark.parametrize("stage", LIFECYCLE_STAGES)
def test_lifecycle_stage_documented(context_text, stage):
    assert f"`{stage}`" in context_text


def test_six_lifecycle_stages_documented(context_text):
    assert len(LIFECYCLE_STAGES) == 6
    for stage in LIFECYCLE_STAGES:
        assert stage in context_text


def test_future_execution_states_out_of_scope(context_text):
    text = _normalized(context_text)
    assert "Future execution states remain explicitly out of scope" in text


def test_lifecycle_distinct_from_runtime_state_model_and_plugin_lifecycle(context_text):
    text = _normalized(context_text)
    assert "distinct vocabulary" in text.lower() or "Runtime State Model" in text


def test_lifecycle_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text.lower()
    assert "lifecycle" in text
    assert "six stages" in text or "6 stages" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 5 — Ownership
# ═══════════════════════════════════════════════════════════════════════


def test_ownership_section_exists(context_text):
    assert "## 5. Ownership" in context_text
    assert "**The Runtime owns:**" in context_text
    assert "**The Registry owns:**" in context_text
    assert "**Plugins own:**" in context_text
    assert "**The Broker owns:**" in context_text
    assert "**Context never owns:**" in context_text


RUNTIME_OWNS = ("Context lifecycle", "Current context", "Context transitions")
CONTEXT_NEVER_OWNS = ("Execution", "Approval decisions", "Policy evaluation")


@pytest.mark.parametrize("item", RUNTIME_OWNS)
def test_runtime_owns_item_documented(context_text, item):
    assert item in context_text


@pytest.mark.parametrize("item", CONTEXT_NEVER_OWNS)
def test_context_never_owns_item_documented(context_text, item):
    assert item in context_text


def test_ownership_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    assert "Context never owns" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 6 — Relationships
# ═══════════════════════════════════════════════════════════════════════


def test_relationships_section_exists(context_text):
    assert "## 6. Context Relationships" in context_text


RELATIONSHIP_ENTITIES = ("Session", "Task", "Phase", "Intent", "Approval", "Broker Decision", "Evidence")


@pytest.mark.parametrize("entity", RELATIONSHIP_ENTITIES)
def test_relationship_entity_documented(context_text, entity):
    assert entity in context_text


def test_relationship_chain_names_future_execution(context_text):
    text = _normalized(context_text)
    assert "(future) Execution" in text


def test_task_phase_cardinality_finding_documented(context_text):
    """This document's evidence-grounded finding (many Tasks per Phase,
    verified against this session's own operational pattern) must be
    documented, not silently omitted."""
    text = _normalized(context_text)
    assert "many Tasks to one Phase" in text or "many-to-one" in text.lower()


def test_approval_broker_decision_ordering_tension_documented(context_text):
    text = _normalized(context_text)
    assert "ordering tension" in text.lower()
    assert "112B" in text


def test_relationships_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text
    assert "Session" in text
    assert "Broker Decision" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 7 — Persistence model (111R condition)
# ═══════════════════════════════════════════════════════════════════════


def test_persistence_model_section_exists(context_text):
    assert "## 7. Persistence Model" in context_text


PERSISTENCE_CONCEPTS = ("Session", "Task", "Phase", "Intent", "Approval", "Broker decision", "Evidence", "Observation state")


@pytest.mark.parametrize("concept", PERSISTENCE_CONCEPTS)
def test_persistence_model_addresses_every_concept(context_text, concept):
    assert concept in context_text


def test_persistence_model_addresses_111r_condition(context_text):
    text = _normalized(context_text)
    assert "111R" in text
    assert "per-concept" in text.lower()


def test_persistence_model_documents_what_must_never_persist(context_text):
    text = _normalized(context_text)
    assert "What must never persist" in text
    assert "credentials" in text.lower() or "secret" in text.lower()


def test_broker_decision_persistence_explicitly_out_of_scope(context_text):
    text = _normalized(context_text)
    assert "out of 112A" in text or "out of 112A's scope" in text


def test_persistence_model_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text.lower()
    assert "persistence model" in text
    assert "111r" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 8 — Context invariants
# ═══════════════════════════════════════════════════════════════════════


def test_context_invariants_section_exists(context_text):
    assert "## 8. Context Invariants" in context_text


CONTEXT_INVARIANTS = (
    "Exactly one active Runtime Context",
    "Task belongs to one Session",
    "Phase belongs to one Task",
    "Intent belongs to one Phase",
    "Execution unavailable",
    "Observation always available",
)


@pytest.mark.parametrize("invariant", CONTEXT_INVARIANTS)
def test_context_invariant_documented(context_text, invariant):
    assert invariant in context_text


def test_invariants_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text.lower()
    assert "invariant" in text


# ═══════════════════════════════════════════════════════════════════════
# Execution unavailable / Observed / observe reconfirmation
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("doc_text_fixture", ["context_text", "phase_doc_text"])
def test_execution_unavailable_documented(request, doc_text_fixture):
    text = _normalized(request.getfixturevalue(doc_text_fixture))
    assert "Execution unavailable" in text or "execution_unavailable" in text


def test_current_maximum_runtime_state_still_observed(context_text, phase_doc_text):
    for text in (context_text, phase_doc_text):
        normalized = _normalized(text)
        assert "Current maximum runtime state" in normalized
        assert "Observed" in normalized


def test_current_maximum_plugin_capability_still_observe(context_text, phase_doc_text):
    for text in (context_text, phase_doc_text):
        normalized = _normalized(text)
        assert "Current maximum plugin capability" in normalized
        assert "`observe`" in normalized or "observe" in normalized


# ═══════════════════════════════════════════════════════════════════════
# No implementation claims
# ═══════════════════════════════════════════════════════════════════════

FORBIDDEN_IMPLEMENTATION_CLAIMS = (
    "runtime context implemented",
    "persistence implemented",
    "database implemented",
    "serialization implemented",
    "runtime execution enabled",
    "plugin loading implemented",
    "plugin instantiation implemented",
    "plugin invocation implemented",
    "dependency injection implemented",
    "shell mediation implemented",
    "backend invocation implemented",
    "adapter invocation implemented",
    "execution enablement implemented",
    "execution capability implemented",
    "permission broker enforcement implemented",
    "audit persistence implemented",
    "rollback execution implemented",
    "emergency stop implemented",
    "telegram inbound implemented",
    "rest endpoint implemented",
    "web ui implemented",
    "daemon implemented",
    "background worker implemented",
    "automatic apply implemented",
)


@pytest.mark.parametrize("doc_path", [CONTEXT_DOC, PHASE_DOC])
@pytest.mark.parametrize("claim", FORBIDDEN_IMPLEMENTATION_CLAIMS)
def test_no_forbidden_implementation_claims(doc_path, claim):
    text = doc_path.read_text().lower()
    assert claim not in text


@pytest.mark.parametrize("doc_path", [CONTEXT_DOC, PHASE_DOC])
def test_no_runtime_context_implementation_claimed(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No Runtime Context implementation" in text


@pytest.mark.parametrize("doc_path", [CONTEXT_DOC, PHASE_DOC])
def test_no_persistence_or_database_claimed(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No persistence implementation" in text
    assert "No database" in text


@pytest.mark.parametrize("doc_path", [CONTEXT_DOC, PHASE_DOC])
def test_no_go_confirmations_section_present(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No-Go Confirmations" in text
    assert "No runtime execution" in text


# ═══════════════════════════════════════════════════════════════════════
# Next phase recommendation exists
# ═══════════════════════════════════════════════════════════════════════


def test_recommended_next_phase_is_112b(context_text, phase_doc_text):
    for text in (context_text, phase_doc_text):
        assert "112B" in text
        assert "Runtime Context Contract Freeze" in text


# ═══════════════════════════════════════════════════════════════════════
# No runtime implementation added anywhere in the source tree
# ═══════════════════════════════════════════════════════════════════════


def test_no_context_module_added_to_core():
    """`runtime_context.py` itself is deliberately excluded from this
    guard: 112C (Runtime Context Prototype) legitimately created it,
    combining all twelve objects into one module rather than twelve
    per-object files -- this test's job is to guard against exactly
    those still-nonexistent per-object files, not the real module."""
    core_dir = REPO_ROOT / "src" / "pcae" / "core"
    forbidden_names = {
        "task_context.py", "phase_context.py",
        "intent_context.py", "approval_context.py", "broker_decision_context.py",
        "evidence_context.py", "observation_context.py", "execution_context.py",
        "audit_context.py", "rollback_context.py", "runtime_session.py",
    }
    existing = {p.name for p in core_dir.glob("*.py")}
    assert not (forbidden_names & existing)


def test_no_new_directory_added_for_context():
    assert not (REPO_ROOT / "src" / "pcae" / "context").exists()
    assert not (REPO_ROOT / "src" / "pcae" / "runtime").exists()
    assert not (REPO_ROOT / "src" / "pcae" / "plugins").exists()


def test_task_contract_excludes_src_pcae():
    """This phase's task contract must not list any src/pcae/ file as
    allowed -- confirming the design-only boundary was respected at the
    governance layer, not just by convention."""
    done_dir = REPO_ROOT / "tasks" / "done"
    matches = list(done_dir.glob("*phase-112a*"))
    if not matches:
        pytest.skip("112A task contract not yet moved to tasks/done/ (phase still in progress)")
    contract_text = matches[0].read_text()
    assert "src/pcae/" not in contract_text
