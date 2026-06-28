"""Tests for enforcement audit event model (89L, simulation-only)."""

from __future__ import annotations

import json

import pytest

from pcae.core.enforcement_audit import (
    SCHEMA_VERSION,
    AuditApproval,
    AuditCommand,
    AuditDecision,
    AuditDecisionContext,
    AuditEvidence,
    AuditHardBlock,
    AuditIntegrity,
    AuditOperator,
    AuditOutcome,
    AuditRepository,
    AuditRisk,
    AuditEvent,
    EVENT_TYPE_ENFORCEMENT_BLOCKED,
    EVENT_TYPE_ENFORCEMENT_ALLOWED,
    EVENT_TYPE_ENFORCEMENT_GATED_REVIEW,
    EVENT_TYPE_RISK_ACCEPTED,
    EVENT_TYPE_APPROVAL_GRANTED,
    make_audit_event,
    make_enforcement_blocked_event,
    make_enforcement_allowed_event,
    make_human_review_event,
    make_hard_block_event,
    make_accepted_risk_event,
    is_valid_event_type,
    validate_audit_event,
    validate_audit_event_dict,
)


# ---------------------------------------------------------------------------
# Audit event construction
# ---------------------------------------------------------------------------

class TestAuditEventConstruction:
    """Tests for basic audit event construction."""

    def test_construct_minimal_event(self):
        event = make_audit_event(EVENT_TYPE_ENFORCEMENT_BLOCKED)
        assert event.event_id.startswith("evt-")
        assert event.event_type == EVENT_TYPE_ENFORCEMENT_BLOCKED
        assert event.schema_version == SCHEMA_VERSION
        assert event.timestamp
        assert event.no_execution is True
        assert event.no_enforcement is True

    def test_construct_event_with_custom_id_and_timestamp(self):
        event = make_audit_event(
            EVENT_TYPE_ENFORCEMENT_ALLOWED,
            event_id="evt-test-12345678",
            timestamp="2026-06-28T00:00:00Z",
        )
        assert event.event_id == "evt-test-12345678"
        assert event.timestamp == "2026-06-28T00:00:00Z"

    def test_construct_event_rejects_invalid_type(self):
        with pytest.raises(ValueError, match="Invalid event_type"):
            make_audit_event("invalid.type")

    def test_construct_event_with_all_sub_objects(self):
        event = make_audit_event(
            EVENT_TYPE_ENFORCEMENT_BLOCKED,
            operator=AuditOperator(user="tester", agent_id="claude-local"),
            command=AuditCommand(
                text_hash="abc123", text_redacted="<redacted>",
            ),
            decision=AuditDecision(hard_block=True),
            outcome=AuditOutcome(action="blocked", enforced=False),
            repository=AuditRepository(root="/repo", branch="main"),
            evidence=AuditEvidence(health_passed=True, check_passed=True),
            hard_block=AuditHardBlock(
                reason="force_push", source="shell_gate",
            ),
        )
        assert event.operator is not None
        assert event.operator.user == "tester"
        assert event.command is not None
        assert event.command.text_hash == "abc123"
        assert event.hard_block is not None
        assert event.hard_block.reason == "force_push"


# ---------------------------------------------------------------------------
# JSON serialization
# ---------------------------------------------------------------------------

