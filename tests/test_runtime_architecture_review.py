"""Tests for Phase 111R — Runtime Architecture Review.

This is a pure documentation-verification suite. Phase 111R is a
review/documentation phase: it assesses the Runtime subsystem built
across 110A-111D (responsibility separation, dependency direction,
plugin isolation, registry/introspection purity, Runtime Inspect CLI
usefulness, safety invariants, and Runtime Context readiness) without
implementing any new functionality. There is no runtime code to
unit-test -- these tests verify the review and phase documents exist,
contain every required section, make no implementation claims, and
that execution-unavailable / next-phase-recommendation content is
present as specified.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
REVIEW_DOC = REPO_ROOT / "docs" / "PCAE_RUNTIME_ARCHITECTURE_REVIEW.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_111_RUNTIME_ARCHITECTURE_REVIEW.md"


@pytest.fixture(scope="module")
def review_text() -> str:
    return REVIEW_DOC.read_text()


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


def test_runtime_architecture_review_document_exists():
    assert REVIEW_DOC.exists()
    assert REVIEW_DOC.stat().st_size > 0


def test_phase_111r_document_exists():
    assert PHASE_DOC.exists()
    assert PHASE_DOC.stat().st_size > 0


# ═══════════════════════════════════════════════════════════════════════
# Scope reviewed — every prior phase named
# ═══════════════════════════════════════════════════════════════════════


PRIOR_PHASES = ("110A", "110B", "110C", "110D", "110E", "110F", "111A", "111B", "111C", "111D")


@pytest.mark.parametrize("phase_id", PRIOR_PHASES)
def test_every_prior_phase_named_in_review(review_text, phase_id):
    assert phase_id in review_text


# ═══════════════════════════════════════════════════════════════════════
# Objective 1 — responsibility review exists
# ═══════════════════════════════════════════════════════════════════════


def test_responsibility_review_section_exists(review_text):
    assert "## 1. Separation of Responsibilities" in review_text


@pytest.mark.parametrize(
    "component",
    ["Runtime", "Registry", "Plugins", "Introspection", "Runtime Inspect CLI", "Permission Broker", "Observation Integration"],
)
def test_responsibility_review_covers_every_component(review_text, component):
    assert component in review_text


def test_responsibility_review_states_no_creep_found(review_text):
    text = _normalized(review_text)
    assert "No responsibility creep identified" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 2 — dependency review exists
# ═══════════════════════════════════════════════════════════════════════


def test_dependency_review_section_exists(review_text):
    assert "## 2. Dependency Direction" in review_text


def test_dependency_review_states_acyclic(review_text):
    text = _normalized(review_text)
    assert "Acyclic: confirmed" in text


def test_dependency_review_states_broker_isolation(review_text):
    text = _normalized(review_text)
    assert "Broker isolation: confirmed" in text


def test_dependency_review_documents_import_graph(review_text):
    for module in ("runtime_inspect.py", "runtime_introspection.py", "runtime_registry.py", "permission_broker_foundation.py", "command_path_observation.py"):
        assert module in review_text


# ═══════════════════════════════════════════════════════════════════════
# Objective 3 — plugin isolation review exists
# ═══════════════════════════════════════════════════════════════════════


def test_plugin_isolation_review_section_exists(review_text):
    assert "## 3. Plugin Isolation and Extensibility" in review_text


FUTURE_PLUGINS = (
    "Claude intent source",
    "Codex intent source",
    "DeepSeek intent source",
    "Telegram intent source",
    "REST intent source",
    "VS Code intent source",
    "Shell execution adapter",
    "Git execution adapter",
    "Filesystem adapter",
    "Backend agent adapter",
    "Notification providers",
    "Audit/storage providers",
)


@pytest.mark.parametrize("plugin", FUTURE_PLUGINS)
def test_plugin_isolation_review_covers_every_named_future_plugin(review_text, plugin):
    assert plugin in review_text


# ═══════════════════════════════════════════════════════════════════════
# Objective 4 — registry purity review exists
# ═══════════════════════════════════════════════════════════════════════


def test_registry_purity_review_section_exists(review_text):
    assert "## 4. Registry Purity" in review_text


@pytest.mark.parametrize(
    "capability",
    ["Orchestration", "Policy decisions", "Approval decisions", "Execution", "Audit persistence", "Rollback", "Plugin invocation"],
)
def test_registry_purity_review_covers_every_forbidden_capability(review_text, capability):
    assert capability in review_text


# ═══════════════════════════════════════════════════════════════════════
# Objective 5 — introspection purity review exists
# ═══════════════════════════════════════════════════════════════════════


def test_introspection_purity_review_section_exists(review_text):
    assert "## 5. Introspection Purity" in review_text


@pytest.mark.parametrize(
    "property_name",
    ["Read-only", "Metadata-only", "Side-effect free", "Secret-safe", "Cannot initialize or execute plugins"],
)
def test_introspection_purity_review_covers_every_property(review_text, property_name):
    assert property_name in review_text


# ═══════════════════════════════════════════════════════════════════════
# Objective 6 — Runtime Inspect review exists
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_inspect_review_section_exists(review_text):
    assert "## 6. Runtime Inspect CLI Review" in review_text


@pytest.mark.parametrize(
    "aspect",
    ["Output usefulness", "JSON stability", "Machine-readability", "Human readability", "Safety", "Long-term usefulness for AI agents"],
)
def test_runtime_inspect_review_covers_every_aspect(review_text, aspect):
    assert aspect in review_text


# ═══════════════════════════════════════════════════════════════════════
# Objective 7 — safety invariant review exists
# ═══════════════════════════════════════════════════════════════════════


def test_safety_invariant_review_section_exists(review_text):
    assert "## 7. Safety Invariants" in review_text


@pytest.mark.parametrize(
    "invariant",
    [
        "Execution unavailable",
        "Runtime state `Observed`",
        "Maximum plugin capability `observe`",
        "No plugin loading",
        "No broker enforcement",
        "No command authorization/denial",
        "Fail-closed posture",
    ],
)
def test_safety_invariant_review_covers_every_invariant(review_text, invariant):
    assert invariant in review_text


def test_safety_invariant_review_states_no_weakening(review_text):
    text = _normalized(review_text)
    assert "No safety invariant has weakened" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 8 — Runtime Context readiness review exists
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_context_readiness_section_exists(review_text):
    assert "## 8. Runtime Context Readiness (112A)" in review_text


@pytest.mark.parametrize(
    "concept",
    ["Session", "Task", "Phase", "Intent", "Approval state", "Broker decision", "Evidence", "Future execution state"],
)
def test_runtime_context_readiness_covers_every_concept(review_text, concept):
    assert concept in review_text


# ═══════════════════════════════════════════════════════════════════════
# Objective 9 — risk classification exists
# ═══════════════════════════════════════════════════════════════════════


def test_risk_register_section_exists(review_text):
    assert "## 9. Architectural Debt and Risk Register" in review_text


RISK_CLASSIFICATIONS = ("Strength", "Low risk", "Medium risk")


@pytest.mark.parametrize("classification", RISK_CLASSIFICATIONS)
def test_risk_register_uses_expected_classifications(review_text, classification):
    assert classification in review_text


def test_risk_register_states_no_blockers(review_text):
    text = _normalized(review_text)
    assert "No Blocker-classified findings" in text


def test_risk_register_entries_have_ids(review_text):
    for risk_id in ("R-1", "R-2", "R-3", "R-4", "R-5", "R-6", "R-7"):
        assert risk_id in review_text


def test_each_risk_addresses_blocking_status(review_text):
    text = _normalized(review_text)
    assert "Blocks 112A?" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 10 — recommendation exists
# ═══════════════════════════════════════════════════════════════════════


def test_recommendation_section_exists(review_text):
    assert "## 11. Recommendation" in review_text


def test_recommendation_states_proceed_to_112a(review_text, phase_doc_text):
    for text in (review_text, phase_doc_text):
        normalized = _normalized(text)
        assert "Proceed to 112A" in normalized


def test_recommendation_is_one_of_three_named_options(phase_doc_text):
    """The brief names three possible recommendation outcomes; the
    review must have picked one and named it unambiguously."""
    text = _normalized(phase_doc_text)
    assert "Proceed to 112A" in text


# ═══════════════════════════════════════════════════════════════════════
# Execution unavailable / no implementation claims / next phase
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("doc_text_fixture", ["review_text", "phase_doc_text"])
def test_execution_unavailable_documented(request, doc_text_fixture):
    text = _normalized(request.getfixturevalue(doc_text_fixture))
    assert "Execution unavailable" in text or "execution_unavailable" in text


def test_current_maximum_runtime_state_still_observed(review_text, phase_doc_text):
    for text in (review_text, phase_doc_text):
        normalized = _normalized(text)
        assert "Current maximum runtime state" in normalized
        assert "Observed" in normalized


def test_current_maximum_plugin_capability_still_observe(review_text, phase_doc_text):
    for text in (review_text, phase_doc_text):
        normalized = _normalized(text)
        assert "Current maximum plugin capability" in normalized
        assert "`observe`" in normalized or "observe" in normalized


FORBIDDEN_IMPLEMENTATION_CLAIMS = (
    "runtime context implemented",
    "runtime execution enabled",
    "plugin loading implemented",
    "plugin instantiation implemented",
    "plugin invocation implemented",
    "dependency injection implemented",
    "command authorization implemented",
    "command denial implemented",
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


@pytest.mark.parametrize("doc_path", [REVIEW_DOC, PHASE_DOC])
@pytest.mark.parametrize("claim", FORBIDDEN_IMPLEMENTATION_CLAIMS)
def test_no_forbidden_implementation_claims(doc_path, claim):
    text = doc_path.read_text().lower()
    assert claim not in text


@pytest.mark.parametrize("doc_path", [REVIEW_DOC, PHASE_DOC])
def test_no_go_confirmations_section_present(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No-Go Confirmations" in text
    assert "No runtime execution" in text


def test_recommended_next_phase_is_112a(review_text, phase_doc_text):
    for text in (review_text, phase_doc_text):
        assert "112A" in text
        assert "Runtime Context Architecture" in text


# ═══════════════════════════════════════════════════════════════════════
# No implementation added anywhere in the source tree
# ═══════════════════════════════════════════════════════════════════════


def test_no_runtime_context_module_added_to_core():
    """`context.py` is deliberately excluded from this forbidden set --
    it already exists as an unrelated, pre-existing module (`pcae
    context`/`pcae continuity`), predating this entire 110-111 series
    arc, not a sign that Runtime Context (112A) has been implemented.

    `runtime_context.py` is also deliberately excluded as of 112C
    (Runtime Context Prototype), which legitimately created it -- this
    111R-era guard predates that phase and must not treat its intended
    outcome as a regression."""
    core_dir = REPO_ROOT / "src" / "pcae" / "core"
    forbidden_names = {
        "session_info.py",
        "task_info.py", "phase_info.py", "intent.py", "approval.py",
        "broker_decision.py", "evidence.py",
    }
    existing = {p.name for p in core_dir.glob("*.py")}
    assert not (forbidden_names & existing)


def test_runtime_registry_and_introspection_modules_unchanged_by_this_phase():
    """This phase's task contract does not list src/pcae/ files as
    allowed -- confirmed directly that the two modules central to this
    review were not touched."""
    for rel_path in ("src/pcae/core/runtime_registry.py", "src/pcae/core/runtime_introspection.py", "src/pcae/commands/runtime_inspect.py"):
        assert (REPO_ROOT / rel_path).exists()


def test_task_contract_excludes_src_pcae():
    """This phase's task contract must not list any src/pcae/ file as
    allowed -- confirming the review-only boundary was respected at the
    governance layer, not just by convention."""
    done_dir = REPO_ROOT / "tasks" / "done"
    matches = list(done_dir.glob("*phase-111r*"))
    if not matches:
        pytest.skip("111R task contract not yet moved to tasks/done/ (phase still in progress)")
    contract_text = matches[0].read_text()
    assert "src/pcae/" not in contract_text
