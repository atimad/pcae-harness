"""Phase 146H.1 tests: Governance Verification Schema-Version Support Repair.

Covers the repair to ``pcae.governance.verification``'s ``_shape_check``:
the record family's own manifest-declared ``schema_version`` (read fresh
from ``manifest.json`` on every call, exactly as ``schema_id`` already
was) is now the authoritative supported value, replacing the stale,
hardcoded ``SUPPORTED_SCHEMA_VERSION = "1.0"`` module constant that
Phase 146D's additive schema amendment (bumping
``human_governance_record.schema.json`` to schema_version ``"1.1"``, for
CHGR-REQ-207) made incorrect. Independently discovered and demonstrated
in Phase 146H (docs/PHASE_146H_CHGR001_SCHEMA_ENVELOPE_INDEPENDENT_IMPLEMENTATION_VERIFICATION.md
Sec.8.1): every ``human_governance_record`` the current production
implementation (Phase 146G) constructs was rejected by
``pcae governance-record verify`` with ``SCHEMA_INVALID`` /
``unsupported_schema_version``, solely because of that stale constant.

``tests/test_chgr_verification.py`` (Phase 143E) covers the module's
general verification behavior; this module focuses specifically on
schema-version support and its interaction with real, current production
CHGR artifacts.
"""
from __future__ import annotations

import copy
import json

import pytest

from pcae.governance.publication.record import build_publication_record
from pcae.governance.publication.models import PublicationAuthorizationEvent
from pcae.governance.verification import verify_artifact_at_path, VerificationFailure, VerificationObservation
from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage
from pcae.interactive_workflow.session.identity import generate_session_id

_TS = "2026-07-24T10:00:00+00:00"
_LATER_TS = "2026-07-24T11:00:00+00:00"


def _package() -> PublicationReadinessPackage:
    return PublicationReadinessPackage(
        package_id="pkg-146h1",
        session_id=generate_session_id(),
        session_state=SessionState.CONFIRMED,
        transition_sequence_number=0,
        evidence_refs=("ev-1",),
        clarification_refs=(),
        audit_refs=(),
        preview_id="preview-1",
        preview_digest="b" * 64,
        confirmation_request_id="req-1",
        confirmation_response_id="resp-1",
        built_at=_TS,
        decision_subject="subject-1",
        template_id="template-1",
        template_version="1.0",
        selected_option_id="option-a",
        rationale_text="Because the data supports it.",
        conditions_text=None,
        options_presented=("option-a", "option-b"),
        decision_maker_identity_evidence={
            "evidence_kind": "typed_confirmation_only",
            "identifier": "human-1",
            "captured_at": _TS,
        },
        preview_rendered_content="Confirm selection: option-a",
        confirmation_statement="Accepted",
        confirmation_timestamp=_TS,
    )


def _event(package: PublicationReadinessPackage) -> PublicationAuthorizationEvent:
    return PublicationAuthorizationEvent(
        event_id="pubauth-146h1", operator_id="alice", package_id=package.package_id, invoked_at=_LATER_TS
    )


def _bundle() -> dict:
    package = _package()
    event = _event(package)
    return build_publication_record(package, event, "chgr-" + "1" * 32, _TS)


def _write(tmp_path, artifact: dict):
    path = tmp_path / f"{artifact['record_id']}.json"
    path.write_text(json.dumps(artifact))
    return path


def _verify(path):
    return verify_artifact_at_path(path, artifact_bytes=path.read_bytes())


# --- Unit: manifest-derived, not hardcoded, schema-version support --------


def test_supported_schema_version_no_longer_a_hardcoded_module_constant():
    """The repair removes the stale global constant entirely -- supported
    versions are read fresh from the manifest per record family, exactly
    like schema_id already was, never duplicated as a separate literal."""

    import pcae.governance.verification as verification_module

    assert not hasattr(verification_module, "SUPPORTED_SCHEMA_VERSION")
    assert "SUPPORTED_SCHEMA_VERSION" not in verification_module.__all__


def test_current_manifest_schema_version_for_human_governance_record_verifies(tmp_path):
    """The specific defect 146H demonstrated: a real, current-production
    human_governance_record (schema_version "1.1", per Phase 146D) now
    verifies standalone, instead of being rejected as unsupported."""

    bundle = _bundle()
    path = _write(tmp_path, bundle["human_governance_record"])
    outcome = _verify(path)
    assert isinstance(outcome, VerificationObservation), outcome
    assert outcome.outcome == "verified"


