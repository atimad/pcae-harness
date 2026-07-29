"""Phase 146H.3 tests: Confirmation Binding Verification Repair.

Covers the repair to ``pcae.governance.verification``: the
``confirmation_binding``, ``provenance_consistency``, and
``integrity_consistency`` checks no longer recompute a digest over the
Human Governance Record's own (stripped) content via the removed,
obsolete ``_confirmable_content_digest_of`` helper (Phase 143E design).
Independently re-confirmed in Phase 146H.2
(docs/PHASE_146H2_CONFIRMATION_BINDING_ROOT_CAUSE_RESOLUTION.md): the
current production construction path (Phase 146G,
``build_publication_record``) populates
``human_confirmation_evidence.confirmed_content_digest``,
``human_confirmation_evidence.preview_rendering_digest``, and
``governance_record_provenance.preview_content_digest`` all from the
same upstream ``PublicationReadinessPackage.preview_digest`` -- a value
with no mathematical relationship to the published record's own
content -- and ``governance_record_integrity.payload_digest`` from the
Human Governance Record's own real, final ``record_digest``
(CHGR-REQ-203). The repaired checks verify exactly those relationships
instead: mutual consistency among the three preview-digest-sourced
fields (CHGR-REQ-201), and integrity's ``payload_digest`` against the
record's own already-verified ``record_digest``.

``tests/test_chgr_verification.py`` (Phase 143E) covers the module's
general verification behavior with its own fixture set, migrated by
this phase to the new binding rule (see fixture migration note in the
Phase 146H.3 report); this module focuses specifically on the repaired
binding checks and their interaction with real, current production CHGR
artifacts, mirroring ``tests/test_phase_146h1_governance_verification_schema_version_repair.py``'s
structure for the sibling 146H.1 repair.
"""
from __future__ import annotations

import copy
import json

import pytest

from pcae.cli import main
from pcae.governance.publication.record import build_publication_record, compute_record_digest
from pcae.governance.publication.models import PublicationAuthorizationEvent
from pcae.governance.verification import verify_artifact_at_path, VerificationFailure, VerificationObservation
from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage
from pcae.interactive_workflow.session.identity import generate_session_id

_TS = "2026-07-24T10:00:00+00:00"
_LATER_TS = "2026-07-24T11:00:00+00:00"


def _package() -> PublicationReadinessPackage:
    return PublicationReadinessPackage(
        package_id="pkg-146h3",
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
        event_id="pubauth-146h3", operator_id="alice", package_id=package.package_id, invoked_at=_LATER_TS
    )


def _bundle() -> dict:
    package = _package()
    event = _event(package)
    return build_publication_record(package, event, "chgr-" + "3" * 32, _TS)


def _write(tmp_path, artifact: dict, name: str | None = None):
    path = tmp_path / f"{name or artifact['record_id']}.json"
    path.write_text(json.dumps(artifact))
    return path


def _verify(path, related=()):
    return verify_artifact_at_path(
        path,
        artifact_bytes=path.read_bytes(),
        related_bytes=tuple(p.read_bytes() for p in related),
    )


def _resign(artifact: dict) -> dict:
    """Recompute record_digest after mutating a self-consistent fixture,
    mirroring build_publication_record's own digest discipline -- so a
    test fixture's *only* defect is the field under test, not a stale
    self-digest that would be caught earlier by digest_self_consistency."""
    artifact = dict(artifact)
    artifact["record_digest"] = compute_record_digest(artifact)
    return artifact


# --- Unit: the obsolete record-content recomputation is gone --------------


def test_confirmable_content_digest_helper_removed():
    """The repair removes the obsolete Phase-143E helper entirely -- the
    verifier no longer has any code path that recomputes a digest over
    the Human Governance Record's own (stripped) content for binding
    purposes."""

    import pcae.governance.verification as verification_module

    assert not hasattr(verification_module, "_confirmable_content_digest_of")


