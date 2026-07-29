"""Phase 143E: pcae.governance.verification tests.

Covers the deterministic, fail-closed verification pipeline: the full
positive cross-artifact chain verifies with every check passing; every
adversarial (schema-legal-but-semantically-wrong) fixture is rejected with
the expected stable error_code; verification performs no mutation and no
network access; results are deterministic.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from pcae.governance.verification import (
    VerificationFailure,
    VerificationObservation,
    verify_artifact_at_path,
)

FIXTURES = Path(__file__).parent / "fixtures" / "chgr"


def _bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def _verify(name: str, related: tuple[str, ...] = ()):
    path = FIXTURES / name
    return verify_artifact_at_path(
        path,
        artifact_bytes=path.read_bytes(),
        related_bytes=tuple(_bytes(r) for r in related),
    )


ALL_RELATED = (
    "valid_confirmation_evidence.json",
    "valid_provenance.json",
    "valid_integrity.json",
    "valid_template.json",
)


def test_143e_full_positive_chain_verifies_with_every_check_passing():
    outcome = _verify("valid_record_published.json", ALL_RELATED)
    assert isinstance(outcome, VerificationObservation)
    statuses = {c.name: c.status for c in outcome.checks}
    assert set(statuses.values()) == {"passed"}
    assert statuses.keys() == {
        "schema_shape",
        "digest_self_consistency",
        "lifecycle_structural_legality",
        "confirmation_binding",
        "assurance_truthfulness",
        "provenance_consistency",
        "integrity_consistency",
        "template_resolution",
    }


@pytest.mark.parametrize(
    "fixture_name",
    sorted(
        p.name
        for p in FIXTURES.glob("valid_record_*.json")
    ),
)
def test_143e_every_lifecycle_state_fixture_verifies_standalone(fixture_name):
    """Every one of the 8 frozen states is representable and self-consistent
    even without related artifacts supplied (schema_shape + digest_self_consistency
    + lifecycle_structural_legality all pass; cross-artifact checks are
    reported skipped, never silently passed)."""
    outcome = _verify(fixture_name)
    assert isinstance(outcome, VerificationObservation), fixture_name
    statuses = {c.name: c.status for c in outcome.checks}
    assert statuses["schema_shape"] == "passed"
    assert statuses["digest_self_consistency"] == "passed"
    assert statuses["lifecycle_structural_legality"] == "passed"
    assert statuses["confirmation_binding"] == "skipped"
    assert statuses["provenance_consistency"] == "skipped"
    assert statuses["integrity_consistency"] == "skipped"
    assert statuses["template_resolution"] == "skipped"


@pytest.mark.parametrize(
    "fixture_name,related,expected_code",
    [
        ("adversarial_record_substitution.json", ALL_RELATED, "DIGEST_MISMATCH"),
        ("adversarial_template_substitution.json", ALL_RELATED, "DIGEST_MISMATCH"),
        ("adversarial_extension_override_attempt.json", ALL_RELATED, "DIGEST_MISMATCH"),
        ("adversarial_unsupported_schema_version.json", ALL_RELATED, "SCHEMA_INVALID"),
        ("adversarial_confirmation_content_mismatch.json", (), "DIGEST_MISMATCH"),
        ("adversarial_altered_published_content.json", (), "DIGEST_MISMATCH"),
        (
            "adversarial_assurance_overclaim_selfconsistent.json",
            ("adversarial_assurance_overclaim_selfconsistent_confirmation.json",),
            "ASSURANCE_OVERCLAIM",
        ),
        ("adversarial_template_mismatch_selfconsistent.json", ("valid_template.json",), "TEMPLATE_UNRESOLVABLE"),
    ],
)
def test_143e_adversarial_fixture_rejected_with_expected_code(fixture_name, related, expected_code):
    outcome = _verify(fixture_name, related)
    assert isinstance(outcome, VerificationFailure), fixture_name
    assert outcome.error_code == expected_code, (fixture_name, outcome.error_code, outcome.message)


def test_143e_phase_report_shaped_document_rejected_as_chgr():
    outcome = _verify("invalid_phase_report_substitution.json")
    assert isinstance(outcome, VerificationFailure)
    assert outcome.error_code == "PHASE_REPORT_SUBSTITUTION"


def test_143e_malformed_json_rejected_schema_invalid():
    path = FIXTURES / "valid_record_published.json"
    outcome = verify_artifact_at_path(path, artifact_bytes=b"{not json")
    assert isinstance(outcome, VerificationFailure)
    assert outcome.error_code == "SCHEMA_INVALID"


def test_143e_verification_is_deterministic():
    a = _verify("valid_record_published.json", ALL_RELATED)
    b = _verify("valid_record_published.json", ALL_RELATED)
    assert a.to_dict() == b.to_dict()


def test_143e_verification_never_mutates_input_bytes():
    path = FIXTURES / "valid_record_published.json"
    original = path.read_bytes()
    verify_artifact_at_path(path, artifact_bytes=original)
    assert path.read_bytes() == original


def test_143e_verification_never_mutates_repository():
    before = sorted(FIXTURES.glob("*"))
    _verify("valid_record_published.json", ALL_RELATED)
    after = sorted(FIXTURES.glob("*"))
    assert before == after


def test_143e_skipped_checks_are_explicit_never_silently_passed():
    outcome = _verify("valid_record_published.json")
    assert isinstance(outcome, VerificationObservation)
    skipped = [c for c in outcome.checks if c.status == "skipped"]
    assert skipped
    for c in skipped:
        assert c.detail


def test_143e_error_code_is_always_one_of_the_stable_categories():
    """Phase 146L (CHGR-REQ-212, CHGR-REQ-213) added three related-artifact
    resolution codes to the original nine: no existing code accurately
    named ambiguous-match rejection, family-identity mismatch, or an
    exact reference-digest mismatch distinct from self-digest tampering."""
    from pcae.governance.verification import _ERROR_CODES

    assert _ERROR_CODES == {
        "SCHEMA_INVALID",
        "DIGEST_MISMATCH",
        "PROVENANCE_INCOMPLETE",
        "CONFIRMATION_UNBOUND",
        "LIFECYCLE_INCONSISTENT",
        "ASSURANCE_OVERCLAIM",
        "TEMPLATE_UNRESOLVABLE",
        "PHASE_REPORT_SUBSTITUTION",
        "UNREGISTERED_SCHEMA",
        "RELATED_ARTIFACT_AMBIGUOUS",
        "RELATED_ARTIFACT_FAMILY_MISMATCH",
        "REFERENCE_DIGEST_MISMATCH",
    }
