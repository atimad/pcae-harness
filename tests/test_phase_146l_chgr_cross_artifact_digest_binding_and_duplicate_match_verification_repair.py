"""Phase 146L tests: CHGR Cross-Artifact Digest-Binding and Duplicate-Match
Verification Repair.

Covers the repair to ``pcae.governance.verification``'s related-artifact
resolution (formerly ``_find_related``, now ``_resolve_related``, a nested
helper of ``verify_artifact_at_path``), implementing CHGR-REQ-212 (exact
``record_family``/``record_id``/``record_digest`` reference matching for
``confirmation_evidence_ref`` and ``provenance_ref``) and CHGR-REQ-213
(fail-closed duplicate-match rejection for every related-artifact role),
while preserving the directed one-way integrity binding CHGR-REQ-211 froze
in Phase 146K (CHGR-001 v1.3 Sec.30): ``integrity_ref.record_digest`` is
never compared against the resolved integrity artifact's own
``record_digest``.

Two independently-constructed genuine ``build_publication_record`` bundles
(A and B, differing in every confirmation/provenance-bearing field so a
cross-bundle substitution attempt is never a coincidental digest match)
back the cross-bundle and duplicate-match scenarios; standalone
self-consistent fixtures back the narrower unit-level matrix cases.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.governance.publication.record import build_publication_record, compute_record_digest
from pcae.governance.publication.models import PublicationAuthorizationEvent
from pcae.governance.verification import (
    VerificationFailure,
    VerificationObservation,
    verify_artifact_at_path,
)
from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage
from pcae.interactive_workflow.session.identity import generate_session_id

_TS = "2026-07-24T10:00:00+00:00"
_LATER_TS = "2026-07-24T11:00:00+00:00"


# --- Bundle construction helpers -------------------------------------------


def _package(pkg_id: str) -> PublicationReadinessPackage:
    variant = "A" if pkg_id.endswith("A") else "B"
    return PublicationReadinessPackage(
        package_id=pkg_id,
        session_id=generate_session_id(),
        session_state=SessionState.CONFIRMED,
        transition_sequence_number=0,
        evidence_refs=("ev-1",),
        clarification_refs=(),
        audit_refs=(),
        preview_id=f"preview-{variant}",
        preview_digest=("b" if variant == "A" else "c") * 64,
        confirmation_request_id="req-1",
        confirmation_response_id="resp-1",
        built_at=_TS,
        decision_subject=f"subject-{variant}",
        template_id="template-1",
        template_version="1.0",
        selected_option_id="option-a",
        rationale_text="Because the data supports it.",
        conditions_text=None,
        options_presented=("option-a", "option-b"),
        decision_maker_identity_evidence={
            "evidence_kind": "typed_confirmation_only",
            "identifier": f"human-{variant}",
            "captured_at": _TS,
        },
        preview_rendered_content=f"Confirm selection: option-{variant.lower()}",
        confirmation_statement=f"Accepted by confirmer {variant}",
        confirmation_timestamp=_TS,
    )


def _event(package: PublicationReadinessPackage) -> PublicationAuthorizationEvent:
    return PublicationAuthorizationEvent(
        event_id="pubauth-146l", operator_id="alice", package_id=package.package_id, invoked_at=_LATER_TS
    )


def _bundle(pkg_id: str, record_char: str) -> dict:
    package = _package(pkg_id)
    event = _event(package)
    return build_publication_record(package, event, "chgr-" + record_char * 32, _TS)


def _bundle_a() -> dict:
    return _bundle("pkg-A", "a")


def _bundle_b() -> dict:
    return _bundle("pkg-B", "b")


def _write(tmp_path: Path, artifact: dict, name: str | None = None) -> Path:
    path = tmp_path / f"{name or artifact['record_id']}.json"
    path.write_text(json.dumps(artifact))
    return path


def _resign(artifact: dict) -> dict:
    artifact = dict(artifact)
    artifact["record_digest"] = compute_record_digest(artifact)
    return artifact


def _rereferenced(record: dict, ref_field: str, sibling: dict) -> dict:
    record = copy.deepcopy(record)
    record[ref_field] = dict(record[ref_field])
    record[ref_field]["record_digest"] = sibling["record_digest"]
    return _resign(record)


def _verify(path: Path, related: tuple[Path, ...] = ()) -> object:
    return verify_artifact_at_path(
        path,
        artifact_bytes=path.read_bytes(),
        related_bytes=tuple(p.read_bytes() for p in related),
    )


def _cli_verify(hgr_path: Path, related: tuple[Path, ...]) -> tuple[int, str]:
    args = ["governance-record", "verify", str(hgr_path)]
    for r in related:
        args += ["--related", str(r)]
    exit_code = main(args)
    return exit_code


def _cli_verify_subprocess(hgr_path: Path, related: tuple[Path, ...]) -> subprocess.CompletedProcess:
    args = ["pcae", "governance-record", "verify", str(hgr_path)]
    for r in related:
        args += ["--related", str(r)]
    return subprocess.run(args, capture_output=True, text=True)


def _cross_bundle_sibling(family: str, source_bundle: dict, target_ref: dict) -> dict:
    """A genuinely different (different content), self-consistent sibling
    from ``source_bundle``, retargeted to ``target_ref``'s record_id and
    re-signed -- CHGR-REQ-212's exact digest-reference threat model."""
    sibling = copy.deepcopy(source_bundle[family])
    sibling["record_id"] = target_ref["record_id"]
    return _resign(sibling)


