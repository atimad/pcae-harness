"""Phase 143E: authority-boundary and security/adversarial tests.

CHGR-001's central boundary: repository presence, schema validity, hash
validity, and canonical formatting never establish authority
(CHGR-REQ-080, CHGR-REQ-091 through CHGR-REQ-095). This file exercises
that boundary directly, plus the AI-authorship-can't-substitute-for-human-
evidence and forged-identity classes of adversarial scenario.
"""
from __future__ import annotations

import json
from pathlib import Path

from pcae.governance.inspection import InspectionObservation, inspect_artifact_at_path
from pcae.governance.verification import VerificationObservation, verify_artifact_at_path

FIXTURES = Path(__file__).parent / "fixtures" / "chgr"


def test_143e_no_schema_field_named_is_authoritative_exists_anywhere():
    import pcae.schema_resources as schema_resources_pkg

    with schema_resources_pkg.chgr_root() as root:
        for schema_file in root.rglob("*.schema.json"):
            assert '"is_authoritative"' not in schema_file.read_text()


def test_143e_forbidden_authority_assertion_fixture_is_schema_rejected():
    """An injected is_authoritative field must be structurally impossible
    (additionalProperties:false), not merely ignored."""
    from pcae.schema_runtime import OutcomeStatus, build_offline_registry, validate_record_shape
    from pcae.schema_resources import chgr_root

    doc = json.loads((FIXTURES / "invalid_forbidden_authority_assertion.json").read_text())
    with chgr_root() as root:
        registry = build_offline_registry(root)
    result = validate_record_shape(doc, schema_id=doc["schema_id"], registry=registry)
    assert result.status is not OutcomeStatus.VALID


def test_143e_repository_presence_is_not_authority_inspection_never_claims_it():
    """A file merely existing on disk and inspecting cleanly must never be
    represented by this module as an affirmative authority grant -- the
    only place 'authorized' may appear is inside the disclosure's own
    negation ("does not establish... performed by an authorized human")."""
    path = FIXTURES / "valid_record_published.json"
    outcome = inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    assert isinstance(outcome, InspectionObservation)
    payload = outcome.to_dict()
    assert "does not establish" in payload["disclosure"]
    non_disclosure_text = json.dumps({k: v for k, v in payload.items() if k != "disclosure"}).lower()
    assert "authorized" not in non_disclosure_text
    assert '"is_authoritative"' not in non_disclosure_text


def test_143e_valid_schema_is_not_authority_verification_output_says_so():
    path = FIXTURES / "valid_record_published.json"
    related = tuple(
        (FIXTURES / n).read_bytes()
        for n in ("valid_confirmation_evidence.json", "valid_provenance.json", "valid_integrity.json", "valid_template.json")
    )
    outcome = verify_artifact_at_path(path, artifact_bytes=path.read_bytes(), related_bytes=related)
    assert isinstance(outcome, VerificationObservation)
    assert "never" in outcome.disclosure or "not" in outcome.disclosure
    assert "authorized human" in outcome.disclosure


def test_143e_hash_validity_alone_is_not_authority():
    """digest_self_consistency passing (a hash-validity fact) never appears
    alongside any authority claim in the observation."""
    path = FIXTURES / "valid_record_published.json"
    outcome = verify_artifact_at_path(path, artifact_bytes=path.read_bytes())
    assert isinstance(outcome, VerificationObservation)
    digest_check = next(c for c in outcome.checks if c.name == "digest_self_consistency")
    assert digest_check.status == "passed"
    assert "authority" not in digest_check.detail.lower()


def test_143e_ai_authorship_marker_cannot_substitute_for_human_evidence():
    """Injecting an 'ai_generated': true-shaped marker anywhere in a
    record's fields does not change verification's outcome favorably --
    there is no code path that treats such a marker as elevating trust,
    and the schema's additionalProperties:false rejects it as an
    unrecognized field outright at the top level."""
    from pcae.schema_runtime import OutcomeStatus, build_offline_registry, validate_record_shape
    from pcae.schema_resources import chgr_root

    doc = json.loads((FIXTURES / "valid_record_published.json").read_text())
    doc["ai_generated"] = True
    with chgr_root() as root:
        registry = build_offline_registry(root)
    result = validate_record_shape(doc, schema_id=doc["schema_id"], registry=registry)
    assert result.status is not OutcomeStatus.VALID


def test_143e_forged_decision_maker_identity_is_not_elevated_by_verification():
    """A record claiming os_authenticated_user identity evidence with a
    plainly fabricated-looking identifier still only reaches 'structurally
    consistent', never an authority claim -- verification has no code path
    that inspects or trusts the identifier string's plausibility."""
    doc = json.loads((FIXTURES / "valid_record_published.json").read_text())
    doc["decision_maker_identity_evidence"]["identifier"] = "definitely-not-a-real-user"
    doc["decision_maker_identity_evidence"]["evidence_kind"] = "os_authenticated_user"
    import hashlib

    def canon(d):
        return json.dumps(d, sort_keys=True, separators=(",", ":")).encode()

    doc["record_digest"] = hashlib.sha256(canon({k: v for k, v in doc.items() if k != "record_digest"})).hexdigest()
    outcome = verify_artifact_at_path(Path("mem"), artifact_bytes=canon(doc))
    assert isinstance(outcome, VerificationObservation)
    payload = outcome.to_dict()
    non_disclosure_text = json.dumps({k: v for k, v in payload.items() if k != "disclosure"})
    assert "authorized" not in non_disclosure_text


def test_143e_stale_or_unsupported_schema_version_fails():
    doc = json.loads((FIXTURES / "adversarial_unsupported_schema_version.json").read_text())
    outcome = verify_artifact_at_path(Path("mem"), artifact_bytes=json.dumps(doc).encode())
    assert outcome.error_code in ("SCHEMA_INVALID", "DIGEST_MISMATCH")
