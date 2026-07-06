"""Phase 115B: Repository Evidence Framework Contract Freeze.

Architecture/documentation verification only. These tests verify that the
Evidence contract is frozen in documentation and that no implementation
claims are introduced.
"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DOC = REPO_ROOT / "docs" / "PCAE_REPOSITORY_EVIDENCE_FRAMEWORK.md"
PROVIDER_DOC = REPO_ROOT / "docs" / "PCAE_EVIDENCE_PROVIDER_CONTRACT.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_115B_REPOSITORY_EVIDENCE_CONTRACT_FREEZE.md"


def _read(path: Path) -> str:
    assert path.exists(), f"expected document missing: {path}"
    return path.read_text(encoding="utf-8")


def test_evidence_contract_documented():
    text = _read(EVIDENCE_DOC)
    assert "Repository Evidence Framework" in text
    assert "Evidence informs Repository Decisions" in text
    assert "does not become a Repository State Kernel primitive" in text


def test_required_evidence_fields_documented():
    text = _read(EVIDENCE_DOC)
    for field in (
        "evidence_id",
        "source",
        "category",
        "producer",
        "timestamp_utc",
        "freshness",
        "confidence",
        "determinism",
        "scope",
        "references",
        "observed_value",
        "expected_value",
        "explanation",
        "limitations",
    ):
        assert f"`{field}`" in text


def test_evidence_identity_documented():
    text = _read(EVIDENCE_DOC)
    assert "stable within one evaluation" in text
    assert "not global permanent repository IDs" in text
    assert "persisted inside a Repository Artifact" in text


def test_evidence_categories_documented():
    text = _read(EVIDENCE_DOC)
    for category in (
        "git",
        "task",
        "phase",
        "report",
        "metadata",
        "architecture",
        "runtime",
        "push_state",
        "notification",
        "governance",
        "test_result",
        "security",
        "documentation",
        "ai_review",
        "unknown",
    ):
        assert f"`{category}`" in text


def test_determinism_levels_documented():
    text = _read(EVIDENCE_DOC)
    for level in (
        "deterministic",
        "reproducible_external",
        "probabilistic",
        "human_asserted",
        "unknown",
    ):
        assert f"`{level}`" in text
    assert "Git evidence" in text or "Git" in text
    assert "SLM/LLM review" in text


def test_confidence_semantics_documented():
    text = _read(EVIDENCE_DOC)
    for level in ("high", "medium", "low", "unknown"):
        assert f"`{level}`" in text
    assert "Confidence must not override hard invariants" in text
    assert "Probabilistic evidence may never alone authorize canonical mutation" in text


def test_freshness_semantics_documented():
    text = _read(EVIDENCE_DOC)
    for level in ("current", "stale", "expired", "unknown"):
        assert f"`{level}`" in text
    assert "Stale evidence is preserved and labelled" in text
    assert "never silently discarded" in text


def test_provider_contract_documented():
    text = _read(PROVIDER_DOC)
    for phrase in (
        "collects evidence",
        "never decide",
        "declares determinism class",
        "declares evidence categories produced",
        "declares required repository inputs",
        "never mutates repository state",
        "never bypasses the Repository Transition Validator",
    ):
        assert phrase in text


def test_conflict_semantics_documented():
    for doc in (EVIDENCE_DOC, PROVIDER_DOC):
        text = _read(doc)
        assert "preserve" in text
        assert "conflict" in text.lower()
        assert "centrally" in text


def test_explanation_references_documented():
    text = _read(EVIDENCE_DOC)
    assert "Decision explanations must be able to cite Evidence IDs" in text
    assert "E-git-001" in text
    assert "E-metadata-002" in text
    assert "phase_identity_consistency" in text


def test_persistence_boundary_documented():
    text = _read(EVIDENCE_DOC)
    assert "Evidence is transient during evaluation" in text
    assert "Raw evidence persistence is future work" in text
    assert "not implemented by Phase 115B" in text


def test_slm_ai_boundary_documented():
    text = _read(EVIDENCE_DOC)
    for phrase in (
        "advisory only",
        "probabilistic by default",
        "never sole authority for Accept",
        "may trigger Requires Human Review",
        "may suggest repairs",
        "labelled model-produced",
    ):
        assert phrase in text


def test_phase_report_covers_required_sections():
    text = _read(PHASE_DOC)
    for section in (
        "Evidence Contract Summary",
        "Evidence Identity",
        "Evidence Categories",
        "Determinism Model",
        "Confidence Model",
        "Freshness Model",
        "Evidence Provider Contract Summary",
        "Conflict Semantics",
        "Explanation Reference Model",
        "Persistence Boundary",
        "SLM / AI Evidence Boundary",
    ):
        assert section in text


def test_no_runtime_implementation_claims():
    for doc in (EVIDENCE_DOC, PROVIDER_DOC, PHASE_DOC):
        text = _read(doc)
        for forbidden in (
            "class Evidence",
            "def collect_evidence",
            "def persist_evidence",
            "def register_provider",
            "RepositoryTransitionValidator changed",
            "Telegram inbound implemented",
            "REST endpoint",
            "Dashboard implemented",
        ):
            assert forbidden not in text, f"{doc.name} appears to claim implementation: {forbidden}"


def test_execution_unavailable_confirmed():
    for doc in (EVIDENCE_DOC, PROVIDER_DOC, PHASE_DOC):
        assert "Execution capability remains unavailable" in _read(doc)


def test_recommended_next_phase_exists():
    assert "115C — Repository Evidence Framework Prototype" in _read(PHASE_DOC)
