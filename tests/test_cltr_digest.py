"""Phase 135K — digest contract tests."""

from __future__ import annotations

from pcae.cltr import schema
from pcae.cltr.digest import compute_record_digest, is_well_formed_digest, verify_record_digest
from pcae.cltr.enums import LifecycleState, TransitionType
from pcae.cltr.models import ProductionCltrRecord


def _record(**overrides) -> ProductionCltrRecord:
    fields = dict(
        schema_id=schema.SCHEMA_ID,
        schema_version=schema.SCHEMA_VERSION,
        contract_version=schema.CONTRACT_VERSION,
        compatibility_id=schema.COMPATIBILITY_ID,
        transition_id="135K-DIGEST",
        phase_id="135K-DIGEST",
        repository_identity="repo",
        branch_identity="main",
        transition_type=TransitionType.PROPOSE_TRANSITION,
        lifecycle_state=LifecycleState.PROPOSED,
        source_revision="abc123",
    )
    fields.update(overrides)
    return ProductionCltrRecord(**fields)


def test_digest_is_deterministic():
    record = _record()
    assert compute_record_digest(record) == compute_record_digest(record)


def test_digest_well_formed():
    digest = compute_record_digest(_record())
    assert is_well_formed_digest(digest)
    assert len(digest) == 64
    assert digest == digest.lower()


def test_tamper_detection_via_authority_field_change():
    d1 = compute_record_digest(_record(source_revision="abc123"))
    d2 = compute_record_digest(_record(source_revision="xyz789"))
    assert d1 != d2


def test_excluded_field_record_digest_itself_does_not_affect_recomputation():
    base = _record()
    with_digest = base.with_digest("a" * 64)
    assert compute_record_digest(base) == compute_record_digest(with_digest)


def test_verify_record_digest_true_for_correct_digest():
    record = _record()
    digest = compute_record_digest(record)
    signed = record.with_digest(digest)
    assert verify_record_digest(signed) is True


def test_verify_record_digest_false_for_wrong_digest():
    record = _record().with_digest("0" * 64)
    assert verify_record_digest(record) is False


def test_verify_record_digest_false_for_malformed_digest():
    record = _record().with_digest("not-hex")
    assert verify_record_digest(record) is False


def test_verify_record_digest_false_for_wrong_length():
    record = _record().with_digest("abc123")
    assert verify_record_digest(record) is False


def test_is_well_formed_digest_rejects_uppercase():
    assert is_well_formed_digest("A" * 64) is False
