"""Phase 135K — production validation tests."""

from __future__ import annotations

from pcae.cltr import schema
from pcae.cltr.enums import LifecycleState, TransitionType
from pcae.cltr.models import ProductionCltrRecord
from pcae.cltr.validation import validate_record, validate_schema_version


def _record(**overrides) -> ProductionCltrRecord:
    fields = dict(
        schema_id=schema.SCHEMA_ID,
        schema_version=schema.SCHEMA_VERSION,
        contract_version=schema.CONTRACT_VERSION,
        compatibility_id=schema.COMPATIBILITY_ID,
        transition_id="135K-VAL",
        phase_id="135K-VAL",
        repository_identity="repo",
        branch_identity="main",
        transition_type=TransitionType.PROPOSE_TRANSITION,
        lifecycle_state=LifecycleState.PROPOSED,
        source_revision="abc123",
        prior_state="none",
    )
    fields.update(overrides)
    return ProductionCltrRecord(**fields)


def test_proposed_without_certified_content_is_permitted():
    record = _record()
    errors = validate_record(record)
    assert errors == ()


def test_certified_with_certified_content_is_conformant():
    record = _record(
        lifecycle_state=LifecycleState.CERTIFIED,
        transition_type=TransitionType.CERTIFY,
        prior_state=None,
        certified_state={"x": 1},
        report_id="r1",
        report_digest="d" * 64,
        metadata_id="m1",
        metadata_digest="d" * 64,
        snapshot_id="s1",
        snapshot_digest="d" * 64,
    )
    errors = validate_record(record)
    assert errors == ()


def test_certified_without_certified_content_is_rejected():
    record = _record(lifecycle_state=LifecycleState.CERTIFIED, transition_type=TransitionType.CERTIFY, prior_state=None)
    errors = validate_record(record)
    assert any(e.code == "CLTR-VALIDATE-CERTIFIED-CONTENT" for e in errors)


def test_later_state_without_certified_content_is_rejected():
    record = _record(
        lifecycle_state=LifecycleState.TERMINAL_SUCCESS,
        transition_type=TransitionType.CLOSE_SUCCESS,
        prior_state=None,
    )
    errors = validate_record(record)
    assert any(e.code == "CLTR-VALIDATE-CERTIFIED-CONTENT" for e in errors)


def test_unsupported_schema_version_fails_closed():
    # ProductionCltrRecord's own constructor already refuses to build a
    # record carrying an unsupported schema_version (test_cltr_models.py's
    # test_record_rejects_unsupported_schema_version) -- validate_schema_
    # version is exercised directly here as the underlying fail-closed rule.
    errors = validate_schema_version("1.0.0")
    assert len(errors) == 1
    assert errors[0].code == "CLTR-VALIDATE-VERSION"
    assert validate_schema_version("1.0.1") == ()


def test_wrong_schema_id_is_rejected():
    record = _record(schema_id="NOT-CLTR-SCHEMA-001")
    errors = validate_record(record)
    assert any(e.code == "CLTR-VALIDATE-SCHEMA-ID" for e in errors)


def test_forbidden_transition_is_rejected():
    record = _record(
        prior_state=LifecycleState.PROPOSED.value,
        lifecycle_state=LifecycleState.PROPOSED,
        transition_type=TransitionType.CERTIFY,
    )
    errors = validate_record(record)
    assert any(e.code == "CLTR-VALIDATE-STATE" for e in errors)


def test_transition_id_path_traversal_rejected():
    record = _record(transition_id="../etc/passwd")
    errors = validate_record(record)
    assert any(e.code == "CLTR-VALIDATE-IDENTITY" for e in errors)


def test_notification_missing_without_suppression_rejected_at_notified():
    record = _record(
        lifecycle_state=LifecycleState.NOTIFIED,
        transition_type=TransitionType.NOTIFY_CONFIRM,
        prior_state="NOTIFYING",
        certified_state={"x": 1},
        report_id="r1", report_digest="d" * 64,
        metadata_id="m1", metadata_digest="d" * 64,
        snapshot_id="s1", snapshot_digest="d" * 64,
        receipt_id="rcpt1",
    )
    errors = validate_record(record)
    assert any(e.code == "CLTR-VALIDATE-NOTIFICATION" for e in errors)
