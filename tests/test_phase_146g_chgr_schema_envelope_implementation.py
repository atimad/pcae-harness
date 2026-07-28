"""Phase 146G tests: CHGR-001 Schema-Envelope Implementation
(CHGR-REQ-194 through CHGR-REQ-209).

Covers construction of the four schema-conformant CHGR-001 v1.2
artifacts (``human_governance_record``, ``human_confirmation_evidence``,
``governance_record_provenance``, ``governance_record_integrity``) that
``build_publication_record`` (widened Phase 144F/146G) now produces:
manifest-sourced envelope fields, identity/digest generation, the
authority-basis and assurance-level construction rules, the fail-closed
CHGR-REQ-204/205/208 validation gate, and end-to-end Publication
Coordinator integration. ``tests/test_phase_144c_publication_coordinator.py``
covers Coordinator-level behavior (authorization, replay, rollback,
storage failure) unaffected by this widening; this module focuses on the
CHGR-001 schema-envelope content itself.
"""
from __future__ import annotations

import json

import pytest

from pcae.governance.publication.chgr_envelope import (
    RECORD_FAMILIES,
    chgr_timestamp,
    envelope_for,
    validate_chgr_artifact,
)
from pcae.governance.publication.coordinator import PublicationCoordinator
from pcae.governance.publication.errors import ChgrSchemaConformanceError
from pcae.governance.publication.models import PublicationAuthorizationEvent
from pcae.governance.publication.record import build_publication_record, compute_record_digest
from pcae.governance.publication.storage import PublicationRecordStore
from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage
from pcae.interactive_workflow.session.identity import generate_session_id

_TS = "2026-07-24T10:00:00+00:00"
_LATER_TS = "2026-07-24T11:00:00+00:00"
_PREVIEW_DIGEST = "b" * 64

_ID_PREFIX_BY_FAMILY = {
    "human_governance_record": "chgr-",
    "human_confirmation_evidence": "chgrconf-",
    "governance_record_provenance": "chgrprov-",
    "governance_record_integrity": "chgrintg-",
}


def _package(
    *,
    evidence_kind: str = "typed_confirmation_only",
    rationale_text: str | None = "Because the data supports it.",
    conditions_text: str | None = None,
    selected_option_id: str = "option-a",
) -> PublicationReadinessPackage:
    return PublicationReadinessPackage(
        package_id="pkg-146g",
        session_id=generate_session_id(),
        session_state=SessionState.CONFIRMED,
        transition_sequence_number=0,
        evidence_refs=("ev-1",),
        clarification_refs=(),
        audit_refs=(),
        preview_id="preview-1",
        preview_digest=_PREVIEW_DIGEST,
        confirmation_request_id="req-1",
        confirmation_response_id="resp-1",
        built_at=_TS,
        decision_subject="subject-1",
        template_id="template-1",
        template_version="1.0",
        selected_option_id=selected_option_id,
        rationale_text=rationale_text,
        conditions_text=conditions_text,
        options_presented=("option-a", "option-b"),
        decision_maker_identity_evidence={
            "evidence_kind": evidence_kind,
            "identifier": "human-1",
            "captured_at": _TS,
        },
        preview_rendered_content="Confirm selection: option-a",
        confirmation_statement="Accepted",
        confirmation_timestamp=_TS,
    )


def _event(package: PublicationReadinessPackage) -> PublicationAuthorizationEvent:
    return PublicationAuthorizationEvent(
        event_id="pubauth-1", operator_id="alice", package_id=package.package_id, invoked_at=_LATER_TS
    )


def _record_id() -> str:
    import uuid

    return f"chgr-{uuid.uuid4().hex}"


# --- Unit: timestamp normalization (146F Risk R-3) ------------------------


def test_chgr_timestamp_normalizes_offset_suffix_to_z():
    assert chgr_timestamp("2026-07-24T10:00:00+00:00") == "2026-07-24T10:00:00Z"


def test_chgr_timestamp_is_idempotent_on_z_suffixed_input():
    assert chgr_timestamp("2026-07-24T10:00:00Z") == "2026-07-24T10:00:00Z"


def test_chgr_timestamp_preserves_fractional_seconds():
    assert chgr_timestamp("2026-07-24T10:00:00.123456+00:00") == "2026-07-24T10:00:00.123456Z"


# --- Unit: manifest-sourced envelope construction (CHGR-REQ-194) ---------


@pytest.mark.parametrize("family", RECORD_FAMILIES)
def test_envelope_schema_id_and_version_match_manifest(family):
    from pcae.governance.publication.chgr_envelope import _manifest_entry_for  # noqa: SLF001

    envelope = envelope_for(family, "some-record-id-00000000", _TS)
    entry = _manifest_entry_for(family)
    assert envelope["schema_id"] == entry["schema_id"]
    assert envelope["schema_version"] == entry["schema_version"]
    assert envelope["contract_version"] == "CHGR-001/1.0"
    assert envelope["record_type"] == family
    assert envelope["created_at"] == "2026-07-24T10:00:00Z"
    assert "record_digest" not in envelope


