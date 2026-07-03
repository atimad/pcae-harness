"""Tests for Phase 112B — Runtime Context Contract Freeze.

This is a pure documentation-verification suite. Phase 112B is a
contract/freeze phase: it freezes the exact immutable identities, state
models, ownership, persistence expectations, relationships, and
invariants for every Runtime Context object 112A designed, and resolves
the two findings 112A deliberately deferred -- without implementing any
Runtime Context module, persistence mechanism, or execution capability.
There is no runtime code to unit-test -- these tests verify the
documents exist, contain the required frozen content, make no
implementation claims, and that identity, state, ownership,
persistence, relationships, invariants, and both resolutions are
present as specified.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACT_DOC = REPO_ROOT / "docs" / "PCAE_RUNTIME_CONTEXT_CONTRACT.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_112_RUNTIME_CONTEXT_CONTRACT_FREEZE.md"
ARCHITECTURE_DOC = REPO_ROOT / "docs" / "PCAE_RUNTIME_CONTEXT_ARCHITECTURE.md"


@pytest.fixture(scope="module")
def contract_text() -> str:
    return CONTRACT_DOC.read_text()


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


def test_runtime_context_contract_document_exists():
    assert CONTRACT_DOC.exists()
    assert CONTRACT_DOC.stat().st_size > 0


def test_phase_112b_document_exists():
    assert PHASE_DOC.exists()
    assert PHASE_DOC.stat().st_size > 0


def test_architecture_doc_still_present_unmodified_reference():
    """112B builds on 112A; 112A's own document must still exist."""
    assert ARCHITECTURE_DOC.exists()


# ═══════════════════════════════════════════════════════════════════════
# New principle: Identity precedes state
# ═══════════════════════════════════════════════════════════════════════


def test_identity_precedes_state_principle_documented(contract_text):
    text = _normalized(contract_text)
    assert "Identity precedes state." in text


def test_identity_precedes_state_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    assert "Identity precedes state" in text


def test_prior_principles_restated(contract_text):
    text = _normalized(contract_text)
    for principle in (
        "Runtime orchestrates.",
        "Registry resolves.",
        "Plugins implement.",
        "Metadata precedes behavior.",
        "Visibility precedes authority.",
        "Context precedes execution.",
    ):
        assert principle in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 1 — Contract freeze overview
# ═══════════════════════════════════════════════════════════════════════


def test_contract_freeze_overview_section_exists(contract_text):
    assert "## 1. Contract Freeze Overview" in contract_text


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


@pytest.mark.parametrize("obj", CONTEXT_OBJECTS)
def test_every_context_object_covered_by_contract(contract_text, obj):
    assert f"`{obj}`" in contract_text


def test_twelve_objects_covered(contract_text):
    assert len(CONTEXT_OBJECTS) == 12
    for obj in CONTEXT_OBJECTS:
        assert obj in contract_text


def test_no_thirteenth_object_introduced(contract_text):
    text = _normalized(contract_text)
    assert "does not introduce a thirteenth object" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 2 — Identity contracts
# ═══════════════════════════════════════════════════════════════════════


def test_identity_contracts_section_exists(contract_text):
    assert "## 2. Identity Contracts" in contract_text


IDENTITY_FIELDS = (
    "session_id",
    "task_id",
    "phase_id",
    "intent_id",
    "approval_id",
    "decision_id",
    "evidence_id",
    "observation_id",
    "execution_id",
    "audit_id",
    "rollback_id",
)


@pytest.mark.parametrize("identifier", IDENTITY_FIELDS)
def test_identifier_documented(contract_text, identifier):
    assert f"`{identifier}`" in contract_text


def test_identity_contracts_document_uniqueness_immutability_lifetime_ownership(contract_text):
    text = contract_text
    assert "Uniqueness" in text
    assert "Immutability" in text
    assert "Lifetime" in text
    assert "Ownership" in text


def test_runtime_context_has_no_independent_identity(contract_text):
    text = _normalized(contract_text)
    assert "not independently identified" in text


def test_identity_contracts_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text
    assert "session_id" in text
    assert "rollback_id" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 3 — State contracts
# ═══════════════════════════════════════════════════════════════════════


def test_state_contracts_section_exists(contract_text):
    assert "## 3. State Contracts" in contract_text


LIFECYCLE_STAGES = ("Created", "Initialized", "Observed", "Updated", "Completed", "Archived")


