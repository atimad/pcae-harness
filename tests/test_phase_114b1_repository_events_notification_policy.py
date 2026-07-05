"""Phase 114B.1: Repository Events & Notification Policy.

Architecture/documentation verification only. This phase adds no runtime
behavior -- these tests verify the frozen documents exist and contain the
required concepts, not any executable behavior.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVENTS_DOC = REPO_ROOT / "docs" / "PCAE_REPOSITORY_EVENTS.md"
POLICY_DOC = REPO_ROOT / "docs" / "PCAE_NOTIFICATION_POLICY.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_114B1_REPOSITORY_EVENTS_NOTIFICATION_POLICY.md"

REQUIRED_EVENT_TAXONOMY = (
    "TransitionAccepted",
    "TransitionRejected",
    "TransitionQuarantined",
    "TransitionRequiresHumanReview",
    "CanonicalPromotionSucceeded",
    "CanonicalPromotionRejected",
    "NotificationDelivered",
    "NotificationFailed",
    "NotificationSkipped",
    "RetryScheduled",
)

FORBIDDEN_IMPLEMENTATION_CLAIMS = (
    "class RepositoryEvent",
    "def emit_event",
    "def emit_repository_event",
    "EventBus",
)


def _read(path: Path) -> str:
    assert path.exists(), f"expected document missing: {path}"
    return path.read_text(encoding="utf-8")


# ── Document existence ────────────────────────────────────────────────────


def test_repository_events_document_exists():
    assert EVENTS_DOC.exists()


def test_notification_policy_document_exists():
    assert POLICY_DOC.exists()


def test_phase_document_exists():
    assert PHASE_DOC.exists()


# ── Four Repository State Kernel primitives ───────────────────────────────


def test_four_primitives_are_defined():
    text = _read(EVENTS_DOC)
    for primitive in ("Repository State", "Repository Transition", "Repository Artifact", "Repository Event"):
        assert primitive in text, f"primitive not defined: {primitive}"
    assert "four" in text.lower()


def test_primitives_answer_distinct_questions():
    text = _read(EVENTS_DOC)
    assert "what exists" in text.lower()
    assert "proposed change" in text.lower() or "what change is proposed" in text.lower()
    assert "durable evidence" in text.lower()
    assert "certified outcome" in text.lower()


# ── Repository Event taxonomy ──────────────────────────────────────────────


def test_event_taxonomy_defined_in_events_doc():
    text = _read(EVENTS_DOC)
    for event in REQUIRED_EVENT_TAXONOMY:
        assert event in text, f"missing event type: {event}"


def test_event_taxonomy_defined_in_phase_doc():
    text = _read(PHASE_DOC)
    for event in REQUIRED_EVENT_TAXONOMY:
        assert event in text, f"missing event type in phase doc: {event}"


def test_events_never_decide():
    text = _read(EVENTS_DOC)
    assert "never decide" in text.lower()


def test_lifecycle_commands_never_notify_directly():
    lowered = " ".join(_read(EVENTS_DOC).split()).lower()
    assert "lifecycle commands never notify" in lowered
    assert "models never notify" in lowered
    assert "agents never notify" in lowered


# ── Event lifecycle ─────────────────────────────────────────────────────────


def test_event_lifecycle_stages_present():
    text = _read(EVENTS_DOC)
    for stage in ("Repository Transition", "Validation", "Promotion", "Repository Event", "Notification Policy", "Consumers"):
        assert stage in text


def test_event_lifecycle_ordering():
    text = _read(EVENTS_DOC)
    section_start = text.index("## Event Lifecycle")
    diagram_start = text.index("```", section_start)
    diagram_end = text.index("```", diagram_start + 3)
    diagram = text[diagram_start:diagram_end]
    positions = [diagram.index(stage) for stage in
                 ("Repository Transition", "Validation", "Promotion", "Repository Event", "Notification Policy", "Consumers")]
    assert positions == sorted(positions), "lifecycle stages must appear in pipeline order"


# ── Model independence ──────────────────────────────────────────────────────


def test_model_independence_documented():
    text = _read(EVENTS_DOC)
    for term in ("model identity", "backend identity", "agent identity", "vendor-specific"):
        assert term in text.lower()


# ── Notification Policy ─────────────────────────────────────────────────────


def test_notification_policy_defined():
    text = _read(POLICY_DOC)
    assert "Notification Policy decides which Repository Events are externally" in text
    assert "Repository Events themselves remain neutral" in text


def test_visibility_rules_defined_for_all_taxonomy_events():
    text = _read(POLICY_DOC)
    for event in REQUIRED_EVENT_TAXONOMY:
        assert event in text, f"visibility rule missing for: {event}"


def test_quarantine_reject_human_review_are_documented_as_visible():
    """The direct answer to the 114B forensic gap: containment outcomes
    must not be silent when operator attention is required."""
    text = _read(POLICY_DOC)
    for event in ("TransitionRejected", "TransitionQuarantined", "TransitionRequiresHumanReview"):
        idx = text.index(event)
        # The visibility table row for each event must mark it visible,
        # not merely mention the event name in passing prose.
        window = text[idx: idx + 200]
        assert "visible" in window.lower(), f"{event} row does not state visibility"


def test_notification_failure_non_circularity_documented():
    text = _read(POLICY_DOC)
    assert "Non-Circularity" in text or "non-circularity" in text.lower()
    assert "NotificationFailed" in text


def test_consumer_model_documented():
    text = _read(POLICY_DOC)
    for consumer in ("Telegram", "REST", "Dashboard", "Web UI", "Audit", "Monitoring", "plugins"):
        assert consumer in text, f"consumer not documented: {consumer}"


def test_consumers_do_not_require_validator_changes():
    text = _read(POLICY_DOC)
    assert "requires a change to" in text
    assert "additive" in text.lower()


# ── Wire diagram ─────────────────────────────────────────────────────────


def test_mermaid_wire_diagram_present():
    text = _read(PHASE_DOC)
    assert "```mermaid" in text
    assert "flowchart" in text


def test_wire_diagram_includes_repository_event_stage():
    text = _read(PHASE_DOC)
    mermaid_start = text.index("```mermaid")
    mermaid_end = text.index("```", mermaid_start + 10)
    diagram = text[mermaid_start:mermaid_end]
    for stage in ("Proposed Transition", "Repository Transition Validator", "Canonical Artifact Promotion",
                  "Certified Repository State", "Repository Event", "Notification Policy", "Consumers"):
        assert stage in diagram, f"wire diagram missing stage: {stage}"


# ── No runtime implementation claims ────────────────────────────────────────


def test_no_runtime_implementation_claims():
    for doc in (EVENTS_DOC, POLICY_DOC, PHASE_DOC):
        text = _read(doc)
        for forbidden in FORBIDDEN_IMPLEMENTATION_CLAIMS:
            assert forbidden not in text, f"{doc.name} appears to claim an implementation: {forbidden}"


def test_events_doc_states_non_goals():
    text = _read(EVENTS_DOC)
    assert "Non-Goals" in text
    assert "does not" in text.lower()


def test_policy_doc_states_non_goals():
    text = _read(POLICY_DOC)
    assert "Non-Goals" in text
    assert "does not" in text.lower()


# ── Execution unavailable / recommended next phase ──────────────────────────


def test_execution_unavailable_confirmed_in_all_docs():
    for doc in (EVENTS_DOC, POLICY_DOC, PHASE_DOC):
        text = _read(doc)
        assert "Execution capability remains unavailable" in text, f"{doc.name} missing execution-unavailable statement"


def test_recommended_next_phase_present():
    text = _read(PHASE_DOC)
    assert "Recommended Next Phase" in text
    assert "114C" in text


def test_phase_doc_status_completed():
    text = _read(PHASE_DOC)
    assert "## Status" in text
    status_idx = text.index("## Status")
    window = text[status_idx: status_idx + 60]
    assert "Completed" in window