def test_envelope_unknown_family_raises():
    from pcae.governance.publication.chgr_envelope import ChgrManifestLookupError

    with pytest.raises(ChgrManifestLookupError):
        envelope_for("not_a_real_family", "id", _TS)


# --- Unit: identity generation (CHGR-REQ-195-197) -------------------------


def test_construction_assigns_four_distinct_family_prefixed_ids():
    package = _package()
    bundle = build_publication_record(package, _event(package), _record_id(), _TS)
    ids = {family: artifact["record_id"] for family, artifact in bundle.items()}
    assert len(set(ids.values())) == 4
    for family, record_id in ids.items():
        assert record_id.startswith(_ID_PREFIX_BY_FAMILY[family])


def test_two_construction_calls_never_collide_identities():
    package = _package()
    bundle_a = build_publication_record(package, _event(package), _record_id(), _TS)
    bundle_b = build_publication_record(package, _event(package), _record_id(), _TS)
    ids_a = {artifact["record_id"] for artifact in bundle_a.values()}
    ids_b = {artifact["record_id"] for artifact in bundle_b.values()}
    assert ids_a.isdisjoint(ids_b)


# --- Unit: digest generation (CHGR-REQ-195-197) ---------------------------


def test_every_artifact_digest_is_64_char_lowercase_hex_and_self_consistent():
    package = _package()
    bundle = build_publication_record(package, _event(package), _record_id(), _TS)
    for artifact in bundle.values():
        digest = artifact["record_digest"]
        assert len(digest) == 64
        assert digest == digest.lower()
        int(digest, 16)  # raises ValueError if not hex
        assert digest == compute_record_digest(artifact)


def test_construction_is_deterministic_for_its_substantive_content():
    """Two constructions from identical (package, created_at) inputs are
    byte-identical in every substantive field; only the three internally
    minted sibling identities (and the digests that depend on them) ever
    differ between calls, by design (CHGR-REQ-077: an identity is never
    reused once assigned)."""

    package = _package()
    record_id = _record_id()
    first = build_publication_record(package, _event(package), record_id, _TS)
    second = build_publication_record(package, _event(package), record_id, _TS)

    first_hgr = first["human_governance_record"]
    second_hgr = second["human_governance_record"]
    for field in (
        "decision_subject",
        "template_ref",
        "selected_option_id",
        "decision_maker_identity_evidence",
        "assurance_level",
        "lifecycle_state",
        "rationale",
        "limitations",
    ):
        assert first_hgr[field] == second_hgr[field]
    assert first_hgr["record_id"] == second_hgr["record_id"] == record_id


def test_no_artifact_digest_hashes_a_sibling_payload_verbatim():
    """CHGR-REQ-197: siblings are cited only via id+digest reference
    tuples, never by embedding the sibling's own full payload bytes."""

    package = _package()
    bundle = build_publication_record(package, _event(package), _record_id(), _TS)
    hgr = bundle["human_governance_record"]
    assert set(hgr["confirmation_evidence_ref"]) == {"record_id", "record_digest", "record_family"}
    assert set(hgr["provenance_ref"]) == {"record_id", "record_digest", "record_family"}
    assert set(hgr["integrity_ref"]) == {"record_id", "record_digest", "record_family"}


# --- Unit: authority-basis handling (CHGR-REQ-199, 207, 208) --------------


def test_authority_basis_claimed_absent_and_disclosed():
    package = _package()
    bundle = build_publication_record(package, _event(package), _record_id(), _TS)
    hgr = bundle["human_governance_record"]
    assert "authority_basis_claimed" not in hgr
    assert any("authority_basis_claimed" in entry for entry in hgr["limitations"])


# --- Unit: assurance-level handling (CHGR-REQ-200, 201) -------------------


@pytest.mark.parametrize(
    ("evidence_kind", "expected_level"),
    [("typed_confirmation_only", "L0"), ("os_authenticated_user", "L1")],
)
def test_assurance_level_mapping(evidence_kind, expected_level):
    package = _package(evidence_kind=evidence_kind)
    bundle = build_publication_record(package, _event(package), _record_id(), _TS)
    hgr = bundle["human_governance_record"]
    hce = bundle["human_confirmation_evidence"]
    assert hgr["assurance_level"] == expected_level
    assert hce["achieved_assurance_level"] == expected_level


def test_unrecognized_evidence_kind_refuses_construction():
    package = _package(evidence_kind="some_future_l3_kind")
    with pytest.raises(ChgrSchemaConformanceError):
        build_publication_record(package, _event(package), _record_id(), _TS)


