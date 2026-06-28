"""Tests for enforcement approval and accepted-risk policy model (89M, simulation-only)."""

from __future__ import annotations

import json

import pytest

from pcae.core.enforcement_approval import (
    SCHEMA_VERSION,
    RISK_LEVEL_LOW,
    RISK_LEVEL_MEDIUM,
    RISK_LEVEL_HIGH,
    RISK_LEVEL_CRITICAL,
    SCOPE_SINGLE_COMMAND,
    SCOPE_COMMAND_CATEGORY,
    SCOPE_FILE_SET,
    SCOPE_TASK_DURATION,
    SCOPE_SESSION,
    CLASSIFICATION_APPROVAL_NOT_RELEVANT,
    CLASSIFICATION_APPROVAL_REQUIRED,
    CLASSIFICATION_APPROVAL_PRESENT_BUT_NOT_AUTHORIZATION,
    CLASSIFICATION_ACCEPTED_RISK_NOT_RELEVANT,
    CLASSIFICATION_ACCEPTED_RISK_RELEVANT_BUT_NOT_OVERRIDE,
    CLASSIFICATION_HARD_BLOCK_NON_OVERRIDABLE,
    ApprovalRecord,
    AcceptedRiskRecord,
    make_approval_record,
    make_accepted_risk_record,
    revoke_approval,
    revoke_accepted_risk,
    classify_hard_block,
    classify_approval,
    classify_accepted_risk,
    is_valid_risk_level,
    is_valid_scope,
    validate_approval_record,
    validate_accepted_risk_record,
    validate_approval_record_dict,
    validate_accepted_risk_record_dict,
)


# ---------------------------------------------------------------------------
# Approval record construction
# ---------------------------------------------------------------------------

class TestApprovalRecordConstruction:
    """Tests for approval record construction."""

    def test_construct_basic_approval(self):
        record = make_approval_record(
            approved_by="operator",
            approved_action="Run tests",
            approved_command_hash="sha256:abc",
        )
        assert record.approval_id.startswith("appr-")
        assert record.approved_by == "operator"
        assert record.scope == SCOPE_SINGLE_COMMAND
        assert record.is_authorization is False
        assert record.no_enforcement is True
        assert record.revocable is True

    def test_construct_with_custom_id_and_timestamps(self):
        record = make_approval_record(
            approved_by="operator",
            approved_action="Deploy",
            approved_command_hash="sha256:def",
            approval_id="appr-custom-1",
            granted_at="2026-06-28T10:00:00Z",
            expires_at="2026-06-28T11:00:00Z",
        )
        assert record.approval_id == "appr-custom-1"
        assert record.granted_at == "2026-06-28T10:00:00Z"
        assert record.expires_at == "2026-06-28T11:00:00Z"

    def test_construct_with_specific_scope(self):
        for scope in [SCOPE_SINGLE_COMMAND, SCOPE_FILE_SET, SCOPE_SESSION]:
            record = make_approval_record(
                approved_by="op",
                approved_action="test",
                approved_command_hash="sha256:x",
                scope=scope,
            )
            assert record.scope == scope

    def test_reject_invalid_scope(self):
        with pytest.raises(ValueError, match="Invalid scope"):
            make_approval_record(
                approved_by="op",
                approved_action="test",
                approved_command_hash="sha256:x",
                scope="invalid_scope",
            )

    def test_approval_is_not_authorization(self):
        record = make_approval_record(
            approved_by="operator",
            approved_action="Sensitive action",
            approved_command_hash="sha256:abc",
        )
        assert record.is_authorization is False

    def test_approval_with_hard_block_still_not_authorization(self):
        record = make_approval_record(
            approved_by="operator",
            approved_action="Blocked action",
            approved_command_hash="sha256:abc",
            hard_block_present=True,
        )
        assert record.is_authorization is False
        assert record.hard_block_present is True


# ---------------------------------------------------------------------------
# Accepted-risk record construction
# ---------------------------------------------------------------------------