@pytest.mark.parametrize("stage", LIFECYCLE_STAGES)
def test_lifecycle_stage_present_in_contract(contract_text, stage):
    assert f"`{stage}`" in contract_text


def test_state_contract_defines_terminal_states(contract_text):
    text = _normalized(contract_text)
    assert "Terminal states" in text
    assert "unconditionally terminal" in text


def test_state_contract_defines_invalid_transitions(contract_text):
    text = _normalized(contract_text)
    assert "Invalid transitions" in text
    assert "backward" in text.lower()


def test_state_contract_forbids_execution_states(contract_text):
    text = _normalized(contract_text)
    assert "Executing" in text
    assert "Executed" in text
    assert "RolledBack" in text


def test_per_object_ceilings_documented(contract_text):
    text = _normalized(contract_text)
    assert "Per-object ceilings" in text


def test_state_contracts_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text.lower()
    assert "state contract" in text
    assert "ceiling" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 4 — Ownership contracts
# ═══════════════════════════════════════════════════════════════════════


def test_ownership_contracts_section_exists(contract_text):
    assert "## 4. Ownership Contracts" in contract_text


OWNERSHIP_ACTIONS = ("Creates", "Owns", "Updates", "Archives", "Observes")


@pytest.mark.parametrize("action", OWNERSHIP_ACTIONS)
def test_ownership_action_column_present(contract_text, action):
    assert action in contract_text


def test_no_plugin_broker_registry_owns_context_object(contract_text):
    text = _normalized(contract_text)
    assert "never grants any Plugin, Broker, or Registry" in text or "No row above grants any Plugin, Broker, or Registry" in text


def test_ownership_summarized_in_phase_doc(phase_doc_text):
    text = _normalized(phase_doc_text)
    assert "Ownership Contract" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 5 — Persistence contracts
# ═══════════════════════════════════════════════════════════════════════


def test_persistence_contracts_section_exists(contract_text):
    assert "## 5. Persistence Contracts" in contract_text


PERSISTENCE_BUCKETS = ("Persistent", "Session-only", "Future persistence", "Never persist")


@pytest.mark.parametrize("bucket", PERSISTENCE_BUCKETS)
def test_persistence_bucket_documented(contract_text, bucket):
    assert bucket in contract_text


def test_persistence_never_persist_field_rule_documented(contract_text):
    text = _normalized(contract_text)
    assert "What must never persist" in text
    assert "credentials" in text.lower() or "secret" in text.lower()


def test_broker_decision_observation_bucket_distinction_documented(contract_text):
    """112B sharpens 112A's loose 'session-only/ephemeral' wording into
    two distinct buckets for Broker Decision vs Observation state."""
    text = _normalized(contract_text)
    assert "Sharpened from 112A" in text


def test_persistence_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text
    assert "Persistent" in text
    assert "Never persist" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 6 — Relationships
# ═══════════════════════════════════════════════════════════════════════


def test_relationship_contracts_section_exists(contract_text):
    assert "## 6. Relationship Contracts" in contract_text


def test_resolved_chain_orders_broker_decision_before_approval(contract_text):
    text = contract_text
    broker_idx = text.index("Broker Decision")
    # Find the resolved chain block specifically (contains "(future) Execution")
    chain_start = text.index("Resolved chain")
    chain_block = text[chain_start:chain_start + 600]
    assert "Broker Decision" in chain_block
    assert "Approval" in chain_block
    assert chain_block.index("Broker Decision") < chain_block.index("Approval")


def test_relationship_chain_extends_to_future_audit_and_rollback(contract_text):
    text = _normalized(contract_text)
    assert "(future) Audit" in text
    assert "(future) Rollback" in text


def test_relationships_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text
    assert "Broker Decision" in text
    assert "Approval" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 7 — Invariants
# ═══════════════════════════════════════════════════════════════════════


def test_invariant_contracts_section_exists(contract_text):
    assert "## 7. Invariant Contracts" in contract_text


def test_nine_invariants_documented(contract_text):
    text = _normalized(contract_text)
    assert "Nine invariants" in text


def test_resolved_task_phase_invariant_documented(contract_text):
    text = _normalized(contract_text)
    assert "most one Task is active per Phase" in text


def test_broker_decision_precedes_approval_invariant_documented(contract_text):
    text = _normalized(contract_text)
    assert "Broker Decision precedes Approval" in text