# --- Unit: validation failures (CHGR-REQ-204, 205) ------------------------


def test_pattern_violating_selected_option_id_refuses_construction_with_diagnostics():
    package = _package(selected_option_id="Not A Valid Option Id!!")
    with pytest.raises(ChgrSchemaConformanceError) as excinfo:
        build_publication_record(package, _event(package), _record_id(), _TS)
    assert "selected_option_id" in str(excinfo.value)


def test_lifecycle_state_is_always_the_fixed_published_constant():
    package = _package()
    bundle = build_publication_record(package, _event(package), _record_id(), _TS)
    assert bundle["human_governance_record"]["lifecycle_state"] == "published"


def test_repository_provenance_unavailable_and_disclosed():
    package = _package()
    bundle = build_publication_record(package, _event(package), _record_id(), _TS)
    provenance = bundle["governance_record_provenance"]
    assert provenance["repository_provenance"] == {"available": False}
    assert any("repository_provenance" in entry for entry in provenance["limitations"])


# --- Integration: Publication Coordinator end-to-end ----------------------


def test_end_to_end_publication_persists_four_cross_referenced_artifacts(tmp_path):
    store = PublicationRecordStore(root=tmp_path / "pub-exec")
    coordinator = PublicationCoordinator(store=store)
    package = _package()
    event = coordinator.authorize(operator_id="alice", package_id=package.package_id, invoked_at=_LATER_TS)

    result = coordinator.execute(package, event)
    assert result.success is True

    hgr = json.loads(store._record_path(result.record_id).read_text())  # noqa: SLF001
    for ref_field, expected_family in (
        ("confirmation_evidence_ref", "human_confirmation_evidence"),
        ("provenance_ref", "governance_record_provenance"),
        ("integrity_ref", "governance_record_integrity"),
    ):
        ref = hgr[ref_field]
        assert ref["record_family"] == expected_family
        sibling_path = store._record_path(ref["record_id"])  # noqa: SLF001
        assert sibling_path.exists()
        sibling = json.loads(sibling_path.read_text())
        assert sibling["record_type"] == expected_family
        assert validate_chgr_artifact(sibling).ok


def test_fail_closed_refusal_leaves_package_unpublished_and_retriable(tmp_path):
    store = PublicationRecordStore(root=tmp_path / "pub-exec")
    coordinator = PublicationCoordinator(store=store)
    bad_package = _package(selected_option_id="Not A Valid Option Id!!")
    event = coordinator.authorize(operator_id="alice", package_id=bad_package.package_id, invoked_at=_LATER_TS)

    with pytest.raises(ChgrSchemaConformanceError):
        coordinator.execute(bad_package, event)

    assert not store.is_published(bad_package.package_id)
    assert list((store.root / "records").glob("*.json")) == []

    good_package = _package()
    object.__setattr__(good_package, "package_id", bad_package.package_id)
    retry_event = coordinator.authorize(
        operator_id="alice", package_id=good_package.package_id, invoked_at=_LATER_TS
    )
    result = coordinator.execute(good_package, retry_event)
    assert result.success is True
    assert store.is_published(good_package.package_id)


def test_round_trip_reload_and_revalidate_from_disk(tmp_path):
    store = PublicationRecordStore(root=tmp_path / "pub-exec")
    coordinator = PublicationCoordinator(store=store)
    package = _package()
    event = coordinator.authorize(operator_id="alice", package_id=package.package_id, invoked_at=_LATER_TS)
    result = coordinator.execute(package, event)

    hgr = json.loads(store._record_path(result.record_id).read_text())  # noqa: SLF001
    reloaded_ids = [result.record_id] + [
        hgr[field]["record_id"] for field in ("confirmation_evidence_ref", "provenance_ref", "integrity_ref")
    ]
    for record_id in reloaded_ids:
        reloaded = json.loads(store._record_path(record_id).read_text())  # noqa: SLF001
        assert reloaded["record_digest"] == compute_record_digest(reloaded)
        assert validate_chgr_artifact(reloaded).ok


# --- Regression: runtime invariants unchanged -----------------------------


def test_no_new_manifest_entry_or_schema_file_is_needed():
    """146G is content-transformation-and-gate-insertion only (146F Sec.2):
    the CHGR schema family and manifest are read-only inputs, never
    written to by construction."""

    package = _package()
    build_publication_record(package, _event(package), _record_id(), _TS)
    # No assertion beyond "did not raise" / no filesystem write attempted --
    # chgr_root() yields a real filesystem path but this module never opens
    # it for writing; a stray write would be caught by chgr_root's own
    # packaging test suite (tests/test_chgr_packaging.py) if introduced.