class TestAcceptedRiskRecordConstruction:
    """Tests for accepted-risk record construction."""

    def test_construct_basic_risk(self):
        record = make_accepted_risk_record(
            accepted_by="operator",
            risk_level=RISK_LEVEL_MEDIUM,
            risk_description="Test risk",
        )
        assert record.risk_id.startswith("risk-")
        assert record.accepted_by == "operator"
        assert record.risk_level == RISK_LEVEL_MEDIUM
        assert record.hard_block_override is False
        assert record.is_authorization is False
        assert record.no_enforcement is True

    def test_construct_all_risk_levels(self):
        for level in [RISK_LEVEL_LOW, RISK_LEVEL_MEDIUM, RISK_LEVEL_HIGH, RISK_LEVEL_CRITICAL]:
            record = make_accepted_risk_record(
                accepted_by="op",
                risk_level=level,
                risk_description=f"Risk at {level}",
            )
            assert record.risk_level == level
            assert record.hard_block_override is False

    def test_reject_invalid_risk_level(self):
        with pytest.raises(ValueError, match="Invalid risk_level"):
            make_accepted_risk_record(
                accepted_by="op",
                risk_level="extreme",
                risk_description="Bad level",
            )

    def test_accepted_risk_hard_block_override_always_false(self):
        record = make_accepted_risk_record(
            accepted_by="op",
            risk_level=RISK_LEVEL_HIGH,
            risk_description="High risk action",
        )
        assert record.hard_block_override is False


# ---------------------------------------------------------------------------
# Expiration fields
# ---------------------------------------------------------------------------

class TestExpirationFields:
    """Tests for approval and risk expiration behavior."""

    def test_approval_is_expired_with_past_expires_at(self):
        record = make_approval_record(
            approved_by="op",
            approved_action="test",
            approved_command_hash="sha256:x",
            expires_at="2020-01-01T00:00:00Z",
        )
        assert record.is_expired() is True

    def test_approval_is_valid_with_future_expires_at(self):
        record = make_approval_record(
            approved_by="op",
            approved_action="test",
            approved_command_hash="sha256:x",
            expires_at="2099-12-31T23:59:59Z",
        )
        assert record.is_valid() is True

    def test_approval_without_expires_at_is_expired(self):
        record = make_approval_record(
            approved_by="op",
            approved_action="test",
            approved_command_hash="sha256:x",
            expires_at="",  # no expiry set
        )
        assert record.is_expired() is True
        assert record.is_valid() is False

    def test_accepted_risk_expiration(self):
        record = make_accepted_risk_record(
            accepted_by="op",
            risk_level=RISK_LEVEL_LOW,
            risk_description="Test",
            expires_at="2020-01-01T00:00:00Z",
        )
        assert record.is_expired() is True

    def test_accepted_risk_future_expiry(self):
        record = make_accepted_risk_record(
            accepted_by="op",
            risk_level=RISK_LEVEL_LOW,
            risk_description="Test",
            expires_at="2099-12-31T23:59:59Z",
        )
        assert record.is_valid() is True


# ---------------------------------------------------------------------------
# Revocation fields
# ---------------------------------------------------------------------------

class TestRevocationFields:
    """Tests for revocation behavior."""

    def test_revoke_approval(self):
        record = make_approval_record(
            approved_by="op",
            approved_action="test",
            approved_command_hash="sha256:x",
            expires_at="2099-12-31T23:59:59Z",
        )
        revoked = revoke_approval(record)
        assert revoked.revoked_at is not None
        assert revoked.is_revoked() is True
        assert revoked.is_valid() is False
        # Original should be unchanged (frozen)
        assert record.revoked_at is None

    def test_revoke_accepted_risk(self):
        record = make_accepted_risk_record(
            accepted_by="op",
            risk_level=RISK_LEVEL_MEDIUM,
            risk_description="Test",
            expires_at="2099-12-31T23:59:59Z",
        )
        revoked = revoke_accepted_risk(record)
        assert revoked.revoked_at is not None
        assert revoked.is_revoked() is True
        assert revoked.is_valid() is False

    def test_revoked_approval_is_expired(self):
        record = make_approval_record(
            approved_by="op",
            approved_action="test",
            approved_command_hash="sha256:x",
            expires_at="2099-12-31T23:59:59Z",
        )
        revoked = revoke_approval(record)
        assert revoked.is_expired() is True

    def test_revoked_risk_is_expired(self):
        record = make_accepted_risk_record(
            accepted_by="op",
            risk_level=RISK_LEVEL_MEDIUM,
            risk_description="Test",
            expires_at="2099-12-31T23:59:59Z",
        )
        revoked = revoke_accepted_risk(record)
        assert revoked.is_expired() is True

    def test_revoked_approval_preserves_no_enforcement(self):
        record = make_approval_record(
            approved_by="op",
            approved_action="test",
            approved_command_hash="sha256:x",
        )
        revoked = revoke_approval(record)
        assert revoked.no_enforcement is True
        assert revoked.is_authorization is False


