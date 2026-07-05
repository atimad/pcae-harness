"""Phase 114R: Repository State Kernel Review.

Architecture/documentation verification only. This phase adds no runtime
behavior -- these tests verify the frozen review documents exist and
contain the required content, not any executable behavior.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
KERNEL_DOC = REPO_ROOT / "docs" / "PCAE_REPOSITORY_STATE_KERNEL.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_114R_REPOSITORY_STATE_KERNEL_REVIEW.md"


def _read(path: Path) -> str:
    assert path.exists(), f"expected document missing: {path}"
    return path.read_text(encoding="utf-8")


def _normalized(path: Path) -> str:
    return " ".join(_read(path).split())


# ── Document existence ────────────────────────────────────────────────────


def test_kernel_document_exists():
    assert KERNEL_DOC.exists()


def test_phase_document_exists():
    assert PHASE_DOC.exists()


# ── Kernel primitive definitions ────────────────────────────────────────────


def test_four_primitives_defined():
    text = _read(KERNEL_DOC)
    for primitive in ("Repository State", "Repository Transition", "Repository Artifact", "Repository Event"):
        assert primitive in text


def test_repository_decision_conclusion_documented():
    text = _read(KERNEL_DOC)
    assert "Repository Decision" in text
    assert "TransitionResult" in text
    assert "fifth" in text.lower()


# ── Invariant taxonomy ──────────────────────────────────────────────────────


def test_invariant_taxonomy_present():
    text = _read(KERNEL_DOC)
    assert "Invariant Taxonomy" in text
    for invariant in (
        "phase_identity_consistency",
        "metadata_consistency",
        "report_completeness",
        "recommended_next_phase_presence",
        "canonical_promotion_eligibility",
        "notification_eligibility",
        "no_execution_availability_unless_contracted",
    ):
        assert invariant in text


def test_duplicates_and_overlap_documented():
    text = _read(KERNEL_DOC)
    assert "Duplicates and Overlap" in text
    assert "phase identity" in text.lower()


# ── Authority table ─────────────────────────────────────────────────────────


def test_authority_table_present():
    text = _read(KERNEL_DOC)
    assert "Kernel Authorities" in text
    for authority in (
        "validate_transition",
        "promote_artifact",
        "certify_notification_transition",
        "reconcile_push_state",
        "resolve_canonical_phase_identity",
        "verify_handoff",
    ):
        assert authority in text


# ── Containment assessment ──────────────────────────────────────────────────


def test_containment_assessment_documented():
    text = _read(KERNEL_DOC)
    assert "Containment Assessment" in text
    lowered = text.lower()
    assert "does not depend on model capability" in lowered
    for model in ("claude", "deepseek", "codex", "glm"):
        assert model in lowered


def test_model_independence_audit_documented():
    text = _read(KERNEL_DOC)
    assert "Model Independence Audit" in text
    assert "zero occurrences" in text.lower() or "zero matches" in text.lower()


# ── Lifecycle connectivity ──────────────────────────────────────────────────


def test_lifecycle_connectivity_documented():
    text = _normalized(KERNEL_DOC)
    assert "Lifecycle Connectivity" in text
    for stage in (
        "Repository Transition", "Repository Transition Validator", "Repository Decision",
        "Canonical Artifact Promotion", "Repository State", "Repository Event",
        "Notification Policy", "Consumers",
    ):
        assert stage in text


def test_wire_diagram_present_and_covers_decision_verdicts():
    text = _read(KERNEL_DOC)
    assert "```mermaid" in text
    assert "flowchart" in text
    mermaid_start = text.index("```mermaid")
    mermaid_end = text.index("```", mermaid_start + 10)
    diagram = text[mermaid_start:mermaid_end]
    for stage in (
        "Model / Human / Automation", "Repository Transition", "Repository Transition Validator",
        "Repository Decision", "Canonical Artifact Promotion", "Repository State",
        "Repository Event", "Notification Policy", "Consumers",
    ):
        assert stage in diagram, f"wire diagram missing stage: {stage}"


# ── Architecture assessment / roadmap ────────────────────────────────────────


def test_architecture_assessment_documented():
    text = _read(KERNEL_DOC)
    assert "Architecture Assessment" in text
    assert "Fundamental" in text
    assert "Implementation detail" in text
    assert "Should never again be duplicated" in text or "should never be duplicated" in text.lower()


def test_future_roadmap_documented():
    for doc in (KERNEL_DOC, PHASE_DOC):
        text = _read(doc)
        assert "Future Roadmap" in text or "Recommended Next Phase" in text
    phase_text = _read(PHASE_DOC)
    assert "115A" in phase_text


def test_no_runtime_implementation_claims():
    for doc in (KERNEL_DOC, PHASE_DOC):
        text = _read(doc)
        for forbidden in ("class RepositoryEvent", "def emit_event", "def emit_repository_event", "EventBus"):
            assert forbidden not in text, f"{doc.name} appears to claim an implementation: {forbidden}"


def test_execution_unavailable_confirmed():
    for doc in (KERNEL_DOC, PHASE_DOC):
        text = _read(doc)
        assert "Execution capability remains unavailable" in text


def test_phase_document_covers_all_eleven_objectives():
    text = _read(PHASE_DOC)
    for n in range(1, 12):
        assert f"Objective {n}" in text, f"missing Objective {n} section"