class TestAuditEventSerialization:
    """Tests for JSON-safe dict serialization."""

    def test_to_dict_minimal(self):
        event = make_audit_event(
            EVENT_TYPE_ENFORCEMENT_BLOCKED,
            event_id="evt-test-00000001",
            timestamp="2026-06-28T00:00:00Z",
        )
        d = event.to_dict()
        assert d["event_id"] == "evt-test-00000001"
        assert d["event_type"] == EVENT_TYPE_ENFORCEMENT_BLOCKED
        assert d["schema_version"] == SCHEMA_VERSION
        assert d["no_execution"] is True
        assert d["no_enforcement"] is True

    def test_to_dict_is_json_serializable(self):
        event = make_enforcement_blocked_event(
            operator=AuditOperator(user="tester"),
            command=AuditCommand(
                text_hash="abc123", text_redacted="<redacted>",
            ),
            hard_block=AuditHardBlock(
                reason="force_push", source="shell_gate",
            ),
            repository=AuditRepository(root="/repo", branch="main"),
            evidence=AuditEvidence(health_passed=True, check_passed=True),
        )
        d = event.to_dict()
        json_str = json.dumps(d, sort_keys=True)
        parsed = json.loads(json_str)
        assert parsed["event_type"] == EVENT_TYPE_ENFORCEMENT_BLOCKED
        assert parsed["no_execution"] is True
        assert parsed["no_enforcement"] is True

    def test_to_dict_omits_none_sub_objects(self):
        event = make_audit_event(
            EVENT_TYPE_ENFORCEMENT_ALLOWED,
            event_id="evt-test-00000002",
            timestamp="2026-06-28T00:00:00Z",
        )
        d = event.to_dict()
        assert "operator" not in d
        assert "command" not in d
        assert "decision" not in d

    def test_to_dict_includes_present_sub_objects(self):
        event = make_audit_event(
            EVENT_TYPE_ENFORCEMENT_BLOCKED,
            event_id="evt-test-00000003",
            timestamp="2026-06-28T00:00:00Z",
            operator=AuditOperator(user="tester"),
            command=AuditCommand(text_hash="abc", text_redacted="***"),
            decision=AuditDecision(),
            outcome=AuditOutcome(action="blocked", enforced=False),
            repository=AuditRepository(root="/repo"),
            evidence=AuditEvidence(),
            integrity=AuditIntegrity(),
            hard_block=AuditHardBlock(reason="test", source="test"),
        )
        d = event.to_dict()
        assert "operator" in d
        assert "command" in d
        assert "decision" in d
        assert "outcome" in d
        assert "repository" in d
        assert "evidence" in d
        assert "integrity" in d
        assert "hard_block" in d


# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------

class TestRequiredFields:
    """Tests for required field validation."""

    def test_validate_empty_event_id(self):
        event = make_audit_event(
            EVENT_TYPE_ENFORCEMENT_BLOCKED,
            event_id="evt-valid-id",
        )
        object.__setattr__(event, "event_id", "")
        issues = validate_audit_event(event)
        assert any("event_id is empty" in i for i in issues)

    def test_validate_empty_timestamp(self):
        event = make_audit_event(
            EVENT_TYPE_ENFORCEMENT_BLOCKED,
            timestamp="2026-06-28T00:00:00Z",
        )
        object.__setattr__(event, "timestamp", "")
        issues = validate_audit_event(event)
        assert any("timestamp is empty" in i for i in issues)

    def test_validate_dict_missing_required_keys(self):
        issues = validate_audit_event_dict({})
        assert any("event_id" in i for i in issues)
        assert any("event_type" in i for i in issues)
        assert any("timestamp" in i for i in issues)
        assert any("schema_version" in i for i in issues)


# ---------------------------------------------------------------------------
# Schema version
# ---------------------------------------------------------------------------

class TestSchemaVersion:
    """Tests for schema version validation."""

    def test_default_schema_version(self):
        event = make_audit_event(EVENT_TYPE_ENFORCEMENT_BLOCKED)
        assert event.schema_version == SCHEMA_VERSION

    def test_validate_wrong_schema_version(self):
        event = make_audit_event(
            EVENT_TYPE_ENFORCEMENT_BLOCKED,
            event_id="evt-test-sv",
        )
        # Bypass frozen dataclass to set wrong version
        object.__setattr__(event, "schema_version", "0.9")
        issues = validate_audit_event(event)
        assert any("schema_version" in i for i in issues)

    def test_validate_dict_wrong_schema_version(self):
        d = {
            "event_id": "evt-1",
            "event_type": EVENT_TYPE_ENFORCEMENT_BLOCKED,
            "timestamp": "2026-01-01T00:00:00Z",
            "schema_version": "0.9",
        }
        issues = validate_audit_event_dict(d)
        assert any("schema_version" in i for i in issues)