# ---------------------------------------------------------------------------
# Scope mismatch
# ---------------------------------------------------------------------------

class TestScopeMismatch:
    """Tests for scope handling."""

    def test_different_scopes_have_different_default_expiries(self):
        expiries = set()
        for scope in [SCOPE_SINGLE_COMMAND, SCOPE_COMMAND_CATEGORY, SCOPE_FILE_SET]:
            from pcae.core.enforcement_approval import DEFAULT_EXPIRY_MINUTES
            expiries.add(DEFAULT_EXPIRY_MINUTES[scope])
        # Each scope should have a distinct default expiry
        assert len(expiries) >= 2

    def test_is_valid_scope(self):
        assert is_valid_scope(SCOPE_SINGLE_COMMAND) is True
        assert is_valid_scope(SCOPE_SESSION) is True
        assert is_valid_scope("not_a_scope") is False

    def test_is_valid_risk_level(self):
        assert is_valid_risk_level(RISK_LEVEL_LOW) is True
        assert is_valid_risk_level(RISK_LEVEL_CRITICAL) is True
        assert is_valid_risk_level("not_a_level") is False


# ---------------------------------------------------------------------------
# Hard-block cannot be approved
# ---------------------------------------------------------------------------

class TestHardBlockNotApprovable:
    """Tests that hard blocks cannot be overridden by approval."""

    def test_classify_hard_block_returns_non_overridable(self):
        result = classify_hard_block(hard_block_present=True)
        assert result == CLASSIFICATION_HARD_BLOCK_NON_OVERRIDABLE

    def test_classify_hard_block_not_present_returns_not_relevant(self):
        result = classify_hard_block(hard_block_present=False)
        assert result == CLASSIFICATION_APPROVAL_NOT_RELEVANT

    def test_approval_with_hard_block_classifies_as_non_overridable(self):
        record = make_approval_record(
            approved_by="op",
            approved_action="test",
            approved_command_hash="sha256:x",
            hard_block_present=True,
        )
        result = classify_approval(record, hard_block_present=True)
        assert result == CLASSIFICATION_HARD_BLOCK_NON_OVERRIDABLE

    def test_approval_with_hard_block_in_record_classifies_non_overridable(self):
        record = make_approval_record(
            approved_by="op",
            approved_action="test",
            approved_command_hash="sha256:x",
            hard_block_present=True,
        )
        result = classify_approval(record)
        assert result == CLASSIFICATION_HARD_BLOCK_NON_OVERRIDABLE

    def test_approval_without_hard_block_classifies_as_present_but_not_auth(self):
        record = make_approval_record(
            approved_by="op",
            approved_action="test",
            approved_command_hash="sha256:x",
            expires_at="2099-12-31T23:59:59Z",
        )
        result = classify_approval(record)
        assert result == CLASSIFICATION_APPROVAL_PRESENT_BUT_NOT_AUTHORIZATION

    def test_no_approval_classifies_as_required(self):
        result = classify_approval(None)
        assert result == CLASSIFICATION_APPROVAL_REQUIRED


# ---------------------------------------------------------------------------
# Accepted risk cannot override hard block
# ---------------------------------------------------------------------------