def test_identity_immutable_invariant_documented(contract_text):
    text = _normalized(contract_text)
    assert "Identity is immutable and precedes state" in text


def test_execution_unavailable_invariant_documented(contract_text):
    text = _normalized(contract_text)
    assert "Execution unavailable" in text


def test_observation_always_available_invariant_documented(contract_text):
    text = _normalized(contract_text)
    assert "Observation always available" in text


def test_invariants_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text.lower()
    assert "invariant" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 8 — Resolution of deferred findings
# ═══════════════════════════════════════════════════════════════════════


def test_resolution_section_exists(contract_text):
    assert "## 8. Resolution of Deferred Findings" in contract_text


def test_task_phase_cardinality_resolution_documented(contract_text):
    text = _normalized(contract_text)
    assert "8.1 Task:Phase cardinality" in text or "Task:Phase cardinality vs" in text
    assert "Resolution." in text


def test_approval_broker_decision_ordering_resolution_documented(contract_text):
    text = _normalized(contract_text)
    assert "8.2 Approval vs. Broker Decision ordering" in text or "Approval vs. Broker Decision ordering" in text
    assert "Decision Pipeline" in text
    assert "110A" in text


def test_both_resolutions_cite_evidence_not_assumption(contract_text):
    text = _normalized(contract_text)
    assert "not a new design decision" in text or "not a new assumption" in text


def test_deferred_findings_resolution_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text
    assert "Resolution of Deferred Findings" in text


# ═══════════════════════════════════════════════════════════════════════
# Execution unavailable / Observed / observe reconfirmation
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("doc_text_fixture", ["contract_text", "phase_doc_text"])
def test_execution_unavailable_documented(request, doc_text_fixture):
    text = _normalized(request.getfixturevalue(doc_text_fixture))
    assert "Execution unavailable" in text or "execution_unavailable" in text


def test_current_maximum_runtime_state_still_observed(contract_text, phase_doc_text):
    for text in (contract_text, phase_doc_text):
        normalized = _normalized(text)
        assert "Current maximum runtime state" in normalized
        assert "Observed" in normalized


def test_current_maximum_plugin_capability_still_observe(contract_text, phase_doc_text):
    for text in (contract_text, phase_doc_text):
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


@pytest.mark.parametrize("doc_path", [CONTRACT_DOC, PHASE_DOC])
@pytest.mark.parametrize("claim", FORBIDDEN_IMPLEMENTATION_CLAIMS)
def test_no_forbidden_implementation_claims(doc_path, claim):
    text = doc_path.read_text().lower()
    assert claim not in text


@pytest.mark.parametrize("doc_path", [CONTRACT_DOC, PHASE_DOC])
def test_no_runtime_context_implementation_claimed(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No Runtime Context implementation" in text


@pytest.mark.parametrize("doc_path", [CONTRACT_DOC, PHASE_DOC])
def test_no_persistence_or_database_claimed(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No persistence implementation" in text
    assert "No database" in text


@pytest.mark.parametrize("doc_path", [CONTRACT_DOC, PHASE_DOC])
def test_no_go_confirmations_section_present(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No-Go Confirmations" in text
    assert "No runtime execution" in text


# ═══════════════════════════════════════════════════════════════════════
# Next phase recommendation exists
# ═══════════════════════════════════════════════════════════════════════


def test_recommended_next_phase_is_112c(contract_text, phase_doc_text):
    for text in (contract_text, phase_doc_text):
        assert "112C" in text
        assert "Runtime Context Prototype" in text


# ═══════════════════════════════════════════════════════════════════════
# No runtime implementation added anywhere in the source tree
# ═══════════════════════════════════════════════════════════════════════


def test_no_context_module_added_to_core():
    core_dir = REPO_ROOT / "src" / "pcae" / "core"
    forbidden_names = {
        "runtime_context.py", "task_context.py", "phase_context.py",
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
    matches = list(done_dir.glob("*phase-112b*"))
    if not matches:
        pytest.skip("112B task contract not yet moved to tasks/done/ (phase still in progress)")
    contract_text_ = matches[0].read_text()
    allowed_files_start = contract_text_.index("## Allowed Files")
    allowed_files_end = contract_text_.index("##", allowed_files_start + 1)
    allowed_files_section = contract_text_[allowed_files_start:allowed_files_end]
    assert "src/pcae/" not in allowed_files_section