# ---------------------------------------------------------------------------
# No-execution/no-enforcement invariant flags
# ---------------------------------------------------------------------------

class TestInvariantFlags:
    """Tests for no_execution and no_enforcement invariants."""

    def test_no_execution_is_always_true(self):
        for event_type_fn in [
            make_enforcement_blocked_event,
            make_enforcement_allowed_event,
            make_human_review_event,
        ]:
            event = event_type_fn()
            assert event.no_execution is True, f"Failed for {event.event_type}"

    def test_no_enforcement_is_always_true(self):
        for event_type_fn in [
            make_enforcement_blocked_event,
            make_enforcement_allowed_event,
            make_human_review_event,
        ]:
            event = event_type_fn()
            assert event.no_enforcement is True, f"Failed for {event.event_type}"

    def test_validate_flags_no_execution_false_is_invalid(self):
        event = make_audit_event(EVENT_TYPE_ENFORCEMENT_BLOCKED)
        object.__setattr__(event, "no_execution", False)
        issues = validate_audit_event(event)
        assert any("no_execution must be True" in i for i in issues)

    def test_validate_flags_no_enforcement_false_is_invalid(self):
        event = make_audit_event(EVENT_TYPE_ENFORCEMENT_BLOCKED)
        object.__setattr__(event, "no_enforcement", False)
        issues = validate_audit_event(event)
        assert any("no_enforcement must be True" in i for i in issues)

    def test_validate_dict_no_execution_false(self):
        d = {
            "event_id": "evt-1",
            "event_type": EVENT_TYPE_ENFORCEMENT_BLOCKED,
            "timestamp": "2026-01-01T00:00:00Z",
            "schema_version": SCHEMA_VERSION,
            "no_execution": False,
        }
        issues = validate_audit_event_dict(d)
        assert any("no_execution must be True" in i for i in issues)

    def test_validate_dict_no_enforcement_false(self):
        d = {
            "event_id": "evt-1",
            "event_type": EVENT_TYPE_ENFORCEMENT_BLOCKED,
            "timestamp": "2026-01-01T00:00:00Z",
            "schema_version": SCHEMA_VERSION,
            "no_enforcement": False,
        }
        issues = validate_audit_event_dict(d)
        assert any("no_enforcement must be True" in i for i in issues)


# ---------------------------------------------------------------------------
# Hard-block event representation
# ---------------------------------------------------------------------------

class TestHardBlockEvent:
    """Tests for hard-block event construction and validation."""

    def test_hard_block_event_has_correct_type(self):
        event = make_hard_block_event(reason="force_push")
        assert event.event_type == EVENT_TYPE_ENFORCEMENT_BLOCKED
        assert event.hard_block is not None
        assert event.hard_block.reason == "force_push"
        assert event.hard_block.overridable is False
        assert event.hard_block.overridden is False
        assert event.hard_block.permanent is True

    def test_hard_block_event_outcome_is_blocked(self):
        event = make_hard_block_event(reason="force_push")
        assert event.outcome is not None
        assert event.outcome.action == "blocked"
        assert event.outcome.enforced is False

    def test_hard_block_event_decision_is_block(self):
        event = make_hard_block_event(reason="force_push")
        assert event.decision is not None
        assert event.decision.hard_block is True

    def test_hard_block_is_not_overridable(self):
        event = make_hard_block_event(reason="force_push")
        issues = validate_audit_event(event)
        # Should be clean — hard_block values are correct
        hard_block_issues = [i for i in issues if "hard_block" in i]
        assert len(hard_block_issues) == 0

    def test_hard_block_invalid_if_overridable_is_true(self):
        event = make_hard_block_event(reason="force_push")
        object.__setattr__(event.hard_block, "overridable", True)
        issues = validate_audit_event(event)
        assert any("overridable must be False" in i for i in issues)

    def test_hard_block_invalid_if_overridden_is_true(self):
        event = make_hard_block_event(reason="force_push")
        object.__setattr__(event.hard_block, "overridden", True)
        issues = validate_audit_event(event)
        assert any("overridden must be False" in i for i in issues)

    def test_hard_block_invalid_if_permanent_is_false(self):
        event = make_hard_block_event(reason="force_push")
        object.__setattr__(event.hard_block, "permanent", False)
        issues = validate_audit_event(event)
        assert any("permanent must be True" in i for i in issues)

    def test_hard_block_dict_validation_catches_overridable(self):
        d = {
            "event_id": "evt-1",
            "event_type": EVENT_TYPE_ENFORCEMENT_BLOCKED,
            "timestamp": "2026-01-01T00:00:00Z",
            "schema_version": SCHEMA_VERSION,
            "hard_block": {
                "reason": "force_push",
                "source": "shell_gate",
                "overridable": True,
                "overridden": False,
                "permanent": True,
            },
        }
        issues = validate_audit_event_dict(d)
        assert any("overridable" in i for i in issues)