class TestAcceptedRiskNotOverride:
    """Tests that accepted risk cannot override hard blocks."""

    def test_accepted_risk_with_hard_block_non_overridable(self):
        result = classify_accepted_risk(None, hard_block_present=True)
        assert result == CLASSIFICATION_HARD_BLOCK_NON_OVERRIDABLE

    def test_accepted_risk_relevant_but_not_override(self):
        record = make_accepted_risk_record(
            accepted_by="op",
            risk_level=RISK_LEVEL_MEDIUM,
            risk_description="Test",
        )
        result = classify_accepted_risk(record)
        assert result == CLASSIFICATION_ACCEPTED_RISK_RELEVANT_BUT_NOT_OVERRIDE

    def test_no_accepted_risk_not_relevant(self):
        result = classify_accepted_risk(None)
        assert result == CLASSIFICATION_ACCEPTED_RISK_NOT_RELEVANT

    def test_accepted_risk_never_has_hard_block_override(self):
        record = make_accepted_risk_record(
            accepted_by="op",
            risk_level=RISK_LEVEL_CRITICAL,
            risk_description="Critical risk — still no override",
        )
        assert record.hard_block_override is False

    def test_accepted_risk_with_hard_block_present_always_non_overridable(self):
        record = make_accepted_risk_record(
            accepted_by="op",
            risk_level=RISK_LEVEL_HIGH,
            risk_description="High risk",
        )
        result = classify_accepted_risk(record, hard_block_present=True)
        assert result == CLASSIFICATION_HARD_BLOCK_NON_OVERRIDABLE


# ---------------------------------------------------------------------------
# Human review is not authorization
# ---------------------------------------------------------------------------

class TestHumanReviewNotAuthorization:
    """Tests that human review and approval are never authorization."""

    def test_approval_record_is_not_authorization(self):
        record = make_approval_record(
            approved_by="operator",
            approved_action="Review and approve deployment",
            approved_command_hash="sha256:abc",
            scope=SCOPE_TASK_DURATION,
            expires_at="2099-12-31T23:59:59Z",
        )
        assert record.is_authorization is False

    def test_accepted_risk_record_is_not_authorization(self):
        record = make_accepted_risk_record(
            accepted_by="operator",
            risk_level=RISK_LEVEL_HIGH,
            risk_description="Deploy without full test suite",
        )
        assert record.is_authorization is False

    def test_validate_approval_rejects_is_authorization_true(self):
        record = make_approval_record(
            approved_by="op",
            approved_action="test",
            approved_command_hash="sha256:x",
        )
        object.__setattr__(record, "is_authorization", True)
        issues = validate_approval_record(record)
        assert any("is_authorization must be False" in i for i in issues)

    def test_validate_risk_rejects_is_authorization_true(self):
        record = make_accepted_risk_record(
            accepted_by="op",
            risk_level=RISK_LEVEL_MEDIUM,
            risk_description="Test",
        )
        object.__setattr__(record, "is_authorization", True)
        issues = validate_accepted_risk_record(record)
        assert any("is_authorization must be False" in i for i in issues)


# ---------------------------------------------------------------------------
# Approval record is not execution authorization
# ---------------------------------------------------------------------------

class TestApprovalNotExecutionAuthorization:
    """Tests that approval records are never execution authorization."""

    def test_all_constructors_set_is_authorization_false(self):
        record = make_approval_record(
            approved_by="op",
            approved_action="test",
            approved_command_hash="sha256:x",
        )
        assert record.is_authorization is False

    def test_revoked_approval_still_not_authorization(self):
        record = make_approval_record(
            approved_by="op",
            approved_action="test",
            approved_command_hash="sha256:x",
        )
        revoked = revoke_approval(record)
        assert revoked.is_authorization is False

    def test_approval_with_all_scopes_not_authorization(self):
        for scope in [SCOPE_SINGLE_COMMAND, SCOPE_COMMAND_CATEGORY,
                       SCOPE_FILE_SET, SCOPE_TASK_DURATION, SCOPE_SESSION]:
            record = make_approval_record(
                approved_by="op",
                approved_action="test",
                approved_command_hash="sha256:x",
                scope=scope,
            )
            assert record.is_authorization is False, f"Failed for scope={scope}"


# ---------------------------------------------------------------------------
# JSON serialization
# ---------------------------------------------------------------------------