# --- A. Confirmation evidence matrix ---------------------------------------


def test_confirmation_exact_family_id_digest_passes(tmp_path):
    bundle = _bundle_a()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    conf_path = _write(tmp_path, bundle["human_confirmation_evidence"])
    outcome = _verify(hgr_path, (conf_path,))
    assert isinstance(outcome, VerificationObservation), outcome
    assert next(c for c in outcome.checks if c.name == "confirmation_binding").status == "passed"


def test_confirmation_id_match_digest_mismatch_fails(tmp_path):
    bundle = _bundle_a()
    confirmation = copy.deepcopy(bundle["human_confirmation_evidence"])
    confirmation["confirmation_statement"] = "A different statement entirely"
    confirmation = _resign(confirmation)  # same record_id, different record_digest
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    conf_path = _write(tmp_path, confirmation)
    outcome = _verify(hgr_path, (conf_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "REFERENCE_DIGEST_MISMATCH"


def test_confirmation_digest_match_id_mismatch_is_not_treated_as_bound(tmp_path):
    """A candidate whose record_digest coincidentally matches some other
    reference's digest but whose record_id does not match this HGR's
    confirmation_evidence_ref is never resolved as its confirmation
    sibling -- the check reports skipped (absent), never passed."""
    bundle = _bundle_a()
    other = copy.deepcopy(bundle["human_confirmation_evidence"])
    other["record_id"] = "chgrconf-" + "9" * 32
    other = _resign(other)
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    other_path = _write(tmp_path, other)
    outcome = _verify(hgr_path, (other_path,))
    assert isinstance(outcome, VerificationObservation), outcome
    assert next(c for c in outcome.checks if c.name == "confirmation_binding").status == "skipped"


def test_confirmation_family_mismatch_fails(tmp_path):
    bundle = _bundle_a()
    ref = bundle["human_governance_record"]["confirmation_evidence_ref"]
    wrong_family = copy.deepcopy(bundle["governance_record_provenance"])
    wrong_family["record_id"] = ref["record_id"]
    wrong_family = _resign(wrong_family)
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    candidate_path = _write(tmp_path, wrong_family)
    outcome = _verify(hgr_path, (candidate_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "RELATED_ARTIFACT_FAMILY_MISMATCH"


def test_confirmation_duplicate_exact_match_fails(tmp_path):
    bundle = _bundle_a()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    conf_path_1 = _write(tmp_path, bundle["human_confirmation_evidence"], name="c1")
    conf_path_2 = _write(tmp_path, bundle["human_confirmation_evidence"], name="c2")
    outcome = _verify(hgr_path, (conf_path_1, conf_path_2))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "RELATED_ARTIFACT_AMBIGUOUS"


def test_confirmation_duplicate_same_id_different_digest_fails(tmp_path):
    bundle = _bundle_a()
    genuine = bundle["human_confirmation_evidence"]
    forged = copy.deepcopy(genuine)
    forged["confirmed_content_digest"] = "9" * 64
    forged["preview_rendering_digest"] = "9" * 64
    forged = _resign(forged)
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    genuine_path = _write(tmp_path, genuine, name="genuine")
    forged_path = _write(tmp_path, forged, name="forged")
    for order in ((genuine_path, forged_path), (forged_path, genuine_path)):
        outcome = _verify(hgr_path, order)
        assert isinstance(outcome, VerificationFailure), outcome
        assert outcome.error_code == "RELATED_ARTIFACT_AMBIGUOUS"


def test_confirmation_cross_bundle_forged_artifact_fails(tmp_path):
    bundle_a, bundle_b = _bundle_a(), _bundle_b()
    ref = bundle_a["human_governance_record"]["confirmation_evidence_ref"]
    forged = _cross_bundle_sibling("human_confirmation_evidence", bundle_b, ref)
    assert forged["record_digest"] != ref["record_digest"]
    hgr_path = _write(tmp_path, bundle_a["human_governance_record"])
    forged_path = _write(tmp_path, forged)
    outcome = _verify(hgr_path, (forged_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "REFERENCE_DIGEST_MISMATCH"


def test_confirmation_reordered_input_remains_identical(tmp_path):
    bundle = _bundle_a()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    conf_path = _write(tmp_path, bundle["human_confirmation_evidence"])
    prov_path = _write(tmp_path, bundle["governance_record_provenance"])
    integ_path = _write(tmp_path, bundle["governance_record_integrity"])
    forward = _verify(hgr_path, (conf_path, prov_path, integ_path))
    backward = _verify(hgr_path, (integ_path, prov_path, conf_path))
    assert forward.to_dict() == backward.to_dict()


def test_confirmation_malformed_artifact_fails(tmp_path):
    bundle = _bundle_a()
    confirmation = copy.deepcopy(bundle["human_confirmation_evidence"])
    del confirmation["confirmation_statement"]  # required field -- schema-shape invalid
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    conf_path = _write(tmp_path, confirmation)
    outcome = _verify(hgr_path, (conf_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "DIGEST_MISMATCH"


def test_confirmation_self_digest_invalid_artifact_fails(tmp_path):
    bundle = _bundle_a()
    confirmation = dict(bundle["human_confirmation_evidence"])
    confirmation["confirmation_statement"] = "tampered after signing, digest not recomputed"
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    conf_path = _write(tmp_path, confirmation)
    outcome = _verify(hgr_path, (conf_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "DIGEST_MISMATCH"


# --- B. Provenance matrix (mirrors confirmation) ----------------------------


def test_provenance_exact_family_id_digest_passes(tmp_path):
    bundle = _bundle_a()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    related = (
        _write(tmp_path, bundle["human_confirmation_evidence"]),
        _write(tmp_path, bundle["governance_record_provenance"]),
    )
    outcome = _verify(hgr_path, related)
    assert isinstance(outcome, VerificationObservation), outcome
    assert next(c for c in outcome.checks if c.name == "provenance_consistency").status == "passed"


def test_provenance_id_match_digest_mismatch_fails(tmp_path):
    bundle = _bundle_a()
    provenance = copy.deepcopy(bundle["governance_record_provenance"])
    provenance["rationale_given"] = "A materially different rationale"
    provenance = _resign(provenance)
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    prov_path = _write(tmp_path, provenance)
    outcome = _verify(hgr_path, (prov_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "REFERENCE_DIGEST_MISMATCH"


def test_provenance_family_mismatch_fails(tmp_path):
    bundle = _bundle_a()
    ref = bundle["human_governance_record"]["provenance_ref"]
    wrong_family = copy.deepcopy(bundle["human_confirmation_evidence"])
    wrong_family["record_id"] = ref["record_id"]
    wrong_family = _resign(wrong_family)
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    candidate_path = _write(tmp_path, wrong_family)
    outcome = _verify(hgr_path, (candidate_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "RELATED_ARTIFACT_FAMILY_MISMATCH"


def test_provenance_duplicate_exact_match_fails(tmp_path):
    bundle = _bundle_a()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    p1 = _write(tmp_path, bundle["governance_record_provenance"], name="p1")
    p2 = _write(tmp_path, bundle["governance_record_provenance"], name="p2")
    outcome = _verify(hgr_path, (p1, p2))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "RELATED_ARTIFACT_AMBIGUOUS"


def test_provenance_duplicate_same_id_different_digest_fails(tmp_path):
    bundle = _bundle_a()
    genuine = bundle["governance_record_provenance"]
    forged = copy.deepcopy(genuine)
    forged["rationale_given"] = "forged alternate rationale"
    forged = _resign(forged)
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    genuine_path = _write(tmp_path, genuine, name="genuine")
    forged_path = _write(tmp_path, forged, name="forged")
    for order in ((genuine_path, forged_path), (forged_path, genuine_path)):
        outcome = _verify(hgr_path, order)
        assert isinstance(outcome, VerificationFailure), outcome
        assert outcome.error_code == "RELATED_ARTIFACT_AMBIGUOUS"


def test_provenance_cross_bundle_forged_artifact_fails(tmp_path):
    bundle_a, bundle_b = _bundle_a(), _bundle_b()
    ref = bundle_a["human_governance_record"]["provenance_ref"]
    forged = _cross_bundle_sibling("governance_record_provenance", bundle_b, ref)
    assert forged["record_digest"] != ref["record_digest"]
    hgr_path = _write(tmp_path, bundle_a["human_governance_record"])
    forged_path = _write(tmp_path, forged)
    outcome = _verify(hgr_path, (forged_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "REFERENCE_DIGEST_MISMATCH"


def test_provenance_reordered_input_remains_identical(tmp_path):
    bundle = _bundle_a()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    conf_path = _write(tmp_path, bundle["human_confirmation_evidence"])
    prov_path = _write(tmp_path, bundle["governance_record_provenance"])
    forward = _verify(hgr_path, (conf_path, prov_path))
    backward = _verify(hgr_path, (prov_path, conf_path))
    assert forward.to_dict() == backward.to_dict()


def test_provenance_malformed_artifact_fails(tmp_path):
    bundle = _bundle_a()
    provenance = copy.deepcopy(bundle["governance_record_provenance"])
    del provenance["selected_option_id"]
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    prov_path = _write(tmp_path, provenance)
    outcome = _verify(hgr_path, (prov_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "DIGEST_MISMATCH"


# --- C. Integrity matrix (directed one-way; no reference-digest check) -----


def test_integrity_exact_family_id_correct_payload_digest_passes(tmp_path):
    bundle = _bundle_a()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    integ_path = _write(tmp_path, bundle["governance_record_integrity"])
    outcome = _verify(hgr_path, (integ_path,))
    assert isinstance(outcome, VerificationObservation), outcome
    assert next(c for c in outcome.checks if c.name == "integrity_consistency").status == "passed"


def test_integrity_wrong_id_treated_as_absent(tmp_path):
    bundle = _bundle_a()
    integrity = copy.deepcopy(bundle["governance_record_integrity"])
    integrity["record_id"] = "chgrintg-" + "9" * 32
    integrity = _resign(integrity)
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    integ_path = _write(tmp_path, integrity)
    outcome = _verify(hgr_path, (integ_path,))
    assert isinstance(outcome, VerificationObservation), outcome
    assert next(c for c in outcome.checks if c.name == "integrity_consistency").status == "skipped"


def test_integrity_wrong_family_fails(tmp_path):
    bundle = _bundle_a()
    ref = bundle["human_governance_record"]["integrity_ref"]
    wrong_family = copy.deepcopy(bundle["human_confirmation_evidence"])
    wrong_family["record_id"] = ref["record_id"]
    wrong_family = _resign(wrong_family)
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    candidate_path = _write(tmp_path, wrong_family)
    outcome = _verify(hgr_path, (candidate_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "RELATED_ARTIFACT_FAMILY_MISMATCH"


def test_integrity_wrong_payload_digest_fails(tmp_path):
    bundle = _bundle_a()
    integrity = copy.deepcopy(bundle["governance_record_integrity"])
    integrity["payload_digest"] = "6" * 64
    integrity = _resign(integrity)
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    integ_path = _write(tmp_path, integrity)
    outcome = _verify(hgr_path, (integ_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "DIGEST_MISMATCH"


def test_integrity_duplicate_exact_identity_fails(tmp_path):
    bundle = _bundle_a()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    i1 = _write(tmp_path, bundle["governance_record_integrity"], name="i1")
    i2 = _write(tmp_path, bundle["governance_record_integrity"], name="i2")
    outcome = _verify(hgr_path, (i1, i2))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "RELATED_ARTIFACT_AMBIGUOUS"


def test_integrity_cross_bundle_sibling_fails(tmp_path):
    """A genuine bundle-B integrity artifact, retargeted to bundle A's
    integrity_ref record_id and re-signed, still fails: its payload_digest
    binds to bundle B's human_governance_record, not bundle A's -- the
    binding CHGR-REQ-211 actually requires is preserved even though the
    (provisional) reference digest is never checked."""
    bundle_a, bundle_b = _bundle_a(), _bundle_b()
    ref = bundle_a["human_governance_record"]["integrity_ref"]
    forged = copy.deepcopy(bundle_b["governance_record_integrity"])
    forged["record_id"] = ref["record_id"]
    forged = _resign(forged)
    hgr_path = _write(tmp_path, bundle_a["human_governance_record"])
    forged_path = _write(tmp_path, forged)
    outcome = _verify(hgr_path, (forged_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "DIGEST_MISMATCH"


def test_integrity_reordered_input_remains_identical(tmp_path):
    bundle = _bundle_a()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    conf_path = _write(tmp_path, bundle["human_confirmation_evidence"])
    integ_path = _write(tmp_path, bundle["governance_record_integrity"])
    forward = _verify(hgr_path, (conf_path, integ_path))
    backward = _verify(hgr_path, (integ_path, conf_path))
    assert forward.to_dict() == backward.to_dict()


def test_integrity_genuine_provisional_reference_digest_bundle_passes(tmp_path):
    """The exact production shape build_publication_record emits:
    integrity_ref.record_digest is a provisional pre-payload_digest-patch
    value that never equals governance_record_integrity's own final
    record_digest (146F Sec.3.3 forward-reference cycle). This must still
    verify (CHGR-REQ-215 legacy/ongoing compatibility)."""
    bundle = _bundle_a()
    ref_digest = bundle["human_governance_record"]["integrity_ref"]["record_digest"]
    actual_digest = bundle["governance_record_integrity"]["record_digest"]
    assert ref_digest != actual_digest, "fixture no longer exercises the provisional-digest shape"
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    integ_path = _write(tmp_path, bundle["governance_record_integrity"])
    outcome = _verify(hgr_path, (integ_path,))
    assert isinstance(outcome, VerificationObservation), outcome
    assert next(c for c in outcome.checks if c.name == "integrity_consistency").status == "passed"


def test_integrity_final_self_digest_equality_is_not_enforced():
    """Direct proof the verifier's integrity resolution never compares
    integrity_ref.record_digest against the resolved artifact's own
    record_digest -- reading the source is the only way to prove a check
    is *absent*, not merely unexercised by this test module's fixtures."""
    import inspect

    import pcae.governance.verification as verification_module

    source = inspect.getsource(verification_module)
    # The one call site that resolves the integrity role must pass
    # enforce_reference_digest=False.
    idx = source.index('"governance_record_integrity", record["integrity_ref"]')
    window = source[idx : idx + 200]
    assert "enforce_reference_digest=False" in window


# --- D. Bundle-level scenarios ----------------------------------------------


def test_bundle_missing_confirmation_sibling_reports_skipped_not_verified_false(tmp_path):
    bundle = _bundle_a()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    prov_path = _write(tmp_path, bundle["governance_record_provenance"])
    integ_path = _write(tmp_path, bundle["governance_record_integrity"])
    outcome = _verify(hgr_path, (prov_path, integ_path))
    assert isinstance(outcome, VerificationObservation), outcome
    binding = next(c for c in outcome.checks if c.name == "confirmation_binding")
    assert binding.status == "skipped"
    assert binding.detail


def test_bundle_missing_provenance_sibling_reports_skipped(tmp_path):
    bundle = _bundle_a()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    conf_path = _write(tmp_path, bundle["human_confirmation_evidence"])
    outcome = _verify(hgr_path, (conf_path,))
    assert isinstance(outcome, VerificationObservation), outcome
    assert next(c for c in outcome.checks if c.name == "provenance_consistency").status == "skipped"


def test_bundle_missing_integrity_sibling_reports_skipped(tmp_path):
    bundle = _bundle_a()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    conf_path = _write(tmp_path, bundle["human_confirmation_evidence"])
    outcome = _verify(hgr_path, (conf_path,))
    assert isinstance(outcome, VerificationObservation), outcome
    assert next(c for c in outcome.checks if c.name == "integrity_consistency").status == "skipped"


def test_bundle_extra_unrelated_siblings_do_not_break_verification(tmp_path):
    bundle_a, bundle_b = _bundle_a(), _bundle_b()
    hgr_path = _write(tmp_path, bundle_a["human_governance_record"])
    related = (
        _write(tmp_path, bundle_a["human_confirmation_evidence"]),
        _write(tmp_path, bundle_a["governance_record_provenance"]),
        _write(tmp_path, bundle_a["governance_record_integrity"]),
        # Unrelated bundle-B siblings, distinct record_ids: no identity
        # collision, so they are simply ignored, not treated as duplicates.
        _write(tmp_path, bundle_b["human_confirmation_evidence"]),
        _write(tmp_path, bundle_b["governance_record_provenance"]),
    )
    outcome = _verify(hgr_path, related)
    assert isinstance(outcome, VerificationObservation), outcome
    assert outcome.outcome == "verified"


def test_bundle_duplicate_siblings_of_multiple_roles_all_fail_ambiguous(tmp_path):
    bundle = _bundle_a()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    related = (
        _write(tmp_path, bundle["human_confirmation_evidence"], name="c1"),
        _write(tmp_path, bundle["human_confirmation_evidence"], name="c2"),
        _write(tmp_path, bundle["governance_record_provenance"]),
    )
    outcome = _verify(hgr_path, related)
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "RELATED_ARTIFACT_AMBIGUOUS"


def test_bundle_all_siblings_valid_but_one_belongs_to_another_bundle(tmp_path):
    bundle_a, bundle_b = _bundle_a(), _bundle_b()
    ref = bundle_a["human_governance_record"]["provenance_ref"]
    forged_provenance = _cross_bundle_sibling("governance_record_provenance", bundle_b, ref)
    hgr_path = _write(tmp_path, bundle_a["human_governance_record"])
    related = (
        _write(tmp_path, bundle_a["human_confirmation_evidence"]),
        _write(tmp_path, forged_provenance),
        _write(tmp_path, bundle_a["governance_record_integrity"]),
    )
    outcome = _verify(hgr_path, related)
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "REFERENCE_DIGEST_MISMATCH"


def test_bundle_primary_record_tampering_still_rejected(tmp_path):
    bundle = _bundle_a()
    tampered = dict(bundle["human_governance_record"])
    tampered["decision_subject"] = "TAMPERED-AFTER-DIGEST"
    hgr_path = _write(tmp_path, tampered)
    conf_path = _write(tmp_path, bundle["human_confirmation_evidence"])
    outcome = _verify(hgr_path, (conf_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "DIGEST_MISMATCH"


def test_bundle_related_artifact_tampering_still_rejected(tmp_path):
    bundle = _bundle_a()
    confirmation = dict(bundle["human_confirmation_evidence"])
    confirmation["confirmation_statement"] = "TAMPERED-AFTER-DIGEST"
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    conf_path = _write(tmp_path, confirmation)
    outcome = _verify(hgr_path, (conf_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "DIGEST_MISMATCH"


def test_bundle_cli_and_api_outcome_agreement(tmp_path):
    bundle_a, bundle_b = _bundle_a(), _bundle_b()
    ref = bundle_a["human_governance_record"]["confirmation_evidence_ref"]
    forged = _cross_bundle_sibling("human_confirmation_evidence", bundle_b, ref)
    hgr_path = _write(tmp_path, bundle_a["human_governance_record"])
    forged_path = _write(tmp_path, forged)

    api_outcome = _verify(hgr_path, (forged_path,))
    assert isinstance(api_outcome, VerificationFailure)

    exit_code = _cli_verify(hgr_path, (forged_path,))
    assert exit_code != 0


# --- E. Live production-bundle verification (real CLI subprocess) ----------


def test_live_genuine_bundle_a_passes_through_api(tmp_path):
    bundle = _bundle_a()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    related = (
        _write(tmp_path, bundle["human_confirmation_evidence"]),
        _write(tmp_path, bundle["governance_record_provenance"]),
        _write(tmp_path, bundle["governance_record_integrity"]),
    )
    outcome = _verify(hgr_path, related)
    assert isinstance(outcome, VerificationObservation), outcome
    assert outcome.outcome == "verified"
    assert {c.status for c in outcome.checks if c.name != "template_resolution"} == {"passed"}


def test_live_genuine_bundle_a_passes_through_real_cli_subprocess(tmp_path):
    bundle = _bundle_a()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    related = (
        _write(tmp_path, bundle["human_confirmation_evidence"]),
        _write(tmp_path, bundle["governance_record_provenance"]),
        _write(tmp_path, bundle["governance_record_integrity"]),
    )
    result = _cli_verify_subprocess(hgr_path, related)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "outcome: verified" in result.stdout


def test_live_bundle_a_with_bundle_b_confirmation_fails(tmp_path):
    bundle_a, bundle_b = _bundle_a(), _bundle_b()
    ref = bundle_a["human_governance_record"]["confirmation_evidence_ref"]
    forged = _cross_bundle_sibling("human_confirmation_evidence", bundle_b, ref)
    hgr_path = _write(tmp_path, bundle_a["human_governance_record"])
    related = (
        _write(tmp_path, forged),
        _write(tmp_path, bundle_a["governance_record_provenance"]),
        _write(tmp_path, bundle_a["governance_record_integrity"]),
    )
    outcome = _verify(hgr_path, related)
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "REFERENCE_DIGEST_MISMATCH"


def test_live_bundle_a_with_bundle_b_provenance_fails(tmp_path):
    bundle_a, bundle_b = _bundle_a(), _bundle_b()
    ref = bundle_a["human_governance_record"]["provenance_ref"]
    forged = _cross_bundle_sibling("governance_record_provenance", bundle_b, ref)
    hgr_path = _write(tmp_path, bundle_a["human_governance_record"])
    related = (
        _write(tmp_path, bundle_a["human_confirmation_evidence"]),
        _write(tmp_path, forged),
        _write(tmp_path, bundle_a["governance_record_integrity"]),
    )
    outcome = _verify(hgr_path, related)
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "REFERENCE_DIGEST_MISMATCH"


def test_live_bundle_a_with_bundle_b_integrity_fails(tmp_path):
    bundle_a, bundle_b = _bundle_a(), _bundle_b()
    ref = bundle_a["human_governance_record"]["integrity_ref"]
    forged = copy.deepcopy(bundle_b["governance_record_integrity"])
    forged["record_id"] = ref["record_id"]
    forged = _resign(forged)
    hgr_path = _write(tmp_path, bundle_a["human_governance_record"])
    related = (
        _write(tmp_path, bundle_a["human_confirmation_evidence"]),
        _write(tmp_path, bundle_a["governance_record_provenance"]),
        _write(tmp_path, forged),
    )
    outcome = _verify(hgr_path, related)
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "DIGEST_MISMATCH"


def test_live_record_id_rewriting_plus_self_digest_recomputation_no_longer_bypasses(tmp_path):
    """The exact Sec.2B reconfirmation scenario, re-proven post-repair:
    retargeting a genuine bundle-B sibling's record_id to bundle A's
    reference and recomputing its own record_digest no longer produces a
    self-consistent artifact this verifier accepts."""
    bundle_a, bundle_b = _bundle_a(), _bundle_b()
    ref = bundle_a["human_governance_record"]["confirmation_evidence_ref"]
    forged = _cross_bundle_sibling("human_confirmation_evidence", bundle_b, ref)
    assert forged["record_digest"] != ref["record_digest"]
    hgr_path = _write(tmp_path, bundle_a["human_governance_record"])
    forged_path = _write(tmp_path, forged)
    outcome = _verify(hgr_path, (forged_path,))
    assert isinstance(outcome, VerificationFailure), outcome
    assert outcome.error_code == "REFERENCE_DIGEST_MISMATCH"


def test_live_duplicate_match_order_reversal_produces_same_rejection(tmp_path):
    bundle = _bundle_a()
    genuine = bundle["human_confirmation_evidence"]
    forged = copy.deepcopy(genuine)
    forged["confirmed_content_digest"] = "9" * 64
    forged["preview_rendering_digest"] = "9" * 64
    forged = _resign(forged)
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    genuine_path = _write(tmp_path, genuine, name="genuine")
    forged_path = _write(tmp_path, forged, name="forged")
    order1 = _verify(hgr_path, (genuine_path, forged_path))
    order2 = _verify(hgr_path, (forged_path, genuine_path))
    assert isinstance(order1, VerificationFailure) and isinstance(order2, VerificationFailure)
    assert order1.error_code == order2.error_code == "RELATED_ARTIFACT_AMBIGUOUS"


def test_live_existing_directed_integrity_relationship_passes(tmp_path):
    bundle = _bundle_a()
    ref_digest = bundle["human_governance_record"]["integrity_ref"]["record_digest"]
    actual_digest = bundle["governance_record_integrity"]["record_digest"]
    assert ref_digest != actual_digest
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    related = (
        _write(tmp_path, bundle["human_confirmation_evidence"]),
        _write(tmp_path, bundle["governance_record_provenance"]),
        _write(tmp_path, bundle["governance_record_integrity"]),
    )
    outcome = _verify(hgr_path, related)
    assert isinstance(outcome, VerificationObservation), outcome
    assert outcome.outcome == "verified"


# --- F. Legacy compatibility (CHGR-REQ-215) ---------------------------------


def test_legacy_genuine_chapter_146_bundle_still_verifies(tmp_path):
    """A second independently-constructed genuine bundle, standing in for
    already-produced Chapter 146 production bundles: this repair changes
    no construction-time behavior, so every such bundle -- carrying the
    same provisional integrity_ref.record_digest shape -- verifies
    unchanged (CHGR-REQ-215)."""
    bundle = _bundle_b()
    hgr_path = _write(tmp_path, bundle["human_governance_record"])
    related = (
        _write(tmp_path, bundle["human_confirmation_evidence"]),
        _write(tmp_path, bundle["governance_record_provenance"]),
        _write(tmp_path, bundle["governance_record_integrity"]),
    )
    outcome = _verify(hgr_path, related)
    assert isinstance(outcome, VerificationObservation), outcome
    assert outcome.outcome == "verified"