# ---------------------------------------------------------------------------
# Human-review event representation
# ---------------------------------------------------------------------------

class TestHumanReviewEvent:
    """Tests for human-review (gated_review) event."""

    def test_gated_review_event_type(self):
        event = make_human_review_event()
        assert event.event_type == EVENT_TYPE_ENFORCEMENT_GATED_REVIEW

    def test_gated_review_not_enforced(self):
        event = make_human_review_event()
        assert event.outcome is not None
        assert event.outcome.enforced is False
        assert event.outcome.action == "gated_review"

    def test_gated_review_decision_is_not_hard_block(self):
        event = make_human_review_event()
        assert event.decision is not None
        assert event.decision.hard_block is False

    def test_gated_review_has_governed_alternative(self):
        event = make_human_review_event()
        assert event.outcome is not None
        assert "human review" in event.outcome.governed_alternative.lower()


# ---------------------------------------------------------------------------
# Accepted-risk event representation without override
# ---------------------------------------------------------------------------

class TestAcceptedRiskEvent:
    """Tests for accepted-risk event (never overrides hard blocks)."""

    def test_accepted_risk_event_type(self):
        event = make_accepted_risk_event(
            accepted_by="tester",
            risk_level="medium",
            risk_description="Test risk",
        )
        assert event.event_type == EVENT_TYPE_RISK_ACCEPTED

    def test_accepted_risk_has_risk_detail(self):
        event = make_accepted_risk_event(
            accepted_by="tester",
            risk_level="medium",
            risk_description="Running test command without preflight",
        )
        assert event.risk is not None
        assert event.risk.accepted_by == "tester"
        assert event.risk.risk_level == "medium"

    def test_accepted_risk_hard_block_override_always_false(self):
        event = make_accepted_risk_event(
            accepted_by="tester",
            risk_level="low",
            risk_description="Test",
            hard_block_override=True,  # Attempt to override — constructor forces False
        )
        assert event.risk is not None
        assert event.risk.hard_block_override is False

    def test_accepted_risk_validation_rejects_hard_block_override(self):
        event = make_accepted_risk_event(
            accepted_by="tester",
            risk_level="medium",
            risk_description="Test",
        )
        object.__setattr__(event.risk, "hard_block_override", True)
        issues = validate_audit_event(event)
        assert any("hard_block_override" in i for i in issues)

    def test_accepted_risk_has_decision_context(self):
        event = make_accepted_risk_event(
            accepted_by="tester",
            risk_level="high",
            risk_description="Test",
            original_decision="would_require_human_review",
        )
        assert event.decision_context is not None
        assert event.decision_context.original_decision == "would_require_human_review"
        assert event.decision_context.hard_block_present is False

    def test_accepted_risk_serialization_preserves_fields(self):
        event = make_accepted_risk_event(
            accepted_by="tester",
            risk_level="medium",
            risk_description="Accepting test risk",
            scope=("test_file.py",),
            expires_at="2026-06-28T01:00:00Z",
        )
        d = event.to_dict()
        assert d["risk"]["accepted_by"] == "tester"
        assert d["risk"]["risk_level"] == "medium"
        assert d["risk"]["hard_block_override"] is False
        assert "test_file.py" in d["risk"]["scope"]