class TestSerialization:
    """Tests for JSON-safe serialization."""

    def test_approval_record_to_dict(self):
        record = make_approval_record(
            approved_by="operator",
            approved_action="Run integration tests",
            approved_command_hash="sha256:abc123",
            scope=SCOPE_FILE_SET,
            granted_at="2026-06-28T10:00:00Z",
            expires_at="2026-06-28T11:00:00Z",
            decision_context="would_require_human_review",
            hard_block_present=False,
        )
        d = record.to_dict()
        assert d["approved_by"] == "operator"
        assert d["scope"] == SCOPE_FILE_SET
        assert d["is_authorization"] is False
        assert d["no_enforcement"] is True

    def test_approval_record_to_dict_is_json_serializable(self):
        record = make_approval_record(
            approved_by="op",
            approved_action="test",
            approved_command_hash="sha256:x",
        )
        d = record.to_dict()
        json_str = json.dumps(d, sort_keys=True)
        parsed = json.loads(json_str)
        assert parsed["approved_by"] == "op"

    def test_accepted_risk_record_to_dict(self):
        record = make_accepted_risk_record(
            accepted_by="operator",
            risk_level=RISK_LEVEL_HIGH,
            risk_description="Skipping preflight for hotfix",
            scope=("src/hotfix.py",),
            expires_at="2026-06-28T12:00:00Z",
        )
        d = record.to_dict()
        assert d["accepted_by"] == "operator"
        assert d["risk_level"] == RISK_LEVEL_HIGH
        assert d["hard_block_override"] is False
        assert d["is_authorization"] is False

    def test_accepted_risk_to_dict_is_json_serializable(self):
        record = make_accepted_risk_record(
            accepted_by="op",
            risk_level=RISK_LEVEL_LOW,
            risk_description="Test",
        )
        d = record.to_dict()
        json_str = json.dumps(d, sort_keys=True)
        parsed = json.loads(json_str)
        assert parsed["risk_level"] == RISK_LEVEL_LOW


# ---------------------------------------------------------------------------
# Invalid record rejection
# ---------------------------------------------------------------------------

class TestInvalidRecordRejection:
    """Tests for rejection of invalid records."""

    def test_validate_approval_missing_fields(self):
        record = make_approval_record(
            approved_by="op",
            approved_action="test",
            approved_command_hash="sha256:x",
        )
        object.__setattr__(record, "approved_by", "")
        issues = validate_approval_record(record)
        assert any("approved_by is empty" in i for i in issues)

    def test_validate_approval_no_enforcement_false(self):
        record = make_approval_record(
            approved_by="op",
            approved_action="test",
            approved_command_hash="sha256:x",
        )
        object.__setattr__(record, "no_enforcement", False)
        issues = validate_approval_record(record)
        assert any("no_enforcement must be True" in i for i in issues)

    def test_validate_approval_hard_block_present(self):
        record = make_approval_record(
            approved_by="op",
            approved_action="test",
            approved_command_hash="sha256:x",
            hard_block_present=True,
        )
        issues = validate_approval_record(record)
        assert any("hard_block_present is True" in i for i in issues)

    def test_validate_approval_revocable_false(self):
        record = make_approval_record(
            approved_by="op",
            approved_action="test",
            approved_command_hash="sha256:x",
        )
        object.__setattr__(record, "revocable", False)
        issues = validate_approval_record(record)
        assert any("revocable must be True" in i for i in issues)

    def test_validate_risk_missing_fields(self):
        record = make_accepted_risk_record(
            accepted_by="op",
            risk_level=RISK_LEVEL_MEDIUM,
            risk_description="Test",
        )
        object.__setattr__(record, "risk_description", "")
        issues = validate_accepted_risk_record(record)
        assert any("risk_description is empty" in i for i in issues)

    def test_validate_risk_hard_block_override_true(self):
        record = make_accepted_risk_record(
            accepted_by="op",
            risk_level=RISK_LEVEL_MEDIUM,
            risk_description="Test",
        )
        object.__setattr__(record, "hard_block_override", True)
        issues = validate_accepted_risk_record(record)
        assert any("hard_block_override must be False" in i for i in issues)

    def test_validate_risk_invalid_level(self):
        record = make_accepted_risk_record(
            accepted_by="op",
            risk_level=RISK_LEVEL_MEDIUM,
            risk_description="Test",
        )
        object.__setattr__(record, "risk_level", "invalid")
        issues = validate_accepted_risk_record(record)
        assert any("invalid risk_level" in i for i in issues)


# ---------------------------------------------------------------------------
# Dict validation
# ---------------------------------------------------------------------------