def test_current_manifest_schema_version_for_sibling_families_still_verifies(tmp_path):
    """Sibling families whose manifest-declared schema_version remains
    "1.0" (untouched by Phase 146D) continue to verify -- the repair does
    not regress the previously-correct case, it only stops the previously
    incorrect global constant from clobbering the per-family value."""

    bundle = _bundle()
    for family in ("human_confirmation_evidence", "governance_record_provenance", "governance_record_integrity"):
        path = _write(tmp_path, bundle[family])
        outcome = _verify(path)
        assert isinstance(outcome, VerificationObservation), (family, outcome)
        assert outcome.outcome == "verified"


@pytest.mark.parametrize("bad_version", ["2.0", "0.9", "1.2"])
def test_genuinely_unsupported_schema_version_still_rejected(tmp_path, bad_version):
    """A schema_version the manifest does not currently declare for this
    record family -- a genuine future/past mismatch, not the 146H defect
    -- is still refused. The repair narrows nothing."""

    bundle = _bundle()
    tampered = copy.deepcopy(bundle["human_governance_record"])
    tampered["schema_version"] = bad_version
    path = _write(tmp_path, tampered)
    outcome = _verify(path)
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "SCHEMA_INVALID"
    assert "unsupported_schema_version" in outcome.message


def test_malformed_schema_version_string_rejected(tmp_path):
    bundle = _bundle()
    tampered = copy.deepcopy(bundle["human_governance_record"])
    tampered["schema_version"] = "not-a-version"
    path = _write(tmp_path, tampered)
    outcome = _verify(path)
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "SCHEMA_INVALID"


def test_stale_pre_146d_schema_version_on_current_family_rejected(tmp_path):
    """The mirror-image case: a human_governance_record declaring the OLD
    "1.0" value the manifest no longer carries for this family is,
    correctly, no longer accepted either -- the fix is a correct
    per-family equality check against the live manifest, not a blanket
    widening of acceptance."""

    bundle = _bundle()
    tampered = copy.deepcopy(bundle["human_governance_record"])
    tampered["schema_version"] = "1.0"
    path = _write(tmp_path, tampered)
    outcome = _verify(path)
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "SCHEMA_INVALID"
    assert "unsupported_schema_version" in outcome.message


def test_manifest_lookup_and_schema_id_match_are_unaffected(tmp_path):
    """The repair touches only the schema_version comparison; the
    preceding manifest-entry lookup and schema_id match (already correct)
    are unchanged -- an artifact with a genuinely wrong schema_id is still
    refused as family_identity_mismatch, not unsupported_schema_version."""

    bundle = _bundle()
    tampered = copy.deepcopy(bundle["human_governance_record"])
    tampered["schema_id"] = "https://pcae.local/schemas/chgr/records/does-not-exist.schema.json"
    path = _write(tmp_path, tampered)
    outcome = _verify(path)
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code in ("SCHEMA_INVALID", "UNREGISTERED_SCHEMA")
    assert "family_identity_mismatch" in outcome.message or "unregistered" in outcome.message.lower()


# --- Integration: fail-closed behavior preserved ---------------------------


def test_tampered_content_still_rejected_as_digest_mismatch(tmp_path):
    """Fail-closed behavior for content tampering is unaffected by this
    repair -- a record whose content was altered after its digest was
    computed is still refused, now correctly reaching that check instead
    of being masked by the (now-fixed) schema_version gate."""

    bundle = _bundle()
    tampered = copy.deepcopy(bundle["human_governance_record"])
    tampered["decision_subject"] = "TAMPERED"
    path = _write(tmp_path, tampered)
    outcome = _verify(path)
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "DIGEST_MISMATCH"


def test_end_to_end_valid_bundle_every_artifact_verifies_standalone(tmp_path):
    """Integration: every one of the four artifacts one real Publication
    Execution produces verifies successfully on its own -- the exact
    scenario 146H demonstrated failing for human_governance_record."""

    bundle = _bundle()
    for family, artifact in bundle.items():
        path = _write(tmp_path, artifact)
        outcome = _verify(path)
        assert isinstance(outcome, VerificationObservation), (family, outcome)
        assert outcome.outcome == "verified"