def test_obsolete_record_content_derived_value_no_longer_satisfies_binding(tmp_path):
    """The exact 143E formula (a digest over the HGR's own stripped
    content) no longer coincidentally satisfies confirmation binding: a
    confirmation evidence artifact whose confirmed_content_digest was set
    via that obsolete formula, but which disagrees with its own
    preview_rendering_digest, is correctly rejected -- proving the
    verifier no longer depends on Human Governance Record content
    recomputation at all."""

    bundle = _bundle()
    record = bundle["human_governance_record"]

    excluded = {"record_digest", "confirmation_evidence_ref", "provenance_ref", "integrity_ref"}
    stripped = {k: v for k, v in record.items() if k not in excluded}
    import hashlib

    obsolete_formula_digest = hashlib.sha256(
        json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    confirmation = copy.deepcopy(bundle["human_confirmation_evidence"])
    confirmation["confirmed_content_digest"] = obsolete_formula_digest
    confirmation = _resign(confirmation)

    hgr_path = _write(tmp_path, record)
    conf_path = _write(tmp_path, confirmation)
    outcome = _verify(hgr_path, related=(conf_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "CONFIRMATION_UNBOUND"


# --- Unit: matching upstream preview-digest fields pass --------------------


def test_matching_upstream_preview_digest_values_pass(tmp_path):
    bundle = _bundle()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    related = [
        _write(tmp_path, bundle[fam])
        for fam in ("human_confirmation_evidence", "governance_record_provenance", "governance_record_integrity")
    ]
    outcome = _verify(hgr_path, related=related)
    assert isinstance(outcome, VerificationObservation), outcome
    statuses = {c.name: c.status for c in outcome.checks}
    assert statuses["confirmation_binding"] == "passed"
    assert statuses["provenance_consistency"] == "passed"
    assert statuses["integrity_consistency"] == "passed"


# --- Unit: each binding field mismatch fails independently -----------------


def test_confirmed_content_digest_mismatched_against_preview_rendering_digest_fails(tmp_path):
    """digest-valid but semantically unbound sibling combination: both
    fields are well-formed sha256 hex digests, but they disagree."""

    bundle = _bundle()
    confirmation = copy.deepcopy(bundle["human_confirmation_evidence"])
    confirmation["confirmed_content_digest"] = "9" * 64
    confirmation = _resign(confirmation)

    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    conf_path = _write(tmp_path, confirmation)
    outcome = _verify(hgr_path, related=(conf_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "CONFIRMATION_UNBOUND"


def test_preview_rendering_digest_mismatched_against_confirmed_content_digest_fails(tmp_path):
    bundle = _bundle()
    confirmation = copy.deepcopy(bundle["human_confirmation_evidence"])
    confirmation["preview_rendering_digest"] = "8" * 64
    confirmation = _resign(confirmation)

    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    conf_path = _write(tmp_path, confirmation)
    outcome = _verify(hgr_path, related=(conf_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "CONFIRMATION_UNBOUND"


def test_provenance_preview_content_digest_mismatched_against_confirmation_fails(tmp_path):
    bundle = _bundle()
    provenance = copy.deepcopy(bundle["governance_record_provenance"])
    provenance["preview_content_digest"] = "7" * 64
    provenance = _resign(provenance)

    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    conf_path = _write(tmp_path, bundle["human_confirmation_evidence"])
    prov_path = _write(tmp_path, provenance)
    outcome = _verify(hgr_path, related=(conf_path, prov_path))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "PROVENANCE_INCOMPLETE"


def test_integrity_payload_digest_mismatched_against_record_digest_fails(tmp_path):
    bundle = _bundle()
    integrity = copy.deepcopy(bundle["governance_record_integrity"])
    integrity["payload_digest"] = "6" * 64
    integrity = _resign(integrity)

    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    integ_path = _write(tmp_path, integrity)
    outcome = _verify(hgr_path, related=(integ_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "DIGEST_MISMATCH"


def test_malformed_digest_value_rejected_at_schema_shape(tmp_path):
    bundle = _bundle()
    confirmation = copy.deepcopy(bundle["human_confirmation_evidence"])
    confirmation["confirmed_content_digest"] = "not-a-hex-digest"
    # Deliberately not re-signed: a malformed value is rejected by the
    # sha256_hex pattern at schema-shape validation, before any digest
    # comparison is reached.
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    conf_path = _write(tmp_path, confirmation)
    outcome = _verify(hgr_path, related=(conf_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code in ("SCHEMA_INVALID", "DIGEST_MISMATCH")


def test_missing_binding_field_rejected(tmp_path):
    bundle = _bundle()
    confirmation = copy.deepcopy(bundle["human_confirmation_evidence"])
    del confirmation["confirmed_content_digest"]
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    conf_path = _write(tmp_path, confirmation)
    outcome = _verify(hgr_path, related=(conf_path,))
    assert isinstance(outcome, VerificationFailure), outcome


def test_confirmation_binding_no_longer_depends_on_human_governance_record_content(tmp_path):
    """Changing the Human Governance Record's own content (decision_subject)
    no longer has any bearing on whether confirmation_binding passes --
    only the confirmation evidence's own internal consistency and its
    cross-check against provenance matter now. (The altered record is
    still independently caught by digest_self_consistency, unrelated to
    this repair.)"""

    bundle = _bundle()
    tampered_record = copy.deepcopy(bundle["human_governance_record"])
    tampered_record["decision_subject"] = "a-different-subject-entirely"
    tampered_record = _resign(tampered_record)

    hgr_path = _write(tmp_path, tampered_record)
    conf_path = _write(tmp_path, bundle["human_confirmation_evidence"])
    outcome = _verify(hgr_path, related=(conf_path,))
    assert isinstance(outcome, VerificationObservation), outcome
    statuses = {c.name: c.status for c in outcome.checks}
    assert statuses["confirmation_binding"] == "passed"


# --- Unit: missing sibling is explicitly skipped, never silently passed ----


def test_missing_confirmation_sibling_explicitly_skipped(tmp_path):
    bundle = _bundle()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    outcome = _verify(hgr_path)
    assert isinstance(outcome, VerificationObservation), outcome
    binding = next(c for c in outcome.checks if c.name == "confirmation_binding")
    assert binding.status == "skipped"
    assert binding.detail


# --- Integration: real production bundle through the public API + CLI -----


def test_end_to_end_valid_bundle_verifies_through_verification_api(tmp_path):
    bundle = _bundle()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    related = [
        _write(tmp_path, bundle[fam])
        for fam in ("human_confirmation_evidence", "governance_record_provenance", "governance_record_integrity")
    ]
    outcome = _verify(hgr_path, related=related)
    assert isinstance(outcome, VerificationObservation), outcome
    assert outcome.outcome == "verified"
    assert {c.status for c in outcome.checks if c.name != "template_resolution"} == {"passed"}


def test_end_to_end_valid_bundle_verifies_through_real_cli(tmp_path, capsys):
    bundle = _bundle()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    related = [
        _write(tmp_path, bundle[fam])
        for fam in ("human_confirmation_evidence", "governance_record_provenance", "governance_record_integrity")
    ]
    args = ["governance-record", "verify", str(hgr_path)]
    for r in related:
        args += ["--related", str(r)]
    exit_code = main(args)
    output = capsys.readouterr().out
    assert exit_code == 0, output
    assert "outcome: verified" in output
    assert "CONFIRMATION_UNBOUND" not in output


def test_end_to_end_tampered_confirmation_sibling_rejected_through_real_cli(tmp_path, capsys):
    bundle = _bundle()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    confirmation = copy.deepcopy(bundle["human_confirmation_evidence"])
    confirmation["confirmed_content_digest"] = "5" * 64
    confirmation = _resign(confirmation)
    related = [
        _write(tmp_path, confirmation, name="confirmation"),
        _write(tmp_path, bundle["governance_record_provenance"]),
        _write(tmp_path, bundle["governance_record_integrity"]),
    ]
    args = ["governance-record", "verify", str(hgr_path)]
    for r in related:
        args += ["--related", str(r)]
    exit_code = main(args)
    output = capsys.readouterr().out
    assert exit_code != 0
    assert "CONFIRMATION_UNBOUND" in output


def test_unsupported_schema_version_still_rejected_alongside_binding_repair(tmp_path):
    """Regression: the 146H.1 schema-version repair and this phase's
    binding repair are independent and both still hold."""

    bundle = _bundle()
    tampered = copy.deepcopy(bundle["human_governance_record"])
    tampered["schema_version"] = "9.9"
    hgr_path = _write(tmp_path, tampered)
    conf_path = _write(tmp_path, bundle["human_confirmation_evidence"])
    outcome = _verify(hgr_path, related=(conf_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "SCHEMA_INVALID"


def test_tampered_human_governance_record_still_rejected(tmp_path):
    bundle = _bundle()
    tampered = copy.deepcopy(bundle["human_governance_record"])
    tampered["decision_subject"] = "TAMPERED-AFTER-DIGEST"
    hgr_path = _write(tmp_path, tampered)
    conf_path = _write(tmp_path, bundle["human_confirmation_evidence"])
    outcome = _verify(hgr_path, related=(conf_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "DIGEST_MISMATCH"


def test_tampered_confirmation_sibling_still_rejected(tmp_path):
    bundle = _bundle()
    confirmation = copy.deepcopy(bundle["human_confirmation_evidence"])
    confirmation["confirmation_statement"] = "TAMPERED-AFTER-DIGEST"
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    conf_path = _write(tmp_path, confirmation)
    outcome = _verify(hgr_path, related=(conf_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "DIGEST_MISMATCH"