class TestDictValidation:
    """Tests for dict-form validation."""

    def test_validate_approval_dict_missing_keys(self):
        issues = validate_approval_record_dict({})
        assert len(issues) >= 5  # approval_id, approved_by, approved_action, scope, granted_at, expires_at, revocable

    def test_validate_approval_dict_invalid_scope(self):
        d = {
            "approval_id": "appr-1",
            "approved_by": "op",
            "approved_action": "test",
            "approved_command_hash": "sha256:x",
            "scope": "bad_scope",
            "granted_at": "2026-01-01T00:00:00Z",
            "expires_at": "2026-01-01T01:00:00Z",
            "revocable": True,
        }
        issues = validate_approval_record_dict(d)
        assert any("invalid scope" in i for i in issues)

    def test_validate_approval_dict_is_authorization_true(self):
        d = {
            "approval_id": "appr-1",
            "approved_by": "op",
            "approved_action": "test",
            "approved_command_hash": "sha256:x",
            "scope": SCOPE_SINGLE_COMMAND,
            "granted_at": "2026-01-01T00:00:00Z",
            "expires_at": "2026-01-01T01:00:00Z",
            "revocable": True,
            "is_authorization": True,
        }
        issues = validate_approval_record_dict(d)
        assert any("is_authorization must be False" in i for i in issues)

    def test_validate_approval_dict_no_enforcement_false(self):
        d = {
            "approval_id": "appr-1",
            "approved_by": "op",
            "approved_action": "test",
            "approved_command_hash": "sha256:x",
            "scope": SCOPE_SINGLE_COMMAND,
            "granted_at": "2026-01-01T00:00:00Z",
            "expires_at": "2026-01-01T01:00:00Z",
            "revocable": True,
            "no_enforcement": False,
        }
        issues = validate_approval_record_dict(d)
        assert any("no_enforcement must be True" in i for i in issues)

    def test_validate_approval_dict_hard_block_present(self):
        d = {
            "approval_id": "appr-1",
            "approved_by": "op",
            "approved_action": "test",
            "approved_command_hash": "sha256:x",
            "scope": SCOPE_SINGLE_COMMAND,
            "granted_at": "2026-01-01T00:00:00Z",
            "expires_at": "2026-01-01T01:00:00Z",
            "revocable": True,
            "hard_block_present": True,
        }
        issues = validate_approval_record_dict(d)
        assert any("hard_block_present is True" in i for i in issues)

    def test_validate_risk_dict_missing_keys(self):
        issues = validate_accepted_risk_record_dict({})
        assert len(issues) >= 4

    def test_validate_risk_dict_invalid_level(self):
        d = {
            "risk_id": "risk-1",
            "accepted_by": "op",
            "risk_level": "extreme",
            "risk_description": "test",
            "accepted_at": "2026-01-01T00:00:00Z",
        }
        issues = validate_accepted_risk_record_dict(d)
        assert any("invalid risk_level" in i for i in issues)

    def test_validate_risk_dict_hard_block_override_true(self):
        d = {
            "risk_id": "risk-1",
            "accepted_by": "op",
            "risk_level": RISK_LEVEL_MEDIUM,
            "risk_description": "test",
            "accepted_at": "2026-01-01T00:00:00Z",
            "hard_block_override": True,
        }
        issues = validate_accepted_risk_record_dict(d)
        assert any("hard_block_override must be False" in i for i in issues)

    def test_validate_risk_dict_is_authorization_true(self):
        d = {
            "risk_id": "risk-1",
            "accepted_by": "op",
            "risk_level": RISK_LEVEL_MEDIUM,
            "risk_description": "test",
            "accepted_at": "2026-01-01T00:00:00Z",
            "is_authorization": True,
        }
        issues = validate_accepted_risk_record_dict(d)
        assert any("is_authorization must be False" in i for i in issues)

    def test_validate_risk_dict_no_enforcement_false(self):
        d = {
            "risk_id": "risk-1",
            "accepted_by": "op",
            "risk_level": RISK_LEVEL_MEDIUM,
            "risk_description": "test",
            "accepted_at": "2026-01-01T00:00:00Z",
            "no_enforcement": False,
        }
        issues = validate_accepted_risk_record_dict(d)
        assert any("no_enforcement must be True" in i for i in issues)