# ---------------------------------------------------------------------------
# Redaction field presence
# ---------------------------------------------------------------------------

class TestRedactionFields:
    """Tests for command text redaction in audit events."""

    def test_command_always_uses_text_redacted(self):
        cmd = AuditCommand(
            text_hash="sha256:abc123",
            text_redacted="<REDACTED: shell command>",
        )
        d = cmd.to_dict()
        assert "text_redacted" in d
        assert d["text_redacted"].startswith("<REDACTED")

    def test_command_does_not_expose_plaintext_field(self):
        cmd = AuditCommand(
            text_hash="sha256:abc123",
            text_redacted="<REDACTED>",
        )
        d = cmd.to_dict()
        # text_redacted must be present, but no 'text' or 'raw' field
        assert "text" not in d
        assert "raw" not in d
        assert "text_redacted" in d

    def test_event_with_command_includes_redacted_field(self):
        event = make_enforcement_blocked_event(
            command=AuditCommand(
                text_hash="sha256:deadbeef",
                text_redacted="<REDACTED: dangerous command>",
            ),
        )
        d = event.to_dict()
        assert d["command"]["text_redacted"].startswith("<REDACTED")


# ---------------------------------------------------------------------------
# Invalid event rejection
# ---------------------------------------------------------------------------

class TestInvalidEventRejection:
    """Tests for rejection of invalid events."""

    def test_reject_unknown_event_type(self):
        with pytest.raises(ValueError, match="Invalid event_type"):
            make_audit_event("not.a.valid.type")

    def test_is_valid_event_type_returns_false_for_unknown(self):
        assert is_valid_event_type("invalid") is False

    def test_is_valid_event_type_returns_true_for_known(self):
        assert is_valid_event_type(EVENT_TYPE_ENFORCEMENT_BLOCKED) is True
        assert is_valid_event_type(EVENT_TYPE_APPROVAL_GRANTED) is True

    def test_validate_dict_rejects_unknown_event_type(self):
        d = {
            "event_id": "evt-1",
            "event_type": "bad.type",
            "timestamp": "2026-01-01T00:00:00Z",
            "schema_version": SCHEMA_VERSION,
        }
        issues = validate_audit_event_dict(d)
        assert any("unknown event_type" in i for i in issues)


# ---------------------------------------------------------------------------
# Approval is not authorization
# ---------------------------------------------------------------------------

class TestApprovalNotAuthorization:
    """Tests that approval records are never execution authorization."""

    def test_approval_record_construction(self):
        approval = AuditApproval(
            approved_by="operator",
            approved_action="Run tests",
            approved_command_hash="sha256:abc",
        )
        assert approval.approved_by == "operator"
        assert approval.revocable is True

    def test_approval_record_to_dict(self):
        approval = AuditApproval(
            approved_by="operator",
            approved_action="Deploy to staging",
            approved_command_hash="sha256:def",
            scope=("src/",),
            expires_at="2026-06-28T02:00:00Z",
        )
        d = approval.to_dict()
        assert d["approved_by"] == "operator"
        assert d["revocable"] is True
        assert "src/" in d["scope"]

    def test_approval_event_is_not_authorization(self):
        event = make_audit_event(
            EVENT_TYPE_APPROVAL_GRANTED,
            approval=AuditApproval(
                approved_by="operator",
                approved_action="Test action",
                approved_command_hash="sha256:123",
            ),
            outcome=AuditOutcome(action="gated_review", enforced=False),
        )
        issues = validate_audit_event(event)
        # Should be clean — enforced is False
        approval_issues = [i for i in issues if "approval" in i.lower()]
        assert len(approval_issues) == 0

    def test_approval_event_with_enforcement_is_invalid(self):
        event = make_audit_event(
            EVENT_TYPE_APPROVAL_GRANTED,
            approval=AuditApproval(
                approved_by="operator",
                approved_action="Test action",
                approved_command_hash="sha256:123",
            ),
            outcome=AuditOutcome(action="allowed", enforced=True),
        )
        issues = validate_audit_event(event)
        assert any("approval is not authorization" in i for i in issues)
